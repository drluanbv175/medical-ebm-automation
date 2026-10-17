"""Chuẩn hoá DOI khi cổng A12 (run_g10_assemble) quét tài liệu — 17/10/2026.

Lỗi gốc: regex DOI giữ `)` là ký tự hợp lệ (DOI Lancet «10.1016/S0140-6736(20)30183-5»), nên DOI viết trong ngoặc
đơn «(doi:10.51298/vmj.v549i2.13771)» bị bắt thành «10.51298/vmj.v549i2.13771)». Trên A12 của C1a, 16 DOI «cần tra»
có 5 bản trùng dính `)` (thật ra 11 DOI), và bản dính ngoặc không ghép được với PMID song song đã kiểm rút bài.
Kiểm HÀNH VI: cắt dấu câu cuối + ngoặc đóng không cân; giữ ngoặc cân bằng hợp lệ trong hậu tố; khử trùng không phân
biệt hoa/thường; ghép PMID song song cho DOI viết trong ngoặc. Ngoại tuyến, văn bản fixture tự soạn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import run_g10_assemble as A  # noqa: E402


def test_doi_trong_ngoac_don_khong_dinh_ngoac_va_khong_trung():
    van_ban = ("Nguyễn A. Khảo sát hài lòng. Y học Việt Nam. 2025 (doi:10.51298/vmj.v549i2.13771).\n"
               "| 10.51298/vmj.v549i2.13771 | Khảo sát hài lòng | ✅ |\n"
               "Bùi T. Sự hài lòng. Y học cộng đồng (doi:10.52163/yhc.v64i1.573)\n")
    assert A._dois_from_text(van_ban) == {"10.51298/vmj.v549i2.13771", "10.52163/yhc.v64i1.573"}


def test_dau_cau_cuoi_cau_bi_cat():
    van_ban = ("Xem doi:10.1000/abc. Rồi 10.1000/def, rồi 10.1000/ghi; và doi: 10.1000/jkl: hết.\n"
               "Cuối đoạn (xem 10.1000/mno).\n")
    assert A._dois_from_text(van_ban) == {"10.1000/abc", "10.1000/def", "10.1000/ghi", "10.1000/jkl", "10.1000/mno"}


def test_ngoac_vuong_dong_khong_can_bi_cat():
    assert A._cat_duoi_doi("10.1000/uvw]") == "10.1000/uvw"
    assert A._cat_duoi_doi("10.1000/uvw).]") == "10.1000/uvw"
    assert A._cat_duoi_doi("10.1000/a[1]") == "10.1000/a[1]"


def test_ngoac_can_bang_hop_le_trong_hau_to_duoc_giu():
    van_ban = ("Lancet (xem 10.1016/S0140-6736(20)30183-5).\n"
               "Bài SICI (doi:10.1002/(SICI)1097-0258(19980430)17:8).\n"
               "Hậu tố tận cùng bằng ngoặc cân: 10.5555/abc(2020).\n")
    assert A._dois_from_text(van_ban) == {"10.1016/S0140-6736(20)30183-5", "10.1002/(SICI)1097-0258(19980430)17:8",
                                          "10.5555/abc(2020)"}


def test_khu_trung_khong_phan_biet_hoa_thuong_giu_cach_viet_dau_tien():
    van_ban = "doi:10.1108/IJHCQA-07-2025-0100. Lặp lại: https://doi.org/10.1108/ijhcqa-07-2025-0100\n"
    assert A._dois_from_text(van_ban) == {"10.1108/IJHCQA-07-2025-0100"}


def test_doi_trong_ngoac_ghep_duoc_pmid_song_song_da_kiem(tmp_path):
    ma = "S-A12-NGOAC"
    (tmp_path / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": {
        "11111111": {"status": "resolved", "doi": "10.51298/vmj.v549i2.13771"},
        "22222222": {"status": "resolved", "doi": "10.1108/ijhcqa-07-2025-0100"}}}), encoding="utf-8", newline="\n")
    (tmp_path / f"DE_CUONG_THONG_NHAT_{ma}.md").write_text(
        "1. Tác giả B. Tiêu đề. Tạp chí. 2025 (doi:10.1108/IJHCQA-07-2025-0100).\n"
        "2. Guideline không index PubMed (doi:10.9999/khong-pmid).\n", encoding="utf-8", newline="\n")
    artifact = "| PMID 11111111 | (doi:10.51298/vmj.v549i2.13771) | ✅ |\n"
    dois = A._scan_doi_citation_coverage(artifact, ma, tmp_path)
    assert dois == {"10.51298/vmj.v549i2.13771", "10.1108/IJHCQA-07-2025-0100", "10.9999/khong-pmid"}
    phu = A._doi_co_pmid_da_kiem(dois, {"11111111", "22222222"}, tmp_path)
    assert phu == {"10.51298/vmj.v549i2.13771", "10.1108/IJHCQA-07-2025-0100"}
    assert dois - phu == {"10.9999/khong-pmid"}
