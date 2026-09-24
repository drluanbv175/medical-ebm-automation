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

LỖI ĐÃ VÁ 23/09/2026 (kiểm sống lần đầu, phát hiện ngay): `https://ginasthma.org/reports/`
KHÔNG còn link PDF trực tiếp nào — trang này chỉ liệt kê link tới các trang LANDING
riêng từng ấn phẩm (`https://ginasthma.org/2026-gina-strategy-report/`,
`.../2026-gina-summary-guide/`, `.../2026-gina-severe-asthma-guide/`...), và PDF thật
nằm Ở TRANG LANDING đó, không nằm ở trang liệt kê. Bản vá đầu chỉ dò `.pdf` trực tiếp
trên `/reports/` nên luôn trả `None`. Đã sửa thành HAI BƯỚC: (1) dò link landing khớp
mẫu `{năm}-gina-strategy-report/` trên `/reports/`; (2) dò `.pdf` trên đúng trang
landing đó bằng regex cũ (`_MAU_LINK_PDF`, vẫn khớp đúng — đã kiểm sống: file thật là
`GINA-2026-Strategy-Report-WMS.pdf`). Không tìm thấy link landing ⇒ `None` kèm cảnh
báo, KHÔNG bịa/đoán slug năm.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.config import settings
from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    GIOI_HAN_KY_TU_MAC_DINH,
    ConnectorChuaBat,
    KetQuaToanVanGuideline,
    sha256_hex,
    thong_diep_co_tat,
    trich_van_ban_tu_pdf,
)
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

TRANG_MUC_LUC = "https://ginasthma.org/reports/"
# Trang mục lục nay chỉ liệt kê link LANDING theo năm, KHÔNG có .pdf trực tiếp — dò
# link landing "{năm}-gina-strategy-report/" trước (bước 1), rồi mới dò .pdf trên
# đúng trang landing đó (bước 2, dùng lại _MAU_LINK_PDF ở dưới).
_MAU_LINK_LANDING = re.compile(
    r'href="(https://ginasthma\.org/\d{4}-gina-strategy-report/)"', re.IGNORECASE
)
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
            raise ConnectorChuaBat(thong_diep_co_tat("gina_asthma", "ENABLE_GINA_ASTHMA_FULLTEXT"))
        # min_interval=10.0: đúng Crawl-delay: 10 mà robots.txt của ginasthma.org đòi —
        # KHÔNG được đặt thấp hơn dù chỉ để "thử nhanh".
        self.http = HttpClient(min_interval=_KHOANG_CACH_TOI_THIEU_GIAY)

    def tim_url_bao_cao_moi_nhat(self) -> Optional[str]:
        """Hai bước (xem "LỖI ĐÃ VÁ 23/09/2026" ở docstring module): (1) tìm link trang
        landing mới nhất trên trang mục lục; (2) tìm link PDF thật trên trang landing đó."""
        try:
            html_muc_luc = self.http.get_text(TRANG_MUC_LUC)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gina_asthma] không tải được trang mục lục %s: %s", TRANG_MUC_LUC, exc)
            return None

        landing = _MAU_LINK_LANDING.findall(html_muc_luc)
        if not landing:
            logger.warning(
                "[gina_asthma] không tìm thấy link trang landing '{năm}-gina-strategy-report/' "
                "trong %s — có thể GINA đã đổi cấu trúc trang HOẶC đang tạm đóng truy cập miễn "
                "phí (đã xảy ra 07-11/2025) — CẦN XÁC NHẬN THỦ CÔNG.", TRANG_MUC_LUC,
            )
            return None
        url_landing = landing[0]

        try:
            html_landing = self.http.get_text(url_landing)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gina_asthma] không tải được trang landing %s: %s", url_landing, exc)
            return None

        links = self._trich_link_pdf(html_landing)
        if not links:
            logger.warning(
                "[gina_asthma] tìm thấy trang landing %s nhưng KHÔNG có link PDF "
                "'GINA...Strategy-Report...pdf' trên đó — cấu trúc trang có thể đã đổi, "
                "CẦN XÁC NHẬN THỦ CÔNG.", url_landing,
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

    def tai_toan_van_pdf(self, url: Optional[str] = None,
                         gioi_han_ky_tu: Optional[int] = GIOI_HAN_KY_TU_MAC_DINH) -> KetQuaToanVanGuideline:
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

        thong_tin: dict = {}
        van_ban = trich_van_ban_tu_pdf(pdf_bytes, gioi_han_ky_tu=gioi_han_ky_tu, thong_tin=thong_tin)
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
            bi_cat=bool(thong_tin.get("bi_cat")), so_trang_pdf=thong_tin.get("so_trang_pdf"),
            moc_trang=list(thong_tin.get("moc_trang") or []), sha256_nguon=sha256_hex(pdf_bytes),
            ghi_chu=(f"Văn bản ĐÃ BỊ CẮT ở {gioi_han_ky_tu} ký tự — phần sau của tài liệu KHÔNG có trong "
                     "kết quả; muốn đọc/tìm toàn bộ thì truyền gioi_han_ky_tu=None."
                     if thong_tin.get("bi_cat") else None),
        )
