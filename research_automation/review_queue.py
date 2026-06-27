"""
review_queue — Hàng đợi review + điểm quyết định của NGƯỜI (V4.3.2).

Tự động hóa CHỈ được: tạo review task, nhắc việc, tổng hợp missing fields,
phát hiện inconsistency, tạo revision draft. TUYỆT ĐỐI không tự chuyển
PENDING_REVIEW → HUMAN_APPROVED_DRAFT (chỉ người mới approve).

KHÔNG dùng "ethics approved" / "PI approved" / "final approved" cho synthetic.
OFFLINE · deterministic · in-memory.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Dict, List, Optional


class ReviewStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    REQUIRES_HUMAN_INPUT = "REQUIRES_HUMAN_INPUT"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    HUMAN_APPROVED_DRAFT = "HUMAN_APPROVED_DRAFT"   # CHỈ người đặt được
    REJECTED_DRAFT = "REJECTED_DRAFT"               # CHỈ người đặt được
    ARCHIVED = "ARCHIVED"


# Trạng thái CHỈ người thật mới được chuyển tới (automation bị cấm).
_HUMAN_ONLY_TARGETS = frozenset({
    ReviewStatus.HUMAN_APPROVED_DRAFT,
    ReviewStatus.REJECTED_DRAFT,
})

# Tự động hóa được phép chuyển tới các trạng thái này.
_AUTOMATION_ALLOWED_TARGETS = frozenset({
    ReviewStatus.PENDING_REVIEW,
    ReviewStatus.REQUIRES_HUMAN_INPUT,
    ReviewStatus.REVISION_REQUESTED,
    ReviewStatus.ARCHIVED,
})


class AutoApprovalForbidden(RuntimeError):
    """Automation cố đặt trạng thái human-only (vd HUMAN_APPROVED_DRAFT)."""


@dataclasses.dataclass
class ReviewItem:
    review_id: str
    project_id: str
    artifact_id: str
    review_reason: str
    blocking_gate: Optional[str]
    required_human_role: str
    missing_information: List[str]
    risks: List[str]
    status: ReviewStatus
    audit_event_id: Optional[str]
    created_utc: str = ""

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["status"] = self.status.value
        return d


class ReviewQueue:
    def __init__(self):
        self._items: List[ReviewItem] = []
        self._seq = 0

    def add(self, *, project_id: str, artifact_id: str, review_reason: str,
            blocking_gate: Optional[str], required_human_role: str,
            missing_information: List[str], risks: List[str],
            audit_event_id: Optional[str],
            status: ReviewStatus = ReviewStatus.PENDING_REVIEW,
            created_utc: str = "") -> ReviewItem:
        # Automation KHÔNG được tạo item ở trạng thái human-only.
        if status in _HUMAN_ONLY_TARGETS:
            raise AutoApprovalForbidden(
                f"AUTO_APPROVAL_FORBIDDEN:{status.value}"
            )
        self._seq += 1
        item = ReviewItem(
            review_id=f"REV-{project_id}-{self._seq:04d}",
            project_id=project_id, artifact_id=artifact_id,
            review_reason=review_reason, blocking_gate=blocking_gate,
            required_human_role=required_human_role,
            missing_information=list(missing_information), risks=list(risks),
            status=status, audit_event_id=audit_event_id, created_utc=created_utc,
        )
        self._items.append(item)
        return item

    def automation_transition(self, review_id: str, target: ReviewStatus) -> ReviewItem:
        """Chuyển trạng thái BỞI AUTOMATION — chặn mọi target human-only."""
        if target in _HUMAN_ONLY_TARGETS:
            raise AutoApprovalForbidden(
                f"AUTO_APPROVAL_FORBIDDEN:{target.value} — chỉ người thật mới đặt"
            )
        if target not in _AUTOMATION_ALLOWED_TARGETS:
            raise AutoApprovalForbidden(f"AUTOMATION_TARGET_NOT_ALLOWED:{target.value}")
        item = self._get(review_id)
        item.status = target
        return item

    def human_decision(self, review_id: str, target: ReviewStatus,
                       human_reviewer_ref: str) -> ReviewItem:
        """
        Quyết định của NGƯỜI THẬT (mô phỏng điểm vào của con người). Chỉ hàm này
        mới đặt được HUMAN_APPROVED_DRAFT/REJECTED_DRAFT. Yêu cầu human ref rõ ràng.
        """
        if not human_reviewer_ref or "AUTO" in human_reviewer_ref.upper():
            raise AutoApprovalForbidden(
                "HUMAN_DECISION_REQUIRES_REAL_HUMAN_REF (không phải automation)"
            )
        item = self._get(review_id)
        item.status = target
        return item

    def stale_items(self, max_pending: int) -> List[ReviewItem]:
        """Item PENDING/REQUIRES_INPUT quá ngưỡng (theo thứ tự đưa vào)."""
        pend = [i for i in self._items
                if i.status in (ReviewStatus.PENDING_REVIEW,
                                ReviewStatus.REQUIRES_HUMAN_INPUT)]
        return pend[max_pending:] if len(pend) > max_pending else []

    def by_status(self, status: ReviewStatus) -> List[ReviewItem]:
        return [i for i in self._items if i.status == status]

    def all(self) -> List[ReviewItem]:
        return list(self._items)

    def count(self) -> int:
        return len(self._items)

    def _get(self, review_id: str) -> ReviewItem:
        for i in self._items:
            if i.review_id == review_id:
                return i
        raise KeyError(f"REVIEW_ITEM_NOT_FOUND:{review_id}")
