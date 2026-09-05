"""Cấu hình logging tập trung – ghi ra console và file data/archive/app.log."""
from __future__ import annotations

import logging
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.config import settings

_CONFIGURED = False


def setup_logging(level: Optional[int] = None) -> None:
    """Thiết lập handler MỘT LẦN (idempotent); cập nhật root level MỖI LẦN gọi
    có truyền `level` tường minh.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 22, phát hiện #4) —
    bản gốc nhận `level: int = logging.INFO` và `get_logger()` (được gọi ở
    MỨC MODULE bởi hầu như mọi file trong hệ thống, chạy NGAY khi import,
    TRƯỚC bất kỳ code CLI nào kịp gọi setup_logging(level=...) tường minh)
    luôn gọi `setup_logging()` KHÔNG truyền `level` — khoá `_CONFIGURED`
    thành True với mức INFO ngay từ import đầu tiên. Mọi lời gọi
    `setup_logging(level=...)` tường minh SAU ĐÓ (vd cờ `--verbose`) bị chặn
    ngay ở `if _CONFIGURED: return` và KHÔNG có tác dụng gì — tham số
    `level` trên thực tế là dead parameter trong toàn bộ codebase.

    Nay `level=None` nghĩa là "không có yêu cầu tường minh" — CHỈ dùng làm
    mặc định khi thiết lập handler LẦN ĐẦU (INFO), không bao giờ tự ý ghi
    đè một mức đã được đặt tường minh trước đó. `get_logger()` tiếp tục gọi
    `setup_logging()` không tham số (level=None) nên không còn nguy cơ
    "get_logger() nào chạy sau cũng âm thầm kéo mức về INFO".
    """
    global _CONFIGURED
    root = logging.getLogger()
    if _CONFIGURED:
        if level is not None:
            root.setLevel(level)
        return

    effective_level = logging.INFO if level is None else level

    settings.archive_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.archive_dir / "app.log"

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root.setLevel(effective_level)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
    except OSError:
        fallback_dir = Path(tempfile.gettempdir()) / "medical-ebm-automation"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            fallback_dir / "app.log", maxBytes=2_000_000, backupCount=5,
            encoding="utf-8"
        )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Giảm ồn từ thư viện bên thứ ba
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
