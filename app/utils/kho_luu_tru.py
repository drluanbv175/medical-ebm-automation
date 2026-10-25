"""Nhận diện bản ghi nằm trên KHO LƯU TRỮ ĐA NĂNG (Zenodo, figshare, OSF, Dryad, Dataverse, Mendeley Data).

Kho lưu trữ đa năng là nơi ai cũng nộp được, không bình duyệt, không phải nơi tổ chức/tạp chí PHÁT HÀNH văn bản. Bản
lưu ở đó có thể là câu trả lời AI, slide, infographic, dữ liệu, kế hoạch phân tích hay bản tự lưu của một bài — không
bao giờ là bản guideline/thử nghiệm để thay đổi thực hành.

Sự cố có thật (18/10/2026, đo lại 25/10/2026 trên DB engine): OpenAlex trả 333 bản ghi Zenodo (không tính bản trùng);
14 bản bị gắn «guideline» chỉ vì tiêu đề có chữ guideline/recommend — cả 14 KHÔNG phải guideline (câu trả lời AI «Trip
Database Ask» như «What do the KDIGO guidelines recommend for anemia management?», infographic, nghiên cứu tuân thủ).
4 bản lên tier A «actionable» (điểm 90–93: nền thiết kế guideline + tên KDIGO trong câu hỏi bị đọc thành tổ chức phát
hành) và cầu nối `scripts/bridge_to_ebm_master.py` đưa chúng vào hub EBM_MASTER thành thẻ «guideline tier A».

Nhận diện theo HAI tín hiệu độc lập: tiền tố DOI do chính kho cấp (bền kể cả khi metadata gán nhầm tên tạp chí — đo
25/10: DOI 10.5281/ mang tên một loạt «tạp chí» dùng Zenodo cấp DOI) và tên nơi lưu do nguồn ghi. Chỉ thư viện chuẩn —
được cả `app.sources`, `app.scoring`, `app.services.filtering` lẫn cầu nối (script độc lập) gọi mà không vướng vòng
import.
"""
from __future__ import annotations

import re
from typing import Optional

# Tên chuẩn → (tiền tố DOI do kho cấp, mẫu tên nơi lưu — khớp trên chữ thường).
KHO_LUU_TRU_DA_NANG: dict[str, tuple[tuple[str, ...], re.Pattern]] = {
    "Zenodo": (("10.5281/",), re.compile(r"\bzenodo\b")),
    "figshare": (("10.6084/",), re.compile(r"\bfigshare\b")),
    "OSF": (("10.17605/",), re.compile(r"\bopen science framework\b|^osf$|^osf registries\b")),
    "Dryad": (("10.5061/",), re.compile(r"\bdryad\b")),
    "Harvard Dataverse": (("10.7910/",), re.compile(r"\bdataverse\b")),
    "Mendeley Data": (("10.17632/",), re.compile(r"\bmendeley data\b")),
}

# Thiết kế MẠNH mà bộ suy chỉ đọc được từ chữ trong tiêu đề — với bản lưu trên kho, chữ đó không chứng minh được
# thiết kế.
THIET_KE_MANH = frozenset({"guideline", "systematic_review", "rct"})


def kho_luu_tru_da_nang(doi: Optional[str] = None, noi_luu: Optional[str] = None) -> Optional[str]:
    """Tên chuẩn của kho lưu trữ đa năng chứa bản ghi, hoặc None.

    `doi` nhận cả dạng «https://doi.org/…» hay «doi:…»; `noi_luu` là `journal_or_organization` của nguồn."""
    d = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", str(doi or "").strip().lower())
    ten = str(noi_luu or "").strip().lower()
    for chuan, (tien_to, mau) in KHO_LUU_TRU_DA_NANG.items():
        if (d and d.startswith(tien_to)) or (ten and mau.search(ten)):
            return chuan
    return None


def ly_do_kho_luu_tru(kho: str) -> str:
    """Lý do phân loại (hiển thị cho bác sĩ) của bản ghi nằm trên kho lưu trữ đa năng."""
    return (f"Bản lưu trên kho lưu trữ đa năng {kho} — không phải bản phát hành của tổ chức/tạp chí (có thể là câu "
            "trả lời AI, slide, dữ liệu hoặc bản tự lưu); chỉ theo dõi, tìm văn bản gốc trước khi dùng. Cần bác sĩ "
            "kiểm chứng.")
