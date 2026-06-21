import pytest

from app.evidence.citation_validator import validate_identifier
from app.evidence.claim_registry import ClaimRegistry
from app.evidence.evidence_lifecycle import verify_evidence
from app.evidence.evidence_registry import EvidenceRegistry, EvidenceStatus
from app.evidence.source_freshness import assess_freshness
from app.research_os.data_lock import lock_dataset
from app.research_os.data_quality_firewall import run_quality_firewall
from app.research_os.design_router import route_design
from app.research_os.protocol_compiler import compile_protocol
from app.research_os.reporting_guideline_mapper import (
    reporting_guideline_for_design,
    reporting_guidelines_all,
)
from app.research_os.reproducibility_runner import compare_result_hash
from app.research_os.sap_engine import StatisticalAnalysisPlan, lock_sap
from app.research_os.study_traceability_matrix import TraceabilityRow, validate_traceability
from app.research_os.variable_dictionary import VariableDefinition, validate_variable_dictionary
from app.safety.data_sufficiency_engine import assess_data_sufficiency
from app.safety.medication_safety_engine import screen_medications
from app.safety.red_flag_engine import detect_red_flags
from app.safety.referral_escalation_engine import requires_escalation


def test_evidence_without_traceability_is_quarantined():
    registry = EvidenceRegistry()
    record = registry.add(title="Nguồn thiếu định danh", source="unknown", evidence_type="review")

    assert record.status is EvidenceStatus.QUARANTINED
    assert record.evidence_id in registry.quarantined_records
    assert record.evidence_id not in registry.records


def test_claim_registry_requires_traceable_evidence_and_grade_source():
    evidence = EvidenceRegistry()
    verified = evidence.add(
        title="Trial có PMID",
        source="PubMed",
        evidence_type="rct",
        identifiers={"pmid": "12345678"},
        status=EvidenceStatus.VERIFIED,
    )
    claims = ClaimRegistry(evidence)

    with pytest.raises(ValueError):
        claims.register_claim(text="Claim thiếu grade source", evidence_ids=[verified.evidence_id], grade_label="high")

    claim = claims.register_claim(
        text="Claim đã liên kết chứng cứ.",
        evidence_ids=[verified.evidence_id],
        grade_label="high",
        grade_source="GRADE guideline chính thức",
    )
    card = claims.create_recommendation_card(
        claim.claim_id,
        "Khuyến nghị cần bác sĩ duyệt",
        "Không tự áp dụng",
        "Theo dõi biến cố bất lợi",
    )

    assert claim.claim_id in claims.claims
    assert "Cần bác sĩ kiểm chứng" in card.disclaimer


def test_citation_lifecycle_and_freshness_checks():
    assert validate_identifier({"pmid": "12345678"}).valid
    assert validate_identifier({"doi": "10.1000/test"}).valid
    assert not validate_identifier({}).valid

    registry = EvidenceRegistry()
    draft = registry.add(
        title="Nguồn có DOI",
        source="Crossref",
        evidence_type="guideline",
        identifiers={"doi": "10.1000/test"},
    )
    assert verify_evidence(draft).status is EvidenceStatus.VERIFIED
    assert assess_freshness("2026-01-01", max_age_days=2000).stale is False
    assert assess_freshness("").stale is True


def test_safety_kernel_detects_red_flags_missing_data_and_medication_pairs():
    signals = detect_red_flags("Ca đã khử định danh có nói khó và méo miệng khởi phát cấp.")
    assert signals
    assert requires_escalation(signals)

    sufficiency = assess_data_sufficiency({"age_group": "adult"}, ["age_group", "chief_complaint"])
    assert not sufficiency.sufficient
    assert sufficiency.missing_fields == ["chief_complaint"]

    issues = screen_medications(["warfarin", "nsaid"])
    assert issues
    assert issues[0].severity == "high"


def test_research_os_gates_design_protocol_sap_and_data_lock():
    assert route_design("Câu hỏi can thiệp random so với chăm sóc chuẩn") == "randomized_controlled_trial"
    protocol = compile_protocol(
        "Nghiên cứu test",
        "randomized_controlled_trial",
        ["Ước tính hiệu quả"],
        ["Biến cố chính"],
    )
    assert protocol.ethics_required
    assert reporting_guideline_for_design(protocol.design) == "CONSORT"

    rows = [TraceabilityRow("RQ1", "outcome_primary", "primary_model", "table_1")]
    assert validate_traceability(rows) == []
    assert validate_variable_dictionary([VariableDefinition("outcome_primary", "Outcome", "binary")]) == []

    sap = StatisticalAnalysisPlan("sap_1", "primary_model")
    assert not sap.can_run_official_analysis(data_locked=True)
    locked_sap = lock_sap(sap)
    data_lock = lock_dataset({"rows": 10, "columns": ["outcome_primary"]}, locked_by="pi")
    assert locked_sap.can_run_official_analysis(data_locked=True)
    assert data_lock.dataset_hash

    firewall = run_quality_firewall({"has_pii": False, "missing_rate": 0.05, "data_dictionary": True})
    assert firewall.passed
    assert compare_result_hash("abc", "abc").passed


# ── CONSORT Semantic Regression Tests (Sprint 2 scope containment gate) ─────
# Added: 2026-06-21  Reason: verify that the CONSORT 2010 → CONSORT rename
# does not silently destroy version metadata and does not regress other guidelines.


def test_consort_canonical_code_is_versionless():
    """Canonical code cho RCT phải là 'CONSORT' (không chứa year pin).

    Design decision: mapper dùng canonical name; version được tra tại EQUATOR.
    Nếu test này fail → có ai đã đưa year trở lại → phải đồng bộ lại test
    test_research_os_gates_design_protocol_sap_and_data_lock (dùng == 'CONSORT').
    """
    result = reporting_guideline_for_design("randomized_controlled_trial")
    assert result == "CONSORT", (
        f"Expected 'CONSORT' (versionless canonical), got {result!r}. "
        "Nếu thêm version vào đây, phải cập nhật tất cả assertion == 'CONSORT'."
    )


def test_consort_full_info_provides_version_guidance():
    """reporting_guidelines_all() phải cung cấp đủ thông tin cho user tìm version.

    Vì canonical code không chứa year, metadata (note + equator_url) là con đường
    duy nhất hướng dẫn version → phải không được rỗng.
    """
    info = reporting_guidelines_all("randomized_controlled_trial")
    assert info["primary"] == "CONSORT"
    # note hoặc equator_url phải có để hướng dẫn version check
    has_version_guidance = bool(info.get("note")) or bool(info.get("equator_url"))
    assert has_version_guidance, (
        "reporting_guidelines_all() thiếu note/equator_url → user không biết version nào dùng."
    )
    # supplementary không được mất (SPIRIT 2013 vẫn phải ở đây)
    supps = info.get("supplementary", [])
    assert any("SPIRIT" in s for s in supps), (
        "Supplementary của RCT phải chứa SPIRIT 2013 — bị mất sau lần edit?"
    )


def test_mapper_other_guidelines_unaffected_by_consort_rename():
    """Rename CONSORT 2010 → CONSORT không được làm hỏng mapping của các guideline khác.

    Regression: kiểm tra toàn bộ 8 thiết kế còn lại vẫn trả đúng code gốc.
    """
    expected = {
        "cohort": "STROBE",
        "cross_sectional": "STROBE",
        "case_control": "STROBE",
        "diagnostic_accuracy": "STARD",
        "systematic_review": "PRISMA",
        "prediction_model": "TRIPOD",
        "qualitative": "COREQ",
        "case_report": "CARE",
        "economic_evaluation": "CHEERS",
        "quality_improvement": "SQUIRE",
    }
    for design, expected_prefix in expected.items():
        result = reporting_guideline_for_design(design)
        assert expected_prefix in result, (
            f"Design '{design}': expected prefix '{expected_prefix}', got {result!r}."
        )
