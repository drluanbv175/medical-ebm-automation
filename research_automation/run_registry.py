"""
run_registry — Sổ đăng ký automation run (V4.3.2).

Mỗi run có run_id + ghi agent hash, artifact hash, project hash, gate decisions,
queue decision, timestamps. Append-only (audit-grade). OFFLINE · in-memory.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _hash_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


@dataclasses.dataclass
class AutomationRunRecord:
    run_id: str
    project_id: str
    request_hash: str
    project_hash: str
    status: str                          # CREATED|RUNNING|COMPLETED|BLOCKED|SAFE_STOP|DUPLICATE
    started_utc: str
    finished_utc: Optional[str] = None
    agent_hashes: Dict[str, str] = dataclasses.field(default_factory=dict)
    artifact_hashes: Dict[str, str] = dataclasses.field(default_factory=dict)
    gate_decisions: List[dict] = dataclasses.field(default_factory=list)
    queue_decisions: List[dict] = dataclasses.field(default_factory=list)
    reason_code: Optional[str] = None
    snapshot_id: Optional[str] = None
    # Audit 2026-07-11: DraftStateMachine.history (research_workflow.ProjectRunResult
    # .history) trước đây bị tính rồi bỏ — không nơi nào persist được project đã đi
    # qua state nào/khi nào/vì sao BLOCK. Nay workflow_runner.py ghi vào đây.
    draft_transitions: List[dict] = dataclasses.field(default_factory=list)


class RunRegistry:
    """Append-only registry các automation run."""

    def __init__(self):
        self._runs: List[AutomationRunRecord] = []
        self._seq = 0

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def new_run_id(self, project_id: str) -> str:
        self._seq += 1
        return f"AUTORUN-{project_id}-{self._seq:04d}"

    def open(self, run_id: str, project_id: str, request_hash: str,
             project_hash: str, snapshot_id: Optional[str] = None) -> AutomationRunRecord:
        rec = AutomationRunRecord(
            run_id=run_id, project_id=project_id, request_hash=request_hash,
            project_hash=project_hash, status="RUNNING", started_utc=self._now(),
            snapshot_id=snapshot_id,
        )
        self._runs.append(rec)
        return rec

    def close(self, rec: AutomationRunRecord, status: str,
              reason_code: Optional[str] = None) -> None:
        rec.status = status
        rec.reason_code = reason_code
        rec.finished_utc = self._now()

    def get(self, run_id: str) -> Optional[AutomationRunRecord]:
        return next((r for r in self._runs if r.run_id == run_id), None)

    def all(self) -> List[AutomationRunRecord]:
        return list(self._runs)

    def count(self) -> int:
        return len(self._runs)

    @staticmethod
    def hash_obj(obj) -> str:
        return _hash_obj(obj)
