"""Tổng quan tài liệu — mỗi tài liệu đỡ một câu (K12), TLTK đúng Vancouver theo metadata A12 (K13), metadata PubMed đủ
cho Vancouver, và đối chiếu con số ↔ toàn văn (20/11/2026).

Bác sĩ 20/11/2026: «Hãy kiểm tra và hoàn thiện vấn đề tổng quan tài liệu». Soát tay đề cương BTM tìm thấy: khối trích
dẫn gộp «[15–36]» (22 tài liệu không đỡ câu nào), danh mục cắt ở 5 tác giả không «et al.» và thiếu tập/số/trang (biên
nhận A12 chỉ giữ 5 tác giả, không có tập/trang), con số gán lệch quần thể. K1–K11 đều ĐẠT nên không thấy.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import kiem_so_lieu_toan_van as KS  # noqa: E402

from app.sources import pubmed as PM  # noqa: E402


def _md(than: str, tltk: str, phu_luc: str = "") -> str:
    return f"# 1. ĐẶT VẤN ĐỀ\n\n{than}\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\nx\n\n" \
           f"# 7. TÀI LIỆU THAM KHẢO\n\n{tltk}\n\n# PHỤ LỤC A. X\n\n{phu_luc}\n"


def _tltk(n: int) -> str:
    return "\n".join(f"{i}. Tác giả {i}. Bài {i}. Tạp chí. 2024;1:1-2. PMID: {1000 + i}." for i in range(1, n + 1))


# ── K12 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_k12_bat_khoi_trich_dan_gop_tu_6_tai_lieu():
    md = _md("Câu một [1]. Các tài liệu khác được tham khảo khi xây dựng đề cương [2–7].",
             _tltk(7))
    loi = KDN.loi_k12(md)
    assert len(loi) == 1 and "khối trích dẫn gộp [2–7] (6 tài liệu)" in loi[0]


def test_k12_cho_phep_ngoac_5_tai_lieu_va_dem_ca_phu_luc():
    md = _md("Câu một [1, 2–5].", _tltk(6), phu_luc="Mẫu phiếu theo [6].")
    assert KDN.loi_k12(md) == []


def test_k12_bat_tai_lieu_khong_duoc_trich():
    md = _md("Câu một [1]. Câu hai [3].", _tltk(4))
    loi = KDN.loi_k12(md)
    assert len(loi) == 1 and "2, 4" in loi[0]


def test_k12_bo_qua_so_trong_chinh_danh_muc_va_chuoi_tim_kiem():
    md = _md('Tìm "x"[tiab] AND 2019:2026[dp] [1].', "1. A. B [2]. C. 2024;1:1. PMID: 1.")
    assert KDN.loi_k12(md) == []


def test_k11_mien_cot_ten_bai_nguyen_van_nhung_van_kiem_cot_khac():
    """Bảng tài liệu ở chương tổng quan giữ tên bài đúng chữ nguồn («vs», số 8 chữ số) — như danh mục TLTK."""
    bang = ("| Tài liệu | Năm | Tên bài (nguyên văn) |\n|---|---|---|\n"
            "| Smith và cộng sự [1] | 2020 | Drug A vs drug B in 22222222 adults |\n")
    assert KDN.loi_k11(_md(bang, _tltk(1))) == []
    sai = bang.replace("| 2020 |", "| 2020 vs 2021 |")
    assert any("«vs»" in x for x in KDN.loi_k11(_md(sai, _tltk(1))))


# ── K13 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _bien_nhan(tmp_path: Path, meta: dict) -> Path:
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": meta}), encoding="utf-8", newline="\n")
    return tmp_path


_MD8 = {"status": "resolved", "year": "2024", "n_authors": 8, "volume": "7", "journal_abbr": "JAMA Netw Open",
        "authors_6": ["Edmonston D", "Lydon E", "Mulder H", "Chiswell K", "Lampron Z", "Marsolo K"]}


def test_k13_dat_khi_dung_vancouver(tmp_path):
    d = _bien_nhan(tmp_path, {"111": _MD8})
    md = _md("Câu [1].", "1. Edmonston D, Lydon E, Mulder H, Chiswell K, Lampron Z, Marsolo K, et al. Concordance. "
             "JAMA Netw Open. 2024;7(6):e2418808. PMID: 111.")
    assert KDN.loi_k13(d, md) == []


def test_k13_bat_cat_5_tac_gia_thieu_tap_va_ten_tap_chi_day_du(tmp_path):
    d = _bien_nhan(tmp_path, {"111": _MD8})
    md = _md("Câu [1].", "1. Edmonston D, Lydon E, Mulder H, Chiswell K, Lampron Z. Concordance. JAMA network open. "
             "2024. doi:10.1/x. PMID: 111.")
    loi = KDN.loi_k13(d, md)
    assert len(loi) == 1
    for y in ("8 tác giả", "Marsolo K", "2024;7", "JAMA Netw Open"):
        assert y in loi[0], y


def test_k13_bat_et_al_thua_khi_it_tac_gia(tmp_path):
    m = dict(_MD8, n_authors=2, authors_6=["Bland JM", "Altman DG"], volume="1", journal_abbr="Lancet",
             year="1986")
    d = _bien_nhan(tmp_path, {"222": m})
    md = _md("Câu [1].", "1. Bland JM, Altman DG, et al. Methods. Lancet. 1986;1(8476):307-10. PMID: 222.")
    assert "ghi đủ, không «et al.»" in KDN.loi_k13(d, md)[0]


def test_k13_bo_qua_bien_nhan_cu_chua_co_truong_vancouver(tmp_path):
    d = _bien_nhan(tmp_path, {"111": {"status": "resolved", "authors": "Edmonston D, Lydon E", "year": "2024"}})
    md = _md("Câu [1].", "1. Edmonston D. Concordance. JAMA network open. 2024. PMID: 111.")
    assert KDN.loi_k13(d, md) == []


# ── metadata PubMed đủ cho Vancouver ─────────────────────────────────────────────────────────────────────────────────
_XML = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>1</PMID><Article>
<Journal><JournalIssue><Volume>49</Volume><Issue>Suppl 1</Issue><PubDate><Year>2026</Year></PubDate></JournalIssue>
<Title>Diabetes care</Title></Journal><ArticleTitle>11. Chronic Kidney Disease.</ArticleTitle>
<Pagination><MedlinePgn>S246-S260</MedlinePgn></Pagination>
<AuthorList>{tac_gia}</AuthorList></Article>
<MedlineJournalInfo><MedlineTA>Diabetes Care</MedlineTA></MedlineJournalInfo>
<CommentsCorrectionsList><CommentsCorrections><RefSource>X</RefSource></CommentsCorrections></CommentsCorrectionsList>
</MedlineCitation></PubmedArticle></PubmedArticleSet>"""


def test_truong_vancouver_tach_ca_nhan_tap_the_bo_dau_sao_lay_tap_so_trang():
    """K13 chạy thật 20/11/2026: tập thể bị đếm vào quy tắc 6 tác giả (STROBE: «bài có 7 tác giả» — sai) và giữ dấu «*»
    của PubMed («…Committee for Diabetes*») ⇒ báo đỏ giả. Nay tách hai loại, bỏ dấu sao."""
    tg = "<Author><CollectiveName>American Diabetes Association Committee*</CollectiveName></Author>" + "".join(
        f"<Author><LastName>Ho{i}</LastName><Initials>A</Initials></Author>" for i in range(7))
    art = ET.fromstring(_XML.format(tac_gia=tg)).find("PubmedArticle")
    r = PM._truong_vancouver(art)
    assert r["n_authors"] == 7 and r["authors_6"] == [f"Ho{i} A" for i in range(6)]
    assert r["nhom_tac_gia"] == ["American Diabetes Association Committee"]
    assert (r["journal_abbr"], r["volume"], r["issue"], r["pages"]) == ("Diabetes Care", "49", "Suppl 1", "S246-S260")


def test_k13_tap_the_sau_ca_nhan_khong_tinh_vao_quy_tac_6_tac_gia(tmp_path):
    m = {"status": "resolved", "year": "2008", "n_authors": 6, "volume": "61", "journal_abbr": "J Clin Epidemiol",
         "authors_6": ["von Elm E", "Altman DG", "Egger M", "Pocock SJ", "Gøtzsche PC", "Vandenbroucke JP"],
         "nhom_tac_gia": ["STROBE Initiative"]}
    d = _bien_nhan(tmp_path, {"333": m})
    dung = ("1. von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP; STROBE Initiative. The STROBE "
            "statement. J Clin Epidemiol. 2008;61(4):344-9. PMID: 333.")
    assert KDN.loi_k13(d, _md("Câu [1].", dung)) == []
    thieu = dung.replace("; STROBE Initiative", "")
    assert "thiếu tác giả tập thể «STROBE Initiative»" in KDN.loi_k13(d, _md("Câu [1].", thieu))[0]


def test_k13_chi_co_tac_gia_tap_the_bo_dau_sao_khi_so(tmp_path):
    m = {"status": "resolved", "year": "2026", "n_authors": 0, "authors_6": [], "volume": "49",
         "journal_abbr": "Diabetes Care", "nhom_tac_gia": ["American Diabetes Association Committee*"]}
    d = _bien_nhan(tmp_path, {"444": m})
    md = _md("Câu [1].", "1. American Diabetes Association Committee. 11. Chronic Kidney Disease. Diabetes Care. "
             "2026;49(Suppl 1):S246-S260. PMID: 444.")
    assert KDN.loi_k13(d, md) == []


def test_vancouver_g10_ghi_tap_the_sau_ca_nhan():
    import run_g10_assemble as G10A
    m = {"status": "resolved", "title": "The STROBE statement.", "year": "2008", "n_authors": 6, "volume": "61",
         "issue": "4", "pages": "344-9", "journal_abbr": "J Clin Epidemiol", "nhom_tac_gia": ["STROBE Initiative"],
         "authors_6": ["von Elm E", "Altman DG", "Egger M", "Pocock SJ", "Gøtzsche PC", "Vandenbroucke JP"]}
    assert G10A._vancouver("333", m) == ("von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP; "
                                         "STROBE Initiative. The STROBE statement. J Clin Epidemiol. "
                                         "2008;61(4):344-9. PMID: 333.")
    chi_nhom = G10A._vancouver("444", dict(m, n_authors=0, authors_6=[], nhom_tac_gia=["ADA Committee"]))
    assert chi_nhom.startswith("ADA Committee. The STROBE statement.")


def test_truong_vancouver_lui_ve_elocation_khi_khong_co_trang():
    xml = _XML.format(tac_gia="<Author><LastName>A</LastName><Initials>B</Initials></Author>").replace(
        "<Pagination><MedlinePgn>S246-S260</MedlinePgn></Pagination>",
        '<ELocationID EIdType="doi">10.1/x</ELocationID><ELocationID EIdType="pii">e2418808</ELocationID>')
    r = PM._truong_vancouver(ET.fromstring(xml).find("PubmedArticle"))
    assert r["pages"] == "e2418808"


def test_vancouver_g10_dung_truong_moi_va_giu_cach_cu():
    import run_g10_assemble as G10A
    moi = G10A._vancouver("111", dict(_MD8, title="Concordance.", journal="JAMA network open", doi="10.1/x",
                                      issue="6", pages="e2418808"))
    assert moi == ("Edmonston D, Lydon E, Mulder H, Chiswell K, Lampron Z, Marsolo K, et al. Concordance. "
                   "JAMA Netw Open. 2024;7(6):e2418808. doi:10.1/x. PMID: 111.")
    cu = G10A._vancouver("111", {"status": "resolved", "title": "Concordance.", "authors": "Edmonston D, Lydon E",
                                 "journal": "JAMA network open", "year": "2024", "doi": "10.1/x"})
    assert cu == "Edmonston D, Lydon E. Concordance. JAMA network open. 2024. doi:10.1/x. PMID: 111."


# ── đối chiếu con số ↔ toàn văn ──────────────────────────────────────────────────────────────────────────────────────
def _nguon(tmp_path: Path) -> Path:
    oa = tmp_path / "toan_van_oa"
    oa.mkdir()
    (oa / "PMID-1001_PMC1.xml").write_text(
        "<article><abstract><p>Only 24.9% received both tests among 316 234 adults; 56.5% received one.</p>"
        "</abstract></article>", encoding="utf-8", newline="\n")
    (oa / "PMID-1002_PMC2.xml").write_text("<article><p>Testing was 43.3% in 2021.</p></article>",
                                           encoding="utf-8", newline="\n")
    return tmp_path


def _chay(tmp_path: Path, than: str):
    md = _md(than, _tltk(3))
    _, muc = KDN._tach_tltk(md)
    khoa = {so: KS._khoa_muc(nd, so) for so, nd in muc.items()}
    van = KS.khoang_van_ban(md, "ĐẶT VẤN ĐỀ", "ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP")
    return KS.doi_chieu(van, muc, lambda so: KS.van_toan_van(tmp_path, khoa[so], None))


def test_so_dung_nguon_dat(tmp_path):
    d = _nguon(tmp_path)
    assert _chay(d, "Trong 316.234 người năm 2024, chỉ 24,9% được làm cả hai xét nghiệm (khuyến cáo 11.1a) [1].") == []


def test_so_sai_bi_bat(tmp_path):
    kq = _chay(_nguon(tmp_path), "Chỉ 25,9% được làm cả hai xét nghiệm [1].")
    assert kq and kq[0].khong_thay == ["25,9"]


def test_so_gan_sai_tai_lieu_bi_bat_theo_tung_ve(tmp_path):
    """Hai vế cách nhau bằng «;» — số của vế sau chỉ được so với nguồn của chính vế sau. 56,5% là số của tài liệu [1]
    nhưng vế sau dẫn [2]: gộp cả câu thì [1] «che» lỗi (đột biến bỏ tách «;» từng lọt khi cả hai vế cùng dẫn [2])."""
    kq = _chay(_nguon(tmp_path), "Chỉ 24,9% được làm cả hai xét nghiệm [1]; 56,5% chỉ làm một xét nghiệm [2].")
    assert [v.khong_thay for v in kq] == [["56,5"]]


def test_tai_lieu_chua_co_toan_van_la_chua_doi_chieu_duoc(tmp_path):
    kq = _chay(_nguon(tmp_path), "Tỷ lệ hài lòng là 78,9% [3].")
    assert kq and kq[0].thieu_toan_van == [3]


def test_bo_tep_tom_tat_do_he_thong_dung(tmp_path):
    a = tmp_path / "PMID-1_TomTatChungCu.pdf"
    b = tmp_path / "PMID-1.pdf"
    for p in (a, b):
        p.write_bytes(b"%PDF-1.4")
    assert KS.chon_tep_endnote([a, b]) == b
    assert KS.chon_tep_endnote([a]) is None


def test_bo_sinh_xep_tai_lieu_con_lai_vao_bang_khong_gom_mot_cau(tmp_path):
    """Gốc của khối «[15–36]»: bộ sinh gom mọi tài liệu chưa được nhắc vào MỘT câu cuối phần bằng chứng."""
    import sinh_de_cuong_nop_hoi_dong as SDC
    sys.path.insert(0, str(ROOT / "tests"))
    import test_sinh_de_cuong_nop_hoi_dong_20261116 as T

    d = T._de_tai(tmp_path)
    (d / f"DE_CUONG_THONG_NHAT_{T.MA}.md").write_text("Nguồn: PMID 22222222.\n", encoding="utf-8", newline="\n")
    assert SDC.sinh(d, T.MA, ghi=True)["ma"] == 0
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{T.MA}.md").read_text(encoding="utf-8")
    assert "Các tài liệu liên quan khác đã được rà soát**" in van and "| Tên bài (nguyên văn) |" in van
    assert "đã được rà soát khi xây dựng đề cương này [" not in van
    assert KDN.loi_k12(van) == []
