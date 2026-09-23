from __future__ import annotations

from datetime import date

from app.scoring import evidence_quality_score, practice_change_score, reliability_tier
from app.services.filtering import classify
from app.sources.authority import (
    assess_source_universe_coverage,
    match_authority_source,
    source_universe_report,
    trusted_source_names,
)
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


def test_source_universe_documents_all_required_evidence_layers():
    report = source_universe_report()

    assert "bibliographic_core" in report
    assert "guideline_authority" in report
    assert "trial_registries" in report
    assert "drug_safety" in report
    assert "retraction_and_integrity" in report
    assert "pubmed" in report["bibliographic_core"]["sources"]
    assert "clinicaltrials" in report["trial_registries"]["sources"]
    assert "openfda" in report["drug_safety"]["sources"]


def test_source_universe_coverage_separates_required_from_discovery_only():
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 20, phát hiện #4) —
    # "nejm" đổi thành "feed_nejm_current": tên "nejm" trần KHÔNG PHẢI tên
    # healthy_sources mà production thật sinh ra (RSS feed sinh
    # f"feed_{feed.id}", và id thật trong feeds.py là "nejm_current", không
    # phải "nejm") — test cũ vô tình PASS nhờ input giả không đại diện thực
    # tế, đúng nguyên nhân khiến app/sources/authority.py::EVIDENCE_SOURCE_
    # UNIVERSE["high_impact_journals"] không bao giờ PASS trên dữ liệu thật
    # dù feed NEJM đang khoẻ mạnh. Đã vá layer đó khớp tên connector thật;
    # test này cập nhật input theo đúng cùng lý do.
    # SỬA 23/09/2026 (audit/14, vấn đề 1) — thêm "gold_copd_fulltext" cho tầng
    # mới "guideline_fulltext" (source_of_record, nên tính vào required) — đã
    # kiểm sống thật cùng ngày (xem data/sources.json SRC-043), không phải tên
    # giả định.
    coverage = assess_source_universe_coverage([
        "pubmed",
        "europepmc",
        "crossref",
        "openalex",
        "guideline_feeds",
        "feed_nejm_current",
        "clinicaltrials",
        "openfda",
        "pubmed_retraction",
        "unpaywall",
        "gold_copd_fulltext",
    ])

    assert coverage["status"] == "PASS"
    assert coverage["missing_required_layers"] == []
    assert "trial_registries" in coverage["discovery_only_layers"]
    assert coverage["layers"]["trial_registries"]["status"] == "PASS"


def test_source_universe_coverage_fails_closed_without_guideline_and_safety_layers():
    coverage = assess_source_universe_coverage(["pubmed", "europepmc", "crossref", "openalex"])

    assert coverage["status"] == "PARTIAL"
    assert "guideline_authority" in coverage["missing_required_layers"]
    assert "drug_safety" in coverage["missing_required_layers"]
    # Tầng mới cũng phải bị thiếu khi healthy_sources rỗng — nếu không, tầng
    # guideline_fulltext im lặng PASS sai (đúng bẫy "high_impact_journals" đã
    # gặp 05/09/2026 khi tên khai không khớp connector thật).
    assert "guideline_fulltext" in coverage["missing_required_layers"]


def test_source_universe_coverage_new_guideline_fulltext_layer_20260923():
    """Hồi quy audit/14 vấn đề 1 — vá 23/09/2026: taxonomy trước đó KHÔNG có
    tên nào khớp 5 connector toàn văn guideline mới (gold_copd_fulltext,
    gina_asthma_fulltext, bts_guidelines_fulltext, pmc_guideline_fulltext,
    wiley_tdm), nên tầng full-text-guideline không bao giờ PASS được dù
    GOLD/GINA đang hoạt động thật. Kiểm đúng 3 việc: tên khớp SourceClient.name
    thật (không suy đoán) · PASS khi có ≥1 connector khoẻ · not_connected liệt
    đúng 3 connector còn lại."""
    coverage = assess_source_universe_coverage(["gold_copd_fulltext", "gina_asthma_fulltext"])
    layer = coverage["layers"]["guideline_fulltext"]

    assert layer["status"] == "PASS"
    assert layer["clinical_use"] == "source_of_record"
    assert sorted(layer["healthy"]) == ["gina_asthma_fulltext", "gold_copd_fulltext"]
    assert sorted(layer["not_connected"]) == [
        "bts_guidelines_fulltext", "pmc_guideline_fulltext", "wiley_tdm",
    ]
    assert "guideline_fulltext" not in coverage["missing_required_layers"]
