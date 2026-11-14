"""feed_bjgp chuyển từ RSS bjgp.org sang Crossref theo ISSN (14/11/2026).

Bối cảnh: `tools/tu_de_xuat_viec.py` (repo gốc) báo «Nguồn feed_bjgp HỎNG KÉO DÀI: 6 lượt live liền từ 2026-10-29
(14 ngày, kiểu: cloudflare-chan)» — lượt vẫn PASS nên không tự lộ. `tools/do_mang_nguon.py` đo lại 14/11/2026: RSS
bjgp.org bị Cloudflare chặn, Crossref thông. ISSN điện tử 1478-5242 đối chiếu bằng api.crossref.org/journals/1478-5242
(«British Journal of General Practice», Royal College of General Practitioners; cùng bản ghi với ISSN in 0960-1643).

Các test này KHOÁ cấu hình mới, hoàn toàn ngoại tuyến (HTTP giả, không gọi mạng):
1. feed `bjgp` đi chế độ Crossref với đúng ISSN, giữ nguyên id/tên nguồn (SourceLog và sổ sức khoẻ nối tiếp được).
2. Lượt tìm CHỈ gọi Crossref (không còn chạm bjgp.org), lọc theo ngày Crossref nhận DOI và đúng loại bài.
3. Crossref lỗi ⇒ trả rỗng, KHÔNG bịa, KHÔNG quay lại RSS đang bị chặn.
4. Điểm đo của `tools/do_mang_nguon.py` đo ĐÚNG đường engine dùng (cùng ISSN với cấu hình).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.sources.feeds import GUIDELINE_FEEDS  # noqa: E402
from app.sources.rss_feed import RSSFeedClient  # noqa: E402

ISSN_BJGP = "1478-5242"
MOC = "2026-11-01"
CROSSREF_WORKS = "https://api.crossref.org/works"


def _feed_bjgp():
    ds = [f for f in GUIDELINE_FEEDS if f.id == "bjgp"]
    assert len(ds) == 1, "phải có ĐÚNG một feed id «bjgp»"
    return ds[0]


class HttpGia:
    """HTTP giả: ghi mọi lần gọi; `get_text` (đường RSS) mà bị gọi là lỗi — feed này không còn đọc RSS."""

    def __init__(self, items: Optional[List[Dict[str, Any]]] = None, loi: Optional[Exception] = None) -> None:
        self.items = items or []
        self.loi = loi
        self.calls: List[Dict[str, Any]] = []

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, **_kw: Any) -> Dict[str, Any]:
        self.calls.append({"url": url, "params": dict(params or {})})
        if self.loi is not None:
            raise self.loi
        return {"message": {"items": list(self.items), "total-results": len(self.items)}}

    def get_text(self, url: str, **_kw: Any) -> str:
        self.calls.append({"url": url, "params": {}})
        raise AssertionError(f"feed_bjgp không được đọc RSS nữa: {url}")


def _bai(doi: str, tieu_de: str, tao: str) -> Dict[str, Any]:
    return {"DOI": doi, "title": [tieu_de], "URL": f"https://doi.org/{doi.lower()}",
            "created": {"date-time": f"{tao}T12:00:00Z"}, "issued": {"date-parts": [[2026, 11, 2]]},
            "type": "journal-article", "ISSN": ["0960-1643", ISSN_BJGP], "abstract": "<jats:p>Tóm tắt giả.</jats:p>"}


def _client(http: HttpGia) -> RSSFeedClient:
    c = RSSFeedClient(_feed_bjgp())
    c.use_mock = False
    c.http = http
    return c


# ═════════════ 1. Cấu hình ═════════════

def test_feed_bjgp_lay_qua_crossref_theo_issn_dien_tu_va_giu_nguyen_ten_nguon():
    feed = _feed_bjgp()
    assert (feed.mode, feed.issn) == ("crossref", ISSN_BJGP)
    # Các thuộc tính khác giữ nguyên — chỉ đổi ĐƯỜNG lấy, không đổi danh tính nguồn.
    assert (feed.org, feed.kind, feed.clinical_area) == ("BJGP", "guideline", None)
    client = RSSFeedClient(feed)
    assert client.name == "feed_bjgp"
    # SourceLog ghi đúng nơi đã gọi, không phải URL RSS cũ đang bị Cloudflare chặn.
    assert client.endpoint == f"{CROSSREF_WORKS}?filter=issn:{ISSN_BJGP}"
    assert "bjgp.org" not in client.endpoint


# ═════════════ 2. Lượt tìm chỉ gọi Crossref ═════════════

def test_feed_bjgp_chi_goi_crossref_loc_theo_ngay_nhan_doi_va_loai_bai():
    http = HttpGia([_bai("10.3399/BJGP.2026.0018", "Bài BJGP giả số một", "2026-11-11"),
                    _bai("10.3399/bjgp.2026.0056", "Bài BJGP giả số hai", "2026-11-02")])
    recs = _client(http).search("", max_results=10, since_date=MOC)

    assert [c["url"] for c in http.calls] == [CROSSREF_WORKS], "chỉ MỘT lần gọi, và là Crossref"
    bo_loc = http.calls[0]["params"]["filter"].split(",")
    assert f"issn:{ISSN_BJGP}" in bo_loc
    assert f"from-created-date:{MOC}" in bo_loc
    assert "type:journal-article" in bo_loc
    assert (http.calls[0]["params"]["sort"], http.calls[0]["params"]["order"]) == ("created", "desc")

    assert [r.doi for r in recs] == ["10.3399/bjgp.2026.0018", "10.3399/bjgp.2026.0056"]
    for r in recs:
        assert r.source == "feed_bjgp"
        assert r.raw["_via"] == "crossref_issn" and r.raw["_feed"] == "bjgp"
        assert r.api_endpoint == f"{CROSSREF_WORKS}?filter=issn:{ISSN_BJGP}"
        assert r.journal_or_organization == "BJGP"
        assert r.abstract == "Tóm tắt giả."


# ═════════════ 3. Crossref lỗi ⇒ rỗng, không bịa, không quay về RSS ═════════════

@pytest.mark.parametrize("loi", [ConnectionError("mạng giả rớt"), TimeoutError("hết giờ giả")])
def test_feed_bjgp_crossref_loi_tra_rong_khong_bia_khong_quay_ve_rss(loi):
    http = HttpGia(loi=loi)
    assert _client(http).search("", max_results=10, since_date=MOC) == []
    assert [c["url"] for c in http.calls] == [CROSSREF_WORKS]


# ═════════════ 4. Công cụ đo mạng đo đúng đường engine dùng ═════════════

def _do_mang():
    spec = importlib.util.spec_from_file_location("do_mang_nguon_bjgp_test", ROOT / "tools" / "do_mang_nguon.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _diem_theo_ten(mod, cfg) -> Dict[str, Dict[str, Any]]:
    """Mở mỗi điểm đo `Diem` thành dict có TÊN trường để khẳng định theo tên, không theo chỉ số `d[2]`/`d[5]`.

    Thứ tự trường lấy đúng chú thích kiểu `Diem` ở `tools/do_mang_nguon.py`: (tên, nhóm, url, params, headers,
    mã HTTP coi là «tới được»). Mở bằng gán SÁU tên: thêm/bớt trường ở `Diem` ⇒ ValueError ngay tại đây, thay vì
    âm thầm so nhầm trường.
    """
    ket_qua: Dict[str, Dict[str, Any]] = {}
    for d in mod.danh_sach_diem(cfg):
        ten, nhom, url, params, headers, ma_toi_duoc = d
        ket_qua[ten] = {"nhom": nhom, "url": url, "params": params, "headers": headers, "ma_toi_duoc": ma_toi_duoc}
    return ket_qua


def test_do_mang_nguon_do_crossref_bjgp_cung_issn_voi_cau_hinh():
    class _Cfg:
        ncbi_email = "x@example.org"

    mod = _do_mang()
    diem = _diem_theo_ten(mod, _Cfg())
    crossref = diem.get("Crossref — BJGP (thay RSS)")
    assert crossref is not None, "thiếu điểm đo đường Crossref của feed_bjgp"
    # Cùng ISSN với cấu hình engine: đổi ISSN một nơi mà quên nơi kia thì test đỏ.
    assert crossref["url"] == f"https://api.crossref.org/journals/{_feed_bjgp().issn}/works"
    assert crossref["nhom"] == mod.NHOM_GUIDELINE
    # Một yêu cầu nhỏ, đi polite pool của Crossref (mailto) như mọi điểm Crossref khác; không header riêng.
    assert crossref["params"] == {"rows": "1", "mailto": "x@example.org"} and crossref["headers"] == {}
    # Chỉ HTTP 200 mới là «tới được»: 403 trang chặn Cloudflare mà lọt vào đây thì bộ đo báo xanh giả.
    assert crossref["ma_toi_duoc"] == (200,)
    # Đường RSS cũ vẫn được đo (biết khi nào thông lại) nhưng nhãn nói rõ engine không dùng nó nữa.
    rss = diem.get("BJGP — RSS (nay engine đọc qua Crossref)")
    assert rss is not None and rss["url"] == "https://bjgp.org/rss/current.xml"
    # Đo RSS bằng ĐÚNG User-Agent của engine — UA khác cho kết quả chặn/không chặn khác.
    assert rss["headers"] == {"User-Agent": mod.UA_ENGINE} and rss["ma_toi_duoc"] == (200,)
    assert rss["nhom"] == mod.NHOM_GUIDELINE
    assert "BJGP — RSS" not in diem
