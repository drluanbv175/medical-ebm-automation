import json

from app.clinical_content.hypertension_pilot_pathway_builder import (
    PACK_ROOT,
    build_hypertension_review_pathway,
    load_hypertension_claim_links,
)
from app.clinical_content.hypertension_pilot_pathway_release_gate import evaluate_hypertension_release_gate
from app.clinical_content.hypertension_pilot_pathway_validator import validate_hypertension_review_pathway
from app.evidence.hypertension_local_adaptation import (
    LOCAL_ADAPTATION_DOMAINS,
    assess_hypertension_manifest_local_adaptation,
)

REQUIRED_PACK_FILES = {
    "01_scope.yaml",
    "02_input_requirements.yaml",
    "03_red_flags.yaml",
    "04_pathway_rules.yaml",
    "05_recommendations.yaml",
    "06_drug_safety_rules.yaml",
    "07_follow_up_rules.yaml",
    "08_referral_rules.yaml",
    "09_local_adaptation.yaml",
    "10_evidence_manifest.json",
    "11_test_cases.json",
    "12_change_log.md",
    "13_approval_record.json",
}


def test_hypertension_pack_has_required_review_only_artifacts():
    present = {path.name for path in PACK_ROOT.iterdir() if path.is_file()}

    assert REQUIRED_PACK_FILES <= present
    approval = json.loads((PACK_ROOT / "13_approval_record.json").read_text(encoding="utf-8"))
    assert approval["status"] == "pending"
    assert approval["clinical_release_allowed"] is False
    assert approval["patient_facing_output_allowed"] is False


def test_hypertension_manifest_claims_are_traceable_but_blocked_until_verified():
    manifest = json.loads((PACK_ROOT / "10_evidence_manifest.json").read_text(encoding="utf-8"))
    required_claim_fields = {
        "claim_id",
        "evidence_id",
        "topic",
        "population",
        "clinical_question",
        "recommendation_text_draft",
        "source_type",
        "source_url",
        "pmid_or_doi_if_available",
        "organization",
        "publication_or_version_date",
        "claim_location",
        "certainty_original",
        "verification_status",
        "freshness_status",
        "local_applicability_status",
        "approval_status",
    }

    assert manifest["release_allowed"] is False
    assert manifest["claims"]
    for claim in manifest["claims"]:
        assert required_claim_fields <= set(claim)
        assert claim["claim_location"]
        assert claim["verification_status"] == "SOURCE_UNAVAILABLE"
        assert claim["approval_status"] == "pending"
        assert claim["release"] == "blocked"


def test_hypertension_pathway_waits_for_missing_inputs_and_stops_for_red_flags():
    pathway = build_hypertension_review_pathway()
    waiting = validate_hypertension_review_pathway(pathway, {"age_group": "adult", "red_flag_screen": {}})
    red_flag = validate_hypertension_review_pathway(
        pathway,
        {
            field: "documented"
            for field in pathway.required_inputs
        }
        | {"red_flag_screen": {"chest_pain_or_suspected_acute_coronary_syndrome": True}},
    )

    assert waiting.status == "WAITING_FOR_INPUT"
    assert "outpatient_stability_status" in waiting.missing_inputs
    assert red_flag.status == "STOP_OUTPATIENT_PATHWAY"
    assert red_flag.red_flags_present == ["chest_pain_or_suspected_acute_coronary_syndrome"]


def test_hypertension_pathway_rejects_pii_and_release_gate_blocks_current_pack():
    pathway = build_hypertension_review_pathway(load_hypertension_claim_links())
    validation = validate_hypertension_review_pathway(pathway, {"patient_name": "Jane Doe"})
    gate = evaluate_hypertension_release_gate(
        pathway,
        feature_flags={
            "v7_clinical_release": False,
            "v7_patient_education_export": False,
            "v7_emr_write": False,
            "v7_production_pathway": False,
            "v7_auto_apply_recommendations": False,
        },
        medication_safety_passed=False,
        selected_pack_approved=False,
        dashboard_read_only=True,
        shadow_schema_has_pii=False,
    )

    assert "pii_or_forbidden_input:patient_name" in validation.issues
    assert gate.allowed is False
    assert "selected_pack_not_approved" in gate.blocked_reasons
    assert "medication_safety_required" in gate.blocked_reasons
    assert "clinical_production_release_not_allowed_in_phase_2c" in gate.blocked_reasons
    assert any(reason.startswith("claim_verification_blocks_release:") for reason in gate.blocked_reasons)


def test_hypertension_local_adaptation_preserves_guideline_certainty_and_meaning():
    manifest = json.loads((PACK_ROOT / "10_evidence_manifest.json").read_text(encoding="utf-8"))
    results = assess_hypertension_manifest_local_adaptation(manifest)

    assert len(results) == len(manifest["claims"])
    for result in results:
        assert set(result.domain_assessments) == set(LOCAL_ADAPTATION_DOMAINS)
        assert result.status == "needs_local_review"
        assert result.original_certainty_preserved is True
        assert result.guideline_meaning_preserved is True
