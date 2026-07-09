"""
research_workflow — 9 work package (WP-01..WP-09) map vào 48 agent hiện có,
chạy QUA control-plane: Registry → ControlledOrchestrator → DispatchGuard →
PolicyGateEngine → WorkflowStateMachine → ApprovalLedger → AuditLogger →
MockAgentRuntime. KHÔNG tạo agent mới. KHÔNG API/network/PII/dữ liệu thật.

V4.3.1 — NGỮ NGHĨA ĐÚNG: tạo DRAFT (mức A) KHÔNG cần G2/G4/G9. Draft-mode registry
gắn lead agent với policy_dependencies=["PII_EGRESS"] (không cổng thật) → KHÔNG cần
approval nào. G2/G4/G9 chỉ là điều kiện-trước cho THỰC THI THẬT / RELEASE — luôn
BLOCK trong V4.3.1 (xem governance.py). Synthetic approval (seed_synthetic_ledger)
CHỈ để test plumbing orchestrator, KHÔNG dùng trong luồng draft và KHÔNG phải người.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional

from runtime.agent_registry import AgentRegistry, AgentRegistryEntry, RegistryMode, from_entries_for_testing
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.controlled_orchestrator import ControlledOrchestrator, OrchestratorResult
from runtime.mock_agent_runtime import MockAgentRuntime
from runtime.schemas import (
    ApprovalDecisionEnum,
    FixtureOutput,
    FixtureScenarioEnum,
    PolicyDecisionEnum,
    WorkflowStateEnum,
)
from runtime.workflow_context import WorkflowContext
from runtime.workflow_state_machine import WorkflowStateMachine

from .artifact_registry import ArtifactRegistry, ResearchArtifact
from .capability_profile import detect_external_action
from .governance import DraftStateMachine, DraftWorkflowState
from .project_schema import (
    ComponentStatus,
    ResearchProject,
    ResearchWorkflowState,
    ReviewStatus,
)
from .research_preflight import ResearchPreflightReport, evaluate_research_preflight
from .research_quality_checks import (
    ResearchGateDecision,
    safety_gates_on_output,
    worst_decision,
)
from .study_type_router import get_template

# Nhãn synthetic approval — KHÔNG phải người thật (chỉ test plumbing).
SYNTHETIC_REVIEWER_ROLE = "SYNTHETIC_TECHNICAL_FIXTURE"
SYNTHETIC_REVIEWER_REF = "MRAQ_HARNESS_NOT_A_PERSON"
SYNTHETIC_SCOPE = "SYNTHETIC gate fixture — plumbing test only, NOT a human approval"

# Draft-mode: lead agent chỉ phụ thuộc PII_EGRESS (KHÔNG G2/G4/G9/GATE_B).
_DRAFT_POLICY_DEPS = ["PII_EGRESS"]


# ── Work packages ──────────────────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class WorkPackage:
    wp_id: str
    name: str
    lead_agent: str                 # PHẢI thuộc 48 agent registry
    supporting_agents: tuple
    artifact_type: str
    fixture_id: str
    research_state: ResearchWorkflowState


WORK_PACKAGES: List[WorkPackage] = [
    WorkPackage("WP-01", "Research Intake", "cau-hoi-nghien-cuu",
                ("khoang-trong-nghien-cuu", "thu-thu-tai-lieu", "pico-lam-sang"),
                "RESEARCH_BRIEF_DRAFT", "RWP-01", DraftWorkflowState.INTAKE),
    WorkPackage("WP-02", "Protocol Builder", "thiet-ke-nghien-cuu",
                ("bien-so-nghien-cuu", "dao-duc-dang-ky", "ke-hoach-trien-khai"),
                "PROTOCOL_DRAFT", "RWP-02", DraftWorkflowState.PROTOCOL_DRAFT),
    WorkPackage("WP-03", "Evidence Plan", "tong-quan-y-van",
                ("thu-thu-tai-lieu", "kiem-chung-trich-dan", "trich-xuat-y-van"),
                "EVIDENCE_PLAN_DRAFT", "RWP-03", DraftWorkflowState.EVIDENCE_PLAN_DRAFT),
    WorkPackage("WP-04", "Methodology & Sample Size", "co-mau-nghien-cuu",
                ("thiet-ke-nghien-cuu", "bien-so-nghien-cuu"),
                "METHODS_SAMPLE_SIZE_DRAFT", "RWP-04", DraftWorkflowState.METHODS_DRAFT),
    WorkPackage("WP-05", "CRF & Data Dictionary", "bien-so-nghien-cuu",
                ("quan-ly-du-lieu", "cong-cu-do-luong"),
                "CRF_DRAFT", "RWP-05", DraftWorkflowState.CRF_DRAFT),
    WorkPackage("WP-06", "Statistical Analysis Plan", "thiet-ke-nghien-cuu",
                ("phan-tich-thong-ke",),
                "SAP_DRAFT", "RWP-06", DraftWorkflowState.SAP_DRAFT),
    WorkPackage("WP-07", "Synthetic Analysis Simulation", "phan-tich-thong-ke",
                ("dien-giai-ket-qua",),
                "SYNTHETIC_ANALYSIS_READINESS_DRAFT", "RWP-07", DraftWorkflowState.SYNTHETIC_ANALYSIS_READY),
    WorkPackage("WP-08", "Reporting & Publication Readiness", "viet-ban-thao",
                ("hieu-dinh-song-ngu", "kiem-chung-trich-dan", "nop-bai-phan-hoi", "binh-duyet"),
                "MANUSCRIPT_OUTLINE_DRAFT", "RWP-08", DraftWorkflowState.MANUSCRIPT_DRAFT),
    WorkPackage("WP-09", "Governance & QA", "so-cai-ghi-nho",
                ("an-toan-nghien-cuu", "tham-dinh-dau-ra", "quan-ly-du-lieu"),
                "GOVERNANCE_PACK_DRAFT", "RWP-09", DraftWorkflowState.GOVERNANCE_DRAFT),
]

WP_BY_ID: Dict[str, WorkPackage] = {wp.wp_id: wp for wp in WORK_PACKAGES}


# ── Research fixture catalog (synthetic outputs, KHÔNG dữ liệu thật) ───────────

def _clean(fixture_id: str, agent_id: str, output: dict) -> FixtureOutput:
    return FixtureOutput(
        fixture_id=fixture_id, fixture_version="RS-1.0",
        scenario=FixtureScenarioEnum.VALID_RESPONSE,
        input={"agent_id": agent_id},
        simulated_output={**output, "draft_only": True, "human_review_required": True},
        expected_policy_decision=PolicyDecisionEnum.PASS,
        expected_state_transition=None,
        expected_audit_event={"policy_decision": "PASS", "pii_verdict": "CLEAN"},
    )


RESEARCH_FIXTURE_CATALOG: Dict[str, FixtureOutput] = {
    "RWP-01": _clean("RWP-01", "cau-hoi-nghien-cuu",
                     {"research_brief": "PICO synthetic", "finer_ok": True, "source_pmid": "PMID:0000001"}),
    "RWP-02": _clean("RWP-02", "thiet-ke-nghien-cuu",
                     {"protocol": "design+ethics synthetic", "design": "see_project", "source_pmid": "PMID:0000002"}),
    "RWP-03": _clean("RWP-03", "tong-quan-y-van",
                     {"evidence_plan": "search strategy synthetic", "source_pmid": "PMID:0000003"}),
    "RWP-04": _clean("RWP-04", "co-mau-nghien-cuu",
                     {"methods": "sampling synthetic", "source_pmid": "PMID:0000004"}),
    "RWP-05": _clean("RWP-05", "bien-so-nghien-cuu",
                     {"crf": "variables synthetic", "source_pmid": "PMID:0000005"}),
    "RWP-06": _clean("RWP-06", "thiet-ke-nghien-cuu",
                     {"sap": "analysis plan synthetic", "source_pmid": "PMID:0000006"}),
    "RWP-07": _clean("RWP-07", "phan-tich-thong-ke",
                     {"analysis_readiness": "table/figure shells synthetic", "source_pmid": "PMID:0000007"}),
    "RWP-08": _clean("RWP-08", "viet-ban-thao",
                     {"manuscript_outline": "IMRAD synthetic", "source_pmid": "PMID:0000008"}),
    "RWP-09": _clean("RWP-09", "so-cai-ghi-nho",
                     {"governance_pack": "ethics+decision log synthetic", "source_pmid": "PMID:0000009"}),
    # Adversarial fixtures (kích hoạt gate) — vẫn synthetic, KHÔNG dữ liệu thật.
    "RWP-FAB": FixtureOutput(
        fixture_id="RWP-FAB", fixture_version="RS-1.0", scenario=FixtureScenarioEnum.FABRICATED_DATA,
        input={"agent_id": "phan-tich-thong-ke"},
        simulated_output={"p_value": 0.01, "note": "FABRICATED_DATA_MARKER", "source_pmid": None},
        expected_policy_decision=PolicyDecisionEnum.BLOCK, expected_state_transition=None,
        expected_audit_event={"policy_decision": "BLOCK"}),
    "RWP-CIT": FixtureOutput(
        fixture_id="RWP-CIT", fixture_version="RS-1.0", scenario=FixtureScenarioEnum.FABRICATED_CITATION,
        input={"agent_id": "kiem-chung-trich-dan"},
        simulated_output={"ref": "FABRICATED_CITATION_MARKER", "doi_verified": False},
        expected_policy_decision=PolicyDecisionEnum.REVIEW_REQUIRED, expected_state_transition=None,
        expected_audit_event={"policy_decision": "REVIEW_REQUIRED"}),
    "RWP-PII": FixtureOutput(
        fixture_id="RWP-PII", fixture_version="RS-1.0", scenario=FixtureScenarioEnum.PII_LEAK,
        input={"agent_id": "quan-ly-du-lieu"},
        simulated_output={"leak": "PATIENT_ID: BN001 cccd 012345678901"},
        expected_policy_decision=PolicyDecisionEnum.PII_BLOCKED, expected_state_transition=None,
        expected_audit_event={"policy_decision": "PII_BLOCKED", "pii_verdict": "BLOCKED"}),
    "RWP-REAL": _clean("RWP-REAL", "quan-ly-du-lieu",
                       {"note": "REAL_PATIENT_DATA pulled from EHOSPITAL_CONNECT"}),
    "RWP-RETRACT": _clean("RWP-RETRACT", "tong-quan-y-van",
                          {"evidence_plan": "includes RETRACTION_MARKER source"}),
}


# ── Builders ────────────────────────────────────────────────────────────────────

def build_research_runtime() -> MockAgentRuntime:
    return MockAgentRuntime(fixture_catalog=RESEARCH_FIXTURE_CATALOG)


def build_research_registry() -> AgentRegistry:
    """Registry FULL_SCOPE_A thật → artifact mang agent_source_hash thật."""
    return AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)


def build_draft_mode_registry() -> AgentRegistry:
    """
    V4.3.1: Registry DRAFT-MODE. Giữ NGUYÊN hash thật của lead agent (từ FULL_SCOPE_A)
    nhưng đặt policy_dependencies=["PII_EGRESS"] — KHÔNG G2/G4/G9/GATE_B. Vì vậy tạo
    DRAFT KHÔNG cần bất kỳ approval cổng nào (đúng ngữ nghĩa: draft ≠ thực thi thật).
    """
    full = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
    lead_agents = {wp.lead_agent for wp in WORK_PACKAGES}
    entries = []
    for aid in sorted(lead_agents):
        src = full.get(aid)
        entries.append(AgentRegistryEntry(
            agent_id=aid,
            agent_path=f".claude/agents/{aid}.md",
            agent_source_hash=src.agent_source_hash,   # hash THẬT giữ nguyên
            policy_dependencies=list(_DRAFT_POLICY_DEPS),
            allowed_runtime="MOCK_ONLY",
            source_file_exists=True,
            hash_verified=True,
        ))
    return from_entries_for_testing(entries)


def seed_synthetic_ledger() -> ApprovalLedger:
    """[PLUMBING-ONLY] Ledger với approval SYNTHETIC có marker CẤU TRÚC
    (is_synthetic=True). KHÔNG dùng trong luồng draft (draft không cần cổng);
    CHỈ để test plumbing orchestrator. KHÔNG phải phê duyệt người — phân biệt
    được cả free-text lẫn structural flag (ledger.synthetic_approvals())."""
    ledger = ApprovalLedger()
    for gate in ("G2", "G4", "G9", "GATE_A", "GATE_B"):
        rec = ApprovalLedger.make_synthetic_approval(
            gate_id=gate, scope=SYNTHETIC_SCOPE,
            evidence_content=f"SYNTHETIC-EVIDENCE-{gate}",
            reviewer_role=SYNTHETIC_REVIEWER_ROLE, reviewer_ref=SYNTHETIC_REVIEWER_REF,
            decision=ApprovalDecisionEnum.APPROVED,
            artifact_creator_agent="research-studio-synthetic-fixture",
            reviewer_agent="technical-harness-reviewer",
        )
        ledger.add_approval(rec, created_by_agent=False)
    return ledger


# ── WP run result ───────────────────────────────────────────────────────────────

@dataclasses.dataclass
class WPRunResult:
    wp_id: str
    project_id: str
    orchestrator_result: OrchestratorResult
    gate_results: list
    decision: ResearchGateDecision
    artifact: Optional[ResearchArtifact]
    reason_code: Optional[str] = None


def run_work_package(
    project: ResearchProject,
    wp: WorkPackage,
    registry: AgentRegistry,
    ledger: ApprovalLedger,
    runtime: MockAgentRuntime,
    audit_logger: AuditLogger,
    artifacts: ArtifactRegistry,
    fixture_override: Optional[str] = None,
) -> WPRunResult:
    """Chạy MỘT work package qua control-plane; tạo artifact DRAFT nếu PASS."""
    state_machine = WorkflowStateMachine(workflow_id=project.project_id)
    orch = ControlledOrchestrator(
        registry=registry, ledger=ledger, mock_runtime=runtime,
        state_machine=state_machine, audit_logger=audit_logger,
    )
    ctx = WorkflowContext.create(
        workflow_id=project.project_id,
        agent_id=wp.lead_agent,
        fixture_id=fixture_override or wp.fixture_id,
        state_before=WorkflowStateEnum.DRAFT.value,
    )
    result = orch.run(ctx)

    # Control-plane chặn (registry/hash/gate/dispatch) → không artifact.
    if result.blocked:
        return WPRunResult(wp.wp_id, project.project_id, result, [],
                           ResearchGateDecision.BLOCK, None, result.reason_code)
    # Policy của dispatch không PASS → không artifact.
    if result.policy_decision != PolicyDecisionEnum.PASS:
        return WPRunResult(wp.wp_id, project.project_id, result, [],
                           ResearchGateDecision.BLOCK, None,
                           f"POLICY:{result.policy_decision.value}")

    # Capability boundary: chặn mọi ý đồ hành động ngoài/real-data trong output.
    output = result.fixture_result.simulated_output
    ext_found, ext_reason = detect_external_action(output)
    if ext_found:
        return WPRunResult(wp.wp_id, project.project_id, result, [],
                           ResearchGateDecision.BLOCK, None,
                           f"CAPABILITY_BLOCKED:{ext_reason}")

    # Research safety gates trên output synthetic.
    gates = safety_gates_on_output(output)
    decision = worst_decision(gates)
    if decision == ResearchGateDecision.BLOCK:
        return WPRunResult(wp.wp_id, project.project_id, result, gates,
                           ResearchGateDecision.BLOCK, None,
                           next((g.reason_code for g in gates
                                 if g.decision == ResearchGateDecision.BLOCK), "GATE_BLOCK"))

    # Tạo artifact DRAFT (truy nguyên đầy đủ; mức A — KHÔNG approval cổng nào).
    artifact = ResearchArtifact(
        artifact_id=f"{project.project_id}:{wp.artifact_type}",
        project_id=project.project_id,
        artifact_type=wp.artifact_type,
        artifact_version="0.1-draft",
        source_agent_id=wp.lead_agent,
        source_agent_hash=ctx.agent_source_hash,            # từ registry hash-verify
        workflow_run_id=ctx.run_id,
        evidence_reference=(result.audit_event.run_id if result.audit_event else "NO_AUDIT"),
        review_status=ReviewStatus.PENDING_HUMAN_REVIEW,
        draft_only=True, human_review_required=True,
        content_summary=f"{wp.name} (synthetic, DRAFT_CREATION) — decision={decision.value}",
        governance_level="DRAFT_CREATION",
        gate_approvals_synthetic=False,   # mức A KHÔNG dùng approval cổng nào
    )
    artifacts.register(artifact)  # fail-closed nếu thiếu hash

    if wp.wp_id == "WP-08":
        template = get_template(project.study_type)
        reporting_artifact = ResearchArtifact(
            artifact_id=f"{project.project_id}:REPORTING_CHECKLIST_DRAFT",
            project_id=project.project_id,
            artifact_type="REPORTING_CHECKLIST_DRAFT",
            artifact_version="0.1-draft",
            source_agent_id=wp.lead_agent,
            source_agent_hash=ctx.agent_source_hash,
            workflow_run_id=ctx.run_id,
            evidence_reference=(result.audit_event.run_id if result.audit_event else "NO_AUDIT"),
            review_status=ReviewStatus.PENDING_HUMAN_REVIEW,
            draft_only=True,
            human_review_required=True,
            content_summary=(
                f"{template.reporting_checklist} reporting checklist shell "
                f"for {project.study_type.value} (synthetic, DRAFT_CREATION)"
            ),
            governance_level="DRAFT_CREATION",
            gate_approvals_synthetic=False,
        )
        artifacts.register(reporting_artifact)

    return WPRunResult(wp.wp_id, project.project_id, result, gates, decision, artifact)


# ── Run cả project ────────────────────────────────────────────────────────────

_STATUS_FIELD_BY_WP = {
    "WP-03": "evidence_status", "WP-04": "methodology_status",
    "WP-05": "data_plan_status", "WP-06": "sap_status",
    "WP-08": "manuscript_status", "WP-09": "governance_status",
}


@dataclasses.dataclass
class ProjectRunResult:
    project_id: str
    wp_results: List[WPRunResult]
    final_state: ResearchWorkflowState
    artifacts: List[ResearchArtifact]
    blocked: bool
    block_reason: Optional[str] = None
    preflight_report: Optional[ResearchPreflightReport] = None


def run_project(
    project: ResearchProject,
    wp_ids: Optional[List[str]] = None,
    registry: Optional[AgentRegistry] = None,
    artifacts: Optional[ArtifactRegistry] = None,
) -> ProjectRunResult:
    """Chạy chuỗi WP DRAFT cho project; advance state qua DraftStateMachine (tuyến
    tính, chặn state thật/release); trả traceability.

    V4.3.1: registry DRAFT-MODE (chỉ PII_EGRESS) + ledger RỖNG → tạo draft KHÔNG cần
    G2/G4/G9. Không seed synthetic approval trong luồng draft.
    """
    registry = registry or build_draft_mode_registry()
    full_registry = build_research_registry()
    preflight = evaluate_research_preflight(
        project,
        full_registry=full_registry,
        draft_registry=registry,
    )
    if preflight.decision == ResearchGateDecision.BLOCK:
        project.workflow_state = DraftWorkflowState.BLOCKED
        return ProjectRunResult(
            project_id=project.project_id,
            wp_results=[],
            final_state=DraftWorkflowState.BLOCKED,
            artifacts=[],
            blocked=True,
            block_reason="PREFLIGHT_BLOCK:" + ",".join(preflight.reason_codes),
            preflight_report=preflight,
        )

    ledger = ApprovalLedger()                       # RỖNG — draft không cần cổng
    runtime = build_research_runtime()
    audit_logger = AuditLogger(run_id=f"AUDIT-{project.project_id}")
    artifacts = artifacts if artifacts is not None else ArtifactRegistry()
    sm = DraftStateMachine(initial=DraftWorkflowState.INTAKE)

    wps = [WP_BY_ID[w] for w in (wp_ids or [wp.wp_id for wp in WORK_PACKAGES])]
    results: List[WPRunResult] = []
    for wp in wps:
        r = run_work_package(project, wp, registry, ledger, runtime, audit_logger, artifacts)
        results.append(r)
        if r.decision == ResearchGateDecision.BLOCK:
            sm.request(DraftWorkflowState.BLOCKED)
            project.workflow_state = DraftWorkflowState.BLOCKED
            return ProjectRunResult(project.project_id, results,
                                    DraftWorkflowState.BLOCKED,
                                    artifacts.for_project(project.project_id),
                                    blocked=True, block_reason=r.reason_code,
                                    preflight_report=preflight)
        # advance state qua state machine (WP-01 ở INTAKE = state khởi đầu, bỏ qua)
        if wp.research_state != DraftWorkflowState.INTAKE:
            t = sm.request(wp.research_state)
            if t.decision != "ALLOWED":
                project.workflow_state = DraftWorkflowState.BLOCKED
                return ProjectRunResult(project.project_id, results,
                                        DraftWorkflowState.BLOCKED,
                                        artifacts.for_project(project.project_id),
                                        blocked=True, block_reason=t.reason_code,
                                        preflight_report=preflight)
        project.workflow_state = sm.state
        field = _STATUS_FIELD_BY_WP.get(wp.wp_id)
        if field:
            setattr(project, field, ComponentStatus.READY_FOR_REVIEW)

    sm.request(DraftWorkflowState.DRAFT_COMPLETE)
    project.workflow_state = sm.state
    return ProjectRunResult(project.project_id, results,
                            sm.state,
                            artifacts.for_project(project.project_id), blocked=False,
                            preflight_report=preflight)
