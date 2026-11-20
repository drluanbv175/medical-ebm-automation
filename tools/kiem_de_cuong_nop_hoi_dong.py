#!/usr/bin/env python3
"""Kiểm bản ĐỀ CƯƠNG NỘP HỘI ĐỒNG `exports/<mã>/DE_CUONG_NOP_HOI_DONG_<mã>.md` + `.docx` (nhiệm vụ G10-T4, 15/10/2026).

Vì sao có: bác sĩ chê bản lắp máy `DE_CUONG_THONG_NHAT_<mã>` (ký hiệu hệ thống, tên biến, bảng cổng) «khó mà chấp
nhận được» để nộp Hội đồng; đề cương nộp được viết lại bằng văn phong khoa học. Viết tay thì dễ trôi khỏi quyết định đã
chốt hoặc sót ký hiệu nội bộ — công cụ này là lớp kiểm MÁY cho đầu ra đó (chất lượng văn phong, độ đúng nguồn vẫn do
`tham-dinh-dau-ra` + `kiem-chung-trich-dan` chấm chéo).

Luật (mỗi lỗi một dòng; rỗng = đạt):
  K1  có đủ cặp `.md` + `.docx`;
  K2  bản Word sinh từ CHÍNH bản `.md`: mọi đề mục cấp 1 của `.md` có trong chữ hiển thị của `.docx`, cùng tập PMID;
  K3  đủ chương mục của đề cương (đặt vấn đề · mục tiêu · tổng quan · đối tượng và phương pháp · đạo đức · dự kiến kết
      quả · kế hoạch · tài liệu tham khảo · phụ lục bản thông tin/phiếu đồng ý · phụ lục công cụ thu thập); tổng quan
      hệ thống (sr_ma) không có người tham gia nên không đòi phụ lục phiếu đồng ý;
  K4  không ký hiệu nội bộ của hệ thống (cổng G0/G4–G10, «SAP §», «§», nhãn [CẦN…], checkpoint, study_meta, pipeline,
      agent, dry-run, forced-in…); tên biến dạng `ten_bien` chỉ được ở bảng hoặc ở phụ lục;
  K5  cỡ mẫu khớp G3 (`confirmed_n` của G3_checkpoint.json có mặt trong văn bản);
  K6  mọi PMID nằm trong biên nhận rút bài A12 (`A12_RETRACTION_RECEIPT.json`) đã kiểm và sạch;
  K7  không email/số điện thoại (bỏ DOI/URL trước khi dò), không nhãn ô trống [CẦN…] (dòng chấm «………» để PI điền tay
      là hợp lệ).
  K9  biểu bảng đúng chuẩn trong chương «Dự kiến kết quả» (bác sĩ 19/11/2026: «phần trình bày biểu bảng chưa có và
      chưa đúng chuẩn»): tên bảng in đậm ĐẶT TRÊN bảng, tên hình/biểu đồ đặt DƯỚI hình, đánh số liên tục; ghi chú giải
      thích chữ viết tắt; không hàng giữ chỗ; bảng đặc điểm nền không cột p; ước lượng kèm KTC 95%; MỖI mục tiêu có bảng
      hoặc biểu đồ; có hình/biểu đồ và đủ khung bắt buộc của chuẩn báo cáo theo thiết kế (luật ở `khung_bieu_bang.py`;
      dựng/nâng cấp: `khung_bieu_bang.py --study <mã> --thay-chuong|--nang-cap --ghi`).
  K8  không dấu vết soạn thảo/máy (bác sĩ 17/11/2026): «DRAFT», «bản nháp», «do AI/trí tuệ nhân tạo soạn»,
      «máy soạn/máy sinh», «Cần bác sĩ kiểm chứng», «Mức tự động», chú thích HTML, nhãn «(giả lập)»/«GIẢ LẬP»,
      «hồ sơ chưa có». Thêm 18/11/2026: «(… đã chốt)», mã SOP-…, mã thiếu («mã KGHS»), «= 1»/«khác 9» trong văn
      xuôi, nhãn tự đánh giá, nhãn biến lặp, thời điểm huỷ bảng nối mã lệch nhau giữa các mục.
  K10 không số liệu «trôi nổi» (bác sĩ 20/11/2026: «Không có số liệu thực, chứng cứ thực hãy loại bỏ»): trong đặt vấn
      đề / tổng quan / bàn luận, mỗi mệnh đề mang số liệu kiểu kết quả (%, OR/RR/HR/PR, KTC 95%, TB ± ĐLC) phải tự mang
      trích dẫn [n]; tách mệnh đề ở «;» ngoài ngoặc. Nguồn không có trong danh mục ⇒ loại con số.
  K11 chuẩn trình bày tiếng Việt (bác sĩ 20/11/2026: «từng câu, từng chữ… từng bảng từng đồ thị phải đúng chuẩn, đúng
      định dạng»): số thập phân dấu phẩy, nhóm nghìn từ 5 chữ số, ngày dd/mm/yyyy, ngoặc kép “…”, không «vs», không chữ
      IN HOA nhấn mạnh ngoài phụ lục, loại biến không bỏ lửng «Định danh/thứ bậc», tên bảng/hình không hai ngoặc liền;
      bảng chữ viết tắt không hai mục cùng nghĩa, không mục thừa, xếp theo vần tiếng Việt. (Bảng «mỗi mức một dòng»
      ở K9.) Danh mục tài liệu tham khảo, mã, chuỗi tìm kiếm, DOI/URL/PMID được miễn.

Lệnh:  python3 tools/kiem_de_cuong_nop_hoi_dong.py --study <mã> [--json]
Mã thoát: 0 đạt · 1 có lỗi · 2 thiếu tệp đề cương nộp.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import g10_quality_gate as G10  # noqa: E402

TEN = "DE_CUONG_NOP_HOI_DONG_{study}"
# (nhãn hiển thị, các từ khoá — một đề mục bất kỳ chứa MỘT từ khoá là đạt; so không phân biệt hoa thường)
CHUONG_BAT_BUOC = (
    ("đặt vấn đề", ("ĐẶT VẤN ĐỀ",)),
    ("mục tiêu nghiên cứu", ("MỤC TIÊU",)),
    ("tổng quan tài liệu", ("TỔNG QUAN",)),
    ("đối tượng và phương pháp", ("ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP",)),
    ("đạo đức nghiên cứu", ("ĐẠO ĐỨC",)),
    ("dự kiến kết quả", ("DỰ KIẾN KẾT QUẢ",)),
    ("kế hoạch thực hiện", ("KẾ HOẠCH THỰC HIỆN", "TIẾN ĐỘ")),
    ("tài liệu tham khảo", ("TÀI LIỆU THAM KHẢO",)),
    ("phụ lục bản thông tin/phiếu đồng ý", ("ĐỒNG Ý THAM GIA", "ĐỒNG THUẬN")),
    ("phụ lục công cụ thu thập", ("PHIẾU KHẢO SÁT", "PHIẾU THU THẬP", "BỘ CÂU HỎI", "BỆNH ÁN NGHIÊN CỨU",
                                  "PHIẾU TRÍCH XUẤT")),
)
# 16/11/2026 (bộ sinh đề cương nộp, giả lập 15 kịch bản): tổng quan hệ thống/phân tích gộp KHÔNG có người tham gia —
# đòi phụ lục phiếu đồng ý là đòi một tài liệu không tồn tại (đề cương sẽ phải bịa ra để qua K3).
KHONG_CAN_DONG_Y = ("sr_ma",)


def _thiet_ke(out_dir: Path) -> str:
    try:
        meta = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
        return str(((meta.get("gate_params") or {}).get("G1") or {}).get("design") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""
# Ký hiệu nội bộ của hệ thống không được lọt vào văn bản nộp. Không bắt «G1–G3» vì có thể là mã câu hỏi của phiếu.
_KY_HIEU_NOI_BO = (
    (re.compile(r"\bcổng\s+G\d", re.IGNORECASE), "«cổng G…»"),
    (re.compile(r"\bG(?:0|[4-9]|10)\b"), "mã cổng G0/G4–G10"),
    (re.compile(r"\bSAP\b"), "«SAP»"),
    (re.compile(r"§"), "ký hiệu «§»"),
    (re.compile(r"\[CẦN", re.IGNORECASE), "nhãn [CẦN…]"),
    (re.compile(r"\b(?:checkpoint|study_meta|pipeline|StudySpec|dry-run|forced-in|complete-case)\b",
                re.IGNORECASE), "thuật ngữ nội bộ hệ thống"),
    (re.compile(r"\bagent\b", re.IGNORECASE), "«agent»"),
)
# K8 (17/11/2026): văn bản nộp đọc như văn bản do nhóm nghiên cứu viết — không còn dấu vết khuôn/máy/bản nháp.
_DAU_VET_MAY = (
    (re.compile(r"\bDRAFT\b"), "«DRAFT»"),
    (re.compile(r"bản\s+nháp", re.IGNORECASE), "«bản nháp»"),
    (re.compile(r"(?:do|bằng|với hỗ trợ của)\s+(?:AI|trí tuệ nhân tạo)\b|\bAI\s+hỗ trợ soạn", re.IGNORECASE),
     "«AI soạn»"),
    (re.compile(r"máy\s+(?:soạn|sinh|tự điền)|tự động sinh", re.IGNORECASE), "«máy soạn/sinh»"),
    (re.compile(r"cần bác sĩ kiểm chứng|mức tự động", re.IGNORECASE), "lời dặn của hệ"),
    (re.compile(r"<!--"), "chú thích HTML"),
    (re.compile(r"GIẢ LẬP|\(giả lập\)|hồ sơ chưa có"), "nhãn giả lập/ô chưa điền"),
    # 17/11/2026 — 11 dấu vết K1–K8 bỏ sót, lộ khi phản biện máy (Claude API) đọc đề cương BTM thật; mã hoá thành luật
    # tất định để lần sau bắt được không cần API.
    (re.compile(r"(?<![\w/.-])[A-Z][A-Z0-9]*_[A-Z0-9][A-Z0-9_]*\b"), "mã tệp nội bộ (vd G0_KHOANG_TRONG)"),
    (re.compile(r"(?<![\w/.@-])[A-Za-zÀ-ỹ]{2,}\.[a-z_]{4,}\b(?![.\w])"),
     "khoá máy dính dấu chấm (vd «như.intervention»)"),
    (re.compile(r"\bgate_params\b"), "khoá gate_params"),
    (re.compile(r"\(\s*(?:quyết|chốt|duyệt)\s*\)"), "dấu quyết định «(quyết)»"),
    (re.compile(r"phiếu đề xuất|công cụ phân tích của hệ thống", re.IGNORECASE), "trỏ tài liệu/công cụ nội bộ"),
    (re.compile(r"\b(?:PI|chủ nhiệm)(?:\s+đề tài)?\s+(?:chọn|chốt|duyệt|quyết)\b[^.;()|]{0,40}\d{1,2}/\d{1,2}/\d{4}"),
     "lời ghi nguồn gốc quyết định kèm ngày"),
    (re.compile(r"\bở\s+A\d{1,2}b?\b"), "mã tài liệu nội bộ «ở A…»"),
    (re.compile(r"\b(?:với|cho|của)\s*[;,)]"), "câu cụt sau giới từ («với;»)"),
    (re.compile(r"(?<![.…])\.\.(?![.…])"), "dấu chấm đôi"),
    # 17/11/2026 vòng đọc 1 trên 16 đề cương giả lập
    (re.compile(r"(?<!\w)(tỷ lệ|nhóm|bệnh nhân|người bệnh|kết cục) \1(?!\w)"), "lặp chữ («tỷ lệ tỷ lệ»)"),
    (re.compile(r"\b(?:EXPEDITED|EXEMPT|FULL BOARD)\b"), "tên hình thức xét duyệt tiếng Anh"),
    (re.compile(r"ghi rõ chính sách|\w…\*\*"), "ghi chú cho người soạn / tiêu đề bị cắt"),
    (re.compile(r"\|\s*(?:yeu to|ket cuc(?: chinh| phu)?|hiep bien|mo ta|phoi nhiem|dieu chinh|nhieu)\s*\|"),
     "mã vai trò không dấu trong bảng"),
    # 18/11/2026 — phản biện máy lượt 2 trên đề cương BTM thật (bác sĩ duyệt nhãn «máy đúng»): 7 dấu vết K1–K8 bỏ sót.
    (re.compile(r"\([^()]{0,24}\bđã\s+(?:chốt|duyệt)\s*\)"), "ghi chú «(… đã chốt)»"),
    (re.compile(r"\bSOP-[A-Z]{1,5}-\d{1,3}\b"), "mã quy trình nội bộ «SOP-…»"),
    (re.compile(r"\bmã\s+(?!ICD|ATC)[A-Z]{3,5}\b(?![-\d])"), "mã thiếu/mã nội bộ («mã KGHS»)"),
    (re.compile(r"[A-Za-zÀ-ỹ]{3,}\s=\s[0-29]\b(?![.,]?\d)|\bkhác\s+9\b"), "mã biến trong văn xuôi («= 1», «khác 9»)"),
    (re.compile(r"\b(?:Mức tính mới|Phạm vi tra)\s*:"), "nhãn tự đánh giá nội bộ («Mức tính mới:»)"),
    (re.compile(r";\s*biến\s+[a-z]+[A-Z0-9]"), "nhãn biến lặp trong ngoặc («; biến hbA1c 3 mức»)"),
    # 18/11/2026 — đề cương BTM ghi «Đn1…Đn9» trong khi kế hoạch phân tích ghi «ĐN1…ĐN9» (bộ sinh hạ chữ nhấn mạnh).
    (re.compile(r"(?<!\w)(?:Đn|đn)\d{1,2}\b"), "mã phân tích độ nhạy bị hạ chữ («Đn2» thay «ĐN2»)"),
    # 18/11/2026 — phản biện máy lượt 3 trên BTM: chú thích tiếng Anh kiểu máy và ngày quyết định trong ngoặc.
    (re.compile(r"\(=\s*[A-Za-z][a-z]+\)"), "chú thích tiếng Anh kiểu máy («(= descriptive)»)"),
    (re.compile(r"\(quyết định\s+(?:ngày\s+)?\d{1,2}/\d{1,2}/\d{4}\)"),
     "ghi ngày quyết định nội bộ «(quyết định 28/10/2026)»"),
)
# 18/11/2026: cùng một bảng nối mã mà hai chỗ hứa hai thời điểm huỷ khác nhau (BTM: «khoá dữ liệu» ở mục đạo đức và quản
# lý dữ liệu, «kết thúc nghiên cứu» ở cam kết bảo mật) — Hội đồng đọc thấy ngay, K1–K8 không so.
_HUY_NOI_MA = {
    "khoá dữ liệu": re.compile(r"huỷ\s+sau\s+khi\s+khoá\s+dữ\s+liệu", re.IGNORECASE),
    "kết thúc nghiên cứu": re.compile(r"huỷ\s+sau\s+khi\s+kết\s+thúc\s+nghiên\s+cứu", re.IGNORECASE),
}
_TEN_BIEN_RE = re.compile(r"(?<![\w./-])[a-z][a-z0-9]*_[a-z0-9_]+\b")
_DE_MUC_RE = re.compile(r"^(#{1,4})\s+(.*\S)\s*$", re.MULTILINE)


def _doc(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _chu_docx(p: Path) -> Optional[str]:
    try:
        with zipfile.ZipFile(p) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="strict")
            return G10._docx_visible_text(archive, xml)
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile):
        return None


def _chuan(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", s)).strip().upper()


def _pmid(text: str) -> set:
    return set(re.findall(r"PMID:?\s*(\d{5,9})", text))


def _dinh_dang_n(n: int) -> tuple:
    return (str(n), f"{n:,}".replace(",", "."), f"{n:,}")


def loi_k8(md: str) -> List[str]:
    """K8 — dấu vết soạn thảo/máy theo từng dòng (mỗi dòng báo mẫu đầu tiên khớp) + thời điểm huỷ bảng nối mã lệch."""
    loi: List[str] = []
    for so, dong in enumerate(md.splitlines(), 1):
        for bt, nhan in _DAU_VET_MAY:
            if bt.search(dong):
                loi.append(f"K8 dòng {so}: dấu vết soạn thảo/máy ({nhan})")
                break
    thoi_diem = [ten for ten, bt in _HUY_NOI_MA.items() if bt.search(md)]
    if len(thoi_diem) > 1:
        loi.append(f"K8 thời điểm huỷ bảng nối mã khác nhau giữa các mục ({' / '.join(thoi_diem)}) — thống nhất theo "
                   "quy trình dữ liệu đã chốt")
    return loi


# K10 (bác sĩ 20/11/2026: «Không có số liệu thực, chứng cứ thực hãy loại bỏ trong hệ thống nghiên cứu y khoa»).
# Phản biện máy đề cương BTM bắt «(15,32% đến 31,1%)» trong tổng quan: hai nghiên cứu trong nước có thật nhưng KHÔNG nằm
# trong danh mục tài liệu tham khảo của đề cương, câu chỉ mang [11] ở MỆNH ĐỀ SAU dấu «;» nên người đọc tưởng có
# nguồn.
_PHAN_CHUNG_CU_RE = re.compile(r"ĐẶT VẤN ĐỀ|TỔNG QUAN|BÀN LUẬN", re.I)
_SO_KET_QUA_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s?%"                                      # tỷ lệ
    r"|\b(?:a?OR|AOR|aPR|PR|RR|HR|IRR)\s*[=:]?\s*\d"           # thước đo hiệu ứng
    r"|\bKTC\s*95|\b95\s*%\s*CI"                                # khoảng tin cậy
    r"|\d\s*±\s*\d")                                            # trung bình ± độ lệch chuẩn
_TRICH_DAN_RE = re.compile(r"\[\d+(?:\s*[–,-]\s*\d+)*\]")
_HET_CAU_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ỹ\[(«])")


def _menh_de(cau: str) -> List[str]:
    """Tách câu thành mệnh đề ở «;» nằm NGOÀI ngoặc — «(aOR 0,53; KTC 95%: 0,28–0,98)» là một khối, không phải hai."""
    ra, sau, tang = [], [], 0
    for ky in cau:
        tang += (ky in "([") - (ky in ")]")
        if ky == ";" and tang <= 0:
            ra.append("".join(sau))
            sau = []
        else:
            sau.append(ky)
    ra.append("".join(sau))
    return [x.strip() for x in ra if x.strip()]


def loi_k10(md: str) -> List[str]:
    """K10 — trong đặt vấn đề / tổng quan / bàn luận, MỖI mệnh đề mang số liệu kiểu kết quả nghiên cứu phải tự
    mang trích dẫn [n]. Không có nguồn trong danh mục ⇒ loại con số (hoặc đưa nguồn thật vào danh mục) — không giữ
    số «trôi nổi»."""
    loi: List[str] = []
    cap: Dict[int, bool] = {}
    trong = False
    for so, dong in enumerate(md.splitlines(), 1):
        m = _DE_MUC_RE.match(dong)
        if m:
            k = len(m.group(1))
            cap = {c: v for c, v in cap.items() if c < k}
            cap[k] = bool(_PHAN_CHUNG_CU_RE.search(m.group(2)))
            trong = any(cap.values())
            continue
        s = dong.strip()
        if not trong or not s or s.startswith(("|", "!", "```", ">", "<!--")):
            continue
        for cau in _HET_CAU_RE.split(s):
            for md_ in _menh_de(cau):
                if _SO_KET_QUA_RE.search(md_) and not _TRICH_DAN_RE.search(md_):
                    loi.append(f"K10 dòng {so}: số liệu không có trích dẫn trong cùng mệnh đề — «{md_[:90]}» "
                               "(không có nguồn thật trong danh mục ⇒ loại con số)")
    return loi


# K11 (bác sĩ 20/11/2026: «từng câu, từng chữ, ngữ nghĩa phải chuẩn, từng bảng từng đồ thị phải đúng chuẩn, đúng định
# dạng»). Soát tay đề cương BTM/C1a gặp lặp lại: số kiểu máy (0.1; 100000; 2026-01-01), ngoặc kép thẳng/«», hai mục
# viết tắt cùng nghĩa (SD và ĐLC), mục viết tắt không dùng, bảng viết tắt không theo vần, loại biến «Định danh/thứ bậc»,
# tên bảng hai ngoặc liền «(…) (Mục tiêu 3)», «vs», chữ IN HOA nhấn mạnh trong câu («ước lượng CAO»).
_SO_THAP_PHAN_MAY_RE = re.compile(r"(?<![\w.,])0\.\d+(?![\d.])")
_SO_LON_MAY_RE = re.compile(r"(?<![\w.,/-])\d{5,}(?![\w.,/-])")
_NGAY_ISO_RE = re.compile(r"(?<![\w-])(?:19|20)\d{2}-[01]\d-[0-3]\d(?![\w-])")
_NGOAC_KEP_RE = re.compile(r"[«»]|\"[^\"\n]{1,200}\"")
_VS_RE = re.compile(r"(?<![\wÀ-ỹ])vs\.?(?![\wÀ-ỹ])")
_IN_HOA_NHAN_RE = re.compile(r"(?<![\wÀ-ỹ])(?:CAO|THẤP|KHÔNG|CHỈ|MỌI|PHẢI|LUÔN|TĂNG|GIẢM|ĐÚNG|SAI)(?![\wÀ-ỹ])")
_TIM_KIEM_RE = re.compile(r"\[(?:Mesh|tiab|pt|ti|tw|majr|dp)\]", re.I)
_TEN_BB_HAI_NGOAC_RE = re.compile(r"^\*\*(?:Bảng|Hình|Biểu đồ) [0-9A-Z]+\.\d+\..*\)\s*\(")


def _khoa_van_viet(k: str) -> str:
    """Khoá xếp theo bảng chữ cái tiếng Việt cho chữ viết tắt: không phân biệt hoa thường, «Đ» sau «D»."""
    return k.upper().replace("Đ", "D~")


def loi_k11(md: str) -> List[str]:
    """K11 — chuẩn trình bày tiếng Việt của văn bản nộp (đề cương, bản thảo). Bỏ qua: danh mục tài liệu tham khảo (giữ
    nguyên văn), mã trong `…`, dòng chuỗi tìm kiếm ([tiab]/[Mesh]…), DOI/URL, PMID, dòng hình. Mỗi dòng báo một lỗi."""
    loi: List[str] = []
    dong = md.splitlines()
    trong_tltk = trong_vt = phu_luc = False
    vt: Dict[str, str] = {}
    vt_dong: List[int] = []
    for so, d in enumerate(dong, 1):
        m = _DE_MUC_RE.match(d)
        if m:
            ten = m.group(2).upper()
            trong_tltk = "TÀI LIỆU THAM KHẢO" in ten
            trong_vt = "CHỮ VIẾT TẮT" in ten
            if len(m.group(1)) == 1:
                phu_luc = ten.startswith("PHỤ LỤC")
        if trong_vt and d.startswith("|") and not re.match(r"^\|[-\s|:]+\|$", d):
            o = [x.strip() for x in d.strip().strip("|").split("|")]
            if len(o) >= 2 and not re.match(r"(?:Chữ viết tắt|Viết tắt)$", o[0], re.I):
                vt[o[0]] = o[1]
                vt_dong.append(so)
            continue
        if trong_tltk or d.startswith("![") or _TIM_KIEM_RE.search(d):
            continue
        s = G10._DOI_URL_RE.sub(" ", re.sub(r"`[^`]*`", " ", d))
        s = re.sub(r"PMID:?\s*\d+|\b10\.\d{4,9}/\S+", " ", s)
        luat = (
            (_SO_THAP_PHAN_MAY_RE, "số thập phân dùng dấu chấm — viết dấu phẩy (0,1)"),
            (_SO_LON_MAY_RE, "số từ 5 chữ số chưa nhóm nghìn — viết 10.000"),
            (_NGAY_ISO_RE, "ngày dạng ISO — viết dd/mm/yyyy"),
            (_NGOAC_KEP_RE, "ngoặc kép thẳng hoặc «» — dùng ngoặc kép tiếng Việt “…”"),
            (_VS_RE, "«vs» — viết «so với»"),
        )
        for bt, nhan in luat:
            hit = bt.search(s)
            if hit:
                loi.append(f"K11 dòng {so}: {nhan} («{hit.group(0)[:30]}»)")
                break
        if "Định danh/thứ bậc" in s or "định danh/thứ bậc" in s:
            loi.append(f"K11 dòng {so}: loại biến bỏ lửng «Định danh/thứ bậc» — ghi rõ Định danh, Thứ bậc hoặc "
                       "Định danh (chọn nhiều)")
        if _TEN_BB_HAI_NGOAC_RE.match(d.strip()):
            loi.append(f"K11 dòng {so}: tên bảng/hình có hai ngoặc đơn liền nhau — gộp hoặc bỏ phần ngoặc thừa")
        # Phụ lục (phiếu thu thập, phiếu đồng ý) được dùng chữ in hoa nhấn mạnh cho người điền («KHÔNG có trong đơn»).
        if not m and not phu_luc and not d.lstrip().startswith("**"):
            # Ô bảng viết hoa toàn bộ là NHÃN trạng thái («KHÔNG ÁP DỤNG» của bảng kiểm STROBE), không phải nhấn mạnh
            # trong câu — chỉ bắt khi chữ in hoa nằm giữa chữ thường của cùng ô/câu.
            doan = [o for o in s.split("|")] if d.lstrip().startswith("|") else [s]
            hoa = next((h for o in doan if any(ch.islower() for ch in o) for h in [_IN_HOA_NHAN_RE.search(o)] if h),
                       None)
            if hoa:
                loi.append(f"K11 dòng {so}: chữ IN HOA để nhấn mạnh trong câu («{hoa.group(0)}») — viết thường")
    if vt:
        nghia: Dict[str, List[str]] = {}
        for k, v in vt.items():
            chinh = re.sub(r"\s*\([^()]*\)\s*", " ", v).split(";")[0].strip().lower()
            nghia.setdefault(chinh, []).append(k)
        for chinh, ds in nghia.items():
            if len(ds) > 1 and chinh:
                loi.append(f"K11 bảng chữ viết tắt: {', '.join(ds)} cùng nghĩa «{chinh}» — giữ một")
        than = "\n".join(d for so, d in enumerate(dong, 1) if so not in set(vt_dong))
        i_tltk = re.search(r"^#{1,2}\s+(?:\d+\.\s*)?TÀI LIỆU THAM KHẢO", than, re.M)
        if i_tltk:
            j = re.search(r"^#{1,2}\s+PHỤ LỤC", than[i_tltk.end():], re.M)
            than = than[:i_tltk.start()] + (than[i_tltk.end() + j.start():] if j else "")
        for k in vt:
            dau = re.split(r"[,\s±]+", k)[0]
            # «ĐN» được dùng dưới dạng ĐN1–ĐN9, «MT» dưới dạng MT1–MT3 ⇒ cho phép số liền sau
            if dau and not re.search(rf"(?<![\wÀ-ỹ]){re.escape(dau)}(?:\d|(?![\wÀ-ỹ]))", than):
                loi.append(f"K11 bảng chữ viết tắt: «{k}» không xuất hiện trong văn bản — bỏ mục này")
        if list(vt) != sorted(vt, key=_khoa_van_viet):
            loi.append("K11 bảng chữ viết tắt chưa xếp theo bảng chữ cái tiếng Việt")
    return loi


def loi_k9(out_dir: Path, md: str, thiet_ke: str) -> List[str]:
    """K9 — biểu bảng của chương «Dự kiến kết quả» (luật và chuẩn ở `khung_bieu_bang`)."""
    import khung_bieu_bang as KBB  # noqa: PLC0415

    try:
        meta = json.loads((Path(out_dir) / "study_meta.json").read_text(encoding="utf-8"))
        mt = ((meta.get("gate_params") or {}).get("G1") or {}).get("objectives") or []
        so_mt = len([x for x in (mt if isinstance(mt, list) else [mt]) if str(x).strip()])
    except (OSError, ValueError, AttributeError):
        so_mt = 0
    return KBB.kiem_bieu_bang(md, thiet_ke, so_mt, goc=Path(out_dir))


def kiem(out_dir: Path, study: str) -> List[str]:
    """Danh sách lỗi của bản đề cương nộp Hội đồng (rỗng = đạt). Thiếu tệp `.md` ⇒ một lỗi K1."""
    out_dir = Path(out_dir)
    md_p = out_dir / (TEN.format(study=study) + ".md")
    docx_p = out_dir / (TEN.format(study=study) + ".docx")
    loi: List[str] = []
    if not md_p.is_file():
        return [f"K1 chưa có {md_p.name}"]
    md = _doc(md_p)
    if md is None:
        return [f"K1 không đọc được {md_p.name}"]
    docx_chu = _chu_docx(docx_p) if docx_p.is_file() else None
    if docx_chu is None:
        loi.append(f"K1 thiếu hoặc hỏng {docx_p.name} (xuất lại: tools/sinh_de_cuong_nop_hoi_dong.py --ghi)")

    de_muc = [(len(m.group(1)), m.group(2)) for m in _DE_MUC_RE.finditer(md)]
    if docx_chu is not None:
        chu = _chuan(docx_chu)
        thieu = [dm for cap, dm in de_muc if cap == 1 and _chuan(dm) not in chu]
        if thieu:
            loi.append(f"K2 bản Word không khớp bản .md — thiếu đề mục: {'; '.join(thieu[:3])} (xuất lại Word)")
        if _pmid(md) != _pmid(docx_chu):
            loi.append("K2 bản Word không khớp bản .md — tập PMID khác nhau (xuất lại Word)")

    tat_ca_de_muc = " | ".join(_chuan(dm) for _, dm in de_muc)
    tk = _thiet_ke(out_dir)
    for nhan, tu in CHUONG_BAT_BUOC:
        if tk in KHONG_CAN_DONG_Y and nhan.startswith("phụ lục bản thông tin"):
            continue
        if not any(t in tat_ca_de_muc for t in tu):
            loi.append(f"K3 thiếu chương/mục «{nhan}»")

    chuong = ""
    for so, dong in enumerate(md.splitlines(), 1):
        m = _DE_MUC_RE.match(dong)
        if m and len(m.group(1)) == 1:
            chuong = _chuan(m.group(2))
        sach = G10._DOI_URL_RE.sub(" ", dong)
        for bt, nhan in _KY_HIEU_NOI_BO:
            # 19/11/2026: «G4 (eGFR 15–29)» là giai đoạn eGFR theo KDIGO, không phải mã cổng — chỉ miễn khi chính dòng
            # đó nói eGFR (khung biểu bảng luôn ghi kèm khoảng eGFR cho các mức G1–G5).
            if nhan == "mã cổng G0/G4–G10" and re.search(r"eGFR", sach):
                continue
            if bt.search(sach):
                loi.append(f"K4 dòng {so}: {nhan}")
                break
        if not chuong.startswith("PHỤ LỤC") and not dong.lstrip().startswith("|"):
            ten = _TEN_BIEN_RE.findall(sach)
            if ten:
                loi.append(f"K4 dòng {so}: tên biến trong văn xuôi ({', '.join(ten[:2])}) — dồn về bảng/phụ lục")

    try:
        g3 = json.loads((out_dir / "G3_checkpoint.json").read_text(encoding="utf-8"))
        n = g3.get("confirmed_n") if g3.get("confirmed_n") not in (None, "") else g3.get("n_adjusted")
        n = int(n)
    except (OSError, ValueError, TypeError, AttributeError):
        n = None
    if n is None:
        loi.append("K5 không đọc được cỡ mẫu đã chốt từ G3_checkpoint.json — không đối chiếu được")
    elif not any(re.search(rf"(?<![\d.,]){re.escape(s)}(?![\d])", md) for s in _dinh_dang_n(n)):
        loi.append(f"K5 cỡ mẫu đã chốt ở G3 ({n}) không xuất hiện trong đề cương nộp")
    # F2 (16/10/2026, diễn tập C1a): đề cương nộp dùng DE 1,78 / N tối thiểu 808 (có hệ số biến thiên cỡ cụm) trong khi
    # G3 ghi DE 1,38 / 626 — K5 cũ chỉ so N chốt nên không thấy. Nay DE và N tối thiểu của G3 cũng phải có mặt.
    if n is not None:
        de = g3.get("design_effect") if isinstance(g3, dict) else None
        n_min = g3.get("n_adjusted") if isinstance(g3, dict) else None
        if isinstance(de, (int, float)) and float(de) > 1:
            dang = {f"{float(de):.2f}", f"{float(de):.2f}".replace(".", ",")}
            if not any(re.search(rf"(?<![\d.,]){re.escape(x)}(?![\d])", md) for x in dang):
                loi.append(f"K5 hiệu ứng thiết kế G3 (DE {float(de):.2f}) không xuất hiện trong đề cương nộp — "
                           "đề cương dùng con số khác G3? Đồng bộ hai bên (chạy lại G3 hoặc sửa đề cương)")
        if isinstance(n_min, (int, float)) and int(n_min) != n:
            if not any(re.search(rf"(?<![\d.,]){re.escape(x)}(?![\d])", md) for x in _dinh_dang_n(int(n_min))):
                loi.append(f"K5 cỡ mẫu tối thiểu G3 ({int(n_min)}) không xuất hiện trong đề cương nộp")

    pm = _pmid(md)
    if pm:
        try:
            rc = json.loads((out_dir / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))
            da_kiem = {str(x) for x in rc.get("pmids_checked") or []}
            sach_rc = rc.get("all_clean") is True
        except (OSError, ValueError, AttributeError):
            da_kiem, sach_rc = set(), False
        chua = sorted(pm - da_kiem)
        if chua:
            loi.append(f"K6 {len(chua)} PMID chưa có trong biên nhận A12: {', '.join(chua[:6])} — chạy "
                       "check_citations.py --study với hợp PMID của bản lắp và bản nộp")
        elif not sach_rc:
            loi.append("K6 biên nhận A12 chưa ghi all_clean=true")

    for so, dong in enumerate(md.splitlines(), 1):
        if G10._PLACEHOLDER_RE.search(dong):
            loi.append(f"K7 dòng {so}: nhãn ô trống [CẦN…]/<…>")
    loi.extend(loi_k8(md))
    loi.extend(loi_k9(out_dir, md, tk))
    loi.extend(loi_k10(md))
    loi.extend(loi_k11(md))
    if G10._co_lien_lac_ca_nhan(md) or (docx_chu is not None and G10._co_lien_lac_ca_nhan(docx_chu)):
        loi.append("K7 có email/số điện thoại — PII liên lạc để dòng chấm cho PI điền tay ngoài hệ thống")
    return loi


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Kiểm bản đề cương nộp Hội đồng (G10-T4).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    loi = kiem(out_dir, a.study)
    ket: Dict[str, Any] = {"study": a.study, "dat": not loi, "loi": loi}
    if a.json:
        print(json.dumps(ket, ensure_ascii=False, indent=2))
    else:
        print(f"Đề cương nộp Hội đồng — {a.study}: {'ĐẠT' if not loi else f'{len(loi)} lỗi'}")
        for d in loi:
            print(f"  ✗ {d}")
        print("Cần bác sĩ kiểm chứng.")
    if loi and loi[0].startswith("K1 chưa có"):
        return 2
    return 0 if not loi else 1


if __name__ == "__main__":
    raise SystemExit(main())
