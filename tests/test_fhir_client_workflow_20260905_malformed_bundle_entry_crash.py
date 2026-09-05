"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 17) trong app/integrations/fhir_client.py::search_resources() và
extract_medication_requests().

CƠ CHẾ LỖI: cả hai hàm giả định MỌI phần tử của danh sách (Bundle.entry
hoặc danh sách resource) là dict. Bundle FHIR là dữ liệu từ MÁY CHỦ THẬT
(EMR/HIS ngoài dự án — đúng docstring module "phải hỗ trợ FHIR R4"), nên
một entry/resource không tuân thủ spec (không phải dict — số, chuỗi…) làm:
- `search_resources()`: `"resource" in e` ném TypeError nếu `e` là số (không
  iterable), hoặc đổi nghĩa thành kiểm tra substring nếu `e` là chuỗi.
- `extract_medication_requests()`: `r.get("resourceType")` ném AttributeError
  nếu `r` không phải dict.
Cả hai lỗi MẤT TOÀN BỘ resource hợp lệ khác trong cùng danh sách/Bundle —
kể cả bệnh nhân/đơn thuốc đứng trước/sau entry lỗi — thay vì chỉ bỏ qua
đúng entry hỏng. Đây là cùng lớp lỗi "một bản ghi hỏng làm sập cả lô" đã
gặp ở europepmc.py/pubmed.py.

BẢN VÁ: thêm `isinstance(e, dict)` / `isinstance(r, dict)` trước khi truy
cập trường, bỏ qua CHỈ phần tử không phải dict.

Nguyên tắc viết test: gọi THẲNG `FhirClient.search_resources()` (qua
monkeypatch `search()` để tiêm Bundle giả, không mock mạng thật) và
`extract_medication_requests()` thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.integrations.fhir_client import (  # noqa: E402
    FhirClient,
    extract_medication_requests,
)


class TestMotEntryHongKhongLamMatResourceHopLeKhac:
    """★★★ Ca chính — Bundle.entry / danh sách resource chứa MỘT phần tử
    không phải dict không được làm sập/mất các phần tử hợp lệ khác."""

    def test_search_resources_bo_qua_entry_khong_phai_dict_giu_resource_hop_le(self):
        client = FhirClient("https://example.org/fhir")
        client.search = lambda resource_type, params=None: {
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "1"}},
                42,
                "malformed-entry",
                None,
                {"resource": {"resourceType": "Patient", "id": "2"}},
            ]
        }

        out = client.search_resources("Patient")

        assert [r["id"] for r in out] == ["1", "2"], (
            "TRƯỚC bản vá: entry không phải dict (vd số nguyên) làm "
            "'\"resource\" in e' ném TypeError, sập toàn bộ search_resources() "
            "và mất luôn cả 2 Patient hợp lệ"
        )

    def test_extract_medication_requests_bo_qua_resource_khong_phai_dict(self):
        resources = [
            {"resourceType": "MedicationRequest", "status": "active", "intent": "order",
             "medicationCodeableConcept": {"text": "Metoprolol 25mg"}},
            "not-a-dict-malformed-entry",
            123,
            {"resourceType": "MedicationRequest", "status": "completed", "intent": "order",
             "medicationCodeableConcept": {"text": "Aspirin"}},
        ]

        out = extract_medication_requests(resources)

        assert [m["medication"] for m in out] == ["Metoprolol 25mg", "Aspirin"], (
            "TRƯỚC bản vá: resource không phải dict (chuỗi/số) làm "
            "r.get(...) ném AttributeError, sập toàn bộ hàm và mất luôn cả "
            "2 MedicationRequest hợp lệ"
        )


class TestDuLieuHopLeThuanTuyVanGiuHanhViCu:
    """Đối chứng bắt buộc — Bundle/danh sách CHỈ chứa dict hợp lệ (hành vi
    gốc) vẫn hoạt động đúng như trước bản vá."""

    def test_search_resources_toan_bo_hop_le(self):
        client = FhirClient("https://example.org/fhir")
        client.search = lambda resource_type, params=None: {
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "1"}},
                {"resource": {"resourceType": "Patient", "id": "2"}},
            ]
        }
        out = client.search_resources("Patient")
        assert [r["id"] for r in out] == ["1", "2"]

    def test_extract_medication_requests_bo_qua_patient_lan_trong_theo_resourcetype(self):
        resources = [
            {"resourceType": "MedicationRequest", "status": "active", "intent": "order",
             "medicationCodeableConcept": {"coding": [{"display": "Aspirin"}]}},
            {"resourceType": "Patient", "gender": "male"},  # phải bị bỏ qua theo resourceType
        ]
        out = extract_medication_requests(resources)
        assert len(out) == 1
        assert out[0]["medication"] == "Aspirin"

    def test_search_resources_bundle_rong(self):
        client = FhirClient("https://example.org/fhir")
        client.search = lambda resource_type, params=None: {}
        assert client.search_resources("Patient") == []
