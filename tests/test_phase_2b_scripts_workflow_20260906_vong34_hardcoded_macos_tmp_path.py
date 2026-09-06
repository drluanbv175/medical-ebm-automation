r"""Hồi quy phát hiện #2 (HIGH) của audit vòng 34 (2026-09-06) trong
scripts/phase_2b_migrate_test_db.py + phase_2b_rollback_test_db.py +
phase_2b_seed_governance_test_data.py — cả 3 script khai đường dẫn DB mặc
định hardcode kiểu macOS (``/private/tmp/...``).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    parser.add_argument("--db-path", default="/private/tmp/ebm_phase_2b_governance.db")
    # (hoặc --database-url="sqlite:////private/tmp/ebm_phase_2b_governance.db")

``/private/tmp`` là symlink-target đặc thù macOS (``/tmp`` → ``/private/tmp``).
Trên Linux (môi trường CI/dev/server thật của repo này), thư mục
``/private`` không tồn tại. Khi chạy 3 script này KHÔNG kèm
``--db-path``/``--database-url`` (đúng cách gọi ngắn gọn thông thường),
SQLAlchemy/sqlite3 không mở được file vì thư mục cha không tồn tại →
``OperationalError: unable to open database file`` — script hoàn toàn
KHÔNG chạy được trên Linux dù logic migrate/rollback/seed bên trong đúng.

Bộ test cũ (``tests/test_phase_2b_migration_scripts.py``) luôn truyền
``--db-path`` tường minh (``tmp_path`` của pytest) nên KHÔNG hề phát hiện
được default path hỏng.

BẢN VÁ: đổi default sang
``str(Path(tempfile.gettempdir()) / "ebm_phase_2b_governance.db")`` (hoặc
dạng URL tương ứng cho script seed) — ``tempfile.gettempdir()`` tự resolve
đúng thư mục tạm theo từng hệ điều hành (Linux/macOS/Windows), không hardcode.

Nguyên tắc viết test: gọi CẢ 3 script THẬT qua subprocess KHÔNG truyền
--db-path/--database-url — đúng kịch bản lỗi đã xảy ra — xác nhận cả 3 chạy
thành công (exit 0) trên máy Linux này."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def _run_script_no_args(script: str, *extra_args: str) -> dict:
    completed = subprocess.run(
        [PYTHON, str(REPO_ROOT / script), *extra_args],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    return completed


class TestCa3ScriptChayDuocKhongCanChiDinhDuongDan:
    """★★★ Ca chính — cả 3 script phase_2b_* phải chạy được KHÔNG kèm
    --db-path/--database-url, trên máy Linux này."""

    def test_migrate_khong_can_db_path(self):
        r = _run_script_no_args("scripts/phase_2b_migrate_test_db.py", "--fresh")
        assert r.returncode == 0, (
            "TRƯỚC bản vá: default '/private/tmp/...' không tồn tại trên Linux "
            f"→ OperationalError. stdout={r.stdout!r} stderr={r.stderr!r}"
        )
        result = json.loads(r.stdout)
        assert result["migration_passed"] is True
        assert result["production_database_touched"] is False

    def test_rollback_khong_can_db_path(self):
        # Chạy migrate trước để tạo file DB mặc định (dùng lại đúng path mặc định).
        _run_script_no_args("scripts/phase_2b_migrate_test_db.py", "--fresh")
        r = _run_script_no_args("scripts/phase_2b_rollback_test_db.py")
        assert r.returncode == 0, (
            f"stdout={r.stdout!r} stderr={r.stderr!r}"
        )
        result = json.loads(r.stdout)
        assert result["rollback_passed"] is True
        assert result["reapply_passed"] is True

    def test_seed_khong_can_database_url(self):
        r = _run_script_no_args("scripts/phase_2b_seed_governance_test_data.py")
        assert r.returncode == 0, (
            f"stdout={r.stdout!r} stderr={r.stderr!r}"
        )
        result = json.loads(r.stdout)
        assert result["invalid_transition_blocked"] is True
        assert result["unapproved_release_blocked"] is True


class TestDoiChungTruyenDuongDanTuongMinhVanHoatDongDung:
    """Đối chứng — hành vi cũ (truyền --db-path/--database-url tường minh)
    không bị bản vá ảnh hưởng, vẫn dùng đúng đường dẫn được chỉ định."""

    def test_truyen_db_path_tuong_minh_van_dung_dung_file(self, tmp_path):
        db_path = tmp_path / "explicit_phase_2b.db"
        r = _run_script_no_args(
            "scripts/phase_2b_migrate_test_db.py", "--db-path", str(db_path), "--fresh",
        )
        assert r.returncode == 0
        result = json.loads(r.stdout)
        assert str(db_path) in result["database_url"]
        assert db_path.exists()
