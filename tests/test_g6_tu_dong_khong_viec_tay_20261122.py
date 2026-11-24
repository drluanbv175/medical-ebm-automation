"""G6 không còn «chưa tự động»/việc tay (22/11/2026) — định nghĩa thay thế khai ở G3 → SAP §9 → G6 tự chạy; phân tích
theo đề cương của RCT; gộp hiệu ứng cố định; kappa hai người mã hoá và bằng chứng thủ tục định tính; dòng mô hình chính
THI HÀNH trong 03_analysis.R và 01_cleaning.R chạy được (kiểm cú pháp bằng R thật khi máy có Rscript)."""
from __future__ import annotations

import csv
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import bang_chung_dinh_tinh as BCD  # noqa: E402
import chay_sap_g6 as CS  # noqa: E402
import dinh_nghia_thay_the as DTT  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402
import phan_tich_thiet_ke_dac_thu as PTD  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import run_g6_auto as R6  # noqa: E402

CO_R = shutil.which("Rscript") is not None

MA_TRAN = [
    {"vai_tro": "ket_cuc_chinh", "bien": "kiem_soat", "khai_niem": "Kiểm soát huyết áp", "kieu": "nhi_phan"},
    {"vai_tro": "phoi_nhiem", "bien": "nhom", "khai_niem": "Nhóm can thiệp", "kieu": "nhi_phan"},
    {"vai_tro": "dinh_nghia_thay_the", "bien": "kiem_soat_130", "khai_niem": "kiểm soát huyết áp", "kieu": "nhi_phan",
     "cong_cu": "Đích < 130 mmHg (PMID 29133356)"},
    {"vai_tro": "tuan_thu_de_cuong", "bien": "tuan_thu", "khai_niem": "Tuân thủ", "kieu": "nhi_phan",
     "cong_cu": "≥ 80% số lần can thiệp"},
]


# ─────────────────────────── định nghĩa thay thế ───────────────────────────
def test_tu_dong_ma_tran_khop_theo_khai_niem_bo_dau():
    ds = DTT.tu_dong_ma_tran(MA_TRAN)
    assert ds == [{"bien": "kiem_soat_130", "kieu": "nhi_phan", "dinh_nghia": "Đích < 130 mmHg (PMID 29133356)",
                   "khai_niem": "kiểm soát huyết áp", "thay": "kiem_soat", "vai_thay": "ket_cuc_chinh"}]


def test_khai_niem_cua_phoi_nhiem_thi_thay_phoi_nhiem():
    mt = MA_TRAN[:2] + [{"vai_tro": "dinh_nghia_thay_the", "bien": "so_thang", "khai_niem": "nhóm can thiệp",
                         "kieu": "lien_tuc", "cong_cu": "thang gốc"}]
    (d,) = DTT.tu_dong_ma_tran(mt)
    assert (d["thay"], d["vai_thay"]) == ("nhom", "phoi_nhiem")
    (pt,) = DTT.phan_tich_g6([d], {"outcome": "kiem_soat", "group": "nhom", "covariates": ["tuoi"], "loc": "a == 1"})
    assert pt["tham_so"] == {"outcome": "kiem_soat", "group": "so_thang", "covariates": ["tuoi"], "loc": "a == 1",
                             "don_vi_phoi_nhiem": "1SD"}


def test_thay_dong_chung_sap_bang_dinh_nghia_cu_the():
    sap = "### §9 PHÂN TÍCH ĐỘ NHẠY\n\n" + DTT.DONG_CHUNG + "\n- Complete case vs MI  \n"
    moi = DTT.thay_dong_chung(sap, DTT.tu_dong_ma_tran(MA_TRAN))
    assert DTT.DONG_CHUNG.strip() not in moi
    assert "`kiem_soat`: `kiem_soat_130` — Đích < 130 mmHg (PMID 29133356)" in moi
    assert "- Complete case vs MI" in moi
    assert DTT.thay_dong_chung(sap, []) == sap  # không khai ⇒ giữ nguyên


@pytest.mark.parametrize("ts, d, mong", [
    ({"outcome": "y", "group": "g"}, {"bien": "y2", "kieu": "lien_tuc", "thay": "y", "vai_thay": "ket_cuc_chinh"},
     {"outcome": "y2", "group": "g", "outcome_type": "continuous"}),
    ({"outcome": "y", "group": "g", "outcome_type": "binary"},
     {"bien": "y2", "kieu": "nhi_phan", "thay": "y", "vai_thay": "ket_cuc_chinh"},
     {"outcome": "y2", "group": "g", "outcome_type": "binary"}),
    ({"ty_le": ["y"]}, {"bien": "y2", "kieu": "nhi_phan", "thay": "y", "vai_thay": "ket_cuc_chinh"}, {"ty_le": ["y2"]}),
    ({"loai_dac_thu": "chan_doan", "tham_chieu": "r", "chi_so": "x", "nguong": 2.67},
     {"bien": "x13", "kieu": "nhi_phan", "thay": "x", "vai_thay": "phoi_nhiem"},
     {"loai_dac_thu": "chan_doan", "tham_chieu": "r", "chi_so": "x13", "nguong": 1}),
    ({"loai_dac_thu": "du_bao", "outcome": "y", "covariates": ["a", "b"]},
     {"bien": "b2", "kieu": "lien_tuc", "thay": "b", "vai_thay": "yeu_to"},
     {"loai_dac_thu": "du_bao", "outcome": "y", "covariates": ["a", "b2"]}),
])
def test_phan_tich_g6_thay_dung_mot_bien(ts, d, mong):
    d = {**d, "dinh_nghia": "căn cứ", "khai_niem": "k"}
    (pt,) = DTT.phan_tich_g6([d], ts)
    assert pt["tham_so"] == mong
    assert pt["sap_neo"] == f"`{d['thay']}`: `{d['bien']}`" and pt["vai"] == "do_nhay" and pt["sap_muc"] == "§9"


def test_vai_khong_co_trong_phan_tich_chinh_thi_khong_dung_muc():
    d = {"bien": "z", "kieu": "nhi_phan", "thay": "khong_co", "vai_thay": "ket_cuc_chinh", "dinh_nghia": "",
         "khai_niem": ""}
    assert DTT.phan_tich_g6([d], {"outcome": "y", "group": "g"}) == []


def test_theo_de_cuong_chen_dau_muc_9_va_dac_ta_loc():
    tt = DTT.tuan_thu_tu_dong_ma_tran(MA_TRAN)
    sap = "### §8 X\n\n### §9 PHÂN TÍCH ĐỘ NHẠY\n\n- Complete case vs MI  \n"
    moi = DTT.chen_theo_de_cuong(sap, tt)
    i9 = moi.index("### §9")
    assert moi.index(DTT.NEO_THEO_DE_CUONG) > i9 and "`tuan_thu` = 1" in moi
    assert DTT.chen_theo_de_cuong(moi, tt) == moi  # không chèn lặp
    pt = DTT.phan_tich_theo_de_cuong(tt, {"outcome": "y", "group": "g", "loc": "du == 1"})
    assert pt["tham_so"]["loc"] == "du == 1 and tuan_thu == 1" and pt["sap_neo"] == DTT.NEO_THEO_DE_CUONG


def test_g4_dien_khung_chep_dinh_nghia_va_theo_de_cuong_cho_rct():
    sap = "### §9 PHÂN TÍCH ĐỘ NHẠY\n\n" + DTT.DONG_CHUNG + "\n- Complete case vs MI  \n"
    khung = {"dinh_nghia_thay_the": DTT.tu_dong_ma_tran(MA_TRAN),
             "tuan_thu_de_cuong": DTT.tuan_thu_tu_dong_ma_tran(MA_TRAN)}
    rct = G4._dien_khung(sap, khung, "rct")
    assert "`kiem_soat_130`" in rct and DTT.NEO_THEO_DE_CUONG in rct
    coh = G4._dien_khung(sap, khung, "cohort")
    assert "`kiem_soat_130`" in coh and DTT.NEO_THEO_DE_CUONG not in coh  # theo đề cương chỉ cho RCT


def test_ma_tran_nhan_hai_vai_moi():
    assert {"dinh_nghia_thay_the", "tuan_thu_de_cuong"} <= MT.VAI_TRO
    vt = MT.vai_tro_tu_dong([{"vai_tro": r["vai_tro"], "bien": r["bien"], "kieu": r["kieu"]} for r in MA_TRAN])
    assert vt["dinh_nghia_thay_the"] == ["kiem_soat_130"] and vt["tuan_thu_de_cuong"] == "tuan_thu"


# ─────────────────────────── chay_sap_g6: kiểu tham số mới ───────────────────────────
def test_kiem_gia_tri_1sd_mo_hinh_bang_chung():
    assert CS._kiem_gia_tri("don_vi_phoi_nhiem", "so", "1SD") == []
    assert CS._kiem_gia_tri("don_vi_phoi_nhiem", "so", "2SD")
    assert CS._kiem_gia_tri("mo_hinh", "s", "co_dinh") == []
    assert CS._kiem_gia_tri("mo_hinh", "s", "khac")
    assert CS._kiem_gia_tri("bang_chung", "bang_chung", "credibility") == []
    assert CS._kiem_gia_tri("bang_chung", "bang_chung", "khac")


def test_tom_tat_gop_co_dinh_bao_uoc_luong_co_dinh():
    dt_ = {"rr_gop_ngau_nhien": 0.7, "ci_95": [0.6, 0.8], "rr_gop_co_dinh": 0.71, "ci_95_co_dinh": [0.65, 0.78],
           "i2_pct": 10.0, "k": 12}
    ra = CS._tom_tat_uoc_luong({"dac_thu": dt_, "loai_dac_thu": "gop", "dac_ta_phan_tich": {"mo_hinh": "co_dinh"}})
    assert ra["gop"]["rr"] == 0.71 and ra["gop"]["ci_95"] == [0.65, 0.78] and ra["gop"]["mo_hinh"] == "co_dinh"
    ra = CS._tom_tat_uoc_luong({"dac_thu": dt_, "loai_dac_thu": "gop", "dac_ta_phan_tich": {}})
    assert ra["gop"]["rr"] == 0.7 and ra["gop"]["mo_hinh"] == "ngau_nhien"


# ─────────────────────────── phân tích đặc thù: gộp cố định · kappa ───────────────────────────
def _hang_gop():
    rng = random.Random(3)
    return [{"study_id": f"S{i}", "a": rng.randint(20, 40), "n1": 400, "c": rng.randint(30, 55), "n0": 400}
            for i in range(10)]


def test_gop_so_doi_chieu_co_hieu_ung_co_dinh_chi_r_so():
    kq = PTD.gop(_hang_gop(), "study_id", "a", "n1", "c", "n0")
    so = PTD.cac_so_doi_chieu("gop", kq)
    assert so["rr_gop_co_dinh"] == kq["rr_gop_co_dinh"] and so["ci_duoi_co_dinh"] == kq["ci_95_co_dinh"][0]
    spss = PTD.dai_luong_spss("gop", so)
    assert "rr_gop" in spss and not any(k.endswith("_co_dinh") for k in spss)


def test_kappa_hai_nguoi_ma_hoa_dung_cong_thuc():
    hang = [{"c1": a, "c2": b} for a, b in [("A", "A")] * 6 + [("B", "B")] * 3 + [("A", "B"), ("B", "A")]
            + [("C", "")]]
    dt = PTD.dong_thuan_hai_nguoi(hang, "c1", "c2")
    po, pe = 9 / 11, (7 / 11) * (7 / 11) + (4 / 11) * (4 / 11)
    assert dt["n_cap"] == 11 and dt["n_trung"] == 9
    assert dt["kappa"] == pytest.approx((po - pe) / (1 - pe))
    kq = PTD.dinh_tinh(hang, "c1", "c2")
    assert PTD.cac_so_doi_chieu("dinh_tinh", kq)["kappa"] == pytest.approx(dt["kappa"])
    assert "kappa" not in PTD.dai_luong_spss("dinh_tinh", PTD.cac_so_doi_chieu("dinh_tinh", kq))
    assert "dong_thuan_hai_nguoi" not in PTD.dinh_tinh(hang, "c1")


# ─────────────────────────── bằng chứng thủ tục định tính ───────────────────────────
def test_bang_chung_thieu_tep_thieu_cot_du(tmp_path):
    assert BCD.kiem(tmp_path, "X", "credibility")["trang_thai"] == BCD.THIEU
    p = BCD.tep_cua(tmp_path, "X", "credibility")
    p.write_text("ma_nguoi_tham_gia,ngay\nP1,2027-01-01\n", encoding="utf-8", newline="\n")
    r = BCD.kiem(tmp_path, "X", "credibility")
    assert r["trang_thai"] == BCD.THIEU and any("thiếu cột" in x for x in r["thieu"])
    p.write_text(",".join(BCD.KHUON["credibility"]["cot"]) + "\n",
        encoding="utf-8", newline="\n")  # khuôn trống: chỉ tiêu đề
    r = BCD.kiem(tmp_path, "X", "credibility")
    assert r["trang_thai"] == BCD.THIEU and r["thieu"] == ["chưa có dòng nào ghi đủ các cột bắt buộc"]
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(BCD.KHUON["credibility"]["cot"])
        w.writerow(["P1", "2027-01-01", "gặp lại", "tóm tắt", "đồng ý", "không đổi"])
    assert BCD.kiem(tmp_path, "X", "credibility")["trang_thai"] == BCD.DA_KIEM


def test_bang_chung_mo_ta_day_doi_moi_muc_co_noi_dung(tmp_path):
    p = BCD.tep_cua(tmp_path, "X", "transferability")
    p.write_text(BCD.khuon_trong("transferability"), encoding="utf-8", newline="\n")
    r = BCD.kiem(tmp_path, "X", "transferability")
    assert r["trang_thai"] == BCD.THIEU and len(r["thieu"]) == 3  # khuôn trống: ba mục chưa có nội dung
    p.write_text("\n".join(f"{m}\n\nNội dung {i}.\n" for i, m in enumerate(BCD.KHUON["transferability"]["muc"])),
                 encoding="utf-8", newline="\n")
    assert BCD.kiem(tmp_path, "X", "transferability")["trang_thai"] == BCD.DA_KIEM


def test_dac_ta_bang_chung_hop_le_khong_doi_outcome(tmp_path):
    """Mục kiểm bằng chứng thủ tục chỉ có tham số bang_chung — không bị đòi outcome/time/ty_le như mô hình."""
    dt = {"phan_tich": [{"id": "TT_c", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "x",
                         "tham_so": {"bang_chung": "credibility"}}]}
    try:
        loi = CS.kiem_dac_ta(tmp_path, dt)["loi"]
    except Exception as e:  # noqa: BLE001
        loi = [str(e)]
    assert not any(x.startswith("TT_c:") for x in loi), loi


def test_dac_ta_bang_chung_khong_kem_tham_so_khac(tmp_path):
    dt = {"phan_tich": [{"id": "TT_c", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "x",
                         "tham_so": {"bang_chung": "credibility", "outcome": "y"}}]}
    loi = []
    try:
        loi = CS.kiem_dac_ta(tmp_path, dt)["loi"]
    except Exception as e:  # noqa: BLE001 — kiem_dac_ta có thể đòi đủ đặc tả; điều cần kiểm là thông điệp lỗi
        loi = [str(e)]
    assert any("chỉ khai tham số bang_chung" in x for x in loi)


# ─────────────────────────── bộ sinh script R: dòng thi hành ───────────────────────────
def test_bat_dong_thi_hanh_chi_dong_mo_hinh_chinh_va_coeftest_cua_no():
    code = ("# df <- readRDS(x)\n# stopifnot(identical(attr(df, \"sha256_khoa\"), LOCKED_SHA))\n"
            "# fit_rr <- glm(y ~ g, data = df)  # ◆ MÔ HÌNH CHÍNH (SAP §4)\n# lmtest::coeftest(fit_rr)\n"
            "# fit_tho <- glm(y ~ g, data = df)\n# lmtest::coeftest(fit_tho)\n"
            "# m <- f(a,  # ◆ MÔ HÌNH CHÍNH (SAP §4)\n#   b)\n# ghi chú")
    ra = R6.bat_dong_thi_hanh(code).split("\n")
    assert ra[:4] == ["df <- readRDS(x)", 'stopifnot(identical(attr(df, "sha256_khoa"), LOCKED_SHA))',
                      "fit_rr <- glm(y ~ g, data = df)  # ◆ MÔ HÌNH CHÍNH (SAP §4)", "lmtest::coeftest(fit_rr)"]
    assert ra[4].startswith("# fit_tho") and ra[5].startswith("# lmtest::coeftest(fit_tho")
    assert ra[6].startswith("m <- f(a,") and ra[7] == "  b)" and ra[8] == "# ghi chú"


def _v(**k):
    v = {"exposure": "nhom", "outcome": "kiem_soat", "time_col": "follow_time", "covariates": ["tuoi", "gioi"],
         "all_vars": ["record_id", "nhom", "kiem_soat", "tuoi", "gioi"], "kieu_bien": {"gioi": "radio", "tuoi": "text",
                                                                                          "nhom": "radio"},
         "detection_log": [], "nhom_con_sap": [], "cluster_col": None}
    v.update(k)
    return v


def test_r01_thi_hanh_khong_co_bien_du_phong_va_phan_loai_theo_tu_dien():
    code = R6.make_r01_cleaning(_v(), "rct")
    dong = [d for d in code.split("\n") if d and not d.startswith("#")]
    assert any(d.startswith("df_khoa <- utils::read.csv(LOCKED_DATA") for d in dong)
    assert 'saveRDS(df, file.path(DATA_PROC, "df_clean.rds"))' in dong
    assert 'df[["gioi"]] <- factor(df[["gioi"]])' in dong
    assert 'df[["nhom"]] <- suppressWarnings(as.numeric(df[["nhom"]]))' in dong  # phơi nhiễm giữ dạng số
    assert "follow_time" not in "\n".join(dong)  # tên dự phòng không vào dòng thi hành


def test_cong_khong_chen_hiep_bien_du_phong():
    assert R6._cong("") == "" and R6._cong("a + b") == " + a + b"
    code = R6.bat_dong_thi_hanh(R6._r03_binary_with_vars(_v(covariates=[]), "rct", "RR"))
    dong = [d for d in code.split("\n") if d.startswith("fit_rr <-")]
    assert dong and "age" not in dong[0] and "kiem_soat ~ nhom," in dong[0]


def test_cot_gop_va_mo_hinh_gop_thi_hanh():
    v = _v(all_vars=["study_id", "bien_co_can_thiep", "n_can_thiep", "bien_co_chung", "n_chung", "thuoc"])
    assert R6.cot_gop(v) == {"study": "study_id", "event.e": "bien_co_can_thiep", "n.e": "n_can_thiep",
                             "event.c": "bien_co_chung", "n.c": "n_chung"}
    code = R6.bat_dong_thi_hanh(R6._r03_srma_template(v))
    dong = [d for d in code.split("\n") if d.startswith(("extracted <-", "m_chinh <-", "stopifnot("))]
    assert len(dong) == 3 and "meta::metabin(bien_co_can_thiep, n_can_thiep, bien_co_chung, n_chung" in dong[2]


def test_goi_r_khong_lay_duoi_tep_python():
    assert "py" not in R6.goi_r_cho_script("# xem g1_design_blocks.py::_TABLES_DIAGNOSTIC\nmeta::metabin(x)")
    assert "meta" in R6.goi_r_cho_script("meta::metabin(x)")


def test_du_bao_dua_moi_yeu_to_vao_mo_hinh():
    code = R6.bat_dong_thi_hanh(R6._r03_prediction_with_vars(_v(exposure="tuoi", covariates=["lvef", "egfr"])))
    dong = [d for d in code.split("\n") if d.startswith("model_full <-")]
    assert dong and "~ tuoi + lvef + egfr," in dong[0]


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
@pytest.mark.parametrize("thiet_ke", ["rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction",
                                      "sr_ma"])
def test_script_r_thi_hanh_hop_le_cu_phap_r(tmp_path, thiet_ke):
    v = _v(all_vars=["study_id", "bien_co_can_thiep", "n_can_thiep", "bien_co_chung", "n_chung", "nhom", "kiem_soat",
                     "tuoi", "gioi"], outcome_ordinal=False, mo_ta_ty_le=(thiet_ke == "cross_sectional"))
    r03 = R6.bat_dong_thi_hanh(R6.hau_xu_ly_script_r(R6.R_ANALYSIS_MAP_FUNC(thiet_ke, v, 200, 0.05, 0.8, 1.5, "RR"),
                                                     "X", la_03=True))
    r01 = R6.hau_xu_ly_script_r(R6.make_r01_cleaning(v, thiet_ke), "X")
    for ten, ma in (("r01.R", r01), ("r03.R", r03)):
        p = tmp_path / ten
        p.write_text(ma, encoding="utf-8", newline="\n")
        # 23/11/2026: as_posix — đường dẫn Windows «C:\Users\…» nhúng thẳng vào chuỗi R bị đọc «\U» thành mã thoát
        r = subprocess.run(["Rscript", "--vanilla", "-e",
                            f"invisible(parse(file = '{p.as_posix()}', encoding = 'UTF-8'))"],
                           capture_output=True, text=True)
        assert r.returncode == 0, (thiet_ke, ten, r.stderr[-400:])
    assert "◆ MÔ HÌNH CHÍNH" in r03 and any(d.lstrip() and not d.startswith("#") and "◆" in d for d in r03.split("\n"))


# ─────────────────────────── dữ liệu giả lập: biến mới khớp biến gốc ───────────────────────────
def test_gia_lap_thang_goc_tuan_thu_va_nguoi_ma_hoa_thu_hai():
    import gia_lap_dinh_ky as GL  # noqa: PLC0415
    import gia_lap_tron_vong as TV  # noqa: PLC0415

    kb = GL.KICH_BAN["thuan_tap_phoi_nhiem"]
    rows = TV.sinh_du_lieu("cohort", kb["bien_so"], {"p0": 0.2, "effect_size": 1.4}, 300)
    assert all((r["so_thang_ppi"] >= 12) == (r["ppi_dai_han"] == 1) for r in rows)
    kb = GL.KICH_BAN["rct_nhi_phan"]
    rows = TV.sinh_du_lieu("rct", kb["bien_so"], {"p0": 0.48, "effect_size": 1.4}, 300)
    assert {r["tuan_thu_de_cuong"] for r in rows} == {0, 1} and all(r["kiem_soat_t6_130"] is None for r in rows)
    kb = GL.KICH_BAN["dinh_tinh"]
    rows = TV.sinh_du_lieu("qualitative", kb["bien_so"], {}, 40)
    trung = sum(r["chu_de_nguoi_2"] == r["chu_de"] for r in rows) / len(rows)
    assert 0.6 < trung < 1.0
    kb = GL.KICH_BAN["benh_chung"]
    rows = TV.sinh_du_lieu("case_control", kb["bien_so"], {"p0": 0.2, "effect_size": 1.8}, 300)
    assert all((r["so_ngay_nsaid_30"] >= 1) == (r["nsaid_30ngay"] == 1) for r in rows)


def test_gia_lap_chan_thuc_dinh_tinh_khong_gan_quan_the_vao_bang_chung():
    import gia_lap_chan_thuc as GCT  # noqa: PLC0415

    kb = GCT.kich_ban_chan_thuc()["qualitative_chan_thuc"]
    tt = [p for p in kb["ho_so_tron_vong"]["g6"] if p["id"].startswith("TT_")]
    assert len(tt) == 3 and all(p["tham_so"] == {"bang_chung": p["id"][3:]} for p in tt)


def test_tep_du_lieu_kiem_cheo_dinh_tinh_co_cot_nguoi_ma_hoa_thu_hai():
    """R tính kappa trên tệp dữ liệu kiểm chéo — tệp phải có cột người mã hoá thứ hai (lượt giả lập 22/11 bắt lỗi)."""
    cot = [c for c, _ in PTD._gia_tri_spss("dinh_tinh", {"chu_de": "c1", "chu_de_nguoi_2": "c2"})]
    assert cot == ["c1", "c2"]
    assert [c for c, _ in PTD._gia_tri_spss("dinh_tinh", {"chu_de": "c1"})] == ["c1"]


# ─────────────────────────── spline: nút khi phơi nhiễm dồn ở 0 (như Hmisc) ───────────────────────────
def test_nut_spline_phoi_nhiem_don_o_0_nhu_hmisc():
    """Thời lượng dùng thuốc dồn ở 0 (người không dùng) — trước đây nút trùng ⇒ hình G6 lỗi; nay đúng nhánh `fractied`
    của Hmisc::rcspline.eval (số mong đợi đo bằng chính Hmisc 22/11/2026)."""
    import bieu_do_hoi_quy as B  # noqa: PLC0415

    x = [0] * 30 + list(range(1, 60))
    assert B.nut_harrell(x, 4) == pytest.approx([1.0, 4.85, 30.5, 55.0])
    assert B.nut_harrell(x, 5) == pytest.approx([1.0, 4.85, 21.95, 39.05, 55.0])
    assert B.nut_harrell(list(range(50)), 4) == pytest.approx([4.0, 17.15, 31.85, 45.0])  # nhánh n < 100 không đổi
    with pytest.raises(B.LoiBieuDo):
        B.nut_harrell([0] * 50 + [1, 2], 4)
