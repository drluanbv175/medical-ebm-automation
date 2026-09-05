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
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 9) — `approved_by_
        # physician` khai kiểu `bool` nhưng Python không ép kiểu ở runtime;
        # `and` dùng TRUTHINESS nên một giá trị chuỗi non-empty mang Ý NGHĨA
        # "chưa duyệt" (vd "chưa duyệt"/"no"/"false" — hoàn toàn khả dĩ nếu
        # một lớp deserialize JSON/form tương lai truyền nhầm kiểu) vẫn được
        # coi là True, cho phép xuất nội dung giáo dục bệnh nhân CHƯA được
        # bác sĩ duyệt. Đây là cổng an toàn DUY NHẤT của toàn dataclass, nên
        # dùng identity `is True` — an toàn hơn theo đúng hướng cần: từ chối
        # xuất khi giá trị không phải bool thật, thay vì đoán ý định.
        return self.approved_by_physician is True and "Cần bác sĩ kiểm chứng" in self.body


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
