"""Khoá bản vá 16/09/2026: record_evidence_surveillance_run.main() từng crash
UnicodeEncodeError trên console Windows (cp1252) ngay ở dòng in JSON cuối cùng khi
payload (trích từ log thật) chứa tiếng Việt — phát hiện khi weekly_safety.sh chạy thật
lần đầu trên Windows (bước ghi trạng thái là bước CUỐI của cả lượt, nên crash ở đây
làm mất luôn file trạng thái JSON dù các bước trước đã chạy xong).

Kiểm ĐÚNG cơ chế đã gây lỗi (stream stdout bị ép về codec không chứa ký tự tiếng Việt),
không gọi lại toàn bộ main() (kéo theo I/O file thật, log thật).
"""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "record_evidence_surveillance_run",
    Path(__file__).resolve().parents[1] / "tools" / "record_evidence_surveillance_run.py",
)
R = importlib.util.module_from_spec(_SPEC)
sys.modules["record_evidence_surveillance_run"] = R
_SPEC.loader.exec_module(R)  # type: ignore[union-attr]


class _Cp1252LikeStream(io.TextIOBase):
    """Mô phỏng stdout Windows mặc định: encode() ném lỗi với ký tự ngoài cp1252,
    và (giống sys.stdout thật) có .reconfigure() để đổi encoding tại chỗ."""

    def __init__(self) -> None:
        self._encoding = "cp1252"
        self.written: list[str] = []

    def write(self, s: str) -> int:  # type: ignore[override]
        s.encode(self._encoding)
        self.written.append(s)
        return len(s)

    def reconfigure(self, encoding: str | None = None, errors: str | None = None) -> None:
        if encoding:
            self._encoding = encoding


def test_disclaimer_with_vietnamese_diacritics_crashes_without_utf8_fix():
    stream = _Cp1252LikeStream()
    try:
        stream.write("Bắt đầu an toàn thuốc hằng tuần")
    except UnicodeEncodeError:
        return
    raise AssertionError("Kỳ vọng UnicodeEncodeError trên cp1252 giả lập — phép thử không còn nhắm đúng lỗi gốc")


def test_configure_utf8_stdio_makes_vietnamese_print_safe(monkeypatch):
    stream = _Cp1252LikeStream()
    monkeypatch.setattr(sys, "stdout", stream)
    monkeypatch.setattr(sys, "stderr", stream)

    R._configure_utf8_stdio()
    stream.write("Bắt đầu an toàn thuốc hằng tuần")

    assert stream.written == ["Bắt đầu an toàn thuốc hằng tuần"]
