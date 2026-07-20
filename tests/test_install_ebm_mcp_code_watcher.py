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
