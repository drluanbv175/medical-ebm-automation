"""Evidence Quality Score (0–100).

Dựa trên: loại nghiên cứu/thiết kế, đa trung tâm, outcome lâm sàng vs surrogate,
guideline chính thức, có GRADE, nguy cơ bias, xung đột lợi ích.

Hàm trả về (score, breakdown) để giải thích minh bạch.
"""
from __future__ import annotations

from typing import Dict, Tuple

# Điểm nền theo loại thiết kế (study_type chuẩn hóa).
DESIGN_BASE = {
    "guideline": 85,
    "systematic_review": 80,
    "rct": 75,
    "network_meta_analysis": 65,
    "cohort": 55,
    "registry": 55,
    "pragmatic_trial": 60,
    "retrospective_single_center": 35,
    "case_series": 25,
    "narrative_review": 25,
    "editorial": 15,
    "expert_opinion": 20,
    "preprint": 10,
    "animal_invitro": 5,
    "pharmacovigilance_signal": 30,
    "regulatory_alert": 80,  # cảnh báo cơ quan quản lý: độ tin cậy nguồn cao
}


def _text(item: Dict, *keys: str) -> str:
    return " ".join(str(item.get(k, "") or "") for k in keys).lower()


def evidence_quality_score(item: Dict) -> Tuple[float, Dict[str, float]]:
    breakdown: Dict[str, float] = {}
    study_type = (item.get("study_type") or "").lower()
    base = DESIGN_BASE.get(study_type, 40)
    breakdown["base_design"] = float(base)

    text = _text(item, "title", "abstract", "document_type")

    # Đa trung tâm
    if any(k in text for k in ("multicenter", "multi-center", "đa trung tâm", "international")):
        breakdown["multicenter"] = 5
    # Outcome lâm sàng cứng vs surrogate
    hard = ("mortality", "death", "stroke", "myocardial infarction", "hospitalization",
            "tử vong", "đột quỵ", "nhập viện", "clinical outcome")
    surrogate = ("biomarker", "surrogate", "hba1c level", "ldl level only")
    if any(k in text for k in hard):
        breakdown["hard_outcome"] = 5
    elif any(k in text for k in surrogate):
        breakdown["surrogate_outcome"] = -5

    # Cỡ mẫu lớn (heuristic theo số trong abstract)
    if any(k in text for k in ("large", "thousands", "n=6", "n = 6", "6609", "10,", "multinational")):
        breakdown["large_sample"] = 3

    # Guideline chính thức / GRADE
    if study_type == "guideline":
        breakdown["official_guideline"] = 5
    if item.get("official_grade"):
        breakdown["has_grade"] = 4

    # Nguồn từ tổ chức/tạp chí chính thống (ESC, AHA, NICE, NEJM, Lancet...)
    from app.sources.classify_meta import detect_official_org
    org = detect_official_org(item.get("title"), item.get("journal_or_organization"),
                              item.get("authors"))
    if org:
        breakdown["official_source"] = 3
        item.setdefault("_detected_org", org)

    # Nguy cơ bias rõ
    if any(k in text for k in ("retrospective", "single-center", "single center",
                               "unblinded", "small sample", "cỡ mẫu nhỏ")):
        breakdown["bias_risk"] = -8
    # Xung đột lợi ích đáng kể
    if any(k in text for k in ("industry funded", "sponsored by", "tài trợ bởi công ty")):
        breakdown["coi"] = -5

    score = sum(breakdown.values())
    score = max(0.0, min(100.0, score))
    return round(score, 1), breakdown
