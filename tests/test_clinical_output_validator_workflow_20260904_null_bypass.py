"""Hồi quy phát hiện HIGH của audit đối kháng đa-agent 2026-09-04 (task #60):
`app/core/clinical_output_validator.py` — JSON `null` TƯỜNG MINH (khác vắng mặt
field) lách qua BA cổng an toàn lâm sàng riêng biệt.

Cơ chế lỗi: `.get(key, default)` chỉ thay `default` khi KEY VẮNG MẶT — một giá
trị `null` hiện diện (bình thường khi một producer JSON serialize field tùy
chọn thành `null` thay vì bỏ hẳn field) khiến `.get()` trả về `None`, và
`str(None) == "None"` — một chuỗi KHÁC RỖNG. Ba nơi trong module dùng
`str(x.get(key, default))` rồi kiểm rỗng/thành-viên:
  1. `source_id`/`source_type` (dòng ~148-149) — `not source_id` sai vì
     `"None"` là chuỗi khác rỗng;
  2. `source_status` (dòng ~152) — mặc định "unknown" (bị chặn) chỉ áp dụng
     khi field VẮNG MẶT; `null` tường minh cho ra `"None"`, không nằm trong
     `BLOCKING_SOURCE_STATUSES` — nghịch lý: khai BÁO null còn AN TOÀN HƠN
     bỏ trống field, ngược chiều thiết kế;
  3. `human_approval_id` (dòng ~214) — cùng lỗi `not "None"` = False.

Module này tự khai (docstring) là "lớp thực thi tối thiểu của Clinical V2
Apply Gate: output chỉ được coi là actionable khi đủ nguồn đã xác minh, an
toàn... và phê duyệt bác sĩ" — cả ba lỗ hổng đều đâm thẳng vào chính lời hứa
đó: một gói với nguồn KHÔNG CÓ ID, trạng thái KHÔNG XÁC ĐỊNH, hoặc HOÀN TOÀN
KHÔNG CÓ mã phê duyệt bác sĩ vẫn được báo `actionable_allowed=True`.

Bản vá thêm `_str_field(mapping, key, default)` — coi `None` (dù tường minh
hay do field vắng mặt) là "chưa có giá trị", trả `default` cho cả hai
trường hợp — rồi thay 3 chỗ gọi `str(x.get(...))` bằng hàm này.

Nguyên tắc viết test: gọi THẲNG `validate_clinical_output_packet()`, dùng lại
CHÍNH fixture `_approved_packet()` của test file hiện có (không tự bịa fixture
mới) rồi `copy.deepcopy` + sửa từng trường, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.clinical_output_validator import validate_clinical_output_packet  # noqa: E402
from tests.test_clinical_output_validator import _approved_packet  # noqa: E402


class TestNullSourceIdSourceTypeBlocked:
    """★★ Ca chính 1 — source_id/source_type = None (JSON null) phải bị chặn
    y hệt như khi field VẮNG MẶT hoàn toàn."""

    def test_source_id_none_blocks(self):
        packet = copy.deepcopy(_approved_packet())
        packet["evidence_basis"][0]["source_id"] = None
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "evidence_source_missing:1" in result.blockers

    def test_source_type_none_blocks(self):
        packet = copy.deepcopy(_approved_packet())
        packet["evidence_basis"][0]["source_type"] = None
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "evidence_source_missing:1" in result.blockers

    def test_missing_source_id_key_still_blocks_as_before(self):
        """★★ Đối chứng bắt buộc — hành vi ĐÃ ĐÚNG từ trước (field VẮNG MẶT
        hoàn toàn, không phải null) phải giữ nguyên."""
        packet = copy.deepcopy(_approved_packet())
        del packet["evidence_basis"][0]["source_id"]
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "evidence_source_missing:1" in result.blockers


class TestNullSourceStatusBlocked:
    """★★ Ca chính 2 — source_status = None phải chặn giống hệt field vắng
    mặt (mặc định "unknown", nằm trong BLOCKING_SOURCE_STATUSES)."""

    def test_source_status_none_blocks_same_as_missing(self):
        packet = copy.deepcopy(_approved_packet())
        packet["evidence_basis"][0]["source_status"] = None
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "source_status_blocks:1:unknown" in result.blockers

    def test_missing_source_status_key_still_blocks_as_before(self):
        packet = copy.deepcopy(_approved_packet())
        del packet["evidence_basis"][0]["source_status"]
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "source_status_blocks:1:unknown" in result.blockers

    def test_explicit_ok_status_still_passes(self):
        """★★ Đối chứng bắt buộc — trạng thái hợp lệ thật ("active"/"ok")
        không bị chặn oan sau khi thêm _str_field()."""
        packet = copy.deepcopy(_approved_packet())
        packet["evidence_basis"][0]["source_status"] = "active"
        result = validate_clinical_output_packet(packet)
        assert not any(b.startswith("source_status_blocks") for b in result.blockers)


class TestNullHumanApprovalIdBlocked:
    """★★ Ca chính 3 — human_approval_id = None phải chặn giống hệt field
    vắng mặt (không phê duyệt bác sĩ nào được ghi nhận)."""

    def test_human_approval_id_none_blocks(self):
        packet = copy.deepcopy(_approved_packet())
        packet["audit_trail"]["human_approval_id"] = None
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "missing_human_approval_id" in result.blockers

    def test_missing_human_approval_id_key_still_blocks_as_before(self):
        packet = copy.deepcopy(_approved_packet())
        del packet["audit_trail"]["human_approval_id"]
        result = validate_clinical_output_packet(packet)
        assert result.actionable_allowed is False
        assert "missing_human_approval_id" in result.blockers

    def test_real_approval_id_still_passes(self):
        packet = copy.deepcopy(_approved_packet())
        packet["audit_trail"]["human_approval_id"] = "DR-2026-001"
        result = validate_clinical_output_packet(packet)
        assert "missing_human_approval_id" not in result.blockers


class TestBaselineApprovedPacketUnaffected:
    """★★ Đối chứng tổng quát — gói ĐÃ ĐÚNG hoàn toàn (fixture gốc, không sửa
    gì) vẫn phải qua cổng bình thường sau bản vá."""

    def test_untouched_approved_packet_still_allowed(self):
        result = validate_clinical_output_packet(copy.deepcopy(_approved_packet()))
        assert result.actionable_allowed is True
        assert result.blockers == []
