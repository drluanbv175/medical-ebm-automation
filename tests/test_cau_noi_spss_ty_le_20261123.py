"""Cầu nối SPSS — Bảng 1b (tỷ lệ + KTC Wilson, có/không cụm) và quy đổi hồi quy THỨ TỰ theo cụm (23/11/2026).

(1) Bảng 1b: trước đây phần SPSS của kiểm chéo ghi «không đo được» cho mọi phân tích cắt ngang. Nay:
    • Wilson độc lập: thủ tục PROPORTIONS … CITYPES=WILSON_SCORE (cài đặt riêng của SPSS);
    • theo cụm: CSDESCRIPTIVES (Complex Samples, CLUSTER, WR) cho phương sai thiết kế (tuyến tính hoá), rồi DE (chặn
      dưới 1), n/DE × (z/t_{K−1})² và Wilson tính bằng cú pháp — đúng công thức Python;
    • đối chiếu theo đơn vị làm tròn của tóm tắt Python (phép tất định), như bản R.
(2) Hồi quy thứ tự theo cụm: SPSS GENLIN GEE cho β trùng nhưng SE là sandwich CR0 với bánh mì Fisher (kỳ vọng) + z;
    Python dùng bánh mì Hessian quan sát + CR1 + t(G−1). Đo bằng số (dữ liệu 600 ca, 30 cụm): tỷ số SE ngược chiều
    giữa các hệ số (0,986 và 1,035) ⇒ không có hệ số đóng; Python ghi SE bánh mì Fisher CR0 để quy đổi.
Máy không có SPSS ⇒ test chạy thật tự bỏ qua. Dữ liệu mô phỏng, không PII.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("statsmodels")
import cau_noi_spss as S  # noqa: E402


# ───────────────────────────── cú pháp ─────────────────────────────
def _man(cot_so=True) -> dict:
    bien = [{"cot": c, "ten": c, "so": cot_so if c == "g1" else True, "muc": None, "muc_do": "SCALE"}
            for c in ("record_id", "g1", "gioi", "cum")]
    return {"sav": "/tmp/x.sav", "bien": bien}


def _dt(cum: str | None = "cum", nguong: float | None = 4.0) -> dict:
    return {"outcome": None, "group": None, "time": None, "event": None, "cot_cum": cum, "covariates": [],
            "outcome_type": "auto", "ty_le": ["g1"], "nguong_ty_le": nguong}


def test_cu_phap_ty_le_wilson_va_phuong_sai_thiet_ke():
    vb, _cb, _phu = S.cu_phap_phan_tich("X", _man(), _dt(), Path("/tmp/kq"))
    a = vb.index("DATASET NAME ebm_goc")
    khoi = vb[a:vb.index("OMSEND TAG='ebm_spv'.")]
    assert "PROPORTIONS /ONESAMPLE ebm_y TESTVAL=0.5 TESTTYPES=NONE CITYPES=WILSON_SCORE" in khoi
    assert "COMPUTE ebm_y = (g1 >= 4.0)." in khoi and "SELECT IF (NOT MISSING(g1) AND NOT MISSING(cum))." in khoi
    assert "/DESIGN CLUSTER=cum /ESTIMATOR TYPE=WR." in khoi and "CSDESCRIPTIVES" in khoi
    assert "IF (ebm_vs > 0) ebm_de = MAX(1, StandardError ** 2 / ebm_vs)." in khoi
    assert "COMPUTE ebm_hs = (ebm_z / IDF.T(0.975, ebm_k - 1)) ** 2." in khoi
    assert "COMPUTE ebm_nh = ebm_n / ebm_de * ebm_hs." in khoi
    # khối OMS của Bảng 1b nằm SAU bản sao bộ dữ liệu (không chen trước phân tích khác)
    assert khoi.index("DATASET COPY ebm_tl_1.") < khoi.index("oms_ty_le_1.xml") < khoi.index("oms_ty_le_cum_1.xml")
    assert vb.count("oms_ty_le_1.xml") == 1


def test_cu_phap_ty_le_khong_cum_cot_chu_va_cot_0_1():
    vb, _cb, _phu = S.cu_phap_phan_tich("X", _man(cot_so=False), _dt(cum=None, nguong=None), Path("/tmp/kq"))
    assert "COMPUTE ebm_x = NUMBER(g1, F40.0)." in vb and "COMPUTE ebm_y = ebm_x." in vb
    assert "CSDESCRIPTIVES" not in vb and "oms_ty_le_cum_1" not in vb


def test_bien_tam_trung_ten_thi_tu_choi():
    man = _man()
    man["bien"].append({"cot": "ebm_de", "ten": "ebm_de", "so": True, "muc": None})
    with pytest.raises(S.TuChoi, match="biến tạm"):
        S.cu_phap_phan_tich("X", man, _dt(), Path("/tmp/kq"))


def test_dac_ta_ty_le_va_lech_dac_ta():
    assert S.ty_le_tu_tom_tat({"dac_ta_phan_tich": {"ty_le": ["g1"], "nguong_ty_le": 4.0}}) == (["g1"], 4.0)
    lech = S.lech_dac_ta({"ty_le": ["g1"], "nguong_ty_le": 3.0}, {"ty_le": ["g2"], "nguong_ty_le": 4.0}, {})
    assert any(x.startswith("ty_le") for x in lech) and any(x.startswith("nguong_ty_le") for x in lech), lech


# ───────────────────────────── đối chiếu ─────────────────────────────
def _py_sp(lech_ci=0.0, lech_de=0.0, n_sp=None) -> tuple[dict, dict]:
    import run_stats_analysis as RSA

    rng = np.random.default_rng(5)
    cum = np.repeat(np.arange(30), 20)
    lp = np.log(0.35 / 0.65) + rng.normal(0, 0.6, 30)[cum]
    df = pd.DataFrame({"y": rng.binomial(1, 1 / (1 + np.exp(-lp))), "cum": cum})
    x = RSA.ty_le_wilson_cum(df, "y", None, "cum")
    from statsmodels.stats.proportion import proportion_confint

    n, e = len(df), int(df["y"].sum())
    p = e / n
    t_c = df.groupby("cum")["y"].sum().to_numpy()
    m_c = df.groupby("cum")["y"].size().to_numpy()
    se2 = 30 / 29 * float(((t_c - p * m_c) ** 2).sum()) / n**2
    de = max(1.0, se2 / (p * (1 - p) / n))
    from scipy import stats as st

    n_hd = n / de * (st.norm.ppf(0.975) / st.t.ppf(0.975, 29)) ** 2
    lo, hi = proportion_confint(p * n_hd, n_hd, method="wilson")
    sp = {"y": {"n": n_sp or n, "so_su_kien": e, "ty_le": p,
                "ci_doc_lap": list(proportion_confint(e, n, method="wilson")), "n_cum": n_sp or n, "so_cum": 30,
                "ty_le_cum": p, "de": de + lech_de, "ci": [lo + lech_ci, hi]}}
    return {"ty_le": [x]}, {"ty_le": sp}


def test_doi_chieu_ty_le_khop_den_don_vi_lam_tron():
    tom, kq = _py_sp()
    ds = S.doi_chieu_ty_le(tom, kq)
    assert len(ds) == 3 and all(x["trang_thai"] == "khop" for x in ds), [(x["muc"], x["kiem"]) for x in ds]


def test_doi_chieu_ty_le_lech_qua_don_vi_lam_tron_va_so_ca_khac():
    tom, kq = _py_sp(lech_ci=0.0002, lech_de=0.002)
    ds = {x["muc"].split(" — ")[0]: x for x in S.doi_chieu_ty_le(tom, kq)}
    assert ds["Tỷ lệ + KTC Wilson theo cụm (n/DE·(z/t)²)"]["trang_thai"] == "lech"
    assert ds["Hiệu ứng thiết kế (DE)"]["trang_thai"] == "lech"
    tom, kq = _py_sp(n_sp=599)
    assert all(x["trang_thai"] == "lech" and "SỐ CA KHÁC" in x["ghi_chu"] for x in S.doi_chieu_ty_le(tom, kq))


def test_doi_chieu_ty_le_spss_thieu_hoac_python_loi():
    assert S.doi_chieu_ty_le({"ty_le": [{"cot": "y", "ty_le": 0.3}]}, {})[0]["trang_thai"] == "khong_so_duoc"
    ds = S.doi_chieu_ty_le({"ty_le": [{"cot": "y", "error": "x"}]}, {"ty_le": {"y": {"ty_le": 0.3}}})
    assert ds[0]["trang_thai"] == "khong_so_duoc" and "Python lỗi" in ds[0]["ghi_chu"]
    assert S.doi_chieu_ty_le({}, {}) == []
    tom, kq = _py_sp()
    muc = [x["muc"] for x in S.doi_chieu(tom, kq)]
    assert any(m.startswith("Tỷ lệ + KTC Wilson theo cụm") for m in muc)


# ───────────────────────────── (2) hồi quy thứ tự theo cụm ─────────────────────────────
def _thu_tu(seed=7) -> "pd.DataFrame":
    rng = np.random.default_rng(seed)
    G, m = 30, 20
    cum = np.repeat(np.arange(G), m)
    nhom = rng.binomial(1, 0.5, G)[cum]
    tuoi = rng.normal(60, 10, G * m)
    lat = 0.7 * nhom + 0.03 * (tuoi - 60) + rng.normal(0, 0.6, G)[cum] + rng.logistic(0, 1, G * m)
    return pd.DataFrame({"g1": (np.digitize(lat, [-1.0, 0.0, 1.0, 2.0]) + 1).astype(float), "nhom": nhom,
                         "tuoi": tuoi.round(1), "cum": cum})


def test_se_fisher_cr0_python_bang_sandwich_tinh_tay_va_khac_hessian_quan_sat():
    """SE bánh mì Fisher CR0 mà Python ghi = sandwich tính tay độc lập (điểm số + thông tin kỳ vọng); khác SE chính theo
    tỷ số KHÔNG cố định giữa các hệ số (căn cứ cần quy đổi riêng, không phải hệ số đóng như Poisson)."""
    import run_stats_analysis as RSA
    from scipy.stats import logistic

    df = _thu_tu()
    o = RSA.ordinal_model(df, "g1", "nhom", ["tuoi"], "cum")
    r = {x["variable"]: x for x in o["results"]}
    assert o["k_tham_so"] == 6 and all("se" in x and "se_cr0_fisher" in x for x in r.values())
    # tính tay: β từ chính lượt fit, điểm số và thông tin kỳ vọng theo định nghĩa
    from statsmodels.miscmodels.ordinal_model import OrderedModel

    y = df["g1"].astype(int).to_numpy()
    X = df[["nhom", "tuoi"]].astype(float)
    fit = OrderedModel(y, X, distr="logit").fit(method="bfgs", disp=False, maxiter=2000)
    th = fit.model.transform_threshold_params(fit.params)
    b = np.asarray(fit.params)[:2]
    xa = X.to_numpy()
    se_tay = []
    yi = np.searchsorted(np.sort(np.unique(y)), y)
    eta = th[None, :] - (xa @ b)[:, None]
    P, f = np.diff(logistic.cdf(eta), axis=1), logistic.pdf(eta)
    J = P.shape[1]

    def diem(i, j):
        s = np.zeros(2 + J - 1)
        s[:2] = -xa[i] * (f[i, j + 1] - f[i, j]) / P[i, j]
        if j < J - 1:
            s[2 + j] += f[i, j + 1] / P[i, j]
        if j > 0:
            s[2 + j - 1] -= f[i, j] / P[i, j]
        return s

    info = sum(P[i, j] * np.outer(diem(i, j), diem(i, j)) for i in range(len(y)) for j in range(J))
    sc = np.array([diem(i, yi[i]) for i in range(len(y))])
    meat = sum(np.outer(sc[df["cum"].to_numpy() == c].sum(0), sc[df["cum"].to_numpy() == c].sum(0))
               for c in range(30))
    B = np.linalg.inv(info)
    se_tay = np.sqrt(np.diag(B @ meat @ B))[:2]
    assert r["nhom"]["se_cr0_fisher"] == pytest.approx(se_tay[0], rel=1e-4)
    assert r["tuoi"]["se_cr0_fisher"] == pytest.approx(se_tay[1], rel=1e-4)
    ty = [r[v]["se"] / r[v]["se_cr0_fisher"] for v in ("nhom", "tuoi")]
    assert abs(ty[0] - ty[1]) > 0.03, ty  # không có một hệ số chung


def _tom_tt(se=0.2128314612, se_f=0.2055563051) -> dict:
    return {"ordinal": {"model": "ordinal_logit_po", "n": 600, "cov_type": "cluster", "k_tham_so": 6,
                        "cluster": {"cot": "cum", "so_cum": 30},
                        "results": [{"variable": "nhom", "OR_adj": 2.335, "CI_95": [1.511, 3.608], "p": 0.0004,
                                     "se": se, "se_cr0_fisher": se_f}]},
            "dac_ta_phan_tich": {"cot_cum": "cum"}}


#: Số SPSS thật (GENLIN MULTINOMIAL CUMLOGIT /REPEATED … COVB=ROBUST, SPSS 31, dữ liệu _thu_tu(7)) — đo 23/11/2026.
SPSS_THU_TU = {"nhom": {"uoc_luong": 2.3349212895916, "ci": [1.5606386181846, 3.4933503279126],
                        "p": 3.7027915752108e-05}}


def test_thu_tu_cum_quy_doi_xong_thi_khop_chat():
    ds = [x for x in S.doi_chieu(_tom_tt(), {"da_bien_cum": {"he_so": SPSS_THU_TU}}) if x["muc"].startswith("Hồi quy")]
    assert len(ds) == 1 and ds[0]["trang_thai"] == "khop", ds
    assert S.GHI_CHU_THU_TU_CUM in ds[0]["ghi_chu"] and ds[0]["spss_goc"]["ci"] == SPSS_THU_TU["nhom"]["ci"]
    b = math.log(2.3349212895916)
    se0 = (math.log(3.4933503279126) - math.log(1.5606386181846)) / (2 * S.Z_975)
    from scipy import stats as st

    se1 = se0 * 0.2128314612 / 0.2055563051
    assert ds[0]["spss"]["ci"] == pytest.approx([math.exp(b - st.t.ppf(0.975, 29) * se1),
                                                 math.exp(b + st.t.ppf(0.975, 29) * se1)])


def test_thu_tu_cum_se_spss_khac_fisher_la_lech_va_thieu_so_thi_ghi_ly_do():
    """Không nới dung sai: nếu SE SPSS không trùng SE Fisher của Python (giả lập lệch 5 %) ⇒ LỆCH."""
    ds = [x for x in S.doi_chieu(_tom_tt(se_f=0.2055563051 * 1.05), {"da_bien_cum": {"he_so": SPSS_THU_TU}})
          if x["muc"].startswith("Hồi quy")]
    assert ds[0]["trang_thai"] == "lech", ds[0]
    tom = _tom_tt()
    del tom["ordinal"]["results"][0]["se_cr0_fisher"]
    ds = [x for x in S.doi_chieu(tom, {"da_bien_cum": {"he_so": SPSS_THU_TU}}) if x["muc"].startswith("Hồi quy")]
    assert "thiếu số để quy đổi" in ds[0]["ghi_chu"], ds[0]


# ───────────────────────────── chạy thật với SPSS ─────────────────────────────
CO_SPSS = any(p.is_file() for p in S.ung_vien_python_spss())
CAN_SPSS = pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")


def _khung_spss(tmp_path: Path, monkeypatch, study: str, df: "pd.DataFrame", tham_so: list[str],
                tu_dien: list[list[str]]) -> Path:
    from tests.test_cau_noi_r_ty_le_20261122 import _khung

    d = _khung(tmp_path, monkeypatch, study, df, tham_so)
    with open(d / f"G5_REDCap_dictionary_{study}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Variable / Field Name", "Field Type", "Field Label", "Choices, Calculations, OR Slider Labels",
                    "Text Validation Type OR Show Slider Number", "Identifier?"])
        w.writerows(tu_dien)
    monkeypatch.setattr(S, "kiem_noi_dung_bien", lambda *a, **k: None)  # E4 (nội dung đề tài) ngoài phạm vi phép này
    return d


def _chay_spss(study: str, monkeypatch) -> dict:
    import kiem_cheo_g6 as KC

    monkeypatch.setattr(KC, "EXPORTS", S.EXPORTS)
    with contextlib.redirect_stdout(io.StringIO()):
        KC.main(["chay", "--study", study, "--chi", "spss"])
    return json.loads((S.EXPORTS / study / "G6_kiem_cheo.json").read_text(encoding="utf-8"))


@CAN_SPSS
def test_that_spss_ty_le_cum_nguong_loc_khop_python(tmp_path, monkeypatch):
    rng = np.random.default_rng(22)
    so_cum, m = 40, 30
    cum = np.repeat(np.arange(so_cum), m)
    lp = np.log(0.6 / 0.4) + rng.normal(0, 0.5, so_cum)[cum]
    dat = rng.binomial(1, 1 / (1 + np.exp(-lp)))
    diem = np.where(dat == 1, rng.integers(4, 6, len(cum)), rng.integers(1, 4, len(cum)))
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(len(cum))], "g1": diem.astype(float),
                       "gioi": rng.integers(1, 3, len(cum)), "cum": cum})
    df.loc[rng.random(len(cum)) < 0.05, "g1"] = np.nan
    td = [["record_id", "text", "Mã", "", "", ""],
          ["g1", "radio", "Hài lòng", "1, 1 | 2, 2 | 3, 3 | 4, 4 | 5, 5", "", ""],
          ["gioi", "radio", "Giới", "1, Nam | 2, Nữ", "", ""], ["cum", "text", "Cụm", "", "integer", ""]]
    _khung_spss(tmp_path, monkeypatch, "TY-CUM-SP", df,
                ["--ty-le", "g1", "--nguong-ty-le", "4", "--cot-cum", "cum", "--loc", "gioi == 2"], td)
    kc = _chay_spss("TY-CUM-SP", monkeypatch)
    assert kc["phan_mem"]["spss"]["trang_thai"] == "KHOP", kc["phan_mem"]["spss"]
    dc = json.loads((S.EXPORTS / "TY-CUM-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    ty = [x for x in dc["dong"] if x["muc"].startswith(("Tỷ lệ", "Hiệu ứng"))]
    assert len(ty) == 3 and all(x["trang_thai"] == "khop" for x in ty), ty
    n_nu = int(((df["gioi"] == 2) & df["g1"].notna()).sum())
    assert all(x["n"] == {"python": n_nu, "spss": n_nu} for x in ty)


@CAN_SPSS
def test_that_spss_ty_le_doc_lap_cot_0_1(tmp_path, monkeypatch):
    rng = np.random.default_rng(9)
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(500)], "kiem_soat_ha": rng.binomial(1, 0.25, 500)})
    td = [["record_id", "text", "Mã", "", "", ""], ["kiem_soat_ha", "yesno", "Kiểm soát huyết áp", "", "", ""]]
    _khung_spss(tmp_path, monkeypatch, "TY-DL-SP", df, ["--ty-le", "kiem_soat_ha"], td)
    kc = _chay_spss("TY-DL-SP", monkeypatch)
    assert kc["phan_mem"]["spss"]["trang_thai"] == "KHOP", kc["phan_mem"]["spss"]
    dc = json.loads((S.EXPORTS / "TY-DL-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    ty = [x for x in dc["dong"] if x["muc"].startswith(("Tỷ lệ", "Hiệu ứng"))]
    assert len(ty) == 1 and ty[0]["trang_thai"] == "khop", ty


@CAN_SPSS
def test_that_spss_thu_tu_cum_quy_doi_khop_python(tmp_path, monkeypatch):
    df = _thu_tu()
    df.insert(0, "record_id", [f"R{i}" for i in range(len(df))])
    td = [["record_id", "text", "Mã", "", "", ""],
          ["g1", "radio", "Mức hài lòng", "1, Rất kém | 2, Kém | 3, Vừa | 4, Tốt | 5, Rất tốt", "", ""],
          ["nhom", "yesno", "Nhóm can thiệp", "", "", ""], ["tuoi", "text", "Tuổi", "", "number", ""],
          ["cum", "text", "Cụm", "", "integer", ""]]
    _khung_spss(tmp_path, monkeypatch, "TT-CUM-SP", df, ["--outcome", "g1", "--group", "nhom", "--covariates", "tuoi",
                                                         "--outcome-type", "ordinal", "--cot-cum", "cum"], td)
    _chay_spss("TT-CUM-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "TT-CUM-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    tt = [x for x in dc["dong"] if x["muc"].startswith("Hồi quy thứ tự")]
    assert len(tt) == 2 and all(x["trang_thai"] == "khop" and S.GHI_CHU_THU_TU_CUM in x["ghi_chu"] for x in tt), tt


@CAN_SPSS
def test_that_spss_cum_dong_deu_de_chan_duoi_1(tmp_path, monkeypatch):
    """Mỗi cụm đúng 3/10 sự kiện ⇒ phương sai thiết kế ≈ 0 ⇒ DE thô < 1: SPSS phải chặn về 1 như Python."""
    rng = np.random.default_rng(3)
    y = np.concatenate([rng.permutation([1, 1, 1, 0, 0, 0, 0, 0, 0, 0]) for _ in range(30)])
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(300)], "co": y, "cum": np.repeat(np.arange(30), 10)})
    td = [["record_id", "text", "Mã", "", "", ""], ["co", "yesno", "Có", "", "", ""],
          ["cum", "text", "Cụm", "", "integer", ""]]
    _khung_spss(tmp_path, monkeypatch, "TY-DEU-SP", df, ["--ty-le", "co", "--cot-cum", "cum"], td)
    kc = _chay_spss("TY-DEU-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "TY-DEU-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    de = next(x for x in dc["dong"] if x["muc"].startswith("Hiệu ứng thiết kế"))
    assert de["trang_thai"] == "khop" and de["spss"]["uoc_luong"] == 1.0, de
    assert kc["phan_mem"]["spss"]["trang_thai"] == "KHOP", kc["phan_mem"]["spss"]
