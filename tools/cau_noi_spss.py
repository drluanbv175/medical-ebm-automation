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


def chay_spss(py: Path, doi_so: list[str], *, thu_muc: Path, thoi_han: int = 1200) -> tuple[int, str, str]:
    """Chạy trình nền bằng Python của SPSS. Trả (mã, stdout, stderr). Không nuốt timeout: báo mã 1 kèm lý do.

    Đầu ra ghi vào TỆP tạm, KHÔNG qua ống dẫn (pipe): đo 14/11/2026, khi SPSS gặp lỗi nghiêm trọng một tiến trình con
    của nó vẫn giữ ống stdout nên `subprocess.run(capture_output=True)` chờ tới hết thời hạn (20 phút) dù trình nền đã
    dừng. Chỉ chờ
    CHÍNH trình nền; hết hạn ⇒ dừng cả nhóm tiến trình."""
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")}
    nhom = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    with tempfile.TemporaryDirectory(prefix="ebm-spss-log-") as tam:
        p_out, p_err = Path(tam) / "out.txt", Path(tam) / "err.txt"
        with open(p_out, "wb") as f_out, open(p_err, "wb") as f_err:
            try:
                p = subprocess.Popen(
                    [str(py), "-I", str(TRINH_CHAY), *doi_so],
                    stdout=f_out,
                    stderr=f_err,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    cwd=str(thu_muc),
                    **nhom,
                )
            except OSError as e:
                return 1, "", f"LOI_SPSS không chạy được Python của SPSS: {e}"
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
        return 1, out, err + f"\nLOI_SPSS quá thời hạn {thoi_han} giây"
    return ma, out, err


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
        "bien": [{k: b[k] for k in ("cot", "ten", "so", "muc_do", "nhan", "muc", "ma_chu")} for b in ke if not b["bo"]],
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
    with vung_tam() as tam_s:
        tam = Path(tam_s)
        shutil.copyfile(csv_p, tam / "du_lieu.csv")
        (tam / "nhan_bien.sps").write_text(
            cu_phap_nhan_bien(tam / "du_lieu.csv", tam / "ra.sav", ke, ghi_chu=ghi_chu), encoding="utf-8", newline="\n"
        )
        ma, out, err = chay_spss(py, ["--cu-phap", str(tam / "nhan_bien.sps")], thu_muc=tam)
        if ma == 0 and (tam / "ra.sav").exists():
            shutil.move(str(tam / "ra.sav"), sav_p)
    (ra / f"{sps_p.stem}.log").write_text(
        out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n"
    )
    so_ca = _gia_tri_dong(out, "SO_CA")
    if ma != 0 or not sav_p.exists():
        print("🔴 SPSS báo lỗi khi tạo .sav —", (err or out).strip()[-800:])
        return MA_LECH
    if so_ca is not None and so_ca != str(n):
        print(f"🔴 Số ca trong .sav ({so_ca}) khác số dòng CSV ({n}) — không dùng tệp này")
        sav_p.unlink()
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
    print(f"✓ {sav_p} — {so_ca} ca · {len(ket['bien'])} biến (chỉ đọc) · manifest {man_sav.name}")
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
    # OR theo MỖI k đơn vị phơi nhiễm (C1a: mỗi 15 phút chờ) — thiếu thì SPSS tính theo mỗi phút ⇒ «lệch» giả
    dv = getattr(args, "don_vi_phoi_nhiem", None)
    if dv is None:
        dv = tom.get("don_vi_phoi_nhiem")
    if dv is None:
        dv = ((tom_day_du.get("ordinal") or {}).get("don_vi_phoi_nhiem") or {}).get("don_vi")
    if dv is not None and (not isinstance(dv, (int, float)) or dv <= 0):
        raise TuChoi(f"đơn vị phơi nhiễm phải > 0 (đang là {dv!r})")
    dt["don_vi_phoi_nhiem"] = dv
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
    cov = [ten(c) for c in dt["covariates"]]
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
    # Kết cục chính
    if y and g:
        if loai in ("binary", "continuous"):
            if len(muc_g or []) != 2:
                raise TuChoi(f"biến nhóm {g} cần đúng 2 mức (đang có {len(muc_g) if muc_g else '>20'})")
            if loai == "binary":
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
        else:
            raise TuChoi(f"outcome_type không hỗ trợ: {loai}")
        if cum:
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
    dt = dac_ta(args)
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
    sps = d / "spss" / f"{args.study}_phan_tich.sps"
    sps.write_text(vb, encoding="utf-8", newline="\n")
    (kq / "dac_ta.json").write_text(json.dumps(dt, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    _xoa_ket_qua_cu(d, args.gate)
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
        buoc = re.match(r"step\s*(\d+)", hang[0], re.I)
        if len(hang) > 1 and buoc and buoc.group(1) != "1":  # chỉ bảng LOGISTIC nhiều bước (Step 0/1…)
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
    return ra


def lenh_chay(args) -> int:
    d = thu_muc_de_tai(args.study)
    sps = d / "spss" / f"{args.study}_phan_tich.sps"
    kq = d / "spss" / "ket_qua"
    if not sps.exists() or not (kq / "dac_ta.json").exists():
        raise KhongDoDuoc(f"chưa có {sps.name} — chạy `cau_noi_spss.py cu-phap --study {args.study}` trước")
    _xoa_ket_qua_cu(d, args.gate)  # lượt hỏng không được để lại kết quả của lượt trước cho doi-chieu đọc nhầm
    man = _doc_manifest_sav(args.study)
    dt = _doc_json(kq / "dac_ta.json")
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
    py = tim_spss()
    for cu in [*kq.glob("oms_*.xml"), kq / f"{args.study}_phan_tich.spv"]:
        if cu.exists():
            cu.unlink()
    with vung_tam() as tam_s:
        tam = Path(tam_s)
        (tam / "kq").mkdir()
        shutil.copyfile(sav, tam / "vao.sav")
        vb, _, _ = cu_phap_phan_tich(
            args.study, man, dt, tam / "kq", sav=tam / "vao.sav", bien_bang1=dt.get("vars_bang1")
        )
        (tam / "phan_tich.sps").write_text(vb, encoding="utf-8", newline="\n")
        ma, out, err = chay_spss(py, ["--cu-phap", str(tam / "phan_tich.sps")], thu_muc=tam, thoi_han=args.thoi_han)
        for f in (tam / "kq").iterdir():
            shutil.move(str(f), kq / f.name)
    (kq / f"{args.study}_phan_tich.log").write_text(
        out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8", newline="\n"
    )
    if ma != 0:
        print("🔴 SPSS báo lỗi —", (err or out).strip()[-800:], f"\n   nhật ký: {kq / (args.study + '_phan_tich.log')}")
        return MA_LECH
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
    for k in ("outcome", "group", "time", "event", "cot_cum"):
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
    man = _doc_manifest_sav(args.study)
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
