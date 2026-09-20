"""Kiểm helper Scite công khai (`app/sources/scite_public.py`, lớp `SciteClient`) — thêm 20/09/2026.

Bộ test này do một tác giả ĐỘC LẬP viết từ HỢP ĐỒNG (CONTRACT) và các SỰ KIỆN SCITE đọc từ
docs.scite.ai ngày 20/09/2026, KHÔNG đọc mã cài đặt, để bắt lệch giữa "điều đã hứa" và "điều đã làm".

`SciteClient` KHÔNG phải nguồn khám phá và KHÔNG phải tầng dự phòng: nó chỉ là lớp XÁC MINH phụ, đọc hai
endpoint CÔNG KHAI không cần khoá (`GET /papers/{doi}`, `GET /tallies/{doi}`). Endpoint Search của Scite đòi khoá
Pro VÀ thoả thuận cấp phép riêng cho việc dùng thương mại/nghiên cứu nên cố ý KHÔNG được dùng. Vì thế các quy
tắc được canh chặt:

  * chỉ gọi đúng `https://api.scite.ai/papers/<doi>` và `/tallies/<doi>`; KHÔNG BAO GIỜ gửi header
    Authorization / khoá API nào; DOI được kiểm và mã hoá URL trước khi dùng (DOI lạ/độc không được đổi host,
    cắt đường dẫn hay chèn tham số);
  * 404 (DOI không có trong Scite) => `None`, không thử lại cùng giá trị; lỗi khác => `RuntimeError` có
    thuộc tính `loai` (khong_tim_thay | gioi_han_toc_do | loi_phia_scite | phan_hoi_khong_hop_le | khac);
  * "im lặng khác an toàn": trường `retracted` vắng/null KHÔNG được biến thành False.

Mọi test OFFLINE: `requests.Session.request` bị thay bằng bản giả ở cấp lớp (chạy NGUYÊN lớp HttpClient thật: retry,
telemetry) và socket bị chặn nên không có gói tin nào rời máy. Dữ liệu mẫu dựng theo ví dụ nguyên văn của tài
liệu Scite (bài 10.1038/nature12373); các giá trị còn lại là dữ liệu giả rõ ràng.
"""
from __future__ import annotations

import json
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.sources.scite_public as scite_mod  # noqa: E402
from app.config import settings  # noqa: E402
from app.sources.base import SourceClient  # noqa: E402
from app.sources.scite_public import SciteClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils.http import HttpClient  # noqa: E402

DOI_MAU = "10.1038/nature12373"
VOCAB_LOI = {"khong_tim_thay", "gioi_han_toc_do", "loi_phia_scite", "phan_hoi_khong_hop_le", "khac"}

# Dựng theo ví dụ nguyên văn của docs.scite.ai (bài 10.1038/nature12373); tóm tắt/tác giả rút gọn thành dữ liệu giả.
BAI_MAU: Dict[str, Any] = {
    "id": 81329739, "doi": DOI_MAU, "slug": "nanometre-scale-thermometry-in-a-living-cell",
    "type": "journal-article", "title": "Nanometre-scale thermometry in a living cell",
    "abstract": "Fake abstract text for tests.",
    "authors": [{"family": "Kucsko", "given": "Georg", "affiliation": "Harvard University",
                 "authorSlug": "georg-kucsko", "authorName": "Georg Kucsko", "authorID": "abc123",
                 "authorSequenceNumber": 1}],
    "keywords": ["Article"], "year": 2013, "shortJournal": "Nature", "publisher": "Fake Publisher LLC",
    "issue": "7460", "volume": "500", "page": "54-58", "retracted": False, "memberId": 297,
    "issns": ["0028-0836", "1476-4687"], "editorialNotices": [], "journalSlug": "nature", "journal": "Nature",
    "preprintLinks": [{"preprintDoi": "10.48550/arxiv.1304.1068"}], "publicationLinks": [],
    "normalizedTypes": ["article"],
}
TALLY_MAU: Dict[str, Any] = {"total": 1909, "supporting": 21, "contradicting": 1, "mentioning": 1878,
                             "unclassified": 9, "doi": DOI_MAU, "citingPublications": 2116}


# ════════════════════════════════════════════════════════════════════════════
# Mạng giả cấp lớp requests.Session.request
# ════════════════════════════════════════════════════════════════════════════

class _PhanHoi:
    """Giả `requests.Response`."""

    def __init__(self, status_code: int, body: Any, url: str, headers: Optional[Dict[str, str]] = None,
                 json_hong: bool = False) -> None:
        self.status_code = status_code
        self._body = body
        self._json_hong = json_hong
        self.text = "<html>khong phai json</html>" if json_hong else json.dumps(body, ensure_ascii=False)
        self.headers: Dict[str, str] = dict(headers or {})
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} Client Error: reason for url: {self.url}")
            err.response = self  # type: ignore[assignment]
            raise err

    def json(self) -> Any:
        if self._json_hong:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._body


class _MangGia:
    """Ghi lại MỌI request rời `requests.Session.request` rồi hỏi `kich_ban(url)` trả phản hồi/ném lỗi."""

    def __init__(self, kich_ban) -> None:
        self.kich_ban = kich_ban
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, session, method, url, params=None, timeout=None, **kw):
        tieu_de = {str(k).lower(): str(v) for k, v in dict(session.headers).items()}
        tieu_de.update({str(k).lower(): str(v) for k, v in dict(kw.get("headers") or {}).items()})
        self.calls.append({"method": method, "url": url, "params": dict(params or {}), "headers": tieu_de})
        return self.kich_ban(url)

    @property
    def urls(self) -> List[str]:
        return [c["url"] for c in self.calls]


@pytest.fixture()
def mang(monkeypatch, tmp_path):
    """Cách ly hoàn toàn: không cache đĩa, không ngủ thật, không socket; trả `_MangGia` để đặt kịch bản."""
    monkeypatch.setattr(settings, "http_cache_ttl", 0)
    monkeypatch.setattr(settings, "http_min_interval", 0)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    ngu: List[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: ngu.append(float(s)))

    def _cam(*_a, **_k):
        raise AssertionError("test Scite KHÔNG được mở kết nối mạng thật")

    monkeypatch.setattr(socket.socket, "connect", _cam)
    monkeypatch.setattr(socket.socket, "connect_ex", _cam)

    holder = _MangGia(lambda url: (_ for _ in ()).throw(AssertionError(f"chưa đặt kịch bản cho {url}")))
    monkeypatch.setattr(requests.Session, "request",
                        lambda self, method, url, params=None, timeout=None, **kw:
                        holder(self, method, url, params, timeout, **kw))
    holder.ngu = ngu  # type: ignore[attr-defined]
    return holder


def _dat(mang: _MangGia, kich_ban) -> None:
    mang.kich_ban = kich_ban


def _ok(bai: Any = None, tally: Any = None):
    """Kịch bản: /papers/ trả bài, /tallies/ trả tally.

    Scite THẬT luôn trả bản ghi của ĐÚNG DOI được hỏi, nên bản giả cũng lặp lại DOI trong đường dẫn (nếu không,
    một DOI khác DOI mẫu sẽ nhận về bản ghi của bài khác — kịch bản không có thật)."""
    def kich_ban(url):
        duong = unquote(urlparse(url).path)
        if duong.startswith("/papers/"):
            return _PhanHoi(200, dict(BAI_MAU if bai is None else bai, doi=duong[len("/papers/"):]), url)
        if duong.startswith("/tallies/"):
            return _PhanHoi(200, dict(TALLY_MAU if tally is None else tally, doi=duong[len("/tallies/"):]), url)
        raise AssertionError(f"endpoint ngoài hợp đồng: {url}")
    return kich_ban


# ════════════════════════════════════════════════════════════════════════════
# Danh tính, phạm vi và tài liệu
# ════════════════════════════════════════════════════════════════════════════

def test_scite_client_is_a_small_helper_not_a_source_or_a_tier():
    assert not issubclass(SciteClient, SourceClient)
    client = SciteClient()
    assert isinstance(client.http, HttpClient)
    assert client.http.max_retries == 1, "HttpClient(max_retries=1) theo hợp đồng"


def test_scite_is_not_registered_as_a_test_live_source():
    from app.main import _build_source_map

    assert not any("scite" in ten.lower() for ten in _build_source_map())


def test_module_docstring_states_the_licence_reason_and_the_unverified_items():
    doc = scite_mod.__doc__ or ""
    assert re.search(r"(?i)search", doc), "phải nêu endpoint Search bị bỏ qua có chủ đích"
    assert re.search(r"(?i)(licen[sc]e|giấy phép|cấp phép|thoả thuận|thỏa thuận)", doc), "phải nêu lý do giấy phép"
    assert re.search(r"(?i)(chưa xác minh|unverified|chưa kiểm)", doc), "phải liệt kê các điều CHƯA xác minh"


def test_constructing_the_client_needs_no_key_and_no_network(mang):
    SciteClient()
    assert mang.calls == []


# ════════════════════════════════════════════════════════════════════════════
# GET /papers/{doi}
# ════════════════════════════════════════════════════════════════════════════

def test_lay_bai_calls_only_the_public_papers_endpoint(mang):
    _dat(mang, _ok())
    SciteClient().lay_bai(DOI_MAU)
    assert len(mang.calls) == 1
    goi = mang.calls[0]
    u = urlparse(goi["url"])
    assert goi["method"].upper() == "GET"
    assert u.scheme == "https" and u.hostname == "api.scite.ai"
    assert unquote(u.path) == f"/papers/{DOI_MAU}"
    assert u.query == "" and u.fragment == "" and not goi["params"]


def test_lay_bai_normalizes_the_documented_papers_response(mang):
    _dat(mang, _ok())
    kq = SciteClient().lay_bai(DOI_MAU)
    assert isinstance(kq, dict)
    assert kq["doi"].lower() == DOI_MAU
    assert kq["title"] == "Nanometre-scale thermometry in a living cell"
    assert kq["year"] == 2013
    assert kq["journal"] == "Nature"
    assert kq["retracted"] is False
    assert kq["editorial_notices"] == []


def test_lay_bai_reports_a_retracted_paper_and_keeps_the_notices(mang):
    bai = dict(BAI_MAU, retracted=True,
               editorialNotices=[{"type": "retraction", "title": "Retraction Note: fake notice"}])
    _dat(mang, _ok(bai=bai))
    kq = SciteClient().lay_bai(DOI_MAU)
    assert kq["retracted"] is True
    assert isinstance(kq["editorial_notices"], list) and len(kq["editorial_notices"]) == 1
    assert "retraction" in json.dumps(kq["editorial_notices"], ensure_ascii=False).lower()


def test_missing_retracted_field_is_never_turned_into_false(mang):
    """Im lặng khác an toàn: Scite không nói gì về `retracted` thì KHÔNG được khẳng định "chưa bị rút"."""
    bai = {k: v for k, v in BAI_MAU.items() if k not in ("retracted", "editorialNotices")}
    _dat(mang, _ok(bai=bai))
    kq = SciteClient().lay_bai(DOI_MAU)
    assert kq is None or kq.get("retracted") is not False
    if kq is not None:
        assert not kq.get("editorial_notices")


def test_null_retracted_field_is_never_turned_into_false(mang):
    _dat(mang, _ok(bai=dict(BAI_MAU, retracted=None)))
    kq = SciteClient().lay_bai(DOI_MAU)
    assert kq is None or kq.get("retracted") is not False


# ════════════════════════════════════════════════════════════════════════════
# GET /tallies/{doi}
# ════════════════════════════════════════════════════════════════════════════

def test_lay_tally_calls_only_the_public_tallies_endpoint_and_returns_the_counts(mang):
    _dat(mang, _ok())
    kq = SciteClient().lay_tally(DOI_MAU)
    assert len(mang.calls) == 1
    u = urlparse(mang.calls[0]["url"])
    assert u.hostname == "api.scite.ai" and unquote(u.path) == f"/tallies/{DOI_MAU}"
    assert isinstance(kq, dict)
    assert kq["total"] == 1909 and kq["supporting"] == 21
    assert kq["contradicting"] == 1 and kq["mentioning"] == 1878


# ════════════════════════════════════════════════════════════════════════════
# Không bao giờ gửi khoá / Authorization; chỉ hai endpoint công khai; không Search
# ════════════════════════════════════════════════════════════════════════════

def test_no_authorization_or_key_header_is_ever_sent(mang, monkeypatch):
    monkeypatch.setenv("SCITE_API_KEY", "SENTINEL_SCITE_KEY_0123")
    monkeypatch.setenv("SCITE_TOKEN", "SENTINEL_SCITE_KEY_0123")
    _dat(mang, _ok())
    client = SciteClient()
    client.lay_bai(DOI_MAU)
    client.lay_tally(DOI_MAU)
    assert len(mang.calls) == 2
    for goi in mang.calls:
        ten_header = set(goi["headers"])
        assert "authorization" not in ten_header
        assert not any("key" in h or "token" in h or "cookie" in h for h in ten_header), ten_header
        assert "SENTINEL_SCITE_KEY_0123" not in json.dumps(goi, default=str)
        assert not any("key" in str(p).lower() or "token" in str(p).lower() for p in goi["params"])


def test_only_papers_and_tallies_endpoints_are_ever_used(mang):
    _dat(mang, _ok())
    client = SciteClient()
    for doi in (DOI_MAU, "10.5555/fake.scite.1", "10.5555/fake.scite.2"):
        client.lay_bai(doi)
        client.lay_tally(doi)
    assert mang.urls, "test vô nghĩa nếu không có request nào"
    for url in mang.urls:
        assert re.match(r"^https://api\.scite\.ai/(papers|tallies)/", url), url
        assert "/search" not in url.lower()


# ════════════════════════════════════════════════════════════════════════════
# 404 => None (không thử lại cùng giá trị); các lỗi khác => lỗi có phân loại
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
def test_404_returns_none_without_retrying(mang, ham):
    _dat(mang, lambda url: _PhanHoi(404, {"detail": "Not Found"}, url))
    assert getattr(SciteClient(), ham)("10.5555/khong.co.trong.scite") is None
    assert len(mang.calls) == 1, "404 là câu trả lời dứt khoát: thử lại cùng DOI là vô ích"


@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
def test_429_raises_a_classified_error_and_retries_at_most_once(mang, ham):
    _dat(mang, lambda url: _PhanHoi(429, {"detail": "Rate limit exceeded"}, url, headers={"Retry-After": "2"}))
    with pytest.raises(RuntimeError) as ei:
        getattr(SciteClient(), ham)(DOI_MAU)
    assert getattr(ei.value, "loai", None) == "gioi_han_toc_do"
    assert 1 <= len(mang.calls) <= 2, "max_retries=1: tối đa MỘT lần thử lại"


@pytest.mark.parametrize("ma", [500, 502, 503, 504])
@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
def test_5xx_raises_a_server_side_classified_error(mang, ham, ma):
    _dat(mang, lambda url: _PhanHoi(ma, {"detail": "boom"}, url))
    with pytest.raises(RuntimeError) as ei:
        getattr(SciteClient(), ham)(DOI_MAU)
    assert getattr(ei.value, "loai", None) == "loi_phia_scite"
    assert 1 <= len(mang.calls) <= 2


@pytest.mark.parametrize("ma", [401, 403])
def test_auth_errors_on_public_endpoints_are_classified_and_never_answered_with_a_key(mang, ma):
    """Endpoint công khai KHÔNG cần khoá; nếu Scite đòi khoá thì báo lỗi phân loại chứ không được tự thử khoá."""
    _dat(mang, lambda url: _PhanHoi(ma, {"detail": "User not authorized"}, url))
    with pytest.raises(RuntimeError) as ei:
        SciteClient().lay_bai(DOI_MAU)
    assert getattr(ei.value, "loai", None) in VOCAB_LOI
    assert len(mang.calls) == 1, "lỗi xác thực là vĩnh viễn: không thử lại"
    assert all("authorization" not in c["headers"] for c in mang.calls)


@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
def test_valid_json_of_the_wrong_shape_is_a_malformed_response_error(mang, ham):
    _dat(mang, lambda url: _PhanHoi(200, ["khong", "phai", "object"], url))
    with pytest.raises(RuntimeError) as ei:
        getattr(SciteClient(), ham)(DOI_MAU)
    assert getattr(ei.value, "loai", None) == "phan_hoi_khong_hop_le"


@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
def test_unparseable_json_raises_a_classified_error_and_never_returns_data(mang, ham):
    _dat(mang, lambda url: _PhanHoi(200, {}, url, json_hong=True))
    with pytest.raises(RuntimeError) as ei:
        getattr(SciteClient(), ham)(DOI_MAU)
    assert getattr(ei.value, "loai", None) in VOCAB_LOI
    assert len(mang.calls) <= 2


@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
@pytest.mark.parametrize("loi", [
    pytest.param(lambda url: (_ for _ in ()).throw(requests.Timeout("Read timed out.")), id="timeout"),
    pytest.param(lambda url: (_ for _ in ()).throw(requests.ConnectionError("Max retries exceeded")), id="mat-mang"),
])
def test_transport_failures_raise_a_classified_error_never_none(mang, ham, loi):
    """Không hỏi được Scite KHÁC với "Scite không có bài này" (404 => None): lỗi vận chuyển phải nổ có phân loại."""
    _dat(mang, loi)
    with pytest.raises(RuntimeError) as ei:
        getattr(SciteClient(), ham)(DOI_MAU)
    assert getattr(ei.value, "loai", None) in VOCAB_LOI
    assert len(mang.calls) <= 2


def test_error_messages_never_carry_headers_or_secrets(mang):
    _dat(mang, lambda url: _PhanHoi(503, {"detail": "boom"}, url))
    with pytest.raises(RuntimeError) as ei:
        SciteClient().lay_bai(DOI_MAU)
    text = str(ei.value).lower()
    assert "authorization" not in text and "bearer" not in text


def test_polite_spacing_between_calls_is_small(mang):
    _dat(mang, _ok())
    client = SciteClient()
    for _ in range(3):
        client.lay_bai(DOI_MAU)
        client.lay_tally(DOI_MAU)
    assert max(mang.ngu, default=0.0) <= 5.0, f"khoảng nghỉ lịch sự phải nhỏ: {mang.ngu}"


# ════════════════════════════════════════════════════════════════════════════
# DOI được kiểm và mã hoá URL trước khi dùng
# ════════════════════════════════════════════════════════════════════════════

_DOI_HONG = [
    pytest.param("", id="rong"),
    pytest.param("   ", id="khoang-trang"),
    pytest.param("not-a-doi", id="khong-phai-doi"),
    pytest.param("10.1038", id="thieu-hau-to"),
    pytest.param("10.1038/", id="hau-to-rong"),
    pytest.param("../../etc/passwd", id="path-traversal"),
    pytest.param("10.1000/abc\ndef", id="xuong-dong"),
    pytest.param("10.1000/abc\x00def", id="byte-null"),
    pytest.param("10.1000/" + "a" * 3000, id="qua-dai"),
    pytest.param(None, id="none"),
    pytest.param(12345, id="so-nguyen"),
]


@pytest.mark.parametrize("ham", ["lay_bai", "lay_tally"])
@pytest.mark.parametrize("doi", _DOI_HONG)
def test_invalid_dois_never_produce_a_request(mang, ham, doi):
    _dat(mang, _ok())
    try:
        kq = getattr(SciteClient(), ham)(doi)
    except (RuntimeError, ValueError, TypeError):
        kq = None
    assert kq is None
    assert mang.calls == [], f"DOI không hợp lệ không được gửi đi: {mang.calls}"


_DOI_LA_HOP_LE = [
    pytest.param("10.1002/(SICI)1097-4571(199806)49:8<693::AID-ASI4>3.0.CO;2-O", id="sici-ngoac-goc"),
    pytest.param("10.1000/a?b#c", id="hoi-va-thang"),
    pytest.param("10.1000/café-über", id="unicode"),
    pytest.param("10.1000/a b", id="khoang-trang-giua"),
    pytest.param("10.1000/a%2Fb", id="phan-tram"),
]


@pytest.mark.parametrize("doi", _DOI_LA_HOP_LE)
def test_unusual_dois_are_url_encoded_and_cannot_alter_the_request_shape(mang, doi):
    _dat(mang, _ok())
    try:
        SciteClient().lay_bai(doi)
    except (RuntimeError, ValueError):
        return  # từ chối hẳn cũng chấp nhận được; điều KHÔNG được là gửi URL sai dạng
    if not mang.calls:
        return
    url = mang.calls[0]["url"]
    u = urlparse(url)
    assert u.scheme == "https" and u.hostname == "api.scite.ai"
    assert u.query == "" and u.fragment == "", f"DOI làm rò sang query/fragment: {url}"
    assert url.isascii() and not any(c in url for c in "<> \n\t\x00"), url
    assert unquote(u.path).lower() == f"/papers/{doi}".lower()


def test_a_doi_with_an_at_sign_cannot_redirect_the_request_to_another_host(mang):
    _dat(mang, _ok())
    try:
        SciteClient().lay_bai("10.1000/x@evil.example.org")
    except (RuntimeError, ValueError):
        pass
    for url in mang.urls:
        assert urlparse(url).hostname == "api.scite.ai"


@pytest.mark.parametrize("dang_nhap", [
    "https://doi.org/10.1038/nature12373",
    "doi:10.1038/nature12373",
    "  10.1038/NATURE12373  ",
])
def test_doi_prefixes_and_case_are_normalized_or_rejected_never_pasted_into_the_path(mang, dang_nhap):
    _dat(mang, _ok())
    try:
        SciteClient().lay_bai(dang_nhap)
    except (RuntimeError, ValueError):
        return
    for url in mang.urls:
        duong = unquote(urlparse(url).path).lower()
        assert duong == "/papers/10.1038/nature12373", url
