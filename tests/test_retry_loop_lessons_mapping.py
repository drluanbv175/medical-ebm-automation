from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import retry_loop  # noqa: E402


def test_r1b_and_r6_use_distinct_lessons_codes():
    assert retry_loop.to_lesson_code("R1b") == "GAP-LABEL-WASH"
    assert retry_loop.to_lesson_code("R6") == "GAP-MISSING"
    assert retry_loop.to_lesson_code("R1b") != retry_loop.to_lesson_code("R6")


def test_retry_loop_lesson_codes_are_controlled_strings():
    for code, lesson_code in retry_loop.RCODE_TO_LESSON_CODE.items():
        assert code.startswith("R")
        assert lesson_code
        assert lesson_code == lesson_code.upper()
