#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bien_phai_sinh.py — BIẾN PHÁI SINH của đề tài: công thức máy đọc được → tính tất định → cùng công thức ở SPSS và R.

Vì sao có tệp này (14/11/2026, soát chuỗi SPSS/R theo yêu cầu bác sĩ): `exports/<mã>/_bien-phai-sinh.csv` đặc tả biến
phái sinh bằng VĂN XUÔI (C1a 12 biến: điểm lĩnh vực A–F, PhieuHopLe…; BTM 23 biến, gồm KẾT CỤC CHÍNH `xn_du`) nhưng
KHÔNG công cụ nào đọc tệp đó, các biến không có trong từ điển G5, và đường nhập Excel/SPSS bỏ qua trường calc ⇒ phân
tích G6 chặn hoặc phải tính tay. Bác sĩ chọn «F1 Biến phái sinh tự động».

Hợp đồng
  • Cột MỚI của `_bien-phai-sinh.csv` (cột cũ giữ nguyên):
      cong_thuc     công thức (ngôn ngữ dưới đây) · bắt đầu bằng «@» = biến tính ở mô-đun khác (vd `@g6_trong_so_survey`
                    cho tầng hậu phân tầng) — công cụ này không tính;
      lap_k         «1-6» ⇒ biến lặp theo chỉ số k: tên `egfr_k` sinh egfr_1…egfr_6, công thức dùng `{k}`;
      nhan_gia_tri  nhãn mã như REDCap «1, G1 | 2, G2»;
      nguoi_duyet   «<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu công thức 12 hex>» — DO THỐNG KÊ VIÊN/PI GHI. Dấu công thức
                    (lệnh `kiem` in ra) gắn lần duyệt với ĐÚNG công thức đó: sửa công thức sau khi duyệt ⇒ hết hiệu lực.
                    Agent KHÔNG BAO GIỜ ghi cột này.
  • Phân tích chính (run_stats_analysis.py) tính biến phái sinh CẦN DÙNG ngay sau khi xác thực dữ liệu khoá — dữ liệu
    khoá không đổi, kết quả tái lập được. Biến cần dùng (kể cả biến nó phụ thuộc) chưa duyệt / duyệt hết hiệu lực ⇒
    DỪNG (đề tài study_kind=synthetic_test: chỉ cảnh báo).
  • Cùng một cây công thức sinh mã SPSS (COMPUTE/DO IF) và R (base R) để hai phần mềm tự tính lại ĐỘC LẬP; lệnh
    `doi-chieu` so từng ô Python ↔ R ↔ SPSS.

Ngôn ngữ công thức — tập con của biểu thức Python, chỉ hàm trong danh sách:
  số, tên cột, + - * / ** , so sánh == != < <= > >= (cho 1/0, thiếu nếu một vế thiếu), and / or / not (logic ba trị
  Kleene: 0 and thiếu = 0; 1 or thiếu = 1), danh sách [a1, a2] (cột) hoặc [7, 8] (số).
    thieu()                            hằng «thiếu» (vd nhánh còn lại của neu)
    neu(dk, a, b)                      dk ≠ 0 ⇒ a, = 0 ⇒ b, thiếu ⇒ thiếu
    bo_ma(x, [998])                    giá trị thuộc danh sách ⇒ thiếu
    la_thieu(x)                        1 nếu thiếu, 0 nếu không (không bao giờ thiếu)
    trong(x, [1, 2, 3])                1/0; thiếu nếu x thiếu
    nhom(x, [40, 60], [1, 2, 3])       x < 40 ⇒ 1 · 40 ≤ x < 60 ⇒ 2 · x ≥ 60 ⇒ 3
    tb_hop_le(ds, hop_le=[1, 5], khong_ap_dung=[7], ty_le_toi_thieu=0.8)
                                       trung bình mục HỢP LỆ trong số mục ÁP DỤNG (mã khong_ap_dung loại khỏi cả tử lẫn
                                       mẫu; trống/ngoài hop_le/mã khác = thiếu); thiếu khi hợp lệ/áp dụng < ngưỡng
    dem(ds, [9], ke_ca_trong=True)     số mục mang mã (± số mục trống)
    dem_co_gt(ds)                      số mục không thiếu
    tat_ca(ds, [9], ke_ca_trong=True)  1 nếu MỌI mục mang mã (± trống)
    co_it_nhat(ds, ">=", 30)           1 nếu có ít nhất một mục thoả (mục thiếu bỏ qua), ngược lại 0
    gt_moi_nhat(ds_gia_tri, ds_ngay)   giá trị ở ngày muộn nhất (trùng ngày ⇒ chỉ số k lớn hơn)
    co_hai_lan(ds_gia_tri, ds_ngay, "<", 60, cach_ngay=90)
                                       1 nếu có HAI mục thoả điều kiện cách nhau ≥ cach_ngay ngày, ngược lại 0
    ckd_epi_2021(scr_mg_dl, tuoi, la_nu)   eGFR CKD-EPI 2021 không hệ số chủng tộc (Inker 2021, PMID 34554658)
    ho("creat_{k}_gt", 1, 6)           danh sách cột creat_1_gt … creat_6_gt
    ngay("2026-07-01")                 hằng ngày
  «Thiếu» = ô trống, chữ (mã thiếu dạng chữ BTR/KDD/KGHS…) hoặc ngày không hợp lệ. Mã SỐ (7/8/9, 998) GIỮ NGUYÊN là số
  — công thức phải xử lý tường minh (bo_ma, tb_hop_le…), không đoán. Cột ngày (Text Validation date_*) tính bằng SỐ
  NGÀY kể từ 01/01/1970 ở cả ba phần mềm.

Lệnh
  kiem      --study <mã> [--json]                 công thức hợp lệ? dấu công thức, trạng thái duyệt, thứ tự phụ thuộc
  tinh      --study <mã> --data <csv> --ra <thư mục NGOÀI repo> [--chi a,b]   tính thử (vd dữ liệu giả lập)
  cu-phap   --study <mã> --dang spss|r [--ra <tệp>]                      mã SPSS/R để đọc/chạy tay
  doi-chieu --study <mã> --data <csv> [--khong-spss] [--khong-r]          Python ↔ R ↔ SPSS từng ô
Mã thoát: 0 đạt · 1 lỗi công thức/lệch · 2 không đo được (thiếu tệp, thiếu SPSS/R) · 3 từ chối (tham số, thư mục ra
trong repo). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TEP_DAC_TA = "_bien-phai-sinh.csv"
TEP_BO_BIEN = "_bo-bien-rieng.csv"
PHIEN_BAN = "1.0.0"
NGAY_GOC = date(1970, 1, 1)
MA_CHU_BAT_DAU = -9991  # PHẢI trùng cau_noi_spss.MA_CHU_BAT_DAU (mã số thay mã thiếu chữ trong .sav) — có test giữ
SAI_SO_TY_LE = 1e-9
PHEP_SS = {"==", "!=", "<", "<=", ">", ">="}
CAN_KIEM = "Cần bác sĩ kiểm chứng."


class LoiCongThuc(ValueError):
    """Công thức không hợp lệ (cú pháp, hàm lạ, cột không có, vòng phụ thuộc…)."""


class TuChoi(RuntimeError):
    """Từ chối chạy (tham số sai, thư mục ra trong repo, biến chưa duyệt…)."""


class KhongDoDuoc(RuntimeError):
    """Thiếu tệp/phần mềm để đo — KHÔNG phải «đạt»."""


# ─────────────────────────────── đặc tả ───────────────────────────────

# Hàm: tham số vị trí theo KIỂU ("bt" biểu thức · "ds" danh sách cột · "so_ds" danh sách số · "so" số · "phep" phép so
# sánh dạng chuỗi) + tham số tên (kiểu, mặc định; mặc định None = bắt buộc nếu ghi «bat_buoc»).
HAM: dict[str, dict] = {
    "thieu": {"vt": [], "kw": {}},
    "neu": {"vt": ["bt", "bt", "bt"], "kw": {}},
    "bo_ma": {"vt": ["bt", "so_ds"], "kw": {}},
    "la_thieu": {"vt": ["bt"], "kw": {}},
    "trong": {"vt": ["bt", "so_ds"], "kw": {}},
    "nhom": {"vt": ["bt", "so_ds", "so_ds"], "kw": {}},
    "tb_hop_le": {
        "vt": ["ds"],
        "kw": {"hop_le": ("so_ds", None), "khong_ap_dung": ("so_ds", []), "ty_le_toi_thieu": ("so", 0.0)},
    },
    "dem": {"vt": ["ds", "so_ds"], "kw": {"ke_ca_trong": ("bool", False)}},
    "dem_co_gt": {"vt": ["ds"], "kw": {}},
    "tat_ca": {"vt": ["ds", "so_ds"], "kw": {"ke_ca_trong": ("bool", False)}},
    "co_it_nhat": {"vt": ["ds", "phep", "so"], "kw": {}},
    "gt_moi_nhat": {"vt": ["ds", "ds"], "kw": {}},
    "co_hai_lan": {"vt": ["ds", "ds", "phep", "so"], "kw": {"cach_ngay": ("so", 90.0)}},
    "ckd_epi_2021": {"vt": ["bt", "bt", "bt"], "kw": {}},
}
PHEP_SO = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Pow: "**"}
PHEP_SS_AST = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}
TEN_COT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass
class BienPS:
    """Một biến phái sinh ĐÃ KHAI TRIỂN (biến lặp k đã thành từng biến)."""

    ten: str
    nhan: str
    kieu: str
    cong_thuc: str  # công thức đã thay {k}
    goc: str  # tên khai ở tệp (vd egfr_k)
    cong_thuc_goc: str
    lap_k: str
    dau: str  # dấu công thức của DÒNG khai (một dấu cho cả họ k)
    nguoi_duyet: str
    nhan_gia_tri: dict[str, str]
    dong: int
    ngoai_tang: bool = False
    cay: dict | None = None
    phu_thuoc: list[str] = field(default_factory=list)
    nguon: list[str] = field(default_factory=list)


def chuan_cong_thuc(s: str) -> str:
    return " ".join((s or "").split())


def dau_cong_thuc(ten: str, cong_thuc: str, lap_k: str) -> str:
    """Dấu 12 hex gắn lần duyệt với ĐÚNG (tên, công thức, lặp k) — đổi một ký tự công thức ⇒ dấu khác."""
    goi = json.dumps([ten.strip(), chuan_cong_thuc(cong_thuc), (lap_k or "").strip()], ensure_ascii=False)
    return hashlib.sha256(goi.encode("utf-8")).hexdigest()[:12]


def trang_thai_duyet(nguoi_duyet: str, dau: str) -> str:
    """CHUA_DUYET · DA_DUYET · HET_HIEU_LUC (dấu khác công thức hiện tại) · SAI_DANG."""
    s = (nguoi_duyet or "").strip()
    if not s:
        return "CHUA_DUYET"
    p = [x.strip() for x in s.split(":")]
    if len(p) != 4 or not all(p) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p[2]) or "[CẦN" in s.upper():
        return "SAI_DANG"
    if not re.fullmatch(r"[0-9a-f]{12}", p[3]):
        return "SAI_DANG"
    return "DA_DUYET" if p[3] == dau else "HET_HIEU_LUC"


def doc_nhan_gia_tri(s: str) -> dict[str, str]:
    kq: dict[str, str] = {}
    for phan in (s or "").split("|"):
        if not phan.strip():
            continue
        if "," not in phan:
            raise LoiCongThuc(f"nhãn giá trị «{phan.strip()}» phải dạng «mã, nhãn»")
        ma, nhan = phan.split(",", 1)
        kq[ma.strip()] = nhan.strip()
    return kq


def _khoang_k(lap_k: str) -> list[int]:
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", lap_k or "")
    if not m or int(m.group(1)) > int(m.group(2)):
        raise LoiCongThuc(f"lap_k «{lap_k}» phải dạng «1-6»")
    return list(range(int(m.group(1)), int(m.group(2)) + 1))


def _ten_k(ten: str, k: int) -> str:
    phan = ten.split("_")
    if "k" not in phan:
        raise LoiCongThuc(f"biến lặp «{ten}» phải có đoạn «_k» trong tên (vd egfr_k)")
    return "_".join(str(k) if p == "k" else p for p in phan)


def _thay_k_ngoai_chuoi(cong_thuc: str, k: int) -> str:
    """Thay {k} ở NGOÀI chuỗi (chuỗi trong ho("…{k}…") giữ nguyên để ho tự khai triển)."""
    phan = re.split(r"(\"[^\"]*\"|'[^']*')", cong_thuc)
    return "".join(p if p[:1] in "\"'" else p.replace("{k}", str(k)) for p in phan)


def doc_dac_ta(study_dir: Path) -> list[BienPS]:
    """Đọc `_bien-phai-sinh.csv` ⇒ danh sách biến đã khai triển. Tệp vắng ⇒ []."""
    p = study_dir / TEP_DAC_TA
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        hang = list(csv.DictReader(f))
    ra: list[BienPS] = []
    for i, r in enumerate(hang, start=2):
        ten = (r.get("ten_bien") or "").strip()
        if not ten:
            continue
        ct = (r.get("cong_thuc") or "").strip()
        lk = (r.get("lap_k") or "").strip()
        dau = dau_cong_thuc(ten, ct, lk)
        try:
            ngt = doc_nhan_gia_tri(r.get("nhan_gia_tri") or "")
        except LoiCongThuc as e:
            raise LoiCongThuc(f"dòng {i} ({ten}): {e}") from e
        chung = dict(
            nhan=(r.get("nhan") or "").strip(),
            kieu=(r.get("kieu") or "").strip(),
            goc=ten,
            cong_thuc_goc=ct,
            lap_k=lk,
            dau=dau,
            nguoi_duyet=(r.get("nguoi_duyet") or "").strip(),
            nhan_gia_tri=ngt,
            dong=i,
            ngoai_tang=ct.startswith("@"),
        )
        if lk and not ct.startswith("@"):
            for k in _khoang_k(lk):
                ra.append(BienPS(ten=_ten_k(ten, k), cong_thuc=_thay_k_ngoai_chuoi(ct, k), **chung))
        else:
            ra.append(BienPS(ten=ten, cong_thuc=ct, **chung))
    ten_ds = [b.ten for b in ra]
    trung = sorted({t for t in ten_ds if ten_ds.count(t) > 1})
    if trung:
        raise LoiCongThuc("tên biến phái sinh trùng: " + ", ".join(trung))
    return ra


# ─────────────────────────────── phân tích cú pháp ───────────────────────────────


def _so_hang(n: ast.AST, ngu_canh: str) -> float:
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
        return float(n.value)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        return -_so_hang(n.operand, ngu_canh)
    raise LoiCongThuc(f"{ngu_canh}: cần một SỐ")


def _ngay_hang(n: ast.Call) -> float:
    a0 = n.args[0] if len(n.args) == 1 else None
    if a0 is None or n.keywords or not isinstance(a0, ast.Constant) or not isinstance(a0.value, str):
        raise LoiCongThuc('ngay(...) cần đúng một chuỗi «YYYY-MM-DD»')
    try:
        d = datetime.strptime(a0.value, "%Y-%m-%d").date()
    except ValueError as e:
        raise LoiCongThuc(f"ngay(\"{a0.value}\") không phải ngày YYYY-MM-DD hợp lệ") from e
    return float((d - NGAY_GOC).days)


def _ds_cot(n: ast.AST) -> list[str]:
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "ho":
        if len(n.args) != 3 or n.keywords:
            raise LoiCongThuc('ho("mau_{k}", tu, den) cần đúng 3 tham số')
        mau = n.args[0]
        if not (isinstance(mau, ast.Constant) and isinstance(mau.value, str) and "{k}" in mau.value):
            raise LoiCongThuc('ho(...): tham số đầu là chuỗi có «{k}»')
        tu, den = int(_so_hang(n.args[1], "ho")), int(_so_hang(n.args[2], "ho"))
        if tu > den:
            raise LoiCongThuc("ho(...): tu > den")
        ds = [mau.value.replace("{k}", str(k)) for k in range(tu, den + 1)]
    elif isinstance(n, ast.List):
        ds = []
        for x in n.elts:
            if not isinstance(x, ast.Name):
                raise LoiCongThuc("danh sách cột chỉ chứa TÊN cột, vd [a1, a2]")
            ds.append(x.id)
    else:
        raise LoiCongThuc("cần danh sách cột: [a1, a2] hoặc ho(\"x_{k}\", 1, 6)")
    if not ds:
        raise LoiCongThuc("danh sách cột rỗng")
    for t in ds:
        if not TEN_COT_RE.match(t):
            raise LoiCongThuc(f"tên cột «{t}» không hợp lệ")
    return ds


def _ds_so(n: ast.AST, ngu_canh: str) -> list[float]:
    if not isinstance(n, ast.List):
        raise LoiCongThuc(f"{ngu_canh}: cần danh sách số, vd [7, 8]")
    return [_so_hang(x, ngu_canh) for x in n.elts]


def _tham_so(kieu: str, n: ast.AST, ten_ham: str) -> object:
    if kieu == "bt":
        return _cay(n)
    if kieu == "ds":
        return _ds_cot(n)
    if kieu == "so_ds":
        return _ds_so(n, ten_ham)
    if kieu == "so":
        return _so_hang(n, ten_ham)
    if kieu == "phep":
        if not (isinstance(n, ast.Constant) and n.value in PHEP_SS):
            raise LoiCongThuc(f'{ten_ham}: phép so sánh phải là một trong {sorted(PHEP_SS)} (dạng chuỗi, vd "<")')
        return n.value
    if kieu == "bool":
        if isinstance(n, ast.Constant) and isinstance(n.value, bool):
            return n.value
        v = _so_hang(n, ten_ham)
        if v not in (0.0, 1.0):
            raise LoiCongThuc(f"{ten_ham}: giá trị đúng/sai là True/False hoặc 1/0")
        return bool(v)
    raise AssertionError(kieu)


def _cay(n: ast.AST) -> dict:
    """AST Python ⇒ cây trung gian (chỉ tập con cho phép)."""
    if isinstance(n, ast.Constant):
        if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
            raise LoiCongThuc(f"hằng «{n.value!r}» không dùng được ở đây (chuỗi chỉ trong ngay/ho/phép so sánh)")
        return {"t": "so", "v": float(n.value)}
    if isinstance(n, ast.Name):
        if not TEN_COT_RE.match(n.id):
            raise LoiCongThuc(f"tên cột «{n.id}» không hợp lệ")
        return {"t": "cot", "ten": n.id}
    if isinstance(n, ast.BinOp) and type(n.op) in PHEP_SO:
        return {"t": "op", "op": PHEP_SO[type(n.op)], "a": _cay(n.left), "b": _cay(n.right)}
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        return {"t": "am", "a": _cay(n.operand)}
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.UAdd):
        return _cay(n.operand)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
        return {"t": "khong", "a": _cay(n.operand)}
    if isinstance(n, ast.BoolOp):
        return {"t": "va" if isinstance(n.op, ast.And) else "hoac", "ds": [_cay(x) for x in n.values]}
    if isinstance(n, ast.Compare):
        if len(n.ops) != 1 or type(n.ops[0]) not in PHEP_SS_AST:
            raise LoiCongThuc("so sánh chỉ một phép mỗi lần (viết a < b and b < c thay cho a < b < c)")
        return {"t": "ss", "op": PHEP_SS_AST[type(n.ops[0])], "a": _cay(n.left), "b": _cay(n.comparators[0])}
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        ten = n.func.id
        if ten == "ngay":
            return {"t": "so", "v": _ngay_hang(n)}
        if ten == "ho":
            raise LoiCongThuc("ho(...) chỉ dùng làm danh sách cột trong một hàm (vd dem_co_gt(ho(\"x_{k}\", 1, 6)))")
        if ten not in HAM:
            raise LoiCongThuc(f"hàm «{ten}» không có trong danh sách cho phép: {', '.join(sorted(HAM))}")
        dt = HAM[ten]
        if len(n.args) != len(dt["vt"]):
            raise LoiCongThuc(f"{ten}(...) cần {len(dt['vt'])} tham số vị trí, nhận {len(n.args)}")
        doi = [_tham_so(k, a, ten) for k, a in zip(dt["vt"], n.args)]
        kw: dict[str, object] = {}
        for k in n.keywords:
            if k.arg not in dt["kw"]:
                raise LoiCongThuc(f"{ten}(...) không có tham số tên «{k.arg}»")
            kw[k.arg] = _tham_so(dt["kw"][k.arg][0], k.value, ten)
        for k, (_kieu, md) in dt["kw"].items():
            kw.setdefault(k, md)
        _kiem_ham(ten, doi, kw)
        return {"t": "ham", "ten": ten, "a": doi, "kw": kw}
    raise LoiCongThuc(f"cấu trúc «{ast.dump(n)[:60]}…» không được phép trong công thức")


def _kiem_ham(ten: str, doi: list, kw: dict) -> None:
    if ten == "nhom":
        cat, nhan = doi[1], doi[2]
        if not cat or any(b <= a for a, b in zip(cat, cat[1:])):
            raise LoiCongThuc("nhom(...): mốc cắt phải tăng dần nghiêm ngặt và không rỗng")
        if len(nhan) != len(cat) + 1:
            raise LoiCongThuc(f"nhom(...): {len(cat)} mốc cắt cần {len(cat) + 1} mã nhóm, nhận {len(nhan)}")
    if ten in ("bo_ma", "trong", "dem", "tat_ca") and not doi[1]:
        raise LoiCongThuc(f"{ten}(...): danh sách mã rỗng")
    if ten == "tb_hop_le":
        hl = kw.get("hop_le")
        if hl is not None and (len(hl) != 2 or hl[0] > hl[1]):
            raise LoiCongThuc("tb_hop_le: hop_le=[thấp, cao]")
        if not 0.0 <= float(kw["ty_le_toi_thieu"]) <= 1.0:
            raise LoiCongThuc("tb_hop_le: ty_le_toi_thieu trong [0, 1]")
    if ten in ("gt_moi_nhat", "co_hai_lan") and len(doi[0]) != len(doi[1]):
        raise LoiCongThuc(f"{ten}(...): danh sách giá trị và danh sách ngày phải dài bằng nhau")
    if ten == "co_hai_lan" and float(kw["cach_ngay"]) < 0:
        raise LoiCongThuc("co_hai_lan: cach_ngay ≥ 0")


def phan_tich(cong_thuc: str) -> dict:
    s = chuan_cong_thuc(cong_thuc)
    if not s:
        raise LoiCongThuc("công thức rỗng")
    if "{k}" in re.sub(r"\"[^\"]*\"|'[^']*'", "", s):
        raise LoiCongThuc("công thức còn «{k}» ngoài ho(...) mà dòng khai không có lap_k")
    try:
        cay = ast.parse(s, mode="eval").body
    except SyntaxError as e:
        raise LoiCongThuc(f"lỗi cú pháp: {e.msg}") from e
    return _cay(cay)


def cot_cua_cay(cay: dict) -> list[str]:
    """Mọi tên cột cây tham chiếu (giữ thứ tự xuất hiện, không trùng)."""
    ra: list[str] = []

    def di(n):
        if isinstance(n, dict):
            if n.get("t") == "cot":
                ra.append(n["ten"])
            for k in ("a", "b"):
                if isinstance(n.get(k), dict):
                    di(n[k])
            for x in n.get("ds", []) if n.get("t") in ("va", "hoac") else []:
                di(x)
            if n.get("t") == "ham":
                dt = HAM[n["ten"]]
                for kieu, x in zip(dt["vt"], n["a"]):
                    if kieu == "bt":
                        di(x)
                    elif kieu == "ds":
                        ra.extend(x)

    di(cay)
    return list(dict.fromkeys(ra))


# ─────────────────────────────── danh mục cột nguồn ───────────────────────────────


@dataclass
class DanhMuc:
    """Cột nguồn có trong dữ liệu + cột nào là NGÀY."""

    cot: set[str]
    ngay: set[str]
    calc: set[str] = field(default_factory=set)
    nguon: str = ""


def doc_danh_muc_tu_dien(study_dir: Path, study: str) -> DanhMuc:
    """Từ điển G5 (nếu có) hoặc `_bo-bien-rieng.csv`: tên cột dữ liệu (checkbox ⇒ <trường>___<mã>), cột ngày, calc."""
    p = study_dir / f"G5_REDCap_dictionary_{study}.csv"
    if not p.exists():
        p = study_dir / TEP_BO_BIEN
    if not p.exists():
        raise KhongDoDuoc(f"không thấy từ điển G5 hay {TEP_BO_BIEN} trong {study_dir}")
    with open(p, encoding="utf-8-sig", newline="") as f:
        hang = list(csv.DictReader(f))
    if not hang:
        raise KhongDoDuoc(f"{p.name} rỗng")
    k = list(hang[0])

    def tim(*mau: str) -> str:
        for c in k:
            if any(m.lower() in c.lower() for m in mau):
                return c
        raise KhongDoDuoc(f"{p.name} thiếu cột {mau[0]}")

    c_ten, c_loai = tim("Variable / Field Name", "Variable"), tim("Field Type")
    c_lc, c_kt = tim("Choices, Calculations", "Choices"), tim("Text Validation Type")
    cot: set[str] = set()
    ngay: set[str] = set()
    calc: set[str] = set()
    for r in hang:
        ten, loai = r[c_ten].strip(), r[c_loai].strip().lower()
        if not ten or loai == "descriptive":
            continue
        if loai == "calc":
            calc.add(ten)
            continue
        if loai == "checkbox":
            for phan in r[c_lc].split("|"):
                if "," in phan:
                    cot.add(f"{ten}___{phan.split(',', 1)[0].strip()}")
            continue
        cot.add(ten)
        if r[c_kt].strip().lower().startswith("date"):
            ngay.add(ten)
    return DanhMuc(cot=cot, ngay=ngay, calc=calc, nguon=p.name)


# ─────────────────────────────── kiểm toàn bộ đặc tả ───────────────────────────────


@dataclass
class KetQuaKiem:
    bien: list[BienPS]
    loi: dict[str, str]
    thu_tu: list[str]
    trang_thai: dict[str, str]


def kiem_dac_ta(bien: list[BienPS], dm: DanhMuc) -> KetQuaKiem:
    """Phân tích mọi công thức, kiểm cột nguồn, phụ thuộc, vòng; trả trạng thái từng biến."""
    loi: dict[str, str] = {}
    # tên trùng cột dữ liệu là LỖI của dòng phái sinh đó — mọi tham chiếu tên ấy hiểu là CỘT DỮ LIỆU (không phụ thuộc
    # vào dòng lỗi): một dòng khai sai không được kéo theo mọi công thức dùng đúng cột dữ liệu
    ten_ps = {b.ten for b in bien if b.ten not in dm.cot}
    for b in bien:
        if b.ten in dm.cot:
            loi[b.ten] = f"tên «{b.ten}» trùng một cột dữ liệu nhập — đổi tên biến phái sinh"
            continue
        if not TEN_COT_RE.match(b.ten) or len(b.ten.encode("utf-8")) > 64:
            loi[b.ten] = "tên biến phải bắt đầu bằng chữ, chỉ chữ/số/_ , ≤ 64 byte (SPSS)"
            continue
        if b.ngoai_tang or not b.cong_thuc.strip():
            continue
        try:
            b.cay = phan_tich(b.cong_thuc)
        except LoiCongThuc as e:
            loi[b.ten] = str(e)
            continue
        ds = cot_cua_cay(b.cay)
        thieu = [c for c in ds if c not in dm.cot and c not in ten_ps]
        if thieu:
            calc = [c for c in thieu if c in dm.calc]
            loi[b.ten] = (
                "cột không có trong dữ liệu nhập: "
                + ", ".join(thieu)
                + (
                    f" ({', '.join(calc)} là trường calc — nhập Excel/SPSS không tính calc; khai thành biến phái sinh)"
                    if calc
                    else ""
                )
            )
            continue
        b.phu_thuoc = [c for c in ds if c in ten_ps]
        b.nguon = [c for c in ds if c not in ten_ps]
    # phụ thuộc vào biến lỗi/chưa có công thức/ngoài tầng
    theo_ten = {b.ten: b for b in bien}
    thay_doi = True
    while thay_doi:
        thay_doi = False
        for b in bien:
            if b.ten in loi or b.cay is None:
                continue
            hong = [
                p
                for p in b.phu_thuoc
                if p in loi or theo_ten[p].cay is None
            ]
            if hong:
                loi[b.ten] = "phụ thuộc biến chưa tính được: " + ", ".join(hong)
                thay_doi = True
    # thứ tự topo + vòng
    thu_tu: list[str] = []
    trang: dict[str, int] = {}

    def tham(t: str, duong: list[str]) -> None:
        if trang.get(t) == 2:
            return
        if trang.get(t) == 1:
            vong = duong[duong.index(t) :] + [t]
            for x in vong:
                loi.setdefault(x, "vòng phụ thuộc: " + " → ".join(vong))
            return
        trang[t] = 1
        for p in theo_ten[t].phu_thuoc:
            tham(p, duong + [t])
        trang[t] = 2
        thu_tu.append(t)

    for b in bien:
        if b.cay is not None and b.ten not in loi:
            tham(b.ten, [])
    thu_tu = [t for t in thu_tu if t not in loi]
    tt: dict[str, str] = {}
    for b in bien:
        if b.ten in loi:
            tt[b.ten] = "LOI"
        elif b.ngoai_tang:
            tt[b.ten] = "NGOAI_TANG"
        elif not b.cong_thuc.strip():
            tt[b.ten] = "CHUA_CO_CONG_THUC"
        else:
            tt[b.ten] = trang_thai_duyet(b.nguoi_duyet, b.dau)
    return KetQuaKiem(bien=bien, loi=loi, thu_tu=thu_tu, trang_thai=tt)


def bao_dong(kq: KetQuaKiem, ten_can: list[str]) -> list[str]:
    """Bao đóng phụ thuộc của các biến cần (theo thứ tự tính)."""
    theo_ten = {b.ten: b for b in kq.bien}
    can: set[str] = set()

    def them(t: str) -> None:
        if t in can:
            return
        can.add(t)
        for p in theo_ten[t].phu_thuoc:
            them(p)

    for t in ten_can:
        if t in theo_ten:
            them(t)
    return [t for t in kq.thu_tu if t in can] + sorted(t for t in can if t not in kq.thu_tu)


# ─────────────────────────────── tính bằng Python ───────────────────────────────


def _np():
    import numpy as np  # noqa: PLC0415

    return np


def _pd():
    import pandas as pd  # noqa: PLC0415

    return pd


def cot_so(df, ten: str, la_ngay: bool):
    """Cột dữ liệu ⇒ số thực (NaN = thiếu). Ngày ISO ⇒ số ngày từ 01/01/1970; chữ/ngày hỏng ⇒ NaN."""
    pd = _pd()
    s = df[ten]
    if la_ngay:
        d = pd.to_datetime(s.astype("string").str.strip(), format="%Y-%m-%d", errors="coerce")
        return ((d - pd.Timestamp(NGAY_GOC)).dt.days).astype("float64")
    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
        return s.astype("float64")
    return pd.to_numeric(s.astype("string").str.strip(), errors="coerce").astype("float64")


def _sach(x):
    np = _np()
    x = x.astype("float64")
    return x.where(np.isfinite(x))


def _dung(x):
    """Giá trị ⇒ logic 1/0/NaN (khác 0 là đúng)."""
    return (x != 0).astype("float64").where(x.notna())


def _ss(a, b, op: str):
    np = _np()
    f = {"==": np.equal, "!=": np.not_equal, "<": np.less, "<=": np.less_equal, ">": np.greater, ">=": np.greater_equal}
    return f[op](a, b).astype("float64").where(a.notna() & b.notna())


def tinh_cay(cay: dict, cot: dict, idx):
    """Tính một cây trên các cột đã chuẩn hoá (dict tên ⇒ Series float, cùng chỉ mục idx). Trả Series float."""
    np, pd = _np(), _pd()
    t = cay["t"]
    if t == "so":
        return pd.Series(cay["v"], index=idx, dtype="float64")
    if t == "cot":
        return cot[cay["ten"]]
    if t == "op":
        a, b = tinh_cay(cay["a"], cot, idx), tinh_cay(cay["b"], cot, idx)
        with np.errstate(all="ignore"):
            if cay["op"] == "+":
                r = a + b
            elif cay["op"] == "-":
                r = a - b
            elif cay["op"] == "*":
                r = a * b
            elif cay["op"] == "/":
                r = a / b.where(b != 0)
            else:
                r = a**b
        return _sach(r)
    if t == "am":
        return -tinh_cay(cay["a"], cot, idx)
    if t == "ss":
        return _ss(tinh_cay(cay["a"], cot, idx), tinh_cay(cay["b"], cot, idx), cay["op"])
    if t == "khong":
        d = _dung(tinh_cay(cay["a"], cot, idx))
        return (1.0 - d).where(d.notna())
    if t in ("va", "hoac"):
        ds = [_dung(tinh_cay(x, cot, idx)) for x in cay["ds"]]
        m = pd.concat(ds, axis=1)
        if t == "va":
            r = pd.Series(1.0, index=idx)
            r[m.isna().any(axis=1)] = np.nan
            r[(m == 0).any(axis=1)] = 0.0
        else:
            r = pd.Series(0.0, index=idx)
            r[m.isna().any(axis=1)] = np.nan
            r[(m == 1).any(axis=1)] = 1.0
        return r
    if t == "ham":
        return _ham_py(cay, cot, idx)
    raise AssertionError(t)


def _ma_tran(cot: dict, ds: list[str]):
    pd = _pd()
    return pd.concat([cot[c].rename(c) for c in ds], axis=1)


def _ham_py(cay: dict, cot: dict, idx):
    np, pd = _np(), _pd()
    ten, a, kw = cay["ten"], cay["a"], cay["kw"]
    if ten == "thieu":
        return pd.Series(np.nan, index=idx, dtype="float64")
    if ten == "neu":
        dk = _dung(tinh_cay(a[0], cot, idx))
        x, y = tinh_cay(a[1], cot, idx), tinh_cay(a[2], cot, idx)
        return pd.Series(np.where(dk == 1, x, y), index=idx, dtype="float64").where(dk.notna())
    if ten == "bo_ma":
        x = tinh_cay(a[0], cot, idx)
        return x.where(~x.isin(a[1]))
    if ten == "la_thieu":
        return tinh_cay(a[0], cot, idx).isna().astype("float64")
    if ten == "trong":
        x = tinh_cay(a[0], cot, idx)
        return x.isin(a[1]).astype("float64").where(x.notna())
    if ten == "nhom":
        x = tinh_cay(a[0], cot, idx)
        cat, nhan = a[1], a[2]
        r = pd.Series(np.nan, index=idx, dtype="float64")
        r[x < cat[0]] = nhan[0]
        for i in range(1, len(cat)):
            r[(x >= cat[i - 1]) & (x < cat[i])] = nhan[i]
        r[x >= cat[-1]] = nhan[-1]
        return r.where(x.notna())
    if ten == "tb_hop_le":
        m = _ma_tran(cot, a[0])
        kad = list(kw.get("khong_ap_dung") or [])
        ap = ~m.isin(kad) if kad else pd.DataFrame(True, index=m.index, columns=m.columns)
        hl = kw.get("hop_le")
        hop = m.notna() & ap & ((m >= hl[0]) & (m <= hl[1]) if hl else True)
        na, nv = ap.sum(axis=1).astype("float64"), hop.sum(axis=1).astype("float64")
        tong = m.where(hop).sum(axis=1, min_count=1)
        ty = float(kw["ty_le_toi_thieu"])
        ok = (na > 0) & (nv > 0) & (nv - ty * na >= -SAI_SO_TY_LE)
        return (tong / nv).where(ok)
    if ten in ("dem", "tat_ca"):
        m = _ma_tran(cot, a[0])
        dung = m.isin(a[1])
        if kw.get("ke_ca_trong"):
            dung = dung | m.isna()
        d = dung.sum(axis=1).astype("float64")
        return d if ten == "dem" else (d == len(a[0])).astype("float64")
    if ten == "dem_co_gt":
        return _ma_tran(cot, a[0]).notna().sum(axis=1).astype("float64")
    if ten == "co_it_nhat":
        m = _ma_tran(cot, a[0])
        f = {"==": m.eq, "!=": m.ne, "<": m.lt, "<=": m.le, ">": m.gt, ">=": m.ge}[a[1]]
        return (f(a[2]) & m.notna()).any(axis=1).astype("float64")
    if ten == "gt_moi_nhat":
        g, d = _ma_tran(cot, a[0]), _ma_tran(cot, a[1])
        r = pd.Series(np.nan, index=idx, dtype="float64")
        tot = pd.Series(np.nan, index=idx, dtype="float64")
        for i in range(len(a[0])):
            gi, di = g.iloc[:, i], d.iloc[:, i]
            chon = gi.notna() & di.notna() & (tot.isna() | (di >= tot))
            r[chon], tot[chon] = gi[chon], di[chon]
        return r
    if ten == "co_hai_lan":
        g, d = _ma_tran(cot, a[0]), _ma_tran(cot, a[1])
        f = {"==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}[a[2]]
        # mảng numpy: hai DataFrame khác TÊN cột (egfr_k · creat_k_ngay) mà «&» thì pandas căn theo nhãn ⇒ toàn False
        gv, dv = g.to_numpy(dtype="float64"), d.to_numpy(dtype="float64")
        with np.errstate(invalid="ignore"):
            thoa = getattr(np, {"eq": "equal", "ne": "not_equal", "lt": "less", "le": "less_equal", "gt": "greater",
                                "ge": "greater_equal"}[f])(gv, a[3]) & ~np.isnan(gv) & ~np.isnan(dv)  # fmt: skip
        r = np.zeros(len(idx))
        k = len(a[0])
        for i in range(k):
            for j in range(i + 1, k):
                with np.errstate(invalid="ignore"):
                    ok = thoa[:, i] & thoa[:, j] & (np.abs(dv[:, i] - dv[:, j]) >= kw["cach_ngay"])
                r[ok] = 1.0
        return pd.Series(r, index=idx, dtype="float64")
    if ten == "ckd_epi_2021":
        scr, tuoi, nu = (tinh_cay(x, cot, idx) for x in a)
        nu1 = (nu != 0).astype("float64").where(nu.notna())
        kap = 0.9 - 0.2 * nu1
        alp = -0.302 + 0.061 * nu1
        hs = 1 + 0.012 * nu1
        q = scr / kap
        with np.errstate(all="ignore"):
            r = 142 * np.minimum(q, 1.0) ** alp * np.maximum(q, 1.0) ** (-1.2) * 0.9938**tuoi * hs
        return _sach(pd.Series(r, index=idx))
    raise AssertionError(ten)


def tinh_df(df, kq: KetQuaKiem, dm: DanhMuc, ten_can: list[str] | None = None):
    """Tính biến phái sinh (ten_can + phụ thuộc; None = mọi biến tính được) ⇒ DataFrame các cột mới (float)."""
    pd = _pd()
    theo_ten = {b.ten: b for b in kq.bien}
    ds = bao_dong(kq, ten_can) if ten_can is not None else list(kq.thu_tu)
    hong = [t for t in ds if kq.trang_thai.get(t) in ("LOI", "CHUA_CO_CONG_THUC", "NGOAI_TANG")]
    if hong:
        raise TuChoi("không tính được: " + "; ".join(f"{t} ({kq.trang_thai[t]}: {kq.loi.get(t, '')})" for t in hong))
    nguon = list(dict.fromkeys(c for t in ds for c in theo_ten[t].nguon))
    vang = [c for c in nguon if c not in df.columns]
    if vang:
        raise TuChoi("dữ liệu thiếu cột nguồn: " + ", ".join(vang))
    cot = {c: cot_so(df, c, c in dm.ngay) for c in nguon}
    ra = pd.DataFrame(index=df.index)
    for t in ds:
        v = tinh_cay(theo_ten[t].cay, cot, df.index)
        cot[t] = v
        ra[t] = v
    return ra


# ─────────────────────────────── sinh mã SPSS ───────────────────────────────


def so_spss(v: float) -> str:
    """Số in cho cú pháp (không dùng ký hiệu mũ)."""
    if float(v).is_integer():
        return str(int(v))
    s = format(v, ".15g")
    if "e" in s or "E" in s:
        s = f"{v:.20f}".rstrip("0").rstrip(".")
    return s


class SinhSpss:
    """Sinh lệnh SPSS. `ten_spss` = {cột CSV: (tên SPSS, là biến số trong .sav)}; cột ngày (chuỗi ISO) ⇒ số ngày."""

    TIEN_TO = "ebm_bps_"

    def __init__(self, ten_spss: dict[str, tuple[str, bool]], ngay: set[str], dang_co: set[str]):
        self.ten_spss = ten_spss
        self.ngay = ngay
        self.dang_co = {x.upper() for x in dang_co}
        self.dong: list[str] = []
        self.so_tam = 0
        self.tam: list[str] = []
        self.nguon: dict[str, str] = {}

    def _tam(self) -> str:
        while True:
            self.so_tam += 1
            t = f"{self.TIEN_TO}{self.so_tam}"
            if t.upper() not in self.dang_co:
                self.tam.append(t)
                return t

    def chuan_bi_nguon(self, cot: str) -> str:
        if cot in self.nguon:
            return self.nguon[cot]
        ten, la_so = self.ten_spss.get(cot, (cot, cot not in self.ngay))  # xuat-sav giữ ngày ISO dạng CHUỖI
        t = self._tam()
        if cot in self.ngay:
            doc = f"VALUE({ten})" if la_so else f"NUMBER({ten}, SDATE10)"
            self.dong.append(f"COMPUTE {t} = ({doc} - DATE.DMY(1,1,1970)) / 86400.")
        elif la_so:
            self.dong.append(f"COMPUTE {t} = VALUE({ten}).")
            self.dong.append(f"IF ({t} <= {MA_CHU_BAT_DAU}) {t} = $SYSMIS.")
        else:
            # F40.0: KHÔNG dùng F40.10 — định dạng nhập F hiểu chữ số thập phân ngầm («5» ⇒ 0,0000000005)
            self.dong.append(f"COMPUTE {t} = NUMBER(LTRIM(RTRIM({ten})), F40.0).")
        self.nguon[cot] = t
        return t

    def bt(self, n: dict, ps: set[str]) -> str:
        t = n["t"]
        if t == "so":
            return so_spss(n["v"]) if n["v"] >= 0 else f"({so_spss(n['v'])})"
        if t == "cot":
            return n["ten"] if n["ten"] in ps else self.chuan_bi_nguon(n["ten"])
        if t == "op":
            op = n["op"]
            return f"({self.bt(n['a'], ps)} {op} {self.bt(n['b'], ps)})"
        if t == "am":
            return f"(-{self.bt(n['a'], ps)})"
        if t == "ss":
            op = {"==": "=", "!=": "<>"}.get(n["op"], n["op"])
            return f"({self.bt(n['a'], ps)} {op} {self.bt(n['b'], ps)})"
        if t == "khong":
            return f"(NOT ({self.bt(n['a'], ps)} <> 0))"
        if t in ("va", "hoac"):
            noi = " AND " if t == "va" else " OR "
            return "(" + noi.join(f"({self.bt(x, ps)} <> 0)" for x in n["ds"]) + ")"
        if t == "ham":
            return self.ham(n, ps)
        raise AssertionError(t)

    def _ds(self, ds: list[str], ps: set[str]) -> list[str]:
        return [c if c in ps else self.chuan_bi_nguon(c) for c in ds]

    def ham(self, n: dict, ps: set[str]) -> str:
        ten, a, kw = n["ten"], n["a"], n["kw"]
        d = self.dong
        if ten == "thieu":
            return "$SYSMIS"
        if ten == "neu":
            dk, x, y = self.bt(a[0], ps), self.bt(a[1], ps), self.bt(a[2], ps)
            t = self._tam()
            d += [f"COMPUTE {t} = $SYSMIS.", f"DO IF ({dk} <> 0).", f"  COMPUTE {t} = {x}.", "ELSE.",
                  f"  COMPUTE {t} = {y}.", "END IF."]  # fmt: skip
            return t
        if ten == "bo_ma":
            x = self.bt(a[0], ps)
            t = self._tam()
            d += [f"COMPUTE {t} = {x}.", f"IF (ANY({t}, {', '.join(so_spss(v) for v in a[1])})) {t} = $SYSMIS."]
            return t
        if ten == "la_thieu":
            return f"SYSMIS({self.bt(a[0], ps)})"
        if ten == "trong":
            return f"ANY({self.bt(a[0], ps)}, {', '.join(so_spss(v) for v in a[1])})"
        if ten == "nhom":
            x = self.bt(a[0], ps)
            cat, nhan = a[1], a[2]
            t = self._tam()
            d.append(f"COMPUTE {t} = $SYSMIS.")
            d.append(f"IF ({x} < {so_spss(cat[0])}) {t} = {so_spss(nhan[0])}.")
            for i in range(1, len(cat)):
                d.append(f"IF ({x} >= {so_spss(cat[i - 1])} AND {x} < {so_spss(cat[i])}) {t} = {so_spss(nhan[i])}.")
            d.append(f"IF ({x} >= {so_spss(cat[-1])}) {t} = {so_spss(nhan[-1])}.")
            return t
        if ten == "tb_hop_le":
            ds = self._ds(a[0], ps)
            na, nv, tong, t = self._tam(), self._tam(), self._tam(), self._tam()
            kad = list(kw.get("khong_ap_dung") or [])
            hl = kw.get("hop_le")
            d += [f"COMPUTE {na} = 0.", f"COMPUTE {nv} = 0.", f"COMPUTE {tong} = 0."]
            for c in ds:
                ap = f"(SYSMIS({c}) OR NOT ANY({c}, {', '.join(so_spss(v) for v in kad)}))" if kad else ""
                hop = f"NOT SYSMIS({c})"
                if kad:
                    hop += f" AND NOT ANY({c}, {', '.join(so_spss(v) for v in kad)})"
                if hl:
                    hop += f" AND {c} >= {so_spss(hl[0])} AND {c} <= {so_spss(hl[1])}"
                d.append(f"IF ({ap}) {na} = {na} + 1." if ap else f"COMPUTE {na} = {na} + 1.")
                d.append(f"DO IF ({hop}).")
                d.append(f"  COMPUTE {nv} = {nv} + 1.")
                d.append(f"  COMPUTE {tong} = {tong} + {c}.")
                d.append("END IF.")
            ty = so_spss(float(kw["ty_le_toi_thieu"]))
            d.append(f"COMPUTE {t} = $SYSMIS.")
            d.append(f"IF ({na} > 0 AND {nv} > 0 AND {nv} - {ty} * {na} >= -0.000000001) {t} = {tong} / {nv}.")
            return t
        if ten in ("dem", "tat_ca"):
            ds = self._ds(a[0], ps)
            t = self._tam()
            d.append(f"COMPUTE {t} = 0.")
            for c in ds:
                dk = f"ANY({c}, {', '.join(so_spss(v) for v in a[1])})"
                if kw.get("ke_ca_trong"):
                    dk = f"SYSMIS({c}) OR {dk}"
                d.append(f"IF ({dk}) {t} = {t} + 1.")
            return t if ten == "dem" else f"({t} = {len(ds)})"
        if ten == "dem_co_gt":
            ds = self._ds(a[0], ps)
            t = self._tam()
            d.append(f"COMPUTE {t} = 0.")
            d += [f"IF (NOT SYSMIS({c})) {t} = {t} + 1." for c in ds]
            return t
        if ten == "co_it_nhat":
            ds = self._ds(a[0], ps)
            op = {"==": "=", "!=": "<>"}.get(a[1], a[1])
            t = self._tam()
            d.append(f"COMPUTE {t} = 0.")
            d += [f"IF ({c} {op} {so_spss(a[2])}) {t} = 1." for c in ds]
            return t
        if ten == "gt_moi_nhat":
            g, ng = self._ds(a[0], ps), self._ds(a[1], ps)
            t, tot = self._tam(), self._tam()
            d += [f"COMPUTE {t} = $SYSMIS.", f"COMPUTE {tot} = $SYSMIS."]
            for gi, di in zip(g, ng):
                d += [f"DO IF (NOT SYSMIS({gi}) AND NOT SYSMIS({di})).",
                      f"  DO IF (SYSMIS({tot}) OR {di} >= {tot}).",
                      f"    COMPUTE {tot} = {di}.", f"    COMPUTE {t} = {gi}.", "  END IF.", "END IF."]  # fmt: skip
            return t
        if ten == "co_hai_lan":
            g, ng = self._ds(a[0], ps), self._ds(a[1], ps)
            op = {"==": "=", "!=": "<>"}.get(a[2], a[2])
            nguong, cach = so_spss(a[3]), so_spss(float(kw["cach_ngay"]))
            t = self._tam()
            d.append(f"COMPUTE {t} = 0.")
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    d.append(
                        f"IF ({g[i]} {op} {nguong} AND {g[j]} {op} {nguong} AND ABS({ng[i]} - {ng[j]}) >= {cach}) "
                        f"{t} = 1."
                    )
            return t
        if ten == "ckd_epi_2021":
            scr, tuoi, nu = (self.bt(x, ps) for x in a)
            nu1, q, t = self._tam(), self._tam(), self._tam()
            d += [f"COMPUTE {nu1} = $SYSMIS.", f"IF (NOT SYSMIS({nu})) {nu1} = ({nu} <> 0).",
                  f"COMPUTE {q} = {scr} / (0.9 - 0.2 * {nu1}).", f"COMPUTE {t} = $SYSMIS.",
                  f"IF (NOT SYSMIS({q}) AND NOT SYSMIS({tuoi})) {t} = 142 * MIN.2({q}, 1) ** (-0.302 + 0.061 * {nu1})"
                  f" * MAX.2({q}, 1) ** (-1.2) * 0.9938 ** {tuoi} * (1 + 0.012 * {nu1})."]  # fmt: skip
            return t
        raise AssertionError(ten)


def _chu_thich_spss(cong_thuc: str) -> str:
    """Công thức trong dòng chú thích SPSS: bỏ nháy (nháy lẻ làm hỏng phân tích cú pháp), tối đa 180 ký tự."""
    return re.sub(r"[\"']", "", chuan_cong_thuc(cong_thuc))[:180]


def cu_phap_spss(
    kq: KetQuaKiem,
    ten_can: list[str] | None,
    *,
    ten_spss: dict[str, tuple[str, bool]] | None = None,
    ngay: set[str] | None = None,
    dang_co: set[str] | None = None,
    nhan: bool = True,
) -> tuple[str, list[str]]:
    """Khối lệnh SPSS tính biến phái sinh (ten_can + phụ thuộc). Trả (cú pháp, danh sách biến tạo ra)."""
    theo_ten = {b.ten: b for b in kq.bien}
    ds = bao_dong(kq, ten_can) if ten_can is not None else list(kq.thu_tu)
    s = SinhSpss(ten_spss or {}, ngay or set(), (dang_co or set()) | set(ds))
    da: set[str] = set()
    for t in ds:
        b = theo_ten[t]
        s.dong.append(f"* {t} = {_chu_thich_spss(b.cong_thuc)}.")
        bt = s.bt(b.cay, da)
        s.dong.append(f"COMPUTE {t} = {bt}.")
        da.add(t)
    dong = [f"* Biến phái sinh — sinh từ {TEP_DAC_TA} bởi tools/bien_phai_sinh.py {PHIEN_BAN}. {CAN_KIEM}"]
    dong += s.dong
    dong.append("EXECUTE.")
    if s.tam:
        dong.append("DELETE VARIABLES " + " ".join(s.tam) + ".")
    if nhan:
        for t in ds:
            b = theo_ten[t]
            if b.nhan:
                dong.append(f"VARIABLE LABELS {t} '{b.nhan[:250].replace(chr(39), chr(39) * 2)}'.")
            if b.nhan_gia_tri:
                cap = " ".join(f"{k} '{v.replace(chr(39), chr(39) * 2)}'" for k, v in b.nhan_gia_tri.items())
                dong.append(f"VALUE LABELS {t} {cap}.")
    return "\n".join(dong) + "\n", ds


# ─────────────────────────────── sinh mã R ───────────────────────────────

R_HAM = r"""
.bps_so <- function(x) suppressWarnings(as.numeric(trimws(as.character(x))))
.bps_ngay <- function(x) { x <- trimws(as.character(x)); ok <- !is.na(x) & grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", x)
  r <- rep(NA_real_, length(x)); r[ok] <- as.numeric(as.Date(x[ok], format = "%Y-%m-%d")); r }
.bps_sach <- function(x) { x <- as.numeric(x); x[!is.finite(x)] <- NA_real_; x }
.bps_dung <- function(x) ifelse(is.na(x), NA, x != 0)
.bps_chia <- function(a, b) { r <- a / b; z <- rep_len(b, length(r)); r[!is.na(z) & z == 0] <- NA_real_
  .bps_sach(r) }  # KHÔNG dùng ifelse: kết quả dài bằng điều kiện ⇒ mẫu số hằng làm cả cột thành một giá trị
.bps_ss <- function(a, b, op) { r <- switch(op, "==" = a == b, "!=" = a != b, "<" = a < b, "<=" = a <= b,
  ">" = a > b, ">=" = a >= b); as.numeric(r) }
.bps_neu <- function(dk, a, b) { d <- .bps_dung(dk); r <- ifelse(d, a, b); as.numeric(r) }
.bps_nhom <- function(x, cat, nhan) { r <- rep(NA_real_, length(x)); ok <- !is.na(x)
  r[ok] <- nhan[findInterval(x[ok], cat) + 1]; r }
.bps_tb <- function(ds, lo, hi, kad, ty) { m <- do.call(cbind, ds)
  ap <- if (length(kad)) !(m %in% kad) else rep(TRUE, length(m)); dim(ap) <- dim(m)
  hop <- !is.na(m) & ap; if (!is.null(lo)) hop <- hop & !is.na(m) & m >= lo & m <= hi; hop[is.na(hop)] <- FALSE
  na <- rowSums(ap); nv <- rowSums(hop); tong <- rowSums(ifelse(hop, m, 0))
  r <- ifelse(na > 0 & nv > 0 & (nv - ty * na) >= -1e-9, tong / nv, NA_real_); as.numeric(r) }
.bps_dem <- function(ds, ma, trong) Reduce(`+`, lapply(ds, function(v) as.numeric((!is.na(v) & v %in% ma) |
  (trong & is.na(v)))))
.bps_co_gt <- function(ds) Reduce(`+`, lapply(ds, function(v) as.numeric(!is.na(v))))
.bps_it_nhat <- function(ds, op, ng) { r <- rep(0, length(ds[[1]])); for (v in ds) { o <- .bps_ss(v, ng, op)
  r[!is.na(o) & o == 1] <- 1 }; r }
.bps_moi_nhat <- function(g, d) { r <- rep(NA_real_, length(g[[1]])); tot <- rep(NA_real_, length(g[[1]]))
  for (i in seq_along(g)) { chon <- !is.na(g[[i]]) & !is.na(d[[i]]) & (is.na(tot) | d[[i]] >= tot)
    r[chon] <- g[[i]][chon]; tot[chon] <- d[[i]][chon] }; r }
.bps_hai_lan <- function(g, d, op, ng, cach) { r <- rep(0, length(g[[1]])); k <- length(g)
  if (k >= 2) for (i in 1:(k - 1)) for (j in (i + 1):k) { oi <- .bps_ss(g[[i]], ng, op); oj <- .bps_ss(g[[j]], ng, op)
    ok <- !is.na(oi) & oi == 1 & !is.na(oj) & oj == 1 & !is.na(d[[i]]) & !is.na(d[[j]]) & abs(d[[i]] - d[[j]]) >= cach
    r[ok] <- 1 }; r }
.bps_ckd <- function(scr, tuoi, nu) { nu1 <- ifelse(is.na(nu), NA_real_, as.numeric(nu != 0))
  q <- scr / (0.9 - 0.2 * nu1)
  .bps_sach(142 * pmin(q, 1)^(-0.302 + 0.061 * nu1) * pmax(q, 1)^(-1.2) * 0.9938^tuoi * (1 + 0.012 * nu1)) }
"""


def _so_r(v: float) -> str:
    return repr(float(v)) if not float(v).is_integer() else f"{int(v)}"


def _vec_r(vs) -> str:
    return "c(" + ", ".join(_so_r(v) for v in vs) + ")"


class SinhR:
    def __init__(self, ngay: set[str], bien_d: str = "d"):
        self.ngay = ngay
        self.d = bien_d
        self.nguon: dict[str, str] = {}
        self.chuan_bi: list[str] = []

    def cot(self, c: str, ps: set[str]) -> str:
        if c in ps:
            return f"{self.d}[[{json.dumps(c)}]]"
        if c not in self.nguon:
            ham = ".bps_ngay" if c in self.ngay else ".bps_so"
            self.nguon[c] = f".n[[{json.dumps(c)}]]"
            self.chuan_bi.append(f".n[[{json.dumps(c)}]] <- {ham}({self.d}[[{json.dumps(c)}]])")
        return self.nguon[c]

    def ds(self, ds: list[str], ps: set[str]) -> str:
        return "list(" + ", ".join(self.cot(c, ps) for c in ds) + ")"

    def bt(self, n: dict, ps: set[str]) -> str:
        t = n["t"]
        if t == "so":
            return _so_r(n["v"])
        if t == "cot":
            return self.cot(n["ten"], ps)
        if t == "op":
            a, b = self.bt(n["a"], ps), self.bt(n["b"], ps)
            if n["op"] == "/":
                return f".bps_chia({a}, {b})"
            return f".bps_sach(({a}) {'^' if n['op'] == '**' else n['op']} ({b}))"
        if t == "am":
            return f"(-({self.bt(n['a'], ps)}))"
        if t == "ss":
            return f".bps_ss({self.bt(n['a'], ps)}, {self.bt(n['b'], ps)}, {json.dumps(n['op'])})"
        if t == "khong":
            return f"as.numeric(!.bps_dung({self.bt(n['a'], ps)}))"
        if t in ("va", "hoac"):
            noi = " & " if t == "va" else " | "
            return "as.numeric(" + noi.join(f".bps_dung({self.bt(x, ps)})" for x in n["ds"]) + ")"
        if t == "ham":
            ten, a, kw = n["ten"], n["a"], n["kw"]
            if ten == "thieu":
                return "NA_real_"
            if ten == "neu":
                return f".bps_neu({self.bt(a[0], ps)}, {self.bt(a[1], ps)}, {self.bt(a[2], ps)})"
            if ten == "bo_ma":
                x = self.bt(a[0], ps)
                return f"(function(x) {{ x[!is.na(x) & x %in% {_vec_r(a[1])}] <- NA_real_; x }})({x})"
            if ten == "la_thieu":
                return f"as.numeric(is.na({self.bt(a[0], ps)}))"
            if ten == "trong":
                x = self.bt(a[0], ps)
                return f"(function(x) ifelse(is.na(x), NA_real_, as.numeric(x %in% {_vec_r(a[1])})))({x})"
            if ten == "nhom":
                return f".bps_nhom({self.bt(a[0], ps)}, {_vec_r(a[1])}, {_vec_r(a[2])})"
            if ten == "tb_hop_le":
                hl = kw.get("hop_le")
                lo, hi = (_so_r(hl[0]), _so_r(hl[1])) if hl else ("NULL", "NULL")
                kad = _vec_r(kw.get("khong_ap_dung") or []) if kw.get("khong_ap_dung") else "numeric(0)"
                return f".bps_tb({self.ds(a[0], ps)}, {lo}, {hi}, {kad}, {_so_r(float(kw['ty_le_toi_thieu']))})"
            if ten in ("dem", "tat_ca"):
                tr = "TRUE" if kw.get("ke_ca_trong") else "FALSE"
                e = f".bps_dem({self.ds(a[0], ps)}, {_vec_r(a[1])}, {tr})"
                return e if ten == "dem" else f"as.numeric({e} == {len(a[0])})"
            if ten == "dem_co_gt":
                return f".bps_co_gt({self.ds(a[0], ps)})"
            if ten == "co_it_nhat":
                return f".bps_it_nhat({self.ds(a[0], ps)}, {json.dumps(a[1])}, {_so_r(a[2])})"
            if ten == "gt_moi_nhat":
                return f".bps_moi_nhat({self.ds(a[0], ps)}, {self.ds(a[1], ps)})"
            if ten == "co_hai_lan":
                return (f".bps_hai_lan({self.ds(a[0], ps)}, {self.ds(a[1], ps)}, {json.dumps(a[2])}, {_so_r(a[3])}, "
                        f"{_so_r(float(kw['cach_ngay']))})")  # fmt: skip
            if ten == "ckd_epi_2021":
                return f".bps_ckd({self.bt(a[0], ps)}, {self.bt(a[1], ps)}, {self.bt(a[2], ps)})"
        raise AssertionError(n)


def ma_r(
    kq: KetQuaKiem, ten_can: list[str] | None, *, ngay: set[str] | None = None, bien_d: str = "d"
) -> tuple[str, list[str]]:
    """Mã R (base R) tính biến phái sinh vào data.frame `d` (cột đọc dạng chữ). Trả (mã, danh sách biến)."""
    theo_ten = {b.ten: b for b in kq.bien}
    ds = bao_dong(kq, ten_can) if ten_can is not None else list(kq.thu_tu)
    s = SinhR(ngay or set(), bien_d)
    than: list[str] = []
    da: set[str] = set()
    for t in ds:
        bt = s.bt(theo_ten[t].cay, da)
        than.append(f"# {t} = {chuan_cong_thuc(theo_ten[t].cong_thuc)[:180]}")
        than.append(f"{bien_d}[[{json.dumps(t)}]] <- as.numeric({bt})")
        da.add(t)
    dong = [f"# Biến phái sinh — sinh từ {TEP_DAC_TA} bởi tools/bien_phai_sinh.py {PHIEN_BAN}. {CAN_KIEM}"]
    dong += [R_HAM.strip(), ".n <- list()", *s.chuan_bi, *than]
    return "\n".join(dong) + "\n", ds


# ─────────────────────────────── dùng trong phân tích chính ───────────────────────────────


def la_de_tai_gia_lap(study_dir: Path) -> bool:
    try:
        m = json.loads((study_dir / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(m, dict) and m.get("study_kind") == "synthetic_test"


def doan_cot_ngay(df) -> set[str]:
    """Không có từ điển: cột mà MỌI ô có giá trị đều dạng YYYY-MM-DD (và có ít nhất một ô) là cột ngày."""
    ra: set[str] = set()
    for c in df.columns:
        v = df[c].dropna().astype(str).str.strip()
        v = v[v != ""]
        if len(v) and v.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
            ra.add(c)
    return ra


def ap_dung_cho_phan_tich(df, study_dir: Path, study: str, ten_can: list[str]):
    """Gọi từ run_stats_analysis.py SAU khi đã xác thực dữ liệu khoá. Biến cần mà dữ liệu không có nhưng có trong
    `_bien-phai-sinh.csv` ⇒ tính (kèm phụ thuộc) và thêm cột. Trả (df, thông tin cho G6_analysis_summary) — thông tin
    None khi không có biến phái sinh nào được dùng. Biến dùng tới chưa duyệt/duyệt hết hiệu lực ⇒ TuChoi (giả lập: cảnh
    báo)."""
    can = [t for t in dict.fromkeys(x for x in ten_can if x) if t not in df.columns]
    if not can or not (study_dir / TEP_DAC_TA).exists():
        return df, None
    bien = doc_dac_ta(study_dir)
    theo_ten = {b.ten: b for b in bien}
    can = [t for t in can if t in theo_ten]
    if not can:
        return df, None
    try:
        dm = doc_danh_muc_tu_dien(study_dir, study)
        dm.cot |= set(df.columns)
    except KhongDoDuoc:
        dm = DanhMuc(cot=set(df.columns), ngay=doan_cot_ngay(df), nguon="cột dữ liệu (không có từ điển — ngày ĐOÁN)")
    kq = kiem_dac_ta(bien, dm)
    ds = bao_dong(kq, can)
    gia_lap = la_de_tai_gia_lap(study_dir)
    chua = [t for t in ds if kq.trang_thai.get(t) != "DA_DUYET"]
    if [t for t in ds if kq.trang_thai.get(t) in ("LOI", "CHUA_CO_CONG_THUC", "NGOAI_TANG")]:
        tinh_df(df, kq, dm, can)  # ném TuChoi kèm lý do cụ thể
    canh_bao: list[str] = []
    if chua:
        ly_do = "; ".join(f"{t}: {kq.trang_thai[t]}" for t in chua)
        if not gia_lap:
            raise TuChoi(
                "biến phái sinh dùng trong phân tích chưa được THỐNG KÊ VIÊN/PI duyệt công thức (" + ly_do + ") — "
                "chạy `python tools/bien_phai_sinh.py kiem --study " + study + "`, người duyệt ghi cột nguoi_duyet "
                "kèm dấu công thức"
            )
        canh_bao.append("ĐỀ TÀI GIẢ LẬP — dùng công thức CHƯA DUYỆT: " + ly_do)
    moi = tinh_df(df, kq, dm, can)
    df2 = df.copy()
    for c in moi.columns:
        df2[c] = moi[c]
    p = study_dir / TEP_DAC_TA
    info = {
        "tep": TEP_DAC_TA,
        "sha256_tep": hashlib.sha256(p.read_bytes()).hexdigest(),
        "phien_ban_bo_may": PHIEN_BAN,
        "danh_muc": dm.nguon,
        "bien": {
            t: {
                "cong_thuc": chuan_cong_thuc(theo_ten[t].cong_thuc),
                "dau": theo_ten[t].dau,
                "duyet": kq.trang_thai[t],
                "nguoi_duyet": theo_ten[t].nguoi_duyet,
                "so_co_gia_tri": int(moi[t].notna().sum()),
            }
            for t in ds
        },
        "cot_ngay": sorted({c for t in ds for c in theo_ten[t].nguon if c in dm.ngay}),
        "canh_bao": canh_bao,
    }
    return df2, info


def khoi_cho_cau_noi(
    study_dir: Path,
    tom: dict,
    dang: str,
    csv_khoa: Path,
    *,
    ten_spss: dict[str, tuple[str, bool]] | None = None,
    dang_co: set[str] | None = None,
    bien_d: str = "D",
) -> tuple[str, list[str], dict[str, list[str] | None]]:
    """Cầu nối SPSS/R: khối mã tính lại ĐỘC LẬP đúng các biến phái sinh lượt Python đã dùng (khoá `bien_phai_sinh` của
    G6_analysis_summary.json), trên CÙNG danh sách cột ngày. Trả (mã, danh sách biến, mức giá trị từng biến — để cầu nối
    nhận diện nhị phân/liên tục như với biến trong .sav). Lượt Python không dùng biến phái sinh ⇒ ("", [], {}).
    Công thức hiện tại khác DẤU đã dùng ở lượt Python ⇒ TuChoi (chạy lại phân tích chính trước)."""
    info = (tom or {}).get("bien_phai_sinh") or {}
    da_dung = info.get("bien") or {}
    ds = list(da_dung)
    if not ds:
        return "", [], {}
    bien = doc_dac_ta(study_dir)
    theo_ten = {b.ten: b for b in bien}
    lech = [t for t in ds if t not in theo_ten or theo_ten[t].dau != (da_dung[t] or {}).get("dau")]
    if lech:
        raise TuChoi(
            "công thức biến phái sinh đã ĐỔI sau lượt phân tích Python (" + ", ".join(lech) + ") — chạy lại "
            "run_stats_analysis.py rồi mới kiểm chéo"
        )
    df = _doc_csv_chu(csv_khoa)
    dm = DanhMuc(cot=set(df.columns), ngay=set(info.get("cot_ngay") or []), nguon="cột dữ liệu khoá + cột ngày đã dùng")
    kq = kiem_dac_ta(bien, dm)
    moi = tinh_df(df, kq, dm, ds)  # ném TuChoi nếu công thức không còn tính được
    if dang == "spss":
        ma, _ = cu_phap_spss(kq, ds, ten_spss=ten_spss, ngay=dm.ngay, dang_co=dang_co)
    elif dang == "r":
        ma, _ = ma_r(kq, ds, ngay=dm.ngay, bien_d=bien_d)
    else:
        raise ValueError(dang)
    muc: dict[str, list[str] | None] = {}
    for t in ds:
        v = sorted(set(moi[t].dropna().tolist()))
        muc[t] = [format(x, "g") for x in v] if len(v) <= 20 else None
    return ma, ds, muc


# ─────────────────────────────── dòng lệnh ───────────────────────────────


def _study_dir(study: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", study or ""):
        raise TuChoi(f"mã đề tài không hợp lệ: {study!r}")
    d = BASE / "exports" / study
    if not d.is_dir():
        raise TuChoi(f"không có thư mục đề tài exports/{study}")
    return d


def _nap(study: str) -> tuple[Path, list[BienPS], DanhMuc, KetQuaKiem]:
    d = _study_dir(study)
    if not (d / TEP_DAC_TA).exists():
        raise KhongDoDuoc(f"đề tài chưa có {TEP_DAC_TA}")
    bien = doc_dac_ta(d)
    dm = doc_danh_muc_tu_dien(d, study)
    return d, bien, dm, kiem_dac_ta(bien, dm)


def lenh_kiem(args) -> int:
    d, bien, dm, kq = _nap(args.study)
    dong: dict[str, dict] = {}
    for b in bien:
        g = dong.setdefault(b.goc, {"ten": b.goc, "lap_k": b.lap_k, "dau": b.dau, "dong": b.dong,
                                    "trang_thai": set(), "loi": []})  # fmt: skip
        g["trang_thai"].add(kq.trang_thai[b.ten])
        if b.ten in kq.loi:
            g["loi"].append(f"{b.ten}: {kq.loi[b.ten]}")
    dem: dict[str, int] = {}
    for b in bien:
        dem[kq.trang_thai[b.ten]] = dem.get(kq.trang_thai[b.ten], 0) + 1
    if args.json:
        print(json.dumps({"study": args.study, "danh_muc": dm.nguon, "dem": dem, "thu_tu": kq.thu_tu,
                          "bien": [{**v, "trang_thai": sorted(v["trang_thai"])} for v in dong.values()]},
                         ensure_ascii=False, indent=1))  # fmt: skip
    else:
        print(f"Biến phái sinh — {args.study} (danh mục cột: {dm.nguon})")
        for v in dong.values():
            tt = "/".join(sorted(v["trang_thai"]))
            print(f"  {v['ten']:24} {tt:20} dấu {v['dau']}" + (f"  lặp k={v['lap_k']}" if v["lap_k"] else ""))
            for loi in v["loi"][:3]:
                print(f"      ✗ {loi}")
        print("Tổng: " + ", ".join(f"{k} {n}" for k, n in sorted(dem.items())))
        print("Người duyệt ghi cột nguoi_duyet: «<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu>» (agent không ghi). " + CAN_KIEM)
    return 1 if kq.loi else 0


def _trong_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(BASE.resolve())
        return True
    except ValueError:
        return False


def _doc_csv_chu(p: Path):
    pd = _pd()
    return pd.read_csv(p, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")


def lenh_tinh(args) -> int:
    d, bien, dm, kq = _nap(args.study)
    data = Path(args.data).expanduser()
    if not data.exists():
        raise KhongDoDuoc(f"không thấy {data}")
    ra = Path(args.ra).expanduser()
    if _trong_repo(ra):
        raise TuChoi("thư mục ra phải NGOÀI repo (dữ liệu chưa qua cổng tiếp nhận không vào cây git)")
    ra.mkdir(parents=True, exist_ok=True)
    df = _doc_csv_chu(data)
    can = [x.strip() for x in args.chi.split(",") if x.strip()] if args.chi else None
    moi = tinh_df(df, kq, dm, can)
    out = df.copy()
    for c in moi.columns:
        out[c] = moi[c]
    tep = ra / f"{data.stem}_phai_sinh.csv"
    out.to_csv(tep, index=False, encoding="utf-8")
    tom = {c: {"co_gia_tri": int(moi[c].notna().sum()), "thieu": int(moi[c].isna().sum()),
               "duyet": kq.trang_thai[c]} for c in moi.columns}  # fmt: skip
    (ra / f"{data.stem}_phai_sinh_bao_cao.json").write_text(
        json.dumps({"study": args.study, "nguon": str(data), "bien": tom, "phien_ban": PHIEN_BAN}, ensure_ascii=False,
                   indent=1), encoding="utf-8", newline="\n")  # fmt: skip
    print(f"✓ {len(moi.columns)} biến phái sinh · {len(df)} ca ⇒ {tep}")
    chua = [c for c in moi.columns if kq.trang_thai[c] != "DA_DUYET"]
    if chua:
        print(f"  ⚠ {len(chua)} biến CHƯA DUYỆT công thức — chỉ dùng thử, không dùng cho phân tích chính")
    print(CAN_KIEM)
    return 0


def lenh_cu_phap(args) -> int:
    d, bien, dm, kq = _nap(args.study)
    can = [x.strip() for x in args.chi.split(",") if x.strip()] if args.chi else None
    if args.dang == "spss":
        ma, _ = cu_phap_spss(kq, can, ngay=dm.ngay)
    else:
        ma, _ = ma_r(kq, can, ngay=dm.ngay)
    if args.ra:
        Path(args.ra).write_text(ma, encoding="utf-8", newline="\n")
        print(f"✓ {args.ra}")
    else:
        print(ma)
    return 1 if kq.loi else 0


# ── đối chiếu Python ↔ R ↔ SPSS ──


def _khop(a: float, b: float) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    if math.isnan(a) or math.isnan(b):
        return False
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def so_tung_o(py, khac, ten: str) -> dict:
    """So cột Python với cột của phần mềm khác (cùng thứ tự ca). Trả {so_o, so_lech, vi_du}."""
    lech = []
    for i, (a, b) in enumerate(zip(py.tolist(), khac.tolist())):
        a = float("nan") if a is None else float(a)
        b = float("nan") if b is None else float(b)
        if not _khop(a, b):
            lech.append({"ca": i + 1, "python": None if math.isnan(a) else a, ten: None if math.isnan(b) else b})
    return {"so_o": len(py), "so_lech": len(lech), "vi_du": lech[:5]}


def chay_r(kq: KetQuaKiem, ds: list[str], data: Path, dm: DanhMuc, thu_muc: Path) -> "object":
    """Chạy mã R sinh ra trên CSV (đọc mọi cột dạng chữ) ⇒ DataFrame các cột phái sinh."""
    rs = _tim_rscript()
    ma, _ = ma_r(kq, ds, ngay=dm.ngay)
    ra = thu_muc / "r_ra.csv"
    script = thu_muc / "bps.R"
    script.write_text(
        f'd <- read.csv({json.dumps(str(data))}, colClasses = "character", na.strings = "", check.names = FALSE, '
        'fileEncoding = "UTF-8-BOM")\n'
        + ma
        + f"o <- d[, {_vec_chu_r(ds)}, drop = FALSE]\n"
        + f'write.csv(format(o, digits = 17), {json.dumps(str(ra))}, row.names = FALSE, na = "")\n',
        encoding="utf-8",
        newline="\n",
    )
    k = subprocess.run([rs, "--vanilla", str(script)], capture_output=True, text=True, timeout=600,
                       stdin=subprocess.DEVNULL, check=False)  # fmt: skip
    if k.returncode != 0:
        raise RuntimeError("R lỗi: " + (k.stderr or k.stdout)[-800:])
    pd = _pd()
    o = pd.read_csv(ra, dtype=str, keep_default_na=False, na_values=["", "NA"])
    return o.apply(lambda c: pd.to_numeric(c.str.strip(), errors="coerce"))


def _vec_chu_r(ds: list[str]) -> str:
    return "c(" + ", ".join(json.dumps(x) for x in ds) + ")"


def _tim_rscript() -> str:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import cau_noi_r  # noqa: PLC0415

        return str(cau_noi_r.tim_r())
    except Exception as e:  # noqa: BLE001 — mọi lỗi tìm R ⇒ không đo được
        raise KhongDoDuoc(f"không tìm thấy Rscript ({e})") from e


def chay_spss_doi_chieu(kq: KetQuaKiem, ds: list[str], data: Path, study_dir: Path, study: str, thu_muc: Path):
    """Dựng .sav tạm từ CSV bằng ĐÚNG kế hoạch biến của cầu nối SPSS, chạy mã SPSS sinh ra ⇒ DataFrame phái sinh."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cau_noi_spss as S  # noqa: PLC0415

    try:
        py = S.tim_spss()
    except Exception as e:  # noqa: BLE001
        raise KhongDoDuoc(str(e)) from e
    td_p = study_dir / f"G5_REDCap_dictionary_{study}.csv"
    if not td_p.exists():
        td_p = study_dir / TEP_BO_BIEN
    mt_p = study_dir / "_ma-thieu-theo-bien.csv"
    td, mt = S.doc_tu_dien(td_p), S.doc_ma_thieu(mt_p if mt_p.exists() else None)
    tieu_de, tk, _n = S.quet_csv(data)
    ke, _cb, _dx = S.ke_hoach_bien(tieu_de, tk, td, mt)
    data_tam = thu_muc / "du_lieu.csv"
    data_tam.write_bytes(data.read_bytes())  # đường dẫn NGẮN: SPSS lỗi khi đường dẫn tệp dài (~255 byte)
    data = data_tam
    sav = thu_muc / "tam.sav"
    nhan_bien = S.cu_phap_nhan_bien(data, sav, ke, ghi_chu=["đối chiếu biến phái sinh — tệp tạm"])
    ten_spss = {b["cot"]: (b["ten"], bool(b["so"])) for b in ke if not b["bo"]}
    dm = doc_danh_muc_tu_dien(study_dir, study)
    ma, _ = cu_phap_spss(kq, ds, ten_spss=ten_spss, ngay=dm.ngay, dang_co={b["ten"] for b in ke}, nhan=False)
    ra = thu_muc / "spss_ra.csv"
    sps = thu_muc / "bps.sps"
    sps.write_text(
        nhan_bien
        + f"\nGET FILE={S.dd_spss(sav)}.\n"
        + ma
        + f"FORMATS {' '.join(ds)} (F40.16).\nSET DECIMAL=DOT.\n"
        + f"SAVE TRANSLATE OUTFILE={S.dd_spss(ra)} /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
        f"/KEEP={' '.join(ds)}.\n",
        encoding="utf-8",
        newline="\n",
    )
    ma_t, out, err = S.chay_spss(py, ["--cu-phap", str(sps)], thu_muc=thu_muc, thoi_han=1200)
    if ma_t != 0 or not ra.exists():
        raise RuntimeError("SPSS lỗi: " + (err or out)[-1200:])
    pd = _pd()
    o = pd.read_csv(ra, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
    o.columns = [c.strip() for c in o.columns]
    theo_hoa = {c.upper(): c for c in o.columns}
    o = o[[theo_hoa[t.upper()] for t in ds]]
    o.columns = ds
    return o.apply(lambda c: pd.to_numeric(c.str.strip().str.replace(",", ".", regex=False), errors="coerce"))


def _spss_vung_ngan(kq: KetQuaKiem, ds: list[str], data: Path, study_dir: Path, study: str):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import cau_noi_spss as S  # noqa: PLC0415

    with S.vung_tam() as tam:
        return chay_spss_doi_chieu(kq, ds, data, study_dir, study, Path(tam))


def lenh_doi_chieu(args) -> int:
    d, bien, dm, kq = _nap(args.study)
    data = Path(args.data).expanduser().resolve()
    if not data.exists():
        raise KhongDoDuoc(f"không thấy {data}")
    can = [x.strip() for x in args.chi.split(",") if x.strip()] if args.chi else None
    df = _doc_csv_chu(data)
    py = tinh_df(df, kq, dm, can)
    ds = list(py.columns)
    bao: dict[str, dict] = {"python": {"so_bien": len(ds), "so_ca": len(df)}}
    ma = 0
    with tempfile.TemporaryDirectory(prefix="ebm-bps-") as tam:
        tam_p = Path(tam)
        viec = [
            ("r", not args.khong_r, lambda: chay_r(kq, ds, data, dm, tam_p)),
            ("spss", not args.khong_spss, lambda: _spss_vung_ngan(kq, ds, data, d, args.study)),
        ]
        for ten, bat, ham in viec:
            if not bat:
                bao[ten] = {"trang_thai": "BO_QUA"}
                continue
            try:
                kq_k = ham()
            except KhongDoDuoc as e:
                bao[ten] = {"trang_thai": "KHONG_DO_DUOC", "ly_do": str(e)}
                ma = max(ma, 2)
                continue
            except (RuntimeError, OSError, subprocess.TimeoutExpired, KeyError) as e:
                bao[ten] = {"trang_thai": "LOI", "ly_do": str(e)[-1500:]}
                ma = 1
                continue
            theo = {c: so_tung_o(py[c], kq_k[c], ten) for c in ds}
            so_lech = sum(v["so_lech"] for v in theo.values())
            bao[ten] = {"trang_thai": "KHOP" if not so_lech else "LECH", "so_lech": so_lech,
                        "bien": {c: v for c, v in theo.items() if v["so_lech"]}}  # fmt: skip
            if so_lech:
                ma = 1
    print(json.dumps({"study": args.study, "du_lieu": data.name, "bien": ds, "ket_qua": bao}, ensure_ascii=False,
                     indent=1))  # fmt: skip
    print(("✓ Python = R = SPSS từng ô" if ma == 0 else "✗ Có lệch / không đo được — xem trên") + f". {CAN_KIEM}")
    return ma


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Biến phái sinh: kiểm công thức, tính, sinh mã SPSS/R, đối chiếu.")
    sp = ap.add_subparsers(dest="lenh", required=True)
    k = sp.add_parser("kiem")
    k.add_argument("--study", required=True)
    k.add_argument("--json", action="store_true")
    t = sp.add_parser("tinh")
    t.add_argument("--study", required=True)
    t.add_argument("--data", required=True)
    t.add_argument("--ra", required=True)
    t.add_argument("--chi", default="")
    c = sp.add_parser("cu-phap")
    c.add_argument("--study", required=True)
    c.add_argument("--dang", choices=["spss", "r"], required=True)
    c.add_argument("--ra", default="")
    c.add_argument("--chi", default="")
    dc = sp.add_parser("doi-chieu")
    dc.add_argument("--study", required=True)
    dc.add_argument("--data", required=True)
    dc.add_argument("--chi", default="")
    dc.add_argument("--khong-spss", action="store_true")
    dc.add_argument("--khong-r", action="store_true")
    args = ap.parse_args(argv)
    try:
        return {"kiem": lenh_kiem, "tinh": lenh_tinh, "cu-phap": lenh_cu_phap, "doi-chieu": lenh_doi_chieu}[args.lenh](
            args
        )
    except LoiCongThuc as e:
        print(f"✗ Công thức: {e}", file=sys.stderr)
        return 1
    except KhongDoDuoc as e:
        print(f"⚪ Không đo được: {e}", file=sys.stderr)
        return 2
    except TuChoi as e:
        print(f"✗ Từ chối: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
