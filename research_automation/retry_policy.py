"""
retry_policy — Retry deterministic có giới hạn + safe-stop (V4.3.2).

CHỈ retry các lỗi deterministic được whitelist. KHÔNG retry vô hạn.
Timeout/lỗi không whitelist → safe-stop (raise SafeStop), KHÔNG nuốt lỗi.
OFFLINE · không sleep mạng (không network).
"""

from __future__ import annotations

import dataclasses
from typing import Callable, FrozenSet, Optional


class SafeStop(RuntimeError):
    """Dừng an toàn: hết retry hoặc gặp lỗi không được phép retry."""


# Các lỗi deterministic ĐƯỢC phép retry (tên class).
DEFAULT_RETRYABLE: FrozenSet[str] = frozenset({
    "TransientDeterministicError",
    "QueueContentionError",
})


class TransientDeterministicError(RuntimeError):
    """Lỗi tạm thời deterministic (vd contention nội bộ) — được phép retry."""


@dataclasses.dataclass
class RetryResult:
    ok: bool
    attempts: int
    value: object = None
    reason_code: Optional[str] = None


class RetryPolicy:
    def __init__(self, max_attempts: int = 3,
                 retryable: FrozenSet[str] = DEFAULT_RETRYABLE):
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self.retryable = retryable

    def run(self, fn: Callable[[], object]) -> RetryResult:
        """
        Gọi fn() tối đa max_attempts lần. Retry CHỈ khi lỗi thuộc whitelist.
        Lỗi khác → SafeStop ngay (không retry). Hết lượt → SafeStop.
        """
        last_exc: Optional[BaseException] = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                value = fn()
                return RetryResult(ok=True, attempts=attempt, value=value)
            except Exception as exc:  # noqa: BLE001 — phân loại ngay dưới
                # Audit 2026-07-11: trước là "except BaseException" — bắt luôn cả
                # KeyboardInterrupt/SystemExit, biến ngắt tiến trình thật thành
                # SafeStop business-logic bình thường thay vì để nó lan lên đúng cách.
                last_exc = exc
                name = type(exc).__name__
                if name not in self.retryable:
                    # Không retry: safe-stop tức thì.
                    raise SafeStop(
                        f"NON_RETRYABLE_SAFE_STOP:{name}:{exc}"
                    ) from exc
                # còn lượt thì thử lại (không sleep mạng); hết lượt → safe-stop
        raise SafeStop(
            f"RETRY_LIMIT_EXCEEDED_SAFE_STOP:{self.max_attempts}:"
            f"{type(last_exc).__name__ if last_exc else 'UNKNOWN'}"
        )
