# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 12 (2026-07-23, dimension
g8_g9_remaining_depth, phát hiện HIGH): nop-bai-phan-hoi.md BƯỚC 0 điểm 2 yêu
cầu xác nhận "G5_STATUS = LOCKED" là tiền đề bắt buộc của G9, nhưng
build_part8_gate_criteria()/write_g9_checkpoint() trước đây chỉ tính boolean
cho G2/G4 — không có nhánh nào cho G5 dù file đã đọc G5_checkpoint.json vào
`cps` từ trước. Một đề tài có CSDL CHƯA khóa (rủi ro thao túng dữ liệu sau khi
biết kết quả) vẫn nhận gói A10 đầy đủ không cảnh báo. Cùng khuôn test với
test_g9_ledger_gate_required.py (G2/G4), mở rộng cho G5.

Đồng thời hồi quy phát hiện MEDIUM cùng dimension: C4 (checklist báo cáo)
phải nhắc CHEERS 2022 khi G1 phát hiện specialist_modules=['economic'].
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
    key_path.write_text("pytest-g9-g5-key", encoding="utf-8")
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


def _write_g5_artifact_and_locked_text(study: str, d: Path) -> str:
    g5_content = "DATA MGMT — nội dung giả lập test (biên bản khóa CSDL)"
    (d / f"G5_A6_DATA_MGMT_{study}.md").write_text(g5_content, encoding="utf-8")
    return g5_content


def _write_ledger_approval(d: Path, gate_id: str, artifact_content: str) -> None:
    evidence_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
    timestamp_utc = "2026-07-23T00:00:00+00:00"
    signature = GC.sign_approval(gate_id, d.name, evidence_hash, timestamp_utc,
                                 reviewer_role="PI_PROJECT_OWNER", reviewer_ref="REF-TEST-001")
    assert signature
    record = {
        "approval_id": f"test-{gate_id}-001", "gate_id": gate_id,
        "reviewer_role": "PI_PROJECT_OWNER",
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


_CPS_G5_TEXT_LOCKED = {
    "G2": {"g2_irb_number": "IRB-2026-00123"},
    "G4": {"sap_signed_date": "2026-07-01"},
    "G5": {"db_lock_date": "2026-07-10"},
}
_GUARDRAIL = {"passed": True, "errors": [], "warnings": []}


class TestG5DbLockInGateCriteriaTable:
    def test_g5_text_only_not_sufficient(self):
        study = "PYTEST-G9-G5-T1"
        d = _study_dir(study)
        try:
            _write_g5_artifact_and_locked_text(study, d)
            md = G9.build_part8_gate_criteria(_CPS_G5_TEXT_LOCKED, n_authors=3, study=study)
            assert "B3. G5 (Khóa CSDL) = LOCKED" in md, (
                "Bảng Phần 8 phải có mục B3 cho G5 — trước đây hoàn toàn thiếu"
            )
            # Cả B1/B2/B3 đều chưa có ledger nên đều phải "⚠ CHỜ BÁC SĨ"
            assert md.count("⚠ CHỜ BÁC SĨ") >= 3
        finally:
            _rmtree_retry(d)

    def test_g5_with_matching_ledger_passes(self, tmp_path, monkeypatch):
        study = "PYTEST-G9-G5-T2"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            g5_content = _write_g5_artifact_and_locked_text(study, d)
            _write_ledger_approval(d, "G5", g5_content)
            md = G9.build_part8_gate_criteria(_CPS_G5_TEXT_LOCKED, n_authors=3, study=study)
            lines = [ln for ln in md.splitlines() if "B3." in ln or "Hiện tại: LOCKED (CSDL" in ln]
            assert any("✅" in ln for ln in lines) or "✅" in md
            assert "LOCKED (CSDL đã khóa thật)" in md
        finally:
            _rmtree_retry(d)


class TestG5DbLockInPendingChecklist:
    def test_pending_lists_g5_when_ledger_missing(self):
        study = "PYTEST-G9-G5-T3"
        d = _study_dir(study)
        try:
            _write_g5_artifact_and_locked_text(study, d)
            cp_path = G9.write_g9_checkpoint(
                study=study, out_dir=d, n_authors=3, target_journal="Test Journal",
                guardrail=_GUARDRAIL, md_path=d / "dummy.md", docx_path=None,
                cps=_CPS_G5_TEXT_LOCKED,
            )
            cp = json.loads(cp_path.read_text(encoding="utf-8"))
            pending_text = " | ".join(cp["pending"])
            assert "G5 (Khóa CSDL) chưa LOCKED" in pending_text
        finally:
            _rmtree_retry(d)

    def test_pending_clears_g5_when_ledger_present(self, tmp_path, monkeypatch):
        study = "PYTEST-G9-G5-T4"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            g5_content = _write_g5_artifact_and_locked_text(study, d)
            _write_ledger_approval(d, "G5", g5_content)
            cp_path = G9.write_g9_checkpoint(
                study=study, out_dir=d, n_authors=3, target_journal="Test Journal",
                guardrail=_GUARDRAIL, md_path=d / "dummy.md", docx_path=None,
                cps=_CPS_G5_TEXT_LOCKED,
            )
            cp = json.loads(cp_path.read_text(encoding="utf-8"))
            pending_text = " | ".join(cp["pending"])
            assert "G5 (Khóa CSDL) chưa LOCKED" not in pending_text
        finally:
            _rmtree_retry(d)


class TestC4ChecklistMentionsCheersForEconomicSpecialistModule:
    def test_c4_mentions_cheers_when_economic_specialist_module_present(self):
        study = "PYTEST-G9-G5-T5"
        d = _study_dir(study)
        try:
            cps = dict(_CPS_G5_TEXT_LOCKED)
            cps["G1"] = {"specialist_modules": ["economic"]}
            md = G9.build_part8_gate_criteria(cps, n_authors=3, study=study)
            assert "CHEERS 2022" in md
            assert "C4." in md
        finally:
            _rmtree_retry(d)

    def test_c4_no_cheers_mention_without_specialist_module(self):
        study = "PYTEST-G9-G5-T6"
        d = _study_dir(study)
        try:
            cps = dict(_CPS_G5_TEXT_LOCKED)
            cps["G1"] = {"specialist_modules": []}
            md = G9.build_part8_gate_criteria(cps, n_authors=3, study=study)
            assert "CHEERS 2022" not in md
        finally:
            _rmtree_retry(d)
