"""Nhóm C — siết luật scoring (đã được người dùng duyệt). Khóa hành vi mới.

C1: regulatory_alert 1 dòng KHÔNG tự lên Tier A/actionable.
C2a: cỡ mẫu lớn bắt n≥1000 thật, không dính 'Oct 10, 2024'.
C2b: detect_official_org không gán nhầm WHO/ADA/ACC từ chữ thường.
C2c: dedup không gộp guideline/RCT khác năm-phiên bản.
"""
from __future__ import annotations

from app.scoring import evidence_quality_score, practice_change_score, reliability_tier
from app.services.deduplication import deduplicate
from app.services.filtering import classify
from app.sources.classify_meta import detect_official_org

# ---- C1 ----

def test_regulatory_single_line_not_actionable():
    item = {"study_type": "regulatory_alert",
            "title": "FDA: clinicians should avoid drug X",
            "abstract": "short safety communication",
            "safety_signal": "avoid drug X"}
    eq, _ = evidence_quality_score(item)
    pc, _ = practice_change_score(item)
    tier = reliability_tier(item, eq, pc)
    assert tier != "A", "cảnh báo 1 dòng không được lên Tier A"
    item["evidence_quality_score"] = eq
    item["practice_change_score"] = pc
    item["reliability_tier"] = tier
    classification, is_actionable, _, _ = classify(item)
    assert is_actionable is False
    assert classification != "actionable"


# ---- C2a ----

def test_large_sample_ignores_date_like_tokens():
    eq, b = evidence_quality_score(
        {"study_type": "rct", "title": "Trial reported on Oct 10, 2024", "abstract": "x"})
    assert "large_sample" not in b


def test_large_sample_detects_real_n():
    _, b = evidence_quality_score(
        {"study_type": "rct", "title": "RCT with n = 6,609 patients", "abstract": "x"})
    assert b.get("large_sample") == 3


def test_large_sample_small_n_not_counted():
    _, b = evidence_quality_score(
        {"study_type": "rct", "title": "pilot with n = 8 patients", "abstract": "x"})
    assert "large_sample" not in b


# ---- C2b ----

def test_official_org_no_false_positive_in_title():
    assert detect_official_org("patients who underwent surgery", journal="J Surg") is None
    assert detect_official_org("a cohort study in Canada", journal="Local Journal") is None
    assert detect_official_org("a vaccine trial", journal="Trials") is None


def test_official_org_true_positive_in_journal():
    assert detect_official_org("AF management", journal="European Heart Journal") == "ESC"
    assert detect_official_org("bulletin", journal="WHO Bulletin") == "WHO"


# ---- C2c ----

def test_dedup_keeps_different_year_guidelines():
    items = [
        {"title": "ESC Guideline on Atrial Fibrillation", "study_type": "guideline",
         "journal_or_organization": "ESC", "publication_date": "2020-08-29"},
        {"title": "ESC Guideline on Atrial Fibrillation", "study_type": "guideline",
         "journal_or_organization": "ESC", "publication_date": "2024-08-30"},
    ]
    primary, links = deduplicate(items)
    assert len(primary) == 2, "guideline khác năm KHÔNG được gộp"


def test_dedup_merges_same_year_duplicate():
    items = [
        {"title": "ESC Guideline on Atrial Fibrillation", "study_type": "guideline",
         "journal_or_organization": "ESC", "publication_date": "2024-08-30"},
        {"title": "ESC Guideline on Atrial Fibrillation", "study_type": "guideline",
         "journal_or_organization": "ESC", "publication_date": "2024-08-30"},
    ]
    primary, links = deduplicate(items)
    assert len(primary) == 1, "trùng thật (cùng năm) vẫn phải gộp"
