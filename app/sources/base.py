"""Interface chung cho mọi nguồn dữ liệu + cấu trúc RawRecord.

Mỗi connector triển khai `search()` trả về list[RawRecord]. Khi không có key /
không truy cập được mạng / USE_MOCK_SOURCES=true, connector dùng `mock_search()`
nhưng vẫn giữ NGUYÊN interface thật để dễ chuyển sang gọi thật.
"""
from __future__ import annotations

import abc
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# THẺ TRƯỜNG PUBMED ([ta] tạp chí, [pt] loại xuất bản, [cn] tác giả tập thể, [ti] tiêu đề...) — MỘT định nghĩa
# DUY NHẤT cho cả repo. Gom 29/09/2026 từ 3 bản chép đã TRÔI LỆCH nhau (serpapi_scholar 7 thẻ, consensus_api 12 thẻ,
# fallback_ladder 17 thẻ); lấy tập RỘNG NHẤT đang có để không nơi nào hồi quy. CLINICAL_AREAS (app/config.py) có
# 8 truy vấn quét theo TẠP CHÍ/tổ chức viết bằng cú pháp này — chỉ PubMed hiểu. Đo 29/09/2026 trên payload thật đã
# lưu (data/raw/): ClinicalTrials.gov trả HTTP 400; Europe PMC, Crossref, OpenAlex trả 200 nhưng là RÁC (vd truy vấn
# NEJM ra "Plantation Technology", "JURNAL TEKNIK PERTAMBANGAN", sách tóm tắt hội nghị — không bài nào của NEJM).
CU_PHAP_PUBMED_RE = re.compile(
    r"\[(?:ta|pt|cn|tiab|mh|majr|dp|ti|tw|au|ad|jour|pdat|sb|mesh|all|la)\]", re.IGNORECASE)
# Mã lý do máy đọc được: ghi ở đầu `error_message` của dòng SourceLog status="skipped" (cùng kiểu tiền tố `du_phong:`).
LY_DO_BO_QUA_CU_PHAP_PUBMED = "bo_qua_cu_phap_pubmed"


def la_truy_van_cu_phap_pubmed(query: Any) -> bool:
    """True nếu truy vấn mang thẻ trường PubMed (xem CU_PHAP_PUBMED_RE); không phải chuỗi thì False."""
    return isinstance(query, str) and CU_PHAP_PUBMED_RE.search(query) is not None


@dataclass
class RawRecord:
    """Bản ghi thô đã được connector trích sơ bộ từ payload nguồn.

    Đây CHƯA phải schema chuẩn hóa cuối cùng; normalization service sẽ map tiếp.
    """

    source: str
    source_type: str = "article"
    title: str = ""
    authors: Optional[str] = None
    journal_or_organization: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    nct_id: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    document_type: Optional[str] = None
    study_type: Optional[str] = None
    clinical_area: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    mesh_terms: List[str] = field(default_factory=list)
    guideline_version: Optional[str] = None
    safety_signal: Optional[str] = None
    official_grade: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    ingest_query: Optional[str] = None
    api_endpoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SourceClient(abc.ABC):
    """Lớp cơ sở cho mọi nguồn."""

    name: str = "base"
    endpoint: str = ""
    # Nguồn có HIỂU thẻ trường PubMed ([ta]/[pt]/[cn]...) không. Mặc định KHÔNG (an toàn khi thêm nguồn mới: bỏ qua
    # có ghi nhận thay vì âm thầm nhận rác/HTTP 400). Chỉ PubMedClient khai True.
    hieu_cu_phap_pubmed: bool = False

    def __init__(self) -> None:
        self.use_mock = settings.use_mock_sources

    def ly_do_bo_qua_truy_van(self, query: str) -> Optional[str]:
        """Mã lý do nguồn này CÓ CHỦ ĐÍCH không gửi truy vấn (hiện chỉ có LY_DO_BO_QUA_CU_PHAP_PUBMED); None = gửi.

        Thuần, không gọi mạng, không ghi log: `ingestion._fetch()` hỏi hàm này TRƯỚC khi gọi `search()` để ghi dòng
        SourceLog status="skipped" — KHÔNG phải lỗi, nhưng cũng KHÔNG được tính là nguồn đã trả lời (khoẻ)."""
        if not self.hieu_cu_phap_pubmed and la_truy_van_cu_phap_pubmed(query):
            return LY_DO_BO_QUA_CU_PHAP_PUBMED
        return None

    def bo_qua_truy_van(self, query: str) -> bool:
        """Chốt đầu `search()` (sau nhánh mock) cho lối gọi ngoài ingestion (dossier, manager, test-live):
        True = KHÔNG gọi mạng, connector trả [] ngay. Ghi log INFO nêu rõ lý do — bỏ qua có chủ đích, không phải lỗi."""
        ly_do = self.ly_do_bo_qua_truy_van(query)
        if ly_do is None:
            return False
        logger.info("[%s] BỎ QUA truy vấn vì cú pháp PubMed (%s: thẻ trường [ta]/[pt]/[cn]... nguồn này không hiểu) "
                    "— không gọi mạng, không tính là lỗi: %r", self.name, ly_do, str(query)[:120])
        return True

    @abc.abstractmethod
    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        """Gọi nguồn thật. Phải bắt lỗi và fallback mock nếu cần.

        since_date: 'YYYY-MM-DD' – chỉ lấy bài kể từ ngày này (lọc 'mới'); None = không lọc.
        """

    def mock_search(self, query: str, clinical_area: Optional[str] = None,
                    max_results: int = 20) -> List[RawRecord]:
        """Mặc định: không có dữ liệu mock. Connector cụ thể override."""
        return []

    # -- Lưu raw payload (không ghi đè dữ liệu cũ) -------------------------
    def save_raw(self, query: str, payload: Any) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        safe_q = "".join(c if c.isalnum() else "_" for c in query)[:40]
        out_dir = settings.raw_dir / self.name
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{ts}_{safe_q}.json"
        try:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover
            logger.warning("Không lưu được raw payload: %s", exc)
        return path
