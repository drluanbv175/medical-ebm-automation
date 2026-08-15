"""Test báo cáo An toàn thuốc & Kháng sinh tuần."""
from app.reports.safety_reports import (
    build_antibiotic_data,
    build_drug_safety_data,
    render_antibiotic_md,
    render_drug_safety_md,
)
from app.services.pipeline import run_pipeline


def test_drug_safety_report_separates_regulatory_and_faers():
    run_pipeline(max_results_per_query=10)
    data = build_drug_safety_data()
    md = render_drug_safety_md(data)
    assert "Cảnh báo chính thức" in md
    assert "KHÔNG" in md and "nhân quả" in md.lower()
    assert "regulatory" in data["counts"]


def test_antibiotic_report_mentions_aware_and_no_overuse():
    run_pipeline(max_results_per_query=10)
    data = build_antibiotic_data()
    md = render_antibiotic_md(data)
    assert "AWaRe" in md
    assert "không cổ vũ lạm dụng" in md.lower()
