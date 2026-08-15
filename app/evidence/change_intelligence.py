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
    if old.get("conclusion") and new.get("conclusion") and old.get("conclusion") != new.get("conclusion"):
        return EvidenceChange("practice_relevant", True, "Kết luận thay đổi")
    if old.get("safety_signal") != new.get("safety_signal") and new.get("safety_signal"):
        return EvidenceChange("safety", True, "Tín hiệu an toàn mới")
    if old.get("version") != new.get("version"):
        return EvidenceChange("version_update", True, "Cập nhật phiên bản nguồn")
    return EvidenceChange("minor", False, "Không phát hiện thay đổi có ý nghĩa vận hành")
