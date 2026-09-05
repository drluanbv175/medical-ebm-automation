"""Release gate Phase 2C: luôn bảo vệ clinical production."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping

from app.clinical_content.pilot_pathway_builder import ReviewOnlyPathway
from app.core.feature_flags import merge_feature_flags

# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 15) — gate này trước
# đây chỉ kiểm 2/5 cờ nguy hiểm, trong khi module song song cho
# hypertension (hypertension_pilot_pathway_release_gate.py::RISKY_FLAGS)
# đã kiểm đủ 5. Bỏ sót v7_emr_write/v7_production_pathway/v7_patient_
# education_export khiến blocked_reasons — thứ dashboard/audit đọc để
# biết "vì sao/những rủi ro nào đang bật" — im lặng hoàn toàn khi 3 cờ đó
# đang bật, dù kết luận cuối (allowed=False) vẫn đúng nhờ dòng chặn cứng.
RISKY_FLAGS = {
    "v7_clinical_release",
    "v7_patient_education_export",
    "v7_emr_write",
    "v7_production_pathway",
    "v7_auto_apply_recommendations",
}


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
    for flag in sorted(RISKY_FLAGS):
        if flags.get(flag):
            reasons.append(f"risky_flag_must_remain_false:{flag}")
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
