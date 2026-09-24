"""Hồi quy vá 24/09/2026 — `app/main.py::cmd_test_live()` phải NÓI THẬT về chế độ đã chạy.

Đo thật trên phiên Cloud (không có ~/.ebm-secrets): `run.py test-live pubmed` ép
`use_mock=False` nhưng `PubMedClient.search()` vẫn tự lùi về dữ liệu minh hoạ khi thiếu
NCBI_EMAIL, và đầu ra cũ ghi «live: true, count: 2» — ai chỉ đọc hai trường đó sẽ tưởng
PubMed đang chạy thật. Cùng lúc, 7 nguồn bị proxy môi trường chặn trả «count: 0» câm: lý do
chỉ nằm trong log, không nằm trong JSON mà bác sĩ được dặn đọc (CLAUDE.md: «kiểm is_mock,
count»). Hai test dưới đây khoá cả hai chiều; không gọi mạng thật."""
from __future__ import annotations

import pytest
import requests

import app.main as main_mod
from app.config import settings
from app.main import cmd_test_live


@pytest.fixture(autouse=True)
def _cache_ban_do_nguon_rieng(monkeypatch):
    """`_build_source_map()` lưu class connector vào dict CẤP MODULE. Để nguyên, file này (chạy
    sớm theo thứ tự chữ cái) giữ class cũ trong cache, và test ở file khác tải lại
    `app.sources.consensus_api` sau đó sẽ so danh tính class lệch nhau (đo thật: 1 đỏ ở
    test_fallback_ladder khi chạy trọn bộ). Mỗi test ở đây dùng dict riêng, trả lại dict gốc khi xong."""
    monkeypatch.setattr(main_mod, "_SOURCE_MAP", {})


def test_ban_ghi_mock_thi_live_la_false_kem_canh_bao(monkeypatch):
    monkeypatch.setattr(settings, "ncbi_email", "")  # đúng tình trạng máy thiếu secrets

    def khong_duoc_goi_mang(*a, **kw):
        raise AssertionError("nhánh thiếu email không được gọi mạng")

    monkeypatch.setattr(requests.Session, "request", khong_duoc_goi_mang)
    out = cmd_test_live("pubmed", "heart failure", limit=5)
    assert out["count"] >= 1, "kho minh hoạ phải có mục khớp 'heart failure' để ca này có nghĩa"
    assert all(r["is_mock"] for r in out["results"])
    assert out["live"] is False
    assert out["so_ban_ghi_mock"] == out["count"]
    assert "mock" in out["canh_bao"] and "NCBI_EMAIL" in out["canh_bao"]


def test_loi_mang_bi_nuot_thanh_rong_duoc_noi_ra(monkeypatch):
    def proxy_tu_choi(self, method, url, **kw):
        raise requests.exceptions.ProxyError(
            "HTTPSConnectionPool(host='www.ebi.ac.uk', port=443): Max retries exceeded "
            "(Caused by ProxyError('Unable to connect to proxy', "
            "OSError('Tunnel connection failed: 403 Forbidden')))")

    monkeypatch.setattr(requests.Session, "request", proxy_tu_choi)
    out = cmd_test_live("europepmc", "heart failure guideline", limit=3)
    assert out["count"] == 0
    assert out["live"] is True  # không có bản ghi mock nào — chỉ là không lấy được gì
    assert "loi_goi_mang" in out and "chính sách" in out["loi_goi_mang"]
    assert "www.ebi.ac.uk" in out["loi_goi_mang"]
