"""Connector TẢI TOÀN VĂN guideline đã lưu trữ trên PubMed Central (PMC) — thêm
23/09/2026, ban đầu cho ADA "Standards of Care in Diabetes" (professional.diabetes.org/
diabetesjournals.org KHÔNG đọc được robots.txt — mọi lần fetch đều 403/lỗi DNS, nên
KHÔNG được coi là "cho phép ngầm"), nhưng viết GENERIC theo PMCID nên dùng lại được
cho BẤT KỲ hội chuyên khoa nào khác có nộp lưu guideline lên PMC (nhiều hội nhận tài
trợ liên quan NIH có nghĩa vụ nộp lưu; hội châu Âu như ESC thì chưa chắc — phải tra
riêng, không suy đoán).

VIẾT LẠI 23/09/2026 (audit/14 vấn đề 4) — bản đầu scrape trực tiếp
`pmc.ncbi.nlm.nih.gov/articles/<PMCID>/` bị chặn HTTP 403 tối giản (không phải
Cloudflare — không có header `Cf-Mitigated`, không đổi theo User-Agent, cả API OA
`ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi` lẫn OAI-PMH `ncbi.nlm.nih.gov/pmc/oai/oai.cgi`
đều cùng bị chặn — kết luận cũ: "chặn cấp biên mạng, ngoài tầm sửa code").

Điều tra tiếp (audit/14 vấn đề 4, cùng ngày) tìm ra đường THẬT sự khác: readme.txt
chính thức của NCBI (`ftp.ncbi.nlm.nih.gov/pub/pmc/readme.txt`, đọc trực tiếp 23/09/2026)
khai FTP Service cũ đang bị khai tử (thông báo 02/2026, đang gỡ dần từ 08/2026), thay
bằng **PMC Cloud Service trên AWS Open Data Registry** — một bản sao PMC Open Access
Subset (chỉ bài có giấy phép cho phép phân phối lại nguyên văn) ở bucket S3 công khai,
KHÔNG CẦN tài khoản AWS, KHÔNG cùng hạ tầng/WAF với `pmc.ncbi.nlm.nih.gov`:
  • Bucket: `pmc-oa-opendata` (arn:aws:s3:::pmc-oa-opendata), region us-east-1.
  • Xác nhận sống 23/09/2026: `https://pmc-oa-opendata.s3.amazonaws.com/` trả lời qua
    HTTPS thường (`requests`), KHÔNG bị 403/WAF — khác hẳn `pmc.ncbi.nlm.nih.gov`.
  • Mỗi bài có thư mục `<PMCID>.<phiên bản>/` chứa `<PMCID>.<phiên bản>.txt` (văn bản
    thuần, có khối metadata đầu file) + `.xml`/`.pdf`/`.json`/ảnh minh hoạ — CHỈ dùng
    `.txt`, không cần thư viện đọc PDF cho đường này.
  • KHÔNG có robots.txt cho bucket này (S3 không tự sinh robots.txt — 404 NoSuchKey,
    KHÔNG phải "cấm crawl"). Điều khoản áp dụng là chính readme.txt ở trên: cho phép
    tải/dùng dữ liệu, chỉ cấm dùng logo/thương hiệu PMC và cấm phân phối lại dữ liệu
    KHÔNG có giấy phép tương ứng — khớp đúng nguyên tắc "chỉ dùng tham chiếu nội bộ,
    không đăng lại toàn văn" đã áp cho GOLD/GINA/BTS ở `guideline_fulltext_common.py`.

GIỚI HẠN THẬT, đã đo bằng 4 PMCID (không đoán, tra qua PubMed trước) — CHỈ bài đã có
mặt trong PMC Open Access Subset (đăng ký `.txt`/`.xml` toàn văn) mới có trong bucket
này; bài chỉ nộp PDF-không-kèm-văn-bản-máy-đọc hoặc chưa từng nộp lưu PMC OA Subset sẽ
KHÔNG có (0 kết quả liệt kê theo prefix — KHÔNG PHẢI lỗi, là sự thật "nguồn không có
toàn văn ở PMC", đúng khuôn "báo trung thực" của module `guideline_fulltext_common.py`).
Không tự tìm PMCID (đó là việc của `app/sources/pubmed.py`/Europe PMC hiện có) — class
này CHỈ nhận PMCID đã biết.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.config import settings
from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    KetQuaToanVanGuideline,
)
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_S3_GOC = "https://pmc-oa-opendata.s3.amazonaws.com/"
_MAU_PMCID = re.compile(r"^PMC\d+$", re.IGNORECASE)
# Khớp <Key>PMC12690171.2/PMC12690171.2.txt</Key> — bắt CẢ số phiên bản để chọn bản
# MỚI NHẤT khi bucket có nhiều phiên bản của cùng một bài.
_MAU_KEY_TXT = re.compile(r"<Key>(PMC\d+)\.(\d+)/\1\.\2\.txt</Key>", re.IGNORECASE)
_GIOI_HAN_KY_TU = 200_000  # đồng bộ với trich_van_ban_tu_pdf() ở guideline_fulltext_common.py


class PmcGuidelineFullTextClient:
    """Tải TOÀN VĂN một bài/chương guideline đã có trong PMC Open Access Subset, theo
    PMCID đã biết — qua bản sao S3 công khai của NCBI (KHÔNG qua trang HTML
    `pmc.ncbi.nlm.nih.gov` — trang đó chặn 403, xem docstring module).

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
        self.http = HttpClient()

    def _tim_key_txt_moi_nhat(self, pmcid_chuan: str) -> Optional[str]:
        """Liệt kê object trong bucket theo prefix `<PMCID>.` rồi chọn key `.txt` của
        phiên bản CAO NHẤT (bucket có thể giữ nhiều phiên bản của cùng một bài)."""
        try:
            xml = self.http.get_text(
                _S3_GOC, params={"list-type": "2", "prefix": f"{pmcid_chuan}."}
            )
        except Exception as exc:  # noqa: BLE001 — lỗi mạng, KHÔNG bịa kết quả
            logger.warning("[pmc_guideline_fulltext] không liệt kê được bucket cho %s: %s",
                            pmcid_chuan, exc)
            return None
        ung_vien: List[tuple[int, str]] = []
        for match in _MAU_KEY_TXT.finditer(xml):
            _pmcid, phien_ban = match.group(1), match.group(2)
            ung_vien.append((int(phien_ban), f"{pmcid_chuan}.{phien_ban}/{pmcid_chuan}.{phien_ban}.txt"))
        if not ung_vien:
            return None
        ung_vien.sort(key=lambda cap: cap[0], reverse=True)
        return ung_vien[0][1]

    def tai_toan_van(self, pmcid: str) -> KetQuaToanVanGuideline:
        """Tải + trích văn bản một bài PMC theo PMCID (định dạng "PMC1234567", có hoặc
        không tiền tố PMC đều được chuẩn hoá). Không bịa PMCID — người gọi phải tự tra
        qua PubMed/Europe PMC trước. 0 kết quả trong bucket ⇒ bài KHÔNG có trong PMC
        Open Access Subset — sự thật, không phải lỗi công cụ."""
        pmcid_chuan = pmcid.strip().upper()
        if not pmcid_chuan.startswith("PMC"):
            pmcid_chuan = f"PMC{pmcid_chuan}"
        if not _MAU_PMCID.match(pmcid_chuan):
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=pmcid, thanh_cong=False,
                ghi_chu=f"'{pmcid}' không đúng định dạng PMCID (kỳ vọng 'PMC' + số).",
            )

        key = self._tim_key_txt_moi_nhat(pmcid_chuan)
        if key is None:
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=_S3_GOC + pmcid_chuan, thanh_cong=False,
                ghi_chu=(
                    f"{pmcid_chuan} KHÔNG có trong PMC Open Access Subset (bucket S3 "
                    "công khai của NCBI) — bài này chưa từng nộp lưu toàn văn máy-đọc "
                    "cho PMC, hoặc chỉ nộp PDF không kèm bản văn bản/XML. Đây là giới "
                    "hạn THẬT của nguồn, không phải lỗi mạng — cần xác nhận thủ công "
                    "(vd đọc trực tiếp trên trang tạp chí gốc)."
                ),
            )

        url_txt = _S3_GOC + key
        try:
            van_ban_tho = self.http.get_text(url_txt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[pmc_guideline_fulltext] tải %s thất bại: %s", url_txt, exc)
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_txt, thanh_cong=False, ghi_chu=str(exc),
            )
        if not van_ban_tho.strip():
            return KetQuaToanVanGuideline(
                to_chuc="PMC", url_nguon=url_txt, thanh_cong=False,
                ghi_chu="Object .txt tồn tại trong bucket nhưng nội dung rỗng — bất "
                        "thường, cần xác nhận thủ công.",
            )
        van_ban = van_ban_tho[:_GIOI_HAN_KY_TU]
        return KetQuaToanVanGuideline(
            to_chuc="PMC", url_nguon=url_txt, thanh_cong=True,
            van_ban_trich=van_ban, so_trang_hoac_ky_tu=len(van_ban),
            ghi_chu_ban_quyen=GHI_CHU_BAN_QUYEN_CHUAN,
        )
