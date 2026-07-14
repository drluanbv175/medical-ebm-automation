"""Hồi quy: run_g10_assemble.py main() — cổng SẴN SÀNG NỘP BÀI cuối cùng — phải
xác minh phê duyệt G8 (bình duyệt độc lập) VÀ G9 (liêm chính tác giả) THẬT trong
approval_ledger.json, không chỉ xuất tài liệu rồi báo "✅ Xong" vô điều kiện.

Trước 2026-07-14, main() đã có chốt G9 (vá 2026-07-12) nhưng KHÔNG có test tự động
nào phủ nhánh CLI này (chỉ được xác minh thủ công một lần, theo lịch sử phiên) —
và hoàn toàn CHƯA có chốt G8 nào (bình duyệt không có cổng cứng). File này phủ cả
hai, dùng CHUNG helper ký ledger thật với tests/test_g9_ledger_gate_required.py.
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
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g10-submission-key", encoding="utf-8")
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


def _write_ledger_approval(d: Path, gate_id: str, artifact_content: str, reviewer_role: str) -> None:
    evidence_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
    timestamp_utc = "2026-07-14T00:00:00+00:00"
    signature = GC.sign_approval(gate_id, d.name, evidence_hash, timestamp_utc)
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


def _run_main(study: str, extra_args: list[str] | None = None) -> int:
    argv = sys.argv
    sys.argv = ["run_g10_assemble.py", "--study", study, "--no-validate", *(extra_args or [])]
    try:
        return G10.main()
    finally:
        sys.argv = argv


class TestG8SubmissionGate:
    def test_blocks_when_g8_not_approved_even_if_g9_is(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-T1"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            # Chỉ ký G9, CỐ Ý bỏ trống G8 — phải vẫn bị chặn vì thiếu G8.
            g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
            _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_blocks_when_g8_approved_by_wrong_role(self, tmp_path, monkeypatch):
        """G8 CÓ bản ghi APPROVED nhưng reviewer_role không thuộc nhóm phản biện
        (vd tự ký bằng vai PI) — phải vẫn bị chặn (fail-closed theo role)."""
        study = "PYTEST-G10SUB-T2"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
            _write_ledger_approval(d, "G8", g8_content, "PI_PROJECT_OWNER")  # sai role cố ý
            rc = _run_main(study)
            assert rc == GC.EXIT_BLOCKED
        finally:
            _rmtree_retry(d)

    def test_passes_when_g8_and_g9_both_approved_with_correct_roles(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-T3"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            g8_content = "PRESUBMISSION REVIEW — nội dung giả lập test"
            g9_content = "AUTHOR INTEGRITY — nội dung giả lập test"
            (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8_content, encoding="utf-8")
            (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9_content, encoding="utf-8")
            _write_ledger_approval(d, "G8", g8_content, "PHAN_BIEN_DOC_LAP")
            _write_ledger_approval(d, "G9", g9_content, "PI_PROJECT_OWNER")
            rc = _run_main(study)
            assert rc == 0
        finally:
            _rmtree_retry(d)

    def test_override_flag_still_produces_draft_when_g8_unsigned(self, tmp_path, monkeypatch):
        """--i-know-g8-not-signed cho phép XEM TRƯỚC bản nháp dù G8 chưa ký —
        nhưng KHÔNG được đồng thời bỏ qua chốt G9 (mỗi cờ chỉ thay được đúng 1 cổng)."""
        study = "PYTEST-G10SUB-T4"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            rc = _run_main(study, ["--i-know-g8-not-signed"])
            # G9 vẫn chưa ký -> vẫn phải bị chặn (chỉ G8 được bỏ qua bằng cờ).
            assert rc == GC.EXIT_BLOCKED
            # Nhưng tài liệu NHÁP vẫn phải được xuất ra (không phải lỗi CRASH).
            assert (d / f"DE_CUONG_THONG_NHAT_{study}.md").exists(), (
                "Override flag phải vẫn cho xuất bản nháp để bác sĩ xem trước")
        finally:
            _rmtree_retry(d)

    def test_override_both_flags_produces_draft_with_exit_blocked(self, tmp_path, monkeypatch):
        study = "PYTEST-G10SUB-T5"
        d = _study_dir(study)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_cross_sectional_fixture(d)
            rc = _run_main(study, ["--i-know-g8-not-signed", "--i-know-g9-not-signed"])
            assert rc == 0
        finally:
            _rmtree_retry(d)
