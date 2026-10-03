"""Hồi quy 03/10/2026: ENABLE_SCOPUS=false phải chặn MỌI lối gọi Scopus thật, không chỉ tầng chọn nguồn.

Bác sĩ đặt ENABLE_SCOPUS=false để tạm dừng làn Scopus (chờ quyết điều kiện Elsevier API Service Agreement §2.4).
`get_enabled_sources()` và bộ quét giám sát đã xét cờ, nhưng `ScopusClient.search()` thì không — lối gọi thẳng client
(`run.py test-live scopus`, mã gọi `ScopusClient().search(...)`) vẫn gọi API thật (đã xảy ra 11:13 ngày 03/10).
`tools/do_mang_nguon.py --co-scopus` cũng chỉ xét có khoá. Offline hoàn toàn: mọi lối ra mạng bị thay bằng hàm GHI LẠI
lời gọi (không dựa vào ném lỗi — connector nuốt Exception quanh get_json nên lỗi ném ra sẽ bị che thành «[]»)."""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, List

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.main as main_mod  # noqa: E402
from app.config import settings  # noqa: E402
from app.sources.scopus import ScopusClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils.http import HttpClient  # noqa: E402

DONG_LOG = "[scopus] ENABLE_SCOPUS=false — không gọi API (bác sĩ tạm dừng)"


@pytest.fixture(autouse=True)
def _co_lap(monkeypatch, tmp_path):
    """Khoá giả, tắt proxy khoá; cache HTTP về tmp_path (`_CACHE_DIR` chốt lúc import, phải vá riêng)."""
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    (tmp_path / "http_cache").mkdir()
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    monkeypatch.setattr(settings, "scopus_api_key", "KHOA_GIA_SCOPUS")
    monkeypatch.setattr(settings, "scopus_insttoken", "")
    monkeypatch.setattr(settings, "scopus_bind_interface", "")
    monkeypatch.setattr(settings, "khoa_qua_proxy", "")
    yield


@pytest.fixture
def goi_mang(monkeypatch) -> List[Any]:
    """Thay MỌI lối ra mạng (HttpClient._request + requests.Session.request) bằng hàm ghi lại lời gọi."""
    goi: List[Any] = []

    def ghi_http(self, method, url, *a, **kw):
        goi.append(("HttpClient", method, url))
        return {"search-results": {"entry": []}}

    def ghi_requests(self, method, url, *a, **kw):
        goi.append(("requests", method, url))
        raise requests.exceptions.ConnectionError("test không được rời máy")

    monkeypatch.setattr(HttpClient, "_request", ghi_http)
    monkeypatch.setattr(requests.Session, "request", ghi_requests)
    return goi


# ═════════════ 1. ScopusClient.search() ═════════════

def test_co_tat_thi_khong_goi_mang_va_tra_rong(monkeypatch, goi_mang, caplog):
    monkeypatch.setattr(settings, "enable_scopus", False)
    caplog.set_level(logging.INFO, logger="app.sources.scopus")
    c = ScopusClient()
    c.use_mock = False
    assert c.search("atrial fibrillation") == []
    assert goi_mang == [], "cờ tắt mà vẫn gọi API Scopus thật"
    assert DONG_LOG in caplog.text
    assert c.ly_do_khong_goi and "ENABLE_SCOPUS=false" in c.ly_do_khong_goi


def test_co_tat_thieu_khoa_khong_no(monkeypatch, goi_mang):
    """Cờ tắt là ý định của bác sĩ, không phải cấu hình sai — chốt cờ đứng TRƯỚC chốt thiếu khoá."""
    monkeypatch.setattr(settings, "enable_scopus", False)
    monkeypatch.setattr(settings, "scopus_api_key", "")
    c = ScopusClient()
    c.use_mock = False
    assert c.search("atrial fibrillation") == []
    assert goi_mang == []


@pytest.mark.parametrize("co", [False, True])
def test_che_do_mock_giu_nguyen_du_co_bat_hay_tat(monkeypatch, goi_mang, co):
    monkeypatch.setattr(settings, "enable_scopus", co)
    c = ScopusClient()
    c.use_mock = True
    recs = c.search("atrial fibrillation", clinical_area="Tim mạch")
    assert recs and all(r.source == "scopus" and r.raw.get("_mock") for r in recs)
    assert goi_mang == []
    assert c.ly_do_khong_goi is None


def test_doi_chung_co_bat_live_van_goi_dung_mot_lan(monkeypatch, goi_mang):
    """Đối chứng: chốt không được chặn quá tay khi cờ BẬT."""
    monkeypatch.setattr(settings, "enable_scopus", True)
    c = ScopusClient()
    c.use_mock = False
    assert c.search("atrial fibrillation") == []
    assert [g[2] for g in goi_mang] == ["https://api.elsevier.com/content/search/scopus"]
    assert c.ly_do_khong_goi is None


def test_doi_chung_co_bat_thieu_khoa_van_no_nhu_cu(monkeypatch, goi_mang):
    monkeypatch.setattr(settings, "enable_scopus", True)
    monkeypatch.setattr(settings, "scopus_api_key", "")
    c = ScopusClient()
    c.use_mock = False
    with pytest.raises(RuntimeError, match="SCOPUS_API_KEY"):
        c.search("atrial fibrillation")
    assert goi_mang == []


# ═════════════ 2. run.py test-live scopus (cmd_test_live) ═════════════

def test_test_live_scopus_co_tat_khong_goi_va_noi_ro(monkeypatch, goi_mang):
    monkeypatch.setattr(main_mod, "_SOURCE_MAP", {})  # cùng lệ test_cmd_test_live_trung_thuc_20260924
    monkeypatch.setattr(settings, "enable_scopus", False)
    out = main_mod.cmd_test_live("scopus", "heart failure", limit=3)
    assert goi_mang == [], "test-live scopus vẫn gọi API thật dù cờ tắt"
    assert out["count"] == 0
    assert out["live"] is False, "không gọi API thì không được báo «live: true»"
    assert "ENABLE_SCOPUS=false" in out["ghi_chu"] and "KHÔNG phải kết quả đo" in out["ghi_chu"]


# ═════════════ 3. tools/do_mang_nguon.py --co-scopus ═════════════

def _cong_cu():
    spec = importlib.util.spec_from_file_location("do_mang_nguon_co_tat", ROOT / "tools" / "do_mang_nguon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Cfg:
    ncbi_email = "nguoi@example.org"
    scopus_api_key = "KHOA_GIA_SCOPUS"
    enable_scopus = False


def _goi_gia(goi: List[str]):
    class _PhanHoi:
        status_code = 200
        text = "ok"

        def __init__(self, url: str) -> None:
            self.url = url

    def goi_gia(url, params, headers):
        goi.append(url)
        return _PhanHoi(url), None
    return goi_gia


def test_do_mang_co_tat_khong_dua_diem_scopus():
    mod = _cong_cu()
    ten = [d[0] for d in mod.danh_sach_diem(_Cfg(), co_scopus=True)]
    assert not any("Scopus" in t for t in ten)
    assert mod.ly_do_bo_scopus(_Cfg()) == "ENABLE_SCOPUS=false"


def test_do_mang_thieu_thuoc_tinh_co_coi_nhu_tat():
    """Fail-closed: không chắc cờ bật thì không tốn hạn mức tổ chức."""
    class _CfgCu:
        scopus_api_key = "KHOA_GIA_SCOPUS"
    mod = _cong_cu()
    assert not any("elsevier" in d[2] for d in mod.danh_sach_diem(_CfgCu(), co_scopus=True))


def test_do_mang_co_bat_va_xin_thi_moi_do():
    class _CfgBat(_Cfg):
        enable_scopus = True
    mod = _cong_cu()
    assert any("elsevier" in d[2] for d in mod.danh_sach_diem(_CfgBat(), co_scopus=True))
    assert not any("elsevier" in d[2] for d in mod.danh_sach_diem(_CfgBat(), co_scopus=False))


def test_do_mang_co_tat_khong_goi_va_ghi_ly_do(monkeypatch):
    mod = _cong_cu()
    monkeypatch.setattr(mod, "dau_van_mang", lambda: {"qua_vpn": True})
    goi: List[str] = []
    kq = mod.do(_Cfg(), co_scopus=True, goi=_goi_gia(goi))
    assert goi and not any("elsevier" in u for u in goi)
    assert kq["bo_qua"] == {"Scopus": "ENABLE_SCOPUS=false"}
    assert "bo_qua" not in mod.do(_Cfg(), co_scopus=False, goi=_goi_gia([])), "không xin Scopus thì không ghi bỏ qua"


@pytest.mark.parametrize("che_do_json", [False, True])
def test_do_mang_main_in_dong_bo_qua(monkeypatch, capsys, che_do_json):
    mod = _cong_cu()
    monkeypatch.setattr(settings, "enable_scopus", False)
    monkeypatch.setattr(mod, "dau_van_mang", lambda: {"qua_vpn": True})
    goi: List[str] = []
    goc = mod.do
    monkeypatch.setattr(mod, "do", lambda cfg, co_scopus=False: goc(cfg, co_scopus, goi=_goi_gia(goi)))
    assert mod.main(["--co-scopus"] + (["--json"] if che_do_json else [])) == 0
    ra = capsys.readouterr()
    assert not any("elsevier" in u for u in goi)
    if che_do_json:
        assert "bỏ qua Scopus: ENABLE_SCOPUS=false" in ra.err
        assert json.loads(ra.out)["bo_qua"] == {"Scopus": "ENABLE_SCOPUS=false"}, "stdout phải còn là JSON hợp lệ"
    else:
        assert "bỏ qua Scopus: ENABLE_SCOPUS=false" in ra.out
