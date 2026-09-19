"""Connector Consensus API (consensus.app) — thêm 19/09/2026 theo yêu cầu bác sĩ, để bổ sung
chứng cứ cho hệ nghiên cứu y khoa / cập nhật guideline / trích dẫn thực hành lâm sàng ngoài
PubMed/Europe PMC/Crossref/OpenAlex/Semantic Scholar/Scopus hiện có.

KHÔNG nhầm với: (a) nhãn thiết kế `design:'Consensus'` = ĐỒNG THUẬN CHUYÊN GIA trong cổng
`verify_dashboard` (không liên quan gì tới nguồn này); (b) kênh MCP của claude.ai
(`mcp__plugin_bio-research_consensus__search`, skill `tong-thuat-chung-cu`, lệnh
`/tra-consensus`) — đó là kênh riêng cho phiên Claude, KHÔNG chia sẻ mã với connector này,
nhưng CHIA SẺ CHUNG hạn mức lượt gọi hằng tháng của tài khoản Consensus.

Thông số đã tra từ tài liệu chính thức của Consensus NLP (README Consensus-NLP/consensus-api,
docs.consensus.app/llms-full.txt) ngày 19/09/2026; chưa gọi thật trước khi viết file này:
  • `GET https://api.consensus.app/v1/search`, xác thực bằng header `x-api-key`. Endpoint cũ
    `/v1/quick_search` đã deprecated (dự kiến gỡ 2027-02-07) — KHÔNG dùng.
  • Gói Free: 30 lượt/tháng (1 lượt = mỗi 100 bài trả về, làm tròn lên), tối đa 20 bài/yêu cầu,
    không phân trang, không có `study_type`/`takeaway`/toàn văn. 1 yêu cầu/giây. Vượt hạn mức → 429.
  • KẾT QUẢ KHÔNG CÓ PMID — chỉ có DOI (và url trang Consensus). Bản ghi chỉ được kiểm rút bài
    qua đường DOI (Crossref `updated-by`, BH33), KHÔNG tham gia chuỗi 3 tầng PMID của
    `retraction_chain.py` (giống Scopus/OpenAlex/Crossref/Semantic Scholar).

VAI TRÒ (doctrine `_CONNECTOR-CHUNG-CU.md`): Consensus là kênh KHÁM PHÁ. Bản ghi vào kho như một
ứng viên; mọi khẳng định muốn TRÍCH phải truy ngược DOI gốc và qua `kiem-chung-trich-dan` /
`verify_dashboard --online`. Connector này không nâng, không gán mức chứng cứ nào.

QUYẾT ĐỊNH LƯU TRỮ của bác sĩ (19/09/2026): điều khoản của Consensus về lưu cache/lưu trữ kết quả
API KHÔNG tìm thấy (điều khoản consensus.app không nhắc API) ⇒ chọn phương án thận trọng:
  1. KHÔNG ghi payload thô ra đĩa: không gọi `save_raw`, và `HttpClient(cache_ttl=0)` + `use_cache=False`
     (cache HTTP mặc định của repo GHI JSON đầy đủ xuống `data/raw/_http_cache/`).
  2. Chỉ giữ tiêu đề · tác giả · tạp chí · năm · DOI · url · số trích dẫn · tứ phân vị SJR. TUYỆT ĐỐI
     không sao chép `abstract` / `takeaway` (do AI của Consensus sinh) / `full_text_chunks` vào
     `RawRecord` (và vì vậy không vào DB).
  3. Cache CHỈ trong bộ nhớ tiến trình (TTL 6 giờ, khóa theo truy vấn+năm+cỡ trang) để một lượt
     quét không tốn lượt gọi hai lần cho cùng một truy vấn. Khóa cache KHÔNG chứa khóa API.

HẠN MỨC NỘI BỘ (fail-closed): gói Free chỉ 30 lượt/tháng mà một lượt quét pipeline có hàng chục truy
vấn — nếu không chặn, lượt quét đầu tiên sẽ ăn hết hạn mức tháng (kể cả phần dành cho MCP). Nên có sổ
đếm bền `data/state/consensus_quota.json` (khóa theo tháng UTC) và trần `CONSENSUS_MONTHLY_CALL_CAP`
(mặc định 20, chừa dư cho MCP dùng chung). Chạm trần ⇒ NỔ TO bằng RuntimeError (Source Log = error),
KHÔNG im lặng trả `[]` (họ lỗi BH27/BH08: «không kiểm được» bị đọc thành «không có gì mới»). Sổ đếm
hỏng ⇒ cũng nổ to, không đoán.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.consensus.app/v1/search"

# Trần số bài/yêu cầu của gói Free. Giữ ≤100 để mỗi yêu cầu luôn tính đúng 1 lượt.
_PAGE_SIZE_TRAN = 20
# 1 yêu cầu/giây trên mọi gói tự phục vụ; chừa dư 0,1s.
_KHOANG_CACH_GIAY = 1.1
_TTL_BO_NHO_GIAY = 6 * 3600
# Mã lỗi phải NỔ TO (khoá sai/hết hạn/không thuộc gói/tham số sai/hết hạn mức) — khác 5xx/timeout
# chỉ ghi cảnh báo và trả rỗng (health của HttpClient vẫn ghi nhận lỗi, ingestion đánh dấu error).
_MA_LOI_NO_TO = (400, 401, 402, 403, 422, 429)

_dong_ho = time.monotonic
_khoa_bo_nho = threading.Lock()
_BO_NHO: Dict[Tuple[str, Optional[int], int], Tuple[float, List[Dict[str, Any]]]] = {}
_khoa_quota = threading.Lock()


# ---------------------------------------------------------------------------
# Sổ đếm hạn mức tháng (bền, fail-closed)
# ---------------------------------------------------------------------------
def _duong_quota() -> Path:
    return settings.data_dir / "state" / "consensus_quota.json"


def _thang_hien_tai() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _doc_so_dem() -> int:
    """Số lượt đã giữ chỗ trong THÁNG HIỆN TẠI (UTC). File chưa có ⇒ 0; sang tháng mới ⇒ 0.

    File có mà không đọc được / sai cấu trúc ⇒ RuntimeError (không đoán là 0: đoán thấp có thể
    làm vượt hạn mức, mà gói trả phí thì vượt hạn mức là tốn tiền thật).
    """
    path = _duong_quota()
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        thang, so = data["thang"], data["so_lan"]
        if not isinstance(thang, str) or isinstance(so, bool) or not isinstance(so, int) or so < 0:
            raise ValueError("sai kiểu dữ liệu")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"[consensus] sổ đếm hạn mức {path} không đọc được ({exc}) — không đoán số lượt đã dùng. "
            "Kiểm tra số lượt thật trong API & MCP Dashboard của Consensus rồi XOÁ file này để đặt lại."
        ) from exc
    return so if thang == _thang_hien_tai() else 0


def so_lan_goi_thang_nay() -> int:
    """Số lượt gọi (đã giữ chỗ) trong tháng UTC hiện tại — cho `run.py test-live consensus`."""
    with _khoa_quota:
        return _doc_so_dem()


def _giu_cho_luot_goi() -> int:
    """Giữ chỗ MỘT lượt TRƯỚC khi gọi mạng; chạm trần nội bộ ⇒ RuntimeError. Trả số lượt sau khi tăng.

    Đếm thừa (kể cả khi yêu cầu sau đó lỗi mạng) là chủ ý: đếm thiếu mới nguy hiểm.
    """
    tran = int(settings.consensus_monthly_call_cap)
    with _khoa_quota:
        da_dung = _doc_so_dem()
        # Trần ≤ 0 cũng bị chặn ở đây vì da_dung ≥ 0 ≥ tran (không cần vế riêng).
        if da_dung >= tran:
            raise RuntimeError(
                f"[consensus] đã dùng {da_dung}/{max(tran, 0)} lượt gọi trong tháng {_thang_hien_tai()} "
                "(trần nội bộ CONSENSUS_MONTHLY_CALL_CAP; gói Free của Consensus chỉ 30 lượt/tháng và "
                "dùng CHUNG với kênh MCP). Nguồn này bị bỏ qua tới đầu tháng sau, hoặc nâng trần nếu "
                "bạn đã có gói cao hơn."
            )
        path = _duong_quota()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({"thang": _thang_hien_tai(), "so_lan": da_dung + 1}),
                           encoding="utf-8")
            os.replace(tmp, path)
        except OSError as exc:
            # Không ghi được sổ đếm ⇒ không chứng minh được mình còn trong hạn mức ⇒ dừng.
            raise RuntimeError(f"[consensus] không ghi được sổ đếm hạn mức {path}: {exc}") from exc
        return da_dung + 1


# ---------------------------------------------------------------------------
# Cache chỉ trong bộ nhớ (không chạm đĩa)
# ---------------------------------------------------------------------------
def xoa_bo_nho() -> None:
    """Xoá cache bộ nhớ (dùng cho test)."""
    with _khoa_bo_nho:
        _BO_NHO.clear()


def _doc_bo_nho(khoa: Tuple[str, Optional[int], int]) -> Optional[List[Dict[str, Any]]]:
    with _khoa_bo_nho:
        muc = _BO_NHO.get(khoa)
        if muc is None:
            return None
        han, rows = muc
        if _dong_ho() > han:
            _BO_NHO.pop(khoa, None)
            return None
        return [dict(r) for r in rows]


def _ghi_bo_nho(khoa: Tuple[str, Optional[int], int], rows: List[Dict[str, Any]]) -> None:
    with _khoa_bo_nho:
        _BO_NHO[khoa] = (_dong_ho() + _TTL_BO_NHO_GIAY, [dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Phân tích phản hồi — CHỈ giữ trường tối thiểu
# ---------------------------------------------------------------------------
def _doi_sach(doi: Any) -> Optional[str]:
    if not doi:
        return None
    s = str(doi).strip()
    for tien_to in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if s.lower().startswith(tien_to):
            s = s[len(tien_to):]
            break
    return s or None


def _so_nguyen(v: Any) -> Optional[int]:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _mot_dong(item: Any) -> Optional[Dict[str, Any]]:
    """Rút gọn một bài về đúng các trường được phép giữ. Không tiêu đề ⇒ bỏ."""
    if not isinstance(item, dict):
        return None
    title = str(item.get("title") or "").strip()
    if not title:
        return None
    authors = item.get("authors")
    if isinstance(authors, list):
        authors = ", ".join(str(a) for a in authors if a) or None
    elif not isinstance(authors, str):
        authors = None
    nam = item.get("publish_year")
    return {
        "title": title,
        "authors": authors,
        "journal": item.get("journal_name") or None,
        "year": str(nam) if nam not in (None, "") else None,
        "doi": _doi_sach(item.get("doi")),
        "url": item.get("url") or None,
        "citation_count": _so_nguyen(item.get("citation_count")),
        "sjr_quartile": _so_nguyen(item.get("sjr_best_quartile")),
        "is_preprint": bool(item.get("is_preprint")),
    }


def _rut_gon(data: Any) -> List[Dict[str, Any]]:
    """Lấy `results[]` và rút gọn. Phản hồi không có mảng `results` ⇒ NỔ TO (API đổi cấu trúc?),
    không đọc thành «0 kết quả»."""
    ket_qua = data.get("results") if isinstance(data, dict) else None
    if not isinstance(ket_qua, list):
        raise RuntimeError(
            "[consensus] phản hồi không có mảng `results` — API có thể đã đổi cấu trúc; "
            "không coi đây là «0 kết quả»."
        )
    return [r for r in (_mot_dong(i) for i in ket_qua) if r]


def _chan_doan(data: Any) -> Dict[str, Any]:
    """Chỉ TÊN trường và số đếm — không giá trị — để `test-live` cho biết gói Free thật sự trả gì."""
    if not isinstance(data, dict):
        return {}
    ds = data.get("results")
    dau = ds[0] if isinstance(ds, list) and ds and isinstance(ds[0], dict) else {}
    return {
        "truong_goc": sorted(data.keys()),
        "tong_ban_ghi": len(ds) if isinstance(ds, list) else None,
        "truong_ban_ghi_dau": sorted(dau.keys()),
        "so_ban_ghi_co_doi": sum(1 for i in ds if isinstance(i, dict) and i.get("doi"))
        if isinstance(ds, list) else None,
    }


def _nam_tu_since(since_date: Optional[str]) -> Optional[int]:
    if not since_date:
        return None
    try:
        return int(since_date[:4])
    except ValueError:
        logger.warning("[consensus] since_date không đúng định dạng YYYY-MM-DD: %r", since_date)
        return None


class ConsensusClient(SourceClient):
    name = "consensus"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        headers = {"Accept": "application/json"}
        if settings.consensus_api_key:
            headers["x-api-key"] = settings.consensus_api_key  # header, KHÔNG bao giờ đi trong URL/query
        self.http = HttpClient(default_headers=headers, cache_ttl=0, min_interval=_KHOANG_CACH_GIAY)
        # Chỉ tên trường/số đếm của lần gọi thật gần nhất (xem `_chan_doan`).
        self.chan_doan: Dict[str, Any] = {}

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        if not settings.consensus_api_key:
            # Chặn SỚM, rõ ràng (cùng nguyên tắc Scopus): nguồn BẬT mà thiếu điều kiện thật
            # phải NỔ TO, không âm thầm trả rỗng.
            raise RuntimeError(
                "[consensus] ENABLE_CONSENSUS=true nhưng thiếu CONSENSUS_API_KEY — "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env rồi thử lại."
            )

        page_size = max(1, min(int(max_results), _PAGE_SIZE_TRAN))
        nam = _nam_tu_since(since_date)
        khoa_nho = (query.strip().lower(), nam, page_size)

        rows = _doc_bo_nho(khoa_nho)
        if rows is None:
            _giu_cho_luot_goi()  # nổ TO khi chạm trần — cố ý nằm NGOÀI khối try bên dưới
            # Boolean phải là chuỗi thường "true"/"false" (đã xác nhận với API thật ở PR ToolUniverse #568).
            params: Dict[str, Any] = {
                "query": query,
                "page_size": page_size,
                "medical_mode": "true",
                "exclude_preprints": "true",
            }
            if nam is not None:
                params["year_min"] = nam  # theo NĂM, không có ngày/tháng — bao gồm cả năm này
            try:
                data = self.http.get_json(SEARCH, params=params, use_cache=False)
            except requests.HTTPError as exc:
                ma = exc.response.status_code if exc.response is not None else None
                if ma in _MA_LOI_NO_TO:
                    raise RuntimeError(_giai_thich_loi(ma)) from exc
                logger.warning("[consensus] lỗi gọi thật (live) HTTP %s — BỎ QUA, KHÔNG bịa mock: %s", ma, exc)
                return []
            except Exception as exc:  # pragma: no cover
                logger.warning("[consensus] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
                return []
            rows = _rut_gon(data)
            self.chan_doan = _chan_doan(data)
            _ghi_bo_nho(khoa_nho, rows)

        out: List[RawRecord] = []
        for r in rows:
            doi = r["doi"]
            out.append(RawRecord(
                source=self.name, title=r["title"], authors=r["authors"],
                journal_or_organization=r["journal"], publication_date=r["year"],
                doi=doi, pmid=None,
                url=r["url"] or (f"https://doi.org/{doi}" if doi else None),
                abstract=None,  # cố ý: xem đoạn QUYẾT ĐỊNH LƯU TRỮ ở đầu file
                study_type=infer_study_type(r["title"], None, r["journal"],
                                            "PPR" if r["is_preprint"] else None),
                clinical_area=clinical_area,
                ingest_query=query, api_endpoint=SEARCH,
                raw={
                    "vai_tro": "kham_pha_can_xac_minh_doi",
                    "citation_count": r["citation_count"],
                    "sjr_quartile": r["sjr_quartile"],
                },
            ))
        return out


def _giai_thich_loi(ma: Optional[int]) -> str:
    y_nghia = {
        400: "yêu cầu bị từ chối — có thể tham số (medical_mode/exclude_preprints/year_min…) không được API "
             "chấp nhận; chạy `python run.py test-live consensus \"<từ khoá>\"` để xem lỗi thật",
        401: "khoá CONSENSUS_API_KEY thiếu/sai/đã thu hồi",
        402: "tài khoản Consensus quá hạn thanh toán",
        403: "tính năng không thuộc gói hiện tại (feature_not_allowed)",
        422: "tham số không hợp lệ với API",
        429: "vượt tốc độ (1 yêu cầu/giây) hoặc HẾT HẠN MỨC THÁNG của Consensus (dùng chung với MCP)",
    }.get(ma, "lỗi không rõ")
    return f"[consensus] HTTP {ma}: {y_nghia}."
