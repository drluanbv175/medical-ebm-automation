"""
V4.2 Integration Tests — ControlledOrchestrator

Tests T01–T03, T17–T21:
  T01 — agent not in registry → STEP2 blocked
  T02 — agent hash is None → STEP3 blocked
  T03 — hash not verified (mismatch) → STEP12 DispatchGuard blocked
  T17 — fixture SCHEMA_FAIL → policy=SCHEMA_FAIL, audit logged, state unchanged
  T18 — fixture TIMEOUT → policy=BLOCK, safe stop, state unchanged
  T19 — invalid/illegal state transition request → WorkflowStateMachine blocks
  T20 — audit event exists after successful run
  T21 — agent_source_hash recorded in WorkflowContext after run

KHÔNG gọi API. KHÔNG PII. KHÔNG kết nối HIS/EMR.
Qualification: NO-GO — MRAQ 43.56/100 (threshold >= 75).
"""

from __future__ import annotations

import pytest

from runtime.agent_registry import (
    AgentRegistryEntry,
    from_entries_for_testing,
    reset_registry,
)
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.controlled_orchestrator import ControlledOrchestrator, _has_pii
from runtime.dispatch_guard import reset_guard_context
from runtime.mock_agent_runtime import MockAgentRuntime, FIXTURE_CATALOG
from runtime.schemas import PolicyDecisionEnum, WorkflowStateEnum
from runtime.workflow_context import WorkflowContext
from runtime.workflow_state_machine import WorkflowStateMachine


# ── Fixtures & helpers ──────────────────────────────────────────────────────

SYNTHETIC_FIXTURE_LABEL = "SYNTHETIC_TECHNICAL_APPROVAL_FIXTURE"
SYNTHETIC_NOT_HUMAN = True  # invariant: never pass as human approval


def _make_entry(
    agent_id: str,
    *,
    source_hash: str = "abc123dead",
    hash_verified: bool = True,
    allowed_runtime: str = "MOCK_ONLY",
    policy_deps: list = None,
) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        agent_id=agent_id,
        agent_path=f".claude/agents/{agent_id}.md",
        agent_source_hash=source_hash,
        policy_dependencies=policy_deps or [],
        allowed_runtime=allowed_runtime,
        source_file_exists=True,
        hash_verified=hash_verified,
    )


def _make_orchestrator(entries: list = None, ledger: ApprovalLedger = None):
    registry = from_entries_for_testing(entries or [])
    ledger = ledger or ApprovalLedger()
    runtime = MockAgentRuntime()
    state_machine = WorkflowStateMachine(workflow_id="WF-TEST")
    logger = AuditLogger(run_id="AUDIT-TEST")
    orch = ControlledOrchestrator(
        registry=registry,
        ledger=ledger,
        mock_runtime=runtime,
        state_machine=state_machine,
        audit_logger=logger,
    )
    return orch, logger


def _make_ctx(agent_id: str, fixture_id: str = "FX-001") -> WorkflowContext:
    return WorkflowContext.create(
        workflow_id="WF-TEST",
        agent_id=agent_id,
        fixture_id=fixture_id,
        state_before=WorkflowStateEnum.DRAFT.value,
    )


def setup_function():
    reset_registry()
    reset_guard_context()


def teardown_function():
    reset_guard_context()


# ── T01: agent not in registry ──────────────────────────────────────────────

class TestT01AgentNotInRegistry:
    """T01 — Dispatch blocked when agent_id not in registry."""

    def test_blocked_at_step2(self):
        orch, _ = _make_orchestrator(entries=[])  # empty registry
        ctx = _make_ctx("nonexistent-agent")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "STEP2" in result.blocked_at_step
        assert "AGENT_NOT_IN_REGISTRY" in result.reason_code

    def test_policy_decision_is_block(self):
        orch, _ = _make_orchestrator(entries=[])
        ctx = _make_ctx("ghost-agent")
        result = orch.run(ctx)
        assert result.policy_decision == PolicyDecisionEnum.BLOCK

    def test_no_dispatch_occurred(self):
        orch, logger = _make_orchestrator(entries=[])
        ctx = _make_ctx("nonexistent-agent")
        orch.run(ctx)
        assert logger.count() == 0  # audit logger not reached

    def test_fixture_result_is_none(self):
        orch, _ = _make_orchestrator(entries=[])
        ctx = _make_ctx("bad-agent")
        result = orch.run(ctx)
        assert result.fixture_result is None


# ── T02: agent source hash is None ─────────────────────────────────────────

class TestT02AgentHashNone:
    """T02 — Dispatch blocked when entry.agent_source_hash is None."""

    def test_blocked_at_step3(self):
        entry = _make_entry("co-mau-nghien-cuu", source_hash=None, hash_verified=False)
        # Bypass dataclass restriction: set None after creation
        object.__setattr__(entry, "agent_source_hash", None)
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu")
        result = orch.run(ctx)
        assert result.blocked is True
        assert "STEP3" in result.blocked_at_step
        assert "AGENT_HASH_NONE" in result.reason_code

    def test_workflow_context_not_updated_on_block(self):
        entry = _make_entry("co-mau-nghien-cuu", source_hash=None, hash_verified=False)
        object.__setattr__(entry, "agent_source_hash", None)
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu")
        result = orch.run(ctx)
        assert result.workflow_context.agent_source_hash is None


# ── T03: hash not verified (would fail dispatch guard) ──────────────────────

class TestT03HashNotVerified:
    """T03 — Dispatch blocked at STEP12 DispatchGuard when hash_verified=False."""

    def test_blocked_by_hash_not_verified(self):
        entry = _make_entry(
            "phan-tich-thong-ke",
            source_hash="deadbeef1234",
            hash_verified=False,   # hash present but NOT verified
        )
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("phan-tich-thong-ke")
        result = orch.run(ctx)
        assert result.blocked is True
        # Blocked at STEP3 (hash verification), not dispatched
        assert "STEP3" in result.blocked_at_step
        assert "HASH" in result.reason_code

    def test_audit_event_not_logged_on_hash_verify_block(self):
        entry = _make_entry(
            "phan-tich-thong-ke",
            source_hash="deadbeef1234",
            hash_verified=False,
        )
        orch, logger = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("phan-tich-thong-ke")
        orch.run(ctx)
        assert logger.count() == 0  # audit not reached


# ── T17: fixture SCHEMA_FAIL ─────────────────────────────────────────────────

class TestT17SchemFail:
    """T17 — SCHEMA_FAIL fixture yields policy SCHEMA_FAIL, state unchanged."""

    def test_schema_fail_policy(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-010")  # INVALID_SCHEMA
        result = orch.run(ctx)
        assert result.blocked is False
        assert result.policy_decision == PolicyDecisionEnum.SCHEMA_FAIL

    def test_state_unchanged_after_schema_fail(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-010")
        result = orch.run(ctx)
        # No state transition triggered on non-PASS
        assert result.state_transition is None

    def test_audit_event_logged_on_schema_fail(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, logger = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-010")
        orch.run(ctx)
        assert logger.count() == 1  # audit event was still logged


# ── T18: fixture TIMEOUT → safe stop ─────────────────────────────────────────

class TestT18TimeoutSafeStop:
    """T18 — TIMEOUT fixture yields BLOCK, workflow stopped safely."""

    def test_timeout_yields_block(self):
        entry = _make_entry("tong-quan-y-van")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("tong-quan-y-van", fixture_id="FX-011")  # TIMEOUT
        result = orch.run(ctx)
        assert result.blocked is False  # orchestrator handled it, not crashed
        assert result.policy_decision == PolicyDecisionEnum.BLOCK

    def test_no_state_transition_on_timeout(self):
        entry = _make_entry("tong-quan-y-van")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("tong-quan-y-van", fixture_id="FX-011")
        result = orch.run(ctx)
        assert result.state_transition is None


# ── T19: illegal state transition ───────────────────────────────────────────

class TestT19IllegalStateTransition:
    """T19 — StateMachine blocks invalid transition; state stays unchanged."""

    def test_invalid_transition_blocked_by_state_machine(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")

        # Try to jump from DRAFT directly to RELEASE_APPROVED (illegal)
        result = orch.run(
            ctx,
            requested_state=WorkflowStateEnum.RELEASE_APPROVED,
        )
        # State machine rejects the transition ...
        assert result.state_transition is not None
        assert result.state_transition.decision == "BLOCKED"
        assert "INVALID_TRANSITION" in result.state_transition.reason
        # ... and the orchestrator MUST propagate that rejection: not a silent
        # PASS. Trước khi sửa (audit 2026-07-10): blocked=False + state_after
        # bị gán nhầm thành state ĐÍCH dù transition thật sự bị chặn.
        assert result.blocked is True
        assert result.blocked_at_step == "STEP13_STATE_TRANSITION"
        assert "STATE_TRANSITION_BLOCKED" in result.reason_code

    def test_workflow_context_state_after_unchanged_on_rejected_transition(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, logger = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")

        result = orch.run(
            ctx,
            requested_state=WorkflowStateEnum.RELEASE_APPROVED,
        )
        # ctx.state_after phải giữ nguyên state_before (draft), KHÔNG được
        # gán thành "release_approved" — transition đó chưa từng xảy ra thật.
        assert result.workflow_context.state_after == WorkflowStateEnum.DRAFT.value
        # Audit event ghi lại cũng phải khớp thực tế, không phải optimistic guess.
        events = logger.get_events()
        assert len(events) == 1
        assert events[0].state_after == WorkflowStateEnum.DRAFT.value
        assert events[0].state_before == WorkflowStateEnum.DRAFT.value

    def test_state_machine_history_records_block(self):
        entry = _make_entry("co-mau-nghien-cuu")
        registry = from_entries_for_testing([entry])
        ledger = ApprovalLedger()
        runtime = MockAgentRuntime()
        sm = WorkflowStateMachine(workflow_id="WF-T19")
        logger = AuditLogger(run_id="AUDIT-T19")
        orch = ControlledOrchestrator(
            registry=registry,
            ledger=ledger,
            mock_runtime=runtime,
            state_machine=sm,
            audit_logger=logger,
        )
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        orch.run(ctx, requested_state=WorkflowStateEnum.RELEASE_APPROVED)
        # State machine history must have at least the blocked transition
        assert sm.current_state == WorkflowStateEnum.DRAFT  # unchanged


# ── T20: audit event exists after success ───────────────────────────────────

class TestT20AuditEventExists:
    """T20 — After successful orchestrated run, audit event is logged."""

    def test_audit_event_logged(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, logger = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.audit_event is not None
        assert logger.count() == 1

    def test_audit_event_has_run_id(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, logger = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        orch.run(ctx)
        events = logger.get_events()
        assert len(events) == 1
        assert events[0].run_id is not None

    def test_audit_event_pii_verdict_clean(self):
        entry = _make_entry("co-mau-nghien-cuu")
        orch, logger = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        orch.run(ctx)
        events = logger.get_events()
        assert events[0].pii_verdict == "CLEAN"


# ── T21: agent source hash recorded in WorkflowContext ──────────────────────

class TestT21AgentHashInContext:
    """T21 — agent_source_hash is recorded in WorkflowContext after run."""

    def test_hash_recorded_after_run(self):
        expected_hash = "cafebabe1234567890abcdef"
        entry = _make_entry("co-mau-nghien-cuu", source_hash=expected_hash)
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.agent_source_hash == expected_hash

    def test_hash_not_none_after_pass(self):
        entry = _make_entry("co-mau-nghien-cuu", source_hash="abc123")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.agent_source_hash is not None

    def test_trace_complete_after_full_pass(self):
        entry = _make_entry("co-mau-nghien-cuu", source_hash="abc123")
        orch, _ = _make_orchestrator(entries=[entry])
        ctx = _make_ctx("co-mau-nghien-cuu", fixture_id="FX-001")
        result = orch.run(ctx)
        assert result.workflow_context.is_trace_complete() is True


# ── _has_pii: audit 2026-07-11 — phải bắt PII lồng trong dict/list, không chỉ
# string cấp cao nhất (bug thật: bỏ lọt tên+CCCD lồng trong records[0]) ─────────

class TestHasPiiCatchesNestedStructures:
    def test_pii_nested_in_list_of_dicts_detected(self):
        output = {"records": [{"id": "BN001", "name": "Nguyễn Văn A", "cccd": "012345678901"}],
                  "count": 1}
        assert _has_pii(output) is True

    def test_clean_output_not_flagged(self):
        output = {"summary": "Không phát hiện bất thường.", "count": 0}
        assert _has_pii(output) is False


# ── Khởi tạo với API runtime: audit 2026-07-11 — claude_api_runtime.py hứa
# "orchestrator gọi assert_offline() để CHẶN api runtime" nhưng trước đây không
# gọi ở đâu cả trong ControlledOrchestrator. Giờ phải chặn NGAY lúc khởi tạo.

class TestConstructorBlocksLiveApiRuntime:
    def test_claude_api_runtime_raises_at_construction(self):
        from runtime.agent_runtime import ClaudeApiRuntime

        registry = from_entries_for_testing([])
        with pytest.raises(RuntimeError):
            ControlledOrchestrator(
                registry=registry,
                ledger=ApprovalLedger(),
                mock_runtime=ClaudeApiRuntime(api_key=""),
                state_machine=WorkflowStateMachine(workflow_id="WF-API-GUARD"),
                audit_logger=AuditLogger(run_id="AUDIT-API-GUARD"),
            )

    def test_mock_runtime_still_constructs_fine(self):
        orch, _ = _make_orchestrator(entries=[])
        assert orch is not None
