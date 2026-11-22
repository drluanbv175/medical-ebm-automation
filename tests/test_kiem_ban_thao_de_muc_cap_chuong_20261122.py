# -*- coding: utf-8 -*-
"""`kiem_ban_thao_tap_chi` đọc đề mục theo CẤP CHƯƠNG, không mặc định `##` (22/11/2026).

Ca thật: bài báo giao thức C1a (`Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md`) dùng `#` cho chương («# TÓM TẮT»,
«# 1. ĐẶT VẤN ĐỀ», «# TÀI LIỆU THAM KHẢO») và `##` cho tên bài cùng các tiểu mục. Bản cũ của `_muc` chỉ tách `##` nên
báo «Thiếu mục TÓM TẮT», «Thiếu mục ABSTRACT», đếm TLTK = 0 và lấy nhãn «GIAO THỨC NGHIÊN CỨU» (4 từ) làm tiêu đề.
Cấp chương nay xác định như K18 (`tieu_chi_ban_thao.tach_ban_thao`).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent.parent
TOOLS = GOC / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import kiem_ban_thao_tap_chi as KB  # noqa: E402

GH = KB.GIOI_HAN["tap_chi_y_duoc_thuc_hanh_175"]
TEN_BAI = "THỰC TRẠNG XÉT NGHIỆM ALBUMIN NIỆU Ở NGƯỜI ĐÁI THÁO ĐƯỜNG: GIAO THỨC NGHIÊN CỨU CẮT NGANG"

#: chương ở cấp 1, tên bài ở cấp 2 dưới nhãn loại bài — đúng bố cục bài báo giao thức C1a
CAP_MOT = f"""# GIAO THỨC NGHIÊN CỨU

## {TEN_BAI}

# TÓM TẮT

**Mục tiêu:** Mô tả tỷ lệ xét nghiệm.

**Từ khoá:** đái tháo đường, albumin niệu, ngoại trú.

# ABSTRACT

**Objective:** Testing rates.

**Keywords:** diabetes, albuminuria, outpatients.

# 1. ĐẶT VẤN ĐỀ

Bệnh thận mạn thường gặp [1],[2].

# 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 2.1. Thiết kế

Nghiên cứu cắt ngang.

## 2.2. Kế hoạch phân tích

Tỷ lệ kèm khoảng tin cậy 95%.

# 3. KẾT QUẢ DỰ KIẾN

Tỷ lệ xét nghiệm sẽ được trình bày theo bảng định trước.

# 4. BÀN LUẬN

So với y văn [2].

# 5. KẾT LUẬN

Cần cải thiện.

# TÀI LIỆU THAM KHẢO

1. Tác giả A. Bài 1. Tạp chí. 2024;1:1-2.
2. Tác giả B. Bài 2. Tạp chí. 2025;2:3-4.
"""


def _do(md: str):
    return KB.do_ban_thao(md, GH)


def test_chuong_cap_mot_doc_du_tom_tat_abstract_tltk_va_ten_bai():
    kq = _do(CAP_MOT)
    assert kq["vi_pham"] == [], kq["vi_pham"]
    so = kq["so_do"]
    assert so["tltk"] == 2
    assert so["tieu_de"] == KB.dem_tu(TEN_BAI)  # tên bài ở «##», không phải nhãn «# GIAO THỨC NGHIÊN CỨU»
    assert so["tom_tat_vi_tu_khoa"] == 3 and so["tom_tat_en_tu_khoa"] == 3


def test_tieu_muc_cap_hai_khong_cat_ngang_chuong():
    """«## 2.1.», «## 2.2.» nằm TRONG chương «# 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP» — chương kéo tới đề mục cùng cấp sau."""
    muc = KB._muc(CAP_MOT)
    pp = muc["ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU"]
    assert "Nghiên cứu cắt ngang." in pp and "Tỷ lệ kèm khoảng tin cậy 95%." in pp
    assert "Tỷ lệ xét nghiệm sẽ được trình bày" not in pp
    assert "2.1. THIẾT KẾ" not in muc  # tiểu mục không thành chương riêng


def test_tom_tat_cap_mot_qua_250_tu_bi_bat():
    md = CAP_MOT.replace("**Mục tiêu:** Mô tả tỷ lệ xét nghiệm.", "**Mục tiêu:** " + " ".join(["chữ"] * 260))
    assert any("TÓM TẮT" in x and "> 250" in x for x in _do(md)["vi_pham"])


def test_thieu_abstract_o_cap_mot_van_bi_bat():
    dau, sau = CAP_MOT.split("# ABSTRACT")
    md = dau + "# 1. ĐẶT VẤN ĐỀ" + sau.split("# 1. ĐẶT VẤN ĐỀ", 1)[1]
    loi = _do(md)["vi_pham"]
    assert "Thiếu mục ABSTRACT" in loi and "Thiếu mục TÓM TẮT" not in loi


def test_trich_dan_o_ket_qua_cap_mot_bi_bat():
    md = CAP_MOT.replace("Tỷ lệ xét nghiệm sẽ được trình bày theo bảng định trước.", "Tỷ lệ là 40% [1].")
    assert any("mục KẾT QUẢ DỰ KIẾN" in x for x in _do(md)["vi_pham"])


def test_trich_dan_gop_trong_tltk_cap_mot_khong_tinh():
    """Thân bài cắt tại «# TÀI LIỆU THAM KHẢO» (mọi cấp) — ngoặc gộp trong một mục TLTK không phải trích dẫn gộp."""
    md = CAP_MOT.replace("2. Tác giả B. Bài 2.", "2. Tác giả B. Bài 2 (bình luận về [3, 4]).")
    assert not any("Trích dẫn gộp" in x for x in _do(md)["vi_pham"])
    md_than = CAP_MOT.replace("So với y văn [2].", "So với y văn [1, 2].")
    assert any("Trích dẫn gộp" in x for x in _do(md_than)["vi_pham"])


def test_dem_tltk_ba_kieu_danh_so():
    ds = "\n".join(f"{i}. Tác giả. Bài {i}. T. 2024;1:1." for i in range(1, 20))
    ds += "\n\n**Văn bản pháp quy**\n\n- [V1] Bộ Y tế. Quyết định 1.\n- [V2] Bộ Y tế. Quyết định 2.\n"
    md = CAP_MOT.split("# TÀI LIỆU THAM KHẢO")[0] + "# TÀI LIỆU THAM KHẢO\n\n" + ds
    kq = _do(md)
    assert kq["so_do"]["tltk"] == 21
    assert any("21 tài liệu tham khảo > 20" in x for x in kq["vi_pham"])
    vuong = "\n\n".join(f"[{i}] Tác giả. Bài {i}." for i in range(1, 4))
    md_vuong = CAP_MOT.split("# TÀI LIỆU THAM KHẢO")[0] + "# TÀI LIỆU THAM KHẢO\n\n" + vuong + "\n"
    assert _do(md_vuong)["so_do"]["tltk"] == 3


def test_de_muc_cap_tren_dong_chuong_cap_hai():
    """Chương ở `##`: đề mục `#` đứng sau (phụ lục cấp 1) đóng chương TLTK — mục đánh số của phụ lục không bị đếm."""
    than = CAP_MOT.split(TEN_BAI, 1)[1].replace("\n# ", "\n## ")  # mọi chương xuống `##`
    md = "# " + TEN_BAI + than + "\n# PHỤ LỤC\n\n3. Bảng kiểm STROBE.\n"
    assert KB._cap_chuong(md) == 2
    assert _do(md)["so_do"]["tltk"] == 2


def test_ban_khong_co_chuong_giu_cach_cu():
    """Không nhận ra chương IMRAD nào ⇒ `_muc` tách `##`, tiêu đề là đề mục `#` đầu tiên (hành vi trước 22/11)."""
    md = "# TÊN BÀI\n\n## PHẦN MỘT\n\nA.\n\n## PHẦN HAI\n\nB.\n"
    assert KB._cap_chuong(md) == 0
    assert set(KB._muc(md)) == {"PHẦN MỘT", "PHẦN HAI"}
    assert KB._tieu_de(md) == "TÊN BÀI"


def test_bai_bao_giao_thuc_c1a_that_doc_dung_cap_chuong():
    p = GOC / "exports" / "hai-long-benh-nhan-C1a-BVQY175" / "Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md"
    if not p.is_file():
        pytest.skip("không có bài báo giao thức C1a trong cây")
    md = p.read_text(encoding="utf-8")
    assert KB._cap_chuong(md) == 1
    kq = _do(md)
    assert "Thiếu mục TÓM TẮT" not in kq["vi_pham"]
    assert kq["so_do"]["tltk"] >= 12
    assert kq["so_do"]["tieu_de"] > 4  # không còn lấy nhãn «GIAO THỨC NGHIÊN CỨU»
