#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BẤT BIẾN NEWLINE VÙNG CHUỖI-KÝ — bản nội-repo cho CI (16/08/2026).

Vì sao: chiến dịch CI 16/08 chứng minh `write_text(..., encoding="utf-8")` THIẾU
`newline="\\n"` trên Windows sinh CRLF → chuỗi «ký hash → sinh lại artifact» lệch
byte → `ledger_approved` fail (592 điểm đã chuẩn hoá). Luật R6 ở chốt workspace
(tools/kiem_tuong_thich_da_nen.py, thư mục mẹ) chỉ chạy trên MÁY BÁC SĨ — CI và
mọi máy khác đẩy code là mù. Bản này tự-chứa trong repo, chạy được ở CI đơn-repo.

Quét tools/ runtime/ tests/ scripts/ của CHÍNH repo này; che docstring/chú thích
(chống bắt lời-kể-về-lỗi); miễn trừ tường minh `# da-nen: bo-qua` kèm lý do.
Mã thoát: 0 sạch · 2 có vi phạm (CI đỏ). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO = Path(__file__).resolve().parents[1]
CAY = ("tools", "runtime", "tests", "scripts")
MIEN_TRU = "da-nen: bo-qua"
# khối write_text trọn vẹn (đa dòng, ngoặc lồng 1 mức) có encoding mà thiếu newline
MAU = re.compile(r'\.write_text\((?:[^()]|\([^()]*\))*?\)', re.S)


def _mask(dong: list[str]) -> list[str]:
    ra, trong, dau = [], False, ""
    for ln in dong:
        s = ln
        if trong:
            if dau in s:
                s = s.split(dau, 1)[1]
                trong = False
            else:
                ra.append("")
                continue
        if "#" in s:
            s = s.split("#", 1)[0]
        for d in ('"""', "'''"):
            while d in s:
                truoc, sau = s.split(d, 1)
                if d in sau:
                    s = truoc + sau.split(d, 1)[1]
                else:
                    s, trong, dau = truoc, True, d
                    break
        ra.append(s)
    return ra


def main() -> int:
    vi_pham: list[str] = []
    n = 0
    for cay in CAY:
        goc = REPO / cay
        if not goc.exists():
            continue
        for p in sorted(goc.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            n += 1
            goc = p.read_text(encoding="utf-8", errors="replace").splitlines()
            text = "\n".join(_mask(goc))
            for m in MAU.finditer(text):
                s = m.group(0)
                if 'encoding="utf-8"' not in s or "newline=" in s:
                    continue
                # miễn trừ phải soi trên DÒNG GỐC — _mask đã cắt chú thích,
                # nên tìm marker trong khối match (bản che) sẽ không bao giờ thấy
                d1 = text[:m.start()].count("\n")
                d2 = d1 + s.count("\n")
                if any(MIEN_TRU in goc[i] for i in range(d1, min(d2 + 1, len(goc)))):
                    continue
                vi_pham.append(f"{p.relative_to(REPO)}:{d1 + 1}")
    print(f"BẤT BIẾN NEWLINE VÙNG KÝ — quét {n} file / {len(CAY)} cây")
    for v in vi_pham:
        print(f"  🔴 {v} — write_text thiếu newline='\\n' (CRLF phá hash ký trên Windows)")
    if vi_pham:
        print(f"KẾT: 🔴 {len(vi_pham)} vi phạm — thêm newline='\\n' hoặc miễn trừ "
              f"`# {MIEN_TRU}` KÈM LÝ DO.")
        return 2
    print("KẾT: 🟢 0 vi phạm. Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
