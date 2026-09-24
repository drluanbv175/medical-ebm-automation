"""Hồi quy 24/09/2026: connector GOLD phải lấy báo cáo NĂM HIỆN HÀNH, không chỉ `archived-reports/`.

Đo sống 24/09: `archived-reports/` chỉ liệt kê bản CŨ (mới nhất GOLD-2025 v1.0), còn GOLD 2026 v1.3
nằm ở trang `/2026-gold-report-and-pocket-guide/` do trang chủ trỏ tới ⇒ bản cũ của connector trả
GOLD-2025. HTML dưới đây rút gọn đúng cấu trúc thật đo được hôm đó. OFFLINE, không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.gold_copd import TRANG_CHU, TRANG_MUC_LUC, GoldCopdFullTextClient  # noqa: E402

TRANG_2026 = "https://goldcopd.org/2026-gold-report-and-pocket-guide/"
PDF_2026 = "https://goldcopd.org/wp-content/uploads/2026/01/GOLD-REPORT-2026-v1.3-8Dec2025_WMV2.pdf"
PDF_KEY = "https://goldcopd.org/wp-content/uploads/2025/11/KEY-CHANGES-GOLD-2026-10Nov2025.pdf"
PDF_2025 = "https://goldcopd.org/wp-content/uploads/2024/11/GOLD-2025-Report-v1.0-15Nov2024_WMV.pdf"

_TRANG_CHU = f"""<html><body>
<a href="https://goldcopd.org/purchase-gold-reports/">Mua</a>
<a href="https://goldcopd.org/2025-gold-report/">2025</a>
<a href="{TRANG_2026}">2026 GOLD Report</a>
</body></html>"""
_TRANG_2026 = f"""<html><body>
<a href="{PDF_KEY}">2026 Summary of Changes</a>
<a href="{PDF_2026}"></a>
<a href="https://goldcopd.org/wp-content/uploads/2026/01/GOLD-Pocket-Guide-2026-v1.1-20Nov2025_WMV2.pdf"></a>
</body></html>"""
_TRANG_2025 = f'<html><body><a href="{PDF_2025}">GOLD 2025</a></body></html>'
_ARCHIVED = f'<html><body><a href="{PDF_2025}">GOLD 2025 Report</a></body></html>'


@pytest.fixture(autouse=True)
def _bat_gold(monkeypatch):
    monkeypatch.setattr(settings, "enable_gold_copd_fulltext", True)
    yield


def _gia_lap(monkeypatch, client, trang: dict):
    def _get_text(url, **kw):
        if url not in trang:
            raise RuntimeError(f"không có mạng giả cho {url}")
        return trang[url]
    monkeypatch.setattr(client.http, "get_text", _get_text)


def test_lay_bao_cao_nam_hien_hanh_khong_phai_ban_luu_tru(monkeypatch):
    c = GoldCopdFullTextClient()
    _gia_lap(monkeypatch, c, {TRANG_CHU: _TRANG_CHU, TRANG_2026: _TRANG_2026,
                              "https://goldcopd.org/2025-gold-report/": _TRANG_2025,
                              TRANG_MUC_LUC: _ARCHIVED})
    assert c.tim_url_bao_cao_moi_nhat() == PDF_2026


def test_bo_qua_ban_tom_tat_thay_doi_va_pocket_guide(monkeypatch):
    c = GoldCopdFullTextClient()
    _gia_lap(monkeypatch, c, {TRANG_CHU: _TRANG_CHU, TRANG_2026: _TRANG_2026})
    url = c.tim_url_bao_cao_moi_nhat()
    assert "KEY-CHANGES" not in url and "Pocket" not in url


def test_trang_chu_loi_thi_lui_ve_archived(monkeypatch):
    c = GoldCopdFullTextClient()
    _gia_lap(monkeypatch, c, {TRANG_MUC_LUC: _ARCHIVED})
    assert c.tim_url_bao_cao_moi_nhat() == PDF_2025


def test_trang_nam_hien_hanh_khong_co_pdf_thi_lui_ve_archived(monkeypatch):
    c = GoldCopdFullTextClient()
    _gia_lap(monkeypatch, c, {TRANG_CHU: _TRANG_CHU, TRANG_2026: "<html></html>",
                              TRANG_MUC_LUC: _ARCHIVED})
    assert c.tim_url_bao_cao_moi_nhat() == PDF_2025
