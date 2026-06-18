"""Base adapter cho live-source citation verification Phase 2B."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from app.evidence.citation_cache import InMemoryCitationCache, citation_cache_key
from app.evidence.citation_verification import SourceLookupAdapter, SourceMetadata
from app.evidence.source_health_monitor import SourceHealth, SourceHealthMonitor


@dataclass(frozen=True)
class LiveSourceConfig:
    source_name: str
    source_type_supported: str
    endpoint: str
    timeout: float = 15.0
    retry_policy: str = "http_client_exponential_backoff"
    rate_limit_policy: str = "respect_429_retry_after"
    cache_policy: str = "ttl_24h_no_verified_when_expired"
    cache_ttl_seconds: int = 86400


class LiveSourceAdapter(SourceLookupAdapter):
    """Adapter base: cache còn hạn được dùng, cache hết hạn không tạo VERIFIED."""

    def __init__(
        self,
        config: LiveSourceConfig,
        *,
        cache: Optional[InMemoryCitationCache] = None,
        monitor: Optional[SourceHealthMonitor] = None,
    ) -> None:
        self.config = config
        self.cache = cache or InMemoryCitationCache()
        self.monitor = monitor or SourceHealthMonitor()
        self.health = self.monitor.register(SourceHealth(
            source_name=config.source_name,
            source_type_supported=config.source_type_supported,
            timeout=config.timeout,
            retry_policy=config.retry_policy,
            rate_limit_policy=config.rate_limit_policy,
            cache_policy=config.cache_policy,
        ))

    @property
    def source_name(self) -> str:
        return self.config.source_name

    def lookup(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        key = citation_cache_key(self.source_name, identifiers)
        cached = self.cache.get(key)
        if cached is not None and cached.payload:
            self.monitor.success(self.source_name)
            payload = dict(cached.payload)
            payload.setdefault("raw", {})
            payload["raw"] = {**dict(payload.get("raw") or {}), "cache_key": cached.cache_key}
            return SourceMetadata(**payload)

        try:
            source = self._lookup_live(identifiers)
        except Exception as exc:
            self.monitor.failure(self.source_name, exc.__class__.__name__)
            return SourceMetadata(
                found=False,
                unavailable=True,
                raw={"source_name": self.source_name, "error_state": exc.__class__.__name__},
            )

        status = "FOUND" if source.found else "UNVERIFIED"
        error_state = "source_unavailable" if source.unavailable else ""
        payload = {
            "found": source.found,
            "title": source.title,
            "authors_or_organization": source.authors_or_organization,
            "year_or_version": source.year_or_version,
            "source_type": source.source_type,
            "population": source.population,
            "retraction_note": source.retraction_note,
            "raw": dict(source.raw),
            "unavailable": source.unavailable,
        }
        self.cache.put(
            source_name=self.source_name,
            identifiers=identifiers,
            payload=payload,
            verification_status=status,
            ttl_seconds=self.config.cache_ttl_seconds,
            error_state=error_state,
        )
        if source.unavailable:
            self.monitor.failure(self.source_name, "source_unavailable")
        else:
            self.monitor.success(self.source_name)
        return source

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        raise NotImplementedError
