"""
research_project — Per-project dossier automation (V4.3.3).

Package cung cấp:
  - 13 module tự động hoá hồ sơ đề tài y khoa.
  - 19 artifact template theo loại nghiên cứu.
  - Change control engine với dependency graph.
  - 15 Draft Quality Gates (D-R1..D-R15).
  - Human Review Pack tổng hợp.
  - CLI `researchctl` với 8 subcommand.

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
Mọi output là DRAFT — REQUIRE HUMAN REVIEW.
"""

from .project_config import (
    StudyType, ArtifactID, ArtifactStatus, EvidenceStatus, GateStatus,
    QualityGateResult, ProjectChangeRecord, ProjectArtifact, ProjectConfig,
    REQUIRE_HUMAN_INPUT_MARKER, DISCLAIMER, REPORTING_STANDARD,
    contains_pii, contains_fabrication, contains_external_action,
    contains_real_data, validate_study_type,
)
from .project_artifact_graph import (
    get_downstream, get_direct_downstream, mark_stale, topological_build_order,
)
from .project_registry import (
    ProjectRegistry, ProjectSummary, DuplicateProjectError, UnknownProjectError,
)
from .project_evidence_intake import (
    EvidenceItem, EvidenceIntake, EvidenceIntakeResult, build_evidence_intake,
)
from .project_methodology_planner import plan_methodology, MethodologyPlan
from .project_crf_builder import build_crf_draft, CRFDraft
from .project_sap_builder import build_sap_draft, SAPDraft
from .project_reporting_planner import build_reporting_checklist, ReportingChecklist
from .project_change_control import (
    ChangeControlEngine, ChangeControlResult, ImmutableAuditLog, bump_version,
)
from .project_dossier_builder import ProjectDossierBuilder, DossierBuildResult
from .project_qa_runner import ProjectQARunner, QARunResult, run_project_qa
from .project_review_pack import ReviewPackBuilder, ReviewPackResult, generate_review_pack
from .project_cli import main as researchctl_main

__all__ = [
    # Config / enums
    "StudyType", "ArtifactID", "ArtifactStatus", "EvidenceStatus", "GateStatus",
    "QualityGateResult", "ProjectChangeRecord", "ProjectArtifact", "ProjectConfig",
    "REQUIRE_HUMAN_INPUT_MARKER", "DISCLAIMER", "REPORTING_STANDARD",
    "contains_pii", "contains_fabrication", "contains_external_action",
    "contains_real_data", "validate_study_type",
    # Artifact graph
    "get_downstream", "get_direct_downstream", "mark_stale", "topological_build_order",
    # Registry
    "ProjectRegistry", "ProjectSummary", "DuplicateProjectError", "UnknownProjectError",
    # Evidence
    "EvidenceItem", "EvidenceIntake", "EvidenceIntakeResult", "build_evidence_intake",
    # Methodology
    "plan_methodology", "MethodologyPlan",
    # CRF / SAP / Reporting
    "build_crf_draft", "CRFDraft",
    "build_sap_draft", "SAPDraft",
    "build_reporting_checklist", "ReportingChecklist",
    # Change control
    "ChangeControlEngine", "ChangeControlResult", "ImmutableAuditLog", "bump_version",
    # Dossier
    "ProjectDossierBuilder", "DossierBuildResult",
    # QA
    "ProjectQARunner", "QARunResult", "run_project_qa",
    # Review pack
    "ReviewPackBuilder", "ReviewPackResult", "generate_review_pack",
    # CLI
    "researchctl_main",
]
