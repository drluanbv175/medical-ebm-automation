#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mark_study_synthetic.py — BƯỚC 1/2 của cơ chế "admin phê duyệt toàn quyền CHỈ
cho dữ liệu tổng hợp/thử nghiệm" (2026-07-15, theo yêu cầu bác sĩ).

Bối cảnh: bác sĩ muốn có "quyền cao nhất phê duyệt mọi cổng" để kiểm thử cơ chế
tự động hóa G0-G9, KỂ CẢ G2 (Hội đồng Đạo đức/IRB) và G8 (phản biện độc lập) —
2 cổng mà `tools/approve_gate.py` (CLI thật) CỐ Ý không cho PI tự ký, vì đó là
nguyên tắc liêm chính nghiên cứu cốt lõi (một PI không thể tự làm hội đồng đạo
đức/tự phản biện chính mình). Sau khi hỏi rõ phạm vi, bác sĩ chọn: TOÀN QUYỀN
kể cả G2/G8, nhưng CHỈ áp dụng cho đề tài tổng hợp/thử nghiệm — KHÔNG BAO GIỜ
đề tài người thật (vd exports/hai-long-benh-nhan-C1a-BVQY175).

Cơ chế 2 lớp phòng thủ (không lớp nào một mình là đủ):
  Lớp 1 — script NÀY: đánh dấu TƯỜNG MINH, CÓ CHỦ Ý một đề tài là
          study_meta.json["study_kind"] = "synthetic_test". Từ chối nếu đề tài
          nằm trong gate_contract.REAL_STUDY_DENYLIST, hoặc đã có dấu hiệu tiến
          độ THẬT (irb_approved/sap_lock_date/... đã bật, hoặc ledger đã có phê
          duyệt G2/G8 KHÔNG-synthetic từ trước — gợi ý đây có thể là đề tài
          đang đi qua quy trình thật, không nên gắn cờ synthetic).
  Lớp 2 — tools/approve_gate_synthetic_admin.py: CHỈ ghi phê duyệt khi đã thấy
          study_kind == "synthetic_test" ở lớp 1, VÀ tự kiểm tra lại
          REAL_STUDY_DENYLIST một lần nữa (không tin lớp 1 một mình).

KHÔNG đè study_kind nếu đã = "synthetic_test" (idempotent). Dùng --unmark để
gỡ cờ (hành động AN TOÀN/giảm quyền, không cần cờ xác nhận).

Dùng:
    python3 tools/mark_study_synthetic.py --study TEST-ADMIN-BYPASS-DEMO \\
        --i-confirm-this-is-synthetic-test-data-not-a-real-study

    python3 tools/mark_study_synthetic.py --study TEST-ADMIN-BYPASS-DEMO --unmark
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import unicodedata
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_contract as GC  # noqa: E402

from app.utils.console import configure_unicode_console  # noqa: E402
from runtime.approval_ledger import ApprovalLedger, LedgerLockInvalidated  # noqa: E402

_REAL_PROGRESS_FLAGS = ("irb_approved", "sap_lock_date", "data_lock_date",
                        "results_final", "integrity_signed")


def _has_real_ledger_progress(ledger_path: Path) -> list:
    """Trả danh sách gate_id đã có phê duyệt APPROVED KHÔNG-synthetic trong ledger
    — dấu hiệu mạnh rằng đề tài đang/đã đi qua quy trình duyệt THẬT, không nên
    gắn cờ synthetic_test (dù chỉ để thử nghiệm) vì có thể trộn lẫn 2 loại bằng
    chứng trong cùng 1 ledger."""
    if not ledger_path.exists():
        return []
    try:
        records = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return sorted({
        r.get("gate_id") for r in records
        if r.get("decision") == "APPROVED" and not r.get("is_synthetic")
    })


def main() -> int:
    configure_unicode_console()
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", required=True, help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument("--i-confirm-this-is-synthetic-test-data-not-a-real-study",
                    dest="confirm", action="store_true",
                    help="Bắt buộc — xác nhận tường minh đây KHÔNG PHẢI đề tài người thật")
    ap.add_argument("--unmark", action="store_true",
                    help="Gỡ cờ synthetic_test (hành động an toàn, không cần --i-confirm-...)")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]

    # CHỐT AN TOÀN dùng chung (gate_contract.resolve_synthetic_study_dir): giải
    # exports/<study> thành đường dẫn CANONICAL đã resolve toàn bộ symlink/"."/"..",
    # kiểm containment (con trực tiếp của exports/) + denylist trên tên canonical +
    # chặn chuỗi rỗng — đóng cùng lúc 4 lỗ hổng red-team đối kháng tái hiện được
    # 2026-07-15 (TOCTOU symlink race, thoát sandbox bằng path tuyệt đối/"../",
    # --study rỗng, biến thể "./<tên thật>"). MỌI I/O bên dưới dùng real_dir này,
    # KHÔNG dùng lại Path chưa resolve.
    real_dir, err = GC.resolve_synthetic_study_dir(args.study, repo_root)
    if err:
        print(f"✗ TỪ CHỐI: {err}")
        if "REAL_STUDY_DENYLIST" in err:
            print("   Nếu đây thực sự là đề tài tổng hợp/thử nghiệm, tạo thư mục tên khác biệt rõ")
            print("   ràng (vd tiền tố TEST-/DEMO-/SANDBOX-) thay vì gắn cờ lên tên đề tài thật.")
        return 1
    study_dir = real_dir
    meta_path = study_dir / "study_meta.json"

    # VÁ 2026-07-16 (red-team vòng 2, CONFIRMED bằng script thật): trước bản vá
    # này, đọc→kiểm→ghi study_meta.json KHÔNG khóa — một tiến trình khác ghi
    # irb_approved=True GIỮA LÚC script đang xử lý có thể bị ghi đè mất trắng
    # (và chính _REAL_PROGRESS_FLAGS/_has_real_ledger_progress ở dưới cũng đọc
    # từ snapshot cũ nên không chặn được). Khóa file độc quyền quanh TRỌN chu
    # trình đọc→kiểm→ghi bằng CHÍNH primitive dùng cho approval_ledger.json
    # (ApprovalLedger._exclusive_file_lock — cross-platform, đã có test riêng).
    lock_path = meta_path.with_suffix(meta_path.suffix + ".lock")
    try:
        with ApprovalLedger._exclusive_file_lock(lock_path) as fd:
            return _do_mark(study_dir, meta_path, args, fd, lock_path)
    except (TimeoutError, LedgerLockInvalidated) as exc:
        print(f"✗ TỪ CHỐI (khóa study_meta.json): {exc}")
        print("   Đây là lỗi tạm thời — chạy lại chính xác lệnh này.")
        return 1


def _write_meta_locked(meta_path: Path, meta: dict, fd, lock_path: Path) -> None:
    """Ghi study_meta.json — xác nhận LẠI khóa còn hợp lệ NGAY TRƯỚC khi ghi
    (không chỉ lúc acquire), khớp mẫu vá ApprovalLedger.locked_update()
    (2026-07-16, red-team vòng 2). Nếu bị vô hiệu hóa giữa chừng (file .lock
    bị xóa/thay), TỪ CHỐI ghi thay vì ghi đè âm thầm."""
    if not ApprovalLedger._lock_identity_matches(fd, lock_path):
        raise LedgerLockInvalidated(
            f"Khóa study_meta.json đã bị VÔ HIỆU HÓA giữa chừng (file .lock bị xóa/thay khi "
            f"tool đang chạy) — TỪ CHỐI ghi để tránh mất cập nhật: {meta_path}. Chạy lại lệnh."
        )
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _do_mark(study_dir: Path, meta_path: Path, args, fd, lock_path: Path) -> int:
    meta = GC.load_study_meta(study_dir)

    if args.unmark:
        if meta.get("study_kind") == "synthetic_test":
            meta.pop("study_kind", None)
            _write_meta_locked(meta_path, meta, fd, lock_path)
            print(f"✅ Đã gỡ cờ synthetic_test khỏi '{args.study}'.")
            print("   tools/approve_gate_synthetic_admin.py sẽ KHÔNG còn hoạt động trên đề tài này.")
        else:
            print(f"(Không có gì để gỡ — '{args.study}' chưa từng được đánh dấu synthetic_test.)")
        return 0

    if meta.get("study_kind") == "synthetic_test":
        print(f"(Đã đánh dấu từ trước — '{args.study}' đã là study_kind=synthetic_test, không đổi gì.)")
        return 0

    if not args.confirm:
        print("✗ Thiếu cờ xác nhận bắt buộc.")
        print("   Chạy lại kèm: --i-confirm-this-is-synthetic-test-data-not-a-real-study")
        return 1

    real_flags_on = [k for k in _REAL_PROGRESS_FLAGS if meta.get(k)]
    if real_flags_on:
        print(f"✗ TỪ CHỐI: '{args.study}' đã có dấu hiệu tiến độ THẬT trong study_meta.json: "
              f"{real_flags_on}")
        print("   Một đề tài đã có irb_approved/sap_lock_date/.../integrity_signed=true KHÔNG nên")
        print("   được gắn cờ synthetic_test — nguy cơ trộn lẫn bằng chứng thật và bằng chứng giả")
        print("   lập trong cùng một ledger. Nếu đây thực sự là lỗi thao tác (cờ thật bị bật nhầm")
        print("   trên đề tài thử nghiệm), sửa tay study_meta.json rồi chạy lại.")
        return 1

    ledger_path = study_dir / "approval_ledger.json"
    real_gates = _has_real_ledger_progress(ledger_path)
    if real_gates:
        print(f"✗ TỪ CHỐI: '{args.study}' đã có phê duyệt THẬT (không-synthetic) trong ledger "
              f"cho cổng: {real_gates}")
        print("   Không gắn cờ synthetic_test lên đề tài đã có lịch sử duyệt thật — nguy cơ")
        print("   admin-bypass sau này ghi thêm phê duyệt giả lập vào CÙNG ledger với phê duyệt")
        print("   thật, gây khó phân biệt khi audit.")
        return 1

    # HEURISTIC BẮT BÍ DANH THEO NỘI DUNG (thêm 2026-07-15 sau red-team) — tổng
    # quát hơn denylist theo tên: một đề tài THỬ NGHIỆM đúng nghĩa KHÔNG mang danh
    # tính cơ sở y tế THẬT. Nếu study_meta.json có org_lines (dòng "BỆNH VIỆN…/
    # TRUNG TÂM…") thì rất có thể đây là đề tài thật (hoặc bí danh chạy-thử dùng
    # danh tính viện thật, như KKB-HAI-LONG-2026) → từ chối, kể cả khi TÊN thư mục
    # chưa kịp thêm vào REAL_STUDY_DENYLIST. Bắt được lớp "bí danh mới chưa ai kịp
    # denylist" mà danh sách tên một mình bỏ sót.
    #
    # MỞ RỘNG 2026-07-15 (audit đối kháng vòng 2 phát hiện): org_lines một mình gần
    # như VÔ DỤNG trên thực tế — KHÔNG tool pipeline nào tự ghi field này, và ngay
    # cả đề tài thật đầu tiên trong denylist (hai-long-benh-nhan-C1a-BVQY175) có
    # org_lines=null dù title chứa nguyên văn "Bệnh viện Quân y 175". Nơi tên cơ sở
    # y tế THẬT thực sự xuất hiện trong dữ liệu hiện có là title/topic. Soi thêm 2
    # trường đó bằng regex tên loại hình cơ sở y tế phổ biến — cố ý RỘNG (chấp nhận
    # false positive, dễ sửa bằng cách đổi tên đề tài) hơn là BỎ SÓT một đề tài thật.
    _REAL_INSTITUTION_PATTERN = re.compile(
        r"bệnh\s*viện|trung\s*tâm\s*y\s*tế|trung\s*tâm\s*khám\s*(chữa)?\s*bệnh|"
        r"phòng\s*khám|khoa\s*khám\s*bệnh|trạm\s*y\s*tế|viện\s*quân\s*y|quân\s*y\s*viện|"
        r"bệnh\s*xá",
        re.IGNORECASE,
    )
    # VÁ 2026-07-16 (red-team vòng 2, CONFIRMED end-to-end — tự duyệt được cả
    # G2+G8 bằng title dạng NFD): regex trên so khớp CODEPOINT THÔ, còn Unicode
    # cho phép CÙNG một chữ hiển thị giống hệt nhau ("bệnh viện") được LƯU bằng
    # 2 dạng byte khác nhau — NFC (dấu đi liền ký tự, 1 codepoint/chữ) và NFD
    # (dấu tổ hợp TÁCH RỜI, 2+ codepoint/chữ). macOS (môi trường dev dự án) hay
    # sinh NFD qua một số đường nhập liệu — KHÔNG CẦN Ý ĐỒ XẤU vẫn có thể tạo ra
    # title NFD né được regex trong khi mắt người đọc thấy giống hệt "Bệnh viện
    # Quân y 175". Chuẩn hóa về NFC TRƯỚC khi so khớp — quy tắc chung khi so
    # khớp chuỗi tiếng Việt/có dấu, không riêng gì heuristic này.
    org_lines = meta.get("org_lines")
    has_org_lines = isinstance(org_lines, list) and any(
        unicodedata.normalize("NFC", str(x)).strip() for x in org_lines
    )
    title_hit = None
    for field in ("title", "topic"):
        val = unicodedata.normalize("NFC", str(meta.get(field) or ""))
        if _REAL_INSTITUTION_PATTERN.search(val):
            title_hit = (field, val)
            break
    if has_org_lines or title_hit:
        print(f"✗ TỪ CHỐI: '{args.study}' mang danh tính CƠ SỞ Y TẾ THẬT trong study_meta.json.")
        if has_org_lines:
            print(f"   org_lines={org_lines}")
        if title_hit:
            field, val = title_hit
            print(f"   {field} chứa tên loại hình cơ sở y tế: \"{val}\"")
        print("   Một đề tài thử nghiệm đúng nghĩa không nên gắn tên bệnh viện/trung tâm thật.")
        print("   Đây có thể là đề tài thật hoặc bí danh chạy-thử dùng danh tính viện thật — nếu")
        print("   chắc chắn là dữ liệu tổng hợp, sửa title/topic/org_lines để không còn tên loại")
        print("   hình cơ sở y tế (vd đổi thành tên hư cấu rõ ràng), hoặc tạo thư mục thử nghiệm")
        print("   MỚI không mang danh tính thật, rồi chạy lại.")
        return 1

    meta["study_kind"] = "synthetic_test"
    meta["_study_kind_note"] = (
        "[ĐÁNH DẤU 2026-07-15 qua tools/mark_study_synthetic.py] Đề tài này được xác nhận "
        "TỔNG HỢP/THỬ NGHIỆM — dùng để kiểm thử cơ chế tự động hóa G0-G9, KHÔNG PHẢI nghiên "
        "cứu người thật. Cờ này mở khóa tools/approve_gate_synthetic_admin.py cho đề tài này "
        "(admin có thể tự duyệt MỌI cổng kể cả G2/G8). Gỡ bằng --unmark nếu đặt nhầm."
    )
    _write_meta_locked(meta_path, meta, fd, lock_path)
    print(f"✅ Đã đánh dấu '{args.study}' là study_kind=synthetic_test.")
    print(f"   Ghi vào: {meta_path}")
    print("   ⚠️  tools/approve_gate_synthetic_admin.py giờ có thể duyệt MỌI cổng (kể cả G2/G8)")
    print("      cho đề tài này. KHÔNG BAO GIỜ dùng cờ này cho nghiên cứu người thật.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
