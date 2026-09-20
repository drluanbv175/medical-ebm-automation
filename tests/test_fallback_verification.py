"""Kiểm lớp XÁC MINH của nhánh dự phòng (`app/services/fallback_verification.py`) — thêm 20/09/2026.

Bộ test này do một tác giả ĐỘC LẬP viết từ HỢP ĐỒNG (CONTRACT), BẢN ĐỒ MÃ (CODE MAP) và các SỰ KIỆN SCITE của giai
đoạn nghiên cứu, KHÔNG đọc mã cài đặt, để bắt lệch giữa "điều đã hứa" và "điều đã làm".

`xac_minh_ban_ghi(rec)` quyết định một phát hiện của Consensus / SerpApi Scholar có được GIỮ hay không. Nguyên tắc
canh chặt (FAIL-CLOSED, "im lặng khác an toàn"):

  * chỉ giữ khi CƠ QUAN ĐĂNG KÝ xác nhận: (a) DOI có thật ở Crossref và tiêu đề khớp (>= 0.9 sau chuẩn hoá); hoặc
    (b) không DOI nhưng có ĐÚNG MỘT ứng viên Crossref rõ ràng nhất (tiêu đề khớp, |lệch năm| <= 1 khi biết năm, họ tác
    giả đầu có trong danh sách khi biết tác giả); hoặc (c) PMID từ link PubMed được PubMed xác nhận có tồn tại;
  * bản ghi trả về là bản ghi CỦA CƠ QUAN ĐĂNG KÝ (không phải bản của tầng dự phòng), kèm dấu vết nguồn phát hiện;
  * tiêu đề chỉ GẦN GIỐNG (khác đối tượng, Phần I/II, Erratum, Correction, Retraction Note), DOI ma, DOI trỏ sang bài
    khác, nhiều ứng viên ngang nhau, lệch năm/tác giả => KHÔNG giữ; lỗi mạng/JSON hỏng => `loi_xac_minh` (KHÁC
    `khong_khop`, và tuyệt đối không bao giờ thành "khớp");
  * TỐI ĐA 2 lời gọi cơ quan đăng ký cho mỗi phát hiện;
  * CỔNG RÚT BÀI / THÔNG BÁO cho mọi phát hiện có DOI đã xác nhận: Crossref (nguyên liệu `CrossrefRetraction` có sẵn)
    HOẶC Scite (`retracted`, `editorialNotices`) báo rút => `bi_rut_bai` và bản ghi bị BỎ; đính chính / expression of
    concern => giữ + cờ `co_thong_bao_bien_tap`; thông báo không phân loại được => giữ + cờ
    `thong_bao_bien_tap_chua_phan_loai`. Tally của Scite CHỈ được ghi nhận (`raw["scite"]`) và cờ
    `nhieu_trich_dan_phan_bac` (phản bác >= 3 và > ủng hộ); không bao giờ đổi điểm/tier/lọc bản ghi. Scite hỏng =>
    `raw["scite"]["da_kiem"] is False`, tuyệt đối không tuyên bố đã kiểm.

Mọi test OFFLINE. Vì hợp đồng KHÔNG quy định giao diện của `crossref_client` / `pubmed_client` tiêm vào, các cơ quan
đăng ký được giả ở tầng VẬN CHUYỂN (`requests.Session.request` và `urllib.request.urlopen`, định tuyến theo host/đường
dẫn công khai của Crossref, NCBI E-utilities và api.scite.ai): test đúng với mọi cách cài đặt. Socket bị chặn.
Dữ liệu là
DỮ LIỆU GIẢ RÕ RÀNG (DOI tiền tố 10.5555, tác giả/tạp chí giả) — không phải bài báo thật.
"""
from __future__ import annotations

import copy
import io
import json
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.services.fallback_verification as fv  # noqa: E402
from app.config import settings  # noqa: E402
from app.services.fallback_verification import KetQuaXacMinh, xac_minh_ban_ghi  # noqa: E402
from app.services.normalization import normalize  # noqa: E402
from app.services.pipeline import score_item  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402
from app.utils import http as http_mod  # noqa: E402

TANG_DU_PHONG = {"consensus", "serpapi_scholar"}
VOCAB_KET_QUA = {"xac_minh_duoc", "khong_khop", "mo_ho", "loi_xac_minh", "bi_rut_bai"}

TIEU_DE = "Effect of dapagliflozin on renal outcomes in adults with chronic kidney disease: a meta-analysis"
DOI = "10.5555/fake.fallback.001"
TAC_GIA_HIT = "Alice Nguyen, Bob Tran"
TAP_CHI = "Fake Journal of Nephrology"


# ════════════════════════════════════════════════════════════════════════════
# Cơ quan đăng ký GIẢ ở tầng vận chuyển
# ════════════════════════════════════════════════════════════════════════════

def _msg_crossref(doi: str, tieu_de: str, *, nam: int = 2021, tac_gia=(("Alice", "Nguyen"), ("Bob", "Tran")),
                  loai: str = "journal-article", updated_by: Optional[List[dict]] = None) -> Dict[str, Any]:
    """Phần `message` của một bản ghi Crossref (cấu trúc công khai của Crossref REST API; dữ liệu giả)."""
    m: Dict[str, Any] = {
        "DOI": doi, "title": [tieu_de], "type": loai, "container-title": [TAP_CHI], "publisher": "Fake Press",
        "issued": {"date-parts": [[nam, 5, 1]]},
        "published": {"date-parts": [[nam, 5, 1]]},
        "author": [{"given": g, "family": f, "sequence": "first" if i == 0 else "additional"}
                   for i, (g, f) in enumerate(tac_gia)],
        "score": 90.0,
    }
    if updated_by is not None:
        m["updated-by"] = updated_by
    return m


def _xml_pubmed(pmid: str, tieu_de: str, *, nam: str = "2021", doi: Optional[str] = None) -> str:
    """XML efetch tối giản theo cấu trúc PubMed (dữ liệu giả)."""
    id_doi = f'<ArticleId IdType="doi">{doi}</ArticleId>' if doi else ""
    elocation = f'<ELocationID EIdType="doi" ValidYN="Y">{doi}</ELocationID>' if doi else ""
    return (
        '<?xml version="1.0" ?>\n<PubmedArticleSet>\n<PubmedArticle><MedlineCitation Status="MEDLINE">'
        f'<PMID Version="1">{pmid}</PMID><Article><Journal><Title>{TAP_CHI}</Title><JournalIssue>'
        f'<PubDate><Year>{nam}</Year></PubDate></JournalIssue></Journal><ArticleTitle>{tieu_de}</ArticleTitle>'
        f'{elocation}<AuthorList><Author><LastName>Nguyen</LastName><Initials>A</Initials></Author></AuthorList>'
        '<PublicationTypeList><PublicationType UI="D016428">Journal Article</PublicationType></PublicationTypeList>'
        f'</Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="pubmed">{pmid}</ArticleId>'
        f'{id_doi}</ArticleIdList></PubmedData></PubmedArticle>\n</PubmedArticleSet>\n'
    )


def _bai_scite(doi: str, **ghi_de: Any) -> Dict[str, Any]:
    """Phản hồi `GET /papers/{doi}` của Scite theo ví dụ tài liệu (dữ liệu giả)."""
    bai: Dict[str, Any] = {
        "id": 1, "doi": doi, "slug": "fake", "type": "journal-article", "title": TIEU_DE, "abstract": "Fake.",
        "authors": [{"family": "Nguyen", "given": "Alice", "authorSequenceNumber": 1}], "keywords": ["Article"],
        "year": 2021, "shortJournal": "FJN", "publisher": "Fake Press", "issue": "1", "volume": "1", "page": "1-9",
        "retracted": False, "memberId": 1, "issns": ["0000-0000"], "editorialNotices": [], "journal": TAP_CHI,
        "preprintLinks": [], "publicationLinks": [], "normalizedTypes": ["article"],
    }
    bai.update(ghi_de)
    return bai


def _tally_scite(doi: str, *, ung_ho: int = 5, phan_bac: int = 0, de_cap: int = 20) -> Dict[str, Any]:
    return {"total": ung_ho + phan_bac + de_cap, "supporting": ung_ho, "contradicting": phan_bac, "mentioning": de_cap,
            "unclassified": 0, "doi": doi, "citingPublications": ung_ho + phan_bac + de_cap}


class _PhanHoi:
    """Giả `requests.Response`."""

    def __init__(self, status_code: int, text: str, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers: Dict[str, str] = dict(headers or {})
        self.url = url
        self.reason = "reason"
        self.ok = status_code < 400
        self.encoding = "utf-8"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} Error: reason for url: {self.url}")
            err.response = self  # type: ignore[assignment]
            raise err

    def json(self) -> Any:
        return json.loads(self.text)


class _UrlopenPhanHoi(io.BytesIO):
    """Giả đối tượng trả về của `urllib.request.urlopen` (dùng được như context manager)."""

    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False


class CoQuanGia:
    """Ghi lại MỌI lời gọi rời máy rồi trả phản hồi theo kịch bản. Host lạ bị ghi vào `ngoai_le` (test kiểm ở cuối)."""

    def __init__(self) -> None:
        self.crossref_doi: Dict[str, Any] = {}    # doi(thường) -> dict `message` | int HTTP status | Exception
        self.crossref_tim: Any = []               # list `message` ứng viên | int HTTP status | Exception
        self.pubmed: Dict[str, str] = {}          # pmid -> xml bản ghi
        self.pubmed_loi: Any = None               # Exception hoặc int HTTP status cho MỌI lời gọi NCBI
        self.crossref_loi: Any = None             # Exception hoặc int HTTP status cho MỌI lời gọi Crossref
        self.scite_bai: Dict[str, Any] = {}       # doi -> dict | int | Exception  (mặc định: bài sạch)
        self.scite_tally: Dict[str, Any] = {}
        self.scite_loi: Any = None                # Exception hoặc int HTTP status cho MỌI lời gọi Scite
        self.scite_bai_rong = False               # True => /papers/ trả JSON hỏng
        self.calls: List[Dict[str, Any]] = []
        self.ngoai_le: List[str] = []

    # -- thống kê -----------------------------------------------------------------------------
    def goi_dang_ky(self) -> List[Dict[str, Any]]:
        return [c for c in self.calls if c["host"] in {"api.crossref.org", "eutils.ncbi.nlm.nih.gov"}
                or c["host"].endswith("europepmc.org") or c["host"].endswith("ebi.ac.uk")]

    def goi_scite(self) -> List[Dict[str, Any]]:
        return [c for c in self.calls if c["host"] == "api.scite.ai"]

    # -- định tuyến ---------------------------------------------------------------------------
    def _xu_ly(self, url: str, params: Optional[dict], headers: Dict[str, str]):
        """Trả (status, text, headers) hoặc ném Exception."""
        u = urlparse(url)
        tham_so = {k: v[-1] for k, v in parse_qs(u.query).items()}
        tham_so.update({str(k): str(v) for k, v in dict(params or {}).items()})
        host = (u.hostname or "").lower()
        duong = unquote(u.path)
        self.calls.append({"host": host, "path": duong, "params": tham_so, "url": url,
                           "headers": {str(k).lower(): str(v) for k, v in headers.items()}})
        if host == "api.crossref.org":
            return self._crossref(duong, tham_so)
        if host == "eutils.ncbi.nlm.nih.gov":
            return self._ncbi(duong, tham_so)
        if host == "api.scite.ai":
            return self._scite(duong)
        if host.endswith("europepmc.org") or host.endswith("ebi.ac.uk"):
            return 200, json.dumps({"hitCount": 0, "resultList": {"result": []}}), {}
        self.ngoai_le.append(f"host ngoài hợp đồng: {url}")
        raise AssertionError(f"host ngoài hợp đồng: {url}")

    def _crossref(self, duong: str, tham_so: Dict[str, str]):
        if isinstance(self.crossref_loi, BaseException):
            raise self.crossref_loi
        if isinstance(self.crossref_loi, int):
            return self.crossref_loi, json.dumps({"status": "failed"}), {}
        if duong.startswith("/works/") and len(duong) > len("/works/"):
            doi = duong[len("/works/"):].lower()
            muc = self.crossref_doi.get(doi)
            if isinstance(muc, BaseException):
                raise muc
            if isinstance(muc, int):
                return muc, "Resource not found." if muc == 404 else "error", {}
            if muc is None:
                return 404, "Resource not found.", {}
            if muc == "json_hong":
                return 200, "<html>khong phai json</html>", {}
            return 200, json.dumps({"status": "ok", "message-type": "work", "message-version": "1.0.0",
                                    "message": muc}, ensure_ascii=False), {}
        if duong.rstrip("/") == "/works":
            if isinstance(self.crossref_tim, BaseException):
                raise self.crossref_tim
            if isinstance(self.crossref_tim, int):
                return self.crossref_tim, "error", {}
            if self.crossref_tim == "json_hong":
                return 200, "<html>khong phai json</html>", {}
            items = list(self.crossref_tim)
            return 200, json.dumps({"status": "ok", "message-type": "work-list", "message-version": "1.0.0",
                                    "message": {"total-results": len(items), "items": items,
                                                "items-per-page": max(1, len(items)),
                                                "query": {"start-index": 0}}}, ensure_ascii=False), {}
        self.ngoai_le.append(f"đường dẫn Crossref ngoài hợp đồng: {duong}")
        raise AssertionError(f"đường dẫn Crossref ngoài hợp đồng: {duong}")

    def _ncbi(self, duong: str, tham_so: Dict[str, str]):
        if isinstance(self.pubmed_loi, BaseException):
            raise self.pubmed_loi
        if isinstance(self.pubmed_loi, int):
            return self.pubmed_loi, "error", {}
        if duong.endswith("efetch.fcgi"):
            ids = [p.strip() for p in str(tham_so.get("id", "")).split(",") if p.strip()]
            khung = '<?xml version="1.0" ?>\n<PubmedArticleSet>\n{}\n</PubmedArticleSet>\n'
            phan = []
            for pmid in ids:
                xml = self.pubmed.get(pmid)
                if xml:
                    than = re.search(r"<PubmedArticle>.*</PubmedArticle>", xml, flags=re.S)
                    phan.append(than.group(0) if than else "")
            return 200, khung.format("\n".join(phan)), {}
        if duong.endswith("esummary.fcgi"):
            ids = [p.strip() for p in str(tham_so.get("id", "")).split(",") if p.strip()]
            ket = {"uids": [i for i in ids if i in self.pubmed]}
            for i in ket["uids"]:
                ket[i] = {"uid": i}
            return 200, json.dumps({"result": ket}), {}
        if duong.endswith("esearch.fcgi"):
            return 200, json.dumps({"esearchresult": {"count": "0", "idlist": []}}), {}
        self.ngoai_le.append(f"đường dẫn NCBI ngoài hợp đồng: {duong}")
        raise AssertionError(f"đường dẫn NCBI ngoài hợp đồng: {duong}")

    def _scite(self, duong: str):
        if isinstance(self.scite_loi, BaseException):
            raise self.scite_loi
        if isinstance(self.scite_loi, int):
            return self.scite_loi, json.dumps({"detail": "loi"}), {}
        if duong.startswith("/papers/"):
            doi = duong[len("/papers/"):]
            if self.scite_bai_rong:
                return 200, "<html>khong phai json</html>", {}
            muc = self.scite_bai.get(doi.lower(), _bai_scite(doi))
            if isinstance(muc, BaseException):
                raise muc
            if isinstance(muc, int):
                return muc, json.dumps({"detail": "x"}), {}
            return 200, json.dumps(muc, ensure_ascii=False), {}
        if duong.startswith("/tallies/"):
            doi = duong[len("/tallies/"):]
            muc = self.scite_tally.get(doi.lower(), _tally_scite(doi))
            if isinstance(muc, BaseException):
                raise muc
            if isinstance(muc, int):
                return muc, json.dumps({"detail": "x"}), {}
            return 200, json.dumps(muc, ensure_ascii=False), {}
        self.ngoai_le.append(f"đường dẫn Scite ngoài hợp đồng: {duong}")
        raise AssertionError(f"đường dẫn Scite ngoài hợp đồng: {duong}")

    # -- hai tầng vận chuyển ------------------------------------------------------------------
    def requests_request(self, session, method, url, params=None, timeout=None, **kw):
        tieu_de = {str(k): str(v) for k, v in dict(session.headers).items()}
        tieu_de.update({str(k): str(v) for k, v in dict(kw.get("headers") or {}).items()})
        status, text, hdr = self._xu_ly(url, params, tieu_de)
        return _PhanHoi(status, text, url, hdr)

    def urlopen(self, req, data=None, timeout=None, *a, **kw):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        tieu_de = dict(getattr(req, "headers", {}) or {})
        status, text, hdr = self._xu_ly(url, None, tieu_de)
        if status >= 400:
            raise urllib.error.HTTPError(url, status, "loi", hdr, io.BytesIO(text.encode("utf-8")))  # type: ignore[arg-type]
        return _UrlopenPhanHoi(text.encode("utf-8"))


@pytest.fixture()
def dk(monkeypatch, tmp_path):
    """Cô lập hoàn toàn: không mạng thật, không cache đĩa, không ngủ thật, không retry; cờ live + Scite bật."""
    monkeypatch.setattr(settings, "use_mock_sources", False)
    monkeypatch.setattr(settings, "enable_scite_verification", True)
    monkeypatch.setattr(settings, "fallback_keep_unverified", False)
    monkeypatch.setattr(settings, "ncbi_email", "tester@example.org")
    monkeypatch.setattr(settings, "ncbi_api_key", "")
    monkeypatch.setattr(settings, "openalex_email", "tester@example.org")
    monkeypatch.setattr(settings, "http_max_retries", 0)
    monkeypatch.setattr(settings, "http_cache_ttl", 0)
    monkeypatch.setattr(settings, "http_min_interval", 0)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    import time
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    def _cam(*_a, **_k):
        raise AssertionError("test xác minh KHÔNG được mở kết nối mạng thật")

    monkeypatch.setattr(socket.socket, "connect", _cam)
    monkeypatch.setattr(socket.socket, "connect_ex", _cam)

    co_quan = CoQuanGia()
    monkeypatch.setattr(requests.Session, "request",
                        lambda self, method, url, params=None, timeout=None, **kw:
                        co_quan.requests_request(self, method, url, params, timeout, **kw))
    monkeypatch.setattr(urllib.request, "urlopen", co_quan.urlopen)
    yield co_quan
    assert co_quan.ngoai_le == [], f"có lời gọi ngoài hợp đồng: {co_quan.ngoai_le}"


# ════════════════════════════════════════════════════════════════════════════
# Helper
# ════════════════════════════════════════════════════════════════════════════

def _hit(nguon: str = "consensus", *, tieu_de: str = TIEU_DE, doi: Optional[str] = DOI, pmid: Optional[str] = None,
         tac_gia: Optional[str] = TAC_GIA_HIT, nam: Optional[str] = "2021", url: Optional[str] = None,
         study_type: Optional[str] = None, abstract: Optional[str] = None,
         raw: Optional[Dict[str, Any]] = None) -> RawRecord:
    return RawRecord(source=nguon, title=tieu_de, authors=tac_gia, publication_date=nam, doi=doi, pmid=pmid, url=url,
                     journal_or_organization=TAP_CHI, study_type=study_type, abstract=abstract, raw=dict(raw or {}))


def _dang_ky_doi(co_quan: CoQuanGia, doi: str = DOI, tieu_de: str = TIEU_DE, **kw: Any) -> None:
    co_quan.crossref_doi[doi.lower()] = _msg_crossref(doi, tieu_de, **kw)


def _xm(co_quan: CoQuanGia, rec: RawRecord, *, toi_da_goi: int = 2, **kw: Any) -> KetQuaXacMinh:
    """Gọi `xac_minh_ban_ghi` và kiểm luôn các bất biến chung: vocab, tối đa 2 lời gọi cơ quan đăng ký, không đổi đầu vào."""
    truoc = copy.deepcopy(rec.to_dict())
    kq = xac_minh_ban_ghi(rec, **kw)
    assert isinstance(kq, KetQuaXacMinh)
    assert kq.ket_qua in VOCAB_KET_QUA, kq.ket_qua
    if kq.ket_qua == "xac_minh_duoc":
        assert isinstance(kq.ban_ghi, RawRecord)
    else:
        assert kq.ban_ghi is None or kq.ban_ghi.raw.get("chua_xac_minh") is True, \
            "bản ghi không được xác minh chỉ được trả về khi được gắn cờ chua_xac_minh"
    assert len(co_quan.goi_dang_ky()) <= toi_da_goi, \
        f"quá {toi_da_goi} lời gọi cơ quan đăng ký cho MỘT phát hiện: {[c['url'] for c in co_quan.goi_dang_ky()]}"
    assert rec.to_dict() == truoc, "xac_minh_ban_ghi không được sửa bản ghi đầu vào"
    return kq


def _khong_giu(kq: KetQuaXacMinh, cho_phep=("khong_khop", "mo_ho")) -> None:
    assert kq.ket_qua in cho_phep, kq.ket_qua
    assert kq.ban_ghi is None


def _co(rec: RawRecord) -> List[str]:
    co = rec.raw.get("co")
    if co is None:
        return []
    return [co] if isinstance(co, str) else [str(x) for x in co]


def _so_duoc(x: Any) -> List[float]:
    """Mọi giá trị số (không phải bool) lồng trong một cấu trúc — dùng tìm độ giống trong `raw["xac_minh"]`."""
    ra: List[float] = []
    if isinstance(x, dict):
        for v in x.values():
            ra += _so_duoc(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            ra += _so_duoc(v)
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        ra.append(float(x))
    return ra


def _nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


# ════════════════════════════════════════════════════════════════════════════
# (a) DOI có thật ở Crossref và tiêu đề khớp => giữ BẢN GHI CỦA CƠ QUAN ĐĂNG KÝ
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("nguon", ["consensus", "serpapi_scholar"])
def test_doi_hit_with_matching_crossref_title_is_kept_as_the_registry_record(dk, nguon):
    _dang_ky_doi(dk)
    kq = _xm(dk, _hit(nguon))
    assert kq.ket_qua == "xac_minh_duoc"
    ban = kq.ban_ghi
    assert ban.doi is not None and ban.doi.lower() == DOI
    assert ban.title == TIEU_DE
    assert ban.source not in TANG_DU_PHONG, "tầng dự phòng không được tự bảo chứng: bản ghi phải là của cơ quan đăng ký"
    assert ban.raw.get("phat_hien_boi") == nguon, "phải giữ dấu vết ai đã PHÁT HIỆN"
    assert not ban.raw.get("_mock")


def test_registry_owns_the_kept_title_not_the_hits_variant(dk):
    tieu_de_hit = "EFFECT OF DAPAGLIFLOZIN ON RENAL OUTCOMES IN ADULTS WITH CHRONIC KIDNEY DISEASE - A META ANALYSIS"
    _dang_ky_doi(dk)
    kq = _xm(dk, _hit(tieu_de=tieu_de_hit))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.title == TIEU_DE, "giữ tiêu đề CỦA CƠ QUAN ĐĂNG KÝ, không phải biến thể của tầng dự phòng"


def test_evidence_dict_records_how_it_was_verified(dk):
    _dang_ky_doi(dk)
    ban = _xm(dk, _hit()).ban_ghi
    bang_chung = ban.raw.get("xac_minh")
    assert isinstance(bang_chung, dict) and len(bang_chung) >= 2
    assert DOI in json.dumps(bang_chung, ensure_ascii=False).lower(), "phải ghi DOI đã đối chiếu"
    do_giong = [x for x in _so_duoc(bang_chung) if 0.0 <= x <= 1.0]
    assert do_giong and max(do_giong) >= 0.9, f"phải ghi độ giống tiêu đề (>= 0.9): {bang_chung}"


@pytest.mark.parametrize("dang_doi", [DOI.upper(), f"https://doi.org/{DOI}", f"doi:{DOI}", f"  {DOI}  "])
def test_doi_written_in_other_forms_is_normalized_before_lookup(dk, dang_doi):
    _dang_ky_doi(dk)
    kq = _xm(dk, _hit(doi=dang_doi))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.doi.lower() == DOI


def test_doi_carried_in_the_link_of_a_scholar_hit_is_used(dk):
    """SerpApi Scholar: DOI có thể nằm ở link nhà xuất bản/doi.org. Đăng ký cả đường tra DOI lẫn đường tìm theo tiêu đề
    để test đúng với cả hai cách cài đặt (điều bắt buộc: kết quả là bản ghi xác minh có DOI đó)."""
    _dang_ky_doi(dk)
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE)]
    kq = _xm(dk, _hit("serpapi_scholar", doi=None, url=f"https://doi.org/{DOI}"))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.doi.lower() == DOI


def test_kept_record_never_gets_a_study_type_derived_from_the_title(dk):
    """"Never derive a study_type from a title alone": tiêu đề chứa meta-analysis/randomized không được thành study_type."""
    _dang_ky_doi(dk, tieu_de="Dapagliflozin in adults: a randomized controlled trial and meta-analysis")
    kq = _xm(dk, _hit(tieu_de="Dapagliflozin in adults: a randomized controlled trial and meta-analysis"))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.study_type in (None, "preprint")


def test_takeaway_of_the_hit_never_becomes_the_registry_abstract(dk):
    _dang_ky_doi(dk)
    takeaway = "TAKEAWAY-AI: dapagliflozin clearly reduces every renal outcome."
    kq = _xm(dk, _hit(raw={"takeaway": takeaway}))
    assert kq.ket_qua == "xac_minh_duoc"
    assert takeaway not in (kq.ban_ghi.abstract or "")


# ════════════════════════════════════════════════════════════════════════════
# Khớp mờ được phép: khác Unicode / hoa-thường / dấu câu / dấu phụ
# ════════════════════════════════════════════════════════════════════════════

_TIEU_DE_VN = "Đánh giá hiệu quả của thuốc ức chế SGLT2 ở bệnh nhân suy tim mạn tính: tổng quan hệ thống"

_CAP_PHAI_KHOP = [
    pytest.param("EFFECT OF DAPAGLIFLOZIN ON RENAL OUTCOMES: A META-ANALYSIS",
                 "Effect of dapagliflozin on renal outcomes: a meta-analysis", id="hoa-thuong"),
    pytest.param("Effect of dapagliflozin on renal outcomes – a meta‑analysis.",
                 "Effect of dapagliflozin on renal outcomes: a meta-analysis", id="gach-dai-gach-noi-cham-cuoi"),
    pytest.param("Effect of  dapagliflozin   on renal outcomes ; a meta analysis",
                 "Effect of dapagliflozin on renal outcomes: a meta-analysis", id="khoang-trang-dau-cau"),
    pytest.param(_nfd(_TIEU_DE_VN), _TIEU_DE_VN, id="nfd-so-voi-nfc"),
    pytest.param(_TIEU_DE_VN, _nfd(_TIEU_DE_VN), id="nfc-so-voi-nfd"),
    pytest.param("Naive Bayes for cardiac risk stratification: a comparison",
                 "Naïve Bayes for cardiac risk stratification: a comparison", id="dau-phu"),
    pytest.param("“Real-world” outcomes of SGLT2 inhibitors in heart failure",
                 "'Real-world' outcomes of SGLT2 inhibitors in heart failure", id="dau-nhay"),
]


@pytest.mark.parametrize("tieu_de_hit,tieu_de_dk", _CAP_PHAI_KHOP)
def test_formatting_differences_that_should_match_are_kept_by_doi(dk, tieu_de_hit, tieu_de_dk):
    _dang_ky_doi(dk, tieu_de=tieu_de_dk)
    kq = _xm(dk, _hit(tieu_de=tieu_de_hit))
    assert kq.ket_qua == "xac_minh_duoc", "khác biệt hình thức thuần tuý không được làm mất bài thật"
    assert kq.ban_ghi.title == tieu_de_dk


@pytest.mark.parametrize("tieu_de_hit,tieu_de_dk", _CAP_PHAI_KHOP[:3])
def test_formatting_differences_that_should_match_are_kept_by_bibliographic_search(dk, tieu_de_hit, tieu_de_dk):
    dk.crossref_tim = [_msg_crossref(DOI, tieu_de_dk)]
    kq = _xm(dk, _hit(tieu_de=tieu_de_hit, doi=None))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.doi.lower() == DOI


# ════════════════════════════════════════════════════════════════════════════
# Tiêu đề GẦN GIỐNG nhưng KHÁC bài => không giữ (cả hai đường)
# ════════════════════════════════════════════════════════════════════════════

_T = "Effect of dapagliflozin in adults with chronic kidney disease: a randomized trial"

_CAP_GAN_GIONG = [
    pytest.param(_T, _T.replace("adults", "children"), id="khac-doi-tuong"),
    pytest.param("Long-term outcomes of sepsis bundles: Part II", "Long-term outcomes of sepsis bundles: Part I",
                 id="phan-II-so-voi-I"),
    pytest.param("Semaglutide in type 2 diabetes: 52-week results", "Semaglutide in type 2 diabetes: 26-week results",
                 id="khac-so-tuan"),
]

_CAP_THONG_BAO = [
    pytest.param(f"Erratum: {_T}", _T, id="dang-ky-la-erratum"),
    pytest.param(_T, f"Erratum: {_T}", id="hit-la-erratum"),
    pytest.param(f"Correction to: {_T}", _T, id="dang-ky-la-correction-to"),
    pytest.param(f"Publisher Correction: {_T}", _T, id="dang-ky-la-publisher-correction"),
    pytest.param(f"Correction: {_T}", f"Correction: {_T}", id="ca-hai-la-correction"),
    pytest.param(f"Erratum: {_T}", f"Erratum: {_T}", id="ca-hai-la-erratum"),
]

_CAP_RUT_BAI = [
    pytest.param(f"Retraction Note: {_T}", _T, id="dang-ky-la-retraction-note"),
    pytest.param(f"Retraction Note: {_T}", f"Retraction Note: {_T}", id="ca-hai-la-retraction-note"),
]


@pytest.mark.parametrize("tieu_de_dk,tieu_de_hit", _CAP_GAN_GIONG)
def test_near_duplicate_titles_are_rejected_when_the_doi_resolves_to_a_different_paper(dk, tieu_de_dk, tieu_de_hit):
    _dang_ky_doi(dk, tieu_de=tieu_de_dk)
    _khong_giu(_xm(dk, _hit(tieu_de=tieu_de_hit)))


@pytest.mark.parametrize("tieu_de_dk,tieu_de_hit", _CAP_GAN_GIONG)
def test_near_duplicate_titles_are_rejected_by_bibliographic_search(dk, tieu_de_dk, tieu_de_hit):
    dk.crossref_tim = [_msg_crossref(DOI, tieu_de_dk)]
    _khong_giu(_xm(dk, _hit(tieu_de=tieu_de_hit, doi=None, tac_gia=None, nam=None)))


@pytest.mark.parametrize("tieu_de_dk,tieu_de_hit", _CAP_THONG_BAO)
def test_erratum_and_correction_titles_are_never_kept_by_doi(dk, tieu_de_dk, tieu_de_hit):
    _dang_ky_doi(dk, tieu_de=tieu_de_dk)
    _khong_giu(_xm(dk, _hit(tieu_de=tieu_de_hit)))


@pytest.mark.parametrize("tieu_de_dk,tieu_de_hit", _CAP_THONG_BAO)
def test_erratum_and_correction_titles_are_never_kept_by_bibliographic_search(dk, tieu_de_dk, tieu_de_hit):
    dk.crossref_tim = [_msg_crossref(DOI, tieu_de_dk)]
    _khong_giu(_xm(dk, _hit(tieu_de=tieu_de_hit, doi=None, tac_gia=None, nam=None)))


@pytest.mark.parametrize("tieu_de_dk,tieu_de_hit", _CAP_RUT_BAI)
def test_retraction_notice_titles_are_never_kept(dk, tieu_de_dk, tieu_de_hit):
    _dang_ky_doi(dk, tieu_de=tieu_de_dk)
    dk.crossref_tim = [_msg_crossref(DOI, tieu_de_dk)]
    _khong_giu(_xm(dk, _hit(tieu_de=tieu_de_hit)), cho_phep=("khong_khop", "mo_ho", "bi_rut_bai"))


# Đo thật 20/09/2026: Crossref ghi tiêu đề của CHÍNH bài bị rút với tiền tố "RETRACTED:" (ca Wakefield, Lancet 1998).
# Trước đây bị xếp "không khớp" (vẫn loại, nhưng sai nhãn) — nay phải là "bi_rut_bai" để đếm đúng.
_TIEN_TO_RUT = ["RETRACTED: ", "Retracted: ", "[Retracted] ", "WITHDRAWN: ", "RETRACTED - "]


@pytest.mark.parametrize("tien_to", _TIEN_TO_RUT)
def test_a_paper_whose_crossref_title_is_marked_retracted_is_classified_bi_rut_bai_by_doi(dk, tien_to):
    _dang_ky_doi(dk, tieu_de=f"{tien_to}{_T}")
    kq = _xm(dk, _hit(tieu_de=_T))
    assert kq.ket_qua == "bi_rut_bai"
    assert kq.ban_ghi is None


@pytest.mark.parametrize("tien_to", _TIEN_TO_RUT)
def test_a_paper_whose_crossref_title_is_marked_retracted_is_classified_bi_rut_bai_by_title_search(dk, tien_to):
    dk.crossref_tim = [_msg_crossref(DOI, f"{tien_to}{_T}")]
    kq = _xm(dk, _hit(tieu_de=_T, doi=None, tac_gia=None, nam=None))
    assert kq.ket_qua == "bi_rut_bai"
    assert kq.ban_ghi is None


def test_the_retracted_marker_on_a_different_paper_does_not_claim_the_hit_is_retracted(dk):
    """DOI gắn nhầm sang một bài KHÁC đã bị rút: hit không phải bài đó nên chỉ là 'không khớp', không được gán 'bị rút'."""
    _dang_ky_doi(dk, tieu_de="RETRACTED: An entirely different paper about statins in elderly patients")
    kq = _xm(dk, _hit(tieu_de=_T))
    assert kq.ket_qua == "khong_khop"
    assert kq.ban_ghi is None


def test_a_retracted_marker_never_rescues_the_record_even_when_keep_unverified_is_on(dk, monkeypatch):
    monkeypatch.setattr(settings, "fallback_keep_unverified", True, raising=False)
    _dang_ky_doi(dk, tieu_de=f"RETRACTED: {_T}")
    kq = _xm(dk, _hit(tieu_de=_T))
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


def test_title_only_moderately_similar_is_not_a_match(dk):
    _dang_ky_doi(dk, tieu_de="Effects of dapagliflozin on kidney outcomes in patients with type 2 diabetes")
    _khong_giu(_xm(dk, _hit(tieu_de="Dapagliflozin and kidney outcomes")))


def test_doi_resolving_to_a_completely_different_paper_is_rejected(dk):
    _dang_ky_doi(dk, tieu_de="Cognitive behavioural therapy for insomnia in older adults: a systematic review")
    kq = _xm(dk, _hit())
    _khong_giu(kq)
    assert kq.ket_qua != "loi_xac_minh"


def test_doi_that_does_not_exist_is_rejected_and_is_not_a_verification_error(dk):
    """Crossref TRẢ LỜI 404 = câu trả lời dứt khoát 'không có DOI này' (khác 'không hỏi được')."""
    kq = _xm(dk, _hit(doi="10.5555/fake.khong.ton.tai"))
    _khong_giu(kq)
    assert kq.ket_qua != "loi_xac_minh"


def test_a_mismatching_doi_is_not_rescued_by_a_lucky_search_hit_for_someone_elses_paper(dk):
    """DOI của hit trỏ sang bài KHÁC, còn ô tìm theo tiêu đề lại có một bài trùng tiêu đề nhưng DOI khác: tiêu đề ở hit
    đi kèm một DOI cụ thể, nên không được 'cứu' bằng cách gán DOI khác — nếu giữ thì phải là DOI của bài khớp tiêu đề."""
    _dang_ky_doi(dk, tieu_de="Cognitive behavioural therapy for insomnia in older adults: a systematic review")
    dk.crossref_tim = [_msg_crossref("10.5555/fake.khac", TIEU_DE)]
    kq = _xm(dk, _hit())
    if kq.ket_qua == "xac_minh_duoc":
        assert kq.ban_ghi.doi.lower() == "10.5555/fake.khac"
        assert kq.ban_ghi.title == TIEU_DE
    else:
        _khong_giu(kq)


# ════════════════════════════════════════════════════════════════════════════
# (b) Không DOI: đúng MỘT ứng viên Crossref rõ ràng nhất
# ════════════════════════════════════════════════════════════════════════════

def test_no_doi_single_clear_candidate_is_kept(dk):
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE)]
    kq = _xm(dk, _hit(doi=None))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.doi.lower() == DOI and kq.ban_ghi.title == TIEU_DE
    assert kq.ban_ghi.source not in TANG_DU_PHONG


def test_no_doi_one_exact_candidate_among_unrelated_ones_is_kept(dk):
    dk.crossref_tim = [
        _msg_crossref("10.5555/fake.la1", "Cognitive behavioural therapy for insomnia in older adults"),
        _msg_crossref(DOI, TIEU_DE),
        _msg_crossref("10.5555/fake.la2", "A survey of nursing workload in rural clinics"),
    ]
    kq = _xm(dk, _hit(doi=None))
    assert kq.ket_qua == "xac_minh_duoc" and kq.ban_ghi.doi.lower() == DOI


def test_no_doi_and_no_candidates_is_not_kept(dk):
    dk.crossref_tim = []
    _khong_giu(_xm(dk, _hit(doi=None)))


def test_no_doi_and_only_unrelated_candidates_is_not_kept(dk):
    dk.crossref_tim = [_msg_crossref("10.5555/fake.la1", "Cognitive behavioural therapy for insomnia in older adults"),
                       _msg_crossref("10.5555/fake.la2", "A survey of nursing workload in rural clinics")]
    _khong_giu(_xm(dk, _hit(doi=None)))


def test_two_equally_good_candidates_are_ambiguous_and_rejected(dk):
    dk.crossref_tim = [_msg_crossref("10.5555/fake.a1", TIEU_DE), _msg_crossref("10.5555/fake.a2", TIEU_DE)]
    _khong_giu(_xm(dk, _hit(doi=None)))


def test_an_indistinguishable_second_candidate_makes_the_best_not_clearly_best(dk):
    """Hai ứng viên KHÔNG thể phân biệt bằng tiêu đề (chỉ khác dấu câu, khác DOI — vd bản tạp chí và bản sao chép):
    không có ứng viên nào "rõ ràng tốt nhất" nên KHÔNG được chọn một cái."""
    dk.crossref_tim = [_msg_crossref("10.5555/fake.p1", "Long-term outcomes of sepsis bundles: Part I"),
                       _msg_crossref("10.5555/fake.p2", "Long-term outcomes of sepsis bundles - Part I.")]
    _khong_giu(_xm(dk, _hit(tieu_de="Long-term outcomes of sepsis bundles: Part I", doi=None)))


def test_a_second_candidate_that_differs_by_a_discriminating_token_is_a_different_paper_not_ambiguity(dk):
    """"Part II" khác "Part I" ở token phân biệt (số La Mã): là BÀI KHÁC, nên hit "Part I" khớp chính xác ứng viên
    "Part I" và chỉ ứng viên đó — giữ đúng DOI của Part I, tuyệt đối không phải DOI của Part II."""
    dk.crossref_tim = [_msg_crossref("10.5555/fake.p1", "Long-term outcomes of sepsis bundles: Part I"),
                       _msg_crossref("10.5555/fake.p2", "Long-term outcomes of sepsis bundles: Part II")]
    kq = _xm(dk, _hit(tieu_de="Long-term outcomes of sepsis bundles: Part I", doi=None))
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.doi.lower() == "10.5555/fake.p1"


def test_hit_with_only_a_title_is_judged_by_the_title_when_year_and_authors_are_unknown(dk):
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE)]
    kq = _xm(dk, _hit(doi=None, tac_gia=None, nam=None))
    assert kq.ket_qua == "xac_minh_duoc"


# -- năm: |lệch| <= 1 khi biết năm ---------------------------------------------------------

@pytest.mark.parametrize("nam_hit,duoc_giu", [
    ("2021", True), ("2020", True), ("2022", True),
    ("2019", False), ("2023", False), ("1999", False),
    ("2021-05-14", True), ("2018-01-01", False),
    (None, True),
])
def test_year_of_the_hit_must_be_within_one_of_the_candidate_when_known(dk, nam_hit, duoc_giu):
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE, nam=2021)]
    kq = _xm(dk, _hit(doi=None, nam=nam_hit))
    if duoc_giu:
        assert kq.ket_qua == "xac_minh_duoc"
    else:
        _khong_giu(kq)


# -- tác giả: họ tác giả ĐẦU của hit phải có trong danh sách của Crossref khi biết tác giả ---------------

@pytest.mark.parametrize("tac_gia_hit,duoc_giu", [
    ("Alice Nguyen, Bob Tran", True),
    ("A Nguyen, B Tran", True),
    ("Nguyen A, Tran B", True),
    ("Carol Mendes, Alice Nguyen", False),       # tác giả đầu KHÔNG có trong Crossref (dù người thứ hai có)
    ("Carol Mendes", False),
    ("Bob Tran, Carol Mendes", True),           # họ tác giả đầu (Tran) xuất hiện ở vị trí 2 của Crossref: chấp nhận
    (None, True),
    ("", True),
])
def test_first_author_surname_must_be_among_the_candidates_authors_when_authors_are_known(dk, tac_gia_hit, duoc_giu):
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE, tac_gia=(("Alice", "Nguyen"), ("Bob", "Tran")))]
    kq = _xm(dk, _hit(doi=None, tac_gia=tac_gia_hit))
    if duoc_giu:
        assert kq.ket_qua == "xac_minh_duoc"
    else:
        _khong_giu(kq)


def test_first_author_match_ignores_vietnamese_diacritics(dk):
    """Họ Việt hay bị bỏ dấu ở một bên: 'Nguyễn' (hit) so với 'Nguyen' (Crossref) phải khớp."""
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE, tac_gia=(("An", "Nguyen"), ("Bob", "Tran")))]
    kq = _xm(dk, _hit(doi=None, tac_gia="Văn An Nguyễn, Bob Tran"))
    assert kq.ket_qua == "xac_minh_duoc"


# ════════════════════════════════════════════════════════════════════════════
# (c) PMID từ link PubMed được PubMed xác nhận có tồn tại
# ════════════════════════════════════════════════════════════════════════════

PMID = "12345678"


def _hit_pmid(nguon: str = "serpapi_scholar", **kw: Any) -> RawRecord:
    kw.setdefault("doi", None)
    kw.setdefault("tac_gia", None)
    kw.setdefault("nam", None)
    return _hit(nguon, pmid=PMID, url=f"https://pubmed.ncbi.nlm.nih.gov/{PMID}/", **kw)


def test_pmid_confirmed_by_pubmed_is_kept_as_the_pubmed_record(dk):
    dk.pubmed[PMID] = _xml_pubmed(PMID, TIEU_DE, doi="10.5555/fake.pm.1")
    dk.crossref_doi["10.5555/fake.pm.1"] = _msg_crossref("10.5555/fake.pm.1", TIEU_DE)
    kq = _xm(dk, _hit_pmid())
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.pmid == PMID
    assert kq.ban_ghi.source not in TANG_DU_PHONG
    assert kq.ban_ghi.raw.get("phat_hien_boi") == "serpapi_scholar"
    assert isinstance(kq.ban_ghi.raw.get("xac_minh"), dict)


def test_pmid_that_pubmed_does_not_know_is_rejected_and_not_an_error(dk):
    kq = _xm(dk, _hit_pmid())
    _khong_giu(kq)
    assert kq.ket_qua != "loi_xac_minh"


def test_pubmed_outage_is_a_verification_error_never_a_match(dk):
    dk.pubmed[PMID] = _xml_pubmed(PMID, TIEU_DE)
    dk.pubmed_loi = requests.ConnectionError("Max retries exceeded")
    kq = _xm(dk, _hit_pmid())
    assert kq.ket_qua == "loi_xac_minh" and kq.ban_ghi is None


def test_a_pubmed_verified_record_that_ends_with_a_doi_goes_through_the_retraction_gate(dk):
    doi_pm = "10.5555/fake.pm.2"
    dk.pubmed[PMID] = _xml_pubmed(PMID, TIEU_DE, doi=doi_pm)
    dk.crossref_doi[doi_pm] = _msg_crossref(doi_pm, TIEU_DE)
    dk.scite_bai[doi_pm] = _bai_scite(doi_pm, retracted=True)
    kq = _xm(dk, _hit_pmid())
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


# ════════════════════════════════════════════════════════════════════════════
# Lỗi vận chuyển / phản hồi hỏng => loi_xac_minh (KHÔNG BAO GIỜ thành khớp, KHÁC khong_khop)
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("loi", [
    pytest.param(requests.ConnectionError("Max retries exceeded"), id="mat-mang"),
    pytest.param(requests.Timeout("Read timed out."), id="timeout"),
    pytest.param(500, id="http-500"),
    pytest.param(503, id="http-503"),
    pytest.param(429, id="http-429"),
])
@pytest.mark.parametrize("co_doi", [True, False], ids=["co-doi", "khong-doi"])
def test_registry_failure_is_a_verification_error_and_never_a_match(dk, loi, co_doi):
    _dang_ky_doi(dk)
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE)]   # nếu Crossref "trả lời được" thì SẼ khớp: lỗi phải thắng
    dk.crossref_loi = loi
    kq = _xm(dk, _hit(doi=DOI if co_doi else None))
    assert kq.ket_qua == "loi_xac_minh", kq.ket_qua
    assert kq.ban_ghi is None
    assert kq.ket_qua != "khong_khop", "lỗi mạng KHÁC 'không khớp': không được báo là đã kiểm rồi mà không thấy"


def test_malformed_crossref_json_is_a_verification_error(dk):
    dk.crossref_doi[DOI] = "json_hong"
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "loi_xac_minh" and kq.ban_ghi is None


def test_malformed_crossref_search_json_is_a_verification_error(dk):
    dk.crossref_tim = "json_hong"
    kq = _xm(dk, _hit(doi=None))
    assert kq.ket_qua == "loi_xac_minh" and kq.ban_ghi is None


# ════════════════════════════════════════════════════════════════════════════
# Tối đa 2 lời gọi cơ quan đăng ký cho mỗi phát hiện
# ════════════════════════════════════════════════════════════════════════════

def _kich_ban_doi_khop(dk):
    _dang_ky_doi(dk)
    return _hit()


def _kich_ban_tim_khop(dk):
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE)]
    return _hit(doi=None)


def _kich_ban_tim_mo_ho(dk):
    dk.crossref_tim = [_msg_crossref("10.5555/fake.a1", TIEU_DE), _msg_crossref("10.5555/fake.a2", TIEU_DE)]
    return _hit(doi=None)


def _kich_ban_doi_404(dk):
    return _hit(doi="10.5555/fake.khong.ton.tai")


def _kich_ban_doi_sai_tieu_de(dk):
    _dang_ky_doi(dk, tieu_de="Cognitive behavioural therapy for insomnia in older adults")
    return _hit()


def _kich_ban_pmid(dk):
    dk.pubmed[PMID] = _xml_pubmed(PMID, TIEU_DE, doi="10.5555/fake.pm.3")
    dk.crossref_doi["10.5555/fake.pm.3"] = _msg_crossref("10.5555/fake.pm.3", TIEU_DE)
    return _hit_pmid()


def _kich_ban_mang_loi(dk):
    dk.crossref_loi = requests.ConnectionError("Max retries exceeded")
    return _hit()


@pytest.mark.parametrize("dung", [_kich_ban_doi_khop, _kich_ban_tim_khop, _kich_ban_tim_mo_ho, _kich_ban_doi_404,
                                  _kich_ban_doi_sai_tieu_de, _kich_ban_pmid, _kich_ban_mang_loi])
def test_at_most_two_registry_calls_per_hit(dk, dung):
    rec = dung(dk)
    _xm(dk, rec, toi_da_goi=2)          # _xm đã kiểm, viết rõ ở đây cho dễ đọc
    assert len(dk.goi_dang_ky()) <= 2


def test_a_hit_that_never_reaches_a_registry_answer_makes_no_scite_call(dk):
    """Scite CHỈ dành cho phát hiện đã tới DOI xác nhận: bị loại ở bước đối chiếu thì không tốn lời gọi Scite nào."""
    _dang_ky_doi(dk, tieu_de="Cognitive behavioural therapy for insomnia in older adults")
    _xm(dk, _hit())
    assert dk.goi_scite() == []


def test_a_verification_error_makes_no_scite_call(dk):
    dk.crossref_loi = requests.ConnectionError("x")
    _xm(dk, _hit())
    assert dk.goi_scite() == []


# ════════════════════════════════════════════════════════════════════════════
# CỔNG RÚT BÀI / THÔNG BÁO BIÊN TẬP
# ════════════════════════════════════════════════════════════════════════════

def test_scite_retracted_true_rejects_with_bi_rut_bai_and_drops_the_record(dk):
    _dang_ky_doi(dk)
    dk.scite_bai[DOI] = _bai_scite(DOI, retracted=True)
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


@pytest.mark.parametrize("thong_bao", [
    pytest.param({"type": "retraction", "title": "Retraction Note: fake notice"}, id="type-retraction"),
    pytest.param({"type": "Retraction", "title": "Notice"}, id="type-hoa"),
    pytest.param({"type": "withdrawal", "title": "Article withdrawn by the publisher"}, id="type-withdrawal"),
    pytest.param({"title": "Retraction notice for the article"}, id="chi-co-tieu-de"),
    pytest.param({"type": "notice", "title": "This article has been withdrawn"}, id="tieu-de-withdrawn"),
])
def test_a_scite_editorial_notice_that_mentions_retract_or_withdraw_rejects(dk, thong_bao):
    _dang_ky_doi(dk)
    dk.scite_bai[DOI] = _bai_scite(DOI, retracted=False, editorialNotices=[thong_bao])
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


def test_crossref_retraction_signal_rejects_even_when_scite_says_clean(dk):
    """Nguyên liệu Crossref có sẵn (`updated-by` loại retraction) là NGUỒN CHÍNH: Scite 'sạch' không cứu được."""
    _dang_ky_doi(dk, updated_by=[{"type": "retraction", "DOI": "10.5555/fake.notice", "label": "Retraction",
                                  "source": "publisher", "updated": {"date-parts": [[2023, 1, 1]]}}])
    dk.crossref_doi["10.5555/fake.notice"] = _msg_crossref("10.5555/fake.notice", f"Retraction Note: {TIEU_DE}")
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


def test_crossref_retraction_signal_still_rejects_when_scite_is_down(dk):
    _dang_ky_doi(dk, updated_by=[{"type": "retraction", "DOI": "10.5555/fake.notice"}])
    dk.scite_loi = requests.ConnectionError("Scite down")
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


def test_crossref_retraction_also_rejects_on_the_bibliographic_route(dk):
    dk.crossref_tim = [_msg_crossref(DOI, TIEU_DE, updated_by=[{"type": "retraction", "DOI": "10.5555/fake.notice"}])]
    _dang_ky_doi(dk, updated_by=[{"type": "retraction", "DOI": "10.5555/fake.notice"}])
    kq = _xm(dk, _hit(doi=None))
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


@pytest.mark.parametrize("nhan", ["expression_of_concern", "expression-of-concern"])
def test_crossref_expression_of_concern_is_kept_and_flagged(dk, nhan):
    _dang_ky_doi(dk, updated_by=[{"type": nhan, "DOI": "10.5555/fake.eoc"}])
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc"
    assert "co_thong_bao_bien_tap" in _co(kq.ban_ghi)


@pytest.mark.parametrize("thong_bao", [
    pytest.param({"type": "correction", "title": "Correction to: fake"}, id="correction"),
    pytest.param({"type": "erratum", "title": "Erratum: fake"}, id="erratum"),
    pytest.param({"type": "expression-of-concern", "title": "Editorial expression of concern"}, id="eoc"),
    pytest.param({"title": "Expression of concern regarding fake article"}, id="eoc-chi-tieu-de"),
])
def test_scite_correction_or_concern_notice_is_kept_with_the_editorial_flag(dk, thong_bao):
    _dang_ky_doi(dk)
    dk.scite_bai[DOI] = _bai_scite(DOI, editorialNotices=[thong_bao])
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc"
    co = _co(kq.ban_ghi)
    assert "co_thong_bao_bien_tap" in co
    assert "thong_bao_bien_tap_chua_phan_loai" not in co


@pytest.mark.parametrize("thong_bao", [
    pytest.param({"id": 991, "weird_field": "???", "payload": {"x": 1}}, id="cau-truc-la"),
    pytest.param({"type": "zzz-unknown", "title": "Some odd notice text about nothing in particular"}, id="loai-la"),
    pytest.param("A notice about something", id="chuoi-tro-tron"),
])
def test_an_unclassifiable_scite_notice_is_kept_but_flagged_never_silently_ignored(dk, thong_bao):
    _dang_ky_doi(dk)
    dk.scite_bai[DOI] = _bai_scite(DOI, editorialNotices=[thong_bao])
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc", "không phân loại được thì GIỮ (không tự quyết bỏ)"
    assert "thong_bao_bien_tap_chua_phan_loai" in _co(kq.ban_ghi), "…nhưng phải GẮN CỜ, không được im lặng"


def test_clean_paper_carries_no_editorial_flags(dk):
    _dang_ky_doi(dk)
    kq = _xm(dk, _hit())
    co = _co(kq.ban_ghi)
    assert "co_thong_bao_bien_tap" not in co
    assert "thong_bao_bien_tap_chua_phan_loai" not in co
    assert "nhieu_trich_dan_phan_bac" not in co


def test_keep_unverified_setting_never_rescues_a_retracted_paper(dk, monkeypatch):
    monkeypatch.setattr(settings, "fallback_keep_unverified", True)
    _dang_ky_doi(dk)
    dk.scite_bai[DOI] = _bai_scite(DOI, retracted=True)
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "bi_rut_bai" and kq.ban_ghi is None


# ════════════════════════════════════════════════════════════════════════════
# Tally của Scite: CHỈ ghi nhận + cờ; không bao giờ đổi điểm/tier/lọc
# ════════════════════════════════════════════════════════════════════════════

def test_scite_tally_is_recorded_with_provenance_and_date(dk):
    _dang_ky_doi(dk)
    dk.scite_tally[DOI] = _tally_scite(DOI, ung_ho=21, phan_bac=1, de_cap=1878)
    ban = _xm(dk, _hit()).ban_ghi
    scite = ban.raw.get("scite")
    assert isinstance(scite, dict)
    assert scite["da_kiem"] is True
    assert scite["nguon"] == "api.scite.ai"
    assert isinstance(scite["tally"], dict)
    assert scite["tally"]["supporting"] == 21 and scite["tally"]["contradicting"] == 1
    date.fromisoformat(str(scite["ngay"])[:10])           # ngày ISO


@pytest.mark.parametrize("ung_ho,phan_bac,co_co", [
    (0, 3, True), (2, 3, True), (1, 10, True), (0, 4, True),
    (3, 3, False), (5, 3, False), (0, 2, False), (0, 0, False), (1, 2, False), (10, 30, True),
])
def test_contradicting_flag_boundary(dk, ung_ho, phan_bac, co_co):
    """Cờ khi phản bác >= 3 VÀ phản bác > ủng hộ."""
    _dang_ky_doi(dk)
    dk.scite_tally[DOI] = _tally_scite(DOI, ung_ho=ung_ho, phan_bac=phan_bac)
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc", "tally KHÔNG BAO GIỜ quyết định giữ/bỏ"
    assert ("nhieu_trich_dan_phan_bac" in _co(kq.ban_ghi)) is co_co


def test_scite_tally_never_changes_the_record_or_its_score(dk):
    """Cùng một bài, tally 'rất tốt' và tally 'rất xấu': mọi thứ NGOÀI khối ghi nhận Scite/cờ phải y hệt và điểm chấm y hệt."""
    def chay(ung_ho, phan_bac):
        dk.calls.clear()
        _dang_ky_doi(dk)
        dk.scite_tally[DOI] = _tally_scite(DOI, ung_ho=ung_ho, phan_bac=phan_bac)
        ban = _xm(dk, _hit()).ban_ghi
        d = ban.to_dict()
        d["raw"] = {k: v for k, v in d["raw"].items() if k not in {"scite", "co"}}
        return ban, d

    ban_tot, d_tot = chay(500, 0)
    ban_xau, d_xau = chay(0, 500)
    assert "nhieu_trich_dan_phan_bac" in _co(ban_xau) and "nhieu_trich_dan_phan_bac" not in _co(ban_tot)
    assert d_tot == d_xau
    diem_tot, diem_xau = score_item(normalize(ban_tot)), score_item(normalize(ban_xau))
    for khoa in ("evidence_quality_score", "reliability_tier", "practice_change_score"):
        assert diem_tot.get(khoa) == diem_xau.get(khoa), khoa


# ════════════════════════════════════════════════════════════════════════════
# Scite hỏng: xét bản ghi bằng các kiểm tra khác, KHÔNG tuyên bố đã kiểm Scite
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("loi", [
    pytest.param(requests.Timeout("Read timed out."), id="timeout"),
    pytest.param(requests.ConnectionError("Max retries exceeded"), id="mat-mang"),
    pytest.param(404, id="404"),
    pytest.param(429, id="429"),
    pytest.param(500, id="500"),
    pytest.param(503, id="503"),
])
def test_scite_failure_is_judged_by_the_other_checks_and_never_claims_a_check(dk, loi):
    _dang_ky_doi(dk)
    dk.scite_loi = loi
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc", "Scite hỏng không được làm mất bài đã qua các kiểm tra khác"
    scite = kq.ban_ghi.raw.get("scite")
    assert isinstance(scite, dict)
    assert scite.get("da_kiem") is False, "KHÔNG được khẳng định đã kiểm Scite khi Scite không trả lời được"
    assert isinstance(scite.get("ly_do"), str) and scite["ly_do"].strip()
    assert not scite.get("tally"), "không được bịa tally"
    co = _co(kq.ban_ghi)
    assert "nhieu_trich_dan_phan_bac" not in co and "co_thong_bao_bien_tap" not in co


def test_malformed_scite_json_is_not_claimed_as_a_check(dk):
    _dang_ky_doi(dk)
    dk.scite_bai_rong = True
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc"
    assert kq.ban_ghi.raw["scite"]["da_kiem"] is False


def test_scite_tally_failure_alone_does_not_drop_the_record_nor_invent_flags(dk):
    _dang_ky_doi(dk)
    dk.scite_tally[DOI] = requests.Timeout("tally timed out")
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc"
    assert isinstance(kq.ban_ghi.raw["scite"]["da_kiem"], bool)
    assert "nhieu_trich_dan_phan_bac" not in _co(kq.ban_ghi)


def test_scite_disabled_by_setting_makes_no_scite_call_and_claims_no_check(dk, monkeypatch):
    monkeypatch.setattr(settings, "enable_scite_verification", False)
    _dang_ky_doi(dk)
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc"
    assert dk.goi_scite() == []
    scite = kq.ban_ghi.raw.get("scite")
    assert scite is None or scite.get("da_kiem") is False


def test_scite_calls_are_public_only_and_never_carry_credentials(dk):
    _dang_ky_doi(dk)
    _xm(dk, _hit())
    goi = dk.goi_scite()
    assert goi, "test vô nghĩa nếu không có lời gọi Scite nào"
    for c in goi:
        assert re.match(r"^/(papers|tallies)/", c["path"]), c["path"]
        assert "authorization" not in c["headers"]
        assert not any("key" in h or "token" in h for h in c["headers"]), c["headers"]
        assert not any("key" in p.lower() or "token" in p.lower() for p in c["params"])


def test_scite_calls_ask_about_the_confirmed_doi_not_the_hits_raw_string(dk):
    _dang_ky_doi(dk)
    _xm(dk, _hit(doi=f"https://doi.org/{DOI.upper()}"))
    for c in dk.goi_scite():
        assert c["path"].split("/", 2)[2].lower() == DOI


# ════════════════════════════════════════════════════════════════════════════
# Không được xác minh => bỏ mặc định; giữ có gắn cờ CHỈ khi fallback_keep_unverified
# ════════════════════════════════════════════════════════════════════════════

def test_unverified_hit_is_dropped_by_default(dk):
    _dang_ky_doi(dk, tieu_de="Cognitive behavioural therapy for insomnia in older adults")
    kq = _xm(dk, _hit())
    assert kq.ban_ghi is None and kq.ket_qua in {"khong_khop", "mo_ho"}


def test_keep_unverified_setting_keeps_only_flagged_records_and_never_changes_the_verdict(dk, monkeypatch):
    monkeypatch.setattr(settings, "fallback_keep_unverified", True)
    _dang_ky_doi(dk, tieu_de="Cognitive behavioural therapy for insomnia in older adults")
    kq = _xm(dk, _hit())
    assert kq.ket_qua in {"khong_khop", "mo_ho"}, "cờ chỉ quyết định GIỮ hay không, không đổi kết luận xác minh"
    if kq.ban_ghi is not None:
        assert kq.ban_ghi.raw.get("chua_xac_minh") is True


def test_a_verified_record_never_carries_the_unverified_flag(dk, monkeypatch):
    monkeypatch.setattr(settings, "fallback_keep_unverified", True)
    _dang_ky_doi(dk)
    kq = _xm(dk, _hit())
    assert kq.ket_qua == "xac_minh_duoc"
    assert not kq.ban_ghi.raw.get("chua_xac_minh")


def test_the_returned_record_is_a_new_object_and_the_hit_is_not_mutated(dk):
    _dang_ky_doi(dk)
    rec = _hit(raw={"takeaway": "X", "consensus_study_type": "rct"})
    truoc = copy.deepcopy(rec.to_dict())
    kq = xac_minh_ban_ghi(rec)
    assert kq.ban_ghi is not rec
    assert rec.to_dict() == truoc


def test_module_public_names_match_the_contract():
    assert callable(xac_minh_ban_ghi)
    assert KetQuaXacMinh.__dataclass_fields__.keys() >= {"ban_ghi", "ket_qua"}
    with pytest.raises(Exception):
        KetQuaXacMinh(None, "khong_khop").ket_qua = "xac_minh_duoc"  # type: ignore[misc]
    assert hasattr(fv, "xac_minh_ban_ghi")
