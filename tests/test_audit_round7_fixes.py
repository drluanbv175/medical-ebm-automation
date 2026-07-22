"""Hồi quy cho phát hiện CRITICAL từ vòng lặp kiểm tra-hoàn thiện vòng 7
(2026-07-22, workflow đối kháng wf_b8f5e3bd-daf): build_redcap_rows() trước
đây KHÔNG có nhánh riêng cho design_code="prediction" — rơi vào else (cohort/
case_control/cross_sectional), sinh CRF dùng bundle["exposure"]/["outcomes"]
kiểu cohort, KHÔNG có cờ tách tập phát triển/đánh giá (TRIPOD+AI).

(Các phát hiện khác của vòng 7 chạm EBM_MASTER/tools/integrity_guard.py —
ROOT gitignored, ngoài phạm vi pytest, đã xác minh riêng bằng script thực
nghiệm, xem commit message.)
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g5_auto as G5  # noqa: E402


class TestG5PredictionBranch:
    def test_prediction_gets_own_form_not_cohort_fallback(self):
        rows, specialty = G5.build_redcap_rows(
            "prediction",
            "Xây dựng và đánh giá mô hình tiên lượng tử vong 1 năm sau nhồi máu cơ tim (TRIPOD+AI)",
        )
        forms = sorted(set(r[1] for r in rows))
        assert "Prediction" in forms

    def test_prediction_has_dataset_split_field(self):
        rows, _ = G5.build_redcap_rows("prediction", "mô hình tiên lượng tái nhập viện")
        field_names = [r[0] for r in rows]
        assert "dataset_split" in field_names

    def test_prediction_differs_from_cohort_row_set(self):
        pred_rows, _ = G5.build_redcap_rows("prediction", "mô hình tiên lượng tử vong")
        cohort_rows, _ = G5.build_redcap_rows("cohort", "mô hình tiên lượng tử vong")
        pred_fields = {r[0] for r in pred_rows}
        cohort_fields = {r[0] for r in cohort_rows}
        assert pred_fields != cohort_fields
        assert "dataset_split" in pred_fields
        assert "dataset_split" not in cohort_fields

    def test_prediction_gets_followup_admin(self):
        # prediction du bao ket cuc TUONG LAI -> can truc thoi gian theo doi.
        rows, _ = G5.build_redcap_rows("prediction", "mô hình tiên lượng tử vong 1 năm")
        forms = [r[1] for r in rows]
        assert "Followup" in forms or any("follow" in r[0].lower() for r in rows)
