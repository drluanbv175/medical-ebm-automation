"""Kiểm thử đối kháng hợp đồng chất lượng G10-2026.1.

Toàn bộ fixture là synthetic, offline, không PII và không đại diện phê duyệt
người thật. Test chấm trực tiếp artifact hiện hành, không tin report lưu sẵn.
"""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import approve_gate as APPROVE  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g10_assemble as G10  # noqa: E402


def _complete_readiness(study: str) -> dict:
    payload = G10Q.build_readiness_template(study)
    payload["release"].update(
        {
            "purpose": "RESEARCH_DOSSIER",
            "package_version": "1.0.0",
            "target_system_or_recipient_ref": "REPOSITORY-REF-01",
            "target_requirements_checked": True,
            "prepared_at": "2026-07-29T00:00:00+00:00",
            "owner_ref": "PI-REF-01",
            "change_log_reviewed": True,
            "final_files_confirmed": True,
            "no_unresolved_critical_issues": True,
            "prepared_for_pi_review": True,
        }
    )
    for key in payload["cross_document_consistency"]:
        payload["cross_document_consistency"][key] = True
    for key in payload["privacy_and_permissions"]:
        payload["privacy_and_permissions"][key] = True
    payload["archive_and_reproducibility"].update(
        {
            "archive_location_ref": "ARCHIVE-REF-01",
            "retention_policy_ref": "RETENTION-POLICY-01",
            "software_environment_captured": True,
            "data_dictionary_included_or_not_applicable": True,
            "audit_trail_preserved": True,
            "responsible_owner_ref": "STEWARD-REF-01",
        }
    )
    return payload


def _write_ready_fixture(out_dir: Path, study: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for index in range(10):
        checkpoint = {
            "gate": f"G{index}",
            "study": study,
            "guardrail": {"passed": True},
        }
        if index == 2:
            checkpoint["g2_status"] = "LOCKED"
        if index == 4:
            checkpoint["g4_status"] = "LOCKED"
        quality_status = {
            0: "PASS_G0_CONFIRMED",
            1: "PASS_G1_CONFIRMED",
            3: "PASS_G3_CONFIRMED",
            8: "PASS_G8_REVIEW_RECORDED",
        }.get(index)
        if quality_status:
            checkpoint["quality_contract_version"] = f"G{index}-2026.1"
            checkpoint["quality_gate"] = {"status": quality_status}
        if index == 9:
            checkpoint["quality_contract_version"] = "G9-2026.2"
        (out_dir / f"G{index}_checkpoint.json").write_text(
            json.dumps(checkpoint, ensure_ascii=False),
            encoding="utf-8", newline="\n"
        )

    g10_checkpoint = {
        "gate": "G10",
        "study": study,
        "quality_contract_version": G10Q.QUALITY_CONTRACT_VERSION,
        "guardrail": {"passed": True},
        "study_spec": {
            "scientific_content_complete": True,
            "protocol_content_complete": True,
            "missing_requirement_ids": [],
            "semantic_error_codes": [],
        },
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    (out_dir / G10Q.CHECKPOINT_JSON).write_text(
        json.dumps(g10_checkpoint, ensure_ascii=False),
        encoding="utf-8", newline="\n"
    )
    (out_dir / G10Q.READINESS_JSON).write_text(
        json.dumps(_complete_readiness(study), ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
    )

    text_files = {
        f"DE_CUONG_THONG_NHAT_{study}.md": "Final protocol. Cần bác sĩ kiểm chứng.\n",
        f"GOI_QUYET_DINH_{study}.md": "Final decision package. Cần bác sĩ kiểm chứng.\n",
        f"G8_A9_PRESUBMISSION_{study}.md": "Independent review final.\n",
        "G9_PUBLICATION_READINESS.json": "{}\n",
        "G9_QUALITY_REPORT.json": "{}\n",
        f"A12_CITATION_VERIFICATION_{study}.md": "Citation verification final.\n",
        "A12_RETRACTION_RECEIPT.json": "{}\n",
        "A12_METADATA_RECEIPT.json": "{}\n",
    }
    for name, content in text_files.items():
        (out_dir / name).write_text(content, encoding="utf-8", newline="\n")
    with zipfile.ZipFile(
        out_dir / f"DE_CUONG_THONG_NHAT_{study}.docx", "w"
    ) as archive:
        archive.writestr(
            "word/document.xml",
            "<w:document><w:body><w:p>Final protocol</w:p></w:body></w:document>",
        )
    (out_dir / f"STUDY_SPEC_{study}.json").write_text(
        json.dumps({"complete": True}), encoding="utf-8", newline="\n"
    )


def _patch_upstream(monkeypatch, approval_state: dict[str, bool]) -> None:
    monkeypatch.setattr(GC, "g2_quality_contract_satisfied", lambda *_a, **_k: True)
    # SỬA 2026-07-30 (G10-01): g10_quality_gate.py nay chấm G4 qua
    # g4_quality_contract_satisfied() thay vì đọc g4_status text (đã lỗi thời) —
    # fixture "ready" ở đây không dựng SAP/ledger G4 đầy đủ nên phải mock đúng
    # hàm mới, nếu không hàm THẬT sẽ chạy và trả False.
    monkeypatch.setattr(GC, "g4_quality_contract_satisfied", lambda *_a, **_k: True)
    monkeypatch.setattr(GC, "g5_quality_contract_satisfied", lambda *_a, **_k: True)
    monkeypatch.setattr(GC, "g9_quality_contract_satisfied", lambda *_a, **_k: True)
    monkeypatch.setattr(
        GC,
        "ledger_approved",
        lambda gate, *_a, **_k: (
            approval_state.get("g10", False)
            if gate == "G10"
            else gate in {"G2", "G4", "G8"}
        ),
    )
    monkeypatch.setattr(G10, "citation_verification_ok", lambda *_a, **_k: (True, ""))


def _criterion(report: dict, criterion_id: str) -> dict:
    return next(
        row for row in report["automatic_criteria"] if row["id"] == criterion_id
    )


def test_template_is_fail_closed_and_contains_no_contact_pii(tmp_path):
    path = G10Q.ensure_readiness("SYNTH-G10-TEMPLATE", tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == G10Q.STATUS_DRAFT
    assert payload["release"]["prepared_for_pi_review"] is False
    assert payload["pi_release_approval"]["completed_by_system"] is False
    assert "@" not in path.read_text(encoding="utf-8")


def test_ready_then_locked_only_after_pi_approval(tmp_path, monkeypatch):
    study = "SYNTH-G10-READY"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)

    ready = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert ready["status"] == G10Q.STATUS_READY
    checkpoint = json.loads((tmp_path / G10Q.CHECKPOINT_JSON).read_text(encoding="utf-8"))
    assert checkpoint["release_manifest"]["algorithm"] == "SHA-256"
    assert checkpoint["quality_gate"]["human_approval_valid"] is False

    approval["g10"] = True
    locked = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=False)
    assert locked["status"] == G10Q.STATUS_LOCKED
    assert locked["external_submission_state"] == "NOT_PERFORMED_OR_PROVEN_BY_G10"


def test_file_change_after_lock_is_blocked(tmp_path, monkeypatch):
    study = "SYNTH-G10-TAMPER"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    assert (
        G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)["status"]
        == G10Q.STATUS_READY
    )
    approval["g10"] = True
    (tmp_path / f"GOI_QUYET_DINH_{study}.md").write_text(
        "Changed after approval.\n", encoding="utf-8", newline="\n"
    )
    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=False)
    assert report["status"] == G10Q.STATUS_BLOCKED
    assert _criterion(report, "G10-AUTO-10")["status"] == "BLOCK"


def test_upstream_revocation_after_lock_is_blocked(tmp_path, monkeypatch):
    study = "SYNTH-G10-UPSTREAM"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    assert (
        G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)["status"]
        == G10Q.STATUS_READY
    )
    approval["g10"] = True
    monkeypatch.setattr(GC, "g9_quality_contract_satisfied", lambda *_a, **_k: False)
    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=False)
    assert report["status"] == G10Q.STATUS_BLOCKED
    assert "G9=False" in _criterion(report, "G10-AUTO-04")["evidence"]


def test_g2_schema_without_irb_ledger_cannot_pass_g10(tmp_path, monkeypatch):
    study = "SYNTH-G10-G2-NO-LEDGER"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    monkeypatch.setattr(
        GC,
        "ledger_approved",
        lambda gate, *_a, **_k: gate in {"G4", "G8"},
    )

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_DRAFT
    assert "G2=False" in _criterion(report, "G10-AUTO-04")["evidence"]


def test_legacy_g1_quality_contract_cannot_be_silently_grandfathered(
    tmp_path, monkeypatch
):
    study = "SYNTH-G10-LEGACY-G1"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    g1_path = tmp_path / "G1_checkpoint.json"
    g1 = json.loads(g1_path.read_text(encoding="utf-8"))
    g1.pop("quality_contract_version", None)
    g1.pop("quality_gate", None)
    g1_path.write_text(json.dumps(g1, ensure_ascii=False), encoding="utf-8", newline="\n")

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_DRAFT
    assert "G1" in _criterion(report, "G10-AUTO-02B")["evidence"]


def test_contact_pii_in_readiness_is_blocked(tmp_path, monkeypatch):
    study = "SYNTH-G10-PII"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    readiness_path = tmp_path / G10Q.READINESS_JSON
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    readiness["release"]["owner_ref"] = "doctor@example.org"
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False), encoding="utf-8", newline="\n")

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_BLOCKED
    assert _criterion(report, "G10-AUTO-08")["status"] == "BLOCK"


def test_contact_pii_in_release_document_is_blocked(tmp_path, monkeypatch):
    study = "SYNTH-G10-DOC-PII"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    (tmp_path / f"GOI_QUYET_DINH_{study}.md").write_text(
        "Contact: investigator@example.org\n", encoding="utf-8", newline="\n"
    )

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_BLOCKED
    assert _criterion(report, "G10-AUTO-09")["status"] == "BLOCK"


def test_path_traversal_and_false_submission_claim_are_blocked(tmp_path, monkeypatch):
    study = "SYNTH-G10-PATH"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    readiness_path = tmp_path / G10Q.READINESS_JSON
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    readiness["additional_artifacts"] = ["../outside.txt"]
    readiness["automation_limits"]["external_submission_performed_by_g10"] = True
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False), encoding="utf-8", newline="\n")

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_BLOCKED
    assert _criterion(report, "G10-AUTO-07")["status"] == "BLOCK"
    assert _criterion(report, "G10-AUTO-09")["status"] == "BLOCK"


def test_placeholder_keeps_external_package_in_draft(tmp_path, monkeypatch):
    study = "SYNTH-G10-PLACEHOLDER"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    readiness_path = tmp_path / G10Q.READINESS_JSON
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    readiness["release"]["purpose"] = "ETHICS_SUBMISSION"
    readiness_path.write_text(json.dumps(readiness, ensure_ascii=False), encoding="utf-8", newline="\n")
    (tmp_path / f"DE_CUONG_THONG_NHAT_{study}.md").write_text(
        "Protocol still has [CẦN BỔ SUNG].\n", encoding="utf-8", newline="\n"
    )

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_DRAFT
    assert _criterion(report, "G10-AUTO-09")["status"] == "REVIEW"


def test_corrupt_docx_is_blocked(tmp_path, monkeypatch):
    study = "SYNTH-G10-CORRUPT-DOCX"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    (tmp_path / f"DE_CUONG_THONG_NHAT_{study}.docx").write_bytes(b"not-a-docx")

    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_BLOCKED
    assert _criterion(report, "G10-AUTO-09")["status"] == "BLOCK"


def test_missing_human_readiness_stays_draft(tmp_path, monkeypatch):
    study = "SYNTH-G10-DRAFT"
    _write_ready_fixture(tmp_path, study)
    approval = {"g10": False}
    _patch_upstream(monkeypatch, approval)
    (tmp_path / G10Q.READINESS_JSON).write_text(
        json.dumps(G10Q.build_readiness_template(study), ensure_ascii=False),
        encoding="utf-8", newline="\n",
    )
    report = G10Q.evaluate_study(study, tmp_path, repo_root=tmp_path, write=True)
    assert report["status"] == G10Q.STATUS_DRAFT
    assert _criterion(report, "G10-HUMAN-01")["status"] == "REVIEW"


def test_gate_contract_requires_pi_for_g10():
    assert GC.reviewer_role_satisfies_gate("G10", "PI")
    assert GC.reviewer_role_satisfies_gate("G10", "PRINCIPAL_INVESTIGATOR")
    assert not GC.reviewer_role_satisfies_gate("G10", "PEER_REVIEWER")
    assert not GC.reviewer_role_satisfies_gate("G10", "BIOSTATISTICIAN")


def test_approve_gate_rejects_non_checkpoint_artifact_for_g10(monkeypatch):
    study = "PYTEST-G10-WRONG-ARTIFACT"
    out_dir = REPO_ROOT / "exports" / study
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    try:
        wrong = out_dir / "G10_QUALITY_REPORT.md"
        wrong.write_text("Synthetic report.", encoding="utf-8", newline="\n")
        argv = sys.argv
        sys.argv = [
            "approve_gate.py",
            "--study",
            study,
            "--gate",
            "G10",
            "--artifact",
            str(wrong),
            "--reviewer-role",
            "PI",
            "--reviewer-ref",
            "PYTEST-PI",
        ]
        try:
            assert APPROVE.main() == 1
        finally:
            sys.argv = argv
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def test_approve_gate_signs_ready_g10_checkpoint_only_in_synthetic_test(
    tmp_path, monkeypatch
):
    study = "PYTEST-G10-APPROVE-READY"
    out_dir = REPO_ROOT / "exports" / study
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g10-quality-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    checkpoint_path = out_dir / G10Q.CHECKPOINT_JSON
    checkpoint_path.write_text(
        json.dumps(
            {
                "gate": "G10",
                "study": study,
                "quality_contract_version": G10Q.QUALITY_CONTRACT_VERSION,
                "gate_status": "BLOCKED — synthetic fixture",
                "needs_input": {"reason_code": GC.REASON_MISSING_RELEASE_APPROVAL},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8", newline="\n"
    )
    monkeypatch.setattr(
        APPROVE.G10Q,
        "evaluate_study",
        lambda *_a, **_k: {
            "status": G10Q.STATUS_READY,
            "automatic_criteria": [],
        },
    )
    argv = sys.argv
    sys.argv = [
        "approve_gate.py",
        "--study",
        study,
        "--gate",
        "G10",
        "--artifact",
        str(checkpoint_path),
        "--reviewer-role",
        "PI",
        "--reviewer-ref",
        "PYTEST-PI",
    ]
    try:
        assert APPROVE.main() == 0
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        assert "needs_input" not in checkpoint
        assert checkpoint["gate_status"] == G10Q.STATUS_READY
        assert GC.ledger_approved(
            "G10", study, checkpoint_path, repo_root=REPO_ROOT
        )
    finally:
        sys.argv = argv
        shutil.rmtree(out_dir, ignore_errors=True)
