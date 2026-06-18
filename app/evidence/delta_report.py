"""Tạo báo cáo delta ngắn cho cập nhật EBM."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DeltaReport:
    topic: str
    added: List[str]
    changed: List[str]
    quarantined: List[str]

    def summary(self) -> str:
        return (
            f"{self.topic}: thêm {len(self.added)}, thay đổi {len(self.changed)}, "
            f"cách ly {len(self.quarantined)} nguồn thiếu truy nguyên."
        )
