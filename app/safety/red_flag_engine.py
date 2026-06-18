"""Red-flag engine deterministic cho cổng lâm sàng."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class SafetySignal:
    code: str
    severity: str
    message: str
    action: str


DEFAULT_RED_FLAGS = {
    "stroke": (
        "critical",
        "Yếu/liệt/nói khó/méo miệng nghi đột quỵ",
        "Đánh giá cấp cứu ngay theo quy trình đột quỵ.",
    ),
    "chest_pain": (
        "critical",
        "Đau ngực nghi hội chứng vành cấp",
        "Chuyển cấp cứu/đánh giá ECG-troponin theo thực hành địa phương.",
    ),
    "sepsis": ("critical", "Sốt hoặc nhiễm trùng kèm tụt huyết áp/lú lẫn", "Escalate cấp cứu, đánh giá sepsis."),
    "suicidal": ("critical", "Ý tưởng tự sát/tự hại", "Không để bệnh nhân một mình; chuyển đánh giá khẩn."),
    "severe_dyspnea": (
        "critical",
        "Khó thở cấp có dấu hiệu nặng",
        "Đánh giá cấp cứu ngay; không xử lý như tư vấn thường quy.",
    ),
    "headache_red_flag": (
        "critical",
        "Đau đầu kèm cờ đỏ thần kinh/toàn thân",
        "Chuyển đánh giá khẩn, loại trừ nguyên nhân nguy hiểm.",
    ),
    "immunocompromised_fever": (
        "critical",
        "Sốt ở người suy giảm miễn dịch",
        "Escalate khẩn để đánh giá nhiễm trùng nặng.",
    ),
    "anaphylaxis": (
        "critical",
        "Dấu hiệu phản vệ",
        "Xử trí cấp cứu phản vệ theo quy trình địa phương.",
    ),
    "pregnancy_lactation": (
        "high",
        "Thai kỳ/cho con bú cần kiểm tra chống chỉ định và an toàn thuốc",
        "Không tự khuyến nghị thuốc; chuyển bác sĩ xác minh.",
    ),
    "unverified_evidence": (
        "high",
        "Nguồn chứng cứ chưa verified",
        "Không phát hành khuyến nghị; gắn nhãn needs_review.",
    ),
    "conflicting_data": (
        "high",
        "Dữ liệu đầu vào mâu thuẫn",
        "Yêu cầu làm rõ thay vì giả định im lặng.",
    ),
}

_KEYWORDS = {
    "stroke": ["liệt", "méo miệng", "nói khó", "weakness", "facial droop", "aphasia"],
    "chest_pain": ["đau ngực", "chest pain", "st elevation", "troponin"],
    "sepsis": ["tụt huyết áp", "hypotension", "sepsis", "lú lẫn", "confusion"],
    "suicidal": ["tự sát", "suicide", "self-harm", "tự hại"],
    "severe_dyspnea": ["khó thở cấp", "spo2 88", "spo2 <90", "cyanosis", "tím tái", "respiratory distress"],
    "headache_red_flag": ["đau đầu dữ dội", "sudden severe headache", "thunderclap", "cứng gáy", "papilledema"],
    "immunocompromised_fever": ["suy giảm miễn dịch", "neutropenia", "hóa trị", "transplant", "ghép tạng"],
    "anaphylaxis": ["phản vệ", "anaphylaxis", "mày đay khó thở", "tụt huyết áp sau tiêm"],
    "pregnancy_lactation": ["thai", "pregnancy", "cho con bú", "lactation"],
    "unverified_evidence": ["evidence unverified", "nguồn chưa verified", "citation unverified"],
    "conflicting_data": ["mâu thuẫn", "conflicting", "inconsistent"],
}


def detect_red_flags(
    text: str,
    enabled_rules: Iterable[str] = DEFAULT_RED_FLAGS.keys(),
) -> List[SafetySignal]:
    lower = (text or "").lower()
    signals: List[SafetySignal] = []
    for code in enabled_rules:
        if any(keyword in lower for keyword in _KEYWORDS.get(code, [])):
            severity, message, action = DEFAULT_RED_FLAGS[code]
            signals.append(SafetySignal(code=code, severity=severity, message=message, action=action))
    return signals
