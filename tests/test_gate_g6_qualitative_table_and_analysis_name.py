# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 11 (2026-07-23, dimension
g6_g7_depth_and_artifact_map): "qualitative" là thiết kế chuẩn thứ 8 duy nhất
còn thiếu trong TABLE_SHELLS và analysis_name_map của run_g6_auto.py — trước
đây rơi vào fallback generic (TABLE_SHELLS) / "[CẦN XÁC ĐỊNH THEO SAP]"
(analysis_name_map), dù _SCRIPT03_INFO["qualitative"] đã có nhãn đúng sẵn
trong CÙNG file (mâu thuẫn nội bộ) và pipeline G0-G10 đã có nhánh định tính
đầy đủ từ vòng trước (task #21). Cùng lớp lỗi/cùng test-pattern với
test_gate_prediction_design_coverage.py (vòng 5/17).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402


def test_qualitative_in_table_shells_not_generic_fallback():
    assert "qualitative" in G6.TABLE_SHELLS
    tables = G6.TABLE_SHELLS["qualitative"]
    table_titles = " ".join(t[0] for t in tables)
    assert "chưa có mẫu bảng" not in table_titles
    assert "bão hòa" in table_titles.lower() or "chủ đề" in table_titles.lower()


def test_qualitative_table_shells_no_fabricated_numbers():
    looks_like_real_number = re.compile(r"\b\d+([.,]\d+)?%?\b")
    for _title, rows in G6.TABLE_SHELLS["qualitative"]:
        header = rows[0]
        note_col = header.index("Ghi chú") if "Ghi chú" in header else None
        for row in rows[1:]:
            for idx, cell in enumerate(row[1:], start=1):
                if idx == note_col:
                    continue
                assert not looks_like_real_number.search(cell), (
                    f"Ô có vẻ như số liệu/trích dẫn bịa sẵn: {cell!r}"
                )


def test_qualitative_analysis_name_consistent_with_script03_info():
    gen_source = (TOOLS_DIR / "run_g6_auto.py").read_text(encoding="utf-8")
    assert '"qualitative":     _SCRIPT03_INFO["qualitative"][0]' in gen_source, (
        "analysis_name_map['qualitative'] nên tái dùng nhãn đã có sẵn ở "
        "_SCRIPT03_INFO thay vì định nghĩa nhãn mới/rơi vào fallback"
    )
