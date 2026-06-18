"""Read-only dashboard adapter cho Chronic Care Phase 3A."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from app.chronic_care.service import ChronicCareDashboardState, build_shadow_pilot_state


def build_chronic_care_readonly_snapshot() -> ChronicCareDashboardState:
    return build_shadow_pilot_state()


def snapshot_to_rows(snapshot: ChronicCareDashboardState) -> Dict[str, List[Dict[str, Any]]]:
    return {
        "overview": [
            {"metric": "total_synthetic_enrollments", "value": snapshot.total_enrollments},
            {"metric": "open_tasks", "value": snapshot.open_tasks},
            {"metric": "overdue_tasks", "value": snapshot.overdue_tasks},
            {"metric": "physician_review_pending", "value": snapshot.physician_review_pending},
            {"metric": "care_plan_draft_pending", "value": snapshot.care_plan_draft_pending},
            {"metric": "post_discharge_synthetic_cases", "value": snapshot.post_discharge_synthetic_cases},
            {"metric": "quality_metrics_count", "value": snapshot.quality_metrics_count},
            {"metric": "shadow_mode_status", "value": snapshot.shadow_mode_status},
            {"metric": "production_block_status", "value": snapshot.production_block_status},
        ],
        "programs": [{"program": key, "count": value} for key, value in sorted(snapshot.enrollments_by_program.items())],
        "risk": [{"risk_label": key, "count": value} for key, value in sorted(snapshot.risk_counts.items())],
        "flags": [{"flag": key, "enabled": value} for key, value in sorted(snapshot.feature_flags.items())],
        "care_coordinator_queue": [dict(row) for row in snapshot.care_coordinator_queue],
        "physician_review_queue": [dict(row) for row in snapshot.physician_review_queue],
        "quality": [asdict(metric) for metric in snapshot.quality_metrics],
        "safety_counters": [{"counter": key, "value": value} for key, value in sorted(snapshot.safety_counters.items())],
    }


def render_chronic_care_shadow_dashboard(st_module) -> ChronicCareDashboardState:
    snapshot = build_chronic_care_readonly_snapshot()
    rows = snapshot_to_rows(snapshot)
    st_module.header("🫀 Chronic Care Shadow Pilot — Read-only")
    st_module.caption(
        "Synthetic shadow mode only: không clinical production, không patient-facing messaging, "
        "không kê đơn/đổi thuốc, không ghi EMR/HIS."
    )
    cols = st_module.columns(4)
    cols[0].metric("Synthetic enrollments", snapshot.total_enrollments)
    cols[1].metric("Open tasks", snapshot.open_tasks)
    cols[2].metric("Physician review", snapshot.physician_review_pending)
    cols[3].metric("Production", snapshot.production_block_status)

    if snapshot.production_block_status == "SHADOW PILOT BLOCKED":
        st_module.error("SHADOW PILOT BLOCKED")
    else:
        st_module.warning("Production blocked by design. Shadow mode synthetic only.")

    st_module.subheader("Feature flags")
    st_module.dataframe(rows["flags"], use_container_width=True, hide_index=True)

    st_module.subheader("Program overview")
    st_module.dataframe(rows["programs"], use_container_width=True, hide_index=True)

    st_module.subheader("Care coordinator queue")
    st_module.dataframe(rows["care_coordinator_queue"], use_container_width=True, hide_index=True)

    st_module.subheader("Physician review queue")
    st_module.dataframe(rows["physician_review_queue"], use_container_width=True, hide_index=True)

    st_module.subheader("Quality metrics")
    st_module.dataframe(rows["quality"], use_container_width=True, hide_index=True)

    st_module.subheader("Safety counters")
    st_module.dataframe(rows["safety_counters"], use_container_width=True, hide_index=True)
    return snapshot
