"""Hồi quy cho tools/_workspace_root.py — vá 07/09/2026 (cùng đợt
tools/ban_sao_tran.py bên repo drluanbv175/ebm-drluanbv175, xem CLAUDE.md
mục "VÁ 07/09/2026").

Nhiều verifier ở đây (`ROOT = REPO.parent`) giả định `medical-ebm-automation`
(REPO) nằm LỒNG một cấp bên trong workspace gốc (đúng máy thật, kiến trúc
OneDrive cây chung: REPO là con trực tiếp của "Claude AI", cùng cấp với
EBM-Dashboards/, sync/, tools/ cấp gốc). Trên phiên cloud, workspace gốc là
ANH EM (sibling) của REPO dưới cùng thư mục cha, không phải CHA trực tiếp —
`REPO.parent` chỉ trỏ tới thư mục chứa cả hai, không có `tools/`, `sync/`
nào. `resolve_workspace_root()` phải dò được CẢ HAI kiến trúc.

Ba kịch bản khoá bằng fixture `tmp_path` (không đụng máy thật):
  ① LỒNG   — workspace/repo/, marker ở workspace  → trả về workspace (cha).
  ② ANH EM — cha/repo/ + cha/workspace/ (marker)   → trả về cha/workspace.
  ③ KHÔNG THẤY — không đâu có marker              → fallback về repo.parent
    (giữ hành vi cũ: lỗi đường dẫn rõ ràng hơn thà báo "không tìm thấy
    file" còn hơn suy đoán sai trong im lặng — BH08)."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from _workspace_root import resolve_workspace_root  # noqa: E402


def _mkrepo(base: Path, name: str = "medical-ebm-automation") -> Path:
    repo = base / name
    (repo / "tools").mkdir(parents=True)
    return repo


class TestLong:
    """Kịch bản ① — REPO nằm lồng trong workspace gốc (máy thật)."""

    def test_marker_o_cha_truc_tiep_tra_ve_cha(self, tmp_path):
        workspace = tmp_path / "Claude AI"
        workspace.mkdir()
        (workspace / "sync").mkdir()
        repo = _mkrepo(workspace)
        assert resolve_workspace_root(repo) == workspace


class TestAnhEm:
    """Kịch bản ② — REPO là sibling của workspace gốc (phiên cloud)."""

    def test_marker_o_thu_muc_anh_em_tra_ve_anh_em(self, tmp_path):
        repo = _mkrepo(tmp_path, "medical-ebm-automation")
        workspace = tmp_path / "EBM-drluanbv175"
        (workspace / "sync").mkdir(parents=True)
        assert resolve_workspace_root(repo) == workspace

    def test_ten_thu_muc_anh_em_khong_quan_trong(self, tmp_path):
        """Tên thư mục workspace gốc KHÔNG được hardcode — đổi tên vẫn tìm ra
        đúng nhờ nội dung (`sync/`), không phải TÊN."""
        repo = _mkrepo(tmp_path, "medical-ebm-automation")
        workspace = tmp_path / "ten-repo-bat-ky-khong-lien-quan"
        (workspace / "sync").mkdir(parents=True)
        assert resolve_workspace_root(repo) == workspace

    def test_bo_qua_anh_em_khong_co_marker(self, tmp_path):
        """Nhiều thư mục anh em, chỉ MỘT có `sync/` — không được nhận nhầm
        một sibling rỗng làm workspace gốc."""
        repo = _mkrepo(tmp_path, "medical-ebm-automation")
        (tmp_path / "some-other-repo").mkdir()
        (tmp_path / "another-empty-dir").mkdir()
        workspace = tmp_path / "EBM-drluanbv175"
        (workspace / "sync").mkdir(parents=True)
        assert resolve_workspace_root(repo) == workspace


class TestKhongTimThay:
    """Kịch bản ③ — không đâu có `sync/` → fallback repo.parent (BH08:
    không suy đoán khi không biết, lỗi đường dẫn rõ ràng còn hơn im lặng)."""

    def test_fallback_ve_repo_parent(self, tmp_path):
        repo = _mkrepo(tmp_path, "medical-ebm-automation")
        (tmp_path / "unrelated-sibling").mkdir()
        assert resolve_workspace_root(repo) == tmp_path

    def test_repo_khong_co_thu_muc_cha_ton_tai(self, tmp_path):
        """repo.parent không tồn tại (đường dẫn giả lập) → vẫn fallback,
        không crash."""
        gia = tmp_path / "khong-ton-tai" / "medical-ebm-automation"
        assert resolve_workspace_root(gia) == gia.parent


class TestMarkerKhongDungThuMucRepoLamWorkspace:
    """`.claude/agents/` KHÔNG dùng được làm dấu hiệu vì REPO cũng có bản
    mirror riêng — bài học ghi trong docstring module. Test này khoá việc
    resolve_workspace_root() không tự chọn CHÍNH repo làm workspace gốc dù
    repo có `.claude/agents/` (repo không có `sync/` nên vẫn không khớp)."""

    def test_repo_co_claude_agents_nhung_khong_co_sync_khong_tu_nhan(self, tmp_path):
        repo = _mkrepo(tmp_path, "medical-ebm-automation")
        (repo / ".claude" / "agents").mkdir(parents=True)
        workspace = tmp_path / "EBM-drluanbv175"
        (workspace / "sync").mkdir(parents=True)
        (workspace / ".claude" / "agents").mkdir(parents=True)
        assert resolve_workspace_root(repo) == workspace
