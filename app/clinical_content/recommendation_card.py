"""Recommendation card chuẩn hóa cho UI/agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ClinicalRecommendationCard:
    card_id: str
    claim_id: str
    question: str
    recommendation: str
    evidence_summary: str
    applicability: str
    monitoring: str
    uncertainty: List[str] = field(default_factory=list)
    disclaimer: str = "Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."

    def patient_facing_allowed(self, physician_approved: bool) -> bool:
        return physician_approved and not self.uncertainty
