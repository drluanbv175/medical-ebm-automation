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
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 11) — trước đây so với
        # self.max_attempts, LỆCH MỘT so với delays() (vốn cố ý trả max_attempts-1
        # phần tử: N lần thử cần N-1 khoảng chờ). Với max_attempts=3, should_retry(2)
        # trả True trong khi delays() chỉ có 2 phần tử (chỉ số 0,1) — caller dùng
        # đúng quy ước "attempt là chỉ số cho delays()[attempt]" sẽ bị IndexError ở
        # lần thử thứ 4 (vượt quá 3 lần đã cấu hình). Trừ thêm 1 để hai hàm khớp số:
        # attempt hợp lệ để còn được retry (và tra delays()[attempt] an toàn) chỉ còn
        # 0..max_attempts-2.
        return retryable and attempt < self.max_attempts - 1


def retryable_status_codes() -> Iterable[int]:
    return (408, 429, 500, 502, 503, 504)
