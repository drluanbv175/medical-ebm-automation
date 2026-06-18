"""Kiểm tra tái lập phân tích bằng hash đầu vào/đầu ra."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReproducibilityResult:
    passed: bool
    expected_hash: str
    observed_hash: str


def compare_result_hash(expected_hash: str, observed_hash: str) -> ReproducibilityResult:
    return ReproducibilityResult(
        passed=expected_hash == observed_hash,
        expected_hash=expected_hash,
        observed_hash=observed_hash,
    )
