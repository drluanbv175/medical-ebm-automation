"""Kiểm connector DynaMed/DynaMedex (EBSCO) — thêm 13/09/2026.

Tất cả test OFFLINE: mock chế độ mặc định + monkeypatch `client.http.post_json`
cho chế độ live, KHÔNG gọi mạng thật — cùng khuôn tests/test_scopus.py.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.dynamed import SEARCH_URL, TOKEN_URL, DynaMedClient  # noqa: E402


@pytest.fixture(autouse=True)
def _don_credential_dynamed(monkeypatch):
    """Cô lập dynamed_client_id/secret khỏi .env thật của máy đang chạy test —
    mỗi test tự đặt giá trị nó cần, không phụ thuộc môi trường ngoài."""
    monkeypatch.setattr(settings, "dynamed_client_id", "")
    monkeypatch.setattr(settings, "dynamed_client_secret", "")
    monkeypatch.setattr(settings, "dynamed_product", "dynamed")
    yield


def _client_capturing_calls(monkeypatch, search_response: Optional[dict] = None,
                             token_response: Optional[dict] = None,
                             client_id: str = "FAKE_ID", client_secret: str = "FAKE_SECRET"):
    """Client use_mock=False, http.post_json bị mock để ghi lại lời gọi thật sự
    gửi đi (token endpoint VÀ search endpoint) thay vì gọi mạng."""
    monkeypatch.setattr(settings, "dynamed_client_id", client_id)
    monkeypatch.setattr(settings, "dynamed_client_secret", client_secret)
    client = DynaMedClient()
    client.use_mock = False
    captured: dict = {"token_calls": [], "search_calls": []}

    def fake_post_json(url, json_body=None, params=None, headers=None, use_cache=False):
        if url == TOKEN_URL:
            captured["token_calls"].append({"json_body": json_body, "use_cache": use_cache})
            return token_response if token_response is not None else {"access_token": "TOKEN123"}
        if url == SEARCH_URL:
            captured["search_calls"].append({
                "json_body": json_body, "headers": headers, "use_cache": use_cache,
            })
            return search_response if search_response is not None else {"items": []}
        raise AssertionError(f"URL không mong đợi: {url}")

    monkeypatch.setattr(client.http, "post_json", fake_post_json)
    return client, captured


# ════════════════════════════════════════════════════════════════════════════
# Chế độ mock mặc định (không key, không mạng)
# ════════════════════════════════════════════════════════════════════════════

def test_dynamed_mock_mode_returns_records_tagged_correctly():
    client = DynaMedClient()
    assert client.use_mock is True
    recs = client.search("atrial fibrillation", clinical_area="Tim mạch")
    assert all(r.source == "dynamed" for r in recs)
    assert all(r.raw.get("_mock") for r in recs)


# ════════════════════════════════════════════════════════════════════════════
# Fail-closed: BẬT nguồn mà thiếu credential phải báo lỗi RÕ, không âm thầm
# trả rỗng — cùng nguyên tắc ScopusClient.
# ════════════════════════════════════════════════════════════════════════════

def test_dynamed_live_without_credentials_raises_clear_error_not_silent_empty():
    client = DynaMedClient()
    client.use_mock = False
    with pytest.raises(RuntimeError, match="DYNAMED_CLIENT_ID"):
        client.search("atrial fibrillation")


def test_dynamed_live_with_only_client_id_still_raises(monkeypatch):
    monkeypatch.setattr(settings, "dynamed_client_id", "ONLY_ID")
    monkeypatch.setattr(settings, "dynamed_client_secret", "")
    client = DynaMedClient()
    client.use_mock = False
    with pytest.raises(RuntimeError, match="DYNAMED_CLIENT_SECRET"):
        client.search("atrial fibrillation")


# ════════════════════════════════════════════════════════════════════════════
# Luồng OAuth2 client_credentials
# ════════════════════════════════════════════════════════════════════════════

def test_dynamed_token_request_sends_correct_grant_and_product(monkeypatch):
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("heart failure")
    assert len(captured["token_calls"]) == 1
    body = captured["token_calls"][0]["json_body"]
    assert body == {
        "grant_type": "client_credentials",
        "client_id": "FAKE_ID",
        "client_secret": "FAKE_SECRET",
        "product": "dynamed",
    }
    # Token là bí mật — KHÔNG được cache ra đĩa.
    assert captured["token_calls"][0]["use_cache"] is False


def test_dynamed_uses_dynamedex_product_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "dynamed_product", "dynamedex")
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("warfarin interaction")
    assert captured["token_calls"][0]["json_body"]["product"] == "dynamedex"


def test_dynamed_search_sends_bearer_token_from_token_response(monkeypatch):
    client, captured = _client_capturing_calls(
        monkeypatch, token_response={"access_token": "REAL_TOKEN_XYZ"})
    client.search("sepsis")
    assert captured["search_calls"][0]["headers"] == {"Authorization": "Bearer REAL_TOKEN_XYZ"}


def test_dynamed_token_reused_across_searches_within_ttl(monkeypatch):
    """Không gọi lại token endpoint nếu token trong bộ nhớ CHƯA hết hạn — tránh
    tốn một lượt gọi OAuth2 cho mỗi query."""
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("query 1")
    client.search("query 2")
    assert len(captured["token_calls"]) == 1
    assert len(captured["search_calls"]) == 2


def test_dynamed_token_refetched_after_ttl_expires(monkeypatch):
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("query 1")
    # Giả lập token đã hết hạn (đẩy mốc hết hạn về quá khứ).
    client._token_expires_at = time.monotonic() - 1
    client.search("query 2")
    assert len(captured["token_calls"]) == 2


def test_dynamed_token_response_missing_access_token_returns_empty_not_raise(monkeypatch):
    """Phản hồi 200 nhưng thiếu 'access_token' là lỗi XẢY RA TRONG LƯỢT GỌI THẬT
    (khác thiếu client_id/secret — bị chặn TRƯỚC khi gọi mạng), nên đi theo
    đúng quy ước 'lỗi gọi thật -> trả rỗng, KHÔNG bịa mock, KHÔNG làm sập cả
    pipeline vì một nguồn' của mọi connector khác (xem
    test_scopus_network_error_returns_empty_list_not_raise)."""
    client, _ = _client_capturing_calls(monkeypatch, token_response={})
    recs = client.search("bat_ky_gi")
    assert recs == []


def test_dynamed_search_body_only_requests_title_and_pubtype(monkeypatch):
    """CỐ Ý không xin field nội dung đầy đủ (description/sections/toc) — nội
    dung DynaMed có bản quyền, xem docstring app/sources/dynamed.py."""
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("copd", max_results=10)
    body = captured["search_calls"][0]["json_body"]
    assert body["fields"] == ["title", "pubType"]
    assert body["pageSize"] == 10
    assert "description" not in body["fields"]
    assert "sections" not in body["fields"]


def test_dynamed_page_size_capped_at_30(monkeypatch):
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("diabetes", max_results=100)
    assert captured["search_calls"][0]["json_body"]["pageSize"] == 30


def test_dynamed_search_result_is_cached_but_token_call_is_not(monkeypatch):
    client, captured = _client_capturing_calls(monkeypatch)
    client.search("query")
    assert captured["search_calls"][0]["use_cache"] is True
    assert captured["token_calls"][0]["use_cache"] is False


# ════════════════════════════════════════════════════════════════════════════
# Phân giải item thật thành RawRecord
# ════════════════════════════════════════════════════════════════════════════

_ITEM_DAY_DU = {
    "id": "T916967",
    "title": "Complications of Myocardial Infarction",
    "pubType": {"title": "Condition"},
    "slug": "/condition/myocardial-infarction-complications",
    "exactMatch": True,
    "links": [{"rel": "self", "href": "https://apis.ebsco.com/medsapi-dynamed/v2/content/articles/T916967"}],
}


def test_dynamed_parses_full_item_fields(monkeypatch):
    client, _ = _client_capturing_calls(monkeypatch, search_response={"items": [_ITEM_DAY_DU]})
    recs = client.search("myocardial infarction complications")
    assert len(recs) == 1
    r = recs[0]
    assert r.title == "Complications of Myocardial Infarction"
    assert r.journal_or_organization == "DynaMed"
    assert r.document_type == "Condition"
    assert r.url == "https://www.dynamed.com/condition/myocardial-infarction-complications"
    assert r.raw["id"] == "T916967"
    assert r.raw["exactMatch"] is True
    # DynaMed không có PMID/DOI/tác giả/ngày xuất bản cố định — phải là None,
    # không được bịa.
    assert r.pmid is None
    assert r.doi is None
    assert r.authors is None
    assert r.publication_date is None
    # Cố ý KHÔNG xin field nội dung đầy đủ -> abstract luôn None.
    assert r.abstract is None


def test_dynamed_organization_label_follows_product(monkeypatch):
    monkeypatch.setattr(settings, "dynamed_product", "dynamedex")
    client, _ = _client_capturing_calls(monkeypatch, search_response={"items": [_ITEM_DAY_DU]})
    recs = client.search("warfarin")
    assert recs[0].journal_or_organization == "DynaMedex"


def test_dynamed_falls_back_to_self_link_when_slug_missing(monkeypatch):
    item = {**_ITEM_DAY_DU, "slug": None}
    client, _ = _client_capturing_calls(monkeypatch, search_response={"items": [item]})
    recs = client.search("myocardial infarction complications")
    assert recs[0].url == "https://apis.ebsco.com/medsapi-dynamed/v2/content/articles/T916967"


def test_dynamed_missing_optional_fields_do_not_crash(monkeypatch):
    item_toi_thieu = {"id": "T1", "title": "Một mục không có slug/link/pubType"}
    client, _ = _client_capturing_calls(monkeypatch, search_response={"items": [item_toi_thieu]})
    recs = client.search("query hiếm")
    assert len(recs) == 1
    assert recs[0].url is None
    assert recs[0].document_type is None


def test_dynamed_one_bad_item_does_not_wipe_out_the_rest(monkeypatch):
    item_hong = {"id": "T-bad", "title": "Mục hỏng", "links": 12345}
    client, _ = _client_capturing_calls(
        monkeypatch, search_response={"items": [item_hong, _ITEM_DAY_DU]})
    recs = client.search("myocardial infarction complications")
    assert len(recs) == 1
    assert recs[0].raw["id"] == "T916967"


# ════════════════════════════════════════════════════════════════════════════
# Lỗi mạng thật (KHÁC lỗi thiếu credential) -> trả rỗng, KHÔNG bịa mock
# ════════════════════════════════════════════════════════════════════════════

def test_dynamed_network_error_during_token_returns_empty_list_not_raise(monkeypatch):
    monkeypatch.setattr(settings, "dynamed_client_id", "FAKE_ID")
    monkeypatch.setattr(settings, "dynamed_client_secret", "FAKE_SECRET")
    client = DynaMedClient()
    client.use_mock = False

    def fake_post_json_loi(*a, **kw):
        raise ConnectionError("giả lập mất mạng")

    monkeypatch.setattr(client.http, "post_json", fake_post_json_loi)
    recs = client.search("bat_ky_gi")
    assert recs == []


def test_dynamed_network_error_during_search_returns_empty_list_not_raise(monkeypatch):
    monkeypatch.setattr(settings, "dynamed_client_id", "FAKE_ID")
    monkeypatch.setattr(settings, "dynamed_client_secret", "FAKE_SECRET")
    client = DynaMedClient()
    client.use_mock = False

    def fake_post_json(url, json_body=None, params=None, headers=None, use_cache=False):
        if url == TOKEN_URL:
            return {"access_token": "TOKEN123"}
        raise ConnectionError("giả lập mất mạng khi tìm kiếm")

    monkeypatch.setattr(client.http, "post_json", fake_post_json)
    recs = client.search("bat_ky_gi")
    assert recs == []
