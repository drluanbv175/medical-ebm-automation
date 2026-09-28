"""N1 (28/09/2026) — engine G6 chạy được SAP của C1a: logistic THỨ TỰ + sai số hiệu chỉnh cụm + ICC + OLS nhạy cảm.

Dữ liệu synthetic có tham số biết trước (không PII). Test cả hàm tính lẫn đường nối trong main() — cổng
G2/G4/G5 được giả lập để chỉ đo phần phân tích, KHÔNG nới cổng thật.
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

pytest.importorskip("statsmodels")

B_X, B_Z = 0.8, -0.5
CAT = [-2.0, -0.5, 0.8, 2.2]


def _du_lieu(seed: int = 20260928, n: int = 1500, n_cum: int = 30, sd_cum: float = 0.0,
             z_cap_cum: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    g = rng.integers(0, n_cum, n)
    u = rng.normal(0, sd_cum, n_cum)[g] if sd_cum else 0.0
    x = rng.normal(0, 1, n)
    z = (rng.integers(0, 2, n_cum)[g] if z_cap_cum else rng.integers(0, 2, n)).astype(float)
    lat = B_X * x + B_Z * z + u + rng.logistic(size=n)
    y = np.digitize(lat, CAT) + 1
    return pd.DataFrame({"G1": y, "cho_phut": x, "tai_kham": z, "ma_ban": g})


def test_ordinal_thu_lai_dung_tham_so_da_gai():
    od = RSA.ordinal_model(_du_lieu(), "G1", "cho_phut", ["tai_kham"])
    assert od["model"] == "ordinal_logit_po" and od["so_muc"] == 5 and not od.get("khong_hoi_tu")
    r = {x["variable"]: x for x in od["results"]}
    assert r["cho_phut"]["CI_95"][0] < np.exp(B_X) < r["cho_phut"]["CI_95"][1]
    assert r["tai_kham"]["CI_95"][0] < np.exp(B_Z) < r["tai_kham"]["CI_95"][1]
    for v in ("cho_phut", "tai_kham"):  # ước lượng điểm phải cùng thang (OR) với KTC của nó
        assert r[v]["CI_95"][0] < r[v]["OR_adj"] < r[v]["CI_95"][1]
    assert od["cov_type"] == "nonrobust"
    assert len(od["kiem_gia_dinh_ty_le_odds"]) == 4


def test_sai_so_cum_lon_hon_khi_bien_o_cap_cum():
    df = _du_lieu(n_cum=20, sd_cum=1.0, z_cap_cum=True)
    thuong = RSA.ordinal_model(df, "G1", "cho_phut", ["tai_kham"])
    cum = RSA.ordinal_model(df, "G1", "cho_phut", ["tai_kham"], cluster_col="ma_ban")
    assert cum["cov_type"] == "cluster" and cum["cluster"]["so_cum"] == 20

    def rong(od):
        ci = {x["variable"]: x["CI_95"] for x in od["results"]}["tai_kham"]
        return np.log(ci[1]) - np.log(ci[0])
    # Biến ở cấp cụm + hiệu ứng cụm mạnh ⇒ KTC hiệu chỉnh cụm phải RỘNG hơn rõ rệt.
    assert rong(cum) > 1.5 * rong(thuong)
    assert any("Số cụm = 20" in c for c in cum["canh_bao"])


def test_ordinal_tu_choi_it_muc_va_ma_chu():
    df = _du_lieu(n=200)
    df["hai_muc"] = (df["G1"] > 3).astype(int)
    assert "≥ 3 mức" in RSA.ordinal_model(df, "hai_muc", "cho_phut", [])["error"]
    df["chu"] = df["G1"].map({1: "a", 2: "b", 3: "c", 4: "d", 5: "e"})
    assert "mã số" in RSA.ordinal_model(df, "chu", "cho_phut", [])["error"]


def test_icc_cum_theo_so_tinh_tay():
    # A=[1,2,3], B=[4,5,6]: MSB=13,5; MSW=1; n0=3 ⇒ ICC=12,5/15,5; DE=1+2·ICC
    df = pd.DataFrame({"y": [1, 2, 3, 4, 5, 6], "c": ["A"] * 3 + ["B"] * 3})
    ic = RSA.icc_cum(df, "y", "c")
    assert ic["icc"] == pytest.approx(12.5 / 15.5, abs=1e-4)
    assert ic["hieu_ung_thiet_ke"] == pytest.approx(1 + 2 * 12.5 / 15.5, abs=1e-3)
    assert ic["co_mau_hieu_dung"] == pytest.approx(6 / (1 + 2 * 12.5 / 15.5), abs=0.1)


def test_icc_co_cum_khong_deu_dung_n0():
    df = pd.DataFrame({"y": [1, 2, 3, 4, 5, 6], "c": ["A", "A", "B", "B", "B", "B"]})
    assert RSA.icc_cum(df, "y", "c")["n0"] == pytest.approx((6 - 20 / 6) / 1, abs=1e-3)


def test_icc_am_khong_lam_de_nho_hon_1():
    df = pd.DataFrame({"y": [1, 5, 1, 5, 1, 5], "c": ["A", "A", "B", "B", "C", "C"]})
    ic = RSA.icc_cum(df, "y", "c")
    assert ic["icc"] < 0 and ic["hieu_ung_thiet_ke"] == 1.0


def test_linear_hc3_khop_statsmodels_va_cum():
    import statsmodels.api as sm
    df = _du_lieu(n=400)
    lh = RSA.linear_hc3(df, "G1", "cho_phut", ["tai_kham"])
    X = sm.add_constant(df[["cho_phut", "tai_kham"]].astype(float))
    ref = sm.OLS(df["G1"].astype(float), X).fit(cov_type="HC3").conf_int().loc["cho_phut"].round(4).tolist()
    assert lh["cov_type"] == "HC3"
    assert {r["variable"]: r["CI_95"] for r in lh["results"]}["cho_phut"] == ref
    assert RSA.linear_hc3(df, "G1", "cho_phut", [], cluster_col="ma_ban")["cov_type"] == "cluster"


def _gia_lap_cong(monkeypatch):
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda *a, **k: {})
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def test_main_nhanh_ordinal_ghi_du_bang_va_json(tmp_path, monkeypatch):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    duong = tmp_path / "d.csv"
    _du_lieu(n=600, n_cum=12, sd_cum=0.5).to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "G1", "--group", "cho_phut",
        "--covariates", "tai_kham", "--outcome-type", "ordinal", "--cot-cum", "ma_ban",
        "--study", "SYN", "--gate", "G6"])
    RSA.main()
    out = tmp_path / "exports" / "SYN"
    for ten in ("G6_table4_ordinal.txt", "G6_table6_sensitivity_linear.txt", "G6_icc_cluster.txt",
                "G6_analysis_syntax.R"):
        assert (out / ten).is_file(), ten
    assert not (out / "G6_table2_main_outcome.txt").exists(), "nhánh 2 nhóm không được chạy cho ordinal"
    tom = json.loads((out / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["ordinal"]["cov_type"] == "cluster" and tom["icc_cluster"]["so_cum"] == 12
    assert tom["sensitivity_linear"]["cov_type"] == "cluster"
    r = (out / "G6_analysis_syntax.R").read_text(encoding="utf-8")
    assert "clm(y_ord ~ cho_phut + tai_kham" in r and "(1 | ma_ban)" in r


def test_main_cot_cum_la_bi_chan(tmp_path, monkeypatch):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    duong = tmp_path / "d.csv"
    _du_lieu(n=200).to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "G1", "--group", "cho_phut",
        "--outcome-type", "ordinal", "--cot-cum", "KHONG_CO", "--study", "SYN"])
    with pytest.raises(SystemExit):
        RSA.main()
