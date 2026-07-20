"""Regression tests for agent manifest sync tooling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_regenerate_agent_manifest_check_mode_matches_locked_manifest() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/regenerate_agent_manifest.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "CHECK PASS" in result.stdout
