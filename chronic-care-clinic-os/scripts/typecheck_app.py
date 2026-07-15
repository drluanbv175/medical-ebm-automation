#!/usr/bin/env python3
"""Run the app TypeScript check without relying on OS-specific pnpm shims."""
from __future__ import annotations

import subprocess
from pathlib import Path

from node_runtime import find_node

ROOT = Path(__file__).resolve().parents[1]
TSC_CONFIG = ROOT / "tsconfig.check.json"


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
