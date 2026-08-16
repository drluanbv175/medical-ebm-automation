"""Hồi quy MEDIUM (vòng lặp kiểm tra-hoàn thiện vòng 3, 2026-07-21):
tools/watch_restart_ebm_tunnel.sh debounce CHỈ theo THỜI GIAN — không xác
nhận các file trong WatchPaths đã đồng bộ xong/nhất quán trước khi
`launchctl kickstart -k`. OneDrive đồng bộ từng file ĐỘC LẬP; nếu tiến trình
được restart nhập (import) một file đang ghi dở (torn write), nó crash.

Test này chạy script THẬT trong môi trường CÁCH LY hoàn toàn (HOME giả,
launchctl giả ghi log thay vì restart tiến trình thật) để xác nhận: file cú
pháp hỏng → BỎ QUA restart + không cập nhật marker; mọi file hợp lệ → restart
như bình thường. Đã xác minh thực nghiệm thủ công trước khi viết test này
(không lặp lại sai lầm vòng 1: một bản vá tưởng đúng nhưng chưa kiểm chứng
thật đã bị revert).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "watch_restart_ebm_tunnel.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("zsh") is None,
    reason="watch_restart_ebm_tunnel.sh is a macOS/zsh launchd watcher",
)

_FAKE_LAUNCHCTL = """#!/bin/bash
if [[ "$1" == "print" ]]; then
  exit 0
fi
if [[ "$1" == "kickstart" ]]; then
  echo "KICKSTART_CALLED" >> "$FAKE_MARKER_LOG"
  exit 0
fi
exit 0
"""


def _make_sandbox(tmp_path: Path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    launchctl = stub_dir / "launchctl"
    launchctl.write_text(_FAKE_LAUNCHCTL, encoding="utf-8", newline="\n")
    launchctl.chmod(0o755)
    marker_log = tmp_path / "kickstart.log"
    marker_log.write_text("", encoding="utf-8", newline="\n")

    repo = tmp_path / "repo"
    (repo / "app/chatgpt_app").mkdir(parents=True)
    (repo / "app/core").mkdir(parents=True)
    (repo / "tools").mkdir(parents=True)
    (repo / "app/chatgpt_app/agents.py").write_text("def foo():\n    return 1\n", encoding="utf-8", newline="\n")
    (repo / "app/chatgpt_app/server.py").write_text("def bar():\n    return 2\n", encoding="utf-8", newline="\n")
    (repo / "app/core/policy_engine.py").write_text("X = 1\n", encoding="utf-8", newline="\n")
    (repo / "app/core/export_policy.py").write_text("Y = 2\n", encoding="utf-8", newline="\n")
    (repo / "tools/run_chatgpt_mcp_stdio.py").write_text("Z = 3\n", encoding="utf-8", newline="\n")

    import os
    env = dict(os.environ)
    env["HOME"] = str(fake_home)
    env["FAKE_MARKER_LOG"] = str(marker_log)
    env["PATH"] = f"{stub_dir}:{env.get('PATH', '')}"
    return repo, fake_home, marker_log, env


def _run(repo: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["zsh", str(SCRIPT), str(repo)], env=env, capture_output=True, text=True, timeout=30
    )


def test_valid_repo_triggers_kickstart_and_writes_marker(tmp_path: Path) -> None:
    repo, fake_home, marker_log, env = _make_sandbox(tmp_path)
    result = _run(repo, env)
    assert result.returncode == 0
    assert marker_log.read_text(encoding="utf-8").strip() == "KICKSTART_CALLED"
    assert (fake_home / "Library/Application Support/tunnel-client/last_code_watch_restart").is_file()


def test_syntax_broken_file_skips_kickstart_and_does_not_write_marker(tmp_path: Path) -> None:
    repo, fake_home, marker_log, env = _make_sandbox(tmp_path)
    (repo / "app/chatgpt_app/server.py").write_text("def bar(\n    return 2\n", encoding="utf-8", newline="\n")

    result = _run(repo, env)

    assert result.returncode == 0
    assert marker_log.read_text(encoding="utf-8").strip() == ""
    assert "BỎ QUA restart" in result.stderr
    assert not (fake_home / "Library/Application Support/tunnel-client/last_code_watch_restart").is_file()


def test_missing_repo_root_falls_back_to_restart_without_compile_check(tmp_path: Path) -> None:
    """Không hồi quy ngược: khi không truyền repo_root (vd cài đặt cũ chưa
    cập nhật ProgramArguments), script vẫn phải restart bình thường (fail-open)."""
    _, fake_home, marker_log, env = _make_sandbox(tmp_path)
    result = subprocess.run(
        ["zsh", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0
    assert marker_log.read_text(encoding="utf-8").strip() == "KICKSTART_CALLED"
