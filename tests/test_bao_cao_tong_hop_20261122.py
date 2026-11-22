"""Bộ sinh báo cáo tổng hợp kết quả (nghiệm thu) — tools/bao_cao_tong_hop.py (22/11/2026)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import bao_cao_tong_hop as B  # noqa: E402
import hoi_dong_khoa_hoc as H  # noqa: E402

S = "ZZTEST-BC"
DE_CUONG = """# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## TỶ LỆ KIỂM SOÁT HUYẾT ÁP Ở NGƯỜI BỆNH NGOẠI TRÚ

## DANH MỤC CHỮ VIẾT TẮT

THA: tăng huyết áp

# 1. ĐẶT VẤN ĐỀ

Tăng huyết áp phổ biến [1]. Kiểm soát còn thấp [2, 3].

# 2. MỤC TIÊU NGHIÊN CỨU

## 2.1. Mục tiêu

Xác định tỷ lệ kiểm soát huyết áp.

# 3. TỔNG QUAN TÀI LIỆU

## 3.1. Bằng chứng hiện có

Các nghiên cứu trước [1–3] cho thấy khác biệt.

# 6. KẾ HOẠCH THỰC HIỆN

## 6.1. Nhân lực và phân công nhiệm vụ

Chủ nhiệm đề tài, thống kê viên, hai điều tra viên.

# 7. TÀI LIỆU THAM KHẢO

1. Alpha A. Hypertension burden worldwide in adults. Lancet. 2020. PMID: 11111111.
2. Beta B. Control of blood pressure in primary care clinics. BMJ. 2021. doi:10.1136/bmj.x2.
3. Gamma C. Adherence and blood pressure control among outpatients. JAMA. 2022. PMID: 33333333.

# PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU

Câu 1. Tuổi.

# PHỤ LỤC D. BẢNG BIẾN SỐ VÀ MÃ HOÁ

| Biến | Mã |
|---|---|
| tuoi | số |
"""
BAN_THAO = """# Tỷ lệ kiểm soát huyết áp

## II. PHƯƠNG PHÁP

### Kết quả chính và cách đo

Nghiên cứu cắt ngang đã thực hiện tại phòng khám [2].

## III. KẾT QUẢ

**Bảng 1. Đặc điểm đối tượng**

Tỷ lệ kiểm soát là 52,0% [1], tương tự [3] và [4].

## IV. BÀN LUẬN

Kết quả phù hợp với [1, 3].

## V. KẾT LUẬN

Khoảng một nửa người bệnh đạt kiểm soát.

## TÀI LIỆU THAM KHẢO (Vancouver format)

[1] [Tác giả] et al. Hypertension burden worldwide in adults. Lancet. 2020; PMID:11111111  *(Kiểm chứng trang)*
[2] [Tác giả] et al. Control of blood pressure in primary care clinics. BMJ. 2021; doi:10.1136/bmj.x2
[3] [Tác giả] et al. Adherence and blood pressure control among outpatients. JAMA. 2022; PMID:33333333
[4] Delta D. A cohort on home blood pressure telemonitoring. Hypertension. 2023; PMID:44444444  *(Cần kiểm)*
"""
DIEN_GIAI = """# Diễn giải kết quả

## 5. Hàm ý thực hành và hướng nghiên cứu tiếp

Rà soát điều trị cho nhóm chưa đạt đích.
"""


def _dung(tmp_path: Path, ban_thao: bool = True) -> Path:
    d = tmp_path / "exports" / S
    d.mkdir(parents=True)
    (d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(DE_CUONG, encoding="utf-8", newline="\n")
    if ban_thao:
        (d / f"G7_A8_MANUSCRIPT_{S}.md").write_text(BAN_THAO, encoding="utf-8", newline="\n")
    (d / f"G6_DIEN_GIAI_{S}.md").write_text(DIEN_GIAI, encoding="utf-8", newline="\n")
    return d


def test_du_chuong_dung_thu_tu_theo_huong_dan_chung(tmp_path):
    kq = B.sinh(S, _dung(tmp_path))
    ct = H.kiem_cau_truc_bao_cao(kq["van"])
    assert not ct.get("canh_bao"), ct
    # đề mục con của nguồn («Kết quả chính…» trong phương pháp) bị hạ cấp 4 ⇒ không bị nhận nhầm là Chương 3
    assert "#### Kết quả chính và cách đo" in kq["van"]
    assert not any(d.startswith("# ") and "KẾT QUẢ" in d and "CHƯƠNG 3" not in d for d in kq["van"].splitlines())


def test_trich_dan_ban_thao_danh_so_theo_danh_muc_de_cuong(tmp_path):
    van = B.sinh(S, _dung(tmp_path))["van"]
    kq_chuong = van.split("# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU")[1].split("# CHƯƠNG 4")[0]
    # bản thảo [1]=PMID 11111111 (đề cương 1), [3]=PMID 33333333 (đề cương 3), [4] chỉ có ở bản thảo ⇒ số 4 mới
    assert "52,0% [1], tương tự [3] và [4]" in kq_chuong
    tltk = van.split("# TÀI LIỆU THAM KHẢO")[1].split("# PHỤ LỤC")[0]
    dong = [d for d in tltk.splitlines() if d.strip()]
    assert len(dong) == 4 and dong[0].startswith("1. Alpha A.") and dong[3].startswith("4. Delta D.")
    # chú thích máy và «[Tác giả] et al.» không lọt vào báo cáo
    assert "Kiểm chứng" not in van and "[Tác giả]" not in van and "Cần kiểm" not in van
    assert dong[3].endswith("PMID:44444444")


def test_danh_so_lai_khi_thu_tu_hai_danh_muc_khac_nhau():
    goc = B.doc_tltk("1. A a. Title one about hypertension control. 2020. PMID: 1000001.\n"
                     "2. B b. Title two about adherence. 2021. PMID: 1000002.")
    them = B.doc_tltk("[1] X. Title two about adherence. PMID:1000002\n[2] Y. Title one about hypertension. "
                      "PMID:1000001")
    _, _, bd = B.gop_tltk(goc, them)
    assert bd == {"1": 2, "2": 1}
    van, thieu = B.doi_so_trich_dan("thấy [1] và [1–2], cả [2, 1]; lạ [9]", bd)
    assert van == "thấy [2] và [1, 2], cả [1, 2]; lạ [9]" and thieu == ["9"]


def test_gon_khoang_trich_dan():
    van, _ = B.doi_so_trich_dan("[1–4]", {"1": 1, "2": 2, "3": 3, "4": 4})
    assert van == "[1–4]"


def test_thieu_ban_thao_thi_khong_sinh(tmp_path):
    kq = B.sinh(S, _dung(tmp_path, ban_thao=False))
    assert "loi" in kq and "van" not in kq


def test_cli_chay_kho_khong_ghi_tep(tmp_path, capsys):
    d = _dung(tmp_path)
    assert B.main(["--study", S, "--goc", str(tmp_path)]) == 0
    assert not (d / f"BAO_CAO_TONG_HOP_{S}.md").exists()
    assert B.main(["--study", S, "--goc", str(tmp_path), "--ghi"]) == 0
    assert (d / f"BAO_CAO_TONG_HOP_{S}.md").read_text(encoding="utf-8").startswith("**BÁO CÁO TỔNG HỢP")


# ── 22/11/2026: báo cáo mang đủ phần tóm tắt và các mục cuối bài của bản thảo (đo K18 trên 8 thiết kế giả lập) ──
BAN_THAO_DU = BAN_THAO.replace("## II. PHƯƠNG PHÁP", "## TÓM TẮT CÓ CẤU TRÚC\n\nNghiên cứu cắt ngang trên 428 người "
                               "bệnh [1].\n\n## II. PHƯƠNG PHÁP").replace(
    "## TÀI LIỆU THAM KHẢO", "## LỜI CẢM ƠN\n\nCảm ơn người bệnh.\n\n## KHAI BÁO\n\nKinh phí: Bệnh viện; nhà tài trợ "
    "không tham gia. Xung đột lợi ích: không có. Dữ liệu chia sẻ khi có yêu cầu hợp lý [3].\n\n## TÀI LIỆU THAM KHẢO")


def _dung_du(tmp_path: Path) -> Path:
    d = _dung(tmp_path)
    (d / f"G7_A8_MANUSCRIPT_{S}.md").write_text(BAN_THAO_DU, encoding="utf-8", newline="\n")
    return d


def test_bao_cao_co_tom_tat_va_khai_bao_cua_ban_thao(tmp_path):
    kq = B.sinh(S, _dung_du(tmp_path))
    van = kq["van"]
    tt = van.split("# TÓM TẮT")[1].split("# ĐẶT VẤN ĐỀ")[0]
    assert "Nghiên cứu cắt ngang trên 428 người bệnh [1]." in tt
    kb = van.split("# LỜI CẢM ƠN VÀ KHAI BÁO")[1].split("# TÀI LIỆU THAM KHẢO")[0]
    assert "#### LỜI CẢM ƠN" in kb and "#### KHAI BÁO" in kb and "Xung đột lợi ích: không có" in kb
    assert "yêu cầu hợp lý [3]" in kb                                  # trích dẫn đánh số theo danh mục chung
    assert not H.kiem_cau_truc_bao_cao(van).get("canh_bao")
    assert "Lời cảm ơn và khai báo" in van.split("# MỤC LỤC")[1].split("# DANH MỤC")[0]


def test_thieu_muc_cuoi_thi_canh_bao_khong_bia(tmp_path):
    kq = B.sinh(S, _dung(tmp_path))                                    # bản thảo không có lời cảm ơn/khai báo
    assert any("lời cảm ơn/khai báo" in c for c in kq["canh_bao"])
    kb = kq["van"].split("# LỜI CẢM ƠN VÀ KHAI BÁO")[1].split("# TÀI LIỆU THAM KHẢO")[0]
    assert not kb.strip()


def test_muc_tieu_danh_so_thanh_cau_chi_duoi_de_muc_muc_tieu():
    khoi = "#### 2.1. Mục tiêu\n\n1. Xác định tỷ lệ.\n2. Mô tả yếu tố.\n\n#### 2.2. Giả thuyết\n\n1. Không đổi."
    ra = B._muc_tieu_thanh_cau(khoi)
    assert "Mục tiêu 1: Xác định tỷ lệ." in ra and "Mục tiêu 2: Mô tả yếu tố." in ra
    assert "\n1. Không đổi." in ra                                     # mục khác giữ nguyên


def test_ten_de_tai_in_hoa_va_muc_tieu_thanh_cau_trong_bao_cao(tmp_path):
    d = _dung(tmp_path)
    (d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(
        DE_CUONG.replace("## TỶ LỆ KIỂM SOÁT HUYẾT ÁP Ở NGƯỜI BỆNH NGOẠI TRÚ",
                         "## Tỷ lệ kiểm soát huyết áp ở người bệnh")
        .replace("Xác định tỷ lệ kiểm soát huyết áp.", "1. Xác định tỷ lệ kiểm soát huyết áp."),
        encoding="utf-8", newline="\n")
    van = B.sinh(S, d)["van"]
    assert "**TỶ LỆ KIỂM SOÁT HUYẾT ÁP Ở NGƯỜI BỆNH**" in van              # bìa: tên in hoa
    assert "Mục tiêu 1: Xác định tỷ lệ kiểm soát huyết áp." in van


# ── 22/11/2026 (tối): câu chuẩn báo cáo ở phần giới thiệu bản thảo phải sang đặt vấn đề của báo cáo ──────────────
GIOI_THIEU_BT = """## I. GIỚI THIỆU

**§1 Bối cảnh và gánh nặng bệnh:**
Tăng huyết áp là gánh nặng lớn ở phòng khám ngoại trú, chiếm tỷ lệ cao trong người bệnh mạn tính.

**§3 Mục tiêu và giả thuyết:**
Nghiên cứu xác định tỷ lệ kiểm soát huyết áp.
Vai trò dự kiến của xét nghiệm đánh giá trong lộ trình chẩn đoán: phân loại ban đầu trước khi chỉ định đo chuyên sâu.
Tăng huyết áp phổ biến [1].

---

"""


def _dung_gioi_thieu(tmp_path: Path) -> Path:
    d = _dung(tmp_path)
    p = d / f"G7_A8_MANUSCRIPT_{S}.md"
    p.write_text(BAN_THAO.replace("## II. PHƯƠNG PHÁP", GIOI_THIEU_BT + "## II. PHƯƠNG PHÁP", 1),
                 encoding="utf-8", newline="\n")
    return d


def _dat_van_de(van: str) -> str:
    a = van.index("# ĐẶT VẤN ĐỀ")
    return van[a:van.index("# CHƯƠNG 1.", a)]


def test_cau_chuan_bao_cao_o_gioi_thieu_ban_thao_sang_dat_van_de(tmp_path):
    """STARD 3 / TRIPOD+AI 3c: câu có nhãn dòng sau khối «§n» của bản thảo phải có trong đặt vấn đề báo cáo."""
    d = _dung_gioi_thieu(tmp_path)
    dvd = _dat_van_de(B.sinh(S, d)["van"])
    assert "Vai trò dự kiến của xét nghiệm đánh giá trong lộ trình chẩn đoán: phân loại ban đầu" in dvd


def test_than_khoi_nhan_so_khong_lap_lai_vao_dat_van_de(tmp_path):
    """Đoạn thân của khối «§n» đã do đặt vấn đề của đề cương phủ — không chép trùng."""
    d = _dung_gioi_thieu(tmp_path)
    dvd = _dat_van_de(B.sinh(S, d)["van"])
    assert "gánh nặng lớn ở phòng khám ngoại trú" not in dvd
    assert "Nghiên cứu xác định tỷ lệ kiểm soát huyết áp." not in dvd


def test_cau_da_co_trong_de_cuong_khong_chep_trung(tmp_path):
    """Câu sau khối «§n» đã có nguyên văn trong đặt vấn đề của đề cương ⇒ chỉ xuất hiện một lần."""
    d = _dung_gioi_thieu(tmp_path)
    dvd = _dat_van_de(B.sinh(S, d)["van"])
    assert dvd.count("Tăng huyết áp phổ biến [1].") == 1
