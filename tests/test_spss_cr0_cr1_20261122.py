"""Cầu nối SPSS — quy đổi SE robust GEE (CR0 + z) sang CR1 + t(G−1) như Python (việc H, 22/11/2026).

Giả lập rct_cum có 5 phân tích «lệch nhỏ»: mọi dòng lệch là Poisson theo cụm, ghi chú «GEE robust (SPSS) ≠ sandwich CR1
+ t(G−1) (Python)». Truy ca: KTC SPSS của PR thô «nhom» [1,20328; 1,78771] trùng ĐÚNG sandwich::vcovCL(type = "HC0",
cadjust = FALSE) + z [1,203275; 1,787713] trên cùng dữ liệu khoá (N = 320, G = 40) — tức CR0. Python/R dùng CR1 =
CR0·G/(G−1)·(N−1)/(N−K) + t(G−1). Khác biệt là một hệ số đóng (căn cứ phương pháp), không phải lỗi ⇒ quy đổi SPSS rồi so
với dung sai CHẶT, không nới dung sai. Số dưới đây chép từ G6_spss_doi_chieu.json của lượt giả lập rct_cum (không PII).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as S  # noqa: E402

# (biến, Python {PR, CI, p}, SPSS {PR, CI, p}) — PR thô và PR hiệu chỉnh của rct_cum
THO = [("nhom", (1.4667, [1.1922, 1.8043], 0.0006), (1.4666666666667, [1.2032797325201, 1.7877065930512], 0.000149)),
       ("tuoi", (0.9961, [0.9885, 1.0038], 0.313), (0.99611292322955, [0.98880598291419, 1.0034738593517], 0.2998)),
       ("gioi_2", (1.3359, [1.086, 1.6435], 0.0074), (1.3359375, [1.096067189101, 1.6283025544903], 0.004125))]
HC = [("nhom", (1.4538, [1.1809, 1.7896], 0.0008), (1.4537642889959, [1.1927134581588, 1.7719516733066], 0.000211)),
      ("tuoi", (0.9958, [0.988, 1.0037], 0.2857), (0.99580677936221, [0.98838808724831, 1.0032811550617], 0.2707)),
      ("gioi_2", (1.3582, [1.1035, 1.6718], 0.0049), (1.3582348714754, [1.1144760468152, 1.6553087626814], 0.002414))]


def _tom_kq(cum: bool = True, so_cum: int = 40) -> tuple[dict, dict]:
    pr = {"model": "poisson_robust_cluster", "n": 320, "nhom_bien": {"nhom": ["nhom"], "tuoi": ["tuoi"],
                                                                      "gioi": ["gioi_2"]},
          "tho": [{"variable": v, "PR": a[0], "CI_95": a[1], "p": a[2]} for v, a, _b in THO],
          "results": [{"variable": v, "PR_adj": a[0], "CI_95": a[1], "p": a[2]} for v, a, _b in HC]}
    if cum:
        pr.update(cov_type="cluster", cluster={"cot": "ma_phong_kham", "so_cum": so_cum})
    kq = {"poisson_tho": {"he_so": {v: {"uoc_luong": b[0], "ci": b[1], "p": b[2]} for v, _a, b in THO}},
          "poisson_hieu_chinh": {"he_so": {v: {"uoc_luong": b[0], "ci": b[1], "p": b[2]} for v, _a, b in HC}}}
    return {"poisson_pr": pr}, kq


def _poisson(dong: list[dict]) -> list[dict]:
    return [x for x in dong if x["muc"].startswith("Poisson")]


def test_rct_cum_poisson_cum_quy_doi_xong_thi_khop_chat():
    tom, kq = _tom_kq()
    ds = _poisson(S.doi_chieu(tom, kq))
    assert len(ds) == 6 and all(x["trang_thai"] == "khop" for x in ds), [(x["muc"], x["trang_thai"], x["kiem"])
                                                                           for x in ds]
    assert all(S.GHI_CHU_CR0_CR1 in x["ghi_chu"] and "spss_goc" in x for x in ds)
    nhom = next(x for x in ds if x["muc"].endswith("PR thô — nhom"))
    assert nhom["spss"]["ci"] == pytest.approx([1.1922, 1.8043], abs=2e-4)  # = KTC Python sau quy đổi
    # K = số tham số của CHÍNH mô hình: PR thô của một biến = 2 (biến + hằng số); hiệu chỉnh = 4 (3 biến + hằng số)
    hc = next(x for x in ds if x["muc"].endswith("PR hiệu chỉnh — nhom"))
    sp_tho, sp_hc = THO[0][2], HC[0][2]
    assert nhom["spss"]["ci"] == pytest.approx(S.quy_doi_cr0_cr1(
        {"uoc_luong": sp_tho[0], "ci": sp_tho[1]}, 40, 320, 2, True)["ci"], rel=1e-12)
    assert hc["spss"]["ci"] == pytest.approx(S.quy_doi_cr0_cr1(
        {"uoc_luong": sp_hc[0], "ci": sp_hc[1]}, 40, 320, 4, True)["ci"], rel=1e-12)


def test_quy_doi_dung_he_so_va_t_g_tru_1():
    import math

    from scipy import stats as st

    qd = S.quy_doi_cr0_cr1({"uoc_luong": 1.4666666666667, "ci": [1.2032797325201, 1.7877065930512]}, 40, 320, 2,
                           True)
    se0 = (math.log(1.7877065930512) - math.log(1.2032797325201)) / (2 * S.Z_975)
    se1 = se0 * math.sqrt(40 / 39 * 319 / 318)
    b = math.log(1.4666666666667)
    assert qd["ci"] == pytest.approx([math.exp(b - st.t.ppf(0.975, 39) * se1), math.exp(b + st.t.ppf(0.975, 39) * se1)])
    assert qd["p"] == pytest.approx(2 * st.t.sf(abs(b / se1), 39))
    assert S.quy_doi_cr0_cr1({"uoc_luong": 1.2, "ci": [1.0, 1.4]}, 1, 320, 2, True) is None  # < 2 cụm


def test_spss_lech_that_sau_quy_doi_van_la_lech():
    """Không nới dung sai: SE SPSS lớn hơn 10 % (lỗi thật) ⇒ LỆCH, không còn «lệch nhỏ» che."""
    tom, kq = _tom_kq()
    sp = kq["poisson_hieu_chinh"]["he_so"]["nhom"]
    import math

    b = math.log(sp["uoc_luong"])
    se0 = (math.log(sp["ci"][1]) - math.log(sp["ci"][0])) / (2 * S.Z_975) * 1.10
    sp["ci"] = [math.exp(b - S.Z_975 * se0), math.exp(b + S.Z_975 * se0)]
    d = next(x for x in _poisson(S.doi_chieu(tom, kq)) if x["muc"].endswith("PR hiệu chỉnh — nhom"))
    assert d["trang_thai"] == "lech", d


def test_thieu_so_cum_khong_quy_doi_duoc_thi_ghi_ro_ly_do():
    tom, kq = _tom_kq()
    tom["poisson_pr"]["cluster"] = {"cot": "ma_phong_kham"}  # không ghi số cụm (tóm tắt cũ)
    ds = _poisson(S.doi_chieu(tom, kq))
    assert all("thiếu N/G để quy đổi" in x["ghi_chu"] for x in ds), [x["ghi_chu"] for x in ds]


def test_da_bien_logistic_cum_quy_doi_khop_statsmodels():
    """Logistic theo cụm: CR0 + z (statsmodels use_correction=False — cùng ước lượng với GEE độc lập robust của SPSS)
    quy đổi xong phải trùng mô hình CR1 + t(G−1) của run_stats_analysis.multivariate_model."""
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    sm = pytest.importorskip("statsmodels.api")
    import run_stats_analysis as RSA

    rng = np.random.default_rng(4)
    n, g = 600, 30
    cum = np.repeat(np.arange(g), n // g)
    x1 = rng.normal(0, 1, n)
    nhom = rng.binomial(1, 0.5, g)[cum]
    lp = -0.5 + 0.6 * nhom + 0.4 * x1 + rng.normal(0, 0.5, g)[cum]
    df = pd.DataFrame({"y": rng.binomial(1, 1 / (1 + np.exp(-lp))), "nhom": nhom, "x1": x1, "cum": cum})
    mv = RSA.multivariate_model(df, "y", "nhom", ["x1"], "binary", "cum")
    X = sm.add_constant(df[["nhom", "x1"]].astype(float))
    m0 = sm.GLM(df["y"].astype(float), X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": df["cum"].to_numpy(), "use_correction": False})
    ci0 = m0.conf_int()
    he = {v: {"uoc_luong": float(np.exp(m0.params[v])), "ci": [float(np.exp(ci0.loc[v, 0])),
                                                                  float(np.exp(ci0.loc[v, 1]))],
              "p": float(m0.pvalues[v])} for v in ("nhom", "x1")}
    tom = {"multivariate": mv, "dac_ta_phan_tich": {"cot_cum": "cum"}}
    ds = [x for x in S.doi_chieu(tom, {"da_bien_cum": {"he_so": he}}) if x["muc"].startswith("Đa biến")]
    assert len(ds) == 2 and all(x["trang_thai"] == "khop" for x in ds), [(x["muc"], x["kiem"], x["spss"],
                                                                           x["python"]) for x in ds]
