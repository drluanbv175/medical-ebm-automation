#!/usr/bin/env python3
"""Khung BIỂU BẢNG chuẩn — bảng trống, biểu đồ, sơ đồ dự kiến — cho chương «Dự kiến kết quả» của đề cương nộp.

VÌ SAO (bác sĩ 19/11/2026): «Tôi đọc qua đề cương thấy phần trình bày biểu bảng chưa có và chưa đúng chuẩn; hãy xây dựng
bổ sung vấn đề này thật hoàn thiện» … «và cả đồ thị và tất cả vấn đề liên quan số liệu phân tích, kết quả phân tích».
Đo ngày đó: chương 5 do máy dựng chỉ chép 2–4 bảng chung của kế hoạch phân tích (bảng nền 2 dòng, ô kết cục «…», dòng
«(12 biến)»), KHÔNG có sơ đồ chọn đối tượng, KHÔNG có biểu đồ, KHÔNG ghi chú chữ viết tắt; bản soạn tay (C1a) đặt tên
bảng
nghiêng và dựng «Hình 5.1» bằng một cái bảng. K1–K8 không có luật nào đo phần này.

Nguồn dựng (đều là quyết định ĐÃ CHỐT của đề tài, không bịa biến):
  - ma trận mục tiêu – biến `_ma-tran-muc-tieu-bien.csv` (mục tiêu, khái niệm, vai trò, biến, kiểu);
  - bộ biến `_bo-bien-rieng.csv` / từ điển G5 (nhãn, kiểu trường, các mức lựa chọn, đơn vị trong ngoặc của nhãn);
  - biến phái sinh `_bien-phai-sinh.csv` (nhãn, nhãn giá trị);
  - đặc tả phân tích `G6_DAC_TA_SAP.json` (phân tích chính/phụ, nhóm nhỏ, độ nhạy, kiểu kết cục → thước đo hiệu ứng).

CHUẨN TRÌNH BÀY (một chỗ duy nhất; `kiem_bieu_bang` đo đúng các điểm này — luật K9 của đề cương nộp):
  1. Bảng, hình (sơ đồ) và biểu đồ đánh số RIÊNG theo chương: Bảng 5.1…, Hình 5.1…, Biểu đồ 5.1…; số liên tục, không
  trùng.
  2. Tên bảng đặt PHÍA TRÊN bảng; tên hình/biểu đồ đặt PHÍA DƯỚI hình; in đậm, căn giữa (bộ xuất Word căn giữa).
  3. Hàng/cột ghi rõ chỉ số thống kê và đơn vị: biến định lượng TB ± ĐLC (gần chuẩn) hoặc trung vị [KTPV]; biến định
  tính
     n (%) kèm mẫu số khi khác N; tỷ lệ và ước lượng hiệu ứng luôn kèm KTC 95%; p ba chữ số thập phân, «< 0,001».
  4. Ngay dưới mỗi bảng có «Ghi chú» giải thích MỌI chữ viết tắt dùng trong bảng, phép kiểm định/mô hình, mẫu số riêng.
  5. Bảng đặc điểm nền KHÔNG có cột p (CONSORT 2010 E&E PMID 20332511; STROBE E&E PMID 18049195 — tránh kiểm định ý
     nghĩa trong bảng mô tả).
  6. Biểu đồ: tên trục kèm đơn vị, thanh sai số là KTC 95%, chú giải nhóm, không 3D; forest plot có đường không hiệu ứng
     (1 với tỷ số — trục log; 0 với hiệu số).
  7. Sơ đồ chọn đối tượng theo chuẩn báo cáo của thiết kế: CONSORT (RCT), STROBE (quan sát), STARD 2015 (chẩn đoán),
     TRIPOD+AI (dự báo), PRISMA 2020 (tổng quan), COREQ (định tính).
  8. Mỗi mục tiêu nghiên cứu có ít nhất một bảng hoặc biểu đồ trả lời nó.

Lệnh:
  python3 tools/khung_bieu_bang.py --study <mã>                 # in chương 5 dựng được (không ghi gì)
  python3 tools/khung_bieu_bang.py --study <mã> --kiem          # chấm K9 trên đề cương nộp hiện có
  python3 tools/khung_bieu_bang.py --study <mã> --thay-chuong --ghi
        # thay ĐÚNG chương «5. DỰ KIẾN KẾT QUẢ» của đề cương nộp hiện có (giữ nguyên mọi chương khác), vẽ hình vào
        # exports/<mã>/bieu-bang/ và xuất lại Word; sao lưu bản cũ trước khi ghi.
Mã thoát: 0 đạt/xong · 1 còn lỗi K9 · 2 thiếu dữ kiện (ma trận/đề cương) · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

THU_MUC_HINH = "bieu-bang"  # gạch nối, KHÔNG gạch dưới — K4 bắt «a_b» trong văn xuôi là tên biến
X = "…"  # ô số liệu trống của bảng dự kiến (chữ X ngắn để bảng khung đọc gọn trong mã)

CHU_VIET_TAT = {
    "TB": "trung bình", "ĐLC": "độ lệch chuẩn", "KTPV": "khoảng tứ phân vị", "KTC": "khoảng tin cậy",
    "OR": "tỷ số chênh", "PR": "tỷ số tỷ lệ hiện mắc", "RR": "nguy cơ tương đối", "HR": "tỷ số nguy cơ tức thời",
    "AUC": "diện tích dưới đường cong ROC", "ROC": "đường cong đặc trưng hoạt động của bộ thu nhận",
    "PPV": "giá trị dự báo dương", "NPV": "giá trị dự báo âm", "LR+": "tỷ số khả dĩ dương", "LR−": "tỷ số khả dĩ âm",
    "GRADE": "hệ thống phân hạng mức chắc chắn của bằng chứng", "ICC": "hệ số tương quan nội cụm",
    "RD": "hiệu số nguy cơ", "MD": "hiệu số trung bình", "SMD": "hiệu số trung bình chuẩn hoá",
}

# Kiểu kết cục của đặc tả phân tích → (tên thước đo, viết tắt, giá trị không hiệu ứng)
THUOC_DO = {
    "binary": ("tỷ số chênh", "OR", 1.0), "logistic": ("tỷ số chênh", "OR", 1.0),
    "ordinal": ("tỷ số chênh chung", "OR", 1.0), "poisson_pr": ("tỷ số tỷ lệ hiện mắc", "PR", 1.0),
    "poisson": ("tỷ số tỷ lệ", "RR", 1.0), "log_binomial": ("nguy cơ tương đối", "RR", 1.0),
    "cox": ("tỷ số nguy cơ tức thời", "HR", 1.0), "survival": ("tỷ số nguy cơ tức thời", "HR", 1.0),
    "linear": ("hiệu số trung bình", "MD", 0.0), "continuous": ("hiệu số trung bình", "MD", 0.0),
}
TEN_CHUAN = {"rct": "CONSORT", "cross_sectional": "STROBE", "cohort": "STROBE", "case_control": "STROBE",
             "diagnostic": "STARD 2015", "prediction": "TRIPOD+AI", "sr_ma": "PRISMA 2020", "qualitative": "COREQ"}


@dataclass
class Bien:
    ten: str
    nhan: str
    kieu: str  # nhi_phan · danh_dinh · thu_tu · lien_tuc · dem · ngay · thoi_gian_den_su_kien · nhieu_lc · van_ban
    muc: List[Tuple[str, str]] = field(default_factory=list)
    don_vi: str = ""


@dataclass
class Khung:
    loai: str  # bang · hinh · bieu_do
    ten: str
    cot: List[str] = field(default_factory=list)
    dong: List[List[str]] = field(default_factory=list)
    ghi_chu: List[str] = field(default_factory=list)
    dac_ta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Muc:
    tieu_de: str
    khung: List[Khung] = field(default_factory=list)
    muc_tieu: Optional[int] = None


@dataclass
class NguCanh:
    thiet_ke: str
    muc_tieu: List[str]
    bien: Dict[str, Bien]
    ma_tran: List[Dict[str, str]]
    phan_tich: List[Dict[str, Any]]
    n: Optional[int] = None


# ─────────────────────────────── nạp dữ kiện ───────────────────────────────
def _doc_csv(p: Path) -> List[Dict[str, str]]:
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            return [dict(r) for r in csv.DictReader(f)]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def _bo_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(s or ""))).strip()


def _tach_don_vi(nhan: str) -> Tuple[str, str]:
    m = re.match(r"^(.*?)\s*\(([^()]{1,25})\)\s*$", nhan)
    if m and re.search(r"[a-zA-Zµ%/²³]|năm|tháng|ngày|phút|giờ|lần|đồng", m.group(2)):
        return m.group(1).strip(), m.group(2).strip()
    return nhan, ""


def _muc_lua_chon(chuoi: str) -> List[Tuple[str, str]]:
    ra = []
    for phan in str(chuoi or "").split("|"):
        if "," in phan:
            ma, nhan = phan.split(",", 1)
            ra.append((ma.strip(), _bo_html(nhan)))
    return ra


_MA_KHOANG = re.compile(r"\b((?:G\d[ab]?)|(?:A\d))\s+([≥<>≤]?\s*[\d.,]+(?:\s*[–-]\s*[\d.,]+)?)")


def _nhan_muc_kem_khoang(muc: List[Tuple[str, str]], dinh_nghia: str, nhan_bien: str) -> List[Tuple[str, str]]:
    """Mức mã hoá kiểu KDIGO («G4», «A2») ⇒ kèm khoảng giá trị từ định nghĩa của biến phái sinh: «G4 (eGFR 15–29)».
    Người đọc hiểu ngay, và mã giai đoạn không bị đọc nhầm thành ký hiệu nội bộ."""
    khoang = {m.group(1): re.sub(r"\s+", " ", m.group(2)).strip() for m in _MA_KHOANG.finditer(dinh_nghia)}
    if not khoang:
        return muc
    chi_so = "eGFR" if re.search(r"eGFR", nhan_bien, re.I) else ("UACR" if re.search(r"albumin", nhan_bien, re.I)
                                                                  else "")
    ra = []
    for ma, nh in muc:
        k = khoang.get(nh.strip())
        ra.append((ma, f"{nh} ({chi_so} {k})".replace("( ", "(") if k else nh))
    return ra


def _lam_sach_mo_ta(ngu: "NguCanh", s: str) -> str:
    """Mô tả phân tích trong đặc tả (viết cho máy) ⇒ câu cho người đọc: tên biến → nhãn, «= 1 (nội tiết)» → «: nội
    tiết», bỏ mã còn lại («= 2»)."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    s = re.sub(r"\s*=\s*\d+\s*\(([^()]+)\)", r": \1", s)
    s = re.sub(r"\(\s*[a-z][a-z0-9]*_[a-z0-9_]+\s*=\s*\d+\s*\)", "", s)

    def _nhan(m: "re.Match") -> str:
        b = ngu.bien.get(m.group(0))
        return b.nhan.lower() if b else m.group(0).replace("_", " ")

    s = re.sub(r"(?<![\w./-])[a-z][a-z0-9]*_[a-z0-9_]+\b", _nhan, s)
    s = re.sub(r"\s*=\s*\d+\b", "", s)
    return _hoa_dau(re.sub(r"\s+", " ", s).strip(" —-"))


TEN_MO_HINH = {"ordinal": "hồi quy logistic thứ tự", "binary": "hồi quy logistic", "logistic": "hồi quy logistic",
               "poisson_pr": "hồi quy Poisson với sai số chuẩn vững", "poisson": "hồi quy Poisson",
               "log_binomial": "hồi quy log-nhị thức", "cox": "mô hình hồi quy Cox", "survival": "mô hình hồi quy Cox",
               "linear": "hồi quy tuyến tính", "continuous": "hồi quy tuyến tính"}


def _kieu_tu_truong(r: Dict[str, str]) -> str:
    ft = (r.get("Field Type") or "").strip().lower()
    vt = (r.get("Text Validation Type OR Show Slider Number") or "").strip().lower()
    if ft in ("yesno", "truefalse"):
        return "nhi_phan"
    if ft in ("radio", "dropdown"):
        return "nhi_phan" if len(_muc_lua_chon(r.get("Choices, Calculations, OR Slider Labels"))) == 2 else "danh_dinh"
    if ft == "checkbox":
        return "nhieu_lc"
    if ft == "calc" or vt in ("integer", "number") or vt.startswith("number"):
        return "lien_tuc"
    if vt.startswith("date"):
        return "ngay"
    return "van_ban"


def nap_ngu_canh(out_dir: Path, study: str, thiet_ke: str = "", muc_tieu: Optional[Sequence[str]] = None,
                 tu_dien: Optional[List[Dict[str, str]]] = None,
                 ma_tran: Optional[List[Dict[str, str]]] = None) -> NguCanh:
    """Gom dữ kiện đã chốt (chỉ đọc). Nơi gọi đã có sẵn thì truyền vào để khỏi đọc lại."""
    out_dir = Path(out_dir)
    meta = _doc_json(out_dir / "study_meta.json")
    g1 = ((meta.get("gate_params") or {}).get("G1") or {})
    tk = (thiet_ke or str(g1.get("design") or meta.get("design_code") or "")).strip()
    if muc_tieu is None:
        mt = g1.get("objectives") or []
        muc_tieu = [str(x) for x in (mt if isinstance(mt, list) else [mt]) if str(x).strip()]
    if tu_dien is None:
        tep = out_dir / f"G5_REDCap_dictionary_{study}.csv"
        tu_dien = _doc_csv(tep) if tep.is_file() else _doc_csv(out_dir / "_bo-bien-rieng.csv")
    if ma_tran is None:
        ma_tran = _doc_csv(out_dir / "_ma-tran-muc-tieu-bien.csv")
    bien: Dict[str, Bien] = {}
    for r in tu_dien or []:
        ten = (r.get("Variable / Field Name") or "").strip()
        if not ten:
            continue
        nhan, dv = _tach_don_vi(_bo_html(r.get("Field Label")))
        kieu = _kieu_tu_truong(r)
        muc = _muc_lua_chon(r.get("Choices, Calculations, OR Slider Labels")) if kieu != "lien_tuc" else []
        if (r.get("Field Type") or "").lower() == "yesno":
            muc = [("1", "Có"), ("0", "Không")]
        bien[ten] = Bien(ten, nhan, kieu, muc, dv)
    for r in _doc_csv(out_dir / "_bien-phai-sinh.csv"):
        ten = (r.get("ten_bien") or "").strip()
        if not ten:
            continue
        nhan, dv = _tach_don_vi(_bo_html(r.get("nhan")))
        muc = _nhan_muc_kem_khoang(_muc_lua_chon(r.get("nhan_gia_tri")), r.get("dinh_nghia") or "", nhan)
        cu = bien.get(ten)
        bien[ten] = Bien(ten, nhan or (cu.nhan if cu else ten), cu.kieu if cu else "lien_tuc", muc or
                         (cu.muc if cu else []), dv or (cu.don_vi if cu else ""))
    for r in ma_tran or []:  # kiểu trong ma trận là quyết định của nhóm nghiên cứu — thắng kiểu suy từ trường
        ten, kieu = (r.get("bien") or "").strip(), (r.get("kieu") or "").strip()
        if ten and ten in bien and kieu:
            bien[ten].kieu = kieu
        elif ten and ten not in bien:
            nhan, dv = _tach_don_vi(_hoa_dau(r.get("khai_niem") or ten))
            bien[ten] = Bien(ten, nhan, kieu or "lien_tuc", [], dv)
    dac = _doc_json(out_dir / "G6_DAC_TA_SAP.json")
    g3 = _doc_json(out_dir / "G3_checkpoint.json")
    n = g3.get("confirmed_n") if g3.get("confirmed_n") not in (None, "") else g3.get("n_adjusted")
    try:
        n = int(n) if n is not None else None
    except (TypeError, ValueError):
        n = None
    return NguCanh(tk, list(muc_tieu or []), bien, list(ma_tran or []), list(dac.get("phan_tich") or []), n)


# ─────────────────────────────── tiện ích chữ ───────────────────────────────
def _hoa_dau(s: str) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:1].upper() + s[1:] if s else s


def _thuong_dau(s: str) -> str:
    """Hạ chữ cái đầu khi nó không mở đầu một viết tắt («Việc không…» → «việc không…»; «UACR…» giữ nguyên)."""
    s = str(s or "")
    dau = s.split(" ", 1)[0]
    return s[:1].lower() + s[1:] if len(dau) > 1 and dau.isalpha() and dau[1:].islower() else s


def _bo_ngoac_noi_bo(s: str) -> str:
    return re.sub(r"\s*\([^()]*(?:\bMT\s*\d|biến phụ thuộc|biến độc lập)[^()]*\)", "", str(s or "")).strip()


def _muc_duong(b: "Bien") -> Tuple[str, str]:
    """Mức «dương» của biến nhị phân để trình bày một hàng n (%): «Có/Đúng» nếu có, rồi mã 1, rồi mức đầu."""
    for m in b.muc:
        if m[1].strip().lower() in ("có", "đúng", "yes"):
            return m
    for m in b.muc:
        if m[0].strip() == "1":
            return m
    return b.muc[0] if b.muc else ("1", "Có")


def _muc_theo_tham_chieu(b: "Bien") -> List[Tuple[str, str]]:
    """Các mức theo thứ tự trình bày, mức ĐẦU là nhóm tham chiếu: biến có/không lấy «Không» làm tham chiếu; biến khác
    giữ thứ tự mã trong bộ biến (mã nhỏ nhất làm tham chiếu)."""
    khong = [m for m in b.muc if m[1].strip().lower() in ("không", "sai", "no")]
    return khong + [m for m in b.muc if m not in khong] if khong else list(b.muc)


def _ten_muc_tieu(s: str) -> str:
    s = re.sub(r"^\s*(?:MT|Mục tiêu)\s*\d+\s*(?:\([^)]*\))?\s*[:.–-]\s*", "", str(s or "")).strip()
    return s.rstrip(". ")


def _so(n: Optional[int]) -> str:
    return f"{n:,}".replace(",", ".") if isinstance(n, int) else X


def _nhan_bien(nc: NguCanh, ten: str, khai_niem: str = "") -> str:
    b = nc.bien.get(ten)
    nhan = _hoa_dau(_bo_ngoac_noi_bo(khai_niem)) if khai_niem else (b.nhan if b else ten)
    nhan = re.sub(r"\s*\([^()]*\)\s*$", "", nhan) if b and b.don_vi and nhan.endswith(")") else nhan
    nhan = nhan.replace("_", " ")
    return f"{nhan} ({b.don_vi})" if b and b.don_vi and f"({b.don_vi})" not in nhan else nhan


def _khai_niem(ngu: NguCanh, ten: str) -> str:
    for r in ngu.ma_tran:
        if (r.get("bien") or "").strip() == ten and (r.get("khai_niem") or "").strip():
            return r["khai_niem"].strip()
    return ""


def _dong_ma_tran(nc: NguCanh, muc_tieu: Optional[int] = None, vai: Iterable[str] = ()) -> List[Dict[str, str]]:
    vai = set(vai)
    ra, da = [], set()
    for r in nc.ma_tran:
        if muc_tieu is not None and str(r.get("muc_tieu") or "").strip() != str(muc_tieu):
            continue
        if vai and (r.get("vai_tro") or "").strip() not in vai:
            continue
        b = (r.get("bien") or "").strip()
        if b and b not in da:
            da.add(b)
            ra.append(r)
    return ra


def _dong_mo_ta(nc: NguCanh, ten: str, khai_niem: str, so_cot: int, chi_so: bool = True) -> List[List[str]]:
    """Hàng của một biến trong bảng mô tả: định lượng một hàng «TB ± ĐLC»; nhị phân một hàng «n (%)»; định danh/thứ tự
    một hàng tiêu đề + mỗi mức một hàng (đúng các mức trong bộ biến — không bịa mức)."""
    b = nc.bien.get(ten) or Bien(ten, ten, "lien_tuc")
    nhan = _nhan_bien(nc, ten, khai_niem)
    kieu = b.kieu
    if kieu in ("lien_tuc", "dem"):
        return [[f"{nhan}, TB ± ĐLC hoặc trung vị [KTPV]" if chi_so else nhan] + [f"{X} ± {X}"] * so_cot]
    if kieu == "nhi_phan":
        muc = _muc_duong(b)[1] if b.muc else "Có"
        mo_ta = nhan if muc in ("Có", "Đúng") else f"{nhan}: {_thuong_dau(muc)}"
        return [[f"{mo_ta}, n (%)"] + [f"{X} ({X})"] * so_cot]
    if kieu in ("danh_dinh", "thu_tu", "nhieu_lc") and b.muc:
        dong = [[f"{nhan}, n (%)" + (" ¹" if kieu == "nhieu_lc" else "")] + [""] * so_cot]
        dong += [[f"– {m[1]}"] + [f"{X} ({X})"] * so_cot for m in b.muc]
        return dong
    if kieu in ("danh_dinh", "thu_tu", "nhieu_lc"):
        return [[f"{nhan} (theo từng nhóm), n (%)"] + [f"{X} ({X})"] * so_cot]
    return []


def _ghi_chu(cot: Sequence[str], dong: Sequence[Sequence[str]], them: Sequence[str] = ()) -> List[str]:
    chu = " ".join(cot) + " " + " ".join(" ".join(d) for d in dong)
    vt = [f"{k}: {v}" for k, v in CHU_VIET_TAT.items() if re.search(rf"(?<![\wÀ-ỹ]){re.escape(k)}(?![\wÀ-ỹ])", chu)]
    ra = []
    if vt:
        ra.append("Chữ viết tắt — " + "; ".join(vt) + ".")
    if "¹" in chu:
        ra.append("¹ Câu hỏi nhiều lựa chọn: một người có thể chọn nhiều mức, tổng tỷ lệ có thể vượt 100%.")
    ra.extend(them)
    return ra


# ─────────────────────────────── nhóm so sánh ───────────────────────────────
def _phan_tich_chinh(nc: NguCanh) -> Dict[str, Any]:
    for p in nc.phan_tich:
        if p.get("vai") == "chinh" and not p.get("chua_tu_dong"):
            return p
    return {}


def _bien_nhom(nc: NguCanh) -> Optional[str]:
    ts = _phan_tich_chinh(nc).get("tham_so") or {}
    g = ts.get("group")
    if g and nc.thiet_ke in ("rct", "cohort", "case_control"):
        return str(g)
    if nc.thiet_ke in ("rct", "cohort"):
        pn = _dong_ma_tran(nc, vai=("phoi_nhiem",))
        return (pn[0].get("bien") or "").strip() if pn else None
    if nc.thiet_ke == "case_control":
        kc = _dong_ma_tran(nc, vai=("ket_cuc_chinh",))
        return (kc[0].get("bien") or "").strip() if kc else None
    return None


def _cot_nhom(nc: NguCanh, ten: Optional[str], mac_dinh: Tuple[str, str]) -> List[str]:
    b = nc.bien.get(ten) if ten else None
    muc = [m[1] for m in (b.muc if b else [])][:4]
    if len(muc) >= 2:
        return [f"{_hoa_dau(m)} (n = {X})" for m in muc]
    return [f"{m} (n = {X})" for m in mac_dinh]


# ─────────────────────────────── sơ đồ chọn đối tượng ───────────────────────────────
def _so_do(nc: NguCanh) -> Khung:
    tk = nc.thiet_ke
    n = f"(n = {X})"
    if tk == "rct":
        nhom = [c.split(" (n =")[0] for c in _cot_nhom(nc, _bien_nhom(nc), ("Nhóm can thiệp", "Nhóm chứng"))]
        buoc = [("Đánh giá tính đủ điều kiện " + n,
                 f"Bị loại {n}\n– Không đủ tiêu chuẩn {n}\n– Từ chối tham gia {n}\n– Lý do khác {n}"),
                ("Ngẫu nhiên hoá " + n, None)]
        tach = [[f"Phân bổ vào nhóm {g} {n}\n– Nhận can thiệp như phân bổ {n}\n– Không nhận {n}",
                 f"Theo dõi\n– Mất dấu {n}\n– Ngừng can thiệp {n}",
                 f"Phân tích {n}\n– Loại khỏi phân tích {n}"] for g in nhom[:2]]
        ten = "Sơ đồ tuyển chọn, phân bổ, theo dõi và phân tích người tham gia (theo CONSORT)"
    elif tk == "diagnostic":
        buoc = [("Người bệnh đủ điều kiện " + n, f"Bị loại {n}"), ("Làm xét nghiệm chỉ điểm " + n, None)]
        tach = [[f"Kết quả dương tính {n}", f"Có tiêu chuẩn tham chiếu {n}", f"Có bệnh {n} · Không bệnh {n}"],
                [f"Kết quả âm tính {n}", f"Có tiêu chuẩn tham chiếu {n}", f"Có bệnh {n} · Không bệnh {n}"],
                [f"Không xác định {n}", f"Có tiêu chuẩn tham chiếu {n}", f"Có bệnh {n} · Không bệnh {n}"]]
        ten = "Sơ đồ người tham gia theo kết quả xét nghiệm chỉ điểm và tiêu chuẩn tham chiếu (theo STARD 2015)"
    elif tk == "sr_ma":
        buoc = [(f"Bản ghi từ cơ sở dữ liệu {n}\nBản ghi từ sổ đăng ký {n}",
                 f"Loại trước sàng lọc\n– Trùng lặp {n}\n– Lý do khác {n}"),
                (f"Bản ghi được sàng lọc {n}", f"Bị loại theo tiêu đề, tóm tắt {n}"),
                (f"Báo cáo cần tìm toàn văn {n}", f"Không lấy được toàn văn {n}"),
                (f"Báo cáo được đánh giá đủ điều kiện {n}", f"Bị loại theo từng lý do {n}"),
                (f"Nghiên cứu đưa vào tổng quan {n}\nNghiên cứu đưa vào phân tích gộp {n}", None)]
        tach = []
        ten = "Sơ đồ tìm kiếm và lựa chọn nghiên cứu (theo PRISMA 2020)"
    elif tk == "qualitative":
        buoc = [(f"Người được tiếp cận theo chọn mẫu có chủ đích {n}", f"Từ chối hoặc không liên lạc được {n}"),
                (f"Tham gia phỏng vấn {n}", f"Rút khỏi nghiên cứu {n}"),
                (f"Đưa vào phân tích đến khi bão hoà dữ liệu {n}", None)]
        tach = []
        ten = "Sơ đồ tiếp cận và tham gia của người tham gia nghiên cứu (theo COREQ)"
    elif tk == "prediction":
        buoc = [(f"Người bệnh trong nguồn dữ liệu {n}", f"Bị loại theo tiêu chuẩn {n}"),
                (f"Đưa vào phát triển mô hình {n}\nSố người có biến cố {n}", f"Thiếu dữ liệu yếu tố dự báo {n}"),
                (f"Kiểm định nội bộ bằng lấy mẫu lặp {n}", None)]
        tach = []
        ten = "Sơ đồ chọn người bệnh cho phát triển và kiểm định mô hình (theo TRIPOD+AI)"
    else:  # cross_sectional · cohort · case_control
        buoc = [(f"Đối tượng trong khung chọn mẫu {n}", f"Không đủ tiêu chuẩn chọn hoặc thuộc tiêu chuẩn loại trừ {n}"),
                (f"Đối tượng đủ điều kiện được mời tham gia {n}", f"Từ chối tham gia {n}"),
                (f"Tham gia nghiên cứu {n}", f"Thiếu dữ liệu kết cục chính {n}")]
        if tk in ("cohort", "case_control"):
            nhom = [c.split(" (n =")[0] for c in _cot_nhom(nc, _bien_nhom(nc), (
                ("Nhóm phơi nhiễm", "Nhóm không phơi nhiễm") if tk == "cohort" else ("Nhóm bệnh", "Nhóm chứng")))]
            tach = [[f"{g} {n}", (f"Mất theo dõi {n}" if tk == "cohort" else f"Thiếu dữ liệu phơi nhiễm {n}"),
                     f"Đưa vào phân tích {n}"] for g in nhom[:2]]
        else:
            buoc.append((f"Đưa vào phân tích {n}", None))
            tach = []
        ten = "Sơ đồ chọn đối tượng nghiên cứu (theo STROBE)"
    return Khung("hinh", ten, dac_ta={"kieu": "so_do", "buoc": buoc, "tach": tach},
                 ghi_chu=["Số lượng ở từng bước và lý do loại được ghi đầy đủ khi kết thúc thu thập số liệu."])


# ─────────────────────────────── bảng đặc điểm ───────────────────────────────
_BO_KHOI_NEN = ("ket_cuc_chinh", "ket_cuc_phu", "phoi_nhiem", "cum", "trong_so", "su_kien", "thoi_gian")


def _bien_nen(nc: NguCanh) -> List[Tuple[str, str]]:
    """Biến của bảng đặc điểm: hiệp biến + biến phân tầng của ma trận; chỉ khi có dưới 4 biến mới thêm các «yếu tố»
    (yếu tố đã có bảng liên quan riêng — không lặp hai bảng dài)."""
    def _chon(vai: Sequence[str]) -> List[Tuple[str, str]]:
        ra, da = [], set()
        for r in nc.ma_tran:
            v, b = (r.get("vai_tro") or "").strip(), (r.get("bien") or "").strip()
            k = (r.get("kieu") or (nc.bien.get(b).kieu if b in nc.bien else "")).strip()
            if b and b not in da and v in vai and k not in ("van_ban", "ngay"):
                da.add(b)
                ra.append((b, r.get("khai_niem") or ""))
        return ra
    ra = _chon(("hiep_bien", "phan_tang"))
    return (ra if len(ra) >= 4 else _chon(("hiep_bien", "phan_tang", "yeu_to")))[:30]


def _bang_dac_diem(nc: NguCanh) -> Khung:
    tk = nc.thiet_ke
    if tk == "sr_ma":
        cot = ["Nghiên cứu (tác giả, năm)", "Quốc gia", "Thiết kế", "Cỡ mẫu", "Quần thể", "Can thiệp / so sánh",
               "Kết cục", "Thời gian theo dõi", "Nguy cơ sai lệch"]
        return Khung("bang", "Đặc điểm các nghiên cứu được đưa vào tổng quan", cot,
                     [[f"Nghiên cứu {i}"] + [X] * (len(cot) - 1) for i in (1, 2, 3)],
                     ["Mỗi nghiên cứu một hàng; nguy cơ sai lệch theo công cụ đã nêu ở mục phương pháp."])
    nhom_ten = _bien_nhom(nc)
    if tk == "rct":
        nhom = _cot_nhom(nc, nhom_ten, ("Nhóm can thiệp", "Nhóm chứng")) + [f"Chung (n = {X})"]
        ten = "Đặc điểm nền của người tham gia theo nhóm phân bổ"
        them = ["Không kiểm định ý nghĩa khác biệt đặc điểm nền giữa các nhóm đã ngẫu nhiên hoá."]
    elif tk in ("cohort", "case_control"):
        nhom = _cot_nhom(nc, nhom_ten, ("Nhóm phơi nhiễm", "Nhóm không phơi nhiễm") if tk == "cohort"
                         else ("Nhóm bệnh", "Nhóm chứng"))
        ten = ("Đặc điểm của đối tượng nghiên cứu theo tình trạng phơi nhiễm" if tk == "cohort"
               else "Đặc điểm của nhóm bệnh và nhóm chứng")
        them = ["Bảng mô tả không kèm giá trị p; khác biệt giữa các nhóm được xử lý bằng hiệu chỉnh trong mô hình."]
    elif tk == "prediction":
        nhom = [f"Toàn mẫu (N = {X})", f"Có biến cố (n = {X})", f"Không có biến cố (n = {X})", "Số thiếu, n (%)"]
        ten = "Đặc điểm người bệnh và các yếu tố dự báo trong mẫu phát triển mô hình"
        them = ["Số thiếu của từng yếu tố dự báo được báo cáo trước khi gán giá trị thiếu."]
    elif tk == "qualitative":
        nhom = [f"Số người tham gia (n = {X})"]
        ten = "Đặc điểm của người tham gia nghiên cứu"
        them = ["Không trình bày thông tin có thể nhận diện người tham gia."]
    elif tk == "diagnostic":
        nhom = [f"Toàn mẫu (N = {X})", f"Tiêu chuẩn tham chiếu dương tính (n = {X})",
                f"Tiêu chuẩn tham chiếu âm tính (n = {X})"]
        ten = "Đặc điểm của người tham gia theo kết quả tiêu chuẩn tham chiếu"
        them = []
    else:
        nhom = [f"Toàn mẫu (N = {_so(nc.n) if nc.n else X})", "Số thiếu, n (%)"]
        ten = "Đặc điểm chung của đối tượng nghiên cứu"
        them = []
    so_cot = len(nhom)
    dong: List[List[str]] = []
    for ten_b, kn in _bien_nen(nc):
        hang = _dong_mo_ta(nc, ten_b, kn, so_cot)
        for j, d in enumerate(hang):
            if nhom[-1].startswith("Số thiếu"):
                d[-1] = f"{X} ({X})" if j == 0 else ""
            dong.append(d)
    if not dong:
        dong = [["Tuổi (năm), TB ± ĐLC hoặc trung vị [KTPV]"] + [f"{X} ± {X}"] * so_cot,
                ["Giới nữ, n (%)"] + [f"{X} ({X})"] * so_cot]
    cot = ["Đặc điểm"] + nhom
    return Khung("bang", ten, cot, dong, _ghi_chu(cot, dong, ["Biến định lượng trình bày TB ± ĐLC khi phân phối gần "
                                                               "chuẩn, ngược lại trung vị [KTPV]."] + them))


# ─────────────────────────────── theo mục tiêu ───────────────────────────────
def _phan_tich_cua(nc: NguCanh, k: int, bien_kq: Sequence[str]) -> List[Dict[str, Any]]:
    ra = []
    for p in nc.phan_tich:
        ma = str(p.get("id") or "")
        ts = p.get("tham_so") or {}
        if re.match(rf"^MT{k}(?:_|$)", ma) or (ts.get("outcome") and ts.get("outcome") in bien_kq):
            ra.append(p)
    return ra


def _thuoc_do(p: Dict[str, Any], tk: str) -> Tuple[str, str, float]:
    ts = p.get("tham_so") or {}
    loai = str(ts.get("outcome_type") or ts.get("loai_dac_thu") or "").lower()
    if loai in THUOC_DO:
        return THUOC_DO[loai]
    if tk == "case_control":
        return THUOC_DO["binary"]
    if tk == "cross_sectional":
        return THUOC_DO["poisson_pr"]
    if tk == "rct":
        return ("nguy cơ tương đối", "RR", 1.0)
    return ("tỷ số chênh", "OR", 1.0)


def _la_phan_tich_lien_quan(muc_tieu: str, dong_mt: List[Dict[str, str]]) -> bool:
    vai = {(r.get("vai_tro") or "").strip() for r in dong_mt}
    return bool(re.search(r"phân\s+tích|yếu\s+tố|liên\s+quan|so\s+sánh|ảnh\s+hưởng|hiệu\s+quả", muc_tieu, re.I)) \
        or bool(vai & {"yeu_to", "phoi_nhiem"}) and bool(vai & {"ket_cuc_chinh", "ket_cuc_phu"})


def _khung_mo_ta_kq(nc: NguCanh, k: int, ten_mt: str, kq: List[Dict[str, str]]) -> List[Khung]:
    """Mục tiêu mô tả (ước lượng tỷ lệ/điểm): bảng ước lượng + KTC 95% và biểu đồ cột kèm KTC 95%."""
    cot = ["Chỉ số", "n/N", "Tỷ lệ % hoặc TB ± ĐLC", "Trung vị [KTPV]", "KTC 95%"]
    dong = []
    for r in kq:
        b = nc.bien.get(r["bien"].strip())
        nhan = _nhan_bien(nc, r["bien"].strip(), r.get("khai_niem") or "")
        if b and b.kieu in ("danh_dinh", "thu_tu") and b.muc:
            dong.append([f"{nhan}, phân bố các mức", "", "", "", ""])
            dong += [[f"– {m[1]}", f"{X}/{X}", X, "—", f"{X} – {X}"] for m in b.muc]
        elif b and b.kieu in ("lien_tuc", "dem"):
            dong.append([nhan, f"{X}", f"{X} ± {X}", f"{X} [{X} – {X}]", f"{X} – {X}"])
        else:
            dong.append([nhan, f"{X}/{X}", X, "—", f"{X} – {X}"])
    chinh_kq = _nhan_bien(nc, kq[0]["bien"].strip(), kq[0].get("khai_niem") or "") if kq and kq[0].get("bien") \
        else _hoa_dau(ten_mt)
    ten = f"{chinh_kq}" + (" và các chỉ số mô tả liên quan" if len(kq) > 1 else "") + f" (Mục tiêu {k})"
    ghi = _ghi_chu(cot, dong, ["Tỷ lệ kèm KTC 95% theo phương pháp đã nêu ở mục xử lý số liệu; mẫu số của từng chỉ số "
                               "ghi ở cột n/N."])
    nhi = [r for r in kq if (nc.bien.get(r["bien"].strip()) or Bien("", "", "nhi_phan")).kieu == "nhi_phan"]
    lt = [r for r in kq if (nc.bien.get(r["bien"].strip()) or Bien("", "", "nhi_phan")).kieu in ("lien_tuc", "dem")]
    co_ty_le = len(nhi) >= 2 or (bool(nhi) and len(lt) < 2)
    nhan_bd = [_nhan_bien(nc, r["bien"].strip(), r.get("khai_niem") or "") for r in (nhi if co_ty_le else lt or kq)][:8]
    bd = Khung("bieu_do", ("Tỷ lệ các chỉ số chính" if co_ty_le else "Giá trị trung bình các chỉ số chính")
               + f" kèm khoảng tin cậy 95% (Mục tiêu {k})",
               dac_ta={"kieu": "cot_ktc", "nhan": nhan_bd,
                       "truc_y": "Tỷ lệ (%)" if co_ty_le else "Giá trị trung bình",
                       "truc_x": "", "nguon": "bảng tương ứng"},
               ghi_chu=["Cột là ước lượng điểm; thanh sai số là KTC 95%."])
    return [Khung("bang", ten, cot, dong, ghi), bd]


def _khung_lien_quan(nc: NguCanh, k: int, ten_mt: str, dong_mt: List[Dict[str, str]],
                     pts: List[Dict[str, Any]]) -> List[Khung]:
    """Mục tiêu phân tích (yếu tố liên quan / so sánh): bảng đơn biến + bảng đa biến (thước đo theo mô hình đã định) +
    forest plot của ước lượng hiệu chỉnh."""
    tk = nc.thiet_ke
    chinh = next((p for p in pts if not p.get("chua_tu_dong") and (p.get("tham_so") or {}).get("outcome")), {})
    ten_td, vt, ref = _thuoc_do(chinh, tk)
    ts = chinh.get("tham_so") or {}
    kq = [r for r in dong_mt if (r.get("vai_tro") or "") in ("ket_cuc_chinh", "ket_cuc_phu")]
    kq_ten = ts.get("outcome") or (kq[0]["bien"].strip() if kq else "")
    kq_nhan = _nhan_bien(nc, kq_ten, next((r.get("khai_niem") or "" for r in kq if r["bien"].strip() == kq_ten),
                                          "") or _khai_niem(nc, kq_ten)) if kq_ten else "kết cục"
    kq_bien = nc.bien.get(kq_ten) if kq_ten else None
    kq_nhi_phan = bool(kq_bien and kq_bien.kieu == "nhi_phan")
    yt = [r for r in dong_mt if (r.get("vai_tro") or "") in ("phoi_nhiem", "yeu_to", "hiep_bien", "phan_tang")]
    ten_cov = set(ts.get("covariates") or []) | ({ts.get("group")} if ts.get("group") else set())
    if not yt and ten_cov:
        yt = [{"bien": c, "khai_niem": ""} for c in ten_cov]
    dong_dv, dong_db, nhan_fp = [], [], []
    for r in yt:
        ten_b = r["bien"].strip()
        b = nc.bien.get(ten_b) or Bien(ten_b, ten_b, "lien_tuc")
        nhan = _nhan_bien(nc, ten_b, r.get("khai_niem") or "")
        o_kq = [f"{X} ({X})", f"{X} ({X})"] if kq_nhi_phan else [f"{X} ± {X}"]
        if b.kieu in ("lien_tuc", "dem"):
            dong_dv.append([nhan, "mỗi đơn vị tăng", *([f"{X} ± {X}"] * len(o_kq)), f"{X} ({X} – {X})", X])
            dong_db.append([nhan, "mỗi đơn vị tăng", f"{X} ({X} – {X})", X])
            nhan_fp.append(nhan)
        elif b.muc:
            for i, m in enumerate(_muc_theo_tham_chieu(b)):
                nhom_tc = i == 0
                dong_dv.append([nhan if i == 0 else "", m[1], *o_kq,
                                "1 (nhóm tham chiếu)" if nhom_tc else f"{X} ({X} – {X})", "" if nhom_tc else X])
                if ten_b in ten_cov or not ten_cov:
                    dong_db.append([nhan if i == 0 else "", m[1],
                                    "1 (nhóm tham chiếu)" if nhom_tc else f"{X} ({X} – {X})", "" if nhom_tc else X])
                    if not nhom_tc:
                        nhan_fp.append(f"{nhan}: {_thuong_dau(m[1])}")
        else:
            dong_dv.append([nhan, "theo nhóm", *o_kq, f"{X} ({X} – {X})", X])
            dong_db.append([nhan, "theo nhóm", f"{X} ({X} – {X})", X])
            nhan_fp.append(nhan)
    if not dong_dv:
        dong_dv = [["Yếu tố trong mô hình", "theo nhóm", *([f"{X} ({X})"] * (2 if kq_nhi_phan else 1)),
                    f"{X} ({X} – {X})", X]]
    if not dong_db:
        dong_db = [["Yếu tố trong mô hình", "theo nhóm", f"{X} ({X} – {X})", X]]
    cot_kq = ["Có kết cục: n (%)", "Không có kết cục: n (%)"] if kq_nhi_phan else ["Kết cục: TB ± ĐLC"]
    cot_dv = ["Yếu tố", "Nhóm / đơn vị", *cot_kq, f"{vt} thô (KTC 95%)", "p"]
    cot_db = ["Yếu tố", "Nhóm / đơn vị", f"{vt} hiệu chỉnh (KTC 95%)", "p"]
    ghi_dv = _ghi_chu(cot_dv, dong_dv, [f"{vt} thô ước lượng bằng mô hình một biến cùng loại với mô hình chính; "
                                        "p ghi ba "
                                        "chữ số thập phân, «< 0,001» khi nhỏ hơn."])
    mo_hinh = TEN_MO_HINH.get(str(ts.get("outcome_type") or "").lower(), "")
    ghi_db = _ghi_chu(cot_db, dong_db, [f"{vt} ({ten_td}) hiệu chỉnh đồng thời cho mọi biến trong bảng"
                                        + (f"; mô hình {mo_hinh}" if mo_hinh else "") + "."])
    nhan_fp = nhan_fp[:16]
    kq_thuong = _thuong_dau(kq_nhan)
    kh = [Khung("bang", f"Phân tích đơn biến các yếu tố liên quan đến {kq_thuong} (Mục tiêu {k})", cot_dv,
                dong_dv, ghi_dv),
          Khung("bang", f"Mô hình đa biến các yếu tố liên quan đến {kq_thuong} (Mục tiêu {k})", cot_db,
                dong_db, ghi_db),
          Khung("bieu_do", f"{vt} hiệu chỉnh và KTC 95% của các yếu tố liên quan đến {kq_thuong} "
                f"(Mục tiêu {k})",
                dac_ta={"kieu": "forest", "nhan": nhan_fp, "ref": ref, "truc_x": f"{vt} hiệu chỉnh (KTC 95%)",
                        "log": ref == 1.0},
                ghi_chu=[f"Điểm là {vt} hiệu chỉnh, đoạn ngang là KTC 95%; đường dọc tại {str(ref).replace('.', ',')} "
                         "là không có liên quan" + ("; trục hoành theo thang log." if ref == 1.0 else "."),
                         "Chữ viết tắt — " + f"{vt}: {CHU_VIET_TAT.get(vt, ten_td)}; KTC: khoảng tin cậy."])]
    return kh


def _khung_rct(nc: NguCanh, k: int, ten_mt: str, dong_mt: List[Dict[str, str]],
               pts: List[Dict[str, Any]]) -> List[Khung]:
    nhom = _cot_nhom(nc, _bien_nhom(nc), ("Nhóm can thiệp", "Nhóm chứng"))[:2]
    chinh = next((p for p in pts if not p.get("chua_tu_dong") and (p.get("tham_so") or {}).get("outcome")), {})
    ten_td, vt, ref = _thuoc_do(chinh, "rct")
    kq = [r for r in dong_mt if (r.get("vai_tro") or "") in ("ket_cuc_chinh", "ket_cuc_phu")] or \
        _dong_ma_tran(nc, vai=("ket_cuc_chinh", "ket_cuc_phu"))
    cot = ["Kết cục"] + [c.replace(f"(n = {X})", "").strip() + ": n/N (%) hoặc TB ± ĐLC" for c in nhom] + \
        ["Hiệu số tuyệt đối (KTC 95%)", f"{vt} (KTC 95%)", "p"]
    dong = []
    for r in kq:
        vai = "chính" if (r.get("vai_tro") or "") == "ket_cuc_chinh" else "phụ"
        dong.append([f"{_nhan_bien(nc, r['bien'].strip(), r.get('khai_niem') or '')} (kết cục {vai})",
                     f"{X}/{X} ({X})", f"{X}/{X} ({X})", f"{X} ({X} – {X})", f"{X} ({X} – {X})", X])
    if not dong:
        dong = [["Kết cục chính", f"{X}/{X} ({X})", f"{X}/{X} ({X})", f"{X} ({X} – {X})", f"{X} ({X} – {X})", X]]
    ghi = _ghi_chu(cot, dong, ["Với kết cục nhị phân trình bày cả hiệu số nguy cơ tuyệt đối và hiệu ứng tương đối; "
                               "phân "
                               "tích theo nguyên tắc ý định điều trị."])
    return [Khung("bang", f"{_hoa_dau(ten_mt)} (Mục tiêu {k})", cot, dong, ghi),
            Khung("bieu_do", f"Kết cục chính theo nhóm phân bổ kèm KTC 95% (Mục tiêu {k})",
                  dac_ta={"kieu": "cot_ktc", "nhan": [c.split(" (n =")[0] for c in nhom], "truc_y": "Tỷ lệ (%)",
                          "truc_x": "Nhóm phân bổ"},
                  ghi_chu=["Cột là tỷ lệ kết cục chính của từng nhóm; thanh sai số là KTC 95%."])]


def _khung_chan_doan(nc: NguCanh, k: int, ten_mt: str) -> List[Khung]:
    bang22 = Khung("bang", f"Kết quả xét nghiệm chỉ điểm so với tiêu chuẩn tham chiếu (Mục tiêu {k})",
                   ["Xét nghiệm chỉ điểm", "Tiêu chuẩn tham chiếu dương tính", "Tiêu chuẩn tham chiếu âm tính", "Tổng"],
                   [["Dương tính", X, X, X], ["Âm tính", X, X, X], ["Tổng", X, X, X]],
                   ["Kết quả không xác định của xét nghiệm chỉ điểm được báo cáo riêng và không đưa vào bảng 2 × 2."])
    cot = ["Chỉ số", "Ước lượng", "KTC 95%"]
    dong = [["Độ nhạy (%)", X, f"{X} – {X}"], ["Độ đặc hiệu (%)", X, f"{X} – {X}"], ["PPV (%)", X, f"{X} – {X}"],
            ["NPV (%)", X, f"{X} – {X}"], ["LR+", X, f"{X} – {X}"], ["LR−", X, f"{X} – {X}"], ["AUC", X, f"{X} – {X}"]]
    chinh = Khung("bang", f"{_hoa_dau(ten_mt)} (Mục tiêu {k})", cot, dong,
                  _ghi_chu(cot, dong, ["PPV và NPV phụ thuộc tỷ lệ bệnh trong mẫu; ngưỡng dương tính đã định trước."]))
    roc = Khung("bieu_do", f"Đường cong ROC của xét nghiệm chỉ điểm (Mục tiêu {k})",
                dac_ta={"kieu": "roc"}, ghi_chu=["Đường chéo là phân biệt ngẫu nhiên (AUC 0,5); ghi AUC và KTC 95% "
                                                 "trên biểu đồ.", "Chữ viết tắt — ROC: " + CHU_VIET_TAT["ROC"]
                                                 + "; AUC: " + CHU_VIET_TAT["AUC"] + "."])
    return [bang22, chinh, roc]


def _khung_du_bao(nc: NguCanh, k: int, ten_mt: str, dong_mt: List[Dict[str, str]]) -> List[Khung]:
    yt = [r for r in dong_mt if (r.get("vai_tro") or "") in ("yeu_to", "hiep_bien", "phoi_nhiem")] or \
        _dong_ma_tran(nc, vai=("yeu_to", "hiep_bien"))
    cot_m = ["Yếu tố dự báo", "Hệ số hồi quy (β)", "OR (KTC 95%)"]
    dong_m = [[_nhan_bien(nc, r["bien"].strip(), r.get("khai_niem") or ""), X, f"{X} ({X} – {X})"] for r in yt] or \
        [["Yếu tố dự báo", X, f"{X} ({X} – {X})"]]
    dong_m.append(["Hệ số chặn", X, "—"])
    cot_h = ["Chỉ số hiệu năng", "Mẫu phát triển", "Sau hiệu chỉnh lạc quan (lấy mẫu lặp)"]
    dong_h = [["Thống kê C (AUC)", f"{X} ({X} – {X})", f"{X} ({X} – {X})"], ["Độ dốc hiệu chuẩn", X, X],
              ["Hiệu chuẩn tổng thể (hệ số chặn)", X, X], ["Điểm Brier", X, X]]
    return [Khung("bang", f"Các yếu tố dự báo trong mô hình cuối cùng (Mục tiêu {k})", cot_m, dong_m,
                  _ghi_chu(cot_m, dong_m, ["Trình bày đầy đủ phương trình mô hình (mọi hệ số và hệ số chặn)."])),
            Khung("bang", f"Hiệu năng phân biệt và hiệu chuẩn của mô hình (Mục tiêu {k})", cot_h, dong_h,
                  _ghi_chu(cot_h, dong_h, ["Hiệu chỉnh lạc quan bằng lấy mẫu lặp 500 lần trở lên."])),
            Khung("bieu_do", f"Biểu đồ hiệu chuẩn: nguy cơ dự báo so với nguy cơ quan sát (Mục tiêu {k})",
                  dac_ta={"kieu": "hieu_chuan"},
                  ghi_chu=["Đường chéo là hiệu chuẩn hoàn hảo; điểm là nhóm thập phân vị nguy cơ dự báo kèm KTC 95%."]),
            Khung("bieu_do", f"Đường cong ROC của mô hình dự báo (Mục tiêu {k})", dac_ta={"kieu": "roc"},
                  ghi_chu=["Chữ viết tắt — ROC: " + CHU_VIET_TAT["ROC"] + "; AUC: " + CHU_VIET_TAT["AUC"] + "."])]


def _khung_gop(nc: NguCanh, k: int, ten_mt: str) -> List[Khung]:
    cot_s = ["Kết cục", "Số nghiên cứu (số người)", "Hiệu ứng tương đối (KTC 95%)", "Hiệu ứng tuyệt đối (KTC 95%)",
             "I² (%)", "Mức chắc chắn GRADE"]
    dong_s = [[f"{_hoa_dau(ten_mt)}", f"{X} ({X})", f"RR {X} ({X} – {X})", f"{X} trên 1.000 ({X} – {X})", X, X]]
    cot_r = ["Nghiên cứu", "Quá trình ngẫu nhiên hoá", "Sai lệch so với can thiệp dự kiến", "Dữ liệu kết cục bị thiếu",
             "Đo lường kết cục", "Lựa chọn kết quả báo cáo", "Tổng thể"]
    dong_r = [[f"Nghiên cứu {i}"] + [X] * 6 for i in (1, 2, 3)]
    return [Khung("bang", f"Tóm tắt kết quả và mức chắc chắn của bằng chứng (Mục tiêu {k})", cot_s, dong_s,
                  _ghi_chu(cot_s, dong_s, ["Mức chắc chắn: cao, trung bình, thấp, rất thấp; lý do hạ bậc ghi kèm."])),
            Khung("bang", f"Đánh giá nguy cơ sai lệch của từng nghiên cứu theo RoB 2 (Mục tiêu {k})", cot_r, dong_r,
                  ["Mỗi miền: nguy cơ thấp, có một số lo ngại, nguy cơ cao."]),
            Khung("bieu_do", f"Forest plot hiệu ứng gộp (Mục tiêu {k})",
                  dac_ta={"kieu": "forest", "nhan": ["Nghiên cứu 1", "Nghiên cứu 2", "Nghiên cứu 3", "Gộp"], "ref": 1.0,
                          "truc_x": "RR (KTC 95%)", "log": True},
                  ghi_chu=["Ô vuông tỷ lệ với trọng số; hình thoi là hiệu ứng gộp; ghi I² và khoảng dự báo.",
                           "Chữ viết tắt — RR: nguy cơ tương đối; KTC: khoảng tin cậy."]),
            Khung("bieu_do", f"Funnel plot đánh giá sai lệch công bố (Mục tiêu {k})", dac_ta={"kieu": "pheu"},
                  ghi_chu=["Chỉ vẽ và kiểm định Egger khi có từ 10 nghiên cứu trở lên."])]


def _khung_dinh_tinh(nc: NguCanh, k: int, ten_mt: str) -> List[Khung]:
    cot = ["Chủ đề", "Chủ đề phụ", "Mô tả", "Trích dẫn minh hoạ (mã người tham gia)"]
    dong = [[f"Chủ đề {i}", X, X, X] for i in (1, 2, 3)]
    return [Khung("bang", f"Các chủ đề và chủ đề phụ rút ra từ phân tích (Mục tiêu {k})", cot, dong,
                  ["Trích dẫn đã khử định danh, ghi mã người tham gia; chủ đề được hình thành từ dữ liệu."]),
            Khung("bieu_do", f"Sơ đồ chủ đề và mối liên hệ giữa các chủ đề (Mục tiêu {k})",
                  dac_ta={"kieu": "so_do_chu_de", "goc": _hoa_dau(ten_mt)[:60]},
                  ghi_chu=["Sơ đồ minh hoạ cấu trúc chủ đề; tên chủ đề điền theo kết quả phân tích."])]


def _khung_muc_tieu(nc: NguCanh, k: int, muc_tieu: str) -> List[Khung]:
    tk = nc.thiet_ke
    ten_mt = _ten_muc_tieu(muc_tieu) or f"Kết quả mục tiêu {k}"
    dong_mt = _dong_ma_tran(nc, muc_tieu=k)
    kq = [r for r in dong_mt if (r.get("vai_tro") or "") in ("ket_cuc_chinh", "ket_cuc_phu", "mo_ta")]
    pts = _phan_tich_cua(nc, k, [r["bien"].strip() for r in kq])
    if tk == "diagnostic":
        return _khung_chan_doan(nc, k, ten_mt)
    if tk == "prediction":
        return _khung_du_bao(nc, k, ten_mt, dong_mt)
    if tk == "sr_ma":
        return _khung_gop(nc, k, ten_mt)
    if tk == "qualitative":
        return _khung_dinh_tinh(nc, k, ten_mt)
    if tk == "rct" and any((r.get("vai_tro") or "") == "phoi_nhiem" for r in dong_mt):
        return _khung_rct(nc, k, ten_mt, dong_mt, pts)
    if _la_phan_tich_lien_quan(muc_tieu, dong_mt) and any((r.get("vai_tro") or "") in ("yeu_to", "phoi_nhiem")
                                                           for r in dong_mt):
        kh = _khung_lien_quan(nc, k, ten_mt, dong_mt, pts)
        if tk == "cohort" and any((p.get("tham_so") or {}).get("outcome_type") in ("cox", "survival") for p in pts):
            kh.append(Khung("bieu_do", f"Đường cong Kaplan–Meier theo tình trạng phơi nhiễm (Mục tiêu {k})",
                            dac_ta={"kieu": "km", "nhan": [c.split(" (n =")[0] for c in _cot_nhom(
                                nc, _bien_nhom(nc), ("Phơi nhiễm", "Không phơi nhiễm"))]},
                            ghi_chu=["Kèm bảng số người còn nguy cơ theo mốc thời gian dưới trục hoành; kiểm định "
                                     "log-rank."]))
        return kh
    if not kq:
        kq = [{"bien": "", "khai_niem": ten_mt}]
    return _khung_mo_ta_kq(nc, k, ten_mt, [r for r in kq if r.get("bien")] or kq)


def _khung_nhom_nho_do_nhay(nc: NguCanh) -> List[Khung]:
    ngu_canh_nho = nc
    nn = [p for p in nc.phan_tich if p.get("vai") == "nhom_con"]
    dn = [p for p in nc.phan_tich if p.get("vai") == "do_nhay"]
    if not nn and not dn:
        return []
    chinh = _phan_tich_chinh(nc)
    _ten, vt, ref = _thuoc_do(chinh, nc.thiet_ke)
    cot = ["Phân tích", "Loại", "n", "Ước lượng (KTC 95%)", "So với phân tích chính"]
    dong = [[_lam_sach_mo_ta(ngu_canh_nho, str(p.get("mo_ta") or p.get("id")))[:110],
             "nhóm nhỏ" if p.get("vai") == "nhom_con" else "độ nhạy", X, f"{X} ({X} – {X})", "cùng chiều / khác chiều"]
            for p in nn + dn]
    kh = [Khung("bang", "Kết quả phân tích nhóm nhỏ và phân tích độ nhạy", cot, dong,
                _ghi_chu(cot, dong, ["Các phân tích đã định trước trong kế hoạch phân tích; phân tích nhóm nhỏ chỉ "
                                     "mang tính thăm dò, kèm kiểm định tương tác."]))]
    if len(nn) >= 2:
        kh.append(Khung("bieu_do", "Ước lượng theo nhóm nhỏ kèm KTC 95%",
                        dac_ta={"kieu": "forest", "nhan": [_lam_sach_mo_ta(ngu_canh_nho, str(p.get("mo_ta") or
                                                                                         p.get("id")))[:40]
                                                          for p in nn][:12] + ["Chung"],
                                "ref": ref if chinh else None, "truc_x": "Ước lượng (KTC 95%)",
                                "log": bool(chinh) and ref == 1.0},
                        ghi_chu=["Đường dọc là ước lượng không hiệu ứng; mỗi hàng là một nhóm nhỏ đã định trước."]))
    return kh


def _khung_an_toan(nc: NguCanh) -> List[Khung]:
    if nc.thiet_ke != "rct":
        return []
    nhom = [c.split(" (n =")[0] for c in _cot_nhom(nc, _bien_nhom(nc), ("Nhóm can thiệp", "Nhóm chứng"))[:2]]
    bc = [r for r in nc.ma_tran if re.search(r"biến cố|an toàn|tác dụng", str(r.get("khai_niem") or ""), re.I)]
    dong = [[_nhan_bien(nc, r["bien"].strip(), r.get("khai_niem") or ""), f"{X} ({X})", f"{X} ({X})"] for r in bc]
    dong += [["Biến cố bất lợi nghiêm trọng", f"{X} ({X})", f"{X} ({X})"],
             ["Ngừng can thiệp do biến cố bất lợi", f"{X} ({X})", f"{X} ({X})"]]
    cot = ["Biến cố"] + [f"{g}: n (%)" for g in nhom]
    return [Khung("bang", "Biến cố bất lợi theo nhóm phân bổ", cot, dong,
                  _ghi_chu(cot, dong, ["Mỗi người được tính một lần cho mỗi loại biến cố; phân độ mức nặng theo định "
                                       "nghĩa ở mục an toàn."]))]


def dung_khung(nc: NguCanh) -> List[Muc]:
    """Các mục của chương «Dự kiến kết quả» theo thiết kế và theo TỪNG mục tiêu."""
    tieu_de_1 = {"sr_ma": "Đặc điểm các nghiên cứu được đưa vào tổng quan",
                 "qualitative": "Đặc điểm người tham gia nghiên cứu"}.get(nc.thiet_ke, "Đặc điểm đối tượng nghiên cứu")
    muc = [Muc(tieu_de_1, [_so_do(nc), _bang_dac_diem(nc)])]
    for k, mt in enumerate(nc.muc_tieu or ["Kết quả nghiên cứu"], 1):
        muc.append(Muc(f"Kết quả theo mục tiêu {k}: {_ten_muc_tieu(mt)}", _khung_muc_tieu(nc, k, mt), k))
    nd = _khung_nhom_nho_do_nhay(nc)
    if nd:
        muc.append(Muc("Phân tích nhóm nhỏ và phân tích độ nhạy", nd))
    at = _khung_an_toan(nc)
    if at:
        muc.append(Muc("An toàn của can thiệp", at))
    return muc


# ─────────────────────────────── xuất Markdown ───────────────────────────────
GIOI_THIEU = (
    "Kết quả được trình bày theo thứ tự đặc điểm đối tượng nghiên cứu, rồi lần lượt theo từng mục tiêu nghiên cứu. Các "
    "bảng, hình và biểu đồ dưới đây là khung trình bày đã xác định trước theo kế hoạch phân tích; số liệu được "
    "điền sau "
    "khi phân tích. Quy ước trình bày: biến định lượng mô tả bằng trung bình ± độ lệch chuẩn khi phân phối gần chuẩn, "
    "ngược lại bằng trung vị [khoảng tứ phân vị]; biến định tính bằng tần số và tỷ lệ phần trăm, ghi rõ mẫu số "
    "khi khác "
    "cỡ mẫu chung; tỷ lệ và các ước lượng hiệu ứng kèm khoảng tin cậy 95%; giá trị p ghi ba chữ số thập phân "
    "(p < 0,001 khi nhỏ hơn). Tên bảng đặt phía trên bảng, tên hình và biểu đồ đặt phía dưới; chữ viết tắt được giải "
    "thích ngay dưới mỗi bảng."
)


def _hang(o: Sequence[str]) -> str:
    return "| " + " | ".join(str(x).replace("|", "/") if str(x) != "" else " " for x in o) + " |"


def ve_chuong(muc: List[Muc], chuong: int = 5, out_dir: Optional[Path] = None, ve_anh: bool = True,
              them_cuoi: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """→ (dòng Markdown của chương, danh sách lỗi vẽ hình). Ảnh ghi vào `<out_dir>/bieu-bang/`; không vẽ được ⇒ hình
    vẫn có tên và mô tả, lỗi trả về để nơi gọi báo (không im lặng)."""
    dong = [f"# {chuong}. DỰ KIẾN KẾT QUẢ", "", GIOI_THIEU, ""]
    dem = {"bang": 0, "hinh": 0, "bieu_do": 0}
    nhan_loai = {"bang": "Bảng", "hinh": "Hình", "bieu_do": "Biểu đồ"}
    loi_ve: List[str] = []
    thu_muc = (Path(out_dir) / THU_MUC_HINH) if out_dir else None
    for i, m in enumerate(muc, 1):
        dong += [f"## {chuong}.{i}. {m.tieu_de}", ""]
        for kh in m.khung:
            dem[kh.loai] += 1
            so = f"{chuong}.{dem[kh.loai]}"
            tieu = f"**{nhan_loai[kh.loai]} {so}. {kh.ten}**"
            if kh.loai == "bang":
                dong += [tieu, "", _hang(kh.cot), _hang(["---"] * len(kh.cot))]
                dong += [_hang(d + [""] * (len(kh.cot) - len(d))) for d in kh.dong]
                dong.append("")
                if kh.ghi_chu:
                    dong += ["*Ghi chú:* " + " ".join(kh.ghi_chu), ""]
            else:
                ten_tep = f"{'hinh' if kh.loai == 'hinh' else 'bieu-do'}-{so.replace('.', '-')}.png"
                ve_duoc = False
                if ve_anh and thu_muc is not None:
                    try:
                        ve_hinh(kh, thu_muc / ten_tep)
                        ve_duoc = True
                    except Exception as e:  # noqa: BLE001 — thiếu matplotlib/font: báo, không sập cả chương
                        loi_ve.append(f"{nhan_loai[kh.loai]} {so}: {type(e).__name__}: {str(e)[:120]}")
                if ve_duoc:
                    dong += [f"![{nhan_loai[kh.loai]} {so}]({THU_MUC_HINH}/{ten_tep})", ""]
                else:
                    dong += [f"*Mô tả {nhan_loai[kh.loai].lower()}:* {_mo_ta_hinh(kh)}", ""]
                dong += [tieu, ""]
                if kh.ghi_chu:
                    dong += ["*Ghi chú:* " + " ".join(kh.ghi_chu), ""]
    if them_cuoi:
        dong += them_cuoi
    return dong, loi_ve


def _mo_ta_hinh(kh: Khung) -> str:
    d = kh.dac_ta
    kieu = d.get("kieu")
    if kieu == "so_do":
        cac = [b[0].split("\n")[0] for b in d.get("buoc", [])]
        return "sơ đồ các bước " + " → ".join(cac) + "."
    return {"cot_ktc": "biểu đồ cột, mỗi cột một nhóm/chỉ số, thanh sai số là KTC 95%.",
            "forest": "forest plot, mỗi hàng một yếu tố, điểm và đoạn KTC 95%, đường dọc không hiệu ứng.",
            "roc": "đường cong ROC, trục tung độ nhạy, trục hoành 1 − độ đặc hiệu.",
            "hieu_chuan": "biểu đồ hiệu chuẩn, trục hoành nguy cơ dự báo, trục tung nguy cơ quan sát.",
            "km": "đường cong Kaplan–Meier theo nhóm, kèm số người còn nguy cơ.",
            "pheu": "funnel plot, trục hoành hiệu ứng, trục tung sai số chuẩn.",
            "so_do_chu_de": "sơ đồ chủ đề chính và chủ đề phụ."}.get(kieu, "biểu đồ.")


# ─────────────────────────────── vẽ hình ───────────────────────────────
def _plt():
    import logging  # noqa: PLC0415

    # 19/11/2026 (CI Ubuntu): lần đầu dựng bộ nhớ đệm phông, matplotlib ghi log INFO («generated new fontManager»…) qua
    # cấu hình logging của app — các dòng này rơi SAU khối JSON của bộ sinh đề cương ⇒ bộ giả lập đọc hỏng kết quả.
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    import matplotlib  # noqa: PLC0415

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
                         "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "khung-bieu-bang", "pdf.fonttype": 42})
    return plt


def _ngat(s: str, rong: int = 34) -> str:
    import textwrap  # noqa: PLC0415

    return "\n".join(textwrap.fill(d, rong) if d else d for d in str(s).split("\n"))


def ve_hinh(kh: Khung, dich: Path, du_lieu: Optional[Dict[str, Any]] = None) -> Path:
    """Vẽ một hình/biểu đồ ra PNG 300 dpi. `du_lieu` (tuỳ chọn, dùng ở G6) mang số thật: {"uoc_luong": [...],
    "duoi": [...], "tren": [...]} — vắng thì vẽ KHUNG (trục, nhãn, đường tham chiếu, chú giải), không vẽ số."""
    plt = _plt()
    d = kh.dac_ta
    kieu = d.get("kieu")
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    if kieu == "so_do":
        fig = _ve_so_do(plt, d.get("buoc") or [], d.get("tach") or [])
    elif kieu == "cot_ktc":
        nhan = [_ngat(x, 18) for x in (d.get("nhan") or ["Nhóm 1", "Nhóm 2"])]
        fig, ax = plt.subplots(figsize=(max(4.5, 1.1 * len(nhan) + 2), 3.6))
        x = list(range(len(nhan)))
        if du_lieu and du_lieu.get("uoc_luong"):
            u, lo, hi = du_lieu["uoc_luong"], du_lieu.get("duoi") or [], du_lieu.get("tren") or []
            ax.bar(x, u, color="#9aa7b5", edgecolor="#333333", width=0.6)
            if lo and hi:
                ax.errorbar(x, u, yerr=[[a - b for a, b in zip(u, lo)], [c - a for a, c in zip(u, hi)]], fmt="none",
                            ecolor="#222222", capsize=4, lw=1)
            ax.set_ylim(0, max(100 if "%" in d.get("truc_y", "") else 0, max(hi or u) * 1.15))
        else:
            ax.set_ylim(0, 100 if "%" in d.get("truc_y", "") else 1)
            ax.bar(x, [0] * len(x), width=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(nhan, fontsize=8)
        ax.set_ylabel(d.get("truc_y") or "")
        if d.get("truc_x"):
            ax.set_xlabel(d["truc_x"])
        ax.yaxis.grid(True, color="#dddddd", lw=0.6)
        ax.set_axisbelow(True)
    elif kieu == "forest":
        nhan = [_ngat(x, 40) for x in (d.get("nhan") or ["Yếu tố 1", "Yếu tố 2"])]
        fig, ax = plt.subplots(figsize=(6.2, max(2.4, 0.38 * len(nhan) + 1.2)))
        y = list(range(len(nhan)))[::-1]
        ref = d.get("ref")
        log = bool(d.get("log"))
        if du_lieu and du_lieu.get("uoc_luong"):
            u, lo, hi = du_lieu["uoc_luong"], du_lieu.get("duoi") or [], du_lieu.get("tren") or []
            for yi, a, b, c in zip(y, u, lo or u, hi or u):
                ax.plot([b, c], [yi, yi], color="#222222", lw=1)
                ax.plot([a], [yi], marker="s", color="#222222", ms=5)
        if log:
            from matplotlib.ticker import FixedLocator, NullLocator  # noqa: PLC0415

            ax.set_xscale("log")
            ax.set_xlim(0.2, 5)
            vach = [0.25, 0.5, 1, 2, 4]
            ax.xaxis.set_major_locator(FixedLocator(vach))
            ax.xaxis.set_minor_locator(NullLocator())
            ax.set_xticklabels([str(v).replace(".", ",") for v in vach])
        elif ref is not None:
            ax.set_xlim(ref - 1, ref + 1)
        if ref is not None:
            ax.axvline(ref, color="#555555", lw=0.8, ls="--")
        ax.set_yticks(y)
        ax.set_yticklabels(nhan, fontsize=8)
        ax.set_ylim(-0.8, len(nhan) - 0.2)
        ax.set_xlabel(d.get("truc_x") or "")
    elif kieu in ("roc", "hieu_chuan"):
        fig, ax = plt.subplots(figsize=(4.2, 4.2))
        ax.plot([0, 1], [0, 1], color="#777777", lw=0.8, ls="--")
        if du_lieu and du_lieu.get("x"):
            ax.plot(du_lieu["x"], du_lieu["y"], color="#222222", lw=1.2)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        if kieu == "roc":
            ax.set_xlabel("1 − Độ đặc hiệu")
            ax.set_ylabel("Độ nhạy")
        else:
            ax.set_xlabel("Nguy cơ dự báo")
            ax.set_ylabel("Nguy cơ quan sát")
    elif kieu == "km":
        fig, ax = plt.subplots(figsize=(5.6, 3.8))
        for i, nh in enumerate(d.get("nhan") or ["Nhóm 1", "Nhóm 2"]):
            ax.plot([], [], color=("#222222", "#888888", "#444444", "#aaaaaa")[i % 4],
                    ls=("-", "--", "-.", ":")[i % 4], label=nh)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("Thời gian theo dõi")
        ax.set_ylabel("Xác suất chưa xảy ra biến cố")
        ax.legend(frameon=False, fontsize=8)
    elif kieu == "pheu":
        fig, ax = plt.subplots(figsize=(4.4, 3.8))
        ax.axvline(1, color="#555555", lw=0.8, ls="--")
        from matplotlib.ticker import FixedLocator, NullLocator  # noqa: PLC0415

        ax.set_xscale("log")
        ax.set_xlim(0.2, 5)
        ax.xaxis.set_major_locator(FixedLocator([0.25, 0.5, 1, 2, 4]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels(["0,25", "0,5", "1", "2", "4"])
        ax.set_ylim(1, 0)
        ax.set_xlabel("Hiệu ứng (thang log)")
        ax.set_ylabel("Sai số chuẩn")
    elif kieu == "so_do_chu_de":
        fig = _ve_so_do_chu_de(plt, d.get("goc") or "Câu hỏi nghiên cứu")
    else:
        raise ValueError(f"kiểu hình chưa hỗ trợ: {kieu}")
    fig.savefig(dich, dpi=300, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    return dich


def _hop(ax, x, y, chu, rong=0.36, cao=None, co=8):
    import matplotlib.patches as mp  # noqa: PLC0415

    rong_chu = max(16, int(rong * 100))
    dong = _ngat(chu, rong_chu).count("\n") + 1
    cao_hinh = ax.figure.get_size_inches()[1]
    cao = cao or (dong * co * 1.35 / 72 + 0.12) / cao_hinh
    ax.add_patch(mp.FancyBboxPatch((x - rong / 2, y - cao / 2), rong, cao, boxstyle="square,pad=0.004",
                                   fc="white", ec="#222222", lw=0.8))
    ax.text(x, y, _ngat(chu, rong_chu), ha="center", va="center", fontsize=co)
    return cao


def _mui_ten(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": "#222222"})


def _ve_so_do(plt, buoc: List[Tuple[str, Optional[str]]], tach: List[List[str]]):
    so_hang = len(buoc) + max((len(c) for c in tach), default=0)
    fig, ax = plt.subplots(figsize=(7.2, 1.35 * so_hang + 0.4))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    buoc_y = 1 / (so_hang + 0.5)
    y = 1 - buoc_y * 0.6
    x_chinh = 0.32 if not tach else 0.5
    rong_chinh = 0.42 if not tach else 0.34
    x_ben, rong_ben = (0.8, 0.34) if not tach else (0.845, 0.29)
    cao_truoc = None
    for i, (chinh, ben) in enumerate(buoc):
        cao = _hop(ax, x_chinh, y, chinh, rong=rong_chinh)
        if cao_truoc is not None:
            _mui_ten(ax, x_chinh, y + buoc_y - cao_truoc / 2, x_chinh, y + cao / 2)
        if ben:
            yb = y - buoc_y / 2 if i < len(buoc) - 1 or tach else y
            _hop(ax, x_ben, yb, ben, rong=rong_ben)
            ax.plot([x_chinh, x_ben - rong_ben / 2], [yb, yb], color="#222222", lw=0.8)
        cao_truoc = cao
        y -= buoc_y
    if tach:
        k = len(tach)
        xs = [(j + 0.5) / k for j in range(k)]
        y_tach = y
        ax.plot([xs[0], xs[-1]], [y_tach + buoc_y * 0.55, y_tach + buoc_y * 0.55], color="#222222", lw=0.8)
        ax.plot([x_chinh, x_chinh], [y_tach + buoc_y - (cao_truoc or 0) / 2, y_tach + buoc_y * 0.55],
                color="#222222", lw=0.8)
        for xj, cot in zip(xs, tach):
            yy = y_tach
            truoc = None
            for j, chu in enumerate(cot):
                cao = _hop(ax, xj, yy, chu, rong=min(0.3, 0.9 / k))
                _mui_ten(ax, xj, (yy + buoc_y - truoc / 2) if truoc else yy + buoc_y * 0.55, xj, yy + cao / 2)
                truoc = cao
                yy -= buoc_y
    return fig


def _ve_so_do_chu_de(plt, goc: str):
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    _hop(ax, 0.5, 0.82, goc, rong=0.5)
    for j, x in enumerate((0.18, 0.5, 0.82), 1):
        _hop(ax, x, 0.46, f"Chủ đề {j}", rong=0.24)
        _mui_ten(ax, 0.5, 0.75, x, 0.5)
        for dx in (-0.06, 0.06):
            _hop(ax, x + dx, 0.15, "Chủ đề phụ", rong=0.11, co=7)
            _mui_ten(ax, x, 0.42, x + dx, 0.18)
    return fig


# ─────────────────────────────── K9 — chấm biểu bảng ───────────────────────────────
_TIEU_DE_BB = re.compile(r"^\*\*(Bảng|Hình|Biểu đồ)\s+(\d+)\.(\d+)\.\s+(.+?)\.?\*\*\s*$")
_TIEU_DE_LECH = re.compile(r"^\s*[*_]?\s*(Bảng|Hình|Biểu đồ|Sơ đồ)\s+\d+(?:\.\d+)*\s*[.:,]")
_O_GIU_CHO = re.compile(r"\(\s*\d+\s+biến\s*\)|\[\s*C[ẦA]N|^\s*…\s*$|^\s*\.\.\.\s*$|thêm biến", re.I)
_VIET_TAT_KIEM = ("TB", "ĐLC", "KTPV", "KTC", "OR", "PR", "RR", "HR", "AUC", "PPV", "NPV", "ICC", "RD", "MD")
# Thiết kế → các loại khung bắt buộc (khoá: mô tả lỗi, mẫu tìm trong TÊN bảng/hình/biểu đồ)
BAT_BUOC = {
    "rct": [("Hình", r"CONSORT|phân bổ"), ("Bảng", r"nền|phân bổ"), ("Bảng", r"[Bb]iến cố")],
    "cross_sectional": [("Hình", r"STROBE|chọn đối tượng"), ("Bảng", r"[Đđ]ặc điểm")],
    "cohort": [("Hình", r"STROBE|chọn đối tượng"), ("Bảng", r"[Đđ]ặc điểm")],
    "case_control": [("Hình", r"STROBE|chọn đối tượng"), ("Bảng", r"[Đđ]ặc điểm")],
    "diagnostic": [("Hình", r"STARD"), ("Bảng", r"tiêu chuẩn tham chiếu"), ("Biểu đồ", r"ROC")],
    "prediction": [("Hình", r"TRIPOD|phát triển"), ("Bảng", r"[Hh]iệu năng"), ("Biểu đồ", r"hiệu chuẩn")],
    "sr_ma": [("Hình", r"PRISMA"), ("Bảng", r"[Đđ]ặc điểm các nghiên cứu"), ("Biểu đồ", r"[Ff]orest")],
    "qualitative": [("Bảng", r"[Đđ]ặc điểm"), ("Bảng", r"[Cc]hủ đề")],
}


def _chuong_du_kien(md: str) -> Tuple[List[str], int]:
    dong = md.splitlines()
    bd = next((i for i, d in enumerate(dong) if re.match(r"^#\s+\d+\.\s+DỰ KIẾN KẾT QUẢ", d.strip())), None)
    if bd is None:
        return [], -1
    kt = next((i for i in range(bd + 1, len(dong)) if re.match(r"^#\s+\S", dong[i])), len(dong))
    return dong[bd:kt], bd


def kiem_bieu_bang(md: str, thiet_ke: str, so_muc_tieu: int, goc: Optional[Path] = None) -> List[str]:
    """Luật K9 (19/11/2026) trên chương «Dự kiến kết quả» của đề cương nộp. Rỗng = đạt."""
    ch, bd = _chuong_du_kien(md)
    if not ch:
        return ["K9 không thấy chương «DỰ KIẾN KẾT QUẢ»"]
    loi: List[str] = []
    so_ch = re.match(r"^#\s+(\d+)\.", ch[0]).group(1)
    dem = {"Bảng": 0, "Hình": 0, "Biểu đồ": 0}
    ten_theo_loai: Dict[str, List[str]] = {"Bảng": [], "Hình": [], "Biểu đồ": []}
    for i, d in enumerate(ch):
        s = d.strip()
        so_dong = bd + i + 1
        m = _TIEU_DE_BB.match(s)
        if not m:
            if _TIEU_DE_LECH.match(s) and not s.startswith("**"):
                loi.append(f"K9 dòng {so_dong}: tên bảng/hình chưa đúng chuẩn (phải in đậm «**Bảng {so_ch}.k. Tên**»)")
            continue
        loai, c, k, ten = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        dem[loai] += 1
        ten_theo_loai[loai].append(ten)
        if c != so_ch or k != dem[loai]:
            loi.append(f"K9 dòng {so_dong}: đánh số {loai} {c}.{k} không liên tục (đúng ra {so_ch}.{dem[loai]})")
        sau = next((x.strip() for x in ch[i + 1:] if x.strip()), "")
        truoc = next((x.strip() for x in reversed(ch[:i]) if x.strip()), "")
        if loai == "Bảng":
            if not sau.startswith("|"):
                loi.append(f"K9 dòng {so_dong}: tên Bảng {c}.{k} phải đặt ngay PHÍA TRÊN bảng")
                continue
            j = i + 1 + next(n for n, x in enumerate(ch[i + 1:]) if x.strip())
            hang = []
            while j < len(ch) and ch[j].strip().startswith("|"):
                hang.append([o.strip() for o in ch[j].strip().strip("|").split("|")])
                j += 1
            than = [h for h in hang[2:]] if len(hang) > 2 else []
            if not than:
                loi.append(f"K9 Bảng {c}.{k}: bảng không có hàng nội dung")
            for h in than:
                if h and _O_GIU_CHO.search(h[0] or ""):
                    loi.append(f"K9 Bảng {c}.{k}: hàng giữ chỗ «{h[0][:30]}» — liệt kê đúng biến/chỉ số")
                    break
            ghi = next((x.strip() for x in ch[j:] if x.strip()), "")
            chu_bang = " ".join(" ".join(h) for h in hang)
            vt_dung = [v for v in _VIET_TAT_KIEM if re.search(rf"(?<![\wÀ-ỹ]){re.escape(v)}(?![\wÀ-ỹ])", chu_bang)]
            if vt_dung and not ghi.startswith("*Ghi chú"):
                loi.append(f"K9 Bảng {c}.{k}: thiếu «Ghi chú» dưới bảng giải thích chữ viết tắt ({', '.join(vt_dung)})")
            elif vt_dung:
                thieu = [v for v in vt_dung if not re.search(rf"(?<![\wÀ-ỹ]){re.escape(v)}\s*:", ghi)]
                if thieu:
                    loi.append(f"K9 Bảng {c}.{k}: ghi chú chưa giải thích {', '.join(thieu)}")
            dau = " ".join(hang[0]) if hang else ""
            if re.search(r"đặc điểm nền", ten, re.I) and re.search(r"(?<![\wÀ-ỹ])p(?![\wÀ-ỹ])", dau):
                loi.append(f"K9 Bảng {c}.{k}: bảng đặc điểm nền có cột p (CONSORT/STROBE: không kiểm định trong bảng "
                           "mô tả)")
            if re.search(r"\b(?:OR|PR|RR|HR|MD)\b|[Hh]iệu ứng|[Hh]iệu số", dau) and "KTC" not in dau and \
                    not re.search(r"KTC|khoảng tin cậy", chu_bang):
                loi.append(f"K9 Bảng {c}.{k}: ước lượng hiệu ứng chưa kèm KTC 95%")
        else:
            if not (truoc.startswith("![") or truoc.startswith("*Mô tả")):
                loi.append(f"K9 dòng {so_dong}: tên {loai} {c}.{k} phải đặt ngay PHÍA DƯỚI hình")
            elif truoc.startswith("![") and goc is not None:
                m2 = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", truoc)
                if m2 and not (Path(goc) / m2.group(1)).is_file():
                    loi.append(f"K9 {loai} {c}.{k}: thiếu tệp hình {m2.group(1)}")
    chu_ch = "\n".join(ch)
    for k in range(1, max(1, so_muc_tieu) + 1):
        if not re.search(rf"\(Mục tiêu {k}(?![\d])[^()]*\)\.?\*\*", chu_ch):
            loi.append(f"K9 mục tiêu {k} chưa có bảng hoặc biểu đồ nào trả lời (tên gắn «(Mục tiêu {k})»)")
    if dem["Hình"] + dem["Biểu đồ"] == 0:
        loi.append("K9 chương dự kiến kết quả chưa có hình/biểu đồ nào")
    for loai, mau in BAT_BUOC.get(thiet_ke, []):
        if not any(re.search(mau, t) for t in ten_theo_loai.get(loai, [])):
            loi.append(f"K9 thiếu {loai.lower()} bắt buộc của thiết kế ({TEN_CHUAN.get(thiet_ke, thiet_ke)}): «{mau}»")
    return loi


# ─────────────────────────────── thay chương trong đề cương hiện có ───────────────────────────────
def chuong_moi(out_dir: Path, study: str, chuong: int = 5, ve_anh: bool = True, **kw: Any
               ) -> Tuple[List[str], List[str], NguCanh]:
    nc = nap_ngu_canh(out_dir, study, **kw)
    dong, loi_ve = ve_chuong(dung_khung(nc), chuong, out_dir if ve_anh else None, ve_anh)
    return dong, loi_ve, nc


def thay_chuong(md: str, chuong_md: List[str]) -> str:
    dong = md.splitlines()
    ch, bd = _chuong_du_kien(md)
    if bd < 0:
        raise ValueError("đề cương không có chương «DỰ KIẾN KẾT QUẢ»")
    kt = bd + len(ch)
    # giữ đúng số chương của văn bản gốc
    so = re.match(r"^#\s+(\d+)\.", dong[bd]).group(1)
    moi = [re.sub(r"^#\s+\d+\.", f"# {so}.", chuong_md[0])] + [
        re.sub(r"^(##\s+)\d+\.", rf"\g<1>{so}.", x) if x.startswith("## ") else
        re.sub(r"^\*\*(Bảng|Hình|Biểu đồ) \d+\.", rf"**\1 {so}.", x) for x in chuong_md[1:]]
    while moi and not moi[-1].strip():
        moi.pop()
    return "\n".join(dong[:bd] + moi + [""] + dong[kt:]) + ("\n" if md.endswith("\n") else "")


_TD_NGHIENG = re.compile(r"^\*(Bảng|Hình|Biểu đồ)\s+(\d+)\.(\d+)\.\s+(.+?)\.?\*(.*)$")


def _so_do_tu_bang(hang: List[List[str]]) -> Optional[Khung]:
    """Bảng «Bước | Số lượng» của sơ đồ soạn tay ⇒ sơ đồ thật: hàng mở đầu «→» là hộp loại bên cạnh bước trước."""
    buoc: List[List[Optional[str]]] = []
    for h in hang[2:]:
        if len(h) < 2:
            continue
        chu = re.sub(r"\*\*", "", h[0]).strip()
        so = re.sub(r"\*\*", "", h[1]).strip()
        o = f"{chu.lstrip('→ ').strip()} ({so if so.startswith('n') else 'n = ' + so})"
        if chu.startswith("→") and buoc:
            buoc[-1][1] = (buoc[-1][1] + "\n" if buoc[-1][1] else "") + o
        else:
            buoc.append([o, None])
    if len(buoc) < 2:
        return None
    return Khung("hinh", "", dac_ta={"kieu": "so_do", "buoc": [tuple(b) for b in buoc], "tach": []})


def nang_cap_chuong(md: str, ngu: NguCanh, out_dir: Optional[Path], ve_anh: bool = True) -> Tuple[str, List[str]]:
    """Nâng cấp TẠI CHỖ chương «Dự kiến kết quả» của đề cương soạn tay (giữ nội dung bảng của nhóm nghiên cứu):
    tên bảng/hình in đậm và đánh số lại liên tục; bảng có chữ viết tắt được thêm/ghép «Ghi chú»; «Hình» dựng bằng bảng
    «Bước | Số lượng» ⇒ sơ đồ thật, tên đặt dưới; tên bảng không kèm bảng (chỉ một câu) ⇒ bảng phân tích độ nhạy/nhóm
    nhỏ dựng từ đặc tả; mỗi mục tiêu chưa có biểu đồ ⇒ thêm biểu đồ của khung chuẩn ngay sau bảng cuối của mục tiêu
    đó."""
    ch, bd = _chuong_du_kien(md)
    if bd < 0:
        raise ValueError("đề cương không có chương «DỰ KIẾN KẾT QUẢ»")
    dong_goc = md.splitlines()
    so_ch = re.match(r"^#\s+(\d+)\.", ch[0]).group(1)
    khung_chuan = {m.muc_tieu: m.khung for m in dung_khung(ngu) if m.muc_tieu}
    nd = _khung_nhom_nho_do_nhay(ngu)
    ra: List[str] = []
    loi_ve: List[str] = []
    dem = {"Bảng": 0, "Hình": 0, "Biểu đồ": 0}
    thu_muc = (Path(out_dir) / THU_MUC_HINH) if out_dir else None
    cuoi_mt: Dict[int, int] = {}

    def _ve(kh: Khung, loai: str) -> List[str]:
        dem[loai] += 1
        so = f"{so_ch}.{dem[loai]}"
        ten_tep = f"{'hinh' if loai == 'Hình' else 'bieu-do'}-{so.replace('.', '-')}.png"
        kq = []
        if ve_anh and thu_muc is not None:
            try:
                ve_hinh(kh, thu_muc / ten_tep)
                kq = [f"![{loai} {so}]({THU_MUC_HINH}/{ten_tep})", ""]
            except Exception as e:  # noqa: BLE001
                loi_ve.append(f"{loai} {so}: {type(e).__name__}: {str(e)[:120]}")
        if not kq:
            kq = [f"*Mô tả {loai.lower()}:* {_mo_ta_hinh(kh)}", ""]
        kq += [f"**{loai} {so}. {kh.ten}**", ""]
        if kh.ghi_chu:
            kq += ["*Ghi chú:* " + " ".join(kh.ghi_chu), ""]
        return kq

    i = 0
    while i < len(ch):
        d = ch[i]
        s_ = d.strip()
        m = _TD_NGHIENG.match(s_) or _TIEU_DE_BB.match(s_)
        if not m:
            ra.append(d)
            i += 1
            continue
        loai, ten = m.group(1), m.group(4).strip().rstrip(".")
        sau_cau = (m.group(5).strip() if m.re is _TD_NGHIENG and m.lastindex >= 5 else "")
        j = i + 1
        while j < len(ch) and not ch[j].strip():
            j += 1
        hang: List[List[str]] = []
        k2 = j
        while k2 < len(ch) and ch[k2].strip().startswith("|"):
            hang.append([o.strip() for o in ch[k2].strip().strip("|").split("|")])
            k2 += 1
        mt = re.search(r"\(Mục tiêu (\d+)", ten)
        if loai == "Hình" and hang and re.search(r"[Bb]ước", " ".join(hang[0])):
            kh = _so_do_tu_bang(hang)
            if kh:
                kh.ten = ten
                kh.ghi_chu = ["Số lượng ở từng bước và lý do loại được ghi đầy đủ khi kết thúc thu thập số liệu."]
                ra += _ve(kh, "Hình")
                i = k2
                continue
        if loai == "Bảng" and not hang:
            dem["Bảng"] += 1
            if nd and re.search(r"độ nhạy|nhóm nhỏ", ten, re.I):
                bang = nd[0]
                ra += [f"**Bảng {so_ch}.{dem['Bảng']}. {ten}**", "", _hang(bang.cot), _hang(["---"] * len(bang.cot))]
                ra += [_hang(x + [""] * (len(bang.cot) - len(x))) for x in bang.dong]
                ra += ["", "*Ghi chú:* " + " ".join(bang.ghi_chu + ([sau_cau] if sau_cau else [])), ""]
            else:
                ra += [f"**Bảng {so_ch}.{dem['Bảng']}. {ten}**", ""] + ([sau_cau, ""] if sau_cau else [])
            i += 1
            continue
        dem[loai] += 1
        ra += [f"**{loai} {so_ch}.{dem[loai]}. {ten}**", ""]
        ra += ch[j:k2]
        i = k2
        if hang:
            # ghi chú: ghép ghi chú nghiêng sẵn có ngay dưới bảng + chữ viết tắt
            n2 = i
            while n2 < len(ch) and not ch[n2].strip():
                n2 += 1
            cu = ch[n2].strip() if n2 < len(ch) else ""
            co_ghi_cu = cu.startswith("*") and not _TD_NGHIENG.match(cu) and not cu.startswith("**")
            ghi_cu = cu.strip("*").strip() if co_ghi_cu else ""
            if ghi_cu.startswith("Ghi chú:"):
                ghi_cu = ghi_cu[len("Ghi chú:"):].strip()
            them = _ghi_chu(hang[0], hang[2:], [ghi_cu] if ghi_cu else [])
            ra += [""] + (["*Ghi chú:* " + " ".join(them)] if them else []) + [""]
            if co_ghi_cu:
                i = n2 + 1
        if mt:
            cuoi_mt[int(mt.group(1))] = len(ra)
    # biểu đồ cho mục tiêu chưa có biểu đồ — chèn sau bảng cuối của mục tiêu (từ dưới lên để chỉ số không trôi)
    chen: List[Tuple[int, List[Khung]]] = []
    chu_ra = "\n".join(ra)
    for k, vi_tri in cuoi_mt.items():
        if re.search(rf"^\*\*Biểu đồ [^\n]*\(Mục tiêu {k}(?![\d])", chu_ra, re.M):
            continue
        bd_k = [kh for kh in khung_chuan.get(k, []) if kh.loai == "bieu_do"]
        if bd_k:
            chen.append((vi_tri, bd_k))
    for k in range(1, len(ngu.muc_tieu) + 1):
        if k not in cuoi_mt:
            chen.append((len(ra), [kh for kh in khung_chuan.get(k, [])]))
    if nd[1:] and not re.search(r"^\*\*Biểu đồ[^\n]*nhóm nhỏ", chu_ra, re.M):
        chen.append((len(ra), nd[1:]))
    # vẽ theo thứ tự xuất hiện để số biểu đồ tăng dần
    them_theo_vi_tri: Dict[int, List[str]] = {}
    for vi_tri, ds in sorted(chen, key=lambda x: x[0]):
        khoi: List[str] = []
        for kh in ds:
            if kh.loai == "bang":
                dem["Bảng"] += 1
                khoi += [f"**Bảng {so_ch}.{dem['Bảng']}. {kh.ten}**", "", _hang(kh.cot), _hang(["---"] * len(kh.cot))]
                khoi += [_hang(x + [""] * (len(kh.cot) - len(x))) for x in kh.dong] + [""]
                if kh.ghi_chu:
                    khoi += ["*Ghi chú:* " + " ".join(kh.ghi_chu), ""]
            else:
                khoi += _ve(kh, "Hình" if kh.loai == "hinh" else "Biểu đồ")
        them_theo_vi_tri.setdefault(vi_tri, []).extend(khoi)
    kq: List[str] = []
    for n3, dong in enumerate(ra + [None]):
        if n3 in them_theo_vi_tri:
            kq += them_theo_vi_tri[n3]
        if dong is not None:
            kq.append(dong)
    # đánh số lại theo thứ tự xuất hiện (bảng/hình/biểu đồ chèn giữa chừng)
    dem2 = {"Bảng": 0, "Hình": 0, "Biểu đồ": 0}
    so_moi: Dict[str, str] = {}
    for n3, dong in enumerate(kq):
        m = _TIEU_DE_BB.match(dong.strip())
        if m:
            dem2[m.group(1)] += 1
            cu, moi = f"{m.group(1)} {m.group(2)}.{m.group(3)}", f"{m.group(1)} {so_ch}.{dem2[m.group(1)]}"
            so_moi[cu] = moi
            kq[n3] = dong.replace(f"**{cu}.", f"**{moi}.", 1)
    for n3, dong in enumerate(kq):
        if dong.startswith("!["):
            m = re.match(r"^!\[(Hình|Biểu đồ) ([\d.]+)\]", dong)
            if m and f"{m.group(1)} {m.group(2)}" in so_moi:
                kq[n3] = dong.replace(f"[{m.group(1)} {m.group(2)}]", f"[{so_moi[m.group(1) + ' ' + m.group(2)]}]", 1)
    # sơ đồ chọn đối tượng (STROBE/CONSORT: luồng người tham gia trình bày ĐẦU TIÊN) lên ngay sau đoạn mở đầu
    i_h = next((n3 for n3, x in enumerate(kq) if re.match(r"^\*\*Hình \d+\.\d+\.\s.*(?:[Ss]ơ đồ|chọn)", x)), None)
    if i_h is not None:
        dau = i_h
        while dau > 0 and (not kq[dau - 1].strip() or kq[dau - 1].startswith("![")):
            dau -= 1
        cuoi = i_h + 1
        while cuoi < len(kq) and (not kq[cuoi].strip() or kq[cuoi].startswith("*Ghi chú")):
            cuoi += 1
        khoi = kq[dau:cuoi]
        kq = kq[:dau] + kq[cuoi:]
        vt = next((n3 for n3, x in enumerate(kq) if _TIEU_DE_BB.match(x.strip())), len(kq))
        kq = kq[:vt] + khoi + kq[vt:]
        dem3 = {"Hình": 0}
        for n3, x in enumerate(kq):
            m = re.match(r"^(\*\*Hình )\d+\.\d+(\.)", x)
            if m:
                dem3["Hình"] += 1
                kq[n3] = re.sub(r"^\*\*Hình \d+\.\d+\.", f"**Hình {so_ch}.{dem3['Hình']}.", x)
    if not any("Quy ước trình bày" in x for x in kq):
        vt = next((n3 for n3, x in enumerate(kq[1:], 1) if x.strip() and not x.startswith("#")), 1)
        kq.insert(vt + 1, "")
        kq.insert(vt + 2, GIOI_THIEU[GIOI_THIEU.index("Quy ước trình bày"):])
    moi_md = "\n".join(dong_goc[:bd] + kq + dong_goc[bd + len(ch):]) + ("\n" if md.endswith("\n") else "")
    return moi_md, loi_ve


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Khung biểu bảng chuẩn cho chương «Dự kiến kết quả».")
    ap.add_argument("--study", required=True)
    ap.add_argument("--kiem", action="store_true", help="chấm K9 trên đề cương nộp hiện có")
    ap.add_argument("--thay-chuong", action="store_true", help="thay chương «Dự kiến kết quả» của đề cương nộp")
    ap.add_argument("--nang-cap", action="store_true",
                    help="nâng cấp TẠI CHỖ chương «Dự kiến kết quả» soạn tay (giữ bảng của nhóm nghiên cứu)")
    ap.add_argument("--ghi", action="store_true", help="ghi thật (mặc định chỉ in)")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    if not out_dir.is_dir():
        print(f"⛔ không thấy {out_dir}")
        return 3
    md_p = out_dir / f"DE_CUONG_NOP_HOI_DONG_{a.study}.md"
    if a.kiem:
        if not md_p.is_file():
            print(f"⛔ chưa có {md_p.name}")
            return 2
        nc = nap_ngu_canh(out_dir, a.study)
        loi = kiem_bieu_bang(md_p.read_text(encoding="utf-8"), nc.thiet_ke, len(nc.muc_tieu), goc=out_dir)
        print(f"K9 biểu bảng — {a.study}: {'ĐẠT' if not loi else f'{len(loi)} lỗi'}")
        for x in loi:
            print(f"  ✗ {x}")
        print("Cần bác sĩ kiểm chứng.")
        return 0 if not loi else 1
    nc = nap_ngu_canh(out_dir, a.study)
    if not nc.ma_tran:
        print("⛔ chưa có ma trận mục tiêu – biến (_ma-tran-muc-tieu-bien.csv) — không dựng khung được")
        return 2
    if a.nang_cap or a.thay_chuong:
        if not md_p.is_file():
            print(f"⛔ chưa có {md_p.name}")
            return 2
        cu = md_p.read_text(encoding="utf-8")
    if a.nang_cap:
        moi, loi_ve = nang_cap_chuong(cu, nc, out_dir if a.ghi else None, ve_anh=a.ghi)
    else:
        dong, loi_ve, nc = chuong_moi(out_dir, a.study, ve_anh=a.ghi)
        if not a.thay_chuong:
            print("\n".join(dong))
            return 0
        moi = thay_chuong(cu, dong)
    loi = kiem_bieu_bang(moi, nc.thiet_ke, len(nc.muc_tieu), goc=out_dir if a.ghi else None)
    if not a.ghi:
        print(f"(chạy khô) chương mới · K9: {'ĐẠT' if not loi else loi}")
        return 0 if not loi else 1
    if loi_ve:
        print("⚠ không vẽ được: " + "; ".join(loi_ve))
    nhan = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    sao = out_dir / "_sao_luu" / f"{md_p.stem}.truoc-bieu-bang-{nhan}.md"
    sao.parent.mkdir(exist_ok=True)
    shutil.copy2(md_p, sao)
    md_p.write_text(moi, encoding="utf-8", newline="\n")
    print(f"✓ thay chương dự kiến kết quả · sao lưu {sao.relative_to(out_dir)}")
    try:
        import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: PLC0415

        SDC.xuat_word(out_dir, a.study, moi)
        print(f"✓ xuất lại {md_p.with_suffix('.docx').name}")
    except Exception as e:  # noqa: BLE001
        print(f"⚠ chưa xuất lại Word: {type(e).__name__}: {e}")
    print(f"K9: {'ĐẠT' if not loi else loi}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if not loi else 1


if __name__ == "__main__":
    raise SystemExit(main())
