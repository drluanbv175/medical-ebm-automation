"""MedWatch bị FDA chặn truy cập tự động (401/403) không được làm mọi lượt thành PARTIAL (29/09/2026).

Bác sĩ chọn «ghi chú, không chặn»: chỉ miễn khi MỌI lỗi của feed là 401/403 VÀ openFDA + ≥ 1 feed an toàn
khác còn khoẻ. Lỗi khác hoặc thiếu dự phòng ⇒ vẫn PARTIAL. Offline, không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ingestion import summarize_source_health  # noqa: E402

API = ["pubmed", "europepmc", "crossref", "openfda"]
FEEDS = ["feed_fda_medwatch", "feed_fda_recalls", "feed_mhra_dsu", "feed_gold", "feed_gina", "feed_kdigo"]
LOI_401 = ("HTTPError: 401 Client Error: Unauthorized for url: "
           "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml")


def _row(src, st="ok", n=5, err=None):
    return {"source": src, "status": st, "record_count": n, "error_message": err}


def _chay(medwatch_rows, bo=()):
    logs = [_row(s) for s in API if s not in bo] + medwatch_rows
    logs += [_row(f) for f in FEEDS[1:] if f not in bo]
    return summarize_source_health(logs, expected_api_sources=API, expected_feed_sources=FEEDS,
                                   safety_enabled=True)


def test_medwatch_401_voi_du_phong_khoe_la_pass_kem_ghi_chu():
    r = _chay([_row("feed_fda_medwatch", "error", 0, LOI_401)])
    assert r["status"] == "PASS"
    assert "feed_fda_medwatch" not in r["degraded_required_sources"]
    assert "FEED_FDA_MEDWATCH_PROVIDER_BLOCKS_AUTOMATED_ACCESS_401_403" in r["mirror_notices"]
    assert r["sources"]["feed_fda_medwatch"]["error_http_401_403"] == 1


def test_medwatch_403_cung_duoc_mien():
    r = _chay([_row("feed_fda_medwatch", "error", 0, "HTTPError: 403 Client Error: Forbidden for url: x")])
    assert r["status"] == "PASS"


def test_medwatch_timeout_van_partial():
    r = _chay([_row("feed_fda_medwatch", "error", 0, "ReadTimeout: HTTPSConnectionPool timed out")])
    assert r["status"] == "PARTIAL" and "feed_fda_medwatch" in r["degraded_required_sources"]


def test_medwatch_lan_401_va_loi_khac_van_partial():
    r = _chay([_row("feed_fda_medwatch", "error", 0, LOI_401),
               _row("feed_fda_medwatch", "error", 0, "HTTPError: 503 Server Error")])
    assert r["status"] == "PARTIAL"


def test_medwatch_401_nhung_openfda_hong_van_partial():
    r = _chay([_row("feed_fda_medwatch", "error", 0, LOI_401), _row("openfda", "error", 0, "x")], bo=("openfda",))
    assert r["status"] == "PARTIAL" and "feed_fda_medwatch" in r["degraded_required_sources"]


def test_medwatch_401_chi_con_openfda_van_partial():
    r = _chay([_row("feed_fda_medwatch", "error", 0, LOI_401),
               _row("feed_fda_recalls", "error", 0, "x"), _row("feed_mhra_dsu", "error", 0, "x")],
              bo=("feed_fda_recalls", "feed_mhra_dsu"))
    assert r["status"] == "PARTIAL" and "feed_fda_medwatch" in r["degraded_required_sources"]


def test_feed_an_toan_khac_401_khong_duoc_mien():
    logs = [_row(s) for s in API] + [_row("feed_fda_medwatch")] + [_row("feed_mhra_dsu", "error", 0, LOI_401)]
    logs += [_row(f) for f in FEEDS[1:] if f != "feed_mhra_dsu"]
    r = summarize_source_health(logs, expected_api_sources=API, expected_feed_sources=FEEDS, safety_enabled=True)
    assert r["status"] == "PARTIAL" and "feed_mhra_dsu" in r["degraded_required_sources"]
