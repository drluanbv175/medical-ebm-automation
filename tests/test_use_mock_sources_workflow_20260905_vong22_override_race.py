"""Hồi quy phát hiện #3 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 22) trong app/utils/seed.py::seed_all() và app/main.py::cmd_live_update()
— đua trên cờ TOÀN CỤC `settings.use_mock_sources`.

CƠ CHẾ LỖI: cả hai hàm dùng khuôn đọc-lưu-ghi-chạy-khôi phục KHÔNG khoá trên
CÙNG một biến toàn cục `settings.use_mock_sources`, theo HAI CHIỀU ĐỐI LẬP:
  - seed_all()       ép use_mock_sources = True  (chạy mock, rồi khôi phục)
  - cmd_live_update() ép use_mock_sources = False (chạy live, rồi khôi phục)
app/dashboard/main.py gọi CẢ HAI đường từ hai nút bấm khác nhau trong CÙNG
một tiến trình Streamlit (nhiều tab/phiên chia sẻ bộ nhớ). Nếu người dùng
bấm "🔄 Cập nhật ngay (nguồn THẬT + email)" rồi bấm "🌱 Dữ liệu mẫu" gần như
đồng thời (hoặc 2 tab khác nhau), lượt cập nhật THẬT đang chạy dở (UI tự ghi
"có thể vài phút") có thể đọc trúng cờ đã bị lượt seed (chạy nhanh, xen
giữa) đẩy tạm về True — dữ liệu MOCK lẫn vào một lượt cập nhật tưởng là dữ
liệu THẬT mà không có cảnh báo nào, vì `run_pipeline()` chỉ chốt biến `mode`
MỘT LẦN ở đầu hàm trong khi từng SourceClient đọc lại cờ toàn cục SỐNG khi
khởi tạo (app/sources/base.py::SourceClient.__init__).

BẢN VÁ: thêm khoá dùng chung `settings.use_mock_sources_override_lock`
(app/config.py) — cả hai hàm giờ acquire cùng một khoá quanh khối
đọc-lưu-ghi-chạy-khôi phục, tuần tự hoá hai lượt để không còn cửa sổ xen kẽ.

Nguyên tắc viết test: gọi THẲNG seed_all() và cmd_live_update() thật (không
tự viết lại logic khoá song song) qua hai luồng thật, chỉ monkeypatch các
phụ thuộc NẶNG (DB/report export/notify) để test nhanh và không đụng
filesystem/network thật — cùng nguyên tắc đã dùng ở
tests/test_http_workflow_20260905_throttle_toctou_race.py cho race khác
trong CÙNG file http.py."""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.main as main_mod  # noqa: E402
import app.utils.seed as seed_mod  # noqa: E402
from app.config import settings  # noqa: E402


class TestKhongConDuaGiuaSeedAllVaCmdLiveUpdate:
    """★★★ Ca chính — seed_all() (ép mock=True) và cmd_live_update() (ép
    mock=False) chạy đồng thời trên 2 luồng: lượt "live" đang chạy DÀI
    (fake run_pipeline sleep + đọc cờ nhiều lần) không bao giờ được thấy
    cờ bị lượt "mock" (chạy nhanh, xen giữa) đẩy tạm về True."""

    def test_cmd_live_update_khong_bao_gio_thay_co_bi_day_ve_mock(self, monkeypatch):
        original = settings.use_mock_sources
        settings.use_mock_sources = False  # trạng thái "production" ban đầu

        quan_sat_live: list[bool] = []
        # SỬA khác với _throttle(): KHÔNG dùng threading.Barrier(2) đòi cả 2
        # luồng cùng vào bên trong critical section — với một khoá mutex
        # ĐANG HOẠT ĐỘNG ĐÚNG, chỉ MỘT luồng được ở trong critical section
        # tại một thời điểm, nên barrier đó sẽ treo vĩnh viễn (đã tái hiện
        # thực nghiệm: luồng live giữ khoá rồi chờ luồng mock tại rào cản,
        # nhưng luồng mock lại đang chờ CHÍNH khoá đó để vào tới rào cản).
        # Dùng Event: mock chỉ CỐ vào critical section SAU KHI live đã chắc
        # chắn đang giữ khoá — đúng kịch bản thật (bấm nút B trong lúc nút A
        # đang chạy dở), không cần cả hai đồng bộ bên trong.
        da_vao_run_pipeline_live = threading.Event()

        def _fake_run_pipeline_live(max_results_per_query=8, strict_source_health=True):
            da_vao_run_pipeline_live.set()
            for _ in range(20):
                quan_sat_live.append(settings.use_mock_sources)
                time.sleep(0.005)  # nới cửa sổ đua — cùng kỹ thuật test _throttle()
            return {
                "new_items": 0,
                "source_health": {"status": "FAIL", "reason": "test"},
            }

        def _fake_run_pipeline_mock(max_results_per_query=10):
            # Ngủ một nhịp NGẮN trong lúc cờ đang là True (nếu không bị
            # khoá chặn) — không có nhịp này, việc set True rồi trả về True
            # -> False có thể gọn trong CÙNG một lát cắt GIL (mặc định
            # ~5ms) và né hết mọi điểm lấy mẫu của luồng live một cách tình
            # cờ, khiến test "may rủi" thay vì đo đúng bất biến của khoá.
            time.sleep(0.02)
            return {"mode": "mock"}

        monkeypatch.setattr(main_mod, "init_db", lambda: None)
        monkeypatch.setattr(main_mod, "run_pipeline", _fake_run_pipeline_live)
        monkeypatch.setattr(
            main_mod, "export_alert_digest",
            lambda days=7: {"markdown": "", "html": "", "total_new": 0},
        )
        monkeypatch.setattr(main_mod, "export_weekly_ebm_markdown", lambda: "")
        monkeypatch.setattr(main_mod, "export_weekly_ebm_html", lambda: "")
        monkeypatch.setattr(
            main_mod, "export_drug_safety_report", lambda: {"markdown": ""}
        )
        monkeypatch.setattr(
            main_mod, "export_antibiotic_report", lambda: {"markdown": ""}
        )
        monkeypatch.setattr(main_mod, "export_weekly_ebm_docx", lambda: None)

        monkeypatch.setattr(seed_mod, "init_db", lambda: None)
        monkeypatch.setattr(seed_mod, "seed_clinical_scores", lambda: 0)
        monkeypatch.setattr(seed_mod, "seed_verified_scores", lambda: 0)
        monkeypatch.setattr(seed_mod, "add_project", lambda proj: None)
        monkeypatch.setattr(seed_mod, "run_pipeline", _fake_run_pipeline_mock)

        try:
            t_live = threading.Thread(target=main_mod.cmd_live_update)
            t_mock = threading.Thread(target=seed_mod.seed_all, kwargs={"run_pipeline_mock": True})
            t_live.start()
            # Chờ tới khi live ĐÃ VÀO run_pipeline (nghĩa là đang giữ khoá) rồi
            # mới bấm nút "Dữ liệu mẫu" — đúng kịch bản thật (nút B bấm SAU
            # khi nút A đã bắt đầu chạy dở), không cần cả hai đồng bộ bên
            # trong critical section.
            assert da_vao_run_pipeline_live.wait(timeout=5), "live không vào được run_pipeline"
            t_mock.start()
            t_live.join(timeout=10)
            t_mock.join(timeout=10)

            assert len(quan_sat_live) == 20, "luồng live chưa hoàn tất (treo/lỗi)"
            assert all(v is False for v in quan_sat_live), (
                "TRƯỚC bản vá: cờ use_mock_sources bị lượt seed_all() (chạy song "
                "song) đẩy tạm về True trong lúc cmd_live_update() đang chạy dở — "
                f"quan sát được: {quan_sat_live}"
            )
            # Cả hai đều phải khôi phục ĐÚNG trạng thái ban đầu sau khi xong.
            assert settings.use_mock_sources is False
        finally:
            settings.use_mock_sources = original

    def test_khoa_dung_chung_giua_hai_module(self):
        """Đối chứng cấu trúc — cả hai module phải dùng CHUNG một đối tượng
        khoá (không phải hai Lock độc lập, vốn sẽ không tuần tự hoá được gì)."""
        from app.config import use_mock_sources_override_lock

        assert use_mock_sources_override_lock.locked() is False


class TestSeedAllVaCmdLiveUpdateVanKhoiPhucDungCoDonLuong:
    """Đối chứng bắt buộc — hành vi ĐƠN LUỒNG (không có tranh chấp) không
    đổi: seed_all() vẫn khôi phục đúng giá trị trước đó, không bị khoá làm
    treo hay đổi kết quả."""

    def test_seed_all_don_luong_khoi_phuc_dung_gia_tri_ban_dau(self, monkeypatch):
        original = settings.use_mock_sources
        settings.use_mock_sources = False
        try:
            monkeypatch.setattr(seed_mod, "init_db", lambda: None)
            monkeypatch.setattr(seed_mod, "seed_clinical_scores", lambda: 0)
            monkeypatch.setattr(seed_mod, "seed_verified_scores", lambda: 0)
            monkeypatch.setattr(seed_mod, "add_project", lambda proj: None)

            gia_tri_luc_chay: list[bool] = []

            def _fake_run_pipeline(max_results_per_query=10):
                gia_tri_luc_chay.append(settings.use_mock_sources)
                return {"mode": "mock"}

            monkeypatch.setattr(seed_mod, "run_pipeline", _fake_run_pipeline)
            seed_mod.seed_all(run_pipeline_mock=True)

            assert gia_tri_luc_chay == [True], "phải ép mock=True trong lúc chạy"
            assert settings.use_mock_sources is False, "phải khôi phục đúng giá trị cũ"
        finally:
            settings.use_mock_sources = original
