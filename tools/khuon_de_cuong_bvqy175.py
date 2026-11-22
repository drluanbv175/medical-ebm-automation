#!/usr/bin/env python3
"""Chuyển ĐỀ CƯƠNG NỘP HỘI ĐỒNG sang khuôn «Hướng dẫn viết đăng ký và báo cáo đề tài KH&CN cấp bệnh viện» (BVQY175).

VÌ SAO (21/11/2026, bác sĩ gửi hướng dẫn chung kèm bộ mẫu BVQY175 và chọn: áp sát hướng dẫn; tài liệu tham khảo xếp theo
ngôn ngữ rồi ABC; trình bày Times New Roman 14, giãn dòng 1,5): đề cương nộp của hệ dựng theo cấu trúc «1. ĐẶT VẤN ĐỀ …
6. KẾ HOẠCH · 7. TÀI LIỆU» — lệch mục II của hướng dẫn (bìa, bìa phụ có chữ ký, danh sách cán bộ, mục lục, danh mục,
Đặt vấn đề kết thúc bằng mục tiêu, Chương 1 Tổng quan · Chương 2 Đối tượng và phương pháp · Chương 3 Dự kiến kết quả và
bàn luận, tài liệu tham khảo theo ngôn ngữ và ABC).

Công cụ CHỈ SẮP XẾP LẠI nội dung đã có — không viết lại câu chuyên môn, không thêm số liệu:
  - Bìa + bìa phụ (khối chữ ký Chủ nhiệm đề tài · Chủ nhiệm khoa · thủ trưởng đơn vị ngay trên Khoa — Viện trưởng hoặc
    Giám đốc Trung tâm — CHỈ khi hồ sơ khai Khoa thuộc Viện/Trung tâm; không chép lời hướng dẫn «— nếu …» của khuôn,
    22/11/2026); dòng cơ quan ở đầu tệp được giữ.
  - Danh sách cán bộ tham gia (vai trò lấy từ mục nhân lực; họ tên để dòng chấm), mục lục, danh mục chữ viết tắt (bảng
    cũ giữ nguyên), danh mục bảng/biểu đồ/hình.
  - Đặt vấn đề: tên đề tài trong ngoặc kép in đậm; bỏ danh sách mục tiêu lặp; «MỤC TIÊU NGHIÊN CỨU» (in nghiêng, đậm) ở
    cuối.
  - Chương 2 xếp theo thứ tự hướng dẫn: đối tượng → thời gian, địa điểm → thiết kế → câu hỏi và giả thuyết → cỡ mẫu và
    chọn mẫu → phương pháp nghiên cứu (công cụ, kỹ thuật thu thập, các bước tiến hành, chỉ tiêu, sai số, phân tích) →
    đạo đức; mục không nhận diện được giữ ở cuối chương (cảnh báo, không mất nội dung).
  - Chương 3 = dự kiến kết quả + «Dự kiến bàn luận» theo từng mục tiêu (khung câu chung + dòng chấm cho chủ nhiệm) +
    hạn chế (chuyển từ chương phương pháp).
  - Tài liệu tham khảo: tiếng Việt rồi tiếng Anh; tác giả Việt xếp theo TÊN (từ cuối), tác giả nước ngoài theo HỌ, cơ
    quan theo chữ đầu tên cơ quan; đánh số lại và thay MỌI trích dẫn [n] trong văn bản (cả ô bảng).
  - Đánh số lại mục (≤ 4 chữ số) và bảng/hình/biểu đồ theo chương (Bảng 2.3 = bảng thứ ba của chương 2); thay mọi tham
    chiếu «mục 4.4.1», «Bảng 4.7», «mục 3.3–3.4», «chương 5» trong văn bản. Kế hoạch thực hiện chuyển thành phụ lục kế
    tiếp.
  - Văn bản ĐÃ theo khuôn (có thể người đã sửa tiếp) không chuyển lại; chỉ qua `sua_ban_da_theo_khuon`: khối ký bìa phụ
    theo đơn vị thật, tham chiếu chương lạc trong câu nói về khung bảng ⇒ chương «Dự kiến kết quả» (22/11/2026).
  - «Tóm tắt» (không có trong khuôn) bị bỏ — nội dung đã có trong thân bài và trong mẫu thuyết minh DTCS-DKCT.02-TM
    (`ho_so_dtcs_bvqy175.py`); «Thông tin chung» (chủ nhiệm, đơn vị, thời gian, kinh phí, phiên bản) giữ nguyên thành
    phụ lục cuối; tên chủ nhiệm (nếu đã điền) lên bìa và danh sách cán bộ.

Ranh giới: chạy khô mặc định; `--ghi` sao lưu bản cũ vào `exports/<mã>/_sao_luu_de_cuong/` rồi ghi `.md` + `.docx`
(md2docx_vn khuôn BVQY175: 14pt, giãn 1,5, lề 3,5/2/3/3 cm, bìa không số trang, phần đầu số La Mã, từ Đặt vấn đề số Ả
rập). Đề cương đã khoá ở G10 ⇒ ghi xong gói G10 cũ, PI phải lắp và ký lại. Không ký, không sửa biên bản/sổ cái.

Lệnh:  python3 tools/khuon_de_cuong_bvqy175.py --study <mã> [--xem] [--json]      # chạy khô
       python3 tools/khuon_de_cuong_bvqy175.py --study <mã> --ghi
Mã thoát: 0 xong (kiểm K đạt) · 1 đã chuyển nhưng bộ kiểm đề cương còn lỗi · 2 thiếu đề cương · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import goi_bao_ve_hoi_dong as GB  # noqa: E402

TEN_DE_CUONG = "DE_CUONG_NOP_HOI_DONG_{study}"
CHAM = "………"
DAU_KHUON = "# CHƯƠNG 1."  # văn bản đã theo khuôn ⇒ không chuyển lại

# Chỉ chữ RIÊNG của tiếng Việt — á/é/ó/ú/à… và ã/õ có cả trong tiếng Tây Ban Nha, Pháp, Bồ Đào Nha (đo C1a 21/11: bài
# «Adaptación transcultural…» từng bị xếp vào nhóm tiếng Việt).
_CHU_VIET = "ăâđêôơưảạằắẳẵặầấẩẫậẻẹềếểễệỉĩịỏọồốổỗộờớởỡợủũụừứửữựỳỷỹỵ"
_VIET_RE = re.compile(f"[{_CHU_VIET}]", re.IGNORECASE)
_DAU_TAY_RE = re.compile(r"[áéíóúàèìòùâêîôûäëïöüãõñçÁÉÍÓÚÀÈÌÒÙÑÇ]")
_THU_TU_CHU = "aăâbcdđeêfghijklmnoôơpqrstuưvwxyz"
_DAU_THANH = {"\u0300": 1, "\u0301": 2, "\u0309": 3, "\u0303": 4, "\u0323": 5}  # huyền sắc hỏi ngã nặng
_DAU_CHU = {"\u0306": "ă", "\u0302": "^", "\u031b": "+"}  # trăng, mũ, móc
_CO_QUAN_RE = re.compile(r"^(Bộ|Bệnh viện|Tổ chức|Viện|Trung tâm|Sở|Cục|Quốc hội|Chính phủ|Hội|Trường|Ban|Ủy ban|"
                         r"Uỷ ban)\b")
_TRICH_RE = re.compile(r"\[(\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–-]\s*\d+)?)*)\]")
_THAM_CHIEU_BB_RE = re.compile(r"\b(Bảng|Hình|Biểu đồ|Sơ đồ)\s+(\d+\.\d+)(?:(\s*[–-]\s*)(\d+\.\d+))?(?![\d])")
# «mục 2.5.1, 4.9», «mục 4.2 và 4.7» — danh sách số mục sau MỘT chữ «mục» (đo BTM 21/11: chỉ số đầu được đổi). Một lượt
# thay duy nhất: số đã đổi không bị đổi lần hai.
_DS_MUC_RE = re.compile(r"\b([Mm]ục)\s+(\d+(?:\.\d+)*(?:\s*(?:,|và|hoặc|–|-)\s*\d+(?:\.\d+)*)*)(?![\d.]?\d)")
_THAM_CHIEU_MUC_RE = re.compile(r"\b([Mm]ục)\s+(\d+(?:\.\d+)*)(?:(\s*[–-]\s*)(\d+(?:\.\d+)*))?(?![\d.]?\d)")
_CHU_THICH_MOI_RE = re.compile(r"^\*\*(Bảng|Hình|Biểu đồ|Sơ đồ)\s+([0-9A-Z]+\.\d+)\.\s+(.+?)\*\*\s*$")
_CHU_THICH_RE = re.compile(r"^\*\*(Bảng|Hình|Biểu đồ|Sơ đồ)\s+(\d+\.\d+)\.\s+(.+?)\*\*\s*$")
# «chương 5» của bản cấu trúc cũ (22/11/2026 — tham-dinh-dau-ra trên đề cương C1a bắt «| Khung bảng kết quả | Theo
# chương 5 |» ở Phụ lục A: chữ viết tay từ 15/10, khi «5. DỰ KIẾN KẾT QUẢ» còn là chương 5; lần chuyển khuôn 21/11 đổi
# số «mục», «Bảng» nhưng bỏ sót «chương» ⇒ văn bản trỏ tới một chương không có — khuôn chỉ có Chương 1–3).
_THAM_CHIEU_CHUONG_RE = re.compile(r"(?<!\w)(?i:chương)\s+(\d+)(?![\d.]?\d)")
_KHUNG_BANG_RE = re.compile(r"(?i)khung bảng|bảng kết quả|dự kiến kết quả")
_DE_MUC_CHUONG_RE = re.compile(r"^#\s+CHƯƠNG\s+(\d+)\.\s*(.*)$")

# Khối ký bìa phụ (22/11/2026). Hướng dẫn chung in khối thứ ba «VIỆN TRƯỞNG — (Họ tên và chữ ký — nếu Khoa trực thuộc
# Viện)»: vế «nếu …» là LỜI HƯỚNG DẪN của khuôn cho người soạn, không phải chữ của văn bản nộp. Bản 21/11 chép nguyên
# khối ⇒ đề cương C1a (Khoa C1a thuộc Trung tâm C1, không thuộc Viện) và BTM (Khoa Khám bệnh trực thuộc bệnh viện) cùng
# mang khối ký Viện trưởng kèm lời hướng dẫn. Nay khối thứ ba theo ĐƠN VỊ THẬT khai trong hồ sơ: Khoa thuộc Viện ⇒ Viện
# trưởng; Khoa thuộc Trung tâm ⇒ Giám đốc Trung tâm (cùng vai thủ trưởng đơn vị ngay trên Khoa); Khoa trực thuộc bệnh
# viện hoặc hồ sơ không khai đơn vị ⇒ không có khối thứ ba (không khẳng định một đơn vị hồ sơ không ghi).
KY_CAP_TREN = {"vien": "VIỆN TRƯỞNG", "trung_tam": "GIÁM ĐỐC TRUNG TÂM"}
CHU_THICH_KY = "(Họ tên và chữ ký)"
_NHAN_KY_CAP_TREN_RE = re.compile(r"^\*\*(?:VIỆN TRƯỞNG|GIÁM ĐỐC TRUNG TÂM)\*\*\s*$")
# lời hướng dẫn của khuôn trong ngoặc: «(Họ tên và chữ ký — nếu Khoa trực thuộc Viện)» ⇒ giữ vế trước gạch nối
_HUONG_DAN_KHUON_RE = re.compile(r"\(([^()\n]*?\S)\s+[—–-]\s*nếu\s[^()\n]*\)")


# ── Xếp tài liệu tham khảo ───────────────────────────────────────────────────────────────────────────────────────────

# ── Dữ kiện cơ bản của đề cương cũ (tên, chủ nhiệm, đơn vị, thời gian, mục tiêu, vai trò) — chỉ đọc, nguyên văn ───────

_CHAM_RE = re.compile(r"^[\s.…_\-–]*$")
_PHIEN_BAN_BIA_RE = re.compile(r"^\**\s*Phiên bản đề cương\s*:", re.I)


@dataclass
class ThongTin:
    ten_de_tai: str = ""
    chu_nhiem: str = ""
    don_vi: str = ""
    thoi_gian: str = ""
    phien_ban: str = ""
    muc_tieu: List[str] = field(default_factory=list)
    vai_tro: List[str] = field(default_factory=list)


def _co(v: object) -> bool:
    """Có nội dung thật (không rỗng, không chỉ dòng chấm)."""
    return isinstance(v, str) and bool(v.strip()) and not _CHAM_RE.match(v)


def _o(d: str) -> List[str]:
    return [x.strip() for x in d.strip().strip("|").split("|")]


def _hang_bang_dau(dong: Sequence[str], muc: GB.Muc) -> List[List[str]]:
    """Các hàng nội dung của BẢNG ĐẦU TIÊN trong mục (bỏ hàng tiêu đề và hàng kẻ); không có bảng ⇒ []."""
    for i in range(muc.dong + 1, muc.het):
        if dong[i - 1].strip().startswith("|") and re.match(r"^\|[\s:|-]+\|?\s*$", dong[i].strip()):
            hang: List[List[str]] = []
            j = i + 2
            while j <= muc.het and dong[j - 1].strip().startswith("|"):
                hang.append(_o(dong[j - 1]))
                j += 1
            return hang
    return []


def _con(cac_muc: Sequence[GB.Muc], cha: GB.Muc) -> List[GB.Muc]:
    return [m for m in cac_muc if m.cap == cha.cap + 1 and cha.dong < m.dong <= cha.het]


def ten_ngan_don_vi(don_vi: str) -> str:
    """«Khoa Khám bệnh C1a, Trung tâm …, Bệnh viện Quân y 175, …» ⇒ «Khoa Khám bệnh C1a» (phần trước dấu phẩy đầu)."""
    return don_vi.split(",")[0].strip() if don_vi else ""


def _loai_don_vi(ten: str) -> str:
    """Loại của MỘT tên đơn vị theo chữ đầu: khoa · trung_tam · vien · benh_vien · "" (không phải tên đơn vị)."""
    k = re.sub(r"[*_]", "", ten).strip().casefold()
    for tien_to, loai in (("khoa ", "khoa"), ("trung tâm ", "trung_tam"), ("viện ", "vien"),
                          ("bệnh viện ", "benh_vien")):
        if k.startswith(tien_to):
            return loai
    return ""


def don_vi_cap_tren(*nguon: Optional[str]) -> Tuple[str, str]:
    """Đơn vị NGAY TRÊN Khoa (giữa Khoa và bệnh viện) — quyết định khối ký thứ ba của bìa phụ.

    `nguon` theo thứ tự ưu tiên do người gọi đặt (đơn vị của chủ nhiệm trong `study_meta.json` → hàng «Đơn vị chủ
    trì/thực hiện» của đề cương → dòng cơ quan ở bìa); mỗi nguồn là chuỗi đơn vị cách nhau dấu phẩy hoặc xuống dòng. Chỉ
    đọc nguồn ĐẦU TIÊN có tên đơn vị. Trả («vien»|«trung_tam», tên đơn vị) · («truc_thuoc», "") khi Khoa trực thuộc bệnh
    viện · («khong_ro», "") khi không nguồn nào có tên đơn vị."""
    for chuoi in nguon:
        if not isinstance(chuoi, str) or not _co(chuoi) or chuoi.lstrip().startswith("["):
            continue
        phan = [re.sub(r"[*_]", "", x).strip() for x in re.split(r"[,\n]", chuoi)]
        loai = [(_loai_don_vi(x), x) for x in phan if _loai_don_vi(x)]
        if not loai:
            continue
        for l_, ten in loai:
            if l_ in KY_CAP_TREN:
                return l_, ten
        return "truc_thuoc", ""
    return "khong_ro", ""


def don_vi_ho_so(meta: object) -> str:
    """Đơn vị của chủ nhiệm khai trong `study_meta.json` (`administrative.pi_unit`); không khai/ô chờ điền ⇒ ""."""
    adm = meta.get("administrative") if isinstance(meta, dict) else None
    v = adm.get("pi_unit") if isinstance(adm, dict) else None
    return v.strip() if isinstance(v, str) and _co(v) and not v.lstrip().startswith("[") else ""


def khoi_ky(loai: str) -> List[str]:
    """Khối chữ ký bìa phụ: Chủ nhiệm đề tài · Chủ nhiệm khoa · thủ trưởng đơn vị ngay trên Khoa (nếu có)."""
    ra = ["**CHỦ NHIỆM ĐỀ TÀI**", "", CHU_THICH_KY, "", "**CHỦ NHIỆM KHOA**", "", CHU_THICH_KY]
    if loai in KY_CAP_TREN:
        ra += ["", f"**{KY_CAP_TREN[loai]}**", "", CHU_THICH_KY]
    return ra


def _bao_cao_khoi_ky(loai: str, ten: str) -> Tuple[List[str], List[str]]:
    """(báo cáo, cảnh báo) về khối ký bìa phụ đã dựng."""
    if loai in KY_CAP_TREN:
        chuc = {"vien": "Viện trưởng", "trung_tam": "Giám đốc Trung tâm"}[loai]
        return [f"khối ký bìa phụ: Chủ nhiệm đề tài · Chủ nhiệm khoa · {chuc} (Khoa thuộc «{ten}»)"], []
    if loai == "truc_thuoc":
        return ["khối ký bìa phụ: Chủ nhiệm đề tài · Chủ nhiệm khoa (Khoa trực thuộc bệnh viện — không có khối "
                "thứ ba)"], []
    return [], ["hồ sơ không khai đơn vị của Khoa — bìa phụ chỉ có khối ký Chủ nhiệm đề tài và Chủ nhiệm khoa; Khoa "
                "thuộc Viện/Trung tâm thì khai `administrative.pi_unit` trong study_meta.json rồi chạy lại"]


def _dong_co_quan(dong: Sequence[str]) -> List[str]:
    """Các dòng cơ quan in đậm ở đầu bìa (trước «ĐỀ CƯƠNG NGHIÊN CỨU»/đề mục đầu) — không lấy tên đề tài."""
    ra: List[str] = []
    for d in dong:
        s = d.strip()
        if s.startswith("#") or "ĐỀ CƯƠNG NGHIÊN CỨU" in s.upper():
            break
        if s.startswith("**"):
            ra.append(s)
    return ra


def sua_khoi_ky_bia_phu(dong: List[str], loai: str) -> int:
    """Sửa TẠI CHỖ khối ký thứ ba của bìa phụ trong văn bản đã theo khuôn (giữ họ tên người đã điền dưới khối ký):
    bỏ khối không đúng đơn vị, đổi tên chức danh, thêm khối thiếu, gỡ lời hướng dẫn «(… — nếu …)» của khuôn trong bìa.
    Trả số chỗ đã sửa."""
    dau_h1 = next((i for i, d in enumerate(dong) if re.match(r"^#\s", d)), len(dong))
    sua = 0
    for i in range(dau_h1):
        moi = _HUONG_DAN_KHUON_RE.sub(r"(\1)", dong[i])
        if moi != dong[i]:
            dong[i], sua = moi, sua + 1
    i_kn = max((i for i in range(dau_h1) if dong[i].strip() == "**CHỦ NHIỆM KHOA**"), default=None)
    if i_kn is None:
        return sua
    i_tt = next((i for i in range(i_kn + 1, dau_h1) if _NHAN_KY_CAP_TREN_RE.match(dong[i].strip())), None)
    mong = KY_CAP_TREN.get(loai)
    if i_tt is not None:
        het = next((j for j in range(i_tt + 1, dau_h1) if dong[j].strip().startswith("**")), dau_h1)
        if mong is None:
            del dong[i_tt:het]
            return sua + 1
        if dong[i_tt].strip() != f"**{mong}**":
            dong[i_tt] = f"**{mong}**"
            sua += 1
        return sua
    if mong is not None:
        chen = next((j for j in range(i_kn + 1, dau_h1) if dong[j].strip().startswith("**")), dau_h1)
        dong[chen:chen] = [f"**{mong}**", "", CHU_THICH_KY, ""]
        sua += 1
    return sua


def sua_ban_da_theo_khuon(md: str, don_vi: str = "") -> Tuple[str, List[str], List[str]]:
    """Văn bản ĐÃ theo khuôn (lần chuyển trước, có thể người đã sửa tiếp) ⇒ chỉ sửa hai lỗi của bản chuyển 21/11, không
    đụng chỗ khác: (1) khối ký bìa phụ theo đơn vị thật, bỏ lời hướng dẫn của khuôn; (2) tham chiếu «chương N» tới
    chương không có trong một câu nói về khung bảng/dự kiến kết quả ⇒ chương chứa khung bảng (chương «DỰ KIẾN KẾT
    QUẢ»). Tham chiếu chương lạc khác chỉ CẢNH BÁO (không đoán). Trả (văn bản, báo cáo, cảnh báo)."""
    dong = md.splitlines()
    cac_muc = GB.doc_muc(dong)
    mh = trich_thong_tin(dong, cac_muc)
    loai, ten = don_vi_cap_tren(don_vi, mh.don_vi, "\n".join(_dong_co_quan(dong)))
    bao: List[str] = []
    canh: List[str] = []
    if sua_khoi_ky_bia_phu(dong, loai):
        b, c = _bao_cao_khoi_ky(loai, ten)
        bao += [f"sửa {x}" for x in b]
        canh += c
    co = {m.group(1): m.group(2) for d in dong for m in [_DE_MUC_CHUONG_RE.match(d)] if m}
    kq = next((n for n, t in co.items() if "DỰ KIẾN KẾT QUẢ" in t.upper()), None)
    i_tl = next((i for i, d in enumerate(dong) if re.match(r"^#\s+TÀI LIỆU THAM KHẢO\s*$", d)), None)
    het_tl = len(dong)
    if i_tl is not None:
        het_tl = next((i for i in range(i_tl + 1, len(dong)) if re.match(r"^#\s", dong[i])), len(dong))
    for i, d in enumerate(dong):
        if d.startswith("#") or (i_tl is not None and i_tl <= i < het_tl):
            continue
        lac = [m for m in _THAM_CHIEU_CHUONG_RE.finditer(d) if m.group(1) not in co]
        if not lac:
            continue
        if kq is not None and _KHUNG_BANG_RE.search(d):
            dong[i] = _THAM_CHIEU_CHUONG_RE.sub(lambda m: f"Chương {kq}" if m.group(1) not in co else m.group(0), d)
            bao.append(f"dòng {i + 1}: tham chiếu «{lac[0].group(0)}» (chương không có) ⇒ «Chương {kq}» — chương chứa "
                       "khung bảng kết quả")
        else:
            canh.append(f"dòng {i + 1}: «{lac[0].group(0)}» trỏ tới chương không có trong văn bản — chủ nhiệm sửa")
    moi = "\n".join(dong) + ("\n" if md.endswith("\n") else "")
    return moi, bao, canh


def trich_thong_tin(dong: Sequence[str], cac_muc: Sequence[GB.Muc]) -> ThongTin:
    """Dữ kiện cơ bản từ đề cương cấu trúc cũ: bảng «Thông tin chung», danh sách mục tiêu (mục «Mục tiêu» hoặc phần
    thân chương «MỤC TIÊU NGHIÊN CỨU» trước mục con đầu tiên — không đếm dòng giả thuyết H₀/H₁ của mục con), vai trò
    nhân lực (bảng, hoặc văn xuôi «Vai trò: nhiệm vụ»)."""
    tt = ThongTin()
    ttc = GB.tim_muc(cac_muc, r"^thông tin chung")
    bang = {GB._chuan(o[0]): o[1] for o in (_hang_bang_dau(dong, ttc) if ttc else []) if len(o) >= 2}

    def _lay(*khoa: str) -> str:
        return next((v for k, v in bang.items() for x in khoa if k.startswith(x) and _co(v)), "")

    tt.ten_de_tai = _lay("tên đề tài")
    tt.chu_nhiem = _lay("chủ nhiệm")
    tt.don_vi = _lay("đơn vị chủ trì", "đơn vị thực hiện")
    tt.thoi_gian = _lay("thời gian")
    tt.phien_ban = _lay("phiên bản")
    for mau, chi_than in ((r"^mục tiêu$", False), (r"^mục tiêu nghiên cứu$", True)):
        muc = GB.tim_muc(cac_muc, mau)
        if muc is None:
            continue
        for i in range(muc.dong + 1, muc.het + 1):
            if chi_than and GB._DE_MUC_RE.match(dong[i - 1].strip()):
                break
            m = GB._MUC_DS_RE.match(dong[i - 1])
            if m:
                tt.muc_tieu.append(re.sub(r"^\*{1,3}(.+?)\*{1,3}$", r"\1", m.group(1).strip()))
        if tt.muc_tieu:
            break
    nl = GB.tim_muc(cac_muc, r"^nhân lực")
    if nl is not None:
        hang = _hang_bang_dau(dong, nl)
        if hang:
            tt.vai_tro = [o[0] for o in hang if o and _co(o[0])]
        else:
            for i in range(nl.dong + 1, nl.het + 1):
                for cau in GB.tach_cau(dong[i - 1].strip()):
                    m = re.match(r"^(?:\*\*)?([^:*]{3,60}?)(?:\*\*)?\s*:", cau)
                    if m:
                        tt.vai_tro.append(m.group(1).split(" (")[0].strip())
    return tt


def khoa_viet(s: str) -> Tuple:
    """Khoá xếp theo bảng chữ cái tiếng Việt: chữ cái (a < ă < â < b … đ sau d) trước, dấu thanh sau."""
    chu: List[int] = []
    thanh: List[int] = []
    for ky in unicodedata.normalize("NFD", s.casefold()):
        if ky in _DAU_THANH:
            if thanh:
                thanh[-1] = _DAU_THANH[ky]
            continue
        if ky in _DAU_CHU and chu:
            goc = _THU_TU_CHU[chu[-1]] if 0 <= chu[-1] < len(_THU_TU_CHU) else ""
            moi = {("a", "ă"): "ă", ("a", "^"): "â", ("e", "^"): "ê", ("o", "^"): "ô", ("o", "+"): "ơ",
                   ("u", "+"): "ư"}.get((goc, _DAU_CHU[ky]))
            if moi:
                chu[-1] = _THU_TU_CHU.index(moi)
            continue
        if unicodedata.category(ky) == "Mn":
            continue
        chu.append(_THU_TU_CHU.index(ky) if ky in _THU_TU_CHU else 100 + ord(ky))
        thanh.append(0)
    return (tuple(chu), tuple(thanh))


def la_tieng_viet(muc: str) -> bool:
    """Mục tài liệu tiếng Việt: phần tác giả + tên bài (trước tên tạp chí) có chữ có dấu tiếng Việt."""
    return bool(_VIET_RE.search(muc.split(". ")[0] + " " + (muc.split(". ")[1] if ". " in muc else "")))


def khoa_tac_gia(muc: str) -> Tuple:
    """Khoá xếp một mục: tác giả Việt theo TÊN (từ cuối của họ tên đầu tiên) rồi cả họ tên; tác giả nước ngoài theo HỌ
    (từ đầu, kiểu Vancouver «Smith J»); cơ quan theo chữ đầu tên cơ quan (Bộ Y tế ⇒ vần B)."""
    tac = muc.split(". ")[0]
    dau = tac.split(",")[0].strip()
    if _CO_QUAN_RE.match(dau) or not la_tieng_viet(muc):
        return (khoa_viet(dau), khoa_viet(tac))
    tu = dau.split()
    return (khoa_viet(tu[-1] if tu else dau), khoa_viet(dau))


def xep_tltk(muc: Dict[int, str]) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]], Dict[int, int]]:
    """(mục tiếng Việt, mục ngoại ngữ, bản đồ số cũ → số mới) theo hướng dẫn chung mục II.9."""
    def _khoa(kv: Tuple[int, str]) -> Tuple:
        return (khoa_tac_gia(kv[1]), kv[0])

    viet = sorted([(k, v) for k, v in muc.items() if la_tieng_viet(v)], key=_khoa)
    ngoai = sorted([(k, v) for k, v in muc.items() if not la_tieng_viet(v)], key=_khoa)
    ban_do = {cu: moi for moi, (cu, _v) in enumerate(viet + ngoai, 1)}
    return viet, ngoai, ban_do


def _gon_so(ds: Sequence[int]) -> str:
    """[3, 4, 5, 9] ⇒ «3–5, 9» (chuỗi ba số liền trở lên gộp bằng gạch nối)."""
    ra: List[str] = []
    ds = sorted(set(ds))
    i = 0
    while i < len(ds):
        j = i
        while j + 1 < len(ds) and ds[j + 1] == ds[j] + 1:
            j += 1
        ra.append(f"{ds[i]}–{ds[j]}" if j - i >= 2 else ", ".join(str(x) for x in ds[i:j + 1]))
        i = j + 1
    return ", ".join(ra)


def _mo_rong(s: str) -> List[int]:
    ra: List[int] = []
    for phan in s.split(","):
        phan = phan.strip().replace("–", "-")
        if "-" in phan:
            a, b = (int(x) for x in phan.split("-", 1))
            ra.extend(range(a, b + 1) if b >= a else [a, b])
        elif phan.isdigit():
            ra.append(int(phan))
    return ra


# ── Dựng khuôn ───────────────────────────────────────────────────────────────────────────────────────────────────────

@dataclass
class Muc_:
    """Một dòng của văn bản mới: đề mục (cap ≥ 1) hoặc dòng thường (cap = 0). `so_cu` = số mục của bản cũ."""
    cap: int
    van: str
    so_cu: str = ""
    so_moi: str = ""
    chuong: str = ""  # nhãn chương để đánh số bảng («1», «2», «3», «F»…)


@dataclass
class KetQua:
    md: str
    bao_cao: List[str] = field(default_factory=list)
    canh_bao: List[str] = field(default_factory=list)
    da_theo_khuon: bool = False


def _khoi(dong: Sequence[str], muc: GB.Muc, cap_goc: int, chuong: str) -> List[Muc_]:
    """Đề mục `muc` + toàn bộ thân (kể cả mục con), dời cấp sao cho đề mục gốc ở `cap_goc`."""
    lech = cap_goc - muc.cap
    ra = [Muc_(cap_goc, muc.ten, muc.so, chuong=chuong)]
    for i in range(muc.dong + 1, muc.het + 1):
        d = dong[i - 1]
        m = GB._DE_MUC_RE.match(d.strip())
        if m:
            t = m.group(2).strip()
            ms = GB._SO_MUC_RE.match(t)
            ra.append(Muc_(len(m.group(1)) + lech, ms.group(2).strip() if ms else t, ms.group(1) if ms else "",
                           chuong=chuong))
        elif d.strip() != "---":  # ngắt trang của bản cũ bỏ — khuôn tự ngắt trang trước mỗi chương
            ra.append(Muc_(0, d, chuong=chuong))
    return ra


def viet_hoa(s: str) -> str:
    """Viết hoa nhưng giữ nguyên từ có chữ số («C1a», «KDIGO 2022» — tránh «C1A»)."""
    return " ".join(w if re.search(r"\d", w) else w.upper() for w in s.split())


def _than(dong: Sequence[str], muc: GB.Muc, chuong: str) -> List[Muc_]:
    """Thân của một chương/phụ lục (bỏ đề mục gốc), GIỮ nguyên cấp các đề mục con."""
    return _khoi(dong, muc, muc.cap, chuong)[1:]


def _danh_so(muc: List[Muc_], chuong: str) -> None:
    """Đánh số đề mục cấp 2–4 theo vị trí trong chương; cấp > 4 hạ thành dòng in đậm (hướng dẫn: ≤ 4 chữ số)."""
    dem = [0] * 8
    for m in muc:
        if m.cap < 2:
            continue
        if m.cap > 4:
            m.van, m.cap = f"**{m.van}**", 0
            continue
        dem[m.cap] += 1
        for k in range(m.cap + 1, 8):
            dem[k] = 0
        m.so_moi = ".".join([chuong] + [str(dem[k]) for k in range(2, m.cap + 1)]) if chuong.isdigit() else ""


def _tim_con(con: Sequence[GB.Muc], mau: str) -> Optional[GB.Muc]:
    bt = re.compile(mau)
    return next((m for m in con if bt.search(GB._chuan(m.ten))), None)


THU_TU_CHUONG_2: Tuple[Tuple[str, str, int], ...] = (
    ("doi_tuong", r"^đối tượng", 2), ("thoi_gian", r"^(?:địa điểm và thời gian|thời gian và địa điểm)", 2),
    ("thiet_ke", r"^thiết kế", 2), ("cau_hoi", "", 2), ("co_mau", r"^cỡ mẫu", 2),
    ("phuong_phap", "", 2), ("cong_cu", r"^công cụ", 3), ("ky_thuat", r"^kỹ thuật thu thập", 3),
    ("quy_trinh", r"^quy trình", 3), ("bien_so", r"^biến số", 3), ("sai_so", r"^sai số", 3),
    ("phan_tich", r"^xử lý và phân tích", 3), ("dao_duc", r"^đạo đức", 2),
)


def chuyen(md: str, nam: Optional[int] = None, don_vi: str = "") -> KetQua:
    """Văn bản đề cương nộp (cấu trúc cũ) ⇒ văn bản theo khuôn hướng dẫn chung. Không đổi nội dung chuyên môn.
    `don_vi` = đơn vị của chủ nhiệm trong hồ sơ (`don_vi_ho_so(study_meta)`), ưu tiên hơn đơn vị ghi trong đề cương khi
    dựng khối ký bìa phụ. Văn bản đã theo khuôn ⇒ không chuyển lại, chỉ qua `sua_ban_da_theo_khuon`."""
    if DAU_KHUON in md:
        moi, bao, canh = sua_ban_da_theo_khuon(md, don_vi)
        return KetQua(moi, ["văn bản đã theo khuôn — không chuyển lại"] + bao, canh, da_theo_khuon=True)
    dong = md.splitlines()
    cac_muc = GB.doc_muc(dong)
    kq = KetQua("")
    mh = trich_thong_tin(dong, cac_muc)
    cap1 = [m for m in cac_muc if m.cap == 1]

    def _c1(mau: str) -> Optional[GB.Muc]:
        bt = re.compile(mau)
        return next((m for m in cap1 if bt.search(GB._chuan(m.ten))), None)

    dvd, mt, tq, pp = _c1(r"đặt vấn đề"), _c1(r"^mục tiêu"), _c1(r"tổng quan"), _c1(r"đối tượng và phương pháp")
    dk, kh, tl = _c1(r"dự kiến kết quả"), _c1(r"kế hoạch thực hiện"), _c1(r"tài liệu tham khảo")
    phu_luc = [m for m in cap1 if GB._chuan(m.ten).startswith("phụ lục") or GB._chuan(m.so).startswith("phụ lục")]
    dau_vb = next((m for m in cap1 if "đề cương" in GB._chuan(m.ten)), None)
    biet = {id(x) for x in (dvd, mt, tq, pp, dk, kh, tl, dau_vb) if x is not None} | {id(x) for x in phu_luc}
    la = [m for m in cap1 if id(m) not in biet]
    for ten, x in (("đặt vấn đề", dvd), ("tổng quan", tq), ("đối tượng và phương pháp", pp), ("dự kiến kết quả", dk),
                   ("tài liệu tham khảo", tl)):
        if x is None:
            kq.canh_bao.append(f"không thấy chương «{ten}» — phần tương ứng của khuôn để trống")
    ten_de_tai = mh.ten_de_tai or (next((m.ten for m in cac_muc if m.cap == 2), ""))
    # ── tài liệu tham khảo ──
    tltk: Dict[int, str] = {}
    if tl is not None:
        for i in range(tl.dong + 1, tl.het + 1):
            m = re.match(r"^(\d+)\.\s+(.+)$", dong[i - 1].strip())
            if m:
                tltk[int(m.group(1))] = m.group(2).strip()
    viet, ngoai, ban_do_tl = xep_tltk(tltk)
    # ── chương nội dung (còn số cũ trong văn bản; thay một lượt ở cuối) ──
    than: List[Muc_] = []
    so_chuong_cu: Dict[str, str] = {}

    def _chuong(nhan: str, tieu_de: str, muc_: List[Muc_], so_cu: str = "") -> None:
        than.append(Muc_(1, tieu_de, so_cu, chuong=nhan))
        _danh_so(muc_, nhan)
        than.extend(muc_)

    if dvd is not None:
        dvd_than = [Muc_(0, d, chuong="0") for d in dong[dvd.dong:dvd.het] if d.strip() != "---"]
        muc_tieu = list(mh.muc_tieu)
        tieu = {re.sub(r"^\*+|\*+$", "", d).strip() for d in muc_tieu}
        dvd_than = [x for x in dvd_than if not (GB._MUC_DS_RE.match(x.van) and
                                               GB._MUC_DS_RE.match(x.van).group(1).strip() in tieu)]
        van_dvd = "\n".join(x.van for x in dvd_than)
        if ten_de_tai and GB._chuan(ten_de_tai) in GB._chuan(van_dvd):
            for x in dvd_than:
                x.van = re.sub(r"“(?!\*\*)" + re.escape(ten_de_tai) + "”", f"“**{ten_de_tai}**”", x.van)
        elif ten_de_tai and "đề tài này" in van_dvd:
            for x in dvd_than:
                if "đề tài này" in x.van:
                    x.van = x.van.replace("đề tài này", f"đề tài “**{ten_de_tai}**”", 1)
                    break
        elif ten_de_tai:
            dvd_than.append(Muc_(0, f"Đề tài: “**{ten_de_tai}**”.", chuong="0"))
            kq.bao_cao.append("đặt vấn đề không nêu tên đề tài — thêm một dòng tên đề tài trong ngoặc kép, in đậm")
        for x in dvd_than:
            x.van = re.sub(r"(trình bày\s+)?(?:ở|tại)\s+mục\s+2(?!\.?\d)", lambda m: f"{m.group(1) or ''}dưới đây",
                           x.van)
        than.append(Muc_(1, "ĐẶT VẤN ĐỀ", dvd.so, chuong="0"))
        than.extend(dvd_than)
        so_chuong_cu[dvd.so] = "dvd"
        than.append(Muc_(2, "MỤC TIÊU NGHIÊN CỨU", chuong="0"))
        con_mt = _con(cac_muc, mt) if mt is not None else []
        mt_than = GB.tim_muc(con_mt, r"^mục tiêu$") if con_mt else None
        nguon_mt = (dong[mt_than.dong:mt_than.het] if mt_than is not None else [f"{k}. {d}"
                                                                                for k, d in enumerate(muc_tieu, 1)])
        for d in nguon_mt:
            m = re.match(r"^(\s*\d+\.\s+)(.+)$", d)
            than.append(Muc_(0, f"{m.group(1)}***{m.group(2).strip()}***" if m else d, chuong="0"))
        if mt is not None:
            so_chuong_cu[mt.so] = "muc_tieu"
            if mt_than is not None:
                so_chuong_cu[mt_than.so] = "muc_tieu"
    if tq is not None:
        _chuong("1", "CHƯƠNG 1. TỔNG QUAN TÀI LIỆU", _than(dong, tq, "1"))
        so_chuong_cu[tq.so] = "chuong:1"
    han_che: Optional[GB.Muc] = None
    if pp is not None:
        con = _con(cac_muc, pp)
        dung: set = set()
        muc2: List[Muc_] = []
        for khoa, mau, cap in THU_TU_CHUONG_2:
            if khoa == "cau_hoi":
                con_mt = _con(cac_muc, mt) if mt is not None else []
                ch = [m for m in con_mt if re.search(r"câu hỏi|giả thuyết", GB._chuan(m.ten))]
                if ch:
                    muc2.append(Muc_(2, "Câu hỏi và giả thuyết nghiên cứu", chuong="2"))
                    for m in ch:
                        muc2 += _khoi(dong, m, 3, "2")
                continue
            if khoa == "phuong_phap":
                if any(_tim_con(con, x[1]) for x in THU_TU_CHUONG_2 if x[2] == 3):
                    muc2.append(Muc_(2, "Phương pháp nghiên cứu", chuong="2"))
                continue
            m = _tim_con(con, mau)
            if m is not None and id(m) not in dung:
                dung.add(id(m))
                muc2 += _khoi(dong, m, cap, "2")
        han_che = _tim_con(con, r"^hạn chế")
        if han_che is not None:
            dung.add(id(han_che))
        con_lai = [m for m in con if id(m) not in dung]
        for m in con_lai:
            muc2 += _khoi(dong, m, 2, "2")
            kq.canh_bao.append(f"mục «{m.ten}» của chương phương pháp không có chỗ trong khuôn — giữ ở cuối Chương 2")
        than_pp = [Muc_(0, d, chuong="2") for d in dong[pp.dong:(con[0].dong - 1 if con else pp.het)]
                   if d.strip() != "---"]
        _chuong("2", "CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", than_pp + muc2)
        so_chuong_cu[pp.so] = "chuong:2"
    if dk is not None:
        muc3 = _than(dong, dk, "3")
        # 21/11/2026: bộ sinh đề cương đã dựng «Dự kiến bàn luận» theo từng mục tiêu (STROBE 18) ngay trong chương dự
        # kiến kết quả ⇒ giữ nguyên, không thêm bản thứ hai.
        if not any("bàn luận" in GB._chuan(m.ten) for m in _con(cac_muc, dk)):
            muc3.append(Muc_(2, "Dự kiến bàn luận", chuong="3"))
            for k in range(1, len(mh.muc_tieu) + 1):
                muc3 += [Muc_(3, f"Bàn luận theo mục tiêu {k}", chuong="3"), Muc_(0, "", chuong="3"),
                         Muc_(0, f"@@BAN_LUAN_{k}@@", chuong="3"), Muc_(0, "", chuong="3")]
        if han_che is not None:
            muc3 += _khoi(dong, han_che, 2, "3")
        _chuong("3", "CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN", muc3)
        so_chuong_cu[dk.so] = "chuong:3"
    for m in la:
        than.append(Muc_(1, m.ten, m.so))
        than.extend(_than(dong, m, ""))
        kq.canh_bao.append(f"chương «{m.ten}» không có chỗ trong khuôn — giữ trước tài liệu tham khảo")
    # ── phụ lục: giữ chữ cái cũ; kế hoạch thực hiện thành phụ lục kế tiếp ──
    chu_pl = [re.sub(r"(?i)^phụ lục\s+", "", m.so).strip() for m in phu_luc]
    sau: List[Muc_] = []
    for m, chu in zip(phu_luc, chu_pl):
        sau.append(Muc_(1, f"{m.so}. {m.ten}" if m.so else m.ten, chuong=chu))
        sau.extend([Muc_(0, d, chuong=chu) for d in dong[m.dong:m.het] if d.strip() != "---"])
    if kh is not None:
        moi = next(c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in chu_pl)
        sau.append(Muc_(1, f"PHỤ LỤC {moi}. KẾ HOẠCH THỰC HIỆN", kh.so, chuong=moi))
        for x in _than(dong, kh, moi):
            sau.append(x)
            if x.cap >= 2:
                so_chuong_cu[x.so_cu] = f"phu_luc:{moi}"
        so_chuong_cu[kh.so] = f"phu_luc:{moi}"
        kq.bao_cao.append(f"kế hoạch thực hiện chuyển thành Phụ lục {moi}")
    # «Thông tin chung» (chủ nhiệm, đơn vị, thời gian, kinh phí, đăng ký, phiên bản đề cương) không có chỗ trong cấu
    # trúc của khuôn nhưng là dữ kiện Hội đồng cần và mẫu DK/TM đọc lại (`ho_so_dtcs_bvqy175.py`) ⇒ giữ nguyên thành phụ
    # lục cuối, không bỏ (21/11/2026: bỏ đi thì mẫu thuyết minh mất chủ nhiệm, thời gian, kinh phí).
    ttc = GB.tim_muc(cac_muc, r"^thông tin chung")
    if ttc is not None:
        da = set(chu_pl) | {re.sub(r"(?i)^phụ lục\s+", "", x.van).split(".")[0] for x in sau if x.cap == 1}
        chu = next(c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in da)
        sau.append(Muc_(1, f"PHỤ LỤC {chu}. THÔNG TIN CHUNG VỀ ĐỀ TÀI", ttc.so, chuong=chu))
        sau.extend([Muc_(0, d, chuong=chu) for d in dong[ttc.dong:ttc.het] if d.strip() != "---"])
        kq.bao_cao.append(f"thông tin chung (chủ nhiệm, đơn vị, thời gian, kinh phí…) chuyển thành Phụ lục {chu}")
    if tl is not None:
        so_chuong_cu[tl.so] = "tltk"
    # ── bản đồ số mục cũ → mới; bảng/hình theo chương ──
    ban_do_muc: Dict[str, str] = {}
    for x in than:
        if x.cap >= 2 and x.so_cu and x.so_moi:
            ban_do_muc[x.so_cu] = x.so_moi
    ban_do_bb: Dict[Tuple[str, str], str] = {}
    dem: Dict[Tuple[str, str], int] = {}
    for x in than + sau:
        m = _CHU_THICH_RE.match(x.van.strip()) if x.cap == 0 else None
        if m and x.chuong and x.chuong != "0" and (m.group(1), m.group(2)) not in ban_do_bb:
            k = (x.chuong, m.group(1))
            dem[k] = dem.get(k, 0) + 1
            ban_do_bb[(m.group(1), m.group(2))] = f"{x.chuong}.{dem[k]}"

    def _muc(so: str) -> str:
        if so in ban_do_muc:
            return f"mục {ban_do_muc[so]}"
        goc = so_chuong_cu.get(so)
        if goc is None and "." in so and so_chuong_cu.get(so.split(".")[0], "").startswith("phu_luc"):
            goc = so_chuong_cu[so.split(".")[0]]  # mục con của kế hoạch thực hiện ⇒ phụ lục kế hoạch
        if not goc:
            return ""
        if goc == "muc_tieu":
            return "phần mục tiêu nghiên cứu"
        if goc == "dvd":
            return "phần đặt vấn đề"
        if goc == "tltk":
            return "phần tài liệu tham khảo"
        loai, _, nhan = goc.partition(":")
        return f"Chương {nhan}" if loai == "chuong" else f"Phụ lục {nhan}"

    def _thay(van: str, chuong: bool = True) -> str:
        """`chuong=False` cho đề mục cấp 1 do khuôn dựng («CHƯƠNG 1. …», «PHỤ LỤC A. …») — đã mang số MỚI."""
        def _tc(m: re.Match) -> str:
            so = [ban_do_tl.get(n, n) for n in _mo_rong(m.group(1))]
            return f"[{_gon_so(so)}]"

        def _bb(m: re.Match) -> str:
            a = ban_do_bb.get((m.group(1), m.group(2)))
            if a is None:
                return m.group(0)
            b = ban_do_bb.get((m.group(1), m.group(4))) if m.group(4) else None
            duoi = f"{m.group(3)}{b or m.group(4)}" if m.group(4) else ""
            return f"{m.group(1)} {a}{duoi}"

        def _mc(m: re.Match) -> str:
            a = _muc(m.group(2))
            if not a:
                return m.group(0)
            if a.startswith("mục ") and m.group(1)[0] == "M":
                a = "M" + a[1:]
            if m.group(4):
                b = _muc(m.group(4))
                if a.startswith(("mục ", "Mục ")) and b.startswith("mục "):
                    return f"{a}{m.group(3)}{b[4:]}"
            return a

        def _ds(m: re.Match) -> str:
            phan = re.split(r"(\s*(?:,|và|hoặc|–|-)\s*)", m.group(2))
            if len(phan) == 1 or (len(phan) == 3 and phan[1].strip() in ("–", "-")):
                return _THAM_CHIEU_MUC_RE.sub(_mc, m.group(0))  # một số hoặc một khoảng: luật cũ
            ra = []
            for t in phan:
                a = _muc(t) if re.fullmatch(r"\d+(?:\.\d+)*", t) else ""
                ra.append(a[4:] if a.startswith("mục ") else (a or t))
            # số đầu thành «Chương n»/«Phụ lục X» ⇒ bỏ chữ «mục» đứng trước
            return "".join(ra) if ra and not re.match(r"\d", ra[0]) else f"{m.group(1)} " + "".join(ra)

        def _ch(m: re.Match) -> str:
            # «chương 5» của bản cũ ⇒ chương/phụ lục/phần mới chứa nội dung chương đó; không biết ⇒ giữ nguyên (K19 bắt)
            a = _muc(m.group(1))
            return a if a.startswith(("Chương ", "Phụ lục ", "phần ")) else m.group(0)

        van = _TRICH_RE.sub(_tc, van)
        van = _THAM_CHIEU_BB_RE.sub(_bb, van)
        if chuong:  # TRƯỚC lượt «mục»: chữ «Chương n» do lượt «mục» sinh ra đã mang số mới, không được đổi lần hai
            van = _THAM_CHIEU_CHUONG_RE.sub(_ch, van)
        return _DS_MUC_RE.sub(_ds, van)

    def _ra(muc: Sequence[Muc_]) -> List[str]:
        out: List[str] = []
        for x in muc:
            if x.cap == 0:
                out.append(_thay(x.van))
            elif x.cap == 1:
                out += ["---", "", f"# {_thay(x.van, chuong=False)}", ""]
            else:
                out += [f"{'#' * x.cap} {x.so_moi + '. ' if x.so_moi else ''}{_thay(x.van)}", ""]
        return out

    than_md = _ra(than)
    sau_md = _ra(sau)
    # khung bàn luận theo mục tiêu: liệt kê đúng bảng/biểu đồ gắn «(Mục tiêu k)» của chương 3 sau khi đánh số lại
    chu_thich_c3 = [(m.group(1), m.group(2), m.group(3)) for d in than_md
                    for m in [_CHU_THICH_RE.match(d.strip())] if m and m.group(2).startswith("3.")]
    for k in range(1, len(mh.muc_tieu) + 1):
        if f"@@BAN_LUAN_{k}@@" not in than_md:  # bàn luận do bộ sinh dựng sẵn (21/11/2026)
            continue
        bb = [f"{a} {b}" for a, b, t in chu_thich_c3 if re.search(rf"\(Mục tiêu {k}(?!\d)", t)]
        cau = (f"Bàn luận lần lượt các kết quả trả lời mục tiêu {k}" + (f" ({', '.join(bb)})" if bb else "")
               + ": so sánh với các nghiên cứu trong nước và quốc tế đã tổng quan ở Chương 1, nêu điểm giống, điểm "
               "khác và lý giải sự khác biệt; diễn giải ý nghĩa của kết quả đối với thực hành tại đơn vị.")
        than_md = [cau if d == f"@@BAN_LUAN_{k}@@" else d for d in than_md]
        i = than_md.index(cau)
        than_md[i + 1:i + 1] = ["", f"Các ý bàn luận chính do chủ nhiệm bổ sung: {CHAM}"]
    # ── tài liệu tham khảo ──
    tl_md: List[str] = []
    if tltk:
        tl_md = ["---", "", "# TÀI LIỆU THAM KHẢO", ""]
        if viet:
            tl_md += ["**Tài liệu tiếng Việt**", ""] + [f"{ban_do_tl[k]}. {v}" for k, v in viet] + [""]
        if ngoai:
            # nhãn «nước ngoài» khi TÊN BÀI (không xét tên tác giả — «Hernández» vẫn có thể là bài tiếng Anh) mang dấu
            # của tiếng khác tiếng Anh
            khac = any(_DAU_TAY_RE.search(v.split(". ")[1]) for _k, v in ngoai if ". " in v)
            tl_md += [f"**Tài liệu tiếng {'nước ngoài' if khac else 'Anh'}**", ""]
            tl_md += [f"{ban_do_tl[k]}. {v}" for k, v in ngoai] + [""]
        kq.bao_cao.append(f"tài liệu tham khảo xếp lại: {len(viet)} tiếng Việt, {len(ngoai)} tiếng Anh; đánh số lại "
                          "mọi trích dẫn")
    # ── phần đầu: bìa, bìa phụ, danh sách cán bộ, mục lục, danh mục ──
    dau_tep = [d for d in dong[:(cac_muc[0].dong - 1 if cac_muc else 0)] if d.strip()]
    co_quan_goc = [d for d in dau_tep if d.strip().startswith("**")]
    co_quan = co_quan_goc or ["**BỆNH VIỆN QUÂN Y 175**"] + (
        [f"**{viet_hoa(ten_ngan_don_vi(mh.don_vi))}**"]
        if mh.don_vi else [f"**KHOA {CHAM}**"])
    loai_tren, ten_tren = don_vi_cap_tren(don_vi, mh.don_vi, "\n".join(co_quan_goc))
    b_ky, c_ky = _bao_cao_khoi_ky(loai_tren, ten_tren)
    kq.bao_cao += b_ky
    kq.canh_bao += c_ky
    nam_bia = nam or datetime.now().year
    m_nam = re.search(r"20\d{2}", mh.thoi_gian or "")
    if nam is None and m_nam:
        nam_bia = int(m_nam.group(0)) if int(m_nam.group(0)) <= datetime.now().year + 1 else nam_bia
    chu_nhiem = re.split(r"\s+[–-]\s+", mh.chu_nhiem)[0] if mh.chu_nhiem else CHAM
    # Dòng «Phiên bản đề cương: …, ngày …» của bìa cũ — Hội đồng đòi trên mọi tài liệu nộp (trục de_cuong_nop DC-01 của
    # nhat_quan_xuyen_cong). Bìa cũ đặt dòng này SAU đề mục đầu nên lần chuyển đầu làm rơi mất (đo C1a/BTM 21/11) ⇒ chép
    # NGUYÊN VĂN lên bìa và bìa phụ; không có dòng đó thì lấy hàng «Phiên bản đề cương» của bảng thông tin chung.
    dau_dvd = dvd.dong - 1 if dvd is not None else len(dong)
    phien_ban = next((d.strip() for d in dong[:dau_dvd] if _PHIEN_BAN_BIA_RE.match(d.strip())), "")
    if not phien_ban and mh.phien_ban:
        phien_ban = f"**Phiên bản đề cương:** {mh.phien_ban}"
    if not phien_ban:
        kq.canh_bao.append("đề cương cũ không ghi «Phiên bản đề cương: …, ngày …» — Hội đồng đòi trên bìa; chủ nhiệm "
                           "bổ sung")
    dong_pb = [phien_ban, ""] if phien_ban else []
    bia = co_quan + ["", "**ĐỀ CƯƠNG NGHIÊN CỨU**", "", "**ĐỀ TÀI KHOA HỌC VÀ CÔNG NGHỆ CẤP BỆNH VIỆN**", "",
                     f"**{viet_hoa(ten_de_tai)}**", ""]
    out = bia + [f"**Chủ nhiệm đề tài: {chu_nhiem}**", ""] + dong_pb + [f"**THÀNH PHỐ HỒ CHÍ MINH, {nam_bia}**", "",
                                                                         "---", ""]
    out += bia + dong_pb + khoi_ky(loai_tren) + ["", f"**THÀNH PHỐ HỒ CHÍ MINH, {nam_bia}**", "", "---", ""]
    vai = mh.vai_tro or ["Chủ nhiệm đề tài"]
    out += ["# DANH SÁCH CÁC CÁN BỘ THAM GIA THỰC HIỆN ĐỀ TÀI", "",
            "| STT | Chức danh, họ và tên | Đơn vị công tác | Nhiệm vụ trong đề tài |", "|---|---|---|---|"]
    for k, v in enumerate(vai, 1):
        la_cn = k == 1 and "chủ nhiệm" in v.lower()
        out.append(f"| {k} | {chu_nhiem if la_cn else CHAM} | {(mh.don_vi or CHAM) if la_cn else CHAM} | {v} |")
    out += ["", f"Chủ nhiệm đề tài (ký và ghi rõ họ tên): {CHAM}", "",
            f"Đơn vị chủ trì đề tài (ký và ghi rõ họ tên): {CHAM}", "",
            f"Phòng Khoa học Quân sự (ký và ghi rõ họ tên): {CHAM}", "", "---", "", "# MỤC LỤC", ""]
    out += [f"- {re.sub(r'^#+ ', '', d)}" for d in than_md + tl_md + sau_md if re.match(r"^#{1,2} ", d)]
    vt = GB.tim_muc(cac_muc, r"chữ viết tắt")
    if vt is None:
        kq.canh_bao.append("đề cương chưa có danh mục chữ viết tắt — hướng dẫn chung đòi có (bảng hai cột, không "
                           "viền); chủ nhiệm bổ sung")
    if vt is not None:
        out += ["", "---", "", "# DANH MỤC CÁC CHỮ VIẾT TẮT", ""] + [d for d in dong[vt.dong:vt.het]
                                                                     if d.strip() != "---"]
    ds_bb = [(f"{m.group(1)} {m.group(2)}", m.group(3)) for d in than_md + sau_md
             for m in [_CHU_THICH_MOI_RE.match(d.strip())] if m]
    if ds_bb:
        out += ["", "---", "", "# DANH MỤC CÁC BẢNG, BIỂU ĐỒ, HÌNH", "",
                "| Số thứ tự | Tên bảng, biểu đồ, hình |", "|---|---|"] + [f"| {a} | {b} |" for a, b in ds_bb]
    out += [""] + than_md + tl_md + sau_md
    van = "\n".join(out)
    van = re.sub(r"\n{3,}", "\n\n", van)
    van = re.sub(r"(?:---\n\n)+---", "---", van)
    kq.md = van.rstrip() + "\n"
    if ban_do_muc:
        kq.bao_cao.append(f"đánh số lại {len(ban_do_muc)} mục và {len(ban_do_bb)} bảng/hình/biểu đồ theo chương")
    for bo in ("tóm tắt",):
        if GB.tim_muc(cac_muc, bo):
            kq.bao_cao.append(f"bỏ mục «{bo}» (không có trong khuôn; nội dung đã có trong thân bài và mẫu thuyết minh)")
    return kq


# ── Ghi ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def xuat_word(md: str, docx_p: Path) -> Optional[str]:
    try:
        import md2docx_vn  # noqa: PLC0415
    except ImportError:
        return None
    md2docx_vn.markdown_to_docx(md, docx_p, khuon_bvqy175=True)
    return docx_p.as_posix()


def chay(study: str, out_dir: Path, ghi: bool = False, nam: Optional[int] = None) -> Dict[str, object]:
    md_p = out_dir / (TEN_DE_CUONG.format(study=study) + ".md")
    if not md_p.is_file():
        return {"ma": 2, "loi": f"thiếu {md_p.name}"}
    cu = md_p.read_text(encoding="utf-8")
    try:
        meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    kq = chuyen(cu, nam, don_vi_ho_so(meta))
    doi = kq.md != cu
    ra: Dict[str, object] = {"ma": 0, "study": study, "da_theo_khuon": kq.da_theo_khuon, "bao_cao": kq.bao_cao,
                             "canh_bao": kq.canh_bao, "so_dong_cu": cu.count("\n"), "so_dong_moi": kq.md.count("\n"),
                             "md": kq.md, "ghi": ghi, "doi": doi, "da_ghi": False}
    # 22/11/2026: văn bản đã theo khuôn vẫn được ghi khi lượt sửa hậu khuôn đổi nội dung (khối ký, tham chiếu chương)
    if not ghi or not doi:
        return ra
    sl = out_dir / "_sao_luu_de_cuong"
    sl.mkdir(parents=True, exist_ok=True)
    moc = datetime.now().strftime("%Y%m%dT%H%M%S")
    nhan = "truoc-sua-khuon" if kq.da_theo_khuon else "truoc-khuon"
    for duoi in (".md", ".docx"):
        p = out_dir / (TEN_DE_CUONG.format(study=study) + duoi)
        if p.is_file():
            shutil.copy2(p, sl / f"{p.stem}.{nhan}-{moc}{duoi}")
    md_p.write_text(kq.md, encoding="utf-8", newline="\n")
    ra["da_ghi"] = True
    ra["sao_luu"] = sl.as_posix()
    ra["docx"] = xuat_word(kq.md, out_dir / (TEN_DE_CUONG.format(study=study) + ".docx"))
    import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: PLC0415

    ra["loi_kiem"] = KDN.kiem(out_dir, study)
    ra["ma"] = 0 if not ra["loi_kiem"] else 1
    return ra


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Chuyển đề cương nộp sang khuôn hướng dẫn chung (BVQY175).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--exports-root", type=Path, default=BASE / "exports")
    ap.add_argument("--ghi", action="store_true", help="ghi (mặc định CHẠY KHÔ); sao lưu bản cũ trước")
    ap.add_argument("--xem", action="store_true", help="in toàn văn bản đã chuyển")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print(f"❌ mã đề tài không hợp lệ: {a.study!r}", file=sys.stderr)
        return 3
    ra = chay(a.study, a.exports_root / a.study, a.ghi)
    if "loi" in ra:
        print(f"❌ {ra['loi']}", file=sys.stderr)
        return int(ra["ma"])  # type: ignore[arg-type]
    if a.xem:
        print(ra["md"])
    if a.json:
        print(json.dumps({k: v for k, v in ra.items() if k != "md"}, ensure_ascii=False, indent=2))
        return int(ra["ma"])  # type: ignore[arg-type]
    print(f"KHUÔN ĐỀ CƯƠNG BVQY175 — {a.study}" + ("" if a.ghi else " (CHẠY KHÔ — chưa ghi gì)"))
    print(f"  {ra['so_dong_cu']} dòng ⇒ {ra['so_dong_moi']} dòng")
    for x in ra["bao_cao"]:  # type: ignore[union-attr]
        print(f"  • {x}")
    for x in ra["canh_bao"]:  # type: ignore[union-attr]
        print(f"  ⚠ {x}")
    if a.ghi and ra.get("da_ghi"):
        print(f"  Đã ghi; bản cũ sao lưu ở {ra.get('sao_luu')}")
        print(f"  Word: {ra.get('docx') or 'chưa xuất (thiếu python-docx)'}")
        loi = ra.get("loi_kiem") or []
        print(f"  Bộ kiểm đề cương nộp: {'ĐẠT' if not loi else f'{len(loi)} lỗi'}")  # type: ignore[arg-type]
        for x in list(loi)[:15]:  # type: ignore[arg-type]
            print(f"    ✗ {x}")
        print("  ⚠ Đề cương đổi ⇒ gói G10 đã khoá (nếu có) thành cũ: lắp lại G10 và PI ký lại.")
    elif a.ghi:
        print("  Không có gì để ghi (văn bản đã đúng khuôn).")
    elif ra.get("doi"):
        print("  Ghi thật: thêm --ghi. Xem toàn văn: --xem")
    print("  Cần bác sĩ kiểm chứng.")
    return int(ra["ma"])  # type: ignore[arg-type]


if __name__ == "__main__":
    sys.exit(main())
