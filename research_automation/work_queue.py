"""
work_queue — Hàng đợi công việc workflow + LOCK theo project (V4.3.2).

Locking: không cho hai workflow cùng sửa một project (acquire/release theo project_id).
OFFLINE · deterministic · in-memory.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional


class ProjectLockError(RuntimeError):
    """Project đang bị khóa bởi một run khác."""


@dataclasses.dataclass
class WorkItem:
    item_id: str
    project_id: str
    request_hash: str
    status: str = "QUEUED"          # QUEUED|RUNNING|DONE|BLOCKED


class WorkQueue:
    def __init__(self):
        self._items: List[WorkItem] = []
        self._locks: Dict[str, str] = {}     # project_id → owner run_id
        self._seq = 0

    # ── Queue ───────────────────────────────────────────────────────────────
    def enqueue(self, project_id: str, request_hash: str) -> WorkItem:
        self._seq += 1
        item = WorkItem(item_id=f"WI-{self._seq:04d}", project_id=project_id,
                        request_hash=request_hash)
        self._items.append(item)
        return item

    def pending(self) -> List[WorkItem]:
        return [i for i in self._items if i.status == "QUEUED"]

    def count(self) -> int:
        return len(self._items)

    # ── Locking ─────────────────────────────────────────────────────────────
    def is_locked(self, project_id: str) -> bool:
        return project_id in self._locks

    def acquire(self, project_id: str, owner_run_id: str) -> None:
        """Khóa project. Raise ProjectLockError nếu đã bị khóa bởi run khác."""
        cur = self._locks.get(project_id)
        if cur is not None and cur != owner_run_id:
            raise ProjectLockError(
                f"PROJECT_LOCKED:{project_id}:held_by:{cur}"
            )
        self._locks[project_id] = owner_run_id

    def release(self, project_id: str, owner_run_id: str) -> None:
        if self._locks.get(project_id) == owner_run_id:
            del self._locks[project_id]

    def lock_owner(self, project_id: str) -> Optional[str]:
        return self._locks.get(project_id)
