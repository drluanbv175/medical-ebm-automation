"""Connector TẢI TOÀN VĂN hướng dẫn BTS (British Thoracic Society) trực tiếp từ
brit-thoracic.org.uk — thêm 23/09/2026 theo yêu cầu bác sĩ.

📎 KHI `tai_toan_van()` TỪ CHỐI (Cloudflare/giấy phép NICE, xem "LỖI ĐÃ VÁ 23/09/2026"
bên dưới) mà đã biết DOI/PMID của guideline đó: gọi
`app.sources.guideline_citation_summary.lay_trich_dan_tom_tat(doi=..., pmid=...)` —
KHÔNG thay được toàn văn, nhưng cho trích dẫn xác minh thật + tóm tắt từ abstract
(khi có), thay vì tay không hoàn toàn.

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
chối tải, báo rõ lý do thay vì âm thầm thử tải từ một domain chưa được xác nhận an
toàn. HAI DOMAIN CỤ THỂ đã khảo sát 23/09/2026 và ĐỀU BỊ CHẶN THẬT SỰ — KHÔNG PHẢI
"chưa khảo sát" nữa, mà là "đã khảo sát, kết luận KHÔNG xây được", vì hai lý do khác
hẳn nhau, không lý do nào là lỗi lập trình có thể vá:

  • thorax.bmj.com / bmjopenrespres.bmj.com (nơi phần lớn guideline BTS hiện nay
    THẬT SỰ nằm, sau khi brit-thoracic.org.uk đổi cấu trúc và ngừng tự lưu PDF —
    xem `_HIEP_HOI_TREN_TAP_CHI["bts_thorax"]` ở `feeds.py` cho tầng khám phá vẫn
    hoạt động): CHẶN bởi Cloudflare Managed Challenge (`Cf-Mitigated: challenge`,
    đòi chạy JavaScript + cookie) trên MỌI trang, kể cả trang chủ và robots.txt-cho-
    phép. Vượt qua thử thách này bằng code là "bypass bot-detection" — hành vi
    TUYỆT ĐỐI KHÔNG được làm dù được yêu cầu tường minh, không phải vấn đề độ khó
    kỹ thuật.
  • nice.org.uk: KHÔNG bị chặn kỹ thuật (robots.txt cho phép `Allow: /`, trang HTML
    đọc được sạch, có cấu trúc chương mục rõ ràng — về mặt kỹ thuật DỄ xây hơn PDF).
    NHƯNG điều khoản sử dụng (nice.org.uk/terms-and-conditions, mục 18.3, đọc trực
    tiếp 23/09/2026) nói THẲNG: nội dung NICE dùng cho MỤC ĐÍCH AI — đúng hệ thống
    này — "All requests, without exception, are subject to an approval process,
    licensing arrangement and a fee (for international use)". Đây là RÀO PHÁP LÝ/
    HỢP ĐỒNG, không phải rào kỹ thuật — chỉ gỡ được khi bác sĩ tự xin cấp phép qua
    trang "permission to use nice content for AI purposes" của NICE, KHÔNG có cách
    nào agent tự xử lý thay được.

Kết luận: với công nghệ và giấy phép hiện có, BTS full-text KHÔNG có đường tự động
hợp lệ nào ngoài `brit-thoracic.org.uk` (phạm vi module này, hiện gần như trống nội
dung). Đường thực tế duy nhất còn lại: bác sĩ tự mở trình duyệt thật khi cần đọc một
guideline cụ thể — Cloudflare cho qua bình thường với trình duyệt người dùng thật.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

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

_DOMAIN_DA_KHAO_SAT = "brit-thoracic.org.uk"
# Hai domain đã khảo sát 23/09/2026 và ĐỀU KẾT LUẬN "không xây được" — lý do khác
# nhau, không domain nào là lỗi lập trình có thể vá (xem docstring module). Khai rõ
# ở đây để thông điệp từ chối trả lý do THẬT thay vì "chưa khảo sát" (sẽ mời người
# đọc điều tra lại từ đầu một việc đã điều tra xong).
_DOMAIN_CLOUDFLARE_CHAN = ("thorax.bmj.com", "bmjopenrespres.bmj.com")
_DOMAIN_NICE_CAN_GIAY_PHEP_AI = ("nice.org.uk",)


class BtsGuidelineFullTextClient:
    """Tải TOÀN VĂN một hướng dẫn BTS theo URL PDF ĐÃ BIẾT trên brit-thoracic.org.uk.

    KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()`, KHÔNG tự dò "bản mới nhất"
    (xem giới hạn ở docstring module) — cùng khuôn `WileyTdmClient`."""

    name = "bts_guidelines_fulltext"

    def __init__(self) -> None:
        if not settings.enable_bts_guidelines_fulltext:
            raise ConnectorChuaBat(thong_diep_co_tat("bts_guidelines", "ENABLE_BTS_GUIDELINES_FULLTEXT"))
        self.http = HttpClient()

    def tai_toan_van(self, url: str,
                     gioi_han_ky_tu: Optional[int] = GIOI_HAN_KY_TU_MAC_DINH) -> KetQuaToanVanGuideline:
        """Tải + trích văn bản từ một URL PDF BTS đã biết. Từ chối NGAY (không gọi
        mạng) nếu domain khác `brit-thoracic.org.uk` — một số hướng dẫn BTS đồng xuất
        bản trỏ sang thorax.bmj.com/bmjopenrespres.bmj.com/nice.org.uk/
        rightdecisions.scot.nhs.uk. Hai domain đầu ĐÃ khảo sát và bị Cloudflare chặn;
        nice.org.uk ĐÃ khảo sát và cần giấy phép AI trả phí — xem docstring module."""
        domain = urlparse(url).netloc.lower()
        if domain.endswith(_DOMAIN_CLOUDFLARE_CHAN):
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False,
                ghi_chu=(
                    f"URL thuộc domain '{domain}' — ĐÃ khảo sát 23/09/2026, KHÔNG PHẢI "
                    "chưa kiểm: mọi trang trên domain này (kể cả robots.txt cho phép) "
                    "trả về thử thách Cloudflare Managed Challenge (đòi chạy JavaScript "
                    "+ cookie), không phải 403 thường. Vượt qua bằng code là 'bypass "
                    "bot-detection' — hành vi không được làm, không phải lỗi kỹ thuật "
                    "có thể vá. Đường thực tế duy nhất: mở trình duyệt thật."
                ),
            )
        if domain.endswith(_DOMAIN_NICE_CAN_GIAY_PHEP_AI):
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False,
                ghi_chu=(
                    f"URL thuộc domain '{domain}' — ĐÃ khảo sát 23/09/2026: KHÔNG bị "
                    "chặn kỹ thuật (robots.txt cho phép), nhưng điều khoản sử dụng "
                    "(nice.org.uk/terms-and-conditions mục 18.3) đòi giấy phép + phí "
                    "cho MỌI truy cập phục vụ mục đích AI, không ngoại lệ. Đây là rào "
                    "pháp lý/hợp đồng — chỉ bác sĩ tự xin cấp phép mới gỡ được, agent "
                    "không có thẩm quyền tự quyết định thay."
                ),
            )
        if not domain.endswith(_DOMAIN_DA_KHAO_SAT):
            return KetQuaToanVanGuideline(
                to_chuc="BTS", url_nguon=url, thanh_cong=False,
                ghi_chu=(
                    f"URL thuộc domain '{domain}', KHÁC '{_DOMAIN_DA_KHAO_SAT}' đã khảo "
                    "sát robots.txt/điều khoản — có thể đây là hướng dẫn BTS đồng xuất "
                    "bản với một tổ chức khác. Connector này CHƯA khảo sát domain đó, "
                    "từ chối tải để không vi phạm kỷ luật 'không crawl khi chưa kiểm "
                    "robots.txt/ToU trước'."
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

        thong_tin: dict = {}
        van_ban = trich_van_ban_tu_pdf(pdf_bytes, gioi_han_ky_tu=gioi_han_ky_tu, thong_tin=thong_tin)
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
            bi_cat=bool(thong_tin.get("bi_cat")), so_trang_pdf=thong_tin.get("so_trang_pdf"),
            moc_trang=list(thong_tin.get("moc_trang") or []), sha256_nguon=sha256_hex(pdf_bytes),
            ghi_chu=(f"Văn bản ĐÃ BỊ CẮT ở {gioi_han_ky_tu} ký tự — phần sau của tài liệu KHÔNG có trong "
                     "kết quả; muốn đọc/tìm toàn bộ thì truyền gioi_han_ky_tu=None."
                     if thong_tin.get("bi_cat") else None),
        )
