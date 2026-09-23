"""Kiểm connector PMC full-text (`app/sources/pmc_guideline_fulltext.py`) — thêm
23/09/2026. Tất cả test OFFLINE, không gọi mạng thật tới pmc.ncbi.nlm.nih.gov.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.pmc_guideline_fulltext import PmcGuidelineFullTextClient  # noqa: E402

_HTML_TRANG_BAI_MAU = """
<html><body>
<a href="/articles/PMC12690171/pdf/dc26s001.pdf">Download PDF</a>
</body></html>
"""


@pytest.fixture(autouse=True)
def _bat_pmc(monkeypatch):
    monkeypatch.setattr(settings, "enable_pmc_guideline_fulltext", True)
    yield


def test_pmc_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_pmc_guideline_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_PMC_GUIDELINE_FULLTEXT"):
        PmcGuidelineFullTextClient()


def test_pmc_client_enforces_1_second_crawl_delay():
    """robots.txt của pmc.ncbi.nlm.nih.gov đòi Crawl-delay: 1."""
    client = PmcGuidelineFullTextClient()
    assert client.http.min_interval == 1.0


def test_tai_toan_van_normalizes_pmcid_without_prefix(monkeypatch):
    client = PmcGuidelineFullTextClient()
    goi_url = {}

    def _gia_lap_get_text(url, **kw):
        goi_url["trang"] = url
        return _HTML_TRANG_BAI_MAU

    monkeypatch.setattr(client.http, "get_text", _gia_lap_get_text)
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-1.4 gia lap")
    monkeypatch.setattr("app.sources.pmc_guideline_fulltext.trich_van_ban_tu_pdf", lambda b, **kw: "noi dung")

    kq = client.tai_toan_van("12690171")  # KHÔNG có tiền tố "PMC"
    assert kq.thanh_cong is True
    assert "PMC12690171" in goi_url["trang"]


def test_tai_toan_van_rejects_invalid_pmcid_format_without_network_call(monkeypatch):
    client = PmcGuidelineFullTextClient()
    goi_mang = []
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: goi_mang.append(url) or "")
    kq = client.tai_toan_van("khong-phai-pmcid")
    assert kq.thanh_cong is False
    assert goi_mang == []


def test_tai_toan_van_returns_failure_when_pdf_link_not_found(monkeypatch):
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: "<html>khong co link pdf</html>")
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False
    assert "pdf" in kq.ghi_chu.lower()


def test_tai_toan_van_page_fetch_error_returns_failure_not_raise(monkeypatch):
    client = PmcGuidelineFullTextClient()

    def _loi(*a, **kw):
        raise ConnectionError("mat mang")

    monkeypatch.setattr(client.http, "get_text", _loi)
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False


def test_tai_toan_van_pdf_download_error_returns_failure(monkeypatch):
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: _HTML_TRANG_BAI_MAU)

    def _loi(*a, **kw):
        raise ConnectionError("mat mang khi tai pdf")

    monkeypatch.setattr(client.http, "get_bytes", _loi)
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False


def test_tai_toan_van_extraction_failure_reported(monkeypatch):
    client = PmcGuidelineFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: _HTML_TRANG_BAI_MAU)
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-gia-lap")
    monkeypatch.setattr("app.sources.pmc_guideline_fulltext.trich_van_ban_tu_pdf", lambda b, **kw: "")
    kq = client.tai_toan_van("PMC12690171")
    assert kq.thanh_cong is False
