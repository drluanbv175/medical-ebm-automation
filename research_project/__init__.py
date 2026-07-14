"""
research_project — Per-project dossier automation (V4.3.5).

Package cung cấp:
  - 15 module tự động hoá hồ sơ đề tài y khoa (V4.3.5).
  - 19 artifact template theo loại nghiên cứu.
  - Change control engine với dependency graph.
  - 15 Draft Quality Gates (D-R1..D-R15).
  - Human Review Pack tổng hợp.
  - CLI `researchctl` với 16 subcommand.
  - Human Review Operating Model (V4.3.4): 4 roles, 5 decisions, append-only ledger.
  - Evidence Intake & Claim Traceability (V4.3.5): Evidence Source Ledger,
    Claim Traceability Ledger, HUMAN_PROVIDED_ONLY guard, AutoVerificationForbidden.

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
Mọi output là DRAFT — REQUIRE HUMAN REVIEW.
"""

from .project_artifact_graph import (
    get_direct_downstream,
    get_downstream,
    mark_stale,
    topological_build_order,
)
from .project_change_control import (
    ChangeControlEngine,
    ChangeControlResult,
    ImmutableAuditLog,
    bump_version,
)
from .project_claim_traceability import (
    CLAIM_LEDGER_FILENAME,
    ClaimRecord,
    ClaimStatus,
    ClaimTraceabilityLedger,
    ClaimType,
    compute_claim_status,
    get_claim_audit,
    register_claim,
)
from .project_cli import main as researchctl_main
from .project_config import (
    DISCLAIMER,
    EVIDENCE_GATE_STATE_BLOCK,
    EVIDENCE_GATE_STATE_PASS,
    EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT,
    EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW,
    REPORTING_STANDARD,
    REQUIRE_HUMAN_INPUT_MARKER,
    ArtifactID,
    ArtifactStatus,
    EvidenceStatus,
    GateStatus,
    ProjectArtifact,
    ProjectChangeRecord,
    ProjectConfig,
    QualityGateResult,
    StudyType,
    contains_external_action,
    contains_external_action_positive,
    contains_fabrication,
    contains_pii,
    contains_real_data,
    validate_study_type,
)
from .project_crf_builder import CRFDraft, build_crf_draft
from .project_dossier_builder import DossierBuildResult, ProjectDossierBuilder
from .project_evidence_intake import (
    EVIDENCE_SOURCE_LEDGER_FILENAME,
    AutoVerificationForbidden,
    EvidenceIntake,
    EvidenceIntakeResult,
    EvidenceItem,
    EvidenceSource,
    EvidenceSourceLedger,
    ForbiddenRetrievalMode,
    PIIInEvidenceError,
    # V4.3.5
    RetrievalMode,
    VerificationState,
    add_evidence_source,
    build_evidence_intake,
    get_evidence_review_queue,
)
from .project_methodology_planner import MethodologyPlan, plan_methodology
from .project_qa_runner import ProjectQARunner, QARunResult, run_project_qa
from .project_registry import (
    DuplicateProjectError,
    ProjectRegistry,
    ProjectSummary,
    UnknownProjectError,
)
from .project_reporting_planner import ReportingChecklist, build_reporting_checklist
from .project_review_operations import (
    LEDGER_FILENAME,
    REVIEW_ROUTING_MATRIX,
    AutoReviewForbidden,
    ForbiddenReviewMode,
    HumanDecision,
    MissingReviewActorReference,
    PIIInReviewRecord,
    ReviewLedger,
    ReviewMode,
    ReviewRecord,
    ReviewRole,
    RiskLevel,
    UnauthorizedReviewRole,
    build_revision_plan,
    get_review_status,
    list_review_queue,
    make_review_queue_item,
    record_decision,
    required_roles_for_artifact,
)
from .project_review_pack import ReviewPackBuilder, ReviewPackResult, generate_review_pack
from .project_sap_builder import SAPDraft, build_sap_draft

__all__ = [
    # Config / enums
    "StudyType", "ArtifactID", "ArtifactStatus", "EvidenceStatus", "GateStatus",
    "QualityGateResult", "ProjectChangeRecord", "ProjectArtifact", "ProjectConfig",
    "REQUIRE_HUMAN_INPUT_MARKER", "DISCLAIMER", "REPORTING_STANDARD",
    "contains_pii", "contains_fabrication",
    "contains_external_action", "contains_external_action_positive",
    "contains_real_data", "validate_study_type",
    "EVIDENCE_GATE_STATE_PASS", "EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT",
    "EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW", "EVIDENCE_GATE_STATE_BLOCK",
    # Artifact graph
    "get_downstream", "get_direct_downstream", "mark_stale", "topological_build_order",
    # Registry
    "ProjectRegistry", "ProjectSummary", "DuplicateProjectError", "UnknownProjectError",
    # Evidence intake (V4.3.3 legacy)
    "EvidenceItem", "EvidenceIntake", "EvidenceIntakeResult", "build_evidence_intake",
    # Evidence Source Ledger (V4.3.5)
    "RetrievalMode", "VerificationState", "EvidenceSource", "EvidenceSourceLedger",
    "ForbiddenRetrievalMode", "AutoVerificationForbidden", "PIIInEvidenceError",
    "EVIDENCE_SOURCE_LEDGER_FILENAME",
    "add_evidence_source", "get_evidence_review_queue",
    # Claim Traceability (V4.3.5)
    "ClaimType", "ClaimStatus", "ClaimRecord", "ClaimTraceabilityLedger",
    "CLAIM_LEDGER_FILENAME",
    "compute_claim_status", "register_claim", "get_claim_audit",
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
    # Review operations (V4.3.4)
    "ReviewRole", "ReviewMode", "HumanDecision", "RiskLevel",
    "ReviewRecord", "ReviewLedger",
    "AutoReviewForbidden", "ForbiddenReviewMode", "UnauthorizedReviewRole",
    "MissingReviewActorReference", "PIIInReviewRecord",
    "REVIEW_ROUTING_MATRIX", "LEDGER_FILENAME",
    "list_review_queue", "record_decision", "get_review_status", "build_revision_plan",
    "make_review_queue_item", "required_roles_for_artifact",
    # CLI
    "researchctl_main",
]
