"""Kiểm connector BTS full-text (`app/sources/bts_guidelines.py`) — thêm 23/09/2026.

Tất cả test OFFLINE, không gọi mạng thật tới brit-thoracic.org.uk.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.bts_guidelines import BtsGuidelineFullTextClient  # noqa: E402

_URL_THAT_BTS = (
    "https://www.brit-thoracic.org.uk/document-library/guidelines/pleural-disease/"
    "bts-guideline-for-pleural-disease/"
)
_URL_DONG_XUAT_BAN_NICE = "https://www.nice.org.uk/guidance/NG245"
_URL_THORAX_BMJ = "https://thorax.bmj.com/content/74/1/1"
_URL_BMJOPENRESPRES = "https://bmjopenrespres.bmj.com/content/5/1/e000348"
_URL_DOMAIN_LA = "https://rightdecisions.scot.nhs.uk/something/"


@pytest.fixture(autouse=True)
def _bat_bts(monkeypatch):
    monkeypatch.setattr(settings, "enable_bts_guidelines_fulltext", True)
    yield


def test_bts_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_bts_guidelines_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_BTS_GUIDELINES_FULLTEXT"):
        BtsGuidelineFullTextClient()


def test_tai_toan_van_success_on_bts_domain(monkeypatch):
    client = BtsGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-1.4 gia lap")
    monkeypatch.setattr("app.sources.bts_guidelines.trich_van_ban_tu_pdf", lambda b, **kw: "noi dung")
    kq = client.tai_toan_van(_URL_THAT_BTS)
    assert kq.thanh_cong is True
    assert kq.to_chuc == "BTS"


def test_tai_toan_van_refuses_nice_url_giay_phep_ai(monkeypatch):
    """nice.org.uk ĐÃ khảo sát 23/09/2026: không bị chặn kỹ thuật, nhưng ToU đòi giấy
    phép AI trả phí — phải TỪ CHỐI mà KHÔNG gọi mạng, thông điệp nói rõ lý do pháp lý,
    KHÔNG được nói 'chưa khảo sát' (đã khảo sát xong, kết luận không xây được)."""
    client = BtsGuidelineFullTextClient()
    goi_mang = []
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: goi_mang.append(url) or b"")
    kq = client.tai_toan_van(_URL_DONG_XUAT_BAN_NICE)
    assert kq.thanh_cong is False
    assert goi_mang == []  # KHÔNG được gọi mạng
    assert "nice.org.uk" in kq.ghi_chu.lower()
    assert "giấy phép" in kq.ghi_chu.lower() or "ai" in kq.ghi_chu.lower()
    assert "chưa khảo sát" not in kq.ghi_chu.lower()


@pytest.mark.parametrize("url", [_URL_THORAX_BMJ, _URL_BMJOPENRESPRES])
def test_tai_toan_van_refuses_cloudflare_domain_without_network_call(monkeypatch, url):
    """thorax.bmj.com/bmjopenrespres.bmj.com ĐÃ khảo sát 23/09/2026: chặn bởi
    Cloudflare Managed Challenge — phải TỪ CHỐI mà KHÔNG gọi mạng, thông điệp nêu
    đúng 'Cloudflare', không nói chung chung 'chưa khảo sát'."""
    client = BtsGuidelineFullTextClient()
    goi_mang = []
    monkeypatch.setattr(client.http, "get_bytes", lambda u, **kw: goi_mang.append(u) or b"")
    kq = client.tai_toan_van(url)
    assert kq.thanh_cong is False
    assert goi_mang == []  # KHÔNG được gọi mạng
    assert "cloudflare" in kq.ghi_chu.lower()
    assert "chưa khảo sát" not in kq.ghi_chu.lower()


def test_tai_toan_van_refuses_truly_unsurveyed_domain(monkeypatch):
    """Domain KHÔNG thuộc 3 nhóm đã khảo sát (BTS/Cloudflare/NICE) vẫn phải từ chối
    với thông điệp 'chưa khảo sát' — hành vi cũ, chưa đổi."""
    client = BtsGuidelineFullTextClient()
    goi_mang = []
    monkeypatch.setattr(client.http, "get_bytes", lambda u, **kw: goi_mang.append(u) or b"")
    kq = client.tai_toan_van(_URL_DOMAIN_LA)
    assert kq.thanh_cong is False
    assert goi_mang == []
    assert "chưa khảo sát" in kq.ghi_chu.lower()


def test_tai_toan_van_non_pdf_response_reported_clearly(monkeypatch):
    client = BtsGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"<html>404</html>")
    kq = client.tai_toan_van(_URL_THAT_BTS)
    assert kq.thanh_cong is False
    assert "%pdf" in kq.ghi_chu.lower() or "pdf" in kq.ghi_chu.lower()


def test_tai_toan_van_network_error_returns_failure_not_raise(monkeypatch):
    client = BtsGuidelineFullTextClient()

    def _loi(*a, **kw):
        raise ConnectionError("mat mang")

    monkeypatch.setattr(client.http, "get_bytes", _loi)
    kq = client.tai_toan_van(_URL_THAT_BTS)
    assert kq.thanh_cong is False


def test_tai_toan_van_extraction_failure_reported(monkeypatch):
    client = BtsGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-gia-lap")
    monkeypatch.setattr("app.sources.bts_guidelines.trich_van_ban_tu_pdf", lambda b, **kw: "")
    kq = client.tai_toan_van(_URL_THAT_BTS)
    assert kq.thanh_cong is False
