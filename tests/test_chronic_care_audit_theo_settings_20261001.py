"""Tệp audit Chronic Care Phase 3A đi theo `settings.processed_dir` — test không ghi vào `data/` thật (01/10/2026).

Trước bản vá, `app/chronic_care/audit.py::default_audit_trail()` mặc định `Path("data/processed/
chronic_care_phase_3a_audit.jsonl")` — tương đối theo thư mục hiện hành, không qua `settings` ⇒ fixture chuyển hướng
dữ liệu của tests/conftest.py không với tới, chốt canh `tests/canh_ghi_du_lieu_that.py` phải miễn trừ riêng tệp này, và
mỗi lượt pytest nối hàng MB sự kiện tổng hợp vào `data/processed/` của chính cây đang chạy (cây chính trên OneDrive:
289 MB, đo 30/09/2026). Nay đường dẫn mặc định tính LÚC GỌI từ `settings.processed_dir`; miễn trừ đã bỏ nên chốt canh
canh cả tệp này (khoá ở tests/test_khong_ghi_du_lieu_that_20260930.py).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import app.config as config_mod
import tests.conftest as C
from app.chronic_care.audit import AUDIT_FILENAME, default_audit_path, default_audit_trail, log_chronic_care_event
from app.chronic_care.service import ChronicCareService
from app.chronic_care.synthetic_cases import build_synthetic_case_pack
from app.config import BASE_DIR, Settings, settings

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_mac_dinh_tinh_luc_goi_theo_settings_processed_dir(monkeypatch, tmp_path):
    """Không phải hằng chốt lúc import: đổi `settings.data_dir` thì đường dẫn mặc định đổi theo ngay."""
    for ten in ("mot", "hai"):
        monkeypatch.setattr(settings, "data_dir", tmp_path / ten)
        assert default_audit_path() == tmp_path / ten / "processed" / AUDIT_FILENAME
        assert default_audit_trail().logger.path == tmp_path / ten / "processed" / AUDIT_FILENAME


def test_duong_dan_truyen_vao_van_duoc_dung(tmp_path):
    rieng = tmp_path / "rieng" / "audit.jsonl"
    assert default_audit_trail(rieng).logger.path == rieng


def test_mac_dinh_khong_phu_thuoc_thu_muc_hien_hanh(monkeypatch, tmp_path):
    """Chạy từ thư mục khác gốc repo: sự kiện vẫn vào `settings.processed_dir`, không đẻ `data/` lạc chỗ."""
    monkeypatch.setattr(settings, "data_dir", tmp_path / "du_lieu")
    khac = tmp_path / "thu_muc_khac"
    khac.mkdir()
    monkeypatch.chdir(khac)
    trail = default_audit_trail()
    log_chronic_care_event(trail, actor="system", action="kiem_duong_dan", entity_type="T", entity_id="t1",
                           environment="test", run_id="r1")
    tep = tmp_path / "du_lieu" / "processed" / AUDIT_FILENAME
    assert trail.logger.path == tep and tep.is_absolute()
    assert len(tep.read_text(encoding="utf-8").splitlines()) == 1
    assert not (khac / "data").exists()


def test_chay_tu_goc_repo_van_la_tep_cu(monkeypatch):
    """Giữ hành vi của dashboard: chạy từ gốc repo (`Mở Dashboard.command`, `python run.py dashboard`) thì đường dẫn
    cũ `Path("data/processed/chronic_care_phase_3a_audit.jsonl")` và đường dẫn mới là CÙNG một tệp.

    Dùng một `Settings()` mới (thư mục dữ liệu mặc định của cây) thay cho singleton — singleton của phiên test vẫn trỏ
    thư mục tạm; ở đây chỉ TÍNH đường dẫn, không mở, không tạo gì trong `data/` thật."""
    monkeypatch.setattr(config_mod, "settings", Settings())
    monkeypatch.chdir(BASE_DIR)
    assert default_audit_path().resolve() == Path("data/processed/chronic_care_phase_3a_audit.jsonl").resolve()


def test_service_mac_dinh_ghi_vao_thu_muc_du_lieu_cua_settings(monkeypatch, tmp_path):
    """Đường thật của tab 14 dashboard: `ChronicCareService()` không truyền `audit_trail`. Sự kiện nằm ở thư mục dữ liệu
    của settings, và chốt canh không thấy lần ghi nào vào `data/` thật."""
    monkeypatch.setattr(settings, "data_dir", tmp_path / "du_lieu")
    so_vi_pham_truoc = len(C._CANH_DU_LIEU_THAT.vi_pham)

    service = ChronicCareService()
    service.create_enrollment(build_synthetic_case_pack()[0])

    tep = tmp_path / "du_lieu" / "processed" / AUDIT_FILENAME
    assert service.audit_trail.logger.path == tep
    assert len(tep.read_text(encoding="utf-8").splitlines()) == len(service.audit_trail.events) == 1
    assert C._CANH_DU_LIEU_THAT.vi_pham[so_vi_pham_truoc:] == []


def test_import_chronic_care_van_khong_keo_theo_app_config():
    """`default_audit_path()` import `app.config` ngay trong hàm: import `app.chronic_care` (chỉ tab 14 dashboard dùng)
    vẫn không nạp `app.config` (.env, tạo thư mục data/) như trước bản vá. Chạy ở tiến trình con vì tiến trình pytest
    đã nạp `app.config` từ conftest."""
    kq = subprocess.run(
        [sys.executable, "-B", "-c", "import sys, app.chronic_care.audit, app.chronic_care; "
                                     "print('app.config' in sys.modules)"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
    )
    assert kq.returncode == 0, kq.stderr[-4000:]
    assert kq.stdout.splitlines()[-1:] == ["False"], kq.stdout
