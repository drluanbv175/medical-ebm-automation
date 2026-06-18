"""Tạo nội dung giáo dục bệnh nhân chỉ sau khi bác sĩ duyệt."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatientEducationLeaflet:
    topic: str
    language: str
    body: str
    approved_by_physician: bool

    def can_export(self) -> bool:
        return self.approved_by_physician and "Cần bác sĩ kiểm chứng" in self.body


def create_leaflet(
    topic: str,
    body: str,
    approved_by_physician: bool = False,
    language: str = "vi",
) -> PatientEducationLeaflet:
    disclaimer = "Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."
    if disclaimer not in body:
        body = body.rstrip() + "\n\n" + disclaimer
    return PatientEducationLeaflet(
        topic=topic,
        language=language,
        body=body,
        approved_by_physician=approved_by_physician,
    )
