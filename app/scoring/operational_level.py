"""Operational Evidence Level (High/Moderate/Low).

Nếu nguồn có GRADE chính thức -> ghi theo nguồn (kèm nhãn 'official').
Nếu không có -> hệ thống gán mức VẬN HÀNH (operational estimate) và GHI RÕ đây
KHÔNG phải phân hạng chính thức. Đây là yêu cầu chống bịa đặt bắt buộc.
"""
from __future__ import annotations

from typing import Dict, Tuple


def operational_evidence_level(item: Dict, evidence_q: float) -> Tuple[str, bool]:
    """Trả về (level, is_official).

    is_official=True nghĩa là lấy theo GRADE chính thức của nguồn.
    """
    official = item.get("official_grade")
    if official:
        # Cố gắng ánh xạ về High/Moderate/Low nếu nguồn ghi rõ, nếu không giữ nguyên.
        text = str(official).lower()
        if "high" in text:
            return "High", True
        if "moderate" in text:
            return "Moderate", True
        if "low" in text or "very low" in text:
            return "Low", True
        # Có GRADE nhưng không rõ mức -> đánh dấu official theo nguồn.
        return f"Theo nguồn: {official}", True

    # Không có GRADE -> ước lượng vận hành từ evidence quality.
    if evidence_q >= 75:
        return "High (operational)", False
    if evidence_q >= 55:
        return "Moderate (operational)", False
    return "Low (operational)", False
