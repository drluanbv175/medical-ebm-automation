"""Hồi quy 20/10/2026: dự phòng openFDA trả lời hợp lệ «0 thu hồi» không được ghi thành lỗi nguồn.

Lượt giám sát tuần 19/10/2026 kết thúc FAIL: RSS thu hồi thuốc của FDA bị chặn 401 ⇒ lùi sang openFDA
drug/enforcement. Đo thật cùng ngày: cửa sổ từ 10/10/2026 ⇒ HTTP 404 + {"error": {"code": "NOT_FOUND",
"message": "No matches found!"}} (báo cáo mới nhất 07/10/2026 — FDA công bố theo tuần); cửa sổ từ 01/09
⇒ 200 với 93 bản ghi. Mã cũ đếm câu trả lời «0 kết quả» đó là lỗi ⇒ feed_fda_recalls «unavailable» ⇒
nguồn an toàn BẮT BUỘC suy giảm ⇒ PARTIAL ⇒ cầu nối Hub bị chặn oan. OFFLINE.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.services.ingestion import _fetch, summarize_source_health  # noqa: E402
from app.sources.feeds import DRUG_SAFETY_FEEDS  # noqa: E402
from app.sources.rss_feed import RSSFeedClient  # noqa: E402


def _loi_http(ma: int, than: str) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = ma
    resp._content = than.encode("utf-8")
    return requests.HTTPError(f"{ma} Client Error", response=resp)


class _Http:
    """RSS bị chặn 401 (đếm lỗi như HttpClient); openFDA ném lỗi do test chọn (cũng đếm lỗi như HttpClient)."""

    def __init__(self, loi_openfda: Exception):
        self.loi_openfda = loi_openfda
        self.snap = {"request_count": 0, "success_count": 0, "failure_count": 0, "transient_failure_count": 0,
                     "cache_hit_count": 0, "last_error": "", "last_status_code": None}

    def health_snapshot(self):
        return dict(self.snap)

    def get_text(self, url, **kw):
        self.snap["failure_count"] += 1
        self.snap["last_error"] = "HTTPError: 401 Client Error: Unauthorized"
        raise RuntimeError("401 Client Error: Unauthorized")

    def get_json(self, url, params=None, **kw):
        self.snap["failure_count"] += 1
        self.snap["last_error"] = str(self.loi_openfda)
        raise self.loi_openfda


@pytest.fixture(autouse=True)
def _khong_khoa(monkeypatch):
    monkeypatch.setattr(settings, "openfda_api_key", "")


def _client(loi, monkeypatch, fid="fda_recalls"):
    c = RSSFeedClient(next(f for f in DRUG_SAFETY_FEEDS if f.id == fid))
    monkeypatch.setattr(c, "use_mock", False)
    c.http = _Http(loi)
    return c


KHONG_KHOP = '{"error": {"code": "NOT_FOUND", "message": "No matches found!"}}'


def test_404_not_found_dat_co_du_phong_tra_loi_rong(monkeypatch):
    c = _client(_loi_http(404, KHONG_KHOP), monkeypatch)
    assert c.search(max_results=5, since_date="2026-10-10") == []
    assert c.du_phong_tra_loi_rong == "openfda_enforcement"


@pytest.mark.parametrize("loi", [_loi_http(500, "{}"), _loi_http(404, "<html>Not Found</html>"),
                                 _loi_http(400, '{"error": {"code": "BAD_REQUEST"}}'), RuntimeError("mất mạng")])
def test_loi_khac_khong_dat_co(monkeypatch, loi):
    c = _client(loi, monkeypatch)
    assert c.search(max_results=5, since_date="2026-10-10") == []
    assert c.du_phong_tra_loi_rong is None


def test_co_dat_lai_moi_luot_search(monkeypatch):
    c = _client(_loi_http(404, KHONG_KHOP), monkeypatch)
    c.search(max_results=5, since_date="2026-10-10")
    c.http.loi_openfda = _loi_http(500, "{}")
    c.search(max_results=5, since_date="2026-10-10")
    assert c.du_phong_tra_loi_rong is None  # cờ của lượt trước không được lan sang lượt sau


def test_fetch_ghi_du_phong_khong_ghi_loi(monkeypatch):
    _recs, log = _fetch(_client(_loi_http(404, KHONG_KHOP), monkeypatch), "", "An toàn thuốc", 5,
                        since_date="2026-10-10")
    assert log["status"] == "degraded" and log["record_count"] == 0
    assert log["error_message"].startswith("du_phong:openfda_enforcement trả lời 0 mục")


def test_fetch_loi_that_van_la_loi(monkeypatch):
    _recs, log = _fetch(_client(_loi_http(500, "{}"), monkeypatch), "", "An toàn thuốc", 5, since_date="2026-10-10")
    assert log["status"] == "error"


def test_tong_hop_luot_tuan_pass_kem_ghi_chu(monkeypatch):
    """Đúng tình huống 19/10: MedWatch bị chặn (đã miễn), thu hồi FDA qua dự phòng 0 mục, openFDA + MHRA khoẻ ⇒ PASS."""
    _recs, log = _fetch(_client(_loi_http(404, KHONG_KHOP), monkeypatch), "", "An toàn thuốc", 5,
                        since_date="2026-10-10")
    logs = [log, {"source": "openfda", "status": "ok", "record_count": 5},
            {"source": "feed_mhra_dsu", "status": "ok", "record_count": 3}]
    r = summarize_source_health(logs, expected_api_sources=["openfda"],
                                expected_feed_sources=["feed_fda_recalls", "feed_mhra_dsu"], safety_enabled=True)
    assert r["status"] == "PASS" and r["degraded_required_sources"] == []
    assert "FEED_FDA_RECALLS_SERVED_BY_OFFICIAL_FALLBACK" in r["mirror_notices"]


def test_co_mang_ten_du_phong_chua_khai_van_la_loi(monkeypatch):
    c = _client(_loi_http(500, "{}"), monkeypatch)
    real_search = c.search

    def search(*a, **k):
        out = real_search(*a, **k)
        c.du_phong_tra_loi_rong = "nguon_chua_khai"  # chỉ dự phòng đã khai trong _VIA_DU_PHONG mới được miễn
        return out
    c.search = search
    _recs, log = _fetch(c, "", "An toàn thuốc", 5, since_date="2026-10-10")
    assert log["status"] == "error"
