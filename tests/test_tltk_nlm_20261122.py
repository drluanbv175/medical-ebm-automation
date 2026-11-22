"""Tài liệu tham khảo đúng chuẩn NLM «Citing Medicine» theo LOẠI tài liệu + khớp hai chiều (K12/K13, 22/11/2026).

Bác sĩ 22/11/2026: «Tài liệu tham khảo, trích dẫn đã có nền, hãy nâng cấp và hoàn thiện đúng chuẩn». K13 cũ chỉ kiểm
mục có PMID; mục không PMID (bài tạp chí trong nước, văn bản quy phạm, sách) không bị kiểm yếu tố nào — đo trên C1a: 7
bài tạp chí trong nước thiếu số trang.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import danh_muc_trich_dan as D  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402

BAI = ("Trần Tất Thắng, Trần Thị Thùy Dung, Nguyễn Sa Huỳnh. Thực trạng thời gian chờ khám bệnh. Tạp chí Y học Cộng "
       "đồng. 2026;67(7):45-51. doi:10.52163/yhc.v67i7.5934.")
VB = ("Bộ Y tế. Quyết định số 56/QĐ-BYT ngày 08/01/2024 ban hành Hướng dẫn phương pháp đo lường sự hài lòng. Hà Nội: "
      "Bộ Y tế; 2024.")
SACH = "Lwanga SK, Lemeshow S. Sample size determination in health studies. Geneva: World Health Organization; 1991."
WEB = ("World Health Organization. Hypertension fact sheet [Internet]. Geneva: WHO; 2023 [cited 2026 Nov 20]. "
       "Available from: https://www.who.int/news-room/fact-sheets/detail/hypertension")
TIEN_IN = "Nguyen A, Tran B. A new score. medRxiv [Preprint]. 2026. doi:10.1101/2026.01.01.123456."
LUAN_VAN = "Nguyễn Văn A. Sự hài lòng của người bệnh [luận văn thạc sĩ]. Hà Nội: Trường Đại học Y Hà Nội; 2024."
CHUONG = ("Smith J. Patient satisfaction. In: Brown K, editor. Health services research. London: Sage; 2020. "
          "p. 45-60.")


def test_phan_loai_theo_loai_tai_lieu():
    assert D.loai_tltk(BAI) == "bai_bao"
    assert D.loai_tltk(VB) == "van_ban_quy_pham"
    assert D.loai_tltk(SACH) == "sach"
    assert D.loai_tltk(WEB) == "trang_web"
    assert D.loai_tltk(TIEN_IN) == "tien_in"
    assert D.loai_tltk(LUAN_VAN) == "luan_van"
    assert D.loai_tltk(CHUONG) == "chuong_sach"


def test_muc_day_du_khong_thieu_yeu_to():
    for dong in (BAI, VB, SACH, WEB, TIEN_IN, LUAN_VAN, CHUONG):
        assert D.yeu_to_nlm(dong)["thieu"] == [], (dong, D.yeu_to_nlm(dong))


def test_bai_tap_chi_thieu_trang_bi_bat():
    y = D.yeu_to_nlm(BAI.replace("2026;67(7):45-51.", "2026;67(7)."))
    assert y["loai"] == "bai_bao" and y["thieu"] == ["trang hoặc mã bài (năm;tập(số):trang)"]
    assert D.yeu_to_nlm(BAI.replace(":45-51", ":e70241"))["thieu"] == []  # mã bài (e-location) được nhận


def test_quy_tac_tac_gia_nlm():
    bay = "A B, C D, E F, G H, I J, K L, M N. Tiêu đề bài. Tạp chí. 2020;1(1):1-5."
    assert any("6 tác giả đầu" in x for x in D.yeu_to_nlm(bay)["thieu"])
    sau_et_al = "A B, C D, E F, G H, I J, K L, và cộng sự. Tiêu đề bài. Tạp chí. 2020;1(1):1-5."
    assert D.yeu_to_nlm(sau_et_al)["thieu"] == []
    nam_et_al = "A B, C D, E F, G H, I J, et al. Tiêu đề bài. Tạp chí. 2020;1(1):1-5."
    assert any("đúng 6 tác giả" in x for x in D.yeu_to_nlm(nam_et_al)["thieu"])


def test_van_ban_quy_pham_sach_web_tien_in_thieu_yeu_to():
    assert D.yeu_to_nlm(VB.replace(" ngày 08/01/2024", ""))["thieu"] == ["ngày ban hành"]
    assert D.yeu_to_nlm(VB.replace(" Hà Nội: Bộ Y tế; 2024.", ""))["thieu"] == ["nơi ban hành: cơ quan; năm"]
    assert D.yeu_to_nlm(SACH.replace("Geneva: World Health Organization; 1991.", "1991."))["thieu"] \
        == ["nơi xuất bản: nhà xuất bản; năm"]
    assert D.yeu_to_nlm(WEB.replace(" [cited 2026 Nov 20]", ""))["thieu"] \
        == ["ngày truy cập ([trích dẫn …]/[cited …])"]
    assert D.yeu_to_nlm(TIEN_IN.replace(" doi:10.1101/2026.01.01.123456.", ""))["thieu"] == ["DOI của bản tiền in"]
    assert D.yeu_to_nlm(CHUONG.replace(" p. 45-60.", ""))["thieu"] == ["trang của chương (p. …/tr. …)"]


def _md(than: str, tltk: str) -> str:
    return f"# ĐẶT VẤN ĐỀ\n\n{than}\n\n# TÀI LIỆU THAM KHẢO\n\n{tltk}\n\n# PHỤ LỤC A\n\nNội dung.\n"


def test_k12_khop_hai_chieu():
    tltk = "1. " + BAI + "\n2. " + SACH
    assert K.loi_k12(_md("Câu một [1]. Câu hai [2].", tltk)) == []
    loi = K.loi_k12(_md("Câu một [1]. Câu hai [2]. Câu ba [3].", tltk))
    assert any(x.startswith("K12 1 số trích dẫn trong thân không có trong danh mục") and ": 3 " in x for x in loi)
    loi = K.loi_k12(_md("Câu một [1]. Câu ba [3].", "1. " + BAI + "\n3. " + SACH))
    assert any("đánh số không liên tục — thiếu số 2" in x for x in loi)


def test_k13_nlm_chi_ap_muc_khong_pmid_va_bao_dung_muc():
    tltk = "\n".join(["1. " + BAI.replace(":45-51", ""), "2. " + VB.replace(" ngày 08/01/2024", ""),
                      "3. Smith J. Bài có PMID. BMJ. 2020. PMID: 11111111."])
    loi = K.loi_k13_nlm(_md("A [1]. B [2]. C [3].", tltk))
    assert len(loi) == 2
    assert loi[0].startswith("K13 TLTK [1] (bài tạp chí, NLM Citing Medicine) thiếu: trang hoặc mã bài")
    assert loi[1].startswith("K13 TLTK [2] (văn bản quy phạm, NLM Citing Medicine) thiếu: ngày ban hành")


def test_k13_pmid_thieu_trang_theo_pubmed(tmp_path):
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": {"40428801": {
        "status": "resolved", "n_authors": 5, "authors_6": ["Kostev K", "Lang M", "Tröbs SO", "Urbisch S", "Gabler M"],
        "year": "2025", "volume": "61", "pages": "843", "journal_abbr": "Medicina (Kaunas)"}}}), encoding="utf-8",
        newline="\n")
    dong = ("1. Kostev K, Lang M, Tröbs SO, Urbisch S, Gabler M. The Underdiagnosis of CKD. Medicina (Kaunas). "
            "2025;61(5). doi:10.3390/medicina61050843. PMID: 40428801.")
    loi = K.loi_k13(tmp_path, _md("A [1].", dong))
    assert len(loi) == 1 and "thiếu trang/mã bài «:843» theo PubMed" in loi[0]
    assert K.loi_k13(tmp_path, _md("A [1].", dong.replace("2025;61(5).", "2025;61(5):843."))) == []
