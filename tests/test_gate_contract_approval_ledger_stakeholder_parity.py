"""Khóa bất biến cấu trúc giữa tools/gate_contract.py và runtime/approval_ledger.py.

Lịch sử (2026-07-14/15): 2 file từng giữ bảng stakeholder RIÊNG, lệch nhau 2 lần
trong 24 giờ (G4 nới PI rồi quên đồng bộ; G8 thêm mới rồi quên đồng bộ) — mỗi lần
do 1 phiên khác sửa gate_contract.py mà quên bản sao trong approval_ledger.py.

Vá 2026-07-15 (hợp nhất): approval_ledger.py không còn dict tay nào — mọi giá trị
SUY RA TRỰC TIẾP từ gate_contract.py (`STAKEHOLDER_ROLE_ALIASES = _GC._STAKEHOLDER_ROLE_ALIASES`
v.v., xem đầu file approval_ledger.py). Về lý thuyết lệch không còn xảy ra được nữa
"by construction". Test này giờ đóng vai trò REGRESSION GUARD: nếu sau này có ai lỡ
tách lại thành dict tay (thay vì derive), hoặc gate_contract.py đổi hình dạng dữ
liệu theo cách phá derivation, test sẽ đỏ ngay thay vì lặng lẽ lệch lại.

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

    def test_includes_g2_g4_g5_g8_g9(self):
        """Khẳng định cụ thể 5 cổng hiện có — bắt regression nếu ai lỡ xoá 1 gate
        thay vì chỉ thêm gate mới."""
        expected = {"G2", "G4", "G5", "G8", "G9"}
        assert set(GATE_REQUIRED_STAKEHOLDERS.keys()) == expected
        assert set(GC._GATE_REQUIRED_STAKEHOLDERS.keys()) == expected

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
