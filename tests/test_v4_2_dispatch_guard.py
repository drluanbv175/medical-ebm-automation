"""
V4.2 Integration Tests — DispatchGuard

Tests T04–T05, T16:
  T04 — direct runtime call without orchestrator context → DirectRuntimeBypassError
  T05 — DispatchGuard blocks dispatch without valid registry entry
  T16 — production connector marker in WorkflowContext → BLOCKED

KHÔNG gọi API. KHÔNG PII. KHÔNG kết nối HIS/EMR.
Qualification: NO-GO — MRAQ 43.56/100 (threshold >= 75).
"""

from __future__ import annotations

import pytest

from runtime.agent_registry import AgentRegistryEntry, from_entries_for_testing
from runtime.dispatch_guard import (
    DispatchGuard,
    DispatchGuardViolation,
    DirectRuntimeBypassError,
    assert_via_orchestrator,
    enter_orchestrated_context,
    exit_orchestrated_context,
    reset_guard_context,
    is_in_orchestrated_context,
)
from runtime.workflow_context import WorkflowContext
from runtime.schemas import WorkflowStateEnum


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_entry(
    agent_id: str = "co-mau-nghien-cuu",
    *,
    source_hash: str = "abc123",
    hash_verified: bool = True,
    allowed_runtime: str = "MOCK_ONLY",
) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        agent_id=agent_id,
        agent_path=f".claude/agents/{agent_id}.md",
        agent_source_hash=source_hash,
        policy_dependencies=[],
        allowed_runtime=allowed_runtime,
        source_file_exists=True,
        hash_verified=hash_verified,
    )


def _make_ctx(run_id: str = "RUN-TESTONLY") -> WorkflowContext:
    ctx = WorkflowContext.create(
        workflow_id="WF-GUARD-TEST",
        agent_id="co-mau-nghien-cuu",
        fixture_id="FX-001",
        state_before=WorkflowStateEnum.DRAFT.value,
    )
    # Override run_id cho test control
    object.__setattr__(ctx, "run_id", run_id)
    return ctx


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


# ── T04: direct runtime bypass blocked ──────────────────────────────────────

class TestT04DirectRuntimeBypass:
    """
    T04 — Calling assert_via_orchestrator with a run_id NOT registered in
    _ORCHESTRATOR_ACTIVE_RUNS raises DirectRuntimeBypassError.

    This proves: if MockAgentRuntime were called directly (bypassing
    ControlledOrchestrator) the DispatchGuard would detect and block it.
    """

    def test_direct_call_raises_bypass_error(self):
        run_id = "BYPASS-ATTEMPT-001"
        # Do NOT enter orchestrated context — simulate direct call
        with pytest.raises(DirectRuntimeBypassError) as exc_info:
            assert_via_orchestrator(run_id)
        assert "DIRECT_RUNTIME_BYPASS_BLOCKED" in str(exc_info.value)
        assert run_id in str(exc_info.value)

    def test_registered_run_id_passes(self):
        run_id = "ORCH-RUN-VALID"
        enter_orchestrated_context(run_id)
        try:
            assert_via_orchestrator(run_id)  # Must NOT raise
        finally:
            exit_orchestrated_context(run_id)

    def test_different_run_id_still_blocked(self):
        real_run_id = "ORCH-RUN-REAL"
        fake_run_id = "BYPASS-ATTEMPT-FAKE"
        enter_orchestrated_context(real_run_id)
        try:
            with pytest.raises(DirectRuntimeBypassError):
                assert_via_orchestrator(fake_run_id)
        finally:
            exit_orchestrated_context(real_run_id)

    def test_context_exits_after_dispatch(self):
        run_id = "ORCH-RUN-EXIT"
        enter_orchestrated_context(run_id)
        exit_orchestrated_context(run_id)
        assert not is_in_orchestrated_context(run_id)
        with pytest.raises(DirectRuntimeBypassError):
            assert_via_orchestrator(run_id)


# ── T05: DispatchGuard blocks missing agent ──────────────────────────────────

class TestT05DispatchGuardMissingEntry:
    """T05 — DispatchGuard.check() raises DispatchGuardViolation when entry=None."""

    def test_none_entry_raises_violation(self):
        guard = DispatchGuard()
        run_id = "RUN-GUARD-T05"
        ctx = _make_ctx(run_id)
        enter_orchestrated_context(run_id)
        try:
            with pytest.raises(DispatchGuardViolation) as exc_info:
                guard.check(
                    agent_id="ghost-agent",
                    entry=None,
                    run_id=run_id,
                    workflow_context=ctx,
                )
            assert "DISPATCH_BLOCKED" in str(exc_info.value)
            assert "not found in registry" in str(exc_info.value)
        finally:
            exit_orchestrated_context(run_id)

    def test_none_agent_id_raises_violation(self):
        guard = DispatchGuard()
        run_id = "RUN-GUARD-T05B"
        ctx = _make_ctx(run_id)
        enter_orchestrated_context(run_id)
        try:
            with pytest.raises(DispatchGuardViolation):
                guard.check(
                    agent_id="",
                    entry=None,
                    run_id=run_id,
                    workflow_context=ctx,
                )
        finally:
            exit_orchestrated_context(run_id)

    def test_none_hash_raises_violation(self):
        guard = DispatchGuard()
        entry = _make_entry()
        object.__setattr__(entry, "agent_source_hash", None)
        run_id = "RUN-GUARD-T05C"
        ctx = _make_ctx(run_id)
        enter_orchestrated_context(run_id)
        try:
            with pytest.raises(DispatchGuardViolation) as exc_info:
                guard.check(
                    agent_id="co-mau-nghien-cuu",
                    entry=entry,
                    run_id=run_id,
                    workflow_context=ctx,
                )
            assert "agent_source_hash is None" in str(exc_info.value)
        finally:
            exit_orchestrated_context(run_id)


# ── T16: production connector marker blocked ─────────────────────────────────

class TestT16ProductionConnectorBlocked:
    """T16 — _production_connector=True in WorkflowContext blocks dispatch."""

    def test_production_connector_raises_violation(self):
        guard = DispatchGuard()
        entry = _make_entry()
        run_id = "RUN-PROD-T16"
        ctx = _make_ctx(run_id)
        # Set production connector marker
        object.__setattr__(ctx, "_production_connector", True)
        enter_orchestrated_context(run_id)
        try:
            with pytest.raises(DispatchGuardViolation) as exc_info:
                guard.check(
                    agent_id="co-mau-nghien-cuu",
                    entry=entry,
                    run_id=run_id,
                    workflow_context=ctx,
                )
            assert "PRODUCTION_CONNECTOR_MARKER" in str(exc_info.value)
        finally:
            exit_orchestrated_context(run_id)

    def test_auto_submit_raises_violation(self):
        guard = DispatchGuard()
        entry = _make_entry()
        run_id = "RUN-AUTO-T16B"
        ctx = _make_ctx(run_id)
        object.__setattr__(ctx, "_auto_submit", True)
        enter_orchestrated_context(run_id)
        try:
            with pytest.raises(DispatchGuardViolation) as exc_info:
                guard.check(
                    agent_id="co-mau-nghien-cuu",
                    entry=entry,
                    run_id=run_id,
                    workflow_context=ctx,
                )
            assert "AUTO_SUBMIT" in str(exc_info.value)
        finally:
            exit_orchestrated_context(run_id)

    def test_clean_context_passes_all_dispatch_guard_checks(self):
        guard = DispatchGuard()
        entry = _make_entry()
        run_id = "RUN-CLEAN-T16C"
        ctx = _make_ctx(run_id)
        enter_orchestrated_context(run_id)
        try:
            guard.check(
                agent_id="co-mau-nghien-cuu",
                entry=entry,
                run_id=run_id,
                workflow_context=ctx,
            )  # Must NOT raise
        finally:
            exit_orchestrated_context(run_id)
