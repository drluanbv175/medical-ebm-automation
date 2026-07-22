"""Hồi quy cho phát hiện MEDIUM từ vòng lặp kiểm tra-hoàn thiện vòng 8
(2026-07-22, tái xác minh workflow wf_22b4cf6b-c01): tools/run_g9_auto.py
dùng --n-authors mặc định=1 làm SENTINEL cho "bác sĩ không truyền cờ" — nhưng
1 cũng là giá trị HỢP LỆ bác sĩ có thể gõ tường minh (vd rút bớt đồng tác giả
sau khi đã pin n_authors=3 từ trước). Trước khi vá, gõ tường minh
`--n-authors 1` khi đã có pin > 1 bị ÂM THẦM ghi đè thành giá trị pin cũ,
không có cảnh báo nào. Vá theo đúng pattern default=None đã dùng ở
run_g3_auto.py (--confirmed-n, --effect-size...).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable


def _run(study: str, extra=None):
    args = [PYTHON, str(TOOLS_DIR / "run_g9_auto.py"), "--study", study]
    if extra:
        args += extra
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)


def _load_cp(study_dir: Path) -> dict:
    return json.loads((study_dir / "G9_checkpoint.json").read_text(encoding="utf-8"))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


class TestNAuthorsSentinelFix:
    def test_no_flag_defaults_to_one_no_pin(self):
        study = "PYTEST-G9-SENTINEL-NOFLAG"
        d = REPO_ROOT / "exports" / study
        _rmtree_retry(d)
        try:
            res = _run(study)
            assert res.returncode == 0, res.stdout[-1500:]
            cp = _load_cp(d)
            assert cp["n_authors"] == 1
            assert "Khôi phục n_authors" not in res.stdout
        finally:
            _rmtree_retry(d)

    def test_explicit_one_after_pin_three_is_NOT_silently_overridden(self):
        """Bác sĩ pin 3 tác giả, sau đó CHẠY LẠI với --n-authors 1 tường minh
        (vd 1 đồng tác giả rút tên) — giá trị 1 PHẢI thắng, không bị ghi đè
        thành 3. Đây chính là bug đã vá."""
        study = "PYTEST-G9-SENTINEL-EXPLICIT1"
        d = REPO_ROOT / "exports" / study
        _rmtree_retry(d)
        try:
            res1 = _run(study, ["--n-authors", "3"])
            assert res1.returncode == 0, res1.stdout[-1500:]
            cp1 = _load_cp(d)
            assert cp1["n_authors"] == 3

            res2 = _run(study, ["--n-authors", "1"])
            assert res2.returncode == 0, res2.stdout[-1500:]
            cp2 = _load_cp(d)
            assert cp2["n_authors"] == 1, (
                "Hồi quy: --n-authors 1 tường minh bị ghi đè âm thầm bằng pin cũ (3) — "
                "đúng bug đã vá ở vòng lặp kiểm tra-hoàn thiện vòng 8."
            )
        finally:
            _rmtree_retry(d)

    def test_rerun_without_flag_restores_pin_and_logs_it(self):
        study = "PYTEST-G9-SENTINEL-RESTORE"
        d = REPO_ROOT / "exports" / study
        _rmtree_retry(d)
        try:
            res1 = _run(study, ["--n-authors", "3"])
            assert res1.returncode == 0, res1.stdout[-1500:]

            res2 = _run(study)
            assert res2.returncode == 0, res2.stdout[-1500:]
            cp2 = _load_cp(d)
            assert cp2["n_authors"] == 3
            assert "Khôi phục n_authors=3" in res2.stdout
        finally:
            _rmtree_retry(d)
