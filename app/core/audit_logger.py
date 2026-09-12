"""Audit logger JSONL có khử PII cơ bản."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.core.policy_engine import _ADDRESS, _DOB, _EMAIL, _MRN, _PHONE, _VN_NAME


def scrub_pii(value: Any) -> Any:
    """Khử PII trước khi ghi audit log.

    SỬA 2026-09-04 (audit đối kháng, phát hiện HIGH — task #55): trước bản vá
    chỉ khử EMAIL/PHONE/MRN/DOB — thiếu `_ADDRESS`/`_VN_NAME`, dù cả hai
    pattern đã có sẵn trong CÙNG module `policy_engine.py` và được dùng bởi
    `contains_pii_text()` (hàm chặn ở nơi khác trong hệ). Hậu quả: một ghi chú
    ("notes"/"payload") chứa tên bệnh nhân ("Nguyễn Văn A") hoặc địa chỉ cư
    trú ("ngụ 12 Nguyễn Trãi Q1") đi qua `AuditLogger.log()` sẽ bị
    `contains_pii_text()` CHẶN ở nơi khác trong hệ nhưng lại được GHI NGUYÊN
    VĂN, không redact, vào chính file audit JSONL — nơi lẽ ra phải an toàn
    nhất để đọc lại khi điều tra sự cố.
    """
    if isinstance(value, str):
        text = value
        for pattern in (_EMAIL, _PHONE, _MRN, _DOB, _ADDRESS, _VN_NAME):
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
