#!/usr/bin/env python3
"""K18 — đối chiếu BẢN THẢO bài báo với TỪNG MỤC chuẩn báo cáo (chế độ «ban_thao» của bộ K17).

VÌ SAO (bác sĩ 21–22/11/2026): mọi khâu của đề tài, tới «Viết báo cáo & công bố kết quả», phải đạt từng mục chuẩn quốc
tế và Việt Nam, cho mọi thiết kế; «những gì không đạt chuẩn sẽ phải được loại bỏ». K17 (`kiem_chuan_de_cuong_theo_muc`)
chỉ đối chiếu ĐỀ CƯƠNG: mục `bao_cao` (tiêu đề, tóm tắt, ranh giới nhóm, diễn giải…) chỉ được liệt kê, mục `ke_hoach`
chỉ đòi «có kế hoạch». `kiem_ban_thao_tap_chi.py` đo thể lệ tạp chí nhưng chưa đối chiếu chuẩn báo cáo theo mục.

CÁCH KIỂM (tất định, không gọi mạng; dùng lại bộ chấm `cham_muc` của K17):
  1. Tách bản thảo theo chương IMRAD tiếng Việt và tiếng Anh (`IMRAD`): Tóm tắt/Abstract · Đặt vấn đề/Introduction ·
     Đối tượng và phương pháp/Methods · Kết quả/Results · Bàn luận/Discussion · Kết luận · Lời cảm ơn, tài trợ, xung đột
     lợi ích, tuyên bố. Cấp chương = cấp đề mục có NHIỀU chương lõi khác nhau nhất (tên bài «KẾT QUẢ ĐIỀU TRỊ…» ở cấp 1
     không bị nhận là chương). Tài liệu tham khảo và phụ lục bảng kiểm chuẩn báo cáo bị XOÁ TRẮNG trước khi chấm (giữ
     số dòng) — tên bài trong TLTK và chữ của bảng kiểm không được làm bằng chứng.
  2. Nhãn còn trống «…: chưa có thông tin» (bộ sinh thiếu dữ kiện) luôn đổi thành ô trống «………» — dòng còn ô trống không
     làm bằng chứng (luật `o_trong_quanh` của K17). Ô «[CẦN…]», «[TO BE COMPLETED…]»: chế độ NỘP (hoặc đã có số liệu)
     ⇒ «………» (nghiêm); chế độ NHÁP ⇒ «⟨chờ điền⟩» — chữ hướng dẫn trong ngoặc không làm bằng chứng, nhưng câu thật quanh
     ô (vd «Hội đồng Đạo đức … chấp thuận theo Quyết định số [CẦN…]», nhãn «Kết quả:» của tóm tắt) vẫn được nhận.
     Điều kiện «áp dụng khi» của mục phương pháp chỉ xét chương Phương pháp và chương của mục (`_pham_vi`) — câu bàn
     luận về nghiên cứu khác không kích hoạt mục.
  3. Mỗi mục của đề cương được đổi sang bản thảo: phần đề cương → chương IMRAD (`PHAN_SANG_IMRAD`); mục `ke_hoach` và
     `bao_cao` trở thành BẮT BUỘC và tìm ở Kết quả/Bàn luận; mục có cách viết riêng ở bài báo có tiêu chí ghi đè
     (`_GHI_DE`: STROBE 1a, 1b, 13c, 16b, 16c, 17, 20…; RECORD 1.1–1.3; chuẩn Việt Nam; CROSS 5d, 11c). RCT dùng
     CONSORT 2025 (42 mục, `_CONSORT`) thay SPIRIT 2025; tổng quan hệ thống/phân tích gộp dùng PRISMA 2020 (42 dòng —
     27 mục kể cả mục con, `_PRISMA_2020`; mục 2 chấm theo 12 mục PRISMA 2020 for Abstracts) thay PRISMA-P 2015.
     RCT theo cụm / không kém hơn thêm phần mở rộng CONSORT 2010 (Campbell 2012, Piaggio 2012) — cùng điều kiện
     kích hoạt với K17 (phần thiết kế CỦA ĐỀ TÀI, không theo tên chuẩn được dẫn); mục kết quả có tiêu chí
     bài báo riêng (số cụm, mất/loại hai mức, ICC ước tính, diễn giải theo giả thuyết không kém hơn).
  4. Bản thảo CHƯA CÓ SỐ LIỆU (còn ô [CẦN…], không ở chế độ nộp): mục thuộc trọn Kết quả/Bàn luận/Kết luận và yếu tố
     `so_lieu` (số liệu kết quả, số quyết định Hội đồng, đồng thuận/miễn) báo «chua_do» — KHÔNG BAO GIỜ là đạt.
     Mục phương pháp và cấu trúc vẫn chấm đầy đủ.
  5. Mục `bao_cao` của chuẩn khác chưa có tiêu chí bản thảo ⇒ «chua_do» (⚪), không đạt suông.

GIỚI HẠN (như K17): yếu tố có mặt ≠ nội dung đúng. Bộ kiểm bắt THIẾU một cách tin cậy; ĐẠT là «có dấu hiệu đủ yếu tố»,
người phân xử (binh-duyet, tham-dinh-dau-ra) đọc bằng chứng từng dòng. Yếu tố CẤM (câu suy nhân quả từ thiết kế cắt
ngang) chỉ bắt câu khẳng định không trích dẫn, không rào đón — câu khéo léo vẫn lọt; phản biện vẫn phải đọc.

Bản quyền: nguyên văn CONSORT 2025 (CC BY 4.0 — bản PLOS Med, PMID 40228477) và PRISMA 2020 (CC BY 4.0 — bản PLOS Med,
PMID 33780438; bản BMJ ghi «No commercial re-use» nên không chép) lấy từ `chuan_bao_cao_items.py`, sinh bằng
`sinh_chuan_bao_cao_items.py` từ XML Europe PMC sau khi đọc khối giấy phép. Chuẩn không mang giấy phép CC (CROSS…) chỉ
lưu mã mục và tiêu chí do hệ viết.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Sequence, Tuple

import chuan_bao_cao_items as CBC
import kiem_chuan_de_cuong_theo_muc as K
import skill_standards as S
import tieu_chi_chuan_de_cuong as TC
from kiem_chuan_de_cuong_theo_muc import KetQua, MucKiem, Phan, _y

# ───────────────────────────── chương IMRAD ─────────────────────────────
#: (khoá, biểu thức khớp ĐẦU đề mục sau khi bỏ số thứ tự) — thứ tự quan trọng: «ĐÓNG GÓP TÁC GIẢ» là `cuoi`, không
#: phải `tac_gia`; «ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP» là `phuong_phap`.
IMRAD: Tuple[Tuple[str, str], ...] = (
    ("tom_tat", r"TÓM TẮT|ABSTRACT|SUMMARY"),
    # «TỔNG QUAN TÀI LIỆU»: chương bối cảnh của báo cáo tổng hợp/luận văn (22/11/2026) — nơi trích dẫn và khoảng trống
    ("gioi_thieu", r"ĐẶT VẤN ĐỀ|GIỚI THIỆU|MỞ ĐẦU|TỔNG QUAN TÀI LIỆU|INTRODUCTION|BACKGROUND"),
    ("phuong_phap", r"(ĐỐI TƯỢNG(,| VÀ)? )?(VẬT LIỆU VÀ |CHẤT LIỆU VÀ )?PHƯƠNG PHÁP|(MATERIALS? AND )?METHODS?\b"),
    ("ca_lam_sang", r"(CA|BỆNH ÁN) LÂM SÀNG|TRÌNH BÀY CA|BÁO CÁO CA|CASE (PRESENTATION|REPORT|DESCRIPTION)"),
    ("ket_qua", r"KẾT QUẢ|RESULTS?\b"),
    ("ban_luan", r"BÀN LUẬN|DISCUSSION"),
    ("ket_luan", r"KẾT LUẬN|KIẾN NGHỊ|KHUYẾN NGHỊ|CONCLUSIONS?"),
    ("cuoi", r"LỜI CẢM ƠN|CẢM ƠN|TÀI TRỢ|NGUỒN (KINH PHÍ|TÀI TRỢ)|KINH PHÍ|XUNG ĐỘT LỢI ÍCH|TUYÊN BỐ|KHAI BÁO|ĐÓNG GÓP|"
             r"TÍNH (CÓ )?SẴN|CHIA SẺ DỮ LIỆU|ĐẠO ĐỨC|ACKNOWLEDG|FUNDING|CONFLICTS? OF INTEREST|COMPETING INTERESTS?|"
             r"DECLARATIONS?|DATA (SHARING|AVAILABILITY)|AUTHOR CONTRIBUTIONS?|ETHICS"),
    ("tltk", r"TÀI LIỆU THAM KHẢO|REFERENCES|BIBLIOGRAPHY"),
    ("phu_luc", r"PHỤ LỤC|APPENDIX|SUPPLEMENT"),
    ("tieu_de_muc", r"TIÊU ĐỀ|TITLE\b"),
    ("tac_gia", r"TÁC GIẢ|AUTHORS?\b"),
)
_LOI = ("tom_tat", "gioi_thieu", "phuong_phap", "ket_qua", "ban_luan", "ket_luan")
TEN_CHUONG: Dict[str, str] = {
    "tom_tat": "Tóm tắt/Abstract", "gioi_thieu": "Đặt vấn đề/Introduction", "phuong_phap": "Đối tượng và phương pháp/"
    "Methods", "ket_qua": "Kết quả/Results", "ban_luan": "Bàn luận/Discussion", "ket_luan": "Kết luận/Conclusion",
    "ca_lam_sang": "Trình bày ca/Case presentation", "cuoi": "Lời cảm ơn · tài trợ · xung đột lợi ích",
    "tieu_de": "Tiêu đề", "phu_luc": "Phụ lục",
}
#: chương bắt buộc theo thiết kế (báo cáo ca: không có Phương pháp/Kết quả, có Trình bày ca)
CHUONG_BAT_BUOC: Dict[str, Tuple[str, ...]] = {"case_report": ("tom_tat", "gioi_thieu", "ca_lam_sang", "ban_luan",
                                                                "ket_luan")}
_SO_TT_RE = re.compile(r"^\s*(?:[IVXLC]+|\d+(?:\.\d+)*)[.):]?\s+")
_BANG_KIEM_RE = re.compile(r"CHECKLIST|BẢNG KIỂM|STROBE|CONSORT|RECORD|STARD|TRIPOD|PRISMA|COREQ|SRQR|CHEERS|SQUIRE|"
                           r"CARE\b|CROSS\b|SPIRIT|chuẩn báo cáo", re.IGNORECASE)
_DE_MUC_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_MUC_TIEU_RE = re.compile(r"mục tiêu|nhằm|\bobjectives?\b|\baims?\b|\bpurpose\b", re.IGNORECASE)
#: ô chờ điền của người («[CẦN…]») — chế độ nháp đổi thành `CHO_DIEN`, chế độ nộp thành ô trống «………» của K17
_O_CAN_RE = re.compile(r"\[(?:CẦN|TO BE COMPLETED|CAN DIEN)[^\]\n]*\]", re.IGNORECASE)
CHO_DIEN = "⟨chờ điền⟩"
#: ô bảng chỉ có «…» (khung bảng kết quả chờ số) — ô trống ở chế độ nộp
_O_BANG_TRONG_RE = re.compile(r"(?<=\|)[ \t]*(?:…|\.{3})[ \t]*(?=\|)")
#: nhãn còn trống của bộ sinh («Sàng lọc: N = chưa có thông tin») — luôn là ô trống (giữ số dòng)
_O_TRONG_SINH = (
    (re.compile(r"(?<=[:=|])([*_\s]*)chưa có thông tin\b", re.IGNORECASE), r"\1………"),
    (re.compile(r"(?m)^([ \t]*)chưa có thông tin\b", re.IGNORECASE), r"\1………"),
)


#: Tiền tố chương của báo cáo tổng hợp/luận văn («CHƯƠNG 3. KẾT QUẢ…», «CHAPTER 2 METHODS») — đo thật 22/11/2026: K18
#: áp lên báo cáo nghiệm thu không nhận chương nào vì tên chương bắt đầu bằng «CHƯƠNG n.» ⇒ mọi mục báo «thiếu» giả.
_CHUONG_RE = re.compile(r"^\s*(?:CHƯƠNG|CHAPTER)\s+(?:[IVXLC]+|\d+)\s*[.:)\-–—]?\s*", re.IGNORECASE)


#: Câu khoảng trống «thiếu …» — gồm «Thiếu RCT/thử nghiệm/nghiên cứu … tại Việt Nam» (đo thật 22/11/2026).
_THIEU_KT = r"thiếu (số liệu|dữ liệu|bằng chứng|nghiên cứu|thử nghiệm|RCT)"


def _ten(td: str) -> str:
    """Tên đề mục để so: bỏ nhấn mạnh Markdown, tiền tố chương («CHƯƠNG 3.») và số thứ tự đầu («2.», «II.», «4.1.»)."""
    return _SO_TT_RE.sub("", _CHUONG_RE.sub("", re.sub(r"[*_`]", "", td))).strip()


def khoa_imrad(td: str) -> Optional[str]:
    t = _ten(td)
    for k, mau in IMRAD:
        if re.match(rf"(?:{mau})", t, re.IGNORECASE):
            return k
    return None


@dataclass
class BanThao:
    md_sach: str
    chuong: Dict[str, List[Phan]] = field(default_factory=dict)
    tieu_de: List[Phan] = field(default_factory=list)
    cac_phan: List[Phan] = field(default_factory=list)
    cap_chuong: int = 0

    def khoi(self, khoa: Sequence[str]) -> List[Phan]:
        """Các khối của những chương đã nêu (không trùng, theo thứ tự dòng)."""
        ra: List[Phan] = []
        for k in khoa:
            for p in (self.tieu_de if k == "tieu_de" else self.chuong.get(k, [])):
                if all(q.dong_dau != p.dong_dau for q in ra):
                    ra.append(p)
        return sorted(ra, key=lambda p: p.dong_dau)


def lam_sach(md: str, nghiem: bool = True) -> str:
    """Chuẩn hoá NFC; ô [CẦN…] ⇒ «………» (`nghiem`, chế độ nộp) hoặc «⟨chờ điền⟩» (nháp); nhãn trống bộ sinh ⇒ «………»."""
    md = _O_CAN_RE.sub("………" if nghiem else CHO_DIEN, unicodedata.normalize("NFC", md))
    if nghiem:
        md = _O_BANG_TRONG_RE.sub(" ……… ", md)
    for mau, thay in _O_TRONG_SINH:
        md = mau.sub(thay, md)
    return md


def tach_ban_thao(md: str, nghiem: bool = True) -> BanThao:
    """Tách bản thảo thành chương IMRAD; xoá trắng TLTK và phụ lục bảng kiểm; dựng khối tiêu đề, khối «MỤC TIÊU (trích)»
    (phạm vi «@muc_tieu:» của K17 — bài báo không có đề mục Mục tiêu riêng) và khối «⟦<chương>⟧» cho phạm vi
    «@phuong_phap,…:» của `K.dieu_kien`."""
    dong = lam_sach(md, nghiem).split("\n")
    de_muc = [(i, len(m.group(1)), m.group(2)) for i, d in enumerate(dong) for m in [_DE_MUC_RE.match(d)] if m]
    dem: Dict[int, set] = {}
    for _i, cap, td in de_muc:
        k = khoa_imrad(td)
        if k in _LOI:
            dem.setdefault(cap, set()).add(k)
    bt = BanThao("")
    if not dem:
        bt.md_sach = "\n".join(dong)
        bt.cac_phan = K.tach_phan(bt.md_sach)
        return bt
    cap_chuong = max(dem, key=lambda c: (len(dem[c]), -c))
    bt.cap_chuong = cap_chuong
    mo: List[Tuple[int, int, str, Optional[str]]] = []  # (dòng đầu, dòng cuối, tiêu đề, khoá)
    for k_, (i, cap, td) in enumerate(de_muc):
        if cap != cap_chuong:
            continue
        het = len(dong)
        for j, cap2, _ in de_muc[k_ + 1:]:
            if cap2 <= cap_chuong:
                het = j
                break
        mo.append((i, het, td, khoa_imrad(td)))
    xoa = set()
    for i, het, td, k in mo:
        if k == "tltk" or (k == "phu_luc" and _BANG_KIEM_RE.search(td)):
            xoa.update(range(i, het))
    dong = ["" if n in xoa else d for n, d in enumerate(dong)]
    bt.md_sach = "\n".join(dong)
    for i, het, td, k in mo:
        if i in xoa:
            continue
        bt.chuong.setdefault(k or "khac", []).append(Phan(td, i + 1, "\n".join(dong[i:het]), td))
    # tiêu đề = mọi đề mục (mọi cấp) đứng trước CHƯƠNG IMRAD đầu tiên (bài báo giao thức C1a: «# GIAO THỨC NGHIÊN
    # CỨU» rồi «## <tên bài>: giao thức nghiên cứu cắt ngang có phân tích»)
    dau_chuong = next((i for i, _h, _t, k in mo if k), len(dong))
    for i, cap, td in de_muc:
        # đề mục trên cấp chương luôn là tên bài, kể cả tên mở bằng chữ IMRAD («# KẾT QUẢ ĐIỀU TRỊ …»)
        if i < dau_chuong and (cap != cap_chuong or not khoa_imrad(td)):
            bt.tieu_de.append(Phan("(tiêu đề)", i + 1, re.sub(r"[*_`]", "", td)))
    for n, d in enumerate(dong[:dau_chuong]):
        t = d.strip()
        # tên bài có phụ đề sau dấu hai chấm («…: thử nghiệm ngẫu nhiên có đối chứng») vẫn là tên; nhãn kết thúc
        # bằng dấu hai chấm («**KẾT QUẢ:**») thì không (22/11/2026: tên báo cáo tổng hợp RCT/tổng quan gộp bị sót)
        m = re.fullmatch(r"\*\*([^*]{11,}[^*:\s])\*\*", t)
        if m and sum(c.isupper() for c in m.group(1)) >= 0.7 * sum(c.isalpha() for c in m.group(1)):
            bt.tieu_de.append(Phan("(tiêu đề tiếng Anh)", n + 1, m.group(1)))
    bt.tieu_de += bt.chuong.get("tieu_de_muc", [])
    bt.cac_phan = K.tach_phan(bt.md_sach)
    # khối phạm vi «⟦chương⟧» chỉ lấy THÂN chương (bỏ dòng đề mục): đề mục nháp «II. PHƯƠNG PHÁP *(… | Tự điền: ~75%)*»
    # của bộ sinh G7 từng làm điều kiện «tự điền» (phiếu tự điền ⇒ CROSS 2021) kích hoạt cho cả RCT và thuần tập
    for k, ds in list(bt.chuong.items()):
        bt.cac_phan += [Phan(f"⟦{k}⟧", p.dong_dau + 1, "\n".join(p.van.split("\n")[1:]), "") for p in ds]
    bt.cac_phan += [Phan("⟦tieu_de⟧", p.dong_dau, p.van, "") for p in bt.tieu_de]
    for k in ("gioi_thieu", "tom_tat"):
        for p in bt.chuong.get(k, []):
            for so, chu in K._don_vi(p):
                if _MUC_TIEU_RE.search(chu):
                    bt.cac_phan.append(Phan(f"MỤC TIÊU (trích từ {p.tieu_de})", so, chu, "MỤC TIÊU"))
    return bt


def thieu_cau_truc(bt: BanThao, thiet_ke: str, co_so_lieu: bool = True) -> List[str]:
    """Chương IMRAD bắt buộc còn thiếu (hoặc chỉ có tiêu đề, không có nội dung). Bản thảo chưa có số liệu: chương kết
    quả/bàn luận/kết luận chỉ chứa ô chờ điền là bình thường (chưa đo), chỉ báo khi THIẾU hẳn đề mục."""
    ma = S.canonical_design_code(thiet_ke) or ""
    ra = []
    for k in CHUONG_BAT_BUOC.get(ma, _LOI):
        ds = bt.chuong.get(k, [])
        if not ds:
            ra.append(f"thiếu chương {TEN_CHUONG[k]}")
            continue
        than = "\n".join("\n".join(p.van.split("\n")[1:]) for p in ds).replace(CHO_DIEN, "")
        if not re.search(r"\w", than) and (co_so_lieu or k not in CHUONG_KET_QUA):
            ra.append(f"chương {TEN_CHUONG[k]} không có nội dung")
    return ra


# ───────────────────────────── phần đề cương → chương bản thảo ─────────────────────────────
PHAN_SANG_IMRAD: Dict[str, Tuple[str, ...]] = {
    "bia": ("tieu_de", "tom_tat", "cuoi"), "dau": ("tieu_de",), "tom_tat": ("tom_tat",),
    "dat_van_de": ("gioi_thieu",), "tong_quan": ("gioi_thieu",),
    "muc_tieu": ("gioi_thieu", "tom_tat"), "cau_hoi": ("gioi_thieu", "tom_tat"),
    "dao_duc": ("phuong_phap", "cuoi"), "kinh_phi": ("cuoi", "phuong_phap"), "pho_bien": ("cuoi", "phuong_phap"),
    "quan_ly_dl": ("phuong_phap", "cuoi"), "nhan_luc": ("cuoi", "phuong_phap"),
    "du_kien_kq": ("ket_qua",), "ban_luan": ("ban_luan",), "han_che": ("ban_luan",),
    "phieu": ("phu_luc", "phuong_phap"), "bang_bien": ("phuong_phap", "phu_luc"),
    "danh_muc_ma": ("phuong_phap", "phu_luc"), "phu_luc_tim": ("phu_luc", "phuong_phap"),
    "trinh_bay_ca": ("ca_lam_sang", "phuong_phap", "ket_qua"),
}
#: chương chỉ có khi đã có số liệu
CHUONG_KET_QUA = frozenset({"ket_qua", "ban_luan", "ket_luan"})
#: chuẩn của ĐỀ CƯƠNG đổi sang chuẩn của BÀI BÁO cùng thiết kế
CHUAN_BAN_THAO: Dict[str, str] = {"SPIRIT 2025": "CONSORT 2025", "PRISMA-P 2015": "PRISMA 2020"}
NGUON_CHUAN_BAN_THAO: Dict[str, str] = {
    "CONSORT 2025": "Hopewell S et al. PLoS Med 2025;22(4):e1004587 (PMID 40228477; CC BY 4.0); cùng bản BMJ "
                    "2025;389:e081123 (PMID 40228833)",
    "PRISMA 2020": "Page MJ et al. PLoS Med 2021;18(3):e1003583 (PMID 33780438; CC BY 4.0); cùng bản BMJ 2021;372:n71 "
                   "(PMID 33782057)",
}

# ───────────────────────────── mẫu dùng cho bản thảo ─────────────────────────────
THIET_KE_QS = r"cắt ngang|thuần tập|đoàn hệ|bệnh[\s–-]*chứng|cross[\s-]*sectional|cohort|case[\s–-]*control"
#: tên sai lệch tiếng Việt và tiếng Anh (bảng sai lệch của bộ sinh G7 ghi «Selection bias», «Recall bias»…)
NGUON_SAI_LECH = (r"(sai số|sai lệch) (chọn|thông tin|nhớ lại|đo lường|phân loại|do không trả lời|kỳ vọng xã hội)|"
                  r"nhiễu|(selection|information|recall|measurement|misclassification|non-?response|reporting|"
                  r"detection|berkson|neyman|social desirability|interviewer|attrition|survivor|"
                  r"prevalence-incidence) bias|confounding|misclassification")
BIEN_PHAP_SAI_LECH = (r"khống chế|hạn chế|kiểm soát|biện pháp|tập huấn|chuẩn hoá|chuẩn hóa|nhập liệu kép|trích lại|"
                      r"độc lập|làm mù|ẩn danh|ngẫu nhiên|liên tiếp|ghép|đa biến|tiền định|matching|blinded|"
                      r"tránh|so sánh|đối chiếu")
NHAN_PP = r"Phương pháp|Đối tượng|Thiết kế|Methods?|Design|Setting|Participants"
NHAN_KQ = r"Kết quả|Results?"
NHAN_KL = r"Kết luận|Conclusions?"
SO_KQ = r"\d+[,.]\d+\s*%|\d+\s*%|\bKTC\b|\bCI\b|\b(OR|PR|RR|HR)\b\s*[=:(]?\s*\d|\bp\s*[<=>]\s*0"
SO_SANH_Y_VAN = (r"(tương tự|tương đồng|phù hợp|khác biệt|khác với|cao hơn|thấp hơn|so với|tương đương)[^.]{0,220}"
                 r"\[\d+|\[\d+\][^.]{0,220}(tương tự|tương đồng|phù hợp|khác biệt|khác với|cao hơn|thấp hơn|"
                 r"tương đương)")
#: (22/11/2026, phiên «G7 đọc sổ sàng lọc» báo) số NGƯỜI phải kèm đơn vị và không dính chữ: «G6 không có (sàng lọc…»
#: (dòng chỉ dẫn máy) và «Bảng 1 … đã phân tích» từng làm STROBE 13a đạt giả, CONSORT 22a có bằng chứng giả
SO_NGUOI = (r"(?<![\w/.,])\d[\d.,]*\s*(người bệnh|người tham gia|người|hồ sơ|đối tượng|bệnh nhân|trường hợp|lượt|"
            r"participants?|patients?)\b")
GIOI_HAN_NHAN_QUA = (r"nhân quả|trình tự thời gian|chiều (thời gian|của (mối )?(liên quan|tác động))|"
                     r"cùng (một )?thời điểm|causal|temporal")
CAU_NHAN_QUA = (r"\b(gây ra|gây nên|là nguyên nhân (của|gây)|dẫn (đến|tới)|làm (tăng|giảm)\b|"
                r"causes?|leads? to|increases? the risk)")
PHAN_NHOM_LIEN_TUC = (r"nhóm tuổi|phân nhóm|chia (thành|làm)\s*\d+\s*(nhóm|mức)|"
                      r"theo (nhóm|mức) (tuổi|BMI|eGFR|HbA1c|thu nhập)|(dưới|từ|trên)\s*\d+\s*tuổi")
RANH_GIOI = (r"[<>≤≥]\s*\d|\d+\s*[–-]\s*\d+\s*(tuổi|năm|kg|mmol|mg|%|mmHg)|từ \d+[,.]?\d*\s*(đến|tới)\s*\d+|"
             r"(dưới|trên|từ)\s*\d+[,.]?\d*\s*(tuổi|năm|kg|mmol|mg|%|mmHg|lần)")
DO_LUONG_TUONG_DOI = r"\b(OR|PR|RR|HR)\b|tỷ số (chênh|nguy cơ|tỷ lệ hiện mắc)|nguy cơ tương đối"
NGUY_CO_TUYET_DOI = (r"nguy cơ tuyệt đối|hiệu số (nguy cơ|tỷ lệ)|chênh lệch (tỷ lệ|nguy cơ)|\bNNT\b|\bNNH\b|"
                     r"\bARR\b|risk difference|absolute risk")
PHAN_TICH_KHAC = (r"phân tích (độ nhạy|nhạy cảm)|phân tích (nhóm nhỏ|phân nhóm)|nhóm nhỏ (tiền định|định trước)|"
                  r"tương tác|sensitivity|subgroup")
TIEU_CHUAN_CHON_BT = (r"Tiêu chuẩn (lựa )?chọn|tiêu chí (nhận|chọn|lựa chọn)|(được|đưa) (chọn|vào) (nghiên cứu|mẫu)|"
                      r"inclusion|(từ|≥)\s*\d+\s*tuổi|Người bệnh từ")
TIEU_CHUAN_LOAI_BT = r"Tiêu chuẩn loại|tiêu chí loại|Loại trừ|loại (khỏi|ra)|exclusion|exclude"
NGUON_KINH_PHI_BT = r"kinh phí|tài trợ|funding|funded|nguồn (tài trợ|kinh phí)"
VAI_TRO_TAI_TRO_BT = TC.VAI_TRO_TAI_TRO + r"|không nhận tài trợ|no (external )?funding"
KTC_BT = r"khoảng tin cậy|\bKTC\b|\bCI\b|Wilson|Clopper|DeLong|bootstrap"
SO_QD_HOI_DONG = r"(Quyết định|số|mã)\s*(số\s*)?[:\s]*[\w./-]*\d|approval (number|no)"
NGAY_DK = r"(đăng ký|registered)[^.]{0,100}(ngày|on\b|\d{1,2}/\d{1,2}/(19|20)\d{2}|(19|20)\d{2})"
MA_DK = r"\bNCT\d{8}\b|\bISRCTN\d+|\bACTRN\d+|\bChiCTR|\bCTRI/|\bTCTR\d+|\bDRKS\d+|\bjRCT|số đăng ký[^.]{0,40}\d"


#: mẫu của tiêu chí ĐỀ CƯƠNG đổi sang mẫu BẢN THẢO khi dùng lại cho mọi chuẩn (22/11/2026 — bản thảo G7 viết «Tiêu chí
#: nhận/loại», «Tài trợ: Không có tài trợ…», «95%CI»: STARD 6, 30, TRIPOD+AI 6b, 18a, SRQR S21 từng báo nhầm)
_MAU_THAY: Dict[str, str] = {}


def _thay_mau(yt):
    moi = _MAU_THAY.get(yt.mau)
    return replace(yt, mau=moi, de_muc=False) if moi else yt


def _g(phan: Tuple[str, ...], tieu_chi: str, yeu_to: tuple, khi: Optional[str] = None, ly_do: str = "",
       cung_doan: bool = False, chan: bool = True, ly_do_khong_chan: str = "", chi_de_cuong: bool = False) -> dict:
    return dict(phan=phan, tieu_chi=tieu_chi, yeu_to=yeu_to, khi=khi, ly_do=ly_do, cung_doan=cung_doan, chan=chan,
                ly_do_khong_chan=ly_do_khong_chan, chi_de_cuong=chi_de_cuong)


_CONSIDER = "chuẩn ghi «Consider…» — khuyến nghị, không bắt buộc: thiếu chỉ cảnh báo"

# ───────────────────────────── ghi đè tiêu chí cho bản thảo ─────────────────────────────
#: khoá (chuẩn, mã) hoặc (chuẩn, mã, thiết kế STROBE) → tiêu chí bản thảo (phần = chương IMRAD)
_GHI_DE: Dict[tuple, dict] = {
    # ───── STROBE 2007 ─────
    ("STROBE 2007", "1a"): _g(("tieu_de", "tom_tat"), "Tiêu đề hoặc tóm tắt nêu thiết kế bằng thuật ngữ thông dụng.",
                              (_y("tên thiết kế", THIET_KE_QS),)),
    ("STROBE 2007", "1b"): _g(("tom_tat",), "Tóm tắt có cấu trúc, cân đối giữa việc đã làm (phương pháp) và kết quả.",
                              (_y("phần phương pháp", NHAN_PP, nhan=True), _y("phần kết quả", NHAN_KQ, nhan=True),
                               _y("phần kết luận", NHAN_KL, nhan=True),
                               _y("số liệu kết quả chính", SO_KQ, so_lieu=True))),
    ("STROBE 2007", "2"): _g(("gioi_thieu",), "Nêu cơ sở khoa học có trích dẫn và lý do thực hiện (khoảng trống).",
                             (_y("trích dẫn nguồn", TC.TRICH_DAN),
                              _y("lý do/khoảng trống", r"khoảng trống|chưa (có|thấy|được|tìm thấy|rõ|biết)|"
                                                       r"còn (ít|hạn chế|thiếu)|ít (nghiên cứu|dữ liệu|số liệu)|"
                                                       + _THIEU_KT + r"|cần (thiết|có)|gap"))),
    # Phạm vi gồm Phương pháp: bản thảo BTM nêu «phân tích thăm dò» ở Xử lý số liệu, không ở Đặt vấn đề (22/11/2026) —
    # STROBE 3 đòi giả thuyết NẾU CÓ («any prespecified hypotheses»); phân tích thăm dò nêu rõ là đủ.
    ("STROBE 2007", "3"): _g(("gioi_thieu", "tom_tat", "phuong_phap"),
                             "Nêu mục tiêu cụ thể; mục tiêu phân tích liên quan kèm giả thuyết định trước hoặc nêu rõ "
                             "là phân tích thăm dò.",
                             (_y("mục tiêu cụ thể", r"(nhằm|mục tiêu)[^.]{0,60}(mô tả|xác định|phân tích|đánh giá|"
                                                    r"so sánh|ước tính|ước lượng|khảo sát|kiểm định)|"
                                                    r"\bObjectives?\b[^.]{0,30}(to |describe|determine|estimate|"
                                                    r"assess|xác định|mô tả)"),
                              _y("giả thuyết định trước hoặc nêu thăm dò", r"giả thuyết|\bH[0₀1₁]\b|thăm dò|"
                                                                          r"exploratory|hypothes",
                                 khi=K.MUC_TIEU_PHAN_TICH))),
    # «Nghiên cứu Đoàn hệ (Cohort)» của bộ sinh G7 — «đoàn hệ» đồng nghĩa «thuần tập» (22/11/2026, báo nhầm STROBE 4)
    ("STROBE 2007", "4"): _g(("phuong_phap", "tom_tat"), "Nêu các yếu tố then chốt của thiết kế: tên thiết kế và hướng "
                                                          "thời gian thu thập.",
                             (_y("tên thiết kế", THIET_KE_QS),
                              _y("hướng thời gian", r"hồi cứu|tiến cứu|(một|cùng) thời điểm|theo dõi|retrospective|"
                                                    r"prospective"))),
    # bệnh–chứng: yếu tố then chốt là cách xác định ca (ca mới mắc hay hiện mắc) — STROBE E&E mục 4
    ("STROBE 2007", "4", "benh_chung"): _g(("phuong_phap", "tom_tat"), "Nêu tên thiết kế và yếu tố then chốt (ca mới "
                                                                        "mắc/hiện mắc hoặc hướng thời gian).",
                                           (_y("tên thiết kế", THIET_KE_QS),
                                            _y("hướng thời gian/ca mới mắc", r"hồi cứu|tiến cứu|ca (bệnh )?mới|"
                                                                             r"mới mắc|hiện mắc|incident|prevalent|"
                                                                             r"retrospective|prospective"))),
    ("STROBE 2007", "6b", "benh_chung"): _g(("phuong_phap",), "Nghiên cứu ghép cặp: nêu tiêu chí ghép và số chứng cho "
                                                               "mỗi ca.",
                                            (_y("tiêu chí ghép", r"ghép (cặp )?theo|tiêu chí ghép|bắt cặp theo|"
                                                                 r"matching theo|matched (on|for|by)"),
                                             _y("số chứng mỗi ca", r"\b\d\s*:\s*\d\b|\d+ chứng (cho )?mỗi ca|"
                                                                   r"\d+\s*chứng\s*:\s*\d+\s*ca|controls? per case")),
                                            "@phuong_phap:" + K.GHEP_CAP, "có ghép cặp"),
    ("STROBE 2007", "6b", "thuan_tap"): _g(("phuong_phap",), "Nghiên cứu ghép cặp: nêu tiêu chí ghép và số người phơi "
                                                              "nhiễm/không phơi nhiễm.",
                                           (_y("tiêu chí ghép", r"ghép (cặp )?theo|tiêu chí ghép|bắt cặp theo|"
                                                                r"matching theo|matched (on|for|by)"),
                                            _y("tỷ lệ ghép", r"\b\d\s*:\s*\d\b|tỷ lệ\s*\d")),
                                           "@phuong_phap:" + K.GHEP_CAP, "có ghép cặp"),
    ("STROBE 2007", "9"): _g(("phuong_phap",), "Nêu cụ thể nguồn sai lệch tiềm tàng và biện pháp khống chế từng nguồn.",
                             (_y("nguồn sai lệch cụ thể", NGUON_SAI_LECH),
                              _y("biện pháp khống chế", BIEN_PHAP_SAI_LECH)), cung_doan=True),
    # biến định lượng tóm tắt bằng trung bình/trung vị là đã nêu «giữ dạng liên tục» (bản thảo mô tả)
    ("STROBE 2007", "11"): _g(("phuong_phap",), "Nêu cách xử lý biến định lượng trong phân tích (giữ liên tục hay phân "
                                                 "nhóm, ngưỡng và lý do).",
                              (_y("biến định lượng", r"định lượng|liên tục|continuous"),
                               _y("cách xử lý/ngưỡng", r"phân nhóm|ngưỡng|giữ (nguyên )?dạng liên tục|spline|"
                                                       r"mỗi \d+|tuyến tính|trung bình|trung vị|độ lệch chuẩn|\bSD\b|"
                                                       r"\bIQR\b|tứ phân vị|categori[sz]"))),
    ("STROBE 2007", "6a", "cat_ngang"): _g(("phuong_phap",), "Nêu tiêu chuẩn chọn, tiêu chuẩn loại, nguồn và cách chọn "
                                                              "người tham gia.",
                                           (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON_BT),
                                            _y("tiêu chuẩn loại", TIEU_CHUAN_LOAI_BT),
                                            _y("cách chọn người tham gia", r"chọn mẫu|lấy mẫu|ngẫu nhiên|thuận tiện|"
                                                                           r"toàn bộ|liên tiếp|hệ thống"))),
    ("STROBE 2007", "6a", "thuan_tap"): _g(("phuong_phap",), "Nêu tiêu chuẩn chọn/loại, nguồn và cách chọn người tham "
                                                              "gia, và cách theo dõi.",
                                           (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON_BT),
                                            _y("tiêu chuẩn loại", TIEU_CHUAN_LOAI_BT),
                                            _y("cách chọn người tham gia", r"chọn mẫu|lấy mẫu|ngẫu nhiên|toàn bộ|"
                                                                           r"liên tiếp"),
                                            _y("cách theo dõi", r"theo dõi|tái khám|kết thúc theo dõi"))),
    ("STROBE 2007", "6a", "benh_chung"): _g(("phuong_phap",), "Nêu tiêu chuẩn chọn, cách xác định ca, cách chọn chứng "
                                                               "và lý do chọn.",
                                            (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON_BT),
                                             _y("cách xác định ca", r"nhóm bệnh|ca bệnh|định nghĩa ca|xác định ca"),
                                             _y("cách chọn chứng", r"nhóm chứng|chọn chứng"),
                                             _y("lý do chọn ca và chứng", r"lý do (chọn|lựa chọn)|nhằm|để (bảo đảm|"
                                                                          r"tránh|đại diện)|đại diện cho"))),
    ("STROBE 2007", "10"): _g(("phuong_phap",), "Giải thích cách tính cỡ mẫu: công thức/phương pháp, tham số có nguồn, "
                                                 "cỡ mẫu cuối cùng.",
                              (_y("công thức/phương pháp", TC.CONG_THUC_CO_MAU),
                               # «p=0.50» (bộ sinh G7): «0[,.]5\b» cũ không khớp vì sau «5» là «0»
                               _y("tham số có nguồn", TC.THAM_SO_NGUON + r"|PMID\s*:?\s*\d{6,9}|doi\s*:?\s*10\.|"
                                                                         r"p\s*=\s*0[,.]50?\b.{0,100}(lớn nhất|tối đa|"
                                                                         r"thận trọng|chưa có (số liệu|dữ liệu|ước)|"
                                                                         r"không có (số liệu|dữ liệu))"),
                               _y("cỡ mẫu cuối cùng", TC.CO_MAU_CUOI))),
    ("STROBE 2007", "13a"): _g(("ket_qua",), "Báo cáo số người ở từng giai đoạn (đủ tiêu chuẩn, tham gia, phân tích).",
                               (_y("số người từng giai đoạn",
                                   SO_NGUOI + r"[^.;]{0,50}(đủ tiêu chuẩn|từ chối|bị loại|tham gia|được phân tích|"
                                              r"phân tích|sàng lọc|được mở|được mời|đủ dữ liệu)|"
                                   r"(đủ tiêu chuẩn|sàng lọc|phân tích|được mời)[^.;\n]{0,30}:\s*[Nn]\s*=\s*\d"),)),
    ("STROBE 2007", "13b"): _g(("ket_qua",), "Báo cáo lý do không tham gia ở từng giai đoạn.",
                               (_y("lý do không tham gia/bị loại", r"(bị loại|loại trừ|từ chối|không tham gia|không đủ)"
                                                                   r"[^.]{0,120}(lý do|vì|do)|lý do (từ chối|không "
                                                                   r"tham gia|bị loại|loại)[^.]{0,40}[\w\d]"),)),
    ("STROBE 2007", "13c"): _g(("ket_qua",), "Cân nhắc dùng sơ đồ luồng chọn người tham gia.",
                               (_y("sơ đồ luồng", r"(Hình|Sơ đồ|Biểu đồ|Figure)\s*\d*\.?[^\n]{0,80}(chọn|tuyển|luồng|"
                                                  r"flow|đối tượng|hồ sơ)|sơ đồ (chọn|tuyển|luồng)|flow diagram"),),
                               chan=False, ly_do_khong_chan=_CONSIDER),
    ("STROBE 2007", "14a"): _g(("ket_qua",), "Báo cáo đặc điểm người tham gia (nhân khẩu, lâm sàng, xã hội) và yếu tố "
                                              "nhiễu tiềm tàng.",
                               (_y("bảng đặc điểm", r"(Bảng|Table)\s*\d+[.:]?[^\n]{0,20}(Đặc điểm|baseline|"
                                                    r"characteristics)|Đặc điểm (chung|nền|của đối tượng)",
                                   de_muc=True),)),
    ("STROBE 2007", "14b"): _g(("ket_qua",), "Báo cáo số người thiếu dữ liệu theo từng biến.",
                               (_y("dữ liệu thiếu theo biến", r"thiếu[^.\n]{0,60}(\d|biến|ở)|không có (dữ liệu|giá trị)"
                                                              r" thiếu|đủ dữ liệu (mọi|tất cả|các) biến|"
                                                              r"complete case|ca đầy đủ|missing"),)),
    # thuần tập: «Nhóm 0: 254/2869 (8,9%)…» là số biến cố theo nhóm trong cửa sổ theo dõi (bản thảo G7) — 22/11/2026
    ("STROBE 2007", "15", "thuan_tap"): _g(("ket_qua",), "Báo cáo số biến cố hoặc chỉ số tóm tắt theo thời gian.",
                                           (_y("số biến cố/chỉ số theo thời gian", r"số biến cố|tỷ suất|người[\s-]năm|"
                                                                                   r"tích luỹ|tích lũy|\d+\s*/\s*\d+"
                                                                                   r"\s*\(\d|incidence|events?"),)),
    ("STROBE 2007", "15", "cat_ngang"): _g(("ket_qua",), "Báo cáo số ca/tỷ lệ kết cục.",
                                           (_y("số ca/tỷ lệ kết cục có số", r"(tỷ lệ|số (ca|người))[^.\n]{0,80}\d"),)),
    ("STROBE 2007", "16a"): _g(("ket_qua",), "Trình bày ước lượng thô và hiệu chỉnh kèm KTC; nêu biến đã hiệu "
                                              "chỉnh.",
                               (_y("ước lượng thô", r"\bthô\b|chưa hiệu chỉnh|đơn biến|crude|unadjusted"),
                                _y("ước lượng hiệu chỉnh", r"hiệu chỉnh|adjusted"),
                                _y("khoảng tin cậy", r"KTC|khoảng tin cậy|\bCI\b"),
                                # bảng «Mô hình đa biến» liệt kê từng biến của mô hình (bộ sinh G7) — biến hiệu chỉnh
                                # nêu theo hàng bảng
                                _y("biến được hiệu chỉnh", r"hiệu chỉnh (theo|cho)|điều chỉnh theo|adjusted for|"
                                                           r"(đã|sau khi) hiệu chỉnh|mô hình đa biến|"
                                                           r"multivariable model")),
                               K.MUC_TIEU_PHAN_TICH, "có mục tiêu phân tích liên quan"),
    ("STROBE 2007", "16b"): _g(("ket_qua", "phuong_phap"), "Báo cáo ranh giới nhóm khi phân nhóm biến liên tục.",
                               (_y("ranh giới nhóm", RANH_GIOI),), PHAN_NHOM_LIEN_TUC, "có phân nhóm biến liên tục"),
    ("STROBE 2007", "16c"): _g(("ket_qua", "ban_luan"), "Cân nhắc chuyển nguy cơ tương đối thành nguy cơ tuyệt đối.",
                               (_y("nguy cơ tuyệt đối", NGUY_CO_TUYET_DOI),), DO_LUONG_TUONG_DOI,
                               "có báo cáo số đo tương đối (OR/PR/RR/HR)", chan=False, ly_do_khong_chan=_CONSIDER),
    ("STROBE 2007", "17"): _g(("ket_qua",), "Báo cáo các phân tích khác đã làm (nhóm nhỏ, tương tác, độ nhạy).",
                              (_y("kết quả phân tích khác", PHAN_TICH_KHAC),), PHAN_TICH_KHAC,
                              "có phân tích nhóm nhỏ/tương tác/độ nhạy"),
    ("STROBE 2007", "18"): _g(("ban_luan",), "Tóm tắt kết quả chính theo mục tiêu nghiên cứu.",
                              # «Tỷ lệ … là 45%» mở đầu mỗi tiểu mục bàn luận theo mục tiêu (cách viết của bản thảo
                              # BTM) cũng là tóm tắt kết quả chính
                              (_y("kết quả chính", r"mục tiêu|phát hiện chính|kết quả chính|"
                                                   r"nghiên cứu (này )?(cho thấy|ghi nhận)|chúng tôi (thấy|ghi nhận)|"
                                                   r"trong nghiên cứu (này|của chúng tôi)|key (results|findings)|"
                                                   r"(tỷ lệ|trung bình|trung vị|\bPR\b|\bOR\b|\bHR\b|\bRR\b)"
                                                   r"[^.\n]{0,100}\b(là|đạt|chiếm|bằng)\s*\d"),)),
    ("STROBE 2007", "20"): _g(("ban_luan", "ket_luan"), "Diễn giải thận trọng: xét mục tiêu, hạn chế, đa phân tích, "
                                                         "đối chiếu nghiên cứu tương tự.",
                              (_y("đối chiếu nghiên cứu tương tự (có trích dẫn)", SO_SANH_Y_VAN),)),
    ("STROBE 2007", "20", "cat_ngang"): _g(("ban_luan", "ket_luan"),
                                           "Diễn giải thận trọng: đối chiếu nghiên cứu tương tự; thiết kế cắt ngang "
                                           "không cho suy nhân quả — nêu rõ giới hạn và không khẳng định nhân quả.",
                                           (_y("đối chiếu nghiên cứu tương tự (có trích dẫn)", SO_SANH_Y_VAN),
                                            _y("nêu giới hạn suy nhân quả của thiết kế cắt ngang", GIOI_HAN_NHAN_QUA,
                                               khi=K.MUC_TIEU_PHAN_TICH),
                                            _y("không khẳng định nhân quả từ dữ liệu cắt ngang", CAU_NHAN_QUA,
                                               cam=True))),
    ("STROBE 2007", "21"): _g(("ban_luan",), "Bàn phạm vi suy rộng (giá trị ngoại) của kết quả.",
                              (_y("suy rộng/giá trị ngoại", TC.SUY_RONG + r"|chỉ (đại diện|phản ánh|áp dụng)|"
                                                            r"không (đại diện|thể suy rộng)|"
                                                            r"generali[sz]ab"),)),
    ("STROBE 2007", "22"): _g(("cuoi", "phuong_phap"), "Nêu nguồn kinh phí và vai trò của đơn vị tài trợ.",
                              (_y("nguồn kinh phí", NGUON_KINH_PHI_BT), _y("vai trò của đơn vị tài trợ",
                                                                            VAI_TRO_TAI_TRO_BT)), cung_doan=True),
    # ───── RECORD 2015 ─────
    ("RECORD 2015", "1.1"): _g(("tieu_de", "tom_tat"), "Tiêu đề/tóm tắt nêu loại dữ liệu; nêu tên cơ sở dữ liệu khi "
                                                        "có tên (RECORD: «when possible»).",
                               (_y("loại dữ liệu thường quy", r"hồ sơ (bệnh án )?(điện tử|có sẵn)|bệnh án điện tử|"
                                                              r"dữ liệu (y tế )?(thu thập )?thường quy|cơ sở dữ liệu|"
                                                              r"electronic (health|medical) records?|registry|"
                                                              r"routinely collected|\bHIS\b|claims"),
                                _y("tên cơ sở dữ liệu", r"eHospital|\bHIS\b|VNPT|FPT\.eHospital|OneHealth",
                                   khi=r"eHospital|VNPT[- ]HIS|FPT\.eHospital|OneHealth"))),
    ("RECORD 2015", "1.2"): _g(("tieu_de", "tom_tat"), "Tiêu đề/tóm tắt nêu vùng địa lý và khung thời gian.",
                               (_y("vùng địa lý/cơ sở", r"Việt Nam|Vietnam|Thành phố|tỉnh|Hà Nội|Hồ Chí Minh|"
                                                        r"Bệnh viện|Hospital|Trung tâm|Khoa"),
                                _y("khung thời gian", r"\b(19|20)\d{2}\b"))),
    ("RECORD 2015", "1.3"): _g(("tieu_de", "tom_tat"), "Tiêu đề/tóm tắt nêu việc liên kết cơ sở dữ liệu.",
                               (_y("liên kết dữ liệu", K.LIEN_KET + r"|linked"),), K.LIEN_KET,
                               "có liên kết cơ sở dữ liệu"),
    # 22/11/2026: «Chủ nhiệm truy cập eHospital …» (BTM) nói AI truy cập — đúng ý RECORD 12.1; mẫu K17 chỉ nhận «quyền/
    # được cấp phép truy cập»
    ("RECORD 2015", "12.1"): _g(("phuong_phap", "cuoi"), "Nêu mức độ nhóm nghiên cứu được truy cập cơ sở dữ liệu dùng "
                                                          "để tạo quần thể.",
                                (_y("quyền/người truy cập dữ liệu", r"(quyền|được (cấp|phép)) truy cập|truy xuất|"
                                                                    r"người trích xuất|phân quyền|(chủ nhiệm|nghiên "
                                                                    r"cứu viên|nhóm nghiên cứu|tác giả|người trích)"
                                                                    r"[^.;]{0,40}(truy cập|truy xuất)|access(ed)? "
                                                                    r"(to )?the (database|records)"),)),
    # Quyết định chia sẻ dữ liệu là của chủ nhiệm/Hội đồng — bản nháp chưa có thì «chưa đo», chế độ nộp bắt buộc.
    ("RECORD 2015", "22.1"): _g(("cuoi", "phuong_phap"), "Nêu cách tiếp cận đề cương, dữ liệu thô hoặc mã phân tích.",
                                (_y("tài liệu được chia sẻ", r"đề cương|mã (phân tích|lập trình|lệnh|R)|script|"
                                                             r"dữ liệu (gốc|thô|giả danh|đã khử định danh)|bộ dữ liệu|"
                                                             r"(không|chưa) chia sẻ", so_lieu=True),
                                 _y("cách tiếp cận", r"cung cấp|chia sẻ|truy cập|công bố|lưu (trữ|tại)|theo yêu cầu",
                                    so_lieu=True)), cung_doan=True),
    # ───── Việt Nam ─────
    ("Việt Nam", "TT43-HĐĐ"): _g(("phuong_phap", "cuoi"), "Nêu Hội đồng Đạo đức đã chấp thuận kèm số quyết định.",
                                 (_y("chấp thuận của Hội đồng", r"(chấp thuận|thông qua|phê duyệt) của Hội đồng|"
                                                                r"Hội đồng (Đạo đức|đạo đức|Y đức|y đức).{0,120}"
                                                                r"(chấp thuận|thông qua|phê duyệt)|ethics committee|"
                                                                r"(IRB|Institutional Review Board)"),
                                  _y("số quyết định chấp thuận", SO_QD_HOI_DONG, so_lieu=True)), cung_doan=True),
    ("Việt Nam", "TT43-Đ7.1b"): _g(("phuong_phap", "cuoi"), "Miễn đồng thuận: nêu quyết định miễn và lý do (nguy cơ"
                                                             " tối thiểu, hồi cứu, không khả thi lấy đồng thuận).",
                                   (_y("quyết định miễn đồng thuận", K.MIEN_DONG_THUAN + r"|waiv", so_lieu=True),
                                    _y("lý do miễn", r"nguy cơ tối thiểu|không (khả thi|thể liên hệ|tiếp xúc)|"
                                                     r"(dữ liệu|hồ sơ) (sẵn có|có sẵn|hồi cứu)|hồi cứu|retrospective")),
                                   K.MIEN_DONG_THUAN, "được miễn đồng thuận"),
    ("Việt Nam", "TT43-ĐỒNG-THUẬN"): _g(("phuong_phap", "cuoi"), "Không miễn: nêu người tham gia được giải thích và "
                                                                  "đồng ý (ký phiếu đồng ý) trước khi tham gia.",
                                        (_y("đồng ý tham gia", r"(ký|đồng ý|đồng thuận|tự nguyện)[^.]{0,80}"
                                                               r"(tham gia|phiếu)|phiếu (đồng ý|đồng thuận|tình "
                                                               r"nguyện)|informed consent", so_lieu=True),),
                                        "!" + K.MIEN_DONG_THUAN, "không được miễn đồng thuận"),
    ("Việt Nam", "TT43-Đ16.6"): _g((), "Thẩm định rút gọn — thủ tục của hồ sơ đề cương, không là mục báo cáo bài báo.",
                                   (), chi_de_cuong=True),
    ("Việt Nam", "DLCN"): _g(("phuong_phap", "cuoi"), "Nêu biện pháp bảo vệ dữ liệu cá nhân (khử định danh/mã hoá, bảo "
                                                       "mật).",
                             (_y("khử định danh/mã hoá/bảo mật", TC.BAO_MAT + r"|giả danh|de-identif|anonymi"),)),
    # ───── COSMIN 2021 ─────
    # bộ câu hỏi «tự xây dựng, dùng lần đầu» đã nêu hiện trạng hiểu biết: chưa có bằng chứng đặc tính đo lường
    ("COSMIN 2021", "I4"): _g(("gioi_thieu", "phuong_phap"), "Tóm lược hiểu biết về đặc tính đo lường của phiên bản "
                                                              "(hoặc nêu công cụ mới, chưa có bằng chứng) và lý do.",
                              (_y("đặc tính đo lường đã biết", r"độ (tin cậy|giá trị)|Cronbach|đã (được )?kiểm định|"
                                                               r"chưa (được )?kiểm định|dùng lần đầu|tự xây dựng|"
                                                               r"phát triển mới|newly developed"),)),
    # ───── CROSS 2021 ─────
    ("CROSS 2021", "5d"): _g(("phuong_phap", "phu_luc"), "Cung cấp toàn bộ bộ câu hỏi (phụ lục/tài liệu bổ sung).",
                             (_y("bộ câu hỏi ở phụ lục", r"(bộ câu hỏi|phiếu|questionnaire)[^.]{0,80}(phụ lục|tài liệu "
                                                         r"bổ sung|supplement)|(phụ lục|tài liệu bổ sung|supplement)"
                                                         r"[^.]{0,80}(bộ câu hỏi|phiếu|questionnaire)"),)),
    ("CROSS 2021", "11c"): _g(("ket_qua",), "Báo cáo tỷ lệ đáp ứng kèm định nghĩa hoặc cách tính.",
                              (_y("tỷ lệ đáp ứng", r"tỷ lệ (đáp ứng|trả lời|tham gia)|response rate"),
                               _y("định nghĩa/cách tính", r"\d+\s*/\s*\d+|=|trên tổng|chia|được tính|định nghĩa")),
                              cung_doan=True),
}

_MAU_THAY.update({TC.TIEU_CHUAN_CHON: TIEU_CHUAN_CHON_BT, TC.TIEU_CHUAN_LOAI: TIEU_CHUAN_LOAI_BT,
                   TC.KINH_PHI: NGUON_KINH_PHI_BT, TC.VAI_TRO_TAI_TRO: VAI_TRO_TAI_TRO_BT})

# ═════════════════════════════════ COREQ 2007 (bản thảo định tính) — chương đúng bảng gốc ═════════════════════════════
_GHI_DE.update({
    # 22/11/2026: COREQ mục 4 «Gender — Was the researcher male or female?» thuộc Domain 1 (nhóm nghiên cứu và phản tư,
    # đặc điểm cá nhân) — bài báo nêu ở Phương pháp, cạnh người phỏng vấn (bản in lại bảng gốc trong PMC12567161,
    # PMC12731783). Tiêu chí đề cương xếp mục là «kế hoạch» nên bản chuyển đổi chỉ tìm ở Kết quả/Bàn luận — sai chỗ so
    # với chuẩn gốc; sửa phép đo, yếu tố giữ nguyên.
    ("COREQ 2007", "4"): _g(("phuong_phap", "ket_qua"), "Nêu giới của người phỏng vấn.",
                            (_y("giới người phỏng vấn", r"(người phỏng vấn|điều tra viên).{0,80}(nam|nữ|giới)"),)),
})

# ═════════════════════════════════ STARD 2015 (bản thảo chẩn đoán) — ghi đè báo nhầm ═════════════════════════════════
_GHI_DE.update({
    # «Gan nhiễm mỡ trên siêu âm kèm …» (tiêu chí nhận) là căn cứ xác định từ kết quả xét nghiệm trước
    ("STARD 2015", "7"): _g(("phuong_phap",), "Nêu căn cứ xác định người có thể đủ điều kiện (triệu chứng, kết quả xét "
                                               "nghiệm trước, sổ đăng ký).",
                            (_y("căn cứ xác định", r"triệu chứng|nghi ngờ|được chỉ định|kết quả (xét nghiệm )?trước|"
                                                   r"sổ đăng ký|danh sách|đến khám|có chỉ định|(trên|qua|theo) (siêu "
                                                   r"âm|xét nghiệm|chẩn đoán)"),)),
    ("STARD 2015", "13a"): _g(("phuong_phap",), "Người đọc xét nghiệm đánh giá có làm mù với chuẩn tham chiếu.",
                              (_y("làm mù người đọc xét nghiệm đánh giá",
                                  r"(index test|xét nghiệm (cần |chỉ điểm|được )?đánh giá|xét nghiệm chỉ điểm|FIB-4)"
                                  r"[^.|]{0,160}(không biết|che giấu|làm mù|\bmù\b|trước khi có|blind)|"
                                  r"(không biết|che giấu|làm mù|blind)[^.|]{0,80}(index test|xét nghiệm (cần |chỉ "
                                  r"điểm|được )?đánh giá)"),)),
    ("STARD 2015", "14"): _g(("phuong_phap",), "Nêu cách ước lượng/so sánh độ chính xác chẩn đoán và độ chính xác "
                                                "của ước lượng.",
                             (_y("chỉ số chính xác", r"độ nhạy|độ đặc hiệu|\bAUC\b|giá trị (dự|tiên) (báo|đoán)|"
                                                    r"tỷ số khả dĩ|\bLR\b"),
                              _y("độ chính xác ước lượng", KTC_BT))),
    # STARD 23: «Cross tabulation of the index test results (or their distribution) by the results of the reference
    # standard» — hình phân bố theo tình trạng bệnh là đủ
    ("STARD 2015", "23"): _g(("ket_qua",), "Bảng chéo/phân bố kết quả xét nghiệm đánh giá theo chuẩn tham chiếu.",
                             (_y("bảng chéo/phân bố theo chuẩn tham chiếu",
                                 r"bảng (2\s*[x×]\s*2|chéo|tiếp liên|hai chiều)|phân bố [^\n]{0,60}theo (tình trạng "
                                 r"bệnh|chuẩn tham chiếu)|(dương|âm) tính (thật|giả)"),)),
    ("STARD 2015", "26"): _g(("ban_luan",), "Bàn hạn chế (sai lệch, bất định) và khả năng khái quát.",
                             (_y("hạn chế/sai lệch", r"hạn chế|sai lệch|sai số"),
                              _y("suy rộng", TC.SUY_RONG + r"|(phổ bệnh|quần thể)[^.;]{0,60}khác|một (cơ sở|trung "
                                                           r"tâm)|generali[sz]ab"))),
    # «định nghĩa: Có ≥1 lần nhập viện … ghi trong hồ sơ …, đối chiếu giấy ra viện» là cách xác định kết cục (22/11)
    ("TRIPOD+AI 2024", "8a"): _g(("phuong_phap",), "Định nghĩa kết cục được dự báo, khoảng dự báo và cách xác định.",
                                 (_y("kết cục", r"kết cục|outcome"),
                                  _y("khoảng dự báo", r"(trong|sau) (vòng )?\d+ (ngày|tháng|năm)|khoảng (thời gian )?"
                                                      r"dự báo|horizon"),
                                  _y("cách xác định", r"xác định (bằng|qua|theo|là)|ghi nhận|đánh giá|định nghĩa|"
                                                      r"đối chiếu|ghi trong|ascertain")), cung_doan=True),
})

# ═════════════════════ Phần mở rộng CONSORT 2010 — thử nghiệm cụm và không kém hơn (bản thảo RCT) ═════════════════════
# 22/11/2026. Cùng bảng mục với K17 (`tieu_chi_chuan_de_cuong._CONSORT_CUM` / `_CONSORT_NI`, đối chiếu Campbell 2012 —
# PMID 22951546 — và Piaggio 2012 — PMID 23268518), cùng điều kiện kích hoạt (phần thiết kế CỦA ĐỀ TÀI nêu cụm/không kém
# hơn). Mục phương pháp dùng lại tiêu chí đề cương qua `sang_ban_thao`; mục dưới đây có cách viết riêng ở bài báo:
# tóm tắt (1b), sơ đồ luồng và số phân tích theo CỤM và CÁ NHÂN (13a, 13b, 16), đặc điểm nền hai mức (15), ICC ước tính
# (17a), diễn giải theo giả thuyết không kém hơn (22). Số liệu (`so_lieu`) chỉ đòi khi bản thảo đã có số liệu.
SO_CUM = r"\d+\s*(cụm|phòng khám|cơ sở)"
_CUM = r"(cụm|phòng khám|cơ sở)"
_SO_CUM_NHOM = SO_CUM + r"[^.\n]{0,160}(phân bổ|ngẫu nhiên|mỗi nhóm|nhóm (can thiệp|chứng))"
_MAT_CUM = r"(mất|loại|rút|ngừng)[^.\n]{0,160}" + _CUM + "|" + _CUM + r"[^.\n]{0,80}(mất|loại|rút|ngừng)"
_MAT_NGUOI = (r"(mất (theo dõi|dấu|liên lạc)|loại|rút (lui|khỏi)|ngừng)[^.\n]{0,160}(người|người tham gia)|"
              r"(người|người tham gia)[^.\n]{0,80}(mất theo dõi|bị loại|rút)")
_NEN_NGUOI = r"(đặc điểm|nền)[^\n]{0,160}(người tham gia|cá nhân|người bệnh)"
_NEN_CUM = (r"(đặc điểm|nền)[^\n]{0,160}(mức cụm|của (các )?" + _CUM + r"|theo " + _CUM + r")|"
            + _CUM + r"[^\n]{0,80}(quy mô|số người bệnh|đặc điểm)")
_SO_CUM_PT = SO_CUM + r"[^.\n]{0,160}(phân tích|đưa vào)|(phân tích|đưa vào)[^.\n]{0,160}" + SO_CUM
_ICC_SO = r"(ICC|tương quan nội cụm)[^.\n]{0,80}\d[,.]\d+"
_DIEN_GIAI_NI = (r"(không kém hơn|tương đương|non-?inferior)[^.\n]{0,200}(kết luận|cho thấy|đạt|không đạt|xác lập|"
                 r"chứng minh|vững)|(kết luận|cho thấy|xác lập)[^.\n]{0,200}(không kém hơn|tương đương)")
_CHUYEN_VUOT_TROI = (r"(chuyển|đổi) sang[^.\n]{0,60}vượt trội|vượt trội[^.\n]{0,120}(định trước|tiền định|khai trước|"
                     r"thứ bậc|kiểm định tuần tự)")
_GHI_DE.update({
    ("CONSORT Cluster 2012", "1b"): _g(("tom_tat",), "Tóm tắt nêu thiết kế cụm và số cụm được phân bổ ở mỗi nhóm.",
                                       (_y("thiết kế cụm", r"theo cụm|cluster"),
                                        _y("số cụm", SO_CUM, so_lieu=True))),
    ("CONSORT Cluster 2012", "13a"): _g(("ket_qua",), "Với mỗi nhóm: số cụm được phân bổ, nhận can thiệp, đưa vào "
                                                       "phân tích kết cục chính, và số người tương ứng.",
                                        (_y("số cụm theo nhóm", _SO_CUM_NHOM, so_lieu=True),
                                         _y("số người theo nhóm", SO_NGUOI, so_lieu=True))),
    ("CONSORT Cluster 2012", "13b"): _g(("ket_qua",), "Với mỗi nhóm: mất và loại ở mức cụm và mức cá nhân, kèm lý do.",
                                        (_y("mất/loại mức cụm", _MAT_CUM), _y("mất/loại mức cá nhân", _MAT_NGUOI))),
    ("CONSORT Cluster 2012", "15"): _g(("ket_qua",), "Đặc điểm nền theo nhóm ở mức cá nhân và (khi có) mức cụm.",
                                       (_y("đặc điểm nền mức cá nhân", _NEN_NGUOI),
                                        _y("đặc điểm nền mức cụm", _NEN_CUM))),
    ("CONSORT Cluster 2012", "16"): _g(("ket_qua",), "Với mỗi nhóm: số cụm đưa vào từng phân tích.",
                                       (_y("số cụm phân tích", _SO_CUM_PT, so_lieu=True),)),
    ("CONSORT Cluster 2012", "17a"): _g(("ket_qua",), "Kết quả ở mức cá nhân hoặc cụm và hệ số tương quan nội cụm "
                                                       "(ICC) ước tính cho mỗi kết cục chính.",
                                        (_y("ICC ước tính", _ICC_SO, so_lieu=True),)),
    ("CONSORT NI 2012", "1b"): _g(("tom_tat",), "Tóm tắt nêu khung không kém hơn/tương đương và biên.",
                                  (_y("khung không kém hơn", TC.KHONG_KEM), _y("biên", r"biên|Δ|margin"))),
    ("CONSORT NI 2012", "22"): _g(("ban_luan", "ket_luan"),
                                  "Diễn giải theo giả thuyết không kém hơn/tương đương; biện minh nếu chuyển sang kết "
                                  "luận vượt trội.",
                                  (_y("diễn giải theo giả thuyết", _DIEN_GIAI_NI),
                                   _y("biện minh chuyển sang vượt trội", _CHUYEN_VUOT_TROI,
                                      khi=r"kết luận[^.\n]{0,80}vượt trội|vượt trội có ý nghĩa"))),
})

# ═════════════════════════════════ CONSORT 2025 (bản thảo RCT) ═════════════════════════════════
#: mã → (chương, tiêu chí, yếu tố, [áp dụng khi, lý do, cùng đoạn])
_CONSORT: Dict[str, tuple] = {
    "1a": (("tieu_de",), "Tiêu đề nêu đây là thử nghiệm ngẫu nhiên.",
           (_y("thử nghiệm ngẫu nhiên trong tiêu đề", r"ngẫu nhiên|randomi[sz]ed"),)),
    "1b": (("tom_tat",), "Tóm tắt có cấu trúc về thiết kế, phương pháp, kết quả và kết luận.",
           (_y("phần phương pháp", NHAN_PP, nhan=True), _y("phần kết quả", NHAN_KQ, nhan=True),
            _y("phần kết luận", NHAN_KL, nhan=True), _y("số liệu kết quả", SO_KQ, so_lieu=True))),
    "2": (("phuong_phap", "cuoi", "tom_tat"), "Nêu cơ quan đăng ký, mã số (kèm đường dẫn) và ngày đăng ký.",
          (_y("cơ quan đăng ký", TC.DANG_KY + r"|ISRCTN|ANZCTR|ChiCTR|CTRI|Thai Clinical Trials"),
           _y("mã số đăng ký", MA_DK), _y("ngày đăng ký", NGAY_DK))),
    "3": (("phuong_phap", "cuoi"), "Nêu nơi truy cập đề cương và kế hoạch phân tích thống kê.",
          (_y("truy cập đề cương", r"(đề cương|protocol)[^.]{0,160}(truy cập|công bố|đăng tải|cung cấp|tài liệu bổ "
                                   r"sung|phụ lục|theo yêu cầu|available|lưu (trữ|tại))"),
           _y("truy cập kế hoạch phân tích", r"(kế hoạch phân tích|\bSAP\b|statistical analysis plan)[^.]{0,160}"
                                             r"(truy cập|công bố|đăng tải|cung cấp|tài liệu bổ sung|phụ lục|theo yêu "
                                             r"cầu|available|lưu (trữ|tại))"))),
    "4": (("cuoi", "phuong_phap"), "Nêu nơi và cách truy cập dữ liệu cá nhân đã khử định danh (kèm từ điển dữ liệu), "
                                   "mã thống kê và tài liệu khác.",
          # 22/11/2026: «dữ liệu cá thể» = individual participant data (đã nhận bản tiếng Anh) — tuyên bố tác giả
          # của giả lập «Dữ liệu cá thể không chia sẻ công khai…» từng bị báo thiếu yếu tố này. Không vắt qua dòng: nhãn
          # «**Tính có sẵn dữ liệu:**» + chữ đầu dòng sau từng làm dòng NHÃN thành bằng chứng
          (_y("dữ liệu cá nhân đã khử định danh", r"dữ liệu[^.\n]{0,60}(khử định danh|giả danh|cá nhân|cá thể|gốc)|"
                                                  r"bộ dữ liệu|(không|chưa) chia sẻ dữ liệu|"
                                                  r"individual (participant )?data", so_lieu=True),
           _y("mã thống kê/từ điển dữ liệu", r"mã (phân tích|lệnh|thống kê|nguồn)|script|code|từ điển dữ liệu|"
                                             r"data dictionary|(không|chưa) chia sẻ", so_lieu=True),
           _y("cách truy cập", r"theo yêu cầu|kho (lưu trữ|dữ liệu)|repository|truy cập|cung cấp|on request",
              so_lieu=True))),
    "5a": (("cuoi", "phuong_phap"), "Nêu nguồn kinh phí, hỗ trợ khác (vd thuốc) và vai trò nhà tài trợ trong thiết kế, "
                                    "thực hiện, phân tích, báo cáo.",
           (_y("nguồn kinh phí/hỗ trợ", NGUON_KINH_PHI_BT), _y("vai trò nhà tài trợ", VAI_TRO_TAI_TRO_BT)), None, "",
           True),
    "5b": (("cuoi",), "Khai xung đột lợi ích tài chính và khác của các tác giả.",
           (_y("xung đột lợi ích", TC.XUNG_DOT + r"|competing interests?|conflicts? of interest"),)),
    "6": (("gioi_thieu",), "Nêu cơ sở khoa học và lý do thực hiện thử nghiệm.",
          (_y("trích dẫn nguồn", TC.TRICH_DAN),
           _y("lý do/khoảng trống", r"khoảng trống|chưa (có|thấy|được|tìm thấy|rõ|biết)|còn (ít|hạn chế|thiếu)|"
                                    + _THIEU_KT + r"|cần (thiết|có)|uncertain"))),
    "7": (("gioi_thieu", "tom_tat"), "Nêu mục tiêu cụ thể về cả lợi ích và tác hại.",
          (_y("mục tiêu cụ thể", r"(nhằm|mục tiêu)[^.]{0,60}(đánh giá|so sánh|xác định|ước lượng|kiểm định)|"
                                 r"\bObjectives?\b"),
           _y("mục tiêu về tác hại/an toàn", r"an toàn|tác hại|biến cố|bất lợi|tác dụng (phụ|không mong muốn)|"
                                             r"harms?|safety"))),
    "8": (("phuong_phap", "cuoi"), "Nêu chi tiết sự tham gia của người bệnh/công chúng vào thiết kế, thực hiện, báo cáo"
                                   " (hoặc nêu không có).",
          (_y("sự tham gia của người bệnh/công chúng", TC.PPI + r"|patient and public involvement"),)),
    "9": (("phuong_phap",), "Nêu loại thử nghiệm, tỷ lệ phân bổ và khung so sánh.",
          (_y("loại thử nghiệm", r"song song|bắt chéo|giai thừa|theo cụm|nhánh|parallel|crossover|cluster"),
           _y("tỷ lệ phân bổ", r"\b\d\s*:\s*\d\b|tỷ lệ (phân bổ|phân nhóm)|allocation ratio"),
           _y("khung so sánh", r"vượt trội|không kém|tương đương|thăm dò|superiority|non-inferiority|equivalence|"
                               r"exploratory"))),
    "10": (("phuong_phap", "ket_qua"), "Nêu thay đổi quan trọng sau khi bắt đầu thử nghiệm (kết cục/phân tích ngoài "
                                       "đề cương) kèm lý do — hoặc nêu không có.",
           (_y("thay đổi so với đề cương", r"(thay đổi|sửa đổi|điều chỉnh)[^.]{0,100}(đề cương|so với đề cương|sau khi"
                                           r" (bắt đầu|tiến hành))|không có (thay đổi|sửa đổi)[^.]{0,80}(đề cương|kết"
                                           r" cục|phân tích)|(đề cương|protocol)[^.]{0,80}không (thay đổi|sửa đổi)|"
                                           r"changes? to (the )?(trial )?protocol"),)),
    "11": (("phuong_phap",), "Nêu bối cảnh và địa điểm thực hiện.", (_y("nơi thực hiện", K.NOI),)),
    "12a": (("phuong_phap",), "Nêu tiêu chuẩn chọn người tham gia (chọn và loại).",
            (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON_BT), _y("tiêu chuẩn loại", TIEU_CHUAN_LOAI_BT))),
    "12b": (("phuong_phap",), "Nêu tiêu chuẩn chọn cơ sở và người thực hiện can thiệp.",
            (_y("tiêu chuẩn cơ sở/người thực hiện", r"tiêu chuẩn.{0,80}(cơ sở|người thực hiện|điều dưỡng|phẫu thuật "
                                                   r"viên|bác sĩ thực hiện)"),),
            r"phẫu thuật viên|người thực hiện can thiệp|đa trung tâm|nhiều (cơ sở|trung tâm)",
            "can thiệp do người có kỹ năng riêng thực hiện hoặc đa cơ sở"),
    "13": (("phuong_phap",), "Mô tả can thiệp và nhóm chứng đủ để lặp lại.",
           (_y("nhóm can thiệp", r"nhóm can thiệp|nhánh can thiệp|intervention (group|arm)"),
            _y("nhóm chứng", r"nhóm (đối )?chứng|nhánh chứng|control (group|arm)|comparator"),
            _y("liều/tần suất/thời gian", r"mỗi (ngày|tuần|tháng)|\d+\s*(lần|tin nhắn|buổi)\s*/|trong \d+ (ngày|tuần|"
                                          r"tháng)|hằng (ngày|tuần)|liều"))),
    "14": (("phuong_phap",), "Nêu kết cục chính và phụ định trước: biến đo, thước đo, cách tổng hợp, thời điểm.",
           (_y("kết cục chính", r"kết cục chính|primary outcome"), _y("kết cục phụ", r"kết cục phụ|secondary outcome"),
            _y("thời điểm đánh giá", r"(tại|sau|ở) (tháng|tuần|ngày|thời điểm)|tháng thứ \d+|at \d+ (weeks|months)"))),
    "15": (("phuong_phap",), "Nêu cách định nghĩa và đánh giá tác hại.",
           (_y("tác hại/biến cố bất lợi", r"biến cố (bất lợi|không mong muốn)|tác dụng (phụ|không mong muốn)|tác hại|"
                                          r"adverse events?|harms?"),
            _y("cách đánh giá/ghi nhận", r"ghi nhận|đánh giá|theo dõi|thu thập|báo cáo|hệ thống|assess")), None, "",
           True),
    "16a": (("phuong_phap",), "Nêu cách xác định cỡ mẫu và mọi giả định.",
            (_y("công thức/phương pháp", TC.CONG_THUC_CO_MAU),
             _y("tham số có nguồn", TC.THAM_SO_NGUON + r"|PMID\s*:?\s*\d{6,9}|doi\s*:?\s*10\."),
             _y("cỡ mẫu cuối cùng", TC.CO_MAU_CUOI))),
    "16b": (("phuong_phap",), "Giải thích phân tích giữa kỳ và quy tắc dừng (hoặc nêu không có).",
            (_y("giữa kỳ/quy tắc dừng", r"phân tích giữa kỳ|quy tắc dừng|dừng sớm|interim|stopping"),)),
    "17a": (("phuong_phap",), "Nêu ai tạo trình tự ngẫu nhiên và bằng phương pháp nào.",
            (_y("phương pháp tạo trình tự", r"(tạo|sinh) (trình tự|danh sách|chuỗi)|phần mềm|máy tính|bảng số ngẫu "
                                            r"nhiên|computer"),
             _y("người tạo", r"thống kê viên|người (độc lập|không tham gia)|độc lập|independent"))),
    "17b": (("phuong_phap",), "Nêu kiểu ngẫu nhiên hoá và giới hạn (phân tầng, khối, cỡ khối).",
            (_y("kiểu ngẫu nhiên hoá", r"khối|ngẫu nhiên (đơn|giản đơn)|phân tầng|không phân tầng|tối thiểu hoá|"
                                       r"block|stratif|minimi[sz]"),)),
    "18": (("phuong_phap",), "Nêu cơ chế thực hiện trình tự phân bổ và cách giấu đến khi phân bổ.",
           (_y("giấu phân bổ", r"giấu (phân bổ|trình tự)|phong bì|phân bổ trung tâm|qua (điện thoại|hệ thống)|"
                               r"concealment|sealed"),)),
    "19": (("phuong_phap",), "Nêu người tuyển và người phân bổ có tiếp cận trình tự hay không.",
           (_y("kiểm soát tiếp cận trình tự", r"(tiếp cận|biết|giữ) (trình tự|danh sách)|người tuyển.{0,120}"
                                              r"(không|chỉ)|độc lập (sinh|giữ)|access to the (allocation|random)|"
                                              r"người không tham gia (tuyển|phân bổ)[^.]{0,40}giữ"),)),
    "20a": (("phuong_phap",), "Nêu ai được làm mù sau phân bổ (hoặc nêu nhãn mở).",
            (_y("làm mù", r"làm mù|che giấu|mù (đơn|đôi)|nhãn mở|blind|open[- ]label|mask"),
             _y("đối tượng làm mù", r"người (tham gia|đo|đánh giá)|thống kê viên|người phân tích|bác sĩ|participants|"
                                    r"assessors?|analysts?"))),
    "20b": (("phuong_phap",), "Nếu làm mù: nêu cách làm mù và độ tương tự của can thiệp.",
            (_y("cách làm mù", r"(giống|tương tự) nhau|giả dược|cách làm mù|che (nhãn|mã)|tách (biệt|riêng) (vai trò|"
                               r"người)|placebo|identical|similar"),), TC.LAM_MU, "có làm mù"),
    # 22/11/2026 (thử nghiệm không kém hơn giả lập): SAP §4 «Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với
    # biên Δ» là phương pháp so sánh nhóm nhưng không khớp TC.PP_THONG_KE ⇒ THIẾU GIẢ. Chỉ thêm TÊN phương pháp: «CI»
    # trơn có ở câu cố định «mọi ước lượng kèm 95%CI» của MỌI bản thảo; «hiệu số tỷ lệ» có ở dòng thiết kế «biên hiệu
    # số tỷ lệ −10 điểm %» (mô tả biên, không phải phương pháp) — cả hai sẽ thành bằng chứng giả.
    "21a": (("phuong_phap",), "Nêu phương pháp thống kê so sánh các nhóm cho kết cục chính, phụ và tác hại.",
            (_y("phương pháp thống kê", TC.PP_THONG_KE + r"|risk difference|Newcombe"),
             _y("kết cục chính", r"kết cục chính|phân tích chính|primary"))),
    "21b": (("phuong_phap",), "Định nghĩa ai được đưa vào từng phân tích và ở nhóm nào.",
            (_y("quần thể phân tích", r"ý định điều trị|\bITT\b|theo đề cương|per[- ]protocol|(mọi|tất cả) (người|đối "
                                      r"tượng) (được )?(ngẫu nhiên|phân bổ)|intention[- ]to[- ]treat"),)),
    "21c": (("phuong_phap",), "Nêu cách xử lý dữ liệu thiếu trong phân tích.",
            (_y("dữ liệu thiếu", TC.DU_LIEU_THIEU), _y("phương pháp xử lý", TC.XU_LY_THIEU)), None, "", True),
    "21d": (("phuong_phap",), "Nêu phân tích bổ sung (nhóm nhỏ, độ nhạy), phân biệt định trước với hậu kiểm.",
            (_y("phân tích bổ sung", r"phân tích (độ nhạy|phân nhóm|nhóm nhỏ)|sensitivity|subgroup"),
             _y("định trước/hậu kiểm", r"định trước|tiền định|khai trước|post[- ]hoc|hậu kiểm|sau khi xem dữ liệu|"
                                       r"pre-?specified"))),
    "22a": (("ket_qua",), "Theo từng nhóm: số được phân bổ ngẫu nhiên, nhận can thiệp dự định, được phân tích kết cục "
                          "chính.",
            (_y("số được phân bổ ngẫu nhiên", SO_NGUOI + r"[^.;]{0,60}(phân bổ|chia|được) ngẫu nhiên|"
                                              r"(phân bổ|chia) ngẫu nhiên[^.;]{0,40}" + SO_NGUOI + "|"
                                              r"\d+ (participants|patients)[^.;]{0,40}randomi[sz]ed"),
             _y("số nhận can thiệp", r"nhận (can thiệp|đủ|đúng|nhánh)|được (can thiệp|điều trị)|received"),
             _y("số được phân tích kết cục chính", SO_NGUOI + r"[^.;]{0,80}(được )?phân tích|"
                                                   r"phân tích[^.;\n]{0,30}:\s*[Nn]\s*=\s*\d|"
                                                   r"\d+ (participants|patients)[^.;]{0,60}analy[sz]ed"),
             _y("theo từng nhóm", r"nhóm (can thiệp|chứng|đối chứng)|mỗi nhóm|từng nhóm|hai nhóm|each group"))),
    # một yếu tố: mất/loại KÈM lý do, HOẶC câu «không có người mất theo dõi» (không có ai thì không có lý do —
    # phiên «G7 đọc sổ sàng lọc» báo thiếu giả 22/11/2026)
    "22b": (("ket_qua",), "Theo từng nhóm: số mất/loại sau phân bổ kèm lý do (hoặc nêu không có ai).",
            (_y("mất/loại sau phân bổ kèm lý do, hoặc nêu không có",
                r"(mất theo dõi|bỏ cuộc|rút khỏi|bị loại|ngừng|lost to follow|withdr)[^.]{0,120}(lý do|vì|do |"
                r"reason)|(lý do|vì|do )[^.]{0,120}(mất theo dõi|bỏ cuộc|rút khỏi|bị loại)|"
                r"không (có|ghi nhận) (người |ai |trường hợp )?(nào )?(mất theo dõi|bỏ cuộc|rút khỏi|bị loại|mất|bỏ)|"
                r"no (participants? )?(were )?(lost|withdr)"),)),
    "23a": (("ket_qua",), "Nêu các mốc ngày tuyển và theo dõi kết cục lợi ích và tác hại.",
            (_y("mốc ngày", K.NGAY), _y("tuyển/theo dõi", r"tuyển|theo dõi|recruit|follow"))),
    "23b": (("ket_qua", "ban_luan"), "Nêu lý do thử nghiệm kết thúc hoặc dừng.",
            (_y("lý do dừng/kết thúc", r"(dừng|kết thúc|ngừng)[^.]{0,80}(vì|do|lý do)|stopped (early )?because"),),
            r"dừng sớm|kết thúc sớm|ngừng (thử nghiệm|tuyển) sớm|stopped early", "thử nghiệm dừng sớm"),
    "24a": (("ket_qua",), "Mô tả can thiệp và nhóm chứng như thực tế đã thực hiện (người thực hiện, tuân thủ, đúng kế "
                          "hoạch).",
            (_y("thực hiện thực tế/tuân thủ", r"tuân thủ|thực tế (nhận|được)|đúng (kế hoạch|đề cương)|nhận đủ|"
                                              r"fidelity|adhere"),)),
    # 22/11/2026 (giả lập đầu–cuối RCT): «chăm sóc thường quy» là TÊN NHÓM CHỨNG — «`0` = Chăm sóc thường quy» (mã
    # nhóm trong dữ liệu khoá), «nhóm chăm sóc thường quy: 118», «so với chăm sóc thường quy» — từng làm 24b ĐẠT GIẢ.
    # Chỉ nhận cụm này khi câu nói mỗi nhóm NHẬN nó («cả hai nhóm tiếp tục chăm sóc thường quy»).
    "24b": (("ket_qua",), "Nêu chăm sóc đồng thời mỗi nhóm nhận được.",
            (_y("chăm sóc đồng thời", r"chăm sóc (đồng thời|đi kèm)|(nhận|tiếp tục|duy trì|vẫn được|đều được|cùng "
                                      r"được)[^.;\n]{0,40}chăm sóc thường quy|điều trị (đi kèm|phối hợp|đồng thời|nền)|"
                                      r"thuốc (dùng )?(kèm|phối hợp)|concomitant"),)),
    "25": (("ket_qua",), "Có bảng đặc điểm nền nhân khẩu và lâm sàng theo từng nhóm.",
           (_y("bảng đặc điểm nền", r"(Bảng|Table)\s*\d+[.:]?[^\n]{0,20}(Đặc điểm|baseline|characteristics)|"
                                    r"Đặc điểm (nền|ban đầu|chung)", de_muc=True),
            _y("theo nhóm", r"nhóm (can thiệp|chứng|đối chứng)|mỗi nhóm|từng nhóm|by group|each group"))),
    "26": (("ket_qua",), "Mỗi kết cục chính và phụ theo nhóm: số phân tích, số có dữ liệu, kết quả từng nhóm, hiệu ứng "
                         "kèm độ chính xác; kết cục nhị phân trình bày cả hiệu ứng tuyệt đối và tương đối.",
           (_y("số được phân tích theo nhóm", r"\bn\s*=\s*\d|\d+\s*/\s*\d+|\d+ người"),
            _y("ước lượng hiệu ứng kèm KTC", r"KTC|khoảng tin cậy|\bCI\b"),
            _y("hiệu ứng tuyệt đối (kết cục nhị phân)", NGUY_CO_TUYET_DOI + r"|\bRD\b",
               khi=r"kết cục (chính|phụ)[^.\n]{0,120}(tỷ lệ|nhị phân)|binary"),
            _y("hiệu ứng tương đối (kết cục nhị phân)", DO_LUONG_TUONG_DOI,
               khi=r"kết cục (chính|phụ)[^.\n]{0,120}(tỷ lệ|nhị phân)|binary"))),
    "27": (("ket_qua",), "Báo cáo mọi tác hại hoặc biến cố ngoài ý muốn ở mỗi nhóm.",
           (_y("tác hại theo nhóm", r"(biến cố (bất lợi|không mong muốn)|tác dụng (phụ|không mong muốn)|tác hại|"
                                    r"adverse events?|harms?)"),)),
    "28": (("ket_qua",), "Báo cáo các phân tích khác (nhóm nhỏ, độ nhạy), phân biệt định trước với hậu kiểm.",
           (_y("kết quả phân tích khác", PHAN_TICH_KHAC),
            _y("định trước/hậu kiểm", r"định trước|tiền định|khai trước|post[- ]hoc|hậu kiểm|pre-?specified")),
           PHAN_TICH_KHAC, "có phân tích nhóm nhỏ/độ nhạy"),
    "29": (("ban_luan",), "Diễn giải nhất quán với kết quả, cân đối lợi ích và tác hại, xét bằng chứng liên quan.",
           (_y("cân đối lợi ích và tác hại", r"(lợi ích|hiệu quả)[^.]{0,200}(tác hại|an toàn|biến cố|bất lợi)|"
                                             r"(tác hại|an toàn|biến cố|bất lợi)[^.]{0,200}(lợi ích|hiệu quả)|"
                                             r"benefits?[^.]{0,120}harms?"),
            _y("đối chiếu bằng chứng khác (có trích dẫn)", SO_SANH_Y_VAN))),
    "30": (("ban_luan",), "Bàn hạn chế: nguồn sai lệch, thiếu chính xác, suy rộng và (khi có) đa so sánh.",
           (_y("sai lệch", r"sai lệch|sai số|thiên lệch|bias"),
            _y("thiếu chính xác", r"(thiếu )?chính xác|cỡ mẫu (nhỏ|hạn chế|không đủ)|khoảng tin cậy rộng|lực (thống kê"
                                  r"|mẫu)|imprecis|power"),
            _y("suy rộng", TC.SUY_RONG + r"|một (cơ sở|trung tâm|bệnh viện)|đơn trung tâm|generali[sz]ab"),
            _y("đa so sánh", r"đa (so sánh|kiểm định)|nhiều (so sánh|kiểm định|phép kiểm)|multiplicity|Bonferroni",
               khi=r"phân tích (phân nhóm|nhóm nhỏ)|nhiều kết cục phụ|subgroup"))),
}


def _muc_consort() -> List[MucKiem]:
    van = {ma: (phan, chu_de, nv) for ma, phan, chu_de, nv in CBC.CONSORT_2025_ITEMS}
    assert set(van) == set(_CONSORT), "mã CONSORT 2025 lệch giữa kho nguyên văn và bảng tiêu chí"
    ra = []
    for ma, tc in _CONSORT.items():
        phan, tieu_chi, yeu_to = tc[:3]
        khi, ly_do = (tc[3], tc[4]) if len(tc) > 4 else (None, "")
        cung = bool(tc[5]) if len(tc) > 5 else False
        ra.append(MucKiem("CONSORT 2025", ma, van[ma][1], van[ma][2], tieu_chi, tuple(phan),
                          tuple(replace(y, khi=_pham_vi(y.khi, phan)) for y in yeu_to), "bat_buoc",
                          _pham_vi(khi, phan), ly_do, cung))
    return ra


# ═════════════════════════════════ PRISMA 2020 (bản thảo tổng quan hệ thống/phân tích gộp) ════════════════════════════
# 22/11/2026. Nguyên văn: Page MJ et al. PLoS Med 2021;18(3):e1003583 (PMID 33780438; PMC8007028; CC BY 4.0) — cùng nội
# dung BMJ 2021;372:n71 (PMID 33782057). Mục 2 («See the PRISMA 2020 for Abstracts checklist») chấm theo 12 mục của
# PRISMA 2020 for Abstracts (Table 2). Chữ «ideally»/«where appropriate» của chuẩn: sơ đồ luồng (16a) không là yếu tố
# bắt buộc; thống kê tóm tắt từng nhóm (19) chỉ đòi khi kết cục nhị phân/liên tục có số đo theo nhánh.
#: cơ sở dữ liệu thư mục — sổ đăng ký thử nghiệm (ClinicalTrials.gov, ICTRP) KHÔNG thay được (22/11/2026: «search
#: unpublished (clinicaltrials.gov)» trong bảng sai lệch của bản thảo giả lập từng làm mục 6 đạt khi không nêu CSDL nào)
CSDL_TQ = r"PubMed|MEDLINE|Embase|Cochrane|CENTRAL|Scopus|Web of Science|CINAHL|PsycINFO|LILACS|Europe PMC"
#: ngày tìm cuối gần chữ tìm/tra cứu — K.NGAY nhận cả «30/06/2027», «tháng 6 năm 2027» và ngày ISO «2027-06-30» của G1
#: `search_last_date` (khớp mẫu «năm–tháng»)
NGAY_TIM = (r"(tìm|tra cứu|search(ed)?)[^.\n|]{0,160}(" + K.NGAY + r")|(" + K.NGAY
            + r")[^.\n|]{0,60}(tìm|tra cứu|search)")
SO_NGUOI_TQ = r"\b(hai|ba|2|3)\s*(người|nghiên cứu viên|thành viên|tác giả|reviewers?|screeners?|người sàng lọc)"
DOC_LAP_TQ = r"độc lập|independent"
THUOC_DO_HIEU_UNG = (r"\b(RR|OR|HR|MD|SMD|RD|WMD)\b|tỷ số (nguy cơ|chênh|rủi ro|nguy hại)|hiệu số (trung bình|nguy cơ)|"
                     r"nguy cơ tương đối|risk ratio|odds ratio|mean difference|hazard ratio")
NGUY_CO_SL_TQ = r"RoB ?2|ROBINS|Newcastle|QUADAS|AMSTAR|\bJBI\b|nguy cơ sai lệch|risk of bias"
SAI_LECH_BAO_CAO_TQ = (r"sai lệch (công bố|xuất bản|báo cáo)|biểu đồ phễu|funnel|Egger|Begg|trim[- ]and[- ]fill|"
                       r"publication bias|reporting bias|hiệu ứng nghiên cứu nhỏ|small[- ]study")
CHAC_CHAN_TQ = (r"\bGRADE\b|mức (độ )?chắc chắn|độ (tin cậy|chắc chắn) (của )?(bằng chứng|chứng cứ)|certainty|"
                r"chất lượng (bằng chứng|chứng cứ)")
PHAN_NHOM_TQ = (r"phân nhóm|nhóm nhỏ|hồi quy gộp|meta-?regression|subgroup|khác biệt giữa (các )?(phân )?nhóm|"
                r"Q giữa nhóm")
DO_NHAY_TQ = r"phân tích (độ nhạy|nhạy cảm)|độ nhạy|sensitivity|bỏ từng nghiên cứu|leave[- ]one[- ]out"
TRICH_DAN_NC = r"\[\d+(?:[,–-]\s*\d+)*\]|\bet al\b|\bPMID\b|\(\w[^()\n]{0,30}(19|20)\d{2}\)"

#: mã → (chương, tiêu chí, yếu tố, [áp dụng khi, lý do, cùng đoạn]) — cùng khuôn `_CONSORT`
_PRISMA_2020: Dict[str, tuple] = {
    "1": (("tieu_de",), "Tiêu đề nêu đây là tổng quan hệ thống.",
          (_y("«tổng quan hệ thống» trong tiêu đề", r"tổng quan (hệ thống|có hệ thống)|systematic review"),)),
    "2": (("tom_tat",), "Tóm tắt theo PRISMA 2020 for Abstracts: mục tiêu, tiêu chí chọn, nguồn tìm kèm ngày tìm cuối, "
                        "đánh giá nguy cơ sai lệch, phương pháp tổng hợp, số nghiên cứu và người tham gia, kết quả "
                        "chính kèm KTC, hạn chế của bằng chứng, diễn giải, tài trợ, cơ quan và số đăng ký.",
          (_y("mục tiêu (A2)", r"mục tiêu|nhằm|\bObjectives?\b|\baims?\b"),
           _y("tiêu chí chọn (A3)", TIEU_CHUAN_CHON_BT + r"|tiêu chí (nhận|loại)|eligib"),
           _y("nguồn thông tin (A4)", CSDL_TQ),
           _y("ngày tìm cuối (A4)", NGAY_TIM),
           _y("đánh giá nguy cơ sai lệch (A5)", NGUY_CO_SL_TQ),
           _y("phương pháp tổng hợp (A6)", r"hiệu ứng (ngẫu nhiên|cố định)|mô hình (ngẫu nhiên|cố định)|"
                                           r"random[- ]effects?|fixed[- ]effects?|DerSimonian|\bREML\b|Mantel|"
                                           r"Hartung|tổng hợp (mô tả|tường thuật|không định lượng)|\bSWiM\b"),
           _y("số nghiên cứu và người tham gia (A7)", r"\d+\s*(nghiên cứu|thử nghiệm|studies|trials)[^.\n]{0,120}"
                                                      r"\d[\d.,]*\s*(người|bệnh nhân|participants|patients)",
              so_lieu=True),
           _y("kết quả chính kèm KTC (A8)", KTC_BT, so_lieu=True),
           _y("hạn chế của bằng chứng (A9)", r"hạn chế|limitations?"),
           _y("diễn giải (A10)", NHAN_KL, nhan=True),
           _y("tài trợ (A11)", NGUON_KINH_PHI_BT),
           _y("cơ quan và số đăng ký (A12)", r"(PROSPERO|INPLASY|\bOSF\b)[^.\n]{0,60}(CRD\d{6,}|INPLASY\d+|osf\.io)|"
                                             r"(CRD\d{6,}|INPLASY\d+)[^.\n]{0,40}(PROSPERO|INPLASY)"))),
    "3": (("gioi_thieu",), "Nêu lý do thực hiện tổng quan trong bối cảnh hiểu biết hiện có.",
          (_y("trích dẫn nguồn", TC.TRICH_DAN),
           _y("lý do/khoảng trống", r"khoảng trống|chưa (có|thấy|được|tìm thấy|rõ|biết)|còn (ít|hạn chế|thiếu)|"
                                    + _THIEU_KT + r"|cần (thiết|có)|cập nhật|uncertain|gap"))),
    "4": (("gioi_thieu", "tom_tat"), "Nêu rõ mục tiêu hoặc câu hỏi của tổng quan (quần thể, can thiệp/phơi nhiễm, kết "
                                     "cục).",
          (_y("mục tiêu/câu hỏi", r"(nhằm|mục tiêu)[^.\n]{0,60}(ước lượng|đánh giá|so sánh|xác định|tổng hợp|tìm hiểu|"
                                  r"mô tả|kiểm định)|\bObjectives?\b|câu hỏi (nghiên cứu|của tổng quan)|"
                                  r"research question"),
           _y("quần thể", r"ở người|người (bệnh|trưởng thành|tham gia|cao tuổi)|bệnh nhân|quần thể|trẻ em|phụ nữ|"
                          r"population|participants|patients"),
           _y("can thiệp/phơi nhiễm", r"can thiệp|phơi nhiễm|điều trị|thuốc|liệu pháp|intervention|exposure|"
                                      r"treatment"),
           _y("kết cục", r"kết cục|outcome|tử vong|nhập viện|biến cố|tỷ lệ|nguy cơ|hiệu quả"))),
    "5": (("phuong_phap",), "Nêu tiêu chí chọn và loại của tổng quan (kể cả đặc điểm báo cáo: ngôn ngữ, năm, tình "
                            "trạng công bố) và cách nhóm nghiên cứu cho các tổng hợp.",
          (_y("tiêu chí chọn", TIEU_CHUAN_CHON_BT + r"|tiêu chí nhận"),
           _y("tiêu chí loại", TIEU_CHUAN_LOAI_BT),
           _y("đặc điểm báo cáo (ngôn ngữ/năm/tình trạng công bố)",
              r"ngôn ngữ|năm (xuất bản|công bố)|tình trạng (xuất bản|công bố)|chưa công bố|tiếng Anh|"
              r"không giới hạn (ngôn ngữ|năm|thời gian)|language|publication status|unpublished"),
           _y("cách nhóm nghiên cứu cho tổng hợp", r"nhóm (các )?(nghiên cứu|thử nghiệm)|nhóm nhỏ|phân nhóm|"
                                                   r"gộp (theo|riêng)|tổng hợp (theo|riêng)|grouped|"
                                                   r"nhóm theo (thuốc|can thiệp|kết cục|thiết kế|liều)"))),
    "6": (("phuong_phap",), "Nêu mọi cơ sở dữ liệu, sổ đăng ký, trang web, tổ chức, danh mục tham khảo và nguồn khác "
                            "đã tìm, kèm ngày tìm/tra cứu cuối của từng nguồn.",
          (_y("cơ sở dữ liệu/sổ đăng ký đã tìm", CSDL_TQ), _y("ngày tìm cuối", NGAY_TIM))),
    "7": (("phuong_phap", "phu_luc"), "Trình bày đầy đủ chiến lược tìm cho mọi cơ sở dữ liệu, sổ đăng ký và trang web "
                                      "(câu lệnh, hoặc dẫn phụ lục chứa câu lệnh), kể cả bộ lọc và giới hạn.",
          (_y("chiến lược tìm đầy đủ (câu lệnh hoặc dẫn phụ lục)",
              r"\bAND\b|\[MeSH|\[mh\]|\[tiab\]|\[ti\]|\[pt\]|/exp\b|:ti,ab|"
              r"(chiến lược tìm|câu lệnh tìm|search strateg)[^.\n]{0,160}(phụ lục|tài liệu bổ sung|supplement|"
              r"appendix)|(phụ lục|tài liệu bổ sung|supplement|appendix)[^.\n]{0,120}(chiến lược tìm|câu lệnh tìm|"
              r"search strateg)"),
           _y("bộ lọc/giới hạn (hoặc nêu không giới hạn)", r"bộ lọc|giới hạn|filters?|limits?"))),
    "8": (("phuong_phap",), "Nêu cách quyết định nghiên cứu đạt tiêu chí: số người sàng lọc mỗi bản ghi và báo cáo, có "
                            "làm độc lập không, các giai đoạn (và công cụ tự động nếu dùng).",
          (_y("số người sàng lọc", SO_NGUOI_TQ), _y("làm độc lập", DOC_LAP_TQ),
           _y("giai đoạn sàng lọc", r"tiêu đề|tóm tắt|toàn văn|titles?|abstracts?|full[- ]?texts?")), None, "", True),
    "9": (("phuong_phap",), "Nêu cách trích dữ liệu: số người trích mỗi báo cáo, có độc lập không, cách xin/xác nhận "
                            "dữ liệu từ tác giả nghiên cứu.",
          (_y("số người trích/độc lập", r"(hai|ba|2|3)\s*(người|nghiên cứu viên|thành viên)[^.\n|]{0,40}"
                                        r"(trích|extract)|(trích|extract)[^.\n|]{0,60}(độc lập|independent)"),
           _y("xin/xác nhận dữ liệu từ tác giả", r"liên hệ (tác giả|nhà nghiên cứu|nhà tài trợ)|xin (thêm )?dữ liệu|"
                                                 r"contact(ed)? (the )?(study )?(authors|investigators)|"
                                                 r"(không|chưa) liên hệ tác giả"))),
    "10a": (("phuong_phap",), "Liệt kê và định nghĩa mọi kết cục cần tìm dữ liệu; nêu cách chọn kết quả khi một nghiên "
                              "cứu báo cáo nhiều thời điểm/thước đo/phân tích.",
            (_y("kết cục được liệt kê", r"kết cục (chính|phụ)|primary outcome|secondary outcome"),
             _y("định nghĩa kết cục", r"định nghĩa|đo bằng|defined"),
             _y("cách chọn kết quả (thời điểm/thước đo)", r"(thời điểm|mốc)[^.\n]{0,80}(dài nhất|cuối|gần nhất|chính)|"
                                                          r"theo dõi dài nhất|chọn[^.\n]{0,60}(kết quả|thời điểm|"
                                                          r"thước đo)|ưu tiên|mọi kết quả|all results|"
                                                          r"longest follow"))),
    "10b": (("phuong_phap",), "Liệt kê và định nghĩa các biến khác cần trích (đặc điểm người tham gia, can thiệp, "
                              "nguồn tài trợ…); nêu giả định với thông tin thiếu hoặc không rõ.",
            (_y("biến khác được trích", r"(biến|dữ liệu|thông tin)[^.\n]{0,40}(trích|thu thập|extract)|"
                                        r"trích (xuất )?[^.\n]{0,80}(đặc điểm|thiết kế|cỡ mẫu|quần thể|can thiệp|"
                                        r"tài trợ|thời gian theo dõi)|data items"),
             _y("giả định khi thiếu/không rõ", r"giả định|thông tin (thiếu|không rõ)|(dữ liệu|số liệu) thiếu|"
                                               r"missing or unclear"))),
    "11": (("phuong_phap",), "Nêu phương pháp đánh giá nguy cơ sai lệch của từng nghiên cứu: công cụ, số người đánh "
                             "giá, có độc lập không.",
           (_y("công cụ đánh giá nguy cơ sai lệch", r"RoB ?2|ROBINS|Newcastle|QUADAS|AMSTAR|\bJBI\b|"
                                                    r"risk of bias tool"),
            _y("số người đánh giá", SO_NGUOI_TQ), _y("đánh giá độc lập", DOC_LAP_TQ)), None, "", True),
    "12": (("phuong_phap",), "Nêu thước đo hiệu ứng cho từng kết cục (RR, OR, MD…).",
           (_y("thước đo hiệu ứng", THUOC_DO_HIEU_UNG),)),
    "13a": (("phuong_phap",), "Nêu quy trình quyết định nghiên cứu nào đủ điều kiện cho từng tổng hợp.",
            (_y("tiêu chí đưa vào từng tổng hợp", r"(đủ điều kiện|đưa vào|chọn)[^.\n]{0,80}(từng |mỗi )?(tổng hợp|"
                                                  r"phân tích gộp)|(gộp|tổng hợp định lượng|phân tích gộp) (chỉ )?"
                                                  r"(khi|nếu)|điều kiện (để )?gộp|không gộp (khi|nếu)|"
                                                  r"eligible for (each )?synthes"),)),
    "13b": (("phuong_phap",), "Nêu cách chuẩn bị dữ liệu cho trình bày/tổng hợp (xử lý thống kê tóm tắt thiếu, chuyển "
                              "đổi dữ liệu).",
            (_y("chuẩn bị dữ liệu/xử lý thiếu", r"(dữ liệu|số liệu) thiếu|thiếu (dữ liệu|số liệu)|chuyển đổi|quy đổi|"
                                                r"ước tính (SD|độ lệch chuẩn)|missing (summary )?statistics|"
                                                r"data conversion|liên hệ tác giả"),)),
    "13c": (("phuong_phap",), "Nêu cách lập bảng hoặc biểu diễn kết quả từng nghiên cứu và các tổng hợp.",
            (_y("cách lập bảng/biểu diễn", r"biểu đồ rừng|forest[- ]?plot|bảng[^.\n]{0,12}(đặc điểm|kết quả|tóm tắt|"
                                           r"ước lượng)|lập bảng|tabulat|tóm tắt phát hiện|summary of findings|"
                                           r"harvest plot|albatross"),)),
    "13d": (("phuong_phap",), "Nêu phương pháp tổng hợp và lý do chọn; nếu gộp: mô hình, cách xác định mức không đồng "
                              "nhất, phần mềm.",
            (_y("mô hình/phương pháp tổng hợp", r"hiệu ứng (ngẫu nhiên|cố định)|random[- ]effects?|fixed[- ]effects?|"
                                                r"DerSimonian|\bREML\b|Mantel|Hartung|nghịch đảo phương sai|"
                                                r"tổng hợp (mô tả|tường thuật)|\bSWiM\b"),
             _y("đo không đồng nhất", r"I²|\bI2\b|\bτ²?|tau|không đồng nhất|heterogeneity|Cochran"),
             _y("phần mềm", r"\bR\b\s*\d|metafor|\bmeta\b \d|RevMan|Stata|Comprehensive Meta|\bCMA\b|"
                            r"phần mềm|software"))),
    "13e": (("phuong_phap",), "Nêu phương pháp khảo sát nguyên nhân không đồng nhất (phân nhóm, hồi quy gộp) — hoặc "
                              "nêu không khảo sát.",
            (_y("khảo sát không đồng nhất", PHAN_NHOM_TQ + r"|(không|chưa) (khảo sát|phân tích) (nguyên nhân )?"
                                                          r"không đồng nhất"),)),
    "13f": (("phuong_phap",), "Nêu các phân tích độ nhạy đánh giá độ vững của kết quả tổng hợp — hoặc nêu không làm.",
            (_y("phân tích độ nhạy", DO_NHAY_TQ + r"|(không|chưa) (thực hiện|làm) phân tích độ nhạy"),)),
    "14": (("phuong_phap",), "Nêu phương pháp đánh giá nguy cơ sai lệch do thiếu kết quả trong tổng hợp (sai lệch báo "
                             "cáo/công bố).",
           (_y("đánh giá sai lệch báo cáo/công bố", SAI_LECH_BAO_CAO_TQ),)),
    "15": (("phuong_phap",), "Nêu phương pháp đánh giá mức chắc chắn của tập bằng chứng cho từng kết cục (vd GRADE).",
           (_y("đánh giá mức chắc chắn", CHAC_CHAN_TQ),)),
    "16a": (("ket_qua",), "Mô tả kết quả tìm và chọn: từ số bản ghi tìm được tới số nghiên cứu đưa vào (lý tưởng kèm "
                          "sơ đồ luồng).",
            (_y("số bản ghi tìm được", r"\d[\d.,]*\s*(bản ghi|kết quả|records?|bài)[^.\n]{0,60}(tìm|xác định|"
                                       r"identified|sàng lọc)|(tìm|xác định|identified)[^.\n]{0,40}\d[\d.,]*\s*"
                                       r"(bản ghi|records?|bài)", so_lieu=True),
             _y("số nghiên cứu đưa vào", r"\d+\s*(nghiên cứu|thử nghiệm|studies|trials|báo cáo)[^.\n]{0,40}(đưa vào|"
                                         r"được chọn|included|đủ tiêu chuẩn|đủ tiêu chí)|(đưa vào|included)"
                                         r"[^.\n]{0,20}\d+\s*(nghiên cứu|thử nghiệm)", so_lieu=True))),
    "16b": (("ket_qua",), "Trích dẫn các nghiên cứu có vẻ đạt tiêu chí nhưng bị loại, kèm lý do loại.",
            (_y("nghiên cứu bị loại kèm lý do", r"(bị loại|loại trừ|excluded)[^.\n]{0,120}(vì|do|lý do|because)|"
                                                r"lý do (loại|bị loại)[^.\n]{0,40}\w|không có nghiên cứu nào bị loại"),
             _y("trích dẫn nghiên cứu bị loại", TRICH_DAN_NC + r"|không có nghiên cứu nào bị loại")), None, "", True),
    "17": (("ket_qua",), "Trích dẫn từng nghiên cứu được đưa vào và trình bày đặc điểm.",
           # «Bảng 1. Đặc điểm nền người tham gia» (khuôn nghiên cứu gốc, số trung bình gộp mọi nghiên cứu) KHÔNG là đặc
           # điểm TỪNG nghiên cứu (22/11/2026, bản thảo tổng quan giả lập)
           (_y("đặc điểm các nghiên cứu", r"(Bảng|Table)\s*\d+[.:,]?[^\n]{0,40}(Đặc điểm (của )?(các |từng )?"
                                          r"(nghiên cứu|thử nghiệm)|characteristics of (the )?(included )?(studies|"
                                          r"trials)|study characteristics)", de_muc=True),
            _y("trích dẫn từng nghiên cứu được đưa vào", TRICH_DAN_NC))),
    "18": (("ket_qua",), "Trình bày đánh giá nguy cơ sai lệch của từng nghiên cứu được đưa vào.",
           (_y("đánh giá nguy cơ sai lệch", NGUY_CO_SL_TQ),
            _y("theo từng nghiên cứu", r"(theo |của |cho )?(từng|mỗi) (nghiên cứu|thử nghiệm)|theo nghiên cứu|"
                                       r"each (included )?study|per study")), None, "", True),
    "19": (("ket_qua",), "Với mọi kết cục, trình bày cho từng nghiên cứu: thống kê tóm tắt từng nhóm (khi phù hợp) và "
                         "ước lượng hiệu ứng kèm độ chính xác (bảng hoặc biểu đồ có cấu trúc).",
           (_y("ước lượng từng nghiên cứu kèm KTC", r"forest[- ]?plot|biểu đồ rừng|"
                                                    r"^\|[^|\n]+\|\s*\d+[.,]\d+\s*\|\s*\d+[.,]\d+\s*[–-]\s*\d+[.,]\d+",
               so_lieu=True),
            # «x/n»: mẫu số ≥ 2 chữ số, không dính ngày «21/11/2026» — «Bảng 2/3» từng được nhận là số biến cố (22/11)
            _y("thống kê tóm tắt từng nhóm (số biến cố/số người mỗi nhánh)",
               r"(?<![/\d])\d{1,6}\s*/\s*\d{2,7}(?![/\d])|(biến cố|sự kiện)[^.\n|]{0,40}(nhóm|nhánh)[^.\n|]{0,20}\d|"
               r"(nhánh|nhóm) (can thiệp|chứng|đối chứng|giả dược)[^.\n|]{0,40}\d+\s*(người|biến cố)|"
               r"\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|",
               khi="@phuong_phap:" + r"\b(RR|OR|RD)\b|nhị phân|risk ratio|odds ratio|\b(MD|SMD)\b|trung bình",
               so_lieu=True))),
    "20a": (("ket_qua",), "Với từng tổng hợp, tóm tắt ngắn đặc điểm và nguy cơ sai lệch của các nghiên cứu đóng góp.",
            (_y("số nghiên cứu đóng góp", r"\bk\s*=\s*\d+|\d+\s*(nghiên cứu|thử nghiệm|studies|trials)", so_lieu=True),
             _y("đặc điểm các nghiên cứu đóng góp", r"đặc điểm|characteristics|thời gian theo dõi|cỡ mẫu|loại thuốc"),
             _y("nguy cơ sai lệch của các nghiên cứu đóng góp", NGUY_CO_SL_TQ))),
    "20b": (("ket_qua",), "Trình bày kết quả mọi tổng hợp thống kê: ước lượng gộp kèm độ chính xác (KTC) và số đo "
                          "không đồng nhất.",
            (_y("ước lượng gộp", r"(gộp|pooled|tổng hợp|summary)[^.\n]{0,60}\b(RR|OR|HR|MD|SMD|RD)\b|"
                                 r"\b(RR|OR|HR|MD|SMD|RD)\b[^.\n]{0,20}gộp", so_lieu=True),
             _y("khoảng tin cậy", KTC_BT, so_lieu=True),
             _y("số đo không đồng nhất", r"I²|\bI2\b|\bτ²?\s*[=:]|\bQ\s*=|không đồng nhất|heterogeneity",
                so_lieu=True))),
    "20c": (("ket_qua",), "Trình bày kết quả khảo sát nguyên nhân không đồng nhất (phân nhóm, hồi quy gộp).",
            (_y("kết quả phân nhóm/hồi quy gộp", PHAN_NHOM_TQ),), PHAN_NHOM_TQ,
            "có phương pháp khảo sát không đồng nhất (phân nhóm/hồi quy gộp)"),
    "20d": (("ket_qua",), "Trình bày kết quả mọi phân tích độ nhạy.",
            (_y("kết quả phân tích độ nhạy (hình/bảng hoặc số)",
                r"(Hình|Bảng|Figure|Table)\s*\d+[^\n]{0,160}(độ nhạy|nhạy cảm|sensitivity|bỏ từng|leave[- ]one[- ]out|"
                r"loại (thử nghiệm|nghiên cứu))|(độ nhạy|nhạy cảm|sensitivity|bỏ từng nghiên cứu|"
                r"loại (thử nghiệm|nghiên cứu)[^.\n]{0,40}(nguy cơ sai lệch|RoB))[^.\n]{0,160}\d+[.,]\d+",
                so_lieu=True),), DO_NHAY_TQ, "có phân tích độ nhạy"),
    "21": (("ket_qua",), "Trình bày đánh giá nguy cơ sai lệch do thiếu kết quả (sai lệch báo cáo/công bố) cho từng "
                         "tổng hợp, kèm nhận định.",
           (_y("đánh giá sai lệch báo cáo/công bố", SAI_LECH_BAO_CAO_TQ),
            _y("nhận định/kết quả kiểm định", r"Egger[^.\n]{0,80}(p\s*[=<>]|\d)|bất đối xứng|đối xứng|asymmetr|"
                                              r"(không|có|chưa) (thấy |gợi ý |có |ghi nhận )?(bằng chứng |dấu hiệu )?"
                                              r"(sai lệch công bố|sai lệch báo cáo)", so_lieu=True))),
    "22": (("ket_qua",), "Trình bày đánh giá mức chắc chắn của bằng chứng cho từng kết cục.",
           (_y("đánh giá mức chắc chắn", CHAC_CHAN_TQ),
            _y("mức chắc chắn đã xếp", r"\b(cao|trung bình|thấp|rất thấp|high|moderate|low|very low)\b", so_lieu=True)),
           None, "", True),
    "23a": (("ban_luan",), "Diễn giải chung kết quả trong bối cảnh bằng chứng khác.",
            (_y("đối chiếu bằng chứng khác (có trích dẫn)", SO_SANH_Y_VAN),)),
    "23b": (("ban_luan",), "Bàn hạn chế của bằng chứng được đưa vào (nguy cơ sai lệch, không nhất quán, thiếu chính "
                           "xác, sai lệch công bố…).",
            (_y("hạn chế", r"hạn chế|limitations?"),
             _y("hạn chế của bằng chứng", r"nguy cơ sai lệch|không đồng nhất|không nhất quán|thiếu chính xác|gián tiếp|"
                                          r"sai lệch công bố|ít (thử nghiệm|nghiên cứu)|(thử nghiệm|nghiên cứu) lớn "
                                          r"chi phối|chất lượng (bằng chứng|các nghiên cứu)|risk of bias|inconsisten|"
                                          r"imprecis|indirect")), None, "", True),
    "23c": (("ban_luan",), "Bàn hạn chế của chính quy trình tổng quan (tìm kiếm, chọn, trích, tổng hợp).",
            (_y("hạn chế", r"hạn chế|limitations?"),
             _y("hạn chế của quy trình tổng quan", r"tìm kiếm|chiến lược tìm|ngôn ngữ|sàng lọc|chọn nghiên cứu|"
                                                   r"trích (xuất )?dữ liệu|dữ liệu (tổng hợp|cấp nghiên cứu)|"
                                                   r"dữ liệu cá thể|tổng quan (này|của chúng tôi)|quy trình tổng quan|"
                                                   r"chưa (phân nhóm|đánh giá|gộp)|không (phân nhóm|đánh giá|gộp)|"
                                                   r"review process")), None, "", True),
    "23d": (("ban_luan", "ket_luan"), "Bàn hàm ý của kết quả cho thực hành, chính sách và nghiên cứu tương lai.",
            (_y("hàm ý cho thực hành/chính sách", r"thực hành|chính sách|khuyến cáo|hướng dẫn|practice|policy"),
             _y("hàm ý cho nghiên cứu tương lai", r"nghiên cứu (tiếp theo|tương lai|thêm|sâu hơn)|hướng (tiếp|nghiên "
                                                  r"cứu)|cần (thêm )?(nghiên cứu|thử nghiệm)|future research"))),
    "24a": (("phuong_phap", "cuoi", "tom_tat"), "Nêu tên cơ quan đăng ký và số đăng ký của tổng quan — hoặc nêu không "
                                                "đăng ký.",
            (_y("tên cơ quan đăng ký", r"PROSPERO|INPLASY|\bOSF\b|Research Registry|(không|chưa) (được )?đăng ký"),
             _y("số đăng ký", r"CRD\d{6,}|INPLASY\d+|osf\.io/\w+|reviewregistry\d+|(không|chưa) (được )?đăng ký")),
            None, "", True),
    "24b": (("phuong_phap", "cuoi"), "Nêu nơi truy cập đề cương tổng quan — hoặc nêu không soạn đề cương.",
            (_y("nơi truy cập đề cương", r"(đề cương|giao thức|protocol)[^.\n]{0,160}(truy cập|công bố|đăng tải|cung "
                                         r"cấp|tài liệu bổ sung|phụ lục|theo yêu cầu|available|lưu (trữ|tại)|"
                                         r"osf\.io|CRD\d)|(không|chưa) (có|soạn|xây dựng) (đề cương|giao thức)"),)),
    "24c": (("phuong_phap", "cuoi", "ket_qua"), "Mô tả và giải thích mọi sửa đổi so với thông tin đăng ký hoặc đề "
                                                "cương — hoặc nêu không có.",
            (_y("sửa đổi so với đăng ký/đề cương", r"(thay đổi|sửa đổi|điều chỉnh|khác)[^.\n]{0,100}(đề cương|đăng ký|"
                                                   r"PROSPERO|giao thức|protocol)|không có (thay đổi|sửa đổi)"
                                                   r"[^.\n]{0,80}(đề cương|đăng ký|giao thức)|(đề cương|giao thức|"
                                                   r"protocol|đăng ký)[^.\n]{0,80}không (thay đổi|sửa đổi)|"
                                                   r"amendments?|deviations? from"),)),
    "25": (("cuoi", "phuong_phap"), "Nêu nguồn hỗ trợ tài chính/phi tài chính và vai trò nhà tài trợ — hoặc nêu không "
                                    "có tài trợ.",
           (_y("nguồn hỗ trợ", NGUON_KINH_PHI_BT + r"|hỗ trợ"), _y("vai trò nhà tài trợ", VAI_TRO_TAI_TRO_BT)),
           None, "", True),
    "26": (("cuoi",), "Khai xung đột lợi ích của các tác giả tổng quan.",
           (_y("xung đột lợi ích", TC.XUNG_DOT + r"|competing interests?|conflicts? of interest"),)),
    "27": (("cuoi", "phuong_phap", "phu_luc"), "Nêu tài liệu nào được công bố và ở đâu: mẫu biểu thu thập dữ liệu, dữ "
                                               "liệu trích từ các nghiên cứu, dữ liệu dùng cho phân tích, mã phân "
                                               "tích, tài liệu khác.",
           (_y("tài liệu được nêu", r"(mẫu|biểu mẫu|phiếu) (thu thập|trích)|dữ liệu (đã |được )?trích|dữ liệu (dùng "
                                    r"cho |của )?(phân tích|nghiên cứu)|bộ dữ liệu|mã (phân tích|lệnh|nguồn)|"
                                    r"kịch bản phân tích|script|\bcode\b|(không|chưa) (công bố|chia sẻ)", so_lieu=True),
            _y("nơi/cách truy cập", r"theo yêu cầu|kho (lưu trữ|dữ liệu)|repository|\bOSF\b|GitHub|Zenodo|"
                                    r"tài liệu bổ sung|gói phát hành|công khai|truy cập|cung cấp|on request",
               so_lieu=True)), None, "", True),
}


def _muc_prisma() -> List[MucKiem]:
    van = {ma: (phan, chu_de, nv) for ma, phan, chu_de, nv in CBC.PRISMA_2020_ITEMS}
    assert set(van) == set(_PRISMA_2020), "mã PRISMA 2020 lệch giữa kho nguyên văn và bảng tiêu chí"
    ra = []
    for ma, tc in _PRISMA_2020.items():
        phan, tieu_chi, yeu_to = tc[:3]
        khi, ly_do = (tc[3], tc[4]) if len(tc) > 4 else (None, "")
        cung = bool(tc[5]) if len(tc) > 5 else False
        nv = van[ma][2]
        if ma == "2":
            # mục 2 chỉ dẫn sang Table 2 — kèm nguyên văn 12 mục PRISMA 2020 for Abstracts để người phân xử đối chiếu
            nv += " PRISMA 2020 for Abstracts: " + " · ".join(f"A{m}. {n}" for m, _p, _c, n in
                                                             CBC.PRISMA_2020_ABSTRACT_ITEMS)
        ra.append(MucKiem("PRISMA 2020", ma, van[ma][1], nv, tieu_chi, tuple(phan),
                          tuple(replace(y, khi=_pham_vi(y.khi, phan)) for y in yeu_to), "bat_buoc",
                          _pham_vi(khi, phan), ly_do, cung))
    return ra


def _pham_vi(mau: Optional[str], phan: Sequence[str]) -> Optional[str]:
    """Gắn phạm vi chương cho biểu thức điều kiện của mục đề cương khi dùng ở bản thảo: chương Phương pháp + chương của
    chính mục, bỏ Đặt vấn đề/Bàn luận/Kết luận (nhắc nghiên cứu khác). Biểu thức đã có phạm vi («@…:») giữ nguyên."""
    if not mau:
        return mau
    phu = mau.startswith("!")
    goc = mau[1:] if phu else mau
    if goc.startswith("@"):
        return mau
    khoa = ["phuong_phap"] + [c for c in phan if c not in ("phuong_phap", "gioi_thieu", "ban_luan", "ket_luan")]
    return ("!" if phu else "") + "@" + ",".join(khoa) + ":" + goc


def sang_ban_thao(muc: MucKiem, thiet_ke: str) -> Optional[MucKiem]:
    """Đổi một mục của ĐỀ CƯƠNG sang mục của BẢN THẢO (phần = chương IMRAD, mọi mục bắt buộc). None = mục chỉ có ở hồ
    sơ đề cương (không áp cho bài báo)."""
    tk = K._TK_STROBE.get(S.canonical_design_code(thiet_ke) or "", "")
    gd = _GHI_DE.get((muc.chuan, muc.ma, tk)) or _GHI_DE.get((muc.chuan, muc.ma))
    if gd:
        if gd["chi_de_cuong"]:
            return None
        # điều kiện của tiêu chí ghi đè cũng chỉ xét Phương pháp + chương của mục (22/11: CONSORT 12b từng kích hoạt
        # vì «Hướng tiếp: thử nghiệm đa trung tâm» ở Bàn luận bản thảo RCT giả lập)
        return replace(muc, phan=gd["phan"], tieu_chi=gd["tieu_chi"], muc_do="bat_buoc",
                       yeu_to=tuple(replace(y, khi=_pham_vi(y.khi, gd["phan"])) for y in gd["yeu_to"]),
                       ap_dung_khi=_pham_vi(gd["khi"] if gd["khi"] is not None else muc.ap_dung_khi, gd["phan"]),
                       ly_do_dieu_kien=gd["ly_do"] or muc.ly_do_dieu_kien, cung_doan=gd["cung_doan"],
                       chan=gd["chan"] and muc.chan, ly_do_khong_chan=gd["ly_do_khong_chan"])
    if muc.muc_do == "bao_cao":
        # chưa có tiêu chí bản thảo: bỏ yếu tố ⇒ `cham_muc` báo «chưa đo được» (không đạt suông)
        return replace(muc, phan=("tom_tat",), yeu_to=(), muc_do="bat_buoc")
    phan: List[str] = []
    for k in muc.phan:
        for c in PHAN_SANG_IMRAD.get(k, ("phuong_phap",)):
            if c not in phan:
                phan.append(c)
    if muc.muc_do == "ke_hoach":
        phan = [c for c in phan if c in CHUONG_KET_QUA] or ["ket_qua", "ban_luan"]
    return replace(muc, phan=tuple(phan), muc_do="bat_buoc", ap_dung_khi=_pham_vi(muc.ap_dung_khi, phan),
                   yeu_to=tuple(_thay_mau(replace(y, khi=_pham_vi(y.khi, phan))) for y in muc.yeu_to))


def danh_sach_muc_ban_thao(chuan: str, thiet_ke: str) -> Optional[List[MucKiem]]:
    """Mục kiểm bản thảo của một chuẩn; None khi chuẩn chưa có tiêu chí tự động."""
    if chuan == "CONSORT 2025":
        return _muc_consort()
    if chuan == "PRISMA 2020":
        return _muc_prisma()
    goc = K.danh_sach_muc(chuan, thiet_ke)
    if goc is None:
        return None
    return [m for m in (sang_ban_thao(x, thiet_ke) for x in goc) if m is not None]


def chuan_ap_dung_ban_thao(thiet_ke: str, md: str, bt: Optional[BanThao] = None) -> List[Tuple[str, str]]:
    """Chuẩn áp cho BÀI BÁO: như K17 nhưng chuẩn đề cương (SPIRIT, PRISMA-P) đổi sang chuẩn báo cáo cùng thiết kế. Điều
    kiện chuẩn (RECORD, CROSS, COSMIN…) xét ở Phương pháp + Tóm tắt khi tách được chương (không lấy câu bàn luận về
    nghiên cứu khác)."""
    if bt is not None:
        # điều kiện kích hoạt chuẩn KHÔNG phụ thuộc ô chờ điền cùng câu (22/11: ở chế độ nộp, «hồ sơ bệnh án điện tử
        # (eHospital) … trích từ [CẦN…]» từng làm RECORD biến mất khỏi bản thảo BTM)
        bt_dk = tach_ban_thao(md, nghiem=False)
        van = "\n".join(p.van for p in bt_dk.cac_phan if p.tieu_de in ("⟦phuong_phap⟧", "⟦tom_tat⟧"))
        md = van or bt_dk.md_sach
    ra = []
    # 22/11/2026: phần mở rộng CONSORT cho thử nghiệm cụm/không kém hơn (`K.CHUAN_DIEU_KIEN_RCT`) áp cho bài báo cùng
    # điều kiện với đề cương — chỉ đọc phần đề tài tự nêu thiết kế (ở đây: Phương pháp + Tóm tắt; `K.chuan_ap_dung`
    # còn bỏ Giới thiệu/Bàn luận/TLTK khi văn bản chưa tách chương). Mục kết quả có tiêu chí bài báo riêng (`_GHI_DE`).
    for ten, ly_do in K.chuan_ap_dung(thiet_ke, md):
        moi = CHUAN_BAN_THAO.get(ten)
        ra.append((moi, f"{ly_do} — bài báo dùng {moi} thay {ten}") if moi else (ten, ly_do))
    return ra


def co_so_lieu_tu_dong(md: str) -> bool:
    """Bản thảo coi là ĐÃ CÓ SỐ LIỆU khi không còn ô [CẦN…]/[TO BE COMPLETED…]."""
    return not _O_CAN_RE.search(unicodedata.normalize("NFC", md))


def sang_giao_thuc(muc: MucKiem, thiet_ke: str) -> MucKiem:
    """Mục ĐỀ CƯƠNG cho BÀI BÁO GIAO THỨC: giữ mức độ của K17 (`bao_cao` chỉ liệt kê, `ke_hoach` đòi kế hoạch) nhưng
    tìm theo chương IMRAD của bài báo; mục phương pháp dùng tiêu chí ghi đè cách viết bài báo khi có."""
    tk = K._TK_STROBE.get(S.canonical_design_code(thiet_ke) or "", "")
    gd = _GHI_DE.get((muc.chuan, muc.ma, tk)) or _GHI_DE.get((muc.chuan, muc.ma))
    if gd and muc.muc_do == "bat_buoc" and not gd["chi_de_cuong"]:
        return replace(sang_ban_thao(muc, thiet_ke) or muc, muc_do="bat_buoc")
    phan: List[str] = []
    for k in muc.phan:
        for c in PHAN_SANG_IMRAD.get(k, ("phuong_phap",)):
            if c not in phan:
                phan.append(c)
    if muc.muc_do == "ke_hoach" and "phuong_phap" not in phan:
        phan.append("phuong_phap")  # bài báo giao thức hay đặt kế hoạch (sơ đồ chọn mẫu, khung bảng) ở Phương pháp
    return replace(muc, phan=tuple(phan), ap_dung_khi=_pham_vi(muc.ap_dung_khi, phan),
                   yeu_to=tuple(_thay_mau(replace(y, khi=_pham_vi(y.khi, phan))) for y in muc.yeu_to))


def doi_chieu_giao_thuc(md: str, thiet_ke: str, nghiem: bool = False) -> Dict[str, object]:
    """BÀI BÁO GIAO THỨC (vd `Bai-bao-giao-thuc_*.md`): tiêu chí ĐỀ CƯƠNG của K17 (chuẩn đề cương SPIRIT/PRISMA-P giữ
    nguyên), phần = chương IMRAD. `nghiem` (chế độ nộp) ⇒ ô [CẦN…] là ô trống và yếu tố `so_lieu` bắt buộc."""
    bt = tach_ban_thao(md, nghiem=nghiem)
    bt_dk = tach_ban_thao(md, nghiem=False)
    van_dk = "\n".join(p.van for p in bt_dk.cac_phan if p.tieu_de in ("⟦phuong_phap⟧", "⟦tom_tat⟧")) or bt_dk.md_sach
    ap_dung = K.chuan_ap_dung(thiet_ke, van_dk)
    ket_qua: List[KetQua] = []
    chua_do: List[Tuple[str, str]] = []
    for chuan, _ly in ap_dung:
        goc = K.danh_sach_muc(chuan, thiet_ke)
        if goc is None:
            chua_do.append((chuan, "chuẩn chưa có tiêu chí kiểm tự động theo mục — KHÔNG ĐO ĐƯỢC, không tính là đạt"))
            continue
        for m in goc:
            ket_qua.append(K.cham_muc(sang_giao_thuc(m, thiet_ke), bt.md_sach, bt.cac_phan, khoi_fn=bt.khoi,
                                      co_so_lieu=nghiem))
    thieu = [x for x in thieu_cau_truc(bt, "", co_so_lieu=False) if "Kết quả" not in x]
    return {"che_do": "giao_thuc", "co_so_lieu": nghiem, "chuan": ap_dung, "ket_qua": ket_qua, "chua_do": chua_do,
            "cau_truc": thieu, "cap_chuong": bt.cap_chuong}


def doi_chieu_ban_thao(md: str, thiet_ke: str, co_so_lieu: Optional[bool] = None) -> Dict[str, object]:
    """Đối chiếu bản thảo: {'che_do', 'co_so_lieu', 'chuan', 'ket_qua': [KetQua], 'chua_do': [(chuẩn, lý do)],
    'cau_truc': [chương thiếu]}."""
    if co_so_lieu is None:
        co_so_lieu = co_so_lieu_tu_dong(md)
    bt = tach_ban_thao(md, nghiem=co_so_lieu)
    ap_dung = chuan_ap_dung_ban_thao(thiet_ke, md, bt)
    ket_qua: List[KetQua] = []
    chua_do: List[Tuple[str, str]] = []
    ly_do_kq = ("bản thảo chưa có số liệu (còn ô [CẦN…], chưa chạy chế độ nộp) — phần kết quả/bàn luận CHƯA ĐO ĐƯỢC, "
                "không tính là đạt")
    for chuan, _ly in ap_dung:
        muc = danh_sach_muc_ban_thao(chuan, thiet_ke)
        if muc is None:
            chua_do.append((chuan, "chuẩn chưa có tiêu chí kiểm tự động cho bản thảo — KHÔNG ĐO ĐƯỢC, không tính là "
                                   "đạt"))
            continue
        for m in muc:
            chi_kq = bool(m.phan) and set(m.phan) <= CHUONG_KET_QUA
            ket_qua.append(K.cham_muc(m, bt.md_sach, bt.cac_phan, khoi_fn=bt.khoi, co_so_lieu=co_so_lieu,
                                      chua_do_ly_do=ly_do_kq if (chi_kq and not co_so_lieu) else None))
    return {"che_do": "ban_thao", "co_so_lieu": co_so_lieu, "chuan": ap_dung, "ket_qua": ket_qua,
            "chua_do": chua_do, "cau_truc": thieu_cau_truc(bt, thiet_ke, co_so_lieu), "cap_chuong": bt.cap_chuong}
