"""BTS: tự tìm URL guideline chính theo chủ đề + năm suy từ nội dung PDF — 26/09/2026.

Ngoại tuyến. HTML giả chỉ mô phỏng CẤU TRÚC link đo thật 26/09 trên brit-thoracic.org.uk
(bản chính + phụ lục/tóm tắt/slide; tài liệu đồng xuất bản NICE), không chứa nội dung y khoa.
"""
from __future__ import annotations

import argparse

import pytest

from app.config import settings
from app.sources import bts_guidelines as B
from tools import toan_van_guideline as T

G = "/document-library/guidelines/"


def _html(*duong: str) -> str:
    return "".join(f'<a href="{d}">x</a>' for d in duong)


def test_chon_ban_chinh_bo_qua_phu_luc_tom_tat_slide():
    html = _html(G + "pleural-disease/bts-guideline-for-pleural-disease/",
                 G + "pleural-disease/bts-guideline-for-pleural-disease-summary-of-guideline/",
                 G + "pleural-disease/online-appendix-1-pleural-disease-literature-search-strategies/",
                 G + "pleural-disease/pleural-disease-full-supplement/",
                 G + "ntm/bts-ntm-guideline-slide-set/")
    kq = B.chon_url_guideline_chinh(html)
    assert kq["url"] == B._GOC_BTS + G + "pleural-disease/bts-guideline-for-pleural-disease/"


def test_hai_ung_vien_thi_khong_doan():
    html = _html(G + "long-term-macrolide-use/british-thoracic-society-guideline-for-the-use-of-long-term-macrolides/",
                 G + "long-term-macrolide-use/bts-guideline-for-long-term-macrolide-use/")
    kq = B.chon_url_guideline_chinh(html)
    assert kq["url"] is None and len(kq["ung_vien"]) == 2 and "không đoán" in kq["ly_do"]


@pytest.mark.parametrize("ten", ["btsnicesign-joint-guideline-on-asthma-diagnosis",
                                 "nice-guideline-on-tobacco-preventing-uptake"])
def test_chi_co_tai_lieu_nice_thi_tu_choi(ten):
    kq = B.chon_url_guideline_chinh(_html(G + f"asthma/{ten}/"))
    assert kq["url"] is None and kq["loai_nice"] and "NICE" in kq["ly_do"]


def test_trang_khong_co_tai_lieu():
    kq = B.chon_url_guideline_chinh("<html>không có link</html>")
    assert kq["url"] is None and not kq["ung_vien"] and not kq["loai_nice"]


def test_chu_de_sai_khuon_khong_goi_mang(monkeypatch):
    monkeypatch.setattr(settings, "enable_bts_guidelines_fulltext", True)
    c = B.BtsGuidelineFullTextClient()

    def cam_goi(*a, **k):
        raise AssertionError("không được gọi mạng khi chủ đề sai khuôn")

    monkeypatch.setattr(c.http, "get_text", cam_goi)
    for xau in ("../etc", "Pleural Disease", "a_b", ""):
        assert c.tim_url_theo_chu_de(xau)["url"] is None


def test_loi_mang_khi_doc_trang_chu_de_la_khong_co_url(monkeypatch):
    monkeypatch.setattr(settings, "enable_bts_guidelines_fulltext", True)
    c = B.BtsGuidelineFullTextClient()
    monkeypatch.setattr(c.http, "get_text", lambda *a, **k: (_ for _ in ()).throw(OSError("mất mạng")))
    kq = c.tim_url_theo_chu_de("pleural-disease")
    assert kq["url"] is None and "không đọc được" in kq["ly_do"]


@pytest.mark.parametrize("van_ban,nam", [
    ("xx THORAX August 2015 Volume 70", "2015"),
    ("Contents Volume 74 Supplement 1 | THORAX January 2019 1 Summary", "2019"),
    ("Thorax 2023;78:s1", "2023"),
    ("References 12. Smith J. Chest 2011;140:1.", None),     # năm của tài liệu tham khảo không được nhận
    ("", None),
])
def test_nam_tu_van_ban_chi_nhan_dong_tieu_de_tap_chi(van_ban, nam):
    assert T.nam_tu_van_ban(van_ban) == nam


def _args(**kw):
    mac_dinh = dict(nguon="bts", dinh_danh=None, url=None, chu_de="x", luu=None, gioi_han=None,
                    toan_bo=False, tim=[], ngu_canh=300, toi_da_khop=10, doi=None, pmid=None)
    mac_dinh.update(kw)
    return argparse.Namespace(**mac_dinh)


class _ClientGia:
    def __init__(self, kq):
        self.kq = kq

    def tim_url_theo_chu_de(self, chu_de):
        return dict(self.kq, trang_chu_de="t")


@pytest.mark.parametrize("kq,trang_thai,ma", [
    ({"url": None, "ly_do": "2 ứng viên", "ung_vien": ["a", "b"], "loai_nice": []}, "can_chon", T.MA_TU_CHOI),
    ({"url": None, "ly_do": "chỉ NICE", "ung_vien": [], "loai_nice": ["n"]}, "tu_choi", T.MA_TU_CHOI),
    ({"url": None, "ly_do": "trống", "ung_vien": [], "loai_nice": []}, "loi", T.MA_LOI),
])
def test_cli_chu_de_khong_tai_khi_khong_chac(monkeypatch, kq, trang_thai, ma):
    monkeypatch.setattr(T, "_dung_client", lambda nguon: _ClientGia(kq))
    monkeypatch.setattr(T, "tai", lambda *a, **k: (_ for _ in ()).throw(AssertionError("không được tải")))
    out = T.xu_ly_tai(_args())
    assert out["trang_thai"] == trang_thai and out["ma_thoat"] == ma


def test_cli_bts_thieu_ca_url_lan_chu_de_bi_tu_choi():
    out = T.xu_ly_tai(_args(chu_de=None))
    assert out["trang_thai"] == "tu_choi" and out["ma_thoat"] == T.MA_TU_CHOI
