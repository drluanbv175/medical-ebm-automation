# -*- coding: utf-8 -*-
"""Khóa chuẩn hình thức Word cho đề cương/tài liệu nghiên cứu.

Các test này đọc trực tiếp XML bên trong .docx để bắt hồi quy về font tiếng Việt,
bảng Word thật, padding ô, tô header và số trang. Đây là lớp kiểm hình thức bổ sung
cho validator nội dung G10.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

pytest.importorskip("docx", reason="python-docx chưa cài — bỏ qua test sinh .docx thật")

import gen_research_docx as G  # noqa: E402
import md2docx_vn  # noqa: E402


def _xml_parts(docx_path: Path) -> dict[str, str]:
    with zipfile.ZipFile(docx_path) as zf:
        return {
            name: zf.read(name).decode("utf-8", errors="ignore")
            for name in zf.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        }


def _all_xml(parts: dict[str, str]) -> str:
    return "\n".join(parts.values())


def test_research_scaffold_docx_has_vietnamese_font_tables_and_page_number(tmp_path):
    gen = G.ResearchDocxGenerator("TEST-FORMAT-DOCX", output_dir=str(tmp_path))
    path = Path(gen.generate("variables", {
        "codebook": [
            ["age", "Tuổi", "Độc lập", "Liên tục", "năm", "T0", "PMID: 40995744"],
        ],
    }))

    parts = _xml_parts(path)
    xml = _all_xml(parts)

    assert 'w:eastAsia="Times New Roman"' in xml
    assert '<w:tblLayout w:type="fixed"' in xml
    assert 'w:fill="D9EAF7"' in xml
    assert "<w:tcMar>" in xml
    assert '<w:tblHeader w:val="true"' in xml
    assert any("PAGE" in text for name, text in parts.items() if name.startswith("word/footer"))


def test_g10_markdown_docx_has_fixed_word_tables_and_page_number(tmp_path):
    out = tmp_path / "de-cuong.docx"
    md2docx_vn.markdown_to_docx(
        "# 1. Tóm tắt\n\n"
        "Đoạn văn tiếng Việt có dấu và **nhãn quan trọng**.\n\n"
        "| Mục | Nội dung |\n"
        "|---|---|\n"
        "| Cỡ mẫu | 428 |\n",
        out,
        title_page={"doc_type": "ĐỀ CƯƠNG NGHIÊN CỨU", "title": "Kiểm định định dạng"},
    )

    parts = _xml_parts(out)
    xml = _all_xml(parts)

    assert 'w:eastAsia="Times New Roman"' in xml
    assert '<w:tblLayout w:type="fixed"' in xml
    assert 'w:fill="D9EAF7"' in xml
    assert "<w:tcMar>" in xml
    assert '<w:tblHeader w:val="true"' in xml
    assert any("PAGE" in text for name, text in parts.items() if name.startswith("word/footer"))
