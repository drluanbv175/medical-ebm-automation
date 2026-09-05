"""Phân loại thay đổi chứng cứ mới."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class EvidenceChange:
    impact: str
    requires_review: bool
    reason: str


def classify_change(old: Mapping[str, str], new: Mapping[str, str]) -> EvidenceChange:
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 12) — bản gốc đòi CẢ HAI
    # old.get("conclusion") VÀ new.get("conclusion") đều truthy mới coi là thay đổi, nên
    # bỏ lọt đúng hai trường hợp quan trọng nhất: kết luận MỚI XUẤT HIỆN (old rỗng, new có
    # nội dung — một chủ đề từ "chưa có kết luận" sang "có kết luận hành động được", rơi
    # xuống "minor"/requires_review=False) và kết luận BỊ RÚT (old có nội dung, new rỗng).
    # Chỉ cần so sánh bất đẳng thức trực tiếp — bao trùm cả hai chiều lẫn trường hợp đổi
    # nội dung, và tự loại trường hợp cả hai đều rỗng (không phải thay đổi thật).
    if old.get("conclusion") != new.get("conclusion"):
        return EvidenceChange("practice_relevant", True, "Kết luận thay đổi")
    if old.get("safety_signal") != new.get("safety_signal") and new.get("safety_signal"):
        return EvidenceChange("safety", True, "Tín hiệu an toàn mới")
    if old.get("version") != new.get("version"):
        return EvidenceChange("version_update", True, "Cập nhật phiên bản nguồn")
    return EvidenceChange("minor", False, "Không phát hiện thay đổi có ý nghĩa vận hành")
