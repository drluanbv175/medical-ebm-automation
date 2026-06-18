"""Hàng đợi xung đột bằng chứng."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import uuid4


@dataclass(frozen=True)
class EvidenceConflict:
    conflict_id: str
    topic: str
    evidence_ids: List[str]
    reason: str
    status: str = "open"


class ConflictQueue:
    def __init__(self) -> None:
        self.items: List[EvidenceConflict] = []

    def add(self, topic: str, evidence_ids: List[str], reason: str) -> EvidenceConflict:
        conflict = EvidenceConflict(
            conflict_id=f"conf_{uuid4().hex}",
            topic=topic,
            evidence_ids=list(evidence_ids),
            reason=reason,
        )
        self.items.append(conflict)
        return conflict

    def open_items(self) -> List[EvidenceConflict]:
        return [item for item in self.items if item.status == "open"]
