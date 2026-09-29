"""Dự phòng CHÍNH THỨC có bản ghi thật không được ghi thành «error» (29/09/2026).

Đo thật: feed thu hồi FDA bị www.fda.gov chặn (401) ⇒ rss_feed lùi openFDA drug/enforcement, trả 5 bản ghi thật,
nhưng `_fetch` vẫn ghi status «error» (bộ đếm lỗi HttpClient của lần gọi RSS) ⇒ nguồn «unavailable» ⇒ mọi lượt
PARTIAL — trái ý định audit/15 #6 (chỉ MedWatch báo lỗi thật). Offline, không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ingestion import _fetch, summarize_source_health  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402


class _Http:
    def __init__(self):
        self.snap = {"request_count": 0, "success_count": 0, "failure_count": 0,
                     "transient_failure_count": 0, "cache_hit_count": 0, "last_error": "", "last_status_code": None}

    def health_snapshot(self):
        return dict(self.snap)


class _Client:
    name = "feed_fda_recalls"
    endpoint = "x"
    use_mock = False

    def __init__(self, vias, loi_chinh=True):
        self.http = _Http()
        self.vias, self.loi_chinh = vias, loi_chinh

    def search(self, query, **kw):
        if self.loi_chinh:
            self.http.snap["failure_count"] += 1
            self.http.snap["last_error"] = "HTTPError: 401 Client Error: Unauthorized"
        self.http.snap["success_count"] += 1
        return [RawRecord(source=self.name, title=f"t{i}", raw=({"_via": v} if v else {}))
                for i, v in enumerate(self.vias)]


def test_toan_bo_ban_ghi_tu_du_phong_la_degraded_co_danh_dau():
    _recs, log = _fetch(_Client(["openfda_enforcement"] * 3), "", "An toàn thuốc", 5)
    assert log["status"] == "degraded" and log["record_count"] == 3
    assert log["error_message"].startswith("du_phong:openfda_enforcement")


def test_loi_nguon_chinh_khong_ban_ghi_van_error():
    _recs, log = _fetch(_Client([]), "", "An toàn thuốc", 5)
    assert log["status"] == "error"


def test_ban_ghi_lan_via_khac_van_error():
    _recs, log = _fetch(_Client(["openfda_enforcement", None]), "", "An toàn thuốc", 5)
    assert log["status"] == "error"


def test_via_crossref_issn_khong_phai_du_phong():
    _recs, log = _fetch(_Client(["crossref_issn"]), "", "x", 5)
    assert log["status"] == "error"


def test_khong_loi_nguon_chinh_thi_ok():
    _recs, log = _fetch(_Client(["openfda_enforcement"], loi_chinh=False), "", "x", 5)
    assert log["status"] == "ok" and log["error_message"] is None


def test_tong_hop_pass_kem_ghi_chu_co_ten():
    _recs, log = _fetch(_Client(["openfda_enforcement"] * 2), "", "An toàn thuốc", 5)
    logs = [log, {"source": "openfda", "status": "ok", "record_count": 5},
            {"source": "feed_mhra_dsu", "status": "ok", "record_count": 3}]
    r = summarize_source_health(logs, expected_api_sources=["openfda"],
                                expected_feed_sources=["feed_fda_recalls", "feed_mhra_dsu"], safety_enabled=True)
    assert r["status"] == "PASS" and r["degraded_required_sources"] == []
    assert "FEED_FDA_RECALLS_SERVED_BY_OFFICIAL_FALLBACK" in r["mirror_notices"]
    assert r["sources"]["feed_fda_recalls"]["du_phong"] == 1
