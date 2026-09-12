r"""Hồi quy phát hiện #3 (MEDIUM/HIGH tùy vận hành) của audit đa-agent
2026-09-06 (vòng 30) trong tools/setup_gate_approval_key.py — `_ROLE_GROUPS`
thiếu "DATA_MANAGER", một nhóm stakeholder CÓ THẬT và BẮT BUỘC theo hợp
đồng cổng G5 (khóa cơ sở dữ liệu).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    _ROLE_GROUPS = ("IRB", "STATISTICIAN", "INDEPENDENT_PEER_REVIEWER", "PI")
    ap.add_argument("--role", choices=_ROLE_GROUPS, ...)

Nhưng `gate_contract.py::_GATE_REQUIRED_STAKEHOLDERS` (nguồn sự thật
CANONICAL cho việc cổng nào cần nhóm stakeholder nào) khai:
    _GATE_REQUIRED_STAKEHOLDERS = {
        "G2": ("IRB",), "G4": ("STATISTICIAN", "PI"),
        "G5": ("DATA_MANAGER", "PI"),          # ← DATA_MANAGER là nhóm THẬT
        "G8": ("INDEPENDENT_PEER_REVIEWER",), "G9": ("PI",), "G10": ("PI",),
    }

Nghĩa là DATA_MANAGER là một trong 5 nhóm stakeholder mà hệ CÔNG NHẬN và
YÊU CẦU cho cổng G5 (`reviewer_role_satisfies_gate("G5", "DATA_MANAGER")`
trả True), nhưng công cụ DUY NHẤT để tạo khóa ký RIÊNG theo vai trò lại
KHÔNG cho phép tạo khóa cho đúng nhóm này — `argparse` từ chối ngay với
"invalid choice: 'DATA_MANAGER'" trước khi main() kịp chạy một dòng nào.
Một bác sĩ/quản trị dữ liệu muốn tách khóa ký G5 khỏi khóa PI (đúng khuyến
nghị mạnh nhất mà chính docstring của file đưa ra) sẽ bị chặn ngay ở bước
đầu tiên cho đúng vai trò mà cổng G5 đòi hỏi.

BẢN VÁ: thêm "DATA_MANAGER" vào _ROLE_GROUPS.

Nguyên tắc viết test:
1. Ca chính — `--role DATA_MANAGER` phải được argparse CHẤP NHẬN và main()
   phải chạy trọn, tạo đúng file khóa riêng cho nhóm này.
2. Đối kháng nguồn sự thật — tập `_ROLE_GROUPS` phải PHỦ ĐỦ mọi nhóm
   stakeholder xuất hiện trong gate_contract.py::_GATE_REQUIRED_STAKEHOLDERS
   (tính ĐỘC LẬP ngay trong test, không mượn lại logic của bản vá) — test
   này sẽ tự bắt lại lỗi NẾU sau này gate_contract.py thêm một nhóm mới mà
   setup_gate_approval_key.py quên cập nhật theo (đúng kiểu drift đã xảy ra
   với DATA_MANAGER).
3. Đối chứng — vai trò lạ (không thuộc canonical) vẫn bị argparse từ chối
   như cũ; vai trò ĐÃ có từ trước (IRB) vẫn tạo khóa được như cũ."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import setup_gate_approval_key as SGAK  # noqa: E402


class TestDataManagerDuocChapNhanLamRole:
    """★★★ Ca chính — --role DATA_MANAGER phải chạy trọn, tạo đúng file khóa
    riêng cho nhóm này, không bị argparse từ chối."""

    def test_data_manager_trong_role_groups(self):
        assert "DATA_MANAGER" in SGAK._ROLE_GROUPS, (
            "TRƯỚC bản vá: _ROLE_GROUPS thiếu 'DATA_MANAGER' — argparse "
            "'--role' sẽ từ chối 'invalid choice' dù đây là nhóm stakeholder "
            "CÓ THẬT và bắt buộc cho cổng G5 (khóa dữ liệu)."
        )

    def test_main_tao_duoc_khoa_rieng_cho_data_manager(self, tmp_path, monkeypatch):
        fake_key_path = tmp_path / ".ebm-secrets" / "gate_approval_key"
        monkeypatch.setattr(SGAK, "_KEY_PATH", fake_key_path)
        monkeypatch.setattr(sys, "argv", ["setup_gate_approval_key.py", "--role", "DATA_MANAGER"])

        ma_thoat = SGAK.main()

        assert ma_thoat == 0
        khoa = SGAK._key_path_for("DATA_MANAGER")
        assert khoa.exists(), "Khóa riêng cho DATA_MANAGER phải được tạo ra trên đĩa"
        assert khoa.read_text(encoding="utf-8").strip(), "Khóa không được rỗng"


class TestRoleGroupsPhuDuTapCanonicalCuaGateContract:
    """★★★ Đối kháng nguồn sự thật — _ROLE_GROUPS phải chứa MỌI nhóm
    stakeholder xuất hiện trong gate_contract.py::_GATE_REQUIRED_STAKEHOLDERS.

    Tính tập canonical ĐỘC LẬP ngay trong test (không gọi lại bất kỳ helper
    nào của bản vá) để test này tự đứng vững nếu sau này gate_contract.py
    thêm một nhóm stakeholder mới mà setup_gate_approval_key.py quên cập
    nhật theo — đúng loại drift đã gây ra chính phát hiện #3 này."""

    def test_moi_nhom_stakeholder_canonical_deu_co_trong_role_groups(self):
        nhom_canonical = {
            g for reqs in GC._GATE_REQUIRED_STAKEHOLDERS.values() for g in reqs
        }
        thieu = nhom_canonical - set(SGAK._ROLE_GROUPS)
        assert not thieu, (
            f"_ROLE_GROUPS thiếu nhóm stakeholder canonical: {thieu} — "
            "một bác sĩ muốn tạo khóa riêng cho nhóm này sẽ bị argparse "
            "từ chối dù cổng thật đòi hỏi đúng nhóm đó."
        )

    def test_nhom_canonical_that_su_gom_ca_nam(self):
        # Neo cứng số lượng nhóm — nếu gate_contract.py thêm/bớt nhóm, test
        # này báo động để người viết biết cần rà lại _ROLE_GROUPS thủ công.
        nhom_canonical = {
            g for reqs in GC._GATE_REQUIRED_STAKEHOLDERS.values() for g in reqs
        }
        assert nhom_canonical == {
            "IRB", "STATISTICIAN", "PI", "DATA_MANAGER", "INDEPENDENT_PEER_REVIEWER",
        }


class TestDoiChungHanhViCuKhongDoi:
    """Đối chứng — vai trò lạ vẫn bị từ chối; vai trò IRB đã có từ trước vẫn
    tạo khóa được y hệt hành vi cũ."""

    def test_vai_tro_la_van_bi_tu_choi(self, tmp_path, monkeypatch, capsys):
        fake_key_path = tmp_path / ".ebm-secrets" / "gate_approval_key"
        monkeypatch.setattr(SGAK, "_KEY_PATH", fake_key_path)
        monkeypatch.setattr(sys, "argv", ["setup_gate_approval_key.py", "--role", "KHONG_TON_TAI"])

        try:
            SGAK.main()
            raised = False
        except SystemExit as e:
            raised = True
            assert e.code == 2
        assert raised, "argparse phải từ chối role không thuộc _ROLE_GROUPS bằng SystemExit(2)"

    def test_irb_van_tao_khoa_duoc_nhu_cu(self, tmp_path, monkeypatch):
        fake_key_path = tmp_path / ".ebm-secrets" / "gate_approval_key"
        monkeypatch.setattr(SGAK, "_KEY_PATH", fake_key_path)
        monkeypatch.setattr(sys, "argv", ["setup_gate_approval_key.py", "--role", "IRB"])

        ma_thoat = SGAK.main()

        assert ma_thoat == 0
        assert SGAK._key_path_for("IRB").exists()
