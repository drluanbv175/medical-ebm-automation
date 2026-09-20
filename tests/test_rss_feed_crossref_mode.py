"""Test offline cho chế độ Crossref của `RSSFeedClient` (feed RSS của nhà xuất bản không đọc được → lấy theo ISSN).

Không gọi mạng: `client.http.get_json` được thay bằng hàm giả ghi lại tham số.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.sources.feeds import DRUG_SAFETY_FEEDS, GUIDELINE_FEEDS, FeedConfig  # noqa: E402
from app.sources.rss_feed import RSSFeedClient  # noqa: E402

ISSN_RE = re.compile(r"^\d{4}-\d{3}[\dX]$")
CA_14_FEED_LOI_RSS = {
    "bmj_ebm", "ard_bmj", "bmj_drc", "diabetologia", "sti_bmj", "bmj_gh", "emj_bmj", "jnnp_bmj",
    "practneurol_bmj", "svn_bmj", "bmc_nephrol", "j_nephrol", "bmj_mentalhealth", "bmj_recent",
}


def _feed(**kw: Any) -> FeedConfig:
    co = dict(id="thu", name="Tạp chí thử", url="https://api.crossref.org/journals/1234-5678", org="Thử",
              kind="guideline", clinical_area="Tim mạch", issn="1234-5678", mode="crossref")
    co.update(kw)
    return FeedConfig(**co)


def _client(monkeypatch, feed: FeedConfig, items: Any = None, loi: BaseException | None = None):
    client = RSSFeedClient(feed)
    client.use_mock = False
    ghi: Dict[str, Any] = {"calls": []}

    def fake_get_json(url, params=None, **kw):
        ghi["calls"].append({"url": url, "params": dict(params or {})})
        if loi is not None:
            raise loi
        return {"message": {"items": items if items is not None else []}}

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    return client, ghi


def _bai(**kw: Any) -> Dict[str, Any]:
    b = {"DOI": "10.1000/ABC.123", "title": ["Một bài <i>nghiên cứu</i> thử"],
         "URL": "https://doi.org/10.1000/abc.123",
         "published-online": {"date-parts": [[2026, 9, 10]]}, "abstract": "<jats:p>Tóm   tắt  thử</jats:p>"}
    b.update(kw)
    return b


# ───────────────────────────── cấu hình ─────────────────────────────

def test_the_14_feeds_that_failed_rss_are_now_crossref_mode_with_a_valid_issn():
    theo_id = {f.id: f for f in GUIDELINE_FEEDS}
    assert CA_14_FEED_LOI_RSS <= set(theo_id)
    for i in CA_14_FEED_LOI_RSS:
        assert theo_id[i].mode == "crossref" and ISSN_RE.match(theo_id[i].issn or ""), i


def test_every_crossref_mode_feed_has_a_valid_issn_and_ids_are_unique():
    tat_ca = list(DRUG_SAFETY_FEEDS) + list(GUIDELINE_FEEDS)
    ids = [f.id for f in tat_ca]
    assert len(ids) == len(set(ids)), "id feed phải duy nhất (id tạo tên nguồn feed_<id> trong SourceLog)"
    for f in tat_ca:
        assert f.mode in {"rss", "crossref"}, f.id
        if f.mode == "crossref":
            assert ISSN_RE.match(f.issn or ""), f"{f.id}: ISSN không hợp lệ"
            assert f.kind == "guideline"
        else:
            assert f.url.startswith("http"), f.id


def test_society_guideline_journals_are_covered_through_crossref():
    theo_id = {f.id: f for f in GUIDELINE_FEEDS}
    for i in ("circulation", "eur_heart_j", "diabetes_care", "cid", "hepatology", "kidney_int", "ajrccm",
              "eur_respir_j", "jags", "ann_intern_med", "cochrane_cdsr", "jco", "ann_oncol", "blood_adv"):
        assert theo_id[i].mode == "crossref", i


def test_bmj_and_cochrane_use_the_electronic_issn_because_the_print_issn_returns_no_recent_articles():
    theo_id = {f.id: f for f in GUIDELINE_FEEDS}
    assert theo_id["bmj_recent"].issn == "1756-1833"
    assert theo_id["cochrane_cdsr"].issn == "1465-1858"


def test_source_log_endpoint_points_to_crossref_not_the_unused_rss_url():
    theo_id = {f.id: f for f in GUIDELINE_FEEDS}
    assert RSSFeedClient(theo_id["bmj_gh"]).endpoint == "https://api.crossref.org/works?filter=issn:2059-7908"
    assert RSSFeedClient(theo_id["jama"]).endpoint == theo_id["jama"].url


def test_drug_safety_feeds_keep_reading_rss():
    assert all(f.mode == "rss" for f in DRUG_SAFETY_FEEDS)


# ───────────────────────────── hành vi ─────────────────────────────

def test_query_params_are_built_from_the_issn_and_window(monkeypatch):
    monkeypatch.setattr(settings, "openalex_email", "bs@example.org")
    client, ghi = _client(monkeypatch, _feed(), items=[_bai()])
    client.search("", max_results=7, since_date="2026-08-01")
    (goi,) = ghi["calls"]
    p = goi["params"]
    assert goi["url"] == "https://api.crossref.org/works"
    assert p["filter"] == "issn:1234-5678,from-pub-date:2026-08-01,type:journal-article"
    assert (p["sort"], p["order"], p["rows"]) == ("published", "desc", 7)
    assert p["mailto"] == "bs@example.org"


def test_without_since_date_the_window_is_the_last_45_days(monkeypatch):
    client, ghi = _client(monkeypatch, _feed(), items=[])
    client.search("", max_results=5)
    dau = ghi["calls"][0]["params"]["filter"].split("from-pub-date:")[1].split(",")[0]
    assert 44 <= (date.today() - date.fromisoformat(dau)).days <= 46


@pytest.mark.parametrize("nhap,ky_vong", [(0, 1), (-5, 1), (10**6, 100)])
def test_rows_are_clamped(monkeypatch, nhap, ky_vong):
    client, ghi = _client(monkeypatch, _feed(), items=[])
    client.search("", max_results=nhap)
    assert ghi["calls"][0]["params"]["rows"] == ky_vong


def test_items_are_mapped_to_records(monkeypatch):
    client, _ = _client(monkeypatch, _feed(id="circulation"), items=[_bai()])
    (r,) = client.search("", max_results=5)
    assert r.source == "feed_circulation"
    assert r.title == "Một bài nghiên cứu thử"
    assert r.doi == "10.1000/abc.123", "DOI phải viết thường để khử trùng với nguồn khác"
    assert r.publication_date == "2026-09-10"
    assert r.abstract == "Tóm tắt thử"
    assert r.url == "https://doi.org/10.1000/abc.123"
    assert r.journal_or_organization == "Thử"
    assert r.clinical_area == "Tim mạch"
    assert r.raw["_via"] == "crossref_issn" and r.raw["_feed"] == "circulation"
    assert r.api_endpoint.endswith("filter=issn:1234-5678")


def test_a_guideline_title_is_recognised_as_a_guideline(monkeypatch):
    tieu_de = "2026 ESC Guidelines for the management of heart failure"
    client, _ = _client(monkeypatch, _feed(), items=[_bai(title=[tieu_de])])
    (r,) = client.search("", max_results=5)
    assert r.study_type == "guideline" and r.source_type == "guideline"


def test_items_without_a_title_or_not_dicts_are_skipped(monkeypatch):
    client, _ = _client(monkeypatch, _feed(), items=[_bai(title=[]), _bai(title=["   "]), "rác", None, _bai()])
    assert len(client.search("", max_results=5)) == 1


@pytest.mark.parametrize("loi", [RuntimeError("mạng lỗi"), ValueError("json hỏng"), TimeoutError("hết giờ")])
def test_network_errors_return_empty_never_mock_and_never_raise(monkeypatch, loi):
    client, _ = _client(monkeypatch, _feed(), loi=loi)
    assert client.search("", max_results=5) == []


def test_a_crossref_mode_feed_without_issn_returns_empty_without_any_request(monkeypatch):
    client, ghi = _client(monkeypatch, _feed(issn=None), items=[_bai()])
    assert client.search("", max_results=5) == []
    assert ghi["calls"] == []


def test_mock_mode_still_uses_the_mock_pool_and_makes_no_request(monkeypatch):
    client, ghi = _client(monkeypatch, _feed(), items=[_bai()])
    client.use_mock = True
    client.search("", max_results=3)
    assert ghi["calls"] == []


def test_rss_mode_does_not_touch_crossref(monkeypatch):
    client = RSSFeedClient(_feed(mode="rss", issn=None, url="https://example.org/rss.xml"))
    client.use_mock = False
    chi_goi: List[str] = []
    monkeypatch.setattr(client.http, "get_text",
                        lambda url, **kw: chi_goi.append(url) or "<rss><channel></channel></rss>")
    monkeypatch.setattr(client.http, "get_json", lambda *a, **k: pytest.fail("mode rss không được gọi Crossref"))
    monkeypatch.setattr(client, "save_raw", lambda *a, **k: None)
    assert client.search("", max_results=3) == []
    assert chi_goi == ["https://example.org/rss.xml"]


# ───────────────────────────── ngày công bố ─────────────────────────────

def _ngay(item: Dict[str, Any]):
    return RSSFeedClient._ngay_crossref(item)


def test_online_first_date_wins_over_issue_date():
    item = {"published-online": {"date-parts": [[2026, 9, 10]]}, "issued": {"date-parts": [[2026, 9]]}}
    assert _ngay(item) == "2026-09-10"


def test_a_future_issue_date_falls_back_to_the_crossref_created_date():
    """Đo thật: bài đăng tháng 9 mang số phát hành 2026-10 — không được để ngày chưa tới làm lệch độ mới."""
    hom_nay = date.today()
    tuong_lai = [hom_nay.year + 1, 1]
    assert _ngay({"issued": {"date-parts": [tuong_lai]}, "created": {"date-parts": [[2026, 6, 3]]}}) == "2026-06-03"


def test_a_future_full_date_is_also_replaced():
    hom_nay = date.today()
    assert _ngay({"published-online": {"date-parts": [[hom_nay.year + 1, 1, 5]]},
                  "created": {"date-parts": [[2026, 5, 30]]}}) == "2026-05-30"


def test_year_only_and_year_month_dates_are_kept_as_given_not_invented():
    assert _ngay({"issued": {"date-parts": [[2025]]}}) == "2025"
    assert _ngay({"issued": {"date-parts": [[2026, 8]]}}) == "2026-08"


def test_missing_or_garbled_dates_return_none():
    assert _ngay({}) is None
    assert _ngay({"issued": {"date-parts": [[None]]}}) is None
    assert _ngay({"issued": "rác", "published-online": None}) is None
    assert _ngay({"issued": {"date-parts": [[True, True]]}}) is None
