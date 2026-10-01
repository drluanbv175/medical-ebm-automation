"""Mốc «bài mới» của lane Crossref/Europe PMC = ngày bản ghi XUẤT HIỆN trong chỉ mục, không phải ngày công bố.

Sự cố đo 30/09/2026 (VPN bật, máy Mac; số đo đầy đủ ở khối chú thích «MỐC BÀI MỚI» của
`app/sources/guideline_lanes.py`): lane `feed_lancet` chưa từng đưa bài nào vào kho, lane ACC/AHA trên JACC bỏ lọt
guideline 2026, lane Kidney Int/Gastroenterology/Ann Oncol «đứng hình» sau lượt đầu — mà SourceLog vẫn `ok`. Gốc: lượt
tuần lọc theo NGÀY CÔNG BỐ ≥ mốc, trong khi nhiều tạp chí chỉ khai ngày tới THÁNG (Crossref coi «2026-09» là 01/09) và
ngày SỐ PHÁT HÀNH tương lai thì lọt qua mọi mốc.

Test KHÔNG ghim chuỗi bộ lọc: `CrossrefGia` thi hành đúng ngữ nghĩa lọc/sắp của Crossref (đã đo bằng lời gọi thật cùng
ngày) trên một kho bài mẫu lấy từ các ca thật, nên mã quay về lọc theo ngày công bố là test đỏ vì HÀNH VI.
"""
from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.sources import guideline_lanes as gl  # noqa: E402
from app.sources.feeds import GUIDELINE_FEEDS, FeedConfig  # noqa: E402
from app.sources.rss_feed import RSSFeedClient  # noqa: E402

MOC_TUAN = "2026-09-19"          # đúng `since_date` của lượt tuần #44 (29/09/2026)


class _HomNay(date):
    """Đóng băng «hôm nay» = 30/09/2026 (ngày đo)."""

    @classmethod
    def today(cls):
        return cls(2026, 9, 30)


@pytest.fixture(autouse=True)
def _dong_bang_hom_nay(monkeypatch):
    monkeypatch.setattr(gl, "date", _HomNay)


def _bai(doi: str, tieu_de: str, cong_bo: Tuple[int, ...], tao: str, issn: str = "0140-6736",
         khoa_ngay: str = "issued") -> Dict[str, Any]:
    """Một bản ghi Crossref. `cong_bo` = date-parts như nhà xuất bản khai (2 phần tử = chỉ tới THÁNG)."""
    y, m, d = (int(x) for x in tao.split("-"))
    return {"DOI": doi, "title": [tieu_de], "URL": f"https://doi.org/{doi}", "ISSN": [issn], "type": "journal-article",
            khoa_ngay: {"date-parts": [list(cong_bo)]},
            "created": {"date-parts": [[y, m, d]], "date-time": f"{tao}T08:00:00Z"}}


# Kho mẫu dựng từ các ca thật đo 30/09/2026 (DOI rút gọn).
THANG_9_MOI = _bai("10.1016/lancet.moi", "Bài Lancet tháng 9, DOI đăng ký 25/09", (2026, 9), "2026-09-25")
THANG_9_CU = _bai("10.1016/lancet.cu", "Bài Lancet tháng 9, DOI đăng ký 05/09 (lượt trước)", (2026, 9), "2026-09-05")
SO_TUONG_LAI_CU = _bai("10.1016/ki.thang11.cu", "Bài số tháng 11, DOI đăng ký 20/08", (2026, 11), "2026-08-20")
SO_TUONG_LAI_MOI = _bai("10.1016/ki.thang11.moi", "Bài số tháng 11, DOI đăng ký 28/09", (2026, 11), "2026-09-28")
DU_NGAY = _bai("10.1056/nejm.du-ngay", "Bài khai đủ ngày 24/09", (2026, 9, 24), "2026-09-24",
               khoa_ngay="published-online")
HOI_TO = _bai("10.1016/lancet.1998", "Bài năm 1998 được cấp DOI muộn", (1998, 3), "2026-09-27")
GUIDELINE_JACC = _bai("10.1016/j.jacc.2026.06.017",
                      "2026 AHA/ACC Guideline for Perioperative Cardiovascular Management",
                      (2026, 9), "2026-09-23", issn="0735-1097")
KHO = [THANG_9_MOI, THANG_9_CU, SO_TUONG_LAI_CU, SO_TUONG_LAI_MOI, DU_NGAY, HOI_TO]


def _ngay_cong_bo(bai: Dict[str, Any]) -> Tuple[int, int, int]:
    """Crossref so ngày công bố khuyết phần bằng cách coi phần khuyết là 1 (đo thật: «2026-09» < 2026-09-22)."""
    for khoa in ("published-online", "issued", "published-print"):
        parts = ((bai.get(khoa) or {}).get("date-parts") or [[]])[0]
        if parts:
            y, m, d = (list(parts) + [1, 1])[:3]
            return (y, m, d)
    return (0, 1, 1)


def _so(ngay: str) -> Tuple[int, int, int]:
    y, m, d = (int(x) for x in ngay.split("-"))
    return (y, m, d)


class CrossrefGia:
    """Máy chủ Crossref giả: thi hành `filter` (issn · from-pub-date · from-created-date · type), `sort`, `rows`."""

    def __init__(self, kho: List[Dict[str, Any]]) -> None:
        self.kho = kho
        self.calls: List[Dict[str, Any]] = []

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, **_kw: Any) -> Dict[str, Any]:
        p = dict(params or {})
        self.calls.append({"url": url, "params": p})
        issn: List[str] = []
        giu = list(self.kho)
        for dk in str(p.get("filter") or "").split(","):
            ten, _, gia_tri = dk.partition(":")
            if ten == "issn":
                issn.append(gia_tri)
            elif ten == "from-pub-date":
                giu = [b for b in giu if _ngay_cong_bo(b) >= _so(gia_tri)]
            elif ten == "from-created-date":
                giu = [b for b in giu if b["created"]["date-time"][:10] >= gia_tri]
            elif ten == "type":
                giu = [b for b in giu if b.get("type") == gia_tri]
            elif ten:
                raise AssertionError(f"bộ lọc Crossref lạ: {dk!r}")
        if issn:
            giu = [b for b in giu if set(b.get("ISSN") or []) & set(issn)]
        sap = p.get("sort")
        if sap == "created":
            giu.sort(key=lambda b: b["created"]["date-time"], reverse=True)
        elif sap == "published":
            giu.sort(key=_ngay_cong_bo, reverse=True)
        tong = len(giu)
        return {"message": {"total-results": tong, "items": giu[: int(p.get("rows") or 20)]}}


def _client(monkeypatch, kho: List[Dict[str, Any]], **feed_kw: Any) -> Tuple[RSSFeedClient, CrossrefGia]:
    co = dict(id="lancet", name="The Lancet", url="https://api.crossref.org/journals/0140-6736", org="The Lancet",
              kind="guideline", clinical_area=None, issn="0140-6736", mode="crossref")
    co.update(feed_kw)
    client = RSSFeedClient(FeedConfig(**co))
    client.use_mock = False
    gia = CrossrefGia(kho)
    monkeypatch.setattr(client, "http", gia)
    return client, gia


def _doi(ds: List[Any]) -> List[str]:
    return [getattr(r, "doi", None) or r.get("doi") for r in ds]


# ═════════════════════════ đối chứng: máy chủ giả tái hiện đúng sự cố ═════════════════════════

def test_doi_chung_loc_theo_ngay_cong_bo_bo_sot_bai_chi_khai_thang_va_giu_mai_bai_so_tuong_lai():
    """Không gọi mã của hệ: chỉ xác nhận máy chủ giả cho ra đúng hiện tượng đã đo thật với bộ lọc CŨ."""
    gia = CrossrefGia(KHO)
    cu = gia.get_json("x", {"filter": f"issn:0140-6736,from-pub-date:{MOC_TUAN},type:journal-article",
                            "sort": "published", "order": "desc", "rows": 10})
    doi = [b["DOI"] for b in cu["message"]["items"]]
    assert THANG_9_MOI["DOI"] not in doi, "bài «2026-09» đăng ký 25/09 bị bộ lọc cũ loại (ca Lancet: 31 DOI mới ⇒ 0)"
    assert set(doi[:2]) == {SO_TUONG_LAI_CU["DOI"], SO_TUONG_LAI_MOI["DOI"]}, "bài số tháng 11 chiếm các chỗ đầu"
    assert SO_TUONG_LAI_CU["DOI"] in doi, "bài đăng ký từ 20/08 vẫn quay lại mỗi tuần (lane đứng hình)"


# ═════════════════════════ chế độ Crossref theo ISSN ═════════════════════════

def test_bai_chi_khai_ngay_toi_thang_van_duoc_thay_o_luot_ngay_sau_khi_no_xuat_hien(monkeypatch):
    client, _ = _client(monkeypatch, KHO)
    doi = _doi(client.search("", max_results=10, since_date=MOC_TUAN))
    assert THANG_9_MOI["DOI"] in doi
    assert doi == [SO_TUONG_LAI_MOI["DOI"], THANG_9_MOI["DOI"], DU_NGAY["DOI"]]      # mới đăng ký nhất đứng trước


def test_bai_da_xuat_hien_truoc_moc_khong_bi_tra_lai_moi_tuan(monkeypatch):
    """Bài số tháng 11 đăng ký từ 20/08 và bài tháng 9 đăng ký 05/09 thuộc các lượt TRƯỚC — không quay lại chiếm chỗ."""
    client, _ = _client(monkeypatch, KHO)
    doi = _doi(client.search("", max_results=10, since_date=MOC_TUAN))
    assert SO_TUONG_LAI_CU["DOI"] not in doi and THANG_9_CU["DOI"] not in doi


def test_so_cho_cua_luot_thuoc_ve_bai_vua_xuat_hien_khong_thuoc_ve_ngay_phat_hanh_xa_nhat(monkeypatch):
    client, gia = _client(monkeypatch, KHO)
    doi = _doi(client.search("", max_results=2, since_date=MOC_TUAN))
    assert doi == [SO_TUONG_LAI_MOI["DOI"], THANG_9_MOI["DOI"]]
    assert gia.calls[0]["params"]["rows"] == 2


def test_bai_cu_duoc_cap_doi_muon_khong_bi_coi_la_bai_moi(monkeypatch):
    client, _ = _client(monkeypatch, KHO)
    assert HOI_TO["DOI"] not in _doi(client.search("", max_results=10, since_date=MOC_TUAN))
    # San chong hoi to la dau NAM TRUOC cua moc: bai cong bo 12/2025 dang ky muon van la bai moi hop le.
    thang_12 = _bai("10.1016/lancet.2025-12", "Bài tháng 12/2025 đăng ký muộn", (2025, 12), "2026-09-26")
    client, _ = _client(monkeypatch, KHO + [thang_12])
    assert thang_12["DOI"] in _doi(client.search("", max_results=10, since_date=MOC_TUAN))


def test_ngay_so_phat_hanh_tuong_lai_hien_bang_ngay_dang_ky_khong_bia_ngay(monkeypatch):
    client, _ = _client(monkeypatch, KHO)
    theo_doi = {r.doi: r for r in client.search("", max_results=10, since_date=MOC_TUAN)}
    assert theo_doi[SO_TUONG_LAI_MOI["DOI"]].publication_date == "2026-09-28"     # «2026-11» là ngày chưa tới
    assert theo_doi[THANG_9_MOI["DOI"]].publication_date == "2026-09"              # chỉ biết tới tháng: giữ nguyên
    assert theo_doi[DU_NGAY["DOI"]].publication_date == "2026-09-24"


def test_khong_co_moc_thi_nhin_lui_45_ngay_theo_ngay_dang_ky(monkeypatch):
    client, _ = _client(monkeypatch, KHO)
    doi = _doi(client.search("", max_results=10))                 # 30/09 − 45 ngày = 16/08
    assert set(doi) == {SO_TUONG_LAI_MOI["DOI"], THANG_9_MOI["DOI"], DU_NGAY["DOI"], THANG_9_CU["DOI"],
                        SO_TUONG_LAI_CU["DOI"]}


@pytest.mark.parametrize("moc_hong", ["", "hôm qua", "2026/09/19", "19-09-2026"])
def test_moc_sai_dinh_dang_thi_lui_ve_cua_so_mac_dinh_khong_nem_loi(monkeypatch, moc_hong):
    client, gia = _client(monkeypatch, KHO)
    client.search("", max_results=10, since_date=moc_hong)
    assert "from-created-date:2026-08-16" in gia.calls[0]["params"]["filter"]


def test_lane_bi_cat_thi_noi_ra_trong_nhat_ky(monkeypatch, caplog):
    client, _ = _client(monkeypatch, KHO)
    with caplog.at_level(logging.INFO):
        client.search("", max_results=2, since_date=MOC_TUAN)
    dong = [r.getMessage() for r in caplog.records if "BỊ CẮT" in r.getMessage()]
    assert len(dong) == 1 and "có 3 bản ghi mới" in dong[0] and "lane lấy 2" in dong[0] and MOC_TUAN in dong[0]
    caplog.clear()
    with caplog.at_level(logging.INFO):
        client.search("", max_results=10, since_date=MOC_TUAN)
    assert not [r for r in caplog.records if "BỊ CẮT" in r.getMessage()], "lấy đủ thì không được báo bị cắt"


# ═════════════════════════ lane Crossref theo tiêu đề ═════════════════════════

def test_lane_hiep_hoi_tren_tap_chi_chi_khai_thang_bat_duoc_guideline_moi():
    gia = CrossrefGia(KHO + [GUIDELINE_JACC])
    muc = gl.crossref_title_lane(gia, ["0735-1097", "1558-3597"], "ACC AHA guideline", r"\b(?:ACC|AHA)\b", 10,
                                 since_date=MOC_TUAN)
    assert _doi(muc) == [GUIDELINE_JACC["DOI"]]
    assert muc[0]["date"] == "2026-09" and muc[0]["guideline"] is True


def test_lane_acc_aha_jacc_that_trong_cau_hinh_bat_duoc_guideline_qua_rssfeedclient(monkeypatch):
    feed = next(f for f in GUIDELINE_FEEDS if f.id == "acc_aha_jacc")
    client = RSSFeedClient(feed)
    client.use_mock = False
    monkeypatch.setattr(client, "http", CrossrefGia(KHO + [GUIDELINE_JACC]))
    (r,) = client.search("", max_results=10, since_date=MOC_TUAN)
    assert r.doi == GUIDELINE_JACC["DOI"] and r.source == "feed_acc_aha_jacc"


# ═════════════════════════ Europe PMC ═════════════════════════

class EpmcGia:
    def __init__(self, *ket_qua: Dict[str, Any], tong: Optional[int] = None) -> None:
        self.ket_qua, self.tong, self.calls = list(ket_qua), tong, []

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, **_kw: Any) -> Dict[str, Any]:
        self.calls.append({"url": url, "params": dict(params or {})})
        return {"hitCount": self.tong if self.tong is not None else len(self.ket_qua),
                "resultList": {"result": self.ket_qua}}


def test_europepmc_hoi_ca_bai_cong_bo_lan_bai_vao_chi_muc_tu_moc_va_co_san_chong_hoi_to():
    http = EpmcGia()
    gl.europepmc_lane(http, 'PUB_TYPE:"Practice Guideline"', 10, since_date=MOC_TUAN)
    q = http.calls[0]["params"]["query"]
    assert "FIRST_IDATE:[2026-09-19 TO 2026-09-30]" in q, "bài vào chỉ mục TRỄ hơn ngày công bố phải được hỏi tới"
    assert "FIRST_PDATE:[2026-09-19 TO 2026-09-30] OR FIRST_IDATE:" in q, "hai mốc là HOẶC, không phải VÀ"
    assert q.endswith("AND FIRST_PDATE:[2025-01-01 TO 3000-12-31]")


def test_europepmc_ngay_tuong_lai_thay_bang_ngay_vao_chi_muc_con_ngay_da_qua_giu_nguyen():
    """Ca thật 30/09: guideline EASL–EASD–EASO vào chỉ mục 29/09 mang ngày công bố 01/12/2026."""
    http = EpmcGia(
        {"title": "EASL-EASD-EASO Guidance", "pmid": "42805503", "source": "MED", "id": "42805503",
         "firstPublicationDate": "2026-12-01", "firstIndexDate": "2026-09-29"},
        {"title": "WHO guideline vào chỉ mục trễ", "pmid": "42777103", "source": "MED", "id": "42777103",
         "firstPublicationDate": "2025-01-01", "firstIndexDate": "2026-09-28"},
        {"title": "Ngày tương lai mà thiếu ngày vào chỉ mục", "pmid": "1", "source": "MED", "id": "1",
         "firstPublicationDate": "2026-11-27"},
        {"title": "Không có ngày nào", "pmid": "2", "source": "MED", "id": "2"})
    ngay = {m["pmid"]: m["date"] for m in gl.europepmc_lane(http, "q", 10, since_date=MOC_TUAN, guideline=True)}
    assert ngay == {"42805503": "2026-09-29", "42777103": "2025-01-01", "1": "2026-11-27", "2": None}


def test_europepmc_bi_cat_thi_noi_ra(caplog):
    http = EpmcGia({"title": "Một guideline", "pmid": "9", "source": "MED", "id": "9",
                    "firstPublicationDate": "2026-09-25"}, tong=75)
    with caplog.at_level(logging.INFO):
        gl.europepmc_lane(http, 'PUB_TYPE:"Practice Guideline"', 50, since_date=MOC_TUAN)
    assert [r for r in caplog.records if "BỊ CẮT" in r.getMessage() and "có 75 bản ghi mới" in r.getMessage()]


# ═════════════════════════ cấu hình: NEJM ═════════════════════════

def test_feed_nejm_lay_qua_crossref_theo_issn_dien_tu_va_giu_nguyen_ten_nguon():
    feed = next(f for f in GUIDELINE_FEEDS if f.id == "nejm_current")
    assert (feed.mode, feed.issn) == ("crossref", "1533-4406")
    client = RSSFeedClient(feed)
    # Tên nguồn không đổi: SourceLog, authority.EVIDENCE_SOURCE_UNIVERSE («feed_nejm_current») vẫn khớp.
    assert client.name == "feed_nejm_current"
    assert client.endpoint == "https://api.crossref.org/works?filter=issn:1533-4406"


def test_moi_lane_crossref_trong_cau_hinh_deu_hoi_theo_ngay_dang_ky(monkeypatch):
    """Không lane nào còn đi đường cũ: quét MỌI feed/lane chế độ Crossref của cấu hình thật."""
    ds = [f for f in GUIDELINE_FEEDS if f.mode in ("crossref", "crossref_title")]
    assert len(ds) >= 50
    for f in ds:
        client = RSSFeedClient(f)
        client.use_mock = False
        gia = CrossrefGia([])
        monkeypatch.setattr(client, "http", gia)
        client.search("", max_results=10, since_date=MOC_TUAN)
        bo_loc = gia.calls[0]["params"]["filter"].split(",")
        assert f"from-created-date:{MOC_TUAN}" in bo_loc, f.id
        assert f"from-pub-date:{MOC_TUAN}" not in bo_loc, f"{f.id}: còn lọc theo ngày công bố ≥ mốc"
