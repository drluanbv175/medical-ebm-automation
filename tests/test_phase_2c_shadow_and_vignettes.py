import pytest

from app.clinical_content.phase_2c_shadow import (
    Phase2COverrideReason,
    Phase2CShadowPilotCase,
    Phase2CShadowReviewLog,
)
from app.clinical_content.phase_2c_vignettes import evaluate_phase_2c_vignettes, phase_2c_minimum_vignettes


def test_phase_2c_shadow_schema_blocks_pii_and_requires_review():
    case = Phase2CShadowPilotCase(
        shadow_pilot_case_id="shadow2c_001",
        pathway_id="review_only",
        pathway_version="2026.1",
        environment="shadow",
        clinical_domain="generic_outpatient",
        question_type="review",
        data_completeness="minimal",
        red_flag_screen={"completed": True},
        comorbidity_flags={"ckd": False},
        medication_context={"high_risk": False},
        evidence_snapshot_id="evsnap_2c_001",
    )
    case.validate()
    review = Phase2CShadowReviewLog.create(
        shadow_pilot_case_id=case.shadow_pilot_case_id,
        pathway_result_status="blocked_review_only",
        physician_agreement="agree",
        override_reason_category=Phase2COverrideReason.INSUFFICIENT_DATA,
        free_text_reason="Synthetic no PII reason",
        reviewer_role="physician",
    )
    assert review.shadow_review_id.startswith("shadow_review_")

    pii_case = Phase2CShadowPilotCase(
        shadow_pilot_case_id="shadow2c_002",
        pathway_id="review_only",
        pathway_version="2026.1",
        environment="shadow",
        clinical_domain="generic_outpatient",
        question_type="review",
        data_completeness="minimal",
        red_flag_screen={},
        comorbidity_flags={},
        medication_context={"note": "phone 0912345678"},
        evidence_snapshot_id="evsnap_2c_002",
    )
    with pytest.raises(ValueError):
        pii_case.validate()


def test_phase_2c_minimum_vignettes_have_required_distribution_and_zero_blockers():
    report = evaluate_phase_2c_vignettes(phase_2c_minimum_vignettes())

    assert report.total == 30
    assert report.passed
    assert report.metrics["routine_pathway_gate_accuracy"] == 1
    assert report.metrics["missing_data_block_accuracy"] == 1
    assert report.metrics["red_flag_detection_rate"] == 1
    assert report.metrics["contraindication_block_rate"] == 1
    assert report.non_negotiable["critical_red_flag_miss"] == 0
    assert report.non_negotiable["emergency_referral_miss"] == 0
    assert report.non_negotiable["contraindicated_medication_allowed"] == 0
    assert report.non_negotiable["recommendation_without_verified_traceability_released"] == 0
    assert report.non_negotiable["approval_bypass"] == 0
    assert report.non_negotiable["pii_leakage"] == 0
