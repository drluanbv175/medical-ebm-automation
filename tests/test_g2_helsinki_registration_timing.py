"""Hồi quy (2026-07-17 — phát hiện khi chạy demo thật cho đề tài hài lòng bệnh nhân
C1a, Bệnh viện Quân y 175, một nghiên cứu cắt ngang TIẾN CỨU khảo sát bệnh nhân mới đến
khám): RISK_PROFILES["cross_sectional"]/["cohort"]/["case_control"] trong run_g2_auto.py
từng khai CỨNG "KHÔNG BẮT BUỘC"/"KHUYẾN KHÍCH" đăng ký nghiên cứu cho MỌI đề tài thuộc 3
thiết kế này — mâu thuẫn thẳng với Tuyên ngôn Helsinki (WMA, bản sửa 2024) §35: đăng ký
công khai BẮT BUỘC trước khi tuyển người tham gia ĐẦU TIÊN cho MỌI nghiên cứu con người có
tuyển mới, không giới hạn RCT/can thiệp.

Doctrine .claude/agents/dao-duc-dang-ky.md đã vá đúng ở round 4 (2026-07-17), nhưng CODE
(RISK_PROFILES ở đây) bị bỏ sót cho tới khi chạy demo thật lộ ra — bug "doctrine nói X
nhưng code vẫn làm Y" lặp lại. Test này khóa: registration/register_where phải NÊU RÕ điều
kiện (tiến cứu tuyển mới → bắt buộc; hồi cứu thuần túy → tùy chọn), không còn khẳng định
cứng một chiều.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g2_auto import RISK_PROFILES  # noqa: E402

_AFFECTED_DESIGNS = ("cohort", "case_control", "cross_sectional")


def test_registration_field_no_longer_unconditionally_says_not_required():
    """Hồi quy trực tiếp: bug gốc là "KHÔNG BẮT BUỘC"/"KHUYẾN KHÍCH" TRƠN (không điều
    kiện) cho 3 thiết kế quan sát — khóa lại rằng field giờ PHẢI nêu điều kiện."""
    for design in _AFFECTED_DESIGNS:
        reg = RISK_PROFILES[design]["registration"]
        assert reg not in ("KHÔNG BẮT BUỘC", "KHUYẾN KHÍCH"), (
            f"{design}: registration vẫn là tuyên bố trơn không điều kiện — "
            "đúng bug Helsinki §35 đã vá"
        )


def test_registration_field_mentions_helsinki_35_mandatory_condition():
    for design in _AFFECTED_DESIGNS:
        reg = RISK_PROFILES[design]["registration"]
        assert "BẮT BUỘC" in reg, f"{design}: thiếu điều kiện BẮT BUỘC khi tuyển mới"
        assert "Helsinki" in reg or "§35" in reg, f"{design}: thiếu trích dẫn Helsinki §35"


def test_registration_field_still_allows_optional_for_pure_retrospective():
    """Không hồi quy ngược: hồi cứu/dữ liệu thứ cấp thuần túy (không có 'người tham gia
    đầu tiên' để mốc thời gian đăng ký áp vào) vẫn phải được nêu là TÙY CHỌN — không biến
    thành 'luôn luôn bắt buộc' quá tay."""
    for design in _AFFECTED_DESIGNS:
        reg = RISK_PROFILES[design]["registration"]
        assert "TÙY CHỌN" in reg, f"{design}: thiếu nhánh tùy chọn cho hồi cứu thuần túy"


def test_register_where_no_longer_says_not_needed():
    """Hồi quy: register_where của cross_sectional từng nói cứng 'Không cần' — nếu tiến
    cứu tuyển mới thì PHẢI có nơi đăng ký thật, không thể là 'không cần'."""
    where = RISK_PROFILES["cross_sectional"]["register_where"]
    assert "không cần" not in where.lower(), (
        "register_where vẫn khẳng định 'không cần' — đúng bug Helsinki §35 đã vá"
    )
    assert "ClinicalTrials" in where or "ICTRP" in where


def test_rct_and_sr_ma_registration_unaffected_by_this_fix():
    """Không hồi quy: rct (đã đúng BẮT BUỘC từ trước) và sr_ma (đã đúng BẮT BUỘC đăng ký
    PROSPERO từ trước) không bị đổi bởi fix này."""
    assert "BẮT BUỘC" in RISK_PROFILES["rct"]["registration"]
    assert "BẮT BUỘC" in RISK_PROFILES["sr_ma"]["registration"]
