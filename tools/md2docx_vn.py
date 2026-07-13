#!/usr/bin/env python3
"""Chuyển Markdown -> Word (.docx) theo chuẩn trình bày LUẬN VĂN/ĐỀ CƯƠNG Việt Nam.

Dùng chung cho mọi cổng pipeline và cho G10 (assembler). Đặc điểm:
- Font Times New Roman, cỡ 13pt thân bài, cách dòng 1.5, căn đều (justify).
- Tiêu đề '# ' (H1) tự sang trang mới, căn giữa (dùng cho Chương/Phần lớn).
- Bảng Markdown (dạng `| ... |`) -> BẢNG WORD thật (không phải text).
- Công thức `$$...$$` -> dòng căn giữa, dọn ký hiệu LaTeX cơ bản.
- Tô ĐẬM + nghiêng mọi nhãn trạng thái skill ([CẦN...], [ĐÃ...], [DỰ THẢO]...)
  để bác sĩ thấy ngay chỗ cần điền.
- Trang bìa TUỲ CHỌN (title_page dict) — không cứng hoá cho một đề tài nào.

Yêu cầu: python-docx (`pip install python-docx`). Nếu thiếu, convert() ném
ImportError để caller tự xử lý (vd bỏ qua bước .docx như các cổng khác).

API chính:
    convert_markdown_file(md_path, out_path, title_page=None) -> Path
    markdown_to_docx(md_text, out_path, title_page=None) -> Path
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

FONT = "Times New Roman"
BODY_PT = 13
TABLE_PT = 11
TABLE_HEADER_FILL = "D9EAF7"
CONTENT_WIDTH_TWIPS = 9072  # A4 21 cm - lề trái 3 cm - lề phải 2 cm.

# Regex tách inline: **đậm** / *nghiêng* / [nhãn ...]
_INLINE_RE = re.compile(r"(\*\*.+?\*\*|\*[^*].*?\*|\[[^\]]+\])")
# Nhãn cần tô nổi bật (đầu chuỗi trong ngoặc vuông).
_HIGHLIGHT_PREFIXES = ("CẦN", "ĐÃ", "DỰ THẢO", "CHƯA", "KHOÁ", "KHÓA")


def _looks_like_flag(bracket_text: str) -> bool:
    """[CẦN...], [ĐÃ CUNG CẤP], [DỰ THẢO], [CẦN KIỂM CHỨNG...] -> True."""
    inner = bracket_text.strip("[]").strip().upper()
    return any(inner.startswith(p) for p in _HIGHLIGHT_PREFIXES)


def _set_run_font(run, size=BODY_PT, bold=False, italic=False):
    """Ép font Times New Roman (kể cả eastAsia) cho 1 run."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)


def _set_fixed_table_layout(table):
    """Cố định layout bảng để mở bằng Word/LibreOffice không bị co giãn khó đọc."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")


def _set_cell_width(cell, width_twips: int):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_twips))
    tc_w.set(qn("w:type"), "dxa")


def _set_cell_margins(cell, margin=108):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn("w:tcMar"))
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side in ("top", "left", "bottom", "right"):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(margin))
        node.set(qn("w:type"), "dxa")


def _set_cell_shading(cell, fill=TABLE_HEADER_FILL):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def _repeat_header_row(row):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = tr_pr.find(qn("w:tblHeader"))
    if tbl_header is None:
        tbl_header = OxmlElement("w:tblHeader")
        tr_pr.append(tbl_header)
    tbl_header.set(qn("w:val"), "true")


def _add_page_number(paragraph):
    """Thêm số trang dạng field PAGE để Word tự cập nhật khi mở tài liệu."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH as A
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    _spacing(paragraph, before=0, after=0, line=1.0, align=A.CENTER)
    _set_run_font(paragraph.add_run("Trang "), size=10)
    run = paragraph.add_run()
    _set_run_font(run, size=10)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(end)


def _add_inline_runs(paragraph, text, size=BODY_PT, bold=False, italic=False):
    """Thêm run vào paragraph, xử lý **đậm**/*nghiêng*/[nhãn] (nhãn -> đậm+nghiêng)."""
    for part in _INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            _set_run_font(paragraph.add_run(part[2:-2]), size, bold=True, italic=italic)
        elif part.startswith("[") and part.endswith("]") and _looks_like_flag(part):
            _set_run_font(paragraph.add_run(part), size, bold=True, italic=True)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            _set_run_font(paragraph.add_run(part[1:-1]), size, bold=bold, italic=True)
        else:
            _set_run_font(paragraph.add_run(part), size, bold=bold, italic=italic)


def _spacing(paragraph, before=0, after=8, line=1.5, align=None):
    from docx.enum.text import WD_LINE_SPACING
    pf = paragraph.paragraph_format
    pf.space_before = _pt(before)
    pf.space_after = _pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line
    if align is not None:
        paragraph.alignment = align


def _pt(v):
    from docx.shared import Pt
    return Pt(v)


def _page_break(doc):
    from docx.enum.text import WD_BREAK
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def _strip_md(text: str) -> str:
    """Bỏ ký hiệu **...** để dùng cho tiêu đề (giữ chữ)."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def _clean_formula(text: str) -> str:
    text = text.strip()
    if text.startswith("$$") and text.endswith("$$"):
        text = text[2:-2]
    subs = [
        (r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1) / (\2)"),
        (r"\\times", "×"), (r"\\cdot", "·"), (r"\\alpha", "α"),
        (r"\\approx", "≈"), (r"_\{([^{}]+)\}", r"_\1"), (r"\\%", "%"),
    ]
    for pat, rep in subs:
        text = re.sub(pat, rep, text)
    return text.replace("{", "").replace("}", "").strip()


def _parse_table(lines: List[str], start: int):
    """lines[start] là dòng header bảng; trả (rows, chỉ_số_kế_tiếp)."""
    header = [c.strip() for c in lines[start].strip().strip("|").split("|")]
    idx = start + 2  # bỏ dòng phân cách |---|
    rows = [header]
    while idx < len(lines) and lines[idx].strip().startswith("|"):
        rows.append([c.strip() for c in lines[idx].strip().strip("|").split("|")])
        idx += 1
    return rows, idx


def _add_table(doc, rows):
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH as A

    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_fixed_table_layout(table)
    try:
        table.style = "Table Grid"
    except KeyError:
        pass
    col_width = max(900, CONTENT_WIDTH_TWIPS // max(1, ncols))
    if table.rows:
        _repeat_header_row(table.rows[0])
    for r, row in enumerate(rows):
        for c in range(ncols):
            cell = table.cell(r, c)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            _set_cell_width(cell, col_width)
            _set_cell_margins(cell)
            if r == 0:
                _set_cell_shading(cell)
            cell.paragraphs[0].text = ""
            p = cell.paragraphs[0]
            _spacing(p, before=2, after=2, line=1.15,
                     align=A.CENTER if r == 0 else A.JUSTIFY)
            _add_inline_runs(p, row[c] if c < len(row) else "",
                             size=TABLE_PT, bold=(r == 0))
    return table


def _render_title_page(doc, tp: Dict):
    """Sinh trang bìa từ dict title_page. Mọi trường tuỳ chọn."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH as A

    def line(text, size, bold=True, after=6, align=A.CENTER):
        p = doc.add_paragraph()
        _spacing(p, before=0, after=after, line=1.3, align=align)
        _set_run_font(p.add_run(text), size, bold=bold)

    for org in tp.get("org_lines", []):
        line(org, 14)
    for _ in range(tp.get("gap_before_title", 4)):
        doc.add_paragraph()
    if tp.get("doc_type"):
        line(tp["doc_type"], 22, after=20)
    if tp.get("title"):
        line(tp["title"], 18, after=30)
    for _ in range(2):
        doc.add_paragraph()
    for meta in tp.get("meta_lines", []):
        p = doc.add_paragraph()
        _spacing(p, align=A.CENTER, line=1.5)
        _add_inline_runs(p, meta, size=BODY_PT, bold=meta.strip().startswith("**"))
    for _ in range(3):
        doc.add_paragraph()
    if tp.get("place_year"):
        line(tp["place_year"], BODY_PT, bold=False)
    _page_break(doc)


def _init_document(title_page: Optional[Dict]):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(3.0)     # gáy trái rộng theo chuẩn luận văn VN
    sec.right_margin = Cm(2.0)
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    _add_page_number(sec.footer.paragraphs[0])

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = _pt(BODY_PT)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)

    if title_page:
        _render_title_page(doc, title_page)
    return doc


def markdown_to_docx(md_text: str, out_path, title_page: Optional[Dict] = None):
    """Chuyển chuỗi Markdown -> .docx. Trả về Path đã lưu.

    md_text: nội dung markdown (KHÔNG gồm trang bìa — trang bìa qua title_page).
    out_path: đường dẫn .docx.
    title_page: dict tuỳ chọn (org_lines, doc_type, title, meta_lines, place_year).
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH as A
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    out_path = Path(out_path)
    doc = _init_document(title_page)
    lines = md_text.split("\n")

    i = 0
    first_h1 = True
    while i < len(lines):
        stripped = lines[i].strip()

        if stripped in ("", "---", "```markdown", "```"):
            i += 1
            continue

        # Blockquote (ghi chú) -> đoạn nghiêng, thụt lề 2 bên.
        if stripped.startswith("> "):
            p = doc.add_paragraph()
            _spacing(p, before=6, after=10, line=1.3, align=A.JUSTIFY)
            _add_inline_runs(p, stripped[2:], size=TABLE_PT, italic=True)
            ppr = p._element.get_or_add_pPr()
            ind = OxmlElement("w:ind")
            ind.set(qn("w:left"), "567")
            ind.set(qn("w:right"), "567")
            ppr.append(ind)
            i += 1
            continue

        if stripped.startswith("### "):
            p = doc.add_paragraph()
            _spacing(p, before=10, after=6, line=1.3)
            _set_run_font(p.add_run(_strip_md(stripped[4:])), BODY_PT, bold=True, italic=True)
            i += 1
            continue

        if stripped.startswith("## "):
            p = doc.add_paragraph()
            _spacing(p, before=14, after=8, line=1.3)
            _set_run_font(p.add_run(_strip_md(stripped[3:])), 14, bold=True)
            i += 1
            continue

        if stripped.startswith("# "):
            if not first_h1:
                _page_break(doc)
            first_h1 = False
            p = doc.add_paragraph()
            _spacing(p, before=0, after=16, line=1.3, align=A.CENTER)
            _set_run_font(p.add_run(_strip_md(stripped[2:])), 16, bold=True)
            i += 1
            continue

        if stripped.startswith("|"):
            rows, i = _parse_table(lines, i)
            _add_table(doc, rows)
            doc.add_paragraph()
            continue

        if stripped.startswith("$$"):
            p = doc.add_paragraph()
            _spacing(p, before=6, after=6, line=1.3, align=A.CENTER)
            _set_run_font(p.add_run(_clean_formula(stripped)), BODY_PT, italic=True)
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m:
            p = doc.add_paragraph(style="List Number")
            _spacing(p, after=6, line=1.5, align=A.JUSTIFY)
            _add_inline_runs(p, m.group(2))
            i += 1
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            _spacing(p, after=4, line=1.5, align=A.JUSTIFY)
            _add_inline_runs(p, stripped[2:])
            i += 1
            continue

        # Đoạn văn thường.
        p = doc.add_paragraph()
        _spacing(p, after=8, line=1.5, align=A.JUSTIFY)
        _add_inline_runs(p, stripped)
        i += 1

    doc.save(str(out_path))
    return out_path


def convert_markdown_file(md_path, out_path, title_page: Optional[Dict] = None):
    """Đọc file .md rồi chuyển sang .docx. Trả về Path đã lưu."""
    md_text = Path(md_path).read_text(encoding="utf-8")
    return markdown_to_docx(md_text, out_path, title_page=title_page)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Chuyển .md -> .docx (chuẩn luận văn VN).")
    ap.add_argument("md", help="Đường dẫn file .md nguồn")
    ap.add_argument("docx", help="Đường dẫn file .docx đích")
    args = ap.parse_args()
    saved = convert_markdown_file(args.md, args.docx)
    print(f"Đã lưu: {saved}")
