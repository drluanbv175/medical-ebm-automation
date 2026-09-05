"""Connector RSS/Atom tổng quát cho feed an toàn thuốc & guideline chính thống.

Parse cả RSS 2.0 (<item>) và Atom (<entry>) bằng thư viện chuẩn (không thêm dependency).
Áp dụng lọc theo since_date (chỉ mục MỚI). Fallback mock khi offline/USE_MOCK_SOURCES.

An toàn thuốc: gắn source_type='drug_safety', study_type='regulatory_alert', và đưa nội
dung vào safety_signal. Guideline: suy study_type từ tiêu đề (classify_meta).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Optional

from defusedxml.ElementTree import fromstring as _safe_fromstring  # chống XXE/billion-laughs

from app.sources._fixtures import MOCK_FEED_ITEMS
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.sources.feeds import FeedConfig
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------------
# Phân loại cảnh báo cơ quan quản lý — vá 13/08/2026
#
# VÌ SAO CÓ: feed `fda_recalls` là "FDA Recalls, Market Withdrawals & Safety
# Alerts" — nó trả TOÀN BỘ thu hồi của FDA: thực phẩm, thiết bị y tế và thuốc.
# Nhưng `_to_record()` gắn `clinical_area="An toàn thuốc"` cho CẢ FEED, nên báo
# cáo An toàn thuốc hằng tuần bị lấp đầy bởi thu hồi salsa, phô mai chay, ớt
# jalapeño, bột rau.
#
# Đo thật trên bản tin 13/08/2026: trong 40 mục "cảnh báo an toàn thuốc CHÍNH
# THỨC mới" chỉ có 8 mục liên quan thuốc; 22 là thực phẩm, 12 là thiết bị. Cảnh
# báo THẬT đáng đọc — "Domperidone: chống chỉ định mới ở u tuỷ thượng thận"
# (MHRA) — bị chôn giữa các vụ thu hồi thực phẩm.
#
# Đây đúng lớp lỗi đã ghi thành bài học trong dự án: nhiễu làm người ta quen bỏ
# qua, rồi bỏ sót cảnh báo thật.
#
# NGUYÊN TẮC AN TOÀN: khi KHÔNG CHẮC thì giữ là "thuoc". Bỏ sót một cảnh báo
# thuốc nguy hiểm hơn nhiều so với để lọt một mục nhiễu — nên bộ lọc này cố ý
# thiên về giữ lại, chỉ loại khi có dấu hiệu RÕ RÀNG là thực phẩm/thiết bị.
#
# Thiết bị và thực phẩm KHÔNG bị vứt bỏ: chúng vẫn được nạp và tra cứu được,
# chỉ tách khỏi báo cáo An toàn thuốc. Bơm insulin rò rỉ vẫn liên quan trực
# tiếp tới bệnh nhân đái tháo đường.
# --------------------------------------------------------------------------

NHAN_CANH_BAO = {
    "thuoc": "An toàn thuốc",
    "thiet_bi": "An toàn thiết bị y tế",
    "thuc_pham": "Thu hồi thực phẩm",
}

# Đường dẫn là tín hiệu ĐÁNG TIN NHẤT — FDA tách sẵn theo mục.
_URL_THIET_BI = re.compile(r"/medical-devices?/", re.I)
_URL_THUOC = re.compile(r"/drug-safety-update/|/drugs/|/vaccines", re.I)

# Chỉ những dấu hiệu RÕ RÀNG là thực phẩm. Cố ý KHÔNG bắt "recall" trần —
# thuốc cũng bị thu hồi (vd Gas-X softgels).
# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 20) — bỏ 4 từ khóa "produce"
# /"juice"/"beverage"/"frozen": chúng KHÔNG phải dấu hiệu RÕ RÀNG là thực phẩm
# như đúng nguyên tắc của bộ lọc này đòi hỏi — cả bốn đều là từ/thuật ngữ dùng
# thường xuyên trong chính văn phong cảnh báo AN TOÀN THUỐC: "produce" là ĐỘNG
# TỪ phổ biến ("can produce severe hypoglycaemia"), "juice" xuất hiện trong
# cảnh báo tương tác kinh điển "grapefruit juice" (statin/thuốc chẹn kênh
# canxi), "beverage" là từ chung cho "tránh đồ uống có cồn/caffein khi dùng
# thuốc X", "frozen" trùng thuật ngữ lâm sàng "frozen shoulder" (đông cứng
# khớp vai/viêm dính bao khớp — tác dụng phụ đã ghi nhận của một số thuốc).
# Xác nhận sống: phan_loai_canh_bao("FDA MedWatch: Insulin glargine dosing
# errors", url_thuoc, "Errors in dose selection can produce severe
# hypoglycaemia...") trả "thuc_pham" trước khi vá — cảnh báo hạ đường huyết
# do insulin bị dán nhãn "Thu hồi thực phẩm" và biến mất khỏi mục an toàn
# thuốc của báo cáo tuần. Các tín hiệu thực phẩm CÒN LẠI (listeria,
# salmonella, undeclared milk/egg..., salsa, cheese, jalapeno, ice cream...)
# đã đủ đặc hiệu để bắt các cảnh báo thu hồi thực phẩm thật — một bản tin thu
# hồi nước trái cây/đồ uống thật hầu như luôn kèm một trong các tín hiệu đó
# (vd "listeria", "undeclared allergen") nên không mất độ phủ thực chất.
_TP = re.compile(
    r"\b(undeclared (milk|egg|soy|peanut|wheat|allergen)|allergy alert|listeria|"
    r"salmonella|e\.? ?coli|salsa|guacamole|pico de gallo|cheese|cheddar|yogurt|"
    r"jalapeno|pepper[s]? because|green powder|seafood|shellfish|"
    r"ice cream|snack|cereal|infant formula|baby food|"
    # Thức ăn thú cưng và mỹ phẩm — FDA quản cả hai, nên chúng lọt vào feed
    # recalls chung. Phát hiện thêm khi rà bản tin 13/08 (Oma's Pride Woof
    # Complete = thức ăn chó; Schwarzkopf = thuốc nhuộm tóc).
    r"pet food|dog food|cat food|treats for (dogs|cats)|raw pet|kibble|"
    r"canine|feline|equine|veterinary|"
    r"shampoo|conditioner|hair (color|dye|care)|cosmetic|lotion|deodorant|"
    r"sunscreen|toothpaste|body wash)\b", re.I)

_TB = re.compile(
    r"\b(device|resuscitation system|anesthesia (delivery|kit)|breathing circuit|"
    r"ankle replacement|catheter|convenience kit|carestation|ventilator|"
    r"infusion (set|pump)|spinal tray|insulin pump|glucose monitor|pacemaker|"
    r"stent|implant|surgical|endoscope|dialysis machine)\b", re.I)


def phan_loai_canh_bao(tieu_de: str, url: str, tom_tat: str = "") -> str:
    """Trả 'thuoc' | 'thiet_bi' | 'thuc_pham' cho một mục cảnh báo.

    Thứ tự: đường dẫn (đáng tin nhất) → từ khoá tiêu đề → mặc định 'thuoc'.
    """
    if _URL_THUOC.search(url):
        return "thuoc"
    if _URL_THIET_BI.search(url):
        return "thiet_bi"
    van_ban = f"{tieu_de} {tom_tat[:400]}"
    if _TB.search(van_ban):
        return "thiet_bi"
    if _TP.search(van_ban):
        return "thuc_pham"
    return "thuoc"          # fail-safe: không chắc thì giữ trong nhóm thuốc


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _find_text(el: ET.Element, *names: str) -> Optional[str]:
    for child in el:
        if _localname(child.tag) in names and (child.text or "").strip():
            return child.text.strip()
    return None


def _find_link(el: ET.Element) -> Optional[str]:
    # RSS: <link>text</link>; Atom: <link href="..."/>
    for child in el:
        if _localname(child.tag) == "link":
            if child.get("href"):
                return child.get("href")
            if (child.text or "").strip():
                return child.text.strip()
    return None


def _parse_date(raw: Optional[str]) -> Optional[str]:
    """Trả về YYYY-MM-DD từ RFC822 (RSS) hoặc ISO8601 (Atom)."""
    if not raw:
        return None
    raw = raw.strip()
    # Thử RFC822
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    # Thử ISO8601
    try:
        iso = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(iso).date().isoformat()
    except ValueError:
        return None


class RSSFeedClient(SourceClient):
    """Một connector cho MỘT feed cụ thể (truyền FeedConfig vào)."""

    def __init__(self, feed: FeedConfig) -> None:
        super().__init__()
        self.feed = feed
        self.name = f"feed_{feed.id}"
        self.endpoint = feed.url
        # Một số CDN (vd FDA/Akamai) chặn User-Agent không giống trình duyệt -> 403.
        # Dùng UA giống trình duyệt để đọc RSS công khai hợp lệ.
        ua = ("Mozilla/5.0 (compatible; medical-ebm-automation/0.1; "
              "RSS reader; +https://example.org/bot)")
        self.http = HttpClient(default_headers={"User-Agent": ua,
                                                "Accept": "application/rss+xml, application/atom+xml, "
                                                "application/xml, text/xml, */*"},
                               cache_ttl=3600)

    def search(self, query: str = "", clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return self._mock(max_results)
        try:
            xml_text = self.http.get_text(self.feed.url, use_cache=True)
            self.save_raw(self.feed.id, xml_text)
            return self._parse(xml_text, max_results, since_date)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[%s] lỗi đọc feed %s — BỎ QUA, KHÔNG bịa mock: %s",
                           self.name, self.feed.url, exc)
            return []

    # -- Parse -----------------------------------------------------------
    def _parse(self, xml_text: str, max_results: int,
               since_date: Optional[str]) -> List[RawRecord]:
        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            logger.warning("[%s] parse XML lỗi/không an toàn: %s", self.name, exc)
            return []
        # Thu thập cả <item> (RSS) và <entry> (Atom)
        entries = [e for e in root.iter() if _localname(e.tag) in ("item", "entry")]
        out: List[RawRecord] = []
        for e in entries:
            title = _find_text(e, "title") or ""
            link = _find_link(e)
            date_raw = _find_text(e, "pubDate", "published", "updated", "date")
            pub_date = _parse_date(date_raw)
            summary = _find_text(e, "description", "summary", "content") or ""

            # Lọc theo since_date (chỉ mục mới)
            if since_date and pub_date and pub_date < since_date:
                continue

            out.append(self._to_record(title, link, pub_date, summary))
            if len(out) >= max_results:
                break
        logger.info("[%s] %d mục từ feed %s", self.name, len(out), self.feed.org)
        return out

    def _to_record(self, title: str, url: Optional[str], pub_date: Optional[str],
                   summary: str) -> RawRecord:
        if self.feed.kind == "drug_safety":
            # Phân loại TỪNG MỤC, không gắn nhãn cả feed (vá 13/08/2026).
            loai = phan_loai_canh_bao(title, url or "", summary)
            return RawRecord(
                source=self.name,
                source_type="drug_safety" if loai == "thuoc" else "safety_other",
                title=title,
                journal_or_organization=self.feed.org, publication_date=pub_date,
                url=url, document_type="regulatory safety communication",
                study_type="regulatory_alert", clinical_area=NHAN_CANH_BAO[loai],
                safety_signal=(summary[:300] or title),
                abstract=summary or None,
                raw={"_feed": self.feed.id, "_org": self.feed.org,
                     "_phan_loai": loai},
                ingest_query=f"feed:{self.feed.id}", api_endpoint=self.feed.url,
            )
        # guideline / nguồn chất lượng cao
        study_type = infer_study_type(title, None, self.feed.org) or None
        return RawRecord(
            source=self.name,
            source_type="guideline" if study_type == "guideline" else "article",
            title=title, journal_or_organization=self.feed.org,
            publication_date=pub_date, url=url, abstract=summary or None,
            document_type="feed item", study_type=study_type,
            clinical_area=self.feed.clinical_area,
            raw={"_feed": self.feed.id, "_org": self.feed.org},
            ingest_query=f"feed:{self.feed.id}", api_endpoint=self.feed.url,
        )

    def _mock(self, max_results: int) -> List[RawRecord]:
        pool = [m for m in MOCK_FEED_ITEMS if m.get("_kind") == self.feed.kind]
        out: List[RawRecord] = []
        for m in pool[:max_results]:
            out.append(self._to_record(m["title"], m.get("url"),
                                       m.get("publication_date"), m.get("summary", "")))
            out[-1].journal_or_organization = m.get("org", self.feed.org)
        return out


def get_feed_clients(drug_safety: bool, guideline: bool) -> List["RSSFeedClient"]:
    from app.sources.feeds import DRUG_SAFETY_FEEDS, GUIDELINE_FEEDS
    clients: List[RSSFeedClient] = []
    if drug_safety:
        clients += [RSSFeedClient(f) for f in DRUG_SAFETY_FEEDS]
    if guideline:
        clients += [RSSFeedClient(f) for f in GUIDELINE_FEEDS]
    return clients
