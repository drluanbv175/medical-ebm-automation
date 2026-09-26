"""Canary giám sát chứng cứ chạy đúng trên cả bố cục LỒNG (máy thật) lẫn ĐẶT CẠNH (Cloud) — 25/09/2026.

Hai lỗi đo được trên phiên Cloud: (1) `ROOT = REPO.parent` trỏ sai gốc workspace khi hai repo nằm cạnh
nhau ⇒ ESD04/ESD07/ESD08 FAIL giả; (2) canary chạy scanner tại chỗ ⇒ khoá `.quet.lock` và cảnh báo khẩn
của 2 chủ đề GIẢ có thể rơi vào thư mục thật (`EBM-Dashboards/alerts/` hoặc repo). Ngoại tuyến.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "verify_evidence_surveillance_deployment.py"
SPEC = importlib.util.spec_from_file_location("verify_esd_bo_cuc", MODULE_PATH)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V
SPEC.loader.exec_module(V)


def _goc_gia(noi: Path) -> Path:
    (noi / "tools").mkdir(parents=True)
    (noi / "tools" / "verify_clinical_evidence_update_pipeline.py").write_text("# gia\n", encoding="utf-8")
    return noi


def test_bo_cuc_long_uu_tien_thu_muc_cha(tmp_path, monkeypatch):
    monkeypatch.delenv("EBM_WORKSPACE_ROOT", raising=False)
    goc = _goc_gia(tmp_path / "Claude AI")
    repo = goc / "medical-ebm-automation"
    repo.mkdir()
    assert V._tim_goc_workspace(repo) == goc.resolve()


def test_bo_cuc_dat_canh_tim_anh_em(tmp_path, monkeypatch):
    monkeypatch.delenv("EBM_WORKSPACE_ROOT", raising=False)
    goc = _goc_gia(tmp_path / "EBM-drluanbv175")
    repo = tmp_path / "medical-ebm-automation"
    repo.mkdir()
    assert V._tim_goc_workspace(repo) == goc.resolve()


def test_bien_moi_truong_thang_va_khong_thay_thi_giu_cu(tmp_path, monkeypatch):
    goc = _goc_gia(tmp_path / "noi-khac")
    repo = tmp_path / "medical-ebm-automation"
    repo.mkdir()
    monkeypatch.setenv("EBM_WORKSPACE_ROOT", str(goc))
    assert V._tim_goc_workspace(repo) == goc.resolve()
    monkeypatch.delenv("EBM_WORKSPACE_ROOT")
    trong = tmp_path / "trong" / "medical-ebm-automation"
    trong.mkdir(parents=True)
    assert V._tim_goc_workspace(trong) == trong.parent       # không bịa gốc


def test_khung_tam_giu_khoa_va_canh_bao_trong_thu_muc_tam(tmp_path):
    nguon = tmp_path / "that" / "tools" / "surveillance_scan.py"
    nguon.parent.mkdir(parents=True)
    nguon.write_text("print('scanner')\n", encoding="utf-8")
    base = tmp_path / "tam"
    base.mkdir()
    ban_sao = V._dung_khung_scanner_tam(base, nguon)
    assert ban_sao.read_bytes() == nguon.read_bytes()
    assert ban_sao != nguon and base in ban_sao.parents
    # scanner đặt watchlist/khoá ở parents[1] và alerts ở parents[2]/alerts — cả hai phải NẰM TRONG base
    assert base in (ban_sao.parents[1] / ".quet.lock").parents
    assert base in (ban_sao.parents[2] / "alerts").parents or ban_sao.parents[2] == base
    assert not (nguon.parent.parent / "alerts").exists()
    lien_ket = base / "medical-ebm-automation"
    if lien_ket.is_symlink():                                  # Windows thiếu quyền ⇒ bỏ qua làn này
        assert (lien_ket / "app" / "sources").is_dir()


def test_scanner_nguon_lui_ve_ban_vendor_khi_khong_co_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "ROOT", tmp_path)
    vendor = tmp_path / "sync" / "skills" / "cap-nhat-chung-cu-y-khoa" / "tools" / "surveillance_scan.py"
    assert V._tim_scanner_nguon() == vendor
    runtime = tmp_path / "EBM-Dashboards" / "tools" / "surveillance_scan.py"
    runtime.parent.mkdir(parents=True)
    runtime.write_text("#\n", encoding="utf-8")
    assert V._tim_scanner_nguon() == runtime                   # máy thật: bản runtime thắng
