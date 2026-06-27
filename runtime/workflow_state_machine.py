"""
WorkflowStateMachine — State machine cho research workflow.
Không cho phép nhảy state sai. Mọi transition cần authorization.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from .schemas import WorkflowStateEnum, WorkflowTransition
from .approval_ledger import ApprovalLedger

# ─── Valid transitions ────────────────────────────────────────────────────────

# Từ state → set các states hợp lệ có thể chuyển đến
VALID_TRANSITIONS: dict[WorkflowStateEnum, set[WorkflowStateEnum]] = {
    WorkflowStateEnum.DRAFT: {
        WorkflowStateEnum.METHOD_REVIEW,
    },
    WorkflowStateEnum.METHOD_REVIEW: {
        WorkflowStateEnum.ETHICS_PENDING,
        WorkflowStateEnum.DRAFT,  # quay lại nếu method cần sửa
    },
    WorkflowStateEnum.ETHICS_PENDING: {
        WorkflowStateEnum.ETHICS_APPROVED,
        WorkflowStateEnum.METHOD_REVIEW,  # rejected → revise
    },
    WorkflowStateEnum.ETHICS_APPROVED: {
        WorkflowStateEnum.DATA_COLLECTION_ALLOWED,
    },
    WorkflowStateEnum.DATA_COLLECTION_ALLOWED: {
        WorkflowStateEnum.SAP_LOCKED,
    },
    WorkflowStateEnum.SAP_LOCKED: {
        WorkflowStateEnum.ANALYSIS_ALLOWED,
    },
    WorkflowStateEnum.ANALYSIS_ALLOWED: {
        WorkflowStateEnum.PI_REVIEW_REQUIRED,
    },
    WorkflowStateEnum.PI_REVIEW_REQUIRED: {
        WorkflowStateEnum.RELEASE_BLOCKED,
        WorkflowStateEnum.RELEASE_APPROVED,
    },
    # Terminal states — không transition tiếp
    WorkflowStateEnum.RELEASE_BLOCKED: set(),
    WorkflowStateEnum.RELEASE_APPROVED: set(),
}

# Gate bắt buộc trước khi cho phép một transition
REQUIRED_GATE_FOR_TRANSITION: dict[WorkflowStateEnum, str] = {
    WorkflowStateEnum.DATA_COLLECTION_ALLOWED: "G2",  # ethics approval
    WorkflowStateEnum.ANALYSIS_ALLOWED: "G4",          # SAP locked
    WorkflowStateEnum.RELEASE_APPROVED: "G9",          # PI sign-off
}


class WorkflowStateMachine:
    """
    State machine cho research workflow G0–G9.
    Không cho phép skip state hoặc tự-approve.
    """

    def __init__(
        self,
        workflow_id: str,
        initial_state: WorkflowStateEnum = WorkflowStateEnum.DRAFT,
    ):
        self.workflow_id = workflow_id
        self._current_state = initial_state
        self._history: list[WorkflowTransition] = []

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def current_state(self) -> WorkflowStateEnum:
        return self._current_state

    @property
    def history(self) -> list[WorkflowTransition]:
        return list(self._history)

    # ── Transition ────────────────────────────────────────────────────────────

    def transition(
        self,
        requested_state: WorkflowStateEnum,
        authorized_by: str,
        evidence_reference: str,
        approval_ledger: ApprovalLedger,
    ) -> WorkflowTransition:
        """
        Thử chuyển sang requested_state.
        Trả WorkflowTransition với decision ALLOWED hoặc BLOCKED.
        """
        prior_state = self._current_state
        ts = datetime.now(timezone.utc).isoformat()

        # 1. Kiểm tra transition hợp lệ
        allowed_targets = VALID_TRANSITIONS.get(prior_state, set())
        if requested_state not in allowed_targets:
            t = WorkflowTransition(
                prior_state=prior_state,
                requested_state=requested_state,
                authorized_by=authorized_by,
                evidence_reference=evidence_reference,
                decision="BLOCKED",
                reason=f"INVALID_TRANSITION:{prior_state.value}→{requested_state.value}",
                timestamp_utc=ts,
            )
            self._history.append(t)
            return t

        # 2. Kiểm tra required gate
        required_gate = REQUIRED_GATE_FOR_TRANSITION.get(requested_state)
        if required_gate:
            approval = approval_ledger.check_has_approval(required_gate)
            if approval is None:
                t = WorkflowTransition(
                    prior_state=prior_state,
                    requested_state=requested_state,
                    authorized_by=authorized_by,
                    evidence_reference=evidence_reference,
                    decision="BLOCKED",
                    reason=f"GATE_NOT_APPROVED:{required_gate}",
                    timestamp_utc=ts,
                )
                self._history.append(t)
                return t

        # 3. Kiểm tra evidence_reference không rỗng
        if not evidence_reference or evidence_reference.strip() in ("", "none"):
            t = WorkflowTransition(
                prior_state=prior_state,
                requested_state=requested_state,
                authorized_by=authorized_by,
                evidence_reference=evidence_reference,
                decision="BLOCKED",
                reason="MISSING_EVIDENCE_REFERENCE",
                timestamp_utc=ts,
            )
            self._history.append(t)
            return t

        # 4. Transition hợp lệ — cập nhật state
        self._current_state = requested_state
        t = WorkflowTransition(
            prior_state=prior_state,
            requested_state=requested_state,
            authorized_by=authorized_by,
            evidence_reference=evidence_reference,
            decision="ALLOWED",
            reason="OK",
            timestamp_utc=ts,
        )
        self._history.append(t)
        return t

    def can_collect_data(self) -> bool:
        return self._current_state in (
            WorkflowStateEnum.DATA_COLLECTION_ALLOWED,
            WorkflowStateEnum.SAP_LOCKED,
            WorkflowStateEnum.ANALYSIS_ALLOWED,
            WorkflowStateEnum.PI_REVIEW_REQUIRED,
            WorkflowStateEnum.RELEASE_APPROVED,
        )

    def can_analyze(self) -> bool:
        return self._current_state in (
            WorkflowStateEnum.ANALYSIS_ALLOWED,
            WorkflowStateEnum.PI_REVIEW_REQUIRED,
        )

    def can_release(self) -> bool:
        return self._current_state == WorkflowStateEnum.RELEASE_APPROVED

    def reset(self, initial_state: WorkflowStateEnum = WorkflowStateEnum.DRAFT) -> None:
        """Reset state machine về trạng thái ban đầu (chỉ dùng trong tests)."""
        self._current_state = initial_state
        self._history.clear()
