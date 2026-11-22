#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""go_khung_ban_thao_g7.py — gỡ KHUNG bản nháp khỏi bản thảo G7 (A8) để thành bản NỘP — không đổi nội dung khoa học.

Vì sao (giả lập trọn vòng đề tài thuần tập, bác sĩ 16/11/2026 «Hãy hoàn thiện vấn đề giả lập»): bản nháp
`G7_A8_MANUSCRIPT_<mã>.md` mang ~40 dòng khung — biểu ngữ «DRAFT», khối hướng dẫn «> …», chú thích «*(ước tính: … từ)*»
ở tiêu đề mục, dòng «*(Xem …)*», bảng ước tính số từ, dòng «[BẢN NHÁP TỰ ĐỘNG — DRAFT G7]». G7-AUTO-05 (dùng chung bộ
quét `g8_quality_gate.manuscript_residues`) coi chúng là «chưa soạn» nên tác giả phải xoá tay từng dòng, dễ xoá nhầm
nội dung. Công cụ này gỡ ĐÚNG các dòng khung ấy.

Không gỡ: ô «[CẦN…]» (chỗ còn thiếu nội dung — phải điền), số liệu, trích dẫn, bảng checklist chuẩn báo cáo. 22/11/2026:
chấm LẠI trạng thái bảng kiểm theo K18 trên bản nộp (☑ chỉ khi K18 chấm đạt — `run_g7_auto.cap_nhat_bang_kiem_k18`).
Chạy khô mặc định; `--ap-dung` mới ghi (sao lưu `*.bak-<giờ>` trước). Sau khi gỡ: chạy lại
`g7_quality_gate.py --study <mã>`; bản thảo đổi ⇒ dấu xác nhận G7 (`dau_van_tay_chot`) phải chốt lại.

Dùng:
  python3 tools/go_khung_ban_thao_g7.py --study <mã> [--ap-dung]
Mã thoát: 0 xong (hoặc không còn khung) · 1 sau khi gỡ vẫn còn dòng «chưa soạn» (liệt kê) · 2 không thấy bản thảo.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

MUC_KHUNG = ("BẢNG ƯỚC TÍNH SỐ TỪ",)  # cả mục «## …» là khung
_DONG_CHU_THICH = re.compile(r"\s*\*[(\[][^\n]*[)\]]\*\s*")  # dòng chỉ gồm «*(…)*» hoặc «*[…]*»
_CHU_THICH_TIEU_DE = re.compile(r"\s*\*\((?:ước tính|điền thủ công|Bảng chép số)[^)]*\)\*")


def go_khung(van: str, tieu_de: Optional[str] = None) -> Tuple[str, int]:
    """(bản nộp, số dòng khung đã gỡ). `tieu_de` thay dòng «# A8 — BẢN THẢO IMRAD SKELETON …»."""
    ra: List[str] = []
    bo = 0
    trong_muc_khung = False
    for d in van.splitlines():
        if d.startswith("## "):
            trong_muc_khung = any(m in d for m in MUC_KHUNG)
        if (trong_muc_khung or d.lstrip().startswith(">") or _DONG_CHU_THICH.fullmatch(d)
                or "BẢN NHÁP TỰ ĐỘNG — DRAFT G7" in d):
            bo += 1
            continue
        if d.startswith("# A8"):
            d = f"# {tieu_de}" if tieu_de else re.sub(r"\s*\(DRAFT[^)]*\)", "", d).replace(" SKELETON", "")
            bo += 1
        moi = _CHU_THICH_TIEU_DE.sub("", d)
        if moi != d:
            bo += 1
        ra.append(moi)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(ra)).rstrip() + "\n", bo


def cham_lai_bang_kiem(van: str, out_dir: Path) -> Tuple[str, int]:
    """Chấm lại phụ lục bảng kiểm chuẩn báo cáo theo K18 trên bản nộp (22/11/2026, chiều — điều phối: «bảng kiểm tự
    đánh ☑ đã báo cáo mà không kiểm»). Trạng thái lúc sinh khung là của bản nháp (còn ô [CẦN]); sau khi tác giả điền ô,
    chỉ mục K18 chấm «dat» mới mang ☑. Không xác định được thiết kế hoặc thiếu mô-đun ⇒ giữ nguyên (0 dòng đổi)."""
    try:
        import gate_contract as GC  # noqa: PLC0415
        import run_g7_auto as G7  # noqa: PLC0415

        thiet_ke, _canh_bao = GC.resolve_design_code(out_dir)
        if not thiet_ke:
            return van, 0
        moi, doi = G7.cap_nhat_bang_kiem_k18(van, thiet_ke)
    except Exception:  # noqa: BLE001 — công cụ gỡ khung không được hỏng vì bước chấm phụ
        return van, 0
    return (moi if moi.endswith("\n") else moi + "\n"), doi


def con_chua_soan(van: str) -> List[str]:
    """Dòng mà bộ quét G7/G8 vẫn coi là chưa soạn sau khi gỡ khung (ô [CẦN…], vệt công cụ nội bộ)."""
    try:
        import g8_quality_gate as G8Q  # noqa: PLC0415

        return list(G8Q.manuscript_residues(van)) + [f"vệt: {v}" for v in G8Q.scan_internal_traces(van)]
    except ImportError:  # pragma: no cover
        return [d for d in van.splitlines() if "[CẦN" in d]


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Gỡ khung bản nháp khỏi bản thảo G7 (A8) — chạy khô mặc định.")
    ap.add_argument("--study", required=True)
    ap.add_argument("--ap-dung", action="store_true", help="ghi bản nộp (sao lưu bản cũ trước)")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    p = out_dir / f"G7_A8_MANUSCRIPT_{a.study}.md"
    if not p.is_file():
        print(f"✗ Không thấy {p.name}")
        return 2
    try:
        meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    van = p.read_text(encoding="utf-8")
    moi, bo = go_khung(van, meta.get("title") if isinstance(meta.get("title"), str) else None)
    moi, doi_bk = cham_lai_bang_kiem(moi, out_dir)
    con = con_chua_soan(moi)
    print(f"{'Đã gỡ' if a.ap_dung else 'Sẽ gỡ'} {bo} dòng khung bản nháp khỏi {p.name}.")
    print(f"{'Đã chấm lại' if a.ap_dung else 'Sẽ chấm lại'} {doi_bk} dòng bảng kiểm chuẩn báo cáo theo K18 "
          "(☑ chỉ khi K18 chấm đạt trên bản nộp).")
    if a.ap_dung and (bo or doi_bk):
        bak = p.with_name(f"{p.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(p, bak)
        p.write_text(moi, encoding="utf-8", newline="\n")
        print(f"  Sao lưu: {bak.name}. Chạy lại g7_quality_gate.py rồi chốt lại dấu xác nhận G7 (bản thảo đã đổi).")
    if con:
        print(f"⚠ Còn {len(con)} dòng chưa soạn (ô [CẦN…] phải điền — không phải khung):")
        for d in con[:20]:
            print(f"   - {d[:150]}")
        print("Cần bác sĩ kiểm chứng.")
        return 1
    print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
