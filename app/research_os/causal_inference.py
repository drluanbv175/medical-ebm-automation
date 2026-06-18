"""Scaffold kiểm tra causal inference assumptions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CausalPlan:
    exposure: str
    outcome: str
    confounders: List[str]
    estimand: str

    def issues(self) -> List[str]:
        issues: List[str] = []
        if not self.confounders:
            issues.append("Chưa khai báo confounders/DAG tối thiểu")
        if not self.estimand:
            issues.append("Chưa khai báo estimand")
        return issues
