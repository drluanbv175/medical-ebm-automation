"""Workflow review phương pháp nghiên cứu."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MethodsReview:
    required_reviews: List[str] = field(default_factory=lambda: ["methodologist", "statistician"])
    passed: bool = False
    notes: List[str] = field(default_factory=list)


def required_method_reviews(design: str) -> MethodsReview:
    reviews = ["methodologist", "statistician"]
    if design in {"randomized_controlled_trial", "diagnostic_accuracy"}:
        reviews.append("clinical_domain_expert")
    return MethodsReview(required_reviews=reviews)
