"""Hồi quy phát hiện #3 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 16) trong app/utils/seed.py::seed_all().

CƠ CHẾ LỖI: tên tham số `run_pipeline_mock` + docstring hàm ("nạp dữ liệu
mẫu") ngụ ý sẽ chạy pipeline ở chế độ MOCK an toàn, nhưng
`run_pipeline()` (app/services/pipeline.py) tự quyết định mock/live HOÀN
TOÀN dựa vào `settings.use_mock_sources` — `seed_all()` trước đây không
hề đọc/ghi cờ đó. So sánh với `app/main.py::cmd_live_update()` (đã làm
ĐÚNG khuôn mẫu save/restore cho chiều ngược lại — ép live) cho thấy đây
là mẫu hình đã biết trong chính codebase nhưng bị bỏ sót ở seed.py. Nếu
vận hành viên đã cấu hình `USE_MOCK_SOURCES=false` (trạng thái production
bình thường), lệnh "seed dữ liệu mẫu" sẽ âm thầm gọi API THẬT.

BẢN VÁ: bọc lời gọi `run_pipeline()` trong `seed_all()` bằng đúng khuôn
mẫu save/restore `settings.use_mock_sources` (ép True khi
`run_pipeline_mock=True`, khôi phục nguyên trạng sau đó — kể cả khi
`run_pipeline()` raise exception, nhờ `finally`).

Nguyên tắc viết test: gọi THẲNG `seed_all()` thật, monkeypatch
`app.utils.seed.run_pipeline` bằng một hàm giả GHI LẠI giá trị
`settings.use_mock_sources` tại thời điểm gọi (không mock request mạng —
chỉ cần quan sát cờ, không cần pipeline thật chạy)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.config import settings  # noqa: E402
from app.utils import seed as seed_mod  # noqa: E402


@pytest.fixture()
def isolated_seed_db(monkeypatch, tmp_path):
    """DB sqlite tạm RIÊNG cho test này (không dùng chung DB của conftest)."""
    import app.database as db_mod
    from app.database import init_db

    db_path = tmp_path / "vong16_seed.db"
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


def _fake_run_pipeline_recording(recorded):
    def _fake(max_results_per_query=10, **kwargs):
        recorded.append(settings.use_mock_sources)
        return {"total": 0, "mode": "mock" if settings.use_mock_sources else "live"}
    return _fake


class TestRunPipelineMockThatSuBiEpKhiSeed:
    """★★★ Ca chính — run_pipeline() bên trong seed_all() phải thấy
    settings.use_mock_sources=True TẠI THỜI ĐIỂM GỌI, bất kể cấu hình
    thật của máy đang là gì (kể cả khi máy đã cấu hình USE_MOCK_SOURCES=
    false cho production)."""

    def test_use_mock_sources_that_bi_ep_true_khi_dang_false(self, monkeypatch, isolated_seed_db):
        monkeypatch.setattr(settings, "use_mock_sources", False)
        recorded = []
        monkeypatch.setattr(seed_mod, "run_pipeline", _fake_run_pipeline_recording(recorded))

        seed_mod.seed_all(run_pipeline_mock=True)

        assert recorded == [True], (
            "TRƯỚC bản vá: seed_all() không hề đọc/ghi settings.use_mock_sources "
            "— run_pipeline() thấy đúng giá trị THẬT của máy (False), gọi API sống"
        )

    def test_cau_hinh_khoi_phuc_sau_khi_seed_xong(self, monkeypatch, isolated_seed_db):
        monkeypatch.setattr(settings, "use_mock_sources", False)
        monkeypatch.setattr(seed_mod, "run_pipeline", _fake_run_pipeline_recording([]))

        seed_mod.seed_all(run_pipeline_mock=True)

        assert settings.use_mock_sources is False, (
            "Sau khi seed xong, cấu hình use_mock_sources của máy phải được "
            "khôi phục nguyên trạng — không được để lại là True"
        )

    def test_khoi_phuc_ngay_ca_khi_run_pipeline_nem_loi(self, monkeypatch, isolated_seed_db):
        monkeypatch.setattr(settings, "use_mock_sources", False)

        def _raising_pipeline(max_results_per_query=10, **kwargs):
            raise RuntimeError("mô phỏng lỗi mạng giữa chừng")

        monkeypatch.setattr(seed_mod, "run_pipeline", _raising_pipeline)

        with pytest.raises(RuntimeError):
            seed_mod.seed_all(run_pipeline_mock=True)

        assert settings.use_mock_sources is False, (
            "Ngay cả khi run_pipeline() lỗi giữa chừng, use_mock_sources vẫn "
            "phải được khôi phục (dùng try/finally, không chỉ set rồi quên restore)"
        )


class TestRunPipelineMockFalseKhongDungChamCoUseMockSources:
    """Đối chứng bắt buộc — khi run_pipeline_mock=False (không chạy
    pipeline), settings.use_mock_sources không bị đụng tới."""

    def test_khong_goi_pipeline_thi_khong_doi_co(self, monkeypatch, isolated_seed_db):
        monkeypatch.setattr(settings, "use_mock_sources", False)
        called = []
        monkeypatch.setattr(seed_mod, "run_pipeline", lambda **kw: called.append(1))

        seed_mod.seed_all(run_pipeline_mock=False)

        assert called == []
        assert settings.use_mock_sources is False

    def test_use_mock_sources_dang_true_van_giu_true_sau_khi_seed(self, monkeypatch, isolated_seed_db):
        """Nếu máy VỐN ĐÃ ở mock=True (trường hợp bình thường nhất), seed
        xong vẫn phải giữ nguyên True — bản vá không làm lệch trạng thái
        vốn đã đúng."""
        monkeypatch.setattr(settings, "use_mock_sources", True)
        recorded = []
        monkeypatch.setattr(seed_mod, "run_pipeline", _fake_run_pipeline_recording(recorded))

        seed_mod.seed_all(run_pipeline_mock=True)

        assert recorded == [True]
        assert settings.use_mock_sources is True
