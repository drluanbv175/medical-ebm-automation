"""
Test cổng G2 (đạo đức/IRB) của run_stats_analysis.py — vá 2026-07-10.

Bối cảnh: run_stats_analysis.py là script DUY NHẤT chạy phân tích thống kê trên DỮ LIỆU
BỆNH NHÂN THẬT (CSV/Excel do bác sĩ cấp). Trước vá này nó chỉ chặn theo G4 (SAP)/G5 (khóa DB)
mà KHÔNG kiểm G2 (phê duyệt Hội đồng Đạo đức) — trong khi sibling run_g6_auto.py (chỉ sinh
template, không đụng dữ liệu thật) lại CÓ cổng G2. Nghĩa là có thể chạy phân tích thật trên
dữ liệu thật mà không có cổng kỹ thuật nào xác nhận đã được phê duyệt đạo đức. Test này khóa
lại hành vi: G2 chưa duyệt → script TỪ CHỐI chạy, độc lập với G4/G5.
"""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "tools" / "run_stats_analysis.py"


def _run(*extra):
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--study", "__g2gate_pytest__",
         "--data", "/khong_ton_tai_9z9z.csv", *extra],
        cwd=str(_REPO_ROOT), capture_output=True, text=True,
    )


class TestRunStatsG2Gate:
    def test_blocks_when_g2_not_approved_even_if_sap_bypassed(self):
        # Bỏ qua G4/G5 bằng --i-confirm-sap-locked, NHƯNG G2 chưa duyệt và KHÔNG có cờ IRB
        # → phải DỪNG ở cổng G2 (exit != 0) với đúng thông báo, TRƯỚC khi đụng dữ liệu.
        res = _run("--i-confirm-sap-locked")
        assert res.returncode != 0
        assert "G2" in res.stdout
        assert "đạo đức" in res.stdout or "IRB" in res.stdout

    def test_passes_g2_gate_with_irb_confirm(self):
        # Bỏ qua CẢ G2 (--i-confirm-irb-approved) và G4/G5 → phải VƯỢT được cổng, rồi mới
        # thất bại ở bước tải dữ liệu (lỗi KHÁC, không phải thông báo dừng-G2).
        res = _run("--i-confirm-sap-locked", "--i-confirm-irb-approved")
        combined = res.stdout + res.stderr
        assert "DỪNG: G2" not in combined  # không còn bị chặn ở cổng G2

    def test_g2_gate_is_independent_of_sap_gate(self):
        # Không cờ nào → phải dừng ở cổng ĐẦU TIÊN gặp phải (G2, vì G2 đứng trước G4/G5).
        res = _run()
        assert res.returncode != 0
        assert "G2" in res.stdout
