"""Hồi quy phát hiện #1 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 14) trong app/services/pipeline.py::run_pipeline().

CƠ CHẾ LỖI: nhánh cuối hàm (chạy khi `strict_source_health=False` — GIÁ TRỊ
MẶC ĐỊNH, dùng thật ở `app/scheduler.py::job_daily()`/`job_weekly()` tự
động) tính `run_status` bằng ternary CHỈ phân biệt `"PARTIAL"` với "mọi giá
trị khác":
    run_status = "partial" if source_status == "PARTIAL" else "ok"
BỎ SÓT hoàn toàn `"FAIL"`. Khi nguồn sập hoàn toàn (`source_health["status"]
== "FAIL"`, `ingest_all()` không lấy được bản ghi thật nào), lần chạy vẫn
được ghi `PipelineRun.status="ok"`. Vì `run_state.compute_since_date()`
CHỈ đọc `PipelineRun.status=="ok"` để tính watermark cho lần live-pull kế
tiếp (`last_finished_run()` lọc đúng điều kiện đó), một lần chạy FAIL sẽ
đẩy watermark nhảy qua đúng khoảng thời gian outage — mọi guideline/cảnh
báo an toàn thuốc công bố trong khoảng đó KHÔNG BAO GIỜ được ingest lại.

BẢN VÁ: thêm nhánh `FAIL` tường minh, đối xứng với nhánh strict đã có sẵn
ở đầu hàm (status="error", release_status="BLOCKED_SOURCE_HEALTH_FAIL").

Nguyên tắc viết test: gọi THẲNG `run_pipeline()` thật với DB SQLite tạm
riêng (không dùng chung DB của conftest), monkeypatch `ingest_all` để mô
phỏng outage (trả 0 bản ghi, `diagnostics["status"]="FAIL"` — đúng cách
`ingest_all()` thật báo lỗi qua tham số `diagnostics` mutable), rồi đọc
lại `PipelineRun` + gọi `run_state.compute_since_date()` thật để chứng
minh hậu quả trên watermark.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import session_scope  # noqa: E402
from app.models import PipelineRun  # noqa: E402
from app.services import pipeline as pipeline_mod  # noqa: E402
from app.services import run_state  # noqa: E402


@pytest.fixture()
def isolated_live_db(monkeypatch, tmp_path):
    """DB sqlite tạm RIÊNG cho test này + ép mode='live' (source_health chỉ
    có ý nghĩa ở live; mock luôn gán status='DEMO')."""
    import app.database as db_mod
    from app.database import init_db

    db_path = tmp_path / "vong14_fail_status.db"
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(settings, "use_mock_sources", False)
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


def _fake_ingest_all_source_down(max_results_per_query=10, areas=None,
                                  since_date=None, diagnostics=None):
    """Mô phỏng CHÍNH XÁC cách ingest_all() thật báo lỗi: mutate `diagnostics`
    dict truyền vào (không return riêng) và trả về danh sách rỗng vì không
    nguồn nào phản hồi được."""
    if diagnostics is not None:
        diagnostics["status"] = "FAIL"
        diagnostics["reason"] = "all_sources_unreachable_vong14_test"
    return []


class TestFailStatusKhongDuocGanOk:
    """★★★ Ca chính — lần chạy có source_health=FAIL, strict_source_health
    mặc định (False, đúng cách job_daily()/job_weekly() gọi), phải ghi
    PipelineRun.status="error", KHÔNG được "ok"."""

    def test_pipeline_run_status_la_error_khi_source_fail(self, monkeypatch, isolated_live_db):
        monkeypatch.setattr(pipeline_mod, "ingest_all", _fake_ingest_all_source_down)

        stats = pipeline_mod.run_pipeline(records=None, incremental=False)

        assert stats["source_health"]["status"] == "FAIL"
        assert stats["release_status"] == "BLOCKED_SOURCE_HEALTH_FAIL", (
            f"TRƯỚC bản vá: release_status='READY_FOR_REVIEW_QUEUE' dù nguồn "
            f"đã báo FAIL. Giá trị thật: {stats.get('release_status')!r}"
        )

        with session_scope() as s:
            run = s.get(PipelineRun, stats["run_id"])
            assert run.status == "error", (
                f"TRƯỚC bản vá: PipelineRun.status='ok' dù source_health='FAIL' "
                f"— giá trị thật: {run.status!r}"
            )

    def test_watermark_khong_nhay_qua_lan_chay_fail(self, monkeypatch, isolated_live_db):
        """Hậu quả thật trên watermark: sau một lần chạy FAIL, since_date của
        lần live-pull KẾ TIẾP phải KHÔNG dựa vào lần chạy FAIL đó."""
        monkeypatch.setattr(pipeline_mod, "ingest_all", _fake_ingest_all_source_down)

        fail_run_started = datetime.now(timezone.utc) - timedelta(days=5)
        stats = pipeline_mod.run_pipeline(records=None, incremental=False)
        with session_scope() as s:
            run = s.get(PipelineRun, stats["run_id"])
            run.started_at = fail_run_started

        since_date_after_fail = run_state.compute_since_date()
        assert since_date_after_fail != fail_run_started.date().isoformat(), (
            "TRƯỚC bản vá: watermark nhảy tới ngày của lần chạy FAIL (trừ "
            "OVERLAP_DAYS) dù lần chạy đó KHÔNG lấy được bản ghi thật nào — "
            "mọi chứng cứ công bố trong khoảng outage bị bỏ sót vĩnh viễn."
        )
        # Không có lần chạy 'ok' nào khác trong DB -> phải lùi về lookback mặc định
        # (30 ngày), KHÔNG neo vào lần chạy FAIL.
        expected_fallback = (datetime.now(timezone.utc)
                              - timedelta(days=run_state.DEFAULT_FIRST_LOOKBACK_DAYS)).date().isoformat()
        assert since_date_after_fail == expected_fallback


class TestPartialVaOkVanGiuHanhViCu:
    """Đối chứng bắt buộc — PARTIAL và trạng thái bình thường (không FAIL,
    không PARTIAL) vẫn giữ đúng hành vi gốc, bản vá không đổi 2 nhánh này."""

    def test_partial_van_status_partial_va_blocked_release(self, monkeypatch, isolated_live_db):
        def fake_ingest_partial(max_results_per_query=10, areas=None,
                                 since_date=None, diagnostics=None):
            if diagnostics is not None:
                diagnostics["status"] = "PARTIAL"
                diagnostics["reason"] = "some_sources_down_vong14_test"
            return []

        monkeypatch.setattr(pipeline_mod, "ingest_all", fake_ingest_partial)
        stats = pipeline_mod.run_pipeline(records=None, incremental=False)

        assert stats["release_status"] == "BLOCKED_SOURCE_HEALTH_PARTIAL"
        with session_scope() as s:
            run = s.get(PipelineRun, stats["run_id"])
            assert run.status == "partial"

    def test_khong_fail_khong_partial_van_status_ok(self, monkeypatch, isolated_live_db):
        def fake_ingest_ok(max_results_per_query=10, areas=None,
                            since_date=None, diagnostics=None):
            if diagnostics is not None:
                diagnostics["status"] = "OK"
            return []

        monkeypatch.setattr(pipeline_mod, "ingest_all", fake_ingest_ok)
        stats = pipeline_mod.run_pipeline(records=None, incremental=False)

        assert stats["release_status"] == "READY_FOR_REVIEW_QUEUE"
        with session_scope() as s:
            run = s.get(PipelineRun, stats["run_id"])
            assert run.status == "ok"

    def test_strict_mode_van_chan_som_nhu_cu(self, monkeypatch, isolated_live_db):
        """Đối chứng: nhánh strict_source_health=True (đã đúng từ trước, KHÔNG
        đổi bởi bản vá này) vẫn chặn sớm và ghi status='error'."""
        monkeypatch.setattr(pipeline_mod, "ingest_all", _fake_ingest_all_source_down)
        stats = pipeline_mod.run_pipeline(records=None, incremental=False,
                                          strict_source_health=True)

        assert stats["release_status"] == "BLOCKED_SOURCE_HEALTH_FAIL"
        with session_scope() as s:
            run = s.get(PipelineRun, stats["run_id"])
            assert run.status == "error"
