"""SAP C1a 1.2 §3 (17/10/2026): Wilson trên n hiệu dụng có hiệu chỉnh bậc tự do thiết kế + CV cỡ cụm + DE Eldridge."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import run_stats_analysis as RSA  # noqa: E402

pytest.importorskip("scipy")


def test_he_so_bac_tu_do_50_cum():
    from scipy.stats import norm
    from scipy.stats import t as student
    assert RSA.he_so_bac_tu_do(50) == pytest.approx((norm.ppf(0.975) / student.ppf(0.975, 49)) ** 2, rel=1e-9)
    assert RSA.he_so_bac_tu_do(50) == pytest.approx(0.951, abs=1e-3)
    assert RSA.he_so_bac_tu_do(1) == 1.0


def _du_lieu():
    rng = np.random.default_rng(17)
    co = rng.integers(5, 40, size=50)                       # cỡ cụm không đều
    p = 1 / (1 + np.exp(-(1.2 + rng.normal(0, 0.8, 50))))
    y = np.concatenate([(rng.random(m) < pc).astype(int) for m, pc in zip(co, p)])
    return pd.DataFrame({"y": y, "c": np.repeat(np.arange(50), co)}), co


def test_ktc_chinh_dung_n_hieu_dung_da_hieu_chinh_va_xuat_cv_eldridge():
    df, co = _du_lieu()
    r = RSA.ty_le_wilson_cum(df, "y", cluster_col="c")
    n_bt = r["n"] / r["hieu_ung_thiet_ke"] * RSA.he_so_bac_tu_do(50)
    assert r["co_mau_hieu_dung_hieu_chinh_bac_tu_do"] == pytest.approx(round(n_bt, 1))
    assert r["CI_95"] == pytest.approx([round(v, 4) for v in RSA._wilson(r["ty_le"], n_bt)], abs=1e-4)
    cv = co.std(ddof=0) / co.mean()
    assert r["cv_co_cum"] == pytest.approx(round(cv, 3))
    assert r["de_theo_icc_eldridge"] == pytest.approx(
        round(1 + ((cv ** 2 + 1) * co.mean() - 1) * max(r["icc"], 0), 3), abs=2e-3)
    rong_bt = r["CI_95"][1] - r["CI_95"][0]
    rong_kbt = np.subtract(*RSA._wilson(r["ty_le"], r["n"] / r["hieu_ung_thiet_ke"])[::-1])
    assert rong_bt > rong_kbt, "hiệu chỉnh bậc tự do phải làm KTC rộng hơn"


def test_bang_van_ban_in_cv_va_bac_tu_do():
    df, _ = _du_lieu()
    txt = RSA.format_ty_le_text([RSA.ty_le_wilson_cum(df, "y", cluster_col="c")])
    assert "DE Eldridge" in txt and "× bậc tự do" in txt
