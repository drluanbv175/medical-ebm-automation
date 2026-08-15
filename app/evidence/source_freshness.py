"""Đánh giá độ mới của nguồn."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class FreshnessAssessment:
    age_days: Optional[int]
    stale: bool
    message: str


def assess_freshness(
    publication_date: str,
    today: Optional[date] = None,
    max_age_days: int = 1095,
) -> FreshnessAssessment:
    if not publication_date:
        return FreshnessAssessment(None, True, "Thiếu ngày xuất bản/phiên bản")
    try:
        parsed = date.fromisoformat(publication_date[:10])
    except ValueError:
        return FreshnessAssessment(None, True, "Ngày xuất bản không hợp lệ")
    current = today or date.today()
    age = (current - parsed).days
    return FreshnessAssessment(age, age > max_age_days, "stale" if age > max_age_days else "current")
