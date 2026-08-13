from __future__ import annotations

from datetime import date

from app.scoring import evidence_quality_score, practice_change_score, reliability_tier
from app.services.filtering import classify
from app.sources.authority import match_authority_source, trusted_source_names
from tools.verify_direct_clinical_practice_readiness import evaluate_card


def test_registry_recognizes_major_journals_and_societies():
    names = trusted_source_names()

    assert "NEJM" in names
    assert "The Lancet" in names
    assert "Cochrane" in names
    assert match_authority_source("New England Journal of Medicine").name == "NEJM"
    assert match_authority_source("The Lancet Diabetes & Endocrinology").name == "The Lancet"
    assert match_authority_source("Cochrane Database of Systematic Reviews").name == "Cochrane"
    assert match_authority_source("European Heart Journal / ESC").name == "ESC"


def test_trusted_journal_rct_gets_authority_bonus_and_tier_a():
    item = {
        "study_type": "rct",
        "journal_or_organization": "New England Journal of Medicine",
        "title": "Multicenter randomized outpatient mortality trial",
        "abstract": (
            "Multicenter mortality outpatient should first-line ckd dose adjustment score "
            "for clinical practice."
        ),
    }

    evidence_quality, breakdown = evidence_quality_score(item)
    practice_change, _ = practice_change_score(item)

    assert "authority_source_a" in breakdown
    assert item["_detected_org"] == "NEJM"
    assert reliability_tier(item, evidence_quality, practice_change) == "A"


def test_authority_source_does_not_promote_editorial_to_actionable():
    item = {
        "study_type": "editorial",
        "journal_or_organization": "The Lancet",
        "title": "Editorial comment on outpatient practice",
        "abstract": "Viewpoint only.",
    }

    evidence_quality, breakdown = evidence_quality_score(item)
    practice_change, _ = practice_change_score(item)
    tier = reliability_tier(item, evidence_quality, practice_change)
    item.update(
        evidence_quality_score=evidence_quality,
        practice_change_score=practice_change,
        reliability_tier=tier,
    )
    classification, actionable, _, reason = classify(item)

    assert "authority_source_a" in breakdown
    assert tier == "D"
    assert classification == "excluded"
    assert actionable is False
    assert "editorial" in reason


def test_direct_readiness_accepts_authority_registry_source_but_keeps_doctor_gate():
    card = {
        "id": "AUTH-NEJM-0001",
        "topic": "Synthetic RCT update",
        "date_source": "2026-08",
        "date_added": "2026-08-13",
        "source": {
            "agency": "",
            "journal_or_organization": "New England Journal of Medicine",
            "title": "Synthetic randomized trial",
            "pmid": "12345678",
            "doi": "",
            "url": "",
            "type": "randomized clinical trial",
        },
        "provenance": "from_engine",
        "verification_status": "verified",
        "gradeLevel": "high",
        "decision": "apply",
        "recommendation": "Synthetic recommendation for review.",
        "references": ["PMID:12345678"],
    }

    result = evaluate_card(card, today=date(2026, 8, 13))

    assert "source_type_not_high_authority" not in result.blockers
    assert "missing_doctor_gate_evidence" in result.blockers
    assert result.status == "BLOCKED_FOR_DIRECT_USE"
