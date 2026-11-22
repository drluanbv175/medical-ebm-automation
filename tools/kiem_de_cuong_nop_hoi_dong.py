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
  K12 mỗi tài liệu tham khảo đỡ một câu cụ thể (bác sĩ 20/11/2026, phản biện BTM O13): không ngoặc trích gộp từ 6 tài
      liệu trở lên, không mục danh mục nào không được trích.
  K13 mục có PMID đúng Vancouver/NLM theo metadata biên nhận A12 (O14): hơn 6 tác giả ⇒ 6 tác giả rồi «et al.»,
      «năm;tập(số):trang», tên tạp chí viết tắt NLM. Biên nhận cũ chưa có các khoá này ⇒ bỏ qua.
  K14 (chỉ khi đề cương đã theo khuôn «Hướng dẫn viết đăng ký và báo cáo đề tài KH&CN cấp bệnh viện» — có
      «# CHƯƠNG 1.»; chuyển: `khuon_de_cuong_bvqy175.py`): đủ và đúng thứ tự cấu trúc mục II (danh sách cán bộ · mục lục
      · danh mục chữ viết tắt · danh mục bảng, biểu · đặt vấn đề · Chương 1–3 · tài liệu tham khảo · phụ lục); bìa có
      «ĐỀ CƯƠNG NGHIÊN CỨU», «Phiên bản đề cương: …, ngày …», «Địa danh, năm», bìa phụ có chữ ký Chủ nhiệm đề tài và
      Chủ nhiệm khoa; mục tiêu ở cuối đặt
      vấn đề, đánh số, in nghiêng đậm, tên đề tài trong ngoặc kép in đậm; tài liệu tham khảo xếp tiếng Việt trước rồi
      ngoại ngữ, mỗi nhóm theo ABC (tác giả Việt theo tên, nước ngoài theo họ, cơ quan theo chữ đầu), đánh số liền, ít
      nhất 50% xuất bản trong 10 năm; danh mục bảng, biểu khớp đúng tên bảng/hình có trong thân bài.
  K15 (21/11/2026): trong đặt vấn đề/tổng quan/bàn luận, mệnh đề mang từ khái quát hay định lượng mơ hồ («phần lớn»,
      «đa số», «thường gặp», «đã được chứng minh»…) phải tự mang trích dẫn — không thì viết bằng số đếm có nguồn.
  Số liệu ↔ toàn văn của đúng tài liệu được dẫn là phép TƯ VẤN riêng: `tools/kiem_so_lieu_toan_van.py --study <mã>`.
  K17 (21/11/2026; mọi đề cương nộp, cả bản nháp cấu trúc cũ): đủ yếu tố từng mục phương pháp/kế hoạch của mọi chuẩn
      áp dụng cho thiết kế — STROBE 2007, RECORD 2015 (dữ liệu thường quy), CROSS 2021 (khảo sát), chuẩn Việt Nam
      (TT43/2024, Luật 91/2025); dòng còn ô trống «………» không tính là có yếu tố. Đo chi tiết:
      `kiem_chuan_de_cuong_theo_muc.py --study <mã> [--chi-tiet]`.

Lệnh:  python3 tools/kiem_de_cuong_nop_hoi_dong.py --study <mã> [--json]
Mã thoát: 0 đạt · 1 có lỗi · 2 thiếu tệp đề cương nộp.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
# 22/11/2026 (đo thật, Hội đồng Khoa học máy QC-HDKH-2.0 trên C1a): «diễn giải tỷ số chênh theo độ lớn và khoảng tin cậy
# 95%» trong «Dự kiến bàn luận» bị K10 coi là số liệu không nguồn ⇒ bản bổ sung bàn luận mục tiêu 2 bị loại hai lần. Mức
# tin cậy/mức ý nghĩa là QUY ƯỚC PHƯƠNG PHÁP, không phải kết quả nghiên cứu. Chỉ bỏ cụm quy ước khi KHÔNG có cận số theo
# sau — «KTC 95%: 0,28–0,98», «khoảng tin cậy 95% (1,1–2,3)» vẫn là kết quả và vẫn phải có nguồn.
_QUY_UOC_MUC_RE = re.compile(
    r"(?:khoảng tin cậy|KTC|độ tin cậy|mức tin cậy|mức ý nghĩa)\s*(?:là\s*)?\d+(?:[.,]\d+)?\s?%"
    r"(?!\s*[:=]?\s*\(?\s*\d)"
    r"|\b\d+(?:[.,]\d+)?\s?%\s*CI\b(?!\s*[:=]?\s*\(?\s*\d)", re.I)
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
            # khuôn hướng dẫn chung: «CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN» — chỉ phần «Dự kiến bàn luận» là bàn
            # luận; phần dự kiến kết quả (khung bảng, câu mô tả chỉ số) không phải câu dẫn chứng cứ
            cap[k] = bool(_PHAN_CHUNG_CU_RE.search(m.group(2))) and not (
                k == 1 and "DỰ KIẾN KẾT QUẢ" in m.group(2).upper())
            trong = any(cap.values())
            continue
        s = dong.strip()
        if not trong or not s or s.startswith(("|", "!", "```", ">", "<!--")):
            continue
        for cau in _HET_CAU_RE.split(s):
            for md_ in _menh_de(cau):
                if _SO_KET_QUA_RE.search(_QUY_UOC_MUC_RE.sub(" ", md_)) and not _TRICH_DAN_RE.search(md_):
                    loi.append(f"K10 dòng {so}: số liệu không có trích dẫn trong cùng mệnh đề — «{md_[:90]}» "
                               "(không có nguồn thật trong danh mục ⇒ loại con số)")
    return loi


# K15 (bác sĩ 21/11/2026: «các lớp kiểm phải nghiêm ngặt từng câu từng chữ … tất cả đều phải dựa trên chứng cứ có độ
# tin cậy cao không được trình bày chung chung, sơ xài»). Đo trên hai đề cương thật: «phần lớn nghiên cứu trong nước đo
# thời gian chờ bằng tự báo cáo…», «thiết kế chặt chẽ hơn mức thường gặp…», «gần như toàn bộ là nghiên cứu quan sát…,
# chủ yếu ở Âu – Mỹ – Úc», «SGLT2i có lợi ích đã được chứng minh…» (mệnh đề chưa tự mang [n]) — khái quát/định lượng
# mơ hồ không nguồn mà K10 (chỉ bắt CON SỐ) bỏ lọt. Mỗi mệnh đề mang từ định lượng/khái quát mơ hồ phải tự mang
# trích dẫn — hoặc viết lại bằng số đếm/ví dụ cụ thể có nguồn.
_MO_HO_RE = re.compile(
    r"(?<![\wÀ-ỹ])(nhiều nghiên cứu|nhiều tác giả|nhiều bằng chứng|các nghiên cứu (?:cho thấy|đều)|y văn (?:cho thấy|"
    r"ghi nhận)|phần lớn|đa số|hầu hết|gần như toàn bộ|một số nghiên cứu|thường gặp|khá cao|rất cao|rất thấp|đáng kể|"
    r"ngày càng|đã được chứng minh|nhiều người|nhiều bệnh nhân|thường (?:được|liên quan|do|xảy ra|kéo dài)|"
    # 22/11/2026: «đã được nghiên cứu nhiều» ở mục khoảng trống của cả hai đề cương thật lọt K15
    r"(?:được )?nghiên cứu nhiều|(?:được )?(?:sử dụng|dùng|áp dụng) rộng rãi)"
    r"(?![\wÀ-ỹ])", re.I)
_CHU_THICH_BB = ("**Bảng", "**Hình", "**Biểu đồ", "**Sơ đồ")


def loi_k15(md: str) -> List[str]:
    """K15 — trong đặt vấn đề / tổng quan / bàn luận, MỖI mệnh đề mang từ khái quát hoặc định lượng mơ hồ («phần lớn»,
    «đa số», «thường gặp», «đã được chứng minh»…) phải tự mang trích dẫn [n]; không có nguồn ⇒ viết lại bằng số đếm hay
    ví dụ cụ thể có nguồn. Tên bảng/hình không xét. Cùng vùng và cùng cách tách mệnh đề với K10."""
    loi: List[str] = []
    cap: Dict[int, bool] = {}
    trong = False
    for so, dong in enumerate(md.splitlines(), 1):
        m = _DE_MUC_RE.match(dong)
        if m:
            k = len(m.group(1))
            cap = {c: v for c, v in cap.items() if c < k}
            cap[k] = bool(_PHAN_CHUNG_CU_RE.search(m.group(2))) and not (
                k == 1 and "DỰ KIẾN KẾT QUẢ" in m.group(2).upper())
            trong = any(cap.values())
            continue
        s = dong.strip()
        if not trong or not s or s.startswith(("|", "!", "```", ">", "<!--") + _CHU_THICH_BB):
            continue
        for cau in _HET_CAU_RE.split(s):
            for md_ in _menh_de(cau):
                mm = _MO_HO_RE.search(md_)
                if mm and not _TRICH_DAN_RE.search(md_):
                    loi.append(f"K15 dòng {so}: «{mm.group(0)}» không có trích dẫn trong cùng mệnh đề — «{md_[:90]}» "
                               "(viết lại bằng số đếm/ví dụ cụ thể có nguồn, hoặc gắn nguồn [n] ngay tại mệnh đề)")
    return loi


# K16 (21/11/2026): bài báo giao thức C1a (bản cũ) khẳng định đã rà «Google Scholar … thư viện luận văn … kỷ yếu» trong
# khi nhật ký PRISMA-S của chính đề tài ghi các nguồn đó «KHÔNG tra» — khẳng định một lượt tìm chưa làm là lỗi liêm
# chính mà không chốt nào bắt. Nguồn khó kiểm được nêu như ĐÃ tra (mệnh đề không có «chưa/không») phải có trong phần
# ĐÃ tra của `G0_TIM_BO_SUNG_PRISMA_S_<mã>.md`; không có nhật ký ⇒ không kết luận (không phải «đạt»).
_NGUON_KHO_KIEM = ("Google Scholar", "luận văn", "luận án", "kỷ yếu", "Scopus", "Web of Science", "ProQuest", "Embase")
_PHU_DINH_RE = re.compile(r"(?<![\wÀ-ỹ])(?:chưa|không)(?![\wÀ-ỹ])", re.I)
_DONG_TU_TRA_RE = re.compile(r"(?<![\wÀ-ỹ])(?:tra|tìm|rà|tham khảo|truy vấn|search)", re.I)


def nhat_ky_prisma_s(out_dir: Path) -> Optional[Tuple[str, str]]:
    """(phần ĐÃ tra, phần KHÔNG tra) của nhật ký PRISMA-S đề tài; không có tệp ⇒ None."""
    ds = sorted(Path(out_dir).glob("G0_TIM_BO_SUNG_PRISMA_S_*.md"))
    if not ds:
        return None
    van = ds[0].read_text(encoding="utf-8")
    m = re.search(r"^#{1,3}[^\n]*KHÔNG tra[^\n]*\n(.*?)(?=^#{1,3} |\Z)", van, re.M | re.S)
    khong = m.group(1) if m else ""
    con = van.replace(m.group(0), "") if m else van
    # dòng nhắc nguồn kèm «chưa/không» (vd «y văn không có DOI (luận văn, kỷ yếu) chưa tra») KHÔNG là bằng chứng đã tra
    da_tra = "\n".join(x for x in con.splitlines() if not _PHU_DINH_RE.search(x))
    return da_tra, khong


def loi_k16(out_dir: Path, md: str) -> List[str]:
    """K16 — câu nêu ĐÃ tra một nguồn khó kiểm phải khớp nhật ký PRISMA-S (nguồn có trong phần đã tra)."""
    nk = nhat_ky_prisma_s(out_dir)
    if nk is None:
        return []
    da_tra, _khong = nk
    loi: List[str] = []
    for so, dong in enumerate(md.splitlines(), 1):
        s = dong.strip()
        if not s or s.startswith(("#", "|", "<!--")):
            continue
        for cau in _HET_CAU_RE.split(s):
            for md_ in _menh_de(cau):
                if _PHU_DINH_RE.search(md_) or not _DONG_TU_TRA_RE.search(md_):
                    continue
                for ng in _NGUON_KHO_KIEM:
                    if ng.lower() in md_.lower() and ng.lower() not in da_tra.lower():
                        loi.append(f"K16 dòng {so}: nêu đã tra «{ng}» nhưng nhật ký PRISMA-S của đề tài không ghi lượt "
                                   f"tra nguồn này — «{md_[:90]}» (sửa câu cho khớp nhật ký, hoặc tra thật rồi ghi "
                                   "nhật ký)")
    return loi


# K11 (bác sĩ 20/11/2026: «từng câu, từng chữ, ngữ nghĩa phải chuẩn, từng bảng từng đồ thị phải đúng chuẩn, đúng định
# dạng»). Soát tay đề cương BTM/C1a gặp lặp lại: số kiểu máy (0.1; 100000; 2026-01-01), ngoặc kép thẳng/«», hai mục
# viết tắt cùng nghĩa (SD và ĐLC), mục viết tắt không dùng, bảng viết tắt không theo vần, loại biến «Định danh/thứ bậc»,
# tên bảng hai ngoặc liền «(…) (Mục tiêu 3)», «vs», chữ IN HOA nhấn mạnh trong câu («ước lượng CAO»).
_SO_THAP_PHAN_MAY_RE = re.compile(r"(?<![\w.,])0\.\d+(?![\d.])")
_SO_LON_MAY_RE = re.compile(r"(?<![\w.,/-])\d{5,}(?![\w.,/-])")
_NGAY_ISO_RE = re.compile(r"(?<![\w-])(?:19|20)\d{2}-[01]\d-[0-3]\d(?![\w-])")
_NGOAC_KEP_RE = re.compile(r"[«»]|\"[^\"\n]{1,200}\"")
_NGU_CANH_MA_RE = re.compile(r"(?:seed|hạt giống|mã|ID|ISSN|NCT|số hiệu|số)\s*[:=]?\s*$", re.I)
_VS_RE = re.compile(r"(?<![\wÀ-ỹ])vs\.?(?![\wÀ-ỹ])")
_IN_HOA_NHAN_RE = re.compile(r"(?<![\wÀ-ỹ])(?:CAO|THẤP|KHÔNG|CHỈ|MỌI|PHẢI|LUÔN|TĂNG|GIẢM|ĐÚNG|SAI)(?![\wÀ-ỹ])")
_TIM_KIEM_RE = re.compile(r"\[(?:Mesh|tiab|pt|ti|tw|majr|dp)\]", re.I)
_TEN_BB_HAI_NGOAC_RE = re.compile(r"^\*\*(?:Bảng|Hình|Biểu đồ) [0-9A-Z]+\.\d+\..*\)\s*\(")


# Chiều ngược của bảng viết tắt (21/11/2026 — phản biện máy C1a, bác sĩ chọn sửa trước khi PI ký G10): danh mục có
# STROBE, COSMIN, CROSS, RECORD mà vắng AGReMA dùng ở §4.8. Chỉ xét tên CHUẨN BÁO CÁO/THẨM ĐỊNH viết tắt (cùng loại, đã
# quen liệt kê trong danh mục) — không xét mọi cụm in hoa (mã biến G1/C6, tên phần mềm REDCap/eHospital là tên riêng).
_CHUAN_VIET_TAT = (
    "AGReMA", "AGREE", "AMSTAR", "CARE", "CHEERS", "CONSORT", "COREQ", "COSMIN", "CROSS", "GRADE", "GRIPP2", "MOOSE",
    "PRISMA", "PRISMA-P", "PROBAST", "QUADAS", "RECORD", "ROBINS-I", "SPIRIT", "SQUIRE", "SRQR", "STARD", "STROBE",
    "TIDieR", "TRIPOD",
)


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
    cot_nguyen_van: set = set()
    dong_than: List[Tuple[int, str]] = []  # dòng thân bài (ngoài danh mục viết tắt, TLTK, mã)
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
        dong_than.append((so, re.sub(r"`[^`]*`", " ", d)))
        # 20/11/2026: cột bảng khai «(nguyên văn)» — vd «Tên bài (nguyên văn)» của bảng tài liệu ở chương tổng quan —
        # giữ đúng chữ của nguồn như danh mục tài liệu tham khảo (tiêu đề tiếng Anh dùng «vs», số không nhóm nghìn).
        if d.startswith("|"):
            o = d.strip().strip("|").split("|")
            if so < len(dong) and re.match(r"^\|[-\s|:]+\|$", dong[so].strip()):
                cot_nguyen_van = {i for i, x in enumerate(o) if "nguyên văn" in x.lower()}
            elif cot_nguyen_van and not re.match(r"^\|[-\s|:]+\|$", d.strip()):
                d = "|" + "|".join(" " if i in cot_nguyen_van else x for i, x in enumerate(o)) + "|"
        else:
            cot_nguyen_van = set()
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
            # Số định danh không phải số đếm («seed 20261115», «mã 40062», «Quyết định số 3869») — không nhóm nghìn.
            while hit and bt is _SO_LON_MAY_RE and _NGU_CANH_MA_RE.search(s[max(0, hit.start() - 25):hit.start()]):
                hit = bt.search(s, hit.end())
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
        co_vt = {re.split(r"[,\s±]+", k)[0] for k in vt}
        for ten in _CHUAN_VIET_TAT:
            if ten in co_vt:
                continue
            mau = re.compile(rf"(?<![\wÀ-ỹ-]){re.escape(ten)}(?![\wÀ-ỹ-])")  # cùng ranh giới với bộ sinh
            so_dau = next((so for so, d in dong_than if mau.search(d)), None)
            if so_dau:
                loi.append(f"K11 bảng chữ viết tắt: «{ten}» dùng ở dòng {so_dau} mà danh mục thiếu — bổ sung mục này")
        if list(vt) != sorted(vt, key=_khoa_van_viet):
            loi.append("K11 bảng chữ viết tắt chưa xếp theo bảng chữ cái tiếng Việt")
    return loi


_TLTK_DE_MUC_RE = re.compile(r"^#{1,3}\s*(?:\d+\.?\s*)?TÀI LIỆU THAM KHẢO\s*$", re.M)
_TRICH_SO_RE = re.compile(r"\[(\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–-]\s*\d+)?)*)\]")
_MUC_TLTK_RE = re.compile(r"^(\d+)\.\s+(.+)$")
TRAN_KHOI_GOP = 6  # một ngoặc trích từ 6 tài liệu trở lên ⇒ khối gộp


def _mo_rong_trich(s: str) -> List[int]:
    """«3–5, 9» ⇒ [3, 4, 5, 9]."""
    ra: List[int] = []
    for phan in s.split(","):
        phan = phan.strip().replace("–", "-")
        if "-" in phan:
            a, b = (int(x) for x in phan.split("-", 1))
            ra.extend(range(a, b + 1) if b >= a else [a, b])
        elif phan.isdigit():
            ra.append(int(phan))
    return ra


def _tach_tltk(md: str) -> tuple:
    """(dòng ngoài danh mục TLTK kèm số dòng, {số: nội dung mục TLTK}). Danh mục kết thúc ở đề mục cấp 1 kế tiếp."""
    ngoai: List[tuple] = []
    muc: Dict[int, str] = {}
    trong = False
    for so, dong in enumerate(md.splitlines(), 1):
        if _TLTK_DE_MUC_RE.match(dong):
            trong = True
            continue
        if trong and re.match(r"^#\s", dong):
            trong = False
        if trong:
            m = _MUC_TLTK_RE.match(dong.strip())
            if m:
                muc[int(m.group(1))] = m.group(2)
            continue
        ngoai.append((so, dong))
    return ngoai, muc


def loi_k12(md: str) -> List[str]:
    """K12 — mỗi tài liệu tham khảo phải đỡ một câu cụ thể (bác sĩ 20/11/2026, phản biện đề cương BTM mục O13).

    Lỗi khi (a) một ngoặc trích dẫn gộp từ `TRAN_KHOI_GOP` tài liệu trở lên — kiểu «các tài liệu khác được tham khảo khi
    xây dựng đề cương [15–36]», Hội đồng và tạp chí coi là trích dẫn độn; (b) một mục trong danh mục không được trích ở
    đâu trong thân bài và phụ lục. Tài liệu không đỡ câu nào thì bỏ khỏi danh mục."""
    ngoai, muc = _tach_tltk(md)
    loi: List[str] = []
    da_trich: set = set()
    for so, dong in ngoai:
        for m in _TRICH_SO_RE.finditer(dong):
            ds = _mo_rong_trich(m.group(1))
            da_trich.update(ds)
            if len(set(ds)) >= TRAN_KHOI_GOP:
                loi.append(f"K12 dòng {so}: khối trích dẫn gộp [{m.group(1)}] ({len(set(ds))} tài liệu) — mỗi tài liệu "
                           "phải đỡ một câu cụ thể; tài liệu không đỡ câu nào thì bỏ khỏi danh mục")
    thua = sorted(set(muc) - da_trich)
    if thua:
        loi.append(f"K12 {len(thua)} mục tài liệu tham khảo không được trích ở đâu: "
                   f"{', '.join(map(str, thua[:10]))} — gắn vào câu mà tài liệu đỡ hoặc bỏ khỏi danh mục")
    return loi


def loi_k13(out_dir: Path, md: str) -> List[str]:
    """K13 — mục tài liệu tham khảo có PMID khớp metadata PubMed của biên nhận A12 theo Vancouver/NLM (20/11/2026,
    phản biện BTM mục O14: tác giả cắt ở 5 người không có «et al.», thiếu tập/số/trang, tên tạp chí không viết tắt).

    Chỉ kiểm khoá mà biên nhận CÓ (`n_authors`/`authors_6`, `volume`, `journal_abbr` — biên nhận từ 20/11/2026); biên
    nhận cũ không có thì bỏ qua (dựng lại biên nhận: `check_citations.py --study <mã>`). Luật: có hơn 6 tác giả ⇒ mục
    ghi 6 tác giả đầu rồi «et al.»; từ 6 tác giả trở xuống ⇒ ghi đủ, không «et al.»; có tập ⇒ có «năm;tập»; có tên
    tạp chí viết tắt NLM ⇒ mục dùng đúng tên đó. Quy tắc 6 tác giả chỉ đếm tác giả CÁ NHÂN; tác giả TẬP THỂ
    (`nhom_tac_gia`) phải có mặt, ghi sau tác giả cá nhân, ngăn bằng «;» (NLM)."""
    _, muc = _tach_tltk(md)
    try:
        meta = json.loads((Path(out_dir) / "A12_METADATA_RECEIPT.json").read_text(encoding="utf-8")).get("metadata")
    except (OSError, ValueError, AttributeError):
        return []
    if not isinstance(meta, dict):
        return []
    loi: List[str] = []
    for so, noi_dung in sorted(muc.items()):
        pm = re.search(r"PMID:\s*(\d+)", noi_dung)
        m = meta.get(pm.group(1)) if pm else None
        if not isinstance(m, dict) or m.get("status") != "resolved":
            continue
        sai: List[str] = []
        # `n_authors`/`authors_6` = tác giả CÁ NHÂN; `nhom_tac_gia` = tác giả TẬP THỂ (ghi sau, ngăn «;» — NLM, không
        # tính vào quy tắc 6 tác giả). Dấu chú thích «*» PubMed gắn vào tên bị bỏ khi so.
        tong, sau = m.get("n_authors"), m.get("authors_6")
        if isinstance(tong, int) and isinstance(sau, list) and sau and tong > 0:
            co_et_al = re.search(r"\bet al\b", noi_dung) is not None
            cuoi = str(sau[min(tong, 6) - 1]).rstrip("*").strip()
            if tong > 6 and not co_et_al:
                sai.append(f"bài có {tong} tác giả cá nhân — ghi 6 tác giả đầu rồi «et al.»")
            elif tong <= 6 and co_et_al:
                sai.append(f"bài có {tong} tác giả cá nhân — ghi đủ, không «et al.»")
            if cuoi and cuoi not in noi_dung:
                sai.append(f"thiếu tác giả thứ {min(tong, 6)} «{cuoi}»")
        for nhom in m.get("nhom_tac_gia") or []:
            nhom = str(nhom).rstrip("*").strip()
            if nhom and nhom not in noi_dung:
                sai.append(f"thiếu tác giả tập thể «{nhom}»")
        nam = str(m.get("year") or "")[:4]
        if m.get("volume") and nam and f"{nam};{m['volume']}" not in noi_dung:
            sai.append(f"thiếu «{nam};{m['volume']}…» (năm;tập(số):trang)")
        if m.get("journal_abbr") and str(m["journal_abbr"]) not in noi_dung:
            sai.append(f"tên tạp chí viết tắt NLM là «{m['journal_abbr']}»")
        if sai:
            loi.append(f"K13 TLTK [{so}] (PMID {pm.group(1)}): " + "; ".join(sai))
    return loi


# K14 (21/11/2026 — bác sĩ gửi hướng dẫn chung kèm bộ mẫu BVQY175, chọn áp sát hướng dẫn). Thứ tự đề mục cấp 1 theo
# mục II «Cấu trúc theo quy định»; mẫu so trên đề mục đã chuẩn hoá (in hoa, bỏ dấu nhấn mạnh).
KHUON_THU_TU = (
    ("danh sách cán bộ tham gia thực hiện đề tài", r"^DANH SÁCH CÁC CÁN BỘ"),
    ("mục lục", r"^MỤC LỤC$"),
    ("danh mục các chữ viết tắt", r"^DANH MỤC CÁC CHỮ VIẾT TẮT"),
    ("danh mục các bảng, biểu", r"^DANH MỤC CÁC BẢNG"),
    ("đặt vấn đề", r"^ĐẶT VẤN ĐỀ$"),
    ("Chương 1. Tổng quan tài liệu", r"^CHƯƠNG 1\.\s+TỔNG QUAN"),
    ("Chương 2. Đối tượng và phương pháp nghiên cứu", r"^CHƯƠNG 2\.\s+ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP"),
    ("Chương 3. Dự kiến kết quả và bàn luận", r"^CHƯƠNG 3\.\s+DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN"),
    ("tài liệu tham khảo", r"^TÀI LIỆU THAM KHẢO$"),
    ("phụ lục", r"^PHỤ LỤC"),
)
NGUONG_10_NAM = 0.5  # hướng dẫn chung mục II.9: «Ít nhất phải có 50% tài liệu tham khảo được xuất bản trong 10 năm»
_DIA_DANH_NAM_RE = re.compile(r"^\*\*[^*\n]+,\s*((?:19|20)\d{2})\*\*\s*$", re.M)
_CHU_THICH_KHUON_RE = re.compile(r"^\*\*(Bảng|Hình|Biểu đồ|Sơ đồ)\s+([0-9A-Z]+\.\d+)\.\s")
_NAM_TAP_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})\s*;")
_NAM_RE = re.compile(r"(?<![\d/])((?:19|20)\d{2})(?![\d/])")


def _nam_xuat_ban(muc: str) -> Optional[int]:
    """Năm xuất bản của một mục: «năm;tập» (bài báo Vancouver); không có thì năm cuối cùng đứng trước DOI/URL/PMID."""
    m = _NAM_TAP_RE.search(muc)
    if m:
        return int(m.group(1))
    truoc = re.split(r"doi:|https?://|PMID", muc, maxsplit=1)[0]
    ds = _NAM_RE.findall(truoc)
    return int(ds[-1]) if ds else None


def loi_k14(md: str, nam: Optional[int] = None) -> List[str]:
    """K14 — đề cương đã theo khuôn hướng dẫn chung (có «# CHƯƠNG 1.») phải đúng cấu trúc và trình bày của khuôn.
    Đề cương cấu trúc cũ ⇒ bỏ qua (rỗng). `nam` = năm của đề cương (mặc định lấy ở dòng «Địa danh, năm» của bìa)."""
    if not re.search(r"^# CHƯƠNG 1\.", md, re.M):
        return []
    import khuon_de_cuong_bvqy175 as KDC  # noqa: PLC0415 — tránh nạp vòng (bộ chuyển khuôn gọi bộ kiểm này)

    loi: List[str] = []
    dong = md.splitlines()
    h1 = [(so, _chuan(d[2:])) for so, d in enumerate(dong, 1) if re.match(r"^#\s", d)]
    vi_tri: List[Tuple[str, int]] = []
    for nhan, mau in KHUON_THU_TU:
        i = next((k for k, (_so, t) in enumerate(h1) if re.search(mau, t)), None)
        if i is None:
            loi.append(f"K14 thiếu phần «{nhan}» (hướng dẫn chung mục II — cấu trúc theo quy định)")
        else:
            vi_tri.append((nhan, i))
    for (n1, i1), (n2, i2) in zip(vi_tri, vi_tri[1:]):
        if i2 < i1:
            loi.append(f"K14 «{n2}» đứng trước «{n1}» — sai thứ tự cấu trúc của hướng dẫn chung")
    # bìa + bìa phụ (phụ lục 6, 7 của hướng dẫn)
    dau_h1 = h1[0][0] - 1 if h1 else len(dong)
    bia = "\n".join(dong[:dau_h1])
    bia_chuan = _chuan(bia)
    if "ĐỀ CƯƠNG NGHIÊN CỨU" not in bia_chuan:
        loi.append("K14 bìa thiếu dòng «ĐỀ CƯƠNG NGHIÊN CỨU ĐỀ TÀI KHOA HỌC VÀ CÔNG NGHỆ CẤP BỆNH VIỆN»")
    nam_bia = _DIA_DANH_NAM_RE.findall(bia)
    if not nam_bia:
        loi.append("K14 bìa thiếu dòng «Địa danh, năm» (in đậm)")
    if not re.search(r"^\**\s*Phiên bản đề cương\s*:", bia, re.M | re.I):
        loi.append("K14 bìa thiếu dòng «Phiên bản đề cương: …, ngày …» (Hội đồng đòi trên mọi tài liệu nộp)")
    if bia_chuan.count("CHỦ NHIỆM ĐỀ TÀI") < 2 or "CHỦ NHIỆM KHOA" not in bia_chuan:
        loi.append("K14 bìa phụ thiếu khối họ tên và chữ ký của Chủ nhiệm đề tài và Chủ nhiệm khoa")
    if nam is None:
        nam = int(nam_bia[-1]) if nam_bia else datetime.now().year
    # đặt vấn đề: tên đề tài trong ngoặc kép in đậm; mục tiêu ở cuối, đánh số, in nghiêng đậm
    i_dvd = next((so for so, t in h1 if t == "ĐẶT VẤN ĐỀ"), None)
    if i_dvd is not None:
        het = next((so for so, _t in h1 if so > i_dvd), len(dong) + 1)
        dvd = dong[i_dvd:het - 1]
        if not any(re.search(r"“\*\*.+?\*\*”", d) for d in dvd):
            loi.append("K14 đặt vấn đề chưa ghi tên đề tài trong ngoặc kép, in đậm (“**…**”)")
        i_mt = next((k for k, d in enumerate(dvd) if re.match(r"^##\s+MỤC TIÊU", d)), None)
        if i_mt is None:
            loi.append("K14 mục tiêu nghiên cứu phải viết ở cuối phần đặt vấn đề (đề mục «MỤC TIÊU NGHIÊN CỨU»)")
        else:
            muc_tieu = [d for d in dvd[i_mt + 1:] if re.match(r"^\d+\.\s", d)]
            if not muc_tieu:
                loi.append("K14 mục tiêu nghiên cứu chưa đánh số thứ tự")
            for d in muc_tieu:
                if not re.match(r"^\d+\.\s+\*\*\*.+\*\*\*\s*$", d):
                    loi.append(f"K14 mục tiêu «{d[:50]}» chưa in nghiêng, đậm")
                    break
    # tài liệu tham khảo: theo ngôn ngữ, ABC, số liền, ≥ 50% trong 10 năm
    _ngoai, muc = _tach_tltk(md)
    if muc:
        so = sorted(muc)
        if so != list(range(1, len(so) + 1)):
            loi.append("K14 tài liệu tham khảo đánh số không liền từ 1")
        thu_tu = [muc[k] for k in so]
        la_viet = [KDC.la_tieng_viet(v) for v in thu_tu]
        if True in la_viet and False in la_viet and la_viet.index(False) < len(la_viet) - la_viet[::-1].index(True) - 1:
            loi.append("K14 tài liệu tham khảo chưa xếp riêng theo ngôn ngữ (tiếng Việt trước, tiếng nước ngoài sau)")
        else:
            for nhom in ([v for v, t in zip(thu_tu, la_viet) if t], [v for v, t in zip(thu_tu, la_viet) if not t]):
                khoa = [KDC.khoa_tac_gia(v) for v in nhom]
                sai = next((i for i in range(1, len(khoa)) if khoa[i] < khoa[i - 1]), None)
                if sai is not None:
                    loi.append(f"K14 tài liệu tham khảo chưa theo ABC: «{nhom[sai][:40]}» đứng sau "
                               f"«{nhom[sai - 1][:40]}»")
        nam_xb = [_nam_xuat_ban(v) for v in thu_tu]
        co_nam = [x for x in nam_xb if x]
        if co_nam:
            moi = sum(1 for x in co_nam if x >= nam - 9)
            if moi / len(co_nam) < NGUONG_10_NAM:
                loi.append(f"K14 chỉ {moi}/{len(co_nam)} tài liệu tham khảo xuất bản trong 10 năm ({nam - 9}–{nam}) "
                           "— hướng dẫn chung đòi ít nhất 50%")
    # danh mục bảng, biểu ↔ tên bảng/hình trong thân bài
    i_dm = next((so for so, t in h1 if t.startswith("DANH MỤC CÁC BẢNG")), None)
    if i_dm is not None:
        het = next((so for so, _t in h1 if so > i_dm), len(dong) + 1)
        dm = set()
        for d in dong[i_dm:het - 1]:
            m = re.match(r"^\|\s*((?:Bảng|Hình|Biểu đồ|Sơ đồ)\s+[0-9A-Z]+\.\d+)\s*\|", d)
            if m:
                dm.add(m.group(1))
        than = {f"{m.group(1)} {m.group(2)}" for d in dong[het - 1:] for m in [_CHU_THICH_KHUON_RE.match(d)] if m}
        thieu, thua = sorted(than - dm), sorted(dm - than)
        if thieu:
            loi.append(f"K14 danh mục bảng, biểu thiếu: {', '.join(thieu[:6])}")
        if thua:
            loi.append(f"K14 danh mục bảng, biểu có mục không thấy trong thân bài: {', '.join(thua[:6])}")
    return loi


def loi_k17(md: str, thiet_ke: str) -> List[str]:
    """K17 (21/11/2026, bác sĩ: «từng tiêu chuẩn trong từng cấu trúc đề cương phải đạt tiêu chuẩn», cho MỌI thiết kế) —
    đề cương nộp phải đủ yếu tố của từng mục phương pháp/kế hoạch của mọi chuẩn áp dụng: STROBE 2007 (quan sát), RECORD
    2015 (dữ liệu thường quy), CROSS 2021 (khảo sát bằng bộ câu hỏi), chuẩn Việt Nam (TT43/2024, Luật 91/2025),
    COSMIN 2021 (kiểm định bộ câu hỏi). Bộ đo ở `kiem_chuan_de_cuong_theo_muc.py`. Chuẩn đã có tiêu chí nhưng bộ sinh
    chưa phủ (SPIRIT, PRISMA-P, STARD, TRIPOD+AI, GRAMMS, SQUIRE, CHEERS, CARE — `KCM.CHUAN_CHO_BO_SINH`) và chuẩn
    chưa đối chiếu bảng gốc (TREND, COREQ, SRQR) chỉ CẢNH BÁO (`canh_bao_k17`, in ⚠ kèm) — không chặn, không tính là
    đạt.

    Chặn MỌI đề cương nộp, cả bản nháp cấu trúc cũ 1–7 (21/11/2026): trước đó chỉ chặn bản theo khuôn «# CHƯƠNG 1.»
    (cùng điều kiện K14) vì bộ sinh còn tạo đề cương thiếu ~50 mục chuẩn trên 8 giả lập; nay bộ sinh dựng từng mục từ
    quyết định đã chốt và 8 thiết kế giả lập đạt K17, nên bản nháp cũng phải đạt trước khi đến tay Hội đồng. Dòng còn ô
    trống «………» không làm bằng chứng cho yếu tố nào (`kiem_chuan_de_cuong_theo_muc.o_trong_quanh`)."""
    import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

    return KCM.loi_k17(md, thiet_ke)


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


def canh_bao_k17(out_dir: Path, study: str) -> List[str]:
    """Cảnh báo K17 không chặn nộp (chuẩn chờ bộ sinh phủ / chưa đối chiếu bảng gốc) — in kèm, không đổi mã thoát."""
    md_p = Path(out_dir) / (TEN.format(study=study) + ".md")
    md = _doc(md_p) if md_p.is_file() else None
    if md is None:
        return []
    import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

    return KCM.canh_bao_k17(md, _thiet_ke(Path(out_dir)))


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
    loi.extend(loi_k12(md))
    loi.extend(loi_k13(out_dir, md))
    loi.extend(loi_k14(md))
    loi.extend(loi_k15(md))
    loi.extend(loi_k16(out_dir, md))
    loi.extend(loi_k17(md, tk))
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
    canh = canh_bao_k17(out_dir, a.study)
    ket: Dict[str, Any] = {"study": a.study, "dat": not loi, "loi": loi, "canh_bao": canh}
    if a.json:
        print(json.dumps(ket, ensure_ascii=False, indent=2))
    else:
        print(f"Đề cương nộp Hội đồng — {a.study}: {'ĐẠT' if not loi else f'{len(loi)} lỗi'}")
        for d in loi:
            print(f"  ✗ {d}")
        for d in canh:
            print(f"  ⚠ {d}")
        print("Cần bác sĩ kiểm chứng.")
    if loi and loi[0].startswith("K1 chưa có"):
        return 2
    return 0 if not loi else 1


if __name__ == "__main__":
    raise SystemExit(main())
