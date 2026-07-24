"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 20, 2026-07-24, phát hiện HIGH x3):

tools/run_g5_auto.py có 3 khoảng trống cùng lớp "add a field upstream, forget
to wire it to every consumer" đã lặp lại nhiều vòng trong chiến dịch audit này:

1. build_redcap_rows() có nhánh riêng cho qualitative/sr_ma/rct/diagnostic/
   prediction nhưng KHÔNG có nhánh nào cho design_code="economic" — rơi vào
   nhánh mặc định cohort/case_control/cross_sectional, sinh CRF LÂM SÀNG cho
   bệnh nhân cá thể thay vì các trường CHEERS 2022 (góc nhìn, chi phí, thỏa
   dụng/QALY, mô hình hóa) mà run_g7_auto.py đã cam kết báo cáo.
2. main() không đọc specialist_modules (G1) — khi "economic" là cấu phần
   CỘNG THÊM (design_code chính khác "economic"), CRF không có field kinh tế
   y tế nào dù run_g7_auto.py/run_g8_auto.py/run_g9_auto.py đã nối checklist
   tương ứng.
3. main() không đọc hypothesis_type/margin (G3) — PHẦN 8 (checklist khóa DB)
   không nhắc quần thể ITT/PP phải chốt TRƯỚC khi khóa DB cho đề tài
   non-inferiority/equivalence (CONSORT-NI/Equivalence, Piaggio 2012,
   doi:10.1001/jama.2012.87802) — khác ITT/PP có thể đảo chiều kết luận.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g5_auto as G5  # noqa: E402

_TOPIC = "Phân tích chi phí-hiệu quả điều trị ARV thế hệ mới ở bệnh nhân HIV"

# Trường lâm sàng cá thể KHÔNG nên xuất hiện trong CRF kinh tế y tế thuần túy.
_CLINICAL_ONLY_FIELDS = ("bp_sys", "bp_dia", "heart_rate", "egfr", "hba1c")

_ECONOMIC_ONLY_FIELDS = (
    "perspective", "time_horizon", "discount_rate", "cost_category",
    "unit_cost_value", "unit_cost_source", "utility_instrument", "model_type",
)


class TestEconomicDesignCodeBranch:
    def test_economic_design_returns_cheers_fields(self):
        rows, _ = G5.build_redcap_rows("economic", _TOPIC)
        names = [r[0] for r in rows]
        for f in _ECONOMIC_ONLY_FIELDS:
            assert f in names, f"CRF kinh tế y tế thiếu trường '{f}'"

    def test_economic_design_has_no_individual_clinical_fields(self):
        rows, _ = G5.build_redcap_rows("economic", _TOPIC)
        names = [r[0] for r in rows]
        for f in _CLINICAL_ONLY_FIELDS:
            assert f not in names, f"CRF kinh tế y tế lẫn trường lâm sàng cá thể '{f}'"

    def test_economic_design_no_duplicate_fields(self):
        rows, _ = G5.build_redcap_rows("economic", _TOPIC)
        names = [r[0] for r in rows]
        assert len(names) == len(set(names))

    def test_economic_unit_cost_flags_needs_source_not_fabricated(self):
        rows, _ = G5.build_redcap_rows("economic", _TOPIC)
        by_name = {r[0]: r for r in rows}
        assert "[CẦN NGUỒN" in by_name["unit_cost_source"][6] or \
               "[CẦN NGUỒN" in by_name["unit_cost_value"][6]


class TestEconomicAsAddOnSpecialistModule:
    """specialist_modules=['economic'] cộng thêm khi design_code chính KHÔNG
    phải 'economic' (vd RCT có tiểu mục chi phí-hiệu quả) — nối THÊM, không
    thay thế, cùng khuôn run_g7_auto.py/run_g8_auto.py/run_g9_auto.py."""

    def test_main_source_reads_specialist_modules_from_g1(self):
        src = inspect.getsource(G5)
        assert 'g1.get("specialist_modules")' in src

    def test_main_source_appends_economic_fields_when_not_primary_design(self):
        src = inspect.getsource(G5)
        assert '"economic" in specialist_modules' in src
        assert 'design_code != "economic"' in src


class TestHypothesisTypeMarginPropagation:
    def _artifact(self, hypothesis_type=None, margin=None):
        rows, specialty = G5.build_redcap_rows("rct", "Thử nghiệm so sánh 2 phác đồ")
        return G5.generate_artifact(
            "TEST-STUDY", "Test topic", "rct",
            100, 100, 50, "2026-07-24", rows, specialty,
            hypothesis_type=hypothesis_type, margin=margin,
        )

    def test_non_inferiority_adds_itt_pp_lock_reminder(self):
        artifact = self._artifact(hypothesis_type="non_inferiority", margin=0.10)
        assert "ITT" in artifact and "Per-Protocol" in artifact
        assert "non_inferiority" in artifact
        assert "0.1" in artifact

    def test_equivalence_also_adds_reminder(self):
        artifact = self._artifact(hypothesis_type="equivalence", margin=0.15)
        assert "ITT" in artifact and "Per-Protocol" in artifact

    def test_default_superiority_has_no_extra_reminder(self):
        artifact = self._artifact()
        assert "Per-Protocol (PP), " not in artifact

    def test_missing_margin_flagged_not_fabricated(self):
        artifact = self._artifact(hypothesis_type="non_inferiority", margin=None)
        assert "[CẦN — chưa ghi ở G3]" in artifact

    def test_main_source_reads_hypothesis_type_and_margin_from_g3(self):
        src = inspect.getsource(G5)
        assert 'g3.get("hypothesis_type")' in src
        assert 'g3.get("margin")' in src
