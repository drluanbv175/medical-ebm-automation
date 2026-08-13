#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TẢI danh mục Retraction Watch (Crossref, CC0) về đĩa để tra NGOẠI TUYẾN.

Đây là nền của chuỗi 3 tầng kiểm rút bài (xem `app/sources/retraction_chain.py`).
Tải một lần rồi tra offline: không cần khoá API, không hạn mức, không IP nào chặn.

Dùng:
    python tools/tai_retraction_watch.py                # tải/làm mới
    python tools/tai_retraction_watch.py --kiem         # chỉ xem bản trên đĩa còn tươi không
    python tools/tai_retraction_watch.py --email a@b.c  # Crossref bắt buộc email

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


def tai(email: str) -> int:
    url = f"{ENDPOINT}?{urllib.parse.quote(email)}"
    print(f"Tải Retraction Watch từ Crossref (gửi email {email} — đúng hợp đồng API của họ)…")
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "EBM-Copilot/tai_retraction_watch"})
        with urllib.request.urlopen(req, timeout=180, context=_ssl_context()) as resp:
            raw = resp.read()
    except ssl.SSLCertVerificationError:
        print("🔴 Thiếu chứng chỉ CA. Chạy lại bằng venv EBM:")
        print("   ~/.ebm-venv/bin/python tools/tai_retraction_watch.py")
        return 2
    except Exception as exc:
        print(f"🔴 Không tải được: {type(exc).__name__}: {exc}")
        return 2

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
    tam.write_text(van_ban, encoding="utf-8")
    tam.replace(CSV_MAC_DINH)
    META_MAC_DINH.write_text(json.dumps({
        "tai_ve_luc": datetime.now(timezone.utc).isoformat(),
        "nguon": ENDPOINT,
        "giay_phep": "CC0 — Retraction Watch / Crossref",
        "so_dong": so_dong,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    idx = RetractionWatchIndex()
    print(f"✅ Đã tải {so_dong} dòng → {CSV_MAC_DINH.relative_to(REPO)}")
    print(f"   {idx.so_ban_ghi()} PMID có phán quyết (rút bài / expression of concern).")
    print("   Từ giờ tra hoàn toàn NGOẠI TUYẾN, không cần khoá và không hạn mức.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--kiem", action="store_true", help="chỉ xem trạng thái bản trên đĩa")
    ap.add_argument("--email", default="", help="email gửi Crossref (bắt buộc theo API của họ)")
    args = ap.parse_args()

    idx = RetractionWatchIndex()
    if args.kiem:
        return in_trang_thai(idx)

    email = args.email or _email()
    if not email:
        print("🔴 Crossref bắt buộc email. Dùng --email <địa chỉ> hoặc đặt OPENALEX_EMAIL.")
        return 2
    return tai(email)


if __name__ == "__main__":
    sys.exit(main())
