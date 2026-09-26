"""Hạ tầng DÙNG CHUNG cho các connector TẢI TOÀN VĂN guideline trực tiếp từ website
chính thức của hiệp hội chuyên ngành (GOLD, GINA, BTS...) — thêm 23/09/2026 theo yêu
cầu bác sĩ, sau khảo sát robots.txt/điều khoản sử dụng của từng tổ chức (xem
`medical-ebm-automation/CLAUDE.md`, mục "Nguồn dữ liệu").

KHÁC HẲN mọi connector tìm kiếm (`SourceClient.search()`): đây là khuôn (B) "tải toàn
văn theo định danh đã biết" — cùng khuôn `app/sources/wiley_tdm.py::WileyTdmClient`.
Mỗi tổ chức có class riêng (`gold_copd.py`, `gina_asthma.py`, `bts_guidelines.py`) vì
cấu trúc trang mỗi nơi khác nhau, nhưng dùng chung 3 thứ ở đây: dataclass kết quả,
hàm trích văn bản từ PDF, và cảnh báo bản quyền chuẩn.

⚠️ RANH GIỚI BẢN QUYỀN — ÁP DỤNG CHO MỌI CONNECTOR DÙNG MODULE NÀY, KHÔNG NGOẠI LỆ:
Cả GOLD, GINA, BTS đều có điều khoản sử dụng CẤM sao chép/phân phối lại/đăng công khai
toàn văn báo cáo khi chưa có phép bằng văn bản (đã đọc trực tiếp, trích nguyên văn khi
khảo sát — xem lịch sử CLAUDE.md). PDF tải về ở đây CHỈ được dùng làm NGUỒN THAM CHIẾU
NỘI BỘ để trích câu chữ khuyến cáo cụ thể kèm PMID/DOI/URL gốc (đúng cách toàn bộ EBM
Copilot đang trích dẫn) — TUYỆT ĐỐI KHÔNG hiển thị nguyên văn PDF trên dashboard công
khai, KHÔNG đăng lại toàn văn, KHÔNG phân phối file cho bên thứ ba.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Nhắc bản quyền chuẩn, gắn vào MỌI kết quả tải thành công — để bất kỳ ai tiêu thụ
# `KetQuaToanVanGuideline.ghi_chu_ban_quyen` cũng thấy ranh giới, không chỉ người đọc
# docstring module này.
GHI_CHU_BAN_QUYEN_CHUAN = (
    "Chỉ dùng làm nguồn tham chiếu NỘI BỘ để trích câu chữ kèm nguồn gốc — "
    "KHÔNG đăng lại toàn văn công khai, KHÔNG phân phối lại file. "
    "Cần bác sĩ kiểm chứng."
)


# Mặc định cũ của trich_van_ban_tu_pdf() — GIỮ NGUYÊN cho mọi nơi gọi không truyền gì. Muốn tìm trong
# TOÀN BỘ báo cáo (GOLD/GINA vài trăm trang, đo 24/09/2026 đều chạm trần 200.000 ký tự) thì truyền
# gioi_han_ky_tu=None — xem tools/toan_van_guideline.py.
GIOI_HAN_KY_TU_MAC_DINH = 200_000


class ConnectorChuaBat(RuntimeError):
    """Cờ ENABLE_* của connector toàn văn đang tắt. Là RuntimeError (giữ tương thích nơi bắt cũ)
    nhưng tách lớp riêng để công cụ gọi phân biệt «chưa bật» với lỗi khác mà không cần đọc chuỗi."""


def la_phien_cloud() -> bool:
    """Phiên Claude Code trên Cloud (claude.ai/code) — biến CLAUDE_CODE_REMOTE=true do môi trường đặt."""
    return os.environ.get("CLAUDE_CODE_REMOTE", "").strip().lower() == "true"


def thong_diep_co_tat(tien_to: str, ten_bien: str) -> str:
    """Thông điệp khi cờ bật connector đang tắt — ĐÚNG NƠI bác sĩ phải bật theo môi trường.

    Trên Cloud không có ~/.ebm-secrets/medical-ebm-automation.env (container dựng mới mỗi phiên) nên
    chỉ dẫn cũ sai chỗ: phải thêm biến môi trường ở cài đặt môi trường Cloud rồi mở phiên MỚI (biến
    chỉ nạp khi container khởi động). Mac/Windows giữ nguyên thông điệp cũ.
    """
    if la_phien_cloud():
        return (
            f"[{tien_to}] {ten_bien} chưa bật — phiên Cloud KHÔNG có ~/.ebm-secrets/: thêm biến môi trường "
            f"{ten_bien}=true ở cài đặt môi trường Cloud (Environment variables) rồi mở PHIÊN MỚI "
            "(biến chỉ nạp khi container khởi động). Bật là quyết định của bác sĩ."
        )
    return (
        f"[{tien_to}] {ten_bien} chưa bật — đặt true trong "
        "~/.ebm-secrets/medical-ebm-automation.env để dùng connector này."
    )


def sha256_hex(du_lieu: bytes) -> str:
    return hashlib.sha256(du_lieu).hexdigest()


@dataclass
class KetQuaToanVanGuideline:
    """Kết quả một lượt tải toàn văn guideline — dataclass Việt hoá dùng chung cho
    GOLD/GINA/BTS/PMC, theo đúng khuôn `wiley_tdm.KetQuaTaiWiley` (cô lập chi tiết kỹ
    thuật của từng nguồn khỏi phần còn lại của hệ thống)."""

    to_chuc: str  # "GOLD" | "GINA" | "BTS" | "ADA (qua PMC)" ...
    url_nguon: str
    thanh_cong: bool
    van_ban_trich: Optional[str] = None  # văn bản trích từ PDF/HTML, None nếu thất bại
    so_trang_hoac_ky_tu: Optional[int] = None
    ghi_chu: Optional[str] = None
    ghi_chu_ban_quyen: str = GHI_CHU_BAN_QUYEN_CHUAN
    ma_http: Optional[int] = None
    # Thêm 24/09/2026 — để nơi dùng biết văn bản có ĐỦ không và trích từ đâu (không đoán):
    bi_cat: bool = False  # True ⇒ văn bản đã bị cắt ở gioi_han_ky_tu, phần sau KHÔNG có trong van_ban_trich
    so_trang_pdf: Optional[int] = None  # tổng số trang của PDF (None với nguồn văn bản như PMC)
    # [(số trang 1-based, vị trí ký tự bắt đầu trong van_ban_trich)] — chỉ các trang có chữ, để định vị trang.
    moc_trang: List[Tuple[int, int]] = field(default_factory=list)
    sha256_nguon: Optional[str] = None  # SHA-256 của tệp đã tải (PDF/.txt) — truy vết đúng bản đã đọc


def trich_van_ban_tu_pdf(
    pdf_bytes: bytes,
    gioi_han_ky_tu: Optional[int] = GIOI_HAN_KY_TU_MAC_DINH,
    thong_tin: Optional[Dict[str, Any]] = None,
) -> str:
    """Trích văn bản thô từ PDF bằng `pypdf`. Trả chuỗi rỗng (KHÔNG raise) nếu PDF hỏng/
    được scan dạng ảnh không có lớp văn bản — người gọi tự quyết định coi đó là thất bại
    hay không, module này chỉ báo trung thực CÓ trích được chữ hay không.

    `gioi_han_ky_tu`: cắt bớt nếu quá dài (báo cáo GOLD/GINA có thể vài trăm trang) — đủ
    cho việc trích dẫn câu chữ cụ thể, không nhằm lưu nguyên văn toàn bộ tài liệu.
    `None` ⇒ trích TOÀN BỘ (dùng khi cần tìm cụm từ ở phần sau của báo cáo).

    `thong_tin` (tuỳ chọn, thêm 24/09/2026): dict được ĐIỀN tại chỗ với `so_trang_pdf`, `bi_cat`
    (văn bản trả về có bị cắt không) và `moc_trang` [(trang 1-based, vị trí ký tự bắt đầu)] — để
    nơi gọi định vị trang và NÓI RÕ khi văn bản bị cắt. Đầu ra chuỗi KHÔNG đổi so với bản cũ.
    """
    if thong_tin is None:
        thong_tin = {}
    thong_tin.update(so_trang_pdf=None, bi_cat=False, moc_trang=[])
    try:
        from pypdf import PdfReader  # nạp trễ — thiếu thư viện không kéo sập app.sources
    except ModuleNotFoundError:
        logger.warning(
            "[guideline_fulltext_common] thiếu thư viện `pypdf` — cài: "
            "~/.ebm-venv/bin/pip install pypdf"
        )
        return ""

    import io

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        tong_trang = len(reader.pages)
        phan: list[str] = []
        moc: list[tuple[int, int]] = []
        vi_tri = 0
        tong_do_dai = 0
        dung_som = False
        for so, trang in enumerate(reader.pages, start=1):
            chu = trang.extract_text() or ""
            if not chu:
                continue
            moc.append((so, vi_tri))
            phan.append(chu)
            vi_tri += len(chu) + 1  # +1 cho "\n" nối giữa các trang
            tong_do_dai += len(chu)
            if gioi_han_ky_tu is not None and tong_do_dai >= gioi_han_ky_tu:
                dung_som = so < tong_trang
                break
        van_ban = "\n".join(phan)
        bi_cat = dung_som
        if gioi_han_ky_tu is not None and len(van_ban) > gioi_han_ky_tu:
            van_ban = van_ban[:gioi_han_ky_tu]
            bi_cat = True
        thong_tin.update(
            so_trang_pdf=tong_trang, bi_cat=bi_cat,
            moc_trang=[(so, vt) for so, vt in moc if vt < len(van_ban)],
        )
        return van_ban
    except Exception as exc:  # PDF hỏng/không đọc được — không phải lỗi lập trình
        logger.warning("[guideline_fulltext_common] không trích được văn bản PDF: %s", exc)
        return ""


def trang_cua_vi_tri(moc_trang: List[Tuple[int, int]], vi_tri: int) -> Optional[int]:
    """Số trang (1-based) chứa ký tự ở `vi_tri` của văn bản trích; None nếu không có mốc trang."""
    trang = None
    for so, bat_dau in moc_trang:
        if bat_dau > vi_tri:
            break
        trang = so
    return trang
