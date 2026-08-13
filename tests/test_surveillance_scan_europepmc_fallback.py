"""Regression cho scanner giám sát chứng cứ định kỳ.

Khi PubMed E-utilities tạm lỗi hoặc trả payload không parse được, hệ chỉ được dùng
Europe PMC như nguồn dự phòng có nhãn rõ để tạo ứng viên review, không được xanh giả.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_scanner():
    path = Path(__file__).resolve().parents[2] / "EBM-Dashboards" / "tools" / "surveillance_scan.py"
    spec = importlib.util.spec_from_file_location("surveillance_scan_runtime", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_search_falls_back_to_europepmc_when_pubmed_runtime_fails(monkeypatch):
    scanner = _load_scanner()
    calls: list[tuple[str, int, int]] = []

    def fake_fallback(query: str, days: int, retmax: int) -> list[str]:
        calls.append((query, days, retmax))
        return ["42119588"]

    monkeypatch.setattr(scanner, "search_europe_pmc", fake_fallback)

    ids = scanner.search(
        "type 2 diabetes guideline",
        30,
        1,
        fetch_json=lambda _url: (_ for _ in ()).throw(RuntimeError("NCBI returned HTML")),
    )

    assert ids == ["42119588"]
    assert calls == [("type 2 diabetes guideline", 30, 1)]


def test_summarize_falls_back_with_explicit_source_label(monkeypatch):
    scanner = _load_scanner()

    def fake_summary(ids):
        return [
            scanner.Candidate(
                pmid=ids[0],
                publication_date="2026-08-01",
                title="Guideline update",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{ids[0]}/",
                source="Europe PMC fallback for PMID",
            )
        ]

    monkeypatch.setattr(scanner, "summarize_europe_pmc", fake_summary)

    candidates = scanner.summarize(
        ["42119588"],
        fetch_json=lambda _url: (_ for _ in ()).throw(RuntimeError("NCBI returned HTML")),
    )

    assert candidates[0].pmid == "42119588"
    assert candidates[0].source == "Europe PMC fallback for PMID"


def test_scanner_labels_trusted_authority_sources():
    scanner = _load_scanner()

    candidates = scanner.summarize(
        ["42119588"],
        fetch_json=lambda _url: {
            "result": {
                "uids": ["42119588"],
                "42119588": {
                    "title": "Multicenter randomized outpatient trial",
                    "pubdate": "2026 Aug",
                    "source": "The Lancet",
                },
            }
        },
    )

    assert candidates[0].journal_or_organization == "The Lancet"
    assert candidates[0].authority_source == "The Lancet"


def test_pubmed_live_adapter_falls_back_to_europepmc_for_pmid(monkeypatch):
    from app.config import settings
    from app.evidence.live_adapters.registry_adapters import PubMedLiveAdapter

    class FakeHttp:
        def get_text(self, *_args, **_kwargs):
            raise RuntimeError("NCBI returned HTML")

        def get_json(self, *_args, **_kwargs):
            return {
                "resultList": {
                    "result": [
                        {
                            "title": "CONSORT explanation and elaboration",
                            "authorString": "Moher D et al.",
                            "firstPublicationDate": "2010-03-23",
                            "pubType": "journal article",
                        }
                    ]
                }
            }

    monkeypatch.setattr(settings, "ncbi_email", "doctor@example.com")
    adapter = PubMedLiveAdapter()
    adapter.http = FakeHttp()

    result = adapter.lookup({"pmid": "20332511"})

    assert result.found is True
    assert result.raw["fallback_source"] == "Europe PMC"
