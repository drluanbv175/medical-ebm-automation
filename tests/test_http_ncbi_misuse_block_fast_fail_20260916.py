"""Hồi quy vá 2026-09-16 trong app/utils/http.py::HttpClient._request().

CƠ CHẾ LỖI (đã xác minh THẬT, không phải suy đoán): NCBI đôi khi CHUYỂN HƯỚNG
(302) mọi request eutils.ncbi.nlm.nih.gov sang
misuse.ncbi.nlm.nih.gov/error/abuse.shtml — trang cảnh báo lạm dụng CHÍNH THỨC
của NCBI, phía SERVER. Trang đó trả HTTP 200 (không phải 4xx/5xx) kèm thân HTML
"NCBI Error Access Denied" thay vì JSON. Vì status là 200, request KHÔNG rơi vào
nhánh permanent/retryable status ngay dưới nó; nó chỉ bị bắt muộn ở `resp.json()`
(ValueError vì thân HTML không phải JSON) và bị đối xử như lỗi TẠM THỜI — retry
đủ `settings.http_max_retries` lần với backoff mũ (mặc định ~46 giây tổng cộng
CHO MỖI truy vấn) dù chặn này KHÔNG BAO GIỜ tự hết bằng cách gọi lại.

Xác minh trực tiếp (16/09/2026, mạng thật của người dùng): gọi thẳng
`requests.get(...)` không qua HttpClient tới esearch.fcgi trả
`r.url == "https://misuse.ncbi.nlm.nih.gov/error/abuse.shtml?orig_args=..."`,
`r.history == [(302, "https://eutils.ncbi.nlm.nih.gov/...")]`,
`r.status_code == 200`, thân trang chứa tiêu đề
"NCBI - WWW Error Blocked Diagnostic" và câu
"Your access to the NCBI website ... has been temporarily blocked due to a
possible misuse/abuse situation".

BẢN VÁ: phát hiện ĐÍCH DANH `urlparse(resp.url).netloc == "misuse.ncbi.nlm.nih.gov"`
ngay sau khi có response — TRƯỚC mọi nhánh status-code khác — raise
RuntimeError ngay lập tức, KHÔNG retry, giữ status code thật, ghi rõ lý do
trong thông điệp lỗi để phân biệt với lỗi mạng tạm thời.

Nguyên tắc viết test: dùng lại đúng mock pattern (_FakeResponse, _ScriptedSession)
đã có ở tests/test_http_retry.py và
tests/test_http_workflow_20260905_vong22_unlisted_status_wasted_retry.py để gọi
THẲNG HttpClient._request() thật, không mock lớp cao hơn."""
from __future__ import annotations

import pytest
import requests

from app.utils import http as http_mod
from app.utils.http import HttpClient


class _FakeResponse:
    def __init__(self, status_code, url, json_data=None, text_data="", headers=None):
        self.status_code = status_code
        self.url = url
        self._json_data = json_data if json_data is not None else {}
        self.text = text_data
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} error for test")
            err.response = self
            raise err

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
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


_MISUSE_URL = (
    "https://misuse.ncbi.nlm.nih.gov/error/abuse.shtml"
    "?orig_args=/entrez/eutils/esearch.fcgi"
)
_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


class TestNcbiMisuseBlockRaiseNgayKhongRetry:
    """★★★ Ca chính — chuyển hướng sang misuse.ncbi.nlm.nih.gov phải raise NGAY
    lần đầu, không retry, không sleep."""

    def test_misuse_redirect_raise_ngay_lan_dau(self, _no_real_sleep):
        client = _client_with(
            [_FakeResponse(200, _MISUSE_URL, text_data="<!doctype html>NCBI Error Access Denied")]
        )
        with pytest.raises(RuntimeError, match="misuse"):
            client.get_json(_ESEARCH_URL)
        assert client.session.calls == 1, (
            "TRƯỚC bản vá: response 200 với thân HTML rơi vào nhánh retry chung, "
            "gọi lại nhiều lần thay vì raise ngay lần đầu"
        )

    def test_misuse_redirect_khong_sleep_backoff(self, _no_real_sleep):
        """TRƯỚC bản vá: 4 lần retry mặc định x backoff mũ ~46 giây tổng cộng."""
        client = _client_with(
            [_FakeResponse(200, _MISUSE_URL, text_data="<!doctype html>NCBI Error Access Denied")]
        )
        with pytest.raises(RuntimeError):
            client.get_json(_ESEARCH_URL)
        assert _no_real_sleep == [], (
            f"Vẫn còn {len(_no_real_sleep)} lần sleep — chặn misuse bị đối xử như "
            f"lỗi tạm thời thay vì fail ngay"
        )

    def test_misuse_redirect_giu_dung_status_code_that(self):
        client = _client_with(
            [_FakeResponse(200, _MISUSE_URL, text_data="<!doctype html>NCBI Error Access Denied")]
        )
        with pytest.raises(RuntimeError):
            client.get_json(_ESEARCH_URL)
        assert client.last_status_code == 200
        assert client.health_snapshot()["last_status_code"] == 200

    def test_thong_diep_loi_phan_biet_duoc_voi_loi_mang_tam_thoi(self):
        """Caller (vd retraction_chain.py) phải phân biệt được đây là chặn VĨNH
        VIỄN phía server, không phải lỗi mạng — để không hiểu nhầm 'unresolved'."""
        client = _client_with(
            [_FakeResponse(200, _MISUSE_URL, text_data="<!doctype html>NCBI Error Access Denied")]
        )
        with pytest.raises(RuntimeError) as exc_info:
            client.get_json(_ESEARCH_URL)
        msg = str(exc_info.value)
        assert "NCBI" in msg
        assert "misuse" in msg.lower() or "lạm dụng" in msg


class TestDoiChungKhongTrungBoLoiThat:
    """Đối chứng bắt buộc — phản hồi NCBI hợp lệ hoặc host khác bị chuyển hướng
    KHÔNG bị bắt nhầm bởi bản vá mới."""

    def test_ncbi_thanh_cong_binh_thuong_khong_bi_anh_huong(self):
        client = _client_with(
            [_FakeResponse(200, _ESEARCH_URL, json_data={"esearchresult": {"idlist": ["1"]}})]
        )
        data = client.get_json(_ESEARCH_URL)
        assert data == {"esearchresult": {"idlist": ["1"]}}
        assert client.session.calls == 1

    def test_chuyen_huong_sang_host_khac_khong_trung_bo_loi_misuse(self):
        """Một host KHÁC bị chuyển hướng (không phải misuse.ncbi.nlm.nih.gov) mà
        thân HTML không parse được JSON vẫn phải đi qua đường xử lý CŨ (transient
        failure, có retry) — bản vá chỉ nhắm đích danh netloc misuse.ncbi."""
        other_redirect_url = "https://example.test/maintenance.html"

        def _html_that_fails_json_parse():
            # .json() thật của requests raise ValueError khi thân không phải JSON —
            # mô phỏng bằng cách truyền một Exception làm "giá trị" để _FakeResponse
            # raise đúng loại lỗi thật sự xảy ra khi parse HTML thành JSON.
            return _FakeResponse(
                200, other_redirect_url, json_data=ValueError("Expecting value: line 1 column 1 (char 0)"),
                text_data="<html>Down for maintenance</html>",
            )

        client = _client_with([_html_that_fails_json_parse() for _ in range(5)])
        with pytest.raises(RuntimeError, match="Gọi API thất bại"):
            client.get_json("https://example.test/api")
        # Vẫn dùng đường xử lý CŨ (retry tối đa http_max_retries+1 lần), không phải
        # fail-fast mới — chứng minh bản vá không quá tay (over-broad).
        assert client.session.calls == 5

    def test_misuse_khi_gap_efetch_text_cung_raise_ngay(self):
        """get_text() (dùng cho efetch XML) cũng phải đi qua cùng đường phát hiện."""
        client = _client_with(
            [_FakeResponse(200, _MISUSE_URL, text_data="<!doctype html>NCBI Error Access Denied")]
        )
        with pytest.raises(RuntimeError, match="misuse"):
            client.get_text("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi")
        assert client.session.calls == 1
