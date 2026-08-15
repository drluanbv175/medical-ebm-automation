"""Test cho bundle CRF "patient_satisfaction" + cơ chế needs_vitals của G5
(tools/run_g5_auto.py) — thêm 2026-07-17.

Bug thật phát hiện khi chạy demo đề tài khảo sát hài lòng bệnh nhân C1a,
BVQY175: chủ đề không khớp chuyên khoa nào → rơi về "generic", nhưng
_BASE_VITALS (huyết áp tâm thu, nhịp tim) trước đây bị nhồi CỨNG vào MỌI
thiết kế bất kể chuyên khoa/bundle — CRF của một khảo sát hài lòng (không hề
đo sinh hiệu) vẫn có 2 trường huyết áp/nhịp tim bắt buộc, đúng lý do bác sĩ
đánh giá "đề cương không đảm bảo".

Test này khóa 2 việc: (1) chủ đề khảo sát hài lòng chọn đúng bundle
"patient_satisfaction" với các trường lĩnh vực hài lòng, KHÔNG còn sinh hiệu;
(2) needs_vitals mặc định True nên các bundle lâm sàng hiện có (vd
cardiology_hf) giữ nguyên hành vi cũ — không bị đổi ngầm bởi cơ chế mới.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g5_auto import _SPECIALTY_BUNDLES, build_redcap_rows  # noqa: E402

_SATISFACTION_TOPIC = (
    "Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại "
    "Khoa Khám bệnh C1a, Bệnh viện Quân y 175"
)


def _field_names(rows):
    return [r[0] for r in rows]


class TestPatientSatisfactionBundleExcludesVitals:
    def test_satisfaction_topic_picks_patient_satisfaction_specialty(self):
        _, specialty = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        assert specialty == "patient_satisfaction"

    def test_no_blood_pressure_or_heart_rate_fields(self):
        """Hồi quy trực tiếp: đúng bug thật — CRF khảo sát hài lòng từng có
        bp_sys/bp_dia/heart_rate vô nghĩa."""
        rows, _ = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        names = _field_names(rows)
        for vital in ("bp_sys", "bp_dia", "heart_rate"):
            assert vital not in names, f"CRF khảo sát hài lòng vẫn còn trường sinh hiệu '{vital}'"

    def test_includes_satisfaction_domain_fields(self):
        rows, _ = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        names = _field_names(rows)
        for expected in (
            "domain_access_score",
            "domain_transparency_score",
            "domain_facility_score",
            "domain_staff_attitude_score",
            "domain_service_result_score",
            "overall_satisfaction_score",
            "overall_satisfaction_binary",
        ):
            assert expected in names, f"Thiếu trường lĩnh vực hài lòng '{expected}'"

    def test_includes_visit_context_fields(self):
        rows, _ = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        names = _field_names(rows)
        for expected in ("visit_type", "payment_type", "wait_time_min", "visit_freq_year"):
            assert expected in names

    def test_no_undisclosed_comorbidity_or_lab_fields(self):
        """Hồi quy trực tiếp (bình duyệt agent dao-duc-dang-ky phát hiện thật,
        2026-07-17): PICO của khảo sát hài lòng không liệt kê bệnh nền là yếu
        tố liên quan, và ICF không công bố sẽ thu thông tin này — CRF từng
        vẫn có dm/htn/comorbid_other/labs_other qua _GENERIC_COMORBIDITIES/
        _GENERIC_LABS, vi phạm nguyên tắc tối thiểu hóa dữ liệu."""
        rows, _ = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        names = _field_names(rows)
        for undisclosed in ("dm", "htn", "comorbid_other", "labs_other"):
            assert undisclosed not in names, (
                f"CRF khảo sát hài lòng vẫn còn trường bệnh nền không công bố '{undisclosed}'"
            )

    def test_no_duplicate_field_names(self):
        rows, _ = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        names = _field_names(rows)
        assert len(names) == len(set(names)), "CRF có tên trường trùng lặp"

    def test_all_rows_have_12_columns(self):
        rows, _ = build_redcap_rows("cross_sectional", _SATISFACTION_TOPIC)
        for row in rows:
            assert len(row) == 12, f"Dòng CRF sai số cột (schema 12 trường): {row[0]}"


class TestNeedsVitalsDoesNotRegressExistingSpecialties:
    """needs_vitals mặc định True (qua .get) — bundle lâm sàng hiện có KHÔNG
    được đổi hành vi ngầm bởi cơ chế mới thêm cho patient_satisfaction."""

    def test_existing_bundles_default_needs_vitals_true(self):
        for specialty, bundle in _SPECIALTY_BUNDLES.items():
            if specialty == "patient_satisfaction":
                continue
            assert bundle.get("needs_vitals", True) is True, (
                f"Bundle '{specialty}' không còn mặc định needs_vitals=True"
            )

    def test_cardiology_hf_still_has_vitals(self):
        rows, specialty = build_redcap_rows(
            "cohort", "Nghiên cứu về suy tim HFpEF ở người cao tuổi"
        )
        assert specialty == "cardiology_hf"
        names = _field_names(rows)
        assert "bp_sys" in names
        assert "heart_rate" in names

    def test_generic_still_has_vitals(self):
        rows, specialty = build_redcap_rows(
            "cross_sectional", "Đánh giá hiệu quả một loại vitamin tổng hợp"
        )
        assert specialty == "generic"
        names = _field_names(rows)
        assert "bp_sys" in names
        assert "heart_rate" in names

    def test_patient_satisfaction_explicitly_opts_out(self):
        assert _SPECIALTY_BUNDLES["patient_satisfaction"]["needs_vitals"] is False
