"""Hồi quy vá 24/09/2026 trong app/utils/http.py::HttpClient._request().

CƠ CHẾ LỖI (đo THẬT trên phiên Cloud, môi trường «Default — Trusted network access»):
proxy thoát mạng của môi trường từ chối lệnh CONNECT tới mọi host API y văn theo CHÍNH
SÁCH, và `requests` ném `ProxyError(... OSError('Tunnel connection failed: 403 Forbidden'))`.
Vì `ProxyError` là con của `RequestException`, lỗi này rơi vào nhánh lỗi TẠM THỜI ⇒ retry
đủ `settings.http_max_retries` (mặc định 4) với backoff ≈ 48 giây cho MỖI lời gọi — đo
thật: 7 nguồn × 48 s trong một lượt `run.py test-live` — mà không bao giờ thành công vì
chính sách không đổi giữa hai lần thử. README proxy của môi trường cũng yêu cầu KHÔNG thử
lại khi bị từ chối theo chính sách.

BẢN VÁ: chỉ khớp ĐÍCH DANH `ProxyError` có «Tunnel connection failed: 403|407» ⇒ raise
RuntimeError ngay, không retry, không ngủ backoff, thông điệp nêu host + chỗ sửa (Network
access của môi trường). Mọi lỗi kết nối khác (kể cả ProxyError không phải 403/407) giữ
nguyên đường retry cũ.

Cùng khuôn mock với tests/test_http_ncbi_misuse_block_fast_fail_20260916.py: gọi THẲNG
HttpClient._request() thật qua phiên giả, không mock lớp cao hơn."""
from __future__ import annotations

import pytest
import requests

from app.utils import http as http_mod
from app.utils.http import HttpClient, _la_proxy_tu_choi_chinh_sach


def _proxy_error(ma: str) -> requests.exceptions.ProxyError:
    """Dựng đúng hình dạng lỗi `requests` ném khi proxy từ chối CONNECT (đã đo thật)."""
    return requests.exceptions.ProxyError(
        "HTTPSConnectionPool(host='api.openalex.org', port=443): Max retries exceeded with url: "
        "/works?per-page=1 (Caused by ProxyError('Unable to connect to proxy', "
        f"OSError('Tunnel connection failed: {ma}')))"
    )


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self.url = "https://api.openalex.org/works"
        self._json_data = json_data if json_data is not None else {"ok": True}
        self.text = ""
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} error for test")
            err.response = self
            raise err

    def json(self):
        return self._json_data


class _ScriptedSession:
    """Mỗi phần tử kịch bản: Exception thì ném, còn lại trả về như response."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def request(self, method, url, params=None, timeout=None):
        self.calls += 1
        if not self.script:
            raise AssertionError("Hết kịch bản nhưng vẫn bị gọi thêm — retry vượt kỳ vọng")
        buoc = self.script.pop(0)
        if isinstance(buoc, BaseException):
            raise buoc
        return buoc


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: slept.append(s))
    return slept


def _client(session, **kw) -> HttpClient:
    # min_interval=0: không giãn cách theo host — `_throttle` gọi time.sleep() lặp (đã giả lập
    # thành no-op) nên bật giãn cách sẽ biến danh sách `slept` thành vòng lặp bận vô nghĩa.
    c = HttpClient(cache_ttl=0, min_interval=0, **kw)
    c.session = session
    return c


def test_nhan_dien_dung_403_va_407():
    assert _la_proxy_tu_choi_chinh_sach(_proxy_error("403 Forbidden"))
    assert _la_proxy_tu_choi_chinh_sach(_proxy_error("407 Proxy Authentication Required"))


def test_khong_nham_proxyerror_khac_hoac_connectionerror_thuong():
    # Proxy chưa lên / đứt kết nối là chuyện TẠM THỜI — không được gộp với chặn chính sách.
    assert not _la_proxy_tu_choi_chinh_sach(requests.exceptions.ProxyError(
        "Caused by ProxyError('Unable to connect to proxy', ConnectionRefusedError(111))"))
    assert not _la_proxy_tu_choi_chinh_sach(requests.exceptions.ConnectionError(
        "Tunnel connection failed: 403 Forbidden"))  # không phải ProxyError ⇒ không khớp
    assert not _la_proxy_tu_choi_chinh_sach(_proxy_error("502 Bad Gateway"))


def test_proxy_tu_choi_bo_ngay_mot_request_khong_ngu(_no_real_sleep):
    s = _ScriptedSession([_proxy_error("403 Forbidden")] * 5)
    c = _client(s)
    with pytest.raises(RuntimeError) as ei:
        c.get_json("https://api.openalex.org/works", params={"per-page": 1})
    assert s.calls == 1, "chặn chính sách phải bỏ ngay — không gửi thêm request nào"
    assert _no_real_sleep == [], "không được ngủ backoff vô ích"
    msg = str(ei.value)
    assert "api.openalex.org" in msg and "chính sách" in msg and "Allowed domains" in msg
    assert c.failure_count == 1 and c.transient_failure_count == 0
    assert "chính sách" in c.last_error


def test_loi_ket_noi_thuong_van_retry_nhu_cu(_no_real_sleep, monkeypatch):
    monkeypatch.setattr(http_mod.settings, "http_max_retries", 2)
    s = _ScriptedSession([requests.exceptions.ConnectionError("reset by peer")] * 2
                         + [_FakeResponse(200, {"results": []})])
    c = _client(s)
    assert c.get_json("https://api.openalex.org/works") == {"results": []}
    assert s.calls == 3 and len(_no_real_sleep) == 2


def test_proxyerror_khong_phai_403_van_retry(_no_real_sleep, monkeypatch):
    monkeypatch.setattr(http_mod.settings, "http_max_retries", 1)
    s = _ScriptedSession([_proxy_error("502 Bad Gateway"), _FakeResponse(200, {"a": 1})])
    c = _client(s)
    assert c.get_json("https://api.openalex.org/works") == {"a": 1}
    assert s.calls == 2


def test_client_co_tran_rieng_cung_bo_ngay():
    s = _ScriptedSession([_proxy_error("403 Forbidden")] * 3)
    c = _client(s, max_retries=3)
    with pytest.raises(RuntimeError):
        c.get_json("https://serpapi.com/search.json", params={"api_key": "BIMAT"})
    assert s.calls == 1
    assert "BIMAT" not in c.last_error, "khoá API không được lọt vào last_error/log"
