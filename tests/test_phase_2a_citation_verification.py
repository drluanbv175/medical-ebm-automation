from datetime import date

import pytest

from app.evidence.citation_verification import (
    CitationVerificationStatus,
    CitationVerifier,
    SourceMetadata,
    StaticSourceLookupAdapter,
)


def _verifier(records, unavailable=False):
    return CitationVerifier(StaticSourceLookupAdapter(records, unavailable=unavailable), today=date(2026, 6, 18))


def _source(**overrides):
    data = {
        "found": True,
        "title": "Correct Trial Title",
        "authors_or_organization": "AHA",
        "year_or_version": "2026-01-01",
        "source_type": "guideline",
        "population": "Adults",
    }
    data.update(overrides)
    return SourceMetadata(**data)


class TimeoutAdapter:
    def lookup(self, identifiers):
        raise TimeoutError("adapter timeout")


def test_verified_requires_traceability_title_type_population_location_and_freshness():
    result = _verifier({"doi:10.1000/test": _source()}).verify({
        "doi": "10.1000/test",
        "title": "Correct Trial Title",
        "source": "AHA",
        "year_or_version": "2026",
        "source_type": "guideline",
        "population": "Adults",
        "claim_location": "section 2",
    })

    assert result.status is CitationVerificationStatus.VERIFIED
    assert result.safe_for_verified_evidence


@pytest.mark.parametrize(
    ("evidence", "source", "expected"),
    [
        (
            {"doi": "10.1000/test", "title": "Wrong title", "source_type": "guideline", "claim_location": "table 1"},
            _source(),
            CitationVerificationStatus.MISMATCH,
        ),
        (
            {"doi": "10.1000/missing", "title": "Correct Trial Title", "source_type": "guideline"},
            SourceMetadata(found=False),
            CitationVerificationStatus.UNVERIFIED,
        ),
        (
            {"pmid": "99999999", "title": "Correct Trial Title", "source_type": "guideline"},
            SourceMetadata(found=False),
            CitationVerificationStatus.UNVERIFIED,
        ),
        (
            {"doi": "10.1000/test", "title": "Correct Trial Title", "source_type": "rct", "claim_location": "table 1"},
            _source(source_type="guideline"),
            CitationVerificationStatus.MISMATCH,
        ),
        (
            {"doi": "10.1000/test", "title": "Correct Trial Title", "source_type": "guideline", "claim_location": "s2"},
            _source(year_or_version="2020-01-01"),
            CitationVerificationStatus.STALE,
        ),
        (
            {"doi": "10.1000/test", "title": "Correct Trial Title", "source_type": "guideline", "claim_location": "s2"},
            _source(retraction_note="retracted"),
            CitationVerificationStatus.RETRACTED,
        ),
        (
            {"doi": "10.1000/test", "title": "Correct Trial Title", "source_type": "guideline"},
            _source(),
            CitationVerificationStatus.PARTIALLY_VERIFIED,
        ),
        (
            {
                "doi": "10.1000/test",
                "title": "Correct Trial Title",
                "source_type": "guideline",
                "population": "Older adults",
                "claim_location": "s2",
            },
            _source(population=""),
            CitationVerificationStatus.MISMATCH,
        ),
        (
            {
                "pmid": "12345678",
                "title": "Correct Trial Title",
                "source_type": "guideline",
                "year_or_version": "2024",
                "claim_location": "s2",
            },
            _source(year_or_version="2026-01-01"),
            CitationVerificationStatus.MISMATCH,
        ),
        (
            {
                "doi": "10.1000/test",
                "title": "Correct Trial Title",
                "source_type": "guideline",
                "claim_location": "s2",
            },
            _source(year_or_version=""),
            CitationVerificationStatus.NEEDS_PHYSICIAN_REVIEW,
        ),
    ],
)
def test_citation_verification_failure_modes(evidence, source, expected):
    key = "pmid:" + evidence["pmid"] if "pmid" in evidence else "doi:" + evidence["doi"]
    result = _verifier({key: source}).verify(evidence)

    assert result.status is expected
    assert not result.safe_for_verified_evidence


def test_online_source_unavailable_is_safe_not_verified():
    result = _verifier({}, unavailable=True).verify({
        "doi": "10.1000/test",
        "title": "Correct Trial Title",
        "source_type": "guideline",
        "claim_location": "s2",
    })

    assert result.status is CitationVerificationStatus.SOURCE_UNAVAILABLE
    assert not result.safe_for_verified_evidence


def test_adapter_timeout_is_source_unavailable_not_verified():
    result = CitationVerifier(TimeoutAdapter(), today=date(2026, 6, 18)).verify({
        "doi": "10.1000/test",
        "title": "Correct Trial Title",
        "source_type": "guideline",
        "claim_location": "s2",
    })

    assert result.status is CitationVerificationStatus.SOURCE_UNAVAILABLE
    assert not result.safe_for_verified_evidence


def test_missing_doi_pmid_or_url_is_unverified():
    result = _verifier({}).verify({
        "title": "Correct Trial Title",
        "source_type": "guideline",
        "claim_location": "s2",
    })

    assert result.status is CitationVerificationStatus.UNVERIFIED
    assert not result.safe_for_verified_evidence
