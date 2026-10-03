"""Hồi quy 03/10/2026 — cây git y khoa không mang trạng thái phiên harness (AN-09) và báo cáo ĐO (B6).

AN-09: 4 tệp `exports/<đề tài>/.claude/state/*.jsonl` (bộ đệm phiên do hook harness ghi) bị track từ trước khi có luật
`**/.claude/state/` — lộ đường dẫn máy/mã phiên ra repo công khai. B6: `tools/kiem_chi_tiet_he_nghien_cuu.py` ghi
`exports/<mã>/KIEM_CHI_TIET_report.{json,md}` mà bản track (12/09) lệch hiện trạng, mỗi lần đo làm bẩn cây.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("git") is None or not (REPO / ".git").exists(),
                                reason="cần git và cây git")


def _tracked() -> list[str]:
    ra = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, timeout=60)
    assert ra.returncode == 0, ra.stderr
    return [f for f in ra.stdout.decode("utf-8", "replace").split("\0") if f]


def test_khong_track_trang_thai_phien_harness():
    lot = [f for f in _tracked() if re.search(r"(^|/)\.claude/(state|sessions|logs)/", f)]
    assert lot == [], f"tệp trạng thái harness đang bị track: {lot[:5]}"


def test_khong_track_bao_cao_do_kiem_chi_tiet():
    lot = [f for f in _tracked() if f.endswith(("KIEM_CHI_TIET_report.json", "KIEM_CHI_TIET_report.md"))]
    assert lot == [], f"báo cáo ĐO bị track (lệch hiện trạng, làm bẩn cây mỗi lần đo): {lot}"
