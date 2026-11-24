#!/usr/bin/env python3
"""HỆ NHẬP LIỆU CỤC BỘ theo từ điển REDCap của G5 — nhập lại PHIẾU GIẤY trên máy người nhập (23/11/2026).

VÌ SAO: bệnh viện chưa có REDCap và không có giấy phép. Bác sĩ chủ nhiệm chọn (23/11/2026) xây hệ nhập liệu CỤC BỘ
theo ĐÚNG khuôn từ điển dữ liệu mà G5 đã sinh (`exports/<mã>/G5_REDCap_dictionary_<mã>.csv`). Công cụ KHÔNG sao chép
phần mềm REDCap — chỉ đọc khuôn tệp từ điển; sau này bệnh viện có REDCap thật thì nạp đúng từ điển đó là chuyển sang.

PHẠM VI: CHỈ nhập lại từ phiếu giấy, trên máy người nhập: web cục bộ chỉ nghe 127.0.0.1, không mở mạng, không có chế
độ người bệnh tự điền. Đường nhập kép bằng Excel/SPSS (`tools/nhap_lieu_excel.py`) giữ nguyên, ngang hàng.

DÙNG LẠI, KHÔNG VIẾT BỘ ĐÁNH GIÁ THỨ HAI: đọc từ điển, kế hoạch cột, logic nhánh (`danh_gia_logic`), trường calc
(`tinh_calc`), luật DQ, mã thiếu, kiểm giá trị (`kiem_gia_tri`), so nhập kép (`so_sanh_bang`), ghi CSV + tự kiểm đọc
lại (`ghi_csv`, `tu_kiem_csv`) đều là hàm của `nhap_lieu_excel.py`; luật định danh là luật của cổng tiếp nhận
`import_real_dataset.py`.

LỆNH (chạy bằng Python của môi trường dự án ~/.ebm-venv):
  khoi-tao         tạo kho SQLite ngoài OneDrive/ngoài git (mặc định ~/NhapLieu/<mã>/), ràng vào dấu vân tay từ
                   điển, khai người quản lý dữ liệu đầu tiên
  nguoi-them       khai người nhập (mã/chữ viết tắt + vai nhap_lieu_1 | nhap_lieu_2 | quan_ly_du_lieu), PIN tuỳ chọn
  mo               mở giao diện web cục bộ (127.0.0.1, cổng tự chọn) và trình duyệt
  trang-thai       số phiếu/lượt/ô lệch/truy vấn/khoá — không in giá trị
  kiem-nhat-ky     tính lại cả chuỗi băm của nhật ký kiểm toán + đối chiếu neo + phát lại trạng thái kho
  bao-cao-lech     tỷ lệ lệch nhập kép theo biến (không chứa giá trị) → exports/<mã>/nhap_lieu/
  xuat             CSV khuôn xuất REDCap (ngoài repo) + tự kiểm + tóm tắt bằng chứng cho G5; --tiep-nhan gọi cổng
  sao-luu          sao lưu kho (API backup của SQLite) ra thư mục ngoài repo/ngoài đám mây + kiểm bản sao
  tu-dien-kho      ghi lại bản từ điển mà kho đang ràng (khi từ điển G5 đã đổi)
  ho-so-tham-dinh  hồ sơ thẩm định hệ thống máy tính (yêu cầu, ma trận truy vết, kết quả test, giới hạn, ICH/ALCOA+)

QUY TRÁCH: phiên làm việc gắn MỘT người đã khai; PIN (nếu có) băm PBKDF2 có muối. Đây là QUY TRÁCH PHIÊN CỤC BỘ —
KHÔNG phải chữ ký điện tử theo chuẩn nào. Mã thoát: 0 đạt · 1 còn việc/ĐỎ · 2 không đo được · 3 từ chối.
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import csv
import getpass
import hashlib
import hmac
import json
import os
import platform
import re
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import cau_noi_spss as SP  # noqa: E402 — thư mục đề tài, mã thiếu, luật «trong repo git»
import import_real_dataset as RDI  # noqa: E402 — luật định danh của cổng tiếp nhận (một nguồn)
import nhap_lieu_excel as NLE  # noqa: E402 — bộ đọc từ điển/đánh giá/kiểm giá trị/so nhập kép/ghi CSV dùng chung

TuChoi = NLE.TuChoi
KhongDoDuoc = NLE.KhongDoDuoc

MA_OK, MA_LOI, MA_KHONG_DO, MA_TU_CHOI = 0, 1, 2, 3
CAN_KIEM = "Cần bác sĩ kiểm chứng — mọi giá trị nghi sai phải đối chiếu PHIẾU GỐC, máy không tự sửa."
QUY_TRACH = (
    "Quy trách phiên cục bộ: mỗi thao tác gắn mã người đã đăng nhập trên máy này. Đây KHÔNG phải chữ ký điện tử "
    "theo chuẩn nào."
)
PHIEN_BAN_LUOC_DO = 1
TEN_KHO = "kho_nhap_lieu.sqlite3"
TEN_NEO = "neo_nhat_ky.jsonl"
HASH_GOC = "0" * 64
VONG_BAM_PIN = 200_000
VAI = ("nhap_lieu_1", "nhap_lieu_2", "quan_ly_du_lieu")
LAN_CUA_VAI = {"nhap_lieu_1": "lan1", "nhap_lieu_2": "lan2"}
LAN = ("lan1", "lan2")
CHOT = "chot"
QLDL = "quan_ly_du_lieu"
TIEN_TO_BANG_CHUNG = "NHAP_LIEU_CUC_BO_bang_chung_"
# Thành phần đường dẫn của thư mục ĐỒNG BỘ ĐÁM MÂY (so không phân biệt hoa/thường; «onedrive» khớp cả
# «OneDrive - Personal», «OneDrive-Personal»). Dữ liệu chưa qua cổng tiếp nhận không được nằm ở đó.
_DONG_BO_BAT_DAU = ("onedrive",)
_DONG_BO_DUNG = ("cloudstorage", "mobile documents", "icloud drive", "dropbox", "google drive", "googledrive")
_MA_PHIEU_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,39}")
_MA_NGUOI_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,15}")
_THAM_CHIEU_RE = re.compile(r"\[([A-Za-z0-9_]+)(?:\(([A-Za-z0-9_-]+)\))?\]")
# Hành động ghi giá trị — `kiem-nhat-ky` PHÁT LẠI các bản ghi này để dựng lại bảng giá trị và so với kho.
HANH_DONG_GIA_TRI = ("NHAP", "CHOT_KHOP", "GIAI_QUYET_LECH", "SUA_CHOT")
_COT_NHAT_KY = ("luc", "nguoi", "hanh_dong", "record_id", "lan", "cot", "cu", "moi", "ly_do", "tham_chieu")

_LUOC_DO = """
CREATE TABLE meta (khoa TEXT PRIMARY KEY, gia_tri TEXT NOT NULL);
CREATE TABLE nguoi (ma TEXT PRIMARY KEY, vai TEXT NOT NULL, pin_bam TEXT, pin_muoi TEXT, pin_vong INTEGER,
    tao_luc TEXT NOT NULL, tao_boi TEXT NOT NULL);
CREATE TABLE phieu (record_id TEXT PRIMARY KEY, tao_luc TEXT NOT NULL, tao_boi TEXT NOT NULL,
    khoa INTEGER NOT NULL DEFAULT 0, nham INTEGER NOT NULL DEFAULT 0);
CREATE TABLE luot (record_id TEXT NOT NULL, lan TEXT NOT NULL, nguoi TEXT NOT NULL, xong INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (record_id, lan));
CREATE TABLE bieu_mau (record_id TEXT NOT NULL, lan TEXT NOT NULL, form TEXT NOT NULL,
    PRIMARY KEY (record_id, lan, form));
CREATE TABLE gia_tri (record_id TEXT NOT NULL, lan TEXT NOT NULL, cot TEXT NOT NULL, gia_tri TEXT NOT NULL,
    PRIMARY KEY (record_id, lan, cot));
CREATE TABLE doi_chieu (record_id TEXT PRIMARY KEY, so_o INTEGER NOT NULL, so_lech INTEGER NOT NULL,
    luc TEXT NOT NULL, nguoi TEXT NOT NULL);
CREATE TABLE lech (record_id TEXT NOT NULL, cot TEXT NOT NULL, gia_tri_lan1 TEXT NOT NULL, gia_tri_lan2 TEXT NOT NULL,
    giai_quyet INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (record_id, cot));
CREATE TABLE truy_van (id INTEGER PRIMARY KEY AUTOINCREMENT, record_id TEXT NOT NULL, cot TEXT NOT NULL,
    nguon TEXT NOT NULL, ma TEXT NOT NULL, noi_dung TEXT NOT NULL, gia_tri TEXT NOT NULL, trang_thai TEXT NOT NULL,
    tao_luc TEXT NOT NULL, tao_boi TEXT NOT NULL, tra_loi TEXT NOT NULL DEFAULT '',
    dong_ly_do TEXT NOT NULL DEFAULT '');
CREATE TABLE nhat_ky (stt INTEGER PRIMARY KEY, luc TEXT NOT NULL, nguoi TEXT NOT NULL, hanh_dong TEXT NOT NULL,
    record_id TEXT NOT NULL, lan TEXT NOT NULL, cot TEXT NOT NULL, cu TEXT NOT NULL, moi TEXT NOT NULL,
    ly_do TEXT NOT NULL, tham_chieu TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TRIGGER nhat_ky_khong_sua BEFORE UPDATE ON nhat_ky
    BEGIN SELECT RAISE(ABORT, 'nhat_ky chi ghi them — khong sua'); END;
CREATE TRIGGER nhat_ky_khong_xoa BEFORE DELETE ON nhat_ky
    BEGIN SELECT RAISE(ABORT, 'nhat_ky chi ghi them — khong xoa'); END;
"""
_TRIGGER_BAT_BUOC = ("nhat_ky_khong_sua", "nhat_ky_khong_xoa")


# ───────────────────────────── vị trí kho ─────────────────────────────


def bay_gio() -> str:
    """Thời điểm có MÚI GIỜ (ALCOA+ Contemporaneous) — đồng hồ của máy nhập liệu."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def thu_muc_kho_mac_dinh(study: str) -> Path:
    """~/NhapLieu/<mã> (Windows: %USERPROFILE%\\NhapLieu\\<mã>) — ngoài OneDrive, ngoài repo."""
    SP.thu_muc_de_tai(study)  # kiểm mã đề tài hợp lệ (không chứa / .. )
    return Path.home() / "NhapLieu" / study


def la_thu_muc_dong_bo(p: Path) -> str | None:
    """Thành phần đường dẫn (sau khi giải symlink) thuộc thư mục đồng bộ đám mây; None nếu không."""
    thuc = Path(os.path.realpath(p))
    for phan in (*thuc.parts, *p.parts):
        thap = phan.lower()
        if thap.startswith(_DONG_BO_BAT_DAU) or thap in _DONG_BO_DUNG:
            return phan
    if os.name == "nt":  # Windows: OneDrive có thể đổi tên thư mục — so với biến môi trường của chính OneDrive
        for bien in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            goc = os.environ.get(bien)
            if goc:
                g = os.path.normcase(os.path.realpath(goc))
                t = os.path.normcase(str(thuc))
                if t == g or t.startswith(g.rstrip("\\/") + os.sep):
                    return goc
    return None


def _to_tien_ton_tai(p: Path) -> Path:
    q = Path(os.path.abspath(p))
    while not q.exists() and q.parent != q:
        q = q.parent
    return q


def kiem_vi_tri_du_lieu(p: Path, *, nhan: str = "kho dữ liệu") -> None:
    """TỪ CHỐI thư mục trong OneDrive/thư mục đồng bộ đám mây hoặc trong một repo git (BẤT KỲ repo nào)."""
    dong_bo = la_thu_muc_dong_bo(p)
    if dong_bo:
        raise TuChoi(
            f"{nhan} nằm trong thư mục ĐỒNG BỘ ĐÁM MÂY («{dong_bo}») — dữ liệu phiếu chưa qua cổng tiếp nhận "
            "không được đồng bộ lên đám mây và hay xung đột bản sao. Chọn thư mục ngoài OneDrive "
            "(mặc định ~/NhapLieu/<mã>)."
        )
    repo = SP._trong_repo_git(_to_tien_ton_tai(p))
    if repo:
        raise TuChoi(f"{nhan} nằm TRONG một repo git ({repo.name}) — dữ liệu phải ở ngoài mọi repo.")


# ───────────────────────────── từ điển → kế hoạch nhập ─────────────────────────────


def _doc_co_dinh_danh(td_p: Path) -> dict[str, bool]:
    """Cột «Identifier?» (hoặc «identifier» của API REDCap) — `doc_tu_dien_day_du` không đọc cột này."""
    with open(td_p, encoding="utf-8-sig", newline="") as f:
        dr = csv.DictReader(f)
        ten_cot = next((t for t in (dr.fieldnames or []) if t in ("Variable / Field Name", "field_name")), None)
        cot_dd = next((t for t in (dr.fieldnames or []) if t in ("Identifier?", "identifier")), None)
        if not ten_cot or not cot_dd:
            return {}
        return {(r.get(ten_cot) or "").strip(): (r.get(cot_dd) or "").strip().lower() in ("y", "yes", "1")
                for r in dr}  # fmt: skip


def _sha256_tep(p: Path) -> str:
    return NLE._sha256(p)


def _sha256_chuoi(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass
class KeHoach:
    """Từ điển G5 đã đọc + kế hoạch cột (dùng CHUNG `ke_hoach_cot`) + phần loại trừ định danh."""

    study: str
    td_p: Path
    mt_p: Path | None
    luat_p: Path | None
    td: list[dict]
    cot_tat_ca: list  # list[NLE.Cot]
    bo_qua: list[str]
    dinh_danh: dict[str, str]  # tên cột → lý do KHÔNG lưu
    cot: list  # cột ĐƯỢC lưu, theo thứ tự từ điển (cột mã bản ghi đứng đầu)
    ds_calc: list[tuple[str, str]]
    luat_dq: list[dict]
    cot_ngay_mien: frozenset
    dau_van_tay: str
    dac_ta_sha256: str
    td_theo_ten: dict[str, dict] = field(default_factory=dict)
    cot_theo_ten: dict = field(default_factory=dict)
    forms: list[str] = field(default_factory=list)

    @property
    def cid(self):
        return self.cot[0]

    def cot_cua_form(self, form: str) -> list:
        return [c for c in self.cot[1:] if c.form == form]

    def form_cua_cot(self, ten: str) -> str:
        c = self.cot_theo_ten.get(ten)
        return c.form if c else ""


def doc_ke_hoach(study: str, tu_dien: str | Path | None = None, ma_thieu: str | Path | None = None,
                 luat_dq: str | Path | None = None) -> KeHoach:
    td_p, mt_p = NLE.tim_tu_dien(study, str(tu_dien) if tu_dien else None, str(ma_thieu) if ma_thieu else None)
    luat_p = Path(luat_dq).expanduser() if luat_dq else SP.thu_muc_de_tai(study) / "_luat-dq.csv"
    td = NLE.doc_tu_dien_day_du(td_p)
    mt = SP.doc_ma_thieu(mt_p) if mt_p else []
    cot_tat_ca, bo_qua = NLE.ke_hoach_cot(td, mt)
    co_dd = _doc_co_dinh_danh(td_p)
    phan_loai_mien = RDI.cot_phan_loai_tu_dien(td_p)  # ĐÚNG miễn trừ mà cổng tiếp nhận áp khi có --dictionary
    cid = cot_tat_ca[0]
    if co_dd.get(cid.truong):
        raise TuChoi(f"trường mã bản ghi «{cid.ten}» bị đánh dấu Identifier? = y — mã bản ghi phải là MÃ NGHIÊN CỨU")
    if RDI._header_issue(cid.ten):
        raise TuChoi(f"trường mã bản ghi «{cid.ten}» có tên gợi ý định danh theo luật cổng tiếp nhận — đổi thành "
                     "mã nghiên cứu (vd record_id) trong bộ biến rồi sinh lại từ điển G5")  # fmt: skip
    dinh_danh: dict[str, str] = {}
    for c in cot_tat_ca[1:]:
        if co_dd.get(c.truong):
            dinh_danh[c.ten] = "từ điển đánh dấu Identifier? = y"
        elif RDI._normalize_header(c.ten) not in phan_loai_mien and RDI._header_issue(c.ten):
            dinh_danh[c.ten] = f"tên cột gợi ý định danh theo luật cổng tiếp nhận ({RDI._header_issue(c.ten)})"
    cot = [c for c in cot_tat_ca if c.ten not in dinh_danh]
    ds_calc = NLE.truong_calc_tu_dien(td)
    dac_ta = NLE.dau_van_tay_dac_ta(cot_tat_ca)
    van_tay = _sha256_chuoi(json.dumps({"dac_ta": dac_ta, "calc": ds_calc, "dinh_danh": sorted(dinh_danh)},
                                       ensure_ascii=False, sort_keys=True))  # fmt: skip
    kh = KeHoach(
        study=study, td_p=td_p, mt_p=mt_p, luat_p=luat_p if luat_p.exists() else None, td=td, cot_tat_ca=cot_tat_ca,
        bo_qua=bo_qua, dinh_danh=dinh_danh, cot=cot, ds_calc=ds_calc, luat_dq=NLE.doc_luat_dq(luat_p),
        cot_ngay_mien=RDI.cot_ngay_tu_dien(td_p), dau_van_tay=van_tay, dac_ta_sha256=dac_ta,
    )  # fmt: skip
    kh.td_theo_ten = {t["ten"]: t for t in td}
    kh.cot_theo_ten = {c.ten: c for c in cot}
    for t in td[1:]:
        form = t["form"] or "du_lieu"
        if form not in kh.forms:
            kh.forms.append(form)
    return kh


# ───────────────────────────── chuẩn hoá + định danh ─────────────────────────────


def quet_pii_gia_tri(kh: KeHoach, ten_cot: str, v: str, *, ma_thieu: dict | None = None) -> list[str]:
    """Mẫu định danh mà CỔNG TIẾP NHẬN sẽ chặn trong ô này — chặn ngay lúc nhập để dữ liệu định danh không vào kho.
    Cùng mẫu (`RDI.VALUE_PATTERNS`), cùng miễn trừ mẫu «date» cho cột từ điển khai kiểu ngày, cùng luật cột BHYT."""
    v = (v or "").strip()
    if not v or (ma_thieu and v in ma_thieu):
        return []
    norm = RDI._normalize_header(ten_cot)
    ra = []
    if RDI._BHYT_COT_RE.search(norm) and RDI._BHYT_MA_RE.match(v):
        ra.append("ma_bhyt_bhxh")
    for nhan, mau in RDI.VALUE_PATTERNS.items():
        if nhan == "date" and norm in kh.cot_ngay_mien:
            continue
        if mau.search(v):
            ra.append(nhan)
    return ra


def quet_pii_van_ban(s: str) -> list[str]:
    """Lý do/tham chiếu/nội dung truy vấn là chữ tự do: chặn SĐT, CCCD/CMND, email, mã thẻ BHYT (không chặn ngày —
    «theo phiếu ngày …» là chuyện thường; nhật ký nằm trong kho cục bộ, không xuất ra)."""
    return [n for n, m in RDI.VALUE_PATTERNS.items() if n != "date" and m.search(s or "")]


def kiem_ma_phieu(rid: str) -> str:
    rid = (rid or "").strip()
    if not _MA_PHIEU_RE.fullmatch(rid):
        raise TuChoi("mã phiếu chỉ gồm chữ không dấu, số, «-», «_» (1–40 ký tự), bắt đầu bằng chữ/số — vd BN-001")
    trung = [n for n, m in RDI.VALUE_PATTERNS.items() if m.search(rid)]
    if trung:
        raise TuChoi(f"mã phiếu trông giống định danh ({', '.join(trung)}) — chỉ dùng MÃ NGHIÊN CỨU")
    return rid


def _ly_do_hop_le(s: str | None, nhan: str) -> str:
    s = (s or "").strip()
    if len(s) < 2:
        raise TuChoi(f"thiếu {nhan}")
    pii = quet_pii_van_ban(s)
    if pii:
        raise TuChoi(f"{nhan} chứa chuỗi giống định danh ({', '.join(pii)}) — không ghi định danh vào hệ")
    return s


_NGAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_NGAY_GIO_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")
_GIO_RE = re.compile(r"([01]\d|2[0-3]):[0-5]\d")


def chuan_hoa_nhap(c, raw) -> tuple[str, str | None, str | None]:
    """Giá trị gõ trên biểu mẫu ⇒ (chuỗi chuẩn, mức NLE.LOI|NLE.TRUY_VAN|None, thông điệp tiếng Việt).

    Chữ/số/mã đi qua ĐÚNG `nhap_lieu_excel.chuyen_o` (NFC, ký tự ẩn, chữ số không ASCII, «1,5», «01»…). Ngày/giờ đến
    từ ô ngày của trình duyệt nên kiểm riêng theo dạng ISO (Excel lưu ngày là đối tượng ngày, web gửi chuỗi)."""
    s = "" if raw is None else str(raw)
    if c.kieu == "hop":
        s = s.strip()
        if s in ("", "0"):
            return "0", None, None
        if s == "1":
            return "1", None, None
        return s, NLE.LOI, "ô chọn nhiều chỉ nhận 0/1"
    if c.kieu in ("ngay", "ngay_gio", "gio"):
        s = NLE._chuan_chuoi(s, {})
        if not s:
            return "", None, None
        khop = [m for m in c.ma_thieu if m.casefold() == s.casefold()]
        if khop:
            return khop[0], None, None
        if c.kieu == "ngay":
            if _NGAY_RE.fullmatch(s):
                try:
                    date.fromisoformat(s)
                    return s, None, None
                except ValueError:
                    pass
            return s, NLE.LOI, "ngày phải theo dạng năm-tháng-ngày (vd 2026-03-12) và là ngày có thật"
        if c.kieu == "ngay_gio":
            m = _NGAY_GIO_RE.fullmatch(s)
            if m:
                try:
                    datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4) or '00'}")
                except ValueError:
                    m = None
            if not m:
                return s, NLE.LOI, "ngày-giờ phải dạng năm-tháng-ngày giờ:phút (vd 2026-03-12 14:30)"
            if "seconds" in c.kiem_tra:
                return f"{m.group(1)} {m.group(2)}:{m.group(3)}:{m.group(4) or '00'}", None, None
            if m.group(4) and m.group(4) != "00":
                return s, NLE.LOI, "trường này không ghi giây"
            return f"{m.group(1)} {m.group(2)}:{m.group(3)}", None, None
        if _GIO_RE.fullmatch(s):
            return s, None, None
        return s, NLE.LOI, "giờ phải dạng giờ:phút 24 giờ (vd 07:45)"
    v, ma, muc = NLE.chuyen_o(c, s, "General", {})
    if muc:
        return v, muc, NLE._GIAI_THICH.get(ma, ma)
    return v, None, None


# ───────────────────────────── nhật ký chuỗi băm ─────────────────────────────


def bam_ban_ghi(stt: int, prev_hash: str, d: dict) -> str:
    """Băm SHA-256 của MỘT bản ghi nhật ký: số thứ tự + băm bản trước + mọi trường (JSON chuẩn tắc)."""
    goi = {"stt": int(stt), "prev_hash": prev_hash, **{k: str(d.get(k, "")) for k in _COT_NHAT_KY}}
    return _sha256_chuoi(json.dumps(goi, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def bam_pin(pin: str, muoi: bytes, vong: int = VONG_BAM_PIN) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), muoi, int(vong)).hex()


@dataclass(frozen=True)
class Phien:
    """Phiên làm việc gắn MỘT người đã khai (quy trách phiên cục bộ)."""

    ma: str
    vai: str


class _GiaoDich:
    def __init__(self, cn: sqlite3.Connection):
        self.cn = cn
        self.neo: tuple[int, str] | None = None


@dataclass
class KetQuaBieuMau:
    luu: bool = False
    loi: dict = field(default_factory=dict)  # cột → [thông điệp chặn lưu]
    canh_bao: dict = field(default_factory=dict)  # cột → [truy vấn/cảnh báo không chặn]
    loi_chung: list = field(default_factory=list)
    canh_bao_chung: list = field(default_factory=list)
    hien_thi: dict = field(default_factory=dict)  # cột → True | False | None (không đánh giá được)
    gia_tri: dict = field(default_factory=dict)  # giá trị hiện hành (đã chuẩn hoá) của MỌI cột lượt này
    da_luu: dict = field(default_factory=dict)  # giá trị đang lưu trong kho
    calc: dict = field(default_factory=dict)  # trường calc → giá trị | None
    loi_calc: dict = field(default_factory=dict)
    can_ly_do: list = field(default_factory=list)
    so_thay_doi: int = 0

    def co_loi(self) -> bool:
        return bool(self.loi or self.loi_chung)


def _them(d: dict, k: str, s: str) -> None:
    d.setdefault(k, [])
    if s not in d[k]:
        d[k].append(s)


# ───────────────────────────── kho ─────────────────────────────


class Kho:
    """Kho SQLite của MỘT đề tài — mọi thay đổi đi qua đây, mỗi thay đổi một bản ghi nhật ký chuỗi băm."""

    def __init__(self, thu_muc: Path, kh: KeHoach):
        self.thu_muc = Path(thu_muc)
        self.duong_dan = self.thu_muc / TEN_KHO
        self.tep_neo = self.thu_muc / TEN_NEO
        self.kh = kh
        self._khoa = threading.RLock()

    # ── mở / tạo ──
    @classmethod
    def khoi_tao(cls, study: str, thu_muc: Path | None, quan_ly: str, *, pin: str | None = None,
                 tu_dien=None, ma_thieu=None, luat_dq=None) -> Kho:
        thu_muc = Path(thu_muc).expanduser() if thu_muc else thu_muc_kho_mac_dinh(study)
        kiem_vi_tri_du_lieu(thu_muc)
        kh = doc_ke_hoach(study, tu_dien, ma_thieu, luat_dq)
        if (thu_muc / TEN_KHO).exists():
            raise TuChoi(f"đã có kho ở {thu_muc} — không tạo đè (mở bằng lệnh «mo»)")
        thu_muc.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            os.chmod(thu_muc, 0o700)
        kho = cls(thu_muc, kh)
        cn = sqlite3.connect(kho.duong_dan, isolation_level=None)
        try:
            cn.executescript(_LUOC_DO)
        finally:
            cn.close()
        if os.name != "nt":
            os.chmod(kho.duong_dan, 0o600)
        kho.tep_neo.write_text("", encoding="utf-8", newline="\n")
        ma_ql = kho._kiem_ma_nguoi(quan_ly)
        with kho._gd() as gd:
            meta = {
                "study": study, "phien_ban_luoc_do": str(PHIEN_BAN_LUOC_DO), "ma_kho": uuid.uuid4().hex,
                "dau_van_tay": kh.dau_van_tay, "dac_ta_sha256": kh.dac_ta_sha256, "tu_dien_ten": kh.td_p.name,
                "tu_dien_sha256": _sha256_tep(kh.td_p), "tu_dien_csv": kh.td_p.read_text(encoding="utf-8-sig"),
                "ma_thieu_csv": kh.mt_p.read_text(encoding="utf-8-sig") if kh.mt_p else "", "tao_luc": bay_gio(),
            }  # fmt: skip
            gd.cn.executemany("INSERT INTO meta(khoa, gia_tri) VALUES (?, ?)", list(meta.items()))
            kho._ghi(gd, ma_ql, "KHOI_TAO", moi=kh.dau_van_tay, ly_do=f"từ điển {kh.td_p.name}")
            kho._them_nguoi(gd, ma_ql, QLDL, pin, ma_ql)
        return kho

    @classmethod
    def mo(cls, study: str, thu_muc: Path | None = None, *, tu_dien=None, ma_thieu=None, luat_dq=None) -> Kho:
        thu_muc = Path(thu_muc).expanduser() if thu_muc else thu_muc_kho_mac_dinh(study)
        kiem_vi_tri_du_lieu(thu_muc)
        if not (thu_muc / TEN_KHO).exists():
            raise KhongDoDuoc(f"chưa có kho ở {thu_muc} — chạy «khoi-tao» trước")
        kh = doc_ke_hoach(study, tu_dien, ma_thieu, luat_dq)
        kho = cls(thu_muc, kh)
        meta = kho.meta()
        if meta.get("study") != study:
            raise TuChoi(f"kho này thuộc đề tài «{meta.get('study')}», không phải «{study}»")
        if meta.get("dau_van_tay") != kh.dau_van_tay:
            raise TuChoi(
                "TỪ ĐIỂN ĐÃ ĐỔI sau khi tạo kho (dấu vân tay kho "
                f"{str(meta.get('dau_van_tay'))[:12]}… ≠ từ điển hiện tại {kh.dau_van_tay[:12]}…). Kho KHÔNG tự di trú "
                "và giữ nguyên dữ liệu cũ. Cách xử lý: (1) đổi từ điển là nhầm ⇒ khôi phục bản từ điển cũ; (2) đổi có "
                "chủ đích (đề cương sửa đổi đã duyệt) ⇒ ghi bản từ điển mà kho đang ràng bằng «tu-dien-kho --ra <tệp>»,"
                " mở kho cũ bằng «--dictionary <tệp đó>» để xuất/khoá phần đã nhập, rồi tạo kho MỚI cho từ điển mới — "
                "mọi chuyển dữ liệu giữa hai kho do người quản lý dữ liệu làm và ghi nhật ký."
            )
        return kho

    # ── kết nối ──
    def _ket_noi(self) -> sqlite3.Connection:
        cn = sqlite3.connect(self.duong_dan, isolation_level=None, timeout=30)
        cn.row_factory = sqlite3.Row
        cn.execute("PRAGMA synchronous=FULL")
        return cn

    @contextlib.contextmanager
    def _gd(self):
        """Giao dịch ghi (BEGIN IMMEDIATE — tuần tự hoá); neo nhật ký ghi ra tệp SAU KHI commit."""
        with self._khoa:
            cn = self._ket_noi()
            gd = _GiaoDich(cn)
            try:
                cn.execute("BEGIN IMMEDIATE")
                yield gd
                cn.execute("COMMIT")
            except BaseException:
                if cn.in_transaction:
                    cn.execute("ROLLBACK")
                raise
            finally:
                cn.close()
            if gd.neo:
                with open(self.tep_neo, "a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps({"stt": gd.neo[0], "hash": gd.neo[1]}) + "\n")

    @contextlib.contextmanager
    def _doc(self):
        cn = self._ket_noi()
        try:
            yield cn
        finally:
            cn.close()

    def meta(self) -> dict[str, str]:
        with self._doc() as cn:
            return {r["khoa"]: r["gia_tri"] for r in cn.execute("SELECT khoa, gia_tri FROM meta")}

    # ── nhật ký ──
    def _ghi(self, gd: _GiaoDich, nguoi: str, hanh_dong: str, *, record_id: str = "", lan: str = "", cot: str = "",
             cu: str = "", moi: str = "", ly_do: str = "", tham_chieu: str = "") -> None:
        cuoi = gd.cn.execute("SELECT stt, hash FROM nhat_ky ORDER BY stt DESC LIMIT 1").fetchone()
        stt, prev = (cuoi["stt"] + 1, cuoi["hash"]) if cuoi else (1, HASH_GOC)
        d = {"luc": bay_gio(), "nguoi": nguoi, "hanh_dong": hanh_dong, "record_id": record_id, "lan": lan, "cot": cot,
             "cu": cu, "moi": moi, "ly_do": ly_do, "tham_chieu": tham_chieu}  # fmt: skip
        h = bam_ban_ghi(stt, prev, d)
        gd.cn.execute(
            "INSERT INTO nhat_ky(stt, luc, nguoi, hanh_dong, record_id, lan, cot, cu, moi, ly_do, tham_chieu, "
            "prev_hash, hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (stt, *[d[k] for k in _COT_NHAT_KY], prev, h),
        )
        gd.neo = (stt, h)

    # ── người ──
    @staticmethod
    def _kiem_ma_nguoi(ma: str) -> str:
        ma = (ma or "").strip()
        if not _MA_NGUOI_RE.fullmatch(ma):
            raise TuChoi("mã người nhập: 2–16 ký tự chữ không dấu/số/«._-» (mã hoặc chữ viết tắt, không ghi họ tên)")
        if quet_pii_van_ban(ma):
            raise TuChoi("mã người nhập trông giống định danh — dùng mã/chữ viết tắt")
        return ma

    def _them_nguoi(self, gd: _GiaoDich, ma: str, vai: str, pin: str | None, boi: str) -> None:
        if vai not in VAI:
            raise TuChoi(f"vai phải là một trong {', '.join(VAI)}")
        if gd.cn.execute("SELECT 1 FROM nguoi WHERE ma = ?", (ma,)).fetchone():
            raise TuChoi(f"đã có người mã «{ma}»")
        muoi = bam = vong = None
        if pin:
            if not (4 <= len(pin) <= 32):
                raise TuChoi("PIN dài 4–32 ký tự")
            muoi_b = secrets.token_bytes(16)
            muoi, bam, vong = muoi_b.hex(), bam_pin(pin, muoi_b), VONG_BAM_PIN
        gd.cn.execute("INSERT INTO nguoi(ma, vai, pin_bam, pin_muoi, pin_vong, tao_luc, tao_boi) "
                      "VALUES (?,?,?,?,?,?,?)", (ma, vai, bam, muoi, vong, bay_gio(), boi))  # fmt: skip
        self._ghi(gd, boi, "THEM_NGUOI", cot=ma, moi=vai, ly_do="có PIN" if pin else "không PIN")

    def them_nguoi(self, phien: Phien, ma: str, vai: str, pin: str | None = None) -> None:
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            self._them_nguoi(gd, self._kiem_ma_nguoi(ma), vai, pin, phien.ma)

    def danh_sach_nguoi(self) -> list[dict]:
        with self._doc() as cn:
            return [{"ma": r["ma"], "vai": r["vai"], "co_pin": bool(r["pin_bam"])}
                    for r in cn.execute("SELECT ma, vai, pin_bam FROM nguoi ORDER BY ma")]  # fmt: skip

    def can_pin(self, ma: str) -> bool:
        with self._doc() as cn:
            r = cn.execute("SELECT pin_bam FROM nguoi WHERE ma = ?", ((ma or "").strip(),)).fetchone()
        return bool(r and r["pin_bam"])

    def dang_nhap(self, ma: str, pin: str | None = None) -> Phien:
        ma = (ma or "").strip()
        with self._gd() as gd:
            r = gd.cn.execute("SELECT * FROM nguoi WHERE ma = ?", (ma,)).fetchone()
            dung = False
            if r is not None:
                if r["pin_bam"]:
                    dung = bool(pin) and hmac.compare_digest(
                        bam_pin(pin, bytes.fromhex(r["pin_muoi"]), r["pin_vong"]), r["pin_bam"])
                else:
                    dung = not pin
            if not dung:
                self._ghi(gd, ma if r is not None else "?", "DANG_NHAP_SAI",
                          ly_do="sai PIN" if r is not None else "mã không có")  # fmt: skip
                loi = True
            else:
                self._ghi(gd, ma, "DANG_NHAP", moi=r["vai"])
                loi = False
        if loi:
            raise TuChoi("mã người nhập hoặc PIN không đúng")
        return Phien(ma, r["vai"])

    def dang_xuat(self, phien: Phien) -> None:
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien)
            self._ghi(gd, phien.ma, "DANG_XUAT")

    def _kiem_phien(self, cn: sqlite3.Connection, phien: Phien, *vai: str) -> None:
        r = cn.execute("SELECT vai FROM nguoi WHERE ma = ?", (phien.ma,)).fetchone()
        if r is None or r["vai"] != phien.vai:
            raise TuChoi("phiên không còn hợp lệ — đăng nhập lại")
        if vai and phien.vai not in vai:
            raise TuChoi(f"thao tác này chỉ dành cho vai {', '.join(vai)} (bạn: {phien.vai})")

    # ── phiếu ──
    def tao_phieu(self, phien: Phien, record_id: str) -> str:
        rid = kiem_ma_phieu(record_id)
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien)
            if gd.cn.execute("SELECT 1 FROM phieu WHERE record_id = ?", (rid,)).fetchone():
                raise TuChoi(f"đã có phiếu «{rid}»")
            gd.cn.execute("INSERT INTO phieu(record_id, tao_luc, tao_boi) VALUES (?,?,?)", (rid, bay_gio(), phien.ma))
            self._ghi(gd, phien.ma, "TAO_PHIEU", record_id=rid)
        return rid

    def danh_dau_nham(self, phien: Phien, record_id: str, ly_do: str, *, nham: bool = True) -> None:
        """Phiếu tạo NHẦM mã (gõ sai mã): loại khỏi xuất/khoá — KHÔNG xoá (dữ liệu và nhật ký giữ nguyên)."""
        ly_do = _ly_do_hop_le(ly_do, "lý do")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            p = self._phieu(gd.cn, record_id)
            if p["khoa"]:
                raise TuChoi("phiếu đang khoá — mở khoá trước")
            gd.cn.execute("UPDATE phieu SET nham = ? WHERE record_id = ?", (int(nham), record_id))
            self._ghi(gd, phien.ma, "NHAM_MA" if nham else "BO_NHAM_MA", record_id=record_id, moi=str(int(nham)),
                      ly_do=ly_do)  # fmt: skip

    def _phieu(self, cn: sqlite3.Connection, record_id: str) -> sqlite3.Row:
        p = cn.execute("SELECT * FROM phieu WHERE record_id = ?", (record_id,)).fetchone()
        if p is None:
            raise TuChoi(f"không có phiếu «{record_id}»")
        return p

    def danh_sach_phieu(self) -> list[dict]:
        """Trạng thái từng phiếu — KHÔNG có giá trị dữ liệu (người lượt 2 xem được mà không thấy giá trị lượt 1)."""
        with self._doc() as cn:
            luot = {(r["record_id"], r["lan"]): dict(r) for r in cn.execute("SELECT * FROM luot")}
            dc = {r["record_id"] for r in cn.execute("SELECT record_id FROM doi_chieu")}
            lech_mo = {r["record_id"]: r["n"] for r in cn.execute(
                "SELECT record_id, COUNT(*) n FROM lech WHERE giai_quyet = 0 GROUP BY record_id")}
            tv_mo = {r["record_id"]: r["n"] for r in cn.execute(
                "SELECT record_id, COUNT(*) n FROM truy_van WHERE trang_thai != 'dong' GROUP BY record_id")}
            ra = []
            for p in cn.execute("SELECT * FROM phieu ORDER BY record_id"):
                rid = p["record_id"]
                ra.append({
                    "record_id": rid, "khoa": bool(p["khoa"]), "nham": bool(p["nham"]),
                    **{f"{lan}_nguoi": (luot.get((rid, lan)) or {}).get("nguoi", "") for lan in LAN},
                    **{f"{lan}_xong": bool((luot.get((rid, lan)) or {}).get("xong")) for lan in LAN},
                    "da_doi_chieu": rid in dc, "lech_mo": lech_mo.get(rid, 0), "truy_van_mo": tv_mo.get(rid, 0),
                })  # fmt: skip
            return ra

    # ── giá trị ──
    def _gia_tri(self, cn: sqlite3.Connection, record_id: str, lan: str) -> dict[str, str]:
        return {r["cot"]: r["gia_tri"] for r in cn.execute(
            "SELECT cot, gia_tri FROM gia_tri WHERE record_id = ? AND lan = ?", (record_id, lan))}

    def _forms_da_luu(self, cn: sqlite3.Connection, record_id: str, lan: str) -> set[str]:
        return {r["form"] for r in cn.execute(
            "SELECT form FROM bieu_mau WHERE record_id = ? AND lan = ?", (record_id, lan))}

    def dong_day_du(self, record_id: str, luu: dict[str, str]) -> dict[str, str]:
        """Hàng ĐỦ mọi cột được lưu: ô chưa nhập = '' (như REDCap), ô chọn nhiều chưa chọn = '0'."""
        ra = {}
        for c in self.kh.cot:
            if c.kieu == "id":
                ra[c.ten] = record_id
            else:
                ra[c.ten] = luu.get(c.ten, "0" if c.kieu == "hop" else "")
        return ra

    def danh_gia_hien_thi(self, dong: dict[str, str]) -> tuple[dict, dict, dict]:
        """(hiển thị từng cột, giá trị calc, lỗi calc) — nhánh đánh giá bằng ĐÚNG `danh_gia_logic`, calc bằng
        `tinh_calc`. Không đánh giá được ⇒ None (KHÔNG BAO GIỜ âm thầm coi là hiện/ẩn)."""
        dong_c, loi_calc = NLE.dong_kem_calc(dong, self.kh.ds_calc)
        hien: dict[str, bool | None] = {}
        for c in self.kh.cot[1:]:
            if not c.nhanh:
                hien[c.ten] = True
                continue
            try:
                hien[c.ten] = bool(NLE.danh_gia_logic(c.nhanh, dong_c))
            except NLE.LogicKhongHo:
                hien[c.ten] = None
        calc = {ten: (dong_c.get(ten) if ten not in loi_calc else None) for ten, _ in self.kh.ds_calc}
        return hien, calc, loi_calc

    def _bang(self, hang: dict[str, dict[str, str]]):
        """`NLE.Bang` dựng từ kho để dùng ĐÚNG `kiem_gia_tri`/`so_sanh_bang`/`ghi_csv`/`tu_kiem_csv`."""
        vi_tri = {rid: {c.ten: f"{c.form}!{c.ten}" for c in self.kh.cot} for rid in hang}
        return NLE.Bang(self.kh.cot, hang, vi_tri, {rid: set(self.kh.forms) for rid in hang}, [], {}, {},
                        [c.ten for c in self.kh.cot])  # fmt: skip

    def _kiem_dong(self, rid: str, dong: dict[str, str]) -> list:
        b = self._bang({rid: dong})
        NLE.kiem_gia_tri(b, self.kh.luat_dq, self.kh.ds_calc)
        return b.phat_hien

    def _cot_cua_luat(self, ma_luat: str) -> list[str]:
        for luat in self.kh.luat_dq:
            if luat["ma_luat"] == ma_luat:
                ra = []
                for m in _THAM_CHIEU_RE.finditer(luat["bieu_thuc_redcap"]):
                    ten = f"{m.group(1)}___{m.group(2)}" if m.group(2) else m.group(1)
                    ra.append(ten)
                return ra
        return []

    def _kiem_luot(self, cn: sqlite3.Connection, phien: Phien, record_id: str, lan: str, *, ghi: bool) -> None:
        if lan not in LAN:
            raise TuChoi("lượt phải là lan1 hoặc lan2")
        self._kiem_phien(cn, phien, "nhap_lieu_1", "nhap_lieu_2")
        if LAN_CUA_VAI.get(phien.vai) != lan:
            raise TuChoi(f"vai {phien.vai} chỉ nhập {LAN_CUA_VAI.get(phien.vai)} — nhập kép phải độc lập")
        p = self._phieu(cn, record_id)
        if ghi and p["khoa"]:
            raise TuChoi("phiếu đã KHOÁ — người quản lý dữ liệu mở khoá (kèm lý do) trước khi sửa")
        if ghi and p["nham"]:
            raise TuChoi("phiếu đã đánh dấu nhầm mã")
        chu = cn.execute("SELECT nguoi FROM luot WHERE record_id = ? AND lan = ?", (record_id, lan)).fetchone()
        if chu and chu["nguoi"] != phien.ma:
            raise TuChoi(f"lượt {lan} của phiếu này do người khác nhập — mỗi lượt một người (quy trách)")
        khac = cn.execute("SELECT nguoi FROM luot WHERE record_id = ? AND lan != ?", (record_id, lan)).fetchone()
        if khac and khac["nguoi"] == phien.ma:
            raise TuChoi("cùng một người không được nhập cả hai lượt của một phiếu")
        if ghi and cn.execute("SELECT 1 FROM doi_chieu WHERE record_id = ?", (record_id,)).fetchone():
            raise TuChoi("phiếu đã đối chiếu nhập kép — mọi sửa đổi làm ở bản chốt (người quản lý dữ liệu)")

    def xem_bieu_mau(self, phien: Phien, record_id: str, lan: str, form: str,
                     gia_tri_moi: dict[str, str] | None = None, ly_do: dict[str, str] | None = None
                     ) -> KetQuaBieuMau:
        """Đánh giá biểu mẫu (KHÔNG lưu): chuẩn hoá giá trị gõ, logic nhánh, calc, kiểm giá trị — lỗi tại chỗ.
        Biểu mẫu chưa lưu lần nào và chưa gõ gì ⇒ chưa nhắc «câu bắt buộc bị trống» (trang mới mở không nhiễu)."""
        with self._doc() as cn:
            self._kiem_luot(cn, phien, record_id, lan, ghi=False)
            bao = bool(gia_tri_moi) or form in self._forms_da_luu(cn, record_id, lan)
            return self._danh_gia(cn, record_id, lan, form, gia_tri_moi or {}, ly_do or {}, bao_bat_buoc=bao)

    def _danh_gia(self, cn, record_id: str, lan: str, form: str, moi: dict[str, str], ly_do: dict[str, str],
                  *, bao_bat_buoc: bool = True) -> KetQuaBieuMau:
        if form not in self.kh.forms:
            raise TuChoi(f"không có biểu mẫu «{form}» trong từ điển")
        kq = KetQuaBieuMau()
        luu = self._gia_tri(cn, record_id, lan)
        kq.da_luu = dict(luu)
        cot_form = {c.ten: c for c in self.kh.cot_cua_form(form)}
        hien_tai = dict(luu)
        for ten, raw in moi.items():
            if ten in self.kh.dinh_danh:
                raise TuChoi(f"«{ten}» là trường ĐỊNH DANH ({self.kh.dinh_danh[ten]}) — hệ không lưu định danh; "
                             "chỉ ghi trên phiếu giấy")  # fmt: skip
            if ten not in cot_form:
                raise TuChoi(f"«{ten}» không thuộc biểu mẫu «{form}» (hoặc không phải cột nhập tay)")
            c = cot_form[ten]
            v, muc, tb = chuan_hoa_nhap(c, raw)
            if muc == NLE.LOI:
                _them(kq.loi, ten, tb)
            elif muc:
                _them(kq.canh_bao, ten, tb)
            pii = quet_pii_gia_tri(self.kh, ten, v, ma_thieu=c.ma_thieu)
            if pii:
                _them(kq.loi, ten, f"giá trị giống định danh ({', '.join(pii)}) — cổng tiếp nhận sẽ chặn; không ghi "
                                   "định danh vào hệ")  # fmt: skip
            if c.kieu == "hop":
                hien_tai[ten] = v  # «0»/«1» — ô chọn nhiều đã hiện trên trang luôn có giá trị
            elif v == "":
                hien_tai.pop(ten, None)
            else:
                hien_tai[ten] = v
        dong = self.dong_day_du(record_id, hien_tai)
        kq.gia_tri = dong
        kq.hien_thi, kq.calc, kq.loi_calc = self.danh_gia_hien_thi(dong)
        for ten, c in cot_form.items():
            cu, moi_v = luu.get(ten, ""), hien_tai.get(ten, "")
            if c.kieu == "hop":
                cu, moi_v = luu.get(ten, "0"), hien_tai.get(ten, "0")
            if cu != moi_v:
                kq.so_thay_doi += 1
                if luu.get(ten, "") != "" and not (c.kieu == "hop" and luu.get(ten) == "0" and moi_v == "1"):
                    kq.can_ly_do.append(ten)
                    ld = (ly_do.get(ten) or "").strip()
                    if len(ld) < 2:
                        _them(kq.loi, ten, "đổi giá trị ĐÃ LƯU phải ghi lý do sửa (vd «gõ nhầm, đối chiếu phiếu gốc»)")
                    elif quet_pii_van_ban(ld):
                        _them(kq.loi, ten, "lý do sửa chứa chuỗi giống định danh — không ghi định danh vào hệ")
            if kq.hien_thi.get(ten) is None and c.nhanh:
                _them(kq.canh_bao, ten, f"máy không đánh giá được logic nhánh «{c.nhanh}» — câu được hiện để nhập; "
                                        "đối chiếu tay theo phiếu gốc")  # fmt: skip
        cot_trong_form = set(cot_form)
        for p in self._kiem_dong(record_id, dong):
            if p.muc == NLE.CANH_BAO:
                if p.ma == "logic_nhanh_khong_danh_gia_duoc":
                    continue  # đã báo tại chỗ ở trên
                if p.ma == "luat_dq_khong_danh_gia_duoc":
                    if set(self._cot_cua_luat(p.cot)) & cot_trong_form:
                        kq.canh_bao_chung.append(f"luật {p.cot}: máy không đánh giá được ({p.chi_tiet})")
                continue
            if p.ma.startswith("luat_"):
                lien_quan = [x for x in self._cot_cua_luat(p.ma[5:]) if x in cot_trong_form]
                if lien_quan:
                    _them(kq.canh_bao, lien_quan[0], f"{p.chi_tiet} — đối chiếu phiếu gốc, nhập ĐÚNG như phiếu")
                continue
            if p.ma == "thieu_bat_buoc" and not bao_bat_buoc:
                continue
            if p.cot in cot_trong_form:
                _them(kq.canh_bao, p.cot, p.chi_tiet + (" — nhập đúng như phiếu gốc" if p.ma != "thieu_bat_buoc"
                                                        else ""))  # fmt: skip
        return kq

    def luu_bieu_mau(self, phien: Phien, record_id: str, lan: str, form: str, gia_tri_moi: dict[str, str],
                     ly_do: dict[str, str] | None = None) -> KetQuaBieuMau:
        """Lưu MỘT biểu mẫu của MỘT lượt. Có lỗi chặn ⇒ không lưu ô nào (cả biểu mẫu hoặc không). Mỗi ô đổi một bản
        ghi nhật ký (cũ → mới, lý do bắt buộc khi đổi giá trị đã lưu)."""
        ly_do = ly_do or {}
        with self._gd() as gd:
            self._kiem_luot(gd.cn, phien, record_id, lan, ghi=True)
            kq = self._danh_gia(gd.cn, record_id, lan, form, gia_tri_moi, ly_do)
            if kq.co_loi():
                return kq
            luu = kq.da_luu
            if not gd.cn.execute("SELECT 1 FROM luot WHERE record_id = ? AND lan = ?", (record_id, lan)).fetchone():
                gd.cn.execute("INSERT INTO luot(record_id, lan, nguoi) VALUES (?,?,?)", (record_id, lan, phien.ma))
                self._ghi(gd, phien.ma, "BAT_DAU_LUOT", record_id=record_id, lan=lan)
            for c in self.kh.cot_cua_form(form):
                cu = luu.get(c.ten, "")
                moi_v = kq.gia_tri.get(c.ten, "")
                if c.kieu == "hop" and c.ten not in gia_tri_moi and c.ten not in luu:
                    continue  # nhóm chọn nhiều không hiện trên trang ⇒ không ghi '0' thay người nhập
                if c.ten not in gia_tri_moi and c.kieu != "hop":
                    continue
                if cu == moi_v:
                    continue
                if moi_v == "":
                    gd.cn.execute("DELETE FROM gia_tri WHERE record_id = ? AND lan = ? AND cot = ?",
                                  (record_id, lan, c.ten))  # fmt: skip
                else:
                    gd.cn.execute("INSERT OR REPLACE INTO gia_tri(record_id, lan, cot, gia_tri) VALUES (?,?,?,?)",
                                  (record_id, lan, c.ten, moi_v))  # fmt: skip
                self._ghi(gd, phien.ma, "NHAP", record_id=record_id, lan=lan, cot=c.ten, cu=cu, moi=moi_v,
                          ly_do=(ly_do.get(c.ten) or "").strip() if c.ten in kq.can_ly_do else "")  # fmt: skip
            if form not in self._forms_da_luu(gd.cn, record_id, lan):
                gd.cn.execute("INSERT INTO bieu_mau(record_id, lan, form) VALUES (?,?,?)", (record_id, lan, form))
                self._ghi(gd, phien.ma, "LUU_BIEU_MAU", record_id=record_id, lan=lan, cot=form)
            kq.luu = True
            kq.da_luu = self._gia_tri(gd.cn, record_id, lan)
        return kq

    def hoan_tat_luot(self, phien: Phien, record_id: str, lan: str) -> None:
        """Đánh dấu lượt nhập XONG: mọi biểu mẫu đã lưu ít nhất một lần và không còn câu bắt buộc đang hiện mà trống
        (phiếu bỏ trống ⇒ ghi mã thiếu)."""
        with self._gd() as gd:
            self._kiem_luot(gd.cn, phien, record_id, lan, ghi=True)
            chu = gd.cn.execute("SELECT xong FROM luot WHERE record_id = ? AND lan = ?", (record_id, lan)).fetchone()
            if chu is None:
                raise TuChoi("lượt này chưa nhập biểu mẫu nào")
            thieu_form = [f for f in self.kh.forms if f not in self._forms_da_luu(gd.cn, record_id, lan)]
            if thieu_form:
                raise TuChoi("còn biểu mẫu chưa lưu: " + ", ".join(thieu_form))
            dong = self.dong_day_du(record_id, self._gia_tri(gd.cn, record_id, lan))
            thieu = [p.cot for p in self._kiem_dong(record_id, dong) if p.ma == "thieu_bat_buoc"]
            if thieu:
                raise TuChoi("còn câu bắt buộc đang hiện mà trống (ghi mã thiếu nếu phiếu bỏ trống): "
                             + ", ".join(thieu))  # fmt: skip
            if chu["xong"]:
                return
            gd.cn.execute("UPDATE luot SET xong = 1 WHERE record_id = ? AND lan = ?", (record_id, lan))
            self._ghi(gd, phien.ma, "HOAN_TAT_LUOT", record_id=record_id, lan=lan)

    # ── nhập kép: đối chiếu ──
    def doi_chieu(self, phien: Phien, record_id: str) -> dict:
        """So TỪNG Ô hai lượt (ĐÚNG `NLE.so_sanh_bang`). Ô khớp ⇒ ghi bản chốt; ô lệch ⇒ chờ giải quyết theo phiếu
        gốc. Chạy một lần cho mỗi phiếu (lượt bị khoá sửa sau đó)."""
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            p = self._phieu(gd.cn, record_id)
            if p["nham"]:
                raise TuChoi("phiếu đã đánh dấu nhầm mã")
            if gd.cn.execute("SELECT 1 FROM doi_chieu WHERE record_id = ?", (record_id,)).fetchone():
                return self.trang_thai_doi_chieu(record_id, cn=gd.cn)
            luot = {r["lan"]: r for r in gd.cn.execute("SELECT * FROM luot WHERE record_id = ?", (record_id,))}
            chua = [lan for lan in LAN if not (luot.get(lan) and luot[lan]["xong"])]
            if chua:
                raise TuChoi("chưa đối chiếu được — lượt chưa hoàn tất: " + ", ".join(chua))
            if luot["lan1"]["nguoi"] == luot["lan2"]["nguoi"]:
                raise TuChoi("hai lượt do cùng một người nhập — không phải nhập kép độc lập")
            b1 = self._bang({record_id: self.dong_day_du(record_id, self._gia_tri(gd.cn, record_id, "lan1"))})
            b2 = self._bang({record_id: self.dong_day_du(record_id, self._gia_tri(gd.cn, record_id, "lan2"))})
            ss = NLE.so_sanh_bang(b1, b2, self.kh.cot)
            lech_cot = {x["cot"] for x in ss["lech"]}
            for x in ss["lech"]:
                gd.cn.execute("INSERT INTO lech(record_id, cot, gia_tri_lan1, gia_tri_lan2) VALUES (?,?,?,?)",
                              (record_id, x["cot"], x["gia_tri_lan1"], x["gia_tri_lan2"]))  # fmt: skip
                self._ghi(gd, phien.ma, "LECH", record_id=record_id, cot=x["cot"], cu=x["gia_tri_lan1"],
                          moi=x["gia_tri_lan2"])  # fmt: skip
            for c in self.kh.cot[1:]:
                v = b1.hang[record_id].get(c.ten, "")
                if c.ten in lech_cot or v == "":
                    continue
                gd.cn.execute("INSERT INTO gia_tri(record_id, lan, cot, gia_tri) VALUES (?,?,?,?)",
                              (record_id, CHOT, c.ten, v))  # fmt: skip
                self._ghi(gd, phien.ma, "CHOT_KHOP", record_id=record_id, lan=CHOT, cot=c.ten, moi=v)
            gd.cn.execute("INSERT INTO doi_chieu(record_id, so_o, so_lech, luc, nguoi) VALUES (?,?,?,?,?)",
                          (record_id, ss["so_o"], len(ss["lech"]), bay_gio(), phien.ma))  # fmt: skip
            self._ghi(gd, phien.ma, "DOI_CHIEU", record_id=record_id, moi=f"{len(ss['lech'])}/{ss['so_o']} ô lệch")
            return self.trang_thai_doi_chieu(record_id, cn=gd.cn)

    def trang_thai_doi_chieu(self, record_id: str, *, cn=None) -> dict:
        with (contextlib.nullcontext(cn) if cn is not None else self._doc()) as c:
            d = c.execute("SELECT * FROM doi_chieu WHERE record_id = ?", (record_id,)).fetchone()
            lech = [dict(r) for r in c.execute("SELECT * FROM lech WHERE record_id = ? ORDER BY cot", (record_id,))]
        return {"da_doi_chieu": d is not None, "so_o": d["so_o"] if d else 0, "lech": lech,
                "con_lech": sum(1 for x in lech if not x["giai_quyet"])}  # fmt: skip

    def giai_quyet_lech(self, phien: Phien, record_id: str, cot: str, gia_tri: str, ly_do: str,
                        tham_chieu: str) -> None:
        """Ô lệch ⇒ giá trị ĐÚNG theo PHIẾU GỐC (lượt 1, lượt 2 hoặc giá trị khác), bắt buộc lý do + tham chiếu."""
        ly_do = _ly_do_hop_le(ly_do, "lý do giải quyết ô lệch")
        tham_chieu = _ly_do_hop_le(tham_chieu, "tham chiếu phiếu gốc (vd «phiếu giấy BN-012, trang 2»)")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            if self._phieu(gd.cn, record_id)["khoa"]:
                raise TuChoi("phiếu đã khoá")
            r = gd.cn.execute("SELECT * FROM lech WHERE record_id = ? AND cot = ?", (record_id, cot)).fetchone()
            if r is None:
                raise TuChoi(f"không có ô lệch {cot} ở phiếu {record_id}")
            if r["giai_quyet"]:
                raise TuChoi("ô lệch này đã giải quyết — sửa tiếp bằng «sửa bản chốt» (kèm lý do)")
            c = self.kh.cot_theo_ten[cot]
            v = self._chuan_hoa_quan_ly(c, gia_tri)
            if v != "":
                gd.cn.execute("INSERT OR REPLACE INTO gia_tri(record_id, lan, cot, gia_tri) VALUES (?,?,?,?)",
                              (record_id, CHOT, cot, v))  # fmt: skip
            gd.cn.execute("UPDATE lech SET giai_quyet = 1 WHERE record_id = ? AND cot = ?", (record_id, cot))
            self._ghi(gd, phien.ma, "GIAI_QUYET_LECH", record_id=record_id, lan=CHOT, cot=cot, moi=v, ly_do=ly_do,
                      tham_chieu=tham_chieu)  # fmt: skip

    def _chuan_hoa_quan_ly(self, c, gia_tri: str) -> str:
        v, muc, tb = chuan_hoa_nhap(c, gia_tri)
        if muc == NLE.LOI:
            raise TuChoi(f"{c.ten}: {tb}")
        pii = quet_pii_gia_tri(self.kh, c.ten, v, ma_thieu=c.ma_thieu)
        if pii:
            raise TuChoi(f"{c.ten}: giá trị giống định danh ({', '.join(pii)})")
        return v

    def _da_chot(self, cn, record_id: str) -> bool:
        d = cn.execute("SELECT 1 FROM doi_chieu WHERE record_id = ?", (record_id,)).fetchone()
        mo = cn.execute("SELECT 1 FROM lech WHERE record_id = ? AND giai_quyet = 0", (record_id,)).fetchone()
        return bool(d) and not mo

    def gia_tri_chot(self, phien: Phien, record_id: str) -> dict[str, str]:
        """Hàng bản chốt (ĐỦ cột) — chỉ người quản lý dữ liệu xem."""
        with self._doc() as cn:
            self._kiem_phien(cn, phien, QLDL)
            return self.dong_day_du(record_id, self._gia_tri(cn, record_id, CHOT))

    def sua_chot(self, phien: Phien, record_id: str, cot: str, gia_tri: str, ly_do: str, tham_chieu: str = "") -> None:
        """Sửa giá trị bản chốt (vd trả lời truy vấn theo phiếu gốc) — bắt buộc lý do; phiếu chưa khoá."""
        ly_do = _ly_do_hop_le(ly_do, "lý do sửa")
        if tham_chieu:
            tham_chieu = _ly_do_hop_le(tham_chieu, "tham chiếu")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            if self._phieu(gd.cn, record_id)["khoa"]:
                raise TuChoi("phiếu đã KHOÁ — mở khoá (kèm lý do) trước khi sửa")
            if not self._da_chot(gd.cn, record_id):
                raise TuChoi("phiếu chưa đối chiếu xong nhập kép — chưa có bản chốt")
            if cot not in self.kh.cot_theo_ten or cot == self.kh.cid.ten:
                raise TuChoi(f"«{cot}» không phải cột nhập liệu được lưu" +
                             (" (trường định danh)" if cot in self.kh.dinh_danh else ""))  # fmt: skip
            c = self.kh.cot_theo_ten[cot]
            v = self._chuan_hoa_quan_ly(c, gia_tri)
            cu = self._gia_tri(gd.cn, record_id, CHOT).get(cot, "")
            if v == cu:
                return
            if v == "":
                gd.cn.execute("DELETE FROM gia_tri WHERE record_id = ? AND lan = ? AND cot = ?", (record_id, CHOT, cot))
            else:
                gd.cn.execute("INSERT OR REPLACE INTO gia_tri(record_id, lan, cot, gia_tri) VALUES (?,?,?,?)",
                              (record_id, CHOT, cot, v))  # fmt: skip
            self._ghi(gd, phien.ma, "SUA_CHOT", record_id=record_id, lan=CHOT, cot=cot, cu=cu, moi=v, ly_do=ly_do,
                      tham_chieu=tham_chieu)  # fmt: skip

    # ── truy vấn ──
    def quet_truy_van(self, phien: Phien, record_id: str | None = None) -> dict:
        """Sinh truy vấn TỰ ĐỘNG trên bản chốt bằng ĐÚNG `NLE.kiem_gia_tri` (khoảng, danh mục, bắt buộc, logic nhánh,
        @MAXCHECKED, luật DQ). Phần máy không đánh giá được ⇒ truy vấn «kiểm tay» (không bao giờ coi là đạt). Truy vấn
        tự động đang mở mà điều kiện không còn ⇒ đóng kèm lý do; truy vấn đã đóng với cùng giá trị không mở lại."""
        tao = dong = 0
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            rids = [record_id] if record_id else [r["record_id"] for r in gd.cn.execute(
                "SELECT record_id FROM phieu WHERE nham = 0 AND khoa = 0 ORDER BY record_id")]
            for rid in rids:
                p = self._phieu(gd.cn, rid)
                if p["khoa"] or p["nham"] or not self._da_chot(gd.cn, rid):
                    continue  # phiếu đã khoá/nhầm mã: không sinh truy vấn mới (mở khoá kèm lý do trước)
                dong_h = self.dong_day_du(rid, self._gia_tri(gd.cn, rid, CHOT))
                moi: dict[tuple[str, str], tuple[str, str]] = {}
                for p in self._kiem_dong(rid, dong_h):
                    if p.muc == NLE.TRUY_VAN:
                        moi[(p.ma, p.cot)] = (p.chi_tiet, dong_h.get(p.cot, ""))
                    elif p.muc == NLE.CANH_BAO and p.ma in NLE.CHUA_DU_KIEM:
                        moi[(f"kiem_tay:{p.ma}", p.cot)] = (
                            f"máy không đánh giá được ({p.chi_tiet}) — đối chiếu tay theo phiếu gốc rồi đóng kèm lý do",
                            "")
                cu = [dict(r) for r in gd.cn.execute(
                    "SELECT * FROM truy_van WHERE record_id = ? AND nguon = 'tu_dong'", (rid,))]
                for q in cu:
                    k = (q["ma"], q["cot"])
                    if q["trang_thai"] != "dong" and k not in moi:
                        gd.cn.execute("UPDATE truy_van SET trang_thai = 'dong', dong_ly_do = ? WHERE id = ?",
                                      ("điều kiện không còn sau khi sửa giá trị", q["id"]))  # fmt: skip
                        self._ghi(gd, phien.ma, "DONG_TRUY_VAN", record_id=rid, cot=q["cot"], moi="dong",
                                  ly_do="điều kiện không còn sau khi sửa giá trị", tham_chieu=f"truy_van#{q['id']}")
                        dong += 1
                for k, (nd, gt) in moi.items():
                    da = [q for q in cu if (q["ma"], q["cot"]) == k]
                    if any(q["trang_thai"] != "dong" for q in da):
                        continue
                    if any(q["gia_tri"] == gt for q in da):
                        continue  # đã đóng với cùng giá trị (đã xác nhận đúng theo phiếu gốc) — không mở lại
                    self._tao_tv(gd, phien, rid, k[1], "tu_dong", k[0], nd, gt)
                    tao += 1
        return {"tao": tao, "dong": dong}

    def _tao_tv(self, gd, phien: Phien, rid: str, cot: str, nguon: str, ma: str, noi_dung: str, gt: str) -> int:
        cur = gd.cn.execute(
            "INSERT INTO truy_van(record_id, cot, nguon, ma, noi_dung, gia_tri, trang_thai, tao_luc, tao_boi) "
            "VALUES (?,?,?,?,?,?,'mo',?,?)", (rid, cot, nguon, ma, noi_dung, gt, bay_gio(), phien.ma))
        qid = int(cur.lastrowid)
        self._ghi(gd, phien.ma, "TAO_TRUY_VAN", record_id=rid, cot=cot, moi="mo", ly_do=noi_dung,
                  tham_chieu=f"truy_van#{qid}")  # fmt: skip
        return qid

    def tao_truy_van(self, phien: Phien, record_id: str, cot: str, noi_dung: str) -> int:
        """Truy vấn TAY của người quản lý dữ liệu."""
        noi_dung = _ly_do_hop_le(noi_dung, "nội dung truy vấn")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            self._phieu(gd.cn, record_id)
            if cot and cot not in self.kh.cot_theo_ten:
                raise TuChoi(f"«{cot}» không phải cột được lưu")
            gt = self._gia_tri(gd.cn, record_id, CHOT).get(cot, "") if cot else ""
            return self._tao_tv(gd, phien, record_id, cot, "tay", "tay", noi_dung, gt)

    def tra_loi_truy_van(self, phien: Phien, qid: int, noi_dung: str) -> None:
        noi_dung = _ly_do_hop_le(noi_dung, "nội dung trả lời")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien)
            q = gd.cn.execute("SELECT * FROM truy_van WHERE id = ?", (int(qid),)).fetchone()
            if q is None or q["trang_thai"] == "dong":
                raise TuChoi("truy vấn không có hoặc đã đóng")
            gd.cn.execute("UPDATE truy_van SET trang_thai = 'da_tra_loi', tra_loi = ? WHERE id = ?", (noi_dung, qid))
            self._ghi(gd, phien.ma, "TRA_LOI_TRUY_VAN", record_id=q["record_id"], cot=q["cot"], moi="da_tra_loi",
                      ly_do=noi_dung, tham_chieu=f"truy_van#{qid}")  # fmt: skip

    def dong_truy_van(self, phien: Phien, qid: int, ly_do: str) -> None:
        ly_do = _ly_do_hop_le(ly_do, "lý do đóng truy vấn")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            q = gd.cn.execute("SELECT * FROM truy_van WHERE id = ?", (int(qid),)).fetchone()
            if q is None or q["trang_thai"] == "dong":
                raise TuChoi("truy vấn không có hoặc đã đóng")
            gd.cn.execute("UPDATE truy_van SET trang_thai = 'dong', dong_ly_do = ? WHERE id = ?", (ly_do, qid))
            self._ghi(gd, phien.ma, "DONG_TRUY_VAN", record_id=q["record_id"], cot=q["cot"], moi="dong", ly_do=ly_do,
                      tham_chieu=f"truy_van#{qid}")  # fmt: skip

    def danh_sach_truy_van(self, record_id: str | None = None, *, chi_mo: bool = False) -> list[dict]:
        sql, ts = "SELECT * FROM truy_van", []
        dk = []
        if record_id:
            dk.append("record_id = ?")
            ts.append(record_id)
        if chi_mo:
            dk.append("trang_thai != 'dong'")
        if dk:
            sql += " WHERE " + " AND ".join(dk)
        with self._doc() as cn:
            return [dict(r) for r in cn.execute(sql + " ORDER BY id", ts)]

    # ── khoá ──
    def khoa_phieu(self, phien: Phien, record_id: str) -> None:
        """KHOÁ: chỉ người quản lý dữ liệu, sau khi đối chiếu nhập kép xong và HẾT truy vấn mở (quét lại ngay trước)."""
        with self._doc() as cn:
            self._kiem_phien(cn, phien, QLDL)
            p = self._phieu(cn, record_id)
            if p["nham"]:
                raise TuChoi("phiếu đã đánh dấu nhầm mã — không khoá")
            if p["khoa"]:
                raise TuChoi("phiếu đã khoá")
            if not self._da_chot(cn, record_id):
                raise TuChoi("chưa đối chiếu xong nhập kép (còn lượt chưa hoàn tất hoặc ô lệch chưa giải quyết)")
        self.quet_truy_van(phien, record_id)
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            mo = gd.cn.execute("SELECT COUNT(*) n FROM truy_van WHERE record_id = ? AND trang_thai != 'dong'",
                               (record_id,)).fetchone()["n"]  # fmt: skip
            if mo:
                raise TuChoi(f"còn {mo} truy vấn chưa đóng — đối chiếu phiếu gốc, trả lời và đóng trước khi khoá")
            if not self._da_chot(gd.cn, record_id):
                raise TuChoi("chưa đối chiếu xong nhập kép")
            gd.cn.execute("UPDATE phieu SET khoa = 1 WHERE record_id = ?", (record_id,))
            self._ghi(gd, phien.ma, "KHOA", record_id=record_id, moi="1")

    def mo_khoa_phieu(self, phien: Phien, record_id: str, ly_do: str) -> None:
        ly_do = _ly_do_hop_le(ly_do, "lý do mở khoá")
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            if not self._phieu(gd.cn, record_id)["khoa"]:
                raise TuChoi("phiếu chưa khoá")
            gd.cn.execute("UPDATE phieu SET khoa = 0 WHERE record_id = ?", (record_id,))
            self._ghi(gd, phien.ma, "MO_KHOA", record_id=record_id, moi="0", ly_do=ly_do)

    # ── báo cáo (không giá trị) ──
    def bao_cao_lech(self) -> dict:
        """Tỷ lệ lệch nhập kép theo biến — CHỈ số đếm, KHÔNG giá trị (bằng chứng đối chiếu nguồn cho G5)."""
        with self._doc() as cn:
            dc = [dict(r) for r in cn.execute("SELECT d.* FROM doi_chieu d JOIN phieu p USING (record_id) "
                                              "WHERE p.nham = 0")]  # fmt: skip
            lech = [dict(r) for r in cn.execute("SELECT l.* FROM lech l JOIN phieu p USING (record_id) "
                                                "WHERE p.nham = 0")]  # fmt: skip
        so_o = sum(x["so_o"] for x in dc)
        theo: dict[str, dict] = {}
        n_phieu = len(dc)
        for c in self.kh.cot[1:]:
            k = sum(1 for x in lech if x["cot"] == c.ten)
            theo[c.ten] = {"so_o": n_phieu, "so_lech": k}
        da_gq = sum(1 for x in lech if x["giai_quyet"])
        return {
            "so_phieu_doi_chieu": n_phieu, "so_o_so_sanh": so_o, "so_o_lech": len(lech),
            "ty_le_lech": round(len(lech) / so_o, 6) if so_o else None, "so_o_lech_da_giai_quyet": da_gq,
            "lech_theo_bien": {k: v for k, v in theo.items() if v["so_lech"]},
            "trang_thai": ("KHONG_CO_DU_LIEU" if not so_o else ("CON_LECH_CHUA_GIAI_QUYET" if da_gq < len(lech)
                                                                 else "DA_GIAI_QUYET_HET")),
        }  # fmt: skip

    def trang_thai(self) -> dict:
        ds = self.danh_sach_phieu()
        tv = self.danh_sach_truy_van()
        with self._doc() as cn:
            n_nk = cn.execute("SELECT COUNT(*) n FROM nhat_ky").fetchone()["n"]
        that = [p for p in ds if not p["nham"]]
        return {
            "so_phieu": len(that), "so_phieu_nham_ma": len(ds) - len(that),
            "lan1_xong": sum(p["lan1_xong"] for p in that), "lan2_xong": sum(p["lan2_xong"] for p in that),
            "da_doi_chieu": sum(p["da_doi_chieu"] for p in that), "lech_mo": sum(p["lech_mo"] for p in that),
            "truy_van_mo": sum(1 for q in tv if q["trang_thai"] != "dong"), "truy_van_tong": len(tv),
            "khoa": sum(p["khoa"] for p in that), "nhat_ky": n_nk,
            "nguoi_theo_vai": {v: sum(1 for n in self.danh_sach_nguoi() if n["vai"] == v) for v in VAI},
        }  # fmt: skip

    # ── kiểm nhật ký ──
    def kiem_nhat_ky(self, *, thu_muc_bang_chung: Path | None = None) -> dict:
        return kiem_kho_tep(self.duong_dan, self.tep_neo, thu_muc_bang_chung=thu_muc_bang_chung
                            if thu_muc_bang_chung is not None else SP.thu_muc_de_tai(self.kh.study) / "nhap_lieu")

    def dau_chuoi(self) -> dict:
        with self._doc() as cn:
            r = cn.execute("SELECT stt, hash FROM nhat_ky ORDER BY stt DESC LIMIT 1").fetchone()
        return {"stt": r["stt"], "hash": r["hash"]} if r else {"stt": 0, "hash": HASH_GOC}

    # ── xuất ──
    def xuat(self, phien: Phien, ra: Path, *, ban_nhap: bool = False, tiep_nhan: bool = False,
             exports_root: Path | None = None) -> dict:
        """CSV khuôn xuất REDCap từ BẢN CHỐT: thứ tự cột theo từ điển, checkbox `<trường>___<mã>`, mã thiếu, UTF-8.
        Chỉ khi MỌI phiếu (trừ phiếu nhầm mã) đã khoá — hoặc `ban_nhap` (gắn nhãn NHÁP, chỉ phiếu đã chốt, không qua
        cổng tiếp nhận). Tự kiểm bằng đúng đường đọc của bộ làm sạch và pandas; ghi tóm tắt bằng chứng KHÔNG giá trị
        ở exports/<mã>/nhap_lieu/."""
        ra = Path(ra).expanduser()
        kiem_vi_tri_du_lieu(ra, nhan="thư mục xuất")
        if ban_nhap and tiep_nhan:
            raise TuChoi("bản NHÁP không được đưa qua cổng tiếp nhận")
        with self._doc() as cn:
            self._kiem_phien(cn, phien, QLDL)
            ds = [dict(r) for r in cn.execute("SELECT * FROM phieu WHERE nham = 0 ORDER BY record_id")]
            if not ds:
                raise TuChoi("kho chưa có phiếu nào")
            chua_khoa = [p["record_id"] for p in ds if not p["khoa"]]
            if chua_khoa and not ban_nhap:
                raise TuChoi(f"còn {len(chua_khoa)} phiếu CHƯA KHOÁ ({', '.join(chua_khoa[:10])}"
                             f"{' …' if len(chua_khoa) > 10 else ''}) — khoá hết, hoặc xuất bản nháp --ban-nhap")
            hang = {}
            for p in ds:
                if self._da_chot(cn, p["record_id"]):
                    hang[p["record_id"]] = self.dong_day_du(p["record_id"], self._gia_tri(cn, p["record_id"], CHOT))
        if not hang:
            raise TuChoi("chưa có phiếu nào đối chiếu xong để xuất")
        bang = self._bang(hang)
        ra.mkdir(parents=True, exist_ok=True)
        luc = datetime.now().strftime("%Y%m%d-%H%M%S")
        ten = f"{self.kh.study}_nhap_lieu_cuc_bo_{luc}{'_BAN_NHAP' if ban_nhap else ''}.csv"
        csv_p = ra / ten
        NLE.ghi_csv(bang, csv_p)
        loi_kiem, da_kiem = NLE.tu_kiem_csv(bang, csv_p)
        if loi_kiem:
            NLE._xoa(csv_p)
            raise TuChoi("tự kiểm CSV thất bại — đã xoá CSV: " + "; ".join(loi_kiem))
        canh_bao = [f"{c}: giá trị pandas mặc định đọc thành THIẾU" for _, c in NLE.o_bi_pandas_coi_la_thieu(bang)]
        kt = self.kiem_nhat_ky()
        if not kt["dat"]:
            NLE._xoa(csv_p)
            raise TuChoi("nhật ký kiểm toán KHÔNG đạt — không xuất: " + "; ".join(kt["loi"][:5]))
        sha = _sha256_tep(csv_p)
        with self._gd() as gd:
            self._kiem_phien(gd.cn, phien, QLDL)
            self._ghi(gd, phien.ma, "XUAT", moi=sha, ly_do=f"{len(hang)} phiếu" + (" — BẢN NHÁP" if ban_nhap else ""),
                      tham_chieu=ten)  # fmt: skip
        tom = self._tom_tat_bang_chung(hang, csv_p, sha, da_kiem, ban_nhap, canh_bao, len(chua_khoa))
        bang_chung = self._ghi_bang_chung(tom, luc, ban_nhap)
        kq = {"csv": csv_p, "csv_sha256": sha, "so_phieu": len(hang), "bang_chung": bang_chung,
              "tu_kiem_doc_bang": da_kiem, "canh_bao": canh_bao, "ban_nhap": ban_nhap, "tiep_nhan": None}  # fmt: skip
        if tiep_nhan:
            kq["tiep_nhan"] = tiep_nhan_csv(self.kh.study, csv_p, self.kh.td_p, exports_root=exports_root)
        return kq

    def _tom_tat_bang_chung(self, hang: dict, csv_p: Path, sha: str, da_kiem: list[str], ban_nhap: bool,
                            canh_bao: list[str], so_chua_khoa: int) -> dict:
        tt = self.trang_thai()
        tv = self.danh_sach_truy_van()
        meta = self.meta()
        return {
            "kind": "nhap_lieu_cuc_bo_bang_chung", "phien_ban": 1, "study": self.kh.study,
            "luc": bay_gio(), "cong_cu": "tools/nhap_lieu_cuc_bo.py",
            "phuong_phap": ("nhập lại phiếu giấy bằng hệ nhập liệu cục bộ theo từ điển G5; nhập kép độc lập bởi hai "
                            "người khác nhau; đối chiếu từng ô; ô lệch giải quyết theo phiếu gốc có lý do và tham "
                            "chiếu; truy vấn tự động + tay; khoá phiếu trước khi xuất"),
            "ban_nhap": ban_nhap, "nhan": "BẢN NHÁP — KHÔNG dùng cho phân tích/khoá dữ liệu" if ban_nhap else "",
            "ma_kho": meta.get("ma_kho"), "dau_van_tay_kho": meta.get("dau_van_tay"),
            "dac_ta_sha256": self.kh.dac_ta_sha256, "tu_dien": self.kh.td_p.name,
            "tu_dien_sha256": _sha256_tep(self.kh.td_p),
            "luat_dq_sha256": _sha256_tep(self.kh.luat_p) if self.kh.luat_p else None,
            "so_phieu": tt["so_phieu"], "so_phieu_xuat": len(hang), "so_phieu_khoa": tt["khoa"],
            "so_phieu_chua_khoa": so_chua_khoa, "so_phieu_nham_ma": tt["so_phieu_nham_ma"],
            "nguoi_nhap_theo_vai": tt["nguoi_theo_vai"],
            "nhap_kep": self.bao_cao_lech(),
            "truy_van": {
                "tong": len(tv), "tu_dong": sum(q["nguon"] == "tu_dong" for q in tv),
                "tay": sum(q["nguon"] == "tay" for q in tv), "mo": sum(q["trang_thai"] == "mo" for q in tv),
                "da_tra_loi": sum(q["trang_thai"] == "da_tra_loi" for q in tv),
                "dong": sum(q["trang_thai"] == "dong" for q in tv),
            },
            "nhat_ky": {"so_ban_ghi": tt["nhat_ky"], "dau_chuoi": self.dau_chuoi(), "kiem_chuoi": "KHOP"},
            "csv": {"ten": csv_p.name, "sha256": sha, "so_cot": len(self.kh.cot), "so_hang": len(hang),
                    "tu_kiem_doc_bang": da_kiem, "tu_kiem": "KHOP"},
            "truong_khong_luu_dinh_danh": sorted(self.kh.dinh_danh),
            "canh_bao": canh_bao,
            "ghi_chu": "Tóm tắt KHÔNG chứa giá trị dữ liệu, mã phiếu hay mã người nhập — bằng chứng nguồn cho G5.",
            "quy_trach": QUY_TRACH, "disclaimer": CAN_KIEM,
        }  # fmt: skip

    def _ghi_bang_chung(self, tom: dict, luc: str, ban_nhap: bool) -> Path:
        d = SP.thu_muc_de_tai(self.kh.study) / "nhap_lieu"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{TIEN_TO_BANG_CHUNG}{luc}{'_BAN_NHAP' if ban_nhap else ''}.json"
        ghi_an_toan(p, json.dumps(tom, ensure_ascii=False, indent=1) + "\n")
        return p

    def ghi_bao_cao_lech(self) -> Path:
        tom = {"kind": "nhap_kep_tom_tat", "study": self.kh.study, "luc": bay_gio(),
               "phuong_phap": "nhập kép độc lập — so từng ô theo mã nghiên cứu (tools/nhap_lieu_cuc_bo.py)",
               "dac_ta_sha256": self.kh.dac_ta_sha256, "tu_dien_sha256": _sha256_tep(self.kh.td_p),
               **self.bao_cao_lech(),
               "ghi_chu": ("Tóm tắt KHÔNG chứa giá trị dữ liệu — bằng chứng đối chiếu nguồn "
                           "(G5 source_data_verification)."),
               "disclaimer": CAN_KIEM}  # fmt: skip
        d = SP.thu_muc_de_tai(self.kh.study) / "nhap_lieu"
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"NHAP_KEP_tom_tat_cuc_bo_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        ghi_an_toan(p, json.dumps(tom, ensure_ascii=False, indent=1) + "\n")
        return p

    # ── sao lưu ──
    def sao_luu(self, phien: Phien, ra: Path) -> dict:
        """Sao lưu bằng API backup của SQLite (nhất quán kể cả khi đang mở) + tệp neo; kiểm chuỗi trên BẢN SAO."""
        ra = Path(ra).expanduser()
        kiem_vi_tri_du_lieu(ra, nhan="thư mục sao lưu")
        with self._doc() as cn:
            self._kiem_phien(cn, phien, QLDL)
        ra.mkdir(parents=True, exist_ok=True)
        luc = datetime.now().strftime("%Y%m%d-%H%M%S")
        dich = ra / f"kho_{self.kh.study}_{luc}.sqlite3"
        neo_dich = ra / f"neo_{self.kh.study}_{luc}.jsonl"
        with self._khoa:
            nguon = sqlite3.connect(self.duong_dan)
            dst = sqlite3.connect(dich)
            try:
                nguon.backup(dst)
            finally:
                dst.close()
                nguon.close()
            neo_dich.write_text(self.tep_neo.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        if os.name != "nt":
            os.chmod(dich, 0o600)
        kt = kiem_kho_tep(dich, neo_dich, thu_muc_bang_chung=None)
        with self._gd() as gd:
            self._ghi(gd, phien.ma, "SAO_LUU", moi=_sha256_tep(dich), tham_chieu=dich.name,
                      ly_do="bản sao kiểm chuỗi " + ("KHỚP" if kt["dat"] else "KHÔNG KHỚP"))  # fmt: skip
        return {"tep": dich, "neo": neo_dich, "kiem": kt}


def ghi_an_toan(p: Path, noi_dung: str) -> None:
    """Ghi đè an toàn: tệp .tam rồi os.replace (không bao giờ để lại tệp ghi dở)."""
    tam = p.with_name(p.name + ".tam")
    tam.write_text(noi_dung, encoding="utf-8", newline="\n")
    os.replace(tam, p)


def tiep_nhan_csv(study: str, csv_p: Path, td_p: Path, *, exports_root: Path | None = None) -> dict:
    """Gọi THẲNG cổng tiếp nhận chuẩn (`import_real_dataset.import_dataset`) với ĐÚNG miễn trừ mà lệnh của nó áp khi
    có --dictionary (cột khai kiểu ngày, cột phân loại có mã)."""
    return RDI.import_dataset(
        study, csv_p, exports_root=exports_root if exports_root is not None else SP.EXPORTS,
        exempt_date_columns=RDI.cot_ngay_tu_dien(td_p), exempt_header_columns=RDI.cot_phan_loai_tu_dien(td_p),
    )  # fmt: skip


# ───────────────────────────── kiểm nhật ký (đọc độc lập) ─────────────────────────────


def kiem_kho_tep(duong_dan: Path, tep_neo: Path | None, *, thu_muc_bang_chung: Path | None) -> dict:
    """Tính lại CẢ chuỗi băm; đối chiếu neo (tệp neo + tóm tắt bằng chứng đã xuất); PHÁT LẠI nhật ký để dựng bảng giá
    trị/khoá/nhầm mã/lượt/truy vấn và so với kho. Bất kỳ lệch nào ⇒ ĐỎ (dat=False). Mở kho CHỈ ĐỌC."""
    loi: list[str] = []
    ds: list[dict] = []
    dau = None
    uri = Path(duong_dan).resolve().as_uri() + "?mode=ro"
    try:
        cn = sqlite3.connect(uri, uri=True)
        cn.execute("SELECT 1 FROM nhat_ky LIMIT 1")
    except sqlite3.Error as e:
        return {"dat": False, "loi": [f"không mở/đọc được kho: {e}"], "so_ban_ghi": 0, "dau_chuoi": None}
    cn.row_factory = sqlite3.Row
    try:
        trig = {r["name"] for r in cn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")}
        for t in _TRIGGER_BAT_BUOC:
            if t not in trig:
                loi.append(f"trigger chặn sửa/xoá nhật ký «{t}» đã bị gỡ")
        ds = [dict(r) for r in cn.execute("SELECT * FROM nhat_ky ORDER BY stt")]
        truoc = HASH_GOC
        theo_stt: dict[int, str] = {}
        for i, r in enumerate(ds, start=1):
            if r["stt"] != i:
                loi.append(f"đứt chuỗi: thiếu bản ghi số {i} (gặp số {r['stt']})")
                break
            if r["prev_hash"] != truoc:
                loi.append(f"đứt chuỗi tại bản ghi {r['stt']}: prev_hash không khớp băm bản trước")
                break
            if bam_ban_ghi(r["stt"], r["prev_hash"], r) != r["hash"]:
                loi.append(f"bản ghi {r['stt']} bị sửa: băm tính lại khác băm lưu")
                break
            if not re.search(r"[+-]\d{2}:\d{2}$|Z$", r["luc"]):
                loi.append(f"bản ghi {r['stt']}: thời điểm không có múi giờ")
                break
            truoc = r["hash"]
            theo_stt[r["stt"]] = r["hash"]
        dau = {"stt": ds[-1]["stt"], "hash": ds[-1]["hash"]} if ds else None
        meta = {r["khoa"]: r["gia_tri"] for r in cn.execute("SELECT khoa, gia_tri FROM meta")}
        # neo: tệp neo cạnh kho
        if tep_neo is not None:
            if not Path(tep_neo).exists():
                loi.append("mất tệp neo nhật ký — không chứng minh được nhật ký không bị cắt đuôi/tính lại")
            else:
                neo = []
                for dong in Path(tep_neo).read_text(encoding="utf-8").splitlines():
                    if dong.strip():
                        try:
                            neo.append(json.loads(dong))
                        except ValueError:
                            loi.append("tệp neo có dòng hỏng")
                for n in neo:
                    if theo_stt.get(int(n.get("stt", 0))) != n.get("hash"):
                        loi.append(f"neo stt {n.get('stt')} không khớp nhật ký (bị cắt đuôi hoặc tính lại chuỗi)")
                        break
                if neo and dau and int(neo[-1]["stt"]) != dau["stt"]:
                    loi.append(f"bản ghi cuối (số {dau['stt']}) không có neo — có bản ghi không đi qua công cụ")
                if ds and not neo:
                    loi.append("tệp neo rỗng trong khi nhật ký có bản ghi")
        # neo: tóm tắt bằng chứng đã xuất (exports/<mã>/nhap_lieu/) của CÙNG kho
        if thu_muc_bang_chung is not None and Path(thu_muc_bang_chung).is_dir():
            for p in sorted(Path(thu_muc_bang_chung).glob(f"{TIEN_TO_BANG_CHUNG}*.json")):
                try:
                    tom = json.loads(p.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if tom.get("ma_kho") != meta.get("ma_kho"):
                    continue
                dc = (tom.get("nhat_ky") or {}).get("dau_chuoi") or {}
                if dc and theo_stt.get(int(dc.get("stt", 0))) != dc.get("hash"):
                    loi.append(f"đầu chuỗi ghi trong {p.name} (stt {dc.get('stt')}) không còn khớp nhật ký")
        if not loi:
            loi += _phat_lai(cn, ds)
    finally:
        cn.close()
    return {"dat": not loi, "loi": loi, "so_ban_ghi": len(ds), "dau_chuoi": dau}


def _phat_lai(cn: sqlite3.Connection, ds: list[dict]) -> list[str]:
    """Dựng lại trạng thái từ nhật ký và so với bảng — sửa thẳng bảng (không qua công cụ) ⇒ lệch ⇒ ĐỎ."""
    loi = []
    gt: dict[tuple[str, str, str], str] = {}
    khoa: dict[str, str] = {}
    nham: dict[str, str] = {}
    phieu: set[str] = set()
    luot_nguoi: dict[tuple[str, str], str] = {}
    luot_xong: set[tuple[str, str]] = set()
    tv: dict[str, str] = {}
    nguoi: dict[str, str] = {}
    lech: dict[tuple[str, str], int] = {}
    for r in ds:
        hd = r["hanh_dong"]
        if hd in HANH_DONG_GIA_TRI:
            k = (r["record_id"], r["lan"], r["cot"])
            if r["moi"] == "":
                gt.pop(k, None)
            else:
                gt[k] = r["moi"]
            if hd == "GIAI_QUYET_LECH":
                lech[(r["record_id"], r["cot"])] = 1
        elif hd == "LECH":
            lech[(r["record_id"], r["cot"])] = 0
        elif hd in ("KHOA", "MO_KHOA"):
            khoa[r["record_id"]] = r["moi"]
        elif hd in ("NHAM_MA", "BO_NHAM_MA"):
            nham[r["record_id"]] = r["moi"]
        elif hd == "TAO_PHIEU":
            phieu.add(r["record_id"])
        elif hd == "BAT_DAU_LUOT":
            luot_nguoi[(r["record_id"], r["lan"])] = r["nguoi"]
        elif hd == "HOAN_TAT_LUOT":
            luot_xong.add((r["record_id"], r["lan"]))
        elif hd in ("TAO_TRUY_VAN", "TRA_LOI_TRUY_VAN", "DONG_TRUY_VAN"):
            tv[r["tham_chieu"]] = r["moi"]
        elif hd == "THEM_NGUOI":
            nguoi[r["cot"]] = r["moi"]
    kho_gt = {(r["record_id"], r["lan"], r["cot"]): r["gia_tri"] for r in cn.execute("SELECT * FROM gia_tri")}
    if kho_gt != gt:
        lech_o = sorted(set(kho_gt.items()) ^ set(gt.items()))[:3]
        loi.append("giá trị trong kho KHÔNG khớp nhật ký (sửa thẳng kho không qua công cụ?) — ô: "
                   + ", ".join(f"{k[0]}/{k[1]}/{k[2]}" for k, _ in lech_o))  # fmt: skip
    for r in cn.execute("SELECT * FROM phieu"):
        if r["record_id"] not in phieu:
            loi.append(f"phiếu {r['record_id']} không có bản ghi tạo trong nhật ký")
        if str(r["khoa"]) != khoa.get(r["record_id"], "0"):
            loi.append(f"trạng thái khoá phiếu {r['record_id']} không khớp nhật ký")
        if str(r["nham"]) != nham.get(r["record_id"], "0"):
            loi.append(f"cờ nhầm mã phiếu {r['record_id']} không khớp nhật ký")
    if len(phieu) != cn.execute("SELECT COUNT(*) FROM phieu").fetchone()[0]:
        loi.append("số phiếu trong kho khác số phiếu tạo trong nhật ký")
    for r in cn.execute("SELECT * FROM luot"):
        k = (r["record_id"], r["lan"])
        if luot_nguoi.get(k) != r["nguoi"] or (bool(r["xong"]) != (k in luot_xong)):
            loi.append(f"lượt {k[1]} của phiếu {k[0]} không khớp nhật ký (người nhập/hoàn tất)")
    for r in cn.execute("SELECT id, trang_thai FROM truy_van"):
        if tv.get(f"truy_van#{r['id']}") != r["trang_thai"]:
            loi.append(f"truy vấn #{r['id']} không khớp nhật ký")
    if len(tv) != cn.execute("SELECT COUNT(*) FROM truy_van").fetchone()[0]:
        loi.append("số truy vấn trong kho khác nhật ký")
    kho_nguoi = {r["ma"]: r["vai"] for r in cn.execute("SELECT ma, vai FROM nguoi")}
    if kho_nguoi != nguoi:
        loi.append("danh sách người nhập/vai không khớp nhật ký")
    kho_lech = {(r["record_id"], r["cot"]): r["giai_quyet"] for r in cn.execute("SELECT * FROM lech")}
    if kho_lech != lech:
        loi.append("bảng ô lệch nhập kép không khớp nhật ký")
    return loi


# ───────────────────────────── hồ sơ thẩm định hệ thống ─────────────────────────────

# Đặc tả yêu cầu người dùng (URS). Mỗi test của hệ ghi mã YC ở DÒNG ĐẦU docstring ⇒ ma trận truy vết sinh tự động.
YEU_CAU: list[tuple[str, str]] = [
    ("YC-01", "Kho SQLite ngoài OneDrive/thư mục đồng bộ đám mây và ngoài mọi repo git; mặc định ~/NhapLieu/<mã>/"),
    ("YC-02", "Kho ràng vào dấu vân tay từ điển G5; từ điển đổi ⇒ từ chối mở, nói rõ cách xử lý, không tự di trú"),
    ("YC-03", "Không lưu trường Identifier? = y hoặc tên cột định danh theo luật cổng tiếp nhận; mã phiếu chỉ là mã "
              "nghiên cứu; giá trị khớp mẫu định danh bị từ chối"),
    ("YC-04", "Giao diện web chỉ nghe 127.0.0.1, cổng tự chọn; chặn Host lạ và yêu cầu chéo trang (CSRF)"),
    ("YC-05", "Biểu mẫu theo instrument: nhãn, mã lựa chọn, kiểu, khoảng hợp lệ, câu bắt buộc, mã thiếu; lỗi tiếng "
              "Việt tại chỗ"),
    ("YC-06", "Logic nhánh ẩn/hiện bằng đúng danh_gia_logic; calc bằng tinh_calc; không đánh giá được ⇒ cảnh báo"),
    ("YC-07", "Người nhập khai theo đề tài với vai; phiên gắn người; PIN băm có muối, không lưu dạng rõ; không tự "
              "nhận là chữ ký điện tử"),
    ("YC-08", "Nhật ký chỉ-ghi-thêm có chuỗi băm: thời điểm có múi giờ, người, mã phiếu, lượt, trường, cũ→mới, lý do "
              "(bắt buộc khi sửa giá trị đã lưu)"),
    ("YC-09", "kiem-nhat-ky tính lại cả chuỗi; đứt/sửa ngầm/cắt đuôi/kho lệch nhật ký ⇒ ĐỎ, mã thoát khác 0; không "
              "có lệnh xoá nhật ký"),
    ("YC-10", "Nhập kép: hai lượt độc lập bởi hai người khác nhau; người lượt 2 không thấy giá trị lượt 1"),
    ("YC-11", "Đối chiếu từng ô; ô lệch giải quyết có lý do + tham chiếu phiếu gốc, ghi nhật ký; báo cáo tỷ lệ lệch "
              "theo biến không chứa giá trị"),
    ("YC-12", "Truy vấn tự động từ luật DQ/khoảng/logic + truy vấn tay; mở → trả lời → đóng, có nhật ký"),
    ("YC-13", "Khoá phiếu chỉ vai quản lý dữ liệu, sau đối chiếu xong và hết truy vấn mở; mở khoá bắt buộc lý do"),
    ("YC-14", "Xuất CSV khuôn REDCap (thứ tự cột từ điển, checkbox <trường>___<mã>, mã thiếu, UTF-8) ra ngoài repo; "
              "chỉ khi mọi phiếu khoá hoặc bản nháp có nhãn"),
    ("YC-15", "Tự kiểm CSV bằng đường đọc của bộ làm sạch và pandas; tuỳ chọn gọi cổng tiếp nhận chuẩn"),
    ("YC-16", "Tóm tắt bằng chứng không chứa giá trị ở exports/<mã>/nhap_lieu/ cho G5"),
    ("YC-17", "Đầu–cuối: dữ liệu mô phỏng đúng từ điển nhập hai lượt, lệch, giải quyết, khoá, xuất, qua cổng tiếp "
              "nhận, khớp từng ô"),
    ("YC-18", "Hồ sơ thẩm định sinh tự động: yêu cầu, ma trận truy vết, kết quả test kèm commit/phiên bản, giới hạn, "
              "đối chiếu ICH E6(R3)/ALCOA+"),
    ("YC-19", "Sao lưu nhất quán ra ngoài repo/đám mây và kiểm chuỗi trên bản sao"),
]

GIOI_HAN: list[str] = [
    "Quy trách phiên cục bộ (mã người + PIN tuỳ chọn) — KHÔNG phải chữ ký điện tử theo chuẩn nào; PIN ngắn đoán được "
    "nếu có tệp kho, nên kho phải nằm trong tài khoản máy có mật khẩu.",
    "Một người khai hai mã khác nhau để nhập cả hai lượt thì máy không phát hiện được — phân công nhập kép do người "
    "quản lý dữ liệu kiểm soát.",
    "Nhật ký chuỗi băm phát hiện sửa/xoá/cắt đuôi/tính lại chuỗi nhờ tệp neo và đầu chuỗi ghi ở tóm tắt bằng chứng; "
    "người có quyền ghi CẢ kho, tệp neo và mọi tóm tắt đã xuất cùng lúc vẫn có thể làm giả — tóm tắt bằng chứng "
    "nằm trong repo git (lịch sử commit là neo ngoài máy).",
    "Thời điểm lấy theo đồng hồ của máy nhập liệu; máy sai giờ thì nhật ký sai giờ.",
    "Logic nhánh/calc/luật DQ dùng tập con biểu thức REDCap của nhap_lieu_excel (if, so sánh, + − × ÷, and/or); hàm "
    "khác (datediff, round, sum…) ⇒ «không đánh giá được», câu được hiện và sinh truy vấn kiểm tay, không coi là đạt.",
    "Trường calc không xuất vào CSV (giống đường Excel); biến phái sinh tính ở bước sau (bien_phai_sinh.py).",
    "Trường ngày-giờ (datetime_*) chứa mẫu ngày bị cổng tiếp nhận coi là định danh — hệ chặn từ lúc nhập cho khớp "
    "cổng.",
    "Không có chế độ người bệnh tự điền, không mở mạng; nhiều người nhập cùng lúc trên MỘT máy (tuần tự).",
    "Hồ sơ thẩm định là bằng chứng kiểm thử tự động trên máy chạy lệnh; chạy «ho-so-tham-dinh» trên chính máy nhập "
    "liệu để hồ sơ ghi đúng môi trường của máy đó.",
]

# Đối chiếu yêu cầu quy phạm — CHỈ ghi tên tài liệu và PHẦN, KHÔNG ghi số mục khi không chắc (bác sĩ dặn 23/11/2026).
DOI_CHIEU_QUY_PHAM: list[tuple[str, str, str, list[str]]] = [
    ("ICH E6(R3) — Annex 1, phần Data Governance (Investigator and Sponsor): vòng đời dữ liệu",
     "thu thập dữ liệu; metadata gồm audit trail; rà soát dữ liệu; sửa dữ liệu có lý do và lưu vết; hoàn tất bộ "
     "dữ liệu trước phân tích",
     "nhập kép + đối chiếu theo phiếu gốc; nhật ký chuỗi băm cũ→mới có lý do; truy vấn; khoá phiếu; xuất chỉ khi đã "
     "khoá", ["YC-08", "YC-09", "YC-10", "YC-11", "YC-12", "YC-13", "YC-14"]),
    ("ICH E6(R3) — Annex 1, phần Data Governance (Investigator and Sponsor): hệ thống máy tính",
     "thẩm định phù hợp mục đích theo rủi ro; an ninh; quản lý người dùng và vai trò; xử lý khi hệ hỏng",
     "hồ sơ thẩm định sinh tự động + ma trận truy vết; chỉ nghe 127.0.0.1, CSRF, chặn Host lạ; người khai theo vai; "
     "sao lưu + kiểm bản sao", ["YC-04", "YC-07", "YC-18", "YC-19"]),
    ("ICH E6(R3) — nguyên tắc GCP về chất lượng và độ tin cậy dữ liệu, bảo vệ thông tin người tham gia",
     "dữ liệu đáng tin cậy; bảo mật thông tin định danh",
     "không lưu định danh; mã phiếu là mã nghiên cứu; kho ngoài đám mây/ngoài repo", ["YC-01", "YC-03"]),
    ("ALCOA+ — Attributable", "biết ai ghi/sửa", "phiên gắn mã người; mọi bản ghi nhật ký có mã người",
     ["YC-07", "YC-08"]),
    ("ALCOA+ — Legible", "đọc được suốt vòng đời", "giá trị lưu dạng chữ UTF-8, mã giữ nguyên như từ điển",
     ["YC-14"]),
    ("ALCOA+ — Contemporaneous", "ghi lúc làm", "thời điểm có múi giờ ở mỗi bản ghi nhật ký", ["YC-08"]),
    ("ALCOA+ — Original", "giữ bản gốc/bản sao xác thực", "phiếu giấy là nguồn; hai lượt nhập giữ nguyên, bản chốt "
     "tách riêng; sửa không xoá lịch sử", ["YC-10", "YC-11"]),
    ("ALCOA+ — Accurate", "chính xác", "nhập kép độc lập, đối chiếu từng ô, kiểm giá trị + luật DQ, truy vấn",
     ["YC-05", "YC-10", "YC-11", "YC-12"]),
    ("ALCOA+ — Complete", "đầy đủ", "mọi biểu mẫu phải lưu, câu bắt buộc phải có giá trị/mã thiếu; phát lại nhật ký "
     "so với kho", ["YC-09", "YC-13"]),
    ("ALCOA+ — Consistent", "nhất quán", "một dấu vân tay từ điển; cùng bộ đánh giá với đường Excel và bộ làm sạch",
     ["YC-02", "YC-06"]),
    ("ALCOA+ — Enduring", "bền", "SQLite ngoài thư mục đồng bộ; sao lưu nhất quán + kiểm bản sao", ["YC-01", "YC-19"]),
    ("ALCOA+ — Available", "truy xuất được", "xuất CSV khuôn REDCap + tóm tắt bằng chứng cho G5",
     ["YC-14", "YC-16"]),
]
NGUON_QUY_PHAM = [
    "ICH E6(R3) Guideline for Good Clinical Practice — bản Step 4 (tháng 1/2025): phần Nguyên tắc và Annex 1.",
    "ALCOA+: thuật ngữ dùng trong EMA «Guideline on computerised systems and electronic data in clinical trials» "
    "(2023) và MHRA «GXP Data Integrity Guidance and Definitions» (2018).",
]
TEP_TEST = ("tests/test_nhap_lieu_cuc_bo_20261123.py", "tests/test_nhap_lieu_cuc_bo_web_20261123.py")


def truy_vet_test(tep_test: tuple[str, ...] = TEP_TEST, goc: Path = BASE) -> dict[str, list[str]]:
    """{YC: [tệp::test]} đọc từ DÒNG ĐẦU docstring của từng hàm test (ast — không chạy test)."""
    ra: dict[str, list[str]] = {ma: [] for ma, _ in YEU_CAU}
    for rel in tep_test:
        p = goc / rel
        if not p.exists():
            continue
        cay = ast.parse(p.read_text(encoding="utf-8"))
        for nut in ast.walk(cay):
            if isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef)) and nut.name.startswith("test_"):
                doc = (ast.get_docstring(nut) or "").splitlines()
                for ma in re.findall(r"YC-\d{2}", doc[0] if doc else ""):
                    ra.setdefault(ma, []).append(f"{Path(rel).name}::{nut.name}")
    return ra


def doc_junit(p: Path) -> dict[str, str]:
    """{tên test: passed|failed|error|skipped} từ tệp JUnit XML của pytest."""
    kq: dict[str, str] = {}
    goc = ET.parse(p).getroot()
    for tc in goc.iter("testcase"):
        ten = re.sub(r"\[.*\]$", "", tc.get("name", ""))
        lop = (tc.get("classname") or "").rsplit(".", 1)[-1]
        tt = "passed"
        for con in tc:
            if con.tag in ("failure", "error"):
                tt = "failed" if con.tag == "failure" else "error"
            elif con.tag == "skipped":
                tt = "skipped"
        khoa = f"{lop}.py::{ten}" if lop else ten
        if kq.get(khoa) not in ("failed", "error"):
            kq[khoa] = tt
    return kq


def _moi_truong() -> dict:
    from importlib import metadata  # noqa: PLC0415

    thu_vien = {}
    for ten in ("flask", "werkzeug", "jinja2", "openpyxl", "pandas", "pytest"):
        try:
            thu_vien[ten] = metadata.version(ten)
        except metadata.PackageNotFoundError:
            thu_vien[ten] = "không cài"
    thu_vien["sqlite"] = sqlite3.sqlite_version

    def _git(*a: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(BASE), *a], capture_output=True, text=True, timeout=30,
                                  check=False).stdout.strip()  # fmt: skip
        except (OSError, subprocess.SubprocessError):
            return ""

    ban = _git("status", "--porcelain", "--", "tools/nhap_lieu_cuc_bo.py", "tools/nhap_lieu_cuc_bo_web.py",
               "tools/nhap_lieu_excel.py", *TEP_TEST)
    return {"commit": _git("rev-parse", "HEAD") or "không đo được", "co_sua_chua_commit": bool(ban),
            "python": platform.python_version(), "he_dieu_hanh": f"{platform.system()} {platform.release()}",
            "thu_vien": thu_vien}  # fmt: skip


def ho_so_tham_dinh(ra: Path, *, junit: Path | None = None) -> dict:
    """Sinh hồ sơ thẩm định hệ thống máy tính (.md + .json). `junit` có sẵn ⇒ dùng; không có ⇒ chạy pytest thật.
    Hồ sơ KHÔNG chứa dữ liệu, đường dẫn tuyệt đối hay tên máy người dùng."""
    thu_muc_ra = Path(ra).expanduser()
    tvet = truy_vet_test()
    tam = None
    if junit is None:
        tam = tempfile.TemporaryDirectory(prefix="nlcb-junit-")
        junit = Path(tam.name) / "ket_qua.xml"
        subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}",
                        *TEP_TEST], cwd=str(BASE), check=False, capture_output=True, timeout=1800)  # fmt: skip
    try:
        kq_test = doc_junit(Path(junit)) if Path(junit).exists() else {}
    finally:
        if tam is not None:
            tam.cleanup()
    mt = _moi_truong()
    hang = []
    for ma, mo_ta in YEU_CAU:
        tests = tvet.get(ma, [])
        tt = [kq_test.get(t, "không có kết quả") for t in tests]
        dat = bool(tests) and all(x == "passed" for x in tt)
        hang.append({"ma": ma, "yeu_cau": mo_ta, "test": tests, "ket_qua": tt, "dat": dat})
    tong = {"so_test": len(kq_test), "dat": sum(v == "passed" for v in kq_test.values()),
            "truot": sum(v in ("failed", "error") for v in kq_test.values()),
            "bo_qua": sum(v == "skipped" for v in kq_test.values())}  # fmt: skip
    dat_het = all(h["dat"] for h in hang) and tong["truot"] == 0 and tong["so_test"] > 0
    goi = {"kind": "ho_so_tham_dinh_he_nhap_lieu_cuc_bo", "luc": bay_gio(), "moi_truong": mt, "tong_ket_test": tong,
           "ma_tran": hang, "gioi_han": GIOI_HAN, "nguon_quy_pham": NGUON_QUY_PHAM,
           "doi_chieu_quy_pham": [{"yeu_cau_quy_pham": a, "noi_dung": b, "he_dap_ung": c, "yc": d}
                                  for a, b, c, d in DOI_CHIEU_QUY_PHAM],
           "trang_thai": "DAT" if dat_het else "CHUA_DAT", "quy_trach": QUY_TRACH, "disclaimer": CAN_KIEM}  # fmt: skip
    dong = [
        "# HỒ SƠ THẨM ĐỊNH HỆ THỐNG MÁY TÍNH — hệ nhập liệu cục bộ theo từ điển G5", "",
        f"- Thời điểm: {goi['luc']}",
        f"- Mã commit: `{mt['commit']}`" + (" (có sửa chưa commit ở tệp hệ)" if mt["co_sua_chua_commit"] else ""),
        f"- Python {mt['python']} · {mt['he_dieu_hanh']} · "
        + " · ".join(f"{k} {v}" for k, v in mt["thu_vien"].items()),
        f"- Kết quả test: {tong['dat']}/{tong['so_test']} đạt · {tong['truot']} trượt · {tong['bo_qua']} bỏ qua",
        f"- Trạng thái: **{goi['trang_thai']}**", "",
        "## 1. Đặc tả yêu cầu người dùng (URS)", "", "| Mã | Yêu cầu |", "|---|---|",
        *[f"| {ma} | {mt_} |" for ma, mt_ in YEU_CAU], "",
        "## 2. Ma trận truy vết yêu cầu ↔ test", "", "| Mã | Test | Kết quả | Đạt |", "|---|---|---|---|",
        *[f"| {h['ma']} | {'<br>'.join(h['test']) or '— CHƯA CÓ TEST —'} | "
          f"{', '.join(sorted(set(h['ket_qua']))) or '—'} | {'✓' if h['dat'] else '✗'} |" for h in hang], "",
        "## 3. Giới hạn đã biết", "", *[f"- {g}" for g in GIOI_HAN], "",
        "## 4. Đối chiếu ICH E6(R3) và ALCOA+", "",
        "Chỉ ghi tên tài liệu và PHẦN; không ghi số mục khi chưa đối chiếu nguyên văn.", "",
        "| Yêu cầu quy phạm | Nội dung | Hệ đáp ứng | YC |", "|---|---|---|---|",
        *[f"| {a} | {b} | {c} | {', '.join(d)} |" for a, b, c, d in DOI_CHIEU_QUY_PHAM], "",
        "Nguồn:", *[f"- {n}" for n in NGUON_QUY_PHAM], "", QUY_TRACH, "", CAN_KIEM, "",
    ]  # fmt: skip
    thu_muc_ra.mkdir(parents=True, exist_ok=True)
    luc = datetime.now().strftime("%Y%m%d-%H%M%S")
    md = thu_muc_ra / f"HO_SO_THAM_DINH_nhap_lieu_cuc_bo_{luc}.md"
    js = md.with_suffix(".json")
    ghi_an_toan(md, "\n".join(dong))
    ghi_an_toan(js, json.dumps(goi, ensure_ascii=False, indent=1) + "\n")
    return {**goi, "md": md, "json": js}


# ───────────────────────────── CLI ─────────────────────────────


def _hoi_pin(nhan: str) -> str:
    return getpass.getpass(f"{nhan}: ")


def _dang_nhap_cli(kho: Kho, ma: str) -> Phien:
    return kho.dang_nhap(ma, _hoi_pin(f"PIN của {ma}") if kho.can_pin(ma) else None)


def _mo_kho(args) -> Kho:
    return Kho.mo(args.study, Path(args.kho) if args.kho else None, tu_dien=args.dictionary,
                  ma_thieu=args.ma_thieu, luat_dq=args.luat_dq)  # fmt: skip


def lenh_khoi_tao(args) -> int:
    pin = None
    if args.co_pin:
        pin = _hoi_pin(f"Đặt PIN cho {args.quan_ly}")
        if pin != _hoi_pin("Nhập lại PIN"):
            raise TuChoi("hai lần PIN không khớp")
    kho = Kho.khoi_tao(args.study, Path(args.kho) if args.kho else None, args.quan_ly, pin=pin,
                       tu_dien=args.dictionary, ma_thieu=args.ma_thieu, luat_dq=args.luat_dq)  # fmt: skip
    kh = kho.kh
    print(f"✓ Kho nhập liệu: {kho.thu_muc}")
    print(f"   Từ điển {kh.td_p.name} · {len(kh.cot) - 1} cột nhập · {len(kh.forms)} biểu mẫu · dấu vân tay "
          f"{kh.dau_van_tay[:12]}…")
    for ten, ly in kh.dinh_danh.items():
        print(f"   ⛔ không lưu «{ten}»: {ly}")
    for b in kh.bo_qua:
        print(f"   ⚪ không nhập tay: {b}")
    print(f"   Người quản lý dữ liệu: {args.quan_ly}. Khai người nhập: nguoi-them --vai nhap_lieu_1|nhap_lieu_2")
    print(QUY_TRACH)
    return MA_OK


def lenh_nguoi_them(args) -> int:
    kho = _mo_kho(args)
    phien = _dang_nhap_cli(kho, args.boi)
    pin = None
    if args.co_pin:
        pin = _hoi_pin(f"Đặt PIN cho {args.ma}")
        if pin != _hoi_pin("Nhập lại PIN"):
            raise TuChoi("hai lần PIN không khớp")
    kho.them_nguoi(phien, args.ma, args.vai, pin)
    print(f"✓ Đã khai {args.ma} ({args.vai})")
    return MA_OK


def lenh_mo(args) -> int:
    kho = _mo_kho(args)
    import nhap_lieu_cuc_bo_web as WEB  # noqa: PLC0415 — Flask chỉ cần khi mở giao diện

    return WEB.chay(kho, cong=args.cong, mo_trinh_duyet=not args.khong_mo_trinh_duyet)


def lenh_trang_thai(args) -> int:
    kho = _mo_kho(args)
    tt = kho.trang_thai()
    print(json.dumps(tt, ensure_ascii=False, indent=1))
    return MA_OK


def lenh_kiem_nhat_ky(args) -> int:
    # Chỉ đọc kho — KHÔNG cần từ điển khớp để kiểm nhật ký (kiểm được cả kho của từ điển cũ).
    thu_muc = Path(args.kho).expanduser() if args.kho else thu_muc_kho_mac_dinh(args.study)
    kiem_vi_tri_du_lieu(thu_muc)
    if not (thu_muc / TEN_KHO).exists():
        raise KhongDoDuoc(f"không có kho ở {thu_muc}")
    kt = kiem_kho_tep(thu_muc / TEN_KHO, thu_muc / TEN_NEO,
                      thu_muc_bang_chung=SP.thu_muc_de_tai(args.study) / "nhap_lieu")  # fmt: skip
    if kt["dat"]:
        print(f"✓ Nhật ký KHỚP: {kt['so_ban_ghi']} bản ghi · đầu chuỗi {kt['dau_chuoi']['hash'][:16]}… "
              f"(stt {kt['dau_chuoi']['stt']}) · neo khớp · phát lại khớp kho")
        return MA_OK
    print("🔴 NHẬT KÝ KHÔNG ĐẠT:")
    for x in kt["loi"]:
        print(f"   ✗ {x}")
    return MA_LOI


def lenh_bao_cao_lech(args) -> int:
    kho = _mo_kho(args)
    p = kho.ghi_bao_cao_lech()
    bc = kho.bao_cao_lech()
    print(f"Nhập kép: {bc['so_phieu_doi_chieu']} phiếu · {bc['so_o_so_sanh']} ô · {bc['so_o_lech']} ô lệch "
          f"({bc['so_o_lech_da_giai_quyet']} đã giải quyết) · {bc['trang_thai']}")
    print(f"   Bằng chứng (không giá trị): {p}")
    return MA_OK if bc["trang_thai"] == "DA_GIAI_QUYET_HET" else MA_LOI


def lenh_xuat(args) -> int:
    kho = _mo_kho(args)
    phien = _dang_nhap_cli(kho, args.boi)
    ra = Path(args.ra).expanduser() if args.ra else kho.thu_muc / "xuat"
    kq = kho.xuat(phien, ra, ban_nhap=args.ban_nhap, tiep_nhan=args.tiep_nhan)
    print(f"✓ CSV: {kq['csv']} ({kq['so_phieu']} phiếu; tự kiểm khớp từng ô: {' · '.join(kq['tu_kiem_doc_bang'])})")
    if kq["ban_nhap"]:
        print("   ⚠ BẢN NHÁP — không dùng cho phân tích/khoá dữ liệu")
    for c in kq["canh_bao"]:
        print(f"   ⚠ {c}")
    print(f"   Bằng chứng (không giá trị): {kq['bang_chung']}")
    if kq["tiep_nhan"] is not None:
        print(f"→ Cổng tiếp nhận: {kq['tiep_nhan']['status']}")
        return MA_OK if kq["tiep_nhan"]["pii_scan"]["passed"] else MA_LOI
    print(CAN_KIEM)
    return MA_OK


def lenh_sao_luu(args) -> int:
    kho = _mo_kho(args)
    phien = _dang_nhap_cli(kho, args.boi)
    kq = kho.sao_luu(phien, Path(args.ra))
    print(f"✓ Sao lưu: {kq['tep']} · kiểm chuỗi bản sao: {'KHỚP' if kq['kiem']['dat'] else 'KHÔNG KHỚP'}")
    return MA_OK if kq["kiem"]["dat"] else MA_LOI


def lenh_tu_dien_kho(args) -> int:
    thu_muc = Path(args.kho).expanduser() if args.kho else thu_muc_kho_mac_dinh(args.study)
    p = thu_muc / TEN_KHO
    if not p.exists():
        raise KhongDoDuoc(f"không có kho ở {thu_muc}")
    ra = Path(args.ra).expanduser()  # từ điển chỉ là đặc tả biến — không chứa dữ liệu phiếu
    cn = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        r = cn.execute("SELECT gia_tri FROM meta WHERE khoa = 'tu_dien_csv'").fetchone()
    finally:
        cn.close()
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(r[0], encoding="utf-8", newline="")
    print(f"✓ Từ điển mà kho đang ràng: {ra}")
    return MA_OK


def lenh_ho_so(args) -> int:
    ra = Path(args.ra).expanduser() if args.ra else (SP.thu_muc_de_tai(args.study) / "nhap_lieu" if args.study
                                                     else None)  # fmt: skip
    if ra is None:
        raise TuChoi("cần --ra hoặc --study")
    kq = ho_so_tham_dinh(ra, junit=Path(args.junit) if args.junit else None)
    t = kq["tong_ket_test"]
    print(f"Hồ sơ thẩm định: {kq['md']}")
    print(f"   {t['dat']}/{t['so_test']} test đạt · ma trận {sum(h['dat'] for h in kq['ma_tran'])}/{len(kq['ma_tran'])}"
          f" yêu cầu có test đạt · {kq['trang_thai']}")
    return MA_OK if kq["trang_thai"] == "DAT" else MA_LOI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Hệ nhập liệu cục bộ theo từ điển REDCap của G5. " + CAN_KIEM)
    sub = ap.add_subparsers(dest="lenh", required=True)

    def chung(p, *, study_bat_buoc: bool = True) -> None:
        p.add_argument("--study", required=study_bat_buoc)
        p.add_argument("--kho", help="thư mục kho (mặc định ~/NhapLieu/<mã>) — ngoài OneDrive, ngoài repo")
        p.add_argument("--dictionary", help="từ điển REDCap (mặc định exports/<mã>/G5_REDCap_dictionary_<mã>.csv)")
        p.add_argument("--ma-thieu", help="mã thiếu (mặc định exports/<mã>/_ma-thieu-theo-bien.csv)")
        p.add_argument("--luat-dq", help="luật DQ (mặc định exports/<mã>/_luat-dq.csv)")

    k = sub.add_parser("khoi-tao", help="tạo kho + người quản lý dữ liệu đầu tiên")
    chung(k)
    k.add_argument("--quan-ly", required=True, help="mã/chữ viết tắt người quản lý dữ liệu")
    k.add_argument("--co-pin", action="store_true", help="đặt PIN (hỏi khi chạy, không hiện)")
    n = sub.add_parser("nguoi-them", help="khai người nhập")
    chung(n)
    n.add_argument("--ma", required=True)
    n.add_argument("--vai", required=True, choices=VAI)
    n.add_argument("--boi", required=True, help="mã người quản lý dữ liệu thực hiện")
    n.add_argument("--co-pin", action="store_true")
    m = sub.add_parser("mo", help="mở giao diện web cục bộ (127.0.0.1)")
    chung(m)
    m.add_argument("--cong", type=int, default=0, help="cổng (mặc định 0 = tự chọn cổng trống)")
    m.add_argument("--khong-mo-trinh-duyet", action="store_true")
    chung(sub.add_parser("trang-thai", help="số đếm trạng thái — không giá trị"))
    kn = sub.add_parser("kiem-nhat-ky", help="tính lại chuỗi băm + neo + phát lại")
    kn.add_argument("--study", required=True)
    kn.add_argument("--kho")
    chung(sub.add_parser("bao-cao-lech", help="tỷ lệ lệch nhập kép theo biến (không giá trị)"))
    x = sub.add_parser("xuat", help="CSV khuôn REDCap + bằng chứng cho G5")
    chung(x)
    x.add_argument("--boi", required=True)
    x.add_argument("--ra", help="thư mục ra (mặc định <kho>/xuat) — ngoài repo")
    x.add_argument("--ban-nhap", action="store_true", help="xuất khi còn phiếu chưa khoá — gắn nhãn NHÁP")
    x.add_argument("--tiep-nhan", action="store_true", help="gọi luôn cổng tiếp nhận import_real_dataset")
    s = sub.add_parser("sao-luu", help="sao lưu kho + kiểm bản sao")
    chung(s)
    s.add_argument("--boi", required=True)
    s.add_argument("--ra", required=True)
    t = sub.add_parser("tu-dien-kho", help="ghi lại từ điển mà kho đang ràng")
    t.add_argument("--study", required=True)
    t.add_argument("--kho")
    t.add_argument("--ra", required=True)
    h = sub.add_parser("ho-so-tham-dinh", help="hồ sơ thẩm định hệ thống máy tính")
    h.add_argument("--study")
    h.add_argument("--ra")
    h.add_argument("--junit", help="tệp JUnit XML đã có (không thì chạy pytest)")
    args = ap.parse_args(argv)
    lenh = {"khoi-tao": lenh_khoi_tao, "nguoi-them": lenh_nguoi_them, "mo": lenh_mo, "trang-thai": lenh_trang_thai,
            "kiem-nhat-ky": lenh_kiem_nhat_ky, "bao-cao-lech": lenh_bao_cao_lech, "xuat": lenh_xuat,
            "sao-luu": lenh_sao_luu, "tu-dien-kho": lenh_tu_dien_kho, "ho-so-tham-dinh": lenh_ho_so}  # fmt: skip
    try:
        return lenh[args.lenh](args)
    except TuChoi as e:
        print(f"⛔ {e}")
        return MA_TU_CHOI
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
