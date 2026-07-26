from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
import gate_contract as GC  # noqa: E402
import lock_analysis_dataset as LAD  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-data-lock-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _approve_g2_g4_g5(study: str) -> None:
    """Vá 2026-07-12 (audit toàn diện cổng G0-G9): run_stats_analysis.py giờ LUÔN
    đòi phê duyệt ledger THẬT cho G2/G4/G5 — --i-confirm-* chỉ còn thay thế
    checkpoint-file bị mất, không thay được ledger nữa (đóng bypass đã kiểm định
    đối kháng xác nhận là thật). Test file này quan tâm cổng DATA LOCK (downstream
    của G2/G4/G5), nên tạo phê duyệt thật ở đây để tới được phần đang test."""
    study_dir = REPO_ROOT / "exports" / study
    ledger_path = study_dir / "approval_ledger.json"
    ledger = ApprovalLedger.from_file(ledger_path)
    for gate_id, artifact_rel, content in (
        ("G2", f"G2_A3_ETHICS_PACKAGE_{study}.md", "Ethics package test content"),
        ("G4", f"G4_A5_SAP_FINAL_{study}.md", "SAP final test content"),
        ("G5", "G5_checkpoint.json", "G5 checkpoint test content"),
    ):
        role_by_gate = {
            "G2": "IRB_ETHICS_COMMITTEE",
            "G4": "METHODS_STATISTICS_REVIEWER",
            "G5": "DATA_GOVERNANCE_QA_REVIEWER",
        }
        artifact = study_dir / artifact_rel
        artifact.write_text(content, encoding="utf-8")
        timestamp_utc = datetime.now(timezone.utc).isoformat()
        evidence_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        signature = GC.sign_approval(gate_id, study, evidence_hash, timestamp_utc,
                                     reviewer_role=role_by_gate[gate_id],
                                     reviewer_ref=f"TEST-{gate_id}",
                                 decision="APPROVED")
        assert signature
        record = ApprovalLedger.make_human_approval(
            gate_id=gate_id,
            reviewer_role=role_by_gate[gate_id],
            reviewer_ref=f"TEST-{gate_id}",
            scope="test", evidence_content=content,
            approver_signature=signature,
            timestamp_utc=timestamp_utc,
        )
        ok, reason = ledger.add_approval(record)
        assert ok, reason
    ledger.to_file(ledger_path)


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def _clean_dataset(path: Path) -> Path:
    return _csv(
        path,
        """
record_id,age,sex,exposure_var,primary_outcome
S001,41,F,0,0
S002,42,M,0,0
S003,43,F,0,1
S004,51,M,1,0
S005,53,F,1,1
S006,55,M,1,1
""",
    )


def _closed_query_log(path: Path) -> Path:
    return _csv(
        path,
        """
timestamp,issue_type,column,row,detail,status,owner,resolution
2026-07-13,INTAKE_CHECK,,,ok,closed,data manager,closed
""",
    )


def _lock_study(study: str, tmp_path: Path) -> Path:
    clean = _clean_dataset(tmp_path / f"{study}_df_clean.csv")
    qlog = _closed_query_log(tmp_path / f"{study}_query_log.csv")
    manifest = LAD.lock_dataset(
        study,
        clean,
        exports_root=REPO_ROOT / "exports",
        lock_date="2026-07-13",
        approved_by="PI Nguyen",
        sap_version="1.0",
        query_log=qlog,
        confirm_deidentified=True,
        confirm_clean_copy=True,
        confirm_no_open_query=True,
        confirm_sap_locked=True,
    )
    assert manifest["status"] == LAD.LOCKED_STATUS
    _approve_g2_g4_g5(study)
    return REPO_ROOT / "exports" / study / manifest["locked_dataset_path"]


def _run_stats(study: str, data_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            PYTHON,
            str(TOOLS_DIR / "run_stats_analysis.py"),
            "--study", study,
            "--data", str(data_path),
            "--outcome", "primary_outcome",
            "--group", "exposure_var",
            "--covariates", "age",
            "--i-confirm-sap-locked",
            "--i-confirm-irb-approved",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_run_stats_requires_and_accepts_locked_dataset(tmp_path, monkeypatch):
    study = "PYTEST-DLOCK-OK"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        locked_path = _lock_study(study, tmp_path)
        res = _run_stats(study, locked_path)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "DATA LOCK" in res.stdout
        summary_path = study_dir / "G6_analysis_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["data_lock"]["locked_dataset_path"]
        assert summary["data_lock"]["sha256"]
    finally:
        _rmtree_retry(study_dir)


def test_run_stats_blocks_unlocked_data_file(tmp_path, monkeypatch):
    study = "PYTEST-DLOCK-WRONG"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        _lock_study(study, tmp_path)
        other = _clean_dataset(tmp_path / "other_clean.csv")
        res = _run_stats(study, other)
        assert res.returncode != 0
        assert "DATA LOCK" in res.stdout
        assert "provided_data_is_not_locked_dataset" in res.stdout
    finally:
        _rmtree_retry(study_dir)


def test_run_stats_blocks_locked_dataset_checksum_mismatch(tmp_path, monkeypatch):
    study = "PYTEST-DLOCK-TAMPER"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        locked_path = _lock_study(study, tmp_path)
        os.chmod(locked_path, stat.S_IRUSR | stat.S_IWUSR)
        with locked_path.open("a", encoding="utf-8") as f:
            f.write("S999,99,F,1,1\n")
        res = _run_stats(study, locked_path)
        assert res.returncode != 0
        assert "locked_dataset_checksum_mismatch" in res.stdout
    finally:
        _rmtree_retry(study_dir)
