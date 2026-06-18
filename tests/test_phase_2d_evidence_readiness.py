import json
from pathlib import Path

import pytest

from app.clinical_content.phase_2c_shadow import Phase2CShadowPilotCase
from app.core.feature_flags import merge_feature_flags
from app.evidence.document_provenance import file_sha256
from app.evidence.manual_source_import import import_official_source
from app.evidence.phase_2d_claim_mapping_validator import validate_claim_to_source_mapping
from app.evidence.phase_2d_pack_readiness import (
    REQUIRED_EVIDENCE_DOSSIER_FILES,
    evaluate_phase_2d_pack_readiness,
    handle_phase_2d_stop_criteria,
)
from app.evidence.phase_2d_review_workflow import (
    Phase2DReviewState,
    evaluate_review_transition,
    validate_shadow_approval_record,
)

PACK_ROOT = Path("knowledge-packs/hypertension_adult_outpatient/2026.1-draft")
DOSSIER_DIR = PACK_ROOT / "evidence_dossier"


def _claim_mappings_from_manifest():
    manifest = json.loads((PACK_ROOT / "10_evidence_manifest.json").read_text(encoding="utf-8"))
    rows = []
    for claim in manifest["claims"]:
        rows.append({
            "claim_id": claim["claim_id"],
            "claim_text_draft": claim["recommendation_text_draft"],
            "population": claim["population"],
            "clinical_question": claim["clinical_question"],
            "source_id": claim["evidence_id"],
            "source_type": claim["source_type"],
            "organization": claim["organization"],
            "title": f"{claim['organization']} source page",
            "version": claim["publication_or_version_date"],
            "publication_date": claim["publication_or_version_date"],
            "pmid": "",
            "doi": "",
            "source_url": claim["source_url"],
            "claim_location": claim["claim_location"],
            "certainty_original": claim["certainty_original"],
            "verification_status": claim["verification_status"],
            "verification_method": "",
            "verified_by": "",
            "verified_at": "",
            "freshness_status": claim["freshness_status"],
            "retraction_status": "unknown_or_unchecked",
            "approval_status": claim["approval_status"],
            "notes": "review-only",
        })
    return rows


def test_phase_2d_evidence_dossier_files_exist_and_current_pack_is_not_ready():
    present = {path.name for path in DOSSIER_DIR.iterdir()}
    approval = json.loads((PACK_ROOT / "13_approval_record.json").read_text(encoding="utf-8"))
    result = evaluate_phase_2d_pack_readiness(
        dossier_dir=DOSSIER_DIR,
        claim_mappings=_claim_mappings_from_manifest(),
        approval_record=approval,
        feature_flags=merge_feature_flags(),
        synthetic_vignettes_pass=True,
        safety_gate_pass=True,
        red_team_pass=True,
        dashboard_read_only=True,
        export_manifest_safe=True,
        shadow_schema_has_pii=False,
        incident_protocol_exists=True,
        rollback_protocol_exists=True,
    )

    assert REQUIRED_EVIDENCE_DOSSIER_FILES <= present
    assert result.ready is False
    assert result.status == "BLOCKED_REVIEW_ONLY"
    assert result.claim_verification_coverage["verified_claims"] == 0
    assert result.claim_verification_coverage["unverified_claims"] == 3
    assert "approval_record_not_approved_for_shadow_review" in result.blocked_reasons
    assert any(reason.startswith("claim_not_release_ready:") for reason in result.blocked_reasons)


def test_phase_2d_manual_source_import_blocks_missing_hash_and_allows_complete_html_snapshot(tmp_path):
    source = tmp_path / "official.html"
    source.write_text("<html><h1>Official guideline</h1></html>", encoding="utf-8")

    blocked = import_official_source({
        "source_file": str(source),
        "source_origin_url": "https://example.org/guideline",
        "organization": "Example Organization",
        "source_type": "guideline",
        "title": "Official guideline",
        "version": "2026",
        "publication_date": "2026-01-01",
        "imported_by": "reviewer_non_pii",
        "import_date": "2026-06-18",
        "page_count_or_html_snapshot": "section:h1",
        "copyright_or_access_note": "public page",
        "section_heading": "Official guideline",
    })
    assert blocked.imported is False
    assert "sha256_required" in blocked.issues

    imported = import_official_source({
        "source_file": str(source),
        "source_origin_url": "https://example.org/guideline",
        "organization": "Example Organization",
        "source_type": "guideline",
        "title": "Official guideline",
        "version": "2026",
        "publication_date": "2026-01-01",
        "imported_by": "reviewer_non_pii",
        "import_date": "2026-06-18",
        "sha256": file_sha256(source),
        "page_count_or_html_snapshot": "section:h1",
        "copyright_or_access_note": "public page",
        "section_heading": "Official guideline",
    })
    assert imported.imported is True
    assert imported.status == "SOURCE_IMPORTED"


def test_phase_2d_pdf_source_without_page_mapping_cannot_verify_claim():
    mapping = {
        "claim_id": "claim_pdf",
        "claim_text_draft": "Draft claim",
        "population": "Adults",
        "clinical_question": "Question",
        "source_id": "source_pdf",
        "source_type": "pdf",
        "organization": "Org",
        "title": "PDF",
        "version": "2026",
        "publication_date": "2026-01-01",
        "pmid": "",
        "doi": "",
        "source_url": "https://example.org/source.pdf",
        "claim_location": "section 1",
        "certainty_original": "not_regraded",
        "verification_status": "VERIFIED",
        "verification_method": "manual_page_check",
        "verified_by": "reviewer_non_pii",
        "verified_at": "2026-06-18",
        "freshness_status": "current",
        "retraction_status": "not_retracted",
        "approval_status": "approved",
        "notes": "",
    }
    result = validate_claim_to_source_mapping(mapping)

    assert result.can_be_verified is False
    assert result.release_ready is False
    assert "pdf_claim_page_mapping_required" in result.issues


def test_phase_2d_review_workflow_blocks_shortcuts_and_requires_reviewer_validation():
    shortcut = evaluate_review_transition(
        Phase2DReviewState.DRAFT,
        Phase2DReviewState.APPROVED_FOR_SHADOW_REVIEW,
    )
    source_verified = evaluate_review_transition(
        Phase2DReviewState.SOURCE_IMPORTED,
        Phase2DReviewState.SOURCE_VERIFIED,
        reviewer_validated=False,
    )

    assert shortcut.allowed is False
    assert "transition_not_allowed:DRAFT->APPROVED_FOR_SHADOW_REVIEW" in shortcut.issues
    assert source_verified.allowed is False
    assert "reviewer_validation_required_for_source_verified" in source_verified.issues


def test_phase_2d_approval_record_auto_generated_is_blocked():
    issues = validate_shadow_approval_record({
        "approver_name_or_non_pii_id": "reviewer_1",
        "approver_role": "physician",
        "approval_scope": "shadow review",
        "pack_version": "2026.1-draft",
        "approval_date": "2026-06-18",
        "approval_decision": "approved_for_shadow_review",
        "conditions_or_limitations": "review-only",
        "signature_or_external_reference": "external-ref-1",
        "generated_by_system": True,
        "clinical_release": False,
    })

    assert "approval_record_must_not_be_auto_generated" in issues


def test_phase_2d_shadow_case_form_blocks_pii_like_text():
    case = Phase2CShadowPilotCase(
        shadow_pilot_case_id="shadow2d_pii",
        pathway_id="hypertension_adult_outpatient_review_only",
        pathway_version="2026.1-draft",
        environment="shadow",
        clinical_domain="hypertension_adult_outpatient",
        question_type="review",
        data_completeness="minimal",
        red_flag_screen={},
        comorbidity_flags={},
        medication_context={"note": "phone 0912345678"},
        evidence_snapshot_id="evsnap_2d",
    )
    with pytest.raises(ValueError):
        case.validate()


def test_phase_2d_stop_criteria_creates_incident_and_disables_shadow_mode():
    action = handle_phase_2d_stop_criteria(
        run_id="run_stop_001",
        observed_events=["critical_red_flag_miss", "citation_mismatch"],
    )

    assert action.stopped is True
    assert action.shadow_mode_disabled is True
    assert action.pack_frozen is True
    assert action.incident is not None
    assert "disable_shadow_mode" in action.required_actions


def test_phase_2d_feature_flags_and_export_manifest_remain_review_only():
    flags = merge_feature_flags()
    manifest = json.loads(Path("exports/chatgpt_project/v7_manifest.json").read_text(encoding="utf-8"))

    assert flags["v7_clinical_release"] is False
    assert flags["v7_patient_education_export"] is False
    assert flags["v7_emr_write"] is False
    assert flags["v7_production_pathway"] is False
    assert flags["v7_auto_apply_recommendations"] is False
    assert manifest["environment"] == "review"
    assert manifest["safe_to_upload"] is True
    assert manifest["contains_pii"] is False
