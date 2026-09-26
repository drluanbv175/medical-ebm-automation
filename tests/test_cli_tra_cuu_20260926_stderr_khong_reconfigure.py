"""Hồi quy rà phản biện #30 (26/09/2026): dòng báo lỗi của `chay_cli` KHÔNG được tự làm mất mã KHÔNG BIẾT.

`configure_unicode_console()` là fail-soft: stream không có `reconfigure` (bị thay bằng wrapper) thì giữ
nguyên encoding cũ. Khi đó chính dòng «LỖI/KHÔNG BIẾT …» (có chữ tiếng Việt ngoài cp1252) ném
UnicodeEncodeError ngay trong nhánh except ⇒ traceback thoát mã 1 — TRÙNG «không thấy/không khớp».
Nay nhánh except lùi về dòng ASCII và vẫn trả mã 2.
"""
from __future__ import annotations

import importlib
import sys

import pytest


class _StreamCp1252KhongReconfigure:
    """Stream giả: không có `reconfigure`, ký tự ngoài cp1252 ⇒ UnicodeEncodeError (như console Windows)."""

    def __init__(self) -> None:
        self.da_ghi: list[str] = []

    def write(self, s: str) -> int:
        s.encode("cp1252")  # ném UnicodeEncodeError nếu có «Ỗ», «Ế»…
        self.da_ghi.append(s)
        return len(s)

    def flush(self) -> None:
        return None


@pytest.mark.parametrize("ten_module", ["tra_thuoc_quoc_te", "toan_van_guideline"])
def test_ngoai_le_la_van_tra_ma_2_khi_stderr_khong_encode_duoc(monkeypatch, ten_module):
    mod = importlib.import_module(f"tools.{ten_module}")

    def no(argv=None):
        raise RuntimeError("lỗi lạ giả lập")

    loi = _StreamCp1252KhongReconfigure()
    monkeypatch.setattr(mod, "main", no)
    monkeypatch.setattr(sys, "stderr", loi)
    assert mod.chay_cli([]) == 2
    van_ban = "".join(loi.da_ghi)
    assert "KHONG BIET" in van_ban and "RuntimeError" in van_ban
