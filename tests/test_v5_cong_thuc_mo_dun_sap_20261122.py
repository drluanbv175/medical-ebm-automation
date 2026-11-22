"""V5 — biến phái sinh có công thức «@<mô-đun>»: số của định nghĩa đối chiếu với tham số mô-đun đọc từ SAP (22/11/2026).

Ca thật C1a: biến `tang` định nghĩa «tầng có nₕ < 10 (hoặc trống) gộp …», công thức `@g6_trong_so_survey`; ngưỡng 10
không nằm trong công thức mà do `tools/g6_trong_so_survey.py` đọc từ SAP §4 (`n_toi_thieu`) ⇒ V5 từng báo «cần xem» sai.
Nay: khớp SAP ⇒ không báo, ghi nguồn số vào «dat_canh»; lệch ⇒ LỆCH; không đọc được ⇒ CẦN XEM kèm lý do. Không miễn
chung mọi công thức «@». Dữ liệu giả, không PII.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import doi_chieu_bien_de_cuong as D  # noqa: E402
import g6_trong_so_survey as G  # noqa: E402
import test_doi_chieu_bien_de_cuong_20261115 as T  # noqa: E402

S = T.S
DONG_TANG = ("| tang | Tầng hậu phân tầng | Danh định (tính toán) | ngay_trong_tuan × khunggio_kham; tầng có nₕ < 10 "
             "(hoặc trống) gộp với khung giờ liền kề{them} | Tính toán |\n")


def _sap(n: str = "10") -> str:
    return ("### §3 Kết cục\n\nHài lòng khi điểm ≥ 4/5.\n\n### §4 Phân tích chính\n\n"
            f"svydesign(ids = ~ma_ban_kham, strata = ~tang) rồi postStratify(...). Tầng có nₕ < {n} (hoặc trống) "
            "được gộp với khung giờ liền kề. Thời gian chờ tính mỗi 15 phút.\n\n### §5 Phụ\n\nKhông.\n")


@pytest.fixture()
def de_tai(tmp_path) -> Path:
    d = tmp_path / S
    d.mkdir()
    (d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(T.DE_CUONG + DONG_TANG.format(them=""), encoding="utf-8",
                                                    newline="\n")
    T.ghi_tu_dien(d / "_bo-bien-rieng.csv", T.TRUONG)
    T.ghi_tu_dien(d / f"G5_REDCap_dictionary_{S}.csv", T.TRUONG)
    T.ghi_ps(d, T.PS + [("tang", "@g6_trong_so_survey")])
    (d / "_ma-thieu-theo-bien.csv").write_text(
        "bien,ma,nhan,pham_vi,nguon\nkyvong,998,Không ước lượng,,đề cương\n", encoding="utf-8", newline="\n")
    return d


def _ghi_sap(d: Path, van: str) -> None:
    (d / f"G4_A5_SAP_FINAL_{S}.md").write_text(van, encoding="utf-8", newline="\n")


def _v5_tang(kq) -> list:
    return [(p.muc, p.chi_tiet) for p in kq.phat_hien if p.luat == "V5" and p.bien == "tang"]


def _dat_canh_tang(kq) -> dict:
    return next(x for x in kq.dat_canh if x["bien"] == "tang")


def test_khop_sap_khong_bao_va_ghi_nguon_so(de_tai):
    _ghi_sap(de_tai, _sap("10"))
    kq = D.doi_chieu(de_tai, S)
    assert _v5_tang(kq) == []
    x = _dat_canh_tang(kq)
    assert x["nguon_so"] == ["n_toi_thieu = 10 từ SAP §4"] and x["so_khong_thay_trong_cong_thuc"] == []
    assert "n_toi_thieu = 10 từ SAP §4" in D.markdown(kq)


def test_lech_sap_la_lech(de_tai):
    _ghi_sap(de_tai, _sap("15"))
    v5 = _v5_tang(D.doi_chieu(de_tai, S))
    assert len(v5) == 1 and v5[0][0] == D.LECH and "mâu thuẫn SAP" in v5[0][1] and "15" in v5[0][1], v5


def test_khong_co_sap_giu_can_xem_kem_ly_do(de_tai):
    v5 = _v5_tang(D.doi_chieu(de_tai, S))
    assert v5 and all(m == D.XEM for m, _ in v5) and any("chưa có SAP" in c for _, c in v5), v5


def test_sap_khong_co_tham_so_giu_can_xem(de_tai):
    _ghi_sap(de_tai, _sap("10").replace("Tầng có nₕ < 10 (hoặc trống) được gộp", "Tầng thưa được gộp"))
    v5 = _v5_tang(D.doi_chieu(de_tai, S))
    assert any(m == D.XEM and "không có tham số n_toi_thieu" in c for m, c in v5), v5


def test_khong_mien_chung_moi_cong_thuc_a_cong(de_tai):
    """Mô-đun không khai hàm đọc tham số từ SAP ⇒ vẫn CẦN XEM, kèm lý do — không miễn chung «@»."""
    _ghi_sap(de_tai, _sap("10"))
    T.ghi_ps(de_tai, T.PS + [("tang", "@chuan_bao_cao_items")])
    v5 = _v5_tang(D.doi_chieu(de_tai, S))
    assert any(m == D.XEM and "không khai hàm đọc tham số từ SAP" in c for m, c in v5), v5


def test_so_khac_khong_do_mo_dun_doc_van_can_xem(de_tai):
    (de_tai / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(
        T.DE_CUONG + DONG_TANG.format(them=", sau 7 ngày thì gộp tiếp"), encoding="utf-8", newline="\n")
    _ghi_sap(de_tai, _sap("10"))
    kq = D.doi_chieu(de_tai, S)
    x = _dat_canh_tang(kq)
    assert x["nguon_so"] == ["n_toi_thieu = 10 từ SAP §4"] and x["so_khong_thay_trong_cong_thuc"] == [7.0]
    assert any(m == D.XEM and "7" in c for m, c in _v5_tang(kq))


def test_mo_dun_trong_so_mot_nguon_tham_so_cho_bo_sinh_va_doi_chieu():
    """`doc_tham_so_trong_so` (bộ sinh) và `doi_chieu_so_dinh_nghia` (đối chiếu) đọc CÙNG bảng `THAM_SO_SAP`."""
    sap = _sap("12")
    assert G.doc_tham_so_trong_so(sap, {})["n_toi_thieu"] == 12 == G.tham_so_tu_sap(sap)["n_toi_thieu"]
    assert G.doc_tham_so_trong_so(sap, {})["don_vi_phoi_nhiem"] == 15
    assert G.doi_chieu_so_dinh_nghia("tầng có nₕ < 10 gộp", sap) == [
        {"tham_so": "n_toi_thieu", "muc": "§4", "gia_tri_dinh_nghia": 10.0, "gia_tri_sap": 12.0}]
