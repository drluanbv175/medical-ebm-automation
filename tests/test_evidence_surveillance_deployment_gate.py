from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "verify_evidence_surveillance_deployment.py"
SPEC = importlib.util.spec_from_file_location("verify_evidence_surveillance_deployment", MODULE_PATH)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V
SPEC.loader.exec_module(V)


def _contract() -> dict:
    return json.loads(V.CONTRACT_PATH.read_text(encoding="utf-8"))


def test_pending_uat_is_a_human_gate_not_a_pass(tmp_path: Path) -> None:
    # Dựng trạng thái PENDING đúng nghĩa bằng fixture riêng (khớp bản khởi tạo
    # UAT_EVIDENCE.json ngày 2026-08-01) thay vì đọc V.UAT_PATH: file đó là bằng chứng UAT
    # SỐNG của dự án, và bác sĩ có thể hoàn tất nó thật (đã xảy ra 2026-09-13, commit
    # e3be5cf "hoàn tất 7/7 mục UAT_EVIDENCE.json") — khi đó nó hợp lệ chuyển sang PASS,
    # đây không phải lỗi fail-open của _check_uat().
    payload = {
        "source_sample_review": [],
        "scheduler_trigger": {
            "status": "PENDING",
            "weekly_runtime_status_path": "",
            "monthly_runtime_status_path": "",
        },
        "alert_delivery": {
            "status": "PENDING",
            "channel": "",
            "tested_at": "",
            "evidence_note": "",
        },
        "rollback_restore": {
            "status": "PENDING",
            "tested_at": "",
            "backup_path": "",
            "restore_hash_match": False,
        },
        "shadow_run": {
            "status": "PENDING",
            "cycles": 0,
            "failed_cycles": 0,
            "auto_apply_observed": False,
            "evidence_paths": [],
        },
        "doctor_approval": {
            "approved": False,
            "approved_by_role": "doctor",
            "approved_at": "",
            "scope": "candidate_only",
        },
        "operations_approval": {
            "approved": False,
            "approved_by_role": "operations",
            "approved_at": "",
            "scope": "scheduler_alert_backup_rollback",
        },
        "clinical_auto_apply": False,
        "real_patient_data": False,
    }
    path = tmp_path / "uat.json"
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")

    result = V._check_uat(_contract(), path)

    assert result.status == V.HUMAN_GATE
    assert "DOCTOR_APPROVAL" in result.evidence
    assert "SHADOW_RUN" in result.evidence


def test_complete_uat_requires_five_doctor_reviewed_sources(tmp_path: Path) -> None:
    samples = [
        {
            "pmid": str(10000 + index),
            "source_opened": True,
            "title_match": True,
            "clinical_claim_checked": True,
            "reviewed_by_role": "doctor",
        }
        for index in range(5)
    ]
    payload = {
        "source_sample_review": samples,
        "scheduler_trigger": {"status": "PASS"},
        "alert_delivery": {"status": "PASS"},
        "rollback_restore": {"status": "PASS", "restore_hash_match": True},
        "shadow_run": {
            "status": "PASS",
            "cycles": 2,
            "failed_cycles": 0,
            "auto_apply_observed": False,
        },
        "doctor_approval": {"approved": True, "approved_by_role": "doctor"},
        "operations_approval": {"approved": True, "approved_by_role": "operations"},
        "clinical_auto_apply": False,
        "real_patient_data": False,
    }
    path = tmp_path / "uat.json"
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")

    result = V._check_uat(_contract(), path)

    assert result.status == V.PASS
    assert "valid_source_samples=5" in result.evidence


def test_uat_fails_if_auto_apply_was_observed(tmp_path: Path) -> None:
    payload = json.loads(V.UAT_PATH.read_text(encoding="utf-8"))
    payload["shadow_run"] = {
        "status": "PASS",
        "cycles": 2,
        "failed_cycles": 0,
        "auto_apply_observed": True,
    }
    path = tmp_path / "uat.json"
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")

    result = V._check_uat(_contract(), path)

    assert result.status == V.HUMAN_GATE
    assert "SHADOW_RUN" in result.evidence


def test_contract_explicitly_prohibits_clinical_auto_apply() -> None:
    result = V._check_contract()

    assert result.status == V.PASS
    contract = _contract()
    assert contract["prohibited"]["clinical_auto_apply"] is True
    assert contract["deployment_mode"] == "candidate_only_doctor_review_required"


def test_shared_report_sanitizes_local_user_paths() -> None:
    raw = f"{V.ROOT}/reports/check.json; {Path.home()}/Library/LaunchAgents"

    sanitized = V._sanitize_local_paths(raw)

    assert str(Path.home()) not in sanitized
    assert sanitized == "<WORKSPACE>/reports/check.json; <HOME>/Library/LaunchAgents"
