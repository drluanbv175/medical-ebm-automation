"""Readiness gate cho Phase 2D hypertension pack."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping, Sequence

from app.core.feature_flags import merge_feature_flags
from app.core.incident_manager import Incident, IncidentManager, IncidentSeverity
from app.evidence.phase_2d_claim_mapping_validator import validate_claim_to_source_mapping
from app.evidence.phase_2d_review_workflow import validate_shadow_approval_record

RISKY_CLINICAL_FLAGS = {
    "v7_clinical_release",
    "v7_patient_education_export",
    "v7_emr_write",
    "v7_production_pathway",
    "v7_auto_apply_recommendations",
}

REQUIRED_EVIDENCE_DOSSIER_FILES = {
    "00_EVIDENCE_REGISTER.md",
    "01_CLAIM_TO_SOURCE_MATRIX.xlsx",
    "02_SOURCE_IMPORT_LOG.json",
    "03_SOURCE_VERIFICATION_LOG.json",
    "04_CONFLICT_REGISTER.md",
    "05_FRESHNESS_REGISTER.md",
    "06_RETRACTION_CORRECTION_REGISTER.md",
    "07_UNVERIFIED_CLAIMS.md",
    "08_EVIDENCE_REVIEW_SUMMARY.md",
}

STOP_CRITERIA = {
    "pii_detected",
    "critical_red_flag_miss",
    "contraindicated_medication_allowed",
    "citation_mismatch",
    "approval_bypass",
    "feature_flag_bypass",
    "source_retracted_affects_claim",
    "clinical_production_use_detected",
}


@dataclass(frozen=True)
class Phase2DReadinessResult:
    ready: bool
    status: str
    blocked_reasons: List[str] = field(default_factory=list)
    claim_verification_coverage: Mapping[str, int] = field(default_factory=dict)


def evaluate_phase_2d_pack_readiness(
    *,
    dossier_dir: Path,
    claim_mappings: Sequence[Mapping[str, object]],
    approval_record: Mapping[str, object],
    feature_flags: Mapping[str, bool],
    synthetic_vignettes_pass: bool,
    safety_gate_pass: bool,
    red_team_pass: bool,
    dashboard_read_only: bool,
    export_manifest_safe: bool,
    shadow_schema_has_pii: bool,
    incident_protocol_exists: bool,
    rollback_protocol_exists: bool,
) -> Phase2DReadinessResult:
    reasons: List[str] = []
    existing = {path.name for path in dossier_dir.iterdir()} if dossier_dir.exists() else set()
    missing = sorted(REQUIRED_EVIDENCE_DOSSIER_FILES - existing)
    reasons.extend(f"missing_evidence_dossier_file:{name}" for name in missing)

    flags = merge_feature_flags(feature_flags)
    for flag in sorted(RISKY_CLINICAL_FLAGS):
        if flags.get(flag):
            reasons.append(f"risky_flag_must_remain_false:{flag}")

    validation_results = [validate_claim_to_source_mapping(mapping) for mapping in claim_mappings]
    verified = sum(1 for mapping in claim_mappings if mapping.get("verification_status") == "VERIFIED")
    unverified = len(claim_mappings) - verified
    release_ready = sum(1 for result in validation_results if result.release_ready)
    for result in validation_results:
        if not result.release_ready:
            reasons.append(f"claim_not_release_ready:{result.claim_id}")
        reasons.extend(f"claim_mapping_issue:{result.claim_id}:{issue}" for issue in result.issues)

    approval_issues = validate_shadow_approval_record(approval_record)
    reasons.extend(approval_issues)
    if approval_record.get("approval_decision") != "approved_for_shadow_review":
        reasons.append("approval_record_not_approved_for_shadow_review")

    checks = {
        "synthetic_vignettes_pass": synthetic_vignettes_pass,
        "safety_gate_pass": safety_gate_pass,
        "red_team_pass": red_team_pass,
        "dashboard_read_only": dashboard_read_only,
        "export_manifest_safe": export_manifest_safe,
        "incident_protocol_exists": incident_protocol_exists,
        "rollback_protocol_exists": rollback_protocol_exists,
    }
    reasons.extend(f"readiness_check_failed:{name}" for name, value in checks.items() if not value)
    if shadow_schema_has_pii:
        reasons.append("shadow_schema_contains_pii")

    return Phase2DReadinessResult(
        ready=False if reasons else True,
        status="READY_FOR_PHYSICIAN_APPROVED_SHADOW_PILOT" if not reasons else "BLOCKED_REVIEW_ONLY",
        blocked_reasons=sorted(set(reasons)),
        claim_verification_coverage={
            "total_claims": len(claim_mappings),
            "verified_claims": verified,
            "unverified_claims": unverified,
            "release_ready_claims": release_ready,
        },
    )


@dataclass(frozen=True)
class StopPilotAction:
    stopped: bool
    shadow_mode_disabled: bool
    pack_frozen: bool
    audit_log_preserved: bool
    incident: Incident | None
    required_actions: List[str] = field(default_factory=list)


def handle_phase_2d_stop_criteria(
    *,
    run_id: str,
    observed_events: Sequence[str],
    incident_manager: IncidentManager | None = None,
) -> StopPilotAction:
    triggering = sorted(STOP_CRITERIA & set(observed_events))
    if not triggering:
        return StopPilotAction(
            stopped=False,
            shadow_mode_disabled=False,
            pack_frozen=False,
            audit_log_preserved=True,
            incident=None,
        )
    manager = incident_manager or IncidentManager()
    incident = manager.open(
        run_id,
        "Phase 2D shadow pilot stop criteria triggered",
        IncidentSeverity.CRITICAL,
        {"criteria": ",".join(triggering)},
    )
    return StopPilotAction(
        stopped=True,
        shadow_mode_disabled=True,
        pack_frozen=True,
        audit_log_preserved=True,
        incident=incident,
        required_actions=[
            "stop_pilot",
            "create_incident",
            "freeze_relevant_pack_version",
            "disable_shadow_mode",
            "preserve_audit_log",
            "perform_root_cause_analysis",
            "add_regression_test",
        ],
    )
