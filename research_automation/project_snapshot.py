"""
project_snapshot — Snapshot/rollback trạng thái DRAFT/synthetic (V4.3.2).

Lưu snapshot TRƯỚC mỗi workflow run. Rollback CHỈ restore DRAFT/synthetic state.
TUYỆT ĐỐI không overwrite audit log (audit là append-only, ngoài snapshot).
OFFLINE · in-memory deterministic.
"""

from __future__ import annotations

import copy
import dataclasses
from typing import Dict, List, Optional

from research_studio.project_schema import ResearchProject


@dataclasses.dataclass
class ProjectSnapshot:
    snapshot_id: str
    project_id: str
    project_state: dict          # bản sao to_dict() của project (DRAFT/synthetic)
    artifact_ids: List[str]      # danh sách artifact_id tại thời điểm snapshot


class SnapshotStore:
    """Kho snapshot in-memory. KHÔNG đụng audit log."""

    def __init__(self):
        self._snaps: Dict[str, ProjectSnapshot] = {}
        self._seq = 0

    def take(self, project: ResearchProject, artifact_ids: List[str]) -> ProjectSnapshot:
        self._seq += 1
        sid = f"SNAP-{project.project_id}-{self._seq:04d}"
        snap = ProjectSnapshot(
            snapshot_id=sid,
            project_id=project.project_id,
            project_state=copy.deepcopy(project.to_dict()),
            artifact_ids=list(artifact_ids),
        )
        self._snaps[sid] = snap
        return snap

    def get(self, snapshot_id: str) -> Optional[ProjectSnapshot]:
        return self._snaps.get(snapshot_id)

    def rollback_view(self, snapshot_id: str) -> Optional[dict]:
        """
        Trả về VIEW trạng thái DRAFT để khôi phục (chỉ dữ liệu synthetic/draft).
        Không tự ghi đè gì — caller áp dụng có kiểm soát. KHÔNG đụng audit log.
        """
        snap = self._snaps.get(snapshot_id)
        if snap is None:
            return None
        return {
            "restores": "DRAFT_SYNTHETIC_STATE_ONLY",
            "project_state": copy.deepcopy(snap.project_state),
            "artifact_ids": list(snap.artifact_ids),
            "audit_log_preserved": True,   # bất biến: audit KHÔNG bị rollback
        }

    def count(self) -> int:
        return len(self._snaps)
