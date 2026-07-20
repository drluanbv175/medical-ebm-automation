"""Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21): dòng
"Effect size" trong SAP (A5) của tools/run_g4_auto.py trước đây dùng CHUNG
điều kiện `n_not_applicable` với dòng "Cỡ mẫu" — cờ này False ngay khi bác
sĩ xác nhận N qua `--confirmed-n` (n_adjusted khác 0), dù thiết kế
(sr_ma/prediction/qualitative) KHÔNG BAO GIỜ dùng effect_size. Hậu quả: một
"[CẦN từ G3]" vĩnh viễn không thể giải, hoặc một effect_val/effect_type còn
sót từ vòng scrape G1 bị in ra như một con số hợp lệ.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g4_auto import generate  # noqa: E402


def _sap_text(design_code, n_adjusted, effect_val=None, effect_type=None):
    return generate(
        study="DEMO",
        topic="Đề tài demo",
        design_code=design_code,
        design_primary=design_code,
        reporting_std="[CẦN]",
        n_adjusted=n_adjusted,
        alpha=0.05,
        power=0.8,
        effect_val=effect_val,
        effect_type=effect_type,
        run_date="2026-07-21",
    )


class TestEffectSizeAlwaysNAForDesignsThatNeverUseIt:
    """Effect size phải LUÔN N/A cho sr_ma/prediction/qualitative, kể cả khi
    N đã được bác sĩ chốt qua --confirmed-n (n_adjusted khác 0)."""

    def test_qualitative_effect_size_na_even_with_confirmed_n(self):
        text = _sap_text("qualitative", n_adjusted=20)
        assert "Effect size:** N/A" in text
        assert "[CẦN từ G3]" not in text.split("Effect size")[1][:60]

    def test_sr_ma_effect_size_na_even_with_confirmed_n(self):
        text = _sap_text("sr_ma", n_adjusted=15)
        assert "Effect size:** N/A" in text

    def test_prediction_effect_size_na_even_with_confirmed_n(self):
        text = _sap_text("prediction", n_adjusted=500)
        assert "Effect size:** N/A" in text

    def test_qualitative_effect_size_na_even_with_stale_leftover_effect_val(self):
        """Kịch bản lỗi cụ thể từ audit: effect_val/effect_type còn sót từ G1
        scrape không được in ra như một con số hợp lệ cho thiết kế định tính."""
        text = _sap_text("qualitative", n_adjusted=20, effect_val=1.45, effect_type="HR")
        assert "HR = 1.45" not in text
        assert "Effect size:** N/A" in text

    def test_cỡ_mẫu_still_shows_real_n_once_confirmed(self):
        """Không hồi quy ngược: dòng 'Cỡ mẫu' (khác 'Effect size') vẫn phải
        hiện N thật một khi đã confirmed_n, không bị khóa cứng N/A."""
        text = _sap_text("qualitative", n_adjusted=20)
        assert "Cỡ mẫu cuối:** N = 20" in text


class TestEffectSizeStillPopulatedForQuantitativeDesigns:
    def test_cohort_effect_size_shows_real_value(self):
        text = _sap_text("cohort", n_adjusted=200, effect_val=1.8, effect_type="HR")
        assert "HR = 1.80" in text

    def test_cohort_effect_size_shows_todo_when_missing(self):
        text = _sap_text("cohort", n_adjusted=200)
        assert "Effect size:** [CẦN từ G3]" in text
