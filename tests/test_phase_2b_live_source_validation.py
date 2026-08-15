from datetime import date, datetime, timedelta, timezone

from app.evidence.citation_cache import InMemoryCitationCache
from app.evidence.citation_verification import CitationVerificationStatus, CitationVerifier, SourceMetadata
from app.evidence.live_adapter_registry import adapter_status_table, build_live_adapter_registry
from app.evidence.live_adapters.base import LiveSourceAdapter, LiveSourceConfig


class UnavailableAdapter(LiveSourceAdapter):
    def __init__(self):
        super().__init__(LiveSourceConfig("test_source", "article", "https://example.test"))

    def _lookup_live(self, identifiers):
        return SourceMetadata(found=False, unavailable=True, raw={"error_state": "timeout"})


class FoundAdapter(LiveSourceAdapter):
    def __init__(self, cache):
        super().__init__(LiveSourceConfig("found_source", "article", "https://example.test"), cache=cache)
        self.calls = 0

    def _lookup_live(self, identifiers):
        self.calls += 1
        return SourceMetadata(
            found=True,
            title="Correct Trial Title",
            authors_or_organization="AHA",
            year_or_version="2026-01-01",
            source_type="article",
            population="Adults",
        )


def test_live_adapter_timeout_maps_to_source_unavailable_not_verified():
    verifier = CitationVerifier(UnavailableAdapter(), today=date(2026, 6, 18))
    result = verifier.verify({
        "doi": "10.1000/test",
        "title": "Correct Trial Title",
        "source_type": "article",
        "claim_location": "s2",
    })

    assert result.status is CitationVerificationStatus.SOURCE_UNAVAILABLE
    assert not result.safe_for_verified_evidence


def test_live_adapter_cache_used_only_when_unexpired():
    cache = InMemoryCitationCache()
    adapter = FoundAdapter(cache)
    evidence = {
        "doi": "10.1000/test",
        "title": "Correct Trial Title",
        "source": "AHA",
        "year_or_version": "2026",
        "source_type": "article",
        "population": "Adults",
        "claim_location": "s2",
    }
    first = CitationVerifier(adapter, today=date(2026, 6, 18)).verify(evidence)
    second = CitationVerifier(adapter, today=date(2026, 6, 18)).verify(evidence)

    assert first.status is CitationVerificationStatus.VERIFIED
    assert second.status is CitationVerificationStatus.VERIFIED
    assert adapter.calls == 1

    expired_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    for key, entry in list(cache._items.items()):
        cache._items[key] = entry.__class__(
            cache_key=entry.cache_key,
            source_name=entry.source_name,
            source_response_hash=entry.source_response_hash,
            fetched_at=entry.fetched_at,
            expires_at=expired_at,
            verification_status=entry.verification_status,
            error_state=entry.error_state,
            payload=entry.payload,
        )
    third = CitationVerifier(adapter, today=date(2026, 6, 18)).verify(evidence)
    assert third.status is CitationVerificationStatus.VERIFIED
    assert adapter.calls == 2


def test_live_adapter_registry_exposes_required_sources_and_health_rows():
    registry = build_live_adapter_registry(["pubmed", "crossref", "openfda"])
    rows = adapter_status_table(registry)

    assert set(registry) == {"pubmed", "crossref", "openfda"}
    assert all("source_name" in row and "cache_policy" in row for row in rows)
