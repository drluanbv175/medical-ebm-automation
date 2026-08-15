"""Test phân loại metadata cho chế độ API thật."""
from app.sources.classify_meta import detect_official_org, infer_study_type


def test_infer_guideline_from_title():
    assert infer_study_type("2024 ESC Guidelines for atrial fibrillation",
                            "journal-article", "European Heart Journal") == "guideline"


def test_infer_systematic_review():
    assert infer_study_type("Tenecteplase vs alteplase: a systematic review and meta-analysis",
                            "journal-article", "Lancet Neurol") == "systematic_review"


def test_infer_rct():
    assert infer_study_type("A randomized controlled trial of drug X",
                            "journal-article", "NEJM") == "rct"


def test_infer_preprint_by_source_tag():
    assert infer_study_type("Some finding", "posted-content", "medRxiv",
                            source_tag="PPR") == "preprint"


def test_infer_preprint_posted_content():
    assert infer_study_type("Some finding", "posted-content", "Research Square") == "preprint"


def test_plain_article_returns_none():
    # Không đủ tín hiệu -> None (pipeline chấm thận trọng), không bịa loại.
    assert infer_study_type("Observations on a patient cohort outcome",
                            "journal-article", "Some Journal") is None


def test_detect_official_org():
    assert detect_official_org("KDIGO 2024 guideline", "Kidney International") == "KDIGO"
    assert detect_official_org("x", "European Heart Journal") == "ESC"
    assert detect_official_org("x", "Unknown Local Journal") is None
