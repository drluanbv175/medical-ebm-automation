"""Regression cho source_health khi PubMed E-utilities tạm hỏng.

Không được xanh giả nếu mất PubMed mà thiếu mirror; nhưng cũng không nên chặn toàn bộ
candidate queue khi Europe PMC MEDLINE và Crossref vẫn khỏe để đối chiếu PMID/DOI.
"""
from __future__ import annotations

from app.services.ingestion import summarize_source_health


def _log(source: str, status: str, records: int) -> dict:
    return {"source": source, "status": status, "record_count": records}


def test_pubmed_outage_can_pass_when_europepmc_and_crossref_mirror_are_healthy():
    health = summarize_source_health(
        [
            _log("pubmed", "error", 0),
            _log("europepmc", "ok", 10),
            _log("crossref", "ok", 10),
            _log("openfda", "ok", 3),
        ],
        expected_api_sources=["pubmed", "europepmc", "crossref"],
        expected_feed_sources=[],
        safety_enabled=True,
    )

    assert health["status"] == "PASS"
    assert health["degraded_required_sources"] == []
    assert health["mirror_notices"] == ["PUBMED_EUTILS_MIRRORED_BY_EUROPEPMC_AND_CROSSREF"]


def test_pubmed_outage_fails_without_required_mirror():
    health = summarize_source_health(
        [
            _log("pubmed", "error", 0),
            _log("europepmc", "error", 0),
            _log("crossref", "ok", 10),
            _log("openfda", "ok", 3),
        ],
        expected_api_sources=["pubmed", "europepmc", "crossref"],
        expected_feed_sources=[],
        safety_enabled=True,
    )

    assert health["status"] == "FAIL"
    assert "pubmed" in health["degraded_required_sources"]
    assert "DISCOVERY_CORE_COVERAGE_INSUFFICIENT" in health["hard_fail_reasons"]
