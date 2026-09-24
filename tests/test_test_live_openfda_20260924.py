"""Hồi quy 24/09/2026 — `run.py test-live openfda` báo sai «lỗi mạng» khi openFDA trả 404 NOT_FOUND.

Đo thật trên Cloud: truy vấn mặc định «atrial fibrillation guideline 2024» không phải tên thuốc ⇒
openFDA trả 404 «No matches found», bị báo thành `loi_goi_mang` kèm
`khoa_api_openfda: co nhung chua goi duoc lan nao`. Bản vá:
  1. truy vấn mặc định THEO NGUỒN (openfda: «metformin»);
  2. 404 NOT_FOUND = 0 kết quả, không phải lỗi mạng;
  3. 404 NOT_FOUND khi CÓ khoá ⇒ khoá đã được FDA chấp nhận.
Ngoại tuyến hoàn toàn: HttpClient giả, không gọi api.fda.gov.
"""
from __future__ import annotations

import pytest
import requests

import app.main as M
from app.config import settings
from app.sources import openfda as ofda
from app.sources.openfda import OpenFDAClient, get_json_openfda, la_404_khong_khop

KHOA = "KHOA_GIA_DE_TEST_0123456789"


def _loi(ma: int, than: bytes) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = ma
    resp.url = "https://api.fda.gov/drug/event.json"
    resp._content = than
    return requests.HTTPError(f"{ma} Client Error", response=resp)


NOT_FOUND = b'{"error": {"code": "NOT_FOUND", "message": "No matches found!"}}'


class _Http:
    def __init__(self, loi: Exception | None = None, tra_ve: dict | None = None):
        self.loi = loi
        self.tra_ve = tra_ve or {"results": []}
        self.cac_lan: list = []
        self.last_error = ""

    def get_json(self, url, params=None, use_cache=True):
        self.cac_lan.append(dict(params or {}))
        if self.loi is not None:
            self.last_error = f"HTTPError: {self.loi}"
            raise self.loi
        return self.tra_ve


@pytest.fixture(autouse=True)
def _sach(monkeypatch):
    monkeypatch.setattr(ofda, "trang_thai_khoa", None)


def _client(http) -> OpenFDAClient:
    c = OpenFDAClient()
    c.http = http
    c.save_raw = lambda *a, **k: None
    return c


def _dung_map(monkeypatch, http, ghi: dict | None = None):
    def factory():
        c = _client(http)
        if ghi is not None:
            goc = c.search

            def search(query, **kw):
                ghi["query"] = query
                return goc(query, **kw)

            c.search = search
        return c

    monkeypatch.setattr(M, "_build_source_map", lambda: {"openfda": factory, "europepmc": factory})


# ── Nhận diện 404 NOT_FOUND ──────────────────────────────────────────────────

def test_nhan_dien_404_not_found():
    assert la_404_khong_khop(_loi(404, NOT_FOUND)) is True
    assert la_404_khong_khop(_loi(404, b"<html>Not Found</html>")) is False
    assert la_404_khong_khop(_loi(404, b'{"error": {"code": "OTHER"}}')) is False
    assert la_404_khong_khop(_loi(500, NOT_FOUND)) is False
    assert la_404_khong_khop(RuntimeError("x")) is False


# ── Truy vấn mặc định theo nguồn ─────────────────────────────────────────────

def test_truy_van_mac_dinh_openfda_la_ten_thuoc():
    assert M.truy_van_test_live_mac_dinh("openfda") == "metformin"
    assert M.truy_van_test_live_mac_dinh("europepmc") == "atrial fibrillation guideline 2024"


def test_cmd_test_live_khong_go_tu_khoa_dung_mac_dinh_theo_nguon(monkeypatch):
    monkeypatch.setattr(settings, "openfda_api_key", "")
    ghi: dict = {}
    _dung_map(monkeypatch, _Http(tra_ve={"results": [{"term": "NAUSEA", "count": 3}]}), ghi)
    out = M.cmd_test_live("openfda")
    assert ghi["query"] == "metformin"
    assert out["query"] == "metformin"
    assert out["count"] == 1


# ── 404 NOT_FOUND = 0 kết quả, không phải lỗi mạng ──────────────────────────

def test_search_404_not_found_la_khong_khop():
    c = _client(_Http(loi=_loi(404, NOT_FOUND)))
    c.use_mock = False
    assert c.search("atrial fibrillation guideline 2024") == []
    assert c.khong_khop is True
    c.http = _Http(tra_ve={"results": []})
    c.search("metformin")
    assert c.khong_khop is False  # đặt lại mỗi lần search


def test_search_loi_khac_khong_phai_khong_khop():
    c = _client(_Http(loi=_loi(500, b"{}")))
    c.use_mock = False
    assert c.search("metformin") == []
    assert c.khong_khop is False


def test_cmd_test_live_404_khong_bao_loi_mang_va_khoa_chap_nhan(monkeypatch):
    monkeypatch.setattr(settings, "openfda_api_key", KHOA)
    _dung_map(monkeypatch, _Http(loi=_loi(404, NOT_FOUND)))
    out = M.cmd_test_live("openfda", "atrial fibrillation guideline 2024")
    assert "loi_goi_mang" not in out
    assert "404 NOT_FOUND" in out["ghi_chu"]
    assert out["count"] == 0
    assert out["khoa_api_openfda"] == "co — FDA CHAP NHAN"
    assert KHOA not in str(out)


def test_cmd_test_live_loi_that_van_bao_loi_mang(monkeypatch):
    monkeypatch.setattr(settings, "openfda_api_key", "")
    _dung_map(monkeypatch, _Http(loi=_loi(503, b"{}")))
    out = M.cmd_test_live("openfda", "metformin")
    assert "loi_goi_mang" in out
    assert "ghi_chu" not in out


def test_helper_404_not_found_co_khoa_van_raise_cho_noi_goi():
    """drug_interactions dựa vào 404 để thử trường kế — không được nuốt."""
    settings_khoa = settings.openfda_api_key
    try:
        settings.openfda_api_key = KHOA
        with pytest.raises(requests.HTTPError):
            get_json_openfda(_Http(loi=_loi(404, NOT_FOUND)), ofda.EVENT, {"search": "x"})
        assert ofda.trang_thai_khoa == "chap_nhan"
    finally:
        settings.openfda_api_key = settings_khoa
