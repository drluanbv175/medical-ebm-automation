"""K11 chiều ngược — tên chuẩn báo cáo viết tắt dùng trong văn bản mà danh mục thiếu (21/11/2026).

Phản biện máy + thẩm tra (Opus) trên đề cương nộp C1a: danh mục có STROBE, COSMIN, CROSS, RECORD nhưng vắng AGReMA dùng
ở §4.8; K11 cũ chỉ kiểm một chiều (mục không dùng, trùng nghĩa, thứ tự). Bộ sinh đề cương mắc cùng lỗi (trích STROBE,
CONSORT, PRISMA… ở mục thiết kế mà `_VIET_TAT` không có) — test bộ sinh mọi thiết kế ở test_dinh_dang_so_viet_20261120
nay chạy qua luật mới. Ngoại tuyến.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402


def _md(vt_them: str = "", than: str = "", tltk: str = "") -> str:
    return (
        "# ĐỀ CƯƠNG\n"
        "## DANH MỤC CHỮ VIẾT TẮT\n\n"
        "| Chữ viết tắt | Nghĩa đầy đủ |\n|---|---|\n"
        "| OSF | Open Science Framework |\n"
        f"{vt_them}"
        "| STROBE | Hướng dẫn báo cáo nghiên cứu quan sát |\n\n"
        "# 4. PHƯƠNG PHÁP\n\n"
        "Báo cáo theo STROBE. Đăng ký trên OSF. Nhập liệu bằng REDCap, trích từ eHospital.\n"
        f"{than}"
        "# 7. TÀI LIỆU THAM KHẢO\n\n"
        f"1. Tac A. STROBE statement. J. 2007.\n{tltk}"
    )


def _thieu(md: str) -> list:
    return [x for x in K.loi_k11(md) if "danh mục thiếu" in x]


def test_ten_chuan_dung_ma_danh_muc_thieu_bi_bat_kem_dong():
    md = _md(than="Phân tích trung gian báo cáo theo AGReMA [5].\n")
    (loi,) = _thieu(md)
    so = md.splitlines().index("Phân tích trung gian báo cáo theo AGReMA [5].") + 1
    assert "«AGReMA»" in loi and f"dòng {so}" in loi


def test_co_trong_danh_muc_thi_dat():
    md = _md(vt_them="| AGReMA | Hướng dẫn báo cáo phân tích trung gian |\n",
             than="Phân tích trung gian báo cáo theo AGReMA [5].\n")
    assert not _thieu(md)


def test_chi_xuat_hien_trong_tltk_hoac_ma_thi_khong_tinh():
    assert not _thieu(_md(tltk="2. Lee H. A guideline for reporting mediation analyses: AGReMA. JAMA. 2021.\n"))
    assert not _thieu(_md(than="Nhãn `CONSORT` chỉ là mã trong hệ thống.\n"))


def test_ten_phan_mem_va_ma_bien_khong_bi_bat():
    assert not _thieu(_md(than="Câu G1, C6 và C9; phần mềm EpiData, REDCap.\n"))


def test_khong_co_danh_muc_thi_khong_xet():
    md = "# 4. PHƯƠNG PHÁP\n\nBáo cáo theo CONSORT.\n"
    assert not _thieu(md)


def test_prisma_p_khong_tinh_la_prisma():
    loi = _thieu(_md(than="Đề cương tổng quan theo PRISMA-P 2015.\n"))
    assert [x.split("«")[1].split("»")[0] for x in loi] == ["PRISMA-P"]
