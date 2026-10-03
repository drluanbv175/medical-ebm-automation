"""Hồi quy synthesis #6 (26/09/2026): hợp đồng «PARTIAL/FAIL/mock không gửi cảnh báo nội dung».

HAI LỖ THỦNG (đã tái lập):
(a) `alert_digest.get_new_items()` lấy mục của MỌI lượt trong N ngày, không lọc mode ⇒ sau lượt
    «Dữ liệu mẫu» (mock), lượt live PASS kế tiếp gửi email chứa cảnh báo FDA MedWatch BỊA như
    thật, kèm dòng «Chế độ: live». Lọc is_mock một mình KHÔNG đủ: mục mock của RSS mang is_mock=0
    (`RSSFeedClient._mock` không gắn raw["_mock"]).
(b) `scheduler.job_daily/job_weekly` (lệnh `run.py schedule`) gọi notify vô điều kiện, cả sau lượt
    PARTIAL/FAIL.

BẢN VÁ: đường GỬI chỉ lấy mục của lượt live (`build_alert_data(chi_live=True)`), notify có cổng
riêng `ly_do_chan_gui()` (lượt mới nhất phải là live + PASS, áp cả khi force), scheduler chỉ
notify khi PASS, RSS mock gắn `_mock`. Đường HIỂN THỊ giữ mục DEMO nhưng gắn nhãn.

Kiểm đột biến (mỗi phép làm đỏ đúng nhóm test):
- bỏ lọc mode trong get_new_items(chi_live) ⇒ `test_chi_live_loai_muc_luot_mock_du_is_mock_0`;
- bỏ `_mock` ở RSS ⇒ `test_rss_mock_gan_co_mock`;
- bỏ cổng PASS ở scheduler ⇒ `test_scheduler_*_khong_notify_khi_*`;
- bỏ cổng `ly_do_chan_gui` trong notify ⇒ `test_notify_chan_khi_luot_moi_nhat_partial*`.
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
from app.models import EvidenceItem, PipelineRun  # noqa: E402
from app.reports import alert_digest  # noqa: E402
from app.services import notify as notify_mod  # noqa: E402
from app.services import pipeline as pipeline_mod  # noqa: E402


@pytest.fixture()
def db_tam(monkeypatch, tmp_path):
    """DB SQLite + thư mục dữ liệu tạm RIÊNG; mọi kênh gửi thật đã tắt ở conftest."""
    import app.database as db_mod
    from app.database import init_db

    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'alert.db'}")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    settings.ensure_dirs()
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


@pytest.fixture()
def bat_gui(monkeypatch):
    """Thay send_email/send_webhook bằng hàm ghi lại nội dung (không gửi thật)."""
    da_gui: list = []

    def _email(subject, body_md, body_html=None, attachments=None):
        # HV-05 (03/10/2026): thân = bản tin ngắn, bản đầy đủ là tệp đính kèm — ghi cả hai để các kiểm cũ soi
        # được nội dung.
        da_gui.append(("email", subject, body_md + "".join(f"\n{a[1]}" for a in (attachments or []))))
        return {"status": "sent"}

    def _webhook(text, payload_extra=None):
        da_gui.append(("webhook", text, ""))
        return {"status": "sent"}

    monkeypatch.setattr(notify_mod, "send_email", _email)
    monkeypatch.setattr(notify_mod, "send_webhook", _webhook)
    return da_gui


def _chay_mock(monkeypatch):
    monkeypatch.setattr(settings, "use_mock_sources", True)
    stats = pipeline_mod.run_pipeline(max_results_per_query=10)
    assert stats["mode"] == "mock" and stats["new_items"] > 0, "fixture sai: lượt mock phải có mục"
    return stats


def _chay_live_pass_rong(monkeypatch, trang_thai: str = "PASS"):
    """Lượt LIVE thật qua run_pipeline, ingest giả trả 0 bản ghi với source_health cho trước."""
    def _ingest_gia(max_results_per_query=10, areas=None, since_date=None, diagnostics=None):
        if diagnostics is not None:
            diagnostics["status"] = trang_thai
        return []

    monkeypatch.setattr(settings, "use_mock_sources", False)
    monkeypatch.setattr(pipeline_mod, "ingest_all", _ingest_gia)
    stats = pipeline_mod.run_pipeline(incremental=True)
    assert stats["mode"] == "live"
    return stats


def _chen_luot(mode: str, status: str, source_status: str, cach_day_phut: int = 0) -> int:
    moc = datetime.now(timezone.utc) - timedelta(minutes=cach_day_phut)
    with session_scope() as s:
        run = PipelineRun(mode=mode, status=status, started_at=moc, finished_at=moc,
                          stats={"source_health": {"status": source_status}})
        s.add(run)
        s.flush()
        return run.id


def _chen_muc(run_id: int, title: str, *, is_mock: bool = False,
              study_type: str = "guideline") -> int:
    with session_scope() as s:
        it = EvidenceItem(source="feed_test", source_type="guideline", title=title,
                          study_type=study_type, is_primary_record=True, is_mock=is_mock,
                          first_seen_run_id=run_id, last_run_id=run_id,
                          classification="need_full_text", reliability_tier="B")
        s.add(it)
        s.flush()
        return it.id


# ---------------------------------------------------------------------------
# (a) Đường GỬI không bao giờ chứa mục của lượt mock
# ---------------------------------------------------------------------------

def test_mock_roi_live_pass_khong_gui_muc_mock(db_tam, monkeypatch, bat_gui):
    """★ Kịch bản tái lập: «Dữ liệu mẫu» rồi lượt live PASS ⇒ không gửi gì từ lượt mock."""
    _chay_mock(monkeypatch)
    _chay_live_pass_rong(monkeypatch)

    data = alert_digest.build_alert_data(days=7, chi_live=True)
    assert data["total_new"] == 0, (
        f"bản tin đường GỬI còn {data['total_new']} mục của lượt mock")
    tieu_de = [r.title for r in data["guidelines"] + data["regulatory"] + data["actionable"]]
    assert not any("MedWatch" in (t or "") for t in tieu_de)

    res = notify_mod.notify_high_priority_new(days=7)
    assert res["status"] == "no_high_priority_new", res
    assert bat_gui == []


def test_force_cung_khong_gui_muc_mock(db_tam, monkeypatch, bat_gui):
    """force=True được đi qua cổng (lượt mới nhất live PASS) nhưng nội dung KHÔNG chứa mục mock."""
    _chay_mock(monkeypatch)
    _chay_live_pass_rong(monkeypatch)
    res = notify_mod.notify_high_priority_new(days=7, force=True)
    assert res["high_priority"] == 0
    noi_dung = "\n".join(b for _k, _s, b in bat_gui)
    assert "MedWatch" not in noi_dung and "DEMO" not in noi_dung


def test_chi_live_loai_muc_luot_mock_du_is_mock_0(db_tam):
    """Hàng mock CŨ trong DB mang is_mock=0 (RSS trước bản vá) ⇒ phải loại theo MODE của lượt."""
    run_mock = _chen_luot("mock", "ok", "DEMO", cach_day_phut=10)
    run_live = _chen_luot("live", "ok", "PASS", cach_day_phut=1)
    _chen_muc(run_mock, "FDA MedWatch: Updated warning (mock cũ, is_mock=0)", is_mock=False,
              study_type="regulatory_alert")
    id_live = _chen_muc(run_live, "Guideline thật từ lượt live")

    data = alert_digest.build_alert_data(days=7, chi_live=True)
    ids = {r.id for r in alert_digest.get_new_items(days=7, chi_live=True)}
    assert ids == {id_live}, f"đường GỬI lấy {ids}, kỳ vọng chỉ mục live {id_live}"
    assert data["n_demo"] == 0 and data["run_mode"] == "live"


def test_chi_live_loai_muc_is_mock_trong_luot_live(db_tam):
    """Phòng thủ nhiều lớp: mục cờ is_mock=True lọt vào lượt live cũng bị loại khỏi đường GỬI."""
    run_live = _chen_luot("live", "ok", "PASS")
    _chen_muc(run_live, "Mục mock lẫn vào lượt live", is_mock=True)
    assert alert_digest.get_new_items(days=7, chi_live=True) == []


def test_rss_mock_gan_co_mock():
    """RSSFeedClient._mock phải gắn raw['_mock']=True ⇒ normalize ra is_mock=True."""
    from app.services.normalization import normalize
    from app.sources.feeds import DRUG_SAFETY_FEEDS, GUIDELINE_FEEDS
    from app.sources.rss_feed import RSSFeedClient

    ban_ghi = []
    for feed in list(DRUG_SAFETY_FEEDS)[:3] + list(GUIDELINE_FEEDS)[:3]:
        ban_ghi += RSSFeedClient(feed)._mock(5)
    assert ban_ghi, "fixture sai: không feed nào có mục mock"
    assert all((r.raw or {}).get("_mock") is True for r in ban_ghi)
    assert all(normalize(r)["is_mock"] is True for r in ban_ghi)
    # Không làm mất các khoá truy vết sẵn có của feed.
    assert all((r.raw or {}).get("_feed") for r in ban_ghi)


# ---------------------------------------------------------------------------
# Cổng GỬI trong notify (mọi nơi gọi)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode,status,src", [
    ("live", "partial", "PARTIAL"),
    ("live", "error", "FAIL"),
    ("mock", "ok", "DEMO"),
    ("live", "ok", "NOT_APPLICABLE"),
])
def test_notify_chan_khi_luot_moi_nhat_partial_fail_mock(db_tam, bat_gui, mode, status, src):
    run_cu = _chen_luot("live", "ok", "PASS", cach_day_phut=30)
    _chen_muc(run_cu, "Guideline thật ưu tiên cao")
    _chen_luot(mode, status, src, cach_day_phut=1)
    for force in (False, True):
        res = notify_mod.notify_high_priority_new(days=7, force=force)
        assert res["status"] == "blocked", (mode, status, src, force, res)
        assert res["email"]["status"] == "skipped"
    assert bat_gui == [], "không được gọi kênh gửi nào khi lượt mới nhất không phải live PASS"


def test_notify_chan_khi_luot_moi_nhat_dang_chay(db_tam, bat_gui):
    run_cu = _chen_luot("live", "ok", "PASS", cach_day_phut=30)
    _chen_muc(run_cu, "Guideline thật ưu tiên cao")
    with session_scope() as s:
        s.add(PipelineRun(mode="live", status="running",
                          started_at=datetime.now(timezone.utc)))
    assert notify_mod.notify_high_priority_new(days=7)["status"] == "blocked"
    assert bat_gui == []


def test_doi_chung_live_pass_co_muc_that_van_gui(db_tam, bat_gui):
    """Đối chứng: cổng không chặn quá tay — lượt mới nhất live PASS + mục live thật ⇒ gửi."""
    run = _chen_luot("live", "ok", "PASS")
    _chen_muc(run, "Guideline thật ưu tiên cao")
    res = notify_mod.notify_high_priority_new(days=7)
    assert res["status"] == "sent", res
    assert any("Guideline thật ưu tiên cao" in b for _k, _s, b in bat_gui)
    assert all("Chế độ: live" in b for k, _s, b in bat_gui if k == "email")


# ---------------------------------------------------------------------------
# Đường HIỂN THỊ: giữ mục DEMO nhưng gắn nhãn; «Chế độ» theo lượt đã góp mục
# ---------------------------------------------------------------------------

def test_hien_thi_gan_nhan_demo_va_che_do_theo_luot_gop_muc(db_tam, monkeypatch):
    _chay_mock(monkeypatch)
    _chay_live_pass_rong(monkeypatch)
    data = alert_digest.build_alert_data(days=7)
    assert data["total_new"] > 0 and data["n_demo"] == data["total_new"]
    assert data["run_mode"] == "mock (DEMO)"
    md = alert_digest.render_alert_markdown(data)
    assert "Chế độ: mock (DEMO)" in md and "Chế độ: live" not in md
    assert "DỮ LIỆU MẪU" in md and "🧪 [DEMO" in md


def test_hien_thi_hon_hop_live_va_mock(db_tam):
    run_mock = _chen_luot("mock", "ok", "DEMO", cach_day_phut=10)
    run_live = _chen_luot("live", "ok", "PASS", cach_day_phut=1)
    id_mock = _chen_muc(run_mock, "Mục mẫu")
    _chen_muc(run_live, "Mục thật")
    data = alert_digest.build_alert_data(days=7)
    assert data["run_mode"] == "live + mock (DEMO)"
    assert data["demo_ids"] == {id_mock}
    md = alert_digest.render_alert_markdown(data)
    dong_mau = [d for d in md.splitlines() if "Mục mẫu" in d]
    dong_that = [d for d in md.splitlines() if "Mục thật" in d]
    assert dong_mau and all("🧪 [DEMO" in d for d in dong_mau)
    assert dong_that and not any("DEMO" in d for d in dong_that)


# ---------------------------------------------------------------------------
# (b) Scheduler chỉ notify khi lượt vừa chạy PASS
# ---------------------------------------------------------------------------

class _Ten:
    name = "gia.md"


def _stub_scheduler(monkeypatch, trang_thai: str):
    import app.services.knowledge_pack_surveillance as kps
    from app import scheduler

    goi: list = []
    monkeypatch.setattr(scheduler, "run_pipeline",
                        lambda **kw: {"new_items": 0, "source_health": {"status": trang_thai}})
    monkeypatch.setattr(scheduler, "export_alert_digest",
                        lambda days=7: {"markdown": _Ten(), "total_new": 0})
    for ten in ("export_weekly_ebm_html", "export_dashboard_excel", "export_source_log_csv"):
        monkeypatch.setattr(scheduler, ten, lambda: None)
    monkeypatch.setattr(scheduler, "export_weekly_ebm_markdown", lambda: _Ten())
    monkeypatch.setattr(scheduler, "export_drug_safety_report", lambda: {"markdown": _Ten()})
    monkeypatch.setattr(scheduler, "export_antibiotic_report", lambda: {"markdown": _Ten()})
    monkeypatch.setattr(scheduler, "_log_change", lambda *a, **k: None)
    monkeypatch.setattr(kps, "write_knowledge_pack_update_queue", lambda days=7: _Ten())
    monkeypatch.setattr(settings, "enable_tiktok_auto", False)
    monkeypatch.setattr(scheduler, "notify_high_priority_new",
                        lambda days=7, force=False: goi.append(days) or {"status": "sent"})
    return scheduler, goi


@pytest.mark.parametrize("trang_thai", ["PARTIAL", "FAIL", "DEMO", "NOT_APPLICABLE", ""])
def test_scheduler_job_daily_khong_notify_khi_khong_pass(monkeypatch, trang_thai):
    scheduler, goi = _stub_scheduler(monkeypatch, trang_thai)
    scheduler.job_daily()
    assert goi == [], f"job_daily vẫn gọi notify khi source_health={trang_thai!r}"


@pytest.mark.parametrize("trang_thai", ["PARTIAL", "FAIL", "DEMO", "NOT_APPLICABLE", ""])
def test_scheduler_job_weekly_khong_notify_khi_khong_pass(monkeypatch, trang_thai):
    scheduler, goi = _stub_scheduler(monkeypatch, trang_thai)
    scheduler.job_weekly()
    assert goi == [], f"job_weekly vẫn gọi notify khi source_health={trang_thai!r}"


def test_scheduler_doi_chung_pass_van_notify(monkeypatch):
    scheduler, goi = _stub_scheduler(monkeypatch, "PASS")
    scheduler.job_daily()
    scheduler.job_weekly()
    assert goi == [1, 7]
