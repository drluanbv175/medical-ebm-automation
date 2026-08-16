"""Kiểm thử đối kháng cho hợp đồng liêm chính công bố G9 hiện hành."""

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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


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
    value["data_access_governance"].update(
        {
            "all_authors_can_review_supporting_data": True,
            "primary_data_access_author_ref": "AUTHOR-01",
            "primary_data_access_confirmed": True,
            "analysis_participation_confirmed": True,
            "academic_nonacademic_collaboration": False,
            "primary_data_access_author_is_academic": None,
            "sponsored_research": False,
            "confirmed_at": now,
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
    value["institutional_confirmation"].update(
        {
            "department_head_required": False,
            "internal_review_required": False,
            "sponsor_review_required": False,
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
        f"G9_COVER_LETTER_{study}.md",
        f"A12_CITATION_VERIFICATION_{study}.md",
    ):
        (out_dir / name).write_text(
            "Final synthetic publication document. Cần bác sĩ kiểm chứng.",
            encoding="utf-8",
        )
    # SỬA 2026-07-30 (G9-F5): G9-AUTO-02 nay chạy LẠI guardrail_check_g9() trên
    # file A10 THẬT thay vì tin checkpoint["guardrail"] cache — fixture cũ chỉ
    # có 1 câu chung chung nên fail R4/R6 thật (thiếu nhãn DRAFT/CHỜ, thiếu đủ
    # 8 tiêu đề PHẦN). Dựng văn bản đủ boilerplate mà guardrail_check_g9() đòi
    # — KHÔNG dùng "[CẦN" (R5 đã hạ xuống chỉ-thông-tin, nhưng _documents_
    # clean()/G9-AUTO-05 vẫn đòi CHÍNH file này sạch placeholder hoàn toàn để
    # coi là "sẵn sàng nộp" — 2 tiêu chí xung khắc nếu còn "[CẦN" ở đây).
    (out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
        "# A10 — LIÊM CHÍNH TÁC GIẢ (DRAFT — CHỜ KÝ)\n\n"
        "**Trạng thái:** DRAFT — CHỜ xác nhận từng tác giả.\n\n"
        "## PHẦN 1\nĐã điền đầy đủ.\n\n"
        "## PHẦN 2\nĐã điền đầy đủ.\n\n"
        "## PHẦN 3\nĐã điền đầy đủ.\n\n"
        "## PHẦN 4\nĐã điền đầy đủ.\n\n"
        "## PHẦN 5\nĐã điền đầy đủ.\n\n"
        "## PHẦN 6\nĐã điền đầy đủ.\n\n"
        "## PHẦN 7\nĐã điền đầy đủ.\n\n"
        "## PHẦN 8 — HARD GATE\nDRAFT — CHỜ ký PI.\n\n"
        "Cần bác sĩ kiểm chứng.\n",
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


def test_readiness_schema_migration_preserves_real_attestations(tmp_path: Path) -> None:
    study = "PYTEST-G9-MIGRATION"
    readiness = _complete_readiness(study)
    readiness["schema_version"] = "G9-2026.1"
    readiness.pop("data_access_governance")
    evidence_ref = readiness["authors"][0]["attestation_evidence_ref"]
    _write_json(tmp_path / G9Q.READINESS_JSON, readiness)

    G9Q.write_readiness_template(tmp_path, study, 2, "Journal of Test Medicine")
    migrated = json.loads((tmp_path / G9Q.READINESS_JSON).read_text(encoding="utf-8"))

    assert migrated["schema_version"] == G9Q.QUALITY_CONTRACT_VERSION
    assert migrated["authors"][0]["attestation_evidence_ref"] == evidence_ref
    assert migrated["data_access_governance"]["primary_data_access_confirmed"] is False
    assert migrated["data_access_governance"]["sponsored_research"] is None


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


def test_icmje_2026_requires_primary_data_access_and_analysis_participation(
    tmp_path, monkeypatch
):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-DATA-ACCESS"
    _prepare_study(out_dir, "PYTEST-G9Q-DATA-ACCESS")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["data_access_governance"]["analysis_participation_confirmed"] = False
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)

    report = G9Q.evaluate_study(
        "PYTEST-G9Q-DATA-ACCESS", out_dir, repo_root=tmp_path
    )

    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-05A")
    assert row["status"] == "REVIEW"
    assert report["status"] != G9Q.STATUS_READY


def test_sponsored_research_requires_access_and_publication_independence_evidence(
    tmp_path, monkeypatch
):
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-SPONSOR-ACCESS"
    _prepare_study(out_dir, "PYTEST-G9Q-SPONSOR-ACCESS")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["data_access_governance"]["sponsored_research"] = True
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)

    report = G9Q.evaluate_study(
        "PYTEST-G9Q-SPONSOR-ACCESS", out_dir, repo_root=tmp_path
    )

    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-05A")
    assert row["status"] == "REVIEW"
    readiness["data_access_governance"].update(
        {
            "sponsor_agreement_preserves_data_access": True,
            "sponsor_agreement_preserves_publication_independence": True,
            "sponsor_agreement_evidence_ref": "SPONSOR-AGREEMENT-REF-001",
        }
    )
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    report = G9Q.evaluate_study(
        "PYTEST-G9Q-SPONSOR-ACCESS", out_dir, repo_root=tmp_path
    )
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-05A")
    assert row["status"] == "PASS"


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


# ════════════════════════════════════════════════════════════════════════════
# G9-HUMAN-11 — NHÓM D (xác nhận thể chế), thêm 2026-07-31 (audit tích hợp plugin)
# ════════════════════════════════════════════════════════════════════════════
# Trước bản vá này, checklist "Phần 8 — Hard Gate" (run_g9_auto.py) in NHÓM D
# (D1 trưởng đơn vị · D2 hội đồng nội bộ · D3 nhà tài trợ) cho bác sĩ đọc/ký trên
# giấy/Word nhưng KHÔNG có field cấu trúc nào để xác nhận máy đọc được — khoảng
# trống THẬT DUY NHẤT trong Phần 8 (NHÓM A/B/C đều đã có ánh xạ điện tử từ trước).
# _complete_readiness() baseline đánh dấu cả 3 nhóm "không cần" (required=False) —
# các test dưới đây kiểm 2 đường lệch: (a) chưa trả lời (required=None) và
# (b) cần nhưng chưa xác nhận (required=True, confirmed=False).


def test_institutional_confirmation_undetermined_blocks_ready(tmp_path, monkeypatch):
    """required=None (bác sĩ chưa trả lời có/không cần) KHÔNG được coi là OK — phải
    trả lời rõ ràng, không được bỏ trống rồi mặc định qua."""
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-INSTDET"
    _prepare_study(out_dir, "PYTEST-G9Q-INSTDET")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["institutional_confirmation"]["department_head_required"] = None
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study("PYTEST-G9Q-INSTDET", out_dir, repo_root=tmp_path)
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-11")
    assert row["status"] == "REVIEW"
    assert report["status"] != G9Q.STATUS_READY


def test_institutional_confirmation_required_not_yet_confirmed_blocks_ready(
    tmp_path, monkeypatch
):
    """Trưởng đơn vị ĐƯỢC đánh dấu là cần duyệt (required=True) nhưng chưa xác
    nhận thật (confirmed=False) — không được qua chỉ vì đã "trả lời có"."""
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-INSTREQ"
    _prepare_study(out_dir, "PYTEST-G9Q-INSTREQ")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    readiness["institutional_confirmation"]["sponsor_review_required"] = True
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study("PYTEST-G9Q-INSTREQ", out_dir, repo_root=tmp_path)
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-11")
    assert row["status"] == "REVIEW"
    assert "sponsor_review" in row["evidence"]
    assert report["status"] != G9Q.STATUS_READY


def test_institutional_confirmation_required_and_confirmed_reaches_ready(
    tmp_path, monkeypatch
):
    """Đường PASS phải đạt được khi cần duyệt VÀ đã xác nhận thật kèm ngày —
    không chỉ đường "không cần" mới qua được."""
    out_dir = tmp_path / "exports" / "PYTEST-G9Q-INSTOK"
    _prepare_study(out_dir, "PYTEST-G9Q-INSTOK")
    readiness = json.loads((out_dir / G9Q.READINESS_JSON).read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    readiness["institutional_confirmation"].update(
        {
            "internal_review_required": True,
            "internal_review_confirmed": True,
            "internal_review_confirmed_at": now,
        }
    )
    _write_json(out_dir / G9Q.READINESS_JSON, readiness)
    _patch_upstream(monkeypatch)
    report = G9Q.evaluate_study(
        "PYTEST-G9Q-INSTOK", out_dir, repo_root=tmp_path, write=True
    )
    row = next(x for x in report["automatic_criteria"] if x["id"] == "G9-HUMAN-11")
    assert row["status"] == "PASS", row
    assert report["status"] == G9Q.STATUS_READY, report


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
        f"G9_COVER_LETTER_{study}.md",
        f"A12_CITATION_VERIFICATION_{study}.md",
    ):
        (study_dir / name).write_text(
            "Final synthetic publication document. Cần bác sĩ kiểm chứng.",
            encoding="utf-8",
        )
    # SỬA 2026-07-30 (G9-F5): xem chú thích tương tự trong _prepare_study() —
    # G9-AUTO-02 nay chạy lại guardrail_check_g9() trên file A10 thật.
    (study_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(
        "# A10 — LIÊM CHÍNH TÁC GIẢ (DRAFT — CHỜ KÝ)\n\n"
        "**Trạng thái:** DRAFT — CHỜ xác nhận từng tác giả.\n\n"
        "## PHẦN 1\nĐã điền đầy đủ.\n\n"
        "## PHẦN 2\nĐã điền đầy đủ.\n\n"
        "## PHẦN 3\nĐã điền đầy đủ.\n\n"
        "## PHẦN 4\nĐã điền đầy đủ.\n\n"
        "## PHẦN 5\nĐã điền đầy đủ.\n\n"
        "## PHẦN 6\nĐã điền đầy đủ.\n\n"
        "## PHẦN 7\nĐã điền đầy đủ.\n\n"
        "## PHẦN 8 — HARD GATE\nDRAFT — CHỜ ký PI.\n\n"
        "Cần bác sĩ kiểm chứng.\n",
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


def test_cope_authorship_ai_citation_khong_con_tro_sai_sang_thesis_publishing():
    """Hồi quy G9-F3 (audit toàn diện G0-G10, HIGH, trích dẫn sai): DOI cũ
    '10.24318/LQU1h9US' xác minh trực tiếp trỏ tới một tài liệu 2017 về XUẤT
    BẢN LUẬN VĂN (thesis publishing), không liên quan tác giả/AI. DOI đúng
    cho 'COPE Position Statement — Authorship and AI Tools' là
    '10.24318/cCVRZBms' (xác minh qua redirect doi.org)."""
    entry = next(
        item for item in G9Q.STANDARDS_BASIS
        if "authorship" in item["standard"].lower() and "ai" in item["standard"].lower()
    )
    assert entry["doi"] == "10.24318/cCVRZBms", entry
    assert entry["doi"] != "10.24318/LQU1h9US"
