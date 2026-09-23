"""Connector TẢI TOÀN VĂN hướng dẫn BTS (British Thoracic Society) trực tiếp từ
brit-thoracic.org.uk — thêm 23/09/2026 theo yêu cầu bác sĩ.

Đã khảo sát TRƯỚC khi viết module này:
  • robots.txt cho phép mọi bot ở `/clinical-resources/guidelines/` và
    `/document-library/guidelines/` (chỉ chặn /auth, /umbraco*, /login/, /search/...).
  • Đã tải THÀNH CÔNG một PDF thật (BTS Guideline for Pleural Disease, 3,4 MB) trực
    tiếp từ `/document-library/guidelines/...` — không đăng nhập, không paywall.
  • Điều khoản sử dụng cấm "reproduce, copy, create derivative work" ngoài mục đích
    "personal non-commercial use" khi chưa có thoả thuận bằng văn bản với BTS.

⚠️ KHÁC HẲN `gold_copd.py`/`gina_asthma.py`: BTS KHÔNG có một trang mục lục ổn định
duy nhất liệt kê "bản mới nhất" theo chủ đề (mỗi bệnh có slug URL riêng, không đổi
theo năm cập nhật). Vì vậy module này KHÔNG có `tim_url_bao_cao_moi_nhat()` tự động —
chỉ cung cấp `tai_toan_van(url)` theo URL ĐÃ BIẾT (do agent/quy trình khác tra ra qua
tìm kiếm/PubMed trước). Đây là phạm vi ĐÃ KIỂM CHỨNG THẬT, không mở rộng suy đoán.

⚠️ MỘT SỐ HƯỚNG DẪN BTS ĐỒNG XUẤT BẢN với NICE/SIGN và KHÔNG tự lưu PDF trên chính
brit-thoracic.org.uk (ví dụ hướng dẫn Hen mới nhất, 11/2024, trỏ sang nice.org.uk) —
với các URL đó, `tai_toan_van()` sẽ nhận diện domain KHÁC brit-thoracic.org.uk và từ
chối tải (chưa khảo sát robots.txt/ToU của NICE/SIGN cho việc này), báo rõ lý do thay
vì âm thầm thử tải từ một domain chưa được xác nhận an toàn.
"""
from __future__ import annotations

from urllib.parse import urlparse

from app.config import settings
from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    KetQuaToanVanGuideline,
    trich_van_ban_tu_pdf,
)
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_DOMAIN_DA_KHAO_SAT = "brit-thoracic.org.uk"


class BtsGuidelineFullTextClient:
    """Tải TOÀN VĂN một hướng dẫn BTS theo URL PDF ĐÃ BIẾT trên brit-thoracic.org.uk.

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()`, KHÔNG tự dò "bản mới nhất"
    (xem giới hạn ở docstring module) — cùng khuôn `WileyTdmClient`."""

    name = "bts_guidelines_fulltext"

    def __init__(self) -> None:
        if not settings.enable_bts_guidelines_fulltext:
            raise RuntimeError(
                "[bts_guidelines] ENABLE_BTS_GUIDELINES_FULLTEXT chưa bật — đặt true "
                "trong ~/.ebm-secrets/medical-ebm-automation.env để dùng connector này."
            )
        self.http = HttpClient()

    def tai_toan_van(self, url: str) -> KetQuaToanVanGuideline:
        """Tải + trích văn bản từ một URL PDF BTS đã biết. Từ chối NGAY (không gọi
        mạng) nếu domain khác `brit-thoracic.org.uk` — một số hướng dẫn BTS đồng xuất
        bản trỏ sang nice.org.uk/rightdecisions.scot.nhs.uk, những domain đó CHƯA
        được khảo sát robots.txt/điều khoản riêng."""
        domain = urlparse(url).netloc.lower()
        if not domain.endswith(_DOMAIN_DA_KHAO_SAT):
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False,
                ghi_chu=(
                    f"URL thuộc domain '{domain}', KHÁC '{_DOMAIN_DA_KHAO_SAT}' đã khảo "
                    "sát robots.txt/điều khoản — có thể đây là hướng dẫn BTS đồng xuất "
                    "bản với NICE/SIGN, toàn văn nằm ở domain của họ. Connector này CHƯA "
                    "khảo sát domain đó, từ chối tải để không vi phạm kỷ luật "
                    "'không crawl khi chưa kiểm robots.txt/ToU trước'."
                ),
            )

        try:
            pdf_bytes = self.http.get_bytes(url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[bts_guidelines] tải PDF thất bại url=%s: %s", url, exc)
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False, ghi_chu=str(exc),
            )

        if not pdf_bytes.startswith(b"%PDF"):
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False,
                ghi_chu="Phản hồi không phải file PDF thật (thiếu chữ ký %PDF) — URL có "
                        "thể đã hết hạn hoặc trỏ sai, cần xác nhận thủ công.",
            )

        van_ban = trich_van_ban_tu_pdf(pdf_bytes)
        if not van_ban:
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False,
                ghi_chu="Tải được PDF thật nhưng không trích được văn bản (có thể là bản "
                        "scan dạng ảnh không có lớp văn bản).",
            )
        return KetQuaToanVanGuideline(
            to_chuc="BTS", url_nguon=url, thanh_cong=True,
            van_ban_trich=van_ban, so_trang_hoac_ky_tu=len(van_ban),
            ghi_chu_ban_quyen=GHI_CHU_BAN_QUYEN_CHUAN,
        )
