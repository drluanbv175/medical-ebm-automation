"""N6 (28/09/2026) — hồi quy đa biến nhị phân/liên tục của engine G6 dùng SE sandwich theo cụm khi có --cot-cum.

SAP C1a có logistic nhị phân thứ cấp (G1 ≥ 4) trên dữ liệu gom cụm theo bàn khám: trước bản vá, Bảng 4 báo KTC
giả định độc lập (hẹp giả). Dữ liệu synthetic, không PII; cổng G2/G4/G5 giả lập để chỉ đo phần phân tích.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import run_stats_analysis as RSA  # noqa: E402

sm = pytest.importorskip("statsmodels.api")


def _du_lieu(seed: int = 7, n: int = 1200, k: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    c = rng.integers(0, k, n)
    u = rng.normal(0, 1.0, k)[c]
    z = rng.integers(0, 2, k)[c].astype(float)  # biến ở CẤP CỤM
    x = rng.normal(0, 1, n)
    eta = 0.3 + 0.6 * x - 0.5 * z + u
    y_bin = (rng.random(n) < 1 / (1 + np.exp(-eta))).astype(int)
    y_lt = 2 + 0.6 * x - 0.5 * z + u + rng.normal(0, 1, n)
    return pd.DataFrame({"hl": y_bin, "diem": y_lt, "cho": x, "tai_kham": z, "ban": c})


def _ci(mv: dict, bien: str) -> list:
    return {r["variable"]: r["CI_95"] for r in mv["results"]}[bien]


@pytest.mark.parametrize("cot, loai, khoa", [("hl", "binary", "OR_adj"), ("diem", "continuous", "beta")])
def test_cum_giu_uoc_luong_diem_va_mo_rong_ktc(cot, loai, khoa):
    df = _du_lieu()
    thuong = RSA.multivariate_model(df, cot, "cho", ["tai_kham"], loai)
    cum = RSA.multivariate_model(df, cot, "cho", ["tai_kham"], loai, cluster_col="ban")
    assert "cov_type" not in thuong and "cluster" not in thuong  # đầu ra cũ không đổi (golden)
    assert cum["cov_type"] == "cluster" and cum["cluster"] == {"cot": "ban", "so_cum": 24}
    assert any("Số cụm = 24" in c for c in cum["canh_bao"])
    uoc = {r["variable"]: r[khoa] for r in thuong["results"]}
    assert {r["variable"]: r[khoa] for r in cum["results"]} == uoc  # chỉ SE đổi
    a, b = _ci(thuong, "tai_kham"), _ci(cum, "tai_kham")
    if loai == "binary":
        a, b = np.log(a), np.log(b)
    assert (b[1] - b[0]) > 1.5 * (a[1] - a[0]), (a, b)


def test_logistic_cum_khop_statsmodels():
    df = _du_lieu()
    cum = RSA.multivariate_model(df, "hl", "cho", ["tai_kham"], "binary", cluster_col="ban")
    X = sm.add_constant(df[["cho", "tai_kham"]].astype(float))
    ref = sm.Logit(df["hl"].astype(float), X).fit(disp=False, cov_type="cluster",
                                                  cov_kwds={"groups": pd.factorize(df["ban"])[0]}, use_t=True)
    ci = np.exp(ref.conf_int().loc["tai_kham"]).round(3).tolist()
    assert _ci(cum, "tai_kham") == ci


def test_dinh_dang_va_script_r():
    df = _du_lieu(n=600)
    cum = RSA.multivariate_model(df, "hl", "cho", ["tai_kham"], "binary", cluster_col="ban")
    txt = RSA.format_multivariate_text(cum)
    assert "sandwich theo cụm «ban» (24 cụm)" in txt and "⚠ Số cụm = 24" in txt
    assert "không hiệu chỉnh cụm" in RSA.format_multivariate_text(
        RSA.multivariate_model(df, "hl", "cho", ["tai_kham"], "binary"))
    r = RSA.generate_r_script("S", "G6", "hl", "cho", ["tai_kham"], "binary", "ban")
    assert "vcovCL(model_adj, cluster = ~ ban)" in r and "print(exp(ci_cum))" in r
    assert "vcovCL" not in RSA.generate_r_script("S", "G6", "hl", "cho", ["tai_kham"], "binary")
    assert "print(ci_cum)" in RSA.generate_r_script("S", "G6", "diem", "cho", [], "continuous", "ban")


def test_dong_thieu_ma_cum_bi_loai():
    df = _du_lieu(n=600)
    df.loc[:9, "ban"] = np.nan
    assert RSA.multivariate_model(df, "hl", "cho", [], "binary", cluster_col="ban")["n"] == 590
    assert RSA.multivariate_model(df, "hl", "cho", [], "binary")["n"] == 600


def _gia_lap_cong(monkeypatch):
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda *a, **k: {})
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def test_main_nhi_phan_co_cum(tmp_path, monkeypatch, capsys):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    duong = tmp_path / "d.csv"
    _du_lieu(n=600).assign(nhom=lambda d: (d["cho"] > 0).astype(int)).to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "hl", "--group", "nhom",
        "--covariates", "tai_kham", "--outcome-type", "binary", "--cot-cum", "ban",
        "--study", "SYN", "--gate", "G6"])
    RSA.main()
    out = tmp_path / "exports" / "SYN"
    assert "sandwich theo cụm «ban»" in (out / "G6_table4_multivariate.txt").read_text(encoding="utf-8")
    tom = json.loads((out / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["multivariate"]["cov_type"] == "cluster"
    assert "vcovCL" in (out / "G6_analysis_syntax.R").read_text(encoding="utf-8")
    assert "Bảng 5 (MI) dùng SE hiệu chỉnh cụm" in capsys.readouterr().out
