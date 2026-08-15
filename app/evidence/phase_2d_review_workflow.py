"""Workflow review chứng cứ Phase 2D."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Mapping


class Phase2DReviewState(str, Enum):
    DRAFT = "DRAFT"
    SOURCE_IMPORTED = "SOURCE_IMPORTED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    CLAIM_MAPPED = "CLAIM_MAPPED"
    EVIDENCE_REVIEWED = "EVIDENCE_REVIEWED"
    NEEDS_PHYSICIAN_APPROVAL = "NEEDS_PHYSICIAN_APPROVAL"
    APPROVED_FOR_SHADOW_REVIEW = "APPROVED_FOR_SHADOW_REVIEW"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


ALLOWED_TRANSITIONS = {
    Phase2DReviewState.DRAFT: {Phase2DReviewState.SOURCE_IMPORTED, Phase2DReviewState.SUPERSEDED},
    Phase2DReviewState.SOURCE_IMPORTED: {Phase2DReviewState.SOURCE_VERIFIED, Phase2DReviewState.SUPERSEDED},
    Phase2DReviewState.SOURCE_VERIFIED: {Phase2DReviewState.CLAIM_MAPPED, Phase2DReviewState.SUPERSEDED},
    Phase2DReviewState.CLAIM_MAPPED: {Phase2DReviewState.EVIDENCE_REVIEWED, Phase2DReviewState.SUPERSEDED},
    Phase2DReviewState.EVIDENCE_REVIEWED: {
        Phase2DReviewState.NEEDS_PHYSICIAN_APPROVAL,
        Phase2DReviewState.SUPERSEDED,
    },
    Phase2DReviewState.NEEDS_PHYSICIAN_APPROVAL: {
        Phase2DReviewState.APPROVED_FOR_SHADOW_REVIEW,
        Phase2DReviewState.SUPERSEDED,
        Phase2DReviewState.RETIRED,
    },
    Phase2DReviewState.APPROVED_FOR_SHADOW_REVIEW: {Phase2DReviewState.SUPERSEDED, Phase2DReviewState.RETIRED},
    Phase2DReviewState.SUPERSEDED: {Phase2DReviewState.RETIRED},
    Phase2DReviewState.RETIRED: set(),
}


@dataclass(frozen=True)
class ReviewTransitionResult:
    allowed: bool
    from_state: Phase2DReviewState
    to_state: Phase2DReviewState
    issues: List[str] = field(default_factory=list)


def evaluate_review_transition(
    from_state: Phase2DReviewState,
    to_state: Phase2DReviewState,
    *,
    reviewer_validated: bool = False,
    approval_record_valid: bool = False,
) -> ReviewTransitionResult:
    issues: List[str] = []
    if to_state not in ALLOWED_TRANSITIONS[from_state]:
        issues.append(f"transition_not_allowed:{from_state.value}->{to_state.value}")
    if from_state == Phase2DReviewState.SOURCE_IMPORTED and to_state == Phase2DReviewState.SOURCE_VERIFIED:
        if not reviewer_validated:
            issues.append("reviewer_validation_required_for_source_verified")
    if from_state == Phase2DReviewState.NEEDS_PHYSICIAN_APPROVAL:
        if to_state == Phase2DReviewState.APPROVED_FOR_SHADOW_REVIEW and not approval_record_valid:
            issues.append("valid_approval_record_required")
    if to_state.value == "CLINICAL_RELEASE":
        issues.append("clinical_release_not_allowed_in_phase_2d")
    return ReviewTransitionResult(
        allowed=not issues,
        from_state=from_state,
        to_state=to_state,
        issues=issues,
    )


REQUIRED_APPROVAL_FIELDS = {
    "approver_name_or_non_pii_id",
    "approver_role",
    "approval_scope",
    "pack_version",
    "approval_date",
    "approval_decision",
    "conditions_or_limitations",
    "signature_or_external_reference",
}


def validate_shadow_approval_record(record: Mapping[str, object]) -> List[str]:
    issues: List[str] = []
    for field_name in sorted(REQUIRED_APPROVAL_FIELDS):
        if not record.get(field_name):
            issues.append(f"missing_approval_field:{field_name}")
    if record.get("generated_by_system") is True:
        issues.append("approval_record_must_not_be_auto_generated")
    if record.get("approval_decision") not in {"approved_for_shadow_review", "rejected", "needs_revision"}:
        issues.append("approval_decision_not_allowed")
    if record.get("clinical_release") is True:
        issues.append("clinical_release_not_allowed")
    return issues
