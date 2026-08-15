"""
Test đơn vị cho infer_study_design() và khối phát hiện từ khóa thiết kế
trong tools/run_g1_auto.py — trước 2026-07-06 KHÔNG có test nào cho hàm này
(phát hiện qua kiểm định đối kháng vòng 2), dù đây là logic quyết định toàn
bộ hướng đi của một đề tài (thiết kế sai → công thức cỡ mẫu sai → Methods/
STROBE checklist sai xuyên suốt G3-G9).

Bug lịch sử được test này khóa lại: 4/5 nhánh (sr/diagnosis/prognosis/
descriptive) có phát hiện từ khóa tường minh trong topic, riêng "harm"
(case-control) thì KHÔNG — một đề tài ghi rõ "nghiên cứu bệnh-chứng" trong
tên vẫn bị mặc định coi là question_type="treatment" rồi suy design="rct"/
"cohort", hoàn toàn bỏ qua tín hiệu case-control tường minh.
"""
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g1_auto import check_topic_design_consistency, infer_study_design  # noqa: E402

# Evidence landscape KHÔNG bão hòa — tình huống phổ biến, không phải hiếm gặp
# (bão hòa RCT/SR có thể che giấu bug vì trùng hợp rơi đúng nhánh cần).
_GAPS = {"n_sr": 0, "n_rct": 1}


class TestKeywordDetectionOverridesQuestionType:
    """Cả 5 nhánh phát hiện từ khóa tường minh phải override được question_type
    mặc định 'treatment' — bất kể question_type truyền vào ban đầu là gì."""

    def test_systematic_review_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Tổng quan hệ thống về statin và biến cố tim mạch")
        assert d["internal_code"] == "sr_ma"

    def test_diagnosis_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Độ nhạy và độ đặc hiệu của NT-proBNP trong chẩn đoán suy tim")
        assert d["internal_code"] == "diagnostic"

    def test_prognosis_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Tiên lượng sống còn ở bệnh nhân ung thư phổi giai đoạn IV")
        assert d["internal_code"] == "cohort"

    def test_descriptive_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Tỷ lệ hài lòng của bệnh nhân ngoại trú: một khảo sát cắt ngang")
        assert d["internal_code"] == "cross_sectional"

    def test_case_control_keyword_vietnamese(self):
        """Bug lịch sử: nhánh này TRƯỚC ĐÂY KHÔNG TỒN TẠI — topic ghi rõ
        'nghiên cứu bệnh-chứng' vẫn bị suy design='rct'/'cohort'."""
        d = infer_study_design(
            "treatment", _GAPS,
            "Yếu tố nguy cơ nhiễm khuẩn vết mổ sau phẫu thuật thay khớp háng: nghiên cứu bệnh-chứng",
        )
        assert d["internal_code"] == "case_control"

    def test_case_control_keyword_english(self):
        d = infer_study_design("treatment", _GAPS, "Risk factors for surgical site infection: a case-control study")
        assert d["internal_code"] == "case_control"

    def test_nested_case_control_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Yếu tố nguy cơ tái phát: nested case-control trong cohort ĐTĐ")
        assert d["internal_code"] == "case_control"


class TestPredictionModelKeywordDetection:
    """Vá 2026-07-17 (round audit gate — tiếp nối hoàn thiện gate cho
    "prediction"): PHÁT HIỆN LỚN — trước khi vá này, internal_code=
    "prediction" KHÔNG BAO GIỜ có thể xuất hiện từ phân loại tự động. Mọi đề
    tài "xây dựng mô hình tiên lượng" khớp từ khóa "tiên lượng" (generic) và
    bị gán internal_code="cohort" — toàn bộ hệ thống TRIPOD+AI đã nối xuyên
    G2-G9 (2 round trước) không bao giờ được chạm tới trong thực tế. Test
    này khóa lại: cụm từ TƯỜNG MINH khai báo Ý ĐỊNH XÂY MÔ HÌNH (không phải
    câu hỏi tiên lượng 1 yếu tố đơn thuần) phải cho internal_code="prediction"."""

    def test_mo_hinh_tien_luong_keyword(self):
        d = infer_study_design(
            "treatment", _GAPS,
            "Xây dựng mô hình tiên lượng nguy cơ tái nhập viện ở bệnh nhân suy tim",
        )
        assert d["internal_code"] == "prediction"
        assert d["reporting_standard"] == "TRIPOD+AI 2024"

    def test_nomogram_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Phát triển và đánh giá nomogram dự đoán biến chứng sau phẫu thuật")
        assert d["internal_code"] == "prediction"

    def test_english_prediction_model_keyword(self):
        d = infer_study_design("treatment", _GAPS, "Prediction model for 30-day mortality in sepsis patients")
        assert d["internal_code"] == "prediction"

    def test_bias_controls_are_prediction_specific_not_cohort_fallback(self):
        """Hồi quy: trước khi 'prediction' reachable, mọi lời gọi (nếu có) sẽ
        rơi vào bias_controls của 'cohort' qua .get() fallback."""
        d = infer_study_design(
            "treatment", _GAPS,
            "Xây dựng mô hình tiên lượng nguy cơ tái nhập viện ở bệnh nhân suy tim",
        )
        labels = [label for label, _ctrl in d["bias_controls"]]
        assert "Overfitting/optimism" in labels
        assert "Predictor bias" in labels

    def test_single_factor_prognosis_still_classified_as_cohort_not_prediction(self):
        """Chống over-match: câu hỏi tiên lượng 1 YẾU TỐ đơn thuần (không xây
        mô hình đa biến) phải VẪN là cohort/STROBE như trước, không bị đẩy
        nhầm sang 'prediction' chỉ vì có chữ 'tiên lượng'."""
        d = infer_study_design("treatment", _GAPS, "Yếu tố tiên lượng sống còn ở bệnh nhân ung thư phổi giai đoạn IV")
        assert d["internal_code"] == "cohort"

    def test_single_factor_prognosis_keyword_still_works(self):
        d = infer_study_design("treatment", _GAPS, "Hút thuốc lá có tiên lượng tử vong ở bệnh nhân COPD hay không")
        assert d["internal_code"] == "cohort"


class TestNoFalsePositiveOnRiskFactorAlone(object):
    """Cụm 'yếu tố nguy cơ' ĐƠN LẺ (không kèm 'bệnh-chứng'/'case-control')
    KHÔNG được tự ý coi là case-control — cụm này cũng dùng phổ biến cho
    cohort. Chỉ khớp khi có khai báo thiết kế case-control tường minh."""

    def test_risk_factor_phrase_without_design_declaration_falls_through(self):
        d = infer_study_design(
            "treatment", _GAPS,
            "Yếu tố nguy cơ tim mạch ở người cao tuổi tại cộng đồng",
        )
        assert d["internal_code"] != "case_control"


class TestExplicitQuestionTypeStillHonored:
    """Khi bác sĩ/agent điều phối TRUYỀN THẲNG question_type (vd qua
    --question-type harm), kết quả phải khớp bất kể topic có từ khóa hay
    không — khối phát hiện từ khóa chỉ NÂNG CẤP, không hạ cấp lựa chọn tường
    minh đã có."""

    def test_explicit_harm_without_keyword_in_topic(self):
        d = infer_study_design("harm", _GAPS, "Tác dụng phụ của một loại thuốc mới")
        assert d["internal_code"] == "case_control"


class TestGuardrailTopicDesignConsistency:
    """R6 (guardrail_check_g1): đối chiếu ngược từ khóa thiết kế trong topic
    với design_code CUỐI CÙNG — lớp phòng thủ thứ 2, độc lập với việc
    infer_study_design() có bắt đúng từ khóa hay không (bắt được cả trường
    hợp bác sĩ pin tay sai qua study_meta.json). Thêm 2026-07-06."""

    def test_warns_when_case_control_topic_but_cohort_chosen(self):
        """Mô phỏng CHÍNH bug lịch sử: topic ghi rõ bệnh-chứng nhưng
        design_code cuối cùng lại là cohort."""
        warns = check_topic_design_consistency(
            "Yếu tố nguy cơ nhiễm khuẩn vết mổ sau phẫu thuật thay khớp háng: nghiên cứu bệnh-chứng",
            "cohort",
        )
        assert len(warns) == 1
        assert "case_control" in warns[0]

    def test_no_warning_when_design_matches_keyword(self):
        warns = check_topic_design_consistency(
            "Yếu tố nguy cơ nhiễm khuẩn vết mổ sau phẫu thuật thay khớp háng: nghiên cứu bệnh-chứng",
            "case_control",
        )
        assert warns == []

    def test_no_warning_when_topic_has_no_explicit_keyword(self):
        """Topic RCT thông thường không có từ khóa đặc thù nào → không cảnh
        báo giả (tránh làm phiền bác sĩ với warning vô căn cứ)."""
        warns = check_topic_design_consistency(
            "Hiệu quả metformin trong kiểm soát đường huyết ở bệnh nhân tiền đái tháo đường",
            "rct",
        )
        assert warns == []

    def test_warns_for_systematic_review_mismatch(self):
        warns = check_topic_design_consistency(
            "Tổng quan hệ thống về statin và biến cố tim mạch", "cohort",
        )
        assert len(warns) == 1
        assert "sr_ma" in warns[0]

    def test_no_false_warning_when_prediction_model_correctly_chosen(self):
        """Hồi quy trực tiếp: "mô hình tiên lượng" khớp CẢ "prediction_model"
        LẪN "prognosis" (chứa "tiên lượng") — nếu không loại trừ nhánh
        prognosis khi prediction_model đã khớp, sẽ có cảnh báo giả "topic gợi
        ý cohort" dù internal_code="prediction" là ĐÚNG."""
        warns = check_topic_design_consistency(
            "Xây dựng mô hình tiên lượng nguy cơ tái nhập viện ở bệnh nhân suy tim",
            "prediction",
        )
        assert warns == []

    def test_warns_when_prediction_model_topic_but_cohort_chosen(self):
        warns = check_topic_design_consistency(
            "Xây dựng mô hình tiên lượng nguy cơ tái nhập viện ở bệnh nhân suy tim",
            "cohort",
        )
        assert len(warns) == 1
        assert "prediction" in warns[0]
