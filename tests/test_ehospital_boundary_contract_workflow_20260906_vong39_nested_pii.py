"""Hồi quy phát hiện #9 (audit vòng 39, 2026-09-06) trong
research_project/ehospital_boundary_contract.py::ExtractRecord.__post_init__.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    found_pii = {k for k in self.data if k.lower() in self._PII_KEYS}
    if found_pii:
        raise ValueError(...)

Chỉ duyệt khoá CẤP 1 (top-level) của `self.data`. Một khoá PII nằm LỒNG bên
trong một dict con vô hại (vd `{"nested_info": {"name": "..."}}`) hoặc bên
trong một phần tử của list (vd `{"contacts": [{"phone": "..."}]}`) hoàn
toàn lọt qua kiểm tra — dù docstring của chính class cam kết
"Không chứa PII. Chỉ dùng trong nghiên cứu." và "data: must not contain
PII keys" mà không giới hạn "chỉ ở cấp 1".

PHẠM VI ẢNH HƯỞNG: ExtractRecord là ranh giới CUỐI CÙNG trước khi dữ liệu
trích xuất từ eHospital (dù chỉ là stub offline trong harness này) được
coi là "đã khử định danh, an toàn cho nghiên cứu". Một payload lồng nhau
(cấu trúc JSON thực tế từ HIS/EMR thường lồng nhiều tầng — vd
demographics.contact.phone) chứa PII ở cấp 2+ sẽ được __post_init__ CHẤP
NHẬN mà không báo lỗi, ngược hẳn với cam kết docstring của lớp."""
from __future__ import annotations

import pytest

from research_project.ehospital_boundary_contract import ExtractRecord

_BASE_KWARGS = dict(
    record_id="REC-001",
    pseudo_id="a" * 64,
    domain="laboratory_results",
    extracted_at_utc="2026-09-06T00:00:00Z",
)


class TestCaChinhPiiLongSauKhongDuocLot:
    """★★★ Ca chính — khoá PII nằm lồng trong dict con hoặc trong list phải
    bị phát hiện, không chỉ khoá PII ở cấp 1."""

    def test_pii_long_trong_dict_con_bi_chan(self):
        with pytest.raises(ValueError, match="potential PII keys"):
            ExtractRecord(
                data={"nested_info": {"name": "Nguyen Van A"}},
                **_BASE_KWARGS,
            )

    def test_pii_long_trong_list_cua_dict_bi_chan(self):
        with pytest.raises(ValueError, match="potential PII keys"):
            ExtractRecord(
                data={"contacts": [{"phone": "0900000000"}]},
                **_BASE_KWARGS,
            )

    def test_pii_long_hai_tang_sau_van_bi_chan(self):
        with pytest.raises(ValueError, match="potential PII keys"):
            ExtractRecord(
                data={"a": {"b": {"email": "x@example.invalid"}}},
                **_BASE_KWARGS,
            )

    def test_pii_trong_dict_ben_trong_list_long_ben_trong_dict_bi_chan(self):
        with pytest.raises(ValueError, match="potential PII keys"):
            ExtractRecord(
                data={"records": [{"inner": [{"mrn": "12345"}]}]},
                **_BASE_KWARGS,
            )


class TestDoiChungKhongPiiVanQuaDuocNhuCu:
    """Đối chứng — dữ liệu lồng nhau KHÔNG chứa khoá PII (dù sâu nhiều
    tầng) vẫn phải tạo ExtractRecord thành công như hành vi cũ."""

    def test_du_lieu_long_khong_pii_van_pass(self):
        record = ExtractRecord(
            data={"vitals": {"systolic_bp": 120, "diastolic_bp": 80}},
            **_BASE_KWARGS,
        )
        assert record.data["vitals"]["systolic_bp"] == 120

    def test_list_long_khong_pii_van_pass(self):
        record = ExtractRecord(
            data={"lab_panel": [{"test": "HbA1c", "value": 6.5}]},
            **_BASE_KWARGS,
        )
        assert record.data["lab_panel"][0]["test"] == "HbA1c"

    def test_pii_o_cap_1_van_bi_chan_nhu_truoc(self):
        with pytest.raises(ValueError, match="potential PII keys"):
            ExtractRecord(data={"name": "Nguyen Van A"}, **_BASE_KWARGS)

    def test_data_rong_van_pass(self):
        record = ExtractRecord(data={}, **_BASE_KWARGS)
        assert record.data == {}
