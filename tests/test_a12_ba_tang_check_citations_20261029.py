"""Công cụ gộp `check_citations.py` kiểm rút bài qua CHUỖI 3 TẦNG — 29/10/2026.

Lỗi đã đo trên C1a (đánh giá chéo hội đồng G10, G10-DG-20261028T211140-262b8de6, RQ2): receipt A12 của gói G10 do
`check_citations.py` sinh lấy thẳng kết quả PubMed — mỗi mục chỉ có {"status": "ok"}, không `source`/`sources_tried`,
và tầng Retraction Watch ngoại tuyến không được hỏi (trái CLAUDE.md §6.4). Test chốt:
① bài PubMed báo «ok» nhưng Retraction Watch biết đã rút ⇒ công cụ báo rút bài, mã thoát 1, receipt không sạch;
② PubMed vẫn chỉ bị gọi MỘT lần (efetch gộp) — tầng NCBI của chuỗi dùng lại kết quả đó;
③ receipt ghi nguồn đã hỏi cho từng PMID.
Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402
import check_citations as CC  # noqa: E402

from app.sources.pubmed import PubMedClient  # noqa: E402
from app.sources.retraction_chain import RetractionChain  # noqa: E402

_META_OK = {"status": "resolved", "title": "t", "authors": "a", "journal": "j", "year": "2020", "doi": None}


class _RW:
    """Nền Retraction Watch giả: biết đúng các PMID đã rút được khai."""

    def __init__(self, da_rut: set[str]) -> None:
        self._da_rut = da_rut

    def san_sang(self) -> bool:
        return True

    def tra(self, pmid):
        if pmid in self._da_rut:
            return {"status": "retracted", "source": "retraction_watch", "reason": "Fabrication"}
        return None


class _EP:
    """Europe PMC giả — ghi lại PMID được hỏi, không kết luận gì."""

    def __init__(self) -> None:
        self.hoi: list[list[str]] = []

    def check_retraction_status(self, pmids):
        self.hoi.append(list(pmids))
        return {p: {"status": "unknown_fetch_error"} for p in pmids}

    def fetch_notice_titles(self, pmids):
        return {}


def _chay(monkeypatch, capsys, argv, ncbi: dict, da_rut: set[str], tmp_path=None):
    dem = {"check_citations": 0}

    def _gop(self, pmids):
        dem["check_citations"] += 1
        return {"retraction": ncbi, "metadata": {p: dict(_META_OK) for p in pmids}}

    def _cam(self, *a, **k):  # tầng NCBI của chuỗi KHÔNG được gọi efetch lần hai
        raise AssertionError("check_retraction_status bị gọi lần hai — phải dùng lại kết quả efetch gộp")

    ep = _EP()
    monkeypatch.setattr(PubMedClient, "check_citations", _gop)
    monkeypatch.setattr(PubMedClient, "check_retraction_status", _cam)
    monkeypatch.setattr(PubMedClient, "fetch_metadata", lambda self, pmids: {})
    monkeypatch.setattr(CC, "RetractionChain", lambda pubmed: RetractionChain(rw=_RW(da_rut), pubmed=pubmed,
                                                                             europepmc=ep))
    if tmp_path is not None:
        for mod in (CCR, CCM, CC):
            monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_citations.py", *argv])
    return CC.main(), capsys.readouterr(), dem, ep


def test_rut_bai_chi_retraction_watch_biet_van_bi_bat(monkeypatch, capsys, tmp_path):
    rc, ra, dem, ep = _chay(monkeypatch, capsys, ["--pmids", "30267080,26760044", "--study", "PYTEST-A12-3T"],
                            {"30267080": {"status": "ok"}, "26760044": {"status": "ok"}}, {"30267080"}, tmp_path)
    assert rc == 1 and "30267080" in ra.out
    assert dem["check_citations"] == 1, "PubMed chỉ một lời gọi gộp"
    assert ep.hoi == [], "NCBI đã kết luận cả hai PMID ⇒ không hỏi Europe PMC"
    r = json.loads((tmp_path / "exports" / "PYTEST-A12-3T" / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))
    assert r["all_clean"] is False
    assert r["results"]["30267080"]["status"] == "retracted"
    assert r["results"]["26760044"]["status"] == "ok"
    assert r["results"]["26760044"]["sources_tried"] == ["retraction_watch", "pubmed"], "receipt ghi nguồn đã hỏi"


def test_ncbi_khong_ket_luan_thi_hoi_europepmc(monkeypatch, capsys):
    rc, _ra, dem, ep = _chay(monkeypatch, capsys, ["--pmids", "1,2", "--json"],
                             {"1": {"status": "ok"}, "2": {"status": "unknown_fetch_error"}}, set())
    assert rc == 1 and dem["check_citations"] == 1
    assert ep.hoi == [["2"]], "chỉ PMID NCBI không kết luận được mới hỏi Europe PMC"


def test_doi_chung_moi_tang_sach_thoat_0(monkeypatch, capsys):
    rc, ra, _dem, _ep = _chay(monkeypatch, capsys, ["--pmids", "1"], {"1": {"status": "ok"}}, set())
    assert rc == 0 and "chuỗi 3 tầng" in ra.out and "đã hỏi: retraction_watch, pubmed" in ra.out
