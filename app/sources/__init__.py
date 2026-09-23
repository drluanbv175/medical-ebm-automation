"""Các connector nguồn dữ liệu (API-first, fallback mock/manual import).

Hàm `get_enabled_sources()` trả về danh sách connector đang bật theo cấu hình (quét song song).
Hàm `get_fallback_sources()` trả về các tầng DỰ PHÒNG có cổng (Consensus, SerpApi Scholar) — KHÔNG
nằm trong `get_enabled_sources()` (xem app/services/fallback_ladder.py).

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
ConsensusClient = _nap_client("consensus_api", "ConsensusClient")
CoreClient = _nap_client("core_api", "CoreClient")
CrossrefClient = _nap_client("crossref", "CrossrefClient")
EpistemonikosClient = _nap_client("epistemonikos", "EpistemonikosClient")
EuropePMCClient = _nap_client("europepmc", "EuropePMCClient")
OpenAlexClient = _nap_client("openalex", "OpenAlexClient")
OpenFDAClient = _nap_client("openfda", "OpenFDAClient")
PubMedClient = _nap_client("pubmed", "PubMedClient")
# Trợ thủ (KHÔNG phải SourceClient, KHÔNG phải tầng): kiểm PUBLIC api.scite.ai cho lớp xác minh của nhánh dự phòng.
SciteClient = _nap_client("scite_public", "SciteClient")
ScopusClient = _nap_client("scopus", "ScopusClient")
SerpApiScholarClient = _nap_client("serpapi_scholar", "SerpApiScholarClient")
SemanticScholarClient = _nap_client("semantic_scholar", "SemanticScholarClient")
UnpaywallClient = _nap_client("unpaywall", "UnpaywallClient")
# KHÔNG phải SourceClient, KHÔNG phải nguồn tìm kiếm — tải TOÀN VĂN PDF theo DOI đã
# biết qua Wiley TDM API (xem app/sources/wiley_tdm.py). Cố ý KHÔNG có trong
# get_enabled_sources()/get_fallback_sources() vì không tham gia vòng quét song song.
WileyTdmClient = _nap_client("wiley_tdm", "WileyTdmClient")


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
        (settings.enable_scopus, "ScopusClient", ScopusClient),
        (settings.enable_core, "CoreClient", CoreClient),
        (settings.enable_epistemonikos, "EpistemonikosClient", EpistemonikosClient),
        # SerpApi Scholar và Consensus KHÔNG còn ở đây (đổi 20/09/2026): chúng là nguồn DỰ PHÒNG có cổng, chỉ
        # chạy SAU khi các nguồn miễn phí đã trả lời và chỉ cho truy vấn còn thiếu chứng cứ đáng tin — xem
        # get_fallback_sources() và app/services/fallback_ladder.py. Nếu để chúng ở đây, mọi vòng quét
        # song song (ingest_all, research/dossier.py, research/manager.py) sẽ gọi mù nguồn TÍNH PHÍ.
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


# Tên tầng dự phòng hợp lệ trong FALLBACK_ORDER, theo thứ tự mặc định của bậc thang.
_TANG_DU_PHONG_MAC_DINH = ("consensus", "serpapi_scholar")


def _phan_tich_thu_tu_du_phong(chuoi: str) -> List[str]:
    """Tách FALLBACK_ORDER thành danh sách tên tầng; tên lạ thì NỔ TO (ValueError), rỗng thì dùng mặc định."""
    ten_hop_le = set(_TANG_DU_PHONG_MAC_DINH)
    thu_tu: List[str] = []
    for phan in (chuoi or "").split(","):
        ten = phan.strip().lower()
        if not ten:
            continue
        if ten not in ten_hop_le:
            raise ValueError(
                f"FALLBACK_ORDER chứa tên tầng lạ {ten!r} — chỉ chấp nhận {sorted(ten_hop_le)} "
                "(phân cách bằng dấu phẩy).")
        if ten not in thu_tu:
            thu_tu.append(ten)
    return thu_tu or list(_TANG_DU_PHONG_MAC_DINH)


def get_fallback_sources() -> List[SourceClient]:
    """Trả về các tầng DỰ PHÒNG đang BẬT, theo thứ tự `settings.fallback_order` (tầng 1 chạy trước).

    Chỉ dựng client cho tầng có cờ bật: ConsensusClient khi `enable_consensus`, SerpApiScholarClient khi
    `enable_serpapi_scholar`. Tầng đang BẬT mà không nạp được thì NỔ ImportError to rõ (cùng phong cách
    get_enabled_sources — không âm thầm bỏ tầng). Tầng đang bật nhưng KHÔNG có trong FALLBACK_ORDER được nối
    vào CUỐI (theo thứ tự mặc định) kèm cảnh báo, thay vì bị bỏ im lặng.
    """
    thu_tu = _phan_tich_thu_tu_du_phong(settings.fallback_order)
    bang = {
        "consensus": (settings.enable_consensus, "ConsensusClient", ConsensusClient),
        "serpapi_scholar": (settings.enable_serpapi_scholar, "SerpApiScholarClient", SerpApiScholarClient),
    }
    for ten in _TANG_DU_PHONG_MAC_DINH:
        if bang[ten][0] and ten not in thu_tu:
            from app.utils.logging_config import get_logger
            get_logger(__name__).warning(
                "Tầng dự phòng %r đang BẬT nhưng không có trong FALLBACK_ORDER=%r — nối vào cuối bậc thang.",
                ten, settings.fallback_order)
            thu_tu.append(ten)
    ket_qua: List[SourceClient] = []
    for ten in thu_tu:
        enabled, ten_lop, lop = bang[ten]
        if not enabled:
            continue
        if lop is None:
            raise ImportError(
                f"Tầng dự phòng {ten_lop} đang BẬT nhưng không nạp được: {_IMPORT_LOI[ten_lop]}"
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
    "ScopusClient",
    "SerpApiScholarClient",
    "ConsensusClient",
    "SciteClient",
    "CoreClient",
    "EpistemonikosClient",
    "SemanticScholarClient",
    "UnpaywallClient",
    "WileyTdmClient",
    "get_enabled_sources",
    "get_fallback_sources",
]
