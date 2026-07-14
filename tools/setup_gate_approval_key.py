#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_gate_approval_key.py — Thiết lập khóa ký MỘT LẦN cho tools/approve_gate.py.

★★★ SCRIPT NÀY CHỈ ĐƯỢC BÁC SĨ TỰ TAY CHẠY — TUYỆT ĐỐI KHÔNG NHỜ AGENT (Claude Code/
Codex) CHẠY HỘ. ★★★

Vì sao: nếu agent chạy script này thay bác sĩ, agent sẽ ĐỌC ĐƯỢC khóa vừa tạo trong lúc
chạy (in ra màn hình/log của phiên làm việc) — từ đó agent có thể tự ký phê duyệt sau
này, và toàn bộ ý nghĩa "chữ ký chứng minh có một người ngoài agent đã duyệt" biến mất.
Đây không phải cảnh báo hình thức — đây là ĐIỀU KIỆN CẦN để cơ chế chữ ký ở
tools/approve_gate.py có tác dụng thật (xem gate_contract.py::ledger_approved()).

Cách dùng (mở Terminal, tự tay gõ — hoặc bấm đúp file .command đi kèm):
    python3 tools/setup_gate_approval_key.py

Script:
  - Nếu ~/.ebm-secrets/gate_approval_key ĐÃ CÓ → không đụng vào (từ chối ghi đè, tránh
    làm mất hiệu lực mọi phê duyệt đã ký bằng khóa cũ). Muốn đổi khóa thật sự, tự tay xóa
    file cũ trước rồi chạy lại — nhưng khi đó MỌI phê duyệt cũ sẽ không còn xác minh được
    (đúng ý nghĩa "khóa mất/đổi thì chữ ký cũ vô hiệu", giống mọi hệ chữ ký số khác).
  - Nếu CHƯA có → sinh 32 byte ngẫu nhiên (secrets.token_hex, cùng chuẩn mật mã Python
    dùng cho token phiên đăng nhập), ghi vào file, đặt quyền 600 (chỉ chủ sở hữu đọc/ghi).
  - KHÔNG in khóa ra sau khi ghi (không để lại trong lịch sử terminal/log nếu tránh được).
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

from secure_permissions import lock_owner_exclusive  # noqa: E402

_KEY_PATH = Path.home() / ".ebm-secrets" / "gate_approval_key"


def main() -> int:
    print("=" * 70)
    print(" THIẾT LẬP KHÓA KÝ DUYỆT CỔNG — chỉ chạy MỘT LẦN, TỰ TAY")
    print("=" * 70)

    if _KEY_PATH.exists():
        print(f"\n✋ Đã có khóa tại: {_KEY_PATH}")
        print("   KHÔNG ghi đè (tránh vô hiệu hóa mọi phê duyệt đã ký bằng khóa cũ).")
        print("   Muốn đổi khóa: tự tay xóa file trên rồi chạy lại script này.")
        return 0

    _KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32)
    _KEY_PATH.write_text(key, encoding="utf-8")
    try:
        # 600 (POSIX) / ACL owner-exclusive (Windows, qua icacls) — chỉ chủ sở hữu
        lock_owner_exclusive(_KEY_PATH, writable=True)
    except (OSError, RuntimeError):
        pass  # một số filesystem (vd exFAT) hoặc thiếu icacls — vẫn tiếp tục, không crash

    print(f"\n✅ Đã tạo khóa mới tại: {_KEY_PATH}")
    print("   Từ giờ, mọi lần chạy tools/approve_gate.py trên MÁY NÀY sẽ tự động ký bằng")
    print("   khóa này. Không cần làm gì thêm — không cần nhớ/gõ lại khóa.")
    print("\n   ⚠️  LƯU Ý:")
    print("   - File này nằm NGOÀI OneDrive → KHÔNG tự đồng bộ sang máy khác. Nếu dùng cả")
    print("     Mac lẫn Windows, chạy script này TRÊN TỪNG MÁY (khóa khác nhau là BÌNH")
    print("     THƯỜNG — mỗi máy tự xác minh phê duyệt do chính máy đó ký).")
    print("   - KHÔNG chia sẻ file này, KHÔNG commit vào git, KHÔNG dán vào chat với agent.")
    print("   - Nếu nghi khóa bị lộ (vd agent đã đọc được), xóa file rồi chạy lại script")
    print("     này để đổi khóa mới — các phê duyệt ký bằng khóa cũ sẽ không còn xác minh")
    print("     được (chủ động coi là đáng ngờ, đúng nguyên tắc).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
