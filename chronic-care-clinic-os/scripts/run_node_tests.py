#!/usr/bin/env python3
"""Run Node test files without relying on node being on PATH."""
from __future__ import annotations

import subprocess
from pathlib import Path

from node_runtime import find_node

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    test_files = sorted((ROOT / "tests").glob("*.test.mjs"))
    if not test_files:
        raise SystemExit("No Node test files found.")
    return subprocess.run(
        [str(find_node()), "--test", *[str(path) for path in test_files]],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
