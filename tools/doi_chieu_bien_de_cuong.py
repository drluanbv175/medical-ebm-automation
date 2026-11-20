#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỐI CHIẾU BIẾN ↔ ĐỀ CƯƠNG — bộ biến máy (từ điển nhập liệu, biến phái sinh, đặc tả phân tích) phải ĐỒNG BỘ với đề
cương
và bộ biến đã duyệt, TRƯỚC khi sinh mẫu nhập, tiếp nhận dữ liệu và phân tích (15/11/2026).

Vì sao: bác sĩ 15/11/2026 — «Biến xác định không đúng, nhập liệu không đúng thì không thể phân tích được nên phải đảm
  bảo xác
định biến đúng đồng bộ với đề cương». Trước công cụ này không chỗ nào so bảng biến số của đề cương với từ điển máy:
lệch chỉ
lộ ra lúc phân tích (vd trường calc `du_tieu_chuan`/`bmi` của REDCap không có trong dữ liệu nhập Excel/SPSS; biến phái
sinh
thêm vào `_bien-phai-sinh.csv` mà bộ biến đã duyệt không có).

NGUỒN NGƯỜI DUYỆT (chuẩn — máy phải khớp nguồn này, không ngược lại):
  • đề cương nộp Hội đồng `DE_CUONG_NOP_HOI_DONG_<mã>.md`: bảng biến số có cột đầu «Mã biến» (vd Bảng E.1);
  • bộ biến G3 đã duyệt `G3_BO_BIEN_SO_<mã>.md`: bảng trường «Tên biến | Nhãn | Loại | Giá trị hợp lệ …» và bảng biến
    phái
    sinh «Tên | … | Định nghĩa / công thức …». Bảng do MÁY soạn (`tools/bang_bien_g3.py`, có dấu `<!-- BANG-BIEN-G3:`)
    chỉ là nguồn người duyệt khi PI đã ghi `gate_params.G3.bo_bien_so_duyet` gắn đúng nội dung (15/11/2026) — bản nháp
    chưa duyệt bị loại (`nguon_bi_loai`), không thì máy so với chính nó.
BẢN MÁY: `_bo-bien-rieng.csv` (nguồn duy nhất của G5) · `G5_REDCap_dictionary_<mã>.csv` · `_bien-phai-sinh.csv` ·
`_ma-thieu-theo-bien.csv` · `G6_DAC_TA_SAP.json`. Ánh xạ tên khác nhau có chủ đích: `_anh-xa-ten-bien.csv`
(ten_nguon,ten_may).

LUẬT (LỆCH = phải sửa trước khi nhập liệu/phân tích · CẦN XEM = người đối chiếu):
  V1 biến của nguồn người duyệt có trong bản máy (tên không phân biệt hoa thường; `ID` ≡ `record_id`); biến «tính
    toán» có
     công thức trong `_bien-phai-sinh.csv`.                                                                       [LỆCH]
  V2 mã giá trị biến phân loại khớp từ điển (đọc «1 = …; 2 = …», «1 = … … 5 = …», «1–9», «1, Có; 0, Không», mệnh đề «chỉ
     A3, A4 …»); mã có trong `_ma-thieu-theo-bien.csv` của biến (hoặc `*`) được miễn; khoảng số «3 – 20» so min/max.
     [LỆCH]
     Không đọc được mã ⇒ CẦN XEM (không đoán).
  V3 loại biến tương thích (định lượng ↔ ô số/ngày; phân loại ↔ chọn một/chọn nhiều).                            [CẦN
    XEM]
  V4 trường chỉ có ở từ điển máy (trừ `record_id` và ô «khác, ghi rõ» đi kèm một biến có trong nguồn).            [CẦN
    XEM]
  V5 biến phái sinh của `_bien-phai-sinh.csv` không có trong nguồn người duyệt ⇒ NGOÀI ĐỀ CƯƠNG.                 [LỆCH]
     Định nghĩa nguồn đặt cạnh công thức; số ngưỡng của định nghĩa không thấy trong công thức ⇒ CẦN XEM.
  V6 trường `calc` của từ điển: đường nhập Excel/SPSS KHÔNG tính calc ⇒ phải có biến phái sinh CÙNG TÊN.
    [LỆCH]
  V7 `_bo-bien-rieng.csv` ≡ `G5_REDCap_dictionary_<mã>.csv` (khi có cả hai).
    [LỆCH]
  V8 mọi biến dùng trong `G6_DAC_TA_SAP.json` (outcome, group, covariates, ty_le, cot_cum, loc…) có trong bản máy và đọc
     được từ dữ liệu nhập (không phải calc chưa có biến phái sinh).
     [LỆCH]

CHỈ ĐỌC — không sửa tệp nào; sửa là việc của người soạn đề cương/bộ biến (chủ nhiệm duyệt) hoặc người dựng từ điển.
Mã thoát: 0 không LỆCH · 1 có LỆCH · 2 không đo được (không có nguồn người duyệt nào, hoặc tệp hỏng) · 3 tham số sai.
Lệnh: python3 tools/doi_chieu_bien_de_cuong.py --study <mã> [--json] [--ghi]   (--ghi: DOI_CHIEU_BIEN_<mã>.md/.json)
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bang_bien_g3 as BB  # noqa: E402
import bien_phai_sinh as BPS  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402

CAN_KIEM = "Cần bác sĩ kiểm chứng."
LECH, XEM = "LECH", "CAN_XEM"
MA_OK, MA_LECH, MA_KHONG_DO, MA_THAM_SO = 0, 1, 2, 3
BI_DANH = {"id": "record_id"}
LOAI_CHON = ("radio", "dropdown", "checkbox", "yesno", "truefalse")


@dataclass
class BienNguon:
    """Một biến khai trong nguồn người duyệt."""

    ten: str
    nguon: str
    loai: str = ""
    ma_hoa: str = ""
    tinh_toan: bool = False
    dinh_nghia: str = ""


PV_NHAP, PV_PHAN_TICH = "nhap_lieu", "phan_tich"
# Phạm vi của lệch: biến TRƯỜNG sai/thiếu/sai mã ⇒ nhập liệu sai (chặn sinh mẫu + tiếp nhận); biến TÍNH TOÁN/đặc tả ⇒
# phân
# tích sai (chặn lúc tính biến phái sinh của G6) — nhập liệu không phụ thuộc biến phái sinh nên không chặn nhập vì
# chúng.
PHAM_VI = {
    "V1": PV_NHAP,
    "V2": PV_NHAP,
    "V3": PV_NHAP,
    "V4": PV_NHAP,
    "V7": PV_NHAP,
    "V1PS": PV_PHAN_TICH,
    "V5": PV_PHAN_TICH,
    "V6": PV_PHAN_TICH,
    "V8": PV_PHAN_TICH,
}


@dataclass
class PhatHien:
    muc: str  # LECH | CAN_XEM
    luat: str
    bien: str
    chi_tiet: str
    pham_vi: str = ""

    def __post_init__(self) -> None:
        self.pham_vi = self.pham_vi or PHAM_VI.get(self.luat, PV_NHAP)


@dataclass
class KetQua:
    study: str
    nguon_nguoi_duyet: list[str] = field(default_factory=list)
    ban_may: list[str] = field(default_factory=list)
    so_bien_nguon: int = 0
    phat_hien: list[PhatHien] = field(default_factory=list)
    khong_do_duoc: str | None = None
    dat_canh: list[dict] = field(default_factory=list)  # định nghĩa nguồn ↔ công thức (để người đối chiếu)
    nguon_bi_loai: list[str] = field(default_factory=list)  # bảng có mà KHÔNG tính là nguồn người duyệt (+ lý do)

    @property
    def so_lech(self) -> int:
        return sum(1 for p in self.phat_hien if p.muc == LECH)

    @property
    def trang_thai(self) -> str:
        if self.khong_do_duoc:
            return "KHONG_DO_DUOC"
        return "LECH" if self.so_lech else ("CAN_XEM" if self.phat_hien else "DONG_BO")

    def lech(self, pham_vi: str | None = None) -> list[PhatHien]:
        return [p for p in self.phat_hien if p.muc == LECH and (pham_vi is None or p.pham_vi == pham_vi)]

    def ma_thoat(self) -> int:
        return MA_KHONG_DO if self.khong_do_duoc else (MA_LECH if self.so_lech else MA_OK)

    def to_dict(self) -> dict:
        return {
            "study": self.study,
            "trang_thai": self.trang_thai,
            "so_lech": self.so_lech,
            "so_can_xem": len(self.phat_hien) - self.so_lech,
            "nguon_nguoi_duyet": self.nguon_nguoi_duyet,
            "nguon_bi_loai": self.nguon_bi_loai,
            "ban_may": self.ban_may,
            "so_bien_nguon": self.so_bien_nguon,
            "khong_do_duoc": self.khong_do_duoc,
            "phat_hien": [asdict(p) for p in self.phat_hien],
            "dat_canh": self.dat_canh,
            "ghi_chu": CAN_KIEM,
        }


# ─────────────────────────── đọc nguồn người duyệt ───────────────────────────


def _o(s: str) -> str:
    return s.strip().strip("`").strip()


def bang_md(chu: str) -> list[tuple[list[str], list[list[str]]]]:
    """Mọi bảng Markdown: (tiêu đề, các dòng). Bỏ dòng phân cách |---|."""
    ra, khoi = [], []
    for dong in chu.splitlines() + [""]:
        if dong.lstrip().startswith("|"):
            khoi.append(dong.strip())
            continue
        if len(khoi) >= 2:
            hang = [[_o(c) for c in d.strip("|").split("|")] for d in khoi]
            tieu_de, than = hang[0], [h for h in hang[1:] if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in h)]
            ra.append((tieu_de, than))
        khoi = []
    return ra


def mo_rong_ten(o: str) -> list[str]:
    """«A1–A6, B1–B8» ⇒ A1…A6, B1…B8 · «A_Mean … F_Mean» ⇒ A_Mean…F_Mean · «a, b» ⇒ a, b."""
    ra: list[str] = []
    for p in [x.strip().strip("`") for x in re.split(r",\s*", o) if x.strip()]:
        m = re.fullmatch(r"([A-Za-z_]+?)(\d+)\s*[–-]\s*\1?(\d+)", p)
        if m and int(m[2]) < int(m[3]):
            ra += [f"{m[1]}{i}" for i in range(int(m[2]), int(m[3]) + 1)]
            continue
        m = re.fullmatch(r"([A-Z])(_\w+)\s*(?:…|\.\.\.)\s*([A-Z])\2", p)
        if m and m[1] < m[3]:
            ra += [f"{chr(c)}{m[2]}" for c in range(ord(m[1]), ord(m[3]) + 1)]
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", p):
            ra.append(p)
    return ra


def doc_de_cuong(d: Path, study: str) -> tuple[list[BienNguon], str | None]:
    p = d / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    if not p.exists():
        return [], None
    ra: list[BienNguon] = []
    for td, than in bang_md(p.read_text(encoding="utf-8")):
        if not td or td[0].lower() != "mã biến" or len(td) < 4:
            continue
        for h in than:
            h = h + [""] * (5 - len(h))
            loai, ma_hoa, nguon = h[2], h[3], h[4]
            tt = "tính toán" in loai.lower() or nguon.lower().startswith("tính toán")
            for ten in mo_rong_ten(h[0]):
                ra.append(BienNguon(ten, f"đề cương ({p.name})", loai, ma_hoa, tt, h[1] + "; " + ma_hoa if tt else ""))
    return ra, (p.name if ra else None)


def doc_bo_bien_g3(d: Path, study: str) -> tuple[list[BienNguon], str | None]:
    p = d / f"G3_BO_BIEN_SO_{study}.md"
    if not p.exists():
        return [], None
    ra: list[BienNguon] = []
    chu = p.read_text(encoding="utf-8")
    if BB.DAU_MAY in chu:
        # Bảng MÁY soạn: chỉ đọc phần TÍNH DẤU (sau khung trạng thái) — bảng chèn vào tiêu đề/khung trạng thái không
        # được góp biến vào đối chiếu mà xác nhận PI vẫn còn hiệu lực (thẩm định #274, ĐỎ 2).
        chu = BB.than_bang(chu)
    for td, than in bang_md(chu):
        tdl = [x.lower() for x in td]
        if tdl and tdl[0] == "tên biến" and "giá trị hợp lệ" in tdl:
            il, ig = tdl.index("loại") if "loại" in tdl else 2, tdl.index("giá trị hợp lệ")
            for h in than:
                if h and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", h[0]):
                    ra.append(
                        BienNguon(
                            h[0], f"bộ biến G3 ({p.name})", h[il] if len(h) > il else "", h[ig] if len(h) > ig else ""
                        )
                    )
        elif tdl and tdl[0] == "tên" and any("định nghĩa" in x for x in tdl):
            idn = next(i for i, x in enumerate(tdl) if "định nghĩa" in x)
            for h in than:
                if h and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", h[0]):
                    ra.append(
                        BienNguon(
                            h[0],
                            f"bộ biến G3 ({p.name}) — biến phái sinh",
                            "tính toán",
                            "",
                            True,
                            h[idn] if len(h) > idn else "",
                        )
                    )
    return ra, (p.name if ra else None)


# ─────────────────────────── đọc bản máy ───────────────────────────


def doc_tu_dien(p: Path) -> dict[str, dict]:
    with open(p, encoding="utf-8-sig", newline="") as f:
        return {
            (r.get("Variable / Field Name") or "").strip(): r
            for r in csv.DictReader(f)
            if (r.get("Variable / Field Name") or "").strip()
        }


def doc_ma_thieu(d: Path) -> dict[str, set[str]]:
    p = d / "_ma-thieu-theo-bien.csv"
    ra: dict[str, set[str]] = {}
    if p.exists():
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                ra.setdefault((r.get("bien") or "").strip().lower(), set()).add((r.get("ma") or "").strip())
    return ra


def doc_anh_xa(d: Path) -> dict[str, str]:
    p = d / "_anh-xa-ten-bien.csv"
    ra = dict(BI_DANH)
    if p.exists():
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                a, b = (r.get("ten_nguon") or "").strip(), (r.get("ten_may") or "").strip()
                if a and b:
                    ra[a.lower()] = b
    return ra


# ─────────────────────────── đọc mã giá trị ───────────────────────────


def ma_tu_dien(lua_chon: str) -> set[int]:
    return {int(x) for x in re.findall(r"(?:^|\|)\s*(-?\d+)\s*,", lua_chon or "")}


def doc_ma(chu: str) -> tuple[set[int] | None, dict[int, set[str]]]:
    """Mã giá trị khai bằng chữ ⇒ (tập mã | None khi không đọc được, {mã: tập biến được dùng — mệnh đề «chỉ …»})."""
    s = (chu or "").replace("–", "-").replace("—", "-")
    ma: set[int] = set()
    gioi_han: dict[int, set[str]] = {}
    if re.search(r"(?:^|;)\s*-?\d+\s*,\s*[^;\d]", s) and "=" not in s:  # khuôn bộ biến G3: «1, Có; 0, Không»
        ma = {int(x) for x in re.findall(r"(?:^|;)\s*(-?\d+)\s*,", s)}
        return (ma or None), gioi_han
    for doan in re.split(r";", s):
        for a, b in re.findall(r"(?<![\d.])(\d{1,3})\s*=[^…]*…\s*(\d{1,3})\s*=", doan):
            ma |= set(range(int(a), int(b) + 1))
        for a, b in re.findall(r"(?<![\d.<>≥≤])(\d{1,2})\s*-\s*(\d{1,2})(?![\d.]|\s*(?:km|triệu|lần|tuổi|%))", doan):
            if int(a) < int(b) <= 20:
                ma |= set(range(int(a), int(b) + 1))
        for x in re.findall(r"(?<![\d.<>≥≤])(\d{1,3})\s*=", doan):
            ma.add(int(x))
            m = re.search(r"\(chỉ\s+([^)]+)\)", doan)
            if m:
                gioi_han[int(x)] = {t.strip().lower() for t in re.split(r",\s*", m[1]) if t.strip()}
    return (ma or None), gioi_han


def _so_trong(chu: str) -> list[tuple[float, bool]]:
    """Số ngưỡng trong định nghĩa (bỏ số mục «4.3.2», bỏ 0/1 là mã, bỏ số đếm «30 câu»/«2 kết quả», bỏ mệnh đề «độ
    nhạy: …»,
    bỏ chỉ số ô chọn «thuoc(2)», % ⇒ tỷ lệ). Khoảng «60–89» trả cả cận trên — _co_so chấp nhận cận trên + 1 (90)."""
    chu = re.sub(r"\(?\s*độ nhạy\s*:[^)]*\)?", " ", chu, flags=re.I)
    chu = re.sub(r"[A-Za-z_]\w*\(\d+\)", " ", chu)
    chu = re.sub(r"\d+\s*(?:kết quả|lần|câu|mục|lĩnh vực|ô|biến)\b", " ", chu, flags=re.I)
    chu = re.sub(r"(?:mục|phụ lục|bảng)\s*[\w.]+", " ", chu, flags=re.I)
    chu = re.sub(r"\b\d+\.\d+\.\d+\b", " ", chu)
    chu = re.sub(r"PMID\s*\d+|doi:\S+|\b(?:19|20)\d{2}\b", " ", chu, flags=re.I)
    ra = []
    for dau, so, pt in re.findall(
        r"([≥≤<>]\s*)?(?<![A-Za-z_\d.,])(\d+(?:[.,]\d+)?)\s*(%?)", chu
    ):  # bỏ chữ số dính chữ: G1
        v = float(so.replace(",", "."))
        if v in (0.0, 1.0):
            continue
        ra.append((v / 100 if pt else v, bool(dau)))  # (giá trị, là NGƯỠNG — đứng sau ≥ ≤ < >)
    return ra


HAM_CONG_THUC_CONG_BO = (
    "ckd_epi_2021",
)  # hàm cài đúng phương trình đã công bố (PMID trong tài liệu) — hằng số không nằm ở công thức


_SO = r"(?<![A-Za-z_\d.])(\d+(?:\.\d+)?)"  # bỏ chữ số dính tên biến (a1, c10)


def _so_nguong_cong_thuc(ct: str) -> set[float]:
    """Số đóng vai NGƯỠNG trong công thức: sau toán tử so sánh, toán tử dạng chuỗi («">=", 30»), điểm cắt của nhom(),
    tham số ty_le_toi_thieu/cach_ngay."""
    ra = {float(x) for x in re.findall(r"(?:>=|<=|==|!=|>|<)\s*" + _SO, ct)}
    ra |= {float(x) for x in re.findall(r'"\s*(?:>=|<=|==|!=|>|<)\s*"\s*,\s*' + _SO, ct)}
    ra |= {float(x) for x in re.findall(r"(?:ty_le_toi_thieu|cach_ngay)\s*=\s*" + _SO, ct)}
    for ds in re.findall(r"nhom\([^,\[]+,\s*\[([^\]]*)\]", ct):
        ra |= {float(x) for x in re.findall(_SO, ds)}
    return ra


def _co_so(cong_thuc: str, v: float, nguong: bool = False) -> bool:
    ct = cong_thuc or ""
    so = _so_nguong_cong_thuc(ct) if nguong else {float(x) for x in re.findall(_SO, ct)}
    if not nguong:
        so |= {float(len([t for t in ds.split(",") if t.strip()])) for ds in re.findall(r"\[([^\[\]]*)\]", ct)}
    return any(abs(v - x) < 1e-9 or abs(v * 100 - x) < 1e-9 or abs(v + 1 - x) < 1e-9 for x in so)


# ─────────────────────────── đối chiếu ───────────────────────────


# Số viết kiểu Việt Nam trong đề cương: nghìn bằng dấu chấm, thập phân bằng dấu phẩy («0,1–2.000», «1–100.000»). Trước
# 20/11/2026 «2.000» bị đọc thành 2,0 ⇒ LỆCH giả với từ điển 0.1–2000 khi soát định dạng số đề cương BTM.
_SO_VN = r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:[.,]\d+)?"


def _so_may(s: str) -> str:
    """«2.000» → «2000»; «1.234,5» → «1234.5»; «0,1» → «0.1»; «0.1» (kiểu máy, 1–2 chữ số sau dấu chấm) giữ nguyên."""
    s = s.strip()
    if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?", s):
        return s.replace(".", "").replace(",", ".")
    return s.replace(",", ".")


def _la_loai_dinh_luong(loai: str) -> bool:
    l = loai.lower()  # noqa: E741
    return any(x in l for x in ("định lượng", "rời rạc", "liên tục", "số", "ngày")) and "danh định" not in l


def doi_chieu(study_dir: Path, study: str) -> KetQua:
    d = Path(study_dir)
    kq = KetQua(study)
    dc, ten_dc = doc_de_cuong(d, study)
    g3, ten_g3 = doc_bo_bien_g3(d, study)
    # 15/11/2026 (G3-T2 — bác sĩ chọn bảng .md cho PI duyệt): bảng G3 do MÁY soạn (bang_bien_g3.py) chỉ là nguồn
    # người duyệt khi PI đã ghi xác nhận gắn đúng nội dung; bản nháp chưa duyệt mà vẫn tính thì máy so với chính nó
    # (vòng tròn, «đồng bộ» giả — giả lập lần 3 đo được). Bảng người soạn (không có dấu máy soạn) giữ luật #266.
    if g3:
        st_g3 = BB.trang_thai(d, study)
        if not st_g3["la_nguon_nguoi_duyet"]:
            kq.nguon_bi_loai.append(f"{ten_g3}: {st_g3['ly_do']}")
            g3, ten_g3 = [], None
    kq.nguon_nguoi_duyet = [x for x in (ten_dc, ten_g3) if x]
    nguon = dc + g3
    kq.so_bien_nguon = len({b.ten.lower() for b in nguon})
    if not nguon:
        kq.khong_do_duoc = (
            "chưa có bảng biến số trong đề cương nộp (DE_CUONG_NOP_HOI_DONG_<mã>.md, cột «Mã biến») lẫn bộ "
            "biến G3 (G3_BO_BIEN_SO_<mã>.md) — không có chuẩn để đối chiếu"
        )
        if kq.nguon_bi_loai:
            kq.khong_do_duoc = (
                "chưa có nguồn người duyệt: " + "; ".join(kq.nguon_bi_loai)
                + " — bản nháp máy chưa duyệt không phải chuẩn để đối chiếu"
            )
        return kq
    p_rieng, p_g5 = d / "_bo-bien-rieng.csv", d / f"G5_REDCap_dictionary_{study}.csv"
    try:
        td_rieng = doc_tu_dien(p_rieng) if p_rieng.exists() else None
        td_g5 = doc_tu_dien(p_g5) if p_g5.exists() else None
        bien_ps = BPS.doc_dac_ta(d)
    except (OSError, ValueError, BPS.LoiCongThuc) as e:
        kq.khong_do_duoc = f"đọc bản máy lỗi: {type(e).__name__}: {e}"[:300]
        return kq
    td = td_g5 if td_g5 is not None else td_rieng
    kq.ban_may = [p.name for p, t in ((p_rieng, td_rieng), (p_g5, td_g5)) if t is not None]
    if (d / "_bien-phai-sinh.csv").exists():
        kq.ban_may.append("_bien-phai-sinh.csv")
    if td is None:
        kq.khong_do_duoc = "chưa có từ điển máy (_bo-bien-rieng.csv / G5_REDCap_dictionary_<mã>.csv)"
        return kq
    them = kq.phat_hien.append
    ma_thieu, anh_xa = doc_ma_thieu(d), doc_anh_xa(d)
    td_thap = {k.lower(): k for k in td}
    ps_goc = {b.goc.lower(): b for b in bien_ps}
    ps_ten = {b.ten.lower() for b in bien_ps} | set(ps_goc)

    def tim_truong(ten: str) -> str | None:
        t = anh_xa.get(ten.lower(), ten).lower()
        return td_thap.get(t)

    # V7 — _bo-bien-rieng ≡ G5
    if td_rieng is not None and td_g5 is not None:
        for k in sorted(set(td_rieng) ^ set(td_g5)):
            them(PhatHien(LECH, "V7", k, f"chỉ có ở {'_bo-bien-rieng.csv' if k in td_rieng else p_g5.name}"))
        for k in sorted(set(td_rieng) & set(td_g5)):
            # 15/11/2026 (E5): so MỌI thuộc tính đi tới SPSS/R/phiếu (thêm nhãn, chú thích «Tên SPSS:», định danh, bắt
            # buộc) — cùng hàm với cầu nối SPSS/R (ma_tran_muc_tieu_bien.lech_thuoc_tinh), chuẩn hoá như G5.
            khac = MT.lech_thuoc_tinh(td_rieng[k], td_g5[k])
            if khac:
                them(PhatHien(LECH, "V7", k, f"_bo-bien-rieng.csv ≠ từ điển G5 ở cột: {', '.join(khac)}"))

    da_khop: set[str] = set()
    nguon_ten = {b.ten.lower() for b in nguon}
    for b in nguon:
        if b.tinh_toan:
            ps = ps_goc.get(b.ten.lower()) or ps_goc.get(anh_xa.get(b.ten.lower(), "").lower())
            if ps is None:
                if tim_truong(b.ten) and (td[tim_truong(b.ten)].get("Field Type") or "") == "calc":
                    continue  # calc của từ điển — V6 lo
                them(
                    PhatHien(
                        LECH,
                        "V1",
                        b.ten,
                        f"biến tính toán của {b.nguon} chưa có công thức trong _bien-phai-sinh.csv",
                        PV_PHAN_TICH,
                    )
                )
                continue
            thieu_so = (
                []
                if any(h in ps.cong_thuc_goc for h in HAM_CONG_THUC_CONG_BO)
                else [v for v, ng in _so_trong(b.dinh_nghia) if not _co_so(ps.cong_thuc_goc, v, ng)]
            )
            kq.dat_canh.append(
                {
                    "bien": b.ten,
                    "dinh_nghia_nguon": b.dinh_nghia[:400],
                    "cong_thuc": ps.cong_thuc_goc[:400],
                    "so_khong_thay_trong_cong_thuc": thieu_so,
                }
            )
            if thieu_so:
                them(
                    PhatHien(
                        XEM,
                        "V5",
                        b.ten,
                        "số trong định nghĩa không thấy trong công thức: "
                        + ", ".join(f"{v:g}" for v in thieu_so[:6])
                        + " — đặt cạnh ở «dat_canh»",
                    )
                )
            continue
        k = tim_truong(b.ten)
        if k is None:
            if b.ten.lower() in ps_goc:  # nguồn khai là trường nhưng máy tính bằng công thức — vẫn đọc được
                continue
            them(
                PhatHien(
                    LECH,
                    "V1",
                    b.ten,
                    f"có trong {b.nguon} nhưng KHÔNG có trong từ điển máy — mẫu nhập sẽ thiếu biến này",
                )
            )
            continue
        da_khop.add(k)
        f = td[k]
        ft = (f.get("Field Type") or "").strip()
        kieu_kt = (f.get("Text Validation Type OR Show Slider Number") or "").strip()
        if b.loai and ft in LOAI_CHON and _la_loai_dinh_luong(b.loai) and "thứ bậc" not in b.loai.lower():
            them(PhatHien(XEM, "V3", b.ten, f"nguồn ghi «{b.loai}» nhưng từ điển là ô chọn ({ft})"))
        elif (
            b.loai
            and ft == "text"
            and not kieu_kt
            and doc_ma(b.ma_hoa)[0] is not None
            and any(x in b.loai.lower() for x in ("danh định", "nhị phân", "thứ bậc", "chọn"))
        ):
            them(PhatHien(XEM, "V3", b.ten, f"nguồn ghi «{b.loai}» nhưng từ điển là ô chữ tự do"))
        mien = {m for m in ma_thieu.get(k.lower(), set()) | ma_thieu.get("*", set())}
        if ft in LOAI_CHON:
            ma_nguon, gioi_han = doc_ma(b.ma_hoa)
            ma_td = (
                {0, 1}
                if ft in ("yesno", "truefalse")
                else ma_tu_dien(f.get("Choices, Calculations, OR Slider Labels") or "")
            )
            if ma_nguon is None:
                if b.ma_hoa:
                    them(
                        PhatHien(
                            XEM,
                            "V2",
                            b.ten,
                            f"không đọc được mã từ «{b.ma_hoa[:80]}» — đối chiếu tay với từ điển {sorted(ma_td)}",
                        )
                    )
            else:
                ma_nguon = {m for m in ma_nguon if m not in gioi_han or b.ten.lower() in gioi_han[m]}
                thieu = sorted(m for m in ma_nguon - ma_td if str(m) not in mien)
                thua = sorted(m for m in ma_td - ma_nguon if str(m) not in mien)
                if thieu or thua:
                    them(
                        PhatHien(
                            LECH,
                            "V2",
                            b.ten,
                            f"mã nguồn {sorted(ma_nguon)} ≠ từ điển {sorted(ma_td)}"
                            + (f" — từ điển thiếu {thieu}" if thieu else "")
                            + (f" — từ điển thừa {thua}" if thua else ""),
                        )
                    )
        else:
            m = re.fullmatch(rf"\s*({_SO_VN})\s*[–-]\s*({_SO_VN})\s*", b.ma_hoa or "")
            if m:
                lo, hi = (f.get("Text Validation Min") or "").strip(), (f.get("Text Validation Max") or "").strip()
                if (lo, hi) != (_so_may(m[1]), _so_may(m[2])) and lo and hi:
                    try:
                        if float(lo) != float(_so_may(m[1])) or float(hi) != float(_so_may(m[2])):
                            them(PhatHien(LECH, "V2", b.ten, f"khoảng nguồn {m[1]}–{m[2]} ≠ từ điển {lo}–{hi}"))
                    except ValueError:
                        pass
            for x in re.findall(r"(?<![\d.])(\d{3,})\s*=", b.ma_hoa or ""):  # mã đặc biệt của biến định lượng (vd 998)
                if x not in mien:
                    them(PhatHien(LECH, "V2", b.ten, f"mã đặc biệt {x} của nguồn chưa khai ở _ma-thieu-theo-bien.csv"))

    # V4 — chỉ có ở từ điển máy
    for k, f in td.items():
        if k in da_khop or k.lower() == "record_id" or k.lower() in ps_goc:
            continue
        if k.lower() in nguon_ten:
            continue
        goc = re.sub(r"_?khac$", "", k.lower())
        if goc != k.lower() and any(x.startswith(goc[:6]) for x in (y.lower() for y in da_khop)):
            continue  # ô «khác, ghi rõ» đi kèm
        them(PhatHien(XEM, "V4", k, "trường chỉ có ở từ điển máy, đề cương/bộ biến không khai"))

    # V5 — biến phái sinh ngoài nguồn
    nguon_tt = nguon_ten | {anh_xa.get(t, t).lower() for t in nguon_ten}
    for g, b in ps_goc.items():
        if g in nguon_tt:
            continue
        if b.ngoai_tang:
            them(
                PhatHien(
                    XEM, "V5", b.goc, f"biến ngoài tầng ({b.cong_thuc_goc[:40]}) — không có trong nguồn người duyệt"
                )
            )
            continue
        them(
            PhatHien(
                LECH,
                "V5",
                b.goc,
                "biến phái sinh NGOÀI ĐỀ CƯƠNG/BỘ BIẾN đã duyệt — bổ sung vào đề cương/bộ biến "
                "(chủ nhiệm duyệt) hoặc bỏ khỏi _bien-phai-sinh.csv",
            )
        )

    # V6 — calc phải có biến phái sinh cùng tên
    calc_thieu = {k for k, f in td.items() if (f.get("Field Type") or "").strip() == "calc" and k.lower() not in ps_goc}
    for k in sorted(calc_thieu):
        them(
            PhatHien(
                LECH,
                "V6",
                k,
                "trường calc của REDCap: nhập Excel/SPSS KHÔNG tính calc ⇒ cột này sẽ trống — khai công "
                "thức CÙNG TÊN trong _bien-phai-sinh.csv (cùng định nghĩa với cột Choices/Calculations) — soạn nháp tự "
                f"động: python tools/bien_phai_sinh.py soan-tu-calc --study {study} --ghi (thống kê viên/PI duyệt)",
            )
        )

    # V8 — biến của đặc tả phân tích
    p_dt = d / "G6_DAC_TA_SAP.json"
    if p_dt.exists():
        try:
            dt = json.loads(p_dt.read_text(encoding="utf-8"))
        except ValueError as e:
            them(PhatHien(LECH, "V8", p_dt.name, f"JSON hỏng: {e}"))
            dt = {}
        doc_duoc = ({k.lower() for k in td} - {c.lower() for c in calc_thieu}) | ps_ten
        for pt in dt.get("phan_tich") or []:
            ts = pt.get("tham_so") or {}
            ten = [ts.get(x) for x in ("outcome", "group", "time", "event", "cot_cum") if ts.get(x)]
            for x in ("covariates", "hiep_bien_phan_loai", "ty_le", "vars"):
                v = ts.get(x) or []
                ten += v if isinstance(v, list) else [s.strip() for s in str(v).split(",") if s.strip()]
            if ts.get("loc"):
                try:
                    ten += BPS.cot_cua_cay(BPS.phan_tich(ts["loc"]))
                except BPS.LoiCongThuc as e:
                    them(PhatHien(LECH, "V8", str(pt.get("id")), f"biểu thức loc không hợp lệ: {e}"))
            for t in dict.fromkeys(ten):
                tl = re.sub(r"___\d+$", "", str(t).lower())
                if tl not in doc_duoc and str(t).lower() not in doc_duoc:
                    ly_do = (
                        "là trường calc chưa có biến phái sinh"
                        if tl in {c.lower() for c in calc_thieu}
                        else "không có trong bản máy"
                    )
                    them(PhatHien(LECH, "V8", str(t), f"đặc tả mục {pt.get('id')} dùng «{t}» nhưng {ly_do}"))
    return kq


# ─────────────────────────── báo cáo ───────────────────────────


def bien_phai_sinh_ngoai_de_cuong(study_dir: Path, study: str, goc: set[str]) -> tuple[list[str], str | None]:
    """Dùng ở cổng PHÂN TÍCH (bien_phai_sinh.ap_dung_cho_phan_tich): trong các biến phái sinh gốc `goc` sắp tính, biến
    nào
    NGOÀI đề cương/bộ biến đã duyệt. Trả (danh sách, lý do không đo được | None)."""
    kq = doi_chieu(study_dir, study)
    if kq.khong_do_duoc:
        return [], kq.khong_do_duoc
    gl = {g.lower() for g in goc}
    return sorted({p.bien for p in kq.phat_hien if p.muc == LECH and p.luat == "V5" and p.bien.lower() in gl}), None


def markdown(kq: KetQua) -> str:
    d = [
        "# Đối chiếu biến ↔ đề cương · " + kq.study,
        "",
        f"- Trạng thái: **{kq.trang_thai}** · LỆCH {kq.so_lech} · CẦN XEM {len(kq.phat_hien) - kq.so_lech}",
        f"- Nguồn người duyệt: {', '.join(kq.nguon_nguoi_duyet) or '—'} ({kq.so_bien_nguon} biến)",
        f"- Bản máy: {', '.join(kq.ban_may) or '—'}",
    ]
    d += [f"- Không tính là nguồn người duyệt: {x}" for x in kq.nguon_bi_loai]
    if kq.khong_do_duoc:
        d += ["", f"⚪ KHÔNG ĐO ĐƯỢC — {kq.khong_do_duoc}. Không đo được ≠ đồng bộ."]
    if kq.phat_hien:
        d += ["", "| Mức | Luật | Phạm vi | Biến | Chi tiết |", "|---|---|---|---|---|"]
        for p in sorted(kq.phat_hien, key=lambda x: (x.muc != LECH, x.luat, x.bien.lower())):
            muc = "🔴 LỆCH" if p.muc == LECH else "🟡 cần xem"
            pv = "nhập liệu" if p.pham_vi == PV_NHAP else "phân tích"
            d.append(f"| {muc} | {p.luat} | {pv} | `{p.bien}` | {p.chi_tiet.replace('|', '/')} |")
    if kq.dat_canh:
        d += [
            "",
            "## Biến tính toán — định nghĩa nguồn đặt cạnh công thức (người đối chiếu)",
            "",
            "| Biến | Định nghĩa (nguồn) | Công thức (máy) |",
            "|---|---|---|",
        ]
        for x in kq.dat_canh:
            d.append(
                f"| `{x['bien']}` | {x['dinh_nghia_nguon'].replace('|', '/')} | `{x['cong_thuc'].replace('|', '/')}` |"
            )
    d += [
        "",
        "Sửa LỆCH: nguồn người duyệt (đề cương/bộ biến) là chuẩn — sửa bản máy cho khớp; nếu chính nguồn cần đổi thì "
        "chủ nhiệm duyệt sửa đề cương/bộ biến trước. " + CAN_KIEM,
        "",
    ]
    return "\n".join(d)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu biến ↔ đề cương/bộ biến đã duyệt (chỉ đọc).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ghi", action="store_true", help="ghi DOI_CHIEU_BIEN_<mã>.md/.json vào thư mục đề tài")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study or ""):
        print("mã đề tài không hợp lệ", file=sys.stderr)
        return MA_THAM_SO
    d = BASE / "exports" / a.study
    if not d.is_dir():
        print(f"không có thư mục exports/{a.study}", file=sys.stderr)
        return MA_THAM_SO
    kq = doi_chieu(d, a.study)
    if a.ghi:
        (d / f"DOI_CHIEU_BIEN_{a.study}.json").write_text(
            json.dumps(kq.to_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
        )
        (d / f"DOI_CHIEU_BIEN_{a.study}.md").write_text(markdown(kq), encoding="utf-8", newline="\n")
    print(json.dumps(kq.to_dict(), ensure_ascii=False, indent=1) if a.json else markdown(kq))
    return kq.ma_thoat()


if __name__ == "__main__":
    raise SystemExit(main())
