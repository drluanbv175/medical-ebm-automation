"""Hồi quy 25/09/2026: feed thu hồi thuốc FDA bị chặn ⇒ lùi sang openFDA drug/enforcement (API chính thức).

www.fda.gov chặn truy cập tự động chập chờn (cùng feed lúc 401 lúc 200). Không giả dạng trình duyệt;
dùng API chính thức tương đương. MedWatch không có API tương đương nên KHÔNG được dự phòng giả. OFFLINE.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources.feeds import DRUG_SAFETY_FEEDS  # noqa: E402
from app.sources.rss_feed import RSSFeedClient  # noqa: E402

_ENF = {"results": [
    {"report_date": "20260916", "classification": "Class III", "recall_number": "D-0836-2026",
     "reason_for_recall": "Failed impurities specifications",
     "product_description": "Fluphenazine Hydrochloride Tablets, USP, 1mg"},
    {"report_date": "20260915", "classification": "Class II", "reason_for_recall": "", "product_description": ""},
]}


class _HttpChan:
    """RSS luôn lỗi 401 (giả www.fda.gov chặn); openFDA trả dữ liệu enforcement."""

    def __init__(self):
        self.goi_json = []

    def get_text(self, url, **kw):
        raise RuntimeError("401 Client Error: Unauthorized")

    def get_json(self, url, params=None, **kw):
        self.goi_json.append((url, dict(params or {})))
        return _ENF


def _feed(fid):
    return next(f for f in DRUG_SAFETY_FEEDS if f.id == fid)


@pytest.fixture(autouse=True)
def _khong_mock(monkeypatch):
    monkeypatch.setattr(settings, "openfda_api_key", "")


def _client(fid, monkeypatch):
    c = RSSFeedClient(_feed(fid))
    monkeypatch.setattr(c, "use_mock", False)
    c.http = _HttpChan()
    return c


def test_fda_recalls_rss_loi_thi_lui_openfda(monkeypatch):
    c = _client("fda_recalls", monkeypatch)
    out = c.search(max_results=5, since_date="2026-09-01")
    assert len(out) == 1                                   # mục rỗng bị bỏ, không bịa
    r = out[0]
    assert r.raw["_via"] == "openfda_enforcement" and r.raw["recall_number"] == "D-0836-2026"
    assert r.publication_date == "2026-09-16" and "Fluphenazine" in r.title
    url, params = c.http.goi_json[0]
    assert url.endswith("/drug/enforcement.json")
    assert params["search"] == "report_date:[20260901 TO 99991231]"


def test_medwatch_loi_khong_du_phong_gia(monkeypatch):
    c = _client("fda_medwatch", monkeypatch)
    assert c.search(max_results=5) == []
    assert c.http.goi_json == []                           # không gọi openFDA thay MedWatch


def test_openfda_cung_loi_tra_rong_khong_bia(monkeypatch):
    c = _client("fda_recalls", monkeypatch)

    def _loi(*a, **k):
        raise RuntimeError("503")
    c.http.get_json = _loi
    assert c.search(max_results=5) == []
