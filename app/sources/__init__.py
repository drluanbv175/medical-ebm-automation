"""Các connector nguồn dữ liệu (API-first, fallback mock/manual import).

Hàm `get_enabled_sources()` trả về danh sách connector đang bật theo cấu hình.
"""
from typing import List

from app.config import settings
from app.sources.base import SourceClient
from app.sources.clinicaltrials import ClinicalTrialsClient
from app.sources.crossref import CrossrefClient
from app.sources.europepmc import EuropePMCClient
from app.sources.openalex import OpenAlexClient
from app.sources.openfda import OpenFDAClient
from app.sources.pubmed import PubMedClient
from app.sources.semantic_scholar import SemanticScholarClient
from app.sources.unpaywall import UnpaywallClient


def get_enabled_sources() -> List[SourceClient]:
    """Trả về danh sách nguồn bài báo/nghiên cứu đang bật."""
    candidates = [
        (settings.enable_pubmed, PubMedClient),
        (settings.enable_europe_pmc, EuropePMCClient),
        (settings.enable_crossref, CrossrefClient),
        (settings.enable_clinicaltrials, ClinicalTrialsClient),
        (settings.enable_openalex, OpenAlexClient),
        (settings.enable_semantic_scholar, SemanticScholarClient),
    ]
    return [cls() for enabled, cls in candidates if enabled]


__all__ = [
    "SourceClient",
    "PubMedClient",
    "EuropePMCClient",
    "CrossrefClient",
    "ClinicalTrialsClient",
    "OpenFDAClient",
    "OpenAlexClient",
    "SemanticScholarClient",
    "UnpaywallClient",
    "get_enabled_sources",
]
