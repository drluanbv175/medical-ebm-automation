#!/usr/bin/env python3
"""Cai LaunchAgent WatchPaths — tu restart Secure MCP Tunnel NGAY khi file
phuc vu MCP server doi TREN DIA, khong can cho git commit.

Bo sung cho .githooks/post-commit (chi phan ung SAU commit): launchd
WatchPaths phan ung tuc thi voi bat ky Edit/Write nao ghi xuong dia — ca khi
Claude Code hoac Codex con dang sua, chua commit. Chay script debounce
tools/watch_restart_ebm_tunnel.sh (>= 8s giua 2 lan restart) de khong bao
restart-storm khi luu file lien tuc.

An toan/minh bach (theo dung nguyen tac du an: KHONG tu doi git config, va o
day cung KHONG tu dong chay ma can bac si bam 1 lan):
    python3 tools/install_ebm_mcp_code_watcher.py
    (hoac --dry-run de xem plist truoc khi cai that)

Go bo:
    launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/vn.drluan.ebm-mcp-code-watch.plist
    rm ~/Library/LaunchAgents/vn.drluan.ebm-mcp-code-watch.plist
"""
from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
from pathlib import Path

LABEL = "vn.drluan.ebm-mcp-code-watch"
INSTALLED_LAUNCHER = Path.home() / ".ebm-tools/bin/watch-restart-ebm-tunnel"
# Cac file DUNG-1-CHO ngoai app/chatgpt_app/ (khong glob duoc vi khong nam
# chung 1 thu muc voi nhau).
WATCHED_STANDALONE = (
    "app/core/policy_engine.py",
    "app/core/export_policy.py",
    "tools/run_chatgpt_mcp_stdio.py",
)


def _watched_relative(repo_root: Path) -> list[str]:
    """Danh sach file can theo doi — glob app/chatgpt_app/* DUNG mau voi
    .githooks/post-commit (pathspec 'app/chatgpt_app/*') thay vi liet ke tay
    tung file rieng. Vá 2026-07-20 (vong lap kiem tra-hoan thien): truoc day
    la tuple TINH, phai sua tay + chay lai installer moi khi them file .py
    moi duoi app/chatgpt_app/ — 2 "danh sach file can theo doi" (glob hook vs
    tuple installer) duy tri doc lap nhau, dung pattern "2 lop xu ly tach roi"
    da lap lai nhieu lan trong lich su du an.

    SUA 2026-07-21 (vong lap kiem tra-hoan thien vong 2, phat hien LOW): glob
    truoc day chi lay "*.py", trong khi pathspec that cua post-commit
    ('app/chatgpt_app/*') khop MOI file bat ke duoi, khong rieng .py — neu
    tuong lai them file server.py doc luc chay (vd prompts.json), sua file do
    KHONG kich hoat restart tuc thi qua LaunchAgent nay du post-commit van
    restart sau commit ke tiep, tao khoang trong live-edit/instant-restart.
    Doi thanh "*" (chi loc file, khong lay thu muc con nhu __pycache__) de
    khop DUNG pham vi voi hook."""
    chatgpt_app_dir = repo_root / "app/chatgpt_app"
    globbed = sorted(
        str(p.relative_to(repo_root))
        for p in chatgpt_app_dir.glob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    return globbed + list(WATCHED_STANDALONE)


def build_plist(repo_root: Path) -> dict[str, object]:
    logs = Path.home() / "Library/Application Support/tunnel-client/logs"
    watched_relative = _watched_relative(repo_root)
    watch_paths = [str(repo_root / rel) for rel in watched_relative]
    missing = [p for p in watch_paths if not Path(p).is_file()]
    if missing:
        raise SystemExit(
            "Thieu file can theo doi (kiem tra lai repo_root/WATCHED_STANDALONE): "
            + ", ".join(missing)
        )
    return {
        "Label": LABEL,
        # QUAN TRONG: tro toi ban sao CUC BO (INSTALLED_LAUNCHER), KHONG PHAI file
        # trong repo/OneDrive. Da xac nhan thuc nghiem 2026-07-20: launchd spawn
        # /bin/zsh doc script TRUC TIEP tu duong dan OneDrive that bai phan lon
        # ("can't open input file") du file ton tai va doc duoc binh thuong tu
        # shell thuong — rat co the do FileProvider/TCC gioi han truy cap cua
        # tien trinh LaunchAgent. WatchPaths (theo doi thay doi) VAN tro vao repo
        # that vi phan do da chay dung — chi ProgramArguments (thuc thi) can ban
        # cuc bo. Cung mau voi install_chatgpt_tunnel_launch_agent.py.
        "ProgramArguments": ["/bin/zsh", str(INSTALLED_LAUNCHER)],
        "WatchPaths": watch_paths,
        "ThrottleInterval": 5,
        "StandardOutPath": str(logs / "code-watch.out.log"),
        "StandardErrorPath": str(logs / "code-watch.err.log"),
        "ProcessType": "Background",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools/watch_restart_ebm_tunnel.sh"
    if not script.is_file():
        raise SystemExit(f"Thieu launcher: {script}")

    payload = build_plist(repo_root)

    if args.dry_run:
        print(plistlib.dumps(payload).decode("utf-8"))
        return 0

    script.chmod(0o755)
    INSTALLED_LAUNCHER.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script, INSTALLED_LAUNCHER)
    INSTALLED_LAUNCHER.chmod(0o755)
    logs = Path.home() / "Library/Application Support/tunnel-client/logs"
    logs.mkdir(parents=True, exist_ok=True)

    destination = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(plistlib.dumps(payload, sort_keys=True))
    destination.chmod(0o644)

    uid = subprocess.run(["id", "-u"], capture_output=True, text=True, check=True).stdout.strip()
    domain = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", domain, str(destination)], check=False)
    subprocess.run(["launchctl", "bootstrap", domain, str(destination)], check=True)
    print(f"installed:{destination}")
    print(f"watching {len(_watched_relative(repo_root))} file(s) duoi {repo_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
