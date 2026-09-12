"""Hồi quy phát hiện #3 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 15) trong
app/clinical_content/phase_2c_selection.py::Phase2CPackSelection.blocked_reasons.

CƠ CHẾ LỖI: `approved_for_real_pack_build` yêu cầu
`physician_approval_required is True`, nhưng `blocked_reasons` không bao
giờ kiểm field này. Khi `physician_approval_required=False` (curator/YAML
tắt nhầm cờ này) trong khi mọi field khác hợp lệ (selected_pack hợp lệ,
approval_record_path có, approval_status="approved"), pathway build vẫn
BỊ CHẶN ĐÚNG (an toàn) nhưng `blocked_reasons` trả về DANH SÁCH RỖNG —
người xem log/CI không thể biết vì sao bị chặn.

BẢN VÁ: thêm nhánh kiểm `physician_approval_required` trong
`blocked_reasons`.

Nguyên tắc viết test: gọi THẲNG property `blocked_reasons`/
`approved_for_real_pack_build` thật trên `Phase2CPackSelection` dựng tay.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.phase_2c_selection import Phase2CPackSelection  # noqa: E402


class TestPhysicianApprovalRequiredFalseNhungBlockedReasonsRong:
    """★★★ Ca chính — mọi field khác hợp lệ NGOẠI TRỪ
    physician_approval_required=False vẫn phải có lý do chặn tường minh."""

    def test_moi_field_khac_hop_le_nhung_approval_required_false(self):
        selection = Phase2CPackSelection(
            selected_pack="hypertension_adult_outpatient",
            physician_approval_required=False,
            approval_record_path="approval.json",
            approval_status="approved",
        )
        assert selection.approved_for_real_pack_build is False
        assert "physician_approval_required_flag_is_false" in selection.blocked_reasons, (
            "TRƯỚC bản vá: blocked_reasons trả về RỖNG dù build bị chặn "
            "đúng vì physician_approval_required=False — không ai biết "
            "vì sao bị chặn"
        )

    def test_blocked_reasons_khong_con_rong(self):
        selection = Phase2CPackSelection(
            selected_pack="hypertension_adult_outpatient",
            physician_approval_required=False,
            approval_record_path="approval.json",
            approval_status="approved",
        )
        assert selection.blocked_reasons != []


class TestPhysicianApprovalRequiredTrueVanHoatDongNhuCu:
    """Đối chứng bắt buộc — physician_approval_required=True (giá trị mặc
    định, dùng thật ở config/phase_2c_pilot_selection.yaml) không sinh lý
    do chặn mới, hành vi gốc không đổi."""

    def test_approval_required_true_khong_them_ly_do_chan(self):
        selection = Phase2CPackSelection(
            selected_pack="hypertension_adult_outpatient",
            physician_approval_required=True,
            approval_record_path="approval.json",
            approval_status="approved",
        )
        assert "physician_approval_required_flag_is_false" not in selection.blocked_reasons
        assert selection.blocked_reasons == []
        assert selection.approved_for_real_pack_build is True

    def test_pending_approval_van_bao_dung_ly_do_cu(self):
        selection = Phase2CPackSelection(
            selected_pack="hypertension_adult_outpatient",
            physician_approval_required=True,
            approval_record_path="approval.json",
            approval_status="pending",
        )
        assert "approval_not_approved:pending" in selection.blocked_reasons
        assert "physician_approval_required_flag_is_false" not in selection.blocked_reasons
