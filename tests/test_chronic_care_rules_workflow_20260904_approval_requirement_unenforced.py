"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-04 (vòng 2):
`app/chronic_care/rules.py::assert_rule_approved_for_test()` — trường
`ChronicCareRule.approval_requirement` được KHAI BÁO nhưng KHÔNG NƠI NÀO đọc.

CƠ CHẾ LỖI: 4/5 luật (CC-001..CC-004) khai `approval_requirement=
"approved_shadow_rule"`, riêng CC-005 khai `"physician_review_required"` —
một yêu cầu MẠNH HƠN. Nhưng `assert_rule_approved_for_test()` (điểm gác DUY
NHẤT trước khi một action từ rule engine được thực thi, gọi bởi
`ChronicCareService.seed_synthetic_cases()`) chỉ kiểm `rule.approved_by`/
`rule.status` — không hề đọc `approval_requirement`. Kết quả: CC-005 đi qua
gác CÙNG MỘT CÁCH như CC-001..CC-004, dù khai yêu cầu khác hẳn — trường tồn
tại thuần tuý để trang trí dataclass.

Manh mối cho thấy đây là dây nối CHƯA XONG, không phải thiết kế cố ý: chính
CC-005 tự gắn `metadata={"physician_review_required": True}` vào RuleAction
nó sinh ra — đặt tên khoá GIỐNG HỆT giá trị của `approval_requirement`. Ý
định rõ ràng là hai nơi khai phải KHỚP NHAU; chỉ là chưa có chỗ nào đối
chiếu, và `seed_synthetic_cases()` cũng chưa từng ĐỌC cờ metadata này (khác
`safety_queue_item` của CC-003, đã có nhánh `add_timeline()` riêng).

BẢN VÁ (hai phần, cả hai đều cần cho ca thật):
1. `assert_rule_approved_for_test(rule_id, action=None)` — khi có `action`,
   đối chiếu `rule.approval_requirement == "physician_review_required"` với
   `action.metadata.get("physician_review_required")`; LỆCH NHAU (một bên
   khai, bên kia không) ⇒ `PermissionError`. Đây là "thực thi" thật: trường
   giờ được ĐỌC và có khả năng CHẶN khi hai nơi khai trôi khỏi nhau.
2. `ChronicCareService.seed_synthetic_cases()`: thêm nhánh
   `add_timeline("PHYSICIAN_REVIEW_REQUIRED", ...)` khi action mang cờ này
   — song song với nhánh `safety_queue_item` đã có, để yêu cầu bác sĩ review
   để lại DẤU VẾT quan sát được trong audit trail, không chỉ nằm trong
   dataclass.

Nguyên tắc viết test: gọi THẲNG `assert_rule_approved_for_test()` và
`ChronicCareService` thật (không mock), dựng `RuleAction` giả để kiểm cả hai
chiều lệch (rule khai mà action không mang cờ, và ngược lại).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.chronic_care.rules import RuleAction, assert_rule_approved_for_test  # noqa: E402
from app.chronic_care.service import ChronicCareService  # noqa: E402


class TestDoiChieuApprovalRequirementVoiActionMetadata:
    """★★ Ca chính — CC-005 khai physician_review_required, action phải
    mang đúng cờ tương ứng; hai nơi khai lệch nhau phải bị chặn."""

    def test_cc005_dung_metadata_thi_qua_duoc(self):
        action = RuleAction("CC-005", "CREATE_TASK", "POST_DISCHARGE_REVIEW",
                             "HIGH", "care_coordinator",
                             metadata={"physician_review_required": True})
        # Không được ném lỗi — đúng cấu hình hiện tại của CC-005 trong rules.py.
        assert_rule_approved_for_test("CC-005", action)

    def test_cc005_thieu_metadata_bi_chan(self):
        """Rule khai physician_review_required nhưng action KHÔNG mang cờ
        tương ứng — hai nơi khai lệch nhau, phải bị chặn."""
        action = RuleAction("CC-005", "CREATE_TASK", "POST_DISCHARGE_REVIEW",
                             "HIGH", "care_coordinator", metadata={})
        with pytest.raises(PermissionError, match="lệch nhau"):
            assert_rule_approved_for_test("CC-005", action)

    def test_cc001_khong_can_metadata_van_qua(self):
        """Đối chứng — CC-001 khai "approved_shadow_rule" (KHÔNG phải
        physician_review_required), action không mang cờ vẫn hợp lệ."""
        action = RuleAction("CC-001", "CREATE_TASK", "REVIEW_OVERDUE_CASE",
                             "LOW", "care_coordinator", metadata={})
        assert_rule_approved_for_test("CC-001", action)

    def test_cc001_co_metadata_thua_cung_bi_chan(self):
        """Chiều ngược lại — một action của rule KHÔNG khai
        physician_review_required mà lại tự gắn cờ đó cũng là lệch nhau,
        không chỉ riêng chiều thiếu."""
        action = RuleAction("CC-001", "CREATE_TASK", "REVIEW_OVERDUE_CASE",
                             "LOW", "care_coordinator",
                             metadata={"physician_review_required": True})
        with pytest.raises(PermissionError, match="lệch nhau"):
            assert_rule_approved_for_test("CC-001", action)

    def test_khong_truyen_action_van_hoat_dong_nhu_cu(self):
        """Đối chứng bắt buộc — gọi không kèm `action` (chữ ký cũ) vẫn hoạt
        động y hệt trước bản vá, không phá vỡ caller nào khác."""
        assert_rule_approved_for_test("CC-005")
        assert_rule_approved_for_test("CC-001")


class TestTimelinePhysicianReviewRequired:
    """★★ Ca tích hợp — seed_synthetic_cases() phải để lại dấu vết audit
    trail khi rule engine sinh ra action mang cờ physician_review_required.

    Dùng đúng bộ dữ liệu tổng hợp CHUẨN (`build_synthetic_case_pack()`, 30
    ca, gọi qua `seed_synthetic_cases()` mặc định) thay vì tự dựng ca đơn lẻ
    — `validate_synthetic_case_pack()` đòi tối thiểu 30 ca, và bộ chuẩn đã
    có sẵn đúng 1 ca `SYN-PD-001` (program_code=POST_DISCHARGE_REVIEW_PROGRAM,
    post_discharge_flag=True) để kiểm nhánh này mà không cần dựng fixture giả."""

    def test_ca_post_discharge_de_lai_dau_vet_timeline(self):
        service = ChronicCareService()
        service.seed_synthetic_cases()
        pd_enrollment = next(e for e in service.enrollments.values()
                             if e.program_code == "POST_DISCHARGE_REVIEW_PROGRAM")
        event_types = {e.event_type for e in service.timeline if e.enrollment_id == pd_enrollment.id}
        assert "PHYSICIAN_REVIEW_REQUIRED" in event_types

    def test_ca_khong_post_discharge_khong_co_dau_vet(self):
        service = ChronicCareService()
        service.seed_synthetic_cases()
        other_enrollment = next(e for e in service.enrollments.values()
                                if e.program_code != "POST_DISCHARGE_REVIEW_PROGRAM")
        event_types = {e.event_type for e in service.timeline if e.enrollment_id == other_enrollment.id}
        assert "PHYSICIAN_REVIEW_REQUIRED" not in event_types
