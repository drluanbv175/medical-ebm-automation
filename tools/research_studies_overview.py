#!/usr/bin/env python3
"""Tổng quan MỘT MÀN HÌNH cho MỌI đề tài đang chạy pipeline G0-G10.

Vì sao cần: bác sĩ có thể chạy song song nhiều đề tài (vd KKB-HAI-LONG-2026,
SGLT2-HFpEF-2026...). Trước đây muốn biết "đề tài nào đang ở đâu, đề tài nào
đang bị chặn chờ gì" phải tự chạy `pipeline_freshness.py --study <TEN>` hoặc
`run_pipeline.py --study <TEN> --check-only` CHO TỪNG đề tài một. Script này
quét exports/*/ MỘT LẦN và in ra bảng tổng hợp: cổng xa nhất đã tới, có tươi
(freshness) không, có đang BLOCKED chờ input đời-thực không (và lý do 1 dòng),
lần cập nhật gần nhất, và trạng thái cổng CỨNG (G2/G4/G5/G9 — draft vs đã khóa
thật bằng bằng-chứng-đời-thực, KHÔNG suy diễn).

NGUYÊN TẮC (khớp toàn hệ):
  - CHỈ ĐỌC — không ghi/sửa bất kỳ checkpoint/ledger nào của đề tài nào.
  - Nhận diện đề tài bằng sự có mặt của ít nhất 1 G*_checkpoint.json trong
    exports/<tên>/ — đây là quy ước chuẩn của pipeline hiện tại. Đề tài cũ
    chạy tay từ trước khi có checkpoint (vd chỉ có .docx, không có .json) sẽ
    KHÔNG xuất hiện ở đây — không bịa suy luận từ file khác.
  - KHÔNG tự phân loại "đề tài thật" và "dữ liệu test/probe" — hệ không đủ
    thông tin để suy đoán an toàn; in ra TẤT CẢ những gì tìm thấy (minh bạch).
    Muốn loại bớt, dùng --exclude <regex> (mặc định: không loại gì).

Dùng:
  python3 tools/research_studies_overview.py
  python3 tools/research_studies_overview.py --exclude '^(PYTEST|PROBE|AUTO)-'
  python3 tools/research_studies_overview.py --json
  python3 tools/research_studies_overview.py --out-md exports/_STUDIES_OVERVIEW.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

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

import gate_contract as GC  # noqa: E402
import pipeline_freshness as FRESH  # noqa: E402

try:
    import skill_standards as SKILL  # noqa: E402
except Exception:  # noqa: BLE001
    SKILL = None

HARD_GATE_SIGNAL = {
    "G2": ("irb_approved", "phê duyệt IRB thật (số + ngày)"),
    "G4": ("sap_locked", "ký + ngày khóa SAP"),
    "G5": ("db_locked", "dữ liệu thật đã khóa (KHÔNG PII)"),
    "G9": ("integrity_signed", "gói liêm chính đã ký (COI/tài trợ/AI/đóng góp)"),
}


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def find_study_dirs(exports_dir: Path, exclude: Optional[str]) -> List[Path]:
    """Mọi thư mục con exports/<tên>/ có ít nhất 1 G*_checkpoint.json."""
    if not exports_dir.exists():
        return []
    pattern = re.compile(exclude) if exclude else None
    out = []
    for d in sorted(exports_dir.iterdir()):
        if not d.is_dir():
            continue
        if pattern and pattern.search(d.name):
            continue
        if any(d.glob("G*_checkpoint.json")):
            out.append(d)
    return out


def _all_checkpoints(out_dir: Path) -> Dict[str, dict]:
    cps: Dict[str, dict] = {}
    for g in FRESH.GATE_ORDER:
        cp = _load_json(FRESH.checkpoint_path(out_dir, g))
        if cp:
            cps[g] = cp
    return cps


def _hard_gate_states(cps: Dict[str, dict], meta: dict) -> List[Dict[str, object]]:
    if SKILL is None:
        return []
    try:
        signals = SKILL.real_world_signals(cps, meta or {})
    except Exception:  # noqa: BLE001
        return []
    out = []
    for gate, (sig_key, need_label) in HARD_GATE_SIGNAL.items():
        if gate not in cps:
            continue
        locked = bool(signals.get(sig_key))
        out.append({
            "gate": gate, "locked": locked,
            "state": "🔒 khóa thật" if locked else f"🔒 draft — chờ {need_label}",
        })
    return out


def study_summary(out_dir: Path) -> Dict[str, object]:
    cps = _all_checkpoints(out_dir)
    present = [g for g in FRESH.GATE_ORDER if g in cps]
    current_gate = present[-1] if present else None
    fresh = FRESH.stale_report(out_dir)
    meta = _load_json(out_dir / "study_meta.json")

    blocked = False
    blocked_detail = None
    if current_gate:
        cp_cur = cps[current_gate]
        blocked = GC.is_blocked(cp_cur)
        if blocked:
            blocked_detail = GC.blocked_detail(cp_cur)

    mtimes = [FRESH.checkpoint_mtime(out_dir, g) for g in present]
    mtimes = [m for m in mtimes if m is not None]
    last_updated_epoch = max(mtimes) if mtimes else None

    topic = meta.get("title") or (cps.get("G0") or {}).get("topic") or ""

    return {
        "study": out_dir.name,
        "topic": topic,
        "current_gate": current_gate,
        "gates_present": present,
        "n_gates": len(present),
        "fresh": fresh["fresh"],
        "stale_gates": fresh["stale_gates"],
        "orphan_gates": fresh["orphan_gates"],
        "blocked": blocked,
        "blocked_detail": blocked_detail,
        "last_updated_epoch": last_updated_epoch,
        "hard_gates": _hard_gate_states(cps, meta),
    }


def build_overview(exports_dir: Path, exclude: Optional[str]) -> Dict[str, object]:
    dirs = find_study_dirs(exports_dir, exclude)
    studies = [study_summary(d) for d in dirs]
    studies.sort(key=lambda s: (s["last_updated_epoch"] or 0), reverse=True)
    return {
        "n_studies": len(studies),
        "n_blocked": sum(1 for s in studies if s["blocked"]),
        "n_stale": sum(1 for s in studies if not s["fresh"]),
        "studies": studies,
    }


def _fmt_epoch(e: Optional[float]) -> str:
    if e is None:
        return "?"
    import datetime as _dt
    return _dt.datetime.fromtimestamp(e).strftime("%Y-%m-%d %H:%M")


def render_text(overview: Dict[str, object]) -> str:
    lines = []
    lines.append("📚 TỔNG QUAN ĐỀ TÀI NGHIÊN CỨU (G0-G10)")
    lines.append(f"  {overview['n_studies']} đề tài · {overview['n_blocked']} đang chặn chờ input · "
                 f"{overview['n_stale']} có cổng cũ/mồ côi")
    lines.append("")
    for s in overview["studies"]:
        mark = "🚧" if s["blocked"] else ("⚠" if not s["fresh"] else "✅")
        title = f" — {s['topic']}" if s["topic"] else ""
        lines.append(f"  {mark} {s['study']}{title}")
        lines.append(f"      Cổng xa nhất: {s['current_gate']} "
                     f"({s['n_gates']}/11 cổng có checkpoint) · cập nhật: "
                     f"{_fmt_epoch(s['last_updated_epoch'])}")
        if s["blocked"]:
            lines.append(f"      🚧 CHẶN: {s['blocked_detail']}")
        if not s["fresh"]:
            extra = []
            if s["stale_gates"]:
                extra.append(f"cũ: {', '.join(s['stale_gates'])}")
            if s["orphan_gates"]:
                extra.append(f"mồ côi: {', '.join(s['orphan_gates'])}")
            lines.append(f"      ⚠ Freshness: {' · '.join(extra)}")
        if s["hard_gates"]:
            hg = " · ".join(f"{h['gate']}:{h['state']}" for h in s["hard_gates"])
            lines.append(f"      {hg}")
    lines.append("")
    lines.append("  → Cần bác sĩ kiểm chứng. Bảng này CHỈ ĐỌC checkpoint đã có, "
                 "không thay phê duyệt/cổng cứng thật.")
    return "\n".join(lines)


def render_md(overview: Dict[str, object]) -> str:
    lines = ["# Tổng quan đề tài nghiên cứu (G0-G10)", "",
             f"{overview['n_studies']} đề tài · {overview['n_blocked']} đang chặn · "
             f"{overview['n_stale']} có cổng cũ/mồ côi", "",
             "| Đề tài | Chủ đề | Cổng xa nhất | Freshness | Chặn? | Cập nhật |",
             "|---|---|---|---|---|---|"]
    for s in overview["studies"]:
        fresh_txt = "tươi" if s["fresh"] else "cũ/mồ côi"
        block_txt = f"🚧 {s['blocked_detail']}" if s["blocked"] else "—"
        lines.append(f"| {s['study']} | {s['topic']} | {s['current_gate']} "
                     f"({s['n_gates']}/11) | {fresh_txt} | {block_txt} | "
                     f"{_fmt_epoch(s['last_updated_epoch'])} |")
    lines.append("")
    lines.append("Cần bác sĩ kiểm chứng. Bảng CHỈ ĐỌC checkpoint đã có, không thay phê "
                 "duyệt/cổng cứng thật.")
    return "\n".join(lines)


def main() -> int:
    GC.ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Tổng quan mọi đề tài G0-G10.")
    ap.add_argument("--exports-dir", default=str(BASE / "exports"))
    ap.add_argument("--exclude", default=None,
                    help="Regex mã đề tài cần loại khỏi bảng (mặc định: không loại gì)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out-md", default=None, help="Ghi thêm ra file markdown")
    args = ap.parse_args()

    overview = build_overview(Path(args.exports_dir), args.exclude)

    if args.json:
        print(json.dumps(overview, ensure_ascii=False, indent=2))
    else:
        print(render_text(overview))

    if args.out_md:
        Path(args.out_md).write_text(render_md(overview), encoding="utf-8")
        print(f"\n📄 Đã ghi: {args.out_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
