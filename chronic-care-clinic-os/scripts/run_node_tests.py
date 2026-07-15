#!/usr/bin/env python3
"""Run Node test files without relying on node being on PATH."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from node_runtime import find_node
from typecheck_app import find_tsc

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    mjs_test_files = sorted((ROOT / "tests").glob("*.test.mjs"))
    ts_test_files = sorted((ROOT / "tests").glob("*.test.ts"))
    if not mjs_test_files and not ts_test_files:
        raise SystemExit("No Node test files found.")
    node = str(find_node())
    mjs_result = subprocess.run(
        [node, "--test", *[str(path) for path in mjs_test_files]],
        cwd=ROOT,
        check=False,
    )
    if mjs_result.returncode != 0 or not ts_test_files:
        return mjs_result.returncode

    with tempfile.TemporaryDirectory(prefix="ccos-node-tests-") as temp_dir:
        out_dir = Path(temp_dir)
        compile_result = subprocess.run(
            [
                node,
                str(find_tsc()),
                "--target",
                "ES2022",
                "--module",
                "CommonJS",
                "--moduleResolution",
                "Node",
                "--rootDir",
                str(ROOT),
                "--outDir",
                str(out_dir),
                "--strict",
                "--skipLibCheck",
                "--esModuleInterop",
                *[str(path) for path in ts_test_files],
            ],
            cwd=ROOT,
            check=False,
        )
        if compile_result.returncode != 0:
            return compile_result.returncode

        compiled_tests = [
            str((out_dir / path.relative_to(ROOT)).with_suffix(".js"))
            for path in ts_test_files
        ]
        return subprocess.run([node, "--test", *compiled_tests], cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
