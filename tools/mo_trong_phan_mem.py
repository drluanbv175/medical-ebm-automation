#!/usr/bin/env python3
"""Mở dữ liệu đề tài THẲNG trong SPSS hoặc RStudio trên máy — một lệnh, như kết nối EndNote (14/11/2026).

Bác sĩ hỏi «sao không nhập liệu luôn vào SPSS và R trên máy của tôi như cách kết nối EndNote». Công cụ này nối đủ chuỗi
rồi mở cửa sổ phần mềm cho bác sĩ:

  spss  --study <mã> [--excel <tệp.xlsx|.sav>]   ⇒ xuất .sav (khứ hồi từng ô + so từ điển) rồi mở trong SPSS
  r     --study <mã> [--excel <tệp.xlsx|.sav>]   ⇒ xuất .rds có nhãn (ba chiều) rồi mở RStudio với tệp nạp sẵn dữ liệu

Nguồn dữ liệu (một bản gốc duy nhất — không gõ riêng vào SPSS và R, tránh hai bản gốc lệch nhau):
  · Dữ liệu ĐÃ KHOÁ (DATA_LOCK_manifest) có ⇒ LUÔN dùng bản khoá (bỏ qua --excel, có báo).
  · Chưa khoá ⇒ cần --excel: chạy `nhap_lieu_excel.py nhap` (CHỈ khi SẠCH mới đi tiếp), rồi xuất BẢN NHÁP (--ban-nhap).
Mọi bước gọi đúng công cụ chuẩn bằng tiến trình con (sys.executable) — không có đường tắt bỏ qua kiểm tra nào.

Mã thoát: 0 mở được · 1 bước trước báo lỗi/truy vấn (in lý do) · 2 không đo được (chưa khoá mà thiếu --excel; máy
không có SPSS/R/RStudio) · 3 từ chối. Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import cau_noi_spss as SP  # noqa: E402

MA_OK, MA_LOI, MA_KHONG_DO, MA_TU_CHOI = 0, 1, 2, 3
CAN_KIEM = "Cần bác sĩ kiểm chứng."
APP_SPSS = "IBM SPSS Statistics"
APP_RSTUDIO = "RStudio"


def chay(lenh: list[str]) -> int:
    """Chạy một công cụ chuẩn, đầu ra chảy thẳng ra màn hình (bác sĩ thấy đủ báo cáo của từng bước)."""
    print("→ " + " ".join(Path(x).name if i == 1 else x for i, x in enumerate(lenh)), flush=True)
    return subprocess.run(lenh, check=False).returncode


def mo_ung_dung(app: str, tep: Path) -> bool:
    """Mở tệp bằng ứng dụng trên máy. macOS: `open -a`; Windows: ứng dụng mặc định của đuôi tệp; khác: xdg-open."""
    he = platform.system()
    try:
        if he == "Darwin":
            return subprocess.run(["open", "-a", app, str(tep)], check=False).returncode == 0
        if he == "Windows":
            os.startfile(str(tep))  # type: ignore[attr-defined]  # noqa: S606 — chỉ có trên Windows
            return True
        return subprocess.run(["xdg-open", str(tep)], check=False).returncode == 0
    except OSError:
        return False


def co_du_lieu_khoa(study: str) -> bool:
    try:
        SP.tim_du_lieu_khoa(study)
        return True
    except (SP.KhongDoDuoc, SP.TuChoi):
        return False


def chuan_bi_csv(study: str, tep: Path, ra: Path | None) -> Path | None:
    """Tệp nhập liệu (Excel hoặc .sav nhập thẳng trong SPSS) ⇒ CSV qua `nhap_lieu_excel.py nhap`; None nếu chưa sạch."""
    lenh = [sys.executable, str(TOOLS / "nhap_lieu_excel.py"), "nhap", "--study", study, "--excel", str(tep)]
    thu_muc = ra if ra else tep.parent / f"{tep.stem}_csv"
    lenh += ["--ra", str(thu_muc)]
    ma = chay(lenh)
    csv_p = thu_muc / f"{tep.stem}.csv"
    if ma != 0 or not csv_p.exists():
        print(
            "⛔ Dữ liệu nhập CHƯA SẠCH (lỗi/truy vấn/chưa đủ kiểm — xem báo cáo trên): sửa trong tệp nhập theo phiếu"
            " gốc rồi bấm lại. Không mở bản có lỗi trong SPSS/R."
        )
        return None
    return csv_p


def kich_ban_rstudio(rds: Path, study: str, ban_nhap: bool) -> Path:
    """Tệp .R nhỏ (KHÔNG chứa dữ liệu — chỉ đường dẫn) để RStudio mở: Source là nạp `d` có nhãn và hiện bảng dữ liệu."""
    p = rds.with_name(f"mo_trong_rstudio_{study}{'_ban-nhap' if ban_nhap else ''}.R")
    duong_dan = rds.as_posix().replace("\\", "/").replace('"', '\\"')
    p.write_text(
        "\n".join(
            [
                f"# Dữ liệu đề tài {study}{' — BẢN NHÁP (chưa khoá)' if ban_nhap else ' — bản ĐÃ KHOÁ'} · sinh bởi "
                "tools/mo_trong_phan_mem.py",
                "# Bấm «Source» (⇧⌘S) để nạp. Nhãn biến/nhãn giá trị theo khuôn haven: as_factor(), zap_missing().",
                f'd <- readRDS("{duong_dan}")',
                'if (requireNamespace("haven", quietly = TRUE)) library(haven)',
                'cat(nrow(d), "ca ·", ncol(d), "biến\\n")',
                "View(d)",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    return p


def lenh_mo(args, phan_mem: str) -> int:
    study = args.study
    d = SP.thu_muc_de_tai(study)
    if not d.exists():
        raise SP.TuChoi(f"không có thư mục đề tài: {d}")
    khoa = co_du_lieu_khoa(study)
    cong_cu = TOOLS / ("cau_noi_spss.py" if phan_mem == "spss" else "cau_noi_r.py")
    lenh_xuat = [sys.executable, str(cong_cu), "xuat-sav" if phan_mem == "spss" else "xuat-rds", "--study", study]
    if khoa:
        if args.excel:
            print("ℹ️ Đề tài ĐÃ KHOÁ dữ liệu — mở bản khoá, bỏ qua --excel (bản khoá là bản gốc duy nhất).")
        ban_nhap = False
    else:
        if not args.excel:
            print(
                "⚪ Chưa khoá dữ liệu — truyền --excel <tệp đã nhập (.xlsx hoặc .sav nhập trong SPSS)> để mở BẢN NHÁP."
            )
            return MA_KHONG_DO
        tep = Path(args.excel).expanduser().resolve()
        csv_p = chuan_bi_csv(study, tep, Path(args.ra).expanduser().resolve() if args.ra else None)
        if csv_p is None:
            return MA_LOI
        lenh_xuat += ["--data", str(csv_p), "--ban-nhap"]
        ban_nhap = True
    ma = chay(lenh_xuat)
    if ma != 0:
        print("⛔ Bước xuất báo lỗi (xem trên) — KHÔNG mở tệp có thể sai. " + CAN_KIEM)
        return ma
    hau = "_BAN-NHAP" if ban_nhap else "_khoa"
    tep_ra = d / ("spss" if phan_mem == "spss" else "r") / f"{study}{hau}.{'sav' if phan_mem == 'spss' else 'rds'}"
    if not tep_ra.exists():
        print(f"⛔ Không thấy tệp xuất {tep_ra.name}")
        return MA_LOI
    nhan = "BẢN NHÁP (chưa khoá)" if ban_nhap else "bản ĐÃ KHOÁ"
    if phan_mem == "spss":
        dich, app = tep_ra, APP_SPSS
    else:
        dich, app = kich_ban_rstudio(tep_ra, study, ban_nhap), APP_RSTUDIO
    if args.khong_mo:
        print(f"✓ Sẵn sàng ({nhan}): {dich}")
        return MA_OK
    if not mo_ung_dung(app, dich):
        print(f"⚪ Không mở được {app} trên máy — mở tay tệp: {dich}")
        return MA_KHONG_DO
    goi_y = "" if phan_mem == "spss" else " — bấm «Source» trong RStudio để nạp dữ liệu và hiện bảng"
    print(f"✓ Đã mở trong {app} ({nhan}): {dich.name}{goi_y}. {CAN_KIEM}")
    return MA_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mở dữ liệu đề tài thẳng trong SPSS hoặc RStudio. " + CAN_KIEM)
    sub = ap.add_subparsers(dest="phan_mem", required=True)
    for ten, giup in (("spss", "xuất .sav (kiểm từng ô) rồi mở trong SPSS"), ("r", "xuất .rds rồi mở RStudio")):
        p = sub.add_parser(ten, help=giup)
        p.add_argument("--study", required=True)
        p.add_argument("--excel", help="tệp đã nhập (.xlsx hoặc .sav nhập trong SPSS) — dùng khi CHƯA khoá dữ liệu")
        p.add_argument("--ra", help="thư mục CSV trung gian (NGOÀI repo; mặc định cạnh tệp nhập)")
        p.add_argument("--khong-mo", action="store_true", help="chỉ chuẩn bị tệp, không mở phần mềm")
    args = ap.parse_args(argv)
    try:
        return lenh_mo(args, args.phan_mem)
    except SP.TuChoi as e:
        print(f"⛔ {e}")
        return MA_TU_CHOI
    except SP.KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
