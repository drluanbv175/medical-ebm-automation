"""Concrete live adapters dùng API/feed ổn định, không scraping tự do."""
from __future__ import annotations

from typing import Any, Mapping, Optional
from urllib.parse import quote

from app.config import settings
from app.evidence.citation_verification import SourceMetadata
from app.evidence.live_adapters.base import LiveSourceAdapter, LiveSourceConfig
from app.sources.feeds import DRUG_SAFETY_FEEDS, GUIDELINE_FEEDS
from app.sources.pubmed import EFETCH, ESEARCH
from app.utils.http import HttpClient


def _first(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _year(value: Any) -> str:
    if isinstance(value, str):
        return value[:10]
    if isinstance(value, Mapping):
        parts = value.get("date-parts") or [[None]]
        first = parts[0] if parts else []
        return str(first[0]) if first and first[0] else ""
    return ""


def _unavailable(source_name: str, reason: str) -> SourceMetadata:
    return SourceMetadata(found=False, unavailable=True, raw={"source_name": source_name, "error_state": reason})


class PubMedLiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(LiveSourceConfig("pubmed", "article|guideline", ESEARCH), **kwargs)
        self.http = HttpClient(cache_ttl=0)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        pmid = identifiers.get("pmid")
        if not pmid:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "pmid_required"})
        if not settings.ncbi_email:
            return _unavailable(self.source_name, "ncbi_email_required")
        try:
            xml_text = self.http.get_text(
                EFETCH,
                params={"db": "pubmed", "id": pmid, "retmode": "xml", "email": settings.ncbi_email},
            )
        except Exception:
            return self._lookup_via_europepmc(pmid)
        title = (
            xml_text.split("<ArticleTitle>", 1)[1].split("</ArticleTitle>", 1)[0]
            if "<ArticleTitle>" in xml_text
            else ""
        )
        if not title:
            return self._lookup_via_europepmc(pmid)
        year = xml_text.split("<Year>", 1)[1].split("</Year>", 1)[0] if "<Year>" in xml_text else ""
        return SourceMetadata(
            found=bool(title),
            title=title,
            year_or_version=year,
            source_type="article",
            raw={"source_name": self.source_name, "pmid": pmid},
        )

    def _lookup_via_europepmc(self, pmid: str) -> SourceMetadata:
        data = self.http.get_json(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f"EXT_ID:{pmid} AND SRC:MED", "format": "json", "pageSize": 1},
        )
        item = (data.get("resultList", {}).get("result") or [{}])[0]
        return SourceMetadata(
            found=bool(item.get("title")),
            title=str(item.get("title") or ""),
            authors_or_organization=str(item.get("authorString") or ""),
            year_or_version=str(item.get("firstPublicationDate") or item.get("pubYear") or ""),
            source_type=str(item.get("pubType") or "article"),
            raw={
                "source_name": self.source_name,
                "pmid": pmid,
                "fallback_source": "Europe PMC",
                "fallback_reason": "NCBI_EFETCH_UNAVAILABLE_OR_UNPARSABLE",
            },
        )


class CrossrefLiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            LiveSourceConfig("crossref", "article|book|proceeding", "https://api.crossref.org/works"),
            **kwargs,
        )
        self.http = HttpClient(cache_ttl=0)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        doi = identifiers.get("doi")
        if not doi:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "doi_required"})
        data = self.http.get_json(f"https://api.crossref.org/works/{quote(doi, safe='')}")
        item = data.get("message", {})
        return SourceMetadata(
            found=bool(item),
            title=_first(item.get("title")),
            authors_or_organization=_first(item.get("publisher")),
            year_or_version=_year(item.get("issued")),
            source_type=_first(item.get("type")),
            raw={"source_name": self.source_name, "doi": doi},
        )


class EuropePMCLiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        super().__init__(LiveSourceConfig("europepmc", "article|preprint", endpoint), **kwargs)
        self.http = HttpClient(cache_ttl=0)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        query: Optional[str] = None
        if identifiers.get("pmid"):
            query = f'EXT_ID:{identifiers["pmid"]} AND SRC:MED'
        elif identifiers.get("doi"):
            query = f'DOI:"{identifiers["doi"]}"'
        if not query:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "pmid_or_doi_required"})
        data = self.http.get_json(self.config.endpoint, params={"query": query, "format": "json", "pageSize": 1})
        item = (data.get("resultList", {}).get("result") or [{}])[0]
        return SourceMetadata(
            found=bool(item.get("title")),
            title=str(item.get("title") or ""),
            authors_or_organization=str(item.get("authorString") or ""),
            year_or_version=str(item.get("firstPublicationDate") or item.get("pubYear") or ""),
            source_type=str(item.get("pubType") or "article"),
            raw={"source_name": self.source_name, "query": query},
        )


class OpenAlexLiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            LiveSourceConfig("openalex", "article|preprint|book", "https://api.openalex.org/works"),
            **kwargs,
        )
        self.http = HttpClient(cache_ttl=0)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        doi = identifiers.get("doi")
        if not doi:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "doi_required"})
        params = {"mailto": settings.openalex_email} if settings.openalex_email else {}
        data = self.http.get_json(f"https://api.openalex.org/works/https://doi.org/{doi}", params=params)
        return SourceMetadata(
            found=bool(data.get("display_name")),
            title=str(data.get("display_name") or ""),
            authors_or_organization=str(data.get("host_venue", {}).get("display_name") or ""),
            year_or_version=str(data.get("publication_date") or data.get("publication_year") or ""),
            source_type=str(data.get("type") or "article"),
            raw={"source_name": self.source_name, "doi": doi},
        )


class SemanticScholarLiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        endpoint = "https://api.semanticscholar.org/graph/v1/paper"
        super().__init__(LiveSourceConfig("semantic_scholar", "article|preprint", endpoint), **kwargs)
        self.http = HttpClient(cache_ttl=0)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        doi = identifiers.get("doi")
        pmid = identifiers.get("pmid")
        paper_id = f"DOI:{doi}" if doi else f"PMID:{pmid}" if pmid else ""
        if not paper_id:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "doi_or_pmid_required"})
        data = self.http.get_json(
            f"{self.config.endpoint}/{quote(paper_id, safe=':')}",
            params={"fields": "title,authors,year,publicationTypes,venue"},
        )
        authors = ", ".join(a.get("name", "") for a in data.get("authors", [])[:5])
        return SourceMetadata(
            found=bool(data.get("title")),
            title=str(data.get("title") or ""),
            authors_or_organization=authors or str(data.get("venue") or ""),
            year_or_version=str(data.get("year") or ""),
            source_type=_first(data.get("publicationTypes")) or "article",
            raw={"source_name": self.source_name, "paper_id": paper_id},
        )


class GuidelineRssLiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(LiveSourceConfig("guideline_rss", "guideline|rss", "configured_rss_feeds"), **kwargs)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        url = identifiers.get("url")
        title_hint = identifiers.get("title") or identifiers.get("query") or ""
        if not url and not title_hint:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "url_or_title_required"})
        all_feeds = [*GUIDELINE_FEEDS, *DRUG_SAFETY_FEEDS]
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #91, vòng 6) — bản
        # gốc duyệt danh sách MỘT LẦN, khớp bất kỳ item nào thoả URL CHÍNH
        # XÁC HOẶC tiêu đề chứa chuỗi con `title_hint`, trả về item ĐẦU TIÊN
        # thoả điều kiện ĐÓ (OR). `app/sources/feeds.py` có hàng chục feed
        # tên chứa "BMJ" (bmj_ebm, thorax_bmj, heart_bmj...) — nếu caller
        # truyền ĐÚNG URL của một feed đứng SAU trong danh sách kèm
        # title_hint chung chung ("BMJ"), vòng lặp gặp feed "BMJ" ĐẦU TIÊN
        # (khớp qua title_hint) TRƯỚC KHI tới đúng feed khớp URL, trả về SAI
        # nguồn dù caller đã cung cấp URL chính xác — nói sai provenance
        # (tên tạp chí/tổ chức) cho một trích dẫn. Sửa: khớp URL CHÍNH XÁC
        # (tín hiệu mạnh hơn hẳn) trên TOÀN BỘ danh sách TRƯỚC, chỉ lùi về
        # khớp chuỗi con theo title_hint khi không có URL nào khớp.
        if url:
            for item in all_feeds:
                if item.url == url:
                    return SourceMetadata(
                        found=True,
                        title=item.name,
                        authors_or_organization=item.org,
                        year_or_version="",
                        source_type="guideline",
                        raw={"source_name": self.source_name, "url": item.url, "feed_id": item.id},
                    )
        if title_hint:
            for item in all_feeds:
                if title_hint.casefold() in item.name.casefold():
                    return SourceMetadata(
                        found=True,
                        title=item.name,
                        authors_or_organization=item.org,
                        year_or_version="",
                        source_type="guideline",
                        raw={"source_name": self.source_name, "url": item.url, "feed_id": item.id},
                    )
        return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "not_found"})


class OpenFDALiveAdapter(LiveSourceAdapter):
    def __init__(self, **kwargs: object) -> None:
        endpoint = "https://api.fda.gov/drug/event.json"
        super().__init__(LiveSourceConfig("openfda", "drug_safety", endpoint), **kwargs)
        self.http = HttpClient(cache_ttl=0)

    def _lookup_live(self, identifiers: Mapping[str, str]) -> SourceMetadata:
        drug = identifiers.get("drug_name") or identifiers.get("query")
        if not drug:
            return SourceMetadata(found=False, raw={"source_name": self.source_name, "reason": "drug_name_required"})
        data = self.http.get_json(
            self.config.endpoint,
            params={"search": f'patient.drug.medicinalproduct:"{drug}"', "limit": 1},
        )
        meta = data.get("meta", {})
        found = bool(data.get("results"))
        return SourceMetadata(
            found=found,
            title=f"openFDA drug safety signal for {drug}" if found else "",
            authors_or_organization="openFDA",
            year_or_version=str(meta.get("last_updated") or ""),
            source_type="drug_safety",
            raw={"source_name": self.source_name, "drug_name": drug},
        )
