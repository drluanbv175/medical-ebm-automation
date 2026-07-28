"""Đơn vị: reviewer_role_satisfies_gate() / required_reviewer_role_hint() trong
gate_contract.py — nâng cấp 2026-07-14 (kiểm soát PI/IRB/thống kê viên/phản biện).

Hai thay đổi cần khóa lại bằng test trực tiếp (không chỉ qua tích hợp G10):
  1. G4 (khóa SAP) nới từ CHỈ STATISTICIAN sang STATISTICIAN HOẶC PI — khớp
     doctrine (thiet-ke-nghien-cuu.md) vốn hướng dẫn "Chủ nhiệm đề tài" tự ký.
  2. G8 (bình duyệt độc lập) — cổng MỚI, trước đây không có yêu cầu role nào.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402


class TestG4AcceptsStatisticianOrPI:
    def test_statistician_alias_satisfies_g4(self):
        for role in ("STATISTICIAN", "BIOSTATISTICIAN", "METHODS_STATISTICS_REVIEWER",
                     "THỐNG_KÊ_VIÊN", "Thống kê viên"):
            assert GC.reviewer_role_satisfies_gate("G4", role), role

    def test_pi_alias_now_also_satisfies_g4(self):
        for role in ("PI", "PI_PROJECT_OWNER", "PRINCIPAL_INVESTIGATOR",
                     "CHỦ_NHIỆM_ĐỀ_TÀI", "Chủ nhiệm đề tài"):
            assert GC.reviewer_role_satisfies_gate("G4", role), role

    def test_unrelated_role_still_rejected_for_g4(self):
        for role in ("IRB", "PHAN_BIEN", "system_owner", ""):
            assert not GC.reviewer_role_satisfies_gate("G4", role), role

    def test_hint_lists_both_groups(self):
        hint = GC.required_reviewer_role_hint("G4")
        assert "STATISTICIAN" in hint
        assert "PI" in hint


class TestG8PeerReviewGate:
    def test_peer_reviewer_alias_satisfies_g8(self):
        for role in ("PHAN_BIEN", "PHAN_BIEN_DOC_LAP", "PEER_REVIEWER",
                     "EXTERNAL_REVIEWER", "INDEPENDENT_PEER_REVIEWER", "Phản biện"):
            assert GC.reviewer_role_satisfies_gate("G8", role), role

    def test_pi_does_not_satisfy_g8(self):
        """PI không được tự đóng vai phản biện — G8 phải fail-closed khác PI/IRB/G4."""
        assert not GC.reviewer_role_satisfies_gate("G8", "PI")
        assert not GC.reviewer_role_satisfies_gate("G8", "PRINCIPAL_INVESTIGATOR")

    def test_statistician_does_not_satisfy_g8(self):
        assert not GC.reviewer_role_satisfies_gate("G8", "STATISTICIAN")

    def test_irb_does_not_satisfy_g8(self):
        assert not GC.reviewer_role_satisfies_gate("G8", "IRB")

    def test_hint_mentions_peer_reviewer(self):
        hint = GC.required_reviewer_role_hint("G8")
        assert "PHAN_BIEN" in hint or "PEER_REVIEWER" in hint


class TestG5DataGovernanceGate:
    def test_data_manager_or_pi_satisfies_g5(self):
        for role in (
            "DATA_MANAGER",
            "DATA_STEWARD",
            "DATA_GOVERNANCE_QA_REVIEWER",
            "PI",
            "PRINCIPAL_INVESTIGATOR",
        ):
            assert GC.reviewer_role_satisfies_gate("G5", role), role

    def test_unrelated_roles_do_not_satisfy_g5(self):
        for role in ("IRB", "STATISTICIAN", "PHAN_BIEN", "ANYTHING_AT_ALL", ""):
            assert not GC.reviewer_role_satisfies_gate("G5", role), role

    def test_hint_names_data_governance_and_pi(self):
        hint = GC.required_reviewer_role_hint("G5")
        assert "DATA_MANAGER" in hint
        assert "PI" in hint


class TestUnchangedGatesStillFailClosed:
    """G2/G9 KHÔNG được nới theo — vẫn chỉ 1 nhóm role như trước, tránh sửa quá tay."""

    def test_g2_still_irb_only(self):
        assert GC.reviewer_role_satisfies_gate("G2", "IRB")
        assert not GC.reviewer_role_satisfies_gate("G2", "PI")
        assert not GC.reviewer_role_satisfies_gate("G2", "STATISTICIAN")

    def test_g9_still_pi_only(self):
        assert GC.reviewer_role_satisfies_gate("G9", "PI")
        assert not GC.reviewer_role_satisfies_gate("G9", "STATISTICIAN")
        assert not GC.reviewer_role_satisfies_gate("G9", "IRB")
        assert not GC.reviewer_role_satisfies_gate("G9", "PHAN_BIEN")

    def test_gates_without_requirement_still_noop_true(self):
        for gate_id in ("G0", "G1", "G3", "G6", "G7", "G10", "GATE_A", "GATE_B"):
            assert GC.reviewer_role_satisfies_gate(gate_id, "ANYTHING_AT_ALL"), gate_id
            assert GC.reviewer_role_satisfies_gate(gate_id, ""), gate_id
