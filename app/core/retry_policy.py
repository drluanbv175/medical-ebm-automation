"""Retry policy có backoff deterministic, không tự sleep."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0

    def delays(self) -> Tuple[float, ...]:
        values = []
        for attempt in range(max(self.max_attempts - 1, 0)):
            values.append(min(self.base_delay_seconds * (2 ** attempt), self.max_delay_seconds))
        return tuple(values)

    def should_retry(self, attempt: int, retryable: bool = True) -> bool:
        return retryable and attempt < self.max_attempts


def retryable_status_codes() -> Iterable[int]:
    return (408, 429, 500, 502, 503, 504)
