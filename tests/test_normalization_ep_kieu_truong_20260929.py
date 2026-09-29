"""Hồi quy 29/09/2026: mọi trường văn bản/danh sách của RawRecord được ép kiểu ở normalization.

Cùng họ lỗi `publication_date` số nguyên của CORE (làm sập cả lượt quét live): dataclass khai
`Optional[str]` nhưng không cưỡng chế. Ca nguy hiểm nhất đo được trên mã: guideline có
`journal_or_organization` dạng DANH SÁCH (kiểu Crossref `container-title`) ⇒
`deduplication._key_for` gọi `.lower()` trên list ⇒ AttributeError. Offline, không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.deduplication import deduplicate  # noqa: E402
from app.services.normalization import _chuoi_hoac_none, _danh_sach_chuoi, normalize  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402


@pytest.mark.parametrize("vao,ra", [
    (None, None), (True, None), ({"name": "X"}, None), ("", None), ("  ", None),
    ("  Lancet ", "Lancet"), (2, "2"), (2.0, "2.0"),
    (["Circulation"], "Circulation"), (["A", None, "", "B"], "A; B"), ([], None), (("x",), "x"),
])
def test_chuoi_hoac_none(vao, ra):
    assert _chuoi_hoac_none(vao) == ra


@pytest.mark.parametrize("vao,ra", [
    (None, []), ("", []), ("copd", ["copd"]), (["a", None, "", 3], ["a", "3"]),
    ({"k": 1}, []), (5, ["5"]), ({"x"}, ["x"]),
])
def test_danh_sach_chuoi(vao, ra):
    assert _danh_sach_chuoi(vao) == ra


def test_normalize_moi_truong_van_ban_la_chuoi_hoac_none():
    rec = RawRecord(source="crossref", title=["Heart failure guideline"], authors=["Smith J", "Doe A"],
                    journal_or_organization=["Circulation"], doi=["10.1/ABC"], pmid=12345,
                    url=None, document_type=["journal-article"], study_type="guideline",
                    guideline_version=2024, keywords=["hf", None], mesh_terms=None,
                    official_grade={"level": "A"})
    it = normalize(rec)
    assert it["title"] == "Heart failure guideline"
    assert it["authors"] == "Smith J; Doe A"
    assert it["journal_or_organization"] == "Circulation"
    assert it["doi"] == "10.1/abc" and it["pmid"] == "12345"
    assert it["document_type"] == "journal-article" and it["guideline_version"] == "2024"
    assert it["keywords"] == ["hf"] and it["mesh_terms"] == []
    assert it["official_grade"] is None


def test_khu_trung_guideline_khong_sap_khi_ten_to_chuc_la_danh_sach():
    a = normalize(RawRecord(source="crossref", title="ESC Guidelines for heart failure",
                            journal_or_organization=["European Heart Journal"], study_type="guideline",
                            publication_date="2023"))
    b = normalize(RawRecord(source="rss", title="ESC Guidelines for heart failure",
                            journal_or_organization="European Heart Journal", study_type="guideline",
                            publication_date="2023-08-25"))
    primary, links = deduplicate([a, b])
    assert primary == [0] and len(links) == 1


def test_gia_tri_chuoi_binh_thuong_giu_nguyen():
    rec = RawRecord(source="pubmed", title="DAPA-HF", authors="McMurray JJV", journal_or_organization="N Engl J Med",
                    pmid="31535829", abstract="Background: x", keywords=["sglt2"], mesh_terms=["Heart Failure"])
    it = normalize(rec)
    assert (it["authors"], it["journal_or_organization"], it["pmid"]) == ("McMurray JJV", "N Engl J Med", "31535829")
    assert it["keywords"] == ["sglt2"] and it["mesh_terms"] == ["Heart Failure"]
    assert it["abstract"].startswith("Background")
