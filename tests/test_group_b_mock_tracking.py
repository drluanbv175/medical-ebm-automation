"""Nhóm B — truy vết mock: cờ is_mock không để dữ liệu demo lẫn vào khuyến cáo thật."""
from __future__ import annotations

from app.database import get_engine, session_scope
from app.models import EvidenceItem
from app.services.normalization import normalize
from app.sources.base import RawRecord


def test_normalize_maps_mock_flag():
    mock = normalize(RawRecord(source="x", title="demo", raw={"_mock": True}))
    live = normalize(RawRecord(source="x", title="real", raw={}))
    assert mock["is_mock"] is True
    assert live["is_mock"] is False


def test_evidence_items_has_is_mock_column():
    from sqlalchemy import inspect
    cols = {c["name"] for c in inspect(get_engine()).get_columns("evidence_items")}
    assert "is_mock" in cols


def test_build_weekly_excludes_mock_from_actionable():
    from app.reports.weekly_ebm import build_weekly_data
    titles = ("ZZ_REAL_actionable_item", "ZZ_DEMO_actionable_item")
    try:
        with session_scope() as s:
            for title, mock in [(titles[0], False), (titles[1], True)]:
                s.add(EvidenceItem(
                    source="t-grpB", title=title, is_primary_record=True,
                    is_actionable=True, actionable_reason="test",
                    classification="actionable", practice_change_score=70, is_mock=mock))
        # exclude_mock=True mô phỏng chế độ LIVE bất kể mode test toàn cục.
        data = build_weekly_data(exclude_mock=True)
        got = [r["title"] for r in data["actionable_checklist"]]
        assert titles[0] in got
        assert titles[1] not in got, "mock không được vào actionable ở chế độ live"
        assert data["mock_count"] >= 1
    finally:
        # Dọn rác để không làm bẩn DB session-scoped dùng chung.
        with session_scope() as s:
            for title in titles:
                for obj in s.query(EvidenceItem).filter(EvidenceItem.title == title).all():
                    s.delete(obj)
