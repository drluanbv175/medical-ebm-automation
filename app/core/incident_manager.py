"""Quản lý sự cố an toàn/liêm chính cho V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Mapping, Optional
from uuid import uuid4


class IncidentSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    MITIGATED = "mitigated"
    CLOSED = "closed"


@dataclass
class Incident:
    incident_id: str
    run_id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: List[str] = field(default_factory=list)
    metadata: Mapping[str, str] = field(default_factory=dict)


class IncidentManager:
    def __init__(self) -> None:
        self._items: Dict[str, Incident] = {}

    def open(
        self,
        run_id: str,
        title: str,
        severity: IncidentSeverity,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Incident:
        incident = Incident(
            incident_id=f"inc_{uuid4().hex}",
            run_id=run_id,
            title=title,
            severity=severity,
            metadata=dict(metadata or {}),
        )
        self._items[incident.incident_id] = incident
        return incident

    def advance(self, incident_id: str, status: IncidentStatus, note: str = "") -> Incident:
        incident = self._items[incident_id]
        incident.status = status
        if note:
            incident.notes.append(note)
        return incident
