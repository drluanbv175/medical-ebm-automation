#!/usr/bin/env python3
"""Cầu nối IBM SPSS Statistics ↔ hệ nghiên cứu G5–G6.

Bác sĩ giao 14/11/2026: «xây dựng kết nối với SPSS giúp tôi một cách tốt nhất».

SPSS chạy ở CHẾ ĐỘ NỀN (external mode của Python đi kèm SPSS — không mở giao diện, không cần bấm). Công cụ luôn sinh cú
pháp `.sps` đọc được, chạy tay được trong SPSS ở bất kỳ máy nào; máy có SPSS thì chạy luôn qua `tools/spss_chay_nen.py`.

Sáu lệnh:
  kiem        Tìm SPSS, phiên bản, chạy thử một lệnh (giấy phép), liệt kê mô-đun được cấp phép.
  xuat-sav    Bộ dữ liệu ĐÃ KHOÁ (manifest khoá, đối chiếu SHA-256) + từ điển REDCap G5 + mã thiếu cấp dự án
              ⇒ `exports/<mã>/spss/<mã>_nhan_bien.sps` + `<mã>_khoa.sav` (nhãn biến · nhãn giá trị · mức đo ·
              MISSING VALUES · tên theo «Tên SPSS: …» trong Field Annotation) + manifest. Mỗi lượt TỰ ĐỘNG đọc lại
              .sav vừa tạo (trước khi nhận) và so TỪNG ô với CSV nguồn qua cùng kế hoạch biến (E3 — khứ hồi) + so từ
              điển .sav với kế hoạch (E2); lệch ⇒ bỏ tệp, mã 1, ghi `khu_hoi`/`kiem_tu_dien` vào manifest.
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
import fnmatch
import hashlib
import json
import math
import os
import plistlib
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation
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


def chuoi_spss(s: str, tran_dong: int = 100, *, gop_trang: bool = True) -> str:
    """Chuỗi trích dẫn SPSS ('…', nháy đơn nhân đôi), tách thành nhiều đoạn nối bằng «+» để không dòng nào quá dài.

    gop_trang=False cho ĐƯỜNG DẪN: không gộp khoảng trắng (thư mục có hai dấu cách liền nhau vẫn đúng)."""
    s = re.sub(r"\s+", " ", str(s)).strip() if gop_trang else str(s)
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


def dd_spss(p: Path | str) -> str:
    """Đường dẫn tệp trong cú pháp SPSS."""
    return chuoi_spss(str(p), 240, gop_trang=False)


def goi_ds(ds: list[str], *, thut: str = "    ", tran: int = 200) -> str:
    """Danh sách tên biến gói thành nhiều dòng ≤ `tran` byte. Đo 14/11/2026: SPSS báo «syntax is incomplete» khi một
    dòng cú pháp dài quá ~1024 byte (bộ 70 biến tên dài)."""
    dong, cur = [], ""
    for v in ds:
        if cur and len((cur + " " + v).encode("utf-8")) > tran:
            dong.append(cur)
            cur = v
        else:
            cur = (cur + " " + v).strip()
    if cur:
        dong.append(cur)
    return ("\n" + thut).join(dong)


def ten_hop_le(ten: str) -> bool:
    # Tên bắt đầu bằng # là biến NHÁP (mất khi lưu), $ là biến hệ thống — không dùng cho biến của bộ dữ liệu.
    return (
        bool(re.fullmatch(r"[A-Za-z@][A-Za-z0-9_.@#$]*", ten))
        and not ten.endswith(".")
        and ten.upper() not in TU_KHOA_SPSS
        and len(ten.encode("utf-8")) <= 64
    )


def chuan_ten(ten: str) -> str:
    t = re.sub(r"[^A-Za-z0-9_.@#$]", "_", ten).rstrip(".")
    if not t or not re.match(r"[A-Za-z]", t):
        t = "v_" + t
    if t.upper() in TU_KHOA_SPSS:
        t += "_"
    return cat_byte(t, 64).rstrip(".")


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


def _dung_nhom_tien_trinh(p: subprocess.Popen) -> None:
    """Dừng trình nền VÀ mọi tiến trình con SPSS nó sinh ra (cùng nhóm/phiên)."""
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        else:  # Windows: p.kill() chỉ dừng trình nền — /T dừng cả cây tiến trình con
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, check=False)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def _don_con_sot(p: subprocess.Popen) -> None:
    """Trình nền đã thoát mà còn tiến trình con cùng nhóm (lõi SPSS mồ côi — giữ tệp, có thể giữ giấy phép) ⇒ dừng."""
    if os.name == "nt":
        return
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _chay_lenh(lenh: list[str], *, thu_muc: Path, thoi_han: int, nhan: str) -> tuple[int, str, str]:
    """Chạy một tiến trình ngoài (Python của SPSS, Rscript). Trả (mã, stdout, stderr); hết hạn ⇒ mã 1 kèm lý do.

    Đầu ra ghi vào TỆP tạm, KHÔNG qua ống dẫn (pipe): đo 14/11/2026, khi SPSS gặp lỗi nghiêm trọng một tiến trình con
    của nó vẫn giữ ống stdout nên `subprocess.run(capture_output=True)` chờ tới hết thời hạn (20 phút) dù trình nền đã
    dừng. Chỉ chờ CHÍNH tiến trình đã gọi; hết hạn hoặc nó đã thoát ⇒ dừng cả nhóm tiến trình."""
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")}
    nhom = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    with tempfile.TemporaryDirectory(prefix="ebm-spss-log-") as tam:
        p_out, p_err = Path(tam) / "out.txt", Path(tam) / "err.txt"
        with open(p_out, "wb") as f_out, open(p_err, "wb") as f_err:
            try:
                p = subprocess.Popen(
                    lenh,
                    stdout=f_out,
                    stderr=f_err,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    cwd=str(thu_muc),
                    **nhom,
                )
            except OSError as e:
                return 1, "", f"{nhan} không chạy được: {e}"
            try:
                ma: int | None = p.wait(timeout=thoi_han)
            except subprocess.TimeoutExpired:
                _dung_nhom_tien_trinh(p)
                ma = None
            else:
                _don_con_sot(p)
        out = p_out.read_text(encoding="utf-8", errors="replace")
        err = p_err.read_text(encoding="utf-8", errors="replace")
    if ma is None:
        return 1, out, err + f"\n{nhan} quá thời hạn {thoi_han} giây"
    return ma, out, err


def chay_spss(py: Path, doi_so: list[str], *, thu_muc: Path, thoi_han: int = 1200) -> tuple[int, str, str]:
    """Chạy trình nền `spss_chay_nen.py` bằng Python của SPSS (xem _chay_lenh)."""
    return _chay_lenh([str(py), "-I", str(TRINH_CHAY), *doi_so], thu_muc=thu_muc, thoi_han=thoi_han, nhan="LOI_SPSS")


def tim_spss() -> Path:
    ds = ung_vien_python_spss()
    if not ds:
        raise KhongDoDuoc(
            "không tìm thấy Python đi kèm IBM SPSS Statistics (Mac: /Applications/IBM SPSS Statistics/Resources/"
            "Python3/bin/python3.X · Windows: C:\\Program Files\\IBM\\SPSS Statistics\\Python3\\python.exe) — "
            "đặt EBM_SPSS_PYTHON nếu cài chỗ khác; cú pháp .sps vẫn sinh được để chạy tay trong SPSS"
        )
    return ds[0]


def _goc_tam_ngan() -> Path:
    """Gốc thư mục tạm có đường dẫn NGẮN. Đo 14/11/2026: SPSS báo «Serious error» khi đường dẫn tệp dài quá ~255 byte
    (FILE HANDLE cũng không cứu được) — đường OneDrive + worktree dễ vượt. Mọi lượt chạy tự động nên làm việc trong
    vùng tạm ngắn rồi chép kết quả về; tệp .sps người đọc vẫn ghi đường dẫn thật."""
    g = Path(tempfile.gettempdir())
    if len(str(g).encode("utf-8")) > 60 and os.name != "nt" and Path("/tmp").is_dir():
        g = Path("/tmp")
    return g


def vung_tam() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix="ebm-spss-", dir=_goc_tam_ngan())


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

    with vung_tam() as tam:
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
    """Tệp mã thiếu cấp dự án (cột bien, ma, nhan).

    bien='*' áp MỌI trường nhưng CHỈ cho mã CHỮ (BTR, KDD…) — mã số như 9 có thể là giá trị hợp lệ ở trường khác.
    bien là mẫu glob (vd `[a-f]1`, `a?`) ⇒ áp cho mọi cột khớp mẫu, cả mã số. Còn lại: tên đúng một trường."""
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


def _ap_cho_cot(m: dict, cot: str, goc: str) -> bool:
    b = m["bien"]
    if b == "*":
        return _so(m["ma"]) is None
    if b in (cot, goc):
        return True
    return bool(re.search(r"[*?\[]", b)) and (fnmatch.fnmatchcase(goc, b) or fnmatch.fnmatchcase(cot, b))


def _ma_so_gon(ma: str) -> str:
    x = _so(ma)
    return str(int(x)) if x is not None and x.is_integer() else ma


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
                t = tk[i]
                # Độ rộng A tính trên ô GỐC chỉ bỏ dấu cách CUỐI: đo 14/11/2026, GET DATA giữ nguyên khoảng trắng ĐẦU
                # (và tab) của ô chuỗi, chỉ dấu cách cuối mất. Bản cũ đo trên ô đã strip() ⇒ «  Nguyễn Văn  » (A13)
                # bị SPSS cắt thành «  Nguyễn V» — phép khứ hồi từng ô (E3) bắt được lỗi này.
                t["rong"] = max(t["rong"], len(v.rstrip(" ").encode("utf-8")))
                v = v.strip()
                if v == "":
                    continue
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


# Nhãn lựa chọn «giống mã thiếu» (Không biết/Không nhớ/Từ chối/Không áp dụng…) — máy chỉ ĐỀ XUẤT, không tự khai thiếu:
# quyết định mã nào là thiếu thuộc SAP/thống kê viên (C1a: Bảng E.1).
_NHAN_GIONG_THIEU = re.compile(
    r"^\s*(không\s+biết|không\s+nhớ|không\s+trả\s+lời|từ\s+chối|không\s+muốn\s+trả\s+lời|không\s+áp\s+dụng|"
    r"không\s+sử\s+dụng|don'?t\s+know|refused|not\s+applicable|no\s+answer|prefer\s+not)",
    re.I,
)
_DAU_THU_TU = re.compile(
    r"\b(rất|hài\s+lòng|bình\s+thường|kém|tốt|trung\s+bình|chắc\s+chắn|đồng\s+ý|nhẹ|vừa|nặng|thường\s+xuyên|"
    r"thỉnh\s+thoảng|hiếm\s+khi|không\s+bao\s+giờ|luôn\s+luôn|dưới|trên|trở\s+lên|lần|very|poor|fair|good|"
    r"excellent|agree|satisf\w*|never|rarely|sometimes|often|always|mild|moderate|severe|less\s+than|more\s+than)\b",
    re.I,
)


def la_thang_thu_tu(nhan_gt: dict[str, str], bo: set[str]) -> bool:
    """≥ 3 mã nguyên LIÊN TIẾP (sau khi bỏ mã thiếu/giống-thiếu) VÀ ≥ một nửa nhãn mang dấu hiệu thứ bậc (rất · kém ·
    tốt · hài lòng · dưới · trên…, hoặc nhãn là số/khoảng như «2», «5–10 km»).

    Đo 14/11/2026 trên từ điển C1a: luật cũ («≥ 4 mã liên tiếp») gán ORDINAL cho nghề nghiệp, hôn nhân, phương tiện,
    ngày trong tuần và NOMINAL cho 30 câu Likert có thêm mã 8/9. Mức đo chỉ là siêu dữ liệu — không đổi mô hình."""
    cap = {k: v for k, v in nhan_gt.items() if k not in bo and _so(k) is not None and float(k).is_integer()}
    ma = sorted(int(float(k)) for k in cap)
    if len(ma) < 3 or ma != list(range(ma[0], ma[0] + len(ma))):
        return False
    dau = sum(1 for v in cap.values() if _DAU_THU_TU.search(v) or re.match(r"\s*[<>≤≥]?\s*\d", v))
    return dau * 2 >= len(cap)


def menh_de_thieu_so(ten: str, ma_so: list[str], ma_chu_so: list[int]) -> str | None:
    """Phần trong ngoặc của MISSING VALUES cho biến SỐ.

    SPSS nhận tối đa 3 giá trị rời, HOẶC một khoảng, HOẶC một khoảng + một giá trị rời. Mã chữ đã đổi về ≤ −9991 nên gom
    thành khoảng «LO THRU −9991». Không khai được hết ⇒ TuChoi (bản cũ giữ 3 mã đầu, mã thứ tư thành giá trị HỢP LỆ)."""
    gia = [*ma_so, *(str(x) for x in ma_chu_so)]
    if not gia:
        return None
    if len(gia) <= 3:
        return ", ".join(gia)
    if ma_chu_so and len(ma_so) <= 1:
        return ", ".join([f"LO THRU {MA_CHU_BAT_DAU}", *ma_so])
    so = [_so(x) for x in ma_so]
    if not ma_chu_so and all(x is not None and x.is_integer() for x in so):
        nguyen = sorted(int(x) for x in so)  # type: ignore[union-attr]
        if nguyen == list(range(nguyen[0], nguyen[-1] + 1)):
            return f"{nguyen[0]} THRU {nguyen[-1]}"
    raise TuChoi(
        f"{ten}: {len(gia)} mã thiếu ({', '.join(gia)}) — SPSS chỉ khai được 3 giá trị rời hoặc một khoảng + một giá "
        "trị; gộp bớt mã trong _ma-thieu-theo-bien.csv (quyết định của thống kê viên)"
    )


def ke_hoach_bien(
    tieu_de: list[str], tk: list[dict], td: dict[str, dict], ma_thieu: list[dict], *, giu_ghi_chu: bool = False
) -> tuple[list[dict], list[str], list[dict]]:
    """Mỗi cột CSV ⇒ một biến SPSS. Trả (kế hoạch, cảnh báo, đề xuất mã thiếu).

    Ném TuChoi khi cột là định danh (Identifier?=y) hoặc tên cột nghi PII. Trường «notes» (văn bản tự do — dễ chứa tên,
    số điện thoại) bị bỏ khỏi .sav trừ khi giu_ghi_chu."""
    canh_bao: list[str] = []
    ke: list[dict] = []
    de_xuat: list[dict] = []
    dung: set[str] = set()
    so_ma_chu: dict[str, int] = {}
    for m in ma_thieu:  # BTR ⇒ −9991, KDD ⇒ −9992… GIỐNG NHAU ở mọi biến
        if _so(m["ma"]) is None and m["ma"] not in so_ma_chu:
            so_ma_chu[m["ma"]] = MA_CHU_BAT_DAU - len(so_ma_chu)
    for i, cot in enumerate(tieu_de):
        t = tk[i]
        goc = re.sub(r"___[^_].*$", "", cot)  # REDCap checkbox xuất thành <trường>___<mã>
        d = td.get(cot) or td.get(goc) or {}
        if d.get("dinh_danh", "").lower() in ("y", "yes", "1"):
            raise TuChoi(
                f"cột «{cot}» là trường ĐỊNH DANH (Identifier?=y) trong từ điển — "
                "bộ dữ liệu xuất SPSS phải khử định danh"
            )
        loai = d.get("loai", "").lower()
        bo_cot = loai == "notes" and not giu_ghi_chu
        ten = ten_spss_tu_chu_thich(d) if d and cot == goc else None
        if ten and not ten_hop_le(ten):
            canh_bao.append(f"«Tên SPSS: {ten}» của {cot} không hợp lệ — dùng tên gốc")
            ten = None
        ten = ten or chuan_ten(cot)
        if ten.upper() in dung:
            canh_bao.append(f"tên {ten} trùng — {cot} giữ tên chuẩn hoá có hậu tố")
            ten = chuan_ten(ten + "_" + str(i))
        dung.add(ten.upper())
        ap = [m for m in ma_thieu if _ap_cho_cot(m, cot, goc)]
        chu_co_mat = []  # mã chữ xuất hiện trong cột (thứ tự theo tệp mã thiếu, không trùng)
        for m in ap:
            if _so(m["ma"]) is None and m["ma"] in t["khong_so"] and m not in chu_co_mat:
                chu_co_mat.append(m)
        khong_so_con = t["khong_so"] - {m["ma"] for m in chu_co_mat}
        la_so = not khong_so_con
        ma_so_ap: dict[str, str] = {}
        for m in ap:
            if _so(m["ma"]) is not None:
                ma_so_ap.setdefault(_ma_so_gon(m["ma"]), m["nhan"])
        if d and cot != goc:  # cột checkbox
            lc = lua_chon(d)
            ma_cb = cot[len(goc) + 3 :]
            nhan = f"{bo_html(d.get('nhan', ''))}: {lc.get(ma_cb, ma_cb)}"
            nhan_gt = {"1": "Có", "0": "Không"}
            muc = "NOMINAL"
        else:
            nhan = bo_html(d.get("nhan", "")) or cot
            nhan_gt = lua_chon(d)
            giong_thieu = {k for k, v in nhan_gt.items() if _NHAN_GIONG_THIEU.search(v)}
            for k in sorted(giong_thieu - set(ma_so_ap), key=lambda x: (_so(x) is None, _so(x) or 0, x)):
                de_xuat.append({"bien": cot, "ma": k, "nhan": nhan_gt[k], "ly_do": "nhãn lựa chọn giống mã thiếu"})
            if not la_so:
                muc = "NOMINAL"
            elif loai in ("radio", "dropdown"):
                muc = "ORDINAL" if la_thang_thu_tu(nhan_gt, giong_thieu | set(ma_so_ap)) else "NOMINAL"
            elif loai in ("yesno", "truefalse", "checkbox"):
                muc = "NOMINAL"
            elif not d and not t["nhieu_muc"] and len(t["gia_tri"]) <= 2:
                muc = "NOMINAL"
            else:
                muc = "SCALE"
        if not d:
            canh_bao.append(f"cột «{cot}» không có trong từ điển G5 — nhãn = tên cột")
        if bo_cot:
            canh_bao.append(f"cột «{cot}» là văn bản tự do (notes) — KHÔNG đưa vào .sav (dùng --giu-ghi-chu nếu cần)")
        rong = t["rong"]
        if la_so:
            ma_chu = {m["ma"]: so_ma_chu[m["ma"]] for m in chu_co_mat}
            cap_thieu = [(k, v) for k, v in ma_so_ap.items()]
            cap_thieu += [(str(so_ma_chu[m["ma"]]), f"{m['ma']} — {m['nhan']}") for m in chu_co_mat]
            menh_de = None if bo_cot else menh_de_thieu_so(ten, list(ma_so_ap), list(ma_chu.values()))
            thieu_chuoi: list[str] = []
            if (
                ma_chu
            ):  # đọc dạng chuỗi rồi RECODE: độ rộng phải chứa được mã thay («-9991») — bản cũ A3 cắt thành «-99»
                rong = max(rong, *(len(str(v)) for v in ma_chu.values()))
        else:
            ma_chu = {}
            # Biến CHUỖI: ô rỗng là giá trị HỢP LỆ trong SPSS nhưng là thiếu (NaN) trong pandas ⇒ khai '' là thiếu.
            thieu_chuoi = ["", *[m["ma"] for m in chu_co_mat], *ma_so_ap]
            if len(thieu_chuoi) > 3 and not bo_cot:
                raise TuChoi(
                    f"{ten}: biến chuỗi có {len(thieu_chuoi)} mã thiếu (gồm ô rỗng) — SPSS chỉ khai được 3 giá trị rời"
                )
            cap_thieu = [(m["ma"], m["nhan"]) for m in chu_co_mat] + list(ma_so_ap.items())
            menh_de = None
            # nhãn giá trị dài hơn độ rộng biến bị SPSS bỏ (Warning #4487)
            rong = max(rong, *(len(k.encode("utf-8")) for k in [*nhan_gt, *(k for k, _ in cap_thieu)] or ["x"]))
        ke.append(
            {
                "cot": cot,
                "ten": ten,
                "so": la_so,
                "bo": bo_cot,
                "doc_chuoi_roi_doi": la_so and bool(ma_chu),
                "rong": rong,
                "le": min(t["le"], 8),
                "nguyen": t["nguyen"],
                "nhan": cat_byte(nhan, TRAN_NHAN_BIEN),
                "nhan_gia_tri": {k: cat_byte(v, TRAN_NHAN_GIA_TRI) for k, v in nhan_gt.items()},
                "muc_do": muc,
                "ma_chu": ma_chu,
                "ma_thieu": [(k, cat_byte(v, TRAN_NHAN_GIA_TRI)) for k, v in cap_thieu],
                "menh_de_thieu": menh_de,
                "thieu_chuoi": thieu_chuoi,
                "ma_thieu_so": list(ma_so_ap),
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
    pii = _quet_pii_ten([b["cot"] for b in ke if not b["bo"]])
    if pii:
        raise TuChoi("tên cột nghi định danh — khử định danh trước khi xuất SPSS: " + "; ".join(pii))
    if de_xuat:
        canh_bao.append(
            f"{len(de_xuat)} mã lựa chọn có nhãn giống mã thiếu (Không biết/Không nhớ/Từ chối…) CHƯA khai thiếu — "
            "xem spss/de-xuat-ma-thieu.csv; thống kê viên quyết, ghi vào _ma-thieu-theo-bien.csv (mẫu glob được)"
        )
    return ke, canh_bao, de_xuat


def _dinh_dang(b: dict) -> str:
    if b["so"] and not b["doc_chuoi_roi_doi"]:
        w = max(8, b["nguyen"] + b["le"] + 2)
        return f"F{w}.{b['le']}"
    return f"A{max(1, b['rong'])}"


def dinh_dang_cuoi(b: dict) -> str:
    """Định dạng SPSS CUỐI CÙNG của biến trong .sav (sau ALTER TYPE nếu đọc chuỗi rồi đổi) — cho format.spss .rds."""
    if b["so"]:
        return f"F{max(8, b['nguyen'] + b['le'] + 2)}.{b['le']}"
    return f"A{max(1, b['rong'])}"


def _chu_thich(s: str) -> str:
    """Một dòng chú thích SPSS. PHẢI kết thúc bằng dấu chấm: chú thích không có dấu chấm nuốt luôn lệnh kế tiếp (đo
    14/11/2026 — `SET UNICODE=ON.` của bản cũ không bao giờ chạy)."""
    s = re.sub(r"\s+", " ", s).strip()
    return "* " + (s if s.endswith(".") else s + ".")


def cu_phap_nhan_bien(csv_p: Path, sav_p: Path, ke: list[dict], *, ghi_chu: list[str]) -> str:
    dong = [
        _chu_thich("Sinh bởi tools/cau_noi_spss.py xuat-sav — KHÔNG sửa tay (sinh lại từ từ điển G5)."),
        *[_chu_thich(g) for g in ghi_chu],
        "SET UNICODE=ON.",
        "SET OLANG=ENGLISH.",
        f"GET DATA /TYPE=TXT /FILE={dd_spss(csv_p)} /ENCODING='UTF8'",
        '  /DELCASE=LINE /DELIMITERS="," /QUALIFIER=\'"\' /ARRANGEMENT=DELIMITED /FIRSTCASE=2',
        "  /VARIABLES=",
    ]
    dong += [f"    {b['ten']} {_dinh_dang(b)}" for b in ke]
    dong[-1] += "."
    giu = [b for b in ke if not b["bo"]]
    for b in giu:
        if b["doc_chuoi_roi_doi"]:
            ma = " ".join(f"('{k}'='{v}')" for k, v in b["ma_chu"].items())
            dong += [
                f"RECODE {b['ten']} {ma}.",
                f"ALTER TYPE {b['ten']} (F{max(8, b['nguyen'] + b['le'] + 2)}.{b['le']}).",
            ]
    dong.append("VARIABLE LABELS")
    dong += [f"  {'/' if k else ''}{b['ten']} {chuoi_spss(b['nhan'])}" for k, b in enumerate(giu)]
    dong[-1] += "."
    khoi_nhan = []
    for b in giu:
        cap = dict(b["nhan_gia_tri"])
        cap.update(dict(b["ma_thieu"]))
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
        ds = [b["ten"] for b in giu if b["muc_do"] == muc]
        if ds:
            dong.append(f"VARIABLE LEVEL {goi_ds(ds)} ({muc}).")
    for b in giu:
        if b["so"] and b["menh_de_thieu"]:
            dong.append(f"MISSING VALUES {b['ten']} ({b['menh_de_thieu']}).")
        elif not b["so"] and b["thieu_chuoi"]:
            gia = ", ".join("'" + x.replace("'", "''") + "'" for x in b["thieu_chuoi"])
            dong.append(f"MISSING VALUES {b['ten']} ({gia}).")
    bo = [b["ten"] for b in ke if b["bo"]]
    luu = f"SAVE OUTFILE={dd_spss(sav_p)} /COMPRESSED"
    luu += f"\n  /DROP={goi_ds(bo)}." if bo else "."
    dong += ["EXECUTE.", luu, ""]
    return "\n".join(dong)


# ───────────────────────────── khứ hồi từng ô (E3) + kiểm từ điển .sav (E2) ─────────────────────────────
#
# Luật GET DATA /TYPE=TXT (SPSS 31.0.1, SET UNICODE=ON, ENCODING='UTF8', DELIMITED) — ĐO THẬT 14/11/2026 bằng
# `spss_chay_nen.py --du-lieu`, không đoán:
#   · biến SỐ (F): độ rộng/số lẻ của định dạng KHÔNG cắt/làm tròn giá trị (F3.0 vẫn đọc đủ 123456789012 và
#     1.2345678901234567); ô rỗng hoặc chỉ dấu cách ⇒ SYSMIS; dấu cách đầu/cuối bỏ qua (« 2 » ⇒ 2); TAB không bỏ
#     («\t3» ⇒ SYSMIS); «NA», «nan», «Inf», «1_000», «3,5», «1,000», «$5», «5%», chữ số Ả Rập, số ngoài miền double
#     ⇒ SYSMIS; «1e3», «1E+02», «+5», «.5», «5.», «007», «-0» ⇒ như float(); «1d3» ⇒ 1000 (Python từ chối «1d3» nên
#     cột đó không bao giờ là biến số trong kế hoạch).
#   · bộ đọc số của SPSS KHÔNG làm tròn đúng tuyệt đối: 662/3000 số ngẫu nhiên 15–17 chữ số có nghĩa (hoặc số mũ lớn)
#     lệch float() của Python 1–6 ulp (R 4.6.2 lệch y hệt) ⇒ so số theo SAI_SO_ULP — lệch thật do hỏng dữ liệu không
#     bao giờ ở cỡ 1e-15 tương đối.
#   · biến CHUỖI (A): giữ khoảng trắng ĐẦU và tab; dấu cách CUỐI mất (đệm); quá độ rộng ⇒ cắt theo BYTE nhưng không cắt
#     giữa một ký tự («Việt» trong A4 ⇒ «Vi»); ô có nháy kép ("a""b", "x,y") đọc đúng.
#   · cấu trúc: dòng TRỐNG bị BỎ (csv.reader của Python trả một dòng rỗng ⇒ số ca lệch); dòng thiếu ô ⇒ ô cuối rỗng;
#     dòng thừa ô ⇒ phần thừa bị bỏ; ô có XUỐNG DÒNG trong nháy ⇒ SPSS TÁCH thành hai ca (dịch dòng) — Python đọc một ô.
#   · ALTER TYPE chuỗi → số dùng CÙNG bộ đọc số (kết quả trùng từng bit với đọc thẳng F).
SAI_SO_ULP = 8
TRAN_MAU_LECH = 20


def _gop(s) -> str:
    """Chuỗi đúng như SPSS nhận qua chuoi_spss(): gộp mọi khoảng trắng thành một dấu cách, bỏ đầu/cuối."""
    return re.sub(r"\s+", " ", str(s)).strip()


def doc_hang_csv(p: Path) -> tuple[list[str], list[list[str]]]:
    """Tiêu đề + mọi dòng dữ liệu, đọc ĐÚNG như quet_csv (utf-8-sig, csv.reader) — cùng số dòng với `so_ca_csv`."""
    with open(p, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        return next(r, []), list(r)


def gia_tri_ky_vong(b: dict, o: str | None) -> float | str | None:
    """Giá trị .sav/.rds PHẢI chứa cho ô nguồn `o` theo kế hoạch biến `b` (None = SYSMIS/NA).

    Biến số: ô rỗng/khoảng trắng ⇒ None; mã thiếu CHỮ (ma_chu) ⇒ mã số thay (−9991…); còn lại float(ô) — kế hoạch chỉ
    gọi một cột là SỐ khi MỌI giá trị (đã strip, như quet_csv) là số hữu hạn hoặc mã chữ đã khai. Biến chuỗi: ô gốc bỏ
    dấu cách CUỐI (SPSS đệm/bỏ dấu cách cuối; khoảng trắng đầu giữ nguyên); dòng thiếu ô ⇒ «»."""
    if b["so"]:
        s = (o or "").strip()
        if s == "":
            return None
        if s in b.get("ma_chu", {}):
            return float(b["ma_chu"][s])
        x = _so(s)
        return x
    return (o or "").rstrip(" ")


def _khop_so(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if a == b:
        return True
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    return abs(a - b) <= SAI_SO_ULP * math.ulp(max(abs(a), abs(b)))


_SO_NGUYEN_15 = re.compile(r"[+-]?[0-9]{1,15}")


def vuot_do_chinh_xac(o: str | None) -> bool:
    """Ô SỐ mà double (SPSS/R/pandas) KHÔNG lưu đúng được: giá trị thập phân ≠ giá trị của double gần nhất
    (vd 12345678901234567 ⇒ 12345678901234568). Ngưỡng ulp sẽ che lệch này ⇒ phải báo riêng. «0.1» không tính."""
    s = (o or "").strip()
    try:
        return Decimal(s) != Decimal(repr(float(s)))
    except (InvalidOperation, ValueError, OverflowError):
        return False


def khop_o(b: dict, ky_vong, nhan_duoc, o: str | None = None) -> bool:
    """`o` = ô nguồn: số NGUYÊN ≤ 15 chữ số (mã, số đếm) phải trùng TUYỆT ĐỐI — ngưỡng ulp chỉ cho số thực dài, nơi bộ
    đọc của SPSS/R lệch float() vài ulp (ở 1e15, 8 ulp = 1 đơn vị: 999999999999999 không được «khớp» 1e15)."""
    if b["so"]:
        if isinstance(nhan_duoc, str):
            return False
        nd = None if nhan_duoc is None else float(nhan_duoc)
        if o is not None and _SO_NGUYEN_15.fullmatch(o.strip()) and ky_vong is not None and nd is not None:
            return ky_vong == nd
        return _khop_so(ky_vong, nd)
    return isinstance(nhan_duoc, str) and nhan_duoc == ky_vong


def la_chu_tu_do(b: dict) -> bool:
    """Biến chuỗi KHÔNG có nhãn giá trị (văn bản tự do, mã phiếu…) ⇒ che giá trị trong báo cáo (có thể chứa PII)."""
    return not b["so"] and not b.get("nhan_gia_tri")


def _hien(b: dict, x) -> str:
    if x is None:
        return "SYSMIS/NA" if b["so"] else "∅"
    if isinstance(x, str):
        if la_chu_tu_do(b):
            return f"‹chuỗi {len(x)} ký tự · {len(x.encode('utf-8'))} byte›"
        return repr(x)
    return repr(float(x))


def _loai_lech(b: dict, ky_vong, nhan_duoc) -> str:
    if b["so"]:
        if isinstance(nhan_duoc, str):
            return "biến số thành chuỗi"
        if ky_vong is not None and nhan_duoc is None:
            return "mất số (đọc thành SYSMIS — ký tự lạ, dấu phẩy thập phân, tab, chữ số không phải ASCII?)"
        if ky_vong is None:
            return "ô trống thành số"
        return "lệch số"
    if not isinstance(nhan_duoc, str):
        return "mất chuỗi"
    kv_b, nd_b = ky_vong.encode("utf-8"), nhan_duoc.encode("utf-8")
    if len(nd_b) < len(kv_b) and ky_vong.startswith(nhan_duoc):
        return f"cắt cụt theo độ rộng (A{b.get('rong', '?')}: {len(kv_b)} → {len(nd_b)} byte)"
    if "�" in nhan_duoc:
        return "hỏng mã hoá (ký tự thay U+FFFD)"
    for ma in ("cp1252", "latin-1"):
        try:
            if kv_b.decode(ma) == nhan_duoc:
                return f"hỏng mã hoá tiếng Việt (UTF-8 đọc thành {ma})"
        except UnicodeDecodeError:
            continue
    import unicodedata

    if unicodedata.normalize("NFC", ky_vong) == unicodedata.normalize("NFC", nhan_duoc):
        return "khác dạng chuẩn hoá Unicode (NFC/NFD)"
    if nhan_duoc.strip() == ky_vong.strip():
        return "khác khoảng trắng đầu"
    return "lệch chuỗi"


def so_sanh_gia_tri(
    csv_p: Path, ke: list[dict], bien: list[str], ca: list[list], *, tran_mau: int = TRAN_MAU_LECH
) -> dict:
    """So TỪNG biến giữ lại × TỪNG ca của bản đọc lại (.sav qua spss.Cursor, hoặc .rds qua R) với giá trị kỳ vọng suy từ
    CSV nguồn qua CÙNG kế hoạch biến `ke`. Ca i của bản đọc lại phải khớp dòng dữ liệu i của CSV (thứ tự giữ nguyên).

    Trả {trang_thai KHOP|LECH, so_o, so_lech, so_ca_nguon, so_ca_doc, so_bien, mau_lech[≤ tran_mau] (giá trị biến chữ tự
    do đã che), lech_theo_bien, ghi_chu}."""
    giu = [b for b in ke if not b["bo"]]
    tieu_de, hang = doc_hang_csv(csv_p)
    cot = {c: i for i, c in enumerate(tieu_de)}
    vi_tri = {t: j for j, t in enumerate(bien)}
    so_o, so_lech, mau, theo_bien, ghi_chu = len(hang) * len(giu), 0, [], {}, []

    def ghi(i: int, b: dict, kv, nd, loai: str | None = None) -> None:
        nonlocal so_lech
        so_lech += 1
        theo_bien[b["ten"]] = theo_bien.get(b["ten"], 0) + 1
        if len(mau) < tran_mau:
            mau.append(
                {
                    "ca": i + 1,
                    "bien": b["ten"],
                    "ky_vong": _hien(b, kv),
                    "nhan_duoc": _hien(b, nd) if loai is None else "—",
                    "loai": loai or _loai_lech(b, kv, nd),
                }
            )

    thieu_bien = [b["ten"] for b in giu if b["ten"] not in vi_tri or b["cot"] not in cot]
    if thieu_bien:
        ghi_chu.append("biến có trong kế hoạch nhưng KHÔNG có trong bản đọc lại: " + ", ".join(thieu_bien[:12]))
    dau_lech: int | None = None
    for i, dong in enumerate(hang):
        hang_doc = ca[i] if i < len(ca) else None
        for b in giu:
            ci = cot.get(b["cot"])
            o = dong[ci] if ci is not None and ci < len(dong) else None
            kv = gia_tri_ky_vong(b, o)
            if hang_doc is None:
                ghi(i, b, kv, None, "thiếu ca trong bản đọc lại")
            elif b["ten"] not in vi_tri:
                ghi(i, b, kv, None, "thiếu biến trong bản đọc lại")
            elif b["so"] and o is not None and o.strip() not in b.get("ma_chu", {}) and vuot_do_chinh_xac(o):
                ghi(i, b, kv, hang_doc[vi_tri[b["ten"]]], "vượt độ chính xác double (> 15 chữ số có nghĩa) — .sav/.rds "
                    "lưu giá trị KHÁC nguồn; nếu là MÃ, giữ dạng chữ ở nguồn")  # fmt: skip
            elif not khop_o(b, kv, hang_doc[vi_tri[b["ten"]]], o):
                ghi(i, b, kv, hang_doc[vi_tri[b["ten"]]])
            else:
                continue
            if dau_lech is None:
                dau_lech = i
    for i in range(len(hang), len(ca)):  # bản đọc lại THỪA ca (ô nhiều dòng bị tách, …)
        so_lech += 1
        if len(mau) < tran_mau:
            mau.append({"ca": i + 1, "bien": "*", "ky_vong": "—", "nhan_duoc": "ca thừa", "loai": "thừa ca"})
        dau_lech = len(hang) if dau_lech is None else dau_lech
    if len(ca) != len(hang):
        ghi_chu.append(f"số ca: CSV {len(hang)} dòng dữ liệu, bản đọc lại {len(ca)} ca")

    def khop_hang(i_ca: int, i_nguon: int) -> bool:
        """Ca i_ca của bản đọc lại khớp TRỌN dòng nguồn i_nguon (mọi biến)?"""
        if not (0 <= i_ca < len(ca) and 0 <= i_nguon < len(hang)):
            return False
        d = hang[i_nguon]
        return all(
            b["ten"] in vi_tri
            and khop_o(
                b,
                gia_tri_ky_vong(b, d[cot[b["cot"]]] if cot[b["cot"]] < len(d) else None),
                ca[i_ca][vi_tri[b["ten"]]],
                d[cot[b["cot"]]] if cot[b["cot"]] < len(d) else None,
            )
            for b in giu
            if b["cot"] in cot
        )

    if dau_lech is not None and dau_lech < min(len(hang), len(ca)):
        r = dau_lech
        if khop_hang(r, r + 1) or khop_hang(r + 1, r + 2):  # bản đọc lại thiếu một dòng nguồn
            ghi_chu.append(f"nghi DỊCH DÒNG từ ca {r + 1}: bản đọc lại đã BỎ một dòng (dòng trống?)")
        elif khop_hang(r + 1, r) or khop_hang(r + 2, r + 1):  # bản đọc lại thêm một ca (một ô bị tách đôi)
            ghi_chu.append(f"nghi DỊCH DÒNG từ ca {r + 1}: bản đọc lại đã CHÈN thêm một ca (ô có xuống dòng bị tách?)")
    so_0_dau = [
        b["ten"]
        for b in giu
        if b["so"]
        and b["cot"] in cot
        and any(
            re.match(r"[+-]?0\d", (d[cot[b["cot"]]] if cot[b["cot"]] < len(d) else "").strip())
            and (d[cot[b["cot"]]].strip() not in b.get("ma_chu", {}))
            for d in hang
        )
    ]
    if so_0_dau:  # TƯ VẤN, không tính lệch: pandas cũng đọc «007» thành 7
        ghi_chu.append(
            "biến SỐ có giá trị mang số 0 đứng đầu (vd «007») — .sav/.rds lưu dạng số nên mất số 0 đầu; nếu đó là MÃ "
            "(mã vùng, mã phiếu) hãy giữ dạng chữ ở nguồn: " + ", ".join(so_0_dau[:12])
        )
    return {
        "trang_thai": "KHOP" if so_lech == 0 else "LECH",
        "so_o": so_o,
        "so_lech": so_lech,
        "so_ca_nguon": len(hang),
        "so_ca_doc": len(ca),
        "so_bien": len(giu),
        "sai_so_ulp": SAI_SO_ULP,
        "mau_lech": mau,
        "lech_theo_bien": theo_bien,
        "ghi_chu": ghi_chu,
    }


def bao_cao_lech(kq: dict, *, tieu_de: str, tran: int = 10) -> list[str]:
    """Báo cáo gọn: N lệch đầu (ca · biến · kỳ vọng · nhận được · loại) + ghi chú. Giá trị biến chữ tự do đã che."""
    dong = [f"{tieu_de}: {kq.get('so_lech', 0)} ô lệch / {kq.get('so_o', 0)} ô"]
    for m in (kq.get("mau_lech") or [])[:tran]:
        dong.append(f"   ca {m['ca']} · {m['bien']}: kỳ vọng {m['ky_vong']} — nhận {m['nhan_duoc']} ({m['loai']})")
    con = kq.get("so_lech", 0) - min(tran, len(kq.get("mau_lech") or []))
    if con > 0:
        dong.append(f"   … còn {con} ô lệch (theo biến: {kq.get('lech_theo_bien')})")
    dong += [f"   • {g}" for g in kq.get("ghi_chu") or []]
    return dong


def ky_vong_nhan_gia_tri(b: dict) -> dict:
    """Nhãn giá trị .sav PHẢI có theo kế hoạch — cùng luật cu_phap_nhan_bien(): nhãn lựa chọn + nhãn mã thiếu (mã thiếu
    ghi sau nên thắng khi trùng mã); biến số bỏ mã chữ; nhãn gộp khoảng trắng như chuoi_spss()."""
    cap = dict(b["nhan_gia_tri"])
    cap.update(dict(b["ma_thieu"]))
    ra: dict = {}
    for ma, nhan in cap.items():
        if b["so"]:
            x = _so(ma)
            if x is not None:
                ra[x] = _gop(nhan)
        else:
            ra[ma.rstrip(" ")] = _gop(nhan)
    return ra


def _gia_tri_thieu(x, so: bool):
    if isinstance(x, str) and x.strip() in ("LO", "HI", "LOWEST", "HIGHEST"):
        return "LO" if x.strip().startswith("LO") else "HI"
    return float(x) if so else str(x).rstrip(" ")


def ky_vong_thieu(b: dict) -> dict:
    """MISSING VALUES theo kế hoạch ⇒ {roi: [giá trị rời, đã xếp], khoang: [thấp, cao] | None} (LO/HI giữ chữ)."""
    if not b["so"]:
        return {"roi": sorted(x.rstrip(" ") for x in b.get("thieu_chuoi") or []), "khoang": None}
    roi, khoang = [], None
    for t in (b.get("menh_de_thieu") or "").split(","):
        t = t.strip()
        if not t:
            continue
        if " THRU " in t:
            lo, hi = t.split(" THRU ", 1)
            khoang = [_gia_tri_thieu(lo, True), _gia_tri_thieu(hi, True)]
        else:
            roi.append(float(t))
    return {"roi": sorted(roi), "khoang": khoang}


def thieu_tu_spss(th: list | None, so: bool) -> dict:
    """missingValues của spss.Dataset ([kiểu, a, b, c] — kiểu 1–3 rời, −2 khoảng, −3 khoảng + rời) ⇒ cùng khuôn
    ky_vong_thieu. Chuỗi bỏ dấu cách đệm (SPSS lưu mã thiếu chuỗi đệm tới 8 byte)."""
    th = list(th or [0])
    k = int(th[0] or 0)
    if k in (-2, -3):
        roi = [_gia_tri_thieu(th[3], so)] if k == -3 and len(th) > 3 and th[3] is not None else []
        return {"roi": sorted(roi), "khoang": [_gia_tri_thieu(th[1], so), _gia_tri_thieu(th[2], so)]}
    return {"roi": sorted(_gia_tri_thieu(x, so) for x in th[1 : 1 + max(0, k)] if x is not None), "khoang": None}


def kiem_tu_dien_sav(ke: list[dict], td: dict) -> dict:
    """Từ điển .sav (dump `--tu-dien`) so với kế hoạch: tên + thứ tự biến, số/chuỗi (và độ rộng A), nhãn biến, nhãn giá
    trị (cả nhãn mã thiếu), MISSING VALUES, mức đo. Trả {trang_thai KHOP|LECH, so_lech, lech[...]}."""
    giu = [b for b in ke if not b["bo"]]
    ds = td.get("bien") or []
    lech: list[str] = []
    ten_ke, ten_sav = [b["ten"] for b in giu], [v.get("ten") for v in ds]
    if ten_ke != ten_sav:
        thieu = [t for t in ten_ke if t not in ten_sav]
        thua = [t for t in ten_sav if t not in ten_ke]
        lech.append(
            "tên/thứ tự biến khác kế hoạch"
            + (f" — thiếu: {', '.join(thieu[:8])}" if thieu else "")
            + (f" — thừa: {', '.join(str(t) for t in thua[:8])}" if thua else "")
            + (" — cùng tập biến nhưng KHÁC thứ tự" if not thieu and not thua else "")
        )
    theo_ten = {v.get("ten"): v for v in ds}
    for b in giu:
        v = theo_ten.get(b["ten"])
        if v is None:
            continue
        kieu = v.get("kieu")
        if b["so"] and kieu != 0:
            lech.append(f"{b['ten']}: kế hoạch là biến SỐ nhưng .sav là chuỗi (A{kieu})")
            continue
        if not b["so"] and kieu != max(1, b["rong"]):
            lech.append(f"{b['ten']}: kế hoạch là chuỗi A{max(1, b['rong'])} nhưng .sav có kiểu {kieu}")
        if (v.get("nhan") or "") != _gop(b["nhan"]):
            lech.append(f"{b['ten']}: nhãn biến khác kế hoạch")
        ngt = {}
        for k, nhan in (v.get("nhan_gia_tri") or {}).items():
            ngt[float(k) if b["so"] else str(k).rstrip(" ")] = nhan
        kv = ky_vong_nhan_gia_tri(b)
        if ngt != kv:
            thieu = sorted(str(k) for k in set(kv) - set(ngt))
            thua = sorted(str(k) for k in set(ngt) - set(kv))
            sai = sorted(str(k) for k in set(kv) & set(ngt) if kv[k] != ngt[k])
            lech.append(
                f"{b['ten']}: nhãn giá trị khác kế hoạch"
                + (f" — thiếu mã {', '.join(thieu[:8])}" if thieu else "")
                + (f" — thừa mã {', '.join(thua[:8])}" if thua else "")
                + (f" — sai nhãn mã {', '.join(sai[:8])}" if sai else "")
            )
        if thieu_tu_spss(v.get("thieu"), b["so"]) != ky_vong_thieu(b):
            lech.append(
                f"{b['ten']}: MISSING VALUES khác kế hoạch (kỳ vọng {ky_vong_thieu(b)} — .sav "
                f"{thieu_tu_spss(v.get('thieu'), b['so'])})"
            )
        if str(v.get("muc_do") or "").upper() != b["muc_do"]:
            lech.append(f"{b['ten']}: mức đo {v.get('muc_do')} khác kế hoạch {b['muc_do']}")
    return {"trang_thai": "KHOP" if not lech else "LECH", "so_lech": len(lech), "lech": lech}


def doc_lai_sav(py: Path, thu_muc: Path, sav: Path, csv_p: Path, ke: list[dict]) -> dict:
    """MỘT lượt SPSS đọc lại .sav vừa tạo (`--du-lieu` kèm từ điển) ⇒ {khu_hoi, kiem_tu_dien, loi, out, err}."""
    p_dl, p_td = thu_muc / "doc_lai_du_lieu.json", thu_muc / "doc_lai_tu_dien.json"
    ma, out, err = chay_spss(py, ["--du-lieu", str(sav), str(p_dl), str(p_td)], thu_muc=thu_muc)
    luc = datetime.now().astimezone().isoformat(timespec="seconds")
    dl, td = _doc_json(p_dl), _doc_json(p_td)
    if ma != 0 or not dl or not td:
        ly_do = "SPSS không đọc lại được .sav vừa tạo — " + ((err or out).strip()[-400:] or f"mã {ma}")
        loi = {"trang_thai": "LOI", "ly_do": ly_do, "luc": luc}
        return {"khu_hoi": loi, "kiem_tu_dien": dict(loi), "loi": ly_do, "out": out, "err": err}
    kh = so_sanh_gia_tri(csv_p, ke, list(dl.get("bien") or []), list(dl.get("ca") or []))
    ktd = kiem_tu_dien_sav(ke, td)
    kh["luc"] = ktd["luc"] = luc
    return {"khu_hoi": kh, "kiem_tu_dien": ktd, "loi": None, "out": out, "err": err}


# ───────────────────────────── lệnh xuat-sav ─────────────────────────────


def tim_du_lieu_khoa(study: str) -> tuple[Path, dict]:
    """Bộ dữ liệu đã khoá + manifest khoá — kiểm bằng ĐÚNG hàm của cổng (gate_contract.locked_analysis_dataset_blockers,
    dùng chung với run_stats_analysis.py): status LOCKED_FOR_ANALYSIS · analysis_allowed · có và khớp SHA-256."""
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
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gate_contract import locked_analysis_dataset_blockers

    chan, _ = locked_analysis_dataset_blockers(study, str(p), repo_root=EXPORTS.parent)
    if chan:
        if "locked_dataset_checksum_mismatch" in chan:
            raise TuChoi("SHA-256 bộ dữ liệu khoá KHÔNG khớp manifest — dữ liệu đã bị đổi sau khi khoá; dừng")
        raise TuChoi("bộ dữ liệu chưa qua cổng khoá (" + ", ".join(chan) + ") — dùng --data … --ban-nhap cho bản nháp")
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
    _, hang_csv = doc_hang_csv(csv_p)
    nhieu_dong = [
        f"dòng {i + 1} · {tieu_de[j] if j < len(tieu_de) else f'cột {j + 1}'}"
        for i, d in enumerate(hang_csv)
        for j, o in enumerate(d)
        if "\n" in o or "\r" in o
    ]
    # SPSS GET DATA tách ô nhiều dòng thành HAI ca ⇒ dịch dòng (đo thật 14/11/2026) — chặn TRƯỚC khi chạy
    if nhieu_dong:
        raise TuChoi(
            f"{len(nhieu_dong)} ô có XUỐNG DÒNG — SPSS sẽ tách thành hai ca: "
            + "; ".join(nhieu_dong[:10])
            + (" …" if len(nhieu_dong) > 10 else "")
            + ". Thay xuống dòng ở nguồn (nhap_lieu_excel báo «xuong_dong_trong_o») rồi chạy lại"
        )
    ke, canh_bao, de_xuat = ke_hoach_bien(tieu_de, tk, td, mt, giu_ghi_chu=getattr(args, "giu_ghi_chu", False))
    ra = d / "spss"
    ra.mkdir(parents=True, exist_ok=True)
    hau_to = "_BAN-NHAP" if args.ban_nhap else "_khoa"
    sav_p, sps_p = (
        ra / f"{args.study}{hau_to}.sav",
        ra / f"{args.study}_nhan_bien{'_ban-nhap' if args.ban_nhap else ''}.sps",
    )
    sha_nguon = sha256_tep(csv_p)
    ghi_chu = [
        f"Nguồn: {csv_p.name} · SHA-256 {sha_nguon[:16]}… · {n} ca · {sum(1 for b in ke if not b['bo'])} biến",
        "Bản NHÁP — chưa khoá"
        if args.ban_nhap
        else f"Khoá ngày {man.get('lock_date', '?')} · SAP {man.get('sap_version', '?')}",
    ]
    sps_p.write_text(cu_phap_nhan_bien(csv_p, sav_p, ke, ghi_chu=ghi_chu), encoding="utf-8", newline="\n")
    print(f"✓ Cú pháp nhãn biến: {sps_p}")
    dx_p = ra / "de-xuat-ma-thieu.csv"
    if de_xuat:
        with open(dx_p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, ["bien", "ma", "nhan", "ly_do"], lineterminator="\n")
            w.writeheader()
            w.writerows(de_xuat)
    elif dx_p.exists():
        dx_p.unlink()
    for c in canh_bao:
        print(f"  ⚠ {c}")
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "ban_nhap": bool(args.ban_nhap),
        "nguon_csv": str(csv_p),
        "sha256_nguon": sha_nguon,
        "manifest_khoa": {k: man.get(k) for k in ("lock_date", "sap_version", "sha256", "approved_by")},
        "tu_dien": str(td_p),
        "sha256_tu_dien": sha256_tep(td_p),
        "ma_thieu": str(mt_p) if mt else None,
        "so_ca_csv": n,
        "cu_phap": str(sps_p),
        "sav": str(sav_p),
        "sav_da_tao": False,
        "canh_bao": canh_bao,
        "bien": [
            {k: b[k] for k in ("cot", "ten", "so", "muc_do", "nhan", "muc", "ma_chu", "ma_thieu_so")}
            for b in ke
            if not b["bo"]
        ],
        "bien_bo": [b["cot"] for b in ke if b["bo"]],
        "disclaimer": CAN_KIEM,
    }
    man_sav = ra / f"{sav_p.name}.manifest.json"
    try:
        py = tim_spss()
    except KhongDoDuoc as e:
        man_sav.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"⚪ {e}\n   Mở {sps_p.name} trong SPSS và Run All để tạo {sav_p.name}.")
        return MA_KHONG_DO
    if sav_p.exists():
        os.chmod(sav_p, stat.S_IWUSR | stat.S_IRUSR)
        sav_p.unlink()
    if man_sav.exists():
        man_sav.unlink()  # manifest cũ không được sống sót qua một lượt tạo .sav hỏng
    doc_lai: dict | None = None
    da_tao = False
    with vung_tam() as tam_s:
        tam = Path(tam_s)
        shutil.copyfile(csv_p, tam / "du_lieu.csv")
        (tam / "nhan_bien.sps").write_text(
            cu_phap_nhan_bien(tam / "du_lieu.csv", tam / "ra.sav", ke, ghi_chu=ghi_chu), encoding="utf-8", newline="\n"
        )
        ma, out, err = chay_spss(py, ["--cu-phap", str(tam / "nhan_bien.sps")], thu_muc=tam)
        so_ca = _gia_tri_dong(out, "SO_CA")
        da_tao = ma == 0 and (tam / "ra.sav").exists()
        if da_tao and (so_ca is None or so_ca == str(n)):
            # E3 + E2: đọc lại .sav NGAY TRONG vùng tạm — chỉ tệp qua cả hai phép kiểm mới được chuyển về exports/.
            doc_lai = doc_lai_sav(py, tam, tam / "ra.sav", tam / "du_lieu.csv", ke)
            if doc_lai["khu_hoi"]["trang_thai"] == "KHOP" and doc_lai["kiem_tu_dien"]["trang_thai"] == "KHOP":
                shutil.move(str(tam / "ra.sav"), sav_p)
    nhat_ky = out + ("\n--- stderr ---\n" + err if err else "")
    if doc_lai:
        nhat_ky += "\n--- đọc lại .sav (--du-lieu) ---\n" + doc_lai["out"]
        nhat_ky += "\n--- stderr ---\n" + doc_lai["err"] if doc_lai["err"] else ""
    (ra / f"{sps_p.stem}.log").write_text(nhat_ky, encoding="utf-8", newline="\n")
    if not da_tao:
        print("🔴 SPSS báo lỗi khi tạo .sav —", (err or out).strip()[-800:])
        return MA_LECH
    if so_ca is not None and so_ca != str(n):
        print(f"🔴 Số ca trong .sav ({so_ca}) khác số dòng CSV ({n}) — không dùng tệp này")
        return MA_LECH
    if doc_lai is None:  # không thể xảy ra (đã tạo + đúng số ca ⇒ đã đọc lại) — giữ cho chắc, không nhận tệp
        return MA_LECH
    ket.update({"khu_hoi": doc_lai["khu_hoi"], "kiem_tu_dien": doc_lai["kiem_tu_dien"]})
    if not sav_p.exists():  # khứ hồi/từ điển LỆCH hoặc không đọc lại được ⇒ .sav đã bị bỏ cùng vùng tạm
        man_sav.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        if doc_lai["loi"]:
            print(f"🔴 {doc_lai['loi']} — không nhận tệp chưa kiểm được")
            return MA_LECH
        print("🔴 .sav KHÔNG khớp nguồn — đã bỏ tệp, không dùng (chi tiết trong manifest, mục khu_hoi/kiem_tu_dien):")
        if doc_lai["khu_hoi"]["trang_thai"] != "KHOP":
            print("\n".join(bao_cao_lech(doc_lai["khu_hoi"], tieu_de="  Khứ hồi từng ô (E3)")))
        if doc_lai["kiem_tu_dien"]["trang_thai"] != "KHOP":
            print(f"  Từ điển .sav ↔ kế hoạch (E2): {doc_lai['kiem_tu_dien']['so_lech']} điểm lệch")
            print("\n".join(f"   • {x}" for x in doc_lai["kiem_tu_dien"]["lech"][:12]))
        return MA_LECH
    os.chmod(sav_p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    ket.update(
        {
            "sav_da_tao": True,
            "sha256_sav": sha256_tep(sav_p),
            "so_ca_sav": int(so_ca) if so_ca else None,
            "spss_phien_ban": _gia_tri_dong(out, "PHIEN_BAN") or phien_ban_tu_goi(py),
        }
    )
    man_sav.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    kh = doc_lai["khu_hoi"]
    print(f"✓ {sav_p} — {so_ca} ca · {len(ket['bien'])} biến (chỉ đọc) · manifest {man_sav.name}")
    print(
        f"✓ Khứ hồi từng ô (E3): {kh['so_o']} ô khớp nguồn · từ điển .sav khớp kế hoạch (E2: tên, nhãn biến, nhãn giá "
        "trị, MISSING VALUES, mức đo)"
    )
    for g in kh.get("ghi_chu") or []:
        print(f"  ⚠ {g}")
    return MA_OK


# ───────────────────────────── lệnh cu-phap ─────────────────────────────


def _doc_manifest_sav(study: str, *, can_sav: bool = True) -> dict:
    """Manifest của .sav đã tạo — ưu tiên bản KHOÁ. can_sav: tệp .sav phải thật sự đã tạo (khớp SHA-256)."""
    d = thu_muc_de_tai(study) / "spss"
    for ten in (f"{study}_khoa.sav.manifest.json", f"{study}_BAN-NHAP.sav.manifest.json"):
        m = _doc_json(d / ten)
        if not m:
            continue
        sav = Path(m.get("sav") or "")
        if can_sav and not (m.get("sav_da_tao", True) and sav.is_file()):
            continue
        return m
    raise KhongDoDuoc(f"chưa có .sav của {study} — chạy `cau_noi_spss.py xuat-sav --study {study}` trước")


def them_bien_phai_sinh(study: str, man: dict, gate: str) -> dict:
    """F1 (14/11/2026): lượt Python dùng biến phái sinh (khoá bien_phai_sinh của <gate>_analysis_summary.json) ⇒ trả
    manifest MỞ RỘNG: thêm các biến đó như thể có trong .sav (tên = tên biến, biến số, mức giá trị tính từ dữ liệu khoá)
    và khoá `khoi_phai_sinh` = cú pháp SPSS tự tính lại ĐỘC LẬP từ cùng công thức (chèn ngay sau GET FILE). Không dùng
    ⇒ trả nguyên manifest. Công thức đổi sau lượt Python ⇒ TuChoi."""
    tom = _doc_json(thu_muc_de_tai(study) / f"{gate}_analysis_summary.json")
    if not ((tom.get("bien_phai_sinh") or {}).get("bien")):
        return man
    import bien_phai_sinh as BPS  # noqa: PLC0415

    csv_khoa = Path(man.get("nguon_csv") or "")
    if not csv_khoa.is_file():
        raise KhongDoDuoc(f"manifest .sav không trỏ tới CSV nguồn đọc được ({csv_khoa}) — không tính biến phái sinh")
    ten_spss = {b["cot"]: (b["ten"], bool(b["so"])) for b in man["bien"] if not b.get("bo")}
    try:
        khoi, ds, muc = BPS.khoi_cho_cau_noi(
            thu_muc_de_tai(study), tom, "spss", csv_khoa, ten_spss=ten_spss, dang_co={b["ten"] for b in man["bien"]}
        )
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"biến phái sinh: {e}") from e
    trung = sorted(t for t in ds if t.upper() in {b["ten"].upper() for b in man["bien"]})
    if trung:
        raise TuChoi(f"biến phái sinh trùng tên biến SPSS đã có trong .sav: {', '.join(trung)}")
    man2 = dict(man)
    man2["bien"] = list(man["bien"]) + [
        {"cot": t, "ten": t, "so": True, "bo": False, "muc": muc.get(t), "nhan": t, "nhan_gia_tri": {}, "ma_chu": {},
         "ma_thieu_so": [], "phai_sinh": True}
        for t in ds
    ]  # fmt: skip
    man2["khoi_phai_sinh"] = khoi
    return man2


def them_loc(study: str, man: dict, gate: str) -> dict:
    """F3 (14/11/2026): lượt Python lọc quần thể (dac_ta_phan_tich.loc) ⇒ manifest có khoá `khoi_loc` = cú pháp SPSS lọc
    Y HỆT (cùng biểu thức, cùng cột ngày; SELECT IF giữ ca = 1) — chèn sau khối biến phái sinh, trước biến giả."""
    tom = _doc_json(thu_muc_de_tai(study) / f"{gate}_analysis_summary.json")
    if not ((tom.get("dac_ta_phan_tich") or {}).get("loc")):
        return man
    import bien_phai_sinh as BPS  # noqa: PLC0415

    ten_spss = {b["cot"]: (b["ten"], bool(b["so"])) for b in man["bien"] if not b.get("bo")}
    try:
        khoi = BPS.khoi_loc_cau_noi(tom, "spss", ten_spss=ten_spss, dang_co={b["ten"] for b in man["bien"]})
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"lọc quần thể: {e}") from e
    man2 = dict(man)
    man2["khoi_loc"] = khoi
    return man2


def them_bien_gia(man: dict, dt: dict) -> dict:
    """F2 (14/11/2026): biến giả TƯỜNG MINH cho hiệp biến phân loại (dt["hiep_bien_phan_loai"] từ tóm tắt Python) ⇒
    manifest mở rộng (biến giả như biến số trong .sav) + khoá `khoi_bien_gia` = cú pháp COMPUTE chèn sau GET FILE (sau
    khối biến phái sinh — biến phái sinh cũng có thể là biến phân loại). Biến giả thiếu khi biến gốc thiếu."""
    bg = dt.get("hiep_bien_phan_loai") or {}
    if not bg:
        return man
    bien = {b["cot"]: b for b in man["bien"]}
    co = {b["ten"].upper() for b in man["bien"]}
    lenh: list[str] = []
    them: list[dict] = []
    for c, v in bg.items():
        b = bien.get(c)
        if b is None:
            raise TuChoi(f"hiệp biến phân loại «{c}» không có trong .sav")
        if not b["so"]:
            raise TuChoi(f"hiệp biến phân loại «{c}» là biến CHUỖI trong .sav — cần mã số")
        for muc, t in zip(v["muc"], v["ten"]):
            if not ten_hop_le(t) or t.upper() in co:
                raise TuChoi(f"biến giả «{t}» không hợp lệ hoặc trùng tên biến đã có trong .sav")
            lenh += [f"COMPUTE {t} = $SYSMIS.", f"IF (NOT MISSING({b['ten']})) {t} = ({b['ten']} = {muc})."]
            them.append({"cot": t, "ten": t, "so": True, "bo": False, "muc": ["0", "1"],
                         "nhan": f"{c} = {muc} (so với {v['tham_chieu']})", "nhan_gia_tri": {}, "ma_chu": {},
                         "ma_thieu_so": [], "bien_gia": True})  # fmt: skip
            co.add(t.upper())
    man2 = dict(man)
    man2["bien"] = list(man["bien"]) + them
    man2["khoi_bien_gia"] = "\n".join(
        ["* Biến giả hiệp biến phân loại (tham chiếu = mã nhỏ nhất) — khớp run_stats_analysis.py.", *lenh, "EXECUTE."]
    )
    return man2


def dac_ta(args) -> dict:
    tom_day_du = _doc_json(thu_muc_de_tai(args.study) / f"{args.gate}_analysis_summary.json")
    tom = tom_day_du.get("dac_ta_phan_tich") or {}
    dt = {
        k: getattr(args, k, None) or tom.get(k)
        for k in ("outcome", "group", "outcome_type", "time", "event", "cot_cum")
    }
    cov = getattr(args, "covariates", None)
    dt["covariates"] = [c.strip() for c in cov.split(",") if c.strip()] if cov else list(tom.get("covariates") or [])
    dt["outcome_type"] = dt["outcome_type"] or "auto"
    # F2: biến giả của hiệp biến phân loại — đúng các mức Python đã dùng (tên hệ số trùng nhau ở cả ba phần mềm)
    bg = tom.get("hiep_bien_phan_loai") or {}
    dt["hiep_bien_phan_loai"] = {c: v for c, v in bg.items() if c in dt["covariates"]}
    dt["loc"] = tom.get("loc")  # F3: quần thể phân tích của lượt Python (để kiểm lệch đặc tả)
    pl = dt["hiep_bien_phan_loai"]
    dt["covariates_mo_hinh"] = [t for c in dt["covariates"] for t in (pl[c]["ten"] if c in pl else [c])]
    # OR theo MỖI k đơn vị phơi nhiễm (C1a: mỗi 15 phút chờ) — thiếu thì SPSS tính theo mỗi phút ⇒ «lệch» giả
    dv = getattr(args, "don_vi_phoi_nhiem", None)
    if dv is None:
        dv = tom.get("don_vi_phoi_nhiem")
    if dv is None:
        dv = ((tom_day_du.get("ordinal") or {}).get("don_vi_phoi_nhiem") or {}).get("don_vi")
    if dv is not None and (not isinstance(dv, (int, float)) or dv <= 0):
        raise TuChoi(f"đơn vị phơi nhiễm phải > 0 (đang là {dv!r})")
    dt["don_vi_phoi_nhiem"] = dv
    # Phân tích bổ sung (mở rộng 14/11/2026)
    thang: dict[str, list[str]] = {}
    for x in getattr(args, "thang_do", None) or []:
        if ":" not in x:
            raise TuChoi(f"--thang-do cần dạng «TÊN:mục1,mục2,…» (đang là {x!r})")
        tn, ds = x.split(":", 1)
        thang[tn.strip()] = [c.strip() for c in ds.split(",") if c.strip()]
    dt["thang_do"] = thang
    dt["hon_hop"] = not getattr(args, "khong_hon_hop", False)
    ts = (_doc_json(thu_muc_de_tai(args.study) / f"{args.gate}_checkpoint.json").get("trong_so")) or {}
    dt["trong_so"] = None
    if ts.get("can_trong_so") and not getattr(args, "khong_trong_so", False):
        if ts.get("thieu"):
            print(f"  ⚠ trọng số: SAP/dictionary chưa cho {', '.join(ts['thieu'])} — bỏ khối Complex Samples")
        else:
            dt["trong_so"] = {k: v for k, v in ts.items() if k not in ("thieu", "can_trong_so")}
    return dt


def cu_phap_phan_tich(
    study: str,
    man: dict,
    dt: dict,
    thu_muc_kq: Path,
    *,
    sav: Path | str | None = None,
    bien_bang1: list[str] | None = None,
) -> tuple[str, list[str], dict]:
    """Cú pháp phân tích SPSS khớp đặc tả G6. Trả (cú pháp, cảnh báo, phụ: {ten_phoi_nhiem_mo_hinh})."""
    bien = {b["cot"]: b for b in man["bien"]}
    canh_bao: list[str] = []
    phu: dict = {}

    def ten(cot: str | None) -> str | None:
        if not cot:
            return None
        if cot not in bien:
            raise TuChoi(f"biến «{cot}» không có trong .sav của {study}")
        return bien[cot]["ten"]

    y, g, t, e, cum = ten(dt["outcome"]), ten(dt["group"]), ten(dt["time"]), ten(dt["event"]), ten(dt["cot_cum"])
    cov = [ten(c) for c in (dt.get("covariates_mo_hinh") or dt["covariates"])]
    so = {b["ten"]: b["so"] for b in man["bien"]}
    loai = dt["outcome_type"]
    if y and loai == "auto":
        m = bien[dt["outcome"]].get("muc")
        loai = "binary" if (m is not None and len(m) == 2) else "continuous"
    muc_g = bien[dt["group"]].get("muc") if g else None
    # Cùng luật với run_stats_analysis.py: kết cục THỨ TỰ + phơi nhiễm > 10 giá trị ⇒ phơi nhiễm LIÊN TỤC (C1a: thời
    # gian chờ) — không có Bảng 1 phân nhóm, không có so sánh thô 2 nhóm.
    phoi_lien_tuc = bool(g) and loai == "ordinal" and (muc_g is None or len(muc_g) > 10)
    dong = [
        _chu_thich("Sinh bởi tools/cau_noi_spss.py cu-phap — khớp đặc tả G6 (run_stats_analysis.py). Cần bác sĩ kiểm."),
        "SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES.",
        f"GET FILE={dd_spss(sav or man['sav'])}.",
        *([man["khoi_phai_sinh"].rstrip("\n")] if man.get("khoi_phai_sinh") else []),
        *([man["khoi_loc"].rstrip("\n")] if man.get("khoi_loc") else []),
        *([man["khoi_bien_gia"]] if man.get("khoi_bien_gia") else []),
        f"OMS /SELECT ALL /DESTINATION FORMAT=SPV OUTFILE={dd_spss(thu_muc_kq / (study + '_phan_tich.spv'))}"
        " /TAG='ebm_spv'.",
    ]
    g_mh = g  # tên phơi nhiễm dùng trong mô hình thứ tự
    dv = dt.get("don_vi_phoi_nhiem")
    if dv and g:
        if loai != "ordinal":
            canh_bao.append("đơn vị phơi nhiễm chỉ áp cho hồi quy thứ tự (như run_stats_analysis.py) — bỏ qua")
        elif not so.get(g):
            raise TuChoi(f"đơn vị phơi nhiễm cần biến số, {g} là chuỗi")
        else:
            g_mh = chuan_ten(f"{g}_dv")
            while g_mh.upper() in {b["ten"].upper() for b in man["bien"]}:
                g_mh = chuan_ten(g_mh + "_")
            dong += [
                f"COMPUTE {g_mh} = {g} / {dv:g}.",
                f"VARIABLE LABELS {g_mh} {chuoi_spss(f'{g} chia {dv:g} (OR cho mỗi {dv:g} đơn vị)')}.",
            ]
            phu["ten_phoi_nhiem_mo_hinh"] = g_mh
            so[g_mh] = True

    def khoi(tag: str, lenh: list[str]):
        dong.append(
            f"OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE={dd_spss(thu_muc_kq / ('oms_' + tag + '.xml'))}"
            f" /TAG='{tag}'."
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
    if phoi_lien_tuc:
        canh_bao.append(f"Bảng 1: bỏ phân nhóm theo {g} (phơi nhiễm liên tục — như run_stats_analysis.py)")
    elif g:
        if bo:
            canh_bao.append(f"Bảng 1 bỏ {len(bo)} biến chuỗi/nhiều mức (vd mã phiếu): {', '.join(bo[:6])}")
        lenh = []
        if lt:
            lenh.append(f"MEANS TABLES={goi_ds(lt)}\n    BY {g} /CELLS=MEAN STDDEV COUNT.")
        if pl:
            lenh.append(f"CROSSTABS /TABLES={goi_ds(pl)}\n    BY {g} /CELLS=COUNT COLUMN /STATISTICS=CHISQ.")
        if lenh:
            khoi("bang1", lenh)
    # Kết cục chính — Poisson (F2) so thô như NHỊ PHÂN, đúng như Python (compare_primary_outcome «binary»)
    if y and g:
        loai_kc = "binary" if loai == "poisson_pr" else loai
        if loai_kc in ("binary", "continuous") and len(muc_g or []) != 2:
            # F3: phơi nhiễm liên tục/nhiều mức — Python cũng BỎ so sánh thô hai nhóm (có chủ đích, không phải lỗi)
            canh_bao.append(f"biến nhóm {g} không có đúng 2 mức — bỏ so sánh thô hai nhóm (như Python)")
        elif loai_kc in ("binary", "continuous"):
            if loai_kc == "binary":
                khoi("ket_cuc_chinh", [f"CROSSTABS /TABLES={g} BY {y} /STATISTICS=CHISQ RISK /CELLS=COUNT ROW."])
            else:
                g0, g1 = (v if so.get(g) else "'" + v + "'" for v in muc_g or [])
                khoi("ket_cuc_chinh", [f"T-TEST GROUPS={g}({g0} {g1}) /VARIABLES={y} /CRITERIA=CI(.95)."])
        pred = [g_mh if loai == "ordinal" else g] + cov
        ps, pc = tach(pred)
        by = f"\n    BY {goi_ds(pc)}" if pc else ""
        wi = f"\n    WITH {goi_ds(ps)}" if ps else ""
        if loai == "binary":
            cat = [f"  /CATEGORICAL={goi_ds(pc)}"] + [f"  /CONTRAST({v})=Indicator(1)" for v in pc] if pc else []
            khoi(
                "da_bien",
                [
                    f"LOGISTIC REGRESSION VARIABLES {y}",
                    f"  /METHOD=ENTER {goi_ds(pred)}",
                    *cat,
                    "  /PRINT=CI(95) /CRITERIA=ITERATE(50) CUT(.5).",
                ],
            )
        elif loai == "continuous":
            khoi(
                "da_bien",
                [f"UNIANOVA {y}{by}{wi}", "  /PRINT=PARAMETER /CRITERIA=ALPHA(.05)", f"  /DESIGN={goi_ds(pred)}."],
            )
        elif loai == "ordinal":
            khoi("da_bien", [f"PLUM {y}{by}{wi} /LINK=LOGIT", "  /PRINT=FIT PARAMETER SUMMARY TPARALLEL."])
        elif loai == "poisson_pr":
            # F2: GENLIN Poisson log-link, SE vững (COVB=ROBUST = sandwich HC0, như statsmodels cov_type="HC0" và R
            # sandwich::vcovHC type "HC0"). PR thô từng biến trên CÙNG tập ca của mô hình đầy đủ (TEMPORARY + SELECT
            # IF).
            if pc:
                raise TuChoi(f"Poisson vững cần biến dự báo dạng số (biến chuỗi: {', '.join(pc)}) — khai hiệp biến "
                             "phân loại để thành biến giả")  # fmt: skip
            bg = dt.get("hiep_bien_phan_loai") or {}
            nhom_bien = [[g]] + [[ten(x) for x in bg[c]["ten"]] if c in bg else [ten(c)]
                                 for c in dt["covariates"]]  # fmt: skip
            tat = [v for ds in nhom_bien for v in ds]
            dk = "\n    AND ".join(f"NOT MISSING({v})" for v in [y, *tat])

            def genlin(ds: list[str]) -> list[str]:
                return [f"GENLIN {y} WITH {goi_ds(ds)}",
                        f"  /MODEL {goi_ds(ds)}\n    INTERCEPT=YES DISTRIBUTION=POISSON LINK=LOG",
                        "  /CRITERIA COVB=ROBUST", "  /PRINT SOLUTION (EXPONENTIATED)."]  # fmt: skip

            for i, ds in enumerate(nhom_bien):
                khoi(f"poisson_tho_{i}", ["TEMPORARY.", f"SELECT IF ({dk}).", *genlin(ds)])
            khoi("poisson_hieu_chinh", genlin(tat))
            phu["poisson_nhom_bien"] = nhom_bien
        else:
            raise TuChoi(f"outcome_type không hỗ trợ: {loai}")
        if cum and loai == "poisson_pr":
            canh_bao.append("Poisson vững: hiệu chỉnh cụm chưa hỗ trợ (Python cũng từ chối) — bỏ khối GENLIN cụm")
        elif cum:
            phan_phoi = {
                "binary": "DISTRIBUTION=BINOMIAL LINK=LOGIT",
                "continuous": "DISTRIBUTION=NORMAL LINK=IDENTITY",
                "ordinal": "DISTRIBUTION=MULTINOMIAL LINK=CUMLOGIT",
            }[loai]
            tham_chieu = " (REFERENCE=FIRST)" if loai == "binary" else ""
            khoi(
                "da_bien_cum",
                [
                    f"GENLIN {y}{tham_chieu}{by}{wi}",
                    f"  /MODEL {goi_ds(pred)}\n    INTERCEPT=YES {phan_phoi}",
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
        # run_stats_analysis.survival_model tính HR «thô» trên CÙNG tập ca đầy đủ hiệp biến với mô hình hiệu chỉnh
        # (dropna trên thời gian · biến cố · nhóm · hiệp biến) — đo 14/11/2026: không lọc thì SPSS dùng nhiều ca
        # hơn, HR thô lệch.
        dk = [f"{'AND ' if k else ''}NOT MISSING({v})" for k, v in enumerate(cov)]
        loc = ["TEMPORARY.", f"SELECT IF ({goi_ds(dk)})."] if cov else []
        khoi("song_con_tho", [*loc, f"COXREG {t} /STATUS={e}(1) /METHOD=ENTER {g} /PRINT=CI(95)."])
        if cov:
            khoi(
                "song_con_hieu_chinh",
                [f"COXREG {t} /STATUS={e}(1)\n  /METHOD=ENTER {goi_ds([g] + cov)}\n  /PRINT=CI(95)."],
            )
        khoi("kaplan_meier", [f"KM {t} BY {g} /STATUS={e}(1) /PRINT TABLE MEAN /TEST LOGRANK /COMPARE OVERALL POOLED."])
        canh_bao.append(
            "Cox: SPSS xử lý thời điểm trùng bằng Breslow, lifelines bằng Efron ⇒ HR lệch rất nhỏ "
            "khi có nhiều thời điểm trùng"
        )
    dong += ["OMSEND TAG='ebm_spv'.", ""]
    return "\n".join(dong), canh_bao, phu


def bien_ten(man: dict, ten: str) -> dict:
    return next((b for b in man["bien"] if b["ten"] == ten), {})


def _xoa_ket_qua_cu(d: Path, gate: str) -> None:
    """Kết quả SPSS / đối chiếu của lượt trước không được sống sót khi đặc tả đổi hoặc lượt chạy mới hỏng."""
    for ten in (f"{gate}_spss_ket_qua.json", f"{gate}_spss_doi_chieu.json", f"{gate}_spss_doi_chieu.md"):
        if (d / ten).exists():
            (d / ten).unlink()


def lenh_cu_phap(args) -> int:
    man = _doc_manifest_sav(args.study, can_sav=False)  # máy không có SPSS vẫn sinh cú pháp để chạy tay
    man = them_loc(args.study, them_bien_phai_sinh(args.study, man, args.gate), args.gate)
    dt = dac_ta(args)
    man = them_bien_gia(man, dt)
    if not dt["outcome"] and not (dt["time"] and dt["event"]):
        raise TuChoi(
            "thiếu đặc tả: chưa có G6_analysis_summary.json với khoá dac_ta_phan_tich — truyền --outcome/--group/"
            "--covariates (hoặc --time/--event) như run_stats_analysis.py"
        )
    d = thu_muc_de_tai(args.study)
    kq = d / "spss" / "ket_qua"
    kq.mkdir(parents=True, exist_ok=True)
    dt["vars_bang1"] = [v.strip() for v in (args.vars or "").split(",") if v.strip()] or None
    vb, canh_bao, phu = cu_phap_phan_tich(args.study, man, dt, kq, bien_bang1=dt["vars_bang1"])
    dt.update(phu)
    dt["sav"] = man.get("sav")
    dt["trong_so_tang"] = None
    if dt.get("trong_so"):
        try:
            dt["trong_so_tang"] = tinh_tang_trong_so(
                Path(man["nguon_csv"]), dt["trong_so"], d / "his_tong_hop" / "N_tang_HIS.csv", _ma_thieu_theo_cot(man)
            )
            if dt["trong_so_tang"]["phieu_co_ket_cuc_thieu_tang"]:
                canh_bao.append(
                    f"trọng số: {dt['trong_so_tang']['phieu_co_ket_cuc_thieu_tang']} phiếu có kết cục nhưng thiếu "
                    "ngày/khung giờ — R postStratify sẽ báo lỗi; SPSS loại các phiếu này"
                )
        except KhongDoDuoc as e:
            canh_bao.append(f"trọng số: {e} — bỏ khối Complex Samples")
    vb_bs, cb_bs, phu_bs = cu_phap_bo_sung(args.study, man, dt, kq)
    canh_bao += cb_bs
    dt.update(
        {
            "po_nguong": phu_bs.get("po_nguong"),
            "hon_hop_da_sinh": bool(phu_bs.get("hon_hop")),
            "tin_cay": phu_bs.get("tin_cay"),
        }
    )
    sps = d / "spss" / f"{args.study}_phan_tich.sps"
    sps.write_text(vb, encoding="utf-8", newline="\n")
    sps_bs = d / "spss" / f"{args.study}_phan_tich_bo_sung.sps"
    if vb_bs:
        sps_bs.write_text(vb_bs, encoding="utf-8", newline="\n")
    elif sps_bs.exists():
        sps_bs.unlink()
    (kq / "dac_ta.json").write_text(json.dumps(dt, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    _xoa_ket_qua_cu(d, args.gate)
    print(f"✓ Cú pháp phân tích: {sps}" + (f"\n✓ Cú pháp bổ sung: {sps_bs}" if vb_bs else ""))
    for c in canh_bao:
        print(f"  ⚠ {c}")
    return MA_OK


def _ma_thieu_theo_cot(man: dict) -> dict[str, set[str]]:
    """Mã thiếu của từng cột (mã chữ + mã số khai) như GIÁ TRỊ CHUỖI trong CSV nguồn."""
    return {b["cot"]: set(b.get("ma_chu") or {}) | set(b.get("ma_thieu_so") or []) for b in man["bien"]}


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
        if not hang or _KHONG_PHAI_BIEN.match(hang[-1].strip()) or hang[0].lower().startswith("threshold"):
            continue
        buoc = re.match(r"step\s*(\d+)", hang[0], re.I)
        if len(hang) > 1 and buoc and buoc.group(1) != "1":  # chỉ bảng LOGISTIC nhiều bước (Step 0/1…)
            continue
        b = _lay(cot, r"^(B|Estimate|Coefficient)$")
        se = _lay(cot, r"^(Std\. Error|Standard Error)$")
        if b is not None and se is None and b == 0 and any("Error" in k for k in cot):
            continue  # hệ số dư (mức tham chiếu của biến phân loại GENLINMIXED) — không phải ước lượng
        p = _lay(cot, r"(^|\| )Sig\.?$")
        exp = _lay(cot, r"^Exp\((B|Coefficient)\)$")
        lo_e, hi_e = _lay(cot, r"exp\((b|coefficient)\)", r"lower"), _lay(cot, r"exp\((b|coefficient)\)", r"upper")
        lo, hi = _lay(cot, r"lower", tru=(r"exp\(",)), _lay(cot, r"upper", tru=(r"exp\(",))
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
            ra[hang[-1].strip()] = {"uoc_luong": uoc, "ci": ci, "p": p, "b": b, "se": se}
    return ra


def doc_ket_qua(thu_muc_kq: Path, dt: dict, man: dict) -> dict:
    nguoc = {b["ten"]: b["cot"] for b in man["bien"]}
    if dt.get("ten_phoi_nhiem_mo_hinh") and dt.get("group"):
        nguoc[dt["ten_phoi_nhiem_mo_hinh"]] = dt["group"]
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
    # F2: Poisson vững — PR thô (mỗi biến một tệp OXML) + PR hiệu chỉnh
    tho: dict = {}
    for p in sorted(thu_muc_kq.glob("oms_poisson_tho_*.xml")):
        bs = [b for b in phang_oxml(p) if _chuan_bang(b["bang"]) == "parameterestimates"]
        if bs:
            tho.update(doi_ten(he_so(bs[-1], mu=True)))
    if tho:
        ra["poisson_tho"] = {"thang": "PR", "he_so": tho}
    bs = bang("poisson_hieu_chinh", "parameterestimates")
    if bs:
        ra["poisson_hieu_chinh"] = {"thang": "PR", "he_so": doi_ten(he_so(bs[-1], mu=True))}
    return ra


def lenh_chay(args) -> int:
    d = thu_muc_de_tai(args.study)
    sps = d / "spss" / f"{args.study}_phan_tich.sps"
    kq = d / "spss" / "ket_qua"
    if not sps.exists() or not (kq / "dac_ta.json").exists():
        raise KhongDoDuoc(f"chưa có {sps.name} — chạy `cau_noi_spss.py cu-phap --study {args.study}` trước")
    _xoa_ket_qua_cu(d, args.gate)  # lượt hỏng không được để lại kết quả của lượt trước cho doi-chieu đọc nhầm
    man = them_loc(args.study, them_bien_phai_sinh(args.study, _doc_manifest_sav(args.study), args.gate), args.gate)
    dt = _doc_json(kq / "dac_ta.json")
    man = them_bien_gia(man, dt)  # F2: cùng biến giả như lúc sinh cú pháp (dac_ta.json giữ hiep_bien_phan_loai)
    sav = Path(man["sav"])
    if man.get("sha256_sav") and sha256_tep(sav) != man["sha256_sav"]:
        raise TuChoi(f"{sav.name} đã bị đổi sau khi xuất (SHA-256 khác manifest) — xuất lại bằng xuat-sav")
    # Lượt chạy dùng cú pháp SINH LẠI từ đặc tả (trong vùng tạm đường dẫn ngắn) — phải trùng tệp .sps người đọc.
    vb_that, _, _ = cu_phap_phan_tich(args.study, man, dt, kq, bien_bang1=dt.get("vars_bang1"))
    if sps.read_text(encoding="utf-8") != vb_that:
        raise TuChoi(
            f"{sps.name} khác bản sinh từ đặc tả + .sav hiện tại (sửa tay, hoặc đã xuất lại .sav) — chạy lại cu-phap; "
            "muốn chạy bản sửa tay thì mở tệp trong SPSS"
        )
    sps_bs = d / "spss" / f"{args.study}_phan_tich_bo_sung.sps"
    vb_bs_that, _, _ = cu_phap_bo_sung(args.study, man, dt, kq)
    if (sps_bs.read_text(encoding="utf-8") if sps_bs.exists() else "") != vb_bs_that:
        raise TuChoi(f"{sps_bs.name} khác bản sinh từ đặc tả (sửa tay/thiếu/thừa) — chạy lại cu-phap")
    tang = dt.get("trong_so_tang") or {}
    his = d / "his_tong_hop" / "N_tang_HIS.csv"
    if tang and (not his.exists() or sha256_tep(his) != tang.get("sha256_his")):
        raise TuChoi("bảng Nₕ HIS đã đổi (hoặc mất) sau khi sinh cú pháp — chạy lại cu-phap")
    py = tim_spss()
    for cu in [*kq.glob("oms_*.xml"), *kq.glob(f"{args.study}_phan_tich*.spv"), *kq.glob("r_*")]:
        if cu.exists():
            cu.unlink()
    ma_bs, out_bs, err_bs, r_kq = None, "", "", {}
    with vung_tam() as tam_s:
        tam = Path(tam_s)
        (tam / "kq").mkdir()
        shutil.copyfile(sav, tam / "vao.sav")
        vb, _, _ = cu_phap_phan_tich(
            args.study, man, dt, tam / "kq", sav=tam / "vao.sav", bien_bang1=dt.get("vars_bang1")
        )
        (tam / "phan_tich.sps").write_text(vb, encoding="utf-8", newline="\n")
        ma, out, err = chay_spss(py, ["--cu-phap", str(tam / "phan_tich.sps")], thu_muc=tam, thoi_han=args.thoi_han)
        if ma == 0 and vb_bs_that:
            vb_bs, _, _ = cu_phap_bo_sung(args.study, man, dt, tam / "kq", sav=tam / "vao.sav")
            (tam / "phan_tich_bo_sung.sps").write_text(vb_bs, encoding="utf-8", newline="\n")
            ma_bs, out_bs, err_bs = chay_spss(
                py, ["--cu-phap", str(tam / "phan_tich_bo_sung.sps")], thu_muc=tam, thoi_han=args.thoi_han
            )
        if ma == 0 and not getattr(args, "khong_r", False):
            (tam / "r").mkdir()
            dt_r = dict(dt)
            m = next((b.get("muc") for b in man["bien"] if b["cot"] == dt.get("outcome")), None)
            if dt_r.get("outcome_type") in (None, "auto"):
                dt_r["outcome_type"] = "binary" if m is not None and len(m) == 2 else "continuous"
            r_kq = chay_r_tham_chieu(man, dt_r, tam / "vao.sav", tam / "r", his=his if tang else None,
                                     khoi_r=ma_r_chuan_bi_tham_chieu(args.study, args.gate, man, dt_r))  # fmt: skip
            for f in (tam / "r").iterdir():
                if f.name in ("r_doi_chieu.R", "r_kq.json"):
                    shutil.copyfile(f, kq / f.name)
        for f in (tam / "kq").iterdir():
            shutil.move(str(f), kq / f.name)
    (kq / f"{args.study}_phan_tich.log").write_text(
        out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n"
    )
    if ma_bs is not None:
        (kq / f"{args.study}_phan_tich_bo_sung.log").write_text(
            out_bs + ("\n--- stderr ---\n" + err_bs if err_bs else ""), encoding="utf-8", newline="\n"
        )
    if ma != 0:
        print("🔴 SPSS báo lỗi —", (err or out).strip()[-800:], f"\n   nhật ký: {kq / (args.study + '_phan_tich.log')}")
        return MA_LECH
    if ma_bs not in (None, 0):
        print("⚠ Phân tích BỔ SUNG của SPSS lỗi (phân tích chính vẫn dùng được) —", (err_bs or out_bs).strip()[-400:])
    if r_kq.get("loi"):
        print(f"⚪ Tham chiếu R: {r_kq['loi']}")
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
        "sha256_nguon": man.get("sha256_nguon"),
        "dac_ta": dt,
        "ket_qua": {**doc_ket_qua(kq, dt, man), "bo_sung": doc_ket_qua_bo_sung(kq, dt, man)},
        "bo_sung_loi": (err_bs or out_bs).strip()[-600:] if ma_bs not in (None, 0) else None,
        "r_tham_chieu": r_kq,
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


def _beta(x: float | None, ty_so: bool) -> float | None:
    if x is None:
        return None
    if not ty_so:
        return x
    return math.log(x) if x > 0 else None


def _se(ci: list | None, ty_so: bool) -> float | None:
    if not ci or None in ci:
        return None
    lo, hi = _beta(ci[0], ty_so), _beta(ci[1], ty_so)
    return (hi - lo) / 3.92 if lo is not None and hi is not None and hi > lo else None


def _gan(
    a: float | None,
    b: float | None,
    tuong_doi: float | None = None,
    tuyet_doi: float = 0.0006,
    *,
    tran: float | None = None,
) -> bool | None:
    """|a − b| ≤ `tran` (dung sai tuyệt đối đã tính sẵn — so_mot dùng). Gọi kiểu CŨ `_gan(a, b, tương_đối)` vẫn chạy:
    |a − b| ≤ max(tuyet_doi, tương_đối·|b|) — tools/cau_noi_r.py (phiên khác, 14/11/2026) dùng chữ ký này."""
    if a is None or b is None:
        return None
    if tran is None:
        tran = max(tuyet_doi, (tuong_doi or 0.0) * abs(b))
    return abs(a - b) <= tran + 1e-9


def _so_p(a: float | None, b: float | None) -> bool | None:
    if a is None or b is None:
        return None
    return (a < 0.001 and b < 0.001) or abs(a - b) <= TOL_P


# Python (run_stats_analysis.py) LÀM TRÒN trước khi ghi tóm tắt: OR/HR/KTC tỷ số 3 chữ số lẻ, β 4 chữ số, hiệu trung
# bình
# 3 chữ số ⇒ dung sai phải cộng nửa đơn vị làm tròn, không thì hai phần mềm khớp tuyệt đối vẫn bị báo «lệch».
LAM_TRON = {"ty_so": 0.0005, "beta": 0.00005, "md": 0.0005}


def so_mot(
    ten: str, py: dict, sp: dict, *, phuong_phap_khac: str | None = None, ty_so: bool = False, lam_tron: float = 0.0
) -> dict:
    """Một dòng đối chiếu: py/sp = {uoc_luong, ci, p}. Trạng thái khop · lech_nho · lech · khong_so_duoc.

    ty_so=True (OR/HR): so trên thang LOG (β) — dung sai tương đối trên thang OR quá lỏng khi OR gần 1 (rà độc lập
    14/11/2026: OR 1,030 so 1,035 «khớp» dù β lệch 16 %). Dung sai gắn theo SE của Python: «khớp» ≤ 0,2 % SE (ước lượng)
    và ≤ 1 % SE (cận KTC), cộng nửa đơn vị làm tròn; khác phương pháp ĐÃ BIẾT thì «lệch nhỏ» khi ước lượng lệch
    ≤ 10 % SE.
    p hai bên KHÁC PHÍA ngưỡng 0,05 thì không bao giờ «khớp»."""
    se = _se(py.get("ci"), ty_so)

    def tron(x: float | None) -> float:  # nửa đơn vị làm tròn của Python, quy về thang so
        if not lam_tron or x is None:
            return 0.0
        return lam_tron / x if ty_so and x > 0 else lam_tron

    b_sp, b_py = _beta(sp.get("uoc_luong"), ty_so), _beta(py.get("uoc_luong"), ty_so)
    goc = abs(b_py) if b_py is not None else 0.0
    t_uoc = tron(py.get("uoc_luong"))
    kt = {"uoc_luong": _gan(b_sp, b_py, tran=(0.002 * se if se else TOL_UOC * goc) + t_uoc)}
    gan_long = _gan(b_sp, b_py, tran=(0.1 * se if se else 0.02 * goc) + t_uoc)
    ci_py, ci_sp = py.get("ci") or [None, None], sp.get("ci") or [None, None]
    if None in (*ci_py, *ci_sp):
        kt["ci"] = None
    else:
        kt["ci"] = all(
            _gan(
                _beta(a, ty_so),
                _beta(b, ty_so),
                tran=(0.01 * se if se else TOL_CI * abs(_beta(b, ty_so) or 0.0)) + tron(b),
            )
            for a, b in zip(ci_sp, ci_py)
        )
    kt["p"] = _so_p(sp.get("p"), py.get("p"))
    ghi = [phuong_phap_khac] if phuong_phap_khac else []
    p_s, p_p = sp.get("p"), py.get("p")
    if p_s is not None and p_p is not None and (p_s < 0.05) != (p_p < 0.05) and abs(p_s - p_p) > 0.0001:
        kt["p"] = False
        ghi.append("⚠ p hai bên KHÁC PHÍA ngưỡng 0,05 — kết luận ý nghĩa thống kê đổi chiều")
    co = [v for v in kt.values() if v is not None]
    if kt["uoc_luong"] is None:
        tt = "khong_so_duoc"
    elif all(co):
        tt = "khop"
    elif phuong_phap_khac and gan_long:
        tt = "lech_nho"
    else:
        tt = "lech"
    return {"muc": ten, "python": py, "spss": sp, "kiem": kt, "trang_thai": tt, "ghi_chu": " · ".join(ghi)}


def _khong_so(muc: str, ly_do: str, *, py: dict | None = None, sp: dict | None = None) -> dict:
    return {"muc": muc, "python": py, "spss": sp, "kiem": {}, "trang_thai": "khong_so_duoc", "ghi_chu": ly_do}


def doi_chieu(tom: dict, kq: dict) -> list[dict]:
    """Mọi mục Python CÓ (hoặc báo lỗi/bỏ qua) đều sinh một dòng — không bỏ dòng im lặng (bản cũ báo «1 khớp, mã 0»
    khi Python lỗi hoặc SPSS thiếu bảng)."""
    dong: list[dict] = []
    pc, sc = tom.get("primary_outcome") or {}, kq.get("ket_cuc_chinh") or {}
    loai_pc = pc.get("outcome_type")
    if pc.get("error"):
        dong.append(_khong_so("Kết cục chính", f"Python lỗi: {pc['error']}"))
    elif loai_pc == "binary" and sc.get("loai") == "binary":
        dong.append(
            so_mot(
                "Kết cục chính — OR thô (nhóm sau so nhóm trước)",
                {"uoc_luong": pc.get("or_crude"), "ci": list(pc.get("ci_95") or []) or None, "p": pc.get("p_value")},
                {"uoc_luong": sc.get("or"), "ci": sc.get("ci"), "p": sc.get("p_yates")},
                ty_so=True,
                lam_tron=LAM_TRON["ty_so"],
            )
        )
    elif loai_pc == "continuous" and sc.get("loai") == "continuous":
        welch = "welch" in str(pc.get("test", "")).lower()
        s = sc.get("welch" if welch else "student") or {}
        p_py = pc.get("p_value") if (welch or "t-test" in str(pc.get("test", "")).lower()) else None
        dong.append(
            so_mot(
                "Kết cục chính — hiệu trung bình (nhóm sau − nhóm trước)",
                {"uoc_luong": pc.get("md_crude"), "ci": None, "p": p_py},
                {"uoc_luong": s.get("md_g1_tru_g0"), "ci": None, "p": s.get("p") if p_py is not None else None},
                phuong_phap_khac=None if p_py is not None else f"Python dùng {pc.get('test')} — chỉ so hiệu trung bình",
                lam_tron=LAM_TRON["md"],
            )
        )
    elif loai_pc or sc:
        dong.append(
            _khong_so(
                "Kết cục chính",
                f"Python «{loai_pc or 'không có'}» · SPSS «{sc.get('loai') or 'không có'}» — không cùng loại để so",
            )
        )
    co_thu_tu = "ordinal" in tom
    mv = (tom.get("ordinal") if co_thu_tu else tom.get("multivariate")) or {}
    ten_mv = "Hồi quy thứ tự" if co_thu_tu else "Đa biến"
    cum = (mv.get("cov_type") == "cluster") or bool((tom.get("dac_ta_phan_tich") or {}).get("cot_cum"))
    nguon = kq.get("da_bien_cum") if cum else kq.get("da_bien")
    if mv.get("error") or mv.get("skipped"):
        dong.append(_khong_so(ten_mv, f"Python không có ước lượng: {mv.get('error') or mv.get('reason') or 'bỏ qua'}"))
    elif mv.get("results") and not nguon:
        dong.append(
            _khong_so(
                ten_mv,
                "SPSS thiếu kết quả GENLIN (hiệu chỉnh cụm) — không so với mô hình KHÔNG hiệu chỉnh cụm"
                if cum
                else "SPSS thiếu bảng hệ số (xem nhật ký chạy)",
            )
        )
    else:
        ty_so = "OR_adj" in (mv.get("results") or [{}])[0] or co_thu_tu
        for r in mv.get("results") or []:
            v = r.get("variable")
            uoc = r.get("OR_adj", r.get("beta"))
            sp = (nguon or {}).get("he_so", {}).get(v)
            if sp is None:
                dong.append(
                    _khong_so(
                        f"{ten_mv} — {v}",
                        "SPSS không có hệ số cùng tên (biến phân loại mã hoá khác?)",
                        py={"uoc_luong": uoc},
                    )
                )
                continue
            dong.append(
                so_mot(
                    f"{ten_mv} ({mv.get('model', '?')}) — {v}",
                    {"uoc_luong": uoc, "ci": r.get("CI_95"), "p": r.get("p")},
                    {"uoc_luong": sp["uoc_luong"], "ci": sp["ci"], "p": sp["p"]},
                    phuong_phap_khac=(
                        "hiệu chỉnh cụm: GEE robust (SPSS) ≠ sandwich có hiệu chỉnh mẫu nhỏ (Python)"
                        if cum
                        else "statsmodels lấy SE từ Hessian xấp xỉ"
                        if mv.get("model") == "ordinal_logit_po"
                        else None
                    ),
                    ty_so=ty_so,
                    lam_tron=LAM_TRON["ty_so" if ty_so else "beta"],
                )
            )
    pr = tom.get("poisson_pr")
    if pr is not None:
        if pr.get("error"):
            dong.append(_khong_so("Poisson vững (PR)", f"Python lỗi: {pr['error']}"))
        for nhan, ds, khoa_py, khoa_sp in (("PR thô", pr.get("tho") or [], "PR", "poisson_tho"),
                                           ("PR hiệu chỉnh", pr.get("results") or [], "PR_adj", "poisson_hieu_chinh")):
            nguon_pr = (kq.get(khoa_sp) or {}).get("he_so") or {}
            for r in ds:
                v, sp = r.get("variable"), nguon_pr.get(r.get("variable"))
                if sp is None:
                    dong.append(_khong_so(f"Poisson — {nhan} — {v}", "SPSS không có hệ số cùng tên",
                                          py={"uoc_luong": r.get(khoa_py)}))  # fmt: skip
                    continue
                dong.append(
                    so_mot(
                        f"Poisson HC0 — {nhan} — {v}",
                        {"uoc_luong": r.get(khoa_py), "ci": r.get("CI_95"), "p": r.get("p")},
                        {"uoc_luong": sp["uoc_luong"], "ci": sp["ci"], "p": sp["p"]},
                        ty_so=True,
                        lam_tron=LAM_TRON["ty_so"],
                    )
                )
    sv = tom.get("survival") or {}
    nhom = (tom.get("dac_ta_phan_tich") or {}).get("group")
    if sv.get("error"):
        dong.append(_khong_so("Cox", f"Python lỗi: {sv['error']}"))
    for khoa_py, khoa_sp, nhan in (("crude", "song_con_tho", "thô"), ("adjusted", "song_con_hieu_chinh", "hiệu chỉnh")):
        r = sv.get(khoa_py) or {}
        sp = ((kq.get(khoa_sp) or {}).get("he_so") or {}).get(nhom) if nhom else None
        if r.get("HR") is None:
            continue
        if not sp:
            dong.append(_khong_so(f"Cox — HR {nhan} ({nhom})", "SPSS thiếu bảng Cox", py={"uoc_luong": r.get("HR")}))
            continue
        dong.append(
            so_mot(
                f"Cox — HR {nhan} ({nhom})",
                {"uoc_luong": r.get("HR"), "ci": r.get("CI_95"), "p": r.get("p")},
                {"uoc_luong": sp["uoc_luong"], "ci": sp["ci"], "p": sp["p"]},
                phuong_phap_khac="thời điểm trùng: Breslow (SPSS) ≠ Efron (lifelines)",
                ty_so=True,
                lam_tron=LAM_TRON["ty_so"],
            )
        )
    return dong


def lech_dac_ta(dt_spss: dict, dt_py: dict, tom: dict) -> list[str]:
    """Đặc tả SPSS đã chạy khác đặc tả Python ở đâu (rỗng = trùng)."""
    ra = []
    for k in ("outcome", "group", "time", "event", "cot_cum", "loc"):
        if (dt_spss.get(k) or None) != (dt_py.get(k) or None):
            ra.append(f"{k}: SPSS {dt_spss.get(k)!r} · Python {dt_py.get(k)!r}")
    if sorted(dt_spss.get("covariates") or []) != sorted(dt_py.get("covariates") or []):
        ra.append(f"covariates: SPSS {dt_spss.get('covariates')} · Python {dt_py.get('covariates')}")
    lo_s, lo_p = dt_spss.get("outcome_type"), dt_py.get("outcome_type")
    if lo_s not in (None, "auto") and lo_p not in (None, "auto") and lo_s != lo_p:
        ra.append(f"outcome_type: SPSS {lo_s} · Python {lo_p}")
    dv_p = dt_py.get("don_vi_phoi_nhiem")
    if dv_p is None:
        dv_p = ((tom.get("ordinal") or {}).get("don_vi_phoi_nhiem") or {}).get("don_vi")
    if (dt_spss.get("don_vi_phoi_nhiem") or None) != (dv_p or None):
        ra.append(f"don_vi_phoi_nhiem: SPSS {dt_spss.get('don_vi_phoi_nhiem')} · Python {dv_p}")
    return ra


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
    # Chuỗi SHA-256 bắt buộc (rà độc lập 14/11/2026: bản cũ bỏ qua khi thiếu khoá, và không so kết quả SPSS với .sav
    # hiện tại ⇒ lượt `chay` hỏng sau khi khoá lại vẫn để doi-chieu so kết quả SPSS CŨ với Python mới).
    sha_py = (tom.get("data_lock") or {}).get("sha256")
    if not sha_py:
        raise KhongDoDuoc(
            "tóm tắt Python không ghi SHA-256 dữ liệu khoá (data_lock.sha256) — không xác nhận được cùng dữ liệu"
        )
    man = them_bien_phai_sinh(args.study, _doc_manifest_sav(args.study), args.gate)
    if not kq.get("sha256_sav") or kq["sha256_sav"] != man.get("sha256_sav"):
        raise TuChoi(
            "kết quả SPSS không thuộc tệp .sav hiện tại (SHA-256 khác/thiếu) — chạy lại `cau_noi_spss.py chay`"
        )
    if man.get("sha256_nguon") != sha_py:
        raise TuChoi("SPSS và Python KHÔNG phân tích cùng một bộ dữ liệu khoá (SHA-256 nguồn khác) — xuất lại .sav")
    dt_py = tom.get("dac_ta_phan_tich")
    if not dt_py:
        raise KhongDoDuoc(
            "tóm tắt Python chưa có dac_ta_phan_tich — chạy lại run_stats_analysis.py (bản ≥ 14/11/2026) để so đặc tả"
        )
    lech = lech_dac_ta(kq.get("dac_ta") or {}, dt_py, tom)
    if lech:
        raise TuChoi(
            "đặc tả SPSS đã chạy KHÁC đặc tả Python — sinh lại cú pháp (cu-phap) rồi chạy lại:\n   "
            + "\n   ".join(lech)
        )
    dong = doi_chieu(tom, kq.get("ket_qua") or {})
    dt_sp = kq.get("dac_ta") or {}
    tin_cay_py = (
        tin_cay_python(man, {x["ten"]: x["muc"] for x in dt_sp.get("tin_cay") or []}) if dt_sp.get("tin_cay") else {}
    )
    dong_bs, thong_tin = doi_chieu_bo_sung(
        tom, kq.get("ket_qua") or {}, dt_sp, r=kq.get("r_tham_chieu"), tin_cay_py=tin_cay_py
    )
    if kq.get("bo_sung_loi"):
        dong_bs.insert(0, _khong_so("Phân tích bổ sung", f"SPSS lỗi ở tệp bổ sung: {kq['bo_sung_loi'][-200:]}"))
    dong += dong_bs
    dem = {k: sum(1 for x in dong if x["trang_thai"] == k) for k in ("khop", "lech_nho", "lech", "khong_so_duoc")}
    ket = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "nguong": {
            "khop_uoc_luong": "≤ 0,2 % SE (thang log cho OR/HR) + nửa đơn vị làm tròn của Python",
            "khop_ci": "≤ 1 % SE + nửa đơn vị làm tròn",
            "lech_nho": "khác phương pháp đã biết và ước lượng lệch ≤ 10 % SE",
            "p_tuyet_doi": TOL_P,
        },
        "spss_phien_ban": kq.get("spss_phien_ban"),
        "dem": dem,
        "dong": dong,
        "thong_tin": thong_tin,
        "r_phien_ban": (kq.get("r_tham_chieu") or {}).get("phien_ban_r"),
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
        f"SPSS {kq.get('spss_phien_ban') or '?'} · {ket['luc']} · ngưỡng khớp: ước lượng ≤ 0,2 % SE (OR/HR so trên "
        f"thang log), KTC ≤ 1 % SE, cộng nửa đơn vị làm tròn của Python; p ±{TOL_P} (hai bên < 0,001 coi là khớp; khác "
        "phía 0,05 thì không khớp). «Lệch nhỏ»: khác phương pháp đã biết, ước lượng lệch ≤ 10 % SE.",
        "",
        f"Tổng: {dem['khop']} khớp · {dem['lech_nho']} lệch nhỏ · {dem['lech']} lệch · "
        f"{dem['khong_so_duoc']} không so được.",
        "",
        "| Mục | Tham chiếu: Python, hoặc R ở dòng ghi «tham chiếu R»/«R …» (ước lượng · KTC 95% · p) "
        "| SPSS (ước lượng · KTC 95% · p) | Kết quả | Ghi chú |",
        "|---|---|---|---|---|",
    ]
    for x in dong:
        py, sp = x.get("python") or {}, x.get("spss") or {}
        md.append(
            f"| {x['muc']} | {_fmt(py.get('uoc_luong'))} · {_fmt(py.get('ci'))} · {_fmt(py.get('p'))} | "
            f"{_fmt(sp.get('uoc_luong'))} · {_fmt(sp.get('ci'))} · {_fmt(sp.get('p'))} | "
            f"{ky[x['trang_thai']]} | {x['ghi_chu']} |"
        )
    if thong_tin:
        md += ["", "Thông tin thêm (không so tự động):", "", *[f"- {x}" for x in thong_tin]]
    if ket["r_phien_ban"]:
        md += ["", f"Tham chiếu R: {ket['r_phien_ban']} — chạy trên CÙNG tệp .sav (haven, mã thiếu người dùng ⇒ NA)."]
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


# ───────────────────────────── phân tích BỔ SUNG (mở rộng 14/11/2026) ─────────────────────────────
#
# Bác sĩ chọn 14/11/2026: (1) mô hình hỗn hợp intercept ngẫu nhiên theo cụm — SAP C1a lấy làm phân tích CHÍNH khi < 15
# cụm; (2) Complex Samples có trọng số hậu phân tầng; (3) RELIABILITY (Cronbach α); (4) kiểm giả định tỷ lệ odds tại
# từng ngưỡng; (5) tự sinh .sps cùng script R ở run_g6_auto.py. Các khối này nằm trong tệp cú pháp RIÊNG
# `<mã>_phan_tich_bo_sung.sps`, chạy SAU phân tích chính: một khối hỏng (vd GENLINMIXED không hội tụ) không làm mất
# phần đối chiếu chính.
#
# Tham chiếu của từng khối: (1)(2) là phân tích mà G6 chỉ có dạng script R (ordinal::clmm / lme4::glmer, survey) —
# công cụ chạy R TRÊN CÙNG tệp .sav (haven, mã thiếu người dùng ⇒ NA) để có số tham chiếu; (3) công cụ tin cậy của hệ
# `kiem_tin_cay_thang_do.py`; (4) bảng OR theo ngưỡng của `run_stats_analysis.ordinal_model`.
#
# Đo thật 14/11/2026 (SPSS 31.0.1, R 4.6.2, dữ liệu giả 400 ca, 10 cụm): CSORDINAL/CSDESCRIPTIVES trùng svyolr/svymean
# (trọng số cố định) tới 5 chữ số, KỂ CẢ SE và DEFF; PLUM trùng MASS::polr; GENLINMIXED (giả khả dĩ tuyến tính hoá) lệch
# clmm (Laplace) ~2 % SE; GENLINMIXED nhị phân cần REFERENCE=<mã thấp> để mô hình hoá P(mã cao) như glmer. GENLINMIXED
# chỉ ra bảng qua OMS khi `SET MDISPLAY=TABLES` (mặc định là Model Viewer). Biến số mức NOMINAL bị GENLINMIXED coi là
# YẾU TỐ (mức cuối làm tham chiếu) — Python coi là biến số ⇒ cú pháp tạm đặt mọi biến dự báo dạng số về SCALE.

TEP_HAM_TRONG_SO = "ham_trong_so.R"


def _ten_g_mh(man: dict, g: str, dv) -> str:
    """Tên biến phơi nhiễm đã chia đơn vị — CÙNG luật với cu_phap_phan_tich (hai tệp cú pháp dùng chung tên)."""
    g_mh = chuan_ten(f"{g}_dv")
    while g_mh.upper() in {b["ten"].upper() for b in man["bien"]}:
        g_mh = chuan_ten(g_mh + "_")
    return g_mh


def _so_r(x: float) -> str:
    """Số in như `sprintf("%s", x)` của R cho mã ô (1 ⇒ «1», 1.5 ⇒ «1.5») — nhãn tầng phải trùng nhãn 04a."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def _gia_tri_ma(v: str | None, thieu: set[str]) -> float | None:
    v = (v or "").strip()
    if v == "" or v in thieu:
        return None
    return _so(v)


def tinh_tang_trong_so(csv_p: Path, ts: dict, his_p: Path, ma_thieu_cot: dict[str, set[str]]) -> dict:
    """Bản Python của `bang_tang` + `gop_tang_nho` + `bang_kich_hoat` (04a_ham_trong_so.R, g6_trong_so_survey.py).

    Cùng quy tắc: nₕ đếm trên MỌI phiếu có đủ ngày + khung (NA bị bỏ như table() của R); ô có phiếu mà HIS không có
    lượt khám ⇒ dừng; tầng nₕ < n_toi_thieu gộp với khung giờ liền kề CÙNG NGÀY, chưa có thì cùng khung giờ của ngày
    liền kề; chọn tầng nhỏ nhất (nₕ rồi nhãn) để gộp trước, gộp vào tầng liền kề có nₕ nhỏ nhất. doi-chieu so kết quả
    này với chính hàm R (04a) ⇒ hai bản của cùng thuật toán phải cho cùng bảng tầng."""
    bn, bk = ts.get("bien_ngay"), ts.get("bien_khung")
    if not bn or not bk:
        raise TuChoi("trọng số: SAP/dictionary chưa cho tên biến ngày/khung giờ (G6_checkpoint.trong_so)")
    dem: dict[tuple[float, float], int] = {}
    thieu_tang = 0
    with open(csv_p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            a = _gia_tri_ma(r.get(bn), ma_thieu_cot.get(bn, set()))
            b = _gia_tri_ma(r.get(bk), ma_thieu_cot.get(bk, set()))
            if a is None or b is None:
                kc = _gia_tri_ma(r.get(ts.get("ket_cuc") or ""), ma_thieu_cot.get(ts.get("ket_cuc") or "", set()))
                thieu_tang += kc is not None
                continue
            dem[(a, b)] = dem.get((a, b), 0) + 1
    if not his_p.exists():
        raise KhongDoDuoc(f"CHƯA CÓ SỐ LIỆU HIS: {his_p} — PI cung cấp Nₕ theo ô ngày × khung giờ (SAP §4)")
    his: dict[tuple[float, float], float] = {}
    with open(his_p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            a, b, nh = _so(r.get(bn) or ""), _so(r.get(bk) or ""), _so(r.get("N_h") or "")
            if a is None or b is None:
                raise TuChoi(f"bảng Nₕ HIS: mã ngày/khung phải là số ({r.get(bn)!r}, {r.get(bk)!r})")
            if (a, b) in his:
                raise TuChoi("bảng Nₕ HIS có ô ngày × khung giờ bị trùng")
            his[(a, b)] = nh if nh is not None else float("nan")
    o_lech = [k for k, n in dem.items() if n > 0 and not (his.get(k, float("nan")) > 0)]
    if o_lech:
        raise TuChoi(
            "có phiếu ở ô không có lượt khám trong bảng Nₕ HIS: "
            + ", ".join(f"{_so_r(a)}×{_so_r(b)}" for a, b in sorted(o_lech))
        )
    o = sorted(
        ({"ngay": a, "khung": b, "nhom": f"N{_so_r(a)}_K{_so_r(b)}", "n_h": dem.get((a, b), 0), "N_h": nh}
         for (a, b), nh in his.items() if nh > 0),
        key=lambda x: (x["ngay"], x["khung"]),
    )  # fmt: skip
    so_o = len(o)

    def tong() -> dict[str, list[float]]:
        t: dict[str, list[float]] = {}
        for x in o:
            t.setdefault(x["nhom"], [0, 0.0])
            t[x["nhom"]][0] += x["n_h"]
            t[x["nhom"]][1] += x["N_h"]
        return t

    def ke(g: str, cap: int) -> set[str]:
        cua_g = [x for x in o if x["nhom"] == g]
        ra = set()
        for x in o:
            if x["nhom"] == g:
                continue
            for y in cua_g:
                if (cap == 1 and y["ngay"] == x["ngay"] and abs(y["khung"] - x["khung"]) == 1) or (
                    cap == 2 and y["khung"] == x["khung"] and abs(y["ngay"] - x["ngay"]) == 1
                ):
                    ra.add(x["nhom"])
        return ra

    n_min = ts.get("n_toi_thieu")
    if n_min is None:
        raise TuChoi("trọng số: SAP chưa cho ngưỡng gộp tầng nₕ")
    nhat_ky = []
    while True:
        t = tong()
        nho = sorted(((v[0], g) for g, v in t.items() if v[0] < n_min))
        if not nho or len(t) == 1:
            break
        n_g, g = nho[0]
        ung, cap = ke(g, 1), 1
        if not ung:
            ung, cap = ke(g, 2), 2
        if not ung:
            raise TuChoi(f"không gộp được tầng {g} (không có ô liền kề theo quy tắc SAP §4)")
        dich = sorted((t[u][0], u) for u in ung)[0][1]
        nhat_ky.append(
            f"gộp {g} (nₕ={int(n_g)}) vào {dich} — "
            + ("khung giờ liền kề cùng ngày" if cap == 1 else "cùng khung giờ, ngày liền kề")
        )
        for x in o:
            if x["nhom"] == g:
                x["nhom"] = dich
    t = tong()
    n, N = sum(v[0] for v in t.values()), sum(v[1] for v in t.values())
    tang = []
    for g in sorted(t):
        nh, Nh = t[g]
        ty = (nh / n) / (Nh / N) if n and N else float("nan")
        tang.append({"nhom": g, "n_h": nh, "N_h": Nh, "lech": abs(ty - 1)})
    nguong = ts.get("nguong_lech")
    lech_max = max((x["lech"] for x in tang), default=float("nan"))
    return {
        "o": [{k: x[k] for k in ("ngay", "khung", "nhom", "N_h")} for x in o],
        "tang": tang,
        "nhat_ky": nhat_ky,
        "so_o_truoc_gop": so_o,
        "so_tang_sau_gop": len(tang),
        "lech_max": lech_max,
        "kich_hoat": bool(nguong is not None and any(x["lech"] > nguong for x in tang)),
        "phieu_co_ket_cuc_thieu_tang": thieu_tang,
        "sha256_his": sha256_tep(his_p),
    }


def cu_phap_bo_sung(
    study: str, man: dict, dt: dict, thu_muc_kq: Path, *, sav: Path | str | None = None
) -> tuple[str, list[str], dict]:
    """Cú pháp `<mã>_phan_tich_bo_sung.sps` (rỗng nếu không có khối nào áp dụng). Trả (cú pháp, cảnh báo, phụ)."""
    bien = {b["cot"]: b for b in man["bien"]}
    so = {b["ten"]: b["so"] for b in man["bien"]}
    canh_bao: list[str] = []
    phu: dict = {}

    def ten(cot: str | None) -> str | None:
        if not cot:
            return None
        if cot not in bien:
            raise TuChoi(f"biến «{cot}» không có trong .sav của {study}")
        return bien[cot]["ten"]

    trung = sorted(b["ten"] for b in man["bien"] if b["ten"].upper().startswith("EBM_"))
    if trung:
        raise TuChoi(f"biến trong .sav trùng tiền tố biến tạm của cầu nối (ebm_…): {', '.join(trung)} — đổi tên trước")
    y, g, cum = ten(dt.get("outcome")), ten(dt.get("group")), ten(dt.get("cot_cum"))
    cov = [ten(c) for c in (dt.get("covariates_mo_hinh") or dt.get("covariates") or [])]
    loai = dt.get("outcome_type") or "auto"
    muc_y = bien[dt["outcome"]].get("muc") if y else None
    if y and loai == "auto":
        loai = "binary" if (muc_y is not None and len(muc_y) == 2) else "continuous"
    dv = dt.get("don_vi_phoi_nhiem")
    dau = [
        _chu_thich(
            "Sinh bởi tools/cau_noi_spss.py cu-phap — phân tích BỔ SUNG (chạy sau phân tích chính). Cần bác sĩ kiểm."
        ),
        "SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES.",
        "SET MDISPLAY=TABLES.",
        f"GET FILE={dd_spss(sav or man['sav'])}.",
        *([man["khoi_phai_sinh"].rstrip("\n")] if man.get("khoi_phai_sinh") else []),
        *([man["khoi_loc"].rstrip("\n")] if man.get("khoi_loc") else []),
        *([man["khoi_bien_gia"]] if man.get("khoi_bien_gia") else []),
        f"OMS /SELECT ALL /DESTINATION FORMAT=SPV OUTFILE={dd_spss(thu_muc_kq / (study + '_phan_tich_bo_sung.spv'))}"
        " /TAG='ebm_spv_bs'.",
    ]
    dong: list[str] = []
    g_mh = g
    if dv and g and loai == "ordinal" and so.get(g):
        g_mh = _ten_g_mh(man, g, dv)
        dong.append(f"COMPUTE {g_mh} = {g} / {dv:g}.")
        so = {**so, g_mh: True}

    def khoi(tag: str, lenh: list[str]):
        dong.append(
            f"OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE={dd_spss(thu_muc_kq / ('oms_' + tag + '.xml'))}"
            f" /TAG='{tag}'."
        )
        dong.extend(lenh)
        dong.append(f"OMSEND TAG='{tag}'.")

    pred = ([g_mh if loai == "ordinal" else g] if g else []) + cov
    so_pred = [v for v in pred if so.get(v)]
    chu_pred = [v for v in pred if not so.get(v)]

    # (4) Giả định tỷ lệ odds: logistic nhị phân tại TỪNG ngưỡng Y > k — cùng phép của ordinal_model (Python)
    if y and g and loai == "ordinal" and dt.get("kiem_po", True):
        muc = sorted((_so(m) for m in muc_y or [] if _so(m) is not None)) if muc_y else []
        if len(muc) >= 3:
            ds = []
            for i, k in enumerate(muc[:-1], 1):
                v = chuan_ten(f"ebm_po{i}")
                ds.append({"i": i, "k": k, "ten": v})
                dong.append(f"COMPUTE {v} = ({y} > {k:g}).")
                cat = [f"  /CATEGORICAL={goi_ds(chu_pred)}"] + [f"  /CONTRAST({c})=Indicator(1)" for c in chu_pred]
                khoi(
                    f"po_nguong_{i}",
                    [
                        f"LOGISTIC REGRESSION VARIABLES {v}",
                        f"  /METHOD=ENTER {goi_ds(pred)}",
                        *(cat if chu_pred else []),
                        "  /PRINT=CI(95) /CRITERIA=ITERATE(50) CUT(.5).",
                    ],
                )
            phu["po_nguong"] = ds
        else:
            canh_bao.append("giả định tỷ lệ odds: kết cục thứ tự cần ≥ 3 mức đọc được trong .sav — bỏ qua")

    # (1) Mô hình hỗn hợp: intercept ngẫu nhiên theo cụm (GENLINMIXED) — SAP C1a: phân tích CHÍNH khi < 15 cụm
    if y and g and cum and loai in ("ordinal", "binary") and dt.get("hon_hop", True):
        tuy_chon = "DISTRIBUTION=MULTINOMIAL LINK=LOGIT"
        if loai == "binary":
            ma0 = sorted(muc_y or [], key=lambda m: (_so(m) is None, _so(m) or 0, m))
            if not so.get(y) or not ma0:
                canh_bao.append("mô hình hỗn hợp: kết cục nhị phân cần mã số đọc được — bỏ qua GENLINMIXED")
                tuy_chon = ""
            else:
                tuy_chon = f"REFERENCE={ma0[0]} DISTRIBUTION=BINOMIAL LINK=LOGIT"
        if tuy_chon:
            muc_do = [f"VARIABLE LEVEL {y} ({'ORDINAL' if loai == 'ordinal' else 'NOMINAL'})", f"/{cum} (NOMINAL)"]
            if so_pred:
                muc_do.append(f"/{goi_ds(so_pred)} (SCALE)")
            khoi(
                "da_bien_hon_hop",
                [
                    "\n  ".join(muc_do) + ".",
                    "GENLINMIXED",
                    f"  /DATA_STRUCTURE SUBJECTS={cum}",
                    f"  /FIELDS TARGET={y} TRIALS=NONE OFFSET=NONE",
                    f"  /TARGET_OPTIONS {tuy_chon}",
                    f"  /FIXED EFFECTS={goi_ds(pred)}\n    USE_INTERCEPT=TRUE",
                    f"  /RANDOM USE_INTERCEPT=TRUE SUBJECTS={cum} COVARIANCE_TYPE=VARIANCE_COMPONENTS",
                    "  /BUILD_OPTIONS TARGET_CATEGORY_ORDER=ASCENDING INPUTS_CATEGORY_ORDER=ASCENDING"
                    " MAX_ITERATIONS=100\n    CONFIDENCE_LEVEL=95 DF_METHOD=RESIDUAL COVB=MODEL.",
                ],
            )
            phu["hon_hop"] = {"loai": loai}
            canh_bao.append(
                "Mô hình hỗn hợp: GENLINMIXED (giả khả dĩ tuyến tính hoá) ≠ R clmm/glmer (Laplace) ⇒ ước lượng "
                "lệch nhỏ là bình thường"
            )

    # (2) Complex Samples: trọng số hậu phân tầng theo SAP §4 (tầng đã gộp tính sẵn — dt["trong_so_tang"])
    ts, tang = dt.get("trong_so") or {}, dt.get("trong_so_tang") or {}
    if ts and tang:
        bn, bk, kc = ten(ts["bien_ngay"]), ten(ts["bien_khung"]), ten(ts["ket_cuc"])
        cum_ts = ten(ts.get("bien_cum"))
        if not (so.get(bn) and so.get(bk) and so.get(kc)) or not cum_ts:
            raise TuChoi("trọng số: biến ngày/khung giờ/kết cục phải là biến số và phải có biến cụm (SAP §4)")
        nhom = sorted({x["nhom"] for x in tang["o"]})
        so_tang = {nh: i for i, nh in enumerate(nhom, 1)}
        lenh = ["COMPUTE ebm_tang = $SYSMIS."]
        lenh += [
            f"IF ({bn} = {_so_r(x['ngay'])} AND {bk} = {_so_r(x['khung'])}) ebm_tang = {so_tang[x['nhom']]}."
            for x in tang["o"]
        ]
        lenh.append("COMPUTE ebm_n_tong_the = $SYSMIS.")
        lenh += [f"IF (ebm_tang = {so_tang[t_['nhom']]}) ebm_n_tong_the = {t_['N_h']:g}." for t_ in tang["tang"]]
        lenh += [
            f"COMPUTE ebm_co_kq = NOT MISSING({kc}).",
            "AGGREGATE /OUTFILE=* MODE=ADDVARIABLES OVERWRITE=YES /BREAK=ebm_tang /ebm_n_mau = SUM(ebm_co_kq).",
            # postStratify của R cho mỗi phiếu có kết cục trọng số Nₕ / nₕ (nₕ đếm trên phiếu CÓ kết cục). Tên biến
            # SPSS KHÔNG phân biệt hoa/thường — bản thử đầu dùng ebm_Nh + ebm_nh (cùng một biến) ⇒ mọi trọng số = 1.
            "COMPUTE ebm_w = ebm_n_tong_the / ebm_n_mau.",
            f"COMPUTE ebm_hl = ({kc} >= {ts['nguong_hai_long']:g}).",
            f"CSPLAN ANALYSIS /PLAN FILE={dd_spss(thu_muc_kq / 'trong_so.csaplan')}",
            f"  /PLANVARS ANALYSISWEIGHT=ebm_w /DESIGN CLUSTER={cum_ts} /ESTIMATOR TYPE=WR.",
        ]
        dong.extend(lenh)
        khoi(
            "trong_so_ty_le",
            [
                f"CSDESCRIPTIVES /PLAN FILE={dd_spss(thu_muc_kq / 'trong_so.csaplan')}",
                "  /SUMMARY VARIABLES=ebm_hl /MEAN /STATISTICS SE CIN(95) DEFF COUNT.",
            ],
        )
        phu["trong_so"] = {"so_tang": so_tang}
        pn = ten(ts.get("phoi_nhiem")) if ts.get("chay_svyolr") else None
        if pn:
            if not so.get(pn):
                raise TuChoi(f"trọng số: phơi nhiễm {pn} của svyolr phải là biến số")
            hb = [ten(c) for c in ts.get("hiep_bien") or []]
            dong.append(f"COMPUTE ebm_pn = {pn} / {float(ts.get('don_vi_phoi_nhiem') or 1):g}.")
            wi = ["ebm_pn"] + [v for v in hb if so.get(v)]
            by = [v for v in hb if not so.get(v)]
            khoi(
                "trong_so_thu_tu",
                [
                    f"CSORDINAL {kc}" + (f" BY {goi_ds(by)}" if by else "") + f"\n    WITH {goi_ds(wi)}",
                    f"  /PLAN FILE={dd_spss(thu_muc_kq / 'trong_so.csaplan')}",
                    "  /LINK FUNCTION=LOGIT /STATISTICS PARAMETER EXP SE CINTERVAL TTEST /PRINT SUMMARY.",
                ],
            )
            phu["trong_so"]["phoi_nhiem"] = ts.get("phoi_nhiem")
        canh_bao.append(
            "Trọng số: SPSS Complex Samples coi trọng số là CỐ ĐỊNH; R postStratify hiệu chỉnh theo tổng thể ⇒ ước "
            "lượng trùng, SE/KTC khác (so cả với R trọng số cố định — phải khớp)"
        )
    elif ts and not tang:
        canh_bao.append("trọng số: chưa tính được bảng tầng (thiếu số liệu HIS?) — bỏ khối Complex Samples")

    # (3) Độ tin cậy thang đo (Cronbach α + KTC Feldt qua ICC nhất quán, trung bình k mục)
    for i, (tn, cot_td) in enumerate((dt.get("thang_do") or {}).items(), 1):
        muc_td = [ten(c) for c in cot_td]
        chu = [c for c, v in zip(cot_td, muc_td) if not so.get(v)]
        if chu:
            raise TuChoi(f"thang đo «{tn}»: mục không phải biến số trong .sav: {', '.join(chu)}")
        if len(muc_td) < 2:
            raise TuChoi(f"thang đo «{tn}» cần ít nhất 2 mục")
        khoi(
            f"tin_cay_{i}",
            [
                f"RELIABILITY /VARIABLES={goi_ds(muc_td)}",
                f"  /SCALE({chuoi_spss(tn)}) ALL /MODEL=ALPHA /SUMMARY=TOTAL",
                "  /ICC=MODEL(MIXED) TYPE(CONSISTENCY) CIN=95 TESTVAL=0.",
            ],
        )
        phu.setdefault("tin_cay", []).append({"i": i, "ten": tn, "muc": list(cot_td)})

    if not dong or not any(x.startswith("OMSEND") for x in dong):
        return "", canh_bao, phu
    return "\n".join(dau + dong + ["OMSEND TAG='ebm_spv_bs'.", ""]), canh_bao, phu


def doc_ket_qua_bo_sung(thu_muc_kq: Path, dt: dict, man: dict) -> dict:
    """Đọc OXML của các khối bổ sung (+ bảng Test of Parallel Lines của PLUM ở phân tích chính)."""
    nguoc = {b["ten"]: b["cot"] for b in man["bien"]}
    if dt.get("ten_phoi_nhiem_mo_hinh") and dt.get("group"):
        nguoc[dt["ten_phoi_nhiem_mo_hinh"]] = dt["group"]
    ts = dt.get("trong_so") or {}
    if ts.get("phoi_nhiem"):
        nguoc["ebm_pn"] = ts["phoi_nhiem"]
    ra: dict = {}

    def bang(tag: str, *loai: str) -> list[dict]:
        p = thu_muc_kq / f"oms_{tag}.xml"
        return [b for b in phang_oxml(p) if _chuan_bang(b["bang"]) in loai] if p.exists() else []

    def doi_ten(d: dict) -> dict:
        return {nguoc.get(k, k): v for k, v in d.items()}

    tp = bang("da_bien", "testofparallellines")
    if tp:
        for hang, cot in _hang_theo_bien(tp[-1]).items():
            if hang and hang[-1].lower().startswith("general"):
                ra["po_tparallel"] = {"chi2": _lay(cot, "chi-square"), "df": _lay(cot, r"^df$"), "p": _lay(cot, "sig")}
    for x in dt.get("po_nguong") or []:
        bs = bang(f"po_nguong_{x['i']}", "variablesintheequation")
        if bs:
            ra.setdefault("po_nguong", {})[f"{x['k']:g}"] = doi_ten(he_so(bs[-1], mu=True))
    bs = bang("da_bien_hon_hop", "fixedcoefficients")
    if bs:
        hs = doi_ten(he_so(bs[-1], mu=True))
        for v in hs.values():  # KTC Wald chuẩn từ SE (R cũng dùng z) — bảng SPSS dùng t bậc tự do phần dư
            if v.get("b") is not None and v.get("se"):
                v["ci"] = [math.exp(v["b"] - 1.959964 * v["se"]), math.exp(v["b"] + 1.959964 * v["se"])]
        ra["hon_hop"] = {"thang": "OR", "he_so": hs}
        cp = bang("da_bien_hon_hop", "covarianceparameters")
        if cp:
            for hang, cot in _hang_theo_bien(cp[-1]).items():
                if hang and "intercept" in hang[-1].lower():
                    ra["hon_hop"]["phuong_sai_ngau_nhien"] = _lay(cot, r"^Estimate$")
    us = bang("trong_so_ty_le", "univariatestatistics")
    if us:
        for hang, cot in _hang_theo_bien(us[-1]).items():
            if hang and hang[-1] == "ebm_hl":
                ra.setdefault("trong_so", {})["ty_le"] = {
                    "p": _lay(cot, r"^Estimate$"),
                    "se": _lay(cot, r"^Standard Error$"),
                    "deff": _lay(cot, r"^Design Effect$"),
                    "n": _lay(cot, r"^Unweighted Count$"),
                }
    pe = bang("trong_so_thu_tu", "parameterestimates")
    if pe:
        hs = doi_ten(he_so(pe[-1], mu=True))
        for v in hs.values():  # so với R trên thang z: KTC/p dựng lại từ SE (bảng SPSS dùng t, bậc tự do = số cụm − 1)
            if v.get("b") is not None and v.get("se"):
                v["ci"] = [math.exp(v["b"] - 1.959964 * v["se"]), math.exp(v["b"] + 1.959964 * v["se"])]
                v["p"] = math.erfc(abs(v["b"] / v["se"]) / math.sqrt(2))
        ra.setdefault("trong_so", {})["thu_tu"] = hs
    for x in dt.get("tin_cay") or []:
        p = thu_muc_kq / f"oms_tin_cay_{x['i']}.xml"
        if not p.exists():
            continue
        kq: dict = {"muc": {}}
        for b in phang_oxml(p):
            loai, hang_cot = _chuan_bang(b["bang"]), _hang_theo_bien(b)
            if loai == "reliabilitystatistics":
                for cot in hang_cot.values():
                    kq["alpha"] = _lay(cot, "cronbach")
            elif loai == "intraclasscorrelationcoefficient":
                for hang, cot in hang_cot.items():
                    if hang and hang[-1].lower().startswith("average"):
                        kq["ktc95"] = [_lay(cot, "lower"), _lay(cot, "upper")]
            elif loai == "itemtotalstatistics":
                for hang, cot in hang_cot.items():
                    if hang:
                        kq["muc"][nguoc.get(hang[-1], hang[-1])] = {
                            "r_muc_tong": _lay(cot, "corrected item-total"),
                            "alpha_neu_bo": _lay(cot, "if item deleted", tru=("mean", "variance")),
                        }
            elif loai == "caseprocessingsummary":
                for hang, cot in hang_cot.items():
                    if hang and hang[-1].lower() == "valid":
                        kq["n"] = _lay(cot, r"^N$")
        ra.setdefault("tin_cay", {})[x["ten"]] = kq
    return ra


R_DOI_CHIEU = r"""# Sinh bởi tools/cau_noi_spss.py — số THAM CHIẾU bằng R cho phân tích bổ sung của SPSS
# (không phải phân tích chính).
# Đọc ĐÚNG tệp .sav SPSS dùng (haven, mã thiếu người dùng ⇒ NA), không đọc dữ liệu nào khác ngoài bảng Nₕ HIS tổng hợp.
suppressPackageStartupMessages({library(jsonlite); library(haven)})
a <- commandArgs(trailingOnly = TRUE)
P <- fromJSON(a[1], simplifyVector = TRUE)
d <- as.data.frame(zap_labels(read_sav(P$sav, user_na = FALSE)))
ten_spss <- unlist(P$ten_theo_cot)
i <- match(names(d), ten_spss)
names(d) <- ifelse(is.na(i), names(d), names(ten_spss)[i])
# @@KHOI_CHUAN_BI@@
hs_ra <- function(est, se, ten) {
  z <- qnorm(0.975); out <- list()
  for (v in ten) if (v %in% names(est) && v %in% names(se)) {
    b <- unname(est[[v]]); s <- unname(se[[v]])
    out[[v]] <- list(uoc_luong = exp(b), ci = c(exp(b - z * s), exp(b + z * s)),
                     p = 2 * pnorm(-abs(b / s)), b = b, se = s)
  }
  out
}
ra <- list(phien_ban_r = R.version.string)
du_bao <- c(P$group, P$covariates)
if (isTRUE(P$hon_hop)) ra$hon_hop <- tryCatch({
  X <- data.frame(.y = d[[P$outcome]], .cum = d[[P$cot_cum]])
  for (v in du_bao) X[[v]] <- if (is.numeric(d[[v]])) d[[v]] else factor(d[[v]])
  if (!is.null(P$don_vi_phoi_nhiem)) X[[P$group]] <- X[[P$group]] / P$don_vi_phoi_nhiem
  X <- X[stats::complete.cases(X), , drop = FALSE]
  X$.cum <- factor(X$.cum)
  vp <- paste(sprintf("`%s`", du_bao), collapse = " + ")
  if (P$loai == "ordinal") {
    suppressPackageStartupMessages(library(ordinal))
    X$.y <- factor(X$.y, ordered = TRUE)
    m <- clmm(stats::as.formula(paste(".y ~", vp, "+ (1 | .cum)")), data = X)
    est <- coef(m); se <- sqrt(diag(stats::vcov(m)))
    list(phuong_phap = "ordinal::clmm (Laplace)", he_so = hs_ra(est, se, du_bao),
         phuong_sai_ngau_nhien = as.numeric(ordinal::VarCorr(m)[[1]][1]), n = nrow(X))
  } else {
    suppressPackageStartupMessages(library(lme4))
    lv <- sort(unique(X$.y)); X$.y <- as.integer(X$.y == lv[length(lv)])
    m <- glmer(stats::as.formula(paste(".y ~", vp, "+ (1 | .cum)")), data = X, family = stats::binomial)
    est <- lme4::fixef(m); v <- as.matrix(stats::vcov(m)); se <- stats::setNames(sqrt(diag(v)), rownames(v))
    list(phuong_phap = "lme4::glmer (Laplace)", he_so = hs_ra(est, se, du_bao),
         phuong_sai_ngau_nhien = as.numeric(lme4::VarCorr(m)[[1]][1]), n = nrow(X))
  }
}, error = function(e) list(loi = conditionMessage(e)))
if (!is.null(P$trong_so)) ra$trong_so <- tryCatch({
  suppressPackageStartupMessages(library(survey))
  source(P$ham_r, encoding = "UTF-8")
  ts <- P$trong_so
  N_his <- utils::read.csv(P$his, stringsAsFactors = FALSE)
  b0 <- bang_tang(d, N_his, ts$bien_ngay, ts$bien_khung)
  gop <- gop_tang_nho(b0, ts$n_toi_thieu)
  kh <- bang_kich_hoat(gop$bang, ts$nguong_lech)
  diem <- suppressWarnings(as.numeric(d[[ts$ket_cuc]]))
  dd <- d[!is.na(diem), , drop = FALSE]
  dd$.hl <- as.integer(diem[!is.na(diem)] >= ts$nguong_hai_long)
  o <- sprintf("N%s_K%s", dd[[ts$bien_ngay]], dd[[ts$bien_khung]])
  dd$.tang <- gop$bang$nhom[match(o, sprintf("N%s_K%s", gop$bang$ngay, gop$bang$khung))]
  dd$.w <- kh$bang$N_h[match(dd$.tang, kh$bang$nhom)] / as.numeric(table(dd$.tang)[dd$.tang])
  co_tt <- isTRUE(ts$chay_svyolr) && !is.null(ts$phoi_nhiem) && nzchar(ts$phoi_nhiem)
  if (co_tt) {
    dd$.yo <- factor(diem[!is.na(diem)], ordered = TRUE)
    dd$.pn <- as.numeric(dd[[ts$phoi_nhiem]]) / ts$don_vi_phoi_nhiem
  }
  ids <- stats::as.formula(paste0("~", ts$bien_cum))
  tk0 <- svydesign(ids = ids, data = dd)
  pop <- stats::setNames(data.frame(kh$bang$nhom, kh$bang$N_h), c(".tang", "Freq"))
  tk_ps <- postStratify(tk0, strata = ~.tang, population = pop)
  tk_cd <- svydesign(ids = ids, weights = ~.w, data = dd)
  ty_le <- function(tk) {
    m <- svymean(~.hl, tk, deff = "replace")  # như 04a (n hiệu dụng cho KTC Wilson)
    m2 <- svymean(~.hl, tk, deff = TRUE)       # định nghĩa SPSS CSDESCRIPTIVES dùng (đo 14/11/2026: trùng)
    list(p = unname(coef(m)[1]), se = unname(SE(m)[1]), deff = unname(deff(m)[1]), deff_spss = unname(deff(m2)[1]))
  }
  out <- list(bang = gop$bang[, c("ngay", "khung", "nhom", "N_h")], nhat_ky = I(gop$nhat_ky),
              kich_hoat = kh$kich_hoat, lech_max = kh$lech_max, so_tang = nrow(kh$bang),
              ty_le = list(hau_phan_tang = ty_le(tk_ps), co_dinh = ty_le(tk_cd)))
  if (co_tt) {
    hb <- ts$hiep_bien
    f <- stats::as.formula(paste(".yo ~", paste(c(".pn", sprintf("`%s`", hb)), collapse = " + ")))
    tt <- function(tk) {
      fit <- svyolr(f, design = tk)
      est <- coef(fit); se <- sqrt(diag(stats::vcov(fit)))
      names(est)[names(est) == ".pn"] <- ts$phoi_nhiem; names(se)[names(se) == ".pn"] <- ts$phoi_nhiem
      hs_ra(est, se, c(ts$phoi_nhiem, hb))
    }
    out$thu_tu <- list(hau_phan_tang = tt(tk_ps), co_dinh = tt(tk_cd))
  }
  out
}, error = function(e) list(loi = conditionMessage(e)))
write_json(ra, a[2], auto_unbox = TRUE, digits = NA, null = "null", na = "null", pretty = TRUE)
"""


def tim_rscript() -> str | None:
    env = os.environ.get("EBM_RSCRIPT", "").strip()
    return env or shutil.which("Rscript")


def ma_r_chuan_bi_tham_chieu(study: str, gate: str, man: dict, dt: dict) -> str:
    """F3 (14/11/2026): R tham chiếu của khối bổ sung đọc .sav (không có biến phái sinh, chưa lọc, chưa có biến giả) —
    sinh ĐÚNG ba khối như SPSS/Python: biến phái sinh → lọc quần thể → biến giả (dữ liệu R tên `d`). Trước bản vá: số
    tham chiếu R tính trên dữ liệu CHƯA lọc và cột mã số ⇒ «LỆCH» giả khi SAP có lọc/biến phân loại."""
    import bien_phai_sinh as BPS  # noqa: PLC0415

    tom = _doc_json(thu_muc_de_tai(study) / f"{gate}_analysis_summary.json")
    csv_khoa = Path(man.get("nguon_csv") or "")
    ma = ""
    if (tom.get("bien_phai_sinh") or {}).get("bien"):
        ma, _ds, _muc = BPS.khoi_cho_cau_noi(thu_muc_de_tai(study), tom, "r", csv_khoa, bien_d="d")
    ma += BPS.khoi_loc_cau_noi(tom, "r", bien_d="d")
    for c, v in (dt.get("hiep_bien_phan_loai") or {}).items():
        for muc, t in zip(v["muc"], v["ten"]):
            ma += (f"d[[{json.dumps(t)}]] <- ifelse(is.na(d[[{json.dumps(c)}]]), NA_real_, "
                   f"as.numeric(d[[{json.dumps(c)}]] == {float(muc)!r}))\n")  # fmt: skip
    return ma


def chay_r_tham_chieu(
    man: dict, dt: dict, sav: Path, thu_muc: Path, *, his: Path | None, thoi_han: int = 900, khoi_r: str = ""
) -> dict:
    """Chạy R (clmm/glmer + survey) trên CÙNG tệp .sav ⇒ {hon_hop, trong_so} hoặc {"loi": …}. Không có R ⇒ «loi».
    khoi_r = mã chuẩn bị (biến phái sinh · lọc · biến giả — ma_r_chuan_bi_tham_chieu) chèn ngay sau khi đọc .sav."""
    can_hh = bool((dt.get("hon_hop_da_sinh")) and dt.get("cot_cum"))
    can_ts = bool(dt.get("trong_so") and dt.get("trong_so_tang") and his)
    if not (can_hh or can_ts):
        return {}
    rs = tim_rscript()
    if not rs:
        return {"loi": "máy không có Rscript (đặt EBM_RSCRIPT nếu cài chỗ khác) — chưa có số tham chiếu R"}
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import g6_trong_so_survey as TSS  # noqa: PLC0415 — hàm R thuần CHÍNH THỨC của SAP (bang_tang, gop_tang_nho…)

    loai = dt.get("outcome_type_da_xac_dinh") or dt.get("outcome_type")
    tham_so = {
        "sav": str(sav),
        "ten_theo_cot": {b["cot"]: b["ten"] for b in man["bien"]},
        "loai": loai,
        "outcome": dt.get("outcome"),
        "group": dt.get("group"),
        "covariates": list(dt.get("covariates_mo_hinh") or dt.get("covariates") or []),
        "cot_cum": dt.get("cot_cum"),
        "don_vi_phoi_nhiem": dt.get("don_vi_phoi_nhiem") if loai == "ordinal" else None,
        "hon_hop": can_hh,
        "trong_so": dt.get("trong_so") if can_ts else None,
        "his": str(his) if can_ts else None,
        "ham_r": str(thu_muc / TEP_HAM_TRONG_SO),
    }
    (thu_muc / TEP_HAM_TRONG_SO).write_text(TSS.R_HAM, encoding="utf-8", newline="\n")
    (thu_muc / "r_tham_so.json").write_text(json.dumps(tham_so, ensure_ascii=False), encoding="utf-8", newline="\n")
    (thu_muc / "r_doi_chieu.R").write_text(R_DOI_CHIEU.replace("# @@KHOI_CHUAN_BI@@\n", khoi_r), encoding="utf-8",
                                           newline="\n")  # fmt: skip
    ma, out, err = _chay_lenh(
        [rs, "--vanilla", str(thu_muc / "r_doi_chieu.R"), str(thu_muc / "r_tham_so.json"), str(thu_muc / "r_kq.json")],
        thu_muc=thu_muc,
        thoi_han=thoi_han,
        nhan="LOI_R",
    )
    kq = _doc_json(thu_muc / "r_kq.json")
    if ma != 0 or not kq:
        return {"loi": "R báo lỗi: " + (err or out).strip()[-600:]}
    return kq


def tin_cay_python(man: dict, thang_do: dict[str, list[str]]) -> dict:
    """Cronbach α, KTC Feldt, r mục–tổng hiệu chỉnh, α nếu bỏ mục bằng `kiem_tin_cay_thang_do.py` trên CÙNG dữ liệu
    nguồn của .sav, với CÙNG mã thiếu (mã chữ ⇒ NaN, mã số khai trong _ma-thieu-theo-bien.csv ⇒ NaN)."""
    import pandas as pd  # noqa: PLC0415

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import kiem_tin_cay_thang_do as K  # noqa: PLC0415

    bien = {b["cot"]: b for b in man["bien"]}
    df = pd.read_csv(man["nguon_csv"], dtype=str, encoding="utf-8-sig", keep_default_na=False)
    ra: dict = {}
    for tn, cot in thang_do.items():
        try:
            sub = df[cot].copy()
            ma_so: set[float] = set()
            for c in cot:
                for ma in (bien.get(c) or {}).get("ma_chu") or {}:
                    sub[c] = sub[c].mask(sub[c].str.strip() == ma, "")
                ma_so |= {float(x) for x in (bien.get(c) or {}).get("ma_thieu_so") or []}
            sub = sub.replace("", None)
            kq = K.phan_tich_thang(tn, K.chuan_hoa_muc(sub, cot, sorted(ma_so)), None, None)
            ra[tn] = {
                "alpha": kq.get("alpha"),
                "ktc95": kq.get("alpha_ktc95"),
                "n": kq.get("n_dung"),
                "muc": {m["muc"]: {"r_muc_tong": m["r_muc_tong_hieu_chinh"], "alpha_neu_bo": m["alpha_neu_bo_muc"]}
                        for m in kq.get("muc") or []},
                "ma_thieu_so": sorted(ma_so),
            }  # fmt: skip
        except (K.LoiDauVao, KeyError, ValueError) as e:
            ra[tn] = {"loi": str(e)}
    return ra


def _dong_tu_so(muc: str, py, sp, *, khop: bool, ghi_chu: str = "", lech_nho: bool = False) -> dict:
    return {
        "muc": muc,
        "python": py,
        "spss": sp,
        "kiem": {},
        "trang_thai": "khop" if khop else ("lech_nho" if lech_nho else "lech"),
        "ghi_chu": ghi_chu,
    }


def doi_chieu_bo_sung(tom: dict, kq: dict, dt: dict, *, r: dict | None = None, tin_cay_py: dict | None = None) -> tuple:
    """Dòng đối chiếu của phân tích bổ sung + thông tin không so được. Trả (dòng, thông tin)."""
    dong: list[dict] = []
    tt: list[str] = []
    bs = kq.get("bo_sung") or {}
    r = r or {}

    # (4) Giả định tỷ lệ odds tại từng ngưỡng: SPSS LOGISTIC ↔ ordinal_model (Python)
    od = tom.get("ordinal") or {}
    if dt.get("po_nguong"):
        sp_ng = bs.get("po_nguong") or {}
        for x in od.get("kiem_gia_dinh_ty_le_odds") or []:
            k = x.get("nguong", "").replace("Y >", "").strip()
            if x.get("loi"):
                dong.append(_khong_so(f"Giả định tỷ lệ odds — {x.get('nguong')}", f"Python lỗi: {x['loi']}"))
                continue
            for v, or_py in (x.get("OR") or {}).items():
                sp = (sp_ng.get(k) or {}).get(v)
                if sp is None:
                    dong.append(
                        _khong_so(f"Giả định tỷ lệ odds — OR tại {x.get('nguong')} — {v}", "SPSS không có hệ số này")
                    )
                    continue
                dong.append(
                    so_mot(
                        f"Giả định tỷ lệ odds — OR tại {x.get('nguong')} — {v}",
                        {"uoc_luong": or_py, "ci": None},
                        {"uoc_luong": sp["uoc_luong"], "ci": None},
                        ty_so=True,
                        lam_tron=LAM_TRON["ty_so"],
                    )
                )
        br, tp = (od.get("brant") or {}).get("tong") or {}, bs.get("po_tparallel") or {}
        if br.get("p") is not None and tp.get("p") is not None:
            cung = (br["p"] < 0.05) == (tp["p"] < 0.05)
            dong.append(
                _dong_tu_so(
                    "Giả định tỷ lệ odds — kiểm định tổng (kết luận ở 0,05)",
                    {"uoc_luong": br["p"]},
                    {"uoc_luong": tp["p"]},
                    khop=cung,
                    lech_nho=not cung,
                    ghi_chu=f"Brant (Wald, Python) χ²={br.get('chi2')} df={br.get('df')} ≠ Test of Parallel Lines (LR, "
                    f"SPSS) χ²={_fmt(tp.get('chi2'))} df={_fmt(tp.get('df'))} — hai kiểm định khác nhau, "
                    "chỉ so kết luận",
                )
            )

    # (1) Mô hình hỗn hợp: SPSS GENLINMIXED ↔ R clmm/glmer
    if dt.get("hon_hop_da_sinh"):
        hh_r, hh_sp = r.get("hon_hop") or {}, bs.get("hon_hop") or {}
        ten_hh = f"Mô hình hỗn hợp — intercept ngẫu nhiên theo {dt.get('cot_cum')}"
        if r.get("loi") or hh_r.get("loi") or not hh_r:
            dong.append(_khong_so(ten_hh, f"chưa có tham chiếu R: {r.get('loi') or hh_r.get('loi') or 'không chạy'}"))
        elif not hh_sp:
            dong.append(_khong_so(ten_hh, "SPSS thiếu bảng GENLINMIXED (xem nhật ký bổ sung)"))
        else:
            for v in [dt.get("group"), *(dt.get("covariates_mo_hinh") or dt.get("covariates") or [])]:  # F3: biến giả
                a, b = (hh_r.get("he_so") or {}).get(v), (hh_sp.get("he_so") or {}).get(v)
                if not a or not b:
                    dong.append(_khong_so(f"{ten_hh} — {v}", "không có hệ số cùng tên ở một bên (biến phân loại?)"))
                    continue
                dong.append(
                    so_mot(
                        f"{ten_hh} — {v} (tham chiếu R)",
                        {"uoc_luong": a["uoc_luong"], "ci": a["ci"], "p": a["p"]},
                        {"uoc_luong": b["uoc_luong"], "ci": b["ci"], "p": b["p"]},
                        phuong_phap_khac=f"GENLINMIXED (giả khả dĩ) ≠ {hh_r.get('phuong_phap')}",
                        ty_so=True,
                    )
                )
            tt.append(
                f"Phương sai intercept ngẫu nhiên ({dt.get('cot_cum')}): "
                f"SPSS {_fmt(hh_sp.get('phuong_sai_ngau_nhien'))}"
                f" · R {_fmt(hh_r.get('phuong_sai_ngau_nhien'))}"
            )

    # (2) Trọng số hậu phân tầng: bảng tầng Python ↔ R 04a; SPSS CS ↔ R (cố định: phải khớp; postStratify: lệch nhỏ)
    if dt.get("trong_so_tang"):
        ts_r, ts_sp, tang_py = r.get("trong_so") or {}, bs.get("trong_so") or {}, dt["trong_so_tang"]
        if r.get("loi") or ts_r.get("loi") or not ts_r:
            dong.append(
                _khong_so("Trọng số hậu phân tầng", f"chưa có tham chiếu R: {r.get('loi') or ts_r.get('loi') or '—'}")
            )
        else:
            o_r = {(float(x["ngay"]), float(x["khung"])): x["nhom"] for x in _hang_r(ts_r.get("bang"))}
            o_py = {(float(x["ngay"]), float(x["khung"])): x["nhom"] for x in tang_py["o"]}
            cung = o_r == o_py and bool(ts_r.get("kich_hoat")) == bool(tang_py["kich_hoat"])
            dong.append(
                _dong_tu_so(
                    "Trọng số — bảng tầng sau gộp + quy tắc kích hoạt (cầu nối Python ↔ hàm R 04a)",
                    {"uoc_luong": f"{tang_py['so_tang_sau_gop']} tầng, kích hoạt={tang_py['kich_hoat']}"},
                    {"uoc_luong": f"{ts_r.get('so_tang')} tầng, kích hoạt={ts_r.get('kich_hoat')}"},
                    khop=cung,
                    ghi_chu=""
                    if cung
                    else "hai bản của cùng thuật toán gộp tầng cho kết quả KHÁC — dừng, báo thống kê viên",
                )
            )
            tl = ts_sp.get("ty_le") or {}

            def _ci(x: dict) -> list | None:
                return [x["p"] - 1.959964 * x["se"], x["p"] + 1.959964 * x["se"]] if x.get("se") is not None else None

            for khoa, nhan, khac in (
                ("co_dinh", "R trọng số cố định", None),
                (
                    "hau_phan_tang",
                    "R postStratify",
                    "R hậu phân tầng hiệu chỉnh SE theo tổng thể ≠ SPSS trọng số cố định",
                ),
            ):
                rr = (ts_r.get("ty_le") or {}).get(khoa) or {}
                if tl.get("p") is None or rr.get("p") is None:
                    dong.append(_khong_so(f"Tỷ lệ hài lòng có trọng số — {nhan}", "thiếu ước lượng ở một bên"))
                    continue
                dong.append(
                    so_mot(
                        f"Tỷ lệ hài lòng có trọng số (SE ⇒ KTC Wald) — {nhan}",
                        {"uoc_luong": rr["p"], "ci": _ci(rr)},
                        {"uoc_luong": tl["p"], "ci": _ci(tl)},
                        phuong_phap_khac=khac,
                    )
                )
                tt.append(
                    f"DEFF tỷ lệ có trọng số — SPSS {_fmt(tl.get('deff'))} · {nhan}: cùng định nghĩa SPSS "
                    f"{_fmt(rr.get('deff_spss'))}, deff='replace' của 04a (n hiệu dụng Wilson) {_fmt(rr.get('deff'))}"
                )
            for khoa, nhan, khac in (
                ("co_dinh", "R svyolr trọng số cố định", None),
                ("hau_phan_tang", "R svyolr postStratify", "R hậu phân tầng ≠ SPSS trọng số cố định (SE)"),
            ):
                hr = ((ts_r.get("thu_tu") or {}).get(khoa)) or {}
                hs = ts_sp.get("thu_tu") or {}
                for v in hr:
                    if v not in hs:
                        dong.append(_khong_so(f"Thứ tự có trọng số — {v} — {nhan}", "SPSS không có hệ số cùng tên"))
                        continue
                    dong.append(
                        so_mot(
                            f"Thứ tự có trọng số — {v} — {nhan}",
                            {"uoc_luong": hr[v]["uoc_luong"], "ci": hr[v]["ci"], "p": hr[v]["p"]},
                            {"uoc_luong": hs[v]["uoc_luong"], "ci": hs[v]["ci"], "p": hs[v]["p"]},
                            phuong_phap_khac=khac,
                            ty_so=True,
                        )
                    )

    # (3) Độ tin cậy: SPSS RELIABILITY ↔ kiem_tin_cay_thang_do.py
    for x in dt.get("tin_cay") or []:
        tn = x["ten"]
        py, sp = (tin_cay_py or {}).get(tn) or {}, (bs.get("tin_cay") or {}).get(tn) or {}
        if py.get("loi") or not py:
            dong.append(_khong_so(f"Tin cậy — {tn}", f"Python: {py.get('loi') or 'không tính được'}"))
            continue
        if not sp.get("alpha"):
            dong.append(_khong_so(f"Tin cậy — {tn}", "SPSS thiếu bảng RELIABILITY"))
            continue
        d1 = so_mot(
            f"Tin cậy — {tn} — Cronbach α (KTC Feldt)",
            {"uoc_luong": py["alpha"], "ci": py.get("ktc95")},
            {"uoc_luong": sp["alpha"], "ci": sp.get("ktc95")},
        )
        if py.get("n") is not None and sp.get("n") is not None and int(py["n"]) != int(sp["n"]):
            d1["trang_thai"] = "lech"
            d1["ghi_chu"] = f"số ca dùng KHÁC: Python {py['n']} · SPSS {int(sp['n'])} — mã thiếu xử lý khác nhau?"
        dong.append(d1)
        lech_max, thieu = 0.0, []
        for m, a in (py.get("muc") or {}).items():
            b = (sp.get("muc") or {}).get(m)
            if not b:
                thieu.append(m)
                continue
            for k in ("r_muc_tong", "alpha_neu_bo"):
                if a.get(k) is not None and b.get(k) is not None:
                    lech_max = max(lech_max, abs(a[k] - b[k]))
        dong.append(
            _dong_tu_so(
                f"Tin cậy — {tn} — r mục–tổng hiệu chỉnh + α nếu bỏ mục ({len(py.get('muc') or {})} mục)",
                {"uoc_luong": f"{len(py.get('muc') or {})} mục"},
                {"uoc_luong": f"lệch lớn nhất {lech_max:.2g}"},
                khop=lech_max <= 0.0005 and not thieu,
                ghi_chu=(f"SPSS thiếu mục: {', '.join(thieu)}" if thieu else ""),
            )
        )
    return dong, tt


def _hang_r(bang) -> list[dict]:
    """jsonlite ghi data.frame thành danh sách bản ghi (hoặc cột) — chuẩn hoá về danh sách bản ghi."""
    if isinstance(bang, list):
        return bang
    if isinstance(bang, dict) and bang:
        k = list(bang)
        return [dict(zip(k, v)) for v in zip(*(bang[x] for x in k))]
    return []


# ───────────────────────────── (5) cú pháp xem trước cho run_g6_auto.py ─────────────────────────────

TEP_SPS_G6, TEP_SPS_G6_BS = "05_spss_phan_tich.sps", "05b_spss_bo_sung.sps"
_THIET_KE_SPS = ("rct", "cohort", "cross_sectional", "case_control")


def man_tu_tu_dien(td: dict[str, dict], ma_thieu: list[dict], sav: Path) -> tuple[dict, list[str]]:
    """Manifest «giả» dựng từ RIÊNG từ điển G5 (G6 sinh script TRƯỚC khi có dữ liệu): tên SPSS theo «Tên SPSS: …»,
    mã mức theo lựa chọn, biến số theo kiểu kiểm tra. Trường định danh/descriptive bị bỏ (bộ khoá đã khử định danh)."""
    tieu_de: list[str] = []
    tk: list[dict] = []
    for ten, d in td.items():
        loai = d.get("loai", "").lower()
        if loai == "descriptive" or d.get("dinh_danh", "").lower() in ("y", "yes", "1"):
            continue
        lc = lua_chon(d)
        if loai == "checkbox":
            for ma in lc:
                tieu_de.append(f"{ten}___{ma}")
                tk.append(
                    {"rong": 1, "le": 0, "nguyen": 1, "khong_so": set(), "gia_tri": {"0", "1"}, "nhieu_muc": False}
                )
            continue
        if lc:
            ma = set(lc)
            tk.append(
                {
                    "rong": max(len(m.encode("utf-8")) for m in ma),
                    "le": 0,
                    "nguyen": max(len(m) for m in ma),
                    "khong_so": {m for m in ma if _so(m) is None},
                    "gia_tri": ma,
                    "nhieu_muc": len(ma) > TRAN_MUC_LIET_KE,
                }
            )
        elif (
            d.get("kiem_tra", "") in ("integer", "number")
            or loai == "calc"
            or d.get("kiem_tra", "").startswith("number")
        ):
            le = 0 if d.get("kiem_tra") == "integer" else 2
            tk.append({"rong": 8, "le": le, "nguyen": 6, "khong_so": set(), "gia_tri": set(), "nhieu_muc": True})
        else:
            tk.append({"rong": 255, "le": 0, "nguyen": 1, "khong_so": {"chữ"}, "gia_tri": set(), "nhieu_muc": True})
        tieu_de.append(ten)
    ke, canh_bao, _ = ke_hoach_bien(tieu_de, tk, td, ma_thieu)
    bien = [
        {k: b[k] for k in ("cot", "ten", "so", "muc_do", "nhan", "muc", "ma_chu", "ma_thieu_so")}
        for b in ke
        if not b["bo"]
    ]
    return {"bien": bien, "sav": str(sav)}, canh_bao


def sps_tu_tu_dien(
    study: str, thu_muc: Path, v: dict, ts: dict | None, design_code: str, *, sinh_ton: bool = False
) -> tuple[dict[str, str], list[str]]:
    """Cú pháp SPSS XEM TRƯỚC (tên biến thật, đặc tả theo SAP/dictionary) để run_g6_auto ghi cạnh script R.

    Trả ({tên tệp: nội dung}, cảnh báo). Thiết kế không có mô hình hồi quy tương ứng (chẩn đoán, dự báo, tổng quan,
    định tính) ⇒ rỗng. Sau khi KHOÁ dữ liệu: `xuat-sav` → `cu-phap` sinh lại bản khớp dữ liệu (độ rộng, mức thật)."""
    if design_code not in _THIET_KE_SPS:
        return {}, [f"thiết kế {design_code}: không có cú pháp SPSS tương ứng — bỏ qua"]
    td_p = thu_muc / f"G5_REDCap_dictionary_{study}.csv"
    td = doc_tu_dien(td_p)
    man, canh_bao = man_tu_tu_dien(
        td, doc_ma_thieu(thu_muc / "_ma-thieu-theo-bien.csv"), thu_muc / "spss" / f"{study}_khoa.sav"
    )
    sinh_ton = sinh_ton and bool(v.get("time_col"))  # cùng cờ _is_cox_like của run_g6_auto
    thu_tu = bool(v.get("outcome_ordinal"))
    dv = (ts or {}).get("don_vi_phoi_nhiem")
    dt = {
        "outcome": None if sinh_ton else v.get("outcome"),
        "group": v.get("exposure"),
        "covariates": [c for c in v.get("covariates") or [] if c],
        "outcome_type": "ordinal" if thu_tu else "auto",
        "time": v.get("time_col") if sinh_ton else None,
        "event": v.get("outcome") if sinh_ton else None,
        "cot_cum": v.get("cluster_col"),
        "don_vi_phoi_nhiem": float(dv) if thu_tu and dv and float(dv) > 1 else None,
        "thang_do": {},
        "hon_hop": True,
        "trong_so": None,
        "trong_so_tang": None,
    }
    kq = thu_muc / "spss" / "ket_qua"
    dau = [
        _chu_thich(
            "BẢN XEM TRƯỚC do run_g6_auto.py sinh TỪ từ điển G5 + SAP, TRƯỚC khi có dữ liệu — cùng đặc tả với script R"
        ),
        _chu_thich(
            f"Sau khi khoá dữ liệu: python3 tools/cau_noi_spss.py xuat-sav --study {study} rồi cu-phap sinh lại bản "
            "khớp dữ liệu; kiểm chéo bằng phần mềm thứ hai, KHÔNG phải phân tích chính G6"
        ),
    ]
    vb, cb, _ = cu_phap_phan_tich(study, man, dt, kq)
    vb_bs, cb_bs, _ = cu_phap_bo_sung(study, man, dt, kq)
    ra = {TEP_SPS_G6: "\n".join(dau) + "\n" + vb}
    if vb_bs:
        ra[TEP_SPS_G6_BS] = "\n".join(dau) + "\n" + vb_bs
    return ra, canh_bao + cb + cb_bs


def doan_a7_spss(ten_tep: list[str], canh_bao: list[str]) -> str:
    """Khối mô tả cho artifact A7 của G6."""
    dong = [
        "",
        "## Cú pháp SPSS xem trước (cầu nối IBM SPSS — kiểm chéo bằng phần mềm thứ hai)",
        "",
        f"- Tệp: {', '.join(f'`scripts/{t}`' for t in ten_tep)} — cùng đặc tả với script R (biến thật, SAP).",
        "- Sinh TỪ từ điển G5 trước khi có dữ liệu. Sau khi khoá: `tools/cau_noi_spss.py xuat-sav` → `cu-phap` → `chay`"
        " → `doi-chieu` (đối chiếu từng ước lượng với Python; mô hình hỗn hợp / Complex Samples có tham chiếu R).",
        "- Không thay script R/Python là phân tích chính; bộ chấm G6 không đọc tệp .sps.",
    ]
    dong += [f"- ⚠️ {c}" for c in canh_bao[:6]]
    return "\n".join(dong) + "\n"


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
        # «cobhyt» (có BHYT — có/không) KHÔNG phải số thẻ: chỉ bắt so/ma/the_bhyt (đo trên từ điển C1a 14/11/2026)
        if not ly_do and re.search(
            r"(ho_?ten|hoten|ten_?bn|dien_?thoai|(^|_)sdt|cccd|cmnd|(so|ma|the)_?bhyt|dia_?chi|ngay_?sinh|email|phone"
            r"|(^|_)name($|_))",
            c.lower(),
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


def mo_ta_thieu(thieu: list) -> str:
    """[kiểu, a, b, c] của spss.Dataset().varlist[i].missingValues ⇒ chữ. kiểu 1–3: giá trị rời; −2: khoảng a..b;
    −3: khoảng a..b + giá trị c. Cận vô hạn của khoảng (LO/HI) ghi «LO»/«HI» — bản cũ in số 309 chữ số."""

    def mot(x) -> str:
        if isinstance(x, str) and x in ("LO", "HI"):
            return x
        so = _so(str(x))
        if so is not None and abs(so) >= 1e300:
            return "LO" if so < 0 else "HI"
        return _ma_gon(str(x))

    k = thieu[0] if thieu else 0
    if k in (-2, -3):
        ra = f"{mot(thieu[1])} THRU {mot(thieu[2])}"
        return ra + (f", {mot(thieu[3])}" if k == -3 and thieu[3] is not None else "")
    return ", ".join(mot(x) for x in thieu[1 : 1 + max(0, int(k))] if x is not None)


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
                ghi += " Mã thiếu SPSS: " + mo_ta_thieu(thieu) + "."
            dong = dict.fromkeys(COT_REDCAP, "")
            dong.update({COT_REDCAP[0]: ten, COT_REDCAP[1]: "nhap_tu_spss", COT_REDCAP[3]: loai,
                         COT_REDCAP[4]: b.get("nhan") or b["ten"],
                         COT_REDCAP[5]: " | ".join(f"{m}, {v}" for m, v in ngl.items()), COT_REDCAP[7]: kt,
                         COT_REDCAP[17]: ghi})  # fmt: skip
            w.writerow(dong)


def _trong_repo_git(p: Path) -> Path | None:
    """Thư mục `p` nằm trong một cây git nào (BẤT KỲ repo nào, không chỉ checkout đang chạy) — so không phân biệt
    hoa/thường (ổ đĩa Mac/Windows mặc định không phân biệt: `/users/…` cũng là `/Users/…`)."""
    p = Path(os.path.normcase(os.path.realpath(p)))
    goc = Path(os.path.normcase(os.path.realpath(BASE)))
    if p == goc or goc in p.parents:
        return goc
    for cha in [p, *p.parents]:
        if (cha / ".git").exists():
            return cha
    return None


def lenh_nhap_sav(args) -> int:
    sav = Path(args.sav).expanduser().resolve()
    if not sav.exists() or sav.suffix.lower() != ".sav":
        raise TuChoi(f"không thấy tệp .sav: {sav}")
    ra = Path(args.ra).expanduser().resolve() if args.ra else sav.parent / f"{sav.stem}_tu_spss"
    repo = _trong_repo_git(ra if ra.exists() else ra.parent)
    if repo:
        raise TuChoi(
            f"thư mục ra nằm TRONG một repo git ({repo}) — dữ liệu chưa qua cổng tiếp nhận phải ở ngoài repo "
            "(chọn --ra khác)"
        )
    py = tim_spss()
    with vung_tam() as tam_s:
        tam = Path(tam_s)
        shutil.copyfile(sav, tam / "vao.sav")
        ma, out, err = chay_spss(py, ["--tu-dien", str(tam / "vao.sav"), str(tam / "tu_dien.json")], thu_muc=tam)
        if ma != 0 or not (tam / "tu_dien.json").exists():
            print("🔴 SPSS không đọc được tệp .sav —", (err or out).strip()[-600:])
            return MA_LECH
        td = _doc_json(tam / "tu_dien.json")
        # Quét tên/nhãn nghi PII TRƯỚC khi ghi bất kỳ tệp dữ liệu nào ra đĩa (bản cũ ghi CSV rồi mới từ chối).
        pii = _quet_pii_ten([b["ten"] for b in td.get("bien", [])] + [b.get("nhan", "") for b in td.get("bien", [])])
        if pii:
            print("🔴 Nghi PII — KHÔNG xuất dữ liệu trước khi khử định danh:\n   " + "\n   ".join(pii))
            return MA_TU_CHOI
        ra.mkdir(parents=True, exist_ok=True)
        csv_p, td_p = ra / f"{sav.stem}.csv", ra / f"{sav.stem}_tu_dien.json"
        shutil.copyfile(tam / "tu_dien.json", td_p)
        lenh = [
            "GET FILE={}.",
            "SAVE TRANSLATE OUTFILE={} /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE.",
            "",
        ]
        (ra / f"{sav.stem}_xuat_csv.sps").write_text(  # bản người đọc (đường dẫn thật)
            "\n".join(lenh).format(dd_spss(sav), dd_spss(csv_p)), encoding="utf-8", newline="\n"
        )
        (tam / "xuat_csv.sps").write_text(
            "\n".join(lenh).format(dd_spss(tam / "vao.sav"), dd_spss(tam / "ra.csv")), encoding="utf-8", newline="\n"
        )
        ma, out, err = chay_spss(py, ["--cu-phap", str(tam / "xuat_csv.sps")], thu_muc=tam)
        if ma != 0 or not (tam / "ra.csv").exists():
            print("🔴 SPSS không xuất được CSV —", (err or out).strip()[-600:])
            return MA_LECH
        b = (tam / "ra.csv").read_bytes()
        # SAVE TRANSLATE /ENCODING='UTF8' ghi BOM — cổng tiếp nhận đọc tiêu đề nguyên văn
        csv_p.write_bytes(b[3:] if b.startswith(b"\xef\xbb\xbf") else b)
    rc_p = ra / f"{sav.stem}_tu_dien_redcap.csv"
    ghi_tu_dien_redcap(td.get("bien", []), rc_p)
    print(f"✓ {csv_p} ({td.get('so_ca')} ca · {len(td.get('bien', []))} biến) + từ điển nhãn {td_p.name}")
    print(f"✓ Từ điển dạng REDCap (khuôn G5, tên gốc giữ ở «Tên SPSS: …»): {rc_p.name}")
    co_thieu = [b["ten"] for b in td.get("bien", []) if (b.get("thieu") or [0])[0]]
    if co_thieu:
        print(
            f"⚠ {len(co_thieu)} biến có mã thiếu do người dùng định nghĩa (CSV giữ NGUYÊN giá trị mã — "
            f"bước làm sạch phải xử lý theo từ điển): {', '.join(co_thieu[:12])}"
        )
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
    x.add_argument("--giu-ghi-chu", action="store_true", help="giữ trường văn bản tự do (notes) trong .sav")
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
            p.add_argument(
                "--don-vi-phoi-nhiem", type=float, help="OR cho MỖI k đơn vị phơi nhiễm (như run_stats_analysis)"
            )
            p.add_argument("--thang-do", action="append", help="thang đo cho RELIABILITY: «TÊN:mục1,mục2,…» (lặp được)")
            p.add_argument("--khong-hon-hop", action="store_true", help="không chạy mô hình hỗn hợp (GENLINMIXED)")
            p.add_argument("--khong-trong-so", action="store_true", help="không chạy Complex Samples có trọng số")
        if ten == "chay":
            p.add_argument("--thoi-han", type=int, default=1200, help="giây (mặc định 1200)")
            p.add_argument("--khong-r", action="store_true", help="không chạy R làm tham chiếu cho phân tích bổ sung")
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
