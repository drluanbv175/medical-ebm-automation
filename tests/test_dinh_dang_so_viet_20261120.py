"""Số và loại biến kiểu Việt Nam trong đề cương nộp (soát định dạng 20/11/2026).

1. Bộ sinh đề cương ghi khoảng giá trị kiểu máy («0.1–2000», «1–100000», «2026-01-01–2026-12-31») vào phiếu và bảng
   biến số ⇒ nay thập phân dấu phẩy, nhóm nghìn từ 5 chữ số, ngày dd/mm/yyyy; số 4 chữ số (năm) giữ nguyên.
2. Loại biến «Định danh/thứ bậc» bỏ lửng ⇒ nay «Định danh», «Thứ bậc» (thang Likert) hoặc «Định danh (chọn nhiều)».
3. Đối chiếu biến ↔ đề cương đọc «2.000» thành 2,0 ⇒ LỆCH giả; nay hiểu số kiểu Việt Nam.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import doi_chieu_bien_de_cuong as DC  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402


def test_so_hien_kieu_viet_nam():
    assert SDC._so_hien("0.1") == "0,1"
    assert SDC._so_hien("10000") == "10.000"
    assert SDC._so_hien("100000") == "100.000"
    assert SDC._so_hien("2000") == "2000" and SDC._so_hien("1950") == "1950"
    assert SDC._so_hien("2026-01-01") == "01/01/2026"
    assert SDC._so_hien("abc") == "abc" and SDC._so_hien("") == ""


def test_phieu_va_bang_bien_dung_so_viet():
    r = {"Field Type": "text", "Text Validation Type OR Show Slider Number": "number",
         "Text Validation Min": "0.1", "Text Validation Max": "10000"}
    assert SDC._o_tra_loi(r).endswith("(từ 0,1 đến 10.000)")


def test_loai_bien_ro_rang():
    radio = {"Field Type": "radio", "Choices, Calculations, OR Slider Labels": "1, Quân nhân | 2, Dịch vụ | 3, Khác"}
    likert = {"Field Type": "radio", "Choices, Calculations, OR Slider Labels":
              "1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường | 4, Hài lòng | 5, Rất hài lòng"}
    hop = {"Field Type": "checkbox", "Choices, Calculations, OR Slider Labels": "1, A | 2, B | 3, C"}
    assert SDC._loai_bien(radio) == "Định danh"
    assert SDC._loai_bien(likert) == "Thứ bậc"
    assert SDC._loai_bien(hop) == "Định danh (chọn nhiều)"
    assert SDC._loai_bien({"Field Type": "yesno"}) == "Nhị phân"


def test_doi_chieu_doc_so_viet_nam():
    assert DC._so_may("2.000") == "2000"
    assert DC._so_may("100.000") == "100000"
    assert DC._so_may("1.234,5") == "1234.5"
    assert DC._so_may("0,1") == "0.1" and DC._so_may("0.1") == "0.1"


# ── K11 «chuẩn trình bày tiếng Việt» áp cho MỌI đề cương (bác sĩ 20/11/2026: «hoàn thiện cho hệ thống chứ không riêng 2
# đề tài C1a và BTM») — bộ sinh phải tự ra văn bản đạt K11 với mọi thiết kế; luật bắt đúng các lỗi đã gặp. ──────────
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import pytest  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sinh_de_cuong_nop_hoi_dong_20261116 import MA, _de_tai  # noqa: E402


# «qualitative» không có ở đây: khuôn đề tài mẫu của test bộ sinh mang cỡ mẫu định lượng (K5 lệch) — ngoài phạm vi K11.
@pytest.mark.parametrize("thiet_ke", ["rct", "cross_sectional", "cohort", "case_control", "diagnostic",
                                      "prediction", "sr_ma"])
def test_bo_sinh_ra_de_cuong_dat_k11_moi_thiet_ke(tmp_path, thiet_ke):
    d = _de_tai(tmp_path, thiet_ke)
    kq = SDC.sinh(d, MA, ghi=True)
    assert kq["ma"] == 0, kq.get("loi")
    van = (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8")
    assert KDN.loi_k11(van) == []


def test_k11_bat_cac_loi_trinh_bay_da_gap():
    md = "\n".join([
        "## DANH MỤC CHỮ VIẾT TẮT", "", "| Viết tắt | Nghĩa |", "|---|---|",
        "| TB | Trung bình |", "| SD | Độ lệch chuẩn |", "| ĐLC | Độ lệch chuẩn |", "| ZZZ | Không dùng |", "",
        "# 1. ĐẶT VẤN ĐỀ", "",
        "Trung bình TB ± SD và ĐLC.", "Ngưỡng 0.1 mg.", "Khung 100000 hồ sơ.", "Ngày 2026-01-01.",
        "Câu có \"ngoặc thẳng\" ở đây.",
        "Mô hình A vs mô hình B.",
        "Dùng 1 lần đo sẽ ước lượng CAO tỷ lệ.",
        "| tuoi | Tuổi | Định danh/thứ bậc | 1–3 | Phiếu |",
        "**Bảng 5.4. Phân tích đơn biến (biến phụ thuộc) (Mục tiêu 3)**",
        "", "# 7. TÀI LIỆU THAM KHẢO", "", "1. Nguyen HA. Tên bài \"gốc\". 2020;12345678.",
    ])
    loi = "\n".join(KDN.loi_k11(md))
    for mau in ("dấu phẩy (0,1)", "nhóm nghìn", "dd/mm/yyyy", "ngoặc kép", "so với", "IN HOA", "Định danh/thứ bậc",
                "hai ngoặc", "SD, ĐLC cùng nghĩa", "«ZZZ» không xuất hiện", "chưa xếp theo"):
        assert mau in loi, mau
    assert "dòng 24" not in loi  # danh mục tài liệu tham khảo giữ nguyên văn (ngoặc thẳng, số 8 chữ số)


def test_k11_mien_phu_luc_ma_va_chuoi_tim_kiem():
    md = "\n".join([
        "# 3. TỔNG QUAN", "",
        '> ("Diabetes Mellitus, Type 2"[Mesh] OR "type 2"[tiab])',
        "Dùng mã `0.1` trong tệp.",
        "# PHỤ LỤC C. PHIẾU", "",
        "| 70 | Bệnh án ghi đang dùng nhưng KHÔNG có trong đơn | ☐ 1. Có | x |",
    ])
    assert KDN.loi_k11(md) == []


def test_k9_bang_khong_don_nhieu_muc_vao_mot_o():
    import khung_bieu_bang as KBB  # noqa: PLC0415

    md = "\n".join([
        "# 5. DỰ KIẾN KẾT QUẢ", "",
        "**Bảng 5.1. Đặc điểm chung của đối tượng nghiên cứu (Mục tiêu 1)**", "",
        "| Đặc điểm | Phân nhóm | n (%) |", "|---|---|---|", "| Giới | Nam; Nữ | … |", "",
        "*Ghi chú:* Chữ viết tắt —.", "", "![Biểu đồ 5.1](x.png)", "", "**Biểu đồ 5.1. Tỷ lệ (Mục tiêu 1)**",
    ])
    assert any("dồn một ô" in x for x in KBB.kiem_bieu_bang(md, "cross_sectional", 1))
    tot = md.replace("| Giới | Nam; Nữ | … |", "| Giới: nữ | | … |")
    assert not any("dồn một ô" in x for x in KBB.kiem_bieu_bang(tot, "cross_sectional", 1))


def test_bang_viet_tat_bo_tu_trong_tai_lieu_tham_khao_va_xep_van():
    than = "\n".join(["# 1. ĐẶT VẤN ĐỀ", "", "Người ĐTĐ có BHYT; KTC 95% và ĐN1.", "",
                      "# 7. TÀI LIỆU THAM KHẢO", "", "1. Nguyen HA, Tran SD. Bài báo. 2020.", "",
                      "# PHỤ LỤC A. KẾ HOẠCH", "", "Ước lượng OR."])
    bang = SDC.viet_tat(than)
    ma = [d.split("|")[1].strip() for d in bang if d.startswith("| ") and "Viết tắt" not in d]
    assert "HA" not in ma and "SD" not in ma  # tên tác giả trong danh mục tài liệu không phải chữ viết tắt
    assert ma == ["BHYT", "ĐTĐ", "KTC", "OR"]  # «Đ» sau «D», trước «E»


def test_k11_o_bang_viet_hoa_toan_bo_la_nhan_khong_phai_nhan_manh():
    md = "\n".join(["# 4. PHƯƠNG PHÁP", "", "| 16c | Chuyển nguy cơ tương đối | — | KHÔNG ÁP DỤNG |",
                    "| 17 | Ghi chú | Ước lượng CAO tỷ lệ | x |"])
    loi = KDN.loi_k11(md)
    assert len(loi) == 1 and "dòng 4" in loi[0]


def test_chuan_viet_doi_so_thap_phan_khong_cham_khong_dung_so_muc():
    van = "\n".join(["# 4. PHƯƠNG PHÁP", "", "So cận KTC với biên Δ = 0.1; xem mục 4.10 và phiên bản 3.14.6.",
                     "Mã `0.1` giữ nguyên.", "# 7. TÀI LIỆU THAM KHẢO", "", "1. Bài 0.5 mg. 2020."])
    ra = SDC._chuan_viet(van)
    assert "Δ = 0,1" in ra and "mục 4.10" in ra and "3.14.6" in ra and "`0.1`" in ra and "Bài 0.5 mg" in ra


def test_k11_mien_so_dinh_danh_khong_phai_so_dem():
    md = "\n".join(["# 4. PHƯƠNG PHÁP", "", "Bootstrap (B = 2000, seed 20261115 cố định).", "Theo Quyết định số 38690.",
                    "Khung 100000 hồ sơ."])
    loi = KDN.loi_k11(md)
    assert len(loi) == 1 and "dòng 5" in loi[0]
