"""
gen_research_docx.py — Bộ tạo file Word chuẩn hóa cho bộ artifact nghiên cứu y khoa G0→G9.

Sử dụng:
    python tools/gen_research_docx.py --study "TEN-DE-TAI" --gate G0 --artifact intake
    python tools/gen_research_docx.py --study "TEN-DE-TAI" --gate G1 --artifact protocol
    python tools/gen_research_docx.py --list   # liệt kê tất cả artifact

Quy ước đặt tên file đầu ra (2026-07-12: sửa ví dụ — khớp đúng _save(), trước đây ví dụ
tự mâu thuẫn với code thật):
    exports/<TEN-DE-TAI>/<artifact_code>_<ARTIFACT_KEY_HOA>_<TEN-DE-TAI>.docx
    Ví dụ: exports/PCOS-MET-2026/G0a_INTAKE_PCOS-MET-2026.docx

⚠ Đây là công cụ SOẠN THẢO/SCAFFOLD artifact theo SPEC gốc — KHÔNG dùng thay cho
`run_g2_auto.py`/`run_g4_auto.py` khi cần artifact G2 (đạo đức)/G4 (SAP) qua cổng khóa
chống p-hacking thật (`run_g6_auto.py::_ledger_approved` chỉ đọc file .md do 2 script đó
sinh, tên khác với công cụ này — xem cảnh báo trong _gen_ethics/_gen_sap; task_a5fde306).

Gọi từ agent dieu-phoi-nghien-cuu sau mỗi cổng G (2026-07-12: sửa ví dụ — __init__
KHÔNG nhận tham số `gate`, trước đây ví dụ gọi sai chữ ký thật):
    from tools.gen_research_docx import ResearchDocxGenerator
    gen = ResearchDocxGenerator(study_name="...")
    gen.generate("intake", content={...})
"""

import argparse
import json
import os

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

try:
    from docx import Document
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    print("[CẢNH BÁO] python-docx chưa cài. Chạy: pip install python-docx")


# ── Ánh xạ artifact chuẩn G0→G9 ────────────────────────────────────────────

ARTIFACT_MAP = {
    # G0 — Câu hỏi & tính khả thi
    "intake":       ("G0a", "G0", "Research Intake & Feasibility Audit"),
    "pico":         ("G0b", "G0", "Câu hỏi nghiên cứu — PICO/PECO/FINER"),
    "literature":   ("G0c", "G0-G1", "Tổng quan y văn & Evidence Ledger"),

    # G1 — Đề cương & thiết kế
    "protocol":     ("G1a", "G1", "Đề cương & Thiết kế nghiên cứu (Protocol)"),
    "charter":      ("G1b", "G1", "Project Charter — Phạm vi & Quản trị đề tài"),
    "plan":         ("G1c", "G1", "Kế hoạch triển khai — Nhân lực · Tiến độ · Kinh phí"),
    "risk":         ("G1d", "G1+G7", "Risk Register sống — Rủi ro & CAPA"),

    # G2 — Đạo đức & đăng ký
    "ethics":       ("G2",  "G2🔒", "Hồ sơ đạo đức (IRB) + ICF + Đăng ký nghiên cứu"),

    # G3 — Cỡ mẫu & biến số
    "samplesize":   ("G3a", "G3", "Tính cỡ mẫu & Power"),
    "variables":    ("G3b", "G3", "Bộ biến số & Data Dictionary (Codebook)"),
    "crf":          ("G3c", "G3", "Công cụ thu thập (CRF / Phiếu khảo sát)"),
    "instrument":   ("G3d", "G3", "Kiểm định công cụ đo lường (COSMIN)"),

    # G4 — SAP & Dummy tables
    "sap":          ("G4",  "G4🔒", "Kế hoạch phân tích thống kê (SAP) + Bảng kết quả dự kiến"),

    # G5 — Thu thập & quản lý dữ liệu
    "sop":          ("G5a", "G5", "SOP Thu thập số liệu"),
    "dmp":          ("G5b", "G5", "Kế hoạch quản lý dữ liệu (DMP vận hành)"),
    "datalock":     ("G5c", "G5-G6", "Biên bản khóa dữ liệu (Data Lock Memo)"),

    # G6 — Phân tích & diễn giải
    "analysis":     ("G6a", "G6", "Kết quả phân tích thống kê"),
    "interpretation": ("G6b", "G6-G7", "Diễn giải kết quả — Ý nghĩa lâm sàng & thống kê"),

    # G7 — Viết bản thảo
    "manuscript":   ("G7a", "G7", "Bản thảo khoa học (IMRAD)"),
    "checklist":    ("G7b", "G7", "Checklist chuẩn báo cáo (CONSORT/STROBE/PRISMA)"),

    # G8 — Bình duyệt nội bộ
    "review":       ("G8",  "G8", "Bình duyệt nội bộ — Nhận xét phản biện"),

    # G9 — Nghiệm thu
    "readiness":    ("G9",  "G9🔒", "Báo cáo sẵn sàng nghiệm thu (Final Readiness Report)"),

    # SỬA 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11, dimension
    # research_agents_deep_audit/g6_g7_depth_and_artifact_map): 10 agent doctrine
    # khai `--artifact <khóa>` bằng khóa KHÔNG tồn tại ở trên — generate() rơi vào
    # fallback code="GX"/gate="" (mất định danh cổng G0-G9), cùng lớp lỗi đã vá
    # cho co-mau-nghien-cuu.md/meta-phan-tich.md/cong-cu-do-luong.md ở các vòng
    # trước. Thêm đúng 10 khóa agent doctrine đang tham chiếu, gắn cổng/tiêu đề
    # đúng nghĩa (dùng _gen_generic như phần lớn khóa hiện có — không cần
    # generator riêng để sửa lỗi mất định danh cổng).
    "research-gap":       ("G0d", "G0-G1", "Đối chiếu khoảng trống nghiên cứu (Research Gap Analysis)"),
    "extraction":         ("G0e", "G0-G1", "Bảng trích xuất dữ liệu nghiên cứu (Data Extraction Table)"),
    "critical-appraisal": ("G0f", "G0-G1",
                           "Thẩm định phê bình một nghiên cứu (RoB 2/ROBINS-I/AMSTAR-2/QUADAS-2 · GRADE)"),
    "qualitative-design": ("G1e", "G1", "Thiết kế nghiên cứu định tính/hỗn hợp (COREQ/SRQR)"),
    "safety-monitoring":  ("G2a", "G2", "Kế hoạch giám sát an toàn — AE/SAE · DSMB · Stopping Rules"),
    "prediction-model":   ("G6c", "G6", "Mô hình tiên lượng/chẩn đoán (TRIPOD+AI/PROBAST+AI)"),
    "clinical-guideline": ("G6d", "G6-G7", "Cầu nối Nghiên cứu↔Thực hành — Evidence-to-Decision (GRADE EtD)"),
    "health-economics":   ("G7c", "G1+G7", "Phân tích kinh tế y tế (CEA/CUA/CBA/BIA — CHEERS 2022/ISPOR BIA GPP II)"),
    "citation-check":     ("G7d", "G7-G8🔒", "Kiểm chứng trích dẫn học thuật (A12 — cổng cứng chống trích dẫn ma)"),
    "study-log":          ("G9a", "G9", "Sổ cái & Bàn giao lưu trữ đề tài (A18 — Final Handover Log)"),

    # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15, dimension
    # workflow_agents_a): 4 khóa LÂM SÀNG (Cổng A/B — KHÔNG thuộc chuỗi cổng
    # G0-G9 nghiên cứu) mà quyet-dinh-chung.md/loi-dan-tuan-thu.md/
    # ket-qua-hoc-tap.md/cap-nhat-guideline.md tham chiếu nhưng chưa có trong
    # danh mục → cùng lớp lỗi "mất định danh cổng, rơi về generic GX" đã vá ở
    # vòng 11 cho 10 khóa nghiên cứu. "gate" ở đây ghi Cổng A/B thật (không
    # phải G-gate) chỉ để hiển thị đúng nghĩa trên header .docx.
    "shared-decision":      ("CA1", "A", "Quyết định chung & Option Grid (Shared Decision-Making)"),
    "outcome-learning":     ("CB1", "B", "Ghi nhận kết quả điều trị & Tín hiệu học tập (QI)"),
    "guideline-update":     ("CB2", "B", "Cảnh báo cập nhật Guideline"),
    # SỬA 2026-07-26 (vòng lặp kiểm tra-hoàn thiện vòng 31): "patient-instructions"
    # (loi-dan-tuan-thu.md) trước đây gắn gate="A" (mã CA2) — SAI, vì agent này tự
    # khai chạy SAU Cổng A (diễn đạt lại quyết định ĐÃ duyệt), thuộc bước "THEO DÕI"
    # khóa Cổng B theo _BAN-DO-KET-NOI.md/dieu-phoi-lam-sang.md, giống hệt
    # ket-qua-hoc-tap.md (CB1). Đổi mã sang CB3 cho khớp dãy CB, gate="B".
    "patient-instructions": ("CB3", "B", "Lời dặn bệnh nhân & Kế hoạch tuân thủ (A5)"),

    # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16): 2 khóa LÂM SÀNG
    # bị bỏ sót ở đợt vá vòng 15 cùng ngày (tra-cuu-chung-cu.md và
    # dieu-phoi-lam-sang.md — agent điều phối chính, dùng khóa này ở bước
    # CUỐI CÙNG sau Cổng B — tham chiếu khóa không tồn tại).
    "evidence-search":      ("CA3", "A", "Tóm tắt tra cứu chứng cứ điểm khám (PICO)"),
    "clinical-case-summary": ("CA4", "A-B", "Tóm tắt gói quyết định ca lâm sàng"),
}


class ResearchDocxGenerator:
    """Bộ tạo file Word chuẩn hóa cho một đề tài nghiên cứu y khoa."""

    # Định nghĩa font và màu chuẩn
    FONT   = "Times New Roman"
    BLUE   = RGBColor(0x00, 0x33, 0x66)
    GREEN  = RGBColor(0x00, 0x55, 0x00)
    RED    = RGBColor(0x99, 0x00, 0x00)
    ORANGE = RGBColor(0xCC, 0x55, 0x00)
    GRAY   = RGBColor(0x55, 0x55, 0x55)
    TABLE_HEADER_FILL = "D9EAF7"
    BODY_PT = 13
    TABLE_PT = 11
    CONTENT_WIDTH_TWIPS = 9072  # A4 21 cm - lề trái 3 cm - lề phải 2 cm.

    def __init__(self, study_name: str, output_dir: str = None):
        self.study_name  = study_name
        self.study_slug  = study_name.replace(" ", "-")
        self.today       = datetime.now().strftime("%Y-%m-%d")

        # Xác định thư mục xuất
        if output_dir:
            self.out_dir = Path(output_dir)
        else:
            base = Path(__file__).parent.parent / "exports" / self.study_slug
            self.out_dir = base
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _set_rfonts(self, rpr):
        """Ép Times New Roman cho cả ascii/hAnsi/eastAsia/cs để tiếng Việt không lỗi font."""
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), self.FONT)

    def _set_style_font(self, style, size=None, bold=None, italic=None):
        style.font.name = self.FONT
        if size is not None:
            style.font.size = Pt(size)
        if bold is not None:
            style.font.bold = bold
        if italic is not None:
            style.font.italic = italic
        self._set_rfonts(style.element.get_or_add_rPr())

    def _set_run_font(self, run, size=None, bold=None, italic=None, color=None):
        run.font.name = self.FONT
        if size is not None:
            run.font.size = Pt(size)
        if bold is not None:
            run.bold = bold
        if italic is not None:
            run.italic = italic
        if color:
            run.font.color.rgb = color
        self._set_rfonts(run._element.get_or_add_rPr())
        return run

    def _format_paragraph(self, para, *, before=0, after=8, line=1.5, align=None):
        pf = para.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        pf.line_spacing = line
        if align is not None:
            para.alignment = align
        return para

    def _add_page_number(self, paragraph):
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._format_paragraph(paragraph, before=0, after=0, line=1.0)
        self._set_run_font(paragraph.add_run("Trang "), size=10, color=self.GRAY)
        run = paragraph.add_run()
        self._set_run_font(run, size=10, color=self.GRAY)
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

    def _new_doc(self):
        doc = Document()
        for sec in doc.sections:
            sec.page_width    = Cm(21.0)
            sec.page_height   = Cm(29.7)
            sec.top_margin    = Cm(2.5)
            sec.bottom_margin = Cm(2.5)
            sec.left_margin   = Cm(3)
            sec.right_margin  = Cm(2)
            self._add_page_number(sec.footer.paragraphs[0])
        self._set_style_font(doc.styles["Normal"], size=self.BODY_PT)
        for name, size in (("Heading 1", 14), ("Heading 2", 13), ("Heading 3", 12)):
            if name in doc.styles:
                self._set_style_font(doc.styles[name], size=size, bold=True)
        return doc

    def _h(self, doc, text, level=1, color=None):
        p = doc.add_heading(text, level=level)
        self._format_paragraph(p, before=10 if level > 1 else 12, after=6, line=1.25)
        for r in p.runs:
            self._set_run_font(r, size=14 if level == 1 else 13 if level == 2 else 12,
                               bold=True, color=color or self.BLUE)
        return p

    def _p(self, doc, text, bold=False, italic=False, color=None, size=13):
        para = doc.add_paragraph()
        run  = para.add_run(text)
        self._set_run_font(run, size=size, bold=bold, italic=italic, color=color)
        self._format_paragraph(para, after=8, line=1.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        return para

    def _flag(self, doc, text):
        """Đoạn cần chủ nhiệm xác nhận."""
        return self._p(doc, f"[CẦN CHỦ NHIỆM XÁC NHẬN] {text}",
                       italic=True, color=self.ORANGE, size=12)

    def _note(self, doc, text):
        """Ghi chú hệ thống."""
        return self._p(doc, f"» {text}", italic=True, color=self.GRAY, size=11)

    def _disclaimer(self, doc):
        doc.add_paragraph("")
        self._p(doc,
            "⚠ Tài liệu do hệ thống AI (EBM Copilot) hỗ trợ soạn thảo — "
            "cần bác sĩ/chủ nhiệm đề tài kiểm chứng và phê duyệt trước khi sử dụng chính thức. "
            "KHÔNG bịa dữ liệu, KHÔNG PII, KHÔNG vượt cổng đạo đức G2. "
            "Cần bác sĩ kiểm chứng.",
            italic=True, color=self.RED, size=11)

    def _set_cell_shading(self, cell, fill):
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = tc_pr.find(qn("w:shd"))
        if shd is None:
            shd = OxmlElement("w:shd")
            tc_pr.append(shd)
        shd.set(qn("w:fill"), fill)

    def _set_cell_margins(self, cell, margin=108):
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

    def _set_cell_width(self, cell, width_twips):
        tc_pr = cell._tc.get_or_add_tcPr()
        tc_w = tc_pr.find(qn("w:tcW"))
        if tc_w is None:
            tc_w = OxmlElement("w:tcW")
            tc_pr.append(tc_w)
        tc_w.set(qn("w:w"), str(width_twips))
        tc_w.set(qn("w:type"), "dxa")

    def _repeat_header_row(self, row):
        tr_pr = row._tr.get_or_add_trPr()
        tbl_header = tr_pr.find(qn("w:tblHeader"))
        if tbl_header is None:
            tbl_header = OxmlElement("w:tblHeader")
            tr_pr.append(tbl_header)
        tbl_header.set(qn("w:val"), "true")

    def _set_fixed_table_layout(self, table):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        tbl_pr = table._tbl.tblPr
        layout = tbl_pr.find(qn("w:tblLayout"))
        if layout is None:
            layout = OxmlElement("w:tblLayout")
            tbl_pr.append(layout)
        layout.set(qn("w:type"), "fixed")

    def _write_cell(self, cell, text, *, bold=False, align=None, width_twips=None):
        if width_twips is not None:
            self._set_cell_width(cell, width_twips)
        self._set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        p = cell.paragraphs[0]
        p.text = ""
        self._format_paragraph(p, before=2, after=2, line=1.15,
                               align=align or WD_ALIGN_PARAGRAPH.JUSTIFY)
        self._set_run_font(p.add_run(str(text)), size=self.TABLE_PT, bold=bold)

    def _tbl(self, doc, headers, rows):
        t = doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = "Table Grid"
        self._set_fixed_table_layout(t)
        col_width = max(900, self.CONTENT_WIDTH_TWIPS // max(1, len(headers)))
        self._repeat_header_row(t.rows[0])
        for i, h in enumerate(headers):
            c = t.rows[0].cells[i]
            self._set_cell_shading(c, self.TABLE_HEADER_FILL)
            self._write_cell(c, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                             width_twips=col_width)
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                c = t.rows[ri + 1].cells[ci]
                self._write_cell(c, val, width_twips=col_width)
        return t

    def _header_block(self, doc, artifact_code, gate, title):
        """Khối tiêu đề chuẩn cho mọi artifact."""
        # Tiêu đề chính
        tp = doc.add_paragraph()
        tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._format_paragraph(tp, after=8, line=1.25, align=WD_ALIGN_PARAGRAPH.CENTER)
        tr = tp.add_run(title.upper())
        self._set_run_font(tr, size=14, bold=True, color=self.BLUE)

        # Dòng phụ
        sp = doc.add_paragraph()
        sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._format_paragraph(sp, after=10, line=1.25, align=WD_ALIGN_PARAGRAPH.CENTER)
        sr = sp.add_run(
            f"Đề tài: {self.study_name}  |  Artifact: {artifact_code}  |  "
            f"Cổng: {gate}  |  Ngày: {self.today}")
        self._set_run_font(sr, size=11, italic=True)

        doc.add_paragraph("")

    # ── Xuất file ───────────────────────────────────────────────────────────

    def _save(self, doc, artifact_code, artifact_key):
        fname  = f"{artifact_code}_{artifact_key.upper()}_{self.study_slug}.docx"
        fpath  = self.out_dir / fname
        doc.save(str(fpath))
        print(f"✓ {fname}")
        return str(fpath)

    # ── Generators cho từng artifact ────────────────────────────────────────

    def generate(self, artifact_key: str, content: dict = None) -> str:
        """Điểm vào chính — tự chọn generator theo artifact_key.

        - Khóa thuộc len(ARTIFACT_MAP) artifact NGHIÊN CỨU chuẩn (32, sau vòng lặp
          kiểm tra-hoàn thiện vòng 11 — trước đó 22, xem comment ở ARTIFACT_MAP) → generator
          chuyên biệt (hoặc generic).
        - Khóa NGOÀI danh mục → KHÔNG sập: dùng mẫu CHUNG (generic) + in cảnh báo
          (fail-soft, không im lặng) để lệnh minh họa chạy được thay vì ValueError.
          Sửa 2026-07-19 (audit vòng 3, D4): nguồn khóa sai KHÔNG chỉ agent lâm
          sàng nhúng khóa lạ (vd `guideline-update`, `chronic-pain`) — 2 agent
          NGHIÊN CỨU (co-mau-nghien-cuu.md, meta-phan-tich.md) cũng từng dùng
          khóa sai chính tả (`sample-size`/`meta-analysis` thay vì `samplesize`/
          `analysis` thật trong ARTIFACT_MAP) trước khi được sửa.
        """
        content = content or {}
        if artifact_key in ARTIFACT_MAP:
            code, gate, title = ARTIFACT_MAP[artifact_key]
            generator = getattr(self, f"_gen_{artifact_key}", self._gen_generic)
        else:
            print(f"⚠ Artifact '{artifact_key}' ngoài danh mục nghiên cứu chuẩn "
                  f"→ dùng mẫu chung (generic). Danh mục hợp lệ: {list(ARTIFACT_MAP.keys())}")
            code, gate, title = ("GX", "", artifact_key.replace("-", " ").title())
            generator = self._gen_generic
        return generator(code, gate, title, content)

    def generate_all_gates(self, gate: str, content_map: dict = None):
        """Xuất tất cả artifact thuộc một cổng G.

        SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 9, phát hiện HIGH):
        trước đây khi `gate` không khớp bất kỳ artifact nào (sai hoa/thường
        như "g3", hoặc cổng không tồn tại như "G10"), hàm âm thầm trả về
        list rỗng — main() không kiểm tra, nên lệnh thoát mã 0, KHÔNG sinh
        file, KHÔNG cảnh báo gì, mâu thuẫn với chính docstring của generate()
        (thiết kế "fail-soft, không im lặng"). Nay cảnh báo rõ + liệt kê
        các mã cổng hợp lệ, giống hệt cách generate() đã làm cho --artifact sai.
        """
        content_map = content_map or {}
        gate_clean  = gate.replace("🔒", "").strip()
        results     = []
        for key, (code, g, _) in ARTIFACT_MAP.items():
            g_clean = g.replace("🔒", "").replace(" ", "").split("-")[0]
            if g_clean == gate_clean or gate_clean in g_clean:
                path = self.generate(key, content_map.get(key, {}))
                results.append(path)
        if not results:
            valid_gates = sorted({
                g.replace("🔒", "").replace(" ", "").split("-")[0]
                for (_, g, _) in ARTIFACT_MAP.values()
            })
            print(f"⚠ Cổng '{gate}' không khớp bất kỳ artifact nào trong ARTIFACT_MAP "
                  f"(phân biệt hoa/thường) → KHÔNG sinh file nào. Cổng hợp lệ: {valid_gates}")
        return results

    # ── Generic (dùng khi chưa có generator chuyên biệt) ───────────────────

    def _gen_generic(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        if content:
            for section_title, section_body in content.items():
                self._h(doc, section_title, level=2)
                if isinstance(section_body, list):
                    for item in section_body:
                        pi = doc.add_paragraph(style="List Bullet")
                        ri = pi.add_run(str(item))
                        self._set_run_font(ri, size=12)
                elif isinstance(section_body, dict):
                    rows = [[k, str(v)] for k, v in section_body.items()]
                    self._tbl(doc, ["Mục", "Nội dung"], rows)
                else:
                    self._p(doc, str(section_body), size=12)
                doc.add_paragraph("")
        else:
            self._flag(doc, "Chủ nhiệm điền nội dung cho phần này.")

        self._disclaimer(doc)
        try:
            key = list(ARTIFACT_MAP.keys())[
                list(ARTIFACT_MAP.values()).index((code, gate, title))]
        except ValueError:  # khóa ngoài 20 artifact chuẩn (vd khóa lâm sàng) → slug từ title
            key = (title or code).replace(" ", "-").lower()
        return self._save(doc, code, key)

    # ── G0a: Research Intake & Feasibility Audit ────────────────────────────

    def _gen_intake(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        self._h(doc, "1. Xác định vấn đề & khoảng trống nghiên cứu")
        self._p(doc, content.get("problem",
            "[CẦN BỔ SUNG] Mô tả vấn đề lâm sàng và khoảng trống bằng chứng."), size=12)

        self._h(doc, "2. Câu hỏi nghiên cứu sơ bộ (PICO/PECO)")
        self._p(doc, content.get("pico_draft",
            "[CẦN BỔ SUNG] P: … · I/E: … · C: … · O: …"), size=12)

        self._h(doc, "3. Giả định loại thiết kế")
        self._p(doc, content.get("design_assumption",
            "[CẦN XÁC NHẬN] Ví dụ: Nghiên cứu cắt ngang mô tả có phân tích."), size=12)

        self._h(doc, "4. Tính mới & ý nghĩa lâm sàng (FINER)")
        finer = content.get("finer", {})
        self._tbl(doc,
            ["Tiêu chí FINER", "Đánh giá", "Trạng thái"],
            [
                ["F — Feasible (Khả thi)",
                 finer.get("feasible", "[CẦN BỔ SUNG]"), "🟡"],
                ["I — Interesting (Thú vị/quan trọng)",
                 finer.get("interesting", "[CẦN BỔ SUNG]"), "🟡"],
                ["N — Novel (Mới)",
                 finer.get("novel", "[CẦN BỔ SUNG]"), "🟡"],
                ["E — Ethical (Đạo đức)",
                 finer.get("ethical", "[CẦN BỔ SUNG]"), "🟡"],
                ["R — Relevant (Liên quan)",
                 finer.get("relevant", "[CẦN BỔ SUNG]"), "🟡"],
            ])

        self._h(doc, "5. Trạng thái dữ liệu & rủi ro đạo đức")
        self._p(doc, content.get("data_status",
            "Chưa có dữ liệu — cần qua cổng G2 (đạo đức) trước khi thu thập."), size=12)

        self._h(doc, "6. Cờ liêm chính & an toàn")
        flags = content.get("integrity_flags",
            ["KHÔNG PII", "KHÔNG bịa số liệu/phê duyệt",
             "G2 (đạo đức) phải ĐÓNG trước khi chạm dữ liệu thật"])
        for f in flags:
            pi = doc.add_paragraph(style="List Bullet")
            ri = pi.add_run(f)
            self._set_run_font(ri, size=12)

        self._h(doc, "7. Cổng kế tiếp & việc cần chủ nhiệm cấp")
        self._p(doc, content.get("next_gate",
            "Cổng G1 — Thiết kế & đề cương. Cần: xác nhận PICO + kết cục chính."), size=12)

        self._disclaimer(doc)
        return self._save(doc, code, "intake")

    # ── G0b: PICO/PECO/FINER ────────────────────────────────────────────────

    def _gen_pico(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        self._h(doc, "1. Khung PICO/PECO")
        pico = content.get("pico", {})
        self._tbl(doc,
            ["Thành phần", "Nội dung", "Ghi chú"],
            [
                ["P — Population (Quần thể)",
                 pico.get("P", "[CẦN BỔ SUNG]"), ""],
                ["I/E — Intervention/Exposure",
                 pico.get("I", "[CẦN BỔ SUNG]"), ""],
                ["C — Comparator (So sánh)",
                 pico.get("C", "[CẦN BỔ SUNG]"), ""],
                ["O — Outcome (Kết cục chính)",
                 pico.get("O_primary", "[CẦN BỔ SUNG]"), "Kết cục CHÍNH"],
                ["O — Outcome (Kết cục phụ)",
                 pico.get("O_secondary", "[CẦN BỔ SUNG]"), "Kết cục phụ"],
                ["T — Time (Thời gian)",
                 pico.get("T", "[CẦN BỔ SUNG]"), ""],
                ["S — Setting (Bối cảnh)",
                 pico.get("S", "[CẦN BỔ SUNG]"), ""],
            ])
        doc.add_paragraph("")

        self._h(doc, "2. Câu hỏi nghiên cứu (dạng văn xuôi)")
        self._p(doc, content.get("research_question",
            "[CẦN BỔ SUNG] Ở quần thể …, can thiệp/phơi nhiễm … so với …, "
            "có liên quan đến … như thế nào, trong thời gian …?"), size=12)

        self._h(doc, "3. Giả thuyết nghiên cứu")
        self._h(doc, "3.1. Giả thuyết không (H₀)", level=3)
        self._p(doc, content.get("h0",
            "[CẦN BỔ SUNG] Không có sự khác biệt/liên quan …"), size=12)
        self._h(doc, "3.2. Giả thuyết thay thế (H₁)", level=3)
        self._p(doc, content.get("h1",
            "[CẦN BỔ SUNG] Có sự khác biệt/liên quan …"), size=12)

        self._h(doc, "4. Kết cục đo lường")
        outcomes = content.get("outcomes", [])
        if outcomes:
            self._tbl(doc,
                ["Loại kết cục", "Tên kết cục", "Định nghĩa vận hành", "Đơn vị", "Nguồn"],
                outcomes)
        else:
            self._flag(doc, "Điền bảng kết cục đo lường.")

        self._h(doc, "5. Đánh giá tính khả thi FINER")
        finer = content.get("finer", {})
        self._tbl(doc,
            ["Tiêu chí", "Mô tả", "✅/🟡/🔴"],
            [
                ["Feasible",    finer.get("F", "[CẦN]"), "🟡"],
                ["Interesting", finer.get("I", "[CẦN]"), "🟡"],
                ["Novel",       finer.get("N", "[CẦN]"), "🟡"],
                ["Ethical",     finer.get("E", "[CẦN]"), "🟡"],
                ["Relevant",    finer.get("R", "[CẦN]"), "🟡"],
            ])

        self._disclaimer(doc)
        return self._save(doc, code, "pico")

    # ── G1a: Protocol ────────────────────────────────────────────────────────

    def _gen_protocol(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        sections = [
            ("1. Tóm tắt đề cương",        "background_summary"),
            ("2. Đặt vấn đề & cơ sở lý luận", "rationale"),
            ("3. Mục tiêu nghiên cứu",      "objectives"),
            ("4. Thiết kế nghiên cứu",      "design"),
            ("5. Dân số nghiên cứu",        "population"),
            ("6. Tiêu chuẩn lựa chọn/loại trừ", "eligibility"),
            ("7. Can thiệp / Phơi nhiễm",   "intervention"),
            ("8. Kết cục chính & phụ",      "outcomes_detail"),
            ("9. Ước tính cỡ mẫu",          "sample_size_brief"),
            ("10. Thu thập dữ liệu",         "data_collection"),
            ("11. Phân tích thống kê (tóm tắt)", "analysis_brief"),
            ("12. Đạo đức nghiên cứu",       "ethics_brief"),
            ("13. Hạn chế dự kiến",          "limitations"),
            ("14. Tài liệu tham khảo chính", "key_references"),
        ]
        for sec_title, key in sections:
            self._h(doc, sec_title, level=2)
            val = content.get(key, f"[CẦN BỔ SUNG] {sec_title}")
            if isinstance(val, list):
                for item in val:
                    pi = doc.add_paragraph(style="List Bullet")
                    pi.add_run(str(item)).font.name = self.FONT
                    pi.add_run("").font.size = Pt(12)
            else:
                self._p(doc, str(val), size=12)
            doc.add_paragraph("")

        self._disclaimer(doc)
        return self._save(doc, code, "protocol")

    # ── G3a: Cỡ mẫu ─────────────────────────────────────────────────────────

    def _gen_samplesize(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        self._h(doc, "1. Loại thiết kế & công thức áp dụng")
        self._p(doc, content.get("design_type",
            "[CẦN BỔ SUNG] Ví dụ: Cắt ngang — công thức ước lượng tỷ lệ."), size=12)

        self._h(doc, "2. Tham số đầu vào")
        params = content.get("params", {})
        self._tbl(doc,
            ["Tham số", "Ký hiệu", "Giá trị", "Nguồn/lý do"],
            [
                ["Mức tin cậy (1−α)", "Z₁₋α/₂",
                 params.get("z", "1,96 (95%)"),
                 params.get("z_source", "Chuẩn thống kê")],
                ["Power (1−β)", "1−β",
                 params.get("power", "0,80 (80%)"),
                 params.get("power_source", "[CẦN nguồn]")],
                ["Effect size / Tỷ lệ nền", "p/δ/OR",
                 params.get("effect", "[CẦN BỔ SUNG]"),
                 params.get("effect_source", "[CẦN PMID/DOI]")],
                ["Sai số cho phép", "d",
                 params.get("d", "[CẦN BỔ SUNG]"), ""],
                ["Tỷ lệ bỏ cuộc dự kiến", "%",
                 params.get("dropout", "10-15%"), ""],
                ["Design effect (nếu cluster)", "DEFF",
                 params.get("deff", "1,0 (không cluster)"), ""],
            ])

        self._h(doc, "3. Công thức & tính toán")
        self._p(doc, content.get("formula",
            "[CẦN BỔ SUNG] n = Z²×p(1−p)/d² hoặc công thức phù hợp."), size=12)
        self._p(doc, content.get("calculation",
            "[CẦN BỔ SUNG] Thay số: n = …; làm tròn lên: n = … người."), size=12)

        self._h(doc, "4. Cỡ mẫu chính thức & lý do")
        self._p(doc, content.get("final_n",
            "[CẦN BỔ SUNG] Cỡ mẫu chính thức = … (bao gồm dự phòng bỏ cuộc)."), size=12)

        self._h(doc, "5. Kiểm tra EPV (đa biến)")
        self._p(doc, content.get("epv_check",
            "[CẦN BỔ SUNG] EPV = sự kiện / số biến độc lập ≥ 10. "
            "Ví dụ: 150 sự kiện / 15 biến = EPV 10 ✅"), size=12)

        self._h(doc, "6. Nguồn tài liệu tham khảo")
        refs = content.get("references", ["[CẦN BỔ SUNG] PMID/DOI cho effect size"])
        for r in refs:
            pi = doc.add_paragraph(style="List Bullet")
            pi.add_run(r).font.name = self.FONT
            if pi.add_run(""):
                pi.runs[-1].font.size = Pt(12)

        self._disclaimer(doc)
        return self._save(doc, code, "samplesize")

    # ── G3b: Biến số & Codebook ──────────────────────────────────────────────

    def _gen_variables(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        self._h(doc, "1. Bản đồ biến số theo nhóm")
        var_groups = content.get("variable_groups", {})
        if var_groups:
            for group_name, vars_list in var_groups.items():
                self._h(doc, f"1.{list(var_groups.keys()).index(group_name)+1}. {group_name}", level=3)
                if isinstance(vars_list, list):
                    for v in vars_list:
                        pi = doc.add_paragraph(style="List Bullet")
                        pi.add_run(str(v)).font.name = self.FONT
                        if pi.add_run(""):
                            pi.runs[-1].font.size = Pt(12)
        else:
            self._flag(doc, "Điền danh sách biến số theo nhóm (độc lập, phụ thuộc, nhiễu, nền).")

        self._h(doc, "2. Bảng Data Dictionary (Codebook)")
        vars_table = content.get("codebook", [])
        if vars_table:
            self._tbl(doc,
                ["Tên biến", "Nhãn", "Loại", "Dạng đo", "Đơn vị/Thang", "Thời điểm", "Nguồn"],
                vars_table)
        else:
            self._note(doc, "Template codebook — điền đầy đủ trước khi khóa CRF.")
            self._tbl(doc,
                ["Tên biến", "Nhãn", "Loại", "Dạng đo", "Đơn vị/Thang", "Thời điểm", "Nguồn"],
                [["age", "Tuổi", "Độc lập", "Liên tục", "năm", "Nhập viện",
                  "[CẦN PMID]"]])

        self._h(doc, "3. Phân loại vai trò biến (DAG sơ bộ)")
        self._tbl(doc,
            ["Nhóm biến", "Danh sách", "Ghi chú"],
            [
                ["Biến phụ thuộc (kết cục chính)",
                 content.get("outcome_vars", "[CẦN BỔ SUNG]"), ""],
                ["Biến độc lập chính",
                 content.get("main_exposures", "[CẦN BỔ SUNG]"), ""],
                ["Biến gây nhiễu / điều chỉnh",
                 content.get("confounders", "[CẦN BỔ SUNG]"), "DAG xác nhận"],
                ["Biến điều chỉnh hiệu quả (effect modifier)",
                 content.get("modifiers", "[CẦN BỔ SUNG]"), ""],
            ])

        self._disclaimer(doc)
        return self._save(doc, code, "variables")

    # ── G4: SAP ──────────────────────────────────────────────────────────────

    def _gen_sap(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)
        self._p(doc,
            "⚠ ĐÂY LÀ KẾ HOẠCH PHÂN TÍCH ĐÃ KHÓA (PRE-SPECIFIED). "
            "KHÔNG sửa đổi sau khi bắt đầu xem dữ liệu thật.",
            bold=True, color=self.RED, size=12)
        # 2026-07-12 (rà kiến trúc — task_a5fde306): cùng lý do như _gen_ethics — file
        # NÀY KHÔNG phải artifact được cổng khóa chống p-hacking (run_g6_auto.py::
        # _ledger_approved) đọc/hash. Cổng đó CHỈ đọc exports/<study>/G4_A5_SAP_FINAL_
        # <study>.md do run_g4_auto.py sinh. KHÔNG đổi tên .docx ở đây để "khớp" — nguy
        # cơ ghi đè nhầm bản SAP thật (đã khóa) bằng bản DỰ THẢO của công cụ này.
        self._p(doc,
            "⚠ Đây là bản DỰ THẢO scaffold (gen_research_docx.py) — KHÔNG phải artifact "
            "chính thức mà cổng khóa chống p-hacking (run_g6_auto.py) đọc để xác nhận G4 "
            "đã LOCKED. Artifact chính thức là exports/<đề tài>/G4_A5_SAP_FINAL_<đề tài>.md "
            "do `python tools/run_g4_auto.py` sinh, được `tools/approve_gate.py` hash để "
            "ghi vào approval_ledger.json. Dùng file này để soạn thảo/tham khảo, KHÔNG dùng "
            "thay cho artifact do run_g4_auto.py sinh khi cần qua cổng G4.",
            bold=True, color=self.ORANGE, size=11)
        doc.add_paragraph("")

        sections = [
            ("1. Mục tiêu phân tích & kết cục chính", "objectives"),
            ("2. Quần thể phân tích (ITT / PP / Completers)", "analysis_population"),
            ("3. Phân tích mô tả (Descriptive)", "descriptive"),
            ("4. Phân tích chính cho Mục tiêu 1", "primary_analysis"),
            ("5. Phân tích chính cho Mục tiêu 2 (đa biến)", "multivariable"),
            ("6. Phân tích phụ (pre-specified subgroups)", "subgroup"),
            ("7. Kiểm tra giả định", "assumption_checks"),
            ("8. Xử lý dữ liệu thiếu", "missing_data"),
            ("9. Phần mềm & phiên bản", "software"),
            ("10. Khung bảng kết quả dự kiến (Dummy Tables)", "dummy_tables"),
        ]
        for sec_title, key in sections:
            self._h(doc, sec_title, level=2)
            val = content.get(key, f"[CẦN BỔ SUNG] {sec_title}")
            self._p(doc, str(val), size=12)
            doc.add_paragraph("")

        self._h(doc, "Xác nhận khóa SAP")
        self._tbl(doc,
            ["Người xác nhận", "Chức danh", "Ngày", "Chữ ký"],
            [
                [content.get("pi_name", "[CẦN]"), "Chủ nhiệm đề tài",
                 content.get("lock_date", "[CẦN]"), "___"],
                ["[CẦN]", "Thư ký KH", "[CẦN]", "___"],
            ])

        self._disclaimer(doc)
        return self._save(doc, code, "sap")

    # ── G2: Hồ sơ đạo đức ───────────────────────────────────────────────────

    def _gen_ethics(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)
        self._p(doc,
            "🔒 CỔNG CỨNG G2: Hồ sơ này chỉ SOẠN THẢO tự động. "
            "Phê duyệt IRB thật phải do Hội đồng đạo đức bệnh viện cấp — "
            "AI KHÔNG tự phê duyệt.",
            bold=True, color=self.RED, size=12)
        # 2026-07-12 (rà kiến trúc — task_a5fde306): file NÀY KHÔNG phải artifact được
        # cổng khóa chống p-hacking (run_g6_auto.py::_ledger_approved) đọc/hash — cổng đó
        # CHỈ đọc exports/<study>/G2_A3_ETHICS_PACKAGE_<study>.md do run_g2_auto.py sinh.
        # Không đổi tên file .docx ở đây để khớp — làm vậy có nguy cơ ghi đè NHẦM lên
        # bản .docx thật (nếu run_g2_auto.py đã chạy trước) bằng bản DỰ THẢO/placeholder
        # của công cụ này. Thay vào đó cảnh báo rõ để không ai nhầm đây là artifact CHÍNH.
        self._p(doc,
            "⚠ Đây là bản DỰ THẢO scaffold (gen_research_docx.py) — KHÔNG phải artifact "
            "chính thức mà cổng khóa chống p-hacking (run_g6_auto.py) đọc để xác nhận G2 "
            "đã LOCKED. Artifact chính thức là exports/<đề tài>/G2_A3_ETHICS_PACKAGE_"
            "<đề tài>.md do `python tools/run_g2_auto.py` sinh, được `tools/approve_gate.py` "
            "hash để ghi vào approval_ledger.json. Dùng file này để soạn thảo/tham khảo, "
            "KHÔNG dùng thay cho artifact do run_g2_auto.py sinh khi cần qua cổng G2.",
            bold=True, color=self.ORANGE, size=11)
        doc.add_paragraph("")

        self._h(doc, "1. Thông tin đề tài")
        self._tbl(doc,
            ["Mục", "Nội dung"],
            [
                ["Tên đề tài", content.get("study_title", self.study_name)],
                ["Chủ nhiệm", content.get("pi", "[CẦN BỔ SUNG]")],
                ["Đơn vị", content.get("institution", "[CẦN BỔ SUNG]")],
                ["Loại nghiên cứu", content.get("study_type", "[CẦN BỔ SUNG]")],
                ["Dân số dễ tổn thương", content.get("vulnerable_population", "Không")],
                ["Can thiệp lâm sàng", content.get("clinical_intervention", "Không — quan sát")],
            ])

        self._h(doc, "2. Đánh giá rủi ro đạo đức")
        risks = content.get("ethical_risks", [
            "Bảo mật thông tin người tham gia — mã giả danh",
            "Tính tự nguyện — quyền từ chối/rút lui",
            "Không can thiệp điều trị — không rủi ro thể chất",
        ])
        for r in risks:
            pi = doc.add_paragraph(style="List Bullet")
            pi.add_run(r).font.name = self.FONT
            if pi.runs:
                pi.runs[0].font.size = Pt(12)

        self._h(doc, "3. Checklist hồ sơ IRB")
        self._tbl(doc,
            ["Hạng mục", "Trạng thái", "Ghi chú"],
            [
                ["Mẫu đơn xin phê duyệt IRB", "🟡 Cần soạn", ""],
                ["Tóm tắt đề cương (lay summary)", "🟡 Cần soạn", ""],
                ["Phiếu đồng ý tham gia (ICF)", content.get("icf_status", "🟡 Cần soạn"), ""],
                ["Bộ công cụ thu thập (CRF/phiếu)", "🟡 Đang soạn — xem G3", ""],
                ["CV chủ nhiệm đề tài", "🟡 Cần đính kèm", ""],
                ["Khai báo xung đột lợi ích (COI)", "🟡 Cần khai báo", ""],
                ["Phê duyệt IRB", "🔴 CHƯA CÓ", "Bác sĩ nộp — AI không tự cấp"],
                ["Đăng ký nghiên cứu (nếu can thiệp)", content.get("registration_status",
                    "⏳ Xem xét yêu cầu"), ""],
            ])

        self._h(doc, "4. Phiếu đồng ý tham gia (ICF) — dự thảo")
        self._p(doc, content.get("icf_draft",
            "[CẦN SOẠN] Dự thảo ICF — mô tả nghiên cứu, quyền lợi/rủi ro, "
            "tính tự nguyện, bảo mật, liên hệ chủ nhiệm."), size=12)

        self._disclaimer(doc)
        return self._save(doc, code, "ethics")

    # ── G5b: DMP ──────────────────────────────────────────────────────────────

    def _gen_dmp(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)
        sections = [
            ("1. Mô tả dữ liệu & định dạng",     "data_description"),
            ("2. Thu thập & nhập liệu",            "collection"),
            ("3. Kiểm tra chất lượng & làm sạch",  "qc"),
            ("4. Khử định danh (De-identification)", "deidentification"),
            ("5. Lưu trữ & bảo mật",               "storage"),
            ("6. Chia sẻ & truy cập",               "sharing"),
            ("7. Lưu trữ dài hạn sau nghiên cứu",  "archiving"),
            ("8. Trách nhiệm & phân công",          "responsibilities"),
        ]
        for sec_title, key in sections:
            self._h(doc, sec_title, level=2)
            self._p(doc, content.get(key,
                f"[CẦN BỔ SUNG] {sec_title}"), size=12)
            doc.add_paragraph("")

        self._disclaimer(doc)
        return self._save(doc, code, "dmp")

    # ── G7a: IMRAD Manuscript ────────────────────────────────────────────────

    def _gen_manuscript(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        for section in ["Abstract", "Introduction", "Methods", "Results",
                         "Discussion", "Conclusion", "References"]:
            self._h(doc, section.upper())
            self._p(doc, content.get(section.lower(),
                f"[CẦN BỔ SUNG] Phần {section}."), size=12)
            doc.add_paragraph("")

        self._h(doc, "Checklist chuẩn báo cáo")
        self._p(doc, content.get("reporting_standard",
            "[CẦN BỔ SUNG] CONSORT/STROBE/PRISMA/SPIRIT/STARD — đính kèm bảng kiểm đã điền."),
            size=12)

        self._disclaimer(doc)
        return self._save(doc, code, "manuscript")

    # ── G9: Final Readiness Report ───────────────────────────────────────────

    def _gen_readiness(self, code, gate, title, content: dict):
        doc = self._new_doc()
        self._header_block(doc, code, gate, title)

        verdict = content.get("verdict", "NOT READY")
        verdict_color = (self.GREEN if verdict == "READY"
                         else self.ORANGE if verdict == "PARTIALLY READY"
                         else self.RED)
        self._p(doc, f"KẾT LUẬN NGHIỆM THU: {verdict}",
                bold=True, color=verdict_color, size=14)
        doc.add_paragraph("")

        self._h(doc, "1. Bảng kiểm Definition of Done (14 điểm)")
        dod_items = content.get("dod", [])
        if dod_items:
            self._tbl(doc,
                ["#", "Điểm DoD", "Trạng thái", "Ghi chú"],
                dod_items)
        else:
            self._flag(doc, "Điền bảng 14 điểm DoD từ _KIEM-TOAN-DAY-DU-NGHIEN-CUU.md.")

        self._h(doc, "2. Gap Register + CAPA")
        gaps = content.get("gaps", [])
        if gaps:
            self._tbl(doc,
                ["#", "Khoảng trống (🔴)", "Mức", "Agent xử lý", "CAPA", "Hạn"],
                gaps)
        else:
            self._note(doc, "Không còn khoảng trống 🔴 — đề tài READY.")

        self._h(doc, "3. Trạng thái 3 cổng cứng")
        self._tbl(doc,
            ["Cổng cứng", "Trạng thái", "Bằng chứng"],
            [
                ["G2 Đạo đức & đăng ký",
                 content.get("g2_status", "🔴 CHƯA ĐÓNG"),
                 content.get("g2_evidence", "[Số phê duyệt IRB]")],
                ["G4 Khóa SAP",
                 content.get("g4_status", "🔴 CHƯA ĐÓNG"),
                 content.get("g4_evidence", "[Biên bản khóa SAP]")],
                ["G9 Liêm chính tác giả",
                 content.get("g9_status", "🔴 CHƯA ĐÓNG"),
                 content.get("g9_evidence", "[COI + tài trợ + khai báo AI]")],
            ])

        self._disclaimer(doc)
        return self._save(doc, code, "readiness")


# ── CLI ─────────────────────────────────────────────────────────────────────

def list_artifacts():
    print(f"\n{len(ARTIFACT_MAP)} ARTIFACT CHUẨN — G0 → G9\n" + "="*50)
    for key, (code, gate, title) in ARTIFACT_MAP.items():
        print(f"  {code:5s}  [{gate:8s}]  --artifact {key:15s}  {title}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Tạo file Word (.docx) chuẩn hóa cho artifact nghiên cứu y khoa")
    parser.add_argument("--study",    help="Tên đề tài (dùng làm slug thư mục)")
    parser.add_argument("--artifact", help="Loại artifact (xem --list)")
    parser.add_argument("--gate",     help="Xuất tất cả artifact của cổng G (vd: G0, G1, G3)")
    parser.add_argument("--all",      action="store_true",
                        help="Xuất TẤT CẢ artifact (scaffold)")
    parser.add_argument("--content",  help="JSON string hoặc path tới file JSON nội dung")
    parser.add_argument("--outdir",   help="Thư mục đầu ra (mặc định: exports/<study>/)")
    parser.add_argument("--list",     action="store_true", help="Liệt kê tất cả artifact")
    args = parser.parse_args()

    if args.list:
        list_artifacts()
        return

    if not args.study:
        parser.error("Cần --study <tên đề tài>")
    if not HAS_DOCX:
        print("Lỗi: python-docx chưa cài. Chạy: pip install python-docx")
        return

    # Đọc content nếu có
    content = {}
    if args.content:
        if os.path.isfile(args.content):
            with open(args.content, encoding="utf-8") as f:
                content = json.load(f)
        else:
            try:
                content = json.loads(args.content)
            except json.JSONDecodeError:
                print("Cảnh báo: --content không phải JSON hợp lệ — dùng content rỗng.")

    gen = ResearchDocxGenerator(args.study, args.outdir)

    # THÊM 2026-07-19 (audit vòng 3, D4_g10_docx_artifact_integrity — trung
    # bình): trước bản vá này, nếu bác sĩ/agent vô tình truyền CẢ --gate LẪN
    # --artifact trong cùng 1 lệnh (3 file doctrine từng làm vậy —
    # co-mau-nghien-cuu.md/meta-phan-tich.md/viet-ban-thao.md), --artifact bị
    # "nuốt" ÂM THẦM (nhánh elif args.gate thắng trước, không cảnh báo gì).
    # Nay báo lỗi tường minh thay vì im lặng bỏ qua 1 cờ.
    if args.gate and args.artifact:
        parser.error("--gate và --artifact loại trừ nhau, chỉ dùng MỘT cờ trong một lệnh")

    if args.all:
        for key in ARTIFACT_MAP:
            gen.generate(key, content.get(key, {}))
    elif args.gate:
        gen.generate_all_gates(args.gate, content)
    elif args.artifact:
        gen.generate(args.artifact, content)
    else:
        parser.error("Cần --artifact, --gate, hoặc --all")


if __name__ == "__main__":
    main()
