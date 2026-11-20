"""Số và loại biến kiểu Việt Nam trong đề cương nộp (soát định dạng 20/11/2026).

1. Bộ sinh đề cương ghi khoảng giá trị kiểu máy («0.1–2000», «1–100000», «2026-01-01–2026-12-31») vào phiếu và bảng
   biến số ⇒ nay thập phân dấu phẩy, nhóm nghìn từ 5 chữ số, ngày dd/mm/yyyy; số 4 chữ số (năm) giữ nguyên.
2. Loại biến «Định danh/thứ bậc» bỏ lửng ⇒ nay «Định danh», «Thứ bậc» (thang Likert) hoặc «Định danh (chọn nhiều)».
3. Đối chiếu biến ↔ đề cương đọc «2.000» thành 2,0 ⇒ LỆCH giả; nay hiểu số kiểu Việt Nam.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import doi_chieu_bien_de_cuong as DC  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402


def test_so_hien_kieu_viet_nam():
    assert SDC._so_hien("0.1") == "0,1"
    assert SDC._so_hien("10000") == "10.000"
    assert SDC._so_hien("100000") == "100.000"
    assert SDC._so_hien("2000") == "2000" and SDC._so_hien("1950") == "1950"
    assert SDC._so_hien("2026-01-01") == "01/01/2026"
    assert SDC._so_hien("abc") == "abc" and SDC._so_hien("") == ""


def test_phieu_va_bang_bien_dung_so_viet():
    r = {"Field Type": "text", "Text Validation Type OR Show Slider Number": "number",
         "Text Validation Min": "0.1", "Text Validation Max": "10000"}
    assert SDC._o_tra_loi(r).endswith("(từ 0,1 đến 10.000)")


def test_loai_bien_ro_rang():
    radio = {"Field Type": "radio", "Choices, Calculations, OR Slider Labels": "1, Quân nhân | 2, Dịch vụ | 3, Khác"}
    likert = {"Field Type": "radio", "Choices, Calculations, OR Slider Labels":
              "1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường | 4, Hài lòng | 5, Rất hài lòng"}
    hop = {"Field Type": "checkbox", "Choices, Calculations, OR Slider Labels": "1, A | 2, B | 3, C"}
    assert SDC._loai_bien(radio) == "Định danh"
    assert SDC._loai_bien(likert) == "Thứ bậc"
    assert SDC._loai_bien(hop) == "Định danh (chọn nhiều)"
    assert SDC._loai_bien({"Field Type": "yesno"}) == "Nhị phân"


def test_doi_chieu_doc_so_viet_nam():
    assert DC._so_may("2.000") == "2000"
    assert DC._so_may("100.000") == "100000"
    assert DC._so_may("1.234,5") == "1234.5"
    assert DC._so_may("0,1") == "0.1" and DC._so_may("0.1") == "0.1"
