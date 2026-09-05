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
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 10) — thứ tự kiểm
        # cũ (high -> moderate -> low) chỉ khớp CHUỖI CON, không hiểu ngữ
        # cảnh: văn bản tự do như "Downgraded from high to low" hay "High
        # risk of bias, low certainty" đều CHỨA chữ "high" nên bị báo "High"
        # dù kết luận thật của câu là "low" — đảo ngược đúng mức độ tin cậy
        # hiển thị cho bác sĩ như thể đó là phân hạng CHÍNH THỨC
        # (is_official=True). Xác nhận sống: operational_evidence_level(
        # {"official_grade": "Downgraded from high to low"}, 50) trả về
        # ("High", True) — SAI, phải là ("Low", True).
        # Đảo thứ tự kiểm THẤP -> TRUNG BÌNH -> CAO (thận trọng nhất trước):
        # cùng nguyên tắc "ưu tiên diễn giải thận trọng khi văn bản mơ hồ"
        # đã dùng ở nhiều nơi khác trong repo — một câu vừa nhắc "cao" vừa
        # nhắc "thấp"/"trung bình" thì mức THẤP HƠN luôn là kết luận được ưu
        # tiên báo cáo, không phải mức cao xuất hiện tình cờ trước đó.
        if "low" in text:
            return "Low", True
        if "moderate" in text:
            return "Moderate", True
        if "high" in text:
            return "High", True
        # Có GRADE nhưng không rõ mức -> đánh dấu official theo nguồn.
        return f"Theo nguồn: {official}", True

    # Không có GRADE -> ước lượng vận hành từ evidence quality.
    if evidence_q >= 75:
        return "High (operational)", False
    if evidence_q >= 55:
        return "Moderate (operational)", False
    return "Low (operational)", False
