"""Test `HttpClient.get_bytes()` — thêm 23/09/2026 để tải PDF cho các connector toàn
văn guideline (GOLD/GINA). Offline, session giả lập, cùng khuôn test_http_retry.py.
"""
from __future__ import annotations

import pytest
import requests

from app.utils import http as http_mod
from app.utils.http import HttpClient


class _FakeResponse:
    def __init__(self, status_code, content=b"", headers=None, url=""):
        self.status_code = status_code
        self.content = content
        self.text = content.decode("latin-1") if isinstance(content, bytes) else content
        self.headers = headers or {}
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} error for test")
            err.response = self
            raise err

    def json(self):  # pragma: no cover — get_bytes() không gọi .json()
        raise AssertionError("get_bytes() không được gọi resp.json()")


class _ScriptedSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def request(self, method, url, params=None, timeout=None):
        self.calls += 1
        if not self.responses:
            raise AssertionError("Hết kịch bản response nhưng vẫn bị gọi thêm")
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: None)


def _client_with(responses):
    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _ScriptedSession(responses)
    return client


def test_get_bytes_returns_raw_binary_content():
    du_lieu_gia = b"%PDF-1.4 noi dung gia lap khong phai PDF that"
    client = _client_with([_FakeResponse(200, content=du_lieu_gia)])
    out = client.get_bytes("https://example.org/bao-cao.pdf")
    assert out == du_lieu_gia
    assert isinstance(out, bytes)


def test_get_bytes_never_writes_to_disk_cache(tmp_path, monkeypatch):
    """get_bytes() luôn use_cache=False — _write_cache() không được gọi, dù client
    được cấu hình cache_ttl khác 0."""
    ghi_cache_duoc_goi = []
    monkeypatch.setattr(http_mod, "_write_cache", lambda *a, **kw: ghi_cache_duoc_goi.append(True))
    client = HttpClient(cache_ttl=3600, min_interval=0)
    client.session = _ScriptedSession([_FakeResponse(200, content=b"abc")])
    client.get_bytes("https://example.org/x.pdf")
    assert ghi_cache_duoc_goi == []


def test_get_bytes_permanent_error_raises_immediately():
    client = _client_with([_FakeResponse(404, content=b"")])
    with pytest.raises(requests.HTTPError):
        client.get_bytes("https://example.org/khong-ton-tai.pdf")


def test_get_bytes_retries_on_transient_5xx_then_succeeds():
    client = _client_with([
        _FakeResponse(503, content=b""),
        _FakeResponse(200, content=b"noi dung that su"),
    ])
    out = client.get_bytes("https://example.org/bao-cao.pdf")
    assert out == b"noi dung that su"


def test_get_bytes_ncbi_misuse_block_still_detected():
    """Cùng lớp phòng thủ chặn NCBI phải hoạt động cho get_bytes() như get_json()."""
    client = _client_with([
        _FakeResponse(200, content=b"", url="https://misuse.ncbi.nlm.nih.gov/error/abuse.shtml"),
    ])
    with pytest.raises(RuntimeError, match="CHẶN"):
        client.get_bytes("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi")
