"""2026-07-11 (round 19 security review): text nguồn NGOÀI (PubMed/RSS/openFDA — vd
title/safety_signal) được đưa thẳng vào Markdown rồi convert sang HTML tĩnh
(EBM_Weekly_Update_*.html, Alert_Digest_*.html) mà KHÔNG escape — nếu title/safety_signal
chứa thẻ HTML/script, mở file HTML tĩnh này bằng trình duyệt sẽ thực thi. Vá bằng
html.escape() tại điểm dựng dữ liệu (weekly_ebm._row) / điểm render (alert_digest._bullets).
"""
from __future__ import annotations

from types import SimpleNamespace

PAYLOAD = "<img src=x onerror=alert(document.domain)>"


def _fake_evidence_item(**overrides):
    base = dict(
        id=1, clinical_area="Tim mạch", title=PAYLOAD,
        journal_or_organization=None, source="pubmed",
        study_type="rct", document_type="article",
        operational_evidence_level="B", official_grade=None,
        evidence_quality_score=70, practice_change_score=50,
        reliability_tier="A", is_actionable=True, classification="actionable",
        actionable_reason="test", reason_for_exclusion=None,
        safety_signal=PAYLOAD, doi="10.1/x", pmid="123456",
        nct_id=None, url="https://example.org", publication_date="2026-01-01",
        authors="A, B", synthesis={}, first_seen_run_id=1, is_mock=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_weekly_ebm_row_escapes_external_text():
    from app.reports.weekly_ebm import _row

    row = _row(_fake_evidence_item())
    assert "<img" not in row["title"]
    assert "&lt;img" in row["title"]
    assert "<img" not in row["safety_signal"]
    assert "&lt;img" in row["safety_signal"]


def test_weekly_ebm_md_table_output_has_no_raw_tag():
    from app.reports.weekly_ebm import _md_table, _row

    row = _row(_fake_evidence_item())
    table = _md_table(["Tiêu đề", "Tín hiệu"], [[row["title"], row["safety_signal"]]])
    assert "<img" not in table


def test_alert_digest_bullets_escapes_external_text():
    from app.reports.alert_digest import _bullets

    out = _bullets([_fake_evidence_item()])
    rendered = "\n".join(out)
    assert "<img" not in rendered
    assert "&lt;img" in rendered
