"""Kiểm thử đối kháng cho hợp đồng liêm chính công bố G9-2026.1."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as APPROVE  # noqa: E402
import g9_quality_gate as G9Q  # noqa: E402
import run_g9_auto as G9  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    append_signed_approval,
    configure_test_signing_key,
    prepare_locked_g5_study,
)


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _complete_readiness(study: str, n_authors: int = 2) -> dict:
    value = G9Q.build_readiness_template(study, n_authors, "Journal of Test Medicine")
    now = datetime.now(timezone.utc).isoformat()
    for index, author in enumerate(value["authors"], start=1):
        author.update(
            {
                "credit_roles": (
                    ["Conceptualization", "Writing - review & editing"]
                    if index == 1
                    else ["Investigation", "Writing - review & editing"]
                ),
                "coi_form_completed": True,
                "coi_evidence_ref": f"COI-FORM-{index:02d}",
                "data_access_confirmed": True,
                "attested_at": now,
                "attestation_evidence_ref": f"AUTHOR-ATTEST-{index:02d}",
            }
        )
        for key in author["icmje_criteria"]:
            author["icmje_criteria"][key] = True
    value["authorship"].update(
        {
            "order_confirmed": True,
            "credit_mapping_confirmed": True,
            "acknowledgements_permission_confirmed": True,
            "guarantor_author_ref": "AUTHOR-01",
            "dispute_absent_or_resolved": True,
        }
    )
    value["coi_funding"].update(
        {
            "all_author_forms_complete": True,
            "collective_coi_statement": "No competing interests declared.",
            "funding_statement": "No external funding.",
            "sponsor_role_statement": "No sponsor.",
            "sponsor_no_publication_restriction_confirmed": True,
        }
    )
    value["ai_disclosure"].update(
        {
            "ai_used": False,
            "human_verification_confirmed": True,
            "sensitive_or_confidential_data_uploaded": False,
            "ai_not_author_confirmed": True,
            "manuscript_statement_final": True,
            "cover_letter_statement_final": True,
            "confirmed_at": now,
        }
    )
    value["data_availability"].update(
        {
            "decision": "OPEN",
            "statement_final": True,
            "clinical_trial": False,
            "what_data": "Deidentified aggregate analysis dataset and code.",
            "access_mechanism": "Controlled test repository record.",
        }
    )
    value["publication_integrity"].update(
        {
            "original_work_confirmed": True,
            "duplicate_submission_absent": True,
            "overlap_disclosed": True,
            "preprint_status_declared": True,
            "plagiarism_review_completed": True,
            "plagiarism_report_ref": "SIMILARITY-REPORT-001",
            "journal_or_institution_criterion": (
                "Journal policy reviewed; every matching passage assessed by a human."
            ),
            "human_similarity_review_confirmed": True,
            "image_integrity_reviewed": True,
            "results_match_locked_analysis": True,
            "analysis_deviations_disclosed": True,
        }
    )
    value["venue_due_diligence"].update(
        {
            "official_journal_url": "https://journal.example.test/",
            "scope_fit_confirmed": True,
            "peer_review_process_checked": True,
            "fees_checked": True,
            "archiving_checked": True,
            "correction_retraction_policy_checked": True,
            "indexing_verified_from_primary_source": True,
            "checked_at": now,
        }
    )
    value["ethics_and_privacy"].update(
        {
            "ethics_statement_final": True,
            "consent_or_waiver_statement_final": True,
            "registration_statement_final": True,
            "no_identifiable_participant_content_confirmed": True,
        }
    )
    value["final_package"].update(
        {
            "manuscript_version": "1.0-final",
            "package_version": "1.0-final",
            "finalized_at": now,
            "prepared_for_pi_review": True,
        }
    )
    return value


def _prepare_study(out_dir: Path, study: str, n_authors: int = 2) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        out_dir / "G2_checkpoint.json",
        {"gate": "G2", "g2_status": "LOCKED", "guardrail": {"passed": True}},
    )
    _write_json(
        out_dir / "G4_checkpoint.json",
        {"gate": "G4", "g4_status": "LOCKED", "guardrail": {"passed": True}},
    )
    for gate, name in (
        ("G2", f"G2_A3_ETHICS_PACKAGE_{study}.md"),
        ("G4", f"G4_A5_SAP_FINAL_{study}.md"),
        ("G8", f"G8_A9_PRESUBMISSION_{study}.md"),
    ):
        (out_dir / name).write_text(
            f"{gate} final synthetic package. Cần bác sĩ kiểm chứng.",
            encoding="utf-8",
        )
    for name in (
        f"G7_A8_MANUSCRIPT_{study}.md",
        f"G9_A10_AUTHOR_INTEGRITY_{study}.md",
        f"G9_COVER_LETTER_{study}.md",
        f"A12_CITATION_VERIFICATION_{study}.md",
    ):
        (out_dir / name).write_text(
            "Final synthetic publication document. Cần bác sĩ kiểm chứng.",
            encoding="utf-8",
        )
    _write_json(out_dir / "A12_RETRACTION_RECEIPT.json", {"all_clean": True})
    _write_json(out_dir / "A12_METADATA_RECEIPT.json", {"all_resolved": True})
    _write_json(out_dir / G9Q.READINESS_JSON, _complete_readiness(study, n_authors))
    _write_json(
        out_dir / G9Q.CHECKPOINT_JSON,
        {
            "gate": "G9",
            "study": study,
            "n_authors": n_authors,
            "quality_contract_version": G9Q.QUALITY_CONTRACT_VERSION,
            "guardrail": {"passed": True, "errors": [], "warnings": []},
            "submission_package_ready": False,
            "disclaimer": "Cần bác sĩ kiểm chứng.",
        },
    )


def _patch_upstream(monkeypatch, approvals: dict[str, bool] | None = None) -> dict[str, bool]:
    state = {"G2": True, "G4": True, "G8": True, "G9": False}
    if approvals:
        state.update(approvals)
    monkeypatch.setattr(
        G9Q.GC,
        "ledger_approved",
        lambda gate, *_args, **_kwargs: state.get(gate, False),
    )
    monkeypatch.setattr(
        G9Q.GC,
        "g2_quality_contract_satisfied",
        lambda *_args, **_kwargs: True,
    )
    # SỬA 2026-07-30 (G10-01): g9_quality_gate.py nay chấm G4 qua
    # g4_quality_contract_satisfied() thay vì đọc g4_status text (đã lỗi thời) —
    # test giả lập tầng upstream này phải mock đúng hàm mới, nếu không hàm THẬT
    # sẽ chạy và trả False vì fixture không dựng SAP/ledger G4 đầy đủ.
    monkeypatch.setattr(
        G9Q.GC,
        "g4_quality_contract_satisfied",
        lambda *_args, **_kwargs: state.get("G4", False),
    )
    monkeypatch.setattr(
        G9Q.GC,
        "g5_quality_contract_satisfied",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        G10,
        "citation_verification_ok",
        lambda *_args, **_kwargs: (True, ""),
    )
    return state


def _evaluate_ready(tmp_path: Path, monkeypatch, study: str = "PYTEST-G9Q") -> tuple[Path, dict]:
    out_dir = tmp_path / "exports" / study
    _prepare_study(out_dir, study)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study(
        study,
        out_dir,
        repo_root=tmp_path,
        write=True,
    )
    assert report["status"] == G9Q.STATUS_READY, report
    return out_dir, report


def test_complete_package_reaches_ready_but_not_locked(tmp_path, monkeypatch):
    _, report = _evaluate_ready(tmp_path, monkeypatch)
    assert report["human_approval_valid"] is False


def test_each_author_must_have_complete_unique_attestation(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-AUTHOR"
    _prepare_study(out_dir, "PYTEST-G9Q-AUTHOR")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["authors"][1]["author_ref"] = readiness["authors"][0]["author_ref"]
    readiness["authors"][1]["icmje_criteria"]["accountability"] = False
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study(
        "PYTEST-G9Q-AUTHOR", out_dir, repo_root=tmp_path, write=True
    )
    assert report["status"] == G9Q.STATUS_DRAFT
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-01")
    assert row["status"] == "REVIEW"
    assert "duplicate_author_ref" in row["evidence"]


def test_sensitive_data_uploaded_to_ai_is_blocking(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-AI"
    _prepare_study(out_dir, "PYTEST-G9Q-AI")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["ai_disclosure"]["ai_used"] = True
    readiness["ai_disclosure"]["tools"] = ["Verified test tool version 1"]
    readiness["ai_disclosure"]["purposes"] = ["Language editing"]
    readiness["ai_disclosure"]["sensitive_or_confidential_data_uploaded"] = True
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study("PYTEST-G9Q-AI", out_dir, repo_root=tmp_path)
    assert report["status"] == G9Q.STATUS_BLOCKED


def test_missing_g8_or_a12_never_reaches_ready(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-UPSTREAM"
    _prepare_study(out_dir, "PYTEST-G9Q-UPSTREAM")
    _patch_upstream(monkeypatch, {"G8": False})
    monkeypatch.setattr(G10, "citation_verification_ok", lambda *_a, **_k: (False, "missing A12"))
    report = G9Q.evaluate_study(
        "PYTEST-G9Q-UPSTREAM", out_dir, repo_root=tmp_path, write=True
    )
    assert report["status"] == G9Q.STATUS_DRAFT
    pending = {row["id"] for row in report["automatic_criteria"] if row["status"] != "PASS"}
    assert {"G9-AUTO-03", "G9-AUTO-04"} <= pending


def test_clinical_trial_requires_full_icmje_data_sharing_detail(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-TRIAL"
    _prepare_study(out_dir, "PYTEST-G9Q-TRIAL")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["data_availability"]["clinical_trial"] = True
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study("PYTEST-G9Q-TRIAL", out_dir, repo_root=tmp_path)
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-05")
    assert row["status"] == "REVIEW"


def test_similarity_requires_human_policy_not_universal_percentage(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-SIMILARITY"
    _prepare_study(out_dir, "PYTEST-G9Q-SIMILARITY")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["publication_integrity"]["journal_or_institution_criterion"] = None
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study(
        "PYTEST-G9Q-SIMILARITY", out_dir, repo_root=tmp_path
    )
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-06")
    assert row["status"] == "REVIEW"
    assert "< 15%" not in G9.build_part5_integrity({}, "PYTEST")
    assert "< 15%" not in G9.build_part8_gate_criteria({}, 1, "PYTEST")


def test_pi_approval_on_checkpoint_locks_then_manuscript_tamper_blocks(
    tmp_path, monkeypatch
):
    out_dir, _ = _evaluate_ready(tmp_path, monkeypatch, "PYTEST-G9Q-TAMPER")
    monkeypatch.setattr(
        G9Q.GC,
        "ledger_approved",
        lambda gate, *_args, **_kwargs: gate in {"G2", "G4", "G8", "G9"},
    )
    locked = G9Q.evaluate_study(
        "PYTEST-G9Q-TAMPER", out_dir, repo_root=tmp_path, write=True
    )
    assert locked["status"] == G9Q.STATUS_LOCKED, locked
    manuscript = out_dir / "G7_A8_MANUSCRIPT_PYTEST-G9Q-TAMPER.md"
    manuscript.write_text(
        manuscript.read_text(encoding="utf-8") + "\nChanged after PI approval.\n",
        encoding="utf-8",
    )
    tampered = G9Q.evaluate_study(
        "PYTEST-G9Q-TAMPER", out_dir, repo_root=tmp_path
    )
    assert tampered["status"] == G9Q.STATUS_BLOCKED
    manifest_row = next(
        x for x in tampered["automatic_criteria"] if x["id"] == "G9-AUTO-07"
    )
    assert manifest_row["status"] == "BLOCK"


def test_readiness_rejects_contact_pii(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-PII"
    _prepare_study(out_dir, "PYTEST-G9Q-PII")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["authors"][0]["attestation_evidence_ref"] = "person@example.org"
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study("PYTEST-G9Q-PII", out_dir, repo_root=tmp_path)
    assert report["status"] == G9Q.STATUS_BLOCKED


def test_approve_gate_rejects_legacy_a10_for_new_g9(tmp_path, monkeypatch):
    study = "PYTEST-G9Q-WRONG-ARTIFACT"
    out_dir = REPO_ROOT / "exports" / study
    shutil.rmtree(out_dir, ignore_errors=True)
    try:
        _prepare_study(out_dir, study)
        artifact = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
        argv = sys.argv
        sys.argv = [
            "approve_gate.py",
            "--study",
            study,
            "--gate",
            "G9",
            "--artifact",
            str(artifact),
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


def test_run_g9_never_announces_completion_for_draft(tmp_path, monkeypatch, capsys):
    study = "PYTEST-G9Q-DRAFT-LABEL"
    out_dir = REPO_ROOT / "exports" / study
    shutil.rmtree(out_dir, ignore_errors=True)
    argv = sys.argv
    sys.argv = ["run_g9_auto.py", "--study", study]
    try:
        G9.main()
        output = capsys.readouterr().out
        assert "G9 HOÀN THÀNH" not in output
        assert "G9 DRAFT ĐÃ SINH" in output
        assert G9Q.READINESS_JSON in output
    finally:
        sys.argv = argv
        shutil.rmtree(out_dir, ignore_errors=True)


def test_full_signed_chain_reaches_locked_with_real_g5_evaluator(tmp_path, monkeypatch):
    """Tích hợp G2/G4/G5/G8/G9 thật; chỉ stub A12 để không gọi mạng."""
    study = "PYTEST-G9Q-FULL-CHAIN"
    exports_root = tmp_path / "exports"
    source = tmp_path / "synthetic.csv"
    fields = [
        "record_id",
        "age",
        "sex",
        "group",
        "exposure",
        "exposure_var",
        "primary_outcome",
        "outcome_cont",
        "outcome_bin",
        "outcome_score",
        "bmi",
        "follow_time",
        "event_flag",
    ]
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "record_id": "SYN-001",
                "age": "52",
                "sex": "F",
                "group": "0",
                "exposure": "0",
                "exposure_var": "0",
                "primary_outcome": "10",
                "outcome_cont": "10",
                "outcome_bin": "0",
                "outcome_score": "10",
                "bmi": "23",
                "follow_time": "12",
                "event_flag": "0",
            }
        )
        writer.writerow(
            {
                "record_id": "SYN-002",
                "age": "61",
                "sex": "M",
                "group": "1",
                "exposure": "1",
                "exposure_var": "1",
                "primary_outcome": "14",
                "outcome_cont": "14",
                "outcome_bin": "1",
                "outcome_score": "14",
                "bmi": "27",
                "follow_time": "10",
                "event_flag": "1",
            }
        )
    configure_test_signing_key(tmp_path, monkeypatch)
    prepare_locked_g5_study(
        study,
        source,
        exports_root=exports_root,
        repo_root=tmp_path,
    )
    study_dir = exports_root / study
    g8_artifact = study_dir / f"G8_A9_PRESUBMISSION_{study}.md"
    g8_artifact.write_text(
        "Independent presubmission review final. Cần bác sĩ kiểm chứng.",
        encoding="utf-8",
    )
    append_signed_approval(
        study,
        g8_artifact,
        "G8",
        "INDEPENDENT_PEER_REVIEWER",
        repo_root=tmp_path,
    )
    for name in (
        f"G7_A8_MANUSCRIPT_{study}.md",
        f"G9_A10_AUTHOR_INTEGRITY_{study}.md",
        f"G9_COVER_LETTER_{study}.md",
        f"A12_CITATION_VERIFICATION_{study}.md",
    ):
        (study_dir / name).write_text(
            "Final synthetic publication document. Cần bác sĩ kiểm chứng.",
            encoding="utf-8",
        )
    _write_json(study_dir / "A12_RETRACTION_RECEIPT.json", {"all_clean": True})
    _write_json(study_dir / "A12_METADATA_RECEIPT.json", {"all_resolved": True})
    _write_json(study_dir / G9Q.READINESS_JSON, _complete_readiness(study))
    _write_json(
        study_dir / G9Q.CHECKPOINT_JSON,
        {
            "gate": "G9",
            "study": study,
            "n_authors": 2,
            "quality_contract_version": G9Q.QUALITY_CONTRACT_VERSION,
            "guardrail": {"passed": True, "errors": [], "warnings": []},
            "submission_package_ready": False,
            "disclaimer": "Cần bác sĩ kiểm chứng.",
        },
    )
    monkeypatch.setattr(G10, "citation_verification_ok", lambda *_a, **_k: (True, ""))
    ready = G9Q.evaluate_study(
        study,
        study_dir,
        repo_root=tmp_path,
        write=True,
    )
    assert ready["status"] == G9Q.STATUS_READY, ready
    append_signed_approval(
        study,
        study_dir / G9Q.CHECKPOINT_JSON,
        "G9",
        "PI_PROJECT_OWNER",
        repo_root=tmp_path,
    )
    locked = G9Q.evaluate_study(
        study,
        study_dir,
        repo_root=tmp_path,
        write=True,
    )
    assert locked["status"] == G9Q.STATUS_LOCKED, locked
    assert G9Q.GC.g9_quality_contract_satisfied(study, repo_root=tmp_path)
