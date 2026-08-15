"""Hồi quy (vòng lặp kiểm tra-hoàn thiện, 2026-07-20, audit đối kháng): 2 lỗ
hổng thật trong tools/run_g6_auto.py, cùng lớp "2 lớp xử lý design_code tách
rời nhau" đã lặp lại nhiều lần trong lịch sử dự án (case_control 2026-07-06,
diagnostic/prediction/sr_ma 2026-07-19):

1. R_ANALYSIS_MAP_FUNC() thiếu hẳn nhánh "qualitative" — rơi vào else →
   make_r03_cohort() (Cox regression + Kaplan-Meier) cho nghiên cứu định tính,
   dù G1/G3/G7 đã hỗ trợ đúng "qualitative" từ 2026-07-19.
2. make_run_analysis_cli()/make_sensitivity_analysis() chỉ tách riêng
   "case_control" khỏi template Cox/HR — 5/8 design_code còn lại
   (cross_sectional/diagnostic/prediction/sr_ma/qualitative) vẫn âm thầm nhận
   CLI/sensitivity Cox/HR dù 03_analysis.R đã đúng phương pháp cho cả 5.

Đã vá: (1) thêm _r03_qualitative_template() + nhánh elif; (2) thêm cảnh báo
nổi bật (cùng mẫu đã có cho effect_type=MD) ở đầu run_analysis_cli.py/
sensitivity_analysis.py khi design_code thuộc 5 mã trên.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402

_V = {
    "exposure": "intervention_arm",
    "outcome": "outcome_event",
    "time_col": "followup_months",
    "covariates": ["age", "sex", "bmi"],
    "detection_log": ["test"],
}

_WRONG_METHOD_DESIGNS = ("cross_sectional", "diagnostic", "prediction", "sr_ma", "qualitative")


def _uncommented_call(script: str, fn_name: str) -> bool:
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if f"{fn_name}(" in stripped:
            return True
    return False


class TestG6QualitativeAnalysis:
    def test_qualitative_uses_thematic_coding_not_cox(self):
        script = G6.R_ANALYSIS_MAP_FUNC("qualitative", _V, 0, 0.05, 0.80, None, "HR")
        assert "mã hóa" in script.lower() or "thematic" in script.lower() or "coding" in script.lower()
        assert not _uncommented_call(script, "coxph")
        assert not _uncommented_call(script, "Surv")

    def test_qualitative_does_not_fall_back_to_cohort_cox_script(self):
        """Trước khi vá: rơi vào make_r03_cohort() → nhãn 'Cohort (Cox + KM)'."""
        script = G6.R_ANALYSIS_MAP_FUNC("qualitative", _V, 0, 0.05, 0.80, None, "HR")
        assert "Cohort (Cox" not in script

    def test_qualitative_mentions_trustworthiness_framework(self):
        script = G6.R_ANALYSIS_MAP_FUNC("qualitative", _V, 0, 0.05, 0.80, None, "HR")
        assert "credibility" in script.lower() or "trustworthiness" in script.lower()


class TestG6RunAnalysisCliWrongMethodWarning:
    def test_warns_for_all_5_non_survival_designs(self):
        for design_code in _WRONG_METHOD_DESIGNS:
            code = G6.make_run_analysis_cli(_V, 100, "STUDY-X", design_code, "OR")
            assert "CẦN CHÚ Ý" in code, f"thiếu cảnh báo cho {design_code}"
            assert design_code.upper() in code

    def test_case_control_still_uses_dedicated_template_no_warning(self):
        code = G6.make_run_analysis_cli(_V, 100, "STUDY-X", "case_control", "OR")
        assert "CẦN CHÚ Ý" not in code
        assert "logistic" in code.lower() or "conditional" in code.lower()

    def test_cohort_hr_still_clean_no_spurious_warning(self):
        code = G6.make_run_analysis_cli(_V, 100, "STUDY-X", "cohort", "HR")
        assert "CẦN CHÚ Ý" not in code


class TestG6SensitivityAnalysisWrongMethodWarning:
    def test_warns_for_all_5_non_survival_designs(self):
        for design_code in _WRONG_METHOD_DESIGNS:
            code = G6.make_sensitivity_analysis(_V, "STUDY-X", design_code)
            assert "CẦN CHÚ Ý" in code, f"thiếu cảnh báo cho {design_code}"
            assert design_code.upper() in code

    def test_case_control_still_uses_dedicated_template_no_warning(self):
        code = G6.make_sensitivity_analysis(_V, "STUDY-X", "case_control")
        assert "CẦN CHÚ Ý" not in code

    def test_cohort_still_clean_no_spurious_warning(self):
        code = G6.make_sensitivity_analysis(_V, "STUDY-X", "cohort")
        assert "CẦN CHÚ Ý" not in code


class TestG6CleaningAndTablesWrongMethodWarning:
    """Hồi quy MEDIUM (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):
    01_cleaning.R/02_tables.R trước đây sinh mutate/Table-1-theo-nhóm-phơi-
    nhiễm KHÔNG ĐIỀU KIỆN cho MỌI design_code, không cảnh báo gì — trong khi
    03_analysis.R/CLI/sensitivity đã có cảnh báo từ 2026-07-20."""

    def test_r01_cleaning_warns_for_all_5_non_cohort_designs(self):
        for design_code in _WRONG_METHOD_DESIGNS:
            code = G6.make_r01_cleaning(_V, design_code)
            assert "CẦN CHÚ Ý" in code, f"01_cleaning.R thiếu cảnh báo cho {design_code}"
            assert design_code.upper() in code

    def test_r02_tables_warns_for_all_5_non_cohort_designs(self):
        for design_code in _WRONG_METHOD_DESIGNS:
            code = G6.make_r02_tables(_V, design_code)
            assert "CẦN CHÚ Ý" in code, f"02_tables.R thiếu cảnh báo cho {design_code}"
            assert design_code.upper() in code

    def test_r01_cleaning_cohort_still_clean_no_spurious_warning(self):
        code = G6.make_r01_cleaning(_V, "cohort")
        assert "CẦN CHÚ Ý" not in code

    def test_r02_tables_cohort_still_clean_no_spurious_warning(self):
        code = G6.make_r02_tables(_V, "cohort")
        assert "CẦN CHÚ Ý" not in code

    def test_r01_cleaning_default_design_code_still_cohort_no_warning(self):
        """Không hồi quy ngược: lời gọi cũ không truyền design_code (mặc định
        'cohort') vẫn phải sinh script sạch, không cảnh báo giả."""
        code = G6.make_r01_cleaning(_V)
        assert "CẦN CHÚ Ý" not in code


class TestWrongMethodDesignsConstantIsSharedNotDuplicated:
    """Hồi quy LOW (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):
    _WRONG_METHOD_DESIGNS trước đây định nghĩa lặp lại y hệt ở 2 hàm — nay
    phải là MỘT hằng số module-level dùng chung cho cả 4 hàm sinh script."""

    def test_module_level_constant_exists_and_matches_test_tuple(self):
        assert G6._WRONG_METHOD_DESIGNS == set(_WRONG_METHOD_DESIGNS)

    def test_method_hint_defined_for_every_wrong_method_design(self):
        for design_code in _WRONG_METHOD_DESIGNS:
            assert design_code in G6._METHOD_HINT_BY_DESIGN
