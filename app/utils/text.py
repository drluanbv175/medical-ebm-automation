"""Làm sạch văn bản nguồn: gỡ thẻ XML/HTML có cấu trúc + giải mã ký tự HTML.

Nhiều abstract (PMC/EuropePMC/ClinicalTrials) chứa thẻ cấu trúc <sec>, <st>, <p>,
<abstracttext label="...">, <list>, và ký tự HTML như &ge; (≥), &le; (≤), &lt; (<).
Nếu KHÔNG làm sạch trước khi hiển thị/dịch/tách PICO thì:
- Giao diện hiện thẻ thô (vd "<sec><st>...").
- Dịch máy dịch luôn cả thẻ (vd "</sec>" -> "</giây>").
- Ký tự ≥/≤ hiện sai (vd "&ge;4").

Hàm dưới CHỈ định dạng/gỡ thẻ — KHÔNG thêm/sửa nội dung (giữ liêm chính).
"""
from __future__ import annotations

import html as _html
import re as _re

_I = _re.IGNORECASE

# Nhãn mục abstract có cấu trúc -> tiêu đề đọc được
_SEC_TITLE = _re.compile(r"<\s*(?:st|title)\s*>\s*", _I)
_SEC_TITLE_END = _re.compile(r"\s*<\s*/\s*(?:st|title)\s*>\s*", _I)
_ABSTRACT_LABEL = _re.compile(r'<\s*abstracttext\b[^>]*\blabel\s*=\s*"([^"]+)"[^>]*>', _I)
_BLOCK_BOUNDARY = _re.compile(r"<\s*/?\s*(?:sec|p|abstracttext|div|br|h[1-6])\s*/?\s*>", _I)
_LIST_ITEM = _re.compile(r"<\s*li(?:st-item)?\b[^>]*>\s*", _I)
# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 22, phát hiện #1):
# `<[^>]+>` khớp từ ký tự "<" ĐẦU TIÊN tới ký tự ">" GẦN NHẤT sau đó, bất kể
# nội dung ở giữa có phải là thẻ hay không. Nguồn JSON (openFDA/
# ClinicalTrials.gov v2/OpenAlex/Crossref) dùng "<"/">" literal cho SO SÁNH
# NGƯỠNG LÂM SÀNG ("eGFR <90 and >30 mL/min") — cực kỳ phổ biến trong
# eligibilityCriteria — bị hiểu nhầm là một cặp thẻ và bị XOÁ SẠCH, không
# exception, không log, làm sai lệch tiêu chí lâm sàng một cách ÂM THẦM.
# Một tên thẻ HTML/XML thật LUÔN bắt đầu bằng chữ cái ngay sau "<" (hoặc "/"
# cho thẻ đóng) — không bao giờ bắt đầu bằng chữ số/khoảng trắng-rồi-số như
# trong so sánh toán học. Thêm ràng buộc này để KHÔNG khớp "<90"/">30" mà
# vẫn khớp đúng mọi thẻ thật (<sec>, </sec>, <a href="...">, <br/>...).
_ANY_TAG = _re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")
_MULTISPACE = _re.compile(r"[ \t]+")
_SPACE_NL = _re.compile(r"[ \t]*\n[ \t]*")
_MULTINL = _re.compile(r"\n{3,}")

# Ký tự CJK (Trung/Nhật) — nhiều abstract tạp chí TQ là SONG NGỮ (Anh + Trung trùng lặp).
_CJK = _re.compile(r"[　-〿㐀-䶿一-鿿豈-﫿＀-￯]")
_CJK_PUNCT = _re.compile(r"[，。；：、？！（）【】「」『』〈〉《》·…]+")
_LATIN = _re.compile(r"[A-Za-z]")


def strip_secondary_cjk(text: str) -> str:
    """Nếu văn bản SONG NGỮ (có cả tiếng Anh đáng kể VÀ tiếng Trung) thì BỎ phần
    tiếng Trung (thường là bản trùng lặp) — tránh dịch máy rối/loạn (vd lặp
    'Bạn có thể làm được điều đó'). Nếu CHỈ có tiếng Trung thì giữ nguyên để dịch.
    """
    if not text:
        return text
    cjk = len(_CJK.findall(text))
    if not cjk:
        return text
    latin = len(_LATIN.findall(text))
    # Giữ nguyên nếu CHỦ YẾU tiếng Trung (ít tiếng Anh) -> để translator dịch ZH->VI.
    # Coi là SONG NGỮ (bỏ phần Trung) khi có lượng tiếng Anh đáng kể so với tiếng Trung.
    if latin < 60 or latin < 0.5 * cjk:
        return text
    t = _CJK.sub("", text)    # song ngữ -> bỏ phần Trung trùng lặp, giữ tiếng Anh
    t = _CJK_PUNCT.sub(" ", t)
    return t


def clean_text(text, structured: bool = True) -> str | None:
    """Trả về text sạch (gỡ thẻ + giải mã ký tự). None nếu đầu vào rỗng.

    structured=True: giữ cấu trúc abstract (mục -> tiêu đề + xuống dòng).
    structured=False: gỡ phẳng (dùng cho tiêu đề, tín hiệu ngắn).
    """
    if not text:
        return text
    t = str(text)
    if structured:
        # Nhãn <abstracttext label="BACKGROUND"> -> "\n\nBackground:\n"
        t = _ABSTRACT_LABEL.sub(lambda m: f"\n\n{m.group(1).strip().title()}:\n", t)
        # <st>Tiêu đề</st> / <title>...</title> -> "\n\nTiêu đề:\n"
        t = _SEC_TITLE.sub("\n\n", t)
        t = _SEC_TITLE_END.sub(":\n", t)
        # Danh sách -> bullet
        t = _LIST_ITEM.sub("\n• ", t)
        # Ranh giới khối -> xuống dòng
        t = _BLOCK_BOUNDARY.sub("\n", t)
    # Gỡ mọi thẻ còn lại (vd <a href="...">...</a> -> giữ phần chữ)
    t = _ANY_TAG.sub("", t)
    # Giải mã ký tự HTML: &ge;->≥, &le;->≤, &lt;-><, &amp;->&, &#x...; ...
    t = _html.unescape(t)
    # Abstract song ngữ TQ (Anh+Trung) -> bỏ phần Trung trùng lặp (tránh dịch rối)
    t = strip_secondary_cjk(t)
    # Dọn khoảng trắng
    t = _MULTISPACE.sub(" ", t)
    t = _SPACE_NL.sub("\n", t)
    t = _MULTINL.sub("\n\n", t)
    return t.strip()
