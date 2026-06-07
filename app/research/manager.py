"""Quản lý dự án nghiên cứu + tích hợp tìm tài liệu nền từ pipeline EBM."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.database import session_scope
from app.models import EvidenceItem, ResearchProject
from app.sources import get_enabled_sources
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

STATUS_FIELDS = [
    "data_collection_status", "ethics_status", "protocol_status",
    "questionnaire_status", "spss_status", "analysis_status",
    "report_status", "manuscript_status",
]


def add_project(data: Dict) -> int:
    """Thêm/cập nhật đề tài theo project_id. Trả về id DB."""
    with session_scope() as s:
        existing = s.query(ResearchProject).filter_by(
            project_id=data["project_id"]).first()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            s.flush()
            return existing.id
        obj = ResearchProject(**{k: v for k, v in data.items()
                                 if hasattr(ResearchProject, k)})
        s.add(obj)
        s.flush()
        return obj.id


def list_projects() -> List[Dict]:
    with session_scope() as s:
        rows = s.query(ResearchProject).order_by(ResearchProject.updated_at.desc()).all()
        return [_to_dict(r) for r in rows]


def update_project(project_id: str, **fields) -> bool:
    with session_scope() as s:
        obj = s.query(ResearchProject).filter_by(project_id=project_id).first()
        if not obj:
            return False
        for k, v in fields.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return True


def link_evidence(project_id: str, evidence_ids: List[int]) -> bool:
    with session_scope() as s:
        obj = s.query(ResearchProject).filter_by(project_id=project_id).first()
        if not obj:
            return False
        current = set(obj.linked_evidence_ids or [])
        current.update(evidence_ids)
        obj.linked_evidence_ids = sorted(current)
        return True


def suggest_background_literature(query: str, clinical_area: Optional[str] = None,
                                  max_results: int = 10) -> List[Dict]:
    """Gợi ý tài liệu nền (guideline/SR/MA/RCT) cho một đề tài.

    Ưu tiên các nguồn mạnh đã có trong DB; nếu chưa có, quét nhanh qua connector.
    Trả về danh sách tài liệu kèm link truy vết.
    """
    results: List[Dict] = []
    with session_scope() as s:
        q = s.query(EvidenceItem).filter(
            EvidenceItem.reliability_tier.in_(["A", "B"]),
            EvidenceItem.is_primary_record.is_(True),
        )
        if clinical_area:
            q = q.filter(EvidenceItem.clinical_area == clinical_area)
        for r in q.limit(max_results).all():
            results.append({
                "id": r.id, "title": r.title, "type": r.study_type,
                "tier": r.reliability_tier, "doi": r.doi, "pmid": r.pmid,
                "url": r.url, "source": r.source,
            })

    if results:
        return results

    # Fallback: quét nhanh connector (mock/live tùy cấu hình).
    for client in get_enabled_sources():
        try:
            for rec in client.search(query, clinical_area=clinical_area,
                                     max_results=max_results):
                results.append({"title": rec.title, "type": rec.study_type,
                                "doi": rec.doi, "pmid": rec.pmid, "url": rec.url,
                                "source": rec.source})
        except Exception as exc:  # pragma: no cover
            logger.warning("Gợi ý tài liệu lỗi nguồn %s: %s", client.name, exc)
        if len(results) >= max_results:
            break
    return results[:max_results]


def _to_dict(r: ResearchProject) -> Dict:
    return {c.name: getattr(r, c.name) for c in r.__table__.columns}
