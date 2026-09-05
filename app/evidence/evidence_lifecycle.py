"""Lifecycle helper cho evidence record."""
from __future__ import annotations

from dataclasses import replace

from app.evidence.evidence_registry import EvidenceRecord, EvidenceStatus

# Trạng thái CUỐI của một evidence — một khi đã rút bài/bị thay thế thì đó là quyết
# định KHÔNG được lật ngược im lặng bằng cách gọi lại verify_evidence().
_TRANG_THAI_CUOI = frozenset({EvidenceStatus.RETRACTED, EvidenceStatus.SUPERSEDED})


def verify_evidence(record: EvidenceRecord) -> EvidenceRecord:
    """SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #85) — bản gốc không kiểm
    `record.status` HIỆN TẠI trước khi verify: gọi `verify_evidence()` trên một bản
    ghi ĐÃ RETRACTED/SUPERSEDED (nếu vẫn còn `has_traceability=True`, đúng trường hợp
    thường gặp — rút bài không xoá PMID/DOI) sẽ lật ngược thành VERIFIED, xoá dấu vết
    quyết định rút bài/thay thế đã có. `retract_evidence()`/`supersede_evidence()` gọi
    RIÊNG rồi cũng không có gì ngăn một lần gọi `verify_evidence()` sau đó ghi đè lại.
    Sửa: từ chối verify một bản ghi đã ở trạng thái CUỐI — báo lỗi rõ ràng thay vì
    lật ngược im lặng."""
    if record.status in _TRANG_THAI_CUOI:
        raise ValueError(
            f"Không thể verify lại evidence {record.evidence_id!r} — đã ở trạng thái "
            f"CUỐI {record.status.value} (rút bài/thay thế không được lật ngược im lặng)"
        )
    if not record.has_traceability:
        return replace(record, status=EvidenceStatus.QUARANTINED, notes="Không thể verify vì thiếu truy nguyên")
    return replace(record, status=EvidenceStatus.VERIFIED)


def retract_evidence(record: EvidenceRecord, reason: str) -> EvidenceRecord:
    return replace(record, status=EvidenceStatus.RETRACTED, notes=reason)


def supersede_evidence(record: EvidenceRecord, replacement_id: str) -> EvidenceRecord:
    return replace(record, status=EvidenceStatus.SUPERSEDED, notes=f"Thay thế bởi {replacement_id}")
