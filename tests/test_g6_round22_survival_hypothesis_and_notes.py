"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 22, 2026-07-24, phát hiện HIGH):

hypothesis_type/margin (G3) chỉ được diễn giải cho nhánh kết cục nhị phân/liên
tục (--outcome) — nhánh sống còn (--time/--event, dùng ĐỘC LẬP không cần
--outcome) không hề gọi interpret_hypothesis_type(), dù log đầu main() đã in
"sẽ diễn giải kết cục chính theo khung này" bất kể loại kết cục.

Đồng thời: format_outcome_text()/print ở main() trước đây chỉ hiển thị diễn
giải khi interpret_hypothesis_type() trả về khóa "hypothesis_type" — nhưng 2
nhánh dự phòng của hàm đó (kết cục KHÔNG nhị phân; thiếu margin) chỉ trả
{"note": ...} không có khóa đó, nên cảnh báo "[CẦN...]" bị ÂM THẦM rớt khỏi
file kết quả thật dù đã được tính.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from run_stats_analysis import (  # noqa: E402
    format_outcome_text,
    format_survival_text,
    interpret_hypothesis_type,
)


class TestSurvivalBranchGetsHypothesisNote:
    def test_survival_synthetic_dict_returns_not_supported_note(self):
        interp = interpret_hypothesis_type(
            {"outcome_type": "survival"}, "non_inferiority", 0.15)
        assert "CẦN" in interp["note"]
        assert "sống còn" in interp["note"] or "kết cục liên tục" in interp["note"]

    def test_superiority_survival_returns_empty_no_noise(self):
        interp = interpret_hypothesis_type(
            {"outcome_type": "survival"}, "superiority", None)
        assert interp == {}

    def test_format_survival_text_renders_hypothesis_note_when_present(self):
        surv = {"n": 100, "n_events": 40, "group_col": "arm",
                "crude": {"HR": 0.8, "CI_95": [0.5, 1.2], "p": 0.2, "concordance": 0.6}}
        interp = interpret_hypothesis_type({"outcome_type": "survival"}, "non_inferiority", 0.2)
        txt = format_survival_text(surv, km=None, hypothesis_interp=interp)
        assert "NON_INFERIORITY" in txt or "EQUIVALENCE" in txt
        assert interp["note"] in txt

    def test_format_survival_text_omits_section_for_superiority(self):
        surv = {"n": 100, "n_events": 40, "group_col": "arm",
                "crude": {"HR": 0.8, "CI_95": [0.5, 1.2], "p": 0.2, "concordance": 0.6}}
        txt = format_survival_text(surv, km=None, hypothesis_interp={})
        assert "DIỄN GIẢI" not in txt

    def test_main_source_calls_interpret_hypothesis_type_for_survival_branch(self):
        import inspect
        import run_stats_analysis as RSA
        src = inspect.getsource(RSA)
        assert '{"outcome_type": "survival"}' in src


class TestFormatOutcomeTextDoesNotSilentlyDropFallbackNotes:
    def test_missing_margin_note_still_appears_in_table2(self):
        """Trước vá: interpret_hypothesis_type() trả {"note": "[CẦN...]"} (không
        có khóa "hypothesis_type") khi thiếu margin — format_outcome_text() cũ
        chỉ kiểm .get("hypothesis_type") nên ÂM THẦM bỏ qua dòng cảnh báo này."""
        res = {"outcome_type": "binary", "groups": ["A", "B"],
               "group_0": {"events": 5, "n": 50, "pct": 10.0},
               "group_1": {"events": 6, "n": 50, "pct": 12.0},
               "p_value": 0.7, "test": "chi-square"}
        interp = interpret_hypothesis_type(res, "non_inferiority", None)
        assert "note" in interp and "hypothesis_type" not in interp
        txt = format_outcome_text(res, "outcome", interp)
        assert interp["note"] in txt

    def test_continuous_outcome_not_supported_note_still_appears(self):
        res = {"outcome_type": "continuous", "groups": ["A", "B"],
               "group_0": {"mean": 1.0, "sd": 0.5}, "group_1": {"mean": 1.2, "sd": 0.4},
               "effect": "MD=0.2", "p_value": 0.3, "test": "Welch's t-test"}
        interp = interpret_hypothesis_type(res, "equivalence", 0.3)
        assert "note" in interp and "hypothesis_type" not in interp
        txt = format_outcome_text(res, "outcome", interp)
        assert interp["note"] in txt

    def test_superiority_shows_no_extra_section(self):
        res = {"outcome_type": "binary", "groups": ["A", "B"],
               "group_0": {"events": 5, "n": 50, "pct": 10.0},
               "group_1": {"events": 6, "n": 50, "pct": 12.0},
               "p_value": 0.7, "test": "chi-square"}
        txt = format_outcome_text(res, "outcome", {})
        assert "DIỄN GIẢI" not in txt
