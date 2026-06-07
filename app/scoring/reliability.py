"""Reliability Tier (A/B/C/D).

A: Có thể cân nhắc thay đổi thực hành ngay nếu phù hợp bối cảnh.
B: Cần đọc toàn văn/guideline gốc trước khi triển khai.
C: Chỉ theo dõi, chưa thay đổi thực hành.
D: Loại khỏi báo cáo chính.
"""
from __future__ import annotations

from typing import Dict

# Các thiết kế bị loại khỏi phần "thay đổi thực hành" -> D.
EXCLUDED_DESIGNS = {
    "preprint", "animal_invitro", "editorial", "narrative_review",
}


def reliability_tier(item: Dict, evidence_q: float, practice_c: float) -> str:
    study_type = (item.get("study_type") or "").lower()

    # D: loại trừ rõ ràng
    if study_type in EXCLUDED_DESIGNS:
        return "D"
    if item.get("reason_for_exclusion"):
        return "D"

    # A: nguồn rất mạnh + tiềm năng đổi thực hành cao.
    # regulatory_alert KHÔNG nằm đây: cảnh báo cơ quan quản lý cần đọc toàn văn (tối đa Tier B),
    # tránh 1 tin feed ngắn tự lên "actionable".
    strong_source = study_type in ("guideline", "systematic_review", "rct")
    if strong_source and evidence_q >= 75 and practice_c >= 60:
        return "A"

    # B: đủ mạnh nhưng cần đọc toàn văn/guideline gốc
    if evidence_q >= 60 and practice_c >= 45:
        return "B"

    # C: chỉ theo dõi
    return "C"
