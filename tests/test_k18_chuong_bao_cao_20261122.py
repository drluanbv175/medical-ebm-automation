"""K18 nhận chương của báo cáo tổng hợp («CHƯƠNG 3. KẾT QUẢ…») — tools/tieu_chi_ban_thao.py (22/11/2026).

Đo thật: K18 áp lên báo cáo nghiệm thu của 8 thiết kế giả lập báo «thiếu» gần như mọi mục vì không nhận chương nào
(tên chương bắt đầu bằng «CHƯƠNG n.») — số «thiếu» là giả, không phải báo cáo thiếu nội dung."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import tieu_chi_ban_thao as T  # noqa: E402


def test_nhan_tien_to_chuong():
    assert T.khoa_imrad("CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU") == "phuong_phap"
    assert T.khoa_imrad("CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU") == "ket_qua"
    assert T.khoa_imrad("Chương 4: Bàn luận") == "ban_luan"
    assert T.khoa_imrad("CHAPTER 2 METHODS") == "phuong_phap"
    # không đổi hành vi cũ
    assert T.khoa_imrad("II. PHƯƠNG PHÁP") == "phuong_phap"
    assert T.khoa_imrad("KẾT LUẬN") == "ket_luan"
    assert T.khoa_imrad("CHƯƠNG TRÌNH CAN THIỆP") is None   # «CHƯƠNG» không kèm số thứ tự không phải tiền tố chương


def test_bao_cao_co_chuong_duoc_tach():
    md = "\n".join([
        "**BÁO CÁO TỔNG HỢP KẾT QUẢ ĐỀ TÀI**", "", "# ĐẶT VẤN ĐỀ", "", "Tăng huyết áp phổ biến [1].", "",
        "# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", "", "Nghiên cứu cắt ngang.", "",
        "# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU", "", "Tỷ lệ là 52,0%.", "", "# CHƯƠNG 4. BÀN LUẬN", "", "Phù hợp [1].", "",
        "# KẾT LUẬN", "", "Một nửa đạt.", "", "# TÀI LIỆU THAM KHẢO", "", "1. A. B. 2020.", ""])
    bt = T.tach_ban_thao(md)
    assert {"gioi_thieu", "phuong_phap", "ket_qua", "ban_luan", "ket_luan"} <= set(bt.chuong)


def test_tong_quan_tai_lieu_la_boi_canh():
    assert T.khoa_imrad("CHƯƠNG 1. TỔNG QUAN TÀI LIỆU") == "gioi_thieu"
    assert T.khoa_imrad("TỔNG QUAN HỆ THỐNG VÀ PHÂN TÍCH GỘP") is None   # không nhầm tên thiết kế


def test_ten_bai_co_dau_hai_cham_va_nhan_khong_phai_ten():
    md = "\n".join(["**HIỆU QUẢ CỦA TIN NHẮN NHẮC UỐNG THUỐC: THỬ NGHIỆM LÂM SÀNG NGẪU NHIÊN CÓ ĐỐI CHỨNG**", "",
                    "**KẾT QUẢ CHÍNH CỦA NGHIÊN CỨU:**", "", "# ĐẶT VẤN ĐỀ", "", "Nội dung [1].", "",
                    "# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU", "", "Số liệu.", ""])
    ten = [p.van for p in T.tach_ban_thao(md).tieu_de]
    assert any("THỬ NGHIỆM LÂM SÀNG NGẪU NHIÊN" in t for t in ten)
    assert not any(t.startswith("KẾT QUẢ CHÍNH") for t in ten)


def test_cau_khoang_trong_thieu_rct():
    import re
    # K18 so mẫu không phân biệt hoa thường (cham_muc)
    assert re.search(T._THIEU_KT, "Thiếu RCT tại Việt Nam với kết cục tỷ lệ kiểm soát huyết áp.", re.IGNORECASE)
    assert re.search(T._THIEU_KT, "thiếu nghiên cứu trên người cao tuổi", re.IGNORECASE)
