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


def test_tai_toan_van_refuses_url_on_different_domain_without_network_call(monkeypatch):
    """Một số hướng dẫn BTS đồng xuất bản trỏ sang nice.org.uk — domain đó CHƯA được
    khảo sát robots.txt/ToU, phải TỪ CHỐI mà KHÔNG gọi mạng."""
    client = BtsGuidelineFullTextClient()
    goi_mang = []
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: goi_mang.append(url) or b"")
    kq = client.tai_toan_van(_URL_DONG_XUAT_BAN_NICE)
    assert kq.thanh_cong is False
    assert goi_mang == []  # KHÔNG được gọi mạng
    assert "nice.org.uk" in kq.ghi_chu.lower()


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
