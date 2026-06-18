"""Evidence registry V7: chỉ đưa nguồn có truy nguyên vào dòng chính."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional
from uuid import uuid4


class EvidenceStatus(str, Enum):
    DRAFT = "draft"
    VERIFIED = "verified"
    QUARANTINED = "quarantined"
    RETRACTED = "retracted"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    title: str
    source: str
    evidence_type: str
    identifiers: Mapping[str, str] = field(default_factory=dict)
    publication_date: str = ""
    url: str = ""
    status: EvidenceStatus = EvidenceStatus.DRAFT
    quality_label: str = "ungraded"
    notes: str = ""

    @property
    def traceability_id(self) -> str:
        for key in ("pmid", "doi", "url"):
            value = self.identifiers.get(key) or (self.url if key == "url" else "")
            if value:
                return f"{key}:{value}"
        return ""

    @property
    def has_traceability(self) -> bool:
        return bool(self.traceability_id)


class EvidenceRegistry:
    def __init__(self) -> None:
        self.records: Dict[str, EvidenceRecord] = {}
        self.quarantined_records: Dict[str, EvidenceRecord] = {}

    def register(self, record: EvidenceRecord) -> EvidenceRecord:
        if not record.has_traceability:
            quarantined = EvidenceRecord(
                evidence_id=record.evidence_id,
                title=record.title,
                source=record.source,
                evidence_type=record.evidence_type,
                identifiers=dict(record.identifiers),
                publication_date=record.publication_date,
                url=record.url,
                status=EvidenceStatus.QUARANTINED,
                quality_label=record.quality_label,
                notes="Thiếu PMID/DOI/URL nên cách ly khỏi evidence chính.",
            )
            self.quarantined_records[quarantined.evidence_id] = quarantined
            return quarantined
        self.records[record.evidence_id] = record
        return record

    def add(
        self,
        *,
        title: str,
        source: str,
        evidence_type: str,
        identifiers: Optional[Mapping[str, str]] = None,
        publication_date: str = "",
        url: str = "",
        status: EvidenceStatus = EvidenceStatus.DRAFT,
        quality_label: str = "ungraded",
    ) -> EvidenceRecord:
        return self.register(EvidenceRecord(
            evidence_id=f"ev_{uuid4().hex}",
            title=title,
            source=source,
            evidence_type=evidence_type,
            identifiers=dict(identifiers or {}),
            publication_date=publication_date,
            url=url,
            status=status,
            quality_label=quality_label,
        ))

    def get(self, evidence_id: str) -> EvidenceRecord:
        if evidence_id in self.records:
            return self.records[evidence_id]
        if evidence_id in self.quarantined_records:
            return self.quarantined_records[evidence_id]
        raise KeyError(evidence_id)

    def verified_trace_ids(self) -> List[str]:
        return [record.traceability_id for record in self.records.values() if record.status == EvidenceStatus.VERIFIED]

    def all_main(self) -> Iterable[EvidenceRecord]:
        return self.records.values()
