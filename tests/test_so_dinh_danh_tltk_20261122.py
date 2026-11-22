"""Sổ định danh + đối chiếu siêu dữ liệu TLTK với nguồn; PMCID theo PubMed; số hiệu văn bản không phải số liệu (22/11).

Bác sĩ 22/11/2026: «Tài liệu tham khảo, trích dẫn đã có nền, hãy nâng cấp và hoàn thiện đúng chuẩn» — (b) định danh kiểm
được cho mọi tài liệu, không tìm được thì ghi lý do, không bịa; (c) siêu dữ liệu khớp nguồn (Crossref/PubMed).
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402
import kiem_so_lieu_toan_van as KSL  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import toan_van_trich_dan as TVT  # noqa: E402

from app.sources import pubmed as PM  # noqa: E402

MA = "ZZ-TLTK"
DC = """# ĐẶT VẤN ĐỀ

Câu một [1]. Câu hai [2]. Câu ba [3]. Câu bốn [4].

# TÀI LIỆU THAM KHẢO

1. Nguyễn Văn A, Trần Thị B. Đánh giá sự hài lòng của người bệnh khám ngoại trú. Journal of Health and Development \
Studies. 2023;7(6). doi:10.38148/jhds.0706skpt23-064.
2. Lương Thị C. Một số yếu tố liên quan đến sự hài lòng. Tạp chí Y học Việt Nam. 2024;540(1). doi:10.51298/vmj.1.
3. Bộ Y tế. Quyết định số 56/QĐ-BYT ngày 08/01/2024 ban hành Hướng dẫn. Hà Nội: Bộ Y tế; 2024.
4. Smith J, Tran B. A trial. BMJ. 2020;370:m1. doi:10.1136/bmj.m1. PMID: 11111111.

# PHỤ LỤC A

Nội dung.
"""
CROSSREF = {
    "10.38148/jhds.0706skpt23-064": {"DOI": "10.38148/jhds.0706skpt23-064", "volume": "07", "issue": "06",
                                     "page": "35-41", "title": ["Đánh giá sự hài lòng của người bệnh khám ngoại trú"],
                                     "issued": {"date-parts": [[2023, 12, 29]]}},
    "10.51298/vmj.1": {"DOI": "10.51298/vmj.1", "volume": "540", "issue": "1",
                       "title": ["Một số yếu tố liên quan đến sự hài lòng"], "issued": {"date-parts": [[2024, 7, 10]]}},
}


def _de_tai(tmp_path: Path, dc: str = DC) -> Path:
    d = tmp_path / MA
    d.mkdir()
    (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").write_text(dc, encoding="utf-8", newline="\n")
    return d


def _so(d: Path) -> dict:
    so = TVT.dung_so_dinh_danh(d, MA, tra_doi=CROSSREF.get, tra_td=lambda *_: None,
                               tra_pmc=lambda pm: {"11111111": "PMC1234567"})
    (d / TVT.TEP_DINH_DANH.format(study=MA)).write_text(json.dumps(so, ensure_ascii=False), encoding="utf-8",
                                                         newline="\n")
    return {e["so"]: e for e in so["muc"]}


def test_so_dinh_danh_ghi_dinh_danh_ly_do_va_trang_nguon(tmp_path):
    e = _so(_de_tai(tmp_path))
    assert e[1]["trang_nguon"] == "35-41" and e[1]["lech"] == []
    assert e[2]["nguon_khong_co_trang"] is True and e[2]["trang_nguon"] is None
    assert e[3]["loai"] == "van_ban_quy_pham" and e[3]["so_hieu"] == "56/QĐ-BYT"
    assert any("đường dẫn nguồn chính thức" in x for x in e[3]["ly_do"])
    assert e[4]["pmcid"] == "PMC1234567"


def test_lech_nguon_duoc_ghi_va_trang_rut_gon_nlm_tuong_duong():
    it = {"volume": "8", "issue": "2", "page": "785-794", "title": ["A trial of X"],
          "issued": {"date-parts": [[2004]]}}
    assert TVT.doi_chieu_crossref("A B. A trial of X. J. 2004;8(2):785-94.", it)["lech"] == []
    lech = TVT.doi_chieu_crossref("A B. A trial of X. J. 2005;9(2):700-9.", it)["lech"]
    assert any(x.startswith("năm 2005") for x in lech) and any(x.startswith("tập 9") for x in lech)
    assert any(x.startswith("trang 700-9") for x in lech)
    assert TVT.doi_chieu_crossref("A B. Another paper entirely. J. 2004;8(2):785-94.", it)["lech"][0] \
        .startswith("tiêu đề khác nguồn")


def test_khong_doi_khong_bia_ly_do_khi_khong_tim_thay(tmp_path):
    dc = DC.replace(" doi:10.51298/vmj.1.", "")
    e = TVT.dung_so_dinh_danh(_de_tai(tmp_path, dc), MA, tra_doi=CROSSREF.get, tra_td=lambda *_: None,
                              tra_pmc=lambda pm: {})["muc"]
    m2 = next(x for x in e if x["so"] == 2)
    assert m2["doi"] is None and m2["doi_de_xuat"] is None
    assert "không tìm thấy DOI khớp tiêu đề + năm trên Crossref" in m2["ly_do"]
    m4 = next(x for x in e if x["so"] == 4)
    assert m4["pmcid"] is None and any("PubMed Central" in x for x in m4["ly_do"])


def test_k13_doc_so_trang_theo_crossref(tmp_path):
    d = _de_tai(tmp_path)
    md = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    truoc = K.loi_k13_nlm(md)
    assert any(x.startswith("K13 TLTK [1]") for x in truoc) and any(x.startswith("K13 TLTK [2]") for x in truoc)
    _so(d)
    sau = K.loi_k13_nlm(md, d)
    assert any(x.startswith("K13 TLTK [1]") and "Crossref ghi «35-41»" in x for x in sau)
    assert not any(x.startswith("K13 TLTK [2]") for x in sau)  # Crossref xác nhận nguồn không ghi trang
    # dòng đổi sau khi lập sổ ⇒ mục sổ hết hiệu lực, quay về đòi trang
    md2 = md.replace("Tạp chí Y học Việt Nam. 2024", "Tạp chí Y học Việt Nam (bản sửa). 2024")
    assert any(x.startswith("K13 TLTK [2]") for x in K.loi_k13_nlm(md2, d))


def test_pmcid_tu_pubmed_vao_dong_vancouver_va_k13(tmp_path):
    xml = ("<PubmedArticle><MedlineCitation><Article><AuthorList><Author><LastName>Smith</LastName><Initials>J"
           "</Initials></Author></AuthorList></Article></MedlineCitation><PubmedData><ArticleIdList>"
           "<ArticleId IdType=\"pubmed\">11111111</ArticleId><ArticleId IdType=\"pmc\">PMC1234567</ArticleId>"
           "</ArticleIdList><ReferenceList><Reference><ArticleIdList><ArticleId IdType=\"pmc\">PMC9999999</ArticleId>"
           "</ArticleIdList></Reference></ReferenceList></PubmedData></PubmedArticle>")
    assert PM._truong_vancouver(ET.fromstring(xml))["pmcid"] == "PMC1234567"
    dong = G10._vancouver("11111111", {"status": "resolved", "title": "A trial", "authors_6": ["Smith J"],
                                       "n_authors": 1, "year": "2020", "volume": "370", "pages": "m1",
                                       "journal_abbr": "BMJ", "pmcid": "PMC1234567"})
    assert dong.endswith("PMID: 11111111. PMCID: PMC1234567.")
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": {"11111111": {
        "status": "resolved", "n_authors": 2, "authors_6": ["Smith J", "Tran B"], "year": "2020", "volume": "370",
        "pages": "m1", "pmcid": "PMC1234567"}}}), encoding="utf-8", newline="\n")
    md = DC
    assert any("thiếu «PMCID: PMC1234567»" in x for x in K.loi_k13(tmp_path, md))
    assert K.loi_k13(tmp_path, md.replace("PMID: 11111111.", "PMID: 11111111. PMCID: PMC1234567.")) == []


def test_so_hieu_van_ban_khong_phai_so_lieu():
    muc = {3: "Bộ Y tế. Quyết định số 56/QĐ-BYT ngày 08/01/2024. Hà Nội: Bộ Y tế; 2024."}
    van = ("Các mẫu phiếu đã được thay thế bởi Quyết định số 56/QĐ-BYT ngày 08/01/2024 [3]. Khung dựa trên Mẫu số 2, "
           "Quyết định 56/QĐ-BYT [3]. Tỷ lệ hài lòng 85% [3].")
    ve = KSL.doi_chieu(van, muc, lambda so: "")
    chua = [v for v in ve if v.thieu_toan_van]
    assert len(chua) == 1 and "85%" in chua[0].trich  # chỉ vế mang SỐ LIỆU cần toàn văn


def test_so_khop_kieu_ghi_khac_nhau_cua_nguon_khong_bao_lech_gia():
    it = {"volume": "18", "issue": "5", "page": "1045", "title": ["Is the CVI acceptable? Appraisal and advice"],
          "issued": {"date-parts": [[2022]]}}
    dong = "A B. Is the CVI acceptable? Appraisal and advice. J. 2022;18(5+6):1045-1056."
    assert TVT.doi_chieu_crossref(dong, it)["lech"] == []  # «5+6» chứa 5; trang đầu khớp; tiêu đề có «?»
    it2 = {"volume": "49", "issue": "Supplement_1", "page": "b2393-b2393", "title": ["Standards of Care—2026"],
           "issued": {"date-parts": [[2026]]}}
    assert TVT.doi_chieu_crossref("X. Standards of Care-2026. D. 2026;49(Suppl 1):b2393.", it2)["lech"] == []
    assert TVT.doi_chieu_crossref("X. Standards of Care-2026. D. 2026;49(Suppl 2):b2393.", it2)["lech"] \
        == ["số Suppl 2 — Crossref ghi Supplement_1"]


def test_pmcid_lay_tu_bien_nhan_a12_truoc_idconv_va_muc_pmid_chi_tham_khao_crossref(tmp_path):
    d = _de_tai(tmp_path)
    (d / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": {"11111111": {
        "status": "resolved", "pmcid": "PMC7654321"}}}), encoding="utf-8", newline="\n")
    goi = []
    cr = {**CROSSREF, "10.1136/bmj.m1": {"volume": "999", "title": ["A trial"], "issued": {"date-parts": [[2020]]}}}
    e = {x["so"]: x for x in TVT.dung_so_dinh_danh(d, MA, tra_doi=cr.get, tra_td=lambda *_: None,
                                                   tra_pmc=lambda pm: goi.append(pm) or {})["muc"]}
    assert e[4]["pmcid"] == "PMC7654321" and goi == []  # đã có từ PubMed ⇒ không gọi idconv
    assert e[4]["lech"] == [] and e[4]["lech_tham_khao"] == ["tập 370 — Crossref ghi 999"]
