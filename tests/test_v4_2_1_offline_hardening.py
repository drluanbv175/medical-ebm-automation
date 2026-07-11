"""
V4.2.1 Offline Hardening Tests.

Đóng và kiểm chứng (offline, deterministic, synthetic):
  - GAP-001: REQUIRED_AGENTS hard-enforce đủ 4 agent trọng yếu → fail-closed.
  - GAP-004: agent_source_hash bắt buộc trong audit event của mọi dispatch.
  - GAP-009: manifest hiệu lực nằm IN-REPO + self-check hash.

KHÔNG gọi API. KHÔNG network. KHÔNG PII. KHÔNG dùng DB thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
"""

from __future__ import annotations

import pytest

import runtime.agent_registry as ar
from runtime.agent_registry import (
    AgentRegistry,
    AgentRegistryEntry,
    AgentRegistryIntegrityError,
    AgentManifestSelfCheckError,
    RegistryMode,
    REQUIRED_AGENTS,
    MINIMUM_AGENT_COUNT,
    from_entries_for_testing,
    reset_registry,
)
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.controlled_orchestrator import ControlledOrchestrator
from runtime.dispatch_guard import reset_guard_context
from runtime.mock_agent_runtime import MockAgentRuntime
from runtime.schemas import PolicyDecisionEnum, RuntimeTypeEnum, WorkflowStateEnum
from runtime.workflow_context import WorkflowContext
from runtime.workflow_state_machine import WorkflowStateMachine


# ── Helpers ──────────────────────────────────────────────────────────────────

def _entry(agent_id, *, source_hash="abc123dead", hash_verified=True, policy_deps=None):
    return AgentRegistryEntry(
        agent_id=agent_id,
        agent_path=f".claude/agents/{agent_id}.md",
        agent_source_hash=source_hash,
        policy_dependencies=policy_deps or ["PII_EGRESS"],
        allowed_runtime="MOCK_ONLY",
        source_file_exists=True,
        hash_verified=hash_verified,
    )


def _orchestrator(entries):
    registry = from_entries_for_testing(entries)
    logger = AuditLogger(run_id="AUDIT-HARDEN")
    orch = ControlledOrchestrator(
        registry=registry,
        ledger=ApprovalLedger(),
        mock_runtime=MockAgentRuntime(),
        state_machine=WorkflowStateMachine(workflow_id="WF-HARDEN"),
        audit_logger=logger,
    )
    return orch, logger


def _ctx(agent_id, fixture_id):
    return WorkflowContext.create(
        workflow_id="WF-HARDEN",
        agent_id=agent_id,
        fixture_id=fixture_id,
        state_before=WorkflowStateEnum.DRAFT.value,
    )


def setup_function():
    reset_registry()
    reset_guard_context()


def teardown_function():
    reset_registry()
    reset_guard_context()


# ── GAP-001: REQUIRED_AGENTS đủ 4 + fail-closed ───────────────────────────────

class TestGap001RequiredAgents:
    REQUIRED_4 = {
        "dieu-phoi-nghien-cuu",
        "dieu-phoi-lam-sang",
        "tham-dinh-dau-ra",
        "so-cai-ghi-nho",
    }

    def test_required_set_contains_all_four(self):
        assert self.REQUIRED_4.issubset(set(REQUIRED_AGENTS))

    def test_full_scope_a_has_all_required(self):
        """FULL_SCOPE_A nạp thực: cả 4 agent trọng yếu present + hash-verified."""
        reg = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        for aid in self.REQUIRED_4:
            e = reg.get(aid)
            assert e is not None, f"required agent missing: {aid}"
            assert e.hash_verified is True

    @pytest.mark.parametrize("missing", sorted(REQUIRED_4))
    def test_fail_closed_when_any_required_missing(self, missing):
        """Thiếu BẤT KỲ required agent nào (dù count>=48) → fail-closed."""
        ids = [f"filler-{i}" for i in range(MINIMUM_AGENT_COUNT)]
        # đảm bảo đủ 4 required rồi loại 1
        present = (self.REQUIRED_4 - {missing})
        entries = [_entry(a) for a in present]
        # bù filler cho đủ >= MINIMUM_AGENT_COUNT
        for i in ids:
            entries.append(_entry(i))
        reg = AgentRegistry.__new__(AgentRegistry)
        reg._mode = RegistryMode.FULL_SCOPE_A
        reg._entries = {e.agent_id: e for e in entries}
        reg._manifest_sha256_map = {}
        assert reg.count() >= MINIMUM_AGENT_COUNT
        with pytest.raises(AgentRegistryIntegrityError) as exc:
            reg._validate_full_scope_a()
        assert missing in str(exc.value)


# ── GAP-004: agent_source_hash trong audit event của mọi dispatch ─────────────

class TestGap004AuditHash:
    def test_pass_dispatch_audit_has_agent_hash(self):
        orch, logger = _orchestrator([_entry("co-mau-nghien-cuu", source_hash="HASHPASS01")])
        result = orch.run(_ctx("co-mau-nghien-cuu", "FX-001"))
        assert result.policy_decision == PolicyDecisionEnum.PASS
        assert result.audit_event is not None
        assert result.audit_event.agent_source_hash == "HASHPASS01"
        assert logger.all_dispatch_events_hashed() is True

    def test_block_at_dispatch_still_has_agent_hash(self):
        """Fixture FABRICATED → policy BLOCK nhưng vẫn dispatch → audit có hash."""
        orch, logger = _orchestrator([_entry("tra-cuu-chung-cu", source_hash="HASHBLK02")])
        result = orch.run(_ctx("tra-cuu-chung-cu", "FX-002"))
        assert result.policy_decision == PolicyDecisionEnum.BLOCK
        assert result.audit_event is not None
        assert result.audit_event.agent_source_hash == "HASHBLK02"
        assert logger.all_dispatch_events_hashed() is True

    def test_fail_closed_when_hash_empty_at_audit(self):
        """Hash rỗng lọt tới bước audit → BLOCK, KHÔNG ghi audit event."""
        orch, logger = _orchestrator(
            [_entry("tra-cuu-chung-cu", source_hash="", hash_verified=True)]
        )
        result = orch.run(_ctx("tra-cuu-chung-cu", "FX-001"))
        assert result.blocked is True
        assert "AGENT_HASH_MISSING_AT_AUDIT" in (result.reason_code or "")
        assert result.audit_event is None
        # Không có dispatch event nào được ghi (fail-closed trước audit).
        assert logger.count() == 0

    def test_audit_logger_flags_unhashed_dispatch_event(self):
        """Validator: dispatch event thiếu hash bị gắn cờ; có hash thì sạch."""
        logger = AuditLogger(run_id="A1")
        logger.log_gate_decision(
            workflow_id="W", agent_id="x", fixture_id="FX-001",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="DRAFT", state_after="DRAFT",
            policy_decision=PolicyDecisionEnum.PASS,
        )  # KHÔNG truyền agent_source_hash
        assert logger.all_dispatch_events_hashed() is False
        assert len(logger.dispatch_events_missing_hash()) == 1

        logger2 = AuditLogger(run_id="A2")
        logger2.log_gate_decision(
            workflow_id="W", agent_id="x", fixture_id="FX-001",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="DRAFT", state_after="DRAFT",
            policy_decision=PolicyDecisionEnum.PASS,
            agent_source_hash="DEADBEEF",
        )
        assert logger2.all_dispatch_events_hashed() is True

    def test_hash_survives_scrub_and_export(self):
        """agent_source_hash được giữ qua scrub PII + có trong export JSON."""
        logger = AuditLogger(run_id="A3")
        logger.log_gate_decision(
            workflow_id="W", agent_id="x", fixture_id="FX-001",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="DRAFT", state_after="DRAFT",
            policy_decision=PolicyDecisionEnum.PASS,
            notes="cccd 012345678901",  # kích hoạt scrub
            agent_source_hash="KEEPHASH99",
        )
        assert logger.get_events()[0].agent_source_hash == "KEEPHASH99"
        assert "KEEPHASH99" in logger.export_json()


# ── GAP-009: manifest in-repo + self-check ────────────────────────────────────

class TestGap009ManifestInRepo:
    def test_manifest_path_is_in_repo_not_onedrive(self):
        p = str(ar.SCOPE_A_MANIFEST_PATH)
        assert "runtime/manifests" in p.replace("\\", "/")
        assert "MRAQ100_AUDIT" not in p  # không còn phụ thuộc manifest ngoài repo

    def test_full_scope_a_loads_with_self_check(self):
        reg = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        assert reg.count() == MINIMUM_AGENT_COUNT
        assert all(e.hash_verified for e in reg.all_agents())

    def test_self_check_fails_closed_on_manifest_tamper(self, monkeypatch):
        """Đổi hằng self-check → mô phỏng manifest bị sửa → fail-closed."""
        monkeypatch.setattr(ar, "MANIFEST_SELF_CHECK_SHA256", "0" * 64)
        with pytest.raises(AgentManifestSelfCheckError):
            AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
