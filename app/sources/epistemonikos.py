"""Connector Epistemonikos API — thêm 16/09/2026 theo yêu cầu bác sĩ ("kết nối
Epistemonikos", chưa có key). Epistemonikos là CSDL tổng quan hệ thống "matched"
(map một câu hỏi lâm sàng vào MỌI tổng quan/nghiên cứu gốc liên quan) — đúng
trọng tâm "chứng cứ tin cậy nhất" mà Cochrane hiện chỉ tra được gián tiếp qua
PubMed watchlist.

XÁC MINH TRỰC TIẾP 16/09/2026 qua Browser thật tại https://api.epistemonikos.org/
(trang CHÍNH epistemonikos.org bị CloudFront 403 chặn từ mạng này — cả Browser
thật lẫn WebFetch đều bị chặn, cùng lớp chặn đã gặp với ACC/AHA/core.ac.uk; may
là trang TÀI LIỆU API nằm ở SUBDOMAIN riêng (api.epistemonikos.org) không bị
chặn, nên vẫn đọc được nguyên văn, không phải suy đoán):

  • Endpoint: GET https://api.epistemonikos.org/v1/documents/search?q=<từ khoá>
  • Xác thực: header `Authorization: Token token="<token>"` — KHÁC hẳn Bearer
    của CORE/Scopus. **KHÔNG tự đăng ký được** — tài liệu chính thức ghi nguyên
    văn: "If you want to register your application and try our API, please
    contact us [dev at epistemonikos.org]." Bác sĩ phải tự gửi email xin cấp
    token (không phải tài khoản/mật khẩu, nhưng vẫn cần người bên Epistemonikos
    duyệt — khác CORE tự cấp ngay qua email).
  • Response search — đã đọc NGUYÊN VĂN ví dụ thật trong tài liệu (query
    "adjuvant treatment", total_hits=205), không bịa cấu trúc:
      {"search_info": {"total_hits": N, "pages": {"self","next","prev","first","last"}},
       "results": [{"id","title","authors":[...],"journal","year","abstract",
                     "document_uri", "classification"?, "external_links"?}]}
    `classification`/`external_links` CHỈ xuất hiện khi request có `show=...`
    tương ứng — connector này LUÔN xin cả hai để lấy được nhiều dữ liệu nhất.

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không hiểu nhầm đã kiểm hết:
  • search() KHÔNG trả `doi`/`pubmed` trần — chỉ có `external_links.publisher`
    (URL, thường nhưng KHÔNG LUÔN là doi.org) và `external_links.pubmed` (URL
    dạng .../pubmed/<số>). `_doi_tu_url()`/`_pmid_tu_url()` cố trích từ URL,
    KHÔNG đảm bảo lấy được — nhiều "publisher" không phải link doi.org (vd HTA
    Database/report không có DOI).
  • Endpoint search KHÔNG có tham số lọc theo năm phía SERVER (chỉ `sort=year`
    để sắp xếp, không lọc) — khác mọi connector khác trong repo này, `since_date`
    ở đây lọc PHÍA CLIENT sau khi nhận kết quả, không phải gửi lên server.
  • Chỉ lấy TRANG ĐẦU (tối đa 10 bản ghi/lần, theo đúng tài liệu: "the results
    list will have from zero to ten results") — CHƯA làm phân trang nhiều
    trang. Ví dụ response có `page_size=10` trong URL trả về nhưng tài liệu
    KHÔNG liệt `page_size` là tham số hợp lệ trong mục "Parameters" — không đủ
    chắc chắn để coi là tham số điều khiển được, nên KHÔNG tự ý gửi lên.
  • KHÔNG tham gia chuỗi 3 tầng kiểm rút bài của retraction_chain.py — giống
    OpenAlex/Crossref/Semantic Scholar/Scopus/CORE.

CHƯA CÓ TOKEN THẬT để gọi thử (bác sĩ chưa xin quyền lúc viết file này) — test
ở tests/test_epistemonikos.py dùng ĐÚNG ví dụ response thật trích từ tài liệu
chính thức, KHÔNG bịa cấu trúc, nhưng CHƯA xác nhận bằng `test-live` thật. Chạy
`python run.py test-live epistemonikos "<truy vấn>"` sau khi có token để đối
chiếu — nếu response thật lệch tài liệu, chỉ cần sửa parser trong file này.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.epistemonikos.org/v1/documents/search"

# Ánh xạ phân loại CỦA CHÍNH Epistemonikos (đã kiểm định bởi họ) sang study_type
# chuẩn của repo — ưu tiên hơn suy đoán từ tiêu đề vì đây là nhãn CON NGƯỜI/máy
# học của Epistemonikos đã gán, không phải suy luận.
_CLASSIFICATION_SANG_STUDY_TYPE = {
    "systematic-review": "systematic_review",
    "structured-summary-of-systematic-review": "systematic_review",
    "broad-synthesis": "systematic_review",
}

_DOI_RE = re.compile(r"doi\.org/(.+)$", re.IGNORECASE)
_PMID_RE = re.compile(r"/(\d+)/?$")


def _doi_tu_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = _DOI_RE.search(url)
    return m.group(1) if m else None


def _pmid_tu_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = _PMID_RE.search(url)
    return m.group(1) if m else None


class EpistemonikosClient(SourceClient):
    name = "epistemonikos"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        headers = {"Accept": "application/json"}
        if settings.epistemonikos_api_token:
            headers["Authorization"] = f'Token token="{settings.epistemonikos_api_token}"'
        self.http = HttpClient(default_headers=headers)

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        if not settings.epistemonikos_api_token:
            # Khác CORE (vẫn gọi được không key): Epistemonikos đòi token BẮT
            # BUỘC — thiếu token API trả 401 ngay. Chặn sớm để thông báo rõ
            # ràng, cùng nguyên tắc fail-closed của scopus.py.
            raise RuntimeError(
                "[epistemonikos] ENABLE_EPISTEMONIKOS=true nhưng thiếu "
                "EPISTEMONIKOS_API_TOKEN — Epistemonikos KHÔNG tự đăng ký được, "
                "phải gửi email xin cấp token tới dev@epistemonikos.org rồi "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env."
            )

        try:
            params = {"q": query, "show": "classification,external_links"}
            data = self.http.get_json(SEARCH, params=params)
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[epistemonikos] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        entries = data.get("results") or []
        nam_toi_thieu: Optional[int] = None
        if since_date:
            try:
                nam_toi_thieu = int(since_date[:4])
            except ValueError:
                logger.warning("[epistemonikos] since_date không đúng định dạng YYYY-MM-DD: %r",
                               since_date)

        out: List[RawRecord] = []
        for e in entries:
            try:
                if not isinstance(e, dict):
                    continue
                year_str = e.get("year")
                if nam_toi_thieu is not None and year_str:
                    try:
                        if int(str(year_str)[:4]) < nam_toi_thieu:
                            continue
                    except ValueError:
                        pass

                title = e.get("title") or ""
                classification = e.get("classification")
                journal = e.get("journal")
                links = e.get("external_links") or {}
                pubmed_url = links.get("pubmed") if isinstance(links, dict) else None
                publisher_url = links.get("publisher") if isinstance(links, dict) else None
                epi_url = (links.get("epistemonikos") if isinstance(links, dict) else None) or (
                    f"https://www.epistemonikos.org/en/documents/{e.get('id')}"
                    if e.get("id") else None
                )
                authors = e.get("authors")
                study_type = _CLASSIFICATION_SANG_STUDY_TYPE.get(classification) or infer_study_type(
                    title, classification, journal)

                out.append(RawRecord(
                    source=self.name, title=title,
                    authors=", ".join(authors) if isinstance(authors, list) else None,
                    journal_or_organization=journal,
                    publication_date=str(year_str) if year_str else None,
                    doi=_doi_tu_url(publisher_url),
                    pmid=_pmid_tu_url(pubmed_url),
                    abstract=e.get("abstract"),
                    document_type=classification,
                    study_type=study_type,
                    clinical_area=clinical_area,
                    url=epi_url,
                    ingest_query=query, api_endpoint=SEARCH,
                    raw={"epistemonikos_id": e.get("id"), "document_uri": e.get("document_uri"),
                         "total_hits": (data.get("search_info") or {}).get("total_hits")},
                ))
                if len(out) >= max_results:
                    break
            except Exception as exc:  # pragma: no cover
                logger.warning("[epistemonikos] bỏ qua 1 bản ghi hỏng trong trang kết quả "
                               "(query=%r): %s", query, exc)
                continue
        return out
