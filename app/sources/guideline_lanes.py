"""LANE guideline: nối trực tiếp, MIỄN PHÍ, KHÔNG khoá vào nơi phát hành khuyến cáo (thêm 20/09/2026).

Vì sao có: đo 20/09/2026 cho thấy tầng «guideline gốc» (source of record) của hệ chỉ có RSS của vài tạp chí. Hầu hết
hiệp hội KHÔNG có RSS đọc được (IDSA/ESC/EULAR/ADA/ACC/SIGN/BTS/ASH/AAN đều 404; WHO 403; NICE 403; USPSTF không có
RSS). Mỗi lane dưới đây dùng đường công khai, chính thức, đã đo chạy thật:

  * Europe PMC (`europepmc_lane`): chỉ mục MEDLINE có PMID; loại xuất bản «Practice Guideline» (toàn cầu), USPSTF,
    WHO, CDC MMWR R&R. Độc lập với NCBI (E-utilities đang bị chặn misuse ở mạng này).
  * WHO IRIS (`who_iris_lane`): kho OAI-PMH chính thức của WHO (iris.who.int/oai/request), giao thức thu thập mở.
  * Bộ Y tế Việt Nam (`kcb_vn_lane`): trang danh sách «Hướng dẫn chẩn đoán, điều trị» của Cục Quản lý Khám chữa
    bệnh (kcb.vn/phac-do), HTML render phía máy chủ, robots.txt cho phép, mỗi lượt đúng 1 GET.
  * Crossref theo TIÊU ĐỀ (`crossref_title_lane`): khuyến cáo của hiệp hội đăng trên tạp chí của họ (ACC/AHA, ESC,
    ADA, IDSA, EULAR, AASLD, KDIGO, ATS, ERS, AGS, ACP, ASCO, ESMO, ASH, AGA, ACG, BTS, AAN, ACR): lọc theo ISSN +
    cụm từ tiêu đề, loại đính chính/thư.

Mọi hàm trả danh sách dict {title, url, date, summary, doi, pmid, guideline}; lỗi mạng/định dạng thì log và trả []
(KHÔNG bịa dữ liệu). Đây là lane KHÁM PHÁ theo tiêu đề: bản ghi vẫn phải qua cổng xác minh/duyệt như mọi ứng viên, KHÔNG
phải nguồn «đã duyệt».
"""
from __future__ import annotations

import html as html_lib
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from defusedxml.ElementTree import fromstring as _safe_fromstring  # chống XXE/billion-laughs

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
WHO_IRIS_OAI = "https://iris.who.int/oai/request"
WHO_IRIS_HQ_SET = "com_10665_8"        # «1. Headquarters»: ấn phẩm của trụ sở WHO
KCB_PHAC_DO = "https://kcb.vn/phac-do"
KCB_GOC = "https://kcb.vn"
CROSSREF_WORKS = "https://api.crossref.org/works"

CUA_SO_MAC_DINH = 60          # ngày: lane cập nhật thường xuyên (Europe PMC, WHO)
CUA_SO_GUIDELINE = 365        # ngày: guideline hiếm (vài cái/năm/hiệp hội) nên nhìn xa hơn

# Tiêu đề là THƯ/ĐÍNH CHÍNH/BÌNH LUẬN chứ không phải khuyến cáo nên loại. Đo thật: «Correction to: 2026 ACC/AHA
# … Guideline», «Response to correspondence on EULAR recommendations…», «Erratum: AASLD Practice Guidance…».
RE_LOAI_TRU = re.compile(
    r"^\s*(?:correction|erratum|errata|corrigendum|corrigenda|retraction|retracted|withdrawn|response|reply|"
    r"comment|comments|correspondence|letter|editorial|clarification|addendum)\b",
    re.IGNORECASE)
# Tiêu đề mang tính khuyến cáo (điều kiện CHUNG; mỗi lane còn có regex tổ chức riêng).
RE_LA_KHUYEN_CAO = re.compile(
    r"\b(?:guidelines?|guidance|recommendations?|standards of care|consensus|position statement|"
    r"scientific statement|practice advisory|focused update|clinical practice|criteria|hướng dẫn|khuyến cáo)\b",
    re.IGNORECASE)
_RE_THE_DONG = re.compile(r"</?(?:i|b|u|em|strong|sup|sub|span|small|mark)\b[^>]*>", re.IGNORECASE)   # thẻ trong dòng
_RE_THE = re.compile(r"<[^>]+>")
_RE_KHOANG = re.compile(r"\s+")


def sach_van_ban(text: object) -> str:
    """Bỏ thẻ HTML/JATS và gộp khoảng trắng. Thẻ TRONG DÒNG (in nghiêng, chỉ số…) bỏ hẳn, không chèn dấu cách."""
    return _RE_KHOANG.sub(" ", _RE_THE.sub(" ", _RE_THE_DONG.sub("", str(text or "")))).strip()


def _tu_ngay(since_date: Optional[str], so_ngay: int) -> str:
    if since_date and re.match(r"^\d{4}-\d{2}-\d{2}", since_date):
        return since_date[:10]
    return (date.today() - timedelta(days=so_ngay)).isoformat()


def _sap_giam_dan_theo_ngay(muc: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(muc, key=lambda m: str(m.get("date") or ""), reverse=True)


# ─────────────────────────────── Europe PMC ───────────────────────────────

def europepmc_lane(http: Any, epmc_query: str, max_results: int, since_date: Optional[str] = None,
                   guideline: bool = False, so_ngay: int = CUA_SO_MAC_DINH) -> List[Dict[str, Any]]:
    """Bài MỚI NHẤT khớp `epmc_query` trong Europe PMC (MEDLINE/PMC), sắp theo ngày đăng lần đầu giảm dần."""
    tu = _tu_ngay(since_date, so_ngay)
    params = {
        "query": f"({epmc_query}) AND FIRST_PDATE:[{tu} TO {date.today().isoformat()}]",
        "format": "json", "resultType": "core", "sort": "FIRST_PDATE_D desc",
        "pageSize": max(1, min(int(max_results), 100)),
    }
    try:
        data = http.get_json(EUROPEPMC, params=params)
        ket_qua = (data.get("resultList") or {}).get("result") or []
    except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
        logger.warning("[europepmc_lane] lỗi truy vấn Europe PMC, BỎ QUA (KHÔNG bịa dữ liệu): %s", exc)
        return []
    out: List[Dict[str, Any]] = []
    for r in ket_qua:
        if not isinstance(r, dict):
            continue
        tieu_de = sach_van_ban(r.get("title")).rstrip(".").strip()
        if not tieu_de:
            continue
        pmid = str(r.get("pmid") or "").strip() or None
        doi = str(r.get("doi") or "").strip().lower() or None
        nguon, ma = str(r.get("source") or ""), str(r.get("id") or "")
        url = (f"https://europepmc.org/article/{nguon}/{ma}" if nguon and ma
               else (f"https://doi.org/{doi}" if doi else None))
        out.append({"title": tieu_de, "url": url, "date": str(r.get("firstPublicationDate") or "") or None,
                    "summary": sach_van_ban(r.get("abstractText")), "doi": doi, "pmid": pmid, "guideline": guideline})
    return out


# ─────────────────────────────── WHO IRIS (OAI-PMH) ───────────────────────────────

_NS_OAI = "{http://www.openarchives.org/OAI/2.0/}"
_NS_DC = "{http://purl.org/dc/elements/1.1/}"
_RE_WHO_KHUYEN_CAO = re.compile(r"\b(?:guidelines?|guidance|recommendations?|consolidated|standards)\b", re.IGNORECASE)
_MAX_TRANG_OAI = 4


def _dc(rec: ET.Element, ten: str) -> List[str]:
    return [(e.text or "").strip() for e in rec.iter(f"{_NS_DC}{ten}") if (e.text or "").strip()]


def _ngay_oai(rec: ET.Element) -> Optional[str]:
    """Ngày công bố thật (`dc:date`), đủ 10 ký tự; chỉ có năm hoặc năm-tháng thì lấy CUỐI kỳ (không đẩy sớm)."""
    for d in _dc(rec, "date"):
        m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", d)
        if m:
            y, mo, dd = m.group(1), m.group(2), m.group(3)
            return f"{y}-{mo or '12'}-{dd or '28'}"
    return None


def who_iris_lane(http: Any, max_results: int, since_date: Optional[str] = None, oai_set: str = WHO_IRIS_HQ_SET,
                  so_ngay: int = CUA_SO_MAC_DINH) -> List[Dict[str, Any]]:
    """Ấn phẩm dạng guideline/khuyến cáo mới của WHO qua OAI-PMH (`ListRecords`, dc). Tối đa vài trang, mỗi trang 1 GET.

    `from` của OAI lọc theo NGÀY SỬA BẢN GHI (datestamp), không phải ngày công bố: WHO cập nhật lại cả ấn phẩm cũ.
    Vì vậy chỉ giữ bản ghi có `dc:date` (ngày công bố thật) từ mốc trở đi và tiêu đề có tính khuyến cáo."""
    tu = _tu_ngay(since_date, so_ngay)
    params: Dict[str, str] = {"verb": "ListRecords", "metadataPrefix": "oai_dc", "from": tu, "set": oai_set}
    giu: List[Dict[str, Any]] = []
    for _ in range(_MAX_TRANG_OAI):
        try:
            xml_text = http.get_text(WHO_IRIS_OAI, params=params)
            goc = _safe_fromstring(xml_text)
        except Exception as exc:  # pragma: no cover - lỗi mạng/định dạng thực tế
            logger.warning("[who_iris_lane] lỗi OAI-PMH, BỎ QUA (KHÔNG bịa dữ liệu): %s", exc)
            break
        if goc.find(f"{_NS_OAI}error") is not None:      # vd noRecordsMatch: không có bản ghi trong cửa sổ
            break
        for rec in goc.iter(f"{_NS_OAI}record"):
            if "governing bodies" in " ".join(_dc(rec, "type")).lower():
                continue
            tieu_de = sach_van_ban((_dc(rec, "title") or [""])[0])
            if not tieu_de or not _RE_WHO_KHUYEN_CAO.search(tieu_de):
                continue
            ngay = _ngay_oai(rec)
            if ngay is None or ngay < tu:
                continue
            url = next((i for i in _dc(rec, "identifier") if i.startswith("http")), None)
            mo_ta = sach_van_ban(" ".join(_dc(rec, "description")))[:600]
            giu.append({"title": tieu_de, "url": url, "date": ngay, "summary": mo_ta,
                        "doi": None, "pmid": None, "guideline": True})
        token = goc.find(f".//{_NS_OAI}resumptionToken")
        if token is None or not (token.text or "").strip() or len(giu) >= max_results:
            break
        params = {"verb": "ListRecords", "resumptionToken": token.text.strip()}
    return _sap_giam_dan_theo_ngay(giu)[: max(1, int(max_results))]


# ─────────────────────────────── Bộ Y tế Việt Nam (kcb.vn) ───────────────────────────────

_RE_KCB_THE_A = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_RE_KCB_HREF = re.compile(r'\bhref="(/phac-do/[^"#?]+)(?:\?[^"#]*)?"', re.IGNORECASE)   # đo thật: có đuôi ?categoryId=…
_RE_KCB_TITLE = re.compile(r'\btitle="([^"]*)"', re.IGNORECASE)
_RE_KCB_NGAY_SO = re.compile(r"ngày\s+(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", re.IGNORECASE)
_RE_KCB_NGAY_CHU = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", re.IGNORECASE)


def _ngay_kcb(tieu_de: str) -> Optional[str]:
    m = _RE_KCB_NGAY_SO.search(tieu_de) or _RE_KCB_NGAY_CHU.search(tieu_de)
    if not m:
        return None
    d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d).isoformat()
    except ValueError:
        return None


def kcb_vn_lane(http: Any, max_results: int, since_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Quyết định ban hành «Hướng dẫn chẩn đoán, điều trị» của Bộ Y tế, từ trang danh sách kcb.vn/phac-do (1 GET)."""
    try:
        html = http.get_text(KCB_PHAC_DO)
    except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
        logger.warning("[kcb_vn_lane] lỗi tải %s, BỎ QUA (KHÔNG bịa dữ liệu): %s", KCB_PHAC_DO, exc)
        return []
    da_thay: set = set()
    out: List[Dict[str, Any]] = []
    for thuoc_tinh, inner in _RE_KCB_THE_A.findall(html):
        h = _RE_KCB_HREF.search(thuoc_tinh)
        if not h:
            continue
        href = h.group(1)
        tt = _RE_KCB_TITLE.search(thuoc_tinh)
        # thuộc tính title thường là tiêu đề ĐẦY ĐỦ (chữ trong thẻ có thể bị cắt); không có thì dùng chữ trong thẻ
        tieu_de = sach_van_ban(unicodedata.normalize(
            "NFC", html_lib.unescape(tt.group(1) if tt and tt.group(1).strip() else inner)))
        if not tieu_de or "quyết định" not in tieu_de.lower() or href in da_thay:
            continue
        da_thay.add(href)
        ngay = _ngay_kcb(tieu_de)
        if since_date and ngay and ngay < since_date[:10]:
            continue
        out.append({"title": tieu_de, "url": KCB_GOC + href, "date": ngay, "summary": "", "doi": None,
                    "pmid": None, "guideline": True})
    return _sap_giam_dan_theo_ngay(out)[: max(1, int(max_results))]


# ─────────────────────────────── Crossref theo tiêu đề ───────────────────────────────

def _so_ngay(muc: object) -> List[int]:
    parts = ((muc or {}).get("date-parts") or [[]])[0] if isinstance(muc, dict) else []
    return [int(x) for x in parts[:3] if isinstance(x, int) and not isinstance(x, bool)]


def _chuoi_ngay(so: List[int]) -> str:
    return "-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(so))


def ngay_crossref(it: dict) -> Optional[str]:
    """Ngày công bố từ Crossref: online-first > ngày phát hành > in.

    Ngày TƯƠNG LAI (số phát hành của tháng sau; đo thật: 2026-10 cho bài đã đăng tháng 9) thì dùng ngày Crossref
    nhận bản ghi (`created`). KHÔNG bịa ngày và không để bài "mới nhất" mang ngày chưa tới làm lệch xếp hạng độ mới."""
    hom_nay = date.today()
    moc = (hom_nay.year, hom_nay.month, hom_nay.day)
    for khoa in ("published-online", "issued", "published-print"):
        so = _so_ngay(it.get(khoa))
        if so and tuple(so) <= moc[: len(so)]:
            return _chuoi_ngay(so)
    so = _so_ngay(it.get("created"))
    return _chuoi_ngay(so) if so else None


def crossref_title_lane(http: Any, issns: List[str], title_query: str, org_regex: Optional[str], max_results: int,
                        since_date: Optional[str] = None, so_ngay: int = CUA_SO_GUIDELINE,
                        mailto: str = "") -> List[Dict[str, Any]]:
    """Khuyến cáo của một hiệp hội trên tạp chí của họ.

    Lọc ISSN + `query.title` (xếp theo độ liên quan), rồi giữ bản ghi có tiêu đề khớp regex tổ chức VÀ có tính khuyến
    cáo, loại đính chính/thư/bình luận. Sắp lại theo ngày công bố giảm dần."""
    issns = [i.strip() for i in issns if i and i.strip()]
    if not issns or not title_query:
        logger.warning("[crossref_title_lane] thiếu ISSN hoặc cụm tìm tiêu đề, BỎ QUA")
        return []
    tu = _tu_ngay(since_date, so_ngay)
    params = {
        "filter": ",".join([f"issn:{i}" for i in issns] + [f"from-pub-date:{tu}", "type:journal-article"]),
        "query.title": title_query, "rows": 60,
        "select": "DOI,title,issued,published-online,published-print,created,URL,abstract",
    }
    if mailto:
        params["mailto"] = mailto
    try:
        data = http.get_json(CROSSREF_WORKS, params=params)
        items = (data.get("message") or {}).get("items") or []
    except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
        logger.warning("[crossref_title_lane] lỗi Crossref (ISSN %s), BỎ QUA (KHÔNG bịa dữ liệu): %s",
                       "|".join(issns), exc)
        return []
    re_org = re.compile(org_regex, re.IGNORECASE) if org_regex else None
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        tieu_de = sach_van_ban((it.get("title") or [""])[0])
        if not tieu_de or RE_LOAI_TRU.match(tieu_de) or not RE_LA_KHUYEN_CAO.search(tieu_de):
            continue
        if re_org is not None and not re_org.search(tieu_de):
            continue
        doi = str(it.get("DOI") or "").strip().lower() or None
        out.append({"title": tieu_de, "url": str(it.get("URL") or "") or (f"https://doi.org/{doi}" if doi else None),
                    "date": ngay_crossref(it), "summary": sach_van_ban(it.get("abstract")), "doi": doi,
                    "pmid": None, "guideline": True})
    return _sap_giam_dan_theo_ngay(out)[: max(1, int(max_results))]
