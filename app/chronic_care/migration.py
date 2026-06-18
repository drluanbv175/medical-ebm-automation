"""Migration helper không phá hủy cho Chronic Care Phase 3A."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import Engine, inspect
from sqlalchemy.schema import CreateTable

from app.chronic_care import models  # noqa: F401
from app.database import Base, get_engine

MIGRATION_ID = "phase_3a_chronic_care_shadow_20260618"
CHRONIC_CARE_TABLES = [
    "chronic_care_enrollments",
    "chronic_care_reviews",
    "chronic_care_risk_drafts",
    "chronic_care_tasks",
    "chronic_care_plan_drafts",
    "chronic_care_timeline_events",
    "chronic_care_quality_metrics",
]


@dataclass(frozen=True)
class ChronicCareMigrationPlan:
    migration_id: str
    missing_tables: List[str]
    sql: List[str]
    destructive: bool = False

    @property
    def ready_for_dry_run(self) -> bool:
        return not self.destructive


def build_chronic_care_migration_plan(engine: Optional[Engine] = None) -> ChronicCareMigrationPlan:
    engine = engine or get_engine()
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    metadata_tables = Base.metadata.tables
    missing = [name for name in CHRONIC_CARE_TABLES if name not in existing]
    sql = [
        str(CreateTable(metadata_tables[name]).compile(engine)).strip() + ";"
        for name in missing
    ]
    return ChronicCareMigrationPlan(migration_id=MIGRATION_ID, missing_tables=missing, sql=sql)


def create_chronic_care_schema(engine: Optional[Engine] = None) -> ChronicCareMigrationPlan:
    """Tạo bảng Phase 3A trên test/dev DB đã chỉ định. Không gọi trong init_db()."""

    engine = engine or get_engine()
    plan = build_chronic_care_migration_plan(engine)
    if plan.missing_tables:
        Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in plan.missing_tables])
    return plan
