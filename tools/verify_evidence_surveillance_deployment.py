#!/usr/bin/env python3
"""Cổng triển khai fail-closed cho giám sát/cập nhật chứng cứ ngoại trú.

PASS kỹ thuật không tự mở production. Trạng thái READY chỉ xuất hiện sau canary online,
runtime tuần/tháng, alert, rollback, shadow run và phê duyệt bác sĩ + vận hành có bằng chứng.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _workspace_root import resolve_workspace_root  # noqa: E402

ROOT = resolve_workspace_root(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
DEPLOYMENT_DIR = REPO / "deployment" / "evidence_surveillance"
CONTRACT_PATH = DEPLOYMENT_DIR / "DEPLOYMENT_CONTRACT.json"
UAT_PATH = DEPLOYMENT_DIR / "UAT_EVIDENCE.json"
DEFAULT_JSON = REPO / "reports" / "EVIDENCE_SURVEILLANCE_DEPLOYMENT_REPORT.json"
DEFAULT_MD = REPO / "reports" / "EVIDENCE_SURVEILLANCE_DEPLOYMENT_REPORT.md"

PASS = "PASS"
FAIL = "FAIL"
HUMAN_GATE = "HUMAN_GATE"
SKIP = "SKIP"
DISCLAIMER = (
    "Cần bác sĩ kiểm chứng. Cổng này chỉ cho phép triển khai chế độ ứng viên; "
    "không tự áp dụng lâm sàng và không dùng dữ liệu bệnh nhân thật."
)


@dataclass(frozen=True)
class Check:
    check_id: str
    title: str
    phase: str
    status: str
    evidence: str
    limitation: str


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Không đọc được {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} phải là JSON object")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text_or_error(path: Path) -> tuple[str, str | None]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore"), None
    except OSError as exc:
        return "", f"{path.name}:unreadable:{exc}"


def _sanitize_local_paths(value: str) -> str:
    """Không ghi tên tài khoản hoặc đường dẫn máy cá nhân vào bằng chứng chia sẻ."""
    return value.replace(str(ROOT), "<WORKSPACE>").replace(str(Path.home()), "<HOME>")


def _run(command: Sequence[str], *, cwd: Path) -> tuple[bool, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONPYCACHEPREFIX", str(Path(tempfile.gettempdir()) / "ebm_pycache"))
    proc = subprocess.run(
        list(command), cwd=str(cwd), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    lines = [line.strip() for line in (proc.stdout or proc.stderr or "").splitlines() if line.strip()]
    return proc.returncode == 0, _sanitize_local_paths(" / ".join(lines[-3:])[:800])


def _check_contract() -> Check:
    try:
        contract = _load_json(CONTRACT_PATH)
    except ValueError as exc:
        return Check("ESD01", "Hợp đồng triển khai", "static", FAIL, str(exc), "Không có contract thì fail-closed.")
    missing = [
        key for key in (
            "schema_version", "deployment_mode", "minimum_live_sources",
            "runtime_freshness_days", "minimum_human_validation", "hard_stops", "prohibited",
        ) if key not in contract
    ]
    prohibited = contract.get("prohibited") or {}
    safe = (
        not missing
        and contract.get("deployment_mode") == "candidate_only_doctor_review_required"
        and prohibited.get("clinical_auto_apply") is True
        and prohibited.get("real_patient_data") is True
        and "DOCTOR_UAT_NOT_APPROVED" in contract.get("hard_stops", [])
    )
    return Check(
        "ESD01", "Hợp đồng triển khai", "static", PASS if safe else FAIL,
        f"schema={contract.get('schema_version')}; missing={missing}; mode={contract.get('deployment_mode')}",
        "Contract chứng minh ranh giới và điều kiện release, không chứng minh runtime đã chạy thật.",
    )


def _check_tool_mirrors() -> Check:
    paths = [
        ROOT / "sync" / "skills" / "cap-nhat-chung-cu-y-khoa" / "tools" / "surveillance_scan.py",
        ROOT / "sync" / "skills" / "dark-analyst" / "tools" / "surveillance_scan.py",
        ROOT / "EBM-Dashboards" / "tools" / "surveillance_scan.py",
    ]
    missing = [str(path) for path in paths if not path.exists()]
    unreadable: list[str] = []
    hashes: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        try:
            hashes.add(_sha256(path))
        except OSError as exc:
            unreadable.append(f"{path}: {exc}")
    ok = not missing and not unreadable and len(hashes) == 1
    return Check(
        "ESD02", "Đồng bộ scanner skill/runtime", "static", PASS if ok else FAIL,
        (
            f"files={len(paths) - len(missing)}/3; hashes={len(hashes)}; "
            f"missing={missing}; unreadable={unreadable}"
        ),
        "Hash đồng nhất không thay xác minh nguồn online.",
    )


def _check_runtime_code() -> Check:
    requirements = {
        REPO / "run.py": ["deployment_status", "return 2", "strict_source_health=True"],
        REPO / "app" / "services" / "ingestion.py": [
            "summarize_source_health", "MOCK_DETECTED_IN_LIVE", "SAFETY_REDUNDANCY_LOW",
        ],
        REPO / "scripts" / "weekly_safety.sh": [
            "--canary", "bridge_to_ebm_master BỊ CHẶN", "record_evidence_surveillance_run.py",
        ],
        REPO / "scripts" / "monthly_update.sh": [
            "--canary", "bridge_to_ebm_master BỊ CHẶN", "record_evidence_surveillance_run.py",
        ],
    }
    missing: list[str] = []
    for path, markers in requirements.items():
        if not path.exists():
            missing.append(f"{path.name}:missing_file")
            continue
        text, error = _read_text_or_error(path)
        if error:
            missing.append(error)
            continue
        missing.extend(f"{path.name}:{marker}" for marker in markers if marker not in text)
    return Check(
        "ESD03", "Runtime fail-closed", "static", PASS if not missing else FAIL,
        "đủ marker" if not missing else "thiếu " + ", ".join(missing),
        "Kiểm marker được bổ sung bằng test hành vi; không tự coi marker là UAT.",
    )


def _check_offline_pipeline() -> Check:
    verifier = ROOT / "tools" / "verify_clinical_evidence_update_pipeline.py"
    ok, detail = _run([sys.executable, str(verifier), "--no-write"], cwd=ROOT)
    return Check(
        "ESD04", "Pipeline Evidence Workbench offline", "static", PASS if ok else FAIL,
        detail,
        "Fixture offline không chứng minh PMID/DOI phân giải được tại thời điểm triển khai.",
    )


def _schedule_specs() -> dict[str, tuple[Path, Path]]:
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    return {
        "com.medicalebm.weeklysafety": (
            launch_agents / "com.medicalebm.weeklysafety.plist",
            REPO / "scripts" / "weekly_safety.sh",
        ),
        "com.medicalebm.monthlyupdate": (
            launch_agents / "com.medicalebm.monthlyupdate.plist",
            REPO / "scripts" / "monthly_update.sh",
        ),
    }


def _check_scheduler_loaded() -> Check:
    if sys.platform != "darwin":
        # HUMAN_GATE chứ KHÔNG phải FAIL: máy không phải macOS thì chưa có scheduler
        # tương đương — đó là việc người phải làm, không phải hợp đồng bị hỏng.
        # Vẫn chặn triển khai thật (human gate ⇒ deployment_allowed=False), nhưng
        # --contract-check chỉ đếm FAIL nên không còn chặn oan. Trước 03/08/2026 mục
        # này trả FAIL, khiến pre-commit CHẶN MỌI COMMIT trên máy Windows chỉ vì máy
        # không phải macOS, dù không có drift nào.
        return Check(
            "ESD05", "Scheduler launchd", "static", HUMAN_GATE,
            f"Không chạy trên macOS (nền tảng: {sys.platform})",
            "Triển khai máy khác cần scheduler tương đương và UAT riêng.",
        )
    # ĐỔI BỘ LỊCH 15/08/2026 (bác sĩ duyệt «A. Lịch nền thật thay launchd»):
    # launchd chết EX_CONFIG vì TCC chặn đọc ~/Library/CloudStorage (đo thật:
    # runs=1 nhưng stdout/stderr 0 byte từ tháng 6 — «đạt-giả»). Bộ lịch CHÍNH
    # nay là tác vụ Claude (chạy trong ngữ cảnh có quyền OneDrive); plist launchd
    # đã đổi đuôi .disabled. Hợp đồng: CÓ tác vụ Claude đăng ký ⇒ đạt yêu cầu
    # lịch nền; launchd nếu CÒN thì vẫn kiểm như cũ; thiếu CẢ HAI ⇒ FAIL.
    claude_tasks = {
        "thu-thap-tuan-an-toan-thuoc": Path.home() / ".claude" / "scheduled-tasks"
        / "thu-thap-tuan-an-toan-thuoc" / "SKILL.md",
        "cap-nhat-thang-ebm": Path.home() / ".claude" / "scheduled-tasks"
        / "cap-nhat-thang-ebm" / "SKILL.md",
    }
    co_claude = [ten for ten, p in claude_tasks.items() if p.exists()]
    failures: list[str] = []
    evidence: list[str] = [f"claude_task:{ten}" for ten in co_claude]
    for label, (plist_path, script_path) in _schedule_specs().items():
        if not plist_path.exists():
            if len(co_claude) == len(claude_tasks):
                evidence.append(f"{label}:legacy_retired")
            else:
                failures.append(f"{label}:missing_plist_va_thieu_claude_task")
            continue
        try:
            with plist_path.open("rb") as handle:
                payload = plistlib.load(handle)
        except (OSError, plistlib.InvalidFileException) as exc:
            failures.append(f"{label}:invalid_plist:{exc}")
            continue
        args = payload.get("ProgramArguments") or []
        if str(script_path) not in args or payload.get("WorkingDirectory") != str(REPO):
            failures.append(f"{label}:path_drift")
        proc = subprocess.run(
            ["launchctl", "print", f"gui/{getattr(os, 'getuid', lambda: 0)()}/{label}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            failures.append(f"{label}:not_loaded")
        else:
            runs_line = next((line.strip() for line in proc.stdout.splitlines() if "runs =" in line), "runs=unknown")
            evidence.append(f"{label}:{runs_line}")
    return Check(
        "ESD05", "Scheduler launchd", "static", PASS if not failures else FAIL,
        "; ".join(evidence + failures),
        "Đăng ký lịch (Claude task/launchd) chưa chứng minh một chu kỳ đã chạy trọn thành công.",
    )


def _check_online_sources() -> Check:
    try:
        from app.evidence.live_adapter_registry import build_live_adapter_registry
    except Exception as exc:  # pragma: no cover - lỗi import hạ tầng
        return Check(
            "ESD06", "Canary nguồn online", "online", FAIL,
            f"import failed: {exc}", "Không có canary thì không release.",
        )
    identifiers = {
        "pubmed": {"pmid": "20332511"},
        "europepmc": {"doi": "10.1136/bmj.c869"},
        "crossref": {"doi": "10.1136/bmj.c869"},
        "openfda": {"drug_name": "warfarin"},
    }
    registry = build_live_adapter_registry(identifiers)
    failed: list[str] = []
    evidence: list[str] = []
    for name, adapter in registry.items():
        result = adapter.lookup(identifiers[name])
        found = bool(result.found) and not bool(result.unavailable)
        evidence.append(f"{name}:found={found},health={adapter.health.health_status}")
        if not found:
            failed.append(name)
    return Check(
        "ESD06", "Canary nguồn online", "online", PASS if not failed else FAIL,
        "; ".join(evidence) + (f"; failed={failed}" if failed else ""),
        "Canary chỉ kiểm định danh cố định; không thay rà toàn bộ nguồn của từng chủ đề.",
    )


def _check_online_scanner() -> Check:
    scanner = ROOT / "EBM-Dashboards" / "tools" / "surveillance_scan.py"
    with tempfile.TemporaryDirectory(prefix="evidence-surveillance-canary-") as tmp:
        base = Path(tmp)
        watchlist = base / "watchlist.json"
        report_path = base / "scan.md"
        json_path = base / "scan.json"
        watchlist.write_text(json.dumps({
            "topics": [
                {"topic": "Canary guideline", "query": "hypertension guideline", "active": True},
                {"topic": "Canary safety", "query": "warfarin drug safety", "active": True},
            ]
        }), encoding="utf-8", newline="\n")
        ok, detail = _run([
            sys.executable, str(scanner), "--watchlist", str(watchlist),
            "--days", "30", "--max", "1", "--report", str(report_path),
            "--json-report", str(json_path),
        ], cwd=ROOT)
        try:
            payload = _load_json(json_path)
            status = payload.get("status")
            topics = int(payload.get("topic_count") or 0)
            ok = ok and status == PASS and topics == 2 and report_path.exists()
            errors = [
                str(item.get("error") or "")[:240]
                for item in payload.get("topics", [])
                if isinstance(item, dict) and item.get("status") != PASS
            ]
            detail = (
                f"status={status}; topics={topics}; failed={payload.get('failed_topics')}; "
                f"candidates={payload.get('candidate_count')}; errors={errors}"
            )
        except (ValueError, TypeError) as exc:
            ok = False
            detail = f"Không đọc được audit JSON scanner canary: {exc}; output={detail}"
    return Check(
        "ESD07", "Scanner PubMed online", "online", PASS if ok else FAIL,
        detail,
        "Hai query canary không thay độ phủ toàn watchlist hoặc thẩm định Track A.",
    )


def _check_online_dashboard() -> Check:
    verifier = ROOT / "tools" / "verify_clinical_evidence_update_pipeline.py"
    proc = subprocess.run(
        [
            sys.executable, str(verifier), "--online-dashboard-gate", "--no-write", "--json",
        ],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    detail = (proc.stderr or "").strip()[:800]
    ok = proc.returncode == 0
    try:
        payload = json.loads(proc.stdout or "{}")
        rows = {row["name"]: row["status"] for row in payload.get("rows", [])}
        online_flag = payload.get("online_dashboard_gate") is True
        gate_pass = rows.get("Dashboard integrity gate") == PASS
        ok = ok and online_flag and gate_pass
        detail = (
            f"overall={payload.get('overall_status')}; online={online_flag}; "
            f"dashboard_gate={rows.get('Dashboard integrity gate')}"
        )
    except (json.JSONDecodeError, TypeError, KeyError) as exc:
        ok = False
        detail = f"Không đọc được JSON canary online: {exc}; stderr={detail}"
    return Check(
        "ESD08", "Dashboard strict source online", "online", PASS if ok else FAIL,
        detail,
        "Fixture online không thay double-review của mẫu nội dung lâm sàng thật.",
    )


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _check_runtime_history(contract: dict) -> Check:
    now = datetime.now(timezone.utc)
    limits = contract.get("runtime_freshness_days") or {}
    failures: list[str] = []
    evidence: list[str] = []
    for cadence in ("weekly", "monthly"):
        path = REPO / "data" / "archive" / f"evidence_surveillance_{cadence}_status.json"
        if not path.exists():
            failures.append(f"{cadence}:missing")
            continue
        try:
            payload = _load_json(path)
        except ValueError as exc:
            failures.append(f"{cadence}:{exc}")
            continue
        finished = _parse_datetime(str(payload.get("finished_at") or ""))
        age_days = (now - finished).total_seconds() / 86400 if finished else float("inf")
        fresh = age_days <= float(limits.get(cadence, 0))
        passed = payload.get("status") == PASS and payload.get("release_to_hub_allowed") is True
        evidence.append(f"{cadence}:status={payload.get('status')},age={age_days:.1f}d")
        if not passed or not fresh:
            failures.append(f"{cadence}:not_pass_or_stale")
    return Check(
        "ESD09", "Lịch sử runtime tuần/tháng", "runtime", PASS if not failures else FAIL,
        "; ".join(evidence + failures),
        "Cần ít nhất các lượt chạy thật còn mới; canary thủ công không thay lịch sử này.",
    )


def _check_notification_config() -> Check:
    from app.config import settings
    email_ready = bool(
        settings.enable_email_alerts and settings.smtp_host and settings.smtp_password
        and settings.smtp_from and settings.alert_email_to
    )
    webhook_ready = bool(settings.alert_webhook_url)
    ready = email_ready or webhook_ready
    return Check(
        "ESD10", "Cấu hình kênh cảnh báo", "runtime", PASS if ready else FAIL,
        f"email_ready={email_ready}; webhook_ready={webhook_ready}",
        "Chỉ kiểm cấu hình có mặt, UAT vẫn phải chứng minh gửi/nhận thật.",
    )


def _check_uat(contract: dict, uat_path: Path) -> Check:
    try:
        uat = _load_json(uat_path)
    except ValueError as exc:
        return Check("ESD11", "UAT và phê duyệt", "human", HUMAN_GATE, str(exc), "Agent không được tự phê duyệt.")
    minimum = contract.get("minimum_human_validation") or {}
    missing: list[str] = []
    samples = uat.get("source_sample_review") or []
    valid_samples = [
        row for row in samples if isinstance(row, dict)
        and row.get("source_opened") is True
        and row.get("title_match") is True
        and row.get("clinical_claim_checked") is True
        and row.get("reviewed_by_role") == "doctor"
        and (row.get("pmid") or row.get("doi") or row.get("url"))
    ]
    if len(valid_samples) < int(minimum.get("source_sample_size", 5)):
        missing.append("SOURCE_SAMPLE_REVIEW")
    if (uat.get("scheduler_trigger") or {}).get("status") != PASS:
        missing.append("SCHEDULER_TRIGGER")
    if (uat.get("alert_delivery") or {}).get("status") != PASS:
        missing.append("ALERT_DELIVERY")
    rollback = uat.get("rollback_restore") or {}
    if rollback.get("status") != PASS or rollback.get("restore_hash_match") is not True:
        missing.append("ROLLBACK_RESTORE")
    shadow = uat.get("shadow_run") or {}
    if (
        shadow.get("status") != PASS
        or int(shadow.get("cycles") or 0) < int(minimum.get("shadow_cycles", 2))
        or int(shadow.get("failed_cycles") or 0) != 0
        or shadow.get("auto_apply_observed") is not False
    ):
        missing.append("SHADOW_RUN")
    doctor = uat.get("doctor_approval") or {}
    operations = uat.get("operations_approval") or {}
    if doctor.get("approved") is not True or doctor.get("approved_by_role") != "doctor":
        missing.append("DOCTOR_APPROVAL")
    if operations.get("approved") is not True or operations.get("approved_by_role") != "operations":
        missing.append("OPERATIONS_APPROVAL")
    if uat.get("clinical_auto_apply") is not False or uat.get("real_patient_data") is not False:
        missing.append("PROHIBITED_MODE_ENABLED")
    return Check(
        "ESD11", "UAT và phê duyệt", "human", PASS if not missing else HUMAN_GATE,
        f"valid_source_samples={len(valid_samples)}; missing={missing}",
        "Đây là cổng người thật; agent chỉ kiểm bằng chứng, không tự ký hoặc tự điền PASS.",
    )


def run_verification(*, online: bool, runtime_canary: bool, contract_check: bool, uat_path: Path) -> dict:
    try:
        contract = _load_json(CONTRACT_PATH) if CONTRACT_PATH.exists() else {}
    except ValueError:
        contract = {}
    checks = [
        _check_contract(),
        _check_tool_mirrors(),
        _check_runtime_code(),
        _check_offline_pipeline(),
        _check_scheduler_loaded(),
    ]
    if contract_check:
        selected = checks
    else:
        if online:
            checks.extend([_check_online_sources(), _check_online_scanner(), _check_online_dashboard()])
        else:
            checks.extend([
                Check(
                    "ESD06", "Canary nguồn online", "online", HUMAN_GATE,
                    "Chưa chạy --online", "Không release khi chưa có canary online.",
                ),
                Check(
                    "ESD07", "Scanner PubMed online", "online", HUMAN_GATE,
                    "Chưa chạy --online", "Không release khi chưa có scanner canary online.",
                ),
                Check(
                    "ESD08", "Dashboard strict source online", "online", HUMAN_GATE,
                    "Chưa chạy --online", "Không release khi chưa có strict source online.",
                ),
            ])
        if runtime_canary:
            selected = checks
        else:
            checks.extend([
                _check_runtime_history(contract),
                _check_notification_config(),
                _check_uat(contract, uat_path),
            ])
            selected = checks

    failures = [row for row in selected if row.status == FAIL]
    human_gates = [row for row in selected if row.status == HUMAN_GATE]
    if failures:
        deployment_status = "BLOCKED_FOR_DEPLOYMENT"
    elif human_gates:
        deployment_status = "HUMAN_VALIDATION_REQUIRED"
    else:
        deployment_status = (
            "RUNTIME_CANARY_PASS" if runtime_canary
            else "CONTRACT_PASS" if contract_check
            else "READY_FOR_CONTROLLED_DEPLOYMENT"
        )
    return {
        "kind": "outpatient_evidence_surveillance_deployment_verification",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "deployment_status": deployment_status,
        "deployment_allowed": deployment_status == "READY_FOR_CONTROLLED_DEPLOYMENT",
        "runtime_canary": runtime_canary,
        "contract_check": contract_check,
        "online": online,
        "failure_count": len(failures),
        "human_gate_count": len(human_gates),
        "checks": [
            {
                **asdict(row),
                "evidence": _sanitize_local_paths(row.evidence),
                "limitation": _sanitize_local_paths(row.limitation),
            }
            for row in selected
        ],
        "clinical_auto_apply": False,
        "real_patient_data_allowed": False,
        "disclaimer": DISCLAIMER,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Evidence Surveillance Deployment Verification",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Deployment status: `{report['deployment_status']}`",
        f"- Deployment allowed: `{report['deployment_allowed']}`",
        f"- Online canary: `{report['online']}`",
        f"- Failures / human gates: `{report['failure_count']}` / `{report['human_gate_count']}`",
        "",
        "| ID | Cổng | Pha | Trạng thái | Bằng chứng | Giới hạn |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["checks"]:
        values = [row[key] for key in ("check_id", "title", "phase", "status", "evidence", "limitation")]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |")
    lines.extend(["", f"> {report['disclaimer']}", ""])
    return "\n".join(lines)


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _print_json(report: dict) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        stdout_buffer = getattr(sys.stdout, "buffer", None)
        if stdout_buffer is None:
            print(json.dumps(report, ensure_ascii=True, indent=2))
        else:
            stdout_buffer.write(text.encode("utf-8", errors="replace") + b"\n")
            stdout_buffer.flush()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--runtime-canary", action="store_true")
    parser.add_argument("--contract-check", action="store_true")
    parser.add_argument("--uat", default=str(UAT_PATH))
    parser.add_argument("--out-json", default=str(DEFAULT_JSON))
    parser.add_argument("--out-md", default=str(DEFAULT_MD))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    if args.runtime_canary and args.contract_check:
        parser.error("--runtime-canary và --contract-check loại trừ nhau")
    online = args.online or args.runtime_canary
    report = run_verification(
        online=online,
        runtime_canary=args.runtime_canary,
        contract_check=args.contract_check,
        uat_path=Path(args.uat),
    )
    if not args.no_write:
        _write_atomic(Path(args.out_json), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        _write_atomic(Path(args.out_md), markdown_report(report))
    _print_json(report)
    if args.contract_check:
        return 0 if report["failure_count"] == 0 else 1
    if args.runtime_canary:
        return 0 if report["deployment_status"] == "RUNTIME_CANARY_PASS" else 1
    return 0 if report["deployment_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
