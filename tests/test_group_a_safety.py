"""Nhóm A — an toàn kỹ thuật: XXE, rate-limit, chống CSV formula injection."""
from __future__ import annotations

import time

import pytest

# ---- 4.A1: XXE / billion-laughs ----

_XXE_ENTITY = (
    '<?xml version="1.0"?>'
    '<!DOCTYPE r [<!ENTITY a "AAA">]>'
    '<PubmedArticleSet>&a;</PubmedArticleSet>'
)


def test_defusedxml_blocks_entity_expansion():
    from defusedxml.common import EntitiesForbidden
    from defusedxml.ElementTree import fromstring
    with pytest.raises(EntitiesForbidden):
        fromstring(_XXE_ENTITY)


def test_pubmed_parse_handles_xxe_gracefully():
    # Connector phải BẮT lỗi và trả [] (không expand entity, không crash).
    from app.sources.pubmed import PubMedClient
    out = PubMedClient()._parse_efetch(_XXE_ENTITY, "Tim mạch", "q")
    assert out == []


def test_pubmed_parse_normal_xml_ok():
    from app.sources.pubmed import PubMedClient
    xml = ('<PubmedArticleSet><PubmedArticle><MedlineCitation>'
           '<PMID>123</PMID><Article><ArticleTitle>Test AF guideline</ArticleTitle>'
           '<Abstract><AbstractText>multicenter outcome</AbstractText></Abstract>'
           '</Article></MedlineCitation></PubmedArticle></PubmedArticleSet>')
    out = PubMedClient()._parse_efetch(xml, "Tim mạch", "q")
    assert len(out) == 1
    assert out[0].title == "Test AF guideline"


# ---- 4.A2: rate-limit theo host ----

def test_throttle_spaces_same_host():
    from app.utils import http
    http._last_request_at.clear()
    t0 = time.monotonic()
    http._throttle("https://eutils.example/a", 0.05)  # đầu tiên: không chờ
    http._throttle("https://eutils.example/b", 0.05)  # cùng host: chờ ~0.05s
    assert time.monotonic() - t0 >= 0.045


def test_throttle_zero_disabled():
    from app.utils import http
    http._last_request_at.clear()
    t0 = time.monotonic()
    http._throttle("https://h/a", 0)
    http._throttle("https://h/a", 0)
    assert time.monotonic() - t0 < 0.03


# ---- 4.A5: chống CSV/Excel formula injection ----

@pytest.mark.parametrize("bad", ["=1+1", "+1", "-1", "@SUM(A1)", "\tx", "\rx"])
def test_safe_cell_escapes_formula(bad):
    from app.reports.exporters import _safe_cell
    assert _safe_cell(bad).startswith("'")


def test_safe_cell_keeps_normal_values():
    from app.reports.exporters import _safe_cell
    assert _safe_cell("CHA2DS2-VA") == "CHA2DS2-VA"
    assert _safe_cell("") == ""
    assert _safe_cell(42) == 42
    assert _safe_cell(None) is None
