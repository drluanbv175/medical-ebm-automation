#!/usr/bin/env python3
"""Sinh `tools/chuan_bao_cao_items.py` — nguyên văn mục các chuẩn báo cáo giấy phép Creative Commons, từ XML Europe PMC.

VÌ SAO (21/11/2026): bác sĩ yêu cầu «từng mục trong cấu trúc đề cương phải đạt từng tiêu chuẩn», cho MỌI thiết kế. Trước
đó kho chỉ có danh mục theo mục cho RCT (SPIRIT 2025) và tổng quan hệ thống (PRISMA-P 2015). Thiết kế quan sát
(cắt ngang, thuần tập, bệnh–chứng) chưa có danh mục, nên các mục phương pháp của STROBE không được kiểm ở đề cương.
Cùng ngày, phần sau mở rộng sang chẩn đoán, tiên lượng, kinh tế y tế, cải tiến chất lượng, ca lâm sàng và mẫu đề cương
HARPER.

Nguyên tắc (giống SPIRIT 2025 trong `protocol_checklist_items.py`): lấy NGUYÊN VĂN bằng script, không gõ tay,
không dịch. Chỉ lưu nguyên văn khi bài nguồn mang giấy phép Creative Commons (đọc ở khối <license> của chính XML):
  - STROBE 2007 — E&E PLoS Med 2007;4(10):e297 (PMID 17941715; PMC2020496), CC BY. Bảng checklist của bài statement
    (PMC2020495) là ẢNH; bài E&E lặp lại nguyên văn từng mục ở tiêu đề tiểu mục, nên lấy từ đó.
  - RECORD 2015 — PLoS Med 2015;12(10):e1001885 (PMID 26440803; PMC4595218), CC BY. Table 1.
  - STARD 2015 — BMJ 2015;351:h5527 (PMID 26511519; PMC4623764), CC BY 4.0. Table 1.
  - TRIPOD+AI 2024 — BMJ 2024;385:e078378 (PMID 38626948; PMC11019967), CC BY 4.0. Table 2.
  - CHEERS 2022 — BMJ 2022;376:e067975 (PMID 35017145; PMC8749494), CC BY 4.0. Table 1.
  - SQUIRE 2.0 — BMJ Qual Saf 2016;25(12):986-992 (PMID 26369893; PMC5256233), CC BY-NC 4.0 (dùng phi thương mại).
  - CARE 2013 — J Med Case Rep 2013;7:223 (PMID 24228906; PMC3844611), CC BY 3.0. Table 1.
  - HARPER 2023 — Pharmacoepidemiol Drug Saf 2023;32(1):44-55 (PMID 36215113; PMC9771861), CC BY 4.0. Table 3 (mục lục
    của MẪU ĐỀ CƯƠNG, không phải checklist báo cáo).
Chuẩn KHÔNG mang giấy phép CC (CROSS, TREND, COREQ, SRQR, GRAMMS, COSMIN) không đi qua tệp này: bộ kiểm chỉ lưu mã mục,
chủ đề và tiêu chí do hệ viết.

Lệnh (cần XML đã tải từ Europe PMC REST `<PMCID>/fullTextXML`, đặt tên `raw_<PMCID>.xml` trong một thư mục):
    python3 tools/sinh_chuan_bao_cao_items.py --thu-muc <thư mục XML> [--ghi]
    (tương thích cũ: --strobe <PMC2020496.xml> --record <PMC4595218.xml>)
Chạy khô in số mục; `--ghi` ghi đè `tools/chuan_bao_cao_items.py` qua tệp tạm. Mỗi chuẩn kiểm số dòng kỳ vọng và kiểm
khối giấy phép của XML là Creative Commons — sai một trong hai thì KHÔNG ghi.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DICH = Path(__file__).resolve().parent / "chuan_bao_cao_items.py"
_TK = {"Cohort": "thuan_tap", "Case-control": "benh_chung", "Cross-sectional": "cat_ngang"}

#: chuẩn → (PMCID, số dòng kỳ vọng, chỉ số bảng checklist trong XML)
NGUON: Dict[str, Tuple[str, int, int]] = {
    "STROBE": ("PMC2020496", 41, -1),
    "RECORD": ("PMC4595218", 13, 0),
    "STARD": ("PMC4623764", 34, 0),
    "TRIPOD_AI": ("PMC11019967", 52, 1),
    "CHEERS": ("PMC8749494", 28, 0),
    "SQUIRE": ("PMC5256233", 40, 0),
    "CARE": ("PMC3844611", 23, 0),
    "HARPER": ("PMC9771861", 43, 2),
}


def _chu(el) -> str:
    """Chữ của một phần tử XML, gộp khoảng trắng."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def giay_phep(xml: Path) -> str:
    """Khối giấy phép của bài (URL creativecommons hoặc chữ của <license>); rỗng nếu không có."""
    goc = ET.parse(xml).getroot()
    for lic in goc.iter("license"):
        href = lic.get("{http://www.w3.org/1999/xlink}href") or ""
        van = _chu(lic)
        m = re.search(r"creativecommons\.org/licenses/[a-z-]+/\d\.\d", href + " " + van)
        if m:
            return m.group(0)
        if van:
            return van[:120]
    return ""


def _bang(xml: Path, chi_so: int):
    return list(ET.parse(xml).getroot().iter("table-wrap"))[chi_so]


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


def _hang(tw) -> List[List[Tuple[str, int, int]]]:
    """Mỗi hàng: [(chữ, colspan, rowspan)]."""
    return [[(_chu(td), int(td.get("colspan") or 1), int(td.get("rowspan") or 1)) for td in tr] for tr in tw.iter("tr")]


def muc_stard(xml: Path) -> list:
    """[(mã, phần, chủ đề, nguyên văn)] — STARD 2015 Table 1 (cột: Section and topic · No · Item)."""
    ra, phan, chu_de = [], "", ""
    for h in _hang(_bang(xml, NGUON["STARD"][2]))[1:]:
        if len(h) == 1 or h[0][1] >= 3:
            phan, chu_de = h[0][0], ""
            continue
        td, so, van = (c[0] for c in h[:3])
        chu_de = td or chu_de or phan
        ra.append((so, phan, chu_de, van))
    return ra


def muc_tripod_ai(xml: Path) -> list:
    """[(mã, phần, chủ đề, D/E, nguyên văn)] — TRIPOD+AI Table 2 (chủ đề trải nhiều hàng bằng rowspan)."""
    ra, phan, chu_de, con_lai = [], "", "", 0
    for h in _hang(_bang(xml, NGUON["TRIPOD_AI"][2]))[1:]:
        if len(h) == 1 or h[0][1] >= 4:
            phan, con_lai = h[0][0], 0
            continue
        if con_lai > 0 and len(h) == 3:
            so, de, van = (c[0] for c in h)
        else:
            chu_de, con_lai = h[0][0], h[0][2]
            so, de, van = (c[0] for c in h[1:4])
        con_lai -= 1
        ra.append((so, phan, chu_de, de, van))
    return ra


def muc_cheers(xml: Path) -> list:
    """[(mã, phần, chủ đề, nguyên văn)] — CHEERS 2022 Table 1 (cột cuối «Reported in section» bỏ)."""
    ra, phan = [], ""
    for h in _hang(_bang(xml, NGUON["CHEERS"][2]))[1:]:
        if h[0][1] >= 3:
            phan = h[0][0]
            continue
        ra.append((h[1][0], phan, h[0][0], h[2][0]))
    return ra


def muc_squire(xml: Path) -> Tuple[list, Dict[str, str]]:
    """([(mã, phần, chủ đề, nguyên văn)], {phần: câu dẫn}) — SQUIRE 2.0 Table 1; ô có danh sách a/b/c tách dòng con."""
    tw = _bang(xml, NGUON["SQUIRE"][2])
    ra, cau_dan, phan = [], {}, ""
    for tr in list(tw.iter("tr"))[1:]:
        o = list(tr)
        dau = _chu(o[0])
        if dau.startswith("Notes to authors"):
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", dau)
        if not m:
            phan = dau
            if len(o) > 1 and int(o[0].get("colspan") or 1) == 1:
                cau_dan[dau] = _chu(o[1])
            continue
        so, chu_de = m.group(1), m.group(2).strip()
        ds = o[1].find(".//list")
        if ds is not None and ds.get("list-type") == "alpha-lower":
            for k, li in enumerate(ds.findall("list-item")):
                ra.append((so + "abcdefghij"[k], phan, chu_de, _chu(li)))
        else:
            ra.append((so, phan, chu_de, _chu(o[1])))
    return ra, cau_dan


def muc_care(xml: Path) -> Tuple[list, str]:
    """([(mã, chủ đề, nguyên văn)], đoạn mở đầu) — CARE Table 1. «a) …» mở mục con; «- …» nối vào mục con trước."""
    hang = _hang(_bang(xml, NGUON["CARE"][2]))
    mo_dau = hang[0][0][0]
    ra: List[List[str]] = []
    so = chu_de = ""
    for h in hang[2:]:
        ten, s, van = (c[0] for c in h[:3])
        if s:
            so, chu_de = s, ten
        m = re.match(r"^([a-e])\)\s*(.*)$", van)
        if m:
            ra.append([so + m.group(1), chu_de, m.group(2)])
        elif van.startswith("- ") and ra:
            ra[-1][2] += " " + van
        else:
            ra.append([so, chu_de, van])
    return [tuple(x) for x in ra], mo_dau


def muc_harper(xml: Path) -> list:
    """[(mã, tiêu đề nguyên văn, thuộc mục)] — mục lục mẫu đề cương HARPER (Table 3); bảng cấu trúc mang mã T<n>."""
    ra, cuoi = [], ""
    for h in _hang(_bang(xml, NGUON["HARPER"][2])):
        van = h[0][0]
        mt = re.match(r"^Table (\d+)\.?\s+(.*)$", van)
        if mt:
            ra.append(("T" + mt.group(1), van, cuoi))
            continue
        m = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$", van)
        if m:
            cuoi = m.group(1)
            ra.append((cuoi, m.group(2).strip(), ""))
    return ra


def _bo(ten: str, chu_thich: str, dong: list) -> List[str]:
    ra = [f"# {chu_thich}", f"{ten} = ("]
    ra += [f"    {tuple(x)!r}," for x in dong]
    ra += [")", ""]
    return ra


def dung_mo_dun(du: Dict[str, object], phep: Dict[str, str]) -> str:
    """Văn bản mô-đun dữ liệu."""
    dong = [
        '"""Nguyên văn mục các chuẩn báo cáo mang giấy phép Creative Commons.',
        "",
        "SINH TỰ ĐỘNG bởi tools/sinh_chuan_bao_cao_items.py — KHÔNG sửa tay.",
        "",
        "Nguồn (lấy qua Europe PMC fullTextXML ngày 21/11/2026; giấy phép đọc từ khối <license> của chính XML):",
        "  STROBE E&E PLoS Med 2007;4(10):e297 (PMID 17941715; PMC2020496) · RECORD PLoS Med 2015;12(10):e1001885",
        "  (PMID 26440803; PMC4595218) · STARD BMJ 2015;351:h5527 (PMID 26511519; PMC4623764) · TRIPOD+AI BMJ",
        "  2024;385:e078378 (PMID 38626948; PMC11019967) · CHEERS BMJ 2022;376:e067975 (PMID 35017145; PMC8749494) ·",
        "  SQUIRE 2.0 BMJ Qual Saf 2016;25(12):986-992 (PMID 26369893; PMC5256233; CC BY-NC — phi thương mại) · CARE",
        "  J Med Case Rep 2013;7:223 (PMID 24228906; PMC3844611) · HARPER Pharmacoepidemiol Drug Saf 2023;32(1):44-55",
        "  (PMID 36215113; PMC9771861; mẫu đề cương).",
        '"""',
        "",
        "#: giấy phép đọc từ XML, theo chuẩn",
        f"GIAY_PHEP = {phep!r}",
        "",
    ]
    dong += _bo("STROBE_2007_ITEMS", "(mã, thiết kế: chung|cat_ngang|thuan_tap|benh_chung, chủ đề, nguyên văn)",
                du["STROBE"])
    dong += _bo("RECORD_2015_ITEMS", "(mã, nguyên văn)", du["RECORD"])
    dong += _bo("STARD_2015_ITEMS", "(mã, phần, chủ đề, nguyên văn)", du["STARD"])
    dong += _bo("TRIPOD_AI_2024_ITEMS", "(mã, phần, chủ đề, D/E — D: phát triển, E: đánh giá, nguyên văn)",
                du["TRIPOD_AI"])
    dong += _bo("CHEERS_2022_ITEMS", "(mã, phần, chủ đề, nguyên văn)", du["CHEERS"])
    dong += _bo("SQUIRE_2_0_ITEMS", "(mã, phần, chủ đề, nguyên văn)", du["SQUIRE"])
    dong += ["# câu dẫn của từng phần SQUIRE 2.0 (nguyên văn)", f"SQUIRE_2_0_CAU_DAN = {du['SQUIRE_CAU_DAN']!r}", ""]
    dong += _bo("CARE_2013_ITEMS", "(mã, chủ đề, nguyên văn)", du["CARE"])
    dong += ["# đoạn mở đầu bảng CARE (nguyên văn)", f"CARE_2013_MO_DAU = {du['CARE_MO_DAU']!r}", ""]
    dong += _bo("HARPER_2023_MUC_LUC", "(mã — T<n> là bảng cấu trúc, tiêu đề nguyên văn, bảng thuộc mục)", du["HARPER"])
    so = " and ".join(f"len({t}) == {len(du[k])}" for k, t in (
        ("STROBE", "STROBE_2007_ITEMS"), ("RECORD", "RECORD_2015_ITEMS"), ("STARD", "STARD_2015_ITEMS"),
        ("TRIPOD_AI", "TRIPOD_AI_2024_ITEMS"), ("CHEERS", "CHEERS_2022_ITEMS"), ("SQUIRE", "SQUIRE_2_0_ITEMS"),
        ("CARE", "CARE_2013_ITEMS"), ("HARPER", "HARPER_2023_MUC_LUC")))
    dong += ["assert (" + so.replace(" and ", "\n        and ") + ")", ""]
    return "\n".join(dong)


_HAM = {"STROBE": muc_strobe, "RECORD": muc_record, "STARD": muc_stard, "TRIPOD_AI": muc_tripod_ai,
        "CHEERS": muc_cheers, "HARPER": muc_harper}


def doc_tat_ca(thu_muc: Optional[Path],
               rieng: Dict[str, Optional[Path]]) -> Tuple[Dict[str, object], Dict[str, str], List[str]]:
    """Đọc mọi chuẩn; trả (dữ liệu, giấy phép, lỗi)."""
    du: Dict[str, object] = {}
    phep: Dict[str, str] = {}
    loi: List[str] = []
    for ten, (pmc, ky_vong, _i) in NGUON.items():
        xml = rieng.get(ten) or (thu_muc / f"raw_{pmc}.xml" if thu_muc else None)
        if xml is None or not xml.is_file():
            loi.append(f"{ten}: thiếu XML {pmc}")
            continue
        phep[ten] = giay_phep(xml)
        if "creativecommons.org/licenses/" not in phep[ten] and "Creative Commons" not in phep[ten]:
            loi.append(f"{ten}: giấy phép không phải Creative Commons ({phep[ten][:60]!r}) — không chép nguyên văn")
        try:
            if ten == "SQUIRE":
                du[ten], du["SQUIRE_CAU_DAN"] = muc_squire(xml)
            elif ten == "CARE":
                du[ten], du["CARE_MO_DAU"] = muc_care(xml)
            else:
                du[ten] = _HAM[ten](xml)
        except (IndexError, TypeError, AttributeError, ET.ParseError) as e:
            loi.append(f"{ten}: không đọc được bảng checklist ({type(e).__name__}) — bố cục nguồn có thể đã đổi")
            continue
        if len(du[ten]) != ky_vong:
            loi.append(f"{ten}: {len(du[ten])} dòng, kỳ vọng {ky_vong} — bố cục nguồn có thể đã đổi")
    return du, phep, loi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc", type=Path, help="thư mục chứa raw_<PMCID>.xml")
    ap.add_argument("--strobe", type=Path)
    ap.add_argument("--record", type=Path)
    ap.add_argument("--ghi", action="store_true")
    a = ap.parse_args(argv)
    du, phep, loi = doc_tat_ca(a.thu_muc, {"STROBE": a.strobe, "RECORD": a.record})
    for ten in NGUON:
        if ten in du:
            print(f"{ten}: {len(du[ten])} dòng · giấy phép {phep.get(ten, '')[:60]}")
    if loi:
        print("KHÔNG ghi:\n  " + "\n  ".join(loi))
        return 1
    if a.ghi:
        tam = DICH.with_suffix(".py.tam")
        tam.write_text(dung_mo_dun(du, phep), encoding="utf-8", newline="\n")
        os.replace(tam, DICH)
        print("đã ghi", DICH.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
