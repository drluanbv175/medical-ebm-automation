"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 21, 2026-07-24) — 6 phát hiện
xác nhận (2 HIGH, 2 HIGH, 1 MEDIUM, 1 LOW) trong tools/run_g1_auto.py, cùng
lớp lỗi "design_code cụ thể rơi vào nhánh generic không phù hợp" và "field
sinh ra ở một hàm không được hàm khác trong CÙNG FILE đọc lại" đã lặp nhiều
lần qua các vòng audit trước — lần này xảy ra NỘI BỘ trong G1, không phải
xuyên gate:

1. _apply_design_pin() chỉ ghi đè internal_code/primary/reporting_standard/
   rationale — bias_controls và alternative_1/alternative_2 vẫn giữ nguyên
   giá trị suy luận tự động TRƯỚC KHI pin, gây artifact A2 tự mâu thuẫn
   (PHẦN 2 hiển thị bias của thiết kế CŨ dù internal_code đã đổi).
2. _canonicalize_pinned_design_code() không validate — pin gõ sai/lạ rơi vào
   else cuối của khối chọn SAP §4 (viết riêng cho "qualitative") mà không
   hề cảnh báo.
3. question_type bị infer_study_design() gán lại CỤC BỘ theo từ khóa topic,
   nhưng biến ở nơi GỌI (main()) không đổi theo (Python truyền string theo
   giá trị) — checkpoint ghi "question_type" cũ mâu thuẫn với
   "design.internal_code" mới.
4. DESIGN_KEYWORD_HINTS["diagnosis"] chứa "auc"/"sensitivity" — khớp cả đề
   tài prediction model (thuật ngữ chỉ-số-hiệu-năng dùng chung) — "diagnosis"
   được kiểm TRƯỚC "prediction_model" nên thắng nhầm.
5. pii_keywords ở G1 thiếu "số hồ sơ" so với pii_patterns ở G0 (run_g0_auto.py).
6. Guardrail R5 chỉ khớp dấu "=" trong khi template thật viết "Cỡ mẫu dự
   kiến: [CẦN...]" bằng dấu hai chấm.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g1_auto as G1  # noqa: E402

_GAPS = {"n_sr": 0, "n_rct": 1}


class TestDesignPinRecomputesBiasControlsAndAlternatives:
    def test_pin_to_diagnostic_recomputes_bias_controls_not_rct(self):
        design = G1.infer_study_design("treatment", _GAPS, "Hiệu quả thuốc X trên biến cố tim mạch")
        assert design["internal_code"] == "rct"
        pinned = G1._apply_design_pin(design, "diagnostic")
        assert pinned["internal_code"] == "diagnostic"
        assert pinned["bias_controls"] == G1.BIAS_CONTROLS["diagnostic"]
        bias_labels = " ".join(label for label, _ in pinned["bias_controls"])
        assert "Ngẫu nhiên hóa" not in bias_labels

    def test_pin_disables_stale_alternative_design_table(self):
        design = G1.infer_study_design("treatment", _GAPS, "Hiệu quả thuốc X trên biến cố tim mạch")
        pinned = G1._apply_design_pin(design, "diagnostic")
        assert "Đã pin" in pinned["alternative_1"]
        assert "Đã pin" in pinned["alternative_2"]
        assert "Cohort tiến cứu (nếu RCT không khả thi" not in pinned["alternative_1"]


class TestPinnedDesignCodeValidation:
    def test_unknown_pin_falls_back_to_empty_string(self):
        assert G1._canonicalize_pinned_design_code("economic") == ""
        assert G1._canonicalize_pinned_design_code("mixed_methods") == ""
        assert G1._canonicalize_pinned_design_code("cohrot") == ""  # lỗi chính tả

    def test_valid_canonical_codes_pass_through(self):
        for code in ("rct", "cohort", "case_control", "cross_sectional",
                     "diagnostic", "sr_ma", "prediction", "qualitative"):
            assert G1._canonicalize_pinned_design_code(code) == code

    def test_known_alias_still_resolves(self):
        assert G1._canonicalize_pinned_design_code("prediction_model") == "prediction"
        assert G1._canonicalize_pinned_design_code("systematic_review") == "sr_ma"


class TestQuestionTypeResolvedPropagation:
    def test_infer_study_design_returns_resolved_question_type(self):
        design = G1.infer_study_design(
            "treatment", _GAPS,
            "Trải nghiệm và rào cản tuân thủ điều trị ở bệnh nhân đái tháo đường",
        )
        assert design["internal_code"] == "qualitative"
        assert design["resolved_question_type"] == "qualitative"

    def test_main_source_reassigns_question_type_after_infer(self):
        src = inspect.getsource(G1)
        assert 'question_type = design.get("resolved_question_type", question_type)' in src


class TestPredictionModelBeatsDiagnosisKeywordOverlap:
    def test_auc_sensitivity_wording_still_routes_to_prediction(self):
        design = G1.infer_study_design(
            "treatment", _GAPS,
            "Phát triển mô hình dự đoán nguy cơ tái nhập viện: độ nhạy, độ đặc hiệu và AUC",
        )
        assert design["internal_code"] == "prediction"

    def test_plain_diagnostic_topic_still_routes_to_diagnostic(self):
        design = G1.infer_study_design(
            "treatment", _GAPS,
            "Độ nhạy và độ đặc hiệu của NT-proBNP trong chẩn đoán suy tim",
        )
        assert design["internal_code"] == "diagnostic"

    def test_consistency_check_does_not_false_flag_diagnosis_for_prediction_topic(self):
        warns = G1.check_topic_design_consistency(
            "Phát triển mô hình dự đoán nguy cơ tái nhập viện: độ nhạy, độ đặc hiệu và AUC",
            "prediction",
        )
        assert not any("diagnostic" in w for w in warns)


class TestPiiKeywordsSyncedWithG0:
    def test_g1_pii_keywords_includes_medical_record_number(self):
        src = inspect.getsource(G1)
        assert '"số hồ sơ"' in src


class TestGuardrailR5AcceptsColonSeparator:
    def test_sample_size_with_colon_and_number_without_can_flag_is_flagged(self):
        artifact = "Nội dung SAP...\nCỡ mẫu dự kiến: 250 bệnh nhân\nHết.\n"
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert any("R5" in e for e in result["errors"])

    def test_sample_size_with_can_label_nearby_not_flagged(self):
        artifact = "Nội dung SAP...\nCỡ mẫu dự kiến: [CẦN → chạy run_g3_auto.py]\nHết.\n"
        result = G1.guardrail_check_g1(artifact, effects=[], topic="", internal_code="")
        assert not any("R5" in e for e in result["errors"])
