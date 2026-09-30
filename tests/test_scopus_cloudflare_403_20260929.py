"""Scopus bị Cloudflare chặn theo IP mạng (VPN) không được làm mọi lượt thành PARTIAL (29/09/2026).

Bác sĩ chọn phương án a «ghi chú, không chặn»: VPN BẬT là mặc định (NCBI chạy) nên api.elsevier.com trả trang chặn
Cloudflare (403, `server: cloudflare`, `cf-ray`, thân HTML có `cf-error-details`/«Cloudflare Ray ID» — đo thật
29/09, giống hệt cho khoá đúng lẫn khoá sai). Chỉ miễn khi MỌI lỗi của Scopus là 403 kèm trang chặn Cloudflare VÀ
PubMed/Europe PMC/Crossref còn khoẻ; 401 (khoá sai), 403 JSON của chính Elsevier, mất mạng… vẫn PARTIAL.
Offline hoàn toàn: phiên HTTP giả, không mở socket.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.services.ingestion import _fetch, summarize_source_health  # noqa: E402
from app.sources.scopus import ScopusClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils.http import DAU_CLOUDFLARE_CHAN, HttpClient  # noqa: E402

TRANG_CHAN = ("<!DOCTYPE html><title>Attention Required! | Cloudflare</title>"
              "<div id=\"cf-error-details\"><h1>Sorry, you have been blocked</h1>"
              "<span>Cloudflare Ray ID: <strong>8c1f0a2b3d4e5f60</strong></span></div>")
TIEU_DE_CF = {"Server": "cloudflare", "CF-RAY": "8c1f0a2b3d4e5f60-SIN", "Content-Type": "text/html; charset=UTF-8"}
LOI_ELSEVIER = '{"service-error":{"status":{"statusCode":"AUTHORIZATION_ERROR"}}}'


class _PhanHoi:
    def __init__(self, status_code: int, text: str = "", headers: Any = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = {} if headers is None else headers
        self.url = "https://api.elsevier.com/content/search/scopus"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error: Forbidden for url: {self.url}")

    def json(self) -> Any:
        return {"search-results": {"entry": []}}


class _PhienGia:
    def __init__(self, phan_hoi: _PhanHoi) -> None:
        self.phan_hoi = phan_hoi

    def request(self, method, url, params=None, timeout=None, **extra):
        return self.phan_hoi


@pytest.fixture(autouse=True)
def _khong_ngu_that(monkeypatch):
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: None)


def _goi(phan_hoi: _PhanHoi) -> HttpClient:
    client = HttpClient(cache_ttl=0, min_interval=0)
    client.session = _PhienGia(phan_hoi)
    with pytest.raises(requests.HTTPError):
        client.get_json("https://api.elsevier.com/content/search/scopus", params={"query": "x"})
    return client


# ---------- Tầng HttpClient: gắn dấu ĐÚNG trang chặn Cloudflare, không gắn nhầm ----------

def test_trang_chan_cloudflare_duoc_gan_dau_o_dau_chuoi():
    loi = _goi(_PhanHoi(403, TRANG_CHAN, TIEU_DE_CF)).health_snapshot()["last_error"]
    assert loi.startswith(DAU_CLOUDFLARE_CHAN + " ") and "403 Client Error" in loi


def test_dau_con_nguyen_khi_url_dai_bi_cat_500_ky_tu():
    ph = _PhanHoi(403, TRANG_CHAN, TIEU_DE_CF)
    ph.url += "?query=" + "a" * 900
    loi = _goi(ph).last_error
    assert len(loi) == 500 and loi.startswith(DAU_CLOUDFLARE_CHAN)


def test_loi_json_cua_elsevier_sau_cloudflare_khong_bi_gan_dau():
    """Elsevier đứng sau Cloudflare nên MỌI phản hồi có `cf-ray` — chỉ tiêu đề thì chưa đủ."""
    loi = _goi(_PhanHoi(403, LOI_ELSEVIER, {"Server": "cloudflare", "CF-RAY": "x"})).last_error
    assert DAU_CLOUDFLARE_CHAN not in loi and "403 Client Error" in loi


def test_than_giong_cloudflare_nhung_khong_qua_cloudflare_khong_bi_gan_dau():
    loi = _goi(_PhanHoi(403, TRANG_CHAN, {"Server": "nginx"})).last_error
    assert DAU_CLOUDFLARE_CHAN not in loi


def test_phan_hoi_thieu_truong_khong_lam_hong_duong_bao_loi():
    class _Thieu(_PhanHoi):
        headers = property(lambda self: (_ for _ in ()).throw(RuntimeError("không có tiêu đề")))
    ph = _Thieu.__new__(_Thieu)
    ph.status_code, ph.text, ph.url = 403, TRANG_CHAN, "https://api.elsevier.com/x"
    assert DAU_CLOUDFLARE_CHAN not in _goi(ph).last_error


def test_trang_403_cua_may_chu_goc_co_script_jsd_khong_bi_gan_dau():
    """Phản biện 29/09: JS Detections của Cloudflare chèn `/cdn-cgi/challenge-platform/…/jsd/main.js` vào MỌI trang
    HTML đi qua nó — trang 403 «khoá không có quyền» của chính máy chủ nguồn không được thành «bị chặn»."""
    than = ("<html><title>403 Forbidden</title><p>The requested APIKey is invalid or not entitled</p>"
            "<script src=\"/cdn-cgi/challenge-platform/scripts/jsd/main.js\"></script></html>")
    assert DAU_CLOUDFLARE_CHAN not in _goi(_PhanHoi(403, than, TIEU_DE_CF)).last_error


def test_trang_thach_thuc_nhan_qua_tieu_de_cf_mitigated():
    tieu_de = {**TIEU_DE_CF, "cf-mitigated": "challenge"}
    assert _goi(_PhanHoi(403, "<title>Just a moment...</title>", tieu_de)).last_error.startswith(DAU_CLOUDFLARE_CHAN)


def test_trang_loi_5xx_cua_cloudflare_khong_phai_bi_chan():
    """521/522… (máy chủ nguồn sập) cũng có «Cloudflare Ray ID» nhưng không phải bị chặn theo mạng."""
    assert DAU_CLOUDFLARE_CHAN not in _goi(_PhanHoi(521, TRANG_CHAN, TIEU_DE_CF)).last_error


# ---------- Trọn chuỗi thật: ScopusClient → _fetch → summarize_source_health ----------

def _row(src, st="ok", n=5, err=None):
    return {"source": src, "status": st, "record_count": n, "error_message": err}


LOI_KHAM_PHA = ["pubmed", "europepmc", "crossref"]
API = LOI_KHAM_PHA + ["scopus"]


def _suc_khoe(scopus_rows, extra=(), bo=()):
    logs = [_row(s) for s in LOI_KHAM_PHA if s not in bo] + list(scopus_rows) + list(extra)
    return summarize_source_health(logs, expected_api_sources=API + [r["source"] for r in extra],
                                   expected_feed_sources=[], safety_enabled=False)


def test_scopus_that_bi_cloudflare_chan_qua_fetch_la_pass_kem_ghi_chu(monkeypatch):
    monkeypatch.setattr(settings, "scopus_api_key", "KHOA_GIA_TEST")
    monkeypatch.setattr(settings, "scopus_insttoken", "")
    monkeypatch.setattr(settings, "scopus_bind_interface", "")
    client = ScopusClient()
    client.use_mock = False
    client.http.cache_ttl = 0
    client.http.min_interval = 0
    client.http.session = _PhienGia(_PhanHoi(403, TRANG_CHAN, TIEU_DE_CF))
    rows = [_fetch(client, "heart failure", "tim_mach", 5)[1] for _ in range(3)]
    assert all(r["status"] == "error" and r["error_message"].startswith(DAU_CLOUDFLARE_CHAN) for r in rows)
    assert "KHOA_GIA_TEST" not in " ".join(r["error_message"] for r in rows)
    h = _suc_khoe(rows)
    assert h["status"] == "PASS", h["warnings"]
    assert "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP" in h["mirror_notices"]
    assert h["optional_enhanced_failed"] == ["scopus"]           # sự thật «hỏng 100%» vẫn ghi
    assert h["optional_enhanced_blocked_by_cloudflare"] == ["scopus"]
    assert h["sources"]["scopus"]["error_http_403_cloudflare"] == 3


CF_403 = f"{DAU_CLOUDFLARE_CHAN} HTTPError: 403 Client Error: Forbidden for url: https://api.elsevier.com/x"


def test_scopus_401_khoa_sai_van_partial():
    h = _suc_khoe([_row("scopus", "error", 0, "HTTPError: 401 Client Error: Unauthorized for url: x")])
    assert h["status"] == "PARTIAL" and "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus" in h["warnings"]


def test_scopus_401_du_co_dau_cloudflare_van_partial():
    h = _suc_khoe([_row("scopus", "error", 0, f"{DAU_CLOUDFLARE_CHAN} HTTPError: 401 Client Error: x")])
    assert h["status"] == "PARTIAL" and h["optional_enhanced_blocked_by_cloudflare"] == []


def test_scopus_403_json_cua_elsevier_van_partial():
    h = _suc_khoe([_row("scopus", "error", 0, "HTTPError: 403 Client Error: Forbidden for url: x")])
    assert h["status"] == "PARTIAL" and not any(n.startswith("SCOPUS_") for n in h["mirror_notices"])


def test_scopus_lan_cloudflare_va_mat_mang_van_partial():
    h = _suc_khoe([_row("scopus", "error", 0, CF_403),
                   _row("scopus", "error", 0, "RuntimeError: Gọi API thất bại sau 4 lần: x")])
    assert h["status"] == "PARTIAL"


def test_dau_khong_o_dau_chuoi_khong_duoc_tinh():
    """Chỉ `HttpClient` gắn dấu, và luôn ở ĐẦU chuỗi — dấu nằm giữa thông điệp khác (vd lỗi bọc lại) không tính."""
    h = _suc_khoe([_row("scopus", "error", 0, f"RuntimeError: bọc lại {DAU_CLOUDFLARE_CHAN} HTTPError: 403 "
                                              "Client Error: x")])
    assert h["status"] == "PARTIAL" and h["sources"]["scopus"]["error_http_403_cloudflare"] == 0


def test_cloudflare_nhung_pubmed_hong_van_partial():
    """PubMed hỏng mà Europe PMC + Crossref còn thì PubMed được gương — nhưng miễn Scopus đòi ĐỦ cả ba lõi."""
    h = _suc_khoe([_row("scopus", "error", 0, CF_403)], extra=[_row("pubmed", "error", 0, "x")], bo=("pubmed",))
    assert h["status"] == "PARTIAL" and "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus" in h["warnings"]


def test_core_bi_cloudflare_chan_khong_duoc_mien():
    h = _suc_khoe([_row("core", "error", 0, CF_403)])
    assert h["status"] == "PARTIAL" and "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:core" in h["warnings"]


def test_scopus_cloudflare_va_core_hong_chi_canh_bao_core():
    h = _suc_khoe([_row("scopus", "error", 0, CF_403)], extra=[_row("core", "error", 0, "x")])
    assert h["status"] == "PARTIAL"
    assert "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:core" in h["warnings"]
    assert "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP" in h["mirror_notices"]


def test_pubmed_suy_giam_giua_luot_khong_du_de_mien():
    """Phản biện 30/09: NCBI chặn giữa lượt ⇒ PubMed 1 thành công + 3 lỗi (health «degraded», được gương Europe PMC/
    Crossref). Trước bản vá: Scopus vẫn được miễn ⇒ PASS dù hai nguồn cùng hỏng; bản gốc ra PARTIAL."""
    pubmed = [_row("pubmed")] + [_row("pubmed", "error", 0, "RuntimeError: NCBI đã CHẶN") for _ in range(3)]
    h = _suc_khoe([_row("scopus", "error", 0, CF_403)], extra=pubmed, bo=("pubmed",))
    assert h["sources"]["pubmed"]["health"] == "degraded"
    assert h["status"] == "PARTIAL" and "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus" in h["warnings"]
    assert "SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP" not in h["mirror_notices"]


def test_chi_bat_pubmed_khong_du_de_mien():
    """Miễn đòi ĐỦ cả ba nguồn lõi — máy tắt Europe PMC/Crossref thì PubMed một mình không đủ bù (phản biện 29/09)."""
    logs = [_row("pubmed"), _row("scopus", "error", 0, CF_403)]
    h = summarize_source_health(logs, expected_api_sources=["pubmed", "scopus"],
                                expected_feed_sources=[], safety_enabled=False)
    assert h["status"] == "PARTIAL" and h["optional_enhanced_blocked_by_cloudflare"] == []


def test_khong_nguon_loi_nao_duoc_bat_khong_mien():
    h = summarize_source_health([_row("openalex"), _row("scopus", "error", 0, CF_403)],
                                expected_api_sources=["openalex", "scopus"], expected_feed_sources=[],
                                safety_enabled=False)
    assert "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus" in h["warnings"]


def test_epistemonikos_bi_cloudflare_chan_khong_duoc_mien():
    h = _suc_khoe([_row("scopus")], extra=[_row("epistemonikos", "error", 0, CF_403)])
    assert h["status"] == "PARTIAL" and "OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:epistemonikos" in h["warnings"]
