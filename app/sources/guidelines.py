"""Quản lý nguồn guideline/khuyến cáo chính thống.

Nhiều tổ chức (WHO, NICE, ESC, ADA, KDIGO, GOLD, GINA, IDSA, EULAR...) KHÔNG có
API công khai hoặc có điều khoản hạn chế crawl. Module này:

1. Giữ DANH MỤC tổ chức + cách lấy dữ liệu ưu tiên (API/RSS/sitemap/manual).
2. Cung cấp `manual_import()` để người dùng nhập tay metadata guideline kèm
   trạng thái xác minh, KHÔNG tự bịa nội dung guideline.

Tôn trọng điều khoản sử dụng: không tự động crawl khi vi phạm ToS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.sources.base import RawRecord

# org -> phương thức lấy dữ liệu ưu tiên (ghi chú vận hành).
GUIDELINE_SOURCES = {
    "WHO": "RSS/website – manual import",
    "NICE": "NICE Syndication API (cần key) / manual import",
    "CDC": "RSS/website – manual import",
    "FDA": "openFDA / RSS Drug Safety – một phần API",
    "EMA": "website – manual import",
    "MHRA": "Drug Safety Update RSS – manual import",
    "ESC": "website – manual import",
    "ACC/AHA": "website / journal – manual import",
    "ADA": "Standards of Care (Diabetes Care) – manual import",
    "KDIGO": "website/journal – manual import",
    "GINA": "website – manual import",
    "GOLD": "website – manual import",
    "IDSA": "website/journal – manual import",
    "EULAR": "Annals Rheum Dis – manual import",
    "ACR": "website/journal – manual import",
    "AASLD": "Hepatology – manual import",
    "EASL": "J Hepatology – manual import",
    "Baveno": "consensus – manual import",
    "ACR Appropriateness Criteria": "website – manual import",
    "LI-RADS": "ACR website – manual import",
    "ESGAR/ESR": "website – manual import",
    "WFUMB": "website – manual import",
}


@dataclass
class ManualGuideline:
    organization: str
    title: str
    version: str
    publication_date: str
    url: str
    clinical_area: Optional[str] = None
    summary: Optional[str] = None
    verification_status: str = "unverified"  # unverified|verified
    official_grade: Optional[str] = None


def manual_import(items: List[ManualGuideline]) -> List[RawRecord]:
    """Chuyển guideline nhập tay thành RawRecord để vào pipeline.

    Mỗi bản ghi mang source='guideline_manual' và giữ trạng thái xác minh.
    """
    out: List[RawRecord] = []
    for g in items:
        out.append(RawRecord(
            source="guideline_manual", source_type="guideline",
            title=g.title, journal_or_organization=g.organization,
            publication_date=g.publication_date, url=g.url,
            document_type="practice guideline", study_type="guideline",
            clinical_area=g.clinical_area, guideline_version=g.version,
            abstract=g.summary, official_grade=g.official_grade,
            raw={"verification_status": g.verification_status,
                 "_manual_import": True},
            ingest_query=f"manual:{g.organization}", api_endpoint="manual",
        ))
    return out
