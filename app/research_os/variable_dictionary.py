"""Từ điển biến nghiên cứu."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class VariableDefinition:
    name: str
    label: str
    data_type: str
    allowed_values: str = ""
    source: str = ""


def validate_variable_dictionary(variables: Iterable[VariableDefinition]) -> List[str]:
    seen: Dict[str, int] = {}
    issues: List[str] = []
    for var in variables:
        seen[var.name] = seen.get(var.name, 0) + 1
        if not var.label or not var.data_type:
            issues.append(f"{var.name}: thiếu label/data_type")
    issues.extend(name + ": trùng tên biến" for name, count in seen.items() if count > 1)
    return issues
