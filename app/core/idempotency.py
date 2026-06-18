"""Idempotency ledger cho các thao tác sync/export."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


def make_idempotency_key(namespace: str, payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


@dataclass(frozen=True)
class IdempotencyResult:
    key: str
    first_seen: bool
    value: Optional[Mapping[str, Any]] = None


class IdempotencyLedger:
    def __init__(self) -> None:
        self._seen: Dict[str, Mapping[str, Any]] = {}

    def record(self, key: str, value: Optional[Mapping[str, Any]] = None) -> IdempotencyResult:
        if key in self._seen:
            return IdempotencyResult(key=key, first_seen=False, value=self._seen[key])
        self._seen[key] = dict(value or {})
        return IdempotencyResult(key=key, first_seen=True, value=self._seen[key])
