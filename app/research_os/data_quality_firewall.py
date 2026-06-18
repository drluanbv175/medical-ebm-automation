"""Data-quality firewall trước phân tích."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping


@dataclass(frozen=True)
class DataQualityReport:
    passed: bool
    issues: List[str] = field(default_factory=list)


def run_quality_firewall(dataset_profile: Mapping[str, object]) -> DataQualityReport:
    issues: List[str] = []
    if dataset_profile.get("has_pii"):
        issues.append("Dataset còn PII")
    if dataset_profile.get("missing_rate", 0) > 0.2:
        issues.append("Missing rate >20%")
    if not dataset_profile.get("data_dictionary"):
        issues.append("Thiếu data dictionary")
    return DataQualityReport(passed=not issues, issues=issues)
