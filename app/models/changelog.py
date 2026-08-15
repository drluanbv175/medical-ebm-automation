"""Model Change Log – ghi lại mọi thay đổi quan trọng, không mất dấu vết."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChangeLogEntry(Base):
    __tablename__ = "change_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    change_date: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    change_summary: Mapped[str] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    module: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), default="pipeline")  # logic/người tạo
    review_status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|reviewed
