#!/usr/bin/env python3
"""Gói chuẩn bị BẢO VỆ đề cương trước Hội đồng Khoa học/Đạo đức của bệnh viện — dàn slide + câu hỏi phản biện dự kiến.

VÌ SAO (21/11/2026, bác sĩ giao «hoàn thiện khoảng trống hệ nghiên cứu»): đối chiếu mã sống thì hệ G0–G10 dựng được
đề cương nộp Hội đồng, có biên bản hội đồng cổng (phản đối của `phan-bien-tranh-bien`, phán quyết của
`trong-tai-tranh-bien`) và báo cáo phản biện đề cương — nhưng KHÔNG có công cụ nào chuẩn bị cho buổi BẢO VỆ: không có
dàn slide 10–15 phút, không có bộ câu hỏi Hội đồng có thể hỏi. Công cụ này chỉ GOM và SẮP XẾP nguyên liệu đã có; nó
không triệu tập hội đồng, không gọi agent, không gọi API (CLAUDE.md §0.6).

Đầu ra (tên MỚI — không đè artifact hợp đồng nào; `exports/` bị .gitignore nên không vào git):
  exports/<mã>/GOI_BAO_VE_DAN_SLIDE_<mã>.md  (+ .docx)  — dàn slide theo đúng các mục của đề cương nộp;
  exports/<mã>/GOI_BAO_VE_CAU_HOI_<mã>.md    (+ .docx)  — câu hỏi phản biện dự kiến, mỗi câu ghi nguồn;
  exports/<mã>/GOI_BAO_VE_TRINH_CHIEU_<mã>.pptx         — tệp trình chiếu 16:9 dựng từ CHÍNH dàn slide (22/11/2026).
Word dựng bằng `tools/md_sang_docx_times.py` của REPO GỐC (Times New Roman, `--trang-de-cuong`: mỗi slide một trang);
.pptx dựng bằng python-pptx (requirements.txt).

Nguồn CHỈ ĐỌC: `DE_CUONG_NOP_HOI_DONG_<mã>.md`, `hoi_dong/G*/` (biên bản tranh biện, biên bản xử lý việc sửa, sổ
quyết định bác sĩ), `hoi_dong_khoa_hoc/QUYET_DINH_HOI_DONG_*.md` (sổ quyết định có căn cứ của hội đồng nghiên cứu),
`PHAN_BIEN_DE_CUONG_NOP*_<mã>.md` (bản mới nhất), `G3_checkpoint.json` (N đã chốt), `bieu-bang/` (hình của đề cương).

Luật:
  S1  Mỗi slide trỏ đúng mục và số dòng đề cương; nội dung là CÂU NGUYÊN VĂN chọn từ mục đó — không cắt câu, không
      viết câu mới, không thêm số. Mục không tìm thấy ⇒ slide ghi rõ «không tìm thấy», máy không tự soạn.
  S2  N đã chốt ở G3 phải có trên slide cỡ mẫu: không nằm trong các câu đã chọn thì thêm câu đầu tiên của mục chứa N;
      đề cương không có N ⇒ cảnh báo trong ghi chú người trình bày.
  Q1  Câu hỏi từ biên bản: chỉ luận điểm của BÊN PHẢN BIỆN (bỏ luận điểm nhường) trong biên bản tranh biện đọc được.
      Lượt mới nhất của mỗi điểm quyết định ở phần chính; lượt cũ hơn ở phụ lục.
  Q2  Gợi ý trả lời chỉ CHÉP NGUYÊN VĂN từ biên bản/đề cương (lý do trọng tài, luận điểm được giữ, giải pháp hội đồng
      khuyến nghị, quyết định bác sĩ đã ghi sổ, câu đề cương đã sửa) — không viết câu trả lời mới.
  Q3  Trọng tài «sửa kết luận» ⇒ kèm phần đã sửa trong đề cương lấy từ biên bản xử lý việc sửa, XÁC MINH mẫu còn có
      trong đề cương hiện hành (không còn ⇒ cảnh báo, không trình như đã sửa).
  Q4  Đề tài chưa có biên bản tranh biện ⇒ nói rõ; câu hỏi lấy từ báo cáo phản biện + mục hạn chế/sai số của đề cương,
      ghi nhãn từng nhóm.
  Q5  Sổ quyết định của hội đồng nghiên cứu: mỗi mục «### <mã> — <vấn đề>» là một câu (nhóm D), gợi ý chép NGUYÊN VĂN
      quyết định và căn cứ; phần «Mới» thay vào đề cương nộp được đối chiếu với bản hiện hành (không còn ⇒ cảnh báo).
  S3  Tệp trình chiếu: mỗi trang là slide của dàn (câu nguyên văn, chân trang + ghi chú trỏ mục/dòng), bảng nguồn thành
      bảng thật, hình `bieu-bang/` nhúng đúng tệp; chữ thân ≥ 18 pt; khung chữ đo bằng phông thật, không vừa thì sang
      trang «(tiếp)»; `kiem_pptx` mở lại tệp và kiểm số trang, nguồn, ảnh, nguyên văn, tràn khung.
  P1  Quét mẫu định danh (SĐT · CCCD · email — cùng bộ mẫu biên bản hội đồng dùng) trên cả hai đầu ra; có ⇒ KHÔNG ghi.

Ranh giới: TƯ VẤN cho chủ nhiệm — không sửa đề cương/biên bản/sổ cái, không ký, không mở/chặn cổng. Nội dung chuyên
môn chỉ là gợi ý; chủ nhiệm tự diễn đạt câu trả lời và kiểm lại với đề cương hiện hành.

Lệnh:
  python3 tools/goi_bao_ve_hoi_dong.py --study <mã> [--xem] [--json]          # CHẠY KHÔ (mặc định): không ghi gì
  python3 tools/goi_bao_ve_hoi_dong.py --study <mã> --ghi [--khong-word]       # ghi vào exports/<mã>/
  python3 tools/goi_bao_ve_hoi_dong.py --study <mã> --ghi --thu-muc-ra <dir>   # ghi bản xem thử ra thư mục khác
Mã thoát: 0 xong · 1 đã ghi .md nhưng chưa xuất được Word hoặc tệp trình chiếu chưa đạt kiểm · 2 thiếu đề cương nộp ·
3 tham số sai / đầu ra có mẫu PII.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import clinical_checkpoint as CC  # noqa: E402  (một bộ mẫu PII dùng chung với biên bản hội đồng)
import hoi_dong_cong as HD  # noqa: E402

TEN_DE_CUONG = "DE_CUONG_NOP_HOI_DONG_{study}.md"
TEN_SLIDE = "GOI_BAO_VE_DAN_SLIDE_{study}.md"
TEN_CAU_HOI = "GOI_BAO_VE_CAU_HOI_{study}.md"
MAU_BAO_CAO = "PHAN_BIEN_DE_CUONG_NOP*_{study}.md"
CONG_CU_WORD = "md_sang_docx_times.py"
LOI_DAN = "Cần bác sĩ kiểm chứng."

_DE_MUC_RE = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")
_SO_MUC_RE = re.compile(r"^((?:PHỤ LỤC\s+[A-Z])|(?:CHƯƠNG\s+\d+)|\d+(?:\.\d+)*)\.?\s+(.*)$")
_HOA = "A-ZĐÂĂÊÔƠƯÁÀẢÃẠẤẦẨẪẬẮẰẲẴẶÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
_HET_CAU_RE = re.compile(r"(?<=[.!?…])\s+(?=[" + _HOA + r"“\"«(\[*])")
_MUC_DS_RE = re.compile(r"^\s*(?:[-*+]|\d{1,2}[.)]|[a-zđ][.)])\s+(.*\S)\s*$")
_CHU_THICH_BANG_RE = re.compile(r"^\**\s*(?:Bảng|Hình|Biểu đồ|Sơ đồ)\s+\d", re.IGNORECASE)
_GHI_CHU_RE = re.compile(r"^\*?\s*(?:Ghi chú|Chú thích)\s*:", re.IGNORECASE)
_DOI_URL_RE = re.compile(r"(?:\bdoi:\s*)?\b10\.\d{4,9}/\S+|https?://\S+", re.IGNORECASE)
_MUC_DO = ("🔴", "🟠", "🟢")


# ── Đọc đề cương ─────────────────────────────────────────────────────────────────────────────────────────────────────

def _chuan(s: str) -> str:
    """Chuẩn hoá để so khớp tiêu đề: NFC + chữ thường + gộp khoảng trắng."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip().casefold()


@dataclass
class Muc:
    """Một đề mục của đề cương: cấp, số hiệu, tên (bỏ số), dòng tiêu đề, dòng cuối của toàn mục (gồm mục con)."""
    cap: int
    so: str
    ten: str
    dong: int
    het: int

    @property
    def nhan(self) -> str:
        return f"mục {self.so} «{self.ten}»" if self.so else f"mục «{self.ten}»"


def doc_muc(dong: Sequence[str]) -> List[Muc]:
    """Danh sách đề mục `#`–`####` theo thứ tự; `het` = dòng trước đề mục kế tiếp cùng cấp hoặc cấp cao hơn."""
    tho: List[Tuple[int, str, int]] = []
    for i, d in enumerate(dong, 1):
        m = _DE_MUC_RE.match(d)
        if m:
            tho.append((len(m.group(1)), m.group(2).strip(), i))
    ra: List[Muc] = []
    for k, (cap, tieu_de, i) in enumerate(tho):
        het = len(dong)
        for cap2, _t, j in tho[k + 1:]:
            if cap2 <= cap:
                het = j - 1
                break
        m = _SO_MUC_RE.match(tieu_de)
        so, ten = (m.group(1), m.group(2).strip()) if m else ("", tieu_de)
        ra.append(Muc(cap, so, ten, i, het))
    return ra


def tim_muc(cac_muc: Sequence[Muc], mau: Any) -> Optional[Muc]:
    """Đề mục đầu tiên có tên (đã bỏ số) khớp biểu thức `mau` (so trên chuỗi đã chuẩn hoá). `mau` là bộ nhiều biểu
    thức ⇒ thử LẦN LƯỢT từng biểu thức (biểu thức trước thắng dù đề mục khớp biểu thức sau đứng trước trong văn bản)."""
    for x in (mau if isinstance(mau, (tuple, list)) else (mau,)):
        bt = re.compile(x)
        m = next((m for m in cac_muc if bt.search(_chuan(m.ten))), None)
        if m is not None:
            return m
    return None


_TEN_TRONG_NGOAC_RE = re.compile(r"“\*\*(.+?)\*\*”")


def ten_de_tai(dong: Sequence[str], cac_muc: Sequence[Muc]) -> Tuple[str, int]:
    """(tên đề tài, số dòng): khuôn hướng dẫn chung ghi tên trong ngoặc kép in đậm ở đặt vấn đề; cấu trúc cũ là đề
    mục cấp 2 đầu tiên."""
    dvd = tim_muc(cac_muc, r"^đặt vấn đề$")
    if dvd is not None:
        for i in range(dvd.dong, dvd.het + 1):
            m = _TEN_TRONG_NGOAC_RE.search(dong[i - 1])
            if m:
                return m.group(1).strip(), i
    dau = next((m for m in cac_muc if m.cap == 2), None)
    return (dau.ten, dau.dong) if dau else ("", 0)


@dataclass
class Cau:
    """Một câu (hoặc một mục danh sách, một ô bảng) NGUYÊN VĂN của đề cương, kèm số dòng.

    `phu`: ô thứ hai NGUYÊN VĂN cùng hàng bảng (cột «Biện pháp khống chế») — hiển thị sau nhãn, không ghép thành câu
    mới."""
    van: str
    dong: int
    la_muc_ds: bool = False
    dau_doan: bool = False
    phu: str = ""
    # tiêu đề NGUYÊN VĂN của hai cột bảng nguồn (ô đầu, cột «biện pháp») — tệp trình chiếu dựng lại bảng thật
    cot: Tuple[str, str] = ("", "")


def tach_cau(van: str) -> List[str]:
    """Tách câu ở dấu kết câu theo sau là chữ HOA/ngoặc mở — giữ nguyên văn, không cắt giữa câu."""
    return [c.strip() for c in _HET_CAU_RE.split(van.strip()) if c.strip()]


def cau_cua_muc(dong: Sequence[str], muc: Muc) -> List[Cau]:
    """Mọi câu/mục danh sách trong thân mục (gồm mục con), bỏ bảng, chú thích bảng, ghi chú, trích dẫn khối, đề mục."""
    ra: List[Cau] = []
    for i in range(muc.dong + 1, muc.het + 1):
        d = dong[i - 1].rstrip()
        s = d.strip()
        if (not s or s.startswith(("|", ">", "#", "<!--", "![", "```")) or set(s) <= set("-*_ ")
                or _CHU_THICH_BANG_RE.match(s) or _GHI_CHU_RE.match(s)):
            continue
        m = _MUC_DS_RE.match(d)
        if m:
            ra.append(Cau(m.group(1).strip(), i, la_muc_ds=True))
            continue
        for k, c in enumerate(tach_cau(s)):
            ra.append(Cau(c, i, dau_doan=(k == 0)))
    return ra


def cau_cua_bang(dong: Sequence[str], muc: Muc) -> List[Cau]:
    """Hàng của BẢNG ĐẦU TIÊN trong mục: ô đầu (vd «Nguồn sai lệch») + ô cột «biện pháp» nếu có — nguyên văn từng ô."""
    for i in range(muc.dong + 1, muc.het):
        s = dong[i - 1].strip()
        if not (s.startswith("|") and re.match(r"^\|[\s:|-]+\|?\s*$", dong[i].strip())):
            continue
        goc = [o.strip() for o in s.strip("|").split("|")]
        dau = [_chuan(o) for o in goc]
        k_bp = next((k for k, o in enumerate(dau) if "biện pháp" in o), None)
        cot = (goc[0], goc[k_bp] if k_bp is not None else "")
        ra: List[Cau] = []
        j = i + 2
        while j <= muc.het and dong[j - 1].strip().startswith("|"):
            o = [x.strip() for x in dong[j - 1].strip().strip("|").split("|")]
            if o and o[0]:
                ra.append(Cau(o[0], j, phu=o[k_bp] if k_bp is not None and k_bp < len(o) else "", cot=cot))
            j += 1
        return ra
    return []


def _dinh_dang_n(n: int) -> Tuple[str, ...]:
    """Các cách viết N trong văn bản tiếng Việt: «1000», «1.000», «1 000»."""
    return tuple(dict.fromkeys((str(n), f"{n:,}".replace(",", "."), f"{n:,}".replace(",", " "))))


def _co_so(van: str, n: int) -> bool:
    return any(re.search(r"(?<![\d.,])" + re.escape(c) + r"(?![\d]|[.,]\d)", van) for c in _dinh_dang_n(n))


def n_da_chot(out_dir: Path) -> Optional[int]:
    """N đã chốt của G3 (cùng quy tắc K5 của kiem_de_cuong_nop_hoi_dong): confirmed_n, không có thì n_adjusted."""
    try:
        g3 = json.loads((out_dir / "G3_checkpoint.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    n = g3.get("confirmed_n") if g3.get("confirmed_n") not in (None, "") else g3.get("n_adjusted")
    try:
        return int(n) if n not in (None, "") else None
    except (TypeError, ValueError):
        return None


# ── Dàn slide ────────────────────────────────────────────────────────────────────────────────────────────────────────

# (khoá, tiêu đề slide, phút, [(nhãn phụ, mẫu tên đề mục, cách chọn, số câu, mẫu câu ưu tiên)]) — thứ tự theo trình tự
# bảo vệ: đặt vấn đề → mục tiêu → phương pháp → cỡ mẫu → đạo đức → kế hoạch. Tổng 14 phút (khung 10–15 phút).
# Cách chọn: «dau» các câu đầu · «dau_doan» câu đầu mỗi đoạn · «danh_sach» mục danh sách · «co_so» câu có số trước ·
# «bang» hàng bảng đầu tiên (ô đầu + cột «biện pháp»), mục không có bảng thì quay về «dau».
_UU_TIEN_KHOANG_TRONG = r"^\**\s*(?:khoảng trống|đóng góp)|khoảng trống của (?:đề tài|nghiên cứu)|đóng góp của đề tài"
KHUON_SLIDE: Tuple[Tuple[str, str, float, Tuple[Tuple[Optional[str], str, str, int, Optional[str]], ...]], ...] = (
    ("ten_de_tai", "Tên đề tài", 0.5, ()),
    ("dat_van_de", "Đặt vấn đề", 1.5, ((None, r"^đặt vấn đề$", "dau_doan", 4, None),)),
    ("khoang_trong", "Khoảng trống nghiên cứu và đóng góp", 1.0,
     ((None, r"khoảng trống", "dau", 3, _UU_TIEN_KHOANG_TRONG),)),
    ("muc_tieu", "Mục tiêu nghiên cứu", 1.0, (("Mục tiêu", (r"^mục tiêu$", r"^mục tiêu nghiên cứu$"), "danh_sach", 5,
                                               None),
                                              ("Giả thuyết", r"^giả thuyết", "dau", 2, None))),
    ("thiet_ke", "Thiết kế, địa điểm và thời gian", 1.0, (
        ("Thiết kế", r"^thiết kế nghiên cứu$", "dau", 2, None),
        ("Địa điểm và thời gian", r"^địa điểm và thời gian", "dau", 2, None))),
    ("doi_tuong", "Đối tượng nghiên cứu", 1.0, (
        ("Tiêu chuẩn lựa chọn", r"^tiêu chuẩn lựa chọn$", "danh_sach", 4, None),
        ("Tiêu chuẩn loại trừ", r"^tiêu chuẩn loại trừ$", "danh_sach", 3, None))),
    ("co_mau", "Cỡ mẫu", 1.5, ((None, r"^cỡ mẫu$", "co_so", 5, None),)),
    ("chon_mau", "Phương pháp chọn mẫu", 0.5, ((None, r"^phương pháp chọn mẫu$", "dau", 3, None),)),
    ("bien_so", "Biến số và công cụ thu thập", 1.0, (("Biến số", r"^biến số", "dau", 2, None),
                                                     ("Công cụ", r"^công cụ.*thu thập", "dau", 2, None))),
    ("phan_tich", "Xử lý và phân tích số liệu", 1.5, ((None, r"^xử lý và phân tích", "dau", 4, None),)),
    ("sai_so", "Sai số và hạn chế", 1.0, (("Sai số và biện pháp khống chế", r"^sai số", "bang", 4, None),
                                          ("Hạn chế", r"^hạn chế", "dau", 2, None))),
    ("dao_duc", "Đạo đức trong nghiên cứu", 1.0, ((None, r"^đạo đức", "dau", 4, None),)),
    ("ke_hoach", "Kế hoạch thực hiện", 1.0, (("Tiến độ", r"^tiến độ", "dau", 2, None),
                                             ("Nhân lực", r"^nhân lực", "dau", 1, None),
                                             ("Kinh phí", r"kinh phí", "dau", 1, None))),
    ("du_kien", "Dự kiến kết quả và phổ biến", 0.5, (("Dự kiến kết quả", r"^dự kiến kết quả", "dau", 2, None),
                                                     ("Dự kiến bàn luận", r"^dự kiến bàn luận", "dau", 2, None),
                                                     ("Phổ biến", r"phổ biến", "dau", 1, None))),
)
# Khối chỉ có ở đề cương theo khuôn hướng dẫn chung (Chương 3 «Dự kiến kết quả và bàn luận») — vắng thì bỏ qua, không
# cảnh báo (đề cương cấu trúc cũ không có phần bàn luận).
KHOI_TUY_CHON = {"Dự kiến bàn luận"}
DAI_UU_TIEN = 350  # câu dài hơn vẫn giữ NGUYÊN (không cắt) nhưng chỉ lấy khi thiếu câu ngắn hơn


def _de_dung(c: Cau) -> bool:
    """Câu dùng tốt trên slide: không quá dài, không treo ở dấu hai chấm (câu dẫn vào bảng/công thức), không chỉ là
    nhãn in đậm đứng một mình («**Quần thể phân tích.**»)."""
    v = c.van.strip()
    return len(v) <= DAI_UU_TIEN and not v.endswith(":") and not re.fullmatch(r"\*\*[^*]+\*\*", v)


def chon_cau(cac_cau: Sequence[Cau], cach: str, so: int, uu_tien: Optional[str] = None) -> List[Cau]:
    """Chọn ≤ `so` câu NGUYÊN VĂN theo cách chọn, giữ thứ tự xuất hiện trong đề cương.

    `uu_tien`: câu khớp mẫu (so trên chữ thường) được xét TRƯỚC mọi câu khác, kể cả khi dài — đúng nội dung quan trọng
    hơn độ ngắn (đo C1a 21/11: câu «Khoảng trống của đề tài…» dài 661 ký tự từng bị câu «Giới hạn…» chen chỗ)."""
    if cach == "danh_sach":
        ung = [c for c in cac_cau if c.la_muc_ds] or [c for c in cac_cau if c.dau_doan]
    elif cach == "dau_doan":  # chỉ câu mở đoạn văn xuôi (không lấy danh sách — vd danh sách mục tiêu cuối đặt vấn đề)
        ung = [c for c in cac_cau if c.dau_doan] or [c for c in cac_cau if c.la_muc_ds]
    elif cach == "co_so":
        co = [c for c in cac_cau if re.search(r"\d", c.van)]
        ung = co + [c for c in cac_cau if c not in co]
    else:  # «dau» (và «bang» đã đổi thành hàng bảng ở nơi gọi): các câu đầu tiên
        ung = list(cac_cau)
    dau: List[Cau] = []
    if uu_tien:
        bt = re.compile(uu_tien)
        khop = [c for c in cac_cau if bt.search(_chuan(c.van))]
        doan = {c.dong for c in khop}  # chỗ còn trống lấp bằng câu CÙNG ĐOẠN với câu ưu tiên trước câu nơi khác
        cung_doan = [c for c in ung if c.dong in doan and c not in khop]
        dau = ([c for c in khop if _de_dung(c)] + [c for c in khop if not _de_dung(c)]
               + [c for c in cung_doan if _de_dung(c)])
        ung = [c for c in ung if c not in dau]
    thu_tu = dau + [c for c in ung if _de_dung(c)] + [c for c in ung if not _de_dung(c)]
    return sorted(thu_tu[:so], key=lambda c: (c.dong, cac_cau.index(c)))


@dataclass
class Slide:
    so: int
    khoa: str
    tieu_de: str
    phut: float
    khoi: List[Tuple[Optional[str], List[Cau]]] = field(default_factory=list)
    nguon: List[str] = field(default_factory=list)
    canh_bao: List[str] = field(default_factory=list)


def dung_slide(dong: Sequence[str], out_dir: Path) -> Tuple[List[Slide], str]:
    """(danh sách slide, tên đề tài). Mọi câu trên slide là câu nguyên văn của đề cương (luật S1, S2)."""
    cac_muc = doc_muc(dong)
    ten, dong_ten = globals()["ten_de_tai"](dong, cac_muc)
    n = n_da_chot(out_dir)
    ra: List[Slide] = []
    for so, (khoa, tieu_de, phut, phan) in enumerate(KHUON_SLIDE, 1):
        sl = Slide(so, khoa, tieu_de, phut)
        if khoa == "ten_de_tai":
            if ten:
                sl.khoi.append((None, [Cau(ten, dong_ten)]))
                sl.nguon.append(f"tên đề tài ở dòng {dong_ten}")
            else:
                sl.canh_bao.append("không tìm thấy tên đề tài (đề mục cấp 2 đầu tiên) — chủ nhiệm tự điền")
            ra.append(sl)
            continue
        for nhan_phu, mau, cach, so_cau, uu_tien in phan:
            muc = tim_muc(cac_muc, mau)
            if muc is None and nhan_phu in KHOI_TUY_CHON:
                continue
            if muc is None:
                sl.canh_bao.append(f"không tìm thấy mục «{nhan_phu or tieu_de}» trong đề cương — chủ nhiệm tự soạn "
                                   "phần này (máy không tự viết)")
                continue
            hang = cau_cua_bang(dong, muc) if cach == "bang" else []
            if hang:
                chon = hang[:so_cau]
                cac_cau = hang
            else:
                # câu chừa dòng chấm «………» cho chủ nhiệm điền (vd «Các ý bàn luận chính do chủ nhiệm bổ sung: ………»)
                # chưa phải nội dung — không đưa lên slide
                cac_cau = [c for c in cau_cua_muc(dong, muc) if "………" not in c.van]
                if khoa == "dat_van_de":
                    # khuôn hướng dẫn chung: mục tiêu là mục con ở cuối đặt vấn đề — slide đặt vấn đề chỉ lấy phần thân
                    # trước mục con, bỏ câu chuyển ý mang tên đề tài («…tiến hành đề tài “**…**” với các mục tiêu sau:»)
                    con = next((m.dong for m in cac_muc if muc.dong < m.dong <= muc.het and m.cap > muc.cap), None)
                    cac_cau = [c for c in cac_cau if (con is None or c.dong < con) and "“**" not in c.van]
                chon = chon_cau(cac_cau, "dau" if cach == "bang" else cach, so_cau, uu_tien)
            if khoa == "co_mau" and n is not None and not any(_co_so(c.van, n) for c in chon):
                co_n = next((c for c in cac_cau if _co_so(c.van, n)), None)
                if co_n is not None:
                    chon = sorted(chon + [co_n], key=lambda c: c.dong)
                else:
                    sl.canh_bao.append(f"N đã chốt ở G3 ({_dinh_dang_n(n)[-1]}) không có trong mục cỡ mẫu của đề "
                                       "cương — đối chiếu lại trước khi trình bày")
            if not chon:
                sl.canh_bao.append(f"{muc.nhan} không có câu văn xuôi hay bảng để chọn — chủ nhiệm tự chọn ý")
            sl.khoi.append((nhan_phu, chon))
            dong_chon = ", ".join(dict.fromkeys(str(c.dong) for c in chon)) or "—"
            sl.nguon.append(f"{muc.nhan}, dòng {muc.dong}–{muc.het}; "
                            + ("hàng bảng" if hang else "câu chọn") + f" ở dòng {dong_chon}")
        ra.append(sl)
    return ra, ten


def _phut(x: float) -> str:
    return (f"{x:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


def _bo_nhan_manh(v: str) -> str:
    """«***Mục tiêu…***» (mục tiêu in nghiêng đậm theo khuôn hướng dẫn chung) ⇒ chữ trơn trên slide."""
    return re.sub(r"^\*{3}(.+)\*{3}$", r"\1", v.strip())


def render_slide(slides: Sequence[Slide], ten_de_tai: str, ten_dc: str, so_dong: int, sha: str) -> str:
    tong = sum(s.phut for s in slides)
    out = ["# DÀN SLIDE BẢO VỆ ĐỀ CƯƠNG TRƯỚC HỘI ĐỒNG", "", f"**{ten_de_tai}**" if ten_de_tai else "", "",
           f"Tổng thời lượng dự kiến: khoảng {_phut(tong)} phút · {len(slides)} slide.", "",
           "Tài liệu chuẩn bị NỘI BỘ cho chủ nhiệm đề tài — không nộp Hội đồng. Mỗi gạch đầu dòng là câu NGUYÊN VĂN "
           "chọn từ đề cương nộp (không cắt câu, không thêm số); khi dựng slide thật, chủ nhiệm rút gọn bằng cách "
           "chọn ý và giữ nguyên số liệu. Ghi chú dưới mỗi slide trỏ đúng mục và số dòng của đề cương.", "",
           f"Nguồn: `{ten_dc}` ({so_dong} dòng, mã băm SHA-256 bắt đầu bằng {sha[:12]}), đọc ngày "
           f"{datetime.now().strftime('%d/%m/%Y')}.", "", f"*{LOI_DAN}*", "", "---", ""]
    for s in slides:
        out += [f"## Slide {s.so}. {s.tieu_de} (khoảng {_phut(s.phut)} phút)", ""]
        if s.khoa == "ten_de_tai":
            out += [f"- {c.van}" for _n, ds in s.khoi for c in ds]
            out += ["- Chủ nhiệm đề tài: ……………………… (điền tay)", "- Đơn vị: ……………………… (điền tay)", ""]
        else:
            for nhan_phu, ds in s.khoi:
                if nhan_phu:
                    out += [f"**{nhan_phu}**", ""]
                out += [f"- {_bo_nhan_manh(c.van)}" + (f" — biện pháp: {c.phu}" if c.phu else "") for c in ds] + [""]
        ghi = ["> Ghi chú người trình bày — nguồn: " + ("; ".join(s.nguon) if s.nguon else "không có") + "."]
        ghi += [f"> ⚠ {c}." for c in s.canh_bao]
        out += ghi + ["", "---", ""]
    while out and out[-1] in ("", "---"):
        out.pop()
    return "\n".join(out) + "\n"


# ── Câu hỏi từ biên bản hội đồng cổng ────────────────────────────────────────────────────────────────────────────────

KET_PHAN_QUYET = {"chap_nhan": "Chấp nhận", "bac": "Bác", "chua_du_can_cu": "Chưa đủ căn cứ"}
KET_QUA_TB = {"giu_ket_luan": "giữ kết luận", "sua_ket_luan": "sửa kết luận", "chuyen_bac_si": "chuyển bác sĩ"}
CACH_XU_LY = {"da_sua": "đã sửa", "chuyen_pi": "chuyển PI", "khong_sua_co_ly_do": "không sửa, có lý do"}


@dataclass
class GoiY:
    """Một dòng gợi ý trả lời: nhãn (chữ của công cụ) + đoạn NGUYÊN VĂN chép từ nguồn (rỗng nếu chỉ là ghi chú)."""
    nhan: str
    trich: str = ""
    canh_bao: bool = False


@dataclass
class CauHoi:
    ma: str
    nhom: str  # A biên bản · B báo cáo phản biện · C đề cương
    tieu_de: str
    chat_van: str  # NGUYÊN VĂN từ nguồn
    nguon: str
    goi_y: List[GoiY] = field(default_factory=list)
    muc_do: str = ""
    noi_bo: List[str] = field(default_factory=list)  # các loại ký hiệu nội bộ gặp trong chat_van


# Phân loại «thiên về quy trình NỘI BỘ của hệ thống» (21/11/2026). Hội đồng cổng xét cả đầu ra của công cụ/agent: nhiều
# phản đối bàn về checkpoint, cờ dòng lệnh, bộ chấm… — Hội đồng Khoa học/Đạo đức bệnh viện không hỏi những điều đó.
# Đo trên 41 phản đối thật của C1a + BTM: phản đối về khoa học/đạo đức chứa 0–3 LOẠI ký hiệu dưới đây; phản đối về công
# cụ/checkpoint chứa 4–11 loại. Ngưỡng 4 loại. Phản đối nội bộ KHÔNG bị bỏ — chuyển sang mục riêng để tra.
_KY_HIEU_NOI_BO: Tuple[Tuple[str, str], ...] = (
    ("tệp mã .py", r"\b\w+\.py\b"),
    ("checkpoint", r"checkpoint"),
    ("study_meta/gate_params", r"study_meta|gate_params"),
    ("tên agent", r"\bagent\b|dieu-phoi|giam-khao|phan-bien-tranh|trong-tai|thu-thu-tai-lieu|cong-cu-do-luong"),
    ("pipeline", r"\bpipeline\b|run_g\d|run_pipeline"),
    ("cờ dòng lệnh", r"(?<![\w-])--[a-z][a-z-]+"),
    ("mã tiêu chí/nhiệm vụ cổng", r"\bG\d{1,2}-(?:AUTO|HUMAN|OPS|T\d)"),
    ("mã rubric", r"\bRQ\d\b"),
    ("định danh máy", r"\b[a-z]+_[a-z0-9_]{2,}\b"),
    ("PR/commit", r"\bPR\b|\bcommit\b"),
    ("tệp json/csv", r"\.json\b|\.csv\b"),
    ("bộ chấm", r"cham-song|bộ chấm|chấm sống|quality_gate|mtime"),
)
NGUONG_NOI_BO = 4


def loai_noi_bo(van: str) -> List[str]:
    """Các LOẠI ký hiệu nội bộ có trong văn bản; ≥ NGUONG_NOI_BO loại ⇒ thiên về quy trình nội bộ."""
    return [ten for ten, mau in _KY_HIEU_NOI_BO if re.search(mau, van)]


def la_noi_bo(van: str) -> bool:
    return len(loai_noi_bo(van)) >= NGUONG_NOI_BO


@dataclass
class NhomBienBan:
    """Một biên bản tranh biện + phần chung (kết luận cuối, giải pháp, phần đã sửa, quyết định bác sĩ)."""
    gate: str
    id: str
    dp: str
    dp_cau_hoi: str
    ngay: str
    ket_qua: str
    trang_thai: str
    chung: List[GoiY] = field(default_factory=list)
    cau: List[CauHoi] = field(default_factory=list)
    so_nhuong: int = 0
    cu_hon: Optional[str] = None  # id lượt mới hơn của cùng điểm quyết định (biên bản này vào phụ lục)


def _ngay(moc: Any) -> str:
    try:
        return datetime.fromisoformat(str(moc)).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return "không rõ ngày"


def _trang_thai_bien_ban(bb: Dict[str, Any], out_dir: Path) -> str:
    try:
        kq = HD.kiem_bien_ban(bb, out_dir)
    except Exception as exc:  # biên bản lạ không được làm hỏng cả gói — ghi rõ, không im lặng
        return f"không kiểm được ({type(exc).__name__})"
    if not kq.get("hop_le"):
        return "biên bản có lỗi cấu trúc — đọc thận trọng (" + "; ".join(kq.get("loi", [])[:2]) + ")"
    if kq.get("cu"):
        return "tài liệu được xét đã đổi sau buổi họp (biên bản cũ) — đối chiếu lại với đề cương hiện hành"
    return "còn hiệu lực"


_TEP_CC_RE = re.compile(r"^(?P<tep>[^:§\s]+?\.md)\s*(?P<con>.*)$")


def _cau_chua(van: str, mau: str) -> str:
    """Các câu NGUYÊN VĂN của một dòng có chứa `mau`; mẫu vắt qua ranh giới câu thì trả cả dòng."""
    s = van.strip().strip("|").strip()
    ds = [c for c in tach_cau(s) if mau in c]
    return " ".join(ds) if ds else s


def xac_minh_trich_de_cuong(cc: Dict[str, Any], dong: Sequence[str], ten_dc: str,
                            cac_muc: Sequence[Muc]) -> Optional[List[GoiY]]:
    """Căn cứ tệp trỏ vào đề cương nộp ⇒ các dòng gợi ý đã XÁC MINH trên đề cương hiện hành (luật Q3); khác ⇒ None."""
    m = _TEP_CC_RE.match(str(cc.get("gia_tri") or "").strip())
    if not m or Path(m.group("tep")).name != ten_dc:
        return None
    con = m.group("con").strip().lstrip(":").strip()
    ra: List[GoiY] = []
    mau, khong = cc.get("mau"), cc.get("khong_chua")
    if isinstance(mau, str) and mau.strip():
        trung = [i for i, d in enumerate(dong, 1) if mau in d]
        for i in trung[:2]:
            ra.append(GoiY(f"Đề cương hiện hành, dòng {i}:", _cau_chua(dong[i - 1], mau)))
        if not trung:
            ra.append(GoiY(f"⚠ Mẫu biên bản xử lý dẫn («{mau}», trỏ «{con or 'cả tệp'}») KHÔNG còn trong đề cương "
                           "hiện hành — đề cương đã đổi sau lần sửa; chủ nhiệm kiểm lại trước khi trả lời.",
                           canh_bao=True))
    if isinstance(khong, str) and khong.strip():
        con_trong = any(khong in d for d in dong)
        ra.append(GoiY("Câu đã gỡ khỏi đề cương" + (" — ⚠ nhưng VẪN CÒN trong đề cương hiện hành:" if con_trong
                                                     else " (xác minh: không còn trong đề cương hiện hành):"),
                       khong, canh_bao=con_trong))
    if not ra:
        so = re.match(r"(\d+)(?:-(\d+))?", con)
        if so:
            i = int(so.group(1))
            if 1 <= i <= len(dong) and dong[i - 1].strip():
                cau = tach_cau(dong[i - 1].strip().strip("|").strip())
                ra.append(GoiY(f"Đề cương hiện hành, dòng {i} (biên bản chỉ trỏ số dòng lúc sửa — chưa xác minh "
                               "nguyên văn; câu đầu của dòng):", cau[0] if cau else ""))
            else:
                ra.append(GoiY(f"⚠ Biên bản trỏ dòng {con} nhưng dòng đó không còn nội dung trong đề cương hiện hành.",
                               canh_bao=True))
        else:
            ms = re.search(r"§\s*(\d+(?:\.\d+)*)", con)
            muc = next((x for x in cac_muc if ms and x.so == ms.group(1)), None)
            ra.append(GoiY(f"Biên bản trỏ {muc.nhan if muc else (con or 'cả tệp')} của đề cương (không kèm mẫu "
                           "nguyên văn) — chủ nhiệm đọc lại mục này."))
    return ra


def _phan_da_sua(tb: Dict[str, Any], xls: Sequence[Dict[str, Any]], dong: Sequence[str], ten_dc: str,
                 cac_muc: Sequence[Muc]) -> List[GoiY]:
    """Phần đã sửa theo biên bản xử lý MỚI NHẤT của biên bản tranh biện này (chỉ việc sửa của trọng tài)."""
    cua_tb = [b for b in xls if b.get("bien_ban_goc") == tb.get("id")]
    if not cua_tb:
        return [GoiY("⚠ Chưa có biên bản xử lý việc sửa cho biên bản này — chưa có bằng chứng phần đề cương đã sửa; "
                     "chủ nhiệm chuẩn bị câu trả lời hoặc sửa đề cương.", canh_bao=True)]
    xl = max(cua_tb, key=lambda b: HD._moc_thoi_gian(b.get("thoi_diem")))
    ra = [GoiY(f"Theo biên bản xử lý {xl.get('id')} (ngày {_ngay(xl.get('thoi_diem'))}):")]
    for v in xl.get("viec") or []:
        if not isinstance(v, dict) or not str(v.get("nguon") or "").startswith(("viec_sua", "chuyen_bac_si")):
            continue
        cach = CACH_XU_LY.get(str(v.get("cach_xu_ly")), str(v.get("cach_xu_ly")))
        dc: List[GoiY] = []
        khac: List[str] = []
        for cc in v.get("can_cu") or []:
            if not isinstance(cc, dict) or cc.get("loai") != "tep":
                continue
            kq = xac_minh_trich_de_cuong(cc, dong, ten_dc, cac_muc)
            if kq is None:
                tm = _TEP_CC_RE.match(str(cc.get("gia_tri") or "").strip())
                khac.append(Path(tm.group("tep")).name if tm else str(cc.get("gia_tri")))
            else:
                dc += kq
        ra.append(GoiY(f"Việc sửa «{v.get('nguon')}» ({cach}):", str(v.get("noi_dung") or "")))
        if dc or str(v.get("cach_xu_ly")) != "da_sua":
            if v.get("mo_ta"):
                ra.append(GoiY("Mô tả của biên bản xử lý:", str(v["mo_ta"])))
        da_co = {(g.nhan, g.trich) for g in ra}  # hai mẫu của cùng việc sửa có thể rơi vào CÙNG một câu đề cương
        for g in dc:
            if (g.nhan, g.trich) not in da_co:
                ra.append(g)
                da_co.add((g.nhan, g.trich))
        if khac and not dc:
            ra.append(GoiY("Sửa ở tài liệu khác, không thuộc đề cương nộp: " + ", ".join(dict.fromkeys(khac)) + "."))
    return ra


def _quyet_dinh(tb: Dict[str, Any], out_dir: Path) -> List[GoiY]:
    pq = tb.get("phan_quyet") or {}
    chuyen = pq.get("chuyen_bac_si") or []
    if not chuyen:
        return []
    so = HD.doc_quyet_dinh(str(tb.get("gate")), out_dir)
    ra: List[GoiY] = []
    for i, c in enumerate(chuyen, 1):
        qd = so.get(f"{tb.get('id')}#{i}")
        van_de = str((c or {}).get("van_de") or "") if isinstance(c, dict) else ""
        ra.append(GoiY(f"Vấn đề chuyển bác sĩ số {i}:", van_de))
        if isinstance(qd, dict) and qd.get("loi_bac_si"):
            ra.append(GoiY(f"Bác sĩ đã quyết ({_ngay(qd.get('thoi_diem'))}):", str(qd["loi_bac_si"])))
        else:
            ra.append(GoiY("⚠ Chưa có quyết định ghi sổ cho vấn đề này — chủ nhiệm chuẩn bị câu trả lời.",
                           canh_bao=True))
    return ra


def cau_hoi_bien_ban(out_dir: Path, dong: Sequence[str], ten_dc: str) -> Tuple[List[NhomBienBan], Dict[str, int]]:
    """Nhóm câu hỏi A (luật Q1–Q3): phản đối của bên phản biện trong mọi biên bản tranh biện đọc được."""
    cac_muc = doc_muc(dong)
    tat_ca = HD.doc_bien_ban(out_dir)
    tbs = [b for b in tat_ca if b.get("loai") == "tranh_bien" and not b.get("_hong")]
    xls = [b for b in tat_ca if b.get("loai") == HD.LOAI_XU_LY and not b.get("_hong")]
    dem = {"tranh_bien": len(tbs), "xu_ly": len(xls), "hong": sum(1 for b in tat_ca if b.get("_hong"))}
    moi_nhat: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for b in tbs:
        k = (str(b.get("gate")), str((b.get("diem_quyet_dinh") or {}).get("ma") or ""))
        if k not in moi_nhat or HD._moc_thoi_gian(b.get("thoi_diem")) > HD._moc_thoi_gian(moi_nhat[k].get("thoi_diem")):
            moi_nhat[k] = b
    thu_tu_cong = {g: i for i, g in enumerate(HD.CONG)}
    tbs.sort(key=lambda b: (thu_tu_cong.get(str(b.get("gate")), 99), str((b.get("diem_quyet_dinh") or {}).get("ma")),
                            HD._moc_thoi_gian(b.get("thoi_diem"))))
    ra: List[NhomBienBan] = []
    for tb in tbs:
        gate = str(tb.get("gate"))
        dp_ma = str((tb.get("diem_quyet_dinh") or {}).get("ma") or "")
        dp = HD._dp_theo_ma(gate, dp_ma) or {}
        pq = tb.get("phan_quyet") if isinstance(tb.get("phan_quyet"), dict) else {}
        ket_qua = str(pq.get("ket_qua") or "")
        moi = moi_nhat.get((gate, dp_ma))
        nhom = NhomBienBan(gate, str(tb.get("id")), dp_ma, str(dp.get("cau_hoi") or ""), _ngay(tb.get("thoi_diem")),
                           KET_QUA_TB.get(ket_qua, ket_qua or "không rõ"), _trang_thai_bien_ban(tb, out_dir),
                           cu_hon=(str(moi.get("id")) if moi is not None and moi is not tb else None))
        if nhom.cu_hon is None:
            if pq.get("ket_luan_cuoi"):
                nhom.chung.append(GoiY("Kết luận cuối của trọng tài:", str(pq["ket_luan_cuoi"])))
            gp = pq.get("giai_phap_tot_nhat") if isinstance(pq.get("giai_phap_tot_nhat"), dict) else {}
            if gp.get("phuong_an") and not la_noi_bo(str(gp["phuong_an"])):
                nhom.chung.append(GoiY("Giải pháp hội đồng khuyến nghị (tư vấn):", str(gp["phuong_an"])))
            elif gp.get("phuong_an"):
                nhom.chung.append(GoiY("Giải pháp hội đồng khuyến nghị thiên về quy trình nội bộ của hệ thống — "
                                       f"không chép vào đây; xem biên bản {tb.get('id')}."))
            bo_qua = 0
            for i, s in enumerate(pq.get("viec_sua") or [], 1):
                van_sua = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
                if la_noi_bo(van_sua):
                    bo_qua += 1
                    continue
                nhom.chung.append(GoiY(f"Việc sửa trọng tài yêu cầu số {i}:", van_sua))
            if bo_qua:
                nhom.chung.append(GoiY(f"{bo_qua} việc sửa khác thiên về quy trình nội bộ của hệ thống (công cụ, "
                                       "checkpoint, agent) — không chép vào đây; xem biên bản."))
            if ket_qua == "sua_ket_luan":
                nhom.chung += _phan_da_sua(tb, xls, dong, ten_dc, cac_muc)
            nhom.chung += _quyet_dinh(tb, out_dir)
        tung = {p.get("ma"): p for p in (pq.get("tung_luan_diem") or []) if isinstance(p, dict)}
        luan_de_xuat = {ld.get("ma"): ld for v in tb.get("vong") or [] if isinstance(v, dict)
                        and v.get("ben") == "de_xuat" for ld in v.get("luan_diem") or [] if isinstance(ld, dict)}
        for v in tb.get("vong") or []:
            if not isinstance(v, dict) or v.get("ben") != "phan_bien":
                continue
            for ld in v.get("luan_diem") or []:
                if not isinstance(ld, dict) or not str(ld.get("noi_dung") or "").strip():
                    continue
                if ld.get("nhuong"):
                    nhom.so_nhuong += 1
                    continue
                p = tung.get(ld.get("ma")) or {}
                ket = str(p.get("ket") or "")
                ch = CauHoi("", "A", f"{gate} · {dp_ma} · phản đối {ld.get('ma')} (vòng {v.get('so')})",
                            str(ld["noi_dung"]), f"biên bản {tb.get('id')}, phản đối {ld.get('ma')}"
                            + (f" nhắm luận điểm {ld.get('phan_doi')}" if ld.get("phan_doi") else ""))
                if la_noi_bo(ch.chat_van):
                    ch.noi_bo = loai_noi_bo(ch.chat_van)
                ch.goi_y.append(GoiY(f"Phán quyết của trọng tài: {KET_PHAN_QUYET.get(ket, ket or 'chưa phán')} —",
                                     str(p.get("ly_do") or "")))
                if ket == "bac" and ld.get("phan_doi") in luan_de_xuat:
                    goc = luan_de_xuat[ld["phan_doi"]]
                    ch.goi_y.append(GoiY(f"Lập luận được giữ (luận điểm {goc.get('ma')} của điều phối cổng):",
                                         str(goc.get("noi_dung") or "")))
                elif ket == "chap_nhan":
                    ch.goi_y.append(GoiY("Phản đối đã được chấp nhận — trả lời dựa trên phần đã sửa/quyết định của "
                                         + ("biên bản này (phần chung bên trên)." if nhom.cu_hon is None else
                                            f"lượt tranh biện mới hơn {nhom.cu_hon}.")))
                elif ket == "chua_du_can_cu":
                    ch.goi_y.append(GoiY("⚠ Trọng tài chưa đủ căn cứ để phán — chủ nhiệm chuẩn bị dữ kiện cho điểm "
                                         "này.", canh_bao=True))
                nhom.cau.append(ch)
        ra.append(nhom)
    return ra, dem


# ── Câu hỏi từ báo cáo phản biện đề cương ────────────────────────────────────────────────────────────────────────────

@dataclass
class PhatHien:
    ma: str
    muc_do: str
    tieu_de: str
    van_de: str
    vi_tri: str
    de_xuat: str
    dong: int


@dataclass
class BaoCao:
    tep: Path
    ngay: str
    sha_doc: Optional[str]
    phat_hien: List[PhatHien]
    cau_hoi: List[Tuple[str, int]]
    tep_khac: List[str] = field(default_factory=list)


_MA_PH_RE = re.compile(r"^(?:#{3,4}\s+|\*\*)([A-ZĐ]{1,2}\d{1,3})\.\s+(.*?)(?:\*\*)?\s*$")
_TRUONG_RE = re.compile(r"^\s*[-*]\s+(?:\*\*)?([^:*\n]{2,40}?)\s*:\s*(?:\*\*)?\s*(.*)$")
_CAU_HOI_TAC_GIA_RE = re.compile(r"câu hỏi cho (?:tác giả|chủ nhiệm)")


def _khoa_truong(k: str) -> Optional[str]:
    k = _chuan(k)
    for ten, dau in (("vi_tri", "vị trí"), ("trich", "trích"), ("van_de", "vấn đề"), ("de_xuat", "đề xuất"),
                     ("can_cu", "căn cứ")):
        if k.startswith(dau):
            return ten
    return None


def _o_bang(d: str) -> List[str]:
    return [o.strip() for o in d.strip().strip("|").split("|")]


def _muc_do_cua(s: str) -> str:
    return next((m for m in _MUC_DO if m in s), "")


def doc_bao_cao(p: Path) -> BaoCao:
    """Đọc báo cáo phản biện ở cả hai khuôn đang có: bảng phát hiện (cột «Vấn đề»/«Góp ý») và mục «Đ1./O1.» có các
    trường «Vị trí · Vấn đề · Đề xuất»; kèm danh sách «Câu hỏi cho tác giả/chủ nhiệm»."""
    dong = p.read_text(encoding="utf-8").splitlines()
    m = re.search(r"_(\d{4})(\d{2})(\d{2})_", p.name)
    ngay = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else "không rõ ngày"
    sha = next((x.group(1) for d in dong[:40] if "sha256" in d.casefold()
                for x in [re.search(r"\b([0-9a-f]{64})\b", d)] if x), None)
    phat_hien: List[PhatHien] = []
    cau_hoi: List[Tuple[str, int]] = []
    muc_do_h2 = ""
    dang: Optional[Dict[str, Any]] = None
    truong: Optional[str] = None
    che_do_cau_hoi = False

    def _dong_muc() -> None:
        nonlocal dang
        if dang:
            phat_hien.append(PhatHien(dang["ma"], dang["muc_do"], dang["tieu_de"], " ".join(dang["van_de"]).strip(),
                                      " ".join(dang["vi_tri"]).strip(), " ".join(dang["de_xuat"]).strip(),
                                      dang["dong"]))
        dang = None

    i = 0
    while i < len(dong):
        d = dong[i]
        s = d.strip()
        mh = _DE_MUC_RE.match(d)
        mp = _MA_PH_RE.match(s)
        if mp and (mh or s.startswith("**")):
            _dong_muc()
            che_do_cau_hoi = False
            dang = {"ma": mp.group(1), "muc_do": _muc_do_cua(s) or muc_do_h2, "tieu_de": mp.group(2).strip(),
                    "van_de": [], "vi_tri": [], "de_xuat": [], "dong": i + 1}
            truong = None
            i += 1
            continue
        if mh or (s.startswith("**") and s.endswith("**") and _CAU_HOI_TAC_GIA_RE.search(_chuan(s))) or s == "---":
            _dong_muc()
            tieu = mh.group(2) if mh else s
            if mh and len(mh.group(1)) == 2:
                muc_do_h2 = _muc_do_cua(tieu)
            che_do_cau_hoi = bool(_CAU_HOI_TAC_GIA_RE.search(_chuan(tieu)))
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(dong) and re.match(r"^\|[\s:|-]+\|?\s*$", dong[i + 1].strip()):
            _dong_muc()
            dau = [_chuan(o) for o in _o_bang(s)]
            cot = {"van_de": next((k for k, o in enumerate(dau) if o.startswith(("vấn đề", "góp ý"))), None),
                   "muc_do": next((k for k, o in enumerate(dau) if o.startswith("mức")), None),
                   "vi_tri": next((k for k, o in enumerate(dau) if o.startswith("vị trí")), None),
                   "de_xuat": next((k for k, o in enumerate(dau) if o.startswith("đề xuất")), None)}
            j = i + 2
            while j < len(dong) and dong[j].strip().startswith("|"):
                if cot["van_de"] is not None:
                    o = _o_bang(dong[j])

                    def _lay(k: Optional[int], o: List[str] = o) -> str:
                        return o[k] if k is not None and k < len(o) else ""
                    if _lay(cot["van_de"]):
                        phat_hien.append(PhatHien(o[0] if o else "", _muc_do_cua(_lay(cot["muc_do"])) or muc_do_h2,
                                                  "", _lay(cot["van_de"]), _lay(cot["vi_tri"]), _lay(cot["de_xuat"]),
                                                  j + 1))
                j += 1
            i = j
            continue
        if che_do_cau_hoi:
            mds = _MUC_DS_RE.match(d)
            if mds:
                cau_hoi.append((mds.group(1).strip(), i + 1))
            elif s and cau_hoi:
                che_do_cau_hoi = False
            i += 1
            continue
        if dang is not None and s:
            mt = _TRUONG_RE.match(d)
            k = _khoa_truong(mt.group(1)) if mt else None
            if k:
                truong = k
                if k in dang:
                    dang[k].append(mt.group(2).strip())
            elif truong in ("van_de", "vi_tri", "de_xuat"):
                dang[truong].append(s)
        i += 1
    _dong_muc()
    return BaoCao(p, ngay, sha, phat_hien, cau_hoi)


def tim_bao_cao(out_dir: Path, study: str) -> Optional[BaoCao]:
    """Báo cáo phản biện MỚI NHẤT (theo ngày trong tên tệp); các bản khác chỉ được liệt kê."""
    ds = sorted(out_dir.glob(MAU_BAO_CAO.format(study=study)),
                key=lambda p: (re.search(r"_(\d{8})_", p.name).group(1) if re.search(r"_(\d{8})_", p.name) else "",
                               p.name))
    if not ds:
        return None
    bc = doc_bao_cao(ds[-1])
    bc.tep_khac = [p.name for p in ds[:-1]]
    return bc


def _muc_lien_quan(van: str, cac_muc: Sequence[Muc]) -> List[str]:
    """Đề mục đề cương hiện hành được báo cáo nhắc tới («mục 4.10», «Phụ lục B»)."""
    ra: List[str] = []
    for so in re.findall(r"\bmục\s+(\d+(?:\.\d+){0,3})", van):
        m = next((x for x in cac_muc if x.so == so), None)
        if m and m.nhan not in ra:
            ra.append(m.nhan)
    for pl in re.findall(r"\bPhụ lục\s+([A-E])\b", van, re.IGNORECASE):
        m = next((x for x in cac_muc if _chuan(x.so) == _chuan(f"PHỤ LỤC {pl}")), None)
        if m and m.nhan not in ra:
            ra.append(m.nhan)
    return ra


def cau_hoi_bao_cao(bc: BaoCao, cac_muc: Sequence[Muc], sha_hien: str) -> List[CauHoi]:
    """Nhóm câu hỏi B: mỗi phát hiện + mỗi câu hỏi đặt cho tác giả; đề xuất của phản biện chỉ là gợi ý chuẩn bị."""
    ra: List[CauHoi] = []
    trung = ("đề cương hiện hành trùng bản phản biện đã đọc" if bc.sha_doc == sha_hien else
             "đề cương ĐÃ ĐỔI sau khi phản biện đọc — số dòng có thể đã dịch chuyển" if bc.sha_doc else
             "báo cáo không ghi mã băm bản đề cương đã đọc — số dòng có thể đã dịch chuyển")
    for ph in bc.phat_hien:
        if ph.tieu_de:
            tieu = f"{ph.muc_do + ' ' if ph.muc_do else ''}{ph.ma + '. ' if ph.ma else ''}{ph.tieu_de}".strip()
        else:  # dòng bảng: mã cột đầu («1», «G1»…) là số thứ tự CỦA BÁO CÁO, không phải mã cổng
            tieu = f"{ph.muc_do + ' ' if ph.muc_do else ''}phát hiện «{ph.ma}» của báo cáo".strip()
        ch = CauHoi("", "B", tieu or "phát hiện của phản biện", ph.van_de or ph.tieu_de,
                    f"{bc.tep.name}, dòng {ph.dong}", muc_do=ph.muc_do)
        if ph.vi_tri:
            ch.goi_y.append(GoiY(f"Vị trí phản biện nêu ({trung}):", ph.vi_tri))
        lq = _muc_lien_quan(f"{ph.vi_tri} {ph.van_de} {ph.tieu_de}", cac_muc)
        if lq:
            ch.goi_y.append(GoiY("Phần đề cương liên quan: " + "; ".join(lq) + "."))
        if ph.de_xuat:
            ch.goi_y.append(GoiY("Đề xuất sửa của phản biện (chuẩn bị — máy KHÔNG xác minh đã áp dụng vào đề cương):",
                                 ph.de_xuat))
        ra.append(ch)
    for van, so_dong in bc.cau_hoi:
        ch = CauHoi("", "B", "câu hỏi phản biện đặt cho tác giả", van, f"{bc.tep.name}, dòng {so_dong}")
        lq = _muc_lien_quan(van, cac_muc)
        ch.goi_y.append(GoiY("Báo cáo không kèm đáp án — chủ nhiệm trả lời từ đề cương hiện hành"
                             + (f" ({'; '.join(lq)})." if lq else ".")))
        ra.append(ch)
    return ra


def cau_hoi_de_cuong(dong: Sequence[str]) -> List[CauHoi]:
    """Nhóm câu hỏi C (chỉ khi chưa có biên bản tranh biện — luật Q4): hạn chế và sai số đề cương TỰ nêu."""
    cac_muc = doc_muc(dong)
    ra: List[CauHoi] = []
    for mau, nhan in ((r"^hạn chế", "hạn chế"), (r"^sai số", "sai số")):
        muc = tim_muc(cac_muc, mau)
        if muc is None:
            continue
        for c in chon_cau(cau_cua_muc(dong, muc), "dau", 4):
            ra.append(CauHoi("", "C", f"{nhan} đề cương tự nêu — {muc.nhan}", c.van,
                             f"đề cương nộp, dòng {c.dong}",
                             [GoiY("Gợi ý: câu này là chính lời đề cương — chủ nhiệm chuẩn bị giải thích biện pháp "
                                   "khống chế/phạm vi suy rộng đã ghi ở cùng mục.")]))
    return ra


# ── Câu hỏi từ sổ quyết định của hội đồng nghiên cứu (22/11/2026) ─────────────────────────────────────────────────────
# Sổ `hoi_dong_khoa_hoc/QUYET_DINH_HOI_DONG_*.md`: mỗi mục «### <mã> — <vấn đề>» là một vấn đề hội đồng nghiên cứu của
# hệ đã nêu, kèm «- Quyết định:», các dòng «- Căn cứ:» và các khối «- Thay ở `<tệp>` dòng N» với «  - Cũ:»/«  - Mới:».
# Vấn đề ⇒ câu Hội đồng bệnh viện có thể hỏi; gợi ý trả lời CHỈ chép nguyên văn quyết định, căn cứ và phần đề cương đã
# thay (luật Q2) — phần «Mới» trỏ vào đề cương nộp được xác minh còn nguyên văn trong bản hiện hành (cùng tinh thần Q3).
THU_MUC_HDKH = "hoi_dong_khoa_hoc"
MAU_SO_QD = "QUYET_DINH_HOI_DONG_*.md"
_QD_MUC_RE = re.compile(r"^###\s+(\S+)\s+—\s+(.+\S)\s*$")
_QD_THAY_RE = re.compile(r"^- Thay ở `([^`]+)` dòng (\d+)")
_QD_CU_MOI_RE = re.compile(r"^\s+- (Cũ|Mới):\s?(.*)$")
_QD_PHAN_RE = re.compile(r"^## (?:Thành viên|Tài liệu)")


def doc_so_quyet_dinh(p: Path) -> List[Dict[str, Any]]:
    """[{ma, van_de, dong, quyet_dinh, can_cu: [...], thay: [{tep, dong, moi}]}] của MỘT sổ quyết định."""
    try:
        dong = p.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    ra: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None
    thay: Optional[Dict[str, Any]] = None
    dang_moi = False
    for i, d in enumerate(dong, 1):
        m = _QD_MUC_RE.match(d)
        # Đoạn «Cũ»/«Mới» chép nguyên khối đề cương nên có thể chứa đề mục «## 3.7. …» hay dòng «- …»: trong khối thay,
        # chỉ đề mục cấu trúc của sổ («## Thành viên…», «## Tài liệu…») và ba gạch đầu dòng của sổ mới kết thúc khối.
        if m or (d.startswith("## ") and (thay is None or _QD_PHAN_RE.match(d))):
            cur, thay, dang_moi = None, None, False
            if m:
                cur = {"ma": m.group(1), "van_de": m.group(2), "dong": i, "quyet_dinh": "", "can_cu": [], "thay": []}
                ra.append(cur)
            continue
        if cur is None:
            continue
        if d.startswith(("- Quyết định:", "- Căn cứ:", "- Thay ở ")) or (thay is None and d.startswith("- ")):
            dang_moi = False
            thay = None
            if d.startswith("- Quyết định:"):
                cur["quyet_dinh"] = d[len("- Quyết định:"):].strip()
            elif d.startswith("- Căn cứ:"):
                cur["can_cu"].append(d[len("- Căn cứ:"):].strip())
            else:
                mt = _QD_THAY_RE.match(d)
                if mt:
                    thay = {"tep": mt.group(1), "dong": int(mt.group(2)), "moi": []}
                    cur["thay"].append(thay)
            continue
        mk = _QD_CU_MOI_RE.match(d)
        if thay is not None and mk:
            dang_moi = mk.group(1) == "Mới"
            if dang_moi:
                thay["moi"].append(mk.group(2).strip())
            continue
        if dang_moi and thay is not None and d.strip():
            thay["moi"].append(d.strip())
    return ra


def cau_hoi_so_quyet_dinh(out_dir: Path, dong: Sequence[str], ten_dc: str) -> Tuple[List[CauHoi], List[str]]:
    """Nhóm câu hỏi D: vấn đề trong các sổ quyết định của hội đồng nghiên cứu (mới nhất trước theo tên tệp)."""
    tep = sorted((Path(out_dir) / THU_MUC_HDKH).glob(MAU_SO_QD))
    van_dc = "\n".join(dong)
    ra: List[CauHoi] = []
    for p in tep:
        for qd in doc_so_quyet_dinh(p):
            ch = CauHoi("", "D", f"{qd['ma']} — sổ {p.name}", qd["van_de"],
                        f"{THU_MUC_HDKH}/{p.name}, dòng {qd['dong']}")
            if la_noi_bo(ch.chat_van):
                ch.noi_bo = loai_noi_bo(ch.chat_van)
            if qd["quyet_dinh"]:
                ch.goi_y.append(GoiY("Quyết định của hội đồng nghiên cứu:", qd["quyet_dinh"]))
            for cc in qd["can_cu"]:
                ch.goi_y.append(GoiY("Căn cứ:", cc))
            khac: List[str] = []
            for t in qd["thay"]:
                if Path(t["tep"]).name != ten_dc:
                    khac.append(Path(t["tep"]).name)
                    continue
                mau = next((x for x in t["moi"] if x.strip()), "")
                k = next((n for n, x in enumerate(dong, 1) if mau and mau in x), None)
                if k is None or mau not in van_dc:
                    ch.goi_y.append(GoiY(f"⚠ Phần đề cương thay theo quyết định (dòng gốc {t['dong']}) không còn "
                                         "nguyên văn trong bản hiện hành — đối chiếu lại trước khi trả lời.",
                                         canh_bao=True))
                else:
                    ch.goi_y.append(GoiY(f"Đề cương hiện hành, dòng {k} (phần đã thay theo quyết định):",
                                         _cau_chua(dong[k - 1], mau[:80])))
            if khac:
                ch.goi_y.append(GoiY("Quyết định còn thay ở tài liệu khác, không thuộc đề cương nộp: "
                                     + ", ".join(dict.fromkeys(khac)) + "."))
            ra.append(ch)
    return ra, [p.name for p in tep]


# ── Kết xuất bộ câu hỏi ──────────────────────────────────────────────────────────────────────────────────────────────

def _dong_goi_y(g: GoiY) -> str:
    return f"- {g.nhan} «{g.trich}»" if g.trich else f"- {g.nhan}"


def _khoa_hoc(nh: NhomBienBan) -> List[CauHoi]:
    return [c for c in nh.cau if not c.noi_bo]


def _noi_bo(nh: NhomBienBan) -> List[CauHoi]:
    return [c for c in nh.cau if c.noi_bo]


def _danh_so(nhom_bb: Sequence[NhomBienBan], cau_b: Sequence[CauHoi], cau_c: Sequence[CauHoi],
             cau_d: Sequence[CauHoi] = ()) -> None:
    """Đánh số đúng thứ tự kết xuất: A (khoa học/đạo đức — phần chính rồi lượt cũ) · B · D (sổ quyết định hội đồng
    nghiên cứu) · C · N (quy trình nội bộ)."""
    chinh = [x for x in nhom_bb if x.cu_hon is None]
    cu = [x for x in nhom_bb if x.cu_hon is not None]
    for i, ch in enumerate([c for nh in chinh + cu for c in _khoa_hoc(nh)], 1):
        ch.ma = f"A{i}"
    for i, ch in enumerate(cau_b, 1):
        ch.ma = f"B{i}"
    for i, ch in enumerate(cau_d, 1):
        ch.ma = f"D{i}"
    for i, ch in enumerate(cau_c, 1):
        ch.ma = f"C{i}"
    for i, ch in enumerate([c for nh in chinh + cu for c in _noi_bo(nh)], 1):
        ch.ma = f"N{i}"


# Mục của «Phiếu nhận xét» (Phụ lục 2 của hướng dẫn chung, bác sĩ gửi 21/11/2026). Phiếu in cho nghiệm thu; thành viên
# Hội đồng xét đề cương nhận xét theo cùng các mục (mục 3 «Kết quả» ⇒ dự kiến kết quả). Gắn bằng từ khoá — chỉ là GỢI Ý
# để chủ nhiệm xếp phần trả lời; câu không khớp mục nào ⇒ mục 5.
TIEU_CHI_PHIEU: Tuple[Tuple[str, str, str], ...] = (
    ("2", "Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật",
     r"mục tiêu|thiết kế|cỡ mẫu|chọn mẫu|biến số|công cụ|thang đo|bộ câu hỏi|phân tích|thống kê|hồi quy|sai số|sai lệch"
     r"|nhiễu|kết cục|giả thuyết|quần thể|tiêu chuẩn (?:chọn|lựa chọn|loại trừ)|độ tin cậy|kappa|lực mẫu|cfa|efa"
     r"|dữ liệu thiếu|thiếu dữ liệu|gom cụm|công thức|đo lường"),
    ("1", "Tính cấp thiết, ý nghĩa khoa học và thực tiễn",
     r"cấp thiết|ý nghĩa (?:khoa học|thực tiễn)|khoảng trống|tính mới|đóng góp|đặt vấn đề|tổng quan"),
    ("4", "Chất lượng văn bản, tài liệu trích dẫn (đầy đủ, rõ ràng, xác thực, lôgíc)",
     r"trích dẫn|tài liệu tham khảo|pmid|doi|vancouver|nhất quán|mâu thuẫn|trình bày|chính tả|viết tắt|định dạng"
     r"|không có nguồn|lệch số|tham chiếu|tối nghĩa|chưa chính xác"),
    ("3", "Kết quả (với đề cương: dự kiến kết quả)", r"dự kiến kết quả|khung bảng|bảng trống|biểu đồ|bàn luận"),
)
TIEU_CHI_KHAC = ("5", "Tồn tại và đề xuất hướng giải quyết")


def tieu_chi_phieu(ch: CauHoi) -> Tuple[str, str]:
    """(số mục, tên mục) của phiếu nhận xét gợi ý cho một câu hỏi: mục khớp NHIỀU từ khoá khác nhau nhất; hoà ⇒ thứ
    tự 2, 1, 4, 3; không khớp ⇒ mục 5."""
    van = f"{ch.tieu_de} {ch.chat_van}".lower()
    diem = [(len(set(re.findall(mau, van))), -i, so, ten) for i, (so, ten, mau) in enumerate(TIEU_CHI_PHIEU)]
    tot = max(diem)
    return (tot[2], tot[3]) if tot[0] else TIEU_CHI_KHAC


def _render_cau(ch: CauHoi) -> List[str]:
    so_tc, ten_tc = tieu_chi_phieu(ch)
    out = [f"#### Câu {ch.ma} — {ch.tieu_de}", "", f"- Hội đồng có thể chất vấn: «{ch.chat_van}»",
           f"- Nguồn: {ch.nguon}.", f"- Mục phiếu nhận xét (gợi ý máy): {so_tc}. {ten_tc}."]
    if ch.noi_bo:
        out.append(f"- Phân loại: thiên về quy trình nội bộ ({len(ch.noi_bo)} loại ký hiệu: {', '.join(ch.noi_bo)}).")
    return out + [_dong_goi_y(g) for g in ch.goi_y] + [""]


def _render_nhom_bb(nh: NhomBienBan, cau: Sequence[CauHoi], co_chung: bool) -> List[str]:
    out = [f"### {nh.gate} · {nh.dp} — biên bản {nh.id} (ngày {nh.ngay}; kết quả tranh biện: {nh.ket_qua})", ""]
    if nh.dp_cau_hoi:
        out += [f"- Điểm quyết định: «{nh.dp_cau_hoi}»"]
    out += [f"- Trạng thái biên bản: {nh.trang_thai}."]
    if nh.cu_hon:
        out += [f"- Đã có lượt tranh biện mới hơn cho cùng điểm quyết định: {nh.cu_hon}."]
    if nh.so_nhuong and co_chung:
        out += [f"- Bên phản biện nhường {nh.so_nhuong} luận điểm (không đưa vào câu hỏi)."]
    if nh.chung and co_chung:
        out += ["- Phần chung cho các câu bên dưới:"] + ["  " + _dong_goi_y(g) for g in nh.chung]
    out += [""]
    for ch in cau:
        out += _render_cau(ch)
    return out


def render_cau_hoi(ten_de_tai: str, ten_dc: str, so_dong: int, sha: str, nhom_bb: Sequence[NhomBienBan],
                   dem_bb: Dict[str, int], bc: Optional[BaoCao], cau_b: Sequence[CauHoi],
                   cau_c: Sequence[CauHoi], cau_d: Sequence[CauHoi] = (), tep_qd: Sequence[str] = ()) -> str:
    chinh = [x for x in nhom_bb if x.cu_hon is None]
    cu = [x for x in nhom_bb if x.cu_hon is not None]
    so_a = sum(len(_khoa_hoc(x)) for x in nhom_bb)
    so_n = sum(len(_noi_bo(x)) for x in nhom_bb)
    out = ["# BỘ CÂU HỎI PHẢN BIỆN DỰ KIẾN KHI BẢO VỆ ĐỀ CƯƠNG", "", f"**{ten_de_tai}**" if ten_de_tai else "", "",
           "Tài liệu chuẩn bị NỘI BỘ cho chủ nhiệm đề tài — không nộp Hội đồng. Câu hỏi rút từ phản đối CÓ THẬT trong "
           "biên bản hội đồng cổng và báo cáo phản biện; mỗi câu ghi nguồn. Đoạn trong ngoặc «…» là NGUYÊN VĂN chép từ "
           "nguồn — máy không viết câu trả lời mới, không thêm số liệu hay trích dẫn. Chủ nhiệm tự diễn đạt câu trả "
           "lời và đối chiếu với đề cương hiện hành.", "",
           "| Nguồn | Đã đọc |", "|---|---|",
           f"| Đề cương nộp | `{ten_dc}` — {so_dong} dòng, mã băm bắt đầu bằng {sha[:12]} |",
           f"| Biên bản tranh biện | {dem_bb.get('tranh_bien', 0)} biên bản ({len(chinh)} lượt mới nhất theo điểm "
           f"quyết định, {len(cu)} lượt cũ hơn) |",
           f"| Biên bản xử lý việc sửa | {dem_bb.get('xu_ly', 0)} biên bản |"]
    if dem_bb.get("hong"):
        out.append(f"| Biên bản không đọc được | {dem_bb['hong']} (bỏ qua) |")
    out.append(f"| Báo cáo phản biện đề cương | {'`' + bc.tep.name + '` (ngày ' + bc.ngay + ')' if bc else 'không có'}"
               + (f"; bản cũ hơn không dùng: {', '.join(bc.tep_khac)}" if bc and bc.tep_khac else "") + " |")
    out.append(f"| Sổ quyết định hội đồng nghiên cứu | {len(tep_qd)} sổ"
               + (f" ({', '.join('`' + x + '`' for x in tep_qd)})" if tep_qd else "") + f", {len(cau_d)} vấn đề |")
    out += ["", f"Tổng: {so_a} câu từ biên bản (nhóm A) · {len(cau_b)} câu từ báo cáo phản biện (nhóm B)"
            + (f" · {len(cau_d)} câu từ sổ quyết định hội đồng nghiên cứu (nhóm D)" if cau_d else "")
            + (f" · {len(cau_c)} câu từ đề cương (nhóm C)" if cau_c else "")
            + (f" · {so_n} phản đối thiên về quy trình nội bộ để tra (nhóm N, cuối tài liệu)" if so_n else "") + ".",
            ""]
    # bảng tra theo mục phiếu nhận xét (các câu khoa học A, B, D, C; không gồm nhóm N)
    theo_tc: Dict[str, List[str]] = {}
    for ch in [c for nh in nhom_bb for c in _khoa_hoc(nh)] + list(cau_b) + list(cau_d) + list(cau_c):
        theo_tc.setdefault(tieu_chi_phieu(ch)[0], []).append(ch.ma)
    if theo_tc:
        out += ["Xếp theo mục của Phiếu nhận xét (Phụ lục 2 hướng dẫn chung; gợi ý máy theo từ khoá):", "",
                "| Mục phiếu nhận xét | Câu |", "|---|---|"]
        for so, ten in [(a, b) for a, b, _m in sorted(TIEU_CHI_PHIEU)] + [TIEU_CHI_KHAC]:
            if theo_tc.get(so):
                ma = sorted(theo_tc[so], key=lambda x: (x[:1], int(x[1:]) if x[1:].isdigit() else 0))
                out.append(f"| {so}. {ten} | {', '.join(ma)} |")
        out.append("")
    out += [f"*{LOI_DAN}*", "", "---", ""]
    out += ["## A. Từ biên bản hội đồng cổng (phản đối của bên phản biện tranh biện)", ""]
    if not dem_bb.get("tranh_bien"):
        out += ["**CHƯA CÓ BIÊN BẢN HỘI ĐỒNG CỔNG** — đề tài chưa có biên bản tranh biện nào trong `hoi_dong/`. Công "
                "cụ không triệu tập hội đồng (tốn token, cần bác sĩ quyết); câu hỏi bên dưới chỉ lấy từ báo cáo phản "
                "biện (nhóm B) và từ chính đề cương (nhóm C).", ""]
    elif not so_a:
        out += ["Mọi phản đối trong biên bản đều thiên về quy trình nội bộ của hệ thống — xem nhóm N cuối tài liệu.",
                ""]
    for nh in chinh:
        if _khoa_hoc(nh):
            out += _render_nhom_bb(nh, _khoa_hoc(nh), co_chung=True)
    if any(_khoa_hoc(nh) for nh in cu):
        out += ["### Phản đối ở các lượt tranh biện cũ hơn", "",
                "Các lượt này đã có lượt mới hơn cho cùng điểm quyết định; giữ lại vì Hội đồng có thể hỏi lại cùng ý.",
                ""]
        for nh in cu:
            if _khoa_hoc(nh):
                out += _render_nhom_bb(nh, _khoa_hoc(nh), co_chung=False)
    out += ["## B. Từ báo cáo phản biện đề cương", ""]
    if bc is None:
        out += ["Không có báo cáo `PHAN_BIEN_DE_CUONG_NOP_*` trong thư mục đề tài.", ""]
    elif not cau_b:
        out += [f"Báo cáo `{bc.tep.name}` không có phát hiện hay câu hỏi nào đọc được theo hai khuôn đã biết "
                "(bảng có cột «Vấn đề/Góp ý»; mục «Đ1./O1.» có trường «Vấn đề») — chủ nhiệm đọc trực tiếp.", ""]
    for ch in cau_b:
        out += _render_cau(ch)
    if tep_qd:
        out += ["## D. Từ sổ quyết định của hội đồng nghiên cứu (vấn đề đã nêu và quyết định có căn cứ)", "",
                "Mỗi câu là một vấn đề hội đồng nghiên cứu của hệ đã nêu khi rà đề tài; gợi ý trả lời chép nguyên văn "
                "quyết định, căn cứ và phần đề cương đã thay (phần thay được đối chiếu với đề cương hiện hành).", ""]
        if not cau_d:
            out += ["Các sổ không có mục vấn đề «### <mã> — <vấn đề>» nào đọc được.", ""]
        for ch in cau_d:
            out += _render_cau(ch)
    if cau_c:
        out += ["## C. Từ chính đề cương (nhãn: KHÔNG phải phản đối thật — chỉ dùng khi chưa có biên bản)", ""]
        for ch in cau_c:
            out += _render_cau(ch)
    if so_n:
        out += ["## N. Phản đối thiên về quy trình nội bộ của hệ thống (để tra — Hội đồng bệnh viện ít khả năng hỏi)",
                "", f"Phân loại máy: phản đối chứa từ {NGUONG_NOI_BO} loại ký hiệu nội bộ trở lên (tệp mã, checkpoint, "
                "cờ dòng lệnh, tên agent…). Phân loại có thể nhầm — chủ nhiệm lướt qua trước buổi bảo vệ.", ""]
        for nh in chinh + cu:
            if _noi_bo(nh):
                out += _render_nhom_bb(nh, _noi_bo(nh), co_chung=False)
    while out and out[-1] in ("", "---"):
        out.pop()
    return "\n".join(out) + "\n"


# ── Tệp trình chiếu .pptx (22/11/2026) ───────────────────────────────────────────────────────────────────────────────
# Bác sĩ (22/11/2026): «Những vấn đề còn lại … có nền hay chưa có nền hãy hoàn thiện, bổ sung và nâng cấp đạt chuẩn».
# Dàn slide .md/.docx chưa trình chiếu được. Tệp .pptx dựng từ CHÍNH các slide của dàn (luật S1: mọi câu nguyên văn, mỗi
# slide trỏ mục và số dòng đề cương ở chân trang và ghi chú người trình bày), bảng nguồn dựng lại thành bảng thật, hình
# và biểu đồ của đề cương (`bieu-bang/`) nhúng đúng tệp, mỗi hình một slide kèm ghi chú nguyên văn của hình.
# Trình bày: 16:9, Times New Roman; thân chữ thử 24 → 18 pt (18 pt là cỡ nhỏ nhất đọc được từ cuối phòng họp), không vừa
# một trang ở 20 pt thì sang trang «(tiếp)» ở 20 pt — không thu chữ nhỏ hơn, không cắt câu. Khung chữ được ĐO bằng phông
# thật (PIL) để không tràn; `kiem_pptx` mở lại tệp và đo lại.
TEN_PPTX = "GOI_BAO_VE_TRINH_CHIEU_{study}.pptx"
KHO_SLIDE = (13.333, 7.5)  # inch, 16:9
LE = 0.55
KHUNG_TIEU_DE = (LE, 0.3, KHO_SLIDE[0] - 2 * LE, 1.0)
KHUNG_THAN = (LE, 1.4, KHO_SLIDE[0] - 2 * LE, 5.4)
KHUNG_CHAN = (LE, 6.95, KHO_SLIDE[0] - 2 * LE, 0.4)
CO_TIEU_DE = (30, 28, 26, 24)
CO_THAN = (24, 22, 20, 18)
CO_THAN_TRANG = 20  # cỡ khi phải sang trang «(tiếp)»
CO_CHAN = 12
GIAN_DONG = 1.2   # chiều cao dòng = 1,2 × cỡ chữ (dãn dòng đơn của PowerPoint)
CACH_DOAN = 6     # pt sau mỗi đoạn
LUI_GACH = 0.3    # inch, thụt treo của gạch đầu dòng
LE_TRONG = (0.1, 0.05)  # inch, lề trong khung chữ (trái/phải, trên/dưới)
DU_PHONG = 0.95   # khung chữ chỉ được dùng tới 95% chiều cao (sai số đo phông)
MAU_TIEU_DE = (0x1F, 0x3A, 0x5F)
MAU_CHAN = (0x59, 0x59, 0x59)
_PHONG: Dict[bool, Any] = {}
_HINH_RE = re.compile(r"^!\[[^\]]*\]\(([^)]+)\)\s*$")
_CHU_HINH_RE = re.compile(r"^\*\*((?:Hình|Biểu đồ)\s+\d+\.\d+)\.\s+(.+?)\.?\*\*\s*$")


def _duong_phong(dam: bool) -> str:
    """Tệp phông Times New Roman (máy không có — vd CI Linux — thì phông có chân mặc định của matplotlib; phép đo và
    phép kiểm dùng cùng một phông nên vẫn nhất quán)."""
    import logging  # noqa: PLC0415

    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    from matplotlib import font_manager as fm  # noqa: PLC0415

    return fm.findfont(fm.FontProperties(family="Times New Roman", weight="bold" if dam else "normal"))


def _emu_tron_len(inch: float) -> int:
    """Inch → EMU làm tròn LÊN (23/11/2026). `pptx.util.Inches` cắt phần lẻ: 0,92 inch tính ra 841 247,9999… EMU bị
    ghi 841 247 — hàng bảng thấp hơn chiều cao đã đo 1 EMU (≈ 1,09·10⁻⁶ inch, vượt dung sai 10⁻⁶ của `kiem_pptx`).
    Trên CI Linux (phông DejaVu) một hàng rơi đúng biên đó ⇒ 6 test đỏ. Làm tròn lên ⇒ khung không bao giờ thấp hơn
    chữ đo được."""
    return int(math.ceil(inch * 914400 - 1e-6))


def _rong_pt(van: str, co: float, dam: bool) -> float:
    """Bề rộng (pt) của chuỗi ở cỡ `co` pt — đo bằng phông thật."""
    from PIL import ImageFont  # noqa: PLC0415

    if dam not in _PHONG:
        _PHONG[dam] = ImageFont.truetype(_duong_phong(dam), 100)
    return _PHONG[dam].getlength(van) * co / 100.0


def so_dong_chu(van: str, co: float, dam: bool, rong_in: float) -> int:
    """Số dòng khi ngắt từ trong khung rộng `rong_in` inch (thuật toán ngắt tham lam như PowerPoint)."""
    rong = rong_in * 72.0
    tong = 0
    for doan in str(van).split("\n"):
        dong, cur = 1, 0.0
        for tu in doan.split():
            w = _rong_pt(tu, co, dam)
            cach = _rong_pt(" ", co, dam) if cur else 0.0
            if cur and cur + cach + w > rong:
                dong += 1
                cur = w
            else:
                cur += cach + w
            while cur > rong:  # một từ dài hơn cả dòng — PowerPoint ngắt giữa từ
                dong += 1
                cur -= rong
        tong += dong
    return tong


def do_cao_doan(doan: Sequence[Tuple[str, float, bool, float]], rong_in: float) -> float:
    """Chiều cao (inch) của các đoạn [(chữ, cỡ, đậm, thụt trái inch)] trong khung rộng `rong_in` (đã trừ lề trong)."""
    cao = 0.0
    for van, co, dam, lui in doan:
        cao += so_dong_chu(van, co, dam, rong_in - lui) * co * GIAN_DONG / 72.0 + CACH_DOAN / 72.0
    return cao


def _chu_tron(v: str) -> str:
    """Bỏ dấu nhấn Markdown (**, ***, `) — chữ vẫn nguyên văn."""
    return re.sub(r"\*{2,3}|`", "", _bo_nhan_manh(str(v))).strip()


def hinh_de_cuong(dong: Sequence[str], out_dir: Path) -> List[Dict[str, Any]]:
    """Mọi hình/biểu đồ của đề cương: [{rel, tep, so, ten, dong, ghi_chu, co_tep}] theo thứ tự xuất hiện."""
    ra = []
    for i, d in enumerate(dong):
        m = _HINH_RE.match(d.strip())
        if not m:
            continue
        j = i + 1
        while j < len(dong) and not dong[j].strip():
            j += 1
        mc = _CHU_HINH_RE.match(dong[j].strip()) if j < len(dong) else None
        if not mc:
            continue
        g = j + 1
        while g < len(dong) and not dong[g].strip():
            g += 1
        ghi = dong[g].strip() if g < len(dong) and _GHI_CHU_RE.match(dong[g].strip()) else ""
        tep = (Path(out_dir) / m.group(1)).resolve()
        ra.append({"rel": m.group(1), "tep": tep, "so": mc.group(1), "ten": mc.group(2), "dong": j + 1,
                   "ghi_chu": re.sub(r"^\*?\s*Ghi chú\s*:\s*\*?\s*", "", ghi).strip(),
                   "co_tep": tep.is_file() and Path(out_dir).resolve() in tep.parents})
    return ra


def _neo_hinh(ten: str) -> str:
    """Slide mà hình đứng ngay sau: sơ đồ chọn ⇒ «Phương pháp chọn mẫu»; khung lý thuyết ⇒ «Khoảng trống»; sơ đồ nhân
    quả ⇒ «Xử lý và phân tích»; còn lại (khung bảng/biểu đồ dự kiến) ⇒ «Dự kiến kết quả». Sơ đồ nhân quả xét TRƯỚC:
    tên kiểu «Sơ đồ nhân quả (DAG) lựa chọn biến» cũng chứa chữ «chọn»."""
    if re.search(r"nhân quả|\bDAG\b", ten):
        return "phan_tich"
    if re.search(r"[Ss]ơ đồ.*(?:chọn|tuyển|STROBE|CONSORT|STARD|PRISMA|TRIPOD|COREQ)", ten):
        return "chon_mau"
    if re.search(r"khung (?:lý thuyết|khái niệm)", ten, re.I):
        return "khoang_trong"
    return "du_kien"


def _muc_ngan(nguon: Sequence[str]) -> str:
    """Chân trang: các mục đề cương của slide («mục 2.5.2 «Phương pháp chọn mẫu»» ⇒ «mục 2.5.2»)."""
    ra = []
    for x in nguon:
        m = re.match(r"^mục (\S.*?) «", x)
        t = f"mục {m.group(1)}" if m else re.split(r", dòng | ở dòng ", x)[0]
        if t not in ra:
            ra.append(t)
    return "; ".join(ra)


@dataclass
class TrangPptx:
    """Một trang của tệp trình chiếu (trước khi ghi): khối chữ/bảng hoặc một hình."""
    loai: str  # noi_dung · hinh · ten_de_tai
    tieu_de: str
    chan: str
    ghi: str
    khoi: List[Tuple[str, Any]] = field(default_factory=list)  # ("chu", [(van, dam, gach)]) · ("bang", (cot, hang))
    co: float = CO_THAN[0]
    hinh: Optional[Dict[str, Any]] = None
    nguon: List[str] = field(default_factory=list)


def _khoi_cua_slide(s: Slide) -> List[Tuple[str, Any]]:
    """Khối hiển thị của một slide dàn: nhãn phụ in đậm, câu nguyên văn có gạch đầu dòng, hàng bảng ⇒ bảng thật."""
    ra: List[Tuple[str, Any]] = []
    for nhan_phu, ds in s.khoi:
        chu: List[Tuple[str, bool, bool]] = [(nhan_phu, True, False)] if nhan_phu else []
        if ds and all(c.phu for c in ds) and ds[0].cot[1]:
            if chu:
                ra.append(("chu", chu))
            ra.append(("bang", (ds[0].cot, [(_chu_tron(c.van), _chu_tron(c.phu)) for c in ds])))
            continue
        chu += [(_chu_tron(c.van), False, True) for c in ds]
        if chu:
            ra.append(("chu", chu))
    return ra


def _cao_khoi(k: Tuple[str, Any], co: float, rong: float) -> float:
    if k[0] == "chu":
        return do_cao_doan([(v, co, d, LUI_GACH if g else 0.0) for v, d, g in k[1]], rong - 2 * LE_TRONG[0]) + \
            2 * LE_TRONG[1]
    cot, hang = k[1]
    return _cao_hang_bang(cot, co, rong, True) + sum(_cao_hang_bang(h, co, rong) for h in hang)


def _cao_hang_bang(hang: Tuple[str, str], co: float, rong: float, dam: bool = False) -> float:
    """Chiều cao (inch) một hàng bảng hai cột 40% / 60% ở cỡ `co`."""
    r = (rong * 0.4, rong * 0.6)
    return max(so_dong_chu(_chu_tron(v), co, dam, w - 2 * LE_TRONG[0]) for v, w in zip(hang, r)) \
        * co * GIAN_DONG / 72.0 + 2 * LE_TRONG[1] + 0.02


def _chia_trang(khoi: List[Tuple[str, Any]], co: float, cao_toi_da: float, rong: float) -> List[List[Tuple[str, Any]]]:
    """Chia các khối vào trang ở cỡ `co`: không cắt câu; khối chữ chia theo đoạn, bảng chia theo hàng (lặp tiêu đề)."""
    trang: List[List[Tuple[str, Any]]] = [[]]
    cao = 0.0
    for k in khoi:
        manh: List[Tuple[str, Any]] = ([("chu", [x]) for x in k[1]] if k[0] == "chu"
                                       else [("bang", (k[1][0], [h])) for h in k[1][1]])
        for m in manh:
            h = _cao_khoi(m, co, rong)
            if trang[-1] and cao + h > cao_toi_da:
                trang.append([])
                cao = 0.0
            cuoi = trang[-1][-1] if trang[-1] else None
            if cuoi and cuoi[0] == m[0] == "chu":
                trang[-1][-1] = ("chu", cuoi[1] + m[1])
            elif cuoi and cuoi[0] == m[0] == "bang" and cuoi[1][0] == m[1][0]:
                trang[-1][-1] = ("bang", (cuoi[1][0], cuoi[1][1] + m[1][1]))
            else:
                trang[-1].append(m)
            cao = sum(_cao_khoi(x, co, rong) for x in trang[-1])
    return [t for t in trang if t]


def dung_trang_pptx(slides: Sequence[Slide], ten_de_tai: str, dong: Sequence[str], out_dir: Path,
                    ten_dc: str) -> Tuple[List[TrangPptx], List[str]]:
    """Các trang trình chiếu + cảnh báo (hình thiếu tệp…). Mỗi trang mang nguồn (mục, dòng) của slide dàn."""
    rong, cao_than = KHUNG_THAN[2], KHUNG_THAN[3] * DU_PHONG
    canh_bao: List[str] = []
    hinh = hinh_de_cuong(dong, out_dir)
    theo_neo: Dict[str, List[Dict[str, Any]]] = {}
    for h in hinh:
        if not h["co_tep"]:
            canh_bao.append(f"{h['so']}: không thấy tệp {h['rel']} — không nhúng (dựng lại hình của đề cương trước)")
            continue
        theo_neo.setdefault(_neo_hinh(h["ten"]), []).append(h)
    ra: List[TrangPptx] = []
    for s in slides:
        ghi = ("Ghi chú người trình bày — nguồn: " + ("; ".join(s.nguon) if s.nguon else "không có") + ".")
        ghi += "".join(f"\n⚠ {c}." for c in s.canh_bao)
        if s.khoa == "ten_de_tai":
            ra.append(TrangPptx("ten_de_tai", ten_de_tai or "Tên đề tài", f"Đề cương nộp: {ten_dc}", ghi,
                                [("chu", [("Chủ nhiệm đề tài: ……………………… (điền tay)", False, False),
                                          ("Đơn vị: ……………………… (điền tay)", False, False)])], 24, nguon=s.nguon))
        else:
            khoi = _khoi_cua_slide(s) or [("chu", [("(Đề cương không có nội dung cho slide này — xem ghi chú.)",
                                                     False, False)])]
            co = next((c for c in CO_THAN if sum(_cao_khoi(k, c, rong) for k in khoi) <= cao_than), None)
            phan = [khoi] if co is not None else _chia_trang(khoi, CO_THAN_TRANG, cao_than, rong)
            co = co or CO_THAN_TRANG
            for k, p in enumerate(phan):
                td = f"{s.so}. {s.tieu_de}" + (" (tiếp)" if k else "")
                ra.append(TrangPptx("noi_dung", td, f"Đề cương nộp: {_muc_ngan(s.nguon)}", ghi, p, co, nguon=s.nguon))
        for h in theo_neo.get(s.khoa, []):
            g = (f"Ghi chú người trình bày — nguồn: {h['rel']}, {h['so']} ở dòng {h['dong']} của đề cương nộp.")
            if h["ghi_chu"]:
                g += f"\nGhi chú của hình (nguyên văn): {h['ghi_chu']}"
            ra.append(TrangPptx("hinh", f"{h['so']}. {h['ten']}", f"Đề cương nộp: {h['so']} (dòng {h['dong']})", g,
                                hinh=h, nguon=[f"{h['so']} ở dòng {h['dong']}"]))
    return ra, canh_bao


def _rgb(m: Tuple[int, int, int]):
    from pptx.dml.color import RGBColor  # noqa: PLC0415

    return RGBColor(*m)


def _ghi_doan(tf, doan: Sequence[Tuple[str, float, bool, bool]], mau: Optional[Tuple[int, int, int]] = None,
              giua: bool = False) -> None:
    """Ghi các đoạn [(chữ, cỡ, đậm, gạch đầu dòng)] vào khung chữ; gạch đầu dòng có thụt treo."""
    from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN  # noqa: PLC0415
    from pptx.oxml.ns import qn  # noqa: PLC0415
    from pptx.util import Inches, Pt  # noqa: PLC0415

    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = Inches(LE_TRONG[0])
    tf.margin_top = tf.margin_bottom = Inches(LE_TRONG[1])
    for i, (van, co, dam, gach) in enumerate(doan):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(CACH_DOAN)
        if giua:
            p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = van
        r.font.size = Pt(co)
        r.font.bold = dam
        r.font.name = "Times New Roman"
        if mau:
            r.font.color.rgb = _rgb(mau)
        if gach:
            ppr = p._p.get_or_add_pPr()
            ppr.set("marL", str(int(Inches(LUI_GACH))))
            ppr.set("indent", str(-int(Inches(LUI_GACH))))
            bu = ppr.makeelement(qn("a:buChar"), {"char": "•"})
            ppr.append(bu)


def _vung_noi_dung(im, nguong: int = 245, dem: float = 0.02) -> Tuple[int, int, int, int]:
    """Khung (x0, y0, x1, y1) chứa nét vẽ của ảnh (điểm tối hơn `nguong`), nới thêm `dem` mỗi phía; ảnh trắng trơn ⇒
    cả ảnh."""
    w, h = im.size
    hop = im.convert("L").point(lambda v: 255 if v < nguong else 0).getbbox()
    if not hop:
        return 0, 0, w, h
    dx, dy = int(w * dem), int(h * dem)
    return max(0, hop[0] - dx), max(0, hop[1] - dy), min(w, hop[2] + dx), min(h, hop[3] + dy)


def _o_chu(slide, khung: Tuple[float, float, float, float], ten: str):
    from pptx.util import Inches  # noqa: PLC0415

    hop = slide.shapes.add_textbox(*(Inches(x) for x in khung))
    hop.name = ten
    return hop


def ghi_pptx(trang: Sequence[TrangPptx], dich: Path) -> Path:
    """Ghi tệp .pptx (ghi tệp tạm rồi đổi tên)."""
    from PIL import Image  # noqa: PLC0415
    from pptx import Presentation  # noqa: PLC0415
    from pptx.util import Emu, Inches  # noqa: PLC0415

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(KHO_SLIDE[0]), Inches(KHO_SLIDE[1])
    trang_trong = prs.slide_layouts[6]
    tong = len(trang)
    for so, t in enumerate(trang, 1):
        sl = prs.slides.add_slide(trang_trong)
        rong_td = KHUNG_TIEU_DE[2] - 2 * LE_TRONG[0]
        if t.loai == "ten_de_tai":
            co_td = next((c for c in (36, 32, 30, 28, 26, 24) if do_cao_doan([(t.tieu_de, c, True, 0.0)], rong_td)
                          <= 3.2 * DU_PHONG), 24)
            hop = _o_chu(sl, (LE, 1.5, KHUNG_TIEU_DE[2], 3.3), "TieuDe")
            _ghi_doan(hop.text_frame, [(t.tieu_de, co_td, True, False)], MAU_TIEU_DE, giua=True)
            hop = _o_chu(sl, (LE, 5.0, KHUNG_TIEU_DE[2], 1.4), "Than")
            _ghi_doan(hop.text_frame, [(v, t.co, d, g) for v, d, g in t.khoi[0][1]], giua=True)
        else:
            co_td = next((c for c in CO_TIEU_DE if do_cao_doan([(t.tieu_de, c, True, 0.0)], rong_td)
                          <= (KHUNG_TIEU_DE[3] - 2 * LE_TRONG[1]) * DU_PHONG), None)
            khung_td = KHUNG_TIEU_DE
            if co_td is None:  # tên hình dài: nới khung tiêu đề xuống phần thân (ảnh co lại), chữ không dưới 18 pt
                khung_td = (LE, 0.3, KHUNG_TIEU_DE[2], 1.6)
                co_td = next((c for c in (24, 22, 20, 18) if do_cao_doan([(t.tieu_de, c, True, 0.0)], rong_td)
                              <= (khung_td[3] - 2 * LE_TRONG[1]) * DU_PHONG), 18)
            hop = _o_chu(sl, khung_td, "TieuDe")
            _ghi_doan(hop.text_frame, [(t.tieu_de, co_td, True, False)], MAU_TIEU_DE)
            if t.loai == "hinh":
                with Image.open(t.hinh["tep"]) as im:
                    w, h = im.size
                    x0, y0, x1, y1 = _vung_noi_dung(im)
                top = khung_td[1] + khung_td[3] + 0.1
                ch_cao = KHUNG_CHAN[1] - 0.1 - top
                tl = min(KHUNG_THAN[2] / (x1 - x0), ch_cao / (y1 - y0))
                ww, hh = (x1 - x0) * tl, (y1 - y0) * tl
                pic = sl.shapes.add_picture(str(t.hinh["tep"]), Inches(LE + (KHUNG_THAN[2] - ww) / 2), Inches(top),
                                            Inches(ww), Inches(hh))
                # lề trắng của ảnh (sơ đồ matplotlib để trống nhiều) được XÉN HIỂN THỊ — tệp nhúng vẫn đúng từng byte
                pic.crop_left, pic.crop_top = x0 / w, y0 / h
                pic.crop_right, pic.crop_bottom = 1 - x1 / w, 1 - y1 / h
                pic.name = "Hinh"
            else:
                y = KHUNG_THAN[1]
                for k in t.khoi:
                    cao = _cao_khoi(k, t.co, KHUNG_THAN[2])
                    if k[0] == "chu":
                        hop = _o_chu(sl, (LE, y, KHUNG_THAN[2], cao / DU_PHONG), "Than")
                        _ghi_doan(hop.text_frame, [(v, t.co, d, g) for v, d, g in k[1]])
                        y += cao / DU_PHONG
                    else:
                        cot, hang = k[1]
                        ds = [cot] + list(hang)
                        gf = sl.shapes.add_table(len(ds), 2, Inches(LE), Inches(y), Inches(KHUNG_THAN[2]),
                                                 Emu(_emu_tron_len(cao)))
                        gf.name = "Bang"
                        bang = gf.table
                        bang.columns[0].width = Emu(int(Inches(KHUNG_THAN[2] * 0.4)))
                        bang.columns[1].width = Emu(int(Inches(KHUNG_THAN[2] * 0.6)))
                        for r, h in enumerate(ds):
                            bang.rows[r].height = Emu(_emu_tron_len(_cao_hang_bang(h, t.co, KHUNG_THAN[2], r == 0)))
                            for c, v in enumerate(h):
                                o = bang.cell(r, c)
                                o.margin_left = o.margin_right = Inches(LE_TRONG[0])
                                o.margin_top = o.margin_bottom = Inches(LE_TRONG[1])
                                o.text_frame.clear()
                                _ghi_doan(o.text_frame, [(_chu_tron(v), t.co, r == 0, False)])
                        y += cao + 0.1
        hop = _o_chu(sl, KHUNG_CHAN, "ChanTrang")
        _ghi_doan(hop.text_frame, [(f"{t.chan} · trang {so}/{tong}", CO_CHAN, False, False)], MAU_CHAN)
        sl.notes_slide.notes_text_frame.text = t.ghi
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    tam = dich.with_name(dich.stem + ".tam.pptx")
    prs.save(str(tam))
    os.replace(tam, dich)
    return dich


def kiem_pptx(p: Path, trang: Sequence[TrangPptx], dong: Sequence[str]) -> List[str]:
    """Mở lại tệp bằng python-pptx và kiểm: số trang; mỗi trang trỏ đúng nguồn (chân trang + ghi chú); ảnh nhúng trùng
    từng byte tệp hình của đề cương; mọi câu thân/ô bảng là nguyên văn đề cương (S1); không khung chữ nào tràn (đo lại
    bằng phông thật); cỡ chữ thân ≥ 18 pt. Rỗng = đạt."""
    from pptx import Presentation  # noqa: PLC0415
    from pptx.util import Emu  # noqa: PLC0415

    loi: List[str] = []
    prs = Presentation(str(p))
    sl = list(prs.slides)
    if len(sl) != len(trang):
        loi.append(f"số trang {len(sl)} khác số trang dựng {len(trang)}")
    van_dc = _chu_tron(" ".join(re.sub(r"\s+", " ", d) for d in dong))
    in_ = 914400.0
    for so, (s, t) in enumerate(zip(sl, trang), 1):
        ghi = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
        for x in t.nguon:
            if x not in ghi:
                loi.append(f"trang {so}: ghi chú người trình bày thiếu nguồn «{x[:60]}»")
        chan = next((sh for sh in s.shapes if sh.name == "ChanTrang"), None)
        if chan is None or not chan.text_frame.text.startswith(t.chan):
            loi.append(f"trang {so}: chân trang không trỏ mục đề cương")
        if t.loai == "hinh":
            anh = [sh for sh in s.shapes if sh.shape_type == 13]
            sha = hashlib.sha256(Path(t.hinh["tep"]).read_bytes()).hexdigest()
            if len(anh) != 1 or hashlib.sha256(anh[0].image.blob).hexdigest() != sha:
                loi.append(f"trang {so}: ảnh nhúng không trùng tệp {t.hinh['rel']}")
            elif anh[0].top + anh[0].height > int(KHUNG_CHAN[1] * in_) or anh[0].left + anh[0].width > \
                    int((KHO_SLIDE[0] - LE + 0.01) * in_):
                loi.append(f"trang {so}: ảnh {t.hinh['rel']} tràn khung")
        for sh in s.shapes:
            if sh.has_text_frame:
                doan = [("".join(r.text for r in pp.runs), (pp.runs[0].font.size or Emu(0)).pt if pp.runs else 0,
                         bool(pp.runs and pp.runs[0].font.bold),
                         LUI_GACH if pp._p.pPr is not None and pp._p.pPr.get("marL") else 0.0)
                        for pp in sh.text_frame.paragraphs]
                cao = do_cao_doan(doan, sh.width / in_ - 2 * LE_TRONG[0]) + 2 * LE_TRONG[1]
                if cao > sh.height / in_ + 1e-6:
                    loi.append(f"trang {so}: khung «{sh.name}» tràn chữ ({cao:.2f} > {sh.height / in_:.2f} inch)")
                if sh.name == "Than":
                    for v, co, dam, lui in doan:
                        if co and co < 18:
                            loi.append(f"trang {so}: cỡ chữ thân {co:g} pt < 18 pt")
                        if t.loai == "noi_dung" and lui and _chu_tron(v) not in van_dc:
                            loi.append(f"trang {so}: câu không nguyên văn đề cương «{v[:60]}»")
            if sh.has_table:
                bang = sh.table
                cao = 0.0
                for r, row in enumerate(bang.rows):
                    o = [row.cells[c].text_frame.text for c in range(len(bang.columns))]
                    chay = row.cells[0].text_frame.paragraphs[0].runs[0]
                    can = _cao_hang_bang((o[0], o[1]), chay.font.size.pt, sh.width / in_, bool(chay.font.bold))
                    if can > row.height / in_ + 1e-6:
                        loi.append(f"trang {so}: hàng bảng {r + 1} tràn chữ")
                    cao += row.height / in_
                    for v in o:
                        if _chu_tron(v) not in van_dc:
                            loi.append(f"trang {so}: ô bảng không nguyên văn đề cương «{v[:60]}»")
                if sh.top / in_ + cao > KHUNG_CHAN[1] + 1e-6:
                    loi.append(f"trang {so}: bảng tràn xuống chân trang")
    return loi


# ── PII · Word · điều phối ───────────────────────────────────────────────────────────────────────────────────────────

def quet_pii(van: str, bo_qua: Sequence[str] = ()) -> List[str]:
    """Dòng có mẫu định danh (bỏ DOI/URL, PMID trước khi dò — cùng cách K7 của kiểm đề cương nộp).

    `bo_qua`: đúng các chuỗi công cụ TỰ in (tiền tố mã băm đề cương) — không bỏ mẫu chung kiểu «chuỗi hex», vì số
    CCCD 12 chữ số cũng là một chuỗi hex hợp lệ."""
    ra: List[str] = []
    for i, d in enumerate(van.splitlines(), 1):
        s = re.sub(r"PMID:?\s*\d+", " ", _DOI_URL_RE.sub(" ", d))
        for x in bo_qua:
            s = s.replace(x, " ")
        for ten, mau in CC._PII_PATTERNS:
            if mau.search(s):
                ra.append(f"dòng {i}: mẫu {ten}")
    return ra


def tim_cong_cu_word() -> Optional[Path]:
    """`tools/md_sang_docx_times.py` của REPO GỐC: biến EBM_GOC_REPO → thư mục cha của repo y khoa → (worktree)
    thư mục cha của bản checkout chính suy từ `git --git-common-dir`. Không đường dẫn cứng một máy."""
    ung: List[Path] = []
    if os.environ.get("EBM_GOC_REPO"):
        ung.append(Path(os.environ["EBM_GOC_REPO"]) / "tools" / CONG_CU_WORD)
    ung.append(BASE.parent / "tools" / CONG_CU_WORD)
    try:
        r = subprocess.run(["git", "-C", str(BASE), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                           capture_output=True, text=True, encoding="utf-8", timeout=20)
        if r.returncode == 0 and r.stdout.strip():
            chung = Path(r.stdout.strip())
            if chung.name == ".git":
                ung.append(chung.parent.parent / "tools" / CONG_CU_WORD)
            else:
                # B1 (24/11/2026): `.git` dời ra `~/.ebm-git/<tên>.git` ngoài OneDrive — cha của common dir KHÔNG phải
                # bản checkout chính; bản checkout chính khai ở config `ebm.cayChinh`.
                k = subprocess.run(["git", "-C", str(BASE), "config", "--get", "ebm.cayChinh"],
                                   capture_output=True, text=True, encoding="utf-8", timeout=20)
                if k.returncode == 0 and k.stdout.strip():
                    ung.append(Path(k.stdout.strip()).parent / "tools" / CONG_CU_WORD)
    except (OSError, subprocess.SubprocessError):
        pass
    return next((p for p in ung if p.is_file()), None)


def xuat_word(md: Path) -> Tuple[bool, str]:
    cong_cu = tim_cong_cu_word()
    if cong_cu is None:
        return False, (f"không tìm thấy tools/{CONG_CU_WORD} của repo gốc (đặt EBM_GOC_REPO=<gốc repo>) — chạy tay ở "
                       f'repo gốc: python3 tools/{CONG_CU_WORD} "{md.as_posix()}" --co-chu 13 --trang-de-cuong')
    try:
        r = subprocess.run([sys.executable, str(cong_cu), str(md), "--co-chu", "13", "--trang-de-cuong"],
                           capture_output=True, text=True, encoding="utf-8", timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"lỗi gọi {CONG_CU_WORD}: {exc}"
    duoi = (r.stdout + r.stderr).strip().splitlines()[-2:]
    return r.returncode == 0, f"mã {r.returncode}: " + " / ".join(duoi)


def dung_goi(study: str, out_dir: Path) -> Dict[str, Any]:
    """Dựng cả gói trong bộ nhớ (không ghi gì). Trả {loi?, slide_md, cau_hoi_md, tom_tat}."""
    p_dc = out_dir / TEN_DE_CUONG.format(study=study)
    if not p_dc.is_file():
        return {"loi": f"thiếu đề cương nộp {p_dc.name} trong {out_dir.as_posix()}"}
    van = p_dc.read_text(encoding="utf-8")
    dong = van.splitlines()
    sha = hashlib.sha256(p_dc.read_bytes()).hexdigest()
    slides, ten_de_tai = dung_slide(dong, out_dir)
    nhom_bb, dem_bb = cau_hoi_bien_ban(out_dir, dong, p_dc.name)
    bc = tim_bao_cao(out_dir, study)
    cac_muc = doc_muc(dong)
    cau_b = cau_hoi_bao_cao(bc, cac_muc, sha) if bc else []
    cau_c = cau_hoi_de_cuong(dong) if not dem_bb.get("tranh_bien") else []
    cau_d, tep_qd = cau_hoi_so_quyet_dinh(out_dir, dong, p_dc.name)
    _danh_so(nhom_bb, cau_b, cau_c, cau_d)
    slide_md = render_slide(slides, ten_de_tai, p_dc.name, len(dong), sha)
    cau_hoi_md = render_cau_hoi(ten_de_tai, p_dc.name, len(dong), sha, nhom_bb, dem_bb, bc, cau_b, cau_c, cau_d,
                                tep_qd)
    canh_bao_sua = sum(1 for nh in nhom_bb for g in nh.chung if g.canh_bao)
    da_xac_minh = sum(1 for nh in nhom_bb for g in nh.chung if g.nhan.startswith("Đề cương hiện hành, dòng")
                      and "chưa xác minh" not in g.nhan)
    tom_tat = {
        "study": study, "de_cuong": p_dc.name, "so_dong": len(dong), "sha256": sha,
        "slide": {"so": len(slides), "phut": sum(s.phut for s in slides),
                  "canh_bao": [f"slide {s.so}: {c}" for s in slides for c in s.canh_bao]},
        "cau_hoi": {"A_bien_ban": sum(1 for x in nhom_bb for c in x.cau if not c.noi_bo),
                    "N_noi_bo": sum(1 for x in nhom_bb for c in x.cau if c.noi_bo),
                    "A_bien_ban_tranh_bien": dem_bb.get("tranh_bien", 0),
                    "A_cong": sorted({x.gate for x in nhom_bb}, key=lambda g: HD.CONG.index(g) if g in HD.CONG else 99),
                    "A_trich_de_cuong_da_xac_minh": da_xac_minh, "A_canh_bao": canh_bao_sua,
                    "B_bao_cao": len(cau_b), "B_tep": bc.tep.name if bc else None, "C_de_cuong": len(cau_c),
                    "D_so_quyet_dinh": len(cau_d), "D_tep": list(tep_qd),
                    "D_canh_bao": sum(1 for c in cau_d for g in c.goi_y if g.canh_bao)},
        "pii": quet_pii(slide_md, (sha[:12],)) + quet_pii(cau_hoi_md, (sha[:12],)),
    }
    return {"slide_md": slide_md, "cau_hoi_md": cau_hoi_md, "tom_tat": tom_tat, "slides": slides,
            "ten_de_tai": ten_de_tai, "dong": dong, "ten_dc": p_dc.name}


def _in_tom_tat(t: Dict[str, Any], ghi: bool, dich: Path, study: str) -> None:
    s, c = t["slide"], t["cau_hoi"]
    print(f"GÓI BẢO VỆ HỘI ĐỒNG — {study}" + ("" if ghi else " (CHẠY KHÔ — chưa ghi gì)"))
    print(f"  Đề cương nộp: {t['de_cuong']} ({t['so_dong']} dòng)")
    print(f"  Dàn slide: {s['so']} slide · khoảng {_phut(s['phut'])} phút · {len(s['canh_bao'])} cảnh báo")
    for cb in s["canh_bao"]:
        print(f"    ⚠ {cb}")
    if c["A_bien_ban_tranh_bien"]:
        print(f"  Câu hỏi A (biên bản hội đồng cổng): {c['A_bien_ban']} câu từ {c['A_bien_ban_tranh_bien']} biên bản "
              f"tranh biện ({', '.join(c['A_cong'])}) · {c['A_trich_de_cuong_da_xac_minh']} câu đề cương đã sửa xác "
              f"minh được · {c['A_canh_bao']} cảnh báo · {c['N_noi_bo']} phản đối thiên về quy trình nội bộ (nhóm N)")
    else:
        print("  Câu hỏi A: CHƯA CÓ BIÊN BẢN HỘI ĐỒNG CỔNG — chỉ dùng báo cáo phản biện + đề cương (đã ghi nhãn)")
    print(f"  Câu hỏi B (báo cáo phản biện): {c['B_bao_cao']} câu" + (f" từ {c['B_tep']}" if c["B_tep"] else
                                                                       " (không có báo cáo)"))
    if c.get("D_tep"):
        print(f"  Câu hỏi D (sổ quyết định hội đồng nghiên cứu): {c['D_so_quyet_dinh']} câu từ {len(c['D_tep'])} sổ"
              f" · {c['D_canh_bao']} cảnh báo phần đề cương đã thay không còn nguyên văn")
    if c["C_de_cuong"]:
        print(f"  Câu hỏi C (từ đề cương — không phải phản đối thật): {c['C_de_cuong']} câu")
    if t["pii"]:
        print(f"  🔴 Có mẫu định danh trong đầu ra ({len(t['pii'])}): " + "; ".join(t["pii"][:5]) + " — KHÔNG ghi")
    ten = (TEN_SLIDE.format(study=study), TEN_CAU_HOI.format(study=study))
    print(("  Đã ghi: " if ghi else "  Sẽ ghi: ") + " · ".join((dich / x).as_posix() for x in ten) + " (+ .docx)")
    if not ghi:
        print("  Ghi thật: thêm --ghi (khi bác sĩ đồng ý). Xem toàn văn: --xem")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Gói chuẩn bị bảo vệ đề cương trước Hội đồng (dàn slide + câu hỏi).")
    ap.add_argument("--study", required=True, help="mã đề tài (thư mục exports/<mã>/)")
    ap.add_argument("--exports-root", type=Path, default=BASE / "exports", help="thư mục exports (mặc định của repo)")
    ap.add_argument("--ghi", action="store_true", help="ghi tệp (mặc định CHẠY KHÔ)")
    ap.add_argument("--thu-muc-ra", type=Path, help="ghi vào thư mục này thay vì exports/<mã>/ (bản xem thử)")
    ap.add_argument("--khong-word", action="store_true", help="không xuất .docx")
    ap.add_argument("--khong-pptx", action="store_true", help="không xuất tệp trình chiếu .pptx")
    ap.add_argument("--xem", action="store_true", help="in toàn văn hai tài liệu ra màn hình")
    ap.add_argument("--json", action="store_true", help="in tóm tắt dạng JSON")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print(f"❌ mã đề tài không hợp lệ: {a.study!r}", file=sys.stderr)
        return 3
    out_dir = a.exports_root / a.study
    goi = dung_goi(a.study, out_dir)
    if "loi" in goi:
        print(f"❌ {goi['loi']}", file=sys.stderr)
        return 2
    t = goi["tom_tat"]
    dich = a.thu_muc_ra or out_dir
    if a.xem:
        print(goi["slide_md"])
        print("\n" + "=" * 100 + "\n")
        print(goi["cau_hoi_md"])
    ma = 0
    trang: List[TrangPptx] = []
    if not a.khong_pptx:
        try:
            trang, cb_hinh = dung_trang_pptx(goi["slides"], goi["ten_de_tai"], goi["dong"], out_dir, goi["ten_dc"])
            t["pptx"] = {"so_trang": len(trang), "so_hinh": sum(1 for x in trang if x.loai == "hinh"),
                         "canh_bao": cb_hinh}
        except ImportError as exc:  # thiếu Pillow/matplotlib để đo phông
            t["pptx"] = {"loi": f"không dựng được tệp trình chiếu: {exc}"}
    if t["pii"]:
        ma = 3
    elif a.ghi:
        dich.mkdir(parents=True, exist_ok=True)
        t["word"] = {}
        for ten, noi_dung in ((TEN_SLIDE, goi["slide_md"]), (TEN_CAU_HOI, goi["cau_hoi_md"])):
            p = dich / ten.format(study=a.study)
            p.write_text(noi_dung, encoding="utf-8", newline="\n")
            if not a.khong_word:
                ok, msg = xuat_word(p)
                t["word"][p.name] = msg
                if not ok:
                    ma = 1
        if trang:
            try:
                p = ghi_pptx(trang, dich / TEN_PPTX.format(study=a.study))
                loi = kiem_pptx(p, trang, goi["dong"])
                t["pptx"].update({"tep": p.name, "kiem": loi})
                if loi:
                    ma = 1
            except ImportError as exc:  # chưa cài python-pptx (requirements.txt)
                t["pptx"] = {"loi": f"chưa cài python-pptx: {exc}"}
                ma = 1
        elif "loi" in (t.get("pptx") or {}):
            ma = 1
    if a.json:
        print(json.dumps(t, ensure_ascii=False, indent=2))
    else:
        _in_tom_tat(t, a.ghi and ma != 3, dich, a.study)
        for ten, msg in (t.get("word") or {}).items():
            print(f"  Word {ten}: {msg}")
        px = t.get("pptx") or {}
        if px.get("loi"):
            print(f"  ⚠ Trình chiếu: {px['loi']}")
        elif px:
            print(f"  Trình chiếu: {px['so_trang']} trang ({px['so_hinh']} trang hình)"
                  + (f" · đã ghi {px['tep']}" if px.get("tep") else " · sẽ ghi " + TEN_PPTX.format(study=a.study)))
            for x in px.get("canh_bao") or []:
                print(f"    ⚠ {x}")
            if "kiem" in px:
                print("  Kiểm tệp trình chiếu: " + ("ĐẠT" if not px["kiem"] else f"{len(px['kiem'])} lỗi"))
                for x in px["kiem"][:20]:
                    print(f"    ✗ {x}")
        print(f"  {LOI_DAN}")
    return ma


if __name__ == "__main__":
    sys.exit(main())
