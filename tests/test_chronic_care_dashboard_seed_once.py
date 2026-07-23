# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 11 (2026-07-23, dimension
third_chronic_care_python_system, phát hiện HIGH):
render_chronic_care_shadow_dashboard() trước đây gọi
build_chronic_care_readonly_snapshot() (→ ChronicCareService()
→ seed_synthetic_cases() → hàng trăm audit event ghi thật vào
data/processed/chronic_care_phase_3a_audit.jsonl) MỖI LẦN hàm này chạy —
và vì app/dashboard/main.py (tab 14, "Chronic Care Shadow Pilot") chạy qua
Streamlit rerun TOÀN BỘ script trên MỌI tương tác widget ở CẢ 14 tab, audit
log phình vô hạn trên đĩa mỗi lần bác sĩ tương tác dashboard dù dữ liệu chỉ
là 30 ca tổng hợp giống hệt nhau. Đã vá: bọc bằng st_module.cache_resource
để chỉ seed MỘT LẦN cho vòng đời tiến trình.

Test dùng fake st_module (chỉ stub các lệnh UI — cache giờ là biến
module-level `_CACHED_SNAPSHOT` trong chính app.chronic_care.dashboard,
không còn phụ thuộc st_module.cache_resource) để xác nhận
build_chronic_care_readonly_snapshot() (và do đó ChronicCareService()/
seed_synthetic_cases()) chỉ được gọi ĐÚNG 1 LẦN dù
render_chronic_care_shadow_dashboard() được gọi nhiều lần liên tiếp.

Lưu ý: `_CACHED_SNAPSHOT` là biến CẤP MODULE (persist suốt tiến trình
pytest) — mỗi test PHẢI tự reset về None trước khi chạy để không phụ
thuộc thứ tự test khác đã làm nóng cache trước đó.
"""
from __future__ import annotations

import app.chronic_care.dashboard as CCD


class _FakeColumn:
    def metric(self, *a, **k):
        pass


class _FakeSt:
    """Stub tối thiểu cho các lệnh UI Streamlit dùng trong render_chronic_care_
    shadow_dashboard() — không cần cache_resource nữa vì cache đã chuyển sang
    biến module-level trong app.chronic_care.dashboard."""

    def header(self, *a, **k):
        pass

    def caption(self, *a, **k):
        pass

    def columns(self, n):
        return [_FakeColumn() for _ in range(n)]

    def error(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass

    def subheader(self, *a, **k):
        pass

    def dataframe(self, *a, **k):
        pass


def test_render_dashboard_only_seeds_snapshot_once_across_multiple_reruns(monkeypatch):
    monkeypatch.setattr(CCD, "_CACHED_SNAPSHOT", None)
    call_count = {"n": 0}
    real_build = CCD.build_chronic_care_readonly_snapshot

    def counting_build():
        call_count["n"] += 1
        return real_build()

    monkeypatch.setattr(CCD, "build_chronic_care_readonly_snapshot", counting_build)

    fake_st = _FakeSt()
    for _ in range(5):  # mô phỏng 5 lần Streamlit rerun (5 tương tác widget)
        CCD.render_chronic_care_shadow_dashboard(fake_st)

    assert call_count["n"] == 1, (
        f"Snapshot builder bị gọi {call_count['n']} lần thay vì đúng 1 lần — "
        "audit log sẽ phình vô hạn mỗi lần Streamlit rerun"
    )
