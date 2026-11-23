# -*- coding: utf-8 -*-
"""G6 phải chạy ĐÚNG phương pháp SAP §4 khai — hai lệch G7 phát hiện ngày 23/11/2026, sửa tại khâu sai đầu tiên.

(1) Bệnh–chứng: G1 ghi «ghép theo giới và nhóm tuổi» (không nói ghép cặp cá thể hay theo tần suất), biện pháp sai lệch
    và SAP §4 ghi «hồi quy logistic có điều kiện», dữ liệu không có mã bộ ghép, G6 chạy logistic không điều kiện. Khâu
    sai đầu tiên là G1: nay kiểu ghép phải CHỐT (khung_de_tai.kieu_ghep_benh_chung, cổng G1-AUTO-04c), khuôn G1/G4 chọn
    họ mô hình theo kiểu ghép, kịch bản giả lập khai ghép THEO TẦN SUẤT (logistic không điều kiện + biến ghép); cổng G6
    tách họ «logistic có điều kiện» (logistic_dk) và G6-AUTO-09 đối chiếu SAP §4 với cả lượt chạy THẬT.
(2) Thử nghiệm không kém hơn: SAP khai KTC Newcombe cho hiệu số nguy cơ, engine tính Wald và không ghi phương pháp. Nay
    run_stats_analysis tính đúng phương pháp đặc tả khai (`--kc-hieu-so`), ghi mã + tên; cầu nối R (DescTools) và SPSS
    (PROPORTIONS) tính lại cùng phương pháp; chay_sap_g6 `kiem` và G6-AUTO-09 chặn khi lệch hoặc SAP khai phương pháp
    G6 chưa tính (không tự lùi về Wald).

Số tham chiếu KTC Newcombe: bảng II của chính bài gốc (Newcombe RG. Stat Med 1998;17:873–90, PMID 9595617 — đã tra
PubMed, kiểm rút bài 23/11/2026: không bị rút), trùng DescTools::BinomDiffCI(method = "score") và SPSS 31 PROPORTIONS.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import chay_sap_g6 as CS6  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import khung_de_tai as KD  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

FX_SPSS = Path(__file__).resolve().parent / "fixtures" / "spss_hieu_so"


# ───────────────────────────── (2) KTC Newcombe hybrid score ─────────────────────────────
@pytest.mark.parametrize("e1, n1, e0, n0, lo, hi", [
    (56, 70, 48, 80, 0.0524, 0.3339),   # Newcombe 1998 bảng II ví dụ (a)
    (9, 10, 3, 10, 0.1705, 0.8090),     # ví dụ (b)
    (5, 56, 0, 29, -0.0381, 0.1926),    # ví dụ (d) — một nhóm 0 % biến cố (Wald suy biến)
    (0, 10, 0, 20, -0.1611, 0.2775),    # ví dụ (e) — cả hai nhóm 0 %
])
def test_newcombe_trung_bang_ii_bai_goc(e1, n1, e0, n0, lo, hi):
    a, b = RSA.kc_hieu_so_newcombe(e1, n1, e0, n0)
    assert a == pytest.approx(lo, abs=6e-5) and b == pytest.approx(hi, abs=6e-5)


def test_newcombe_trung_spss_va_descTools_toi_chu_so_cuoi():
    """SPSS 31 PROPORTIONS (OXML thật trong fixture) và DescTools ra 0,052431472402 – 0,333872654037 cho ví dụ (a)."""
    a, b = RSA.kc_hieu_so_newcombe(56, 70, 48, 80)
    sp = S.doc_hieu_so(FX_SPSS)
    assert sp == {"rd": 0.2, "ci": [pytest.approx(a, abs=1e-12), pytest.approx(b, abs=1e-12)],
                  "phuong_phap": "newcombe", "n": 150}


def _df_nhi_phan():
    pd = pytest.importorskip("pandas")
    y = [1] * 56 + [0] * 14 + [1] * 48 + [0] * 32
    g = [1] * 70 + [0] * 80
    return pd.DataFrame({"y": y, "nhom": g})


def test_compare_primary_outcome_ghi_dung_phuong_phap():
    df = _df_nhi_phan()
    nc = RSA.compare_primary_outcome(df, "y", "nhom", "binary", kc_hieu_so_pp="newcombe")
    assert nc["risk_diff_ci_method"] == "newcombe" and "Newcombe" in nc["risk_diff_ci_ten"]
    assert nc["risk_diff_ci_95"] == (0.0524, 0.3339)
    wd = RSA.compare_primary_outcome(df, "y", "nhom", "binary")  # mặc định cũ: Wald, nay GHI tên
    assert wd["risk_diff_ci_method"] == "wald" and wd["risk_diff_ci_95"] == (0.0575, 0.3425)
    txt = RSA.format_outcome_text(nc, "y", {})
    assert "Phương pháp KTC của hiệu số nguy cơ: Newcombe hybrid score" in txt


def test_phuong_phap_la_bi_tu_choi_khong_lui_ve_wald():
    with pytest.raises(ValueError, match="không tự lùi về Wald"):
        RSA.compare_primary_outcome(_df_nhi_phan(), "y", "nhom", "binary", kc_hieu_so_pp="miettinen_nurminen")
    with pytest.raises(ValueError, match="không tự lùi về Wald"):
        RSA.kc_hieu_so(1, 10, 2, 10, "agresti_caffo")


def test_benh_chung_go_ca_ma_phuong_phap_hieu_so():
    res = RSA.bo_hieu_so_benh_chung(RSA.compare_primary_outcome(_df_nhi_phan(), "y", "nhom", "binary"))
    assert not {"risk_diff", "risk_diff_ci_95", "risk_diff_ci_method", "risk_diff_ci_ten"} & set(res)


def test_mot_danh_sach_phuong_phap_cho_engine_cong_va_cau_noi():
    """Engine, cổng G6 và cầu nối SPSS cùng MỘT tập phương pháp — thêm ở một nơi mà quên nơi khác thì đỏ."""
    assert set(RSA.KC_HIEU_SO) == {ma for ma, _ in G6Q.KC_HIEU_SO_HO_TRO} == set(S.CITYPES_HIEU_SO)


# ───────────────────────────── cổng G6: họ mô hình + phương pháp KTC ─────────────────────────────
@pytest.mark.parametrize("sap4, ho", [
    ("- **Phương pháp:** Conditional logistic regression", {"logistic_dk"}),
    ("- **Phương pháp:** Hồi quy logistic có điều kiện theo bộ ghép", {"logistic_dk"}),
    ("- **Phương pháp:** Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép (ghép theo tần suất) → OR",
     {"logistic"}),
    ("- Chính: hồi quy logistic có điều kiện; độ nhạy: hồi quy logistic không điều kiện", {"logistic_dk", "logistic"}),
])
def test_ho_sap_tach_logistic_co_dieu_kien(sap4, ho):
    assert G6Q._ho_mo_hinh_sap(sap4) == ho


def test_ho_script_clogit_la_logistic_co_dieu_kien():
    assert G6Q._ho_mo_hinh_script("fit <- survival::clogit(y ~ x + strata(bo))") == ["logistic_dk"]
    assert G6Q._ho_mo_hinh_script("fit <- glm(y ~ x, family = binomial())") == ["logistic"]


@pytest.mark.parametrize("sap4, pp, chua", [
    ("- **Phương pháp:** Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với biên Δ", "newcombe", []),
    ("- Hiệu số nguy cơ + KTC 95% Wald", "wald", []),
    ("- Hiệu số nguy cơ + KTC Miettinen–Nurminen", None, ["Miettinen–Nurminen"]),
    ("- Hiệu tỷ lệ + KTC Newcombe có hiệu chỉnh liên tục", None, ["newcombe có hiệu chỉnh liên tục"]),
    ("- Hiệu nguy cơ (risk difference) + 95%CI; hiệu chỉnh: hồi quy nhị thức", None, []),
    ("- Hồi quy logistic, p kiểm định Wald\n- Hiệu tỷ lệ + 95%CI", None, []),  # «Wald» KHÔNG trên dòng hiệu số
])
def test_doc_phuong_phap_kc_hieu_so_tu_sap(sap4, pp, chua):
    kc = G6Q.phuong_phap_kc_hieu_so_sap(sap4)
    assert kc["phuong_phap"] == pp and kc["chua_ho_tro"] == chua


SAP_BC_DK = "### §4\n- **Phương pháp:** Conditional logistic regression\n"
SAP_BC_KDK = "- **Phương pháp:** Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép → OR (95%CI)\n"
SAP_NI = "- **Phương pháp:** Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với biên Δ\n"
TOM_BC = {"primary_outcome": {"outcome_type": "binary", "or_crude": 1.6}, "multivariate": {"model": "logistic"}}


def _tom_ni(pp):
    po = {"outcome_type": "binary", "risk_diff": -0.0437, "risk_diff_ci_95": [-0.1084, 0.0215]}
    if pp:
        po["risk_diff_ci_method"] = pp
    return {"primary_outcome": po, "multivariate": {"model": "logistic"}}


def test_auto12_benh_chung_sap_co_dieu_kien_ma_chay_khong_dieu_kien_la_do():
    dat, ct = G6Q.doi_chieu_phuong_phap_da_chay(SAP_BC_DK, TOM_BC)
    assert dat is False and "logistic_dk" in ct and "không tự lùi" in ct
    assert G6Q.doi_chieu_phuong_phap_da_chay(SAP_BC_KDK, TOM_BC)[0] is True


@pytest.mark.parametrize("pp, dat", [("newcombe", True), ("wald", False), (None, False)])
def test_auto12_ni_phuong_phap_ktc_phai_dung_sap(pp, dat):
    kq, ct = G6Q.doi_chieu_phuong_phap_da_chay(SAP_NI, _tom_ni(pp))
    assert kq is dat, ct


def test_auto12_sap_khai_phuong_phap_chua_ho_tro_la_do_va_khong_do_duoc_khong_xanh():
    kq, ct = G6Q.doi_chieu_phuong_phap_da_chay("- Hiệu tỷ lệ + KTC Miettinen–Nurminen\n", _tom_ni("wald"))
    assert kq is False and "CHƯA tính" in ct
    assert G6Q.doi_chieu_phuong_phap_da_chay(SAP_NI, None)[0] is None          # chưa chạy ⇒ không đo được
    assert G6Q.doi_chieu_phuong_phap_da_chay(SAP_NI, {"x": 1})[0] is None      # không nhận ra họ ⇒ không đo được
    assert G6Q.doi_chieu_phuong_phap_da_chay("- Hiệu tỷ lệ\n", {"primary_outcome": {"risk_diff": 0.1}})[0] is True


@pytest.mark.parametrize("tom, ho", [
    ({"multivariate": {"model": "logistic"}}, {"logistic"}),
    ({"multivariate": {"model": "logistic", "error": "x"}}, set()),
    ({"poisson_pr": {"model": "poisson_robust_hc0"}, "primary_outcome": {"risk_diff": 0.1}}, {"poisson", "risk_diff"}),
    ({"ordinal": {"model": "ordinal_logit_po"}}, {"ordinal"}),
    ({"survival": {"crude": {}}}, {"cox"}),
    ({"ty_le": [{"cot": "a"}]}, {"proportion"}),
    ({"loai_dac_thu": "chan_doan"}, {"roc"}),
    ({"primary_outcome": {"outcome_type": "continuous", "md_crude": 1.2}}, {"linear"}),
])
def test_ho_mo_hinh_tu_tom_tat(tom, ho):
    assert G6Q.ho_mo_hinh_tom_tat(tom) == ho


# ───────────────────────────── chay_sap_g6: đặc tả phải theo SAP ─────────────────────────────
def _ds(*ts_phu, kc=None):
    chinh = {"outcome": "y", "group": "nhom"}
    if kc:
        chinh["kc_hieu_so"] = kc
    ds = [{"id": "MT1_chinh", "vai": "chinh", "tham_so": chinh}]
    ds += [{"id": f"P{i}", "vai": "nhom_con", "tham_so": t} for i, t in enumerate(ts_phu)]
    return ds


def test_dac_ta_thieu_hoac_lech_phuong_phap_sap_bi_tu_choi():
    sap = "### §4\n" + SAP_NI
    assert CS6.kiem_kc_hieu_so_sap(_ds(kc="newcombe"), sap) == ([], [])
    loi, _ = CS6.kiem_kc_hieu_so_sap(_ds(), sap)
    assert loi and "engine sẽ tính Wald" in loi[0]
    loi, _ = CS6.kiem_kc_hieu_so_sap(_ds(kc="wald"), sap)
    assert loi and "«wald»" in loi[0]
    # nhóm con CÙNG kết cục chính cũng phải cùng phương pháp; kết cục khác không bị đòi
    loi, _ = CS6.kiem_kc_hieu_so_sap(_ds({"outcome": "y", "group": "nhom", "loc": "gioi == 1"}, kc="newcombe"), sap)
    assert len(loi) == 1 and loi[0].startswith("P0")
    assert CS6.kiem_kc_hieu_so_sap(_ds({"outcome": "khac", "group": "nhom"}, kc="newcombe"), sap) == ([], [])


def test_dac_ta_sap_khai_phuong_phap_chua_ho_tro_va_gia_tri_la():
    loi, _ = CS6.kiem_kc_hieu_so_sap(_ds(kc="newcombe"), "### §4\n- Hiệu tỷ lệ + KTC Agresti–Caffo\n")
    assert loi and "Agresti–Caffo" in loi[0]
    assert CS6._kiem_gia_tri("kc_hieu_so", "kc_hieu_so", "miettinen")
    assert CS6._kiem_gia_tri("kc_hieu_so", "kc_hieu_so", "newcombe") == []
    _, canh = CS6.kiem_kc_hieu_so_sap(_ds(kc="newcombe"), "### §4\n- Hiệu tỷ lệ + 95%CI\n")
    assert canh and "không khai phương pháp" in canh[0]
    assert CS6.doi_so_run_stats({"tham_so": {"outcome": "y", "group": "g", "kc_hieu_so": "newcombe"}})[-2:] == [
        "--kc-hieu-so", "newcombe"]


# ───────────────────────────── cầu nối SPSS / R: cùng phương pháp ─────────────────────────────
def test_cu_phap_spss_hieu_so_dung_chieu_va_phuong_phap():
    dong = S.cu_phap_hieu_so("y", "nhom", ["0", "1"], True, "newcombe")
    assert "SELECT=LEVEL(1 0) CITYPES=NEWCOMBE" in dong[0] and "SUCCESS VALUE=LAST" in dong[1]
    assert "CITYPES=WALD" in S.cu_phap_hieu_so("y", "nhom", ["0", "1"], True, None)[0]  # tóm tắt cũ = Wald
    with pytest.raises(S.TuChoi, match="không tự lùi về Wald"):
        S.cu_phap_hieu_so("y", "nhom", ["0", "1"], True, "agresti_caffo")


def _pc(pp="newcombe"):
    return {"outcome_type": "binary", "group_0": {"n": 80}, "group_1": {"n": 70}, "risk_diff": 0.2,
            "risk_diff_ci_95": [0.0524, 0.3339], "risk_diff_ci_method": pp}


def test_doi_chieu_spss_hieu_so():
    sp = S.doc_hieu_so(FX_SPSS)
    d = S.doi_chieu_hieu_so(_pc(), sp)
    assert len(d) == 1 and d[0]["trang_thai"] == "khop", d
    assert S.doi_chieu_hieu_so(_pc("wald"), sp)[0]["trang_thai"] == "khong_so_duoc"
    lech = dict(_pc(), risk_diff_ci_95=[0.0534, 0.3339])  # lệch 0,001 > đơn vị làm tròn ⇒ LỆCH
    assert S.doi_chieu_hieu_so(lech, sp)[0]["trang_thai"] == "lech"
    assert S.doi_chieu_hieu_so({"outcome_type": "binary", "or_crude": 1.5}, sp) == []  # bệnh–chứng: không hiệu số


R_DESCTOOLS = {"n": [80, 70], "rd": 0.2, "rd_ci": [0.0524314724023647, 0.333872654036911], "rd_phuong_phap": "newcombe"}


def test_doi_chieu_r_hieu_so():
    d = R._hieu_so_nguy_co(_pc(), R_DESCTOOLS, 150, 150)
    assert len(d) == 1 and d[0]["trang_thai"] == "khop", d
    assert R._hieu_so_nguy_co(_pc("wald"), R_DESCTOOLS, 150, 150)[0]["trang_thai"] == "khong_so_duoc"
    lech = dict(_pc(), risk_diff_ci_95=[0.0534, 0.3339])
    assert R._hieu_so_nguy_co(lech, R_DESCTOOLS, 150, 150)[0]["trang_thai"] == "lech"
    assert "R không ra" in R._hieu_so_nguy_co(_pc(), {"n": [80, 70]}, 150, 150)[0]["ghi_chu"]


def test_script_r_tinh_newcombe_bang_desctools_va_dac_ta_lech_bi_tu_choi():
    dong = [d for d in R.MAU_R.splitlines() if d.strip() and not d.strip().startswith("#")]
    assert any('DescTools::BinomDiffCI(e1, n1, e0, n0, conf.level = 0.95, method = "score")' in d for d in dong)
    assert any('if (identical(KC_HIEU_SO, "newcombe")) "DescTools"' in d for d in dong)
    assert any(d.startswith("KC_HIEU_SO <- @@KC_HIEU_SO@@") for d in dong)
    assert R._dac_ta_lech({"kc_hieu_so": "newcombe"}, {"kc_hieu_so": "wald"})


# ───────────────────────────── (1) bệnh–chứng: kiểu ghép ở G1 → SAP G4 ─────────────────────────────
@pytest.mark.parametrize("g1, kieu", [
    ({"control_source": "ghép theo giới và nhóm tuổi 5 năm, tỷ lệ 2 chứng : 1 ca"}, None),  # lời cũ: mơ hồ
    ({"control_source": "ghép theo tần suất theo giới, không ghép cặp cá thể"}, "tan_suat"),
    ({"control_source": "mỗi ca ghép cặp 1:2 với chứng cùng giới"}, "ca_the"),
    ({"control_source": "chứng ngẫu nhiên, không ghép"}, "khong_ghep"),
    ({"control_source": "chứng ngẫu nhiên từ sổ khám"}, "khong_ghep"),
    ({"control_source": "ghép theo tần suất; mỗi ca có bộ ghép riêng"}, None),  # mâu thuẫn
    ({"matching_type": "individual", "control_source": "ghép theo tần suất"}, "ca_the"),  # khai tường minh thắng
    ({"matching_type": "nhom"}, None),
])
def test_kieu_ghep_benh_chung(g1, kieu):
    assert KD.kieu_ghep_benh_chung(g1)[0] == kieu


def _tc(g1, a2="", internal="case_control"):
    tt, bc, hd = G1Q._kiem_kieu_ghep(internal, g1, a2)
    return {"status": tt, "evidence": bc, "action": hd}


def test_g1_auto04c_chan_kieu_ghep_mo_ho_va_phuong_phap_trai_kieu_ghep():
    assert _tc({"control_source": "ghép theo giới và nhóm tuổi"})["status"] == "BLOCK"
    ts = {"matching_type": "frequency",
          "bias_controls": [{"bien_phap": "Hiệu chỉnh trong mô hình hồi quy logistic có điều kiện"}]}
    assert _tc(ts)["status"] == "BLOCK"
    ts["bias_controls"] = [{"bien_phap": "Hiệu chỉnh trong hồi quy logistic không điều kiện cùng các biến ghép"}]
    assert _tc(ts)["status"] == "PASS"
    assert _tc(ts, a2="Phân tích chính: Conditional logistic regression theo matched set")["status"] == "BLOCK"
    assert _tc(ts, a2="Không dùng hồi quy logistic có điều kiện vì không có bộ ghép")["status"] == "PASS"
    ct = {"matching_type": "individual", "bias_controls": [{"bien_phap": "hồi quy logistic không điều kiện"}]}
    assert _tc(ct)["status"] == "BLOCK"
    assert _tc({}, internal="rct")["status"] == "PASS"


def test_g1_auto04c_trong_cong_gom_kiem_kieu_ghep(tmp_path):
    """Nối dây: kiểm kiểu ghép đi vào CHÍNH tiêu chí G1-AUTO-04c của evaluate_g1_quality (không mở mã mới)."""
    from tests.test_g1_quality_gate import _build_case, _design, _evaluate

    thiet_ke = dict(_design(), internal_code="case_control")

    def tc04c(g1, thu):
        bao = _evaluate(_build_case(tmp_path / thu, meta={"gate_params": {"G1": g1}}, design_value=thiet_ke))
        return next(c for c in bao["automatic_criteria"] if c["id"] == "G1-AUTO-04c")

    mo_ho = tc04c({"control_source": "ghép theo giới và nhóm tuổi 5 năm"}, "a")
    assert mo_ho["status"] == "BLOCK" and "chưa chốt kiểu ghép" in mo_ho["evidence"], mo_ho
    ro = tc04c({"matching_type": "frequency", "control_source": "ghép theo tần suất theo giới"}, "b")
    assert ro["status"] == "PASS" and "ghép theo tần suất" in ro["evidence"], ro


def _sap_g4(kieu):
    return G4.generate("BC", "Bệnh–chứng X", "case_control", "Bệnh–chứng", "STROBE", 300, 0.05, 0.8, 1.84, "OR",
                       "2026-11-23", khung={"kieu_ghep": kieu} if kieu else None)


def test_g4_khuon_sap_benh_chung_theo_kieu_ghep():
    def muc4(s):
        return s.split("§4", 1)[1].split("§5", 1)[0]

    assert "Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép" in muc4(_sap_g4("tan_suat"))
    assert "conditional logistic" not in muc4(_sap_g4("tan_suat")).casefold()
    assert "Conditional logistic" in muc4(_sap_g4("ca_the")) or "conditional logistic" in muc4(_sap_g4("ca_the"))
    assert "Hồi quy logistic không điều kiện → OR" in muc4(_sap_g4("khong_ghep"))
    assert "[CẦN CHỐT kiểu ghép" in muc4(_sap_g4(None))  # chưa chốt ⇒ ô trống, G4 không khoá được §4


def test_k17_12d_nhan_hieu_chinh_theo_bien_ghep():
    import kiem_chuan_de_cuong_theo_muc as K

    mau = K._STROBE_TIEU_CHI[("12d", "benh_chung")][3][0].mau
    assert re.search(mau, "Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép (ghép theo tần suất)")
    assert re.search(mau, "hồi quy logistic có điều kiện theo bộ ghép")
    assert not re.search(mau, "Hồi quy logistic → OR")


# ───────────────────────────── kịch bản giả lập: dữ liệu nguồn đúng thiết kế ─────────────────────────────
def test_kich_ban_benh_chung_khai_ghep_tan_suat_va_dac_ta_g6_co_bien_ghep():
    import gia_lap_dinh_ky as GL
    import gia_lap_kich_ban_them as KBT

    kb = GL.KICH_BAN["benh_chung"]
    g1 = kb["pi"]["G1"]
    kieu, can_cu = KD.kieu_ghep_benh_chung(g1)
    assert kieu == "tan_suat" and "matching_type" in can_cu, "PI chốt kiểu ghép tường minh (không để máy suy từ lời)"
    assert not any("có điều kiện" in b["bien_phap"] for b in KBT.SAI_LECH_PI["case_control"])
    assert _tc(g1)["status"] == "PASS"
    chinh = next(x for x in kb["ho_so_tron_vong"]["g6"] if x.get("vai") == "chinh")
    assert {"tuoi", "gioi"} <= set(chinh["tham_so"]["covariates"])
    vai = {d[3]: d[2] for d in kb["bien_so"]["ma_tran"]}
    assert vai.get("tuoi") == "hiep_bien" and vai.get("gioi") == "hiep_bien"


# ───────────────────────────── tích hợp: G6-AUTO-09 (phần lượt chạy) trong evaluate_study ─────────────────
from tests.test_g6_quality_gate_20260815 import de_tai_g6  # noqa: E402,F401 — fixture đề tài G6 chuỗi thật


def _ck(bao, ma):
    return next(k for k in bao["checks"] if k["id"] == ma)


def test_auto09_luot_chay_trong_cong(de_tai_g6):  # noqa: F811 — fixture nạp ở trên
    """Fixture RCT: SAP §4 họ tuyến tính, script tuyến tính ⇒ phần script ĐẠT; phần lượt chạy quyết định kết quả."""
    study, out, goc = de_tai_g6
    tom_p = out / "G6_analysis_summary.json"
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    k = _ck(bao, "G6-AUTO-09")
    assert k["pass"] is True and "chưa có G6_analysis_summary.json" in k["detail"]  # chưa chạy: giữ kết quả script
    assert bao["status"] == "READY_FOR_STATISTICIAN_REVIEW"  # tiền đề: mẫu lành không DRAFT
    tom_p.write_text(json.dumps(TOM_BC), encoding="utf-8", newline="\n")  # engine chạy logistic, SAP khoá tuyến tính
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    k = _ck(bao, "G6-AUTO-09")
    assert k["pass"] is False and k["blocking"] and bao["status"] == "BLOCKED" and "ĐÃ CHẠY" in k["detail"], k
    tom_p.write_text(json.dumps({"multivariate": {"model": "linear"}}), encoding="utf-8", newline="\n")
    k = _ck(G6Q.evaluate_study(study, out, write=False, repo_root=goc), "G6-AUTO-09")
    assert k["pass"] is True and "LƯỢT CHẠY: phân tích chính đã chạy họ ['linear']" in k["detail"], k
    # khối mô hình chính có mà lỗi (không nhận ra họ đã chạy) ⇒ chưa đối chiếu được ⇒ không PASS
    tom_p.write_text(json.dumps({"multivariate": {"error": "không hội tụ"}}), encoding="utf-8", newline="\n")
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert _ck(bao, "G6-AUTO-09")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"
    # tóm tắt chỉ có siêu dữ liệu (chưa ghi lượt chạy nào) ⇒ như chưa có tóm tắt: giữ kết quả script, ghi rõ chưa đo
    tom_p.write_text(json.dumps({"n_total": 6, "data_lock": {"sha256": "a" * 64}}), encoding="utf-8", newline="\n")
    k = _ck(G6Q.evaluate_study(study, out, write=False, repo_root=goc), "G6-AUTO-09")
    assert k["pass"] is True and "chỉ siêu dữ liệu" in k["detail"], k
    tom_p.write_text("{hỏng", encoding="utf-8", newline="\n")
    with contextlib.redirect_stdout(io.StringIO()):
        bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert _ck(bao, "G6-AUTO-09")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


# ───────────────────────────── chạy THẬT: Python → R (DescTools) / SPSS (PROPORTIONS) cùng Newcombe ─────────────────
def _df_ni(seed: int = 23):
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    rng = np.random.default_rng(seed)
    nhom = rng.integers(0, 2, 300)
    y = rng.binomial(1, np.where(nhom == 1, 0.55, 0.60))
    return pd.DataFrame({"record_id": [f"R{i}" for i in range(300)], "kiem_soat": y, "nhom": nhom,
                         "tuoi": np.round(rng.normal(60, 10, 300), 1)})


THAM_SO_NI = ["--outcome", "kiem_soat", "--group", "nhom", "--covariates", "tuoi", "--outcome-type", "binary",
              "--kc-hieu-so", "newcombe"]


def _dong_hieu_so(dc: dict) -> list[dict]:
    return [x for x in dc["dong"] if "hiệu số nguy cơ thô" in x["muc"]]


@pytest.mark.skipif(not R.ung_vien_rscript(), reason="máy không có Rscript")
def test_that_r_desctools_khop_newcombe_python(tmp_path, monkeypatch):
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi, _khung

    try:
        if R.kiem_moi_truong(R.tim_r())["thieu"]:
            pytest.skip("thiếu gói R của cầu nối (cài: cau_noi_r.py cai-goi --ap-dung)")
    except Exception:  # noqa: BLE001
        pytest.skip("không kiểm được môi trường R")
    d = _khung(tmp_path, monkeypatch, "NI-R", _df_ni(), THAM_SO_NI)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["primary_outcome"]["risk_diff_ci_method"] == "newcombe"
    assert tom["dac_ta_phan_tich"]["kc_hieu_so"] == "newcombe"
    dc = _chay_cau_noi("NI-R")
    rd = _dong_hieu_so(dc)
    assert len(rd) == 1 and rd[0]["trang_thai"] == "khop" and "newcombe" in rd[0]["muc"], rd
    script = (d / "r" / "NI-R_phan_tich.R").read_text(encoding="utf-8")
    assert 'KC_HIEU_SO <- "newcombe"' in script


CO_SPSS = any(p.is_file() for p in S.ung_vien_python_spss())


@pytest.mark.skipif(not CO_SPSS, reason="máy không có IBM SPSS Statistics")
def test_that_spss_proportions_khop_newcombe_python(tmp_path, monkeypatch):
    from tests.test_cau_noi_spss_ty_le_20261123 import _chay_spss, _khung_spss

    td = [["record_id", "text", "Mã", "", "", ""], ["kiem_soat", "yesno", "Kiểm soát huyết áp", "", "", ""],
          ["nhom", "yesno", "Nhóm điện thoại", "", "", ""], ["tuoi", "text", "Tuổi", "", "number", ""]]
    _khung_spss(tmp_path, monkeypatch, "NI-SP", _df_ni(), THAM_SO_NI, td)
    _chay_spss("NI-SP", monkeypatch)
    dc = json.loads((S.EXPORTS / "NI-SP" / "G6_spss_doi_chieu.json").read_text(encoding="utf-8"))
    rd = _dong_hieu_so(dc)
    assert len(rd) == 1 and rd[0]["trang_thai"] == "khop", rd
    assert rd[0]["n"]["python"] == rd[0]["n"]["spss"] == 300


# ───────────────────────────── nhãn bộ sinh G1/G6 theo kiểu ghép / họ SAP ─────────────────────────────
def test_bo_sinh_g6_nhan_benh_chung_theo_ho_sap():
    import run_g6_auto as G6A

    kdk = G6A._script03_row("case_control", "OR", "nsaid", "nhom_ca", "t", logistic_dk=False)
    dk = G6A._script03_row("case_control", "OR", "nsaid", "nhom_ca", "t", logistic_dk=True)
    assert "KHÔNG điều kiện" in kdk and "clogit" not in kdk
    assert "CÓ ĐIỀU KIỆN" in dk and "clogit" in dk


@pytest.mark.parametrize("kieu, co, khong", [
    ("frequency", "glm logistic, hiệu chỉnh biến ghép", "clogit"),
    ("individual", "clogit theo bộ ghép", "glm logistic"),
])
def test_bo_sinh_g1_goi_r_theo_kieu_ghep(kieu, co, khong):
    import run_g1_auto as G1A

    design = G1A.infer_study_design("harm", {}, "Tác hại hiếm của phơi nhiễm X")
    a2 = G1A.generate_g1_artifact("Tác hại hiếm của phơi nhiễm X", "BC", design["resolved_question_type"], design, [],
                                  {}, "2026-11-23 10:00", meta={"gate_params": {"G1": {"matching_type": kieu}}})
    dong = next(d for d in a2.splitlines() if d.startswith("R packages dự kiến"))
    assert co in dong and khong not in dong
    phan_tich = next(d for d in a2.splitlines() if d.startswith("Phân tích chính ("))  # khung SAP §4 của A2
    ky_vong = KD.KIEU_GHEP[{"frequency": "tan_suat", "individual": "ca_the"}[kieu]]
    assert ky_vong[0] in phan_tich and ky_vong[1] in phan_tich, phan_tich
