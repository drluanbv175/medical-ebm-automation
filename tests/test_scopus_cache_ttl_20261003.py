"""Hồi quy 03/10/2026: lưu đệm RIÊNG cho phản hồi Scopus (SCOPUS_CACHE_TTL).

Elsevier API Service Agreement §2.4 chỉ cho dùng API cùng hệ AI khi «không sao chép/lưu cục bộ đáng kể hoặc
có hệ thống». Engine lưu đệm mọi phản hồi HTTP 24 giờ (HTTP_CACHE_TTL). Bác sĩ quyết có tắt lưu đệm cho Scopus không —
biến này làm quyết định đó thành một dòng cấu hình. Mặc định (vắng biến) PHẢI giữ nguyên hành vi cũ."""
from __future__ import annotations

from app import config as cfg
from app.config import settings
from app.sources import scopus as sc


def test_mac_dinh_theo_http_cache_ttl(monkeypatch):
    monkeypatch.setattr(settings, "scopus_cache_ttl", None)
    assert sc.ScopusClient().http.cache_ttl == settings.http_cache_ttl, "vắng SCOPUS_CACHE_TTL phải giữ hành vi cũ"


def test_dat_0_thi_khong_luu_dem(monkeypatch):
    monkeypatch.setattr(settings, "scopus_cache_ttl", 0)
    assert sc.ScopusClient().http.cache_ttl == 0


def test_doc_bien_moi_truong(monkeypatch):
    monkeypatch.delenv("SCOPUS_CACHE_TTL", raising=False)
    assert cfg._get_int_tuy_chon("SCOPUS_CACHE_TTL") is None
    monkeypatch.setenv("SCOPUS_CACHE_TTL", "0")
    assert cfg._get_int_tuy_chon("SCOPUS_CACHE_TTL") == 0
    monkeypatch.setenv("SCOPUS_CACHE_TTL", " 3600 ")
    assert cfg._get_int_tuy_chon("SCOPUS_CACHE_TTL") == 3600
    monkeypatch.setenv("SCOPUS_CACHE_TTL", "khong-phai-so")
    assert cfg._get_int_tuy_chon("SCOPUS_CACHE_TTL") is None, "giá trị sai ⇒ theo mặc định chung"
