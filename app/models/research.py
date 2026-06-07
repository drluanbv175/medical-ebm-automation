"""Model dự án nghiên cứu y khoa."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    project_title: Mapped[str] = mapped_column(Text)
    short_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    principal_investigator: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    study_design: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    secondary_objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    secondary_outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Trạng thái các giai đoạn (vd: not_started|in_progress|done|delayed)
    data_collection_status: Mapped[str] = mapped_column(String(32), default="not_started")
    ethics_status: Mapped[str] = mapped_column(String(32), default="not_started")
    protocol_status: Mapped[str] = mapped_column(String(32), default="not_started")
    questionnaire_status: Mapped[str] = mapped_column(String(32), default="not_started")
    spss_status: Mapped[str] = mapped_column(String(32), default="not_started")
    analysis_status: Mapped[str] = mapped_column(String(32), default="not_started")
    report_status: Mapped[str] = mapped_column(String(32), default="not_started")
    manuscript_status: Mapped[str] = mapped_column(String(32), default="not_started")

    next_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    missing_documents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    deadline: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    linked_evidence_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
