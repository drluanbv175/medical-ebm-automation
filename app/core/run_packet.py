"""RunPacket chuẩn cho mọi phiên EBM V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional
from uuid import uuid4

from app.core.feature_flags import merge_feature_flags


class Lane(str, Enum):
    CLINICAL = "clinical"
    RESEARCH = "research"
    KNOWLEDGE = "knowledge"
    DASHBOARD = "dashboard"
    EXPORT = "export"
    SYSTEM = "system"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class InputCompleteness(str, Enum):
    MINIMAL = "minimal"
    PARTIAL = "partial"
    SUFFICIENT_FOR_DRAFT = "sufficient_for_draft"
    SUFFICIENT_FOR_REVIEW = "sufficient_for_review"


class PiiStatus(str, Enum):
    NOT_ASSESSED = "not_assessed"
    NONE_DETECTED = "none_detected"
    SUSPECTED = "suspected"
    PRESENT = "present"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING_PHYSICIAN = "pending_physician"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class RunPacket:
    """Đơn vị điều phối chuẩn để Claude Code và Codex cùng hiểu."""

    run_id: str
    request_id: str
    created_at: str
    lane: Lane
    objective: str
    actor_role: str = "assistant"
    risk_level: RiskLevel = RiskLevel.MODERATE
    input_completeness: InputCompleteness = InputCompleteness.MINIMAL
    pii_status: PiiStatus = PiiStatus.NOT_ASSESSED
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_PHYSICIAN
    inputs: Mapping[str, Any] = field(default_factory=dict)
    trace_ids: List[str] = field(default_factory=list)
    feature_flags: Mapping[str, bool] = field(default_factory=merge_feature_flags)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("RunPacket.objective không được rỗng")
        # ĐÁNH GIÁ 2026-09-05 (Workflow đối kháng đa-agent, task #73) — đã gỡ một
        # nhánh chết ở đây: `if lane in {...} and not self.trace_ids:
        # object.__setattr__(self, "trace_ids", [])`. Điều kiện chỉ đúng khi
        # `trace_ids` đã rỗng (falsy), và hành động gán lại đúng giá trị RỖNG
        # — không khác gì giữ nguyên. `RunPacket` chỉ được dựng qua
        # `new_run_packet()` (nơi DUY NHẤT gọi hàm khởi tạo trực tiếp trong toàn
        # repo), và hàm đó LUÔN chuẩn hoá `trace_ids=list(trace_ids or [])`
        # trước khi truyền vào — nên `self.trace_ids` không bao giờ là `None`
        # ở đây trên bất kỳ đường mã thật nào. Nhánh này không hề "bắt buộc
        # CLINICAL/RESEARCH/DASHBOARD phải có trace_ids" như tên các Lane gợi
        # ý — nó không kiểm tra, không cảnh báo, không raise: một cách chấp
        # nhận VÔ ĐIỀU KIỆN. Không thêm enforcement thật (vd raise khi rỗng):
        # `ChronicCareService.__init__` — người gọi CLINICAL-lane DUY NHẤT
        # trong repo — không truyền `trace_ids`, nên chặn cứng ở đây sẽ phá vỡ
        # toàn bộ module chronic_care mà không có yêu cầu nào (test/doctrine)
        # từng đòi hỏi điều đó — đúng nguyên tắc không tự bịa yêu cầu mới.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "request_id": self.request_id,
            "created_at": self.created_at,
            "lane": self.lane.value,
            "objective": self.objective,
            "actor_role": self.actor_role,
            "risk_level": self.risk_level.value,
            "input_completeness": self.input_completeness.value,
            "pii_status": self.pii_status.value,
            "approval_status": self.approval_status.value,
            "inputs": dict(self.inputs),
            "trace_ids": list(self.trace_ids),
            "feature_flags": merge_feature_flags(self.feature_flags),
            "metadata": dict(self.metadata),
        }


def new_run_packet(
    lane: Lane,
    objective: str,
    *,
    inputs: Optional[Mapping[str, Any]] = None,
    risk_level: RiskLevel = RiskLevel.MODERATE,
    input_completeness: InputCompleteness = InputCompleteness.MINIMAL,
    pii_status: PiiStatus = PiiStatus.NOT_ASSESSED,
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_PHYSICIAN,
    trace_ids: Optional[List[str]] = None,
    feature_flags: Optional[Mapping[str, bool]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> RunPacket:
    return RunPacket(
        run_id=f"run_{uuid4().hex}",
        request_id=f"req_{uuid4().hex}",
        created_at=datetime.now(timezone.utc).isoformat(),
        lane=lane,
        objective=objective,
        risk_level=risk_level,
        input_completeness=input_completeness,
        pii_status=pii_status,
        approval_status=approval_status,
        inputs=dict(inputs or {}),
        trace_ids=list(trace_ids or []),
        feature_flags=merge_feature_flags(feature_flags),
        metadata=dict(metadata or {}),
    )
