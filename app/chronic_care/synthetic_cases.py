"""Synthetic case pack cho Chronic Care Phase 3A."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from app.chronic_care.constants import PROGRAM_CODES
from app.core.policy_engine import contains_pii_text


@dataclass(frozen=True)
class SyntheticChronicCareCase:
    patient_reference_id: str
    age_band: str
    sex: str
    program_code: str
    synthetic_status_fields: Dict[str, object] = field(default_factory=dict)
    synthetic_task_history: List[str] = field(default_factory=list)
    synthetic_appointment_status: str = "SCHEDULED"
    synthetic_risk_label: str = "UNASSESSED"
    synthetic_care_plan_draft_status: str = "DRAFT"

    def searchable_text(self) -> str:
        return " ".join([
            self.patient_reference_id,
            self.age_band,
            self.sex,
            self.program_code,
            self.synthetic_appointment_status,
            self.synthetic_risk_label,
            self.synthetic_care_plan_draft_status,
            repr(self.synthetic_status_fields),
            " ".join(self.synthetic_task_history),
        ])


def build_synthetic_case_pack(now: datetime | None = None) -> List[SyntheticChronicCareCase]:
    now = now or datetime.now(timezone.utc)
    cases: List[SyntheticChronicCareCase] = []
    distributions = [
        ("HTN_PROGRAM", "SYN-HTN", 10),
        ("T2D_PROGRAM", "SYN-T2D", 8),
        ("DYSLIPIDEMIA_PROGRAM", "SYN-DL", 6),
        ("CARDIOMETABOLIC_RISK_PROGRAM", "SYN-CM", 3),
        ("POLYPHARMACY_REVIEW_PROGRAM", "SYN-PR", 2),
        ("POST_DISCHARGE_REVIEW_PROGRAM", "SYN-PD", 1),
    ]
    counter = 0
    for program_code, prefix, count in distributions:
        assert program_code in PROGRAM_CODES
        for idx in range(1, count + 1):
            counter += 1
            due_delta = -7 if counter in {2, 11, 20, 29} else 14
            status_fields: Dict[str, object] = {
                "next_review_due_at": (now + timedelta(days=due_delta)).isoformat(),
                "medication_review_status": "OVERDUE" if counter in {5, 24} else "CURRENT",
                "lab_review_required": counter in {6, 14},
                "post_discharge_flag": program_code == "POST_DISCHARGE_REVIEW_PROGRAM",
                "evidence_status": "MISSING" if counter in {7, 23} else "COMPLETE",
                "claim_status": "MISSING" if counter == 7 else "COMPLETE",
                "blocked_export_probe": counter == 30,
            }
            cases.append(SyntheticChronicCareCase(
                patient_reference_id=f"{prefix}-{idx:03d}",
                age_band="45-64" if counter % 3 else "65-79",
                sex="F" if counter % 2 == 0 else "M",
                program_code=program_code,
                synthetic_status_fields=status_fields,
                synthetic_task_history=["task_escalated"] if counter == 29 else [],
                synthetic_appointment_status="NO_SHOW" if counter in {3, 12} else "SCHEDULED",
                synthetic_risk_label="RED" if counter in {8, 30} else ("YELLOW" if counter % 4 == 0 else "GREEN"),
                synthetic_care_plan_draft_status=(
                    "REJECTED" if counter == 9 else
                    "APPROVED_FOR_SHADOW" if counter == 10 else
                    "PENDING_REVIEW"
                ),
            ))
    return cases


def validate_synthetic_case_pack(cases: List[SyntheticChronicCareCase]) -> None:
    if len(cases) < 30:
        raise ValueError("Synthetic case pack must contain at least 30 cases")
    for case in cases:
        if contains_pii_text(case.searchable_text()):
            raise ValueError(f"PII-like text detected in synthetic case {case.patient_reference_id}")
        if not case.patient_reference_id.startswith("SYN-"):
            raise ValueError(f"Invalid synthetic ID {case.patient_reference_id}")
