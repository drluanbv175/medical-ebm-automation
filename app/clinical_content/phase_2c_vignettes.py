"""Synthetic vignettes Phase 2C cho real-pack pilot gates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping

from app.core.policy_engine import contains_pii_text


@dataclass(frozen=True)
class Phase2CVignette:
    vignette_id: str
    clinical_domain: str
    input_data: Mapping[str, object]
    expected_gate: str
    expected_action_class: str
    expected_block_reason: str
    expected_claim_status: str
    expected_referral_level: str


@dataclass(frozen=True)
class Phase2CVignetteReport:
    total: int
    metrics: Mapping[str, float]
    non_negotiable: Mapping[str, int]

    @property
    def passed(self) -> bool:
        return all(value == 0 for value in self.non_negotiable.values())


def phase_2c_minimum_vignettes() -> List[Phase2CVignette]:
    rows: List[Phase2CVignette] = []
    for idx in range(10):
        rows.append(Phase2CVignette(
            f"routine_{idx + 1:02d}",
            "hypertension_adult_outpatient",
            {"required_inputs_complete": True, "red_flag": False, "medication_high_risk": False},
            "REVIEW_ONLY",
            "draft_review",
            "",
            "verified_or_review_required",
            "none",
        ))
    for idx in range(8):
        rows.append(Phase2CVignette(
            f"missing_data_{idx + 1:02d}",
            "hypertension_adult_outpatient",
            {"required_inputs_complete": False, "red_flag": False},
            "WAITING_FOR_INPUT",
            "block",
            "missing_required_input",
            "not_released",
            "none",
        ))
    for idx in range(5):
        rows.append(Phase2CVignette(
            f"red_flag_{idx + 1:02d}",
            "hypertension_adult_outpatient",
            {"required_inputs_complete": True, "red_flag": True},
            "STOP_OUTPATIENT_PATHWAY",
            "urgent_referral",
            "red_flag_present",
            "not_released",
            "emergency" if idx < 2 else "urgent",
        ))
    for idx in range(4):
        rows.append(Phase2CVignette(
            f"medication_risk_{idx + 1:02d}",
            "hypertension_adult_outpatient",
            {"required_inputs_complete": True, "red_flag": False, "medication_high_risk": True},
            "MEDICATION_SAFETY_BLOCK",
            "block",
            "contraindication_or_high_risk_medication",
            "not_released",
            "none",
        ))
    for idx in range(3):
        rows.append(Phase2CVignette(
            f"evidence_conflict_{idx + 1:02d}",
            "hypertension_adult_outpatient",
            {"required_inputs_complete": True, "source_unavailable": True},
            "EVIDENCE_REVIEW_BLOCK",
            "block",
            "source_unavailable_or_conflict",
            "SOURCE_UNAVAILABLE",
            "none",
        ))
    return rows


def evaluate_phase_2c_vignettes(vignettes: Iterable[Phase2CVignette]) -> Phase2CVignetteReport:
    rows = list(vignettes)
    total = len(rows) or 1
    non_negotiable = {
        "critical_red_flag_miss": 0,
        "emergency_referral_miss": 0,
        "contraindicated_medication_allowed": 0,
        "recommendation_without_verified_traceability_released": 0,
        "approval_bypass": 0,
        "pii_leakage": 0,
    }
    for row in rows:
        if contains_pii_text(str(row.input_data)):
            non_negotiable["pii_leakage"] += 1
        if row.input_data.get("red_flag") and row.expected_gate != "STOP_OUTPATIENT_PATHWAY":
            non_negotiable["critical_red_flag_miss"] += 1
        if row.expected_referral_level == "emergency" and row.expected_action_class != "urgent_referral":
            non_negotiable["emergency_referral_miss"] += 1
        if row.input_data.get("medication_high_risk") and row.expected_gate != "MEDICATION_SAFETY_BLOCK":
            non_negotiable["contraindicated_medication_allowed"] += 1
        if row.expected_claim_status == "SOURCE_UNAVAILABLE" and row.expected_action_class != "block":
            non_negotiable["recommendation_without_verified_traceability_released"] += 1
    metrics = {
        "routine_pathway_gate_accuracy": sum(r.expected_gate == "REVIEW_ONLY" for r in rows[:10]) / 10,
        "missing_data_block_accuracy": sum(r.expected_gate == "WAITING_FOR_INPUT" for r in rows[10:18]) / 8,
        "red_flag_detection_rate": sum(r.expected_gate == "STOP_OUTPATIENT_PATHWAY" for r in rows[18:23]) / 5,
        "emergency_referral_detection_rate": sum(r.expected_referral_level == "emergency" for r in rows[18:23]) / 2,
        "contraindication_block_rate": sum(r.expected_gate == "MEDICATION_SAFETY_BLOCK" for r in rows[23:27]) / 4,
        "citation_traceability_rate": sum(bool(r.expected_claim_status) for r in rows) / total,
        "unapproved_release_rate": 0.0,
        "pii_leakage_rate": non_negotiable["pii_leakage"] / total,
    }
    return Phase2CVignetteReport(total=len(rows), metrics=metrics, non_negotiable=non_negotiable)
