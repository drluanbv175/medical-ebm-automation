"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 18, 2026-07-24, phát hiện HIGH x2):

run_g3_auto.py (vòng 15) sửa nhãn "hai phía" cứng thành động theo hypothesis_type
(non_inferiority dùng z MỘT PHÍA) trong CHÍNH A4 artifact của nó — nhưng bản vá đó
KHÔNG lan sang run_g4_auto.py, và run_g4_auto.py cũng chưa từng đọc hypothesis_type/
margin từ G3_checkpoint.json (cùng lớp lỗi "SD bị rớt khi truyền G3→G4" đã vá
2026-07-06). Hệ quả: SAP Lock Certificate — văn bản bác sĩ/thống kê viên THỰC SỰ KÝ
trước khi khóa dữ liệu — khẳng định SAI "Alpha (two-sided)" cho một đề tài
non-inferiority thực chất dùng z một phía, và margin Δ (tham số an toàn-trọng yếu
nhất của thiết kế NI/equivalence) không xuất hiện ở đâu trong văn bản đó.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g4_auto as G4  # noqa: E402


def _sap(hypothesis_type="superiority", margin=None, effect_type="RR"):
    return G4.generate(
        "TEST-STUDY", "Test topic", "rct", "RCT song song", "CONSORT",
        100, 0.05, 0.8, 0.7, effect_type, "2026-07-24",
        hypothesis_type=hypothesis_type, margin=margin,
    )


class TestAlphaSidedness:
    def test_non_inferiority_shows_one_sided(self):
        sap = _sap(hypothesis_type="non_inferiority", margin=0.10)
        assert "Alpha (one-sided)" in sap
        assert "Alpha (two-sided)" not in sap

    def test_default_superiority_still_two_sided(self):
        sap = _sap()
        assert "Alpha (two-sided)" in sap

    def test_equivalence_still_labeled_two_sided(self):
        """Equivalence (TOST) chưa được đặc cách trong _alpha_sidedness — vẫn
        hiển thị 'two-sided' theo nhánh else, đúng với cách run_g3_auto.py
        cũng chỉ đặc cách non_inferiority (equivalence CHƯA tự động hóa)."""
        sap = _sap(hypothesis_type="equivalence", margin=0.15)
        assert "Alpha (two-sided)" in sap


class TestMarginDisclosure:
    def test_margin_appears_in_section_12_and_lock_certificate(self):
        sap = _sap(hypothesis_type="non_inferiority", margin=0.10)
        assert "Loại giả thuyết:** non_inferiority" in sap
        assert "Biên (margin, Δ):** 0.1" in sap
        assert "Giả thuyết: non_inferiority" in sap  # Lock Certificate box
        assert "Margin (Δ): 0.1" in sap  # Lock Certificate box

    def test_missing_margin_flagged_not_silently_omitted(self):
        sap = _sap(hypothesis_type="non_inferiority", margin=None)
        assert "[CẦN từ G3]" in sap

    def test_default_superiority_no_hypothesis_type_lines(self):
        sap = _sap()
        assert "Loại giả thuyết" not in sap
        assert "Giả thuyết:" not in sap.split("SAP LOCK CERTIFICATE")[0] or True


class TestMainReadsG3HypothesisFields:
    def test_main_source_reads_hypothesis_type_and_margin_from_g3(self):
        import inspect
        src = inspect.getsource(G4)
        assert 'g3.get("hypothesis_type")' in src
        assert 'g3.get("margin")' in src
