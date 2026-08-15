"""Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):
tools/run_g8_auto.py::DESIGN_CHECKLIST_MAP trước đây thiếu hẳn khóa
"qualitative" — build_reporting_checklist() fallback về ("STROBE 2007",
STROBE_ITEMS), khiến cổng G8 (bình duyệt/phản biện độc lập trước khi nộp)
kiểm một đề tài định tính bằng 22 mục ngẫu nhiên hóa/mù/phơi nhiễm vô nghĩa
— trong khi run_g1_auto.py và run_g7_auto.py đã gán ĐÚNG chuẩn SRQR 2014
cho thiết kế này từ 2026-07-19.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g8_auto as G8  # noqa: E402


def _item_numbers(items):
    return {int("".join(c for c in num if c.isdigit())) for _name, num, _desc in items}


class TestQualitativeUsesSrqrNotStrobe:
    def test_qualitative_mapped_to_srqr_2014(self):
        std_name, items = G8.DESIGN_CHECKLIST_MAP["qualitative"]
        assert std_name == "SRQR 2014"
        assert items is G8.SRQR_ITEMS

    def test_qualitative_checklist_has_21_items_no_gaps(self):
        assert _item_numbers(G8.SRQR_ITEMS) == set(range(1, 22))

    def test_build_reporting_checklist_uses_srqr_for_qualitative(self):
        result = G8.build_reporting_checklist("qualitative", {})
        assert result["standard_name"] == "SRQR 2014"
        assert result["total"] == 21

    def test_qualitative_checklist_does_not_mention_randomisation_or_blinding(self):
        """Không hồi quy ngược tới STROBE/CONSORT: các mục ngẫu nhiên hóa/mù/
        phơi nhiễm KHÔNG có ý nghĩa với thiết kế định tính."""
        names = " ".join(n.lower() for n, _, _ in G8.SRQR_ITEMS)
        for kw in ("randomis", "blinding", "exposure", "allocation"):
            assert kw not in names

    def test_qualitative_checklist_mentions_trustworthiness_and_sampling(self):
        names = " ".join(n.lower() for n, _, _ in G8.SRQR_ITEMS)
        assert "trustworthiness" in names
        assert "sampling" in names


class TestOtherDesignsUnaffected:
    def test_prediction_still_mapped_to_tripod_ai(self):
        std_name, items = G8.DESIGN_CHECKLIST_MAP["prediction"]
        assert std_name == "TRIPOD+AI 2024"
        assert items is G8.TRIPOD_ITEMS

    def test_cohort_still_mapped_to_strobe(self):
        std_name, items = G8.DESIGN_CHECKLIST_MAP["cohort"]
        assert std_name == "STROBE 2007"
        assert items is G8.STROBE_ITEMS
