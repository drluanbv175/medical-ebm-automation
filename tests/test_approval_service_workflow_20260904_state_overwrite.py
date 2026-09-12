"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-04 (vòng 2):
`app/core/approval_service.py::ApprovalCenter.approve()/reject()` — ghi đè
trạng thái/audit-trail của một `ApprovalItem` VÔ ĐIỀU KIỆN, không kiểm trạng
thái hiện tại trước khi ghi.

CƠ CHẾ LỖI: cả `approve()` lẫn `reject()` chỉ kiểm `reviewer_role` có đúng
thẩm quyền hay không, rồi gán thẳng `item.status`/`reviewed_at`/
`reviewer_role`/`reviewer_note` — không hề đọc `item.status` HIỆN TẠI trước
khi ghi. Hậu quả: gọi `approve()` trên một item ĐÃ `REJECTED` sẽ lặng lẽ lật
thành `APPROVED` (và ngược lại), XOÁ MẤT dấu vết ai đã ra quyết định lần đầu
— trong khi `ApprovalCenter` là sổ audit-trail (mỗi field ghi rõ ai/lúc nào),
không phải một biến cờ boolean có thể ghi đè tuỳ ý. Cùng lớp lỗi đã vá trước
đó ở `tools/gate_contract.py` (tie-break cho phép xoá bản ghi REJECTED của
cổng nghiên cứu G0-G10) — chỉ khác tầng: đây là tầng chronic-care shadow
pilot, gate_contract.py là tầng nghiên cứu G0-G10.

`app/core/release_manager.py::ReleaseManager.release()` gate cứng vào
`approval.status is ReviewStatus.APPROVED` — nên một item bị REJECTED rồi bị
approve() lặng lẽ lật lại sẽ vượt qua gate release mà không ai biết quyết
định gốc là REJECTED.

Bản vá thêm `_require_pending()`: `approve()`/`reject()` chỉ được gọi trên
item còn `PENDING`; gọi trên item đã có quyết định (APPROVED hoặc REJECTED)
ném `PermissionError` nêu rõ trạng thái hiện tại + ai đã quyết định.

Nguyên tắc viết test: gọi THẲNG `ApprovalCenter` thật (không mock), dùng
đúng exception type mà class này đã dùng cho lỗi thẩm quyền (`PermissionError`)
để giữ nhất quán API.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.approval_service import ApprovalCenter, ReviewStatus  # noqa: E402


class TestKhongDuocGhiDeQuyetDinhDaCo:
    """★★ Ca chính — approve()/reject() trên item đã REJECTED/APPROVED phải
    ném PermissionError, KHÔNG được lặng lẽ đổi status."""

    def test_approve_sau_reject_bi_chan(self):
        center = ApprovalCenter()
        item = center.submit("run_1", "risk_draft", "tóm tắt")
        center.reject(item.approval_id, "physician", "không đủ căn cứ")
        assert center.get(item.approval_id).status == ReviewStatus.REJECTED

        with pytest.raises(PermissionError):
            center.approve(item.approval_id, "physician", "đổi ý")

        # Trạng thái VÀ audit-trail gốc phải còn nguyên sau lần gọi bị chặn.
        after = center.get(item.approval_id)
        assert after.status == ReviewStatus.REJECTED
        assert after.reviewer_note == "không đủ căn cứ"

    def test_reject_sau_approve_bi_chan(self):
        center = ApprovalCenter()
        item = center.submit("run_1", "risk_draft", "tóm tắt")
        center.approve(item.approval_id, "physician", "đã duyệt")
        assert center.get(item.approval_id).status == ReviewStatus.APPROVED

        with pytest.raises(PermissionError):
            center.reject(item.approval_id, "physician", "đổi ý")

        after = center.get(item.approval_id)
        assert after.status == ReviewStatus.APPROVED
        assert after.reviewer_note == "đã duyệt"

    def test_approve_lai_tren_item_da_approved_cung_bi_chan(self):
        """Không chỉ đảo trạng thái — GỌI LẶP approve() trên chính item đã
        APPROVED cũng phải bị chặn, tránh một reviewer KHÁC âm thầm ghi đè
        reviewer_role/reviewer_note của người duyệt đầu tiên."""
        center = ApprovalCenter()
        item = center.submit("run_1", "risk_draft", "tóm tắt")
        center.approve(item.approval_id, "physician", "duyệt lần 1")

        with pytest.raises(PermissionError):
            center.approve(item.approval_id, "principal_investigator", "duyệt lần 2")

        after = center.get(item.approval_id)
        assert after.reviewer_role == "physician"
        assert after.reviewer_note == "duyệt lần 1"


class TestApproveRejectBinhThuongVanHoatDong:
    """Đối chứng bắt buộc — approve()/reject() đầu tiên trên một item PENDING
    (đúng luồng caller thật trong chronic_care/service.py) vẫn hoạt động y hệt
    trước bản vá."""

    def test_approve_lan_dau_thanh_cong(self):
        center = ApprovalCenter()
        item = center.submit("run_1", "risk_draft", "tóm tắt")
        approved = center.approve(item.approval_id, "physician", "ok")
        assert approved.status == ReviewStatus.APPROVED
        assert approved.reviewer_role == "physician"
        assert approved.reviewer_note == "ok"
        assert approved.reviewed_at is not None

    def test_reject_lan_dau_thanh_cong(self):
        center = ApprovalCenter()
        item = center.submit("run_1", "risk_draft", "tóm tắt")
        rejected = center.reject(item.approval_id, "physician", "chưa đủ căn cứ")
        assert rejected.status == ReviewStatus.REJECTED
        assert rejected.reviewer_note == "chưa đủ căn cứ"


class TestReleaseManagerKhongBiLatQuaApproveSauReject:
    """★★ Ca tích hợp — chứng minh tác động thật: trước bản vá, một item bị
    REJECTED rồi bị approve() lại sẽ vượt qua gate của ReleaseManager."""

    def test_release_van_chan_dung_khi_khong_the_lat_trang_thai(self):
        from app.core.release_manager import ReleaseManager

        center = ApprovalCenter()
        item = center.submit("run_1", "clinical_draft", "bản nháp")
        center.reject(item.approval_id, "physician", "không đạt")

        # Nỗ lực "lật lại" quyết định REJECTED giờ bị chặn ngay tại nguồn —
        # ReleaseManager không bao giờ thấy được một APPROVED giả.
        with pytest.raises(PermissionError):
            center.approve(item.approval_id, "physician", "thử lật lại")

        manager = ReleaseManager()
        with pytest.raises(PermissionError):
            manager.release(
                run_id="run_1",
                channel="clinical_dashboard",
                payload_hash="abc",
                approval=center.get(item.approval_id),
                policy_context={"action": "clinical_release"},
            )
