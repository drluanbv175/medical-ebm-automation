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
    for idx, signoff in enumerate(package["signoffs"], 1):
        signoff["signer_reference"] = f"signer-ref-{idx:02d}"
        signoff["signed_at"] = "2026-07-15T18:00:00+00:00"
        signoff["scope"] = "signed-personal-production-hardening-scope-v1"
        signoff["artifact_refs"] = [f"signoffs/{signoff['role']}-v1.json"]
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


def test_completed_evidence_package_is_external_review_ready_not_production_enablement() -> None:
    mod = _load_module()
    package = _completed_evidence_package(mod)
    summary = mod.validate_evidence_package(package, generated_at=FIXED_NOW)
    report = mod.evaluate_all(generated_at=FIXED_NOW, evidence_package=package)

    assert summary.status == "STRUCTURALLY_COMPLETE_EXTERNAL_REVIEW_READY"
    assert summary.valid is True
    assert summary.valid_evidence_records == 7
    assert summary.valid_signoffs == len(mod.REQUIRED_SIGNOFF_ROLES)
    assert report["evidence_package_summary"]["valid"] is True
    assert report["clinical_production_allowed"] is False
    assert report["real_patient_data_allowed"] is False
