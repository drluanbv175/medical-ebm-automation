"""Test scoring: evidence quality, practice change, reliability, operational level."""
from app.scoring import (
    evidence_quality_score,
    operational_evidence_level,
    practice_change_score,
    reliability_tier,
)


def test_guideline_scores_high():
    item = {"study_type": "guideline", "title": "ESC guideline recommend anticoagulation",
            "abstract": "multicenter clinical outcome mortality", "official_grade": "GRADE"}
    eq, _ = evidence_quality_score(item)
    pc, _ = practice_change_score(item)
    assert eq >= 75
    assert pc >= 50
    tier = reliability_tier(item, eq, pc)
    assert tier == "A"


def test_preprint_scores_low_and_excluded_tier():
    item = {"study_type": "preprint", "title": "Novel biomarker preprint",
            "abstract": "not peer reviewed"}
    eq, _ = evidence_quality_score(item)
    pc, _ = practice_change_score(item)
    assert eq <= 30
    tier = reliability_tier(item, eq, pc)
    assert tier == "D"


def test_operational_level_marks_non_official():
    item = {"study_type": "rct", "title": "x", "abstract": "mortality multicenter"}
    eq, _ = evidence_quality_score(item)
    level, is_official = operational_evidence_level(item, eq)
    assert is_official is False
    assert "operational" in level.lower()


def test_operational_level_uses_official_grade():
    item = {"official_grade": "High"}
    level, is_official = operational_evidence_level(item, 50)
    assert is_official is True
    assert level == "High"


def test_scores_bounded_0_100():
    item = {"study_type": "rct", "title": "a " * 50, "abstract": "mortality outpatient ckd dose"}
    eq, _ = evidence_quality_score(item)
    pc, _ = practice_change_score(item)
    assert 0 <= eq <= 100
    assert 0 <= pc <= 100
