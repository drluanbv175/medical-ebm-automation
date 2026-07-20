"""Test cho sec_sap() của G10 assembler (tools/run_g10_assemble.py) — thêm
2026-07-17.

Phát hiện thật (bình duyệt agent `binh-duyet` cho đề tài khảo sát hài lòng
bệnh nhân C1a, BVQY175): câu SAP "đa biến (hồi quy logistic/tuyến tính/Cox
tuỳ thiết kế)" trước đây KHÔNG điều kiện theo thiết kế — hồi quy Cox chỉ có
ý nghĩa với dữ liệu sống còn/thời gian-đến-biến cố (cohort/rct theo dõi
dọc); một nghiên cứu cắt ngang MỘT thời điểm không có trục thời gian để
tính Cox. Nhắc "Cox" ở SAP của một khảo sát cắt ngang là dấu vết SAP dùng
chung mọi thiết kế — phản biện thật sẽ bắt ngay.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g10_assemble as G10  # noqa: E402


def _cps_for(design_code):
    return {
        "G1": {"design": {"internal_code": design_code}},
        "G3": {},
        "G4": {"g4_sap_version": "1.0", "g4_status": "PENDING"},
    }


class TestCoxMentionedOnlyForLongitudinalDesigns:
    def test_cross_sectional_does_not_mention_cox(self):
        text = G10.sec_sap(_cps_for("cross_sectional"), {})
        assert "Cox" not in text or "không áp dụng Cox" in text

    def test_case_control_does_not_mention_cox_as_available(self):
        text = G10.sec_sap(_cps_for("case_control"), {})
        assert "không áp dụng Cox" in text

    def test_diagnostic_does_not_mention_cox_as_available(self):
        text = G10.sec_sap(_cps_for("diagnostic"), {})
        assert "không áp dụng Cox" in text

    def test_cohort_still_mentions_cox_as_option(self):
        text = G10.sec_sap(_cps_for("cohort"), {})
        assert "hồi quy logistic/tuyến tính/Cox tuỳ thiết kế" in text

    def test_rct_still_mentions_cox_as_option(self):
        text = G10.sec_sap(_cps_for("rct"), {})
        assert "hồi quy logistic/tuyến tính/Cox tuỳ thiết kế" in text

    def test_prediction_still_mentions_cox_as_option(self):
        """Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):
        _SURVIVAL_CAPABLE_DESIGNS thiếu 'prediction' làm G10 khẳng định cứng
        'không áp dụng Cox' cho MỌI mô hình tiên lượng — mâu thuẫn trực tiếp
        với run_g6_auto.py (analysis_name_map['prediction'] ghi rõ 'hồi quy
        logistic/Cox hoặc ML tuỳ SAP'), vì mô hình tiên lượng thời gian-đến-
        biến cố (vd Cox tiên lượng tử vong 5 năm, TRIPOD+AI) là thiết kế hợp lệ."""
        text = G10.sec_sap(_cps_for("prediction"), {})
        assert "hồi quy logistic/tuyến tính/Cox tuỳ thiết kế" in text
        assert "không áp dụng Cox" not in text

    def test_logistic_and_linear_always_mentioned(self):
        for code in ("cross_sectional", "case_control", "diagnostic", "cohort", "rct"):
            text = G10.sec_sap(_cps_for(code), {})
            assert "logistic" in text
            assert "tuyến tính" in text


class TestQualitativeSapIsNotQuantitative:
    """Hồi quy CRITICAL (vòng lặp kiểm tra-hoàn thiện vòng 3, 2026-07-21):
    sec_sap() hoàn toàn thiếu nhánh design_code="qualitative" — rơi vào
    nhánh định lượng, sinh Mục 11 dùng χ²/Fisher/t-test/hồi quy cho nghiên
    cứu định tính, mâu thuẫn với G2/G5/G6/G7/G8 (đã đúng COREQ/SRQR)."""

    def test_qualitative_sap_does_not_prescribe_quantitative_tests(self):
        """Không hồi quy về nhánh định lượng cũ ('đơn biến (χ²/Fisher,
        t-test/Mann-Whitney) → đa biến...') — các test này chỉ được PHÉP
        xuất hiện trong câu 'KHÔNG dùng', không phải như phương pháp chính."""
        text = G10.sec_sap(_cps_for("qualitative"), {})
        assert "đơn biến (χ²/Fisher, t-test/Mann-Whitney)" not in text
        assert "Phân tích yếu tố liên quan" not in text

    def test_qualitative_sap_mentions_thematic_coding_and_saturation(self):
        text = G10.sec_sap(_cps_for("qualitative"), {})
        assert "mã hóa chủ đề" in text or "thematic" in text.lower()
        assert "bão hòa" in text.lower() or "saturation" in text.lower()

    def test_qualitative_sap_mentions_trustworthiness(self):
        text = G10.sec_sap(_cps_for("qualitative"), {})
        assert "credibility" in text.lower() or "trustworthiness" in text.lower()


class TestNonResponseBiasMentioned:
    """Bình duyệt agent `binh-duyet` phát hiện thật: Mục 12 liệt kê sai số
    chọn mẫu/thông tin/nhớ lại/nhiễu/mong muốn xã hội nhưng KHÔNG đặt tên
    'sai lệch không trả lời' (non-response bias) — sai lệch đặc thù và
    thường quan trọng NHẤT của khảo sát hài lòng."""

    def test_sec_sailech_mentions_non_response_bias(self):
        text = G10.sec_sailech(_cps_for("cross_sectional"), {})
        assert "sai lệch không trả lời" in text
        assert "non-response bias" in text
