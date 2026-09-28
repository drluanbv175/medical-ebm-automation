"""N2 (28/09/2026) — tỷ lệ Mục tiêu 1 + KTC 95% Wilson hiệu chỉnh gom cụm (n hiệu dụng = n/DE).

Dữ liệu synthetic, không PII. Có một mô phỏng độ phủ: KTC độc lập phải PHỦ THIẾU khi dữ liệu gom cụm,
KTC hiệu chỉnh phải về gần 95%.
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


def test_wilson_khop_statsmodels():
    from statsmodels.stats.proportion import proportion_confint
    for x, n in [(80, 100), (3, 50), (0, 20), (999, 1000)]:
        ref = proportion_confint(x, n, method="wilson")
        assert RSA._wilson(x / n, n) == pytest.approx(list(ref), abs=1e-9)


def test_nguong_va_ma_01():
    df = pd.DataFrame({"G1": [5, 4, 3, 2, 4, 5, 1, None]})
    r = RSA.ty_le_wilson_cum(df, "G1", nguong=4)
    assert (r["n"], r["so_su_kien"], r["so_thieu_bo_qua"]) == (7, 4, 1)
    assert r["dinh_nghia"] == "G1 ≥ 4" and "CI_95" not in r
    assert "0/1" in RSA.ty_le_wilson_cum(df, "G1")["error"]
    df["hl"] = (df["G1"] >= 4).astype(float).where(df["G1"].notna())
    assert RSA.ty_le_wilson_cum(df, "hl")["so_su_kien"] == 4
    assert "không có cột" in RSA.ty_le_wilson_cum(df, "X")["error"]


def test_de_tuyen_tinh_hoa_theo_so_tinh_tay():
    # Cụm A: 4/4, cụm B: 0/4 ⇒ p = 0,5; t−p·m = ±2 ⇒ Var = 2/1·8/64 = 0,25; Var_SRS = 0,25/8 ⇒ DE = 8.
    df = pd.DataFrame({"y": [1] * 4 + [0] * 4, "c": ["A"] * 4 + ["B"] * 4})
    r = RSA.ty_le_wilson_cum(df, "y", cluster_col="c")
    assert r["de_thiet_ke_tho"] == pytest.approx(8.0) and r["co_mau_hieu_dung"] == pytest.approx(1.0)
    assert r["CI_95"] == pytest.approx([round(v, 4) for v in RSA._wilson(0.5, 1.0)])


def test_de_chan_duoi_1_va_ty_le_bien():
    # Mỗi cụm đúng 1/2 ⇒ phương sai giữa cụm = 0 ⇒ DE thô 0 → dùng 1 (không làm KTC hẹp hơn độc lập).
    df = pd.DataFrame({"y": [1, 0] * 5, "c": np.repeat(list("ABCDE"), 2)})
    r = RSA.ty_le_wilson_cum(df, "y", cluster_col="c")
    assert r["hieu_ung_thiet_ke"] == 1.0 and r["CI_95"] == r["CI_95_wilson_doc_lap"]
    tat_ca = RSA.ty_le_wilson_cum(pd.DataFrame({"y": [1] * 6, "c": list("AABBCC")}), "y", cluster_col="c")
    assert tat_ca["hieu_ung_thiet_ke"] == 1.0 and any("0 hoặc 1" in c for c in tat_ca["canh_bao"])


# Tỷ lệ quần thể thật dưới mô hình logit-chuẩn (p cụm = logit⁻¹(logit 0,8 + u), u ~ N(0; 0,9)).
_g = np.random.default_rng(1).normal(0, 0.9, 2_000_000)
P_QUAN_THE = float(np.mean(1 / (1 + np.exp(-(np.log(4.0) + _g)))))


def test_do_phu_mo_phong_gom_cum():
    rng = np.random.default_rng(20260928)
    p_that, K, m, lap = 0.8, 40, 25, 400
    logit = np.log(p_that / (1 - p_that))
    phu_dl = phu_cum = 0
    for _ in range(lap):
        u = rng.normal(0, 0.9, K)
        pc = 1 / (1 + np.exp(-(logit + u)))
        y = (rng.random((K, m)) < pc[:, None]).astype(int).ravel()
        df = pd.DataFrame({"y": y, "c": np.repeat(np.arange(K), m)})
        r = RSA.ty_le_wilson_cum(df, "y", cluster_col="c")
        phu_dl += r["CI_95_wilson_doc_lap"][0] <= P_QUAN_THE <= r["CI_95_wilson_doc_lap"][1]
        phu_cum += r["CI_95"][0] <= P_QUAN_THE <= r["CI_95"][1]
    assert phu_dl / lap < 0.80, phu_dl / lap
    assert 0.90 <= phu_cum / lap <= 0.99, phu_cum / lap


def _gia_lap_cong(monkeypatch):
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda *a, **k: {})
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def test_main_ghi_bang_ty_le(tmp_path, monkeypatch):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    rng = np.random.default_rng(7)
    df = pd.DataFrame({"G1": rng.integers(1, 6, 300), "A_diem": rng.integers(1, 6, 300),
                       "cho_phut": rng.normal(0, 1, 300), "ma_ban": rng.integers(0, 10, 300)})
    duong = tmp_path / "d.csv"
    df.to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "G1", "--group", "cho_phut",
        "--outcome-type", "ordinal", "--cot-cum", "ma_ban", "--ty-le", "G1", "A_diem",
        "--nguong-ty-le", "4", "--study", "SYN", "--gate", "G6"])
    RSA.main()
    out = tmp_path / "exports" / "SYN"
    txt = (out / "G6_table1b_proportions.txt").read_text(encoding="utf-8")
    assert "G1 ≥ 4" in txt and "A_diem ≥ 4" in txt and "hiệu chỉnh cụm «ma_ban»" in txt
    tom = json.loads((out / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert [r["cot"] for r in tom["ty_le"]] == ["G1", "A_diem"]
    assert tom["ty_le"][0]["so_su_kien"] == int((df["G1"] >= 4).sum())
