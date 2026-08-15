"""Release gate cho pathway tăng huyết áp ngoại trú Phase 2C."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping

from app.clinical_content.hypertension_pilot_pathway_builder import HypertensionReviewPathway
from app.clinical_content.hypertension_pilot_pathway_validator import validate_hypertension_review_pathway
from app.core.feature_flags import merge_feature_flags

RISKY_FLAGS = {
    "v7_clinical_release",
    "v7_patient_education_export",
    "v7_emr_write",
    "v7_production_pathway",
    "v7_auto_apply_recommendations",
}


@dataclass(frozen=True)
class HypertensionReleaseGateResult:
    allowed: bool
    status: str
    blocked_reasons: List[str] = field(default_factory=list)


def evaluate_hypertension_release_gate(
    pathway: HypertensionReviewPathway,
    *,
    feature_flags: Mapping[str, bool],
    medication_safety_passed: bool,
    selected_pack_approved: bool,
    dashboard_read_only: bool,
    shadow_schema_has_pii: bool,
) -> HypertensionReleaseGateResult:
    flags = merge_feature_flags(feature_flags)
    reasons: List[str] = []
    validation = validate_hypertension_review_pathway(pathway)
    reasons.extend(validation.issues)

    for flag in sorted(RISKY_FLAGS):
        if flags.get(flag):
            reasons.append(f"risky_flag_must_remain_false:{flag}")
    if not selected_pack_approved:
        reasons.append("selected_pack_not_approved")
    if not dashboard_read_only:
        reasons.append("dashboard_not_read_only")
    if shadow_schema_has_pii:
        reasons.append("shadow_schema_contains_pii")
    if not medication_safety_passed:
        reasons.append("medication_safety_required")
    if not pathway.review_only:
        reasons.append("pathway_not_review_only")
    if pathway.can_create_prescription:
        reasons.append("prescription_generation_not_allowed")
    if pathway.can_generate_medication_dose:
        reasons.append("dose_generation_not_allowed")
    if pathway.can_send_patient_facing_output:
        reasons.append("patient_facing_output_not_allowed")
    if pathway.can_write_emr:
        reasons.append("emr_write_not_allowed")
    for link in pathway.evidence_claim_links:
        if not link.claim_location:
            reasons.append(f"claim_location_missing:{link.claim_id}")
        if link.verification_status in {"SOURCE_UNAVAILABLE", "STALE", "RETRACTED", "UNVERIFIED", ""}:
            reasons.append(f"claim_verification_blocks_release:{link.claim_id}:{link.verification_status}")
        if not link.release_ready:
            reasons.append(f"claim_not_release_ready:{link.claim_id}")

    # Phase 2C chỉ cho shadow/review. Clinical production luôn bị chặn.
    reasons.append("clinical_production_release_not_allowed_in_phase_2c")
    return HypertensionReleaseGateResult(
        allowed=False,
        status="review_only_release_blocked",
        blocked_reasons=sorted(set(reasons)),
    )
