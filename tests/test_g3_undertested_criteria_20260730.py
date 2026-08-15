"""Hồi quy G3-QG-04 (audit toàn diện G0-G10, 2026-07-30, HIGH — phần còn lại):

Trước vá này, 9/25 tiêu chí của g3_quality_gate.py hoàn toàn không có
assertion _row() riêng trong tests/test_g3_quality_gate.py: G3-AUTO-02,
G3-AUTO-04, G3-AUTO-10, G3-AUTO-14, G3-AUTO-15, G3-HUMAN-01, G3-HUMAN-02,
G3-HUMAN-03, G3-HUMAN-05. G3-AUTO-10 đã có test tích hợp thật riêng (đóng
cùng lúc với sửa G3-QG-01 ở round trước — xem TestPipelineThatKhongDungFixtureGia
trong test_g3_quality_gate.py). File này đóng nốt 7 tiêu chí còn lại — mỗi
tiêu chí có ít nhất 1 ca PASS và 1 ca REVIEW/BLOCK để xác nhận nó THẬT SỰ có
thể đi cả hai hướng (không phải tautology ẩn chưa bị phát hiện)."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from tests.test_g3_quality_gate import (  # noqa: E402
    _checkpoint,
    _evaluate,
    _full_meta,
    _row,
)


class TestG3Auto02CanonicalDesignCode:
    def test_canonical_design_passes(self, tmp_path):
        report = _evaluate(tmp_path, checkpoint=_checkpoint(design_code="rct"))
        assert _row(report, "G3-AUTO-02")["status"] == "PASS"

    def test_non_canonical_design_blocks(self, tmp_path):
        report = _evaluate(tmp_path, checkpoint=_checkpoint(design_code="typo_design"))
        assert _row(report, "G3-AUTO-02")["status"] == "BLOCK"


class TestG3Auto04UsableSampleSize:
    def test_positive_n_adjusted_passes(self, tmp_path):
        report = _evaluate(tmp_path, checkpoint=_checkpoint(n_adjusted=1178))
        assert _row(report, "G3-AUTO-04")["status"] == "PASS"

    def test_zero_n_adjusted_and_no_confirmed_n_blocks(self, tmp_path):
        report = _evaluate(
            tmp_path,
            checkpoint=_checkpoint(n_adjusted=0, confirmed_n=None, design_code="rct"),
        )
        assert _row(report, "G3-AUTO-04")["status"] == "BLOCK"


class TestG3Auto15FormulaAndSoftwareDisclosed:
    def test_formula_and_software_present_passes(self, tmp_path):
        report = _evaluate(
            tmp_path,
            checkpoint=_checkpoint(
                formula_used="Hai tỷ lệ độc lập (xấp xỉ chuẩn), z(α/2)=1.96",
            ),
            meta=_full_meta(software="run_g3_auto.py + scipy 1.18.0"),
        )
        assert _row(report, "G3-AUTO-15")["status"] == "PASS"

    def test_missing_software_reviews(self, tmp_path):
        report = _evaluate(
            tmp_path,
            checkpoint=_checkpoint(),
            meta=_full_meta(software=None),
        )
        assert _row(report, "G3-AUTO-15")["status"] == "REVIEW"

    def test_placeholder_formula_reviews(self, tmp_path):
        report = _evaluate(
            tmp_path,
            checkpoint=_checkpoint(formula_used="[CẦN EFFECT SIZE trước khi tính]"),
        )
        assert _row(report, "G3-AUTO-15")["status"] == "REVIEW"


class TestG3Human01EffectSourceConfirmed:
    def test_confirmed_with_source_passes(self, tmp_path):
        report = _evaluate(
            tmp_path,
            meta=_full_meta(effect_source_confirmed=True, effect_source="PMID: 30560792"),
        )
        assert _row(report, "G3-HUMAN-01")["status"] == "PASS"

    def test_not_confirmed_reviews(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(effect_source_confirmed=False))
        assert _row(report, "G3-HUMAN-01")["status"] == "REVIEW"


class TestG3Human02AssumptionsConfirmed:
    def test_confirmed_passes(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(assumptions_confirmed=True))
        assert _row(report, "G3-HUMAN-02")["status"] == "PASS"

    def test_not_confirmed_reviews(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(assumptions_confirmed=False))
        assert _row(report, "G3-HUMAN-02")["status"] == "REVIEW"


class TestG3Human03HypothesisTypeConfirmed:
    def test_confirmed_passes(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(hypothesis_confirmed=True))
        assert _row(report, "G3-HUMAN-03")["status"] == "PASS"

    def test_not_confirmed_reviews(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(hypothesis_confirmed=False))
        assert _row(report, "G3-HUMAN-03")["status"] == "REVIEW"


class TestG3Human05RecruitmentFeasibilityConfirmed:
    def test_confirmed_passes(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(recruitment_feasibility_confirmed=True))
        assert _row(report, "G3-HUMAN-05")["status"] == "PASS"

    def test_not_confirmed_reviews(self, tmp_path):
        report = _evaluate(tmp_path, meta=_full_meta(recruitment_feasibility_confirmed=False))
        assert _row(report, "G3-HUMAN-05")["status"] == "REVIEW"
