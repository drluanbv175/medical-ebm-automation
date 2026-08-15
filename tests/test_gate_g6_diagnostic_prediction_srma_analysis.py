"""Hồi quy (audit vòng 3, 2026-07-19, D2_prediction_dta_gate_coverage — NGHIÊM
TRỌNG): R_ANALYSIS_MAP_FUNC() sinh 03_analysis.R SAI HOÀN TOÀN cho design_code
"diagnostic"/"prediction"/"sr_ma" — cả 3 rơi vào nhánh `else` → make_r03_cohort()
(Cox regression + Kaplan-Meier), dù không thiết kế nào trong 3 có trục thời
gian-đến-biến-cố hợp lệ theo nghĩa Cox. Mâu thuẫn nội tại: TABLE_SHELLS/
analysis_name_map (đã vá 2026-07-17) ghi đúng ROC/AUC+DCA (diagnostic),
TRIPOD+AI (prediction), PRISMA meta-analysis (sr_ma) — nhưng 03_analysis.R thực
tế lại dạy Cox/HR, y hệt lớp lỗi "2 lớp xử lý design_code tách rời" mà
case_control từng gặp (2026-07-06, xem test_gate_g6_g7_md_dispatch.py).

Đã vá: thêm 3 nhánh riêng trong R_ANALYSIS_MAP_FUNC() — _r03_diagnostic_with_vars
(ROC/AUC + Se/Sp tại ngưỡng Youden, KHÔNG Cox), _r03_prediction_with_vars (TRIPOD+AI:
mô hình đa biến + shrinkage + bootstrap internal validation + calibration + DCA,
theo Riley RD et al. BMJ 2020;368:m441), _r03_srma_template (meta::metabin/metagen
random-effects trên bảng STUDY-LEVEL — KHÁC HẲN 6 thiết kế còn lại, không nhận `v`
participant-level).
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402

_V = {
    "exposure": "index_test_positive",
    "outcome": "disease_confirmed_biopsy",
    "time_col": "followup_months",
    "covariates": ["age", "sex", "bmi"],
    "detection_log": ["test"],
}


def _uncommented_call(script: str, fn_name: str) -> bool:
    """True nếu `fn_name(` xuất hiện ở ĐẦU một dòng KHÔNG bắt đầu bằng '#'
    (code thật đang thực thi), bỏ qua mọi dòng comment/hướng dẫn."""
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if f"{fn_name}(" in stripped:
            return True
    return False


class TestG6DiagnosticAnalysis:
    def test_diagnostic_uses_roc_auc_not_cox(self):
        script = G6.R_ANALYSIS_MAP_FUNC("diagnostic", _V, 100, 0.05, 0.80, 0.80, "AUC")
        assert "pROC::roc" in script or "roc(" in script
        assert "Youden" in script or "youden" in script
        assert not _uncommented_call(script, "coxph")
        assert not _uncommented_call(script, "Surv")

    def test_diagnostic_mentions_index_test_and_reference_standard_vars(self):
        script = G6.R_ANALYSIS_MAP_FUNC("diagnostic", _V, 100, 0.05, 0.80, 0.80, "AUC")
        assert _V["exposure"] in script
        assert _V["outcome"] in script


class TestG6PredictionAnalysis:
    def test_prediction_uses_tripod_ai_workflow_not_plain_cox(self):
        script = G6.R_ANALYSIS_MAP_FUNC("prediction", _V, 100, 0.05, 0.80, None, "HR")
        assert "TRIPOD" in script
        assert "rms::validate" in script or "validate(" in script
        assert "glmnet" in script or "shrinkage" in script.lower()
        assert "dca(" in script.lower() or "decision curve" in script.lower()
        # Cox có thể XUẤT HIỆN như một lựa chọn (nếu kết cục là time-to-event)
        # nhưng CHỈ trong comment hướng dẫn — không phải lệnh thực thi trần trụi
        # như make_r03_cohort() sinh ra.
        assert not _uncommented_call(script, "coxph")

    def test_prediction_mentions_riley_2020_pmid(self):
        script = G6.R_ANALYSIS_MAP_FUNC("prediction", _V, 100, 0.05, 0.80, None, "HR")
        assert "32188600" in script  # PMID Riley RD et al. BMJ 2020;368:m441


class TestG6SrmaAnalysis:
    def test_srma_uses_meta_package_not_cox(self):
        script = G6.R_ANALYSIS_MAP_FUNC("sr_ma", _V, 0, 0.05, 0.80, None, "HR")
        assert "metabin" in script or "metagen" in script
        assert not _uncommented_call(script, "coxph")
        assert not _uncommented_call(script, "glm")

    def test_srma_clarifies_study_level_not_participant_level(self):
        """Khác biệt cấu trúc quan trọng nhất: sr_ma phân tích bảng NGHIÊN CỨU,
        không phải bảng BỆNH NHÂN — script phải nói rõ để không nhầm dùng REDCap
        participant-level df."""
        script = G6.R_ANALYSIS_MAP_FUNC("sr_ma", _V, 0, 0.05, 0.80, None, "HR")
        assert "STUDY-LEVEL" in script or "study-level" in script.lower()


class TestG6OtherDesignsUnaffected:
    """Đối chứng: thêm 3 nhánh mới KHÔNG được đè lên các thiết kế đã đúng từ trước."""

    def test_cohort_still_uses_cox(self):
        script = G6.R_ANALYSIS_MAP_FUNC("cohort", _V, 100, 0.05, 0.80, 0.7, "HR")
        assert _uncommented_call(script, "make_r03_cohort") or "coxph" in script

    def test_case_control_still_uses_logistic_not_cox(self):
        script = G6.R_ANALYSIS_MAP_FUNC("case_control", _V, 100, 0.05, 0.80, 1.5, "OR")
        assert not _uncommented_call(script, "coxph")

    def test_rct_still_uses_cox_or_continuous(self):
        script = G6.R_ANALYSIS_MAP_FUNC("rct", _V, 100, 0.05, 0.80, 0.7, "HR")
        assert "coxph" in script or "Surv(" in script
