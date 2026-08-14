"""Các connector nguồn dữ liệu (API-first, fallback mock/manual import).

Hàm `get_enabled_sources()` trả về danh sách connector đang bật theo cấu hình.

NẠP CHỊU LỖI (15/08/2026): hook SessionStart và các chốt kiểm (chot_hoi_quy_bai_hoc,
canary đầu-cuối) chạy bằng python3 HỆ THỐNG — không có requests/defusedxml. Trước
đây package này import háo hức mọi client nên chết ngay từ
`import app.sources.retraction_chain`, kéo sập cả tầng kiểm rút bài NGOẠI TUYẾN
vốn thuần stdlib (BH34/BH43 đỏ ngày 15/08). Nay client nào thiếu thư viện bên thứ
ba thì VẮNG MẶT CÓ KHAI BÁO trong `_IMPORT_LOI`; code thật sự cần nó sẽ nổ NGAY
với lý do gốc (fail-closed — KHÔNG âm thầm bỏ nguồn, im lặng ≠ an toàn). Dưới venv
~/.ebm-venv đầy đủ thư viện, hành vi giống hệt trước.
"""
from typing import Dict, List

from app.config import settings
from app.sources.base import SourceClient

_IMPORT_LOI: Dict[str, str] = {}


def _nap_client(ten_module: str, ten_lop: str):
    """Nạp một client; thiếu thư viện bên thứ ba thì ghi sổ thay vì chết cả package."""
    try:
        mod = __import__(f"app.sources.{ten_module}", fromlist=[ten_lop])
        return getattr(mod, ten_lop)
    except ModuleNotFoundError as exc:
        _IMPORT_LOI[ten_lop] = f"{exc} — chạy bằng venv ~/.ebm-venv để có đủ thư viện"
        return None


ClinicalTrialsClient = _nap_client("clinicaltrials", "ClinicalTrialsClient")
CrossrefClient = _nap_client("crossref", "CrossrefClient")
EuropePMCClient = _nap_client("europepmc", "EuropePMCClient")
OpenAlexClient = _nap_client("openalex", "OpenAlexClient")
OpenFDAClient = _nap_client("openfda", "OpenFDAClient")
PubMedClient = _nap_client("pubmed", "PubMedClient")
SemanticScholarClient = _nap_client("semantic_scholar", "SemanticScholarClient")
UnpaywallClient = _nap_client("unpaywall", "UnpaywallClient")


def get_enabled_sources() -> List[SourceClient]:
    """Trả về danh sách nguồn bài báo/nghiên cứu đang bật.

    Nguồn đang BẬT mà không nạp được thư viện thì phải NỔ TO ngay tại đây — trả
    về thiếu nguồn trong im lặng chính là lớp lỗi "dữ liệu giả chạy êm" đã gặp
    12/08 (USE_MOCK_SOURCES rơi về True không ai hay).
    """
    candidates = [
        (settings.enable_pubmed, "PubMedClient", PubMedClient),
        (settings.enable_europe_pmc, "EuropePMCClient", EuropePMCClient),
        (settings.enable_crossref, "CrossrefClient", CrossrefClient),
        (settings.enable_clinicaltrials, "ClinicalTrialsClient", ClinicalTrialsClient),
        (settings.enable_openalex, "OpenAlexClient", OpenAlexClient),
        (settings.enable_semantic_scholar, "SemanticScholarClient", SemanticScholarClient),
    ]
    ket_qua: List[SourceClient] = []
    for enabled, ten, lop in candidates:
        if not enabled:
            continue
        if lop is None:
            raise ImportError(
                f"Nguồn {ten} đang BẬT nhưng không nạp được: {_IMPORT_LOI[ten]}"
            )
        ket_qua.append(lop())
    return ket_qua


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
