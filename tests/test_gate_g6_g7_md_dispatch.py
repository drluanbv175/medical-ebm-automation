"""
Test cho việc dispatch phương pháp phân tích theo effect_type ở G6 và gợi ý
phương pháp thống kê ở G7 — thêm 2026-07-06 sau khi kiểm định đối kháng vòng 2
phát hiện: G6 LUÔN sinh Cox/log-rank bất kể effect_type (kể cả kết cục LIÊN
TỤC effect_type=MD, sai phương pháp thống kê), và nhãn analysis 'rct' overclaim
"GLM/LM/Cox theo loại kết cục" trong khi chỉ sinh Cox.

Bối cảnh: G3 đã hỗ trợ effect_type=MD (kết cục liên tục — đau NRS/HbA1c/chất
lượng sống) từ một lần sửa trước. Các cổng downstream (G6 phân tích, G7 bản
thảo) phải nhất quán chọn phương pháp đúng theo effect_type, không mặc định
Cox/logistic cho biến liên tục.
"""
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402

_V = {
    "exposure": "arm",
    "outcome": "pain_nrs_change",
    "time_col": "",
    "covariates": ["age", "sex"],
    "detection_log": ["test"],
}


class TestG6ContinuousMDDispatch:
    def test_rct_md_uses_ttest_ancova_not_cox(self):
        """RCT + effect_type=MD → t-test/ANCOVA/lm, KHÔNG Cox/Surv."""
        script = G6.R_ANALYSIS_MAP_FUNC("rct", _V, 60, 0.05, 0.80, 1.5, "MD")
        assert "t.test" in script
        assert "lm(" in script or "ANCOVA" in script
        assert "coxph" not in script and "Surv(" not in script

    def test_cohort_md_uses_continuous_analysis(self):
        """Cohort + MD cũng phải dùng phân tích liên tục, không Cox."""
        script = G6.R_ANALYSIS_MAP_FUNC("cohort", _V, 60, 0.05, 0.80, 1.5, "MD")
        assert "t.test" in script or "lm(" in script
        assert "coxph" not in script

    def test_rct_hr_still_uses_cox(self):
        """RCT + HR (thời gian-đến-biến-cố) vẫn phải là Cox — không hồi quy hóa."""
        script = G6.R_ANALYSIS_MAP_FUNC("rct", _V, 60, 0.05, 0.80, 0.7, "HR")
        assert "coxph" in script or "Surv(" in script

    def test_case_control_unaffected_by_md_branch(self):
        """Case-control (effect OR) vẫn dùng logistic, không bị nhánh MD chiếm."""
        script = G6.R_ANALYSIS_MAP_FUNC("case_control", _V, 60, 0.05, 0.80, 1.5, "OR")
        assert "logistic" in script.lower() or "glm(" in script or "clogit" in script

    def test_python_cli_md_carries_warning(self):
        """CLI Python (template Cox) với MD phải có cảnh báo nổi bật, giữ shebang đầu file."""
        cli = G6.make_run_analysis_cli(_V, 60, "TEST", "rct", "MD")
        assert "KẾT CỤC LIÊN TỤC" in cli
        assert cli.startswith("#!")

    def test_python_cli_hr_no_warning(self):
        """CLI với HR (đúng cho Cox) KHÔNG được có cảnh báo MD giả."""
        cli = G6.make_run_analysis_cli(_V, 60, "TEST", "cohort", "HR")
        assert "KẾT CỤC LIÊN TỤC" not in cli
