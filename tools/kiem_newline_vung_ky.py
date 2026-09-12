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


def _tim_loi_goi_write_text(text: str) -> list[tuple[int, int, str, str]]:
    """Tìm mọi lời gọi `.write_text(...)` trong `text` bằng cách ĐẾM NGOẶC THẬT
    (khớp mọi cấp lồng), thay cho regex cũ `\\.write_text\\((?:[^()]|\\([^()]*\\))*?\\)`
    vốn chỉ khớp được đúng 1 CẤP ngoặc lồng bên trong. Một lời gọi có ≥2 cấp
    lồng — vd `write_text(f(g(x)), encoding="utf-8")` — hoàn toàn KHÔNG được
    regex cũ tìm thấy (không phải khớp sai, mà là finditer() bỏ qua occurrence
    đó), nên vi phạm "thiếu newline=" thật ẩn trong lời gọi kiểu này lọt qua CI
    mà không có cảnh báo nào.

    Trả thêm `outer` — nội dung CHỈ ở cấp ngoài cùng của write_text() (nội dung
    bên trong mọi lời gọi lồng bên trong bị lược bỏ, chỉ giữ dấu ngoặc rỗng
    "()" đánh dấu vị trí). Bắt buộc phải tách riêng: nếu một hàm LỒNG BÊN
    TRONG (vd `src.read_text(encoding="utf-8", newline="\\n")`) tình cờ có
    kwarg `newline=`, kiểm tra "newline=" in <toàn bộ chuỗi khớp> sẽ SAI —
    nhận nhầm write_text() NGOÀI CÙNG là đã có newline= trong khi nó không hề
    có, y hệt bug thật đang tồn tại ở tools/vn_prose_style.py:218
    (`dst.write_text(clean_generated_prose(src.read_text(..., newline="\\n")),
    encoding="utf-8")` — outer write_text KHÔNG có newline=, chỉ inner
    read_text mới có). Luật kiểm vi phạm PHẢI soi trên `outer`, KHÔNG soi trên
    chuỗi khớp đầy đủ.

    Trả về (vị trí bắt đầu, vị trí kết thúc, chuỗi khớp đầy đủ, outer)."""
    ra: list[tuple[int, int, str, str]] = []
    tim = ".write_text("
    i = 0
    while True:
        idx = text.find(tim, i)
        if idx == -1:
            break
        j = idx + len(tim)
        depth = 1
        outer_chars: list[str] = []
        while j < len(text) and depth > 0:
            ch = text[j]
            if ch == "(":
                if depth == 1:
                    outer_chars.append("(")
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 1:
                    outer_chars.append(")")
            elif depth == 1:
                outer_chars.append(ch)
            j += 1
        ra.append((idx, j, text[idx:j], "".join(outer_chars)))
        i = j
    return ra


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
            for start, _end, s, outer in _tim_loi_goi_write_text(text):
                if 'encoding="utf-8"' not in outer or "newline=" in outer:
                    continue
                # miễn trừ phải soi trên DÒNG GỐC — _mask đã cắt chú thích,
                # nên tìm marker trong khối match (bản che) sẽ không bao giờ thấy
                d1 = text[:start].count("\n")
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
