#!/usr/bin/env python3
"""Đối chiếu mọi con số trong các câu có trích dẫn [n] với TOÀN VĂN của đúng tài liệu được dẫn (TƯ VẤN, 20/11/2026).

VÌ SAO: bác sĩ yêu cầu «kiểm tra và hoàn thiện tổng quan tài liệu». Lượt soát tay đề cương BTM tìm thấy con số gán
lệch quần thể (46,9% là của mọi người bệnh thận mạn chứ không phải người ĐTĐ típ 2), ước lượng chọn lọc (chỉ nêu 22% mà
bỏ 49%) — các chốt K1–K13 không thấy vì chúng không đọc nguồn. `kiem_noi_dung_trich_dan.py` đọc nguồn ở mức ABSTRACT và
gọi API tính phí; công cụ này đọc TOÀN VĂN có sẵn trên máy, không mạng, không phí.

Cách làm: tách khoảng văn bản (mặc định từ «ĐẶT VẤN ĐỀ» tới «ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP») thành từng VẾ (dấu chấm hoặc
chấm phẩy); vế nào mang trích dẫn [n] thì mọi con số trong vế (trừ năm, số hiệu khuyến cáo/mục/bảng/mục tiêu) phải có
trong toàn văn của CÁC tài liệu được dẫn ở chính vế đó. So linh hoạt kiểu viết: «24,9» ↔ «24.9», «316.234» ↔ «316 234»
/ «316,234».

Nguồn toàn văn (theo thứ tự): `exports/<mã>/toan_van_oa/PMID-<pmid>_*.xml` (JATS) → `toan_van_trong_nuoc/` và
`toan_van_tltk/` (`DOI-<doi, «/» thành «_»>.pdf`, `TLTK-<n>.pdf`) → PDF đính kèm trong thư viện EndNote khai ở
`~/.ebm-endnote.json` (đọc BẢN SAO `sdb.eni`, chỉ đọc; BỎ tệp `*TomTatChungCu*` — đó là bản tóm tắt do hệ thống dựng,
không phải nguồn: ngày 20/11/2026 tệp đính kèm đầu tiên của KDIGO 2022/2024 là bản tóm tắt).

GIỚI HẠN (nói thẳng): (1) số viết bằng chữ trong nguồn («Eighty-eight») máy không thấy ⇒ báo «không thấy», người đọc
soát bằng mắt; (2) số ngắn («1,1») có thể trùng ngẫu nhiên với một chỗ khác trong bài ⇒ không chứng minh được đúng ngữ
cảnh — đột biến chuyển «1,1%» sang sai tài liệu từng lọt; (3) chỉ kiểm SỰ CÓ MẶT của con số, không kiểm quần thể hay
chiều liên quan — vẫn phải đọc; (4) tài liệu không có toàn văn trên máy ⇒ vế đó «chưa đối chiếu được», không phải lỗi.

Ranh giới: TƯ VẤN — không sửa đề cương, không ghi biên nhận, không mở/chặn cổng.
Lệnh:  python3 tools/kiem_so_lieu_toan_van.py --study <mã> [--tep <.md>] [--tu "ĐẶT VẤN ĐỀ"] [--den "ĐỐI TƯỢNG"]
                                               [--khong-endnote] [--json]
Mã thoát: 0 mọi con số đều thấy · 1 có con số không thấy trong nguồn · 2 không đối chiếu được (thiếu tệp/khoảng
văn bản/không tài liệu nào có toàn văn) · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402

TEN_MAC_DINH = "DE_CUONG_NOP_HOI_DONG_{study}.md"
BO_TEP_HE_THONG = ("TomTatChungCu",)  # tệp do hệ thống dựng, không phải nguồn
_SO_RE = re.compile(r"\d{1,3}(?:\.\d{3})+|\d+,\d+|\d+")
_NAM_RE = re.compile(r"^(19|20)\d\d$")
_SO_HIEU_RE = re.compile(r"(khuyến cáo|điểm thực hành|mục|Mục|Bảng|Hình|MT|phụ lục|Phụ lục)\s*[\d.]+[a-z]?")
_TACH_VE_RE = re.compile(r"(?<=\.)\s+|;\s+|\n")


@dataclass
class Ve:
    """Một vế văn bản mang trích dẫn và kết quả đối chiếu."""
    tai_lieu: List[int]
    trich: str
    khong_thay: List[str] = field(default_factory=list)
    thieu_toan_van: List[int] = field(default_factory=list)


def _khoa_muc(noi_dung: str, so: int) -> Dict[str, Optional[str]]:
    pm = re.search(r"PMID:\s*(\d+)", noi_dung)
    do = re.search(r"doi:\s*(\S+?)\.?(?:\s|$)", noi_dung, re.I)
    return {"so": str(so), "pmid": pm.group(1) if pm else None,
            "doi": do.group(1).rstrip(".").lower() if do else None}


def _van_xml(p: Path) -> str:
    try:
        goc = ET.parse(str(p)).getroot()
    except (ET.ParseError, OSError):
        return ""
    return " ".join(" ".join(e.itertext()) for e in goc.iter()
                    if str(e.tag).split("}")[-1] in ("p", "title", "td", "th", "caption", "label", "abstract"))


def _van_pdf(p: Path) -> str:
    try:
        from pypdf import PdfReader  # noqa: PLC0415 — chỉ cần khi có PDF
    except ImportError:
        return ""
    try:
        return "\n".join((trang.extract_text() or "") for trang in PdfReader(str(p)).pages)
    except Exception:  # noqa: BLE001 — PDF hỏng/mã hoá: coi như không đọc được, không làm sập lượt kiểm
        return ""


def chon_tep_endnote(duong_dan: Sequence[Path]) -> Optional[Path]:
    """PDF nguồn đầu tiên còn trên đĩa, BỎ tệp do hệ thống dựng (`*TomTatChungCu*`)."""
    for p in duong_dan:
        if p.suffix.lower() == ".pdf" and not any(x in p.name for x in BO_TEP_HE_THONG) and p.is_file():
            return p
    return None


class NguonEndNote:
    """Tra PDF đính kèm của thư viện EndNote qua BẢN SAO `sdb.eni` (chỉ đọc, không đụng thư viện thật)."""

    def __init__(self, cau_hinh: Path = Path.home() / ".ebm-endnote.json"):
        self.db = None
        self.thu_muc_pdf: Optional[Path] = None
        self._tam: Optional[Path] = None
        try:
            thu_vien = Path(json.loads(cau_hinh.read_text(encoding="utf-8"))["thu_vien"])
        except (OSError, ValueError, KeyError, TypeError):
            return
        du_lieu = thu_vien.with_suffix(".Data")
        sdb = du_lieu / "sdb" / "sdb.eni"
        if not sdb.is_file():
            return
        self._tam = Path(tempfile.mkdtemp(prefix="ebm_sdb_"))
        ban_sao = self._tam / "sdb.eni"
        try:
            shutil.copy2(sdb, ban_sao)
            self.db = sqlite3.connect(f"file:{ban_sao.as_posix()}?mode=ro", uri=True)
            cot = [r[1] for r in self.db.execute("pragma table_info(refs)")]
            self._cot_doi = "electronic_resource_number" if "electronic_resource_number" in cot else None
        except (OSError, sqlite3.Error):
            self.db = None
        self.thu_muc_pdf = du_lieu / "PDF"

    def tim(self, pmid: Optional[str], doi: Optional[str]) -> Optional[Path]:
        if self.db is None or self.thu_muc_pdf is None:
            return None
        dieu_kien = []
        if pmid:
            dieu_kien.append(("accession_number = ?", pmid))
        if doi and self._cot_doi:
            dieu_kien.append((f"lower({self._cot_doi}) = ?", doi))
        for cau, gt in dieu_kien:
            try:
                ids = [r[0] for r in self.db.execute(f"select id from refs where trash_state = 0 and {cau}", (gt,))]
                tep: List[Path] = []
                for rid in ids:
                    for (fp,) in self.db.execute("select file_path from file_res where refs_id = ?", (rid,)):
                        p = Path(fp)
                        tep.append(p if p.is_absolute() else self.thu_muc_pdf / fp)
            except sqlite3.Error:
                return None
            chon = chon_tep_endnote(tep)
            if chon:
                return chon
        return None

    def dong(self) -> None:
        if self.db is not None:
            self.db.close()
        if self._tam is not None:
            shutil.rmtree(self._tam, ignore_errors=True)


def van_toan_van(out_dir: Path, khoa: Dict[str, Optional[str]], endnote: Optional[NguonEndNote]) -> str:
    """Văn bản toàn văn của một tài liệu (rỗng nếu máy không có)."""
    if khoa.get("pmid"):
        for p in sorted((out_dir / "toan_van_oa").glob(f"PMID-{khoa['pmid']}_*.xml")):
            van = _van_xml(p)
            if van.strip():
                return van
    ung_vien: List[Path] = []
    if khoa.get("doi"):
        ten = "DOI-" + str(khoa["doi"]).replace("/", "_") + ".pdf"
        ung_vien += [out_dir / "toan_van_trong_nuoc" / ten, out_dir / "toan_van_tltk" / ten]
    ung_vien.append(out_dir / "toan_van_tltk" / f"TLTK-{khoa['so']}.pdf")
    for p in ung_vien:
        if p.is_file():
            van = _van_pdf(p)
            if van.strip():
                return van
    if endnote is not None:
        p = endnote.tim(khoa.get("pmid"), khoa.get("doi"))
        if p:
            return _van_pdf(p)
    return ""


def mau_so(tok: str) -> str:
    """Regex linh hoạt cho một con số viết kiểu Việt Nam."""
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", tok):  # 316.234 ↔ 316 234 / 316,234 / 316234
        return r"(?<![\d.,])" + r"[\s,.  ]?".join(tok.split(".")) + r"(?!\d)"
    if "," in tok:  # 24,9 ↔ 24.9
        a, b = tok.split(",")
        return rf"(?<![\d.,]){a}[.,]{b}(?!\d)"
    return rf"(?<![\d.,]){tok}(?!\d)"


def khoang_van_ban(md: str, tu: str, den: str) -> Optional[str]:
    """Đoạn từ đề mục chứa `tu` tới đề mục chứa `den` (không phân biệt hoa thường)."""
    dong = md.splitlines()
    bd = next((i for i, d in enumerate(dong) if d.startswith("#") and tu.lower() in d.lower()), None)
    if bd is None:
        return None
    kt = next((i for i in range(bd + 1, len(dong)) if dong[i].startswith("#") and den.lower() in dong[i].lower()),
              len(dong))
    return "\n".join(dong[bd:kt])


def doi_chieu(van: str, muc: Dict[int, str], lay_van) -> List[Ve]:
    """Đối chiếu từng vế; `lay_van(so)` trả toàn văn của tài liệu số `so` (rỗng nếu không có)."""
    bo_dem: Dict[int, str] = {}

    def nguon(so: int) -> str:
        if so not in bo_dem:
            bo_dem[so] = re.sub(r"\s+", " ", lay_van(so) or "")
        return bo_dem[so]

    ket_qua: List[Ve] = []
    for ve in _TACH_VE_RE.split(van):
        ngoac = KDN._TRICH_SO_RE.findall(ve)
        if not ngoac:
            continue
        so = sorted({x for s in ngoac for x in KDN._mo_rong_trich(s) if x in muc})
        if not so:
            continue
        sach = KDN._TRICH_SO_RE.sub(" ", ve)
        sach = _SO_HIEU_RE.sub(" ", sach)
        toks = [t for t in _SO_RE.findall(sach) if not _NAM_RE.match(t)]
        if not toks:
            continue
        gop = " ".join(nguon(s) for s in so)
        thieu_tv = [s for s in so if not nguon(s).strip()]
        khong = [t for t in toks if not re.search(mau_so(t), gop)]
        # mọi con số đã thấy trong nguồn có toàn văn ⇒ vế đạt dù một tài liệu khác trong ngoặc chưa có toàn văn
        if khong:
            ket_qua.append(Ve(tai_lieu=so, trich=ve.strip()[:220], khong_thay=khong, thieu_toan_van=thieu_tv))
    return ket_qua


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu con số trong câu có trích dẫn với toàn văn nguồn (tư vấn).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--tep", help="tệp Markdown (mặc định: đề cương nộp Hội đồng của đề tài)")
    ap.add_argument("--tu", default="ĐẶT VẤN ĐỀ", help="đề mục bắt đầu khoảng kiểm")
    ap.add_argument("--den", default="ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP", help="đề mục kết thúc khoảng kiểm (không gồm)")
    ap.add_argument("--khong-endnote", action="store_true", help="không tra PDF đính kèm EndNote")
    ap.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 3
    out_dir = BASE / "exports" / a.study
    tep = Path(a.tep) if a.tep else out_dir / TEN_MAC_DINH.format(study=a.study)
    if not tep.is_file():
        print(f"Không thấy tệp {tep}")
        return 2
    md = tep.read_text(encoding="utf-8")
    van = khoang_van_ban(md, a.tu, a.den)
    if van is None:
        print(f"Không thấy đề mục chứa «{a.tu}»")
        return 2
    _, muc = KDN._tach_tltk(md)
    khoa = {so: _khoa_muc(nd, so) for so, nd in muc.items()}
    endnote = None if a.khong_endnote else NguonEndNote()
    da_doc: Dict[int, str] = {}

    def lay(so: int) -> str:
        if so not in da_doc:
            da_doc[so] = van_toan_van(out_dir, khoa[so], endnote)
        return da_doc[so]

    try:
        ket_qua = doi_chieu(van, muc, lay)
    finally:
        if endnote is not None:
            endnote.dong()
    co_van = [so for so, v in da_doc.items() if v.strip()]
    loi = [v for v in ket_qua if v.khong_thay and not v.thieu_toan_van]
    chua = [v for v in ket_qua if v.thieu_toan_van]
    if a.json:
        print(json.dumps({"study": a.study, "khong_thay": [asdict(v) for v in loi],
                          "chua_doi_chieu_duoc": [asdict(v) for v in chua]}, ensure_ascii=False, indent=1))
    else:
        for v in loi:
            print(f"✗ [{', '.join(map(str, v.tai_lieu))}] không thấy {v.khong_thay} trong toàn văn: {v.trich}…")
        for v in chua:
            print(f"⚪ [{', '.join(map(str, v.tai_lieu))}] chưa đối chiếu được — chưa có toàn văn "
                  f"{v.thieu_toan_van} (con số chưa thấy: {v.khong_thay or 'không'}): {v.trich[:120]}…")
        print(f"\n{a.study}: {len(loi)} vế có con số không thấy trong nguồn · {len(chua)} vế chưa đối chiếu được. "
              "Phép kiểm chỉ xét SỰ CÓ MẶT của con số — quần thể, chiều liên quan vẫn phải đọc. Cần bác sĩ kiểm chứng.")
    if loi:
        return 1
    if not co_van:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
