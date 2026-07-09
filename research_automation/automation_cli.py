"""
automation_cli — CLI offline cho automation layer (V4.3.2).

Subcommands: run-project · project-qa · daily-integrity · weekly-quality · dashboard.
KHÔNG API/network/eHospital/email/submission. Dùng bởi scripts/*.sh.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import List, Optional


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_run_project(args) -> int:
    from .project_intake import load_yaml
    from .workflow_runner import WorkflowRunner
    with open(args.request, "r", encoding="utf-8") as f:
        data = load_yaml(f.read())
    res = WorkflowRunner().run(data)
    _print({"status": res.status, "project_id": res.project_id, "run_id": res.run_id,
            "reason_code": res.reason_code, "artifacts": len(res.artifacts),
            "review_items": len(res.review_items),
            "quality_overall": (res.quality_report or {}).get("overall")})
    return 0 if res.status in ("CREATED", "DUPLICATE") else 1


def cmd_project_qa(args) -> int:
    from .project_intake import IntakeDecision, load_yaml, run_intake
    from .quality_gate_runner import run_all
    with open(args.request, "r", encoding="utf-8") as f:
        data = load_yaml(f.read())
    intake = run_intake(data)
    if intake.decision != IntakeDecision.CREATED:
        _print({"qa": "BLOCKED_AT_INTAKE", "reason": intake.reason_code})
        return 1
    report = run_all(intake.project)
    _print(report.to_dict())
    return 0


def _git_untracked() -> List[str]:
    try:
        out = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                             text=True, timeout=30)
        return [ln[3:] for ln in out.stdout.splitlines() if ln.startswith("?? ")]
    except Exception:  # noqa: BLE001
        return []


def cmd_daily_integrity(args) -> int:
    from .schedule_runner import daily_integrity_check
    rep = daily_integrity_check(untracked_paths=_git_untracked())
    _print({"job": rep.job, "ok": rep.ok, "findings": rep.findings, "detail": rep.detail})
    return 0 if rep.ok else 1


def cmd_weekly_quality(args) -> int:
    # Phần thuần Python (review/artifact) cần state runtime; ở CLI chỉ kiểm manifest/registry
    # + untracked, và để test suite (do shell wrapper chạy pytest) đánh giá phần còn lại.
    from .schedule_runner import check_manifest_integrity, check_registry, detect_untracked_critical
    parts = [check_manifest_integrity(), check_registry(),
             detect_untracked_critical(_git_untracked())]
    ok = all(p.ok for p in parts)
    _print({"job": "weekly_quality_static", "ok": ok,
            "findings": [f for p in parts for f in p.findings]})
    return 0 if ok else 1


def cmd_dashboard(args) -> int:
    from .automation_dashboard_data import main as dash_main
    return dash_main([args.out, args.utc, args.test_status])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="automation_cli",
                                description="Offline Research Studio automation (V4.3.2)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("run-project")
    s.add_argument("request")
    s.set_defaults(fn=cmd_run_project)
    s = sub.add_parser("project-qa")
    s.add_argument("request")
    s.set_defaults(fn=cmd_project_qa)
    s = sub.add_parser("daily-integrity")
    s.set_defaults(fn=cmd_daily_integrity)
    s = sub.add_parser("weekly-quality")
    s.set_defaults(fn=cmd_weekly_quality)
    s = sub.add_parser("dashboard")
    s.add_argument("--out", default="research_studio_dashboard.html")
    s.add_argument("--utc", default="STATIC-OFFLINE")
    s.add_argument("--test-status", dest="test_status", default="UNKNOWN")
    s.set_defaults(fn=cmd_dashboard)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
