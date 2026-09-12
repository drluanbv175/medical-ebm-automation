"""Red-flag engine deterministic cho cổng lâm sàng."""
from __future__ import annotations

import re
import unicodedata
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

# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 21, phát hiện #5):
# "liệt" (đơn âm tiết, không ranh giới từ trong so khớp substring cũ) khớp
# NHẦM vào cụm hành chính cực kỳ phổ biến trong ghi chú lâm sàng "liệt kê"
# (= liệt kê danh sách thuốc/tiền sử — không liên quan đột quỵ), gây cờ đỏ
# "stroke" (critical) giả trên câu hoàn toàn thường quy. Cùng lớp lỗi
# substring-thiếu-ranh-giới-từ đã tái phát nhiều lần trong marathon này
# ("uti"/"solution", "aware"/"awareness" x2, "gan"/"organ",
# "perspective"/"perspectives"). Đã bỏ "liệt" khỏi danh sách substring và
# chuyển sang _STROKE_LIET_RE bên dưới — dùng \b + loại trừ tường minh
# " kê" đứng ngay sau (khác các từ khoá khác, "liệt" là ÂM TIẾT riêng nên
# \b không đủ: "liệt kê" gồm 2 âm tiết cách nhau bằng khoảng trắng, mỗi âm
# tiết đều thỏa \b).
_STROKE_LIET_RE = re.compile(r"\bliệt(?!\s*kê)\b")

# SỬA 2026-09-05 (vòng 21, phát hiện #3): "spo2 88"/"spo2 <90" là khớp CHUỖI
# SỐ CỨNG (literal string), không phải so sánh ngưỡng — "SpO2 82%"/"SpO2 85"
# (đều là suy hô hấp nặng, cần cấp cứu) KHÔNG khớp bất kỳ mẫu nào trong danh
# sách cũ vì chỉ đúng số "88" từng được liệt kê. Đã thay bằng trích số thật
# sau "spo2" rồi so ngưỡng lâm sàng <90% (SpO2 dưới 90% là chỉ dấu suy hô hấp
# nặng cần đánh giá cấp cứu ngay theo hầu hết hướng dẫn).
_SPO2_RE = re.compile(r"spo2\D{0,20}?(\d{1,3})")
_SPO2_ALERT_THRESHOLD = 90


def _spo2_below_threshold(lower_text: str) -> bool:
    for match in _SPO2_RE.finditer(lower_text):
        try:
            value = int(match.group(1))
        except ValueError:
            continue
        if value < _SPO2_ALERT_THRESHOLD:
            return True
    return False


_KEYWORDS = {
    "stroke": ["méo miệng", "nói khó", "weakness", "facial droop", "aphasia"],
    "chest_pain": ["đau ngực", "chest pain", "st elevation", "troponin"],
    "sepsis": ["tụt huyết áp", "hypotension", "sepsis", "lú lẫn", "confusion"],
    "suicidal": ["tự sát", "suicide", "self-harm", "tự hại"],
    "severe_dyspnea": ["khó thở cấp", "cyanosis", "tím tái", "respiratory distress"],
    "headache_red_flag": ["đau đầu dữ dội", "sudden severe headache", "thunderclap", "cứng gáy", "papilledema"],
    "immunocompromised_fever": ["suy giảm miễn dịch", "neutropenia", "hóa trị", "transplant", "ghép tạng"],
    "anaphylaxis": ["phản vệ", "anaphylaxis", "mày đay khó thở", "tụt huyết áp sau tiêm"],
    "pregnancy_lactation": ["thai", "pregnancy", "cho con bú", "lactation"],
    "unverified_evidence": ["evidence unverified", "nguồn chưa verified", "citation unverified"],
    "conflicting_data": ["mâu thuẫn", "conflicting", "inconsistent"],
}

# Khớp bổ sung không biểu diễn an toàn được bằng substring thuần (cần ranh
# giới từ hoặc so sánh số) — xem chú thích _STROKE_LIET_RE/_spo2_below_
# threshold ở trên. Tra theo `code`, OR với _KEYWORDS[code] trong vòng lặp.
_EXTRA_MATCHERS = {
    "stroke": lambda lower: bool(_STROKE_LIET_RE.search(lower)),
    "severe_dyspnea": _spo2_below_threshold,
}


def detect_red_flags(
    text: str,
    enabled_rules: Iterable[str] = DEFAULT_RED_FLAGS.keys(),
) -> List[SafetySignal]:
    # SỬA 2026-09-05 (vòng 21, phát hiện #2): thiếu chuẩn hoá NFC trước khi so
    # khớp. Văn bản đến dưới dạng NFD (chữ nền + dấu tổ hợp RỜI — hiển thị
    # giống hệt NFC nhưng khác byte-sequence, rủi ro THẬT đã từng gây bug
    # trong chính codebase này, xem app/core/policy_engine.py::
    # contains_pii_text, SỬA 2026-07-21) khớp trượt hoàn toàn với mọi từ khoá
    # có dấu — "liệt"/"méo miệng"/"nói khó" NFD sẽ không kích hoạt cờ đỏ
    # stroke dù văn bản mô tả rõ ràng nghi đột quỵ. Cùng pattern chuẩn hoá đã
    # áp dụng ở policy_engine.py.
    lower = unicodedata.normalize("NFC", text or "").lower()
    signals: List[SafetySignal] = []
    for code in enabled_rules:
        matched = any(keyword in lower for keyword in _KEYWORDS.get(code, []))
        if not matched and code in _EXTRA_MATCHERS:
            matched = _EXTRA_MATCHERS[code](lower)
        if matched:
            severity, message, action = DEFAULT_RED_FLAGS[code]
            signals.append(SafetySignal(code=code, severity=severity, message=message, action=action))
    return signals
