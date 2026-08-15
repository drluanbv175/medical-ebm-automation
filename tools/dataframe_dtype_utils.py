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


def text_like_columns(df: pd.DataFrame, *, include_category: bool = False) -> List[str]:
    """Trả tên cột dạng chuỗi/object và tùy chọn category, không dùng select_dtypes.

    Lý do: trên các nhánh pandas mới, `select_dtypes(include=["object", "str"])`
    có thể phát warning hoặc TypeError tùy version. Helper này dùng API dtype
    ổn định hơn để không bỏ sót PII trong cột chuỗi.
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
