"""Audit logger JSONL có khử PII cơ bản."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.core.policy_engine import _DOB, _EMAIL, _MRN, _PHONE


def scrub_pii(value: Any) -> Any:
    if isinstance(value, str):
        text = value
        for pattern in (_EMAIL, _PHONE, _MRN, _DOB):
            text = pattern.sub("[REDACTED_PII]", text)
        return text
    if isinstance(value, list):
        return [scrub_pii(v) for v in value]
    if isinstance(value, dict):
        return {str(k): scrub_pii(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    created_at: str
    run_id: str
    actor: str
    payload: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "run_id": self.run_id,
            "actor": self.actor,
            "payload": scrub_pii(dict(self.payload)),
        }


class AuditLogger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, run_id: str, actor: str, payload: Optional[Mapping[str, Any]] = None) -> AuditEvent:
        event = AuditEvent(
            event_id=f"audit_{uuid4().hex}",
            event_type=event_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            run_id=run_id,
            actor=actor,
            payload=dict(payload or {}),
        )
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return event
