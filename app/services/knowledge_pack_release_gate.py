"""Release readiness gate for clinical knowledge packs.

Schema validity means a pack is readable. Release readiness is stricter: it
requires explicit approval, traceable evidence, and disabled patient/EMR write
surfaces unless a future review intentionally enables them.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

from app.services.knowledge_pack_schema import load_yaml_mapping, validate_pack_version

REQUIRED_APPROVAL_FILE = "13_approval_record.json"
REQUIRED_EVIDENCE_MANIFEST = "10_evidence_manifest.json"


@dataclass(frozen=True)
class KnowledgePackReleaseIssue:
    file: str
    message: str
    severity: str = "blocker"


@dataclass(frozen=True)
class KnowledgePackReleaseReadiness:
    pack_id: str
    version_dir: str
    schema_ok: bool
    review_ready: bool
    clinical_release_ready: bool
    patient_facing_ready: bool
    approval_record_present: bool
    evidence_manifest_present: bool
    issues: List[KnowledgePackReleaseIssue] = field(default_factory=list)

    @property
    def blockers(self) -> List[KnowledgePackReleaseIssue]:
        return [issue for issue in self.issues if issue.severity == "blocker"]


def assess_pack_release_readiness(pack_dir: Path, version_dir: str = "2026.1-draft") -> KnowledgePackReleaseReadiness:
    """Assess whether a pack may move beyond draft/review-only use."""
    schema_result = validate_pack_version(pack_dir, version_dir)
    version_path = pack_dir / version_dir
    scope = load_yaml_mapping(version_path / "01_scope.yaml")
    approval_record = _load_json_mapping(version_path / REQUIRED_APPROVAL_FILE)
    evidence_manifest = _load_json_mapping(version_path / REQUIRED_EVIDENCE_MANIFEST)

    issues: List[KnowledgePackReleaseIssue] = [
        KnowledgePackReleaseIssue(issue.file, f"schema:{issue.message}")
        for issue in schema_result.errors
    ]

    issues.extend(_scope_release_issues(scope))
    issues.extend(_approval_issues(approval_record))
    issues.extend(_evidence_manifest_issues(evidence_manifest))

    review_ready = schema_result.ok and _draft_safety_flags_are_closed(scope)
    clinical_release_ready = schema_result.ok and not issues and _clinical_release_flags_are_open(
        scope,
        approval_record,
        evidence_manifest,
    )
    patient_facing_ready = clinical_release_ready and bool(scope.get("patient_facing_output_allowed"))

    return KnowledgePackReleaseReadiness(
        pack_id=pack_dir.name,
        version_dir=version_dir,
        schema_ok=schema_result.ok,
        review_ready=review_ready,
        clinical_release_ready=clinical_release_ready,
        patient_facing_ready=patient_facing_ready,
        approval_record_present=bool(approval_record),
        evidence_manifest_present=bool(evidence_manifest),
        issues=issues,
    )


def assess_all_pack_release_readiness(
    packs_dir: Path,
    version_dir: str = "2026.1-draft",
) -> List[KnowledgePackReleaseReadiness]:
    """Assess every pack directory in stable order."""
    if not packs_dir.exists():
        return []
    return [
        assess_pack_release_readiness(pack_dir, version_dir)
        for pack_dir in sorted(path for path in packs_dir.iterdir() if path.is_dir())
    ]


def summarize_release_readiness(results: List[KnowledgePackReleaseReadiness]) -> Dict[str, int]:
    """Return counts for dashboards and CI summaries."""
    return {
        "total": len(results),
        "schema_ok": sum(1 for result in results if result.schema_ok),
        "review_ready": sum(1 for result in results if result.review_ready),
        "clinical_release_ready": sum(1 for result in results if result.clinical_release_ready),
        "patient_facing_ready": sum(1 for result in results if result.patient_facing_ready),
        "blocked": sum(1 for result in results if not result.clinical_release_ready),
    }


def _scope_release_issues(scope: Mapping[str, Any]) -> List[KnowledgePackReleaseIssue]:
    issues: List[KnowledgePackReleaseIssue] = []
    if not scope:
        return [KnowledgePackReleaseIssue("01_scope.yaml", "missing_or_invalid_scope")]
    if scope.get("status") == "draft_review_only":
        issues.append(KnowledgePackReleaseIssue("01_scope.yaml", "status_is_draft_review_only"))
    if not bool(scope.get("clinical_release_allowed")):
        issues.append(KnowledgePackReleaseIssue("01_scope.yaml", "clinical_release_allowed_false"))
    if bool(scope.get("emr_write_allowed")):
        issues.append(KnowledgePackReleaseIssue("01_scope.yaml", "emr_write_must_remain_disabled"))
    if bool(scope.get("prescription_generation_allowed")):
        issues.append(KnowledgePackReleaseIssue("01_scope.yaml", "prescription_generation_must_remain_disabled"))
    if not _non_empty_text(scope.get("disclaimer")):
        issues.append(KnowledgePackReleaseIssue("01_scope.yaml", "disclaimer_missing"))
    return issues


def _approval_issues(approval_record: Mapping[str, Any]) -> List[KnowledgePackReleaseIssue]:
    if not approval_record:
        return [KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "missing_approval_record")]
    issues: List[KnowledgePackReleaseIssue] = []
    if approval_record.get("status") != "approved":
        issues.append(KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "approval_status_not_approved"))
    if not bool(approval_record.get("clinical_release_allowed")):
        issues.append(KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "approval_clinical_release_false"))
    if bool(approval_record.get("pii_present")):
        issues.append(KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "approval_record_pii_present"))
    if not _non_empty_text(approval_record.get("reviewer_role_required")):
        issues.append(KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "reviewer_role_required_missing"))
    if not _non_empty_text(approval_record.get("created_at")):
        issues.append(KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "created_at_missing"))
    if not _non_empty_text(approval_record.get("next_review_due")):
        issues.append(KnowledgePackReleaseIssue(REQUIRED_APPROVAL_FILE, "next_review_due_missing"))
    return issues


def _evidence_manifest_issues(evidence_manifest: Mapping[str, Any]) -> List[KnowledgePackReleaseIssue]:
    if not evidence_manifest:
        return [KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, "missing_evidence_manifest")]
    issues: List[KnowledgePackReleaseIssue] = []
    claims = evidence_manifest.get("claims")
    if not isinstance(claims, list) or not claims:
        return [KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, "claims_missing")]
    if not bool(evidence_manifest.get("release_allowed")):
        issues.append(KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, "manifest_release_allowed_false"))
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            issues.append(KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, f"claims[{index}].invalid"))
            continue
        source_url = _non_empty_text(claim.get("source_url"))
        pmid_or_doi = _non_empty_text(claim.get("pmid_or_doi_if_available"))
        if not source_url and not pmid_or_doi:
            issues.append(KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, f"claims[{index}].missing_source"))
        if claim.get("verification_status") != "VERIFIED":
            issues.append(KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, f"claims[{index}].not_verified"))
        if claim.get("approval_status") != "approved":
            issues.append(KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, f"claims[{index}].not_approved"))
        if claim.get("release") != "allowed":
            issues.append(KnowledgePackReleaseIssue(REQUIRED_EVIDENCE_MANIFEST, f"claims[{index}].release_not_allowed"))
    return issues


def _clinical_release_flags_are_open(
    scope: Mapping[str, Any],
    approval_record: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
) -> bool:
    return (
        bool(scope.get("clinical_release_allowed"))
        and bool(approval_record.get("clinical_release_allowed"))
        and bool(evidence_manifest.get("release_allowed"))
    )


def _draft_safety_flags_are_closed(scope: Mapping[str, Any]) -> bool:
    return (
        bool(scope)
        and not bool(scope.get("clinical_release_allowed"))
        and not bool(scope.get("patient_facing_output_allowed"))
        and not bool(scope.get("emr_write_allowed"))
        and not bool(scope.get("prescription_generation_allowed"))
    )


def _load_json_mapping(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

