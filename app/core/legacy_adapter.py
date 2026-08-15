"""Adapter không xâm lấn để bọc pipeline cũ bằng RunPacket V7."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from app.core.run_packet import InputCompleteness, Lane, PiiStatus, RiskLevel, RunPacket, new_run_packet


def packet_from_legacy_job(
    *,
    lane: Lane,
    objective: str,
    legacy_payload: Mapping[str, Any],
    trace_id: Optional[str] = None,
) -> RunPacket:
    """Tạo RunPacket từ payload cũ mà không thay đổi schema DB hiện hữu."""

    trace_ids = [trace_id] if trace_id else []
    return new_run_packet(
        lane=lane,
        objective=objective,
        inputs={"legacy_payload": dict(legacy_payload)},
        risk_level=RiskLevel.MODERATE,
        input_completeness=InputCompleteness.PARTIAL,
        pii_status=PiiStatus.NOT_ASSESSED,
        trace_ids=trace_ids,
        metadata={"adapter": "legacy_v1_to_v7"},
    )
