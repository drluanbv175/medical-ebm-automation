#!/usr/bin/env python3
"""Bảo vệ TÍNH TƯƠI (freshness) của chuỗi checkpoint G0-G10.

Sửa LỚP BUG "stale-checkpoint" đã gây nhiễm G7 seed của đề tài KKB (G0 chạy lại
SAU G7 → G7 dùng seed từ G0 CŨ, chứa PMID đề tài khác). Trước đây pipeline không
có cơ chế phát hiện downstream cũ hơn upstream — chỉ R4 tình cờ bắt được.

Nguyên tắc: mỗi cổng ĐỌC checkpoint của các cổng thượng nguồn. Nếu checkpoint
của 1 cổng được sinh TRƯỚC checkpoint thượng nguồn nó phụ thuộc → nó ĐÃ CŨ
(stale) → phải chạy lại. Cũng phát hiện downstream MỒ CÔI (tồn tại trong khi
upstream còn thiếu).

Dùng:
  - import: find_stale_gates(out_dir) / stale_report(out_dir)
  - CLI:   python3 tools/pipeline_freshness.py --study <MÃ> [--json]
"""

from __future__ import annotations

import argparse
import json

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from pathlib import Path
from typing import Dict, List, Optional

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]

# Thứ tự cổng trong chuỗi.
GATE_ORDER = [f"G{i}" for i in range(11)]  # G0..G10

# Cổng -> các cổng THƯỢNG NGUỒN mà nó đọc checkpoint (trực tiếp là đủ; tính bắc
# cầu qua thứ tự xử lý). Khớp thực tế load_cp(...) trong các run_g*_auto.py.
GATE_DEPS: Dict[str, List[str]] = {
    "G0": [],
    "G1": ["G0"],
    "G2": ["G0", "G1", "G3"],   # + G3: G2 (đạo đức/ICF) nhúng cỡ mẫu N từ G3
    "G3": ["G0", "G1"],
    "G4": ["G3"],
    "G5": ["G0", "G1", "G3"],
    "G6": ["G5"],
    "G7": ["G0", "G1", "G2", "G3", "G4", "G5", "G6"],
    "G8": ["G7"],
    "G9": ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"],
    "G10": ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"],
}

# Dung sai thời gian (giây): coi hai checkpoint sinh cách nhau < ngưỡng này là
# "cùng đợt" để tránh báo stale giả do thứ tự ghi file trong CÙNG một lần chạy
# chuỗi (upstream luôn ghi trước downstream vài giây).
SAME_RUN_TOLERANCE_S = 120.0


def checkpoint_path(out_dir: Path, gate: str) -> Path:
    return out_dir / f"{gate}_checkpoint.json"


def checkpoint_mtime(out_dir: Path, gate: str) -> Optional[float]:
    """Thời điểm sinh checkpoint (epoch giây), None nếu thiếu.

    DÙNG mtime FILE làm chính — đây là tín hiệu ĐỘ PHÂN GIẢI ĐẦY ĐỦ và nhất quán
    trong 1 phiên. KHÔNG dùng trường nội dung làm chính vì một nửa số cổng ghi
    'run_date' DẠNG NGÀY (2026-07-03, phân giải về 00:00:00) trong khi nửa kia
    ghi 'generated_at' đầy đủ giờ — trộn hai loại làm cổng ngày-đơn LUÔN bị coi
    'cũ hơn' cổng cùng ngày có giờ (dương tính giả). Nếu mtime không đọc được
    (hiếm) mới rơi về nội dung.
    """
    p = checkpoint_path(out_dir, gate)
    if not p.exists():
        return None
    try:
        return p.stat().st_mtime
    except OSError:
        pass
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        stamp = data.get("generated_at") or data.get("run_date")
        if stamp:
            return _parse_stamp(str(stamp))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _parse_stamp(s: str) -> Optional[float]:
    """Chuyển 'YYYY-MM-DDTHH:MM:SS...' hoặc 'YYYY-MM-DD' -> epoch giây.

    Dùng datetime.fromisoformat; không dùng Date.now(). Trả None nếu không phân
    giải được (để rơi về mtime file).
    """
    from datetime import datetime
    s = s.strip()
    for fmt in (None,):  # thử isoformat trước
        try:
            # cắt phần lẻ giây/timezone lạ nếu có
            core = s.replace("Z", "").split("+")[0].strip()
            dt = datetime.fromisoformat(core)
            return dt.timestamp()
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def find_stale_gates(out_dir: Path) -> List[Dict[str, object]]:
    """Tìm các cổng CŨ (stale) hoặc downstream MỒ CÔI.

    Trả list dict{gate, kind, reason, offending_upstream}. kind ∈
    {'stale', 'orphan_downstream'}.
    """
    out: List[Dict[str, object]] = []
    mtimes = {g: checkpoint_mtime(out_dir, g) for g in GATE_ORDER}

    for gate in GATE_ORDER:
        gm = mtimes[gate]
        if gm is None:
            continue  # cổng chưa chạy — không phải stale, chỉ là chưa có
        deps = GATE_DEPS.get(gate, [])
        present_deps = [(d, mtimes[d]) for d in deps if mtimes[d] is not None]
        missing_deps = [d for d in deps if mtimes[d] is None]

        # Downstream mồ côi: cổng này có checkpoint nhưng thượng nguồn còn thiếu.
        if missing_deps:
            out.append({
                "gate": gate, "kind": "orphan_downstream",
                "reason": f"{gate} có checkpoint nhưng thượng nguồn còn THIẾU: "
                          f"{', '.join(missing_deps)}",
                "offending_upstream": missing_deps,
            })
            continue

        # Stale: cổng này sinh TRƯỚC một thượng nguồn (quá dung sai cùng-đợt).
        newer = [
            d for d, dm in present_deps
            if dm is not None and dm - gm > SAME_RUN_TOLERANCE_S
        ]
        if newer:
            out.append({
                "gate": gate, "kind": "stale",
                "reason": f"{gate} sinh TRƯỚC thượng nguồn {', '.join(newer)} "
                          f"(> {SAME_RUN_TOLERANCE_S:.0f}s) → cần chạy lại để "
                          "đồng bộ dữ liệu mới nhất",
                "offending_upstream": newer,
            })
    return out


def stale_report(out_dir: Path) -> Dict[str, object]:
    """Báo cáo tổng hợp freshness cho 1 study."""
    issues = find_stale_gates(out_dir)
    present = [g for g in GATE_ORDER if checkpoint_mtime(out_dir, g) is not None]
    return {
        "checkpoints_present": present,
        "n_present": len(present),
        "issues": issues,
        "n_issues": len(issues),
        "fresh": len(issues) == 0,
        "stale_gates": [i["gate"] for i in issues if i["kind"] == "stale"],
        "orphan_gates": [i["gate"] for i in issues if i["kind"] == "orphan_downstream"],
    }


def print_report(report: Dict[str, object]) -> None:
    status = "✅ TƯƠI (nhất quán)" if report["fresh"] else "⚠ CÓ CỔNG CŨ/MỒ CÔI"
    print(f"  Freshness chuỗi checkpoint: {status}")
    print(f"    - checkpoint có: {', '.join(report['checkpoints_present']) or '(chưa có)'}")
    for issue in report["issues"]:
        print(f"    ⚠ [{issue['kind']}] {issue['reason']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Kiểm tính tươi chuỗi checkpoint G0-G10.")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--json", action="store_true", help="In JSON thay vì văn bản")
    args = ap.parse_args()

    out_dir = BASE / "exports" / args.study
    if not out_dir.exists():
        print(f"❌ Không thấy thư mục {out_dir}")
        return 2
    report = stale_report(out_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    return 0 if report["fresh"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
