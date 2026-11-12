#!/usr/bin/env python3
"""Xếp ngẫu nhiên khung mẫu và chọn hồ sơ trích lại — đề tài btm-dtd2-ngoai-tru-BVQY175 (SOP-TR-01).

Hai lệnh:

  xep       Đọc danh sách khung mẫu xuất từ eHospital (CSV hoặc XLSX), gộp các dòng trùng của cùng một người
            theo cột mã người bệnh, rồi xếp thứ tự ngẫu nhiên theo hạt giống đã ghi vào sổ khung mẫu.
            Đầu ra là BẢNG NỐI MÃ (có mã người bệnh) ⇒ chỉ được ghi ra thư mục mã hoá NGOÀI OneDrive.
  trich-lai Chọn ngẫu nhiên các bản ghi cho người thứ hai trích lại, từ tệp xuất REDCap (chỉ cần cột record_id và
            du_tieu_chuan). Đầu ra chỉ có mã nghiên cứu, không có mã người bệnh.

Cách xếp: thứ tự = sắp theo SHA-256(«hạt giống|mã»). Cùng hạt giống và cùng danh sách thì ra đúng cùng thứ tự trên
mọi máy (Mac, Windows) và mọi phiên bản Python — người kiểm tra chạy lại là tái lập được.
Công cụ in ra «dấu thứ tự» (SHA-256 của danh sách đã xếp) để ghi vào sổ khung mẫu mà không lộ mã người bệnh.

Chỉ dùng thư viện chuẩn của Python (đọc XLSX cần openpyxl). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Thư mục đồng bộ đám mây: bảng nối mã (có mã người bệnh) không được nằm ở đây (sổ rủi ro R6).
_DAU_HIEU_DONG_BO = ("onedrive", "cloudstorage", "dropbox", "google drive", "googledrive", "icloud")


def _nam_trong_thu_muc_dong_bo(p: Path) -> bool:
    """Đường dẫn có nằm trong một thư mục đồng bộ đám mây không (so khớp không phân biệt hoa thường)."""
    chuoi = str(p.resolve()).lower()
    return any(d in chuoi for d in _DAU_HIEU_DONG_BO)


def _doc_bang(duong: Path) -> tuple[list[str], list[dict]]:
    """Đọc CSV (UTF-8 có/không BOM, hoặc UTF-16 như Excel Windows hay xuất) hoặc XLSX; trả (tiêu đề, các dòng)."""
    if duong.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise SystemExit("❌ Đọc XLSX cần thư viện openpyxl. Hoặc lưu tệp thành «CSV UTF-8» rồi chạy lại.")
        ws = load_workbook(duong, read_only=True, data_only=True).active
        hang = [[("" if v is None else str(v)).strip() for v in r] for r in ws.iter_rows(values_only=True)]
        hang = [r for r in hang if any(r)]
        if not hang:
            raise SystemExit("❌ Tệp không có dòng nào.")
        tieu_de = hang[0]
        return tieu_de, [dict(zip(tieu_de, r)) for r in hang[1:]]
    for ma_hoa in ("utf-8-sig", "utf-16"):
        try:
            with duong.open(encoding=ma_hoa, newline="") as f:
                doc = csv.DictReader(f)
                dong = list(doc)
                return [c.strip() for c in (doc.fieldnames or [])], dong
        except (UnicodeError, UnicodeDecodeError):
            continue
    raise SystemExit("❌ Không đọc được bảng mã của tệp. Mở bằng Excel, lưu thành «CSV UTF-8» rồi chạy lại.")


def _khoa(hat_giong: str, ma: str) -> str:
    return hashlib.sha256(f"{hat_giong}|{ma}".encode("utf-8")).hexdigest()


def _dau_thu_tu(ds: list[str]) -> str:
    return hashlib.sha256("\n".join(ds).encode("utf-8")).hexdigest()


def lenh_xep(a: argparse.Namespace) -> int:
    nguon, ra = Path(a.khung), Path(a.ra)
    if _nam_trong_thu_muc_dong_bo(ra) and not a.cho_phep_thu_muc_dong_bo:
        print("❌ Tệp ra là BẢNG NỐI MÃ (có mã người bệnh) — không ghi vào thư mục đồng bộ đám mây "
              f"({ra}). Chọn thư mục mã hoá trên máy (sổ rủi ro R6).")
        return 2
    if ra.exists():
        print(f"❌ {ra} đã có — không ghi đè bảng nối mã. Đổi tên tệp ra nếu thật sự cần xếp lại.")
        return 2
    tieu_de, dong = _doc_bang(nguon)
    if a.cot_ma not in tieu_de:
        print(f"❌ Không có cột «{a.cot_ma}». Các cột có trong tệp: {', '.join(tieu_de)}")
        return 2
    ma_rong = sum(1 for r in dong if not (r.get(a.cot_ma) or "").strip())
    dem: dict[str, int] = {}
    for r in dong:
        ma = (r.get(a.cot_ma) or "").strip()
        if ma:
            dem[ma] = dem.get(ma, 0) + 1
    ds = sorted(dem, key=lambda m: (_khoa(a.hat_giong, m), m))
    ra.parent.mkdir(parents=True, exist_ok=True)
    with ra.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["thu_tu_ngau_nhien", "ma_nguoi_benh", "so_dong_trong_danh_sach", "ma_nghien_cuu", "ngay_mo",
                    "ket_qua_sang_loc"])
        for i, ma in enumerate(ds, start=1):
            w.writerow([i, ma, dem[ma], "", "", ""])
    print("ĐÃ XẾP KHUNG MẪU — ghi các dòng dưới vào Sổ khung mẫu (không có mã người bệnh):")
    print(f"  Số dòng đọc được trong danh sách eHospital : {len(dong)}")
    print(f"  Dòng không có mã người bệnh (bỏ qua)       : {ma_rong}")
    print(f"  Số người sau khi gộp dòng trùng           : {len(ds)}")
    print(f"  Số người có nhiều hơn một dòng (đã gộp)   : {sum(1 for v in dem.values() if v > 1)}")
    print(f"  Hạt giống                                  : {a.hat_giong}")
    print(f"  Dấu thứ tự (SHA-256)                       : {_dau_thu_tu(ds)}")
    print(f"  Bảng nối mã đã ghi                         : {ra}")
    return 0


def lenh_trich_lai(a: argparse.Namespace) -> int:
    _, dong = _doc_bang(Path(a.ds))
    du = [(r.get("record_id") or "").strip() for r in dong
          if (r.get("du_tieu_chuan") or "").strip() in ("1", "1.0") and (r.get("record_id") or "").strip()]
    loai = set()
    if a.loai_tru:
        loai = {(r.get("record_id") or "").strip() for r in _doc_bang(Path(a.loai_tru))[1]}
    ung_vien = sorted(set(du) - loai)
    so = a.so if a.so is not None else math.ceil(a.ty_le * len(du))
    if so > len(ung_vien):
        print(f"❌ Cần {so} bản ghi nhưng chỉ còn {len(ung_vien)} bản ghi đủ tiêu chuẩn chưa được chọn.")
        return 2
    chon = sorted(ung_vien, key=lambda m: (_khoa(a.hat_giong, m), m))[:so]
    print(f"Bản ghi đủ tiêu chuẩn: {len(du)} · đã chọn ở đợt trước (loại trừ): {len(loai)} · chọn lần này: {so}")
    print(f"Hạt giống: {a.hat_giong} · dấu danh sách chọn (SHA-256): {_dau_thu_tu(chon)}")
    if a.ra:
        with Path(a.ra).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["record_id"])
            w.writerows([[m] for m in chon])
        print(f"Đã ghi danh sách mã nghiên cứu: {a.ra}")
    else:
        print("Danh sách mã nghiên cứu:", ", ".join(chon))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Xếp ngẫu nhiên khung mẫu và chọn hồ sơ trích lại (SOP-TR-01)")
    sub = p.add_subparsers(dest="lenh", required=True)
    x = sub.add_parser("xep", help="Xếp ngẫu nhiên danh sách khung mẫu xuất từ eHospital")
    x.add_argument("--khung", required=True, help="Tệp danh sách khung mẫu (.csv hoặc .xlsx)")
    x.add_argument("--cot-ma", required=True, help="Tên cột chứa mã người bệnh trong tệp")
    x.add_argument("--hat-giong", required=True, help="Hạt giống đã ghi vào sổ khung mẫu TRƯỚC khi chạy")
    x.add_argument("--ra", required=True, help="Tệp bảng nối mã (.csv) — thư mục mã hoá ngoài OneDrive")
    x.add_argument("--cho-phep-thu-muc-dong-bo", action="store_true", help=argparse.SUPPRESS)
    t = sub.add_parser("trich-lai", help="Chọn ngẫu nhiên bản ghi cho người thứ hai trích lại")
    t.add_argument("--ds", required=True, help="Tệp xuất REDCap có cột record_id và du_tieu_chuan")
    t.add_argument("--hat-giong", required=True, help="Hạt giống thứ hai, ghi vào sổ khung mẫu trước khi chạy")
    nhom = t.add_mutually_exclusive_group(required=True)
    nhom.add_argument("--so", type=int, help="Số bản ghi cần chọn")
    nhom.add_argument("--ty-le", type=float, help="Tỷ lệ cần chọn trên số bản ghi đủ tiêu chuẩn (vd 0.1)")
    t.add_argument("--loai-tru", help="Tệp record_id đã chọn ở đợt trước (không chọn lại)")
    t.add_argument("--ra", help="Tệp ghi danh sách record_id được chọn")
    a = p.parse_args(argv)
    return lenh_xep(a) if a.lenh == "xep" else lenh_trich_lai(a)


if __name__ == "__main__":
    sys.exit(main())
