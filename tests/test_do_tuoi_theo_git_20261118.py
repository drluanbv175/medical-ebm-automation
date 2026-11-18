"""Độ tươi checkpoint: git ghi lại tệp (pull, checkout, trả tệp) KHÔNG còn làm cổng sau bị báo «cũ» giả (18/11/2026).

Ca thật: trả hai checkpoint G0/G2 của C1a về đúng bản git (`git checkout --`) làm mtime nhảy thành «bây giờ» ⇒ G1/G3/G4
bị báo «cũ», G10-AUTO-03 CHẶN, dù nội dung không đổi một byte. Bộ test dựng repo git thật trong thư mục tạm và khoá:
gỡ cảnh báo CHỈ khi đủ ba bằng chứng; thượng nguồn đổi thật, commit chung che cổng cũ, tệp đang sửa, ngoài git, không có
git ⇒ vẫn «cũ» như trước.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import pipeline_freshness as PF  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="máy không có git")

T0 = time.time() - 100_000  # mốc commit đầu, đủ xa để mọi mtime «bây giờ» đều muộn hơn


def _git(goc: Path, *args: str, ngay: float | None = None) -> None:
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
    if ngay is not None:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"@{int(ngay)} +0000"
    subprocess.run(["git", "-c", "user.name=thu", "-c", "user.email=thu@example.invalid", "-c", "commit.gpgsign=false",
                    "-c", "core.hooksPath=/dev/null", *args], cwd=goc, check=True, capture_output=True, env=env)


def _ghi(out: Path, gate: str, noi_dung: dict, mtime: float) -> Path:
    p = out / f"{gate}_checkpoint.json"
    p.write_text(json.dumps(noi_dung), encoding="utf-8", newline="\n")
    os.utime(p, (mtime, mtime))
    return p


def _repo(tmp_path: Path):
    """Repo có G0 (sinh trước) và G1 (sinh sau), cùng commit lúc T0 — chuỗi đang TƯƠI."""
    goc = tmp_path / "repo"
    out = goc / "exports" / "de-tai"
    out.mkdir(parents=True)
    _git(goc, "init", "-q")
    _ghi(out, "G0", {"topic": "A"}, T0 - 1000)
    _ghi(out, "G1", {"aim": "B"}, T0 - 500)
    _git(goc, "add", "-A")
    _git(goc, "commit", "-q", "-m", "dau", ngay=T0)
    assert PF.find_stale_gates(out) == []
    return goc, out


def _git_ghi_lai(goc: Path, out: Path, gate: str) -> None:
    """Mô phỏng git ghi lại tệp (như pull/checkout): xoá rồi lấy lại đúng bản HEAD ⇒ mtime = bây giờ."""
    (out / f"{gate}_checkpoint.json").unlink()
    _git(goc, "checkout", "--", f"exports/de-tai/{gate}_checkpoint.json")


def test_git_ghi_lai_tep_thuong_nguon_khong_doi_thi_khong_bao_cu(tmp_path, capsys):
    goc, out = _repo(tmp_path)
    _git_ghi_lai(goc, out, "G0")
    assert [i["gate"] for i in PF.find_stale_gates(out, dung_git=False)] == ["G1"]  # mtime đơn thuần: báo cũ giả
    bc = PF.stale_report(out)
    assert bc["fresh"] is True and bc["stale_gates"] == []
    assert [(c["gate"], c["upstream"]) for c in bc["cuu_theo_git"]] == [("G1", "G0")]
    PF.print_report(bc)
    assert "ℹ [git] G1 ← G0" in capsys.readouterr().out  # báo cáo nói rõ cặp được gỡ, không gỡ lặng lẽ


def test_thuong_nguon_doi_noi_dung_sau_commit_cong_sau_van_bao_cu(tmp_path):
    goc, out = _repo(tmp_path)
    _ghi(out, "G0", {"topic": "A — đổi tên đề tài"}, T0 + 100)
    _git(goc, "commit", "-q", "-am", "doi-g0", ngay=T0 + 200)
    _git_ghi_lai(goc, out, "G0")  # mtime do git (muộn hơn commit) nhưng nội dung G0 đã đổi kể từ commit của G1
    bc = PF.stale_report(out)
    assert bc["stale_gates"] == ["G1"] and bc["cuu_theo_git"] == []


def test_commit_chung_cong_sau_da_cu_khong_duoc_xoa_canh_bao(tmp_path):
    """G1 sinh trước, G0 sửa sau, rồi commit CHUNG — mtime G0 sớm hơn giờ commit (mtime thật) ⇒ vẫn «cũ»."""
    goc = tmp_path / "repo"
    out = goc / "exports" / "de-tai"
    out.mkdir(parents=True)
    _git(goc, "init", "-q")
    _ghi(out, "G1", {"aim": "B"}, T0 - 1000)
    _ghi(out, "G0", {"topic": "A2"}, T0 - 100)
    _git(goc, "add", "-A")
    _git(goc, "commit", "-q", "-m", "chung", ngay=T0)
    bc = PF.stale_report(out)
    assert bc["stale_gates"] == ["G1"] and bc["cuu_theo_git"] == []


def test_cong_sau_dang_sua_chua_commit_khong_go(tmp_path):
    goc, out = _repo(tmp_path)
    _git_ghi_lai(goc, out, "G0")
    _ghi(out, "G1", {"aim": "B sửa tại chỗ"}, T0 - 500)  # G1 khác HEAD (chưa commit), mtime cũ giữ nguyên
    assert PF.stale_report(out)["stale_gates"] == ["G1"]


def test_thuong_nguon_dang_sua_chua_commit_khong_go(tmp_path):
    goc, out = _repo(tmp_path)
    _ghi(out, "G0", {"topic": "A sửa tại chỗ"}, time.time())  # G0 khác HEAD, mtime bây giờ
    assert PF.stale_report(out)["stale_gates"] == ["G1"]


def test_thuong_nguon_chua_duoc_git_theo_doi_khong_go(tmp_path):
    goc = tmp_path / "repo"
    out = goc / "exports" / "de-tai"
    out.mkdir(parents=True)
    _git(goc, "init", "-q")
    _ghi(out, "G1", {"aim": "B"}, T0 - 500)
    _git(goc, "add", "-A")
    _git(goc, "commit", "-q", "-m", "chi-g1", ngay=T0)
    _ghi(out, "G0", {"topic": "A"}, time.time())  # G0 chưa add
    assert PF.stale_report(out)["stale_gates"] == ["G1"]


def test_ngoai_git_giu_nguyen_ket_luan_theo_mtime(tmp_path):
    out = tmp_path / "khong-git"
    out.mkdir()
    _ghi(out, "G0", {"topic": "A"}, time.time())
    _ghi(out, "G1", {"aim": "B"}, time.time() - 5000)
    bc = PF.stale_report(out)
    assert bc["stale_gates"] == ["G1"] and bc["cuu_theo_git"] == []


def test_khong_chay_duoc_git_giu_nguyen_ket_luan_theo_mtime(tmp_path, monkeypatch):
    goc, out = _repo(tmp_path)
    _git_ghi_lai(goc, out, "G0")

    def _hong(*_a, **_k):
        raise FileNotFoundError("git")

    monkeypatch.setattr(PF.subprocess, "run", _hong)
    assert PF.stale_report(out)["stale_gates"] == ["G1"]


def test_khong_co_cap_cu_thi_khong_goi_git(tmp_path, monkeypatch):
    """Chuỗi tươi theo mtime ⇒ không dựng nhân chứng git (không tốn lệnh git cho đa số lượt đo)."""
    goc, out = _repo(tmp_path)

    def _cam(*_a, **_k):
        raise AssertionError("không được gọi git khi không có cặp «cũ»")

    monkeypatch.setattr(PF.subprocess, "run", _cam)
    assert PF.stale_report(out)["fresh"] is True
