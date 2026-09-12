#!/usr/bin/env python3
"""Khóa dataset phân tích đã làm sạch, có audit trail và không PII.

Công cụ này chạy SAU bước intake/làm sạch và TRƯỚC phân tích chính G6/G7.
Nó không sửa dữ liệu gốc; chỉ copy bản clean đã được xác nhận sang
`05_clean_locked/`, đặt read-only, tạo lock memo/manifest và cập nhật
`study_meta.json` khi đủ xác nhận thật.

Ví dụ:
  python3 tools/lock_analysis_dataset.py --study KKB-HAI-LONG-2026 \\
    --clean-data df_clean.csv --query-log query_log.csv \\
    --dictionary G5_REDCap_dictionary_KKB-HAI-LONG-2026.csv \\
    --cleaning-report DATA_CLEANING_report.json \\
    --lock-date 2026-07-13 --reviewer-role DATA_MANAGER \\
    --reviewer-ref DM-LOCK-001 --sap-version 1.0 \\
    --confirm-deidentified --confirm-clean-copy --confirm-no-open-query \\
    --confirm-sap-locked --confirm-dictionary-crf-aligned \\
    --confirm-access-control-reviewed --confirm-backup-restore-tested \\
    --confirm-retention-plan --confirm-protocol-deviations-reconciled
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import stat
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import clean_research_dataset as CLEAN  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402

LOCKED_STATUS = "LOCKED_FOR_ANALYSIS"
BLOCKED_STATUS = "BLOCKED_DATA_LOCK_REQUIREMENTS"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CLOSED_QUERY_STATUSES = {
    "closed", "resolved", "verified", "complete", "done",
    "dong", "da_dong",
}


def _safe_rel(path: Optional[Path], base: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _is_filled(value: Optional[str]) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if not s:
        return False
    return not s.startswith("[CẦN")


def _read_query_log(query_log: Optional[Path]) -> Dict[str, Any]:
    """Đọc query log theo fail-closed: chỉ trạng thái đóng rõ ràng mới được qua."""
    if query_log is None:
        return {
            "path": None,
            "exists": False,
            "open_queries": [{"row": None, "status": "missing_file"}],
            "n_rows": 0,
            "sha256": None,
            "note": "Không cung cấp query log.",
        }
    query_log = Path(query_log)
    if not query_log.exists():
        return {
            "path": str(query_log),
            "exists": False,
            "open_queries": [{"row": None, "status": "missing_file"}],
            "n_rows": 0,
            "sha256": None,
            "note": "Không thấy query log.",
        }

    open_queries: List[Dict[str, Any]] = []
    n_rows = 0
    with query_log.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {
            RDI._normalize_header(name): name
            for name in (reader.fieldnames or [])
        }
        status_field = fields.get("status") or fields.get("trang_thai")
        if not status_field:
            return {
                "path": str(query_log),
                "exists": True,
                "open_queries": [{"row": None, "status": "missing_status_column"}],
                "n_rows": 0,
                "sha256": RDI._sha256_file(query_log),
                "note": "Query log thiếu cột status/trang_thai.",
            }
        for idx, row in enumerate(reader, 1):
            n_rows += 1
            status = RDI._normalize_header(row.get(status_field) or "")
            if status not in CLOSED_QUERY_STATUSES:
                open_queries.append({
                    "row": idx,
                    "issue_type": row.get("issue_type") or row.get("type") or "",
                    "status": status or "missing_status",
                })
    return {
        "path": str(query_log),
        "exists": True,
        "open_queries": open_queries,
        "n_rows": n_rows,
        "sha256": RDI._sha256_file(query_log),
        "note": "Query log đã đọc; manifest không lưu dữ liệu bệnh nhân.",
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _status_is_locked(value: Any) -> bool:
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G5-F5 — LOW): regex cũ chỉ
    # nhận đúng dấu ("CHƯA"/"KHÔNG"), lệch với bản ở run_g5_auto.py (chấp
    # nhận cả không dấu "CHUA"/"KHONG"). Đồng bộ để 3 hàm cùng tên
    # _status_is_locked() không kết luận khác nhau về cùng một chuỗi.
    text = str(value or "").strip().upper()
    if re.search(r"(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED", text):
        return False
    return bool(re.match(r"^LOCKED\b", text))


def _safe_child(base: Path, value: Any) -> Optional[Path]:
    if not str(value or "").strip():
        return None
    candidate = Path(str(value))
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(base.resolve())
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved


def _upstream_approval_report(
    study: str,
    out_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    """Xác minh G2/G4 bằng checkpoint + ledger hash, không tin cờ CLI tự khai."""
    g2_cp = _read_json(out_dir / "G2_checkpoint.json")
    g4_cp = _read_json(out_dir / "G4_checkpoint.json")
    meta = GC.load_study_meta(out_dir)
    g2_artifact = out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    g4_artifact = out_dir / f"G4_A5_SAP_FINAL_{study}.md"
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G10-01 — CRITICAL, bản sao thứ 3 của
    # cùng lỗi cũng đã vá ở g9_quality_gate.py/g10_quality_gate.py): _status_is_locked
    # đọc g2_status/g4_status — chuỗi mà run_g2_auto.py/run_g4_auto.py KHÔNG BAO GIỜ
    # ghi "LOCKED" vào. g4 vì vậy vĩnh viễn False, khóa dữ liệu (G5) không bao giờ mở
    # được cho một đề tài SAP đã ký hợp lệ thật. Dùng đúng hàm chấm trực tiếp.
    g2 = bool(
        GC.ledger_approved("G2", study, g2_artifact, repo_root=repo_root)
        and GC.g2_quality_contract_satisfied(g2_cp, meta)
    )
    g4 = GC.g4_quality_contract_satisfied(study, repo_root=repo_root)
    return {
        "G2": g2,
        "G4": g4,
        "g2_reason": (
            None
            if g2
            else GC.gate_block_reason(
                "G2", study, g2_artifact, repo_root=repo_root
            )
        ),
        "g4_reason": (
            None
            if g4
            else GC.gate_block_reason(
                "G4", study, g4_artifact, repo_root=repo_root
            )
        ),
        "g4_sap_version": g4_cp.get("g4_sap_version"),
    }


def _provenance_report(
    *,
    out_dir: Path,
    clean_data: Path,
    dictionary_path: Optional[Path],
    cleaning_report_path: Optional[Path],
    query_log: Optional[Path],
) -> Dict[str, Any]:
    """Liên kết intake -> cleaning -> dictionary/query bằng checksum."""
    intake_path = out_dir / "DATA_INTAKE_manifest.json"
    intake = _read_json(intake_path)
    cleaning = _read_json(cleaning_report_path) if cleaning_report_path else {}
    raw_path = _safe_child(out_dir, intake.get("raw_readonly_path"))
    clean_sha = RDI._sha256_file(clean_data) if clean_data.exists() else None
    dictionary_sha = (
        RDI._sha256_file(dictionary_path)
        if dictionary_path and dictionary_path.exists()
        else None
    )
    cleaning_sha = (
        RDI._sha256_file(cleaning_report_path)
        if cleaning_report_path and cleaning_report_path.exists()
        else None
    )
    query_sha = (
        RDI._sha256_file(query_log)
        if query_log and query_log.exists()
        else None
    )
    raw_sha = RDI._sha256_file(raw_path) if raw_path and raw_path.exists() else None
    clean_report_path = _safe_child(out_dir, cleaning.get("clean_dataset_path"))
    report_query_path = _safe_child(out_dir, cleaning.get("query_log"))
    report_dictionary_path = _safe_child(out_dir, cleaning.get("dictionary_path"))
    return {
        "intake_manifest": intake_path.name,
        "intake_ready": (
            intake.get("status") == RDI.READY_STATUS
            and intake.get("pii_scan", {}).get("passed") is True
        ),
        "raw_readonly": bool(
            raw_path
            and raw_path.exists()
            and raw_sha == intake.get("sha256")
            and not (raw_path.stat().st_mode & stat.S_IWUSR)
        ),
        "raw_sha256": raw_sha,
        "cleaning_report": (
            _safe_rel(cleaning_report_path, out_dir) if cleaning_report_path else None
        ),
        "cleaning_ready": (
            cleaning.get("status") == "CLEAN_READY_FOR_LOCK"
            and cleaning.get("ready_for_lock") is True
            and cleaning.get("dictionary_loaded") is True
        ),
        "clean_path_matches_report": bool(
            clean_report_path and clean_report_path == clean_data.resolve()
        ),
        "clean_sha256": clean_sha,
        "clean_hash_matches_report": clean_sha == cleaning.get("output_sha256"),
        "clean_source_matches_intake": (
            cleaning.get("source_sha256") == intake.get("sha256")
        ),
        "dictionary": _safe_rel(dictionary_path, out_dir) if dictionary_path else None,
        "dictionary_sha256": dictionary_sha,
        "dictionary_matches_report": bool(
            report_dictionary_path
            and dictionary_path
            and report_dictionary_path == dictionary_path.resolve()
            and cleaning.get("dictionary_sha256") == dictionary_sha
        ),
        "cleaning_report_sha256": cleaning_sha,
        "query_log_sha256": query_sha,
        "query_matches_report": bool(
            report_query_path
            and query_log
            and report_query_path == query_log.resolve()
            and cleaning.get("query_log_sha256") == query_sha
        ),
    }


def _build_blockers(
    *,
    clean_data: Path,
    lock_date: str,
    reviewer_role: str,
    reviewer_ref: str,
    sap_version: str,
    confirmations: Dict[str, bool],
    query_report: Dict[str, Any],
    pii_issues: List[Dict[str, Any]],
    upstream: Dict[str, Any],
    provenance: Dict[str, Any],
    operational_readiness: Dict[str, Any],
    row_count: int,
    column_count: int,
) -> List[str]:
    blockers: List[str] = []
    if clean_data.suffix.lower() not in RDI.SUPPORTED_SUFFIXES:
        blockers.append("unsupported_format: chỉ khóa CSV đã khử định danh")
    if not clean_data.exists():
        blockers.append("missing_clean_data")
    if not DATE_RE.match(str(lock_date or "")):
        blockers.append("missing_or_invalid_lock_date: YYYY-MM-DD")
    else:
        try:
            parsed_lock_date = datetime.strptime(lock_date, "%Y-%m-%d").date()
        except ValueError:
            blockers.append("invalid_lock_date")
        else:
            if parsed_lock_date > datetime.now().date():
                blockers.append("lock_date_in_future")
    if not GC.reviewer_role_satisfies_gate("G5", reviewer_role):
        blockers.append(
            "invalid_reviewer_role: cần DATA_MANAGER/DATA_GOVERNANCE_QA_REVIEWER hoặc PI"
        )
    if not _is_filled(reviewer_ref):
        blockers.append("missing_reviewer_ref_non_pii")
    if not _is_filled(sap_version):
        blockers.append("missing_sap_version")
    for key, value in confirmations.items():
        if not value:
            blockers.append(f"missing_confirmation:{key}")
    if not query_report.get("exists") or query_report.get("open_queries"):
        blockers.append("open_query_log")
    if pii_issues:
        blockers.append("pii_detected_in_clean_data")
    if operational_readiness.get("valid") is not True:
        blockers.append(
            "operational_readiness_not_verified:"
            + ",".join(operational_readiness.get("issues") or ["unknown"])
        )
    if row_count <= 0 or column_count <= 0:
        blockers.append("empty_clean_dataset")
    if not upstream.get("G2"):
        blockers.append("G2_not_approved_or_not_locked")
    if not upstream.get("G4"):
        blockers.append("G4_not_approved_or_not_locked")
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology CRITICAL):
    # tools/run_g4_auto.py CHỈ TỪNG ghi upstream["g4_sap_version"] là None
    # (G4 BLOCK) hoặc hardcode "1.0" (G4 sinh thành công) — không CLI flag,
    # không phép tính nào từng gán giá trị khác (đã grep toàn tools/*.py).
    # Nghĩa là check này chỉ thật sự kiểm "bác sĩ có gõ ĐÚNG hằng số 1.0 hay
    # không", KHÔNG kiểm được SAP có thật sự khớp phiên bản đang dùng để
    # khóa hay không. Xác nhận thực nghiệm bằng _build_blockers() thật:
    # (A) sap_version="1.0" khớp g4="1.0" -> không blocker (đúng, vô nghĩa).
    # (B) sap_version="2.0" (bác sĩ khai TRUNG THỰC một SAP đã tu chỉnh,
    #     đúng thực tế) trong khi g4="1.0" (vì run_g4_auto.py không có cách
    #     ghi khác) -> bị chặn dù khai ĐÚNG sự thật — reverse-tautology.
    # (C) sap_version="1.0" dù SAP thật đã là bản 2.0 (khai SAI để né kiểm)
    #     -> KHÔNG bị chặn, lọt qua trơn tru — thưởng khai gian.
    # Hạ từ BLOCK cứng xuống trường ghi-nhận-để-audit (không chặn) cho tới
    # khi run_g4_auto.py có --sap-version CLI thật (việc LỚN hơn, ngoài phạm
    # vi bản vá này). KHÔNG mất bảo vệ thật: chống SAP bị đổi SAU khi khóa
    # do một cơ chế ĐỘC LẬP khác đảm nhiệm — upstream["G4"] (dòng phía trên)
    # gọi GC.g4_quality_contract_satisfied()+GC.ledger_approved(), tức so
    # khớp hash/chữ ký mật mã trên chính nội dung SAP đã ký. Giá trị
    # upstream["g4_sap_version"] được ghi lại (không chặn) vào manifest ở
    # caller (_lock(), khóa "g4_sap_version_at_signing") để phục vụ audit.
    for key in (
        "intake_ready",
        "raw_readonly",
        "cleaning_ready",
        "clean_path_matches_report",
        "clean_hash_matches_report",
        "clean_source_matches_intake",
        "dictionary_matches_report",
        "query_matches_report",
    ):
        if provenance.get(key) is not True:
            blockers.append(f"provenance_failed:{key}")
    return blockers


def _write_manifest(out_dir: Path, manifest: Dict[str, Any]) -> Path:
    path = out_dir / "DATA_LOCK_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def _write_lock_memo(out_dir: Path, manifest: Dict[str, Any]) -> Path:
    path = out_dir / "DATA_LOCK_memo.md"
    lines = [
        "# Biên bản khóa dữ liệu phân tích\n",
        "| Nội dung | Giá trị |",
        "|---|---|",
        f"| Trạng thái | {manifest['status']} |",
        f"| Dataset khóa | `{manifest.get('locked_dataset_path') or '[CHƯA KHÓA]'}` |",
        f"| Ngày khóa | {manifest.get('lock_date') or '[CẦN BỔ SUNG]'} |",
        f"| Số quan sát | {manifest.get('row_count')} |",
        f"| Số biến | {manifest.get('column_count')} |",
        f"| SHA-256 | `{manifest.get('sha256') or '[CẦN BỔ SUNG]'}` |",
        f"| Query còn mở | {len(manifest['query_log']['open_queries'])} |",
        f"| Protocol/SAP áp dụng | SAP version {manifest.get('sap_version') or '[CẦN BỔ SUNG]'} |",
        f"| Vai trò xác nhận | {manifest.get('reviewer_role') or '[CẦN BỔ SUNG]'} |",
        f"| Mã tham chiếu người duyệt (không PII) | {manifest.get('reviewer_ref') or '[CẦN BỔ SUNG]'} |",
        f"| Data dictionary SHA-256 | `{manifest.get('dictionary_sha256') or '[CẦN BỔ SUNG]'}` |",
        f"| Cleaning report SHA-256 | `{manifest.get('cleaning_report_sha256') or '[CẦN BỔ SUNG]'}` |",
        f"| Query log SHA-256 | `{manifest.get('query_log_sha256') or '[CẦN BỔ SUNG]'}` |",
        (
            "| Hồ sơ vận hành SHA-256 | "
            f"`{manifest.get('operational_readiness_sha256') or '[CẦN BỔ SUNG]'}` |"
        ),
        f"| G2/G4 xác minh | {manifest.get('upstream_approvals')} |",
        "| Quy tắc mở khóa | Chỉ bằng biên bản mở khóa và phê duyệt phù hợp |",
        "",
        "> Cần bác sĩ/chủ nhiệm kiểm chứng. Không tự mở khóa sau khi xem kết quả.\n",
    ]
    if manifest["blockers"]:
        lines.extend(["## Lý do chưa khóa", ""])
        lines.extend(f"- {b}" for b in manifest["blockers"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def _update_meta(out_dir: Path, manifest: Dict[str, Any],
                 manifest_path: Path, memo_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["real_data_lock"] = {
        "status": manifest["status"],
        "manifest": str(manifest_path.relative_to(out_dir)),
        "memo": str(memo_path.relative_to(out_dir)),
        "locked_dataset_path": manifest.get("locked_dataset_path"),
        "lock_date": manifest.get("lock_date"),
        "reviewer_role": manifest.get("reviewer_role"),
        "reviewer_ref": manifest.get("reviewer_ref"),
        # Giữ khóa legacy cho trình lắp ráp cũ, nhưng chỉ lưu VAI TRÒ, không lưu họ tên.
        "approved_by": manifest.get("reviewer_role"),
        "sap_version": manifest.get("sap_version"),
        "sha256": manifest.get("sha256"),
        "dictionary_sha256": manifest.get("dictionary_sha256"),
        "cleaning_report_sha256": manifest.get("cleaning_report_sha256"),
        "query_log_sha256": manifest.get("query_log_sha256"),
        "operational_readiness_sha256": manifest.get(
            "operational_readiness_sha256"
        ),
        "rows": manifest.get("row_count"),
        "columns": manifest.get("column_count"),
        "blockers": manifest.get("blockers", []),
    }
    if manifest["status"] == LOCKED_STATUS:
        meta["data_lock_date"] = manifest["lock_date"]
        intake = meta.get("real_data_intake")
        if isinstance(intake, dict):
            intake["db_locked"] = True
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def lock_dataset(
    study: str,
    clean_data: Path,
    *,
    lock_date: str,
    reviewer_role: str,
    reviewer_ref: str,
    sap_version: str,
    query_log: Optional[Path] = None,
    dictionary_path: Optional[Path] = None,
    cleaning_report_path: Optional[Path] = None,
    operational_readiness_path: Optional[Path] = None,
    exports_root: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    confirm_deidentified: bool = False,
    confirm_clean_copy: bool = False,
    confirm_no_open_query: bool = False,
    confirm_sap_locked: bool = False,
    confirm_dictionary_crf_aligned: bool = False,
    confirm_access_control_reviewed: bool = False,
    confirm_backup_restore_tested: bool = False,
    confirm_retention_plan: bool = False,
    confirm_protocol_deviations_reconciled: bool = False,
    max_scan_rows: int = 5000,
) -> Dict[str, Any]:
    """Khóa bản dữ liệu phân tích nếu đủ xác nhận và không còn blocker."""
    study_id = RDI._sanitize_study(study)
    clean_data = Path(clean_data)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    repo_root = Path(repo_root) if repo_root else exports_root.parent
    out_dir = exports_root / study_id
    out_dir.mkdir(parents=True, exist_ok=True)
    dictionary_path = (
        Path(dictionary_path)
        if dictionary_path
        else out_dir / f"G5_REDCap_dictionary_{study_id}.csv"
    )
    cleaning_report_path = (
        Path(cleaning_report_path)
        if cleaning_report_path
        else out_dir / "DATA_CLEANING_report.json"
    )
    operational_readiness_path = (
        Path(operational_readiness_path)
        if operational_readiness_path
        else out_dir / G5Q.OPERATIONAL_READINESS_JSON
    )
    query_log = Path(query_log) if query_log else None

    # ★★ VÁ 2026-07-27 — CHẶN KHÓA ĐÈ. Đánh giá độc lập tái hiện được đòn nguy hiểm nhất
    # của cả hệ: xóa 25 ca bất lợi khỏi tập dữ liệu rồi CHẠY LẠI lock_dataset() — hệ ghi
    # đè manifest cũ, in "✅ checksum khớp", và phân tích hạ nguồn chạy trơn tru với
    # OR 1,485 → 4,858 (p 0,15 → <0,001). Đó chính là p-hacking, KÈM DẤU TÍCH XANH.
    # Một cơ chế "khóa dữ liệu" cho phép khóa lại vô điều kiện thì TỆ HƠN không có khóa,
    # vì nó cấp cho dữ liệu đã bị sửa một bằng chứng giả về tính bất biến.
    # Nay: đã khóa rồi thì KHÔNG khóa lại được trừ khi nội dung y hệt (idempotent).
    # Muốn khóa dữ liệu KHÁC phải là một quyết định CÓ CHỦ Ý, ghi lại được — hiện tại
    # đường duy nhất là bác sĩ tự tay xóa/đổi tên manifest cũ, để hành vi đó hiện trong
    # lịch sử thư mục thay vì diễn ra âm thầm bên trong một lệnh trông vô hại.
    _existing_manifest = out_dir / "DATA_LOCK_manifest.json"
    if _existing_manifest.exists():
        try:
            _old = json.loads(_existing_manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            _old = {}
        if _old.get("status") == LOCKED_STATUS:
            if _old.get("quality_contract_version") != G5Q.QUALITY_CONTRACT_VERSION:
                return {
                    **_old,
                    "status": BLOCKED_STATUS,
                    "analysis_allowed": False,
                    "blockers": [
                        "legacy_lock_manifest_requires_migration_and_human_review: "
                        f"thiếu {G5Q.QUALITY_CONTRACT_VERSION}"
                    ],
                }
            try:
                _new_sha = RDI._sha256_file(Path(clean_data))
            except OSError:
                _new_sha = None
            _old_locked_path = _safe_child(out_dir, _old.get("locked_dataset_path"))
            try:
                _old_locked_sha = (
                    RDI._sha256_file(_old_locked_path) if _old_locked_path else None
                )
            except OSError:
                _old_locked_sha = None
            if (
                _new_sha
                and _new_sha == _old.get("sha256")
                and _old_locked_sha == _old.get("sha256")
            ):
                return _old          # khóa lại đúng y file cũ — vô hại, trả nguyên trạng
            return {
                **_old,
                "status": BLOCKED_STATUS,
                "blockers": [
                    "ĐÃ KHÓA TRƯỚC ĐÓ — TỪ CHỐI KHÓA ĐÈ. Đề tài này đã có DATA_LOCK_manifest.json "
                    f"ở trạng thái {LOCKED_STATUS} (khóa lúc {_old.get('locked_at')}, "
                    f"sha256 {str(_old.get('sha256'))[:12]}…), nhưng file dữ liệu đưa vào lần này "
                    f"có sha256 {str(_new_sha)[:12]}… — tức NỘI DUNG ĐÃ KHÁC. Khóa đè sẽ xóa dấu "
                    "vết bản khóa cũ và hợp thức hóa một tập dữ liệu đã bị thay đổi sau khi khóa "
                    "(chính là p-hacking có dấu tích xanh). Nếu thật sự cần khóa một tập khác, "
                    "hãy TỰ TAY lưu/đổi tên manifest cũ trước, để việc đó hiện trong lịch sử.",
                ],
            }

    locked_at = datetime.now().isoformat(timespec="seconds")
    # Cột đã khai "type": "date" trong data dictionary (vd visit_date) không
    # phải PII cần xóa — chỉ miễn mẫu "date", các mẫu PII khác (SĐT/email/CCCD)
    # vẫn quét bình thường. Cùng cơ chế đã áp cho import_dataset()/clean_dataset()
    # ở import_real_dataset.py và pseudonymize_research_dataset.py; thiếu bước
    # này ở đây làm lock_dataset() tự chặn dữ liệu ĐÃ được clean_dataset() cho
    # qua với đúng dictionary, chỉ vì scan lại một lần nữa mà không biết dictionary.
    _lock_dictionary = CLEAN._load_dictionary(dictionary_path)
    _lock_exempt_date_columns = frozenset(
        RDI._normalize_header(str(rule["name"]))
        for rule in (_lock_dictionary.get("variables") or [])
        if isinstance(rule, dict) and rule.get("type") == "date" and rule.get("name")
    )
    profile = (
        RDI._scan_csv(
            clean_data,
            max_scan_rows=max_scan_rows,
            exempt_date_columns=_lock_exempt_date_columns,
        )
        if clean_data.exists() and clean_data.suffix.lower() in RDI.SUPPORTED_SUFFIXES
        else {"rows": 0, "columns": [], "issues": []}
    )
    pii_issues = list(profile.get("issues") or [])
    query_report = _read_query_log(query_log)
    confirmations = {
        "deidentified": confirm_deidentified,
        "clean_copy_not_raw": confirm_clean_copy,
        "no_open_query": confirm_no_open_query,
        "sap_locked": confirm_sap_locked,
        "dictionary_crf_aligned": confirm_dictionary_crf_aligned,
        "access_control_reviewed": confirm_access_control_reviewed,
        "backup_restore_tested": confirm_backup_restore_tested,
        "retention_plan_confirmed": confirm_retention_plan,
        "protocol_deviations_reconciled": confirm_protocol_deviations_reconciled,
    }
    upstream = _upstream_approval_report(study_id, out_dir, repo_root)
    provenance = _provenance_report(
        out_dir=out_dir,
        clean_data=clean_data,
        dictionary_path=dictionary_path,
        cleaning_report_path=cleaning_report_path,
        query_log=query_log,
    )
    operational_readiness = G5Q.evaluate_operational_readiness(
        operational_readiness_path
    )
    blockers = _build_blockers(
        clean_data=clean_data,
        lock_date=lock_date,
        reviewer_role=reviewer_role,
        reviewer_ref=reviewer_ref,
        sap_version=sap_version,
        confirmations=confirmations,
        query_report=query_report,
        pii_issues=pii_issues,
        upstream=upstream,
        provenance=provenance,
        operational_readiness=operational_readiness,
        row_count=int(profile.get("rows") or 0),
        column_count=len(profile.get("columns") or []),
    )

    manifest: Dict[str, Any] = {
        "kind": "analysis_dataset_lock_manifest",
        "quality_contract_version": G5Q.QUALITY_CONTRACT_VERSION,
        "study": study_id,
        "status": LOCKED_STATUS if not blockers else BLOCKED_STATUS,
        "locked_at": locked_at,
        "source_clean_filename": clean_data.name,
        "locked_dataset_path": None,
        "lock_date": lock_date,
        "reviewer_role": reviewer_role,
        "reviewer_ref": reviewer_ref,
        # Trường legacy chỉ chứa vai trò để không lưu tên người.
        "approved_by": reviewer_role,
        "sap_version": sap_version,
        # THÊM 2026-07-31 (audit tautology vòng 2): ghi lại (KHÔNG chặn) giá
        # trị g4_sap_version thật tại thời điểm khóa để phục vụ audit thủ
        # công sau này — xem chú thích tại _build_blockers() vì sao trường
        # này không còn tham gia blockers.
        "g4_sap_version_at_signing": upstream.get("g4_sap_version"),
        "row_count": int(profile.get("rows") or 0),
        "column_count": len(profile.get("columns") or []),
        "columns": profile.get("columns") or [],
        "sha256": None,
        "query_log": query_report,
        "query_log_sha256": provenance.get("query_log_sha256"),
        "dictionary_path": provenance.get("dictionary"),
        "dictionary_sha256": provenance.get("dictionary_sha256"),
        "cleaning_report": provenance.get("cleaning_report"),
        "cleaning_report_sha256": provenance.get("cleaning_report_sha256"),
        "operational_readiness": _safe_rel(operational_readiness_path, out_dir),
        "operational_readiness_sha256": operational_readiness.get("sha256"),
        "raw_sha256": provenance.get("raw_sha256"),
        "provenance": provenance,
        "upstream_approvals": {
            "G2": upstream.get("G2") is True,
            "G4": upstream.get("G4") is True,
        },
        "confirmations": confirmations,
        "pii_scan": {
            "passed": not pii_issues,
            "n_blockers": len(pii_issues),
            "issues": pii_issues,
        },
        "blockers": blockers,
        "analysis_allowed": not blockers,
        "rules": [
            "Dataset khóa là bản clean copy, không phải raw.",
            "Dataset khóa đặt read-only và có SHA-256.",
            "Mọi phân tích chính phải dùng đúng file khóa trong manifest.",
            "Không mở khóa/sửa sau khi xem kết quả nếu không có biên bản.",
            "G5 chỉ qua sau khi người quản trị dữ liệu/PI phê duyệt checkpoint bằng approval ledger.",
        ],
    }

    locked_path: Optional[Path] = None
    if not blockers:
        sha = RDI._sha256_file(clean_data)
        lock_dir = out_dir / "05_clean_locked"
        lock_dir.mkdir(parents=True, exist_ok=True)
        locked_path = lock_dir / f"{RDI._safe_stem(clean_data)}.{sha[:12]}.locked.csv"
        if not locked_path.exists():
            shutil.copy2(clean_data, locked_path)
        os.chmod(locked_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        manifest["locked_dataset_path"] = str(locked_path.relative_to(out_dir))
        manifest["sha256"] = sha

    manifest_path = _write_manifest(out_dir, manifest)
    memo_path = _write_lock_memo(out_dir, manifest)
    _update_meta(out_dir, manifest, manifest_path, memo_path)
    checkpoint_path = out_dir / "G5_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    if not checkpoint:
        checkpoint = {
            "gate": "G5",
            "study": study_id,
            "guardrail": "⚠ BLOCKED — thiếu bộ công cụ G5",
        }
    checkpoint["quality_contract_version"] = G5Q.QUALITY_CONTRACT_VERSION
    checkpoint["data_lock_manifest"] = manifest_path.name
    checkpoint["data_lock_memo"] = memo_path.name
    checkpoint["database_lock_status"] = manifest["status"]
    if manifest["status"] == LOCKED_STATUS:
        checkpoint.update(
            {
                "g5_status": "LOCKED",
                "data_lock_date": manifest["lock_date"],
                "locked_dataset_sha256": manifest["sha256"],
                "locked_dataset_path": manifest["locked_dataset_path"],
                "raw_dataset_sha256": manifest.get("raw_sha256"),
                "data_dictionary_sha256": manifest.get("dictionary_sha256"),
                "cleaning_report_sha256": manifest.get(
                    "cleaning_report_sha256"
                ),
                "query_log_sha256": manifest.get("query_log_sha256"),
                "operational_readiness_sha256": manifest.get(
                    "operational_readiness_sha256"
                ),
                "reviewer_role": reviewer_role,
                "reviewer_ref": reviewer_ref,
                "sap_version": sap_version,
            }
        )
    else:
        checkpoint["g5_status"] = "PENDING"
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )
    quality = G5Q.evaluate_study(
        study_id,
        out_dir,
        repo_root=repo_root,
        write=True,
    )
    manifest["g5_quality_status"] = quality["status"]
    # Ghi lại trạng thái chất lượng vào manifest blocker/lock để audit một lệnh
    # thấy ngay; manifest vẫn chưa được người thật ký ở bước này.
    _write_manifest(out_dir, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Khóa dataset phân tích đã làm sạch cho nghiên cứu y khoa.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--clean-data", required=True, help="CSV clean đã khử định danh")
    parser.add_argument("--query-log", default=None, help="CSV query log đã đóng query")
    parser.add_argument(
        "--dictionary",
        default=None,
        help="REDCap/data dictionary G5 đã chốt (mặc định tự tìm trong exports/<study>)",
    )
    parser.add_argument(
        "--cleaning-report",
        default=None,
        help="DATA_CLEANING_report.json (mặc định tự tìm trong exports/<study>)",
    )
    parser.add_argument(
        "--operational-readiness",
        default=None,
        help=(
            f"{G5Q.OPERATIONAL_READINESS_JSON} đã VERIFIED "
            "(mặc định tự tìm trong exports/<study>)"
        ),
    )
    parser.add_argument("--lock-date", required=True, help="Ngày khóa YYYY-MM-DD")
    parser.add_argument(
        "--reviewer-role",
        required=True,
        help="DATA_MANAGER/DATA_GOVERNANCE_QA_REVIEWER hoặc PI",
    )
    parser.add_argument(
        "--reviewer-ref",
        required=True,
        help="Mã tham chiếu người duyệt, không ghi họ tên/PII",
    )
    parser.add_argument("--sap-version", required=True, help="Phiên bản SAP đã khóa")
    parser.add_argument("--confirm-deidentified", action="store_true")
    parser.add_argument("--confirm-clean-copy", action="store_true")
    parser.add_argument("--confirm-no-open-query", action="store_true")
    parser.add_argument("--confirm-sap-locked", action="store_true")
    parser.add_argument("--confirm-dictionary-crf-aligned", action="store_true")
    parser.add_argument("--confirm-access-control-reviewed", action="store_true")
    parser.add_argument("--confirm-backup-restore-tested", action="store_true")
    parser.add_argument("--confirm-retention-plan", action="store_true")
    parser.add_argument("--confirm-protocol-deviations-reconciled", action="store_true")
    parser.add_argument("--max-scan-rows", type=int, default=5000)
    args = parser.parse_args()

    manifest = lock_dataset(
        args.study,
        Path(args.clean_data),
        lock_date=args.lock_date,
        reviewer_role=args.reviewer_role,
        reviewer_ref=args.reviewer_ref,
        sap_version=args.sap_version,
        query_log=Path(args.query_log) if args.query_log else None,
        dictionary_path=Path(args.dictionary) if args.dictionary else None,
        cleaning_report_path=(
            Path(args.cleaning_report) if args.cleaning_report else None
        ),
        operational_readiness_path=(
            Path(args.operational_readiness)
            if args.operational_readiness
            else None
        ),
        confirm_deidentified=args.confirm_deidentified,
        confirm_clean_copy=args.confirm_clean_copy,
        confirm_no_open_query=args.confirm_no_open_query,
        confirm_sap_locked=args.confirm_sap_locked,
        confirm_dictionary_crf_aligned=args.confirm_dictionary_crf_aligned,
        confirm_access_control_reviewed=args.confirm_access_control_reviewed,
        confirm_backup_restore_tested=args.confirm_backup_restore_tested,
        confirm_retention_plan=args.confirm_retention_plan,
        confirm_protocol_deviations_reconciled=(
            args.confirm_protocol_deviations_reconciled
        ),
        max_scan_rows=args.max_scan_rows,
    )
    print(f"DATA_LOCK: {manifest['status']}")
    print(f"rows={manifest['row_count']} columns={manifest['column_count']}")
    if manifest["status"] == LOCKED_STATUS:
        print(f"locked_dataset={manifest['locked_dataset_path']}")
        print("Tiếp theo: dùng đúng file locked này cho phân tích chính G6/G7.")
        return 0
    print("BLOCKED: chưa đủ điều kiện khóa dữ liệu; xem DATA_LOCK_manifest.json và DATA_LOCK_memo.md.")
    for blocker in manifest["blockers"]:
        print(f"- {blocker}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
