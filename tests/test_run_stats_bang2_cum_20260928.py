"""N7 (28/09/2026) — Bảng 2 (so sánh 2 nhóm thô) của engine G6 có thêm ước lượng hiệu chỉnh cụm khi có --cot-cum.

Trước bản vá, Bảng 2 chỉ có Chi-square/t-test giả định quan sát độc lập: với dữ liệu gom cụm (nhóm gán theo bàn
khám) KTC hẹp giả. Kiểm: (1) không có cụm ⇒ đầu ra cũ giữ nguyên (golden GOLDEN-G6-001); (2) ước lượng điểm trùng
ước lượng thô, KTC rộng hơn; (3) mô phỏng độ phủ KTC 95% khi nhóm gán theo cụm; (4) lỗi/ca biên; (5) main() nối
đúng. Dữ liệu synthetic, không PII; cổng G2/G4/G5 giả lập để chỉ đo phần phân tích.
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

pytest.importorskip("statsmodels.api")


def _du_lieu(seed: int = 3, n: int = 1200, k: int = 30, hieu_ung: float = 0.0) -> pd.DataFrame:
    """Nhóm gán THEO CỤM (mọi người cùng bàn cùng nhóm) + hiệu ứng ngẫu nhiên cụm mạnh."""
    rng = np.random.default_rng(seed)
    c = rng.integers(0, k, n)
    nhom = rng.integers(0, 2, k)[c]
    u = rng.normal(0, 1.0, k)[c]
    y_lt = 5 + hieu_ung * nhom + u + rng.normal(0, 1, n)
    y_bin = (rng.random(n) < 1 / (1 + np.exp(-(-0.2 + hieu_ung * nhom + u)))).astype(int)
    return pd.DataFrame({"diem": y_lt, "hl": y_bin, "nhom": nhom, "ban": c})


def test_khong_cum_giu_nguyen_dau_ra_cu():
    df = _du_lieu()
    for cot, loai in (("diem", "continuous"), ("hl", "binary")):
        cu = RSA.compare_primary_outcome(df, cot, "nhom", loai)
        moi = RSA.compare_primary_outcome(df, cot, "nhom", loai, None)
        assert cu == moi and "cum" not in moi
        assert "ĐỘC LẬP" not in RSA.format_outcome_text(moi, cot)


def test_lien_tuc_cum_trung_uoc_luong_diem_va_ktc_rong_hon():
    df = _du_lieu()
    r = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous", "ban")
    cu = r["cum"]
    assert cu["cov_type"] == "cluster" and cu["so_cum"] == 30 and cu["n"] == len(df)
    assert cu["md_cum"] == pytest.approx(r["md_crude"], abs=1e-3)
    lo, hi = cu["md_ci_95_cum"]
    se_doc_lap = np.sqrt(sum(df.loc[df.nhom == g, "diem"].var() / (df.nhom == g).sum() for g in (0, 1)))
    assert (hi - lo) > 2 * 1.96 * se_doc_lap * 2  # ICC cao ⇒ KTC cụm rộng hơn > 2 lần
    txt = RSA.format_outcome_text(r, "diem")
    assert "HIỆU CHỈNH CỤM «ban» (30 cụm)" in txt and "MD thô (cụm)" in txt and "ĐỘC LẬP" in txt


def test_nhi_phan_cum_or_va_rd():
    df = _du_lieu(hieu_ung=0.5)
    r = RSA.compare_primary_outcome(df, "hl", "nhom", "binary", "ban")
    cu = r["cum"]
    assert cu["or_cum"] == pytest.approx(r["or_crude"], abs=2e-3)
    assert cu["risk_diff_cum"] == pytest.approx(r["risk_diff"], abs=1e-4)
    rd_lo, rd_hi = cu["risk_diff_ci_95_cum"]
    lo0, hi0 = r["risk_diff_ci_95"]
    assert rd_hi - rd_lo > hi0 - lo0
    or_lo, or_hi = cu["ci_95_cum"]
    assert or_hi / or_lo > r["ci_95"][1] / r["ci_95"][0]
    txt = RSA.format_outcome_text(r, "hl")
    assert "OR thô (cụm)" in txt and "Risk difference (cụm)" in txt


def test_nhi_phan_ma_hoa_1_2_dem_dung_bien_co():
    df = _du_lieu(hieu_ung=0.5)
    ma = df.assign(hl=df["hl"] + 1)  # REDCap 1/2
    a = RSA.compare_primary_outcome(df, "hl", "nhom", "binary", "ban")["cum"]
    b = RSA.compare_primary_outcome(ma, "hl", "nhom", "binary", "ban")["cum"]
    assert a["or_cum"] == b["or_cum"] and a["risk_diff_cum"] == b["risk_diff_cum"]


def test_do_phu_ktc_khi_nhom_gan_theo_cum():
    """Không có hiệu ứng thật: KTC độc lập phủ < 80%, KTC cụm phủ gần 95%."""
    phu_doc_lap = phu_cum = 0
    lan = 150
    for s in range(lan):
        df = _du_lieu(seed=100 + s, n=600, k=40)
        r = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous", "ban")
        md = r["md_crude"]
        se = np.sqrt(sum(df.loc[df.nhom == g, "diem"].var() / (df.nhom == g).sum() for g in (0, 1)))
        phu_doc_lap += abs(md) <= 1.96 * se
        lo, hi = r["cum"]["md_ci_95_cum"]
        phu_cum += lo <= 0 <= hi
    assert phu_doc_lap / lan < 0.80
    assert 0.86 <= phu_cum / lan <= 1.0


def test_dong_thieu_ma_cum_bi_loai_va_ghi_so():
    df = _du_lieu()
    df.loc[:9, "ban"] = np.nan
    cu = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous", "ban")["cum"]
    assert cu["n"] == len(df) - 10 and cu["loai_thieu_ma_cum"] == 10
    assert "Loại 10 hàng thiếu mã cụm" in "\n".join(RSA._dong_bang2_cum(cu))


def test_mot_cum_bao_loi_ro():
    df = _du_lieu().assign(ban=1)
    r = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous", "ban")
    assert "không hiệu chỉnh cụm được" in r["cum"]["error"]
    assert "[CẦN THỐNG KÊ VIÊN]" in RSA.format_outcome_text(r, "diem")


def test_mot_nhom_khong_bien_co_khong_bia_or():
    df = _du_lieu(hieu_ung=0.5)
    df.loc[df.nhom == 0, "hl"] = 0
    cu = RSA.compare_primary_outcome(df, "hl", "nhom", "binary", "ban")["cum"]
    assert "or_cum" not in cu and "0% hoặc 100%" in cu["ghi_chu"]
    assert "risk_diff_cum" in cu


def _gia_lap_cong(monkeypatch):
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda *a, **k: {})
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})


def test_main_bang2_co_cum(tmp_path, monkeypatch):
    _gia_lap_cong(monkeypatch)
    monkeypatch.chdir(tmp_path)
    duong = tmp_path / "d.csv"
    _du_lieu(n=600).to_csv(duong, index=False)
    monkeypatch.setattr(sys, "argv", [
        "run_stats_analysis.py", "--data", str(duong), "--outcome", "diem", "--group", "nhom",
        "--outcome-type", "continuous", "--cot-cum", "ban", "--study", "SYN", "--gate", "G6"])
    RSA.main()
    out = tmp_path / "exports" / "SYN"
    assert "HIỆU CHỈNH CỤM «ban»" in (out / "G6_table2_main_outcome.txt").read_text(encoding="utf-8")
    tom = json.loads((out / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["primary_outcome"]["cum"]["cov_type"] == "cluster"
