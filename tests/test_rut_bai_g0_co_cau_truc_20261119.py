"""Kiểm rút bài của G0-T3 phải là DANH SÁCH MÃ có cấu trúc, không suy từ câu văn (19/11/2026, bác sĩ duyệt).

Lỗ đo được: `nhat_quan_xuyen_cong._da_kiem_rut_bai` đọc câu văn tự do của khoá `rut_bai` trong
`G0_TONG_HOP_BANG_CHUNG_<mã>.json` và coi MỌI dãy 7–8 chữ số là «PMID đã kiểm rút bài». Câu «PMID x chưa kiểm được»
cũng thành đã kiểm ⇒ mục TLTK trích PMID đó không bị báo «chưa có bản ghi kiểm rút bài» (báo xanh giả về an toàn);
C1a còn bị đọc nhầm ngày viết liền «20261017» thành một PMID. Nay: `rut_bai.pmid_da_kiem` (bắt buộc) +
`rut_bai.doi_da_kiem` (tuỳ chọn) là nguồn DUY NHẤT từ G0; câu văn chỉ để người đọc. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_tong_hop as GT  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402

from tests.test_g0_tong_hop_bien_ban_20261010 import PMIDS, _tong_hop_hop_le  # noqa: E402
from tests.test_tong_quan_trich_dan_20261115 import DC, R1, R2, R3, S, _de_cuong, _ghi  # noqa: E402

CAU_CHUA_KIEM = "PMID 11111111: CHƯA kiểm được (mạng lỗi) — không kết luận về rút bài"


def _rb(**them) -> dict:
    return dict({"ngay": "2026-11-14", "cong_cu": "check_citation_retraction.py", "ket_qua": CAU_CHUA_KIEM}, **them)


def _ho_so(d: Path, rb: dict, tltk: list | None = None) -> None:
    """Đề cương có TLTK; KHÔNG biên nhận A12, KHÔNG báo cáo A12 ⇒ nguồn «đã kiểm» duy nhất là tổng hợp G0."""
    _ghi(d, DC, _de_cuong("Mở đầu [1]. Tiếp [2, 3].", tltk or [R1, R2, R3]))
    _ghi(d, f"G0_TONG_HOP_BANG_CHUNG_{S}.json", {"rut_bai": rb})


def _truc(d: Path, monkeypatch) -> dict:
    monkeypatch.setattr(NQ, "_hom_nay", lambda: date(2026, 11, 15))
    return NQ._truc_trich_dan(d, S, {})


# ── ① bộ đọc danh sách ─────────────────────────────────────────────────────────────────────────────────────────────
def test_ma_da_kiem_chi_doc_danh_sach_khong_doc_cau_van():
    rb = _rb(pmid_da_kiem=["22222222", " 33333333 ", "abc", 44444444], doi_da_kiem=["10.1000/Hai", "khong-phai-doi"])
    assert GT.ma_da_kiem_rut_bai(rb) == (["22222222", "33333333"], ["10.1000/Hai"])
    assert GT.ma_da_kiem_rut_bai(_rb()) == ([], [])  # câu văn nêu 11111111 nhưng không có danh sách ⇒ không mã nào
    assert GT.ma_da_kiem_rut_bai("PMID 11111111 OK") == ([], [])


# ── ② bộ kiểm G0-T3 ────────────────────────────────────────────────────────────────────────────────────────────────
def test_kiem_tong_hop_doi_pmid_da_kiem_la_danh_sach():
    d = _tong_hop_hop_le()
    assert GT.kiem_tong_hop(d, PMIDS) == []
    d["rut_bai"]["pmid_da_kiem"] = []  # rỗng hợp lệ: chưa kiểm mã nào thì nói thật
    assert GT.kiem_tong_hop(d, PMIDS) == []
    del d["rut_bai"]["pmid_da_kiem"]
    assert any("rut_bai.pmid_da_kiem" in x and "DANH SÁCH" in x for x in GT.kiem_tong_hop(d, PMIDS))
    d["rut_bai"]["pmid_da_kiem"] = "34445940, 36439278"
    assert any("rut_bai.pmid_da_kiem" in x for x in GT.kiem_tong_hop(d, PMIDS))


def test_kiem_tong_hop_bat_ma_sai_dang_va_trung():
    d = _tong_hop_hop_le()
    d["rut_bai"]["pmid_da_kiem"] = ["34445940", "PMID 1", "34445940"]
    loi = GT.kiem_tong_hop(d, PMIDS)
    assert any("sai dạng" in x and "PMID 1" in x for x in loi)
    assert any("trùng mã: 34445940" in x for x in loi)


def test_kiem_tong_hop_doi_da_kiem_tuy_chon_nhung_phai_dung_dang():
    d = _tong_hop_hop_le()
    d["rut_bai"]["doi_da_kiem"] = ["10.52163/yhc.v67i2.4385"]
    assert GT.kiem_tong_hop(d, PMIDS) == []
    d["rut_bai"]["doi_da_kiem"] = ["yhc.v67i2.4385"]
    assert any("rut_bai.doi_da_kiem" in x and "sai dạng" in x for x in GT.kiem_tong_hop(d, PMIDS))
    d["rut_bai"]["doi_da_kiem"] = "10.52163/yhc.v67i2.4385"
    assert any("rut_bai.doi_da_kiem" in x and "DANH SÁCH" in x for x in GT.kiem_tong_hop(d, PMIDS))


# ── ③ bộ đối chiếu xuyên cổng: đúng ca báo xanh giả ───────────────────────────────────────────────────────────────
def test_cau_chua_kiem_khong_thanh_da_kiem(tmp_path, monkeypatch):
    _ho_so(tmp_path, _rb(pmid_da_kiem=[]))
    k = _truc(tmp_path, monkeypatch)
    assert "chưa có bản ghi kiểm rút bài" in k["ghi_chu"] and "(số [1, 2])" in k["ghi_chu"]


def test_danh_sach_co_cau_truc_duoc_tinh_la_da_kiem(tmp_path, monkeypatch):
    # DOI viết hoa vẫn khớp mục TLTK chữ thường (cùng chuẩn hoá khoá với danh mục trích dẫn)
    _ho_so(tmp_path, _rb(pmid_da_kiem=["11111111"], doi_da_kiem=["10.1000/HAI"]))
    assert "chưa có bản ghi kiểm rút bài" not in _truc(tmp_path, monkeypatch)["ghi_chu"]
    _ho_so(tmp_path, _rb(pmid_da_kiem=["11111111"]))
    assert "(số [2])" in _truc(tmp_path, monkeypatch)["ghi_chu"]  # thiếu DOI trong danh sách ⇒ mục 2 vẫn bị báo


def test_ngay_viet_lien_khong_bi_doc_thanh_pmid(tmp_path, monkeypatch):
    # C1a: khoá «ngay_bo_sung_20261017» từng làm bộ đọc cũ coi 20261017 là PMID đã kiểm
    tltk = ["Tác giả C. Bài ba. 2010. PMID: 20261017."]
    _ho_so(tmp_path, {"ngay": "2026-10-17", "cong_cu": "x", "ket_qua": "OK", "pmid_da_kiem": [],
                      "ngay_bo_sung_20261017": "PMID 20261017 OK"}, tltk)
    _ghi(tmp_path, DC, _de_cuong("Mở đầu [1].", tltk))
    assert "(số [1])" in _truc(tmp_path, monkeypatch)["ghi_chu"]
