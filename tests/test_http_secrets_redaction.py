"""Regression test: khóa API (vd NCBI_API_KEY) không được lọt vào log qua thông báo lỗi.

Audit 2026-07-11: requests tự nhúng URL ĐẦY ĐỦ (kèm query string, gồm api_key) vào thông
báo exception (HTTPError/ConnectionError…) khi request lỗi — nếu HttpClient/caller log
thẳng str(exc), khóa API sẽ lọt nguyên văn vào data/archive/app.log/stdout. Tái hiện live
với NCBI thật đã xác nhận lỗi này có thật trước khi vá (app/utils/http.py::_redact,
_raise_for_status_redacted).
"""
from __future__ import annotations

import logging

import pytest
import requests

from app.utils import http as http_mod
from app.utils.http import HttpClient, _redact


class _FakeResponseWithUrl:
    """Mô phỏng requests.Response.raise_for_status() — thông báo lỗi thật của requests
    LUÔN nhúng resp.url (URL đã resolve, kèm query string) vào message."""

    def __init__(self, status_code, url, headers=None):
        self.status_code = status_code
        self.url = url
        self.headers = headers or {}
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(
                f"{self.status_code} Client Error: Bad Request for url: {self.url}"
            )
            err.response = self
            raise err

    def json(self):
        return {}


class _ScriptedSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def request(self, method, url, params=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: None)


def _leaked_url():
    return (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        "?db=pubmed&term=x&api_key=FAKESECRETKEY1234567890"
    )


def test_redact_strips_api_key_value():
    safe = _redact(_leaked_url())
    assert "FAKESECRETKEY1234567890" not in safe
    assert "api_key=***" in safe


def test_redact_is_case_and_separator_insensitive():
    assert "SECRET1" not in _redact("...&API_KEY=SECRET1&db=pubmed")
    assert "SECRET2" not in _redact("...&api-key=SECRET2&db=pubmed")


def test_permanent_4xx_httperror_does_not_leak_api_key_in_message():
    """Lỗi vĩnh viễn (401 sai key…) raise thẳng ra caller — exception PHẢI đã được che
    trước khi rời HttpClient, vì caller (vd resolve_pmids()) log thẳng exc."""
    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _ScriptedSession([_FakeResponseWithUrl(401, _leaked_url())])
    with pytest.raises(requests.HTTPError) as exc_info:
        client.get_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": "x", "api_key": "FAKESECRETKEY1234567890"},
        )
    assert "FAKESECRETKEY1234567890" not in str(exc_info.value)


def test_retryable_status_exhausted_does_not_leak_api_key_in_message():
    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _ScriptedSession([
        _FakeResponseWithUrl(429, _leaked_url()),
        _FakeResponseWithUrl(429, _leaked_url()),
    ])
    with pytest.raises(requests.HTTPError) as exc_info:
        client.get_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                        params={"api_key": "FAKESECRETKEY1234567890"})
    assert "FAKESECRETKEY1234567890" not in str(exc_info.value)


def test_json_parse_failure_after_2xx_does_not_leak_api_key_in_log(caplog):
    """resp.raise_for_status() PASS (200) nhưng .json() hỏng -> except (RequestException,
    ValueError) nhánh log local — cũng phải che, không chỉ nhánh raise-ra-ngoài."""
    class _BadJsonResponse(_FakeResponseWithUrl):
        def json(self):
            raise ValueError(f"Expecting value: line 1 column 1 (url={self.url})")

    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _ScriptedSession([])
    client.session.request = lambda method, url, params=None, timeout=None: _BadJsonResponse(
        200, _leaked_url()
    )
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError):
            client.get_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                            params={"api_key": "FAKESECRETKEY1234567890"})
    assert "FAKESECRETKEY1234567890" not in caplog.text


def test_network_exception_does_not_leak_api_key_in_log(caplog):
    """ConnectionError/timeout thật của requests cũng nhúng URL đầy đủ — nhánh log local
    (trước khi raise RuntimeError an toàn ở caller) phải che."""
    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _ScriptedSession([])

    def _raising_request(method, url, params=None, timeout=None):
        raise requests.ConnectionError(
            "HTTPSConnectionPool: Max retries exceeded with url: "
            "/entrez/eutils/esearch.fcgi?api_key=FAKESECRETKEY1234567890"
        )

    client.session.request = _raising_request
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError):
            client.get_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                            params={"api_key": "FAKESECRETKEY1234567890"})
    assert "FAKESECRETKEY1234567890" not in caplog.text
