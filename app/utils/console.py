"""Tiện ích console nhỏ cho CLI chạy ổn trên Windows/macOS.

Một số máy Windows dùng code page như cp1252, không in được ký tự tiếng Việt
hoặc biểu tượng trạng thái. Các CLI y khoa không được sập chỉ vì dòng cảnh báo
không encode được, nên cấu hình stream theo hướng fail-soft.
"""
from __future__ import annotations

import sys
from typing import TextIO


def _safe_reconfigure(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            return


def configure_unicode_console() -> None:
    """Cho phép CLI in Unicode mà không gây UnicodeEncodeError trên Windows."""
    _safe_reconfigure(sys.stdout)
    _safe_reconfigure(sys.stderr)
