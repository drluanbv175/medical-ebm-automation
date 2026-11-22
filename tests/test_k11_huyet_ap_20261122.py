"""K11 — số đo huyết áp ghi đúng định dạng (bác sĩ 22/11/2026: «180/110 mmHg là số đo huyết áp phải ghi đúng định
dạng»). Đo được trước bản vá: hồ sơ giả lập có 16 chỗ «<140/90», «≥180/110 mmHg», nhãn biến «(<140/90)» thiếu đơn vị;
bảng biến G3 của đề tài BTM ghi «từ 140/90 ở 2 lượt khám» — không chốt nào bắt."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402


@pytest.mark.parametrize("dong, loi", [
    ("Thêm huyết áp đo được từ 140/90 ở 2 lượt khám", "thiếu đơn vị mmHg"),
    ("Kiểm soát huyết áp tháng 6 (<140/90)", "thiếu đơn vị mmHg"),
    ("Ngừng khi HA ≥180/110 mmHg", "dấu so sánh cách số"),
    ("huyết áp 140 / 90 mmHg", "khoảng trắng quanh «/»"),
    ("huyết áp đích 130/80mmHg", "một khoảng trắng trước đơn vị"),
])
def test_bat_dinh_dang_huyet_ap_sai(dong, loi):
    assert loi in (K.loi_huyet_ap(dong) or "")


@pytest.mark.parametrize("dong", [
    "Cơn tăng huyết áp ≥ 180/110 mmHg phải xử trí",
    "Kiểm soát huyết áp tháng 6 (< 140/90 mmHg)",
    "Huyết áp mục tiêu 120/80 mmHg",
    "Threshold Criteria of 140/90 or 130/80 mmHg",                     # đơn vị dùng chung, tiêu đề nguyên văn
    "huyết áp 140/90 hoặc 130/80 mmHg",
    "ngày 17/11/2026, phiên bản 1.0",                                   # ngày
    "Kiểm soát huyết áp — nhóm chứng: 57/118 (48.3%)",                  # tỷ số đếm
    "Đạt kiểm soát huyết áp: 120/100 người bệnh",                      # tỷ số đếm (tử > mẫu vẫn không phải huyết áp)
    "Kiểm soát huyết áp tháng 6: 118/100 (54,1%)",
    "Không có số đo nào trong câu này",
])
def test_khong_bat_nham(dong):
    assert K.loi_huyet_ap(dong) is None


def test_loi_k11_bao_dong_huyet_ap_ngoai_tltk():
    md = ("# ĐẶT VẤN ĐỀ\n\nNgười bệnh có huyết áp từ 140/90 ở 2 lượt khám.\n\n"
          "# TÀI LIỆU THAM KHẢO\n\n1. Smith. BP <140/90 in adults. 2020.\n")
    loi = [x for x in K.loi_k11(md) if "huyết áp" in x]
    assert loi == ["K11 dòng 3: số đo huyết áp «140/90» — thiếu đơn vị mmHg (vd «≥ 180/110 mmHg»)"]


def test_ho_so_gia_lap_khong_con_so_do_huyet_ap_sai():
    """Chuỗi hồ sơ giả lập đi thẳng vào đề cương/bản thảo — mọi số đo huyết áp phải đúng định dạng."""
    sai = []
    for ten in ("gia_lap_dinh_ky.py", "gia_lap_chan_thuc.py", "gia_lap_bien_the_kho.py", "gia_lap_tron_vong.py",
                "gia_lap_ho_so_sau_g6.py", "gia_lap_kich_ban_them.py"):
        for so, d in enumerate((ROOT / "tools" / ten).read_text(encoding="utf-8").splitlines(), 1):
            if d.lstrip().startswith("#"):
                continue
            loi = K.loi_huyet_ap(d)
            if loi:
                sai.append(f"{ten}:{so}: {loi}")
    assert sai == []
