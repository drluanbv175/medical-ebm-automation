"""Research health score cho dashboard nghiên cứu."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ResearchHealthScore:
    score: int
    blockers: List[str]


def calculate_research_health_score(blockers: List[str], warnings: List[str]) -> ResearchHealthScore:
    score = max(0, 100 - 20 * len(blockers) - 5 * len(warnings))
    return ResearchHealthScore(score=score, blockers=list(blockers))
