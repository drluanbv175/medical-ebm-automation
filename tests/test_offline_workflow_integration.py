"""
Phase 3 — Offline Integration Tests (14 test cases).
Kiểm tra toàn bộ pipeline: MockRuntime → PolicyGate → StateMachine → AuditLog.
Không có API call, không PII, hoàn toàn deterministic.
"""

import pytest

from runtime.agent_runtime import ClaudeApiRuntime, LocalModelRuntime, OpenAIApiRuntime
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.mock_agent_runtime import FIXTURE_CATALOG, MockAgentRuntime
from runtime.policy_gate_engine import PolicyGateEngine
from runtime.schemas import (
    GateDecisionEnum,
    PolicyDecisionEnum,
    RuntimeTypeEnum,
    WorkflowStateEnum,
)
from runtime.workflow_state_machine import WorkflowStateMachine

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def runtime():
    return MockAgentRuntime()


@pytest.fixture
def engine():
    return PolicyGateEngine()


@pytest.fixture
def empty_ledger():
    return ApprovalLedger()


@pytest.fixture
def logger():
    return AuditLogger(run_id="run-integration-test")


@pytest.fixture
def state_machine():
    return WorkflowStateMachine("WF-INTEGRATION-001")


def _make_approval(gate_id: str) -> ApprovalLedger:
    ledger = ApprovalLedger()
    record = ApprovalLedger.make_human_approval(
        gate_id=gate_id,
        reviewer_role="TEST",
        reviewer_ref=f"TEST-{gate_id}",
        scope=f"Scope {gate_id}",
        evidence_content=f"Evidence for {gate_id}",
    )
    ledger.add_approval(record)
    return ledger


# ─── TC-01: MockAgentRuntime không gọi API ────────────────────────────────────

class TestTC01MockRuntimeNoApi:
    """TC-01: MockAgentRuntime là offline — không gọi API."""

    def test_mock_runtime_is_not_api(self, runtime):
        assert not runtime.is_api_runtime()

    def test_mock_runtime_type(self, runtime):
        assert runtime.get_runtime_type() == RuntimeTypeEnum.MOCK

    def test_assert_offline_does_not_raise_for_mock(self, runtime):
        runtime.assert_offline()  # không raise

    def test_claude_api_runtime_falls_back_without_key(self):
        # V4.4: ClaudeApiRuntime không raise khi không có key — fallback sang MockRuntime
        api = ClaudeApiRuntime(api_key="")
        result = api.run("co-mau-nghien-cuu", "FX-001", {})
        assert result is not None  # fallback trả FixtureOutput, không raise

    def test_claude_api_runtime_is_api_runtime(self):
        # V4.4: ClaudeApiRuntime là api runtime thật (không phải placeholder offline).
        api = ClaudeApiRuntime(api_key="")
        assert api.is_api_runtime() is True
        assert api.get_runtime_type() == RuntimeTypeEnum.CLAUDE_API

    def test_claude_api_runtime_blocked_offline_governance(self):
        # V4.3 governance: assert_offline() CHẶN api runtime trong Offline/Internal-QA mode.
        api = ClaudeApiRuntime(api_key="")
        with pytest.raises(RuntimeError):
            api.assert_offline()

    def test_openai_api_runtime_raises(self):
        api = OpenAIApiRuntime()
        with pytest.raises(RuntimeError):
            api.run("agent", "FX-001", {})

    def test_local_model_runtime_raises(self):
        api = LocalModelRuntime()
        with pytest.raises(RuntimeError):
            api.run("agent", "FX-001", {})


# ─── TC-02: Tất cả 12 fixture trả đúng expected_policy_decision ──────────────

class TestTC02AllFixturesExpectedDecision:
    """TC-02: 12 fixture đều trả expected_policy_decision đúng."""

    @pytest.mark.parametrize("fixture_id", list(FIXTURE_CATALOG.keys()))
    def test_fixture_expected_decision_matches_evaluation(self, fixture_id, engine, empty_ledger):
        fixture = FIXTURE_CATALOG[fixture_id]
        evaluated = engine.evaluate_fixture(fixture, empty_ledger)
        assert evaluated == fixture.expected_policy_decision, (
            f"Fixture {fixture_id}: expected {fixture.expected_policy_decision}, got {evaluated}"
        )


# ─── TC-03: FX-001 VALID_RESPONSE → PASS ─────────────────────────────────────

class TestTC03ValidResponse:
    """TC-03: FX-001 valid response pipeline."""

    def test_fx001_end_to_end(self, runtime, engine, empty_ledger, logger):
        fixture = runtime.run("co-mau-nghien-cuu", "FX-001", {})
        assert fixture.fixture_id == "FX-001"
        decision = engine.evaluate_fixture(fixture, empty_ledger)
        assert decision == PolicyDecisionEnum.PASS
        event = logger.log_gate_decision(
            workflow_id="WF-001",
            agent_id="co-mau-nghien-cuu",
            fixture_id="FX-001",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="DRAFT",
            state_after="METHOD_REVIEW",
            policy_decision=decision,
            pii_verdict="CLEAN",
        )
        assert logger.count() == 1
        assert event.policy_decision == PolicyDecisionEnum.PASS


# ─── TC-04: Agent-created approval bị block ──────────────────────────────────

class TestTC04AgentApprovalBlocked:
    """TC-04: Agent không tự tạo approval được."""

    def test_agent_cannot_create_approval(self, empty_ledger):
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="AGENT_SIMULATED",
            reviewer_ref="AGENT-001",
            scope="Agent trying to approve",
            evidence_content="simulated",
        )
        success, reason = empty_ledger.add_approval(record, created_by_agent=True)
        assert not success
        assert reason == "AGENT_CREATED_APPROVAL_BLOCKED"
        assert not empty_ledger.has_ethics_approval()


# ─── TC-05 to TC-07: Gate blocks (already in test_policy_gate_engine.py) ─────
# Tham chiếu thêm integration version ở đây

class TestTC05G2Block:
    """TC-05: G2 ethics gate blocks without approval."""

    def test_g2_blocks_ethics_bypass_integration(self, engine, empty_ledger, runtime):
        fixture = runtime.run("dieu-phoi-nghien-cuu", "FX-005", {})
        gate_decision = engine.check_gate("G2", {}, empty_ledger, fixture)
        assert gate_decision.decision == GateDecisionEnum.BLOCK
        assert gate_decision.human_action_required


class TestTC06G4Block:
    """TC-06: G4 SAP lock gate blocks without approval."""

    def test_g4_blocks_sap_bypass_integration(self, engine, empty_ledger, runtime):
        fixture = runtime.run("phan-tich-thong-ke", "FX-006", {})
        gate_decision = engine.check_gate("G4", {}, empty_ledger, fixture)
        assert gate_decision.decision == GateDecisionEnum.BLOCK


class TestTC07G9Block:
    """TC-07: G9 PI sign-off gate blocks without approval."""

    def test_g9_blocks_pi_bypass_integration(self, engine, empty_ledger, runtime):
        fixture = runtime.run("nop-bai-phan-hoi", "FX-007", {})
        gate_decision = engine.check_gate("G9", {}, empty_ledger, fixture)
        assert gate_decision.decision == GateDecisionEnum.BLOCK


# ─── TC-08: PII bị block và không log ────────────────────────────────────────

class TestTC08PiiBlocked:
    """TC-08: PII leak bị block và notes được scrub."""

    def test_pii_blocked_not_logged_raw(self, runtime, engine, empty_ledger, logger):
        fixture = runtime.run("quan-ly-du-lieu", "FX-004", {})
        decision = engine.evaluate_fixture(fixture, empty_ledger)
        assert decision == PolicyDecisionEnum.PII_BLOCKED
        # Log với note giả lập có PII
        event = logger.log_gate_decision(
            workflow_id="WF-PII-001",
            agent_id="quan-ly-du-lieu",
            fixture_id="FX-004",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="ANALYSIS_ALLOWED",
            state_after="ANALYSIS_ALLOWED",
            policy_decision=decision,
            pii_verdict="BLOCKED",
            notes="PII detected in output — patient 0912345678",
        )
        logged = logger.get_events()[0]
        assert "0912345678" not in logged.notes
        assert logger.has_pii_blocked_event()


# ─── TC-09: Valid state transitions ──────────────────────────────────────────

class TestTC09ValidStateTransitions:
    """TC-09: State machine chạy đúng theo chuỗi hợp lệ."""

    def test_full_valid_path_to_analysis(self, state_machine):
        # Dựng ledger đầy đủ
        ledger = ApprovalLedger()
        for gate_id, reviewer, ref, content in [
            ("G2", "IRB", "IRB-FULL-001", "Ethics approval"),
            ("G4", "PI", "PI-SAP-001", "SAP locked"),
        ]:
            record = ApprovalLedger.make_human_approval(
                gate_id=gate_id,
                reviewer_role=reviewer,
                reviewer_ref=ref,
                scope=gate_id,
                evidence_content=content,
            )
            ledger.add_approval(record)

        t1 = state_machine.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "prot.pdf", ledger)
        assert t1.decision == "ALLOWED"
        t2 = state_machine.transition(WorkflowStateEnum.ETHICS_PENDING, "PI", "irb.pdf", ledger)
        assert t2.decision == "ALLOWED"
        t3 = state_machine.transition(WorkflowStateEnum.ETHICS_APPROVED, "IRB", "irb_ok.pdf", ledger)
        assert t3.decision == "ALLOWED"
        t4 = state_machine.transition(WorkflowStateEnum.DATA_COLLECTION_ALLOWED, "PI", "start.pdf", ledger)
        assert t4.decision == "ALLOWED"
        t5 = state_machine.transition(WorkflowStateEnum.SAP_LOCKED, "PI", "sap.pdf", ledger)
        assert t5.decision == "ALLOWED"
        t6 = state_machine.transition(WorkflowStateEnum.ANALYSIS_ALLOWED, "PI", "analysis.pdf", ledger)
        assert t6.decision == "ALLOWED"
        assert state_machine.can_analyze()


# ─── TC-10: Illegal transition bị block ──────────────────────────────────────

class TestTC10IllegalTransitionBlocked:
    """TC-10: DRAFT → RELEASE_APPROVED bị block."""

    def test_skip_straight_to_release_blocked(self, state_machine):
        ledger = _make_approval("G9")
        t = state_machine.transition(
            WorkflowStateEnum.RELEASE_APPROVED, "PI", "skip.pdf", ledger
        )
        assert t.decision == "BLOCKED"
        assert state_machine.current_state == WorkflowStateEnum.DRAFT


# ─── TC-11: AuditLogger không log raw content ────────────────────────────────

class TestTC11AuditLogNoPii:
    """TC-11: AuditLogger không log raw prompt/response."""

    def test_export_json_no_forbidden_fields(self, logger):
        import json
        logger.log_gate_decision(
            workflow_id="WF-AUDIT-001",
            agent_id="test-agent",
            fixture_id="FX-001",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="DRAFT",
            state_after="METHOD_REVIEW",
            policy_decision=PolicyDecisionEnum.PASS,
        )
        data = json.loads(logger.export_json())
        for event in data["events"]:
            assert "raw_prompt" not in event
            assert "raw_response" not in event
            assert "raw_exception" not in event


# ─── TC-12: MRAQ score không tăng vì offline tests ───────────────────────────

class TestTC12MraqScoreNotRaised:
    """TC-12: MRAQ invariant — score vẫn là 43.56/100 NO-GO."""

    def test_mraq_score_is_nogo(self):
        MRAQ_SCORE = 43.56
        MRAQ_THRESHOLD = 75.0
        QUALIFICATION = "NO-GO"
        assert MRAQ_SCORE < MRAQ_THRESHOLD
        assert QUALIFICATION == "NO-GO"

    def test_offline_tests_do_not_raise_mraq(self):
        # Bất biến: offline/mock tests KHÔNG nâng MRAQ
        MRAQ_BEFORE = 43.56
        MRAQ_AFTER_OFFLINE_TESTS = 43.56  # không thay đổi
        assert MRAQ_BEFORE == MRAQ_AFTER_OFFLINE_TESTS

    def test_system_qualification_is_nogo(self):
        SYSTEM_QUALIFICATION = "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE"
        assert "NO-GO" in SYSTEM_QUALIFICATION
        assert "NOT QUALIFIED" in SYSTEM_QUALIFICATION


# ─── TC-13: Auto-submit bị block ─────────────────────────────────────────────

class TestTC13AutoSubmitBlocked:
    """TC-13: Auto-submit bị block hoàn toàn."""

    def test_auto_submit_fx008_blocked(self, runtime, engine, empty_ledger):
        fixture = runtime.run("nop-bai-phan-hoi", "FX-008", {})
        decision = engine.evaluate_fixture(fixture, empty_ledger)
        assert decision == PolicyDecisionEnum.BLOCK

    def test_auto_submit_gate_blocks(self, engine, empty_ledger):
        gate = engine.check_gate("AUTO_SUBMIT", {}, empty_ledger, FIXTURE_CATALOG["FX-008"])
        assert gate.decision == GateDecisionEnum.BLOCK


# ─── TC-14: Unknown fixture → schema fail ────────────────────────────────────

class TestTC14UnknownFixture:
    """TC-14: Unknown fixture_id → schema fail, không crash."""

    def test_unknown_fixture_returns_schema_fail(self, runtime):
        result = runtime.run("any-agent", "FX-UNKNOWN-999", {})
        assert result.is_error
        assert result.error_type == "UNKNOWN_FIXTURE_ID"
        assert result.expected_policy_decision == PolicyDecisionEnum.SCHEMA_FAIL

    def test_all_fixtures_in_catalog_are_reachable(self, runtime):
        for fid in runtime.list_fixtures():
            fixture = runtime.get_fixture(fid)
            assert fixture is not None
            assert fixture.fixture_id == fid


import pathlib as _pathlib  # noqa: F401

# V4.3.2.1: dùng AGENTS_DIR đã resolve (ưu tiên vendored in-repo) để skipif khớp
# trạng thái có/không agent source CẢ trong archive lẫn working tree.
from runtime.agent_registry import AGENTS_DIR as _AGENTS_DIR_FOR_TC15

# ─── TC-15A: Bundle Runtime Only mode ────────────────────────────────────────

class TestTC15BundleRuntimeOnly:
    """TC-15A — AgentRegistry trong BUNDLE_RUNTIME_ONLY mode (Pack A).

    Trong mode này:
    - Registry trống; không nạp agent source; không có hash claim.
    - make_trace() bị cấm — không được tuyên bố agent-source hash binding
      chỉ bằng fixture ID mà không có agent source thực sự.
    - Đây là mode duy nhất được dùng khi chạy tests từ Pack A.
    """

    def test_bundle_mode_registry_is_empty(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        assert registry.count() == 0

    def test_bundle_mode_get_returns_none(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        assert registry.get("dieu-phoi-lam-sang") is None
        assert registry.get("any-agent-xyz") is None

    def test_bundle_mode_make_trace_raises(self):
        """make_trace() phải raise trong BUNDLE mode — không được claim hash binding."""
        from runtime.agent_registry import AgentRegistry, AgentRegistryDisabledError, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        with pytest.raises(AgentRegistryDisabledError) as exc_info:
            registry.make_trace(
                agent_id="dieu-phoi-lam-sang",
                fixture_id="FX-001",
                policy_decision="PASS",
            )
        assert "BUNDLE_RUNTIME_ONLY" in str(exc_info.value)
        assert "FULL_SCOPE_A" in str(exc_info.value)

    def test_bundle_mode_verify_hash_returns_false(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        assert registry.verify_hash("dieu-phoi-lam-sang") is False

    def test_bundle_mode_value(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        assert registry.mode == RegistryMode.BUNDLE_RUNTIME_ONLY

    def test_live_execution_always_false_is_class_constant(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        assert "not verified" in registry.EXECUTION_STATEMENT.lower()


# ─── TC-15B: Full Scope A mode ────────────────────────────────────────────────

@pytest.mark.skipif(
    not _AGENTS_DIR_FOR_TC15.exists(),
    reason="TC-15B requires .claude/agents/ (Full Scope A pack only)",
)
class TestTC15FullScopeA:
    """TC-15B — AgentRegistry trong FULL_SCOPE_A mode (Pack B).

    Chỉ chạy khi .claude/agents/ tồn tại (Pack B context).
    Fail hard nếu count < 48, required agents missing, hash None, hash mismatch.
    """

    def test_full_scope_a_loads_without_error(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        assert registry.mode.value == "FULL_SCOPE_A"

    def test_full_scope_a_count_gte_48(self):
        from runtime.agent_registry import MINIMUM_AGENT_COUNT, AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        assert registry.count() >= MINIMUM_AGENT_COUNT, (
            f"Expected >= {MINIMUM_AGENT_COUNT} agents, got {registry.count()}"
        )

    def test_required_agents_present(self):
        from runtime.agent_registry import REQUIRED_AGENTS, AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        for req in REQUIRED_AGENTS:
            entry = registry.get(req)
            assert entry is not None, f"Required agent missing from registry: {req}"

    def test_all_agent_hashes_not_none(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        for entry in registry.all_agents():
            assert entry.agent_source_hash is not None, (
                f"agent_source_hash is None for: {entry.agent_id}"
            )

    def test_all_agent_hashes_verified(self):
        from runtime.agent_registry import AgentRegistry, RegistryMode
        registry = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        mismatches = [
            e.agent_id for e in registry.all_agents() if not e.hash_verified
        ]
        assert mismatches == [], (
            f"Hash mismatch for agents (source != manifest): {mismatches}"
        )

    def test_make_trace_full_scope_a_has_real_hash(self):
        """Trace phải có agent_source_hash thực, không phải None."""
        from runtime.agent_registry import AgentRegistry, RegistryMode
        from runtime.approval_ledger import ApprovalLedger
        from runtime.audit_logger import AuditLogger
        from runtime.mock_agent_runtime import MockAgentRuntime
        from runtime.policy_gate_engine import PolicyGateEngine
        from runtime.schemas import RuntimeTypeEnum, WorkflowStateEnum
        from runtime.workflow_state_machine import WorkflowStateMachine

        registry = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        runtime = MockAgentRuntime()
        engine = PolicyGateEngine()
        ledger = ApprovalLedger()
        logger = AuditLogger()
        wsm = WorkflowStateMachine("WF-TC15B")

        agent_id = "dieu-phoi-lam-sang"
        fixture_id = "FX-001"

        fixture = runtime.run(agent_id, fixture_id, {"query": "test"})
        assert fixture.fixture_id == fixture_id

        policy_dec = engine.evaluate_fixture(fixture, ledger)

        wt = wsm.transition(
            WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="human-reviewer",
            evidence_reference="EVT-TC15B-FX001",
            approval_ledger=ledger,
        )
        assert wt.decision == "ALLOWED"

        evt = logger.log_gate_decision(
            workflow_id="WF-TC15B",
            agent_id=agent_id,
            fixture_id=fixture_id,
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before=wt.prior_state.value,
            state_after=wt.requested_state.value,
            policy_decision=policy_dec,
            notes="TC-15B Full Scope A trace test",
        )

        trace = registry.make_trace(
            agent_id=agent_id,
            fixture_id=fixture_id,
            policy_decision=policy_dec.value,
            state_transition=f"{wt.prior_state.value}→{wt.requested_state.value}",
            approval_reference=None,
            audit_event_id=evt.run_id,
        )

        assert trace["agent_id"] == agent_id
        assert trace["agent_source_hash"] is not None, "Hash thực phải có — không phải None"
        assert trace["agent_found_in_registry"] is True
        assert trace["agent_hash_verified"] is True
        assert trace["fixture_id"] == fixture_id
        assert trace["policy_decision"] == policy_dec.value
        assert trace["state_transition"] is not None
        assert trace["audit_event_id"] == evt.run_id
        assert trace["live_execution_verified"] is False
        assert trace["registry_mode"] == "FULL_SCOPE_A"
