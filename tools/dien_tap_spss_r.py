#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dien_tap_spss_r.py — DIỄN TẬP khai báo biến ở SPSS và R TRƯỚC khi thu thập dữ liệu (mọi đề tài).

Vì sao (15/11/2026, bác sĩ: «hoàn thiện hệ thống nghiên cứu, không chỉ riêng 2 đề tài»): chuỗi khai báo biến
(từ điển G5 → kế hoạch biến → .sav nhãn/mức đo/mã thiếu/11 thuộc tính → .rds khuôn haven → đối chiếu khứ hồi) chỉ
chạy được khi đã có DỮ LIỆU (`cau_noi_spss.py xuat-sav` cần bộ đã khoá hoặc bản nháp). Đề tài thật ở G1–G4 chưa có dữ
liệu ⇒ khai báo sai (mức đo, nhãn, mã thiếu, ngày, khoảng hợp lệ…) chỉ lộ ra SAU khi đã nhập liệu. Công cụ này sinh
một bộ dữ liệu GIẢ từ chính từ điển G5 của đề tài (mỗi mã lựa chọn, mỗi mã thiếu đều xuất hiện), chép đề tài sang một
thư mục tạm NGOÀI repo, rồi chạy ĐÚNG cầu nối thật:
  ① SPSS: `xuat-sav` bản nháp — khứ hồi từng ô (E3) + từ điển .sav ↔ kế hoạch (E2) + 11 thuộc tính (E5);
  ② R: `xuat-rds` — .rds khuôn haven, đối chiếu ba chiều từ điển ↔ .sav ↔ .rds;
  ③ biến phái sinh (nếu `_bien-phai-sinh.csv` có công thức): tính thử bằng Python trên dữ liệu giả.
Không ghi gì vào exports/ của đề tài (trừ `--ghi` báo cáo `DIEN_TAP_SPSS_R_<mã>.md`, tệp RIÊNG của máy — không băm
vào biên bản nào). Dữ liệu giả KHÔNG BAO GIỜ là dữ liệu nghiên cứu: ở thư mục tạm, xoá khi xong.

Lệnh: python3 tools/dien_tap_spss_r.py --study <mã> [--so-ca 24] [--khong-spss] [--khong-r] [--json] [--ghi]
Mã thoát: 0 mọi chặng đo được đều ĐẠT · 1 có chặng LỆCH · 2 không đo được (thiếu từ điển G5 / SPSS / R) · 3 từ chối.
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import re
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bien_phai_sinh as BPS  # noqa: E402
import cau_noi_r as RN  # noqa: E402
import cau_noi_spss as SP  # noqa: E402
import nhap_lieu_excel as NL  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
CAN_KIEM = "Cần bác sĩ kiểm chứng."
DAT, LECH, KHONG_DO = "DAT", "LECH", "KHONG_DO_DUOC"
#: Tệp/thư mục KHÔNG chép sang vùng diễn tập (nặng, hoặc là sản phẩm của lượt trước).
_BO_QUA_CHEP = {".docx", ".pdf", ".xlsx", ".pptx", ".png", ".jpg", ".zip"}
_BO_QUA_THU_MUC = {"spss", "r", "_backup", "__pycache__"}


class TuChoi(RuntimeError):
    """Tham số sai."""


class KhongDoDuoc(RuntimeError):
    """Thiếu đầu vào để diễn tập — KHÔNG phải «đạt»."""


def _so_le(kiem_tra: str) -> int:
    m = re.search(r"(\d+)dp", kiem_tra or "")
    return int(m.group(1)) if m else 1


def _so(s: str, mac_dinh: float) -> float:
    try:
        return float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return mac_dinh


def _ngay(s: str, mac_dinh: date) -> date:
    try:
        return date.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return mac_dinh


def gia_tri_gia(c: "NL.Cot", i: int, so_ca: int) -> str:
    """Giá trị GIẢ hợp lệ cho cột `c` ở ca thứ i — mỗi mã lựa chọn đều xuất hiện; ca CUỐI mang mã thiếu (nếu cột có)."""
    if c.kieu == "id":
        return f"DT{i + 1:03d}"
    if i == so_ca - 1 and c.ma_thieu:
        return str(next(iter(c.ma_thieu)))
    if c.kieu == "ma":
        ma = list(c.lua_chon) or ["1"]
        return str(ma[i % len(ma)])
    if c.kieu == "hop":
        return "1" if (i + len(c.ten)) % 2 else "0"
    if c.kieu in ("so_nguyen", "so"):
        lo = _so(c.min, 0.0)
        hi = _so(c.max, lo + 100.0)
        if hi < lo:
            hi = lo
        if c.kieu == "so_nguyen":
            lo_i, hi_i = int(-(-lo // 1)), int(hi // 1)
            return str(lo_i + (i % (hi_i - lo_i + 1)) if hi_i >= lo_i else lo_i)
        dp = _so_le(c.kiem_tra)
        buoc = (hi - lo) / max(so_ca, 1)
        return f"{lo + buoc * (i % max(so_ca, 1)):.{dp}f}"
    if c.kieu in ("ngay", "ngay_gio"):
        lo = _ngay(c.min, date(2026, 1, 1))
        hi = _ngay(c.max, lo + timedelta(days=365))
        so_ngay = max((hi - lo).days, 0)
        ngay = lo + timedelta(days=(i * 7) % (so_ngay + 1))
        return ngay.isoformat() + (" 08:30" if c.kieu == "ngay_gio" else "")
    if c.kieu == "gio":
        return f"{8 + i % 10:02d}:30"
    if c.kieu == "van_ban":
        return f"ghi chu dien tap {i + 1}"
    return f"x{i + 1}"


def sinh_du_lieu_gia(td_p: Path, mt_p: Path | None, ra: Path, so_ca: int) -> dict:
    """Từ điển G5 ⇒ CSV dữ liệu giả (UTF-8, không xuống dòng trong ô). Trả {so_ca, so_cot, bo_qua}."""
    td = NL.doc_tu_dien_day_du(td_p)
    mt = SP.doc_ma_thieu(mt_p) if mt_p and mt_p.exists() else []
    cot, bo_qua = NL.ke_hoach_cot(td, mt)
    if not cot:
        raise KhongDoDuoc(f"{td_p.name} không có cột nhập liệu nào")
    with open(ra, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow([c.ten for c in cot])
        for i in range(so_ca):
            w.writerow([gia_tri_gia(c, i, so_ca) for c in cot])
    return {"so_ca": so_ca, "so_cot": len(cot), "bo_qua": bo_qua}


def chep_de_tai(goc: Path, dich: Path) -> None:
    """Chép thư mục đề tài sang vùng diễn tập (bỏ tệp nặng và sản phẩm spss/r cũ)."""
    def _bo(thu_muc: str, ten: list[str]) -> set[str]:
        return {t for t in ten if Path(t).suffix.lower() in _BO_QUA_CHEP or t in _BO_QUA_THU_MUC}
    shutil.copytree(goc, dich, ignore=_bo)


def _chay_ghi_lai(ham, args) -> tuple[int, str]:
    """Chạy một lệnh cầu nối, bắt stdout/stderr; ngoại lệ có chủ ý của cầu nối ⇒ mã tương ứng."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            ma = ham(args)
        except SP.KhongDoDuoc as e:  # cau_noi_r dùng CHÍNH lớp này (RN.KhongDoDuoc is SP.KhongDoDuoc)
            print(f"⚪ {e}")
            ma = 2
        except SP.TuChoi as e:
            print(f"✗ Từ chối: {e}")
            ma = 3
    return ma, buf.getvalue()


def _trang_thai(ma: int) -> str:
    return DAT if ma == 0 else (KHONG_DO if ma == 2 else LECH)


def dien_tap(study: str, *, so_ca: int = 24, spss: bool = True, r: bool = True,
             goc_exports: Path | None = None) -> dict:
    """Diễn tập trọn chuỗi trên bản sao tạm. Trả báo cáo {study, chang: [...], trang_thai, ...}."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", study or ""):
        raise TuChoi(f"mã đề tài không hợp lệ: {study!r}")
    if so_ca < 3:
        raise TuChoi("--so-ca phải ≥ 3 (cần đủ ca cho mọi mã lựa chọn và một ca mang mã thiếu)")
    goc = (goc_exports or BASE / "exports") / study
    if not goc.is_dir():
        raise TuChoi(f"không có thư mục đề tài {goc}")
    td_goc = goc / f"G5_REDCap_dictionary_{study}.csv"
    bc = {"study": study, "luc": datetime.now().astimezone().isoformat(timespec="seconds"), "so_ca_gia": so_ca,
          "chang": [], "disclaimer": CAN_KIEM}
    if not td_goc.exists():
        bc["chang"].append({"ten": "từ điển G5", "trang_thai": KHONG_DO,
                            "ghi": f"chưa có {td_goc.name} — chạy G5 (run_g5_auto) để dựng từ điển rồi diễn tập"})
        bc["trang_thai"] = KHONG_DO
        return bc
    luu = (SP.EXPORTS, BPS._study_dir)
    with tempfile.TemporaryDirectory(prefix="dien-tap-spss-r-") as tam_s:
        tam = Path(tam_s)
        ex = tam / "exports"
        ex.mkdir()
        d = ex / study
        chep_de_tai(goc, d)
        csv_p = tam / "du_lieu_gia.csv"
        gen = sinh_du_lieu_gia(d / td_goc.name, d / "_ma-thieu-theo-bien.csv", csv_p, so_ca)
        bc["chang"].append({"ten": "sinh dữ liệu giả từ từ điển G5", "trang_thai": DAT,
                            "ghi": f"{gen['so_ca']} ca × {gen['so_cot']} cột; không nhập tay: "
                                   + (", ".join(gen["bo_qua"]) or "—")})
        SP.EXPORTS = ex
        BPS._study_dir = lambda s: ex / s  # noqa: E731 — vùng tạm, không bao giờ exports thật
        try:
            khung = dict(study=study, data=str(csv_p), ban_nhap=True, dictionary=None, ma_thieu=None,
                         giu_ghi_chu=False)
            if spss:
                ma, out = _chay_ghi_lai(SP.lenh_xuat_sav, SimpleNamespace(**khung))
                bc["chang"].append({"ten": "SPSS .sav (E2 từ điển · E3 khứ hồi · E5 11 thuộc tính)",
                                    "trang_thai": _trang_thai(ma), "ma": ma, "nhat_ky": out[-4000:]})
            if r:
                ma, out = _chay_ghi_lai(RN.lenh_xuat_rds, SimpleNamespace(**khung, thoi_han=600))
                bc["chang"].append({"ten": "R .rds khuôn haven (đối chiếu ba chiều từ điển ↔ .sav ↔ .rds)",
                                    "trang_thai": _trang_thai(ma), "ma": ma, "nhat_ky": out[-4000:]})
            if (d / BPS.TEP_DAC_TA).exists():
                try:
                    bien = BPS.doc_dac_ta(d)
                    kq = BPS.kiem_dac_ta(bien, BPS.doc_danh_muc_tu_dien(d, study))
                    co_ct = [b.ten for b in bien if b.cong_thuc.strip() and not b.ngoai_tang]
                    loi = {k: v for k, v in kq.loi.items() if k in co_ct}
                    if loi:
                        bc["chang"].append({"ten": "biến phái sinh (công thức ↔ cột dữ liệu)", "trang_thai": LECH,
                                            "ghi": "; ".join(f"{k}: {v}" for k, v in list(loi.items())[:12])})
                    elif co_ct:
                        df = BPS._doc_csv_chu(csv_p)
                        BPS.tinh_df(df, kq, BPS.doc_danh_muc_tu_dien(d, study), co_ct)
                        bc["chang"].append({"ten": "biến phái sinh (tính thử trên dữ liệu giả)", "trang_thai": DAT,
                                            "ghi": f"{len(co_ct)} biến tính được: " + ", ".join(co_ct[:20])})
                except (BPS.LoiCongThuc, BPS.KhongDoDuoc, BPS.TuChoi) as e:
                    bc["chang"].append({"ten": "biến phái sinh", "trang_thai": LECH, "ghi": str(e)})
        finally:
            SP.EXPORTS, BPS._study_dir = luu
    tt = [c["trang_thai"] for c in bc["chang"]]
    bc["trang_thai"] = LECH if LECH in tt else (KHONG_DO if KHONG_DO in tt else DAT)
    return bc


def markdown(bc: dict) -> str:
    bieu = {DAT: "✅ ĐẠT", LECH: "🔴 LỆCH", KHONG_DO: "⚪ KHÔNG ĐO ĐƯỢC"}
    dong = [f"# Diễn tập SPSS/R trước thu thập — {bc['study']}", "",
            f"- Lúc: {bc['luc']} · dữ liệu GIẢ {bc['so_ca_gia']} ca sinh từ từ điển G5 (không phải dữ liệu nghiên cứu)",
            f"- Kết luận: **{bieu[bc['trang_thai']]}**", "", "| Chặng | Kết quả | Ghi chú |", "|---|---|---|"]
    for c in bc["chang"]:
        ghi = (c.get("ghi") or "").replace("|", "/").replace("\n", " ")
        if not ghi and c.get("nhat_ky"):
            dau = [x.strip() for x in c["nhat_ky"].splitlines() if x.strip().startswith(("✓", "🔴", "⚪", "✗", "⚠"))]
            ghi = " · ".join(dau[-4:]).replace("|", "/")
        dong.append(f"| {c['ten']} | {bieu[c['trang_thai']]} | {ghi[:400]} |")
    dong += ["", "Dữ liệu giả ở thư mục tạm ngoài repo, đã xoá. " + CAN_KIEM, ""]
    return "\n".join(dong)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Diễn tập khai báo biến ở SPSS/R trước thu thập. " + CAN_KIEM)
    ap.add_argument("--study", required=True)
    ap.add_argument("--so-ca", type=int, default=24)
    ap.add_argument("--khong-spss", action="store_true")
    ap.add_argument("--khong-r", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ghi", action="store_true", help="ghi exports/<mã>/DIEN_TAP_SPSS_R_<mã>.md (tệp riêng của máy)")
    a = ap.parse_args(argv)
    try:
        bc = dien_tap(a.study, so_ca=a.so_ca, spss=not a.khong_spss, r=not a.khong_r)
    except TuChoi as e:
        print(f"✗ Từ chối: {e}", file=sys.stderr)
        return 3
    except KhongDoDuoc as e:
        print(f"⚪ Không đo được: {e}", file=sys.stderr)
        return 2
    md = markdown(bc)
    print(json.dumps(bc, ensure_ascii=False, indent=1) if a.json else md)
    if a.ghi:
        p = BASE / "exports" / a.study / f"DIEN_TAP_SPSS_R_{a.study}.md"
        p.write_text(md, encoding="utf-8", newline="\n")
        print(f"✓ Đã ghi {p.relative_to(BASE).as_posix()}")
    return {DAT: 0, LECH: 1, KHONG_DO: 2}[bc["trang_thai"]]


if __name__ == "__main__":
    sys.exit(main())
