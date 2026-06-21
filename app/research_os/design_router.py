"""Router chọn thiết kế nghiên cứu từ câu hỏi PICO (G1)."""
from __future__ import annotations

from typing import Tuple

# Ánh xạ từ khóa → thiết kế (thứ tự ưu tiên từ trên xuống — cụ thể hơn ưu tiên trước)
_DESIGN_RULES: list[Tuple[list[str], str]] = [
    # Meta-analysis / systematic review — phải trước cohort
    (["meta-analysis", "meta analysis", "tổng quan hệ thống", "systematic review", "prisma"], "systematic_review"),
    # Prediction model — phải trước cohort vì "nguy cơ" có thể trùng
    (["mô hình dự báo", "prediction model", "tripod", "prognostic model", "nomogram", "điểm số dự báo"], "prediction_model"),
    # RCT
    (["random", "can thiệp", "intervention", "trial", "thử nghiệm lâm sàng", "rct"], "randomized_controlled_trial"),
    # Case-control — trước cohort
    (["case-control", "ca-chứng", "case control", "bệnh-chứng"], "case_control"),
    # Cohort / prognostic
    (["nguy cơ", "risk factor", "tiên lượng", "prognosis", "cohort", "đoàn hệ", "hazard"], "cohort"),
    # Diagnostic accuracy
    (["chẩn đoán", "diagnostic", "độ nhạy", "specificity", "sensitivity", "auc", "roc", "stard"], "diagnostic_accuracy"),
    # Qualitative
    (["định tính", "qualitative", "phỏng vấn sâu", "focus group", "grounded theory", "thematic analysis"], "qualitative"),
    # Case report
    (["ca bệnh", "case report", "ca lâm sàng", "care guideline"], "case_report"),
    # Cross-sectional / prevalence
    (["tỉ lệ", "prevalence", "khảo sát", "cross-sectional", "cắt ngang", "mô tả"], "cross_sectional"),
    # Economic evaluation
    (["kinh tế y tế", "cost-effectiveness", "cost effectiveness", "health economic", "cheers"], "economic_evaluation"),
    # Quality improvement
    (["cải tiến chất lượng", "quality improvement", "squire", "pdsa", "qi"], "quality_improvement"),
    # Scoping / evidence mapping
    (["scoping review", "evidence mapping", "tổng quan phạm vi"], "evidence_mapping_or_scoping_review"),
]


def route_design(question: str) -> str:
    """Trả về thiết kế phù hợp nhất cho câu hỏi nghiên cứu."""
    text = question.lower()
    for keywords, design in _DESIGN_RULES:
        if any(kw in text for kw in keywords):
            return design
    return "evidence_mapping_or_scoping_review"


def route_design_with_confidence(question: str) -> Tuple[str, float]:
    """Trả (design, confidence) — confidence 1.0 nếu khớp rõ, 0.4 nếu mặc định."""
    text = question.lower()
    for keywords, design in _DESIGN_RULES:
        matches = sum(1 for kw in keywords if kw in text)
        if matches > 0:
            confidence = min(1.0, 0.6 + 0.2 * matches)
            return design, round(confidence, 2)
    return "evidence_mapping_or_scoping_review", 0.4
