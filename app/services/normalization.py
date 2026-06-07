"""Bước 2: Normalization – chuyển RawRecord về dict schema chuẩn hóa chung."""
from __future__ import annotations

import re
from typing import Dict

from app.sources.base import RawRecord
from app.utils.text import clean_text


def _clean_doi(doi):
    if not doi:
        return None
    doi = str(doi).strip().lower()
    doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    return doi or None


def _clean_id(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def normalize(record: RawRecord) -> Dict:
    """Map RawRecord -> dict khớp các cột EvidenceItem (chưa có scoring)."""
    return {
        "source": record.source,
        "source_type": record.source_type,
        "title": clean_text(record.title, structured=False) or "",
        "authors": record.authors,
        "journal_or_organization": record.journal_or_organization,
        "publication_date": record.publication_date,
        "update_date": None,
        "doi": _clean_doi(record.doi),
        "pmid": _clean_id(record.pmid),
        "pmcid": _clean_id(record.pmcid),
        "nct_id": _clean_id(record.nct_id),
        "url": record.url,
        "abstract": clean_text(record.abstract, structured=True),
        "document_type": record.document_type,
        "study_type": record.study_type,
        "clinical_area": record.clinical_area,
        "keywords": record.keywords or [],
        "mesh_terms": record.mesh_terms or [],
        "guideline_version": record.guideline_version,
        "safety_signal": clean_text(record.safety_signal, structured=False),
        "official_grade": record.official_grade,
        "ingest_query": record.ingest_query,
        "api_endpoint": record.api_endpoint,
        # Truy vết mock: cờ raw["_mock"] (do _fixtures gắn) -> cột is_mock.
        "is_mock": bool((getattr(record, "raw", None) or {}).get("_mock", False)),
    }


def normalized_title_key(title: str) -> str:
    """Chuẩn hóa tiêu đề cho so khớp trùng (lowercase, bỏ ký tự thừa)."""
    t = (title or "").lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
