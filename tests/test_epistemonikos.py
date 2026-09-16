"""Kiểm connector Epistemonikos API — thêm 16/09/2026.

Fixture `_RESPONSE_THAT_TU_TAI_LIEU` chép NGUYÊN VĂN ví dụ response thật trong
tài liệu chính thức (https://api.epistemonikos.org/, đọc trực tiếp 16/09/2026,
query "adjuvant treatment", total_hits=205) — KHÔNG bịa cấu trúc.

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
from app.sources.epistemonikos import EpistemonikosClient  # noqa: E402


@pytest.fixture(autouse=True)
def _don_token_epistemonikos(monkeypatch):
    monkeypatch.setattr(settings, "epistemonikos_api_token", "")
    yield


def _client_capturing_call(monkeypatch, response: Optional[dict] = None,
                            token: str = "FAKE_TOKEN_FOR_TEST"):
    monkeypatch.setattr(settings, "epistemonikos_api_token", token)
    client = EpistemonikosClient()
    client.use_mock = False
    captured: dict = {}

    def fake_get_json(url, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return response if response is not None else {
            "search_info": {"total_hits": 0}, "results": []}

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    return client, captured


# Ví dụ response THẬT trích nguyên văn từ tài liệu chính thức (rút gọn còn 2 mục
# thay vì 10, giữ nguyên hình dạng dữ liệu — KHÔNG đổi trường nào).
_RESPONSE_THAT_TU_TAI_LIEU = {
    "search_info": {
        "total_hits": 205,
        "pages": {
            "self": "/v1/documents/search?q=\"adjuvant treatment\"&page_size=10&p=1",
            "last": "/v1/documents/search?q=\"adjuvant treatment\"&page_size=10&p=20",
            "next": "/v1/documents/search?q=\"adjuvant treatment\"&page_size=10&p=2",
            "first": "/v1/documents/search?q=\"adjuvant treatment\"&page_size=10&p=1",
        },
    },
    "results": [
        {
            "id": "2ed67c61bfce637948dd7a25e637080f1476ba70",
            "title": "[Carbamazepine: an efficient adjuvant treatment in schizophrenia].",
            "authors": ["Martín Muñoz JC", "Moriñigo Domínguez AV"],
            "document_uri": "/v1/documents/2ed67c61bfce637948dd7a25e637080f1476ba70",
            "journal": "Actas luso-españolas de neurología, psiquiatría y ciencias afines",
            "year": "1992",
            "abstract": "Different studies published in the last years...",
        },
        {
            "id": "3f9f005e4a6b35f11493eb8578caa17f825c827d",
            "title": "Adjuvant treatment for phenylketonuria (PKU)",
            "authors": ["Lindegren ML", "Krishnaswami S"],
            "document_uri": "/v1/documents/3f9f005e4a6b35f11493eb8578caa17f825c827d",
            "journal": "HTA Database",
            "year": "2013",
            "abstract": "RECORD STATUS: This is a bibliographic record...",
        },
    ],
}

# Bản có show=classification,external_links (dựng theo đúng schema tài liệu mô
# tả cho /documents/{id}, áp dụng cho từng item của search khi có show=).
_ENTRY_CO_SHOW = {
    "id": "aced6ce12e1f54fb98c16d3435195ceb284240d2",
    "title": "The Regai Dzive Shiri project: results of a randomized trial.",
    "authors": ["Cowan FM", "Pascoe SJ"],
    "document_uri": "/v1/documents/aced6ce12e1f54fb98c16d3435195ceb284240d2",
    "journal": "AIDS (London, England)",
    "year": "2010",
    "abstract": "BACKGROUND: HIV prevention among young people...",
    "classification": "systematic-review",
    "external_links": {
        "publisher": "https://dx.doi.org/10.1097/QAD.0b013e32833e77c9",
        "pubmed": "https://www.ncbi.nlm.nih.gov/pubmed/20881473",
        "epistemonikos": "https://www.epistemonikos.org/en/documents/aced6ce12e1f54fb98c16d3435195ceb284240d2",
    },
}


# ════════════════════════════════════════════════════════════════════════════
# Chế độ mock mặc định (không token, không mạng)
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_mock_mode_returns_records_tagged_correctly():
    client = EpistemonikosClient()
    assert client.use_mock is True
    recs = client.search("systematic review heart failure", clinical_area="Tim mạch")
    assert all(r.source == "epistemonikos" for r in recs)
    assert all(r.raw.get("_mock") for r in recs)


# ════════════════════════════════════════════════════════════════════════════
# Fail-closed: BẬT nguồn mà thiếu token phải báo lỗi RÕ (giống Scopus, khác CORE)
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_live_without_token_raises_clear_error():
    client = EpistemonikosClient()
    client.use_mock = False
    with pytest.raises(RuntimeError, match="EPISTEMONIKOS_API_TOKEN"):
        client.search("heart failure")


def test_epistemonikos_header_uses_token_auth_format(monkeypatch):
    monkeypatch.setattr(settings, "epistemonikos_api_token", "abc123")
    client = EpistemonikosClient()
    assert client.http.session.headers.get("Authorization") == 'Token token="abc123"'


def test_epistemonikos_no_authorization_header_when_token_absent():
    client = EpistemonikosClient()
    assert "Authorization" not in client.http.session.headers


# ════════════════════════════════════════════════════════════════════════════
# Xây câu truy vấn
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_sends_q_and_show_params(monkeypatch):
    client, captured = _client_capturing_call(monkeypatch)
    client.search("chronic kidney disease")
    assert captured["params"]["q"] == "chronic kidney disease"
    assert captured["params"]["show"] == "classification,external_links"


# ════════════════════════════════════════════════════════════════════════════
# Phân giải response THẬT (nguyên văn tài liệu) thành RawRecord
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_parses_real_documented_response(monkeypatch):
    client, _ = _client_capturing_call(monkeypatch, response=_RESPONSE_THAT_TU_TAI_LIEU)
    recs = client.search("adjuvant treatment")
    assert len(recs) == 2
    r0 = recs[0]
    assert r0.title == "[Carbamazepine: an efficient adjuvant treatment in schizophrenia]."
    assert r0.authors == "Martín Muñoz JC, Moriñigo Domínguez AV"
    assert r0.journal_or_organization == "Actas luso-españolas de neurología, psiquiatría y ciencias afines"
    assert r0.publication_date == "1992"
    assert r0.url == "https://www.epistemonikos.org/en/documents/2ed67c61bfce637948dd7a25e637080f1476ba70"
    assert r0.raw["epistemonikos_id"] == "2ed67c61bfce637948dd7a25e637080f1476ba70"
    assert r0.raw["total_hits"] == 205
    # Response gốc KHÔNG có show=classification,external_links trong ví dụ này
    # (đúng tài liệu: chỉ xuất hiện khi request có show=) -> doi/pmid phải None,
    # KHÔNG được bịa.
    assert r0.doi is None
    assert r0.pmid is None


def test_epistemonikos_extracts_doi_and_pmid_when_external_links_present(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch,
        response={"search_info": {"total_hits": 1}, "results": [_ENTRY_CO_SHOW]})
    recs = client.search("hiv prevention rct")
    assert len(recs) == 1
    r = recs[0]
    assert r.doi == "10.1097/QAD.0b013e32833e77c9"
    assert r.pmid == "20881473"
    assert r.url == _ENTRY_CO_SHOW["external_links"]["epistemonikos"]
    assert r.document_type == "systematic-review"
    assert r.study_type == "systematic_review"


def test_epistemonikos_publisher_link_not_doi_org_gives_none_not_bogus(monkeypatch):
    entry = {**_ENTRY_CO_SHOW,
             "external_links": {**_ENTRY_CO_SHOW["external_links"],
                                 "publisher": "https://journals.example.org/article/123"}}
    client, _ = _client_capturing_call(
        monkeypatch, response={"search_info": {"total_hits": 1}, "results": [entry]})
    recs = client.search("query gì đó")
    assert recs[0].doi is None


# ════════════════════════════════════════════════════════════════════════════
# Lọc since_date PHÍA CLIENT (server không hỗ trợ lọc theo năm)
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_since_date_filters_client_side(monkeypatch):
    client, _ = _client_capturing_call(monkeypatch, response=_RESPONSE_THAT_TU_TAI_LIEU)
    recs = client.search("adjuvant treatment", since_date="2000-01-01")
    # Chỉ giữ bản 2013, loại bản 1992
    assert len(recs) == 1
    assert recs[0].publication_date == "2013"


def test_epistemonikos_malformed_since_date_does_not_crash(monkeypatch):
    client, _ = _client_capturing_call(monkeypatch, response=_RESPONSE_THAT_TU_TAI_LIEU)
    recs = client.search("adjuvant treatment", since_date="khong-phai-ngay")
    # Không lọc được thì giữ nguyên tất cả, không crash.
    assert len(recs) == 2


# ════════════════════════════════════════════════════════════════════════════
# max_results giới hạn số bản ghi trả về
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_respects_max_results(monkeypatch):
    client, _ = _client_capturing_call(monkeypatch, response=_RESPONSE_THAT_TU_TAI_LIEU)
    recs = client.search("adjuvant treatment", max_results=1)
    assert len(recs) == 1


# ════════════════════════════════════════════════════════════════════════════
# Bản ghi hỏng không kéo sập cả trang
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_missing_optional_fields_do_not_crash(monkeypatch):
    entry_toi_thieu = {"id": "x", "title": "Một bài không có authors/journal"}
    client, _ = _client_capturing_call(
        monkeypatch, response={"search_info": {"total_hits": 1}, "results": [entry_toi_thieu]})
    recs = client.search("query hiếm")
    assert len(recs) == 1
    assert recs[0].authors is None
    assert recs[0].doi is None


def test_epistemonikos_one_bad_entry_does_not_wipe_out_the_rest(monkeypatch):
    """`authors` sai kiểu (vd int) KHÔNG làm vỡ — _danh_sach_tac_gia()-tương-đương
    ở đây đã kiểm isinstance TRƯỚC khi join, khác CORE (không kiểm trước, ném
    lỗi rồi bị try/except cấp entry bắt). Muốn ép crash thật ở CHÍNH connector
    này phải đi qua `_doi_tu_url()`/`_pmid_tu_url()` — hai hàm regex.search()
    trên giá trị KHÔNG PHẢI chuỗi (vd int) mới ném TypeError."""
    entry_hong = {"id": "y", "title": "Bài có external_links hỏng dạng",
                  "external_links": {"publisher": 12345}}
    client, _ = _client_capturing_call(
        monkeypatch, response={"search_info": {"total_hits": 2},
                                "results": [entry_hong, _RESPONSE_THAT_TU_TAI_LIEU["results"][0]]})
    recs = client.search("sglt2 ckd")
    assert len(recs) == 1
    assert recs[0].title == _RESPONSE_THAT_TU_TAI_LIEU["results"][0]["title"]


def test_epistemonikos_authors_wrong_type_does_not_crash_but_returns_none(monkeypatch):
    """Khác CORE: kiểu sai của `authors` (vd int) được XỬ LÝ AN TOÀN (isinstance
    kiểm trước khi join) — bản ghi KHÔNG bị loại, chỉ có authors=None."""
    entry = {"id": "z", "title": "Authors kiểu sai nhưng không crash", "authors": 12345}
    client, _ = _client_capturing_call(
        monkeypatch, response={"search_info": {"total_hits": 1}, "results": [entry]})
    recs = client.search("query")
    assert len(recs) == 1
    assert recs[0].authors is None


def test_epistemonikos_skips_non_dict_entries_without_crashing(monkeypatch):
    client, _ = _client_capturing_call(
        monkeypatch, response={"search_info": {"total_hits": 2},
                                "results": [None, _RESPONSE_THAT_TU_TAI_LIEU["results"][0]]})
    recs = client.search("query gì đó hiếm")
    assert len(recs) == 1


# ════════════════════════════════════════════════════════════════════════════
# Lỗi mạng thật -> trả rỗng, KHÔNG bịa mock, KHÔNG crash
# ════════════════════════════════════════════════════════════════════════════

def test_epistemonikos_network_error_returns_empty_list_not_raise(monkeypatch):
    monkeypatch.setattr(settings, "epistemonikos_api_token", "FAKE_TOKEN")
    client = EpistemonikosClient()
    client.use_mock = False

    def fake_get_json_loi(*a, **kw):
        raise ConnectionError("giả lập mất mạng")

    monkeypatch.setattr(client.http, "get_json", fake_get_json_loi)
    recs = client.search("bat_ky_gi")
    assert recs == []
