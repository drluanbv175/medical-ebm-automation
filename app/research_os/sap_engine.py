"""Statistical Analysis Plan engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class SapStatus(str, Enum):
    DRAFT = "draft"
    LOCKED = "locked"


@dataclass(frozen=True)
class StatisticalAnalysisPlan:
    sap_id: str
    primary_analysis: str
    secondary_analyses: List[str] = field(default_factory=list)
    status: SapStatus = SapStatus.DRAFT

    def can_run_official_analysis(self, data_locked: bool) -> bool:
        return self.status is SapStatus.LOCKED and data_locked


def lock_sap(sap: StatisticalAnalysisPlan) -> StatisticalAnalysisPlan:
    return StatisticalAnalysisPlan(
        sap_id=sap.sap_id,
        primary_analysis=sap.primary_analysis,
        secondary_analyses=list(sap.secondary_analyses),
        status=SapStatus.LOCKED,
    )
