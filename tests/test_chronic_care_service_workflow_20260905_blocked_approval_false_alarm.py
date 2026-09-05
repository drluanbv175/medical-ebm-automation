"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 17) trong app/chronic_care/service.py::approve_care_plan_draft().

CƠ CHẾ LỖI: khi `approve_care_plan_draft()` phát hiện một draft ĐANG BỊ
CHẶN (thiếu evidence_reference_ids/claim_reference_ids, hoặc cờ
`v7_clinical_release` sai), nó tăng `self.unverified_evidence_released`
NGAY TRƯỚC KHI raise PermissionError — tức đúng lúc hệ thống NGĂN THÀNH
CÔNG việc duyệt, KHÔNG có gì được "released" cả. Bộ đếm này được
`dashboard_state()` đọc để quyết định `production_block_status`:
`any(safety_counters.values())` → "SHADOW PILOT BLOCKED" (trạng thái báo
động). Hệ quả: `_physician_row()` chủ động gắn
`required_action: "physician_review"` cho MỌI draft đang BLOCKED (mời bác
sĩ vào xem/duyệt) — nên đúng luồng làm việc bình thường mà hàng đợi tự
mời gọi (mở một draft bị chặn ra để duyệt) lại là thứ TỰ KÍCH báo động,
không phân biệt được với một lần bypass thật (`approval_bypass`/
`clinical_release_flag_bypass`).

BẢN VÁ: bỏ dòng tăng `unverified_evidence_released` trong nhánh `blocked`
của `approve_care_plan_draft()` — nhánh này LUÔN kết thúc bằng
`raise PermissionError(blocked)`, không có đường nào cho draft chuyển
sang APPROVED_FOR_SHADOW ở đây, nên tăng bộ đếm "đã released" tại đây là
sai bản chất. Các bộ đếm vi phạm THẬT khác
(`approval_bypass`/`clinical_release_flag_bypass`) không đổi.

Nguyên tắc viết test: gọi THẲNG `ChronicCareService.approve_care_plan_draft()`
+ `dashboard_state()` thật, không mock nội bộ."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.chronic_care.service import ChronicCareService  # noqa: E402


class TestDuyetDraftDangBiChanKhongDuocTangBoDemDaPhatHanh:
    """★★★ Ca chính — một lần approve() bị TỪ CHỐI ĐÚNG THIẾT KẾ (draft đang
    BLOCKED, PermissionError được raise) không được coi là "đã phát hành
    chứng cứ chưa xác minh": bộ đếm phải giữ nguyên 0 và dashboard không
    được nhảy sang trạng thái báo động."""

    def test_thieu_evidence_bi_chan_dung_nhung_khong_tang_bo_dem(self):
        service = ChronicCareService()
        service.seed_synthetic_cases()
        blocked = next(p for p in service.plan_drafts.values() if p.status == "BLOCKED")
        before = service.unverified_evidence_released

        with pytest.raises(PermissionError, match="EVIDENCE_INSUFFICIENT_OR_UNVERIFIED"):
            service.approve_care_plan_draft(blocked.id)

        assert service.unverified_evidence_released == before, (
            "TRƯỚC bản vá: mỗi lần approve() một draft BLOCKED (đúng thiết kế, "
            "không có gì được duyệt/phát hành) vẫn tăng unverified_evidence_"
            "released — biến việc CHẶN THÀNH CÔNG thành một 'vi phạm' giả"
        )

    def test_dashboard_khong_bao_dong_gia_sau_khi_tu_choi_dung_thiet_ke(self):
        service = ChronicCareService()
        service.seed_synthetic_cases()
        blocked = next(p for p in service.plan_drafts.values() if p.status == "BLOCKED")

        with pytest.raises(PermissionError):
            service.approve_care_plan_draft(blocked.id)

        state = service.dashboard_state()
        assert state.safety_counters["unverified_evidence_released"] == 0
        assert state.production_block_status == "production_blocked_by_design", (
            "TRƯỚC bản vá: production_block_status nhảy sang 'SHADOW PILOT "
            "BLOCKED' dù không thuốc/chứng cứ nào thực sự được phát hành — "
            "báo động sai không phân biệt được với bypass thật"
        )

    def test_nhieu_lan_thu_duyet_draft_bi_chan_van_khong_tich_luy_bo_dem(self):
        """Bác sĩ có thể mở lại cùng một draft BLOCKED nhiều lần (đúng gợi ý
        required_action='physician_review' của hàng đợi) — mỗi lần thử đều
        bị từ chối đúng thiết kế, không lần nào được tính là vi phạm."""
        service = ChronicCareService()
        service.seed_synthetic_cases()
        blocked = next(p for p in service.plan_drafts.values() if p.status == "BLOCKED")

        for _ in range(3):
            with pytest.raises(PermissionError):
                service.approve_care_plan_draft(blocked.id)

        assert service.unverified_evidence_released == 0


class TestBoDemViPhamThatVanHoatDongDungNhuCu:
    """Đối chứng bắt buộc — các bộ đếm vi phạm THẬT (không liên quan tới
    nhánh vừa sửa) vẫn tăng đúng như trước bản vá."""

    def test_khong_phai_bac_si_duyet_van_tang_approval_bypass(self):
        service = ChronicCareService()
        service.seed_synthetic_cases()
        complete = next(p for p in service.plan_drafts.values() if p.status == "PENDING_REVIEW")

        with pytest.raises(PermissionError, match="Only physician"):
            service.approve_care_plan_draft(complete.id, reviewer_role="care_coordinator")

        assert service.approval_bypass == 1

    def test_duyet_draft_du_dieu_kien_van_thanh_cong_va_khong_tang_bo_dem_chan(self):
        service = ChronicCareService()
        service.seed_synthetic_cases()
        complete = next(p for p in service.plan_drafts.values() if p.status == "PENDING_REVIEW")

        approved = service.approve_care_plan_draft(complete.id)

        assert approved.status == "APPROVED_FOR_SHADOW"
        assert service.unverified_evidence_released == 0

    def test_co_v7_clinical_release_van_tang_clinical_release_flag_bypass(self):
        """Cờ `v7_clinical_release` bật là một vi phạm THẬT (cờ này BẮT BUỘC
        phải luôn False — constructor tự ép False cho MỌI cờ trong
        RISKY_FLAGS_MUST_STAY_FALSE, nên mô phỏng bằng cách gán trực tiếp
        SAU KHI khởi tạo để cô lập đúng nhánh `_care_plan_blocked_reason()`
        cần kiểm). Bộ đếm riêng của nhánh này (`clinical_release_flag_bypass`)
        không bị đụng bởi bản vá — bản vá chỉ bỏ dòng tăng
        `unverified_evidence_released` ở `approve_care_plan_draft()`."""
        service = ChronicCareService()
        service.seed_synthetic_cases()
        complete = next(p for p in service.plan_drafts.values() if p.status == "PENDING_REVIEW")
        service.feature_flags["v7_clinical_release"] = True

        with pytest.raises(PermissionError, match="CLINICAL_RELEASE_FLAG_MUST_STAY_FALSE"):
            service.approve_care_plan_draft(complete.id)

        assert service.clinical_release_flag_bypass == 1
