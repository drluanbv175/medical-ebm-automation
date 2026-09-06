r"""Hồi quy phát hiện #5 (LOW/MEDIUM — lỗi tiềm ẩn, chưa bị dữ liệu sản xuất
kích hoạt) của audit vòng 33 (2026-09-06) trong
tools/g10_quality_gate.py::_guardrail_ok() — so khớp chuỗi con "PASS in
status" không có ranh giới từ, khiến một giá trị guardrail dạng TEXT mang
nghĩa THẤT BẠI nhưng tình cờ chứa chuỗi con "PASS" bị chấm PASS SAI cho G10
(cổng phát hành cuối cùng — capstone release gate).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    return bool(
        ("PASS" in status or "✅" in status or "[OK]" in status)
        and not any(token in status for token in ("FAIL", "BLOCK", "LỖI", "🔴"))
    )

Ví dụ: status = "BYPASSED" → "PASS" in "BYPASSED" là True (B-Y-PASS-ED chứa
chuỗi con "PASS") → và không token loại trừ nào khớp → _guardrail_ok() trả
True, dù "BYPASSED" mang nghĩa NGƯỢC LẠI (một cơ chế kiểm tra đã bị BỎ QUA,
không phải ĐÃ QUA). Tương tự "SURPASSED_THRESHOLD_ERROR" (chứa "PASS" và
đồng thời có ý nghĩa lỗi trong tên).

Hiện tại KHÔNG module nào trong repo ghi checkpoint["guardrail"] dạng text
như vậy — mọi checkpoint thật đều dùng dict {"passed": bool}, xử lý ở nhánh
riêng phía trên _guardrail_ok() không đi qua đường so khớp chuỗi này (đã xác
nhận bằng grep run_g0_auto.py..run_g9_auto.py). Đây là lỗi TIỀM ẨN — vá
trước khi có gate/dữ liệu mới kích hoạt nó, đúng nguyên tắc phòng ngừa của
chiến dịch audit này.

BẢN VÁ: thay ``"PASS" in status`` bằng ``_PASS_WORD.search(status)`` với
``_PASS_WORD = re.compile(r"\\bPASS\\b")`` — chỉ khớp "PASS" như một TỪ độc
lập (có ranh giới trước/sau), không khớp khi nó là chuỗi con của từ khác."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g10_quality_gate as G10Q  # noqa: E402


class TestChuoiConPassKhongDuocChamPassSai:
    """★★★ Ca chính — giá trị guardrail dạng text mang nghĩa thất bại nhưng
    chứa chuỗi con "PASS" phải bị chấm KHÔNG đạt."""

    def test_bypassed_khong_duoc_cham_pass(self):
        result = G10Q._guardrail_ok({"guardrail": "BYPASSED"})
        assert result is False, (
            "TRƯỚC bản vá: 'PASS' in 'BYPASSED' là True (khớp chuỗi con "
            f"B-Y-PASS-ED) → chấm PASS sai cho một trạng thái mang nghĩa "
            f"'đã bị bỏ qua'. Thực tế: {result!r}"
        )

    def test_surpassed_threshold_error_khong_duoc_cham_pass(self):
        result = G10Q._guardrail_ok({"guardrail": "SURPASSED_THRESHOLD_ERROR"})
        assert result is False

    def test_compassionate_use_override_khong_duoc_cham_pass(self):
        result = G10Q._guardrail_ok({"guardrail": "COMPASSIONATE_USE_OVERRIDE"})
        assert result is False


class TestDoiChungChuoiPassThatVanDuocChamDung:
    """Đối chứng — các dạng "PASS" hợp lệ THẬT (từ độc lập, có ranh giới)
    vẫn phải được chấm ĐẠT như thiết kế ban đầu."""

    def test_pass_don_le_van_dat(self):
        assert G10Q._guardrail_ok({"guardrail": "PASS"}) is True

    def test_emoji_pass_van_dat(self):
        assert G10Q._guardrail_ok({"guardrail": "✅ PASS"}) is True

    def test_chu_thuong_pass_van_dat(self):
        assert G10Q._guardrail_ok({"guardrail": "pass"}) is True

    def test_nhan_ok_van_dat(self):
        assert G10Q._guardrail_ok({"guardrail": "[OK]"}) is True

    def test_dict_co_khoa_passed_khong_bi_anh_huong(self):
        """Đường xử lý CHÍNH THẬT SỰ dùng trong production (dict {"passed":
        bool}) hoàn toàn không đi qua nhánh so khớp chuỗi — bản vá không
        được đổi hành vi đường này."""
        assert G10Q._guardrail_ok({"guardrail": {"passed": True}}) is True
        assert G10Q._guardrail_ok({"guardrail": {"passed": False}}) is False

    def test_fail_that_van_bi_cham_khong_dat(self):
        assert G10Q._guardrail_ok({"guardrail": "FAIL"}) is False
        assert G10Q._guardrail_ok({"guardrail": "BLOCKED"}) is False
