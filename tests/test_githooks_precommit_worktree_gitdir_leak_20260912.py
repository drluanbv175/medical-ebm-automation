"""Hồi quy 12/09/2026 — `.githooks/pre-commit` (wrapper repo y khoa) rò
biến môi trường GIT_DIR/GIT_INDEX_FILE khi commit chạy trong git worktree
LIÊN KẾT (`git worktree add`), làm ROOT_HOOK (hook đồng bộ ở repo workspace
gốc) so sánh nhầm INDEX, sinh cảnh báo "source/mirror drift" hàng loạt
hoàn toàn không liên quan tới commit thật.

CƠ CHẾ LỖI (đã đo thực nghiệm bằng 4 bước trước khi viết test này —
không suy đoán): khi git chạy hook cho một commit trong worktree LIÊN
KẾT, nó export GIT_DIR/GIT_INDEX_FILE — BIẾN MÔI TRƯỜNG THẬT — trỏ vào
thư mục quản trị của CHÍNH worktree đó
(".../<repo>/.git/worktrees/<tên>"). Wrapper `cd` đúng vào WORKSPACE_ROOT
rồi gọi ROOT_HOOK như một tiến trình con trong subshell — tiến trình con
đó KẾ THỪA nguyên các biến GIT_* kia.

ĐIỀU TƯỞNG NHƯ HIỂN NHIÊN NHƯNG SAI (tự đo lại để không viết test dựa
trên suy đoán): "git rev-parse --show-toplevel" bên trong ROOT_HOOK
KHÔNG bị kéo lệch theo GIT_DIR đã rò — với git 2.54, lệnh này chỉ đơn
giản in $PWD khi GIT_WORK_TREE không được set kèm theo. Nghĩa là ROOT_HOOK
KHÔNG "cd nhầm về worktree lồng bên trong" như suy luận ban đầu (đã thử
và bị chính phép đột biến bác bỏ). CƠ CHẾ THẬT: ROOT_HOOK vẫn chạy ĐÚNG
thư mục ($PWD = WORKSPACE_ROOT), nhưng các lệnh git PHÍA SAU (cụ thể là
`git diff --name-only -- .claude/agents .Codex/agents .codex/agents`) vẫn
đọc INDEX của repo SAI (medical-ebm-automation, do GIT_DIR/GIT_INDEX_FILE
còn rò) trong khi so với các FILE THẬT trên đĩa tại $PWD đúng (workspace).
Hai repo đều mirror file cùng tên tương đối (".claude/agents/*.md") theo
đúng thiết kế đồng bộ nguồn↔runtime của repo này, nhưng nội dung khác
nhau tại bất kỳ thời điểm nào — nên MỌI file trùng tên đó bị báo "đã sửa"
so với INDEX sai, dù file thật trên đĩa hoàn toàn không đổi. Đây chính là
danh sách 150+ file giả đã quan sát được khi chẩn đoán lỗi.

BẢN VÁ: unset các biến GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE/GIT_COMMON_DIR/
GIT_PREFIX/GIT_OBJECT_DIRECTORY ngay trong subshell, TRƯỚC khi cd và gọi
ROOT_HOOK — buộc mọi lệnh git bên trong ROOT_HOOK tự định vị lại repo (và
INDEX) theo $PWD thật thay vì theo GIT_DIR/GIT_INDEX_FILE đã rò.

NGUYÊN TẮC VIẾT TEST (khớp quy ước repo — kiểm HÀNH VI thật, không đếm
chuỗi, không dựa suy đoán chưa đo):
    Test đọc THẲNG nội dung wrapper thật từ đĩa (`.githooks/pre-commit`).
    Để tách bạch hai điều đang được kiểm — (a) "git có thật sự export
    GIT_DIR/GIT_INDEX_FILE cho hook của worktree liên kết không" (đã xác
    nhận bằng thực nghiệm thủ công trên hai repo thật khi chẩn đoán lỗi,
    KHÔNG lặp lại ở đây vì phụ thuộc phiên bản git, không ổn định để làm
    test tự động) và (b) "wrapper có tự bảo vệ đúng trước các biến đó
    không" — test này CHỈ kiểm (b): tạo một worktree liên kết THẬT (để lấy
    đúng đường dẫn thư mục quản trị mà git THẬT SỰ dùng cho worktree đó,
    không đoán), rồi tự set GIT_DIR/GIT_INDEX_FILE bằng đúng giá trị đó và
    gọi thẳng wrapper thật bằng subprocess.

    ROOT_HOOK giả (ở "WORKSPACE_ROOT" giả) chỉ chạy đúng MỘT lệnh
    `git diff --name-only -- sentinel.txt` (thay cho chuỗi kiểm tra thật,
    nặng, cần venv) — "workspace" và "repo" giả đều có sentinel.txt CÙNG
    TÊN nhưng NỘI DUNG KHÁC NHAU, mô phỏng đúng cơ chế mirror cùng đường
    dẫn tương đối khác nội dung của .claude/agents thật.

    Test thứ hai (`TestBanVaThatSuCanThiet`) tự dựng lại đúng bản TRƯỚC khi
    vá (bỏ dòng "unset ...") và chứng minh phép thử ở test đầu THẬT SỰ
    phân biệt được đúng/sai — một phép đột biến ngược, khớp quy ước "kiểm
    bằng đột biến" mà CLAUDE.md của repo này đòi hỏi cho mọi bản vá. Chính
    phép đột biến ngược nay lại là thứ đã BÁC BỎ giả thuyết cơ chế ban đầu
    của tôi (cd sai thư mục) và buộc phải đo lại cho ra cơ chế thật (index
    sai) — ghi lại đúng tinh thần "một đột biến không bắt được có thể là
    lỗi của phép thử, không phải bằng chứng chốt yếu" mà chính repo này đã
    từng rút ra (xem CLAUDE.md, mục BH93/BH94/BH95).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

EBM_ROOT = Path(__file__).resolve().parent.parent
WRAPPER_HOOK_SRC = EBM_ROOT / ".githooks" / "pre-commit"

DONG_UNSET = (
    "  unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR "
    "GIT_PREFIX GIT_OBJECT_DIRECTORY\n"
)

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "pytest",
    "GIT_AUTHOR_EMAIL": "pytest@example.invalid",
    "GIT_COMMITTER_NAME": "pytest",
    "GIT_COMMITTER_EMAIL": "pytest@example.invalid",
}


def _run(cmd, cwd, env, timeout=30):
    return subprocess.run(
        cmd, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout
    )


def _git(cwd, *args, env):
    return _run(["git", *args], cwd=cwd, env=env)


def _moi_truong_sach(tmp_path) -> dict:
    """Moi truong toi thieu cho git chay duoc, khong ke thua GIT_* cua
    chinh tien trinh pytest dang chay (session nay cung dang o trong mot
    git worktree that, khong duoc de GIT_DIR that ro vao phep thu)."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path),
    }
    env.update(_GIT_ENV)
    return env


@pytest.fixture()
def gia_lap_wrapper_va_worktree(tmp_path):
    """Dung:
      workspace/            (WORKSPACE_ROOT gia — CHINH NO cung la 1 git
                              repo, giong "Claude AI" that)
        sentinel.txt         (noi dung A — dai dien file mirror THAT tren
                               dia, khong doi trong luc test)
        .githooks/pre-commit (ROOT_HOOK gia: chay dung 1 lenh
                               "git diff --name-only -- sentinel.txt" roi
                               ghi ket qua vao marker, thoat 0)
        repo/                (mo phong medical-ebm-automation)
          sentinel.txt         (noi dung B — KHAC noi dung A, mo phong
                                 repo mirror cung ten khac noi dung)
          .githooks/pre-commit  (dung NGUYEN VAN wrapper that tu dia)
          scripts/regenerate_agent_manifest.py  (stub, exit 0)
          tools/agent_gate_governance.py        (stub, exit 0)
        repo-worktree/       (worktree LIEN KET that cua repo/, tao bang
                               "git worktree add" — de lay dung duong dan
                               thu muc quan tri ".git/worktrees/<ten>" ma
                               GIT THAT dung, khong doan)

    Tra ve (workspace, repo, wt, marker, admin_dir, env). marker RONG
    nghia la sach (dung); marker chua "sentinel.txt" nghia la ROOT_HOOK da
    so sanh nham file that tren dia voi INDEX cua repo SAI (dung bang
    chung cho co che ro ri that su, khong phai gia dinh)."""
    assert WRAPPER_HOOK_SRC.is_file(), f"khong tim thay wrapper that: {WRAPPER_HOOK_SRC}"

    env = _moi_truong_sach(tmp_path)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    assert _git(workspace, "init", "-q", env=env).returncode == 0
    assert _git(workspace, "config", "user.name", "pytest", env=env).returncode == 0
    assert _git(workspace, "config", "user.email", "pytest@example.invalid", env=env).returncode == 0
    (workspace / "sentinel.txt").write_text(
        "noi dung THAT cua workspace\n", encoding="utf-8", newline="\n"
    )
    assert _git(workspace, "add", "sentinel.txt", env=env).returncode == 0
    assert _git(workspace, "commit", "-q", "-m", "khoi tao workspace", env=env).returncode == 0

    marker = workspace / "root_hook_diff.txt"
    root_hooks_dir = workspace / ".githooks"
    root_hooks_dir.mkdir()
    root_hook = root_hooks_dir / "pre-commit"
    root_hook.write_text(
        "#!/bin/sh\n"
        f'git diff --name-only -- sentinel.txt > "{marker}" 2>&1\n'
        "exit 0\n",
        encoding="utf-8",
        newline="\n",
    )
    root_hook.chmod(0o755)

    repo = workspace / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q", env=env).returncode == 0
    assert _git(repo, "config", "user.name", "pytest", env=env).returncode == 0
    assert _git(repo, "config", "user.email", "pytest@example.invalid", env=env).returncode == 0

    hooks_dir = repo / ".githooks"
    hooks_dir.mkdir()
    wrapper_dst = hooks_dir / "pre-commit"
    wrapper_dst.write_text(
        WRAPPER_HOOK_SRC.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
    )
    wrapper_dst.chmod(0o755)

    # Wrapper that (sau khi goi ROOT_HOOK) con tu chay them
    # "scripts/regenerate_agent_manifest.py --check" va
    # "tools/agent_gate_governance.py" KHONG DIEU KIEN (khong co "if [ -f ]"
    # bao ve nhu buoc verify_exports_integrity.py cuoi cung) - stub hai file
    # nay de repo gia khong bi chan boi ly do khong lien quan (thieu file),
    # giu tin hieu kiem tra CHI o cho ROOT_HOOK so sanh dung/sai INDEX.
    (repo / "scripts").mkdir()
    (repo / "scripts" / "regenerate_agent_manifest.py").write_text(
        "import sys\nsys.exit(0)\n", encoding="utf-8", newline="\n"
    )
    (repo / "tools").mkdir()
    (repo / "tools" / "agent_gate_governance.py").write_text(
        "import sys\nsys.exit(0)\n", encoding="utf-8", newline="\n"
    )

    (repo / "sentinel.txt").write_text(
        "noi dung KHAC cua repo long ben trong\n", encoding="utf-8", newline="\n"
    )
    add = _git(
        repo, "add", "sentinel.txt", ".githooks/pre-commit",
        "scripts/regenerate_agent_manifest.py", "tools/agent_gate_governance.py",
        env=env,
    )
    assert add.returncode == 0, add.stderr
    commit0 = _git(repo, "commit", "-q", "-m", "khoi tao repo", env=env)
    assert commit0.returncode == 0, commit0.stderr

    wt = workspace / "repo-worktree"
    wt_add = _git(repo, "worktree", "add", str(wt), "-b", "nhanh-worktree", env=env)
    assert wt_add.returncode == 0, wt_add.stderr

    admin_dirs = list((repo / ".git" / "worktrees").iterdir())
    assert len(admin_dirs) == 1, (
        f"ky vong dung 1 thu muc quan tri worktree, thay {admin_dirs}"
    )
    admin_dir = admin_dirs[0]

    return workspace, repo, wt, marker, admin_dir, env


def _goi_wrapper_voi_moi_truong_ro_ri(wt, admin_dir, env):
    """Goi wrapper THAT (nam trong worktree lien ket "wt") nhu git se lam
    khi chay hook cho mot commit trong worktree do - tu set
    GIT_DIR/GIT_INDEX_FILE bang DUNG gia tri thu muc quan tri that (khong
    doan), khop thuc nghiem da do duoc tren repo that khi chan doan loi
    (GIT_WORK_TREE/GIT_COMMON_DIR RONG trong thuc nghiem do, nen khong set
    o day)."""
    env_ro_ri = dict(env)
    env_ro_ri["GIT_DIR"] = str(admin_dir)
    env_ro_ri["GIT_INDEX_FILE"] = str(admin_dir / "index")
    wrapper = wt / ".githooks" / "pre-commit"
    return _run(["sh", str(wrapper)], cwd=wt, env=env_ro_ri)


class TestWrapperThatKhongRoBienMoiTruong:
    """★★★ Ca chính — wrapper THẬT (đọc từ đĩa, đã vá) không được để
    ROOT_HOOK so sánh nhầm INDEX khi GIT_DIR/GIT_INDEX_FILE bị rò vào môi
    trường của nó."""

    def test_root_hook_khong_bao_dong_gia_khi_gitdir_bi_ro(
        self, gia_lap_wrapper_va_worktree
    ):
        workspace, repo, wt, marker, admin_dir, env = gia_lap_wrapper_va_worktree

        ket_qua = _goi_wrapper_voi_moi_truong_ro_ri(wt, admin_dir, env)

        assert ket_qua.returncode == 0, (
            "Wrapper da va phai cho qua (ROOT_HOOK gia luon exit 0, cac stub "
            f"scripts/tools cung exit 0); stdout={ket_qua.stdout} "
            f"stderr={ket_qua.stderr}"
        )

        noi_dung_marker = marker.read_text(encoding="utf-8")
        assert noi_dung_marker == "", (
            "ROOT_HOOK phai so sanh sentinel.txt voi INDEX cua CHINH "
            "workspace (sach, khong drift) — thay vi do, no bao dong "
            f"'{noi_dung_marker.strip()}', nghia la GIT_DIR/GIT_INDEX_FILE "
            "van con ro ri tro ve INDEX cua repo SAI (worktree lien ket)."
        )

    def test_wrapper_that_co_dung_dong_unset(self):
        """Doi chung cau truc — dam bao test tren khong ngau nhien xanh vi
        wrapper that da mat dong unset (vd ai do lo revert)."""
        noi_dung = WRAPPER_HOOK_SRC.read_text(encoding="utf-8")
        assert DONG_UNSET in noi_dung, (
            "Khong tim thay dong 'unset GIT_DIR ...' trong wrapper that — "
            "ban va 12/09/2026 co the da bi revert."
        )


class TestBanVaThatSuCanThiet:
    """Kiem chung nguoc (dot bien): dung lai dung noi dung wrapper NHUNG
    bo dong 'unset ...' (mo phong chinh xac ban TRUOC khi va) va chung
    minh marker cho thay ROOT_HOOK bao dong gia dung nhu da quan sat khi
    chan doan loi that — tuc la phep thu o class tren THAT SU phan biet
    duoc dung/sai, khong phai mot bai test luon xanh bat ke wrapper co
    dung hay khong."""

    def test_neu_bo_dong_unset_root_hook_bao_dong_gia(
        self, gia_lap_wrapper_va_worktree
    ):
        workspace, repo, wt, marker, admin_dir, env = gia_lap_wrapper_va_worktree

        wrapper_trong_wt = wt / ".githooks" / "pre-commit"
        noi_dung = wrapper_trong_wt.read_text(encoding="utf-8")
        assert DONG_UNSET in noi_dung, "fixture chua dung wrapper that? cau truc da doi?"
        noi_dung_cu = noi_dung.replace(DONG_UNSET, "", 1)
        wrapper_trong_wt.write_text(noi_dung_cu, encoding="utf-8", newline="\n")
        wrapper_trong_wt.chmod(0o755)

        ket_qua = _goi_wrapper_voi_moi_truong_ro_ri(wt, admin_dir, env)

        # ROOT_HOOK gia luon exit 0 nen wrapper van thanh cong o ca hai ban -
        # diem khac biet nam o NOI DUNG marker, khong o ket qua thoat.
        assert ket_qua.returncode == 0, ket_qua.stderr

        noi_dung_marker = marker.read_text(encoding="utf-8")
        assert "sentinel.txt" in noi_dung_marker, (
            "TRUOC ban va: ROOT_HOOK phai bao dong gia 'sentinel.txt' (dung "
            "bang chung cho hanh vi loi that su xay ra khi GIT_DIR/"
            "GIT_INDEX_FILE con ro ri, khong phai gia dinh). Marker thuc te "
            f"rong hoac khac: '{noi_dung_marker!r}'"
        )
