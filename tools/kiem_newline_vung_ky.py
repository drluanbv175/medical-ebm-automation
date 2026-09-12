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


def _dung_offset_dong_cot(text: str):
    """Trả về hàm đổi toạ độ `tokenize` (dòng 1-based, cột 0-based) thành
    offset ký tự tuyệt đối trong `text`. `text` LUÔN được dựng bằng
    `"\\n".join(...)` (xem `_mask()`/`main()`), nên tách lại bằng
    `text.split("\\n")` khớp CHÍNH XÁC ranh giới dòng gốc, không lệch."""
    dong = text.split("\n")
    bat_dau: list[int] = [0]
    for ln in dong:
        bat_dau.append(bat_dau[-1] + len(ln) + 1)

    def doi(vi_tri: tuple[int, int]) -> int:
        dong_so, cot = vi_tri
        return bat_dau[dong_so - 1] + cot

    return doi


def _tim_loi_goi_write_text_ngay_tho(text: str) -> list[tuple[int, int, str, str]]:
    """Bản CŨ — ĐẾM NGOẶC THEO KÝ TỰ THÔ trên `text`. CHỈ dùng khi `text`
    không tokenize được (file đã lỗi cú pháp từ trước khiến `_mask()` phải
    hạ về `_mask_ngay_tho`, xem `_tim_loi_goi_write_text()`) — còn hơn không
    quét được gì cho một file đã hỏng cú pháp.

    KHÔNG dùng cho đường đi bình thường: đây CHÍNH LÀ nguồn của bug đã vá ở
    bản tokenize-hoá bên dưới — một dấu '(' NẰM BÊN TRONG một chuỗi (string
    literal) bị đếm y hệt một dấu '(' mở lời gọi lồng thật, đẩy `depth` lố
    một cấp cho phần còn lại của lời gọi. Ca cụ thể (bằng chứng thực
    nghiệm, không phải giả định — xác nhận qua ba lượt rà độc lập trong một
    Workflow đối kháng khi kiểm một thay đổi khác):
    `dst.write_text(clean(src.read_text(x, "see foo(bar")), encoding="utf-8",
    newline="\\n")` — dấu '(' trong chuỗi `"see foo(bar"` làm `encoding=` và
    `newline=` phía sau — vốn ở CẤP NGOÀI CÙNG thật sự của `write_text()` —
    bị đếm nhầm là nằm trong lời gọi lồng bên trong, nên `outer` mất cả hai
    kwarg đó dù `write_text()` NGOÀI CÙNG thật sự thiếu `newline=`: vi phạm
    thật trở nên vô hình (false negative), ngược hướng an toàn của một
    checker sinh ra để KHÔNG được bỏ sót loại vi phạm này."""
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


def _tim_loi_goi_write_text(text: str) -> list[tuple[int, int, str, str]]:
    """Tìm mọi lời gọi `.write_text(...)` trong `text` bằng `tokenize` —
    cùng module chuẩn của Python mà `_mask()` đã dùng — thay cho việc ĐẾM
    NGOẶC THEO KÝ TỰ THÔ (nay là `_tim_loi_goi_write_text_ngay_tho()`, chỉ
    còn dùng làm dự phòng, xem docstring hàm đó để biết ca lỗi cụ thể).

    VÌ SAO ĐẾM KÝ TỰ THÔ KHÔNG ĐỦ (bug đã vá, phát hiện qua ba lượt rà độc
    lập trong một Workflow đối kháng kiểm một thay đổi khác): nếu một đối
    số CHUỖI của một lời gọi LỒNG BÊN TRONG chứa một dấu '(' không cân —
    vd `dst.write_text(clean(src.read_text(x, "see foo(bar")),
    encoding="utf-8", newline="\\n")` — bộ đếm ký tự thô không phân biệt
    được dấu '(' đó với một dấu '(' MỞ LỜI GỌI LỒNG THẬT, nên `depth` bị
    đẩy lố một cấp cho toàn bộ phần còn lại của lời gọi: `encoding=` và
    `newline=` phía sau (vốn ở đúng CẤP NGOÀI CÙNG của `write_text()`) bị
    coi là nằm trong lời gọi lồng, khiến `outer` mất cả hai — vi phạm thật
    (thiếu `newline=` ở `write_text()` ngoài cùng) trở nên vô hình, đúng
    chiều NGUY HIỂM nhất cho một checker sinh ra để không được bỏ sót loại
    vi phạm này.

    `tokenize` khớp mọi cấp ngoặc lồng bằng cách chỉ đếm token OP `(`/`)` —
    một dấu '(' bên trong một STRING token KHÔNG BAO GIỜ là một OP token
    riêng (nó chỉ là một phần nội dung nguyên văn của MỘT token STRING duy
    nhất), nên không thể bị fooled theo cách bộ đếm ký tự thô mắc phải —
    đúng NGUYÊN TẮC `_mask()` đã dùng để phân biệt '#' trong comment thật
    với '#' nằm trong string literal (xem docstring `_mask()` ở trên).

    Trả thêm `outer` — nội dung CHỈ ở cấp ngoài cùng của write_text() (nội
    dung bên trong mọi lời gọi lồng bên trong bị lược bỏ, chỉ giữ dấu ngoặc
    "()" đánh dấu vị trí, ghép trực tiếp từ `tok.string` của từng token ở
    cấp ngoài cùng — không chèn khoảng trắng giữa các token, vì luật kiểm ở
    `main()` so khớp CHÍNH XÁC chuỗi con `'encoding="utf-8"'`/`"newline="`
    liền nhau như trong mã nguồn thật; chèn khoảng trắng sẽ làm gãy phép so
    khớp đó). Lý do bắt buộc tách `outer` khỏi chuỗi khớp đầy đủ: xem
    `TestNewlineTrongLoiGoiLongKhongDuocTinhChoOuterCall` ở
    tests/test_kiem_newline_vung_ky_workflow_20260905_vong24_nested_write_text.py.

    Trả về (vị trí bắt đầu, vị trí kết thúc, chuỗi khớp đầy đủ, outer). Nếu
    `text` không tokenize được (chỉ xảy ra khi `_mask()` đã phải hạ về
    `_mask_ngay_tho` cho một file lỗi cú pháp từ trước), hạ về
    `_tim_loi_goi_write_text_ngay_tho()` — còn hơn không quét được gì."""
    try:
        cac_token = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return _tim_loi_goi_write_text_ngay_tho(text)

    doi = _dung_offset_dong_cot(text)
    ra: list[tuple[int, int, str, str]] = []
    so_token = len(cac_token)
    i = 0
    while i < so_token - 2:
        tok_cham, tok_ten, tok_ngoac = cac_token[i], cac_token[i + 1], cac_token[i + 2]
        la_loi_goi_write_text = (
            tok_cham.type == tokenize.OP and tok_cham.string == "."
            and tok_ten.type == tokenize.NAME and tok_ten.string == "write_text"
            and tok_ngoac.type == tokenize.OP and tok_ngoac.string == "("
        )
        if not la_loi_goi_write_text:
            i += 1
            continue

        start = doi(tok_cham.start)
        end = doi(tok_ngoac.end)  # dự phòng nếu không tìm được ngoặc đóng khớp
        depth = 1
        outer_chars: list[str] = []
        j = i + 3
        while j < so_token and depth > 0:
            tok = cac_token[j]
            if tok.type == tokenize.OP and tok.string == "(":
                if depth == 1:
                    outer_chars.append("(")
                depth += 1
            elif tok.type == tokenize.OP and tok.string == ")":
                depth -= 1
                if depth == 1:
                    outer_chars.append(")")
                if depth == 0:
                    end = doi(tok.end)
            elif depth == 1:
                outer_chars.append(tok.string)
            j += 1
        ra.append((start, end, text[start:end], "".join(outer_chars)))
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
