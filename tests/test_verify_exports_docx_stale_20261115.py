"""EXP-DOCX-STALE (15/11/2026) — `.md` trong exports/ đổi mà bản Word cùng tên được theo dõi không đổi cùng commit.

Kiểm toàn hệ theo khung 12 bước: ba bản Word (gói G2 C1a, SAP C1a, SAP BTM) không được xuất lại sau khi `.md` sửa ở
giai đoạn 4. Mỗi test khoá MỘT hành vi của hàm thuần `docx_chua_xuat_lai`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import verify_exports_integrity as V  # noqa: E402

MD = "exports/ZZ/G4_A5_SAP_FINAL_ZZ.md"
DOCX = "exports/ZZ/G4_A5_SAP_FINAL_ZZ.docx"


def test_md_doi_ma_docx_duoc_theo_doi_khong_doi_la_chan():
    assert V.docx_chua_xuat_lai({MD}, {MD, DOCX}) == [MD]


def test_md_va_docx_cung_doi_la_dat():
    assert V.docx_chua_xuat_lai({MD, DOCX}, {MD, DOCX}) == []


def test_docx_khong_duoc_theo_doi_thi_khong_xet():
    assert V.docx_chua_xuat_lai({MD}, {MD}) == []


def test_chi_xet_md_trong_exports():
    assert V.docx_chua_xuat_lai({"docs/X.md"}, {"docs/X.md", "docs/X.docx"}) == []
    assert V.docx_chua_xuat_lai({"exports/ZZ/a.csv"}, {"exports/ZZ/a.csv", "exports/ZZ/a.docx"}) == []
