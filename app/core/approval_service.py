"""Approval center bắt buộc cho đầu ra lâm sàng/nghiên cứu chính thức."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Mapping, Optional
from uuid import uuid4


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalItem:
    approval_id: str
    run_id: str
    item_type: str
    summary: str
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_at: Optional[str] = None
    reviewer_role: Optional[str] = None
    reviewer_note: Optional[str] = None
    metadata: Mapping[str, str] = field(default_factory=dict)


class ApprovalCenter:
    """Kho phê duyệt in-memory dùng cho test và adapter ban đầu."""

    def __init__(self) -> None:
        self._items: Dict[str, ApprovalItem] = {}

    def submit(
        self,
        run_id: str,
        item_type: str,
        summary: str,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> ApprovalItem:
        item = ApprovalItem(
            approval_id=f"apr_{uuid4().hex}",
            run_id=run_id,
            item_type=item_type,
            summary=summary,
            metadata=dict(metadata or {}),
        )
        self._items[item.approval_id] = item
        return item

    def approve(self, approval_id: str, reviewer_role: str, note: str = "") -> ApprovalItem:
        item = self._require_item(approval_id)
        if reviewer_role not in {"physician", "principal_investigator", "system_owner"}:
            raise PermissionError("Chỉ reviewer có thẩm quyền mới được approve")
        item.status = ReviewStatus.APPROVED
        item.reviewed_at = datetime.now(timezone.utc).isoformat()
        item.reviewer_role = reviewer_role
        item.reviewer_note = note
        return item

    def reject(self, approval_id: str, reviewer_role: str, note: str) -> ApprovalItem:
        item = self._require_item(approval_id)
        # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện LOW
        # — defense-in-depth, không phải lỗ hổng đang khai thác được: route
        # sống hiện tại (app/chronic_care/dashboard.py) không hề gọi
        # reject(), nhưng approve() đã có kiểm role này còn reject() thì
        # không — bất đối xứng dễ gây lỗi nếu Phase 3B thêm UI ghi thật gọi
        # thẳng reject() mà quên kiểm role riêng).
        if reviewer_role not in {"physician", "principal_investigator", "system_owner"}:
            raise PermissionError("Chỉ reviewer có thẩm quyền mới được reject")
        item.status = ReviewStatus.REJECTED
        item.reviewed_at = datetime.now(timezone.utc).isoformat()
        item.reviewer_role = reviewer_role
        item.reviewer_note = note
        return item

    def get(self, approval_id: str) -> Optional[ApprovalItem]:
        return self._items.get(approval_id)

    def _require_item(self, approval_id: str) -> ApprovalItem:
        item = self.get(approval_id)
        if item is None:
            raise KeyError(f"Không tìm thấy approval_id={approval_id}")
        return item
