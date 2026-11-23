"""Mã thoát phân tích thiết kế đặc thù khi kiểm chéo SPSS/R KHÔNG ĐO ĐƯỢC (23/11/2026).

CI không có R/SPSS ⇒ kiểm chéo KHONG_DO_DUOC. Trước đây công cụ thoát mã 1 ⇒ chay_sap_g6 xếp phân tích là LỖI ⇒ G7
bỏ khối kết quả (rct_kinh_te thiếu CHEERS 2022 mục 22; chẩn đoán/dự báo/gộp có phân tích chính LỖI). «Không đo được» ≠
«có vấn đề»; LECH/LOI vẫn phải đỏ. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import phan_tich_thiet_ke_dac_thu as P  # noqa: E402


@pytest.mark.parametrize("kc, ma", [
    (None, 0),
    ({"trang_thai": "KHOP"}, 0),
    ({"trang_thai": "KHONG_DO_DUOC"}, 0),
    ({"trang_thai": "LECH"}, 1),
    ({"trang_thai": "LOI"}, 1),
])
def test_ma_thoat_theo_trang_thai_kiem_cheo(kc, ma):
    assert P.ma_thoat_kiem_cheo(kc) == ma


def test_chay_tra_ma_thoat_qua_ham_chung():
    """`chay` trả đúng hàm chung — không quay lại so «== KHOP» (đã làm CI xếp LỖI khi máy không có R/SPSS)."""
    import inspect

    nguon = inspect.getsource(P.chay)
    dong_cuoi = [d.strip() for d in nguon.splitlines() if d.strip().startswith("return")]
    assert dong_cuoi[-1] == "return ma_thoat_kiem_cheo(kc)"
