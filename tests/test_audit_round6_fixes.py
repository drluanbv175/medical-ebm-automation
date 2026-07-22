"""Hồi quy cho phát hiện HIGH từ vòng lặp kiểm tra-hoàn thiện vòng 6
(2026-07-21, workflow đối kháng wf_8e2830c1-fa1): doctrine mo-hinh-tien-luong.md
(M7) yêu cầu kiểm định NGOẠI (external validation) là "Bắt buộc" cho mô hình
tiên lượng, nhưng tools/run_g6_auto.py::_r03_prediction_with_vars() (sinh
03_analysis.R cho thiết kế 'prediction') trước đây không có mục nào — kể cả
comment hướng dẫn — cho bước này (grep "ngoại"/"external" trên toàn file cho
0 kết quả)."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402


def _minimal_prediction_vars():
    return {
        "exposure": "exposure_var",
        "outcome": "primary_outcome",
        "time_col": "time_to_event",
        "covariates": ["age", "sex", "bmi"],
        "detection_log": [],
    }


class TestPredictionExternalValidation:
    def test_generated_script_mentions_external_validation(self):
        script = G6._r03_prediction_with_vars(_minimal_prediction_vars())
        lowered = script.lower()
        assert "external" in lowered or "ngoại" in lowered

    def test_generated_script_uses_val_prob_on_a_separate_dataset(self):
        script = G6._r03_prediction_with_vars(_minimal_prediction_vars())
        assert "df_external" in script
        assert "val.prob(pred_external" in script

    def test_final_message_flags_external_validation_requirement(self):
        script = G6._r03_prediction_with_vars(_minimal_prediction_vars())
        assert "kiểm định NGOẠI" in script or "external" in script.lower()
