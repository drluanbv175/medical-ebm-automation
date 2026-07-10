"""
V4.2 Integration Tests — Bypass Resistance

Tests T04 (bypass angle), T05 (dispatch without valid context), T22:
  T04 — prove MockAgentRuntime cannot be dispatched without orchestrator
  T05 — dispatch without valid workflow_context is blocked
  T22 — SYNTHETIC_TECHNICAL_APPROVAL_FIXTURE is NOT mistaken for human approval

Mục đích: chứng minh các cơ chế chống bypass hoạt động theo 4 góc tấn công:
  A. Direct runtime call (không qua orchestrator)
  B. Dispatch với context None
  C. Synthetic approval được truyền vào gate check thật
  D. Agent-created approval bị ledger block

KHÔNG gọi API. KHÔNG PII. KHÔNG kết nối HIS/EMR.
Qualification: NO-GO — MRAQ 43.56/100 (threshold >= 75).
"""

from __future__ import annotations

import pytest

from runtime.agent_registry import AgentRegistryEntry, from_entries_for_testing
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.controlled_orchestrator import ControlledOrchestrator
from runtime.dispatch_guard import (
    DirectRuntimeBypassError,
    assert_via_orchestrator,
    reset_guard_context,
)
from runtime.mock_agent_runtime import MockAgentRuntime
from runtime.schemas import PolicyDecisionEnum, WorkflowStateEnum
from runtime.workflow_context import WorkflowContext
from runtime.workflow_state_machine import WorkflowStateMachine

# ── Helpers ──────────────────────────────────────────────────────────────────

SYNTHETIC_FIXTURE_LABEL = "SYNTHETIC_TECHNICAL_APPROVAL_FIXTURE"


def _make_entry(agent_id: str = "co-mau-nghien-cuu") -> AgentRegistryEntry:
    return AgentRegistryEntry(
        agent_id=agent_id,
        agent_path=f".claude/agents/{agent_id}.md",
        agent_source_hash="testsha256cafebabe",
        policy_dependencies=[],
        allowed_runtime="MOCK_ONLY",
        source_file_exists=True,
        hash_verified=True,
    )


def _make_orchestrator(entries=None, ledger=None):
    registry = from_entries_for_testing(entries or [])
    ledger = ledger or ApprovalLedger()
    return ControlledOrchestrator(
        registry=registry,
        ledger=ledger,
        mock_runtime=MockAgentRuntime(),
        state_machine=WorkflowStateMachine(workflow_id="WF-BYPASS"),
        audit_logger=AuditLogger(run_id="AUDIT-BYPASS"),
    ), ledger


def _make_synthetic_approval(gate_id: str):
    """
    SYNTHETIC_TECHNICAL_APPROVAL_FIXTURE — tạo approval dán nhãn rõ ràng.
    reviewer_role = SYNTHETIC_TEST_FIXTURE → KHÔNG phải người thật.
    """
    return ApprovalLedger.make_human_approval(
        gate_id=gate_id,
        reviewer_role=SYNTHETIC_FIXTURE_LABEL,
        reviewer_ref="OFFLINE_TEST_HARNESS",
        scope=f"{gate_id}_SYNTHETIC_TEST",
        evidence_content=f"SYNTHETIC_FIXTURE_EVIDENCE_FOR_{gate_id}",
    )


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


# ── T04 (bypass angle): MockAgentRuntime inaccessible without orchestrator ───

class TestT04BypassResistance:
    """
    T04 — Prove that MockAgentRuntime cannot be reached without orchestrator.

    ControlledOrchestrator registers run_id in _ORCHESTRATOR_ACTIVE_RUNS.
    Any direct dispatch attempt (no registered run_id) is caught by
    assert_via_orchestrator() → DirectRuntimeBypassError.

    This test proves the mechanism works by:
    1. Attempting direct call → gets blocked
    2. Going through orchestrator → succeeds
    """

    def test_direct_bypass_attempt_blocked(self):
        fake_run_id = "DIRECT-BYPASS-001"
        with pytest.raises(DirectRuntimeBypassError) as exc_info:
            assert_via_orchestrator(fake_run_id)
        assert "DIRECT_RUNTIME_BYPASS_BLOCKED" in str(exc_info.value)

    def test_multiple_bypass_attempts_all_blocked(self):
        for i in range(5):
            with pytest.raises(DirectRuntimeBypassError):
                assert_via_orchestrator(f"BYPASS-ATTEMPT-{i:03d}")

    def test_orchestrated_path_succeeds(self):
        entry = _make_entry()
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = WorkflowContext.create(
            workflow_id="WF-T04",
            agent_id="co-mau-nghien-cuu",
            fixture_id="FX-001",
            state_before=WorkflowStateEnum.DRAFT.value,
        )
        result = orch.run(ctx)
        assert result.blocked is False
        assert result.policy_decision == PolicyDecisionEnum.PASS

    def test_bypass_with_valid_but_unregistered_run_id_blocked(self):
        # Even a well-formed run_id is blocked if not via orchestrator
        with pytest.raises(DirectRuntimeBypassError):
            assert_via_orchestrator("RUN-A1B2C3D4E5F6")


# ── T05 (bypass angle): dispatch without valid workflow_context ──────────────

class TestT05DispatchWithoutContext:
    """T05 — Dispatch with workflow_context=None is blocked at PRE_STEP1."""

    def test_none_context_blocked(self):
        entry = _make_entry()
        orch, _ = _make_orchestrator(entries=[entry])
        result = orch.run(workflow_context=None)
        assert result.blocked is True
        assert "NONE" in result.reason_code.upper()

    def test_none_context_policy_block(self):
        entry = _make_entry()
        orch, _ = _make_orchestrator(entries=[entry])
        result = orch.run(workflow_context=None)
        assert result.policy_decision == PolicyDecisionEnum.BLOCK

    def test_none_context_no_audit_event(self):
        entry = _make_entry()
        registry = from_entries_for_testing([entry])
        ledger = ApprovalLedger()
        logger = AuditLogger(run_id="AUDIT-T05")
        orch = ControlledOrchestrator(
            registry=registry,
            ledger=ledger,
            mock_runtime=MockAgentRuntime(),
            state_machine=WorkflowStateMachine(workflow_id="WF-T05"),
            audit_logger=logger,
        )
        orch.run(workflow_context=None)
        assert logger.count() == 0


# ── T22: Synthetic approval NOT mistaken for human ───────────────────────────

class TestT22SyntheticNotHuman:
    """
    T22 — SYNTHETIC_TECHNICAL_APPROVAL_FIXTURE is clearly labeled.

    Invariant: reviewer_role MUST be "SYNTHETIC_TEST_FIXTURE", NOT a real role.
    The fixture is used ONLY to test gate plumbing, NOT to claim real approval.
    """

    def test_synthetic_approval_has_fixture_label(self):
        record = _make_synthetic_approval("G2")
        assert record.reviewer_role == SYNTHETIC_FIXTURE_LABEL

    def test_synthetic_approval_not_human_role(self):
        record = _make_synthetic_approval("G2")
        human_roles = {"PI", "IRB_CHAIR", "ETHICS_BOARD", "PHYSICIAN", "REVIEWER"}
        assert record.reviewer_role not in human_roles

    def test_synthetic_approval_can_be_added_to_ledger(self):
        # The fixture CAN be added to the ledger (it is valid data format)
        ledger = ApprovalLedger()
        record = _make_synthetic_approval("G2")
        success, reason = ledger.add_approval(record, created_by_agent=False)
        assert success is True
        assert reason == "ADDED"

    def test_synthetic_approval_makes_gate_pass_in_test_only(self):
        # In test context: synthetic approval satisfies gate check for plumbing test
        # This proves gate plumbing works WITHOUT claiming real ethics approval
        ledger = ApprovalLedger()
        record = _make_synthetic_approval("G2")
        ledger.add_approval(record, created_by_agent=False)
        assert ledger.has_ethics_approval() is True

    def test_agent_created_approval_is_blocked_by_ledger(self):
        # Prove: an Agent cannot create its own approval to bypass gates
        ledger = ApprovalLedger()
        record = _make_synthetic_approval("G2")
        # Force agent-created flag
        object.__setattr__(record, "_created_by_agent", True)
        success, reason = ledger.add_approval(record, created_by_agent=True)
        assert success is False
        assert "AGENT_CREATED" in reason

    def test_synthetic_scope_clearly_labeled(self):
        record = _make_synthetic_approval("G2")
        assert "SYNTHETIC" in record.scope.upper() or "TEST" in record.scope.upper()

    def test_synthetic_reviewer_ref_is_harness_not_person(self):
        record = _make_synthetic_approval("G9")
        assert "HARNESS" in record.reviewer_identity_reference.upper()
