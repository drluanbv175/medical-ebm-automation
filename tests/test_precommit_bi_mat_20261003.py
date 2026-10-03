"""Hồi quy AN-06 (03/10/2026): pre-commit y khoa quét bí mật/PII trong phần đã stage CỦA CHÍNH REPO Y KHOA.

Hook gốc (gọi ở đầu `.githooks/pre-commit`) chạy với thư mục làm việc là repo GỐC nên chốt bí mật của nó chỉ quét
phần stage của repo gốc — một tệp khoá lạc vào `config/gate_ed25519_pubkeys/` của repo này sẽ lọt. Test tách ĐÚNG
khối mới (từ dòng chú thích AN-06 tới `exit 0`) và chạy bằng sh: công cụ báo chặn ⇒ chặn · công cụ đạt ⇒ cho qua ·
công cụ quét ĐÚNG repo y khoa (`--repo`) · vắng công cụ ⇒ ⚪ cho qua. Có thêm một phép tích hợp với công cụ THẬT khi
repo gốc có nó (CI y khoa không có repo gốc ⇒ bỏ qua có khai báo).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".githooks" / "pre-commit"
SH = shutil.which("sh")
MOC = "# Them 03/10/2026 (AN-06)"

pytestmark = pytest.mark.skipif(SH is None or os.name == "nt",
                                reason="cần sh POSIX và công cụ giả dạng script (Windows: ⚪ có khai báo)")


def _khoi_moi() -> str:
    s = HOOK.read_text(encoding="utf-8")
    return s[s.index(MOC):]


def _bin_python(tmp_path: Path) -> Path:
    bin_rieng = tmp_path / "bin"
    bin_rieng.mkdir(exist_ok=True)
    py = bin_rieng / "python3"
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8", newline="\n")
    py.chmod(0o755)
    return bin_rieng


def _chay(tmp_path: Path, goc: Path | None, repo: Path) -> subprocess.CompletedProcess:
    script = tmp_path / "khoi.sh"
    script.write_text(_khoi_moi(), encoding="utf-8", newline="\n")
    env = {"HOME": str(tmp_path), "PATH": f"{_bin_python(tmp_path)}{os.pathsep}/usr/bin{os.pathsep}/bin",
           "REPO_ROOT": str(repo)}
    if goc is not None:
        env["WORKSPACE_ROOT"] = str(goc)
    return subprocess.run([SH, str(script)], cwd=repo, env=env, capture_output=True, text=True, timeout=60)


def _goc_gia(tmp_path: Path, ma: int) -> Path:
    goc = tmp_path / "goc"
    (goc / "tools").mkdir(parents=True)
    (goc / "tools" / "kiem_bi_mat_truoc_commit.py").write_text(
        "import sys, pathlib\n"
        f"pathlib.Path({str(tmp_path / 'argv.txt')!r}).write_text(' '.join(sys.argv[1:]), encoding='utf-8')\n"
        f"sys.exit({ma})\n", encoding="utf-8", newline="\n")
    return goc


def test_cong_cu_bao_chan_thi_chan_commit(tmp_path):
    repo = tmp_path / "yk"
    repo.mkdir()
    r = _chay(tmp_path, _goc_gia(tmp_path, 1), repo)
    assert r.returncode == 1 and "chot bi mat/PII" in r.stderr


def test_cong_cu_dat_thi_cho_qua_va_quet_dung_repo_y_khoa(tmp_path):
    repo = tmp_path / "yk"
    repo.mkdir()
    r = _chay(tmp_path, _goc_gia(tmp_path, 0), repo)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "argv.txt").read_text(encoding="utf-8") == f"--repo {repo}", \
        "phải quét phần stage của repo Y KHOA, không phải repo gốc"


def test_vang_cong_cu_thi_bao_trang_va_cho_qua(tmp_path):
    repo = tmp_path / "yk"
    repo.mkdir()
    for goc in (None, tmp_path / "goc-trong"):
        r = _chay(tmp_path, goc, repo)
        assert r.returncode == 0 and "bo qua chot bi mat" in r.stderr


def _cong_cu_that() -> Path | None:
    for goc in filter(None, (os.environ.get("EBM_WORKSPACE_ROOT"), str(HOOK.parents[2]))):
        p = Path(goc) / "tools" / "kiem_bi_mat_truoc_commit.py"
        if p.is_file():
            return p.parents[1]
    return None


@pytest.mark.skipif(_cong_cu_that() is None or shutil.which("git") is None,
                    reason="repo gốc chưa có tools/kiem_bi_mat_truoc_commit.py (CI y khoa / gốc chưa gộp #99)"
                           " — ⚪ có khai báo")
def test_tich_hop_cong_cu_that_chan_khoi_khoa_rieng_trong_phan_stage(tmp_path):
    repo = tmp_path / "yk"
    repo.mkdir()
    git = ["git", "-C", str(repo), "-c", "user.email=t@t.invalid", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q"], check=True)
    # Ghép chuỗi lúc chạy — tệp test này không được tự chứa một khối khoá (chốt sẽ chặn chính nó).
    (repo / "khoa.txt").write_text("-----BEGIN " + "PRIVATE KEY-----\nabc\n", encoding="utf-8", newline="\n")
    subprocess.run([*git, "add", "khoa.txt"], check=True)
    r = _chay(tmp_path, _cong_cu_that(), repo)
    assert r.returncode == 1 and "chot bi mat/PII" in r.stderr
    (repo / "khoa.txt").write_text("binh thuong\n", encoding="utf-8", newline="\n")
    subprocess.run([*git, "add", "khoa.txt"], check=True)
    assert _chay(tmp_path, _cong_cu_that(), repo).returncode == 0
