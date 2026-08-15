#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HỎI TOÀN VĂN ĐÃ GOM — tìm cụm/số trong kho JATS XML của một đề tài (PHA R5-D).

Vì sao: SciSpace trả lời câu hỏi TRÊN TOÀN VĂN kèm trích đoạn; hệ này nay có kho
toàn văn OA hợp pháp cho từng đề tài (`gom_toan_van_oa.py`) nhưng chưa có máy
hỏi. Công cụ này là lớp «grounding» ngoại tuyến: mỗi kết quả kèm PMID + PMCID +
đoạn ngữ cảnh NGẮN để bác sĩ nhảy thẳng tới chỗ cần đọc — máy KHÔNG diễn giải
thay, không tóm tắt thay (đó là việc của bác sĩ/agent thẩm định với nguồn mở sẵn).

Dùng:  python3 tools/doc_toan_van.py --study <mã> --tim "response rate"
       python3 tools/doc_toan_van.py --study <mã> --thong-ke
Mã thoát: 0 = chạy trọn · 1 = không có kho toàn văn · 2 = tham số sai.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"


def _van_ban(xml_path: Path) -> str:
    """JATS XML → văn bản thuần (bỏ thẻ, gộp khoảng trắng). Parse hỏng → chuỗi rỗng
    có khai — một file hỏng không được giết cả kho."""
    try:
        goc = ET.fromstring(xml_path.read_bytes())
    except ET.ParseError:
        return ""
    return re.sub(r"\s+", " ", " ".join(goc.itertext()))


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def main() -> int:
    ap = argparse.ArgumentParser(description="Hỏi kho toàn văn OA của một đề tài")
    ap.add_argument("--study", required=True)
    ap.add_argument("--tim", help="cụm từ/con số cần tìm (không dấu cũng khớp)")
    ap.add_argument("--thong-ke", action="store_true")
    ap.add_argument("--max", type=int, default=3, help="số đoạn ngữ cảnh mỗi bài")
    a = ap.parse_args()
    kho = EXPORTS / a.study / "toan_van_oa"
    files = sorted(kho.glob("PMID-*.xml"))
    if not files:
        print(f"🔴 Chưa có kho toàn văn cho {a.study} — chạy gom_toan_van_oa trước.")
        return 1
    if a.thong_ke or not a.tim:
        tong = 0
        for f in files:
            n = len(_van_ban(f).split())
            tong += n
            print(f"  {f.name}: ~{n:,} từ")
        print(f"KHO: {len(files)} bài toàn văn OA · ~{tong:,} từ — sẵn cho thẩm định")
        return 0

    truy = _bo_dau(a.tim)
    thay = 0
    for f in files:
        vb = _van_ban(f)
        vb_bd = _bo_dau(vb)
        vi_tri = [m.start() for m in re.finditer(re.escape(truy), vb_bd)][: a.max]
        if not vi_tri:
            continue
        thay += 1
        pm = re.search(r"PMID-(\d+)_PMC(\d+)", f.name)
        print(f"\n📄 PMID {pm.group(1)} (PMC{pm.group(2)}) — {len(vi_tri)} chỗ khớp"
              f" · đọc đủ: https://pmc.ncbi.nlm.nih.gov/articles/PMC{pm.group(2)}/")
        for v in vi_tri:
            doan = vb[max(0, v - 70):v + 90].strip()
            print(f"   …{doan}…")
    if not thay:
        print(f"Không bài nào trong {len(files)} toàn văn chứa «{a.tim}» — "
              "đó là SỰ THẬT về kho OA này, không phải máy đoán.")
    else:
        print(f"\n{thay}/{len(files)} bài chứa «{a.tim}». Máy chỉ TRÍCH VỊ TRÍ — "
              "diễn giải là của bác sĩ. Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
