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
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _workspace_root import resolve_workspace_root  # noqa: E402

ROOT = resolve_workspace_root(REPO)
REPORTS = REPO / "reports"
DEFAULT_JSON = REPORTS / "PERSONAL_PRODUCTION_HARDENING_REPORT.json"
DEFAULT_MD = REPORTS / "PERSONAL_PRODUCTION_HARDENING_REPORT.md"
SOP_DOC = REPO / "docs" / "PERSONAL_PRODUCTION_HARDENING_SOP.md"

PASS = "PASS"
HUMAN_GATE = "HUMAN_GATE"
FAIL = "FAIL"
PACKAGE_KIND = "personal_production_hardening_evidence_package"
PLACEHOLDER_RE = re.compile(r"(TODO|TBD|PLACEHOLDER|REPLACE_ME|\[CẦN|\[CAN)", re.IGNORECASE)
SAFE_PATH_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,79}$")
ARTIFACT_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+-]{2,199}$")
PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)),
    ("phone", re.compile(r"\b0\d{9,10}\b")),
    ("national_id", re.compile(r"\b\d{12}\b")),
)


def ensure_utf8_console() -> None:
    """Keep Windows PowerShell/cp1252 from crashing on Vietnamese gate text."""
    for stream in (sys.stdout, sys.stderr):
        try:
            encoding = (getattr(stream, "encoding", "") or "").lower()
            if encoding and "utf" not in encoding and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            continue
FORBIDDEN_PII_KEYS = {
    "address",
    "cccd",
    "cmnd",
    "date_of_birth",
    "dob",
    "ho_ten",
    "medical_record_number",
    "mrn",
    "patient_id",
    "patient_name",
    "phone",
    "phone_number",
    "ten_benh_nhan",
}
FORBIDDEN_ARTIFACT_SEGMENTS = {
    ".env",
    "identifiers",
    "phi",
    "pii",
    "raw",
    "restricted",
    "secret",
    "secrets",
}
FORBIDDEN_ARTIFACT_SUBSTRINGS = (
    ".env",
    "linkage-key",
    "mapping-table",
    "patient-identifiers",
    "raw-dataset",
    "reidentification",
)
REQUIRED_SIGNOFF_ROLES = [
    "security_owner",
    "data_protection_owner",
    "legal_compliance_owner",
    "physician_lead",
    "uat_owner",
    "operations_owner",
    "ai_governance_owner",
    "pi_or_clinic_owner",
]
DOMAIN_EVIDENCE_REQUIREMENTS = {
    "P1": ("production_owner", "Production blocker closure evidence package and signoffs."),
    "P2": ("pi_or_clinic_owner", "Actor authentication/key custody and gate approval evidence."),
    "P3": ("data_protection_owner", "Real-data PII, pseudonymization, mapping custody and data-lock evidence."),
    "P4": ("pi_or_clinic_owner", "Signed personal SOP and operating boundary evidence."),
    "P5": ("physician_lead", "Synthetic/de-identified UAT and clinical shadow pilot evidence."),
    "P6": ("operations_owner", "Backup, restore drill, rollback and incident drill evidence."),
    "P7": ("ai_governance_owner", "Mode separation, feature-flag and no-auto-apply evidence."),
}

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


@dataclass(frozen=True)
class EvidencePackageSummary:
    status: str
    provided: bool
    valid: bool
    evidence_records: int
    valid_evidence_records: int
    valid_signoffs: int
    valid_approval_record: bool
    missing_domains: list[str]
    missing_signoffs: list[str]
    errors: list[str]


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


def _parse_iso(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_reference(value: Any) -> bool:
    """Opaque non-PII reference: không placeholder, email, phone hoặc số định danh dài."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    if len(text) < 3:
        return False
    if PLACEHOLDER_RE.search(text):
        return False
    if any(pattern.search(text) for _label, pattern in PII_PATTERNS):
        return False
    return True


def _normalize_json_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _safe_json_path_key(value: str) -> str:
    if not SAFE_PATH_KEY_RE.fullmatch(value):
        return "<key>"
    if PLACEHOLDER_RE.search(value):
        return "<key>"
    if any(pattern.search(value) for _label, pattern in PII_PATTERNS):
        return "<key>"
    return value


def _safe_artifact_reference(value: Any) -> bool:
    """Artefact ref an toàn: tương đối, không URL/traversal, không trỏ vùng PII/secret/raw."""
    if not _safe_reference(value):
        return False
    text = str(value).strip()
    lowered = text.lower()
    if not ARTIFACT_REF_RE.fullmatch(text):
        return False
    if lowered.startswith(("/", "~")) or lowered.endswith("/"):
        return False
    if "\\" in text or ":" in text or "//" in text:
        return False
    segments = [segment for segment in lowered.split("/") if segment]
    if len(segments) != len(lowered.split("/")):
        return False
    if any(segment in {".", ".."} or segment.startswith(".") for segment in segments):
        return False
    if any(segment in FORBIDDEN_ARTIFACT_SEGMENTS for segment in segments):
        return False
    return not any(token in lowered for token in FORBIDDEN_ARTIFACT_SUBSTRINGS)


def _scan_package_text_policy(value: Any, path: str = "$") -> list[str]:
    """Quét placeholder/PII trong toàn package mà không đưa giá trị nhạy cảm vào lỗi."""
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{path}.{_safe_json_path_key(key_text)}"
            normalized = _normalize_json_key(key_text)
            if normalized in FORBIDDEN_PII_KEYS:
                findings.append(f"package_text_policy:{key_path}:forbidden_pii_key")
            if PLACEHOLDER_RE.search(key_text):
                findings.append(f"package_text_policy:{key_path}:placeholder_key")
            for label, pattern in PII_PATTERNS:
                if pattern.search(key_text):
                    findings.append(f"package_text_policy:{key_path}:pii_key_{label}")
            findings.extend(_scan_package_text_policy(item, key_path))
        return findings
    if isinstance(value, list):
        for idx, item in enumerate(value):
            findings.extend(_scan_package_text_policy(item, f"{path}[{idx}]"))
        return findings
    if isinstance(value, str):
        if PLACEHOLDER_RE.search(value):
            findings.append(f"package_text_policy:{path}:placeholder_value")
        for label, pattern in PII_PATTERNS:
            if pattern.search(value):
                findings.append(f"package_text_policy:{path}:pii_value_{label}")
    return findings


def build_evidence_template(generated_at: str | None = None) -> dict[str, Any]:
    """Sinh mẫu evidence package; mọi placeholder cố ý làm validator fail-closed."""
    stamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "kind": PACKAGE_KIND,
        "generated_at": stamp,
        "scope": "TODO_REPLACE_WITH_SIGNED_SCOPE_NO_PII",
        "evidence": [
            {
                "domain_id": domain_id,
                "status": "TODO_REVIEW",
                "reviewed_by_role": owner_role,
                "reviewer_reference": f"TODO_NON_PII_REVIEWER_REF_{domain_id}",
                "reviewed_at": "TODO_ISO8601",
                "artifact_refs": [f"TODO/evidence/{domain_id}.json"],
                "controls_verified": [description],
                "notes": "TODO replace after human review. Do not include PII.",
            }
            for domain_id, (owner_role, description) in DOMAIN_EVIDENCE_REQUIREMENTS.items()
        ],
        "signoffs": [
            {
                "role": role,
                "signer_reference": f"TODO_NON_PII_SIGNER_REF_{role}",
                "signed_at": "TODO_ISO8601",
                "scope": "TODO_REPLACE_WITH_SIGNED_SCOPE_NO_PII",
                "artifact_refs": [f"TODO/signoffs/{role}.json"],
            }
            for role in REQUIRED_SIGNOFF_ROLES
        ],
        "approval_record": {
            "approval_id": "TODO_GO_LIVE_APPROVAL_ID",
            "status": "approved_for_go_live_review",
            "approver_role": "pi_or_clinic_owner",
            "approver_reference": "TODO_DISTINCT_PI_OR_CLINIC_APPROVER_REF",
            "approved_at": "TODO_ISO8601",
            "scope": "TODO_REPLACE_WITH_SIGNED_SCOPE_NO_PII",
            "artifact_refs": ["TODO/approval-record/go-live-approval.json"],
        },
        "go_live_attestation": {
            "release_id": "TODO_RELEASE_ID",
            "change_ticket_reference": "TODO_CHANGE_TICKET",
            "rollback_plan_artifact_ref": "TODO/rollback-plan.json",
            "post_deployment_checklist_ref": "TODO/post-deploy-checklist.json",
            "evidence_dossier_sha256": "TODO_64_HEX_SHA256",
            "operator_reference": "TODO_OPERATOR_REF",
            "admin_approver_reference": "TODO_DISTINCT_ADMIN_APPROVER_REF",
        },
        "safety_boundary": (
            "Template only. A structurally valid package is ready for external/human review; "
            "it does not by itself authorize clinical production or real patient data."
        ),
    }


def validate_evidence_package(
    package: dict[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> EvidencePackageSummary:
    if package is None:
        return EvidencePackageSummary(
            status="NOT_PROVIDED",
            provided=False,
            valid=False,
            evidence_records=0,
            valid_evidence_records=0,
            valid_signoffs=0,
            valid_approval_record=False,
            missing_domains=list(DOMAIN_EVIDENCE_REQUIREMENTS),
            missing_signoffs=list(REQUIRED_SIGNOFF_ROLES),
            errors=[],
        )

    now = _parse_iso(generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"))
    errors: list[str] = []
    errors.extend(_scan_package_text_policy(package))
    if package.get("kind") != PACKAGE_KIND:
        errors.append("package_kind_invalid")
    pkg_time = _parse_iso(str(package.get("generated_at", "")))
    if pkg_time is None:
        errors.append("package_generated_at_invalid")
    elif now and pkg_time > now:
        errors.append("package_generated_at_future")
    if not _safe_reference(str(package.get("scope", ""))):
        errors.append("scope_missing_or_placeholder_or_pii")

    evidence = package.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
        errors.append("evidence_must_be_list")
    seen_domains: set[str] = set()
    valid_domains: set[str] = set()
    for idx, record in enumerate(evidence):
        if not isinstance(record, dict):
            errors.append(f"evidence[{idx}]_not_object")
            continue
        domain_id = str(record.get("domain_id", ""))
        if domain_id not in DOMAIN_EVIDENCE_REQUIREMENTS:
            errors.append(f"evidence[{idx}]_unknown_domain:{domain_id}")
            continue
        if domain_id in seen_domains:
            errors.append(f"evidence_duplicate_domain:{domain_id}")
            continue
        seen_domains.add(domain_id)
        required_role, _description = DOMAIN_EVIDENCE_REQUIREMENTS[domain_id]
        record_errors: list[str] = []
        if record.get("status") != "CLEARED":
            record_errors.append("status_not_cleared")
        if record.get("reviewed_by_role") != required_role:
            record_errors.append("reviewed_by_role_invalid")
        if not _safe_reference(record.get("reviewer_reference")):
            record_errors.append("reviewer_reference_invalid")
        reviewed_at = _parse_iso(str(record.get("reviewed_at", "")))
        if reviewed_at is None:
            record_errors.append("reviewed_at_invalid")
        elif now and reviewed_at > now:
            record_errors.append("reviewed_at_future")
        artifact_refs = record.get("artifact_refs")
        if (
            not isinstance(artifact_refs, list)
            or not artifact_refs
            or not all(_safe_artifact_reference(x) for x in artifact_refs)
        ):
            record_errors.append("artifact_refs_invalid")
        controls = record.get("controls_verified")
        if not isinstance(controls, list) or not controls or not all(_safe_reference(x) for x in controls):
            record_errors.append("controls_verified_invalid")
        if record_errors:
            errors.extend(f"evidence[{domain_id}]:{err}" for err in record_errors)
        else:
            valid_domains.add(domain_id)

    missing_domains = [
        domain_id
        for domain_id in DOMAIN_EVIDENCE_REQUIREMENTS
        if domain_id not in seen_domains
    ]
    errors.extend(f"missing_domain:{domain_id}" for domain_id in missing_domains)

    signoffs = package.get("signoffs")
    if not isinstance(signoffs, list):
        signoffs = []
        errors.append("signoffs_must_be_list")
    seen_signoffs: set[str] = set()
    valid_signoffs: set[str] = set()
    signer_refs: dict[str, str] = {}
    for idx, signoff in enumerate(signoffs):
        if not isinstance(signoff, dict):
            errors.append(f"signoff[{idx}]_not_object")
            continue
        role = str(signoff.get("role", ""))
        if role not in REQUIRED_SIGNOFF_ROLES:
            errors.append(f"signoff[{idx}]_unknown_role:{role}")
            continue
        if role in seen_signoffs:
            errors.append(f"signoff_duplicate_role:{role}")
            continue
        seen_signoffs.add(role)
        signoff_errors: list[str] = []
        signer = signoff.get("signer_reference")
        if not _safe_reference(signer):
            signoff_errors.append("signer_reference_invalid")
        elif str(signer).lower() in signer_refs:
            signoff_errors.append(f"signer_reference_reused_with:{signer_refs[str(signer).lower()]}")
        else:
            signer_refs[str(signer).lower()] = role
        signed_at = _parse_iso(str(signoff.get("signed_at", "")))
        if signed_at is None:
            signoff_errors.append("signed_at_invalid")
        elif now and signed_at > now:
            signoff_errors.append("signed_at_future")
        if not _safe_reference(signoff.get("scope")):
            signoff_errors.append("scope_invalid")
        refs = signoff.get("artifact_refs")
        if not isinstance(refs, list) or not refs or not all(_safe_artifact_reference(x) for x in refs):
            signoff_errors.append("artifact_refs_invalid")
        if signoff_errors:
            errors.extend(f"signoff[{role}]:{err}" for err in signoff_errors)
        else:
            valid_signoffs.add(role)

    missing_signoffs = [
        role
        for role in REQUIRED_SIGNOFF_ROLES
        if role not in seen_signoffs
    ]
    errors.extend(f"missing_signoff:{role}" for role in missing_signoffs)

    approval_record = package.get("approval_record")
    valid_approval_record = False
    if not isinstance(approval_record, dict):
        errors.append("approval_record_missing")
    else:
        approval_errors: list[str] = []
        if not _safe_reference(approval_record.get("approval_id")):
            approval_errors.append("approval_id_invalid")
        if approval_record.get("status") != "approved_for_go_live_review":
            approval_errors.append("status_invalid")
        if approval_record.get("approver_role") != "pi_or_clinic_owner":
            approval_errors.append("approver_role_invalid")
        approver = approval_record.get("approver_reference")
        if not _safe_reference(approver):
            approval_errors.append("approver_reference_invalid")
        elif str(approver).lower() in signer_refs:
            approval_errors.append(f"approver_reference_reused_with:{signer_refs[str(approver).lower()]}")
        approved_at = _parse_iso(str(approval_record.get("approved_at", "")))
        if approved_at is None:
            approval_errors.append("approved_at_invalid")
        elif now and approved_at > now:
            approval_errors.append("approved_at_future")
        if not _safe_reference(approval_record.get("scope")):
            approval_errors.append("scope_invalid")
        refs = approval_record.get("artifact_refs")
        if not isinstance(refs, list) or not refs or not all(_safe_artifact_reference(x) for x in refs):
            approval_errors.append("artifact_refs_invalid")
        if approval_errors:
            errors.extend(f"approval_record:{err}" for err in approval_errors)
        else:
            valid_approval_record = True

    attestation = package.get("go_live_attestation")
    if not isinstance(attestation, dict):
        errors.append("go_live_attestation_missing")
    else:
        for field in (
            "release_id",
            "change_ticket_reference",
            "operator_reference",
            "admin_approver_reference",
        ):
            if not _safe_reference(attestation.get(field)):
                errors.append(f"go_live_attestation:{field}_invalid")
        for field in ("rollback_plan_artifact_ref", "post_deployment_checklist_ref"):
            if not _safe_artifact_reference(attestation.get(field)):
                errors.append(f"go_live_attestation:{field}_invalid")
        dossier = str(attestation.get("evidence_dossier_sha256", ""))
        if not re.fullmatch(r"[a-f0-9]{64}", dossier, flags=re.IGNORECASE):
            errors.append("go_live_attestation:evidence_dossier_sha256_invalid")
        operator = str(attestation.get("operator_reference", "")).strip().lower()
        admin = str(attestation.get("admin_approver_reference", "")).strip().lower()
        if operator and admin and operator == admin:
            errors.append("go_live_attestation:operator_admin_must_be_distinct")

    valid = not errors
    status = "STRUCTURALLY_COMPLETE_EXTERNAL_REVIEW_READY" if valid else "INVALID_OR_INCOMPLETE"
    return EvidencePackageSummary(
        status=status,
        provided=True,
        valid=valid,
        evidence_records=len(evidence),
        valid_evidence_records=len(valid_domains),
        valid_signoffs=len(valid_signoffs),
        valid_approval_record=valid_approval_record,
        missing_domains=missing_domains,
        missing_signoffs=missing_signoffs,
        errors=errors,
    )


def load_evidence_package(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
            "7 signoff độc lập, approval record, dossier hash, rollback và checklist hậu triển khai."
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


def evaluate_all(
    generated_at: str | None = None,
    evidence_package: dict[str, Any] | None = None,
    evidence_path: Path | None = None,
) -> dict:
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
    if evidence_package is None and evidence_path is not None:
        evidence_package = load_evidence_package(evidence_path)
    evidence_summary = validate_evidence_package(evidence_package, generated_at=generated_at)
    if evidence_summary.provided and not evidence_summary.valid:
        overall = "FAIL_CLOSED"
    return {
        "kind": "personal_production_hardening_report",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": overall,
        "fail_count": fail_count,
        "human_gate_count": human_gate_count,
        "evidence_package_summary": asdict(evidence_summary),
        "clinical_production_allowed": False,
        # SỬA vòng 26 (2026-09-05): trước là "False if human_gate_count or
        # fail_count else False" — cả hai nhánh đều trả False, điều kiện
        # không bao giờ ảnh hưởng tới giá trị (code chết/tautology). Không
        # đổi hành vi (kết quả luôn False cả trước và sau, khớp cách các
        # module chị em verify_clinical_production_control_plane.py và
        # verify_evidence_surveillance_deployment.py hard-code sẵn) — chỉ
        # bỏ nhánh điều kiện vô nghĩa để không gây hiểu lầm là có logic ở đây.
        "real_patient_data_allowed": False,
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
        f"- Evidence package: `{report['evidence_package_summary']['status']}`",
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
    evidence = report["evidence_package_summary"]
    lines.extend(
        [
            "",
            "## Evidence Package",
            "",
            f"- Status: `{evidence['status']}`",
            f"- Valid evidence records: `{evidence['valid_evidence_records']}/{len(DOMAIN_EVIDENCE_REQUIREMENTS)}`",
            f"- Valid signoffs: `{evidence['valid_signoffs']}/{len(REQUIRED_SIGNOFF_ROLES)}`",
            f"- Missing domains: `{', '.join(evidence['missing_domains']) or 'none'}`",
            f"- Missing signoffs: `{', '.join(evidence['missing_signoffs']) or 'none'}`",
        ]
    )
    if evidence["errors"]:
        lines.append(f"- Errors: `{'; '.join(evidence['errors'][:20])}`")
    lines.extend(["", report["disclaimer"], ""])
    return "\n".join(lines)


def write_reports(report: dict, json_path: Path = DEFAULT_JSON, md_path: Path = DEFAULT_MD) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    md_path.write_text(markdown_report(report), encoding="utf-8", newline="\n")


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="In toàn bộ báo cáo JSON ra stdout.")
    parser.add_argument("--no-write", action="store_true", help="Không ghi report vào reports/.")
    parser.add_argument("--evidence", type=Path, default=None, help="Gói evidence package đã điền để kiểm schema.")
    parser.add_argument("--init-evidence-template", type=Path, default=None, help="Ghi mẫu evidence package đầy đủ.")
    parser.add_argument("--force", action="store_true", help="Ghi đè khi dùng --init-evidence-template.")
    args = parser.parse_args()

    if args.init_evidence_template is not None:
        if args.init_evidence_template.exists() and not args.force:
            print(f"BLOCKED: template already exists: {args.init_evidence_template}")
            return 2
        args.init_evidence_template.parent.mkdir(parents=True, exist_ok=True)
        template = build_evidence_template()
        args.init_evidence_template.write_text(
            json.dumps(template, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n"
        )
        validation = validate_evidence_package(template)
        print(f"template={args.init_evidence_template}")
        print(f"evidence_records={len(template['evidence'])}")
        print(f"signoffs={len(template['signoffs'])}")
        print(f"status={validation.status}")
        print("Cần bác sĩ kiểm chứng.")
        return 0

    report = evaluate_all(evidence_path=args.evidence)
    if not args.no_write:
        write_reports(report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={report['overall_status']}")
        print(f"fail_count={report['fail_count']}")
        print(f"human_gate_count={report['human_gate_count']}")
        print(f"evidence_package_status={report['evidence_package_summary']['status']}")
        print("clinical_production_allowed=False")
        print("real_patient_data_allowed=False")
        print("Cần bác sĩ kiểm chứng.")
    evidence_ok = (
        not report["evidence_package_summary"]["provided"]
        or report["evidence_package_summary"]["valid"]
    )
    return 0 if report["fail_count"] == 0 and evidence_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
