#!/usr/bin/env python3
"""Sinh `tools/chuan_bao_cao_items.py` — nguyên văn mục STROBE 2007 và RECORD 2015 từ XML toàn văn Europe PMC.

VÌ SAO (21/11/2026): bác sĩ yêu cầu «từng mục trong cấu trúc đề cương phải đạt từng tiêu chuẩn», cho MỌI thiết kế. Trước
đó kho chỉ có danh mục theo mục cho RCT (SPIRIT 2025) và tổng quan hệ thống (PRISMA-P 2015). Thiết kế quan sát
(cắt ngang, thuần tập, bệnh–chứng) chưa có danh mục, nên các mục phương pháp của STROBE không được kiểm ở đề cương.

Nguyên tắc (giống SPIRIT 2025 trong `protocol_checklist_items.py`): lấy NGUYÊN VĂN bằng script, không gõ tay,
không dịch.
Chỉ lưu nguyên văn khi bài nguồn mang giấy phép Creative Commons. Cả hai bài dưới đây đều CC BY:
  - STROBE: Vandenbroucke JP et al. Strengthening the Reporting of Observational Studies in Epidemiology (STROBE):
    explanation and elaboration. PLoS Med 2007;4(10):e297 (PMID 17941715; PMC2020496). Bảng checklist của bài statement
    (PMC2020495) là ẢNH. Bài E&E lặp lại nguyên văn từng mục ở tiêu đề tiểu mục, nên lấy từ đó.
  - RECORD: Benchimol EI et al. The REporting of studies Conducted using Observational Routinely-collected health Data
    (RECORD) statement. PLoS Med 2015;12(10):e1001885 (PMID 26440803; PMC4595218). Lấy từ Table 1 dạng XML.

Lệnh (cần hai tệp XML đã tải từ Europe PMC REST `<PMCID>/fullTextXML`; chạy lại khi cần kiểm chứng):
    python3 tools/sinh_chuan_bao_cao_items.py --strobe <PMC2020496.xml> --record <PMC4595218.xml> [--ghi]
Chạy khô in số mục; `--ghi` ghi đè `tools/chuan_bao_cao_items.py` qua tệp tạm.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DICH = Path(__file__).resolve().parent / "chuan_bao_cao_items.py"
_TK = {"Cohort": "thuan_tap", "Case-control": "benh_chung", "Cross-sectional": "cat_ngang"}


def _chu(el) -> str:
    """Chữ của một phần tử XML, gộp khoảng trắng."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def muc_strobe(xml: Path) -> list:
    """[(mã, thiết kế, chủ đề, nguyên văn)] từ tiêu đề tiểu mục của bài E&E STROBE."""
    goc = ET.parse(xml).getroot()
    tieu_de = []
    for sec in goc.iter("sec"):
        t = sec.find("title")
        tt = re.sub(r"^(TITLE AND ABSTRACT|OTHER INFORMATION)\s+", "", _chu(t)) if t is not None else ""
        if re.match(r"^\d+\s*(\([a-e]\))?\.\s", tt) or re.match(r"^(Case-control|Cross-sectional) study: Report", tt):
            tieu_de.append(tt)
    ra, truoc = [], None
    for tt in tieu_de:
        m = re.match(r"^(\d+)\.\s+([A-Za-z/ ]+):\s+(\d+ \(([a-e])\)\.\s+)?(.*)$", tt)
        m2 = re.match(r"^(\d+) \(([a-e])\)\.\s+(.*)$", tt)
        if m:
            so, chu_de, con, van = m.group(1), m.group(2).strip(), m.group(4) or "", m.group(5)
        elif m2:
            so, con, van = m2.group(1), m2.group(2), m2.group(3)
            chu_de = truoc[1] if truoc and truoc[0] == so else ""
        else:
            so, chu_de, con, van = truoc[0], truoc[1], truoc[2], tt
        tk = "chung"
        mm = re.match(r"^(Cohort|Case-control|Cross-sectional) study:\s+(.*)$", van)
        if mm:
            tk, van = _TK[mm.group(1)], mm.group(2)
        truoc = (so, chu_de, con)
        if so == "1":
            chu_de = "Title and abstract"
        ra.append((so + con, tk, chu_de, van))
    return ra


def muc_record(xml: Path) -> list:
    """[(mã, nguyên văn)] các mục RECORD x.y trong Table 1."""
    goc = ET.parse(xml).getroot()
    ra = []
    for tw in goc.iter("table-wrap"):
        for tr in tw.iter("tr"):
            for td in tr:
                for m in re.finditer(r"RECORD (\d+\.\d+):\s*(.*?)(?=RECORD \d+\.\d+:|$)", _chu(td)):
                    ra.append((m.group(1), m.group(2).strip()))
        break
    return ra


def dung_mo_dun(strobe: list, record: list) -> str:
    """Văn bản mô-đun dữ liệu."""
    dong = [
        '"""Nguyên văn mục STROBE 2007 và RECORD 2015.',
        "",
        "SINH TỰ ĐỘNG bởi tools/sinh_chuan_bao_cao_items.py — KHÔNG sửa tay.",
        "",
        "Nguồn (CC BY): STROBE E&E PLoS Med 2007;4(10):e297 (PMID 17941715; PMC2020496) · RECORD PLoS Med 2015;12(10):",
        "e1001885 (PMID 26440803; PMC4595218). Lấy qua Europe PMC fullTextXML ngày 21/11/2026.",
        '"""',
        "",
        "# (mã, thiết kế: chung|cat_ngang|thuan_tap|benh_chung, chủ đề, nguyên văn)",
        "STROBE_2007_ITEMS = (",
    ]
    dong += [f"    ({ma!r}, {tk!r}, {cd!r}, {van!r})," for ma, tk, cd, van in strobe]
    dong += [")", "", "# (mã, nguyên văn)", "RECORD_2015_ITEMS = ("]
    dong += [f"    ({ma!r}, {van!r})," for ma, van in record]
    dong += [")", "", f"assert len(STROBE_2007_ITEMS) == {len(strobe)} and len(RECORD_2015_ITEMS) == {len(record)}", ""]
    return "\n".join(dong)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strobe", required=True, type=Path)
    ap.add_argument("--record", required=True, type=Path)
    ap.add_argument("--ghi", action="store_true")
    a = ap.parse_args(argv)
    s, r = muc_strobe(a.strobe), muc_record(a.record)
    print(f"STROBE: {len(s)} dòng · RECORD: {len(r)} mục")
    if len(s) != 41 or len(r) != 13:
        print("Số mục khác kỳ vọng (41 · 13) — bố cục nguồn có thể đã đổi, không ghi.")
        return 1
    if a.ghi:
        tam = DICH.with_suffix(".py.tam")
        tam.write_text(dung_mo_dun(s, r), encoding="utf-8", newline="\n")
        os.replace(tam, DICH)
        print("đã ghi", DICH.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
