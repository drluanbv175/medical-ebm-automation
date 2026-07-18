"""Connector PubMed / NCBI E-utilities.

Thật: esearch -> efetch (XML). Ở MVP, parse XML tối giản; nếu lỗi/không có email
hoặc USE_MOCK_SOURCES=true thì fallback mock. Lọc ưu tiên SR/MA/RCT/guideline qua
publication type filter trong query.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from defusedxml.ElementTree import fromstring as _safe_fromstring  # chống XXE/billion-laughs

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Bộ lọc ưu tiên các thiết kế bằng chứng mạnh.
PUBTYPE_FILTER = (
    '("systematic review"[Publication Type] OR "meta-analysis"[Publication Type] '
    'OR "randomized controlled trial"[Publication Type] OR "guideline"[Publication Type] '
    'OR "practice guideline"[Publication Type])'
)


class PubMedClient(SourceClient):
    name = "pubmed"
    endpoint = ESEARCH

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock or not settings.ncbi_email:
            logger.info("[pubmed] dùng mock (use_mock=%s, có email=%s)",
                        self.use_mock, bool(settings.ncbi_email))
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            return self._live_search(query, clinical_area, max_results, since_date)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] lỗi gọi thật (live) — BỎ QUA nguồn này, KHÔNG bịa mock: %s", exc)
            return []

    # -- Live ------------------------------------------------------------
    def _live_search(self, query: str, clinical_area: Optional[str],
                     max_results: int, since_date: Optional[str] = None) -> List[RawRecord]:
        term = f"({query}) AND {PUBTYPE_FILTER}"
        params = {
            "db": "pubmed", "term": term, "retmax": max_results,
            "retmode": "json", "email": settings.ncbi_email, "sort": "date",
        }
        # Lọc theo ngày xuất bản: chỉ bài MỚI kể từ since_date.
        if since_date:
            params["datetype"] = "pdat"
            params["mindate"] = since_date.replace("-", "/")
            params["maxdate"] = "3000/01/01"
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        data = self.http.get_json(ESEARCH, params=params)
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        fetch_params = {
            "db": "pubmed", "id": ",".join(ids), "retmode": "xml",
            "email": settings.ncbi_email,
        }
        if settings.ncbi_api_key:
            fetch_params["api_key"] = settings.ncbi_api_key
        xml_text = self.http.get_text(EFETCH, params=fetch_params)
        self.save_raw(query, xml_text)
        return self._parse_efetch(xml_text, clinical_area, query)

    def _parse_efetch(self, xml_text: str, clinical_area: Optional[str],
                      query: str) -> List[RawRecord]:
        records: List[RawRecord] = []
        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            logger.warning("[pubmed] parse XML lỗi/không an toàn: %s", exc)
            return records
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            title = art.findtext(".//ArticleTitle") or ""
            abstract = " ".join(t.text or "" for t in art.findall(".//AbstractText"))
            journal = art.findtext(".//Journal/Title")
            year = art.findtext(".//PubDate/Year")
            pubtypes = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
            mesh = [m.text for m in art.findall(".//MeshHeading/DescriptorName") if m.text]
            doi = None
            for el in art.findall(".//ArticleId"):
                if el.get("IdType") == "doi":
                    doi = el.text
            authors = ", ".join(
                f"{a.findtext('LastName') or ''} {a.findtext('Initials') or ''}".strip()
                for a in art.findall(".//Author")[:5]
            )
            records.append(RawRecord(
                source=self.name, source_type="article", title=title,
                authors=authors or None, journal_or_organization=journal,
                publication_date=year, doi=doi, pmid=pmid, abstract=abstract or None,
                document_type=pubtypes[0] if pubtypes else None,
                study_type=self._infer_study_type(pubtypes),
                clinical_area=clinical_area, mesh_terms=mesh,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                ingest_query=query, api_endpoint=EFETCH,
            ))
        return records

    # -- Kiểm rút bài CHỦ ĐỘNG (vá 2026-07-15) ---------------------------
    def check_retraction_status(self, pmids: List[str]) -> Dict[str, dict]:
        """Tra cứu CHỦ ĐỘNG trạng thái rút bài/expression-of-concern THẬT từ
        PubMed cho danh sách PMID — khác `app/evidence/retraction_monitor.py`
        (nhánh mồ côi, xem CLAUDE.md) vốn chỉ đọc chữ "retracted"/"withdrawn"
        ĐÃ CÓ SẴN trong metadata truyền vào, không tự tra cứu gì. Xác nhận
        bằng test thật với PMID 9500320 (Wakefield 1998, Lancet — rút 2010):
        PubMed đánh dấu qua CẢ HAI `<PublicationType>Retracted Publication</
        PublicationType>` VÀ `<CommentsCorrections RefType="RetractionIn">`
        (kèm PMID/trích dẫn thông báo rút bài) — hàm này đọc cả hai để không
        bỏ sót trường hợp chỉ có một trong hai (đã gặp khi phiên bản DTD PubMed
        đổi cách gắn cờ theo thời gian).

        Trả {pmid: {"status": ..., ...}}, status một trong:
          "retracted"              — CommentsCorrections RefType="RetractionIn"
                                      hoặc PublicationType="Retracted Publication"
          "expression_of_concern"  — RefType="ExpressionOfConcernIn" (cảnh báo nhẹ hơn)
          "ok"                     — tra được, không có tín hiệu trên
          "unresolved"             — PubMed không trả bản ghi cho PMID này (nghi ma)
          "unknown_mock_or_no_email" — KHÔNG tra cứu thật được (mock/thiếu NCBI_EMAIL/
                                      lỗi mạng) — PHẢI coi là CHƯA XÁC MINH, không phải "ok".
        """
        if not pmids:
            return {}
        if self.use_mock or not settings.ncbi_email:
            reason = ("USE_MOCK_SOURCES=true" if self.use_mock else "thiếu NCBI_EMAIL")
            return {
                pmid: {"status": "unknown_mock_or_no_email",
                       "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là 'ok'"}
                for pmid in pmids
            }
        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "email": settings.ncbi_email}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            xml_text = self.http.get_text(EFETCH, params=params)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] check_retraction_status lỗi gọi thật: %s", exc)
            return {
                pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                for pmid in pmids
            }
        return self._parse_retraction_xml(xml_text, pmids)

    @staticmethod
    def _parse_retraction_xml(xml_text: str, requested_pmids: List[str]) -> Dict[str, dict]:
        results: Dict[str, dict] = {}
        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            logger.warning("[pubmed] parse XML (retraction) lỗi/không an toàn: %s", exc)
            return {pmid: {"status": "unresolved", "reason": f"parse XML lỗi: {exc}"}
                    for pmid in requested_pmids}
        found = set()
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            if not pmid:
                continue
            found.add(pmid)
            pubtypes = {pt.text for pt in art.findall(".//PublicationType") if pt.text}
            retraction_notice = None
            eoc_notice = None
            for cc in art.findall(".//CommentsCorrectionsList/CommentsCorrections"):
                ref_type = cc.get("RefType", "")
                notice = {"pmid": cc.findtext("PMID"), "citation": cc.findtext("RefSource")}
                if ref_type == "RetractionIn":
                    retraction_notice = notice
                elif ref_type == "ExpressionOfConcernIn":
                    eoc_notice = notice
            if "Retracted Publication" in pubtypes or retraction_notice:
                results[pmid] = {"status": "retracted", "retraction_notice": retraction_notice}
            elif "Expression of Concern" in pubtypes or eoc_notice:
                results[pmid] = {"status": "expression_of_concern",
                                  "expression_of_concern_notice": eoc_notice}
            else:
                results[pmid] = {"status": "ok"}
        for pmid in requested_pmids:
            if pmid not in found:
                results[pmid] = {"status": "unresolved",
                                  "reason": "PubMed không trả về bản ghi cho PMID này"}
        return results

    # -- Phân giải METADATA gốc CHỦ ĐỘNG (vá 2026-07-18) ------------------
    def fetch_metadata(self, pmids: List[str]) -> Dict[str, dict]:
        """Phân giải CHỦ ĐỘNG metadata gốc (tác giả·tiêu đề·tạp chí·năm·DOI) THẬT
        từ PubMed cho danh sách PMID — dùng để đối chiếu Bước 1-2 của
        `kiem-chung-trich-dan` (metadata trong bài vs gốc). Khác
        `check_retraction_status()` (chỉ đọc cờ rút bài): hàm này trả metadata
        định danh đầy đủ, làm nền cho `tools/check_citation_metadata.py` ghi
        receipt máy-kiểm A12_METADATA_RECEIPT.json — bằng chứng PMID đã thật sự
        được phân giải, không phải agent tự điền ✅ từ trí nhớ.

        Trả {pmid: {"status": ..., "title", "authors", "journal", "year", "doi"}}:
          "resolved"                 — PubMed trả bản ghi, có metadata gốc
          "unresolved"               — PubMed không trả bản ghi (nghi ma/PMID sai)
          "unknown_mock_or_no_email" — KHÔNG tra cứu thật được (mock/thiếu email/
                                        lỗi mạng) — PHẢI coi là CHƯA phân giải.
        """
        if not pmids:
            return {}
        if self.use_mock or not settings.ncbi_email:
            reason = ("USE_MOCK_SOURCES=true" if self.use_mock else "thiếu NCBI_EMAIL")
            return {
                pmid: {"status": "unknown_mock_or_no_email",
                       "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là đã phân giải"}
                for pmid in pmids
            }
        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "email": settings.ncbi_email}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            xml_text = self.http.get_text(EFETCH, params=params)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] fetch_metadata lỗi gọi thật: %s", exc)
            return {
                pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                for pmid in pmids
            }
        return self._parse_metadata_xml(xml_text, pmids)

    @staticmethod
    def _parse_metadata_xml(xml_text: str, requested_pmids: List[str]) -> Dict[str, dict]:
        results: Dict[str, dict] = {}
        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            logger.warning("[pubmed] parse XML (metadata) lỗi/không an toàn: %s", exc)
            return {pmid: {"status": "unresolved", "reason": f"parse XML lỗi: {exc}"}
                    for pmid in requested_pmids}
        found = set()
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            if not pmid:
                continue
            found.add(pmid)
            title = (art.findtext(".//ArticleTitle") or "").strip()
            journal = (art.findtext(".//Journal/Title") or "").strip()
            year = (art.findtext(".//PubDate/Year")
                    or art.findtext(".//PubDate/MedlineDate") or "").strip()
            doi = None
            for el in art.findall(".//ArticleId"):
                if el.get("IdType") == "doi":
                    doi = (el.text or "").strip() or None
            authors = ", ".join(
                f"{a.findtext('LastName') or ''} {a.findtext('Initials') or ''}".strip()
                for a in art.findall(".//Author")[:5]
            ).strip()
            results[pmid] = {
                "status": "resolved",
                "title": title,
                "authors": authors or None,
                "journal": journal or None,
                "year": year or None,
                "doi": doi,
            }
        for pmid in requested_pmids:
            if pmid not in found:
                results[pmid] = {"status": "unresolved",
                                  "reason": "PubMed không trả về bản ghi cho PMID này"}
        return results

    @staticmethod
    def _infer_study_type(pubtypes: List[str]) -> Optional[str]:
        joined = " ".join(pubtypes).lower()
        if "meta-analysis" in joined or "systematic review" in joined:
            return "systematic_review"
        if "guideline" in joined:
            return "guideline"
        if "randomized" in joined:
            return "rct"
        return None
