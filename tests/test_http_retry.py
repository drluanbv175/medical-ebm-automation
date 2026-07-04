"""Test retry/backoff của HttpClient (app/utils/http.py) — offline, session giả lập.

Đây là regression test cho 2 lỗi treo máy thật đã xảy ra và được sửa trong dự án:
- BMJ trả 429 kèm Retry-After: 600 -> code cũ ngủ đúng 600s, thử lại 4 lần (~40 phút/feed).
- OpenAlex trả 503 liên tục -> code cũ thử lại đủ http_max_retries cho MỖI truy vấn.
Không có test nào che phủ HttpClient trước khi các lỗi này được phát hiện (audit xác nhận
`HttpClient` không được import ở bất kỳ đâu trong tests/) — bộ test này lấp khoảng trống đó.
"""
from __future__ import annotations

import pytest
import requests

from app.utils import http as http_mod
from app.utils.http import HttpClient


class _FakeResponse:
    def __init__(self, status_code, json_data=None, text_data="", headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = text_data
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} error for test")
            err.response = self
            raise err

    def json(self):
        return self._json_data


class _ScriptedSession:
    """session.request() giả lập: trả lần lượt các response đã lên kịch bản."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def request(self, method, url, params=None, timeout=None):
        self.calls += 1
        if not self.responses:
            raise AssertionError(
                "Hết kịch bản response nhưng vẫn bị gọi thêm — retry vượt giới hạn kỳ vọng"
            )
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """KHÔNG ngủ thật trong test — ghi lại thời lượng đã 'chờ' để assert giới hạn cap."""
    slept = []
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: slept.append(s))
    return slept


def _client_with(responses):
    client = HttpClient(cache_ttl=0, min_interval=0)  # cache_ttl=0 -> không đụng cache đĩa thật
    client.session = _ScriptedSession(responses)
    return client


def test_permanent_4xx_does_not_retry():
    """403/404... là lỗi vĩnh viễn -> chỉ gọi 1 lần, không retry vô ích."""
    client = _client_with([_FakeResponse(404)])
    with pytest.raises(requests.HTTPError):
        client.get_json("http://example.test/notfound")
    assert client.session.calls == 1


def test_retryable_429_retries_exactly_once_then_gives_up():
    """429/503... chỉ retry ĐÚNG 1 lần rồi bỏ, không thử tới http_max_retries lần."""
    client = _client_with([_FakeResponse(429), _FakeResponse(429)])
    with pytest.raises(requests.HTTPError):
        client.get_json("http://example.test/ratelimited")
    assert client.session.calls == 2  # lần đầu + đúng 1 lần retry, không hơn


def test_retry_after_600_seconds_is_capped(_no_real_sleep):
    """Regression trực tiếp cho lỗi BMJ: Retry-After: 600 KHÔNG được ngủ đủ 600s."""
    client = _client_with([
        _FakeResponse(429, headers={"Retry-After": "600"}),
        _FakeResponse(429),
    ])
    with pytest.raises(requests.HTTPError):
        client.get_json("http://example.test/bmj-like")
    assert _no_real_sleep, "Phải có ít nhất 1 lần gọi time.sleep (đã mock)"
    assert max(_no_real_sleep) <= 30.0, (
        f"Retry-After=600 phải bị cap <=30s, nhưng đã 'chờ' {max(_no_real_sleep)}s"
    )


def test_success_after_one_transient_error_returns_data():
    """503 thoáng qua rồi phục hồi -> vẫn lấy được dữ liệu (retry có ích khi nguồn tự hồi)."""
    client = _client_with([
        _FakeResponse(503),
        _FakeResponse(200, json_data={"ok": True}),
    ])
    data = client.get_json("http://example.test/flaky")
    assert data == {"ok": True}
    assert client.session.calls == 2


def test_network_exception_also_capped_and_limited(_no_real_sleep):
    """Lỗi kết nối (không phải status code) cũng phải tôn trọng http_max_retries, không vô hạn."""
    client = _client_with([])
    calls = {"n": 0}

    def _raising_request(method, url, params=None, timeout=None):
        calls["n"] += 1
        raise requests.ConnectionError("boom")

    client.session.request = _raising_request
    with pytest.raises(RuntimeError, match="Gọi API thất bại"):
        client.get_json("http://example.test/downhost")
    # Dừng sau http_max_retries+1 lần thử, không lặp vô hạn.
    from app.config import settings
    assert calls["n"] == settings.http_max_retries + 1
    assert max(_no_real_sleep) <= 30.0
