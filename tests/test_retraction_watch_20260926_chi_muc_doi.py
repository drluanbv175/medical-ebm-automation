"""Hồi quy phát hiện #31 (đợt dò nâng cấp 26/09/2026): nền Retraction Watch có chỉ mục THEO DOI.

Tái hiện gốc: `RetractionWatchIndex.nap()` bỏ mọi dòng không có `OriginalPaperPubMedID` (33.294/72.606
dòng thật, 31.778 là rút bài hẳn) và chỉ khoá theo PMID; cổng verify_dashboard chỉ hỏi nền bằng PMID.
Cùng một bài đã rút: trích bằng PMID thì bị chặn cứng, trích bằng DOI thì chỉ cảnh báo «chưa kiểm».

Bản vá thêm `tra_doi()` (hàm MỚI) — chữ ký và hành vi `tra()` theo PMID giữ nguyên.
Dựng CSV THẬT theo đúng tên cột Retraction Watch; không mock nội bộ, không mạng.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.retraction_watch import RetractionWatchIndex, chuan_hoa_doi  # noqa: E402

_COLS = ["Title", "OriginalPaperDOI", "OriginalPaperPubMedID", "RetractionNature", "RetractionPubMedID",
         "RetractionDOI", "RetractionDate", "Reason", "Journal"]


def _viet_csv(tmp_path: Path, hang: list[dict]) -> Path:
    p = tmp_path / "retraction_watch.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=_COLS)
        w.writeheader()
        for h in hang:
            w.writerow({c: h.get(c, "") for c in _COLS})
    return p


def _chi_muc(tmp_path: Path) -> RetractionWatchIndex:
    hang = [
        # (1) DOI-only: không có PMID (giữ chỗ "0") — trước bản vá bị bỏ hẳn
        {"Title": "Bài chỉ có DOI", "OriginalPaperDOI": "10.1007/s11042-022-14078-2",
         "OriginalPaperPubMedID": "0", "RetractionNature": "Retraction", "Reason": "+Paper Mill;"},
        # (2) dòng có PMID, gói trích bằng DOI
        {"Title": "Bài có PMID", "OriginalPaperDOI": "10.1007/S11042-023-15640-2",
         "OriginalPaperPubMedID": "37362712", "RetractionNature": "Retraction"},
        # (3) DOI rút rồi PHỤC HỒI (hai dòng, reinstatement sau)
        {"Title": "Bài được phục hồi", "OriginalPaperDOI": "10.1000/phuc.hoi", "OriginalPaperPubMedID": "",
         "RetractionNature": "Retraction"},
        {"Title": "Bài được phục hồi", "OriginalPaperDOI": "10.1000/phuc.hoi", "OriginalPaperPubMedID": "",
         "RetractionNature": "Reinstatement"},
        # (4) giá trị giữ chỗ
        {"Title": "Không rõ DOI", "OriginalPaperDOI": "Unavailable", "OriginalPaperPubMedID": "0",
         "RetractionNature": "Retraction"},
        # (5) EoC trước, rút sau — rút phải thắng bất kể thứ tự
        {"Title": "EoC rồi rút", "OriginalPaperDOI": "10.1000/eoc.roi.rut",
         "RetractionNature": "Expression of concern"},
        {"Title": "EoC rồi rút", "OriginalPaperDOI": "10.1000/eoc.roi.rut", "RetractionNature": "Retraction"},
        # (6) chỉ Correction — không phải phán quyết
        {"Title": "Chỉ đính chính", "OriginalPaperDOI": "10.1000/dinh.chinh", "RetractionNature": "Correction"},
        # (7) PMID được phục hồi ở dòng KHÔNG có DOI ⇒ DOI của chính bài đó (dòng rút) cũng không kết luận
        {"Title": "Phục hồi theo PMID", "OriginalPaperDOI": "10.1000/pmid.phuc.hoi",
         "OriginalPaperPubMedID": "11112222", "RetractionNature": "Retraction"},
        {"Title": "Phục hồi theo PMID", "OriginalPaperDOI": "", "OriginalPaperPubMedID": "11112222",
         "RetractionNature": "Reinstatement"},
        # (8) EoC thuần
        {"Title": "Chỉ EoC", "OriginalPaperDOI": "10.1000/chi.eoc", "RetractionNature": "Expression of Concern"},
    ]
    return RetractionWatchIndex(csv_path=_viet_csv(tmp_path, hang), meta_path=tmp_path / "khong_co.json")


def test_dong_chi_co_doi_duoc_tra_ra(tmp_path):
    idx = _chi_muc(tmp_path)
    kq = idx.tra_doi("10.1007/s11042-022-14078-2")
    assert kq and kq["status"] == "retracted" and kq["source"] == "retraction_watch"
    assert kq["title"] == "Bài chỉ có DOI", "phải giữ tiêu đề RW để bác sĩ đối chiếu"


def test_dong_co_pmid_tra_duoc_bang_doi_bien_the_chu_hoa_tien_to(tmp_path):
    idx = _chi_muc(tmp_path)
    for bien_the in ("10.1007/s11042-023-15640-2", "10.1007/S11042-023-15640-2",
                     "https://doi.org/10.1007/s11042-023-15640-2", "doi:10.1007/s11042-023-15640-2",
                     "  https://dx.doi.org/10.1007/S11042-023-15640-2 "):
        kq = idx.tra_doi(bien_the)
        assert kq and kq["status"] == "retracted", bien_the
    assert idx.tra("37362712")["status"] == "retracted", "chỉ mục PMID phải giữ nguyên"


def test_phuc_hoi_theo_doi_khong_ket_luan(tmp_path):
    assert _chi_muc(tmp_path).tra_doi("10.1000/phuc.hoi") is None


def test_phuc_hoi_theo_pmid_keo_theo_doi_cung_bai(tmp_path):
    idx = _chi_muc(tmp_path)
    assert idx.tra("11112222") is None
    assert idx.tra_doi("10.1000/pmid.phuc.hoi") is None, "cùng một bài: PMID «không kết luận» mà DOI «đã rút» = đỏ giả"


def test_gia_tri_giu_cho_khong_thanh_khoa(tmp_path):
    idx = _chi_muc(tmp_path)
    assert idx.tra_doi("Unavailable") is None and idx.tra_doi("0") is None and idx.tra_doi("") is None
    assert "unavailable" not in idx._chi_muc_doi


def test_rut_thang_eoc_va_correction_khong_phai_phan_quyet(tmp_path):
    idx = _chi_muc(tmp_path)
    assert idx.tra_doi("10.1000/eoc.roi.rut")["status"] == "retracted"
    assert idx.tra_doi("10.1000/chi.eoc")["status"] == "expression_of_concern"
    assert idx.tra_doi("10.1000/dinh.chinh") is None


def test_vang_mat_la_none_khong_phai_ok(tmp_path):
    idx = _chi_muc(tmp_path)
    assert idx.tra_doi("10.1000/khong.co.trong.danh.muc") is None
    assert idx.san_sang_doi() and idx.so_ban_ghi_doi() >= 5


def test_khong_co_csv_thi_khong_san_sang(tmp_path):
    idx = RetractionWatchIndex(csv_path=tmp_path / "vang.csv", meta_path=tmp_path / "vang.json")
    assert idx.san_sang_doi() is False and idx.tra_doi("10.1007/s11042-022-14078-2") is None


def test_chuan_hoa_doi():
    assert chuan_hoa_doi(" HTTPS://DOI.ORG/10.1000/ABC ") == "10.1000/abc"
    assert chuan_hoa_doi("doi: 10.1000/x") == "10.1000/x"
    assert chuan_hoa_doi("unavailable") is None and chuan_hoa_doi("11.1/x") is None and chuan_hoa_doi(None) is None
