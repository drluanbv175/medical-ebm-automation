"""Chốt: nhật ký sức khoẻ API giữ lượt gần nhất theo TỪNG công cụ (17/11/2026, bác sĩ duyệt «mục 2»).

Trước đây `~/.ebm-api-claude.json` chỉ giữ MỘT lượt: 8 công cụ (5 ở repo này, 3 ở repo gốc) ghi chung một ô nên lượt
sau xoá lượt trước — công cụ A lỗi 401 rồi công cụ B chạy ổn ngay sau thì lỗi của A biến mất trước khi hòm việc (repo
gốc, `tu_de_xuat_viec.giac_quan_api_claude`) kịp đọc. Nay khoá «theo_nguon» giữ lượt gần nhất của từng công cụ.

Ngoại tuyến tuyệt đối: chỉ ghi vào tmp_path, không đọc kho khoá, không gọi API.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def api():
    sp = importlib.util.spec_from_file_location("_api_nc_theo_nguon", ROOT / "tools" / "api_claude_nc.py")
    m = importlib.util.module_from_spec(sp)
    sys.modules["_api_nc_theo_nguon"] = m
    sp.loader.exec_module(m)
    return m


def _doc(tep: Path) -> dict:
    return json.loads(tep.read_text(encoding="utf-8"))


def test_loi_cua_cong_cu_a_khong_bi_luot_ok_cua_b_xoa(tmp_path, api):
    """★ Đúng kịch bản lỗ hổng: hội đồng Batch lỗi 401, ngay sau đó kiểm nội dung trích dẫn chạy ổn."""
    tep = tmp_path / "nk.json"
    api.ghi_nhat_ky_api("error", "AuthenticationError: 401", 0, "hoi_dong_cong_batch", tep=str(tep))
    api.ghi_nhat_ky_api("ok", "", 21, "kiem_noi_dung_trich_dan", tep=str(tep))
    d = _doc(tep)
    assert (d["trang_thai"], d["so_muc"], d["nguon"]) == ("ok", 21, "kiem_noi_dung_trich_dan")  # cấp cao = lượt mới
    assert d["theo_nguon"]["hoi_dong_cong_batch"]["trang_thai"] == "error"                       # lỗi của A CÒN
    assert set(d["theo_nguon"]["kiem_noi_dung_trich_dan"]) == {"luc", "trang_thai", "ly_do", "so_muc"}


def test_nhat_ky_kieu_cu_duoc_giu(tmp_path, api):
    tep = tmp_path / "nk.json"
    cu = {"luc": "2026-11-17T10:00:00", "trang_thai": "error", "ly_do": "429", "so_muc": 0,
          "nguon": "quet_lac_chu_de_kho"}
    tep.write_text(json.dumps(cu), encoding="utf-8", newline="\n")
    api.ghi_nhat_ky_api("ok", "", 1, "phan_bien_may_de_cuong", tep=str(tep))
    d = _doc(tep)
    assert d["theo_nguon"]["quet_lac_chu_de_kho"] == {k: cu[k] for k in ("luc", "trang_thai", "ly_do", "so_muc")}


def test_nhat_ky_hong_thi_ghi_lai_tu_dau(tmp_path, api):
    tep = tmp_path / "nk.json"
    tep.write_text("{ hỏng", encoding="utf-8", newline="\n")
    api.ghi_nhat_ky_api("ok", "", 1, "image_reading", tep=str(tep))
    assert set(_doc(tep)["theo_nguon"]) == {"image_reading"}


def test_ghi_nguyen_tu_khong_de_lai_tep_tam_va_khong_nem(tmp_path, api):
    tep = tmp_path / "nk.json"
    api.ghi_nhat_ky_api("ok", "", 1, "ambient_scribe", tep=str(tep))
    assert [p.name for p in tmp_path.iterdir()] == ["nk.json"]
    api.ghi_nhat_ky_api("ok", tep=str(tmp_path / "khong" / "co" / "nk.json"))   # thư mục vắng: không được ném


def test_duoi_pytest_van_khong_ghi_tep_that(api, monkeypatch, tmp_path):
    """Rào BH181 giữ nguyên với khuôn mới: dưới pytest, đường THẬT bị từ chối (không ghi, không đọc để trộn)."""
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    monkeypatch.setattr(api, "_NK_THAT", str(tmp_path / "that.json"))
    api.ghi_nhat_ky_api("ok", "", 1, "x", tep=str(tmp_path / "that.json"))
    assert not (tmp_path / "that.json").exists()
