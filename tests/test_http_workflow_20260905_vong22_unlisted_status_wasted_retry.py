"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 22) trong app/utils/http.py::HttpClient._request().

CƠ CHẾ LỖI: trước bản vá, chỉ đúng 5 mã (400/401/403/404/410, `_PERMANENT_
STATUS`) được coi là "vĩnh viễn" (raise ngay). Mọi mã lỗi KHÁC không nằm
trong danh sách đó VÀ cũng không nằm trong `_RETRYABLE_STATUS`
(429/500/502/503/504) — vd 402, 405, 406, 409, 415, 422, 423, 428, 431, 451,
501, 505... — rơi thẳng vào nhánh try/except cuối cùng (vốn để bắt lỗi
PARSE JSON/kết nối SAU KHI status đã "coi là OK"). Vì `requests.HTTPError`
là subclass của `requests.RequestException`, exception đó bị đối xử y như
lỗi tạm thời: retry đủ `settings.http_max_retries` lần rồi cuối cùng raise
một `RuntimeError` CHUNG CHUNG, mất luôn status code thật
(`last_status_code` không được cập nhật ở nhánh đó) — ngược với chính ý
định "4xx vĩnh viễn: retry vô ích, bỏ ngay lần đầu" mà comment gốc tự khai.

Với ingestion chạy hàng chục query liên tiếp tới cùng một nguồn (comment
gốc dòng ~220-222 tự thừa nhận rủi ro này cho _RETRYABLE_STATUS), một
endpoint trả mã lỗi ngoài 2 danh sách gây treo lặp lại nhiều phút — đúng sự
cố mà `_MAX_RETRYABLE_RETRIES` được viết ra để tránh, nhưng lọt qua đường
vòng này.

BẢN VÁ: mọi mã lỗi (>=400) không thuộc `_RETRYABLE_STATUS` đều coi là vĩnh
viễn — raise ngay lần đầu, giữ đúng status code thật trong
`last_status_code`/`health_snapshot()`.

Nguyên tắc viết test: dùng lại đúng mock pattern (_FakeResponse,
_ScriptedSession) đã có ở tests/test_http_retry.py để gọi THẲNG
HttpClient._request() thật."""
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
    slept = []
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: slept.append(s))
    return slept


def _client_with(responses):
    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _ScriptedSession(responses)
    return client


class TestMaLoiNgoaiHaiDanhSachRaiseNgayKhongLangPhiRetry:
    """★★★ Ca chính — mã lỗi ngoài _PERMANENT_STATUS/_RETRYABLE_STATUS cũ
    phải raise HTTPError NGAY LẦN ĐẦU, giữ đúng status code, không lãng phí
    retry."""

    @pytest.mark.parametrize("status", [402, 405, 406, 409, 415, 422, 423, 428, 431, 451, 501, 505])
    def test_ma_loi_khong_liet_ke_raise_ngay_khong_retry(self, status):
        client = _client_with([_FakeResponse(status)])
        with pytest.raises(requests.HTTPError):
            client.get_json(f"http://example.test/unlisted-{status}")
        assert client.session.calls == 1, (
            f"TRƯỚC bản vá: HTTP {status} rơi vào nhánh retry chung, gọi lại "
            f"nhiều lần thay vì raise ngay lần đầu"
        )

    def test_status_422_giu_dung_status_code_that_trong_last_status_code(self):
        """TRƯỚC bản vá: nhánh retry-chung không cập nhật last_status_code,
        nên health_snapshot() mất dấu vết mã lỗi thật."""
        client = _client_with([_FakeResponse(422)])
        with pytest.raises(requests.HTTPError):
            client.get_json("http://example.test/unprocessable")
        assert client.last_status_code == 422
        assert client.health_snapshot()["last_status_code"] == 422

    def test_status_422_khong_raise_runtimeerror_chung_chung(self):
        """TRƯỚC bản vá: sau khi retry hết settings.http_max_retries lần,
        client raise RuntimeError("Gọi API thất bại...") thay vì HTTPError —
        caller mất luôn dấu vết mã lỗi thật."""
        client = _client_with([_FakeResponse(422)])
        with pytest.raises(requests.HTTPError) as exc_info:
            client.get_json("http://example.test/unprocessable")
        assert "422" in str(exc_info.value)


class TestDoiChungMaLoiDaLietKeKhongDoiHanhVi:
    """Đối chứng bắt buộc — hành vi của 5 mã _PERMANENT_STATUS cũ và
    _RETRYABLE_STATUS không đổi (không phải bản vá tự sinh ra bằng cách
    xoá bỏ hoàn toàn hai danh sách gốc)."""

    def test_404_van_raise_ngay_khong_retry(self):
        client = _client_with([_FakeResponse(404)])
        with pytest.raises(requests.HTTPError):
            client.get_json("http://example.test/notfound")
        assert client.session.calls == 1

    def test_429_van_retry_dung_1_lan_roi_bo(self):
        client = _client_with([_FakeResponse(429), _FakeResponse(429)])
        with pytest.raises(requests.HTTPError):
            client.get_json("http://example.test/ratelimited")
        assert client.session.calls == 2

    def test_503_thoang_qua_van_phuc_hoi_duoc(self):
        client = _client_with([_FakeResponse(503), _FakeResponse(200, json_data={"ok": True})])
        data = client.get_json("http://example.test/flaky")
        assert data == {"ok": True}
        assert client.session.calls == 2

    def test_200_thanh_cong_van_hoat_dong_dung(self):
        client = _client_with([_FakeResponse(200, json_data={"ok": True})])
        data = client.get_json("http://example.test/ok")
        assert data == {"ok": True}
        assert client.last_status_code == 200
