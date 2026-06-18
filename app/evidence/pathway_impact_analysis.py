"""Đánh giá ảnh hưởng chứng cứ lên pathway lâm sàng."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PathwayImpact:
    pathway_id: str
    affected_steps: List[str]
    requires_retraining: bool
    requires_dashboard_update: bool


def analyze_pathway_impact(pathway_id: str, changed_claim_ids: List[str]) -> PathwayImpact:
    return PathwayImpact(
        pathway_id=pathway_id,
        affected_steps=list(changed_claim_ids),
        requires_retraining=bool(changed_claim_ids),
        requires_dashboard_update=bool(changed_claim_ids),
    )
