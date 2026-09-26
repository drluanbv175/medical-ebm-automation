"""Hồi quy #23 (26/09/2026): test chống bịa của 45 thang điểm phải CHẠY ở mọi nơi, không chỉ trên một máy Mac.

`meta['source_path']` trong data/reference/clinical_scores_45.json là đường tuyệt đối /Users/… (giữ nguyên —
dashboard dùng làm mặc định khi nhập lại) nên test cũ skip ở mọi máy khác. Bản sao nguồn có trong git ở
`SOURCE_DIR / meta['source']`; `resolve_source_path` ưu tiên đường đó, vắng cả hai thì FAIL (không skip).
"""
from __future__ import annotations

import copy

import pytest

from app.clinical_scores import reference_import as ri
from tests import test_reference_import as T


def _chay_khong_skip(ham) -> None:
    """Gọi test gốc; bị skip thì coi là ĐỎ — skip chính là lỗi #23 cần chặn."""
    try:
        ham()
    except pytest.skip.Exception as exc:
        pytest.fail(f"test chống bịa bị SKIP thay vì chạy: {exc}")


def test_resolve_uu_tien_ban_sao_trong_repo_du_source_path_tuyet_doi_cua_may_khac():
    ref = ri.load_reference()
    assert ref, "data/reference/clinical_scores_45.json (có trong git) không nạp được"
    ref = copy.deepcopy(ref)
    ref["meta"]["source_path"] = "/Users/may-khac/khong-ton-tai/Thang_diem.html"
    duong = T.resolve_source_path(ref)
    assert duong == ri.SOURCE_DIR / ref["meta"]["source"]
    assert duong.is_file()


def test_du_lieu_khong_bi_doi_source_path():
    """Không được «sửa» bằng cách đổi source_path sang tương đối trong dữ liệu (hợp đồng với dashboard)."""
    ref = ri.load_reference()
    assert ref and ref["meta"]["source_path"].endswith(ref["meta"]["source"])


def test_verbatim_chay_that_va_dat_du_45():
    ref = ri.load_reference()
    assert ref and ref["meta"]["count"] == len(ref["items"]) == 45
    _chay_khong_skip(T.test_items_are_verbatim_from_source)  # không được skip, không được đỏ


def test_ten_bi_sua_thi_do(monkeypatch):
    """Đột biến dữ liệu: bịa một tên thang điểm ⇒ test chống bịa phải ĐỎ (không skip)."""
    ref = copy.deepcopy(ri.load_reference())
    ref["items"][0]["name"] = ref["items"][0]["name"] + " — tên bịa ZZZ-KHONG-CO-TRONG-NGUON"
    monkeypatch.setattr(ri, "load_reference", lambda: ref)
    with pytest.raises(AssertionError, match="Tên không khớp nguồn"):
        _chay_khong_skip(T.test_items_are_verbatim_from_source)


def test_vang_ca_hai_duong_thi_fail_khong_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(ri, "SOURCE_DIR", tmp_path / "khong-co")
    ref = {"meta": {"source": "x.html", "source_path": str(tmp_path / "cung-khong-co.html")}, "items": []}
    try:
        T.resolve_source_path(ref)
    except pytest.skip.Exception as exc:
        pytest.fail(f"vắng file nguồn phải FAIL, không được SKIP: {exc}")
    except pytest.fail.Exception as exc:
        assert "Không tìm thấy bản sao file nguồn" in str(exc)
    else:
        pytest.fail("vắng cả hai đường mà resolve_source_path không báo lỗi")
