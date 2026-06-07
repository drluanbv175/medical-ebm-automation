"""Test exclusion rule & classification."""
from app.services.filtering import classify


def test_preprint_excluded():
    item = {"study_type": "preprint", "title": "x", "evidence_quality_score": 10,
            "practice_change_score": 0, "reliability_tier": "D"}
    classification, actionable, _, reason = classify(item)
    assert classification == "excluded"
    assert actionable is False
    assert reason  # phải có lý do loại trừ


def test_actionable_requires_tier_a_and_thresholds():
    item = {"study_type": "guideline", "title": "guideline", "evidence_quality_score": 90,
            "practice_change_score": 80, "reliability_tier": "A"}
    classification, actionable, a_reason, _ = classify(item)
    assert classification == "actionable"
    assert actionable is True
    assert a_reason  # phải có lý do actionable


def test_watch_only_for_weak_evidence():
    item = {"study_type": "cohort", "title": "small cohort", "evidence_quality_score": 40,
            "practice_change_score": 20, "reliability_tier": "C"}
    classification, actionable, _, reason = classify(item)
    assert classification == "watch_only"
    assert actionable is False
    assert reason


def test_missing_title_excluded():
    item = {"study_type": "rct", "title": "", "evidence_quality_score": 80,
            "practice_change_score": 70, "reliability_tier": "A"}
    classification, actionable, _, _ = classify(item)
    assert classification == "excluded"
