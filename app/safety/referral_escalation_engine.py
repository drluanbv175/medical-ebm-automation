"""Gợi ý escalation/referral khi safety signal vượt ngưỡng."""
from __future__ import annotations

from typing import Iterable

from app.safety.red_flag_engine import SafetySignal


def requires_escalation(signals: Iterable[SafetySignal]) -> bool:
    return any(signal.severity in {"high", "critical"} for signal in signals)


def escalation_message(signals: Iterable[SafetySignal]) -> str:
    critical = [signal for signal in signals if signal.severity == "critical"]
    if critical:
        return "Có cờ đỏ mức critical: cần bác sĩ đánh giá ngay trước khi tiếp tục."
    return "Không có cờ đỏ critical trong dữ liệu đã cung cấp."
