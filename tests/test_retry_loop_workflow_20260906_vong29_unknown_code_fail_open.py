"""Hồi quy phát hiện #1 (CRITICAL) của Workflow đối kháng đa-agent 2026-09-06
(vòng 29) trong tools/retry_loop.py — classify_error() mặc định FAIL-OPEN
(AUTO_FIX) cho mã lỗi CHƯA đăng ký trong ERROR_ROUTING_TABLE.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def classify_error(code, message=""):
        routing = ERROR_ROUTING_TABLE.get(code)
        if routing:
            severity, fix_agent = routing
        else:
            severity = ErrorSeverity.AUTO_FIX   # ← FAIL-OPEN
            fix_agent = "agent-goc"
        ...

Mã lỗi KHÔNG có trong ERROR_ROUTING_TABLE mặc định được coi là "tự sửa được"
(AUTO_FIX), KHÔNG phải "phải dừng ngay" (ESCALATE_HARD). Vì RetryLoop.run()
chỉ dừng ngay khi check.must_escalate (có lỗi ESCALATE_HARD trong danh sách),
một mã lỗi MỚI/CHƯA kịp đăng ký — kể cả khi bản chất là PII lộ, vượt cổng,
hay thiếu safety-net bắt buộc — sẽ bị đưa vào vòng "tự sửa" lặp tối đa
max_retries lần thay vì báo bác sĩ NGAY.

Đây KHÔNG phải suy đoán: chính comment trong ERROR_ROUTING_TABLE (dòng
145-159 tại thời điểm phát hiện) ghi lại HAI sự cố THẬT trước đó do đúng cơ
chế fallback này gây ra — thiếu entry R14 (an toàn kê đơn), rồi thiếu
STD-REPORT/STAT-MISMATCH/AI-DISCLOSE — cả hai lần chỉ được vá bằng cách
THÊM entry cụ thể vào bảng, không sửa cơ chế fallback gốc. Nghĩa là mã lỗi
KẾ TIẾP chưa kịp đăng ký (một guardrail mới ra đời trước khi ai đó cập nhật
bảng) sẽ tái diễn chính xác lỗi này.

BẢN VÁ: fallback mặc định đổi từ AUTO_FIX sang ESCALATE_HARD — mã lỗi chưa
đăng ký thì DỪNG NGAY báo người, thay vì mặc định "tự sửa được". Đúng
nguyên tắc fail-closed cho cái CHƯA BIẾT (BH08: thiếu thông tin không phải
bằng chứng an toàn) đã áp dụng ở mọi cổng cứng khác trong hệ.

Nguyên tắc viết test:
1. classify_error() với mã lạ phải trả ESCALATE_HARD (ca chính, đơn vị).
2. Đối chứng — mã ĐÃ đăng ký (R7, AUTO_FIX theo bảng) không bị đổi hành vi.
3. Đầu-cuối qua RetryLoop.run() thật: guardrail trả về đúng MỘT lỗi mang mã
   lạ → phải dừng NGAY ở vòng đầu tiên (check_fn chỉ được gọi 1 lần), không
   được lặp tự sửa tới max_retries — đây là ca chính có tác động thật nhất,
   vì retries lãng phí không phải vấn đề chính, vấn đề chính là bác sĩ
   không được báo ngay khi có PII/vượt cổng ẩn dưới một mã mới."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import retry_loop as RL  # noqa: E402


class TestClassifyErrorMaLaMacDinhEscalate:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. Mã lỗi chưa đăng ký phải mặc
    định ESCALATE_HARD, không phải AUTO_FIX."""

    def test_ma_la_tra_ve_escalate_hard(self):
        item = RL.classify_error("R99-NEW-PII-LEAK", "phát hiện PII lộ trong đầu ra")
        assert item.severity == RL.ErrorSeverity.ESCALATE_HARD, (
            "TRƯỚC bản vá: mã chưa đăng ký mặc định AUTO_FIX — RetryLoop coi đây là "
            "lỗi 'tự sửa được' thay vì dừng ngay báo bác sĩ, dù bản chất lỗi có thể "
            "nghiêm trọng ngang R2 (PII)/R3 (vượt cổng)."
        )

    def test_ma_la_bat_ky_deu_escalate_khong_rieng_gi_mot_ma(self):
        for code in ("XYZ-UNKNOWN", "", "R15-CHUA-DANG-KY", "STD-REPORT-V2"):
            item = RL.classify_error(code, "test")
            assert item.severity == RL.ErrorSeverity.ESCALATE_HARD, f"mã '{code}' phải escalate"


class TestDoiChungMaDaDangKyKhongDoi:
    """Đối chứng bắt buộc — mã ĐÃ có trong ERROR_ROUTING_TABLE giữ nguyên
    severity đã khai báo, bản vá không được đổi hành vi của mã đã biết."""

    def test_r7_van_la_auto_fix(self):
        item = RL.classify_error("R7", "thiếu 95% CI")
        assert item.severity == RL.ErrorSeverity.AUTO_FIX

    def test_r2_van_la_escalate_hard(self):
        item = RL.classify_error("R2", "phát hiện PII")
        assert item.severity == RL.ErrorSeverity.ESCALATE_HARD

    def test_g2_lock_van_la_wait_input(self):
        item = RL.classify_error("G2-lock", "chờ IRB")
        assert item.severity == RL.ErrorSeverity.WAIT_INPUT


class TestEndToEndRetryLoopDungNgayVoiMaLa:
    """★★★ Ca chính đầu-cuối — RetryLoop.run() thật phải dừng NGAY (không lặp
    tự sửa) khi guardrail trả về một lỗi mang mã chưa đăng ký."""

    def test_dung_ngay_o_vong_dau_khong_lap_tu_sua(self):
        loop = RL.RetryLoop(study="VONG29-TEST", gate="G6", max_retries=3)
        call_count = {"n": 0}

        def agent_fn(ctx):
            return "output nào đó"

        def check_fn(output):
            call_count["n"] += 1
            return RL.GuardrailResult(
                passed=False,
                errors=[RL.classify_error("R99-CHUA-DANG-KY", "guardrail mới chưa kịp đăng ký mã")],
            )

        result = loop.run(agent_fn, check_fn, {})

        assert call_count["n"] == 1, (
            "TRƯỚC bản vá: mã lạ được coi là AUTO_FIX nên check.must_escalate=False, "
            "vòng lặp tiếp tục tự sửa tối đa max_retries lần (check_fn bị gọi lại "
            "nhiều lần) thay vì dừng NGAY ở lần đầu tiên."
        )
        assert result.success is False
        assert result.retries_used == 1
        assert result.escalation_reason is not None
