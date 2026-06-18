"""Builder review-only pathway Phase 2C."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping

from app.clinical_content.phase_2c_selection import Phase2CPackSelection


@dataclass(frozen=True)
class EvidenceClaimLink:
    claim_id: str
    evidence_id: str
    verification_status: str
    claim_location: str
    approval_status: str = "pending_physician"
    physician_exception_reason: str = ""

    @property
    def release_ready(self) -> bool:
        return (
            self.verification_status == "VERIFIED"
            and bool(self.claim_location)
            and self.approval_status == "approved"
        )


@dataclass(frozen=True)
class ReviewOnlyPathway:
    pathway_id: str
    pathway_version: str
    environment: str
    entry_criteria: List[str]
    required_inputs: List[str]
    data_sufficiency_rules: List[str]
    red_flags: List[str]
    hard_stop_conditions: List[str]
    decision_nodes: List[Mapping[str, object]]
    evidence_claim_links: List[EvidenceClaimLink]
    medication_safety_requirement: str
    uncertainty_escalation: str
    follow_up_rules: List[str]
    referral_rules: List[str]
    physician_review_requirement: str = "required"
    review_only: bool = True
    can_create_prescription: bool = False


@dataclass(frozen=True)
class PathwayBuildResult:
    status: str
    pathway: ReviewOnlyPathway | None = None
    blocked_reasons: List[str] = field(default_factory=list)


def build_phase_2c_review_pathway(
    selection: Phase2CPackSelection,
    evidence_claim_links: List[EvidenceClaimLink],
) -> PathwayBuildResult:
    if not selection.approved_for_real_pack_build:
        return PathwayBuildResult(status="blocked", blocked_reasons=selection.blocked_reasons)
    pathway = ReviewOnlyPathway(
        pathway_id=str(selection.selected_pack),
        pathway_version="2026.1",
        environment="review",
        entry_criteria=["adult_outpatient_review_only"],
        required_inputs=["age_group", "clinical_domain", "question_type", "red_flag_screen"],
        data_sufficiency_rules=["missing_required_input_waiting_for_input"],
        red_flags=["acute_severe_symptom", "suspected_emergency", "unstable_vital_sign"],
        hard_stop_conditions=["red_flag_present", "pii_detected", "unverified_evidence"],
        decision_nodes=[{"node_id": "review_gate", "action": "draft_only"}],
        evidence_claim_links=evidence_claim_links,
        medication_safety_requirement="required_for_medication_related_recommendations",
        uncertainty_escalation="physician_review_required",
        follow_up_rules=["draft_follow_up_only_after_physician_review"],
        referral_rules=["urgent_or_emergency_referral_for_red_flags"],
    )
    return PathwayBuildResult(status="built_review_only", pathway=pathway)
