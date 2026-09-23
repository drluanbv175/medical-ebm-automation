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


# HTML thật đo được từ ginasthma.org/reports/ 23/09/2026: trang mục lục CHỈ liệt kê
# link LANDING theo năm, KHÔNG có .pdf trực tiếp — xem "LỖI ĐÃ VÁ 23/09/2026" ở
# docstring module gina_asthma.py.
_HTML_TRANG_MUC_LUC_MAU = """
<html><body>
<a href="https://ginasthma.org/2026-gina-strategy-report/">2026 GINA Strategy Report</a>
<a href="https://ginasthma.org/2026-gina-summary-guide/">2026 GINA Summary Guide</a>
</body></html>
"""

# HTML thật đo được từ trang landing https://ginasthma.org/2026-gina-strategy-report/.
_HTML_TRANG_LANDING_MAU = """
<html><body>
<a href="https://ginasthma.org/wp-content/uploads/2026/05/GINA-2026-Strategy-Report-WMS.pdf">Download</a>
</body></html>
"""


def _dieu_huong_gia_lap(url, **kw):
    """Giả lập điều hướng 2 bước: trang mục lục -> trang landing."""
    if url == "https://ginasthma.org/2026-gina-strategy-report/":
        return _HTML_TRANG_LANDING_MAU
    return _HTML_TRANG_MUC_LUC_MAU


def test_gina_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_gina_asthma_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_GINA_ASTHMA_FULLTEXT"):
        GinaAsthmaFullTextClient()


def test_gina_client_enforces_10_second_crawl_delay():
    """robots.txt của ginasthma.org đòi Crawl-delay: 10 — kiểm client TRUYỀN đúng
    cấu hình cho HttpClient, không kiểm hành vi ngủ thật (tốn thời gian test)."""
    client = GinaAsthmaFullTextClient()
    assert client.http.min_interval == 10.0


def test_tim_url_bao_cao_moi_nhat_returns_matching_link_qua_hai_buoc(monkeypatch):
    """Hồi quy cho lỗi kiểm sống 23/09/2026: trang mục lục KHÔNG có .pdf trực tiếp,
    phải đi qua trang landing mới lấy được link PDF thật."""
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_text", _dieu_huong_gia_lap)
    url = client.tim_url_bao_cao_moi_nhat()
    assert url == "https://ginasthma.org/wp-content/uploads/2026/05/GINA-2026-Strategy-Report-WMS.pdf"


def test_tim_url_bao_cao_moi_nhat_returns_none_when_no_landing_link_matches(monkeypatch):
    client = GinaAsthmaFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: "<html>khong co gi</html>")
    assert client.tim_url_bao_cao_moi_nhat() is None


def test_tim_url_bao_cao_moi_nhat_returns_none_when_landing_page_has_no_pdf(monkeypatch):
    client = GinaAsthmaFullTextClient()

    def _landing_rong(url, **kw):
        if url == "https://ginasthma.org/2026-gina-strategy-report/":
            return "<html>trang landing khong co pdf</html>"
        return _HTML_TRANG_MUC_LUC_MAU

    monkeypatch.setattr(client.http, "get_text", _landing_rong)
    assert client.tim_url_bao_cao_moi_nhat() is None


def test_tim_url_bao_cao_moi_nhat_returns_none_on_landing_page_network_error(monkeypatch):
    client = GinaAsthmaFullTextClient()

    def _loi_landing(url, **kw):
        if url == "https://ginasthma.org/2026-gina-strategy-report/":
            raise ConnectionError("mat mang khi tai trang landing")
        return _HTML_TRANG_MUC_LUC_MAU

    monkeypatch.setattr(client.http, "get_text", _loi_landing)
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
