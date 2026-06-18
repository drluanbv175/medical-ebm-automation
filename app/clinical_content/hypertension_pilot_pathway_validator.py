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


def _present_fields(payload: Mapping[str, object]) -> set[str]:
    return {key for key, value in payload.items() if value not in (None, "", [], {})}


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
            red_flags_present = sorted(str(flag) for flag, value in red_flag_screen.items() if value is True)
        elif red_flag_screen is True:
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
