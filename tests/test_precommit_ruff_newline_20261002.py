"""Hồi quy PM-05 (02/10/2026): pre-commit y khoa chạy `ruff check .` và bất biến newline vùng ký.

Hai bước CI chặn nhiều nhất: 14/29 lượt CI đỏ từ 14/09 (chạy < 2 giây); PR #65 ngày 02/10 đỏ 4/4 vì đúng lỗi newline.
Test tách ĐÚNG khối mới của `.githooks/pre-commit` (từ `RUFF=""` tới `exit 0`) và chạy bằng sh với ruff GIẢ (HOME giả)
và công cụ newline GIẢ: ruff lỗi ⇒ chặn · newline lỗi ⇒ chặn · cả hai đạt ⇒ cho qua · máy không có ruff ⇒ ⚪ cho qua.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".githooks" / "pre-commit"
SH = shutil.which("sh")


def _khoi_moi() -> str:
    s = HOOK.read_text(encoding="utf-8")
    i = s.index('RUFF=""')
    return s[i:]


def _chay(tmp_path: Path, ruff_ma: int | None, newline_ma: int) -> subprocess.CompletedProcess:
    home = tmp_path / "home"
    if ruff_ma is not None:
        b = home / ".ebm-venv" / "bin"
        b.mkdir(parents=True)
        r = b / "ruff"
        r.write_text(f"#!/bin/sh\necho ruff-gia \"$@\"\nexit {ruff_ma}\n", encoding="utf-8", newline="\n")
        r.chmod(0o755)
    else:
        home.mkdir()
    (tmp_path / "tools").mkdir()
    nl = tmp_path / "tools" / "kiem_newline_vung_ky.py"
    nl.write_text(f"import sys\nprint('newline-gia')\nsys.exit({newline_ma})\n", encoding="utf-8", newline="\n")
    script = tmp_path / "khoi.sh"
    script.write_text(_khoi_moi(), encoding="utf-8", newline="\n")
    # PATH riêng chỉ có «python3» (bọc trình thông dịch đang chạy) — KHÔNG lấy thư mục venv vì ở đó có sẵn ruff thật.
    bin_rieng = tmp_path / "bin"
    bin_rieng.mkdir()
    py = bin_rieng / "python3"
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8", newline="\n")
    py.chmod(0o755)
    env = {"HOME": str(home), "PATH": f"{bin_rieng}{os.pathsep}/usr/bin{os.pathsep}/bin"}
    return subprocess.run([SH, str(script)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)


pytestmark = pytest.mark.skipif(SH is None or os.name == "nt",
                                reason="cần sh POSIX và ruff giả dạng script (Windows: ⚪ có khai báo)")


def test_ruff_loi_thi_chan(tmp_path):
    r = _chay(tmp_path, ruff_ma=1, newline_ma=0)
    assert r.returncode == 1 and "ruff check . co loi" in r.stderr


def test_newline_loi_thi_chan(tmp_path):
    r = _chay(tmp_path, ruff_ma=0, newline_ma=2)
    assert r.returncode == 1 and "bat bien newline" in r.stderr and "newline-gia" in r.stderr


def test_ca_hai_dat_thi_cho_qua(tmp_path):
    assert _chay(tmp_path, ruff_ma=0, newline_ma=0).returncode == 0


def test_khong_co_ruff_thi_bao_trang_va_cho_qua(tmp_path):
    if shutil.which("ruff", path=f"/usr/bin{os.pathsep}/bin"):
        pytest.skip("máy có ruff hệ thống trong /usr/bin — không dựng được ca «vắng ruff»")
    r = _chay(tmp_path, ruff_ma=None, newline_ma=0)
    assert r.returncode == 0 and "khong co ruff" in r.stderr


def test_khoi_moi_chay_cung_lenh_voi_ci():
    s = _khoi_moi()
    assert '"$RUFF" check . -q' in s and "python3 tools/kiem_newline_vung_ky.py" in s
    ci = (HOOK.parents[1] / ".github" / "workflows" / "offline-ci.yml").read_text(encoding="utf-8")
    assert "ruff check ." in ci and "tools/kiem_newline_vung_ky.py" in ci, "CI đổi lệnh thì pre-commit phải đổi theo"
