"""Hồi quy 25/09/2026: PubMed «lấy đủ rồi chọn mạnh nhất» (audit/15 §7sexies).

Trước bản vá, `_live_search` sắp theo NGÀY rồi cắt `max_results` ⇒ trả 10 bài MỚI NHẤT; đo sống
trên 6 bệnh ngoại trú cho 0/15 guideline chuẩn lọt vào. Test OFFLINE: HttpClient giả, XML dựng tay.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources import pubmed as P  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402


def _bai(pmid, tieu_de, nam, pts):
    pt = "".join(f"<PublicationType>{p}</PublicationType>" for p in pts)
    return (f"<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article>"
            f"<Journal><Title>J</Title><JournalIssue><PubDate><Year>{nam}</Year></PubDate></JournalIssue></Journal>"
            f"<ArticleTitle>{tieu_de}</ArticleTitle><PublicationTypeList>{pt}</PublicationTypeList>"
            f"</Article></MedlineCitation></PubmedArticle>")


BAI = {
    "1": ("Small new review of hypertension apps", 2026, ["Systematic Review"]),
    "2": ("Therapeutic apheresis guideline", 2026, ["Practice Guideline"]),          # lạc đề
    "3": ("2025 AHA/ACC Guideline for High Blood Pressure in Adults", 2025, ["Practice Guideline"]),
    "4": ("New RCT in hypertension", 2026, ["Randomized Controlled Trial"]),
    "5": ("Retracted hypertension guideline", 2026, ["Practice Guideline", "Retracted Publication"]),
    "6": ("2024 ESC Guidelines for elevated blood pressure and hypertension", 2024, ["Guideline"]),
}


class _HttpGia:
    def __init__(self, ids_moi, ids_gl):
        self.ids_moi, self.ids_gl, self.goi = ids_moi, ids_gl, []

    def get_json(self, url, params=None, **kw):
        self.goi.append(dict(params))
        ids = self.ids_gl if params.get("sort") == "relevance" else self.ids_moi
        return {"esearchresult": {"idlist": ids[: params["retmax"]]}}

    def get_text(self, url, params=None, **kw):
        ids = params["id"].split(",")
        return "<PubmedArticleSet>" + "".join(_bai(i, *BAI[i]) for i in ids) + "</PubmedArticleSet>"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "ncbi_email", "test@example.com")
    monkeypatch.setattr(settings, "ncbi_api_key", "")
    c = P.PubMedClient()
    monkeypatch.setattr(c, "use_mock", False)
    monkeypatch.setattr(c, "save_raw", lambda *a, **k: None)
    return c


def test_hang_do_manh():
    assert P.hang_do_manh(["Practice Guideline"]) == 0
    assert P.hang_do_manh(["Consensus Statement"]) == 0
    assert P.hang_do_manh(["Meta-Analysis"]) == 1
    assert P.hang_do_manh(["Randomized Controlled Trial"]) == 2
    assert P.hang_do_manh(["Journal Article"]) == 3
    assert P.hang_do_manh(["Practice Guideline", "Retracted Publication"]) == 9


def test_guideline_sat_chu_de_dung_dau_bai_moi_nho_bi_day_xuong(client, monkeypatch):
    monkeypatch.setattr(settings, "pubmed_chon_manh_nhat", True)
    client.http = _HttpGia(ids_moi=["1", "4", "2", "5"], ids_gl=["3", "6", "2"])
    out = client.search("hypertension guideline", max_results=3)
    assert [r.pmid for r in out] == ["3", "6", "2"]
    # vùng rộng: làn mới nhất xin tới VUNG_MOI_NHAT, làn guideline sort=relevance
    moi = [g for g in client.http.goi if g["sort"] == "date"]
    gl = [g for g in client.http.goi if g["sort"] == "relevance"]
    assert moi[0]["retmax"] == P.VUNG_MOI_NHAT and gl and P.GUIDELINE_FILTER in gl[0]["term"]


def test_bai_bi_rut_xep_cuoi_nhung_khong_bi_vut(client, monkeypatch):
    monkeypatch.setattr(settings, "pubmed_chon_manh_nhat", True)
    client.http = _HttpGia(ids_moi=["5", "1"], ids_gl=[])
    out = client.search("hypertension", max_results=5)
    assert [r.pmid for r in out] == ["1", "5"]


def test_dong_nghia_tieu_de_high_blood_pressure():
    r = [RawRecord(source="pubmed", title=BAI[i][0], pmid=i, publication_date=str(BAI[i][1]),
                   raw={"publication_types": BAI[i][2]}) for i in ("2", "3")]
    assert [x.pmid for x in P.xep_theo_do_manh(r, "hypertension")] == ["3", "2"]


def test_tat_co_quay_ve_hanh_vi_cu(client, monkeypatch):
    monkeypatch.setattr(settings, "pubmed_chon_manh_nhat", False)
    client.http = _HttpGia(ids_moi=["1", "4"], ids_gl=["3"])
    out = client.search("hypertension", max_results=2)
    assert [r.pmid for r in out] == ["1", "4"]
    assert len(client.http.goi) == 1 and client.http.goi[0]["retmax"] == 2


def test_bo_loc_tuy_chinh_khong_bi_xep_lai(client, monkeypatch):
    monkeypatch.setattr(settings, "pubmed_chon_manh_nhat", True)
    client.http = _HttpGia(ids_moi=["1", "4"], ids_gl=["3"])
    out = client.search("hypertension", max_results=2, pubtype_filter=None)
    assert [r.pmid for r in out] == ["1", "4"] and len(client.http.goi) == 1


def test_since_date_ap_cho_ca_lan_guideline(client, monkeypatch):
    monkeypatch.setattr(settings, "pubmed_chon_manh_nhat", True)
    client.http = _HttpGia(ids_moi=["1"], ids_gl=["3"])
    client.search("hypertension", max_results=2, since_date="2026-09-01")
    gl = [g for g in client.http.goi if g["sort"] == "relevance"][0]
    assert gl["mindate"] == "2026/09/01"
