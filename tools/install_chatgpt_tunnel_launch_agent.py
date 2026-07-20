#!/usr/bin/env python3
"""Cài LaunchAgent người dùng cho EBM Tunnel, không ghi API key vào plist."""
from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path

LABEL = "vn.drluan.ebm-copilot-tunnel"


def build_plist(launcher: Path) -> dict[str, object]:
    """Dựng cấu hình launchd trỏ tới launcher không chứa secret."""
    logs = Path.home() / "Library/Application Support/tunnel-client/logs"
    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/zsh", str(launcher)],
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 15,
        "StandardOutPath": str(logs / "launchd-ebm-copilot.out.log"),
        "StandardErrorPath": str(logs / "launchd-ebm-copilot.err.log"),
        "ProcessType": "Background",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source_launcher = root / "tools/run_ebm_tunnel_managed.sh"
    installed_launcher = Path.home() / ".ebm-tools/bin/run-ebm-tunnel-managed"
    if not source_launcher.is_file():
        raise SystemExit("Thiếu launcher tunnel.")
    payload = build_plist(installed_launcher)
    if args.dry_run:
        print(plistlib.dumps(payload).decode("utf-8"))
        return 0

    logs = Path.home() / "Library/Application Support/tunnel-client/logs"
    logs.mkdir(parents=True, exist_ok=True)
    # Khóa quyền thư mục log (vá audit MCP 2026-07-20): plist (0600) và launcher
    # (0700) đã được khóa chặt bên dưới nhưng thư mục log trước đây bị bỏ ngỏ theo
    # umask hệ thống (thường 022 → world-readable 755/644). launchd tạo file log
    # theo umask, không theo quyền thư mục cha; nhưng 0700 trên THƯ MỤC vẫn chặn
    # được user khác truy cập file bên trong (cần quyền execute trên thư mục cha).
    logs.chmod(0o700)
    logs.parent.chmod(0o700)
    installed_launcher.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_launcher, installed_launcher)
    installed_launcher.chmod(0o700)
    destination = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(plistlib.dumps(payload, sort_keys=True))
    destination.chmod(0o600)
    uid = subprocess.run(["id", "-u"], capture_output=True, text=True, check=True).stdout.strip()
    domain = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", domain, str(destination)], check=False)
    subprocess.run(["launchctl", "bootstrap", domain, str(destination)], check=True)
    subprocess.run(["launchctl", "kickstart", "-k", f"{domain}/{LABEL}"], check=True)
    print(f"installed:{destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
