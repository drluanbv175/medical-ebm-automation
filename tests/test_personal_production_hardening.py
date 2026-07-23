from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "verify_personal_production_hardening.py"
FIXED_NOW = "2026-07-16T00:00:00+00:00"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_personal_production_hardening", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_personal_production_hardening_covers_all_seven_domains() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)

    assert report["kind"] == "personal_production_hardening_report"
    assert report["overall_status"] == "CONTROLLED_PERSONAL_READY_WITH_HUMAN_GATES"
    assert report["fail_count"] == 0
    assert report["human_gate_count"] >= 6
    assert report["evidence_package_summary"]["status"] == "NOT_PROVIDED"
    assert report["clinical_production_allowed"] is False
    assert report["real_patient_data_allowed"] is False
    assert {row["domain_id"] for row in report["checks"]} == {
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
        "P7",
    }


def test_mode_separation_keeps_dangerous_flags_disabled() -> None:
    mod = _load_module()
    check = mod.check_mode_separation()

    assert check.status == mod.PASS
    assert "dangerous_flags_disabled=true" in check.findings


def _completed_evidence_package(mod):
    package = mod.build_evidence_template(generated_at=FIXED_NOW)
    package["scope"] = "signed-personal-production-hardening-scope-v1"
    for idx, record in enumerate(package["evidence"], 1):
        record["status"] = "CLEARED"
        record["reviewer_reference"] = f"reviewer-ref-{idx:02d}"
        record["reviewed_at"] = "2026-07-15T12:00:00+00:00"
        record["artifact_refs"] = [f"evidence/domain-{record['domain_id'].lower()}-artifact-v1.json"]
        record["controls_verified"] = [f"control-{record['domain_id'].lower()}-verified-v1"]
        record["notes"] = f"review-note-{idx:02d}-no-pii"
    for idx, signoff in enumerate(package["signoffs"], 1):
        signoff["signer_reference"] = f"signer-ref-{idx:02d}"
        signoff["signed_at"] = "2026-07-15T18:00:00+00:00"
        signoff["scope"] = "signed-personal-production-hardening-scope-v1"
        signoff["artifact_refs"] = [f"signoffs/{signoff['role']}-v1.json"]
    package["approval_record"] = {
        "approval_id": "approval-record-2026-07-16-001",
        "status": "approved_for_go_live_review",
        "approver_role": "pi_or_clinic_owner",
        "approver_reference": "pi-or-clinic-approver-ref-001",
        "approved_at": "2026-07-15T20:00:00+00:00",
        "scope": "signed-personal-production-hardening-scope-v1",
        "artifact_refs": ["approval-record/go-live-approval-v1.json"],
    }
    package["go_live_attestation"] = {
        "release_id": "release-2026-07-16-001",
        "change_ticket_reference": "change-ticket-2026-07-16-001",
        "rollback_plan_artifact_ref": "ops/rollback-plan-001.json",
        "post_deployment_checklist_ref": "ops/post-deploy-checklist-001.json",
        "evidence_dossier_sha256": "a" * 64,
        "operator_reference": "operator-ref-001",
        "admin_approver_reference": "admin-approver-ref-001",
    }
    return package


def test_evidence_template_is_complete_but_fail_closed_until_filled() -> None:
    mod = _load_module()
    template = mod.build_evidence_template(generated_at=FIXED_NOW)
    summary = mod.validate_evidence_package(template, generated_at=FIXED_NOW)

    assert template["kind"] == mod.PACKAGE_KIND
    assert len(template["evidence"]) == 7
    assert len(template["signoffs"]) == len(mod.REQUIRED_SIGNOFF_ROLES)
    assert summary.status == "INVALID_OR_INCOMPLETE"
    assert summary.valid is False
    assert any("status_not_cleared" in err for err in summary.errors)
    assert any("signer_reference_invalid" in err for err in summary.errors)
    assert any("approval_record:approver_reference_invalid" in err for err in summary.errors)


def test_completed_evidence_package_is_external_review_ready_not_production_enablement() -> None:
    mod = _load_module()
    package = _completed_evidence_package(mod)
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)
    report = mod.evaluate_all(generated_at=FIXED_NOW, evidence_package=package)

    assert summary.status == "STRUCTURALLY_COMPLETE_EXTERNAL_REVIEW_READY"
    assert summary.valid is True
    assert summary.valid_evidence_records == 7
    assert summary.valid_signoffs == len(mod.REQUIRED_SIGNOFF_ROLES)
    assert summary.valid_approval_record is True
    assert report["evidence_package_summary"]["valid"] is True
    assert report["clinical_production_allowed"] is False
    assert report["real_patient_data_allowed"] is False


def test_evidence_package_rejects_pii_hidden_in_optional_notes() -> None:
    mod = _load_module()
    package = _completed_evidence_package(mod)
    package["evidence"][0]["notes"] = "Internal note accidentally includes phone 0912345678."
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)

    assert summary.status == "INVALID_OR_INCOMPLETE"
    assert summary.valid is False
    assert any("package_text_policy:$.evidence[0].notes:pii_value_phone" in err for err in summary.errors)


def test_evidence_package_rejects_placeholder_and_forbidden_pii_keys_anywhere() -> None:
    mod = _load_module()
    package = _completed_evidence_package(mod)
    package["extra_review"] = {
        "patient_name": "redacted",
        "comment": "TODO fill this later",
    }
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)

    assert summary.status == "INVALID_OR_INCOMPLETE"
    assert any("package_text_policy:$.extra_review.patient_name:forbidden_pii_key" in err for err in summary.errors)
    assert any("package_text_policy:$.extra_review.comment:placeholder_value" in err for err in summary.errors)


def test_evidence_package_redacts_pii_from_error_paths() -> None:
    mod = _load_module()
    package = _completed_evidence_package(mod)
    package["extra_review"] = {"0912345678": "safe opaque note"}
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)
    joined_errors = "\n".join(summary.errors)

    assert summary.status == "INVALID_OR_INCOMPLETE"
    assert "package_text_policy:$.extra_review.<key>:pii_key_phone" in joined_errors
    assert "0912345678" not in joined_errors


def test_evidence_package_rejects_unsafe_artifact_references() -> None:
    mod = _load_module()
    package = _completed_evidence_package(mod)
    package["evidence"][0]["artifact_refs"] = ["../secrets/.env"]
    package["signoffs"][0]["artifact_refs"] = ["https://example.test/signoff.json"]
    package["go_live_attestation"]["rollback_plan_artifact_ref"] = "/tmp/raw/patient-identifiers.csv"
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)

    assert summary.status == "INVALID_OR_INCOMPLETE"
    assert "evidence[P1]:artifact_refs_invalid" in summary.errors
    assert "signoff[security_owner]:artifact_refs_invalid" in summary.errors
    assert "go_live_attestation:rollback_plan_artifact_ref_invalid" in summary.errors


def test_evidence_package_requires_distinct_final_approval_record():
    mod = _load_module()
    package = _completed_evidence_package(mod)
    package["approval_record"]["approver_reference"] = package["signoffs"][0]["signer_reference"]
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)

    assert summary.status == "INVALID_OR_INCOMPLETE"
    assert summary.valid_approval_record is False
    assert any("approval_record:approver_reference_reused_with:" in err for err in summary.errors)
