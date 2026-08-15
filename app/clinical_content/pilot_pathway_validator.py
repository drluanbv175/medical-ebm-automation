"""Validator Phase 2C review-only pathway."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.clinical_content.pilot_pathway_builder import ReviewOnlyPathway


@dataclass(frozen=True)
class PathwayValidationResult:
    valid: bool
    issues: List[str] = field(default_factory=list)


def validate_review_only_pathway(pathway: ReviewOnlyPathway) -> PathwayValidationResult:
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
    if not pathway.review_only:
        issues.append("pathway_not_review_only")
    if pathway.can_create_prescription:
        issues.append("prescription_generation_not_allowed")
    if pathway.environment not in {"review", "shadow", "test"}:
        issues.append("environment_not_allowed")
    if pathway.physician_review_requirement != "required":
        issues.append("physician_review_not_required")
    return PathwayValidationResult(valid=not issues, issues=issues)
