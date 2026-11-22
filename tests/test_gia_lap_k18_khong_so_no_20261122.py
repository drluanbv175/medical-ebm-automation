"""Chốt CI chuẩn báo cáo theo mục (K18) KHÔNG sổ nợ — tools/kiem_gia_lap_16.py (22/11/2026).

Bác sĩ 22/11/2026: «ghi nhỏ sổ nợ sẽ không ghi sổ nợ nữa, giải quyết theo nguyên tắc». Mọi kịch bản phải đạt đủ mục
chuẩn áp dụng ở bản thảo G7 và báo cáo tổng hợp; thiếu bất kỳ mục nào ⇒ trượt; chưa đo ⇒ trượt.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import kiem_gia_lap_16 as K  # noqa: E402


def _j(bt, bc, cau_truc=None):
    return {"chuan_bao_cao": {"ban_thao_thieu": bt, "bao_cao_thieu": bc, "bao_cao_cau_truc": cau_truc or []}}


def test_khong_thieu_muc_nao_thi_dat():
    assert K.kiem_chuan_bao_cao(_j([], [])) == []


def test_ban_thao_thieu_mot_muc_thi_truot():
    loi = K.kiem_chuan_bao_cao(_j(["CONSORT 2025 3"], []))
    assert loi and "bản thảo thiếu" in loi[0] and "CONSORT 2025 3" in loi[0]


def test_bao_cao_thieu_mot_muc_thi_truot():
    loi = K.kiem_chuan_bao_cao(_j([], ["STARD 2015 3"]))
    assert loi and "báo cáo tổng hợp thiếu" in loi[0] and "STARD 2015 3" in loi[0]


def test_chua_do_thi_truot():
    assert K.kiem_chuan_bao_cao({})
    assert K.kiem_chuan_bao_cao({"chuan_bao_cao": {"loi": "chưa có bản thảo G7"}})
    assert K.kiem_chuan_bao_cao({"chuan_bao_cao": {"ban_thao_thieu": []}})  # thiếu khoá báo cáo ⇒ chưa đo


def test_canh_bao_cau_truc_bao_cao_thi_truot():
    loi = K.kiem_chuan_bao_cao(_j([], [], ["thiếu: Kết luận"]))
    assert loi and "cấu trúc báo cáo" in loi[0]


def test_khong_con_so_no_hay_tuy_chon_ghi_so_no():
    nguon = (ROOT / "tools" / "kiem_gia_lap_16.py").read_text(encoding="utf-8")
    assert "SO_NO_K18" not in nguon and "--ghi-so-no" not in nguon and "--cho-them" not in nguon
    assert not (ROOT / "tests" / "fixtures" / "gia_lap_k18_so_no.json").exists()
