"""SQLAlchemy models cho Chronic Care Phase 3A.

Không import vào `init_db()` để tránh tự migrate production. Dùng migration helper riêng.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChronicCareEnrollmentRecord(Base):
    __tablename__ = "chronic_care_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    patient_reference_id: Mapped[str] = mapped_column(String(80), index=True)
    program_code: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    discharged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    discharge_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_physician_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    assigned_care_coordinator_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    current_risk_status: Mapped[str] = mapped_column(String(24), default="UNASSESSED", index=True)
    next_review_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChronicCareReviewRecord(Base):
    __tablename__ = "chronic_care_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    enrollment_id: Mapped[str] = mapped_column(String(80), index=True)
    review_type: Mapped[str] = mapped_column(String(80), index=True)
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    review_reason: Mapped[str] = mapped_column(Text)
    review_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    physician_confirmation_required: Mapped[str] = mapped_column(String(8), default="true")
    physician_confirmed_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    physician_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChronicCareRiskDraftRecord(Base):
    __tablename__ = "chronic_care_risk_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    risk_draft_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    enrollment_id: Mapped[str] = mapped_column(String(80), index=True)
    risk_label: Mapped[str] = mapped_column(String(24), index=True)
    risk_status: Mapped[str] = mapped_column(String(40), default="PENDING_REVIEW", index=True)
    risk_factors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    trigger_summary: Mapped[str] = mapped_column(Text)
    suggested_non_clinical_actions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    requires_physician_review: Mapped[str] = mapped_column(String(8), default="true")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChronicCareTaskRecord(Base):
    __tablename__ = "chronic_care_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    enrollment_id: Mapped[str] = mapped_column(String(80), index=True)
    task_type: Mapped[str] = mapped_column(String(80), index=True)
    priority: Mapped[str] = mapped_column(String(24), index=True)
    status: Mapped[str] = mapped_column(String(40), default="OPEN", index=True)
    assigned_role: Mapped[str] = mapped_column(String(80), index=True)
    assigned_user_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completion_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChronicCarePlanDraftRecord(Base):
    __tablename__ = "chronic_care_plan_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_draft_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    enrollment_id: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    problem_list_reference: Mapped[str] = mapped_column(Text)
    goal_summary: Mapped[str] = mapped_column(Text)
    follow_up_summary: Mapped[str] = mapped_column(Text)
    pending_review_items: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    clinical_content_reference_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    claim_reference_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    evidence_reference_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    physician_review_required: Mapped[str] = mapped_column(String(8), default="true")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChronicCareTimelineEventRecord(Base):
    __tablename__ = "chronic_care_timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    enrollment_id: Mapped[str] = mapped_column(String(80), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_type: Mapped[str] = mapped_column(String(80))
    source_reference_id: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ChronicCareQualityMetricRecord(Base):
    __tablename__ = "chronic_care_quality_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    metric_code: Mapped[str] = mapped_column(String(80), index=True)
    metric_name: Mapped[str] = mapped_column(Text)
    metric_category: Mapped[str] = mapped_column(String(80), index=True)
    numerator: Mapped[int] = mapped_column(Integer)
    denominator: Mapped[int] = mapped_column(Integer)
    value: Mapped[float] = mapped_column(Float)
    measurement_period_start: Mapped[datetime] = mapped_column(DateTime)
    measurement_period_end: Mapped[datetime] = mapped_column(DateTime)
    program_code: Mapped[str] = mapped_column(String(80), default="ALL")
    environment: Mapped[str] = mapped_column(String(40), default="synthetic_shadow", index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    generated_by: Mapped[str] = mapped_column(String(80), default="system")
    version: Mapped[int] = mapped_column(Integer, default=1)
