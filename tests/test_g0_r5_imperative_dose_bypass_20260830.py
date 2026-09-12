"""Hồi quy audit cổng 30/08/2026 (khoảng hở #4): đóng lỗ lách R5 đã tự khai
trong chú thích "GIỚI HẠN THẬT" của run_g0_auto.py — một chỉ thị lâm sàng thật
lồng trong VỎ CÂU HỎI ("Có nên kê ngay 500mg X cho bệnh nhân tại phòng cấp cứu
không?") từng LỌT qua R5 sau bản vá reverse-tautology 2026-07-31.

Luật hẹp mới: vỏ câu hỏi KHÔNG miễn trừ khi câu hội đủ CẢ HAI dấu hiệu
(a) động từ y lệnh đi liền "ngay" (kê/cho/dùng/chỉ định/tiêm/truyền ngay) VÀ
(b) liều CỤ THỂ (số + đơn vị mg/mcg/g/ml/UI...).

File này kiểm cả hai vế:
- TRUE-POSITIVE: bypass đã tài liệu hoá phải bị bắt lại.
- FALSE-POSITIVE: các PICO hợp lệ chỉ mang MỘT trong hai dấu hiệu (timing-PICO
  không liều; liều không y lệnh tức thời) TUYỆT ĐỐI không được chặn oan — đúng
  bài học reverse-tautology mà bản vá 31/07 đã trả giá để học.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g0_auto as G0  # noqa: E402

_RESULTS = {"sr": [], "rct": [], "guideline": [], "observational": []}


def _r5_errors(text: str) -> list[str]:
    report = G0.guardrail_check_g0(text, _RESULTS)
    return [e for e in report["errors"] if e.startswith("R5")]


class TestImperativeDoseBypassClosed:
    """Vế TRUE-POSITIVE: y lệnh liều tức thời trong vỏ câu hỏi phải bị bắt."""

    def test_documented_bypass_now_blocked(self):
        # Chính ví dụ trong chú thích GIỚI HẠN THẬT cũ của run_g0_auto.py.
        text = "Có nên kê ngay 500mg X cho bệnh nhân tại phòng cấp cứu không?"
        errs = _r5_errors(text)
        assert errs != [], "bypass đã tài liệu hoá vẫn lọt R5"
        # Thông điệp phải nói rõ đường bắt (vỏ câu hỏi + y lệnh liều) để bác sĩ
        # hiểu vì sao một câu-có-dấu-hỏi vẫn bị chặn.
        assert any("y lệnh liều tức thời" in e for e in errs), errs

    def test_bypass_variant_truyen_ngay_with_ml_blocked(self):
        text = "Nên cho bệnh nhân truyền ngay 500 ml NaCl 0,9% tại phòng khám không?"
        assert _r5_errors(text) != []

    def test_declarative_directive_still_blocked_unchanged(self):
        # Hành vi cũ (chỉ thị khẳng định) không được đổi bởi luật hẹp mới.
        text = "Bác sĩ nên kê đơn 500mg thuốc X ngay cho bệnh nhân tại phòng khám."
        assert _r5_errors(text) != []


class TestLegitPicoStillPasses:
    """Vế FALSE-POSITIVE: PICO hợp lệ chỉ mang MỘT dấu hiệu không được chặn oan."""

    def test_plain_pico_question_not_blocked(self):
        text = "Nên dùng statin cho bệnh nhân đái tháo đường không."
        assert _r5_errors(text) == []

    def test_pico_with_dose_but_no_imperative_ngay_not_blocked(self):
        # Có liều (81mg) nhưng KHÔNG có "kê/dùng... ngay" — PICO dự phòng hợp lệ.
        text = (
            "Có nên dùng aspirin 81mg cho bệnh nhân đái tháo đường để dự phòng "
            "tiên phát biến cố tim mạch không?"
        )
        assert _r5_errors(text) == []

    def test_timing_pico_ngay_but_no_dose_not_blocked(self):
        # Có "ngay" (so sánh thời điểm) nhưng KHÔNG có liều — timing-PICO hợp lệ.
        text = (
            "Có nên chỉ định kháng sinh theo kinh nghiệm ngay khi nghi ngờ "
            "nhiễm khuẩn huyết thay vì chờ kết quả cấy máu không?"
        )
        assert _r5_errors(text) == []
