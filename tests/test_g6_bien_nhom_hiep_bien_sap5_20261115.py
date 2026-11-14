# -*- coding: utf-8 -*-
"""Khuôn G6 theo biến phân nhóm thật + hiệp biến SAP §5 (giả lập RCT lần 2 ngày 14/11/2026, N6) và định dạng p (N15).

N6: dictionary G5 của RCT ghi biến nhánh `nhom` dưới mục «Ngẫu nhiên hoá» ⇒ khuôn từng rơi về tên dự phòng `exposure`;
    SAP §5 khoá «nhom + tuoi, gioi, ha_tt_nen, so_thuoc_nen» nhưng khuôn chỉ dò được `tuoi, gioi` từ từ khoá.
N15: bảng độ nhạy/nhóm con của sensitivity_analysis.py ghi `round(pv, 3)` ⇒ «0.0» cho p rất nhỏ.
Dữ liệu mô phỏng, không PII. Không ký cổng, không đụng exports/ thật (mọi đề tài dựng trong tmp_path).
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import run_g5_auto as G5  # noqa: E402
import run_g6_auto as G6  # noqa: E402

STUDY = "G6N6-RCT"


def _hang(var: str, muc: str, kieu: str = "text", nhan: str = "", lua_chon: str = "", xac_thuc: str = "") -> tuple:
    return (var, "phieu", muc, kieu, nhan or var, lua_chon, "", xac_thuc, "", "", "y", "")


#: Dictionary G5 của RCT giả lập lần 2 (rút gọn): biến nhánh dưới «Ngẫu nhiên hoá», không có mục «Phơi nhiễm».
_HANG_RCT = [
    _hang("record_id", "Hành chính", nhan="Mã nghiên cứu"),
    _hang("ngay_nn", "Ngẫu nhiên hoá", kieu="text", nhan="Ngày ngẫu nhiên hoá", xac_thuc="date_dmy"),
    _hang("tang_nn", "", kieu="radio", nhan="Tầng ngẫu nhiên hoá", lua_chon="1, Tầng A | 2, Tầng B"),
    _hang("nhom", "", kieu="radio", nhan="Nhánh được phân bổ", lua_chon="0, Chăm sóc thường quy | 1, Tin nhắn SMS"),
    _hang("tuoi", "Đặc điểm nền", nhan="Tuổi (năm)", xac_thuc="integer"),
    _hang("gioi", "", kieu="radio", nhan="Giới", lua_chon="0, Nam | 1, Nữ"),
    _hang("ha_tt_nen", "", nhan="HA tâm thu nền (mmHg)", xac_thuc="integer"),
    _hang("so_thuoc_nen", "", nhan="Số thuốc hạ áp đang dùng lúc nền", xac_thuc="integer"),
    _hang("dtd", "", kieu="radio", nhan="Đái tháo đường kèm theo", lua_chon="0, Không | 1, Có"),
    _hang("kiem_soat_t6", "Kết cục chính", kieu="radio", nhan="Đạt kiểm soát HA tháng 6",
          lua_chon="0, Không | 1, Có"),
]

_SAP5_RCT = ("- **Biến độc lập đưa vào:** nhom + tuoi, gioi, ha_tt_nen, so_thuoc_nen (yếu tố tiên lượng mạnh, chọn "
             "trước). EPV ước tính ≈ 85 biến cố / 5 tham số ≈ 17 (>10); kiểm VIF < 5  \n"
             "- **Phương pháp chọn biến:** Đưa vào toàn bộ (không stepwise)  \n")


def _sap(sap5: str = _SAP5_RCT) -> str:
    return ("# SAP\n\n### §2 KẾT CỤC\n\n- **Kết cục chính:** Đạt kiểm soát HA tháng 6 (`kiem_soat_t6`)  \n\n"
            "### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** hiệu số tỷ lệ (RD) + KTC 95%; kèm RR (Poisson robust)  \n\n"
            f"### §5 PHÂN TÍCH ĐA BIẾN\n\n{sap5}\n"
            "### §6 DỮ LIỆU THIẾU\n\n- **Chiến lược:** Multiple Imputation (MI, m=20, method=pmm)  \n\n"
            "### §7 PHÂN TÍCH NHÓM NHỎ\n\nKhông có.\n\n"
            "### §10 PHẦN MỀM + SEED\n\n- **Random seed:** 20261115  \n\n"
            "### §12 ALPHA + POWER\n\n- **Alpha (two-sided):** 0.05  \n")


def _do(tmp_path: Path, rows: list) -> dict:
    csv_path, _ = G5.generate_csv("T", tmp_path, rows)
    return G6.detect_variables_from_redcap(csv_path)


def _ten_goc(v: dict) -> dict:
    return {str(x).lower(): str(x) for x in v["all_vars"]}


# ── (1) Dò biến phân nhóm từ mục «Ngẫu nhiên hoá» của dictionary ──────────────────────────────────────────────────────

def test_rct_bien_nhanh_duoi_muc_ngau_nhien_hoa_khong_roi_ve_exposure(tmp_path):
    v = _do(tmp_path, _HANG_RCT)
    assert v["exposure"] == "nhom", v["detection_log"]
    assert "exposure" not in v["covariates"] and "nhom" not in v["covariates"]
    assert any("ngẫu nhiên hoá/phân bổ" in d for d in v["detection_log"])


def test_muc_ngau_nhien_chi_co_bien_tang_thi_lay_bien_chon_mot_dau_tien_khong_lay_ngay(tmp_path):
    hang = [h for h in _HANG_RCT if h[0] != "nhom"]
    assert _do(tmp_path, hang)["exposure"] == "tang_nn", "ngày ngẫu nhiên hoá (text) không bao giờ là biến nhóm"


def test_tieu_de_nhac_ngau_nhien_hoa_o_giua_khong_phai_muc_phan_nhom(tmp_path):
    hang = [_hang("record_id", "Hành chính"),
            _hang("nhom_mau", "Đặc điểm nền (trước ngẫu nhiên hoá)", kieu="radio", lua_chon="1, A | 2, B"),
            _hang("y", "Kết cục chính", kieu="radio", lua_chon="0, Không | 1, Có")]
    assert _do(tmp_path, hang)["exposure"] == "exposure", "mục khớp theo ĐẦU tiêu đề, không khớp chứa"


def test_muc_phoi_nhiem_van_thang_muc_ngau_nhien(tmp_path):
    hang = _HANG_RCT[:1] + [_hang("can_thiep", "Phơi nhiễm/Can thiệp", kieu="radio", lua_chon="0, Không | 1, Có")] \
        + _HANG_RCT[1:]
    assert _do(tmp_path, hang)["exposure"] == "can_thiep"


# ── (2) Bộ đọc SAP §5 ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_sap5_dang_nhom_cong_danh_sach(tmp_path):
    v = _do(tmp_path, _HANG_RCT)
    dt = G6.doc_bien_sap_5(_sap(), _ten_goc(v))
    assert dt["bien_phan_nhom"] == "nhom"
    assert dt["hiep_bien"] == ["tuoi", "gioi", "ha_tt_nen", "so_thuoc_nen"] and dt["mo_ho"] == []


def test_sap5_forced_in_backtick_bo_bien_trong_ngoac_va_dong_khong_hieu_chinh(tmp_path):
    """Khuôn §5 kiểu đề tài cắt ngang: exposure riêng dòng, forced-in trong backtick, biến BỊ LOẠI chỉ nêu trong ngoặc,
    dòng «KHÔNG hiệu chỉnh» liệt kê biến trung gian — không biến nào trong hai loại sau lọt vào hiệp biến."""
    ten = {t: t for t in ("thoigian", "tuoi", "gioi", "bhyt", "chuyenkhoa", "trung_gian", "co_cls")}
    sap5 = ("- **Exposure chính:** `thoigian` (phút; nguồn ưu tiên HIS).  \n"
            "- **Covariates KHÔNG đưa vào (xảy ra sau phơi nhiễm):** `co_cls`.  \n"
            "- **Biến điều chỉnh bắt buộc (forced-in):** `tuoi` (giữ liên tục), `gioi` và `bhyt` *(PI xác nhận: "
            "`chuyenkhoa` loại khỏi tập forced-in)*.  \n"
            "- **Biến trung gian — KHÔNG hiệu chỉnh trong mô hình chính:** `trung_gian`, `co_cls`.  \n")
    dt = G6.doc_bien_sap_5(_sap(sap5), ten)
    assert dt["bien_phan_nhom"] == "thoigian"
    assert dt["hiep_bien"] == ["tuoi", "gioi", "bhyt"], dt


def test_sap5_van_xuoi_thi_khong_doan_ma_ghi_mo_ho(tmp_path):
    v = _do(tmp_path, _HANG_RCT)
    sap5 = "- **Biến độc lập đưa vào:** 5 biến đã chốt ở G0 — tuổi, giới, huyết áp nền, `so_thuoc_nen`.  \n"
    dt = G6.doc_bien_sap_5(_sap(sap5), _ten_goc(v))
    assert dt["hiep_bien"] is None and "giới" in dt["mo_ho"]
    truoc = list(v["covariates"])
    G6.ap_bien_sap_5(v, _sap(sap5), _ten_goc(v))
    assert v["covariates"] == truoc, "SAP văn xuôi ⇒ giữ biến dò từ dictionary"
    assert any("KHÔNG phải tên biến" in d for d in v["detection_log"])


def test_sap5_chua_dien_thi_khong_doi_gi(tmp_path):
    v = _do(tmp_path, _HANG_RCT)
    sap5 = "- **Biến độc lập đưa vào:** [CẦN THỐNG KÊ VIÊN ĐIỀN — ví dụ: nhom + tuoi, gioi]  \n"
    dt = G6.doc_bien_sap_5(_sap(sap5), _ten_goc(v))
    assert dt == {"bien_phan_nhom": None, "hiep_bien": None, "mo_ho": [], "nguon": None}, \
        "câu ví dụ BÊN TRONG nhãn chưa điền không được đọc thành danh sách đã chốt"


# ── (3) Áp vào biến của khuôn ─────────────────────────────────────────────────────────────────────────────────────────

def test_ap_sap5_thay_hiep_bien_do_tu_khoa(tmp_path):
    v = _do(tmp_path, _HANG_RCT)
    v["outcome"] = "kiem_soat_t6"
    assert set(v["covariates"]) != {"tuoi", "gioi", "ha_tt_nen", "so_thuoc_nen"}, "tiền đề: từ khoá dò thiếu/khác"
    G6.ap_bien_sap_5(v, _sap(), _ten_goc(v))
    assert v["exposure"] == "nhom" and v["covariates"] == ["tuoi", "gioi", "ha_tt_nen", "so_thuoc_nen"]


def test_ap_sap5_cung_tap_bien_giu_thu_tu_cu(tmp_path):
    v = {"exposure": "nhom", "outcome": "y", "covariates": ["gioi", "tuoi"], "cluster_col": None,
         "detection_log": []}
    G6.ap_bien_sap_5(v, _sap("- **Biến độc lập đưa vào:** nhom + tuoi, gioi  \n"),
                     {"nhom": "nhom", "y": "y", "tuoi": "tuoi", "gioi": "gioi"})
    assert v["covariates"] == ["gioi", "tuoi"] and "KHỚP SAP §5" in v["detection_log"][-1]


def test_ap_sap5_bien_cum_khong_dong_thoi_la_hiep_bien(tmp_path):
    v = {"exposure": "nhom", "outcome": "y", "covariates": ["tuoi"], "cluster_col": "ban_kham", "detection_log": []}
    G6.ap_bien_sap_5(v, _sap("- **Biến độc lập đưa vào:** nhom + tuoi, gioi, ban_kham  \n"),
                     {t: t for t in ("nhom", "y", "tuoi", "gioi", "ban_kham")})
    assert v["covariates"] == ["tuoi", "gioi"]
    assert any("biến CỤM" in d for d in v["detection_log"])


def test_ap_sap5_chi_neu_bien_nhom_thi_khong_ghi_de_bang_danh_sach_rong(tmp_path):
    v = {"exposure": "nhom", "outcome": "y", "covariates": ["tuoi"], "cluster_col": None, "detection_log": []}
    G6.ap_bien_sap_5(v, _sap("- **Biến độc lập đưa vào:** nhom  \n"), {t: t for t in ("nhom", "y", "tuoi")})
    assert v["covariates"] == ["tuoi"], "danh sách rỗng ⇒ khuôn rơi về «age + sex + bmi» — không được ghi đè"


# ── (4) Đầu–cuối: run_g6_auto.main() trên đề tài RCT dựng tay ⇒ script dùng biến THẬT + hiệp biến SAP §5───────────────

def _de_tai_rct(tmp_path: Path, monkeypatch) -> Path:
    goc = tmp_path / "goc"
    out = goc / "exports" / STUDY
    out.mkdir(parents=True)
    (out / "G1_checkpoint.json").write_text(json.dumps({"design_code": "rct"}), encoding="utf-8", newline="\n")
    (out / "G3_checkpoint.json").write_text(json.dumps({"effect_type": "RR", "n_adjusted": 218, "alpha": 0.05}),
                                            encoding="utf-8", newline="\n")
    (out / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(_sap(), encoding="utf-8", newline="\n")
    G5.generate_csv(STUDY, out, _HANG_RCT)
    CS.xoa_dem()
    monkeypatch.setattr(G6, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g6_auto.py", "--study", STUDY])
    with contextlib.redirect_stdout(io.StringIO()):
        G6.main()
    CS.xoa_dem()
    return out


def test_dau_cuoi_khuon_rct_dung_nhom_va_hiep_bien_sap5(tmp_path, monkeypatch):
    out = _de_tai_rct(tmp_path, monkeypatch)
    cp = json.loads((out / "G6_checkpoint.json").read_text(encoding="utf-8"))
    vd = cp["variables_detected"]
    assert vd["exposure"] == "nhom" and vd["outcome"] == "kiem_soat_t6"
    assert vd["covariates"] == ["tuoi", "gioi", "ha_tt_nen", "so_thuoc_nen"]
    assert cp["bien_sap_5"]["hiep_bien"] == ["tuoi", "gioi", "ha_tt_nen", "so_thuoc_nen"]
    r03 = (out / "scripts" / "03_analysis.R").read_text(encoding="utf-8")
    assert "kiem_soat_t6 ~ nhom + tuoi + gioi + ha_tt_nen + so_thuoc_nen" in r03
    assert not re.search(r"\bexposure\b", r03), "không còn tên dự phòng `exposure` trong công thức"
    cli = (out / "scripts" / "run_analysis_cli.py").read_text(encoding="utf-8")
    assert 'default="tuoi,gioi,ha_tt_nen,so_thuoc_nen"' in cli
    a7 = (out / f"G6_A7_ANALYSIS_SCRIPTS_{STUDY}.md").read_text(encoding="utf-8")
    assert "Hiệp biến THEO SAP §5" in a7 and "Biến phân nhóm (từ Section Header" in a7


def test_dau_cuoi_cong_thuc_khuon_khop_du_lieu_va_uoc_luong_rr_cai_san_nam_trong_ktc(tmp_path, monkeypatch):
    """Dữ liệu mô phỏng có hiệu quả CÀI SẴN (RR thật 1,5 sau hiệu chỉnh HA nền): công thức RR do khuôn sinh chạy được
    trên bảng có cột THẬT của dictionary (bản cũ gọi cột `exposure` không tồn tại) và KTC 95% (Poisson + HC0, đúng
    Zou 2004) chứa giá trị cài. Thiếu `ha_tt_nen` (bản cũ chỉ hiệu chỉnh tuoi, gioi) thì RR lệch khỏi giá trị cài."""
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    smf = pytest.importorskip("statsmodels.formula.api")
    sm = pytest.importorskip("statsmodels.api")

    out = _de_tai_rct(tmp_path, monkeypatch)
    r03 = (out / "scripts" / "03_analysis.R").read_text(encoding="utf-8")
    dong = next(d for d in r03.splitlines() if "fit_rr <- glm(" in d)
    cong_thuc = re.search(r"glm\(([^,]+),", dong).group(1).strip()

    rng = np.random.default_rng(20261115)
    n = 4000
    nhom = rng.integers(0, 2, n)
    ha = rng.normal(150, 12, n)
    # HA nền mất cân bằng giữa hai nhánh (ngẫu nhiên hoá theo tầng HA lệch) ⇒ thiếu ha_tt_nen thì RR bị nhiễu.
    ha = ha + 8 * nhom
    p = np.clip(0.30 * 1.5 ** nhom * np.exp(-0.03 * (ha - 150)), 0, 0.98)
    df = pd.DataFrame({"nhom": nhom, "tuoi": rng.normal(60, 10, n).round(), "gioi": rng.integers(0, 2, n),
                       "ha_tt_nen": ha.round(), "so_thuoc_nen": rng.integers(1, 5, n),
                       "kiem_soat_t6": rng.binomial(1, p)})
    thieu = [t.strip() for t in re.split(r"[~+]", cong_thuc) if t.strip() not in df.columns]
    assert not thieu, f"công thức khuôn gọi cột không có trong dữ liệu khoá: {thieu}"

    fit = smf.glm(cong_thuc, data=df, family=sm.families.Poisson()).fit(cov_type="HC0")
    lo, hi = np.exp(fit.conf_int().loc["nhom"])
    assert lo < 1.5 < hi, (float(np.exp(fit.params["nhom"])), lo, hi)
    cu = smf.glm("kiem_soat_t6 ~ nhom + tuoi + gioi", data=df, family=sm.families.Poisson()).fit(cov_type="HC0")
    lo_cu, hi_cu = np.exp(cu.conf_int().loc["nhom"])
    assert not (lo_cu < 1.5 < hi_cu), "tiền đề phép thử: bỏ ha_tt_nen (hiệp biến cũ) thì KTC không chứa RR cài"


# ── (5) N15: cột p của bảng độ nhạy/nhóm con không bao giờ là «0.0»────────────────────────────────────────────────────

@pytest.mark.parametrize("thiet_ke", ["rct", "cohort", "case_control"])
def test_bang_do_nhay_ghi_p_bang_fmt_pval(thiet_ke):
    v = {"exposure": "nhom", "outcome": "y", "time_col": "t", "covariates": ["tuoi"], "all_vars": [],
         "detection_log": []}
    code = G6.make_sensitivity_analysis(v, "S", thiet_ke, "HR" if thiet_ke != "case_control" else "OR")
    dong_p = [d for d in code.splitlines() if "_rows.append(dict(" in d]
    assert dong_p, "khuôn phải có bảng độ nhạy/nhóm con"
    assert all("p=fmt_pval(pv)" in d for d in dong_p), [d for d in dong_p if "p=fmt_pval(pv)" not in d][:2]
    assert "round(pv" not in code
    ns: dict = {}
    exec(re.search(r"^def fmt_pval\(p\):\n(?:    .*\n)+", code, re.M).group(0), ns)
    assert ns["fmt_pval"](1e-9) == "<0.001" and ns["fmt_pval"](0.0421) == "0.042"
