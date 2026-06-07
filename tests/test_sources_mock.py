"""Test API client hoạt động ở chế độ mock (không gọi mạng thật)."""
from app.sources.crossref import CrossrefClient
from app.sources.openfda import OpenFDAClient
from app.sources.pubmed import PubMedClient


def test_pubmed_mock_returns_records():
    client = PubMedClient()
    assert client.use_mock is True
    recs = client.search("atrial fibrillation", clinical_area="Tim mạch")
    assert len(recs) >= 1
    assert all(r.source == "pubmed" for r in recs)
    assert all(r.raw.get("_mock") for r in recs)


def test_crossref_mock_has_doi():
    recs = CrossrefClient().search("chronic kidney disease", clinical_area="Thận")
    assert any(r.doi for r in recs)


def test_openfda_mock_is_drug_safety():
    recs = OpenFDAClient().search("sglt2")
    assert recs, "openFDA mock phải trả ít nhất 1 tín hiệu"
    assert all(r.source_type == "drug_safety" for r in recs)
    # Phải có ghi chú không kết luận nhân quả
    assert any("nhân quả" in (r.safety_signal or "").lower() for r in recs)
