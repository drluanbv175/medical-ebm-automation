"""N8 (28/09/2026) — Bảng 5 (multiple imputation) của engine G6 dùng SE sandwich theo cụm khi có --cot-cum.

Trước bản vá, MI gộp theo Rubin các SE giả định độc lập: với dữ liệu gom cụm (bàn khám) KTC hẹp giả, đúng lớp lỗi
đã vá cho Bảng 2/Bảng 4. Kiểm: không có cụm ⇒ khoá cũ giữ nguyên; có cụm ⇒ ước lượng điểm như cũ, KTC biến cấp cụm
rộng hơn; hàng thiếu mã cụm bị loại và đếm; mã cụm không vào mô hình impute; 1 cụm ⇒ lỗi rõ; logistic chạy được.
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

pytest.importorskip("statsmodels.api")


def _du_lieu(seed: int = 5, n: int = 900, k: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    c = rng.integers(0, k, n)
    z = rng.integers(0, 2, k)[c].astype(float)  # biến ở CẤP CỤM
    u = rng.normal(0, 1.0, k)[c]
    x = rng.normal(0, 1, n)
    y = 2 + 0.5 * x - 0.4 * z + u + rng.normal(0, 1, n)
    y_bin = (rng.random(n) < 1 / (1 + np.exp(-(0.2 + 0.5 * x - 0.4 * z + u)))).astype(int)
    df = pd.DataFrame({"diem": y, "hl": y_bin, "nhom": z, "tuoi": x, "ban": c})
    df.loc[rng.random(n) < 0.2, "tuoi"] = np.nan
    return df


def _mi(df, cot="diem", loai="continuous", cum=None):
    np.random.seed(0)
    return RSA.multiple_imputation_model(df, cot, "nhom", ["tuoi"], loai, n_imputations=8, cluster_col=cum)


def _dong(mi, bien):
    return {r["variable"]: r for r in mi["results"]}[bien]


def test_khong_cum_khong_them_khoa():
    mi = _mi(_du_lieu())
    assert not {"cov_type", "cluster", "canh_bao", "loai_thieu_ma_cum"} & set(mi)
    assert "sandwich" not in RSA.format_mi_text(mi)


def test_cum_giu_uoc_luong_diem_va_mo_rong_ktc_bien_cap_cum():
    df = _du_lieu()
    cu, moi = _mi(df), _mi(df, cum="ban")
    assert moi["cov_type"] == "cluster" and moi["cluster"] == {"cot": "ban", "so_cum": 30}
    a, b = _dong(cu, "nhom"), _dong(moi, "nhom")
    assert b["beta"] == pytest.approx(a["beta"], abs=1e-3)
    assert (b["CI_95"][1] - b["CI_95"][0]) > 2 * (a["CI_95"][1] - a["CI_95"][0])
    txt = RSA.format_mi_text(moi)
    assert "sandwich theo cụm «ban» (30 cụm)" in txt and "Số cụm = 30" in txt


def test_ma_cum_khong_vao_mo_hinh_impute():
    moi = _mi(_du_lieu(), cum="ban")
    assert {r["variable"] for r in moi["results"]} == {"nhom", "tuoi"}


def test_hang_thieu_ma_cum_bi_loai_va_dem():
    df = _du_lieu()
    df.loc[:14, "ban"] = np.nan
    moi = _mi(df, cum="ban")
    assert moi["loai_thieu_ma_cum"] == 15 and moi["n_total"] == len(df) - 15
    assert "Loại 15 hàng thiếu mã cụm" in RSA.format_mi_text(moi)


def test_mot_cum_bao_loi_ro():
    moi = _mi(_du_lieu().assign(ban=1), cum="ban")
    assert "không hiệu chỉnh cụm được" in moi["error"]


def test_logistic_co_cum_chay_duoc():
    df = _du_lieu()
    cu, moi = _mi(df, "hl", "binary"), _mi(df, "hl", "binary", "ban")
    a, b = _dong(cu, "nhom"), _dong(moi, "nhom")
    assert b["OR_adj"] == pytest.approx(a["OR_adj"], abs=2e-3)
    assert b["CI_95"][1] / b["CI_95"][0] > a["CI_95"][1] / a["CI_95"][0]


def _gia_lap_cong(monkeypatch):
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda *a, **k: {})
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def test_main_bang5_co_cum(tmp_path, monkeypatch):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    duong = tmp_path / "d.csv"
    _du_lieu(n=500).to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "diem", "--group", "nhom",
        "--covariates", "tuoi", "--outcome-type", "continuous", "--cot-cum", "ban",
        "--n-imputations", "5", "--study", "SYN", "--gate", "G6"])
    RSA.main()
    txt = (tmp_path / "exports" / "SYN" / "G6_table5_multiple_imputation.txt").read_text(encoding="utf-8")
    assert "sandwich theo cụm «ban»" in txt
