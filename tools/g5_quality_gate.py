#!/usr/bin/env python3
"""Hợp đồng chất lượng G5 cho quản trị và khóa dữ liệu nghiên cứu.

G5 không được coi là đạt chỉ vì đã sinh CRF hoặc vì checkpoint chứa chữ
``LOCKED``. Cổng có năm trạng thái:

- ``BLOCKED``: lỗi liêm chính, provenance hoặc khóa dữ liệu.
- ``DRAFT_READY_NEEDS_REAL_DATA``: bộ công cụ đã sẵn sàng nhưng chưa có dữ liệu.
- ``DRAFT_LOCKED_NEEDS_HUMAN_REVIEW``: đã khoá kỹ thuật nhưng còn mục người phải rà (DMP còn ô trống ở mục sống,
  kế hoạch SDV chưa khai, SAP ký lại sau khi nạp dữ liệu chưa khai sửa đổi…) — approve_gate chỉ ký khi READY.
  (Thêm 04/10/2026 — soát từng cổng G5: trước đó REVIEW không ảnh hưởng trạng thái nên không chặn được gì.)
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
import pipeline_freshness as PF
import placeholder_contract as PC

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_READY_NEEDS_REAL_DATA"
STATUS_DRAFT_REVIEW = "DRAFT_LOCKED_NEEDS_HUMAN_REVIEW"
STATUS_READY = "READY_FOR_G5_APPROVAL"
STATUS_LOCKED = "PASS_G5_DATA_LOCKED"
QUALITY_CONTRACT_VERSION = "G5-2026.2"  # 04/10/2026: khoá gắn DMP, giải quyết query, bản gỡ băng
# VÁ 04/10/2026 (soát từng cổng, G5-07): hồ sơ vận hành phiên bản 2 — bằng chứng (evidence_ref/log_ref) bắt buộc, thêm
# rà soát audit trail và kế hoạch kiểm dữ liệu nguồn (SDV/spot-check, QĐ-10).
OPERATIONAL_SCHEMA_VERSION = "G5-OPS-2026.2"
# VÁ 04/10/2026 (G5-08): bản gỡ băng/ghi âm của thiết kế định tính — dữ liệu thô nhạy PII nhất — vào manifest có băm.
TRANSCRIPT_MANIFEST_JSON = "TRANSCRIPT_manifest.json"
# VÁ 04/10/2026 (G5-04, QĐ-9): mã đóng query hợp lệ (kèm lý do, người đóng, thời điểm ISO).
MA_DONG_QUERY = frozenset({"da_sua", "xac_nhan_dung", "khong_ap_dung_co_ly_do"})

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
# Nhãn THAM CHIẾU (chuẩn được viện dẫn) chỉ cần có mặt — không phải một MỤC có thân nội dung (G5-01).
_DMP_NHAN_THAM_CHIEU = frozenset({"ICH E6(R3)"})
_DMP_NHAN_KHOA = "KHÓA CƠ SỞ DỮ LIỆU"

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


def _la_ten_bien_dinh_danh(name: Any) -> bool:
    """Tên biến là định danh trực tiếp — HỢP NHẤT danh sách của G5 với PII_HEADER_EXACT/CONTAINS của bước nạp
    (import_real_dataset).

    VÁ 04/10/2026 (soát từng cổng, G5-06): danh sách cũ của G5 hẹp hơn bước nạp (thiếu ma_benh_an, sdt, ten_benh_nhan,
    hoten, ma_bn, initials…) ⇒ dictionary khai biến định danh vẫn PASS rồi mới bị chặn ở intake. Không dùng luật TOKEN
    «name»/«ten» của bước nạp: «drug_name» (tên thuốc) không phải định danh người (đã có test chống báo nhầm)."""
    norm = _normalise_key(name)
    if norm in _DIRECT_IDENTIFIER_TOKENS or set(norm.split("_")) & _DIRECT_IDENTIFIER_COMPONENTS:
        return True
    return norm in RDI.PII_HEADER_EXACT or any(tok in norm for tok in RDI.PII_HEADER_CONTAINS)


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
    pii_names = sorted({name for name in names if name and _la_ten_bien_dinh_danh(name)})
    required_header = headers.get("required_field?")
    required_names = [
        str(row.get(name_header) or "").strip()
        for row in rows
        if required_header and str(row.get(required_header) or "").strip().casefold() in {"1", "true", "y", "yes"}
        and str(row.get(name_header) or "").strip()
    ]
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
        "required_names": required_names,
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


def _ngay_hop_le(value: Any) -> Optional[str]:
    """None nếu `value` là ngày/giờ ISO không ở tương lai; ngược lại trả mã lỗi ngắn ("invalid"/"future")."""
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return "invalid"
    # Ngày lịch không kèm múi giờ do người duyệt gõ theo NGÀY ĐỊA PHƯƠNG (cùng quy ước lock_date) — so với UTC sẽ báo
    # sai «future_» với múi giờ trước UTC (VD UTC+7) suốt khoảng nửa đêm tới rạng sáng giờ địa phương.
    if parsed.date() > datetime.now().date():
        return "future"
    return None


def evaluate_operational_readiness(path: Path) -> Dict[str, Any]:
    """Kiểm hồ sơ vận hành G5 mà không đọc dữ liệu người tham gia.

    VÁ 04/10/2026 (soát từng cổng, G5-07 — hồ sơ ``G5-OPS-2026.2``): (a) evidence_ref của rà quyền truy cập/thử phục hồi
    và log_ref của sai lệch đề cương BẮT BUỘC có nội dung thật — bản cũ để chuỗi rỗng vẫn valid=True; (b) thêm
    ``audit_trail_review`` {completed, reviewed_at, evidence_ref} — checklist khoá CSDL của chính DMP đòi «Audit trail
    REDCap đầy đủ» mà không tiêu chí nào kiểm; (c) ``source_data_verification`` {method, fraction_or_n, completed,
    evidence_ref} HOẶC {not_applicable_reason} — QĐ-10: thiếu ⇒ cảnh báo (REVIEW ở G5-AUTO-04b), không phải lỗi cứng.
    Trả thêm ``canh_bao`` (mục chỉ REVIEW)."""
    payload = _read_json(path)
    issues: list[str] = []
    canh_bao: list[str] = []
    if not payload:
        return {"valid": False, "issues": ["missing_or_invalid_record"], "canh_bao": [], "sha256": None}
    if payload.get("schema_version") != OPERATIONAL_SCHEMA_VERSION:
        issues.append(f"schema_version_khong_phai_{OPERATIONAL_SCHEMA_VERSION}")
    if payload.get("status") != "VERIFIED":
        issues.append("status_not_verified")

    def _muc(ten: str) -> Mapping[str, Any]:
        value = payload.get(ten)
        return value if isinstance(value, Mapping) else {}

    access = _muc("access_control_review")
    if not (access.get("completed") is True and access.get("least_privilege_confirmed") is True):
        issues.append("access_control_not_verified")
    backup = _muc("backup_restore_test")
    if not (
        backup.get("completed") is True
        and backup.get("restore_verified") is True
        and backup.get("checksum_verified") is True
    ):
        issues.append("backup_restore_not_verified")
    retention = _muc("retention_plan")
    if not (retention.get("confirmed") is True and PC.co_noi_dung_that(retention.get("retention_rule"))):
        issues.append("retention_plan_not_confirmed")
    deviations = _muc("protocol_deviations")
    try:
        open_count = int(deviations.get("open_count"))
    except (TypeError, ValueError):
        open_count = -1
    if not (deviations.get("reconciled") is True and open_count == 0):
        issues.append("protocol_deviations_not_reconciled")
    audit = _muc("audit_trail_review")
    if audit.get("completed") is not True:
        issues.append("audit_trail_not_reviewed")
    for ten, section in (("access_control_review.evidence_ref", access.get("evidence_ref")),
                         ("backup_restore_test.evidence_ref", backup.get("evidence_ref")),
                         ("protocol_deviations.log_ref", deviations.get("log_ref")),
                         ("audit_trail_review.evidence_ref", audit.get("evidence_ref"))):
        if not PC.co_noi_dung_that(section):
            issues.append(f"thieu_bang_chung:{ten}")
    reviewer_role = str(payload.get("reviewer_role") or "")
    if not GC.reviewer_role_satisfies_gate("G5", reviewer_role):
        issues.append("invalid_reviewer_role")
    if not PC.co_noi_dung_that(payload.get("reviewer_ref")):
        issues.append("missing_reviewer_ref")
    for field, section in (("reviewed_at", access), ("tested_at", backup), ("audit_reviewed_at", audit)):
        loi = _ngay_hop_le(section.get("reviewed_at" if field == "audit_reviewed_at" else field))
        if loi:
            issues.append(f"{loi}_{field}")
    sdv = _muc("source_data_verification")
    if PC.co_noi_dung_that(sdv.get("not_applicable_reason")):
        pass  # khai «không áp dụng» kèm lý do là câu trả lời hợp lệ (QĐ-10)
    elif not (
        sdv.get("completed") is True
        and PC.co_noi_dung_that(sdv.get("method"))
        and PC.co_noi_dung_that(sdv.get("fraction_or_n"))
        and PC.co_noi_dung_that(sdv.get("evidence_ref"))
    ):
        canh_bao.append("sdv_chua_khai_hoac_chua_xong: khai source_data_verification {method, fraction_or_n, "
                        "completed, "
                        "evidence_ref} hoặc not_applicable_reason")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raw_text = ""
    if PC.co_o_trong(raw_text):
        issues.append("unresolved_placeholder")
    return {
        "valid": not issues,
        "issues": issues,
        "canh_bao": canh_bao,
        "sha256": _sha256(path),
        "reviewer_group": GC.role_group_for(reviewer_role),
    }


_NGUONG_NOI_DUNG_THAT_SAU_NHAN = 20  # ký tự, sau khi đã bỏ mọi placeholder


_RE_TIEU_DE = re.compile(r"^\s*#{1,6}\s+(.*)$")
_RE_NHAN_DAM = re.compile(r"^\s*[-*]\s+\*\*([^*\n]+)\*\*")


def _phan_nhan_cua_dong(line: str) -> Optional[str]:
    """Phần NHÃN của một dòng cấu trúc: cả tiêu đề, hoặc chỉ phần in đậm đầu gạch đầu dòng — None nếu là câu văn."""
    m = _RE_TIEU_DE.match(line)
    if m:
        return m.group(1)
    m = _RE_NHAN_DAM.match(line)
    return m.group(1) if m else None


def _dmp_neo_nhan(dmp_text: str, tokens: Iterable[str]) -> Dict[str, int]:
    """{nhãn: chỉ số DÒNG cấu trúc đầu tiên chứa nhãn} — dòng cấu trúc = tiêu đề Markdown («# …») hoặc gạch đầu dòng
    in đậm («- **Nhãn:** …»). Nhãn THAM CHIẾU (ICH E6(R3)) không có neo.

    VÁ 04/10/2026 (soát từng cổng, G5-01): bản cũ dùng ``find()`` lấy lần xuất hiện ĐẦU TIÊN ở BẤT KỲ đâu — «KHỬ ĐỊNH
    DANH» khớp câu cảnh báo bảo mật đầu tệp, «ICH E6(R3)» khớp dòng tham chiếu, nên văn mẫu bộ sinh (≥ 20 ký tự sau mỗi
    lần xuất hiện) luôn PASS kể cả DMP nháp còn 20 ô [CẦN]. Nay chỉ neo ở dòng cấu trúc."""
    lines = dmp_text.splitlines()
    neo: Dict[str, int] = {}
    for tok in tokens:
        if tok in _DMP_NHAN_THAM_CHIEU:
            continue
        for i, line in enumerate(lines):
            nhan = _phan_nhan_cua_dong(line)
            if nhan is not None and tok.casefold() in nhan.casefold():
                neo[tok] = i
                break
    return neo


def _bo_o_trong(text: str) -> str:
    """Bỏ mọi ô trống dạng ngoặc mà hợp đồng chung nhận ra («[CẦN…]», «[REQUIRE_HUMAN…]», «[TBD]»…)."""
    return re.sub(r"\[[^\]\n]*\]", lambda m: "" if PC.co_o_trong(m.group(0), PC.TAT_CA_HO) else m.group(0), text)


def _dmp_noi_dung_thieu_duoi_nhan(dmp_text: str, tokens: Iterable[str]) -> list:
    """Nhãn (không kể nhãn tham chiếu) mà thân mục RỖNG/chỉ ô trống, hoặc KHÔNG có dòng cấu trúc riêng.

    Thân mục = phần dòng neo sau nhãn + các dòng tới neo kế tiếp (theo vị trí thật trong văn bản). Nhãn chỉ xuất hiện
    trong câu văn (không có tiêu đề/gạch đầu dòng riêng) bị coi là THIẾU MỤC (G5-01). Khuôn BH97: phân biệt «thiếu nhãn»
    (missing_dmp, xử lý riêng) với «có nhãn nhưng thân mục trống rỗng»."""
    tokens = [t for t in tokens if t not in _DMP_NHAN_THAM_CHIEU]
    lines = dmp_text.splitlines()
    neo = _dmp_neo_nhan(dmp_text, tokens)
    thieu = [tok for tok in tokens if tok.casefold() in dmp_text.casefold() and tok not in neo]
    thu_tu = sorted(neo.items(), key=lambda kv: kv[1])
    for i, (tok, idx) in enumerate(thu_tu):
        dong_neo = lines[idx]
        sau_nhan = dong_neo[dong_neo.casefold().index(tok.casefold()) + len(tok):]
        ket_thuc = thu_tu[i + 1][1] if i + 1 < len(thu_tu) else len(lines)
        than_muc = "\n".join([sau_nhan, *lines[idx + 1:ket_thuc]])
        that = re.sub(r"[*#|\-\s:()]+", " ", _bo_o_trong(than_muc)).strip()
        if len(that) < _NGUONG_NOI_DUNG_THAT_SAU_NHAN:
            thieu.append(tok)
    return thieu


def _dmp_khoi_khoa(dmp_text: str) -> str:
    """Thân mục KHOÁ CƠ SỞ DỮ LIỆU: từ dòng neo tới tiêu đề cùng cấp hoặc cao hơn kế tiếp."""
    lines = dmp_text.splitlines()
    idx = _dmp_neo_nhan(dmp_text, (_DMP_NHAN_KHOA,)).get(_DMP_NHAN_KHOA)
    if idx is None:
        return ""
    m = re.match(r"^\s*(#{1,6})\s", lines[idx])
    cap = len(m.group(1)) if m else 6
    ket_thuc = len(lines)
    for j in range(idx + 1, len(lines)):
        m2 = re.match(r"^\s*(#{1,6})\s", lines[j])
        if m2 and len(m2.group(1)) <= cap:
            ket_thuc = j
            break
    return "\n".join(lines[idx:ket_thuc])


def dmp_chua_hoan_tat_khi_khoa(dmp_text: str) -> list:
    """Lý do DMP CHƯA được hoàn tất cho thời điểm khoá dữ liệu (rỗng = đã hoàn tất).

    VÁ 04/10/2026 (soát từng cổng, G5-01): G5 từng tới PASS_G5_DATA_LOCKED khi DMP vẫn «Trạng thái: DRAFT» và checklist
    khoá còn «Ngày khóa DB: [CẦN]», «Người khóa DB (chữ ký): [CẦN]». Khi đã có dữ liệu khoá: tiêu đề/dòng trạng thái còn
    DRAFT, mục khoá CSDL còn ô trống hoặc ô tick chưa đánh dấu ⇒ BLOCK (lock_analysis_dataset cũng từ chối khoá)."""
    ly_do: list = []
    for line in dmp_text.splitlines()[:15]:
        if (line.startswith("# ") or re.search(r"\*\*Trạng thái:\*\*", line)) and re.search(r"\bDRAFT\b", line):
            ly_do.append(f"DMP còn nhãn bản nháp: {line.strip()[:90]!r}")
            break
    khoi = _dmp_khoi_khoa(dmp_text)
    if not khoi:
        ly_do.append("DMP không có mục KHÓA CƠ SỞ DỮ LIỆU (checklist khoá) có tiêu đề riêng")
        return ly_do
    o_trong = PC.dong_con_trong(khoi, PC.TAT_CA_HO)
    if o_trong:
        ly_do.append("mục KHÓA CƠ SỞ DỮ LIỆU còn ô trống: " + " | ".join(o_trong[:3]))
    chua_tick = [ln.strip() for ln in khoi.splitlines() if re.match(r"^\s*[-*]\s+\[\s\]", ln)]
    if chua_tick:
        ly_do.append(f"checklist khoá còn {len(chua_tick)} mục chưa đánh dấu: " + " | ".join(chua_tick[:2]))
    return ly_do


def dmp_o_trong_muc_song(dmp_text: str) -> list:
    """Dòng còn ô trống NGOÀI mục khoá CSDL (mục «sống» — lưu đồ N, ngưỡng thiếu…) — chỉ REVIEW sau khi khoá."""
    khoi = _dmp_khoi_khoa(dmp_text)
    phan_con_lai = dmp_text.replace(khoi, "") if khoi else dmp_text
    return PC.dong_con_trong(phan_con_lai)


def _moc_utc(value: Any) -> Optional[datetime]:
    """Mốc thời gian ISO → UTC. Không kèm múi giờ ⇒ coi là giờ ĐỊA PHƯƠNG của máy ghi (imported_at/cleaned_at cũ)."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        moc = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moc.tzinfo is None:
        moc = moc.astimezone()
    return moc.astimezone(timezone.utc)


def _som_hon(moc: datetime, moc_ky: datetime) -> bool:
    """``moc`` (nạp/làm sạch) có SỚM HƠN ``moc_ky`` không — so ở đúng độ chính xác của ``moc``.

    Mốc nạp/làm sạch cũ ghi tới GIÂY (timespec=seconds) còn mốc ký sổ cái có micro-giây: lần nạp diễn ra ngay sau khi ký
    (cùng giây) từng bị coi là «trước khi ký». Mốc không có phần lẻ giây ⇒ làm tròn mốc ký xuống giây trước khi so."""
    if moc.microsecond == 0:
        moc_ky = moc_ky.replace(microsecond=0)
    return moc < moc_ky


def _moc_ky_so_cai(study: str, gate: str, artifact: Path, repo_root: Path) -> tuple:
    """(lần ký APPROVED SỚM NHẤT của cổng — mọi phiên bản, lần ký MỚI NHẤT khớp băm artifact HIỆN TẠI) theo UTC.

    Chỉ đọc sổ cái để lấy MỐC — phán «đã ký hợp lệ» vẫn là việc của gate_contract.ledger_approved (G5-AUTO-05)."""
    try:
        records = json.loads((Path(repo_root) / "exports" / str(study) / "approval_ledger.json")
                             .read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(records, list):
        return None, None
    approved = [r for r in records if isinstance(r, dict)
                and str(r.get("gate_id") or "").upper() == gate and str(r.get("decision") or "").upper() == "APPROVED"]
    moc_tat_ca = [m for m in (_moc_utc(r.get("timestamp_utc")) for r in approved) if m]
    bam = _sha256(artifact) if artifact.exists() else None
    moc_hien_hanh = [m for m in (_moc_utc(r.get("timestamp_utc")) for r in approved
                                 if bam and r.get("evidence_hash") == bam) if m]
    return (min(moc_tat_ca) if moc_tat_ca else None), (max(moc_hien_hanh) if moc_hien_hanh else None)


def _doc_header_csv(path: Optional[Path]) -> list:
    if path is None or not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(next(csv.reader(handle), []) or [])
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def danh_gia_transcript(out_dir: Path, du_lieu: Optional[Path]) -> Dict[str, Any]:
    """Kiểm TRANSCRIPT_manifest.json của thiết kế định tính (G5-08): mỗi transcript_id có trong dataset phải có mục
    {file (tương đối trong thư mục đề tài), sha256, deidentified=true, reviewer_ref}; tệp tồn tại, băm khớp, CHỈ ĐỌC, và
    nội dung (.txt/.md; .docx nếu có python-docx) không còn mẫu PII mà bước nạp quét (RDI.VALUE_PATTERNS)."""
    out_dir = Path(out_dir)
    mf_path = out_dir / TRANSCRIPT_MANIFEST_JSON
    mf = _read_json(mf_path)
    issues: list = []
    if not mf:
        return {"issues": [f"thieu_{TRANSCRIPT_MANIFEST_JSON}"], "sha256": None, "n": 0}
    try:
        if PC.co_o_trong(mf_path.read_text(encoding="utf-8")):
            issues.append("manifest_con_o_trong")
    except (OSError, UnicodeDecodeError):
        issues.append("manifest_khong_doc_duoc")
    entries = [e for e in (mf.get("transcripts") or []) if isinstance(e, Mapping)]
    if not entries:
        # Đề tài định tính đã có dữ liệu thật mà manifest không khai bản gỡ băng nào = bản gỡ băng nằm ngoài kiểm soát.
        issues.append("manifest_khong_co_ban_go_bang")
    da_khai: set = set()
    for e in entries:
        tid = str(e.get("transcript_id") or "").strip()
        if not tid:
            issues.append("muc_thieu_transcript_id")
            continue
        da_khai.add(tid)
        tep = _safe_child(out_dir, e.get("file"))
        if tep is None or not tep.exists():
            issues.append(f"{tid}:thieu_tep")
            continue
        if _sha256(tep) != str(e.get("sha256") or "").strip().lower():
            issues.append(f"{tid}:bam_lech")
        if not _readonly(tep):
            issues.append(f"{tid}:chua_chi_doc")
        if e.get("deidentified") is not True:
            issues.append(f"{tid}:chua_khu_dinh_danh")
        if not PC.co_noi_dung_that(e.get("reviewer_ref")):
            issues.append(f"{tid}:thieu_reviewer_ref")
        noi_dung = ""
        if tep.suffix.lower() in {".txt", ".md"}:
            try:
                noi_dung = tep.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                issues.append(f"{tid}:khong_doc_duoc")
        elif tep.suffix.lower() == ".docx":
            try:
                from docx import Document  # noqa: PLC0415
                noi_dung = "\n".join(par.text for par in Document(str(tep)).paragraphs)
            except Exception:  # noqa: BLE001 — không đọc được ⇒ không kiểm được PII ⇒ không phải «sạch»
                issues.append(f"{tid}:khong_doc_duoc_docx")
        else:
            issues.append(f"{tid}:dinh_dang_khong_ho_tro")
        for ten, mau in RDI.VALUE_PATTERNS.items():
            if noi_dung and mau.search(noi_dung):
                issues.append(f"{tid}:pii_{ten}")
    if du_lieu is not None and du_lieu.exists():
        try:
            with du_lieu.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                cot = next((c for c in (reader.fieldnames or []) if _normalise_key(c) == "transcript_id"), None)
                trong_du_lieu = {str(r.get(cot) or "").strip() for r in reader if cot} - {""}
            if cot is None:
                # Không có cột nối dữ liệu ↔ bản gỡ băng thì không đối chiếu được — không phải «mọi bản đã khai».
                issues.append("dataset_thieu_cot_transcript_id")
        except (OSError, UnicodeDecodeError, csv.Error):
            trong_du_lieu = set()
            issues.append("khong_doc_duoc_dataset")
        thieu = sorted(trong_du_lieu - da_khai)
        if thieu:
            issues.append(f"transcript_chua_co_trong_manifest:{thieu[:10]}")
    return {"issues": issues, "sha256": _sha256(mf_path), "n": len(entries)}


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
    # VÁ 04/10/2026 (soát từng cổng, G5-01): khi dữ liệu ĐÃ KHOÁ, DMP phải được hoàn tất cho thời điểm khoá (hết nhãn
    # DRAFT, mục khoá CSDL không còn ô trống/ô tick trống) ⇒ BLOCK; mục «sống» khác còn ô trống ⇒ REVIEW.
    khoa_chua_xong = dmp_chua_hoan_tat_khi_khoa(dmp_text) if has_locked_data else []
    muc_song = dmp_o_trong_muc_song(dmp_text) if has_locked_data else []
    if missing_dmp:
        dmp_status, bang_chung = "BLOCK", "thiếu nhãn: " + ", ".join(missing_dmp)
    elif content_thieu:
        dmp_status = "BLOCK"
        bang_chung = ("mục không có tiêu đề/gạch đầu dòng riêng hoặc thân mục rỗng/chỉ ô trống: "
                      + ", ".join(content_thieu))
    elif khoa_chua_xong:
        dmp_status, bang_chung = "BLOCK", "đã khoá dữ liệu nhưng DMP chưa hoàn tất: " + "; ".join(khoa_chua_xong)
    elif muc_song:
        dmp_status, bang_chung = "REVIEW", "mục sống của DMP còn ô trống: " + " | ".join(muc_song[:3])
    else:
        dmp_status = "PASS"
        bang_chung = (
            "đủ 11 nhãn, mỗi mục có tiêu đề riêng và nội dung thật "
            "(capture/QC/audit/privacy/access/backup/retention/lock/sharing)"
            + ("; DMP đã hoàn tất cho thời điểm khoá" if has_locked_data else "")
        )
    automatic.append(
        _criterion(
            "G5-AUTO-03",
            "DMP phủ vòng đời dữ liệu theo ICH E6(R3), có NỘI DUNG thật dưới mỗi mục; hoàn tất khi khoá dữ liệu",
            dmp_status,
            bang_chung,
            "Bổ sung mục còn thiếu/viết nội dung thật dưới các phần vòng đời dữ liệu; trước khi khoá dữ liệu: bỏ nhãn "
            "DRAFT, điền ngày khoá + người khoá/người chứng kiến (mã, không PII) và đánh dấu đủ checklist khoá CSDL.",
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
    canh_bao_ops = list(operational.get("canh_bao") or [])
    automatic.append(
        _criterion(
            "G5-AUTO-04b",
            "Kế hoạch kiểm dữ liệu nguồn (SDV/spot-check) đã khai và hoàn tất, hoặc khai không áp dụng kèm lý do",
            "REVIEW" if canh_bao_ops else "PASS",
            "; ".join(canh_bao_ops) or "source_data_verification đã khai",
            f"Ghi source_data_verification trong {OPERATIONAL_READINESS_JSON} (QĐ-10).",
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
        and GC.g2_quality_contract_satisfied(g2_cp, meta, study=study, out_dir=out_dir)
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

    # ── G5-AUTO-05b — THỨ TỰ THỜI GIAN: dữ liệu chỉ được nạp/làm sạch SAU khi IRB (G2) và SAP (G4) được ký ──────────
    # VÁ 04/10/2026 (soát từng cổng, G5-02): AUTO-05 chỉ hỏi trạng thái G2/G4 HIỆN TẠI — nạp + làm sạch dữ liệu TRƯỚC,
    # rồi mới ký SAP vẫn khoá và qua G5 (chính là HARKing mà chốt G4→G5 sinh ra để chặn). Nay so mốc nạp (imported_at)
    # và mốc làm sạch (cleaned_at) — giờ địa phương không kèm múi giờ được quy về UTC — với lần ký APPROVED đầu tiên
    # của G2/G4 trên sổ cái: sớm hơn ⇒ BLOCK. SAP ký LẠI sau khi đã nạp dữ liệu ⇒ REVIEW trừ khi PHẦN 4 của SAP có
    # dòng «SAP AMENDMENT».
    sap_path = out_dir / f"G4_A5_SAP_FINAL_{study}.md"
    tg_van_de: list = []
    tg_status = "PASS"
    if has_real_data:
        t_nap = _moc_utc(intake.get("imported_at_utc") or intake.get("imported_at"))
        t_sach = _moc_utc(cleaning.get("cleaned_at_utc") or cleaning.get("cleaned_at")) if cleaning else None
        if intake and t_nap is None:
            tg_status = "REVIEW"
            tg_van_de.append("không đọc được mốc nạp dữ liệu (imported_at) để so với lúc ký")
        for cong, tep in (("G2", g2_artifact), ("G4", sap_path)):
            dau_tien, hien_hanh = _moc_ky_so_cai(study, cong, tep, root)
            if dau_tien is None:
                continue  # chưa ký — G5-AUTO-05 đã chặn
            for nhan, moc in (("nạp", t_nap), ("làm sạch", t_sach)):
                if moc is not None and _som_hon(moc, dau_tien):
                    tg_status = "BLOCK"
                    tg_van_de.append(f"{nhan} dữ liệu lúc {moc.isoformat(timespec='seconds')} TRƯỚC lần ký {cong} đầu "
                                     f"tiên {dau_tien.isoformat(timespec='seconds')}")
            if cong == "G4" and hien_hanh is not None and t_nap is not None and _som_hon(t_nap, hien_hanh):
                try:
                    import g4_quality_gate as G4Q  # noqa: PLC0415 — import lười
                    co_sua_doi = bool(G4Q._dong_sua_doi_sap(sap_path.read_text(encoding="utf-8")))
                except (ImportError, OSError, UnicodeDecodeError):
                    co_sua_doi = False
                if not co_sua_doi:
                    tg_status = "BLOCK" if tg_status == "BLOCK" else "REVIEW"
                    tg_van_de.append(f"SAP được ký LẠI lúc {hien_hanh.isoformat(timespec='seconds')} sau khi đã nạp dữ "
                                     "liệu mà PHẦN 4 không có dòng «SAP AMENDMENT»")
    automatic.append(
        _criterion(
            "G5-AUTO-05b",
            "Dữ liệu được nạp/làm sạch SAU khi G2 (IRB) và G4 (SAP) được ký",
            tg_status,
            "; ".join(tg_van_de) or ("mốc nạp/làm sạch sau mốc ký G2/G4" if has_real_data else "chưa có dữ liệu"),
            "Không nạp dữ liệu trước khi IRB và SAP được ký; SAP sửa sau khi đã thấy dữ liệu phải ghi SAP AMENDMENT.",
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

    # ── G5-AUTO-07b — cột dữ liệu KHỚP dictionary (G5-03) ─────────────────────────────────────────────────────────────
    # VÁ 04/10/2026 (soát từng cổng): cột không có trong dictionary thì không luật range/category nào được áp
    # (clean_research_dataset bỏ qua «if not rule: continue») mà cổng vẫn PASS — tuoi_nam=450 lọt vì dictionary khai
    # «age». Nay so header bộ dữ liệu (bản khoá, chưa khoá thì bản sạch) với tên biến dictionary: cột ngoài dictionary
    # hoặc biến Required=y vắng ⇒ BLOCK; ghi tỷ lệ phủ.
    locked_path = _safe_child(out_dir, lock.get("locked_dataset_path"))
    du_lieu_path = locked_path if (locked_path and locked_path.exists()) else clean_path
    header = _doc_header_csv(du_lieu_path)
    ten_dict = {_normalise_key(n) for n in dictionary.get("names") or [] if n}
    ten_cot = {_normalise_key(c) for c in header}
    ngoai_dict = [c for c in header if _normalise_key(c) not in ten_dict]
    thieu_bat_buoc = [n for n in dictionary.get("required_names") or [] if _normalise_key(n) not in ten_cot]
    if not header:
        phu_status = "BLOCK" if has_real_data and cleaning else "REVIEW" if has_real_data else "PASS"
        phu_bang_chung = "chưa có bộ dữ liệu sạch/khoá để đối chiếu" if has_real_data else "chưa có dữ liệu"
    elif ngoai_dict or thieu_bat_buoc:
        phu_status = "BLOCK"
        phu_bang_chung = (f"cột ngoài dictionary: {ngoai_dict[:10]}; biến bắt buộc vắng: {thieu_bat_buoc[:10]}; "
                          f"phủ {len(header) - len(ngoai_dict)}/{len(header)} cột")
    else:
        phu_status, phu_bang_chung = "PASS", f"{len(header)}/{len(header)} cột có trong dictionary; đủ biến bắt buộc"
    automatic.append(
        _criterion(
            "G5-AUTO-07b",
            "Mọi cột của bộ dữ liệu có trong data dictionary và đủ biến bắt buộc",
            phu_status,
            phu_bang_chung,
            "Khai mọi biến trong G5_REDCap_dictionary (kèm loại/phạm vi) hoặc bỏ cột ngoài kế hoạch; không khoá cột "
            "không có luật kiểm.",
        )
    )

    query_path = _safe_child(out_dir, cleaning.get("query_log"))
    query = _query_log_report(query_path)
    query_sha = _sha256(query_path) if query_path else None
    # VÁ 04/10/2026 (G5-04): query đóng bằng tệp giải quyết (clean_dataset --query-resolutions) — băm tệp đó phải khớp
    # báo cáo làm sạch (sửa tệp giải quyết sau khi làm sạch ⇒ không còn khớp).
    qr_path = _safe_child(out_dir, cleaning.get("query_resolutions"))
    qr_sha = _sha256(qr_path) if qr_path else None
    qr_ok = (not cleaning.get("query_resolutions") and not cleaning.get("query_resolutions_sha256")) or bool(
        qr_sha and qr_sha == cleaning.get("query_resolutions_sha256"))
    query_ok = bool(
        query_path
        and not query.get("issues")
        and query.get("open") == 0
        and query_sha
        and cleaning.get("query_log_sha256") == query_sha
        and qr_ok
    )
    automatic.append(
        _criterion(
            "G5-AUTO-08",
            "Query log tồn tại, mọi query đã đóng và hash khớp",
            "PASS" if query_ok else ("BLOCK" if has_real_data else "REVIEW"),
            (
                f"rows={query.get('rows')}; open={query.get('open')}; "
                f"issues={query.get('issues')}; hash_match="
                f"{cleaning.get('query_log_sha256') == query_sha}; giai_quyet_khop={qr_ok}"
            ),
            "Đối chiếu nguồn rồi ghi tệp giải quyết query (clean_research_dataset.py --query-resolutions: mã "
            "da_sua/xac_nhan_dung/khong_ap_dung_co_ly_do + lý do + người đóng + thời điểm ISO); không tự sửa giá trị.",
        )
    )

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
        # VÁ 04/10/2026 (G5-07): rà soát audit trail trước khoá — checklist khoá CSDL của DMP đòi mà trước đây không ai
        # xác nhận.
        "audit_trail_reviewed",
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
        # VÁ 04/10/2026 (G5-01/G5-04/G5-08): DMP, tệp giải quyết query và manifest bản gỡ băng (định tính) gắn vào
        # checkpoint được ký.
        and checkpoint.get("dmp_sha256") == _sha256(dmp_path)
        and checkpoint.get("query_resolutions_sha256") == cleaning.get("query_resolutions_sha256")
        and checkpoint.get("transcript_manifest_sha256") == lock.get("transcript_manifest_sha256")
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
        and lock.get("dmp_sha256") == _sha256(dmp_path)
        and lock.get("query_resolutions_sha256") == cleaning.get("query_resolutions_sha256")
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

    # ── G5-AUTO-10 — định tính: bản gỡ băng/ghi âm có manifest băm, khử định danh, chỉ đọc (G5-08) ─────────────────
    # VÁ 04/10/2026 (soát từng cổng): với thiết kế định tính, G5 chỉ khoá CSV siêu dữ liệu (transcript_id…) trong khi
    # bản gỡ băng — dữ liệu thô nhạy PII nhất — nằm ngoài mọi kiểm soát.
    thiet_ke_g5 = str(GC.resolve_design_code(out_dir, default="")[0] or "").strip().lower()
    if thiet_ke_g5 == "qualitative" and has_real_data:
        tr = danh_gia_transcript(out_dir, du_lieu_path)
        if has_locked_data and lock.get("transcript_manifest_sha256") != tr.get("sha256"):
            tr["issues"].append("manifest_ban_go_bang_doi_sau_khi_khoa")
        tr_status = "BLOCK" if tr["issues"] else "PASS"
        tr_bang_chung = "; ".join(tr["issues"][:8]) or f"{tr['n']} bản gỡ băng có băm, khử định danh, chỉ đọc"
    else:
        tr_status = "PASS"
        tr_bang_chung = "không áp dụng (không phải định tính hoặc chưa có dữ liệu)"
    automatic.append(
        _criterion(
            "G5-AUTO-10",
            "Định tính: bản gỡ băng có TRANSCRIPT_manifest (băm, khử định danh, chỉ đọc, không còn mẫu PII)",
            tr_status,
            tr_bang_chung,
            f"Lập {TRANSCRIPT_MANIFEST_JSON} cho mọi transcript_id (tệp đã khử định danh, chỉ đọc, sha256, "
            "reviewer_ref không PII) rồi khoá lại.",
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
    # VÁ 04/10/2026 (soát từng cổng G5): REVIEW sau khi đã khoá kỹ thuật (DMP mục sống còn ô trống, SDV chưa khai, SAP
    # ký lại sau khi nạp…) từng KHÔNG ảnh hưởng trạng thái ⇒ vẫn READY và ký được. Nay chặn ký (approve_gate chỉ
    # ký READY).
    # G5 đã ký trước luật mới không bị hạ cấp vì REVIEW (chỉ hiển thị).
    con_review = any(row["status"] == "REVIEW" for row in automatic if row["id"] != "G5-HUMAN-01")
    if any_block:
        status = STATUS_BLOCKED
    elif not lock_ok:
        status = STATUS_DRAFT
    elif g5_approved:
        status = STATUS_LOCKED
    elif con_review:
        status = STATUS_DRAFT_REVIEW
    else:
        status = STATUS_READY

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
            PF.ghi_checkpoint_giu_moc_sinh(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
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
