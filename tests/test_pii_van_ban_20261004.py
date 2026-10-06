# -*- coding: utf-8 -*-
"""Bộ dò PII dùng chung `tools/pii_van_ban.py` (CHUNG-G, soát từng cổng 04/10/2026). Ngoại tuyến; số liệu là GIẢ."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import pii_van_ban as PII  # noqa: E402


def _loai(vb, **kw):
    return {p.loai for p in PII.quet_pii_van_ban(vb, **kw)}


@pytest.mark.parametrize("vb,loai", [
    ("BN sinh 03/11/1958 tại Hà Nội", "ngày tháng cụ thể"),
    ("liên hệ 0912345678", "số điện thoại"),
    ("liên hệ (090) 123 4567", "số điện thoại"),
    ("CC 012345678901", "số căn cước"),  # bimat-mien: số giả trong test
    ("CC 012 345 678 901", "số căn cước (nhóm)"),  # bimat-mien: số giả trong test
    ("gửi a.b@example.org", "email"),
    ("thẻ DN4791234567890", "số thẻ BHYT"),  # bimat-mien: số giả trong test
])
def test_che_do_chat_bat_hinh_dang(vb, loai):
    assert loai in _loai(vb), (vb, _loai(vb))


def test_che_do_chat_bat_nhan_va_duyet_dict_list():
    assert any(x.startswith("nhãn định danh") for x in _loai({"population": {"ghi_chu": "Họ tên bệnh nhân: ..."}}))
    assert "số điện thoại" in _loai(["không", {"a": ["0912345678"]}])


@pytest.mark.parametrize("vb", ["PMID: 30267080", "NCT05123456", "doi:10.1056/NEJMoa2034577",
                                "Người lớn ≥ 18 tuổi suy tim EF < 40%", "Cỡ mẫu N = 1000",
                                "Kinh phí 150000000 đồng", "ISBN 978604123456"])
def test_che_do_chat_khong_bat_so_hoc_thuat(vb):
    assert PII.quet_pii_van_ban(vb) == [], (vb, PII.quet_pii_van_ban(vb))


def test_che_do_ho_so_cho_qua_ngay_va_lien_he_nghien_cuu_vien():
    vb = ("Phiên bản 1.2 ngày 04/10/2026. Nghiên cứu viên chính: BS. A, điện thoại 0912345678, email pi@bv.vn. "
          "Hội đồng Đạo đức: 024-3825-1234.")
    assert PII.quet_pii_van_ban(vb, che_do=PII.HO_SO) == []


@pytest.mark.parametrize("vb,loai", [
    ("Ngày sinh: 03/11/1958", "ngày sinh cụ thể"),
    ("Họ tên bệnh nhân: Nguyễn Văn An", "tên người bệnh"),
    ("Số CCCD 012345678901 của người tham gia", "số căn cước"),  # bimat-mien: số giả trong test
    ("thẻ DN4791234567890", "số thẻ BHYT"),  # bimat-mien: số giả trong test
])
def test_che_do_ho_so_bat_dinh_danh_nguoi_benh(vb, loai):
    assert loai in _loai(vb, che_do=PII.HO_SO)


def test_mien_so_irb_that():
    vb = "Số phê duyệt của Hội đồng: 123456789012"  # bimat-mien: số giả trong test
    assert "số căn cước" in _loai(vb, che_do=PII.HO_SO)
    assert PII.quet_pii_van_ban(vb, che_do=PII.HO_SO, mien=["123456789012"]) == []


def test_mau_che_khong_in_lai_pii_day_du():
    p = PII.quet_pii_van_ban("liên hệ 0912345678")
    assert p and all("0912345678" not in x.mau_che for x in p)
    assert "0912345678" not in PII.tom_tat(p)
    assert PII.tom_tat([]) == "không thấy mẫu PII"


def test_che_do_la_bi_tu_choi():
    with pytest.raises(ValueError):
        PII.quet_pii_van_ban("x", che_do="khac")
