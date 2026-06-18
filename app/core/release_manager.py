"""Release manager cho V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from uuid import uuid4

from app.core.approval_service import ApprovalItem, ReviewStatus
from app.core.policy_engine import PolicyDecision, PolicyEngine


@dataclass(frozen=True)
class ReleaseRecord:
    release_id: str
    run_id: str
    channel: str
    payload_hash: str
    released_at: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


class ReleaseManager:
    def __init__(self, policy_engine: Optional[PolicyEngine] = None) -> None:
        self.policy_engine = policy_engine or PolicyEngine()

    def stage(self, run_id: str, channel: str, payload_hash: str) -> ReleaseRecord:
        return ReleaseRecord(
            release_id=f"rel_stage_{uuid4().hex}",
            run_id=run_id,
            channel=channel,
            payload_hash=payload_hash,
            released_at="",
            metadata={"status": "staged"},
        )

    def release(
        self,
        *,
        run_id: str,
        channel: str,
        payload_hash: str,
        approval: ApprovalItem,
        policy_context: Mapping[str, Any],
    ) -> ReleaseRecord:
        if approval.status is not ReviewStatus.APPROVED:
            raise PermissionError("Không phát hành khi chưa được duyệt")
        decision: PolicyDecision = self.policy_engine.evaluate(policy_context)
        decision.require_allowed()
        return ReleaseRecord(
            release_id=f"rel_{uuid4().hex}",
            run_id=run_id,
            channel=channel,
            payload_hash=payload_hash,
            released_at=datetime.now(timezone.utc).isoformat(),
            metadata={"approval_id": approval.approval_id, "status": "released"},
        )
