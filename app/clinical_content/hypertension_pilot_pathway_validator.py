"""Validator cho pathway tăng huyết áp ngoại trú Phase 2C."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Mapping

from app.clinical_content.hypertension_pilot_pathway_builder import HypertensionReviewPathway

FORBIDDEN_INPUT_FIELDS = {
    "patient_name",
    "date_of_birth",
    "phone_number",
    "address",
    "medical_record_number",
    "exact_visit_date",
    "photo",
    "free_text_containing_identifiers",
}


@dataclass(frozen=True)
class HypertensionPathwayValidationResult:
    valid: bool
    status: str
    issues: List[str] = field(default_factory=list)
    missing_inputs: List[str] = field(default_factory=list)
    red_flags_present: List[str] = field(default_factory=list)


def _has_value(value: object) -> bool:
    """`value not in (None, "", [], {})` mà chuỗi CHỈ TOÀN KHOẢNG TRẮNG cũng
    coi là RỖNG.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #92, vòng 7, phát
    hiện #5) — bản gốc chỉ loại chuỗi rỗng tuyệt đối (`""`); một giá trị
    `"   "` (dấu cách do lỗi nhập liệu/mặc định của form web) KHÁC `""` nên
    vẫn được `_present_fields()` tính là "đã điền", làm `missing_inputs`
    BỎ LỌT một `required_inputs` thực chất còn trống — sai NGƯỢC chiều an
    toàn (hard-stop "missing_required_input" không kích hoạt dù dữ liệu
    lâm sàng chưa có nội dung thật)."""
    if isinstance(value, str):
        return value.strip() != ""
    return value not in (None, [], {})


def _present_fields(payload: Mapping[str, object]) -> set[str]:
    return {key for key, value in payload.items() if _has_value(value)}


def _is_true_flag(value: object) -> bool:
    """Coi `value` là cờ TRUE mà KHÔNG dựa vào identity `is True`.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #92, vòng 7, phát
    hiện #4) — `red_flag_screen` khai kiểu `Mapping[str, object]` (không
    ép `bool`, xem `phase_2c_shadow.py::Phase2CShadowCase`), nên một
    producer tuân thủ ĐÚNG type hint đó được quyền gửi `1`/`1.0` cho "có
    cờ đỏ". Bản gốc dùng `value is True` — kiểm IDENTITY, không phải
    EQUALITY — nên `1 is True` cho `False` dù `1 == True`; một cờ đỏ
    dương tính hợp lệ (vd "chest_pain_or_suspected_acute_coronary_
    syndrome": 1) bị BỎ LỌT, khiến pathway KHÔNG dừng dù đáng lẽ phải
    `STOP_OUTPATIENT_PATHWAY` — sai NGƯỢC chiều an toàn. Cố ý KHÔNG coi
    chuỗi non-empty là true (vd "false" là chuỗi khác rỗng) — chỉ mở
    rộng cho bool/số, không suy đoán cú pháp chuỗi mà repo chưa có bằng
    chứng nào dùng tới."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return False


def validate_hypertension_review_pathway(
    pathway: HypertensionReviewPathway,
    clinical_payload: Mapping[str, object] | None = None,
) -> HypertensionPathwayValidationResult:
    issues: List[str] = []
    required_lists = {
        "entry_criteria": pathway.entry_criteria,
        "required_inputs": pathway.required_inputs,
        "data_sufficiency_rules": pathway.data_sufficiency_rules,
        "red_flags": pathway.red_flags,
        "hard_stop_conditions": pathway.hard_stop_conditions,
        "decision_nodes": pathway.decision_nodes,
        "evidence_claim_links": pathway.evidence_claim_links,
        "follow_up_rules": pathway.follow_up_rules,
        "referral_rules": pathway.referral_rules,
    }
    issues.extend(name for name, value in required_lists.items() if not value)
    if pathway.environment != "review":
        issues.append("environment_must_be_review")
    if not pathway.review_only:
        issues.append("pathway_not_review_only")
    if pathway.can_create_prescription:
        issues.append("prescription_generation_not_allowed")
    if pathway.can_generate_medication_dose:
        issues.append("dose_generation_not_allowed")
    if pathway.can_send_patient_facing_output:
        issues.append("patient_facing_output_not_allowed")
    if pathway.can_write_emr:
        issues.append("emr_write_not_allowed")
    if pathway.physician_review_requirement != "required":
        issues.append("physician_review_not_required")
    if not any(condition.startswith("red_flag_present:") for condition in pathway.hard_stop_conditions):
        issues.append("red_flag_hard_stop_missing")
    if not any(condition.startswith("missing_required_input:") for condition in pathway.hard_stop_conditions):
        issues.append("missing_input_hard_stop_missing")
    if not any(condition.startswith("evidence_not_verified:") for condition in pathway.hard_stop_conditions):
        issues.append("evidence_gate_missing")

    missing_inputs: List[str] = []
    red_flags_present: List[str] = []
    if clinical_payload is not None:
        present = _present_fields(clinical_payload)
        forbidden = sorted(FORBIDDEN_INPUT_FIELDS & present)
        issues.extend(f"pii_or_forbidden_input:{field}" for field in forbidden)
        missing_inputs = [field for field in pathway.required_inputs if field not in present]
        red_flag_screen = clinical_payload.get("red_flag_screen", {})
        if isinstance(red_flag_screen, Mapping):
            red_flags_present = sorted(
                str(flag) for flag, value in red_flag_screen.items() if _is_true_flag(value)
            )
        elif _is_true_flag(red_flag_screen):
            red_flags_present = ["red_flag_screen_positive"]

    if red_flags_present:
        status = "STOP_OUTPATIENT_PATHWAY"
    elif missing_inputs:
        status = "WAITING_FOR_INPUT"
    elif issues:
        status = "INVALID_REVIEW_PATHWAY"
    else:
        status = "VALID_REVIEW_ONLY"

    return HypertensionPathwayValidationResult(
        valid=not issues and not red_flags_present and not missing_inputs,
        status=status,
        issues=issues,
        missing_inputs=missing_inputs,
        red_flags_present=red_flags_present,
    )


def count_red_flag_misses(results: Iterable[HypertensionPathwayValidationResult]) -> int:
    """Đếm tình huống có red flag nhưng validator không dừng pathway."""
    misses = 0
    for result in results:
        if result.red_flags_present and result.status != "STOP_OUTPATIENT_PATHWAY":
            misses += 1
    return misses
