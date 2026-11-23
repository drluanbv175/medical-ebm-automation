# -*- coding: utf-8 -*-
"""Hai lỗi G6 do agent G7 phát hiện ngày 23/11/2026, sửa tại khâu sai đầu tiên.

(3) `n_imputations = 0` (độ nhạy «ca đầy đủ» của SAP §9, vd DN_ca_day_du của cohort_mi): engine vẫn gọi MICE.fit với
    m = 0 và ghi lỗi nội bộ statsmodels «cannot access local variable 'result'». Nay m = 0 nghĩa là phân tích ca đầy
    đủ: không gán đa trị, không lỗi; ước lượng là mô hình ca đầy đủ ở Bảng 4.
(4) rct_cum, tổn hại G6_TH_nghiem_trong: chỉ 2 biến cố ⇒ rào EPV từ chối logistic ⇒ bảng đa biến bản thảo để trống
    («chưa có thông tin»). Sửa theo thứ tự khâu: khuôn SAP G4 khai TRƯỚC phương pháp biến cố hiếm (G4-AUTO-04 đòi, SAP
    chưa ký mà thiếu ⇒ chưa khoá); đặc tả G6 mang phương pháp (chay_sap_g6 `kiem`); engine chạy đúng phương pháp khi
    rào EPV chặn (số biến cố từng nhóm + KTC chính xác Clopper–Pearson + p chính xác Fisher), ghi vào tóm tắt; cầu nối
    R (binom.test/fisher.test) và SPSS (PROPORTIONS Clopper–Pearson theo nhóm + Fisher của CROSSTABS) tính lại cùng
    phương pháp; G6-AUTO-09 (phần lượt chạy) chặn khi SAP khai mà lượt chạy thiếu; G7 chép bảng thay vì để trống.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("statsmodels")

import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import chay_sap_g6 as CS6  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402


# ───────────────────────────── (3) n_imputations = 0 ⇒ ca đầy đủ ─────────────────────────────
def _df_thieu(seed: int = 3) -> "pd.DataFrame":
    rng = np.random.default_rng(seed)
    n = 300
    x = rng.integers(0, 2, n)
    tuoi = rng.normal(60, 8, n)
    y = rng.binomial(1, 1 / (1 + np.exp(-(-1 + 0.8 * x + 0.02 * (tuoi - 60)))))
    df = pd.DataFrame({"y": y, "x": x, "tuoi": tuoi})
    df.loc[rng.random(n) < 0.15, "tuoi"] = np.nan
    return df


@pytest.mark.parametrize("loai", ["binary", "poisson_pr"])
def test_mi_bang_0_la_ca_day_du_khong_loi(loai):
    df = _df_thieu()
    mi = RSA.multiple_imputation_model(df, "y", "x", ["tuoi"], loai, n_imputations=0)
    assert mi.get("skipped") and mi.get("ca_day_du") and "error" not in mi, mi
    assert mi["n_imputations"] == 0 and mi["n_complete_case"] == int(df.notna().all(axis=1).sum())
    assert "ca đầy đủ" in mi["reason"].lower()


def test_mi_am_la_loi_va_mi_duong_van_gan_da_tri():
    df = _df_thieu()
    am = RSA.multiple_imputation_model(df, "y", "x", ["tuoi"], "binary", n_imputations=-1)
    assert "phải ≥ 0" in am.get("error", ""), am  # lỗi RÕ của đặc tả, không phải lỗi nội bộ statsmodels
    mi = RSA.multiple_imputation_model(df, "y", "x", ["tuoi"], "binary", n_imputations=3)
    assert mi.get("results") and mi["n_imputations"] == 3, mi  # m > 0 không đổi hành vi


def test_r_khong_dung_khoi_mi_khi_m_bang_0():
    mi = RSA.multiple_imputation_model(_df_thieu(), "y", "x", ["tuoi"], "binary", n_imputations=0)
    assert "MI_CO <- FALSE" in R.khoi_mi_r({"multiple_imputation": mi}, Path("."), Path("x.csv"))


# ───────────────────────────── (4) biến cố hiếm ─────────────────────────────
def _df_hiem() -> "pd.DataFrame":
    return pd.DataFrame({"y": [1] + [0] * 159 + [1] + [0] * 159, "nhom": [0] * 160 + [1] * 160})


def test_rao_epv_danh_dau_va_mo_ta_chinh_xac_trung_spss_r():
    mv = RSA.multivariate_model(_df_hiem(), "y", "nhom", [], "binary")
    assert mv.get("rao_epv") and mv["so_bien_co"] == 2 and "results" not in mv
    b = RSA.mo_ta_bien_co_hiem(_df_hiem(), "y", "nhom")
    # SPSS 31 PROPORTIONS Clopper–Pearson và R binom.test: 1/160 ⇒ 0,000158224 – 0,034329330 (đo 23/11/2026)
    lo, hi = RSA.ktc_clopper_pearson(1, 160)
    assert lo == pytest.approx(0.000158223781, abs=1e-9) and hi == pytest.approx(0.034329329684, abs=1e-9)
    assert [g["ci_95_clopper_pearson"] for g in b["nhom"]] == [[0.0002, 0.0343]] * 2
    assert b["fisher_p_hai_phia"] == 1.0 and b["phuong_phap"] == "mo_ta_chinh_xac"
    assert RSA.ktc_clopper_pearson(0, 10)[0] == 0.0 and RSA.ktc_clopper_pearson(10, 10)[1] == 1.0
    assert RSA.mo_ta_bien_co_hiem(_df_hiem().assign(y=2), "y", "nhom").get("error")


def test_khuon_sap_g4_khai_bien_co_hiem_theo_thiet_ke():
    def sap(tk, et="OR", **kw):
        return G4.generate("S", "Chủ đề", tk, tk, "STROBE", 300, 0.05, 0.8, 1.5, et, "2026-11-23", **kw)

    for tk in ("rct", "cohort"):
        assert G4Q.NHAN_BIEN_CO_HIEM in G4Q._section_body(sap(tk), "§5"), tk
    assert G4Q.NHAN_BIEN_CO_HIEM in G4Q._section_body(sap("case_control", khung={"kieu_ghep": "tan_suat"}), "§5")
    mo_ta = sap("cross_sectional", et=None, hypothesis_type="descriptive", g3={"precision": 0.05})
    assert G4Q.NHAN_BIEN_CO_HIEM not in mo_ta  # cắt ngang MÔ TẢ: không hồi quy ⇒ không áp dụng
    assert G4Q.NHAN_BIEN_CO_HIEM not in sap("diagnostic", et=None)


@pytest.mark.parametrize("dong, pp", [
    (f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** mô tả số biến cố từng nhóm + KTC chính xác Clopper–Pearson + p chính xác Fisher",
     "mo_ta_chinh_xac"),
    (f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** hồi quy logistic Firth (logistf)", "firth"),
    (f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** [CẦN THỐNG KÊ VIÊN CHỌN — x]", None),
    (f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** Đã xác định trong đề cương (tổng hợp)", None),
    ("- **Giả định:** VIF < 5", None),
])
def test_doc_phuong_phap_bien_co_hiem(dong, pp):
    assert G4Q.phuong_phap_bien_co_hiem_sap(dong)["phuong_phap"] == pp


def _g4_auto04(tmp_path, monkeypatch, dong5: str, ky: bool) -> dict:
    """Chạy G4-AUTO-04 qua evaluate_g4_quality với SAP §5 tối thiểu (thiết kế thuần tập)."""
    text = ("### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic → OR\n\n### §5 PHÂN TÍCH ĐA BIẾN\n"
            f"- EPV ≈ 20; VIF < 5\n{dong5}\n\n### §6 DỮ LIỆU THIẾU\n")
    bao = G4Q.evaluate_g4_quality(study="S", checkpoint={"design_code": "cohort"}, artifact_text=text,
                                  g3_checkpoint={"design_code": "cohort"}, g1_checkpoint={}, meta={}, ledger_signed=ky,
                                  ledger_reason="", signature_scope=None, role_key_available=False, cross_gate_refs={})
    return next(c for c in bao["automatic_criteria"] if c["id"] == "G4-AUTO-04")


def test_g4_auto04_doi_khai_bien_co_hiem_truoc_khi_ky(tmp_path, monkeypatch):
    du = f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['mo_ta_chinh_xac'][0]}"
    assert _g4_auto04(tmp_path, monkeypatch, du, ky=False)["status"] == "PASS"
    thieu = _g4_auto04(tmp_path, monkeypatch, "", ky=False)
    assert thieu["status"] == "REVIEW" and "biến cố hiếm" in thieu["evidence"], thieu
    o_trong = _g4_auto04(tmp_path, monkeypatch, f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** [CẦN THỐNG KÊ VIÊN CHỌN]", ky=False)
    assert o_trong["status"] == "REVIEW" and "ô trống" in o_trong["evidence"]
    # SAP đã ký trước luật này: chỉ hiển thị, không hạ cấp quyết định đã ký
    da_ky = _g4_auto04(tmp_path, monkeypatch, "", ky=True)
    assert da_ky["status"] == "PASS" and "chỉ hiển thị" in da_ky["evidence"], da_ky


SAP_BCH = (f"### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic → OR\n\n### §5 PHÂN TÍCH ĐA BIẾN\n"
           f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['mo_ta_chinh_xac'][0]}\n\n### §6 DỮ LIỆU THIẾU\n")


def test_chay_sap_g6_doi_moi_phan_tich_mang_phuong_phap_sap():
    ds = [{"id": "MT1", "vai": "chinh", "tham_so": {"outcome": "y", "group": "g", "bien_co_hiem": "mo_ta_chinh_xac"}},
          {"id": "TH", "vai": "phu", "tham_so": {"outcome": "bc", "group": "g"}},
          {"id": "BS", "vai": "phu", "tham_so": {"loai_bo_sung": "firth", "cau_hinh": {}}}]
    loi = CS6.kiem_bien_co_hiem_sap(ds, SAP_BCH)
    assert len(loi) == 1 and loi[0].startswith("TH"), loi
    ds[1]["tham_so"]["bien_co_hiem"] = "mo_ta_chinh_xac"
    assert CS6.kiem_bien_co_hiem_sap(ds, SAP_BCH) == []
    firth = SAP_BCH.replace(G4Q.BIEN_CO_HIEM["mo_ta_chinh_xac"][0], "hồi quy logistic Firth (logistf)")
    assert CS6.kiem_bien_co_hiem_sap(ds[:2], firth) and CS6.kiem_bien_co_hiem_sap(ds, firth) == []
    assert CS6.kiem_bien_co_hiem_sap(ds[:2], "### §5\n- VIF\n") == []  # SAP cũ không có dòng ⇒ không đòi


def test_kiem_dac_ta_goi_kiem_bien_co_hiem(tmp_path):
    """Nối dây: `chay_sap_g6 kiem` (kiem_dac_ta) thật sự chạy kiểm biến cố hiếm trên SAP của đề tài."""
    sap = tmp_path / "G4_A5_SAP_FINAL_S.md"
    sap.write_text(SAP_BCH, encoding="utf-8", newline="\n")
    dt = {"nguon_sap": sap.name, "sha256_sap": CS6.sha256_tep(sap),
          "phan_tich": [{"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "chính",
                         "tham_so": {"outcome": "y", "group": "g"}}]}
    loi = CS6.kiem_dac_ta(tmp_path, dt)["loi"]
    assert any("MT1" in x and "biến cố hiếm" in x for x in loi), loi
    assert CS6._kiem_gia_tri("bien_co_hiem", "bien_co_hiem", "firth")  # engine không tự chạy Firth
    assert CS6.doi_so_run_stats({"tham_so": {"outcome": "y", "group": "g", "bien_co_hiem": "mo_ta_chinh_xac"}})[
        -2:] == ["--bien-co-hiem", "mo_ta_chinh_xac"]


def _tom(bch: bool) -> dict:
    tom = {"primary_outcome": {"outcome_type": "binary", "or_crude": 1.0},
           "multivariate": {"warning": "Số biến cố 2 … EPV …", "rao_epv": True}}
    if bch:
        tom["bien_co_hiem"] = RSA.mo_ta_bien_co_hiem(_df_hiem(), "y", "nhom")
        tom["multivariate"]["thay_the_theo_sap"] = "bien_co_hiem"
    return tom


def test_g6_auto09_luot_chay_doi_phuong_phap_bien_co_hiem():
    sap4, sap5 = G6Q._sec(SAP_BCH, 4), G6Q._sec(SAP_BCH, 5)
    dat, ct = G6Q.doi_chieu_phuong_phap_da_chay(sap4, _tom(False), sap5=sap5)
    assert dat is False and "biến cố hiếm" in ct, ct
    assert G6Q.doi_chieu_phuong_phap_da_chay(sap4, _tom(True), sap5=sap5)[0] is True


def test_cau_noi_spss_va_r_doi_chieu_bien_co_hiem():
    b = RSA.mo_ta_bien_co_hiem(_df_hiem(), "y", "nhom")
    sp = {"0": {"n": 160, "so_bien_co": 1, "ty_le": 0.00625, "ci": [0.00015822378119879, 0.034329329683959]},
          "1": {"n": 160, "so_bien_co": 1, "ty_le": 0.00625, "ci": [0.00015822378119879, 0.034329329683959]}}
    d = S.doi_chieu_bien_co_hiem(b, sp, 0.99999999999994)  # số SPSS 31 thật (đo 23/11/2026)
    assert len(d) == 3 and all(x["trang_thai"] == "khop" for x in d), d
    sp_lech = json.loads(json.dumps(sp))
    sp_lech["1"]["ci"][1] = 0.0353
    assert S.doi_chieu_bien_co_hiem(b, sp_lech, 1.0)[1]["trang_thai"] == "lech"
    rc = {"n": [160, 160], "bien_co": [1, 1],
          "bien_co_hiem": {"ci0": [0.0001582238, 0.0343293297], "ci1": [0.0001582238, 0.0343293297], "fisher_p": 1}}
    dr = R._bien_co_hiem_r({"bien_co_hiem": b}, rc)
    assert len(dr) == 3 and all(x["trang_thai"] == "khop" for x in dr), dr
    assert "R không ra" in R._bien_co_hiem_r({"bien_co_hiem": b}, {"n": [160, 160]})[0]["ghi_chu"]
    rc_lech = json.loads(json.dumps(rc))
    rc_lech["bien_co_hiem"]["ci1"][1] = 0.0353  # lệch 0,001 > đơn vị làm tròn ⇒ LỆCH (phép tất định)
    assert R._bien_co_hiem_r({"bien_co_hiem": b}, rc_lech)[1]["trang_thai"] == "lech"
    dong = S.cu_phap_bien_co_hiem("y", "nhom")
    assert "SPLIT FILE LAYERED BY nhom." in dong and any("CITYPES=CLOPPER_PEARSON" in x for x in dong)
    assert dong[-1] == "SPLIT FILE OFF."


def test_g7_chep_bang_bien_co_hiem_thay_vi_de_trong():
    import run_g7_auto as G7A

    tom = _tom(True)
    dong = "\n".join(G7A._bang_mo_hinh_g6("Mô hình đa biến (G6)", tom["multivariate"])
                     + G7A._bang_bien_co_hiem_g6(tom["bien_co_hiem"], "G6_TH"))
    # nhãn chuẩn «đối chiếu G6» của mọi bảng chép từ G6 vẫn có; KHÔNG còn ô [CẦN THỐNG KÊ VIÊN — G6 không chạy mô hình]
    assert "[CẦN THỐNG KÊ VIÊN" not in dong and G7A.NHAN_DOI_CHIEU_G6 in dong, dong
    assert "Clopper–Pearson" in dong and "1/160" in dong and "0.0002–0.0343" in dong, dong
    assert "Fisher" in dong
    # bộ tự kiểm số của G7: mọi chữ số trong khối phải có nguyên văn trong tóm tắt G6 (không «§5», không «KTC 95%»)
    assert G7A.kiem_so_trich_g6(dong, json.dumps(tom, ensure_ascii=False)) == []
    assert G7A._bang_mo_hinh_g6("M", _tom(False)["multivariate"])[0].startswith("M: [CẦN THỐNG KÊ VIÊN")
    # nối dây: khối ước lượng G7 dựng từ tóm tắt (đường của kết cục phụ/tổn hại) có bảng biến cố hiếm
    khoi = "\n".join(G7A._khoi_uoc_luong_g6(tom, "G6_TH_analysis_summary.json", tien_to="G6_TH"))
    assert "| `1` | 1/160 | 0.0063 | 0.0002–0.0343 |" in khoi, khoi


# ───────────────────────────── chạy THẬT: engine → R / SPSS cùng phương pháp ─────────────────────────────
THAM_SO = ["--outcome", "y", "--group", "nhom", "--outcome-type", "binary", "--bien-co-hiem", "mo_ta_chinh_xac"]


def _df_that() -> "pd.DataFrame":
    d = _df_hiem()
    return d.assign(record_id=[f"R{i}" for i in range(len(d))])[["record_id", "y", "nhom"]]


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_engine_va_r_cung_phuong_phap(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi, _khung

    try:
        if R.kiem_moi_truong(R.tim_r())["thieu"]:
            pytest.skip("thiếu gói R của cầu nối")
    except Exception:  # noqa: BLE001
        pytest.skip("không kiểm được môi trường R")
    d = _khung(tmp_path, monkeypatch, "BCH-R", _df_that(), THAM_SO)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["bien_co_hiem"]["phuong_phap"] == "mo_ta_chinh_xac" and tom["multivariate"]["thay_the_theo_sap"]
    assert (d / "G6_table4b_bien_co_hiem.txt").is_file()
    dc = _chay_cau_noi("BCH-R")
    bch = [x for x in dc["dong"] if x["muc"].startswith("Biến cố hiếm")]
    assert len(bch) == 3 and all(x["trang_thai"] == "khop" for x in bch), bch


CO_SPSS = any(p.is_file() for p in S.ung_vien_python_spss())


@pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")
def test_that_engine_va_spss_cung_phuong_phap(tmp_path, monkeypatch):
    from tests.test_cau_noi_spss_ty_le_20261123 import _chay_spss, _khung_spss

    td = [["record_id", "text", "Mã", "", "", ""], ["y", "yesno", "Biến cố nghiêm trọng", "", "", ""],
          ["nhom", "yesno", "Nhóm can thiệp", "", "", ""]]
    _khung_spss(tmp_path, monkeypatch, "BCH-SP", _df_that(), THAM_SO, td)
    _chay_spss("BCH-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "BCH-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    bch = [x for x in dc["dong"] if x["muc"].startswith("Biến cố hiếm")]
    assert len(bch) == 3 and all(x["trang_thai"] == "khop" for x in bch), bch
