"""Evidence Quality Score (0–100).

Dựa trên: loại nghiên cứu/thiết kế, đa trung tâm, outcome lâm sàng vs surrogate,
guideline chính thức, có GRADE, nguy cơ bias, xung đột lợi ích.

Hàm trả về (score, breakdown) để giải thích minh bạch.
"""
from __future__ import annotations

import re
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
    # Cảnh báo cơ quan quản lý: NGUỒN đáng tin nhưng 1 tin feed ngắn KHÔNG phải chứng cứ
    # chất lượng cao. Để 60 (≤ ngưỡng Tier A) → mặc định cần đọc toàn văn trước khi hành động.
    "regulatory_alert": 60,
}


def _text(item: Dict, *keys: str) -> str:
    return " ".join(str(item.get(k, "") or "") for k in keys).lower()


def evidence_quality_score(item: Dict) -> Tuple[float, Dict[str, float]]:
    breakdown: Dict[str, float] = {}
    study_type = (item.get("study_type") or "").lower()
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 10) — mặc định cũ là
    # 40, CAO HƠN 6 thiết kế đã biết và tự khai là YẾU
    # (case_series/narrative_review=25, expert_opinion=20, editorial=15,
    # preprint=10, animal_invitro=5). `classify_meta.py` tự khai ý định:
    # "Khi không đủ tín hiệu -> trả None để pipeline xử lý THẬN TRỌNG (điểm
    # THẤP)" — mặc định 40 làm NGƯỢC lại đúng ý định đó, thưởng cho việc
    # KHÔNG xác định được thiết kế hơn là phạt việc thành thật khai yếu.
    # Xác nhận sống: cùng title/abstract, chỉ đổi study_type=None vs
    # "case_series" -> None cho eq=45/tier C trong khi case_series cho
    # eq=30/tier C — và None còn cao hơn cả editorial/preprint/animal_invitro
    # (đều tier D). Đưa về 0 — thấp hơn MỌI thiết kế đã đặt tên, đúng tinh
    # thần "không biết gì thì không được cộng điểm mặc định"; các cộng điểm
    # khác (đa trung tâm, outcome cứng, uy tín nguồn...) vẫn cộng bình
    # thường nếu văn bản có tín hiệu thật.
    base = DESIGN_BASE.get(study_type, 0)
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

    # Cỡ mẫu lớn: bắt cỡ mẫu THẬT (n = <số> ≥ 1000), không dùng token cứng dễ dương tính giả.
    _n = re.search(r"\bn\s*=\s*(\d[\d,]{2,})", text)
    _big_n = bool(_n and int(_n.group(1).replace(",", "")) >= 1000)
    if _big_n or any(k in text for k in ("multicenter trial", "large multinational",
                                         "multinational cohort", "thousands of patients")):
        breakdown["large_sample"] = 3

    # Guideline chính thức / GRADE
    if study_type == "guideline":
        breakdown["official_guideline"] = 5
    if item.get("official_grade"):
        breakdown["has_grade"] = 4

    # Nguồn từ tổ chức/tạp chí chính thống (ESC, AHA, NICE, NEJM, Lancet...)
    from app.sources.authority import authority_breakdown_for
    authority, authority_breakdown = authority_breakdown_for((
        item.get("journal_or_organization"),
        item.get("source"),
        item.get("authors"),
        item.get("title"),
    ))
    if authority:
        breakdown.update(authority_breakdown)
        item.setdefault("_detected_org", authority.name)
        item.setdefault("_authority_tier", authority.tier)
        item.setdefault("_authority_category", authority.category)

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
