"""Audit helpers cho Chronic Care Phase 3A, tái sử dụng AuditLogger V7."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from app.core.audit_logger import AuditEvent, AuditLogger


def state_hash(state: Optional[Mapping[str, Any]]) -> str:
    payload = json.dumps(dict(state or {}), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChronicCareAuditTrail:
    logger: AuditLogger
    events: list[AuditEvent]


AUDIT_FILENAME = "chronic_care_phase_3a_audit.jsonl"


def default_audit_path() -> Path:
    """Tệp audit mặc định `settings.processed_dir / AUDIT_FILENAME`, tính LÚC GỌI.

    SỬA 01/10/2026: trước đây là `Path("data/processed/chronic_care_phase_3a_audit.jsonl")` — tương đối theo thư mục
    hiện hành, không qua `settings`, nên bộ test không chuyển hướng được và mỗi lượt pytest nối sự kiện tổng hợp vào
    `data/processed/` thật của cây. Chạy dashboard từ gốc repo (`Mở Dashboard.command`, `python run.py dashboard`) vẫn
    ra đúng tệp cũ. Import `app.config` trong hàm để import `app.chronic_care` vẫn không kéo theo `app.config` (nạp
    .env, tạo thư mục data/) — chỉ lời gọi dùng đường dẫn mặc định mới cần."""
    from app.config import settings

    return settings.processed_dir / AUDIT_FILENAME


def default_audit_trail(path: Path | None = None) -> ChronicCareAuditTrail:
    return ChronicCareAuditTrail(
        logger=AuditLogger(path or default_audit_path()),
        events=[],
    )


def log_chronic_care_event(
    trail: ChronicCareAuditTrail,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    environment: str,
    run_id: str,
    before_state: Optional[Mapping[str, Any]] = None,
    after_state: Optional[Mapping[str, Any]] = None,
    approval_reference: str = "",
    blocked_reason: str = "",
) -> AuditEvent:
    payload: Dict[str, Any] = {
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "environment": environment,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before_state_hash": state_hash(before_state),
        "after_state_hash": state_hash(after_state),
        "approval_reference": approval_reference,
        "blocked_reason": blocked_reason,
    }
    event = trail.logger.log(
        event_type=f"chronic_care.{action}",
        run_id=run_id,
        actor=actor,
        payload=payload,
    )
    trail.events.append(event)
    return event
