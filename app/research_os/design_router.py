"""Router chọn thiết kế nghiên cứu từ câu hỏi."""
from __future__ import annotations


def route_design(question: str) -> str:
    text = question.lower()
    if any(term in text for term in ("random", "can thiệp", "intervention", "trial")):
        return "randomized_controlled_trial"
    if any(term in text for term in ("nguy cơ", "risk", "tiên lượng", "prognosis")):
        return "cohort"
    if any(term in text for term in ("chẩn đoán", "diagnostic", "độ nhạy", "specificity")):
        return "diagnostic_accuracy"
    if any(term in text for term in ("tỉ lệ", "prevalence", "khảo sát")):
        return "cross_sectional"
    return "evidence_mapping_or_scoping_review"
