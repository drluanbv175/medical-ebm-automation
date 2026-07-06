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

from run_g1_auto import infer_study_design  # noqa: E402

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
