#!/usr/bin/env python3
"""Hồ sơ ĐĂNG KÝ đề tài KH&CN cấp Bệnh viện theo bộ mẫu riêng của BVQY175 (DTCS-DKCT.01-DK · 02-TM · 03-LLKH).

VÌ SAO (21/11/2026, bác sĩ gửi bộ mẫu «7. Mẫu DTCS-DKCT.01-DK», «8. Mẫu DTCS-DKCT.02-TM», «9. Mẫu DTCS-DKCT.03-LLKH» —
«những mẫu đã được chỉnh sửa riêng cho phù hợp BVQY175»): hệ G0–G10 dựng được đề cương nộp, còn bản THUYẾT MINH (TM)
bác sĩ từng điền tay hồi 06/2026 nay đã LỆCH đề cương đã khoá (TM cũ ghi chọn mẫu thuận tiện, d = 0,031, tiến độ 2026;
đề cương hiện hành của C1a chọn mẫu hệ thống phân tầng, tiến độ 12/2026–12/2028). Công cụ này điền TM và đơn đăng ký
(DK) TỪ ĐỀ CƯƠNG NỘP HIỆN HÀNH, để hai văn bản không trôi khỏi nhau.

Cách làm: trích dữ kiện TẤT ĐỊNH từ `exports/<mã>/DE_CUONG_NOP_HOI_DONG_<mã>.md` (đọc được cả cấu trúc cũ «1. ĐẶT VẤN
ĐỀ … 6. KẾ HOẠCH» lẫn khuôn chương của hướng dẫn chung) thành một mô hình nội dung — mọi đoạn là NGUYÊN VĂN đề cương,
kèm số dòng nguồn — rồi (a) dựng bản xem `.md`; (b) điền thẳng vào TỆP MẪU Word của bệnh viện (giữ nguyên khung tiêu
ngữ, bảng, ô chọn); (c) dựng danh mục hồ sơ: ô nào chủ nhiệm tự điền, ai phải nộp lý lịch khoa học.

Đầu ra (thư mục mới `exports/<mã>/ho_so_dtcs/`, `exports/` bị .gitignore):
  DTCS-DKCT.01-DK_<mã>.docx · DTCS-DKCT.02-TM_<mã>.docx · DTCS-DKCT.02-TM_<mã>.md · DANH_MUC_HO_SO_DTCS_<mã>.md
Tệp đã có ⇒ sao lưu `ho_so_dtcs/_sao_luu/<tên>.bak-<giờ>` TRƯỚC khi ghi đè.

Ranh giới:
  - KHÔNG điền thông tin cá nhân (số định danh/CCCD, ngày sinh, điện thoại, e-mail, địa chỉ riêng) — ô đó giữ dòng chấm;
    vì thế KHÔNG dựng mẫu 03-LLKH (toàn mục cá nhân): danh mục chỉ liệt kê ai phải nộp.
  - KHÔNG chọn thay chủ nhiệm các ô quyết định (phương thức khoán chi, loại đề tài, tình trạng đề tài, đơn vị phối hợp,
    số tiền) — chỉ đánh dấu «Y, dược» (lĩnh vực) và ghi nguồn «Tự có» khi đề cương ghi tự túc.
  - KHÔNG viết câu mới cho nội dung chuyên môn: 15.1 tách đoạn ngoài/trong nước bằng luật từ khoá (ghi rõ để chủ nhiệm
    rà); 17 chép chương đối tượng và phương pháp; 21 chép bảng tiến độ (hoặc các bước của quy trình nghiên cứu).
  - Quét mẫu định danh trên mọi đoạn máy chèn; có ⇒ không ghi (mã 3).

Lệnh:
  python3 tools/ho_so_dtcs_bvqy175.py --study <mã> [--xem] [--json]        # CHẠY KHÔ (mặc định): không ghi gì
  python3 tools/ho_so_dtcs_bvqy175.py --study <mã> --ghi [--thu-muc-ra <dir>]
Mẫu Word: biến `EBM_MAU_DTCS_BVQY175` → `<cha-của-«Claude AI»>/Đề tài NCKH/Mau DTCS BV175/docx` (ngoài git).
Mã thoát: 0 xong · 1 đã ghi bản xem/danh mục nhưng chưa điền được Word (thiếu mẫu/python-docx) · 2 thiếu đề cương nộp ·
3 tham số sai / có mẫu định danh.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
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

import goi_bao_ve_hoi_dong as GB  # noqa: E402  (đọc đề mục/câu/bảng của đề cương nộp — một bộ đọc dùng chung)

TEN_DE_CUONG = "DE_CUONG_NOP_HOI_DONG_{study}.md"
THU_MUC_RA = "ho_so_dtcs"
MAU = {"dk": "7. Mau DTCS-DKCT.01-DK.docx", "tm": "8. Mau DTCS-DKCT.02-TM.docx"}
TEN_RA = {"dk": "DTCS-DKCT.01-DK_{study}.docx", "tm": "DTCS-DKCT.02-TM_{study}.docx",
          "tm_md": "DTCS-DKCT.02-TM_{study}.md", "danh_muc": "DANH_MUC_HO_SO_DTCS_{study}.md"}
CHAM = "………"
LOI_DAN = "Cần bác sĩ kiểm chứng."
TRAN_HANG_BANG = 20  # bảng dài hơn (vd bảng biến số) chỉ chép 20 hàng đầu, ghi chỗ xem bảng đầy đủ

_CHAM_RE = re.compile(r"^[\s.…_\-–]*$")
_TRONG_NUOC_RE = re.compile(r"Việt Nam|trong nước|Bộ Y tế|Thông tư|Quyết định số|Nghị định|quân y|Quân đội|Hà Nội|"
                            r"Hồ Chí Minh|TP\.? ?HCM|Cần Thơ|Huế|Đà Nẵng|BVQY|\b175\b", re.IGNORECASE)
_KHOANG_THANG_RE = re.compile(r"(?:tháng\s+)?(?<![\d/])(\d{1,2})/(\d{4})\s*(?:[–-]|đến(?:\s+tháng)?)\s*"
                              r"(?:tháng\s+)?(\d{1,2})/(\d{4})(?![\d/])")
_TRICH_SO_RE = re.compile(r"\[(\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–-]\s*\d+)?)*)\]")
_MUC_TLTK_RE = re.compile(r"^(\d+)\.\s+(.+)$")


# ── Đọc đề cương ─────────────────────────────────────────────────────────────────────────────────────────────────────

def _co(v: Any) -> bool:
    """Có nội dung thật (không rỗng, không chỉ dòng chấm)."""
    return isinstance(v, str) and bool(v.strip()) and not _CHAM_RE.match(v)


def _o(d: str) -> List[str]:
    return [x.strip() for x in d.strip().strip("|").split("|")]


def _bang_dau(dong: Sequence[str], muc: GB.Muc) -> Tuple[List[str], List[Tuple[int, List[str]]]]:
    """(tiêu đề cột, [(số dòng, ô)]) của BẢNG ĐẦU TIÊN trong mục; không có ⇒ ([], [])."""
    for i in range(muc.dong + 1, muc.het):
        s = dong[i - 1].strip()
        if s.startswith("|") and re.match(r"^\|[\s:|-]+\|?\s*$", dong[i].strip()):
            dau = _o(s)
            hang: List[Tuple[int, List[str]]] = []
            j = i + 2
            while j <= muc.het and dong[j - 1].strip().startswith("|"):
                hang.append((j, _o(dong[j - 1])))
                j += 1
            return dau, hang
    return [], []


def _cot(dau: Sequence[str], *tu: str) -> Optional[int]:
    return next((k for k, o in enumerate(dau) if any(t in GB._chuan(o) for t in tu)), None)


@dataclass
class Doan:
    """Một đoạn/mục danh sách/hàng bảng NGUYÊN VĂN của đề cương, kèm số dòng."""
    van: str
    dong: int
    loai: str = "doan"  # doan · ds · bang · tieu_de


def doan_cua_muc(dong: Sequence[str], muc: GB.Muc, bo: Sequence[GB.Muc] = (), bang: bool = True) -> List[Doan]:
    """Đoạn văn (cả dòng), mục danh sách, đề mục con và hàng bảng của mục — bỏ các mục con trong `bo`."""
    ra: List[Doan] = []
    bo_dong = {i for m in bo for i in range(m.dong, m.het + 1)}
    i = muc.dong + 1
    while i <= muc.het:
        if i in bo_dong:
            i += 1
            continue
        s = dong[i - 1].strip()
        mh = GB._DE_MUC_RE.match(s)
        if mh:
            ra.append(Doan(mh.group(2).strip(), i, "tieu_de"))
        elif s.startswith("|") and i < len(dong) and re.match(r"^\|[\s:|-]+\|?\s*$", dong[i].strip()):
            dau = _o(s)
            j, n = i + 2, 0
            while j <= muc.het and dong[j - 1].strip().startswith("|"):
                if bang and n < TRAN_HANG_BANG:
                    o = _o(dong[j - 1])
                    ra.append(Doan("; ".join(f"{dau[k]}: {x}" if k < len(dau) and dau[k] and k else x
                                             for k, x in enumerate(o) if x), j, "bang"))
                n += 1
                j += 1
            if bang and n > TRAN_HANG_BANG:
                ra.append(Doan(f"(bảng còn {n - TRAN_HANG_BANG} hàng — xem bảng đầy đủ trong đề cương nộp, dòng "
                               f"{i}–{j - 1})", i, "bang"))
            i = j
            continue
        elif s and not s.startswith((">", "![", "<!--", "```")) and not set(s) <= set("-*_ ") and \
                not (not bang and (GB._CHU_THICH_BANG_RE.match(s) or GB._GHI_CHU_RE.match(s))):
            m = GB._MUC_DS_RE.match(dong[i - 1])
            ra.append(Doan(m.group(1).strip() if m else s, i, "ds" if m else "doan"))
        i += 1
    return ra


@dataclass
class MoHinh:
    """Nội dung điền mẫu — mọi chuỗi là nguyên văn đề cương (trừ nhãn của công cụ); `nguon` ghi số dòng."""
    study: str
    ten_de_tai: str = ""
    chu_nhiem: str = ""
    don_vi: str = ""
    thoi_gian: str = ""
    thang: Optional[Tuple[str, str]] = None  # ("12/2026", "12/2028")
    kinh_phi: str = ""
    tu_co: bool = False
    muc_tieu: List[Doan] = field(default_factory=list)
    ngoai_nuoc: List[Doan] = field(default_factory=list)
    trong_nuoc: List[Doan] = field(default_factory=list)
    luan_giai: List[Doan] = field(default_factory=list)
    tltk: List[Tuple[int, str]] = field(default_factory=list)
    phuong_phap: List[Tuple[str, List[Doan]]] = field(default_factory=list)
    vai_tro: List[str] = field(default_factory=list)
    tien_do: List[Tuple[str, str, str]] = field(default_factory=list)  # (nội dung, kết quả, thời gian)
    san_pham_bai_bao: List[str] = field(default_factory=list)
    san_pham_khac: List[str] = field(default_factory=list)
    pho_bien: List[Doan] = field(default_factory=list)
    dong_gop: List[Doan] = field(default_factory=list)
    du_tru: List[str] = field(default_factory=list)
    canh_bao: List[str] = field(default_factory=list)
    nguon: Dict[str, str] = field(default_factory=dict)


def _thong_tin_chung(dong: Sequence[str], cac_muc: Sequence[GB.Muc]) -> Dict[str, str]:
    muc = GB.tim_muc(cac_muc, r"thông tin chung")
    if muc is None:
        return {}
    _dau, hang = _bang_dau(dong, muc)
    return {GB._chuan(o[0]): o[1] for _so, o in hang if len(o) >= 2}


def _lay_tt(tt: Dict[str, str], *khoa: str) -> str:
    return next((v for k, v in tt.items() for x in khoa if k.startswith(x) and _co(v)), "")


def _muc_tieu(dong: Sequence[str], cac_muc: Sequence[GB.Muc]) -> List[Doan]:
    """Danh sách mục tiêu: mục «Mục tiêu» (2.1) trước; chương «MỤC TIÊU NGHIÊN CỨU» thì chỉ phần TRƯỚC mục con đầu tiên
    (đo C1a 21/11: lấy cả chương thì đếm luôn hai dòng giả thuyết H₀/H₁ của mục 2.3 thành mục tiêu)."""
    for mau, chi_than in ((r"^mục tiêu$", False), (r"^mục tiêu nghiên cứu$", True)):
        muc = GB.tim_muc(cac_muc, mau)
        if muc is None:
            continue
        ds: List[Doan] = []
        for d in doan_cua_muc(dong, muc, bang=False):
            if d.loai == "tieu_de" and chi_than:
                break
            if d.loai == "ds":
                ds.append(d)
        if ds:
            return ds
    dvd = GB.tim_muc(cac_muc, r"^đặt vấn đề$")  # khuôn hướng dẫn chung: mục tiêu ở cuối đặt vấn đề
    if dvd is not None:
        doan = doan_cua_muc(dong, dvd, bang=False)
        k = next((i for i, d in enumerate(doan) if "mục tiêu nghiên cứu" in GB._chuan(d.van)), None)
        if k is not None:
            return [d for d in doan[k + 1:] if d.loai == "ds"]
    return []


def _chuong(cac_muc: Sequence[GB.Muc], mau: str) -> Optional[GB.Muc]:
    """Chương cấp 1 khớp mẫu (bỏ tiền tố «CHƯƠNG n.» của khuôn hướng dẫn chung)."""
    bt = re.compile(mau)
    for m in cac_muc:
        if m.cap == 1 and bt.search(re.sub(r"^chương\s+\d+\.?\s*", "", GB._chuan(m.ten))):
            return m
    return None


def _con(cac_muc: Sequence[GB.Muc], cha: GB.Muc) -> List[GB.Muc]:
    return [m for m in cac_muc if m.cap == cha.cap + 1 and cha.dong < m.dong <= cha.het]


def _tltk(dong: Sequence[str]) -> Dict[int, str]:
    ra: Dict[int, str] = {}
    trong = False
    for d in dong:
        if re.match(r"^#{1,3}\s*(?:\d+\.?\s*)?TÀI LIỆU THAM KHẢO\s*$", d.strip()):
            trong = True
            continue
        if trong and re.match(r"^#\s", d):
            break
        m = _MUC_TLTK_RE.match(d.strip()) if trong else None
        if m:
            ra[int(m.group(1))] = m.group(2).strip()
    return ra


def _so_trich(van: str) -> List[int]:
    ra: List[int] = []
    for m in _TRICH_SO_RE.finditer(van):
        for phan in m.group(1).split(","):
            phan = phan.strip().replace("–", "-")
            if "-" in phan:
                a, b = (int(x) for x in phan.split("-", 1))
                ra.extend(range(a, b + 1) if b >= a else [a, b])
            elif phan.isdigit():
                ra.append(int(phan))
    return ra


def trich(study: str, dong: Sequence[str]) -> MoHinh:
    """Mô hình nội dung từ các dòng của đề cương nộp (không đọc tệp nào khác)."""
    cac_muc = GB.doc_muc(dong)
    mh = MoHinh(study)
    tt = _thong_tin_chung(dong, cac_muc)
    ten = _lay_tt(tt, "tên đề tài")
    if not ten:
        dau = next((m for m in cac_muc if m.cap == 2), None)
        ten = dau.ten if dau else ""
    mh.ten_de_tai = ten
    mh.chu_nhiem = _lay_tt(tt, "chủ nhiệm")
    mh.don_vi = _lay_tt(tt, "đơn vị chủ trì", "đơn vị thực hiện")
    mh.thoi_gian = _lay_tt(tt, "thời gian")
    if mh.thoi_gian:
        sau = mh.thoi_gian[mh.thoi_gian.lower().find("thực hiện"):] if "thực hiện" in mh.thoi_gian.lower() else ""
        k = _KHOANG_THANG_RE.search(sau) or _KHOANG_THANG_RE.search(mh.thoi_gian)
        if k:
            mh.thang = (f"{int(k.group(1)):02d}/{k.group(2)}", f"{int(k.group(3)):02d}/{k.group(4)}")
    mh.kinh_phi = _lay_tt(tt, "kinh phí")
    mh.tu_co = bool(re.search(r"tự túc|tự chi trả|tự có", mh.kinh_phi, re.IGNORECASE))
    mh.muc_tieu = _muc_tieu(dong, cac_muc)
    if not mh.muc_tieu:
        mh.canh_bao.append("không tìm thấy danh sách mục tiêu trong đề cương — mục 13 để trống")
    elif len(mh.muc_tieu) > 2:
        mh.canh_bao.append(f"đề tài có {len(mh.muc_tieu)} mục tiêu — hướng dẫn chung khuyên tối đa 2 mục tiêu cho đề "
                           "tài cấp bệnh viện (chủ nhiệm cân nhắc, máy không gộp)")
    if mh.thang:
        tu_t, tu_n = (int(x) for x in mh.thang[0].split("/"))
        den_t, den_n = (int(x) for x in mh.thang[1].split("/"))
        so = (den_n - tu_n) * 12 + den_t - tu_t + 1
        if so > 18:
            mh.canh_bao.append(f"thời gian thực hiện khoảng {so} tháng (tính cả tháng đầu và cuối) — hướng dẫn chung "
                               "nêu đề tài cấp bệnh viện thường 18 tháng")
    # 15 — tổng quan: đoạn văn của chương tổng quan trừ mục khoảng trống (15.2) và mục chiến lược tìm kiếm
    tq = _chuong(cac_muc, r"tổng quan")
    kt = GB.tim_muc(cac_muc, r"khoảng trống")
    if tq is not None:
        con = _con(cac_muc, tq)
        bo = [m for m in con if re.search(r"khoảng trống|chiến lược tìm", GB._chuan(m.ten))]
        theo_muc: Optional[bool] = None  # tên mục con nói rõ phạm vi ⇒ thắng luật từ khoá của từng đoạn
        for d in doan_cua_muc(dong, tq, bo, bang=False):
            if d.loai == "tieu_de":
                t = GB._chuan(d.van)
                theo_muc = (True if re.search(r"việt nam|trong nước|bộ y tế", t) else
                            False if re.search(r"thế giới|quốc tế|nước ngoài|ngoài nước", t) else None)
                continue
            trong = theo_muc if theo_muc is not None else bool(_TRONG_NUOC_RE.search(d.van))
            (mh.trong_nuoc if trong else mh.ngoai_nuoc).append(d)
        mh.nguon["15.1"] = f"chương tổng quan, dòng {tq.dong}–{tq.het}"
    if kt is not None:
        mh.luan_giai = [d for d in doan_cua_muc(dong, kt, bang=False)
                        if d.loai != "tieu_de" and not re.match(r"\*\*Chiến lược tìm", d.van)]
        mh.dong_gop = [d for d in mh.luan_giai if re.search(r"đóng góp", d.van, re.IGNORECASE)]
        mh.nguon["15.2"] = f"{kt.nhan}, dòng {kt.dong}–{kt.het}"
    # 17 — chương đối tượng và phương pháp, theo từng mục con
    pp = _chuong(cac_muc, r"đối tượng và phương pháp")
    if pp is not None:
        for m in _con(cac_muc, pp):
            mh.phuong_phap.append((m.ten, doan_cua_muc(dong, m)))
        mh.nguon["17"] = f"chương đối tượng và phương pháp, dòng {pp.dong}–{pp.het}"
    else:
        mh.canh_bao.append("không tìm thấy chương đối tượng và phương pháp — mục 17 để trống")
    # 16 — tài liệu được trích trong các phần TM chép lại
    tltk = _tltk(dong)
    chep = [d.van for d in mh.ngoai_nuoc + mh.trong_nuoc + mh.luan_giai] + [
        d.van for _t, ds in mh.phuong_phap for d in ds]
    so = sorted({s for v in chep for s in _so_trich(v)})
    mh.tltk = [(s, tltk[s]) for s in so if s in tltk]
    thieu = [s for s in so if s not in tltk]
    if thieu:
        mh.canh_bao.append(f"trích dẫn [{', '.join(map(str, thieu[:8]))}] không có trong danh mục tài liệu tham khảo")
    # 12 — vai trò nhân lực
    nl = GB.tim_muc(cac_muc, r"^nhân lực")
    if nl is not None:
        dau, hang = _bang_dau(dong, nl)
        if hang:
            mh.vai_tro = [o[0] for _s, o in hang if o and _co(o[0])]
        else:
            for d in doan_cua_muc(dong, nl, bang=False):  # văn xuôi «Vai trò: nhiệm vụ.» — có thể nhiều câu một đoạn
                for cau in GB.tach_cau(d.van):
                    m = re.match(r"^(?:\*\*)?([^:*]{3,60}?)(?:\*\*)?\s*:", cau)
                    if m:
                        mh.vai_tro.append(m.group(1).split(" (")[0].strip())
    # 21 — tiến độ: bảng của mục tiến độ; không có bảng ⇒ các bước của quy trình nghiên cứu
    td = GB.tim_muc(cac_muc, r"^tiến độ")
    dau, hang = _bang_dau(dong, td) if td is not None else ([], [])
    if hang:
        k_nd = _cot(dau, "nội dung", "công việc")
        k_tg = _cot(dau, "thời gian")
        k_sp = _cot(dau, "sản phẩm", "kết quả")
        for _s, o in hang:
            def _x(k: Optional[int], o: List[str] = o) -> str:
                return o[k] if k is not None and k < len(o) else ""
            mh.tien_do.append((_x(k_nd), _x(k_sp), _x(k_tg)))
        mh.nguon["21"] = f"{td.nhan}, dòng {td.dong}–{td.het}"
    else:
        qt = GB.tim_muc(cac_muc, r"^quy trình nghiên cứu")
        if qt is not None:
            for d in doan_cua_muc(dong, qt, bang=False):
                if d.loai == "ds":
                    tg = re.search(r"\(([^()]*\d[^()]*)\)\.?\s*$", d.van)
                    mh.tien_do.append((d.van, "", tg.group(1) if tg else ""))
            mh.nguon["21"] = f"{qt.nhan} (các bước), dòng {qt.dong}–{qt.het}"
    if not mh.tien_do:
        mh.canh_bao.append("không tìm thấy bảng tiến độ hay các bước quy trình — mục 21 để trống")
    # 22–25 — sản phẩm, phổ biến
    pb = GB.tim_muc(cac_muc, r"phổ biến")
    if pb is not None:
        mh.pho_bien = [d for d in doan_cua_muc(dong, pb, bang=False) if d.loai in ("ds", "doan")]
        mh.san_pham_bai_bao = [d.van for d in mh.pho_bien if re.search(r"bài báo|công bố trên", d.van, re.I)]
    sp = {x for _nd, x, _tg in mh.tien_do for x in re.split(r"[;,]\s*", x) if x}
    mh.san_pham_khac = sorted({x.strip() for x in sp if re.search(r"báo cáo|cơ sở dữ liệu|bộ câu hỏi|phiếu", x, re.I)})
    kp = GB.tim_muc(cac_muc, r"kinh phí")
    if kp is not None:
        dau, hang = _bang_dau(dong, kp)
        k_nd = _cot(dau, "nội dung", "khoản chi")
        mh.du_tru = [o[k_nd] for _s, o in hang if k_nd is not None and k_nd < len(o) and _co(o[k_nd])
                     and "tổng" not in GB._chuan(o[k_nd])]
    return mh


# ── Bản xem Markdown + danh mục ──────────────────────────────────────────────────────────────────────────────────────

def _ds(doan: Sequence[Doan]) -> List[str]:
    return [f"- {d.van}" if d.loai in ("ds", "bang") else (f"**{d.van}**" if d.loai == "tieu_de" else d.van)
            for d in doan] or [CHAM]


def ten_ngan_don_vi(don_vi: str) -> str:
    """«Khoa Khám bệnh C1a, Trung tâm …, Bệnh viện Quân y 175, …» ⇒ «Khoa Khám bệnh C1a» (phần trước dấu phẩy đầu)."""
    return don_vi.split(",")[0].strip() if don_vi else ""


def render_tm(mh: MoHinh) -> str:
    tg = f"Từ tháng {mh.thang[0]} đến tháng {mh.thang[1]}" if mh.thang else f"Từ tháng {CHAM} đến tháng {CHAM}"
    out = ["# THUYẾT MINH ĐỀ TÀI KHOA HỌC VÀ CÔNG NGHỆ CẤP BỆNH VIỆN", "",
           "*Mẫu DTCS-DKCT.02-TM — bản điền sẵn từ đề cương nộp hiện hành để đối chiếu với tệp Word cùng tên. Mọi "
           "đoạn nội dung là nguyên văn đề cương; ô «………» do chủ nhiệm tự điền (thông tin cá nhân, số tiền, các lựa "
           "chọn).*", "",
           f"*{LOI_DAN}*", "", "## I. THÔNG TIN CHUNG VỀ ĐỀ TÀI", "",
           f"**1. Tên đề tài:** {mh.ten_de_tai or CHAM}", "",
           f"**2. Thời gian thực hiện:** {CHAM} tháng ({tg})", "", "**3. Cấp quản lý:** Cấp cơ sở", "",
           f"**4. Tổng kinh phí thực hiện:** {CHAM} triệu đồng"
           + (f"; nguồn: Tự có (đề cương: “{mh.kinh_phi}”)" if mh.tu_co else ""), "",
           f"**5. Đề nghị phương thức khoán chi:** {CHAM} (chủ nhiệm chọn)", "",
           f"**6. Loại đề tài:** {CHAM} (chủ nhiệm chọn)", "", "**7. Lĩnh vực:** [x] Y, dược", "",
           f"**8. Chủ nhiệm đề tài:** {mh.chu_nhiem or CHAM} — số định danh, ngày sinh, giới tính, học hàm học vị, "
           "chức danh, cấp bậc, chức vụ, điện thoại, e-mail: chủ nhiệm tự điền.", "",
           f"**9. Thư ký khoa học của đề tài:** {CHAM} (tự điền)", "",
           f"**10. Đơn vị chủ trì đề tài:** {mh.don_vi or CHAM}; thủ trưởng đơn vị: {CHAM}; đơn vị chủ quản: Bệnh viện "
           "Quân y 175", "", f"**11. Các đơn vị phối hợp chính:** {CHAM}", "",
           "**12. Thành viên thực hiện đề tài**", "",
           "| TT | Họ và tên, học hàm, học vị | Chức danh thực hiện đề tài | Tổ chức công tác |", "|---|---|---|---|"]
    out += [f"| {i} | {CHAM} | {v} | {CHAM} |" for i, v in enumerate(mh.vai_tro or ["Chủ nhiệm đề tài"], 1)]
    out += ["", "## II. MỤC TIÊU, NỘI DUNG VÀ PHƯƠNG ÁN TỔ CHỨC THỰC HIỆN ĐỀ TÀI", "",
            "**13. Mục tiêu của đề tài**", ""]
    out += [f"- Mục tiêu {i}: {d.van}" for i, d in enumerate(mh.muc_tieu, 1)] or [CHAM]
    out += ["", f"**14. Tình trạng của đề tài:** {CHAM} (chủ nhiệm chọn: Mới / Kế tiếp …)", "",
            "**15.1. Đánh giá tổng quan tình hình nghiên cứu** (tách đoạn ngoài/trong nước theo tên mục và từ khoá — "
            "chủ nhiệm rà lại)", "", "*Ngoài nước*", ""] + _ds(mh.ngoai_nuoc)
    out += ["", "*Trong nước*", ""] + _ds(mh.trong_nuoc)
    out += ["", "**15.2. Luận giải về những nội dung cần nghiên cứu**", ""] + _ds(mh.luan_giai)
    out += ["", "**16. Danh mục công trình, tài liệu đã trích dẫn**", ""]
    out += [f"{s}. {v}" for s, v in mh.tltk] or [CHAM]
    out += ["", "**17. Nội dung nghiên cứu và phương án thực hiện**", ""]
    out += [f"- Nội dung {i}: {d.van}" for i, d in enumerate(mh.muc_tieu, 1)] + [""]
    for ten, ds in mh.phuong_phap:
        out += [f"*{ten}*", ""] + _ds(ds) + [""]
    out += [f"**18. Phương án phối hợp:** {CHAM}", "", f"**19. Hợp tác quốc tế:** {CHAM}", "",
            f"**20. Thuê chuyên gia:** {CHAM}", "", "**21. Tiến độ thực hiện**", "",
            "| TT | Nội dung, công việc | Kết quả phải đạt | Thời gian | Cá nhân, đơn vị chủ trì | Dự kiến kinh phí |",
            "|---|---|---|---|---|---|"]
    out += [f"| {i} | {nd} | {kq or CHAM} | {tgian or CHAM} | {CHAM} | {CHAM} |"
            for i, (nd, kq, tgian) in enumerate(mh.tien_do, 1)]
    out += ["", "## III. SẢN PHẨM KH&CN CỦA ĐỀ TÀI", "", "**22. Sản phẩm** — Dạng I (công bố khoa học):", ""]
    out += [f"- {x} — yêu cầu khoa học cần đạt: {CHAM}" for x in mh.san_pham_bai_bao] or [CHAM]
    out += ["", "Dạng II:", "", f"- Báo cáo tổng hợp kết quả nghiên cứu đề tài — yêu cầu khoa học cần đạt: {CHAM}"]
    out += [f"- {x} — yêu cầu khoa học cần đạt: {CHAM}" for x in mh.san_pham_khac]
    out += ["", f"**22.1–22.3:** {CHAM}", "", "**23–24. Khả năng ứng dụng, phạm vi và địa chỉ ứng dụng**", ""]
    out += _ds(mh.pho_bien)
    out += ["", "**25. Tác động và lợi ích**", ""] + _ds(mh.dong_gop)
    out += ["", f"**26. Phương án trang bị thiết bị:** {CHAM}", "", "## V. NHU CẦU KINH PHÍ", "",
            f"**27.** Tổng kinh phí {CHAM} triệu đồng" + ("; nguồn: Tự có." if mh.tu_co else "."), ""]
    if mh.du_tru:
        out += ["*Căn cứ dự toán (khoản chi trong bảng dự trù kinh phí của đề cương):*", ""]
        out += [f"- {x}" for x in mh.du_tru]
    return "\n".join(out).rstrip() + "\n"


def render_danh_muc(mh: MoHinh, co_word: Dict[str, str]) -> str:
    out = ["# DANH MỤC HỒ SƠ ĐĂNG KÝ ĐỀ TÀI CẤP BỆNH VIỆN (BỘ MẪU BVQY175)", "",
           f"Đề tài: {mh.ten_de_tai or CHAM}", "",
           "| Mẫu | Tệp | Trạng thái |", "|---|---|---|",
           f"| DTCS-DKCT.01-DK (đơn đăng ký) | `{TEN_RA['dk'].format(study=mh.study)}` | "
           f"{co_word.get('dk', 'chưa dựng')} |",
           f"| DTCS-DKCT.02-TM (thuyết minh) | `{TEN_RA['tm'].format(study=mh.study)}` | "
           f"{co_word.get('tm', 'chưa dựng')} |",
           "| DTCS-DKCT.03-LLKH (lý lịch khoa học) | — | máy KHÔNG dựng: toàn mục thông tin cá nhân |", "",
           "## Ai phải nộp lý lịch khoa học (mẫu 03-LLKH)", "",
           "Theo đơn đăng ký: cá nhân đăng ký chủ nhiệm và các thành viên thực hiện chính. Vai trò trong đề cương:", ""]
    out += [f"- {v}" for v in (mh.vai_tro or ["Chủ nhiệm đề tài"])]
    out += ["", "## Ô chủ nhiệm tự điền (máy để dòng chấm)", "",
            "- Mục 2: số tháng; mục 4, 27 và phụ lục dự toán: số tiền; mục 5, 6, 14: các lựa chọn.",
            "- Mục 8, 9: thông tin cá nhân của chủ nhiệm và thư ký khoa học (máy không giữ số định danh, ngày sinh, "
            "điện thoại, e-mail).",
            "- Mục 10: họ tên thủ trưởng đơn vị; mục 11, 18–20: đơn vị phối hợp, hợp tác quốc tế, thuê chuyên gia "
            "(đề cương không nêu — ghi «Không có» nếu đúng).",
            "- Mục 12: họ tên và tổ chức công tác của từng thành viên; mục 21: cá nhân chủ trì và kinh phí từng "
            "công việc.",
            "- Mục 22: yêu cầu khoa học cần đạt của từng sản phẩm; 22.1–22.3, 23.1–23.3, 25.1, 26: theo đơn vị.",
            "- Đơn đăng ký: học hàm, học vị, cấp bậc, chức vụ; ngày tháng; chữ ký chủ nhiệm và chỉ huy đơn vị.", "",
            "## Nguồn đã chép từ đề cương nộp", ""]
    out += [f"- Mục {k}: {v}" for k, v in sorted(mh.nguon.items())] or ["- (không có)"]
    if mh.canh_bao:
        out += ["", "## Cảnh báo", ""] + [f"- ⚠ {c}." for c in mh.canh_bao]
    out += ["", f"*{LOI_DAN}*"]
    return "\n".join(out) + "\n"


# ── Điền tệp mẫu Word ────────────────────────────────────────────────────────────────────────────────────────────────

def tim_thu_muc_mau() -> Optional[Path]:
    """Thư mục bộ mẫu DTCS (ngoài git): biến EBM_MAU_DTCS_BVQY175 → cạnh thư mục bộ mẫu HĐĐ mà `ho_so_hdd_bvqy175`
    dò được (cùng «Đề tài NCKH/») → `<cha-của-«Claude AI»>/Đề tài NCKH/Mau DTCS BV175/docx`. Không đường dẫn cứng."""
    bien = os.environ.get("EBM_MAU_DTCS_BVQY175", "").strip()
    if bien and Path(bien).expanduser().is_dir():
        return Path(bien).expanduser()
    duoi = Path("Mau DTCS BV175") / "docx"
    ung: List[Path] = []
    try:
        import ho_so_hdd_bvqy175 as HDD  # noqa: PLC0415

        hdd = HDD.tim_thu_muc_mau()
        if hdd is not None:
            ung.append(hdd.parent.parent / duoi)
    except Exception:  # noqa: BLE001 — dò vị trí không được làm hỏng lệnh
        pass
    for ancestor in Path(__file__).resolve().parents:
        if ancestor.name == "medical-ebm-automation":
            ung += [ancestor.parent.parent / "Đề tài NCKH" / duoi, ancestor.parent / "Đề tài NCKH" / duoi]
            break
    return next((p for p in ung if p.is_dir()), None)


def _danh_dau(p: Any, thu_tu: int) -> bool:
    """Đánh dấu ô chọn (trường biểu mẫu FORMCHECKBOX) thứ `thu_tu` (đếm từ 0) trong đoạn p."""
    from docx.oxml.ns import qn  # noqa: PLC0415

    hop = p._p.findall(".//" + qn("w:checkBox"))
    if thu_tu >= len(hop):
        return False
    mac = hop[thu_tu].find(qn("w:default"))
    if mac is None:
        from docx.oxml import OxmlElement  # noqa: PLC0415

        mac = OxmlElement("w:default")
        hop[thu_tu].append(mac)
    mac.set(qn("w:val"), "1")
    return True


_DAM_RE = re.compile(r"(\*\*[^*]+\*\*)")
_SO_MUC_CU_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")


def _ghi(H: Any, p: Any, text: str, dam: bool = False) -> None:
    """Ghi `text` vào đoạn p (xoá chữ cũ): «**…**» của Markdown thành chữ đậm thật, không để dấu sao trong Word."""
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    for manh in _DAM_RE.split(text):
        if manh:
            dam_manh = dam or (manh.startswith("**") and manh.endswith("**"))
            H._run(p, manh.strip("*") if manh.startswith("**") else manh, bold=dam_manh or None)


def _chen(H: Any, neo: Any, text: str, dam: bool = False) -> Any:
    q = H.chen_sau(neo)
    _ghi(H, q, text, dam)
    return q


def _ghi_khoi(H: Any, ps: List[Any], i: int, van: Sequence[str], toi_da: int = 12) -> None:
    """Thay các đoạn dòng chấm liền sau ps[i] bằng `van` (mỗi chuỗi một đoạn); thừa dòng chấm ⇒ xoá."""
    cham = []
    for j in range(i + 1, min(i + 1 + toi_da, len(ps))):
        if _CHAM_RE.match(ps[j].text) and ps[j].text.strip():
            cham.append(ps[j])
        else:
            break
    if not van:
        return
    neo = cham[0] if cham else H.chen_sau(ps[i])
    _ghi(H, neo, van[0])
    for t in reversed(van[1:]):
        _chen(H, neo, t)
    for p in cham[1:]:
        H.xoa(p)


def _van(doan: Sequence[Doan]) -> List[str]:
    return [("• " + d.van) if d.loai in ("ds", "bang") else d.van for d in doan]


def _dien_bang(tb: Any, tu_hang: int, hang: Sequence[Sequence[str]]) -> None:
    """Ghi các hàng từ `tu_hang`; thiếu hàng ⇒ thêm; thừa hàng mẫu ⇒ xoá."""
    while len(tb.rows) < tu_hang + len(hang):
        tb.add_row()
    for k, o in enumerate(hang):
        r = tb.rows[tu_hang + k]
        for c, x in enumerate(o[:len(r.cells)]):
            r.cells[c].text = x
    for r in list(tb.rows)[tu_hang + len(hang):]:
        r._tr.getparent().remove(r._tr)


def dien_tm(mau: Path, ra: Path, mh: MoHinh) -> List[str]:
    """Điền tệp mẫu 02-TM; trả về danh sách mốc không thấy trong mẫu (báo, không sập)."""
    import docx  # noqa: PLC0415
    import ho_so_hdd_bvqy175 as H  # noqa: PLC0415

    doc = docx.Document(str(mau))
    thieu: List[str] = []

    def _tim(bat_dau: str) -> Optional[int]:
        i = H.tim(doc.paragraphs, bat_dau)
        if i is None:
            thieu.append(bat_dau)
        return i

    ps = doc.paragraphs
    i = _tim("1. Tên đề tài")
    if i is not None and mh.ten_de_tai:
        _ghi_khoi(H, ps, i, [mh.ten_de_tai])
    ps = doc.paragraphs
    i = _tim("(Từ tháng")
    if i is not None and mh.thang:
        H.dat_text(ps[i], f"(Từ tháng {mh.thang[0]} đến tháng {mh.thang[1]})", giu_dinh_dang=True)
    i = _tim("7. Lĩnh vực")
    if i is not None:
        j = H.tim_chua(ps, "Y, dược", tu=i)
        if j is None or not _danh_dau(ps[j], 1):
            thieu.append("ô Y, dược")
    i = _tim("8. Chủ nhiệm đề tài")
    if i is not None and mh.chu_nhiem:
        j = H.tim(ps, "Họ và tên", tu=i)
        if j is not None:
            ten = re.split(r"\s+[–-]\s+", mh.chu_nhiem)[0]
            H.dat_text(ps[j], re.sub(r"^Họ và tên:\s*\.+", f"Họ và tên: {ten} ", ps[j].text), giu_dinh_dang=True)
        k = H.tim(ps, "Tên đơn vị đang công tác", tu=i)
        if k is not None and mh.don_vi:
            H.dat_text(ps[k], f"Tên đơn vị đang công tác: {ten_ngan_don_vi(mh.don_vi)}/Bệnh viện Quân y 175",
                       giu_dinh_dang=True)
    i = _tim("Tên đơn vị chủ trì thực hiện đề tài")
    if i is not None and mh.don_vi:
        H.dat_text(ps[i], f"Tên đơn vị chủ trì thực hiện đề tài: {mh.don_vi}", giu_dinh_dang=True)
    for so, van in (("13. Mục tiêu", [f"Mục tiêu {k}: {d.van}" for k, d in enumerate(mh.muc_tieu, 1)]),
                    ("Ngoài nước", _van(mh.ngoai_nuoc)), ("Trong nước", _van(mh.trong_nuoc)),
                    ("(Trên cơ sở đánh giá", _van(mh.luan_giai)),
                    ("(Tên công trình, tác giả", [f"{s}. {v}" for s, v in mh.tltk])):
        ps = doc.paragraphs
        i = _tim(so)
        if i is not None:
            _ghi_khoi(H, ps, i, van)
    ps = doc.paragraphs
    i = _tim("- Nội dung thuê chuyên gia")
    if i is not None:
        van: List[Tuple[str, bool]] = [(f"Nội dung {k}: {d.van}", False) for k, d in enumerate(mh.muc_tieu, 1)]
        for ten, ds in mh.phuong_phap:
            van.append((ten, True))  # tên mục cấp 2 của bộ đọc đề mục đã bỏ số; cấp 3 bỏ số ở dòng dưới
            van += [(_SO_MUC_CU_RE.sub("", d.van), d.loai == "tieu_de") if d.loai == "tieu_de" else (t, False)
                    for d, t in zip(ds, _van(ds))]
        j = H.tim(ps, "18. Phương án phối hợp", tu=i)
        for p in ps[i + 1:j if j is not None else i + 13]:
            H.xoa(p)
        neo = ps[i]
        for t, dam in reversed(van):
            _chen(H, neo, t, dam)
    # bảng: 12 thành viên · 21 tiến độ · 22 sản phẩm Dạng I/II · 4 nguồn kinh phí
    for tb in doc.tables:
        dau = " | ".join(c.text.strip() for c in tb.rows[0].cells)
        if dau.startswith("TT | Họ và tên") and "Chức danh thực hiện" in dau:
            _dien_bang(tb, 1, [[str(k), "", v, ""] for k, v in enumerate(mh.vai_tro or ["Chủ nhiệm đề tài"], 1)])
        elif "Các nội dung, công việc" in dau and mh.tien_do:
            _dien_bang(tb, 2, [[str(k), nd, kq, tg, "", ""] for k, (nd, kq, tg) in enumerate(mh.tien_do, 1)])
        elif "Dự kiến nơi công bố" in dau and mh.san_pham_bai_bao:
            _dien_bang(tb, 2, [[str(k), x, "", "", ""] for k, x in enumerate(mh.san_pham_bai_bao, 1)])
        elif dau.startswith("TT | Tên sản phẩm | Yêu cầu khoa học") and len(tb.columns) == 4 and "Dạng II" in \
                _doan_truoc_bang(doc, tb):
            sp = ["Báo cáo tổng hợp kết quả nghiên cứu đề tài"] + mh.san_pham_khac
            _dien_bang(tb, 2, [[str(k), x, "", ""] for k, x in enumerate(sp, 1)])
        elif dau.startswith("Nguồn | Kinh phí") and mh.tu_co:
            for r in tb.rows:
                if r.cells[0].text.strip() == "Tự có":
                    r.cells[1].text = "Toàn bộ (đề cương: tự túc)"
    chuyen_giao = [d for d in mh.pho_bien if re.search(r"báo cáo|trình bày|chuyển giao|hội nghị", d.van, re.I)]
    dia_chi = [d for d in mh.pho_bien if re.search(r"Khoa|Trung tâm|Bệnh viện|Phòng|Ban Giám đốc", d.van)]
    for so, van in (("23.4", _van(chuyen_giao or mh.pho_bien)), ("24. Phạm vi", _van(dia_chi or mh.pho_bien)),
                    ("25.2", _van(mh.dong_gop)), ("25.3", _van(dia_chi or mh.dong_gop))):
        ps = doc.paragraphs
        i = _tim(so)
        if i is not None and van:
            j = i + 1 if i + 1 < len(ps) and ps[i + 1].text.strip().startswith("(") else i
            _ghi_khoi(H, ps, j, van)
    ra.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(ra))
    return thieu


def _doan_truoc_bang(doc: Any, tb: Any) -> str:
    """Chữ của đoạn đứng ngay trước bảng (để phân biệt bảng Dạng II với Dạng IV cùng khuôn cột)."""
    truoc = tb._tbl.getprevious()
    while truoc is not None and not truoc.tag.endswith("}p"):
        truoc = truoc.getprevious()
    return "".join(t.text or "" for t in truoc.iter() if t.tag.endswith("}t")) if truoc is not None else ""


def dien_dk(mau: Path, ra: Path, mh: MoHinh) -> List[str]:
    """Điền tệp mẫu 01-DK (đơn đăng ký)."""
    import docx  # noqa: PLC0415
    import ho_so_hdd_bvqy175 as H  # noqa: PLC0415

    doc = docx.Document(str(mau))
    thieu: List[str] = []
    ngan = ten_ngan_don_vi(mh.don_vi)
    if ngan and doc.tables:
        for p in doc.tables[0].rows[0].cells[0].paragraphs:
            if p.text.strip() == "…":
                H.dat_text(p, " ".join(w if re.search(r"\d", w) else w.upper() for w in ngan.split()),
                           giu_dinh_dang=True)
    ps = doc.paragraphs
    i = H.tim_chua(ps, "kính đề nghị Phòng Khoa học")
    if i is None:
        thieu.append("…1 kính đề nghị")
    elif ngan:
        for r in ps[i].runs:
            if r.text.startswith("…"):
                r.text = ngan + r.text[1:]
                break
    for bat_dau, van in (("(Tên Khoa, phòng Ban", mh.don_vi),
                         ("(Họ tên, học hàm", (re.split(r"\s+[–-]\s+", mh.chu_nhiem)[0] + "; học hàm, cấp bậc, chức "
                                               f"vụ: {CHAM}") if mh.chu_nhiem else "")):
        ps = doc.paragraphs
        i = H.tim(ps, bat_dau)
        if i is None:
            thieu.append(bat_dau)
        elif van:
            H.chen_sau(ps[i], van)
    ps = doc.paragraphs
    i = H.tim(ps, "Đăng ký chủ trì thực hiện nhiệm vụ")
    if i is None:
        thieu.append("Đăng ký chủ trì thực hiện nhiệm vụ")
    elif mh.ten_de_tai:
        _ghi_khoi(H, ps, i, [f"“{mh.ten_de_tai}”"])
    ra.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(ra))
    return thieu


# ── Điều phối ────────────────────────────────────────────────────────────────────────────────────────────────────────

def _chuoi_chen(mh: MoHinh) -> List[str]:
    """Mọi chuỗi máy chèn vào mẫu — để quét mẫu định danh."""
    ds = [mh.ten_de_tai, mh.chu_nhiem, mh.don_vi, mh.kinh_phi] + mh.vai_tro + mh.du_tru + mh.san_pham_bai_bao
    ds += [d.van for d in mh.muc_tieu + mh.ngoai_nuoc + mh.trong_nuoc + mh.luan_giai + mh.pho_bien + mh.dong_gop]
    ds += [v for _s, v in mh.tltk] + [d.van for _t, x in mh.phuong_phap for d in x]
    ds += [x for hang in mh.tien_do for x in hang]
    return [x for x in ds if x]


def _sao_luu(p: Path) -> Optional[Path]:
    if not p.is_file():
        return None
    d = p.parent / "_sao_luu"
    d.mkdir(parents=True, exist_ok=True)
    dich = d / f"{p.name}.bak-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    shutil.copy2(p, dich)
    return dich


def chay(study: str, out_dir: Path, ghi: bool = False, thu_muc_ra: Optional[Path] = None,
         thu_muc_mau: Optional[Path] = None) -> Dict[str, Any]:
    p_dc = out_dir / TEN_DE_CUONG.format(study=study)
    if not p_dc.is_file():
        return {"ma": 2, "loi": f"thiếu đề cương nộp {p_dc.name}"}
    mh = trich(study, p_dc.read_text(encoding="utf-8").splitlines())
    tm_md = render_tm(mh)
    pii = GB.quet_pii("\n".join(_chuoi_chen(mh)))
    kq: Dict[str, Any] = {"ma": 0, "study": study, "ten_de_tai": mh.ten_de_tai, "muc_tieu": len(mh.muc_tieu),
                          "tong_quan": {"ngoai_nuoc": len(mh.ngoai_nuoc), "trong_nuoc": len(mh.trong_nuoc)},
                          "phuong_phap_muc": len(mh.phuong_phap), "tltk": len(mh.tltk), "tien_do": len(mh.tien_do),
                          "vai_tro": len(mh.vai_tro), "canh_bao": mh.canh_bao, "pii": pii, "ghi": ghi,
                          "tm_md": tm_md}
    if pii:
        kq["ma"] = 3
        return kq
    dich = (thu_muc_ra or out_dir / THU_MUC_RA)
    kq["dich"] = dich.as_posix()
    if not ghi:
        return kq
    dich.mkdir(parents=True, exist_ok=True)
    trang: Dict[str, str] = {}
    mau_dir = thu_muc_mau or tim_thu_muc_mau()
    kq["sao_luu"] = []
    for loai, ham in (("dk", dien_dk), ("tm", dien_tm)):
        mau = (mau_dir / MAU[loai]) if mau_dir else None
        ra = dich / TEN_RA[loai].format(study=study)
        if mau is None or not mau.is_file():
            trang[loai] = "chưa dựng — không tìm thấy tệp mẫu (đặt EBM_MAU_DTCS_BVQY175)"
            kq["ma"] = 1
            continue
        try:
            bk = _sao_luu(ra)
            thieu = ham(mau, ra, mh)
        except ImportError:
            trang[loai] = "chưa dựng — thiếu python-docx"
            kq["ma"] = 1
            continue
        if bk:
            kq["sao_luu"].append(bk.as_posix())
        trang[loai] = "đã điền sẵn" + (f"; mốc không thấy trong mẫu: {', '.join(thieu)}" if thieu else "")
    for loai, noi_dung in (("tm_md", tm_md), ("danh_muc", render_danh_muc(mh, trang))):
        p = dich / TEN_RA[loai].format(study=study)
        bk = _sao_luu(p)
        if bk:
            kq["sao_luu"].append(bk.as_posix())
        p.write_text(noi_dung, encoding="utf-8", newline="\n")
    kq["word"] = trang
    return kq


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hồ sơ đăng ký đề tài cấp bệnh viện theo bộ mẫu BVQY175 (DK, TM).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--exports-root", type=Path, default=BASE / "exports")
    ap.add_argument("--ghi", action="store_true", help="ghi tệp (mặc định CHẠY KHÔ)")
    ap.add_argument("--thu-muc-ra", type=Path, help="ghi vào thư mục này thay vì exports/<mã>/ho_so_dtcs/")
    ap.add_argument("--thu-muc-mau", type=Path, help="thư mục chứa tệp mẫu .docx (mặc định tự dò)")
    ap.add_argument("--xem", action="store_true", help="in bản xem thuyết minh")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print(f"❌ mã đề tài không hợp lệ: {a.study!r}", file=sys.stderr)
        return 3
    kq = chay(a.study, a.exports_root / a.study, a.ghi, a.thu_muc_ra, a.thu_muc_mau)
    if "loi" in kq:
        print(f"❌ {kq['loi']}", file=sys.stderr)
        return kq["ma"]
    if a.xem:
        print(kq["tm_md"])
    if a.json:
        print(json.dumps({k: v for k, v in kq.items() if k != "tm_md"}, ensure_ascii=False, indent=2))
        return kq["ma"]
    print(f"HỒ SƠ ĐĂNG KÝ ĐỀ TÀI (BỘ MẪU BVQY175) — {a.study}" + ("" if a.ghi else " (CHẠY KHÔ — chưa ghi gì)"))
    print(f"  Tên đề tài: {kq['ten_de_tai'] or '(không thấy)'}")
    print(f"  Thuyết minh: {kq['muc_tieu']} mục tiêu · tổng quan {kq['tong_quan']['ngoai_nuoc']} đoạn ngoài nước/"
          f"{kq['tong_quan']['trong_nuoc']} đoạn trong nước · {kq['phuong_phap_muc']} mục phương pháp · "
          f"{kq['tltk']} tài liệu · {kq['tien_do']} dòng tiến độ · {kq['vai_tro']} vai trò")
    for c in kq["canh_bao"]:
        print(f"  ⚠ {c}")
    if kq["pii"]:
        print(f"  🔴 Có mẫu định danh trong nội dung chèn: {'; '.join(kq['pii'][:5])} — KHÔNG ghi")
    for loai, t in (kq.get("word") or {}).items():
        print(f"  Word {loai.upper()}: {t}")
    print(("  Đã ghi vào: " if a.ghi and kq["ma"] != 3 else "  Sẽ ghi vào: ") + kq.get("dich", ""))
    if not a.ghi:
        print("  Ghi thật: thêm --ghi. Xem bản thuyết minh: --xem")
    print(f"  {LOI_DAN}")
    return kq["ma"]


if __name__ == "__main__":
    sys.exit(main())
