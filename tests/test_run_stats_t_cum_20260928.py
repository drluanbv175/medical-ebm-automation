"""N11 (28/09/2026) — KTC/p hiệu chỉnh cụm của engine G6 dùng phân phối t(G−1) thay cho z.

Trước bản vá, statsmodels ``cov_type='cluster'`` mặc định suy luận theo z: với ít cụm (vd 12 bàn khám) KTC hẹp
giả và p nhỏ giả (đo: p z 0,060 so với p t(11) 0,087). Quy ước t(G−1) + hiệu chỉnh CR1 là khuyến nghị thông
dụng cho SE sandwich theo cụm khi số cụm hữu hạn [CẦN KIỂM CHỨNG nguồn trích dẫn cụ thể khi đưa vào SAP].
Kiểm từng chỗ fit: Bảng 2, Bảng 4 (logistic + OLS), Bảng 5 (MI — MICE bỏ qua use_t nên tự tính), logistic thứ tự,
OLS nhạy cảm; không cụm ⇒ không đổi. Dữ liệu synthetic, không PII.
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

sm = pytest.importorskip("statsmodels.api")
from scipy import stats  # noqa: E402

K = 8


def _du_lieu(seed: int = 5, n: int = 400, k: int = K, hieu_ung: float = 0.3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    c = rng.integers(0, k, n)
    nhom = rng.permutation(np.arange(k) % 2)[c]  # nhóm cân bằng theo cụm, luôn đủ 2 nhóm
    u = rng.normal(0, 1.0, k)[c]
    x = rng.normal(0, 1, n)
    diem = 5 + hieu_ung * nhom + 0.5 * x + u + rng.normal(0, 1, n)
    hl = (rng.random(n) < 1 / (1 + np.exp(-(0.3 * nhom + 0.5 * x + u)))).astype(int)
    thu_tu = np.digitize(0.5 * x + 0.4 * nhom + u + rng.logistic(size=n), [-1.5, 0, 1.5]) + 1
    return pd.DataFrame({"diem": diem, "hl": hl, "nhom": nhom, "x": x, "g1": thu_tu, "ban": c})


def _tham_chieu_ols(df, y, cot_x, dung_t):
    X = sm.add_constant(df[cot_x].astype(float))
    return sm.OLS(df[y].astype(float), X).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(df["ban"])[0]}, use_t=dung_t)


def test_bang2_lien_tuc_p_theo_t_g_tru_1():
    df = _du_lieu()
    cu = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous", "ban")["cum"]
    ref_t = _tham_chieu_ols(df, "diem", ["nhom"], True)
    ref_z = _tham_chieu_ols(df, "diem", ["nhom"], False)
    assert ref_t.df_resid_inference == K - 1
    assert cu["p_cum"] == round(float(ref_t.pvalues["nhom"]), 4)
    assert cu["p_cum"] > round(float(ref_z.pvalues["nhom"]), 4)
    lo, hi = ref_t.conf_int().loc["nhom"]
    assert cu["md_ci_95_cum"] == (round(float(lo), 3), round(float(hi), 3))


def test_bang2_nhi_phan_or_va_rd_theo_t():
    df = _du_lieu()
    cu = RSA.compare_primary_outcome(df, "hl", "nhom", "binary", "ban")["cum"]
    X = sm.add_constant(df["nhom"].astype(float))
    kw = {"cov_type": "cluster", "cov_kwds": {"groups": pd.factorize(df["ban"])[0]}, "use_t": True}
    ref = sm.Logit(df["hl"].astype(float), X).fit(disp=False, **kw)
    assert cu["p_cum"] == round(float(ref.pvalues["nhom"]), 4)
    ref_rd = sm.OLS(df["hl"].astype(float), X).fit(**kw)
    assert cu["p_rd_cum"] == round(float(ref_rd.pvalues["nhom"]), 4)


def test_do_phu_ktc_it_cum_gan_95():
    """Không có hiệu ứng thật, 8 cụm: KTC t(G−1) phủ ≥ 88%; KTC z cùng SE phủ thấp hơn rõ."""
    phu_t = phu_z = 0
    lan = 200
    for s in range(lan):
        df = _du_lieu(seed=1000 + s, n=240, hieu_ung=0.0)
        cu = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous", "ban")["cum"]
        lo, hi = cu["md_ci_95_cum"]
        phu_t += lo <= 0 <= hi
        se = (hi - lo) / (2 * stats.t.ppf(0.975, K - 1))
        phu_z += abs(cu["md_cum"]) <= 1.96 * se
    assert phu_t / lan >= 0.88
    assert phu_z / lan < phu_t / lan - 0.02


def test_da_bien_ols_va_logistic_theo_t():
    df = _du_lieu(n=600)
    mv = RSA.multivariate_model(df, "diem", "nhom", ["x"], "continuous", "ban")
    ref = _tham_chieu_ols(df, "diem", ["nhom", "x"], True)
    dong = {r["variable"]: r for r in mv["results"]}
    assert dong["nhom"]["p"] == round(float(ref.pvalues["nhom"]), 4)
    mvb = RSA.multivariate_model(df, "hl", "nhom", ["x"], "binary", "ban")
    X = sm.add_constant(df[["nhom", "x"]].astype(float))
    refb = sm.Logit(df["hl"].astype(float), X).fit(
        disp=False, cov_type="cluster", cov_kwds={"groups": pd.factorize(df["ban"])[0]}, use_t=True)
    dong_b = {r["variable"]: r for r in mvb["results"]}
    assert dong_b["nhom"]["p"] == round(float(refb.pvalues["nhom"]), 4)


def test_suy_luan_t_cum_khop_scipy():
    ci, p = RSA._suy_luan_t_cum(pd.Series([0.5, -1.0]), pd.Series([0.2, 0.4]), 6)
    q = stats.t.ppf(0.975, 5)
    assert ci[0].tolist() == pytest.approx([0.5 - q * 0.2, 0.5 + q * 0.2])
    assert p.tolist() == pytest.approx([2 * stats.t.sf(2.5, 5), 2 * stats.t.sf(2.5, 5)])


def test_mi_cum_p_nhat_quan_voi_t_g_tru_1():
    df = _du_lieu(seed=11, n=500, k=6, hieu_ung=1.5)
    df.loc[df.index[:60], "x"] = np.nan
    mi = RSA.multiple_imputation_model(df, "diem", "nhom", ["x"], "continuous", 5, "ban")
    r = next(v for v in mi["results"] if v["variable"] == "nhom")
    lo, hi = r["CI_95"]
    q = stats.t.ppf(0.975, 5)
    se = (hi - lo) / (2 * q)
    assert r["p"] == pytest.approx(2 * stats.t.sf(abs(r["beta"]) / se, 5), abs=2e-3)
    p_z = 2 * stats.norm.sf(abs(r["beta"]) / se)
    assert r["p"] - p_z > 0.01
    assert "G−1 = 5 bậc tự do" in " ".join(mi["canh_bao"])


def test_thu_tu_va_ols_nhay_cam_theo_t():
    df = _du_lieu(n=600)
    od = RSA.ordinal_model(df, "g1", "nhom", ["x"], "ban")
    r = next(v for v in od["results"] if v["variable"] == "nhom")
    lo, hi = np.log(r["CI_95"])
    se = (hi - lo) / (2 * stats.t.ppf(0.975, K - 1))
    assert r["p"] == pytest.approx(2 * stats.t.sf(abs(np.log(r["OR_adj"])) / se, K - 1), abs=5e-3)
    lh = RSA.linear_hc3(df, "g1", "nhom", ["x"], "ban")
    ref = _tham_chieu_ols(df, "g1", ["nhom", "x"], True)
    assert next(v for v in lh["results"] if v["variable"] == "nhom")["p"] == round(float(ref.pvalues["nhom"]), 4)


def test_khong_cum_giu_z_va_khong_khoa_moi():
    df = _du_lieu()
    r = RSA.compare_primary_outcome(df, "diem", "nhom", "continuous")
    assert "cum" not in r
    lh = RSA.linear_hc3(df, "diem", "nhom", ["x"])
    X = sm.add_constant(df[["nhom", "x"]].astype(float))
    ref = sm.OLS(df["diem"], X).fit(cov_type="HC3")
    assert next(v for v in lh["results"] if v["variable"] == "nhom")["p"] == round(float(ref.pvalues["nhom"]), 4)


def test_script_r_dung_t_g_tru_1_khi_co_cum():
    nhi = RSA.generate_r_script("S", "G6", "hl", "nhom", ["x"], "binary", "ban")
    assert "df_cum <- length(unique(na.omit(data$ban))) - 1" in nhi
    assert nhi.count("df = df_cum") == 5  # 3b coeftest+coefci · 3c coeftest+coefci · RD coefci
    assert "df_cum" not in RSA.generate_r_script("S", "G6", "hl", "nhom", ["x"], "binary")
    od = RSA.generate_r_script_ordinal("S", "G6", "g1", "nhom", ["x"], "ban")
    assert "df_suy_luan <- length(unique(na.omit(data$ban))) - 1" in od
    assert "coeftest(m_lm, vcov = vc, df = df_suy_luan)" in od
    assert "df_suy_luan <- Inf" in RSA.generate_r_script_ordinal("S", "G6", "g1", "nhom", ["x"], None)
