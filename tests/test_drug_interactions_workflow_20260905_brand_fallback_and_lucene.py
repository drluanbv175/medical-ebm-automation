"""Hồi quy 2 phát hiện CRITICAL của Workflow đối kháng đa-agent 2026-09-05 (vòng 5) trong
`app/integrations/drug_interactions.py::DrugSafetyChecker.fetch_label()`.

═══ TASK #77 — không fallback sang brand name khi generic_name 404 ═══════════════════════
CƠ CHẾ LỖI: `fetch_label()` lặp qua ("openfda.generic_name", "openfda.brand_name") để tra
nhãn openFDA. openFDA trả **HTTP 404** (KHÔNG phải 200 kèm `results: []`) khi một trường tìm
kiếm không khớp bản ghi nào — `app/utils/http.py::HttpClient._request()` xếp 404 vào
`_PERMANENT_STATUS` nên `get_json()` raise `requests.HTTPError` NGAY, không trả về dict rỗng.
Bản gốc bắt MỌI exception ở field ĐẦU TIÊN rồi `raise DrugInteractionError` ngay lập tức —
vòng lặp không bao giờ chạm tới field THỨ HAI (brand_name).

HẬU QUẢ LÂM SÀNG: một bác sĩ nhập TÊN BIỆT DƯỢC (vd "Lipitor" thay vì hoạt chất
"atorvastatin") sẽ luôn nhận 404 ở field generic_name → hàm dừng NGAY, không bao giờ thử
field brand_name lẽ ra khớp được — toàn bộ sàng lọc tương tác/chống chỉ định cho thuốc đó bị
BỎ QUA mà không có cảnh báo nào (không phải `not_found`, mà là `lookup_failed` — khác nghĩa,
và khiến bác sĩ tưởng có lỗi mạng thay vì "chưa thử đủ tên").

BẢN VÁ: 404 ở MỘT field nghĩa là "trường này không khớp" — không phải lỗi thật — nên tiếp
tục thử field kế tiếp thay vì raise ngay. Exception KHÁC 404 (mạng lỗi, 5xx, timeout…) vẫn
raise `DrugInteractionError` như cũ — KHÔNG được nuốt lỗi thật.

═══ TASK #78 — Lucene injection giống openfda.py (task #75) cùng đợt ═══════════════════════
CƠ CHẾ LỖI: `params = {"search": f'{field}:"{drug.strip()}"', ...}` nhét tên thuốc THẲNG vào
cụm trích dẫn Lucene không thoát dấu `"` — cùng lớp lỗi vừa vá ở
`app/sources/openfda.py::_escape_lucene_phrase()` (task #75) nhưng KHÔNG được lan sang file
này. BẢN VÁ thêm `_escape_lucene_phrase()` RIÊNG cho module này (không import hàm `_`-prefix
xuyên module — phá vỡ tín hiệu "nội bộ" của tiền tố đó).

Nguyên tắc viết test: gọi THẲNG `fetch_label()`/`_escape_lucene_phrase()` thật qua một
FakeHttp giả lập đúng ngữ nghĩa 404-per-field của openFDA (raise `requests.HTTPError` với
`.response.status_code`), không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.integrations.drug_interactions import (  # noqa: E402
    DrugInteractionError,
    DrugSafetyChecker,
    _escape_lucene_phrase,
)


def _http_error(status_code: int) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = status_code
    return requests.HTTPError(f"{status_code} lỗi giả lập", response=resp)


class FakeHttpFieldAware:
    """FakeHttp phân biệt theo FIELD trong params['search'] — mô phỏng đúng ngữ nghĩa
    404-per-field của openFDA thật (khác FakeHttp cũ trong test_drug_interactions.py, vốn
    luôn trả `{"results": []}` — không tái hiện được lỗi 404 nên chưa từng bắt được bug này)."""

    def __init__(self, *, raise_status_by_field: dict, result_by_field: dict | None = None):
        self.raise_status_by_field = raise_status_by_field
        self.result_by_field = result_by_field or {}
        self.calls: list[str] = []

    def get_json(self, url, params=None, use_cache=True):
        search = (params or {}).get("search", "")
        field = search.split(":", 1)[0]
        self.calls.append(search)
        if field in self.raise_status_by_field:
            raise _http_error(self.raise_status_by_field[field])
        if field in self.result_by_field:
            return {"results": [self.result_by_field[field]]}
        return {"results": []}


def _raw_label(generic: str, brand: str) -> dict:
    return {
        "openfda": {"generic_name": [generic], "brand_name": [brand],
                    "spl_set_id": ["SET-" + generic]},
        "set_id": "SET-" + generic,
        "drug_interactions": ["Có thể tương tác với warfarin."],
    }


class TestFallbackSangBrandNameSauKhi404GenericName:
    """★★★ Ca chính TASK #77 — generic_name 404, brand_name khớp → PHẢI trả về nhãn, không
    được dừng ở field đầu."""

    def test_generic_404_brand_khop_van_tra_ve_nhan(self):
        http = FakeHttpFieldAware(
            raise_status_by_field={"openfda.generic_name": 404},
            result_by_field={"openfda.brand_name": _raw_label("atorvastatin", "Lipitor")},
        )
        chk = DrugSafetyChecker(http=http)
        label = chk.fetch_label("Lipitor")
        assert label is not None, "phải fallback sang brand_name khi generic_name 404"
        assert "atorvastatin" in [g.lower() for g in label["generic_names"]]
        # Đối chứng: cả hai field đều PHẢI được thử (không dừng ở field đầu).
        assert len(http.calls) == 2

    def test_ca_hai_field_404_tra_ve_none_khong_raise(self):
        """Cả hai field đều 404 (thuốc thật sự không có trong openFDA) — vẫn phải trả về
        None như thiết kế gốc (không phải lỗi), KHÔNG raise DrugInteractionError."""
        http = FakeHttpFieldAware(
            raise_status_by_field={"openfda.generic_name": 404, "openfda.brand_name": 404},
        )
        chk = DrugSafetyChecker(http=http)
        assert chk.fetch_label("thuoc_khong_ton_tai") is None
        assert len(http.calls) == 2


class TestLoiThatKhac404VanRaiseNgay:
    """★★ Đối chứng BẮT BUỘC — một lỗi THẬT (không phải 404) vẫn phải raise
    DrugInteractionError ngay, KHÔNG được nuốt lỗi thật rồi âm thầm coi là "không tìm thấy"."""

    def test_loi_500_van_raise_ngay_khong_thu_field_ke(self):
        http = FakeHttpFieldAware(raise_status_by_field={"openfda.generic_name": 500})
        chk = DrugSafetyChecker(http=http)
        with pytest.raises(DrugInteractionError):
            chk.fetch_label("aspirin")

    def test_loi_mang_khong_phai_httperror_van_raise(self):
        class BoomHttp:
            def get_json(self, url, params=None, use_cache=True):
                raise RuntimeError("network down")

        chk = DrugSafetyChecker(http=BoomHttp())
        with pytest.raises(DrugInteractionError):
            chk.fetch_label("aspirin")


class TestEscapeLucenePhraseHamNguon:
    """★★ TASK #78 — hàm thoát ký tự tự thân, kiểm trực tiếp không qua HTTP."""

    def test_dau_ngoac_kep_duoc_thoat(self):
        assert _escape_lucene_phrase('drug"injected') == 'drug\\"injected'

    def test_dau_gach_cheo_nguoc_duoc_thoat_truoc(self):
        assert _escape_lucene_phrase('a\\"b') == 'a\\\\\\"b'

    def test_chuoi_binh_thuong_khong_doi(self):
        assert _escape_lucene_phrase("atorvastatin") == "atorvastatin"


class TestFetchLabelThoatDauNgoacKepTruocKhiGui:
    """★★ Ca tích hợp — fetch_label() thật phải gửi tham số `search` đã thoát, không còn
    dấu `"` trần từ tên thuốc gốc có thể đóng cụm trích dẫn Lucene sớm."""

    def test_ten_thuoc_co_dau_ngoac_kep_duoc_thoat_truoc_khi_gui(self):
        http = FakeHttpFieldAware(raise_status_by_field={
            "openfda.generic_name": 404, "openfda.brand_name": 404,
        })
        chk = DrugSafetyChecker(http=http)
        chk.fetch_label('drug" OR patient.patientdeath.patientdeathdate:*')
        assert http.calls[0] == (
            'openfda.generic_name:"drug\\" OR '
            'patient.patientdeath.patientdeathdate:*"'
        )
        # Cụm trích dẫn phải ĐÓNG ở cuối chuỗi (dấu `"` cuối không có `\` đứng trước).
        assert http.calls[0].endswith('*"')
        assert not http.calls[0].endswith('\\"')
