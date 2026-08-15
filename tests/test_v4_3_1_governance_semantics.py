"""
V4.3.1 — Research governance semantic correction tests.

Phân tách 4 mức: DRAFT_CREATION (không cần G2/G4/G9) · GOVERNANCE_LOCK ·
REAL_RESEARCH_EXECUTION (luôn BLOCK) · EXTERNAL_RELEASE (luôn BLOCK).

KHÔNG API/network/PII/dữ liệu thật/eHospital. Qualification NO-GO.
"""

from __future__ import annotations

import pytest

from research_studio.artifact_registry import ArtifactRegistry
from research_studio.capability_profile import (
    HIGH_RISK_AGENTS,
    ExternalActionType,
    check_external_action,
    detect_external_action,
    get_profile,
)
from research_studio.governance import (
    BlockedRealState,
    DraftStateMachine,
    DraftWorkflowState,
    GovernanceLevel,
    attempt_external_release,
    attempt_real_analysis,
    attempt_real_data_collection,
    is_real_or_release_state,
)
from research_studio.project_schema import ResearchProject, StudyType
from research_studio.research_quality_checks import ResearchGateDecision
from research_studio.research_workflow import (
    WP_BY_ID,
    build_draft_mode_registry,
    build_research_runtime,
    run_project,
    run_work_package,
)
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.dispatch_guard import reset_guard_context


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


def _project(study_type=StudyType.RCT, pid="RS-G-001"):
    return ResearchProject(
        project_id=pid, title="[SYNTHETIC] gov", principal_investigator="PI-SYNTH-G",
        research_domain="test", study_type=study_type,
        clinical_question="Q?", pico_or_equivalent={"P": "x", "O": "y"},
        objectives=["o"], outcomes=["outcome-A"],
    )


def _harness():
    return (build_draft_mode_registry(), ApprovalLedger(), build_research_runtime(),
            AuditLogger(run_id="A-G"), ArtifactRegistry())


# ── Mức A: DRAFT không cần G2/G4/G9 (ledger RỖNG) ─────────────────────────────

def test_protocol_draft_needs_no_g4():
    reg, ledger, rt, audit, arts = _harness()
    assert ledger.count() == 0  # KHÔNG có approval nào
    res = run_work_package(_project(), WP_BY_ID["WP-02"], reg, ledger, rt, audit, arts)
    assert res.decision == ResearchGateDecision.PASS
    assert res.artifact is not None
    assert res.artifact.artifact_type == "PROTOCOL_DRAFT"
    assert res.artifact.governance_level == "DRAFT_CREATION"


def test_sap_draft_needs_no_g4():
    reg, ledger, rt, audit, arts = _harness()
    res = run_work_package(_project(), WP_BY_ID["WP-06"], reg, ledger, rt, audit, arts)
    assert res.decision == ResearchGateDecision.PASS
    assert res.artifact.artifact_type == "SAP_DRAFT"


def test_manuscript_outline_needs_no_g9():
    reg, ledger, rt, audit, arts = _harness()
    res = run_work_package(_project(), WP_BY_ID["WP-08"], reg, ledger, rt, audit, arts)
    assert res.decision == ResearchGateDecision.PASS
    assert res.artifact.artifact_type == "MANUSCRIPT_OUTLINE_DRAFT"


def test_all_draft_outputs_draft_only_and_human_review():
    p = _project(study_type=StudyType.COHORT, pid="RS-G-COH")
    res = run_project(p)
    assert not res.blocked and res.artifacts
    for a in res.artifacts:
        assert a.draft_only is True
        assert a.human_review_required is True
        assert a.governance_level == "DRAFT_CREATION"


# ── Mức C: REAL_RESEARCH_EXECUTION luôn BLOCK ─────────────────────────────────

def test_real_data_collection_without_g2_blocks():
    d = attempt_real_data_collection(has_g2_real=False)
    assert d.decision == "BLOCKED"
    assert d.level == GovernanceLevel.REAL_RESEARCH_EXECUTION
    assert "REAL_RESEARCH_EXECUTION_BLOCKED_V4_3_1" in d.reason_code
    assert "G2_REAL_ETHICS_NOT_PRESENT" in d.reason_code


def test_real_data_collection_blocks_even_with_g2():
    # Ngay cả khi có điều kiện-trước G2, V4.3.1 vẫn BLOCK thực thi thật.
    assert attempt_real_data_collection(has_g2_real=True).decision == "BLOCKED"


def test_real_analysis_without_sap_lock_blocks():
    d = attempt_real_analysis(has_sap_lock_real=False)
    assert d.decision == "BLOCKED"
    assert "SAP_LOCK_REAL_NOT_PRESENT" in d.reason_code


# ── Mức D: EXTERNAL_RELEASE luôn BLOCK ────────────────────────────────────────

def test_external_release_without_g9_blocks():
    d = attempt_external_release(has_g9_real=False)
    assert d.decision == "BLOCKED"
    assert d.level == GovernanceLevel.EXTERNAL_RELEASE
    assert "G9_REAL_SIGNOFF_NOT_PRESENT" in d.reason_code


# ── Capability boundary cho 3 agent dễ gây hiểu nhầm ──────────────────────────

@pytest.mark.parametrize("agent_id", list(HIGH_RISK_AGENTS))
def test_high_risk_agent_profile_forbids_external(agent_id):
    p = get_profile(agent_id)
    assert p.draft_only and p.external_actions_forbidden
    assert p.auto_submit_forbidden and p.real_data_forbidden and p.human_review_required


@pytest.mark.parametrize("agent_id", list(HIGH_RISK_AGENTS))
@pytest.mark.parametrize("action", list(ExternalActionType))
def test_agent_external_action_blocked(agent_id, action):
    r = check_external_action(agent_id, action)
    assert r.allowed is False
    assert "FORBIDDEN_V4_3_1" in r.reason_code


def test_submit_and_ethics_registration_blocked():
    assert check_external_action("nop-bai-phan-hoi", ExternalActionType.SUBMIT).allowed is False
    assert check_external_action("dao-duc-dang-ky", ExternalActionType.ETHICS_REGISTRATION).allowed is False


# ── Synthetic analysis dùng real-data marker → BLOCK ──────────────────────────

def test_synthetic_analysis_real_data_marker_blocks():
    reg, ledger, rt, audit, arts = _harness()
    res = run_work_package(_project(), WP_BY_ID["WP-07"], reg, ledger, rt, audit, arts,
                           fixture_override="RWP-REAL")
    assert res.decision == ResearchGateDecision.BLOCK
    assert res.artifact is None
    assert "CAPABILITY_BLOCKED" in (res.reason_code or "") or "REAL_DATA" in (res.reason_code or "")


def test_detect_external_action_markers():
    assert detect_external_action({"x": "AUTO_SUBMIT to journal"})[0] is True
    assert detect_external_action({"x": "ETHICS_REGISTER now"})[0] is True
    assert detect_external_action({"x": "REAL_PATIENT_DATA"})[0] is True
    assert detect_external_action({"x": "clean synthetic draft"})[0] is False


# ── State machine: chặn state thật/release, cho draft tuyến tính ───────────────

@pytest.mark.parametrize("blocked_state", list(BlockedRealState))
def test_state_machine_blocks_all_real_states(blocked_state):
    sm = DraftStateMachine()
    t = sm.request(blocked_state)
    assert t.decision == "BLOCKED"
    assert "REAL_OR_RELEASE_STATE_BLOCKED_V4_3_1" in t.reason_code
    assert is_real_or_release_state(blocked_state.value)


def test_state_machine_linear_draft_ok():
    sm = DraftStateMachine()
    assert sm.request(DraftWorkflowState.PROTOCOL_DRAFT).decision == "ALLOWED"
    assert sm.request(DraftWorkflowState.EVIDENCE_PLAN_DRAFT).decision == "ALLOWED"
    # nhảy cóc bị chặn
    assert sm.request(DraftWorkflowState.MANUSCRIPT_DRAFT).decision == "BLOCKED"


def test_full_draft_sequence_reaches_complete():
    sm = DraftStateMachine()
    for s in [DraftWorkflowState.PROTOCOL_DRAFT, DraftWorkflowState.EVIDENCE_PLAN_DRAFT,
              DraftWorkflowState.METHODS_DRAFT, DraftWorkflowState.CRF_DRAFT,
              DraftWorkflowState.SAP_DRAFT, DraftWorkflowState.SYNTHETIC_ANALYSIS_READY,
              DraftWorkflowState.MANUSCRIPT_DRAFT, DraftWorkflowState.GOVERNANCE_DRAFT,
              DraftWorkflowState.DRAFT_COMPLETE]:
        assert sm.request(s).decision == "ALLOWED"
    assert sm.state == DraftWorkflowState.DRAFT_COMPLETE
