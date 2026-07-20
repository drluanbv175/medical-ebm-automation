"""Hồi quy LOW (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):
tools/install_ebm_mcp_code_watcher.py::_watched_relative() trước đây chỉ
glob "*.py" dưới app/chatgpt_app/, trong khi pathspec THẬT của
.githooks/post-commit ('app/chatgpt_app/*') khớp MỌI file bất kể đuôi. Một
file phi-.py (vd server.py đọc prompts.json lúc chạy) sửa xong sẽ KHÔNG kích
hoạt LaunchAgent restart tức thời dù post-commit vẫn restart sau commit kế
tiếp — khoảng trống live-edit/instant-restart.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import install_ebm_mcp_code_watcher as WATCHER  # noqa: E402


def test_watched_relative_includes_non_py_files_under_chatgpt_app(tmp_path: Path) -> None:
    chatgpt_app_dir = tmp_path / "app/chatgpt_app"
    chatgpt_app_dir.mkdir(parents=True)
    (chatgpt_app_dir / "server.py").write_text("# demo\n", encoding="utf-8")
    (chatgpt_app_dir / "prompts.json").write_text("{}", encoding="utf-8")

    watched = WATCHER._watched_relative(tmp_path)

    assert "app/chatgpt_app/server.py" in watched
    assert "app/chatgpt_app/prompts.json" in watched


def test_watched_relative_excludes_pycache_and_directories(tmp_path: Path) -> None:
    chatgpt_app_dir = tmp_path / "app/chatgpt_app"
    chatgpt_app_dir.mkdir(parents=True)
    (chatgpt_app_dir / "agents.py").write_text("# demo\n", encoding="utf-8")
    pycache = chatgpt_app_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "agents.cpython-312.pyc").write_bytes(b"\x00")
    subdir = chatgpt_app_dir / "some_subdir"
    subdir.mkdir()

    watched = WATCHER._watched_relative(tmp_path)

    assert "app/chatgpt_app/agents.py" in watched
    assert not any("__pycache__" in w for w in watched)
    assert not any(w.endswith("some_subdir") for w in watched)


def test_watched_relative_always_includes_standalone_files(tmp_path: Path) -> None:
    watched = WATCHER._watched_relative(tmp_path)
    for standalone in WATCHER.WATCHED_STANDALONE:
        assert standalone in watched


def test_build_plist_passes_repo_root_as_program_argument(tmp_path: Path) -> None:
    """Hồi quy MEDIUM (vòng lặp kiểm tra-hoàn thiện vòng 3, 2026-07-21):
    watch_restart_ebm_tunnel.sh cần biết repo_root THẬT để py_compile các
    file trước khi restart (tránh nạp file đang đồng bộ dở từ OneDrive) —
    build_plist() phải truyền repo_root làm đối số 2 trong ProgramArguments."""
    (tmp_path / "app/chatgpt_app").mkdir(parents=True)
    (tmp_path / "app/core").mkdir(parents=True)
    for rel in WATCHER.WATCHED_STANDALONE:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# demo\n", encoding="utf-8")
    (tmp_path / "app/chatgpt_app/server.py").write_text("# demo\n", encoding="utf-8")

    payload = WATCHER.build_plist(tmp_path)

    assert payload["ProgramArguments"][-1] == str(tmp_path)


def test_install_local_files_locks_down_permissions(tmp_path: Path) -> None:
    """Hồi quy MEDIUM (vòng lặp kiểm tra-hoàn thiện vòng 3, 2026-07-21):
    logs.mkdir() trước đây không chmod — thư mục log TRÙNG đường dẫn với
    install_chatgpt_tunnel_launch_agent.py (đã khóa 0700/0600) bị tạo lại
    với quyền mặc định theo umask nếu installer này chạy trước, làm mất tác
    dụng lớp khóa quyền đã vá cho CÙNG thư mục đó."""
    script = tmp_path / "src" / "watch_restart_ebm_tunnel.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/bin/zsh\necho ok\n", encoding="utf-8")

    installed_launcher = tmp_path / "installed" / "watch-restart-ebm-tunnel"
    logs_dir = tmp_path / "AppSupport" / "tunnel-client" / "logs"
    destination = tmp_path / "LaunchAgents" / "vn.drluan.ebm-mcp-code-watch.plist"

    WATCHER._install_local_files(script, installed_launcher, logs_dir, destination, {"Label": "demo"})

    assert (logs_dir.stat().st_mode & 0o777) == 0o700
    assert (logs_dir.parent.stat().st_mode & 0o777) == 0o700
    assert (installed_launcher.stat().st_mode & 0o777) == 0o700
    assert (destination.stat().st_mode & 0o777) == 0o600
    assert installed_launcher.read_text(encoding="utf-8") == script.read_text(encoding="utf-8")
