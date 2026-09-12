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

import io
import re
import sys
import tokenize
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


_TIEN_TO_CHUOI_RE = re.compile(r"^[a-zA-Z]*")

# Python ≥3.12 (PEP 701) tách f-string thành 3 loại token FSTRING_START/
# MIDDLE/END thay vì MỘT token STRING duy nhất như <3.12. `getattr(...,
# None)` để tương thích ngược: trên <3.12 hai hằng số này không tồn tại,
# nhánh so sánh `tok.type == None` không bao giờ khớp một token type thật
# (luôn là số nguyên ≥0) nên nhánh FSTRING dưới đây tự động không chạy —
# đúng ý, vì trên <3.12 f-string đã là STRING token, được `_la_chuoi_ba_nhay`
# xử lý đủ rồi.
_FSTRING_START = getattr(tokenize, "FSTRING_START", None)
_FSTRING_END = getattr(tokenize, "FSTRING_END", None)


def _la_chuoi_ba_nhay(nguyen_van_token: str) -> bool:
    """True nếu token STRING là chuỗi BA NHÁY kiểu docstring (`'''...'''` hay
    `\"\"\"...\"\"\"`, có thể mang tiền tố r/b/f/u). Dùng để giữ NGUYÊN hành vi
    che docstring cũ (chống bắt lời-kể-về-lỗi khi chính file này, hay file
    khác, mô tả một lời gọi `write_text(...)` trong văn xuôi tài liệu) — còn
    chuỗi một/hai nháy (vd đối số thật của `write_text(...)`, hay giá trị
    `"utf-8"` của `encoding=`) thì GIỮ NGUYÊN VĂN, không che."""
    phan_con_lai = _TIEN_TO_CHUOI_RE.sub("", nguyen_van_token, count=1)
    return phan_con_lai.startswith('"""') or phan_con_lai.startswith("'''")


def _che_khoang(dong_ky_tu: list[list[str]], bd: tuple[int, int], kt: tuple[int, int]) -> None:
    """Thay ký tự trong khoảng [bd, kt) (toạ độ (dòng 1-based, cột 0-based)
    của `tokenize`) bằng khoảng trắng, KHÔNG xoá — giữ nguyên số dòng và độ
    dài từng dòng để vị trí tính bằng `text.count("\\n")` ở nơi gọi
    (`main()`) không bị lệch so với `goc` (danh sách dòng GỐC chưa che)."""
    (dong_dau, cot_dau), (dong_cuoi, cot_cuoi) = bd, kt
    for so_dong in range(dong_dau, dong_cuoi + 1):
        idx = so_dong - 1
        if not (0 <= idx < len(dong_ky_tu)):
            continue
        ky_tu = dong_ky_tu[idx]
        c0 = cot_dau if so_dong == dong_dau else 0
        c1 = cot_cuoi if so_dong == dong_cuoi else len(ky_tu)
        for k in range(c0, min(c1, len(ky_tu))):
            ky_tu[k] = " "


def _mask_ngay_tho(dong: list[str]) -> list[str]:
    """Bản CŨ (che theo ký tự, cắt tại '#' ĐẦU TIÊN trên dòng) — CHỈ dùng khi
    `tokenize` không đọc được văn bản (file lỗi cú pháp Python), còn hơn
    không che gì cả. KHÔNG dùng cho đường đi bình thường: nó chính là nguồn
    của bug đã vá — cắt nhầm tại '#' NẰM TRONG một string literal (vd
    `.write_text("# Script phân tích\\n(placeholder)\\n", encoding="utf-8")`),
    làm mất luôn phần `encoding=`/`newline=` phía sau TRÊN CÙNG một dòng và
    gộp nhiều lời gọi `write_text()` liên tiếp thành một match rác duy nhất."""
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


def _mask(dong: list[str]) -> list[str]:
    """Che COMMENT thật và nội dung chuỗi BA NHÁY (docstring-style) bằng
    `tokenize` chuẩn của Python — thay cho bản cũ (`_mask_ngay_tho`) vốn cắt
    tại ký tự '#' ĐẦU TIÊN trên mỗi dòng mà không phân biệt được đó là mở đầu
    một comment thật hay chỉ là một ký tự '#' NẰM BÊN TRONG một string
    literal.

    Bằng chứng thực nghiệm (không phải giả định): với
    `.write_text("# Script phân tích\\n(placeholder)\\n", encoding="utf-8",
    newline="\\n")` theo sau bởi một `write_text(...)` khác THIẾU
    `newline=`, bản cũ cắt cụt dòng đầu ngay tại '#' trong chuỗi, làm mất
    dấu ngoặc đóng và mọi ký tự phía sau trên cùng dòng — kết quả là
    `_tim_loi_goi_write_text()` gộp CẢ HAI lời gọi thành một match duy nhất
    và mất luôn khả năng thấy `encoding="utf-8"` của lời gọi thứ hai, khiến
    vi phạm THẬT (thiếu `newline=`) trở nên vô hình.

    `tokenize` là chính bộ phân tích cú pháp Python dùng để biên dịch, nên nó
    KHÔNG BAO GIỜ nhầm '#' trong một string literal (một/hai/ba nháy, kể cả
    f-string) là một COMMENT token — phân biệt này đúng bởi thiết kế, không
    phải suy đoán bằng regex/quét ký tự.

    F-STRING BA NHÁY (vd `f\"\"\"...{x}...\"\"\"`) cần xử lý RIÊNG: từ Python
    3.12 (PEP 701), `tokenize` tách một f-string thành CHUỖI token
    FSTRING_START/FSTRING_MIDDLE/(token biểu thức lồng bên trong `{...}`)/
    FSTRING_END, KHÔNG còn là MỘT token STRING duy nhất như <3.12 — nên nếu
    chỉ gác cửa bằng `tok.type == tokenize.STRING`, một f-string ba nháy trên
    3.12+ sẽ hoàn toàn KHÔNG được che (bản cũ `_mask_ngay_tho` che được, vì
    nó quét ký tự `'''`/`\"\"\"` bất kể tiền tố), tạo hồi quy tuỳ phiên bản
    Python — đã bắt được thực nghiệm bằng cách chạy trên cả Python 3.9 (chưa
    có PEP 701, vẫn 1 token STRING, được che đúng) lẫn 3.14 (đã có PEP 701,
    KHÔNG được che nếu thiếu nhánh riêng này). Đoạn dưới dò cặp
    FSTRING_START…FSTRING_END (có đếm ĐỘ SÂU lồng, vì f-string có thể lồng
    f-string khác bên trong biểu thức `{...}`) rồi che TRỌN khoảng đó, y hệt
    cách chuỗi ba nháy thường được che.

    CHỈ che token COMMENT và token STRING dạng BA NHÁY (giữ đúng hành vi
    docstring-masking cũ, chống bắt lời-kể-về-lỗi). Chuỗi một/hai nháy —
    kể cả chuỗi chứa '#' như ví dụ trên, hay giá trị `"utf-8"` của
    `encoding=` — được GIỮ NGUYÊN VĂN: `_tim_loi_goi_write_text()` so khớp
    trực tiếp `'encoding="utf-8"' in outer` trên chính văn bản gốc, che luôn
    những chuỗi đó sẽ xoá mất chữ cần so khớp và làm chốt câm hoàn toàn.

    Chỉ THAY ký tự bị che bằng khoảng trắng (không xoá, không nối dòng) để
    giữ nguyên số dòng — nơi gọi (`main()`) tính vị trí bằng
    `text[:start].count("\\n")` trên `text = "\\n".join(_mask(goc))`, lệch số
    dòng ở đây sẽ làm sai luôn cả việc tra miễn trừ `# da-nen: bo-qua` lẫn
    số dòng báo cáo."""
    nguon = "\n".join(dong)
    dong_ky_tu = [list(ln) for ln in dong]
    try:
        cac_token = list(tokenize.generate_tokens(io.StringIO(nguon).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError) as loi:
        print(
            f"⚠️  _mask: tokenize thất bại ({loi!r}) — dùng chế độ dự phòng "
            "ngây thơ (kém chính xác hơn) cho file này.",
            file=sys.stderr,
        )
        return _mask_ngay_tho(dong)

    so_token = len(cac_token)
    i = 0
    while i < so_token:
        tok = cac_token[i]
        if tok.type == tokenize.COMMENT:
            _che_khoang(dong_ky_tu, tok.start, tok.end)
            i += 1
            continue
        if tok.type == tokenize.STRING and _la_chuoi_ba_nhay(tok.string):
            _che_khoang(dong_ky_tu, tok.start, tok.end)
            i += 1
            continue
        if (
            _FSTRING_START is not None
            and tok.type == _FSTRING_START
            and _la_chuoi_ba_nhay(tok.string)
        ):
            # F-string ba nháy (PEP 701, Python 3.12+) — dò tới FSTRING_END
            # KHỚP (đếm độ sâu, vì có thể lồng f-string khác bên trong biểu
            # thức `{...}`), che TRỌN từ FSTRING_START tới FSTRING_END đó.
            do_sau = 1
            j = i + 1
            ket_thuc = tok.end
            while j < so_token and do_sau > 0:
                tk = cac_token[j]
                if tk.type == _FSTRING_START:
                    do_sau += 1
                elif tk.type == _FSTRING_END:
                    do_sau -= 1
                ket_thuc = tk.end
                j += 1
            _che_khoang(dong_ky_tu, tok.start, ket_thuc)
            i = j
            continue
        i += 1

    return ["".join(ky_tu) for ky_tu in dong_ky_tu]


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
