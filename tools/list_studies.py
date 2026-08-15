#!/usr/bin/env python3
"""
list_studies.py — Liệt kê + theo dõi TẤT CẢ đề tài trong exports/

THÊM 2026-07-17 (theo yêu cầu bác sĩ: "mỗi đề tài phải có một thư mục riêng để
lưu trữ và theo dõi tại đó"). Mỗi đề tài ĐÃ luôn có thư mục riêng exports/<study>/
(mọi tool run_g*_auto.py dùng --study nhất quán để ghi vào đó) — nhưng trước đây
KHÔNG có cách nào xem TOÀN CẢNH: đề tài nào đang ở đâu, thư mục nào rỗng/mồ côi
(phát hiện thật: KKB-HAI-LONG-2026 rỗng song song với hai-long-benh-nhan-C1a-
BVQY175 thật — cùng 1 đề tài bị tách 2 thư mục do gõ mã khác nhau).

Quét exports/*/, với MỖI thư mục:
  - Đọc topic từ study_meta.json (ưu tiên) hoặc G0_checkpoint.json (dự phòng).
  - Xác định cổng XA NHẤT đã chạy (quét G0_checkpoint.json .. G10_checkpoint.json).
  - Đọc 5 cờ mốc đời thực từ study_meta.json (irb_approved, sap_lock_date,
    data_lock_date, results_final, integrity_signed) — KHÔNG suy diễn, chỉ đọc
    đúng giá trị đã ghi (mặc định rỗng/False nếu thiếu).
  - Thư mục KHÔNG có study_meta.json LẪN G0_checkpoint.json → đánh dấu "KHÔNG RÕ
    ĐỀ TÀI" thay vì bỏ qua âm thầm (để bác sĩ chủ động dọn hoặc bỏ qua).

Cách dùng:
    python tools/list_studies.py            # bảng tóm tắt cho người đọc
    python tools/list_studies.py --json      # JSON máy đọc được
    python tools/list_studies.py --study X   # chi tiết 1 đề tài
"""
from __future__ import annotations

import argparse
import json
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE / "exports"

_MILESTONE_FIELDS = [
    ("irb_approved", "IRB"),
    ("sap_lock_date", "SAP khóa"),
    ("data_lock_date", "DB khóa"),
    ("results_final", "Kết quả"),
    ("integrity_signed", "G9 ký"),
]


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _furthest_gate(d: Path) -> str:
    """Cổng XA NHẤT có checkpoint — quét G10 xuống G0, trả về mã cổng đầu tiên
    tìm thấy (không giả định tuyến tính — chỉ báo cổng nào có file, không suy
    diễn các cổng ở giữa có chạy hay không)."""
    for n in range(10, -1, -1):
        if (d / f"G{n}_checkpoint.json").exists():
            return f"G{n}"
    return "—"


def _last_modified(d: Path) -> str:
    files = [f for f in d.rglob("*") if f.is_file()]
    if not files:
        return "—"
    newest = max(files, key=lambda f: f.stat().st_mtime)
    import datetime
    return datetime.datetime.fromtimestamp(newest.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def scan_study(d: Path) -> dict:
    meta = _load_json(d / "study_meta.json")
    topic = str(meta.get("topic") or meta.get("title") or "").strip()
    has_g0 = (d / "G0_checkpoint.json").exists()
    if not topic and has_g0:
        g0 = _load_json(d / "G0_checkpoint.json")
        topic = str(g0.get("topic") or "").strip()

    n_files = sum(1 for f in d.rglob("*") if f.is_file())

    milestones = {}
    for field, _label in _MILESTONE_FIELDS:
        val = meta.get(field)
        milestones[field] = bool(val) if isinstance(val, bool) else (val if val else None)

    return {
        "study": d.name,
        "topic": topic or None,
        "furthest_gate": _furthest_gate(d),
        "n_files": n_files,
        "recognized": bool(topic) or has_g0,
        "milestones": milestones,
        "last_modified": _last_modified(d),
    }


def scan_all() -> list[dict]:
    if not EXPORTS_DIR.exists():
        return []
    rows = []
    for d in sorted(EXPORTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        rows.append(scan_study(d))
    return rows


def _fmt_milestone(row: dict) -> str:
    m = row["milestones"]
    marks = []
    for field, label in _MILESTONE_FIELDS:
        v = m.get(field)
        if v is True:
            marks.append(f"✅{label}")
        elif v not in (None, False):
            marks.append(f"✅{label}({v})")
    return " ".join(marks) if marks else "—"


def print_table(rows: list[dict]) -> None:
    GC.ensure_utf8_stdout()
    real = [r for r in rows if r["recognized"]]
    unknown = [r for r in rows if not r["recognized"] and r["n_files"] > 0]
    empty = [r for r in rows if not r["recognized"] and r["n_files"] == 0]

    print(f"\n{'='*100}")
    print(f"  DANH SÁCH ĐỀ TÀI — exports/  (tổng {len(rows)} thư mục)")
    print(f"{'='*100}\n")

    if real:
        print(f"📋 ĐỀ TÀI (nhận diện được qua study_meta.json / G0_checkpoint.json) — {len(real)}\n")
        for r in real:
            topic_short = (r["topic"] or "[CHƯA CÓ TOPIC]")[:70]
            print(f"  • {r['study']}")
            print(f"      Topic         : {topic_short}")
            print(f"      Cổng xa nhất  : {r['furthest_gate']}  |  Sửa lần cuối: {r['last_modified']}")
            ms = _fmt_milestone(r)
            if ms != "—":
                print(f"      Mốc đời thực  : {ms}")
            print()

    if unknown:
        print(f"⚠️  THƯ MỤC CÓ FILE NHƯNG KHÔNG RÕ ĐỀ TÀI (không phải pipeline G0-G10) — {len(unknown)}\n")
        for r in unknown:
            print(f"  • {r['study']}  ({r['n_files']} file, sửa lần cuối {r['last_modified']})")
        print()

    if empty:
        names = ", ".join(r["study"] for r in empty)
        print(f"🗑️  THƯ MỤC RỖNG (có thể là đề tài bị bỏ dở/gõ nhầm mã — cân nhắc dọn) — {len(empty)}\n")
        print(f"  {names}\n")

    print("Cần bác sĩ kiểm chứng.")


def print_detail(study: str) -> int:
    GC.ensure_utf8_stdout()
    d = EXPORTS_DIR / study
    if not d.exists():
        print(f"❌ Không tìm thấy thư mục exports/{study}/")
        return 1
    row = scan_study(d)
    print(f"\n{'='*70}")
    print(f"  ĐỀ TÀI: {study}")
    print(f"{'='*70}")
    print(f"Topic         : {row['topic'] or '[CHƯA CÓ]'}")
    print(f"Cổng xa nhất  : {row['furthest_gate']}")
    print(f"Sửa lần cuối  : {row['last_modified']}")
    print(f"Số file       : {row['n_files']}")
    print("\nCổng đã chạy:")
    for n in range(11):
        exists = (d / f"G{n}_checkpoint.json").exists()
        print(f"  {'✅' if exists else '  '} G{n}")
    print("\nMốc đời thực (study_meta.json):")
    for field, label in _MILESTONE_FIELDS:
        v = row["milestones"].get(field)
        mark = "✅" if v is True else ("—" if v in (None, False) else f"✅ ({v})")
        print(f"  {mark} {label}")
    print("\nCần bác sĩ kiểm chứng.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Liệt kê + theo dõi tất cả đề tài trong exports/"
    )
    parser.add_argument("--json", action="store_true", help="Xuất JSON máy đọc được")
    parser.add_argument("--study", default=None, help="Xem chi tiết 1 đề tài")
    args = parser.parse_args()

    if args.study:
        return print_detail(args.study)

    rows = scan_all()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print_table(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
