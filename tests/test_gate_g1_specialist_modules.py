"""
Test đơn vị cho detect_specialist_modules() của cổng G1 (tools/run_g1_auto.py).

Bối cảnh (2026-07-05): 4 agent chuyên biệt (cong-cu-do-luong, mo-hinh-tien-luong,
kinh-te-y-te, nghien-cuu-dinh-tinh) đã có trong bản đồ đội + control-plane
dry-run (tools/orchestrator/) nhưng CHƯA từng được nối vào automation THẬT
của G1 — đề tài cần 1 trong 4 năng lực này trước đây không được A2 nhắc gì.

Rủi ro cần test bắt được: từ khóa của 4 mô-đun này PHẢI không va chạm với
từ khóa suy loại thiết kế đã có (vd "tiên lượng"/"auc" dùng cho
infer_study_design) — một đề tài tiên lượng/chẩn đoán THÔNG THƯỜNG không
được bị hiểu nhầm thành "đang xây mô hình/công cụ mới".
"""
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g1_auto import (  # noqa: E402
    SPECIALIST_MODULE_KEYWORDS,
    detect_specialist_modules,
    generate_g1_artifact,
    specialist_modules_block,
)

ALL_MODULES = list(SPECIALIST_MODULE_KEYWORDS.keys())


class TestDetectionReachability:
    """Mỗi mô-đun PHẢI tự bật khi đề tài chỉ chứa từ khóa của riêng nó."""

    def test_all_modules_are_reachable(self):
        for module, keywords in SPECIALIST_MODULE_KEYWORDS.items():
            longest_kw = max(keywords, key=len)
            topic = f"Nghiên cứu về {longest_kw} ở bệnh nhân ngoại trú"
            assert module in detect_specialist_modules(topic), (
                f"Mô-đun '{module}' không tự bật được với từ khóa đặc hiệu "
                f"của chính nó ({longest_kw!r})"
            )

    def test_prom_tool(self):
        assert detect_specialist_modules(
            "Xây dựng thang đo hài lòng người bệnh khoa khám bệnh"
        ) == ["prom_tool"]

    def test_prognostic_model(self):
        assert detect_specialist_modules(
            "Xây dựng mô hình tiên lượng tử vong ở bệnh nhân suy tim"
        ) == ["prognostic_model"]

    def test_economic(self):
        assert detect_specialist_modules(
            "Phân tích chi phí hiệu quả của SGLT2i ở bệnh nhân ĐTĐ2"
        ) == ["economic"]

    def test_qualitative(self):
        assert detect_specialist_modules(
            "Nghiên cứu định tính trải nghiệm của bệnh nhân ung thư giai đoạn cuối"
        ) == ["qualitative"]

    def test_multiple_modules_can_co_trigger(self):
        topic = ("Kiểm định thang đo chất lượng sống kết hợp phân tích "
                 "chi phí hiệu quả triển khai chương trình")
        got = set(detect_specialist_modules(topic))
        assert got == {"prom_tool", "economic"}


class TestNoFalsePositiveWithExistingDesignKeywords:
    """Từ khóa suy loại thiết kế (infer_study_design) KHÔNG được tự kích hoạt
    mô-đun chuyên biệt — hai cơ chế độc lập, không được va chạm."""

    def test_plain_prognosis_topic_does_not_trigger_prognostic_model(self):
        topic = "Tiên lượng sống còn ở bệnh nhân xơ gan (theo dõi cohort)"
        assert "prognostic_model" not in detect_specialist_modules(topic)

    def test_plain_diagnostic_auc_topic_does_not_trigger_anything(self):
        topic = "Độ chính xác chẩn đoán AUC của troponin trong nhồi máu cơ tim"
        assert detect_specialist_modules(topic) == []

    def test_plain_satisfaction_survey_does_not_trigger_prom_tool(self):
        # "hài lòng" một mình đã đủ để infer_study_design chọn descriptive
        # design (xem run_g1_auto.py dòng ~202) — nhưng KHÔNG có nghĩa đề
        # tài đang XÂY/KIỂM ĐỊNH công cụ đo mới, nên KHÔNG nên bật prom_tool.
        topic = "Khảo sát mức độ hài lòng người bệnh tại khoa khám bệnh ngoại trú"
        assert detect_specialist_modules(topic) == []

    def test_plain_treatment_topic_triggers_nothing(self):
        topic = "Hiệu quả metformin ở bệnh nhân PCOS ngoại trú"
        assert detect_specialist_modules(topic) == []


class TestSpecialistModulesBlock:
    def test_empty_modules_returns_empty_string(self):
        assert specialist_modules_block([]) == ""

    def test_each_module_mentions_its_reporting_standard(self):
        expected_standard = {
            "prom_tool": "COSMIN",
            "prognostic_model": "TRIPOD+AI",
            "economic": "CHEERS",
            "qualitative": "COREQ",
        }
        for module in ALL_MODULES:
            block = specialist_modules_block([module])
            assert expected_standard[module] in block, (
                f"Khối mô-đun '{module}' thiếu tên chuẩn báo cáo {expected_standard[module]!r}"
            )
            assert "[CẦN" in block, f"Mô-đun '{module}' thiếu nhãn [CẦN...] (nghi bịa nội dung)"

    def test_block_names_the_specialist_agent(self):
        agent_by_module = {
            "prom_tool": "cong-cu-do-luong",
            "prognostic_model": "mo-hinh-tien-luong",
            "economic": "kinh-te-y-te",
            "qualitative": "nghien-cuu-dinh-tinh",
        }
        for module, agent in agent_by_module.items():
            assert agent in specialist_modules_block([module])


class TestGenerateG1ArtifactIntegration:
    """Xác nhận artifact THẬT (không chỉ hàm nội bộ) phản ánh đúng tín hiệu."""

    _DESIGN = {
        "primary": "Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)",
        "internal_code": "cross_sectional",
        "alternative_1": "Khảo sát dựa cộng đồng",
        "alternative_2": "Registry",
        "rationale": "test",
        "reporting_standard": "STROBE",
        "bias_controls": [("Selection bias", "test control")],
    }

    def test_artifact_includes_part8_when_signal_present(self):
        artifact = generate_g1_artifact(
            topic="Xây dựng thang đo hài lòng người bệnh khoa khám bệnh",
            study_name="TEST-STUDY", question_type="descriptive",
            design=self._DESIGN, effects=[], g0_gaps={}, run_date="2026-07-05 00:00",
        )
        assert "PHẦN 8 — MÔ-ĐUN CHUYÊN BIỆT" in artifact
        assert "COSMIN" in artifact

    def test_artifact_omits_part8_when_no_signal(self):
        artifact = generate_g1_artifact(
            topic="Hiệu quả metformin ở bệnh nhân PCOS ngoại trú",
            study_name="TEST-STUDY", question_type="treatment",
            design=self._DESIGN, effects=[], g0_gaps={}, run_date="2026-07-05 00:00",
        )
        assert "PHẦN 8 — MÔ-ĐUN CHUYÊN BIỆT" not in artifact
