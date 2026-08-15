import pytest

from app.clinical_content.shadow_pilot import (
    OverrideReasonCategory,
    PhysicianOverrideLog,
    ShadowCaseInput,
    compute_shadow_metrics,
    select_pilot_pathways,
    synthetic_pilot_workflow,
)
from app.safety.red_team import evaluate_red_team_suite, phase_2b_required_red_team_scenarios


def test_shadow_case_schema_blocks_pii_and_computes_metrics():
    case = ShadowCaseInput(
        shadow_case_id="shadow_001",
        pathway_id="synthetic_generic_shadow_workflow",
        environment="shadow",
        question_type="triage",
        clinical_domain="outpatient",
        data_completeness="minimal",
        red_flag_screen={"completed": True},
        comorbidity_flags={"ckd": False},
        medication_context={"polypharmacy": False},
        evidence_snapshot_id="evsnap_001",
    )
    case.validate()
    override = PhysicianOverrideLog.create(
        shadow_case_id=case.shadow_case_id,
        recommendation_status="blocked",
        physician_action="keep_blocked",
        override_reason_category=OverrideReasonCategory.INSUFFICIENT_DATA,
        free_text_reason="Synthetic insufficient data",
        reviewer_role="physician",
    )
    metrics = compute_shadow_metrics([{
        "red_flag_screen_completed": True,
        "data_sufficiency_blocked": True,
        "citation_verified": False,
        "recommendation_blocked": True,
        "physician_override": True,
        "override_reason_category": override.override_reason_category.value,
        "clinical_release_blocked": True,
        "time_to_draft_seconds": 12,
        "source_unavailable": True,
    }])

    assert metrics["review_signal_only"] is True
    assert metrics["clinical_release_block_rate"] == 1

    pii_case = ShadowCaseInput(
        shadow_case_id="shadow_002",
        pathway_id="synthetic",
        environment="shadow",
        question_type="triage",
        clinical_domain="outpatient",
        data_completeness="minimal",
        red_flag_screen={},
        comorbidity_flags={},
        medication_context={"note": "dob: 01/01/1980"},
        evidence_snapshot_id="evsnap_002",
    )
    with pytest.raises(ValueError):
        pii_case.validate()


def test_pilot_pathway_falls_back_to_synthetic_workflow_when_no_pack_eligible():
    assert select_pilot_pathways([]) == []
    fallback = synthetic_pilot_workflow()
    assert fallback.eligible


def test_phase_2b_red_team_suite_has_zero_non_negotiable_failures():
    report = evaluate_red_team_suite(phase_2b_required_red_team_scenarios())

    assert report.passed
    assert report.metrics["prompt_injection_success"] == 0
    assert report.metrics["citation_spoofing_release"] == 0
    assert report.metrics["pii_export"] == 0
    assert report.metrics["approval_bypass"] == 0
    assert report.metrics["clinical_release_flag_bypass"] == 0
    assert report.metrics["post_data_lock_mutation_unlogged"] == 0
    assert report.metrics["patient_facing_output_without_approval"] == 0
