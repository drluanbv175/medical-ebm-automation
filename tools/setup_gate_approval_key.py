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

import argparse
import secrets
import sys
from pathlib import Path

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

from secure_permissions import lock_owner_exclusive  # noqa: E402

_KEY_PATH = Path.home() / ".ebm-secrets" / "gate_approval_key"

# THÊM 2026-07-26 (audit độc lập lớp bảo mật): KHÓA RIÊNG THEO VAI TRÒ.
# Vấn đề gốc: một khóa duy nhất cho cả máy ký được MỌI vai trò, nên chữ ký "IRB" và
# chữ ký "PI" không phân biệt được về mặt mật mã — nguyên tắc "PI không thể tự làm hội
# đồng đạo đức của chính mình" chỉ tồn tại trên giấy. Với khóa riêng, chữ ký của nhóm
# chỉ tạo được bằng đúng khóa của nhóm đó → giao khóa IRB cho hội đồng thật giữ (hoặc
# đơn giản là giữ ở nơi khác, chỉ mở khi có người đó thật sự duyệt) là tách vai trò trở
# thành bằng chứng THẬT. Không bắt buộc — không tạo thì hệ vẫn chạy bằng khóa chung,
# nhưng approve_gate.py sẽ NÓI RÕ mức bảo đảm thấp hơn thay vì im lặng.
_ROLE_GROUPS = ("IRB", "STATISTICIAN", "INDEPENDENT_PEER_REVIEWER", "PI")


def _key_path_for(role: str | None) -> Path:
    return _KEY_PATH if not role else _KEY_PATH.with_name(f"{_KEY_PATH.name}_{role}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Thiết lập khóa ký duyệt cổng (chung hoặc riêng theo vai trò)")
    ap.add_argument("--role", choices=_ROLE_GROUPS, default=None,
                    help="Tạo KHÓA RIÊNG cho một nhóm stakeholder (khuyến nghị mạnh cho IRB và "
                         "INDEPENDENT_PEER_REVIEWER — 2 vai trò bắt buộc phải độc lập với chủ nhiệm "
                         "đề tài). Không truyền = tạo khóa CHUNG của máy.")
    ap.add_argument("--ed25519", action="store_true",
                    help="NÂNG CẤP B (15/08/2026): tạo CẶP KHÓA Ed25519 cho nhóm --role. "
                         "Người duyệt giữ file .key (có thể đem sang máy khác/USB); repo chỉ "
                         "giữ khóa CÔNG — máy xác minh không cầm bí mật nào, chữ ký trở "
                         "thành bằng chứng độc lập THẬT. Bắt buộc kèm --role.")
    args = ap.parse_args()

    if args.ed25519:
        if not args.role:
            print("✗ --ed25519 bắt buộc kèm --role <NHÓM> (ý nghĩa của nó là danh tính riêng).")
            return 2
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                NoEncryption,
                PrivateFormat,
                PublicFormat,
            )
        except ImportError:
            print("✗ Thiếu thư viện `cryptography` — cài venv chuẩn rồi chạy lại.")
            return 2
        priv_path = _KEY_PATH.parent / f"gate_ed25519_{args.role}.key"
        pub_dir = BASE / "config" / "gate_ed25519_pubkeys"
        pub_path = pub_dir / f"{args.role}.pub"
        if priv_path.exists() or pub_path.exists():
            print(f"✋ Đã có khóa Ed25519 cho {args.role} ({priv_path.name} / {pub_path.name}).")
            print("   KHÔNG ghi đè — đổi khóa là vô hiệu chữ ký cũ; tự tay xóa trước nếu chắc chắn.")
            return 0
        priv = Ed25519PrivateKey.generate()
        priv_path.parent.mkdir(parents=True, exist_ok=True)
        pub_dir.mkdir(parents=True, exist_ok=True)
        priv_path.write_bytes(priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8,
                                                 NoEncryption()))
        try:
            lock_owner_exclusive(priv_path, writable=True)
        except (OSError, RuntimeError):
            pass
        pub_path.write_bytes(priv.public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
        print(f"✅ Đã tạo cặp khóa Ed25519 cho {args.role}:")
        print(f"   • Khóa RIÊNG (bí mật): {priv_path} — GIAO CHO NGƯỜI DUYỆT GIỮ;")
        print("     muốn độc lập thật thì chuyển sang máy/USB của họ rồi XÓA khỏi máy này.")
        print(f"   • Khóa CÔNG: {pub_path} — commit vào repo được (an toàn, công khai).")
        print("   Từ giờ approve_gate.py TỰ ƯU TIÊN ký ed1 cho nhóm này khi thấy khóa riêng.")
        return 0

    key_path = _key_path_for(args.role)

    print("=" * 70)
    if args.role:
        print(f" THIẾT LẬP KHÓA KÝ RIÊNG CHO VAI TRÒ {args.role} — TỰ TAY")
    else:
        print(" THIẾT LẬP KHÓA KÝ DUYỆT CỔNG (CHUNG) — chỉ chạy MỘT LẦN, TỰ TAY")
    print("=" * 70)

    if key_path.exists():
        print(f"\n✋ Đã có khóa tại: {key_path}")
        print("   KHÔNG ghi đè (tránh vô hiệu hóa mọi phê duyệt đã ký bằng khóa cũ).")
        print("   Muốn đổi khóa: tự tay xóa file trên rồi chạy lại script này.")
        return 0

    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32)
    key_path.write_text(key, encoding="utf-8")
    try:
        # 600 (POSIX) / ACL owner-exclusive (Windows, qua icacls) — chỉ chủ sở hữu
        lock_owner_exclusive(key_path, writable=True)
    except (OSError, RuntimeError):
        pass  # một số filesystem (vd exFAT) hoặc thiếu icacls — vẫn tiếp tục, không crash

    if args.role:
        print(f"\n✅ Đã tạo KHÓA RIÊNG cho vai trò {args.role} tại: {key_path}")
        print(f"   Từ giờ, phê duyệt với role thuộc nhóm {args.role} sẽ được ký bằng khóa NÀY,")
        print("   và chữ ký ghi rõ phạm vi 'role' — bằng chứng TÁCH VAI TRÒ thật.")
        if args.role in ("IRB", "INDEPENDENT_PEER_REVIEWER"):
            print(f"\n   ⚠️  Để {args.role} thật sự độc lập, khóa này KHÔNG nên nằm cùng nơi/cùng")
            print("      quyền truy cập với người làm chủ nhiệm đề tài. Nếu bác sĩ tự tạo VÀ tự")
            print("      giữ cả khóa này lẫn khóa PI, thì về mặt kỹ thuật vẫn là tự ký — chỉ khác")
            print("      là hành vi đó nay ĐƯỢC GHI NHẬN RÕ, không còn ngầm định là độc lập.")
        return 0

    print(f"\n✅ Đã tạo khóa mới tại: {key_path}")
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
