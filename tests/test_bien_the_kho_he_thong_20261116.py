"""Bản vá HỆ THỐNG lộ ra khi giả lập các biến thể khó (bác sĩ 16/11/2026: «làm tiếp giả lập thêm các biến thể khó,
mỗi biến thể một kịch bản» — rồi «giả lập tới khi xác nhận đạt hoàn thiện»).

1. Engine G6: Poisson vững của THỬ NGHIỆM CỤM — bản cũ trả lỗi «chưa hỗ trợ hiệu chỉnh cụm» ⇒ RCT cụm không có PR nào.
   Nay sandwich theo cụm CR1 + t(G−1), khớp R ``sandwich::vcovCL(type = "HC1")`` (số chuẩn tính bằng R 16/11/2026).
2. Làm sạch G5: ô bắt buộc mang MÃ THIẾU ĐÃ KHAI (_ma-thieu-theo-bien.csv) là thiếu có ghi nhận — không mở truy vấn
   (hướng dẫn nhập liệu dạy ghi mã thay vì để trống; bản cũ vẫn mở truy vấn từng ô ⇒ đề tài hồi cứu không khoá được G5).
3. G4: đề tài khai đánh giá kinh tế (gate_params.G1.economic_evaluation) ⇒ SAP có §16 (CHEERS 2022) và §16 BẮT BUỘC.
4. G6: phân tích đặc thù «kinh_te» — ICER, NMB, bootstrap phân tầng, CEAC; kịch bản R/SPSS kiểm chéo.
5. Khuôn script G6: dòng mô hình chính của Cox và hiệu số tỷ lệ có dấu «◆ MÔ HÌNH CHÍNH (SAP §4)»; prop.test tính
   hiệu nhóm 1 − nhóm 0 (cùng chiều engine — bản cũ ra p0 − p1, đảo kết luận không kém hơn).
"""
from __future__ import annotations

import math
import random
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import approve_gate as AG  # noqa: E402
import chay_sap_g6 as CS6  # noqa: E402
import clean_research_dataset as CRD  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import phan_tich_thiet_ke_dac_thu as PTD  # noqa: E402
import run_g4_auto as G4A  # noqa: E402
import run_g6_auto as G6A  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")


# ───────────────────────────── 1. Poisson vững theo cụm ─────────────────────────────
def _du_lieu_cum(sd_cum: float = 0.9, so_cum: int = 16, m: int = 6, seed: int = 7):
    rng = random.Random(seed)
    rows = []
    for k in range(so_cum):
        arm, u = k % 2, rng.gauss(0, sd_cum)
        for _ in range(m):
            p = min(0.9, 0.4 * (1.5 if arm else 1))
            lg = math.log(p / (1 - p)) + u
            rows.append({"y": int(rng.random() < 1 / (1 + math.exp(-lg))), "nhom": arm,
                         "tuoi": round(rng.gauss(60, 8), 1), "cum": k + 1})
    return pd.DataFrame(rows)


def test_poisson_theo_cum_khop_r_vcovcl_hc1():
    """Số chuẩn: R 4.x glm(poisson) + sandwich::vcovCL(type="HC1", cadjust=TRUE) + coefci(df = G−1)."""
    kq = RSA.poisson_pr_model(_du_lieu_cum(), "y", "nhom", ["tuoi"], None, "cum")
    assert kq["model"] == "poisson_robust_cluster" and kq["cov_type"] == "cluster"
    assert kq["cluster"] == {"cot": "cum", "so_cum": 16}
    hc = kq["results"][0]
    assert hc["variable"] == "nhom"
    assert hc["PR_adj"] == pytest.approx(1.042401, abs=1e-4)
    assert hc["CI_95"] == pytest.approx([0.549850, 1.976174], abs=1e-4)
    assert kq["tho"][0]["CI_95"] == pytest.approx([0.552914, 1.969288], abs=1e-4)


def test_poisson_theo_cum_rong_hon_hc0_khi_cum_manh():
    df = _du_lieu_cum(sd_cum=1.5, so_cum=30, m=10, seed=11)
    cum = RSA.poisson_pr_model(df, "y", "nhom", ["tuoi"], None, "cum")["results"][0]["CI_95"]
    hc0 = RSA.poisson_pr_model(df, "y", "nhom", ["tuoi"])["results"][0]["CI_95"]
    assert math.log(cum[1] / cum[0]) > 1.3 * math.log(hc0[1] / hc0[0]), (cum, hc0)


def test_poisson_mot_cum_bao_loi_khong_chay_sai():
    df = _du_lieu_cum().assign(cum=1)
    kq = RSA.poisson_pr_model(df, "y", "nhom", ["tuoi"], None, "cum")
    assert "error" in kq and "1 giá trị" in kq["error"]


def test_poisson_khong_cum_giu_hc0():
    kq = RSA.poisson_pr_model(_du_lieu_cum(), "y", "nhom", ["tuoi"])
    assert kq["model"] == "poisson_robust_hc0" and "cluster" not in kq


def test_kich_ban_r_tai_lap_poisson_cum_dung_vcovcl():
    r = RSA.generate_r_script("S", "G6", "y", "nhom", ["tuoi"], "poisson_pr", "cum")
    assert "vcovCL(model_adj, cluster = ~ cum, type = 'HC1')" in r and "df = df_cum" in r
    assert "vcovHC" not in r


# ───────────────────────────── 2. Mã thiếu đã khai không mở truy vấn ─────────────────────────────
def _kiem_lam_sach(gia_tri_goc: list[str], khai: dict | None):
    cot = ["record_id", "corticoid"]
    goc = [{"record_id": f"R{i}", "corticoid": v} for i, v in enumerate(gia_tri_goc, 1)]
    meo_thieu = {"", "na", "kdd"}  # ô đã quy về trống sau _clean_cell (mã thiếu ⇒ "")
    sach = [{"record_id": r["record_id"], "corticoid": "" if r["corticoid"].strip().lower() in meo_thieu
             else r["corticoid"]} for r in goc]
    luat = {"corticoid": {"name": "corticoid", "required": True}}
    tk: dict = {}
    loi = CRD._validate_rows(cot, sach, luat, "record_id", ["corticoid"],
                             logic_rows=[CRD._dong_cho_logic(r, cot) for r in goc], branching_stats=tk,
                             ma_thieu_khai=khai)
    return [x for x in loi if x["type"] == "missing_required_value"], tk


def test_o_bat_buoc_mang_ma_thieu_da_khai_khong_mo_truy_van():
    loi, tk = _kiem_lam_sach(["KDD", "kdd", "1"], {"corticoid": ["KDD"]})
    assert loi == [] and tk["required_missing_coded"] == 2


def test_o_trong_that_va_token_mac_dinh_van_bi_truy_van():
    loi, tk = _kiem_lam_sach(["", "NA", "KDD"], {"corticoid": ["KDD"]})
    assert sorted(x["row"] for x in loi) == [1, 2] and tk["required_missing_coded"] == 1


def test_khong_khai_ma_thieu_thi_ma_chu_cung_bi_truy_van():
    loi, _tk = _kiem_lam_sach(["KDD"], None)
    assert len(loi) == 1, "mã CHƯA khai không được coi là thiếu có ghi nhận"


def test_ma_thieu_cua_bien_khac_khong_mien_truy_van():
    loi, _tk = _kiem_lam_sach(["KDD"], {"loang_xuong": ["KDD"]})
    assert len(loi) == 1


# ───────────────────────────── 3. SAP §16 đánh giá kinh tế ─────────────────────────────
_KT_DU = {k: f"giá trị {k}" for k, _n, _g in G4A.KINH_TE_O} | {"bien_nhom": "nhom", "bien_chi_phi": "cp",
                                                                 "bien_hieu_qua": "ks"}


def test_muc_kinh_te_chi_sinh_khi_g1_khai():
    assert G4A.muc_kinh_te(None) == [] and G4A.muc_kinh_te({}) == []
    du = "\n".join(G4A.muc_kinh_te(_KT_DU))
    assert "### §16 ĐÁNH GIÁ KINH TẾ Y TẾ" in du and "PMID 35017145" in du and "ICER = ΔC/ΔE" in du
    assert "[CẦN" not in du
    thieu = "\n".join(G4A.muc_kinh_te({"perspective": "cơ sở y tế"}))
    assert thieu.count("[CẦN BÁC SĨ") == len(G4A.KINH_TE_O) - 1 + 1  # 10 ô vắng + dòng biến phân tích


def _sap(muc16: list[str]) -> str:
    than = "\n".join(f"### §{i} MỤC {i}\n\n- **Nội dung:** đã điền đủ  \n" for i in (1, 2, 4, 5, 9, 10))
    return "## PHẦN 3, SAP\n\n" + than + "\n".join(muc16) + "\n## PHẦN 4, THAY ĐỔI\n"


def test_muc_16_bat_buoc_khi_g1_khai_kinh_te_hoac_sap_co_muc():
    assert "§16" not in AG._g4_muc_bat_buoc(_sap([]), "cohort")
    assert "§16" in AG._g4_muc_bat_buoc(_sap([]), "cohort", co_kinh_te=True)
    assert "§16" in AG._g4_muc_bat_buoc(_sap(G4A.muc_kinh_te(_KT_DU)), "cohort")


def test_muc_16_con_o_trong_hoac_vang_thi_chua_ky_duoc():
    con_trong = AG._g4_sections_still_draft(_sap(G4A.muc_kinh_te({"perspective": "x"})), "cohort", True)
    assert any(m.startswith("§16") for m in con_trong)
    vang = AG._g4_sections_still_draft(_sap([]), "cohort", True)
    assert any(m.startswith("§16") for m in vang), "G1 khai kinh tế mà SAP mất §16 ⇒ phải báo VẮNG"
    assert not any(m.startswith("§16") for m in AG._g4_sections_still_draft(_sap(G4A.muc_kinh_te(_KT_DU)), "cohort",
                                                                              True))


# ───────────────────────────── 4. Phân tích đặc thù «kinh_te» ─────────────────────────────
def _hang_kinh_te(n: int = 400, seed: int = 1):
    rng = random.Random(seed)
    hang = []
    for i in range(n):
        g = i % 2
        ks = 1 if rng.random() < (0.70 if g else 0.48) else 0
        hang.append({"nhom": g, "cp": max(0.0, rng.gauss(1_800_000, 400_000) + 600_000 * g - 150_000 * ks),
                     "ks": ks})
    return hang


def test_kinh_te_icer_goc_phan_tu_va_nmb_dung_dinh_nghia():
    hang = _hang_kinh_te()
    kq = PTD.kinh_te(hang, "nhom", "cp", "ks", 5_000_000)
    tb = {(g, c): sum(r[c] for r in hang if r["nhom"] == g) / 200 for g in (0, 1) for c in ("cp", "ks")}
    dc, de = tb[1, "cp"] - tb[0, "cp"], tb[1, "ks"] - tb[0, "ks"]
    assert kq["delta_c"] == pytest.approx(dc) and kq["delta_e"] == pytest.approx(de)
    assert kq["icer"] == pytest.approx(dc / de)
    assert kq["nmb_tai_wtp"] == pytest.approx(5_000_000 * de - dc)
    assert kq["goc_phan_tu"].startswith("Đông Bắc")
    assert kq["ci_95_delta_c"][0] < dc < kq["ci_95_delta_c"][1]
    assert sum(kq["mat_phang_bootstrap_pct"].values()) == pytest.approx(100.0)


def test_kinh_te_bootstrap_tat_dinh_va_ceac_tai_lambda_0():
    hang = _hang_kinh_te()
    a, b = PTD.kinh_te(hang, "nhom", "cp", "ks", 5_000_000), PTD.kinh_te(hang, "nhom", "cp", "ks", 5_000_000)
    assert a["ceac"] == b["ceac"] and a["ci_95_nmb"] == b["ci_95_nmb"]
    goc = a["mat_phang_bootstrap_pct"]
    assert a["ceac"][0]["ty_le_chi_phi_hieu_qua"] * 100 == pytest.approx(goc["dong_nam"] + goc["tay_nam"], abs=1e-9)


def test_kinh_te_tu_choi_wtp_am_va_nhanh_qua_nho():
    with pytest.raises(PTD.TuChoi):
        PTD.kinh_te(_hang_kinh_te(), "nhom", "cp", "ks", -1)
    with pytest.raises(PTD.TuChoi):
        PTD.kinh_te([{"nhom": 1, "cp": 1, "ks": 1}, {"nhom": 0, "cp": 1, "ks": 0}], "nhom", "cp", "ks", 1)


def test_kinh_te_kich_ban_r_spss_va_doi_so_chay_sap():
    ts = {"nhom": "nhom", "chi_phi": "cp", "hieu_qua": "ks", "nguong_wtp": 5_000_000}
    r = PTD.kich_ban_r("kinh_te", ts, Path("/tmp/x.csv"), Path("/tmp/y.txt"))
    assert 'ghi("icer", (c1 - c0) / (e1 - e0))' in r and f"set.seed({PTD.HAT_GIONG_KT})" in r
    sp = PTD.kich_ban_spss("kinh_te", ts, Path("/tmp/x.csv"), Path("/tmp/y.csv"))
    assert "COMPUTE icer = delta_c / delta_e." in sp and "/KEEP=chi_phi_tb_1" in sp
    assert set(PTD.LOAI["kinh_te"]) <= set(CS6.THAM_SO) and "kinh_te" in CS6.DAC_THU
    pt = {"id": "KT", "vai": "phu", "tham_so": {"loai_dac_thu": "kinh_te", **ts}}
    assert CS6.doi_so_run_stats(pt)[-2:] == ["--nguong-wtp", "5000000"]


def test_doc_kq_spss_bo_o_trong_khong_gan_0(tmp_path):
    p = tmp_path / "kq.csv"
    p.write_text("delta_c,icer\n10.5,\n", encoding="utf-8", newline="\n")
    assert PTD._doc_kq_spss(p, "kinh_te") == {"delta_c": 10.5}


# ───────────────────────────── 5. Khuôn script G6: dòng mô hình chính + chiều hiệu số ─────────────────────────────
_V = {"exposure": "ppi", "outcome": "gay", "time_col": "t", "covariates": ["tuoi"], "detection_log": [],
      "cluster_col": None, "outcome_ordinal": False}
_BAT = re.compile(r"^# ((?:df <- readRDS|fit_\w+ <- |(?=[^\n]*◆ MÔ HÌNH CHÍNH))[^\n]*)$", re.M)


@pytest.mark.parametrize(("thiet_ke", "loai", "ho"), [("cohort", "HR", "cox"), ("rct", "HR", "cox"),
                                                      ("rct", "ARR%", "risk_diff"),
                                                      ("rct", "NI_PROPORTION", "risk_diff")])
def test_bat_dong_mo_hinh_chinh_cho_ra_ho_mo_hinh_dung(thiet_ke, loai, ho):
    """Thống kê viên bật ĐÚNG các dòng có dấu ◆ ⇒ cổng G6 thấy họ mô hình ở dòng THI HÀNH (G6-AUTO-09)."""
    r03 = G6A.R_ANALYSIS_MAP_FUNC(thiet_ke, dict(_V), 100, 0.05, 0.8, 1.5, loai)
    bat = _BAT.sub(r"\1", r03)
    thi_hanh = G6Q._dong_thi_hanh(bat)
    assert ho in G6Q._ho_mo_hinh_script("\n".join(thi_hanh)), r03[:400]
    # dòng MÔ HÌNH (không chỉ đối tượng Surv) phải được bật: Cox ⇒ coxph( · hiệu số ⇒ prop.test(
    assert any(("coxph(" if ho == "cox" else "prop.test(") in d for d in thi_hanh), thi_hanh
    for dong in bat.splitlines():  # dòng đã bật phải là MỘT câu lệnh R trọn vẹn (không mở ngoặc dở dang)
        if not dong.lstrip().startswith("#") and "◆" in dong:
            ma = dong.split("#", 1)[0]
            assert ma.count("(") == ma.count(")"), dong


def test_prop_test_tinh_nhom_1_tru_nhom_0():
    r03 = G6A.R_ANALYSIS_MAP_FUNC("rct", dict(_V), 100, 0.05, 0.8, 1.5, "ARR%")
    assert 'prop.test(bang[c("1", "0"), "1"], rowSums(bang)[c("1", "0")]' in r03
    assert not re.search(r"^# hieu_nguy_co <- prop\.test\(bang\[, \"1\"\]", r03, re.M)


def test_prop_test_chay_that_bang_r_cung_dau_engine(tmp_path):
    try:
        import cau_noi_r as CR

        r_bin = CR.tim_r()
    except Exception:  # noqa: BLE001 — máy không có R ⇒ bỏ qua phép thử chạy thật (phép thử chữ vẫn chạy)
        pytest.skip("không có R")
    csv_p = tmp_path / "d.csv"
    hang = ["nhom,ks"] + [f"1,{int(i < 30)}" for i in range(50)] + [f"0,{int(i < 40)}" for i in range(50)]
    csv_p.write_text("\n".join(hang) + "\n", encoding="utf-8", newline="\n")
    dong = next(d for d in G6A.R_ANALYSIS_MAP_FUNC("rct", dict(_V, exposure="nhom", outcome="ks"), 100, 0.05, 0.8,
                                                   1.5, "ARR%").splitlines() if "hieu_nguy_co <- prop.test" in d)
    ma = (f'df <- read.csv("{csv_p.as_posix()}")\nbang <- table(df$nhom, df$ks)\n'
          + dong.lstrip("# ").split("  #")[0] + '\ncat(sprintf("%.6f", diff(rev(hieu_nguy_co$estimate))))\n')
    (tmp_path / "k.R").write_text(ma, encoding="utf-8", newline="\n")
    ra = subprocess.run([str(r_bin), str(tmp_path / "k.R")], capture_output=True, text=True, timeout=120)
    # estimate = (p nhóm 1, p nhóm 0) ⇒ diff(rev()) = p1 − p0 = 0,60 − 0,80 = −0,20 (cùng dấu risk_diff của engine)
    assert ra.stdout.strip().endswith("-0.200000"), ra.stdout + ra.stderr


# ───────────────────────────── 6. Bảng 5 MI với kết cục Poisson (PR) ─────────────────────────────
def test_bang_5_mi_poisson_in_pr_khong_in_dau_hoi():
    mi = {"model": "poisson_hc0_mi", "n_imputations": 20, "n_total": 100, "n_complete_case": 80, "n_missing_rows": 20,
          "pct_missing_rows": 20.0, "results": [{"variable": "ppi", "PR_adj": 1.3308, "CI_95": [1.1111, 1.5941],
                                                  "p": 0.0019}]}
    cc = {"results": [{"variable": "ppi", "PR_adj": 1.4067, "CI_95": [1.1489, 1.7223], "p": 0.001}]}
    van = RSA.format_mi_text(mi, cc)
    dong = next(d for d in van.splitlines() if d.strip().startswith("ppi"))
    assert "1.3308" in dong and "1.4067" in dong and "?" not in dong, dong
    assert "PR (MI)" in van and "OR/β (MI)" not in van


# ───────────────────────────── 7. Mục tiêu chung PI khai ở G1 (đề tài nhiều mục tiêu) ─────────────────────────────
def test_study_spec_doc_muc_tieu_chung_tu_g1():
    import research_study_spec as RS

    sp = RS.build_study_spec("ZZ", {}, {"gate_params": {"G1": {"objectives": ["A", "B"], "aim": "Mục tiêu chung X"}}})
    assert sp["objectives"] == {"general": "Mục tiêu chung X", "specific": ["A", "B"]}
    cap_cao = RS.build_study_spec("ZZ", {}, {"aim": "Cấp cao", "gate_params": {"G1": {"aim": "G1"}}})
    assert cap_cao["objectives"]["general"] == "Cấp cao", "khoá cấp cao vẫn là ghi đè có chủ ý"


# ───────────────────────────── 8. Ô hỏi lại điều đã chốt (đo trên 15 kịch bản) ─────────────────────────────
def _goi_g2(meta: dict | None) -> str:
    import run_g2_auto as G2

    return G2.generate_g2_full_package(
        topic="Đề tài test", study_name="TEST-STUDY", design_code="cohort", design_primary="Thuần tập",
        reporting_std="STROBE", n_sr=5, n_rct=1, evidence_level="TRUNG BÌNH", registry=None,
        risk=G2.RISK_PROFILES["cohort"], run_date="2026-11-16", n_adjusted=300, meta=meta)


def test_g2_lay_thoi_gian_va_khoang_trong_tu_g1():
    meta = {"gate_params": {"G1": {"study_period": "01/2027 đến 12/2027",
                                   "knowledge_gap": "Chưa có số liệu tại phòng khám ngoại trú Việt Nam"}}}
    doc = _goi_g2(meta)
    assert "Thời gian nghiên cứu: 01/2027 đến 12/2027" in doc
    assert "Lý do cần nghiên cứu tại bối cảnh Việt Nam: Chưa có số liệu tại phòng khám ngoại trú Việt Nam" in doc
    trong = _goi_g2({})
    assert "Thời gian nghiên cứu: [CẦN — từ ___/___/" in trong, "G1 chưa khai ⇒ vẫn hỏi PI"
    assert "[CẦN BỔ SUNG: lý do cần nghiên cứu thêm tại bối cảnh Việt Nam]" in trong


def test_khoang_trong_nguoi_viet_thay_o_cho_dien_cua_g0():
    import quyet_dinh_da_chot as QD

    g0 = ["KHÔNG phát hiện khoảng trống — [CẦN BÁC SĨ TỰ XÁC ĐỊNH khoảng trống]", "Có 6 thử nghiệm đang tuyển"]
    meta = {"gate_params": {"G1": {"knowledge_gap": "Thiếu ước lượng ở người không suy tim"}}}
    assert QD.khoang_trong_cho_van_ban(meta, g0) == ["Thiếu ước lượng ở người không suy tim",
                                                      "Có 6 thử nghiệm đang tuyển"]
    assert QD.khoang_trong_cho_van_ban({}, g0) == g0, "chưa ai viết ⇒ giữ nguyên ô hỏi PI"
    assert QD.khoang_trong_da_chot({"gate_params": {"G1": {"knowledge_gap": "[CẦN BỔ SUNG]"}}}) is None


def test_g4_ket_cuc_phu_ngung_mot_nguoi_va_itt_tu_g1(tmp_path):
    sap = "\n".join(["- **Kết cục phụ 1:** [CẦN]  ", "- **Kết cục phụ 2:** [CẦN]  ",
                     "- **Tiêu chí ngừng/đổi can thiệp cho MỘT người tham gia:** [CẦN — vd đổi liều khi có tác "
                     "dụng phụ, tiêu chí rút khỏi nghiên cứu — khác quy tắc dừng CẢ nghiên cứu ở §13]  ",
                     "- **Quần thể phân tích CHÍNH:** [CẦN THỐNG KÊ VIÊN/PI CHỐT — phải khớp chiến lược biến cố xen "
                     "ngang của estimand (vd treatment-policy ⇒ ITT); quần thể khác (vd per-protocol) chỉ là phân tích "
                     "độ nhạy ở §9]  "])
    meta = {"gate_params": {"G1": {"secondary_outcomes": ["Huyết áp tâm thu"], "stopping_rescue_rules": "Ngừng khi HA "
                                   "≥180/110", "estimand": {"intercurrent_events_strategy": "Treatment-policy"}}}}
    khung = G4A._khung_sap(tmp_path, meta)
    assert khung["phu_da_khai"] and khung["itt_tu_estimand"] and khung["ngung_mot_nguoi"]
    ra = G4A._dien_khung(sap, khung, "rct")
    assert "Kết cục phụ 1:** Huyết áp tâm thu" in ra and "Kết cục phụ 2:** Không có — G1 chốt 1 kết cục phụ" in ra
    assert "MỘT người tham gia:** Ngừng khi HA ≥180/110" in ra and "Quần thể phân tích CHÍNH:** ITT" in ra
    khung2 = G4A._khung_sap(tmp_path, {"gate_params": {"G1": {}}})
    assert not khung2["phu_da_khai"] and not khung2["itt_tu_estimand"], "G1 chưa khai ⇒ giữ ô hỏi người"
