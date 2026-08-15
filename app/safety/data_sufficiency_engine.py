"""Đánh giá đủ dữ liệu trước khi tổng hợp lâm sàng."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Mapping


@dataclass(frozen=True)
class DataSufficiencyResult:
    sufficient: bool
    missing_fields: List[str] = field(default_factory=list)
    message: str = ""


def assess_data_sufficiency(case: Mapping[str, object], required_fields: Iterable[str]) -> DataSufficiencyResult:
    missing = [field for field in required_fields if case.get(field) in (None, "", [], {})]
    return DataSufficiencyResult(
        sufficient=not missing,
        missing_fields=missing,
        message="Đủ dữ liệu cho bản nháp" if not missing else "Thiếu: " + ", ".join(missing),
    )
