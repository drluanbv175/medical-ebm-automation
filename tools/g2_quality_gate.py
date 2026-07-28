#!/usr/bin/env python3
"""Hợp đồng chất lượng G2: đạo đức, đồng thuận và đăng ký nghiên cứu.

Module cố ý tách ba sự kiện khác nhau:

1. Hệ thống đã sinh hồ sơ.
2. Hồ sơ đã đủ để nộp Hội đồng Đạo đức.
3. Hội đồng Đạo đức thật đã phê duyệt đúng phiên bản và đăng ký nghiên cứu
   đã hoàn tất đúng thời điểm khi bắt buộc.

Chỉ sự kiện thứ ba mới nhận ``PASS_G2_APPROVED``. Agent không được tạo chữ ký,
không được tự ghi phê duyệt và không được thay quyết định của IRB/IEC.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional

import gate_contract as GC

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_NEEDS_HUMAN_COMPLETION"
STATUS_READY = "READY_FOR_IRB_SUBMISSION"
STATUS_PENDING = "PENDING_REAL_IRB_OR_REGISTRATION"
STATUS_APPROVED = "PASS_G2_APPROVED"

QUALITY_CONTRACT_VERSION = "G2-2026.1"
ATTESTATION_SCHEMA = "g2-approval-attestation-v1"
ATTESTATION_BEGIN = "<!-- G2_APPROVAL_ATTESTATION_BEGIN -->"
ATTESTATION_END = "<!-- G2_APPROVAL_ATTESTATION_END -->"

WHO_TRDS_VERSION = "1.3.1"
WHO_TRDS_ITEM_COUNT = 24

WHO_TRDS_LABELS = {
    1: "Primary Registry and Trial Identifying Number",
    2: "Date of Registration in Primary Registry",
    3: "Secondary Identifying Numbers",
    4: "Source(s) of Monetary or Material Support",
    5: "Primary Sponsor",
    6: "Secondary Sponsor(s)",
    7: "Contact for Public Queries",
    8: "Contact for Scientific Queries",
    9: "Public Title",
    10: "Scientific Title",
    11: "Countries of Recruitment",
    12: "Health Condition(s) or Problem(s) Studied",
    13: "Intervention(s)",
    14: "Key Inclusion and Exclusion Criteria",
    15: "Study Type",
    16: "Date of First Enrolment",
    17: "Target Sample Size",
    18: "Recruitment Status",
    19: "Primary Outcome(s)",
    20: "Key Secondary Outcomes",
    21: "Ethics Review",
    22: "Completion Date",
    23: "Summary Results",
    24: "IPD Sharing Statement",
}

STANDARDS_BASIS = (
    {
        "standard": "WMA Declaration of Helsinki 2024",
        "scope": "Ethics review, consent, protocol amendments and registration before recruitment",
        "url": "https://www.wma.net/policies-post/wma-declaration-of-helsinki/",
    },
    {
        "standard": "ICH E6(R3)",
        "scope": "IRB/IEC, informed consent, safety and protocol control for clinical trials",
        "url": "https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf",
    },
    {
        "standard": f"WHO Trial Registration Data Set {WHO_TRDS_VERSION}",
        "scope": f"{WHO_TRDS_ITEM_COUNT} data items for complete trial registration",
        "url": "https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set",
    },
    {
        "standard": "Thông tư 43/2024/TT-BYT",
        "scope": "Tổ chức và hoạt động Hội đồng Đạo đức trong nghiên cứu y sinh học tại Việt Nam",
        "url": "https://vbpl.vn/TW/Pages/vbpq-van-ban-goc.aspx?ItemID=172919",
    },
    {
        "standard": "Luật 91/2025/QH15 và Nghị định 356/2025/NĐ-CP",
        "scope": "Bảo vệ dữ liệu cá nhân tại Việt Nam",
        "url": "https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=",
    },
)

_PACKAGE_MARKERS = (
    "TÀI LIỆU 1",
    "TÀI LIỆU 2",
    "TÀI LIỆU 3",
    "TÀI LIỆU 4",
    "TÀI LIỆU 5",
    "TÀI LIỆU 6",
    "TÀI LIỆU 7",
    "TÀI LIỆU 8",
    "PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU",
    "KẾ HOẠCH QUẢN LÝ DỮ LIỆU",
    "RỦI RO",
    "BỒI THƯỜNG KHI CÓ TỔN HẠI",
    "NGUỒN TÀI TRỢ VÀ XUNG ĐỘT LỢI ÍCH",
)

_PII_ONLY_HINTS = (
    "HỌ TÊN",
    "TÊN CHỦ NHIỆM",
    "ĐIỆN THOẠI",
    "EMAIL",
    "ĐỊA CHỈ",
    "CHỮ KÝ",
    "NGƯỜI LIÊN HỆ",
)

_RECRUITMENT_MODES = {
    "PROSPECTIVE_NEW_PARTICIPANTS",
    "RETROSPECTIVE_SECONDARY_DATA",
    "NOT_APPLICABLE",
}


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str = "",
) -> dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_iso_date(value: Any) -> Optional[date]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _g2_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get("G2")
    return value if isinstance(value, Mapping) else {}


def strip_attestation(package_text: str) -> str:
    """Bỏ phụ lục attestation cũ để tính hash và ghi lại idempotent."""
    marker_index = package_text.rfind(ATTESTATION_BEGIN)
    if marker_index < 0:
        return package_text.rstrip() + "\n"
    prefix = package_text[:marker_index]
    heading = "\n---\n\n## PHỤ LỤC KIỂM TOÁN PHÊ DUYỆT G2"
    heading_index = prefix.rfind(heading)
    if heading_index >= 0:
        prefix = prefix[:heading_index]
    return prefix.rstrip() + "\n"


def append_attestation(package_text: str, attestation: Mapping[str, Any]) -> str:
    """Gắn phụ lục JSON có cấu trúc vào bản hồ sơ đã duyệt."""
    base = strip_attestation(package_text)
    payload = json.dumps(attestation, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        f"{base}\n---\n\n## PHỤ LỤC KIỂM TOÁN PHÊ DUYỆT G2\n\n"
        f"{ATTESTATION_BEGIN}\n```json\n{payload}\n```\n{ATTESTATION_END}\n"
        "\n> Phụ lục này chỉ là dấu vết kiểm toán; quyết định thuộc Hội đồng Đạo đức.\n"
        "> Cần bác sĩ kiểm chứng.\n"
    )


def extract_attestation(package_text: str) -> dict[str, Any]:
    """Đọc phụ lục attestation cuối cùng; lỗi định dạng trả dict rỗng."""
    pattern = (
        rf"{re.escape(ATTESTATION_BEGIN)}\s*```json\s*(.*?)\s*```\s*"
        rf"{re.escape(ATTESTATION_END)}"
    )
    matches = re.findall(pattern, package_text, flags=re.DOTALL)
    if not matches:
        return {}
    try:
        value = json.loads(matches[-1])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def build_registration_draft(
    *,
    study: str,
    topic: str,
    design_code: str,
    design_primary: str,
    risk: Mapping[str, Any],
    n_target: Optional[int],
    out_dir: Path,
    generated_at: str,
) -> Path:
    """Sinh bản nháp WHO TRDS 1.3.1 đủ 24 mục, không lưu PII."""
    design_type = {
        "rct": "Interventional",
        "cohort": "Observational",
        "case_control": "Observational",
        "cross_sectional": "Observational",
        "diagnostic": "Observational",
        "prediction": "Observational",
        "qualitative": "Observational",
        "sr_ma": "Not applicable - systematic review protocol",
    }.get(design_code, "Other")
    primary_purpose = {
        "rct": "Treatment",
        "diagnostic": "Diagnostic",
        "prediction": "Prognosis",
        "cohort": "Epidemiology",
        "case_control": "Epidemiology",
        "cross_sectional": "Epidemiology",
        "qualitative": "Health services research",
        "sr_ma": "Evidence synthesis",
    }.get(design_code, "Other")

    values = {
        1: None,
        2: None,
        3: None,
        4: None,
        5: "[ĐIỀN TRỰC TIẾP TRÊN REGISTRY; KHÔNG LƯU PII TRONG HỆ THỐNG]",
        6: None,
        7: "[ĐIỀN LIÊN HỆ CÔNG KHAI TRỰC TIẾP TRÊN REGISTRY]",
        8: "[ĐIỀN LIÊN HỆ KHOA HỌC TRỰC TIẾP TRÊN REGISTRY]",
        9: None,
        10: topic,
        11: "Vietnam",
        12: None,
        13: None,
        14: {"inclusion": None, "exclusion": None},
        15: {
            "design": design_type,
            "primary_purpose": primary_purpose,
            "description": design_primary,
        },
        16: None,
        17: n_target,
        18: "Not yet recruiting",
        19: None,
        20: None,
        21: {"status": "Not approved", "approval_date": None, "committee_ref": None},
        22: None,
        23: {
            "summary_results_date": None,
            "first_publication_date": None,
            "protocol_url": None,
        },
        24: {
            "plan_to_share_ipd": None,
            "what_when_how_with_whom": None,
        },
    }
    document = {
        "schema_version": "who-trds-draft-v1",
        "who_trds_version": WHO_TRDS_VERSION,
        "item_count": WHO_TRDS_ITEM_COUNT,
        "study": study,
        "generated_at": generated_at,
        "status": "DRAFT",
        "registration_requirement": risk.get("registration"),
        "suggested_registry": risk.get("register_where"),
        "items": [
            {
                "number": number,
                "label": WHO_TRDS_LABELS[number],
                "value": values[number],
            }
            for number in range(1, WHO_TRDS_ITEM_COUNT + 1)
        ],
        "no_pii_note": (
            "Thông tin liên hệ cá nhân phải điền trực tiếp trên registry công khai; "
            "không lưu PII trong artifact pipeline."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    path = Path(out_dir) / f"G2_REGISTRATION_DRAFT_{study}.json"
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _registration_draft_errors(document: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("who_trds_version") != WHO_TRDS_VERSION:
        errors.append(f"WHO TRDS phải là phiên bản {WHO_TRDS_VERSION}")
    items = document.get("items")
    if not isinstance(items, list) or len(items) != WHO_TRDS_ITEM_COUNT:
        errors.append(f"WHO TRDS phải có đúng {WHO_TRDS_ITEM_COUNT} mục")
        return errors
    numbers = {item.get("number") for item in items if isinstance(item, Mapping)}
    if numbers != set(range(1, WHO_TRDS_ITEM_COUNT + 1)):
        errors.append("WHO TRDS thiếu hoặc trùng số mục 1-24")
    for item in items:
        if not isinstance(item, Mapping):
            errors.append("WHO TRDS có mục không phải object")
            continue
        number = item.get("number")
        if number in WHO_TRDS_LABELS and item.get("label") != WHO_TRDS_LABELS[number]:
            errors.append(f"Nhãn WHO TRDS mục {number} không đúng")
    return errors


def unresolved_critical_placeholders(package_text: str) -> list[str]:
    """Liệt kê placeholder khoa học/vận hành còn lại, bỏ qua dòng chỉ chứa PII."""
    base = strip_attestation(package_text)
    unresolved: list[str] = []
    for line in base.splitlines():
        if "[CẦN" not in line.upper():
            continue
        upper = line.upper()
        if any(hint in upper for hint in _PII_ONLY_HINTS):
            continue
        compact = re.sub(r"\s+", " ", line.strip())
        if compact and compact not in unresolved:
            unresolved.append(compact[:240])
    return unresolved


def validate_attestation(
    *,
    attestation: Mapping[str, Any],
    package_text: str,
    study: str,
    design_code: str,
    meta: Mapping[str, Any],
    today: Optional[date] = None,
) -> list[str]:
    """Kiểm metadata phê duyệt; không thay kiểm chữ ký trong approval ledger."""
    errors: list[str] = []
    today = today or date.today()
    if attestation.get("schema_version") != ATTESTATION_SCHEMA:
        errors.append("Sai/thiếu schema attestation G2")
    if attestation.get("study") != study:
        errors.append("Attestation không khớp mã đề tài")
    if attestation.get("ethics_decision") not in {"APPROVED", "EXEMPT", "WAIVER"}:
        errors.append("Thiếu quyết định đạo đức APPROVED/EXEMPT/WAIVER")
    for field, label in (
        ("ethics_committee_ref", "mã Hội đồng Đạo đức"),
        ("approval_number", "số quyết định/phê duyệt"),
        ("approved_protocol_version", "phiên bản protocol được duyệt"),
    ):
        if not str(attestation.get(field) or "").strip():
            errors.append(f"Thiếu {label}")

    approval_date = _parse_iso_date(attestation.get("approval_date"))
    if approval_date is None:
        errors.append("Ngày phê duyệt phải theo YYYY-MM-DD")
    elif approval_date > today:
        errors.append("Ngày phê duyệt không được ở tương lai")

    valid_until = _parse_iso_date(attestation.get("valid_until"))
    no_expiry = attestation.get("no_expiry_confirmed") is True
    if not valid_until and not no_expiry:
        errors.append("Phải có ngày hết hiệu lực/rà tiếp hoặc xác nhận quyết định không ghi hạn")
    if valid_until and valid_until < today:
        errors.append("Phê duyệt G2 đã hết hiệu lực")

    g2 = _g2_meta(meta)
    protocol_version = str(g2.get("protocol_version") or "").strip()
    approved_protocol = str(attestation.get("approved_protocol_version") or "").strip()
    if protocol_version and approved_protocol != protocol_version:
        errors.append("Phiên bản protocol hiện hành không khớp phiên bản IRB đã duyệt")

    waiver = attestation.get("icf_waiver_approved") is True
    approved_icf = str(attestation.get("approved_icf_version") or "").strip()
    if not waiver and not approved_icf:
        errors.append("Thiếu phiên bản ICF được duyệt hoặc quyết định miễn ICF")
    current_icf = str(g2.get("icf_version") or "").strip()
    if current_icf and not waiver and approved_icf != current_icf:
        errors.append("Phiên bản ICF hiện hành không khớp phiên bản IRB đã duyệt")

    mode = str(attestation.get("recruitment_mode") or "").strip()
    if mode not in _RECRUITMENT_MODES:
        errors.append("Thiếu/sai recruitment_mode")
    if design_code == "rct" and mode != "PROSPECTIVE_NEW_PARTICIPANTS":
        errors.append("RCT phải dùng recruitment_mode tiến cứu tuyển người tham gia")

    registration = attestation.get("registration")
    if not isinstance(registration, Mapping):
        errors.append("Thiếu metadata đăng ký nghiên cứu")
    else:
        required = (
            mode == "PROSPECTIVE_NEW_PARTICIPANTS"
            or design_code == "sr_ma"
        )
        if bool(registration.get("required")) != required:
            errors.append("Cờ registration.required không khớp recruitment_mode")
        status = str(registration.get("status") or "").strip()
        if required and status != "REGISTERED":
            errors.append(
                "Thiết kế này chưa có trạng thái REGISTERED ở registry phù hợp"
            )
        if required:
            for field, label in (
                ("registry", "tên registry"),
                ("registration_id", "mã đăng ký"),
                ("registration_date", "ngày đăng ký"),
            ):
                if not str(registration.get(field) or "").strip():
                    errors.append(f"Thiếu {label}")
            registration_date = _parse_iso_date(registration.get("registration_date"))
            enrolment_date = _parse_iso_date(attestation.get("first_enrolment_date"))
            first_search_date = _parse_iso_date(attestation.get("first_search_date"))
            if registration_date is None:
                errors.append("Ngày đăng ký phải theo YYYY-MM-DD")
            elif registration_date > today:
                errors.append("Ngày đăng ký không được ở tương lai")
            if enrolment_date and registration_date and registration_date > enrolment_date:
                errors.append("Đăng ký muộn hơn ngày tuyển người tham gia đầu tiên")
            if design_code == "sr_ma" and first_search_date is None:
                errors.append("SR/MA thiếu ngày bắt đầu tìm kiếm")
            if (
                design_code == "sr_ma"
                and first_search_date
                and registration_date
                and registration_date > first_search_date
            ):
                errors.append("Đăng ký protocol muộn hơn ngày bắt đầu tìm kiếm")
        elif status != "NOT_REQUIRED":
            errors.append("Nghiên cứu không tuyển mới phải ghi registration.status=NOT_REQUIRED")

    base_hash = _sha256_text(strip_attestation(package_text))
    if attestation.get("package_sha256_before_attestation") != base_hash:
        errors.append("Hash hồ sơ nền không khớp attestation")
    return errors


def evaluate_g2_quality(
    *,
    study: str,
    design_code: str,
    package_path: Path,
    registration_path: Path,
    g1_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    guardrail_passed: bool,
    ledger_approved: bool,
    design_ambiguous: bool = False,
    today: Optional[date] = None,
) -> dict[str, Any]:
    """Đánh giá G2 theo lớp tự động và lớp quyết định người thật."""
    package_path = Path(package_path)
    registration_path = Path(registration_path)
    package_text = (
        package_path.read_text(encoding="utf-8")
        if package_path.exists()
        else ""
    )
    registration = _read_json(registration_path)
    automatic: list[dict[str, str]] = []
    approval: list[dict[str, str]] = []

    automatic.append(_criterion(
        "G2-AUTO-01",
        "Guardrail liêm chính G2 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa PII, nguồn, disclaimer hoặc tuyên bố vượt cổng trước khi nộp.",
    ))

    g1_status = (
        (g1_checkpoint.get("quality_gate") or {}).get("status")
        if isinstance(g1_checkpoint.get("quality_gate"), Mapping)
        else None
    )
    automatic.append(_criterion(
        "G2-AUTO-02",
        "G1 đã được PI/methodologist xác nhận",
        "PASS" if g1_status == "PASS_G1_CONFIRMED" else "REVIEW",
        f"G1 quality status={g1_status or 'thiếu'}",
        "Hoàn tất xác nhận phương pháp G1; có thể soạn G2 song song nhưng chưa khóa.",
    ))

    missing_markers = [
        marker for marker in _PACKAGE_MARKERS
        if marker.casefold() not in package_text.casefold()
    ]
    automatic.append(_criterion(
        "G2-AUTO-03",
        "Bộ hồ sơ IRB/ICF/DMP có đủ cấu trúc bắt buộc",
        "BLOCK" if missing_markers or not package_text else "PASS",
        (
            f"thiếu: {', '.join(missing_markers)}"
            if missing_markers
            else "đủ marker tài liệu 1-8, ICF, DMP, rủi ro/bồi thường/COI"
        ),
        "Sinh lại hoặc bổ sung phần hồ sơ bị thiếu.",
    ))

    registration_errors = _registration_draft_errors(registration)
    automatic.append(_criterion(
        "G2-AUTO-04",
        f"WHO TRDS {WHO_TRDS_VERSION} đủ {WHO_TRDS_ITEM_COUNT} mục",
        "BLOCK" if registration_errors else "PASS",
        "; ".join(registration_errors) if registration_errors else "24/24 mục đúng số và nhãn",
        "Sinh lại bản đăng ký từ nguồn WHO TRDS hiện hành.",
    ))

    unresolved = unresolved_critical_placeholders(package_text)
    automatic.append(_criterion(
        "G2-AUTO-05",
        "Không còn placeholder khoa học/vận hành trọng yếu",
        "REVIEW" if unresolved else "PASS",
        f"còn {len(unresolved)} dòng [CẦN] ngoài các dòng chỉ chứa PII",
        "Điền nội dung thật; với PII dùng bản nộp ngoài hệ thống và giữ bản redacted.",
    ))

    automatic.append(_criterion(
        "G2-AUTO-06",
        "Thiết kế và lộ trình đạo đức không còn mơ hồ",
        "REVIEW" if design_ambiguous else "PASS",
        f"design_code={design_code}; ambiguous={design_ambiguous}",
        "PI/methodologist xác nhận thiết kế rồi tính lại lộ trình IRB.",
    ))

    if design_code == "rct":
        safety_requirements = {
            "AE/SAE": ("AE/SAE",),
            "DSMB/DMC": ("DSMB", "DMC"),
            "quy tắc dừng": ("quy tắc dừng", "dừng nghiên cứu", "stopping rule"),
        }
        missing_safety = [
            label
            for label, alternatives in safety_requirements.items()
            if not any(
                token.casefold() in package_text.casefold()
                for token in alternatives
            )
        ]
        safety_status = "BLOCK" if missing_safety else "PASS"
        safety_evidence = (
            f"thiếu: {', '.join(missing_safety)}"
            if missing_safety else "có AE/SAE, DSMB/DMC và quy tắc dừng"
        )
    else:
        safety_status = "PASS"
        safety_evidence = "không phải RCT; kế hoạch an toàn điều chỉnh theo nguy cơ"
    automatic.append(_criterion(
        "G2-AUTO-07",
        "Kế hoạch an toàn tương xứng thiết kế",
        safety_status,
        safety_evidence,
        "Bổ sung giám sát AE/SAE, DSMB/DMC và stopping rules cho thử nghiệm.",
    ))

    attestation = extract_attestation(package_text)
    attestation_errors = validate_attestation(
        attestation=attestation,
        package_text=package_text,
        study=study,
        design_code=design_code,
        meta=meta,
        today=today,
    ) if attestation else ["Chưa có phụ lục quyết định IRB có cấu trúc"]
    approval.append(_criterion(
        "G2-HUMAN-01",
        "Quyết định IRB/IEC có số, ngày, hiệu lực, phạm vi và phiên bản",
        "PASS" if not attestation_errors else "REVIEW",
        "; ".join(attestation_errors) if attestation_errors else "attestation hợp lệ",
        "Hội đồng/đầu mối được ủy quyền ghi quyết định bằng approve_gate.py.",
    ))
    approval.append(_criterion(
        "G2-HUMAN-02",
        "Approval ledger đúng vai trò IRB và khớp hash artifact",
        "PASS" if ledger_approved else "REVIEW",
        f"ledger_approved={ledger_approved}",
        "Người có thẩm quyền IRB tự ký; agent không được chạy lệnh phê duyệt.",
    ))

    auto_blocked = any(row["status"] == "BLOCK" for row in automatic)
    auto_review = any(row["status"] == "REVIEW" for row in automatic)
    approval_complete = all(row["status"] == "PASS" for row in approval)
    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review:
        status = STATUS_DRAFT
    elif not attestation:
        status = STATUS_READY
    elif not approval_complete:
        status = STATUS_PENDING
    else:
        status = STATUS_APPROVED

    pending = [
        row["action"] for row in automatic + approval
        if row["status"] != "PASS" and row.get("action")
    ]
    return {
        "contract_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "gate": "G2",
        "status": status,
        "package_checks_passed": not auto_blocked,
        "package_ready_for_submission": not auto_blocked and not auto_review,
        "human_approval_complete": approval_complete,
        "automatic_criteria": automatic,
        "human_approval_criteria": approval,
        "unresolved_critical_placeholders": unresolved,
        "pending_actions": list(dict.fromkeys(pending)),
        "attestation": attestation,
        "standards_basis": list(STANDARDS_BASIS),
        "scope_statement": (
            "PASS_G2_APPROVED chỉ xác nhận dấu vết IRB/IEC, phiên bản và đăng ký "
            "đã cung cấp cho hệ thống. HMAC cục bộ không tự chứng minh tính độc lập "
            "của Hội đồng; hồ sơ gốc và quyết định thật vẫn phải được kiểm tra."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    """Ghi JSON máy đọc và Markdown để bác sĩ rà."""
    out_dir = Path(out_dir)
    json_path = out_dir / "G2_QUALITY_REPORT.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        f"# G2 QUALITY REPORT — {study}",
        "",
        f"- Trạng thái: **{report.get('status')}**",
        f"- Hồ sơ sẵn sàng nộp: **{report.get('package_ready_for_submission')}**",
        f"- Phê duyệt người thật đủ: **{report.get('human_approval_complete')}**",
        "",
        "## Kiểm tự động",
        "| ID | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(f"| {row['id']} | {row['label']} | {row['status']} | {evidence} |")
    lines.extend([
        "",
        "## Phê duyệt người thật",
        "| ID | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ])
    for row in report.get("human_approval_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(f"| {row['id']} | {row['label']} | {row['status']} | {evidence} |")
    lines.extend(["", "## Việc còn lại"])
    pending = report.get("pending_actions") or []
    lines.extend(f"- {item}" for item in pending)
    if not pending:
        lines.append("- Không còn mục chờ trong hợp đồng G2.")
    lines.extend([
        "",
        "## Giới hạn",
        str(report.get("scope_statement") or ""),
        "",
        "> Cần bác sĩ kiểm chứng.",
    ])
    md_path = out_dir / "G2_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def refresh_checkpoint(
    *,
    study: str,
    out_dir: Path,
    report: Mapping[str, Any],
    quality_report_path: Path,
) -> Path:
    """Cập nhật trạng thái G2 từ báo cáo; không tự tạo phê duyệt."""
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G2_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint.update({
        "study": study,
        "gate": "G2",
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "quality_gate": dict(report),
        "pending_doctor_actions": list(report.get("pending_actions") or []),
    })
    artifacts = checkpoint.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        checkpoint["artifacts"] = artifacts
    artifacts["quality_report"] = str(quality_report_path)
    if report.get("status") == STATUS_APPROVED:
        attestation = report.get("attestation") or {}
        registration = attestation.get("registration") or {}
        checkpoint.update({
            "gate_status": "PASS — G2 ĐÃ CÓ PHÊ DUYỆT IRB/IEC THẬT VÀ ĐĂNG KÝ HỢP LỆ",
            "g2_status": "LOCKED",
            "g2_irb_number": attestation.get("approval_number"),
            "g2_approval_date": attestation.get("approval_date"),
            "g2_approval_valid_until": attestation.get("valid_until"),
            "g2_no_expiry_confirmed": attestation.get("no_expiry_confirmed") is True,
            "g2_protocol_version": attestation.get("approved_protocol_version"),
            "g2_icf_version": attestation.get("approved_icf_version"),
            "g2_icf_waiver_approved": attestation.get("icf_waiver_approved") is True,
            "g2_registration": registration.get("registration_id"),
        })
    else:
        checkpoint["gate_status"] = f"{report.get('status')} — G2 CHƯA ĐƯỢC KHÓA"
        checkpoint["g2_status"] = "PENDING"
    checkpoint["disclaimer"] = "Cần bác sĩ kiểm chứng."
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return checkpoint_path


def evaluate_study(
    study: str,
    out_dir: Path,
    *,
    repo_root: Optional[Path] = None,
    write: bool = True,
    today: Optional[date] = None,
) -> dict[str, Any]:
    """Đọc artifact hiện có và đánh giá lại G2 mà không sinh/ghi phê duyệt."""
    out_dir = Path(out_dir)
    repo_root = Path(repo_root) if repo_root else out_dir.parent.parent
    checkpoint = _read_json(out_dir / "G2_checkpoint.json")
    g1 = _read_json(out_dir / "G1_checkpoint.json")
    meta = _read_json(out_dir / "study_meta.json")
    package_path = out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    registration_path = out_dir / f"G2_REGISTRATION_DRAFT_{study}.json"
    design_code = str(
        checkpoint.get("design_code")
        or (g1.get("design") or {}).get("internal_code")
        or "cohort"
    )
    guardrail = checkpoint.get("guardrail") or {}
    guardrail_passed = bool(
        isinstance(guardrail, Mapping) and guardrail.get("passed") is True
    )
    ledger_ok = GC.ledger_approved(
        "G2",
        study,
        package_path,
        repo_root=repo_root,
    )
    report = evaluate_g2_quality(
        study=study,
        design_code=design_code,
        package_path=package_path,
        registration_path=registration_path,
        g1_checkpoint=g1,
        meta=meta,
        guardrail_passed=guardrail_passed,
        ledger_approved=ledger_ok,
        design_ambiguous=bool(checkpoint.get("design_ambiguous")),
        today=today,
    )
    if write:
        report_path = write_quality_report(study, out_dir, report)
        refresh_checkpoint(
            study=study,
            out_dir=out_dir,
            report=report,
            quality_report_path=report_path,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Đánh giá lại G2; không tự phê duyệt hoặc ký thay IRB."
    )
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "exports" / args.study
    report = evaluate_study(args.study, out_dir, repo_root=repo_root, write=True)
    print(f"G2 quality status: {report['status']}")
    print(f"Báo cáo: {out_dir / 'G2_QUALITY_REPORT.md'}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
