"""Scaffold kiểm tra causal inference assumptions (G7).

Quy tắc: không kết luận quan hệ nhân quả từ thiết kế không cho phép.
Chỉ RCT và một số thiết kế can thiệp có thiết kế phù hợp để suy luận nhân quả.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

# Thiết kế CHO PHÉP kết luận nhân quả (dưới điều kiện phân tích đúng)
_CAUSAL_DESIGNS = {
    "randomized_controlled_trial",
    "quasi_experimental",
    "interrupted_time_series",
    "difference_in_differences",
}

# Thiết kế cần cảnh báo khi suy luận nhân quả
_CAUSAL_WARNING_DESIGNS = {
    "cohort": "Cohort có thể điều chỉnh confounders nhưng không loại trừ unmeasured confounding",
    "case_control": "Case-control tính OR, không trực tiếp kết luận nhân quả; cần diễn giải thận trọng",
}


@dataclass(frozen=True)
class CausalPlan:
    """Kế hoạch suy luận nhân quả cho một nghiên cứu."""
    exposure: str
    outcome: str
    confounders: List[str]
    estimand: str

    def issues(self) -> List[str]:
        """Trả danh sách vấn đề về kế hoạch. [] = không có."""
        problems: List[str] = []
        if not self.exposure or not self.exposure.strip():
            problems.append("Chưa khai báo exposure/yếu tố phơi nhiễm")
        if not self.outcome or not self.outcome.strip():
            problems.append("Chưa khai báo outcome/kết cục")
        if not self.confounders:
            problems.append("Chưa khai báo confounders/DAG tối thiểu")
        if not self.estimand or not self.estimand.strip():
            problems.append("Chưa khai báo estimand (ATE/ATT/LATE/…)")
        return problems


def design_allows_causal(design: str) -> bool:
    """True nếu thiết kế THƯỜNG được chấp nhận để kết luận nhân quả.

    Lưu ý: trả True KHÔNG có nghĩa là phân tích tự động hợp lệ —
    vẫn cần CausalPlan.issues() kiểm tra estimand và confounders.
    """
    return design in _CAUSAL_DESIGNS


def causal_design_warning(design: str) -> str:
    """Trả cảnh báo khi suy luận nhân quả từ thiết kế quan sát, hoặc '' nếu không."""
    return _CAUSAL_WARNING_DESIGNS.get(design, "")
