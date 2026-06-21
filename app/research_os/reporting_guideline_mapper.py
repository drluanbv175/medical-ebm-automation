"""Map thiết kế nghiên cứu sang reporting guideline chuẩn EQUATOR (G8).

Tất cả guideline được kiểm tra phiên bản tại equator-network.org.
Khi cần nhiều guideline đồng thời, dùng reporting_guidelines_all().
"""
from __future__ import annotations

from typing import Dict, List

# Guideline chính theo thiết kế
GUIDELINE_BY_DESIGN: Dict[str, str] = {
    "randomized_controlled_trial": "CONSORT",
    "cohort": "STROBE",
    "cross_sectional": "STROBE",
    "case_control": "STROBE",
    "diagnostic_accuracy": "STARD 2015",
    "systematic_review": "PRISMA 2020",
    "scoping_review": "PRISMA-ScR",
    "evidence_mapping_or_scoping_review": "PRISMA-ScR",
    "prediction_model": "TRIPOD+AI 2024",
    "qualitative": "COREQ / SRQR",
    "case_report": "CARE 2013",
    "economic_evaluation": "CHEERS 2022",
    "quality_improvement": "SQUIRE 2.0",
}

# Guideline bổ sung (supplement checklist)
_SUPPLEMENTARY: Dict[str, List[str]] = {
    "randomized_controlled_trial": ["SPIRIT 2013 (protocol)", "TIDieR (intervention description)"],
    "systematic_review": ["GRADE (evidence grading)", "PROSPERO (registration)"],
    "prediction_model": ["GRADE-AI (accuracy)", "TRIPOD checklist"],
    "qualitative": ["SRQR (alternative)"],
    "randomized_controlled_trial_protocol": ["SPIRIT 2013"],
}


def reporting_guideline_for_design(design: str) -> str:
    """Trả guideline chính. Nếu chưa ánh xạ → hướng dẫn tra EQUATOR thủ công."""
    return GUIDELINE_BY_DESIGN.get(
        design, "EQUATOR Network checklist cần chọn thủ công"
    )


def reporting_guidelines_all(design: str) -> Dict[str, object]:
    """Trả dict đầy đủ: primary + supplementary + equator_url."""
    primary = reporting_guideline_for_design(design)
    supplementary = _SUPPLEMENTARY.get(design, [])
    return {
        "primary": primary,
        "supplementary": supplementary,
        "equator_url": "https://www.equator-network.org/reporting-guidelines/",
        "note": (
            "Xác nhận phiên bản mới nhất tại EQUATOR trước khi nộp bản thảo."
            if primary != "EQUATOR Network checklist cần chọn thủ công"
            else "Thiết kế chưa có guideline tự động — truy cập EQUATOR để chọn."
        ),
    }
