"""Luật dùng chung «không cung cấp thông tin» của K17/K18 (23/11/2026).

Agent G7 phát hiện: «tuân thủ tự khai chưa phân tích» từng làm mọi bản thảo RCT đạt CONSORT 2025 mục 24a — yếu
tố chỉ khớp từ khoá «tuân thủ» nên câu phủ định/trì hoãn cũng thoả. Luật mới (`kiem_chuan_de_cuong_theo_muc.
khong_cung_cap_thong_tin`, gọi trong `_tim` cho MỌI yếu tố): lần khớp sát một cụm «chưa phân tích / báo cáo sau / ở
bài khác / không có thông tin / không được đánh giá» cùng mệnh đề không là bằng chứng. Lời khai «không có X» có thật mà
chuẩn cho phép (không có PPI, không có thay đổi so với đề cương, không chia sẻ dữ liệu, không phân tích phân bố kèm lý
do) quyết bằng biểu thức của chính tiêu chí (chữ phủ định nằm trong lần khớp).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import tieu_chi_ban_thao as K18  # noqa: E402


def _khop(cau: str, cum: str) -> bool:
    i = cau.index(cum)
    return K.khong_cung_cap_thong_tin(cau, i, i + len(cum))


@pytest.mark.parametrize("cau, cum, mong", [
    ("Tuân thủ tự khai chưa phân tích ở đợt này.", "Tuân thủ", True),
    ("Chưa đánh giá tuân thủ.", "tuân thủ", True),
    ("Biến cố bất lợi sẽ được báo cáo ở bài riêng.", "Biến cố bất lợi", True),
    ("Độ tin cậy của thang: không có thông tin.", "Độ tin cậy", True),
    ("Tuân thủ được báo cáo sau.", "Tuân thủ", True),
    ("| Tuân thủ | Chưa phân tích |", "Tuân thủ", True),
    # lời khai «không có X» có thật / câu kế hoạch tương lai / câu nhiều vế — KHÔNG phải thiếu thông tin
    ("Không có sự tham gia của người bệnh hoặc công chúng trong thiết kế.", "sự tham gia của người bệnh", False),
    ("Không có thay đổi nào so với đề cương và kế hoạch phân tích đã khoá sau khi bắt đầu.", "thay đổi", False),
    ("Dữ liệu sẽ được phân tích bằng R 4.6.", "phân tích", False),
    ("Tuân thủ được đánh giá bằng đếm viên thuốc còn lại.", "Tuân thủ", False),
    ("Kết quả không xác định của xét nghiệm được báo cáo riêng và không đưa vào bảng 2 × 2.", "bảng 2 × 2", False),
    ("Dữ liệu không được thu thập cho câu hỏi nghiên cứu này, nên có thể phân loại sai các biến.", "phân loại sai",
     False),
    ("chọn p = 0,5 để có cỡ mẫu lớn nhất khi chưa có số liệu tại cơ sở", "p = 0,5", False),
])
def test_nhan_dien_cau_khong_cung_cap_thong_tin(cau, cum, mong):
    assert _khop(cau, cum) is mong


def test_chu_phu_dinh_nam_trong_lan_khop_la_loi_khai_tieu_chi_nhan():
    """Biểu thức của yếu tố chủ ý nhận lời khai («(không|chưa) chia sẻ dữ liệu») ⇒ vẫn là bằng chứng; cụm bắt đầu
    TRƯỚC lần khớp («chưa phân tích độ nhạy» với yếu tố khớp «phân tích độ nhạy») thì không."""
    cau = "Dữ liệu chưa phân tích độ nhạy."
    assert K.khong_cung_cap_thong_tin(cau, cau.index("phân tích độ nhạy"), len(cau) - 1)
    cau2 = "Dữ liệu cá thể chưa chia sẻ công khai."
    assert not K.khong_cung_cap_thong_tin(cau2, cau2.index("chưa chia sẻ"), cau2.index("chưa chia sẻ") + 12)


_BT = ("# TIN NHẮN NHẮC UỐNG THUỐC: THỬ NGHIỆM NGẪU NHIÊN\n\n## TÓM TẮT\n\nThử nghiệm ngẫu nhiên.\n\n"
       "## I. GIỚI THIỆU\n\nNội dung [1].\n\n## II. PHƯƠNG PHÁP\n\nThử nghiệm ngẫu nhiên song song hai nhánh.\n\n"
       "## III. KẾT QUẢ\n\n{kq}\n\n## IV. BÀN LUẬN\n\nBàn luận.\n")


def _k18(kq: str) -> dict:
    return {(r.chuan, r.ma): r for r in K18.doi_chieu_ban_thao(_BT.format(kq=kq), "rct", co_so_lieu=True)["ket_qua"]}


def test_consort_24a_khong_dat_nho_cau_tri_hoan():
    hoan = _k18("Kết cục phụ (huyết áp tâm thu; tuân thủ tự khai) chưa phân tích ở đợt này — báo cáo riêng theo "
                "SAP.")
    assert hoan[("CONSORT 2025", "24a")].trang_thai == "thieu"
    co = _k18("Tỷ lệ tuân thủ (nhận ≥ 80% tin nhắn) là 87% ở nhóm can thiệp; can thiệp được thực hiện đúng kế "
              "hoạch.")
    assert co[("CONSORT 2025", "24a")].trang_thai == "dat"


def test_loi_khai_khong_co_thay_doi_van_dat_consort_10():
    md = _BT.format(kq="Kết quả.").replace(
        "Thử nghiệm ngẫu nhiên song song hai nhánh.",
        "Thử nghiệm ngẫu nhiên song song hai nhánh. *Thay đổi so với đề cương sau khi bắt đầu nghiên cứu:* Không có "
        "thay đổi nào so với đề cương và kế hoạch phân tích đã khoá sau khi bắt đầu nghiên cứu.")
    kq = {(r.chuan, r.ma): r for r in K18.doi_chieu_ban_thao(md, "rct", co_so_lieu=True)["ket_qua"]}
    assert kq[("CONSORT 2025", "10")].trang_thai == "dat"


def _k17(md: str, tk: str) -> dict:
    return {(r.chuan, r.ma): r for r in K.doi_chieu(md, tk)["ket_qua"]}


_DC = ("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\nNội dung.\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n"
       "## 4.10. Xử lý và phân tích số liệu\n\n{pt}\n\n## 6.5. Đăng ký nghiên cứu và phổ biến kết quả\n\n{pb}\n")


def test_ppi_khai_khong_co_van_dat_spirit_11():
    md = _DC.format(pt="Hồi quy Poisson.", pb="- Sự tham gia của người bệnh và công chúng: Không có sự tham gia của "
                                              "người bệnh hoặc công chúng trong thiết kế.")
    assert _k17(md, "rct")[("SPIRIT 2025", "11")].trang_thai == "dat"


def test_cheers_19_khai_khong_phan_tich_kem_ly_do_dat_khong_ly_do_thi_thieu():
    md = ("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\nNội dung.\n\n# 4. PHƯƠNG PHÁP\n\n## 4.12. Đánh giá kinh tế y tế\n\n{x}\n")
    co = md.format(x="- Tác động phân bố (công bằng): Không phân tích tác động phân bố theo nhóm thu nhập vì phiếu thu "
                     "thập không ghi thu nhập.")
    khong = md.format(x="- Kinh tế: chưa phân tích tác động phân bố.")
    quyet = md.format(x="- Tác động phân bố: Không phân tích phân bố tác động theo nhóm thu nhập hay vùng.")
    assert _k17(quyet, "economic")[("CHEERS 2022", "19")].trang_thai == "dat"  # quyết định đã khai (không kèm lý do)
    assert _k17(co, "economic")[("CHEERS 2022", "19")].trang_thai == "dat"
    assert _k17(khong, "economic")[("CHEERS 2022", "19")].trang_thai == "thieu"
