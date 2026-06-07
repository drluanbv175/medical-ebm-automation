"""Model thang điểm / công cụ lâm sàng.

Nguyên tắc chống bịa đặt: nếu công thức / cut-off CHƯA được xác minh nguồn,
trạng thái `update_status` để là "needs_verification" và KHÔNG tự bịa công thức.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalScore(Base):
    __tablename__ = "clinical_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    score_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    score_name: Mapped[str] = mapped_column(String(128), index=True)
    clinical_area: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    clinical_situation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    components: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    calculation_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_thresholds: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clinical_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contraindications_or_cautions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guideline_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_reviewed_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # verified | needs_verification | updated
    update_status: Mapped[str] = mapped_column(String(32), default="needs_verification")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
