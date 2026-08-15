"""ORM governance V7.

Các bảng này phục vụ shadow/review mode. Không tự động tạo trong `init_db()` để tránh
thay đổi production DB khi chưa có quyết định migration; dùng migration helper Phase 2A.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunPacketRecord(Base):
    __tablename__ = "run_packets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    run_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    request_id: Mapped[str] = mapped_column(String(80), index=True)
    lane: Mapped[str] = mapped_column(String(32), index=True)
    objective: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32), default="moderate")
    input_completeness: Mapped[str] = mapped_column(String(40), default="minimal")
    pii_status: Mapped[str] = mapped_column(String(32), default="not_assessed")
    approval_status: Mapped[str] = mapped_column(String(40), default="pending_physician")
    state: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    trace_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    feature_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    approval_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    item_type: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    reviewer_role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reviewer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    event_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    actor: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(48), default="recorded", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class IncidentRecord(Base):
    __tablename__ = "incident_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    incident_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    notes_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class EvidenceRecordV2(Base):
    __tablename__ = "evidence_records_v2"
    __table_args__ = (UniqueConstraint("traceability_id", name="uq_evidence_records_v2_traceability"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    evidence_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    traceability_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120))
    evidence_type: Mapped[str] = mapped_column(String(64))
    identifiers_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(48), default="UNVERIFIED", index=True)
    lifecycle_status: Mapped[str] = mapped_column(String(48), default="draft", index=True)
    status: Mapped[str] = mapped_column(String(48), default="draft", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    verification_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    history_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ClaimRecordModel(Base):
    __tablename__ = "claim_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    claim_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    text: Mapped[str] = mapped_column(Text)
    evidence_ids_json: Mapped[list] = mapped_column(JSON)
    claim_type: Mapped[str] = mapped_column(String(48), default="clinical")
    grade_label: Mapped[str] = mapped_column(String(48), default="ungraded")
    grade_source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(48), default="draft", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class RecommendationCardRecord(Base):
    __tablename__ = "recommendation_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    card_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    claim_id: Mapped[str] = mapped_column(String(80), index=True)
    headline: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    monitoring: Mapped[str] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(48), default="pending_physician", index=True)
    status: Mapped[str] = mapped_column(String(48), default="draft", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    patient_facing_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ClinicalDecisionRecord(Base):
    __tablename__ = "clinical_decision_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    decision_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    case_context_hash: Mapped[str] = mapped_column(String(128))
    decision_summary: Mapped[str] = mapped_column(Text)
    safety_flags_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    evidence_ids_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    approval_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(48), default="draft", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ResearchLockRecord(Base):
    __tablename__ = "research_lock_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    lock_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    project_id: Mapped[str] = mapped_column(String(80), index=True)
    lock_type: Mapped[str] = mapped_column(String(48))
    hash_value: Mapped[str] = mapped_column(String(128))
    locked_by: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(48), default="locked", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ReleaseManifestRecord(Base):
    __tablename__ = "release_manifests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    release_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    channel: Mapped[str] = mapped_column(String(80))
    payload_hash: Mapped[str] = mapped_column(String(128))
    approval_id: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(48), default="staged")
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ExportManifestRecord(Base):
    __tablename__ = "export_manifests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    manifest_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    system_version: Mapped[str] = mapped_column(String(40))
    environment: Mapped[str] = mapped_column(String(40), default="review")
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    safe_to_upload: Mapped[bool] = mapped_column(Boolean, default=False)
    files_json: Mapped[dict] = mapped_column(JSON)
    sha256: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(48), default="draft")
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class FeatureFlagAuditRecord(Base):
    __tablename__ = "feature_flag_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    flag_name: Mapped[str] = mapped_column(String(100), index=True)
    old_value: Mapped[bool] = mapped_column(Boolean)
    new_value: Mapped[bool] = mapped_column(Boolean)
    changed_by: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(48), default="recorded", index=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class CitationVerificationRecord(Base):
    __tablename__ = "citation_verification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    verification_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    evidence_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    claim_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    traceability_id: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(48), default="UNVERIFIED", index=True)
    verification_method: Mapped[str] = mapped_column(String(80), default="source_lookup")
    last_verified_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    checks_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reasons_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    source_metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(String(80), default="system")
    environment: Mapped[str] = mapped_column(String(40), default="review", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
