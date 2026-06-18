"""Theo dõi retract/supersede từ metadata nguồn."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RetractionSignal:
    affected: bool
    reason: str


def detect_retraction(metadata: Mapping[str, str]) -> RetractionSignal:
    text = " ".join(str(v).lower() for v in metadata.values())
    if "retracted" in text or "withdrawn" in text:
        return RetractionSignal(True, "Nguồn có dấu hiệu retracted/withdrawn")
    if "expression of concern" in text:
        return RetractionSignal(True, "Nguồn có expression of concern")
    return RetractionSignal(False, "Không phát hiện tín hiệu retract trong metadata đã cung cấp")
