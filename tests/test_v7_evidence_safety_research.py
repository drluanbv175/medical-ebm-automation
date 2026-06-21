import pytest

from app.evidence.citation_validator import validate_identifier
from app.evidence.claim_registry import ClaimRegistry
from app.evidence.evidence_lifecycle import verify_evidence
from app.evidence.evidence_registry import EvidenceRegistry, EvidenceStatus
from app.evidence.source_freshness import assess_freshness
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
