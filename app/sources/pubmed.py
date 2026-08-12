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
#
# ★ VÁ 2026-07-27 (cổng G0) — TRƯỚC ĐÂY BỘ LỌC NÀY LÀ BẮT BUỘC VỚI MỌI TRUY VẤN, khiến hệ
# MÙ HOÀN TOÀN với nghiên cứu QUAN SÁT. Đo thật trên "outpatient satisfaction hospital":
# 335 hit lọt lưới / 2.916 hit thật — 88% y văn gần đây vô hình. Hệ quả nghiêm trọng cho
# một cổng "phân tích khoảng trống nghiên cứu": một lĩnh vực có 200 cohort và 0 RCT bị báo
# là "THIẾU — chưa có RCT/SR … Khoảng trống lớn — cơ hội nghiên cứu rõ ràng", tức khuyên
# bác sĩ làm một đề tài đã có nhiều người làm. Đề tài hài lòng người bệnh của chính dự án
# này thuộc đúng loại đó. Nay bộ lọc là THAM SỐ: mặc định giữ nguyên (tương thích ngược),
# nhưng caller có thể truyền bộ lọc khác hoặc None để tìm không giới hạn thiết kế.
PUBTYPE_FILTER = (
    '("systematic review"[Publication Type] OR "meta-analysis"[Publication Type] '
    'OR "randomized controlled trial"[Publication Type] OR "guideline"[Publication Type] '
    'OR "practice guideline"[Publication Type])'
)

# Bộ lọc nghiên cứu QUAN SÁT — dùng MeSH thay vì [Publication Type] vì PubMed KHÔNG có
# publication type cho cohort/case-control/cross-sectional (đó là lý do bộ lọc cũ không
# thể tìm ra chúng dù có muốn).
OBSERVATIONAL_FILTER = (
    '("Cohort Studies"[MeSH] OR "Case-Control Studies"[MeSH] '
    'OR "Cross-Sectional Studies"[MeSH] OR "Observational Study"[Publication Type] '
    'OR "Prospective Studies"[MeSH] OR "Retrospective Studies"[MeSH])'
)


class PubMedClient(SourceClient):
    name = "pubmed"
    endpoint = ESEARCH

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None,
               pubtype_filter: Optional[str] = PUBTYPE_FILTER) -> List[RawRecord]:
        """pubtype_filter: None = KHÔNG giới hạn thiết kế (xem chú thích PUBTYPE_FILTER)."""
        if self.use_mock or not settings.ncbi_email:
            logger.info("[pubmed] dùng mock (use_mock=%s, có email=%s)",
                        self.use_mock, bool(settings.ncbi_email))
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            return self._live_search(query, clinical_area, max_results, since_date,
                                     pubtype_filter)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] lỗi gọi thật (live) — BỎ QUA nguồn này, KHÔNG bịa mock: %s", exc)
            return []

    def count_hits(self, query: str, since_date: Optional[str] = None,
                   pubtype_filter: Optional[str] = PUBTYPE_FILTER) -> Optional[int]:
        """SỐ BÀI THẬT khớp truy vấn (esearch Count), KHÔNG phải số bài lấy về.

        ★ VÁ 2026-07-27 (cổng G0): analyze_evidence_gaps() trước đây đếm len(danh sách đã
        lấy) — mà danh sách đó bị chặn trần bởi --max-results (mặc định 15). Đo thật: một
        chủ đề có 34 SR/MA và 16 RCT được ghi vào checkpoint là 15/15. Ngưỡng phân loại
        (n_sr>=3 → "MẠNH", n_rct>=2 …) vì thế BÃO HÒA với gần như mọi chủ đề, và hệ không
        thể phân biệt 3 SR với 3.400 SR. Một cổng có nhiệm vụ nói "khoảng trống nghiên cứu
        ở đâu" mà đếm sai bậc độ lớn thì kết luận của nó không dùng được.
        Trả None nếu không tra được (mock/không mạng/không email) — caller PHẢI phân biệt
        "không biết" với "bằng 0", đúng nguyên tắc không bịa của dự án."""
        if self.use_mock or not settings.ncbi_email:
            return None
        term = f"({query}) AND {pubtype_filter}" if pubtype_filter else f"({query})"
        params = {"db": "pubmed", "term": term, "retmax": 0, "retmode": "json",
                  "email": settings.ncbi_email}
        if since_date:
            params.update(datetype="pdat", mindate=since_date.replace("-", "/"),
                          maxdate="3000/01/01")
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            data = self.http.get_json(ESEARCH, params=params)
            # VÁ 2026-07-27 (kiểm định độc lập): mặc định 0 khi THIẾU khóa "count" là
            # fail-OPEN ngay tại hàm mà lý do tồn tại là "phân biệt KHÔNG BIẾT với BẰNG 0".
            # E-utilities trả {"esearchresult": {"ERROR": "..."}} khi truy vấn hỏng — khi đó
            # 0 nghĩa là "không tra được", không phải "không có bài nào".
            _res = data.get("esearchresult")
            if not isinstance(_res, dict) or "count" not in _res:
                logger.warning("[pubmed] esearch không trả 'count' (%s) — trả None, KHÔNG suy ra 0",
                               str(_res)[:120])
                return None
            return int(_res["count"])
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] count_hits lỗi — trả None (KHÔNG suy ra 0): %s", exc)
            return None

    # -- Live ------------------------------------------------------------
    def _live_search(self, query: str, clinical_area: Optional[str],
                     max_results: int, since_date: Optional[str] = None,
                     pubtype_filter: Optional[str] = PUBTYPE_FILTER) -> List[RawRecord]:
        term = f"({query}) AND {pubtype_filter}" if pubtype_filter else f"({query})"
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
          "unresolved"             — PubMed trả XML hợp lệ nhưng KHÔNG có bản ghi
                                      cho PMID này (nghi trích dẫn ma)
          "unknown_mock_or_no_email" — KHÔNG tra cứu thật được (mock/thiếu NCBI_EMAIL/
                                      lỗi mạng) — PHẢI coi là CHƯA XÁC MINH, không phải "ok".
          "unknown_fetch_error"    — gọi được nhưng KHÔNG đọc được phản hồi (mạng cắt
                                      giữa chừng, NCBI trả trang chặn thay vì XML).
                                      PHẢI coi là CHƯA XÁC MINH — KHÁC "unresolved":
                                      ở đây ta không biết gì cả, không có cơ sở nghi
                                      trích dẫn ma. Tách ra 12/08/2026 sau khi trạng
                                      thái gộp gây báo động giả cho 18 PMID có thật.
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
            # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH):
            # use_cache=False bắt buộc — self.http mặc định cache 24h (settings.http_cache_ttl),
            # phù hợp cho search() (tra cứu y văn thường) nhưng SAI cho kiểm rút bài: một bài bị
            # rút NGAY SAU lần kiểm trước (trong cửa sổ 24h) sẽ không bị phát hiện cho tới khi
            # cache hết hạn, dù receipt vẫn ghi checked_at_utc MỚI tạo cảm giác đã kiểm tra live.
            xml_text = self.http.get_text(EFETCH, params=params, use_cache=False)
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

        # NCBI đôi lúc trả HTTP 200 kèm TRANG HTML "WWW Error Blocked Diagnostic"
        # thay vì XML — hay gặp khi gọi nhiều từ một IP dùng chung (mạng bệnh viện)
        # mà không có NCBI_API_KEY. Nhận ra sớm để nói đúng nguyên nhân và cách sửa,
        # thay vì để nó rơi xuống nhánh "parse XML lỗi" mơ hồ (thêm 12/08/2026).
        dau = (xml_text or "").lstrip()[:400].lower()
        if dau.startswith("<!doctype html") or "blocked diagnostic" in dau:
            logger.warning("[pubmed] NCBI trả trang CHẶN thay vì XML — cần NCBI_API_KEY")
            return {pmid: {"status": "unknown_fetch_error",
                           "reason": "NCBI đang CHẶN máy/IP này (WWW Error Blocked "
                                     "Diagnostic). Đăng ký NCBI_API_KEY miễn phí và đặt "
                                     "vào .env để nâng hạn mức; KHÔNG kết luận gì về PMID."}
                    for pmid in requested_pmids}

        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            # SỬA 12/08/2026: trước đây trả "unresolved" — mà theo docstring của
            # check_retraction_status(), "unresolved" nghĩa là PUBMED KHÔNG CÓ bản
            # ghi cho PMID này, tức NGHI TRÍCH DẪN MA. Lỗi parse XML là chuyện hoàn
            # toàn khác: response bị cắt giữa chừng do mạng chập chờn, hoặc NCBI trả
            # trang chặn thay vì XML. Gộp hai thứ vào một status khiến công cụ gọi
            # nó báo "nghi trích dẫn ma" cho CẢ 18 PMID vốn vừa được chính PubMed
            # xác minh là có thật ở bước trước — báo động giả hàng loạt, và loại báo
            # động này còn tệ hơn không kiểm vì nó làm người ta mất tin vào cảnh báo
            # thật. Nay tách thành status riêng, và caller phải coi là CHƯA KIỂM.
            logger.warning("[pubmed] parse XML (retraction) lỗi/không an toàn: %s", exc)
            return {pmid: {"status": "unknown_fetch_error",
                           "reason": f"không đọc được phản hồi PubMed ({exc}) — "
                                     f"KHÔNG kết luận gì về PMID này"}
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
                                  # SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 10, phat hien
                                  # LOW): thong diep cu ngu y "PMID sai" - nhung neu PubMed tra HTTP
                                  # 200 hop le ma KHONG chua <PubmedArticle> nao cho CA LO (loi tang
                                  # API/NCBI), MOI pmid deu roi vao day du khong sai. Van chan dung
                                  # (fail-closed), chi lam ro nguyen nhan co the.
                                  "reason": "PubMed không trả về bản ghi cho PMID này trong lô truy vấn "
                                            "(PMID có thể sai/không tồn tại, HOẶC lỗi tầng API khiến "
                                            "cả lô bị bỏ sót — nghi lỗi API nếu NHIỀU PMID cùng lô đều "
                                            "'unresolved')"}
        return results

    # -- GỘP: rút bài + metadata trong MỘT efetch (vá 2026-07-18, giảm token) ---
    def check_citations(self, pmids: List[str]) -> Dict[str, Dict[str, dict]]:
        """Gọi PubMed efetch MỘT LẦN cho danh sách PMID rồi trả CẢ trạng thái rút
        bài LẪN metadata gốc — thay cho việc gọi `check_retraction_status()` và
        `fetch_metadata()` riêng (2 efetch cho cùng danh sách PMID = gấp đôi mạng,
        parse, và token đọc kết quả). Dùng bởi `tools/check_citations.py` để ghi cả
        hai receipt (rút bài + metadata) từ một lệnh duy nhất.

        Trả {"retraction": {pmid: {...}}, "metadata": {pmid: {...}}} — mỗi nhánh
        đúng format của `check_retraction_status()`/`fetch_metadata()` tương ứng, để
        các hàm ghi receipt hiện có tái dùng y nguyên (không phân kỳ logic)."""
        if not pmids:
            return {"retraction": {}, "metadata": {}}
        if self.use_mock or not settings.ncbi_email:
            reason = ("USE_MOCK_SOURCES=true" if self.use_mock else "thiếu NCBI_EMAIL")
            retr = {pmid: {"status": "unknown_mock_or_no_email",
                           "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là 'ok'"}
                    for pmid in pmids}
            meta = {pmid: {"status": "unknown_mock_or_no_email",
                           "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là đã phân giải"}
                    for pmid in pmids}
            return {"retraction": retr, "metadata": meta}
        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "email": settings.ncbi_email}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH) — cùng lý
            # do với check_retraction_status(): tắt cache 24h cho cổng kiểm rút bài/trích dẫn.
            xml_text = self.http.get_text(EFETCH, params=params, use_cache=False)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] check_citations lỗi gọi thật: %s", exc)
            retr = {pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                    for pmid in pmids}
            meta = {pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                    for pmid in pmids}
            return {"retraction": retr, "metadata": meta}
        # Một XML → hai parser (không gọi mạng lần 2).
        return {
            "retraction": self._parse_retraction_xml(xml_text, pmids),
            "metadata": self._parse_metadata_xml(xml_text, pmids),
        }

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
            # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH) — cùng lý
            # do với check_retraction_status()/check_citations(): đây cũng là một phần cơ chế
            # A12 THẬT (kiểm metadata trích dẫn), tắt cache để nhất quán và tránh dữ liệu cũ.
            xml_text = self.http.get_text(EFETCH, params=params, use_cache=False)
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
                                  # SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 10, phat hien
                                  # LOW): thong diep cu ngu y "PMID sai" - nhung neu PubMed tra HTTP
                                  # 200 hop le ma KHONG chua <PubmedArticle> nao cho CA LO (loi tang
                                  # API/NCBI), MOI pmid deu roi vao day du khong sai. Van chan dung
                                  # (fail-closed), chi lam ro nguyen nhan co the.
                                  "reason": "PubMed không trả về bản ghi cho PMID này trong lô truy vấn "
                                            "(PMID có thể sai/không tồn tại, HOẶC lỗi tầng API khiến "
                                            "cả lô bị bỏ sót — nghi lỗi API nếu NHIỀU PMID cùng lô đều "
                                            "'unresolved')"}
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
