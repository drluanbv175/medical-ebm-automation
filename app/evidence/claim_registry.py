"""Claim registry liên kết mọi khuyến nghị với chứng cứ truy nguyên."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Mapping, Optional
from uuid import uuid4

from app.evidence.evidence_registry import EvidenceRegistry, EvidenceStatus


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    RETIRED = "retired"


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    text: str
    evidence_ids: List[str]
    claim_type: str = "clinical"
    grade_label: str = "ungraded"
    grade_source: str = ""
    status: ClaimStatus = ClaimStatus.DRAFT
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationCard:
    card_id: str
    claim_id: str
    headline: str
    action: str
    monitoring: str
    disclaimer: str = "Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."


class ClaimRegistry:
    def __init__(self, evidence_registry: EvidenceRegistry) -> None:
        self.evidence_registry = evidence_registry
        self.claims: Dict[str, ClaimRecord] = {}
        self.cards: Dict[str, RecommendationCard] = {}

    def register_claim(
        self,
        *,
        text: str,
        evidence_ids: List[str],
        claim_type: str = "clinical",
        grade_label: str = "ungraded",
        grade_source: str = "",
        status: ClaimStatus = ClaimStatus.DRAFT,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> ClaimRecord:
        if not evidence_ids:
            raise ValueError("Claim bắt buộc có ít nhất một evidence_id")
        for evidence_id in evidence_ids:
            record = self.evidence_registry.get(evidence_id)
            # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #85) — bản gốc chỉ
            # chặn QUARANTINED, KHÔNG chặn RETRACTED/SUPERSEDED. Rút bài/thay thế
            # KHÔNG xoá `has_traceability` (PMID/DOI vẫn còn) nên một claim có thể
            # được đăng ký dựa trên chứng cứ ĐÃ RÚT BÀI mà không bị chặn.
            if record.status in (EvidenceStatus.QUARANTINED, EvidenceStatus.RETRACTED,
                                  EvidenceStatus.SUPERSEDED) or not record.has_traceability:
                raise ValueError(
                    f"Evidence {evidence_id} không đủ điều kiện làm căn cứ cho claim "
                    f"(trạng thái: {record.status.value})"
                )
        if grade_label != "ungraded" and not grade_source:
            raise ValueError("Không được tự gán grade nếu thiếu grade_source")
        claim = ClaimRecord(
            claim_id=f"claim_{uuid4().hex}",
            text=text,
            evidence_ids=list(evidence_ids),
            claim_type=claim_type,
            grade_label=grade_label,
            grade_source=grade_source,
            status=status,
            metadata=dict(metadata or {}),
        )
        self.claims[claim.claim_id] = claim
        return claim

    def create_recommendation_card(
        self,
        claim_id: str,
        headline: str,
        action: str,
        monitoring: str,
    ) -> RecommendationCard:
        if claim_id not in self.claims:
            raise KeyError(claim_id)
        card = RecommendationCard(
            card_id=f"card_{uuid4().hex}",
            claim_id=claim_id,
            headline=headline,
            action=action,
            monitoring=monitoring,
        )
        self.cards[card.card_id] = card
        return card
