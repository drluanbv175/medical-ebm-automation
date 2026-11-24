# -*- coding: utf-8 -*-
"""Hai đường phân tích G6 trước đây để fail-closed (ô ⚪ hệ phải xây tiếp — điều phối giao 23/11/2026).

(1) Bệnh–chứng ghép cặp CÁ THỂ: hồi quy logistic CÓ ĐIỀU KIỆN theo mã bộ ghép (statsmodels ConditionalLogit, hợp lý có
    điều kiện chính xác) — OR hiệu chỉnh + OR thô có điều kiện, KTC Wald; đối chiếu R survival::clogit(method="exact")
    và SPSS COXREG phân tầng theo bộ ghép (thời gian giả 2 − ca). Đặc tả G6 khai `bo_ghep`; `chay_sap_g6 kiem` đòi khi
    SAP §4 khoá họ có điều kiện; G6-AUTO-09 nhận họ `logistic_dk`; ma trận G3 có vai trò `bo_ghep`; script 03 thi hành
    dòng clogit theo đúng cột bộ ghép; G7 chép OR thô có điều kiện; giả lập có kịch bản case_control_ghep_cap.
(2) Firth khi SAP §5 khai Firth cho biến cố hiếm: hợp lý phạt Jeffreys (Firth 1993, doi:10.1093/biomet/80.1.27;
    Heinze & Schemper 2002, PMID 12210625), KTC hợp lý phạt hồ sơ, p tỷ số hợp lý phạt — đối chiếu R logistf(pl=TRUE);
    SPSS không có Firth ⇒ dòng «không đối chiếu được bằng SPSS — đối chiếu bằng R», không chấm khớp giả.
Số tham chiếu R ghi trong tệp này đo 23/11/2026 bằng R survival 3.8-12 / logistf 1.26.1 trên CÙNG dữ liệu sinh tất định.
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
import run_stats_analysis as RSA  # noqa: E402


# ───────────────────────────── dữ liệu tất định + số tham chiếu R ─────────────────────────────
def _df_ghep(so_bo: int = 90, seed: int = 7) -> "pd.DataFrame":
    """90 bộ ghép 1 ca : 2 chứng; phơi nhiễm x cao hơn ở ca; z, a không liên quan."""
    rng = np.random.default_rng(seed)
    dong = []
    for s in range(so_bo):
        for j in range(3):
            ca = 1 if j == 0 else 0
            dong.append({"bo": s + 1, "y": ca, "x": rng.binomial(1, 0.5 if ca else 0.3), "z": rng.binomial(1, 0.4),
                         "a": rng.normal(60, 5)})
    return pd.DataFrame(dong)


# R: clogit(y ~ x + z + a + strata(bo), method = "exact") — coef / SE (đo 23/11/2026)
R_CLOGIT = {"x": (0.984795018013, 0.27961024806), "z": (0.066866874550, 0.28952201518),
            "a": (-0.007134421242, 0.02833463374)}


def _df_hiem(seed: int = 8) -> "pd.DataFrame":
    """200 người, 8 biến cố (2 ở nhóm x = 0, 6 ở nhóm x = 1) — rào EPV chặn logistic thường; Firth ước lượng được."""
    rng = np.random.default_rng(seed)
    n = 200
    x, z, c = rng.binomial(1, 0.5, n), rng.normal(0, 1, n), rng.binomial(1, 0.3, n)
    y = rng.binomial(1, 1 / (1 + np.exp(-(-4 + 1.2 * x + 0.5 * z))))
    return pd.DataFrame({"y": y, "x": x, "z": z, "c": c})


# R: logistf(y ~ x + z + c, pl = TRUE) — exp(coef), exp(KTC hồ sơ), p tỷ số hợp lý phạt (đo 23/11/2026)
R_FIRTH = {"x": (3.27817235297, 0.799715071420, 18.47089597279, 0.10100722453),
           "z": (2.24914166738, 1.133706689090, 4.66683957190, 0.02034019226),
           "c": (0.71041211820, 0.071807106914, 3.54053765070, 0.70418216008)}


# ───────────────────────────── (1) engine: logistic có điều kiện ─────────────────────────────
def test_clogit_trung_r_survival_exact():
    mv = RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")
    assert mv["model"] == "logistic_dk" and mv["convergence"] is True
    assert (mv["n"], mv["so_bo_ghep"], mv["so_bo_thong_tin"], mv["ca_toi_da_moi_bo"]) == (270, 90, 90, 1)
    for r in mv["results"]:
        b, se = R_CLOGIT[r["variable"]]
        assert r["OR_adj"] == round(float(np.exp(b)), 3), r
        assert r["CI_95"] == [round(float(np.exp(b - 1.959963984540054 * se)), 3),
                              round(float(np.exp(b + 1.959963984540054 * se)), 3)], r
    assert [r["variable"] for r in mv["crude"]] == ["x"] and mv["crude"][0]["OR_adj"] == 2.699
    txt = RSA.format_multivariate_text(mv)
    assert "HỒI QUY LOGISTIC CÓ ĐIỀU KIỆN (theo bộ ghép «bo»)" in txt.split("\n")[0]
    assert "OR thô có điều kiện" in txt and "2.677" in txt and "90 bộ ghép" in txt


def test_clogit_bo_khong_thong_tin_dem_vao_n_khong_vao_hop_ly():
    d = _df_ghep()
    them = pd.DataFrame({"bo": [999, 999], "y": [0, 0], "x": [1, 0], "z": [0, 1], "a": [60.0, 61.0]})
    mv = RSA.conditional_logit_model(pd.concat([d, them], ignore_index=True), "y", "x", ["z", "a"], "bo")
    assert (mv["n"], mv["so_bo_ghep"], mv["so_bo_thong_tin"], mv["n_thong_tin"]) == (272, 91, 90, 270)
    assert mv["ca_toi_da_moi_bo"] == 1  # bộ toàn chứng có 0 ca — vẫn là số ca TỐI ĐA
    assert mv["results"][0]["OR_adj"] == round(float(np.exp(R_CLOGIT["x"][0])), 3)  # bộ toàn chứng không đổi ước lượng
    hai_ca = pd.DataFrame({"bo": [998] * 3, "y": [1, 1, 0], "x": [1, 0, 0], "z": [0, 1, 0], "a": [60.0, 61, 62]})
    assert RSA.conditional_logit_model(pd.concat([d, hai_ca], ignore_index=True), "y", "x", ["z", "a"],
                                       "bo")["ca_toi_da_moi_bo"] == 2


def test_clogit_bien_hang_xet_tren_bo_mang_thong_tin():
    """Biến hằng trong mọi bộ MANG THÔNG TIN nhưng khác nhau ở một bộ toàn chứng (bộ đó bị loại khỏi hợp lý) vẫn không
    ước lượng được ⇒ phải báo lỗi có tên biến, không để statsmodels gặp ma trận suy biến."""
    d = _df_ghep().assign(gioi=lambda t: t["bo"] % 2)
    them = pd.DataFrame({"bo": [999, 999], "y": [0, 0], "x": [1, 0], "z": [0, 1], "a": [60.0, 61.0], "gioi": [0, 1]})
    mv = RSA.conditional_logit_model(pd.concat([d, them], ignore_index=True), "y", "x", ["z", "gioi"], "bo")
    assert "gioi" in (mv.get("error") or "") and "HẰNG trong mọi bộ ghép" in mv["error"], mv


def test_clogit_bien_hang_trong_bo_la_loi_co_ten_bien():
    d = _df_ghep().assign(gioi=lambda t: t["bo"] % 2)
    mv = RSA.conditional_logit_model(d, "y", "x", ["z", "gioi"], "bo")
    assert "gioi" in mv["error"] and "HẰNG trong mọi bộ ghép" in mv["error"] and "results" not in mv


def test_clogit_rao_epv_va_cot_bo_ghep_vang():
    mv = RSA.conditional_logit_model(_df_ghep(so_bo=8), "y", "x", ["z", "a"], "bo")
    assert mv.get("rao_epv") is True and "results" not in mv and mv["model"] == "logistic_dk"
    assert "không có trong dữ liệu" in RSA.conditional_logit_model(_df_ghep(), "y", "x", [], "khong_co")["error"]


# ───────────────────────────── (2) engine: Firth ─────────────────────────────
def test_firth_trung_r_logistf_ktc_ho_so_va_p_ty_so_hop_ly_phat():
    f = RSA.firth_logistic_model(_df_hiem(), "y", "x", ["z", "c"])
    assert (f["phuong_phap"], f["n"], f["so_bien_co"], f["so_tham_so"]) == ("firth", 200, 8, 3)
    for r in f["results"]:
        or_, lo, hi, p = R_FIRTH[r["variable"]]
        assert r["OR_adj"] == round(or_, 3) and r["CI_95"] == [round(lo, 3), round(hi, 3)], r
        assert r["p"] == round(p, 4), r


def test_firth_dung_la_toi_uu_hop_ly_phat():
    """β Firth là điểm dừng của ĐIỂM SỐ ĐÃ SỬA (không phải của hợp lý thường) và cực đại ℓ*: lệch nhỏ quanh β ⇒ ℓ*
    giảm."""
    d = _df_hiem()
    X = np.column_stack([np.ones(len(d)), d["x"], d["z"], d["c"]]).astype(float)
    y = d["y"].to_numpy(dtype=float)
    b, l_max, hoi_tu = RSA._firth_toi_uu(X, y)
    assert hoi_tu
    for j in range(4):
        for h in (-1e-3, 1e-3):
            bb = b.copy()
            bb[j] += h
            assert RSA._hop_ly_phat(X, y, bb) < l_max
    p = 1 / (1 + np.exp(-(X @ b)))
    assert np.max(np.abs(X.T @ (y - p))) > 1e-2  # điểm số THƯỜNG khác 0 ⇒ không phải MLE thường


def test_firth_thiet_ke_cum_la_loi_va_bang_4b():
    assert "cụm" in RSA.firth_logistic_model(_df_hiem(), "y", "x", [], cluster_col="k")["error"]
    f = RSA.firth_logistic_model(_df_hiem(), "y", "x", ["z", "c"])
    f["ly_do"] = "EPV"
    txt = RSA.format_bien_co_hiem_text(f)
    assert "OR (Firth)" in txt and "0.8–18.471" in txt and "hợp lý phạt hồ sơ" in txt


def test_ten_phuong_phap_firth_dong_bo_g4_g6():
    assert "firth" in RSA.BIEN_CO_HIEM_G6 and G4Q.BIEN_CO_HIEM["firth"][1] is True
    assert set(RSA.BIEN_CO_HIEM_G6) == {k for k, (_t, co) in G4Q.BIEN_CO_HIEM.items() if co}


# ───────────────────────────── chay_sap_g6: đặc tả ↔ SAP ─────────────────────────────
SAP_DK = ("### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic có điều kiện (conditional logistic regression) "
          "theo bộ ghép (matched set) → OR (95%CI)\n\n### §5 PHÂN TÍCH ĐA BIẾN\n- VIF\n\n### §6 DỮ LIỆU THIẾU\n")
SAP_KDK = SAP_DK.replace("có điều kiện (conditional logistic regression) theo bộ ghép (matched set)",
                         "không điều kiện")


def test_kiem_bo_ghep_sap_hai_chieu():
    ds = [{"id": "MT1", "vai": "chinh", "tham_so": {"outcome": "y", "group": "x"}},
          {"id": "NC", "vai": "nhom_con", "tham_so": {"outcome": "y", "group": "x", "loc": "g == 1"}},
          {"id": "PHU", "vai": "phu", "tham_so": {"outcome": "khac", "group": "x"}}]
    loi = CS6.kiem_bo_ghep_sap(ds, SAP_DK)
    assert [x.split(":")[0] for x in loi] == ["MT1", "NC"], loi  # kết cục khác không bắt buộc
    for pt in ds[:2]:
        pt["tham_so"]["bo_ghep"] = "bo"
    # 23/11/2026 (chiều): khai bo_ghep thì phải khai biến dùng để ghép (mô hình gán đa trị — Seaman & Keogh 2015)
    assert [x.split(":")[0] for x in CS6.kiem_bo_ghep_sap(ds, SAP_DK)] == ["MT1", "NC"]
    for pt in ds[:2]:
        pt["tham_so"]["bien_ghep"] = ["gioi"]
    assert CS6.kiem_bo_ghep_sap(ds, SAP_DK) == []
    loi = CS6.kiem_bo_ghep_sap(ds, SAP_KDK)
    assert len(loi) == 2 and all("không khoá hồi quy" in x for x in loi), loi
    assert CS6.doi_so_run_stats({"tham_so": {"outcome": "y", "group": "x", "bo_ghep": "bo"}})[-2:] == [
        "--bo-ghep", "bo"]


def test_kiem_dac_ta_goi_kiem_bo_ghep(tmp_path):
    sap = tmp_path / "G4_A5_SAP_FINAL_S.md"
    sap.write_text(SAP_DK, encoding="utf-8", newline="\n")
    dt = {"nguon_sap": sap.name, "sha256_sap": CS6.sha256_tep(sap),
          "phan_tich": [{"id": "MT1", "vai": "chinh", "sap_muc": "§4", "mo_ta": "chính",
                         "tham_so": {"outcome": "y", "group": "x"}}]}
    assert any("MT1" in x and "bo_ghep" in x for x in CS6.kiem_dac_ta(tmp_path, dt)["loi"])


SAP_FIRTH = (f"### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Hồi quy logistic → OR\n\n### §5 PHÂN TÍCH ĐA BIẾN\n"
             f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['firth'][0]}\n\n### §6 DỮ LIỆU THIẾU\n")


def test_firth_tu_chay_khong_doi_phan_tich_bo_sung_va_chan_cot_cum(monkeypatch):
    ds = [{"id": "MT1", "vai": "chinh", "tham_so": {"outcome": "y", "group": "g", "bien_co_hiem": "firth"}},
          {"id": "TH", "vai": "phu", "tham_so": {"outcome": "bc", "group": "g", "bien_co_hiem": "firth"}}]
    assert CS6.kiem_bien_co_hiem_sap(ds, SAP_FIRTH) == []
    assert CS6._kiem_gia_tri("bien_co_hiem", "bien_co_hiem", "firth") == []
    ds[1]["tham_so"]["cot_cum"] = "k"
    loi = CS6.kiem_bien_co_hiem_sap(ds, SAP_FIRTH)
    assert len(loi) == 1 and loi[0].startswith("TH") and "cụm" in loi[0], loi
    # phương pháp engine CHƯA tự chạy (cờ False) vẫn đòi phân tích bổ sung cùng mã — nhánh dành cho phương pháp mới
    monkeypatch.setitem(G4Q.BIEN_CO_HIEM, "firth", (G4Q.BIEN_CO_HIEM["firth"][0], False))
    assert "loai_bo_sung" in CS6.kiem_bien_co_hiem_sap(ds[:1], SAP_FIRTH)[0]
    ds.append({"id": "BS", "vai": "phu", "tham_so": {"loai_bo_sung": "firth", "cau_hinh": {}}})
    assert CS6.kiem_bien_co_hiem_sap(ds, SAP_FIRTH) == []


# ───────────────────────────── G6-AUTO-09 (lượt chạy) ─────────────────────────────
def test_g6_auto09_nhan_ho_logistic_dk():
    tom = {"primary_outcome": {"outcome_type": "binary", "or_crude": 2.0},
           "multivariate": RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")}
    dat, ct = G6Q.doi_chieu_phuong_phap_da_chay(G6Q._sec(SAP_DK, 4), tom)
    assert dat is True and "logistic_dk" in ct, ct
    tom["multivariate"] = {"model": "logistic", "results": [{"variable": "x"}]}
    dat, ct = G6Q.doi_chieu_phuong_phap_da_chay(G6Q._sec(SAP_DK, 4), tom)
    assert dat is False and "bo_ghep" in ct, ct
    tom["multivariate"] = RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")
    assert G6Q.doi_chieu_phuong_phap_da_chay(G6Q._sec(SAP_KDK, 4), tom)[0] is False


def test_g6_auto09_rao_epv_firth():
    tom = {"primary_outcome": {"outcome_type": "binary", "or_crude": 1.0},
           "multivariate": {"warning": "… EPV …", "rao_epv": True, "thay_the_theo_sap": "bien_co_hiem"},
           "bien_co_hiem": RSA.firth_logistic_model(_df_hiem(), "y", "x", ["z", "c"])}
    s4, s5 = G6Q._sec(SAP_FIRTH, 4), G6Q._sec(SAP_FIRTH, 5)
    assert G6Q.doi_chieu_phuong_phap_da_chay(s4, tom, sap5=s5)[0] is True
    tom["bien_co_hiem"] = RSA.mo_ta_bien_co_hiem(_df_hiem(), "y", "x")
    assert G6Q.doi_chieu_phuong_phap_da_chay(s4, tom, sap5=s5)[0] is False


# ───────────────────────────── cầu nối R / SPSS (đối chiếu) ─────────────────────────────
def _he_so_r(bang: dict) -> dict:
    return {v: {"uoc_luong": t[0], "ci": [t[1], t[2]], "p": t[3]} for v, t in bang.items()}


def test_doi_chieu_r_firth_va_clogit_tho():
    f = RSA.firth_logistic_model(_df_hiem(), "y", "x", ["z", "c"])
    kq = {"firth": {"n": 200, "he_so": _he_so_r(R_FIRTH)}}
    d = R._firth_r({"bien_co_hiem": f}, kq, {})
    assert len(d) == 3 and all(x["trang_thai"] == "khop" for x in d), d
    lech = json.loads(json.dumps(kq))
    lech["firth"]["he_so"]["c"]["ci"][0] = 0.08
    assert next(x for x in R._firth_r({"bien_co_hiem": f}, lech, {}) if "— c" in x["muc"])["trang_thai"] == "lech"
    assert "R KHÔNG ra" in R._firth_r({"bien_co_hiem": f}, {}, {"firth": "lỗi"})[0]["ghi_chu"]
    assert R._bien_co_hiem_r({"bien_co_hiem": f}, {}) == []  # Firth không đi đường mô tả chính xác
    mv = RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")
    tho = {"x": (2.699, mv["crude"][0]["CI_95"][0], mv["crude"][0]["CI_95"][1], mv["crude"][0]["p"])}
    ket = {"da_bien": {"n": 270, "he_so": _he_so_r({r["variable"]: (r["OR_adj"], *r["CI_95"], r["p"])
                                                    for r in mv["results"]})},
           "da_bien_tho": {"n": 270, "he_so": _he_so_r(tho)}}
    dong = R.doi_chieu({"multivariate": mv, "dac_ta_phan_tich": {}}, {"ket_qua": ket, "loi": {}})
    tho_d = [x for x in dong if "OR thô (chỉ phơi nhiễm)" in x["muc"]]
    assert len(tho_d) == 1 and tho_d[0]["trang_thai"] == "khop", tho_d
    assert len([x for x in dong if x["muc"].startswith("Đa biến (logistic_dk")]) == 3
    assert "bo_ghep" in R._dac_ta_lech({"bo_ghep": "bo"}, {})[0]


def test_khuon_r_co_clogit_va_logistf():
    assert "clogit(" in R.MAU_R and 'method = "exact"' in R.MAU_R and "strata(.bo)" in R.MAU_R
    assert "logistf::logistf(" in R.MAU_R and "pl = TRUE" in R.MAU_R and "logistf" in R.GOI_CAN


def test_cu_phap_spss_clogit():
    man = {"bien": [{"ten": "y"}, {"ten": "x"}, {"ten": "z"}, {"ten": "bo"}]}
    so = {"y": True, "x": True, "z": True, "bo": True}
    (dk, tho), cb = S.cu_phap_clogit("y", "bo", ["x", "z"], ["z"], {"muc": ["0", "1"]}, so, man)
    assert dk[0] == "COMPUTE ebm_tg = 2 - (y = 1)." and "/STATUS=y(1) /STRATA=bo" in dk[1]
    assert "/METHOD=ENTER x z" in dk[1] and "/PRINT=CI(95)" in dk[1]
    assert tho[1:3] == ["TEMPORARY.", "SELECT IF (NOT MISSING(z))."] and "/METHOD=ENTER x\n" in tho[3]
    assert "Breslow" in cb[0]
    with pytest.raises(S.TuChoi):
        S.cu_phap_clogit("y", "bo", ["x", "nhom_chu"], [], {"muc": ["0", "1"]}, {**so, "nhom_chu": False}, man)
    with pytest.raises(S.TuChoi):
        S.cu_phap_clogit("y", "bo", ["x"], [], {"muc": ["0", "1"]}, so, {"bien": [*man["bien"], {"ten": "EBM_TG"}]})


def test_doi_chieu_spss_clogit_va_firth():
    mv = RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")
    sp = {r["variable"]: {"uoc_luong": float(np.exp(R_CLOGIT[r["variable"]][0])), "ci": r["CI_95"], "p": r["p"]}
          for r in mv["results"]}
    kq = {"da_bien": {"he_so": sp},
          "da_bien_tho": {"he_so": {"x": {"uoc_luong": 2.699, "ci": mv["crude"][0]["CI_95"],
                                          "p": mv["crude"][0]["p"]}}}}
    tom = {"multivariate": mv, "primary_outcome": {}}
    dong = S.doi_chieu(tom, kq)
    dk = [x for x in dong if "logistic_dk" in x["muc"] or "OR thô" in x["muc"]]
    assert len(dk) == 4 and all(x["trang_thai"] == "khop" for x in dk), dk
    tom["multivariate"] = {**mv, "ca_toi_da_moi_bo": 2}
    assert all("Breslow" in x["ghi_chu"] for x in S.doi_chieu(tom, kq) if "logistic_dk" in x["muc"])
    f = RSA.firth_logistic_model(_df_hiem(), "y", "x", ["z", "c"])
    fd = S.doi_chieu({"bien_co_hiem": f, "primary_outcome": {}}, {})
    fd = [x for x in fd if "Firth" in x["muc"]]
    assert len(fd) == 3 and all(x["trang_thai"] == "khong_so_duoc" and x["ghi_chu"] == S.KHONG_SO_FIRTH_SPSS
                                for x in fd), fd


# ───────────────────────────── G7 · ma trận · script 03 · giả lập ─────────────────────────────
def test_g7_ho_mo_hinh_va_bang_clogit_firth():
    import run_g7_auto as G7A

    assert G7A._ho_mo_hinh_khop_sap("logistic_dk", "Hồi quy logistic có điều kiện theo bộ ghép")
    assert not G7A._ho_mo_hinh_khop_sap("logistic_dk", "Hồi quy logistic không điều kiện")
    assert G7A._ho_mo_hinh_khop_sap("logistic", "Hồi quy logistic không điều kiện")
    mv = RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")
    dong = "\n".join(G7A._bang_mo_hinh_g6("Mô hình đa biến (G6)", mv))
    assert "OR thô có điều kiện" in dong and "| `x` | 2.699 |" in dong, dong
    f = RSA.firth_logistic_model(_df_hiem(), "y", "x", ["z", "c"])
    bf = "\n".join(G7A._bang_bien_co_hiem_g6(f, "G6_TH"))
    assert "| `x` | 3.278 | 0.8–18.471 |" in bf and "OR (Firth)" in bf, bf
    tom = json.dumps({"multivariate": mv, "bien_co_hiem": f}, ensure_ascii=False)
    assert G7A.kiem_so_trich_g6(dong + "\n" + bf, tom) == []
    f2 = {**f, "results": [{**f["results"][0], "CI_95": [0.8, None]}]}
    assert "[CẦN THỐNG KÊ VIÊN — G6 không tìm được cận KTC hồ sơ]" in "\n".join(G7A._bang_bien_co_hiem_g6(f2, "G6"))
    po = {"outcome_type": "binary", "groups": ["0", "1"], "or_crude": 2.5, "ci_95": [1.5, 4.0],
          "ghep_ca_the": RSA.GHI_CHU_OR_THO_GHEP_CA_THE}
    kc = "\n".join(G7A._khoi_ket_cuc_chinh_g6(po))
    assert "Ghép cặp cá thể (G6)" in kc and G7A.kiem_so_trich_g6(kc, json.dumps(po, ensure_ascii=False)) == []


def test_ma_tran_vai_tro_bo_ghep_va_script_03():
    import ma_tran_muc_tieu_bien as MT
    import run_g6_auto as G6A

    assert "bo_ghep" in MT.VAI_TRO
    assert MT.vai_tro_tu_dong([{"vai_tro": "bo_ghep", "bien": "ma_bo_ghep"}])["bo_ghep"] == "ma_bo_ghep"
    v = {"exposure": "nsaid", "outcome": "ca", "covariates": ["chong_dong"], "logistic_dk": True,
         "bo_ghep_col": "ma_bo_ghep"}
    code = G6A.bat_dong_thi_hanh(G6A._r03_case_control_with_vars(v))
    thi_hanh = [d for d in code.split("\n") if d.strip() and not d.lstrip().startswith("#")]
    assert any("clogit(ca ~ nsaid + chong_dong + strata(ma_bo_ghep)" in d for d in thi_hanh), thi_hanh
    assert not any("glm(" in d for d in thi_hanh)
    code2 = G6A.bat_dong_thi_hanh(G6A._r03_case_control_with_vars({**v, "bo_ghep_col": None}))
    assert not any("clogit(" in d for d in code2.split("\n") if not d.lstrip().startswith("#"))
    assert "[CẦN MA TRẬN KHAI VAI TRÒ bo_ghep]" in code2
    code3 = G6A.bat_dong_thi_hanh(G6A._r03_case_control_with_vars({**v, "logistic_dk": False}))
    assert any("glm(ca ~ nsaid" in d for d in code3.split("\n") if not d.lstrip().startswith("#"))


def test_gia_lap_ghep_cap_sinh_bo_ghep_that():
    import gia_lap_bien_the_kho as BTK
    import gia_lap_tron_vong as GTV

    kb = BTK.kich_ban_kho()["benh_chung_ghep_cap"]
    assert ("benh_chung_ghep_cap", "case_control_ghep_cap") in BTK.danh_sach()
    assert kb["pi"]["G1"]["matching_type"] == "individual"
    rows = GTV.sinh_du_lieu("case_control", kb["bien_so"], kb["pi"]["G3"], 300, bien_the=kb["bien_the"])
    d = pd.DataFrame(rows)
    nhom = d.groupby("ma_bo_ghep")
    assert (nhom["nhom_ca"].sum() == 1).all() and (nhom.size() == 3).all()
    assert (nhom["gioi"].nunique() == 1).all() and ((nhom["tuoi"].max() - nhom["tuoi"].min()) <= 4).all()
    vai = {d[3]: d[2] for d in kb["bien_so"]["ma_tran"]}
    assert vai["ma_bo_ghep"] == "bo_ghep" and vai["gioi"] == vai["tuoi"] == "bien_ghep"  # 23/11 chiều: vai biến ghép
    for pt in kb["ho_so_tron_vong"]["g6"]:
        assert not {"tuoi", "gioi"} & set((pt.get("tham_so") or {}).get("covariates") or [])
    # kịch bản gốc (ghép tần suất) KHÔNG đổi
    import gia_lap_dinh_ky as GL

    assert GL.KICH_BAN["benh_chung"]["pi"]["G1"]["matching_type"] == "frequency"
    assert "ma_bo_ghep" not in {b[0] for b in GL.KICH_BAN["benh_chung"]["bien_so"]["bo_bien"]}


def test_gia_lap_firth_o_rct_goc_va_cum_giu_mo_ta():
    import gia_lap_bien_the_kho as BTK
    import gia_lap_dinh_ky as GL

    tl = GL.KICH_BAN["rct_nhi_phan"]["ho_so_tron_vong"]["tra_loi_G4"]
    assert tl[0][0] == r"bien co hiem" and G4Q.phuong_phap_bien_co_hiem_sap(
        f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {tl[0][1]}")["phuong_phap"] == "firth"
    cum = BTK.kich_ban_kho()["rct_cum"]["ho_so_tron_vong"]["tra_loi_G4"]
    bch = [x for x in cum if x[0] == r"bien co hiem"]
    assert len(bch) == 1 and G4Q.phuong_phap_bien_co_hiem_sap(
        f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {bch[0][1]}")["phuong_phap"] == "mo_ta_chinh_xac"


# ───────────────────────────── chạy THẬT: engine → R / SPSS ─────────────────────────────
def _df_ghep_that() -> "pd.DataFrame":
    d = _df_ghep()
    return d.assign(record_id=[f"R{i}" for i in range(len(d))])[["record_id", "y", "x", "z", "a", "bo"]]


def _df_hiem_that() -> "pd.DataFrame":
    d = _df_hiem()
    return d.assign(record_id=[f"R{i}" for i in range(len(d))])[["record_id", "y", "x", "z", "c"]]


TS_DK = ["--outcome", "y", "--group", "x", "--covariates", "z,a", "--outcome-type", "binary", "--bo-ghep", "bo"]
TS_FIRTH = ["--outcome", "y", "--group", "x", "--covariates", "z,c", "--outcome-type", "binary", "--bien-co-hiem",
            "firth"]


def _can_r() -> None:
    try:
        if R.kiem_moi_truong(R.tim_r())["thieu"]:
            pytest.skip("thiếu gói R của cầu nối")
    except Exception:  # noqa: BLE001
        pytest.skip("không kiểm được môi trường R")


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_clogit_engine_khop_r(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi, _khung

    _can_r()
    d = _khung(tmp_path, monkeypatch, "DK-R", _df_ghep_that(), TS_DK)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["multivariate"]["model"] == "logistic_dk" and tom["dac_ta_phan_tich"]["bo_ghep"] == "bo"
    assert tom["primary_outcome"]["ghep_ca_the"] == RSA.GHI_CHU_OR_THO_GHEP_CA_THE
    dc = _chay_cau_noi("DK-R")
    dk = [x for x in dc["dong"] if "logistic_dk" in x["muc"] or "OR thô (chỉ phơi nhiễm)" in x["muc"]]
    assert len(dk) == 4 and all(x["trang_thai"] == "khop" for x in dk), dk
    assert dc["dem"]["lech"] == 0, dc["dem"]


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_firth_engine_khop_r_logistf(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi, _khung

    _can_r()
    d = _khung(tmp_path, monkeypatch, "FI-R", _df_hiem_that(), TS_FIRTH)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["multivariate"]["rao_epv"] and tom["bien_co_hiem"]["phuong_phap"] == "firth"
    assert (d / "G6_table4b_bien_co_hiem.txt").is_file()
    dc = _chay_cau_noi("FI-R")
    fi = [x for x in dc["dong"] if "Firth" in x["muc"]]
    assert len(fi) == 3 and all(x["trang_thai"] == "khop" for x in fi), fi


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_bo_ghep_co_du_lieu_thieu_khong_gan_da_tri_sai_ho(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _khung

    df = _df_ghep_that()
    df.loc[df.index % 17 == 5, "z"] = np.nan
    d = _khung(tmp_path, monkeypatch, "DK-MI", df, TS_DK)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    # 23/11/2026 (chiều): gán đa trị ghép cặp đã có đường — thiếu biến ghép thì báo lỗi, không gán thiếu cấu trúc ghép
    assert tom["multiple_imputation"]["error"] == RSA.LOI_MI_THIEU_BIEN_GHEP
    assert tom["multivariate"]["model"] == "logistic_dk" and tom["multivariate"]["n"] < 270


CO_SPSS = any(p.is_file() for p in S.ung_vien_python_spss())


@pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")
def test_that_clogit_engine_khop_spss_coxreg(tmp_path, monkeypatch):
    from tests.test_cau_noi_spss_ty_le_20261123 import _chay_spss, _khung_spss

    td = [["record_id", "text", "Mã", "", "", ""], ["y", "yesno", "Ca", "", "", ""],
          ["x", "yesno", "Phơi nhiễm", "", "", ""], ["z", "yesno", "Hiệp biến", "", "", ""],
          ["a", "text", "Tuổi", "", "number", ""], ["bo", "text", "Mã bộ ghép", "", "integer", ""]]
    _khung_spss(tmp_path, monkeypatch, "DK-SP", _df_ghep_that(), TS_DK, td)
    _chay_spss("DK-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "DK-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    dk = [x for x in dc["dong"] if "logistic_dk" in x["muc"] or "OR thô (chỉ phơi nhiễm)" in x["muc"]]
    assert len(dk) == 4 and all(x["trang_thai"] == "khop" for x in dk), dk


@pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")
def test_that_firth_spss_ghi_khong_doi_chieu_duoc(tmp_path, monkeypatch):
    from tests.test_cau_noi_spss_ty_le_20261123 import _chay_spss, _khung_spss

    td = [["record_id", "text", "Mã", "", "", ""], ["y", "yesno", "Biến cố", "", "", ""],
          ["x", "yesno", "Nhóm", "", "", ""], ["z", "text", "z", "", "number", ""], ["c", "yesno", "c", "", "", ""]]
    _khung_spss(tmp_path, monkeypatch, "FI-SP", _df_hiem_that(), TS_FIRTH, td)
    _chay_spss("FI-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "FI-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    fi = [x for x in dc["dong"] if "Firth" in x["muc"]]
    assert len(fi) == 3 and all(x["trang_thai"] == "khong_so_duoc" for x in fi), fi
    assert all(x["ghi_chu"] == S.KHONG_SO_FIRTH_SPSS for x in fi)


def test_g6_lay_cot_bo_ghep_tu_ma_tran(tmp_path, monkeypatch):
    import ma_tran_muc_tieu_bien as MT
    import run_g6_auto as G6A

    vt = MT.vai_tro_tu_dong([{"vai_tro": "ket_cuc_chinh", "bien": "y", "kieu": "nhi_phan"},
                             {"vai_tro": "phoi_nhiem", "bien": "x"}, {"vai_tro": "bo_ghep", "bien": "bo"}])
    monkeypatch.setattr(MT, "vai_tro_bien", lambda *_a, **_k: vt)
    v = {"exposure": "x", "outcome": "y", "covariates": [], "detection_log": []}
    assert G6A.ap_vai_tro_ma_tran(v, tmp_path, "S", {"x": "x", "y": "y", "bo": "bo"}, "case_control") is None
    assert v["bo_ghep_col"] == "bo"


def _tron_vong_tam(tmp_path: Path, thiet_ke: str = "case_control"):
    from datetime import date

    import gia_lap_tron_vong as GTV

    tv = object.__new__(GTV.TronVong)
    tv.out, tv.study, tv.thiet_ke, tv.hom_nay = tmp_path, "S", thiet_ke, date(2026, 11, 23)
    return tv


def test_thong_ke_vien_gia_lap_khai_bo_ghep_theo_sap_va_ma_tran(tmp_path):
    import csv as _csv

    (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(SAP_DK, encoding="utf-8", newline="\n")
    with open(tmp_path / "_ma-tran-muc-tieu-bien.csv", "w", encoding="utf-8", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["muc_tieu", "khai_niem", "vai_tro", "bien", "kieu"])
        w.writerows([["1", "ca", "ket_cuc_chinh", "y", "nhi_phan"], ["1", "pn", "phoi_nhiem", "x", "nhi_phan"],
                     ["1", "bộ ghép", "bo_ghep", "bo", "lien_tuc"]])
    tv = _tron_vong_tam(tmp_path)
    tv.kb = {"ho_so_tron_vong": {"g6": [
        {"id": "MT1", "vai": "chinh", "sap_muc": "§4", "sap_neo": "<§4>", "mo_ta": "chính",
         "tham_so": {"outcome": "y", "group": "x"}},
        {"id": "NC", "vai": "nhom_con", "sap_muc": "§7", "sap_neo": "Giới", "mo_ta": "nhóm con", "ke_thua": True,
         "tham_so": {"loc": "g == 1"}}]}}
    dt = tv._dac_ta_g6()
    ts = {pt["id"]: pt.get("tham_so") or {} for pt in dt["phan_tich"]}
    assert ts["MT1"]["bo_ghep"] == "bo" and ts["NC"]["bo_ghep"] == "bo", ts
    (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(SAP_KDK, encoding="utf-8", newline="\n")
    assert "bo_ghep" not in {k for pt in tv._dac_ta_g6()["phan_tich"] for k in (pt.get("tham_so") or {})}


def test_dien_giai_gia_lap_chep_or_tho_co_dieu_kien(tmp_path):
    mv = RSA.conditional_logit_model(_df_ghep(), "y", "x", ["z", "a"], "bo")
    (tmp_path / "G6_analysis_summary.json").write_text(json.dumps(
        {"multivariate": mv, "dac_ta_phan_tich": {"group": "x"}, "primary_outcome": {"or_crude": 9.9,
                                                                                  "ci_95": [1, 2]}}),
        encoding="utf-8", newline="\n")
    r = _tron_vong_tam(tmp_path)._uoc_luong("or_tho_dk", "G6")
    assert r["uoc"] == 2.699 and r["ci"] == mv["crude"][0]["CI_95"] and r["nguon"] == "G6_table4_multivariate.txt"
