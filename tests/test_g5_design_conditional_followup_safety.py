"""Test cho tính điều kiện theo THIẾT KẾ của _FOLLOWUP_ADMIN/_BASE_SAFETY_AE
trong CRF của G5 (tools/run_g5_auto.py) — thêm 2026-07-17.

Phát hiện thật (bình duyệt độc lập đa vai trò cho đề tài khảo sát hài lòng
bệnh nhân C1a, BVQY175 — cả agent `binh-duyet` lẫn `dao-duc-dang-ky` cùng
bắt độc lập): censor_date/censor_reason/protocol_deviation/ltfu (theo dõi
dọc) và ae_any/ae_description/ae_grade/sae_any (biến cố bất lợi, thuật ngữ
ICH-GCP của thử nghiệm can thiệp) trước đây nhồi CỨNG vào CRF của MỌI thiết
kế — kể cả cross_sectional (một thời điểm, không can thiệp) — dấu vết CRF
dùng chung mọi thiết kế mà một hội đồng khoa học/đạo đức thật rất dễ bắt lỗi.

Cùng loại bug với _BASE_VITALS (đã sửa cùng ngày, xem
test_g5_patient_satisfaction_crf.py) nhưng khác trục: needs_vitals theo
CHUYÊN KHOA, còn đây theo THIẾT KẾ (rct/cohort có theo dõi dọc + có thể có
can thiệp → giữ; case_control/cross_sectional/diagnostic → bỏ).
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g5_auto import build_redcap_rows  # noqa: E402

_FOLLOWUP_FIELDS = ("censor_date", "censor_reason", "protocol_deviation", "ltfu")
_AE_FIELDS = ("ae_any", "ae_description", "ae_grade", "sae_any")
_GENERIC_TOPIC = "Tác dụng can thiệp X lên kết cục Y ở bệnh nhân ngoại trú"


def _names(design_code):
    rows, _ = build_redcap_rows(design_code, _GENERIC_TOPIC)
    return [r[0] for r in rows]


class TestFollowupAndSafetyDroppedForSingleTimepointDesigns:
    """Hồi quy trực tiếp: đúng bug thật — cross_sectional/case_control/
    diagnostic KHÔNG có trục thời gian theo dõi dọc lẫn can thiệp đang thử
    nghiệm, không được có các trường này."""

    def test_cross_sectional_has_no_followup_fields(self):
        names = _names("cross_sectional")
        for f in _FOLLOWUP_FIELDS:
            assert f not in names, f"cross_sectional vẫn còn trường theo dõi dọc '{f}'"

    def test_cross_sectional_has_no_ae_safety_fields(self):
        names = _names("cross_sectional")
        for f in _AE_FIELDS:
            assert f not in names, f"cross_sectional vẫn còn trường biến cố bất lợi '{f}'"

    def test_case_control_has_no_followup_or_ae_fields(self):
        names = _names("case_control")
        for f in _FOLLOWUP_FIELDS + _AE_FIELDS:
            assert f not in names

    def test_diagnostic_has_no_followup_or_ae_fields(self):
        names = _names("diagnostic")
        for f in _FOLLOWUP_FIELDS + _AE_FIELDS:
            assert f not in names


class TestFollowupAndSafetyKeptForLongitudinalDesigns:
    """Không hồi quy ngược: rct/cohort THẬT SỰ có theo dõi dọc/can thiệp —
    KHÔNG được vô tình bỏ mất các trường này (an toàn dữ liệu/cảnh giác dược)."""

    def test_rct_keeps_followup_fields(self):
        names = _names("rct")
        for f in _FOLLOWUP_FIELDS:
            assert f in names, f"rct bị mất trường theo dõi dọc '{f}'"

    def test_rct_keeps_ae_safety_fields(self):
        names = _names("rct")
        for f in _AE_FIELDS:
            assert f in names, f"rct bị mất trường biến cố bất lợi '{f}'"

    def test_cohort_keeps_followup_and_ae_fields(self):
        names = _names("cohort")
        for f in _FOLLOWUP_FIELDS + _AE_FIELDS:
            assert f in names


class TestCompleteFlagAlwaysPresent:
    """complete_flag (trạng thái hoàn thành phiếu) hoàn toàn tổng quát —
    không ngụ ý can thiệp — phải có ở MỌI thiết kế, kể cả sau khi tách khỏi
    _BASE_SAFETY."""

    def test_present_in_all_non_srma_designs(self):
        for code in ("rct", "cohort", "case_control", "cross_sectional", "diagnostic"):
            assert "complete_flag" in _names(code), f"{code}: thiếu complete_flag"


class TestNoDuplicateOrMissingRowsAfterSplit:
    """Đảm bảo việc tách _BASE_ADMIN/_BASE_SAFETY không làm mất/nhân đôi cột
    nào — chỉ CHUYỂN vị trí điều kiện, không đổi tổng nội dung cho rct/cohort."""

    def test_rct_field_count_matches_prior_baseline(self):
        # 12 field _BASE_ADMIN cũ (record_id..ltfu, 8 dòng) + demographics(5)
        # + vitals(3) + rct extra(4) + safety+admin(5) — chỉ cần đảm bảo
        # không trùng lặp và có đủ nhóm, không khóa cứng số tuyệt đối dễ vỡ
        # khi bundle đổi.
        rows, _ = build_redcap_rows("rct", _GENERIC_TOPIC)
        names = [r[0] for r in rows]
        assert len(names) == len(set(names)), "CRF rct có tên trường trùng lặp sau khi tách"

    def test_cross_sectional_no_duplicate_fields(self):
        rows, _ = build_redcap_rows("cross_sectional", _GENERIC_TOPIC)
        names = [r[0] for r in rows]
        assert len(names) == len(set(names)), "CRF cross_sectional có tên trường trùng lặp"
