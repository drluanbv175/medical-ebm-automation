"""Tiện ích nhận diện cột văn bản/phân loại ổn định giữa các phiên bản pandas."""

from __future__ import annotations

from typing import List

import pandas as pd


def _is_category_dtype(dtype: object) -> bool:
    """Tránh `is_categorical_dtype` vì hàm đó có thể phát deprecation warning."""
    categorical_dtype = getattr(pd, "CategoricalDtype", None)
    if categorical_dtype is not None and isinstance(dtype, categorical_dtype):
        return True
    return str(dtype) == "category"


def text_like_columns(df: pd.DataFrame, *, include_category: bool = True) -> List[str]:
    """Trả tên cột dạng chuỗi/object và (mặc định) category, không dùng select_dtypes.

    Lý do: trên các nhánh pandas mới, `select_dtypes(include=["object", "str"])`
    có thể phát warning hoặc TypeError tùy version. Helper này dùng API dtype
    ổn định hơn để không bỏ sót PII trong cột chuỗi.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 23, phát hiện #3):
    `include_category` trước đây mặc định `False`. `app_data_analysis.py::
    scan_pii()` — bộ quét PII DUY NHẤT của công cụ — gọi hàm này KHÔNG
    truyền `include_category=True`, trong khi `table1()` trong cùng file
    lại truyền `True`, cho thấy cột dtype `category` là tình huống có thật
    (dữ liệu lâm sàng hay được convert sang category để tiết kiệm bộ nhớ)
    nhưng bị bỏ sót ngay ở đúng chỗ quan trọng nhất — cột `category` chứa
    PII (vd họ tên) hoàn toàn không được xét, công cụ báo "sạch" trong khi
    PII thật vẫn còn. Đổi mặc định thành `True` để khớp đúng mục đích hàm
    tự công bố ("không bỏ sót PII trong cột chuỗi") — an toàn hơn là mặc
    định loại trừ.
    """
    cols: List[str] = []
    for col in df.columns:
        dtype = df[col].dtype
        if (
            pd.api.types.is_object_dtype(dtype)
            or pd.api.types.is_string_dtype(dtype)
            or (include_category and _is_category_dtype(dtype))
        ):
            cols.append(col)
    return cols
