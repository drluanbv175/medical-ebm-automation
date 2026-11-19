"""Hồi quy 19/11/2026 — cầu nối SPSS miễn chặn theo TÊN cột cho trường PHÂN LOẠI CÓ MÃ (đúng luật cổng tiếp nhận).

Kiểm toàn diện 19/11/2026, kịch bản RCT chân thực: từ điển G5 có tiêu chí chọn «tc_dien_thoai» (yesno — «Có điện thoại
di động nhận được tin nhắn»). Cổng tiếp nhận/làm sạch/khoá đã miễn trường phân loại có mã khỏi phép chặn theo tên cột
từ 17/11 (`import_real_dataset.cot_phan_loai_tu_variables`), nhưng `cau_noi_spss.ke_hoach_bien` vẫn chặn ⇒ `xuat-sav`
mã 3 ⇒ nửa SPSS của kiểm chéo G6 «TU_CHOI» cho MỌI phân tích (R khớp 8/8) và bác sĩ không xuất được .sav của dữ
liệu đã khoá.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import cau_noi_spss as C  # noqa: E402


def _ke(tmp_path, td, dong="record_id,tc_dien_thoai\n1,1\n2,0\n"):
    p = tmp_path / "d.csv"
    p.write_text(dong, encoding="utf-8", newline="\n")
    tieu_de, tk, _ = C.quet_csv(p)
    return C.ke_hoach_bien(tieu_de, tk, td, [])


@pytest.mark.parametrize("td_truong", [
    {"loai": "yesno", "nhan": "Có điện thoại di động nhận được tin nhắn"},
    {"loai": "radio", "nhan": "Loại điện thoại", "lua_chon": "1, Di động | 0, Không có"},
])
def test_truong_phan_loai_ten_giong_dinh_danh_xuat_duoc(tmp_path, td_truong):
    ke, _cb, _dx = _ke(tmp_path, {"record_id": {"loai": "text", "nhan": "Mã"}, "tc_dien_thoai": td_truong})
    b = {x["cot"]: x for x in ke}
    assert b["tc_dien_thoai"]["phan_loai_co_ma"] and b["tc_dien_thoai"]["nhan_gia_tri"]


def test_truong_van_ban_ten_dien_thoai_van_bi_chan(tmp_path):
    with pytest.raises(C.TuChoi, match="so_dien_thoai"):
        _ke(tmp_path, {"record_id": {"loai": "text", "nhan": "Mã"}, "so_dien_thoai": {"loai": "text", "nhan": "SĐT"}},
            dong="record_id,so_dien_thoai\n1,0901234567\n")


def test_cot_khong_co_trong_tu_dien_van_bi_chan(tmp_path):
    with pytest.raises(C.TuChoi, match="tc_dien_thoai"):
        _ke(tmp_path, {"record_id": {"loai": "text", "nhan": "Mã"}})
