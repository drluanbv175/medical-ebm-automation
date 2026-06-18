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
        if self.lane in {Lane.CLINICAL, Lane.RESEARCH, Lane.DASHBOARD} and not self.trace_ids:
            object.__setattr__(self, "trace_ids", [])

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
