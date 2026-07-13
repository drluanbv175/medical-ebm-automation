#!/usr/bin/env python3
"""Khóa dataset phân tích đã làm sạch, có audit trail và không PII.

Công cụ này chạy SAU bước intake/làm sạch và TRƯỚC phân tích chính G6/G7.
Nó không sửa dữ liệu gốc; chỉ copy bản clean đã được xác nhận sang
`05_clean_locked/`, đặt read-only, tạo lock memo/manifest và cập nhật
`study_meta.json` khi đủ xác nhận thật.

Ví dụ:
  python3 tools/lock_analysis_dataset.py --study KKB-HAI-LONG-2026 \\
    --clean-data df_clean.csv --query-log query_log.csv \\
    --lock-date 2026-07-13 --approved-by "PI Nguyen Van A" --sap-version 1.0 \\
    --confirm-deidentified --confirm-clean-copy --confirm-no-open-query --confirm-sap-locked
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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402

LOCKED_STATUS = "LOCKED_FOR_ANALYSIS"
BLOCKED_STATUS = "BLOCKED_DATA_LOCK_REQUIREMENTS"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    """Đọc query log và phát hiện query còn mở."""
    if query_log is None:
        return {
            "path": None,
            "exists": False,
            "open_queries": [],
            "n_rows": 0,
            "note": "Không cung cấp query log; chỉ chấp nhận nếu có xác nhận no-open-query.",
        }
    query_log = Path(query_log)
    if not query_log.exists():
        return {
            "path": str(query_log),
            "exists": False,
            "open_queries": [{"row": None, "status": "missing_file"}],
            "n_rows": 0,
            "note": "Không thấy query log.",
        }

    open_queries: List[Dict[str, Any]] = []
    n_rows = 0
    with query_log.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            n_rows += 1
            status = str(row.get("status") or row.get("trang_thai") or "").strip().lower()
            if status in {"open", "pending", "unresolved", "reopen", "mở", "dang_mo"}:
                open_queries.append({
                    "row": idx,
                    "issue_type": row.get("issue_type") or row.get("type") or "",
                    "status": status,
                })
    return {
        "path": str(query_log),
        "exists": True,
        "open_queries": open_queries,
        "n_rows": n_rows,
        "note": "Query log đã đọc; manifest không lưu dữ liệu bệnh nhân.",
    }


def _build_blockers(*, clean_data: Path, lock_date: str, approved_by: str, sap_version: str,
                    confirmations: Dict[str, bool], query_report: Dict[str, Any],
                    pii_issues: List[Dict[str, Any]]) -> List[str]:
    blockers: List[str] = []
    if clean_data.suffix.lower() not in RDI.SUPPORTED_SUFFIXES:
        blockers.append("unsupported_format: chỉ khóa CSV đã khử định danh")
    if not clean_data.exists():
        blockers.append("missing_clean_data")
    if not DATE_RE.match(str(lock_date or "")):
        blockers.append("missing_or_invalid_lock_date: YYYY-MM-DD")
    if not _is_filled(approved_by):
        blockers.append("missing_approved_by")
    if not _is_filled(sap_version):
        blockers.append("missing_sap_version")
    for key, value in confirmations.items():
        if not value:
            blockers.append(f"missing_confirmation:{key}")
    if query_report.get("open_queries"):
        blockers.append("open_query_log")
    if pii_issues:
        blockers.append("pii_detected_in_clean_data")
    return blockers


def _write_manifest(out_dir: Path, manifest: Dict[str, Any]) -> Path:
    path = out_dir / "DATA_LOCK_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
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
        f"| Người xác nhận | {manifest.get('approved_by') or '[CẦN BỔ SUNG]'} |",
        "| Quy tắc mở khóa | Chỉ bằng biên bản mở khóa và phê duyệt phù hợp |",
        "",
        "> Cần bác sĩ/chủ nhiệm kiểm chứng. Không tự mở khóa sau khi xem kết quả.\n",
    ]
    if manifest["blockers"]:
        lines.extend(["## Lý do chưa khóa", ""])
        lines.extend(f"- {b}" for b in manifest["blockers"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
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
        "approved_by": manifest.get("approved_by"),
        "sap_version": manifest.get("sap_version"),
        "sha256": manifest.get("sha256"),
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
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def lock_dataset(study: str, clean_data: Path, *, lock_date: str, approved_by: str,
                 sap_version: str, query_log: Optional[Path] = None,
                 exports_root: Optional[Path] = None,
                 confirm_deidentified: bool = False,
                 confirm_clean_copy: bool = False,
                 confirm_no_open_query: bool = False,
                 confirm_sap_locked: bool = False,
                 max_scan_rows: int = 5000) -> Dict[str, Any]:
    """Khóa bản dữ liệu phân tích nếu đủ xác nhận và không còn blocker."""
    study_id = RDI._sanitize_study(study)
    clean_data = Path(clean_data)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    out_dir = exports_root / study_id
    out_dir.mkdir(parents=True, exist_ok=True)

    locked_at = datetime.now().isoformat(timespec="seconds")
    profile = (
        RDI._scan_csv(clean_data, max_scan_rows=max_scan_rows)
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
    }
    blockers = _build_blockers(
        clean_data=clean_data,
        lock_date=lock_date,
        approved_by=approved_by,
        sap_version=sap_version,
        confirmations=confirmations,
        query_report=query_report,
        pii_issues=pii_issues,
    )

    manifest: Dict[str, Any] = {
        "kind": "analysis_dataset_lock_manifest",
        "study": study_id,
        "status": LOCKED_STATUS if not blockers else BLOCKED_STATUS,
        "locked_at": locked_at,
        "source_clean_filename": clean_data.name,
        "locked_dataset_path": None,
        "lock_date": lock_date,
        "approved_by": approved_by,
        "sap_version": sap_version,
        "row_count": int(profile.get("rows") or 0),
        "column_count": len(profile.get("columns") or []),
        "columns": profile.get("columns") or [],
        "sha256": None,
        "query_log": query_report,
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
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Khóa dataset phân tích đã làm sạch cho nghiên cứu y khoa.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--clean-data", required=True, help="CSV clean đã khử định danh")
    parser.add_argument("--query-log", default=None, help="CSV query log đã đóng query")
    parser.add_argument("--lock-date", required=True, help="Ngày khóa YYYY-MM-DD")
    parser.add_argument("--approved-by", required=True, help="Người xác nhận/chủ nhiệm")
    parser.add_argument("--sap-version", required=True, help="Phiên bản SAP đã khóa")
    parser.add_argument("--confirm-deidentified", action="store_true")
    parser.add_argument("--confirm-clean-copy", action="store_true")
    parser.add_argument("--confirm-no-open-query", action="store_true")
    parser.add_argument("--confirm-sap-locked", action="store_true")
    parser.add_argument("--max-scan-rows", type=int, default=5000)
    args = parser.parse_args()

    manifest = lock_dataset(
        args.study,
        Path(args.clean_data),
        lock_date=args.lock_date,
        approved_by=args.approved_by,
        sap_version=args.sap_version,
        query_log=Path(args.query_log) if args.query_log else None,
        confirm_deidentified=args.confirm_deidentified,
        confirm_clean_copy=args.confirm_clean_copy,
        confirm_no_open_query=args.confirm_no_open_query,
        confirm_sap_locked=args.confirm_sap_locked,
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
