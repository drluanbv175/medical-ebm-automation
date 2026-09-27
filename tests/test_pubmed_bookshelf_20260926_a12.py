"""PMID của NCBI Bookshelf (PubmedBookArticle) không còn bị gắn «nghi trích dẫn ma» ở cổng A12.

Vá 26/09/2026 (phát hiện #29). PubMed efetch trả tài liệu Bookshelf (StatPearls, GeneReviews, guideline NICE
dạng sách…) trong `<PubmedBookArticle>` với PMID ở `BookDocument/PMID`. Hai parser của A12 trước đây chỉ duyệt
`.//PubmedArticle`, nên PMID sách luôn ra 'unresolved' ⇒ receipt ghi «nghi ma» ⇒ G10 chặn oan.

Hợp đồng được khoá ở đây:
  • metadata ⇒ "resolved"; tác giả KHÔNG lẫn biên tập viên; bản ghi cả cuốn không có ArticleTitle ⇒ BookTitle;
  • rút bài ⇒ "ok" kèm `loai_ban_ghi`/`ghi_chu` — KHÔNG tạo trạng thái mới;
  • không nhặt PMID/DOI trong danh mục tham khảo của sách;
  • `_parse_efetch` (dây chuyền khám phá) KHÔNG đổi.

Fixture dựng theo DTD pubmed_250101 (PubmedBookArticle > BookDocument/PubmedBookData), không gọi mạng.
"""
from __future__ import annotations

import pytest

from app.sources.pubmed import GHI_CHU_RUT_BAI_SACH, LOAI_BAN_GHI_SACH, PubMedClient

_SACH_STATPEARLS = """
  <PubmedBookArticle>
    <BookDocument>
      <PMID Version="1">31111111</PMID>
      <ArticleIdList>
        <ArticleId IdType="bookaccession">NBK999999</ArticleId>
        <ArticleId IdType="doi">10.9999/statpearls.chapter</ArticleId>
      </ArticleIdList>
      <Book>
        <Publisher><PublisherName>StatPearls Publishing</PublisherName></Publisher>
        <BookTitle book="statpearls">StatPearls</BookTitle>
        <PubDate><Year>2025</Year><Month>01</Month></PubDate>
        <AuthorList Type="editors">
          <Author><LastName>Editorson</LastName><ForeName>Eve</ForeName><Initials>E</Initials></Author>
          <Author><LastName>Redactor</LastName><ForeName>Rex</ForeName><Initials>R</Initials></Author>
        </AuthorList>
      </Book>
      <ArticleTitle book="statpearls" part="article-1">Essential <i>Hypertension</i></ArticleTitle>
      <AuthorList Type="authors">
        <Author><LastName>Chapman</LastName><ForeName>Carl</ForeName><Initials>C</Initials></Author>
        <Author><LastName>Writer</LastName><ForeName>Wendy</ForeName><Initials>W</Initials></Author>
      </AuthorList>
      <PublicationType UI="D016454">Review</PublicationType>
      <ReferenceList>
        <Reference>
          <Citation>Ref paper.</Citation>
          <ArticleIdList>
            <ArticleId IdType="pubmed">12345678</ArticleId>
            <ArticleId IdType="doi">10.1000/reference.doi</ArticleId>
          </ArticleIdList>
        </Reference>
      </ReferenceList>
    </BookDocument>
    <PubmedBookData>
      <PublicationStatus>ppublish</PublicationStatus>
      <ArticleIdList><ArticleId IdType="pubmed">31111111</ArticleId></ArticleIdList>
    </PubmedBookData>
  </PubmedBookArticle>
"""

# Bản ghi CẢ CUỐN (vd guideline NICE): không có ArticleTitle, không có BookDocument/AuthorList;
# tác giả tập thể khai ở Book/AuthorList Type="authors", biên tập viên ở Type="editors".
_SACH_CA_CUON_NICE = """
  <PubmedBookArticle>
    <BookDocument>
      <PMID Version="1">33333333</PMID>
      <ArticleIdList><ArticleId IdType="bookaccession">NBK888888</ArticleId></ArticleIdList>
      <Book>
        <Publisher><PublisherName>NICE</PublisherName></Publisher>
        <BookTitle book="nicecg">Hypertension in adults: diagnosis and management</BookTitle>
        <PubDate><Year>2023</Year></PubDate>
        <AuthorList Type="authors">
          <Author><CollectiveName>National Guideline Centre (UK)</CollectiveName></Author>
        </AuthorList>
        <AuthorList Type="editors"><Author><LastName>Boss</LastName><Initials>B</Initials></Author></AuthorList>
      </Book>
      <PublicationType UI="D017065">Practice Guideline</PublicationType>
    </BookDocument>
    <PubmedBookData><PublicationStatus>ppublish</PublicationStatus></PubmedBookData>
  </PubmedBookArticle>
"""

_BAI_BAO = """
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">32222222</PMID>
      <Article>
        <Journal><Title>The Lancet</Title></Journal>
        <ArticleTitle>A normal journal article</ArticleTitle>
        <AuthorList><Author><LastName>Nguyen</LastName><Initials>A</Initials></Author></AuthorList>
        <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList><ArticleId IdType="pubmed">32222222</ArticleId></ArticleIdList>
    </PubmedData>
  </PubmedArticle>
"""


def _xml(*phan: str) -> str:
    return '<?xml version="1.0"?>\n<PubmedArticleSet>' + "".join(phan) + "</PubmedArticleSet>"


# ---------------------------------------------------------------- metadata

def test_metadata_sach_don_le_resolved_khong_lan_bien_tap_vien():
    kq = PubMedClient._parse_metadata_xml(_xml(_SACH_STATPEARLS), ["31111111"])["31111111"]
    assert kq["status"] == "resolved"
    assert kq["loai_ban_ghi"] == LOAI_BAN_GHI_SACH
    assert kq["title"] == "Essential Hypertension"
    assert kq["journal"] == "StatPearls"
    assert kq["year"] == "2025"
    assert kq["authors"] == "Chapman C, Writer W"
    assert "Editorson" not in kq["authors"] and "Redactor" not in kq["authors"]
    # DOI của CHÍNH tài liệu — không phải DOI trong danh mục tham khảo.
    assert kq["doi"] == "10.9999/statpearls.chapter"


def test_metadata_ban_ghi_ca_cuon_lui_ve_book_title():
    kq = PubMedClient._parse_metadata_xml(_xml(_SACH_CA_CUON_NICE), ["33333333"])["33333333"]
    assert kq["status"] == "resolved"
    assert kq["title"] == "Hypertension in adults: diagnosis and management"
    assert kq["authors"] == "National Guideline Centre (UK)"
    assert "Boss" not in (kq["authors"] or "")
    assert kq["doi"] is None
    assert kq["year"] == "2023"


def test_metadata_lo_lan_sach_va_bai_bao():
    kq = PubMedClient._parse_metadata_xml(_xml(_BAI_BAO, _SACH_STATPEARLS), ["32222222", "31111111"])
    assert kq["32222222"]["status"] == "resolved"
    assert "loai_ban_ghi" not in kq["32222222"]
    assert kq["31111111"]["status"] == "resolved"


def test_metadata_pmid_trong_danh_muc_tham_khao_cua_sach_van_unresolved():
    """PMID 12345678 chỉ xuất hiện trong ReferenceList của sách ⇒ PubMed KHÔNG trả bản ghi cho nó."""
    kq = PubMedClient._parse_metadata_xml(_xml(_SACH_STATPEARLS), ["31111111", "12345678"])
    assert kq["31111111"]["status"] == "resolved"
    assert kq["12345678"]["status"] == "unresolved"


# ---------------------------------------------------------------- rút bài

def test_rut_bai_sach_don_le_ok_kem_ghi_chu():
    kq = PubMedClient._parse_retraction_xml(_xml(_SACH_STATPEARLS), ["31111111"])["31111111"]
    assert kq["status"] == "ok"
    assert kq["loai_ban_ghi"] == LOAI_BAN_GHI_SACH
    assert kq["ghi_chu"] == GHI_CHU_RUT_BAI_SACH
    assert "Retraction Watch" in kq["ghi_chu"]


def test_rut_bai_lo_lan_khong_con_unresolved():
    kq = PubMedClient._parse_retraction_xml(_xml(_SACH_STATPEARLS, _BAI_BAO), ["32222222", "31111111"])
    assert kq == {
        "32222222": {"status": "ok"},
        "31111111": {"status": "ok", "loai_ban_ghi": LOAI_BAN_GHI_SACH, "ghi_chu": GHI_CHU_RUT_BAI_SACH},
    }


def test_rut_bai_ca_cuon_ok():
    kq = PubMedClient._parse_retraction_xml(_xml(_SACH_CA_CUON_NICE), ["33333333"])["33333333"]
    assert kq["status"] == "ok"


def test_rut_bai_sach_mang_co_retracted_van_duong_tinh():
    """Nếu NLM có gắn PublicationType rút bài cho sách thì vẫn DƯƠNG TÍNH như bài báo, không bị nuốt thành ok."""
    sach_rut = _SACH_STATPEARLS.replace(
        '<PublicationType UI="D016454">Review</PublicationType>',
        '<PublicationType UI="D016454">Review</PublicationType>'
        '<PublicationType UI="D016441">Retracted Publication</PublicationType>')
    kq = PubMedClient._parse_retraction_xml(_xml(sach_rut), ["31111111"])["31111111"]
    assert kq["status"] == "retracted"


def test_rut_bai_pmid_tham_khao_khong_bi_nhan_la_ban_ghi():
    kq = PubMedClient._parse_retraction_xml(_xml(_SACH_STATPEARLS), ["12345678"])
    assert kq["12345678"]["status"] == "unresolved"


@pytest.mark.parametrize("parser", [PubMedClient._parse_retraction_xml, PubMedClient._parse_metadata_xml])
def test_khong_tao_trang_thai_moi(parser):
    """Trạng thái của sách phải nằm trong tập đã biết — một tên lạ từng bị blacklist A12 coi là SẠCH."""
    kq = parser(_xml(_SACH_STATPEARLS, _SACH_CA_CUON_NICE), ["31111111", "33333333"])
    for v in kq.values():
        assert v["status"] in {"ok", "resolved"}


# ---------------------------------------------------------------- ranh giới phạm vi

def test_parse_efetch_kham_pha_khong_doi():
    """Dây chuyền khám phá cố ý KHÔNG nhận sách (việc riêng, tránh bơm StatPearls/NICE vào ingestion)."""
    ban_ghi = PubMedClient()._parse_efetch(_xml(_BAI_BAO, _SACH_STATPEARLS), None, "q")
    assert [r.pmid for r in ban_ghi] == ["32222222"]
