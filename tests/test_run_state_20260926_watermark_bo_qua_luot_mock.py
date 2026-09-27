"""Hồi quy synthesis #7 (26/09/2026): lượt MOCK không được làm watermark live.

CƠ CHẾ LỖI (đã tái lập): `run_state.compute_since_date()` đọc `last_finished_run()` — hàm
này chỉ lọc `PipelineRun.status == "ok"`, KHÔNG lọc `mode`. Lượt mock (seed_all / nút «🌱 Dữ
liệu mẫu» / `python run.py` không tham số) kết thúc bằng status "ok" (source_health "DEMO")
⇒ watermark live nhảy từ «lượt live ok cuối − 2 ngày» lên «hôm nay − 2 ngày». Guideline và
cảnh báo an toàn thuốc công bố trong khoảng outage/PARTIAL bị bỏ lỡ VĨNH VIỄN.

BẢN VÁ: `run_state.last_live_ok_run()` (status "ok" VÀ mode "live") là mốc duy nhất của
`compute_since_date()`. `last_finished_run()` giữ nguyên cho phần hiển thị.

Kiểm đột biến: đổi `compute_since_date()` về `last_finished_run()` (hoặc bỏ lọc mode trong
`last_live_ok_run()`) ⇒ các test «giu_nguyen» phải đỏ.
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
def db_tam(monkeypatch, tmp_path):
    """DB SQLite + thư mục dữ liệu tạm RIÊNG (không đụng DB/data của conftest hay repo)."""
    import app.database as db_mod
    from app.database import init_db

    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'wm.db'}")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    settings.ensure_dirs()
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


def _chen_luot(mode: str, status: str, cach_day_ngay: int) -> int:
    """Chèn thẳng một PipelineRun đã kết thúc (mô phỏng lịch sử chạy)."""
    moc = datetime.now(timezone.utc) - timedelta(days=cach_day_ngay)
    with session_scope() as s:
        run = PipelineRun(mode=mode, status=status, started_at=moc, finished_at=moc,
                          since_date=None, window_days=None)
        s.add(run)
        s.flush()
        return run.id


def _moc_ky_vong(cach_day_ngay: int) -> str:
    moc = datetime.now(timezone.utc) - timedelta(days=cach_day_ngay)
    return (moc - timedelta(days=run_state.OVERLAP_DAYS)).date().isoformat()


def _lich_su_outage() -> str:
    """1 lượt live ok cách 30 ngày + 2 lượt live partial ⇒ watermark đúng = mốc 30 ngày − 2."""
    _chen_luot("live", "ok", 30)
    _chen_luot("live", "partial", 14)
    _chen_luot("live", "partial", 7)
    truoc = run_state.compute_since_date()
    assert truoc == _moc_ky_vong(30), "fixture sai: watermark trước khi seed phải là mốc live ok"
    return truoc


def test_seed_mock_khong_day_watermark_live(db_tam):
    """★ Ca chính: seed_all(run_pipeline_mock=True) — ĐÚNG đường kích hoạt thật."""
    from app.utils.seed import seed_all

    truoc = _lich_su_outage()
    seed_all(run_pipeline_mock=True)

    last = run_state.last_finished_run()
    assert last is not None and last.mode == "mock" and last.status == "ok", (
        "fixture sai: lượt seed phải là mock/ok (đúng tình huống tái lập)")
    sau = run_state.compute_since_date()
    assert sau == truoc, (
        f"Watermark live nhảy từ {truoc} lên {sau} sau một lượt MOCK — khoảng outage bị bỏ lỡ")


def test_luot_mock_chen_tay_cung_khong_duoc_lam_moc(db_tam):
    truoc = _lich_su_outage()
    _chen_luot("mock", "ok", 0)
    assert run_state.compute_since_date() == truoc
    moc = run_state.last_live_ok_run()
    assert moc is not None and moc.mode == "live" and moc.status == "ok"


def test_luot_live_ke_tiep_nhan_since_date_cu_qua_run_pipeline(db_tam, monkeypatch):
    """Đầu–cuối: lượt live incremental sau lượt mock phải gọi ingest với since_date CŨ."""
    truoc = _lich_su_outage()
    _chen_luot("mock", "ok", 0)

    nhan: dict = {}

    def _ingest_gia(max_results_per_query=10, areas=None, since_date=None, diagnostics=None):
        nhan["since_date"] = since_date
        if diagnostics is not None:
            diagnostics["status"] = "PASS"
        return []

    monkeypatch.setattr(settings, "use_mock_sources", False)
    monkeypatch.setattr(pipeline_mod, "ingest_all", _ingest_gia)
    stats = pipeline_mod.run_pipeline(incremental=True)
    assert stats["mode"] == "live"
    assert nhan["since_date"] == truoc, (
        f"ingest nhận since_date={nhan['since_date']}, kỳ vọng {truoc} (mốc live ok cuối)")


def test_doi_chung_luot_live_ok_moi_van_day_watermark(db_tam):
    """Đối chứng: một lượt LIVE ok mới (sau lượt mock) vẫn đẩy watermark lên bình thường."""
    _lich_su_outage()
    _chen_luot("mock", "ok", 3)
    _chen_luot("live", "ok", 1)
    assert run_state.compute_since_date() == _moc_ky_vong(1)


def test_chua_tung_live_ok_thi_nhin_lui_mac_dinh(db_tam):
    """Môi trường chỉ từng chạy mock: lượt live đầu nhìn lùi DEFAULT_FIRST_LOOKBACK_DAYS."""
    _chen_luot("mock", "ok", 0)
    _chen_luot("live", "partial", 0)
    assert run_state.last_live_ok_run() is None
    ky_vong = (datetime.now(timezone.utc)
               - timedelta(days=run_state.DEFAULT_FIRST_LOOKBACK_DAYS)).date().isoformat()
    assert run_state.compute_since_date() == ky_vong


def test_last_finished_run_giu_hop_dong_hien_thi(db_tam):
    """last_finished_run() vẫn trả lượt 'ok' mới nhất KỂ CẢ mock (bản tin/test_incremental dùng)."""
    _chen_luot("live", "ok", 5)
    mock_id = _chen_luot("mock", "ok", 0)
    last = run_state.last_finished_run()
    assert last is not None and last.id == mock_id
