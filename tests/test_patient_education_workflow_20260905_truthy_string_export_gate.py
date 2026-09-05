"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 9,
task #94) trong
`app/patient_education/patient_education.py::PatientEducationLeaflet.can_export()`
— cổng duyệt bác sĩ dùng TRUTHINESS thay vì kiểm giá trị `bool` thật.

CƠ CHẾ LỖI: `approved_by_physician` khai kiểu `bool` (cả ở dataclass field
lẫn tham số `create_leaflet()`) nhưng Python không ép kiểu ở runtime.
`can_export()` bản gốc dùng `self.approved_by_physician and "..." in
self.body` — TRUTHINESS, không phải kiểm giá trị đúng `bool`. Một chuỗi
non-empty MANG Ý NGHĨA "chưa duyệt" (vd "chưa duyệt"/"no"/"false" — hoàn
toàn khả dĩ nếu một lớp deserialize JSON/form tương lai truyền nhầm kiểu
dữ liệu) vẫn được Python coi là truthy, khiến `can_export()` trả `True` dù
bác sĩ CHƯA duyệt.

Xác nhận sống: create_leaflet(..., approved_by_physician="chưa duyệt")
-> can_export() == True (SAI — phải là False).

BẢN VÁ: `self.approved_by_physician is True` — chỉ chấp nhận giá trị `bool`
`True` thật, mọi giá trị khác (kể cả chuỗi truthy) đều bị từ chối. Đây là
cổng an toàn DUY NHẤT của dataclass này nên hướng an toàn là TỪ CHỐI xuất
khi giá trị không phải bool thật.

Nguyên tắc viết test: gọi THẲNG `create_leaflet()`/`PatientEducationLeaflet`
thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.patient_education.patient_education import (  # noqa: E402
    PatientEducationLeaflet,
    create_leaflet,
)

_APPROVED_BODY = "Nội dung giáo dục đã được bác sĩ kiểm tra.\n\nCần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."


class TestChuoiTruthyKhongDuocCoiLaDaDuyet:
    """★★★ Ca chính — giá trị chuỗi non-empty (kể cả mang nghĩa "chưa
    duyệt") phải bị TỪ CHỐI xuất, không được coi là True."""

    def test_chuoi_chua_duyet_khong_duoc_xuat(self):
        leaflet = create_leaflet("X", _APPROVED_BODY, approved_by_physician="chưa duyệt")
        assert leaflet.can_export() is False

    def test_chuoi_false_khong_duoc_xuat(self):
        """"false" là chuỗi non-empty -> truthy trong Python -- đúng bẫy cổ
        điển mà bản vá phải chặn."""
        leaflet = create_leaflet("X", _APPROVED_BODY, approved_by_physician="false")
        assert leaflet.can_export() is False

    def test_so_1_khong_duoc_xuat(self):
        leaflet = create_leaflet("X", _APPROVED_BODY, approved_by_physician=1)
        assert leaflet.can_export() is False


class TestBoolThatVanHoatDongNhuCu:
    """Đối chứng bắt buộc — giá trị `bool` thật (True/False) vẫn hoạt động
    đúng hành vi gốc."""

    def test_true_that_van_xuat_duoc(self):
        leaflet = create_leaflet("X", _APPROVED_BODY, approved_by_physician=True)
        assert leaflet.can_export() is True

    def test_false_that_khong_xuat_duoc(self):
        leaflet = create_leaflet("X", _APPROVED_BODY, approved_by_physician=False)
        assert leaflet.can_export() is False

    def test_mac_dinh_false_khong_xuat_duoc(self):
        leaflet = create_leaflet("X", _APPROVED_BODY)
        assert leaflet.can_export() is False


class TestThieuDisclaimerVanChanXuatNhuCu:
    """Đối chứng bắt buộc — dù `approved_by_physician=True`, thiếu câu
    disclaimer trong body vẫn phải chặn xuất (luật thứ hai của cổng,
    không bị bản vá vô tình vô hiệu hoá)."""

    def test_thieu_disclaimer_van_bi_chan(self):
        leaflet = PatientEducationLeaflet(
            topic="X", language="vi", body="Nội dung không có câu bắt buộc.",
            approved_by_physician=True,
        )
        assert leaflet.can_export() is False
