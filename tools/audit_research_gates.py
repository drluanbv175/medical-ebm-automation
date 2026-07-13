#!/usr/bin/env python3
"""Audit tự động hóa từng cổng nghiên cứu G0-G10.

Tool này không chạy mạng/subprocess. Nó đọc checkpoint, study_meta, freshness và
tín hiệu đời-thực để trả lời 4 câu hỏi cho từng cổng:
- Cổng đã có artifact chưa?
- Guardrail có pass không?
- Cổng cứng có bằng chứng thật chưa?
- Lệnh/hành động kế tiếp là gì?

Mục tiêu là làm "control tower" cho run_pipeline.py: chạy được bất kỳ lúc nào
để resume đúng chỗ, không vượt IRB/SAP/data-lock/liêm chính tác giả.

Ví dụ:
  python3 tools/audit_research_gates.py --study KKB-HAI-LONG-2026 --topic "..."
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import pipeline_freshness as FRESH  # noqa: E402
import skill_standards as S  # noqa: E402

REPORT_JSON = "GATE_AUTOMATION_matrix.json"
REPORT_MD = "GATE_AUTOMATION_report.md"
PIPELINE_GATES = [f"G{i}" for i in range(11)]

STATUS_LOCKED = "LOCKED_REAL_SIGNAL"
STATUS_READY = "READY_DRAFT"
STATUS_MISSING = "MISSING"
STATUS_BLOCKED = "BLOCKED_INPUT"
STATUS_GUARDRAIL_FAIL = "GUARDRAIL_FAIL"
STATUS_NEEDS_REAL = "DRAFT_NEEDS_REAL_INPUT"
STATUS_UNKNOWN = "UNKNOWN"

REAL_SIGNAL_BY_PIPELINE_GATE: Dict[str, Tuple[str, str]] = {
    "G2": ("irb_approved", "phê duyệt IRB thật"),
    "G4": ("sap_locked", "SAP đã ký khóa trước khi xem dữ liệu"),
    "G6": ("db_locked", "dataset phân tích đã khóa trước phân tích chính"),
    "G9": ("integrity_signed", "COI/tài trợ/đóng góp tác giả/khai báo AI đã ký"),
}

PIPELINE_GATE_LABELS = {
    "G0": "Câu hỏi, PICO/FINER, evidence seed",
    "G1": "Thiết kế, reporting map, project plan",
    "G2": "Đạo đức, IRB, consent, registration",
    "G3": "Cỡ mẫu, biến số, CRF nền",
    "G4": "SAP và dummy tables",
    "G5": "Quản trị dữ liệu, SOP, CRF/scripts",
    "G6": "Phân tích theo SAP",
    "G7": "Bản thảo/báo cáo",
    "G8": "Bình duyệt nội bộ",
    "G9": "Liêm chính tác giả/công bố",
    "G10": "Lắp ráp đề cương thống nhất",
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _load_meta(out_dir: Path) -> Dict[str, Any]:
    return _load_json(out_dir / "study_meta.json")


def _load_checkpoints(out_dir: Path) -> Dict[str, Dict[str, Any]]:
    cps: Dict[str, Dict[str, Any]] = {}
    for gate in PIPELINE_GATES:
        cp = _load_json(out_dir / f"{gate}_checkpoint.json")
        if cp:
            cps[gate] = cp
    return cps


def _read_guardrail(cp: Optional[Dict[str, Any]]) -> Optional[bool]:
    if not cp:
        return None
    guardrail = cp.get("guardrail")
    if isinstance(guardrail, dict):
        if "passed" in guardrail:
            return bool(guardrail.get("passed"))
        status = guardrail.get("status")
        if isinstance(status, str):
            up = status.upper()
            if "FAIL" in up or "LỖI" in up or "🔴" in status:
                return False
            return "PASS" in up or "✅" in status or "[OK]" in up
    if isinstance(guardrail, str):
        up = guardrail.upper()
        if "FAIL" in up or "LỖI" in up or "🔴" in guardrail:
            return False
        return "PASS" in up or "✅" in guardrail or "[OK]" in up
    return None


def _script_command(gate: str, study: str, topic: Optional[str], meta: Dict[str, Any]) -> str:
    if gate == "G0":
        topic_value = topic or meta.get("title") or "<chủ đề>"
        return f'python3 tools/run_g0_auto.py --study {study} --topic "{topic_value}"'
    if gate == "G10":
        return f"python3 tools/run_g10_assemble.py --study {study}"
    return f"python3 tools/run_{gate.lower()}_auto.py --study {study}"


def _real_action(gate: str, study: str) -> str:
    if gate == "G2":
        return (
            "Bác sĩ nộp/nhận phê duyệt IRB thật rồi cập nhật study_meta.json "
            "`irb_approved=true` + số/ngày phê duyệt; không tự bật."
        )
    if gate == "G4":
        return (
            "Bác sĩ ký SAP Lock Certificate trước khi xem dữ liệu; có thể ghi "
            "`sap_lock_date` vào study_meta.json hoặc dùng tools/approve_gate.py --gate G4."
        )
    if gate == "G6":
        return (
            "Hoàn tất intake/de-identification/pseudonymization -> clean_research_dataset.py "
            "-> lock_analysis_dataset.py; cần DATA_LOCK_manifest status LOCKED_FOR_ANALYSIS."
        )
    if gate == "G9":
        return (
            "Chủ nhiệm và tác giả xác nhận COI/tài trợ/đóng góp/khai báo AI; "
            "sau đó cập nhật `integrity_signed=true` hoặc dùng tools/approve_gate.py --gate G9."
        )
    return f"Chạy tiếp pipeline: python3 tools/run_pipeline.py --study {study}"


def _blocked_action(cp: Dict[str, Any], fallback: str) -> str:
    detail = GC.blocked_detail(cp)
    if detail:
        return detail
    remediation = (cp.get("needs_input") or {}).get("remediation") or {}
    command = remediation.get("command")
    return command or fallback


def _classify_gate(gate: str, study: str, out_dir: Path, topic: Optional[str],
                   meta: Dict[str, Any], cps: Dict[str, Dict[str, Any]],
                   signals: Dict[str, bool],
                   freshness: Dict[str, Any]) -> Dict[str, Any]:
    cp = cps.get(gate)
    guardrail = _read_guardrail(cp)
    checkpoint_path = out_dir / f"{gate}_checkpoint.json"
    stale = gate in set(freshness.get("stale_gates") or [])
    orphan = gate in set(freshness.get("orphan_gates") or [])
    default_command = _script_command(gate, study, topic, meta)

    if not cp:
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_MISSING,
            "guardrail": None,
            "checkpoint": None,
            "real_signal": None,
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": gate not in REAL_SIGNAL_BY_PIPELINE_GATE,
            "next_action": default_command,
        }

    if GC.is_blocked(cp):
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_BLOCKED,
            "guardrail": guardrail,
            "checkpoint": str(checkpoint_path),
            "real_signal": None,
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": False,
            "next_action": _blocked_action(cp, default_command),
        }

    if guardrail is False:
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_GUARDRAIL_FAIL,
            "guardrail": False,
            "checkpoint": str(checkpoint_path),
            "real_signal": None,
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": True,
            "next_action": f"Rà guardrail rồi chạy lại: {default_command}",
        }

    if gate in REAL_SIGNAL_BY_PIPELINE_GATE:
        signal_key, signal_label = REAL_SIGNAL_BY_PIPELINE_GATE[gate]
        locked = bool(signals.get(signal_key))
        return {
            "gate": gate,
            "label": PIPELINE_GATE_LABELS[gate],
            "status": STATUS_LOCKED if locked else STATUS_NEEDS_REAL,
            "guardrail": guardrail,
            "checkpoint": str(checkpoint_path),
            "real_signal": {
                "key": signal_key,
                "label": signal_label,
                "present": locked,
            },
            "stale": stale,
            "orphan": orphan,
            "can_auto_run": False if not locked else True,
            "next_action": "Không cần hành động." if locked else _real_action(gate, study),
        }

    return {
        "gate": gate,
        "label": PIPELINE_GATE_LABELS[gate],
        "status": STATUS_READY if guardrail is True else STATUS_UNKNOWN,
        "guardrail": guardrail,
        "checkpoint": str(checkpoint_path),
        "real_signal": None,
        "stale": stale,
        "orphan": orphan,
        "can_auto_run": True,
        "next_action": (
            f"Checkpoint stale/orphan; chạy lại: {default_command}"
            if stale or orphan else "Không cần hành động."
        ),
    }


def _data_pipeline(meta: Dict[str, Any], study: str) -> List[Dict[str, Any]]:
    deid = meta.get("real_data_deidentification") or {}
    pseudo = meta.get("real_data_pseudonymization") or {}
    intake = meta.get("real_data_intake") or {}
    cleaning = meta.get("real_data_cleaning") or {}
    lock = meta.get("real_data_lock") or {}
    return [
        {
            "step": "deidentify_or_pseudonymize",
            "status": deid.get("status") or pseudo.get("status") or "OPTIONAL_OR_PENDING",
            "artifact": deid.get("deidentified_path") or pseudo.get("pseudonymized_path"),
            "next_action": (
                f"python3 tools/deidentify_research_dataset.py --study {study} --data <file.csv> --then-import "
                "hoặc python3 tools/pseudonymize_research_dataset.py --study "
                f"{study} --data <file.csv> --then-import"
            ),
        },
        {
            "step": "intake",
            "status": intake.get("status") or "MISSING",
            "artifact": intake.get("raw_readonly_path"),
            "next_action": f"python3 tools/import_real_dataset.py --study {study} --data <deidentified.csv>",
        },
        {
            "step": "cleaning",
            "status": cleaning.get("status") or "MISSING",
            "artifact": cleaning.get("clean_dataset_path"),
            "open_query_count": cleaning.get("open_query_count"),
            "next_action": (
                f"python3 tools/clean_research_dataset.py --study {study} "
                "--data <raw_readonly.csv> --dictionary <data_dictionary.json>"
            ),
        },
        {
            "step": "data_lock",
            "status": lock.get("status") or "MISSING",
            "artifact": lock.get("locked_dataset_path"),
            "blockers": lock.get("blockers") or [],
            "next_action": (
                f"python3 tools/lock_analysis_dataset.py --study {study} "
                "--clean-data <df_clean.csv> --query-log <query_log.csv> "
                "--lock-date <YYYY-MM-DD> --approved-by <PI> --sap-version <x.y> "
                "--confirm-deidentified --confirm-clean-copy --confirm-no-open-query "
                "--confirm-sap-locked"
            ),
        },
    ]


def _skill_gate_rows(cps: Dict[str, Dict[str, Any]], meta: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for gate, (name, condition, product) in S.SKILL_GATES.items():
        rows.append({
            "gate": gate,
            "name": name,
            "state": S.skill_gate_state(gate, cps, meta),
            "minimum_condition": condition,
            "required_product": product,
            "pipeline_sources": ", ".join(S.SKILL_TO_PIPELINE_GATE.get(gate, [])) or "real-signal-only",
        })
    return rows


def _first_actionable_gate(rows: List[Dict[str, Any]]) -> Optional[str]:
    priority = {
        STATUS_GUARDRAIL_FAIL: 0,
        STATUS_BLOCKED: 1,
        STATUS_MISSING: 2,
        STATUS_NEEDS_REAL: 3,
        STATUS_UNKNOWN: 4,
    }
    actionable = [
        row for row in rows
        if row["status"] in priority or row.get("stale") or row.get("orphan")
    ]
    if not actionable:
        return None
    actionable.sort(key=lambda item: (priority.get(item["status"], 5), PIPELINE_GATES.index(item["gate"])))
    return actionable[0]["gate"]


def _write_markdown(out_dir: Path, report: Dict[str, Any]) -> Path:
    path = out_dir / REPORT_MD
    lines = [
        f"# Gate Automation Report — {report['study']}",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Current actionable gate: `{report.get('current_actionable_gate') or 'NONE'}`",
        f"- Freshness: {'PASS' if report['freshness']['fresh'] else 'STALE'}",
        "",
        "## Pipeline Gates",
        "",
        "| Gate | Status | Guardrail | Real Signal | Stale | Next Action |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["pipeline_gates"]:
        real = row.get("real_signal")
        if isinstance(real, dict):
            real_text = f"{real['key']}={real['present']}"
        else:
            real_text = ""
        lines.append(
            f"| {row['gate']} | {row['status']} | {row.get('guardrail')} | "
            f"{real_text} | {row.get('stale') or row.get('orphan')} | "
            f"{row['next_action']} |"
        )
    lines.extend([
        "",
        "## Data Pipeline",
        "",
        "| Step | Status | Artifact | Next Action |",
        "|---|---|---|---|",
    ])
    for row in report["data_pipeline"]:
        lines.append(
            f"| {row['step']} | {row['status']} | {row.get('artifact') or ''} | "
            f"{row['next_action']} |"
        )
    lines.extend([
        "",
        "## Skill Gates",
        "",
        "| Gate | Name | State | Required Product | Sources |",
        "|---|---|---|---|---|",
    ])
    for row in report["skill_gates"]:
        lines.append(
            f"| {row['gate']} | {row['name']} | {row['state']} | "
            f"{row['required_product']} | {row['pipeline_sources']} |"
        )
    lines.extend([
        "",
        "> Cần bác sĩ kiểm chứng. Cổng cứng không được tự vượt.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_json(out_dir: Path, report: Dict[str, Any]) -> Path:
    path = out_dir / REPORT_JSON
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _update_meta(out_dir: Path, report: Dict[str, Any],
                 json_path: Path, md_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["research_gate_automation"] = {
        "status": report["overall_status"],
        "current_actionable_gate": report.get("current_actionable_gate"),
        "json": str(json_path.relative_to(out_dir)),
        "markdown": str(md_path.relative_to(out_dir)),
        "generated_at": report["generated_at"],
        "fresh": report["freshness"]["fresh"],
        "hard_stop_count": report["hard_stop_count"],
        "note": "Audit điều hướng; không thay thế phê duyệt IRB/SAP/data lock/liêm chính thật.",
    }
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def audit_gates(study: str, *, out_dir: Optional[Path] = None,
                topic: Optional[str] = None, write: bool = True) -> Dict[str, Any]:
    study_id = study.strip()
    out_dir = Path(out_dir) if out_dir else BASE / "exports" / study_id
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = _load_meta(out_dir)
    cps = _load_checkpoints(out_dir)
    freshness = FRESH.stale_report(out_dir)
    signals = S.real_world_signals(cps, meta)
    pipeline_rows = [
        _classify_gate(gate, study_id, out_dir, topic, meta, cps, signals, freshness)
        for gate in PIPELINE_GATES
    ]
    hard_stop_count = sum(
        1 for row in pipeline_rows
        if row["status"] in {STATUS_BLOCKED, STATUS_GUARDRAIL_FAIL, STATUS_NEEDS_REAL}
    )
    current_gate = _first_actionable_gate(pipeline_rows)
    overall = "PASS_READY_OR_DRAFTS" if hard_stop_count == 0 and freshness["fresh"] else "ACTION_REQUIRED"
    report: Dict[str, Any] = {
        "kind": "research_gate_automation_matrix",
        "study": study_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": overall,
        "current_actionable_gate": current_gate,
        "freshness": freshness,
        "real_world_signals": signals,
        "pipeline_gates": pipeline_rows,
        "data_pipeline": _data_pipeline(meta, study_id),
        "skill_gates": _skill_gate_rows(cps, meta),
        "readiness": S.readiness_report(cps, meta),
        "hard_stop_count": hard_stop_count,
        "rules": [
            "Không tự vượt cổng IRB/SAP/data-lock/liêm chính.",
            "Checkpoint guardrail pass chỉ là draft nếu thiếu tín hiệu đời-thực.",
            "Data pipeline phải qua intake -> cleaning -> data lock trước phân tích chính.",
        ],
    }
    if write:
        json_path = _write_json(out_dir, report)
        md_path = _write_markdown(out_dir, report)
        _update_meta(out_dir, report, json_path, md_path)
    return report


def print_summary(report: Dict[str, Any]) -> None:
    print(f"GATE_AUTOMATION: {report['overall_status']}")
    print(f"study={report['study']}")
    print(f"current_actionable_gate={report.get('current_actionable_gate') or 'NONE'}")
    print(f"hard_stop_count={report['hard_stop_count']}")
    for row in report["pipeline_gates"]:
        if row["gate"] == report.get("current_actionable_gate"):
            print(f"next_action={row['next_action']}")
            break
    print("Cần bác sĩ kiểm chứng.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit tự động hóa cổng nghiên cứu G0-G10.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--topic", default=None, help="Chủ đề, dùng để gợi ý lệnh G0 nếu thiếu")
    parser.add_argument("--no-write", action="store_true", help="Chỉ in/kết quả, không ghi report")
    args = parser.parse_args()

    GC.ensure_utf8_stdout()
    report = audit_gates(args.study, topic=args.topic, write=not args.no_write)
    print_summary(report)
    return 0 if report["overall_status"] == "PASS_READY_OR_DRAFTS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
