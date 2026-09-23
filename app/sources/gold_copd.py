"""Connector TẢI TOÀN VĂN báo cáo GOLD (Global Initiative for Chronic Obstructive
Lung Disease) trực tiếp từ goldcopd.org — thêm 23/09/2026 theo yêu cầu bác sĩ.

Đã khảo sát TRƯỚC khi viết module này (không suy đoán):
  • robots.txt (`https://goldcopd.org/robots.txt`) chỉ có khối Yoast SEO mặc định,
    `Disallow:` để TRỐNG — không chặn bất kỳ đường dẫn nào, kể cả /wp-content/uploads/.
  • Báo cáo GOLD mới nhất là một file PDF tải được TRỰC TIẾP, KHÔNG cần đăng nhập/
    đăng ký/trả phí (đã kiểm bằng WebFetch trang landing thật).
  • Trang "Legal Policy" (goldcopd.org/legal-policy/) cấm sao chép/phân phối lại nội
    dung khi chưa có phép bằng văn bản của GOLD, chỉ cho phép tải MỘT bản cho mục đích
    giáo dục cá nhân — xem `GHI_CHU_BAN_QUYEN_CHUAN` ở `guideline_fulltext_common.py`.

GIỚI HẠN QUAN TRỌNG NHẤT, đã đo bằng dữ liệu thật (KHÔNG phải suy đoán):
  • Tên slug trang landing ĐỔI GIỮA CÁC NĂM — không phải luôn "{năm}-gold-report/"
    (2024="2024-gold-report/", 2026="2026-gold-report-and-pocket-guide/"). Vì vậy
    KHÔNG được ghép URL landing theo công thức năm.
  • Tên file PDF cũng KHÔNG cố định — chứa số phiên bản (v1.0, v1.2, v1.3...) và ngày
    chỉnh sửa nguyên văn, đổi mỗi khi GOLD phát hành bản vá trong năm.
  • Vì hai điểm trên, việc "tìm URL báo cáo mới nhất" PHẢI đi qua trang mục lục ổn định
    `https://goldcopd.org/archived-reports/` (luôn tồn tại, liệt kê link mọi năm) rồi
    trích `<a href>` trỏ tới file `.pdf` có "GOLD" trong tên — KHÔNG BAO GIỜ đoán/ghép
    URL theo công thức. Không tìm thấy link khớp mẫu kỳ vọng ⇒ trả `None` kèm cảnh báo
    rõ ràng, KHÔNG bịa kết quả.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.config import settings
from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    KetQuaToanVanGuideline,
    trich_van_ban_tu_pdf,
)
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

TRANG_MUC_LUC = "https://goldcopd.org/archived-reports/"
# Bắt <a href="....pdf"> có "GOLD" (không phân biệt hoa/thường) trong đường dẫn — đúng
# quy ước đặt tên đã quan sát được (GOLD-REPORT-2026-..., GOLD-2024_v1.2-...).
_MAU_LINK_PDF = re.compile(
    r'href="([^"]+\.pdf)"[^>]*>[^<]*GOLD', re.IGNORECASE
)
_MAU_LINK_PDF_DU_PHONG = re.compile(
    r'href="([^"]*GOLD[^"]*\.pdf)"', re.IGNORECASE
)


class GoldCopdFullTextClient:
    """Tải TOÀN VĂN báo cáo GOLD mới nhất (hoặc theo URL đã biết) từ goldcopd.org.

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()` — cùng khuôn `WileyTdmClient`.
    Dùng khi một quy trình cần trích câu chữ cụ thể từ báo cáo GOLD, KHÔNG dùng để
    khám phá/tìm kiếm (việc đó vẫn do lane RSS `feeds.py::GUIDELINE_LANES` đảm nhiệm)."""

    name = "gold_copd_fulltext"

    def __init__(self) -> None:
        if not settings.enable_gold_copd_fulltext:
            raise RuntimeError(
                "[gold_copd] ENABLE_GOLD_COPD_FULLTEXT chưa bật — đặt true trong "
                "~/.ebm-secrets/medical-ebm-automation.env để dùng connector này."
            )
        self.http = HttpClient()

    def tim_url_bao_cao_moi_nhat(self) -> Optional[str]:
        """Trích link PDF từ trang mục lục ổn định — KHÔNG đoán URL theo công thức năm
        (xem giới hạn ở docstring module). Trả `None` + log cảnh báo nếu không tìm
        thấy link nào khớp mẫu kỳ vọng, để người gọi biết cần xác nhận thủ công."""
        try:
            html = self.http.get_text(TRANG_MUC_LUC)
        except Exception as exc:  # noqa: BLE001 — lỗi mạng, KHÔNG bịa URL
            logger.warning("[gold_copd] không tải được trang mục lục %s: %s", TRANG_MUC_LUC, exc)
            return None

        links = self._trich_link_pdf(html)
        if not links:
            logger.warning(
                "[gold_copd] không tìm thấy link PDF nào khớp mẫu 'GOLD...*.pdf' trong %s — "
                "có thể GOLD đã đổi cấu trúc trang, CẦN XÁC NHẬN THỦ CÔNG.", TRANG_MUC_LUC,
            )
            return None
        # Trang archived-reports liệt kê nhiều năm — link đầu tiên xuất hiện trong HTML
        # là năm MỚI NHẤT theo cách GOLD luôn trình bày (mới nhất lên đầu, đã xác nhận
        # khi khảo sát). Không sắp xếp lại theo "đoán" số năm trong URL.
        return links[0]

    @staticmethod
    def _trich_link_pdf(html: str) -> List[str]:
        tim_thay = _MAU_LINK_PDF.findall(html) or _MAU_LINK_PDF_DU_PHONG.findall(html)
        # Loại trùng lặp, giữ thứ tự xuất hiện.
        da_thay: List[str] = []
        for link in tim_thay:
            if link not in da_thay:
                da_thay.append(link)
        return da_thay

    def tai_toan_van_pdf(self, url: Optional[str] = None) -> KetQuaToanVanGuideline:
        """Tải + trích văn bản từ báo cáo GOLD. `url=None` ⇒ tự tìm bản mới nhất qua
        `tim_url_bao_cao_moi_nhat()`. KHÔNG bịa kết quả khi lỗi — `thanh_cong=False`
        kèm `ghi_chu` giải thích rõ, không quy hết về một thông điệp chung chung."""
        if url is None:
            url = self.tim_url_bao_cao_moi_nhat()
            if url is None:
                return KetQuaToanVanGuideline(
                    to_chuc="GOLD", url_nguon=TRANG_MUC_LUC, thanh_cong=False,
                    ghi_chu="Không tìm thấy link PDF báo cáo mới nhất trên trang mục lục — "
                            "cấu trúc trang có thể đã đổi, cần xác nhận thủ công.",
                )

        try:
            pdf_bytes = self.http.get_bytes(url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gold_copd] tải PDF thất bại url=%s: %s", url, exc)
            return KetQuaToanVanGuideline(
                to_chuc="GOLD", url_nguon=url, thanh_cong=False, ghi_chu=str(exc),
            )

        van_ban = trich_van_ban_tu_pdf(pdf_bytes)
        if not van_ban:
            return KetQuaToanVanGuideline(
                to_chuc="GOLD", url_nguon=url, thanh_cong=False,
                ghi_chu="Tải được file nhưng không trích được văn bản (không phải PDF hợp "
                        "lệ, hoặc PDF dạng ảnh scan không có lớp văn bản, hoặc GOLD đã đổi "
                        "chính sách truy cập và trả về trang HTML thay vì PDF thật).",
            )
        return KetQuaToanVanGuideline(
            to_chuc="GOLD", url_nguon=url, thanh_cong=True,
            van_ban_trich=van_ban, so_trang_hoac_ky_tu=len(van_ban),
            ghi_chu_ban_quyen=GHI_CHU_BAN_QUYEN_CHUAN,
        )
