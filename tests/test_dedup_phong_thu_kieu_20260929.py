"""Hồi quy 29/09/2026: khử trùng lặp tự phòng thủ khi `publication_date` là SỐ NGUYÊN.

Lượt `weekly_safety.sh` 29/09/2026 18:31 chạy trên cây chưa có bản vá normalizer và sập ở
`deduplication._same_version` (`TypeError: 'int' object is not subscriptable`). Các test ở đây gọi
THẲNG `deduplicate`/`_same_version` với dict chưa qua `normalize` — tức kiểm lớp phòng thủ riêng của
bước 3, độc lập với `tests/test_publication_date_int_core_20260929.py` (kiểm bước 2).
"""
from __future__ import annotations

from app.services.deduplication import _key_for, _same_version, deduplicate

TIEU_DE = "Empagliflozin in heart failure with preserved ejection fraction"


def test_same_version_nam_so_nguyen_va_chuoi_cung_nam_la_cung_ban():
    assert _same_version({"publication_date": 2026}, {"publication_date": "2026-03-01"}) is True


def test_same_version_nam_so_nguyen_khac_nam_la_khac_ban():
    assert _same_version({"publication_date": 2024}, {"publication_date": "2026"}) is False


def test_same_version_chi_mot_ben_co_nam_so_nguyen_van_fail_closed():
    """Ngữ nghĩa vá 05/09 giữ nguyên: chỉ MỘT bên có năm ⇒ không xác nhận cùng phiên bản."""
    assert _same_version({"publication_date": 2026}, {"publication_date": None}) is False
    assert _same_version({"publication_date": None}, {"publication_date": 2026}) is False


def test_same_version_ca_hai_thieu_nam_van_la_cung_ban():
    assert _same_version({"publication_date": None}, {"publication_date": ""}) is True


def test_same_version_guideline_version_so_khong_sap():
    a = {"publication_date": 2026, "guideline_version": 2}
    b = {"publication_date": "2026", "guideline_version": "3"}
    assert _same_version(a, b) is False


def test_key_for_guideline_nam_so_nguyen_khong_sap():
    item = {"study_type": "guideline", "journal_or_organization": "ESC",
            "title": TIEU_DE, "publication_date": 2026}
    assert _key_for(item).endswith(":2026")


def test_deduplicate_khong_sap_va_van_gop_dung_khi_co_nam_so_nguyen():
    items = [
        {"title": TIEU_DE, "publication_date": 2026},
        {"title": TIEU_DE + ".", "publication_date": "2026-05-01"},
        {"title": TIEU_DE, "publication_date": 2021},
    ]
    chinh, lien_ket = deduplicate(items)
    assert chinh == [0, 2]
    assert lien_ket == [(0, 1, "title_similarity")]
