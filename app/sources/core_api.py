"""Connector CORE API (core.ac.uk) — thêm 16/09/2026 theo yêu cầu bác sĩ, sau khi
khảo sát toàn hệ xác định đây là nguồn Open Access bổ sung MIỄN PHÍ, TỰ ĐĂNG KÝ NGAY
(không cần duyệt), bổ trợ cho Unpaywall khi Unpaywall không tìm ra bản OA cho một
DOI (CORE gộp >450 triệu bản ghi từ >16.000 kho lưu trữ, gồm cả luận văn/báo cáo
xám mà Unpaywall không phủ).

XÁC MINH TRỰC TIẾP 16/09/2026 qua trình duyệt thật (Cloudflare chặn urllib/WebFetch
headless — cùng lớp chặn đã ghi nhận với ACC/AHA, phải dùng Browser thật):
  • Trang https://api.core.ac.uk/docs/v3 (Redoc chính thức) — endpoint tìm kiếm
    `GET https://api.core.ac.uk/v3/search/works?q=<truy vấn>&limit=&offset=&sort=`,
    xác thực bằng header `Authorization: Bearer <apikey>` (không phải query param —
    khác NCBI/Elsevier — nên KHÔNG cần lớp che tham số nhạy cảm của HttpClient).
  • Trang https://core.ac.uk/services/api — đăng ký key: chỉ cần NHẬP EMAIL, bấm
    "REGISTER NOW", key gửi thẳng qua email — KHÔNG tài khoản/mật khẩu, KHÔNG chờ
    duyệt (khác Epistemonikos). Trang cũng tự khai "Free API access WITHOUT
    registration" ở nhịp thấp hơn (1 batch hoặc 5 request đơn/10 giây) — vì vậy
    khác Scopus (0 quyền truy cập nếu thiếu key), CORE vẫn thử gọi được khi thiếu
    key, chỉ cảnh báo nhịp thấp thay vì chặn cứng.

GIỚI HẠN CHƯA XÁC MINH ĐƯỢC, ghi rõ để không hiểu nhầm đã kiểm hết: trang Redoc chỉ
hiện mẫu response đầy đủ cho `GET /v3/works/{id}` (một bản ghi), dùng snake_case
(`published_date`, `document_type`, `full_text`, `year_published`) — nhưng chính
phần "Search Works" trên CÙNG trang lại viết truy vấn mẫu bằng camelCase
(`yearPublished>=`, `_exists_:fullText`), và bản thân CORE là index Elasticsearch
nên nhiều khả năng THẬT SỰ trả kết quả theo camelCase (đúng tên trường dùng để
truy vấn). Tài liệu Redoc tự mâu thuẫn giữa hai phần — CHƯA có key thật để gọi thử
nên chưa chốt được bên nào đúng. `_lay()` dưới đây vì vậy thử CẢ HAI dạng khoá,
ưu tiên camelCase; sau khi có `CORE_API_KEY` thật, chạy
`python run.py test-live core "heart failure guideline"` một lần rồi đối chiếu
`raw` trong RawRecord để xác nhận — nếu camelCase sai, chỉ cần đổi thứ tự ưu tiên
trong `_lay()`, không phải viết lại connector.

KHÔNG tham gia chuỗi 3 tầng kiểm rút bài của retraction_chain.py — giống
OpenAlex/Crossref/Semantic Scholar/Scopus, CORE không phải nguồn quyết định rút
bài, chỉ là nguồn khám phá/bổ sung full-text.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.core.ac.uk/v3/search/works"


def _lay(entry: Dict[str, Any], *ten_khoa: str) -> Any:
    """Đọc một trường theo NHIỀU tên khoá khả dĩ (camelCase rồi snake_case) —
    xem docstring module: tài liệu chính thức tự mâu thuẫn giữa hai kiểu đặt tên."""
    for khoa in ten_khoa:
        if khoa in entry and entry[khoa] not in (None, ""):
            return entry[khoa]
    return None


def _ten_tap_chi(entry: Dict[str, Any]) -> Optional[str]:
    journals = _lay(entry, "journals") or []
    if isinstance(journals, list) and journals:
        j0 = journals[0]
        if isinstance(j0, dict):
            return j0.get("title") or j0.get("name")
        if isinstance(j0, str):
            return j0
    publisher = _lay(entry, "publisher")
    if isinstance(publisher, str):
        return publisher
    return None


def _danh_sach_tac_gia(entry: Dict[str, Any]) -> Optional[str]:
    authors = _lay(entry, "authors")
    if not authors:
        return None
    ten: List[str] = []
    for a in authors:
        if isinstance(a, dict):
            n = a.get("name")
            if n:
                ten.append(n)
        elif isinstance(a, str):
            ten.append(a)
    return ", ".join(ten) if ten else None


def _url_toan_van(entry: Dict[str, Any]) -> Optional[str]:
    du = _lay(entry, "downloadUrl", "download_url")
    if du:
        return du
    ds = _lay(entry, "sourceFulltextUrls", "source_fulltext_urls")
    if isinstance(ds, list) and ds:
        return ds[0]
    core_id = _lay(entry, "id")
    if core_id:
        return f"https://core.ac.uk/works/{core_id}"
    return None


class CoreClient(SourceClient):
    name = "core"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        headers = {"Accept": "application/json"}
        if settings.core_api_key:
            headers["Authorization"] = f"Bearer {settings.core_api_key}"
        self.http = HttpClient(default_headers=headers)

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        if not settings.core_api_key:
            # KHÁC Scopus (chặn cứng khi thiếu key): CORE tự khai vẫn cho gọi
            # không đăng ký, chỉ ở nhịp thấp hơn — chỉ cảnh báo, không raise.
            logger.warning(
                "[core] ENABLE_CORE=true nhưng thiếu CORE_API_KEY — vẫn gọi được "
                "ở nhịp thấp (theo T&C của core.ac.uk), đăng ký miễn phí tại "
                "https://core.ac.uk/services/api để tăng nhịp."
            )

        core_query = query
        if since_date:
            try:
                nam = int(since_date[:4])
                core_query = f'({query}) AND yearPublished>="{nam}"'
            except ValueError:
                logger.warning("[core] since_date không đúng định dạng YYYY-MM-DD: %r", since_date)

        try:
            params = {
                "q": core_query,
                "limit": min(max_results, 100),
                "offset": 0,
                "sort": "relevance",
            }
            data = self.http.get_json(SEARCH, params=params)
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[core] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        entries = data.get("results") or []
        out: List[RawRecord] = []
        for e in entries:
            try:
                if not isinstance(e, dict):
                    continue
                title = _lay(e, "title") or ""
                doc_type = _lay(e, "documentType", "document_type")
                journal = _ten_tap_chi(e)
                out.append(RawRecord(
                    source=self.name, title=title,
                    authors=_danh_sach_tac_gia(e),
                    journal_or_organization=journal,
                    publication_date=_lay(e, "publishedDate", "published_date", "yearPublished", "year_published"),
                    doi=_lay(e, "doi"),
                    pmid=str(_lay(e, "pubmedId", "pubmed_id")) if _lay(e, "pubmedId", "pubmed_id") else None,
                    abstract=_lay(e, "abstract"),
                    document_type=str(doc_type) if doc_type else None,
                    study_type=infer_study_type(title, str(doc_type) if doc_type else None, journal),
                    clinical_area=clinical_area,
                    url=_url_toan_van(e),
                    ingest_query=query, api_endpoint=SEARCH,
                    raw={"core_id": _lay(e, "id"), "language": _lay(e, "language")},
                ))
            except Exception as exc:  # pragma: no cover
                logger.warning("[core] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s",
                               query, exc)
                continue
        return out
