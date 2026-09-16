"""Kiểm connector CORE API (core.ac.uk) — thêm 16/09/2026.

Tất cả test OFFLINE: mock chế độ mặc định + monkeypatch `client.http.get_json`
cho chế độ live, KHÔNG gọi mạng thật (đúng khuôn tests/test_scopus.py).
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
from app.sources.core_api import CoreClient  # noqa: E402


@pytest.fixture(autouse=True)
def _don_key_core(monkeypatch):
    """Cô lập core_api_key khỏi .env thật của máy đang chạy test."""
    monkeypatch.setattr(settings, "core_api_key", "")
    yield


def _client_capturing_call(monkeypatch, response: Optional[dict] = None,
                            api_key: str = "FAKE_KEY_FOR_TEST"):
    monkeypatch.setattr(settings, "core_api_key", api_key)
    client = CoreClient()
    client.use_mock = False
    captured: dict = {}

    def fake_get_json(url, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return response if response is not None else {"totalHits": 0, "results": []}

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    return client, captured


# ════════════════════════════════════════════════════════════════════════════
# Chế độ mock mặc định (không key, không mạng)
# ════════════════════════════════════════════════════════════════════════════

def test_core_mock_mode_returns_records_tagged_correctly():
    client = CoreClient()
    assert client.use_mock is True
    recs = client.search("atrial fibrillation", clinical_area="Tim mạch")
    assert all(r.source == "core" for r in recs)
    assert all(r.raw.get("_mock") for r in recs)


# ════════════════════════════════════════════════════════════════════════════
# KHÁC Scopus: thiếu key KHÔNG chặn cứng — CORE tự khai vẫn gọi được nhịp thấp
# ════════════════════════════════════════════════════════════════════════════

def test_core_live_without_key_does_not_raise_and_still_calls(monkeypatch):
    client = CoreClient()
    client.use_mock = False
    captured = {}

    def fake_get_json(url, params=None, **kwargs):
        captured["params"] = params
        return {"totalHits": 0, "results": []}

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    recs = client.search("heart failure")
    assert recs == []
    assert captured["params"]["q"] == "heart failure"


def test_core_header_uses_bearer_token_when_key_present(monkeypatch):
    monkeypatch.setattr(settings, "core_api_key", "REAL_KEY_123")
    client = CoreClient()
    assert client.http.session.headers.get("Authorization") == "Bearer REAL_KEY_123"


def test_core_no_authorization_header_when_key_absent():
    client = CoreClient()
    assert "Authorization" not in client.http.session.headers


# ════════════════════════════════════════════════════════════════════════════
# Xây câu truy vấn
# ════════════════════════════════════════════════════════════════════════════

def test_core_query_passed_through_when_no_since_date(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    client.search("chronic kidney disease")
    assert captured["params"]["q"] == "chronic kidney disease"


def test_core_since_date_adds_year_published_filter(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    client.search("heart failure", since_date="2023-06-01")
    assert captured["params"]["q"] == '(heart failure) AND yearPublished>="2023"'


def test_core_malformed_since_date_does_not_crash(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    recs = client.search("copd", since_date="not-a-date")
    assert "yearPublished" not in captured["params"]["q"]
    assert recs == []


def test_core_limit_param_capped_at_100(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    client.search("diabetes", max_results=500)
    assert captured["params"]["limit"] == 100


# ════════════════════════════════════════════════════════════════════════════
# Phân giải entry thật thành RawRecord — CẢ HAI dạng khoá (camelCase/snake_case),
# vì tài liệu chính thức tự mâu thuẫn giữa hai phần (xem docstring core_api.py)
# ════════════════════════════════════════════════════════════════════════════

_ENTRY_CAMEL = {
    "id": 267312,
    "title": "SGLT2 inhibitors in chronic kidney disease: a systematic review",
    "authors": [{"name": "Nguyen T."}, {"name": "Tran V."}],
    "journals": [{"title": "Kidney International"}],
    "publishedDate": "2024-03-15",
    "doi": "10.1016/j.kint.2024.01.001",
    "pubmedId": "38000000",
    "abstract": "Toàn văn tóm tắt...",
    "documentType": "review",
    "downloadUrl": "https://core.ac.uk/download/267312.pdf",
    "language": {"code": "en"},
}

_ENTRY_SNAKE = {
    "id": 999999,
    "title": "A study in snake_case shape",
    "authors": ["Author A", "Author B"],
    "journals": [{"name": "Some Journal"}],
    "published_date": "2022-01-01",
    "doi": "10.1000/xyz",
    "pubmed_id": "12345678",
    "abstract": "Snake case abstract",
    "document_type": "article",
    "source_fulltext_urls": ["https://example.org/full.pdf"],
}


def test_core_parses_camelcase_entry_fields(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch, response={"totalHits": 1, "results": [_ENTRY_CAMEL]})
    recs = client.search("sglt2 ckd")
    assert len(recs) == 1
    r = recs[0]
    assert r.title == _ENTRY_CAMEL["title"]
    assert r.authors == "Nguyen T., Tran V."
    assert r.journal_or_organization == "Kidney International"
    assert r.publication_date == "2024-03-15"
    assert r.doi == "10.1016/j.kint.2024.01.001"
    assert r.pmid == "38000000"
    assert r.document_type == "review"
    assert r.url == "https://core.ac.uk/download/267312.pdf"
    assert r.raw["core_id"] == 267312


def test_core_parses_snake_case_entry_fields_as_fallback(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch, response={"totalHits": 1, "results": [_ENTRY_SNAKE]})
    recs = client.search("query khác")
    assert len(recs) == 1
    r = recs[0]
    assert r.title == _ENTRY_SNAKE["title"]
    assert r.authors == "Author A, Author B"
    assert r.journal_or_organization == "Some Journal"
    assert r.publication_date == "2022-01-01"
    assert r.doi == "10.1000/xyz"
    assert r.pmid == "12345678"
    assert r.document_type == "article"
    assert r.url == "https://example.org/full.pdf"


def test_core_falls_back_to_core_url_when_no_download_link(monkeypatch):
    entry = {**_ENTRY_CAMEL}
    entry.pop("downloadUrl")
    client, _ = _client_capturing_call(
        monkeypatch, response={"totalHits": 1, "results": [entry]})
    recs = client.search("sglt2 ckd")
    assert recs[0].url == "https://core.ac.uk/works/267312"


def test_core_missing_optional_fields_do_not_crash(monkeypatch):
    entry_toi_thieu = {"id": 1, "title": "Một bài không có DOI/PMID/authors"}
    client, _ = _client_capturing_call(
        monkeypatch, response={"totalHits": 1, "results": [entry_toi_thieu]})
    recs = client.search("query hiếm")
    assert len(recs) == 1
    assert recs[0].doi is None
    assert recs[0].pmid is None
    assert recs[0].authors is None


def test_core_skips_non_dict_entries_without_crashing(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch, response={"totalHits": 2, "results": [None, _ENTRY_CAMEL]})
    recs = client.search("query gì đó hiếm")
    assert len(recs) == 1
    assert recs[0].doi == _ENTRY_CAMEL["doi"]


def test_core_one_bad_entry_does_not_wipe_out_the_rest(monkeypatch):
    """Cùng khuôn test_scopus_one_bad_entry_does_not_wipe_out_the_rest: entry hỏng
    (authors kiểu sai, không phải list/None) bị BỎ QUA TOÀN BỘ bởi try/except cấp
    entry trong search() — không giữ lại một phần — nhưng KHÔNG kéo sập các entry
    tốt khác trong cùng trang kết quả."""
    entry_hong = {"id": 2, "title": "Bài có authors hỏng dạng", "authors": 12345}
    client, _ = _client_capturing_call(
        monkeypatch, response={"totalHits": 2, "results": [entry_hong, _ENTRY_CAMEL]})
    recs = client.search("sglt2 ckd")
    assert len(recs) == 1
    assert recs[0].doi == _ENTRY_CAMEL["doi"]


# ════════════════════════════════════════════════════════════════════════════
# Lỗi mạng thật -> trả rỗng, KHÔNG bịa mock, KHÔNG crash
# ════════════════════════════════════════════════════════════════════════════

def test_core_network_error_returns_empty_list_not_raise(monkeypatch):
    monkeypatch.setattr(settings, "core_api_key", "FAKE_KEY")
    client = CoreClient()
    client.use_mock = False

    def fake_get_json_loi(*a, **kw):
        raise ConnectionError("giả lập mất mạng")

    monkeypatch.setattr(client.http, "get_json", fake_get_json_loi)
    recs = client.search("bat_ky_gi")
    assert recs == []
