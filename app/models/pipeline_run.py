"""Model lịch sử mỗi lần chạy pipeline – nền tảng cho watermark "mới tuần này"."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mode: Mapped[str] = mapped_column(String(16), default="mock")        # live|mock
    window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    since_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    until_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_fetched: Mapped[int] = mapped_column(Integer, default=0)
    new_items: Mapped[int] = mapped_column(Integer, default=0)
    new_actionable: Mapped[int] = mapped_column(Integer, default=0)
    new_drug_safety: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="running")   # running|ok|error
    stats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
