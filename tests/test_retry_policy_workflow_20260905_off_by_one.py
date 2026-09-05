"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 11) trong app/core/retry_policy.py::RetryPolicy.

CƠ CHẾ LỖI: `delays()` cố ý trả `max_attempts - 1` phần tử (N lần thử cần
N-1 khoảng chờ), nhưng `should_retry(attempt)` so với `max_attempts` (không
trừ 1) — LỆCH MỘT giữa hai hàm. Với `max_attempts=3`: `delays()` trả 2 phần
tử (chỉ số 0,1) nhưng `should_retry(2)` vẫn trả True. Một caller dùng đúng
quy ước tự nhiên `delays()[attempt]` để tra khoảng chờ cho lần retry hiện
tại sẽ gặp `IndexError` ở lần thử thứ 4 (vượt quá 3 lần đã cấu hình), vì
`should_retry()` đã "bật đèn xanh" cho một lần retry mà `delays()` không có
khoảng chờ tương ứng.

BẢN VÁ: `should_retry()` so với `max_attempts - 1` — khớp đúng số phần tử
của `delays()`.

Nguyên tắc viết test: gọi THẲNG `RetryPolicy.should_retry()`/`delays()` thật,
và mô phỏng ĐÚNG vòng lặp caller tự nhiên (`while should_retry(attempt): ...
delays()[attempt] ...`) để chứng minh IndexError không còn xảy ra.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.retry_policy import RetryPolicy  # noqa: E402


class TestShouldRetryKhopSoVoiDelays:
    """★★★ Ca chính — should_retry() không bao giờ cho phép một chỉ số
    attempt vượt quá số phần tử thật sự có trong delays()."""

    def test_max_attempts_3_should_retry_dung_bang_so_phan_tu_delays(self):
        policy = RetryPolicy(max_attempts=3)
        delays = policy.delays()
        assert len(delays) == 2  # 3 lần thử -> 2 khoảng chờ (hành vi cũ, không đổi)

        # should_retry(attempt) phải False đúng tại attempt == len(delays())
        assert policy.should_retry(0) is True
        assert policy.should_retry(1) is True
        assert policy.should_retry(2) is False  # TRƯỚC bản vá: trả True (lỗi)

    def test_mo_phong_vong_lap_caller_tu_nhien_khong_con_indexerror(self):
        policy = RetryPolicy(max_attempts=3)
        delays = policy.delays()
        attempt = 0
        so_lan_lay_delay = 0
        while policy.should_retry(attempt):
            _ = delays[attempt]  # TRƯỚC bản vá: IndexError ở attempt=2
            so_lan_lay_delay += 1
            attempt += 1
        assert so_lan_lay_delay == len(delays) == 2

    def test_max_attempts_1_khong_bao_gio_duoc_retry(self):
        policy = RetryPolicy(max_attempts=1)
        assert policy.delays() == ()
        assert policy.should_retry(0) is False

    def test_max_attempts_0_khong_bao_gio_duoc_retry(self):
        policy = RetryPolicy(max_attempts=0)
        assert policy.delays() == ()
        assert policy.should_retry(0) is False


class TestRetryableFalseVanChanNhuCu:
    """Đối chứng bắt buộc — retryable=False vẫn chặn ngay bất kể attempt,
    hành vi này không đổi qua bản vá."""

    def test_retryable_false_luon_false(self):
        policy = RetryPolicy(max_attempts=5)
        assert policy.should_retry(0, retryable=False) is False
        assert policy.should_retry(3, retryable=False) is False
