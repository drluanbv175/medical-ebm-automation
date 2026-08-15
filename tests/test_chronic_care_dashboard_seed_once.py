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

import threading
import time

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


def test_render_dashboard_seeds_exactly_once_under_concurrent_reruns(monkeypatch):
    """Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 16 (2026-07-24, phát hiện
    MEDIUM): test tuần tự ở trên không bắt được TOCTOU — 2 phiên bác sĩ rerun
    gần như đồng thời (cùng thread pool của 1 tiến trình Streamlit) đều thấy
    _CACHED_SNAPSHOT is None TRƯỚC khi bên kia kịp gán, cùng gọi
    seed_synthetic_cases() độc lập, cùng APPEND audit log — phá vỡ mục tiêu
    "chỉ seed MỘT LẦN". Test này dùng threading.Barrier để ép NHIỀU thread
    cùng vào đường kiểm tra y hệt lúc, mô phỏng đúng race window đã vá bằng
    _CACHE_LOCK (double-checked locking)."""
    monkeypatch.setattr(CCD, "_CACHED_SNAPSHOT", None)
    call_count = {"n": 0}
    call_lock = threading.Lock()
    real_build = CCD.build_chronic_care_readonly_snapshot

    def slow_counting_build():
        with call_lock:
            call_count["n"] += 1
        time.sleep(0.05)  # nới rộng cửa sổ race để test bắt được lỗi nếu khóa bị bỏ
        return real_build()

    monkeypatch.setattr(CCD, "build_chronic_care_readonly_snapshot", slow_counting_build)

    n_threads = 8
    barrier = threading.Barrier(n_threads)
    errors = []

    def worker():
        try:
            barrier.wait(timeout=5)  # ép mọi thread cùng gọi render() gần như đồng thời
            CCD.render_chronic_care_shadow_dashboard(_FakeSt())
        except Exception as exc:  # noqa: BLE001 — thu lỗi để assert ở main thread
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"Lỗi trong thread: {errors}"
    assert call_count["n"] == 1, (
        f"Snapshot builder bị gọi {call_count['n']} lần dưới {n_threads} thread đồng thời "
        "thay vì đúng 1 lần — TOCTOU race, mỗi lần gọi APPEND audit log riêng vào cùng file"
    )
