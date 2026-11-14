#!/usr/bin/env python3
"""Nhập liệu BẰNG TAY qua Excel → CSV chuẩn cho cổng tiếp nhận G5 (14/11/2026, gói E1).

Bác sĩ nhập phiếu giấy vào Excel. Công cụ này giữ cho đường đó CHÍNH XÁC từ ô đầu tiên:

  mau      Sinh tệp mẫu nhập liệu .xlsx từ từ điển G5 (REDCap) + mã thiếu: mỗi biểu mẫu một trang, hàng 1 tên biến,
           hàng 2 nhãn, hàng 3 gợi ý mã/khoảng, ô có KIỂM TRA NHẬP của chính Excel (danh sách mã, số nguyên trong
           khoảng, mã thiếu BTR/KDD/998…, mã nghiên cứu không trùng, ô chọn nhiều 0/1 có trần @MAXCHECKED), trang
           TU_DIEN và HUONG_DAN, trang ẩn _META ghi dấu vân tay đặc tả để lúc nhập biết tệp sinh từ từ điển nào.
  nhap     Đọc Excel đã nhập (CHỈ ĐỌC, không sửa tệp) → CSV UTF-8 ở thư mục NGOÀI repo + báo cáo lỗi theo từng ô
           (trang!ô). Không đoán, không tự sửa giá trị: lỗi cấu trúc (ô gộp, công thức, Excel tự đổi mã thành ngày,
           tiêu đề lạ, trùng mã…) ⇒ KHÔNG ghi CSV; lỗi giá trị (ngoài danh mục/khoảng, thiếu câu bắt buộc, logic
           nhánh, luật DQ của `_luat-dq.csv`) ⇒ ghi CSV kèm danh sách truy vấn để sửa trong Excel rồi nhập lại.
           Tự kiểm CSV vừa ghi bằng ĐÚNG đường đọc của bộ làm sạch (clean_research_dataset._read_csv) và của
           pandas (run_stats_analysis). `--tiep-nhan` gọi luôn cổng tiếp nhận chuẩn (import_real_dataset.py).
  so-sanh  So hai lần nhập độc lập (NHẬP KÉP) từng ô theo mã nghiên cứu → danh sách ô lệch để đối chiếu phiếu gốc,
           tỷ lệ lệch theo biến, và bản tóm tắt KHÔNG chứa giá trị làm bằng chứng đối chiếu nguồn cho G5.

Không thay thống kê viên/quản lý dữ liệu; mọi giá trị nghi sai phải đối chiếu PHIẾU GỐC. Cần bác sĩ kiểm chứng.

Chạy bằng Python của MÔI TRƯỜNG DỰ ÁN (~/.ebm-venv — python3 hệ thống của máy không có openpyxl). Ví dụ:
  ~/.ebm-venv/bin/python tools/nhap_lieu_excel.py mau --study hai-long-benh-nhan-C1a-BVQY175
  ~/.ebm-venv/bin/python tools/nhap_lieu_excel.py nhap --study hai-long-benh-nhan-C1a-BVQY175 \\
      --excel ~/NhapLieu/lan1.xlsx
  ~/.ebm-venv/bin/python tools/nhap_lieu_excel.py so-sanh --study hai-long-benh-nhan-C1a-BVQY175 \\
      --excel1 ~/NhapLieu/lan1.xlsx --excel2 ~/NhapLieu/lan2.xlsx
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import cau_noi_spss as SP  # noqa: E402 — dùng CHUNG luật mã thiếu (_ap_cho_cot) và luật «ngoài repo»

MA_OK, MA_LOI, MA_KHONG_DO, MA_TU_CHOI = 0, 1, 2, 3
CAN_KIEM = "Cần bác sĩ kiểm chứng — mọi giá trị nghi sai phải đối chiếu PHIẾU GỐC, máy không tự sửa."
PHIEN_BAN_MAU = 1
TEN_META, TEN_DM, TEN_HD, TEN_TD = "_META", "_DANH_MUC", "HUONG_DAN", "TU_DIEN"
TRANG_PHU = {TEN_META, TEN_DM, TEN_HD, TEN_TD}
DONG_TEN, DONG_NHAN, DONG_GOI_Y, DONG_DAU = 1, 2, 3, 4
SO_DONG_MAC_DINH = 1000

# Mức nghiêm trọng của một phát hiện.
LOI = "LOI"  # lỗi cấu trúc/chuyển đổi — CSV KHÔNG được ghi
TRUY_VAN = "TRUY_VAN"  # giá trị cần đối chiếu phiếu gốc — CSV vẫn ghi, mã thoát 1
CANH_BAO = "CANH_BAO"  # không chặn, ghi vào báo cáo

# Cảnh báo mang nghĩa «có phần CHƯA ĐƯỢC KIỂM/ĐỌC» ⇒ trạng thái CHUA_DU (mã 1, chặn --tiep-nhan), không bao giờ SACH.
CHUA_DU_KIEM = frozenset(
    {"logic_nhanh_khong_danh_gia_duoc", "luat_dq_khong_danh_gia_duoc", "trang_la_bi_bo_qua", "cot_cua_trang_vang_mat"}
)
# Chuỗi pandas.read_csv mặc định coi là THIẾU — bản chép pandas 2.x dùng khi máy không có pandas.
NA_PANDAS_DU_PHONG = frozenset(
    {"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA",
     "NULL", "NaN", "None", "n/a", "nan", "null"}
)  # fmt: skip
KIEU_CHU = {"id", "chu", "van_ban"}  # giá trị chữ tự do: KHÔNG in nguyên văn ra màn hình/báo cáo tóm tắt
_KHONG_RONG = "​‌‍⁠﻿"  # ký tự rộng 0 hay lẫn khi dán từ web/Zalo


class TuChoi(Exception):
    """Tham số/đầu vào không được phép (mã 3)."""


class KhongDoDuoc(Exception):
    """Thiếu điều kiện để đo (mã 2): không có từ điển, thiếu openpyxl…"""


# ───────────────────────────── từ điển ─────────────────────────────

_COT_TD = {
    "ten": ("Variable / Field Name", "field_name"),
    "form": ("Form Name", "form_name"),
    "phan": ("Section Header", "section_header"),
    "loai": ("Field Type", "field_type"),
    "nhan": ("Field Label", "field_label"),
    "lua_chon": ("Choices, Calculations, OR Slider Labels", "select_choices_or_calculations"),
    "ghi_chu": ("Field Note", "field_note"),
    "kiem_tra": ("Text Validation Type OR Show Slider Number", "text_validation_type_or_show_slider_number"),
    "min": ("Text Validation Min", "text_validation_min"),
    "max": ("Text Validation Max", "text_validation_max"),
    "nhanh": ("Branching Logic (Show field only if...)", "branching_logic"),
    "bat_buoc": ("Required Field?", "required_field"),
    "chu_thich": ("Field Annotation", "field_annotation"),
}


@dataclass
class Cot:
    """Một CỘT nhập liệu (trường checkbox REDCap tách thành nhiều cột `<trường>___<mã>`)."""

    ten: str
    truong: str
    form: str
    kieu: str  # id · ma · hop · so_nguyen · so · ngay · ngay_gio · gio · chu · van_ban
    nhan: str = ""
    ghi_chu: str = ""
    kiem_tra: str = ""
    lua_chon: dict = field(default_factory=dict)  # mã → nhãn (ma) hoặc của cả nhóm (hop)
    ma_thieu: dict = field(default_factory=dict)  # mã thiếu ÁP cho cột này: mã → nhãn
    min: str = ""
    max: str = ""
    bat_buoc: bool = False
    nhanh: str = ""
    toi_da_chon: int | None = None  # @MAXCHECKED của nhóm checkbox
    ma_hop: str = ""  # mã của ô checkbox
    nomissing: bool = False

    def dac_ta(self) -> dict:
        """Phần đặc tả QUYẾT ĐỊNH việc kiểm/chuyển đổi — nhãn và chú thích văn xuôi không tính (sửa câu chữ không
        làm mẫu cũ mất hiệu lực)."""
        return {
            "ten": self.ten,
            "truong": self.truong,
            "form": self.form,
            "kieu": self.kieu,
            "kiem_tra": self.kiem_tra,
            "lua_chon": sorted(self.lua_chon),
            "ma_thieu": sorted(self.ma_thieu),
            "min": self.min,
            "max": self.max,
            "bat_buoc": self.bat_buoc,
            "nhanh": self.nhanh,
            "toi_da_chon": self.toi_da_chon,
            "ma_hop": self.ma_hop,
            "nomissing": self.nomissing,
        }


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 16), b""):
            h.update(khoi)
    return h.hexdigest()


def doc_tu_dien_day_du(p: Path) -> list[dict]:
    """Từ điển REDCap (tiêu đề hiển thị HOẶC tiêu đề API) ⇒ danh sách trường theo ĐÚNG thứ tự tệp."""
    with open(p, encoding="utf-8-sig", newline="") as f:
        dr = csv.DictReader(f)
        tieu_de = dr.fieldnames or []
        cot = {k: next((t for t in tieu_de if t in v), None) for k, v in _COT_TD.items()}
        if not cot["ten"] or not cot["loai"]:
            raise TuChoi(f"{p.name}: không thấy cột «Variable / Field Name»/«Field Type» của từ điển REDCap")
        ra = []
        for r in dr:
            ten = (r.get(cot["ten"]) or "").strip()
            if ten:
                ra.append({k: (r.get(c) or "").strip() if c else "" for k, c in cot.items()})
    if not ra:
        raise TuChoi(f"{p.name}: từ điển rỗng")
    ten_trung = sorted({t["ten"] for t in ra if [x["ten"] for x in ra].count(t["ten"]) > 1})
    if ten_trung:
        raise TuChoi(f"{p.name}: tên trường trùng: {', '.join(ten_trung)}")
    return ra


def _lua_chon(t: dict) -> dict[str, str]:
    loai = t["loai"].lower()
    if loai == "yesno":
        return {"1": "Có", "0": "Không"}
    if loai == "truefalse":
        return {"1": "Đúng", "0": "Sai"}
    ra: dict[str, str] = {}
    for phan in t.get("lua_chon", "").split("|"):
        if "," in phan:
            ma, nhan = phan.split(",", 1)
            if ma.strip():
                ra[ma.strip()] = SP.bo_html(nhan)
    return ra


def _ma_thieu_cho(cot: str, goc: str, mt: list[dict], nomissing: bool) -> dict[str, str]:
    ra: dict[str, str] = {}
    for m in mt:
        if nomissing and m["bien"] == "*":
            continue  # @NOMISSING: trường không nhận mã thiếu cấp dự án
        if SP._ap_cho_cot(m, cot, goc):
            ra[m["ma"]] = m["nhan"]
    return ra


def ke_hoach_cot(td: list[dict], mt: list[dict]) -> tuple[list[Cot], list[str]]:
    """Từ điển + mã thiếu ⇒ (các cột nhập liệu theo thứ tự từ điển, ghi chú các trường KHÔNG nhập tay)."""
    cot: list[Cot] = []
    bo_qua: list[str] = []
    for i, t in enumerate(td):
        loai, kt = t["loai"].lower(), t["kiem_tra"].lower()
        chung = {
            "truong": t["ten"],
            "form": t["form"] or "du_lieu",
            "nhan": SP.bo_html(t["nhan"]),
            "ghi_chu": SP.bo_html(t["ghi_chu"]),
            "kiem_tra": kt,
            "bat_buoc": t["bat_buoc"].lower() in ("y", "yes", "1"),
            "nhanh": t["nhanh"],
            "nomissing": "@NOMISSING" in t["chu_thich"].upper(),
        }
        if i == 0:  # REDCap: trường ĐẦU TIÊN là mã bản ghi
            cot.append(Cot(ten=t["ten"], kieu="id", **{**chung, "bat_buoc": True, "nhanh": ""}))
            continue
        if loai in ("descriptive", "calc", "file", "sql"):
            bo_qua.append(f"{t['ten']} ({loai} — không nhập tay)")
            continue
        if loai == "checkbox":
            lc = _lua_chon(t)
            m = re.search(r"@MAXCHECKED\s*=\s*(\d+)", t["chu_thich"], re.I)
            for ma in lc:
                if not re.fullmatch(r"[A-Za-z0-9_-]+", ma):
                    bo_qua.append(f"{t['ten']}: mã checkbox «{ma}» không tạo được tên cột REDCap")
                    continue
                cot.append(
                    Cot(
                        ten=f"{t['ten']}___{ma}",
                        kieu="hop",
                        lua_chon=lc,
                        ma_hop=ma,
                        toi_da_chon=int(m.group(1)) if m else None,
                        **{**chung, "bat_buoc": False},
                    )
                )
            continue
        if loai in ("radio", "dropdown", "yesno", "truefalse"):
            kieu = "ma"
        elif loai == "slider":
            kieu = "so_nguyen"
            chung.update(kiem_tra="integer")
        elif loai == "notes":
            kieu = "van_ban"
        elif kt == "integer":
            kieu = "so_nguyen"
        elif kt.startswith("number"):
            kieu = "so"
        elif kt.startswith("datetime"):
            kieu = "ngay_gio"
        elif kt.startswith("date"):
            kieu = "ngay"
        elif kt in ("time", "time_hh_mm"):
            kieu = "gio"
        else:
            kieu = "chu"
        c = Cot(ten=t["ten"], kieu=kieu, lua_chon=_lua_chon(t) if kieu == "ma" else {}, **chung)
        if loai == "slider":
            c.min, c.max = t["min"] or "0", t["max"] or "100"
        else:
            c.min, c.max = t["min"], t["max"]
        cot.append(c)
    for c in cot:
        if c.kieu not in ("id", "hop"):
            c.ma_thieu = _ma_thieu_cho(c.ten, c.truong, mt, c.nomissing)
    return cot, bo_qua


def dau_van_tay_dac_ta(cot: list[Cot]) -> str:
    return hashlib.sha256(
        json.dumps([c.dac_ta() for c in cot], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def tim_tu_dien(study: str, tu_dien: str | None, ma_thieu: str | None) -> tuple[Path, Path | None]:
    d = SP.thu_muc_de_tai(study)
    td_p = Path(tu_dien).expanduser().resolve() if tu_dien else d / f"G5_REDCap_dictionary_{study}.csv"
    if not td_p.exists():
        goi_y = d / "_bo-bien-rieng.csv"
        raise KhongDoDuoc(
            f"không thấy từ điển G5: {td_p.name} — chạy run_g5_auto.py trước"
            + (f", hoặc dùng --dictionary {goi_y} nếu đã duyệt bộ biến" if goi_y.exists() else "")
        )
    mt_p = Path(ma_thieu).expanduser().resolve() if ma_thieu else d / "_ma-thieu-theo-bien.csv"
    return td_p, (mt_p if mt_p.exists() else None)


# ───────────────────────────── số ASCII chặt ─────────────────────────────

_SO_CHU = re.compile(r"[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?")


def _so_chat(s) -> float | None:
    """Số theo cú pháp ASCII CHẶT — float() của Python nhận cả «1_0», «６０», «inf», «nan» mà SPSS đọc thành SYSMIS."""
    if not isinstance(s, str) or not _SO_CHU.fullmatch(s.strip()):
        return None
    x = float(s)
    return x if math.isfinite(x) else None


def vuot_do_chinh_xac(s: str) -> bool:
    """Số mà double (Excel, SPSS, R, pandas) KHÔNG lưu đúng được: giá trị thập phân ≠ giá trị của double gần nhất
    (vd 12345678901234567 ⇒ 12345678901234568). «0.1» không tính — chuỗi ngắn nhất của double khứ hồi đúng."""
    try:
        return Decimal(s.strip()) != Decimal(repr(float(s)))
    except (InvalidOperation, ValueError, OverflowError):
        return False


def _co_chu_so_khong_ascii(s: str) -> bool:
    return any(ch.isdigit() and not ch.isascii() for ch in s)


# ───────────────────────────── logic REDCap (nhánh + luật DQ) ─────────────────────────────

_TOKEN = re.compile(
    r"\s*(?:(?P<ref>\[[A-Za-z0-9_]+(?:\([A-Za-z0-9_-]+\))?\])|(?P<str>'[^']*'|\"[^\"]*\")"
    r"|(?P<num>\d+(?:\.\d+)?)|(?P<op><>|!=|>=|<=|=|>|<)|(?P<ar>[-+*/])|(?P<par>[()])|(?P<kw>and\b|or\b))",
    re.I,
)


class LogicKhongHo(ValueError):
    """Biểu thức REDCap dùng cú pháp công cụ chưa hỗ trợ (hàm, biến vắng mặt…) — KHÔNG được coi là đúng/sai."""


def _tach_token(bt: str) -> list[tuple[str, str]]:
    ra, i = [], 0
    while i < len(bt):
        if bt[i:].strip() == "":
            break
        m = _TOKEN.match(bt, i)
        if not m or m.end() == i:
            raise LogicKhongHo(f"không hiểu đoạn «{bt[i : i + 20].strip()}»")
        loai = m.lastgroup
        ra.append((loai, m.group(loai)))
        i = m.end()
    return ra


def _so_logic(s) -> float | None:
    if isinstance(s, float):
        return s
    return _so_chat(s)


def _so_sanh(a, op: str, b) -> bool:
    if a is None or b is None:
        return op in ("<>", "!=")  # phép tính có toán hạng không phải số ⇒ NaN: NaN <> x đúng, mọi so sánh khác sai
    na, nb = _so_logic(a), _so_logic(b)
    if na is not None and nb is not None:
        x, y = na, nb
    elif op in ("=", "<>", "!="):
        x, y = str(a), str(b)  # so chuỗi: '' = '' đúng; '' = '2' sai
    else:
        return False  # so lớn/nhỏ với ô trống/chữ: REDCap cho sai
    return {
        "=": x == y,
        "<>": x != y,
        "!=": x != y,
        ">": x > y,
        "<": x < y,
        ">=": x >= y,
        "<=": x <= y,
    }[op]


def danh_gia_logic(bt: str, dong: dict[str, str]) -> bool:
    """Đánh giá biểu thức REDCap tập con: [biến], [biến(mã)] (checkbox), '…', số, + - * / (toán hạng không phải số
    ⇒ NaN ⇒ so sánh sai, như REDCap), = <> != > < >= <=, and/or, ngoặc. Ngoài tập con hoặc biến không có trong
    dòng ⇒ LogicKhongHo (không bao giờ âm thầm coi là đúng/sai)."""
    tk = _tach_token(bt)
    vt = 0

    def nhin(k: int = 0):
        return tk[vt + k] if vt + k < len(tk) else (None, None)

    def lay():
        nonlocal vt
        x = nhin()
        vt += 1
        return x

    def nguyen_to():
        loai, v = lay()
        if loai == "ref":
            m = re.fullmatch(r"\[([A-Za-z0-9_]+)(?:\(([A-Za-z0-9_-]+)\))?\]", v)
            ten = f"{m.group(1)}___{m.group(2)}" if m.group(2) else m.group(1)
            if ten not in dong:
                raise LogicKhongHo(f"biến {v} không có trong dữ liệu")
            return dong[ten]
        if loai == "str":
            return v[1:-1]
        if loai == "num":
            return v
        if loai == "ar" and v == "-":
            x = _so_logic(nguyen_to())
            return None if x is None else -x
        if loai == "par" and v == "(":
            x = bieu_thuc_so()
            if lay()[1] != ")":
                raise LogicKhongHo("thiếu ngoặc đóng")
            return x
        raise LogicKhongHo(f"cần giá trị, gặp «{v}»")

    def tinh(a, op, b):
        x, y = _so_logic(a), _so_logic(b)
        if x is None or y is None:
            return None
        if op == "/":
            return None if y == 0 else x / y
        return {"+": x + y, "-": x - y, "*": x * y}[op]

    def tich():
        kq = nguyen_to()
        while nhin()[0] == "ar" and nhin()[1] in "*/":
            op = lay()[1]
            kq = tinh(kq, op, nguyen_to())
        return kq

    def bieu_thuc_so():
        kq = tich()
        while nhin()[0] == "ar" and nhin()[1] in "+-":
            op = lay()[1]
            kq = tinh(kq, op, tich())
        return kq

    def so_sanh() -> bool:
        nonlocal vt
        if nhin() == ("par", "("):
            luu = vt
            lay()
            try:
                kq = hoac()
                if lay()[1] == ")" and nhin()[0] != "op" and nhin()[0] != "ar":
                    return kq
            except LogicKhongHo:
                pass
            vt = luu  # không phải nhóm logic ⇒ thử như biểu thức số: «( [a] + [b] ) > 2»
        a = bieu_thuc_so()
        loai, op = lay()
        if loai != "op":
            raise LogicKhongHo("biểu thức không có phép so sánh")
        return _so_sanh(a, op, bieu_thuc_so())

    def va() -> bool:
        kq = so_sanh()
        while (nhin()[1] or "").lower() == "and":
            lay()
            rhs = so_sanh()
            kq = kq and rhs
        return kq

    def hoac() -> bool:
        kq = va()
        while (nhin()[1] or "").lower() == "or":
            lay()
            rhs = va()
            kq = kq or rhs
        return kq

    kq = hoac()
    if vt != len(tk):
        raise LogicKhongHo(f"thừa «{tk[vt][1]}»")
    return kq


def doc_luat_dq(p: Path | None) -> list[dict]:
    if not p or not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return [
            {k: (r.get(k) or "").strip() for k in ("ma_luat", "muc_do", "mo_ta", "bieu_thuc_redcap")}
            for r in csv.DictReader(f)
            if (r.get("bieu_thuc_redcap") or "").strip()
        ]


# ───────────────────────────── sinh mẫu Excel ─────────────────────────────


def _py() -> str:
    """Lệnh Python để IN trong gợi ý bước kế: đúng trình thông dịch đang chạy (venv dự án ⇒ «~/.ebm-venv/bin/python»)
    — gợi ý «python3» từng làm bác sĩ chạy bằng python3 hệ thống (không có openpyxl)."""
    exe = Path(sys.executable)
    try:
        return (
            "~/" + exe.relative_to(Path.home()).as_posix() if (Path.home() / ".ebm-venv") in exe.parents else str(exe)
        )
    except ValueError:
        return str(exe)


def _openpyxl():
    try:
        import openpyxl  # noqa: PLC0415

        return openpyxl
    except ImportError as e:
        raise KhongDoDuoc(
            "thiếu thư viện openpyxl — chạy bằng Python của môi trường dự án: ~/.ebm-venv/bin/python "
            "tools/nhap_lieu_excel.py … (python3 hệ thống của máy không có openpyxl; Windows: "
            "%USERPROFILE%\\.ebm-venv\\Scripts\\python)"
        ) from e


def _so_hay_chu(ma: str):
    """Mã danh mục ghi vào ô danh sách: mã SỐ phải là SỐ (Excel so ô gõ 1 — kiểu số — với mục danh sách cùng kiểu)."""
    x = _so_chat(ma)
    if x is None:
        return ma
    return int(x) if x.is_integer() and re.fullmatch(r"-?\d+", ma) else x


def _chuoi_xl(s: str) -> str:
    return '"' + s.replace('"', '""') + '"'


def _ngay_xl(s: str) -> str | None:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s.strip())
    return f"DATE({int(m.group(1))},{int(m.group(2))},{int(m.group(3))})" if m else None


def cong_thuc_kiem(c: Cot, o: str, vung_hop: str | None, vung_id: str | None) -> str | None:
    """Công thức kiểm tra nhập (Excel «Custom») cho ô trên-trái `o` của vùng; None = không đặt (kiểm lúc nhập)."""
    so_thieu = [m for m in c.ma_thieu if _so_chat(m) is not None]
    chu_thieu = [m for m in c.ma_thieu if _so_chat(m) is None]
    nhanh_chu = "OR(" + ",".join(f"{o}={_chuoi_xl(m)}" for m in chu_thieu) + ")" if chu_thieu else "FALSE"
    if c.kieu == "id":
        return f"COUNTIF({vung_id},{o})=1" if vung_id else None
    if c.kieu == "hop":
        co_ban = f"OR({o}=0,{o}=1)"
        if c.toi_da_chon and vung_hop:
            return f"AND({co_ban},COUNTIF({vung_hop},1)<={c.toi_da_chon})"
        return co_ban
    if c.kieu in ("so_nguyen", "so", "ngay", "ngay_gio"):
        dk = []
        if c.kieu in ("so_nguyen", "ngay"):
            dk.append(f"{o}=INT({o})")
        for gh, op in ((c.min, ">="), (c.max, "<=")):
            if not gh:
                continue
            if c.kieu in ("ngay", "ngay_gio"):
                x = _ngay_xl(gh)
                if x:
                    dk.append(f"{o}{op}{x}")
            elif _so_chat(gh) is not None:
                dk.append(f"{o}{op}{gh}")
        nhanh_so = "AND(" + ",".join(dk) + ")" if dk else "TRUE"
        if so_thieu:
            nhanh_so = "OR(" + ",".join(f"{o}={m}" for m in so_thieu) + "," + nhanh_so + ")"
        return f"IF(ISNUMBER({o}),{nhanh_so},{nhanh_chu})"
    return None


def _dinh_dang_cot(c: Cot) -> str:
    """Định dạng số của ô nhập liệu trong mẫu — «nhap» so lại: ô số mang định dạng KHÁC ⇒ truy vấn (vd «50%» ⇒ 0.5)."""
    if c.kieu == "ngay":
        return {"date_mdy": "mm/dd/yyyy", "date_ymd": "yyyy-mm-dd"}.get(c.kiem_tra, "dd/mm/yyyy")
    if c.kieu == "ngay_gio":
        return "dd/mm/yyyy hh:mm:ss" if "seconds" in c.kiem_tra else "dd/mm/yyyy hh:mm"
    return {"id": "@", "chu": "@", "van_ban": "@", "gio": "@"}.get(c.kieu, "General")


def _goi_y(c: Cot) -> str:
    phan = []
    if c.kieu == "id":
        phan.append("mã nghiên cứu — không trùng, KHÔNG họ tên/số hồ sơ")
    elif c.kieu == "ma":
        phan.append("; ".join(f"{m}={n}" for m, n in c.lua_chon.items()))
    elif c.kieu == "hop":
        phan.append(f"1 = có chọn «{c.lua_chon.get(c.ma_hop, c.ma_hop)}» · 0 hoặc trống = không")
        if c.toi_da_chon:
            phan.append(f"tối đa {c.toi_da_chon} ô của câu này")
    elif c.kieu in ("so_nguyen", "so"):
        loai = "số nguyên" if c.kieu == "so_nguyen" else "số (gõ theo dấu thập phân của máy, vd 37,5)"
        kh = f" {c.min or '…'}–{c.max or '…'}" if (c.min or c.max) else ""
        phan.append(loai + kh)
    elif c.kieu in ("ngay", "ngay_gio"):
        phan.append("ngày (gõ theo định dạng ô)" + (f" {c.min or '…'}–{c.max or '…'}" if (c.min or c.max) else ""))
    elif c.kieu == "gio":
        phan.append("giờ HH:MM")
    elif c.kieu == "van_ban":
        phan.append("chép nguyên văn — KHÔNG ghi thông tin định danh")
    else:
        phan.append("chữ")
    if c.ma_thieu:
        phan.append("thiếu: " + ", ".join(c.ma_thieu))
    if c.bat_buoc:
        phan.append("BẮT BUỘC")
    if c.nhanh:
        phan.append(f"chỉ khi {c.nhanh}")
    return " | ".join(p for p in phan if p)


def _bam_hang_phu(ws, so_cot: int) -> str:
    """Dấu vân tay hàng nhãn + gợi ý (giữa hàng tên và hàng dữ liệu đầu) — gõ nhầm dữ liệu vào đó sẽ bị phát hiện."""
    gia = [[ws.cell(r, j).value for j in range(1, so_cot + 1)] for r in range(DONG_TEN + 1, DONG_DAU)]
    return hashlib.sha256(json.dumps(gia, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _ten_trang(form: str, da_dung: set[str]) -> str:
    ten = re.sub(r"[\[\]:*?/\\]", "_", form)[:31] or "du_lieu"
    goc, k = ten, 2
    while ten.lower() in {x.lower() for x in da_dung | TRANG_PHU}:
        hau = f"_{k}"
        ten, k = goc[: 31 - len(hau)] + hau, k + 1
    da_dung.add(ten)
    return ten


def _nhom_form(cot: list[Cot]) -> list[tuple[str, list[Cot]]]:
    """[(form, các cột)] theo thứ tự từ điển; cột mã bản ghi đứng đầu MỌI trang."""
    cid = cot[0]
    ra: dict[str, list[Cot]] = {}
    for c in cot[1:]:
        ra.setdefault(c.form, []).append(c)
    if not ra:
        ra[cid.form] = []
    return [(f, [cid, *ds]) for f, ds in ra.items()]


def tao_mau(
    study: str, td_p: Path, mt_p: Path | None, ra: Path, *, so_dong: int = SO_DONG_MAC_DINH, forms: list[str] | None
) -> dict:
    opx = _openpyxl()
    from openpyxl.comments import Comment  # noqa: PLC0415
    from openpyxl.styles import Alignment, Font, PatternFill, Protection  # noqa: PLC0415
    from openpyxl.utils import get_column_letter, quote_sheetname  # noqa: PLC0415
    from openpyxl.workbook.defined_name import DefinedName  # noqa: PLC0415
    from openpyxl.worksheet.datavalidation import DataValidation  # noqa: PLC0415

    td = doc_tu_dien_day_du(td_p)
    mt = SP.doc_ma_thieu(mt_p) if mt_p else []
    cot, bo_qua = ke_hoach_cot(td, mt)
    nhom = _nhom_form(cot)
    if forms:
        nhom = [(f, ds) for f, ds in nhom if f in forms]
        if not nhom:
            raise TuChoi(f"không có biểu mẫu nào khớp --form {','.join(forms)}")
    wb = opx.Workbook()
    wb.properties.creator = "nhap_lieu_excel.py"  # KHÔNG ghi tên người dùng máy vào docProps
    wb.properties.lastModifiedBy = "nhap_lieu_excel.py"
    wb.properties.title = f"Mẫu nhập liệu {study}"
    dm = wb.active
    dm.title = TEN_DM
    dm.sheet_state = "veryHidden"
    dau = Font(bold=True)
    nen_ten = PatternFill("solid", fgColor="D9E2F3")
    nen_goi_y = PatternFill("solid", fgColor="F2F2F2")
    mo_khoa = Protection(locked=False)
    ket_thuc = DONG_DAU + so_dong - 1
    cot_dm = 0
    trang_meta: dict[str, list[str]] = {}
    hang_phu: dict[str, str] = {}
    da_dung: set[str] = set()
    khong_kiem: list[str] = []
    for form, ds in nhom:
        ws = wb.create_sheet(_ten_trang(form, da_dung))
        trang_meta[ws.title] = [c.ten for c in ds]
        vi_tri = {c.ten: get_column_letter(j) for j, c in enumerate(ds, start=1)}
        for j, c in enumerate(ds, start=1):
            chu = get_column_letter(j)
            o_ten = ws.cell(DONG_TEN, j, c.ten)
            o_ten.font, o_ten.fill = dau, nen_ten
            o_nhan = ws.cell(DONG_NHAN, j, c.nhan if c.kieu != "hop" else f"{c.nhan} — {c.lua_chon[c.ma_hop]}")
            o_nhan.alignment = Alignment(wrap_text=True, vertical="top")
            o_gy = ws.cell(DONG_GOI_Y, j, _goi_y(c))
            o_gy.alignment, o_gy.fill = Alignment(wrap_text=True, vertical="top"), nen_goi_y
            if c.ghi_chu:
                o_nhan.comment = Comment(c.ghi_chu[:1000], "nhap_lieu_excel")
            ws.column_dimensions[chu].width = max(12, min(28, len(c.ten) + 2))
            dinh_dang = _dinh_dang_cot(c)
            for r in range(DONG_DAU, ket_thuc + 1):
                o = ws.cell(r, j)
                o.protection = mo_khoa
                o.number_format = dinh_dang
            vung = f"{chu}{DONG_DAU}:{chu}{ket_thuc}"
            o0 = f"{chu}{DONG_DAU}"
            loi_msg = _goi_y(c)[:220]  # Excel: thông báo lỗi ≤ 225 ký tự
            if c.kieu == "ma":
                ds_ma = list(c.lua_chon) + list(c.ma_thieu)
                cot_dm += 1
                cdm = get_column_letter(cot_dm)
                dm.cell(1, cot_dm, c.ten)
                for k, m in enumerate(ds_ma, start=2):
                    dm.cell(k, cot_dm, _so_hay_chu(m))
                ten_ds = f"ds_{c.ten}"
                ref = f"{quote_sheetname(TEN_DM)}!${cdm}$2:${cdm}${len(ds_ma) + 1}"
                wb.defined_names[ten_ds] = DefinedName(ten_ds, attr_text=ref)
                dv = DataValidation(type="list", formula1=ten_ds, allow_blank=True)
            else:
                vung_hop = None
                if c.kieu == "hop" and c.toi_da_chon:
                    anh_em = [x for x in ds if x.kieu == "hop" and x.truong == c.truong]
                    vung_hop = f"${vi_tri[anh_em[0].ten]}{DONG_DAU}:${vi_tri[anh_em[-1].ten]}{DONG_DAU}"
                vung_id = f"${chu}${DONG_DAU}:${chu}${ket_thuc}" if c.kieu == "id" else None
                ct = cong_thuc_kiem(c, o0, vung_hop, vung_id)
                if ct and len(ct) > 255:
                    khong_kiem.append(c.ten)
                    ct = None
                if not ct:
                    continue
                dv = DataValidation(type="custom", formula1=ct, allow_blank=True)
            dv.showErrorMessage, dv.showInputMessage = True, True
            dv.errorStyle = "stop"
            dv.errorTitle, dv.error = "Giá trị không hợp lệ", loi_msg or "Xem hàng 3"
            dv.promptTitle, dv.prompt = c.ten[:32], (c.nhan + " — " + _goi_y(c))[:250]
            ws.add_data_validation(dv)
            dv.add(vung)
        hang_phu[ws.title] = _bam_hang_phu(ws, len(ds))
        ws.row_dimensions[DONG_NHAN].height = 60
        ws.row_dimensions[DONG_GOI_Y].height = 45
        ws.freeze_panes = f"B{DONG_DAU}"
        ws.protection.sheet = True  # khoá HÀNG TIÊU ĐỀ (không mật khẩu); ô nhập liệu đã mở khoá
        for thuoc_tinh in ("sort", "autoFilter", "formatColumns", "formatRows", "insertRows", "deleteRows"):
            setattr(ws.protection, thuoc_tinh, False)
    _trang_tu_dien(wb, cot, bo_qua)
    _trang_huong_dan(wb, study, ket_thuc)
    meta = wb.create_sheet(TEN_META)
    meta.sheet_state = "veryHidden"
    thong_tin = {
        "cong_cu": "tools/nhap_lieu_excel.py",
        "phien_ban_mau": PHIEN_BAN_MAU,
        "study": study,
        "tu_dien": td_p.name,
        "tu_dien_sha256": _sha256(td_p),
        "ma_thieu_sha256": _sha256(mt_p) if mt_p else "",
        "dac_ta_sha256": dau_van_tay_dac_ta(cot),
        "dong_tieu_de": DONG_TEN,
        "dong_du_lieu": DONG_DAU,
        "so_dong": so_dong,
        "tao_luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "trang": trang_meta,
        "hang_phu": hang_phu,
    }
    for k, (khoa, gt) in enumerate(thong_tin.items(), start=1):
        meta.cell(k, 1, khoa)
        meta.cell(k, 2, json.dumps(gt, ensure_ascii=False) if isinstance(gt, dict) else gt)
    wb.move_sheet(wb[TEN_HD], offset=-wb.sheetnames.index(TEN_HD))
    wb.active = wb.sheetnames.index(next(iter(trang_meta)))
    ra.parent.mkdir(parents=True, exist_ok=True)
    tam = ra.with_name(ra.name + ".tmp")
    wb.save(tam)
    tam.replace(ra)
    return {"trang": trang_meta, "bo_qua": bo_qua, "khong_kiem_excel": khong_kiem, "so_cot": len(cot)}


def _trang_tu_dien(wb, cot: list[Cot], bo_qua: list[str]) -> None:
    from openpyxl.styles import Alignment, Font  # noqa: PLC0415

    ws = wb.create_sheet(TEN_TD)
    tieu_de = ["Cột", "Trang", "Nhãn", "Kiểu", "Mã hợp lệ", "Khoảng", "Mã thiếu", "Bắt buộc", "Chỉ hiện khi", "Ghi chú"]
    ws.append(tieu_de)
    for o in ws[1]:
        o.font = Font(bold=True)
    for c in cot:
        ws.append(
            [
                c.ten,
                c.form,
                c.nhan if c.kieu != "hop" else f"{c.nhan} — {c.lua_chon[c.ma_hop]}",
                c.kieu,
                "; ".join(f"{m}={n}" for m, n in c.lua_chon.items())
                if c.kieu == "ma"
                else ("0/1" if c.kieu == "hop" else ""),
                f"{c.min}–{c.max}" if (c.min or c.max) else "",
                "; ".join(f"{m}={n}" for m, n in c.ma_thieu.items()),
                "có" if c.bat_buoc else "",
                c.nhanh,
                c.ghi_chu,
            ]
        )
    for ten in bo_qua:
        ws.append(["", "", f"KHÔNG NHẬP TAY: {ten}"])
    for chu, rong in zip("ABCDEFGHIJ", (24, 16, 48, 10, 40, 12, 30, 9, 26, 50), strict=True):
        ws.column_dimensions[chu].width = rong
    for hang in ws.iter_rows(min_row=2):
        for o in hang:
            o.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"
    ws.protection.sheet = True


def _trang_huong_dan(wb, study: str, ket_thuc: int) -> None:
    from openpyxl.styles import Alignment, Font  # noqa: PLC0415

    ws = wb.create_sheet(TEN_HD)
    dong = [
        f"MẪU NHẬP LIỆU — đề tài {study}",
        "",
        "1. Mỗi biểu mẫu một trang. KHÔNG đổi tên, xoá, chèn hay đổi chỗ cột; KHÔNG sửa hàng 1–3"
        " (đã khoá, không mật khẩu).",
        f"2. Nhập từ hàng {DONG_DAU}, mỗi phiếu một hàng; cột đầu là MÃ NGHIÊN CỨU (không trùng)"
        " — không họ tên, ngày sinh, số điện thoại, số hồ sơ, địa chỉ.",
        "3. Nhập MÃ SỐ của đáp án (xem hàng 3 hoặc trang TU_DIEN), không gõ chữ của đáp án."
        " Câu bỏ trống/không đọc được: ghi đúng mã thiếu của dự án (vd BTR, KDD) — không để trống nếu câu bắt buộc.",
        "4. Câu chọn nhiều đáp án: mỗi đáp án một cột, ghi 1 nếu chọn (0 hoặc để trống nếu không chọn).",
        "5. Số thập phân gõ theo dấu thập phân của máy (Excel tiếng Việt: dấu phẩy, vd 37,5) — Excel từ chối nếu ô"
        " không thành SỐ. Ngày gõ đúng định dạng của ô.",
        f"6. Excel chỉ kiểm khi GÕ trong vùng tới hàng {ket_thuc}; DÁN (paste) sẽ bỏ qua kiểm tra"
        " — công cụ nhập sẽ kiểm lại TOÀN BỘ.",
        "7. Không dùng công thức, không gộp ô, không thêm trang chứa dữ liệu khác.",
        "8. Nhập kép: hai người nhập độc lập hai bản từ CÙNG mẫu này (lưu NGOÀI thư mục repo, vd ~/NhapLieu/), rồi chạy"
        " trong thư mục medical-ebm-automation (Python của môi trường dự án ~/.ebm-venv, KHÔNG phải python3 hệ thống):",
        f"   ~/.ebm-venv/bin/python tools/nhap_lieu_excel.py so-sanh --study {study}"
        " --excel1 ~/NhapLieu/lan1.xlsx --excel2 ~/NhapLieu/lan2.xlsx",
        f"9. Đưa vào hệ thống: ~/.ebm-venv/bin/python tools/nhap_lieu_excel.py nhap --study {study}"
        " --excel ~/NhapLieu/lan1.xlsx --tiep-nhan",
        "",
        "Tệp đã có dữ liệu là dữ liệu nghiên cứu: lưu ở nơi được phép theo kế hoạch quản lý dữ liệu,"
        " không gửi qua mạng xã hội.",
        CAN_KIEM,
    ]
    for d in dong:
        ws.append([d])
    ws["A1"].font = Font(bold=True, size=13)
    ws.column_dimensions["A"].width = 130
    for hang in ws.iter_rows():
        hang[0].alignment = Alignment(wrap_text=True, vertical="top")


# ───────────────────────────── đọc Excel ─────────────────────────────


@dataclass
class PhatHien:
    muc: str
    ma: str
    trang: str
    o: str
    cot: str
    ma_nc: str
    chi_tiet: str
    gia_tri: str = ""

    def dict(self) -> dict:
        return dict(self.__dict__)


def _so_chuoi(v: float) -> str:
    """Số thực ⇒ chuỗi thập phân NGẮN NHẤT khứ hồi được, không ký pháp khoa học (1e-05 ⇒ 0.00001; 18.0 ⇒ 18)."""
    if v.is_integer() and abs(v) < 2**53:
        return str(int(v))
    s = format(Decimal(repr(v)), "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _chuan_chuoi(s: str, dem: dict) -> str:
    goc = s
    s = unicodedata.normalize("NFC", s)
    if s != goc:
        dem["chuan_unicode_nfc"] = dem.get("chuan_unicode_nfc", 0) + 1
    s2 = s.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    s2 = "".join(ch for ch in s2 if ch not in _KHONG_RONG)
    if s2 != s:
        dem["bo_khoang_trang_dac_biet"] = dem.get("bo_khoang_trang_dac_biet", 0) + 1
    s3 = s2.strip()
    if s3 != s2:
        dem["cat_khoang_trang_dau_cuoi"] = dem.get("cat_khoang_trang_dau_cuoi", 0) + 1
    return s3


_DIEU_KHIEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def chuyen_o(
    c: Cot, v, dinh_dang: str, dem: dict, dinh_dang_mau: str | None = None
) -> tuple[str, str | None, str | None]:
    """Giá trị ô openpyxl ⇒ (chuỗi chuẩn, mã phát hiện | None, mức LOI/TRUY_VAN | None). KHÔNG đoán: mơ hồ ⇒ lỗi.

    `dinh_dang_mau`: định dạng mẫu đã gán cho ô (None khi tệp không sinh từ «mau»). Chuẩn hoá KHÔNG đổi nghĩa thì chỉ
    đếm vào `dem`; mọi thứ có thể đã đổi giá trị (định dạng %, số 0 đầu, số quá 15 chữ số…) là phát hiện."""

    def dem_(k: str) -> None:
        dem[k] = dem.get(k, 0) + 1

    if v is None:
        return "", None, None
    if isinstance(v, bool):
        return str(v).upper(), "o_kieu_logic_true_false", LOI
    if isinstance(v, (datetime, date, time)):
        if c.kieu == "ngay":
            if isinstance(v, datetime) and (v.hour, v.minute, v.second, v.microsecond) != (0, 0, 0, 0):
                return v.isoformat(sep=" "), "ngay_co_gio", LOI
            if isinstance(v, time):
                return v.isoformat(), "excel_tu_doi_thanh_gio", LOI
            return (v.date() if isinstance(v, datetime) else v).isoformat(), None, None
        if c.kieu == "ngay_gio" and isinstance(v, datetime):
            if "seconds" in c.kiem_tra:
                return v.strftime("%Y-%m-%d %H:%M:%S"), None, None
            if v.second or v.microsecond:
                return v.isoformat(sep=" "), "ngay_gio_co_giay", LOI
            return v.strftime("%Y-%m-%d %H:%M"), None, None
        if c.kieu == "gio" and isinstance(v, time) and not v.second and not v.microsecond:
            return v.strftime("%H:%M"), None, None
        return str(v), "excel_tu_doi_thanh_ngay_gio", LOI
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v != v:  # NaN
            return "", "o_so_khong_hop_le", LOI
        s = str(v) if isinstance(v, int) else _so_chuoi(v)
        dd = dinh_dang or "General"
        if c.kieu in ("chu", "van_ban", "gio"):
            return s, "so_trong_cot_chu", TRUY_VAN  # ô chữ thành SỐ: số 0 đầu/định dạng có thể đã mất
        if c.kieu == "id":
            if isinstance(v, float) and not v.is_integer():
                return s, "ma_nghien_cuu_la_so_le", LOI
            return s, "ma_nghien_cuu_luu_dang_so", TRUY_VAN
        if c.kieu in ("ngay", "ngay_gio"):
            if s in c.ma_thieu:
                return s, None, None  # mã thiếu dạng số (khai qua mẫu glob) ở cột ngày
            return s, "ngay_luu_dang_so", LOI
        if "%" in dd:
            return s, "dinh_dang_phan_tram", LOI  # «50%» được Excel lưu thành 0.5
        if dinh_dang_mau is not None and dd != dinh_dang_mau:
            return s, "dinh_dang_o_khac_mau", TRUY_VAN
        if dinh_dang_mau is None and re.search(r"#[,.]##", dd):
            return s, "dinh_dang_hang_nghin", TRUY_VAN  # «1.500» trên máy tiếng Việt ⇒ 1500
        return s, None, None
    s = _chuan_chuoi(str(v), dem)
    if _DIEU_KHIEN.search(s):
        return _DIEU_KHIEN.sub("", s), "ky_tu_dieu_khien", LOI
    if s.startswith("#") and s.upper() in ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NUM!", "#NAME?", "#NULL!"):
        return s, "o_loi_excel", LOI
    if c.kieu not in ("chu", "van_ban") and _co_chu_so_khong_ascii(s):
        return s, "chu_so_khong_ascii", LOI  # «６０»: SPSS đọc thành SYSMIS, pandas đọc thành chữ
    if "\n" in s:
        return s, "xuong_dong_trong_o", TRUY_VAN  # SPSS GET DATA tách ô nhiều dòng thành HAI ca
    if s and c.kieu not in ("id", "chu", "van_ban", "gio"):
        hop_le = [*c.lua_chon, *c.ma_thieu] if c.kieu == "ma" else list(c.ma_thieu)
        khop = [m for m in hop_le if m.casefold() == s.casefold()]
        if s not in hop_le and len(khop) == 1:  # «btr» = «BTR»: Excel kiểm nhập & bộ làm sạch đều không phân biệt
            s = khop[0]
            dem_("chuan_hoa_thuong_ma")
    if c.kieu in ("so_nguyen", "so") and s and s not in c.ma_thieu:
        if re.fullmatch(r"[+-]?[0-9]+,[0-9]+", s):
            return s, "so_dung_dau_phay", LOI
        if _SO_CHU.fullmatch(s):
            if vuot_do_chinh_xac(s):
                return s, "so_vuot_do_chinh_xac", TRUY_VAN  # > 15 chữ số có nghĩa: SPSS/R/pandas lưu số KHÁC
            dem_("so_luu_dang_chu")
    if c.kieu == "ma" and s and s not in c.lua_chon and s not in c.ma_thieu and _SO_CHU.fullmatch(s):
        x = _so_chat(s)
        if x is not None and x.is_integer() and str(int(x)) in c.lua_chon and s != str(int(x)):
            return s, "ma_so_viet_khac", LOI  # «01», «1.0» gõ dạng chữ: không tự đổi thành «1»
    if c.kieu in ("ngay", "ngay_gio") and s and s not in c.ma_thieu:
        return s, "ngay_luu_dang_chu", LOI  # «12/03/2026» mơ hồ ngày/tháng ⇒ gõ lại thành ô ngày thật
    return s, None, None


@dataclass
class Bang:
    """Kết quả ĐỌC một tệp Excel: giá trị đã chuẩn hoá theo mã nghiên cứu, kèm vị trí ô để báo cáo."""

    cot: list[Cot]
    hang: dict[str, dict[str, str]]  # mã NC → {cột: giá trị}
    vi_tri: dict[str, dict[str, str]]  # mã NC → {cột: "Trang!B12"}
    trang_cua_ma: dict[str, set[str]]  # mã NC → các trang có hàng
    phat_hien: list[PhatHien]
    dem: dict
    meta: dict
    cot_co: list[str]  # cột thật sự có trong tệp, theo thứ tự từ điển

    def loi(self) -> list[PhatHien]:
        return [p for p in self.phat_hien if p.muc == LOI]


def _doc_meta(wb) -> dict:
    if TEN_META not in wb.sheetnames:
        return {}
    ra = {}
    for k, v in wb[TEN_META].iter_rows(min_col=1, max_col=2, values_only=True):
        if k:
            ra[str(k)] = v
    for khoa in ("trang", "hang_phu"):
        if isinstance(ra.get(khoa), str):
            try:
                ra[khoa] = json.loads(ra[khoa])
            except ValueError:
                ra[khoa] = {}
    return ra


def doc_excel(
    p: Path,
    cot: list[Cot],
    *,
    dong_tieu_de: int | None = None,
    dong_du_lieu: int | None = None,
    cho_phep_cong_thuc: bool = False,
    dac_ta_hien: str | None = None,
    chap_nhan_tu_dien_moi: bool = False,
) -> Bang:
    opx = _openpyxl()
    if p.suffix.lower() not in (".xlsx", ".xlsm"):
        raise TuChoi(f"chỉ đọc .xlsx/.xlsm (tệp .xls cũ: mở bằng Excel rồi Lưu thành .xlsx): {p.name}")
    if not p.exists():
        raise TuChoi(f"không thấy tệp: {p}")
    try:
        wb = opx.load_workbook(p, data_only=False)
    except Exception as e:  # noqa: BLE001 — tệp hỏng/khoá mật khẩu: báo rõ, không đổ vết
        raise TuChoi(f"không mở được {p.name} bằng openpyxl ({type(e).__name__}) — tệp hỏng hoặc có mật khẩu?") from e
    wb_gt = None
    meta = _doc_meta(wb)
    ph: list[PhatHien] = []
    dem: dict = {}
    theo_ten = {c.ten.lower(): c for c in cot}
    truong_hop = {c.truong.lower() for c in cot if c.kieu == "hop"}
    cid = cot[0]
    if meta:
        if dac_ta_hien and meta.get("dac_ta_sha256") and meta["dac_ta_sha256"] != dac_ta_hien:
            if not chap_nhan_tu_dien_moi:
                raise TuChoi(
                    "tệp được sinh từ một đặc tả từ điển KHÁC đặc tả hiện tại (biến/mã/khoảng/mã thiếu đã đổi sau khi "
                    "tạo mẫu). Sinh mẫu mới và chép dữ liệu sang, hoặc dùng --chap-nhan-tu-dien-moi để kiểm theo từ "
                    "điển hiện tại (mọi khác biệt sẽ hiện thành lỗi/truy vấn)."
                )
            ph.append(PhatHien(CANH_BAO, "mau_tu_tu_dien_cu", "", "", "", "", "kiểm theo từ điển HIỆN TẠI"))
        dtd = int(meta.get("dong_tieu_de") or DONG_TEN)
        ddl = int(meta.get("dong_du_lieu") or DONG_DAU)
        so_dong_mau = int(meta.get("so_dong") or 0)
        trang_du_lieu = [t for t in (meta.get("trang") or {}) if t in wb.sheetnames]
        thieu_trang = [t for t in (meta.get("trang") or {}) if t not in wb.sheetnames]
        for t in thieu_trang:
            ph.append(PhatHien(LOI, "mat_trang_mau", t, "", "", "", "trang của mẫu đã bị xoá/đổi tên"))
    else:
        dtd = dong_tieu_de or 1
        ddl = dong_du_lieu or dtd + 1
        so_dong_mau = 0
        trang_du_lieu = []
        for ws in wb.worksheets:
            if ws.title in TRANG_PHU:
                continue
            ten = [str(o.value).strip().lower() for o in ws[dtd] if o.value is not None]
            if any(t in theo_ten for t in ten):
                trang_du_lieu.append(ws.title)  # trang ẨN có tiêu đề biến vẫn được đọc (không bỏ dữ liệu lặng lẽ)
                if ws.sheet_state != "visible":
                    ph.append(PhatHien(CANH_BAO, "trang_an", ws.title, "", "", "", "trang đang ẨN (vẫn được đọc)"))
        if not trang_du_lieu:
            raise TuChoi(
                f"không trang nào có hàng tiêu đề (hàng {dtd}) chứa tên biến của từ điển — dùng mẫu của «mau» hoặc "
                "--dong-tieu-de/--dong-du-lieu"
            )
    if ddl <= dtd:
        raise TuChoi("hàng dữ liệu phải nằm dưới hàng tiêu đề")
    for ws in wb.worksheets:
        if ws.title not in trang_du_lieu and ws.title not in TRANG_PHU:
            co_gt = any(v is not None for hang in ws.iter_rows(values_only=True) for v in hang)
            if co_gt and meta:  # mẫu: mọi dữ liệu phải ở trang của mẫu — trang chép thêm («phieu (2)») KHÔNG được đọc
                ph.append(
                    PhatHien(LOI, "trang_la_co_du_lieu", ws.title, "", "", "", "trang ngoài mẫu có dữ liệu — KHÔNG đọc")
                )
            elif co_gt:
                ph.append(
                    PhatHien(
                        CANH_BAO, "trang_la_bi_bo_qua", ws.title, "", "", "", "trang không có tiêu đề biến, KHÔNG đọc"
                    )
                )
    hang: dict[str, dict[str, str]] = {}
    vi_tri: dict[str, dict[str, str]] = {}
    trang_cua_ma: dict[str, set[str]] = {}
    cot_thay: dict[str, str] = {}  # tên cột → trang
    for t in trang_du_lieu:
        ws = wb[t]
        tieu_de: dict[int, Cot] = {}
        bam_mau = (meta.get("hang_phu") or {}).get(t) if meta else None
        if bam_mau and _bam_hang_phu(ws, len((meta.get("trang") or {}).get(t, []))) != bam_mau:
            ph.append(
                PhatHien(
                    LOI,
                    "hang_tieu_de_bi_sua",
                    t,
                    f"{DONG_TEN + 1}:{DONG_DAU - 1}",
                    "",
                    "",
                    f"hàng {DONG_TEN + 1}–{DONG_DAU - 1} (nhãn/gợi ý) đã bị sửa — dữ liệu gõ vào đó KHÔNG được đọc",
                )
            )
        for o in ws[dtd]:
            if o.value is None or str(o.value).strip() == "":
                continue
            ten = unicodedata.normalize("NFC", str(o.value)).strip()
            c = theo_ten.get(ten.lower())
            if c is None:
                ma = "cot_checkbox_chua_tach" if ten.lower() in truong_hop else "cot_khong_co_trong_tu_dien"
                ph.append(PhatHien(LOI, ma, t, o.coordinate, ten, "", "tiêu đề không khớp cột nhập liệu của từ điển"))
                continue
            if c.ten != ten:
                ph.append(PhatHien(CANH_BAO, "tieu_de_khac_hoa_thuong", t, o.coordinate, c.ten, "", f"ghi «{ten}»"))
            if c.ten in cot_thay and (c.kieu != "id" or cot_thay[c.ten] == t):
                ph.append(PhatHien(LOI, "cot_trung", t, o.coordinate, c.ten, "", f"đã có ở trang {cot_thay[c.ten]}"))
                continue
            cot_thay.setdefault(c.ten, t)
            tieu_de[o.column] = c
        if cid not in tieu_de.values():
            ph.append(
                PhatHien(LOI, "thieu_cot_ma_nghien_cuu", t, "", cid.ten, "", "mỗi trang phải có cột mã nghiên cứu")
            )
            continue
        col_id = next(k for k, c in tieu_de.items() if c is cid)
        # Ô trống có tiêu đề rỗng nhưng có dữ liệu bên dưới ⇒ cột không tên
        for vung in ws.merged_cells.ranges:
            if vung.max_row >= ddl:
                ph.append(
                    PhatHien(LOI, "o_gop", t, str(vung), "", "", "ô gộp trong vùng dữ liệu — tách ô rồi nhập lại")
                )
        for k, cd in ws.column_dimensions.items():
            if cd.hidden:
                ph.append(PhatHien(CANH_BAO, "cot_an", t, k, "", "", "cột đang ẩn (vẫn được đọc)"))
        cot_khong_ten: set[int] = set()
        for hang_o in ws.iter_rows(min_row=ddl):
            co = [o for o in hang_o if o.value is not None and not (isinstance(o.value, str) and o.value.strip() == "")]
            if not co:
                continue
            r = hang_o[0].row
            for o in co:
                if o.column not in tieu_de and o.column not in cot_khong_ten:
                    cot_khong_ten.add(o.column)
                    ph.append(
                        PhatHien(
                            LOI,
                            "du_lieu_o_cot_khong_ten",
                            t,
                            o.coordinate,
                            "",
                            "",
                            "ô có dữ liệu dưới cột không có tiêu đề hợp lệ",
                        )
                    )
            if ws.row_dimensions[r].hidden:
                ph.append(PhatHien(CANH_BAO, "hang_an", t, f"{r}", "", "", "hàng đang ẩn (vẫn được đọc)"))
            if so_dong_mau and r > ddl + so_dong_mau - 1:
                dem["hang_ngoai_vung_kiem_excel"] = dem.get("hang_ngoai_vung_kiem_excel", 0) + 1
            gt_hang: dict[str, str] = {}
            vt_hang: dict[str, str] = {}
            for o in hang_o:
                c = tieu_de.get(o.column)
                if c is None:
                    continue
                v = o.value
                if o.data_type == "f":
                    if not cho_phep_cong_thuc:
                        ph.append(
                            PhatHien(
                                LOI, "o_cong_thuc", t, o.coordinate, c.ten, "", "ô nhập liệu không được là công thức"
                            )
                        )
                        continue
                    if wb_gt is None:
                        wb_gt = opx.load_workbook(p, data_only=True)
                    v = wb_gt[t][o.coordinate].value
                    if v is None:
                        ph.append(
                            PhatHien(
                                LOI,
                                "cong_thuc_chua_tinh",
                                t,
                                o.coordinate,
                                c.ten,
                                "",
                                "công thức chưa có giá trị lưu sẵn — mở bằng Excel, lưu lại",
                            )
                        )
                        continue
                if o.data_type == "e":
                    ph.append(PhatHien(LOI, "o_loi_excel", t, o.coordinate, c.ten, "", f"ô báo lỗi {v}"))
                    continue
                s, ma, muc = chuyen_o(c, v, o.number_format, dem, _dinh_dang_cot(c) if meta else None)
                hien = "" if c.kieu in KIEU_CHU - {"id"} else s
                if muc:
                    chi_tiet = _GIAI_THICH.get(ma, ma)
                    if ma in ("dinh_dang_o_khac_mau", "dinh_dang_hang_nghin", "dinh_dang_phan_tram"):
                        chi_tiet += f" (định dạng ô «{o.number_format}»)"
                    ph.append(PhatHien(muc, ma, t, o.coordinate, c.ten, "", chi_tiet, hien))
                gt_hang[c.ten] = s
                vt_hang[c.ten] = f"{t}!{o.coordinate}"
            ma_nc = gt_hang.get(cid.ten, "")
            if not ma_nc:
                ph.append(
                    PhatHien(
                        LOI,
                        "thieu_ma_nghien_cuu",
                        t,
                        f"{ws.cell(r, col_id).coordinate}",
                        cid.ten,
                        "",
                        "hàng có dữ liệu nhưng trống mã nghiên cứu",
                    )
                )
                continue
            for c in tieu_de.values():
                if c.kieu == "hop" and gt_hang.get(c.ten, "") == "":
                    gt_hang[c.ten] = "0"  # quy ước REDCap: ô checkbox không chọn = 0
                    vt_hang.setdefault(
                        c.ten, f"{t}!{ws.cell(r, next(k for k, x in tieu_de.items() if x is c)).coordinate}"
                    )
                    dem["o_checkbox_trong_ghi_0"] = dem.get("o_checkbox_trong_ghi_0", 0) + 1
            if t in trang_cua_ma.get(ma_nc, set()):
                ph.append(
                    PhatHien(
                        LOI,
                        "trung_ma_nghien_cuu",
                        t,
                        vt_hang[cid.ten].split("!")[1],
                        cid.ten,
                        ma_nc,
                        "mã nghiên cứu xuất hiện hai lần trong cùng trang",
                    )
                )
                continue
            trang_cua_ma.setdefault(ma_nc, set()).add(t)
            hang.setdefault(ma_nc, {}).update(gt_hang)
            vi_tri.setdefault(ma_nc, {}).update(vt_hang)
    for k, p_ in enumerate(ph):  # gắn mã nghiên cứu cho phát hiện cấp ô đã biết vị trí
        if not p_.ma_nc and p_.o and p_.trang:
            for ma_nc, vt in vi_tri.items():
                if f"{p_.trang}!{p_.o}" in vt.values():
                    ph[k].ma_nc = ma_nc
                    break
    theo_thuong: dict[str, list[str]] = {}
    for m in hang:
        theo_thuong.setdefault(m.casefold(), []).append(m)
    for ds in theo_thuong.values():
        if len(ds) > 1:  # Excel (COUNTIF) coi là TRÙNG; máy không đoán đây là hai người khác nhau
            chi_tiet = "mã nghiên cứu chỉ khác hoa/thường: " + ", ".join(ds)
            ph.append(PhatHien(LOI, "trung_ma_khac_hoa_thuong", "", "", cid.ten, ds[0], chi_tiet))
    cot_co = [c.ten for c in cot if c.ten in cot_thay]
    return Bang(cot, hang, vi_tri, trang_cua_ma, ph, dem, meta, cot_co)


_GIAI_THICH = {
    "o_kieu_logic_true_false": "Excel lưu thành TRUE/FALSE — nhập lại đúng mã",
    "ngay_co_gio": "ô ngày có cả giờ",
    "ngay_gio_co_giay": "ô ngày-giờ có giây",
    "excel_tu_doi_thanh_gio": "Excel tự đổi thành giờ",
    "excel_tu_doi_thanh_ngay_gio": "Excel tự đổi giá trị gõ vào thành NGÀY/GIỜ (vd «1/2», «3-4») — nhập lại đúng mã",
    "o_so_khong_hop_le": "số không hợp lệ",
    "ma_nghien_cuu_la_so_le": "mã nghiên cứu là số lẻ",
    "ngay_luu_dang_so": "ô ngày đang là SỐ — định dạng lại ô thành ngày",
    "ky_tu_dieu_khien": "có ký tự điều khiển ẩn",
    "o_loi_excel": "ô báo lỗi của Excel",
    "so_dung_dau_phay": "số dạng chữ dùng dấu phẩy («1,5») — không đoán 1.5 hay 15; gõ lại số",
    "ma_so_viet_khac": "mã gõ dạng chữ khác mã của từ điển («01», «1.0») — gõ lại đúng mã",
    "ngay_luu_dang_chu": "ngày đang là CHỮ (mơ hồ ngày/tháng) — gõ lại thành ô ngày thật",
    "so_trong_cot_chu": "ô chữ bị Excel đổi thành SỐ — số 0 đầu có thể đã mất; đối chiếu phiếu, gõ lại dạng chữ",
    "ma_nghien_cuu_luu_dang_so": "mã nghiên cứu lưu dạng SỐ — số 0 đầu có thể đã mất; đối chiếu phiếu",
    "dinh_dang_phan_tram": "ô định dạng PHẦN TRĂM: Excel lưu «50%» thành 0.5 — gõ lại số trong ô định dạng General",
    "dinh_dang_o_khac_mau": "ô số mang định dạng khác mẫu — kiểm giá trị thật (Excel có thể đã đổi khi gõ)",
    "dinh_dang_hang_nghin": "ô số định dạng hàng nghìn — «1.500» trên máy tiếng Việt là 1500; đối chiếu phiếu",
    "chu_so_khong_ascii": "chữ số không phải ASCII (vd chữ số toàn khổ «６０») — gõ lại",
    "xuong_dong_trong_o": "ô có XUỐNG DÒNG (Alt+Enter) — SPSS tách thành hai ca; thay xuống dòng bằng « / »",
    "so_vuot_do_chinh_xac": "số quá 15 chữ số có nghĩa — SPSS/R/pandas lưu số KHÁC; nếu là mã, nhập dạng chữ",
}


# ───────────────────────────── kiểm giá trị ─────────────────────────────


def kiem_gia_tri(bang: Bang, luat_dq: list[dict]) -> None:
    """Kiểm từng giá trị như REDCap kiểm lúc nhập (danh mục, khoảng, bắt buộc, logic nhánh, @MAXCHECKED,
    @NOMISSING) + luật DQ. Kết quả là TRUY VẤN — đối chiếu phiếu gốc, không tự sửa."""
    co = set(bang.cot_co)
    cot = [c for c in bang.cot if c.ten in co]
    nhanh_khong_ho: dict[str, list] = {}  # cột → [lý do đầu tiên, số hàng]
    dq_khong_ho: dict[str, list] = {}
    nhom_hop: dict[str, list[Cot]] = {}
    for c in cot:
        if c.kieu == "hop":
            nhom_hop.setdefault(c.truong, []).append(c)
    for ma_nc, dong in bang.hang.items():
        vt = bang.vi_tri.get(ma_nc, {})

        def tv(ma: str, c: Cot, chi_tiet: str, gia: str = "", *, _vt=vt, _ma=ma_nc) -> None:
            noi = _vt.get(c.ten, "")
            trang, _, o = noi.partition("!")
            hien = "" if c.kieu in KIEU_CHU else gia
            bang.phat_hien.append(PhatHien(TRUY_VAN, ma, trang, o, c.ten, _ma, chi_tiet, hien))

        for c in cot:
            if c.kieu == "id" or c.ten not in dong:
                continue  # cột của trang mà mã này chưa nhập
            v = dong.get(c.ten, "")
            hien_thi = True
            if c.nhanh:
                try:
                    hien_thi = danh_gia_logic(c.nhanh, dong)
                except LogicKhongHo as e:
                    nhanh_khong_ho.setdefault(c.ten, [str(e), 0])[1] += 1
                    hien_thi = None
            if v == "":
                if c.bat_buoc and hien_thi:
                    goi_y = f" (ghi mã thiếu {'/'.join(c.ma_thieu)} nếu phiếu bỏ trống)" if c.ma_thieu else ""
                    tv("thieu_bat_buoc", c, "câu bắt buộc bị trống" + goi_y)
                continue
            # ô chọn nhiều trống được ghi 0 (quy ước REDCap) — đó KHÔNG phải «có giá trị khi câu bị ẩn»
            bo_qua_hop_0 = c.kieu == "hop" and v == "0"
            if hien_thi is False and not bo_qua_hop_0:
                tv("co_gia_tri_khi_bi_an", c, f"có giá trị dù logic nhánh «{c.nhanh}» đang ẩn câu này", v)
            if v in c.ma_thieu:
                continue
            if c.kieu == "ma" and v not in c.lua_chon:
                tv("ngoai_danh_muc", c, "mã ngoài danh mục: " + ", ".join(list(c.lua_chon) + list(c.ma_thieu)), v)
            elif c.kieu == "hop" and v not in ("0", "1"):
                tv("checkbox_khong_phai_0_1", c, "ô chọn nhiều chỉ nhận 0/1", v)
            elif c.kieu in ("so_nguyen", "so"):
                x = _so_chat(v)
                if x is None:
                    tv("khong_phai_so", c, "không phải số" + (", không phải mã thiếu" if c.ma_thieu else ""), v)
                    continue
                if c.kieu == "so_nguyen" and not x.is_integer():
                    tv("khong_phai_so_nguyen", c, "không phải số nguyên — không tự làm tròn", v)
                if c.min and _so_chat(c.min) is not None and x < float(c.min):
                    tv("duoi_khoang", c, f"nhỏ hơn {c.min}", v)
                if c.max and _so_chat(c.max) is not None and x > float(c.max):
                    tv("tren_khoang", c, f"lớn hơn {c.max}", v)
            elif c.kieu in ("ngay", "ngay_gio"):
                for gh, ten_ma, op in ((c.min, "truoc_khoang", "<"), (c.max, "sau_khoang", ">")):
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", gh or "") and ((v[:10] < gh) if op == "<" else (v[:10] > gh)):
                        tv(ten_ma, c, f"ngoài khoảng {c.min or '…'}–{c.max or '…'}", v)
            elif c.kieu == "gio" and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v):
                tv("gio_sai_dinh_dang", c, "giờ phải dạng HH:MM", v)
        for truong, ds in nhom_hop.items():
            tran = ds[0].toi_da_chon
            if tran and sum(dong.get(c.ten) == "1" for c in ds) > tran:
                tv("vuot_toi_da_chon", ds[0], f"chọn quá {tran} đáp án ở {truong}")
        for luat in luat_dq:
            try:
                if danh_gia_logic(luat["bieu_thuc_redcap"], dong):
                    c0 = next((c for c in cot if f"[{c.truong}" in luat["bieu_thuc_redcap"]), bang.cot[0])
                    tv(f"luat_{luat['ma_luat']}", c0, f"{luat['ma_luat']}: {luat['mo_ta']}")
            except LogicKhongHo as e:
                dq_khong_ho.setdefault(luat["ma_luat"], [str(e), 0])[1] += 1
    n = len(bang.hang)
    for ten, (ly_do, k) in nhanh_khong_ho.items():
        bang.phat_hien.append(
            PhatHien(CANH_BAO, "logic_nhanh_khong_danh_gia_duoc", "", "", ten, "", f"{k}/{n} hàng: {ly_do}")
        )
    for ma, (ly_do, k) in dq_khong_ho.items():
        bang.phat_hien.append(
            PhatHien(CANH_BAO, "luat_dq_khong_danh_gia_duoc", "", "", ma, "", f"{k}/{n} hàng: {ly_do}")
        )


# ───────────────────────────── ghi CSV + tự kiểm ─────────────────────────────


def ghi_csv(bang: Bang, p: Path) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(bang.cot_co)
    for ma_nc in bang.hang:
        w.writerow([bang.hang[ma_nc].get(c, "") for c in bang.cot_co])
    tam = p.with_name(p.name + ".tmp")
    tam.write_text(buf.getvalue(), encoding="utf-8", newline="")
    tam.replace(p)


def tu_kiem_csv(bang: Bang, p: Path) -> tuple[list[str], list[str]]:
    """Đọc lại CSV bằng ĐÚNG các đường đọc phía sau và so từng ô với bảng trong bộ nhớ.
    Trả (lỗi, các đường đọc ĐÃ THẬT SỰ kiểm) — không khai đã kiểm pandas khi máy không có pandas."""
    loi: list[str] = []
    da_kiem = ["csv"]
    mong = [[c for c in bang.cot_co]] + [[bang.hang[m].get(c, "") for c in bang.cot_co] for m in bang.hang]
    with open(p, encoding="utf-8", newline="") as f:
        doc = list(csv.reader(f))
    if doc != mong:
        loi.append("đọc lại CSV bằng csv của Python không trùng từng ô với dữ liệu đã đọc từ Excel")
    try:
        import clean_research_dataset as CRD  # noqa: PLC0415

        cot_crd, hang_crd, _ = CRD._read_csv(p)
        da_kiem.append("bộ làm sạch")
        if cot_crd != mong[0] or [[r.get(c, "") for c in cot_crd] for r in hang_crd] != mong[1:]:
            loi.append(
                "bộ làm sạch (clean_research_dataset) đọc CSV KHÁC dữ liệu gốc — csv.Sniffer đoán sai dấu phân cách"
            )
    except ImportError as e:
        loi.append(f"không tự kiểm được đường đọc của bộ làm sạch ({e}) — KHÔNG coi là đạt")
    try:
        import pandas as pd  # noqa: PLC0415

        df = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        da_kiem.append("pandas")
        if list(df.columns) != mong[0] or df.values.tolist() != mong[1:]:
            loi.append("pandas đọc CSV (dtype=str) không trùng từng ô với dữ liệu gốc")
    except ImportError:
        pass
    return loi, da_kiem


def o_bi_pandas_coi_la_thieu(bang: Bang) -> list[tuple[str, str]]:
    """Ô có giá trị mà pandas.read_csv mặc định (run_stats_analysis) sẽ đọc thành THIẾU (vd «NA», «None»)."""
    try:
        from pandas._libs.parsers import STR_NA_VALUES  # noqa: PLC0415
    except ImportError:
        STR_NA_VALUES = NA_PANDAS_DU_PHONG  # noqa: N806 — máy không có pandas: dùng bản chép, không bỏ kiểm
    ra = []
    for ma_nc, dong in bang.hang.items():
        for c, v in dong.items():
            if v and v in STR_NA_VALUES:
                ra.append((ma_nc, c))
    return ra


def kiem_trang_thieu(bang: Bang) -> None:
    """Mã nghiên cứu có ở trang này mà vắng ở trang khác ⇒ TRUY VẤN từng mã (gõ lệch «BN001»/«BN00l» tách MỘT người
    thành HAI bản ghi nửa trống — câu bắt buộc của trang vắng sẽ không được kiểm)."""
    moi_trang = sorted({t for v in bang.trang_cua_ma.values() for t in v})
    if len(moi_trang) < 2:
        return
    for ma_nc, co in bang.trang_cua_ma.items():
        thieu = [t for t in moi_trang if t not in co]
        if thieu:
            bang.phat_hien.append(
                PhatHien(
                    TRUY_VAN,
                    "ma_nc_thieu_trang",
                    sorted(co)[0],
                    "",
                    bang.cot[0].ten,
                    ma_nc,
                    "mã có ở trang "
                    + ", ".join(sorted(co))
                    + " nhưng VẮNG ở trang "
                    + ", ".join(thieu)
                    + " — gõ lệch mã hoặc chưa nhập trang đó",
                )
            )


# ───────────────────────────── lệnh ─────────────────────────────


def _ngoai_repo(ra: Path) -> None:
    repo = SP._trong_repo_git(ra if ra.exists() else ra.parent)
    if repo:
        raise TuChoi(
            f"thư mục ra nằm TRONG một repo git ({repo}) — dữ liệu chưa qua cổng tiếp nhận phải ở ngoài repo"
            " (chọn --ra khác)"
        )


def lenh_mau(args) -> int:
    td_p, mt_p = tim_tu_dien(args.study, args.dictionary, args.ma_thieu)
    d = SP.thu_muc_de_tai(args.study)
    ra = Path(args.ra).expanduser().resolve() if args.ra else d / "nhap_lieu" / f"MAU_NHAP_LIEU_{args.study}.xlsx"
    if ra.suffix.lower() != ".xlsx":
        raise TuChoi("tệp mẫu phải có đuôi .xlsx")
    if ra.exists():
        if not args.ghi_de:
            raise TuChoi(f"đã có {ra} — KHÔNG ghi đè (có thể đã có dữ liệu). Chọn --ra khác hoặc --ghi-de")
        cot, _ = ke_hoach_cot(doc_tu_dien_day_du(td_p), SP.doc_ma_thieu(mt_p) if mt_p else [])
        try:
            cu = doc_excel(ra, cot, chap_nhan_tu_dien_moi=True)
            co_du_lieu = bool(cu.hang or cu.loi())
        except TuChoi:
            co_du_lieu = True  # không đọc được tệp cũ ⇒ không dám ghi đè
        if co_du_lieu:
            raise TuChoi(f"{ra.name} có (hoặc có thể có) dữ liệu — không ghi đè kể cả khi có --ghi-de; chọn --ra khác")
    if args.so_dong < 1 or args.so_dong > 20000:
        raise TuChoi("--so-dong phải trong 1–20000")
    kq = tao_mau(args.study, td_p, mt_p, ra, so_dong=args.so_dong, forms=args.form.split(",") if args.form else None)
    print(f"✓ Mẫu nhập liệu: {ra}")
    for t, ds in kq["trang"].items():
        print(f"   · trang «{t}»: {len(ds)} cột (gồm cột mã nghiên cứu)")
    for b in kq["bo_qua"]:
        print(f"   ⚪ không nhập tay: {b}")
    if kq["khong_kiem_excel"]:
        print(
            "   ⚠ công thức kiểm quá dài, Excel không kiểm (công cụ «nhap» vẫn kiểm): "
            + ", ".join(kq["khong_kiem_excel"])
        )
    print(f"   Từ điển: {td_p.name}" + (f" · mã thiếu: {mt_p.name}" if mt_p else " · KHÔNG có tệp mã thiếu"))
    print("→ Chép mẫu ra NGOÀI repo (vd ~/NhapLieu/lan1.xlsx, lan2.xlsx) rồi nhập. Nhập xong:")
    print(f"   {_py()} tools/nhap_lieu_excel.py nhap --study {args.study} --excel ~/NhapLieu/lan1.xlsx")
    print(CAN_KIEM)
    return MA_OK


def _bang_tu_args(args, p: Path) -> tuple[Bang, list[Cot], Path, Path | None]:
    td_p, mt_p = tim_tu_dien(args.study, args.dictionary, args.ma_thieu)
    cot, _ = ke_hoach_cot(doc_tu_dien_day_du(td_p), SP.doc_ma_thieu(mt_p) if mt_p else [])
    bang = doc_excel(
        p,
        cot,
        dong_tieu_de=args.dong_tieu_de,
        dong_du_lieu=args.dong_du_lieu,
        cho_phep_cong_thuc=args.cho_phep_cong_thuc,
        dac_ta_hien=dau_van_tay_dac_ta(cot),
        chap_nhan_tu_dien_moi=args.chap_nhan_tu_dien_moi,
    )
    return bang, cot, td_p, mt_p


def _in_phat_hien(ds: list[PhatHien], toi_da: int = 40) -> None:
    for p in ds[:toi_da]:
        noi = f"{p.trang}!{p.o}" if p.trang and p.o else (p.trang or "")
        gia = f" [giá trị: {p.gia_tri}]" if p.gia_tri else ""
        ma_nc = f" mã NC {p.ma_nc}" if p.ma_nc else ""
        print(f"   {noi:<22} {p.cot:<26}{ma_nc} — {p.chi_tiet}{gia}")
    if len(ds) > toi_da:
        print(f"   … còn {len(ds) - toi_da} mục — xem báo cáo")


def _ghi_bao_cao(ra: Path, ten: str, bang: Bang, tom: dict) -> None:
    (ra / f"{ten}_bao_cao_nhap.json").write_text(
        json.dumps({**tom, "phat_hien": [p.dict() for p in bang.phat_hien]}, ensure_ascii=False, indent=1),
        encoding="utf-8",
        newline="\n",
    )
    dong = [
        f"# Báo cáo nhập Excel — {tom['study']}",
        "",
        f"- Tệp: {tom['excel']} · SHA-256 `{tom['excel_sha256'][:16]}…`",
    ]
    dong += [
        f"- {tom['so_ma_nghien_cuu']} mã nghiên cứu · {len(bang.cot_co)} cột · trạng thái **{tom['trang_thai']}**",
        f"- Lỗi: {tom['so_loi']} · truy vấn: {tom['so_truy_van']} · cảnh báo: {tom['so_canh_bao']}",
        "",
        "| Mức | Mã | Ô | Cột | Mã NC | Chi tiết | Giá trị |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in bang.phat_hien:
        o = f"{p.trang}!{p.o}" if p.trang and p.o else p.trang
        dong.append(f"| {p.muc} | {p.ma} | {o} | {p.cot} | {p.ma_nc} | {p.chi_tiet.replace('|', '/')} | {p.gia_tri} |")
    dong += ["", f"Chuẩn hoá đã làm (đếm ô): {json.dumps(bang.dem, ensure_ascii=False)}", "", CAN_KIEM, ""]
    (ra / f"{ten}_bao_cao_nhap.md").write_text("\n".join(dong), encoding="utf-8", newline="\n")


def lenh_nhap(args) -> int:
    p = Path(args.excel).expanduser().resolve()
    ra = Path(args.ra).expanduser().resolve() if args.ra else p.parent / f"{p.stem}_csv"
    _ngoai_repo(ra)
    bang, cot, td_p, mt_p = _bang_tu_args(args, p)
    d = SP.thu_muc_de_tai(args.study)
    luat_p = Path(args.luat_dq).expanduser() if args.luat_dq else d / "_luat-dq.csv"
    luat = doc_luat_dq(luat_p)
    if not bang.loi():
        kiem_gia_tri(bang, luat)
    kiem_trang_thieu(bang)
    form_co = {c.form for c in cot if c.ten in bang.cot_co and c.kieu != "id"}
    for ma, muc, cung_form in (
        ("cot_cua_trang_vang_mat", CANH_BAO, True),  # cột của biểu mẫu ĐANG có trong tệp mà vắng ⇒ CHUA_DU
        ("trang_tu_dien_chua_nhap", CANH_BAO, False),  # cả biểu mẫu chưa có trong tệp ⇒ chỉ báo
    ):
        thieu_cot = [
            c.ten for c in cot if c.ten not in bang.cot_co and c.kieu != "id" and ((c.form in form_co) == cung_form)
        ]
        if thieu_cot:
            bang.phat_hien.append(PhatHien(muc, ma, "", "", f"{len(thieu_cot)} cột", "", ", ".join(thieu_cot[:30])))
    if SP._trong_repo_git(p.parent):
        bang.phat_hien.append(
            PhatHien(
                CANH_BAO,
                "excel_trong_repo",
                "",
                "",
                "",
                "",
                "tệp Excel ĐÃ CÓ DỮ LIỆU đang nằm trong cây repo — chuyển ra ngoài (vd ~/NhapLieu/) trước khi lưu tiếp",
            )
        )
    for ma_nc, c in o_bi_pandas_coi_la_thieu(bang):
        bang.phat_hien.append(
            PhatHien(
                CANH_BAO,
                "pandas_doc_thanh_thieu",
                "",
                "",
                c,
                ma_nc,
                "giá trị trùng chuỗi pandas coi là THIẾU (NA/None…)",
            )
        )
    loi, tv = bang.loi(), [x for x in bang.phat_hien if x.muc == TRUY_VAN]
    canh = [x for x in bang.phat_hien if x.muc == CANH_BAO]
    chua_du = [x for x in canh if x.ma in CHUA_DU_KIEM]
    ra.mkdir(parents=True, exist_ok=True)
    csv_p = ra / f"{p.stem}.csv"
    tu_kiem: list[str] = []
    da_kiem: list[str] = []
    if not loi and bang.hang:
        ghi_csv(bang, csv_p)
        tu_kiem, da_kiem = tu_kiem_csv(bang, csv_p)
        if tu_kiem:
            _xoa(csv_p)
    elif csv_p.exists():
        _xoa(csv_p)  # CSV cũ không được sống sót qua một lượt có lỗi
    if loi or tu_kiem or not bang.hang:
        trang_thai = "LOI"
    else:
        trang_thai = "CAN_DOI_CHIEU" if tv else ("CHUA_DU" if chua_du else "SACH")
    tom = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "excel": p.name if not _ten_nghi_pii(p) else "[ĐÃ ẨN TÊN TỆP]" + p.suffix,
        "excel_sha256": _sha256(p),
        "tu_dien": td_p.name,
        "tu_dien_sha256": _sha256(td_p),
        "ma_thieu": mt_p.name if mt_p else None,
        "luat_dq": luat_p.name if luat else None,
        "dac_ta_sha256": dau_van_tay_dac_ta(cot),
        "mau": {k: bang.meta.get(k) for k in ("phien_ban_mau", "dac_ta_sha256", "tao_luc")} if bang.meta else None,
        "so_ma_nghien_cuu": len(bang.hang),
        "cot": bang.cot_co,
        "so_loi": len(loi),
        "so_truy_van": len(tv),
        "so_canh_bao": len(canh),
        "tu_kiem_csv": tu_kiem or "KHOP",
        "tu_kiem_doc_bang": da_kiem,
        "chuan_hoa": bang.dem,
        "csv": str(csv_p) if csv_p.exists() else None,
        "csv_sha256": _sha256(csv_p) if csv_p.exists() else None,
        "trang_thai": trang_thai,
        "disclaimer": CAN_KIEM,
    }
    _ghi_bao_cao(ra, p.stem, bang, tom)
    print(f"Đọc {p.name}: {len(bang.hang)} mã nghiên cứu · {len(bang.cot_co)} cột")
    if loi:
        print(f"🔴 {len(loi)} LỖI cấu trúc/chuyển đổi — KHÔNG ghi CSV. Sửa trong Excel rồi chạy lại:")
        _in_phat_hien(loi)
    if tu_kiem:
        print("🔴 Tự kiểm CSV thất bại — đã xoá CSV:\n   " + "\n   ".join(tu_kiem))
    if not bang.hang and not loi:
        print("🔴 Không có hàng dữ liệu nào")
    if tv:
        print(f"🟠 {len(tv)} TRUY VẤN — đối chiếu PHIẾU GỐC, sửa trong Excel rồi nhập lại:")
        _in_phat_hien(tv)
    if chua_du:
        print(f"⚪ {len(chua_du)} phần CHƯA KIỂM/ĐỌC ĐƯỢC — trạng thái CHUA_DU, không phải sạch:")
        _in_phat_hien(chua_du)
    if canh:
        print(f"⚠ {len(canh)} cảnh báo (xem báo cáo)")
    if bang.dem:
        print("   Chuẩn hoá KHÔNG đổi nghĩa (đếm ô): " + ", ".join(f"{k}={v}" for k, v in bang.dem.items()))
    print(f"   Báo cáo: {ra / (p.stem + '_bao_cao_nhap.md')}")
    if csv_p.exists():
        print(f"✓ CSV: {csv_p} (tự kiểm đọc lại, khớp từng ô: {' · '.join(da_kiem)})")
    if trang_thai == "LOI":
        return MA_LOI
    lenh_cong = [sys.executable, str(TOOLS / "import_real_dataset.py"), "--study", args.study, "--data", str(csv_p)]
    if args.tiep_nhan:
        if chua_du and not tv:
            print("⛔ --tiep-nhan: còn phần CHƯA KIỂM/ĐỌC ĐƯỢC (xem trên) — không chạy cổng tiếp nhận.")
            return MA_LOI
        if tv:
            print(
                "⛔ --tiep-nhan: còn truy vấn — sửa trong Excel rồi nhập lại. Nếu giá trị ĐÚNG là thật"
                " (đã đối chiếu phiếu gốc), chạy cổng tiếp nhận bằng tay và ghi giải quyết truy vấn ở bước làm sạch."
            )
            return MA_LOI
        print("→ Cổng tiếp nhận: " + " ".join(lenh_cong[1:]))
        kq = subprocess.run(lenh_cong, check=False)
        return kq.returncode
    print(
        f"→ Bước kế (cổng tiếp nhận, quét PII theo giá trị): {_py()} tools/import_real_dataset.py --study "
        f'{args.study} --data "{csv_p}"'
    )
    print(CAN_KIEM)
    return MA_LOI if (tv or chua_du) else MA_OK


def _xoa(p: Path) -> None:
    """Xoá CSV cũ/hỏng; tệp đang mở (Windows khoá tệp) ⇒ báo rõ thay vì đổ vết, và KHÔNG để nó trông như kết quả mới."""
    try:
        p.unlink()
    except FileNotFoundError:
        pass
    except PermissionError as e:
        raise TuChoi(f"không xoá được {p.name} (đang mở trong Excel?) — đóng tệp rồi chạy lại") from e


def _ten_nghi_pii(p: Path) -> bool:
    try:
        import import_real_dataset as RDI  # noqa: PLC0415

        return RDI._filename_has_pii_signal(p.name)
    except ImportError:
        return False


def lenh_so_sanh(args) -> int:
    p1, p2 = Path(args.excel1).expanduser().resolve(), Path(args.excel2).expanduser().resolve()
    if p1 == p2:
        raise TuChoi("hai lần nhập là CÙNG một tệp")
    ra = Path(args.ra).expanduser().resolve() if args.ra else p1.parent / f"nhap_kep_{p1.stem}_{p2.stem}"
    _ngoai_repo(ra)
    b1, cot, td_p, _ = _bang_tu_args(args, p1)
    b2, _, _, _ = _bang_tu_args(args, p2)
    loi = [(p1.name, x) for x in b1.loi()] + [(p2.name, x) for x in b2.loi()]
    if loi:
        print(f"🔴 {len(loi)} lỗi cấu trúc khi đọc — sửa trước khi so nhập kép:")
        for ten, x in loi[:40]:
            print(f"   {ten}: {x.trang}!{x.o} {x.cot} — {x.chi_tiet}")
        return MA_LOI
    chi_1 = sorted(set(b1.hang) - set(b2.hang))
    chi_2 = sorted(set(b2.hang) - set(b1.hang))
    chung = [m for m in b1.hang if m in b2.hang]
    cot_ss = [c for c in cot if c.ten in set(b1.cot_co) | set(b2.cot_co) and c.kieu != "id"]
    lech: list[dict] = []
    theo_bien: dict[str, list[int]] = {c.ten: [0, 0] for c in cot_ss}
    for m in chung:
        for c in cot_ss:
            if c.ten not in b1.cot_co or c.ten not in b2.cot_co:
                continue
            if c.ten not in b1.vi_tri[m] and c.ten not in b2.vi_tri[m]:
                continue  # cả hai lần đều chưa nhập trang chứa cột này cho mã này — không tính vào mẫu số
            v1, v2 = b1.hang[m].get(c.ten, ""), b2.hang[m].get(c.ten, "")
            theo_bien[c.ten][0] += 1
            if v1 != v2:
                theo_bien[c.ten][1] += 1
                lech.append(
                    {
                        "ma_nc": m,
                        "cot": c.ten,
                        "o_lan1": b1.vi_tri[m].get(c.ten, ""),
                        "o_lan2": b2.vi_tri[m].get(c.ten, ""),
                        "gia_tri_lan1": v1,
                        "gia_tri_lan2": v2,
                        "kieu": c.kieu,
                    }
                )
    cot_chi_mot = sorted(set(b1.cot_co) ^ set(b2.cot_co))
    so_o = sum(v[0] for v in theo_bien.values())
    ra.mkdir(parents=True, exist_ok=True)
    with open(ra / "NHAP_KEP_chi_tiet.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, ["ma_nc", "cot", "o_lan1", "o_lan2", "gia_tri_lan1", "gia_tri_lan2", "kieu"], lineterminator="\n"
        )
        w.writeheader()
        w.writerows(lech)
    tom = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "phuong_phap": "nhập kép độc lập — so từng ô theo mã nghiên cứu (tools/nhap_lieu_excel.py so-sanh)",
        "lan1_sha256": _sha256(p1),
        "lan2_sha256": _sha256(p2),
        "tu_dien_sha256": _sha256(td_p),
        "dac_ta_sha256": dau_van_tay_dac_ta(cot),
        "so_ma_chung": len(chung),
        "so_ma_chi_lan1": len(chi_1),
        "so_ma_chi_lan2": len(chi_2),
        "cot_chi_co_o_mot_lan": cot_chi_mot,
        "so_o_so_sanh": so_o,
        "so_o_lech": len(lech),
        "ty_le_lech": round(len(lech) / so_o, 6) if so_o else None,
        "lech_theo_bien": {k: {"so_o": v[0], "so_lech": v[1]} for k, v in theo_bien.items() if v[1]},
        "trang_thai": (
            "CO_LECH"
            if (lech or chi_1 or chi_2 or cot_chi_mot)
            else ("TRUNG_KHOP" if so_o else "KHONG_CO_DU_LIEU")  # 0 ô được so KHÔNG BAO GIỜ là «trùng khớp»
        ),
        "ghi_chu": "Tóm tắt KHÔNG chứa giá trị dữ liệu — bằng chứng đối chiếu nguồn (G5 source_data_verification).",
        "disclaimer": CAN_KIEM,
    }
    (ra / "NHAP_KEP_tom_tat.json").write_text(
        json.dumps(tom, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    if tom["trang_thai"] == "KHONG_CO_DU_LIEU":  # không ghi «bằng chứng» nhập kép khi chưa so được ô nào
        print(
            f"🔴 Không có ô nào để so ({len(chung)} mã chung · {so_o} ô) — hai tệp chưa có dữ liệu nhập, hoặc không"
            " có mã nghiên cứu chung. KHÔNG ghi bằng chứng nhập kép."
        )
        return MA_LOI
    bang_chung = SP.thu_muc_de_tai(args.study) / "nhap_lieu"
    bang_chung.mkdir(parents=True, exist_ok=True)
    ten_bc = f"NHAP_KEP_tom_tat_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    (bang_chung / ten_bc).write_text(json.dumps(tom, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(
        f"Nhập kép: {len(chung)} mã chung · {so_o} ô so sánh · {len(lech)} ô lệch"
        + (f" ({tom['ty_le_lech']:.4%})" if so_o else "")
    )
    for nhan, ds in (("chỉ có ở lần 1", chi_1), ("chỉ có ở lần 2", chi_2)):
        if ds:
            print(f"🟠 {len(ds)} mã {nhan}: {', '.join(ds[:20])}" + (" …" if len(ds) > 20 else ""))
    if cot_chi_mot:
        print(f"🟠 cột chỉ có ở một lần nhập: {', '.join(cot_chi_mot)}")
    for x in lech[:40]:
        g1 = "«chữ»" if x["kieu"] in KIEU_CHU else (x["gia_tri_lan1"] or "∅")
        g2 = "«chữ»" if x["kieu"] in KIEU_CHU else (x["gia_tri_lan2"] or "∅")
        print(f"   mã NC {x['ma_nc']:<12} {x['cot']:<26} lần 1 {x['o_lan1']} = {g1} · lần 2 {x['o_lan2']} = {g2}")
    if len(lech) > 40:
        print(f"   … còn {len(lech) - 40} ô — xem NHAP_KEP_chi_tiet.csv")
    print(f"   Chi tiết (có giá trị, ngoài repo): {ra / 'NHAP_KEP_chi_tiet.csv'}")
    print(f"   Bằng chứng (không giá trị): {bang_chung / ten_bc}")
    if tom["trang_thai"] == "TRUNG_KHOP":
        print("✓ Hai lần nhập TRÙNG KHỚP từng ô")
        return MA_OK
    print("→ Đối chiếu PHIẾU GỐC cho từng ô lệch, sửa bản sai, rồi so lại tới khi trùng khớp. " + CAN_KIEM)
    return MA_LOI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Nhập liệu bằng tay qua Excel → CSV chuẩn cho G5. " + CAN_KIEM)
    sub = ap.add_subparsers(dest="lenh", required=True)

    def chung(p, *, doc: bool) -> None:
        p.add_argument("--study", required=True)
        p.add_argument("--dictionary", help="từ điển REDCap (mặc định exports/<mã>/G5_REDCap_dictionary_<mã>.csv)")
        p.add_argument("--ma-thieu", help="mã thiếu (mặc định exports/<mã>/_ma-thieu-theo-bien.csv)")
        if doc:
            p.add_argument("--dong-tieu-de", type=int, help="hàng tiêu đề khi Excel KHÔNG sinh từ «mau» (mặc định 1)")
            p.add_argument("--dong-du-lieu", type=int, help="hàng dữ liệu đầu khi Excel không sinh từ «mau»")
            p.add_argument("--cho-phep-cong-thuc", action="store_true", help="nhận giá trị lưu sẵn của ô công thức")
            p.add_argument(
                "--chap-nhan-tu-dien-moi",
                action="store_true",
                help="mẫu sinh từ từ điển cũ: kiểm theo từ điển hiện tại",
            )
            p.add_argument("--ra", help="thư mục ra (NGOÀI repo)")

    m = sub.add_parser("mau", help="sinh mẫu nhập liệu .xlsx từ từ điển G5")
    chung(m, doc=False)
    m.add_argument("--ra", help="tệp .xlsx (mặc định exports/<mã>/nhap_lieu/MAU_NHAP_LIEU_<mã>.xlsx)")
    m.add_argument("--so-dong", type=int, default=SO_DONG_MAC_DINH, help="số hàng có kiểm tra nhập (mặc định 1000)")
    m.add_argument("--form", help="chỉ các biểu mẫu này (ngăn cách dấu phẩy)")
    m.add_argument("--ghi-de", action="store_true", help="ghi đè mẫu CHƯA có dữ liệu")
    n = sub.add_parser("nhap", help="Excel đã nhập ⇒ CSV chuẩn + báo cáo lỗi từng ô")
    chung(n, doc=True)
    n.add_argument("--excel", required=True)
    n.add_argument("--luat-dq", help="luật DQ (mặc định exports/<mã>/_luat-dq.csv)")
    n.add_argument("--tiep-nhan", action="store_true", help="sạch ⇒ chạy luôn cổng tiếp nhận import_real_dataset.py")
    s = sub.add_parser("so-sanh", help="so hai lần nhập độc lập (nhập kép) từng ô")
    chung(s, doc=True)
    s.add_argument("--excel1", required=True)
    s.add_argument("--excel2", required=True)
    args = ap.parse_args(argv)
    try:
        return {"mau": lenh_mau, "nhap": lenh_nhap, "so-sanh": lenh_so_sanh}[args.lenh](args)
    except TuChoi as e:
        print(f"⛔ {e}")
        return MA_TU_CHOI
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
