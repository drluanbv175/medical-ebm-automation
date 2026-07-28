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

import run_g1_auto as G1  # noqa: E402
import run_g2_auto as G2  # noqa: E402
import run_g3_auto as G3  # noqa: E402
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


class TestG3SensitivityTableMissingBranches:
    """Hồi quy cho phát hiện HIGH (tái xác minh vòng 6, workflow w6mos9z33):
    sensitivity_table() trước đây trả '100% N/A' cho cross_sectional/diagnostic
    dù N chính đã tính được bình thường qua n_prevalence()/n_auc()."""

    def test_cross_sectional_no_longer_all_na(self):
        rows, _ = G3.sensitivity_table("cross_sectional", 385, 0.30, "ARR%", 0.05, 0.30, 0.30, None)
        all_na = all(cell == "N/A" for _, row in rows for cell in row)
        assert not all_na

    def test_diagnostic_no_longer_all_na(self):
        rows, _ = G3.sensitivity_table("diagnostic", 27, 0.75, "AUC", 0.05, 0.30, 0.30, None)
        all_na = all(cell == "N/A" for _, row in rows for cell in row)
        assert not all_na

    def test_cross_sectional_matches_main_n_prevalence(self):
        rows, _ = G3.sensitivity_table("cross_sectional", 385, 0.30, "ARR%", 0.05, 0.30, 0.30, None)
        base_col_value = rows[0][1][1]  # power=0.70, mult=1.00 (cột giữa)
        assert base_col_value == G3.n_prevalence(0.30, 0.05, 0.05)


class TestG3CohortOrRrNotFedIntoLogRank:
    """Hồi quy cho phát hiện HIGH (tái xác minh vòng 6): nhánh cohort+OR/RR
    trước đây đưa thẳng OR/RR vào n_log_rank() như thể là HR (công thức
    Schoenfeld chỉ đúng cho HR thật) — đánh giá thấp N tới ~41% khi effect
    size là OR. Nay dùng two-proportion (cùng kỹ thuật case_control)."""

    def test_sensitivity_table_cohort_or_no_longer_matches_raw_log_rank(self):
        rows, _ = G3.sensitivity_table("cohort", 220, 0.5, "OR", 0.05, 0.30, 0.30, None)
        base_n = rows[1][1][1]  # power=0.80, mult=1.00 (ev=0.5, không đổi)
        # Hành vi CŨ (sai): đưa thẳng OR=0.5 vào n_log_rank() như HR.
        old_wrong_n_total, _ = G3.n_log_rank(0.5, 0.05, 0.80, 0.30)
        assert base_n != old_wrong_n_total
        assert base_n != "N/A"

    def test_cohort_hr_still_uses_log_rank(self):
        rows, _ = G3.sensitivity_table("cohort", 220, 0.5, "HR", 0.05, 0.30, 0.30, None)
        assert rows[1][1][1] != "N/A"


class TestG3PrevalenceLabelAccurate:
    """Hồi quy cho phát hiện MEDIUM (tái xác minh vòng 6): n_prevalence()
    gắn nhãn "Wilson" nhưng công thức thật là xấp xỉ chuẩn/Cochran cổ điển."""

    def test_docstring_summary_no_longer_claims_wilson(self):
        # Dòng tóm tắt đầu tiên KHÔNG còn tự nhận "(Wilson)" — phần thân
        # docstring vẫn được phép NHẮC tới Wilson để giải thích vì sao nhãn
        # cũ sai (đối chiếu), đó là nội dung hợp lệ, không phải hồi quy.
        first_line = (G3.n_prevalence.__doc__ or "").strip().splitlines()[0]
        assert "Wilson" not in first_line

    def test_formula_value_unchanged_regression_lock(self):
        # Giá trị số KHÔNG đổi (chỉ sửa nhãn) — khóa lại đúng số đã có từ trước.
        assert G3.n_prevalence(0.30, e=0.05, alpha=0.05) == 323


class TestG3SensitivityTableArrClampFlagged:
    """Hồi quy cho phát hiện LOW (tái xác minh vòng 6): sensitivity_table()
    kẹp p2≤0→0.05 ở nhánh ARR% mà không báo hiệu — nay đánh dấu "*"."""

    def test_clamped_cell_is_flagged_with_asterisk(self):
        # p0=0.10, ev=15 (x1.2 = 18) -> p2 = 0.10 - 0.18 < 0 -> phải kẹp.
        rows, _ = G3.sensitivity_table("rct", 100, 15, "ARR%", 0.05, 0.30, 0.10, None)
        flagged_cells = [cell for _, row in rows for cell in row if isinstance(cell, str) and cell.endswith("*")]
        assert flagged_cells, "không có ô nào bị kẹp p2<=0 được đánh dấu trong kịch bản này"


class TestG1SapDoesNotMisapplySrMaToPrediction:
    """Hồi quy cho phát hiện HIGH (tái xác minh vòng 6): SAP §4 trước đây rơi
    vào nhánh else (viết cho sr_ma) cho cả 'prediction' và 'qualitative'."""

    def test_qualitative_sap_is_not_meta_analysis(self):
        design = G1.infer_study_design("qualitative", {}, "nghiên cứu định tính trải nghiệm")
        artifact = G1.generate_g1_artifact("t", "S", "qualitative", design, [], {}, "2026-07-21 10:00")
        assert "DerSimonian-Laird" not in artifact
        assert "Bão hòa dữ liệu" in artifact

    def test_prediction_sap_is_not_meta_analysis(self):
        design = G1.infer_study_design("prediction_model", {}, "phát triển mô hình tiên lượng tử vong")
        artifact = G1.generate_g1_artifact("t", "S", "prediction_model", design, [], {}, "2026-07-21 10:00")
        assert "DerSimonian-Laird" not in artifact
        assert "shrinkage/penalization" in artifact

    def test_prediction_epv_note_is_not_na_sr_ma(self):
        design = G1.infer_study_design("prediction_model", {}, "phát triển mô hình tiên lượng tử vong")
        artifact = G1.generate_g1_artifact("t", "S", "prediction_model", design, [], {}, "2026-07-21 10:00")
        assert "N/A (SR/MA)" not in artifact


class TestG1DesignLabelCoversAllEightCodes:
    """Hồi quy cho phát hiện MEDIUM (tái xác minh vòng 6): _DESIGN_LABEL
    thiếu 'prediction'/'qualitative' — PIN design_code qua study_meta.json
    nhận nhãn generic 'Thiết kế: prediction' thay vì nhãn đầy đủ."""

    def test_prediction_pin_gets_full_label_not_generic(self):
        d = {"primary": "orig", "internal_code": "x", "rationale": "r"}
        result = G1._apply_design_pin(dict(d), "prediction")
        assert result["primary"] != "Thiết kế: prediction"
        assert "Mô hình Tiên lượng" in result["primary"]

    def test_qualitative_pin_gets_full_label_not_generic(self):
        d = {"primary": "orig", "internal_code": "x", "rationale": "r"}
        result = G1._apply_design_pin(dict(d), "qualitative")
        assert result["primary"] != "Thiết kế: qualitative"
        assert "Định tính" in result["primary"]


class TestG2WhoFieldCoversQualitative:
    """Hồi quy cho phát hiện LOW (tái xác minh vòng 6): WHO Trial Registration
    mục Study Type thiếu mã 'qualitative' — nay là Trường 15 theo TRDS 1.3.1."""

    def test_qualitative_primary_purpose_not_other(self):
        doc = G2.generate_g2_full_package(
            topic="Đề tài test", study_name="TEST-STUDY", design_code="qualitative",
            design_primary="Nghiên cứu Định tính (Qualitative Research)",
            reporting_std="SRQR", n_sr=5, n_rct=0, evidence_level="TRUNG BÌNH",
            registry=None, risk=G2.RISK_PROFILES["qualitative"],
            run_date="2026-07-21", n_adjusted=1000,
        )
        import re
        m = re.search(r"Trường 15.*", doc)
        assert m is not None
        assert "Other" not in m.group(0)
