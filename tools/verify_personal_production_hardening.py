#!/usr/bin/env python3
"""Kiểm 7 miền hardening production cho sử dụng cá nhân có kiểm soát.

Tool này không tự tuyên bố hệ thống production-ready. Nó kiểm rằng 7 miền bắt
buộc cho dữ liệu thật/thực hành thật đều có cổng kỹ thuật, tài liệu vận hành và
điểm dừng người thật rõ ràng. Nếu thiếu phê duyệt/UAT/bảo mật thật, kết quả
vẫn PASS ở mức control-plane nhưng trạng thái chung là HUMAN_GATED.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
REPORTS = REPO / "reports"
DEFAULT_JSON = REPORTS / "PERSONAL_PRODUCTION_HARDENING_REPORT.json"
DEFAULT_MD = REPORTS / "PERSONAL_PRODUCTION_HARDENING_REPORT.md"
SOP_DOC = REPO / "docs" / "PERSONAL_PRODUCTION_HARDENING_SOP.md"

PASS = "PASS"
HUMAN_GATE = "HUMAN_GATE"
FAIL = "FAIL"

DISCLAIMER = (
    "Cần bác sĩ kiểm chứng. Đây là cổng hardening kỹ thuật/offline; không thay "
    "IRB, PI, thống kê viên, phản biện độc lập, pháp lý, bảo mật bệnh viện, UAT "
    "hoặc quyết định lâm sàng."
)


@dataclass(frozen=True)
class HardeningCheck:
    domain_id: str
    title: str
    status: str
    evidence: list[str]
    findings: list[str]
    human_action: str


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _missing(paths: Iterable[Path]) -> list[str]:
    return [_rel(path) for path in paths if not path.exists()]


def _contains(path: Path, tokens: Iterable[str]) -> list[str]:
    text = _read(path).lower()
    return [token for token in tokens if token.lower() not in text]


def _count_markdown_bullets(path: Path) -> int:
    return sum(
        1
        for line in _read(path).splitlines()
        if line.strip().startswith(("- ", "* "))
    )


def _check(
    domain_id: str,
    title: str,
    evidence_paths: list[Path],
    required_tokens: dict[Path, list[str]] | None = None,
    findings: list[str] | None = None,
    human_action: str = "",
    human_gated: bool = False,
) -> HardeningCheck:
    errors: list[str] = []
    missing = _missing(evidence_paths)
    if missing:
        errors.extend(f"missing:{item}" for item in missing)
    for path, tokens in (required_tokens or {}).items():
        absent = _contains(path, tokens)
        if absent:
            errors.append(f"{_rel(path)} thiếu token: {', '.join(absent)}")
    status = FAIL if errors else (HUMAN_GATE if human_gated else PASS)
    return HardeningCheck(
        domain_id=domain_id,
        title=title,
        status=status,
        evidence=[_rel(path) for path in evidence_paths],
        findings=[*(findings or []), *errors],
        human_action=human_action,
    )


def check_production_blocker_closure() -> HardeningCheck:
    blocker_doc = REPO / "chronic-care-clinic-os" / "PRODUCTION_BLOCKERS.md"
    phase_doc = REPO / "docs" / "chronic-care" / "PHASE_3A_PRODUCTION_BLOCKERS.md"
    readiness_ts = REPO / "chronic-care-clinic-os" / "lib" / "production-readiness.ts"
    go_live_ts = REPO / "chronic-care-clinic-os" / "lib" / "production-go-live.ts"
    verifier = REPO / "chronic-care-clinic-os" / "scripts" / "verify-production-readiness.ts"
    blocker_count = _count_markdown_bullets(blocker_doc) + _count_markdown_bullets(phase_doc)
    findings = [
        f"open_blocker_bullets={blocker_count}",
        "production remains blocked until a valid evidence package and independent signoffs exist.",
    ]
    if blocker_count < 30:
        findings.append("expected at least 30 open blocker bullets across clinical runtime sources")
    return _check(
        "P1",
        "Đóng 37 blocker production bằng bằng chứng thật, không tự gỡ",
        [blocker_doc, phase_doc, readiness_ts, go_live_ts, verifier],
        {
            readiness_ts: [
                "productionBlockers",
                "requiredProductionSignoffs",
                "evidencePackage",
                "Not production-ready",
            ],
            go_live_ts: [
                "rollbackPlanArtifactRef",
                "postDeploymentChecklistRef",
                "adminApproverReference",
                "Blocked: do not use with real patient data",
            ],
            verifier: ["--evidence", "--init-template", "PLACEHOLDER_BLOCKED_UNTIL_REVIEWED"],
        },
        findings=findings,
        human_action=(
            "Bác sĩ/quản trị viên chỉ đánh dấu blocker CLEARED sau khi có evidence package, "
            "5 signoff độc lập, dossier hash, rollback và checklist hậu triển khai."
        ),
        human_gated=True,
    )


def check_actor_authentication() -> HardeningCheck:
    approve_gate = REPO / "tools" / "approve_gate.py"
    setup_key = REPO / "tools" / "setup_gate_approval_key.py"
    gate_contract = REPO / "tools" / "gate_contract.py"
    ledger = REPO / "runtime" / "approval_ledger.py"
    tests = [
        REPO / "tests" / "test_approval_ledger.py",
        REPO / "tests" / "test_gate_contract_roles.py",
        REPO / "tests" / "test_gate_contract_approval_ledger_stakeholder_parity.py",
        REPO / "tests" / "test_g9_ledger_gate_required.py",
    ]
    return _check(
        "P2",
        "Xác thực actor thật cho PI/IRB/thống kê/phản biện",
        [approve_gate, setup_key, gate_contract, ledger, *tests],
        {
            approve_gate: ["approver_signature", "reviewer_role_satisfies_gate", "locked_update"],
            setup_key: ["gate_approval_key", "secrets.token_hex", "không nhờ agent"],
            gate_contract: [
                "sign_approval",
                "verify_approval_signature",
                "ledger_approved",
                "G2",
                "G4",
                "G8",
                "G9",
            ],
            ledger: ["AGENT_CREATED_APPROVAL_BLOCKED", "SELF_REVIEW_BLOCKED", "LedgerLockInvalidated"],
        },
        findings=[
            "approval ledger binds role, artifact hash, timestamp and optional local HMAC signature.",
        ],
        human_action=(
            "Bác sĩ tự chạy setup_gate_approval_key.py ngoài phiên agent; mỗi approval thật phải do "
            "người đúng vai trò tự thực hiện, không nhờ agent chạy hộ."
        ),
        human_gated=True,
    )


def check_real_data_pipeline() -> HardeningCheck:
    files = [
        REPO / "tools" / "import_real_dataset.py",
        REPO / "tools" / "deidentify_research_dataset.py",
        REPO / "tools" / "pseudonymize_research_dataset.py",
        REPO / "tools" / "clean_research_dataset.py",
        REPO / "tools" / "lock_analysis_dataset.py",
        REPO / "tools" / "secure_permissions.py",
        REPO / "tests" / "test_real_data_intake.py",
        REPO / "tests" / "test_deidentify_research_dataset.py",
        REPO / "tests" / "test_pseudonymize_research_dataset.py",
        REPO / "tests" / "test_clean_research_dataset.py",
        REPO / "tests" / "test_analysis_dataset_lock.py",
    ]
    return _check(
        "P3",
        "Pipeline dữ liệu thật: PII → pseudonymization → cleaning → data lock",
        files,
        {
            REPO / "tools" / "pseudonymize_research_dataset.py": [
                "mapping_root_inside_repo",
                "mapping_root_inside_exports",
                "mapping_root_inside_onedrive",
                "RETENTION_UNSET_MARKER",
                "protected_mapping_created",
            ],
            REPO / "tools" / "clean_research_dataset.py": [
                "Cleaning không chạy nếu còn PII",
                "query log",
                "raw",
            ],
            REPO / "tools" / "lock_analysis_dataset.py": [
                "confirm_deidentified",
                "confirm_sap_locked",
                "LOCKED_STATUS",
            ],
        },
        findings=[
            "raw file is never overwritten; linkage map stays outside repo/OneDrive by default.",
        ],
        human_action=(
            "Trước dữ liệu thật: cần IRB/DMP, retention owner, mapping custody, data manager "
            "xác nhận no-PII và PI ký data-lock."
        ),
        human_gated=True,
    )


def check_personal_sop() -> HardeningCheck:
    return _check(
        "P4",
        "SOP cá nhân: khi dùng, khi dừng, ai duyệt",
        [SOP_DOC],
        {
            SOP_DOC: [
                "research_mode",
                "clinical_support_mode",
                "Dừng ngay",
                "PII",
                "UAT",
                "backup",
                "rollback",
                "Cần bác sĩ kiểm chứng",
            ],
        },
        findings=["single personal SOP now binds the 7 hardening domains to daily operation."],
        human_action=(
            "Bác sĩ/quản trị viên đọc SOP, điền người phụ trách thật và lưu bản ký tại cơ sở trước "
            "khi chuyển từ synthetic/de-identified pilot sang dữ liệu thật."
        ),
        human_gated=True,
    )


def check_uat_and_shadow_pilot() -> HardeningCheck:
    files = [
        REPO / "chronic-care-clinic-os" / "MVP_01_ACCEPTANCE_TEST.md",
        REPO / "chronic-care-clinic-os" / "TEST_PLAN.md",
        REPO / "docs" / "system-v7" / "PHASE_2C_SHADOW_PILOT_PROTOCOL.md",
        REPO / "docs" / "system-v7" / "PHASE_2D_SHADOW_PILOT_READINESS.md",
        REPO / "tests" / "evals" / "clinical_safety" / "vignettes" / "phase_2a_minimum_vignettes.json",
        REPO / "tests" / "evals" / "clinical_safety" / "vignettes" / "phase_2c_minimum_vignettes.json",
        REPO / "chronic-care-clinic-os" / "scripts" / "verify-outpatient-automation-control.ts",
    ]
    return _check(
        "P5",
        "UAT bằng dữ liệu giả lập và đã khử định danh trước dữ liệu thật",
        files,
        {
            REPO / "chronic-care-clinic-os" / "MVP_01_ACCEPTANCE_TEST.md": [
                "No real data",
                "No e-prescribing",
            ],
            REPO / "docs" / "system-v7" / "PHASE_2C_SHADOW_PILOT_PROTOCOL.md": [
                "shadow",
                "No EMR/HIS write",
            ],
            REPO / "chronic-care-clinic-os" / "scripts" / "verify-outpatient-automation-control.ts": [
                "outpatient",
                "automation",
            ],
        },
        findings=[
            "UAT artifacts exist but real clinic UAT signoff must remain an external human gate.",
        ],
        human_action=(
            "Chạy shadow/UAT với dữ liệu synthetic hoặc đã khử định danh; bác sĩ, điều dưỡng, "
            "quản trị dữ liệu ký biên bản trước khi bật bất kỳ workflow thật nào."
        ),
        human_gated=True,
    )


def check_backup_rollback_monitoring() -> HardeningCheck:
    files = [
        REPO / "docs" / "system-v7" / "ROLLBACK_PLAN.md",
        REPO / "docs" / "system-v7" / "INCIDENT_RESPONSE.md",
        REPO / "docs" / "system-v7" / "CHANGE_CONTROL_POLICY.md",
        REPO / "chronic-care-clinic-os" / "PRODUCTION_GO_LIVE_RUNBOOK.md",
        REPO / "chronic-care-clinic-os" / "DATA_RETENTION_POLICY.md",
        REPO / "chronic-care-clinic-os" / "lib" / "audit-storage-contract.ts",
        REPO / "chronic-care-clinic-os" / "lib" / "prisma-rollback-evidence.ts",
        REPO / "research_automation" / "project_snapshot.py",
        REPO / "app" / "core" / "incident_manager.py",
    ]
    return _check(
        "P6",
        "Backup, versioning, rollback, monitoring và incident response",
        files,
        {
            REPO / "chronic-care-clinic-os" / "PRODUCTION_GO_LIVE_RUNBOOK.md": [
                "rollback",
                "post-deploy",
            ],
            REPO / "docs" / "system-v7" / "ROLLBACK_PLAN.md": ["rollback", "PII leakage"],
            REPO / "research_automation" / "project_snapshot.py": ["snapshot", "rollback"],
        },
        findings=[
            "repo has rollback and incident contracts; production still needs restore drill evidence.",
        ],
        human_action=(
            "Thực hiện restore drill có checksum, xác nhận RPO/RTO, tabletop incident drill và "
            "change ticket/rollback plan cho từng lần go-live."
        ),
        human_gated=True,
    )


def _dangerous_feature_flags_disabled() -> tuple[bool, list[str]]:
    text = _read(REPO / "app" / "core" / "feature_flags.py")
    flags = [
        "v7_clinical_release",
        "v7_research_official_analysis",
        "v7_auto_apply_recommendations",
        "v7_emr_write",
        "v7_production_pathway",
    ]
    missing = [
        flag
        for flag in flags
        if not re.search(rf'"{re.escape(flag)}"\s*:\s*False', text)
    ]
    return not missing, missing


def check_mode_separation() -> HardeningCheck:
    ok, bad_flags = _dangerous_feature_flags_disabled()
    files = [
        REPO / "app" / "core" / "feature_flags.py",
        REPO / "runtime" / "dispatch_guard.py",
        REPO / "research_studio" / "research_workflow.py",
        REPO / "app" / "dashboard" / "v7_readonly.py",
        REPO / "app" / "clinical_content" / "shadow_pilot.py",
        REPO / "chronic-care-clinic-os" / "lib" / "workflow-actions.ts",
    ]
    result = _check(
        "P7",
        "Tách research_mode và clinical_support_mode, không auto-apply/EMR write",
        files,
        {
            REPO / "runtime" / "dispatch_guard.py": [
                "PRODUCTION_CONNECTOR_MARKER",
                "AUTO_SUBMIT_MARKER",
            ],
            REPO / "research_studio" / "research_workflow.py": ["Draft-mode", "build_draft_mode_registry"],
            REPO / "app" / "clinical_content" / "shadow_pilot.py": ["draft/review mode", "không ghi EMR/HIS"],
            REPO / "chronic-care-clinic-os" / "lib" / "workflow-actions.ts": [
                "PREVIEW_ONLY_NOT_PERSISTED",
                "PERSISTENT_PLAN_NOT_COMMITTED",
            ],
        },
        findings=[
            "dangerous_flags_disabled=" + ("true" if ok else "false"),
            *[f"dangerous_flag_not_disabled:{flag}" for flag in bad_flags],
        ],
        human_action=(
            "Chỉ bật research official analysis hoặc clinical release bằng change-control riêng, "
            "không bật chung với auto-apply hoặc EMR write khi chưa có go-live signoff."
        ),
        human_gated=False,
    )
    if ok or result.status == FAIL:
        return result
    return HardeningCheck(
        domain_id=result.domain_id,
        title=result.title,
        status=FAIL,
        evidence=result.evidence,
        findings=result.findings,
        human_action=result.human_action,
    )


def evaluate_all(generated_at: str | None = None) -> dict:
    checks = [
        check_production_blocker_closure(),
        check_actor_authentication(),
        check_real_data_pipeline(),
        check_personal_sop(),
        check_uat_and_shadow_pilot(),
        check_backup_rollback_monitoring(),
        check_mode_separation(),
    ]
    fail_count = sum(1 for item in checks if item.status == FAIL)
    human_gate_count = sum(1 for item in checks if item.status == HUMAN_GATE)
    if fail_count:
        overall = "FAIL_CLOSED"
    elif human_gate_count:
        overall = "CONTROLLED_PERSONAL_READY_WITH_HUMAN_GATES"
    else:
        overall = "CONTROLLED_PERSONAL_READY"
    return {
        "kind": "personal_production_hardening_report",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": overall,
        "fail_count": fail_count,
        "human_gate_count": human_gate_count,
        "clinical_production_allowed": False,
        "real_patient_data_allowed": False if human_gate_count or fail_count else False,
        "checks": [asdict(item) for item in checks],
        "disclaimer": DISCLAIMER,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Personal Production Hardening Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Fail count: `{report['fail_count']}`",
        f"- Human gates: `{report['human_gate_count']}`",
        f"- Clinical production allowed: `{report['clinical_production_allowed']}`",
        f"- Real patient data allowed: `{report['real_patient_data_allowed']}`",
        "",
        "| Domain | Status | Key findings | Required human action |",
        "|---|---|---|---|",
    ]
    for item in report["checks"]:
        findings = "<br>".join(str(x).replace("|", "\\|") for x in item["findings"])
        action = str(item["human_action"]).replace("|", "\\|")
        lines.append(
            f"| {item['domain_id']} - {item['title']} | `{item['status']}` | {findings} | {action} |"
        )
    lines.extend(["", report["disclaimer"], ""])
    return "\n".join(lines)


def write_reports(report: dict, json_path: Path = DEFAULT_JSON, md_path: Path = DEFAULT_MD) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="In toàn bộ báo cáo JSON ra stdout.")
    parser.add_argument("--no-write", action="store_true", help="Không ghi report vào reports/.")
    args = parser.parse_args()

    report = evaluate_all()
    if not args.no_write:
        write_reports(report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={report['overall_status']}")
        print(f"fail_count={report['fail_count']}")
        print(f"human_gate_count={report['human_gate_count']}")
        print("clinical_production_allowed=False")
        print("real_patient_data_allowed=False")
        print("Cần bác sĩ kiểm chứng.")
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
