#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""study_readiness.py — "Đề tài này THỰC SỰ đang ở đâu, và còn gì phải làm?"

★ VÌ SAO CÓ CÔNG CỤ NÀY (2026-07-27):
Hệ thống ĐÃ BIẾT một đề tài còn 31 việc chưa làm — chúng nằm ngay trong
`_checklist-noi-bo.md` của chính đề tài đó — nhưng KHÔNG CÓ LỆNH NÀO NÓI RA. Hệ quả thật:
chủ nhiệm đề tài tin rằng "chỉ còn xác nhận cổng G2 nữa là xong", trong khi thực tế còn
hội đồng chuyên gia (I-CVI/S-CVI), phỏng vấn nhận thức 10-15 người bệnh, pilot thực địa
n≈50-100, khóa vFinal, VÀ một quyết định còn treo có thể đổi số mục bộ công cụ 30→32 (phải
in lại phiếu, sửa đề cương xuyên suốt).

Một hệ thống an toàn không chỉ cần CHẶN đúng chỗ — nó còn phải làm cho **khối lượng việc
còn lại HIỆN RÕ**. Chặn im lặng và "trông như sắp xong" là hai mặt của cùng một vấn đề:
người dùng xây một mô hình sai về trạng thái thật.

Công cụ này CỐ Ý bi quan: nó đếm việc CHƯA làm, không khoe việc đã làm. Nó KHÔNG BAO GIỜ
in chữ "sẵn sàng" — chỉ có bác sĩ và Hội đồng mới kết luận được điều đó.

Dùng:
    python3 tools/study_readiness.py --study hai-long-benh-nhan-C1a-BVQY175
    python3 tools/study_readiness.py --all
"""
from __future__ import annotations

import argparse
import json
import re
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
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools"))

import gate_contract as GC  # noqa: E402

# Chuỗi cổng theo doctrine dieu-phoi-nghien-cuu.md. G2/G4/G8/G9 là cổng CỨNG cần chữ ký.
_GATES = [
    ("G0", "Câu hỏi + tổng quan", False),
    ("G1", "Thiết kế", False),
    ("G2", "Đạo đức + đăng ký", True),
    ("G3", "Cỡ mẫu", False),
    ("G4", "Khóa SAP", True),
    ("G5", "Khóa dữ liệu", False),
    ("G6", "Phân tích", False),
    ("G7", "Bản thảo", False),
    ("G8", "Bình duyệt độc lập", True),
    ("G9", "Liêm chính tác giả", True),
    ("G10", "Lắp gói nộp", False),
]

_UNCHECKED = re.compile(r"^\s*[-*]\s*\[ \]\s*(.+?)\s*$", re.M)
_PENDING_DECISION = re.compile(r"QUYẾT ĐỊNH CÒN TREO|CHƯA TỰ Ý XỬ LÝ|CẦN QUYẾT ĐỊNH", re.I)
# Chỗ để trống trong tài liệu: dãy dấu chấm/gạch dưới dài, hoặc placeholder [CẦN…]
_BLANKS = re.compile(r"…{3,}|\.{5,}|_{5,}|\[CẦN")


def _study_dir(study: str) -> Path:
    return BASE / "exports" / study


_G0_QUALITY_LABELS = {
    "PASS_G0_CONFIRMED": "✅ ĐÃ CHỐT (PASS_G0_CONFIRMED — PICO/kết cục chính đã do bác sĩ xác nhận)",
    "BLOCKED": "🔴 BỊ CHẶN (guardrail/liêm chính) — xem G0_QUALITY_REPORT.md",
    "DRAFT_READY_NEEDS_HUMAN_REVIEW": "🟡 DỰ THẢO — PICO/kết cục chính CHƯA được bác sĩ chốt",
}


def _g0_quality_status(cp: Path) -> str | None:
    """quality_gate.status THẬT trong G0_checkpoint.json, None nếu không đọc được
    (file hỏng, hoặc checkpoint CŨ trước 2026-07-28 chưa có khối này)."""
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    quality = data.get("quality_gate") if isinstance(data, dict) else None
    return quality.get("status") if isinstance(quality, dict) else None


def _gate_state(study: str, d: Path) -> list[tuple[str, str, str]]:
    """[(gate, nhãn, trạng thái)] — trạng thái là chuỗi người đọc hiểu ngay."""
    rows = []
    for gate, label, hard in _GATES:
        cp = d / f"{gate}_checkpoint.json"
        artifacts = list(d.glob(f"{gate}_*")) + list(d.glob(f"{gate.lower()}_*"))
        if hard:
            # Cổng cứng: chỉ "ĐÃ KÝ" khi ledger xác nhận thật.
            signed = False
            for art in artifacts:
                if art.is_file() and GC.ledger_approved(gate, study, art, repo_root=BASE):
                    signed = True
                    break
            if signed:
                state = "🔒 ĐÃ KÝ (ledger xác nhận)"
            elif cp.exists() or artifacts:
                state = "📝 có hồ sơ, CHƯA AI KÝ"
            else:
                state = "— chưa chạy"
        elif gate == "G0" and cp.exists():
            # SỬA 2026-07-30 (audit toàn diện G0-G10, G0-02 — HIGH): trước đây
            # G0 chỉ được đánh giá bằng "checkpoint tồn tại hay không" — một
            # checkpoint với quality_gate.status == DRAFT_READY_NEEDS_HUMAN_
            # REVIEW (PICO còn placeholder) và một checkpoint PASS_G0_CONFIRMED
            # hiển thị Y HỆT NHAU: dấu "✅". Đây đúng là công cụ được xây RIÊNG
            # để chống ảo giác "trông như sắp xong" (xem docstring module),
            # nên khoảng trống này đặc biệt đáng chú ý. Đọc quality_gate.status
            # THẬT; checkpoint CŨ (không có khối này) giữ nguyên hành vi cũ.
            quality_status = _g0_quality_status(cp)
            if quality_status is None:
                state = "✅ có checkpoint (chưa có lớp chất lượng — checkpoint cũ)"
            else:
                state = _G0_QUALITY_LABELS.get(quality_status, f"🟡 {quality_status}")
        else:
            state = "✅ có checkpoint" if cp.exists() else (
                "📄 có artifact, chưa có checkpoint" if artifacts else "— chưa chạy")
        rows.append((gate, label, state))
    return rows


def _collect_todo(d: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """(việc chưa tick, cảnh báo quyết định treo) quét mọi tài liệu .md trong thư mục."""
    todo: list[tuple[str, str]] = []
    pending: list[str] = []
    for f in sorted(d.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in _UNCHECKED.finditer(text):
            item = re.sub(r"\s+", " ", m.group(1)).strip()
            todo.append((f.name, item))
        for line in text.splitlines():
            if _PENDING_DECISION.search(line):
                _clean = re.sub(r"\s+", " ", line).strip()[:200]
                pending.append(f"{f.name}: {_clean}")
    return todo, pending


def report(study: str) -> int:
    d = _study_dir(study)
    print("=" * 78)
    print(f" TÌNH TRẠNG THẬT CỦA ĐỀ TÀI — {study}")
    print("=" * 78)
    if not d.exists():
        print(f"\n✗ Không thấy thư mục: {d}")
        return 1

    print("\n📍 CHUỖI CỔNG G0–G10")
    signed_hard = 0
    for gate, label, state in _gate_state(study, d):
        print(f"   {gate:4} {label:24} {state}")
        if state.startswith("🔒"):
            signed_hard += 1
    print(f"\n   → Cổng CỨNG đã có chữ ký thật: {signed_hard}/4 (G2 · G4 · G8 · G9)")
    if signed_hard == 0:
        print("     ⚠️  CHƯA CỔNG CỨNG NÀO ĐƯỢC KÝ. Mọi hồ sơ hiện có là DỰ THẢO.")

    todo, pending = _collect_todo(d)
    print(f"\n📋 VIỆC CHƯA LÀM (đếm từ chính tài liệu của đề tài): {len(todo)}")
    if todo:
        by_file: dict[str, int] = {}
        for fname, _ in todo:
            by_file[fname] = by_file.get(fname, 0) + 1
        for fname, n in sorted(by_file.items(), key=lambda x: -x[1]):
            print(f"   · {fname}: {n} việc")
        print("\n   10 việc đầu:")
        for _fname, item in todo[:10]:
            print(f"     [ ] {item[:110]}")
        if len(todo) > 10:
            print(f"     … và {len(todo) - 10} việc nữa (xem đầy đủ trong các file trên)")

    if pending:
        print(f"\n🔴 QUYẾT ĐỊNH CÒN TREO ({len(pending)}) — có thể làm THAY ĐỔI đề cương:")
        for p in pending[:5]:
            print(f"   · {p}")

    # Chỗ để trống trong tài liệu trình Hội đồng (tên PI, mã IRB, mã đăng ký…)
    blanks = []
    for f in sorted(d.glob("*.md")):
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if _BLANKS.search(line):
                    blanks.append(f"{f.name}:{i}  {line.strip()[:95]}")
        except (OSError, UnicodeDecodeError):
            continue
    if blanks:
        print(f"\n✏️  CHỖ CÒN ĐỂ TRỐNG trong tài liệu ({len(blanks)}) — 6 dòng đầu:")
        for b in blanks[:6]:
            print(f"   · {b}")

    print("\n" + "-" * 78)
    total = len(todo) + len(pending)
    if signed_hard == 4 and total == 0:
        print("Mọi cổng cứng đã ký và không còn việc nào trong danh sách nội bộ.")
        print("Việc kết luận đề tài 'đủ điều kiện' vẫn thuộc về BÁC SĨ và HỘI ĐỒNG, không phải công cụ này.")
    else:
        print(f"KẾT LUẬN: CÒN {total} việc chưa xong và {4 - signed_hard}/4 cổng cứng chưa ký.")
        print("Đây KHÔNG phải trạng thái sẵn sàng triển khai. Công cụ này cố ý chỉ đếm việc")
        print("CHƯA làm — nó không bao giờ tự tuyên bố 'sẵn sàng'; điều đó thuộc thẩm quyền")
        print("của bác sĩ và Hội đồng Đạo đức.")
    print("Cần bác sĩ kiểm chứng.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument("--all", action="store_true", help="Báo cáo mọi thư mục trong exports/")
    args = ap.parse_args()
    if args.all:
        root = BASE / "exports"
        studies = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.exists() else []
        for s in studies:
            report(s)
            print()
        return 0
    if not args.study:
        ap.error("cần --study <tên> hoặc --all")
    return report(args.study)


if __name__ == "__main__":
    sys.exit(main())
