"""Ma trận truy nguyên nghiên cứu: question -> variable -> analysis -> output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TraceabilityRow:
    research_question: str
    variable_name: str
    analysis_step: str
    output_table: str


def validate_traceability(rows: List[TraceabilityRow]) -> List[str]:
    issues: List[str] = []
    for index, row in enumerate(rows, start=1):
        if not row.research_question or not row.variable_name or not row.analysis_step or not row.output_table:
            issues.append(f"Row {index} thiếu trường truy nguyên")
    return issues
