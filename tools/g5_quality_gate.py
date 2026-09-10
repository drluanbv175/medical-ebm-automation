#!/usr/bin/env python3
"""Hợp đồng chất lượng G5 cho quản trị và khóa dữ liệu nghiên cứu.

G5 không được coi là đạt chỉ vì đã sinh CRF hoặc vì checkpoint chứa chữ
``LOCKED``. Cổng có bốn trạng thái:

- ``BLOCKED``: lỗi liêm chính, provenance hoặc khóa dữ liệu.
- ``DRAFT_READY_NEEDS_REAL_DATA``: bộ công cụ đã sẵn sàng nhưng chưa có dữ liệu.
- ``READY_FOR_G5_APPROVAL``: dataset đã khóa kỹ thuật, chờ người có thẩm quyền ký.
- ``PASS_G5_DATA_LOCKED``: khóa kỹ thuật hợp lệ và approval ledger khớp hash.

Module chỉ đọc dữ liệu khử định danh và metadata kiểm toán; không lưu giá trị
người tham gia trong báo cáo chất lượng.
"""

from __future__ import annotations

import csv
import json
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

import gate_contract as GC
import import_real_dataset as RDI

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_READY_NEEDS_REAL_DATA"
STATUS_READY = "READY_FOR_G5_APPROVAL"
STATUS_LOCKED = "PASS_G5_DATA_LOCKED"
QUALITY_CONTRACT_VERSION = "G5-2026.1"

REPORT_JSON = "G5_QUALITY_REPORT.json"
REPORT_MD = "G5_QUALITY_REPORT.md"
OPERATIONAL_READINESS_JSON = "G5_OPERATIONAL_READINESS.json"

_LOCKED_STATUS = "LOCKED_FOR_ANALYSIS"
_INTAKE_READY_STATUS = "READY_FOR_CLEANING_NOT_LOCKED"
_CLEAN_READY_STATUS = "CLEAN_READY_FOR_LOCK"
_CLOSED_QUERY_STATUSES = {
    "closed",
    "resolved",
    "verified",
    "complete",
    "done",
    "dong",
    "da_dong",
}
_DIRECT_IDENTIFIER_TOKENS = {
    "name",
    "full_name",
    "patient_name",
    "phone",
    "email",
    "address",
    "dob",
    "date_of_birth",
    "cccd",
    "cmnd",
    "passport",
    "mrn",
    "medical_record_number",
    "patient_id",
    "bhyt",
    "ssn",
    "ho_ten",
    "ngay_sinh",
    "dia_chi",
    "so_dien_thoai",
}
_DIRECT_IDENTIFIER_COMPONENTS = {
    "phone",
    "email",
    "address",
    "dob",
    "cccd",
    "cmnd",
    "passport",
    "mrn",
    "bhyt",
    "ssn",
}
_REQUIRED_DMP_TOKENS = (
    "CẤU TRÚC CRF",
    "REDCAP DATA DICTIONARY",
    "LUẬT KIỂM TRA DỮ LIỆU",
    "AUDIT TRAIL",
    "KHỬ ĐỊNH DANH",
    "PHÂN QUYỀN",
    "SAO LƯU",
    "LƯU TRỮ",
    "KHÓA CƠ SỞ DỮ LIỆU",
    "CHIA SẺ DỮ LIỆU",
    "ICH E6(R3)",
)

STANDARDS_BASIS = (
    {
        "standard": "ICH E6(R3), Principles and Annex 1",
        "scope": (
            "Data governance, metadata/audit trail, correction có lý do, "
            "finalisation trước phân tích, bảo mật và validation hệ thống"
        ),
        "url": (
            "https://www.ema.europa.eu/en/ich-e6-good-clinical-practice-"
            "scientific-guideline"
        ),
    },
    {
        "standard": "FDA Electronic Systems, Electronic Records and Signatures (2024)",
        "scope": "Hồ sơ điện tử tin cậy, audit trail và chữ ký điện tử",
        "url": (
            "https://www.fda.gov/regulatory-information/search-fda-guidance-"
            "documents/electronic-systems-electronic-records-and-electronic-"
            "signatures-clinical-investigations-questions"
        ),
    },
    {
        "standard": "CDISC CDASH",
        "scope": "Metadata và cấu trúc biến thu thập dữ liệu lâm sàng",
        "url": "https://www.cdisc.org/standards/foundational/cdash",
    },
    {
        "standard": "NIH Data Management and Sharing Policy / 2026 format",
        "scope": "Quản lý, bảo tồn, quyền riêng tư, repository và giám sát chia sẻ",
        "url": (
            "https://www.grants.nih.gov/policy-and-compliance/policy-topics/"
            "sharing-policies/dms/writing-dms-plan"
        ),
    },
    {
        "standard": "FAIR Guiding Principles",
        "scope": "Dữ liệu và metadata tìm được, truy cập được, liên thông và tái sử dụng",
        "pmid": "26978244",
        "doi": "10.1038/sdata.2016.18",
    },
)


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str,
) -> Dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256(path: Path) -> Optional[str]:
    try:
        return RDI._sha256_file(path)
    except OSError:
        return None


def _guardrail_ok(checkpoint: Mapping[str, Any]) -> bool:
    guardrail = checkpoint.get("guardrail")
    if isinstance(guardrail, Mapping):
        return guardrail.get("passed") is True
    text = str(guardrail or "").strip().upper()
    return "PASS" in text and not any(
        token in text for token in ("FAIL", "LỖI", "ERROR", "BLOCK")
    )


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


def _normalise_key(value: Any) -> str:
    return RDI._normalize_header(str(value or ""))


def _read_redcap_dictionary(path: Path) -> Dict[str, Any]:
    """Đọc data dictionary CSV thật và trả kiểm tra cấu trúc không chứa dữ liệu."""
    if not path.exists():
        return {"rows": 0, "names": [], "issues": ["missing_dictionary"]}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"rows": 0, "names": [], "issues": ["unreadable_dictionary"]}

    headers = {_normalise_key(name): name for name in (reader.fieldnames or [])}
    required_headers = {
        "variable_field_name",
        "form_name",
        "field_type",
        "field_label",
        "identifier?",
    }
    missing_headers = sorted(required_headers - set(headers))
    name_header = next(
        (
            headers[key]
            for key in ("variable_field_name", "variable_name", "field_name", "variable")
            if key in headers
        ),
        None,
    )
    issues: list[str] = []
    if missing_headers:
        issues.append(f"missing_core_headers:{missing_headers}")
    if not name_header:
        issues.append("missing_variable_field_name_header")
        return {"rows": len(rows), "names": [], "issues": issues}

    names = [str(row.get(name_header) or "").strip() for row in rows]
    empty = [idx + 2 for idx, name in enumerate(names) if not name]
    duplicates = sorted({name for name in names if name and names.count(name) > 1})
    pii_names = sorted(
        {
            name
            for name in names
            if _normalise_key(name) in _DIRECT_IDENTIFIER_TOKENS
            or set(_normalise_key(name).split("_"))
            & _DIRECT_IDENTIFIER_COMPONENTS
        }
    )
    identifier_header = headers.get("identifier?")
    flagged_identifiers = [
        idx + 2
        for idx, row in enumerate(rows)
        if identifier_header
        and str(row.get(identifier_header) or "").strip().casefold()
        in {"1", "true", "y", "yes"}
    ]
    if empty:
        issues.append(f"empty_variable_name_rows:{empty[:10]}")
    if duplicates:
        issues.append(f"duplicate_variable_names:{duplicates[:10]}")
    if pii_names:
        issues.append(f"direct_identifier_fields:{pii_names[:10]}")
    if flagged_identifiers:
        issues.append(f"redcap_identifier_rows:{flagged_identifiers[:10]}")
    if not names:
        issues.append("empty_dictionary")
    return {
        "rows": len(rows),
        "names": names,
        "issues": issues,
        "headers": list(reader.fieldnames or []),
    }


def _query_log_report(path: Optional[Path]) -> Dict[str, Any]:
    if path is None or not path.exists():
        return {"rows": 0, "open": 0, "issues": ["missing_query_log"]}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        return {"rows": 0, "open": 0, "issues": ["unreadable_query_log"]}
    fields = {_normalise_key(name): name for name in (reader.fieldnames or [])}
    status_header = fields.get("status") or fields.get("trang_thai")
    issues: list[str] = []
    if not status_header:
        issues.append("missing_query_status_column")
        return {"rows": len(rows), "open": len(rows), "issues": issues}
    unresolved = [
        idx + 2
        for idx, row in enumerate(rows)
        if _normalise_key(row.get(status_header)) not in _CLOSED_QUERY_STATUSES
    ]
    if unresolved:
        issues.append(f"query_not_closed_rows:{unresolved[:20]}")
    return {"rows": len(rows), "open": len(unresolved), "issues": issues}


def _readonly(path: Optional[Path]) -> bool:
    if path is None or not path.exists():
        return False
    try:
        return not bool(path.stat().st_mode & stat.S_IWUSR)
    except OSError:
        return False


def evaluate_operational_readiness(path: Path) -> Dict[str, Any]:
    """Kiểm hồ sơ vận hành G5 mà không đọc dữ liệu người tham gia."""
    payload = _read_json(path)
    issues: list[str] = []
    if not payload:
        return {"valid": False, "issues": ["missing_or_invalid_record"], "sha256": None}
    if payload.get("status") != "VERIFIED":
        issues.append("status_not_verified")
    access = payload.get("access_control_review")
    access = access if isinstance(access, Mapping) else {}
    if not (
        access.get("completed") is True
        and access.get("least_privilege_confirmed") is True
    ):
        issues.append("access_control_not_verified")
    backup = payload.get("backup_restore_test")
    backup = backup if isinstance(backup, Mapping) else {}
    if not (
        backup.get("completed") is True
        and backup.get("restore_verified") is True
        and backup.get("checksum_verified") is True
    ):
        issues.append("backup_restore_not_verified")
    retention = payload.get("retention_plan")
    retention = retention if isinstance(retention, Mapping) else {}
    if not (
        retention.get("confirmed") is True
        and str(retention.get("retention_rule") or "").strip()
    ):
        issues.append("retention_plan_not_confirmed")
    deviations = payload.get("protocol_deviations")
    deviations = deviations if isinstance(deviations, Mapping) else {}
    try:
        open_count = int(deviations.get("open_count"))
    except (TypeError, ValueError):
        open_count = -1
    if not (
        deviations.get("reconciled") is True
        and open_count == 0
    ):
        issues.append("protocol_deviations_not_reconciled")
    reviewer_role = str(payload.get("reviewer_role") or "")
    if not GC.reviewer_role_satisfies_gate("G5", reviewer_role):
        issues.append("invalid_reviewer_role")
    if not str(payload.get("reviewer_ref") or "").strip():
        issues.append("missing_reviewer_ref")
    for field, section in (
        ("reviewed_at", access),
        ("tested_at", backup),
    ):
        value = str(section.get(field) or "")
        try:
            parsed = datetime.fromisoformat(value).date()
        except ValueError:
            issues.append(f"invalid_{field}")
        else:
            # reviewed_at/tested_at là ngày lịch không kèm múi giờ, do người
            # duyệt gõ tay theo NGÀY ĐỊA PHƯƠNG trên máy họ (giống quy ước
            # lock_date ở lock_analysis_dataset.py) — so với UTC sẽ báo sai
            # "future_" với múi giờ trước UTC (VD UTC+7) suốt khoảng nửa đêm
            # đến rạng sáng giờ địa phương.
            if parsed > datetime.now().date():
                issues.append(f"future_{field}")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raw_text = ""
    if "[CẦN" in raw_text or "[REQUIRE_HUMAN" in raw_text:
        issues.append("unresolved_placeholder")
    return {
        "valid": not issues,
        "issues": issues,
        "sha256": _sha256(path),
        "reviewer_group": GC.role_group_for(reviewer_role),
    }


_NGUONG_NOI_DUNG_THAT_SAU_NHAN = 20  # ký tự, sau khi đã bỏ mọi placeholder


def _dmp_noi_dung_thieu_duoi_nhan(dmp_text: str, tokens: Iterable[str]) -> list:
    """Với MỖI nhãn trong `tokens` đã XUẤT HIỆN trong `dmp_text`, kiểm đoạn văn bản
    NGAY SAU nhãn đó tới nhãn KẾ TIẾP (theo đúng vị trí thật trong văn bản, không
    theo thứ tự khai trong tuple) — hoặc hết văn bản nếu là nhãn cuối. Trả về danh
    sách nhãn mà đoạn đó RỖNG hoặc chỉ toàn placeholder `[CẦN...]`/`[REQUIRE_HUMAN...]`.

    Sinh ra để đóng khoảng trống G5-F3 (audit 2026-07-30, vá thật 10/09/2026): trước
    đây G5-AUTO-03 chỉ hỏi "nhãn có xuất hiện ở đâu đó trong toàn văn bản không" —
    một DMP mà mọi mục đều rỗng/placeholder vẫn PASS miễn 11 chuỗi nhãn còn nằm đâu
    đó (vd trong mục lục). Khoá này đòi thêm NỘI DUNG THẬT đứng ngay sau nhãn, theo
    đúng khuôn BH97 (`approve_gate._g4_sections_still_draft`): phân biệt "còn thiếu
    một vài mục" (không bắt ở đây — G5-AUTO-03 chỉ xét 11 nhãn bắt buộc) với
    "nhãn có mặt nhưng thân mục trống rỗng" (BLOCK).

    Không tính token VẮNG MẶT hoàn toàn ở đây — đã có `missing_dmp` xử lý riêng.
    """
    lower = dmp_text.casefold()
    positions = []
    for tok in tokens:
        idx = lower.find(tok.casefold())
        if idx != -1:
            positions.append((idx, tok))
    positions.sort(key=lambda cap: cap[0])
    thieu_noi_dung = []
    for i, (idx, tok) in enumerate(positions):
        start = idx + len(tok)
        end = positions[i + 1][0] if i + 1 < len(positions) else len(dmp_text)
        than_muc = dmp_text[start:end]
        that = re.sub(r"\[(CẦN|REQUIRE_HUMAN)[^\]]*\]", "", than_muc, flags=re.IGNORECASE).strip()
        if len(that) < _NGUONG_NOI_DUNG_THAT_SAU_NHAN:
            thieu_noi_dung.append(tok)
    return thieu_noi_dung


def _contains_placeholder(paths: Iterable[Path]) -> bool:
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "[CẦN" in text or "[REQUIRE_HUMAN" in text:
            return True
    return False


def _write_markdown(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# Báo cáo chất lượng G5",
        "",
        f"- Hợp đồng: `{report.get('quality_contract_version')}`",
        f"- Trạng thái: **{report.get('status')}**",
        f"- Sinh lúc: {report.get('generated_at')}",
        "",
        "## Tiêu chí tự động",
        "",
        "| ID | Tiêu chí | Kết quả | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(
            f"| {row.get('id')} | {row.get('label')} | {row.get('status')} | {evidence} |"
        )
    lines.extend(["", "## Hành động còn lại", ""])
    actions = report.get("actions") or ["Không có."]
    lines.extend(f"- {action}" for action in actions)
    lines.extend(["", "Cần bác sĩ kiểm chứng.", ""])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def evaluate_study(
    study: str,
    out_dir: Path,
    *,
    repo_root: Optional[Path] = None,
    write: bool = True,
) -> Dict[str, Any]:
    """Chấm G5 từ artifact nháp đến khóa dữ liệu và phê duyệt cuối."""
    out_dir = Path(out_dir)
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
    checkpoint_path = out_dir / "G5_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    meta = GC.load_study_meta(out_dir)

    dmp_path = out_dir / f"G5_A6_DATA_MGMT_{study}.md"
    dictionary_path = out_dir / f"G5_REDCap_dictionary_{study}.csv"
    cleaning_report_path = out_dir / "DATA_CLEANING_report.json"
    intake_manifest_path = out_dir / "DATA_INTAKE_manifest.json"
    lock_manifest_path = out_dir / "DATA_LOCK_manifest.json"
    operational_path = out_dir / OPERATIONAL_READINESS_JSON

    dmp_text = ""
    try:
        dmp_text = dmp_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        pass
    dictionary = _read_redcap_dictionary(dictionary_path)
    intake = _read_json(intake_manifest_path)
    cleaning = _read_json(cleaning_report_path)
    lock = _read_json(lock_manifest_path)
    operational = evaluate_operational_readiness(operational_path)
    has_real_data = bool(intake or cleaning or lock)
    has_locked_data = lock.get("status") == _LOCKED_STATUS

    automatic: list[Dict[str, str]] = []
    automatic.append(
        _criterion(
            "G5-AUTO-00",
            "Guardrail liêm chính G5 sạch",
            "PASS" if _guardrail_ok(checkpoint) else "BLOCK",
            f"guardrail={checkpoint.get('guardrail')!r}",
            "Sửa lỗi nguồn, PII, vượt cổng hoặc disclaimer trước khi dùng bộ công cụ.",
        )
    )

    artifacts = {
        "DMP": dmp_path.exists(),
        "dictionary": dictionary_path.exists(),
        "cleaning_script": (out_dir / "scripts" / "data_cleaning.py").exists(),
        "quality_script": (out_dir / "scripts" / "data_quality_report.py").exists(),
    }
    artifact_ok = all(artifacts.values())
    automatic.append(
        _criterion(
            "G5-AUTO-01",
            "Đủ DMP, data dictionary và script QC tái lập",
            "PASS" if artifact_ok else "BLOCK",
            ", ".join(f"{key}={value}" for key, value in artifacts.items()),
            "Chạy lại run_g5_auto.py để sinh đủ bộ công cụ G5.",
        )
    )

    dictionary_issues = list(dictionary.get("issues") or [])
    # DMP là tài liệu sống nên có thể còn mục [CẦN] không liên quan tới schema
    # (vd số người loại sau tuyển). Trước data lock, phần không được còn
    # placeholder là chính data dictionary dùng để thu thập/làm sạch.
    placeholder = _contains_placeholder((dictionary_path,))
    if dictionary_issues:
        dictionary_status = "BLOCK"
    elif has_real_data and placeholder:
        dictionary_status = "BLOCK"
    elif placeholder:
        dictionary_status = "REVIEW"
    else:
        dictionary_status = "PASS"
    automatic.append(
        _criterion(
            "G5-AUTO-02",
            "Data dictionary là CSV có cấu trúc, tên biến duy nhất và không có định danh trực tiếp",
            dictionary_status,
            (
                "; ".join(dictionary_issues)
                if dictionary_issues
                else f"rows={dictionary.get('rows')}; placeholder={placeholder}"
            ),
            "Hoàn thiện CRF/codebook, xóa placeholder và đối chiếu với G3/SAP trước thu thập.",
        )
    )

    # LƯU Ý PHẠM VI (audit toàn diện G0-G10, 2026-07-30, G5-F3 — MEDIUM).
    # ⛔ ĐÃ VÁ 10/09/2026 (audit toàn diện hệ nghiên cứu, xác nhận độc lập lỗ hổng
    # vẫn còn nguyên tính đến hôm đó): trước đây _REQUIRED_DMP_TOKENS chỉ hỏi "11
    # tiêu đề mục cố định có xuất hiện ĐÂU ĐÓ trong toàn văn bản không" — bộ sinh
    # `generate_artifact()` luôn in đủ 11 nhãn vô điều kiện nên tiêu chí này CHƯA
    # BAO GIỜ có thể BLOCK về mặt cấu trúc, kể cả khi thân mỗi mục toàn placeholder
    # rỗng. Nay gọi thêm `_dmp_noi_dung_thieu_duoi_nhan()` (khuôn BH97: phân biệt
    # "thiếu nhãn" khỏi "có nhãn nhưng thân mục rỗng") — luật CÓ THỂ BLOCK thật, đã
    # kiểm bằng đột biến (xem tests/test_g5_auto03_content_check_20260910.py).
    missing_dmp = [
        token for token in _REQUIRED_DMP_TOKENS if token.casefold() not in dmp_text.casefold()
    ]
    content_thieu = _dmp_noi_dung_thieu_duoi_nhan(dmp_text, _REQUIRED_DMP_TOKENS)
    thieu_tong = missing_dmp or content_thieu
    if missing_dmp:
        bang_chung = "thiếu nhãn: " + ", ".join(missing_dmp)
    elif content_thieu:
        bang_chung = "có nhãn nhưng thân mục rỗng/chỉ placeholder: " + ", ".join(content_thieu)
    else:
        bang_chung = (
            "đủ 11 nhãn + nội dung thật dưới mỗi nhãn "
            "(capture/QC/audit/privacy/access/backup/retention/lock/sharing)"
        )
    automatic.append(
        _criterion(
            "G5-AUTO-03",
            "DMP phủ vòng đời dữ liệu theo ICH E6(R3), có NỘI DUNG thật dưới mỗi nhãn",
            "BLOCK" if thieu_tong else "PASS",
            bang_chung,
            "Bổ sung nhãn còn thiếu và/hoặc viết nội dung thật (không chỉ [CẦN...]) "
            "dưới các phần vòng đời dữ liệu trong DMP.",
        )
    )

    operational_ok = operational.get("valid") is True
    automatic.append(
        _criterion(
            "G5-AUTO-04",
            "Hồ sơ vận hành xác minh access, backup/restore, retention và deviation",
            "PASS" if operational_ok else ("BLOCK" if has_real_data else "REVIEW"),
            (
                f"valid={operational_ok}; issues={operational.get('issues')}; "
                f"sha256={operational.get('sha256')}"
            ),
            (
                f"Hoàn tất {OPERATIONAL_READINESS_JSON} bằng bằng chứng vận hành "
                "và người quản trị dữ liệu/PI xác nhận."
            ),
        )
    )

    g2_cp = _read_json(out_dir / "G2_checkpoint.json")
    g2_artifact = out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G10-01 — CRITICAL, bản sao thứ 4 của
    # cùng lỗi cũng đã vá ở lock_analysis_dataset.py/g9_quality_gate.py/
    # g10_quality_gate.py): _status_is_locked đọc g2_status/g4_status — chuỗi mà
    # run_g2_auto.py/run_g4_auto.py KHÔNG BAO GIỜ ghi "LOCKED". g4_ok vì vậy vĩnh
    # viễn False, G5-AUTO-05 không bao giờ PASS cho một đề tài SAP đã ký hợp lệ thật.
    g2_ok = (
        _status_is_locked(g2_cp.get("g2_status") or g2_cp.get("G2_STATUS"))
        and GC.ledger_approved("G2", study, g2_artifact, repo_root=root)
        and GC.g2_quality_contract_satisfied(g2_cp, meta)
    )
    g4_ok = GC.g4_quality_contract_satisfied(study, repo_root=root)
    upstream_status = "PASS" if g2_ok and g4_ok else ("BLOCK" if has_real_data else "REVIEW")
    automatic.append(
        _criterion(
            "G5-AUTO-05",
            "G2 và G4 đã khóa bằng phê duyệt hợp lệ trước xử lý dữ liệu thật",
            upstream_status,
            f"G2={g2_ok}; G4={g4_ok}",
            "Hoàn tất G2 IRB/IEC và G4 SAP trong approval ledger trước intake/lock.",
        )
    )

    intake_path = _safe_child(out_dir, intake.get("raw_readonly_path"))
    intake_sha = _sha256(intake_path) if intake_path else None
    intake_ok = bool(
        intake.get("status") == _INTAKE_READY_STATUS
        and intake.get("pii_scan", {}).get("passed") is True
        and intake_sha
        and intake_sha == intake.get("sha256")
        and _readonly(intake_path)
    )
    automatic.append(
        _criterion(
            "G5-AUTO-06",
            "Bản raw khử định danh có checksum và chỉ đọc",
            "PASS" if intake_ok else ("BLOCK" if has_real_data else "REVIEW"),
            (
                f"status={intake.get('status')}; hash_match={intake_sha == intake.get('sha256')}; "
                f"readonly={_readonly(intake_path)}"
            ),
            "Nạp dữ liệu qua import_real_dataset.py; không khóa file ngoài provenance intake.",
        )
    )

    clean_path = _safe_child(out_dir, cleaning.get("clean_dataset_path"))
    clean_sha = _sha256(clean_path) if clean_path else None
    cleaning_ok = bool(
        cleaning.get("status") == _CLEAN_READY_STATUS
        and cleaning.get("ready_for_lock") is True
        and cleaning.get("dictionary_loaded") is True
        and clean_sha
        and clean_sha == cleaning.get("output_sha256")
        and intake.get("sha256")
        and cleaning.get("source_sha256") == intake.get("sha256")
        and cleaning.get("dictionary_sha256") == _sha256(dictionary_path)
    )
    automatic.append(
        _criterion(
            "G5-AUTO-07",
            "Làm sạch có provenance, dictionary và checksum khớp",
            "PASS" if cleaning_ok else ("BLOCK" if has_real_data else "REVIEW"),
            (
                f"status={cleaning.get('status')}; output_hash_match="
                f"{clean_sha == cleaning.get('output_sha256')}; "
                f"source_matches_intake={cleaning.get('source_sha256') == intake.get('sha256')}; "
                f"dictionary_loaded={cleaning.get('dictionary_loaded')}"
            ),
            "Chạy clean_research_dataset.py trên raw readonly với đúng data dictionary G5.",
        )
    )

    query_path = _safe_child(out_dir, cleaning.get("query_log"))
    query = _query_log_report(query_path)
    query_sha = _sha256(query_path) if query_path else None
    query_ok = bool(
        query_path
        and not query.get("issues")
        and query.get("open") == 0
        and query_sha
        and cleaning.get("query_log_sha256") == query_sha
    )
    automatic.append(
        _criterion(
            "G5-AUTO-08",
            "Query log tồn tại, mọi query đã đóng và hash khớp",
            "PASS" if query_ok else ("BLOCK" if has_real_data else "REVIEW"),
            (
                f"rows={query.get('rows')}; open={query.get('open')}; "
                f"issues={query.get('issues')}; hash_match="
                f"{cleaning.get('query_log_sha256') == query_sha}"
            ),
            "Đối chiếu nguồn, ghi resolution và đóng từng query; không tự sửa giá trị.",
        )
    )

    locked_path = _safe_child(out_dir, lock.get("locked_dataset_path"))
    locked_sha = _sha256(locked_path) if locked_path else None
    confirmations = lock.get("confirmations")
    confirmations = confirmations if isinstance(confirmations, Mapping) else {}
    required_confirmations = {
        "deidentified",
        "clean_copy_not_raw",
        "no_open_query",
        "sap_locked",
        "dictionary_crf_aligned",
        "access_control_reviewed",
        "backup_restore_tested",
        "retention_plan_confirmed",
        "protocol_deviations_reconciled",
    }
    confirmations_ok = all(confirmations.get(key) is True for key in required_confirmations)
    reviewer_group = GC.role_group_for(str(lock.get("reviewer_role") or ""))
    checkpoint_hashes_ok = bool(
        checkpoint.get("locked_dataset_sha256") == locked_sha
        and checkpoint.get("raw_dataset_sha256") == intake_sha
        and checkpoint.get("data_dictionary_sha256") == _sha256(dictionary_path)
        and checkpoint.get("cleaning_report_sha256")
        == _sha256(cleaning_report_path)
        and checkpoint.get("query_log_sha256") == query_sha
        and checkpoint.get("operational_readiness_sha256")
        == operational.get("sha256")
    )
    lock_ok = bool(
        has_locked_data
        and lock.get("quality_contract_version") == QUALITY_CONTRACT_VERSION
        and lock.get("analysis_allowed") is True
        and locked_path
        and locked_sha
        and locked_sha == lock.get("sha256")
        and clean_sha == lock.get("sha256")
        and _readonly(locked_path)
        and int(lock.get("row_count") or 0) > 0
        and int(lock.get("column_count") or 0) > 0
        and reviewer_group in {"DATA_MANAGER", "PI"}
        and str(lock.get("reviewer_ref") or "").strip()
        and confirmations_ok
        and lock.get("dictionary_sha256") == _sha256(dictionary_path)
        and lock.get("cleaning_report_sha256") == _sha256(cleaning_report_path)
        and lock.get("query_log_sha256") == query_sha
        and lock.get("operational_readiness_sha256") == operational.get("sha256")
        and operational_ok
        and checkpoint_hashes_ok
        and lock.get("upstream_approvals", {}).get("G2") is True
        and lock.get("upstream_approvals", {}).get("G4") is True
    )
    automatic.append(
        _criterion(
            "G5-AUTO-09",
            "Manifest khóa liên kết toàn bộ hồ sơ và dataset chỉ đọc",
            "PASS" if lock_ok else ("BLOCK" if lock else "REVIEW"),
            (
                f"status={lock.get('status')}; checksum={locked_sha == lock.get('sha256')}; "
                f"readonly={_readonly(locked_path)}; reviewer_group={reviewer_group}; "
                f"confirmations={confirmations_ok}; "
                f"checkpoint_hashes={checkpoint_hashes_ok}"
            ),
            "Khóa lại qua lock_analysis_dataset.py sau khi mọi điều kiện đã đủ.",
        )
    )

    g5_approved = bool(
        checkpoint_path.exists()
        and GC.ledger_approved("G5", study, checkpoint_path, repo_root=root)
    )
    automatic.append(
        _criterion(
            "G5-HUMAN-01",
            "Người quản trị dữ liệu/PI phê duyệt G5 gắn với hash checkpoint",
            "PASS" if g5_approved else "REVIEW",
            f"approval_ledger_G5={g5_approved}",
            (
                "Người có thẩm quyền tự chạy approve_gate.py cho G5 sau khi đọc "
                "DATA_LOCK_memo và G5_QUALITY_REPORT; agent không tự phê duyệt."
            ),
        )
    )

    any_block = any(row["status"] == "BLOCK" for row in automatic)
    if any_block:
        status = STATUS_BLOCKED
    elif not lock_ok:
        status = STATUS_DRAFT
    elif not g5_approved:
        status = STATUS_READY
    else:
        status = STATUS_LOCKED

    actions = [
        row["action"]
        for row in automatic
        if row["status"] != "PASS" and row.get("action")
    ]
    report: Dict[str, Any] = {
        "kind": "g5_quality_report",
        "study": study,
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "automatic_criteria": automatic,
        "actions": list(dict.fromkeys(actions)),
        "standards_basis": list(STANDARDS_BASIS),
        "real_data_present": has_real_data,
        "technical_lock_valid": lock_ok,
        "human_approval_valid": g5_approved,
        "release_rule": (
            "Chỉ PASS_G5_DATA_LOCKED khi khóa kỹ thuật hợp lệ và approval ledger "
            "G5 khớp hash; không tự phê duyệt."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }

    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / REPORT_JSON).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8", newline="\n"
        )
        _write_markdown(out_dir / REPORT_MD, report)
        meta_for_write = GC.ensure_study_meta(out_dir)
        meta_for_write["g5_quality_status"] = status
        real_lock = meta_for_write.get("real_data_lock")
        if isinstance(real_lock, dict):
            real_lock["g5_quality_status"] = status
        (out_dir / "study_meta.json").write_text(
            json.dumps(meta_for_write, ensure_ascii=False, indent=2),
            encoding="utf-8", newline="\n"
        )

        # Không sửa checkpoint sau khi đã ký: sửa dù chỉ một byte sẽ làm ledger
        # G5 mất hiệu lực. Trước chữ ký, ghi trạng thái chất lượng để người duyệt
        # biết chính xác artifact mình sắp ký.
        if checkpoint and not g5_approved:
            checkpoint["quality_contract_version"] = QUALITY_CONTRACT_VERSION
            checkpoint["quality_gate"] = {
                "status": status,
                "report": REPORT_JSON,
                "technical_lock_valid": lock_ok,
                "human_approval_valid": False,
            }
            checkpoint["g5_status"] = (
                "LOCKED" if lock_ok else checkpoint.get("g5_status", "PENDING")
            )
            checkpoint_path.write_text(
                json.dumps(checkpoint, ensure_ascii=False, indent=2),
                encoding="utf-8", newline="\n"
            )
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Chấm hợp đồng chất lượng G5.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    study = RDI._sanitize_study(args.study)
    report = evaluate_study(
        study,
        root / "exports" / study,
        repo_root=root,
        write=True,
    )
    print(f"G5 quality status: {report['status']}")
    print(f"Report: exports/{study}/{REPORT_JSON}")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
