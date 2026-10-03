#!/usr/bin/env python3
"""Hợp đồng NHẬN DIỆN Ô CÒN TRỐNG dùng chung cho 11 cổng chất lượng G0–G10 và các vị từ «đã điền» (03/10/2026).

VÌ SAO CÓ. Trước ngày này mỗi `tools/gN_quality_gate.py` tự viết một danh sách «dấu hiệu chưa điền» riêng — 11 danh
sách, không cái
nào giống cái nào (G5/G6 chỉ «[CẦN», G9/G10 có «[TBD|TODO|PENDING», G0/G7 có «___», G3 có «<CẦN»…), và 6 vị từ trường
ngoài cổng
(`annex2_quality_gate._present`, `lock_analysis_dataset._is_filled`, `research_study_spec.is_present`,
`skill_standards._is_real_value`,
`audit_research_gates._present_value`, chốt G4 của `approve_gate`) coi «[TO BE COMPLETED]», «___», «[đơn vị]» là GIÁ
TRỊ THẬT. Khuôn
sinh `run_gN_auto.py` lại in ô mẫu KHÔNG mang nhãn [CẦN]. Sự cố 03/10/2026 (đề tài C1a): ICF đã điền mục đích vẫn còn
câu ví dụ thử
nghiệm thuốc và 14 ô [TO BE COMPLETED]; lượt đo cùng ngày chạy thật thấy cả 11 cổng có đường tới READY/PASS khi còn ô
mẫu.

HAI API — đừng dùng lẫn:
  • QUÉT VĂN BẢN (`tim`, `co_o_trong`, `dong_con_trong`, `tom_tat`): tài liệu do khuôn sinh in ra rồi người điền. Chọn
  HỌ theo ngữ cảnh.
  • VỊ TỪ TRƯỜNG (`co_noi_dung_that`): MỘT giá trị (study_meta.gate_params…, trường hồ sơ khoá). Mặc định bật MỌI họ +
  luật riêng của
    trường (ký hiệu đứng một mình «?», «-»; chuỗi chỉ toàn ô tick «☐ … ☐ …»). Chỉ được AND thêm vào vị từ cũ — không
    thay token cũ.

CÁC HỌ DẤU HIỆU (so trên văn bản đã chuẩn hoá NFC):
  • `NHAN`      — nhãn chưa điền MANG CHỮ: [CẦN…] (mọi hoa/thường) · [CAN …] bản bỏ dấu (CHỮ HOA, theo sau là khoảng
                  trắng/_/]/—/:/-;
                  «[Cancer]», «[can thiệp]» KHÔNG khớp) · [REQUIRE_HUMAN…] (bắt buộc có «[» — enum
                  REQUIRE_HUMAN_REVIEW trong JSON không
                  khớp) · [TODO]/[TBD]/[PENDING] · [TO BE COMPLETED…] · <CẦN…> · CHƯA XÁC NHẬN (CHỮ HOA — văn xuôi
                  «chưa xác nhận» không
                  khớp) · [BÁC SĨ ĐIỀN/TỰ/CHỌN/XÁC NHẬN/ẤN ĐỊNH/RÀ…] · [TÁC GIẢ ĐIỀN…] · [CHỜ BÁC SĨ…] · [ĐIỀN TRỰC
                  TIẾP…] ·
                  <…điền/fill/name/date/tên/ngày…> (ngoặc nhọn KHÔNG chứa «=» và không mở bằng «!»/«/» — thẻ XML
                  «<w:shd w:fill=…>» và
                  chú thích HTML «<!-- … -->» không khớp).
  • `NHAP`      — nhãn BẢN NHÁP/chờ duyệt: [DỰ THẢO…] · [BẢN NHÁP…]. Trong GIÁ TRỊ TRƯỜNG = chưa chốt; trong TÀI LIỆU
                  thường là nhãn
                  bắt buộc (guardrail R_LABEL của G0, khối DRAFT của G7, R3/R4 của G9 A10, «[DỰ THẢO]» của G10) ⇒ quét
                  tài liệu KHÔNG
                  bật họ này trừ khi cổng biết rõ ngữ cảnh.
  • `MAU_CHUNG` — ô mẫu chung của khuôn sinh không mang nhãn: [đơn vị] · [bệnh] · [nơi thực hiện] · [địa điểm] ·
                  [ca/hồ sơ] ·
                  [tài trợ… (khuôn ngắt dòng giữa ô) · thuốc/can thiệp X · ô khung «[P — điền]» (mọi «[… — điền]») ·
                  [xem §N bên
                  dưới] · [sẽ/sẽ không] · ô mẫu chữ thường mở đầu bằng «tên/mô tả/căn cứ pháp lý/họ tên» · lệnh soạn
                  thảo «XOÁ/XÓA mục
                  này». «[Đã pin bởi bác sĩ — …]» KHÔNG khớp (nhãn hợp lệ của G1).
  • `TRONG`     — ô trống không chữ: «___» (≥3 gạch dưới) · «……» (≥2 ký tự ba chấm liền — MỘT «…» là dấu lược) ·
                  «......» (≥6 dấu
                  chấm). «...» ba chấm ASCII là văn xuôi hợp lệ (đo: C1a primary_outcome_measure) — KHÔNG khớp. PHỤ
                  THUỘC NGỮ CẢNH:
                  bảng trống dự kiến của SAP, dòng ký/ngày điền tay, ô điều kiện là HỢP LỆ ⇒ chỉ bật ở trường/mục đòi
                  điền đủ.
  • `THU_CONG`  — «[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]» của G10: còn nhãn = CHƯA xác nhận. G10 sinh nhãn này VÔ ĐIỀU
                  KIỆN trong bản
                  nháp ⇒ quét toàn văn đề cương G10 sẽ chặn vĩnh viễn; dùng cho GIÁ TRỊ TRƯỜNG, hoặc đếm hiển thị.

Docstring/chú thích tiếng Việt; tên hàm tiếng Anh theo thông lệ của `gate_contract.py`. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable

NHAN = "nhan"
NHAP = "nhap"
MAU_CHUNG = "mau_chung"
TRONG = "trong"
THU_CONG = "thu_cong"
TAT_CA_HO = (NHAN, NHAP, MAU_CHUNG, TRONG, THU_CONG)
# Quét TÀI LIỆU có chữ do người điền (ICF, đề cương, bản thảo…): nhãn + ô mẫu chung. Ô trống không chữ / nhãn nháp /
# thủ công bật riêng.
HO_MAC_DINH = (NHAN, MAU_CHUNG)
# Vị từ GIÁ TRỊ TRƯỜNG: một giá trị còn BẤT KỲ dấu hiệu nào là chưa điền.
HO_TRUONG = TAT_CA_HO

TAG_THU_CONG = "[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]"

_MAU: dict[str, tuple[re.Pattern[str], ...]] = {
    NHAN: (
        re.compile(r"\[\s*CẦN|\[\s*(?:REQUIRE_HUMAN|TODO\b|TBD\b|PENDING\b|TO BE COMPLETED|CHỜ BÁC SĨ|"
                   r"ĐIỀN TRỰC TIẾP|TÁC GIẢ ĐIỀN|BÁC SĨ (?:ĐIỀN|TỰ|CHỌN|XÁC NHẬN|ẤN ĐỊNH|RÀ))|<\s*CẦN", re.IGNORECASE),
        # Bản bỏ dấu của [CẦN …] — CHỮ HOA và không phải đầu một từ dài hơn («[Cancer]», «[can thiệp]», «[Canxi]»
        # không khớp).
        re.compile(r"\[\s*CAN(?=[\s_\]—:\-]|$)"),
        re.compile(r"CHƯA XÁC NHẬN"),
        re.compile(r"<(?![!/])(?![^<>\n]*=)[^<>\n]{0,40}\b(?:điền|fill|name|date|tên|ngày)\b[^<>\n]{0,40}>",
                   re.IGNORECASE),
    ),
    NHAP: (re.compile(r"\[\s*(?:DỰ THẢO|BẢN NHÁP)", re.IGNORECASE),),
    MAU_CHUNG: (
        re.compile(r"\[(?:đơn vị|bệnh|nơi thực hiện|địa điểm|ca/hồ sơ|sẽ/sẽ không)\]|\[tài trợ|thuốc/can thiệp X\b",
                   re.IGNORECASE),
        re.compile(r"\[[^\[\]\n]{0,40}—\s*điền\s*\]|\[xem §\s*\d+[^\]\n]{0,20}\]", re.IGNORECASE),
        re.compile(r"\[(?:tên|mô tả|căn cứ pháp lý|họ tên)\b[^\]\n]{0,80}\]"),
        re.compile(r"\bX[OÓ]A mục này\b", re.IGNORECASE),
    ),
    TRONG: (re.compile(r"_{3,}|…{2,}|\.{6,}"),),
    THU_CONG: (re.compile(re.escape(TAG_THU_CONG), re.IGNORECASE),),
}

# Ký hiệu đứng MỘT MÌNH thay cho giá trị (chỉ áp cho vị từ trường).
_KY_HIEU_TRONG = {"?", "??", "-", "--", "—", "–", "…", "...", "x", "xx", "xxx"}
_O_TICK_TRONG, _O_TICK_DA_CHON = "☐", ("☑", "☒", "✔", "✓", "■", "[x]", "[X]")


@dataclass(frozen=True)
class PhatHien:
    """Một ô còn trống: họ, chuỗi khớp, số dòng (từ 1) và dòng đã rút gọn khoảng trắng (≤ 240 ký tự)."""

    ho: str
    khop: str
    dong_so: int
    dong: str


def _chuan_ho(ho: Iterable[str] | None, mac_dinh: tuple[str, ...] = HO_MAC_DINH) -> tuple[str, ...]:
    ho = tuple(mac_dinh if ho is None else ho)
    la = [h for h in ho if h not in _MAU]
    if la:
        raise ValueError(f"họ dấu hiệu không có: {la} — chỉ nhận {TAT_CA_HO}")
    return ho


def _nfc(van_ban: Any) -> str:
    return unicodedata.normalize("NFC", str(van_ban or ""))


def mau(ho: str) -> tuple[re.Pattern[str], ...]:
    """Các biểu thức của MỘT họ — cho cổng cần ghép luật riêng."""
    return _MAU[_chuan_ho((ho,))[0]]


def tim(van_ban: Any, ho: Iterable[str] | None = None, them: Iterable[str] = ()) -> list[PhatHien]:
    """Mọi ô còn trống theo các họ `ho` (mặc định NHAN + MAU_CHUNG), theo thứ tự dòng rồi vị trí.

    `them`: chuỗi CON nguyên văn riêng của một cổng (so không phân biệt hoa/thường) — giữ marker cũ của cổng, vd «SUY
    RA TỪ TOPIC»."""
    ho_chon = _chuan_ho(ho)
    them_up = tuple(t.upper() for t in them if t)
    ra: list[PhatHien] = []
    for so, dong in enumerate(_nfc(van_ban).splitlines(), 1):
        trung: list[tuple[int, str, str]] = []
        for h in ho_chon:
            for bt in _MAU[h]:
                trung.extend((m.start(), h, m.group(0)) for m in bt.finditer(dong))
        if them_up:
            up = dong.upper()
            for t in them_up:
                i = up.find(t)
                while i >= 0:
                    trung.append((i, "them", dong[i:i + len(t)]))
                    i = up.find(t, i + 1)
        if trung:
            gon = re.sub(r"\s+", " ", dong.strip())[:240]
            ra.extend(PhatHien(h, k, so, gon) for _vt, h, k in sorted(trung))
    return ra


def co_o_trong(van_ban: Any, ho: Iterable[str] | None = None, them: Iterable[str] = ()) -> bool:
    """True khi còn ÍT NHẤT một ô trống theo các họ `ho` (+ chuỗi riêng `them`)."""
    vb = _nfc(van_ban)
    if any(bt.search(vb) for h in _chuan_ho(ho) for bt in _MAU[h]):
        return True
    up = vb.upper()
    return any(t and t.upper() in up for t in them)


def dong_con_trong(van_ban: Any, ho: Iterable[str] | None = None, them: Iterable[str] = ()) -> list[str]:
    """Các DÒNG (đã rút gọn, không lặp, theo thứ tự) còn ô trống — dạng bằng chứng các cổng in vào báo cáo."""
    ra: list[str] = []
    for p in tim(van_ban, ho, them):
        if p.dong and p.dong not in ra:
            ra.append(p.dong)
    return ra


def tom_tat(van_ban: Any, ho: Iterable[str] | None = None) -> dict[str, int]:
    """Đếm ô trống theo họ (chỉ các họ được chọn) — cho bằng chứng/nhãn báo cáo."""
    dem = {h: 0 for h in _chuan_ho(ho)}
    for p in tim(van_ban, ho):
        dem[p.ho] += 1
    return dem


def _chi_toan_o_tick(s: str) -> bool:
    """Chuỗi chỉ là danh sách lựa chọn CHƯA chọn («☐ tăng ☐ giảm»): ≥ 2 ô ☐ và không ô nào đã đánh dấu."""
    return s.count(_O_TICK_TRONG) >= 2 and not any(d in s for d in _O_TICK_DA_CHON)


def co_noi_dung_that(gia_tri: Any, ho: Iterable[str] | None = None, them: Iterable[str] = (), toi_thieu: int = 1,
                     danh_sach_moi_phan_tu: bool = True) -> bool:
    """Vị từ GIÁ TRỊ TRƯỜNG: có nội dung thật không.

    None / rỗng / chỉ khoảng trắng / ký hiệu đứng một mình («?», «-», «—», «...», «x») / chuỗi chỉ toàn ô tick chưa
    chọn / còn ô trống
    theo `ho` (mặc định MỌI họ) hoặc chuỗi riêng `them` ⇒ False. Số và bool là giá trị thật (0 vẫn là giá trị). Danh
    sách/tuple/set:
    rỗng ⇒ False; `danh_sach_moi_phan_tu=True` (mặc định) đòi MỌI phần tử thật — đặt False để giữ ngữ nghĩa any() cũ
    của cổng nào cần.
    Dict: rỗng ⇒ False, mọi giá trị phải thật. `toi_thieu` = số ký tự chữ-số tối thiểu sau khi bỏ dấu câu."""
    ho_chon = _chuan_ho(ho, HO_TRUONG)
    if gia_tri is None:
        return False
    if isinstance(gia_tri, bool) or isinstance(gia_tri, (int, float)):
        return True
    if isinstance(gia_tri, (list, tuple, set)):
        if not gia_tri:
            return False
        kq = [co_noi_dung_that(x, ho_chon, them, toi_thieu, danh_sach_moi_phan_tu) for x in gia_tri]
        return all(kq) if danh_sach_moi_phan_tu else any(kq)
    if isinstance(gia_tri, dict):
        return bool(gia_tri) and all(co_noi_dung_that(x, ho_chon, them, toi_thieu, danh_sach_moi_phan_tu)
                                     for x in gia_tri.values())
    s = _nfc(gia_tri).strip()
    if not s or s.casefold() in _KY_HIEU_TRONG or _chi_toan_o_tick(s):
        return False
    if co_o_trong(s, ho_chon, them):
        return False
    return len(re.sub(r"[\W_]+", "", s)) >= toi_thieu
