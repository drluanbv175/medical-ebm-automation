from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from app.chronic_care.dashboard import build_chronic_care_readonly_snapshot, snapshot_to_rows
from app.chronic_care.migration import CHRONIC_CARE_TABLES, build_chronic_care_migration_plan, create_chronic_care_schema
from app.chronic_care.service import ChronicCareService
from app.chronic_care.synthetic_cases import build_synthetic_case_pack


def test_create_synthetic_enrollment_and_initial_review_task() -> None:
    service = ChronicCareService()
    case = build_synthetic_case_pack()[0]
    enrollment = service.create_enrollment(case)
    review = service.create_review(enrollment.id, "INITIAL_REVIEW", "initial shadow review")
    task = service.create_task(enrollment.id, "CARE_PLAN_REVIEW", "MEDIUM", "care_coordinator")

    assert enrollment.patient_reference_id.startswith("SYN-")
    assert review.physician_confirmation_required is True
    assert task.status == "OPEN"
    assert len(service.audit_trail.events) >= 3


def test_overdue_task_completion_and_escalation() -> None:
    service = ChronicCareService()
    service.seed_synthetic_cases()
    overdue = next(task for task in service.tasks.values() if task.task_type == "REVIEW_OVERDUE_CASE")
    service.complete_task(overdue.id)
    assert service.tasks[overdue.id].status == "COMPLETED"

    another = next(task for task in service.tasks.values() if task.status == "OPEN")
    service.escalate_task(another.id)
    assert service.tasks[another.id].assigned_role == "physician"
    assert service.tasks[another.id].escalation_level == 1


def test_risk_draft_physician_approve_and_reject() -> None:
    service = ChronicCareService()
    service.seed_synthetic_cases()
    red = next(draft for draft in service.risk_drafts.values() if draft.risk_label == "RED")
    approved = service.review_risk_draft(red.id, reviewer_role="physician", approve=True)
    assert approved.risk_status == "APPROVED_FOR_SHADOW"

    yellow = next(draft for draft in service.risk_drafts.values() if draft.risk_label == "YELLOW")
    rejected = service.review_risk_draft(yellow.id, reviewer_role="physician", approve=False, note="needs more context")
    assert rejected.risk_status == "REJECTED"
    assert rejected.rejection_reason == "needs more context"


def test_care_plan_draft_blocks_missing_evidence_and_approves_shadow_when_complete() -> None:
    service = ChronicCareService()
    service.seed_synthetic_cases()
    blocked = next(plan for plan in service.plan_drafts.values() if plan.status == "BLOCKED")
    with pytest.raises(PermissionError, match="EVIDENCE_INSUFFICIENT_OR_UNVERIFIED"):
        service.approve_care_plan_draft(blocked.id)

    complete = next(plan for plan in service.plan_drafts.values() if plan.status == "PENDING_REVIEW")
    approved = service.approve_care_plan_draft(complete.id)
    assert approved.status == "APPROVED_FOR_SHADOW"


def test_quality_metrics_dashboard_and_aggregate_export() -> None:
    service = ChronicCareService()
    service.seed_synthetic_cases()
    state = service.dashboard_state()
    rows = snapshot_to_rows(state)
    export_json = service.export_aggregate_json()
    export_csv = service.export_aggregate_csv()

    assert state.total_enrollments == 30
    assert state.quality_metrics_count >= 10
    assert rows["care_coordinator_queue"]
    assert "quality_metrics" in export_json
    assert "metric_code" in export_csv


def test_dashboard_snapshot_renders_synthetic_shadow_state() -> None:
    state = build_chronic_care_readonly_snapshot()
    assert state.total_enrollments == 30
    assert state.feature_flags["v7_clinical_release"] is False
    assert state.production_block_status in {"production_blocked_by_design", "SHADOW PILOT BLOCKED"}


def test_chronic_care_migration_plan_is_non_destructive() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    plan = build_chronic_care_migration_plan(engine)
    assert plan.destructive is False
    assert set(plan.missing_tables) == set(CHRONIC_CARE_TABLES)

    created = create_chronic_care_schema(engine)
    assert created.destructive is False
    assert set(created.missing_tables) == set(CHRONIC_CARE_TABLES)
    after = build_chronic_care_migration_plan(engine)
    assert after.missing_tables == []
