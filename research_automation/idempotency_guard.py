"""
idempotency_guard — Chống tạo trùng artifact cho cùng (project_id + request hash).

OFFLINE · DETERMINISTIC. Rerun cùng request → trả kết quả đã có (không tạo mới).
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Optional


def request_hash(payload: dict) -> str:
    """SHA-256 ổn định của request (sort_keys → deterministic)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class IdempotencyGuard:
    """Map (project_id, request_hash) → run_id đã hoàn tất."""

    def __init__(self):
        self._seen: Dict[str, str] = {}

    @staticmethod
    def _key(project_id: str, req_hash: str) -> str:
        return f"{project_id}:{req_hash}"

    def existing_run(self, project_id: str, req_hash: str) -> Optional[str]:
        return self._seen.get(self._key(project_id, req_hash))

    def is_duplicate(self, project_id: str, req_hash: str) -> bool:
        return self._key(project_id, req_hash) in self._seen

    def record(self, project_id: str, req_hash: str, run_id: str) -> None:
        self._seen.setdefault(self._key(project_id, req_hash), run_id)

    def count(self) -> int:
        return len(self._seen)
