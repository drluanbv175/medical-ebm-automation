"""Hồi quy 24/09/2026 — KHOA_QUA_PROXY: dùng được tính năng «API credentials» của môi trường Cloud.

Trên Cloud, agent proxy gắn khoá vào HEADER request sau khi request rời sandbox; engine không bao giờ
thấy khoá. Trước bản vá, connector thấy biến khoá rỗng liền tự chặn («thiếu …_API_KEY») nên tính năng
đó vô dụng. Các test không gọi mạng: `client.http.get_json` được thay bằng hàm ghi lại lời gọi."""
from __future__ import annotations

import logging

import pytest

from app.config import khoa_do_proxy_gan, settings
from app.sources.core_api import CoreClient
from app.sources.epistemonikos import EpistemonikosClient
from app.sources.scopus import ScopusClient


@pytest.fixture(autouse=True)
def _sach(monkeypatch):
    for k in ("scopus_api_key", "scopus_insttoken", "scopus_bind_interface", "core_api_key",
              "epistemonikos_api_token", "khoa_qua_proxy"):
        monkeypatch.setattr(settings, k, "")


def _song(client, monkeypatch, tra_ve):
    client.use_mock = False
    goi = []

    def gia(url, params=None, **kw):
        goi.append((url, params))
        return tra_ve

    monkeypatch.setattr(client.http, "get_json", gia)
    return goi


def test_khai_bao_chi_nhan_nguon_gui_khoa_qua_header(monkeypatch):
    monkeypatch.setattr(settings, "khoa_qua_proxy", " Scopus , core,serpapi_scholar,pubmed ")
    assert khoa_do_proxy_gan("scopus") and khoa_do_proxy_gan("core")
    # SerpApi/NCBI gửi khoá qua tham số URL ⇒ proxy không gắn được ⇒ khai vào cũng vô hiệu
    assert not khoa_do_proxy_gan("serpapi_scholar") and not khoa_do_proxy_gan("pubmed")
    assert not khoa_do_proxy_gan("consensus")  # không khai thì không nhận


def test_scopus_qua_proxy_khong_tu_chan_va_khong_gui_header_rong(monkeypatch):
    monkeypatch.setattr(settings, "khoa_qua_proxy", "scopus")
    c = ScopusClient()
    assert "X-ELS-APIKey" not in c.http.session.headers, "không được gửi header khoá rỗng — proxy tự gắn"
    goi = _song(c, monkeypatch, {"search-results": {"entry": []}})
    assert c.search("atrial fibrillation") == []
    assert len(goi) == 1, "khai qua proxy thì phải gọi thật, không chặn vì thiếu khoá"


def test_scopus_khong_khai_proxy_van_chan_nhu_cu(monkeypatch):
    c = ScopusClient()
    goi = _song(c, monkeypatch, {})
    with pytest.raises(RuntimeError, match="SCOPUS_API_KEY"):
        c.search("atrial fibrillation")
    assert goi == []


def test_epistemonikos_qua_proxy_khong_tu_chan(monkeypatch):
    monkeypatch.setattr(settings, "khoa_qua_proxy", "epistemonikos")
    c = EpistemonikosClient()
    assert "Authorization" not in c.http.session.headers
    goi = _song(c, monkeypatch, {"search_info": {"total_hits": 0}, "results": []})
    c.search("heart failure")
    assert len(goi) == 1


def test_epistemonikos_khong_khai_proxy_van_chan(monkeypatch):
    c = EpistemonikosClient()
    _song(c, monkeypatch, {})
    with pytest.raises(RuntimeError, match="EPISTEMONIKOS_API_TOKEN"):
        c.search("heart failure")


def test_core_qua_proxy_khong_canh_bao_thieu_khoa(monkeypatch, caplog):
    monkeypatch.setattr(settings, "khoa_qua_proxy", "core")
    c = CoreClient()
    assert "Authorization" not in c.http.session.headers
    _song(c, monkeypatch, {"results": []})
    caplog.set_level(logging.WARNING)
    c.search("heart failure")
    assert "thiếu CORE_API_KEY" not in caplog.text
