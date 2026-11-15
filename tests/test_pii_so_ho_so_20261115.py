"""Luật PII «số hồ sơ» chỉ bắt khi kèm GIÁ TRỊ định danh (15/11/2026).

Đo thật: dựng lại G1 phụ trợ của BTM (giai đoạn «Mục tiêu») làm G1 BLOCKED vì R2 bắt câu đếm «Số hồ sơ phải MỞ sẽ lớn
hơn cỡ mẫu» (giải trình G3 chủ nhiệm đã xác nhận). Luật mới dùng chung ở G0 và G1: «số hồ sơ: …», «số hồ sơ #…» hoặc
«số hồ sơ …» kèm mã ≥ 4 chữ số (không tính năm) là PII; câu nói VỀ hồ sơ thì không. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pii_van_ban as PV  # noqa: E402
import run_g0_auto as G0  # noqa: E402
import run_g1_auto as G1  # noqa: E402

DEM = "Số hồ sơ phải MỞ sẽ lớn hơn cỡ mẫu."
MA = "Số hồ sơ: BA2026001234"


def test_nhan_so_ho_so_phan_biet_gia_tri_voi_cau_dem():
    for co in (MA, "số hồ sơ #12345", "số hồ sơ bệnh án BA20261234 của người bệnh", "số hồ sơ 7788123"):
        assert PV.nhan_so_ho_so(co), co
    for khong in (DEM, "số hồ sơ năm 2026 cần mở", "không ghi họ tên/số hồ sơ, địa chỉ", "số hồ sơ đã trích: 385"):
        assert not PV.nhan_so_ho_so(khong), khong
    assert PV.nhan_so_ho_so(unicodedata.normalize("NFD", MA))  # dạng NFD vẫn bắt


def test_g1_khong_chan_cau_dem_nhung_chan_so_ho_so_that():
    assert not any("R2" in e for e in G1.guardrail_check_g1(f"Nội dung.\n{DEM}\n", effects=[])["errors"])
    assert any("R2" in e and "số hồ sơ" in e for e in G1.guardrail_check_g1(f"Nội dung.\n{MA}\n", effects=[])["errors"])
    assert any("R2" in e for e in G1.guardrail_check_g1("Họ tên: Nguyễn Văn A\n", effects=[])["errors"])


def test_g0_cung_luat_voi_g1():
    def _r2(txt: str) -> bool:
        return any("R2" in e for e in G0.guardrail_check_g0(txt, {"all_pmids": [], "n_pmids": 0})["errors"])

    assert not _r2(f"Chủ đề.\n{DEM}\n")
    assert _r2(f"Chủ đề.\n{MA}\n")
