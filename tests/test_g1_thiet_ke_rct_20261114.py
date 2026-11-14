# -*- coding: utf-8 -*-
"""Vá K1 (+K11) của giả lập đề tài RCT 14/11/2026 — G1 không được ghi đè loại câu hỏi PI đã chốt ở G0 bằng từ khoá.

Bằng chứng giả lập: đề tài «Hiệu quả của tin nhắn nhắc uống thuốc … lên TỶ LỆ kiểm soát huyết áp …: thử nghiệm lâm
sàng ngẫu nhiên có đối chứng», PI chốt G0 question_type=treatment; chữ «tỷ lệ» khớp nhóm "descriptive" nên G1 dựng
cắt ngang (STROBE, N theo độ chính xác 0,5, SAP 12 mục), G1-AUTO-02d chỉ REVIEW, R6 còn cảnh báo sai chiều khi PI đã
ghim rct. Thứ tự ưu tiên sau vá: thiết kế PI ghim > loại câu hỏi PI chốt ở G0 > từ khoá tên đề tài. Ngoại tuyến.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import g1_quality_gate as G1Q  # noqa: E402
import run_g1_auto as G1  # noqa: E402
from test_g1_hoan_thien_20261004 import _chay_main  # noqa: E402
from test_g1_quality_gate import _build_case, _design, _evaluate  # noqa: E402

# Chủ đề NGUYÊN VĂN của đề tài giả ZZSIM-RCT-NHAC-THUOC-THA-20261114 (không người thật, không PII).
CHU_DE_GIA_LAP = ("Hiệu quả của tin nhắn nhắc uống thuốc so với chăm sóc thường quy lên tỷ lệ kiểm soát huyết áp sau "
                  "6 tháng ở người tăng huyết áp điều trị ngoại trú: thử nghiệm lâm sàng ngẫu nhiên có đối chứng")
# Cùng câu hỏi nhưng KHÔNG tự khai thiết kế — chỉ còn «tỷ lệ» làm mồi.
CHU_DE_KHONG_KHAI_RCT = ("Hiệu quả của tin nhắn nhắc uống thuốc so với chăm sóc thường quy lên tỷ lệ kiểm soát huyết "
                         "áp ở người tăng huyết áp điều trị ngoại trú")
# Kiểu chủ đề của nhánh C1a (cắt ngang mô tả + yếu tố liên quan) — không được hồi quy.
CHU_DE_KIEU_C1A = "Tỷ lệ hài lòng của người bệnh ngoại trú và một số yếu tố liên quan tại bệnh viện quân y"

# Nền bằng chứng G0 của đề tài giả ở lượt 4 (27 SR/MA, 70 RCT — nhánh «bão hoà» của câu hỏi điều trị).
_PM_GIA_LAP = {"total_found": 44, "n_pmids": 44, "all_pmids": [], "n_sr": 27, "n_rct": 70, "n_guideline": 0,
               "n_observational": 0, "n_recent": 0, "counts_are_real": True, "counts_unavailable": []}
_PM_TRONG = {**_PM_GIA_LAP, "total_found": 0, "n_pmids": 0, "n_sr": 0, "n_rct": 0}


def _row(r, tid):
    return next(c for c in r["automatic_criteria"] + r["human_criteria"] if c["id"] == tid)


# ── (1) Đường thật: run_g1_auto.main() với G0 đã chốt ──────────────────────────────────────────────────────────────
def test_k1_de_tai_gia_lap_g0_treatment_ra_rct_khong_ra_cat_ngang(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "treatment"},
                       g0_ghi_de={"topic": CHU_DE_GIA_LAP, "pubmed_results": _PM_GIA_LAP})
    assert cp["question_type"] == "treatment", cp["question_type"]
    assert cp["design"]["internal_code"] == "rct", cp["design"]
    assert "CONSORT" in cp["design"]["reporting_standard"]
    assert cp["design"]["ambiguous"] is False
    assert cp["dac_ta_thiet_ke"]["question_type"] == "treatment"
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=False)
    assert _row(r, "G1-AUTO-02d")["status"] == "PASS", _row(r, "G1-AUTO-02d")
    # K11: R6 không còn cảnh báo «gợi ý cross_sectional» cho đề tài tự khai RCT (R6 chỉ là cảnh báo, không vào
    # checkpoint — kiểm thẳng hàm guardrail trên đúng artifact A2 vừa sinh).
    a2 = (d / "G1_A2_PROTOCOL_DESIGN_TEST-G1-MAIN.md").read_text(encoding="utf-8")
    canh_bao = G1.guardrail_check_g1(a2, [], topic=CHU_DE_GIA_LAP, internal_code="rct")["warnings"]
    assert not [w for w in canh_bao if w.startswith("R6 ⚠️")], canh_bao


def test_k1_g0_treatment_khong_khai_rct_van_khong_bao_gio_ha_thanh_cat_ngang(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "therapy"},
                       g0_ghi_de={"topic": CHU_DE_KHONG_KHAI_RCT, "pubmed_results": _PM_GIA_LAP})
    assert cp["question_type"] == "treatment"
    assert cp["design"]["internal_code"] in G1Q.thiet_ke_hop_le_theo_cau_hoi("treatment"), cp["design"]
    assert cp["design"]["internal_code"] != "cross_sectional"
    # Máy không lặng lẽ: từ khoá bị bỏ qua phải nằm trong checkpoint.
    bo_qua = cp["design"].get("tu_khoa_bi_bo_qua") or []
    assert bo_qua and "cross_sectional" in bo_qua[0] and "treatment" in bo_qua[0], bo_qua
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=False)
    assert _row(r, "G1-AUTO-02d")["status"] == "PASS"


def test_k1_nhanh_c1a_cat_ngang_khong_hoi_quy(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"},
                       g0_ghi_de={"topic": CHU_DE_KIEU_C1A, "pubmed_results": _PM_TRONG})
    assert cp["question_type"] == "descriptive" and cp["design"]["internal_code"] == "cross_sectional"
    assert not cp["design"].get("tu_khoa_bi_bo_qua")
    assert _row(G1Q.evaluate_study("TEST-G1-MAIN", d, write=False), "G1-AUTO-02d")["status"] == "PASS"


def test_k1_ghim_cua_pi_van_thang_loai_cau_hoi_g0(tmp_path, monkeypatch):
    """PI ghim thiết kế (kể cả trái loại câu hỏi G0) ⇒ dùng đúng pin; từ khoá bỏ qua không in/ghi nữa."""
    import json
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "treatment"},
                      g0_ghi_de={"topic": CHU_DE_KHONG_KHAI_RCT, "pubmed_results": _PM_GIA_LAP})
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["design_code"] = "rct"
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    _, cp = _chay_main(tmp_path, monkeypatch)
    assert cp["design"]["internal_code"] == "rct" and not cp["design"].get("tu_khoa_bi_bo_qua")


# ── (2) Thứ tự ưu tiên ở infer_study_design ─────────────────────────────────────────────────────────────────────────
_KHONG_BAO_HOA = {"n_sr": 0, "n_rct": 0}


@pytest.mark.parametrize("qt,chu_de,ky_vong", [
    # Câu hỏi can thiệp: cụm chủ đề/kết cục không đổi được thiết kế (trước: «tử vong» ⇒ cohort, «tỷ lệ» ⇒ cắt ngang).
    ("treatment", "Hiệu quả của thuốc X lên tỷ lệ tử vong ở bệnh nhân suy tim", "rct"),
    ("treatment", "Chương trình nhắc tái khám và tỷ lệ kiểm soát đường huyết", "rct"),
    # Cụm KHAI THIẾT KẾ hợp với câu hỏi can thiệp vẫn được tinh chỉnh.
    ("treatment", "Tổng quan hệ thống hiệu quả của thuốc X lên tỷ lệ tử vong", "sr_ma"),
    ("treatment", "Yếu tố nguy cơ nhiễm khuẩn vết mổ: nghiên cứu bệnh-chứng", "case_control"),
    # Tinh chỉnh trong nhóm hợp lệ của loại câu hỏi khác (giữ hành vi cũ).
    ("prognosis", "Xây dựng mô hình dự đoán tái nhập viện ở bệnh nhân suy tim", "prediction"),
    ("descriptive", "Trải nghiệm người bệnh khi dùng insulin: nghiên cứu định tính phỏng vấn sâu", "qualitative"),
    ("harm", CHU_DE_KIEU_C1A, "cross_sectional"),
    ("descriptive", CHU_DE_KIEU_C1A, "cross_sectional"),
    # PI chốt mô tả mà tên đề tài nói thử nghiệm ⇒ lựa chọn PI thắng (R6 vẫn cảnh báo để PI soát).
    ("descriptive", "Thử nghiệm ngẫu nhiên có đối chứng về tỷ lệ tuân thủ thuốc", "cross_sectional"),
    # Loại câu hỏi không có bảng (sr) ⇒ giữ nguyên lựa chọn PI.
    ("sr", "Tỷ lệ tăng huyết áp ở người cao tuổi", "sr_ma"),
])
def test_k1_loai_cau_hoi_da_chot_dung_tren_tu_khoa(qt, chu_de, ky_vong):
    d = G1.infer_study_design(qt, _KHONG_BAO_HOA, chu_de, loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == ky_vong, (qt, chu_de, d["internal_code"], d["tu_khoa_bi_bo_qua"])
    hop_le = G1Q.thiet_ke_hop_le_theo_cau_hoi(qt)
    if hop_le:
        assert d["internal_code"] in hop_le, "thiết kế suy ra phải luôn qua được G1-AUTO-02d"


def test_k1_chua_chot_thi_tu_khoa_van_doi_loai_cau_hoi_nhu_cu():
    """Không chốt (mặc định «treatment») ⇒ hành vi cũ: từ khoá đổi loại câu hỏi (G1 gắn cờ mơ hồ ở main)."""
    d = G1.infer_study_design("treatment", _KHONG_BAO_HOA, CHU_DE_KIEU_C1A)
    assert d["internal_code"] == "cross_sectional" and d["tu_khoa_bi_bo_qua"] == []


# ── (3) Nhóm từ khoá RCT ────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("chu_de", [
    CHU_DE_GIA_LAP,
    "Hiệu quả của bài tập thở lên chất lượng sống: thử nghiệm ngẫu nhiên",
    "Phân bổ ngẫu nhiên bệnh nhân đái tháo đường vào hai chế độ theo dõi đường huyết",
    "A randomized controlled trial of text-message reminders for hypertension",
    "Effect of salt substitution on stroke: a randomised trial",
    "RCT so sánh hai phác đồ diệt Helicobacter pylori",
])
def test_k1_tu_khoa_rct_nhan_ra_de_tai_tu_khai_thu_nghiem(chu_de):
    d = G1.infer_study_design("treatment", {"n_sr": 27, "n_rct": 70}, chu_de)
    assert d["internal_code"] == "rct" and d["ambiguous"] is False, (chu_de, d["internal_code"])
    assert d["resolved_question_type"] == "treatment"


@pytest.mark.parametrize("chu_de,ky_vong", [
    # «chọn mẫu ngẫu nhiên» là cách CHỌN MẪU của khảo sát cắt ngang, không phải phân bổ ngẫu nhiên.
    ("Khảo sát tỷ lệ tăng huyết áp ở người cao tuổi, chọn mẫu ngẫu nhiên phân tầng", "cross_sectional"),
    # Phủ định: không ngẫu nhiên / non-randomized ⇒ không dựng RCT.
    ("Thử nghiệm lâm sàng không ngẫu nhiên đánh giá tỷ lệ tuân thủ điều trị", "cross_sectional"),
    ("A non-randomized controlled trial: prevalence of adherence", "cross_sectional"),
    # Tổng quan các thử nghiệm ngẫu nhiên vẫn là SR/MA; mô hình dự đoán từ dữ liệu thử nghiệm vẫn là prediction.
    ("Tổng quan hệ thống và phân tích gộp các thử nghiệm ngẫu nhiên về statin", "sr_ma"),
    ("Mô hình dự đoán biến cố tim mạch xây dựng từ dữ liệu thử nghiệm lâm sàng", "prediction"),
])
def test_k1_tu_khoa_rct_khong_bat_nham(chu_de, ky_vong):
    d = G1.infer_study_design("treatment", _KHONG_BAO_HOA, chu_de)
    assert d["internal_code"] == ky_vong, (chu_de, d["internal_code"])


# ── (4) R6 — K11 cảnh báo sai chiều ─────────────────────────────────────────────────────────────────────────────────
def test_k11_r6_khong_canh_bao_cat_ngang_khi_de_tai_tu_khai_rct_va_da_chon_rct():
    assert G1.check_topic_design_consistency(CHU_DE_GIA_LAP, "rct") == []


def test_k11_r6_van_canh_bao_khi_de_tai_khai_rct_ma_thiet_ke_khac():
    warns = G1.check_topic_design_consistency(CHU_DE_GIA_LAP, "cross_sectional")
    assert len(warns) == 1 and "'rct'" in warns[0], warns


def test_k11_r6_van_canh_bao_mau_thuan_that_rct_kem_benh_chung():
    warns = G1.check_topic_design_consistency("Thử nghiệm ngẫu nhiên lồng trong nghiên cứu bệnh-chứng", "rct")
    assert any("case_control" in w for w in warns), warns


# ── (5) G1-AUTO-02d: lệch loại câu hỏi G0 ⇒ BLOCK khi PI chưa ghim ─────────────────────────────────────────────────
def _thiet_ke_cat_ngang():
    return _design(internal_code="cross_sectional", primary="Cắt ngang mô tả", reporting_standard="STROBE",
                   protocol_standard="STROBE (không có chuẩn protocol bắt buộc)")


def test_k1_02d_anh_chup_luot4_chua_ghim_la_block(tmp_path):
    """Tái hiện ảnh chụp lượt 4: G0 treatment, G1 do máy suy cross_sectional, PI chưa ghim ⇒ CHẶN."""
    meta = {"gate_params": {"G0": {"question_type": "treatment"}}}
    r = _evaluate(_build_case(tmp_path, meta=meta, design_value=_thiet_ke_cat_ngang()))
    a2d = _row(r, "G1-AUTO-02d")
    assert a2d["status"] == "BLOCK", a2d
    assert "PI chưa ghim" in a2d["evidence"] and "treatment" in a2d["evidence"]
    assert r["status"] == G1Q.STATUS_BLOCKED


def test_k1_02d_pi_da_ghim_thiet_ke_lech_thi_chi_review(tmp_path):
    """Quyết định tường minh của PI không bị hạ thành CHẶN (PI giải trình nếu cố ý)."""
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": {"question_type": "treatment"}}}
    a2d = _row(_evaluate(_build_case(tmp_path, meta=meta, design_value=_thiet_ke_cat_ngang())), "G1-AUTO-02d")
    assert a2d["status"] == "REVIEW" and "PI đã ghim" in a2d["evidence"], a2d


def test_k1_02d_ghim_khong_khop_thiet_ke_dang_dung_khong_tinh_la_da_ghim(tmp_path):
    meta = {"design_code": "rct", "gate_params": {"G0": {"question_type": "treatment"}}}
    a2d = _row(_evaluate(_build_case(tmp_path, meta=meta, design_value=_thiet_ke_cat_ngang())), "G1-AUTO-02d")
    assert a2d["status"] == "BLOCK", a2d


def test_k1_02d_hop_loai_cau_hoi_van_pass(tmp_path):
    meta = {"gate_params": {"G0": {"question_type": "therapy"}}}
    assert _row(_evaluate(_build_case(tmp_path, meta=meta)), "G1-AUTO-02d")["status"] == "PASS"


def test_bang_thiet_ke_hop_le_mot_nguon():
    assert G1Q.thiet_ke_hop_le_theo_cau_hoi("therapy") == G1Q._THIET_KE_HOP_LE_THEO_CAU_HOI["treatment"]
    assert G1Q.thiet_ke_hop_le_theo_cau_hoi(None) == frozenset()
    assert G1Q.thiet_ke_hop_le_theo_cau_hoi("sr") == frozenset()


# ── (6) Sửa theo thẩm định PR #246 ─────────────────────────────────────────────────────────────────────────────────
# (6a) Phủ định có chữ chen giữa / một nhánh / non-RCT / Mendel: không dựng RCT im lặng.
CHU_DE_KHONG_PHAN_BO = ("Hiệu quả của chương trình tư vấn dùng thuốc lên tỷ lệ kiểm soát huyết áp: thử nghiệm có nhóm "
                        "chứng không phân bổ ngẫu nhiên")


@pytest.mark.parametrize("chu_de", [
    CHU_DE_KHONG_PHAN_BO,
    "Thử nghiệm lâm sàng không được phân bổ ngẫu nhiên về hai phác đồ insulin",
    "thu nghiem lam sang khong phan bo ngau nhien ve hai phac do insulin",
    "A non-RCT comparison of two dressing strategies after surgery",
    "Thử nghiệm lâm sàng pha II một nhánh thuốc X ở ung thư gan",
    "A single-arm clinical trial of drug X in hepatocellular carcinoma",
    "Thử nghiệm lâm sàng không có nhóm đối chứng về liệu pháp Y",
    "Mendelian randomization: LDL cholesterol và bệnh mạch vành",
    "Ngẫu nhiên hoá Mendel: chỉ số khối cơ thể và đái tháo đường",
])
@pytest.mark.parametrize("gaps", [_KHONG_BAO_HOA, {"n_sr": 27, "n_rct": 70}])
def test_ps246_phu_dinh_rct_khong_dung_rct_im_lang(chu_de, gaps):
    tl = chu_de.lower()
    assert G1._khop_nhom_tu_khoa("rct", tl) is False, chu_de
    d = G1.infer_study_design("treatment", gaps, chu_de, loai_cau_hoi_da_chot=True)
    # Thiết kế thật ngoài 8 mã ⇒ mọi lựa chọn của máy chỉ là đoán: phải MƠ HỒ (G1-AUTO-04 REVIEW), kể cả khi nhánh
    # «chưa có RCT» (0 SR/0 RCT) trả RCT.
    assert d["ambiguous"] is True, (chu_de, gaps, d["internal_code"])
    assert "KHÔNG ngẫu nhiên" in d["rationale"]
    assert any("KHÔNG ngẫu nhiên" in w for w in G1.check_topic_design_consistency(chu_de, d["internal_code"]))


@pytest.mark.parametrize("chu_de", [
    # Không nói tới thử nghiệm ⇒ «không có nhóm chứng» không phải tín hiệu thiết kế.
    "Tỷ lệ tăng huyết áp ở người cao tuổi: nghiên cứu cắt ngang không có nhóm chứng",
    # «không chứng minh» không phải phủ định thiết kế.
    "Thử nghiệm ngẫu nhiên có đối chứng: vì sao các nghiên cứu trước không chứng minh được lợi ích của thuốc X",
])
def test_ps246_phu_dinh_khong_bat_nham(chu_de):
    tl = chu_de.lower()
    assert G1._khai_thiet_ke_khong_ngau_nhien(tl) is False, chu_de
    assert not [w for w in G1.check_topic_design_consistency(chu_de, "cross_sectional") if "KHÔNG ngẫu nhiên" in w]


def test_ps246_main_de_tai_khong_phan_bo_ngau_nhien_khong_qua_im_lang(tmp_path, monkeypatch):
    """Tái hiện đúng ca thẩm định qua main(): G0 treatment + «… không phân bổ ngẫu nhiên», nền 0 SR/0 RCT.

    Trước: internal=rct, CONSORT, ambiguous=False, R6 im lặng. Sau: MƠ HỒ ⇒ G1-AUTO-04 REVIEW, R6 cảnh báo."""
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "treatment"},
                       g0_ghi_de={"topic": CHU_DE_KHONG_PHAN_BO, "pubmed_results": _PM_TRONG})
    assert cp["design"]["ambiguous"] is True, cp["design"]
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=False)
    assert _row(r, "G1-AUTO-04")["status"] == "REVIEW", _row(r, "G1-AUTO-04")
    a2 = (d / "G1_A2_PROTOCOL_DESIGN_TEST-G1-MAIN.md").read_text(encoding="utf-8")
    canh_bao = G1.guardrail_check_g1(a2, [], topic=CHU_DE_KHONG_PHAN_BO,
                                     internal_code=cp["design"]["internal_code"])["warnings"]
    assert [w for w in canh_bao if w.startswith("R6 ⚠️") and "KHÔNG ngẫu nhiên" in w], canh_bao


# (6b) Chỉ cụm CHUNG «thử nghiệm lâm sàng» ⇒ vẫn RCT nhưng MƠ HỒ; khai ngẫu nhiên (cụm hay «ngẫu nhiên» trơn) ⇒ rõ.
@pytest.mark.parametrize("chu_de,mo_ho", [
    ("Hiệu quả của thuốc X lên tỷ lệ tử vong ở bệnh nhân suy tim: thử nghiệm lâm sàng đa trung tâm", True),
    ("Effect of drug X on mortality in heart failure: a controlled trial", True),
    # «chọn mẫu ngẫu nhiên» là cách chọn mẫu, không phải phân bổ ⇒ vẫn chỉ là cụm chung.
    ("Thử nghiệm lâm sàng thuốc X ở người suy tim, chọn mẫu ngẫu nhiên từ sổ đăng ký", True),
    ("Hiệu quả của thuốc X lên tỷ lệ tử vong: thử nghiệm lâm sàng đa trung tâm, mù đôi, ngẫu nhiên", False),
    (CHU_DE_GIA_LAP, False),
    ("A randomized clinical trial of drug X in heart failure", False),
])
@pytest.mark.parametrize("gaps", [_KHONG_BAO_HOA, {"n_sr": 27, "n_rct": 70}])
def test_ps246_rct_chi_cum_chung_thi_mo_ho(chu_de, mo_ho, gaps):
    d = G1.infer_study_design("treatment", gaps, chu_de, loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "rct", (chu_de, d["internal_code"])
    assert d["ambiguous"] is mo_ho, (chu_de, gaps, d["ambiguous"])


# (6c) G0 prediction_model: đối chiếu từ khoá theo ĐÚNG loại G1-AUTO-02d dùng, không theo «prognosis» đã hạ.
CHU_DE_SR_MO_HINH = "Tổng quan hệ thống các mô hình dự đoán tái nhập viện ở bệnh nhân suy tim"


def test_ps246_g0_prediction_model_kem_tong_quan_van_qua_02d(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "prediction_model"},
                       g0_ghi_de={"topic": CHU_DE_SR_MO_HINH, "pubmed_results": _PM_TRONG})
    assert cp["design"]["internal_code"] in G1Q.thiet_ke_hop_le_theo_cau_hoi("prediction_model"), cp["design"]
    bo_qua = cp["design"].get("tu_khoa_bi_bo_qua") or []
    assert bo_qua and "sr_ma" in bo_qua[0] and "prediction_model" in bo_qua[0], bo_qua
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=False)
    assert _row(r, "G1-AUTO-02d")["status"] == "PASS", _row(r, "G1-AUTO-02d")


def test_ps246_infer_loai_doi_chieu_tach_khoi_loai_dung_noi_dung():
    d = G1.infer_study_design("prognosis", _KHONG_BAO_HOA, CHU_DE_SR_MO_HINH, loai_cau_hoi_da_chot=True,
                              loai_cau_hoi_doi_chieu="prediction_model")
    assert d["internal_code"] == "prediction", d["internal_code"]
    # Vắng loại đối chiếu ⇒ như cũ (đối chiếu theo chính question_type).
    assert G1.infer_study_design("prognosis", _KHONG_BAO_HOA, CHU_DE_SR_MO_HINH,
                                 loai_cau_hoi_da_chot=True)["internal_code"] == "sr_ma"


# (6d) Loại câu hỏi «sr» (không có bảng 02d): không còn cảnh báo giả viện dẫn G1-AUTO-02d.
def test_ps246_sr_tong_quan_khong_ghi_tu_khoa_bi_bo_qua():
    d = G1.infer_study_design("sr", _KHONG_BAO_HOA, "Tổng quan hệ thống hiệu quả của thuốc X lên tỷ lệ tử vong",
                              loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "sr_ma" and d["tu_khoa_bi_bo_qua"] == [], d["tu_khoa_bi_bo_qua"]


def test_ps246_sr_nhom_khac_ghi_ly_do_khong_vien_dan_02d():
    d = G1.infer_study_design("sr", _KHONG_BAO_HOA, "Tỷ lệ tăng huyết áp ở người cao tuổi", loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "sr_ma"
    assert len(d["tu_khoa_bi_bo_qua"]) == 1 and "G1-AUTO-02d" not in d["tu_khoa_bi_bo_qua"][0], d["tu_khoa_bi_bo_qua"]
    assert "«sr»" in d["tu_khoa_bi_bo_qua"][0]


def test_ps246_main_g0_sr_khong_ghi_tu_khoa_bi_bo_qua(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "sr"},
                       g0_ghi_de={"topic": "Tổng quan hệ thống và phân tích gộp hiệu quả của statin",
                                  "pubmed_results": _PM_TRONG})
    assert cp["design"]["internal_code"] == "sr_ma"
    assert "tu_khoa_bi_bo_qua" not in cp["design"], cp["design"].get("tu_khoa_bi_bo_qua")


# (6e) Chốt CÓ CHỦ Ý hành vi khi G0 CHƯA chốt loại câu hỏi: nhóm "rct" mới đứng trước diagnosis/descriptive nên hai ca
# dưới đổi so với trước bản vá (diagnostic → rct; cross_sectional → rct) — nhưng chỉ có cụm chung «thử nghiệm lâm
# sàng» nên MƠ HỒ (G1-AUTO-04 REVIEW), cộng cờ mơ hồ «G0 chưa chốt» ở main() và G1-AUTO-01 giữ G1.
@pytest.mark.parametrize("chu_de", [
    "Giá trị NT-proBNP trong chẩn đoán suy tim: thử nghiệm lâm sàng",
    "Khảo sát kiến thức của điều dưỡng về thử nghiệm lâm sàng",
])
def test_ps246_chua_chot_nhom_rct_doi_ket_qua_co_chu_y_va_mo_ho(chu_de):
    d = G1.infer_study_design("treatment", _KHONG_BAO_HOA, chu_de)
    assert d["internal_code"] == "rct" and d["ambiguous"] is True, (chu_de, d["internal_code"], d["ambiguous"])
