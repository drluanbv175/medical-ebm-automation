#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kiểm tra môi trường Python cho dự án EBM.

Script này không cài gì và không cần mạng. Mục tiêu là giúp Claude Code/Codex
phân biệt lỗi hệ thống với lỗi venv thiếu dependency.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXPECTED_VENV_WIN = Path.home() / ".ebm-venv" / "Scripts" / "python.exe"
EXPECTED_VENV_POSIX = Path.home() / ".ebm-venv" / "bin" / "python"

REQUIRED_IMPORTS = {
    "dotenv": "python-dotenv",
    "sqlalchemy": "SQLAlchemy",
    "requests": "requests",
    "pydantic": "pydantic",
    "defusedxml": "defusedxml",
    "apscheduler": "APScheduler",
    "streamlit": "streamlit",
    "pandas": "pandas",
    "plotly": "plotly",
    "jinja2": "Jinja2",
    "deep_translator": "deep-translator",
    "docx": "python-docx",
    "openpyxl": "openpyxl",
    "markdown": "markdown",
    "PIL": "Pillow",
    "imageio_ffmpeg": "imageio-ffmpeg",
    "pytest": "pytest",
}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def command_ok(cmd: list[str]) -> bool:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception:
        return False
    return proc.returncode == 0


def expected_venv_python() -> Path:
    return EXPECTED_VENV_WIN if os.name == "nt" else EXPECTED_VENV_POSIX


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true", help="chỉ dùng exit code")
    args = parser.parse_args()

    missing = [pkg for mod, pkg in REQUIRED_IMPORTS.items() if not module_exists(mod)]
    ruff_ok = command_ok([sys.executable, "-m", "ruff", "--version"])
    if not ruff_ok:
        missing.append("ruff")

    venv = expected_venv_python()
    using_expected = Path(sys.executable).resolve() == venv.resolve() if venv.exists() else False

    if not args.quiet:
        print("============================================================")
        print("KIỂM TRA MÔI TRƯỜNG — medical-ebm-automation")
        print("============================================================")
        print(f"Python hiện tại: {sys.executable}")
        print(f"Venv chuẩn:      {venv}")
        print(f"Đang dùng venv chuẩn: {'yes' if using_expected else 'no'}")
        print(f"Dependency thiếu: {', '.join(missing) if missing else 'không'}")
        if missing:
            print("------------------------------------------------------------")
            print("Cách sửa chuẩn: cài vào venv ngoài OneDrive, không tạo venv trong repo.")
            print(f"{venv} -m pip install -r requirements.txt")
        else:
            print("KẾT QUẢ: PASS — môi trường đủ dependency để chạy app/test/lint.")

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
