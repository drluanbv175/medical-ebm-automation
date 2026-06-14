"""Khởi tạo engine/session SQLAlchemy. SQLite mặc định, nâng cấp PostgreSQL dễ dàng.

Quan trọng: hệ thống KHÔNG xóa dữ liệu cũ khi chạy lại; chỉ thêm/cập nhật.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base declarative cho toàn bộ model."""


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = settings.resolved_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, connect_args=connect_args)
        logger.info("Khởi tạo database engine: %s", url)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal


def init_db() -> None:
    """Tạo bảng nếu chưa tồn tại + migration nhẹ. An toàn khi gọi lại nhiều lần."""
    # import để đăng ký model vào metadata
    from app.models import (  # noqa: F401
        changelog,
        clinical_score,
        evidence,
        pipeline_run,
        research,
        source_log,
    )

    Base.metadata.create_all(get_engine())
    _ensure_columns()
    logger.info("Đã đảm bảo schema database tồn tại (create_all + migration nhẹ).")


def _ensure_columns() -> None:
    """Migration nhẹ: thêm cột mới vào bảng cũ mà không mất dữ liệu.

    `create_all` không ALTER bảng đã tồn tại. Hàm này thêm cột còn thiếu (ADD COLUMN
    – an toàn trên SQLite & PostgreSQL) để nâng cấp DB cũ sang schema mới.
    """
    from sqlalchemy import inspect, text

    engine = get_engine()
    insp = inspect(engine)
    # (bảng, cột, kiểu SQL) – chỉ các cột thêm sau này.
    needed = [
        ("evidence_items", "first_seen_run_id", "INTEGER"),
        ("evidence_items", "last_run_id", "INTEGER"),
        ("evidence_items", "is_mock", "BOOLEAN DEFAULT 0"),
        ("clinical_scores", "pmid", "VARCHAR(16)"),
        ("clinical_scores", "doi", "VARCHAR(128)"),
    ]
    with engine.begin() as conn:
        for table, column, sqltype in needed:
            if not insp.has_table(table):
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sqltype}"))
                logger.info("Migration: thêm cột %s.%s", table, column)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager quản lý transaction an toàn."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
