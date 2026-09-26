"""ESD07: bản scanner RUNTIME (EBM-Dashboards/tools) cũng chạy trong hộp cát — 26/09/2026.

Bản runtime ghi `.quet.lock`, `.so-xac-minh-nguon.json` cạnh chính nó và alert khẩn vào
`<gốc EBM>/alerts/`; chạy canary (2 chủ đề GIẢ) tại chỗ có thể ghi «CỔNG QUÉT FAIL: Canary…» vào
thư mục thật trên máy bác sĩ. Máy không tạo được symlink (Windows thiếu quyền) thì giữ hành vi cũ.
Ngoại tuyến: repo EBM giả dựng trong tmp_path, dùng lại helper của test bố cục 24/09.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_verify_esd_bo_cuc_cloud_20260924 import _anh_chup, _dung_ebm, _tao_duoc_symlink
from tools import verify_evidence_surveillance_deployment as V


def test_runtime_chay_trong_hop_cat_khong_ghi_vao_ebm_dashboards(tmp_path, monkeypatch):
    if not _tao_duoc_symlink(tmp_path):
        pytest.skip("máy không tạo được symlink — nhánh dự phòng có test riêng")
    goc = _dung_ebm(tmp_path / "ws", dashboards=True)
    truoc = _anh_chup(goc)
    monkeypatch.setattr(V, "ROOT", goc)
    check = V._check_online_scanner()  # subprocess THẬT với scanner giả
    assert check.status == V.PASS, check.evidence
    assert "scanner=EBM-Dashboards_hop_cat" in check.evidence
    assert _anh_chup(goc) == truoc  # không khoá, không alert nào rơi vào cây thật
    assert not (goc / "alerts").exists()


def test_runtime_duoc_uu_tien_hon_vendor_khi_chep(tmp_path):
    if not _tao_duoc_symlink(tmp_path):
        pytest.skip("máy không tạo được symlink")
    goc = _dung_ebm(tmp_path / "ws", dashboards=True)
    runtime = goc / "EBM-Dashboards" / "tools" / "surveillance_scan.py"
    runtime.write_text("# ban runtime\n", encoding="utf-8", newline="\n")
    base = tmp_path / "tam"
    base.mkdir()
    dich, cwd, nguon = V._chuan_bi_scanner(goc, base)
    assert dich.read_bytes() == runtime.read_bytes()
    assert base in dich.parents and cwd == base / "hop_cat"
    assert nguon == "EBM-Dashboards_hop_cat"


def test_khong_tao_duoc_symlink_thi_runtime_chay_tai_cho_nhu_cu(tmp_path, monkeypatch):
    goc = _dung_ebm(tmp_path / "ws", dashboards=True)
    monkeypatch.setattr(V, "ROOT", goc)

    def no_symlink(self, *a, **k):
        raise OSError("symlink bị cấm")

    monkeypatch.setattr(Path, "symlink_to", no_symlink)
    base = tmp_path / "tam"
    base.mkdir()
    dich, cwd, nguon = V._chuan_bi_scanner(goc, base)
    assert dich == goc / "EBM-Dashboards" / "tools" / "surveillance_scan.py"
    assert cwd == goc and nguon == "EBM-Dashboards"   # không tụt xuống «chưa đo được»
