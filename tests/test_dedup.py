"""Test deduplication theo DOI/PMID/title similarity."""
from app.services.deduplication import deduplicate


def test_dedup_by_doi():
    items = [
        {"title": "A", "doi": "10.1/x"},
        {"title": "A bis", "doi": "10.1/x"},  # cùng DOI -> trùng
        {"title": "B", "doi": "10.2/y"},
    ]
    primary, links = deduplicate(items)
    assert len(primary) == 2
    assert len(links) == 1
    assert links[0][2] == "doi"


def test_dedup_by_pmid():
    items = [
        {"title": "Foo", "pmid": "111"},
        {"title": "Bar", "pmid": "111"},
    ]
    primary, links = deduplicate(items)
    assert len(primary) == 1
    assert links[0][2] == "pmid"


def test_dedup_by_title_similarity():
    items = [
        {"title": "Empagliflozin in Patients with Chronic Kidney Disease"},
        {"title": "Empagliflozin in patients with chronic kidney disease!!"},
    ]
    primary, links = deduplicate(items)
    assert len(primary) == 1
    assert links[0][2] == "title_similarity"


def test_no_false_merge():
    items = [{"title": "Stroke trial", "doi": "10.1/a"},
             {"title": "Diabetes guideline", "doi": "10.2/b"}]
    primary, links = deduplicate(items)
    assert len(primary) == 2
    assert links == []
