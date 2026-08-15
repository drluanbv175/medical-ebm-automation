"""Parser PubMed phải trả DOI CỦA CHÍNH BÀI, không phải DOI trong danh mục
tham khảo — vá 2026-08-14 (`app/sources/pubmed.py::_own_article_doi`).

LỖI CÓ THẬT, ĐO ĐƯỢC, không phải giả định. `_parse_efetch()` và
`_parse_metadata_xml()` cùng dùng `art.findall(".//ArticleId")`: trục `.//` quét
TOÀN BỘ cây con `<PubmedArticle>` nên với tới cả
`PubmedData/ReferenceList/Reference/ArticleIdList/ArticleId` — DOI của những bài
NẰM TRONG DANH MỤC THAM KHẢO. Vòng lặp lại KHÔNG `break` nên giá trị bị GHI ĐÈ
tới cuối, và bên thắng cuộc là tài liệu tham khảo CUỐI CÙNG.

Ca thật: PMID 30267080 (Choi và cs., JAMA Oncology 2019) — parser cũ trả
`10.1159/000096313` (tiền tố 10.1159 = nhà xuất bản Karger, thuộc tham khảo thứ
32/32, PMID 17164558) thay vì DOI thật `10.1001/jamaoncol.2018.4070`. Quét 10
PMID có thật ngày 14/08: 3 bài sai — và cả 3 đều là bài PubMed trả kèm
`<ReferenceList>` có DOI. Bài không kèm ReferenceList vẫn cho DOI đúng, nên lỗi
ẩn mình rất lâu.

VÌ SAO ĐÁNG CHẶN BẰNG TEST: DOI này chảy thẳng vào cổng A12
(`tools/check_citations.py`, `tools/check_citation_retraction.py`) để đối chiếu
Crossref. DOI của bài KHÁC làm cổng báo "không khớp" trên một trích dẫn LÀNH —
hoặc tệ hơn, khớp trót lọt với một bài không liên quan. Báo động giả nặng hơn
không kiểm (CLAUDE.md), vì nó làm mất niềm tin vào cảnh báo thật.

Fixture dưới đây là XML THẬT (rút gọn) lấy từ `efetch.fcgi?db=pubmed&id=30267080`
ngày 14/08/2026 — giữ nguyên nội dung khối `ArticleIdList` của chính bài, khối
`ELocationID`, và hai `<Reference>` (mục cuối chính là mục Karger đã gây lỗi);
chỉ tách chuỗi thành nhiều dòng cho vừa giới hạn 120 ký tự của `ruff`. Test chạy
NGOẠI TUYẾN, không cần mạng, cùng quy ước tests/test_check_citation_retraction.py.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.sources.pubmed import (  # noqa: E402
    PubMedClient,
    _own_article_doi,
    _own_article_pmid,
)

# DOI thật của bài (JAMA Network — tiền tố 10.1001).
OWN_DOI = "10.1001/jamaoncol.2018.4070"
# DOI của THAM KHẢO CUỐI CÙNG — giá trị mà parser hỏng từng trả ra (Karger).
LAST_REFERENCE_DOI = "10.1159/000096313"
# DOI của tham khảo ĐẦU TIÊN — dùng cho test chống phụ thuộc thứ tự phần tử.
FIRST_REFERENCE_DOI = "10.1016/S2468-1253(18)30056-6"

# ── XML THẬT (rút gọn) — PMID 30267080, lấy từ efetch.fcgi ngày 14/08/2026 ──
# Tách thành các khối hằng để (a) không vượt 120 ký tự/dòng, (b) test bên dưới
# thay/đảo khối bằng CHÍNH hằng này thay vì chép lại chuỗi dài (chép lại là cách
# chắc chắn để test và fixture lệch nhau về sau).
_OWN_ARTICLE_ID_LIST = (
    "<ArticleIdList>"
    '<ArticleId IdType="pubmed">30267080</ArticleId>'
    '<ArticleId IdType="pmc">PMC6439769</ArticleId>'
    '<ArticleId IdType="doi">10.1001/jamaoncol.2018.4070</ArticleId>'
    '<ArticleId IdType="pii">2703887</ArticleId>'
    "</ArticleIdList>"
)

_REFERENCE_LIST = (
    "<ReferenceList>"
    "<Reference><Citation>Global prevalence, treatment, and prevention of "
    "hepatitis B virus infection in 2016. Lancet Gastroenterol Hepatol. 2018."
    "</Citation><ArticleIdList>"
    f'<ArticleId IdType="doi">{FIRST_REFERENCE_DOI}</ArticleId>'
    '<ArticleId IdType="pubmed">29599078</ArticleId>'
    "</ArticleIdList></Reference>"
    "<Reference><Citation>Kim H, Jee YM, Song BC, et al. Molecular epidemiology "
    "of hepatitis B virus (HBV) genotypes and serotypes in patients with chronic "
    "HBV infection in Korea. Intervirology. 2007;50(1):52-57. "
    "doi: 10.1159/000096313</Citation><ArticleIdList>"
    f'<ArticleId IdType="doi">{LAST_REFERENCE_DOI}</ArticleId>'
    '<ArticleId IdType="pubmed">17164558</ArticleId>'
    "</ArticleIdList></Reference>"
    "</ReferenceList>"
)

_ELOCATION_ID = '<ELocationID EIdType="doi" ValidYN="Y">10.1001/jamaoncol.2018.4070</ELocationID>'

_MEDLINE_CITATION = (
    '<MedlineCitation Status="MEDLINE" Owner="NLM">'
    '<PMID Version="1">30267080</PMID>'
    '<Article PubModel="Print">'
    "<Journal><Title>JAMA oncology</Title>"
    "<JournalIssue><PubDate><Year>2019</Year></PubDate></JournalIssue></Journal>"
    "<ArticleTitle>Risk of Hepatocellular Carcinoma in Patients Treated With "
    "Entecavir vs Tenofovir for Chronic Hepatitis B: A Korean Nationwide Cohort "
    "Study.</ArticleTitle>"
    f"{_ELOCATION_ID}"
    "<AuthorList>"
    "<Author><LastName>Choi</LastName><Initials>J</Initials></Author>"
    "<Author><LastName>Kim</LastName><Initials>HJ</Initials></Author>"
    "</AuthorList>"
    "<PublicationTypeList><PublicationType>Journal Article</PublicationType>"
    "</PublicationTypeList>"
    "</Article>"
    "</MedlineCitation>"
)


def _build_xml(medline: str = _MEDLINE_CITATION, pubmed_data: str | None = None) -> str:
    """Ráp một `<PubmedArticleSet>` hợp lệ từ các khối trên."""
    if pubmed_data is None:
        pubmed_data = _OWN_ARTICLE_ID_LIST + _REFERENCE_LIST
    return (
        '<?xml version="1.0" ?>\n<PubmedArticleSet>\n<PubmedArticle>\n'
        f"{medline}\n<PubmedData>{pubmed_data}</PubmedData>\n"
        "</PubmedArticle>\n</PubmedArticleSet>\n"
    )


# XML tương đương bản thật: ArticleIdList của bài, rồi ReferenceList.
_XML_WITH_REFERENCES = _build_xml()


def _article(xml_text: str) -> ET.Element:
    return ET.fromstring(xml_text).find(".//PubmedArticle")


# ── 1. Ca hồi quy trung tâm: đúng PMID 30267080 ───────────────────────────────
def test_metadata_tra_dung_doi_cua_chinh_bai_pmid_30267080():
    """`fetch_metadata()` phải trả DOI JAMA, KHÔNG phải DOI Karger của tham khảo."""
    out = PubMedClient._parse_metadata_xml(_XML_WITH_REFERENCES, ["30267080"])
    assert out["30267080"]["status"] == "resolved"
    assert out["30267080"]["doi"] == OWN_DOI


def test_metadata_khong_bao_gio_tra_doi_cua_tai_lieu_tham_khao():
    """Chốt bất biến: DOI trả về không được TRÙNG bất kỳ DOI tham khảo nào."""
    doi = PubMedClient._parse_metadata_xml(_XML_WITH_REFERENCES, ["30267080"])["30267080"]["doi"]
    assert doi not in {LAST_REFERENCE_DOI, FIRST_REFERENCE_DOI}
    assert doi.startswith("10.1001/"), "DOI phải mang tiền tố JAMA Network"


def test_parse_efetch_cung_tra_dung_doi():
    """`_parse_efetch()` mắc CÙNG lỗi và phải được vá cùng lúc — không chỉ metadata."""
    records = PubMedClient()._parse_efetch(_XML_WITH_REFERENCES, None, "q")
    assert len(records) == 1
    assert records[0].pmid == "30267080"
    assert records[0].doi == OWN_DOI


# ── 2. Không được dựa vào THỨ TỰ phần tử ──────────────────────────────────────
def test_khong_duoc_dua_vao_THU_TU_phan_tu_ma_phai_neo_theo_DUONG_DAN():
    """Đảo thứ tự: `<ReferenceList>` đặt TRƯỚC `<ArticleIdList>` của chính bài.

    ĐO ĐƯỢC, KHÔNG PHẢI GIẢ ĐỊNH — kiểm bằng phép đột biến ngày 14/08: nếu "sửa"
    lỗi bằng cách chỉ thêm `break` vào vòng lặp `.//ArticleId` cũ (lấy phần tử
    ĐẦU TIÊN thay vì cuối cùng), thì mọi test còn lại vẫn XANH, bởi trong XML
    PubMed thật `ArticleIdList` của bài luôn đứng TRƯỚC `ReferenceList` nên "phần
    tử đầu tiên" tình cờ đúng. Bản vá khi ấy chỉ đúng NHỜ MAY và sẽ vỡ im lặng
    nếu NLM đổi thứ tự phần tử.

    Thứ tự đảo dưới đây là TỔNG HỢP CÓ CHỦ Ý (DTD của PubMed quy định
    ArticleIdList đứng trước ReferenceList, nên bản ghi thật không có dạng này).
    Mục đích không phải mô phỏng PubMed, mà ép parser chứng minh nó neo vào
    ĐƯỜNG DẪN `PubmedData/ArticleIdList` chứ không dựa vào thứ tự tài liệu.
    """
    swapped = _build_xml(pubmed_data=_REFERENCE_LIST + _OWN_ARTICLE_ID_LIST)

    art = _article(swapped)
    # Tiền đề của test: ReferenceList thật sự đứng trước ArticleIdList của bài.
    all_doi = [e.text for e in art.findall(".//ArticleId") if e.get("IdType") == "doi"]
    assert all_doi[0] == FIRST_REFERENCE_DOI, "fixture đảo thứ tự không thành"

    assert _own_article_doi(art) == OWN_DOI
    assert PubMedClient._parse_metadata_xml(swapped, ["30267080"])["30267080"]["doi"] == OWN_DOI


# ── 3. Hai vị trí hợp lệ của DOI chính bài ────────────────────────────────────
def test_du_phong_elocationid_khi_thieu_articleidlist():
    """Thiếu `PubmedData/ArticleIdList` thì lấy `ELocationID`, KHÔNG rơi xuống tham khảo."""
    minimal_ids = '<ArticleIdList><ArticleId IdType="pubmed">30267080</ArticleId></ArticleIdList>'
    xml = _build_xml(pubmed_data=minimal_ids + _REFERENCE_LIST)
    assert _own_article_doi(_article(xml)) == OWN_DOI


def test_bo_qua_elocationid_bi_pubmed_danh_dau_sai():
    """`ValidYN="N"` là DOI mà CHÍNH PubMed đánh dấu SAI — không được dùng."""
    minimal_ids = '<ArticleIdList><ArticleId IdType="pubmed">30267080</ArticleId></ArticleIdList>'
    medline = _MEDLINE_CITATION.replace('ValidYN="Y"', 'ValidYN="N"')
    xml = _build_xml(medline=medline, pubmed_data=minimal_ids + _REFERENCE_LIST)
    # Thà KHÔNG BIẾT còn hơn trả một DOI sai — cùng nguyên tắc fail-closed đã ghi
    # trong CLAUDE.md ("không gộp 'không biết' với 'có vấn đề'").
    assert _own_article_doi(_article(xml)) is None


def test_khong_co_doi_nao_thi_tra_none():
    """Không có DOI ở cả hai vị trí chính bài ⇒ None, KHÔNG mượn DOI tham khảo."""
    minimal_ids = '<ArticleIdList><ArticleId IdType="pubmed">30267080</ArticleId></ArticleIdList>'
    medline = _MEDLINE_CITATION.replace(_ELOCATION_ID, "")
    xml = _build_xml(medline=medline, pubmed_data=minimal_ids + _REFERENCE_LIST)
    assert _own_article_doi(_article(xml)) is None
    assert PubMedClient._parse_metadata_xml(xml, ["30267080"])["30267080"]["doi"] is None


# ── 4. Không hồi quy ở bản ghi KHÔNG có ReferenceList ─────────────────────────
def test_ban_ghi_khong_co_reference_list_van_dung():
    """Nhóm bản ghi vốn đã đúng trước khi vá phải giữ nguyên hành vi."""
    xml = _build_xml(pubmed_data=_OWN_ARTICLE_ID_LIST)
    out = PubMedClient._parse_metadata_xml(xml, ["30267080"])
    assert out["30267080"]["doi"] == OWN_DOI


# ── 5. PMID cũng phải neo vào chính bài (siết phòng xa, cùng họ lỗi) ──────────
def test_pmid_lay_tu_chinh_bai_khong_lay_tu_comments_corrections():
    """`.//PMID` chạm được `CommentsCorrections/PMID` (PMID thông báo rút bài…).

    Thứ tự tài liệu hiện đang cứu `findtext`, nên đây là chốt phòng xa: nếu bản
    ghi có `CommentsCorrectionsList` thì PMID trả về vẫn phải là của chính bài.
    """
    medline = _MEDLINE_CITATION.replace(
        "</Article>",
        "</Article><CommentsCorrectionsList>"
        '<CommentsCorrections RefType="ErratumIn">'
        '<PMID Version="1">99999999</PMID></CommentsCorrections>'
        "</CommentsCorrectionsList>",
    )
    xml = _build_xml(medline=medline)
    assert _own_article_pmid(_article(xml)) == "30267080"
    out = PubMedClient._parse_metadata_xml(xml, ["30267080"])
    assert out["30267080"]["status"] == "resolved"
    assert "99999999" not in out
