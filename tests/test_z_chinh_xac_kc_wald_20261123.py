# -*- coding: utf-8 -*-
"""KTC Wald của hiệu số nguy cơ và OR thô dùng phân vị chuẩn CHÍNH XÁC z₀,₉₇₅ (23/11/2026).

Trước đây `kc_hieu_so` (Wald) và KTC OR thô của `compare_primary_outcome` dùng z = 1,96 làm tròn, trong khi Newcombe,
SPSS và R dùng phân vị chính xác 1,959963985. Nửa độ rộng lệch ≈ 0,0018 % — đủ đẩy cận KTC (làm tròn 4 chữ số) qua
ngưỡng: giả lập trên máy có SPSS báo kiểm chéo LỆCH giả ở rct_chan_thuc (0,1030 so với 0,10305) và rct_kinh_te
(−0,1630 so với −0,16295). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_stats_analysis as RSA  # noqa: E402

Z = NormalDist().inv_cdf(0.975)


@pytest.mark.parametrize("e1, n1, e0, n0", [(30, 50, 20, 50), (77, 110, 55, 108), (12, 110, 5, 108)])
def test_wald_hieu_so_dung_phan_vi_chinh_xac(e1, n1, e0, n0):
    p1, p0 = e1 / n1, e0 / n0
    se = math.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
    lo, hi = RSA.kc_hieu_so(e1, n1, e0, n0, "wald")
    assert (hi - lo) / 2 == pytest.approx(Z * se, rel=1e-12)
    assert (lo + hi) / 2 == pytest.approx(p1 - p0, abs=1e-15)


def test_ktc_or_tho_dung_phan_vi_chinh_xac():
    # 2×2: nhóm 1 có 22/60 biến cố, nhóm 0 có 5/80 — bảng chọn để z = 1,96 và z chính xác cho KHÁC nhau ở cả hai cận
    # sau khi làm tròn 3 chữ số: chính xác (3,05; 24,73), z = 1,96 (3,049; 24,731)
    df = pd.DataFrame({"nhom": [1] * 60 + [0] * 80,
                       "kq": [1] * 22 + [0] * 38 + [1] * 5 + [0] * 75})
    r = RSA.compare_primary_outcome(df, "kq", "nhom", "binary")
    or_ = (22 / 38) / (5 / 75)
    se = math.sqrt(1 / 5 + 1 / 75 + 1 / 22 + 1 / 38)
    assert tuple(r["ci_95"]) == (round(math.exp(math.log(or_) - Z * se), 3),
                                 round(math.exp(math.log(or_) + Z * se), 3)) == (3.05, 24.73)
