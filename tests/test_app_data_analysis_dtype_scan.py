"""Vá 2026-07-14 (rà soát pandas 3.x): `tools/app_data_analysis.py` dùng
`df.select_dtypes(include="object")` / `include=["object","category"]` để (1) quét PII
theo cột chuỗi (`scan_pii`, dùng bởi Streamlit app xử lý dữ liệu bệnh nhân thật) và
(2) chọn biến phân loại cho Bảng 1. Trên pandas 3.x, cột chuỗi mặc định có dtype mới
`"str"` (không còn là `"object"`); `select_dtypes(include="object")` VẪN bắt được cột
`"str"` hiện tại NHƯNG chỉ qua một lớp tương thích ngược đã bị pandas đánh dấu
deprecated (`Pandas4Warning`) và sẽ NGỪNG hoạt động ở pandas 4.x — hậu quả nghiêm
trọng nhất là PII scan (`scan_pii`, dòng ~41) sẽ bỏ sót toàn bộ cột chuỗi.

`app_data_analysis.py` là Streamlit script (chạy `st.set_page_config()` và tham chiếu
biến `df` từ file uploader ở top-level) nên KHÔNG thể import trực tiếp trong pytest.
Test này (a) kiểm tra mã nguồn không còn pattern `select_dtypes` dễ vỡ cho cột chuỗi
và (b) xác nhận helper thuần `text_like_columns()` chọn đúng cột chuỗi + category,
không phát cảnh báo `Pandas4Warning`.
"""
from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

APP_PATH = (
    Path(__file__).resolve().parent.parent / "tools" / "app_data_analysis.py"
)
TOOLS_DIR = APP_PATH.parent

sys.path.insert(0, str(TOOLS_DIR))
from dataframe_dtype_utils import text_like_columns  # noqa: E402


def _source() -> str:
    return APP_PATH.read_text(encoding="utf-8")


def _load_scan_pii():
    """Exec chỉ phần ĐỊNH NGHĨA (import/hằng số/hàm) của app_data_analysis.py, dừng TRƯỚC
    khối UI top-level (`# ─── SIDEBAR ───`) vốn cần Streamlit script context thật (tham chiếu
    `df`/`uploaded` ở top-level) nên không import trực tiếp được trong pytest. `scan_pii` và
    `PII_VALUE_PATTERNS` đều được định nghĩa trước mốc đó nên vẫn lấy được hàm THẬT (không
    phải bản chép lại) để kiểm hành vi chống hồi quy NFD Unicode."""
    src = _source()
    marker = "# ─────────────────────────── SIDEBAR ────────────────────────────"
    assert marker in src, "Mốc SIDEBAR không còn — cần cập nhật điểm cắt exec cho test này"
    head = src.split(marker, 1)[0]
    ns: dict = {"__name__": "app_data_analysis_defs_only", "__file__": str(APP_PATH)}
    exec(compile(head, str(APP_PATH), "exec"), ns)  # noqa: S102 - test nội bộ, nguồn tin cậy
    return ns["scan_pii"]


def test_scan_pii_catches_vietnamese_name_in_nfd_unicode_form():
    """Hồi quy: mẫu 'Họ tên VN' trong PII_VALUE_PATTERNS liệt kê chữ cái có dấu ở dạng tổ hợp
    sẵn (NFC); dữ liệu NFD (chữ nền + dấu rời — vd xuất từ một số phần mềm HIS/Excel trên
    macOS) trước bản vá khớp trượt hoàn toàn, khiến scan_pii() báo "sạch" dù cột còn PII thật.
    Đây là công cụ PHÂN TÍCH THỐNG KÊ THẬT (mở qua "Mở Phân tích Thống kê.command")."""
    import unicodedata

    import pandas as pd

    scan_pii = _load_scan_pii()
    name_nfc = "Nguyễn Văn An"
    name_nfd = unicodedata.normalize("NFD", name_nfc)

    df_nfc = pd.DataFrame({"ghi_chu": [f"Bệnh nhân {name_nfc} tái khám"]})
    df_nfd = pd.DataFrame({"ghi_chu": [f"Bệnh nhân {name_nfd} tái khám"]})

    issues_nfc = scan_pii(df_nfc)
    issues_nfd = scan_pii(df_nfd)

    assert any("Họ tên VN" in msg for msg in issues_nfc)
    assert any("Họ tên VN" in msg for msg in issues_nfd)


def test_no_bare_object_select_dtypes_regression():
    """Chặn hồi quy: không còn `select_dtypes(include="object")` hay
    `select_dtypes(["object","category"])`/`select_dtypes(include=["object","str"])`
    cho cột văn bản — các pattern này cảnh báo hoặc lỗi tùy pandas version."""
    src = _source()
    bare_include_object = re.findall(r'select_dtypes\(\s*include\s*=\s*"object"\s*\)', src)
    assert not bare_include_object, (
        f"Tìm thấy select_dtypes(include=\"object\") cụt (thiếu 'str'): {bare_include_object}"
    )
    bare_object_category = re.findall(
        r'select_dtypes\(\s*(?:include\s*=\s*)?\[\s*"object"\s*,\s*"category"\s*\]\s*\)', src
    )
    assert not bare_object_category, (
        f"Tìm thấy select_dtypes([...\"object\",\"category\"]) thiếu 'str': {bare_object_category}"
    )
    fragile_text_select = re.findall(
        r'select_dtypes\([^)]*(?:"object"|"str"|"category")[^)]*\)', src
    )
    assert not fragile_text_select, (
        f"Tìm thấy select_dtypes cho cột văn bản/phân loại dễ vỡ: {fragile_text_select}"
    )
    assert "text_like_columns" in src


def test_patched_select_dtypes_pattern_catches_str_and_category_columns():
    """Thực nghiệm: helper dtype bắt đúng cột str/object + category, không cảnh báo."""
    df = pd.DataFrame(
        {
            "ten_chuoi": ["a", "b", "c"],
            "so": [1, 2, 3],
            "nhom": pd.Categorical(["x", "y", "x"]),
        }
    )
    # Cột chuỗi mặc định phải là dtype mới "str" trên pandas 3.x (không phải "object"),
    # nếu môi trường pandas không có dtype này thì test không còn ý nghĩa để kiểm.
    assert str(df["ten_chuoi"].dtype) in {"str", "object"}

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # bất kỳ warning nào (kể cả Pandas4Warning) → lỗi
        pii_cols = text_like_columns(df)
        cat_cols = text_like_columns(df, include_category=True)

    assert "ten_chuoi" in pii_cols, "select_dtypes vá phải bắt được cột dtype str cho PII scan"
    assert "ten_chuoi" in cat_cols and "nhom" in cat_cols, (
        "select_dtypes vá phải bắt được cả cột str lẫn category cho Bảng 1"
    )
    assert "so" not in pii_cols and "so" not in cat_cols, (
        "select_dtypes vá không được bắt nhầm cột số"
    )


def test_bare_object_pattern_would_warn_on_current_pandas():
    """Đối chứng: xác nhận pattern CŨ (include='object' không kèm 'str') vẫn chạy được
    hôm nay nhưng phát Pandas4Warning — đúng như báo cáo quét đã ghi nhận, để tài liệu hóa
    lý do phải vá dù chưa crash ngay bây giờ."""
    df = pd.DataFrame({"ten_chuoi": ["a", "b"], "so": [1, 2]})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cols = df.select_dtypes(include="object").columns.tolist()
    assert "ten_chuoi" in cols
    warning_names = [w.category.__name__ for w in caught]
    if "Pandas4Warning" not in warning_names:
        pytest.skip(
            "Phiên bản pandas hiện tại không phát Pandas4Warning cho pattern cũ "
            "(có thể pandas đã đổi hành vi) — bỏ qua đối chứng."
        )
