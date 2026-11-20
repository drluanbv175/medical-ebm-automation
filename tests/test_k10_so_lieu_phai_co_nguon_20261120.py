"""K10 — số liệu trong đặt vấn đề / tổng quan / bàn luận phải tự mang trích dẫn (bác sĩ 20/11/2026: «Không có số
liệu thực, chứng cứ thực hãy loại bỏ trong hệ thống nghiên cứu y khoa»).

Ca gốc: đề cương BTM «Trong nước: các nghiên cứu tìm được đo tỷ lệ … (15,32% đến 31,1%) …; chỉ một nghiên cứu … [11].»
— hai con số của các nghiên cứu KHÔNG có trong danh mục, câu chỉ mang [11] ở mệnh đề sau «;».
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402


def _md(than: str, muc: str = "# 3. TỔNG QUAN TÀI LIỆU\n\n## 3.2. Các bằng chứng hiện có\n\n") -> str:
    return ("# 1. ĐẶT VẤN ĐỀ\n\nMở đầu [1].\n\n" + muc + than
            + "\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP\n\nN = 385; 95% số ca.\n")


def test_ca_goc_btm_so_o_menh_de_khong_nguon_bi_bat():
    loi = K.loi_k10(_md("Trong nước: các nghiên cứu tìm được đo tỷ lệ bệnh thận mạn (15,32% đến 31,1%) hoặc mô tả kê "
                        "đơn; chỉ một nghiên cứu đo tỷ lệ làm UACR [11]."))
    assert len(loi) == 1 and loi[0].startswith("K10 dòng") and "15,32%" in loi[0]


def test_so_cung_menh_de_voi_trich_dan_dat():
    assert K.loi_k10(_md("Chỉ 24,9% được làm cả creatinin lẫn UACR [5]; "
                         "UACR 43,3% trong khi creatinin 84,8% [6].")) == []


def test_cham_phay_trong_ngoac_khong_tach_menh_de():
    assert K.loi_k10(_md("Học vấn cao hơn (aOR 0,53; KTC 95%: 0,28–0,98) đi kèm hài lòng thấp hơn [26].")) == []


def test_trung_binh_do_lech_chuan_khong_nguon_bi_bat():
    assert len(K.loi_k10(_md("Điểm hài lòng chung là 3,54 ± 0,54 trên thang 5 mức; "
                             "thời gian chờ chấp nhận được [9]."))) == 1


def test_muc_con_ke_thua_phan_tong_quan_va_ngoai_phan_khong_xet():
    # mục con 3.2 thuộc «TỔNG QUAN» ⇒ xét; chương phương pháp ⇒ không xét («95% số ca» không bị báo)
    assert len(K.loi_k10(_md("Tỷ lệ 30% ở người cao tuổi."))) == 1
    assert K.loi_k10("# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP\n\nTỷ lệ dự kiến 30%.\n") == []


def test_dong_bang_khong_xet():
    assert K.loi_k10(_md("| Nghiên cứu | Tỷ lệ |\n|---|---|\n| A | 30% |")) == []


def test_kiem_goi_k10(tmp_path):
    s = "x"
    (tmp_path / f"DE_CUONG_NOP_HOI_DONG_{s}.md").write_text(_md("Tỷ lệ 30% ở người cao tuổi."), encoding="utf-8",
                                                           newline="\n")
    assert any(x.startswith("K10") for x in K.kiem(tmp_path, s))
