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
# API công khai của chính trang www.who.int (đứng sau Cloudflare, KHÁC hạ tầng iris.who.int) — xem `who_hub_lane`.
WHO_HUB_API = "https://www.who.int/api/hubs/publications"
WHO_HUB_SITE = "15210d59-ad60-47ff-a542-7ed76645f0c7"   # mã site trang Ấn phẩm, chép từ chính trang /publications/i
WHO_ITEM_URL = "https://www.who.int/publications/i/item"
WHO_DON_API = "https://www.who.int/api/emergencies/diseaseoutbreaknews"
WHO_DON_ITEM_URL = "https://www.who.int/emergencies/disease-outbreak-news/item"
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


# ── MỐC «BÀI MỚI» = NGÀY BẢN GHI XUẤT HIỆN TRONG CHỈ MỤC, KHÔNG PHẢI NGÀY CÔNG BỐ (sửa 30/09/2026) ───────────────────
# Lượt tuần hỏi «có gì mới từ lượt trước» (mốc ≈ 9 ngày). Trước 30/09 mọi lane lọc theo NGÀY CÔNG BỐ ≥ mốc, và bỏ sót
# IM LẶNG (SourceLog vẫn `ok`) ở ba kiểu bản ghi — đo thật 30/09/2026:
#   (1) ngày công bố chỉ khai tới THÁNG. Crossref coi «2026-09» là 01/09 nên mốc 22/09 loại SẠCH bài tháng 9: Lancet
#       có 31 DOI mới trong 8 ngày ⇒ trả 0; `feed_lancet`, `feed_ard_bmj`, `feed_acc_aha_jacc` chưa từng đưa bài nào
#       vào kho. 9 tạp chí chỉ khai tới tháng (Lancet, JACC, Kidney Int, Gastroenterology, Ann Oncol, ARD, BMJ DRC,
#       BMJ Global Health, BMJ Mental Health), 5 tạp chí khai lẫn lộn (AJG, ERJ, JAGS, Ann Intern Med, Stroke);
#   (2) ngày SỐ PHÁT HÀNH tương lai (2026-10, 2026-11): lọt qua mọi mốc, chiếm hết N chỗ đầu suốt nhiều tuần ⇒ lane
#       «đứng hình» — Kidney Int, Gastroenterology, Ann Oncol vào kho 8 bài ở lượt đầu rồi 0 ở các lượt sau, trong khi
#       mỗi tuần có 4–25 DOI mới; ở Europe PMC thì ngược lại, ngày tương lai bị cận trên «hôm nay» loại tới khi tới ngày
#       (guideline EASL–EASD–EASO vào chỉ mục 29/09 mang ngày 01/12 ⇒ hai tháng sau mới được thấy);
#   (3) bản ghi vào chỉ mục TRỄ hơn ngày công bố: 14/83 guideline tháng 8 trong Europe PMC trễ hơn 9 ngày; trong cửa sổ
#       22–30/09 lane «Practice Guideline» thấy 11 bài trong khi có 25 bài mới xuất hiện.
# Mốc đúng cho giám sát là ngày bản ghi LẦN ĐẦU có mặt trong chỉ mục (`created` của Crossref, `FIRST_IDATE` của Europe
# PMC): luôn đủ ngày, không đổi khi nhà xuất bản sửa bản ghi, nên mỗi bài được thấy ở đúng lượt ngay sau khi nó xuất
# hiện. Bài học đo: phép thử 20/09 («31/31 feed trả bài») chạy KHÔNG kèm mốc nên không đi qua đường mà lượt tuần đi.

def bao_bi_cat(ten: str, mo_ta: object, tong: object, lay: int, tu: str) -> None:
    """Chỉ mục báo có NHIỀU bản ghi mới hơn số lane lấy về ⇒ nói ra trong nhật ký, không cắt im lặng.

    «0 bài» và «10 bài» của một lane không có nghĩa là «không còn gì»: mỗi lượt lane chỉ lấy một số tối đa."""
    if isinstance(tong, int) and not isinstance(tong, bool) and tong > lay:
        logger.info("[%s] %s: chỉ mục có %d bản ghi mới từ %s, lane lấy %d — phần còn lại BỊ CẮT theo số tối đa "
                    "mỗi lượt", ten, mo_ta, tong, tu, lay)


def bo_loc_crossref_moi_xuat_hien(since_date: Optional[str], so_ngay: int) -> List[str]:
    """Hai bộ lọc Crossref cho «bản ghi MỚI XUẤT HIỆN từ mốc» — xem khối chú thích ngay trên.

    `from-created-date` là mốc thật. `from-pub-date:<năm trước>-01-01` chỉ là SÀN chống hồi tố: bài cũ được cấp DOI
    muộn (số hoá kho lưu trữ) không bị coi là bài mới."""
    tu = _tu_ngay(since_date, so_ngay)
    return [f"from-created-date:{tu}", f"from-pub-date:{int(tu[:4]) - 1}-01-01"]


# ─────────────────────────────── Europe PMC ───────────────────────────────

def _ngay_epmc(r: Dict[str, Any]) -> Optional[str]:
    """Ngày công bố lần đầu; là ngày TƯƠNG LAI (số phát hành chưa tới) thì dùng ngày VÀO CHỈ MỤC lần đầu.

    Cùng luật với `ngay_crossref`: không bịa ngày, và không để bài mới nhất mang ngày chưa tới làm lệch độ mới."""
    cong_bo = str(r.get("firstPublicationDate") or "") or None
    if cong_bo and cong_bo[:10] > date.today().isoformat():
        return str(r.get("firstIndexDate") or "") or cong_bo
    return cong_bo


def europepmc_lane(http: Any, epmc_query: str, max_results: int, since_date: Optional[str] = None,
                   guideline: bool = False, so_ngay: int = CUA_SO_MAC_DINH) -> List[Dict[str, Any]]:
    """Bản ghi khớp `epmc_query` MỚI XUẤT HIỆN trong Europe PMC (MEDLINE/PMC) từ mốc, sắp theo ngày đăng giảm dần.

    «Mới xuất hiện» = công bố lần đầu HOẶC vào chỉ mục lần đầu (`FIRST_IDATE`) từ mốc — xem khối chú thích «MỐC BÀI
    MỚI» ở trên. Sàn `FIRST_PDATE` từ đầu năm trước chống hồi tố (bài cũ vào chỉ mục muộn không bị coi là mới).
    Giới hạn còn lại: bài được MEDLINE gán loại xuất bản SAU khi đã vào chỉ mục quá một chu kỳ thì cả hai mốc đều đã
    trôi qua — lane lọc theo `PUB_TYPE` vẫn có thể sót những bài đó."""
    tu = _tu_ngay(since_date, so_ngay)
    nay = date.today().isoformat()
    params = {
        "query": (f"({epmc_query}) AND (FIRST_PDATE:[{tu} TO {nay}] OR FIRST_IDATE:[{tu} TO {nay}]) "
                  f"AND FIRST_PDATE:[{int(tu[:4]) - 1}-01-01 TO 3000-12-31]"),
        "format": "json", "resultType": "core", "sort": "FIRST_PDATE_D desc",
        "pageSize": max(1, min(int(max_results), 100)),
    }
    try:
        data = http.get_json(EUROPEPMC, params=params)
        ket_qua = (data.get("resultList") or {}).get("result") or []
    except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
        logger.warning("[europepmc_lane] lỗi truy vấn Europe PMC, BỎ QUA (KHÔNG bịa dữ liệu): %s", exc)
        return []
    bao_bi_cat("europepmc_lane", epmc_query, data.get("hitCount"), len(ket_qua), tu)
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
        out.append({"title": tieu_de, "url": url, "date": _ngay_epmc(r),
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


# ─────────── WHO qua API của www.who.int — chạy được khi VPN BẬT (thêm 01/10/2026, bác sĩ: «VPN luôn bật») ───────────
# Đo thật 01/10/2026 qua Kaspersky VPN: iris.who.int hết giờ MỞ kết nối (lane OAI-PMH ở trên hỏng 4/4 lượt 29/09), còn
# www.who.int trả 200 cho cả hai API dưới đây — cùng nhà phát hành, khác hạ tầng. Đối chiếu kho: hai bài lane IRIS lấy
# ngày 17/09 đều có trên API ấn phẩm («Implementation guidance … wasting» cùng ngày; «WHO guidelines on expanding
# contraceptive options» mang ngày đăng web 23/09 — muộn hơn ngày IRIS vài ngày). Lane Europe PMC «WHO» (epmc_who)
# KHÔNG thay được: 0 bản ghi ở MỌI lượt từ khi tạo. `Tag` không lọc được phía máy chủ (OData báo lỗi 400) ⇒ lọc ở đây;
# ngày thì lọc được.
_TAG_WHO_KHUYEN_CAO = frozenset({"Guideline", "Guidance (normative)"})
# Văn kiện cơ quan quản trị (lane IRIS cũng bỏ) và bản tóm tắt điều hành (trùng ý với chính guideline, gây bản ghi đôi).
_TAG_WHO_BO = frozenset({"Governing bodies documentation", "Executive summary"})
_TRAN_WHO_HUB = 100           # ~36 ấn phẩm/tháng (đo 08–09/2026) ⇒ 100 đủ cho cửa sổ 60 ngày
_TRAN_WHO_DON = 50
_RE_NGAY_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def _goi_who_api(http: Any, url: str, params: Dict[str, str], ten: str, tran: int, tu: str) -> Optional[List[Any]]:
    """GET một API OData của www.who.int → danh sách `value`; None khi lỗi MẠNG (HttpClient đã ghi lỗi + nhãn mạng).

    Bố cục lạ (không có `value` dạng danh sách) ⇒ NÉM lỗi: «0 bản ghi» chỉ được phép khi máy chủ thật sự trả rỗng, không
    được là «đọc hỏng nên rỗng» (xanh giả)."""
    try:
        d = http.get_json(url, params=params)
    except Exception as exc:  # pragma: no cover - lỗi mạng thực tế; HttpClient đã đếm lỗi cuối cho Source Log
        logger.warning("[%s] lỗi gọi API www.who.int, BỎ QUA (KHÔNG bịa dữ liệu): %s", ten, exc)
        return None
    ds = d.get("value") if isinstance(d, dict) else None
    if not isinstance(ds, list):
        raise ValueError(f"[{ten}] bố cục API www.who.int không như dự kiến (thiếu danh sách `value`)")
    if len(ds) >= tran:
        logger.info("[%s] API trả đủ trần %d bản ghi từ %s — có thể còn bản ghi cũ hơn BỊ CẮT", ten, tran, tu)
    return ds


def _ngay_who(x: Dict[str, Any]) -> Optional[str]:
    ngay = str(x.get("PublicationDateAndTime") or "")[:10]
    return ngay if _RE_NGAY_ISO.fullmatch(ngay) else None


def who_hub_lane(http: Any, max_results: int, since_date: Optional[str] = None,
                 so_ngay: int = CUA_SO_MAC_DINH) -> List[Dict[str, Any]]:
    """Ấn phẩm dạng guideline/khuyến cáo mới của WHO qua API trang Ấn phẩm của www.who.int (1 GET).

    Giữ khi `Tag` là Guideline/Guidance (normative) HOẶC tiêu đề có tính khuyến cáo (cùng regex lane IRIS — có guideline
    mang `Tag` «Publication», vd bài «wasting» 17/09); bỏ văn kiện cơ quan quản trị và bản tóm tắt điều hành.

    KHÔNG xin trường `Summary`: đo 01/10/2026 qua VPN, có `Summary` thì máy chủ bốn lần liền quá 30 giây (lượt đầu chỉ
    xong ở lần thử thứ năm); bỏ đi thì 6/6 lần 1–5 giây. Tiêu đề + trang ấn phẩm đủ cho bản tin; tóm tắt đọc ở trang
    đó."""
    tu = _tu_ngay(since_date, so_ngay)
    params = {"sf_site": WHO_HUB_SITE, "sf_provider": "OpenAccessProvider", "sf_culture": "en",
              "$select": "Title,ItemDefaultUrl,PublicationDateAndTime,Tag",
              "$orderby": "PublicationDateAndTime desc", "$top": str(_TRAN_WHO_HUB),
              "$filter": f"PublicationDateAndTime ge {tu}T00:00:00Z"}
    ds = _goi_who_api(http, WHO_HUB_API, params, "who_hub_lane", _TRAN_WHO_HUB, tu)
    giu: List[Dict[str, Any]] = []
    for x in ds or []:
        if not isinstance(x, dict):
            continue
        tieu_de = sach_van_ban(x.get("Title"))
        tag = str(x.get("Tag") or "").strip()
        if not tieu_de or tag in _TAG_WHO_BO:
            continue
        if tag not in _TAG_WHO_KHUYEN_CAO and not _RE_WHO_KHUYEN_CAO.search(tieu_de):
            continue
        ngay = _ngay_who(x)
        if ngay is None or ngay < tu:
            continue
        duong = str(x.get("ItemDefaultUrl") or "")
        giu.append({"title": tieu_de, "url": WHO_ITEM_URL + duong if duong.startswith("/") else None, "date": ngay,
                    "summary": "", "doi": None, "pmid": None, "guideline": True})
    return _sap_giam_dan_theo_ngay(giu)[: max(1, int(max_results))]


def who_don_lane(http: Any, max_results: int, since_date: Optional[str] = None,
                 so_ngay: int = CUA_SO_MAC_DINH) -> List[Dict[str, Any]]:
    """Tin bùng phát dịch CHÍNH THỨC của WHO (Disease Outbreak News) qua API www.who.int (1 GET).

    Là đường thay chạy được khi VPN bật cho feed «mối đe doạ bệnh truyền nhiễm» của ECDC (bị CloudFront chặn qua VPN),
    và phủ toàn cầu (gồm châu Á) thay vì chỉ châu Âu. Đây là TIN dịch, không phải guideline: `guideline` luôn False."""
    tu = _tu_ngay(since_date, so_ngay)
    params = {"sf_culture": "en", "$select": "Title,ItemDefaultUrl,PublicationDateAndTime,Summary",
              "$orderby": "PublicationDateAndTime desc", "$top": str(_TRAN_WHO_DON),
              "$filter": f"PublicationDateAndTime ge {tu}T00:00:00Z"}
    ds = _goi_who_api(http, WHO_DON_API, params, "who_don_lane", _TRAN_WHO_DON, tu)
    giu: List[Dict[str, Any]] = []
    for x in ds or []:
        if not isinstance(x, dict):
            continue
        tieu_de = sach_van_ban(x.get("Title"))
        ngay = _ngay_who(x)
        if not tieu_de or ngay is None or ngay < tu:
            continue
        duong = str(x.get("ItemDefaultUrl") or "")
        giu.append({"title": tieu_de, "url": WHO_DON_ITEM_URL + duong if duong.startswith("/") else None, "date": ngay,
                    "summary": sach_van_ban(html_lib.unescape(str(x.get("Summary") or "")))[:600],
                    "doi": None, "pmid": None, "guideline": False})
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
    params = {
        "filter": ",".join([f"issn:{i}" for i in issns] + bo_loc_crossref_moi_xuat_hien(since_date, so_ngay)
                           + ["type:journal-article"]),
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
    bao_bi_cat("crossref_title_lane", "|".join(issns), (data.get("message") or {}).get("total-results"), len(items),
               _tu_ngay(since_date, so_ngay))
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
