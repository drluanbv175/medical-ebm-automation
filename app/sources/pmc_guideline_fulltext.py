"""Connector TẢI TOÀN VĂN guideline đã lưu trữ trên PubMed Central (PMC) — thêm
23/09/2026, ban đầu cho ADA "Standards of Care in Diabetes" (professional.diabetes.org/
diabetesjournals.org KHÔNG đọc được robots.txt — mọi lần fetch đều 403/lỗi DNS, nên
KHÔNG được coi là "cho phép ngầm"), nhưng viết GENERIC theo PMCID nên dùng lại được
cho BẤT KỲ hội chuyên khoa nào khác có nộp lưu guideline lên PMC (nhiều hội nhận tài
trợ liên quan NIH có nghĩa vụ nộp lưu; hội châu Âu như ESC thì chưa chắc — phải tra
riêng, không suy đoán).

Đã khảo sát TRƯỚC khi viết module này:
  • `pmc.ncbi.nlm.nih.gov/robots.txt` đọc trực tiếp 23/09/2026: kiểu ALLOWLIST, có dòng
    `Allow: /articles/` tường minh (đúng đường dẫn toàn văn cần dùng), `Crawl-delay: 1`,
    `Disallow: /` cho mọi thứ KHÔNG nằm trong danh sách Allow.
  • Đã tự tay đọc PMC12690171 (chương "Standards of Care in Diabetes—2026"), xác nhận
    toàn văn đầy đủ, miễn phí, license CC BY-NC-ND ("Readers may use this work for
    educational, noncommercial purposes if properly cited and unaltered").

CC BY-NC-ND cấm tạo bản phái sinh/đăng lại nguyên văn — xem `GHI_CHU_BAN_QUYEN_CHUAN`.
KHÔNG tự tìm PMCID (đó là việc của `app/sources/pubmed.py`/Europe PMC hiện có) — class
này CHỈ nhận PMCID đã biết và tải/trích văn bản, đúng khuôn (B) `WileyTdmClient`.
"""
from __future__ import annotations

import re

from app.config import settings
from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    KetQuaToanVanGuideline,
    trich_van_ban_tu_pdf,
)
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Crawl-delay: 1 trong robots.txt của pmc.ncbi.nlm.nih.gov.
_KHOANG_CACH_TOI_THIEU_GIAY = 1.0
_MAU_PMCID = re.compile(r"^PMC\d+$", re.IGNORECASE)
# Trang bài PMC có link "Download PDF" dạng /articles/PMC{id}/pdf/... — trích bằng regex
# đơn giản trên HTML, không cần BeautifulSoup cho một mẫu cố định thế này.
_MAU_LINK_PDF = re.compile(r'href="(/articles/PMC\d+/pdf/[^"]+\.pdf)"', re.IGNORECASE)


class PmcGuidelineFullTextClient:
    """Tải TOÀN VĂN một bài/chương guideline đã lưu trên PMC, theo PMCID đã biết.

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()` — cùng khuôn `WileyTdmClient`.
    Dùng khi đã có PMCID (từ `app/sources/pubmed.py`/Europe PMC) và cần trích toàn văn
    để lấy câu chữ khuyến cáo cụ thể, không dùng để khám phá/tìm kiếm."""

    name = "pmc_guideline_fulltext"

    def __init__(self) -> None:
        if not settings.enable_pmc_guideline_fulltext:
            raise RuntimeError(
                "[pmc_guideline_fulltext] ENABLE_PMC_GUIDELINE_FULLTEXT chưa bật — đặt "
                "true trong ~/.ebm-secrets/medical-ebm-automation.env để dùng connector này."
            )
        # min_interval=1.0: đúng Crawl-delay: 1 mà robots.txt của pmc.ncbi.nlm.nih.gov đòi.
        self.http = HttpClient(min_interval=_KHOANG_CACH_TOI_THIEU_GIAY)

    def tai_toan_van(self, pmcid: str) -> KetQuaToanVanGuideline:
        """Tải + trích văn bản từ một bài PMC theo PMCID (định dạng "PMC1234567",
        có hoặc không tiền tố PMC đều được chuẩn hoá). Không bịa PMCID — người gọi
        phải tự tra qua PubMed/Europe PMC trước."""
        pmcid_chuan = pmcid.strip().upper()
        if not pmcid_chuan.startswith("PMC"):
            pmcid_chuan = f"PMC{pmcid_chuan}"
        if not _MAU_PMCID.match(pmcid_chuan):
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=pmcid, thanh_cong=False,
                ghi_chu=f"'{pmcid}' không đúng định dạng PMCID (kỳ vọng 'PMC' + số).",
            )

        url_trang = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid_chuan}/"
        try:
            html = self.http.get_text(url_trang)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[pmc_guideline_fulltext] không mở được trang %s: %s", url_trang, exc)
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_trang, thanh_cong=False, ghi_chu=str(exc),
            )

        khop_pdf = _MAU_LINK_PDF.search(html)
        if not khop_pdf:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_trang, thanh_cong=False,
                ghi_chu="Không tìm thấy link 'Download PDF' trên trang — bài có thể không "
                        "có bản PDF (chỉ có HTML), PMCID sai, hoặc PMC đã đổi cấu trúc "
                        "trang. Cần xác nhận thủ công.",
            )
        url_pdf = "https://pmc.ncbi.nlm.nih.gov" + khop_pdf.group(1)

        try:
            pdf_bytes = self.http.get_bytes(url_pdf)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[pmc_guideline_fulltext] tải PDF thất bại url=%s: %s", url_pdf, exc)
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_pdf, thanh_cong=False, ghi_chu=str(exc),
            )

        van_ban = trich_van_ban_tu_pdf(pdf_bytes)
        if not van_ban:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_pdf, thanh_cong=False,
                ghi_chu="Tải được PDF nhưng không trích được văn bản.",
            )
        return KetQuaToanVanGuideline(
            to_chuc="PMC", url_nguon=url_pdf, thanh_cong=True,
            van_ban_trich=van_ban, so_trang_hoac_ky_tu=len(van_ban),
            ghi_chu_ban_quyen=GHI_CHU_BAN_QUYEN_CHUAN,
        )
