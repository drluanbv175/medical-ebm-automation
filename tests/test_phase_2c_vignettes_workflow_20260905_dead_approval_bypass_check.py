"""Hồi quy phát hiện #1 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 15) trong
app/clinical_content/phase_2c_vignettes.py::evaluate_phase_2c_vignettes().

CƠ CHẾ LỖI: khóa "approval_bypass" trong `non_negotiable` được khởi tạo 0
nhưng KHÔNG có nhánh nào trong vòng lặp từng tăng nó — `Phase2CVignette`
không có field nào biểu diễn "được duyệt/bỏ qua duyệt" để có thể kiểm.
Hậu quả: `non_negotiable["approval_bypass"]` LUÔN LUÔN = 0 với BẤT KỲ
input nào, khiến `Phase2CVignetteReport.passed` (all(value == 0 ...))
không bao giờ phát hiện được một kịch bản approval-bypass thật. Đây
không chỉ là lỗi test nội bộ: `docs/system-v7/PHASE_2C_SYNTHETIC_
VIGNETTE_REPORT.md` (báo cáo bằng chứng governance đã publish) trích dẫn
nguyên văn `approval_bypass = 0` như một tiêu chí ĐÃ ĐƯỢC KIỂM CHỨNG,
trong khi phép kiểm đó không hề tồn tại.

BẢN VÁ: bất biến thật của pathway là mọi vignette CHỈ được phép có
`expected_action_class` thuộc {draft_review, block, urgent_referral} —
không hành động nào được tự áp dụng mà bỏ qua bác sĩ review. Một
action_class ngoài tập này là bằng chứng approval-bypass.

Nguyên tắc viết test: gọi THẲNG `evaluate_phase_2c_vignettes()` thật với
`Phase2CVignette` dựng tay (input cụ thể mô phỏng bypass), đối chiếu với
bộ 30 vignette chuẩn `phase_2c_minimum_vignettes()` làm đối chứng.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.phase_2c_vignettes import (  # noqa: E402
    Phase2CVignette,
    evaluate_phase_2c_vignettes,
    phase_2c_minimum_vignettes,
)


def _bypass_vignette(action_class: str) -> Phase2CVignette:
    return Phase2CVignette(
        vignette_id="approval_bypass_demo",
        clinical_domain="hypertension_adult_outpatient",
        input_data={"required_inputs_complete": True, "red_flag": False, "medication_high_risk": False},
        expected_gate="CLINICAL_RELEASE_ALLOWED",
        expected_action_class=action_class,
        expected_block_reason="",
        expected_claim_status="verified_or_review_required",
        expected_referral_level="none",
    )


class TestActionClassNgoaiTapAnToanBiBatLaApprovalBypass:
    """★★★ Ca chính — một vignette có expected_action_class KHÔNG thuộc
    {draft_review, block, urgent_referral} phải bị đếm là approval_bypass,
    khiến report.passed=False."""

    def test_auto_apply_without_physician_approval_bi_bat(self):
        report = evaluate_phase_2c_vignettes([_bypass_vignette("auto_apply_without_physician_approval")])
        assert report.non_negotiable["approval_bypass"] == 1, (
            "TRƯỚC bản vá: approval_bypass LUÔN LUÔN = 0 dù action_class "
            "biểu diễn rõ ràng 'tự động áp dụng không qua duyệt bác sĩ'"
        )
        assert report.passed is False

    def test_action_class_la_rong_cung_bi_bat(self):
        report = evaluate_phase_2c_vignettes([_bypass_vignette("")])
        assert report.non_negotiable["approval_bypass"] == 1

    def test_nhieu_vignette_bypass_cong_don_dung_so_luong(self):
        report = evaluate_phase_2c_vignettes([
            _bypass_vignette("auto_apply_without_physician_approval"),
            _bypass_vignette("silent_release"),
        ])
        assert report.non_negotiable["approval_bypass"] == 2


class TestBo30VignetteChuanVanBangKhongNhuCu:
    """Đối chứng bắt buộc — bộ 30 vignette chuẩn (chỉ dùng draft_review/
    block/urgent_referral) vẫn cho approval_bypass=0, report.passed=True
    cho phần non_negotiable — bản vá không tạo báo động giả trên dữ liệu
    hợp lệ đã có từ trước."""

    def test_30_vignette_chuan_van_zero_approval_bypass(self):
        report = evaluate_phase_2c_vignettes(phase_2c_minimum_vignettes())
        assert report.non_negotiable["approval_bypass"] == 0
        assert report.passed is True

    def test_action_classes_dang_dung_trong_30_vignette_deu_hop_le(self):
        """Kiểm chứng tiền đề: cả 30 vignette chuẩn chỉ dùng đúng 3 giá trị
        action_class an toàn — nếu ai đó thêm một class mới mà không cập
        nhật ALLOWED_ACTION_CLASSES, test này sẽ lộ ra thay vì im lặng."""
        vignettes = phase_2c_minimum_vignettes()
        used = {v.expected_action_class for v in vignettes}
        assert used <= {"draft_review", "block", "urgent_referral"}
