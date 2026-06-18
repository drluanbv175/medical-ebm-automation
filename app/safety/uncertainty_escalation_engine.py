"""Escalate khi độ bất định vượt ngưỡng."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class UncertaintyAssessment:
    score: float
    reasons: List[str]
    escalate: bool


def assess_uncertainty(reasons: List[str], threshold: int = 2) -> UncertaintyAssessment:
    score = min(len(reasons) / max(threshold, 1), 1.0)
    return UncertaintyAssessment(score=score, reasons=list(reasons), escalate=len(reasons) >= threshold)
