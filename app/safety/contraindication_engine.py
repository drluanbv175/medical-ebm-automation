"""Kiểm tra chống chỉ định khai báo theo rule cục bộ."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping


@dataclass(frozen=True)
class ContraindicationIssue:
    intervention: str
    reason: str
    severity: str = "high"


def check_contraindications(
    interventions: Iterable[str],
    contraindications: Mapping[str, Iterable[str]],
) -> List[ContraindicationIssue]:
    normalized = {item.lower().strip() for item in interventions}
    issues: List[ContraindicationIssue] = []
    for intervention, reasons in contraindications.items():
        if intervention.lower().strip() in normalized:
            for reason in reasons:
                issues.append(ContraindicationIssue(intervention=intervention, reason=str(reason)))
    return issues
