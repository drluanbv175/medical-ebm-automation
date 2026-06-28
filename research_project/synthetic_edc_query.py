"""
R2.0 Synthetic EDC Query — Vòng đời truy vấn, hiệu chỉnh có kiểm soát, độ lệch giao thức.

Chỉ dùng trong harness kiểm thử offline tổng hợp.
KHÔNG xử lý dữ liệu nghiên cứu thật hoặc PII.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from research_project.synthetic_edc_core import DISCLAIMER_EDC


# ── Trạng thái truy vấn ───────────────────────────────────────────────────

class QueryStatus(str, Enum):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


# ── Truy vấn dữ liệu ──────────────────────────────────────────────────────

@dataclass
class EDCQuery:
    """Một truy vấn dữ liệu trong vòng đời EDC."""

    query_id: str
    record_id: str
    field: str
    message: str
    raised_by: str
    raised_at_utc: str
    status: QueryStatus = QueryStatus.OPEN
    answer: Optional[str] = None
    answered_by: Optional[str] = None
    answered_at_utc: Optional[str] = None
    closed_by: Optional[str] = None
    closed_at_utc: Optional[str] = None
    cancellation_reason: Optional[str] = None
    disclaimer: str = DISCLAIMER_EDC

    def __post_init__(self) -> None:
        if not self.query_id:
            raise ValueError("query_id must be non-empty")
        if not self.record_id:
            raise ValueError("record_id must be non-empty")
        if not self.field:
            raise ValueError("field must be non-empty")
        if not self.message:
            raise ValueError("message must be non-empty")
        if not self.raised_by:
            raise ValueError("raised_by must be non-empty")


class QueryLifecycleManager:
    """
    Quản lý vòng đời truy vấn EDC: mở → trả lời → đóng (hoặc hủy).
    """

    def __init__(self) -> None:
        self._queries: Dict[str, EDCQuery] = {}

    def raise_query(
        self,
        record_id: str,
        field: str,
        message: str,
        raised_by: str,
        raised_at_utc: str,
    ) -> EDCQuery:
        """Mở một truy vấn mới."""
        query = EDCQuery(
            query_id=str(uuid.uuid4()),
            record_id=record_id,
            field=field,
            message=message,
            raised_by=raised_by,
            raised_at_utc=raised_at_utc,
        )
        self._queries[query.query_id] = query
        return query

    def answer_query(
        self,
        query_id: str,
        answer: str,
        answered_by: str,
        answered_at_utc: str,
    ) -> EDCQuery:
        """Trả lời một truy vấn đang OPEN."""
        q = self._get(query_id)
        if q.status != QueryStatus.OPEN:
            raise ValueError(f"Query {query_id} is not OPEN (status={q.status})")
        if not answer:
            raise ValueError("answer must be non-empty")
        if not answered_by:
            raise ValueError("answered_by must be non-empty")
        q.status = QueryStatus.ANSWERED
        q.answer = answer
        q.answered_by = answered_by
        q.answered_at_utc = answered_at_utc
        return q

    def close_query(
        self,
        query_id: str,
        closed_by: str,
        closed_at_utc: str,
    ) -> EDCQuery:
        """Đóng một truy vấn đã được trả lời."""
        q = self._get(query_id)
        if q.status != QueryStatus.ANSWERED:
            raise ValueError(f"Query {query_id} must be ANSWERED before closing")
        if not closed_by:
            raise ValueError("closed_by must be non-empty")
        q.status = QueryStatus.CLOSED
        q.closed_by = closed_by
        q.closed_at_utc = closed_at_utc
        return q

    def cancel_query(
        self,
        query_id: str,
        cancelled_by: str,
        reason: str,
    ) -> EDCQuery:
        """Hủy một truy vấn (chỉ được hủy khi OPEN hoặc ANSWERED)."""
        q = self._get(query_id)
        if q.status == QueryStatus.CLOSED:
            raise ValueError(f"Query {query_id} is already CLOSED — cannot cancel")
        if not reason:
            raise ValueError("cancellation reason must be non-empty")
        q.status = QueryStatus.CANCELLED
        q.cancellation_reason = reason
        q.closed_by = cancelled_by
        return q

    def queries_for_record(self, record_id: str) -> List[EDCQuery]:
        return [q for q in self._queries.values() if q.record_id == record_id]

    def open_queries(self) -> List[EDCQuery]:
        return [q for q in self._queries.values() if q.status == QueryStatus.OPEN]

    def get_query(self, query_id: str) -> EDCQuery:
        return self._get(query_id)

    def _get(self, query_id: str) -> EDCQuery:
        if query_id not in self._queries:
            raise KeyError(f"query_id not found: {query_id}")
        return self._queries[query_id]

    @property
    def total_queries(self) -> int:
        return len(self._queries)


# ── Hiệu chỉnh có kiểm soát ───────────────────────────────────────────────

@dataclass
class CorrectionEntry:
    """Một lần hiệu chỉnh có kiểm soát trên bản ghi EDC."""

    correction_id: str
    record_id: str
    field: str
    old_value: object
    new_value: object
    reason: str
    actor_id: str
    corrected_at_utc: str
    query_id: Optional[str] = None
    disclaimer: str = DISCLAIMER_EDC

    def __post_init__(self) -> None:
        if not self.correction_id:
            raise ValueError("correction_id must be non-empty")
        if not self.record_id:
            raise ValueError("record_id must be non-empty")
        if not self.field:
            raise ValueError("field must be non-empty")
        if not self.reason:
            raise ValueError("reason must be non-empty — controlled correction requires reason")
        if not self.actor_id:
            raise ValueError("actor_id must be non-empty")


class CorrectionManager:
    """
    Quản lý hiệu chỉnh có kiểm soát — mỗi thay đổi phải có lý do rõ ràng.
    """

    def __init__(self) -> None:
        self._corrections: Dict[str, CorrectionEntry] = {}

    def record_correction(
        self,
        record_id: str,
        field: str,
        old_value: object,
        new_value: object,
        reason: str,
        actor_id: str,
        corrected_at_utc: str,
        query_id: Optional[str] = None,
    ) -> CorrectionEntry:
        """Ghi nhận một hiệu chỉnh có kiểm soát; lý do là bắt buộc."""
        correction = CorrectionEntry(
            correction_id=str(uuid.uuid4()),
            record_id=record_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            actor_id=actor_id,
            corrected_at_utc=corrected_at_utc,
            query_id=query_id,
        )
        self._corrections[correction.correction_id] = correction
        return correction

    def corrections_for_record(self, record_id: str) -> List[CorrectionEntry]:
        return [c for c in self._corrections.values() if c.record_id == record_id]

    def corrections_for_field(self, record_id: str, field: str) -> List[CorrectionEntry]:
        return [
            c for c in self._corrections.values()
            if c.record_id == record_id and c.field == field
        ]

    @property
    def total_corrections(self) -> int:
        return len(self._corrections)


# ── Độ lệch giao thức ─────────────────────────────────────────────────────

class DeviationSeverity(str, Enum):
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


@dataclass
class ProtocolDeviation:
    """Một độ lệch giao thức được ghi nhận trong nghiên cứu."""

    deviation_id: str
    record_id: str
    description: str
    severity: DeviationSeverity
    reported_by: str
    reported_at_utc: str
    impact_on_subject: str
    corrective_action: str
    disclaimer: str = DISCLAIMER_EDC

    def __post_init__(self) -> None:
        if not self.deviation_id:
            raise ValueError("deviation_id must be non-empty")
        if not self.description:
            raise ValueError("description must be non-empty")
        if not self.corrective_action:
            raise ValueError("corrective_action must be non-empty")


class DeviationRegistry:
    """Đăng ký độ lệch giao thức."""

    def __init__(self) -> None:
        self._deviations: Dict[str, ProtocolDeviation] = {}

    def record_deviation(
        self,
        record_id: str,
        description: str,
        severity: DeviationSeverity,
        reported_by: str,
        reported_at_utc: str,
        impact: str,
        corrective_action: str,
    ) -> ProtocolDeviation:
        deviation = ProtocolDeviation(
            deviation_id=str(uuid.uuid4()),
            record_id=record_id,
            description=description,
            severity=severity,
            reported_by=reported_by,
            reported_at_utc=reported_at_utc,
            impact_on_subject=impact,
            corrective_action=corrective_action,
        )
        self._deviations[deviation.deviation_id] = deviation
        return deviation

    def deviations_for_record(self, record_id: str) -> List[ProtocolDeviation]:
        return [d for d in self._deviations.values() if d.record_id == record_id]

    def major_or_critical(self) -> List[ProtocolDeviation]:
        return [
            d for d in self._deviations.values()
            if d.severity in (DeviationSeverity.MAJOR, DeviationSeverity.CRITICAL)
        ]

    @property
    def total_deviations(self) -> int:
        return len(self._deviations)
