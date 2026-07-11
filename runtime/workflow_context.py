"""
WorkflowContext — ngữ cảnh bắt buộc cho mọi invocation qua ControlledOrchestrator.

Mỗi workflow run phải có đủ 10 field trace trước khi được coi là hoàn tất.
WorkflowContext không chứa PII và không gọi API.
"""

from __future__ import annotations

import dataclasses
import datetime
import uuid
from typing import Optional


def _utc_now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_run_id() -> str:
    return f"RUN-{uuid.uuid4().hex[:12].upper()}"


@dataclasses.dataclass
class WorkflowContext:
    """
    Ngữ cảnh đầy đủ của một lần chạy workflow offline có kiểm soát.

    Bất biến:
    - Mọi invocation qua ControlledOrchestrator phải mang WorkflowContext hợp lệ.
    - Mọi dispatch không có context bị block bởi DispatchGuard.
    - human_approval luôn False trong offline mode.
    - not_valid_for_real_research luôn True.
    """

    run_id: str
    workflow_id: str
    agent_id: str
    fixture_id: str
    state_before: str
    agent_source_hash: Optional[str] = None
    state_after: Optional[str] = None
    policy_decision: Optional[str] = None
    approval_reference: Optional[str] = None
    audit_event_id: Optional[str] = None
    timestamp_utc: str = dataclasses.field(default_factory=_utc_now)
    approval_mode: str = "NONE"
    human_approval: bool = False
    not_valid_for_real_research: bool = True
    blocked_at_control: Optional[str] = None
    reason_code: Optional[str] = None
    _production_connector: bool = False
    _auto_submit: bool = False

    @classmethod
    def create(
        cls,
        workflow_id: str,
        agent_id: str,
        fixture_id: str,
        state_before: str,
        approval_mode: str = "NONE",
    ) -> "WorkflowContext":
        return cls(
            run_id=_new_run_id(),
            workflow_id=workflow_id,
            agent_id=agent_id,
            fixture_id=fixture_id,
            state_before=state_before,
            timestamp_utc=_utc_now(),
            approval_mode=approval_mode,
        )

    def is_trace_complete(self) -> bool:
        """True khi đủ 10 field trace bắt buộc."""
        return all([
            self.run_id,
            self.workflow_id,
            self.agent_id,
            self.agent_source_hash,
            self.fixture_id,
            self.state_before,
            self.state_after is not None,
            self.policy_decision is not None,
            self.audit_event_id is not None,
            self.timestamp_utc,
        ])

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        # Loại các field nội bộ có tiền tố _
        return {k: v for k, v in d.items() if not k.startswith("_")}
