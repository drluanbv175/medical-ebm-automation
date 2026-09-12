"""Hồi quy phát hiện HIGH của Workflow đối kháng đa-agent 2026-09-04 (vòng 2):
`app/sources/pubmed.py` — ArticleTitle/AbstractText bị CẮT CỤT khi XML có thẻ
lồng, vì `_parse_efetch()`/`_parse_metadata_xml()` đọc `.text`/`findtext()`
thay vì duyệt toàn bộ cây con.

CƠ CHẾ LỖI: theo ngữ nghĩa `xml.etree.ElementTree`, `.text` CHỈ là văn bản
đứng TRƯỚC thẻ con ĐẦU TIÊN của một phần tử. XML PubMed rất hay chứa thẻ lồng
(`<i>`/`<b>`/`<sub>`/`<sup>`) ngay trong ArticleTitle/AbstractText cho tên
gen/thuốc/công thức hoá học — phổ biến trong y văn. Xác nhận bằng thực nghiệm
TRƯỚC khi vá: tiêu đề `"Test article about <i>BRCA1</i> mutation"` đọc bằng
`.text` chỉ ra `"Test article about "` (mất "BRCA1 mutation" — MẤT TÊN GEN);
abstract có `<b>significant</b> reduction of 45% (95% CI 30-60%)` chỉ ra
`"We found a "` — MẤT TRẮNG toàn bộ số liệu (%, CI), không có ngoại lệ nào
báo lỗi.

VÌ SAO ĐÁNG CHẶN BẰNG TEST: title/abstract cụt đi thẳng vào cổng kiểm trích
dẫn A12 và bị `tools/kiem_so_lieu.py` đọc nhầm thành "⚪ tóm tắt không nêu"
(an toàn nhưng sai — bỏ sót một số liệu THẬT SỰ có trong tóm tắt) thay vì so
được số thật; title cụt có thể khiến cổng đối chiếu tiêu đề trích dẫn báo
"không khớp" giả cho một trích dẫn hoàn toàn đúng.

Bản vá thêm `_full_text()` (dùng `"".join(elem.itertext())`) và áp dụng cho
CẢ HAI hàm tiêu thụ cùng loại dữ liệu — `_parse_efetch()` (title + abstract)
và `_parse_metadata_xml()` (title) — đúng bài học BH39 đã ghi trong chính
file này ở một bản vá trước (một luật thêm ở một hàm phải lan sang mọi hàm
chị em tiêu thụ cùng dữ liệu).

Test chạy NGOẠI TUYẾN, không cần mạng, cùng quy ước
tests/test_pubmed_own_doi_20260814.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.pubmed import PubMedClient, _full_text  # noqa: E402

XML_CO_THE_LONG = """<?xml version="1.0"?>
<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>12345</PMID><Article>
<ArticleTitle>Test article about <i>BRCA1</i> mutation</ArticleTitle>
<Abstract><AbstractText Label="RESULTS">We found a <b>significant</b> \
reduction of 45% (95% CI 30-60%) in <i>TP53</i>-mutant tumors, p&lt;0.001.\
</AbstractText></Abstract>
<Journal><Title>Test Journal</Title></Journal>
<PubDate><Year>2026</Year></PubDate>
<AuthorList><Author><LastName>Smith</LastName><Initials>J</Initials></Author></AuthorList>
</Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""

TIEU_DE_DAY_DU = "Test article about BRCA1 mutation"
ABSTRACT_DAY_DU = ("We found a significant reduction of 45% (95% CI 30-60%) "
                   "in TP53-mutant tumors, p<0.001.")


def _client() -> PubMedClient:
    c = PubMedClient.__new__(PubMedClient)
    c.name = "pubmed"
    return c


class TestParseEfetchKhongCatCutThe:
    """★★ Ca chính — _parse_efetch() (dùng bởi search()/RawRecord ingestion)."""

    def test_title_giu_du_ten_gen_trong_the_i(self):
        recs = _client()._parse_efetch(XML_CO_THE_LONG, None, "test query")
        assert recs[0].title == TIEU_DE_DAY_DU

    def test_abstract_giu_du_so_lieu_trong_the_b(self):
        recs = _client()._parse_efetch(XML_CO_THE_LONG, None, "test query")
        assert recs[0].abstract == ABSTRACT_DAY_DU

    def test_khong_bi_cat_o_dau_thang_gia(self):
        """★★ Đối chứng bắt buộc — dấu "<" mã hoá thực thể (&lt;) trong nội
        dung (không phải thẻ thật) không bị hiểu nhầm, số liệu p<0.001 vẫn
        ra đúng dấu "<" sau khi ElementTree giải mã thực thể."""
        recs = _client()._parse_efetch(XML_CO_THE_LONG, None, "test query")
        assert "p<0.001" in recs[0].abstract


class TestParseMetadataXmlKhongCatCutThe:
    """★★ Ca chính — _parse_metadata_xml() (dùng bởi check_citations(), khác
    hàm ở trên nhưng CÙNG loại dữ liệu — đúng bài học BH39 của chính file
    này: một luật phải lan sang mọi hàm chị em tiêu thụ cùng dữ liệu)."""

    def test_title_giu_du_ten_gen(self):
        meta = _client()._parse_metadata_xml(XML_CO_THE_LONG, ["12345"])
        assert meta["12345"]["title"] == TIEU_DE_DAY_DU


class TestFullTextHamDungChung:
    """Đối chứng hàm `_full_text()` tự thân — None-safe, không có thẻ con
    vẫn hoạt động như `.text` cũ."""

    def test_none_tra_ve_chuoi_rong(self):
        assert _full_text(None) == ""

    def test_khong_co_the_con_giong_het_text_cu(self):
        import xml.etree.ElementTree as ET
        elem = ET.fromstring("<x>chỉ văn bản thường, không thẻ con</x>")
        assert _full_text(elem) == "chỉ văn bản thường, không thẻ con"
