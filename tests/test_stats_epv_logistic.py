"""Hồi quy: multivariate_model() tính EPV (Events-Per-Variable, Peduzzi 1996) cho
hồi quy LOGISTIC theo SỐ BIẾN CỐ (nhóm hiếm hơn), không phải tổng N (audit
2026-07-11). Trước vá: N=500 nhưng chỉ 25 biến cố + 5 biến dự báo (EPV thật=5,
KHÔNG đủ) từng lọt qua vì check dùng len(data)=500 >= 5*10=50."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_stats_analysis as rsa  # noqa: E402

pytest.importorskip("statsmodels")


def _synthetic_df(n_events: int, n_total: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "outcome": [1] * n_events + [0] * (n_total - n_events),
        "group": rng.integers(0, 2, n_total),
        "age": rng.normal(50, 10, n_total),
        "sex": rng.integers(0, 2, n_total),
        "bmi": rng.normal(25, 3, n_total),
        "htn": rng.integers(0, 2, n_total),
    })


def test_binary_rare_event_warns_on_true_epv_not_total_n():
    """N=500, chỉ 25 biến cố, 5 biến dự báo → EPV thật=5 (<10) — PHẢI warn dù
    tổng N=500 >= 5*10=50 (check cũ theo N sẽ bỏ lọt trường hợp này)."""
    df = _synthetic_df(n_events=25, n_total=500)
    res = rsa.multivariate_model(df, "outcome", "group", ["age", "sex", "bmi", "htn"],
                                  outcome_type="binary")
    assert "warning" in res
    assert "biến cố" in res["warning"]


def test_binary_balanced_event_no_warning():
    """N=500, 250 biến cố, 5 biến dự báo → EPV=50 (>=10) — KHÔNG warn."""
    df = _synthetic_df(n_events=250, n_total=500)
    res = rsa.multivariate_model(df, "outcome", "group", ["age", "sex", "bmi", "htn"],
                                  outcome_type="binary")
    assert "warning" not in res


def test_continuous_outcome_still_uses_total_n():
    """Nhánh liên tục (OLS) không đổi hành vi — vẫn dùng tổng N, không có khái
    niệm 'biến cố'."""
    rng = np.random.default_rng(1)
    n = 30
    df = pd.DataFrame({
        "outcome": rng.normal(120, 15, n),
        "group": rng.integers(0, 2, n),
        "age": rng.normal(50, 10, n),
        "sex": rng.integers(0, 2, n),
        "bmi": rng.normal(25, 3, n),
        "htn": rng.integers(0, 2, n),
    })
    res = rsa.multivariate_model(df, "outcome", "group", ["age", "sex", "bmi", "htn"],
                                  outcome_type="continuous")
    assert "warning" in res
    assert "Cỡ mẫu" in res["warning"]
