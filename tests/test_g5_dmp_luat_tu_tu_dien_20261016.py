"""F10 (diễn tập C1a 16/10/2026): PHẦN 3 DMP (luật kiểm tra) dựng từ CHÍNH từ điển của đề tài.

Bản cũ in nguyên bảng VALIDATION_RULES tĩnh (suy tim: lvef, NT-proBNP, «qol_score_baseline … [CẦN CHỈ ĐỊNH THANG ĐO]»)
cho MỌI đề tài ⇒ DMP mô tả luật cho biến không tồn tại và G5-AUTO-03 báo REVIEW.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

import run_g5_auto as RG5  # noqa: E402

# (biến, form, mục, loại trường, nhãn, lựa chọn, ghi chú, xác thực, min, max, bắt buộc, điều kiện hiện)
_ROWS = [
    ("record_id", "f", "", "text", "Mã phiếu", "", "", "", "", "", "y", ""),
    ("g1", "f", "", "radio", "Hài lòng chung", "1, Rất không | 2, Không | 3, BT | 4, Có | 5, Rất", "", "", "", "",
     "y", ""),
    ("lydo", "f", "", "checkbox", "Lý do chọn", "1, Gần | 2, Giỏi | 3, Khác", "", "", "", "", "", ""),
    ("lydo_khac", "f", "", "text", "Lý do khác | ghi rõ", "", "", "", "", "", "y", "[lydo(3)] = '1'"),
    ("tuoi", "f", "", "text", "Tuổi", "", "", "integer", "18", "120", "y", ""),
    ("ngay_kham", "f", "", "text", "Ngày khám", "", "", "date_ymd", "2026-01-01", "", "y", ""),
    ("gop_y", "f", "", "notes", "Góp ý tự do", "", "", "", "", "", "", ""),
    ("diem_tb", "f", "", "calc", "Điểm trung bình", "mean([g1])", "", "", "", "", "", ""),
]


def test_luat_dung_rang_buoc_cua_tu_dien():
    luat, tu_do = RG5.bang_luat_kiem_tra(_ROWS)
    theo = {r[0]: r for r in luat}
    assert set(theo) == {"record_id", "g1", "lydo", "lydo_khac", "tuoi", "ngay_kham"}
    assert theo["g1"][2] == "mã 1, 2, 3, 4, 5" and "query nếu trống" in theo["g1"][4]
    assert theo["lydo"][2] == "0/1 mỗi cột `lydo___<mã>` (mã 1, 2, 3)"
    assert theo["tuoi"][2] == "18–120" and "ngoài phạm vi" in theo["tuoi"][4]
    assert theo["ngay_kham"][2].startswith("YYYY-MM-DD (2026-01-01")
    assert "bắt buộc (khi được hiện)" in theo["lydo_khac"][3] and "chỉ hiện khi [lydo(3)] = '1'" in theo["lydo_khac"][3]
    assert "|" not in theo["lydo_khac"][3], "ký tự | trong nhãn phá bảng Markdown"
    assert tu_do == 1, "văn bản tự do không ràng buộc chỉ được đếm (gop_y); trường tính (calc) bỏ qua"


def test_bien_trung_bang_tinh_mang_ghi_chu_lam_sang():
    luat, _ = RG5.bang_luat_kiem_tra([("record_id", "f", "", "text", "Mã", "", "", "", "", "", "y", "")])
    assert "trùng ID" in luat[0][4]


def test_dmp_khong_con_dong_khuon_la():
    dmp = RG5.generate_artifact(study="PYTEST-F10", topic="Hài lòng", design_code="cross_sectional", n_adjusted=100,
                                n_total=100, n_per_group=0, run_date="2026-10-16", rows=_ROWS, specialty="generic")
    phan3 = dmp.split("## PHẦN 3", 1)[1].split("## PHẦN 4", 1)[0]
    for la in ("qol_score_baseline", "lvef", "nt_probnp", "CẦN CHỈ ĐỊNH THANG ĐO"):
        assert la not in phan3, f"dòng khuôn lạ «{la}» vẫn nằm trong luật kiểm tra"
    assert "| `g1` | radio | mã 1, 2, 3, 4, 5 |" in phan3
    assert "1 biến văn bản tự do" in phan3


def test_dong_khuon_cu_11_truong_khong_vo():
    luat, _ = RG5.bang_luat_kiem_tra([("age", "d", "", "number", "Tuổi", "", "", "", "18", "99", "y")])
    assert luat[0][2] == "18–99"
