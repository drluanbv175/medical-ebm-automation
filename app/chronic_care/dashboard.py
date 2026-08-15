"""Read-only dashboard adapter cho Chronic Care Phase 3A."""
from __future__ import annotations

import threading
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.chronic_care.service import ChronicCareDashboardState, build_shadow_pilot_state


def build_chronic_care_readonly_snapshot() -> ChronicCareDashboardState:
    return build_shadow_pilot_state()


# SỬA 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11, phát hiện HIGH): cache
# CẤP TIẾN TRÌNH cho snapshot dashboard — xem lý do đầy đủ trong
# render_chronic_care_shadow_dashboard() bên dưới. Cố ý dùng biến module-level
# đơn giản thay vì st_module.cache_resource (thử ban đầu SAI: gọi
# cache_resource(...) BÊN TRONG hàm render tạo một wrapper lru_cache MỚI mỗi
# lần render chạy — cache rỗng lại từ đầu mỗi lần, không hề cache được gì cả;
# bắt được lỗi này bằng test_chronic_care_dashboard_seed_once.py trước khi commit).
_CACHED_SNAPSHOT: Optional[ChronicCareDashboardState] = None
# THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện MEDIUM):
# check-then-set trần (không khóa) ở trên là TOCTOU race thật trên route đã
# xác nhận CHẠY THẬT (app/dashboard/main.py tab 14, mỗi phiên bác sĩ là 1
# thread trong CÙNG tiến trình Streamlit) — 2 phiên rerun gần như đồng thời
# TRƯỚC khi biến toàn cục được gán có thể cùng thấy None, cùng gọi
# seed_synthetic_cases() độc lập, mỗi lần APPEND một lô dòng audit MỚI vào
# CÙNG file (AuditLogger mở "a") trước khi cache hội tụ về 1 snapshot — làm
# hỏng đúng mục tiêu "chỉ seed MỘT LẦN" của bản vá vòng 11. Khóa bằng
# threading.Lock (double-checked locking) — vẫn giữ nguyên lý do KHÔNG dùng
# st_module.cache_resource đã giải thích ở trên.
_CACHE_LOCK = threading.Lock()


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
    # SỬA 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11, phát hiện HIGH):
    # trước đây gọi build_chronic_care_readonly_snapshot() TRỰC TIẾP mỗi lần
    # hàm này chạy — và vì Streamlit rerun TOÀN BỘ script trên MỌI tương tác
    # widget ở CẢ 14 tab (không chỉ khi bác sĩ mở đúng tab này), mỗi lần rerun
    # tạo ChronicCareService() MỚI → seed_synthetic_cases() MỚI → hàng trăm
    # dòng audit event thật được APPEND vào data/processed/chronic_care_phase_
    # 3a_audit.jsonl (AuditLogger.log() mở file chế độ "a", không giới hạn) —
    # phình vô hạn trên đĩa mỗi lần bác sĩ tương tác dashboard, dù toàn bộ dữ
    # liệu chỉ là 30 ca TỔNG HỢP giống hệt nhau mỗi lần seed. Dùng cache
    # module-level (_CACHED_SNAPSHOT) để chỉ seed MỘT LẦN cho vòng đời tiến
    # trình (an toàn vì dữ liệu 100% tổng hợp/tĩnh, không phụ thuộc input
    # người dùng) — không đổi hành vi hiển thị, chỉ chặn việc seed lặp lại.
    global _CACHED_SNAPSHOT
    if _CACHED_SNAPSHOT is None:  # kiểm nhanh không khóa (đường phổ biến sau lần seed đầu)
        with _CACHE_LOCK:
            if _CACHED_SNAPSHOT is None:  # kiểm lại TRONG khóa — chặn race vòng 16
                _CACHED_SNAPSHOT = build_chronic_care_readonly_snapshot()
    snapshot = _CACHED_SNAPSHOT
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
