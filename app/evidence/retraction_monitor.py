"""Theo dõi retract/supersede từ metadata nguồn.

CẢNH BÁO: đây KHÔNG PHẢI cơ chế retraction-check đang được dùng thật trong pipeline
G0-G9. retraction_monitor.detect_retraction() chỉ đọc field 'retracted'/'withdrawn'
đã có sẵn trong metadata truyền vào — KHÔNG tự tra cứu gì. Cơ chế THẬT (tự tra cứu
PubMed E-utilities sống) nằm ở app/sources/pubmed.py::PubMedClient.check_retraction_status(),
dùng bởi tools/check_citation_retraction.py + cổng A12 trong tools/run_g10_assemble.py.
Module này là 1 trong 5 nhánh mồ côi đã ghi nhận trong CLAUDE.md — không xoá vì có thể
còn dùng nội bộ/thử nghiệm, nhưng KHÔNG dùng làm cơ chế retraction-check chính thức.
"""
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
