"""Crossref: rút MỘT PHẦN và tiền tố tiêu đề RETRACTED/WITHDRAWN không bao giờ được ra «ok».

Vá 26/09/2026 (phát hiện #12). Trước đó `CrossrefRetraction.check()` chỉ nhận các nhãn `updated-by`
đã liệt kê; `partial_retraction`, một nhãn rút lạ, hay một bản ghi mà nhà xuất bản chỉ đánh dấu bằng
tiền tố tiêu đề «RETRACTED:»/«WITHDRAWN:» đều rơi xuống nhánh mặc định `ok`. Với DOI không có PMID,
Crossref là nguồn DUY NHẤT, nên đó là tín hiệu DƯƠNG bị đảo thành ÂM (trái luật gộp bất đối xứng).

Ngoại tuyến hoàn toàn: `_lay` được thay bằng từ điển bản ghi dựng tay, không gọi mạng.
"""
from __future__ import annotations

import pytest

from app.sources import crossref_retraction as cr
from app.sources.crossref_retraction import CrossrefRetraction


class _Crossref(CrossrefRetraction):
    """Crossref giả: trả bản ghi dựng sẵn theo DOI, DOI lạ ⇒ KeyError (không bao giờ gọi mạng)."""

    def __init__(self, ban_ghi: dict) -> None:
        super().__init__()
        self._bg = ban_ghi

    def _lay(self, doi):
        return self._bg[doi]


def _kiem(ban_ghi_bai: dict, thong_bao: dict | None = None) -> dict:
    kho = {"10.x/bai": ban_ghi_bai}
    kho.update(thong_bao or {})
    return _Crossref(kho).check(["10.x/bai"])["10.x/bai"]


# ---------------------------------------------------------------- ba ca đã đo (đều phải DƯƠNG TÍNH)

def test_partial_retraction_la_rut_bai():
    kq = _kiem({"title": ["Bai A"], "updated-by": [{"type": "partial_retraction", "DOI": "10.x/n1"}]},
               {"10.x/n1": {"title": ["Partial retraction notice: Bai A"]}})
    assert kq["status"] == "retracted"
    assert kq["notice_doi"] == "10.x/n1"


def test_partial_retraction_dang_gach_noi_cung_khop():
    kq = _kiem({"title": ["Bai A"], "updated-by": [{"type": "partial-retraction", "DOI": "10.x/n1"}]},
               {"10.x/n1": {"title": ["x"]}})
    assert kq["status"] == "retracted"


@pytest.mark.parametrize("nhan", ["retraction_note", "Partial Retraction", "withdrawal_notice",
                                  "retracted_and_republished"])
def test_nhan_rut_la_chua_tung_thay_van_la_rut(nhan):
    """Nhãn lạ chứa «retract»/«withdraw» nghiêng về DƯƠNG TÍNH, không rơi xuống «ok»."""
    kq = _kiem({"title": ["Bai A"], "updated-by": [{"type": nhan, "DOI": "10.x/n1"}]},
               {"10.x/n1": {"title": ["x"]}})
    assert kq["status"] == "retracted", nhan


@pytest.mark.parametrize("tieu_de", [
    "RETRACTED: Ileal-lymphoid-nodular hyperplasia, non-specific colitis",
    "WITHDRAWN: Something about a Cochrane review",
    "[Retracted] Efficacy of drug X",
    "Withdrawn — A trial of Y",
    "  retracted - an old paper",
])
def test_tieu_de_mang_tien_to_rut_la_rut_bai(tieu_de):
    kq = _kiem({"title": [tieu_de], "updated-by": []})
    assert kq["status"] == "retracted", tieu_de
    assert kq["source"] == "crossref"
    assert kq["title_marker"] is True
    # Không có DOI thông báo ⇒ không có dấu vân tay ⇒ KHÔNG được mở đường miễn trừ của sổ do bác sĩ ký.
    assert kq["withdrawn_correction_notice"] is False
    assert kq["notice_dois"] == []
    assert kq["notice_doi"] == ""
    assert kq["retract_and_replace"] is False
    assert kq["title"] == tieu_de


def test_tieu_de_khong_co_khoa_updated_by_cung_la_rut():
    kq = _kiem({"title": ["WITHDRAWN: Something"]})
    assert kq["status"] == "retracted"


def test_tieu_de_dang_chuoi_tran_van_duoc_doc():
    kq = _kiem({"title": "RETRACTED: string title"})
    assert kq["status"] == "retracted"


def test_tieu_de_rut_thang_quan_ngai():
    """Có EoC mà tiêu đề đã nói «RETRACTED» ⇒ nặng hơn thắng: retracted, không hạ xuống EoC."""
    kq = _kiem({"title": ["RETRACTED: Bai B"],
                "updated-by": [{"type": "expression_of_concern", "DOI": "10.x/eoc"}]})
    assert kq["status"] == "retracted"
    assert kq["title_marker"] is True


def test_updated_by_rut_van_di_nhanh_cu_co_thong_bao():
    """Có quan hệ updated-by rút bài ⇒ giữ nhánh cũ (có DOI thông báo, không gắn title_marker)."""
    kq = _kiem({"title": ["RETRACTED: Bai C"], "updated-by": [{"type": "retraction", "DOI": "10.x/n9"}]},
               {"10.x/n9": {"title": ["Retraction notice"]}})
    assert kq["status"] == "retracted"
    assert kq["notice_doi"] == "10.x/n9"
    assert "title_marker" not in kq


# ---------------------------------------------------------------- ca âm (vẫn phải «ok»)

@pytest.mark.parametrize("ban_ghi", [
    {"title": ["Bai D"], "updated-by": [{"type": "correction", "DOI": "10.x/c1"}]},
    {"title": ["Bai D"], "updated-by": [{"type": "erratum", "DOI": "10.x/c1"}]},
    {"title": ["Bai D"], "updated-by": [{"type": "corrigendum", "DOI": "10.x/c1"}]},
    {"title": ["Retraction of a mesh implant in pelvic surgery"]},
    {"title": ["Correction to: Outcomes of therapy"]},
    {"title": ["Withdrawal symptoms of long-term benzodiazepine use"]},
    {"title": ["Retracted tongue as a sign"]},
    {"title": ["Bai sach"], "updated-by": []},
    {"title": []},
])
def test_ca_am_van_la_ok(ban_ghi):
    kq = _kiem(ban_ghi)
    assert kq["status"] == "ok", ban_ghi


def test_quan_ngai_khong_bi_nang_thanh_rut():
    kq = _kiem({"title": ["Bai E"], "updated-by": [{"type": "expression_of_concern", "DOI": "10.x/e"}]})
    assert kq["status"] == "expression_of_concern"


# ---------------------------------------------------------------- một định nghĩa regex, đúng tầng

def test_fallback_verification_dung_chung_regex_tang_sources():
    from app.services import fallback_verification as fv

    assert fv._TIEU_DE_BAI_BI_RUT_RE is cr.TIEU_DE_BAI_BI_RUT_RE
    assert fv._la_tieu_de_bai_bi_rut("RETRACTED: X")
    assert fv._bo_tien_to_bi_rut("WITHDRAWN: Bai Y") == "Bai Y"


def test_tang_sources_khong_nhap_tang_services():
    """Tầng sources không được import tầng services (tránh vòng import, giữ đúng chiều phụ thuộc)."""
    from pathlib import Path

    nguon = Path(cr.__file__).read_text(encoding="utf-8")
    dong_import = [d.strip() for d in nguon.splitlines()
                   if d.strip().startswith(("import ", "from "))]
    assert not any("app.services" in d for d in dong_import), dong_import


def test_partial_retraction_nam_trong_tap_liet_ke():
    """Liệt kê TƯỜNG MINH (không chỉ trông vào luật dự phòng chuỗi con): hai lớp độc lập."""
    assert "partial_retraction" in cr.NHAN_RUT
    assert cr.la_nhan_rut("partial_retraction")
    assert not cr.la_nhan_rut("correction")
    assert not cr.la_nhan_rut("expression_of_concern")
