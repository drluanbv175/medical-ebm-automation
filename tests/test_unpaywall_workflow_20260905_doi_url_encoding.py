"""Hồi quy phát hiện LOW của Workflow đối kháng đa-agent 2026-09-04 (vòng 2,
task #74): `app/sources/unpaywall.py::UnpaywallClient.oa_url_for_doi()` — DOI
được ghép THẲNG vào path URL bằng f-string, không URL-encode.

CƠ CHẾ LỖI (xác nhận bằng thực nghiệm trước khi vá, dùng
`requests.Request(...).prepare().url` — cách `HttpClient` trong repo này
thực sự gửi request qua thư viện `requests`):
  - DOI chứa "#" → `requests` hiểu là URL FRAGMENT, phần sau "#" bị CẮT KHỎI
    request thật gửi đi (tra nhầm DOI bị cụt mà không có lỗi nào báo ra).
  - DOI chứa "?" → bị gộp lẫn vào query string, va chạm với
    `params={"email": ...}` được nối riêng.
DOI theo DOI Handbook có thể chứa bất kỳ ký tự Unicode in được (kể cả "#",
"?", khoảng trắng) ở phần hậu tố — hiếm nhưng có thật ở một số nhà xuất bản.

BẢN VÁ: `urllib.parse.quote(doi, safe="/")` — thoát mọi ký tự có thể phá cấu
trúc URL, GIỮ NGUYÊN dấu "/" nội tại của DOI (khác
`crossref_retraction.py::_lay()` dùng `safe=""` vì API Crossref coi TOÀN BỘ
DOI là một đoạn path duy nhất, còn API Unpaywall v2 giữ dấu "/" ở dạng
thường theo tài liệu chính thức của họ — copy y hệt mẫu `safe=""` của
Crossref sẽ làm hỏng MỌI DOI hợp lệ bình thường vì Unpaywall không mong đợi
dấu "/" bị mã hoá thành %2F).

Nguyên tắc viết test: monkeypatch `client.http.get_json` để bắt URL thật đã
được xây dựng, gọi THẲNG `oa_url_for_doi()` — không grep chuỗi trong mã
nguồn; kèm một test tích hợp dùng `requests.Request(...).prepare().url` để
chứng minh URL sau khi vá KHÔNG còn bị requests hiểu sai cấu trúc.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.unpaywall import BASE, UnpaywallClient  # noqa: E402


def _client(monkeypatch) -> tuple[UnpaywallClient, dict]:
    import app.config as cfg
    monkeypatch.setattr(cfg.settings, "unpaywall_email", "test@example.com", raising=False)
    c = UnpaywallClient()
    c.use_mock = False
    goi_url: dict = {}

    def _fake_get_json(url, params=None, use_cache=True):
        goi_url["url"] = url
        goi_url["params"] = params
        return {"best_oa_location": {"url": "https://example.org/pdf"}}

    monkeypatch.setattr(c.http, "get_json", _fake_get_json)
    return c, goi_url


class TestDoiCoKyTuNguyHiemDuocMaHoa:
    """★★ Ca chính — DOI chứa "#"/"?"/khoảng trắng phải được mã hoá trước khi
    ghép vào path, không còn nguyên văn trong URL gửi tới HttpClient."""

    def test_doi_co_dau_thang_khong_con_nguyen_van(self, monkeypatch):
        client, goi = _client(monkeypatch)
        client.oa_url_for_doi("10.1000/xyz#123")
        assert "#123" not in goi["url"]
        assert "%23123" in goi["url"]

    def test_doi_co_dau_hoi_khong_con_nguyen_van(self, monkeypatch):
        client, goi = _client(monkeypatch)
        client.oa_url_for_doi("10.1000/xyz?foo=bar")
        assert "?foo=bar" not in goi["url"]
        assert "%3Ffoo%3Dbar" in goi["url"]

    def test_doi_co_khoang_trang_duoc_ma_hoa(self, monkeypatch):
        client, goi = _client(monkeypatch)
        client.oa_url_for_doi("10.1000/xyz abc")
        assert " " not in goi["url"]
        assert "%20" in goi["url"]


class TestDoiBinhThuongGiuNguyenDauGachCheo:
    """Đối chứng bắt buộc — DOI bình thường (một dấu "/" giữa tiền tố/hậu
    tố, đúng hình dạng phổ biến nhất) phải GIỮ NGUYÊN dấu "/", không bị mã
    hoá thành %2F — khác `crossref_retraction.py`, API Unpaywall giữ "/" ở
    dạng thường."""

    def test_doi_binh_thuong_giu_nguyen_dau_gach_cheo(self, monkeypatch):
        client, goi = _client(monkeypatch)
        client.oa_url_for_doi("10.1038/nature12373")
        assert goi["url"] == f"{BASE}/10.1038/nature12373"
        assert "%2F" not in goi["url"]

    def test_doi_nhieu_dau_gach_cheo_van_giu_nguyen(self, monkeypatch):
        """DOI hậu tố có thêm dấu "/" bên trong (có thật ở một số nhà xuất
        bản) — cả hai đều phải giữ nguyên literal."""
        client, goi = _client(monkeypatch)
        client.oa_url_for_doi("10.1000/abc/def")
        assert goi["url"] == f"{BASE}/10.1000/abc/def"

    def test_ket_qua_tra_ve_khong_doi(self, monkeypatch):
        client, _goi = _client(monkeypatch)
        assert client.oa_url_for_doi("10.1038/nature12373") == "https://example.org/pdf"


class TestUrlSauKhiVaKhongBiRequestsHieuSai:
    """★★ Ca tích hợp — URL sau khi vá, đưa qua chính cơ chế `requests` dùng
    thật (PreparedRequest), không còn bị cắt cụt ở "#" hay gộp lẫn ở "?"."""

    def test_url_da_ma_hoa_khong_bi_cat_o_dau_thang(self, monkeypatch):
        client, goi = _client(monkeypatch)
        client.oa_url_for_doi("10.1000/xyz#123")
        prepped = requests.Request("GET", goi["url"], params=goi["params"]).prepare()
        assert "xyz%23123" in prepped.url
