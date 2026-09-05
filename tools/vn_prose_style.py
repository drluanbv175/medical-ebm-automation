#!/usr/bin/env python3
"""Chuẩn hoá VĂN PHONG tài liệu nghiên cứu tiếng Việt do hệ sinh ra.

VÌ SAO CÓ MODULE NÀY (2026-07-31)
----------------------------------
Đề cương C1a đã được làm sạch dấu vết văn phong máy, nhưng các artifact do cổng
G0–G4 sinh ra thì chưa: riêng hồ sơ đạo đức G2 còn 99 dấu gạch dài đang làm dấu
ngắt câu và 17 dòng phân cách bằng ký tự vẽ khung. Hai tài liệu này (hồ sơ IRB và
SAP) là thứ THẬT SỰ in ra để nộp Hội đồng và để ký, nên chúng phải đọc như văn
bản khoa học do người viết, không phải kết xuất máy.

Logic ở đây là bản đã kiểm chứng khi làm sạch đề cương: điểm mấu chốt là dấu `—`
trong tài liệu nghiên cứu mang HAI nghĩa hoàn toàn khác nhau, và chỉ được đụng
vào một nghĩa:

  * dấu ngắt câu kiểu máy   → thay bằng dấu câu tiếng Việt (bỏ)
  * ô trống chờ điền số liệu → "n = —", "— ± —", "— (—; —)" (GIỮ TUYỆT ĐỐI)

Phân biệt bằng ngữ cảnh chữ cái: dấu ngắt câu luôn có chữ ở ít nhất một phía;
dấu không có chữ ở cả hai phía là chỗ trống chờ điền.

PHẠM VI CỐ Ý HẸP: chỉ đổi DẤU CÂU và ký tự trình bày. Không đổi một chữ nào của
nội dung khoa học, không đụng số liệu, PMID/DOI hay bảng.
"""

from __future__ import annotations

import re

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

__all__ = ["clean_generated_prose"]

_LETTER = re.compile(r"[A-Za-zÀ-ỹ]")
_SKIP = " \t*_`[\""
_LOOK = 5

# Cụm mở đầu vế sau quyết định dấu câu nào nghe tự nhiên trong tiếng Việt.
_APPOSITIVE = ("một ", "nơi ", "cụ thể là", "tức là", "nghĩa là", "trong đó",
               "gồm ", "bao gồm", "kể cả")
_CONTRAST = ("không phải", "chứ không", "khác với", "thay vì", "không còn")
_CROSSREF = ("mục ", "xem ", "phụ lục", "bảng ", "chi tiết ", "theo ", "đối chiếu")
_CAUSAL = ("vì ", "do ", "nên ", "bởi ", "để ", "nhằm ")

# Ký tự vẽ khung: hợp với terminal, không hợp văn bản trình Hội đồng.
_BOX_LINE = re.compile(r"^\s*[═━─╌]{3,}\s*$")
_BOX_EDGE = re.compile(r"[║│╔╗╚╝╠╣╦╩╬┌┐└┘├┤┬┴┼]")

_SYMBOL_WORDS = {
    "✅": "", "❌": "", "🔴": "", "🟡": "", "🟢": "",
    "⚠️": "LƯU Ý:", "⚠": "LƯU Ý:", "📋": "", "📄": "", "🛡️": "", "💾": "",
    "🔍": "", "⚖️": "", "📁": "", "📝": "", "🧭": "", "🔢": "", "🧾": "", "📊": "",
}


def _has_letter_near(text: str, pos: int, step: int) -> bool:
    i = pos + step
    for _ in range(_LOOK):
        if not (0 <= i < len(text)):
            return False
        if text[i] not in _SKIP:
            return bool(_LETTER.match(text[i]))
        i += step
    return False


# Nhãn trạng thái là CHỈ DẪN cho người điền và là HỢP ĐỒNG máy đọc: approve_gate
# và các quality gate dò đúng chuỗi này để biết mục nào chưa điền, còn bộ test
# thay thế chúng theo chuỗi chính xác. Sửa dấu câu bên trong nhãn sẽ vừa làm hỏng
# chốt chặn trước khi ký, vừa không đem lại lợi ích văn phong nào.
_STATUS_LABEL = re.compile(
    r"\[(?:CẦN|ĐÃ|DỰ THẢO|BẢN NHÁP|LƯU Ý|TÊN ĐƠN VỊ|ref)[^\]]*\]", re.IGNORECASE
)


def _mask_placeholders(text: str) -> tuple[str, list[str]]:
    kept: list[str] = []

    def hide(m: re.Match) -> str:
        kept.append(m.group())
        return f"\x00{len(kept) - 1}\x00"

    text = _STATUS_LABEL.sub(hide, text)

    out = []
    for i, ch in enumerate(text):
        if ch == "—" and not _has_letter_near(text, i, -1) and not _has_letter_near(text, i, 1):
            kept.append(ch)
            out.append(f"\x00{len(kept) - 1}\x00")
        else:
            out.append(ch)
    return "".join(out), kept


def _unmask(text: str, kept: list[str]) -> str:
    for i, val in enumerate(kept):
        text = text.replace(f"\x00{i}\x00", val)
    return text


def _pick_separator(before: str, after: str) -> str:
    tail = after.lstrip()
    low = tail.lower()
    if re.search(r"(Phần|Bước|Giai đoạn|Vòng|Chương|Mục|Tài liệu|TÀI LIỆU)\s+\d+\s*$", before):
        return ". "
    if before.count("**") % 2 == 1:
        return ", "
    in_paren = before.count("(") > before.count(")")
    if low.startswith(_CROSSREF):
        return ", " if in_paren else " ("
    if low.startswith(_CONTRAST) or low.startswith(_APPOSITIVE) or low.startswith(_CAUSAL):
        return ", "
    if (
        len(tail) > 70
        and not in_paren
        and not before.rstrip().endswith((",", ";", ":", ")"))
    ):
        return ". "
    return ", "


def _fix_dashes(line: str) -> str:
    is_table = line.lstrip().startswith("|")
    line, kept = _mask_placeholders(line)

    if is_table:
        cells = line.split("|")
        for idx, cell in enumerate(cells):
            if "—" not in cell:
                continue
            if not re.search(r"[A-Za-zÀ-ỹ0-9]", cell.replace("X", "")):
                continue
            cells[idx] = re.sub(r"\s*—\s*", ", ", cell).replace(", ,", ",")
        return _unmask("|".join(cells), kept)

    line = re.sub(r"^(\s*)—\s+", r"\1- ", line)

    out: list[str] = []
    i = 0
    while True:
        m = re.search(r"\s*—\s*", line[i:])
        if not m:
            out.append(line[i:])
            break
        start, end = i + m.start(), i + m.end()
        before = "".join(out) + line[i:start]
        sep = _pick_separator(before, line[end:])
        out.append(line[i:start])
        if sep == ". ":
            tail = line[end:]
            line = line[:end] + tail[:1].upper() + tail[1:]
        elif sep == " (":
            tail = line[end:]
            close = re.search(r"(?=[.,;]|$)", tail)
            pos = close.start() if close else len(tail)
            line = line[:end] + tail[:pos] + ")" + tail[pos:]
        out.append(sep)
        i = end
    line = "".join(out)

    line = line.replace("bệnh–chứng", "bệnh chứng")
    line = re.sub(r"\s–\s(?=[a-zàáâãèéêìíòóôõùúýăđĩũơưạ-ỹ])", ", ", line)
    line = re.sub(r"(?<=[)\d])\s–\s(?=[A-ZÀ-Ỹ])", ", ", line)

    line = re.sub(r",\s*,", ",", line)
    line = re.sub(r",\s*\.", ".", line)
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line)
    line = re.sub(r"\(\)", "", line)
    # Gộp khoảng trắng thừa GIỮA dòng, nhưng giữ nguyên phần đuôi: hai dấu cách
    # cuối dòng là DẤU XUỐNG DÒNG của markdown, xoá đi sẽ dính dòng khi render.
    _trailing = len(line) - len(line.rstrip(" "))
    line = re.sub(r" {2,}", " ", line.rstrip(" ")) + " " * _trailing
    return _unmask(line, kept)


def clean_generated_prose(text: str, *, keep_box: bool = False) -> str:
    """Làm sạch văn phong máy khỏi một artifact đã sinh.

    keep_box=True giữ nguyên khung vẽ (dùng cho khối có chủ đích như giấy chứng
    nhận khóa SAP, nơi khung đóng vai con dấu).
    """
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        if not keep_box:
            if _BOX_LINE.match(line):
                out.append("---")
                continue
            line = _BOX_EDGE.sub("", line)
        for sym, word in _SYMBOL_WORDS.items():
            if sym in line:
                line = line.replace(sym, word)
        line = _fix_dashes(line)
        out.append(line)
    # Gộp các đường kẻ liên tiếp thành một.
    merged: list[str] = []
    for line in out:
        if line.strip() == "---" and merged and merged[-1].strip() == "---":
            continue
        merged.append(line)
    return "\n".join(merged)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    dst.write_text(clean_generated_prose(src.read_text(encoding="utf-8", newline="\n")), encoding="utf-8", newline="\n")
    print(f"Đã làm sạch văn phong: {dst}")
