"""Hồi quy phát hiện #2 (High) của Workflow đối kháng đa-agent 2026-09-05
(vòng 11) trong app/core/release_manager.py::ReleaseManager.release().

CƠ CHẾ LỖI: `PolicyEngine.evaluate()` chỉ kiểm cổng bác sĩ duyệt (P006)/
feature flag clinical release (P007) KHI `context["action"]` khớp đúng một
trong {"clinical_release","publish_clinical","apply_recommendation"}. Trước
bản vá, `release()` truyền THẲNG `policy_context` do caller cung cấp vào
`evaluate()` mà không đòi hỏi gì về khóa "action" — thiếu hẳn khóa này (vd
`policy_context={"feature_flags": {}}`) làm `action=""` và BỎ QUA ÂM THẦM
toàn bộ nhóm cổng theo action: `release()` vẫn thành công dù chưa hề được
PolicyEngine soi cổng bác sĩ duyệt nào, kể cả cho channel
"clinical_dashboard" — đúng channel mà `tests/test_v7_core_control_plane.py`
đã dùng để kiểm cổng P006/P007 (nhưng LUÔN kèm action="clinical_release" nên
chưa từng lộ khoảng hở này).

BẢN VÁ: `release()` từ chối (ValueError) khi `policy_context` không khai
"action" — không sửa được lỗi "khai sai/gõ nhầm action" (đặc điểm chung của
PolicyEngine dùng string dispatch, vượt phạm vi file này), nhưng chặn đúng
trường hợp quên khai hoàn toàn.

Nguyên tắc viết test: gọi THẲNG `ReleaseManager.release()` thật với
`ApprovalItem`/`ReviewStatus` thật, không mock PolicyEngine.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.core.approval_service import ApprovalItem, ReviewStatus  # noqa: E402
from app.core.release_manager import ReleaseManager  # noqa: E402


def _da_duyet(item_type: str = "clinical_release") -> ApprovalItem:
    return ApprovalItem(
        approval_id="apr_x", run_id="run_x", item_type=item_type,
        summary="Release to clinical dashboard", status=ReviewStatus.APPROVED,
    )


class TestThieuActionBiChanCung:
    """★★★ Ca chính — thiếu hẳn khóa 'action' trong policy_context phải bị
    CHẶN NGAY (ValueError), không được lặng lẽ bỏ qua toàn bộ cổng P006/P007."""

    def test_thieu_action_hoan_toan_bi_chan(self):
        manager = ReleaseManager()
        approval = _da_duyet()

        with pytest.raises(ValueError, match="action"):
            manager.release(
                run_id="run_x", channel="clinical_dashboard", payload_hash="abc123",
                approval=approval,
                policy_context={"feature_flags": {}},  # KHÔNG có "action"
            )

    def test_action_rong_cung_bi_chan(self):
        manager = ReleaseManager()
        approval = _da_duyet()

        with pytest.raises(ValueError, match="action"):
            manager.release(
                run_id="run_x", channel="clinical_dashboard", payload_hash="abc123",
                approval=approval,
                policy_context={"action": "", "feature_flags": {}},
            )

    def test_action_chi_toan_khoang_trang_cung_bi_chan(self):
        manager = ReleaseManager()
        approval = _da_duyet()

        with pytest.raises(ValueError, match="action"):
            manager.release(
                run_id="run_x", channel="clinical_dashboard", payload_hash="abc123",
                approval=approval,
                policy_context={"action": "   ", "feature_flags": {}},
            )


class TestCoActionThatVanHoatDongDungNhuCu:
    """Đối chứng bắt buộc — khai đúng action="clinical_release" vẫn đi qua
    ĐÚNG luồng cũ: bị chặn khi thiếu physician_approved/feature flag, và
    thành công khi đủ cả hai (khớp hành vi đã kiểm ở
    tests/test_v7_core_control_plane.py::test_release_requires_approval_and_enabled_flag)."""

    def test_co_action_nhung_thieu_physician_approved_van_bi_chan_nhu_cu(self):
        manager = ReleaseManager()
        approval = _da_duyet()

        with pytest.raises(PermissionError):
            manager.release(
                run_id="run_x", channel="clinical_dashboard", payload_hash="abc123",
                approval=approval,
                policy_context={"action": "clinical_release"},
            )

    def test_du_dieu_kien_van_release_thanh_cong_nhu_cu(self):
        manager = ReleaseManager()
        approval = _da_duyet()

        record = manager.release(
            run_id="run_x", channel="clinical_dashboard", payload_hash="abc123",
            approval=approval,
            policy_context={
                "action": "clinical_release",
                "physician_approved": True,
                "feature_flags": {"v7_clinical_release": True},
            },
        )
        assert record.release_id.startswith("rel_")

    def test_action_khong_thuoc_nhom_lam_sang_van_khong_bi_chan_thieu_action(self):
        """Kịch bản seed/test thật (scripts/phase_2b_seed_governance_test_data.py)
        dùng action="test_release" cho channel không phải lâm sàng — vẫn phải
        chạy được, bản vá chỉ đòi CÓ khai action, không đòi đúng action lâm sàng."""
        manager = ReleaseManager()
        approval = _da_duyet(item_type="test_release")

        record = manager.release(
            run_id="run_x", channel="test_only", payload_hash="sha256:test",
            approval=approval,
            policy_context={"action": "test_release", "feature_flags": {}},
        )
        assert record.release_id.startswith("rel_")
