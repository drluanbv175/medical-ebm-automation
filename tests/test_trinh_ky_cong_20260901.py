"""Hồi quy cho trợ lý trình-ký (trinh_ky_cong.py, 01/09/2026).

Ba thứ phải khoá:
- Rào người-thật: stdin không phải terminal ⇒ TỪ CHỐI chạy (mã 2) — đây là
  hàng rào chống agent/pipe điều khiển buổi ký, mất nó là mất nghĩa công cụ.
- soan_lenh: soạn đúng vector đối số approve_gate (điểm nhập ký DUY NHẤT
  không đổi), cờ loại-trừ-nhau và cờ rỗng xử lý đúng.
- KY_DUOC: bảng trạng thái ký được chép đúng dây nối approve_gate 24/08.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import trinh_ky_cong as TK  # noqa: E402


class TestNgay:
    def test_ngay_hop_le(self):
        assert TK.hop_le_ngay("2026-09-01")

    def test_ngay_bia_bi_tu_choi(self):
        assert not TK.hop_le_ngay("2026-13-40")
        assert not TK.hop_le_ngay("01/09/2026")


class TestSoanLenh:
    def test_g2_du_co_bat_buoc_va_khong_het_han(self):
        tl = {
            "reviewer_ref": "HĐĐĐ/Người A",
            "g2_ethics_committee_ref": "HĐĐĐ-BVQY175",
            "g2_approval_number": "123/QĐ-HĐĐĐ",
            "g2_approval_date": "2026-09-01",
            "g2_ethics_decision": "APPROVED",
            "g2_protocol_version": "v1.1",
            "g2_no_expiry_confirmed": True,
            "g2_icf_version": "v1.0",
            "g2_recruitment_mode": "PROSPECTIVE_NEW_PARTICIPANTS",
            "g2_registration_status": "REGISTERED",
            "g2_registry": "OSF Registries",
            "g2_registration_id": "osf-abc12",
            "g2_registration_date": "2026-08-30",
        }
        lenh = TK.soan_lenh("G2", "DE-TAI", Path("/x/a.md"), tl)
        assert "--g2-approval-number" in lenh and "123/QĐ-HĐĐĐ" in lenh
        assert "--g2-no-expiry-confirmed" in lenh
        assert "--g2-valid-until" not in lenh, "no-expiry và valid-until loại trừ nhau"
        assert "--reviewer-role" in lenh and "IRB" in lenh
        assert str(TOOLS_DIR / "approve_gate.py") in lenh, (
            "điểm nhập ký DUY NHẤT phải vẫn là approve_gate.py"
        )

    def test_g2_truong_rong_khong_sinh_co(self):
        tl = {"reviewer_ref": "X", "g2_registry": "  "}
        lenh = TK.soan_lenh("G2", "DE-TAI", Path("/x/a.md"), tl)
        assert "--g2-registry" not in lenh

    def test_g8_toi_gian(self):
        lenh = TK.soan_lenh(
            "G8", "DE-TAI", Path("/x/b.md"),
            {"reviewer_ref": "PB Nguyễn B", "decision": "CONDITIONAL"},
        )
        assert "INDEPENDENT_PEER_REVIEWER" in lenh
        assert "CONDITIONAL" in lenh


class TestTrangThaiKyDuoc:
    def test_g2_chan_blocked_va_draft(self):
        assert not TK.KY_DUOC["G2"]("BLOCKED")
        assert not TK.KY_DUOC["G2"]("DRAFT_NEEDS_HUMAN_CONTENT")
        assert TK.KY_DUOC["G2"]("READY_FOR_G2_SIGNATURE")

    def test_g8_chi_nhan_dung_hai_trang_thai(self):
        assert TK.KY_DUOC["G8"]("PENDING_REAL_REVIEW_SIGNATURE")
        assert TK.KY_DUOC["G8"]("PASS_G8_REVIEW_RECORDED")
        assert not TK.KY_DUOC["G8"]("READY_FOR_INDEPENDENT_REVIEW")


class TestRaoNguoiThat:
    def test_stdin_khong_phai_terminal_bi_tu_choi(self):
        """Agent/pipe điều khiển ⇒ mã 2, không đi tới bất kỳ bước nào khác."""
        r = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "trinh_ky_cong.py"),
             "--study", "KHONG-TON-TAI", "--gate", "G2"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 2
        assert "không tương tác" in (r.stdout + r.stderr)
