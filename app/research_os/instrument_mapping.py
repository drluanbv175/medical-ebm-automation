"""Mapping công cụ đo lường sang biến nghiên cứu."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class InstrumentMap:
    instrument_name: str
    variable_name: str
    scoring_rule: str


def missing_instrument_mappings(required_variables: List[str], mappings: List[InstrumentMap]) -> List[str]:
    mapped = {item.variable_name for item in mappings}
    return [var for var in required_variables if var not in mapped]
