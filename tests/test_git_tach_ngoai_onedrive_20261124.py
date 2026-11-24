# -*- coding: utf-8 -*-
"""Chốt: `goi_bao_ve_hoi_dong.tim_cong_cu_word` tìm được công cụ Word của repo gốc khi `.git` nằm NGOÀI cây.

B1 (24/11/2026) dời `.git` ra `~/.ebm-git/<tên>.git` để OneDrive thôi hỏi «Remove files from OneDrive?». Khi đó
common dir không còn tên `.git`; `cha.cha` của nó không phải repo gốc ⇒ chạy từ một worktree phụ thì xuất Word bị bỏ
qua âm thầm. Bản checkout chính khai ở config `ebm.cayChinh`. Kiểm trên repo thật dựng bằng
`git init --separate-git-dir` (ngoại tuyến)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import goi_bao_ve_hoi_dong as G  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="cần git (⚪ có khai báo)")


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd,
                   capture_output=True, text=True, check=True)


def test_tim_cong_cu_word_khi_git_tach(tmp_path, monkeypatch):
    goc = tmp_path / "od" / "Claude AI"                     # repo gốc (chỉ cần có tools/<công cụ Word>)
    yk = goc / "medical-ebm-automation"                     # bản checkout chính của repo y khoa
    ext, wt = tmp_path / "ext" / "yk.git", tmp_path / "wt" / "w1"
    (goc / "tools").mkdir(parents=True)
    (goc / "tools" / G.CONG_CU_WORD).write_text("# công cụ Word giả\n", encoding="utf-8", newline="\n")
    ext.parent.mkdir(parents=True)
    _git("init", "-q", "-b", "main", "--separate-git-dir", str(ext), str(yk))
    (yk / "a.txt").write_text("a", encoding="utf-8", newline="\n")
    _git("add", "-A", cwd=yk)
    _git("commit", "-qm", "c1", cwd=yk)
    _git("worktree", "add", "-q", "-b", "n1", str(wt), cwd=yk)
    monkeypatch.delenv("EBM_GOC_REPO", raising=False)
    monkeypatch.setattr(G, "BASE", wt)                      # chạy từ worktree phụ nằm ngoài cây gốc
    assert G.tim_cong_cu_word() is None                     # chưa khai ⇒ không đoán bừa
    _git("config", "ebm.cayChinh", str(yk), cwd=yk)
    assert G.tim_cong_cu_word() == goc / "tools" / G.CONG_CU_WORD
