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


def resolve_source_path(ref) -> Path:
    """Tìm bản sao file HTML nguồn: ưu tiên ``SOURCE_DIR / meta['source']`` (tệp có trong git, chạy được
    trên mọi máy/CI), sau đó mới ``meta['source_path']`` (đường TUYỆT ĐỐI ghi lúc nhập — thường là
    /Users/… của một máy Mac, giữ nguyên trong dữ liệu vì dashboard dùng làm mặc định khi nhập lại).

    Vắng cả hai ⇒ ``pytest.fail`` (KHÔNG skip): skip từng làm test chống bịa của 45 thang điểm không
    chạy ở bất kỳ đâu ngoài một máy Mac (#23, 26/09/2026).
    """
    meta = ref.get("meta", {}) if isinstance(ref, dict) else {}
    ung_vien = []
    if meta.get("source"):
        ung_vien.append(ri.SOURCE_DIR / Path(str(meta["source"])).name)
    if meta.get("source_path"):
        ung_vien.append(Path(str(meta["source_path"])))
    for duong in ung_vien:
        if duong.is_file():
            return duong
    pytest.fail(
        "Không tìm thấy bản sao file nguồn 45 thang điểm (đã thử: "
        + ", ".join(str(d) for d in ung_vien) + ") — không kiểm được «trích nguyên văn»."
    )


def test_items_are_verbatim_from_source():
    """Mỗi tên thang điểm phải xuất hiện y nguyên trong file HTML nguồn đã lưu."""
    ref = ri.load_reference()
    if not ref:
        pytest.skip("Chưa nhập tài liệu.")
    src_path = resolve_source_path(ref)
    src = src_path.read_text(encoding="utf-8")
    for it in ref["items"]:
        # tên thang điểm là chuỗi con của tài liệu gốc -> không bịa
        assert it["name"] in src, f"Tên không khớp nguồn: {it['name']}"


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ri.import_from_html("/khong/ton/tai/file_khong_co.html")
