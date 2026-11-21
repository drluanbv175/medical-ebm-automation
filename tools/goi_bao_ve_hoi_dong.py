#!/usr/bin/env python3
"""Gói chuẩn bị BẢO VỆ đề cương trước Hội đồng Khoa học/Đạo đức của bệnh viện — dàn slide + câu hỏi phản biện dự kiến.

VÌ SAO (21/11/2026, bác sĩ giao «hoàn thiện khoảng trống hệ nghiên cứu»): đối chiếu mã sống thì hệ G0–G10 dựng được
đề cương nộp Hội đồng, có biên bản hội đồng cổng (phản đối của `phan-bien-tranh-bien`, phán quyết của
`trong-tai-tranh-bien`) và báo cáo phản biện đề cương — nhưng KHÔNG có công cụ nào chuẩn bị cho buổi BẢO VỆ: không có
dàn slide 10–15 phút, không có bộ câu hỏi Hội đồng có thể hỏi. Công cụ này chỉ GOM và SẮP XẾP nguyên liệu đã có; nó
không triệu tập hội đồng, không gọi agent, không gọi API (CLAUDE.md §0.6).

Đầu ra (tên MỚI — không đè artifact hợp đồng nào; `exports/` bị .gitignore nên không vào git):
  exports/<mã>/GOI_BAO_VE_DAN_SLIDE_<mã>.md  (+ .docx)  — dàn slide theo đúng các mục của đề cương nộp;
  exports/<mã>/GOI_BAO_VE_CAU_HOI_<mã>.md    (+ .docx)  — câu hỏi phản biện dự kiến, mỗi câu ghi nguồn.
Word dựng bằng `tools/md_sang_docx_times.py` của REPO GỐC (Times New Roman, `--trang-de-cuong`: mỗi slide một trang).

Nguồn CHỈ ĐỌC: `DE_CUONG_NOP_HOI_DONG_<mã>.md`, `hoi_dong/G*/` (biên bản tranh biện, biên bản xử lý việc sửa, sổ
quyết định bác sĩ), `PHAN_BIEN_DE_CUONG_NOP*_<mã>.md` (bản mới nhất), `G3_checkpoint.json` (N đã chốt).

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
  P1  Quét mẫu định danh (SĐT · CCCD · email — cùng bộ mẫu biên bản hội đồng dùng) trên cả hai đầu ra; có ⇒ KHÔNG ghi.

Ranh giới: TƯ VẤN cho chủ nhiệm — không sửa đề cương/biên bản/sổ cái, không ký, không mở/chặn cổng. Nội dung chuyên
môn chỉ là gợi ý; chủ nhiệm tự diễn đạt câu trả lời và kiểm lại với đề cương hiện hành.

Lệnh:
  python3 tools/goi_bao_ve_hoi_dong.py --study <mã> [--xem] [--json]          # CHẠY KHÔ (mặc định): không ghi gì
  python3 tools/goi_bao_ve_hoi_dong.py --study <mã> --ghi [--khong-word]       # ghi vào exports/<mã>/
  python3 tools/goi_bao_ve_hoi_dong.py --study <mã> --ghi --thu-muc-ra <dir>   # ghi bản xem thử ra thư mục khác
Mã thoát: 0 xong · 1 đã ghi .md nhưng chưa xuất được Word · 2 thiếu đề cương nộp · 3 tham số sai / đầu ra có mẫu PII.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
_SO_MUC_RE = re.compile(r"^((?:PHỤ LỤC\s+[A-Z])|\d+(?:\.\d+)*)\.?\s+(.*)$")
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


def tim_muc(cac_muc: Sequence[Muc], mau: str) -> Optional[Muc]:
    """Đề mục đầu tiên có tên (đã bỏ số) khớp biểu thức `mau` (so trên chuỗi đã chuẩn hoá)."""
    bt = re.compile(mau)
    return next((m for m in cac_muc if bt.search(_chuan(m.ten))), None)


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
        dau = [_chuan(o) for o in s.strip("|").split("|")]
        k_bp = next((k for k, o in enumerate(dau) if "biện pháp" in o), None)
        ra: List[Cau] = []
        j = i + 2
        while j <= muc.het and dong[j - 1].strip().startswith("|"):
            o = [x.strip() for x in dong[j - 1].strip().strip("|").split("|")]
            if o and o[0]:
                ra.append(Cau(o[0], j, phu=o[k_bp] if k_bp is not None and k_bp < len(o) else ""))
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
    ("muc_tieu", "Mục tiêu nghiên cứu", 1.0, (("Mục tiêu", r"^mục tiêu$", "danh_sach", 5, None),
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
    ("du_kien", "Dự kiến kết quả và phổ biến", 0.5, (("Dự kiến kết quả", r"^dự kiến kết quả$", "dau", 2, None),
                                                     ("Phổ biến", r"phổ biến", "dau", 1, None))),
)
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
    ten_muc = next((m for m in cac_muc if m.cap == 2), None)
    ten_de_tai = ten_muc.ten if ten_muc else ""
    n = n_da_chot(out_dir)
    ra: List[Slide] = []
    for so, (khoa, tieu_de, phut, phan) in enumerate(KHUON_SLIDE, 1):
        sl = Slide(so, khoa, tieu_de, phut)
        if khoa == "ten_de_tai":
            if ten_muc:
                sl.khoi.append((None, [Cau(ten_de_tai, ten_muc.dong)]))
                sl.nguon.append(f"tên đề tài ở dòng {ten_muc.dong}")
            else:
                sl.canh_bao.append("không tìm thấy tên đề tài (đề mục cấp 2 đầu tiên) — chủ nhiệm tự điền")
            ra.append(sl)
            continue
        for nhan_phu, mau, cach, so_cau, uu_tien in phan:
            muc = tim_muc(cac_muc, mau)
            if muc is None:
                sl.canh_bao.append(f"không tìm thấy mục «{nhan_phu or tieu_de}» trong đề cương — chủ nhiệm tự soạn "
                                   "phần này (máy không tự viết)")
                continue
            hang = cau_cua_bang(dong, muc) if cach == "bang" else []
            if hang:
                chon = hang[:so_cau]
                cac_cau = hang
            else:
                cac_cau = cau_cua_muc(dong, muc)
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
    return ra, ten_de_tai


def _phut(x: float) -> str:
    return (f"{x:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


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
                out += [f"- {c.van}" + (f" — biện pháp: {c.phu}" if c.phu else "") for c in ds] + [""]
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


# ── Kết xuất bộ câu hỏi ──────────────────────────────────────────────────────────────────────────────────────────────

def _dong_goi_y(g: GoiY) -> str:
    return f"- {g.nhan} «{g.trich}»" if g.trich else f"- {g.nhan}"


def _khoa_hoc(nh: NhomBienBan) -> List[CauHoi]:
    return [c for c in nh.cau if not c.noi_bo]


def _noi_bo(nh: NhomBienBan) -> List[CauHoi]:
    return [c for c in nh.cau if c.noi_bo]


def _danh_so(nhom_bb: Sequence[NhomBienBan], cau_b: Sequence[CauHoi], cau_c: Sequence[CauHoi]) -> None:
    """Đánh số đúng thứ tự kết xuất: A (khoa học/đạo đức — phần chính rồi lượt cũ) · B · C · N (quy trình nội bộ)."""
    chinh = [x for x in nhom_bb if x.cu_hon is None]
    cu = [x for x in nhom_bb if x.cu_hon is not None]
    for i, ch in enumerate([c for nh in chinh + cu for c in _khoa_hoc(nh)], 1):
        ch.ma = f"A{i}"
    for i, ch in enumerate(cau_b, 1):
        ch.ma = f"B{i}"
    for i, ch in enumerate(cau_c, 1):
        ch.ma = f"C{i}"
    for i, ch in enumerate([c for nh in chinh + cu for c in _noi_bo(nh)], 1):
        ch.ma = f"N{i}"


def _render_cau(ch: CauHoi) -> List[str]:
    out = [f"#### Câu {ch.ma} — {ch.tieu_de}", "", f"- Hội đồng có thể chất vấn: «{ch.chat_van}»",
           f"- Nguồn: {ch.nguon}."]
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
                   cau_c: Sequence[CauHoi]) -> str:
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
    out += ["", f"Tổng: {so_a} câu từ biên bản (nhóm A) · {len(cau_b)} câu từ báo cáo phản biện (nhóm B)"
            + (f" · {len(cau_c)} câu từ đề cương (nhóm C)" if cau_c else "")
            + (f" · {so_n} phản đối thiên về quy trình nội bộ để tra (nhóm N, cuối tài liệu)" if so_n else "") + ".",
            "", f"*{LOI_DAN}*", "", "---", ""]
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
            ung.append(Path(r.stdout.strip()).parent.parent / "tools" / CONG_CU_WORD)
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
    _danh_so(nhom_bb, cau_b, cau_c)
    slide_md = render_slide(slides, ten_de_tai, p_dc.name, len(dong), sha)
    cau_hoi_md = render_cau_hoi(ten_de_tai, p_dc.name, len(dong), sha, nhom_bb, dem_bb, bc, cau_b, cau_c)
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
                    "B_bao_cao": len(cau_b), "B_tep": bc.tep.name if bc else None, "C_de_cuong": len(cau_c)},
        "pii": quet_pii(slide_md, (sha[:12],)) + quet_pii(cau_hoi_md, (sha[:12],)),
    }
    return {"slide_md": slide_md, "cau_hoi_md": cau_hoi_md, "tom_tat": tom_tat}


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
    if a.json:
        print(json.dumps(t, ensure_ascii=False, indent=2))
    else:
        _in_tom_tat(t, a.ghi and ma != 3, dich, a.study)
        for ten, msg in (t.get("word") or {}).items():
            print(f"  Word {ten}: {msg}")
        print(f"  {LOI_DAN}")
    return ma


if __name__ == "__main__":
    sys.exit(main())
