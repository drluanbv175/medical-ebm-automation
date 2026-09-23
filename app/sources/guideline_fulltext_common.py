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

from dataclasses import dataclass
from typing import Optional

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


def trich_van_ban_tu_pdf(pdf_bytes: bytes, gioi_han_ky_tu: int = 200_000) -> str:
    """Trích văn bản thô từ PDF bằng `pypdf`. Trả chuỗi rỗng (KHÔNG raise) nếu PDF hỏng/
    được scan dạng ảnh không có lớp văn bản — người gọi tự quyết định coi đó là thất bại
    hay không, module này chỉ báo trung thực CÓ trích được chữ hay không.

    `gioi_han_ky_tu`: cắt bớt nếu quá dài (báo cáo GOLD/GINA có thể vài trăm trang) — đủ
    cho việc trích dẫn câu chữ cụ thể, không nhằm lưu nguyên văn toàn bộ tài liệu.
    """
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
        phan: list[str] = []
        tong_do_dai = 0
        for trang in reader.pages:
            chu = trang.extract_text() or ""
            if not chu:
                continue
            phan.append(chu)
            tong_do_dai += len(chu)
            if tong_do_dai >= gioi_han_ky_tu:
                break
        return "\n".join(phan)[:gioi_han_ky_tu]
    except Exception as exc:  # PDF hỏng/không đọc được — không phải lỗi lập trình
        logger.warning("[guideline_fulltext_common] không trích được văn bản PDF: %s", exc)
        return ""
