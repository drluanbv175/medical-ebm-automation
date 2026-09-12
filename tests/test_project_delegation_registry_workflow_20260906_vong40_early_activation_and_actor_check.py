"""Hồi quy phát hiện #2 (audit vòng 40, 2026-09-06) trong
research_project/project_delegation_registry.py.

── PHÁT HIỆN #2a — compute_status() không đọc effective_from_utc ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    def compute_status(self, now_utc=None) -> str:
        if self.status in (REVOKED, REJECTED): return self.status
        if self.status == PROPOSED: return PROPOSED
        now = now_utc or datetime.now(timezone.utc)
        end = datetime.fromisoformat(self.effective_until_utc)
        if now > end: return EXPIRED
        return ACTIVE

`compute_status()` — hàm "status hiệu lực" dùng ở MỌI nơi thật (get_status,
list_active, evaluate_delegation_action) — CHỈ đọc effective_until_utc,
KHÔNG BAO GIỜ đọc effective_from_utc. Sibling method is_active() (0 caller
thật trong repo) kiểm CẢ HAI mốc đúng. Hệ quả: một delegation được
activate() (status thô = ACTIVE) NHƯNG effective_from_utc còn ở TƯƠNG LAI
vẫn báo ACTIVE ngay lập tức, thay vì "chưa tới ngày hiệu lực".

── PHÁT HIỆN #2b — evaluate_delegation_action() không đối chiếu actor ──
CƠ CHẾ LỖI (TRƯỚC bản vá): hàm tự khai docstring "Evaluate liệu MỘT ACTOR
có được phép thực hiện action" nhưng KHÔNG BAO GIỜ so sánh actor_reference
với record.delegatee_synthetic_actor_id — bất kỳ actor nào cũng được đánh
giá y như chính người được ủy quyền.

PHẠM VI ẢNH HƯỞNG: `researchctl delegation-status` (CLI thật) →
DelegationRegistry.get_status() → compute_status() — báo status SAI cho
mọi delegation đã activate() sớm. evaluate_delegation_action() (RBAC
enforcement) hiện chưa có subcommand CLI riêng (chỉ activate/revoke/
evaluate qua test), nhưng là hàm CHÍNH cho phép/chặn hành động qua ủy
quyền — 2 lỗ hổng cộng dồn nghĩa là (a) một PI có thể activate() một
delegation trước ngày hiệu lực và nó lập tức dùng được, và (b) BẤT KỲ
actor nào — không chỉ delegatee — cũng được evaluate_delegation_action()
coi là hợp lệ."""
from __future__ import annotations

import pathlib
from datetime import datetime, timedelta, timezone

from research_project.project_delegation_registry import (
    DelegationReasonCode,
    DelegationRegistry,
    DelegationStatus,
    evaluate_delegation_action,
)

_FUTURE_START = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
_FAR_FUTURE_END = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
_NOW = datetime.now(timezone.utc).isoformat()
_NEAR_FUTURE_END = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def _make_registry(tmp_path: pathlib.Path) -> DelegationRegistry:
    return DelegationRegistry(tmp_path / "delegation_registry.jsonl")


class TestCaChinh2aActivateSomKhongDuocBaoLaActive:
    """★★★ Ca chính — delegation activate() sớm (effective_from_utc còn ở
    tương lai) KHÔNG được compute_status() báo là ACTIVE."""

    def test_activate_som_bao_pending_effective_khong_phai_active(self, tmp_path):
        reg = _make_registry(tmp_path)
        rec = reg.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role="METHODS_STATISTICS_REVIEWER",
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=_FUTURE_START,
            effective_until_utc=_FAR_FUTURE_END,
            reason="Test delegation chưa tới ngày hiệu lực",
        )
        reg.activate(rec.delegation_id)
        status = reg.get_status(rec.delegation_id)
        assert status != DelegationStatus.ACTIVE.value, (
            "TRƯỚC bản vá: compute_status() không đọc effective_from_utc — "
            "một delegation activate() sớm, trước ngày hiệu lực, vẫn báo "
            f"ACTIVE ngay lập tức. Kết quả thực tế: {status}"
        )
        assert status == DelegationStatus.PENDING_EFFECTIVE.value

    def test_evaluate_action_tren_delegation_chua_hieu_luc_bi_block(self, tmp_path):
        reg = _make_registry(tmp_path)
        rec = reg.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role="METHODS_STATISTICS_REVIEWER",
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=_FUTURE_START,
            effective_until_utc=_FAR_FUTURE_END,
            reason="Test delegation chưa tới ngày hiệu lực",
        )
        reg.activate(rec.delegation_id)
        result = evaluate_delegation_action(
            reg, rec.delegation_id,
            actor_reference="SYN-STAT-001",
            action="RECORD_REVIEW_ATTESTATION",
        )
        assert result.decision == "BLOCK", (
            "TRƯỚC bản vá: evaluate_delegation_action() chỉ kiểm EXPIRED, "
            "không kiểm PENDING_EFFECTIVE — action được ALLOW dù chưa tới "
            f"ngày hiệu lực. Kết quả thực tế: {result.decision}"
        )
        assert result.reason_code == DelegationReasonCode.DELEGATION_NOT_ACTIVE.value


class TestCaChinh2bActorPhaiKhopDelegatee:
    """★★★ Ca chính — actor_reference KHÁC delegatee_synthetic_actor_id
    phải bị BLOCK, không được đánh giá như chính delegatee."""

    def test_actor_khong_phai_delegatee_bi_block(self, tmp_path):
        reg = _make_registry(tmp_path)
        rec = reg.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role="METHODS_STATISTICS_REVIEWER",
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=_NOW,
            effective_until_utc=_NEAR_FUTURE_END,
            reason="Test delegation hợp lệ",
        )
        reg.activate(rec.delegation_id)
        result = evaluate_delegation_action(
            reg, rec.delegation_id,
            actor_reference="SYN-IMPOSTER-999",
            action="RECORD_REVIEW_ATTESTATION",
        )
        assert result.decision == "BLOCK", (
            "TRƯỚC bản vá: actor_reference không bao giờ được đối chiếu với "
            "delegatee_synthetic_actor_id — bất kỳ actor nào cũng được ALLOW "
            f"nếu action nằm trong permitted_actions. Kết quả thực tế: {result.decision}"
        )
        assert result.reason_code == DelegationReasonCode.DELEGATION_ACTOR_MISMATCH.value


class TestDoiChungHanhViCuVanDung:
    """Đối chứng — delegation ĐANG trong cửa sổ hiệu lực với ĐÚNG actor vẫn
    ALLOW; PROPOSED/EXPIRED/REVOKED vẫn báo đúng như cũ."""

    def test_actor_dung_va_trong_cua_so_hieu_luc_van_allow(self, tmp_path):
        reg = _make_registry(tmp_path)
        rec = reg.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role="METHODS_STATISTICS_REVIEWER",
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=_NOW,
            effective_until_utc=_NEAR_FUTURE_END,
            reason="Test delegation hợp lệ",
        )
        reg.activate(rec.delegation_id)
        result = evaluate_delegation_action(
            reg, rec.delegation_id,
            actor_reference="SYN-STAT-001",
            action="RECORD_REVIEW_ATTESTATION",
        )
        assert result.decision == "ALLOW"
        assert result.reason_code == DelegationReasonCode.DELEGATION_PERMITTED.value

    def test_proposed_van_bao_proposed(self, tmp_path):
        reg = _make_registry(tmp_path)
        rec = reg.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role="METHODS_STATISTICS_REVIEWER",
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=_NOW,
            effective_until_utc=_NEAR_FUTURE_END,
            reason="Chưa activate",
        )
        assert reg.get_status(rec.delegation_id) == DelegationStatus.PROPOSED.value

    def test_expired_van_bao_expired(self, tmp_path):
        reg = _make_registry(tmp_path)
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        near_past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        rec = reg.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role="METHODS_STATISTICS_REVIEWER",
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=past,
            effective_until_utc=near_past,
            reason="Đã hết hạn",
        )
        reg.activate(rec.delegation_id)
        assert reg.get_status(rec.delegation_id) == DelegationStatus.EXPIRED.value
