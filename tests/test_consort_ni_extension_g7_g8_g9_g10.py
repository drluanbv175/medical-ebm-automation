"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 17, 2026-07-24):

CONSORT có phụ lục RIÊNG cho thử nghiệm non-inferiority/equivalence — Piaggio G,
Elbourne DR, Pocock SJ, Evans SJ, Altman DG; CONSORT Group. "Reporting of
noninferiority and equivalence randomized trials: extension of the CONSORT 2010
statement." JAMA. 2012;308(24):2594-2604. doi:10.1001/jama.2012.87802 (xác minh
thật qua trang bài báo JAMA). Vòng 15-16 đã thêm hypothesis_type/margin xuyên
suốt G3→G6, nhưng G7 (bản thảo), G8 (kiểm trước nộp), G9 (nghiệm thu), G10 (lắp
ráp đề cương) đều KHÔNG hề đọc lại 2 trường này — một đề tài NI/equivalence được
thiết kế đúng ở G3 sẽ bị báo cáo/nghiệm thu như thể là superiority thông thường,
thiếu các mục bắt buộc riêng của phụ lục Piaggio 2012 (tiêu đề, margin, CI-vs-
margin) — cùng lớp lỗi "thêm tính năng 1 cổng, quên nối cổng sau" đã lặp lại
nhiều lần (specialist_modules G1→G7/G8/G9 ở vòng 11-15; hypothesis_type G3→G6 ở
vòng 16).
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g7_auto as G7  # noqa: E402
import run_g8_auto as G8  # noqa: E402
import run_g9_auto as G9  # noqa: E402
import run_g10_assemble as G10  # noqa: E402


class TestG7ConsortNiChecklist:
    def test_ni_extension_appended_for_rct_non_inferiority(self):
        block = G7.generate_checklist(
            design_code="rct", reporting_std="CONSORT 2025", std_total_items=30,
            irb_number="X", registration="Y", n_adjusted=100, alpha=0.05, power=0.8,
            specialist_modules=[], hypothesis_type="non_inferiority", margin=0.10,
        )
        assert "Piaggio" in block
        assert "doi:10.1001/jama.2012.87802" in block
        assert "1a-NI" in block and "22-NI" in block
        assert "margin Δ=0.1" in block or "0.1" in block

    def test_ni_extension_appended_for_equivalence(self):
        block = G7.generate_checklist(
            design_code="rct", reporting_std="CONSORT 2025", std_total_items=30,
            irb_number="X", registration="Y", n_adjusted=100, alpha=0.05, power=0.8,
            hypothesis_type="equivalence", margin=0.15,
        )
        assert "EQUIVALENCE" in block

    def test_no_ni_extension_for_default_superiority(self):
        block = G7.generate_checklist(
            design_code="rct", reporting_std="CONSORT 2025", std_total_items=30,
            irb_number="X", registration="Y", n_adjusted=100, alpha=0.05, power=0.8,
        )
        assert "Piaggio" not in block

    def test_no_ni_extension_for_non_rct_design_even_if_hypothesis_type_set(self):
        """hypothesis_type chỉ có ý nghĩa cho RCT — cohort/cross_sectional không
        nên bị nối nhầm phụ lục CONSORT-NI dù trường vẫn tồn tại trong checkpoint."""
        block = G7.generate_checklist(
            design_code="cohort", reporting_std="STROBE 2007", std_total_items=22,
            irb_number="X", registration="Y", n_adjusted=100, alpha=0.05, power=0.8,
            hypothesis_type="non_inferiority", margin=0.10,
        )
        assert "Piaggio" not in block


class TestG8ConsortNiChecklist:
    def test_ni_extension_checklist_built_for_rct_non_inferiority(self):
        r = G8.build_reporting_checklist("rct", {}, hypothesis_type="non_inferiority", margin=0.10)
        assert r["ni_extension_checklist"] is not None
        ni = r["ni_extension_checklist"]
        assert "Piaggio" in ni["standard_name"]
        assert ni["margin"] == 0.10
        assert ni["hypothesis_type"] == "non_inferiority"
        assert len(ni["items"]) == 11

    def test_no_ni_extension_for_default_superiority(self):
        r = G8.build_reporting_checklist("rct", {})
        assert r["ni_extension_checklist"] is None

    def test_no_ni_extension_for_non_rct_design(self):
        r = G8.build_reporting_checklist("cohort", {}, hypothesis_type="non_inferiority", margin=0.10)
        assert r["ni_extension_checklist"] is None

    def test_main_reads_hypothesis_type_from_g3_gate(self):
        """Xác nhận build_presubmission call site thật (main()) đọc gates['G3']
        — không chỉ hàm build_reporting_checklist() độc lập."""
        import inspect
        src = inspect.getsource(G8)
        assert 'gates.get("G3", {}).get("hypothesis_type")' in src


class TestG9NonInferiorityGateItem:
    def test_a6_item_added_for_non_inferiority(self):
        cps = {"G1": {}, "G2": {}, "G3": {"hypothesis_type": "non_inferiority", "margin": 0.10},
               "G4": {}, "G5": {}, "G7": {}}
        block = G9.build_part8_gate_criteria(cps, n_authors=3, study="TEST-VONG17-G9-NI")
        assert "A6." in block
        assert "NON_INFERIORITY" in block
        assert "0.1" in block

    def test_a6_item_added_for_equivalence(self):
        cps = {"G1": {}, "G2": {}, "G3": {"hypothesis_type": "equivalence", "margin": 0.15},
               "G4": {}, "G5": {}, "G7": {}}
        block = G9.build_part8_gate_criteria(cps, n_authors=3, study="TEST-VONG17-G9-EQ")
        assert "A6." in block
        assert "EQUIVALENCE" in block

    def test_no_a6_item_for_default_superiority(self):
        cps = {"G1": {}, "G2": {}, "G3": {}, "G4": {}, "G5": {}, "G7": {}}
        block = G9.build_part8_gate_criteria(cps, n_authors=3, study="TEST-VONG17-G9-SUP")
        assert "A6." not in block

    def test_missing_g3_checkpoint_does_not_crash(self):
        cps = {"G1": {}, "G2": {}, "G4": {}, "G5": {}, "G7": {}}
        block = G9.build_part8_gate_criteria(cps, n_authors=3, study="TEST-VONG17-G9-NOG3")
        assert "A6." not in block


class TestG10HypothesisTypeDisclosure:
    def test_non_inferiority_disclosed_in_cauhoi_section(self):
        cps = {"G1": {}, "G3": {"hypothesis_type": "non_inferiority", "margin": 0.10}}
        text = G10.sec_cauhoi(cps, {})
        assert "NON_INFERIORITY" in text
        assert "0.1" in text
        assert "Piaggio" in text

    def test_equivalence_disclosed_in_cauhoi_section(self):
        cps = {"G1": {}, "G3": {"hypothesis_type": "equivalence", "margin": 0.15}}
        text = G10.sec_cauhoi(cps, {})
        assert "EQUIVALENCE" in text

    def test_default_superiority_not_mentioned(self):
        cps = {"G1": {}, "G3": {}}
        text = G10.sec_cauhoi(cps, {})
        assert "NON_INFERIORITY" not in text
        assert "EQUIVALENCE" not in text

    def test_missing_g3_checkpoint_does_not_crash(self):
        cps = {"G1": {}}
        text = G10.sec_cauhoi(cps, {})
        assert isinstance(text, str)
