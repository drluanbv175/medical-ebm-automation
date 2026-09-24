"""Connector Scopus (Elsevier) — thêm 13/09/2026 theo yêu cầu bác sĩ, sau khi có
SCOPUS_API_KEY thật, để mở rộng độ phủ chứng cứ ngoài PubMed/Europe PMC/Crossref/
OpenAlex/Semantic Scholar hiện có.

KHÁC các nguồn mặc định BẬT (PubMed/Crossref/OpenAlex...): Scopus đòi API key
THẬT SỰ bắt buộc — không có key thì 0 quyền truy cập (401 ngay từ request đầu),
khác Semantic Scholar vẫn chạy được không key ở QPS thấp hơn. Vì vậy
`enable_scopus` mặc định TẮT (app/config.py) và `search()` tự chặn SỚM bằng lỗi
rõ ràng nếu bật cờ mà thiếu key, thay vì để mỗi lượt gọi ăn một lỗi 401 mù mờ.

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không ai hiểu nhầm độ phủ dữ liệu:
  • Scopus Search API (endpoint `/content/search/scopus`) KHÔNG trả abstract đầy
    đủ theo mặc định — trả `abstract=None` trừ khi entry có sẵn `dc:description`
    (hiếm). Muốn tóm tắt đầy đủ phải gọi Abstract Retrieval API riêng theo từng
    `eid`/DOI — CHƯA làm ở bản đầu này (phạm vi: tìm kiếm/khám phá nguồn, không
    phải kiểm rút bài — connector này KHÔNG tham gia chuỗi 3 tầng rút bài của
    retraction_chain.py, giống OpenAlex/Crossref/Semantic Scholar).
  • Search API mặc định chỉ trả TÁC GIẢ ĐẦU (`dc:creator`), không phải danh sách
    đầy đủ — cần Abstract Retrieval API để có full author list.
  • Lọc theo ngày dùng cú pháp Scopus `PUBYEAR AFT <năm>` (chỉ theo NĂM, không có
    ngày/tháng) — `AFT` loại trừ chính năm đó nên trừ 1 để bao gồm cả since_date.
"""
from __future__ import annotations

from typing import List, Optional

from app.config import khoa_do_proxy_gan, settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.elsevier.com/content/search/scopus"


def _lay_url_scopus(links: Optional[List[dict]], eid: Optional[str]) -> Optional[str]:
    """Tìm href trong mảng `link[]` có @ref == 'scopus' (trang chi tiết công khai);
    dự phòng dựng URL từ `eid` nếu Elsevier đổi cấu trúc mảng link."""
    for lk in links or []:
        if isinstance(lk, dict) and lk.get("@ref") == "scopus":
            href = lk.get("@href")
            if href:
                return href
    if eid:
        return f"https://www.scopus.com/record/display.uri?eid={eid}&origin=resultslist"
    return None


class ScopusClient(SourceClient):
    name = "scopus"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        headers = {}
        if settings.scopus_api_key:
            headers["X-ELS-APIKey"] = settings.scopus_api_key
        if settings.scopus_insttoken:
            headers["X-ELS-Insttoken"] = settings.scopus_insttoken
        headers["Accept"] = "application/json"
        self.http = HttpClient(
            default_headers=headers or None,
            bind_interface=settings.scopus_bind_interface or None,
        )

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        if not settings.scopus_api_key and not khoa_do_proxy_gan("scopus"):
            # (KHOA_QUA_PROXY khai «scopus» ⇒ proxy Cloud gắn X-ELS-APIKey — không chặn.)
            # Chặn SỚM, rõ ràng — khác để lọt xuống rồi nhận 401 mù mờ từ Elsevier.
            # Cùng nguyên tắc fail-closed của get_enabled_sources(): nguồn BẬT mà
            # thiếu điều kiện thật phải NỔ TO, không âm thầm trả rỗng.
            raise RuntimeError(
                "[scopus] ENABLE_SCOPUS=true nhưng thiếu SCOPUS_API_KEY — "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env rồi thử lại."
            )

        try:
            scopus_query = f"TITLE-ABS-KEY({query})"
            if since_date:
                # AFT loại trừ chính năm đó -> trừ 1 để KHÔNG bỏ sót since_date.
                try:
                    nam = int(since_date[:4]) - 1
                    scopus_query += f" AND PUBYEAR AFT {nam}"
                except ValueError:
                    logger.warning("[scopus] since_date không đúng định dạng YYYY-MM-DD: %r", since_date)
            params = {
                "query": scopus_query,
                "count": min(max_results, 25),  # trần an toàn theo view mặc định (STANDARD)
                "view": "STANDARD",
            }
            data = self.http.get_json(SEARCH, params=params)
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[scopus] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        entries = (data.get("search-results") or {}).get("entry") or []
        out: List[RawRecord] = []
        for e in entries:
            try:
                # Entry lỗi/rỗng của Scopus đôi khi chỉ có {"error": "..."} — bỏ qua,
                # không phải bản ghi thật.
                if "error" in e:
                    continue
                title = e.get("dc:title") or ""
                journal = e.get("prism:publicationName")
                doc_type = e.get("subtypeDescription")
                doi = e.get("prism:doi") or None
                pmid = e.get("pubmed-id") or None
                eid = e.get("eid")
                out.append(RawRecord(
                    source=self.name, title=title,
                    authors=e.get("dc:creator") or None,
                    journal_or_organization=journal,
                    publication_date=e.get("prism:coverDate"),
                    doi=doi, pmid=str(pmid) if pmid else None,
                    abstract=e.get("dc:description") or None,
                    document_type=doc_type,
                    study_type=infer_study_type(title, doc_type, journal),
                    clinical_area=clinical_area,
                    url=_lay_url_scopus(e.get("link"), eid),
                    ingest_query=query, api_endpoint=SEARCH,
                    raw={"eid": eid, "citedby_count": e.get("citedby-count")},
                ))
            except Exception as exc:  # pragma: no cover
                logger.warning("[scopus] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s",
                               query, exc)
                continue
        return out
