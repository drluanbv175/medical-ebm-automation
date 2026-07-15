"""Chống drift giữa 2 bảng stakeholder SONG SONG — tools/gate_contract.py và
runtime/approval_ledger.py.

Bối cảnh (vá 2026-07-15): tools/gate_contract.py::_GATE_REQUIRED_STAKEHOLDERS là
cổng THẬT (dùng bởi tools/approve_gate.py + run_g*_auto.py). runtime/approval_ledger.py
giữ một bản sao RIÊNG (GATE_REQUIRED_STAKEHOLDERS + GATE_ADDITIONAL_STAKEHOLDERS) — dùng
bởi ApprovalLedger.stakeholder_gate_status()/check_required_stakeholder_approval(), lớp
audit/verifier (KHÔNG phải cổng chặn thật, xem ghi chú trong approval_ledger.py). G8 (bình
duyệt độc lập) được thêm vào gate_contract.py ngày 2026-07-14 nhưng bản sao trong
approval_ledger.py bị bỏ sót cho tới 2026-07-15 — nếu không phát hiện, một gate mới thêm
sau này rất dễ lặp lại đúng kiểu lệch này (thêm ở 1 nơi, quên nơi kia) và khiến
ApprovalLedger coi approval synthetic/self-review là "đủ" cho gate đó (rơi vào nhánh
NO_STAKEHOLDER_REQUIREMENT).

Test này KHÔNG lặp lại logic role-alias (đã có tests/test_gate_contract_roles.py +
TestApprovalLedgerStakeholderRoles trong tests/test_approval_ledger.py) — chỉ khóa lại
BẤT BIẾN CẤU TRÚC: tập hợp gate_id có yêu cầu stakeholder phải GIỐNG NHAU giữa 2 module.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402

from runtime.approval_ledger import (  # noqa: E402
    GATE_ADDITIONAL_STAKEHOLDERS,
    GATE_REQUIRED_STAKEHOLDERS,
    _allowed_stakeholders_for_gate,
)


class TestGateKeySetParity:
    """Tập khoá gate phải đồng nhất giữa gate_contract.py và approval_ledger.py."""

    def test_same_gate_keys_as_gate_contract(self):
        gate_contract_keys = set(GC._GATE_REQUIRED_STAKEHOLDERS.keys())
        ledger_keys = set(GATE_REQUIRED_STAKEHOLDERS.keys())
        assert ledger_keys == gate_contract_keys, (
            f"Lệch khoá gate giữa 2 bảng: gate_contract.py có {gate_contract_keys}, "
            f"runtime/approval_ledger.py có {ledger_keys}. Mọi gate thêm vào một bên "
            "PHẢI được thêm vào bên kia (xem docstring module này)."
        )

    def test_includes_g2_g4_g8_g9(self):
        """Khẳng định cụ thể 4 cổng hiện có — bắt regression nếu ai lỡ xoá 1 gate
        thay vì chỉ thêm gate mới."""
        assert set(GATE_REQUIRED_STAKEHOLDERS.keys()) == {"G2", "G4", "G8", "G9"}
        assert set(GC._GATE_REQUIRED_STAKEHOLDERS.keys()) == {"G2", "G4", "G8", "G9"}

    def test_g8_maps_to_independent_peer_reviewer_in_both(self):
        assert GATE_REQUIRED_STAKEHOLDERS["G8"] == "INDEPENDENT_PEER_REVIEWER"
        assert GC._GATE_REQUIRED_STAKEHOLDERS["G8"] == ("INDEPENDENT_PEER_REVIEWER",)

    def test_allowed_groups_per_gate_match_gate_contract(self):
        """Với mỗi gate, tập NHÓM ĐƯỢC CHẤP NHẬN (primary + additional) trong
        approval_ledger.py phải khớp đúng tuple cho phép trong gate_contract.py —
        kể cả G4 (nới thêm PI) và G8 (chỉ 1 nhóm, không có additional)."""
        for gate_id, expected_groups in GC._GATE_REQUIRED_STAKEHOLDERS.items():
            ledger_groups = set(_allowed_stakeholders_for_gate(gate_id))
            assert ledger_groups == set(expected_groups), (
                f"{gate_id}: gate_contract.py cho phép {expected_groups}, "
                f"approval_ledger.py cho phép {ledger_groups}"
            )

    def test_g8_has_no_stray_additional_entry(self):
        """G8 chỉ có 1 nhóm bắt buộc (khớp gate_contract.py) — không cần/không nên
        có entry phụ trong GATE_ADDITIONAL_STAKEHOLDERS."""
        assert "G8" not in GATE_ADDITIONAL_STAKEHOLDERS
