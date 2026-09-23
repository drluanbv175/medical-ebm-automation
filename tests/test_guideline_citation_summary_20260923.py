"""Kiểm `app/sources/guideline_citation_summary.py` — thêm 23/09/2026, dự phòng
trích dẫn+tóm tắt cho guideline KHÔNG đọc được toàn văn (BTS/Thorax/NICE...).
Tất cả test OFFLINE, không gọi mạng thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.base import RawRecord  # noqa: E402
from app.sources.guideline_citation_summary import lay_trich_dan_tom_tat  # noqa: E402


def _ban_ghi_epmc_co_abstract(**overrides):
    mac_dinh = dict(
        source="europepmc", title="Bai guideline mau", authors="Nguyen A, Tran B",
        journal_or_organization="Journal Mau", publication_date="2026-01-01",
        doi="10.1000/mau", pmid="12345678", abstract="<p>Tom tat that cua bai.</p>",
    )
    mac_dinh.update(overrides)
    return RawRecord(**mac_dinh)


def test_khong_truyen_doi_lan_pmid_tu_choi_ngay_khong_goi_mang(monkeypatch):
    goi_mang = []
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary.EuropePMCClient.search",
        lambda self, *a, **kw: goi_mang.append(a) or [],
    )
    r = lay_trich_dan_tom_tat()
    assert r.thanh_cong is False
    assert goi_mang == []
    assert "cần ít nhất" in r.ghi_chu.lower()


def test_europepmc_co_abstract_duoc_dung_ngay_khong_can_crossref(monkeypatch):
    goi_crossref = []
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary.EuropePMCClient.search",
        lambda self, q, **kw: [_ban_ghi_epmc_co_abstract()],
    )
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary._tra_crossref_truc_tiep",
        lambda doi: goi_crossref.append(doi) or None,
    )
    r = lay_trich_dan_tom_tat(doi="10.1000/mau")
    assert r.thanh_cong is True
    assert r.nguon_tom_tat == "europepmc"
    assert r.tom_tat == "Tom tat that cua bai."  # đã bóc thẻ HTML/JATS
    assert goi_crossref == []  # KHÔNG cần gọi Crossref khi Europe PMC đã có abstract
    assert "không phải toàn văn" in r.ghi_chu.lower()


def test_europepmc_thieu_abstract_thi_bo_sung_tu_crossref(monkeypatch):
    """Europe PMC có bản ghi nhưng KHÔNG có abstract — phải thử Crossref để lấp,
    KHÔNG được dừng lại và báo 'không có abstract' quá sớm."""
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary.EuropePMCClient.search",
        lambda self, q, **kw: [_ban_ghi_epmc_co_abstract(abstract=None)],
    )
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary._tra_crossref_truc_tiep",
        lambda doi: RawRecord(source="crossref", abstract="Tom tat tu Crossref.", doi=doi),
    )
    r = lay_trich_dan_tom_tat(doi="10.1000/mau")
    assert r.thanh_cong is True
    assert r.tom_tat == "Tom tat tu Crossref."
    assert r.nguon_tom_tat == "crossref"
    # Metadata (tác giả/tiêu đề) vẫn giữ từ Europe PMC — chỉ abstract lấy từ Crossref.
    assert r.tac_gia == "Nguyen A, Tran B"


def test_ca_hai_nguon_khong_co_abstract_bao_trung_thuc_khong_bia(monkeypatch):
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary.EuropePMCClient.search",
        lambda self, q, **kw: [_ban_ghi_epmc_co_abstract(abstract=None)],
    )
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary._tra_crossref_truc_tiep",
        lambda doi: RawRecord(source="crossref", abstract=None, doi=doi),
    )
    r = lay_trich_dan_tom_tat(doi="10.1000/mau")
    assert r.thanh_cong is True  # vẫn có trích dẫn thật
    assert r.tom_tat is None
    assert r.nguon_tom_tat is None
    assert "không có abstract công khai" in r.ghi_chu.lower()


def test_ca_hai_nguon_deu_khong_tim_thay_that_bai_trung_thuc(monkeypatch):
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary.EuropePMCClient.search",
        lambda self, q, **kw: [],
    )
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary._tra_crossref_truc_tiep",
        lambda doi: None,
    )
    r = lay_trich_dan_tom_tat(doi="10.1000/khong-ton-tai")
    assert r.thanh_cong is False
    assert "không bịa trích dẫn" in r.ghi_chu.lower()


def test_europepmc_loi_mang_khong_lam_sap_toan_bo_khong_raise(monkeypatch):
    def _loi(self, q, **kw):
        raise ConnectionError("mat mang")

    monkeypatch.setattr("app.sources.guideline_citation_summary.EuropePMCClient.search", _loi)
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary._tra_crossref_truc_tiep",
        lambda doi: RawRecord(source="crossref", title="Bai", doi=doi),
    )
    r = lay_trich_dan_tom_tat(doi="10.1000/mau")
    assert r.thanh_cong is True  # Crossref vẫn cứu được dù Europe PMC lỗi mạng


def test_dinh_dang_trich_dan_khong_bia_truong_thieu(monkeypatch):
    """Bản ghi thiếu tác giả (thường gặp — nhiều bản ghi Crossref không có author) —
    trích dẫn chỉ ghép trường THẬT CÓ, không chèn chuỗi rỗng/None."""
    monkeypatch.setattr(
        "app.sources.guideline_citation_summary.EuropePMCClient.search",
        lambda self, q, **kw: [RawRecord(source="europepmc", title="Chi co tieu de", doi="10.1000/x")],
    )
    r = lay_trich_dan_tom_tat(doi="10.1000/x")
    assert r.thanh_cong is True
    assert "None" not in r.trich_dan
    assert r.trich_dan.startswith("Chi co tieu de.")


def test_pmid_dung_truy_van_chinh_xac_khong_tim_mo(monkeypatch):
    """Phải dùng cú pháp EXT_ID chính xác — không phải query mờ dễ trả nhầm bài."""
    truy_van_thuc = {}

    def _bat_truy_van(self, q, **kw):
        truy_van_thuc["q"] = q
        return [_ban_ghi_epmc_co_abstract()]

    monkeypatch.setattr("app.sources.guideline_citation_summary.EuropePMCClient.search", _bat_truy_van)
    lay_trich_dan_tom_tat(pmid="12345678")
    assert truy_van_thuc["q"] == "EXT_ID:12345678 AND SRC:MED"
