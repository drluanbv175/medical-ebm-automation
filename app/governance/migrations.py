"""Migration helper an toàn cho governance V7."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import Engine, inspect
from sqlalchemy.schema import CreateTable

from app.database import Base, get_engine
from app.models import governance_v7  # noqa: F401

MIGRATION_ID = "v7_phase_2a_governance_20260618"
GOVERNANCE_TABLES = [
    "run_packets",
    "approval_records",
    "audit_events",
    "incident_records",
    "evidence_records_v2",
    "claim_records",
    "recommendation_cards",
    "clinical_decision_records",
    "research_lock_records",
    "release_manifests",
    "export_manifests",
    "feature_flag_audit",
    "citation_verification_records",
]


@dataclass(frozen=True)
class MigrationPlan:
    migration_id: str
    missing_tables: List[str]
    sql: List[str]
    destructive: bool = False

    @property
    def ready_for_dry_run(self) -> bool:
        return not self.destructive


def build_governance_migration_plan(engine: Optional[Engine] = None) -> MigrationPlan:
    engine = engine or get_engine()
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    metadata_tables = Base.metadata.tables
    missing = [name for name in GOVERNANCE_TABLES if name not in existing]
    sql = [
        str(CreateTable(metadata_tables[name]).compile(engine)).strip() + ";"
        for name in missing
    ]
    return MigrationPlan(migration_id=MIGRATION_ID, missing_tables=missing, sql=sql)


def create_governance_schema(engine: Optional[Engine] = None) -> MigrationPlan:
    """Tạo bảng governance còn thiếu trên database được truyền vào.

    Chỉ dùng cho test/dev/dry-run đã chỉ định engine. Không tự gọi trong `init_db()`.
    """

    engine = engine or get_engine()
    plan = build_governance_migration_plan(engine)
    if plan.missing_tables:
        Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in plan.missing_tables])
    return plan
