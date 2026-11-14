#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đối chiếu LỜI KHAI trong mô tả A12 với biên nhận máy-kiểm (A12_RETRACTION_RECEIPT / A12_METADATA_RECEIPT).

Vì sao (12/11/2026, nhóm B — B3; bình duyệt độc lập C1a 29/10): `citation_verification_ok()` của run_g10_assemble chỉ
kiểm mọi PMID nhắc trong `A12_CITATION_VERIFICATION_<mã>.md` đã nằm trong biên nhận — KHÔNG kiểm phần mô tả bằng chứng.
Mô tả A12 của C1a viết tay ngày 14/10 ghi «Rút bài + metadata 9 PMID … (2026-10-14T13:42:42Z)» trong khi biên nhận
hiện hành kiểm 35 PMID lúc 2026-10-15T14:00Z: người đọc hồ sơ thấy một bằng chứng KHÔNG còn tồn tại.

Công cụ này chỉ ĐO và BÁO, không sửa tệp nào. Từ 14/11/2026 (bác sĩ duyệt) `run_g10_assemble.main()` dùng kết quả
LỆCH để CHẶN LẮP MỚI G10 (mã lý do `gate_contract.REASON_A12_DESCRIPTION_MISMATCH`); phép chấm sống
(`citation_verification_ok`, g10_quality_gate G10-AUTO-05) KHÔNG đổi nên gói G10 đã ký giữ nguyên trạng thái.
`--goi-y` in dòng «Bằng chứng máy-kiểm» dựng THẲNG từ biên nhận để dán vào lượt sửa sau.

Ba loại lời khai được đối chiếu ĐỘC LẬP (sửa 14/11/2026 theo bình duyệt PR #227):
- số PMID: CHỈ đọc ô ĐẦU (tên bước) của dòng bảng có chữ «rút bài»/«metadata»/«retraction», lấy cụm «N PMID(s)» đầu
  tiên của ô đó — ghi chú ở ô khác hay dòng văn xuôi («0 PMID bị rút», «Ghi chú metadata: 2 PMID có erratum») không
  phải lời khai số PMID đã kiểm (bản cũ gom mọi cụm trên dòng ⇒ chặn sai mô tả khai đúng);
- thời điểm (mọi mốc ISO trong mục bằng chứng — lệch khi KHÔNG mốc nào trùng mốc biên nhận);
- `all_clean=true|false`.
Thiếu số PMID KHÔNG còn làm bỏ qua hai phép so còn lại (bản cũ trả KHÔNG ĐO ĐƯỢC sớm ⇒ mô tả ghi «9 PMIDs»/«9 bài» kèm
thời điểm sai vẫn lọt luật chặn G10).

Mã thoát: 0 KHỚP · 1 LỆCH · 2 KHÔNG ĐO ĐƯỢC (thiếu tệp / mô tả không có lời khai nào kiểm được: số PMID, thời điểm,
all_clean) — «không đo được» không phải «khớp».
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"

_RE_SO_PMID = re.compile(r"(\d+)\s*PMIDs?\b")
_RE_BUOC_KIEM = re.compile(r"rút bài|metadata|retraction", re.I)
_RE_MOC = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?Z?")
_RE_ALL_CLEAN = re.compile(r"all_clean\s*=\s*(true|false)", re.I)


def _doc_json(p: Path) -> dict | None:
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return j if isinstance(j, dict) else None


def _muc_bang_chung(md: str) -> str:
    """Phần mô tả bằng chứng máy-kiểm: từ đầu tệp tới tiêu đề «## 2» (đối chiếu nội dung từng PMID không tính)."""
    m = re.search(r"^##\s*2\b", md, re.M)
    return md[: m.start()] if m else md


def _so_pmid_khai(phan: str) -> list[int]:
    """Số PMID mô tả khai đã kiểm: chỉ ô ĐẦU (tên bước) của dòng bảng nhắc bước rút bài/metadata, cụm đầu tiên."""
    so: set[int] = set()
    for dong in phan.splitlines():
        s = dong.strip()
        if not s.startswith("|"):
            continue
        o_dau = s.strip("|").split("|", 1)[0]
        if not _RE_BUOC_KIEM.search(o_dau):
            continue
        m = _RE_SO_PMID.search(o_dau)
        if m:
            so.add(int(m.group(1)))
    return sorted(so)


def doi_chieu(study: str, out_dir: Path | None = None) -> dict[str, Any]:
    """{trang_thai: KHOP|LECH|KHONG_DO_DUOC, chi_tiet: [...], bien_nhan: {...}, da_doi_chieu: [...]}.

    `da_doi_chieu`: loại lời khai đã so được (`so_pmid` · `thoi_diem` · `all_clean`) — KHỚP chỉ nói về các loại này.
    LỆCH khi MỘT lời khai kiểm được lệch biên nhận; KHÔNG ĐO ĐƯỢC chỉ khi không có lời khai nào kiểm được."""
    d = Path(out_dir) if out_dir is not None else EXPORTS / study
    md_p = d / f"A12_CITATION_VERIFICATION_{study}.md"
    rut = _doc_json(d / "A12_RETRACTION_RECEIPT.json")
    meta = _doc_json(d / "A12_METADATA_RECEIPT.json")
    if not md_p.exists() or rut is None or not isinstance(rut.get("pmids_checked"), list):
        return {"trang_thai": "KHONG_DO_DUOC", "chi_tiet": ["thiếu mô tả A12 hoặc biên nhận rút bài đọc được"],
                "bien_nhan": {}, "da_doi_chieu": []}
    n_rut = len(rut["pmids_checked"])
    moc_rut = str(rut.get("checked_at_utc") or "")[:16]
    bn = {"so_pmid": n_rut, "moc": moc_rut, "all_clean": rut.get("all_clean")}
    if meta is not None:
        bn["moc_metadata"] = str(meta.get("checked_at_utc") or "")[:16]
        bn["all_resolved"] = meta.get("all_resolved")
    phan = _muc_bang_chung(md_p.read_text(encoding="utf-8", errors="replace"))
    so_khai = _so_pmid_khai(phan)
    moc_khai = set(_RE_MOC.findall(phan))
    all_clean_khai = {g.lower() for g in _RE_ALL_CLEAN.findall(phan)}
    da_doi_chieu = [ten for ten, co in (("so_pmid", so_khai), ("thoi_diem", moc_khai), ("all_clean", all_clean_khai))
                    if co]
    if not da_doi_chieu:
        return {"trang_thai": "KHONG_DO_DUOC",
                "chi_tiet": ["mô tả A12 không có lời khai nào kiểm được ở mục bằng chứng "
                             "(số PMID, thời điểm, all_clean)"],
                "bien_nhan": bn, "da_doi_chieu": []}
    # Mỗi loại lời khai so ĐỘC LẬP — thiếu số PMID không được làm bỏ qua phép so thời điểm/all_clean.
    lech = [f"mô tả khai {n} PMID, biên nhận rút bài kiểm {n_rut}" for n in so_khai if n != n_rut]
    moc_bn = {moc_rut} | ({bn["moc_metadata"]} if bn.get("moc_metadata") else set())
    if moc_khai and not (moc_khai & moc_bn):
        lech.append(f"mô tả ghi thời điểm {', '.join(sorted(moc_khai))}, biên nhận lúc {', '.join(sorted(moc_bn))}")
    for gt in sorted(all_clean_khai):
        if (gt == "true") != bool(rut.get("all_clean")):
            lech.append(f"mô tả ghi all_clean={gt}, biên nhận all_clean={rut.get('all_clean')}")
    return {"trang_thai": "LECH" if lech else "KHOP", "chi_tiet": lech, "bien_nhan": bn, "da_doi_chieu": da_doi_chieu}


def goi_y(study: str, out_dir: Path | None = None) -> str:
    """Dòng bảng «Bằng chứng máy-kiểm» dựng từ biên nhận (dán vào mô tả A12 ở lượt sửa sau)."""
    bn = doi_chieu(study, out_dir)["bien_nhan"]
    if not bn:
        return ""
    phan_meta = (f"; `A12_METADATA_RECEIPT.json` all_resolved={str(bn.get('all_resolved')).lower()} "
                 f"({bn.get('moc_metadata')}Z)" if bn.get("moc_metadata") else "")
    return (f"| Rút bài + metadata {bn['so_pmid']} PMID | `tools/check_citations.py --study {study}` | "
            f"`A12_RETRACTION_RECEIPT.json` all_clean={str(bn.get('all_clean')).lower()} ({bn['moc']}Z){phan_meta} |")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Đối chiếu mô tả A12 với biên nhận máy-kiểm (chỉ đọc).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--goi-y", action="store_true", help="in dòng bằng chứng dựng từ biên nhận")
    a = ap.parse_args(argv)
    kq = doi_chieu(a.study)
    nhan = {"KHOP": "🟢 KHỚP", "LECH": "🟠 LỆCH", "KHONG_DO_DUOC": "⚪ KHÔNG ĐO ĐƯỢC"}[kq["trang_thai"]]
    print(f"{nhan} — mô tả A12 ↔ biên nhận ({a.study})")
    for d in kq["chi_tiet"]:
        print(f"  • {d}")
    if kq.get("da_doi_chieu"):
        print(f"  (đã đối chiếu: {', '.join(kq['da_doi_chieu'])})")
    if a.goi_y:
        print(goi_y(a.study) or "(không có biên nhận để dựng dòng gợi ý)")
    print("Cần bác sĩ kiểm chứng.")
    return {"KHOP": 0, "LECH": 1}.get(kq["trang_thai"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
