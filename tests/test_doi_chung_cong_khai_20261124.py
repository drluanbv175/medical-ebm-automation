"""Kiểm ba việc ngày 24/11/2026 (bác sĩ duyệt 23/11).

(⚪ a) Mô hình hỗn hợp intercept ngẫu nhiên (thứ bậc/nhị phân) theo cụm: SPSS 31 GENLINMIXED chỉ ước lượng bằng giả
    khả dĩ phần dư (RSPL — Wolfinger & O'Connell 1993; đặc tả cú pháp không có tuỳ chọn Laplace/cầu phương) ⇒ R tham
    chiếu mô phỏng ĐÚNG RSPL (`pl_rspl` trong cau_noi_spss.R_DOI_CHIEU), hai bên KHỚP tới ≥ 7 chữ số; bản Laplace
    (clmm/glmer — phương pháp phân tích chính theo SAP) chỉ in kèm, không còn dòng «lệch nhỏ» không giải thích.
(⚪ b) Dupont 1988 (PMID 3233252): toàn văn gốc không truy cập được qua làn hợp lệ (JSTOR, không OA, ngoài sổ uỷ
    quyền) ⇒ đối chiếu bằng ví dụ ĐÃ CÔNG BỐ của Stata [PSS] power mcc và StatsDirect (test ở
    test_ghep_cap_mi_hiem_co_mau_20261123).
(3) Đề tài đối chứng công khai — test ở phần dưới.

Ca cần R/SPSS thật tự bỏ qua khi máy không có phần mềm.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC / "tools"))
import cau_noi_spss as C  # noqa: E402

# 24/11/2026: test chạy R thật cần GÓI của cầu nối (ordinal, jsonlite…), không chỉ Rscript — máy CI Windows có R
# nhưng thiếu gói ⇒ trượt thay vì «không đo được». Dùng đúng điều kiện CAN_R của tệp test cầu nối.
from tests.test_cau_noi_r_ty_le_20261122 import CAN_R  # noqa: E402, I001

FX_RSPL = GOC / "tests" / "fixtures" / "spss_oxml" / "rspl"
FX_MR = GOC / "tests" / "fixtures" / "spss_oxml" / "mo_rong"
RSCRIPT = C.tim_rscript()


def _j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _ham_r_pl() -> str:
    s = C.R_DOI_CHIEU
    return s[s.index("pl_rspl <- function"):s.index("hs_ra_t <- function")]


def _chay_r(ma: str, tmp: Path) -> list[float]:
    (tmp / "pl.R").write_text(_ham_r_pl(), encoding="utf-8", newline="\n")
    kq = subprocess.run([RSCRIPT, "--vanilla", "-e", ma], cwd=tmp, capture_output=True, text=True, timeout=600)
    assert kq.returncode == 0, kq.stderr[-1500:]
    return [float(x) for x in kq.stdout.split()]


# ───────────────────────────── (⚪ a) RSPL ↔ GENLINMIXED ─────────────────────────────


@CAN_R
@pytest.mark.parametrize("loai", ["thu_bac", "nhi_phan"])
def test_that_rspl_r_trung_spss_genlinmixed_da_do(loai, tmp_path):
    """R RSPL trên CÙNG dữ liệu giả ⇒ hệ số, SE, phương sai, p (t bậc tự do phần dư) trùng SPSS 31.0.1 đã đo."""
    sp = _j(FX_RSPL / "spss_genlinmixed.json")[loai]
    y = "d$g1" if loai == "thu_bac" else "as.integer(d$g1 >= 4)"
    ma = ('source("pl.R"); d <- read.csv("' + (FX_RSPL / "du_lieu_gia_cum.csv").as_posix() + '"); '
          f'f <- pl_rspl({y}, cbind(nhom = d$nhom, tuoi = d$tuoi), d$cum); stopifnot(f$hoi_tu); '
          'cat(format(c(f$beta, f$se, f$s2, f$df, 2 * pt(-abs(f$beta / f$se), f$df)), digits = 15))')
    b1, b2, s1, s2, var, df, p1, p2 = _chay_r(ma, tmp_path)
    assert (b1, b2) == pytest.approx((sp["nhom"]["b"], sp["tuoi"]["b"]), rel=1e-7)
    assert (s1, s2) == pytest.approx((sp["nhom"]["se"], sp["tuoi"]["se"]), rel=1e-7)
    assert var == pytest.approx(sp["phuong_sai"], rel=1e-6) and df == sp["df"]
    assert (p1, p2) == pytest.approx((sp["nhom"]["p"], sp["tuoi"]["p"]), rel=1e-5)


@CAN_R
def test_that_rspl_khac_laplace_va_khac_ml(tmp_path):
    """Đột biến phương pháp phải lộ: Laplace (clmm) và giả khả dĩ CỰC ĐẠI (MSPL — bỏ số hạng REML) KHÔNG trùng SPSS."""
    sp = _j(FX_RSPL / "spss_genlinmixed.json")["thu_bac"]
    ma = ('source("pl.R"); pl_ml <- eval(parse(text = sub("as.numeric(determinant(G$XVX)$modulus)", "0", '
          'paste(deparse(pl_rspl), collapse = "\\n"), fixed = TRUE))); d <- read.csv("'
          + (FX_RSPL / "du_lieu_gia_cum.csv").as_posix() + '"); '
          'f <- pl_ml(d$g1, cbind(nhom = d$nhom, tuoi = d$tuoi), d$cum); '
          'm <- ordinal::clmm(factor(g1, ordered = TRUE) ~ nhom + tuoi + (1 | cum), data = d); '
          'cat(format(c(f$beta[1], f$s2, coef(m)[["nhom"]]), digits = 15))')
    b_ml, var_ml, b_lap = _chay_r(ma, tmp_path)
    for b in (b_ml, b_lap):
        assert abs(b - sp["nhom"]["b"]) > 1e-3
    assert abs(var_ml - sp["phuong_sai"]) > 1e-2


@pytest.mark.skipif(not RSCRIPT, reason="máy không có Rscript")
def test_that_r_tham_chieu_mo_rong_trung_spss_va_laplace_giu_nguyen(tmp_path):
    """chay_r_tham_chieu thật trên .sav dựng lại từ fixture mo_rong: RSPL trùng r_kq (đã khớp SPSS OXML thật); Laplace
    trùng r_kq cũ (kiểm .sav dựng lại đúng)."""
    sav = tmp_path / "fx.sav"
    ma = ('d <- read.csv("' + (FX_MR / "du_lieu_gia.csv").as_posix() + '", colClasses = "character"); '
          'o <- data.frame(record_id = d$record_id, HL_Chung = suppressWarnings(as.numeric(d$g1)), '
          'thoigian_cho = as.numeric(d$thoigian_cho), tuoi = as.numeric(d$tuoi), gioitinh = as.numeric(d$gioitinh), '
          'ma_ban_kham = d$ma_ban_kham); haven::write_sav(o, "' + sav.as_posix() + '")')
    kq = subprocess.run([RSCRIPT, "--vanilla", "-e", ma], capture_output=True, text=True, timeout=300)
    if kq.returncode != 0:
        pytest.skip("thiếu gói haven")
    dt = _j(FX_MR / "dac_ta.json") | {"trong_so": None, "hon_hop_da_sinh": True}
    r = C.chay_r_tham_chieu(_j(FX_MR / "man_bien.json"), dt, sav, tmp_path, his=None)
    fx = _j(FX_MR / "r_kq.json")
    assert r["hon_hop_laplace"] == fx["hon_hop_laplace"]
    for v, x in fx["hon_hop"]["he_so"].items():
        assert r["hon_hop"]["he_so"][v]["b"] == pytest.approx(x["b"], rel=1e-6)
        # p theo t bậc tự do phần dư (như DF_METHOD=RESIDUAL của SPSS) — p theo z lệch rõ ở p nhỏ
        assert r["hon_hop"]["he_so"][v]["p"] == pytest.approx(x["p"], rel=1e-4)
    assert r["hon_hop"]["df"] == r["hon_hop"]["n"] - 4 - 3  # 4 ngưỡng (5 mức) + 3 hệ số


def _bo_mo_rong() -> tuple[dict, dict, dict, dict]:
    import tempfile

    t = Path(tempfile.mkdtemp(prefix="ebm-fx-"))
    for f in FX_MR.glob("oms_*.xml"):
        (t / f.name).write_bytes(f.read_bytes())
    dt = _j(FX_MR / "dac_ta.json")
    man = _j(FX_MR / "man_bien.json") | {"sav": "x", "nguon_csv": str(FX_MR / "du_lieu_gia.csv")}
    return _j(FX_MR / "tom_ordinal.json"), {"bo_sung": C.doc_ket_qua_bo_sung(t, dt, man)}, dt, _j(FX_MR / "r_kq.json")


def _hh(dong: list[dict]) -> list[dict]:
    return [x for x in dong if x["muc"].startswith("Mô hình hỗn hợp")]


def test_doi_chieu_hon_hop_cung_phuong_phap_khop_va_bat_lech():
    tom, kq, dt, r = _bo_mo_rong()
    dong, tt = C.doi_chieu_bo_sung(tom, kq, dt, r=r)
    hh = _hh(dong)
    assert len(hh) == 4 and {x["trang_thai"] for x in hh} == {"khop"} and not any(x["ghi_chu"] for x in hh)
    assert any("clmm (Laplace)" in x and "KHÁC phương pháp" in x for x in tt)
    # số R lệch 1 % SE ⇒ «lệch» (không còn đường «lệch nhỏ» cho mô hình hỗn hợp)
    r2 = copy.deepcopy(r)
    x = r2["hon_hop"]["he_so"]["thoigian_cho"]
    x["b"] += 0.01 * x["se"]
    x["uoc_luong"] = __import__("math").exp(x["b"])
    tt2 = {y["muc"]: y["trang_thai"] for y in _hh(C.doi_chieu_bo_sung(tom, kq, dt, r=r2)[0])}
    assert [v for k, v in tt2.items() if "thoigian_cho" in k] == ["lech"]
    r3 = copy.deepcopy(r)
    r3["hon_hop"]["phuong_sai_ngau_nhien"] *= 1.05
    assert [y["trang_thai"] for y in _hh(C.doi_chieu_bo_sung(tom, kq, dt, r=r3)[0]) if "phương sai" in y["muc"]] == [
        "lech"]


def test_doi_chieu_hon_hop_tham_chieu_r_cu_la_khong_so_duoc():
    tom, kq, dt, r = _bo_mo_rong()
    cu = copy.deepcopy(r)
    cu["hon_hop"] = cu.pop("hon_hop_laplace")  # bản R cũ: hon_hop là clmm Laplace
    hh = _hh(C.doi_chieu_bo_sung(tom, kq, dt, r=cu)[0])
    assert len(hh) == 1 and hh[0]["trang_thai"] == "khong_so_duoc" and "RSPL" in hh[0]["ghi_chu"]


def test_canh_bao_cu_phap_khong_con_hua_lech_nho(tmp_path):
    man = _j(FX_MR / "man_bien.json") | {"sav": "THU-MR_khoa.sav", "nguon_csv": str(FX_MR / "du_lieu_gia.csv")}
    _vb, cb, _phu = C.cu_phap_bo_sung("THU-MR", man, _j(FX_MR / "dac_ta.json"), tmp_path, sav="x.sav")
    cb_hh = [x for x in cb if x.startswith("Mô hình hỗn hợp")]
    assert len(cb_hh) == 1 and "RSPL" in cb_hh[0] and "lệch nhỏ" not in cb_hh[0]


def _xml_genlinmixed() -> Path | None:
    for g in (Path("/Applications/IBM SPSS Statistics/IBM SPSS Statistics.app/Contents/bin/syntax_xml"),
              Path("C:/Program Files/IBM/SPSS Statistics/syntax_xml")):
        if (g / "GENLINMIXED.xml").is_file():
            return g / "GENLINMIXED.xml"
    return None


@pytest.mark.skipif(_xml_genlinmixed() is None, reason="máy không cài IBM SPSS Statistics")
def test_that_dac_ta_cu_phap_genlinmixed_khong_co_tuy_chon_laplace():
    """Căn cứ tài liệu SPSS: đặc tả cú pháp GENLINMIXED của bản cài không có từ khoá chọn phương pháp ước lượng
    (Laplace/cầu phương/METHOD) ⇒ không đối chiếu được Laplace ↔ Laplace; R mô phỏng RSPL là đường cùng phương pháp."""
    import re

    ten = set(re.findall(r'Name="([A-Z_]+)"', _xml_genlinmixed().read_text(encoding="utf-8", errors="replace")))
    assert "GENLINMIXED" in ten and "BUILD_OPTIONS" in ten
    assert not ten & {"LAPLACE", "QUADRATURE", "ADAPTIVE", "ESTIMATION", "METHOD", "NAGQ", "QUADPOINTS"}


def _co_spss() -> bool:
    try:
        return bool(C.tim_spss())
    except Exception:  # noqa: BLE001 — KhongDoDuoc: máy không cài SPSS
        return False


@pytest.mark.skipif(not _co_spss(), reason="máy không cài IBM SPSS Statistics")
def test_that_spss_genlinmixed_chay_song_trung_so_da_do():
    """Chạy GENLINMIXED nhị phân THẬT ⇒ đúng số đã ghi trong fixture (cùng số R RSPL ở test trên)."""
    sp = _j(FX_RSPL / "spss_genlinmixed.json")["nhi_phan"]
    with C.vung_tam() as t:
        t = Path(t)
        (t / "t.sps").write_text(
            "SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES MDISPLAY=TABLES.\n"
            f"GET DATA /TYPE=TXT /FILE={C.dd_spss(FX_RSPL / 'du_lieu_gia_cum.csv')} /DELIMITERS=\",\" /FIRSTCASE=2\n"
            "  /VARIABLES=record_id A8 g1 F8.0 nhom F8.0 tuoi F8.2 cum F8.0.\n"
            "COMPUTE yb = (g1 >= 4).\nFORMATS yb (F8.0).\n"
            "VARIABLE LEVEL yb (NOMINAL) /cum (NOMINAL) /nhom tuoi (SCALE).\n"
            f"OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE={C.dd_spss(t / 'o.xml')} /TAG='t'.\n"
            "GENLINMIXED /DATA_STRUCTURE SUBJECTS=cum /FIELDS TARGET=yb TRIALS=NONE OFFSET=NONE\n"
            "  /TARGET_OPTIONS REFERENCE=0 DISTRIBUTION=BINOMIAL LINK=LOGIT\n"
            "  /FIXED EFFECTS=nhom tuoi USE_INTERCEPT=TRUE\n"
            "  /RANDOM USE_INTERCEPT=TRUE SUBJECTS=cum COVARIANCE_TYPE=VARIANCE_COMPONENTS\n"
            "  /BUILD_OPTIONS TARGET_CATEGORY_ORDER=ASCENDING INPUTS_CATEGORY_ORDER=ASCENDING MAX_ITERATIONS=100\n"
            "    CONFIDENCE_LEVEL=95 DF_METHOD=RESIDUAL COVB=MODEL.\nOMSEND TAG='t'.\n", encoding="utf-8", newline="\n")
        ma, _out, err = C.chay_spss(C.tim_spss(), ["--cu-phap", str(t / "t.sps")], thu_muc=t, thoi_han=600)
        assert ma == 0, err[-800:]
        so = {}
        for b in C.phang_oxml(t / "o.xml"):
            for o in b["o"]:
                if o["cot"] in (["Coefficient"], ["Estimate"]) and o["hang"]:
                    so[o["hang"][0]] = o["so"]
    assert so["nhom"] == pytest.approx(sp["nhom"]["b"], rel=1e-9)
    assert so["tuoi"] == pytest.approx(sp["tuoi"]["b"], rel=1e-9)
    assert so["Var(Intercept)"] == pytest.approx(sp["phuong_sai"], rel=1e-8)


# ───────────────────────────── (3) đề tài đối chứng công khai ─────────────────────────────
import doi_chung_cong_khai as DC  # noqa: E402


def test_du_lieu_dung_dau_giay_phep_va_khu_dinh_danh(tmp_path):
    assert DC.sha256_tep(DC.TEP_DU_LIEU) == DC.NGUON["sha256"] and DC.NGUON["giay_phep"] == "CC0-1.0"
    df = DC.doc_du_lieu()
    assert len(df) == 202 and set(df.columns) == {"record_id", *DC.BIEN}
    assert int(df["qft_duong"].notna().sum()) == 192 and int(df["qft_duong"].sum()) == 105
    assert int(df["seo_bcg"].isna().sum()) == 1
    # không có cột định danh (tên, ngày sinh, điện thoại, địa chỉ) — chỉ mã thứ tự tuyển
    assert df["record_id"].str.fullmatch(r"QFT\d{3}").all()
    # tệp bị sửa một byte ⇒ từ chối
    sai = tmp_path / "x.xlsx"
    b = bytearray(DC.TEP_DU_LIEU.read_bytes())
    b[-1] ^= 1
    sai.write_bytes(bytes(b))
    with pytest.raises(DC.LoiDuLieu, match="SHA-256"):
        DC.doc_du_lieu(sai)


def test_bang_dem_bai_khac_tep_dung_hai_bien_va_trung_cac_bien_khac():
    """Bằng chứng nguyên nhân «dữ liệu sửa»: hai biến lệch bảng đếm Bảng 2; cường độ tiếp xúc trùng khi nhóm như bài."""
    df = DC.doc_du_lieu()
    assert DC.bang_dem(df, "tiep_xuc_trong_ho") == {0: (5, 21), 1: (100, 171)} != DC.BANG_DEM_BAI["tiep_xuc_trong_ho"]
    assert DC.bang_dem(df, "cung_nha") == {0: (14, 50), 1: (91, 142)} != DC.BANG_DEM_BAI["cung_nha"]
    assert DC.bang_dem(df, "cuong_do_cao") == {0: (24, 45), 1: (81, 147)}  # Bảng 2: 24/45 và 81/147
    assert DC.bang_dem(df, "quan_he_gia_dinh") == {0: (21, 58), 1: (84, 134)}  # Bảng 2: 21/58 và 84/134
    assert DC.bang_dem(df, "hut_thuoc") == {0: (85, 161), 1: (20, 31)}  # Bảng 2: 85/161 và 20/31


def test_doi_chieu_phan_loai_tai_lap_va_lech():
    he = {}
    for m in DC.CONG_BO:
        k = f"{m['loai']}:{m['bien']}"
        he[k] = ({"uoc": 105 / 192, "ci": [0.4762, 0.6157], "so_su_kien": 105, "n": 192} if m["loai"] == "ty_le"
                 else {"uoc": m["uoc"], "ci": list(m["ci"]), "p": m["p"]})
    # ô có nguyên nhân mà lại trùng ⇒ sổ nguyên nhân cũ ⇒ không đạt
    kq = DC.doi_chieu(he)
    assert kq["ket"] == "KHONG_DAT" and kq["dem"]["NGUYEN_NHAN_CU"] == 2 and kq["dem"]["TAI_LAP"] == 24
    for m in DC.CONG_BO:
        if DC.nguyen_nhan_lech(m):
            he[f"{m['loai']}:{m['bien']}"]["uoc"] = m["uoc"] * 1.2
    kq = DC.doi_chieu(he)
    assert kq["ket"] == "DAT" and kq["dem"] == {"TAI_LAP": 11, "LECH_CO_NGUYEN_NHAN": 15, "LECH": 0, "KHONG_CO_SO": 0,
                                                "NGUYEN_NHAN_CU": 0}
    # một ô phải tái lập lệch 0,01 ⇒ LECH; thiếu số ⇒ KHONG_CO_SO
    he["or_tho:hiv"]["uoc"] = 1.05
    del he["or_tho:bmi"]
    kq = DC.doi_chieu(he)
    assert kq["ket"] == "KHONG_DAT" and kq["dem"]["LECH"] == 1 and kq["dem"]["KHONG_CO_SO"] == 1
    assert DC.khop_lam_tron(1.0771, 1.08, 2) and DC.khop_lam_tron(3.0663, 3.07, 2) and not DC.khop_lam_tron(1.086, 1.08,
                                                                                                             2)


def _khung_dc(tmp_path, monkeypatch, study, tham_so):
    from tests.test_cau_noi_r_ty_le_20261122 import _khung

    return _khung(tmp_path, monkeypatch, study, DC.doc_du_lieu(), tham_so)


def _so_he_tu_tom_tat(d: Path) -> dict:
    return json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("bien", DC.YEU_TO)
def test_engine_g6_tai_lap_or_tho_cong_bo(bien, tmp_path, monkeypatch):
    """Mỗi yếu tố: run_stats_analysis (hồi quy logistic đơn biến) ⇒ OR, KTC, p làm tròn = Bảng 2 (trừ 2 ô dữ liệu
    sửa)."""
    d = _khung_dc(tmp_path, monkeypatch, "DC-QFT", ["--outcome", "qft_duong", "--group", bien,
                                                    "--outcome-type", "binary"])
    tom = _so_he_tu_tom_tat(d)
    r = next(x for x in tom["multivariate"]["results"] if x["variable"] == bien)
    m = next(x for x in DC.CONG_BO if x["loai"] == "or_tho" and x["bien"] == bien)
    trung = DC.khop_lam_tron(r["OR_adj"], m["uoc"], 2) and all(
        DC.khop_lam_tron(a, b, 2) for a, b in zip(r["CI_95"], m["ci"]))
    assert trung is (DC.nguyen_nhan_lech(m) is None), (bien, r, m)
    if trung:
        assert abs(r["p"] - m["p"]) <= 0.0005 + 1e-9 or (m["p"] == 0.001 and r["p"] < 0.0015), (r["p"], m["p"])


def test_engine_g6_tai_lap_ty_le_va_ktc_wilson(tmp_path, monkeypatch):
    d = _khung_dc(tmp_path, monkeypatch, "DC-QFT-TL", ["--ty-le", "qft_duong"])
    t = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))["ty_le"][0]
    m = DC.CONG_BO[0]
    assert (t["so_su_kien"], t["n"]) == (m["so_su_kien"], m["n"]), t
    assert all(DC.khop_lam_tron(a, b, 2) for a, b in zip(t["CI_95_wilson_doc_lap"], m["ci"])), t


def test_engine_g6_mo_hinh_bai_bi_rao_epv_va_firth_theo_sap(tmp_path, monkeypatch):
    """Mô hình 13 biến của bài: 87 biến cố nhóm hiếm / 13 biến = 6,7 < 10 ⇒ hệ KHÔNG chạy logistic thường (rào EPV),
    chạy Firth theo SAP §5 — nguyên nhân «chuan_epv» của các ô OR hiệu chỉnh là có thật, không phải ghi cho có."""
    d = _khung_dc(tmp_path, monkeypatch, "DC-QFT-DB", ["--outcome", "qft_duong", "--group", "cung_nha",
                                                       "--covariates",
                                                       ",".join(b for b in DC.DA_BIEN if b != "cung_nha"),
                                                       "--outcome-type", "binary", "--bien-co-hiem", "firth"])
    tom = _so_he_tu_tom_tat(d)
    mv = tom["multivariate"]
    assert mv["rao_epv"] and mv["so_bien_co"] == 87 and mv["so_tham_so"] == 13
    bch = tom["bien_co_hiem"]
    assert bch["phuong_phap"] == "firth" and {r["variable"] for r in bch["results"]} >= set(DC.DA_BIEN)


THAM_SO_DA_BIEN = ["--outcome", "qft_duong", "--group", "cung_nha", "--covariates",
                   ",".join(b for b in DC.DA_BIEN if b != "cung_nha"), "--outcome-type", "binary",
                   "--bien-co-hiem", "firth"]


@CAN_R
def test_that_r_khop_engine_tren_du_lieu_that(tmp_path, monkeypatch):
    """Cầu nối R (glm + logistf) trên CÙNG dữ liệu thật: đơn biến và mô hình Firth của SAP đều KHỚP engine."""
    from tests.test_cau_noi_r_ty_le_20261122 import _chay_cau_noi

    _khung_dc(tmp_path, monkeypatch, "DC-QFT-R1", ["--outcome", "qft_duong", "--group", "quan_he_gia_dinh",
                                                   "--outcome-type", "binary"])
    dc = _chay_cau_noi("DC-QFT-R1")
    assert dc["dem"]["lech"] == 0 and dc["dem"]["khop"] > 0, dc["dem"]
    _khung_dc(tmp_path / "b", monkeypatch, "DC-QFT-R2", THAM_SO_DA_BIEN)
    dc = _chay_cau_noi("DC-QFT-R2")
    fd = [x for x in dc["dong"] if "Firth" in x["muc"]]
    assert len(fd) == 13 and all(x["trang_thai"] == "khop" for x in fd), [(x["muc"], x["trang_thai"]) for x in fd]


def _tu_dien_spss() -> list[list[str]]:
    td = [["record_id", "text", "Mã", "", "", ""]]
    for b, nhan in DC.BIEN.items():
        td.append([b, "text", nhan[:40], "", "number", ""] if b in ("tuoi", "bmi") else
                  [b, "yesno", nhan[:40], "", "", ""])
    return td


@pytest.mark.skipif(not _co_spss(), reason="máy không cài IBM SPSS Statistics")
def test_that_spss_khop_engine_tren_du_lieu_that(tmp_path, monkeypatch):
    from tests.test_cau_noi_spss_ty_le_20261123 import _chay_spss, _khung_spss

    _khung_spss(tmp_path, monkeypatch, "DC-QFT-SP", DC.doc_du_lieu(),
                ["--outcome", "qft_duong", "--group", "lao_dong_chan_tay", "--covariates", "bmi,hut_thuoc",
                 "--outcome-type", "binary"], _tu_dien_spss())
    kc = _chay_spss("DC-QFT-SP", monkeypatch)
    assert kc["phan_mem"]["spss"]["trang_thai"] == "KHOP", kc["phan_mem"]["spss"]


def test_engine_g6_doi_chieu_toan_bo_cong_bo_dat(tmp_path, monkeypatch):
    """Toàn bộ 27 ước lượng công bố qua engine G6 thật: 11 tái lập đúng (tỷ lệ + 10 OR thô), 15 lệch đúng nguyên nhân đã
    chứng minh (2 OR thô dữ liệu sửa + 13 OR hiệu chỉnh do chuẩn EPV ⇒ Firth), 0 lệch không giải thích ⇒ DAT."""
    he: dict = {}
    d = _khung_dc(tmp_path / "tl", monkeypatch, "DC-TL", ["--ty-le", "qft_duong"])
    t = _so_he_tu_tom_tat(d)["ty_le"][0]
    he["ty_le:qft_duong"] = {"uoc": t["ty_le"], "ci": t["CI_95_wilson_doc_lap"], "so_su_kien": t["so_su_kien"],
                             "n": t["n"]}
    for i, b in enumerate(DC.YEU_TO):
        d = _khung_dc(tmp_path / f"db{i}", monkeypatch, f"DC-DB{i}", ["--outcome", "qft_duong", "--group", b,
                                                                     "--outcome-type", "binary"])
        r = next(x for x in _so_he_tu_tom_tat(d)["multivariate"]["results"] if x["variable"] == b)
        he[f"or_tho:{b}"] = {"uoc": r["OR_adj"], "ci": r["CI_95"], "p": r["p"]}
    d = _khung_dc(tmp_path / "mv", monkeypatch, "DC-MV", THAM_SO_DA_BIEN)
    for r in _so_he_tu_tom_tat(d)["bien_co_hiem"]["results"]:
        he[f"or_hieu_chinh:{r['variable']}"] = {"uoc": r["OR_adj"], "ci": r["CI_95"], "p": r.get("p")}
    kq = DC.doi_chieu(he)
    assert kq["ket"] == "DAT", [(x["bien"], x["loai"], x["trang_thai"]) for x in kq["dong"] if x["trang_thai"] in
                               ("LECH", "KHONG_CO_SO", "NGUYEN_NHAN_CU")]
    assert kq["dem"]["TAI_LAP"] == 11 and kq["dem"]["LECH_CO_NGUYEN_NHAN"] == 15, kq["dem"]


# ───── (3) lỗi hệ đề tài đối chứng phát hiện: cắt ngang «tỷ lệ + yếu tố liên quan» thiếu phương pháp biến cố hiếm ─────
import g4_quality_gate as G4Q  # noqa: E402
import run_g4_auto as G4  # noqa: E402


def _sap_cat_ngang(gia_thuyet_phu: str | None) -> str:
    return G4.generate("S", "Chủ đề", "cross_sectional", "cross_sectional", "STROBE", 199, 0.05, None, 0.65,
                       "PREVALENCE", "2026-11-24", hypothesis_type="descriptive_precision",
                       g3={"precision": 0.07, "prevalence": 0.65}, gia_thuyet_phu=gia_thuyet_phu)


def test_sap_cat_ngang_co_muc_tieu_phu_khai_bien_co_hiem():
    co = _sap_cat_ngang("Sống cùng nhà với ca nguồn liên quan với QFT-Plus dương tính")
    khong = _sap_cat_ngang(None)
    assert G4Q.co_muc_tieu_phu_phan_tich(co) and not G4Q.co_muc_tieu_phu_phan_tich(khong)
    assert G4Q.NHAN_BIEN_CO_HIEM in G4Q._section_body(co, "§5")
    assert G4Q.NHAN_BIEN_CO_HIEM not in G4Q._section_body(khong, "§5")
    assert G4Q.ap_dung_bien_co_hiem("cross_sectional", "Ước lượng tỷ lệ + KTC 95%", True)
    assert not G4Q.ap_dung_bien_co_hiem("cross_sectional", "Ước lượng tỷ lệ + KTC 95%", False)
    assert G4Q.ap_dung_bien_co_hiem("cohort", "Hồi quy Poisson")  # thiết kế khác: như cũ


def _auto04_cat_ngang(text: str, ky: bool = False) -> dict:
    bao = G4Q.evaluate_g4_quality(study="S", checkpoint={"design_code": "cross_sectional"}, artifact_text=text,
                                  g3_checkpoint={"design_code": "cross_sectional"}, g1_checkpoint={}, meta={},
                                  ledger_signed=ky, ledger_reason="", signature_scope=None, role_key_available=False,
                                  cross_gate_refs={})
    return next(c for c in bao["automatic_criteria"] if c["id"] == "G4-AUTO-04")


def test_cong_g4_auto04_cat_ngang_muc_tieu_phu_doi_khai_bien_co_hiem():
    goc = ("### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** Ước lượng tỷ lệ + KTC 95% (Wilson)\n\n### §5 PHÂN TÍCH ĐA BIẾN\n"
           "- EPV ≈ 7; VIF < 5\n{dong5}\n\n### §6 DỮ LIỆU THIẾU\n\n### §12 CỠ MẪU\n{dong12}\n")
    phu = f"- **{G4Q.NHAN_GIA_THUYET_PHU}, gate_params.G0.hypothesis_secondary):** yếu tố X liên quan Y  "
    firth = f"- **{G4Q.NHAN_BIEN_CO_HIEM}:** {G4Q.BIEN_CO_HIEM['firth'][0]}"
    assert _auto04_cat_ngang(goc.format(dong5="", dong12=phu))["status"] == "REVIEW"
    assert _auto04_cat_ngang(goc.format(dong5=firth, dong12=phu))["status"] == "PASS"
    assert _auto04_cat_ngang(goc.format(dong5="", dong12=""))["status"] == "PASS"  # mô tả thuần: không áp dụng
    ky = _auto04_cat_ngang(goc.format(dong5="", dong12=phu), ky=True)  # SAP đã ký trước luật: chỉ hiển thị
    assert ky["status"] == "PASS" and "chỉ hiển thị" in ky["evidence"]


# ───── (3) nối vào bộ giả lập trọn vòng + cổng CI ─────
def test_kich_ban_doi_chung_dang_ky_va_g5_doc_du_lieu_that():
    import gia_lap_bien_the_kho as BTK
    import gia_lap_doi_chung as GDC
    import kiem_gia_lap_16 as K16

    kb = BTK.kich_ban_kho()[GDC.MA]
    assert (GDC.MA, "cross_sectional_doi_chung") in BTK.danh_sach()
    assert K16.KICH_BAN["cross_sectional_doi_chung"] == GDC.MA
    assert kb["thiet_ke"] == "cross_sectional" and kb["bien_the"]["du_lieu_that"]
    assert kb["pi"]["G0"]["hypothesis_secondary"] and kb["ho_so_tron_vong"]["G2"]["icf_waiver_requested"]
    # nguồn đo gốc có «phỏng vấn» ⇒ hệ không tự suy công cụ; chủ nhiệm khai ở G10 (G10-AUTO-09 chặn ô trống)
    assert "Phiếu trích dữ liệu" in kb["ho_so_tron_vong"]["dac_ta_G10"]["instrument"]["name"]
    hang = GDC.hang_du_lieu_that(kb)
    assert len(hang) == 202 and set(hang[0]) == {b[0] for b in kb["bien_so"]["bo_bien"]}
    assert sum(r["qft_duong"] is None for r in hang) == 10 and sum(r["seo_bcg"] is None for r in hang) == 1
    ids = {pt["id"] for pt in kb["ho_so_tron_vong"]["g6"]}
    assert {"MT1_ty_le", "MT2_da_bien", "DN_rut_gon"} <= ids and {f"DB_{b}" for b in DC.YEU_TO} <= ids


def test_kiem_gia_lap_16_chan_khi_doi_chung_khong_dat(tmp_path):
    import kiem_gia_lap_16 as K16

    goc = {"cong": {"G10": {"trang_thai": "PASS_G10_LOCKED"}}, "so_o_loi_may": 0,
           "du_lieu": {"de_cuong_nop": {"ma": 0}, "g6": {"khong_tu_dong": True}}}
    p = tmp_path / "x.json"
    for dch, co_loi in (({"ket": "DAT"}, False), ({"ket": "KHONG_AP_DUNG"}, False),
                        ({"ket": "KHONG_DAT", "dong": [{"loai": "or_tho", "bien": "hiv", "trang_thai": "LECH"}]},
                         True), ({"ket": "CHUA_DO", "ly_do": "chưa có G6"}, True)):
        p.write_text(json.dumps({**goc, "doi_chung": dch}), encoding="utf-8", newline="\n")
        loi = [x for x in K16.kiem_mot(p) if x.startswith("đối chứng")]
        assert bool(loi) is co_loi, (dch, loi)
        if co_loi and dch["ket"] == "KHONG_DAT":
            assert "or_tho:hiv LECH" in loi[0]


def test_tron_vong_kiem_doi_chung_doc_dung_tep_g6(tmp_path):
    import gia_lap_bien_the_kho as BTK
    import gia_lap_doi_chung as GDC
    import gia_lap_tron_vong as GTV

    tv = GTV.TronVong.__new__(GTV.TronVong)
    tv.kb, tv.out = BTK.kich_ban_kho()[GDC.MA], tmp_path
    assert tv.kiem_doi_chung()["ket"] == "CHUA_DO"
    tl = DC.CONG_BO[0]
    (tmp_path / "G6_analysis_summary.json").write_text(json.dumps({"ty_le": [
        {"ty_le": 105 / 192, "CI_95_wilson_doc_lap": [0.4762, 0.6157], "so_su_kien": tl["so_su_kien"], "n": tl["n"]}]}),
        encoding="utf-8", newline="\n")
    for m in DC.CONG_BO[1:]:
        lech = 1.3 if DC.nguyen_nhan_lech(m) else 1.0
        r = {"variable": m["bien"], "OR_adj": m["uoc"] * lech, "CI_95": list(m["ci"]), "p": m["p"]}
        if m["loai"] == "or_tho":
            (tmp_path / f"G6_DB_{m['bien']}_analysis_summary.json").write_text(
                json.dumps({"multivariate": {"results": [r]}}), encoding="utf-8", newline="\n")
        else:
            p = tmp_path / "G6_MT2_da_bien_analysis_summary.json"
            cu = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"bien_co_hiem": {
                "phuong_phap": "firth", "results": []}}
            cu["bien_co_hiem"]["results"].append(r)
            p.write_text(json.dumps(cu), encoding="utf-8", newline="\n")
    kq = tv.kiem_doi_chung()
    assert kq["ket"] == "DAT" and kq["dem"]["TAI_LAP"] == 11 and kq["phuong_phap_da_bien"] == "firth", kq["dem"]
    (tmp_path / "G6_DB_hiv_analysis_summary.json").unlink()
    assert tv.kiem_doi_chung()["dem"]["KHONG_CO_SO"] == 1
    tv.kb = BTK.kich_ban_kho()["benh_chung_ghep_cap"]
    assert tv.kiem_doi_chung() == {"ket": "KHONG_AP_DUNG"}


# ───── lỗi hệ lộ ra khi chạy đề tài đối chứng tới đề cương nộp ─────
def test_sai_lech_kich_ban_doi_chung_khong_hua_phan_tich_khong_co_trong_sap():
    """Biện pháp G1 «Phân tích toàn bộ bộ dữ liệu» từng bị đối chiếu G1↔SAP hiểu là hứa một phân tích (SL-05 «[CẦN §]»)
    trong khi đó là biện pháp ở khâu chọn mẫu. Biện pháp chỉ mang từ khoá phân tích khi SAP có mục tương ứng."""
    import doi_chieu_sai_lech_sap as DS
    import gia_lap_bien_the_kho as BTK
    import gia_lap_doi_chung as GDC

    g1 = BTK.kich_ban_kho()[GDC.MA]["pi"]["G1"]
    khung = {r["sai_lech"]: r["can_phan_tich"] for r in DS.khung({"gate_params": {"G1": g1}})}
    assert list(khung.values()) == ["khong", "khong", "co"], khung
    assert "Firth" in g1["bias_controls"][2]["bien_phap"] and "SAP §5" in g1["bias_controls"][2]["bien_phap"]


def test_de_cuong_cat_ngang_co_bien_phoi_nhiem_dat_strobe_8(tmp_path):
    """Cắt ngang có mục tiêu phân tích khai biến vai «phoi_nhiem» ⇒ bảng biến in «Phơi nhiễm/nhóm so sánh», STROBE 8
    đòi tương đồng cách đo giữa các nhóm. Bộ sinh dựng câu từ CHÍNH biến đó; trước 24/11 chỉ rct/cohort/bệnh–chứng
    có câu."""
    sys.path.insert(0, str(GOC / "tests"))
    import test_sinh_de_cuong_dat_k17_20261121 as TK

    van = TK._van(tmp_path, "cross_sectional",
                  g1={"critical_to_quality": "Dấu SHA-256 của tệp gốc khớp kho dữ liệu", "monitoring_plan": None})
    assert TK._thieu(van, "cross_sectional") == {}
    assert ("- Đo lường như nhau giữa các nhóm so sánh theo nhóm: mọi người tham gia được thu thập bằng cùng một phiếu "
            "(Phụ lục C), cùng định nghĩa biến (Phụ lục D) và theo cùng lịch thu thập.") in van.splitlines()


def test_k13_et_al_trong_tieu_de_khong_phai_tac_gia_cat_cut(tmp_path):
    """K13 xét «et al.» ở PHẦN TÁC GIẢ: tiêu đề «Erratum for Chee et al., …» (bài 4 tác giả ghi đủ) từng bị báo «ghi
    đủ, không et al.»; danh sách 4 tác giả thật sự thêm «et al.» vẫn bị bắt."""
    sys.path.insert(0, str(GOC / "tests"))
    import kiem_de_cuong_nop_hoi_dong as KDN
    from test_tong_quan_k12_k13_20261120 import _bien_nhan, _md

    meta = {"status": "resolved", "year": "2026", "n_authors": 4, "volume": "14", "journal_abbr": "Microbiol Spectr",
            "authors_6": ["Chee CB", "Kyi-Win K", "Tan S", "Wang YT"]}
    d = _bien_nhan(tmp_path, {"222": meta})
    dung = ("1. Chee CB, Kyi-Win K, Tan S, Wang YT. Erratum for Chee et al., \"QuantiFERON-TB Gold Plus CD8+ T cell "
            "responses\". Microbiol Spectr. 2026;14(10). PMID: 222.")
    assert KDN.loi_k13(d, _md("Câu [1].", dung)) == []
    sai = dung.replace("Wang YT. Erratum", "Wang YT, et al. Erratum")
    assert any("ghi đủ, không «et al.»" in x for x in KDN.loi_k13(d, _md("Câu [1].", sai)))


def test_sang_loc_gia_lap_xep_thong_bao_bien_tap_khong_lien_quan():
    """Người sàng lọc (giả lập) không dùng thông báo đính chính/rút bài làm bằng chứng, dù tiêu đề chạm đủ khối."""
    import gia_lap_van_ban_tac_tu as VB

    khoi = [["quantiferon"], ["contact"]]
    tieu_de = "Erratum for Chee et al., \"QuantiFERON-TB Gold Plus CD8+ T cell responses in contacts\""
    assert VB.xep_lien_quan(tieu_de, khoi) == ("khong", [])
    assert VB._ly_do_khong(khoi, [], tieu_de) == VB.LY_DO_THONG_BAO
    assert VB._tom_tat({"title": tieu_de}, "khong", khoi, []).endswith(VB.LY_DO_THONG_BAO)
    assert VB.xep_lien_quan("QuantiFERON-TB Gold Plus responses in contacts", khoi)[0] == "truc_tiep"
    for t in ("Correction to: QuantiFERON in contacts", "Retraction note: QuantiFERON in contacts",
              "Expression of concern: QuantiFERON in contacts", "Corrigendum: QuantiFERON contact study"):
        assert VB.xep_lien_quan(t, khoi)[0] == "khong", t
    # khối rỗng (không tách được khái niệm) không phải thông báo — giữ lý do cũ
    assert VB._ly_do_khong([], [], "QuantiFERON in contacts") != VB.LY_DO_THONG_BAO


def test_co_mau_mot_ty_le_in_nguon_cua_p(tmp_path):
    """STROBE 10 «tham số có nguồn»: p ≠ 0,5 lấy từ y văn ⇒ mục cỡ mẫu in nguồn đã chốt ở G3 (prevalence_source); p =
    0,5 giữ lý do «cỡ mẫu lớn nhất»."""
    sys.path.insert(0, str(GOC / "tests"))
    import sinh_de_cuong_nop_hoi_dong as SDC
    import test_sinh_de_cuong_dat_k17_20261121 as TK

    n = TK._nguon(tmp_path, "cross_sectional")
    n.g3cp = {"effect_type": "PREVALENCE", "prevalence": 0.65, "precision": 0.07, "n_total": 179}
    n.g3 = {**n.g3, "prevalence_source": "PMID: 25372043 (Biraro 2014) — 65% ở người tiếp xúc hộ gia đình"}
    n.td.so = lambda pmid: 7 if str(pmid) == "25372043" else 0
    van = " ".join(SDC.doan_co_mau(n))
    assert "tỷ lệ ước tính p = 0,65 theo Biraro 2014 [7] và sai số" in van, van
    n.g3 = {**n.g3, "prevalence_source": "Giả định từ báo cáo chương trình chống lao"}
    assert "p = 0,65 (giả định từ báo cáo chương trình chống lao) và" in " ".join(SDC.doan_co_mau(n))


def test_kich_ban_doi_chung_khong_co_cau_nhan_qua_cho_du_lieu_cat_ngang():
    """STROBE 20 (cắt ngang): mọi văn bản của kịch bản đi vào bản thảo/đề cương không khẳng định nhân quả — câu cơ chế
    «… làm tăng phơi nhiễm …» từng làm G10-AUTO-09 chặn gói (bản thảo thiếu STROBE 20)."""
    import re

    import gia_lap_bien_the_kho as BTK
    import gia_lap_doi_chung as GDC
    import tieu_chi_ban_thao as TCB

    kb = BTK.kich_ban_kho()[GDC.MA]
    van = json.dumps(kb, ensure_ascii=False)
    assert not re.search(TCB.CAU_NHAN_QUA, van), re.search(TCB.CAU_NHAN_QUA, van)
    assert re.search(TCB.GIOI_HAN_NHAN_QUA, van)  # giới hạn suy nhân quả có nêu
