"""Registry live-source adapters Phase 2B."""
from __future__ import annotations

from typing import Dict, Iterable, Mapping

from app.evidence.citation_cache import InMemoryCitationCache
from app.evidence.live_adapters import (
    CrossrefLiveAdapter,
    EuropePMCLiveAdapter,
    GuidelineRssLiveAdapter,
    OpenAlexLiveAdapter,
    OpenFDALiveAdapter,
    PubMedLiveAdapter,
    SemanticScholarLiveAdapter,
)
from app.evidence.live_adapters.base import LiveSourceAdapter
from app.evidence.source_health_monitor import SourceHealthMonitor

ADAPTER_CLASSES = {
    "pubmed": PubMedLiveAdapter,
    "europepmc": EuropePMCLiveAdapter,
    "crossref": CrossrefLiveAdapter,
    "openalex": OpenAlexLiveAdapter,
    "semantic_scholar": SemanticScholarLiveAdapter,
    "guideline_rss": GuidelineRssLiveAdapter,
    "openfda": OpenFDALiveAdapter,
}


def build_live_adapter_registry(
    sources: Iterable[str] | None = None,
    *,
    cache: InMemoryCitationCache | None = None,
    monitor: SourceHealthMonitor | None = None,
) -> Dict[str, LiveSourceAdapter]:
    selected = list(sources or ADAPTER_CLASSES.keys())
    shared_cache = cache or InMemoryCitationCache()
    shared_monitor = monitor or SourceHealthMonitor()
    return {
        name: ADAPTER_CLASSES[name](cache=shared_cache, monitor=shared_monitor)
        for name in selected
        if name in ADAPTER_CLASSES
    }


def adapter_status_table(registry: Mapping[str, LiveSourceAdapter]) -> list[dict]:
    rows = []
    for name, adapter in registry.items():
        health = adapter.health
        rows.append({
            "source_name": name,
            "source_type_supported": health.source_type_supported,
            "timeout": health.timeout,
            "retry_policy": health.retry_policy,
            "rate_limit_policy": health.rate_limit_policy,
            "cache_policy": health.cache_policy,
            "health_status": health.health_status,
            "last_success_at": health.last_success_at,
            "last_failure_at": health.last_failure_at,
            "failure_reason": health.failure_reason,
        })
    return rows
