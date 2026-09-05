"""Hồi quy phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 9,
task #94) trong `app/chronic_care/service.py::ChronicCareService._physician_row()`
— hàng đợi xét duyệt của bác sĩ KHÔNG BAO GIỜ hết một ca RED/YELLOW dù đã
được duyệt hay từ chối.

CƠ CHẾ LỖI: `enrollment.current_risk_status` được đặt DUY NHẤT một lần lúc
`create_enrollment()` (từ `case.synthetic_risk_label`) và không bao giờ đổi.
`review_risk_draft()` đúng khi cập nhật `draft.risk_status` (PENDING_REVIEW
-> APPROVED_FOR_SHADOW/REJECTED) nhưng KHÔNG đụng tới `enrollment.
current_risk_status`. `_physician_row()` (trước bản vá) tính `safety_flags`/
`required_action` từ `enrollment.current_risk_status` — nên một ca RED đã
được bác sĩ duyệt HOẶC từ chối vẫn hiện y hệt lúc chưa duyệt.

Xác nhận sống trước khi vá: seed 1 enrollment RED + risk draft PENDING_REVIEW
-> review_risk_draft(approve=False) -> risk_draft_status đổi đúng thành
REJECTED, nhưng safety_flags/required_action ở _physician_row() vẫn
"red_review"/"physician_review" y hệt trước khi duyệt.

BẢN VÁ: dùng bản ghi risk draft MỚI NHẤT (risks[-1], đã có sẵn ở
risk_draft_status) làm nguồn sự thật — chỉ còn "cần hành động" khi
risk_status của draft đó VẪN là PENDING_REVIEW.

Nguyên tắc viết test: gọi THẲNG `ChronicCareService` thật (create_enrollment
-> create_risk_draft -> review_risk_draft -> _physician_row()/
dashboard_state()), không mock nội bộ.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.chronic_care.service import ChronicCareService  # noqa: E402
from app.chronic_care.synthetic_cases import SyntheticChronicCareCase  # noqa: E402


def _enroll(svc: ChronicCareService, risk_label: str = "RED"):
    case = SyntheticChronicCareCase(
        patient_reference_id="SYN-VONG9-001", age_band="60-69", sex="F",
        program_code="POST_DISCHARGE_REVIEW_PROGRAM", synthetic_risk_label=risk_label,
    )
    return svc.create_enrollment(case)


class TestHangDoiHetSauKhiTuChoiRiskDraft:
    """★★★ Ca chính — từ chối (reject) một risk draft RED phải làm
    required_action/safety_flags về "không còn cần hành động", KHÔNG được
    giữ nguyên "physician_review"/"red_review"."""

    def test_reject_lam_het_can_hanh_dong(self):
        svc = ChronicCareService()
        enr = _enroll(svc, "RED")
        draft = svc.create_risk_draft(enr.id, "RED", ["synthetic_status"], "trigger")

        row_before = svc._physician_row(enr)
        assert row_before["safety_flags"] == "red_review"
        assert row_before["required_action"] == "physician_review"

        svc.review_risk_draft(draft.id, reviewer_role="physician", approve=False, note="false alarm")
        row_after = svc._physician_row(enr)
        assert row_after["safety_flags"] == ""
        assert row_after["required_action"] == "none"


class TestHangDoiHetSauKhiDuyetRiskDraft:
    """★★★ Ca chính thứ hai — chấp thuận (approve) risk draft cũng phải làm
    hết "cần hành động" (đã xử lý xong, không còn PENDING_REVIEW)."""

    def test_approve_lam_het_can_hanh_dong(self):
        svc = ChronicCareService()
        enr = _enroll(svc, "YELLOW")
        draft = svc.create_risk_draft(enr.id, "YELLOW", ["synthetic_status"], "trigger")

        svc.review_risk_draft(draft.id, reviewer_role="physician", approve=True, note="confirmed")
        row_after = svc._physician_row(enr)
        assert row_after["safety_flags"] == ""
        assert row_after["required_action"] == "none"


class TestChuaReviewVanHienDungCanHanhDong:
    """Đối chứng bắt buộc — một draft RED/YELLOW CHƯA được review vẫn phải
    hiện "cần hành động" như hành vi gốc (không bị bản vá vô tình xoá luôn)."""

    def test_red_chua_review_van_can_hanh_dong(self):
        svc = ChronicCareService()
        enr = _enroll(svc, "RED")
        svc.create_risk_draft(enr.id, "RED", ["synthetic_status"], "trigger")
        row = svc._physician_row(enr)
        assert row["safety_flags"] == "red_review"
        assert row["required_action"] == "physician_review"

    def test_yellow_chua_review_van_can_hanh_dong_khong_co_safety_flag_do(self):
        svc = ChronicCareService()
        enr = _enroll(svc, "YELLOW")
        svc.create_risk_draft(enr.id, "YELLOW", ["synthetic_status"], "trigger")
        row = svc._physician_row(enr)
        # safety_flags chỉ dành cho RED (theo thiết kế gốc), YELLOW không có cờ đỏ riêng.
        assert row["safety_flags"] == ""
        assert row["required_action"] == "physician_review"


class TestGreenKhongBaoGioCanHanhDongVeRisk:
    """Đối chứng bắt buộc — enrollment GREEN không có risk draft RED/YELLOW
    thì không bao giờ "cần hành động" vì lý do risk (dù plan có thể vẫn
    pending, đó là nhánh khác)."""

    def test_green_khong_can_hanh_dong_neu_khong_co_plan_pending(self):
        svc = ChronicCareService()
        enr = _enroll(svc, "GREEN")
        svc.create_risk_draft(enr.id, "GREEN", ["synthetic_status"], "trigger")
        row = svc._physician_row(enr)
        assert row["safety_flags"] == ""
        assert row["required_action"] == "none"


class TestDashboardStateQueueGiamKhiDaXuLyHet:
    """★★★ Ca chính đo qua dashboard_state() (đường thật bác sĩ nhìn thấy)
    — physician_review_queue của MỘT enrollment RED đã reject phải không
    còn "physician_review" trong required_action."""

    def test_physician_review_queue_row_dung_sau_khi_reject(self):
        svc = ChronicCareService()
        enr = _enroll(svc, "RED")
        draft = svc.create_risk_draft(enr.id, "RED", ["synthetic_status"], "trigger")
        svc.review_risk_draft(draft.id, reviewer_role="physician", approve=False, note="not red")

        state = svc.dashboard_state()
        rows = [r for r in state.physician_review_queue if r["synthetic_id"] == "SYN-VONG9-001"]
        assert len(rows) == 1
        assert rows[0]["required_action"] == "none"
        assert rows[0]["risk_draft_status"] == "REJECTED"
