"""Hồi quy 27/09/2026 — hệ số chặn lớn KHÔNG còn làm logistic bị gắn «không hội tụ» giả.

Lỗi gốc (giới hạn đã ghi khi merge #10): hai ngưỡng độ lớn |hệ số log| > 15 và sai số
chuẩn > 10 áp cả cho HỆ SỐ CHẶN. Độ lớn hệ số chặn phụ thuộc thang đo hiệp biến — tuổi
tính bằng năm, không căn giữa, biến cố hiếm ⇒ intercept ≈ −18 là hợp lệ — nên mô hình
hội tụ tốt vẫn bị thay OR bằng dòng «⚠ MÔ HÌNH KHÔNG HỘI TỤ». Bản vá: hệ số chặn chỉ
chịu phép kiểm không hữu hạn / CI tràn, không chịu phép kiểm độ lớn.
Dữ liệu synthetic, không PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import run_stats_analysis as RSA  # noqa: E402

pytest.importorskip("statsmodels")


def _du_lieu_he_so_chan_lon(seed: int = 20260927) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 3000
    tuoi = rng.uniform(60, 90, n)
    nhom = rng.integers(0, 2, n)
    logit = -18.0 + 0.2 * tuoi + 0.5 * nhom
    y = (rng.random(n) < 1.0 / (1.0 + np.exp(-logit))).astype(int)
    return pd.DataFrame({"outcome": y, "group": nhom, "age": tuoi})


def test_logistic_hoi_tu_voi_he_so_chan_lon_khong_bi_gan_co():
    df = _du_lieu_he_so_chan_lon()
    out = RSA.multivariate_model(df, "outcome", "group", ["age"], outcome_type="binary")
    assert out.get("model") == "logistic", out
    assert out.get("convergence") is not False
    assert not out.get("khong_hoi_tu"), out.get("ly_do")
    by_var = {r["variable"]: r for r in out["results"]}
    assert "OR_adj" in by_var["group"] and "CI_95" in by_var["group"]
    assert not by_var["group"].get("khong_hoi_tu")


def test_ham_kiem_bo_do_lon_cho_he_so_chan_nhung_van_bat_khong_huu_han():
    # Hệ số chặn −20, sai số chuẩn 12: bỏ phép kiểm độ lớn ⇒ không lý do.
    assert RSA._ly_do_tu_uoc_luong("const", -20.0, 12.0, -43.5, 3.5, kiem_do_lon=False) == []
    # Cùng số đó ở một hệ số thường (mặc định) ⇒ vẫn bị bắt.
    assert RSA._ly_do_tu_uoc_luong("age", -20.0, 12.0, -43.5, 3.5)
    # Hệ số chặn không hữu hạn vẫn bị bắt dù bỏ phép kiểm độ lớn.
    assert RSA._ly_do_tu_uoc_luong("const", float("inf"), 1.0, 0.0, 1.0, kiem_do_lon=False)
    assert RSA._ly_do_tu_uoc_luong("const", -20.0, float("nan"), -21.0, -19.0, kiem_do_lon=False)


def test_mi_logistic_he_so_chan_lon_khong_bi_gan_co():
    df = _du_lieu_he_so_chan_lon(seed=7)
    rng = np.random.default_rng(1)
    df.loc[rng.choice(len(df), 90, replace=False), "age"] = np.nan  # 3 % thiếu
    out = RSA.multiple_imputation_model(df, "outcome", "group", ["age"],
                                        outcome_type="binary", n_imputations=3)
    assert "error" not in out, out
    assert not out.get("khong_hoi_tu"), out.get("ly_do")
