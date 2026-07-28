"""Test cho 2 lỗi thật do bình duyệt độc lập agent `dao-duc-dang-ky` phát hiện
(2026-07-17, đề tài khảo sát hài lòng bệnh nhân C1a, BVQY175) trong
tools/run_g2_auto.py::generate_g2_full_package():

1. Bảng "TỔNG QUAN G2" (dòng đầu tài liệu) tự tính RIÊNG một biến
   `irb_required = "BẮT BUỘC" if design_code == "rct" else "KHUYẾN KHÍCH"`,
   KHÔNG dùng chung risk["registration"] (nguồn đã vá đúng điều kiện Helsinki
   §35 — xem test_g2_helsinki_registration_timing.py). Hậu quả: mục ĐĂNG KÝ
   NGHIÊN CỨU chi tiết trong CÙNG tài liệu nói "BẮT BUỘC nếu tiến cứu..."
   nhưng bảng tóm tắt ở đầu lại nói trơn "KHUYẾN KHÍCH" — mâu thuẫn nội bộ
   ngay trong 1 file, dễ khiến bác sĩ đọc lướt bảng tóm tắt rồi bỏ qua đăng
   ký. Test khóa: 2 vị trí phải dùng CHUNG một nguồn, không thể lệch nhau.

2. ICF (TÀI LIỆU 4) LUÔN in sẵn "Bước 3: lấy 5 mL máu tĩnh mạch" + "Bước 4:
   tái khám sau 3-6 tháng" + lợi ích "tiếp cận thuốc/can thiệp mới" cho MỌI
   thiết kế — kể cả khảo sát cắt ngang một lần, không xâm lấn, không can
   thiệp. Nguy cơ: bác sĩ chỉ điền chỗ trống theo mẫu mà quên XÓA các dòng
   không áp dụng, ICF cuối cùng ngụ ý sai bản chất nghiên cứu. Test khóa:
   các dòng lấy máu/tái khám CHỈ xuất hiện cho thiết kế thật sự có thể có lấy
   mẫu sinh học/theo dõi nhiều lần (rct, cohort) — KHÔNG cho cross_sectional/
   case_control/diagnostic/sr_ma.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g2_auto import RISK_PROFILES, generate_g2_full_package  # noqa: E402


def _gen(design_code, design_primary="Thiết kế test"):
    risk = RISK_PROFILES[design_code]
    return generate_g2_full_package(
        topic="Đề tài test", study_name="TEST-STUDY", design_code=design_code,
        design_primary=design_primary, reporting_std="STROBE", n_sr=5, n_rct=0,
        evidence_level="TRUNG BÌNH", registry=None, risk=risk,
        run_date="2026-07-17", n_adjusted=1000,
    )


def _summary_table_block(doc: str) -> str:
    return doc.split("TỔNG QUAN G2")[1].split("TÀI LIỆU 1")[0]


class TestSummaryTableUsesSameRegistrationSource:
    """Hồi quy trực tiếp: bảng tóm tắt và mục chi tiết PHẢI thống nhất."""

    def test_cross_sectional_summary_not_bare_khuyen_khich(self):
        doc = _gen("cross_sectional")
        summary = _summary_table_block(doc)
        assert "KHUYẾN KHÍCH" not in summary, (
            "Bảng TỔNG QUAN vẫn in 'KHUYẾN KHÍCH' trơn cho cross_sectional — "
            "đúng bug mâu thuẫn với mục ĐĂNG KÝ NGHIÊN CỨU chi tiết"
        )
        assert "BẮT BUỘC" in summary

    def test_cohort_summary_matches_detailed_registration_text(self):
        doc = _gen("cohort")
        summary = _summary_table_block(doc)
        assert RISK_PROFILES["cohort"]["registration"] in summary

    def test_case_control_summary_matches_detailed_registration_text(self):
        doc = _gen("case_control")
        summary = _summary_table_block(doc)
        assert RISK_PROFILES["case_control"]["registration"] in summary

    def test_rct_summary_still_says_bat_buoc(self):
        doc = _gen("rct")
        summary = _summary_table_block(doc)
        assert "BẮT BUỘC" in summary

    def test_srma_summary_matches_detailed_registration_text(self):
        doc = _gen("sr_ma")
        summary = _summary_table_block(doc)
        assert RISK_PROFILES["sr_ma"]["registration"] in summary


class TestICFStepsDesignConditional:
    def test_cross_sectional_icf_has_no_blood_draw_step(self):
        doc = _gen("cross_sectional")
        assert "lấy 5 mL máu" not in doc

    def test_cross_sectional_icf_has_no_multi_visit_followup_step(self):
        doc = _gen("cross_sectional")
        assert "tái khám sau 3 tháng" not in doc

    def test_cross_sectional_icf_benefit_does_not_promise_new_treatment_access(self):
        doc = _gen("cross_sectional")
        assert "tiếp cận thuốc/can thiệp mới" not in doc

    def test_case_control_icf_has_no_blood_draw_or_followup_step(self):
        doc = _gen("case_control")
        assert "lấy 5 mL máu" not in doc
        assert "tái khám sau 3 tháng" not in doc

    def test_diagnostic_icf_has_no_blood_draw_or_followup_step(self):
        doc = _gen("diagnostic")
        assert "lấy 5 mL máu" not in doc
        assert "tái khám sau 3 tháng" not in doc

    def test_rct_icf_keeps_blood_draw_and_followup_step(self):
        """Không hồi quy ngược: rct THẬT SỰ có thể lấy mẫu/theo dõi nhiều lần."""
        doc = _gen("rct")
        assert "lấy 5 mL máu" in doc
        assert "tái khám sau 3 tháng" in doc

    def test_cohort_icf_keeps_blood_draw_and_followup_step(self):
        doc = _gen("cohort")
        assert "lấy 5 mL máu" in doc
        assert "tái khám sau 3 tháng" in doc

    def test_all_designs_still_generate_valid_document(self):
        """An toàn cấu trúc: mọi thiết kế vẫn sinh đủ tài liệu, không crash/thiếu mục."""
        for code in ("rct", "cohort", "case_control", "cross_sectional", "diagnostic", "sr_ma"):
            doc = _gen(code)
            assert "TÀI LIỆU 4" in doc
            assert "PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU" in doc
