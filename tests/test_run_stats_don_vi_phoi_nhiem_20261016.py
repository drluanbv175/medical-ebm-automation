"""F17 + F18 (16/10/2026, diễn tập C1a): đơn vị phơi nhiễm liên tục (OR mỗi 15 phút như SAP) và cảnh báo khi mô hình
chính thứ tự không chạy vì thiếu phơi nhiễm. Ngoại tuyến, dữ liệu tổng hợp."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import run_stats_analysis as RSA  # noqa: E402


def _du_lieu(seed: int = 7, n: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cho = rng.uniform(5, 120, n)
    tiem = -0.02 * cho + rng.logistic(size=n)
    hl = np.digitize(tiem, np.quantile(tiem, [0.2, 0.4, 0.6, 0.8])) + 1
    return pd.DataFrame({"hl": hl, "cho": cho, "tuoi": rng.integers(18, 80, n)})


def _or(od: dict, bien: str) -> float:
    return next(r["OR_adj"] for r in od["results"] if r["variable"] == bien)


def test_f18_or_moi_15_phut_bang_or_moi_phut_mu_15():
    df = _du_lieu()
    or1 = _or(RSA.ordinal_model(df, "hl", "cho", ["tuoi"]), "cho")
    or15 = _or(RSA.ordinal_model(RSA.ap_don_vi_phoi_nhiem(df, "cho", 15), "hl", "cho", ["tuoi"]), "cho")
    assert math.isclose(or15, or1 ** 15, rel_tol=0.02), (or1, or15)
    assert or15 < 0.9 < or1 < 1.0, "mỗi 15 phút phải thấy rõ hiệu ứng mà mỗi phút gần 1"


def test_f18_khong_don_vi_tra_nguyen_va_don_vi_am_bi_tu_choi():
    df = _du_lieu()
    assert RSA.ap_don_vi_phoi_nhiem(df, "cho", None) is df
    with pytest.raises(ValueError):
        RSA.ap_don_vi_phoi_nhiem(df, "cho", 0)
    assert df["cho"].max() > 100, "bản gốc không bị chia tại chỗ"


def test_f18_bang4_ghi_ro_don_vi():
    od = RSA.ordinal_model(RSA.ap_don_vi_phoi_nhiem(_du_lieu(), "cho", 15), "hl", "cho", ["tuoi"])
    od["don_vi_phoi_nhiem"] = {"cot": "cho", "don_vi": 15.0, "dien_giai": "OR cho MỖI 15 đơn vị «cho»"}
    assert "MỖI 15 đơn vị" in RSA.format_ordinal_text(od)


def test_f17_thieu_phoi_nhiem_canh_bao_va_ghi_tom_tat(capsys):
    tom = {}
    assert RSA.canh_bao_thieu_phoi_nhiem("ordinal", "hl", "", tom) is True
    assert tom["mo_hinh_chinh"]["da_chay"] is False and "CHƯA CHẠY" in capsys.readouterr().out


def test_f17_co_phoi_nhiem_hoac_khong_phai_thu_tu_thi_im():
    tom = {}
    assert RSA.canh_bao_thieu_phoi_nhiem("ordinal", "hl", "cho", tom) is False
    assert RSA.canh_bao_thieu_phoi_nhiem("binary", "y", "", tom) is False
    assert tom == {}
