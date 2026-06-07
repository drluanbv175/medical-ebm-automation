"""45 thang điểm: bảo đảm CHỈ trích nguyên văn từ file HTML nguồn (không bịa)."""
from pathlib import Path

import pytest

from app.clinical_scores import reference_import as ri


def test_load_reference_structure():
    ref = ri.load_reference()
    if not ref:
        pytest.skip("Chưa nhập tài liệu 45 thang điểm (chạy import_from_html trước).")
    assert ref["meta"]["count"] == len(ref["items"]) > 0
    for it in ref["items"]:
        assert it["name"] and it["html"]
        assert "group" in it and "evidence" in it


def test_items_are_verbatim_from_source():
    """Mỗi tên thang điểm phải xuất hiện y nguyên trong file HTML nguồn đã lưu."""
    ref = ri.load_reference()
    if not ref:
        pytest.skip("Chưa nhập tài liệu.")
    src_path = Path(ref["meta"].get("source_path", ""))
    if not src_path.exists():
        pytest.skip("Không tìm thấy bản sao file nguồn.")
    src = src_path.read_text(encoding="utf-8")
    for it in ref["items"]:
        # tên thang điểm là chuỗi con của tài liệu gốc -> không bịa
        assert it["name"] in src, f"Tên không khớp nguồn: {it['name']}"


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ri.import_from_html("/khong/ton/tai/file_khong_co.html")
