"""Medication-safety screen mức trợ lý, không thay thế kiểm tra của bác sĩ/dược sĩ."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class MedicationSafetyIssue:
    code: str
    severity: str
    message: str
    action: str


HIGH_RISK_PAIRS: Sequence[Tuple[str, str, str]] = (
    ("warfarin", "nsaid", "Tăng nguy cơ chảy máu; cần bác sĩ kiểm chứng và cân nhắc bảo vệ dạ dày/theo dõi."),
    ("anticoagulant", "antiplatelet", "Tăng nguy cơ chảy máu; cần đánh giá chỉ định và nguy cơ xuất huyết."),
    ("acei", "arb", "Phối hợp ACEi + ARB thường không khuyến nghị thường quy; cần rà soát chỉ định."),
    ("nitrate", "pde5", "Nitrate + PDE5 inhibitor có nguy cơ tụt huyết áp nặng."),
    ("ckd", "nsaid", "CKD + NSAID có nguy cơ độc thận hoặc làm nặng chức năng thận."),
    ("liver_disease", "hepatotoxic", "Bệnh gan + thuốc nguy cơ độc gan cần bác sĩ kiểm chứng."),
    ("pregnancy", "teratogenic", "Thai kỳ + thuốc nguy cơ gây hại thai cần chống chỉ định/đánh giá chuyên môn."),
)


def screen_medications(medications: Iterable[str]) -> List[MedicationSafetyIssue]:
    normalized = {m.lower().strip() for m in medications}
    issues: List[MedicationSafetyIssue] = []
    for left, right, message in HIGH_RISK_PAIRS:
        if left in normalized and right in normalized:
            issues.append(MedicationSafetyIssue(
                code=f"med_pair_{left}_{right}",
                severity="high",
                message=message,
                action="Không tự áp dụng; chuyển bác sĩ/dược sĩ rà soát.",
            ))
    return issues
