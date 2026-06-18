"""Cache xác minh citation cho Phase 2B.

Cache này không chứa PII và không được dùng để nâng citation thành VERIFIED khi đã
hết hạn. Nếu hết hạn, adapter phải gọi nguồn lại hoặc trả trạng thái an toàn.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Mapping, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def citation_cache_key(source_name: str, identifiers: Mapping[str, str]) -> str:
    payload = json.dumps({"source": source_name, "identifiers": dict(identifiers)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CitationCacheEntry:
    cache_key: str
    source_name: str
    source_response_hash: str
    fetched_at: str
    expires_at: str
    verification_status: str
    error_state: str = ""
    payload: Mapping[str, object] = field(default_factory=dict)

    @property
    def expired(self) -> bool:
        return datetime.fromisoformat(self.expires_at) <= utc_now()


class InMemoryCitationCache:
    """Cache deterministic cho tests và smoke script opt-in."""

    def __init__(self) -> None:
        self._items: Dict[str, CitationCacheEntry] = {}

    def get(self, key: str) -> Optional[CitationCacheEntry]:
        item = self._items.get(key)
        if item is None or item.expired:
            return None
        return item

    def put(
        self,
        *,
        source_name: str,
        identifiers: Mapping[str, str],
        payload: Mapping[str, object],
        verification_status: str,
        ttl_seconds: int,
        error_state: str = "",
    ) -> CitationCacheEntry:
        key = citation_cache_key(source_name, identifiers)
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        fetched_at = utc_now()
        entry = CitationCacheEntry(
            cache_key=key,
            source_name=source_name,
            source_response_hash=hashlib.sha256(blob.encode("utf-8")).hexdigest(),
            fetched_at=fetched_at.isoformat(),
            expires_at=(fetched_at + timedelta(seconds=ttl_seconds)).isoformat(),
            verification_status=verification_status,
            error_state=error_state,
            payload=dict(payload),
        )
        self._items[key] = entry
        return entry
