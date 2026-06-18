"""Map thiết kế nghiên cứu sang reporting guideline."""
from __future__ import annotations

GUIDELINE_BY_DESIGN = {
    "randomized_controlled_trial": "CONSORT",
    "cohort": "STROBE",
    "cross_sectional": "STROBE",
    "case_control": "STROBE",
    "diagnostic_accuracy": "STARD",
    "systematic_review": "PRISMA",
    "scoping_review": "PRISMA-ScR",
}


def reporting_guideline_for_design(design: str) -> str:
    return GUIDELINE_BY_DESIGN.get(design, "EQUATOR Network checklist cần chọn thủ công")
