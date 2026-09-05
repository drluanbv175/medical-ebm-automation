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
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 11) — PolicyEngine.evaluate()
        # chỉ kiểm cổng bác sĩ duyệt (P006)/feature flag (P007) KHI context["action"] khớp
        # đúng một trong {"clinical_release","publish_clinical","apply_recommendation"};
        # thiếu hẳn khóa "action" (vd policy_context={"feature_flags": {}}) làm action="" và
        # BỎ QUA ÂM THẦM toàn bộ nhóm cổng theo action — release() vẫn thành công dù chưa hề
        # được PolicyEngine soi cổng bác sĩ duyệt nào. Buộc caller khai action tường minh:
        # không sửa được lỗi "khai sai/gõ nhầm action" (đặc điểm chung của toàn bộ
        # PolicyEngine dùng string dispatch, vượt phạm vi release_manager.py), nhưng chặn
        # đúng trường hợp quên khai hoàn toàn — chính kịch bản tái hiện của phát hiện này.
        if not str(policy_context.get("action") or "").strip():
            raise ValueError(
                "policy_context phải khai 'action' — thiếu 'action' khiến PolicyEngine bỏ qua "
                "ÂM THẦM toàn bộ cổng theo action (bác sĩ duyệt P006, feature flag P007...)."
            )
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
