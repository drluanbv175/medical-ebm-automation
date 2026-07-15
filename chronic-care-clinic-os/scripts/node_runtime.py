"""Shared Node.js runtime discovery for Codex/Windows and normal shells."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def candidate_node_paths() -> list[Path]:
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
    for path in candidate_node_paths():
        if path.exists():
            return path
    raise SystemExit("Cannot find Node.js. Set NODE=/path/to/node or install Node on PATH.")
