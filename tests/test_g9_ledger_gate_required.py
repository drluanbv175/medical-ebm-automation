"""Hồi quy: G9 (cổng cứng CUỐI CÙNG trước nộp bài) phải xác minh phê duyệt G2/G4
THẬT trong approval_ledger.json (hash khớp artifact), không chỉ checkpoint text tự
do (audit 2026-07-11 — cùng lỗ hổng đã vá ở run_stats_analysis.py/run_g6_auto.py
2026-07-09, nhưng chưa từng lan tới G9 dù đây là cổng có hậu quả nặng nhất: nộp bản
thảo ra ngoài với IRB/SAP CHƯA THẬT sự phê duyệt).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import run_g9_auto as G9  # noqa: E402


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g9-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_artifacts_and_locked_text(study: str, d: Path) -> tuple[str, str]:
    """Tạo artifact G2/G4 + checkpoint TEXT nói đã có IRB/SAP (nhưng KHÔNG có
    ledger) — trả nội dung 2 artifact để gọi hàm ledger dùng chung."""
    g2_content = "ETHICS PACKAGE — nội dung giả lập test"
    g4_content = "SAP FINAL — nội dung giả lập test"
    (d / f"G2_A3_ETHICS_PACKAGE_{study}.md").write_text(g2_content, encoding="utf-8")
    (d / f"G4_A5_SAP_FINAL_{study}.md").write_text(g4_content, encoding="utf-8")
    return g2_content, g4_content


def _write_ledger_approval(d: Path, gate_id: str, artifact_content: str) -> None:
    evidence_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
    timestamp_utc = "2026-07-11T00:00:00+00:00"
    role_by_gate = {
        "G2": "IRB_ETHICS_COMMITTEE",
        "G4": "METHODS_STATISTICS_REVIEWER",
        "G9": "PI_PROJECT_OWNER",
    }
    reviewer_role = role_by_gate.get(gate_id, "PI_PROJECT_OWNER")
    signature = GC.sign_approval(gate_id, d.name, evidence_hash, timestamp_utc,
                                 reviewer_role=reviewer_role, reviewer_ref="REF-TEST-001",
                                 decision="APPROVED")
    assert signature
    record = {
        "approval_id": f"test-{gate_id}-001", "gate_id": gate_id,
        "reviewer_role": reviewer_role,
        "reviewer_identity_reference": "REF-TEST-001",
        "decision": "APPROVED", "scope": "test", "evidence_hash": evidence_hash,
        "timestamp_utc": timestamp_utc, "supersedes": None,
        "artifact_creator_agent": None, "reviewer_agent": None,
        "is_synthetic": False,
        "approver_signature": signature,
    }
    ledger_path = d / "approval_ledger.json"
    existing = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    existing.append(record)
    ledger_path.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
    # Niem phong (2026-07-27): so cai khong rong ma thieu con dau la BAT THUONG.
    GC.write_ledger_seal(d.name, existing, repo_root=REPO_ROOT)


_CPS_TEXT_LOCKED = {
    "G2": {"g2_irb_number": "IRB-2026-00123"},
    "G4": {"sap_signed_date": "2026-07-01"},
}
_GUARDRAIL = {"passed": True, "errors": [], "warnings": []}


def test_build_part8_checkpoint_text_alone_not_sufficient():
    """Checkpoint TEXT nói đã có IRB/SAP nhưng KHÔNG có approval_ledger.json —
    build_part8_gate_criteria() vẫn phải hiện '⚠ CHỜ BÁC SĨ', không phải '✅'."""
    study = "PYTEST-G9-T1"
    d = _study_dir(study)
    try:
        _write_artifacts_and_locked_text(study, d)
        md = G9.build_part8_gate_criteria(_CPS_TEXT_LOCKED, n_authors=3, study=study)
        assert "⚠ CHỜ BÁC SĨ" in md, (
            "Checkpoint text một mình đủ để G9 báo '✅' — hồi quy về lỗ hổng đã vá "
            "ở run_stats_analysis.py/run_g6_auto.py nhưng chưa lan tới G9.")
    finally:
        _rmtree_retry(d)


def test_build_part8_checkpoint_with_matching_ledger_passes(tmp_path, monkeypatch):
    """Checkpoint text + approval_ledger.json khớp hash → phải hiện '✅'."""
    study = "PYTEST-G9-T2"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        g2_content, g4_content = _write_artifacts_and_locked_text(study, d)
        _write_ledger_approval(d, "G2", g2_content)
        _write_ledger_approval(d, "G4", g4_content)
        md = G9.build_part8_gate_criteria(_CPS_TEXT_LOCKED, n_authors=3, study=study)
        assert "✅" in md
    finally:
        _rmtree_retry(d)


def test_write_g9_checkpoint_pending_lists_gate_when_ledger_missing():
    """write_g9_checkpoint(): checkpoint text LOCKED nhưng KHÔNG có ledger →
    'pending' vẫn phải liệt kê G2/G4 chưa LOCKED (không được để lọt qua)."""
    study = "PYTEST-G9-T3"
    d = _study_dir(study)
    try:
        _write_artifacts_and_locked_text(study, d)
        cp_path = G9.write_g9_checkpoint(
            study=study, out_dir=d, n_authors=3, target_journal="Test Journal",
            guardrail=_GUARDRAIL, md_path=d / "dummy.md", docx_path=None,
            cps=_CPS_TEXT_LOCKED,
        )
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        pending_text = " | ".join(cp["pending"])
        assert "G2 (Đạo đức) chưa LOCKED" in pending_text
        assert "G4 (SAP) chưa LOCKED" in pending_text
    finally:
        _rmtree_retry(d)


def test_write_g9_checkpoint_pending_clears_when_ledger_present(tmp_path, monkeypatch):
    """Cùng kịch bản trên nhưng CÓ ledger khớp hash → pending không còn liệt kê
    G2/G4 là 'chưa LOCKED'."""
    study = "PYTEST-G9-T4"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        g2_content, g4_content = _write_artifacts_and_locked_text(study, d)
        _write_ledger_approval(d, "G2", g2_content)
        _write_ledger_approval(d, "G4", g4_content)
        cp_path = G9.write_g9_checkpoint(
            study=study, out_dir=d, n_authors=3, target_journal="Test Journal",
            guardrail=_GUARDRAIL, md_path=d / "dummy.md", docx_path=None,
            cps=_CPS_TEXT_LOCKED,
        )
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        pending_text = " | ".join(cp["pending"])
        assert "G2 (Đạo đức) chưa LOCKED" not in pending_text
        assert "G4 (SAP) chưa LOCKED" not in pending_text
    finally:
        _rmtree_retry(d)
