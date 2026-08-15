"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 22, 2026-07-24, phát hiện CRITICAL + HIGH):

tools/run_stats_analysis.py (engine THỰC THI phân tích trên dữ liệu đã khóa,
khác run_g6_auto.py vốn chỉ SINH template) trước đây hoàn toàn không đọc
G1_checkpoint.json — chạy y hệt một quy trình so sánh 2-nhóm kiểu cohort/RCT
(Bảng 1, OR/MD thô, logistic/linear đa biến) cho BẤT KỲ design_code nào, kể cả
"qualitative"/"sr_ma" (không có trục so sánh 2-nhóm participant-level phù hợp)
và "prediction"/"diagnostic" (cần AUC/calibration hoặc Se/Sp/PPV/NPV, không
phải OR/HR thô). Cũng không đọc specialist_modules (G1) để cảnh báo thiếu
phân tích kinh tế y tế khi "economic" là cấu phần cộng thêm.

Test này dùng chính hạ tầng subprocess/lock-dataset đã có ở
test_run_stats_data_lock_gate.py để xác nhận HÀNH VI THẬT của main(), không
chỉ đọc mã nguồn.
"""
from __future__ import annotations

import hashlib
import json
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

from runtime.approval_ledger import ApprovalLedger  # noqa: E402
from tests.g5_test_helpers import prepare_locked_g5_study  # noqa: E402


def _configure_test_signing_key(tmp_path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-design-gate-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _approve_g2_g4_g5(study: str) -> None:
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
    import shutil
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


def _lock_study(study: str, tmp_path: Path, g1_checkpoint: dict) -> Path:
    study_dir = REPO_ROOT / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G1_checkpoint.json").write_text(
        json.dumps(g1_checkpoint), encoding="utf-8")
    clean = _clean_dataset(tmp_path / f"{study}_df_clean.csv")
    locked_path, _ = prepare_locked_g5_study(
        study, clean, exports_root=REPO_ROOT / "exports",
        repo_root=REPO_ROOT,
    )
    return locked_path


def _run_stats(study: str, data_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
            "--study", study, "--data", str(data_path),
            "--outcome", "primary_outcome", "--group", "exposure_var",
            "--i-confirm-sap-locked", "--i-confirm-irb-approved",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
    )


class TestQualitativeAndSrmaHardStop:
    def test_qualitative_design_code_stops_before_analysis(self, tmp_path, monkeypatch):
        study = "PYTEST-G6GATE-QUALITATIVE"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(study, tmp_path, {"design_code": "qualitative"})
            res = _run_stats(study, locked_path)
            assert res.returncode != 0, res.stdout + res.stderr
            assert "DỪNG" in res.stdout
            assert "qualitative" in res.stdout
            assert not (study_dir / "G6_table2_main_outcome.txt").exists()
        finally:
            _rmtree_retry(study_dir)

    def test_sr_ma_design_code_stops_before_analysis(self, tmp_path, monkeypatch):
        study = "PYTEST-G6GATE-SRMA"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(study, tmp_path, {"design_code": "sr_ma"})
            res = _run_stats(study, locked_path)
            assert res.returncode != 0, res.stdout + res.stderr
            assert "DỪNG" in res.stdout
            assert "sr_ma" in res.stdout
        finally:
            _rmtree_retry(study_dir)


class TestPredictionDiagnosticWarnNotBlock:
    def test_prediction_design_warns_but_still_runs(self, tmp_path, monkeypatch):
        study = "PYTEST-G6GATE-PREDICTION"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(study, tmp_path, {"design_code": "prediction"})
            res = _run_stats(study, locked_path)
            assert res.returncode == 0, res.stdout + res.stderr
            assert "CẦN THỐNG KÊ VIÊN" in res.stdout
            assert "AUC" in res.stdout
            assert (study_dir / "G6_table2_main_outcome.txt").exists()
        finally:
            _rmtree_retry(study_dir)

    def test_diagnostic_design_warns_but_still_runs(self, tmp_path, monkeypatch):
        study = "PYTEST-G6GATE-DIAGNOSTIC"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(study, tmp_path, {"design_code": "diagnostic"})
            res = _run_stats(study, locked_path)
            assert res.returncode == 0, res.stdout + res.stderr
            assert "CẦN THỐNG KÊ VIÊN" in res.stdout
            assert "Se/Sp/PPV/NPV" in res.stdout
        finally:
            _rmtree_retry(study_dir)

    def test_rct_design_has_no_wrong_measure_warning(self, tmp_path, monkeypatch):
        """Thiết kế rct (khuôn engine này thực sự phù hợp) KHÔNG bị cảnh báo sai lầm."""
        study = "PYTEST-G6GATE-RCT-CLEAN"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(study, tmp_path, {"design_code": "rct"})
            res = _run_stats(study, locked_path)
            assert res.returncode == 0, res.stdout + res.stderr
            assert "CẦN THỐNG KÊ VIÊN] design_code" not in res.stdout
        finally:
            _rmtree_retry(study_dir)


class TestSpecialistModulesEconomicWarning:
    def test_economic_add_on_module_flags_missing_cost_effectiveness_analysis(self, tmp_path, monkeypatch):
        study = "PYTEST-G6GATE-ECONOMIC-ADDON"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(
                study, tmp_path,
                {"design_code": "rct", "specialist_modules": ["economic"]})
            res = _run_stats(study, locked_path)
            assert res.returncode == 0, res.stdout + res.stderr
            assert "KINH TẾ Y TẾ" in res.stdout
            assert "ICER" in res.stdout
        finally:
            _rmtree_retry(study_dir)

    def test_no_specialist_modules_no_economic_warning(self, tmp_path, monkeypatch):
        study = "PYTEST-G6GATE-NO-ECONOMIC"
        study_dir = REPO_ROOT / "exports" / study
        _rmtree_retry(study_dir)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            locked_path = _lock_study(study, tmp_path, {"design_code": "rct"})
            res = _run_stats(study, locked_path)
            assert res.returncode == 0, res.stdout + res.stderr
            assert "KINH TẾ Y TẾ" not in res.stdout
        finally:
            _rmtree_retry(study_dir)
