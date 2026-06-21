"""Workflow review phương pháp nghiên cứu (G4–G5)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class MethodsReview:
    """Trạng thái review phương pháp — có thể cập nhật (không frozen)."""
    required_reviews: List[str] = field(default_factory=lambda: ["methodologist", "statistician"])
    completed_reviews: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True khi tất cả required_reviews đã hoàn thành."""
        return all(r in self.completed_reviews for r in self.required_reviews)

    @property
    def pending_reviews(self) -> List[str]:
        """Danh sách reviewer chưa hoàn thành."""
        return [r for r in self.required_reviews if r not in self.completed_reviews]

    def complete_review(self, reviewer: str, note: str = "") -> None:
        """Đánh dấu một reviewer đã hoàn thành."""
        if reviewer not in self.required_reviews:
            raise ValueError(f"'{reviewer}' không trong danh sách required_reviews: {self.required_reviews}")
        if reviewer not in self.completed_reviews:
            self.completed_reviews.append(reviewer)
        if note:
            self.notes.append(f"[{reviewer}] {note}")

    def is_review_complete(self) -> bool:
        """Alias rõ ràng cho .passed."""
        return self.passed


def required_method_reviews(design: str) -> MethodsReview:
    """Trả MethodsReview với danh sách reviewer tối thiểu theo thiết kế."""
    reviews = ["methodologist", "statistician"]
    if design in {"randomized_controlled_trial", "diagnostic_accuracy", "prediction_model"}:
        reviews.append("clinical_domain_expert")
    if design in {"systematic_review", "meta_analysis"}:
        reviews.extend(["librarian", "second_screener"])
    if design == "qualitative":
        reviews.append("qualitative_methods_expert")
    if design == "economic_evaluation":
        reviews.append("health_economist")
    return MethodsReview(required_reviews=reviews)
