"""Hồi quy phát hiện #1 và #2 (audit vòng 41, 2026-09-06) trong
research_project/project_rbac_simulation.py.

── PHÁT HIỆN #1 — SoD-06 CONFLICTING_ROLES_SAME_ACTOR chưa từng thực thi ──
CƠ CHẾ LỖI (TRƯỚC bản vá): `SoDViolation.CONFLICTING_ROLES_SAME_ACTOR` tồn
tại trong enum từ trước (mã SoD-06), và chính comment của
`RBAC_POLICY[PI]` tự khai "RECORD_REVIEW_ATTESTATION # SELF_REVIEW only;
SoD guard blocks independent claim" — nhưng `evaluate_rbac()` chỉ có 7
guard thật (SoD-01 đến SoD-05, SoD-07, SoD-08), KHÔNG guard nào đối chiếu
việc một actor giữ ĐỒNG THỜI role PI và một role review độc lập
(METHODS_STATISTICS_REVIEWER/EVIDENCE_CITATION_REVIEWER/
DATA_GOVERNANCE_QA_REVIEWER). Một actor như vậy có thể tự ghi nhận
RECORD_REVIEW_ATTESTATION/RECORD_EVIDENCE_ATTESTATION dưới danh nghĩa
"độc lập" trong khi thực chất chính là PI/tác giả — mâu thuẫn trực tiếp
với câu chữ tự khai và với
`release_evidence/R1_1/R1_1_ROLE_POLICY_REFERENCE.md` (tự khai "SoD
matrix: DEFINED (8 guards implemented)").

── PHÁT HIỆN #2 — RoleAssignment.is_expired() chỉ kiểm mốc KẾT THÚC ──
CƠ CHẾ LỖI (TRƯỚC bản vá):
    def is_expired(self, now_utc=None) -> bool:
        if self.expires_at_utc is None: return False
        ...
        return now > exp

`is_expired()` — dùng bởi CẢ `active_roles()` LẪN vòng lặp per-role trong
`evaluate_rbac()` (Guard 7) — chỉ đọc `expires_at_utc`, KHÔNG BAO GIỜ đọc
`assigned_at_utc` (mốc BẮT ĐẦU). Một role assignment với `assigned_at_utc`
còn ở TƯƠNG LAI (chưa tới ngày bắt đầu hiệu lực) vẫn được coi là "chưa
expired" ⇒ đang hoạt động ngay hôm nay, dù chưa tới ngày được cấp.

PHẠM VI ẢNH HƯỞNG: `evaluate_rbac()`/`SyntheticActor.active_roles()` là
engine quyết định RBAC thật đứng sau `researchctl rbac-simulate`
(`project_cli.py::_cmd_rbac_simulate`) và được gọi trực tiếp bởi
`tests/test_r1_1_offline_rbac_synthetic_identity.py`/
`tests/test_r1_1_2_gap_remediation.py`. Cả hai lỗ hổng cho phép actor có
quyền SỚM HƠN hoặc RỘNG HƠN dự kiến."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from research_project.project_rbac_simulation import (
    EvaluationContext,
    ResearchRole,
    RoleAssignment,
    SoDViolation,
    SyntheticActor,
    evaluate_rbac,
)

_NOW_DT = datetime.now(timezone.utc)
_NOW = _NOW_DT.isoformat()
_FUTURE = (_NOW_DT + timedelta(days=30)).isoformat()


def _make_actor(actor_id: str, role_assignments) -> SyntheticActor:
    return SyntheticActor(
        synthetic_actor_id=actor_id,
        display_label=f"Test actor {actor_id}",
        role_assignments=role_assignments,
    )


class TestCaChinh1SoD06ChanRoleXungDot:
    """★★★ Ca chính — actor giữ đồng thời PI và một role review độc lập
    phải bị BLOCK khi ghi nhận attestation review/evidence."""

    def test_pi_va_methods_statistics_reviewer_bi_block(self):
        actor = _make_actor("SYN-DUAL-001", [
            RoleAssignment(role=ResearchRole.PI.value, assigned_at_utc=_NOW),
            RoleAssignment(
                role=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
                assigned_at_utc=_NOW,
            ),
        ])
        result = evaluate_rbac(actor, "RECORD_REVIEW_ATTESTATION")
        assert result.decision == "BLOCK", (
            "TRƯỚC bản vá: không guard nào kiểm actor giữ đồng thời PI + "
            "role review độc lập — action luôn được ALLOW. Kết quả thực "
            f"tế: {result.decision}"
        )
        assert result.reason_code == SoDViolation.CONFLICTING_ROLES_SAME_ACTOR.value

    def test_pi_va_evidence_citation_reviewer_bi_block(self):
        actor = _make_actor("SYN-DUAL-002", [
            RoleAssignment(role=ResearchRole.PI.value, assigned_at_utc=_NOW),
            RoleAssignment(
                role=ResearchRole.EVIDENCE_CITATION_REVIEWER.value,
                assigned_at_utc=_NOW,
            ),
        ])
        result = evaluate_rbac(actor, "RECORD_EVIDENCE_ATTESTATION")
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.CONFLICTING_ROLES_SAME_ACTOR.value


class TestCaChinh2RoleTuongLaiChuaDuocKichHoat:
    """★★★ Ca chính — role assignment với assigned_at_utc ở TƯƠNG LAI
    không được coi là đang hoạt động hôm nay."""

    def test_role_tuong_lai_khong_duoc_cap_quyen_som(self):
        # Actor có CO_INVESTIGATOR hiệu lực ngay (tránh nhánh "no active
        # role" SoD-07 để cô lập đúng lỗi #2) + DATA_MANAGER TƯƠNG LAI.
        actor = _make_actor("SYN-FUTURE-001", [
            RoleAssignment(role=ResearchRole.CO_INVESTIGATOR.value, assigned_at_utc=_NOW),
            RoleAssignment(role=ResearchRole.DATA_MANAGER.value, assigned_at_utc=_FUTURE),
        ])
        ctx = EvaluationContext(has_controlled_change_authorization=True)
        result = evaluate_rbac(actor, "UNLOCK_RESEARCH_DATA", ctx)
        assert result.decision == "BLOCK", (
            "TRƯỚC bản vá: is_expired() không kiểm assigned_at_utc — role "
            "DATA_MANAGER chưa tới ngày hiệu lực vẫn được active_roles() "
            f"tính là đang hoạt động. Kết quả thực tế: {result.decision}"
        )

    def test_active_roles_khong_gom_role_tuong_lai(self):
        actor = _make_actor("SYN-FUTURE-002", [
            RoleAssignment(role=ResearchRole.CO_INVESTIGATOR.value, assigned_at_utc=_NOW),
            RoleAssignment(role=ResearchRole.DATA_MANAGER.value, assigned_at_utc=_FUTURE),
        ])
        roles = actor.active_roles()
        assert ResearchRole.DATA_MANAGER.value not in roles, (
            f"DATA_MANAGER chưa tới assigned_at_utc nhưng vẫn nằm trong "
            f"active_roles(): {roles}"
        )
        assert ResearchRole.CO_INVESTIGATOR.value in roles


class TestDoiChungHanhViCuVanDung:
    """Đối chứng — role đơn (không xung đột), role đã BẮT ĐẦU hiệu lực,
    và role đã HẾT HẠN vẫn hoạt động đúng như cũ."""

    def test_pi_don_le_van_duoc_tu_review(self):
        actor = _make_actor("SYN-SOLO-001", [
            RoleAssignment(role=ResearchRole.PI.value, assigned_at_utc=_NOW),
        ])
        result = evaluate_rbac(actor, "RECORD_REVIEW_ATTESTATION")
        assert result.decision == "ALLOW"

    def test_role_da_bat_dau_hieu_luc_van_active(self):
        past = (_NOW_DT - timedelta(days=1)).isoformat()
        actor = _make_actor("SYN-PAST-001", [
            RoleAssignment(role=ResearchRole.PI.value, assigned_at_utc=past),
        ])
        assert ResearchRole.PI.value in actor.active_roles()

    def test_role_da_het_han_van_bi_loai_nhu_cu(self):
        past = (_NOW_DT - timedelta(days=10)).isoformat()
        expired = (_NOW_DT - timedelta(days=1)).isoformat()
        actor = _make_actor("SYN-EXPIRED-001", [
            RoleAssignment(role=ResearchRole.PI.value, assigned_at_utc=past,
                            expires_at_utc=expired),
        ])
        assert ResearchRole.PI.value not in actor.active_roles()
        result = evaluate_rbac(actor, "CREATE_DRAFT_PROJECT")
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.EXPIRED_ROLE.value
