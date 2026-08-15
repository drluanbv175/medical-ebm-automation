"""Change-control record cho thay đổi hệ thống V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Mapping
from uuid import uuid4


class ChangeRisk(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class ChangeRequest:
    change_id: str
    title: str
    risk: ChangeRisk
    affected_modules: List[str]
    rollback_plan: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Mapping[str, str] = field(default_factory=dict)


def new_change_request(title: str, risk: ChangeRisk, affected_modules: List[str], rollback_plan: str) -> ChangeRequest:
    if not rollback_plan.strip():
        raise ValueError("Change request bắt buộc có rollback_plan")
    return ChangeRequest(
        change_id=f"chg_{uuid4().hex}",
        title=title,
        risk=risk,
        affected_modules=list(affected_modules),
        rollback_plan=rollback_plan,
    )
