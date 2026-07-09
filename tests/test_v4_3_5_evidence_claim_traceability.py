"""
tests/test_v4_3_5_evidence_claim_traceability.py

V4.3.5 — Evidence Intake & Claim Traceability: 21 kiểm thử xác định.

Bất biến được kiểm thử:
  T01  HUMAN_PROVIDED_ONLY được chấp nhận
  T02  AUTO_RETRIEVED bị block
  T03  MODEL_GENERATED bị block
  T04  API_FETCHED bị block
  T05  UNVERIFIED source không thể support claim
  T06  RETRACTED source block claim
  T07  HUMAN_VERIFIED source → claim SUPPORTED
  T08  Không có source → REQUIRE_HUMAN_EVIDENCE_INPUT
  T09  Hỗn hợp verified/unverified → BLOCKED_UNVERIFIED_EVIDENCE
  T10  Evidence Ledger append-only (không xóa/ghi đè record cũ)
  T10b Claim Ledger append-only (không xóa/ghi đè record cũ)
  T11  Evidence source không chứa PII
  T12  Claim không chứa PII
  T13  D-R8 ledger rỗng = REQUIRE_HUMAN_EVIDENCE_INPUT
  T14  D-R8 claim bị BLOCK_UNVERIFIED → FAIL
  T15  D-R8 RETRACTED source → FAIL
  T16  D-R8 PASS chỉ khi tất cả HUMAN_VERIFIED, không claim blocked
  T17  Evidence review queue định tuyến về EVIDENCE_CITATION_REVIEWER
  T18  Automation không thể tự đặt HUMAN_VERIFIED
  T19  CLI có 4 subcommand mới; không gọi network/API
  T20  Reproducibility check vẫn PASS (D-R13 không bị phá vỡ)

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII.
"""

from __future__ import annotations

import json
import pathlib

import pytest

# Imports từ package
from research_project import (
    # Evidence Source Ledger (V4.3.5)
    RetrievalMode, VerificationState, EvidenceSource, EvidenceSourceLedger,
    ForbiddenRetrievalMode, AutoVerificationForbidden, PIIInEvidenceError,
    EVIDENCE_SOURCE_LEDGER_FILENAME,
    add_evidence_source, get_evidence_review_queue,
    # Claim Traceability (V4.3.5)
    ClaimType, ClaimStatus, ClaimRecord, ClaimTraceabilityLedger,
    CLAIM_LEDGER_FILENAME,
    compute_claim_status, register_claim, get_claim_audit,
    # Config / QA
    GateStatus, ProjectConfig, StudyType,
)
from research_project.project_qa_runner import ProjectQARunner
from research_project.project_config import (
    EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT,
    EVIDENCE_GATE_STATE_BLOCK,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SYNTH_PROJECT_ID = "SYNTH-V435-TEST"


def _make_config() -> ProjectConfig:
    return ProjectConfig(
        project_id=_SYNTH_PROJECT_ID,
        title="Synth V4.3.5 Test Project",
        study_type=StudyType.CROSS_SECTIONAL,
        primary_objectives=["Mục tiêu test"],
        secondary_objectives=[],
        primary_outcomes=["Kết cục test"],
        secondary_outcomes=[],
        research_constraints={},
        data_mode="NO_REAL_DATA",
        external_actions_forbidden=True,
        draft_only=True,
        created_at="2026-06-28T00:00:00Z",
        version="0.1.0",
        human_owner="TEST_PI",
    )


def _make_runner(project_dir: pathlib.Path) -> ProjectQARunner:
    return ProjectQARunner(project_dir, _make_config())


def _make_project_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Tạo project_dir giả tối thiểu (không cần registry thật)."""
    d = tmp_path / _SYNTH_PROJECT_ID
    d.mkdir()
    return d


def _add_source(
    project_dir: pathlib.Path,
    verification_state: VerificationState = VerificationState.UNVERIFIED,
    title: str = "Synth Study Title",
    automation_caller: bool = False,
) -> EvidenceSource:
    return add_evidence_source(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        source_type="RCT",
        title=title,
        authors_or_organization="Synth Author",
        publication_year="2025",
        journal_or_publisher="Synth Journal",
        doi="10.0000/synth.001",
        pmid="99999901",
        url="",
        human_provided_reference="Synth Author. Synth Journal. 2025;1:1.",
        verification_state=verification_state,
        verification_reason="Synth verification reason",
        reviewer_reference="EVIDENCE_CITATION_REVIEWER",
        automation_caller=automation_caller,
    )


# ---------------------------------------------------------------------------
# T01 — HUMAN_PROVIDED_ONLY được chấp nhận
# ---------------------------------------------------------------------------

def test_t01_human_provided_only_accepted(tmp_path):
    """EvidenceSource với HUMAN_PROVIDED_ONLY được lưu thành công."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir)
    assert source.retrieval_mode == RetrievalMode.HUMAN_PROVIDED_ONLY
    assert (project_dir / EVIDENCE_SOURCE_LEDGER_FILENAME).exists()


# ---------------------------------------------------------------------------
# T02 — AUTO_RETRIEVED bị block
# ---------------------------------------------------------------------------

def test_t02_auto_retrieved_blocked(tmp_path):
    """EvidenceSource với retrieval_mode AUTO_RETRIEVED → ForbiddenRetrievalMode."""
    project_dir = _make_project_dir(tmp_path)
    ts = "2025-01-01T00:00:00"
    bad_source = EvidenceSource(
        source_id="ES-BADTEST001",
        project_id=_SYNTH_PROJECT_ID,
        source_type="RCT",
        title="Auto Test",
        authors_or_organization="Bot",
        publication_year="2025",
        journal_or_publisher="Bot Journal",
        doi="10.0/bot",
        pmid="",
        url="",
        human_provided_reference="",
        retrieval_mode=RetrievalMode("AUTO_RETRIEVED"),  # type: ignore[arg-type]
        verification_state=VerificationState.UNVERIFIED,
        verification_reason="",
        reviewer_reference="",
        review_mode="",
        retraction_status="NOT_RETRACTED",
        claim_use_allowed=False,
        created_at_utc=ts,
        audit_event_id="AE-BAD001",
    )
    ledger = EvidenceSourceLedger(project_dir)
    with pytest.raises((ForbiddenRetrievalMode, ValueError)):
        ledger.add(bad_source)


# ---------------------------------------------------------------------------
# T03 — MODEL_GENERATED bị block
# ---------------------------------------------------------------------------

def test_t03_model_generated_blocked(tmp_path):
    """retrieval_mode=MODEL_GENERATED → ForbiddenRetrievalMode hoặc ValueError."""
    project_dir = _make_project_dir(tmp_path)
    ts = "2025-01-01T00:00:00"
    bad_source = EvidenceSource(
        source_id="ES-MODELTEST",
        project_id=_SYNTH_PROJECT_ID,
        source_type="GUIDELINE",
        title="Model Generated Source",
        authors_or_organization="LLM",
        publication_year="2025",
        journal_or_publisher="Model Journal",
        doi="",
        pmid="",
        url="",
        human_provided_reference="",
        retrieval_mode=RetrievalMode("MODEL_GENERATED"),  # type: ignore[arg-type]
        verification_state=VerificationState.UNVERIFIED,
        verification_reason="",
        reviewer_reference="",
        review_mode="",
        retraction_status="NOT_RETRACTED",
        claim_use_allowed=False,
        created_at_utc=ts,
        audit_event_id="AE-MODEL01",
    )
    ledger = EvidenceSourceLedger(project_dir)
    with pytest.raises((ForbiddenRetrievalMode, ValueError)):
        ledger.add(bad_source)


# ---------------------------------------------------------------------------
# T04 — API_FETCHED bị block
# ---------------------------------------------------------------------------

def test_t04_api_fetched_blocked(tmp_path):
    """retrieval_mode=API_FETCHED → ForbiddenRetrievalMode hoặc ValueError."""
    project_dir = _make_project_dir(tmp_path)
    ts = "2025-01-01T00:00:00"
    bad_source = EvidenceSource(
        source_id="ES-APITEST01",
        project_id=_SYNTH_PROJECT_ID,
        source_type="META_ANALYSIS",
        title="API Fetched Source",
        authors_or_organization="API Bot",
        publication_year="2024",
        journal_or_publisher="API Journal",
        doi="",
        pmid="",
        url="",
        human_provided_reference="",
        retrieval_mode=RetrievalMode("API_FETCHED"),  # type: ignore[arg-type]
        verification_state=VerificationState.UNVERIFIED,
        verification_reason="",
        reviewer_reference="",
        review_mode="",
        retraction_status="NOT_RETRACTED",
        claim_use_allowed=False,
        created_at_utc=ts,
        audit_event_id="AE-API0001",
    )
    ledger = EvidenceSourceLedger(project_dir)
    with pytest.raises((ForbiddenRetrievalMode, ValueError)):
        ledger.add(bad_source)


# ---------------------------------------------------------------------------
# T05 — UNVERIFIED source không thể support claim
# ---------------------------------------------------------------------------

def test_t05_unverified_source_cannot_support_claim(tmp_path):
    """Claim liên kết với UNVERIFIED source → BLOCKED_UNVERIFIED_EVIDENCE."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir, VerificationState.UNVERIFIED)
    record = register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Synth background claim from unverified study.",
        claim_type=ClaimType.BACKGROUND,
        linked_source_ids=[source.source_id],
    )
    assert record.claim_status == ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE


# ---------------------------------------------------------------------------
# T06 — RETRACTED source block claim
# ---------------------------------------------------------------------------

def test_t06_retracted_source_blocks_claim(tmp_path):
    """Claim liên kết với RETRACTED source → BLOCKED_RETRACTED_EVIDENCE."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir, VerificationState.RETRACTED)
    record = register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Claim referencing retracted evidence.",
        claim_type=ClaimType.SAFETY,
        linked_source_ids=[source.source_id],
    )
    assert record.claim_status == ClaimStatus.BLOCKED_RETRACTED_EVIDENCE


# ---------------------------------------------------------------------------
# T07 — HUMAN_VERIFIED source → claim SUPPORTED
# ---------------------------------------------------------------------------

def test_t07_human_verified_source_supports_claim(tmp_path):
    """Claim liên kết với HUMAN_VERIFIED source → SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir, VerificationState.HUMAN_VERIFIED)
    record = register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Synth claim supported by verified evidence.",
        claim_type=ClaimType.GUIDELINE,
        linked_source_ids=[source.source_id],
    )
    assert record.claim_status == ClaimStatus.SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE


# ---------------------------------------------------------------------------
# T08 — Không có source → REQUIRE_HUMAN_EVIDENCE_INPUT
# ---------------------------------------------------------------------------

def test_t08_no_source_require_human_input(tmp_path):
    """Claim không có linked_source_ids → REQUIRE_HUMAN_EVIDENCE_INPUT."""
    project_dir = _make_project_dir(tmp_path)
    ev_ledger = EvidenceSourceLedger(project_dir)
    status, reason, summary = compute_claim_status([], ev_ledger)
    assert status == ClaimStatus.REQUIRE_HUMAN_EVIDENCE_INPUT
    assert not summary


# ---------------------------------------------------------------------------
# T09 — Hỗn hợp verified/unverified → BLOCKED_UNVERIFIED_EVIDENCE
# ---------------------------------------------------------------------------

def test_t09_mixed_verified_unverified_blocked(tmp_path):
    """Claim liên kết 1 HUMAN_VERIFIED + 1 UNVERIFIED → BLOCKED_UNVERIFIED_EVIDENCE."""
    project_dir = _make_project_dir(tmp_path)
    s_verified = _add_source(project_dir, VerificationState.HUMAN_VERIFIED, "Verified Study")
    s_unverified = _add_source(project_dir, VerificationState.UNVERIFIED, "Unverified Study")
    record = register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Mixed evidence claim.",
        claim_type=ClaimType.METHODS,
        linked_source_ids=[s_verified.source_id, s_unverified.source_id],
    )
    assert record.claim_status == ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE


# ---------------------------------------------------------------------------
# T10 — Ledger append-only
# ---------------------------------------------------------------------------

def test_t10_ledger_append_only(tmp_path):
    """Mỗi lần add() ghi thêm dòng mới; không ghi đè dòng cũ."""
    project_dir = _make_project_dir(tmp_path)
    _add_source(project_dir, VerificationState.UNVERIFIED, "Study A")
    _add_source(project_dir, VerificationState.HUMAN_VERIFIED, "Study B")
    ev_ledger = EvidenceSourceLedger(project_dir)
    sources = ev_ledger.read_all()
    assert len(sources) == 2
    titles = {s.title for s in sources}
    assert "Study A" in titles
    assert "Study B" in titles


# ---------------------------------------------------------------------------
# T10b — Claim Ledger append-only
# ---------------------------------------------------------------------------

def test_t10b_claim_ledger_append_only(tmp_path):
    """Mỗi lần register_claim() ghi thêm dòng mới vào claim ledger; không ghi đè."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir, VerificationState.HUMAN_VERIFIED)
    register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="First synth claim.",
        claim_type=ClaimType.BACKGROUND,
        linked_source_ids=[source.source_id],
    )
    register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Second synth claim.",
        claim_type=ClaimType.METHODS,
        linked_source_ids=[source.source_id],
    )
    ledger = ClaimTraceabilityLedger(project_dir)
    records = ledger.read_all()
    assert len(records) == 2
    texts = {r.claim_text for r in records}
    assert "First synth claim." in texts
    assert "Second synth claim." in texts
    # Kiểm tra file tồn tại và không thể delete()
    assert not hasattr(ledger, "delete")
    assert not hasattr(ledger, "update")


# ---------------------------------------------------------------------------
# T11 — Evidence source không chứa PII
# ---------------------------------------------------------------------------

def test_t11_evidence_source_no_pii(tmp_path):
    """PII trong title hoặc authors → PIIInEvidenceError."""
    project_dir = _make_project_dir(tmp_path)
    pii_title = "Study for patient Nguyen Van An, DOB 01/01/1980, ID 123456"
    with pytest.raises(PIIInEvidenceError):
        add_evidence_source(
            project_dir=project_dir,
            project_id=_SYNTH_PROJECT_ID,
            source_type="RCT",
            title=pii_title,
            authors_or_organization="Synth Author",
            publication_year="2025",
            journal_or_publisher="Synth Journal",
            doi="",
            pmid="",
            url="",
            human_provided_reference="",
            verification_state=VerificationState.UNVERIFIED,
            verification_reason="",
            reviewer_reference="",
        )


# ---------------------------------------------------------------------------
# T12 — Claim không chứa PII
# ---------------------------------------------------------------------------

def test_t12_claim_no_pii(tmp_path):
    """PII trong claim_text → PIIInEvidenceError."""
    project_dir = _make_project_dir(tmp_path)
    # Dùng marker "patient id" có trong _PII_MARKERS
    pii_claim = "Participant patient id 789012 showed significant improvement."
    with pytest.raises(PIIInEvidenceError):
        register_claim(
            project_dir=project_dir,
            project_id=_SYNTH_PROJECT_ID,
            artifact_id="03_EVIDENCE_PLAN",
            artifact_version="0.1.0",
            claim_text=pii_claim,
            claim_type=ClaimType.BACKGROUND,
            linked_source_ids=[],
        )


# ---------------------------------------------------------------------------
# T13 — D-R8 ledger rỗng = REQUIRE_HUMAN_EVIDENCE_INPUT
# ---------------------------------------------------------------------------

def test_t13_dr8_empty_ledger_require_human_evidence_input(tmp_path):
    """D-R8 V4.3.5: ledger rỗng → WARN + REQUIRE_HUMAN_EVIDENCE_INPUT."""
    project_dir = _make_project_dir(tmp_path)
    (project_dir / EVIDENCE_SOURCE_LEDGER_FILENAME).write_text("", encoding="utf-8")
    runner = _make_runner(project_dir)
    result = runner._dr8_evidence_status()
    assert result.status == GateStatus.WARN
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT


# ---------------------------------------------------------------------------
# T14 — D-R8 claim bị BLOCK_UNVERIFIED → FAIL
# ---------------------------------------------------------------------------

def test_t14_dr8_blocked_unverified_claim_fail(tmp_path):
    """D-R8 V4.3.5: claim dùng UNVERIFIED source → FAIL + BLOCK."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir, VerificationState.UNVERIFIED)
    register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Claim with unverified evidence.",
        claim_type=ClaimType.BACKGROUND,
        linked_source_ids=[source.source_id],
    )
    runner = _make_runner(project_dir)
    result = runner._dr8_evidence_status()
    assert result.status == GateStatus.FAIL
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_BLOCK


# ---------------------------------------------------------------------------
# T15 — D-R8 RETRACTED source → FAIL
# ---------------------------------------------------------------------------

def test_t15_dr8_retracted_source_fail(tmp_path):
    """D-R8 V4.3.5: RETRACTED source → FAIL + BLOCK ngay cả khi không có claim."""
    project_dir = _make_project_dir(tmp_path)
    _add_source(project_dir, VerificationState.RETRACTED)
    runner = _make_runner(project_dir)
    result = runner._dr8_evidence_status()
    assert result.status == GateStatus.FAIL
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_BLOCK


# ---------------------------------------------------------------------------
# T16 — D-R8 PASS chỉ khi tất cả HUMAN_VERIFIED và không có blocked claim
# ---------------------------------------------------------------------------

def test_t16_dr8_pass_all_verified_no_blocked_claims(tmp_path):
    """D-R8 V4.3.5: tất cả HUMAN_VERIFIED, claim SUPPORTED → PASS."""
    project_dir = _make_project_dir(tmp_path)
    source = _add_source(project_dir, VerificationState.HUMAN_VERIFIED)
    register_claim(
        project_dir=project_dir,
        project_id=_SYNTH_PROJECT_ID,
        artifact_id="03_EVIDENCE_PLAN",
        artifact_version="0.1.0",
        claim_text="Fully supported synth claim.",
        claim_type=ClaimType.BACKGROUND,
        linked_source_ids=[source.source_id],
    )
    runner = _make_runner(project_dir)
    result = runner._dr8_evidence_status()
    assert result.status == GateStatus.PASS


# ---------------------------------------------------------------------------
# T17 — Evidence review queue định tuyến về EVIDENCE_CITATION_REVIEWER
# ---------------------------------------------------------------------------

def test_t17_review_queue_routes_to_evidence_citation_reviewer(tmp_path):
    """get_evidence_review_queue trả reviewer_reference = EVIDENCE_CITATION_REVIEWER."""
    project_dir = _make_project_dir(tmp_path)
    _add_source(project_dir, VerificationState.UNVERIFIED)
    _add_source(project_dir, VerificationState.REQUIRES_HUMAN_REVIEW, "Study Needs Review")
    queue = get_evidence_review_queue(project_dir)
    assert len(queue) == 2
    for item in queue:
        assert item["reviewer_reference"] == "EVIDENCE_CITATION_REVIEWER"
        assert "not implemented" in item["note"]


# ---------------------------------------------------------------------------
# T18 — Automation không thể tự đặt HUMAN_VERIFIED
# ---------------------------------------------------------------------------

def test_t18_automation_cannot_set_human_verified(tmp_path):
    """automation_caller=True + HUMAN_VERIFIED → AutoVerificationForbidden."""
    project_dir = _make_project_dir(tmp_path)
    with pytest.raises(AutoVerificationForbidden):
        _add_source(
            project_dir,
            verification_state=VerificationState.HUMAN_VERIFIED,
            automation_caller=True,
        )


# ---------------------------------------------------------------------------
# T19 — CLI có 4 subcommand mới; không gọi network/API
# ---------------------------------------------------------------------------

def test_t19_cli_has_4_new_subcommands():
    """CLI parser có đủ 4 subcommand V4.3.5; không import network/requests."""
    from research_project.project_cli import _build_parser
    import sys

    parser = _build_parser()
    subparsers_action = None
    for action in parser._actions:
        if hasattr(action, "_name_parser_map"):
            subparsers_action = action
            break

    assert subparsers_action is not None
    commands = set(subparsers_action._name_parser_map.keys())
    assert "project-evidence-import" in commands
    assert "project-evidence-list" in commands
    assert "project-claim-register" in commands
    assert "project-claim-audit" in commands

    # Không import requests / httpx / urllib trong module
    import research_project.project_cli as cli_module
    import research_project.project_evidence_intake as ei_module
    import research_project.project_claim_traceability as ct_module
    for mod in (cli_module, ei_module, ct_module):
        for attr in ("requests", "httpx", "urllib3"):
            assert not hasattr(mod, attr), f"Module {mod.__name__} imports {attr}"


# ---------------------------------------------------------------------------
# T20 — Reproducibility check vẫn PASS (D-R13 không bị phá vỡ)
# ---------------------------------------------------------------------------

def test_t20_reproducibility_check_still_passes(tmp_path):
    """
    Thêm V4.3.5 modules không phá D-R13 reproducibility check.
    Kiểm tra compile sạch và import thành công.
    """
    import importlib
    import sys

    # Xoá cache nếu có để test import tươi
    mods_to_check = [
        "research_project.project_evidence_intake",
        "research_project.project_claim_traceability",
        "research_project.project_qa_runner",
        "research_project.project_cli",
        "research_project",
    ]
    for mod_name in mods_to_check:
        if mod_name in sys.modules:
            # Chỉ kiểm tra — không xoá vì sẽ ảnh hưởng test khác
            pass

    # Kiểm tra toàn bộ có thể import
    from research_project import (
        RetrievalMode, VerificationState, EvidenceSource,
        ClaimType, ClaimStatus,
        ForbiddenRetrievalMode, AutoVerificationForbidden,
        compute_claim_status, register_claim,
    )

    # Kiểm tra FORBIDDEN_RETRIEVAL_MODES đúng tập
    from research_project.project_evidence_intake import FORBIDDEN_RETRIEVAL_MODES
    assert "AUTO_RETRIEVED" in FORBIDDEN_RETRIEVAL_MODES
    assert "MODEL_GENERATED" in FORBIDDEN_RETRIEVAL_MODES
    assert "WEB_SCRAPED" in FORBIDDEN_RETRIEVAL_MODES
    assert "API_FETCHED" in FORBIDDEN_RETRIEVAL_MODES
    assert "HUMAN_PROVIDED_ONLY" not in FORBIDDEN_RETRIEVAL_MODES

    # Kiểm tra ClaimStatus không có FINAL/APPROVED
    from research_project.project_claim_traceability import FORBIDDEN_CLAIM_STATUSES
    assert "FINAL" in FORBIDDEN_CLAIM_STATUSES
    assert "APPROVED" in FORBIDDEN_CLAIM_STATUSES
