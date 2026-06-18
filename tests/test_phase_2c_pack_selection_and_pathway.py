from pathlib import Path

from app.clinical_content.phase_2c_selection import Phase2CPackSelection, load_phase_2c_selection
from app.clinical_content.pilot_pathway_builder import EvidenceClaimLink, build_phase_2c_review_pathway
from app.clinical_content.pilot_pathway_release_gate import evaluate_phase_2c_release_gate
from app.clinical_content.pilot_pathway_validator import validate_review_only_pathway


def test_phase_2c_current_selection_blocks_real_pack_build_until_approved():
    selection = load_phase_2c_selection(Path("config/phase_2c_pilot_selection.yaml"))
    result = build_phase_2c_review_pathway(selection, [])

    assert selection.selected_pack == "hypertension_adult_outpatient"
    assert selection.approval_status == "pending"
    assert selection.approved_for_real_pack_build is False
    assert "approval_not_approved:pending" in result.blocked_reasons


def test_phase_2c_approved_selection_builds_review_only_pathway_but_release_gate_blocks():
    selection = Phase2CPackSelection(
        selected_pack="hypertension_adult_outpatient",
        physician_approval_required=True,
        approval_record_path="approval.json",
        approval_status="approved",
    )
    claim = EvidenceClaimLink(
        claim_id="claim_1",
        evidence_id="evidence_1",
        verification_status="VERIFIED",
        claim_location="section 1",
        approval_status="approved",
    )
    build = build_phase_2c_review_pathway(selection, [claim])

    assert build.status == "built_review_only"
    assert build.pathway is not None
    validation = validate_review_only_pathway(build.pathway)
    gate = evaluate_phase_2c_release_gate(
        build.pathway,
        feature_flags={"v7_clinical_release": False},
        medication_safety_passed=True,
    )

    assert validation.valid
    assert gate.allowed is False
    assert "clinical_release_not_in_phase_2c_scope" in gate.blocked_reasons
