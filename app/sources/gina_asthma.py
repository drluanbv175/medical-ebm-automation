"""Connector TẢI TOÀN VĂN báo cáo GINA (Global Initiative for Asthma) trực tiếp từ
ginasthma.org — thêm 23/09/2026 theo yêu cầu bác sĩ. Cùng khuôn `gold_copd.py`, chỉ
khác Ở HAI ĐIỂM bắt buộc dưới đây (KHÔNG được bỏ qua khi bảo trì):

  1) robots.txt (`https://ginasthma.org/robots.txt`) cho phép mọi bot NHƯNG đòi
     `Crawl-delay: 10` — connector này BẮT BUỘC giãn cách ≥10 giây giữa các request
     tới `ginasthma.org` (dùng `HttpClient(min_interval=10.0)`, không lách).
  2) GINA từng TẠM ĐÓNG truy cập miễn phí 07→11/2025 vì lý do tài chính (xác nhận qua
     tìm kiếm, không phải suy đoán) — chính sách có thể đổi bất kỳ lúc nào. Vì vậy
     phải PHÂN BIỆT "lỗi mạng tạm thời" với "phản hồi không phải PDF thật" (ví dụ
     content-type sai/HTML thay vì PDF) — trường hợp sau phải cảnh báo RÕ khác hẳn
     lỗi mạng, không được gộp chung.

Điều khoản sử dụng (`https://ginasthma.org/legal-policy/`) cấm sao chép/phân phối/
đăng lại nội dung khi chưa có phép — xem `GHI_CHU_BAN_QUYEN_CHUAN`. Muốn xin phép:
`https://ginasthma.org/copyright-requests/`.
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

TRANG_MUC_LUC = "https://ginasthma.org/reports/"
_MAU_LINK_PDF = re.compile(
    r'href="([^"]*GINA[^"]*Strategy-Report[^"]*\.pdf)"', re.IGNORECASE
)
_MAU_LINK_PDF_DU_PHONG = re.compile(
    r'href="([^"]*/wp-content/uploads/[^"]*GINA[^"]*\.pdf)"', re.IGNORECASE
)
# Crawl-delay: 10 trong robots.txt của ginasthma.org — BẮT BUỘC, không lách.
_KHOANG_CACH_TOI_THIEU_GIAY = 10.0


class GinaAsthmaFullTextClient:
    """Tải TOÀN VĂN báo cáo GINA mới nhất (hoặc theo URL đã biết) từ ginasthma.org.

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()` — cùng khuôn `WileyTdmClient`/
    `GoldCopdFullTextClient`."""

    name = "gina_asthma_fulltext"

    def __init__(self) -> None:
        if not settings.enable_gina_asthma_fulltext:
            raise RuntimeError(
                "[gina_asthma] ENABLE_GINA_ASTHMA_FULLTEXT chưa bật — đặt true trong "
                "~/.ebm-secrets/medical-ebm-automation.env để dùng connector này."
            )
        # min_interval=10.0: đúng Crawl-delay: 10 mà robots.txt của ginasthma.org đòi —
        # KHÔNG được đặt thấp hơn dù chỉ để "thử nhanh".
        self.http = HttpClient(min_interval=_KHOANG_CACH_TOI_THIEU_GIAY)

    def tim_url_bao_cao_moi_nhat(self) -> Optional[str]:
        try:
            html = self.http.get_text(TRANG_MUC_LUC)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gina_asthma] không tải được trang mục lục %s: %s", TRANG_MUC_LUC, exc)
            return None

        links = self._trich_link_pdf(html)
        if not links:
            logger.warning(
                "[gina_asthma] không tìm thấy link PDF 'GINA...Strategy-Report...pdf' trong "
                "%s — có thể GINA đã đổi cấu trúc trang HOẶC đang tạm đóng truy cập miễn phí "
                "(đã xảy ra 07-11/2025) — CẦN XÁC NHẬN THỦ CÔNG.", TRANG_MUC_LUC,
            )
            return None
        return links[0]

    @staticmethod
    def _trich_link_pdf(html: str) -> List[str]:
        tim_thay = _MAU_LINK_PDF.findall(html) or _MAU_LINK_PDF_DU_PHONG.findall(html)
        da_thay: List[str] = []
        for link in tim_thay:
            if link not in da_thay:
                da_thay.append(link)
        return da_thay

    def tai_toan_van_pdf(self, url: Optional[str] = None) -> KetQuaToanVanGuideline:
        if url is None:
            url = self.tim_url_bao_cao_moi_nhat()
            if url is None:
                return KetQuaToanVanGuideline(
                    to_chuc="GINA", url_nguon=TRANG_MUC_LUC, thanh_cong=False,
                    ghi_chu="Không tìm thấy link PDF báo cáo mới nhất — cấu trúc trang có "
                            "thể đã đổi, hoặc GINA đang tạm đóng truy cập miễn phí. Cần xác "
                            "nhận thủ công.",
                )

        try:
            pdf_bytes = self.http.get_bytes(url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gina_asthma] tải PDF thất bại url=%s: %s", url, exc)
            return KetQuaToanVanGuideline(
                to_chuc="GINA", url_nguon=url, thanh_cong=False, ghi_chu=str(exc),
            )

        # Phân biệt "tải được nhưng không phải PDF thật" (dấu hiệu đổi chính sách truy
        # cập, vd trả về trang HTML "please subscribe") với lỗi mạng ở trên — đúng yêu
        # cầu (2) trong docstring module.
        if not pdf_bytes.startswith(b"%PDF"):
            logger.warning(
                "[gina_asthma] phản hồi từ %s KHÔNG phải PDF thật (thiếu chữ ký %%PDF) — "
                "nghi GINA đã đổi chính sách truy cập, KHÔNG PHẢI lỗi mạng.", url,
            )
            return KetQuaToanVanGuideline(
                to_chuc="GINA", url_nguon=url, thanh_cong=False,
                ghi_chu="Phản hồi không phải file PDF thật (thiếu chữ ký %PDF ở đầu file) — "
                        "nghi GINA đã thay đổi chính sách truy cập (từng xảy ra 07-11/2025), "
                        "KHÔNG phải lỗi mạng tạm thời. Cần bác sĩ xác nhận trực tiếp trên "
                        "trình duyệt.",
            )

        van_ban = trich_van_ban_tu_pdf(pdf_bytes)
        if not van_ban:
            return KetQuaToanVanGuideline(
                to_chuc="GINA", url_nguon=url, thanh_cong=False,
                ghi_chu="Tải được PDF thật nhưng không trích được văn bản (có thể là bản "
                        "scan dạng ảnh không có lớp văn bản).",
            )
        return KetQuaToanVanGuideline(
            to_chuc="GINA", url_nguon=url, thanh_cong=True,
            van_ban_trich=van_ban, so_trang_hoac_ky_tu=len(van_ban),
            ghi_chu_ban_quyen=GHI_CHU_BAN_QUYEN_CHUAN,
        )
