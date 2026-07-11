"""
Tests cho WorkflowStateMachine — Phase 3 Offline Controlled-System.
Không có API call, không PII, hoàn toàn deterministic.
"""

from runtime.approval_ledger import ApprovalLedger
from runtime.schemas import WorkflowStateEnum
from runtime.workflow_state_machine import WorkflowStateMachine


def _ledger_with_ethics() -> ApprovalLedger:
    ledger = ApprovalLedger()
    record = ApprovalLedger.make_human_approval(
        gate_id="G2",
        reviewer_role="IRB",
        reviewer_ref="IRB-TEST-G2",
        scope="Ethics approval",
        evidence_content="Ethics approval document",
    )
    ledger.add_approval(record)
    return ledger


def _ledger_with_ethics_and_sap() -> ApprovalLedger:
    ledger = _ledger_with_ethics()
    record = ApprovalLedger.make_human_approval(
        gate_id="G4",
        reviewer_role="PI",
        reviewer_ref="PI-SAP-LOCK-001",
        scope="SAP lock",
        evidence_content="SAP signed and locked",
    )
    ledger.add_approval(record)
    return ledger


def _ledger_with_all_gates() -> ApprovalLedger:
    ledger = _ledger_with_ethics_and_sap()
    record = ApprovalLedger.make_human_approval(
        gate_id="G9",
        reviewer_role="PI",
        reviewer_ref="PI-G9-001",
        scope="PI final sign-off",
        evidence_content="PI sign-off declaration",
    )
    ledger.add_approval(record)
    return ledger


class TestValidTransitions:
    """TC-09: Valid state transitions."""

    def test_draft_to_method_review(self):
        sm = WorkflowStateMachine("WF-001")
        ledger = ApprovalLedger()
        t = sm.transition(
            WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="PI",
            evidence_reference="protocol_v1.pdf",
            approval_ledger=ledger,
        )
        assert t.decision == "ALLOWED"
        assert sm.current_state == WorkflowStateEnum.METHOD_REVIEW

    def test_method_review_to_ethics_pending(self):
        sm = WorkflowStateMachine("WF-002")
        ledger = ApprovalLedger()
        sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "protocol.pdf", ledger)
        t = sm.transition(WorkflowStateEnum.ETHICS_PENDING, "PI", "irb_submission.pdf", ledger)
        assert t.decision == "ALLOWED"
        assert sm.current_state == WorkflowStateEnum.ETHICS_PENDING

    def test_ethics_pending_to_ethics_approved_with_g2(self):
        sm = WorkflowStateMachine("WF-003")
        ledger = _ledger_with_ethics()
        sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "protocol.pdf", ledger)
        sm.transition(WorkflowStateEnum.ETHICS_PENDING, "PI", "irb_submission.pdf", ledger)
        t = sm.transition(WorkflowStateEnum.ETHICS_APPROVED, "IRB", "irb_approval_letter.pdf", ledger)
        assert t.decision == "ALLOWED"

    def test_ethics_approved_to_data_collection(self):
        sm = WorkflowStateMachine("WF-004")
        ledger = _ledger_with_ethics()
        sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "p.pdf", ledger)
        sm.transition(WorkflowStateEnum.ETHICS_PENDING, "PI", "s.pdf", ledger)
        sm.transition(WorkflowStateEnum.ETHICS_APPROVED, "IRB", "a.pdf", ledger)
        t = sm.transition(WorkflowStateEnum.DATA_COLLECTION_ALLOWED, "PI", "data_start.pdf", ledger)
        assert t.decision == "ALLOWED"
        assert sm.can_collect_data()


class TestBlockedTransitions:
    """TC-10: Illegal transitions bị block."""

    def test_draft_to_analysis_blocked(self):
        sm = WorkflowStateMachine("WF-005")
        ledger = ApprovalLedger()
        t = sm.transition(WorkflowStateEnum.ANALYSIS_ALLOWED, "PI", "evidence.pdf", ledger)
        assert t.decision == "BLOCKED"
        assert "INVALID_TRANSITION" in t.reason
        # State không thay đổi
        assert sm.current_state == WorkflowStateEnum.DRAFT

    def test_draft_to_release_blocked(self):
        sm = WorkflowStateMachine("WF-006")
        ledger = _ledger_with_all_gates()
        t = sm.transition(WorkflowStateEnum.RELEASE_APPROVED, "PI", "final.pdf", ledger)
        assert t.decision == "BLOCKED"
        assert sm.current_state == WorkflowStateEnum.DRAFT

    def test_terminal_state_no_transition(self):
        sm = WorkflowStateMachine("WF-007", initial_state=WorkflowStateEnum.RELEASE_BLOCKED)
        ledger = _ledger_with_all_gates()
        t = sm.transition(WorkflowStateEnum.RELEASE_APPROVED, "PI", "doc.pdf", ledger)
        assert t.decision == "BLOCKED"
        assert sm.current_state == WorkflowStateEnum.RELEASE_BLOCKED


class TestGateRequirements:
    """Gates bắt buộc kiểm tra đúng."""

    def test_data_collection_requires_g2(self):
        sm = WorkflowStateMachine("WF-008")
        ledger = ApprovalLedger()  # không có G2
        # Advance to ETHICS_APPROVED manually
        sm._current_state = WorkflowStateEnum.ETHICS_APPROVED
        t = sm.transition(WorkflowStateEnum.DATA_COLLECTION_ALLOWED, "PI", "data.pdf", ledger)
        assert t.decision == "BLOCKED"
        assert "G2" in t.reason

    def test_analysis_requires_g4(self):
        sm = WorkflowStateMachine("WF-009")
        ledger = _ledger_with_ethics()  # có G2 nhưng không có G4
        sm._current_state = WorkflowStateEnum.SAP_LOCKED
        t = sm.transition(WorkflowStateEnum.ANALYSIS_ALLOWED, "PI", "analysis.pdf", ledger)
        assert t.decision == "BLOCKED"
        assert "G4" in t.reason

    def test_release_approved_requires_g9(self):
        sm = WorkflowStateMachine("WF-010")
        ledger = _ledger_with_ethics_and_sap()  # G2+G4 nhưng không có G9
        sm._current_state = WorkflowStateEnum.PI_REVIEW_REQUIRED
        t = sm.transition(WorkflowStateEnum.RELEASE_APPROVED, "PI", "final.pdf", ledger)
        assert t.decision == "BLOCKED"
        assert "G9" in t.reason


class TestMissingEvidenceReference:
    """Evidence reference rỗng bị block."""

    def test_empty_evidence_reference_blocked(self):
        sm = WorkflowStateMachine("WF-011")
        ledger = ApprovalLedger()
        t = sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "", ledger)
        assert t.decision == "BLOCKED"
        assert t.reason == "MISSING_EVIDENCE_REFERENCE"

    def test_none_string_evidence_blocked(self):
        sm = WorkflowStateMachine("WF-012")
        ledger = ApprovalLedger()
        t = sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "none", ledger)
        assert t.decision == "BLOCKED"


class TestStateMachineHistory:
    """History ghi lại đầy đủ."""

    def test_history_grows(self):
        sm = WorkflowStateMachine("WF-013")
        ledger = ApprovalLedger()
        sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "doc.pdf", ledger)
        sm.transition(WorkflowStateEnum.DRAFT, "PI", "revised.pdf", ledger)  # back allowed
        assert len(sm.history) == 2

    def test_reset_clears_history(self):
        sm = WorkflowStateMachine("WF-014")
        ledger = ApprovalLedger()
        sm.transition(WorkflowStateEnum.METHOD_REVIEW, "PI", "doc.pdf", ledger)
        sm.reset()
        assert len(sm.history) == 0
        assert sm.current_state == WorkflowStateEnum.DRAFT
