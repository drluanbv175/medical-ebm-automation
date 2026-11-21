"""K17 — đối chiếu đề cương với từng mục của chuẩn quốc tế và Việt Nam (21/11/2026).

Bác sĩ: «từng tiêu chuẩn trong từng cấu trúc đề cương nghiên cứu phải đạt tiêu chuẩn và sự tin cậy cao nhất», cho MỌI
thiết kế. Mỗi test khoá một hành vi đã phân xử trên hai đề cương thật (C1a, BTM) và tám đề cương giả lập.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))

import chuan_bao_cao_items as CBC  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KD  # noqa: E402


def _kq(md: str, tk: str = "cross_sectional"):
    return {(r.chuan, r.ma): r for r in K.doi_chieu(md, tk)["ket_qua"]}


# Đề cương khuôn BVQY175 tối thiểu nhưng ĐỦ mọi mục STROBE (cắt ngang) và chuẩn Việt Nam.
DU = """**ĐỀ CƯƠNG NGHIÊN CỨU**

# ĐẶT VẤN ĐỀ

Tỷ lệ kiểm soát huyết áp còn thấp [1]; tại đơn vị chưa có số liệu, đây là khoảng trống cần lấp.

## MỤC TIÊU NGHIÊN CỨU

1. ***Xác định tỷ lệ kiểm soát huyết áp.***
2. ***Phân tích một số yếu tố liên quan đến kiểm soát huyết áp.***

# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU

## 1.1. Khái niệm

Nội dung tổng quan [2].

# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 2.1. Đối tượng nghiên cứu

### 2.1.1. Tiêu chuẩn lựa chọn

- Người từ 18 tuổi.

### 2.1.2. Tiêu chuẩn loại trừ

- Có thai.

## 2.2. Địa điểm và thời gian nghiên cứu

- Địa điểm: Khoa Khám bệnh, Bệnh viện X.
- Thời gian thu thập số liệu: từ tháng 03/2027 đến tháng 09/2027.

## 2.3. Thiết kế nghiên cứu

Nghiên cứu cắt ngang có phân tích, thu thập tiến cứu tại một thời điểm.

## 2.4. Câu hỏi và giả thuyết nghiên cứu

Giả thuyết: tuổi cao liên quan với kiểm soát kém.

## 2.5. Cỡ mẫu và phương pháp chọn mẫu

### 2.5.1. Cỡ mẫu

Áp dụng công thức ước lượng một tỷ lệ với p = 0,5 theo nghiên cứu trước [3]; cỡ mẫu cuối cùng là 385 người.

### 2.5.2. Phương pháp chọn mẫu

Chọn mẫu ngẫu nhiên hệ thống; sơ đồ chọn mẫu ghi số người đủ tiêu chuẩn, từ chối và được phân tích, kèm lý do từ chối.

## 2.6. Phương pháp nghiên cứu

### 2.6.1. Công cụ và kỹ thuật thu thập số liệu

Nguồn số liệu: phiếu thu thập; huyết áp đo bằng máy đo tự động theo phương pháp chuẩn.

### 2.6.2. Biến số nghiên cứu

- Biến kết cục: kiểm soát huyết áp, định nghĩa theo tiêu chuẩn chẩn đoán của Bộ Y tế.
- Biến độc lập: tuổi, giới; yếu tố nhiễu được hiệu chỉnh theo DAG.
- Biến định lượng tuổi giữ dạng liên tục.

### 2.6.3. Sai số và biện pháp khống chế sai số

| Nguồn sai lệch | Biện pháp khống chế |
|---|---|
| Sai lệch thông tin do đo huyết áp | Dùng một loại máy đã hiệu chuẩn |

### 2.6.4. Xử lý và phân tích số liệu

Hồi quy Poisson ước lượng PR thô và hiệu chỉnh kèm khoảng tin cậy 95%.
Dữ liệu thiếu được mô tả theo từng biến; phân tích chính trên trường hợp đủ dữ liệu.
Phân tích độ nhạy loại người dùng thuốc mới.
Không có phân tích phân nhóm xác định trước.

## 2.7. Đạo đức trong nghiên cứu

Đề tài chỉ tiến hành sau khi có chấp thuận của Hội đồng Đạo đức. Người tham gia ký phiếu đồng ý.
Phiếu chỉ mang mã nghiên cứu (khử định danh); phân quyền truy cập; dữ liệu lưu trữ trên máy tính có mật khẩu.

# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN

## 3.1. Đặc điểm đối tượng nghiên cứu

Bảng đặc điểm chung; tỷ lệ kiểm soát huyết áp.

## 3.2. Dự kiến bàn luận

### 3.2.1. Bàn luận theo mục tiêu 1

So sánh với các nghiên cứu khác.

## 3.3. Hạn chế của nghiên cứu và phạm vi suy rộng kết quả

| Hạn chế | Chiều hướng sai lệch |
|---|---|
| Sai lệch chọn | Ước lượng cao tỷ lệ kiểm soát |

Kết quả chỉ suy rộng cho người bệnh tại khoa.

# PHỤ LỤC G. THÔNG TIN CHUNG VỀ ĐỀ TÀI

| Kinh phí | Tự túc (chủ nhiệm đề tài tự chi trả) |
"""


def test_du_lieu_nguyen_van_strobe_record_dung_so_muc_va_dung_chu():
    assert len(CBC.STROBE_2007_ITEMS) == 41 and len(CBC.RECORD_2015_ITEMS) == 13
    van = {(m, t): v for m, t, _c, v in CBC.STROBE_2007_ITEMS}
    assert van[("5", "chung")].startswith("Describe the setting, locations, and relevant dates")
    assert van[("12d", "cat_ngang")] == (
        "If applicable, describe analytical methods taking account of sampling strategy.")
    assert dict(CBC.RECORD_2015_ITEMS)["6.1"].startswith("The methods of study population selection")


def test_moi_dong_strobe_co_tieu_chi_cho_ca_ba_thiet_ke_quan_sat():
    for tk in ("cross_sectional", "cohort", "case_control"):
        muc = K.danh_sach_muc("STROBE 2007", tk)
        so_goc = {re.match(r"\d+", m.ma).group(0) for m in muc}
        assert so_goc == {str(i) for i in range(1, 23)}, tk  # đủ 22 mục STROBE
        bien_the = {m.nguyen_van for m in muc if m.ma == "6a"}
        assert len(bien_the) == 1, tk  # đúng MỘT biến thể 6a theo thiết kế


def test_de_cuong_du_yeu_to_khong_bi_bao_thieu():
    assert KD.loi_k17(DU, "cross_sectional") == []
    assert K.loi_k17(DU, "cross_sectional") == []


def test_thieu_moc_ngay_thi_strobe_5_thieu_dung_yeu_to():
    md = DU.replace("từ tháng 03/2027 đến tháng 09/2027", "trong thời gian nghiên cứu")
    r = _kq(md)[("STROBE 2007", "5")]
    assert r.trang_thai == "thieu" and r.thieu == ["mốc ngày cụ thể"]


def test_cau_phu_dinh_khong_kich_hoat_dieu_kien():
    assert not K.co_dieu_kien(r"phân tích phân nhóm", "Không có phân tích phân nhóm xác định trước.")
    assert not K.co_dieu_kien(r"bộ câu hỏi", "- Các đặc tính dành cho thang đo và bộ câu hỏi — không áp dụng.")
    assert K.co_dieu_kien(r"phân tích phân nhóm", "Phân tích phân nhóm theo giới.")


def test_chuan_dieu_kien_record_cross_va_tong_quan_he_thong():
    ten = lambda md, tk="cross_sectional": [c for c, _ in K.chuan_ap_dung(tk, md)]  # noqa: E731
    assert "RECORD 2015" in ten("Thời gian chờ lấy từ HIS.")
    assert "CROSS 2021" in ten("Số liệu thu thập bằng bộ câu hỏi tự điền.")
    assert "CROSS 2021" not in ten("Phiếu trích hồ sơ; các đặc tính của bộ câu hỏi — không áp dụng.")
    assert "CROSS 2021" not in ten("Nghiên cứu trích hồ sơ. Tổng quan các bộ câu hỏi hài lòng đã công bố [2].")
    # Tổng quan hệ thống: «cơ sở dữ liệu điện tử» là PubMed — không phải dữ liệu thường quy; không có người tham gia.
    sr = ten("Tìm trên cơ sở dữ liệu điện tử PubMed, trích xuất dữ liệu kép.", "sr_ma")
    assert sr == ["PRISMA-P 2015"]


def test_chuan_chua_co_tieu_chi_la_chua_do_khong_bao_gio_dat():
    # 21/11/2026 (PR 12 chuẩn): mọi chuẩn của 13 thiết kế đã có tiêu chí — ⚪ chỉ còn cho mã thiết kế ngoài bảng.
    kq = K.doi_chieu(DU, "case_series")
    assert [c for c, _ in kq["chua_do"]] == ["(không xác định)"]
    assert not any(r.chuan == "(không xác định)" for r in kq["ket_qua"])


def test_bang_sai_lech_doc_kem_hang_tieu_de_cot():
    r = _kq(DU)[("STROBE 2007", "9")]
    assert r.trang_thai == "dat"
    # Bỏ tiêu đề cột «Biện pháp khống chế» và ô biện pháp ⇒ không còn biện pháp cùng dòng với nguồn sai lệch.
    md = DU.replace("| Nguồn sai lệch | Biện pháp khống chế |", "| Nguồn | Ghi chú |").replace(
        "| Dùng một loại máy đã hiệu chuẩn |", "| Có thể xảy ra |")
    assert _kq(md)[("STROBE 2007", "9")].trang_thai == "thieu"


def test_tong_quan_khong_lam_bang_chung_cho_muc_phuong_phap():
    md = DU.replace("Nguồn số liệu: phiếu thu thập; huyết áp đo bằng máy đo tự động theo phương pháp chuẩn.",
                    "Như đã mô tả.")
    md = md.replace("Nội dung tổng quan [2].",
                    "Nội dung tổng quan [2].\n\n## 1.2. Công cụ đo huyết áp\n\n"
                    "Nguồn số liệu thường là phiếu; đo bằng máy [2].")
    assert _kq(md)[("STROBE 2007", "8")].trang_thai == "thieu"


def test_tieu_chuan_loai_tru_neu_bang_de_muc_duoc_tinh():
    assert _kq(DU)[("STROBE 2007", "6a")].trang_thai == "dat"
    md = DU.replace("### 2.1.2. Tiêu chuẩn loại trừ\n\n- Có thai.\n", "")
    assert _kq(md)[("STROBE 2007", "6a")].thieu == ["tiêu chuẩn loại"]


def test_kinh_phi_tu_tuc_la_khong_co_nha_tai_tro():
    assert _kq(DU)[("STROBE 2007", "22")].trang_thai == "dat"
    md = DU.replace("| Kinh phí | Tự túc (chủ nhiệm đề tài tự chi trả) |", "| Kinh phí | Đơn vị cấp |")
    md = md.replace("Người tham gia ký phiếu đồng ý.", "Nghiên cứu không can thiệp vào điều trị. Ký phiếu đồng ý.")
    assert _kq(md)[("STROBE 2007", "22")].trang_thai == "thieu"


def test_mien_dong_thuan_phai_dan_tt43_dieu_7():
    md = DU.replace("Người tham gia ký phiếu đồng ý.", "Đề nghị miễn đồng thuận vì dữ liệu hồi cứu, nguy cơ tối thiểu.")
    kq = _kq(md)
    assert kq[("Việt Nam", "TT43-Đ7.1b")].thieu == ["căn cứ TT43 Điều 7"]
    assert kq[("Việt Nam", "TT43-ĐỒNG-THUẬN")].trang_thai == "khong_ap_dung"
    md2 = md.replace("Đề nghị miễn đồng thuận",
                     "Đề nghị miễn đồng thuận theo Điều 7 khoản 1 điểm b Thông tư 43/2024/TT-BYT")
    assert _kq(md2)[("Việt Nam", "TT43-Đ7.1b")].trang_thai == "dat"


def test_k17_chan_ca_ban_nhap_cau_truc_cu():
    """21/11/2026 (sau khi bộ sinh dựng đủ mục chuẩn và 8 thiết kế giả lập đạt): K17 không còn chỉ chặn đề cương theo
    khuôn «# CHƯƠNG 1.» — bản nháp cấu trúc cũ 1–7 thiếu mục cũng bị chặn."""
    nhap = DU.replace("# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU", "# 3. TỔNG QUAN TÀI LIỆU")
    assert not re.search(r"^# CHƯƠNG 1\.", nhap, re.M)
    assert KD.loi_k17(nhap, "cross_sectional") == []  # bản nháp đủ mục: đạt
    hong = nhap.replace("từ tháng 03/2027 đến tháng 09/2027", "trong thời gian nghiên cứu")
    assert any(x.startswith("K17 STROBE 2007 mục 5") for x in KD.loi_k17(hong, "cross_sectional"))
    loi = KD.loi_k17(DU.replace("từ tháng 03/2027 đến tháng 09/2027", "trong thời gian nghiên cứu"), "cross_sectional")
    assert any(x.startswith("K17 STROBE 2007 mục 5") for x in loi)


# ─────────────── 21/11/2026 — phân xử trên 8 đề cương giả lập sinh lại (bộ sinh dựng từng mục chuẩn) ───────────────
def test_dong_con_o_trong_khong_lam_bang_chung():
    """Nhãn có mặt ≠ nội dung có mặt: «Lý do chọn …: ………» không được tính là có lý do; câu thật kèm ô số quyết định
    để trống ở câu SAU vẫn là bằng chứng (C1a: «… phê duyệt của Hội đồng Y đức … Số quyết định phê duyệt: ………»)."""
    assert K.o_trong_quanh("- Lý do chọn nhóm bệnh và nhóm chứng: ………", 3)
    assert not K.o_trong_quanh("Chỉ tiến hành sau khi có phê duyệt của Hội đồng. Số quyết định: ………", 20)
    hang = "| Sai lệch chọn | ……… | Tập huấn |\t⟦| Nguồn | Chiều ảnh hưởng | Biện pháp |⟧"
    assert K.o_trong_quanh(hang, hang.index("Chiều"))  # chữ «chiều» chỉ có ở tiêu đề cột, ô của hàng trống
    md = DU.replace("| Sai lệch chọn | Ước lượng cao tỷ lệ kiểm soát |", "| Sai lệch chọn | ……… |")
    assert md != DU
    assert _kq(md)[("STROBE 2007", "19")].trang_thai == "thieu"
    assert not K.co_dieu_kien(K.GHEP_CAP, "- Ghép cặp: ………")  # nhãn ô trống không kích hoạt điều kiện


def test_dieu_kien_phan_tich_chi_xet_muc_tieu():
    """Đề tài MÔ TẢ: chữ «OR» của chuỗi tìm PubMed và «liên quan đến» của câu đạo đức không biến nó thành đề tài phân
    tích (từng đòi phơi nhiễm, giả thuyết, ước lượng thô/hiệu chỉnh)."""
    mo_ta = DU.replace("2. ***Phân tích một số yếu tố liên quan đến kiểm soát huyết áp.***\n", "").replace(
        "Giả thuyết: tuổi cao liên quan với kiểm soát kém.", "Nghiên cứu mô tả, không kiểm định giả thuyết.")
    assert mo_ta.count("liên quan") < DU.count("liên quan")
    mo_ta += "\n> (hypertension[MeSH] OR hypertension[tiab])\n\nMọi vấn đề liên quan đến nghiên cứu báo chủ nhiệm.\n"
    cac = K.tach_phan(mo_ta)
    assert not K.dieu_kien(K.MUC_TIEU_PHAN_TICH, mo_ta, cac)
    assert K.co_dieu_kien(K.PHAN_TICH, mo_ta)  # biểu thức cũ trên cả văn bản thì khớp — đúng lỗi đã gặp
    assert _kq(mo_ta)[("STROBE 2007", "16a")].trang_thai == "khong_ap_dung"
    assert K.dieu_kien(K.MUC_TIEU_PHAN_TICH, DU, K.tach_phan(DU))  # có mục tiêu yếu tố liên quan ⇒ phân tích
    # «Bàn luận theo mục tiêu k» (so sánh với nghiên cứu khác) không phải mục tiêu
    bl = mo_ta + "\n### 3.6.1. Bàn luận theo mục tiêu 1\n\nSo sánh với các nghiên cứu trong nước.\n"
    assert not K.dieu_kien(K.MUC_TIEU_PHAN_TICH, bl, K.tach_phan(bl))


def test_phan_doi_tuong_khong_lay_chuong_ket_qua():
    md = DU + "\n## 3.1. Đặc điểm đối tượng nghiên cứu\n\nLý do loại được ghi đầy đủ.\n"
    khoi = K.khoi_cua(K.tach_phan(md), ("doi_tuong",))
    assert khoi and not any("Đặc điểm" in p.tieu_de for p in khoi)


def test_ba_mau_bat_sot_cach_viet_hop_le():
    benh_chung = "### 2.1.3. Nhóm bệnh và nhóm chứng\n\n- Nhóm chứng: ghép theo giới, tỷ lệ 2 chứng : 1 ca.\n"
    r6b = {r.ma: r for r in K.doi_chieu(DU + "\n" + benh_chung, "case_control")["ket_qua"]}["6b"]
    assert r6b.trang_thai == "dat", r6b.thieu
    # Hai nhánh của điều kiện ghép cặp, mỗi nhánh tự đủ (đề tài ghép mà không viết chữ «ghép cặp»)
    assert K.co_dieu_kien(K.GHEP_CAP, "Chứng chọn cùng tuần, ghép theo giới và nhóm tuổi 5 năm.")
    assert K.co_dieu_kien(K.GHEP_CAP, "Mỗi ca chọn 2 chứng : 1 ca cùng tuần.")
    assert not K.co_dieu_kien(K.GHEP_CAP, "Chứng chọn ngẫu nhiên trong danh sách khám cùng tuần.")
    m8 = [m for m in K.danh_sach_muc("STROBE 2007", "cohort") if m.ma == "8"][0]
    tuong_dong = [y for y in m8.yeu_to if y.ten.startswith("tương đồng")][0]
    assert re.search(tuong_dong.mau, "cùng bộ câu hỏi cho ca và chứng", re.I)
    m10 = [m for m in K.danh_sach_muc("STROBE 2007", "cross_sectional") if m.ma == "10"][0]
    nguon = [y for y in m10.yeu_to if y.ten == "tham số có nguồn"][0]
    assert re.search(nguon.mau, "tỷ lệ ước tính p = 0,5 (chọn p = 0,5 để có cỡ mẫu lớn nhất khi chưa có số liệu)", re.I)
