#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TẢI danh mục Retraction Watch (Crossref, CC0) về đĩa để tra NGOẠI TUYẾN.

Đây là nền của chuỗi 3 tầng kiểm rút bài (xem `app/sources/retraction_chain.py`).
Tải một lần rồi tra offline: không cần khoá API, không hạn mức, không IP nào chặn.

Dùng:
    python tools/tai_retraction_watch.py                # tải/làm mới (Crossref → gương GitLab)
    python tools/tai_retraction_watch.py --kiem         # chỉ xem bản trên đĩa còn tươi không
    python tools/tai_retraction_watch.py --email a@b.c  # Crossref Labs API bắt buộc email
    python tools/tai_retraction_watch.py --nguon gitlab # chỉ dùng gương GitLab của Crossref

NGUỒN (thêm 24/09/2026, kiểm nguồn chứng cứ trên phiên Cloud): môi trường Cloud mặc định
«Trusted» CHẶN `api.labs.crossref.org` (proxy trả 403 theo chính sách) và container không có
~/.ebm-secrets nên cũng không có email ⇒ tầng ① của chuỗi rút bài — tầng DUY NHẤT bắt được ca
rút-và-thay PMID 30267080 mà PubMed lẫn Europe PMC đều trả «ok» — chưa từng chạy trên Cloud.
Crossref phát hành CÙNG bộ dữ liệu (cùng tên cột, cập nhật mỗi ngày làm việc, CC0) ở kho
chính thức `gitlab.com/crossref/retraction-watch-data`, và gitlab.com nằm trong danh sách
«Trusted». Thứ tự mặc định: Crossref Labs API (nếu có email) → gương GitLab. Cả hai đi qua
CÙNG một cổng kiểm schema + số dòng tối thiểu trước khi thay bản cũ.

Mã thoát: 0 = có bản dùng được · 1 = bản trên đĩa quá hạn · 2 = không tải được.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.sources.retraction_watch import (  # noqa: E402
    CSV_MAC_DINH,
    ENDPOINT,
    META_MAC_DINH,
    THU_MUC,
    RetractionWatchIndex,
)

# Hạn dùng 30 ngày — khớp tầng "rút bài" của `tools/so_xac_minh_nguon.py`. Cố ý
# KHÁC tầng "tồn tại + metadata" 180 ngày: một bài đang tốt hôm nay có thể bị rút
# ngày mai, nên danh mục rút bài phải làm mới thường xuyên hơn nhiều.
HAN_NGAY = 30

# Cột bắt buộc phải có thì file mới dùng được. Kiểm TRƯỚC khi thay bản cũ để một
# lần Crossref đổi schema (hoặc trả trang lỗi) không âm thầm xoá mất nền đang chạy.
COT_BAT_BUOC = {"OriginalPaperPubMedID", "RetractionPubMedID", "RetractionNature"}

# Gương CHÍNH THỨC của Crossref (README kho: «In September 2023, Crossref acquired the Retraction
# Watch database … and have made it publicly available»). Hai đường cùng một tệp: `raw` (ưu tiên)
# và REST API v4 của GitLab (dự phòng khi `raw` bị chuyển hướng sang host khác). Không cần email.
GUONG_GITLAB = (
    "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv",
    "https://gitlab.com/api/v4/projects/crossref%2Fretraction-watch-data/repository/files/"
    "retraction_watch.csv/raw?ref=main",
)


def _ssl_context() -> ssl.SSLContext:
    """Python 3.14 cài tay trên Mac này thiếu CA hệ thống → urllib gãy im lặng."""
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _email() -> str:
    for ten in ("OPENALEX_EMAIL", "NCBI_EMAIL", "UNPAYWALL_EMAIL"):
        if os.getenv(ten):
            return os.environ[ten]
    kho = Path.home() / ".ebm-secrets" / "medical-ebm-automation.env"
    if kho.exists():
        for dong in kho.read_text(encoding="utf-8", errors="replace").splitlines():
            for ten in ("OPENALEX_EMAIL", "NCBI_EMAIL", "UNPAYWALL_EMAIL"):
                if dong.startswith(ten + "="):
                    gt = dong.split("=", 1)[1].strip()
                    if gt:
                        return gt
    return ""


def in_trang_thai(idx: RetractionWatchIndex) -> int:
    if not idx.san_sang():
        print("🔴 CHƯA có bản Retraction Watch nào trên đĩa.")
        print("   Chạy: python tools/tai_retraction_watch.py")
        return 2
    tuoi = idx.tuoi_ngay()
    so = idx.so_ban_ghi()
    if tuoi is None:
        print(f"🟡 Có CSV ({so} PMID) nhưng KHÔNG biết tải về lúc nào — nên tải lại.")
        return 1
    if tuoi > HAN_NGAY:
        print(f"🟡 Bản trên đĩa {tuoi:.0f} ngày tuổi (hạn {HAN_NGAY}) — QUÁ HẠN, tải lại.")
        print(f"   {so} PMID có phán quyết. Vẫn dùng được nhưng có thể bỏ sót bài mới bị rút.")
        return 1
    print(f"🟢 Bản trên đĩa còn tươi: {tuoi:.1f} ngày tuổi, {so} PMID có phán quyết.")
    return 0


def _tai_ve(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "EBM-Copilot/tai_retraction_watch"})
    with urllib.request.urlopen(req, timeout=180, context=_ssl_context()) as resp:
        return resp.read()


def _kiem_va_ghi(raw: bytes, nguon: str) -> int:
    """Kiểm schema + số dòng rồi ghi NGUYÊN TỬ. 0 = đã thay bản mới · 2 = giữ nguyên bản cũ."""
    van_ban = raw.decode("utf-8", errors="replace")
    try:
        csv.field_size_limit(sys.maxsize)
    except (OverflowError, ValueError):  # pragma: no cover
        csv.field_size_limit(2 ** 31 - 1)
    doc = csv.DictReader(io.StringIO(van_ban))
    cot = set(doc.fieldnames or [])
    thieu = COT_BAT_BUOC - cot
    if thieu:
        print(f"🔴 Phản hồi KHÔNG đúng schema, thiếu cột: {sorted(thieu)}")
        print("   GIỮ NGUYÊN bản cũ trên đĩa — không thay bằng thứ chưa kiểm được.")
        return 2
    so_dong = sum(1 for _ in doc)
    if so_dong < 1000:
        print(f"🔴 Chỉ {so_dong} dòng — nghi tải thiếu/bị cắt. GIỮ NGUYÊN bản cũ.")
        return 2

    # Ghi NGUYÊN TỬ: ghi ra file tạm rồi mới đổi tên. Ghi thẳng đè sẽ để lại một
    # CSV cụt nếu mạng đứt giữa chừng, mà CSV cụt thì "không thấy PMID" — im lặng
    # biến một bài đã bị rút thành không có phán quyết.
    THU_MUC.mkdir(parents=True, exist_ok=True)
    tam = CSV_MAC_DINH.with_suffix(".csv.tmp")
    tam.write_text(van_ban, encoding="utf-8", newline="\n")
    tam.replace(CSV_MAC_DINH)
    META_MAC_DINH.write_text(json.dumps({
        "tai_ve_luc": datetime.now(timezone.utc).isoformat(),
        "nguon": nguon,
        "giay_phep": "CC0 — Retraction Watch / Crossref",
        "so_dong": so_dong,
    }, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    idx = RetractionWatchIndex()
    print(f"✅ Đã tải {so_dong} dòng → {CSV_MAC_DINH.relative_to(REPO)}")
    print(f"   {idx.so_ban_ghi()} PMID có phán quyết (rút bài / expression of concern).")
    print("   Từ giờ tra hoàn toàn NGOẠI TUYẾN, không cần khoá và không hạn mức.")
    return 0


def tai(email: str, nguon: str = "tu-dong") -> int:
    """Tải theo thứ tự nguồn; nguồn đầu tiên cho bản HỢP LỆ thắng, nguồn lỗi thì thử nguồn kế.

    `nguon`: "tu-dong" (Crossref Labs API nếu có email → gương GitLab) · "crossref" · "gitlab".
    Meta ghi URL KHÔNG kèm email (email chỉ là tham số lịch sự gửi Crossref)."""
    ung_vien: list[tuple[str, str, str]] = []  # (url gọi, url ghi meta, mô tả)
    if nguon in ("tu-dong", "crossref"):
        if email:
            ung_vien.append((f"{ENDPOINT}?{urllib.parse.quote(email)}", ENDPOINT,
                             f"Crossref Labs API (gửi email {email} — đúng hợp đồng API của họ)"))
        elif nguon == "crossref":
            print("🔴 Crossref Labs API bắt buộc email. Dùng --email <địa chỉ> hoặc --nguon gitlab.")
            return 2
        else:
            print("ℹ Không có email cho Crossref Labs API — dùng gương GitLab chính thức của Crossref.")
    if nguon in ("tu-dong", "gitlab"):
        ung_vien += [(u, u, "gương GitLab chính thức của Crossref") for u in GUONG_GITLAB]

    for url, url_meta, mo_ta in ung_vien:
        print(f"Tải Retraction Watch từ {mo_ta}…")
        try:
            raw = _tai_ve(url)
        except ssl.SSLCertVerificationError:
            print("🔴 Thiếu chứng chỉ CA. Chạy lại bằng venv EBM:")
            print("   ~/.ebm-venv/bin/python tools/tai_retraction_watch.py")
            return 2
        except Exception as exc:  # noqa: BLE001 — lỗi một nguồn không được chặn nguồn kế tiếp
            print(f"   ✗ Không tải được: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        if _kiem_va_ghi(raw, url_meta) == 0:
            return 0
    print("🔴 Không nguồn nào cho bản hợp lệ — GIỮ NGUYÊN bản cũ trên đĩa (nếu có).")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--kiem", action="store_true", help="chỉ xem trạng thái bản trên đĩa")
    ap.add_argument("--email", default="", help="email gửi Crossref (bắt buộc theo API của họ)")
    ap.add_argument("--nguon", choices=("tu-dong", "crossref", "gitlab"), default="tu-dong",
                    help="tu-dong = Crossref Labs API (nếu có email) rồi gương GitLab của Crossref")
    args = ap.parse_args()

    idx = RetractionWatchIndex()
    if args.kiem:
        return in_trang_thai(idx)

    return tai(args.email or _email(), args.nguon)


if __name__ == "__main__":
    sys.exit(main())
