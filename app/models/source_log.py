"""Model Source Log – nhật ký mỗi lần gọi nguồn/API (Tab 8 dashboard)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceLog(Base):
    __tablename__ = "source_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    api_endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="ok")  # ok|degraded|error|mock
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(16), default="live")  # live|mock
