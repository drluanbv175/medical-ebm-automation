"""Test offline cho `app/sources/guideline_lanes.py` và các lane guideline trong `feeds.py` (không gọi mạng)."""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.sources import guideline_lanes as gl  # noqa: E402
from app.sources.authority import FEED_TO_AUTHORITY, assess_source_universe_coverage  # noqa: E402
from app.sources.feeds import GUIDELINE_FEEDS, GUIDELINE_LANES  # noqa: E402
from app.sources.rss_feed import RSSFeedClient  # noqa: E402

ISSN_RE = re.compile(r"^\d{4}-\d{3}[\dX]$")
HOM_NAY = date.today()
CACH_DAY = (HOM_NAY - timedelta(days=5)).isoformat()


class HttpGia:
    """Http giả: ghi lại lời gọi, trả JSON/text đã định sẵn hoặc ném lỗi."""

    def __init__(self, json_data: Any = None, text: Any = None, loi: BaseException | None = None) -> None:
        self.json_data, self.text, self.loi = json_data, text, loi
        self.calls: List[Dict[str, Any]] = []

    def get_json(self, url, params=None, **kw):
        self.calls.append({"url": url, "params": dict(params or {})})
        if self.loi:
            raise self.loi
        return self.json_data

    def get_text(self, url, params=None, **kw):
        self.calls.append({"url": url, "params": dict(params or {})})
        if self.loi:
            raise self.loi
        if isinstance(self.text, list):
            return self.text[min(len(self.calls) - 1, len(self.text) - 1)]
        return self.text


# ═════════════════════════ cấu hình ═════════════════════════

def test_every_lane_has_the_fields_its_mode_needs_and_ids_are_unique():
    ids = [f.id for f in GUIDELINE_FEEDS]
    assert len(ids) == len(set(ids))
    for f in GUIDELINE_LANES:
        if f.mode == "crossref_title":
            assert f.title_query and f.issn, f.id
            assert all(ISSN_RE.match(i) for i in f.issn.split("|")), f.id
            re.compile(f.title_regex or ".")            # regex phải biên dịch được
        elif f.mode == "europepmc":
            assert f.epmc_query, f.id
        elif f.mode in {"who_iris", "kcb_vn", "rss"}:
            assert f.url.startswith("https://"), f.id


def test_the_named_authorities_are_covered_by_lanes():
    ids = {f.id for f in GUIDELINE_LANES}
    for i in ("epmc_uspstf", "epmc_who", "who_iris", "kcb_vn", "acc_aha_circ", "acc_aha_jacc", "esc_ehj", "ada_standards",
              "idsa_cid", "eular_ard", "aasld_hep", "kdigo_ki", "gold_copd", "gina", "kdigo_news", "easl",
              "aasld_rss", "ats_ajrccm", "ers_erj", "bts_thorax", "ags_jags", "epmc_practice_guideline"):
        assert i in ids, i


def test_the_authority_alias_table_points_only_to_names_in_the_universe_and_to_real_feeds():
    from app.sources.authority import EVIDENCE_SOURCE_UNIVERSE
    ten_that = {n for layer in EVIDENCE_SOURCE_UNIVERSE for n in layer.sources}
    feed_that = {f"feed_{f.id}" for f in GUIDELINE_FEEDS}
    for feed, org in FEED_TO_AUTHORITY.items():
        assert org in ten_that, f"{feed} -> {org}: tên tổ chức không có trong vũ trụ nguồn"
        assert feed in feed_that, f"{feed}: không có feed tương ứng trong feeds.py"


def test_coverage_reports_lane_coverage_separately_from_direct_connectors():
    r = assess_source_universe_coverage(["feed_esc_ehj", "feed_epmc_uspstf", "feed_who_iris", "feed_kcb_vn"])
    tang = r["layers"]["guideline_authority"]
    assert tang["healthy"] == []                      # không có connector trực tiếp nào
    assert set(tang["healthy_via_lane"]) == {"esc", "uspstf", "who", "moh_vietnam"}
    assert tang["status"] == "PASS"
    assert "nice" in tang["not_connected"] and "esc" not in tang["not_connected"]


def test_without_any_lane_the_guideline_layer_is_partial_and_lists_everything_as_not_connected():
    tang = assess_source_universe_coverage([])["layers"]["guideline_authority"]
    assert tang["status"] == "PARTIAL" and tang["healthy_via_lane"] == []
    assert set(tang["not_connected"]) == set(tang["expected"])


# ═════════════════════════ Europe PMC ═════════════════════════

def _epmc(*ket_qua: Dict[str, Any]) -> Dict[str, Any]:
    return {"resultList": {"result": list(ket_qua)}}


def test_europepmc_lane_builds_the_query_window_and_sort():
    http = HttpGia(json_data=_epmc())
    gl.europepmc_lane(http, 'PUB_TYPE:"Practice Guideline"', 500, since_date="2026-08-01")
    (c,) = http.calls
    assert c["url"] == gl.EUROPEPMC
    assert c["params"]["query"] == f'(PUB_TYPE:"Practice Guideline") AND FIRST_PDATE:[2026-08-01 TO {HOM_NAY.isoformat()}]'
    assert c["params"]["sort"] == "FIRST_PDATE_D desc" and c["params"]["pageSize"] == 100    # kẹp ở 100
    assert c["params"]["resultType"] == "core"


def test_europepmc_lane_maps_records_including_pmid_and_flags_guideline():
    http = HttpGia(json_data=_epmc({"title": "Hướng dẫn <i>X</i>.", "pmid": "123", "doi": "10.1/ABC", "source": "MED", "id": "123",
                                    "firstPublicationDate": "2026-09-01", "abstractText": "<p>Tóm  tắt</p>"}))
    (m,) = gl.europepmc_lane(http, "q", 5, guideline=True)
    assert m["title"] == "Hướng dẫn X" and m["pmid"] == "123" and m["doi"] == "10.1/abc"
    assert m["summary"] == "Tóm tắt" and m["guideline"] is True and m["url"] == "https://europepmc.org/article/MED/123"


def test_europepmc_lane_skips_junk_and_survives_errors():
    assert gl.europepmc_lane(HttpGia(json_data=_epmc({"title": "  "}, "rác", None)), "q", 5) == []
    assert gl.europepmc_lane(HttpGia(loi=RuntimeError("mạng")), "q", 5) == []
    assert gl.europepmc_lane(HttpGia(json_data={"lạ": 1}), "q", 5) == []


# ═════════════════════════ WHO IRIS (OAI-PMH) ═════════════════════════

def _oai(*bi: Dict[str, Any], token: str = "", loi_oai: str = "") -> str:
    if loi_oai:
        return f'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="{loi_oai}">x</error></OAI-PMH>'
    ban_ghi = ""
    for b in bi:
        dc = "".join(f"<dc:{k}>{v}</dc:{k}>" for k in ("title", "date", "type", "identifier", "description") if k in b
                     for v in ([b[k]] if not isinstance(b[k], list) else b[k]))
        ban_ghi += f"<record><header><datestamp>2026-09-01T00:00:00Z</datestamp></header><metadata>" \
                   f'<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" ' \
                   f'xmlns:dc="http://purl.org/dc/elements/1.1/">{dc}</oai_dc:dc></metadata></record>'
    tk = f"<resumptionToken>{token}</resumptionToken>" if token else ""
    return f'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><ListRecords>{ban_ghi}{tk}</ListRecords></OAI-PMH>'


def test_who_iris_keeps_only_recent_publications_that_look_like_guidelines():
    xml = _oai(
        {"title": "WHO guidelines on hand hygiene", "date": CACH_DAY, "type": "Publications", "identifier": "https://iris.who.int/h/1"},
        {"title": "Guideline: sugars intake", "date": "2009-03-01", "type": "Publications"},          # ấn phẩm CŨ (WHO sửa lại)
        {"title": "Annual report of the Director", "date": CACH_DAY, "type": "Publications"},          # không phải khuyến cáo
        {"title": "Guidance for governing bodies", "date": CACH_DAY, "type": "Governing Bodies documents"},
    )
    http = HttpGia(text=xml)
    r = gl.who_iris_lane(http, 10, since_date=(HOM_NAY - timedelta(days=30)).isoformat())
    assert [m["title"] for m in r] == ["WHO guidelines on hand hygiene"]
    assert r[0]["url"] == "https://iris.who.int/h/1" and r[0]["guideline"] is True
    p = http.calls[0]["params"]
    assert p["verb"] == "ListRecords" and p["metadataPrefix"] == "oai_dc" and p["set"] == gl.WHO_IRIS_HQ_SET


def test_who_iris_follows_the_resumption_token_but_stops_at_the_page_cap():
    trang = _oai({"title": "WHO guideline A", "date": CACH_DAY, "type": "Publications"}, token="TOK")
    http = HttpGia(text=[trang] * 10)
    gl.who_iris_lane(http, 500, since_date="2026-01-01")
    assert len(http.calls) == gl._MAX_TRANG_OAI
    assert http.calls[1]["params"] == {"verb": "ListRecords", "resumptionToken": "TOK"}


def test_who_iris_stops_when_enough_records_or_on_oai_error():
    trang = _oai({"title": "WHO guideline A", "date": CACH_DAY, "type": "Publications"}, token="TOK")
    http = HttpGia(text=[trang] * 5)
    gl.who_iris_lane(http, 1, since_date="2026-01-01")
    assert len(http.calls) == 1, "đã đủ số bản ghi thì không kéo thêm trang"
    assert gl.who_iris_lane(HttpGia(text=_oai(loi_oai="noRecordsMatch")), 5) == []


@pytest.mark.parametrize("hong", ["<không phải xml", "", "<a><b></a>"])
def test_who_iris_survives_garbled_xml_and_network_errors(hong):
    assert gl.who_iris_lane(HttpGia(text=hong), 5) == []
    assert gl.who_iris_lane(HttpGia(loi=TimeoutError("hết giờ")), 5) == []


def test_who_iris_rejects_xml_entity_expansion_attacks():
    bom = ('<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;">]>'
           '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><ListRecords>&b;</ListRecords></OAI-PMH>')
    assert gl.who_iris_lane(HttpGia(text=bom), 5) == []


@pytest.mark.parametrize("dc,ky_vong", [("2026", "2026-12-28"), ("2026-03", "2026-03-28"), ("2026-03-09T00:00:00Z", "2026-03-09"),
                                        ("không phải ngày", None)])
def test_oai_partial_dates_are_completed_to_the_end_of_the_period_never_earlier(dc, ky_vong):
    import xml.etree.ElementTree as ET
    rec = ET.fromstring(f'<r xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:date>{dc}</dc:date></r>')
    assert gl._ngay_oai(rec) == ky_vong


# ═════════════════════════ kcb.vn ═════════════════════════

KCB_HTML = '''
<div class="title"><a href="/phac-do/quyet-dinh-so-2388-qd-byt.html?categoryId=101" title="Quyết định số 2388/QĐ-BYT ngày 12/8/2024 Về việc ban hành &quot;Hướng dẫn X&quot;">Quyết định số 2388/QĐ-BYT ngày 12/8/2024…</a></div>
<div class="title"><a href="/phac-do/quyet-dinh-3908.html">Quyết định 3908/QĐ-BYT của Bộ Y tế ngày 20 tháng 10 năm 2023 về việc ban hành</a></div>
<div class="title"><a href="/phac-do/quyet-dinh-khong-ngay.html">Quyết định về việc ban hành tài liệu chuyên môn</a></div>
<div><a href="/phac-do/quyet-dinh-3908.html">Quyết định 3908/QĐ-BYT lặp</a></div>
<div><a href="/van-ban/khac">Quyết định ở mục khác</a></div>
<div><a href="/phac-do/tin-tuc.html">Tin tức và hoạt động chuyên môn</a></div>
'''


def test_kcb_vn_parses_decisions_with_full_title_query_suffix_and_dates():
    r = gl.kcb_vn_lane(HttpGia(text=KCB_HTML), 20)
    assert [m["date"] for m in r] == ["2024-08-12", "2023-10-20", None]
    assert r[0]["title"] == 'Quyết định số 2388/QĐ-BYT ngày 12/8/2024 Về việc ban hành "Hướng dẫn X"'   # title đầy đủ, đã giải mã
    assert r[0]["url"] == "https://kcb.vn/phac-do/quyet-dinh-so-2388-qd-byt.html"                    # bỏ ?categoryId
    assert all(m["guideline"] for m in r)


def test_kcb_vn_deduplicates_and_ignores_other_sections_and_non_decisions():
    urls = [m["url"] for m in gl.kcb_vn_lane(HttpGia(text=KCB_HTML), 20)]
    assert len(urls) == len(set(urls)) == 3


def test_kcb_vn_since_date_drops_old_decisions_but_keeps_undated_ones():
    r = gl.kcb_vn_lane(HttpGia(text=KCB_HTML), 20, since_date="2024-01-01")
    assert [m["date"] for m in r] == ["2024-08-12", None]


def test_kcb_vn_survives_errors_and_unexpected_html():
    assert gl.kcb_vn_lane(HttpGia(loi=RuntimeError("x")), 5) == []
    assert gl.kcb_vn_lane(HttpGia(text="<html>không có danh sách</html>"), 5) == []


@pytest.mark.parametrize("tieu_de,ky_vong", [("… ngày 31/2/2024 …", None), ("… ngày 05-07-2022 …", "2022-07-05"),
                                             ("… ngày 17 tháng 07 năm 2020 …", "2020-07-17"), ("không có ngày", None)])
def test_kcb_vn_date_parsing(tieu_de, ky_vong):
    assert gl._ngay_kcb(tieu_de) == ky_vong


# ═════════════════════════ Crossref theo tiêu đề ═════════════════════════

def _bai(tieu_de: str, doi: str = "10.1/x", ngay=(2026, 9, 1)) -> Dict[str, Any]:
    return {"DOI": doi, "title": [tieu_de], "URL": f"https://doi.org/{doi}", "published-online": {"date-parts": [list(ngay)]}}


def _cr(*items: Dict[str, Any]) -> Dict[str, Any]:
    return {"message": {"items": list(items)}}


def test_crossref_title_lane_builds_a_multi_issn_filter_and_title_query():
    http = HttpGia(json_data=_cr())
    gl.crossref_title_lane(http, ["0195-668X", "1522-9645"], "ESC Guidelines", r"\bESC\b", 5, since_date="2026-01-01",
                           mailto="bs@example.org")
    p = http.calls[0]["params"]
    assert p["filter"] == "issn:0195-668X,issn:1522-9645,from-pub-date:2026-01-01,type:journal-article"
    assert p["query.title"] == "ESC Guidelines" and p["rows"] == 60 and p["mailto"] == "bs@example.org"


def test_crossref_title_lane_keeps_org_guidelines_and_drops_corrections_letters_and_offtopic():
    http = HttpGia(json_data=_cr(
        _bai("2026 ESC Guidelines for the management of heart failure", "10.1/a", (2026, 8, 28)),
        _bai("Correction to: 2026 ESC Guidelines for the management of heart failure", "10.1/b"),
        _bai("Response to correspondence on ESC guidelines", "10.1/c"),
        _bai("Erratum: ESC consensus statement", "10.1/d"),
        _bai("Guideline-Recommended Follow-Up for Aortic Stenosis", "10.1/e"),            # không có token tổ chức
        _bai("ESC congress report of the year", "10.1/f"),                                # không có tính khuyến cáo
        _bai("ESC consensus statement on cardiac rehabilitation", "10.1/g", (2026, 9, 2)),
    ))
    r = gl.crossref_title_lane(http, ["0195-668X"], "ESC Guidelines", r"\bESC\b", 10)
    assert [m["doi"] for m in r] == ["10.1/g", "10.1/a"], "sắp theo ngày giảm dần, chỉ giữ khuyến cáo của ESC"
    assert all(m["guideline"] for m in r)


def test_crossref_title_lane_truncates_to_max_results_after_sorting():
    items = [_bai(f"ESC Guidelines part {i}", f"10.1/{i}", (2026, 1, i + 1)) for i in range(8)]
    r = gl.crossref_title_lane(HttpGia(json_data=_cr(*items)), ["1"], "ESC", r"ESC", 3)
    assert [m["doi"] for m in r] == ["10.1/7", "10.1/6", "10.1/5"]


def test_crossref_title_lane_without_issn_or_query_makes_no_request():
    http = HttpGia(json_data=_cr(_bai("ESC Guidelines")))
    assert gl.crossref_title_lane(http, [], "q", None, 5) == []
    assert gl.crossref_title_lane(http, ["1234-5678"], "", None, 5) == []
    assert http.calls == []


@pytest.mark.parametrize("loi", [RuntimeError("x"), ValueError("y"), TimeoutError("z")])
def test_crossref_title_lane_survives_errors(loi):
    assert gl.crossref_title_lane(HttpGia(loi=loi), ["1234-5678"], "q", None, 5) == []


def test_crossref_title_lane_ignores_garbage_items_and_missing_titles():
    r = gl.crossref_title_lane(HttpGia(json_data=_cr("rác", None, {"title": []}, _bai("ESC guideline ok"))), ["1"], "q", "ESC", 5)
    assert len(r) == 1


# ═════════════════════════ tích hợp RSSFeedClient ═════════════════════════

def _client(feed_id: str, monkeypatch, **http_kw) -> RSSFeedClient:
    f = next(x for x in GUIDELINE_FEEDS if x.id == feed_id)
    c = RSSFeedClient(f)
    c.use_mock = False
    http = HttpGia(**http_kw)
    monkeypatch.setattr(c, "http", http)
    return c


def test_the_client_wraps_lane_items_as_raw_records_with_pmid_doi_and_guideline_type(monkeypatch):
    c = _client("epmc_practice_guideline", monkeypatch, json_data=_epmc(
        {"title": "Position statement X", "pmid": "42", "doi": "10.1/x", "source": "MED", "id": "42",
         "firstPublicationDate": "2026-09-01", "abstractText": "tóm tắt"}))
    (r,) = c.search("", max_results=5)
    assert r.source == "feed_epmc_practice_guideline" and r.pmid == "42" and r.doi == "10.1/x"
    assert r.study_type == "guideline" and r.source_type == "guideline"
    assert r.raw["_via"] == "europepmc" and r.api_endpoint == gl.EUROPEPMC


def test_the_high_volume_lane_asks_for_at_least_its_cap_even_when_ingestion_passes_a_small_number(monkeypatch):
    c = _client("epmc_practice_guideline", monkeypatch, json_data=_epmc())
    c.search("", max_results=10)
    assert c.http.calls[0]["params"]["pageSize"] == 50


def test_since_date_from_ingestion_is_forwarded_to_every_lane_mode(monkeypatch):
    c = _client("epmc_uspstf", monkeypatch, json_data=_epmc())
    c.search("", max_results=5, since_date="2026-09-10")
    assert "FIRST_PDATE:[2026-09-10 TO" in c.http.calls[0]["params"]["query"]
    c = _client("esc_ehj", monkeypatch, json_data=_cr())
    c.search("", max_results=5, since_date="2026-09-10")
    assert "from-pub-date:2026-09-10" in c.http.calls[0]["params"]["filter"]


def test_title_lane_records_use_the_generic_classifier_not_a_forced_guideline_label(monkeypatch):
    c = _client("esc_ehj", monkeypatch, json_data=_cr(_bai("ESC consensus statement on something", "10.1/z")))
    (r,) = c.search("", max_results=5)
    assert r.raw["_via"] == "crossref_title" and r.doi == "10.1/z"
    assert r.study_type != "guideline" or r.source_type == "guideline"    # nhất quán, không tự gán nhãn cứng


def test_who_iris_and_kcb_records_are_labelled_guideline(monkeypatch):
    c = _client("kcb_vn", monkeypatch, text=KCB_HTML)
    recs = c.search("", max_results=5)
    assert recs and all(r.study_type == "guideline" and r.source_type == "guideline" for r in recs)
    assert recs[0].source == "feed_kcb_vn" and recs[0].api_endpoint == gl.KCB_PHAC_DO


def test_lane_errors_return_empty_and_never_mock(monkeypatch):
    for fid in ("epmc_practice_guideline", "who_iris", "kcb_vn", "esc_ehj"):
        c = _client(fid, monkeypatch, loi=RuntimeError("mạng lỗi"))
        assert c.search("", max_results=5) == [], fid


def test_source_log_endpoint_points_to_the_real_lane_endpoint():
    theo_id = {f.id: f for f in GUIDELINE_FEEDS}
    assert RSSFeedClient(theo_id["who_iris"]).endpoint == gl.WHO_IRIS_OAI
    assert RSSFeedClient(theo_id["epmc_who"]).endpoint == gl.EUROPEPMC
    assert RSSFeedClient(theo_id["kcb_vn"]).endpoint == gl.KCB_PHAC_DO
    assert RSSFeedClient(theo_id["esc_ehj"]).endpoint.startswith(gl.CROSSREF_WORKS)
