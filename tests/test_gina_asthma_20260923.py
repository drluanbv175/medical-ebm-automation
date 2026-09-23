"""Kiểm connector GINA full-text (`app/sources/gina_asthma.py`) — thêm 23/09/2026.

Tất cả test OFFLINE, không gọi mạng thật tới ginasthma.org.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.gina_asthma import GinaAsthmaFullTextClient  # noqa: E402


@pytest.fixture(autouse=True)
def _bat_gina(monkeypatch):
    monkeypatch.setattr(settings, "enable_gina_asthma_fulltext", True)
    yield


_HTML_TRANG_MUC_LUC_MAU = """
<html><body>
<a href="https://ginasthma.org/wp-content/uploads/2026/05/GINA-2026-Strategy-Report-WMS.pdf">2026 Strategy Report</a>
</body></html>
"""


def test_gina_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_gina_asthma_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_GINA_ASTHMA_FULLTEXT"):
        GinaAsthmaFullTextClient()


def test_gina_client_enforces_10_second_crawl_delay():
    """robots.txt của ginasthma.org đòi Crawl-delay: 10 — kiểm client TRUYỀN đúng
    cấu hình cho HttpClient, không kiểm hành vi ngủ thật (tốn thời gian test)."""
    client = GinaAsthmaFullTextClient()
    assert client.http.min_interval == 10.0


def test_tim_url_bao_cao_moi_nhat_returns_matching_link(monkeypatch):
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: _HTML_TRANG_MUC_LUC_MAU)
    url = client.tim_url_bao_cao_moi_nhat()
    assert url == "https://ginasthma.org/wp-content/uploads/2026/05/GINA-2026-Strategy-Report-WMS.pdf"


def test_tim_url_bao_cao_moi_nhat_returns_none_when_no_link_matches(monkeypatch):
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: "<html>khong co gi</html>")
    assert client.tim_url_bao_cao_moi_nhat() is None


def test_tai_toan_van_pdf_success(monkeypatch):
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-1.4 gia lap")
    monkeypatch.setattr("app.sources.gina_asthma.trich_van_ban_tu_pdf", lambda b, **kw: "noi dung")
    kq = client.tai_toan_van_pdf(url="https://ginasthma.org/x.pdf")
    assert kq.thanh_cong is True
    assert kq.to_chuc == "GINA"


def test_tai_toan_van_pdf_detects_non_pdf_response_as_policy_change_not_network_error(monkeypatch):
    """Đây là luật riêng của GINA (khác GOLD): GINA từng tạm đóng truy cập miễn phí,
    phản hồi không phải PDF thật (thiếu chữ ký %PDF) phải báo RÕ nghi đổi chính sách,
    KHÔNG được gộp chung với lỗi mạng."""
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"<html>Please subscribe</html>")
    kq = client.tai_toan_van_pdf(url="https://ginasthma.org/x.pdf")
    assert kq.thanh_cong is False
    assert "chính sách truy cập" in kq.ghi_chu.lower()


def test_tai_toan_van_pdf_network_error_message_differs_from_policy_change_message(monkeypatch):
    client = GinaAsthmaFullTextClient()

    def _loi(*a, **kw):
        raise ConnectionError("mat mang that su")

    monkeypatch.setattr(client.http, "get_bytes", _loi)
    kq = client.tai_toan_van_pdf(url="https://ginasthma.org/x.pdf")
    assert kq.thanh_cong is False
    assert "mat mang" in kq.ghi_chu.lower()
    assert "chính sách truy cập" not in kq.ghi_chu.lower()


def test_tai_toan_van_pdf_extraction_failure_reported(monkeypatch):
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-gia-lap")
    monkeypatch.setattr("app.sources.gina_asthma.trich_van_ban_tu_pdf", lambda b, **kw: "")
    kq = client.tai_toan_van_pdf(url="https://ginasthma.org/x.pdf")
    assert kq.thanh_cong is False
