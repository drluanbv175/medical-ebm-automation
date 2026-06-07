"""Connector RSS/Atom tổng quát cho feed an toàn thuốc & guideline chính thống.

Parse cả RSS 2.0 (<item>) và Atom (<entry>) bằng thư viện chuẩn (không thêm dependency).
Áp dụng lọc theo since_date (chỉ mục MỚI). Fallback mock khi offline/USE_MOCK_SOURCES.

An toàn thuốc: gắn source_type='drug_safety', study_type='regulatory_alert', và đưa nội
dung vào safety_signal. Guideline: suy study_type từ tiêu đề (classify_meta).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Optional

from app.sources._fixtures import MOCK_FEED_ITEMS
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.sources.feeds import FeedConfig
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


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
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("[%s] parse XML lỗi: %s", self.name, exc)
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
            return RawRecord(
                source=self.name, source_type="drug_safety", title=title,
                journal_or_organization=self.feed.org, publication_date=pub_date,
                url=url, document_type="regulatory safety communication",
                study_type="regulatory_alert", clinical_area="An toàn thuốc",
                safety_signal=(summary[:300] or title),
                abstract=summary or None,
                raw={"_feed": self.feed.id, "_org": self.feed.org},
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
