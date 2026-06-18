"""Compiler protocol nghiên cứu từ registry + SAP."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ProtocolDraft:
    title: str
    design: str
    objectives: List[str]
    outcomes: List[str]
    ethics_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.objectives:
            raise ValueError("Protocol thiếu objectives")
        if not self.outcomes:
            raise ValueError("Protocol thiếu outcomes")


def compile_protocol(title: str, design: str, objectives: List[str], outcomes: List[str]) -> ProtocolDraft:
    draft = ProtocolDraft(title=title, design=design, objectives=list(objectives), outcomes=list(outcomes))
    draft.validate()
    return draft
