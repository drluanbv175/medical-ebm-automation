"""Lỗi hệ thống lộ ra khi đưa 7 thiết kế ngoài thuần tập đi hết G6.5 → G10 (16/11/2026, giả lập trọn vòng 8 thiết kế).

Mỗi nhóm phép thử khoá MỘT lỗi đo được trên đề tài giả lập:
  1. Engine G6 ghi «Risk difference» cho đề tài BỆNH–CHỨNG (lấy mẫu theo bệnh ⇒ không ước lượng được nguy cơ).
  2. Bảng Poisson in «PR — tỷ lệ hiện mắc» cho RCT/thuần tập (kết cục là nguy cơ tích luỹ ⇒ RR).
  3. G0 để nhãn «[CẦN BÁC SĨ TỰ XÁC ĐỊNH …]» ngoài bộ nhãn skill ⇒ check_de_cuong R3 chặn G10.
  4. Mục Đặt vấn đề G10 in khoảng trống MÁY suy dù PI đã viết khoảng trống ở G1 (StudySpec ưu tiên người từ 10/10).
  5. Đề cương G10 đòi PI khai lại quyết định đặc thù thiết kế đã chốt ở G1/SAP (ngưỡng chẩn đoán, tiêu chuẩn chọn +
     công cụ RoB của tổng quan, chọn mẫu + audit trail của định tính, kiểm định/hiệu chuẩn/phân biệt của dự báo) và in
     «Yếu tố nhiễu: [CẦN BỔ SUNG]» cho thiết kế không ước lượng nhân quả.
  6. G8-AUTO-08 đòi khai lại tuyên bố chia sẻ dữ liệu tác giả đã khai ở G7.
  7. SAP tổng quan–gộp dùng khuôn cá thể (EPV, gán đa trị MI, ±1 SD, mice); SAP định tính hỏi lại tiếp cận/bão hoà/
     chọn mẫu đã chốt ở G1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_de_cuong as CDC  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import quyet_dinh_da_chot as QD  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402
import skill_standards as S  # noqa: E402

STUDY = "ZZ-HE-THONG"


# ── 1. Bệnh–chứng: không báo hiệu số nguy cơ ───────────────────────────────────────────────────────────────────
def test_benh_chung_go_hieu_so_nguy_co_ke_ca_ban_cum_va_ghi_ly_do():
    res = {"outcome_type": "binary", "or_crude": 1.67, "ci_95": (1.09, 2.56), "risk_diff": 0.119,
           "risk_diff_ci_95": (0.017, 0.221), "p_value": 0.02,
           "cum": {"or_cum": 1.6, "risk_diff_cum": 0.1, "risk_diff_ci_95_cum": (0.0, 0.2), "p_rd_cum": 0.05}}
    ra = RSA.bo_hieu_so_benh_chung(res)
    assert "risk_diff" not in ra and "risk_diff_ci_95" not in ra and ra["or_crude"] == 1.67
    assert set(ra["cum"]) == {"or_cum"} and "bệnh–chứng" in ra["hieu_so_khong_ap_dung"]
    assert "risk_diff" in res  # không sửa dict gốc
    assert RSA.bo_hieu_so_benh_chung({"error": "x"}) == {"error": "x"}
    lien_tuc = {"outcome_type": "continuous", "md_crude": 1.0}
    assert RSA.bo_hieu_so_benh_chung(lien_tuc) is lien_tuc


def test_engine_goi_go_hieu_so_dung_cho_benh_chung_tren_dong_thi_hanh():
    dong = [d.strip() for d in Path(RSA.__file__).read_text(encoding="utf-8").splitlines()
            if not d.strip().startswith("#")]
    i = dong.index('if design_code == "case_control":')
    assert dong[i + 1] == "res = bo_hieu_so_benh_chung(res)"


# ── 2. Bảng Poisson: RR cho RCT/thuần tập, PR cho cắt ngang ───────────────────────────────────────────────────
_PR = {"n": 100, "n_bien_co": 40, "tho": [{"variable": "nhom", "PR": 1.4, "CI_95": [1.1, 1.8], "p": 0.01}],
       "results": [{"variable": "nhom", "PR_adj": 1.39, "CI_95": [1.1, 1.75], "p": 0.005}]}


@pytest.mark.parametrize("ma, nhan, khong", [("rct", "RR HIỆU CHỈNH", "hiện mắc"), ("cohort", "RR THÔ", "hiện mắc"),
                                              ("cross_sectional", "PR HIỆU CHỈNH", "nguy cơ tương đối"),
                                              (None, "PR THÔ", "nguy cơ tương đối")])
def test_bang_poisson_goi_dung_ty_so_theo_thiet_ke(ma, nhan, khong):
    bang = RSA.format_poisson_text(_PR, ma)
    assert nhan in bang and khong not in bang and "1.39" in bang


# ── 3. Nhãn khoảng trống của G0 thuộc bộ nhãn hợp lệ (R3) ──────────────────────────────────────────────────────
def test_nhan_khoang_trong_g0_qua_luat_r3():
    van = Path(ROOT / "tools" / "run_g0_auto.py").read_text(encoding="utf-8")
    nhan = [m.group(0) for m in CDC._MARKER_WORD_RE.finditer(van.replace('"\n            "', ""))
            if "khoảng trống" in m.group(0)]
    assert nhan, "không thấy nhãn khoảng trống trong run_g0_auto"
    for t in nhan:
        assert S.is_valid_status_tag(t) or CDC._FREEFORM_CAN_RE.match(t), t


# ── 4. Đặt vấn đề G10: khoảng trống do NGƯỜI viết đi trước ────────────────────────────────────────────────────
_CPS = {"G0": {"evidence_level": "MẠNH", "pubmed_results": {"n_pmids": 30},
               "research_gaps": ["KHÔNG phát hiện khoảng trống — [CẦN — bác sĩ tự xác định khoảng trống]",
                                 "Bằng chứng mới nhất từ 2015 — có thể đã lỗi thời"]}}


def test_dat_van_de_uu_tien_khoang_trong_pi_va_bo_cau_may_con_nhan():
    van = G10.sec_datvande(_CPS, {"gate_params": {"G1": {"knowledge_gap": "Chưa có dữ liệu ở người Việt"}}})
    khoang = van.split("Khoảng trống nghiên cứu:\n\n")[1].split("\n>")[0]
    assert "Chưa có dữ liệu ở người Việt" in khoang and "[CẦN" not in khoang
    assert "Bằng chứng mới nhất từ 2015" in van  # tín hiệu máy hợp lệ vẫn giữ, dán nhãn tham khảo
    assert "(tự động từ G0)" not in van.split("Mức độ chứng cứ")[1].split("\n\n")[1]


def test_dat_van_de_khong_co_khoang_trong_nguoi_thi_giu_danh_sach_may():
    van = G10.sec_datvande(_CPS, {"gate_params": {}})
    assert "Khoảng trống nghiên cứu (tự động từ G0)" in van and "bác sĩ tự xác định" in van


# ── 5. Quyết định đặc thù thiết kế ⇒ khoá StudySpec, không khai lại ở G10 ─────────────────────────────────────
def _de_tai(tmp_path: Path, ma: str, sap: str) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    (d / "G1_checkpoint.json").write_text(json.dumps({"design": {"internal_code": ma}}), encoding="utf-8",
                                          newline="\n")
    (d / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(sap, encoding="utf-8", newline="\n")
    return d


_SAP_CHUNG = ("### §4 PHÂN TÍCH CHÍNH\n\n- **Phương pháp:** {pp}  \n- **Quần thể:** {qt}  \n\n"
              "### §5 PHÂN TÍCH ĐA BIẾN\n\n- **Giả định:** {gd}  \n\n"
              "### §6 DỮ LIỆU THIẾU\n\n- **Chiến lược:** {cl}  \n\n"
              "### §7 NHÓM\n\n- **Chiến lược chọn mẫu:** {cm}  \n\n### §9 ĐỘ NHẠY\n\n- {dn}  \n"
              "- **Dependability:** {dep}  \n\n### §10 PHẦN MỀM + SEED\n\n- **Phần mềm:** R 4.6  \n\n### §11 BẢNG\n")


def _sap(**kw: str) -> str:
    mac = dict(pp="Hồi quy logistic", qt="Phân tích đầy đủ", gd="VIF < 5", cl="MI", cm="[CẦN]", dn="Complete case",
               dep="[CẦN]")
    return _SAP_CHUNG.format(**{**mac, **kw})


def test_chan_doan_nguong_tu_sap_va_khong_ap_dung_yeu_to_nhieu(tmp_path):
    d = _de_tai(tmp_path, "diagnostic", _sap(pp="ROC, AUC, độ nhạy/đặc hiệu", gd="Ngưỡng FIB-4 1,3 và 2,67 định trước"))
    ra = QD.rut(d, STUDY, {})
    assert "2,67" in ra["design_specific"][0]["threshold"] and "SAP" in ra["design_specific"][0]["threshold"]
    assert ra["confounders"][0][0].startswith("Không áp dụng — nghiên cứu độ chính xác chẩn đoán")
    assert "R 4.6" in ra["analysis_software"][0]


def test_tong_quan_tieu_chuan_chon_cong_cu_rob_va_co_mau_khong_tinh(tmp_path):
    d = _de_tai(tmp_path, "sr_ma", _sap(pp="Random/Fixed effects meta-analysis"))
    meta = {"gate_params": {"G1": {"inclusion_criteria": ["Thử nghiệm ngẫu nhiên có đối chứng", "ĐTĐ típ 2"],
                                   "exclusion_criteria": ["Thử nghiệm bắt chéo"]}}}
    ra = QD.rut(d, STUDY, meta)
    ds = ra["design_specific"][0]
    assert "Thử nghiệm ngẫu nhiên" in ds["eligibility"] and "bắt chéo" in ds["eligibility"]
    assert ds["risk_of_bias"].startswith("RoB 2")
    assert "Không tính cỡ mẫu" in ra["sampling_sufficiency"][0]
    assert "gộp ở cấp nghiên cứu" in ra["confounders"][0][0]


@pytest.mark.parametrize("tieu_chi, ky_vong", [(["Thử nghiệm ngẫu nhiên"], "RoB 2"),
                                               (["Nghiên cứu chẩn đoán"], "QUADAS"), (["Thuần tập tiến cứu"], "ROBINS"),
                                               (["Người lớn"], None), (None, None)])
def test_cong_cu_rob_theo_loai_nghien_cuu(tieu_chi, ky_vong):
    kq = QD.cong_cu_rob(tieu_chi)
    assert (kq is None) if ky_vong is None else kq.startswith(ky_vong)


def test_dinh_tinh_chon_mau_audit_trail_va_du_lieu_thieu_khong_ap_dung(tmp_path):
    d = _de_tai(tmp_path, "qualitative", _sap(pp="Phân tích chủ đề", cm="Chọn mẫu có chủ đích đa dạng",
                                               dep="Nhật ký quyết định mã hoá"))
    ra = QD.rut(d, STUDY, {})
    assert "chủ đích" in ra["sampling_strategy"][0] and "Nhật ký" in ra["design_specific"][0]["audit_trail"]
    assert ra["missing_data_analysis"][0].startswith("Không áp dụng")  # đi TRƯỚC §6 «Chiến lược» của SAP


def test_du_bao_kiem_dinh_hieu_chuan_phan_biet_tu_sap(tmp_path):
    d = _de_tai(tmp_path, "prediction", _sap(
        pp="Hồi quy logistic, discrimination (C-statistic) + calibration (TRIPOD+AI)",
        qt="Phân tích đầy đủ; internal validation qua bootstrap", gd="Hiệu chuẩn bằng biểu đồ",
        dn="Bootstrap 500 lần để hiệu chỉnh lạc quan"))
    ds = QD.rut(d, STUDY, {})["design_specific"][0]
    assert "C-statistic" in ds["discrimination"] and "Bootstrap 500" in ds["validation"]
    assert "calibration" in ds["calibration"].lower() or "hiệu chuẩn" in ds["calibration"].lower()


def test_thuan_tap_khong_nhan_dong_khong_ap_dung(tmp_path):
    d = _de_tai(tmp_path, "cohort", _sap())
    ra = QD.rut(d, STUDY, {})
    assert "confounders" not in ra and "design_specific" not in ra


def test_studyspec_doc_ten_phang_cua_khoa_dac_thu():
    meta = {"design_code": "qualitative", "reflexivity_statement": "Người phỏng vấn không điều trị người tham gia",
            "qda_software": "NVivo 14", "index_test_threshold": "2,67"}
    ds = RS.build_study_spec(STUDY, {}, meta)["design_specific"]
    assert ds["reflexivity"].startswith("Người phỏng vấn") and ds["qda_software"] == "NVivo 14"
    assert ds["threshold"] == "2,67"


# ── 6. G8 đọc tuyên bố chia sẻ dữ liệu đã khai ở G7 ───────────────────────────────────────────────────────────
def test_g8_dung_tuyen_bo_chia_se_cua_g7_khi_chua_khai_rieng():
    tb = "Không chia sẻ dữ liệu cá nhân (dữ liệu mô phỏng); kịch bản phân tích kèm gói phát hành"
    meta = {"gate_params": {"G7": {"data_sharing_statement": tb}}}
    g8 = G8Q.g8_kem_tuyen_bo_g7(meta, {"ipd_sharing": False})
    assert g8["data_sharing_statement"] == tb and G8Q.data_sharing_issues("rct", g8)[0] == "PASS"
    assert G8Q.data_sharing_issues("rct", {"ipd_sharing": False})[0] == "REVIEW"  # trước bản vá
    rieng = {"data_sharing_statement": "Chia sẻ IPD theo yêu cầu", "ipd_sharing": True}
    assert G8Q.g8_kem_tuyen_bo_g7(meta, rieng) is rieng  # G8 đã khai ⇒ G8 thắng
    assert G8Q.g8_kem_tuyen_bo_g7({}, {}) == {}


# ── 7. SAP tổng quan–gộp có khung riêng; SAP định tính lấy quyết định G1 ─────────────────────────────────────
def _gen(ma: str, **kw):
    return G4.generate(STUDY, "Chủ đề", ma, "Thiết kế", "PRISMA 2020", 0, 0.05, 0.8, None, None, "2026-11-16", **kw)


def test_sap_tong_quan_khong_con_khuon_ca_the():
    sap = _gen("sr_ma")
    assert "### §5 TỔNG HỢP ĐỊNH LƯỢNG" in sap and "### §6 DỮ LIỆU THIẾU CẤP NGHIÊN CỨU" in sap
    for khuon_ca_the in ("Multiple Imputation", "±1 SD", "Complete case vs MI", "mice", "Biến độc lập đưa vào"):
        assert khuon_ca_the not in sap, khuon_ca_the
    assert "Multiple Imputation" in _gen("cohort")  # thiết kế cá thể giữ nguyên


def test_sap_dinh_tinh_dien_san_tiep_can_bao_hoa_chon_mau_tu_g1(tmp_path):
    khung = {"tiep_can": "Phân tích chủ đề phản tư", "bao_hoa": "Dừng khi 3 phỏng vấn liên tiếp không có mã mới",
             "chon_mau": "Chọn mẫu có chủ đích đa dạng"}
    sap = _gen("qualitative", khung=khung)
    assert "- **Tiếp cận:** Phân tích chủ đề phản tư" in sap
    assert "- **Tiêu chí bão hòa:** Dừng khi 3 phỏng vấn" in sap
    assert "- **Chiến lược chọn mẫu:** Chọn mẫu có chủ đích đa dạng" in sap
    assert "[CẦN BÁC SĨ — quy nạp" not in sap
    sap_trong = _gen("qualitative", khung={"tiep_can": "[CẦN BÁC SĨ — x]"})
    assert "[CẦN BÁC SĨ — quy nạp" in sap_trong  # khung còn ô trống ⇒ giữ ô của SAP


def test_g4_mien_epv_du_lieu_thieu_ca_the_va_seed_cho_tong_quan():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_g4_quality_gate import _checkpoint, _evaluate, _g3_checkpoint, _row  # noqa: PLC0415

    sap = _gen("sr_ma")
    for o, gia_tri in (("[CẦN THỐNG KÊ VIÊN — RR/OR/HR cho kết cục nhị phân/sống còn; MD/SMD cho liên tục]", "RR"),
                       ("[CẦN BÁC SĨ — phải ghi TRƯỚC khi xem dữ liệu]", "Loại thuốc"),
                       ("[CẦN — Bonferroni / FDR nếu >3 kết cục chính]", "Không điều chỉnh"),
                       ("[CẦN BÁC SĨ thêm kịch bản cụ thể]", "Loại nghiên cứu nguy cơ sai lệch cao"),
                       ("[CẦN — R v4.x (metafor/meta) / Stata v18 (meta) / RevMan 5.4]", "R 4.6"),
                       ("[CẦN — metafor, meta...]", "metafor 4.6")):
        assert o in sap, o
        sap = sap.replace(o, gia_tri)
    bc = _evaluate(checkpoint=_checkpoint(design_code="sr_ma"), artifact_text=sap,
                   g3_checkpoint=_g3_checkpoint(design_code="sr_ma", n_adjusted=0, confirmed_n=15,
                                                effect_val=None, effect_type=None),
                   g1_checkpoint={"design": {"internal_code": "sr_ma"}})
    assert _row(bc, "G4-AUTO-04")["status"] == "PASS" and _row(bc, "G4-AUTO-05")["status"] == "PASS"
    sap_thieu = sap.replace("liên hệ tác giả xin dữ liệu thiếu", "[CẦN — cách xử lý]")
    bc2 = _evaluate(checkpoint=_checkpoint(design_code="sr_ma"), artifact_text=sap_thieu,
                    g3_checkpoint=_g3_checkpoint(design_code="sr_ma", n_adjusted=0, confirmed_n=15,
                                                 effect_val=None, effect_type=None),
                    g1_checkpoint={"design": {"internal_code": "sr_ma"}})
    assert _row(bc2, "G4-AUTO-05")["status"] == "REVIEW"


# ── 8. G9: thử nghiệm KHÔNG chia sẻ IPD hợp lệ (ICMJE 2017 Ví dụ 4) — như G8 ─────────────────────────────────────
def test_g9_thu_nghiem_khong_chia_se_ipd_can_ly_do_va_khop_dang_ky():
    import g9_quality_gate as G9Q

    co_so = {"decision": "NOT_SHARED_WITH_JUSTIFICATION", "statement_final": True, "clinical_trial": True,
             "access_criteria": "Dữ liệu mô phỏng — không có dữ liệu người thật để chia sẻ"}
    assert G9Q._data_availability_ok({"data_availability": {**co_so, "registry_statement_consistent": True}})[0]
    assert not G9Q._data_availability_ok({"data_availability": co_so})[0]  # chưa khớp bản đăng ký
    assert not G9Q._data_availability_ok({"data_availability": {**co_so, "access_criteria": "",
                                                                "registry_statement_consistent": True}})[0]
    mo = {**co_so, "decision": "OPEN", "registry_statement_consistent": True}
    assert not G9Q._data_availability_ok({"data_availability": mo})[0]  # CÓ chia sẻ ⇒ vẫn đòi đủ trường ICMJE


# ── 9. G10: DOI không phải số điện thoại ───────────────────────────────────────────────────────────────────────
def test_g10_doi_trong_tai_lieu_tham_khao_khong_bi_coi_la_so_dien_thoai():
    import g10_quality_gate as G10Q

    assert not G10Q._co_lien_lac_ca_nhan("J Gen Intern Med. 2026. doi:10.1007/s11606-026-10477-5. PMID: 42082844.")
    assert not G10Q._co_lien_lac_ca_nhan("doi:10.2165/11633470-000000000-00000")
    assert G10Q._co_lien_lac_ca_nhan("Liên hệ: 0912 345 678") and G10Q._co_lien_lac_ca_nhan("a.b@benhvien.vn")
    # ô «1.0» + ô ngày giờ của bảng Lịch sử phiên bản (chữ hiển thị .docx nối ô bằng xuống dòng)
    assert not G10Q._co_lien_lac_ca_nhan("Người phê duyệt\n1.0\n2026-11-16 17:34\nG10 assembler")
    dong = [d.split("#")[0].strip() for d in Path(G10Q.__file__).read_text(encoding="utf-8").splitlines()
            if d.strip().startswith("if ")]
    assert "if _co_lien_lac_ca_nhan(text):" in dong and "if _co_lien_lac_ca_nhan(docx_visible):" in dong
    assert "if _EMAIL_RE.search(text) or _PHONE_RE.search(text):" not in dong


# ── 10. Nguồn giả định cỡ mẫu G3 đã chốt (cắt ngang theo độ chính xác, dự báo pmsampsize) ────────────────────
@pytest.mark.parametrize("khoa, gia_tri", [("prevalence_source", "Giả định p = 0,5 khi chưa có ước tính"),
                                           ("confirmed_n_method", "pmsampsize theo Riley 2020 (PMID 32188600)")])
def test_studyspec_nguon_gia_dinh_co_mau_tu_g3(khoa, gia_tri):
    spec = RS.build_study_spec(STUDY, {}, {"gate_params": {"G3": {khoa: gia_tri}}})
    assert spec["sample_size"]["assumptions_source"] == gia_tri


# ── 11. PMID chuẩn đề cương theo thiết kế (kiểm ở A12 trước khi G9 khoá) ──────────────────────────────────────
def test_pmid_tai_lieu_chuan_theo_thiet_ke():
    import protocol_checklist_items as PCI

    assert PCI.pmid_tai_lieu_chuan("sr_ma") == frozenset({"25554246"})
    assert PCI.pmid_tai_lieu_chuan("rct") and "25554246" not in PCI.pmid_tai_lieu_chuan("rct")
    assert PCI.pmid_tai_lieu_chuan("cohort") == frozenset() == PCI.pmid_tai_lieu_chuan("")
    assert PCI.pmid_tai_lieu_chuan() == PCI.pmid_tai_lieu_chuan("rct") | PCI.pmid_tai_lieu_chuan("sr_ma")


# ── 12. Ma trận truy xuất G10: «phơi nhiễm/yếu tố chính» theo thiết kế; công cụ định tính từ G1 ────────────────
def _ma_tran(d: Path, dong: list) -> None:
    import ma_tran_muc_tieu_bien as MT

    with (d / "_ma-tran-muc-tieu-bien.csv").open("w", encoding="utf-8", newline="") as f:
        w = __import__("csv").writer(f)
        w.writerow(["muc_tieu", "khai_niem", "vai_tro", "bien", "kieu", "cau_hoi", "cong_cu", "phan_tich_sap",
                    "ghi_chu"])
        w.writerows(dong)
    return MT


def test_du_bao_phoi_nhiem_la_bo_yeu_to_du_bao(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, "prediction", _sap())
    _ma_tran(d, [[1, "Nhập viện", "ket_cuc_chinh", "nv", "nhi_phan", "KC1", "hồ sơ", "§4", ""],
                 [1, "Tuổi", "yeu_to", "tuoi", "lien_tuc", "YT1", "hồ sơ", "§4", ""]])
    monkeypatch.setattr(QD, "ma_tran", lambda *_a: [{"khai_niem": "Tuổi", "vai_tro": "yeu_to", "bien": "tuoi"}])
    ra = QD.rut(d, STUDY, {})
    assert ra["exposure"][0] == "Yếu tố dự báo: Tuổi (`tuoi`)" and "Tuổi" in ra["confounders"][0][0]


def test_cat_ngang_mo_ta_khong_co_phoi_nhiem(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, "cross_sectional", _sap(pp="Ước lượng tỷ lệ + KTC 95% (Wilson)"))
    monkeypatch.setattr(QD, "ma_tran", lambda *_a: [{"khai_niem": "tuổi", "vai_tro": "mo_ta", "bien": "tuoi"}])
    ra = QD.rut(d, STUDY, {})
    assert ra["exposure"][0].startswith("Không áp dụng — mục tiêu mô tả tỷ lệ") and "tuổi" in ra["exposure"][0]


def test_dinh_tinh_hien_tuong_trung_tam_va_huong_dan_phong_van_tu_g1(tmp_path):
    d = _de_tai(tmp_path, "qualitative", _sap(pp="Phân tích chủ đề"))
    meta = {"gate_params": {"G1": {"central_phenomenon": "Trải nghiệm bắt đầu insulin",
                                   "data_collection_method": "Phỏng vấn sâu bán cấu trúc 45–60 phút"}}}
    ra = QD.rut(d, STUDY, meta)
    assert "Trải nghiệm bắt đầu insulin" in ra["exposure"][0]
    cc = ra["instrument"][0]
    assert "Phỏng vấn sâu bán cấu trúc" in cc["name"] and "COSMIN" in cc["note"]


# ── 13. Kịch bản R tái lặp G6 chạy được trên máy bác sĩ ────────────────────────────────────────────────────────
def test_kich_ban_r_tai_lap_bo_cot_ma_bien_hang_va_goi_tuy_chon():
    """Bảng 1 từng đưa record_id (168 mức) + biến hằng sau lọc nhóm con vào CreateTableOne ⇒ R treo > 600 giây;
    Hosmer–Lemeshow gọi thẳng library(ResourceSelection) ⇒ máy chưa cài gói thì cả kịch bản dừng."""
    import inspect

    r = RSA.generate_r_script("S", "G6_NC_nam", "nhom_ca", "nsaid_30ngay", ["chong_dong"], "binary")
    assert 'vars_all <- setdiff(vars_all, c("record_id", "study_id"' in r
    assert "length(unique(stats::na.omit(x))) > 1" in r
    assert 'requireNamespace("ResourceSelection", quietly = TRUE)' in r and "\nlibrary(ResourceSelection)" not in r
    assert "length(unique(stats::na.omit(x))) > 1" in inspect.getsource(RSA._generate_r_script_survival)


# ── 14. .sav giữ trường văn bản là BIẾN PHÂN TÍCH của đặc tả G6 (mã chủ đề định tính) ────────────────────────
def test_xuat_sav_giu_truong_van_ban_la_bien_phan_tich(tmp_path):
    import cau_noi_spss as CS

    (tmp_path / "G6_DAC_TA_SAP.json").write_text(json.dumps({"phan_tich": [
        {"id": "MT1", "vai": "chinh", "tham_so": {"loai_dac_thu": "dinh_tinh", "chu_de": "chu_de"}},
        {"id": "NC", "vai": "nhom_con", "tham_so": {"loc": "a == 1", "covariates": ["tuoi"]}}]}), encoding="utf-8",
                                                 newline="\n")
    giu = CS.bien_phan_tich_g6(tmp_path)
    assert {"chu_de", "tuoi", "dinh_tinh"} <= giu and "a == 1" not in giu
    csv_p = tmp_path / "dl.csv"
    csv_p.write_text("chu_de,ghi_chu\nSợ kim tiêm,ghi chú tự do\nChi phí,khác\n", encoding="utf-8", newline="\n")
    tieu_de, tk, _n = CS.quet_csv(csv_p)
    td = {"chu_de": {"loai": "notes"}, "ghi_chu": {"loai": "notes"}}
    ke, canh_bao, _ = CS.ke_hoach_bien(tieu_de, tk, td, [], giu_cot=giu)
    bo = {k["cot"]: k.get("bo") for k in ke}
    assert bo == {"chu_de": False, "ghi_chu": True}, bo
    assert any("chu_de" in c and "BIẾN PHÂN TÍCH" in c for c in canh_bao)
    ke0, _cb, _ = CS.ke_hoach_bien(tieu_de, tk, td, [])  # không có đặc tả G6 ⇒ hành vi cũ: bỏ cả hai trường notes
    assert {k["cot"]: k.get("bo") for k in ke0} == {"chu_de": True, "ghi_chu": True}
    assert CS.bien_phan_tich_g6(tmp_path / "khong_co") == set()
