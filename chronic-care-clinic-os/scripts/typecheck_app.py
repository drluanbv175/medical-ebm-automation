#!/usr/bin/env python3
"""Run the app TypeScript check without relying on OS-specific pnpm shims."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from node_runtime import find_node

ROOT = Path(__file__).resolve().parents[1]
TSC_CONFIG = ROOT / "tsconfig.check.json"

_PNPM_TYPESCRIPT_VERSION_RE = re.compile(r"typescript@(\d+)\.(\d+)\.(\d+)")


def _typescript_version_key(path: Path) -> tuple[int, int, int]:
    """Sắp theo phiên bản SỐ (semver), không phải sắp chuỗi.

    So chuỗi khiến "typescript@10.0.0" < "typescript@9.0.0" (ký tự '1' < '9'
    ở vị trí đầu tiên khác nhau) — chọn nhầm bản CŨ HƠN khi kho pnpm có cả
    bản 1 chữ số và 2 chữ số cùng lúc (vd 5.9.0 và 5.10.0)."""
    match = _PNPM_TYPESCRIPT_VERSION_RE.search(str(path))
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def find_tsc() -> Path:
    matches = sorted(
        (ROOT / "node_modules" / ".pnpm").glob("typescript@*/node_modules/typescript/bin/tsc"),
        key=_typescript_version_key,
    )
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
