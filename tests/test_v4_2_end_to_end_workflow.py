"""
V4.2 Integration Tests — End-to-End Workflow

Tests T06–T15, T23–T24:
  T06 — G2 gate blocks transition without ethics approval
  T07 — G4 gate blocks analysis without SAP lock
  T08 — G9 gate blocks release without PI sign-off
  T09 — GATE_A blocks clinical application step
  T10 — GATE_B blocks ledger write step
  T11 — PII in fixture output → policy=PII_BLOCKED, dispatch halted
  T12 — fabricated data in fixture → policy=BLOCK
  T13 — fabricated citation sentinel → policy=BLOCK
  T14 — raw data write attempt → policy=BLOCK
  T15 — auto-submit attempt → blocked at STEP5 marker check
  T23 — happy path: all gates pass, FX-001 → PASS, trace complete
  T24 — full chain traceable: run_id → audit_event_id → context

OFFLINE_ROLE_APPROVAL_FIXTURE dùng để test gate plumbing với role đúng nhóm.
KHÔNG thay thế approval của người thật trong vận hành thực.
KHÔNG gọi API. KHÔNG PII. Qualification: NO-GO — MRAQ 43.56/100.
"""

from __future__ import annotations

from runtime.agent_registry import AgentRegistryEntry, from_entries_for_testing
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.controlled_orchestrator import ControlledOrchestrator
from runtime.dispatch_guard import reset_guard_context
from runtime.mock_agent_runtime import MockAgentRuntime
from runtime.schemas import PolicyDecisionEnum, WorkflowStateEnum
from runtime.workflow_context import WorkflowContext
from runtime.workflow_state_machine import WorkflowStateMachine

# ── Helpers ──────────────────────────────────────────────────────────────────

OFFLINE_ROLE_APPROVAL_FIXTURE = "OFFLINE_ROLE_APPROVAL_FIXTURE"


def _make_entry(
    agent_id: str,
    policy_deps: list = None,
    source_hash: str = "sha256testvalue",
) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        agent_id=agent_id,
        agent_path=f".claude/agents/{agent_id}.md",
        agent_source_hash=source_hash,
        policy_dependencies=policy_deps or [],
        allowed_runtime="MOCK_ONLY",
        source_file_exists=True,
        hash_verified=True,
    )


def _make_synthetic_approval(gate_id: str):
    role_by_gate = {
        "G2": "IRB_ETHICS_COMMITTEE",
        "G4": "METHODS_STATISTICS_REVIEWER",
        "G9": "PI_PROJECT_OWNER",
    }
    return ApprovalLedger.make_human_approval(
        gate_id=gate_id,
        reviewer_role=role_by_gate.get(gate_id, OFFLINE_ROLE_APPROVAL_FIXTURE),
        reviewer_ref="OFFLINE_TEST_HARNESS",
        scope=f"{gate_id}_SYNTHETIC_TEST",
        evidence_content=f"SYNTHETIC_EVIDENCE_{gate_id}",
    )


def _build_orch(
    agent_id: str,
    policy_deps: list = None,
    ledger: ApprovalLedger = None,
    workflow_id: str = "WF-E2E",
) -> tuple[ControlledOrchestrator, ApprovalLedger, AuditLogger]:
    entry = _make_entry(agent_id, policy_deps=policy_deps or [])
    registry = from_entries_for_testing([entry])
    ledger = ledger or ApprovalLedger()
    logger = AuditLogger(run_id=f"AUDIT-{workflow_id}")
    orch = ControlledOrchestrator(
        registry=registry,
        ledger=ledger,
        mock_runtime=MockAgentRuntime(),
        state_machine=WorkflowStateMachine(workflow_id=workflow_id),
        audit_logger=logger,
    )
    return orch, ledger, logger


def _ctx(
    agent_id: str,
    fixture_id: str = "FX-001",
    state_before: str = WorkflowStateEnum.DRAFT.value,
) -> WorkflowContext:
    return WorkflowContext.create(
        workflow_id="WF-E2E",
        agent_id=agent_id,
        fixture_id=fixture_id,
        state_before=state_before,
    )


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


# ── T06: G2 gate blocks without ethics approval ──────────────────────────────

class TestT06G2GateBlocks:
    """T06 — Without G2 approval, agent with G2 dependency is blocked."""

    def test_g2_gate_blocks_dispatch(self):
        orch, ledger, _ = _build_orch("dao-duc-dang-ky", policy_deps=["G2"])
        ctx = _ctx("dao-duc-dang-ky")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "G2" in result.reason_code or "ETHICS" in result.reason_code

    def test_g2_gate_passes_with_synthetic_approval(self):
        orch, ledger, _ = _build_orch("dao-duc-dang-ky", policy_deps=["G2"])
        ledger.add_approval(_make_synthetic_approval("G2"))
        ctx = _ctx("dao-duc-dang-ky")
        result = orch.run(ctx)
        assert result.blocked is False

    def test_blocked_at_step6(self):
        orch, _, _ = _build_orch("dao-duc-dang-ky", policy_deps=["G2"])
        ctx = _ctx("dao-duc-dang-ky")
        result = orch.run(ctx)
        assert "STEP6" in result.blocked_at_step


# ── T07: G4 gate blocks without SAP lock ────────────────────────────────────

class TestT07G4SAPGateBlocks:
    """T07 — Without G4 (SAP lock), agent with G4 dependency is blocked."""

    def test_g4_gate_blocks(self):
        orch, _, _ = _build_orch("phan-tich-thong-ke", policy_deps=["G4"])
        ctx = _ctx("phan-tich-thong-ke")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "G4" in result.reason_code or "SAP" in result.reason_code

    def test_g4_gate_passes_with_synthetic_sap(self):
        orch, ledger, _ = _build_orch("phan-tich-thong-ke", policy_deps=["G4"])
        ledger.add_approval(_make_synthetic_approval("G4"))
        ctx = _ctx("phan-tich-thong-ke")
        result = orch.run(ctx)
        assert result.blocked is False

    def test_blocked_at_step7(self):
        orch, _, _ = _build_orch("phan-tich-thong-ke", policy_deps=["G4"])
        ctx = _ctx("phan-tich-thong-ke")
        result = orch.run(ctx)
        assert "STEP7" in result.blocked_at_step


# ── T08: G9 gate blocks without PI sign-off ─────────────────────────────────

class TestT08G9PIGateBlocks:
    """T08 — Without G9 (PI sign-off), agent with G9 dependency is blocked."""

    def test_g9_gate_blocks(self):
        orch, _, _ = _build_orch("viet-ban-thao", policy_deps=["G9"])
        ctx = _ctx("viet-ban-thao")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "G9" in result.reason_code or "PI" in result.reason_code

    def test_g9_gate_passes_with_synthetic_pi(self):
        orch, ledger, _ = _build_orch("viet-ban-thao", policy_deps=["G9"])
        ledger.add_approval(_make_synthetic_approval("G9"))
        ctx = _ctx("viet-ban-thao")
        result = orch.run(ctx)
        assert result.blocked is False


# ── T09: GATE_A blocks clinical application step ─────────────────────────────

class TestT09GateABlocks:
    """T09 — Without GATE_A, agent with GATE_A dependency is blocked."""

    def test_gate_a_blocks(self):
        orch, _, _ = _build_orch("ke-don-an-toan", policy_deps=["GATE_A"])
        ctx = _ctx("ke-don-an-toan")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "GATE_A" in result.reason_code

    def test_gate_a_passes_with_approval(self):
        orch, ledger, _ = _build_orch("ke-don-an-toan", policy_deps=["GATE_A"])
        ledger.add_approval(_make_synthetic_approval("GATE_A"))
        ctx = _ctx("ke-don-an-toan")
        result = orch.run(ctx)
        assert result.blocked is False


# ── T10: GATE_B blocks ledger write step ────────────────────────────────────

class TestT10GateBBlocks:
    """T10 — Without GATE_B, agent with GATE_B dependency is blocked."""

    def test_gate_b_blocks(self):
        orch, _, _ = _build_orch("so-cai-ghi-nho", policy_deps=["GATE_B"])
        ctx = _ctx("so-cai-ghi-nho")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "GATE_B" in result.reason_code

    def test_gate_b_passes_with_approval(self):
        orch, ledger, _ = _build_orch("so-cai-ghi-nho", policy_deps=["GATE_B"])
        ledger.add_approval(_make_synthetic_approval("GATE_B"))
        ctx = _ctx("so-cai-ghi-nho")
        result = orch.run(ctx)
        assert result.blocked is False


# ── T11: PII in fixture output → PII_BLOCKED ─────────────────────────────────

class TestT11PIIInFixture:
    """T11 — FX-004 (PII_LEAK) → policy=PII_BLOCKED."""

    def test_pii_fixture_yields_blocked(self):
        orch, _, _ = _build_orch("ke-don-an-toan")
        ctx = _ctx("ke-don-an-toan", fixture_id="FX-004")
        result = orch.run(ctx)
        assert result.blocked is False  # orchestrator ran, did not crash
        assert result.policy_decision in (
            PolicyDecisionEnum.PII_BLOCKED,
            PolicyDecisionEnum.BLOCK,
        )

    def test_pii_blocked_audit_pii_verdict(self):
        """FX-004's simulated_output nests real-shaped PII (tên + CCCD) trong list
        (records[0]) — trước audit 2026-07-11, _has_pii() chỉ soát string cấp CAO
        NHẤT nên bỏ lọt, pii_verdict ghi sai 'CLEAN'. Giờ PHẢI là 'BLOCKED'."""
        orch, _, logger = _build_orch("ke-don-an-toan")
        ctx = _ctx("ke-don-an-toan", fixture_id="FX-004")
        orch.run(ctx)
        assert logger.count() > 0
        events = logger.get_events()
        assert all(e.pii_verdict == "BLOCKED" for e in events)


# ── T12: fabricated data → BLOCK ─────────────────────────────────────────────

class TestT12FabricatedData:
    """T12 — FX-002 (FABRICATED_DATA) → policy=BLOCK."""

    def test_fabricated_data_blocked(self):
        orch, _, _ = _build_orch("phan-tich-thong-ke")
        ctx = _ctx("phan-tich-thong-ke", fixture_id="FX-002")
        result = orch.run(ctx)
        assert result.blocked is False
        assert result.policy_decision == PolicyDecisionEnum.BLOCK

    def test_state_unchanged_on_fabricated(self):
        orch, _, _ = _build_orch("phan-tich-thong-ke")
        ctx = _ctx("phan-tich-thong-ke", fixture_id="FX-002")
        result = orch.run(ctx)
        assert result.state_transition is None


# ── T13: fabricated citation → BLOCK ─────────────────────────────────────────

class TestT13FabricatedCitation:
    """T13 — FX-003 (FABRICATED_CITATION) → policy=BLOCK."""

    def test_fabricated_citation_blocked(self):
        orch, _, _ = _build_orch("kiem-chung-trich-dan")
        ctx = _ctx("kiem-chung-trich-dan", fixture_id="FX-003")
        result = orch.run(ctx)
        assert result.blocked is False
        assert result.policy_decision == PolicyDecisionEnum.BLOCK


# ── T14: raw data write attempt → BLOCK ──────────────────────────────────────

class TestT14RawDataWrite:
    """T14 — FX-009 (RAW_DATA_WRITE_ATTEMPT) → policy=BLOCK."""

    def test_raw_data_write_blocked(self):
        orch, _, _ = _build_orch("quan-ly-du-lieu")
        ctx = _ctx("quan-ly-du-lieu", fixture_id="FX-009")
        result = orch.run(ctx)
        assert result.blocked is False
        assert result.policy_decision == PolicyDecisionEnum.BLOCK


# ── T15: auto-submit → STEP5 blocked ─────────────────────────────────────────

class TestT15AutoSubmit:
    """T15 — AUTO_SUBMIT_MARKER in context → blocked at STEP5."""

    def test_auto_submit_blocked_at_step5(self):
        orch, _, _ = _build_orch("nop-bai-phan-hoi", policy_deps=["AUTO_SUBMIT"])
        ctx = _ctx("nop-bai-phan-hoi", fixture_id="FX-008")
        object.__setattr__(ctx, "_auto_submit", True)
        result = orch.run(ctx)
        assert result.blocked is True
        assert "STEP5" in result.blocked_at_step
        assert "AUTO_SUBMIT" in result.reason_code

    def test_auto_submit_flag_false_passes_step5(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu")
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        # _auto_submit defaults to False
        assert getattr(ctx, "_auto_submit", False) is False
        result = orch.run(ctx)
        # Should not be blocked at STEP5
        if result.blocked:
            assert "STEP5" not in (result.blocked_at_step or "")


# ── T23: happy path, all gates pass, FX-001 ──────────────────────────────────

class TestT23HappyPath:
    """T23 — Happy path: no gate deps, FX-001, PASS, trace complete."""

    def test_happy_path_pass(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.blocked is False
        assert result.policy_decision == PolicyDecisionEnum.PASS

    def test_happy_path_audit_event(self):
        orch, _, logger = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        orch.run(ctx)
        assert logger.count() == 1

    def test_happy_path_pii_verdict_clean(self):
        orch, _, logger = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        orch.run(ctx)
        events = logger.get_events()
        assert events[0].pii_verdict == "CLEAN"

    def test_happy_path_state_before_available(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.state_before == WorkflowStateEnum.DRAFT.value

    def test_happy_path_not_valid_for_research(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        # Invariant: never claims validity for real research
        assert result.workflow_context.not_valid_for_real_research is True

    def test_happy_path_human_approval_false(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        # Invariant: no human approval claimed in offline mode
        assert result.workflow_context.human_approval is False


# ── T24: full chain traceable ─────────────────────────────────────────────────

class TestT24Traceability:
    """T24 — Full chain: run_id → audit_event_id → WorkflowContext traceable."""

    def test_run_id_propagates_to_audit(self):
        orch, _, logger = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.audit_event is not None
        assert result.audit_event.run_id is not None

    def test_audit_event_id_in_context(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.audit_event_id is not None

    def test_agent_hash_traceable(self):
        source_hash = "traceable_hash_12345"
        orch, _, _ = _build_orch(
            "co-mau-nghien-cuu", policy_deps=[],
        )
        # Inject known hash
        entry = _make_entry("co-mau-nghien-cuu", source_hash=source_hash)
        from runtime.agent_registry import from_entries_for_testing
        registry = from_entries_for_testing([entry])
        orch._registry = registry
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.agent_source_hash == source_hash

    def test_is_trace_complete_after_happy_path(self):
        orch, _, _ = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.is_trace_complete() is True

    def test_fixture_id_in_audit_event(self):
        orch, _, logger = _build_orch("co-mau-nghien-cuu", policy_deps=[])
        ctx = _ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        orch.run(ctx)
        events = logger.get_events()
        assert events[0].fixture_id == "FX-001"

    def test_workflow_id_in_audit_event(self):
        orch, _, logger = _build_orch("co-mau-nghien-cuu", policy_deps=[], workflow_id="WF-TRACE")
        ctx = WorkflowContext.create(
            workflow_id="WF-TRACE",
            agent_id="co-mau-nghien-cuu",
            fixture_id="FX-001",
            state_before=WorkflowStateEnum.DRAFT.value,
        )
        orch.run(ctx)
        events = logger.get_events()
        assert events[0].workflow_id == "WF-TRACE"
