"""
Tests cho ApprovalLedger — Phase 3 Offline Controlled-System.
Không có API call, không PII, hoàn toàn deterministic.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from runtime.approval_ledger import ApprovalLedger
from runtime.schemas import ApprovalDecisionEnum

_REPO_ROOT = Path(__file__).resolve().parents[1]


class TestApprovalLedgerBlock:
    """TC-04: Agent-created approval bị block."""

    def test_agent_created_approval_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="PI",
            reviewer_ref="REF-PI-001",
            scope="Ethics approval scope",
            evidence_content="Ethics committee letter",
        )
        # Ghi đè flag _created_by_agent
        record._created_by_agent = True
        success, reason = ledger.add_approval(record, created_by_agent=True)
        assert not success
        assert reason == "AGENT_CREATED_APPROVAL_BLOCKED"
        assert ledger.count() == 0

    def test_explicit_created_by_agent_flag_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G4",
            reviewer_role="PI",
            reviewer_ref="REF-PI-002",
            scope="SAP lock scope",
            evidence_content="SAP signed document",
        )
        # Không cần ghi đè record — truyền qua param
        success, reason = ledger.add_approval(record, created_by_agent=True)
        assert not success
        assert reason == "AGENT_CREATED_APPROVAL_BLOCKED"

    def test_creator_reviewer_same_agent_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="GATE_A",
            reviewer_role="GUARDRAIL_REVIEWER",
            reviewer_ref="REVIEWER-AGENT-TRACE",
            scope="Clinical output packet review",
            evidence_content="Draft clinical packet hash source",
            artifact_creator_agent="tham-dinh-dau-ra",
            reviewer_agent="tham-dinh-dau-ra",
        )
        success, reason = ledger.add_approval(record)
        assert not success
        assert reason == "SELF_REVIEW_BLOCKED"
        assert ledger.count() == 0

    def test_creator_reviewer_different_agents_allowed(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="GATE_A",
            reviewer_role="GUARDRAIL_REVIEWER",
            reviewer_ref="REVIEWER-AGENT-TRACE",
            scope="Clinical output packet review",
            evidence_content="Draft clinical packet hash source",
            artifact_creator_agent="dieu-phoi-lam-sang",
            reviewer_agent="tham-dinh-dau-ra",
        )
        success, reason = ledger.add_approval(record)
        assert success
        assert reason == "ADDED"

    def test_self_review_audit_detects_imported_legacy_violation(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="GATE_B",
            reviewer_role="LEGACY_IMPORT_REVIEWER",
            reviewer_ref="LEGACY-TRACE",
            scope="Imported legacy approval trace",
            evidence_content="Legacy approval content",
            artifact_creator_agent="tham-dinh-dau-ra",
            reviewer_agent="tham-dinh-dau-ra",
        )
        ledger._records.append(record)
        assert ledger.has_self_review_violations()
        assert ledger.self_review_violations() == [record]


class TestApprovalLedgerValidApproval:
    """Human approval hợp lệ được add."""

    def test_valid_human_approval_added(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB_CHAIR",
            reviewer_ref="IRB-QY175-2026-01",
            scope="Full ethics approval QY175",
            evidence_content="Letter ref IRB-QY175-2026-01",
        )
        success, reason = ledger.add_approval(record)
        assert success
        assert reason == "ADDED"
        assert ledger.count() == 1

    def test_has_ethics_approval_after_add(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB_CHAIR",
            reviewer_ref="IRB-001",
            scope="Ethics",
            evidence_content="Ethics doc",
        )
        ledger.add_approval(record)
        assert ledger.has_ethics_approval()

    def test_no_ethics_approval_initially(self):
        ledger = ApprovalLedger()
        assert not ledger.has_ethics_approval()

    def test_no_sap_lock_initially(self):
        ledger = ApprovalLedger()
        assert not ledger.has_sap_lock()

    def test_no_pi_signoff_initially(self):
        ledger = ApprovalLedger()
        assert not ledger.has_pi_signoff()


class TestApprovalLedgerStakeholderRoles:
    """Cổng G2/G4/G9 cần đúng stakeholder, không chỉ có record APPROVED."""

    def _add(self, ledger: ApprovalLedger, gate_id: str, role: str):
        record = ApprovalLedger.make_human_approval(
            gate_id=gate_id,
            reviewer_role=role,
            reviewer_ref=f"REF-{gate_id}-{role}",
            scope=f"Stakeholder test {gate_id}",
            evidence_content=f"Evidence {gate_id} {role}",
        )
        ok, reason = ledger.add_approval(record)
        assert ok, reason
        return record

    def test_g2_requires_irb_or_ethics_role(self):
        ledger = ApprovalLedger()
        self._add(ledger, "G2", "PI_PROJECT_OWNER")
        assert not ledger.has_ethics_approval()
        status = ledger.stakeholder_gate_status("G2")
        assert status["satisfied"] is False
        assert status["required_stakeholder"] == "IRB"

        self._add(ledger, "G2", "IRB_ETHICS_COMMITTEE")
        assert ledger.has_ethics_approval()

    def test_g4_requires_statistician_or_pi_role(self):
        """Vá 2026-07-15: G4 chấp nhận CẢ thống kê viên LẪN PI tự ký (khớp
        gate_contract.py, doctrine thiet-ke-nghien-cuu.md) — IRB vẫn KHÔNG thỏa."""
        ledger = ApprovalLedger()
        self._add(ledger, "G4", "IRB_ETHICS_COMMITTEE")
        assert not ledger.has_sap_lock()

        self._add(ledger, "G4", "PI")
        assert ledger.has_sap_lock()

    def test_g4_accepts_statistician_role_alone_too(self):
        ledger = ApprovalLedger()
        self._add(ledger, "G4", "BIOSTATISTICIAN")
        assert ledger.has_sap_lock()

    def test_g9_requires_pi_role(self):
        ledger = ApprovalLedger()
        self._add(ledger, "G9", "INDEPENDENT_PEER_REVIEWER")
        assert not ledger.has_pi_signoff()

        self._add(ledger, "G9", "PRINCIPAL_INVESTIGATOR")
        assert ledger.has_pi_signoff()

    def test_synthetic_stakeholder_approval_does_not_satisfy_gate(self):
        ledger = ApprovalLedger()
        syn = ApprovalLedger.make_synthetic_approval(
            gate_id="G2",
            scope="Synthetic IRB fixture",
            evidence_content="Synthetic ethics content",
            reviewer_role="IRB_ETHICS_COMMITTEE",
            reviewer_ref="IRB-SYNTHETIC",
        )
        ledger._records.append(syn)
        assert ledger.check_has_approval("G2") is syn
        assert not ledger.has_ethics_approval()


class TestApprovalLedgerDuplicate:
    """Duplicate approval_id bị block."""

    def test_duplicate_approval_id_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB",
            reviewer_ref="IRB-DUP-TEST",
            scope="Test",
            evidence_content="Content for duplicate test",
        )
        ledger.add_approval(record)
        success2, reason2 = ledger.add_approval(record)
        assert not success2
        assert "DUPLICATE_APPROVAL_ID" in reason2


class TestApprovalLedgerMissingEvidence:
    """Missing evidence_hash bị block."""

    def test_missing_evidence_hash_blocked(self):
        from runtime.schemas import ApprovalRecord
        record = ApprovalRecord(
            approval_id="test-id-001",
            gate_id="G2",
            reviewer_role="IRB",
            reviewer_identity_reference="IRB-TEST",
            decision=ApprovalDecisionEnum.APPROVED,
            scope="Test",
            evidence_hash="",  # rỗng
            timestamp_utc="2026-06-21T00:00:00+00:00",
            supersedes=None,
            _created_by_agent=False,
        )
        ledger = ApprovalLedger()
        success, reason = ledger.add_approval(record)
        assert not success
        assert reason == "MISSING_EVIDENCE_HASH"


class TestApprovalLedgerExport:
    """Export JSON không có PII."""

    def test_export_json_no_pii(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G9",
            reviewer_role="PI",
            reviewer_ref="PI-SIGN-001",
            scope="Final PI sign-off",
            evidence_content="PI declaration document",
        )
        ledger.add_approval(record)
        json_str = ledger.export_json()
        # Không có _created_by_agent trong export
        assert "_created_by_agent" not in json_str
        assert "G9" in json_str

    def test_evidence_hash_verify(self):
        ledger = ApprovalLedger()
        content = "Ethics committee letter for QY175 study, ref IRB-001"
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB",
            reviewer_ref="IRB-VERIFY-TEST",
            scope="Verify test",
            evidence_content=content,
        )
        ledger.add_approval(record)
        assert ledger.verify_evidence_hash(record, content)
        assert not ledger.verify_evidence_hash(record, "tampered content")


class TestApprovalLedgerPersistence:
    """BL-06: to_file()/from_file() — ledger phải SỐNG qua nhiều lần chạy CLI.

    Đây là cơ chế cốt lõi của BL-06 (ràng buộc mật mã qua các tiến trình riêng);
    trước 2026-07-09 hoàn toàn KHÔNG có test — commit chỉ chứng minh 'không vỡ',
    không chứng minh các hàm này CHẠY ĐÚNG.
    """

    def _one_human_approval(self):
        return ApprovalLedger.make_human_approval(
            gate_id="G4",
            reviewer_role="Chủ nhiệm đề tài",
            reviewer_ref="PI-BL06-01",
            scope="Khóa SAP",
            evidence_content="Nội dung SAP đã ký — tiếng Việt có dấu",
        )

    def test_to_file_from_file_roundtrip(self, tmp_path):
        ledger = ApprovalLedger()
        rec = self._one_human_approval()
        ledger.add_approval(rec)
        p = tmp_path / "approval_ledger.json"
        ledger.to_file(p)

        loaded = ApprovalLedger.from_file(p)
        assert loaded.count() == 1
        r = loaded.get_all_approvals()[0]
        assert r.gate_id == "G4"
        assert r.evidence_hash == rec.evidence_hash
        assert r.decision == ApprovalDecisionEnum.APPROVED
        assert r.approval_id == rec.approval_id

    def test_from_file_missing_returns_empty_no_raise(self, tmp_path):
        loaded = ApprovalLedger.from_file(tmp_path / "khong-ton-tai.json")
        assert loaded.count() == 0  # trạng thái HỢP LỆ (đề tài chưa từng duyệt), không raise

    def test_from_file_corrupt_returns_empty_no_raise(self, tmp_path):
        p = tmp_path / "approval_ledger.json"
        p.write_text("{ đây không phải JSON hợp lệ", encoding="utf-8", newline="\n")
        loaded = ApprovalLedger.from_file(p)
        assert loaded.count() == 0  # 1 dòng hỏng KHÔNG được làm sập cả ledger

    def test_from_file_forces_not_agent_created(self, tmp_path):
        ledger = ApprovalLedger()
        ledger.add_approval(self._one_human_approval())
        p = tmp_path / "approval_ledger.json"
        ledger.to_file(p)
        loaded = ApprovalLedger.from_file(p)
        # Nạp lại KHÔNG cho phép giả mạo "do agent tạo" — mọi record _created_by_agent=False
        assert all(not r._created_by_agent for r in loaded.get_all_approvals())

    def test_roundtrip_preserves_synthetic_flag(self, tmp_path):
        # QUAN TRỌNG: _ledger_approved lọc `not is_synthetic`. Nếu cờ này MẤT khi nạp
        # lại (mặc định False), một approval MÔ PHỎNG sẽ bị nhầm thành phê duyệt THẬT
        # → thủng cổng. Test khóa lại: cờ synthetic phải sống qua to_file/from_file.
        ledger = ApprovalLedger()
        syn = ApprovalLedger.make_synthetic_approval(
            gate_id="G4", scope="synthetic", evidence_content="fixture")
        ledger._records.append(syn)
        p = tmp_path / "approval_ledger.json"
        ledger.to_file(p)
        loaded = ApprovalLedger.from_file(p)
        assert loaded.count() == 1
        assert loaded.get_all_approvals()[0].is_synthetic is True

    def test_to_file_atomic_leaves_no_tmp(self, tmp_path):
        ledger = ApprovalLedger()
        ledger.add_approval(self._one_human_approval())
        p = tmp_path / "approval_ledger.json"
        ledger.to_file(p)
        assert p.exists()
        assert not (tmp_path / "approval_ledger.json.tmp").exists()  # ghi nguyên tử

    def test_to_file_creates_parent_dirs(self, tmp_path):
        ledger = ApprovalLedger()
        ledger.add_approval(self._one_human_approval())
        p = tmp_path / "sub" / "dir" / "approval_ledger.json"
        ledger.to_file(p)
        assert p.exists()


class TestApproveGateEndToEnd:
    """BL-06 end-to-end: tools/approve_gate.py phải ghi evidence_hash KHỚP đúng cái
    mà _ledger_approved (ở run_g6/run_stats_analysis) sẽ kiểm — tức
    sha256(read_bytes() của artifact). Đây là hợp đồng khóa 2 đầu approve↔check;
    nếu lệch (vd text-vs-bytes), bác sĩ duyệt thật mà cổng vẫn báo 'chưa duyệt'."""

    _STUDY = "__bl06_selftest_delete_me__"

    @pytest.fixture()
    def study_dir(self):
        d = _REPO_ROOT / "exports" / self._STUDY
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        try:
            yield d
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(_REPO_ROOT / "tools" / "approve_gate.py"), *extra],
            cwd=str(_REPO_ROOT), capture_output=True, text=True,
        )

    def test_approve_gate_hash_matches_ledger_approved_predicate(self, study_dir):
        artifact = study_dir / "G4_A5_SAP_FINAL.md"
        # Nội dung tiếng Việt có dấu (đa byte UTF-8) — bẫy điển hình của text-vs-bytes.
        artifact.write_text("# SAP đã khóa\nƯớc lượng hiệu quả HR=0,74 (khoảng tin cậy).",
                            encoding="utf-8", newline="\n")
        res = self._run("--study", self._STUDY, "--gate", "G4",
                        "--artifact", str(artifact),
                        "--reviewer-role", "METHODS_STATISTICS_REVIEWER",
                        "--reviewer-ref", "STAT-01")
        assert res.returncode == 0, f"stderr={res.stderr}\nstdout={res.stdout}"

        ledger_file = study_dir / "approval_ledger.json"
        assert ledger_file.exists()
        records = json.loads(ledger_file.read_text(encoding="utf-8"))
        assert len(records) == 1
        r = records[0]
        assert r["gate_id"] == "G4"
        assert r["decision"] == "APPROVED"
        assert r.get("is_synthetic") is False
        # ★ Hợp đồng cốt lõi: hash đã ghi == sha256(bytes artifact) — ĐÚNG cái _ledger_approved kiểm.
        expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
        assert r["evidence_hash"] == expected

    def test_approve_gate_missing_artifact_exits_nonzero(self, study_dir):
        res = self._run("--study", self._STUDY, "--gate", "G4",
                        "--artifact", str(study_dir / "khong-ton-tai.md"),
                        "--reviewer-role", "PI", "--reviewer-ref", "PI-01")
        assert res.returncode != 0

    def test_approve_gate_rejects_wrong_reviewer_role_for_g4(self, study_dir):
        """G4 nới chấp nhận PI từ 2026-07-14 (khớp doctrine "Chủ nhiệm đề tài" tự
        ký khi không có thống kê viên riêng — xem thiet-ke-nghien-cuu.md) — vai
        KHÔNG liên quan tới G4 (vd IRB) vẫn phải bị từ chối."""
        artifact = study_dir / "G4_A5_SAP_FINAL.md"
        artifact.write_text("# SAP đã khóa\nNội dung test.", encoding="utf-8", newline="\n")
        res = self._run("--study", self._STUDY, "--gate", "G4",
                        "--artifact", str(artifact),
                        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01")
        assert res.returncode != 0
        assert "METHODS_STATISTICS_REVIEWER" in res.stdout

    def test_approve_gate_accepts_pi_role_for_g4(self, study_dir):
        """Vá 2026-07-14: G4 giờ chấp nhận CẢ PI, không chỉ STATISTICIAN — trước
        đó bác sĩ tự ký khóa SAP đúng theo hướng dẫn doctrine vẫn bị từ chối vì
        code fail-closed chỉ chấp nhận thống kê viên (lệch code/doctrine thật)."""
        artifact = study_dir / "G4_A5_SAP_FINAL.md"
        artifact.write_text("# SAP đã khóa\nNội dung test.", encoding="utf-8", newline="\n")
        res = self._run("--study", self._STUDY, "--gate", "G4",
                        "--artifact", str(artifact),
                        "--reviewer-role", "PI", "--reviewer-ref", "PI-01")
        assert res.returncode == 0, f"stderr={res.stderr}\nstdout={res.stdout}"

    def test_approve_gate_g5_rejects_arbitrary_artifact(self, study_dir):
        artifact = study_dir / "tu-khai-g5.md"
        artifact.write_text("Tự khai đã khóa.", encoding="utf-8", newline="\n")
        res = self._run(
            "--study",
            self._STUDY,
            "--gate",
            "G5",
            "--artifact",
            str(artifact),
            "--reviewer-role",
            "DATA_MANAGER",
            "--reviewer-ref",
            "DM-01",
        )
        assert res.returncode != 0
        assert "artifact phải là G5_checkpoint.json" in res.stdout

    def test_approve_gate_g5_rejects_checkpoint_without_quality_chain(
        self,
        study_dir,
    ):
        artifact = study_dir / "G5_checkpoint.json"
        artifact.write_text(
            json.dumps({"g5_status": "LOCKED"}),
            encoding="utf-8",
        )
        res = self._run(
            "--study",
            self._STUDY,
            "--gate",
            "G5",
            "--artifact",
            str(artifact),
            "--reviewer-role",
            "DATA_MANAGER",
            "--reviewer-ref",
            "DM-01",
        )
        assert res.returncode != 0
        assert "hồ sơ chưa ở trạng thái READY_FOR_G5_APPROVAL" in res.stdout
        assert not (study_dir / "approval_ledger.json").exists()

    def test_approve_gate_missing_study_dir_exits_nonzero(self, tmp_path):
        # Đề tài chưa có thư mục exports/<study> → từ chối (không tự tạo phê duyệt khống).
        artifact = tmp_path / "art.md"
        artifact.write_text("noi dung", encoding="utf-8", newline="\n")
        res = self._run("--study", "__khong_ton_tai_9z9z__", "--gate", "G4",
                        "--artifact", str(artifact),
                        "--reviewer-role", "PI", "--reviewer-ref", "PI-01")
        assert res.returncode != 0
