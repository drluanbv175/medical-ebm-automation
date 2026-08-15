"""Đánh giá hiệu chỉnh địa phương cho gói tăng huyết áp Phase 2C."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping

LOCAL_ADAPTATION_DOMAINS = [
    "availability_of_medicine",
    "monitoring",
    "lab_testing",
    "outpatient_feasibility",
    "renal_function_monitoring",
    "pregnancy_reproductive",
    "local_constraints",
    "referral",
    "internal_policy",
]


@dataclass(frozen=True)
class HypertensionLocalAdaptationResult:
    claim_id: str
    status: str
    domain_assessments: Mapping[str, str]
    original_certainty_preserved: bool = True
    guideline_meaning_preserved: bool = True
    notes: str = "Cần bác sĩ kiểm chứng và đối chiếu chính sách/nguồn lực tại đơn vị."


def assess_hypertension_local_adaptation(
    claim: Mapping[str, object],
    local_context: Mapping[str, object] | None = None,
) -> HypertensionLocalAdaptationResult:
    context = local_context or {}
    assessments = {}
    for domain in LOCAL_ADAPTATION_DOMAINS:
        if context.get(domain):
            assessments[domain] = "locally_documented_needs_physician_confirmation"
        else:
            assessments[domain] = "needs_local_confirmation"
    status = "needs_local_review"
    if all(value == "locally_documented_needs_physician_confirmation" for value in assessments.values()):
        status = "local_context_documented_pending_physician_approval"
    return HypertensionLocalAdaptationResult(
        claim_id=str(claim.get("claim_id", "")),
        status=status,
        domain_assessments=assessments,
    )


def assess_hypertension_manifest_local_adaptation(
    manifest: Mapping[str, object],
    local_context: Mapping[str, object] | None = None,
) -> List[HypertensionLocalAdaptationResult]:
    claims = manifest.get("claims", [])
    if not isinstance(claims, list):
        return []
    return [
        assess_hypertension_local_adaptation(claim, local_context)
        for claim in claims
        if isinstance(claim, Mapping)
    ]
