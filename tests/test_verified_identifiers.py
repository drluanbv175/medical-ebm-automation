"""Test độ phủ + tính hợp lệ của PMID/DOI nguồn gốc cho thang điểm verified (CAFÉ-S 3.1).

Bảo vệ chống: (1) tụt độ phủ trích dẫn; (2) PMID/DOI sai định dạng (dấu hiệu bịa); (3) bỏ sót
mapping khi thêm thang mới. KHÔNG gọi mạng — chỉ kiểm dữ liệu tĩnh đã xác minh.
"""
from __future__ import annotations

import re

from app.clinical_scores.verified import (
    VERIFIED_SCORES,
    citation_links,
    identifier_coverage,
)

# 3 thang nguồn báo cáo thể chế/sách — KHÔNG tồn tại PMID/DOI (đã xác nhận PubMed/Crossref = 0).
_NO_IDENTIFIER_OK = {"news2", "nyha", "gold_abe"}


def test_coverage_jumped_from_baseline():
    cov = identifier_coverage()
    assert cov["total"] == 32
    # Mốc cũ 2/32 (6%); mục tiêu vá ≥ 90%.
    assert cov["with_identifier"] >= 29
    assert cov["coverage_pct"] >= 90.0


def test_every_score_has_id_or_is_known_institutional():
    """Mỗi thang phải CÓ pmid/doi, HOẶC nằm trong danh sách nguồn không-định-danh đã biết."""
    for s in VERIFIED_SCORES:
        has_id = bool(s.get("pmid") or s.get("doi"))
        assert has_id or s["score_id"] in _NO_IDENTIFIER_OK, (
            f"{s['score_id']} thiếu pmid/doi và KHÔNG thuộc nhóm báo cáo/sách — "
            f"phải xác minh định danh hoặc giải thích."
        )


def test_pmid_is_digits_only():
    for s in VERIFIED_SCORES:
        if s.get("pmid"):
            assert re.fullmatch(r"\d+", s["pmid"]), f"PMID sai định dạng: {s['score_id']}={s['pmid']}"


def test_doi_format_no_url_prefix():
    for s in VERIFIED_SCORES:
        doi = s.get("doi")
        if doi:
            assert doi.startswith("10."), f"DOI phải bắt đầu '10.': {s['score_id']}={doi}"
            assert "http" not in doi and "doi.org" not in doi, (
                f"DOI không được kèm URL/tiền tố: {s['score_id']}={doi}")


def test_institutional_sources_have_no_fabricated_id():
    for s in VERIFIED_SCORES:
        if s["score_id"] in _NO_IDENTIFIER_OK:
            assert not s.get("pmid") and not s.get("doi"), (
                f"{s['score_id']} là báo cáo/sách — KHÔNG được gán định danh khống.")


def test_citation_links_builds_urls():
    curb = next(s for s in VERIFIED_SCORES if s["score_id"] == "curb65")
    links = citation_links(curb)
    assert links["pubmed"] == "https://pubmed.ncbi.nlm.nih.gov/12728155/"
    assert links["doi"] == "https://doi.org/10.1136/thorax.58.5.377"

    nyha = next(s for s in VERIFIED_SCORES if s["score_id"] == "nyha")
    assert citation_links(nyha) == {"pubmed": None, "doi": None}
