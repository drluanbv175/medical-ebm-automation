"""Hồi quy phát hiện #3 (Critical) của Workflow đối kháng đa-agent 2026-09-05
(vòng 23) trong tools/dataframe_dtype_utils.py::text_like_columns().

CƠ CHẾ LỖI: `text_like_columns()` tuyên bố mục đích "không bỏ sót PII trong
cột chuỗi" (docstring), nhưng tham số `include_category` mặc định `False`
loại hẳn cột dtype `category` ra khỏi kết quả. `tools/app_data_analysis.py
::scan_pii()` — bộ quét PII DUY NHẤT của công cụ — gọi `text_like_columns
(df)` KHÔNG truyền `include_category=True`, trong khi `table1()` cùng file
lại gọi với `include_category=True` — chứng tỏ cột `category` là tình
huống thực tế đã được lường trước ở nơi khác nhưng bị bỏ sót ở bộ quét PII.

Dữ liệu lâm sàng thường được convert sang dtype `category` để tiết kiệm bộ
nhớ (rất phổ biến khi đọc CSV lớn hoặc sau groupby), nên đây không phải
tình huống hiếm gặp. Một cột `ho_ten` (họ tên bệnh nhân) dtype `category`
hoàn toàn không được `scan_pii()` xét tới — công cụ báo "sạch" trong khi
PII thật vẫn còn.

BẢN VÁ: đổi mặc định `include_category` thành `True` — khớp đúng mục đích
hàm tự công bố. Callers muốn loại trừ category vẫn truyền
`include_category=False` tường minh.

Nguyên tắc viết test: gọi THẲNG text_like_columns() thật."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import pandas as pd  # noqa: E402
from dataframe_dtype_utils import text_like_columns  # noqa: E402


class TestCotCategoryKhongConBiBoSotOMacDinh:
    """★★★ Ca chính — cột dtype category chứa PII phải được liệt kê ở lời
    gọi MẶC ĐỊNH (không truyền include_category), đúng cách scan_pii() gọi."""

    def test_cot_ho_ten_category_duoc_bat_o_mac_dinh(self):
        df = pd.DataFrame({
            "ho_ten": pd.Categorical(["Nguyễn Văn A", "Trần Thị B", "Nguyễn Văn A"]),
            "ket_qua": ["âm tính", "dương tính", "âm tính"],
        })
        cols = text_like_columns(df)
        assert "ho_ten" in cols, (
            "TRƯỚC bản vá: include_category mặc định False khiến cột "
            "'ho_ten' (dtype category, chứa họ tên bệnh nhân) hoàn toàn "
            "không được scan_pii() xét tới — công cụ báo 'sạch' dù còn PII"
        )
        assert "ket_qua" in cols

    def test_include_category_false_tuong_minh_van_loai_tru_dung(self):
        """Đối chứng bắt buộc — caller vẫn có thể tường minh loại trừ
        category nếu thật sự cần (vd table1() không muốn trộn kiểu)."""
        df = pd.DataFrame({
            "ho_ten": pd.Categorical(["Nguyễn Văn A", "Trần Thị B"]),
            "ket_qua": ["âm tính", "dương tính"],
        })
        cols = text_like_columns(df, include_category=False)
        assert "ho_ten" not in cols
        assert "ket_qua" in cols

    def test_include_category_true_tuong_minh_khong_doi(self):
        df = pd.DataFrame({
            "nhom": pd.Categorical(["x", "y", "x"]),
            "so": [1, 2, 3],
        })
        cols = text_like_columns(df, include_category=True)
        assert "nhom" in cols
        assert "so" not in cols

    def test_cot_so_khong_bao_gio_bi_bat_nham(self):
        """Đối chứng — cột số vẫn phải bị loại trừ dù ở chế độ mặc định mới."""
        df = pd.DataFrame({"tuoi": [25, 30, 45]})
        cols = text_like_columns(df)
        assert "tuoi" not in cols
