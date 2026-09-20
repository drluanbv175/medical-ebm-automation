"""Test trần retry RIÊNG của từng HttpClient (`HttpClient(max_retries=...)`, thêm 20/09/2026).

Lý do tồn tại: connector SerpApi tính phí THEO REQUEST, hợp đồng là đúng MỘT request cho mỗi
`search()`. Vòng retry toàn cục của HttpClient nhân một truy vấn lỗi thành 2 request (429/5xx) hoặc
1 + http_max_retries request (timeout/mất mạng/JSON hỏng). Tham số mới cho phép một client tắt retry
mà KHÔNG đổi hành vi của mọi nguồn khác (mặc định None = dùng cấu hình toàn cục).

Offline hoàn toàn: session giả, không mở socket, không ngủ thật, không đụng cache đĩa.
"""
from __future__ import annotations

from typing import Any, List

import pytest
import requests

from app.config import settings
from app.utils import http as http_mod
from app.utils.http import HttpClient


class _PhanHoi:
    def __init__(self, status_code: int, body: Any = None, json_hong: bool = False) -> None:
        self.status_code = status_code
        self._body = {} if body is None else body
        self._json_hong = json_hong
        self.text = ""
        self.headers: dict = {}
        self.url = "https://example.invalid/api"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} error for test")
            err.response = self  # type: ignore[assignment]
            raise err

    def json(self) -> Any:
        if self._json_hong:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._body


class _PhienGia:
    """`session.request()` giả: mỗi lần gọi đếm rồi chạy kịch bản (trả response hoặc ném)."""

    def __init__(self, kich_ban) -> None:
        self.kich_ban = kich_ban
        self.calls = 0

    def request(self, method, url, params=None, timeout=None, **extra):
        self.calls += 1
        return self.kich_ban()


@pytest.fixture(autouse=True)
def _khong_ngu_that(monkeypatch):
    ngu: List[float] = []
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: ngu.append(s))
    monkeypatch.setattr(settings, "http_max_retries", 4)
    return ngu


def _client(kich_ban, **kwargs: Any) -> HttpClient:
    client = HttpClient(cache_ttl=0, min_interval=0, **kwargs)
    client.session = _PhienGia(kich_ban)
    return client


def _ném(exc: BaseException):
    def _k():
        raise exc
    return _k


_KICH_BAN_LOI = [
    pytest.param(lambda: _PhanHoi(503), id="503"),
    pytest.param(lambda: _PhanHoi(429), id="429"),
    pytest.param(lambda: _PhanHoi(500), id="500"),
    pytest.param(_ném(requests.Timeout("timeout")), id="timeout"),
    pytest.param(_ném(requests.ConnectionError("mất mạng")), id="mat-mang"),
    pytest.param(lambda: _PhanHoi(200, json_hong=True), id="200-json-hong"),
]


@pytest.mark.parametrize("kich_ban", _KICH_BAN_LOI)
def test_max_retries_zero_sends_exactly_one_request_and_never_sleeps(kich_ban, _khong_ngu_that):
    client = _client(kich_ban, max_retries=0)
    with pytest.raises((requests.HTTPError, RuntimeError)):
        client.get_json("https://example.invalid/api", params={"q": "x"})
    assert client.session.calls == 1
    assert client.request_count == 1
    assert _khong_ngu_that == [], f"không còn lượt thử lại thì không được ngủ backoff: {_khong_ngu_that}"
    assert client.health_snapshot()["failure_count"] == 1


def test_max_retries_zero_keeps_real_status_code_on_http_error():
    client = _client(lambda: _PhanHoi(503), max_retries=0)
    with pytest.raises(requests.HTTPError):
        client.get_json("https://example.invalid/api")
    assert client.health_snapshot()["last_status_code"] == 503


def test_max_retries_zero_still_returns_success_normally():
    client = _client(lambda: _PhanHoi(200, {"ok": True}), max_retries=0)
    assert client.get_json("https://example.invalid/api") == {"ok": True}
    assert client.session.calls == 1
    assert client.health_snapshot()["success_count"] == 1


@pytest.mark.parametrize("kich_ban", [
    pytest.param(_ném(requests.Timeout("timeout")), id="timeout"),
    pytest.param(lambda: _PhanHoi(200, json_hong=True), id="200-json-hong"),
])
def test_positive_cap_limits_transport_retries_to_the_cap(kich_ban):
    client = _client(kich_ban, max_retries=2)
    with pytest.raises(RuntimeError):
        client.get_json("https://example.invalid/api")
    assert client.session.calls == 3  # 1 lần đầu + 2 lần thử lại


def test_positive_cap_keeps_the_single_retry_for_429_and_5xx():
    client = _client(lambda: _PhanHoi(503), max_retries=2)
    with pytest.raises(requests.HTTPError):
        client.get_json("https://example.invalid/api")
    assert client.session.calls == 2  # 429/5xx vẫn chỉ thử lại đúng 1 lần như hành vi cũ


def test_retry_then_success_within_positive_cap():
    thu_tu = iter([_PhanHoi(503), _PhanHoi(200, {"ok": 1})])
    client = _client(lambda: next(thu_tu), max_retries=1)
    assert client.get_json("https://example.invalid/api") == {"ok": 1}
    assert client.session.calls == 2


# ── Hành vi mặc định của MỌI nguồn khác không đổi ────────────────────────────

def test_default_client_keeps_global_retry_behaviour_for_transport_errors():
    client = _client(_ném(requests.ConnectionError("mất mạng")))
    assert client.max_retries is None
    with pytest.raises(RuntimeError):
        client.get_json("https://example.invalid/api")
    assert client.session.calls == settings.http_max_retries + 1


def test_default_client_keeps_single_retry_for_5xx():
    client = _client(lambda: _PhanHoi(503))
    with pytest.raises(requests.HTTPError):
        client.get_json("https://example.invalid/api")
    assert client.session.calls == 2


def test_default_client_terminal_message_unchanged():
    client = _client(_ném(requests.ConnectionError("mất mạng")))
    with pytest.raises(RuntimeError) as ei:
        client.get_json("https://example.invalid/api")
    assert str(ei.value) == f"Gọi API thất bại sau {settings.http_max_retries} lần: https://example.invalid/api"


@pytest.mark.parametrize("gia_tri", [-1, True, False, "3", 1.5])
def test_invalid_max_retries_is_rejected_at_construction(gia_tri):
    with pytest.raises(ValueError):
        HttpClient(cache_ttl=0, min_interval=0, max_retries=gia_tri)


def test_api_key_never_appears_in_terminal_error_of_capped_client():
    """Thông báo lỗi cuối của client có trần riêng không được chứa query/params (nơi có api_key)."""
    client = _client(_ném(requests.ConnectionError("mất mạng")), max_retries=0)
    with pytest.raises(RuntimeError) as ei:
        client.get_json("https://example.invalid/api", params={"api_key": "SENTINEL_KEY_XYZ", "q": "x"})
    assert "SENTINEL_KEY_XYZ" not in str(ei.value)
    assert "SENTINEL_KEY_XYZ" not in client.health_snapshot()["last_error"]
