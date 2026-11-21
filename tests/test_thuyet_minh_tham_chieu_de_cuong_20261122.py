"""Thuyết minh DKCT.02: tham chiếu chéo theo đánh số đề cương phải ghi «của đề cương» (22/11/2026).

Thuyết minh bỏ số mục của đề cương khi chép, nên «mục 2.6.4», «Bảng 2.2», «Phụ lục C» không trỏ được trong thuyết minh.
Lần kiểm 22/11 còn 55 (C1a) và 26 (BTM) chỗ như vậy.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import ho_so_dtcs_bvqy175 as H  # noqa: E402

CO = H.nhan_co_trong_thuyet_minh([["**Bảng 2.1. Các nguồn sai lệch**", "#### 2.6.1.1. Bộ câu hỏi"]])


def _g(s: str) -> str:
    return H.ghi_nguon_tham_chieu([s], CO)[0]


def test_tham_chieu_khong_tro_duoc_duoc_ghi_cua_de_cuong():
    assert _g("Xem mục 2.6.4.") == "Xem mục 2.6.4 của đề cương."
    assert _g("theo Bảng 2.2") == "theo Bảng 2.2 của đề cương"
    assert _g("đơn ở Phụ lục B") == "đơn ở Phụ lục B của đề cương"


def test_cum_khoang_va_danh_sach_chi_ghi_mot_lan_o_cuoi():
    assert _g("(mục 3.3–3.4)") == "(mục 3.3–3.4 của đề cương)"
    assert _g("Phụ lục C và D") == "Phụ lục C và D của đề cương"


def test_bang_co_chu_thich_giu_nguyen_con_muc_luon_tro_ve_de_cuong():
    assert _g("như Bảng 2.1") == "như Bảng 2.1"
    # bộ dựng Word bỏ số đề mục ⇒ dù văn bản chép có «#### 2.6.1.1.», «mục 2.6.1.1» vẫn trỏ về đề cương
    assert _g("mục 2.6.1.1 nêu rõ") == "mục 2.6.1.1 của đề cương nêu rõ"
    # cụm lẫn: một phần không có trong thuyết minh ⇒ vẫn ghi nguồn
    assert _g("Bảng 2.1–2.3") == "Bảng 2.1–2.3 của đề cương"


def test_khong_ghi_lap_va_khong_bat_nham_chu_khac():
    assert _g("mục 2.6.4 của đề cương") == "mục 2.6.4 của đề cương"
    assert _g("Phụ lục B (đề cương)") == "Phụ lục B (đề cương)"
    assert _g("mục tiêu 1 năm 2026; mục 2, 3") == "mục tiêu 1 năm 2026; mục 2, 3"
    assert _g("![Hình 3.1](hinh/h31.png)") == "![Hình 3.1](hinh/h31.png)"  # dòng ảnh là chính hình


def test_kiem_chi_dem_tham_chieu_chua_ghi_nguon():
    van = "mục 2.6.4 của đề cương; Bảng 2.3; Phụ lục B (đề cương); mục 3.1"
    assert H.dem_tham_chieu_chua_ghi_nguon(van) == 2
    assert H.dem_tham_chieu_chua_ghi_nguon(_g("Bảng 2.3 và mục 3.1")) == 0
    # chính dòng chú thích và tham chiếu tới bảng có chú thích trong văn bản không bị đếm
    assert H.dem_tham_chieu_chua_ghi_nguon("Bảng 2.1. Các nguồn sai lệch\ntrình bày ở Bảng 2.1.\nxem Bảng 2.4.") == 1
