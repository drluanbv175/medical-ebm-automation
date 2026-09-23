"""Kiểm connector GOLD full-text (`app/sources/gold_copd.py`) — thêm 23/09/2026.

Tất cả test OFFLINE: mock `client.http.get_text`/`get_bytes` và
`guideline_fulltext_common.trich_van_ban_tu_pdf` — KHÔNG gọi mạng thật tới
goldcopd.org, đúng quy ước `tests/test_scopus.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.gold_copd import TRANG_MUC_LUC, GoldCopdFullTextClient  # noqa: E402


@pytest.fixture(autouse=True)
def _bat_gold(monkeypatch):
    monkeypatch.setattr(settings, "enable_gold_copd_fulltext", True)
    yield


_HTML_TRANG_MUC_LUC_MAU = """
<html><body>
<h2>2026</h2>
<a href="https://goldcopd.org/wp-content/uploads/2026/01/GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf">GOLD 2026 Report</a>
<h2>2025</h2>
<a href="https://goldcopd.org/wp-content/uploads/2024/11/GOLD-2025-Report-v1.0-15Nov2024_WMV.pdf">GOLD 2025 Report</a>
</body></html>
"""


def test_gold_raises_when_flag_not_enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_gold_copd_fulltext", False)
    with pytest.raises(RuntimeError, match="ENABLE_GOLD_COPD_FULLTEXT"):
        GoldCopdFullTextClient()


def test_tim_url_bao_cao_moi_nhat_returns_first_matching_link(monkeypatch):
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: _HTML_TRANG_MUC_LUC_MAU)
    url = client.tim_url_bao_cao_moi_nhat()
    assert url == "https://goldcopd.org/wp-content/uploads/2026/01/GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf"


# HTML thật đo được từ goldcopd.org/archived-reports/ 23/09/2026 — mỗi năm liệt kê
# báo cáo đầy đủ (văn bản hiển thị KHÔNG chứa "GOLD") RỒI MỚI tới Pocket Guide (văn
# bản hiển thị CÓ chứa "GOLD"). Kiểm sống lần đầu lấy nhầm Pocket Guide — xem docstring
# module "LỖI ĐÃ VÁ 23/09/2026".
_URL_BAO_CAO_DAY_DU = (
    "https://goldcopd.org/wp-content/uploads/2024/11/"
    "GOLD-2025-Report-v1.0-15Nov2024_WMV.pdf"
)
_URL_POCKET_GUIDE = (
    "https://goldcopd.org/wp-content/uploads/2024/12/"
    "Pocket-Guide-2025-v1.2-FINAL-covered-13Dec2024_WMV.pdf"
)
_HTML_TRANG_MUC_LUC_THAT = f"""
<html><body>
<a href="{_URL_BAO_CAO_DAY_DU}">2025 Global Strategy for Prevention, Diagnosis
and Management of COPD</a>
<a href="{_URL_POCKET_GUIDE}">2025 GOLD Pocket Guide</a>
</body></html>
"""


def test_tim_url_bao_cao_moi_nhat_bo_qua_pocket_guide_lay_bao_cao_day_du(monkeypatch):
    """Hồi quy cho lỗi kiểm sống 23/09/2026: phải lấy báo cáo ĐẦY ĐỦ, KHÔNG lấy nhầm
    Pocket Guide dù Pocket Guide là link duy nhất có chữ "GOLD" trong văn bản hiển thị."""
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: _HTML_TRANG_MUC_LUC_THAT)
    url = client.tim_url_bao_cao_moi_nhat()
    assert url == _URL_BAO_CAO_DAY_DU
    assert "pocket" not in url.lower()


def test_tim_url_bao_cao_moi_nhat_returns_none_when_no_link_matches(monkeypatch):
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: "<html><body>khong co gi</body></html>")
    assert client.tim_url_bao_cao_moi_nhat() is None


def test_tim_url_bao_cao_moi_nhat_returns_none_on_network_error(monkeypatch):
    client = GoldCopdFullTextClient()

    def _loi(*a, **kw):
        raise ConnectionError("gia lap mat mang")

    monkeypatch.setattr(client.http, "get_text", _loi)
    assert client.tim_url_bao_cao_moi_nhat() is None


def test_tai_toan_van_pdf_success_with_explicit_url(monkeypatch):
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-1.4 gia lap")
    monkeypatch.setattr(
        "app.sources.gold_copd.trich_van_ban_tu_pdf", lambda pdf_bytes, **kw: "noi dung trich duoc"
    )
    kq = client.tai_toan_van_pdf(url="https://goldcopd.org/x.pdf")
    assert kq.thanh_cong is True
    assert kq.van_ban_trich == "noi dung trich duoc"
    assert kq.to_chuc == "GOLD"


def test_tai_toan_van_pdf_auto_discovers_url_when_none_given(monkeypatch):
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: _HTML_TRANG_MUC_LUC_MAU)
    goi_url = {}

    def _gia_lap_get_bytes(url, **kw):
        goi_url["url"] = url
        return b"%PDF-gia-lap"

    monkeypatch.setattr(client.http, "get_bytes", _gia_lap_get_bytes)
    monkeypatch.setattr("app.sources.gold_copd.trich_van_ban_tu_pdf", lambda b, **kw: "abc")
    kq = client.tai_toan_van_pdf()
    assert kq.thanh_cong is True
    assert "GOLD-REPORT-2026" in goi_url["url"]


def test_tai_toan_van_pdf_fails_cleanly_when_url_not_found(monkeypatch):
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_text", lambda url, **kw: "<html></html>")
    kq = client.tai_toan_van_pdf()
    assert kq.thanh_cong is False
    assert kq.url_nguon == TRANG_MUC_LUC
    assert "không tìm thấy" in kq.ghi_chu.lower() or "cần xác nhận" in kq.ghi_chu.lower()


def test_tai_toan_van_pdf_download_error_returns_failure_not_raise(monkeypatch):
    client = GoldCopdFullTextClient()

    def _loi(*a, **kw):
        raise ConnectionError("mat mang khi tai pdf")

    monkeypatch.setattr(client.http, "get_bytes", _loi)
    kq = client.tai_toan_van_pdf(url="https://goldcopd.org/x.pdf")
    assert kq.thanh_cong is False
    assert "mat mang" in kq.ghi_chu.lower()


def test_tai_toan_van_pdf_extraction_failure_is_reported_not_hidden(monkeypatch):
    client = GoldCopdFullTextClient()
    monkeypatch.setattr(client.http, "get_bytes", lambda url, **kw: b"%PDF-gia-lap")
    monkeypatch.setattr("app.sources.gold_copd.trich_van_ban_tu_pdf", lambda b, **kw: "")
    kq = client.tai_toan_van_pdf(url="https://goldcopd.org/x.pdf")
    assert kq.thanh_cong is False
    assert "không trích được văn bản" in kq.ghi_chu.lower()
