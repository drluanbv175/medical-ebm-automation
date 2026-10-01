"""«VPN luôn bật» (bác sĩ chốt 01/10/2026): ba nguồn bị chặn qua VPN có ĐƯỜNG THAY chạy được qua VPN.

Đo đối chứng 01/10/2026 (VPN tắt 19:07 so với bật 18:01): CHỈ qua VPN = NCBI; CHỈ đi thẳng = EMA, ECDC, WHO IRIS.
Đường thay (đo thật qua VPN cùng ngày):
- WHO IRIS (hết giờ mở kết nối) ⇒ API ấn phẩm của www.who.int (`who_hub_lane`);
- ECDC «mối đe doạ» (CloudFront) ⇒ tin bùng phát dịch WHO (`who_don_lane`) + tạp chí Eurosurveillance (ECDC) qua
  Crossref;
- EMA (CloudFront) ⇒ Sổ đăng ký Liên minh của Uỷ ban châu Âu (`ec_union_register`, dự phòng trong `EmaMedicinesClient`).
Lane gốc bị chặn mà đường thay khoẻ ⇒ ghi chú «có đường thay» (hòm việc xếp ưu tiên thấp nhất), không đổi trạng thái.
Offline hoàn toàn: HTTP giả.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services import nguon_hong_keo_dai as nhkd  # noqa: E402
from app.services.ingestion import summarize_source_health  # noqa: E402
from app.sources import ec_union_register as ecr  # noqa: E402
from app.sources.ema_medicines import EMA_URL, TRUONG_GIU, EmaMedicinesClient  # noqa: E402
from app.sources.feeds import GUIDELINE_FEEDS  # noqa: E402
from app.sources.guideline_lanes import (  # noqa: E402
    WHO_DON_API,
    WHO_DON_ITEM_URL,
    WHO_HUB_API,
    WHO_ITEM_URL,
    who_don_lane,
    who_hub_lane,
)
from app.sources.rss_feed import RSSFeedClient  # noqa: E402
from app.utils.http import DAU_CLOUDFRONT_CHAN, DAU_KET_NOI_HET_GIO  # noqa: E402


class _HttpGia:
    """get_json/get_text giả theo URL; ghi lại lời gọi. Giá trị là ngoại lệ ⇒ ném."""

    def __init__(self, json_theo_url: Optional[Dict[str, Any]] = None,
                 text_theo_url: Optional[Dict[str, Any]] = None) -> None:
        self.json_theo_url, self.text_theo_url = json_theo_url or {}, text_theo_url or {}
        self.goi: List[Dict[str, Any]] = []

    @staticmethod
    def _tra(bang: Dict[str, Any], url: str) -> Any:
        if url not in bang:
            raise AssertionError(f"lời gọi ngoài dự kiến: {url}")
        gia_tri = bang[url]
        if isinstance(gia_tri, BaseException):
            raise gia_tri
        return gia_tri

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Any:
        self.goi.append({"url": url, "params": dict(params or {})})
        return self._tra(self.json_theo_url, url)

    def get_text(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Any:
        self.goi.append({"url": url, "params": dict(params or {})})
        return self._tra(self.text_theo_url, url)


def _an_pham(tieu_de: str, tag: str, ngay: str, duong: str = "/9789240000000") -> Dict[str, Any]:
    return {"Title": tieu_de, "Tag": tag, "PublicationDateAndTime": f"{ngay}T09:00:00Z", "ItemDefaultUrl": duong}


AN_PHAM = [
    _an_pham("WHO guidelines on expanding contraceptive options", "Guideline", "2026-09-23", "/9789240124578"),
    _an_pham("Social and behaviour change interventions for contraception", "Guidance (normative)", "2026-09-22"),
    _an_pham("Implementation guidance on the management of wasting", "Publication", "2026-09-17", "/9789240122840"),
    _an_pham("Global leprosy (Hansen Disease) update, 2025", "Publication", "2026-09-17"),
    _an_pham("Risk reduction of cognitive decline: WHO guidelines: executive summary", "Executive summary",
             "2026-09-16"),
    _an_pham("Programme budget guidance for Member States", "Governing bodies documentation", "2026-09-15"),
    _an_pham("WHO guidelines for malaria", "Guideline", "2026-08-01", "/guidelines-for-malaria"),
    _an_pham("WHO consolidated guidelines on tuberculosis", "Guideline", "ngày-hỏng"),
    _an_pham("WHO standards for something", "Guideline", "2026-09-20", "khong-co-gach-dau"),
]


# ═════════════ 1. Lane ấn phẩm WHO (thay WHO IRIS) ═════════════

def test_who_hub_giu_guideline_va_khuyen_cao_bo_tom_tat_va_van_kien_quan_tri():
    http = _HttpGia({WHO_HUB_API: {"value": AN_PHAM}})
    muc = who_hub_lane(http, 20, since_date="2026-09-01")
    assert [m["title"] for m in muc] == [
        "WHO guidelines on expanding contraceptive options",
        "Social and behaviour change interventions for contraception",
        "WHO standards for something",
        "Implementation guidance on the management of wasting",
    ]
    assert all(m["guideline"] is True and m["doi"] is None and m["pmid"] is None for m in muc)
    assert muc[0]["url"] == WHO_ITEM_URL + "/9789240124578" and muc[0]["date"] == "2026-09-23"
    assert muc[2]["url"] is None


def test_who_hub_tham_so_loc_ngay_phia_may_chu_va_khong_xin_summary():
    http = _HttpGia({WHO_HUB_API: {"value": []}})
    who_hub_lane(http, 10, since_date="2026-09-20")
    p = http.goi[0]["params"]
    assert p["$filter"] == "PublicationDateAndTime ge 2026-09-20T00:00:00Z"
    assert p["$orderby"] == "PublicationDateAndTime desc" and p["$top"] == "100"
    assert "Summary" not in p["$select"] and "Tag" in p["$select"]
    assert p["sf_provider"] == "OpenAccessProvider" and p["sf_site"]


def test_who_hub_cat_theo_so_toi_da_sau_khi_sap_giam_dan():
    muc = who_hub_lane(_HttpGia({WHO_HUB_API: {"value": AN_PHAM}}), 1, since_date="2026-09-01")
    assert [m["date"] for m in muc] == ["2026-09-23"]


def test_who_hub_bo_cuc_la_thi_nem_loi_khong_ve_rong():
    """Đọc hỏng không được thành «0 bản ghi» (xanh giả)."""
    with pytest.raises(ValueError):
        who_hub_lane(_HttpGia({WHO_HUB_API: {"error": {"code": "BadRequest"}}}), 10, since_date="2026-09-01")


def test_who_hub_loi_mang_tra_rong_de_httpclient_ghi_loi():
    assert who_hub_lane(_HttpGia({WHO_HUB_API: ConnectionError("mất mạng")}), 10, since_date="2026-09-01") == []


# ═════════════ 2. Lane tin dịch WHO (thay ECDC) ═════════════

def test_who_don_lay_tin_dich_kem_tom_tat_khong_phai_guideline():
    tin = [{"Title": "Ebola disease caused by Bundibugyo virus - Democratic Republic of the Congo",
            "PublicationDateAndTime": "2026-09-25T10:00:00Z", "ItemDefaultUrl": "/2026-DON618",
            "Summary": "<p>On 20 September &amp; after</p>"},
           {"Title": "Cũ", "PublicationDateAndTime": "2026-08-01T00:00:00Z", "ItemDefaultUrl": "/2026-DON600"}]
    http = _HttpGia({WHO_DON_API: {"value": tin}})
    muc = who_don_lane(http, 10, since_date="2026-09-01")
    assert len(muc) == 1 and muc[0]["guideline"] is False
    assert muc[0]["url"] == WHO_DON_ITEM_URL + "/2026-DON618" and muc[0]["summary"] == "On 20 September & after"
    assert http.goi[0]["params"]["$filter"] == "PublicationDateAndTime ge 2026-09-01T00:00:00Z"


def test_who_don_bo_cuc_la_thi_nem_loi():
    with pytest.raises(ValueError):
        who_don_lane(_HttpGia({WHO_DON_API: ["khong-phai-dict"]}), 10, since_date="2026-09-01")


# ═════════════ 3. Khai báo nguồn + điều phối trong rss_feed ═════════════

def _feed(fid: str):
    return next(f for f in GUIDELINE_FEEDS if f.id == fid)


def test_khai_bao_ba_duong_thay():
    assert _feed("who_publications").mode == "who_hub" and _feed("who_don").mode == "who_don"
    euro = _feed("eurosurveillance")
    assert euro.mode == "crossref" and euro.issn == "1560-7917" and euro.clinical_area == "Nhiễm khuẩn"


def test_rss_feed_dieu_phoi_lane_who_va_gan_guideline_dung_cho():
    c = RSSFeedClient(_feed("who_publications"))
    c.use_mock = False
    c.http = _HttpGia({WHO_HUB_API: {"value": AN_PHAM[:1]}})
    recs = c.search("", max_results=10, since_date="2026-09-01")
    assert c.endpoint == WHO_HUB_API and len(recs) == 1
    assert recs[0].study_type == "guideline" and recs[0].raw["_via"] == "who_hub"
    d = RSSFeedClient(_feed("who_don"))
    d.use_mock = False
    d.http = _HttpGia({WHO_DON_API: {"value": [{"Title": "Ebola disease - Congo", "ItemDefaultUrl": "/x",
                                                "PublicationDateAndTime": "2026-09-25T00:00:00Z"}]}})
    tin = d.search("", max_results=10, since_date="2026-09-01")
    assert d.endpoint == WHO_DON_API and len(tin) == 1 and tin[0].study_type != "guideline"


# ═════════════ 4. Ghi chú «có đường thay» — chỉ để NHÌN ═════════════

def _dong(nguon: str, status: str, so: int = 0, loi: Optional[str] = None) -> dict:
    return {"source": nguon, "status": status, "record_count": so, "error_message": loi}


def _tong_hop(dong: List[dict]) -> dict:
    nen = [_dong(n, "ok", 5) for n in ("pubmed", "europepmc", "crossref")]
    feeds = sorted({d["source"] for d in dong} | {"feed_g1", "feed_g2", "feed_g3"})
    return summarize_source_health(nen + [_dong(f"feed_g{i}", "ok", 2) for i in (1, 2, 3)] + dong,
                                   expected_api_sources=["pubmed", "europepmc", "crossref"],
                                   expected_feed_sources=feeds, safety_enabled=False)


IRIS_CHAN = _dong("feed_who_iris", "error", 0, f"{DAU_KET_NOI_HET_GIO} RuntimeError (lỗi cuối: ConnectTimeout): x")
ECDC_CHAN = _dong("feed_ecdc_threats", "error", 0, f"{DAU_CLOUDFRONT_CHAN} HTTPError: 403 Client Error: x")
GHI_CHU_IRIS = "FEED_WHO_IRIS_BLOCKED_ON_NETWORK_PATH_SERVED_BY_FEED_WHO_PUBLICATIONS"


def test_iris_bi_chan_mang_va_duong_thay_khoe_thi_co_ghi_chu():
    h = _tong_hop([IRIS_CHAN, _dong("feed_who_publications", "ok", 3)])
    assert GHI_CHU_IRIS in h["mirror_notices"]


@pytest.mark.parametrize("dong_iris, dong_thay", [
    (_dong("feed_who_iris", "error", 0, "HTTPError: 500 Server Error: x"), _dong("feed_who_publications", "ok", 3)),
    (IRIS_CHAN, _dong("feed_who_publications", "error", 0, "HTTPError: 500 Server Error: x")),
    (IRIS_CHAN, None),
])
def test_khong_ghi_chu_khi_loi_that_hoac_duong_thay_hong_hoac_vang(dong_iris, dong_thay):
    h = _tong_hop([dong_iris] + ([dong_thay] if dong_thay else []))
    assert not any(g.startswith("FEED_WHO_IRIS_") for g in h["mirror_notices"])


def test_iris_mot_phan_chay_duoc_khong_phai_unavailable_thi_khong_ghi_chu():
    h = _tong_hop([IRIS_CHAN, _dong("feed_who_iris", "ok", 2), _dong("feed_who_publications", "ok", 3)])
    assert not any(g.startswith("FEED_WHO_IRIS_") for g in h["mirror_notices"])


def test_ecdc_ghi_chu_neu_dung_duong_thay_dang_khoe():
    mot = _tong_hop([ECDC_CHAN, _dong("feed_who_don", "ok", 1),
                     _dong("feed_eurosurveillance", "error", 0, "HTTPError: 500 Server Error: x")])
    assert "FEED_ECDC_THREATS_BLOCKED_ON_NETWORK_PATH_SERVED_BY_FEED_WHO_DON" in mot["mirror_notices"]
    hai = _tong_hop([ECDC_CHAN, _dong("feed_who_don", "ok", 1), _dong("feed_eurosurveillance", "ok", 10)])
    assert ("FEED_ECDC_THREATS_BLOCKED_ON_NETWORK_PATH_SERVED_BY_FEED_WHO_DON_AND_FEED_EUROSURVEILLANCE"
            in hai["mirror_notices"])


def test_ghi_chu_khong_doi_trang_thai_va_ha_uu_tien_trong_danh_sach_hong_keo_dai():
    co = _tong_hop([IRIS_CHAN, _dong("feed_who_publications", "ok", 3)])
    khong = _tong_hop([IRIS_CHAN, _dong("feed_who_publications", "error", 0, "HTTPError: 500 Server Error: x")])
    assert co["status"] == khong["status"] and co["warnings"] == khong["warnings"]
    from datetime import datetime, timedelta
    luc = datetime(2026, 10, 6, 12, 0)
    hong = {"feed_who_iris": {"health": "unavailable"}}
    lich_su = [{"luc": luc - timedelta(days=d), "sources": hong} for d in (3, 7)]
    kq = nhkd.tinh_hong_keo_dai(co["sources"], lich_su, luc, ghi_chu=co["mirror_notices"])
    assert kq["feed_who_iris"]["da_co_ghi_chu"] == GHI_CHU_IRIS


# ═════════════ 5. Sổ đăng ký Liên minh (EC) ═════════════

TRANG_EC = ('<html><script>var exportTitle ="x";\n\t\tvar dataSet = [\n'
            '{"eu_num":{"display":"EU/1/04/273","pre":"h","id":"273"},"name":"Lysodren","inn":"Mitotane",'
            '"indication":"dòng có\tký tự điều khiển và chuỗi ]; giả","company":"Esteve"},\n'
            '{"eu_num":{"display":"EU/1/00/137","pre":"h","id":"137"},"name":"Avandia","inn":"Rosiglitazone",'
            '"indication":"x","company":"SmithKline"}\n];\n</script></html>')


def test_ec_doc_khoi_du_lieu_ke_ca_ky_tu_dieu_khien_va_chuoi_giong_dau_ket():
    ds = ecr.doc_bo_du_lieu(TRANG_EC)
    assert [x["name"] for x in ds] == ["Lysodren", "Avandia"] and "\t" in ds[0]["indication"]


@pytest.mark.parametrize("trang", ["<html>không có dữ liệu</html>", "var dataSet = [];", "var dataSet = {\"a\": 1};",
                                   "var dataSet = [{\"name\": ", "var dataSet = [{\"khac\": 1}];"])
def test_ec_bo_cuc_la_rong_hoac_hong_la_loi(trang):
    with pytest.raises(ecr.EcLoi):
        ecr.doc_bo_du_lieu(trang)


def test_ec_url_trang_thuoc():
    assert ecr.url_trang_thuoc({"pre": "h", "id": "137"}) == ecr.EC_SO_DANG_KY + "h137.htm"
    assert ecr.url_trang_thuoc({"pre": "h", "id": "../../x"}) == "" and ecr.url_trang_thuoc(None) == ""


def _trang(*thuoc: Dict[str, Any]) -> str:
    import json
    return "var dataSet = " + json.dumps(list(thuoc)) + ";\n"


def _thuoc(ten: str, hoat_chat: str, ma: str) -> Dict[str, Any]:
    return {"eu_num": {"display": f"EU/1/00/{ma}", "pre": "h", "id": ma}, "name": ten, "inn": hoat_chat,
            "indication": "x", "company": "C"}


SO_EC = {ecr.EC_DANG_LUU_HANH: _trang(_thuoc("Glucophage XR", "Metformin hydrochloride", "500"),
                                      _thuoc("Jentadueto", "linagliptin / metformin", "501")),
         ecr.EC_KHONG_CON: _trang(_thuoc("Avandia", "Rosiglitazone", "137"),
                                  _thuoc("Avandamet", "rosiglitazone / metformin", "258"))}


def test_ec_nap_hai_trang_mot_trang_hong_la_ca_lan_hong():
    so = ecr.EcUnionRegisterClient(_HttpGia(text_theo_url=SO_EC)).nap()
    assert len(so["dang_luu_hanh"]) == 2 and len(so["khong_con"]) == 2
    hong = dict(SO_EC)
    hong[ecr.EC_KHONG_CON] = ConnectionError("mất mạng")
    with pytest.raises(ecr.EcLoi):
        ecr.EcUnionRegisterClient(_HttpGia(text_theo_url=hong)).nap()


# ═════════════ 6. EMA dự phòng qua sổ EC ═════════════

def _ema_chan(text_ec: Optional[Dict[str, Any]] = None) -> _HttpGia:
    return _HttpGia({EMA_URL: RuntimeError("[cloudfront-chan] HTTPError: 403 Client Error")},
                    text_theo_url=SO_EC if text_ec is None else text_ec)


def test_ema_bi_chan_thi_tra_so_ec_dang_luu_hanh_truoc_khong_con_sau():
    kq = EmaMedicinesClient(_ema_chan()).tra("metformin")
    assert kq["trang_thai"] == "co_ket_qua" and "DỰ PHÒNG" in kq["nguon"] and kq["du_phong"]["ly_do_ema"]
    assert [b["name_of_medicine"] for b in kq["ket_qua"]] == ["Glucophage XR", "Jentadueto", "Avandamet"]
    assert [b["medicine_status"] for b in kq["ket_qua"]][:2] == ["Authorised", "Authorised"]
    assert kq["ket_qua"][2]["medicine_status"] == ecr.TRANG_THAI_EC_KHONG_CON
    assert all(set(TRUONG_GIU) <= set(b) and b["nguon_ban_ghi"] == "EC Union Register" for b in kq["ket_qua"])
    assert kq["ket_qua"][2]["medicine_url"] == ecr.EC_SO_DANG_KY + "h258.htm"
    assert all(c in kq["canh_bao"] for c in ecr.CANH_BAO_EC)


def test_ema_bi_chan_khong_thay_trong_so_ec_van_kem_canh_bao():
    kq = EmaMedicinesClient(_ema_chan()).tra("zzzzqqqq")
    assert kq["trang_thai"] == "khong_thay" and any("TỪ CHỐI" in c for c in kq["canh_bao"])
    assert any("cấp phép quốc gia" in c for c in kq["canh_bao"])


def test_ema_va_so_ec_cung_hong_la_khong_biet_khong_phai_khong_thay():
    hong = {ecr.EC_DANG_LUU_HANH: ConnectionError("x"), ecr.EC_KHONG_CON: ConnectionError("x")}
    kq = EmaMedicinesClient(_ema_chan(hong)).tra("metformin")
    assert kq["trang_thai"] == "loi" and any("KHÔNG BIẾT" in c for c in kq["canh_bao"])
    assert "dự phòng EC Union Register cũng lỗi" in kq["ly_do"]


def test_ema_chay_duoc_thi_khong_cham_so_ec():
    class _EcCam:
        def nap(self):
            raise AssertionError("EMA chạy được mà vẫn gọi sổ EC")
    http = _HttpGia({EMA_URL: {"meta": {"timestamp": "t"}, "data": [
        {"category": "Human", "name_of_medicine": "Glucophage", "active_substance": "metformin",
         "medicine_status": "Authorised", "last_updated_date": "01/01/2026"}]}})
    kq = EmaMedicinesClient(http, ec=_EcCam()).tra("metformin")
    assert kq["trang_thai"] == "co_ket_qua" and "du_phong" not in kq


def test_ema_du_phong_khi_hoi_ca_thu_y_thi_noi_ro_khong_tra_thu_y():
    kq = EmaMedicinesClient(_ema_chan()).tra("metformin", ca_thu_y=True)
    assert any("thú y KHÔNG được tra" in c for c in kq["canh_bao"])


def test_cong_cu_tra_thuoc_in_dong_du_phong(capsys):
    spec = importlib.util.spec_from_file_location("tra_thuoc_test", ROOT / "tools" / "tra_thuoc_quoc_te.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._in_ema(EmaMedicinesClient(_ema_chan()).tra("rosiglitazone"))
    ra = capsys.readouterr().out
    assert "DỰ PHÒNG sổ EC" in ra and "Avandia" in ra and "h137.htm" in ra


# ═════════════ 7. Công cụ đo đường mạng biết các đường thay ═════════════

def test_cong_cu_do_mang_co_cac_duong_thay():
    spec = importlib.util.spec_from_file_location("do_mang_test", ROOT / "tools" / "do_mang_nguon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class _Cfg:
        ncbi_email = "x@example.org"
    ten = {d[0] for d in mod.danh_sach_diem(_Cfg())}
    assert {"WHO — API ấn phẩm (thay WHO IRIS)", "WHO — tin dịch DON (thay ECDC)",
            "Crossref — Eurosurveillance (thay ECDC)", "EC Union Register (thay EMA)"} <= ten
