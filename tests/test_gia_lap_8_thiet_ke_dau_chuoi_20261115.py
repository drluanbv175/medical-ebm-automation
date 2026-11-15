"""Giả lập 8 thiết kế (15/11/2026) — các lỗi ĐẦU CHUỖI (G0, G1) lộ ra khi chạy đề tài tổng hợp của 6 thiết kế mới.

Bác sĩ giao: «Hãy giả lập hoàn thiện chi tiết 8 loại thiết kế rồi từ đó vá để hệ thống đang trạng thái tự động tốt
nhất». Canary chạy dây chuyền THẬT (run_pipeline trên bản sao tạm, PI giả lập điền nội dung kịch bản) cho thuần tập,
bệnh–chứng, chẩn đoán, mô hình dự báo, tổng quan/gộp, định tính. Đo được:

- G0-AUTO-08 (đối chiếu truy vấn với PICO) kẹt đề tài CHẨN ĐOÁN và ĐỊNH TÍNH dù truy vấn PI viết đúng chuẩn: hàm so
  thuật ngữ đòi ĐỦ MỌI CHỮ của cụm dịch máy — «diagnosis» không nhận «diagnostic accuracy»[tiab], «insulin therapy»
  (từ «tiêm insulin») không nhận `insulin[tiab]`.
- G1 không có nhóm từ khoá «thuần tập/đoàn hệ/cohort»: câu hỏi tác hại luôn thành bệnh–chứng, kể cả khi tên đề tài
  tự khai «nghiên cứu thuần tập hồi cứu».
- G1 không nhận «bệnh–chứng» viết bằng gạch ngang dài (–) và tên đề tài dạng NFD.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import g0_quality_gate as G0Q  # noqa: E402
import run_g1_auto as R1  # noqa: E402

# ─────────────────────────────────────────────────────────────── G0-AUTO-08: so thuật ngữ với truy vấn PI viết

TRUY_VAN_CHAN_DOAN = ('("FIB-4"[tiab] OR "fibrosis-4"[tiab]) AND ("Non-alcoholic Fatty Liver Disease"[MeSH] OR '
                      'NAFLD[tiab]) AND ("Elasticity Imaging Techniques"[MeSH] OR elastography[tiab]) AND '
                      '("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab] OR AUROC[tiab])')


@pytest.mark.parametrize("thuat_ngu, truy_van, mong", [
    ("diagnosis", TRUY_VAN_CHAN_DOAN, True),                       # biến thể hình thái diagnostic
    ("insulin therapy", 'insulin[tiab] AND qualitative[tiab]', True),  # «therapy» là chữ chung
    ("diagnosis", 'diabetes[tiab] AND insulin[tiab]', False),      # gốc ≥5 ký tự: không khớp «diabetes»
    ("insulin therapy", 'metformin[tiab] AND qualitative[tiab]', False),
    ("therapy", 'insulin[tiab]', False),                           # cụm chỉ có chữ chung vẫn đòi đủ
    ("hypertension", 'hypertensive[tiab]', True),
    ("fracture", 'fractures[tiab]', True),
    ("satisfaction", 'satisf*[tiab]', True),                       # hành vi cũ: cắt cụt của PI
])
def test_co_trong_truy_van_bien_the_va_chu_chung(thuat_ngu, truy_van, mong):
    assert G0Q._co_trong_truy_van(thuat_ngu, truy_van) is mong


def _meta_chan_doan():
    return {"query_en": TRUY_VAN_CHAN_DOAN, "gate_params": {"G0": {
        "pico_confirmed": True,
        "population": "Người trưởng thành có gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú",
        "intervention": "Chỉ số FIB-4 (xét nghiệm cần đánh giá)",
        "primary_outcome": "Độ chính xác chẩn đoán của FIB-4 đối với xơ hoá gan tiến triển"}}}


def test_g0_auto_08_de_tai_chan_doan_truy_van_chuan_thi_dat():
    c = G0Q._tieu_chi_phu_pico({"base_query": TRUY_VAN_CHAN_DOAN}, _meta_chan_doan(),
                               {"query": TRUY_VAN_CHAN_DOAN}, {})
    assert c["status"] == "PASS", c["evidence"]


def test_g0_auto_08_van_chan_khi_truy_van_thieu_khai_niem_o():
    q = '("FIB-4"[tiab]) AND (NAFLD[tiab]) AND (elastography[tiab])'
    c = G0Q._tieu_chi_phu_pico({"base_query": q}, dict(_meta_chan_doan(), query_en=q), {"query": q}, {})
    assert c["status"] == "REVIEW" and "diagnosis" in c["evidence"], c["evidence"]


# ─────────────────────────────────────────────────────────────── G1: nhóm từ khoá thuần tập + chuẩn hoá gạch/NFC

TEN_THUAN_TAP = ("Sử dụng thuốc ức chế bơm proton kéo dài và nguy cơ gãy xương ở người từ 60 tuổi điều trị ngoại trú: "
                 "nghiên cứu thuần tập hồi cứu")


@pytest.mark.parametrize("qt, da_chot", [("harm", True), ("treatment", True), ("treatment", False)])
def test_ten_de_tai_khai_thuan_tap_thi_g1_de_xuat_cohort_va_giu_loai_cau_hoi(qt, da_chot):
    d = R1.infer_study_design(qt, {"n_sr": 3, "n_rct": 5}, TEN_THUAN_TAP, loai_cau_hoi_da_chot=da_chot)
    assert d["internal_code"] == "cohort" and "Hồi cứu" in d["primary"], d
    assert d["resolved_question_type"] == qt  # «cohort» là cụm khai thiết kế, không phải loại câu hỏi


def test_cau_hoi_tac_hai_khong_khai_thiet_ke_van_la_benh_chung():
    d = R1.infer_study_design("harm", {}, "NSAID và xuất huyết tiêu hoá trên ở người cao tuổi",
                              loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "case_control"


def test_chan_doan_lay_mau_thuan_tap_van_la_chan_doan():
    d = R1.infer_study_design("diagnosis", {}, "Giá trị chẩn đoán của FIB-4 trong một thuần tập ngoại trú",
                              loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "diagnostic"


@pytest.mark.parametrize("ten", ["NSAID và xuất huyết tiêu hoá: nghiên cứu bệnh–chứng lồng trong thuần tập",
                                 "NSAID và xuất huyết tiêu hoá: nghiên cứu bệnh—chứng lồng trong thuần tập"])
def test_gach_ngang_dai_benh_chung_long_trong_thuan_tap_la_benh_chung(ten):
    d = R1.infer_study_design("harm", {}, ten, loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "case_control", d["primary"]


def test_ten_de_tai_nfd_van_khop_tu_khoa():
    d = R1.infer_study_design("harm", {}, unicodedata.normalize("NFD", TEN_THUAN_TAP), loai_cau_hoi_da_chot=True)
    assert d["internal_code"] == "cohort"


def test_kiem_nhat_quan_ten_de_tai_canh_bao_cohort_dung_cho():
    assert R1.check_topic_design_consistency(TEN_THUAN_TAP, "cohort") == []
    assert any("'cohort'" in w for w in R1.check_topic_design_consistency(TEN_THUAN_TAP, "case_control"))
    # khung lấy mẫu thuần tập của nghiên cứu chẩn đoán/dự báo/tổng quan không phải mâu thuẫn
    for tk in ("diagnostic", "prediction", "sr_ma"):
        assert not any("'cohort'" in w for w in R1.check_topic_design_consistency(TEN_THUAN_TAP, tk)), tk


# ─────────────────────────────── G0-AUTO-08: can thiệp «Tin nhắn SMS…» chỉ ánh xạ thuật ngữ phụ (thuốc hạ áp)
TRUY_VAN_RCT = ('("text messaging"[tiab] OR "text message"[tiab] OR SMS[tiab] OR "Text Messaging"[MeSH]) AND '
                '(hypertension[MeSH] OR hypertension[tiab]) AND (adherence[tiab] OR "blood pressure"[tiab])')


def _meta_rct(**g0):
    base = {"pico_confirmed": True,
            "population": "Người trưởng thành ≥18 tuổi tăng huyết áp đang dùng thuốc hạ áp, quản lý ngoại trú",
            "intervention": "Tin nhắn SMS tự động nhắc uống thuốc hạ áp hằng ngày kèm chăm sóc thường quy",
            "primary_outcome": "Tỷ lệ người bệnh đạt kiểm soát huyết áp"}
    base.update(g0)
    return {"query_en": TRUY_VAN_RCT, "gate_params": {"G0": base}}


def test_g0_auto_08_rct_tin_nhan_sms_truy_van_pi_phu_dung_thi_dat():
    c = G0Q._tieu_chi_phu_pico({"base_query": TRUY_VAN_RCT}, _meta_rct(), {"query": TRUY_VAN_RCT}, {})
    assert c["status"] == "PASS", c["evidence"]


def test_g0_auto_08_nhac_tin_nhan_khong_co_chu_sms_van_nhan_qua_tu_dien():
    m = _meta_rct(intervention="Tin nhắn tự động nhắc uống thuốc hạ áp hằng ngày")
    c = G0Q._tieu_chi_phu_pico({"base_query": TRUY_VAN_RCT}, m, {"query": TRUY_VAN_RCT}, {})
    assert c["status"] == "PASS", c["evidence"]


def test_thuat_ngu_latin_khong_tao_nghia_vu_moi_cho_truy_van_pi_tu_viet():
    """Khái niệm không có thuật ngữ từ điển mà chỉ có mã ICD: truy vấn PI tự viết không bị chặn vì mã đó."""
    q = '(sms[tiab]) AND (adherence[tiab])'
    m = _meta_rct(population="Người bệnh ICD-10 I10 tại phòng khám", intervention="Tin nhắn SMS nhắc thuốc")
    c = G0Q._tieu_chi_phu_pico({"base_query": q}, dict(m, query_en=q), {"query": q}, {})
    assert "I10" not in c["evidence"], c["evidence"]


def test_thuat_ngu_latin_rut_dung_token():
    assert G0Q._thuat_ngu_latin("Tin nhắn SMS tự động") == ["SMS"]
    assert G0Q._thuat_ngu_latin("NT-proBNP (log), eGFR, NYHA, BMI") == ["NT-proBNP", "eGFR", "NYHA"]
    assert G0Q._thuat_ngu_latin("Người bệnh có thẻ BHYT") == ["BHYT"]
    assert G0Q._thuat_ngu_latin("Chăm sóc thường quy") == []


def test_g0_auto_08_chi_token_latin_cuu_khi_tu_dien_rut_thuat_ngu_phu():
    """I = «Nhắc uống thuốc hạ áp qua SMS»: từ điển chỉ rút «antihypertensive agents» (vắng truy vấn) — «SMS» PI viết
    sẵn trong PICO và có trong truy vấn ⇒ đạt."""
    m = _meta_rct(intervention="Nhắc uống thuốc hạ áp qua SMS hằng ngày")
    c = G0Q._tieu_chi_phu_pico({"base_query": TRUY_VAN_RCT}, m, {"query": TRUY_VAN_RCT}, {})
    assert c["status"] == "PASS", c["evidence"]
