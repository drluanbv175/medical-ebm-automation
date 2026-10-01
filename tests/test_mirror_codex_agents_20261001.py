"""Mirror `.codex/agents/` (Codex nạp agent DỰ ÁN từ đây) phải khớp bản sinh từ `.claude/agents/*.md`. 01/10/2026.

VÌ SAO. Repo track mirror từ commit 20660c0 (08/09) nhưng không có bộ sinh lẫn chốt canh. Đo 01/10 trên nhánh mặc
định: kỳ vọng 84 tệp · khớp 3 · lệch nội dung 79 (cả 50/50 agent) · thiếu 2 — mọi phiên Codex trong repo này chạy
đội agent của GIỮA THÁNG 7 (README còn QUADAS-2, «Ba cổng nghiên cứu»). Đây là lớp 1 của chốt hai lớp: chạy ở CI
(ubuntu + windows) nên bắt lệch TRƯỚC khi merge; lớp 2 là BH144 ở repo gốc (mỗi lần mở phiên trên máy thật, bắt
phần lọt sau merge vì CI không phải check bắt buộc). Bộ sinh `tools/sinh_mirror_codex.py` tự chứa nên CI đơn-repo
chạy trọn; phép đối chiếu với bộ sinh gốc chỉ chạy khi tìm thấy repo gốc EBM.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _nap(ten: str, duong: Path):
    spec = importlib.util.spec_from_file_location(ten, duong)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten] = mod  # @dataclass cần module có trong sys.modules lúc thi hành
    spec.loader.exec_module(mod)
    return mod


SMC = _nap("sinh_mirror_codex_test_20261001", REPO / "tools" / "sinh_mirror_codex.py")


def test_mirror_codex_that_khop_ban_sinh_tu_claude_agents():
    loi = SMC.kiem()
    assert not loi, (
        f"{len(loi)} lỗi ở mirror .codex/agents — Codex trong repo này sẽ chạy đội agent CŨ. "
        "Sửa: python3 tools/sinh_mirror_codex.py --ghi rồi git add .codex/agents\n  " + "\n  ".join(loi[:40]))


def test_moi_tep_ky_vong_deu_duoc_git_track():
    """Có trên đĩa mà chưa `git add` thì checkout tươi (CI, worktree Codex, Codex Cloud) vẫn thiếu tệp đó."""
    try:
        r = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--", ".codex/agents"],
                           capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"không đọc được git ls-files ({type(e).__name__}) — bản xuất không có .git, chỉ kiểm được đĩa")
    da_track = {Path(p).name for p in r.stdout.decode("utf-8").split("\0") if p}
    chua_track = sorted(set(SMC.ban_ky_vong()) - da_track)
    assert not chua_track, (f"{len(chua_track)} tệp mirror chưa được git track — chạy: git add .codex/agents\n  "
                            + "\n  ".join(chua_track[:40]))


def test_ban_dung_cua_repo_y_khoa_trung_byte_bo_sinh_goc():
    """Bản dựng chép ở repo y khoa phải ra ĐÚNG byte như `tools/sync_agents_to_codex.py` của repo gốc, ở cả hai nhãn."""
    goc_ebm = _nap("goc_ebm_test_mirror_20261001", REPO / "tools" / "goc_ebm.py")
    goc = goc_ebm.tim_goc_ebm(REPO)
    bo_sinh_goc = goc / "tools" / "sync_agents_to_codex.py"
    if not (goc_ebm.la_goc_ebm(goc) and bo_sinh_goc.is_file()):
        pytest.skip("không tìm thấy repo gốc EBM (CI đơn-repo / worktree ngoài cây; đặt EBM_REPO_ROOT để bật) — "
                    "đối chiếu chéo khi đó do BH144 của repo gốc đảm nhận")
    sac = _nap("sync_agents_to_codex_goc_test_20261001", bo_sinh_goc)
    sac.SOURCE_DIR = REPO / ".claude" / "agents"
    for nhan in (".codex/agents", ".Codex/agents"):
        ky_vong_goc = sac.expected_files(nhan)
        ban_chep = SMC.ban_ky_vong(nhan=nhan)
        assert sorted(ky_vong_goc) == sorted(ban_chep), f"[{nhan}] tập tệp khác bộ sinh gốc"
        khac = sorted(t for t in ky_vong_goc if ky_vong_goc[t] != ban_chep[t])
        assert not khac, (f"[{nhan}] {len(khac)} tệp khác byte bộ sinh gốc — bộ sinh gốc đã đổi, sửa "
                          f"tools/sinh_mirror_codex.py theo: {khac[:10]}")


def _dung_nguon(nguon: Path, than_agent: str) -> None:
    nguon.mkdir(parents=True)
    (nguon / "thu-nghiem.md").write_text(
        "---\nname: thu-nghiem\ndescription: agent thử\n---\n" + than_agent, encoding="utf-8", newline="\n")
    (nguon / "_SO-THU.md").write_text("Đọc `.claude/agents/thu-nghiem.md` trước.\n", encoding="utf-8", newline="\n")


def test_kiem_co_rang_tren_fixture(tmp_path):
    """Chốt phải ĐỎ đúng loại lỗi: lệch một ký tự, sai nhãn, thiếu tệp, tệp mồ côi — và XANH khi vừa sinh xong."""
    nguon, dich = tmp_path / "nguon", tmp_path / "dich"
    _dung_nguon(nguon, "Trỏ sang .claude/agents/_SO-THU.md khi cần.\n")
    assert sorted(SMC.ghi(nguon, dich)) == ["_SO-THU.md", "thu-nghiem.toml"]
    assert SMC.kiem(nguon, dich) == []
    toml = dich / "thu-nghiem.toml"
    goc = toml.read_text(encoding="utf-8")
    assert ".codex/agents/_SO-THU.md" in goc and ".Codex/" not in goc

    toml.write_text(goc.replace("khi cần", "khi can"), encoding="utf-8", newline="\n")
    assert SMC.kiem(nguon, dich) == ["LỆCH .codex/agents/thu-nghiem.toml"]

    toml.write_text(goc.replace(".codex/agents", ".Codex/agents"), encoding="utf-8", newline="\n")
    assert SMC.kiem(nguon, dich) == ["LỆCH .codex/agents/thu-nghiem.toml"], "sai nhãn đường dẫn phải đỏ"

    toml.unlink()
    assert SMC.kiem(nguon, dich) == ["THIẾU .codex/agents/thu-nghiem.toml"]

    SMC.ghi(nguon, dich)
    (dich / "agent-da-xoa.toml").write_text(goc, encoding="utf-8", newline="\n")
    loi = SMC.kiem(nguon, dich)
    assert any(dong.startswith("MỒ CÔI .codex/agents/agent-da-xoa.toml") for dong in loi), loi


def test_than_agent_lam_hong_toml_bi_bat(tmp_path):
    """Thân agent chứa `'''` làm TOML literal string vỡ — Codex sẽ không nạp được agent đó."""
    if SMC.tomllib is None:
        pytest.skip("Python thiếu tomllib/tomli — không kiểm được cú pháp TOML")
    nguon, dich = tmp_path / "nguon", tmp_path / "dich"
    _dung_nguon(nguon, "Ví dụ chuỗi ''' làm vỡ TOML.\n")
    SMC.ghi(nguon, dich)
    loi = SMC.kiem(nguon, dich)
    assert any(dong.startswith("TOML HỎNG .codex/agents/thu-nghiem.toml") for dong in loi), loi
