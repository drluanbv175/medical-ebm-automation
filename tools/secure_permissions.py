#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Khóa quyền truy cập "chỉ chủ sở hữu" cho file/thư mục nhạy cảm (PII, khóa ký).

Vì sao module này tồn tại:
- `os.chmod` / `Path.chmod` trên POSIX (macOS/Linux) áp dụng đúng bit owner/group/
  other — `stat.S_IRWXU` (700) hay `stat.S_IRUSR | stat.S_IWUSR` (600) thật sự chặn
  người khác đọc/ghi.
- Trên Windows, `os.chmod`/`Path.chmod` KHÔNG áp dụng ACL kiểu POSIX — CPython chỉ
  bật/tắt thuộc tính FILE_ATTRIBUTE_READONLY. Windows quyết định "read-only" bằng
  cách xem TOÀN BỘ mode có bit ghi nào không, bất kể là owner/group/other. Vì các
  cờ "chỉ chủ sở hữu nhưng owner vẫn ghi được" (vd `S_IRUSR | S_IWUSR`) CÓ bit ghi,
  Windows hiểu là "không phải read-only" và bỏ qua hoàn toàn — file/thư mục vẫn mở
  đọc/ghi được bởi bất kỳ ai có quyền truy cập thư mục cha. Đã xác nhận bằng thực
  nghiệm độc lập (xem lịch sử phiên vá lỗi 2026-07-14): với mode CÓ bit ghi, Windows
  không chặn ghi; chỉ khi mode read-only-cho-TẤT-CẢ (khôhng owner-exclusive, vd
  `S_IRUSR | S_IRGRP | S_IROTH` — dùng ở import_real_dataset.py/lock_analysis_dataset.py)
  thì Windows mới thật sự set thuộc tính read-only và chặn ghi (nhưng đó là chặn
  ghi cho MỌI người, không phải "chỉ chủ sở hữu đọc/ghi được" như ý định 700/600).

  => Với nhu cầu "CHỈ chủ sở hữu được đọc/ghi, người khác KHÔNG đọc được" (bảng ánh
     xạ tái định danh PII, khóa ký riêng tư), module này dùng `icacls` trên Windows
     để gỡ kế thừa ACL rồi cấp quyền tường minh cho user hiện tại — cách duy nhất
     trên NTFS mô phỏng đúng ngữ nghĩa "owner-exclusive" của POSIX 700/600.

Lưu ý kỹ thuật quan trọng (cũng từ thực nghiệm khi viết module này): cờ container
`(OI)(CI)` (Object Inherit / Container Inherit) CHỈ được dùng cho THƯ MỤC. Áp cờ
này lên một FILE khiến icacls tạo ra một ACE hỏng — kể cả chủ sở hữu cũng bị khóa
đọc/ghi (đã kiểm chứng: `icacls file /grant:r user:(OI)(CI)F` làm chính user đó
nhận PermissionError khi mở file). Vì vậy hàm dưới đây chỉ thêm `(OI)(CI)` khi
`path.is_dir()`, còn file dùng quyền phẳng `F`/`R`.

Dùng module này thay cho gọi `os.chmod`/`Path.chmod` trực tiếp bất cứ khi nào cần
khóa "chỉ chủ sở hữu" một file/thư mục nhạy cảm.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

# Các principal "rộng" (không phải chỉ-chủ-sở-hữu) mà is_owner_exclusive() coi là
# dấu hiệu CHƯA khóa đúng trên Windows.
_WIDE_PRINCIPALS = (
    "Everyone",
    "BUILTIN\\Users",
    "Authenticated Users",
    "NT AUTHORITY\\Authenticated Users",
)


def _windows_principal() -> str:
    """Trả về principal icacls của user hiện tại, dạng DOMAIN\\user nếu có domain."""
    user = os.environ.get("USERNAME", "")
    domain = os.environ.get("USERDOMAIN", "")
    if domain and user:
        return f"{domain}\\{user}"
    return user


def _run_icacls(args: list) -> subprocess.CompletedProcess:
    """Chạy icacls, raise RuntimeError rõ ràng kèm stderr nếu thất bại (không nuốt lỗi)."""
    result = subprocess.run(
        ["icacls", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "icacls thất bại (args={args}, exit={code}):\nstdout: {out}\nstderr: {err}".format(
                args=args, code=result.returncode,
                out=result.stdout.strip(), err=result.stderr.strip(),
            )
        )
    return result


def lock_owner_exclusive(path: Path, *, writable: bool) -> None:
    """Khóa `path` để CHỈ chủ sở hữu (user hiện tại) đọc được (và ghi nếu `writable`).

    POSIX: giữ nguyên hành vi cũ — `os.chmod` với `stat.S_IRWXU` (700) cho thư mục,
    hoặc `stat.S_IRUSR | stat.S_IWUSR` (600, nếu `writable`) / `stat.S_IRUSR` (400)
    cho file.

    Windows: `os.chmod`/`Path.chmod` không đủ (xem docstring module). Dùng `icacls`:
    gỡ kế thừa ACL (`/inheritance:r`) rồi cấp quyền tường minh cho user hiện tại
    (`/grant:r`). Thư mục cần cờ `(OI)(CI)` để file con tạo sau cũng kế thừa quyền;
    file thì KHÔNG được thêm `(OI)(CI)` (làm hỏng ACE, khóa luôn cả chủ sở hữu).
    """
    path = Path(path)
    is_dir = path.is_dir()

    if os.name == "nt":
        _run_icacls([str(path), "/inheritance:r"])
        principal = _windows_principal()
        if is_dir:
            rights = "(OI)(CI)F" if writable else "(OI)(CI)R"
        else:
            rights = "F" if writable else "R"
        _run_icacls([str(path), "/grant:r", f"{principal}:{rights}"])
        return

    if is_dir:
        os.chmod(path, stat.S_IRWXU)
    else:
        mode = (stat.S_IRUSR | stat.S_IWUSR) if writable else stat.S_IRUSR
        os.chmod(path, mode)


def is_owner_exclusive(path: Path) -> bool:
    """True nếu `path` đã bị khóa chỉ-chủ-sở-hữu truy cập được. Dùng để kiểm tra trong test.

    POSIX: đúng logic cũ — mode & 0o077 == 0 (không group/other nào có quyền).
    Windows: chạy `icacls path` và xác nhận output KHÔNG chứa principal rộng nào
    (Everyone/BUILTIN\\Users/Authenticated Users/NT AUTHORITY\\Authenticated Users).
    """
    path = Path(path)
    if os.name == "nt":
        result = subprocess.run(
            ["icacls", str(path)], capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            return False
        return not any(principal in result.stdout for principal in _WIDE_PRINCIPALS)
    return stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
