"""Chuẩn Clinical Knowledge Pack V7."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping


@dataclass(frozen=True)
class ClinicalKnowledgePack:
    pack_id: str
    topic: str
    version: str
    scope: str
    evidence_ids: List[str]
    claim_ids: List[str]
    pathway_ids: List[str] = field(default_factory=list)
    vietnam_localization: Mapping[str, str] = field(default_factory=dict)
    safety_notes: List[str] = field(default_factory=list)
    disclaimer: str = "Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."

    def validate(self) -> None:
        if not self.evidence_ids:
            raise ValueError("Knowledge pack bắt buộc có evidence_ids")
        if not self.claim_ids:
            raise ValueError("Knowledge pack bắt buộc có claim_ids")
        if "Cần bác sĩ kiểm chứng" not in self.disclaimer:
            raise ValueError("Thiếu disclaimer bắt buộc")
