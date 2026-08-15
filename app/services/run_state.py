"""Quản lý trạng thái lần chạy (watermark) cho cơ chế "mới tuần này".

Hai khái niệm bổ trợ nhau:
1. since_date (cửa sổ thời gian): chỉ LẤY bài mới từ API kể từ mốc này (hiệu quả + đúng trọng tâm).
2. first_seen_run_id (DB): trong số bài lấy về, bài nào LẦN ĐẦU vào kho mới là "mới" thật sự.

"Mới tuần này" = bản ghi có first_seen_run_id thuộc các lần chạy trong N ngày gần đây.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Set

from app.database import session_scope
from app.models import PipelineRun
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Mặc định: lần chạy ĐẦU TIÊN nhìn lùi 30 ngày (backfill); các lần sau lấy từ mốc lần trước.
DEFAULT_FIRST_LOOKBACK_DAYS = 30
# Đệm chồng lấp để không bỏ sót bài được index trễ.
OVERLAP_DAYS = 2


def _today() -> datetime:
    return datetime.now(timezone.utc)


def last_finished_run() -> Optional[PipelineRun]:
    with session_scope() as s:
        return (s.query(PipelineRun)
                .filter(PipelineRun.status == "ok")
                .order_by(PipelineRun.started_at.desc())
                .first())


def compute_since_date(window_days: Optional[int] = None) -> str:
    """Tính mốc since_date (YYYY-MM-DD) để lọc API ở chế độ live.

    - Nếu có lần chạy thành công trước: lấy từ ngày bắt đầu lần đó trừ OVERLAP_DAYS.
    - Nếu chưa từng chạy: nhìn lùi window_days (hoặc DEFAULT_FIRST_LOOKBACK_DAYS).
    """
    prev = last_finished_run()
    if prev and prev.started_at:
        base = prev.started_at - timedelta(days=OVERLAP_DAYS)
    else:
        lookback = window_days or DEFAULT_FIRST_LOOKBACK_DAYS
        base = _today() - timedelta(days=lookback)
    return base.date().isoformat()


def start_run(mode: str, window_days: Optional[int], since_date: Optional[str],
              until_date: Optional[str]) -> int:
    """Mở một bản ghi PipelineRun (status=running). Trả về run_id."""
    with session_scope() as s:
        run = PipelineRun(mode=mode, window_days=window_days, since_date=since_date,
                          until_date=until_date, status="running")
        s.add(run)
        s.flush()
        return run.id


def finish_run(run_id: int, *, total_fetched: int, new_items: int,
               new_actionable: int, new_drug_safety: int, stats: dict,
               status: str = "ok") -> None:
    with session_scope() as s:
        run = s.get(PipelineRun, run_id)
        if not run:
            return
        run.finished_at = _today()
        run.total_fetched = total_fetched
        run.new_items = new_items
        run.new_actionable = new_actionable
        run.new_drug_safety = new_drug_safety
        run.stats = stats
        run.status = status


def recent_run_ids(days: int = 7) -> Set[int]:
    """ID các lần chạy trong `days` ngày gần đây (để xác định 'mới tuần này')."""
    cutoff = _today() - timedelta(days=days)
    with session_scope() as s:
        rows = (s.query(PipelineRun.id)
                .filter(PipelineRun.started_at >= cutoff)
                .all())
        return {r[0] for r in rows}


def latest_run_id() -> Optional[int]:
    with session_scope() as s:
        row = s.query(PipelineRun.id).order_by(PipelineRun.id.desc()).first()
        return row[0] if row else None
