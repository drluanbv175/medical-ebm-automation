"""Biểu đồ phân tích gộp + SROC (bác sĩ 21/11/2026: «không chỉ riêng biểu đồ SROC mà phải thực hiện được tất cả biểu đồ
một cách chi tiết và chính xác nhất»).

Giá trị chuẩn lấy từ R 4.6 + metafor 5.0.1 + metadat trên hai bộ dữ liệu công khai:
  - dat.bcg (13 thử nghiệm vắc-xin BCG; Colditz 1994) — rma REML/DL/knha, regtest, trimfill;
  - dat.kearon1998 (siêu âm chẩn đoán huyết khối tĩnh mạch sâu; Kearon 1998, PMID 9537941) — rma.mv hai biến
    (struct UN, REML) cho cả 30 nghiên cứu và từng nhóm có/không triệu chứng.
Test sống với R (đánh dấu skip khi máy không có Rscript) chạy lại chính đoạn R mà `--kiem-cheo-r` dùng.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bieu_do_chung as BC  # noqa: E402
import bieu_do_gop as G  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"
BCG = FX / "bcg_dat_metadat.csv"
KEARON = FX / "kearon1998_metadat.csv"

# escalc(measure="RR", ai=tpos, bi=tneg, ci=cpos, di=cneg, data=dat.bcg)
BCG_YI = [-0.8893113339, -1.5853886572, -1.3480731483, -1.4415511900, -0.2175473222, -0.7861155858, -1.6208982236,
          0.0119523335, -0.4694176487, -1.3713448035, -0.3393588283, 0.4459134006, -0.0173139482]
BCG_VI = [0.3255847650, 0.1945811214, 0.4153679654, 0.0200100319, 0.0512101722, 0.0069056185, 0.2230172476,
          0.0039615793, 0.0564342105, 0.0730247936, 0.0124122140, 0.5325058452, 0.0714046597]
# rma.mv hai biến (mu1, mu2, se1, se2, tau2_1, tau2_2, rho, cov12)
KEARON_R = {
    None: (1.1097400670, 3.0671954200, 0.2543511153, 0.2250670409, 1.6839407775, 0.9338873611, -0.2790793664,
           -0.0117084526),
    "Có triệu chứng": (2.1100423275, 3.0089819580, 0.2214188306, 0.3504894498, 0.4881578093, 1.2538358660,
                       -0.2566378180, -0.0126945597),
    "Không triệu chứng": (-0.0512946841, 3.1534144425, 0.2088851382, 0.2819698772, 0.4523563079, 0.6443760253,
                          -0.4602207456, -0.0179542699),
}


def _gan(a: float, b: float, tuong_doi: float = 1e-6, tuyet_doi: float = 1e-7) -> bool:
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def _bcg_ds():
    return G.chuan_bi_gop(G.doc_csv(BCG), "RR")[0]


def _kearon_ds(nhom=None):
    ds = G.chuan_bi_dta(G.doc_csv(KEARON))
    return [r for r in ds if nhom is None or r["nhom"] == nhom]


# ── 1. Cỡ hiệu ứng = escalc ─────────────────────────────────────────────────────────────────────────────────────
def test_co_hieu_ung_rr_khop_escalc_tren_bcg():
    ds = _bcg_ds()
    assert len(ds) == 13
    for e, y, v in zip(ds, BCG_YI, BCG_VI):
        assert _gan(e["yi"], y, 1e-8) and _gan(e["vi"], v, 1e-8), e["nghien_cuu"]


def test_smd_dung_he_so_j_chinh_xac_nhu_metafor():
    e = G.co_hieu_ung({"nghien_cuu": "x", "tb_1": 5, "dlc_1": 2, "n_1": 30, "tb_2": 4, "dlc_2": 2.2, "n_2": 28}, "SMD")
    assert _gan(e["yi"], 0.470046061141, 1e-9) and _gan(e["vi"], 0.0709523026648, 1e-9)


def test_o_bang_0_cong_05_ca_bon_o_va_hai_nhanh_0_bi_loai():
    e = G.co_hieu_ung({"nghien_cuu": "x", "su_kien_1": 0, "tong_1": 10, "su_kien_2": 3, "tong_2": 10}, "OR")
    assert _gan(e["yi"], -2.28238238568, 1e-9) and _gan(e["vi"], 2.51428571429, 1e-9)
    assert G.co_hieu_ung({"nghien_cuu": "x", "su_kien_1": 0, "tong_1": 10, "su_kien_2": 0, "tong_2": 12}, "RR") is None
    ds, loai = G.chuan_bi_gop([{"nghien_cuu": "a", "su_kien_1": 0, "tong_1": 9, "su_kien_2": 0, "tong_2": 9},
                               {"nghien_cuu": "b", "su_kien_1": 2, "tong_1": 9, "su_kien_2": 4, "tong_2": 9},
                               {"nghien_cuu": "c", "su_kien_1": 3, "tong_1": 9, "su_kien_2": 5, "tong_2": 9}], "RR")
    assert [e["nghien_cuu"] for e in ds] == ["b", "c"] and "a" in loai[0]


def test_hr_tu_ktc_va_du_lieu_sai_bi_tu_choi():
    e = G.co_hieu_ung({"nghien_cuu": "x", "hr": 0.72, "duoi": 0.58, "tren": 0.89}, "HR")
    assert _gan(e["yi"], math.log(0.72), 1e-12)
    assert _gan(math.sqrt(e["vi"]), (math.log(0.89) - math.log(0.58)) / (2 * 1.959963984540054), 1e-12)
    with pytest.raises(BC.LoiBieuDo):
        G.co_hieu_ung({"nghien_cuu": "x", "hr": 0.5, "duoi": 0.6, "tren": 0.9}, "HR")
    with pytest.raises(BC.LoiBieuDo):
        G.co_hieu_ung({"nghien_cuu": "x", "su_kien_1": 11, "tong_1": 10, "su_kien_2": 1, "tong_2": 10}, "OR")


# ── 2. Gộp một biến = metafor ───────────────────────────────────────────────────────────────────────────────────
def test_gop_reml_khop_metafor():
    g = G.gop(BCG_YI, BCG_VI, "REML")
    assert _gan(g["mu"], -0.7145323484, 1e-7)
    assert _gan(g["se"], 0.1797815318, 1e-6)
    assert _gan(g["tau2"], 0.313243326, 1e-6)
    assert _gan(g["I2"], 92.22138607, 1e-6)
    assert _gan(g["Q"], 152.2330081, 1e-8)
    assert g["df"] == 12 and g["k"] == 13


def test_gop_dl_va_hartung_knapp_khop_metafor():
    d = G.gop(BCG_YI, BCG_VI, "DL")
    assert _gan(d["mu"], -0.7141172221, 1e-8) and _gan(d["tau2"], 0.3087602629, 1e-8)
    h = G.gop(BCG_YI, BCG_VI, "REML", hk=True)
    assert _gan(h["ktc"][0], -1.108443723, 1e-6) and _gan(h["ktc"][1], -0.3206209737, 1e-6)


def test_khoang_du_bao_dung_t_k_tru_2_khong_dung_z():
    from scipy import stats

    g = G.gop(BCG_YI, BCG_VI, "REML")
    w = math.sqrt(g["tau2"] + g["se"] ** 2)
    assert _gan(g["khoang_du_bao"][1], g["mu"] + stats.t.ppf(0.975, 11) * w, 1e-12)
    assert not _gan(g["khoang_du_bao"][1], g["mu"] + 1.959963984540054 * w, 1e-3)
    assert G.gop(BCG_YI, BCG_VI, "FE")["khoang_du_bao"] is None
    assert G.gop(BCG_YI[:2], BCG_VI[:2], "REML")["khoang_du_bao"] is None


def test_egger_khop_regtest_lm_sei():
    e = G.egger(BCG_YI, BCG_VI)
    assert _gan(e["t"], -1.401282002, 1e-8) and _gan(e["p"], 0.1887069951, 1e-7) and e["df"] == 11
    assert G.egger(BCG_YI[:2], BCG_VI[:2])["p"] is None


def test_trim_fill_khop_metafor_reml_va_fe():
    t = G.trim_fill(BCG_YI, BCG_VI, "REML")
    assert t["k0"] == 1 and t["phia"] == "right"
    assert _gan(t["gop_sau_bu"]["mu"], -0.6570828008, 1e-6)
    assert _gan(t["gop_sau_bu"]["tau2"], 0.3312880373, 1e-5)
    f = G.trim_fill(BCG_YI, BCG_VI, "FE")
    assert f["k0"] == 4 and f["phia"] == "right" and _gan(f["gop_sau_bu"]["mu"], -0.2910259921, 1e-8)
    assert len(f["yi_bu"]) == 4 and all(y > -0.2910259921 for y in f["yi_bu"])  # bù ở bên phải


# ── 3. Mô hình hai biến + SROC = metafor rma.mv ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("nhom", [None, "Có triệu chứng", "Không triệu chứng"])
def test_hai_bien_khop_rma_mv(nhom):
    m = G.hai_bien(_kearon_ds(nhom))
    mu1, mu2, se1, se2, t1, t2, rho, cov = KEARON_R[nhom]
    assert _gan(m["mu"][0], mu1, 2e-6) and _gan(m["mu"][1], mu2, 2e-6)
    assert _gan(m["se_mu"][0], se1, 2e-5) and _gan(m["se_mu"][1], se2, 2e-5)
    assert _gan(m["tau2"][0], t1, 1e-4) and _gan(m["tau2"][1], t2, 1e-4)
    assert _gan(m["rho"], rho, 1e-4) and _gan(m["Vmu"][0][1], cov, 1e-4)
    assert _gan(m["do_nhay"]["uoc_luong"], 1 / (1 + math.exp(-mu1)), 1e-6)


def test_hai_bien_tu_choi_duoi_4_nghien_cuu():
    with pytest.raises(BC.LoiBieuDo):
        G.hai_bien(_kearon_ds()[:3])


def test_lr_va_dor_nhat_quan_voi_se_sp():
    m = G.hai_bien(_kearon_ds("Có triệu chứng"))
    se, sp = m["do_nhay"]["uoc_luong"], m["do_dac_hieu"]["uoc_luong"]
    assert _gan(m["lr_duong"]["uoc_luong"], se / (1 - sp), 1e-10)
    assert _gan(m["lr_am"]["uoc_luong"], (1 - se) / sp, 1e-10)
    assert _gan(m["dor"]["uoc_luong"], (se / (1 - se)) / ((1 - sp) / sp), 1e-9)
    for k in ("lr_duong", "lr_am", "dor"):
        lo, hi = m[k]["ktc"]
        assert lo < m[k]["uoc_luong"] < hi


def test_duong_sroc_qua_diem_tom_tat_dung_do_doc_va_khong_ngoai_suy():
    ds = _kearon_ds("Có triệu chứng")
    m = G.hai_bien(ds)
    fpr0 = 1 - m["do_dac_hieu"]["uoc_luong"]
    xs, ys = G.duong_sroc(m, fpr0 - 1e-9, fpr0 + 1e-9, so_diem=3)
    assert _gan(ys[1], m["do_nhay"]["uoc_luong"], 1e-6)  # Rutter–Gatsonis đi qua điểm tóm tắt
    # độ dốc trong không gian logit = σA/σB (RG) và −ρσA/σB (Reitsma)
    lg = lambda p: math.log(p / (1 - p))  # noqa: E731
    xa, ya = G.duong_sroc(m, 0.02, 0.2, "rutter-gatsonis", 2)
    assert _gan((lg(ya[1]) - lg(ya[0])) / (lg(xa[1]) - lg(xa[0])), math.sqrt(m["tau2"][0] / m["tau2"][1]), 1e-9)
    xb, yb = G.duong_sroc(m, 0.02, 0.2, "reitsma", 2)
    assert _gan((lg(yb[1]) - lg(yb[0])) / (lg(xb[1]) - lg(xb[0])),
                -m["rho"] * math.sqrt(m["tau2"][0] / m["tau2"][1]), 1e-9)
    xs, _ = G.duong_sroc(m, 0.05, 0.3)
    assert min(xs) >= 0.05 - 1e-12 and max(xs) <= 0.3 + 1e-12


def test_vung_du_bao_bao_trum_vung_tin_cay_va_diem_tom_tat():
    import numpy as np

    m = G.hai_bien(_kearon_ds("Không triệu chứng"))
    lg = lambda p: math.log(p / (1 - p))  # noqa: E731
    tam = np.array([-m["mu"][1], m["mu"][0]])
    V = np.array(m["Vmu"]) + np.array(m["Sigma"])
    C = np.linalg.inv(np.array([[V[1, 1], -V[0, 1]], [-V[0, 1], V[0, 0]]]))
    ex, ey = G.elip(m, "tin_cay")
    for x, y in zip(ex, ey):
        d = np.array([lg(x), lg(y)]) - tam
        assert float(d @ C @ d) < 5.991  # mọi điểm của vùng tin cậy nằm trong vùng dự báo (χ²₂ 0,95 = 5,991)
    xs = [lg(x) for x in ex]
    assert min(xs) < tam[0] < max(xs)
    # elip dự báo nằm ĐÚNG trên đường đồng mức χ²₂(0,95) của Σ + Var(μ̂) (bỏ Σ ⇒ elip co lại thành vùng tin cậy)
    px, py = G.elip(m, "du_bao")
    for x, y in list(zip(px, py))[::20]:
        d = np.array([lg(x), lg(y)]) - tam
        assert abs(float(d @ C @ d) - 5.991464547) < 1e-6


def test_auc_sroc_trong_0_1_va_lon_hon_nhom_kem_hon():
    a1 = G.auc_sroc(G.hai_bien(_kearon_ds("Có triệu chứng")))
    a2 = G.auc_sroc(G.hai_bien(_kearon_ds("Không triệu chứng")))
    assert 0.5 < a2 < a1 < 1


def test_clopper_pearson_khop_binom_test():
    lo, hi = G.clopper_pearson(20, 25)
    assert _gan(lo, 0.592962567721, 1e-9) and _gan(hi, 0.931688535988, 1e-9)
    lo, hi = G.clopper_pearson(0, 29)
    assert lo == 0.0 and _gan(hi, 0.11944486907, 1e-9)
    assert G.clopper_pearson(29, 29)[1] == 1.0


def test_deeks_khop_lm_co_trong_so_ess():
    d = G.deeks(_kearon_ds())
    assert _gan(d["doc"], -24.1221843967, 1e-8) and _gan(d["t"], -2.84877807262, 1e-8)
    assert _gan(d["p"], 0.00813680848458, 1e-6) and d["df"] == 28


def test_hieu_chinh_lien_tuc_ba_che_do():
    r = {"nghien_cuu": "x", "tp": 20, "fp": 0, "fn": 5, "tn": 29}
    a = G.logit_dta(r, "chi_o_0")
    assert _gan(a[0], math.log(20.5 / 5.5)) and _gan(a[2], math.log(29.5 / 0.5))
    b = G.logit_dta({**r, "fp": 1}, "chi_o_0")
    assert _gan(b[0], math.log(20 / 5))
    c = G.logit_dta({**r, "fp": 1}, "tat_ca")
    assert _gan(c[0], math.log(20.5 / 5.5))
    with pytest.raises(BC.LoiBieuDo):
        G.logit_dta(r, "khong")


# ── 4. Định dạng số theo ngôn ngữ tài liệu ───────────────────────────────────────────────────────────────────────
def test_so_viet_dung_dau_phay_va_dau_tru():
    assert BC.so(0.48942, 2, "vi") == "0,49"
    assert BC.so(-1.2, 2, "vi") == "−1,20"
    assert BC.so(-0.0001, 2, "vi") == "0,00"
    assert BC.so(0.48942, 2, "en") == "0.49"
    assert BC.p_chu(0.0004, "vi") == "p < 0,001" and BC.p_chu(0.1887, "vi") == "p = 0,189"
    assert BC.p_chu(0.1887, "en") == "p = 0.189"
    assert G._nhan_vach(0.5, "vi") == "0,5" and G._nhan_vach(2, "vi") == "2" and G._nhan_vach(0.25, "en") == "0.25"
    with pytest.raises(BC.LoiBieuDo):
        BC.kiem_ngon_ngu("fr")


# ── 5. Hình ghi ra đúng chuẩn + JSON khớp số tính ────────────────────────────────────────────────────────────────
def _dpi(p: Path):
    from PIL import Image

    with Image.open(p) as im:
        return im.info.get("dpi")


@pytest.mark.parametrize("lenh,du_lieu,them", [
    ("forest", BCG, ["--do", "RR", "--nhan-trai", "Ưu thế vắc-xin", "--nhan-phai", "Ưu thế chứng"]),
    ("pheu", BCG, ["--do", "RR", "--duong-vien", "--trim-fill"]),
    ("bo-tung-nc", BCG, ["--do", "RR"]),
    ("dta-forest", KEARON, []),
    ("sroc", KEARON, []),
    ("deeks", KEARON, []),
])
def test_dong_lenh_ghi_png_300dpi_pdf_va_json(tmp_path, lenh, du_lieu, them):
    ra = tmp_path / lenh
    assert G.main([lenh, "--du-lieu", str(du_lieu), "--ra", str(ra), *them]) == 0
    png, pdf, js = ra.with_suffix(".png"), ra.with_suffix(".pdf"), ra.with_suffix(".json")
    assert png.stat().st_size > 10_000 and pdf.read_bytes()[:5] == b"%PDF-"
    assert round(_dpi(png)[0]) == 300
    so_lieu = json.loads(js.read_text(encoding="utf-8"))
    assert so_lieu["loai"] == lenh.replace("-", "_").replace("bo_tung_nc", "bo_tung_nc")
    assert not list(tmp_path.glob("*.tam.*"))  # không để lại tệp tạm


def test_json_forest_mang_dung_so_va_phan_nhom(tmp_path):
    sl = G.ve_forest(_bcg_ds(), "RR", tmp_path / "f")
    assert _gan(sl["gop"]["uoc_luong"], math.exp(-0.7145323484), 1e-6)
    assert set(sl["phan_nhom"]) == {"Phân bổ ngẫu nhiên", "Phân bổ khác"}
    assert sl["kiem_dinh_khac_biet_nhom"]["df"] == 1
    assert _gan(sum(x["trong_so_pt"] for x in sl["nghien_cuu"]), 100.0, 1e-9)


def test_json_sroc_duong_trong_khoang_fpr_da_hieu_chinh(tmp_path):
    sl = G.ve_sroc(_kearon_ds(), tmp_path / "s")
    for ten, m in sl["nhom"].items():
        lo, hi = m["khoang_fpr_duong"]
        assert lo > 0  # nghiên cứu FP = 0 không kéo đường về FPR = 0
        assert min(m["duong"]["fpr"]) >= lo - 1e-12 and max(m["duong"]["fpr"]) <= hi + 1e-12, ten


def test_sroc_nhom_duoi_4_nghien_cuu_chi_ve_cham(tmp_path):
    ds = _kearon_ds("Có triệu chứng")[:3] + _kearon_ds("Không triệu chứng")
    sl = G.ve_sroc(ds, tmp_path / "s")
    assert sl["nhom"]["Có triệu chứng"]["mo_hinh"] is None
    assert sl["nhom"]["Không triệu chứng"]["mo_hinh"]["k"] == 14


def test_ma_thoat_du_lieu_sai_va_tham_so_sai(tmp_path):
    assert G.main(["forest", "--du-lieu", str(tmp_path / "khong-co.csv"), "--ra", str(tmp_path / "x")]) == 2
    assert G.main(["forest", "--du-lieu", str(BCG), "--ra", str(tmp_path / "x"), "--do", "XYZ"]) == 3
    p = tmp_path / "mot.csv"
    p.write_text("nghien_cuu,yi,vi\na,0.1,0.02\n", encoding="utf-8", newline="\n")
    assert G.main(["forest", "--du-lieu", str(p), "--ra", str(tmp_path / "x")]) == 2


# ── 6. Kiểm chéo R: không có R ⇒ «không kiểm chéo được», không bao giờ «khớp» ────────────────────────────────────
def test_khong_co_r_thi_khong_bao_khop(monkeypatch):
    import cau_noi_r as CR

    def _khong(*_a, **_k):
        raise CR.KhongDoDuoc("không tìm thấy Rscript")

    monkeypatch.setattr(CR, "tim_r", _khong)
    kc = G.kiem_cheo_gop_r(BCG_YI, BCG_VI)
    assert kc["trang_thai"] == "khong_kiem_cheo_duoc"
    assert BC.doi_chieu({"a": 1.0}, {"trang_thai": "da_chay", "kq": {}})["trang_thai"] == "thieu_khoa"
    assert BC.doi_chieu({"a": 1.0}, {"trang_thai": "da_chay", "kq": {"a": 1.1}})["trang_thai"] == "lech"


def _co_r_metafor() -> bool:
    try:
        import cau_noi_r as CR

        CR.tim_r()
    except Exception:  # noqa: BLE001
        return False
    kq = BC.chay_r_kiem_cheo('cat("KQ ok", as.numeric(requireNamespace("metafor", quietly=TRUE)), "\\n")')
    return kq["kq"].get("ok") == 1.0


CO_R = shutil.which("Rscript") is not None and _co_r_metafor()


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript + metafor")
def test_song_kiem_cheo_r_gop_va_hai_bien():
    assert G.kiem_cheo_gop_r(BCG_YI, BCG_VI, "REML")["trang_thai"] == "khop"
    assert G.kiem_cheo_gop_r(BCG_YI, BCG_VI, "DL", hk=True)["trang_thai"] == "khop"
    assert G.kiem_cheo_dta_r(_kearon_ds("Không triệu chứng"))["trang_thai"] == "khop"
