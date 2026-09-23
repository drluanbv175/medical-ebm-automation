"""Kết nối Wiley Text and Data Mining (TDM) API — thêm 23/09/2026 theo yêu cầu bác sĩ,
sau khi đã có TDM API token thật từ tài khoản Wiley Online Library (WOL) của bác sĩ.

KHÁC HOÀN TOÀN mọi connector khác trong app/sources/: đây KHÔNG phải nguồn TÌM KIẾM/
KHÁM PHÁ (không có `SourceClient.search()`) — TDM API chỉ TẢI TOÀN VĂN PDF theo DOI ĐÃ
BIẾT trước. Vì vậy `WileyTdmClient` KHÔNG kế thừa `SourceClient`, KHÔNG có trong
`get_enabled_sources()`/`get_fallback_sources()`, và KHÔNG tham gia bất kỳ vòng quét
song song nào (`ingest_all`, `research/manager.py`, `research/dossier.py`). Dùng khi một
agent/quy trình ĐÃ CÓ DOI (từ PubMed/Crossref/Scopus/Europe PMC…) và cần lấy toàn văn
của một bài xuất bản trên nền tảng Wiley Online Library — ví dụ để trích xuất dữ liệu
chi tiết ngoài phạm vi abstract cho tổng quan hệ thống.

Thư viện nền: gói PyPI chính thức `wiley-tdm` (import `wiley_tdm`), mã nguồn
`github.com/WileyLabs/tdm-client` — bọc lại ở đây theo đúng khuôn NẠP CHỊU LỖI của gói
này (xem `app/sources/__init__.py::_nap_client`): thiếu thư viện thì VẮNG MẶT CÓ KHAI
BÁO ở nơi gọi, không kéo sập cả gói `app.sources`.

Đây KHÔNG phải MCP connector `plugin:bio-research:wiley` (claude.ai connector, cần bác
sĩ tự cấp quyền OAuth qua giao diện claude.ai) — hai thứ hoàn toàn tách biệt, ghi ở
`data/sources.json` với hai mã SRC khác nhau.

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không ai hiểu nhầm mức độ phủ:
  • ⚠️ QUAN TRỌNG NHẤT — "Access is IP address based only" (README chính thức của
    WileyLabs/tdm-client, mục Known Limitations): dù token hợp lệ, IP gọi request PHẢI
    nằm trong dải IP mà tài khoản WOL của bác sĩ được cấp quyền truy cập (thường là
    mạng của bệnh viện/tổ chức đã mua gói Wiley Online Library). Gọi từ mạng nhà/VPN/
    máy ngoài dải đó → `DownloadStatus.ACCESS_DENIED` cho các bài KHÔNG PHẢI Open
    Access, dù token đúng. CHỈ bài Open Access chắc chắn tải được từ mọi IP.
    **CHƯA được xác nhận chạy thật** với dải IP của bác sĩ lúc viết module này — phải
    tự kiểm bằng `python run.py wiley-tdm-test <DOI Open Access>` rồi một DOI KHÔNG Open
    Access để biết đúng ranh giới thật của tài khoản, KHÔNG giả định nó "chắc chắn chạy".
  • Không phải nguồn tìm kiếm — không có DOI thì không tải được gì (khác PubMed/
    Crossref/Scopus có thể tìm THEO từ khoá).
  • Trần nhịp gọi do Wiley công bố: ~3 bài/giây, 60 request/10 phút; thư viện mặc định
    nghỉ 5 giây giữa các lượt tải hàng loạt (`api_rate_limit`), README khuyến nghị
    10 giây cho việc dùng LIÊN TỤC — cấu hình qua `WILEY_TDM_RATE_LIMIT_SECONDS`.
  • KHÔNG tham gia chuỗi 3 tầng kiểm rút bài (`retraction_chain.py`) — tải được PDF
    không xác nhận bài chưa bị rút; PHẢI kiểm rút bài qua kênh hiện có (PubMed/Europe
    PMC/Retraction Watch offline) TRƯỚC khi dùng nội dung PDF tải về cho việc gì.
  • Token là chuỗi UUID lấy từ trang "Text and Data Mining" trong tài khoản Wiley Online
    Library của bác sĩ — KHÔNG BAO GIỜ nhập/dán token qua Claude Code; xem hướng dẫn ở
    `.env.example`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_TRANG_THAI_THANH_CONG = {"SUCCESS", "EXISTING_FILE"}


@dataclass
class KetQuaTaiWiley:
    """Kết quả một lượt tải PDF qua Wiley TDM — Việt hoá lại `DownloadResult`/
    `DownloadStatus` của thư viện gốc để phần còn lại của hệ thống không phải import
    `wiley_tdm` trực tiếp (thư viện đổi kiểu dữ liệu thì chỉ sửa ở `_quy_doi_ket_qua`)."""

    doi: str
    trang_thai: str  # tên gốc của DownloadStatus: SUCCESS, ACCESS_DENIED, UNKNOWN_DOI,
    # KNOWN_ISSUE, API_ERROR, EXISTING_FILE, STORAGE_ERROR, INVALID_DOI, NETWORK_ERROR
    thanh_cong: bool
    duong_dan: Optional[str] = None
    kich_thuoc_byte: Optional[int] = None
    ghi_chu: Optional[str] = None
    ma_http: Optional[int] = None


def _quy_doi_ket_qua(ket_qua) -> KetQuaTaiWiley:
    ten_trang_thai = ket_qua.status.name
    return KetQuaTaiWiley(
        doi=ket_qua.doi,
        trang_thai=ten_trang_thai,
        thanh_cong=ten_trang_thai in _TRANG_THAI_THANH_CONG,
        duong_dan=str(ket_qua.path) if ket_qua.path else None,
        kich_thuoc_byte=ket_qua.size,
        ghi_chu=ket_qua.comment or None,
        ma_http=int(ket_qua.api_status) if ket_qua.api_status else None,
    )


class WileyTdmClient:
    """Bọc `wiley_tdm.TDMClient` — tải TOÀN VĂN PDF theo DOI qua Wiley TDM API.

    KHÔNG kế thừa `SourceClient` (xem docstring module). Dùng trực tiếp::

        client = WileyTdmClient()
        kq = client.download_pdf("10.1002/xxxx")
        if kq.thanh_cong:
            ...  # kq.duong_dan là đường dẫn PDF trên đĩa
    """

    name = "wiley_tdm"

    def __init__(self, download_dir: Optional[str] = None) -> None:
        if not settings.enable_wiley_tdm:
            raise RuntimeError(
                "[wiley_tdm] ENABLE_WILEY_TDM chưa bật — đặt true trong "
                "~/.ebm-secrets/medical-ebm-automation.env sau khi đã có "
                "WILEY_TDM_API_TOKEN."
            )
        if not settings.wiley_tdm_api_token:
            # Chặn SỚM bằng tiếng Việt rõ ràng, thay vì để thư viện gốc ném ValueError
            # tiếng Anh mù mờ — cùng nguyên tắc đã áp cho Scopus/Epistemonikos/SerpApi.
            raise RuntimeError(
                "[wiley_tdm] ENABLE_WILEY_TDM=true nhưng thiếu WILEY_TDM_API_TOKEN — "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env rồi thử lại. Token "
                "lấy từ trang 'Text and Data Mining' trong tài khoản Wiley Online "
                "Library của bác sĩ."
            )
        try:
            from wiley_tdm import TDMClient  # nạp trễ, xem docstring module
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "[wiley_tdm] thiếu thư viện `wiley-tdm` — cài: "
                "~/.ebm-venv/bin/pip install wiley-tdm (macOS/Linux) hoặc "
                "%USERPROFILE%\\.ebm-venv\\Scripts\\pip.exe install wiley-tdm (Windows)."
            ) from exc

        thu_muc = download_dir or settings.wiley_tdm_download_dir or "downloads_wiley_tdm"
        self._client = TDMClient(api_token=settings.wiley_tdm_api_token, download_dir=thu_muc)
        self._client.api_rate_limit = settings.wiley_tdm_rate_limit_seconds
        # skip_existing_files=True là mặc định của thư viện — giữ nguyên để không tải
        # lại PDF đã có trên đĩa.

    def download_pdf(self, doi: str) -> KetQuaTaiWiley:
        """Tải MỘT bài theo DOI. Không bịa kết quả khi lỗi — trả nguyên trạng thái thật
        của Wiley (ACCESS_DENIED/UNKNOWN_DOI/NETWORK_ERROR/...), không quy hết về 'lỗi'
        chung chung để người gọi biết chính xác phải làm gì tiếp theo."""
        ket_qua = self._client.download_pdf(doi)
        out = _quy_doi_ket_qua(ket_qua)
        if not out.thanh_cong:
            logger.warning(
                "[wiley_tdm] tải thất bại doi=%s trạng_thái=%s ghi_chú=%s",
                doi, out.trang_thai, out.ghi_chu,
            )
        return out

    def download_pdfs(
        self,
        dois: List[str],
        on_result: Optional[Callable[[KetQuaTaiWiley], None]] = None,
    ) -> List[KetQuaTaiWiley]:
        """Tải HÀNG LOẠT theo danh sách DOI — thư viện tự giãn nhịp giữa các lượt
        (xem `api_rate_limit`). `on_result` (tuỳ chọn) được gọi sau MỖI lượt tải."""

        def _cb(ket_qua):
            if on_result:
                on_result(_quy_doi_ket_qua(ket_qua))

        ket_qua_tho = self._client.download_pdfs(dois, on_result=_cb if on_result else None)
        return [_quy_doi_ket_qua(k) for k in ket_qua_tho]

    @property
    def download_dir(self) -> Path:
        return self._client.download_dir
