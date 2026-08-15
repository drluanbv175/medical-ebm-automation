"""Hồi quy cổng G6 (2026-07-29, vòng 3) — 2 phát hiện từ lăng kính "đúng thiết kế"
của workflow soi G6, tự tay xác nhận bằng đọc mã nguồn trước khi vá.

F4 — Nhánh diagnostic (`_r03_diagnostic_with_vars`) chỉ tính Se/Sp/AUC qua
`pROC::coords()`/`ci.coords()`, KHÔNG sinh bảng chéo 2×2 (TP/FP/FN/TN) nào.
STARD 2015 mục 23 đòi CHÍNH XÁC "Cross tabulation of the index test results (or
their distribution) by the results of the reference standard" — một bảng THÔ
độc lập, không suy ra được chỉ bằng cách đọc summary() của ROC object. Đây còn
là mâu thuẫn nội bộ: G1 (`g1_design_blocks.py::_TABLES_DIAGNOSTIC`) đã hứa sẵn
"BẢNG 2 — Bảng chéo 2×2" trong dummy tables, nhưng G6 không sinh code để điền.

F5 — Bốn nhánh hồi quy đa biến (cohort, cross_sectional, case_control,
prediction) không có dòng code nào tính VIF, dù chính SAP §5 mà hệ sinh ra
("Kiểm đa cộng tuyến: VIF < 5 cho mọi biến") đã hứa. Riêng RCT (cũng dùng
`coxph()` như cohort) còn thiếu cả kiểm định PH assumption (`cox.zph()`) mà
cohort đã có sẵn — hai thiết kế dùng CHUNG một mô hình nhưng chỉ một bên được
kiểm tra giả định.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO), str(_REPO / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_g6_auto as G6  # noqa: E402

_V = {
    "exposure": "phoi_nhiem",
    "outcome": "ket_cuc",
    "time_col": "thoi_gian",
    "covariates": ["tuoi", "gioi"],
    "all_vars": ["ma_bn", "tuoi", "gioi", "phoi_nhiem", "ket_cuc", "thoi_gian"],
    "detection_log": [],
}


class TestBangCheo2x2ChoDoChinhXacChanDoan:
    def test_co_bang_cheo_2x2(self):
        code = G6._r03_diagnostic_with_vars(_V)
        assert "table_2x2" in code
        assert 'table(Index_test' in code

    def test_co_du_bon_o_tp_fp_fn_tn(self):
        code = G6._r03_diagnostic_with_vars(_V)
        for cell in ('TP <-', 'FP <-', 'FN <-', 'TN <-'):
            assert cell in code, f"thiếu ô {cell!r} — bảng 2x2 không đầy đủ"

    def test_nhac_dung_muc_stard(self):
        code = G6._r03_diagnostic_with_vars(_V)
        assert "STARD 2015 mục 23" in code

    def test_khong_lam_mat_tinh_toan_roc_da_co(self):
        """Không được xóa mất phần Se/Sp/AUC/CI đã có khi thêm bảng 2x2."""
        code = G6._r03_diagnostic_with_vars(_V)
        assert "pROC::roc(" in code
        assert "ci.coords" in code


class TestKiemDinhGiaDinhMoHinhHoiQuyDaBien:
    """SAP §5 hứa 'VIF < 5 cho mọi biến' — 4 nhánh hồi quy đa biến phải có
    dòng code thật, không chỉ nằm trong checklist văn bản của artifact .md."""

    def test_cohort_co_vif(self):
        code = G6.make_r03_cohort(_V, 2, 0.05, 0.8, 0.7, "HR")
        assert "car::vif(" in code

    def test_cohort_van_giu_ph_check_da_co_tu_truoc(self):
        code = G6.make_r03_cohort(_V, 2, 0.05, 0.8, 0.7, "HR")
        assert "cox.zph" in code

    def test_cross_sectional_co_vif(self):
        code = G6._r03_cross_with_vars(_V)
        assert "car::vif(" in code

    def test_cross_sectional_co_hosmer_lemeshow(self):
        """generalhoslem::logitgof() — xác minh là gói R THẬT trên CRAN
        (Jay M, "Goodness of Fit Tests for Logistic Regression Models") trước
        khi thêm, tránh tái diễn lỗi trích dẫn gói bịa (vd 'giả::val.prob')."""
        code = G6._r03_cross_with_vars(_V)
        assert "generalhoslem::logitgof(" in code

    def test_case_control_co_vif(self):
        code = G6._r03_case_control_with_vars(_V)
        assert "car::vif(" in code

    def test_prediction_co_vif_truoc_shrinkage(self):
        code = G6._r03_prediction_with_vars(_V)
        assert "car::vif(model_full)" in code


class TestRctKhongConMienKiemDinhPh:
    """RCT và cohort đều dùng coxph() — không có lý do RCT được miễn kiểm PH."""

    def test_rct_co_cox_zph(self):
        code = G6._r03_rct_with_vars(_V)
        assert "cox.zph" in code

    def test_rct_co_vif(self):
        code = G6._r03_rct_with_vars(_V)
        assert "car::vif(" in code

    def test_sr_ma_va_qualitative_khong_bi_them_kiem_dinh_hoi_quy_sai_cho(self):
        """Chống sửa quá tay: SR/MA và định tính không có mô hình hồi quy nào
        — không được thêm VIF/cox.zph cho hai thiết kế này."""
        sr_ma_code = G6._r03_srma_template()
        qual_code = G6._r03_qualitative_template()
        for code in (sr_ma_code, qual_code):
            assert "car::vif(" not in code
            assert "cox.zph(" not in code
