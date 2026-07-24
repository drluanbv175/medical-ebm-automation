"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 21, 2026-07-24) — 2 phát hiện
xác nhận trong tools/run_g5_auto.py, phát hiện đầu tiên là lỗi do CHÍNH bản
vá vòng 20 (2026-07-24, cùng ngày) gây ra:

1. Khi specialist_modules chứa "economic" và design_code chính KHÔNG PHẢI
   "economic", main() nối `_ECONOMIC_FIELDS` vào rows đã có _BASE_ADMIN —
   nhưng cả 2 khối đều tự khai "record_id" riêng, tạo 2 định nghĩa TRÙNG TÊN
   trong CÙNG data dictionary REDCap (REDCap yêu cầu tên biến duy nhất).
2. build_strobe_flowchart() nhánh design_code="diagnostic" nhúng cứng PMID
   sai cho STARD 2015 (26511081 — một bài báo icodextrin/glucose không liên
   quan) thay vì PMID thật (26511519, Bossuyt et al., BMJ 2015, đã xác minh
   qua PubMed trực tiếp).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g5_auto as G5  # noqa: E402


class TestEconomicAddOnDoesNotDuplicateRecordId:
    def test_manual_merge_dedupes_record_id_by_name(self):
        """Tái hiện đúng logic nối trong main(): rows (đã có _BASE_ADMIN) +
        _ECONOMIC_FIELDS phải khử trùng theo tên trước khi nối."""
        rows, _ = G5.build_redcap_rows("rct", "Thử nghiệm tim mạch có tiểu mục chi phí-hiệu quả")
        existing_names = {r[0] for r in rows}
        add_on_fields = [r for r in G5._ECONOMIC_FIELDS if r[0] not in existing_names]
        merged = rows + add_on_fields
        names = [r[0] for r in merged]
        counts = Counter(names)
        duplicates = {name: n for name, n in counts.items() if n > 1}
        assert not duplicates, f"CRF nối thêm economic vẫn còn tên biến trùng: {duplicates}"

    def test_economic_fields_still_has_record_id_standalone(self):
        """Nhánh design_code='economic' đứng MỘT MÌNH (không đi qua _BASE_ADMIN)
        vẫn phải giữ record_id — chỉ merge mới cần dedupe, không phải xóa hẳn."""
        names = [r[0] for r in G5._ECONOMIC_FIELDS]
        assert "record_id" in names


class TestStardPmidCorrect:
    def test_diagnostic_flowchart_cites_correct_stard_pmid(self):
        chart = G5.build_strobe_flowchart("Demo", "diagnostic", 100, 100, 50, "generic")
        assert "PMID: 26511519" in chart
        assert "PMID: 26511081" not in chart
