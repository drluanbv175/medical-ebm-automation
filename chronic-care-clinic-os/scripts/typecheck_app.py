#!/usr/bin/env python3
"""Run the app TypeScript check without relying on OS-specific pnpm shims."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSC_CONFIG = ROOT / "tsconfig.check.json"


def _candidate_node_paths() -> list[Path]:
    paths: list[Path] = []
    env_node = os.environ.get("NODE")
    if env_node:
        paths.append(Path(env_node))

    for name in ("node", "node.exe"):
        found = shutil.which(name)
        if found:
            paths.append(Path(found))

    home = Path.home()
    paths.extend(
        [
            home / ".cache" / "codex-runtimes" / "codex-primary-runtime"
            / "dependencies" / "node" / "bin" / "node.exe",
            home / ".cache" / "codex-runtimes" / "codex-primary-runtime"
            / "dependencies" / "node" / "bin" / "node",
        ]
    )
    return paths


def find_node() -> Path:
    for path in _candidate_node_paths():
        if path.exists():
            return path
    raise SystemExit("Cannot find Node.js. Set NODE=/path/to/node or install Node on PATH.")


def find_tsc() -> Path:
    matches = sorted((ROOT / "node_modules" / ".pnpm").glob("typescript@*/node_modules/typescript/bin/tsc"))
    if matches:
        return matches[-1]
    fallback = ROOT / "node_modules" / "typescript" / "bin" / "tsc"
    if fallback.exists():
        return fallback
    raise SystemExit("Cannot find TypeScript compiler. Run pnpm install first.")


def main() -> int:
    node = find_node()
    tsc = find_tsc()
    return subprocess.run(
        [str(node), str(tsc), "-p", str(TSC_CONFIG), "--noEmit"],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
