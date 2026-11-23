# -*- coding: utf-8 -*-
"""Đường CHỌN phương pháp KTC hiệu số nguy cơ theo SAP — `run_stats_analysis.kc_hieu_so` (23/11/2026).

Bộ kiểm đột biến định kỳ (`tools/kiem_dot_bien_dinh_ky.py`) phát hiện: tắt nhánh «SAP khai Newcombe ⇒ tính Newcombe»
trong `kc_hieu_so` mà mọi test thuần Python vẫn xanh — test cũ chỉ gọi thẳng `kc_hieu_so_newcombe` hoặc nhánh
«phương pháp lạ ⇒ lỗi»; đường chọn chỉ được đi qua ở test cần SPSS/R thật. Test này đi qua đường chọn bằng Python
thuần. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_stats_analysis as RSA  # noqa: E402


@pytest.mark.parametrize("e1, n1, e0, n0", [(56, 70, 48, 80), (5, 56, 0, 29), (0, 10, 0, 20)])
def test_sap_khai_newcombe_thi_kc_hieu_so_tinh_newcombe(e1, n1, e0, n0):
    assert RSA.kc_hieu_so(e1, n1, e0, n0, "newcombe") == RSA.kc_hieu_so_newcombe(e1, n1, e0, n0)


def test_newcombe_khac_wald_o_nhom_khong_bien_co():
    # Newcombe 1998 bảng II ví dụ (d): một nhóm 0 % biến cố — Wald suy biến, Newcombe thì không (−0,0381; 0,1926)
    nc = RSA.kc_hieu_so(5, 56, 0, 29, "newcombe")
    wald = RSA.kc_hieu_so(5, 56, 0, 29, "wald")
    assert nc != wald
    assert round(nc[0], 4) == -0.0381 and round(nc[1], 4) == 0.1926
