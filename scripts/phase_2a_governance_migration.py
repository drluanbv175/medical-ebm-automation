#!/usr/bin/env python3
"""Dry-run/apply-dev migration governance V7 Phase 2A.

Mặc định chỉ in kế hoạch. Chỉ dùng `--apply-dev` trên SQLite/test database đã sao lưu.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine  # noqa: E402

from app.governance.migrations import build_governance_migration_plan, create_governance_schema  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Governance V7 Phase 2A migration helper")
    parser.add_argument(
        "--apply-dev", action="store_true",
        help="Tạo bảng còn thiếu trên DB chỉ định bởi --database-url",
    )
    parser.add_argument(
        "--database-url", default=None,
        help="URL SQLAlchemy của DB dev/test đã sao lưu — BẮT BUỘC khi dùng --apply-dev.",
    )
    args = parser.parse_args()

    if args.apply_dev:
        # Vá 2026-09-06 (audit vòng 34, phát hiện #1 — CRITICAL): trước đây
        # create_governance_schema() được gọi KHÔNG truyền engine, nên nó
        # rơi về get_engine() = settings.resolved_database_url() — mặc định
        # là DB SẢN XUẤT thật của app (sqlite:///data/medical_ebm.db), resolve
        # tuyệt đối theo BASE_DIR của repo, không phụ thuộc CWD hay bất kỳ
        # biến môi trường nào đã set sẵn. Docstring module CẢNH BÁO bằng lời
        # ("Chỉ dùng --apply-dev trên SQLite/test database đã sao lưu") nhưng
        # KHÔNG có gì trong code ép buộc điều đó — ai chạy đúng câu lệnh
        # `--apply-dev` mà quên chỉ định DB đích sẽ ghi thẳng 13 bảng mới vào
        # DB sản xuất. Đã tái hiện thật trong lúc audit vòng 34 (agent audit
        # vô tình kích hoạt đúng lỗi này). Nay --database-url là BẮT BUỘC,
        # không có mặc định — buộc người gọi ý thức chọn đích, khớp đúng quy
        # ước --db-path/--database-url mà các script phase_2b_* chị em đã
        # dùng (dù mặc định của CHÚNG lại mắc lỗi khác — xem phát hiện #2).
        if not args.database_url:
            parser.error(
                "--apply-dev bắt buộc phải kèm --database-url trỏ tới DB "
                "dev/test đã sao lưu — không có mặc định, để tránh ghi nhầm "
                "vào DB sản xuất mặc định của app."
            )
        connect_args = {"check_same_thread": False} if args.database_url.startswith("sqlite") else {}
        engine = create_engine(args.database_url, future=True, connect_args=connect_args)
        plan = create_governance_schema(engine)
        print(f"APPLIED_DEV migration_id={plan.migration_id} missing_before={len(plan.missing_tables)}")
        return 0

    plan = build_governance_migration_plan()
    print(f"DRY_RUN migration_id={plan.migration_id}")
    print(f"destructive={plan.destructive}")
    print("missing_tables=" + ",".join(plan.missing_tables))
    for statement in plan.sql:
        print(statement)
    return 0


if __name__ == "__main__":
    sys.exit(main())
