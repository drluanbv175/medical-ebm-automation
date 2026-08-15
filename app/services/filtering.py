"""Bước 4: Evidence filtering – áp bộ lọc chứng cứ bắt buộc.

Phân loại thành: actionable | need_full_text | watch_only | excluded.
Mỗi bản ghi PHẢI có lý do (actionable_reason hoặc reason_for_exclusion).
"""
from __future__ import annotations

from typing import Dict, Tuple

from app.config import settings

# Thiết kế bị loại khỏi phần "thay đổi thực hành" (mục 4.4).
EXCLUDED_STUDY_TYPES = {
    "preprint", "animal_invitro", "editorial", "narrative_review",
}
EXCLUDE_KEYWORDS = ("advertisement", "press release", "quảng cáo", "company pr")

# Từ khóa nhận diện chủ đề kháng sinh (dùng CHUNG cho báo cáo + dashboard, tránh trùng lặp).
ANTIBIOTIC_KEYWORDS = ("antibiotic", "antimicrobial", "stewardship",
                       "kháng sinh", "aware", "pneumonia")


def is_antibiotic_text(*parts) -> bool:
    """True nếu bất kỳ phần văn bản nào (title/abstract/keywords/source) chứa từ khóa kháng sinh."""
    text = " ".join(str(p or "") for p in parts).lower()
    return any(k in text for k in ANTIBIOTIC_KEYWORDS)


def classify(item: Dict) -> Tuple[str, bool, str, str]:
    """Trả về (classification, is_actionable, actionable_reason, reason_for_exclusion)."""
    study_type = (item.get("study_type") or "").lower()
    eq = float(item.get("evidence_quality_score") or 0)
    pc = float(item.get("practice_change_score") or 0)
    tier = item.get("reliability_tier") or "C"
    text = " ".join(str(item.get(k, "") or "") for k in ("title", "abstract")).lower()

    # 1) Loại trừ tuyệt đối
    if study_type in EXCLUDED_STUDY_TYPES:
        return ("excluded", False, "",
                f"Loại thiết kế '{study_type}' không dùng để thay đổi thực hành (mục 4.4).")
    if any(k in text for k in EXCLUDE_KEYWORDS):
        return ("excluded", False, "", "Phát hiện dấu hiệu quảng cáo/PR, loại khỏi báo cáo chính.")
    if not item.get("title"):
        return ("excluded", False, "", "Tài liệu không có tiêu đề/không truy xuất được nguồn gốc.")
    if tier == "D":
        return ("excluded", False, "", "Reliability Tier D – loại khỏi báo cáo chính.")

    # 2) Actionable: đạt ngưỡng cấu hình + tier A
    if (eq >= settings.min_evidence_score and pc >= settings.min_practice_change_score
            and tier == "A"):
        reason = (f"Tier A, Evidence={eq:.0f}≥{settings.min_evidence_score}, "
                  f"PracticeChange={pc:.0f}≥{settings.min_practice_change_score}. "
                  "Nguồn mạnh, có hành động cụ thể, áp dụng được.")
        return ("actionable", True, reason, "")

    # 3) Cần đọc toàn văn / guideline gốc
    if tier == "B" or (eq >= 60 and pc >= 45):
        reason_x = ("Bằng chứng/khả năng đổi thực hành ở mức trung bình; "
                    "cần đọc toàn văn hoặc guideline gốc trước khi triển khai.")
        return ("need_full_text", False, "", reason_x)

    # 4) Chỉ theo dõi
    return ("watch_only", False, "",
            "Chứng cứ chưa đủ mạnh hoặc tác động thực hành thấp; chỉ theo dõi (watch).")
