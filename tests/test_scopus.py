"""Kiểm connector Scopus (Elsevier) — thêm 13/09/2026.

Tất cả test OFFLINE: mock chế độ mặc định + monkeypatch `client.http.get_json`
cho chế độ live, KHÔNG gọi mạng thật (đúng quy ước tests/test_sources_mock.py +
tests/test_europepmc_malformed_pmid_query_injection_20260904.py).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.scopus import ScopusClient  # noqa: E402


@pytest.fixture(autouse=True)
def _don_key_scopus(monkeypatch):
    """Cô lập scopus_api_key/scopus_insttoken/scopus_bind_interface khỏi .env
    thật của máy đang chạy test — mỗi test tự đặt giá trị nó cần, không phụ
    thuộc môi trường ngoài."""
    monkeypatch.setattr(settings, "scopus_api_key", "")
    monkeypatch.setattr(settings, "scopus_insttoken", "")
    monkeypatch.setattr(settings, "scopus_bind_interface", "")
    # Vá 25/09/2026: KHOA_QUA_PROXY của môi trường (phiên Cloud) miễn chặn «thiếu khoá» ⇒ test đỏ giả.
    monkeypatch.setattr(settings, "khoa_qua_proxy", "")
    yield


def _client_capturing_call(monkeypatch, response: Optional[dict] = None,
                            api_key: str = "FAKE_KEY_FOR_TEST"):
    """Client use_mock=False, http.get_json bị mock để ghi lại params thật sự
    gửi đi thay vì gọi mạng — cùng khuôn _client_capturing_query của
    test_europepmc_malformed_pmid_query_injection_20260904.py."""
    monkeypatch.setattr(settings, "scopus_api_key", api_key)
    client = ScopusClient()
    client.use_mock = False
    captured: dict = {}

    def fake_get_json(url, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return response if response is not None else {"search-results": {"entry": []}}

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    return client, captured


# ════════════════════════════════════════════════════════════════════════════
# Chế độ mock mặc định (không key, không mạng)
# ════════════════════════════════════════════════════════════════════════════

def test_scopus_mock_mode_returns_records_tagged_correctly():
    client = ScopusClient()
    assert client.use_mock is True
    recs = client.search("atrial fibrillation", clinical_area="Tim mạch")
    assert all(r.source == "scopus" for r in recs)
    assert all(r.raw.get("_mock") for r in recs)


# ════════════════════════════════════════════════════════════════════════════
# Fail-closed: BẬT nguồn mà thiếu key phải báo lỗi RÕ, không âm thầm trả rỗng
# ════════════════════════════════════════════════════════════════════════════

def test_scopus_live_without_key_raises_clear_error_not_silent_empty():
    client = ScopusClient()
    client.use_mock = False
    with pytest.raises(RuntimeError, match="SCOPUS_API_KEY"):
        client.search("atrial fibrillation")


def test_scopus_header_uses_api_key_when_present(monkeypatch):
    monkeypatch.setattr(settings, "scopus_api_key", "REAL_KEY_123")
    client = ScopusClient()
    assert client.http.session.headers.get("X-ELS-APIKey") == "REAL_KEY_123"


def test_scopus_no_apikey_header_when_key_absent():
    client = ScopusClient()
    assert "X-ELS-APIKey" not in client.http.session.headers


# ════════════════════════════════════════════════════════════════════════════
# Xây câu truy vấn đúng cú pháp Scopus
# ════════════════════════════════════════════════════════════════════════════

def test_scopus_query_wrapped_in_title_abs_key(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    client.search("chronic kidney disease")
    assert captured["params"]["query"] == "TITLE-ABS-KEY(chronic kidney disease)"


def test_scopus_since_date_adds_pubyear_aft_minus_one(monkeypatch):
    """AFT loại trừ chính năm đó -> phải trừ 1 để KHÔNG bỏ sót since_date."""
    client, captured = _client_capturing_call(monkeypatch)
    client.search("heart failure", since_date="2023-06-01")
    assert captured["params"]["query"] == "TITLE-ABS-KEY(heart failure) AND PUBYEAR AFT 2022"


def test_scopus_malformed_since_date_does_not_crash(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    recs = client.search("copd", since_date="not-a-date")
    # Không thêm mệnh đề PUBYEAR khi ngày hỏng, nhưng vẫn trả kết quả bình thường.
    assert "PUBYEAR" not in captured["params"]["query"]
    assert recs == []


def test_scopus_count_param_capped_at_25(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    client.search("diabetes", max_results=100)
    assert captured["params"]["count"] == 25


# ════════════════════════════════════════════════════════════════════════════
# Phân giải entry thật thành RawRecord
# ════════════════════════════════════════════════════════════════════════════

_ENTRY_DAY_DU = {
    "dc:title": "SGLT2 inhibitors in chronic kidney disease: a systematic review",
    "dc:creator": "Nguyen T.",
    "prism:publicationName": "Kidney International",
    "prism:coverDate": "2024-03-15",
    "prism:doi": "10.1016/j.kint.2024.01.001",
    "pubmed-id": "38000000",
    "eid": "2-s2.0-85180000000",
    "subtypeDescription": "Review",
    "citedby-count": "12",
    "link": [
        {"@ref": "self", "@href": "https://api.elsevier.com/xyz"},
        {"@ref": "scopus", "@href": "https://www.scopus.com/inward/record.uri?eid=2-s2.0-85180000000"},
    ],
}


def test_scopus_parses_full_entry_fields(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch, response={"search-results": {"entry": [_ENTRY_DAY_DU]}})
    recs = client.search("sglt2 ckd")
    assert len(recs) == 1
    r = recs[0]
    assert r.title == _ENTRY_DAY_DU["dc:title"]
    assert r.authors == "Nguyen T."
    assert r.journal_or_organization == "Kidney International"
    assert r.publication_date == "2024-03-15"
    assert r.doi == "10.1016/j.kint.2024.01.001"
    assert r.pmid == "38000000"
    assert r.document_type == "Review"
    assert r.study_type == "systematic_review"
    assert r.url == "https://www.scopus.com/inward/record.uri?eid=2-s2.0-85180000000"
    assert r.raw["eid"] == "2-s2.0-85180000000"
    assert r.raw["citedby_count"] == "12"
    # Search API mặc định KHÔNG có abstract — phải là None, không được bịa.
    assert r.abstract is None


def test_scopus_falls_back_to_eid_url_when_scopus_link_missing(monkeypatch):
    entry = {**_ENTRY_DAY_DU, "link": [{"@ref": "self", "@href": "https://api.elsevier.com/xyz"}]}
    client, _ = _client_capturing_call(
        monkeypatch, response={"search-results": {"entry": [entry]}})
    recs = client.search("sglt2 ckd")
    assert recs[0].url == (
        "https://www.scopus.com/record/display.uri?eid=2-s2.0-85180000000&origin=resultslist"
    )


def test_scopus_skips_error_entries_without_crashing(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch,
        response={"search-results": {"entry": [
            {"error": "Result set was empty"},
            _ENTRY_DAY_DU,
        ]}},
    )
    recs = client.search("query gì đó hiếm")
    assert len(recs) == 1
    assert recs[0].doi == _ENTRY_DAY_DU["prism:doi"]


def test_scopus_one_bad_entry_does_not_wipe_out_the_rest(monkeypatch):
    """Cùng họ lỗi đã vá ở openalex.py/semantic_scholar.py (task #89 vòng 6):
    một bản ghi hỏng trong trang không được xoá sạch các bản ghi khác.

    `link` là số nguyên (không phải list/None) khiến `for lk in links or []`
    trong `_lay_url_scopus()` ném TypeError thật khi xử lý entry này."""
    entry_hong = {"dc:title": "Bài có link hỏng", "link": 12345}
    client, _ = _client_capturing_call(
        monkeypatch,
        response={"search-results": {"entry": [entry_hong, _ENTRY_DAY_DU]}},
    )
    recs = client.search("sglt2 ckd")
    assert len(recs) == 1
    assert recs[0].doi == _ENTRY_DAY_DU["prism:doi"]


def test_scopus_missing_optional_fields_do_not_crash(monkeypatch):
    entry_toi_thieu = {"dc:title": "Một bài không có DOI/PMID/link"}
    client, _ = _client_capturing_call(
        monkeypatch, response={"search-results": {"entry": [entry_toi_thieu]}})
    recs = client.search("query hiếm")
    assert len(recs) == 1
    assert recs[0].doi is None
    assert recs[0].pmid is None
    assert recs[0].url is None


# ════════════════════════════════════════════════════════════════════════════
# Lỗi mạng thật (KHÁC lỗi thiếu key) -> trả rỗng, KHÔNG bịa mock, KHÔNG crash
# ════════════════════════════════════════════════════════════════════════════

def test_scopus_network_error_returns_empty_list_not_raise(monkeypatch):
    monkeypatch.setattr(settings, "scopus_api_key", "FAKE_KEY")
    client = ScopusClient()
    client.use_mock = False

    def fake_get_json_loi(*a, **kw):
        raise ConnectionError("giả lập mất mạng")

    monkeypatch.setattr(client.http, "get_json", fake_get_json_loi)
    recs = client.search("bat_ky_gi")
    assert recs == []


# ════════════════════════════════════════════════════════════════════════════
# Lách VPN toàn tuyến bằng bind_interface (thêm 17/09/2026, xem
# tests/test_http_bind_interface_vpn_bypass_20260917.py cho hành vi chi tiết
# của bản thân adapter — ở đây chỉ kiểm ScopusClient TRUYỀN đúng cấu hình)
# ════════════════════════════════════════════════════════════════════════════

def test_scopus_client_passes_bind_interface_setting_to_http_client(monkeypatch):
    monkeypatch.setattr(settings, "scopus_bind_interface", "en1")
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("socket.if_nametoindex", lambda name: 9)
    client = ScopusClient()
    assert client.http.bind_interface == "en1"


def test_scopus_client_default_bind_interface_is_none_unchanged_behavior():
    """SCOPUS_BIND_INTERFACE không đặt (mặc định rỗng) -> không đổi hành vi cũ,
    không đòi macOS, không đòi tên card mạng hợp lệ."""
    client = ScopusClient()
    assert client.http.bind_interface is None
