#!/usr/bin/env python3
"""Cầu nối IBM SPSS Statistics ↔ hệ nghiên cứu G5–G6.

Bác sĩ giao 14/11/2026: «xây dựng kết nối với SPSS giúp tôi một cách tốt nhất».

SPSS chạy ở CHẾ ĐỘ NỀN (external mode của Python đi kèm SPSS — không mở giao diện, không cần bấm). Công cụ luôn sinh cú
pháp `.sps` đọc được, chạy tay được trong SPSS ở bất kỳ máy nào; máy có SPSS thì chạy luôn qua `tools/spss_chay_nen.py`.

Sáu lệnh:
  kiem        Tìm SPSS, phiên bản, chạy thử một lệnh (giấy phép), liệt kê mô-đun được cấp phép.
  xuat-sav    Bộ dữ liệu ĐÃ KHOÁ (manifest khoá, đối chiếu SHA-256) + từ điển REDCap G5 + mã thiếu cấp dự án
              ⇒ `exports/<mã>/spss/<mã>_nhan_bien.sps` + `<mã>_khoa.sav` (nhãn biến · nhãn giá trị · mức đo ·
              MISSING VALUES · tên theo «Tên SPSS: …» trong Field Annotation) + manifest.
  cu-phap     Cú pháp phân tích `<mã>_phan_tich.sps` khớp ĐẶC TẢ của run_stats_analysis.py (khoá `dac_ta_phan_tich`
              trong G6_analysis_summary.json, hoặc --outcome/--group/… như lệnh đó): Bảng 1, kết cục chính, mô hình đa
              biến (logistic · tuyến tính · thứ tự), hiệu chỉnh cụm (GENLIN robust), sống còn (Cox + Kaplan–Meier).
              Mọi bảng ghi qua OMS (OXML) + một tệp `.spv` mở được trong SPSS.
  chay        Chạy cú pháp phân tích trong SPSS ⇒ `spss/ket_qua/*.xml`, `.spv`, nhật ký, `G6_spss_ket_qua.json`.
  doi-chieu   So ước lượng SPSS với kết quả Python (G6_analysis_summary.json) ⇒ `G6_spss_doi_chieu.json/.md`.
  nhap-sav    Tệp .sav của bác sĩ ⇒ CSV + từ điển nhãn (JSON) ở thư mục NGOÀI repo, quét tên cột nghi PII, rồi in lệnh
              nhập chuẩn `import_real_dataset.py` (cổng tiếp nhận vẫn là công cụ đó).

RANH GIỚI (CLAUDE.md §1.1): SPSS là phần mềm KIỂM CHÉO — chủ G6 vẫn là `run_stats_analysis.py`. Công cụ này không đổi
trạng thái cổng, không ký, không ghi study_meta/approval_ledger; dữ liệu không PII (biến «Identifier?=y» ⇒ từ chối).

Đo thật 14/11/2026 trên SPSS 31.0.1 (Mac): logistic, OLS, OR thô, t-test khớp statsmodels/scipy tới 6 chữ số; hồi quy
thứ tự lệch KTC ~0,3% (statsmodels lấy SE từ Hessian xấp xỉ); Cox của SPSS xử lý thời điểm trùng bằng Breslow
(lifelines dùng Efron).

Mã thoát: 0 xong/khớp · 1 lệch hoặc SPSS lỗi · 2 không đo được (máy không có SPSS, thiếu tệp đầu vào) · 3 từ chối (PII,
dữ liệu không khớp manifest khoá, tham số sai). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import plistlib
import re
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows cp1252 (BH55/R4)
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
EXPORTS = BASE / "exports"
TRINH_CHAY = Path(__file__).resolve().parent / "spss_chay_nen.py"
MA_OK, MA_LECH, MA_KHONG_DO, MA_TU_CHOI = 0, 1, 2, 3
CAN_KIEM = "Cần bác sĩ kiểm chứng."
TU_KHOA_SPSS = {"ALL", "AND", "BY", "EQ", "GE", "GT", "LE", "LT", "NE", "NOT", "OR", "TO", "WITH"}
MA_CHU_BAT_DAU = -9991  # mã số thay cho mã thiếu dạng CHỮ (BTR, KDD…) trong biến số — xem _ke_hoach_bien
TRAN_NHAN_BIEN, TRAN_NHAN_GIA_TRI = 255, 120  # byte UTF-8 (giới hạn SPSS)
TRAN_MUC_LIET_KE = 20


class TuChoi(Exception):
    """Điều kiện chặn (mã 3): PII, dữ liệu không khớp manifest khoá, tham số sai."""


class KhongDoDuoc(Exception):
    """Không đo được (mã 2): thiếu SPSS hoặc thiếu tệp đầu vào — không phải «đạt»."""


# ───────────────────────────── tiện ích ─────────────────────────────


def sha256_tep(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def cat_byte(s: str, tran: int) -> str:
    """Cắt chuỗi theo số byte UTF-8, không cắt giữa một ký tự."""
    b = s.encode("utf-8")
    if len(b) <= tran:
        return s
    return b[:tran].decode("utf-8", errors="ignore").rstrip()


def chuoi_spss(s: str, tran_dong: int = 100) -> str:
    """Chuỗi trích dẫn SPSS ('…', nháy đơn nhân đôi), tách thành nhiều đoạn nối bằng «+» để không dòng nào quá dài."""
    s = re.sub(r"\s+", " ", str(s)).strip()
    doan, cur = [], ""
    for ch in s:
        if len((cur + ch).encode("utf-8")) > tran_dong:
            doan.append(cur)
            cur = ""
        cur += ch
    doan.append(cur)
    return " +\n    ".join("'" + d.replace("'", "''") + "'" for d in doan)


def bo_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def ten_hop_le(ten: str) -> bool:
    return (
        bool(re.fullmatch(r"[A-Za-z@#$][A-Za-z0-9_.@#$]*", ten))
        and not ten.endswith(".")
        and ten.upper() not in TU_KHOA_SPSS
        and len(ten.encode("utf-8")) <= 64
    )


def chuan_ten(ten: str) -> str:
    t = re.sub(r"[^A-Za-z0-9_.@#$]", "_", ten).rstrip(".")
    if not t or not re.match(r"[A-Za-z@#$]", t):
        t = "v_" + t
    if t.upper() in TU_KHOA_SPSS:
        t += "_"
    return cat_byte(t, 64)


def _so(s: str) -> float | None:
    try:
        x = float(s)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _doc_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def thu_muc_de_tai(study: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", study or ""):
        raise TuChoi(f"mã đề tài không hợp lệ: {study!r}")
    return EXPORTS / study


# ───────────────────────────── tìm và chạy SPSS ─────────────────────────────


def ung_vien_python_spss(thu_muc_ung_dung: Path = Path("/Applications")) -> list[Path]:
    """Python ĐI KÈM SPSS (có gói `spss`). Biến môi trường EBM_SPSS_PYTHON thắng mọi dò tìm."""
    env = os.environ.get("EBM_SPSS_PYTHON", "").strip()
    if env:
        return [Path(env)]
    ra: list[Path] = []
    if sys.platform == "darwin":
        for goc in sorted(thu_muc_ung_dung.glob("IBM SPSS Statistics*"), reverse=True):
            # Dùng `python3.13`, KHÔNG dùng `python3`: ở SPSS 31.0.1 `python3` liên kết libintl theo đường Homebrew
            # /usr/local/opt/gettext (đo 14/11/2026: dyld «Library not loaded»), còn `python3.X` dùng @executable_path.
            bin_ = goc / "Resources" / "Python3" / "bin"
            ds = [p for p in bin_.glob("python3.*") if re.fullmatch(r"python3\.\d+", p.name)]
            ra += sorted(ds, key=lambda p: int(p.name.split(".")[1]), reverse=True)
    elif os.name == "nt":
        for pf in {os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramW6432", "")}:
            if not pf:
                continue
            ra.append(Path(pf) / "IBM" / "SPSS Statistics" / "Python3" / "python.exe")
            ra += sorted(Path(pf, "IBM", "SPSS", "Statistics").glob("*/Python3/python.exe"), reverse=True)
    return [p for p in ra if p.is_file()]


def phien_ban_tu_goi(py: Path) -> str | None:
    """Phiên bản SPSS đọc từ Info.plist của gói ứng dụng (Mac). Windows: None (lấy từ lượt chạy)."""
    try:
        goc = py.resolve().parents[3]
    except IndexError:
        return None
    for app in goc.glob("*.app/Contents/Info.plist"):
        try:
            d = plistlib.loads(app.read_bytes())
        except (OSError, ValueError, plistlib.InvalidFileException):
            continue
        # gói ứng dụng chính — gói «Python3 for SPSS Statistics» cũng mang id com.ibm.spss…
        if d.get("CFBundleExecutable") == "stats":
            return str(d.get("CFBundleShortVersionString") or "") or None
    return None


def chay_spss(py: Path, doi_so: list[str], *, thu_muc: Path, thoi_han: int = 1200) -> tuple[int, str, str]:
    """Chạy trình nền bằng Python của SPSS. Trả (mã, stdout, stderr). Không nuốt timeout: báo mã 1 kèm lý do."""
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")}
    try:
        r = subprocess.run(
            [str(py), "-I", str(TRINH_CHAY), *doi_so],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=thoi_han,
            env=env,
            cwd=str(thu_muc),
        )
    except subprocess.TimeoutExpired:
        return 1, "", f"LOI_SPSS quá thời hạn {thoi_han} giây"
    except OSError as e:
        return 1, "", f"LOI_SPSS không chạy được Python của SPSS: {e}"
    return r.returncode, r.stdout, r.stderr


def tim_spss() -> Path:
    ds = ung_vien_python_spss()
    if not ds:
        raise KhongDoDuoc(
            "không tìm thấy Python đi kèm IBM SPSS Statistics (Mac: /Applications/IBM SPSS Statistics/Resources/"
            "Python3/bin/python3.X · Windows: C:\\Program Files\\IBM\\SPSS Statistics\\Python3\\python.exe) — "
            "đặt EBM_SPSS_PYTHON nếu cài chỗ khác; cú pháp .sps vẫn sinh được để chạy tay trong SPSS"
        )
    return ds[0]


def _gia_tri_dong(out: str, khoa: str) -> str | None:
    for dong in out.splitlines():
        if dong.startswith(khoa + "="):
            return dong.split("=", 1)[1].strip()
    return None


def phang_oxml(tep: Path) -> list[dict]:
    """Mọi bảng của một tệp OXML ⇒ [{bang (subType), tieu_de, o: [{hang: [...], cot: [...], so, chu}]}]."""
    goc = ET.parse(tep).getroot()
    ns = goc.tag.split("}")[0] + "}" if goc.tag.startswith("{") else ""
    ra = []
    for pt in goc.iter(ns + "pivotTable"):
        cha = {c: p for p in pt.iter() for c in p}

        def truc(e):
            p = cha.get(e)
            while p is not None and p.tag != ns + "dimension":
                p = cha.get(p)
            return p.get("axis") if p is not None else None

        o: list[dict] = []

        def di(e, hang, cot):
            for c in e:
                if c.tag == ns + "cell":
                    o.append({"hang": hang, "cot": cot, "so": _so(c.get("number")), "chu": c.get("text")})
                elif c.tag in (ns + "category", ns + "group"):
                    t = c.get("text") or ""
                    ax = truc(c)
                    di(c, hang + [t] if ax == "row" else hang, cot + [t] if ax == "column" else cot)
                else:
                    di(c, hang, cot)

        di(pt, [], [])
        ra.append({"bang": pt.get("subType") or "", "tieu_de": pt.get("text") or "", "o": o})
    return ra


def _chuan_bang(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


# ───────────────────────────── lệnh kiem ─────────────────────────────


def lenh_kiem(_args) -> int:
    try:
        py = tim_spss()
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO
    print(f"• Python của SPSS: {py}")
    pb = phien_ban_tu_goi(py)
    if pb:
        print(f"• Phiên bản (gói ứng dụng): {pb}")
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ebm-spss-kiem-") as tam:
        xml = Path(tam) / "giay_phep.xml"
        ma, out, err = chay_spss(py, ["--kiem", str(xml)], thu_muc=Path(tam), thoi_han=300)
        if ma != 0 or not xml.exists():
            print("🔴 SPSS không chạy được ở chế độ nền:", (err or out).strip()[-600:])
            return MA_LECH
        print(f"• Phiên bản (lõi SPSS): {_gia_tri_dong(out, 'PHIEN_BAN') or '?'}")
        mo_dun = []
        for b in phang_oxml(xml):
            for x in b["o"]:
                if x["hang"] and x["cot"] and "Expiration" in " ".join(x["cot"]):
                    mo_dun.append((x["hang"][0], x["chu"]))
        for ten, han in dict(mo_dun).items():
            print(f"  ✓ {ten} — hạn {han}")
        can = {
            "IBM SPSS Statistics": "lõi (CROSSTABS, T-TEST, MEANS, UNIANOVA)",
            "IBM SPSS Regression": "LOGISTIC REGRESSION, PLUM",
            "IBM SPSS Advanced Statistics": "COXREG, KM, GENLIN",
        }
        thieu = [f"{k} ({v})" for k, v in can.items() if k not in dict(mo_dun)]
        if thieu:
            print("⚠ Chưa thấy giấy phép:", "; ".join(thieu), "— lệnh dùng mô-đun đó sẽ báo lỗi khi chạy")
    print("✓ SPSS sẵn sàng cho cầu nối (chế độ nền).")
    return MA_OK


# ───────────────────────────── từ điển, mã thiếu, kế hoạch biến ─────────────────────────────

_TEN_COT_TD = {
    "ten": ("Variable / Field Name", "field_name"),
    "loai": ("Field Type", "field_type"),
    "nhan": ("Field Label", "field_label"),
    "lua_chon": ("Choices, Calculations, OR Slider Labels", "select_choices_or_calculations"),
    "kiem_tra": ("Text Validation Type OR Show Slider Number", "text_validation_type_or_show_slider_number"),
    "dinh_danh": ("Identifier?", "identifier"),
    "chu_thich": ("Field Annotation", "field_annotation"),
}


def doc_tu_dien(p: Path) -> dict[str, dict]:
    """Từ điển REDCap (G5) ⇒ {tên_trường: {...}}; chấp nhận cả tiêu đề cột dạng hiển thị lẫn dạng API."""
    with open(p, encoding="utf-8-sig", newline="") as f:
        dr = csv.DictReader(f)
        tieu_de = dr.fieldnames or []
        cot = {k: next((t for t in tieu_de if t in v), None) for k, v in _TEN_COT_TD.items()}
        if not cot["ten"]:
            raise TuChoi(f"{p.name}: không thấy cột tên trường (Variable / Field Name)")
        ra = {}
        for r in dr:
            ten = (r.get(cot["ten"]) or "").strip()
            if ten:
                ra[ten] = {k: (r.get(c) or "").strip() if c else "" for k, c in cot.items()}
    return ra


def lua_chon(td: dict) -> dict[str, str]:
    loai = td.get("loai", "").lower()
    if loai == "yesno":
        return {"1": "Có", "0": "Không"}
    if loai == "truefalse":
        return {"1": "Đúng", "0": "Sai"}
    if loai not in ("radio", "dropdown", "checkbox"):
        return {}
    ra = {}
    for phan in td.get("lua_chon", "").split("|"):
        if "," in phan:
            ma, nhan = phan.split(",", 1)
            ra[ma.strip()] = bo_html(nhan)
    return ra


def ten_spss_tu_chu_thich(td: dict) -> str | None:
    m = re.search(r"Tên SPSS:\s*([A-Za-z@#$][A-Za-z0-9_.@#$]*)", td.get("chu_thich", ""))
    return m.group(1).rstrip(".") if m else None


def doc_ma_thieu(p: Path | None) -> list[dict]:
    """Tệp mã thiếu cấp dự án (cột bien, ma, nhan): bien='*' áp mọi trường."""
    if not p or not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return [
            {
                "bien": (r.get("bien") or "").strip(),
                "ma": (r.get("ma") or "").strip(),
                "nhan": (r.get("nhan") or "").strip(),
            }
            for r in csv.DictReader(f)
            if (r.get("ma") or "").strip()
        ]


def quet_csv(p: Path) -> tuple[list[str], list[dict], int]:
    """Đọc tiêu đề + thống kê từng cột: số hay chuỗi, độ rộng, số lẻ, tập giá trị (≤ 20), giá trị không phải số."""
    with open(p, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        tieu_de = next(r, None)
        if not tieu_de:
            raise TuChoi(f"{p.name}: tệp rỗng")
        tk = [
            {"rong": 1, "le": 0, "nguyen": 1, "khong_so": set(), "gia_tri": set(), "nhieu_muc": False} for _ in tieu_de
        ]
        n = 0
        for dong in r:
            n += 1
            for i, v in enumerate(dong[: len(tieu_de)]):
                v = v.strip()
                if v == "":
                    continue
                t = tk[i]
                t["rong"] = max(t["rong"], len(v.encode("utf-8")))
                x = _so(v)
                if x is None:
                    t["khong_so"].add(v)
                else:
                    if "." in v and "e" not in v.lower():
                        t["le"] = max(t["le"], len(v.split(".")[1]))
                    t["nguyen"] = max(t["nguyen"], len(str(int(abs(x)))) + (1 if x < 0 else 0))
                if not t["nhieu_muc"]:
                    t["gia_tri"].add(v)
                    if len(t["gia_tri"]) > TRAN_MUC_LIET_KE:
                        t["nhieu_muc"] = True
                        t["gia_tri"] = set()
    return tieu_de, tk, n


def ke_hoach_bien(
    tieu_de: list[str], tk: list[dict], td: dict[str, dict], ma_thieu: list[dict]
) -> tuple[list[dict], list[str]]:
    """Mỗi cột CSV ⇒ một biến SPSS. Trả (kế hoạch, cảnh báo). Ném TuChoi khi cột là định danh (Identifier?=y)."""
    canh_bao, ke, dung = [], [], set()
    ma_chu_chung = [m for m in ma_thieu if m["bien"] == "*" and _so(m["ma"]) is None]
    for i, cot in enumerate(tieu_de):
        t = tk[i]
        goc = re.sub(r"___[^_].*$", "", cot)  # REDCap checkbox xuất thành <trường>___<mã>
        d = td.get(cot) or td.get(goc) or {}
        if d.get("dinh_danh", "").lower() in ("y", "yes", "1"):
            raise TuChoi(
                f"cột «{cot}» là trường ĐỊNH DANH (Identifier?=y) trong từ điển — "
                "bộ dữ liệu xuất SPSS phải khử định danh"
            )
        ten = ten_spss_tu_chu_thich(d) if d and cot == goc else None
        if ten and not ten_hop_le(ten):
            canh_bao.append(f"«Tên SPSS: {ten}» của {cot} không hợp lệ — dùng tên gốc")
            ten = None
        ten = ten or chuan_ten(cot)
        if ten.upper() in dung:
            canh_bao.append(f"tên {ten} trùng — {cot} giữ tên chuẩn hoá có hậu tố")
            ten = chuan_ten(ten + "_" + str(i))
        dung.add(ten.upper())
        ma_chu = {m["ma"]: MA_CHU_BAT_DAU - k for k, m in enumerate(ma_chu_chung) if m["ma"] in t["khong_so"]}
        khong_so_con = t["khong_so"] - set(ma_chu)
        la_so = not khong_so_con
        nhan_gt: dict[str, str] = {}
        if d and cot != goc:  # cột checkbox
            lc = lua_chon(d)
            ma_cb = cot[len(goc) + 3 :]
            nhan = f"{bo_html(d.get('nhan', ''))}: {lc.get(ma_cb, ma_cb)}"
            nhan_gt = {"1": "Có", "0": "Không"}
            muc = "NOMINAL"
        else:
            nhan = bo_html(d.get("nhan", "")) or cot
            nhan_gt = lua_chon(d)
            loai = d.get("loai", "").lower()
            if not la_so:
                muc = "NOMINAL"
            elif loai in ("radio", "dropdown"):
                ma_so = sorted(int(float(k)) for k in nhan_gt if _so(k) is not None and float(k).is_integer())
                lien = len(ma_so) >= 4 and ma_so == list(range(ma_so[0], ma_so[0] + len(ma_so)))
                muc = "ORDINAL" if lien else "NOMINAL"
            elif loai in ("yesno", "truefalse", "checkbox"):
                muc = "NOMINAL"
            elif not d and not t["nhieu_muc"] and len(t["gia_tri"]) <= 2:
                muc = "NOMINAL"
            else:
                muc = "SCALE"
        if not d:
            canh_bao.append(f"cột «{cot}» không có trong từ điển G5 — nhãn = tên cột")
        thieu_so = []
        for m in ma_thieu:
            if m["bien"] in (cot, goc) and _so(m["ma"]) is not None:
                thieu_so.append((m["ma"], m["nhan"]))
        for ma, so_ma in ma_chu.items():
            nhan_ma = next(m["nhan"] for m in ma_chu_chung if m["ma"] == ma)
            thieu_so.append((str(so_ma), f"{ma} — {nhan_ma}"))
        if len(thieu_so) > 3:
            canh_bao.append(f"{ten}: {len(thieu_so)} mã thiếu — SPSS chỉ nhận 3 giá trị rời, giữ 3 mã đầu")
        ke.append(
            {
                "cot": cot,
                "ten": ten,
                "so": la_so,
                "doc_chuoi_roi_doi": la_so and bool(ma_chu),
                "rong": t["rong"],
                "le": min(t["le"], 8),
                "nguyen": t["nguyen"],
                "nhan": cat_byte(nhan, TRAN_NHAN_BIEN),
                "nhan_gia_tri": {k: cat_byte(v, TRAN_NHAN_GIA_TRI) for k, v in nhan_gt.items()},
                "muc_do": muc,
                "ma_chu": ma_chu,
                "ma_thieu": thieu_so[:3],
                "muc": sorted(t["gia_tri"], key=lambda v: (_so(v) is None, _so(v) or 0, v))
                if not t["nhieu_muc"]
                else None,
            }
        )
        if khong_so_con and d.get("kiem_tra", "") in ("integer", "number"):
            canh_bao.append(
                f"{cot}: từ điển ghi kiểu số nhưng có giá trị chữ ngoài mã thiếu "
                f"({len(khong_so_con)} giá trị) — đọc dạng chuỗi"
            )
    return ke, canh_bao


def _dinh_dang(b: dict) -> str:
    if b["so"] and not b["doc_chuoi_roi_doi"]:
        w = max(8, b["nguyen"] + b["le"] + 2)
        return f"F{w}.{b['le']}"
    return f"A{max(1, b['rong'])}"


def cu_phap_nhan_bien(csv_p: Path, sav_p: Path, ke: list[dict], *, ghi_chu: list[str]) -> str:
    dong = [
        "* Sinh bởi tools/cau_noi_spss.py xuat-sav — KHÔNG sửa tay (sinh lại từ từ điển G5).",
        *[f"* {g}" for g in ghi_chu],
        "SET UNICODE=ON.",
        "SET OLANG=ENGLISH.",
        f"GET DATA /TYPE=TXT /FILE={chuoi_spss(str(csv_p), 240)} /ENCODING='UTF8'",
        '  /DELCASE=LINE /DELIMITERS="," /QUALIFIER=\'"\' /ARRANGEMENT=DELIMITED /FIRSTCASE=2',
        "  /VARIABLES=",
    ]
    dong += [f"    {b['ten']} {_dinh_dang(b)}" for b in ke]
    dong[-1] += "."
    for b in ke:
        if b["doc_chuoi_roi_doi"]:
            ma = " ".join(f"('{k}'='{v}')" for k, v in b["ma_chu"].items())
            dong += [
                f"RECODE {b['ten']} {ma}.",
                f"ALTER TYPE {b['ten']} (F{max(8, b['nguyen'] + b['le'] + 2)}.{b['le']}).",
            ]
    dong.append("VARIABLE LABELS")
    dong += [f"  {'/' if k else ''}{b['ten']} {chuoi_spss(b['nhan'])}" for k, b in enumerate(ke)]
    dong[-1] += "."
    khoi_nhan = []
    for b in ke:
        cap = dict(b["nhan_gia_tri"])
        cap.update({m: n for m, n in b["ma_thieu"]})
        gia = []
        for ma, nhan in cap.items():
            if b["so"] and _so(ma) is None:
                continue  # mã chữ không gắn được cho biến số
            ma_s = ma if b["so"] else "'" + ma.replace("'", "''") + "'"
            gia.append(f"    {ma_s} {chuoi_spss(nhan)}")
        if gia:
            khoi_nhan.append((b["ten"], gia))
    if khoi_nhan:
        dong.append("VALUE LABELS")
        for k, (ten, gia) in enumerate(khoi_nhan):
            dong.append(f"  {'/' if k else ''}{ten}")
            dong += gia
        dong[-1] += "."
    for muc in ("SCALE", "ORDINAL", "NOMINAL"):
        ds = [b["ten"] for b in ke if b["muc_do"] == muc]
        if ds:
            dong.append(f"VARIABLE LEVEL {' '.join(ds)} ({muc}).")
    for b in ke:
        if b["ma_thieu"] and b["so"]:
            dong.append(f"MISSING VALUES {b['ten']} ({', '.join(m for m, _ in b['ma_thieu'])}).")
    dong += ["EXECUTE.", f"SAVE OUTFILE={chuoi_spss(str(sav_p), 240)} /COMPRESSED.", ""]
    return "\n".join(dong)


# ───────────────────────────── lệnh xuat-sav ─────────────────────────────


def tim_du_lieu_khoa(study: str) -> tuple[Path, dict]:
    """Bộ dữ liệu đã khoá + manifest khoá (cùng cách tìm với run_stats_analysis._data_lock_manifest_path)."""
    d = thu_muc_de_tai(study)
    meta = _doc_json(d / "study_meta.json")
    rel = (meta.get("real_data_lock") or {}).get("manifest")
    man_p = d / rel if rel else d / "DATA_LOCK_manifest.json"
    man = _doc_json(man_p)
    if not man:
        raise KhongDoDuoc(
            f"chưa có manifest khoá dữ liệu ({man_p.relative_to(BASE) if man_p.is_relative_to(BASE) else man_p}) — "
            "khoá bằng tools/lock_analysis_dataset.py trước, hoặc dùng --data … --ban-nhap cho bản nháp"
        )
    p = Path(man.get("locked_dataset_path") or "")
    if not p.is_absolute():
        p = d / p
    if not p.exists():
        raise KhongDoDuoc(f"manifest khoá trỏ tới {p} nhưng tệp không có trên máy này")
    if man.get("sha256") and sha256_tep(p) != man["sha256"]:
        raise TuChoi("SHA-256 bộ dữ liệu khoá KHÔNG khớp manifest — dữ liệu đã bị đổi sau khi khoá; dừng")
    return p, man


def lenh_xuat_sav(args) -> int:
    d = thu_muc_de_tai(args.study)
    if args.data:
        csv_p = Path(args.data).expanduser().resolve()
        if not args.ban_nhap:
            raise TuChoi(
                "--data chỉ dùng cùng --ban-nhap (bản nháp, KHÔNG phải dữ liệu khoá); bỏ --data để dùng bộ đã khoá"
            )
        man = {"locked": False}
    else:
        csv_p, man = tim_du_lieu_khoa(args.study)
    if csv_p.suffix.lower() != ".csv":
        raise TuChoi(f"chỉ nhận CSV (đang là {csv_p.suffix})")
    td_p = Path(args.dictionary).expanduser() if args.dictionary else d / f"G5_REDCap_dictionary_{args.study}.csv"
    if not td_p.exists():
        raise KhongDoDuoc(f"không thấy từ điển G5: {td_p}")
    mt_p = Path(args.ma_thieu).expanduser() if args.ma_thieu else d / "_ma-thieu-theo-bien.csv"
    td, mt = doc_tu_dien(td_p), doc_ma_thieu(mt_p)
    tieu_de, tk, n = quet_csv(csv_p)
    ke, canh_bao = ke_hoach_bien(tieu_de, tk, td, mt)
    ra = d / "spss"
    ra.mkdir(parents=True, exist_ok=True)
    hau_to = "_BAN-NHAP" if args.ban_nhap else "_khoa"
    sav_p, sps_p = (
        ra / f"{args.study}{hau_to}.sav",
        ra / f"{args.study}_nhan_bien{'_ban-nhap' if args.ban_nhap else ''}.sps",
    )
    ghi_chu = [
        f"Nguồn: {csv_p.name} · SHA-256 {sha256_tep(csv_p)[:16]}… · {n} ca · {len(ke)} biến",
        "Bản NHÁP — chưa khoá"
        if args.ban_nhap
        else f"Khoá ngày {man.get('lock_date', '?')} · SAP {man.get('sap_version', '?')}",
    ]
    sps_p.write_text(cu_phap_nhan_bien(csv_p, sav_p, ke, ghi_chu=ghi_chu), encoding="utf-8", newline="\n")
    print(f"✓ Cú pháp nhãn biến: {sps_p}")
    for c in canh_bao:
        print(f"  ⚠ {c}")
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "ban_nhap": bool(args.ban_nhap),
        "nguon_csv": str(csv_p),
        "sha256_nguon": sha256_tep(csv_p),
        "manifest_khoa": {k: man.get(k) for k in ("lock_date", "sap_version", "sha256", "approved_by")},
        "tu_dien": str(td_p),
        "sha256_tu_dien": sha256_tep(td_p),
        "ma_thieu": str(mt_p) if mt else None,
        "so_ca_csv": n,
        "cu_phap": str(sps_p),
        "canh_bao": canh_bao,
        "bien": [{k: b[k] for k in ("cot", "ten", "so", "muc_do", "nhan", "muc", "ma_chu")} for b in ke],
        "disclaimer": CAN_KIEM,
    }
    try:
        py = tim_spss()
    except KhongDoDuoc as e:
        (ra / f"{sav_p.name}.manifest.json").write_text(
            json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
        )
        print(f"⚪ {e}\n   Mở {sps_p.name} trong SPSS và Run All để tạo {sav_p.name}.")
        return MA_KHONG_DO
    if sav_p.exists():
        os.chmod(sav_p, stat.S_IWUSR | stat.S_IRUSR)
        sav_p.unlink()
    ma, out, err = chay_spss(py, ["--cu-phap", str(sps_p)], thu_muc=ra)
    (ra / f"{sps_p.stem}.log").write_text(
        out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n"
    )
    so_ca = _gia_tri_dong(out, "SO_CA")
    if ma != 0 or not sav_p.exists():
        print("🔴 SPSS báo lỗi khi tạo .sav —", (err or out).strip()[-800:])
        return MA_LECH
    if so_ca is not None and so_ca != str(n):
        print(f"🔴 Số ca trong .sav ({so_ca}) khác số dòng CSV ({n}) — không dùng tệp này")
        return MA_LECH
    os.chmod(sav_p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    ket.update(
        {
            "sav": str(sav_p),
            "sha256_sav": sha256_tep(sav_p),
            "so_ca_sav": int(so_ca) if so_ca else None,
            "spss_phien_ban": _gia_tri_dong(out, "PHIEN_BAN") or phien_ban_tu_goi(py),
        }
    )
    (ra / f"{sav_p.name}.manifest.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print(f"✓ {sav_p} — {so_ca} ca · {len(ke)} biến (chỉ đọc) · manifest {sav_p.name}.manifest.json")
    return MA_OK


# ───────────────────────────── lệnh cu-phap ─────────────────────────────


def _doc_manifest_sav(study: str) -> dict:
    d = thu_muc_de_tai(study) / "spss"
    for ten in (f"{study}_khoa.sav.manifest.json", f"{study}_BAN-NHAP.sav.manifest.json"):
        m = _doc_json(d / ten)
        if m:
            return m
    raise KhongDoDuoc(f"chưa có {study}_khoa.sav — chạy `cau_noi_spss.py xuat-sav --study {study}` trước")


def dac_ta(args) -> dict:
    tom = _doc_json(thu_muc_de_tai(args.study) / f"{args.gate}_analysis_summary.json").get("dac_ta_phan_tich") or {}
    dt = {
        k: getattr(args, k, None) or tom.get(k)
        for k in ("outcome", "group", "outcome_type", "time", "event", "cot_cum")
    }
    cov = getattr(args, "covariates", None)
    dt["covariates"] = [c.strip() for c in cov.split(",") if c.strip()] if cov else list(tom.get("covariates") or [])
    dt["outcome_type"] = dt["outcome_type"] or "auto"
    return dt


def cu_phap_phan_tich(
    study: str, man: dict, dt: dict, thu_muc_kq: Path, *, bien_bang1: list[str] | None = None
) -> tuple[str, list[str]]:
    bien = {b["cot"]: b for b in man["bien"]}
    canh_bao = []

    def ten(cot: str | None) -> str | None:
        if not cot:
            return None
        if cot not in bien:
            raise TuChoi(f"biến «{cot}» không có trong {study}_khoa.sav")
        return bien[cot]["ten"]

    y, g, t, e, cum = ten(dt["outcome"]), ten(dt["group"]), ten(dt["time"]), ten(dt["event"]), ten(dt["cot_cum"])
    cov = [ten(c) for c in dt["covariates"]]
    so = {b["ten"]: b["so"] for b in man["bien"]}
    loai = dt["outcome_type"]
    if y and loai == "auto":
        m = bien[dt["outcome"]].get("muc")
        loai = "binary" if (m is not None and len(m) == 2) else "continuous"
    sav = man.get("sav") or str(thu_muc_de_tai(study) / "spss" / f"{study}_khoa.sav")
    dong = [
        "* Sinh bởi tools/cau_noi_spss.py cu-phap — khớp đặc tả G6 (run_stats_analysis.py). Cần bác sĩ kiểm chứng.",
        "SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES.",
        f"GET FILE={chuoi_spss(sav, 240)}.",
        "OMS /SELECT ALL /DESTINATION FORMAT=SPV OUTFILE="
        + chuoi_spss(str(thu_muc_kq / (study + "_phan_tich.spv")), 240)
        + " /TAG='ebm_spv'.",
    ]

    def khoi(tag: str, lenh: list[str]):
        dong.append(
            "OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE="
            + chuoi_spss(str(thu_muc_kq / ("oms_" + tag + ".xml")), 240)
            + f" /TAG='{tag}'."
        )
        dong.extend(lenh)
        dong.append(f"OMSEND TAG='{tag}'.")

    def tach(ds: list[str]) -> tuple[list[str], list[str]]:
        return [v for v in ds if so.get(v)], [v for v in ds if not so.get(v)]

    # Bảng 1
    loai_tru = {x for x in (y, g, t, e, cum) if x}
    b1 = [ten(c) for c in bien_bang1] if bien_bang1 else [b["ten"] for b in man["bien"] if b["ten"] not in loai_tru]
    lt = [v for v in b1 if bien_ten(man, v).get("muc_do") == "SCALE" and so.get(v)]
    pl = [v for v in b1 if v not in lt and bien_ten(man, v).get("muc") is not None]
    bo = [v for v in b1 if v not in lt and v not in pl]
    if bo:
        canh_bao.append(f"Bảng 1 bỏ {len(bo)} biến chuỗi/nhiều mức (vd mã phiếu): {', '.join(bo[:6])}")
    if g:
        lenh = []
        if lt:
            lenh.append(f"MEANS TABLES={' '.join(lt)} BY {g} /CELLS=MEAN STDDEV COUNT.")
        if pl:
            lenh.append(f"CROSSTABS /TABLES={' '.join(pl)} BY {g} /CELLS=COUNT COLUMN /STATISTICS=CHISQ.")
        if lenh:
            khoi("bang1", lenh)
    # Kết cục chính
    if y and g:
        muc_g = bien[dt["group"]].get("muc") or []
        if len(muc_g) != 2:
            raise TuChoi(f"biến nhóm {g} cần đúng 2 mức (đang có {len(muc_g) if muc_g else '>20'})")
        if loai == "binary":
            khoi("ket_cuc_chinh", [f"CROSSTABS /TABLES={g} BY {y} /STATISTICS=CHISQ RISK /CELLS=COUNT ROW."])
        elif loai == "continuous":
            g0, g1 = (v if so.get(g) else "'" + v + "'" for v in muc_g)
            khoi("ket_cuc_chinh", [f"T-TEST GROUPS={g}({g0} {g1}) /VARIABLES={y} /CRITERIA=CI(.95)."])
        pred = [g] + cov
        ps, pc = tach(pred)
        if loai == "binary":
            cat = ([f"  /CATEGORICAL={' '.join(pc)}"] + [f"  /CONTRAST({v})=Indicator(1)" for v in pc]) if pc else []
            khoi(
                "da_bien",
                [
                    f"LOGISTIC REGRESSION VARIABLES {y}",
                    f"  /METHOD=ENTER {' '.join(pred)}",
                    *cat,
                    "  /PRINT=CI(95) /CRITERIA=ITERATE(50) CUT(.5).",
                ],
            )
        elif loai == "continuous":
            by = f" BY {' '.join(pc)}" if pc else ""
            wi = f" WITH {' '.join(ps)}" if ps else ""
            khoi(
                "da_bien",
                [f"UNIANOVA {y}{by}{wi}", "  /PRINT=PARAMETER /CRITERIA=ALPHA(.05)", f"  /DESIGN={' '.join(pred)}."],
            )
        elif loai == "ordinal":
            by = f" BY {' '.join(pc)}" if pc else ""
            wi = f" WITH {' '.join(ps)}" if ps else ""
            khoi("da_bien", [f"PLUM {y}{by}{wi} /LINK=LOGIT", "  /PRINT=FIT PARAMETER SUMMARY TPARALLEL."])
        else:
            raise TuChoi(f"outcome_type không hỗ trợ: {loai}")
        if cum:
            phan_phoi = {
                "binary": "DISTRIBUTION=BINOMIAL LINK=LOGIT",
                "continuous": "DISTRIBUTION=NORMAL LINK=IDENTITY",
                "ordinal": "DISTRIBUTION=MULTINOMIAL LINK=CUMLOGIT",
            }[loai]
            tham_chieu = " (REFERENCE=FIRST)" if loai == "binary" else ""
            by = f" BY {' '.join(pc)}" if pc else ""
            wi = f" WITH {' '.join(ps)}" if ps else ""
            khoi(
                "da_bien_cum",
                [
                    f"GENLIN {y}{tham_chieu}{by}{wi}",
                    f"  /MODEL {' '.join(pred)} INTERCEPT=YES {phan_phoi}",
                    f"  /REPEATED SUBJECT={cum} CORRTYPE=INDEPENDENT ADJUSTCORR=NO COVB=ROBUST",
                    "  /PRINT SOLUTION (EXPONENTIATED).",
                ],
            )
            canh_bao.append(
                "Hiệu chỉnh cụm: GENLIN (GEE độc lập, SE robust) — Python dùng sandwich theo cụm có hiệu chỉnh mẫu nhỏ "
                "và phân phối t ⇒ ước lượng phải trùng, KTC/p có thể lệch nhẹ"
            )
    # Sống còn
    if t and e and g:
        cov_s = " ".join([g] + cov)
        # run_stats_analysis.survival_model tính HR «thô» trên CÙNG tập ca đầy đủ hiệp biến với mô hình hiệu chỉnh
        # (dropna trên thời gian · biến cố · nhóm · hiệp biến) — đo 14/11/2026: không lọc thì SPSS dùng nhiều ca
        # hơn, HR thô lệch.
        loc = ["TEMPORARY.", "SELECT IF (" + " AND ".join(f"NOT MISSING({v})" for v in cov) + ")."] if cov else []
        khoi("song_con_tho", [*loc, f"COXREG {t} /STATUS={e}(1) /METHOD=ENTER {g} /PRINT=CI(95)."])
        if cov:
            khoi("song_con_hieu_chinh", [f"COXREG {t} /STATUS={e}(1) /METHOD=ENTER {cov_s} /PRINT=CI(95)."])
        khoi("kaplan_meier", [f"KM {t} BY {g} /STATUS={e}(1) /PRINT TABLE MEAN /TEST LOGRANK /COMPARE OVERALL POOLED."])
        canh_bao.append(
            "Cox: SPSS xử lý thời điểm trùng bằng Breslow, lifelines bằng Efron ⇒ HR lệch rất nhỏ "
            "khi có nhiều thời điểm trùng"
        )
    dong += ["OMSEND TAG='ebm_spv'.", ""]
    return "\n".join(dong), canh_bao


def bien_ten(man: dict, ten: str) -> dict:
    return next((b for b in man["bien"] if b["ten"] == ten), {})


def lenh_cu_phap(args) -> int:
    man = _doc_manifest_sav(args.study)
    dt = dac_ta(args)
    if not dt["outcome"] and not (dt["time"] and dt["event"]):
        raise TuChoi(
            "thiếu đặc tả: chưa có G6_analysis_summary.json với khoá dac_ta_phan_tich — truyền --outcome/--group/"
            "--covariates (hoặc --time/--event) như run_stats_analysis.py"
        )
    kq = thu_muc_de_tai(args.study) / "spss" / "ket_qua"
    kq.mkdir(parents=True, exist_ok=True)
    vb, canh_bao = cu_phap_phan_tich(
        args.study, man, dt, kq, bien_bang1=[v.strip() for v in (args.vars or "").split(",") if v.strip()] or None
    )
    sps = thu_muc_de_tai(args.study) / "spss" / f"{args.study}_phan_tich.sps"
    sps.write_text(vb, encoding="utf-8", newline="\n")
    (kq / "dac_ta.json").write_text(json.dumps(dt, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"✓ Cú pháp phân tích: {sps}")
    for c in canh_bao:
        print(f"  ⚠ {c}")
    return MA_OK


# ───────────────────────────── lệnh chay + đọc OXML ─────────────────────────────


def _hang_theo_bien(bang: dict) -> dict[tuple, dict[str, float | None]]:
    ra: dict[tuple, dict] = {}
    for o in bang["o"]:
        ra.setdefault(tuple(o["hang"]), {})[" | ".join(o["cot"])] = o["so"]
    return ra


def _lay(cot: dict[str, float | None], *mau: str, tru: tuple[str, ...] = ()) -> float | None:
    for k, v in cot.items():
        if all(re.search(m, k, re.I) for m in mau) and not any(re.search(t, k, re.I) for t in tru):
            return v
    return None


_KHONG_PHAI_BIEN = re.compile(
    r"^(constant|intercept|\(intercept\)|\(scale\)|threshold|n of valid cases|\[.*=.*\])$", re.I
)


def he_so(bang: dict, *, mu: bool) -> dict[str, dict]:
    """Bảng hệ số (Variables in the Equation / Parameter Estimates) ⇒ {biến: {uoc_luong, ci, p, b}}.

    mu=True ⇒ thang Exp(B) (OR/HR); PLUM chỉ in B nên lấy mũ của B và hai cận KTC."""
    ra = {}
    for hang, cot in _hang_theo_bien(bang).items():
        if not hang or _KHONG_PHAI_BIEN.match(hang[-1].strip()) or (hang and hang[0].lower() == "threshold"):
            continue
        if hang[0].lower().startswith("step") and not hang[0].lower().startswith("step 1"):
            continue
        b = _lay(cot, r"^(B|Estimate)$")
        p = _lay(cot, r"(^|\| )Sig\.?$")
        exp = _lay(cot, r"^Exp\(B\)$")
        lo_e, hi_e = _lay(cot, r"exp\(b\)", r"lower"), _lay(cot, r"exp\(b\)", r"upper")
        lo, hi = _lay(cot, r"lower", tru=(r"exp\(b\)",)), _lay(cot, r"upper", tru=(r"exp\(b\)",))
        if mu:
            uoc = exp if exp is not None else (math.exp(b) if b is not None else None)
            ci = (
                [lo_e, hi_e]
                if lo_e is not None
                else ([math.exp(lo), math.exp(hi)] if lo is not None and hi is not None else None)
            )
        else:
            uoc, ci = b, ([lo, hi] if lo is not None else None)
        if uoc is not None:
            ra[hang[-1].strip()] = {"uoc_luong": uoc, "ci": ci, "p": p, "b": b}
    return ra


def doc_ket_qua(thu_muc_kq: Path, dt: dict, man: dict) -> dict:
    nguoc = {b["ten"]: b["cot"] for b in man["bien"]}
    ra: dict = {}

    def bang(tag: str, loai: str) -> list[dict]:
        p = thu_muc_kq / f"oms_{tag}.xml"
        return [b for b in phang_oxml(p) if _chuan_bang(b["bang"]) == loai] if p.exists() else []

    def doi_ten(d: dict) -> dict:
        return {nguoc.get(k, k): v for k, v in d.items()}

    loai = dt.get("outcome_type_da_xac_dinh") or dt.get("outcome_type")
    rk = bang("ket_cuc_chinh", "riskestimate")
    if rk:
        for hang, cot in _hang_theo_bien(rk[-1]).items():
            if hang and hang[-1].lower().startswith("odds ratio"):
                ra["ket_cuc_chinh"] = {
                    "loai": "binary",
                    "or": _lay(cot, r"^Value$"),
                    "ci": [_lay(cot, "lower"), _lay(cot, "upper")],
                }
        cs = bang("ket_cuc_chinh", "chisquaretests")
        if cs and "ket_cuc_chinh" in ra:
            for hang, cot in _hang_theo_bien(cs[-1]).items():
                if hang and hang[-1] == "Pearson Chi-Square":
                    ra["ket_cuc_chinh"]["p_pearson"] = _lay(cot, "asymptotic")
                if hang and hang[-1] == "Continuity Correction":
                    ra["ket_cuc_chinh"]["p_yates"] = _lay(cot, "asymptotic")
    tt = bang("ket_cuc_chinh", "independentsamplestest")
    if tt:
        kq = {"loai": "continuous"}
        for hang, cot in _hang_theo_bien(tt[-1]).items():
            khoa = "welch" if hang and "not assumed" in hang[-1] else "student"
            md = _lay(cot, r"mean difference")
            # SPSS: nhóm (mã nhỏ) − nhóm (mã lớn); Python: g1 − g0 ⇒ đổi dấu để cùng chiều
            kq[khoa] = {
                "md_g1_tru_g0": -md if md is not None else None,
                "p": _lay(cot, r"two-sided p"),
                "ci": [-x for x in (_lay(cot, "upper"), _lay(cot, "lower")) if x is not None] or None,
            }
        ra["ket_cuc_chinh"] = kq
    for tag, khoa in (("da_bien", "da_bien"), ("da_bien_cum", "da_bien_cum")):
        p = thu_muc_kq / f"oms_{tag}.xml"
        if not p.exists():
            continue
        bs = [b for b in phang_oxml(p) if _chuan_bang(b["bang"]) in ("variablesintheequation", "parameterestimates")]
        if not bs:
            continue
        mu = loai in ("binary", "ordinal")
        ra[khoa] = {"thang": "OR" if mu else "B", "he_so": doi_ten(he_so(bs[-1], mu=mu))}
    for tag in ("song_con_tho", "song_con_hieu_chinh"):
        bs = bang(tag, "variablesintheequation")
        if bs:
            ra[tag] = {"thang": "HR", "he_so": doi_ten(he_so(bs[-1], mu=True))}
    return ra


def lenh_chay(args) -> int:
    d = thu_muc_de_tai(args.study)
    sps = d / "spss" / f"{args.study}_phan_tich.sps"
    if not sps.exists():
        raise KhongDoDuoc(f"chưa có {sps.name} — chạy `cau_noi_spss.py cu-phap --study {args.study}` trước")
    py = tim_spss()
    kq = d / "spss" / "ket_qua"
    for cu in kq.glob("oms_*.xml"):
        cu.unlink()
    ma, out, err = chay_spss(py, ["--cu-phap", str(sps)], thu_muc=kq, thoi_han=args.thoi_han)
    (kq / f"{args.study}_phan_tich.log").write_text(
        out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n"
    )
    if ma != 0:
        print("🔴 SPSS báo lỗi —", (err or out).strip()[-800:], f"\n   nhật ký: {kq / (args.study + '_phan_tich.log')}")
        return MA_LECH
    man = _doc_manifest_sav(args.study)
    dt = _doc_json(kq / "dac_ta.json")
    m = next((b.get("muc") for b in man["bien"] if b["cot"] == dt.get("outcome")), None)
    dt["outcome_type_da_xac_dinh"] = (
        dt.get("outcome_type")
        if dt.get("outcome_type") not in (None, "auto")
        else ("binary" if m is not None and len(m) == 2 else "continuous")
    )
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "spss_phien_ban": _gia_tri_dong(out, "PHIEN_BAN") or phien_ban_tu_goi(py),
        "sav": man.get("sav"),
        "sha256_sav": man.get("sha256_sav"),
        "dac_ta": dt,
        "ket_qua": doc_ket_qua(kq, dt, man),
        "spv": str(kq / f"{args.study}_phan_tich.spv"),
        "disclaimer": CAN_KIEM,
    }
    (d / f"{args.gate}_spss_ket_qua.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print(f"✓ SPSS chạy xong · kết quả {d / (args.gate + '_spss_ket_qua.json')} · bảng mở trong SPSS: {ket['spv']}")
    return MA_OK


# ───────────────────────────── lệnh doi-chieu ─────────────────────────────

TOL_UOC, TOL_CI, TOL_P = 0.005, 0.015, 0.005


def _gan(a: float | None, b: float | None, tuong_doi: float, tuyet_doi: float = 0.0006) -> bool | None:
    if a is None or b is None:
        return None
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def _so_p(a: float | None, b: float | None) -> bool | None:
    if a is None or b is None:
        return None
    return (a < 0.001 and b < 0.001) or abs(a - b) <= TOL_P


def so_mot(ten: str, py: dict, sp: dict, *, phuong_phap_khac: str | None = None) -> dict:
    """Một dòng đối chiếu: py/sp = {uoc_luong, ci, p}. Trạng thái khop · lech_nho · lech · khong_so_duoc."""
    kt = {"uoc_luong": _gan(sp.get("uoc_luong"), py.get("uoc_luong"), TOL_UOC)}
    ci_py, ci_sp = py.get("ci") or [None, None], sp.get("ci") or [None, None]
    kt["ci"] = None if None in (*ci_py, *ci_sp) else all(_gan(a, b, TOL_CI) for a, b in zip(ci_sp, ci_py))
    kt["p"] = _so_p(sp.get("p"), py.get("p"))
    co = [v for v in kt.values() if v is not None]
    if kt["uoc_luong"] is None:
        tt = "khong_so_duoc"
    elif all(co):
        tt = "khop"
    elif kt["uoc_luong"] and phuong_phap_khac:
        tt = "lech_nho"
    else:
        tt = "lech"
    return {"muc": ten, "python": py, "spss": sp, "kiem": kt, "trang_thai": tt, "ghi_chu": phuong_phap_khac or ""}


def doi_chieu(tom: dict, kq: dict) -> list[dict]:
    dong: list[dict] = []
    pc, sc = tom.get("primary_outcome") or {}, kq.get("ket_cuc_chinh") or {}
    if pc.get("outcome_type") == "binary" and sc.get("loai") == "binary":
        dong.append(
            so_mot(
                "Kết cục chính — OR thô (nhóm sau so nhóm trước)",
                {"uoc_luong": pc.get("or_crude"), "ci": list(pc.get("ci_95") or []) or None, "p": pc.get("p_value")},
                {"uoc_luong": sc.get("or"), "ci": sc.get("ci"), "p": sc.get("p_yates")},
            )
        )
    elif pc.get("outcome_type") == "continuous" and sc.get("loai") == "continuous":
        welch = "welch" in str(pc.get("test", "")).lower()
        s = sc.get("welch" if welch else "student") or {}
        p_py = pc.get("p_value") if (welch or "t-test" in str(pc.get("test", "")).lower()) else None
        dong.append(
            so_mot(
                "Kết cục chính — hiệu trung bình (nhóm sau − nhóm trước)",
                {"uoc_luong": pc.get("md_crude"), "ci": None, "p": p_py},
                {"uoc_luong": s.get("md_g1_tru_g0"), "ci": None, "p": s.get("p") if p_py is not None else None},
                phuong_phap_khac=None if p_py is not None else f"Python dùng {pc.get('test')} — chỉ so hiệu trung bình",
            )
        )
    mv = tom.get("ordinal") if (tom.get("ordinal") or {}).get("results") else tom.get("multivariate") or {}
    cum = (mv.get("cov_type") == "cluster") or bool((tom.get("dac_ta_phan_tich") or {}).get("cot_cum"))
    nguon = kq.get("da_bien_cum") if cum and kq.get("da_bien_cum") else kq.get("da_bien")
    for r in mv.get("results") or []:
        v = r.get("variable")
        uoc = r.get("OR_adj", r.get("beta"))
        sp = (nguon or {}).get("he_so", {}).get(v)
        if sp is None:
            dong.append(
                {
                    "muc": f"Đa biến — {v}",
                    "python": {"uoc_luong": uoc},
                    "spss": None,
                    "kiem": {},
                    "trang_thai": "khong_so_duoc",
                    "ghi_chu": "SPSS không có hệ số cùng tên (biến phân loại mã hoá khác?)",
                }
            )
            continue
        dong.append(
            so_mot(
                f"Đa biến ({mv.get('model', '?')}) — {v}",
                {"uoc_luong": uoc, "ci": r.get("CI_95"), "p": r.get("p")},
                {"uoc_luong": sp["uoc_luong"], "ci": sp["ci"], "p": sp["p"]},
                phuong_phap_khac=(
                    "hiệu chỉnh cụm: GEE robust (SPSS) ≠ sandwich có hiệu chỉnh mẫu nhỏ (Python)"
                    if cum
                    else "statsmodels lấy SE từ Hessian xấp xỉ"
                    if mv.get("model") == "ordinal_logit_po"
                    else None
                ),
            )
        )
    sv = tom.get("survival") or {}
    nhom = (tom.get("dac_ta_phan_tich") or {}).get("group")
    for khoa_py, khoa_sp, nhan in (("crude", "song_con_tho", "thô"), ("adjusted", "song_con_hieu_chinh", "hiệu chỉnh")):
        r = sv.get(khoa_py) or {}
        sp = ((kq.get(khoa_sp) or {}).get("he_so") or {}).get(nhom) if nhom else None
        if r.get("HR") is not None and sp:
            dong.append(
                so_mot(
                    f"Cox — HR {nhan} ({nhom})",
                    {"uoc_luong": r.get("HR"), "ci": r.get("CI_95"), "p": r.get("p")},
                    {"uoc_luong": sp["uoc_luong"], "ci": sp["ci"], "p": sp["p"]},
                    phuong_phap_khac="thời điểm trùng: Breslow (SPSS) ≠ Efron (lifelines)",
                )
            )
    return dong


def _fmt(x) -> str:
    if x is None:
        return "—"
    if isinstance(x, (list, tuple)):
        return "–".join(_fmt(v) for v in x)
    return f"{x:.4g}" if isinstance(x, float) else str(x)


def lenh_doi_chieu(args) -> int:
    d = thu_muc_de_tai(args.study)
    tom = _doc_json(d / f"{args.gate}_analysis_summary.json")
    kq = _doc_json(d / f"{args.gate}_spss_ket_qua.json")
    if not tom:
        raise KhongDoDuoc(f"chưa có {args.gate}_analysis_summary.json (chạy run_stats_analysis.py trước)")
    if not kq:
        raise KhongDoDuoc(f"chưa có {args.gate}_spss_ket_qua.json (chạy `cau_noi_spss.py chay` trước)")
    if (tom.get("data_lock") or {}).get("sha256") and kq.get("sha256_sav"):
        man = _doc_manifest_sav(args.study)
        if man.get("sha256_nguon") != tom["data_lock"]["sha256"]:
            raise TuChoi("SPSS và Python KHÔNG phân tích cùng một bộ dữ liệu khoá (SHA-256 nguồn khác) — xuất lại .sav")
    dong = doi_chieu(tom, kq.get("ket_qua") or {})
    dem = {k: sum(1 for x in dong if x["trang_thai"] == k) for k in ("khop", "lech_nho", "lech", "khong_so_duoc")}
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "nguong": {"uoc_luong_tuong_doi": TOL_UOC, "ci_tuong_doi": TOL_CI, "p_tuyet_doi": TOL_P},
        "spss_phien_ban": kq.get("spss_phien_ban"),
        "dem": dem,
        "dong": dong,
        "disclaimer": CAN_KIEM,
    }
    (d / f"{args.gate}_spss_doi_chieu.json").write_text(
        json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    ky = {
        "khop": "✓ khớp",
        "lech_nho": "⚠ lệch nhỏ (khác phương pháp)",
        "lech": "✗ LỆCH",
        "khong_so_duoc": "⚪ không so được",
    }
    md = [
        f"# Đối chiếu SPSS ↔ Python — {args.study}",
        "",
        f"SPSS {kq.get('spss_phien_ban') or '?'} · {ket['luc']} · ngưỡng: ước lượng ±{TOL_UOC:.1%}, KTC ±{TOL_CI:.1%}, "
        f"p ±{TOL_P} (hai bên < 0,001 coi là khớp).",
        "",
        f"Tổng: {dem['khop']} khớp · {dem['lech_nho']} lệch nhỏ · {dem['lech']} lệch · "
        f"{dem['khong_so_duoc']} không so được.",
        "",
        "| Mục | Python (ước lượng · KTC 95% · p) | SPSS (ước lượng · KTC 95% · p) | Kết quả | Ghi chú |",
        "|---|---|---|---|---|",
    ]
    for x in dong:
        py, sp = x.get("python") or {}, x.get("spss") or {}
        md.append(
            f"| {x['muc']} | {_fmt(py.get('uoc_luong'))} · {_fmt(py.get('ci'))} · {_fmt(py.get('p'))} | "
            f"{_fmt(sp.get('uoc_luong'))} · {_fmt(sp.get('ci'))} · {_fmt(sp.get('p'))} | "
            f"{ky[x['trang_thai']]} | {x['ghi_chu']} |"
        )
    md += [
        "",
        "Đối chiếu bằng phần mềm thứ hai là KIỂM CHÉO kỹ thuật — không thay thống kê viên, "
        "không đổi trạng thái cổng G6.",
        "",
        CAN_KIEM,
        "",
    ]
    (d / f"{args.gate}_spss_doi_chieu.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    print("\n".join(md[4:5]))
    print(f"✓ {d / (args.gate + '_spss_doi_chieu.md')}")
    if dem["lech"]:
        return MA_LECH
    return MA_OK if (dem["khop"] + dem["lech_nho"]) else MA_KHONG_DO


# ───────────────────────────── lệnh nhap-sav ─────────────────────────────


def _quet_pii_ten(ten_cot: list[str]) -> list[str]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import import_real_dataset as rdi  # cùng luật quét tiêu đề với cổng tiếp nhận

        ham = getattr(rdi, "_header_issue", None)
    except ImportError:
        ham = None
    ra = []
    for c in ten_cot:
        ly_do = ham(c) if ham else None
        if not ly_do and re.search(
            r"(ho_?ten|hoten|ten_?bn|dien_?thoai|sdt|cccd|cmnd|bhyt|dia_?chi|ngay_?sinh|email|phone|name)", c.lower()
        ):
            ly_do = "tên cột nghi định danh"
        if ly_do:
            ra.append(f"{c}: {ly_do}")
    return ra


COT_REDCAP = [
    "Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
    "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
    "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
    "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name", "Matrix Ranking?",
    "Field Annotation",
]  # fmt: skip


def _ma_gon(k: str) -> str:
    x = _so(k)
    return str(int(x)) if x is not None and float(x).is_integer() else str(k).strip()


def ghi_tu_dien_redcap(bien: list[dict], p: Path) -> None:
    """Từ điển biến của .sav ⇒ khuôn từ điển REDCap (G5). Cột «Identifier?» để TRỐNG — bác sĩ tự đánh dấu."""
    dung: set[str] = set()
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COT_REDCAP)
        w.writeheader()
        for b in bien:
            ten = re.sub(r"[^a-z0-9_]", "_", b["ten"].lower()).strip("_") or "bien"
            ten = ten if re.match(r"[a-z]", ten) else "v_" + ten
            goc, k = ten, 2
            while ten in dung:
                ten, k = f"{goc}_{k}", k + 1
            dung.add(ten)
            ngl = {_ma_gon(m): v for m, v in (b.get("nhan_gia_tri") or {}).items()}
            thieu = b.get("thieu") or [0]
            dd = str(b.get("dinh_dang") or "")
            loai, kt = "text", ""
            if ngl:
                loai = "radio" if b.get("kieu") == 0 else "dropdown"
            elif re.fullmatch(r"F\d+(\.\d+)?", dd):
                kt = "number" if re.fullmatch(r"F\d+\.[1-9]\d*", dd) else "integer"
            ghi = f"Tên SPSS: {b['ten']}. Mức đo SPSS: {b.get('muc_do') or '?'}."
            if thieu[0]:
                ghi += " Mã thiếu SPSS: " + ", ".join(_ma_gon(str(x)) for x in thieu[1:] if x is not None) + "."
            dong = dict.fromkeys(COT_REDCAP, "")
            dong.update({COT_REDCAP[0]: ten, COT_REDCAP[1]: "nhap_tu_spss", COT_REDCAP[3]: loai,
                         COT_REDCAP[4]: b.get("nhan") or b["ten"],
                         COT_REDCAP[5]: " | ".join(f"{m}, {v}" for m, v in ngl.items()), COT_REDCAP[7]: kt,
                         COT_REDCAP[17]: ghi})  # fmt: skip
            w.writerow(dong)


def lenh_nhap_sav(args) -> int:
    sav = Path(args.sav).expanduser().resolve()
    if not sav.exists() or sav.suffix.lower() != ".sav":
        raise TuChoi(f"không thấy tệp .sav: {sav}")
    ra = Path(args.ra).expanduser().resolve() if args.ra else sav.parent / f"{sav.stem}_tu_spss"
    try:
        ra.relative_to(BASE)
        raise TuChoi("thư mục ra nằm TRONG repo — dữ liệu chưa qua cổng tiếp nhận phải ở ngoài repo (chọn --ra khác)")
    except ValueError:
        pass
    ra.mkdir(parents=True, exist_ok=True)
    py = tim_spss()
    csv_p, td_p = ra / f"{sav.stem}.csv", ra / f"{sav.stem}_tu_dien.json"
    ma, out, err = chay_spss(py, ["--tu-dien", str(sav), str(td_p)], thu_muc=ra)
    if ma != 0 or not td_p.exists():
        print("🔴 SPSS không đọc được tệp .sav —", (err or out).strip()[-600:])
        return MA_LECH
    sps = ra / f"{sav.stem}_xuat_csv.sps"
    sps.write_text(
        "\n".join(
            [
                f"GET FILE={chuoi_spss(str(sav), 240)}.",
                f"SAVE TRANSLATE OUTFILE={chuoi_spss(str(csv_p), 240)} /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES"
                " /CELLS=VALUES /REPLACE.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    ma, out, err = chay_spss(py, ["--cu-phap", str(sps)], thu_muc=ra)
    if ma != 0 or not csv_p.exists():
        print("🔴 SPSS không xuất được CSV —", (err or out).strip()[-600:])
        return MA_LECH
    b = csv_p.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):  # SAVE TRANSLATE /ENCODING='UTF8' ghi BOM — cổng tiếp nhận đọc tiêu đề nguyên văn
        csv_p.write_bytes(b[3:])
    td = _doc_json(td_p)
    rc_p = ra / f"{sav.stem}_tu_dien_redcap.csv"
    ghi_tu_dien_redcap(td.get("bien", []), rc_p)
    pii = _quet_pii_ten([b["ten"] for b in td.get("bien", [])] + [b.get("nhan", "") for b in td.get("bien", [])])
    print(f"✓ {csv_p} ({td.get('so_ca')} ca · {len(td.get('bien', []))} biến) + từ điển nhãn {td_p.name}")
    print(f"✓ Từ điển dạng REDCap (khuôn G5, tên gốc giữ ở «Tên SPSS: …»): {rc_p.name}")
    co_thieu = [b["ten"] for b in td.get("bien", []) if (b.get("thieu") or [0])[0]]
    if co_thieu:
        print(
            f"⚠ {len(co_thieu)} biến có mã thiếu do người dùng định nghĩa (CSV giữ NGUYÊN giá trị mã — "
            f"bước làm sạch phải xử lý theo từ điển): {', '.join(co_thieu[:12])}"
        )
    if pii:
        print("🔴 Nghi PII — KHÔNG nhập vào hồ sơ trước khi khử định danh:\n   " + "\n   ".join(pii))
        return MA_TU_CHOI
    print(
        "→ Bước kế (cổng tiếp nhận chuẩn, quét PII theo giá trị): "
        f'python3 tools/import_real_dataset.py --study <mã> --data "{csv_p}"'
    )
    return MA_OK


# ───────────────────────────── CLI ─────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Cầu nối IBM SPSS Statistics ↔ hệ nghiên cứu G5–G6 (chế độ nền). " + CAN_KIEM
    )
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("kiem", help="tìm SPSS, chạy thử, liệt kê mô-đun được cấp phép")
    x = sub.add_parser("xuat-sav", help="bộ dữ liệu khoá + từ điển G5 ⇒ .sps nhãn biến + .sav")
    x.add_argument("--study", required=True)
    x.add_argument("--data", help="CSV khác bộ đã khoá (bắt buộc kèm --ban-nhap)")
    x.add_argument("--ban-nhap", action="store_true", help="bản nháp, KHÔNG phải dữ liệu khoá")
    x.add_argument("--dictionary", help="từ điển REDCap (mặc định exports/<mã>/G5_REDCap_dictionary_<mã>.csv)")
    x.add_argument("--ma-thieu", help="tệp mã thiếu cấp dự án (mặc định exports/<mã>/_ma-thieu-theo-bien.csv)")
    for ten, giup in (
        ("cu-phap", "sinh cú pháp phân tích khớp đặc tả G6"),
        ("chay", "chạy cú pháp phân tích trong SPSS"),
        ("doi-chieu", "so kết quả SPSS với Python (G6_analysis_summary.json)"),
    ):
        p = sub.add_parser(ten, help=giup)
        p.add_argument("--study", required=True)
        p.add_argument("--gate", default="G6")
        if ten == "cu-phap":
            for opt in ("--outcome", "--group", "--covariates", "--time", "--event", "--cot-cum", "--vars"):
                p.add_argument(opt)
            p.add_argument("--outcome-type", choices=["auto", "binary", "continuous", "ordinal"])
        if ten == "chay":
            p.add_argument("--thoi-han", type=int, default=1200, help="giây (mặc định 1200)")
    n = sub.add_parser("nhap-sav", help=".sav của bác sĩ ⇒ CSV + từ điển nhãn (ngoài repo) cho cổng tiếp nhận")
    n.add_argument("--sav", required=True)
    n.add_argument("--ra", help="thư mục ra (NGOÀI repo; mặc định cạnh tệp .sav)")
    args = ap.parse_args(argv)
    ham = {
        "kiem": lenh_kiem,
        "xuat-sav": lenh_xuat_sav,
        "cu-phap": lenh_cu_phap,
        "chay": lenh_chay,
        "doi-chieu": lenh_doi_chieu,
        "nhap-sav": lenh_nhap_sav,
    }[args.lenh]
    try:
        return ham(args)
    except TuChoi as e:
        print(f"⛔ {e}")
        return MA_TU_CHOI
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
