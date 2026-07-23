# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 11 (2026-07-23, workflow đối kháng
wf_37b290b2-31e, dimension g6_g7_depth_and_artifact_map, 2 phát hiện liên quan):

1. kinh-te-y-te.md (dòng 102) + dieu-phoi-nghien-cuu.md (dòng 39/137) khẳng định
   "G1 thiết kế cấu phần kinh tế · G7 báo cáo CHEERS" nhưng run_g7_auto.py trước
   đây KHÔNG có khóa "economic" nào trong REPORTING_CHECKLISTS/CHECKLIST_ITEMS —
   design_code="economic" (khi bác sĩ PIN trực tiếp cho đề tài kinh tế y tế
   thuần túy) rơi vào fallback "cohort"/STROBE (sai hoàn toàn chuẩn báo cáo).
2. run_g1_auto.py::detect_specialist_modules() phát hiện 'economic' như MODULE
   CỘNG THÊM (đề tài có primary design khác, vd RCT có nhánh chi phí-hiệu quả
   lồng bên trong) và ghi vào G1 checkpoint — nhưng generate_checklist() trước
   đây KHÔNG BAO GIỜ đọc lại specialist_modules, nên CHEERS không bao giờ xuất
   hiện trong checklist G7 dù đề tài có cấu phần kinh tế thật.

Đã vá: thêm CHECKLIST_ITEMS["economic"]/REPORTING_CHECKLISTS["economic"] (CHEERS
2022, 28 mục — xác minh trực tiếp Table 1, Husereau D et al. Value Health.
2022;25(1):3-9, không suy diễn từ trí nhớ huấn luyện); generate_checklist() nhận
thêm tham số specialist_modules — khi 'economic' có mặt VÀ design_code chính
KHÔNG PHẢI 'economic', nối thêm khối CHEERS riêng sau checklist chính (tránh
trùng lặp khi 'economic' đã LÀ design_code chính).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g7_auto as G7  # noqa: E402


class TestCheersStandaloneDesignCode:
    def test_economic_in_reporting_checklists_and_checklist_items(self):
        assert "economic" in G7.REPORTING_CHECKLISTS
        assert G7.REPORTING_CHECKLISTS["economic"] == ("CHEERS 2022", 28)
        assert "economic" in G7.CHECKLIST_ITEMS
        assert len(G7.CHECKLIST_ITEMS["economic"]) == 28
        item_ids = [i[0] for i in G7.CHECKLIST_ITEMS["economic"]]
        assert item_ids == [str(n) for n in range(1, 29)]

    def test_economic_as_primary_design_generates_cheers_not_generic_fallback(self):
        out = G7.generate_checklist(
            "economic", "CHEERS 2022", 28, "IRB-001", "N/A", 0, 0.05, 0.80
        )
        assert "CHEERS 2022" in out
        assert "Xác định đây là đánh giá kinh tế y tế" not in out  # không lặp tiêu đề sai
        assert out.count("PHỤ LỤC — CHECKLIST") == 1, "Không nên nối thêm khối CHEERS thứ 2"


class TestCheersAsSpecialistModuleAddOn:
    def test_rct_with_economic_specialist_module_appends_cheers_block(self):
        out = G7.generate_checklist(
            "rct", "CONSORT 2025", 30, "IRB-001", "NCT-001", 200, 0.05, 0.80,
            specialist_modules=["economic"],
        )
        assert "CONSORT 2025" in out
        assert "CHEERS 2022" in out
        assert out.count("PHỤ LỤC — CHECKLIST") == 2, (
            "RCT + specialist_module 'economic' phải có CẢ 2 khối checklist"
        )
        assert "cấu phần **kinh tế y tế** cộng thêm" in out

    def test_rct_without_economic_module_has_no_cheers_block(self):
        out = G7.generate_checklist(
            "rct", "CONSORT 2025", 30, "IRB-001", "NCT-001", 200, 0.05, 0.80,
            specialist_modules=[],
        )
        assert "CHEERS 2022" not in out
        assert out.count("PHỤ LỤC — CHECKLIST") == 1

    def test_specialist_modules_defaults_to_empty_no_crash(self):
        out = G7.generate_checklist(
            "cohort", "STROBE 2007", 22, "IRB-001", "N/A", 200, 0.05, 0.80,
        )
        assert "CHEERS 2022" not in out

    def test_economic_primary_design_not_duplicated_even_if_specialist_modules_also_lists_it(self):
        """Ca biên: nếu design_code CHÍNH đã là 'economic' (bác sĩ PIN trực tiếp),
        specialist_modules cũng có thể vô tình chứa 'economic' — không được nối
        khối CHEERS thứ 2 (tránh trùng lặp báo cáo)."""
        out = G7.generate_checklist(
            "economic", "CHEERS 2022", 28, "IRB-001", "N/A", 0, 0.05, 0.80,
            specialist_modules=["economic"],
        )
        assert out.count("PHỤ LỤC — CHECKLIST") == 1
