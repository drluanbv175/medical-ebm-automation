"""Theo dõi sức khỏe source adapter Phase 2B."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceHealth:
    source_name: str
    source_type_supported: str
    timeout: float
    retry_policy: str
    rate_limit_policy: str
    cache_policy: str
    health_status: str = "unknown"
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    failure_reason: str = ""


class SourceHealthMonitor:
    def __init__(self) -> None:
        self._health: Dict[str, SourceHealth] = {}

    def register(self, health: SourceHealth) -> SourceHealth:
        self._health[health.source_name] = health
        return health

    def success(self, source_name: str) -> SourceHealth:
        health = self._health[source_name]
        health.health_status = "ok"
        health.last_success_at = _now()
        health.failure_reason = ""
        return health

    def failure(self, source_name: str, reason: str) -> SourceHealth:
        health = self._health[source_name]
        health.health_status = "unavailable"
        health.last_failure_at = _now()
        health.failure_reason = reason
        return health

    def snapshot(self) -> Dict[str, SourceHealth]:
        return dict(self._health)
