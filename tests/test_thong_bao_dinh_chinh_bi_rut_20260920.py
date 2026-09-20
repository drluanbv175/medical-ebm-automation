"""Thông báo rút bài là BẢN ĐÍNH CHÍNH bị rút (20/09/2026, ca TienLuongSuyTim_20260914 ITEM-11).

Máy chỉ NHẬN DIỆN CÂU CHỮ: trạng thái luôn `retracted` (cổng vẫn chặn), cờ chỉ bật khi hội đủ điều kiện
và không bao giờ bật cho một vụ rút bài thật. Hạ cờ là việc của sổ do bác sĩ ký (kiểm ở chốt BH109).
"""
from __future__ import annotations

import pytest

from app.sources.crossref_retraction import CrossrefRetraction, la_thong_bao_sua_loi_bi_rut
from app.sources.retraction_chain import RetractionChain

TB1 = {"pmid": "1", "citation": "x"}
TB2 = {"pmid": "2", "citation": "y"}


def _pm(*ds):
    return {"status": "retracted", "retraction_notice": ds[-1], "retraction_notices": list(ds)}


@pytest.mark.parametrize("tieu_de", [
    'WITHDRAWN: Corrigendum to "2025 guideline" [Can J Cardiol 2025]',
    "RETRACTED: Erratum for X",
    "WITHDRAWN: Author Correction: y",
    "  withdrawn : Addendum to foo",
])
def test_nhan_ra_tieu_de_dinh_chinh_bi_rut(tieu_de):
    assert la_thong_bao_sua_loi_bi_rut(tieu_de)


@pytest.mark.parametrize("tieu_de", [
    "WITHDRAWN: Correction of hypertension by exercise",  # bài nghiên cứu tình cờ tên «Correction of…»
    "Retraction: Fabricated data",
    "Notice of Retraction and Replacement. Choi et al.",
    "WITHDRAWN: Efficacy of drug",
    "Corrigendum to X",  # đính chính bình thường, chưa bị rút
    "",
])
def test_khong_nhan_nham(tieu_de):
    assert not la_thong_bao_sua_loi_bi_rut(tieu_de)


def test_chuoi_bat_co_va_giu_trang_thai_retracted():
    kq = RetractionChain._gop("9", None, _pm(TB1), None, ["pubmed"], {"1": "WITHDRAWN: Corrigendum to X"})
    assert kq["status"] == "retracted"
    assert kq["withdrawn_correction_notice"] is True
    assert kq["notice_ids"] == ["1"]


@pytest.mark.parametrize("ten,rw,pm,titles", [
    ("thiếu tiêu đề", None, _pm(TB1), {}),
    ("có thông báo thật bên cạnh", None, _pm(TB1, TB2),
     {"1": "WITHDRAWN: Corrigendum to X", "2": "RETRACTED: Efficacy of drug"}),
    ("chỉ biết một trong hai tiêu đề", None, _pm(TB1, TB2), {"1": "WITHDRAWN: Corrigendum to X"}),
    ("Retraction Watch dương tính riêng",
     {"status": "retracted", "reason": "Falsification", "nature": "Retraction"},
     _pm(TB1), {"1": "WITHDRAWN: Corrigendum to X"}),
])
def test_chuoi_khong_bat_co_khi_thieu_bang_chung(ten, rw, pm, titles):
    kq = RetractionChain._gop("9", rw, pm, None, ["pubmed"], titles)
    assert kq["status"] == "retracted", ten
    assert not kq.get("withdrawn_correction_notice"), ten


class _Crossref(CrossrefRetraction):
    def __init__(self, ban_ghi):
        super().__init__()
        self._bg = ban_ghi

    def _lay(self, doi):
        return self._bg[doi]


def test_crossref_chi_bat_co_khi_dung_mot_thong_bao_la_dinh_chinh():
    bai = {"title": ["G"], "updated-by": [{"type": "retraction", "DOI": "10.x/n1"}]}
    ok = _Crossref({"10.x/g": bai, "10.x/n1": {"title": ["WITHDRAWN: Corrigendum to G"]}}).check(["10.x/g"])
    assert ok["10.x/g"]["status"] == "retracted"
    assert ok["10.x/g"]["withdrawn_correction_notice"] is True
    hai = {"title": ["G"], "updated-by": [{"type": "retraction", "DOI": "10.x/n1"},
                                          {"type": "retraction", "DOI": "10.x/n2"}]}
    kq = _Crossref({"10.x/g": hai, "10.x/n1": {"title": ["WITHDRAWN: Corrigendum to G"]},
                    "10.x/n2": {"title": ["Retraction: G"]}}).check(["10.x/g"])
    assert kq["10.x/g"]["status"] == "retracted"
    assert kq["10.x/g"]["withdrawn_correction_notice"] is False
