"""Release gate Phase 2C: luôn bảo vệ clinical production."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping

from app.clinical_content.pilot_pathway_builder import ReviewOnlyPathway
from app.core.feature_flags import merge_feature_flags


@dataclass(frozen=True)
class PathwayReleaseGateResult:
    allowed: bool
    status: str
    blocked_reasons: List[str] = field(default_factory=list)


def evaluate_phase_2c_release_gate(
    pathway: ReviewOnlyPathway,
    *,
    feature_flags: Mapping[str, bool],
    medication_safety_passed: bool,
) -> PathwayReleaseGateResult:
    flags = merge_feature_flags(feature_flags)
    reasons: List[str] = []
    if flags.get("v7_clinical_release"):
        reasons.append("clinical_release_flag_must_remain_false")
    if flags.get("v7_auto_apply_recommendations"):
        reasons.append("auto_apply_must_remain_false")
    if not pathway.review_only:
        reasons.append("pathway_not_review_only")
    if pathway.can_create_prescription:
        reasons.append("prescription_generation_not_allowed")
    if not medication_safety_passed:
        reasons.append("medication_safety_required")
    for link in pathway.evidence_claim_links:
        if not link.release_ready:
            reasons.append(f"claim_not_release_ready:{link.claim_id}")
    # Phase 2C real-pack pilot is still shadow/review only, so clinical release is never allowed.
    reasons.append("clinical_release_not_in_phase_2c_scope")
    return PathwayReleaseGateResult(
        allowed=False,
        status="review_only_blocked_for_release",
        blocked_reasons=reasons,
    )
