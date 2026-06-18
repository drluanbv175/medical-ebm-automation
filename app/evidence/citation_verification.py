"""Citation verification V7 Phase 2A.

Verifier này nhận metadata từ adapter nguồn hiện hữu hoặc stub test. Khi source không
khả dụng, trạng thái luôn bảo thủ (`SOURCE_UNAVAILABLE`), không tự suy đoán verified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Mapping, Optional, Protocol

from app.evidence.citation_validator import validate_identifier
from app.evidence.retraction_monitor import detect_retraction
from app.evidence.source_freshness import assess_freshness


class CitationVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    STALE = "STALE"
    RETRACTED = "RETRACTED"
    NEEDS_PHYSICIAN_REVIEW = "NEEDS_PHYSICIAN_REVIEW"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


@dataclass(frozen=True)
class SourceMetadata:
    found: bool
    title: str = ""
    authors_or_organization: str = ""
    year_or_version: str = ""
    source_type: str = ""
    population: str = ""
    retraction_note: str = ""
    raw: Mapping[str, str] = field(default_factory=dict)
    unavailable: bool = False


class SourceLookupAdapter(Protocol):
    def lookup(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        ...


@dataclass(frozen=True)
class CitationVerificationResult:
    status: CitationVerificationStatus
    checks: Mapping[str, bool]
    reasons: list
    last_verified_date: str
    verification_method: str
    source_metadata: SourceMetadata

    @property
    def safe_for_verified_evidence(self) -> bool:
        return self.status is CitationVerificationStatus.VERIFIED


def _norm(value: str) -> str:
    return " ".join((value or "").casefold().split())


def _title_matches(expected: str, observed: str) -> bool:
    exp = _norm(expected)
    obs = _norm(observed)
    if not exp or not obs:
        return False
    return exp in obs or obs in exp


def _loose_contains(expected: str, observed: str) -> bool:
    expected = _norm(expected)
    observed = _norm(observed)
    return bool(expected and observed and (expected in observed or observed in expected))


class CitationVerifier:
    def __init__(self, adapter: SourceLookupAdapter, today: Optional[date] = None) -> None:
        self.adapter = adapter
        self.today = today or date.today()

    def verify(self, evidence: Mapping[str, object]) -> CitationVerificationResult:
        identifiers = dict(evidence.get("identifiers") or {})
        if evidence.get("doi"):
            identifiers.setdefault("doi", str(evidence["doi"]))
        if evidence.get("pmid"):
            identifiers.setdefault("pmid", str(evidence["pmid"]))
        if evidence.get("url"):
            identifiers.setdefault("url", str(evidence["url"]))

        id_check = validate_identifier(identifiers)
        if not id_check.valid:
            return self._result(
                CitationVerificationStatus.UNVERIFIED,
                SourceMetadata(found=False),
                {"traceability": False},
                ["Thiếu hoặc sai định dạng PMID/DOI/URL"],
                "format_check_only",
            )

        try:
            source = self.adapter.lookup(identifiers)
        except Exception as exc:  # pragma: no cover - type phụ thuộc adapter thật
            return self._result(
                CitationVerificationStatus.SOURCE_UNAVAILABLE,
                SourceMetadata(found=False, unavailable=True),
                {"source_available": False, "traceability": True},
                [f"Source adapter unavailable: {exc.__class__.__name__}"],
                "source_unavailable",
            )
        if source.unavailable:
            return self._result(
                CitationVerificationStatus.SOURCE_UNAVAILABLE,
                source,
                {"source_available": False, "traceability": True},
                ["Online/source adapter unavailable; không được tự xác minh"],
                "source_unavailable",
            )
        if not source.found:
            return self._result(
                CitationVerificationStatus.UNVERIFIED,
                source,
                {"source_found": False, "traceability": True},
                ["Không tìm thấy nguồn theo định danh"],
                "source_lookup",
            )

        retraction = detect_retraction({**source.raw, "retraction_note": source.retraction_note})
        if retraction.affected:
            return self._result(
                CitationVerificationStatus.RETRACTED,
                source,
                {"not_retracted": False, "traceability": True},
                [retraction.reason],
                "source_lookup",
            )

        title_ok = _title_matches(str(evidence.get("title") or ""), source.title)
        author_ok = _loose_contains(
            str(evidence.get("authors_or_organization") or evidence.get("source") or ""),
            source.authors_or_organization,
        )
        expected_year = str(evidence.get("year_or_version") or "")
        expected_type = str(evidence.get("source_type") or "")
        year_ok = bool(not expected_year or _loose_contains(expected_year, source.year_or_version))
        type_ok = bool(not expected_type or _loose_contains(expected_type, source.source_type))
        population_ok = bool(
            not evidence.get("population")
            or _loose_contains(str(evidence.get("population") or ""), source.population)
        )
        location_ok = bool(evidence.get("claim_location") or evidence.get("claim_location_reason"))
        guideline_has_version = bool(
            "guideline" not in _norm(expected_type or source.source_type) or source.year_or_version
        )

        freshness = assess_freshness(source.year_or_version[:10], today=self.today, max_age_days=1095)
        checks = {
            "traceability": True,
            "source_found": True,
            "title_match": title_ok,
            "author_or_org_match": author_ok,
            "year_or_version_match": year_ok,
            "source_type_match": type_ok,
            "population_assessable": population_ok,
            "claim_location_present": location_ok,
            "guideline_version_present": guideline_has_version,
            "not_stale": not freshness.stale,
            "not_retracted": True,
        }
        reasons = [name for name, passed in checks.items() if not passed]
        if not guideline_has_version:
            status = CitationVerificationStatus.NEEDS_PHYSICIAN_REVIEW
        elif not checks["not_stale"]:
            status = CitationVerificationStatus.STALE
        elif not title_ok or not year_ok or not type_ok or not population_ok:
            status = CitationVerificationStatus.MISMATCH
        elif all(checks.values()):
            status = CitationVerificationStatus.VERIFIED
        elif title_ok and checks["source_found"]:
            status = CitationVerificationStatus.PARTIALLY_VERIFIED
        else:
            status = CitationVerificationStatus.NEEDS_PHYSICIAN_REVIEW
        return self._result(status, source, checks, reasons, "source_lookup")

    def _result(
        self,
        status: CitationVerificationStatus,
        source: SourceMetadata,
        checks: Mapping[str, bool],
        reasons: list,
        method: str,
    ) -> CitationVerificationResult:
        return CitationVerificationResult(
            status=status,
            checks=dict(checks),
            reasons=list(reasons),
            last_verified_date=self.today.isoformat(),
            verification_method=method,
            source_metadata=source,
        )


class StaticSourceLookupAdapter:
    """Adapter deterministic cho tests/evals."""

    def __init__(self, records: Mapping[str, SourceMetadata], unavailable: bool = False) -> None:
        self.records = dict(records)
        self.unavailable = unavailable

    def lookup(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        if self.unavailable:
            return SourceMetadata(found=False, unavailable=True)
        for key in ("doi", "pmid", "url"):
            value = identifiers.get(key)
            if value and f"{key}:{value}" in self.records:
                return self.records[f"{key}:{value}"]
        return SourceMetadata(found=False)
