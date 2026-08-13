from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "verify_direct_clinical_practice_readiness.py"
spec = importlib.util.spec_from_file_location("verify_direct_clinical_practice_readiness", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


TODAY = date(2026, 8, 13)


def _card(**overrides: object) -> dict:
    card = {
        "id": "EVID-SYN-0001",
        "topic": "Synthetic CKD guideline update",
        "date_source": "2026",
        "date_added": "2026-08-13",
        "source": {
            "agency": "KDIGO",
            "title": "Synthetic guideline source",
            "url": "",
            "pmid": "38490803",
            "doi": "10.1016/j.kint.2023.10.018",
            "type": "guideline/RCT",
        },
        "provenance": "from_doctor_master",
        "verification_status": "đã xác minh",
        "gradeLevel": "high",
        "decision": "apply",
        "recommendation": "Synthetic recommendation for outpatient EBM review.",
        "references": ["PMID:38490803", "DOI:10.1016/j.kint.2023.10.018"],
    }
    card.update(overrides)
    return card


def test_doctor_verified_high_grade_apply_card_is_direct_ready():
    result = module.evaluate_card(_card(), today=TODAY)

    assert result.status == module.READY
    assert result.blockers == []
    assert "legacy_doctor_curated_without_signed_approval_id" in result.warnings


def test_engine_verified_consider_card_stays_in_review_queue():
    result = module.evaluate_card(
        _card(
            provenance="from_engine",
            verification_status="đã xác minh nguồn chính thức",
            decision="consider",
        ),
        today=TODAY,
    )

    assert result.status == module.REVIEW
    assert "decision_not_apply:consider" in result.blockers
    assert "missing_doctor_gate_evidence" in result.blockers


def test_apply_card_without_durable_or_official_trace_is_blocked():
    card = _card(
        source={
            "agency": "Unknown journal",
            "title": "Synthetic source",
            "url": "https://example.com/source",
            "pmid": "",
            "doi": "",
            "type": "observational",
        },
        references=["URL:https://example.com/source"],
    )

    result = module.evaluate_card(card, today=TODAY)

    assert result.status == module.BLOCKED
    assert "missing_pmid_doi_or_trusted_official_url" in result.blockers
    assert "source_type_not_high_authority" in result.blockers


def test_apply_card_with_stale_review_date_is_blocked_for_latest_gate():
    result = module.evaluate_card(_card(date_added="2026-01-01"), today=TODAY, freshness_days=90)

    assert result.status == module.BLOCKED
    assert any(blocker.startswith("freshness_review_stale:") for blocker in result.blockers)


def test_apply_card_with_pii_marker_is_blocked_but_study_dates_are_allowed():
    safe_date = module.evaluate_card(_card(recommendation="Trial dates 10/07/2026 were reported."), today=TODAY)
    unsafe_identifier = module.evaluate_card(_card(recommendation="Synthetic text with CCCD 012345678901."), today=TODAY)

    assert safe_date.status == module.READY
    assert unsafe_identifier.status == module.BLOCKED
    assert "pii_suspected" in unsafe_identifier.blockers


def test_master_report_counts_ready_and_blocked_apply_cards():
    report = module.evaluate_master(
        {
            "evidence_cards": [
                _card(id="READY"),
                _card(id="REVIEW", provenance="from_engine", decision="consider"),
                _card(id="BLOCKED", source={"agency": "Unknown", "type": "observational", "url": ""}, references=[]),
            ]
        },
        today=TODAY,
    )

    assert report["auto_apply_allowed"] is False
    assert report["doctor_final_decision_required"] is True
    assert report["ready_for_physician_direct_use"] == 1
    assert report["review_required"] == 1
    assert report["blocked_apply_items"] == 1
