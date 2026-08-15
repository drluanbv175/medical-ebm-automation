"""Lifecycle helper cho evidence record."""
from __future__ import annotations

from dataclasses import replace

from app.evidence.evidence_registry import EvidenceRecord, EvidenceStatus


def verify_evidence(record: EvidenceRecord) -> EvidenceRecord:
    if not record.has_traceability:
        return replace(record, status=EvidenceStatus.QUARANTINED, notes="Không thể verify vì thiếu truy nguyên")
    return replace(record, status=EvidenceStatus.VERIFIED)


def retract_evidence(record: EvidenceRecord, reason: str) -> EvidenceRecord:
    return replace(record, status=EvidenceStatus.RETRACTED, notes=reason)


def supersede_evidence(record: EvidenceRecord, replacement_id: str) -> EvidenceRecord:
    return replace(record, status=EvidenceStatus.SUPERSEDED, notes=f"Thay thế bởi {replacement_id}")
