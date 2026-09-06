r"""Hồi quy phát hiện #1 (CRITICAL) của audit vòng 34 (2026-09-06) trong
scripts/phase_2a_governance_migration.py — ``--apply-dev`` trước đây không
có bất kỳ guard nào ép chỉ định DB đích, nên mặc định ghi thẳng vào DB SẢN
XUẤT thật của app.

BỐI CẢNH SỰ CỐ THẬT (không phải giả định): trong lúc audit vòng 34, agent
Explore đã tái hiện đúng lỗi này và VÔ TÌNH GHI THẬT 13 bảng governance rỗng
vào ``data/medical_ebm.db`` — file DB mà ``app/`` dùng thật. Phiên chính đã
khôi phục file từ bản sao lưu của agent trước khi viết bản vá này.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    if args.apply_dev:
        plan = create_governance_schema()   # KHÔNG truyền engine
        ...

``create_governance_schema(engine=None)`` (app/governance/migrations.py)
khi không truyền engine sẽ dùng ``get_engine()`` = ``settings.
resolved_database_url()`` — mặc định là ``sqlite:///data/medical_ebm.db``,
CHÍNH LÀ DB sản xuất thật, resolve theo BASE_DIR của repo (không phụ thuộc
CWD). Docstring module cảnh báo bằng lời ("Chỉ dùng --apply-dev trên
SQLite/test database đã sao lưu") nhưng KHÔNG có gì trong code ép buộc điều
đó — chạy đúng câu lệnh CLI cơ bản mà quên chỉ định DB đích sẽ ghi thẳng vào
DB sản xuất, không cảnh báo, không cần xác nhận.

BẢN VÁ: ``--database-url`` nay BẮT BUỘC khi dùng ``--apply-dev`` (không có
giá trị mặc định) — thiếu thì ``argparse`` báo lỗi và thoát mã 2 TRƯỚC khi
chạm tới bất kỳ engine/DB nào; có thì tạo engine THẲNG từ URL đó, không bao
giờ rơi về ``get_engine()`` mặc định.

Nguyên tắc viết test: gọi script THẬT qua subprocess (CLI thật, không mock
argparse) — xác nhận (a) thiếu --database-url thì KHÔNG được chạm tới DB sản
xuất thật (kiểm bằng cách chạy trong CWD tạm và xác nhận DB sản xuất thật
của repo không đổi md5), và (b) có --database-url trỏ file tạm thì migration
áp dụng ĐÚNG vào file đó, không phải DB sản xuất."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
PROD_DB = REPO_ROOT / "data" / "medical_ebm.db"


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


class TestApplyDevBatBuocChiDinhDatabaseUrl:
    """★★★ Ca chính — --apply-dev không kèm --database-url phải bị CHẶN ở
    argparse, KHÔNG được chạm tới DB sản xuất thật của repo."""

    def test_thieu_database_url_bi_chan_va_khong_dung_toi_db_that(self, tmp_path):
        prod_md5_before = _md5(PROD_DB) if PROD_DB.exists() else None

        r = subprocess.run(
            [PYTHON, str(REPO_ROOT / "scripts" / "phase_2a_governance_migration.py"), "--apply-dev"],
            cwd=tmp_path, capture_output=True, text=True, timeout=30,
        )

        assert r.returncode == 2, (
            "TRƯỚC bản vá: --apply-dev không cần --database-url, chạy thẳng "
            f"và trả về 0. Thực tế: exit={r.returncode}, stdout={r.stdout!r}"
        )
        assert "--database-url" in r.stderr

        if prod_md5_before is not None:
            assert _md5(PROD_DB) == prod_md5_before, (
                "DB sản xuất thật của repo (data/medical_ebm.db) bị đổi sau "
                "khi chạy --apply-dev thiếu --database-url — đúng sự cố đã "
                "xảy ra thật trong lúc audit vòng 34."
            )

    def test_co_database_url_ap_dung_dung_vao_file_chi_dinh(self, tmp_path):
        prod_md5_before = _md5(PROD_DB) if PROD_DB.exists() else None
        target_db = tmp_path / "vong34_test.db"

        r = subprocess.run(
            [PYTHON, str(REPO_ROOT / "scripts" / "phase_2a_governance_migration.py"),
             "--apply-dev", "--database-url", f"sqlite:///{target_db}"],
            cwd=tmp_path, capture_output=True, text=True, timeout=30,
        )

        assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"
        assert "APPLIED_DEV" in r.stdout
        assert target_db.exists(), "Migration phải áp dụng vào ĐÚNG file --database-url chỉ định"

        if prod_md5_before is not None:
            assert _md5(PROD_DB) == prod_md5_before, (
                "DB sản xuất thật không được đụng tới khi đã chỉ định --database-url khác."
            )


class TestDoiChungDryRunKhongCanDatabaseUrl:
    """Đối chứng — chế độ dry-run (không --apply-dev) chỉ ĐỌC (inspect schema,
    không create_all/ghi), nên không cần --database-url và hành vi giữ
    nguyên như trước bản vá."""

    def test_dry_run_khong_can_database_url(self, tmp_path):
        r = subprocess.run(
            [PYTHON, str(REPO_ROOT / "scripts" / "phase_2a_governance_migration.py")],
            cwd=tmp_path, capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0, f"stdout={r.stdout!r} stderr={r.stderr!r}"
        assert "DRY_RUN" in r.stdout
