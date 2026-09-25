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
    trích `<a href>` trỏ tới file `.pdf`. Không tìm thấy link khớp mẫu kỳ vọng ⇒ trả
    `None` kèm cảnh báo rõ ràng, KHÔNG bịa kết quả.

LỖI ĐÃ VÁ 23/09/2026 (kiểm sống lần đầu, phát hiện ngay): mỗi năm trang mục lục liệt
kê HAI file .pdf liền nhau — báo cáo ĐẦY ĐỦ ("2025 Global Strategy for Prevention,
Diagnosis and Management...") RỒI MỚI tới "2025 GOLD Pocket Guide" (bản tóm tắt bỏ
túi, ngắn hơn nhiều). Bản vá đầu chỉ khớp link có chữ "GOLD" NGAY SAU thẻ `<a>` trong
văn bản hiển thị — nhưng chữ "GOLD" chỉ xuất hiện ở link Pocket Guide ("2025 GOLD
Pocket Guide"), KHÔNG xuất hiện ở link báo cáo đầy đủ ("2025 Global Strategy for...").
Kết quả: kiểm sống đầu tiên lấy NHẦM Pocket Guide (31.772 ký tự) thay vì báo cáo đầy
đủ. Đã sửa: lọc theo URL/văn bản CHỨA "pocket" (không phân biệt hoa/thường) để LOẠI
TRỪ, giữ lại link ĐẦU TIÊN còn lại — đúng thứ tự trang liệt kê (mới nhất lên đầu, báo
cáo đầy đủ luôn đứng trước pocket guide cùng năm, đã xác nhận cho mọi năm 2016-2025).
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

TRANG_MUC_LUC = "https://goldcopd.org/archived-reports/"
# Trang chủ liệt kê link tới trang báo cáo NĂM HIỆN HÀNH (vd `/2026-gold-report-and-pocket-guide/`).
# LỖI ĐÃ VÁ 24/09/2026 (đo sống): `archived-reports/` theo đúng nghĩa KHÔNG chứa báo cáo năm hiện
# hành ⇒ connector trả GOLD-2025 trong khi GOLD 2026 v1.3 (12/2025) đã phát hành. Nay đọc năm từ
# CHÍNH các link có trên trang chủ (không ghép URL theo công thức năm), chọn năm lớn nhất, lấy PDF
# báo cáo đầy đủ trên trang đó; không được thì lùi về `archived-reports/` như cũ.
TRANG_CHU = "https://goldcopd.org/"
_MAU_TRANG_BAO_CAO = re.compile(r'https://goldcopd\.org/(20\d\d)-gold-report[0-9a-z-]*/?', re.IGNORECASE)
# PDF không phải báo cáo đầy đủ: Pocket Guide và bản «tóm tắt thay đổi» (KEY-CHANGES).
_KHONG_PHAI_BAO_CAO = ("pocket", "key-changes", "summary of changes")
# Bắt CẢ href lẫn văn bản hiển thị của thẻ <a href="....pdf">...</a> — cần văn bản để
# lọc "pocket" (xem LỖI ĐÃ VÁ ở docstring module: chữ "GOLD" không đủ để phân biệt báo
# cáo đầy đủ với Pocket Guide, vì Pocket Guide MỚI là link có chữ "GOLD" trong text).
_MAU_LINK_PDF = re.compile(
    r'href="([^"]+\.pdf)"[^>]*>([^<]*)', re.IGNORECASE
)


class GoldCopdFullTextClient:
    """Tải TOÀN VĂN báo cáo GOLD mới nhất (hoặc theo URL đã biết) từ goldcopd.org.

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()` — cùng khuôn `WileyTdmClient`.
    Dùng khi một quy trình cần trích câu chữ cụ thể từ báo cáo GOLD, KHÔNG dùng để
    khám phá/tìm kiếm (việc đó vẫn do lane RSS `feeds.py::GUIDELINE_LANES` đảm nhiệm)."""

    name = "gold_copd_fulltext"

    def __init__(self) -> None:
        if not settings.enable_gold_copd_fulltext:
            raise ConnectorChuaBat(thong_diep_co_tat("gold_copd", "ENABLE_GOLD_COPD_FULLTEXT"))
        self.http = HttpClient()

    def tim_url_bao_cao_moi_nhat(self) -> Optional[str]:
        """Trích link PDF từ trang mục lục ổn định — KHÔNG đoán URL theo công thức năm
        (xem giới hạn ở docstring module). Trả `None` + log cảnh báo nếu không tìm
        thấy link nào khớp mẫu kỳ vọng, để người gọi biết cần xác nhận thủ công."""
        hien_hanh = self._tim_qua_trang_nam_hien_hanh()
        if hien_hanh:
            return hien_hanh
        try:
            html = self.http.get_text(TRANG_MUC_LUC)
        except Exception as exc:  # noqa: BLE001 — lỗi mạng, KHÔNG bịa URL
            logger.warning("[gold_copd] không tải được trang mục lục %s: %s", TRANG_MUC_LUC, exc)
            return None

        links = self._trich_link_pdf(html)
        if not links:
            logger.warning(
                "[gold_copd] không tìm thấy link PDF báo cáo đầy đủ (đã loại Pocket Guide) "
                "trong %s — có thể GOLD đã đổi cấu trúc trang, CẦN XÁC NHẬN THỦ CÔNG.",
                TRANG_MUC_LUC,
            )
            return None
        # Trang archived-reports liệt kê nhiều năm — link đầu tiên xuất hiện trong HTML
        # là năm MỚI NHẤT theo cách GOLD luôn trình bày (mới nhất lên đầu, đã xác nhận
        # khi khảo sát). Không sắp xếp lại theo "đoán" số năm trong URL.
        return links[0]

    def _tim_qua_trang_nam_hien_hanh(self) -> Optional[str]:
        """Trang chủ → trang báo cáo có NĂM LỚN NHẤT trong các link đang hiển thị → PDF đầy đủ.
        Mọi lỗi/không khớp ⇒ `None` để người gọi lùi về `archived-reports/`."""
        try:
            trang_chu = self.http.get_text(TRANG_CHU)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gold_copd] không tải được trang chủ %s: %s", TRANG_CHU, exc)
            return None
        ung_vien = {}
        for m in _MAU_TRANG_BAO_CAO.finditer(trang_chu):
            ung_vien.setdefault(int(m.group(1)), m.group(0))
        if not ung_vien:
            return None
        trang = ung_vien[max(ung_vien)]
        try:
            html = self.http.get_text(trang)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[gold_copd] không tải được trang báo cáo %s: %s", trang, exc)
            return None
        links = self._trich_link_pdf(html)
        return links[0] if links else None

    @staticmethod
    def _trich_link_pdf(html: str) -> List[str]:
        """Trả danh sách URL PDF theo thứ tự xuất hiện, ĐÃ LOẠI Pocket Guide (URL hoặc
        văn bản hiển thị chứa "pocket", không phân biệt hoa/thường) — xem LỖI ĐÃ VÁ ở
        docstring module. Không suy đoán/sắp xếp lại thứ tự trang liệt kê."""
        cap = _MAU_LINK_PDF.findall(html)
        da_thay: List[str] = []
        for url, text in cap:
            nhan = (url + " " + text).lower()
            if any(t in nhan for t in _KHONG_PHAI_BAO_CAO):
                continue
            if url not in da_thay:
                da_thay.append(url)
        return da_thay

    def tai_toan_van_pdf(self, url: Optional[str] = None,
                         gioi_han_ky_tu: Optional[int] = GIOI_HAN_KY_TU_MAC_DINH) -> KetQuaToanVanGuideline:
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

        thong_tin: dict = {}
        van_ban = trich_van_ban_tu_pdf(pdf_bytes, gioi_han_ky_tu=gioi_han_ky_tu, thong_tin=thong_tin)
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
            bi_cat=bool(thong_tin.get("bi_cat")), so_trang_pdf=thong_tin.get("so_trang_pdf"),
            moc_trang=list(thong_tin.get("moc_trang") or []), sha256_nguon=sha256_hex(pdf_bytes),
            ghi_chu=(f"Văn bản ĐÃ BỊ CẮT ở {gioi_han_ky_tu} ký tự — phần sau của tài liệu KHÔNG có trong "
                     "kết quả; muốn đọc/tìm toàn bộ thì truyền gioi_han_ky_tu=None."
                     if thong_tin.get("bi_cat") else None),
        )
