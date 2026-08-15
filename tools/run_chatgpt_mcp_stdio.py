#!/usr/bin/env python3
# ruff: noqa: E402, I001
"""Launcher tuyệt đối cho tunnel-client quản lý MCP EBM qua stdio."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["EBM_MCP_TRANSPORT"] = "stdio"

from app.chatgpt_app.server import main  # noqa: E402


if __name__ == "__main__":
    main()
