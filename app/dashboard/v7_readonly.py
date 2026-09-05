"""Dashboard V7 read-only cho shadow/review mode."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Mapping

from sqlalchemy import inspect, text

from app.config import settings
from app.core.feature_flags import merge_feature_flags
from app.database import get_engine, session_scope
from app.governance.migrations import GOVERNANCE_TABLES


@dataclass(frozen=True)
class V7ReadOnlySnapshot:
    environment: str
    feature_flags: Mapping[str, bool]
    schema_ready: bool
    shadow_mode_status: str
    last_updated: str
    run_id: str = "not_available"
    release_id: str = "not_available"
    table_counts: Mapping[str, int] = field(default_factory=dict)
    blocked_reasons: List[str] = field(default_factory=list)


def build_v7_readonly_snapshot() -> V7ReadOnlySnapshot:
    engine = get_engine()
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing_tables = [table for table in GOVERNANCE_TABLES if table not in existing]
    flags = merge_feature_flags({
        "v7_read_only_dashboard": True,
        "v7_shadow_mode": False,
        "v7_clinical_release": False,
        "v7_patient_education_export": False,
        "v7_emr_write": False,
        "v7_production_pathway": False,
    })
    counts: Dict[str, int] = {}
    if not missing_tables:
        with session_scope() as session:
            for table in GOVERNANCE_TABLES:
                counts[table] = int(session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
    blocked = [
        "clinical_release_disabled",
        "patient_education_export_disabled",
        "emr_write_disabled",
        "production_pathway_disabled",
    ]
    if missing_tables:
        blocked.append("governance_schema_not_migrated")
    # GHI CHÚ 2026-09-05 (Workflow đối kháng đa-agent, vòng 12) — nhánh
    # "shadow_mode_enabled_read_only" ở dưới KHÔNG BAO GIỜ đạt được với cách nối dây
    # hiện tại: `merge_feature_flags()` ở trên tự ép `"v7_shadow_mode": False` làm
    # override, và không nơi nào khác trong repo (kể cả app/config.py) đọc một giá trị
    # THẬT cho cờ này từ env/DB/settings — grep xác nhận `v7_shadow_mode` chỉ xuất hiện ở
    # `DEFAULT_FEATURE_FLAGS` (cũng False) và đúng 2 dòng này. Khác các cờ rủi ro cao
    # khác bị ép False CÓ CHỦ Ý ở trên (clinical_release/emr_write/production_pathway —
    # đúng ý "trang này chỉ báo sẵn sàng schema, không phải cổng bật rủi ro thật"), shadow
    # mode CHÍNH LÀ năng lực trang này được sinh ra để báo trạng thái — tự ép về False làm
    # `shadow_mode_status` vĩnh viễn kẹt ở "ready_flag_off", và
    # `tests/test_phase_2a_dashboard_readonly.py` chấp nhận cả hai giá trị nên không bắt
    # được việc nhánh kia chết. Không tự bịa nguồn đọc thật ở đây (chưa có cơ chế cấu
    # hình động nào cho feature flag trong toàn repo — bịa sẽ là phát minh kiến trúc mới
    # ngoài phạm vi một lần vá lỗi, cùng nguyên tắc đã áp cho EBM-V7-P009 ở
    # app/core/policy_engine.py vòng 11).
    shadow_status = "ready_flag_off"
    if flags.get("v7_shadow_mode") is True and not missing_tables:
        shadow_status = "shadow_mode_enabled_read_only"
    return V7ReadOnlySnapshot(
        environment=settings.app_env if settings.app_env else "local",
        feature_flags=flags,
        schema_ready=not missing_tables,
        shadow_mode_status=shadow_status,
        last_updated=datetime.now(timezone.utc).isoformat(),
        table_counts=counts,
        blocked_reasons=blocked,
    )


def render_v7_readonly_dashboard(st_module) -> V7ReadOnlySnapshot:
    snapshot = build_v7_readonly_snapshot()
    st_module.header("🧭 V7 Shadow Governance — Read-only")
    st_module.caption(
        "Chế độ chỉ đọc cho Phase 2A: không auto-apply, không kê đơn, không gửi lời dặn, không ghi EMR/HIS."
    )
    cols = st_module.columns(4)
    cols[0].metric("Environment", snapshot.environment)
    cols[1].metric("Governance schema", "ready" if snapshot.schema_ready else "pending")
    cols[2].metric("Clinical release", "blocked")
    cols[3].metric("Shadow mode", snapshot.shadow_mode_status)

    st_module.subheader("Feature Flag Status")
    flag_rows = [{"flag": key, "enabled": value} for key, value in sorted(snapshot.feature_flags.items())]
    st_module.dataframe(flag_rows, use_container_width=True, hide_index=True)

    st_module.subheader("Governance Tables")
    if snapshot.table_counts:
        st_module.dataframe(
            [{"table": table, "rows": count} for table, count in snapshot.table_counts.items()],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st_module.info("Governance schema chưa migrate; tab vẫn read-only và không tạo bảng tự động.")

    st_module.subheader("Blocked Reasons")
    st_module.dataframe(
        [{"blocked_reason": reason} for reason in snapshot.blocked_reasons],
        use_container_width=True,
        hide_index=True,
    )

    st_module.subheader("Required Screens")
    screens = [
        "Run Monitor",
        "Approval Inbox",
        "Evidence Registry",
        "Claim Registry",
        "Citation Verification Status",
        "Evidence Freshness",
        "Conflict Queue",
        "Clinical Safety Queue",
        "Clinical Decision Record Explorer",
        "Research Lock Status",
        "Incident Center",
        "Feature Flag Status",
        "Shadow Mode Status",
        "ChatGPT Export Safety",
        "Shadow Pilot Overview",
        "Case Queue",
        "Safety Gate Summary",
        "Citation Status",
        "Physician Override Summary",
        "Blocked Recommendation Reasons",
        "Source Health",
        "ResearchOS Pilot Status",
        "Pilot Pack Status",
        "Evidence Verification Coverage",
        "Pathway Validation Results",
        "Synthetic Vignette Metrics",
        "Shadow Review Queue",
        "Blocked Release Reasons",
        "ResearchOS Metadata Pilot",
        "Hypertension Pack Approval Status",
        "Evidence Dossier Status",
        "Claim Verification Coverage",
        "Unverified Claim Queue",
        "Conflict Register",
        "Freshness / Retraction Status",
        "Physician Approval Status",
        "Shadow Pilot Readiness",
        "Stop Criteria Status",
        "ResearchOS Metadata Readiness",
    ]
    screen_rows = [
        {
            "screen": screen,
            "mode": "read-only",
            "environment": snapshot.environment,
            "approval_status": "pending_physician_or_not_applicable",
            "citation_status": "visible_not_editable",
            "freshness_status": "visible_not_editable",
            "blocked_reason": "; ".join(snapshot.blocked_reasons),
            "feature_flags": ", ".join(
                f"{name}={value}" for name, value in sorted(snapshot.feature_flags.items())
            ),
            "shadow_mode": snapshot.shadow_mode_status,
            "last_updated": snapshot.last_updated,
            "run_id": snapshot.run_id,
            "release_id": snapshot.release_id,
        }
        for screen in screens
    ]
    st_module.dataframe(screen_rows, use_container_width=True, hide_index=True)
    return snapshot
