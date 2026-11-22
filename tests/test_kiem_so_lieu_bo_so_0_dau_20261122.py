"""Đối chiếu con số ↔ toàn văn: «0,78» ↔ «0.78» ↔ «.78» là MỘT số (22/11/2026).

Bác sĩ 22/11/2026: «đã nhầm và sai thì phải sửa». Đề cương C1a trích [41] Polit 2007 với «I-CVI ≥ 0,78» và
«S-CVI/Ave ≥ 0,90»; toàn văn viết «.78», «.90» (kiểu APA bỏ số 0 đứng đầu cho hệ số không vượt 1), nên
`tools/kiem_so_lieu_toan_van.py` báo «không thấy 0,78 / 0,90» — báo SAI. Bộ test giữ hai chiều: ca dương (các cách viết
của cùng một số phải khớp) và ca âm (số khác — «78», «7,8», «1.78», «p.78», «0,780» — không được khớp nhầm).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import kiem_so_lieu_toan_van as KS  # noqa: E402


def _khop(tok: str, nguon: str) -> bool:
    return re.search(KS.mau_so(tok), nguon) is not None


@pytest.mark.parametrize("tok, nguon", [
    ("0,78", "items with an I-CVI of .78 or higher"),       # bỏ số 0 đứng đầu, sau dấu cách
    ("0,90", "the S-CVI/Ave approach (.90)."),               # sau ngoặc mở
    ("0,90", "agreement across the three experts¼.90."),     # pypdf dịch «=» thành «¼» (đo trên PDF Polit 2007)
    ("0,78", "kappa 0.78 (95% CI 0.70-0.85)"),               # dấu chấm tiếng Anh
    ("0,78", "hệ số 0,78"),                                  # dấu phẩy tiếng Việt
    ("0,78", "HR 0·78 (95% CI 0·70–0·88)"),                  # dấu chấm giữa của Lancet
    ("0,78", "r = −.78"),                                     # dấu âm không phải chữ số
    ("24,9", "24·9% of patients"),                           # số ≥ 1 kiểu Lancet
])
def test_cac_cach_viet_cung_mot_so_deu_khop(tok, nguon):
    assert _khop(tok, nguon)


@pytest.mark.parametrize("tok, nguon", [
    ("0,78", "78 patients were enrolled"),       # số nguyên khác
    ("0,78", "a rate of 7,8 per 1000"),          # 7,8
    ("0,78", "a rate of 7.8 per 1000"),          # 7.8
    ("0,78", "mean 1.78 mmol"),                  # 1.78 — số 0 không được thay bằng chữ số khác
    ("0,78", "mean 10.78 mmol"),                 # 10.78
    ("0,78", "Res Nurs Health. 2007.78"),        # năm dính số
    ("0,78", "see p.78 for details"),            # số trang
    ("0,78", "Lancet vol.78"),                   # số tập
    ("0,78", "pp. 78-80"),                       # trang có dấu cách
    ("0,78", "a value of 0.780 was used"),       # số 0 ở CUỐI đổi độ chính xác ⇒ không coi là một
    ("0,78", "a value of .780 was used"),
    ("0,78", "a value of .781"),
    ("0,780", "items with an I-CVI of .78"),     # bản thảo khai độ chính xác mà nguồn không có
    ("0,780", "kappa 0.78 here"),
    ("24,9", "124.9 adults"),
])
def test_so_khac_khong_khop_nham(tok, nguon):
    assert not _khop(tok, nguon)


def test_0780_khop_dung_nguyen_van_cua_no():
    """«0,780» vẫn khớp chính nó (và kiểu «.780»): quy tắc chỉ bỏ số 0 ĐẦU, không bỏ số 0 cuối."""
    assert _khop("0,780", "ICC 0.780") and _khop("0,780", "ICC .780")


def _md(than: str) -> str:
    return (f"# 1. ĐẶT VẤN ĐỀ\n\n{than}\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\nx\n\n"
            "# 7. TÀI LIỆU THAM KHẢO\n\n41. Polit DF, Beck CT, Owen SV. Is the CVI an acceptable indicator of content "
            "validity? Res Nurs Health. 2007;30(4):459-467. PMID: 17654487.\n")


def _doi_chieu(tmp_path: Path, than: str, nguon: str):
    oa = tmp_path / "toan_van_oa"
    oa.mkdir()
    (oa / "PMID-17654487_PMC1.xml").write_text(f"<article><p>{nguon}</p></article>", encoding="utf-8", newline="\n")
    md = _md(than)
    _, muc = KDN._tach_tltk(md)
    khoa = {so: KS._khoa_muc(nd, so) for so, nd in muc.items()}
    van = KS.khoang_van_ban(md, "ĐẶT VẤN ĐỀ", "ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP")
    return KS.doi_chieu(van, muc, lambda so: KS.van_toan_van(tmp_path, khoa[so], None))


CAU_C1A = "Câu đạt khi I-CVI ≥ 0,78, toàn thang đạt khi S-CVI/Ave ≥ 0,90 [41]."


def test_ca_that_c1a_polit_khong_con_bao_sai(tmp_path):
    nguon = ("Items with an I-CVI of .78 or higher are considered evidence of good content validity. "
             "The S-CVI/Ave should be .90 or higher.")
    assert _doi_chieu(tmp_path, CAU_C1A, nguon) == []


def test_nguon_chi_co_so_khac_van_bi_bat(tmp_path):
    """Nguồn có «7.8», «78», «1.90» nhưng không có 0,78 hay 0,90 ⇒ vẫn báo «không thấy» cả hai."""
    nguon = "Agreement was 7.8 points on 78 items; the ratio was 1.90 and the cut-off .780."
    kq = _doi_chieu(tmp_path, CAU_C1A, nguon)
    assert [v.khong_thay for v in kq] == [["0,78", "0,90"]]
