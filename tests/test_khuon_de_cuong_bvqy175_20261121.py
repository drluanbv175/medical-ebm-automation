"""Khuôn «Hướng dẫn viết đăng ký và báo cáo đề tài KH&CN cấp bệnh viện» cho đề cương nộp (21/11/2026).

Phủ: bộ chuyển `tools/khuon_de_cuong_bvqy175.py`; luật K14 + giới hạn K10 của `kiem_de_cuong_nop_hoi_dong.py`; chế độ
khuôn của `md2docx_vn.py` (14pt, giãn 1,5, lề, ba phần đánh số trang, mục lục tự động, danh mục không viền, đúng thứ tự
lược đồ OOXML); và các công cụ đọc đề cương phải hiểu đề mục «CHƯƠNG n.» (`khung_bieu_bang`, `ho_so_hdd_bvqy175`,
`phan_bien_may_de_cuong`, `ho_so_dtcs_bvqy175`, `goi_bao_ve_hoi_dong`, `sinh_de_cuong_nop_hoi_dong`).

Fixture tự soạn, ngoại tuyến, không dữ liệu thật (repo công khai): đề cương cấu trúc cũ «1. ĐẶT VẤN ĐỀ … 7. TÀI LIỆU
THAM KHẢO» mang đủ kiểu dữ kiện mà bộ chuyển phải xử lý."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import goi_bao_ve_hoi_dong as GB  # noqa: E402
import ho_so_dtcs_bvqy175 as DT  # noqa: E402
import ho_so_hdd_bvqy175 as HDD  # noqa: E402
import khung_bieu_bang as KBB  # noqa: E402
import khuon_de_cuong_bvqy175 as K  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import phan_bien_may_de_cuong as PB  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SINH  # noqa: E402

DE_CUONG_CU = """**BỘ QUỐC PHÒNG**
**BỆNH VIỆN MẪU 175**

# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## THÔNG TIN CHUNG VỀ ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Khảo sát thử tại Khoa Mẫu |
| Chủ nhiệm đề tài | BS. Người Thử – Khoa Mẫu, Bệnh viện Mẫu 175 |
| Đơn vị chủ trì | Khoa Mẫu, Bệnh viện Mẫu 175 |
| Thời gian thực hiện | Từ tháng 12/2026 đến tháng 06/2027 (chi tiết ở mục 4.3 và 4.4) |
| Kinh phí | Tự túc |

## TÓM TẮT ĐỀ CƯƠNG

Tóm tắt ngắn của đề cương thử.

## DANH MỤC CHỮ VIẾT TẮT

| Viết tắt | Nghĩa |
|---|---|
| BYT | Bộ Y tế |

# 1. ĐẶT VẤN ĐỀ

Thời gian chờ là điểm yếu thường gặp [3]. Tại khoa mẫu chưa có số liệu [1].

Vì vậy chúng tôi tiến hành đề tài này với các mục tiêu trình bày ở mục 2.

1. Xác định tỷ lệ hài lòng tại khoa mẫu.
2. Phân tích yếu tố liên quan.

# 2. MỤC TIÊU NGHIÊN CỨU

## 2.1. Mục tiêu

1. Xác định tỷ lệ hài lòng tại khoa mẫu.
2. Phân tích yếu tố liên quan.

## 2.2. Câu hỏi nghiên cứu

Tỷ lệ hài lòng tại khoa mẫu là bao nhiêu?

# 3. TỔNG QUAN TÀI LIỆU

## 3.1. Khái niệm

Hài lòng là đánh giá chủ quan của người bệnh [2].

## 3.2. Khoảng trống nghiên cứu và đóng góp của đề tài

Chưa có số liệu tại khoa mẫu (xem mục 4.2, 4.4 và Bảng 5.1).

# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 4.1. Thiết kế nghiên cứu

Nghiên cứu mô tả cắt ngang [4].

## 4.2. Đối tượng nghiên cứu

Người bệnh từ đủ 18 tuổi.

## 4.3. Địa điểm và thời gian nghiên cứu

Khoa Mẫu, từ tháng 12/2026.

## 4.4. Cỡ mẫu

Cỡ mẫu 385 người.

## 4.5. Biến số và chỉ số nghiên cứu

Biến số chính trình bày ở mục 4.4–4.5.

## 4.6. Xử lý và phân tích số liệu

Phân tích mô tả.

## 4.7. Hạn chế của nghiên cứu

Một khoa duy nhất.

## 4.8. Đạo đức trong nghiên cứu

Tuân thủ Tuyên bố Helsinki.

# 5. DỰ KIẾN KẾT QUẢ

## 5.1. Kết quả theo mục tiêu 1

**Bảng 5.1. Tỷ lệ hài lòng (Mục tiêu 1)**

| Chỉ số | n (%) |
|---|---|
| Hài lòng | |

# 6. KẾ HOẠCH THỰC HIỆN

## 6.1. Nhân lực và phân công nhiệm vụ

| Vai trò | Nhiệm vụ chính |
|---|---|
| Chủ nhiệm đề tài | Chịu trách nhiệm chung |

## 6.2. Dự trù kinh phí

Tự túc.

# 7. TÀI LIỆU THAM KHẢO

1. Bộ Y tế. Quyết định về đo lường sự hài lòng. Hà Nội: Bộ Y tế; 2024.
2. Smith J, Brown K. Patient satisfaction: a review. BMJ. 2021;372:1-2.
3. Nguyễn Văn Bình, Trần Thị An. Sự hài lòng của người bệnh ngoại trú. Tạp chí Y học Việt Nam. 2023;530(1):1-5.
4. Adams P. Cross-sectional designs. Lancet. 2019;393:1-2.
5. Lê Thị Cúc. Thời gian chờ khám bệnh. Tạp chí Y học Thực hành. 2022;12(2):3-4.

# PHỤ LỤC A. PHIẾU KHẢO SÁT

Phiếu giả.

# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA

Bản giả.
"""


@pytest.fixture(scope="module")
def ket() -> K.KetQua:
    return K.chuyen(DE_CUONG_CU, nam=2026)


def _h1(md: str):
    return [d[2:] for d in md.splitlines() if d.startswith("# ")]


def _muc(md: str, de_muc: str) -> str:
    """Thân của mục có đề mục `de_muc` (tới đề mục cùng cấp hoặc cao hơn kế tiếp)."""
    dong = md.splitlines()
    i = next(k for k, d in enumerate(dong) if d.strip() == de_muc)
    cap = len(de_muc) - len(de_muc.lstrip("#"))
    j = next((k for k in range(i + 1, len(dong)) if re.match(rf"^#{{1,{cap}}}\s", dong[k])), len(dong))
    return "\n".join(dong[i + 1:j])


# ── bộ chuyển khuôn ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_khoa_viet_xep_dung_bang_chu_cai_tieng_viet():
    ds = ["Đức", "Bảo", "Dung", "Anh", "Ánh", "Ăn"]
    assert sorted(ds, key=K.khoa_viet) == ["Anh", "Ánh", "Ăn", "Bảo", "Dung", "Đức"]


def test_xep_tltk_theo_ngon_ngu_ten_ho_co_quan():
    muc = {1: "Bộ Y tế. Quyết định. 2024.", 2: "Smith J. Review. BMJ. 2021;1:1.",
           3: "Nguyễn Văn Bình. Bài Việt. Tạp chí. 2023;1:1.", 4: "Adams P. Design. Lancet. 2019;1:1.",
           5: "Lê Thị Cúc. Bài khác. Tạp chí. 2022;1:1.", 6: "García L. Satisfacción del paciente. Rev. 2020;1:1."}
    viet, ngoai, ban_do = K.xep_tltk(muc)
    # Việt: tác giả theo TÊN (Bình, Cúc), cơ quan theo chữ đầu (Bộ ⇒ vần B, sau «Bình» vì i < ô)
    assert [k for k, _v in viet] == [3, 1, 5]
    # ngoại: theo HỌ; bài tiếng Tây Ban Nha không có chữ riêng của tiếng Việt ⇒ nhóm ngoại ngữ
    assert [k for k, _v in ngoai] == [4, 6, 2]
    assert ban_do == {3: 1, 1: 2, 5: 3, 4: 4, 6: 5, 2: 6}


def test_chuyen_dung_thu_tu_cau_truc_cua_huong_dan(ket):
    h1 = _h1(ket.md)
    thu_tu = ["DANH SÁCH CÁC CÁN BỘ THAM GIA THỰC HIỆN ĐỀ TÀI", "MỤC LỤC", "DANH MỤC CÁC CHỮ VIẾT TẮT",
              "DANH MỤC CÁC BẢNG, BIỂU ĐỒ, HÌNH", "ĐẶT VẤN ĐỀ", "CHƯƠNG 1. TỔNG QUAN TÀI LIỆU",
              "CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", "CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN",
              "TÀI LIỆU THAM KHẢO"]
    assert [h for h in h1 if h in thu_tu] == thu_tu
    assert h1[-4:] == ["PHỤ LỤC A. PHIẾU KHẢO SÁT", "PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA",
                       "PHỤ LỤC C. KẾ HOẠCH THỰC HIỆN", "PHỤ LỤC D. THÔNG TIN CHUNG VỀ ĐỀ TÀI"]
    assert not ket.canh_bao
    assert KDN.loi_k14(ket.md) == []


def test_chuong_2_xep_theo_huong_dan_han_che_sang_chuong_3(ket):
    h = [d for d in ket.md.splitlines() if re.match(r"^#{2,3} [23]\.", d)]
    assert h == ["## 2.1. Đối tượng nghiên cứu", "## 2.2. Địa điểm và thời gian nghiên cứu",
                 "## 2.3. Thiết kế nghiên cứu", "## 2.4. Câu hỏi và giả thuyết nghiên cứu",
                 "### 2.4.1. Câu hỏi nghiên cứu", "## 2.5. Cỡ mẫu", "## 2.6. Phương pháp nghiên cứu",
                 "### 2.6.1. Biến số và chỉ số nghiên cứu", "### 2.6.2. Xử lý và phân tích số liệu",
                 "## 2.7. Đạo đức trong nghiên cứu", "## 3.1. Kết quả theo mục tiêu 1", "## 3.2. Dự kiến bàn luận",
                 "### 3.2.1. Bàn luận theo mục tiêu 1", "### 3.2.2. Bàn luận theo mục tiêu 2",
                 "## 3.3. Hạn chế của nghiên cứu"]


def test_trich_dan_va_tham_chieu_doi_so_dung_noi_dung(ket):
    md = ket.md
    # [3] cũ (Nguyễn Văn Bình) ⇒ [1]; [1] cũ (Bộ Y tế) ⇒ [2]; [2] cũ (Smith) ⇒ [5]; [4] cũ (Adams) ⇒ [4]
    assert "Thời gian chờ là điểm yếu thường gặp [1]. Tại khoa mẫu chưa có số liệu [2]." in md
    assert "đánh giá chủ quan của người bệnh [5]." in md
    assert "Nghiên cứu mô tả cắt ngang [4]." in md
    tl = _muc(md, "# TÀI LIỆU THAM KHẢO")
    assert re.search(r"^1\. Nguyễn Văn Bình", tl, re.M) and re.search(r"^2\. Bộ Y tế", tl, re.M)
    assert re.search(r"^5\. Smith J", tl, re.M)
    assert tl.index("**Tài liệu tiếng Việt**") < tl.index("**Tài liệu tiếng Anh**")
    # danh sách mục sau MỘT chữ «mục» — mọi số đều đổi (lỗi đo BTM 21/11: chỉ số đầu được đổi); khoảng «4.4–4.5»
    assert "(xem mục 2.1, 2.5 và Bảng 3.1)" in md
    assert "trình bày ở mục 2.5–2.6.1" in md
    assert "(chi tiết ở mục 2.2 và 2.5)" in md  # ô bảng của phụ lục thông tin chung


def test_dat_van_de_ten_de_tai_va_muc_tieu_theo_khuon(ket):
    dvd = _muc(ket.md, "# ĐẶT VẤN ĐỀ")
    assert "tiến hành đề tài “**Khảo sát thử tại Khoa Mẫu**” với các mục tiêu trình bày dưới đây." in dvd
    assert "## MỤC TIÊU NGHIÊN CỨU" in dvd
    assert "1. ***Xác định tỷ lệ hài lòng tại khoa mẫu.***" in dvd
    # danh sách mục tiêu lặp trong đặt vấn đề bị bỏ ⇒ mỗi mục tiêu đúng MỘT lần
    assert dvd.count("Xác định tỷ lệ hài lòng tại khoa mẫu.") == 1


def test_bia_bia_phu_danh_sach_can_bo(ket):
    dau = ket.md.split("# DANH SÁCH CÁC CÁN BỘ")[0]
    assert dau.startswith("**BỘ QUỐC PHÒNG**\n**BỆNH VIỆN MẪU 175**")
    assert dau.count("**ĐỀ CƯƠNG NGHIÊN CỨU**") == 2 and dau.count("**THÀNH PHỐ HỒ CHÍ MINH, 2026**") == 2
    assert "**Chủ nhiệm đề tài: BS. Người Thử**" in dau
    assert "**CHỦ NHIỆM KHOA**" in dau and "**VIỆN TRƯỞNG**" in dau
    ds = _muc(ket.md, "# DANH SÁCH CÁC CÁN BỘ THAM GIA THỰC HIỆN ĐỀ TÀI")
    assert "| 1 | BS. Người Thử | Khoa Mẫu, Bệnh viện Mẫu 175 | Chủ nhiệm đề tài |" in ds


def test_bao_cao_bo_tom_tat_giu_thong_tin_chung(ket):
    assert "Tóm tắt ngắn của đề cương thử." not in ket.md
    assert any("bỏ mục «tóm tắt»" in x for x in ket.bao_cao)
    ttc = _muc(ket.md, "# PHỤ LỤC D. THÔNG TIN CHUNG VỀ ĐỀ TÀI")
    assert "| Kinh phí | Tự túc |" in ttc


def test_chuyen_lan_hai_khong_doi(ket):
    lai = K.chuyen(ket.md)
    assert lai.da_theo_khuon and lai.md == ket.md


def test_canh_bao_khi_thieu_danh_muc_chu_viet_tat():
    md = re.sub(r"## DANH MỤC CHỮ VIẾT TẮT\n\n(?:\|.*\n)+", "", DE_CUONG_CU)
    kq = K.chuyen(md, nam=2026)
    assert any("danh mục chữ viết tắt" in x for x in kq.canh_bao)
    assert any("danh mục các chữ viết tắt" in x for x in KDN.loi_k14(kq.md))


def test_chay_kho_khong_ghi_ghi_that_co_sao_luu(tmp_path):
    ma = "de-tai-khuon-thu"
    d = tmp_path / ma
    d.mkdir()
    p = d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md"
    p.write_text(DE_CUONG_CU, encoding="utf-8", newline="\n")
    kho = K.chay(ma, d, ghi=False, nam=2026)
    assert kho["ma"] == 0 and p.read_text(encoding="utf-8") == DE_CUONG_CU
    assert not (d / "_sao_luu_de_cuong").exists()
    pytest.importorskip("docx")
    that = K.chay(ma, d, ghi=True, nam=2026)
    assert p.read_text(encoding="utf-8").count("# CHƯƠNG 1.") == 1
    sao = list((d / "_sao_luu_de_cuong").glob("*.truoc-khuon-*.md"))
    assert len(sao) == 1 and sao[0].read_text(encoding="utf-8") == DE_CUONG_CU
    assert Path(that["docx"]).is_file()


# ── K14 · K10 của bộ kiểm đề cương nộp ──────────────────────────────────────────────────────────────────────────────

def test_k14_bo_qua_de_cuong_cau_truc_cu():
    assert KDN.loi_k14(DE_CUONG_CU) == []


@pytest.mark.parametrize("sua, mong", [
    (lambda m: m.replace("# ĐẶT VẤN ĐỀ\n", "# MỞ ĐẦU\n"), "thiếu phần «đặt vấn đề»"),
    (lambda m: m.replace("# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU", "@@").replace(
        "# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", "# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU").replace(
        "@@", "# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU"), "đứng trước"),
    (lambda m: m.replace("**ĐỀ CƯƠNG NGHIÊN CỨU**", "**TÀI LIỆU**"), "ĐỀ CƯƠNG NGHIÊN CỨU"),
    (lambda m: m.replace("**THÀNH PHỐ HỒ CHÍ MINH, 2026**", "**THÀNH PHỐ HỒ CHÍ MINH**"), "Địa danh, năm"),
    (lambda m: m.replace("**CHỦ NHIỆM KHOA**", "**TRƯỞNG PHÒNG**"), "Chủ nhiệm khoa"),
    (lambda m: m.replace("“**Khảo sát thử tại Khoa Mẫu**”", "Khảo sát thử tại Khoa Mẫu"), "ngoặc kép"),
    (lambda m: m.replace("1. ***Xác định tỷ lệ hài lòng tại khoa mẫu.***", "1. Xác định tỷ lệ hài lòng tại khoa mẫu."),
     "chưa in nghiêng, đậm"),
    (lambda m: m.replace("## MỤC TIÊU NGHIÊN CỨU", "**Mục tiêu**"), "cuối phần đặt vấn đề"),
    (lambda m: m.replace("1. Nguyễn Văn Bình", "@@").replace("4. Adams P", "1. Adams P").replace(
        "@@", "4. Nguyễn Văn Bình"), "riêng theo ngôn ngữ"),
    (lambda m: m.replace("1. Nguyễn Văn Bình, Trần Thị An.", "1. Lê Văn Xuân.").replace(
        "3. Lê Thị Cúc.", "3. Lê Thị An."), "chưa theo ABC"),
    (lambda m: re.sub(r"(?<=\. )20(1\d|2\d)(?=;|\.)", "2001", m), "10 năm"),
    (lambda m: m.replace("| Bảng 3.1 |", "| Bảng 3.9 |"), "danh mục bảng, biểu thiếu: Bảng 3.1"),
    (lambda m: m.replace("\n5. Smith J", "\n6. Smith J"), "không liền từ 1"),
])
def test_k14_bat_tung_luat(ket, sua, mong):
    loi = KDN.loi_k14(sua(ket.md))
    assert any(mong in x for x in loi), loi


def test_k10_khong_ap_cho_du_kien_ket_qua_nhung_ap_cho_du_kien_ban_luan():
    md = ("# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN\n\nTỷ lệ dự kiến khoảng 80% người bệnh hài lòng.\n\n"
          "## 3.2. Dự kiến bàn luận\n\nTỷ lệ này cao hơn mức 60% của một nghiên cứu khác.\n")
    loi = KDN.loi_k10(md)
    assert len(loi) == 1 and "60%" in loi[0]
    # cấu trúc cũ: chương «BÀN LUẬN» vẫn bị kiểm như trước
    assert KDN.loi_k10("# 6. BÀN LUẬN\n\nTỷ lệ 70% cao hơn.\n")


# ── md2docx chế độ khuôn ────────────────────────────────────────────────────────────────────────────────────────────

def test_md2docx_khuon_dinh_dang_va_dung_luoc_do(ket, tmp_path):
    docx = pytest.importorskip("docx")
    import md2docx_vn as M
    from docx.shared import Cm, Pt

    p = M.markdown_to_docx(ket.md, tmp_path / "khuon.docx", khuon_bvqy175=True)
    d = docx.Document(str(p))
    assert len(d.sections) == 3  # bìa (không số) · phần đầu (La Mã) · từ Đặt vấn đề (Ả rập)
    s0 = d.sections[0]
    assert abs(s0.left_margin - Cm(3.5)) < Cm(0.01) and abs(s0.right_margin - Cm(2.0)) < Cm(0.01)
    assert abs(s0.top_margin - Cm(3.0)) < Cm(0.01) and abs(s0.bottom_margin - Cm(3.0)) < Cm(0.01)
    with zipfile.ZipFile(p) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        settings = z.read("word/settings.xml").decode("utf-8")
    assert re.search(r'<w:pgNumType w:fmt="lowerRoman" w:start="1"/>', xml)
    assert re.search(r'<w:pgNumType w:fmt="decimal" w:start="1"/>', xml)
    assert "TOC \\o" in xml and "<w:updateFields" in settings
    # thứ tự lược đồ: pgNumType trước cols/docGrid trong sectPr; tblBorders trước tblLook trong tblPr
    for sect in re.findall(r"<w:sectPr\b.*?</w:sectPr>", xml, re.S):
        if "pgNumType" in sect and "docGrid" in sect:
            assert sect.index("pgNumType") < sect.index("docGrid")
    vien = re.findall(r"<w:tblPr>.*?</w:tblPr>", xml, re.S)
    khong_vien = [t for t in vien if 'w:top w:val="nil"' in t]
    assert khong_vien, "danh mục chữ viết tắt/bảng biểu phải là bảng không viền"
    for t in khong_vien:
        if "tblLook" in t:
            assert t.index("tblBorders") < t.index("tblLook")
    # cỡ chữ thân 14pt, giãn dòng 1,5 ở một đoạn thân bài
    doan = next(q for q in d.paragraphs if q.text.startswith("Thời gian chờ là điểm yếu"))
    assert doan.paragraph_format.line_spacing == pytest.approx(1.5)
    assert any(r.font.size == Pt(14) for r in doan.runs)


def test_md2docx_thu_tu_luoc_do_chung(tmp_path):
    """Lỗi có sẵn từ trước của md2docx (đo bằng bộ xác thực OOXML 21/11): zoom thiếu w:percent, shd thiếu w:val,
    tcMar/shd/ind nối sai chỗ — sửa cho MỌI bản Word, không riêng khuôn."""
    pytest.importorskip("docx")
    import md2docx_vn as M

    md = "# TIÊU ĐỀ\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n> Ghi chú thụt lề.\n"
    p = M.markdown_to_docx(md, tmp_path / "thu.docx")
    with zipfile.ZipFile(p) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        settings = z.read("word/settings.xml").decode("utf-8")
    z = re.search(r"<w:zoom\b[^>]*/>", settings)
    assert z is None or "w:percent=" in z.group(0)
    for shd in re.findall(r"<w:shd\b[^>]*/>", xml):
        assert "w:val=" in shd
    for tc in re.findall(r"<w:tcPr>.*?</w:tcPr>", xml, re.S):
        if "w:tcMar" in tc and "w:vAlign" in tc:
            assert tc.index("w:tcMar") < tc.index("w:vAlign")
        if "w:shd" in tc and "w:tcMar" in tc:
            assert tc.index("w:shd") < tc.index("w:tcMar")
    for ppr in re.findall(r"<w:pPr>.*?</w:pPr>", xml, re.S):
        if "<w:ind " in ppr and "<w:jc " in ppr:
            assert ppr.index("<w:ind ") < ppr.index("<w:jc ")


# ── công cụ đọc đề cương hiểu «CHƯƠNG n.» ───────────────────────────────────────────────────────────────────────────

def test_khung_bieu_bang_nhan_chuong_khuon_va_bo_qua_bang_han_che(ket):
    md = ket.md.replace("Một khoa duy nhất.", "**Bảng 3.2. Hạn chế dự kiến**\n\n| Hạn chế | Hướng |\n|---|---|\n"
                                                "| Một khoa; một thời điểm | Giảm |")
    ch, bd = KBB._chuong_du_kien(md)
    assert ch[0] == "# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN" and bd > 0
    khung, _ = KBB._chuong_du_kien(md, chi_khung=True)
    assert not any("Dự kiến bàn luận" in x for x in khung)
    loi = KBB.kiem_bieu_bang(md, "", 1)
    assert not any("Bảng 3.2" in x for x in loi), loi  # bảng hạn chế không chấm như bảng kết quả


def test_thay_chuong_giu_de_muc_va_phan_ban_luan(ket):
    moi = ["# 5. DỰ KIẾN KẾT QUẢ", "", "## 5.1. Khung mới", "", "**Bảng 5.1. Bảng mới (Mục tiêu 1)**", "",
           "| A | B |", "|---|---|", "| x | y |"]
    md = KBB.thay_chuong(ket.md, moi)
    ch, _ = KBB._chuong_du_kien(md)
    assert ch[0] == "# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN"
    h = [x for x in ch if x.startswith("##")]
    assert h == ["## 3.1. Khung mới", "## 3.2. Dự kiến bàn luận", "### 3.2.1. Bàn luận theo mục tiêu 1",
                 "### 3.2.2. Bàn luận theo mục tiêu 2", "## 3.3. Hạn chế của nghiên cứu"]
    assert "**Bảng 3.1. Bảng mới (Mục tiêu 1)**" in ch


def test_ho_so_hdd_tro_chuong_cho_de_cuong_khuon(ket):
    assert HDD._so_muc_de_cuong(ket.md, "TỔNG QUAN TÀI LIỆU") == "Chương 1"
    assert HDD._so_muc_de_cuong(DE_CUONG_CU, "TỔNG QUAN TÀI LIỆU") == "mục 3"


def test_phan_bien_may_khong_ap_luat_thu_tu_vancouver_cho_khuon(ket):
    assert not any("Vancouver" in x["van_de"] for x in PB.kiem_trich_dan_tat_dinh(ket.md))
    # cấu trúc cũ: trích [3] trước [1] ⇒ vẫn báo
    assert any("Vancouver" in x["van_de"] for x in PB.kiem_trich_dan_tat_dinh(DE_CUONG_CU))


def test_ho_so_dtcs_doc_duoc_muc_tieu_de_cuong_khuon(ket):
    """`ho_so_dtcs_bvqy175` (PR #379) tìm mục tiêu ở chương cấp 1 «MỤC TIÊU» — khuôn đặt mục tiêu thành mục con cuối
    đặt vấn đề ⇒ mục 13/17 của thuyết minh thành «[CẦN BỔ SUNG]» (đo C1a/BTM 21/11)."""
    dong, ds = DT.tach_muc(ket.md)
    md, ds_mt, nguon = DT.muc_tieu(dong, ds)
    assert ds_mt == ["Xác định tỷ lệ hài lòng tại khoa mẫu.", "Phân tích yếu tố liên quan."]
    assert not any("***" in x or x == "---" for x in md)
    assert "cuối đặt vấn đề" in nguon
    dong, ds = DT.tach_muc(DE_CUONG_CU)  # cấu trúc cũ giữ nguyên hành vi
    _md, ds_mt, nguon = DT.muc_tieu(dong, ds)
    assert ds_mt == ["Xác định tỷ lệ hài lòng tại khoa mẫu.", "Phân tích yếu tố liên quan."]
    assert nguon == "đề cương nộp mục 2.1"


def test_khuon_tu_trich_thong_tin_co_ban():
    cac_muc = GB.doc_muc(DE_CUONG_CU.splitlines())
    tt = K.trich_thong_tin(DE_CUONG_CU.splitlines(), cac_muc)
    assert tt.ten_de_tai == "Khảo sát thử tại Khoa Mẫu" and tt.chu_nhiem.startswith("BS. Người Thử")
    assert tt.muc_tieu == ["Xác định tỷ lệ hài lòng tại khoa mẫu.", "Phân tích yếu tố liên quan."]
    assert tt.vai_tro == ["Chủ nhiệm đề tài"]
    # chương «MỤC TIÊU NGHIÊN CỨU» không có mục «Mục tiêu»: chỉ lấy thân trước mục con (không đếm H₀/H₁)
    md = DE_CUONG_CU.replace("## 2.1. Mục tiêu\n\n", "").replace(
        "## 2.2. Câu hỏi nghiên cứu\n\nTỷ lệ hài lòng tại khoa mẫu là bao nhiêu?",
        "## 2.2. Giả thuyết nghiên cứu\n\n1. H₀: tỷ số chênh bằng 1.")
    tt2 = K.trich_thong_tin(md.splitlines(), GB.doc_muc(md.splitlines()))
    assert tt2.muc_tieu == ["Xác định tỷ lệ hài lòng tại khoa mẫu.", "Phân tích yếu tố liên quan."]


def test_goi_bao_ve_tren_de_cuong_khuon(ket, tmp_path):
    slides, ten = GB.dung_slide(ket.md.splitlines(), tmp_path)
    assert ten == "Khảo sát thử tại Khoa Mẫu"
    dvd = next(s for s in slides if s.khoa == "dat_van_de")
    van = [c.van for _n, ds in dvd.khoi for c in ds]
    assert not any("“**" in v or "Xác định tỷ lệ" in v for v in van)  # không lấn sang mục tiêu / câu chuyển ý
    md_slide = GB.render_slide(slides, ten, "x.md", 10, "0" * 64)
    assert "- Xác định tỷ lệ hài lòng tại khoa mẫu." in md_slide and "***" not in md_slide
    assert "do chủ nhiệm bổ sung: ………" not in md_slide  # câu chừa dòng chấm chưa phải nội dung
    dk = next(s for s in slides if s.khoa == "du_kien")
    assert any(n == "Dự kiến bàn luận" for n, _ds in dk.khoi)
    # cấu trúc cũ không có «Dự kiến bàn luận» ⇒ bỏ qua, không cảnh báo
    cu, _ = GB.dung_slide(DE_CUONG_CU.splitlines(), tmp_path)
    assert not any("Dự kiến bàn luận" in c for s in cu for c in s.canh_bao)


@pytest.mark.parametrize("chat_van, so", [
    ("Cỡ mẫu chưa tính hiệu ứng thiết kế và hồi quy chưa hiệu chỉnh nhiễu.", "2"),
    ("Trích dẫn [12] không có trong danh mục tài liệu tham khảo.", "4"),
    ("Khoảng trống nghiên cứu và tính mới chưa nêu rõ.", "1"),
    ("Khung bảng dự kiến kết quả thiếu biểu đồ.", "3"),
    ("Phiếu đồng ý có ký tên là bản ghi định danh duy nhất.", "5"),
])
def test_tieu_chi_phieu_nhan_xet(chat_van, so):
    ch = GB.CauHoi("A1", "A", "", chat_van, "nguồn")
    assert GB.tieu_chi_phieu(ch)[0] == so


def test_sinh_de_cuong_mac_dinh_khuon_cho_ma_bvqy175():
    assert SINH.dung_khuon("de-tai-x-BVQY175") is True
    assert SINH.dung_khuon("de-tai-x") is False
    assert SINH.dung_khuon("de-tai-x-BVQY175", False) is False
    assert SINH.dung_khuon("de-tai-x", True) is True


def test_truc_trinh_bay_nhan_14pt_cho_de_cuong_khuon(ket, tmp_path):
    """Trục ④ của bộ đo hệ nghiên cứu chỉ nhận thân 13pt — đề cương khuôn 14pt (bác sĩ chọn theo mẫu) bị báo «sai chuẩn
    trình bày» và bị gợi ý xuất lại 13pt (đo C1a/BTM 21/11). Đề cương cấu trúc cũ vẫn chỉ được 13pt."""
    pytest.importorskip("docx")
    import kiem_chi_tiet_he_nghien_cuu as KCT
    import xuat_docx_chuan as XDC

    md_p = tmp_path / "DE_CUONG_NOP_HOI_DONG_x.md"
    md_p.write_text(ket.md, encoding="utf-8", newline="\n")
    assert 14 in KCT._co_than_cho_phep(md_p.name, md_p)
    docx_p = XDC.render_mot_file(md_p)  # xuất lại theo bộ xuất chuẩn ⇒ vẫn đúng khuôn
    assert KCT.kiem_docx(docx_p)["co_than_uu_the"] == 14.0
    assert KCT.danh_gia_docx(md_p, docx_p)[0][0] == KCT.XANH
    md_p.write_text(DE_CUONG_CU, encoding="utf-8", newline="\n")
    assert KCT._co_than_cho_phep(md_p.name, md_p) == {13}


def test_nhat_quan_khong_doi_thu_tu_vancouver_voi_de_cuong_khuon(ket, tmp_path):
    """Trục `trich_dan_tong_quan` báo 🟡 «thứ tự trích lần đầu không theo Vancouver» trên đề cương khuôn BTM (đo
    21/11) — khuôn xếp TLTK theo ngôn ngữ rồi ABC; cấu trúc cũ vẫn bị kiểm."""
    import nhat_quan_xuyen_cong as NQ

    ma = "de-tai-khuon-nq"
    d = tmp_path / ma
    d.mkdir()
    p = d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md"
    p.write_text(ket.md, encoding="utf-8", newline="\n")
    k = NQ._truc_trich_dan(d, ma, {})
    assert "Vancouver" not in str(k)
    p.write_text(DE_CUONG_CU, encoding="utf-8", newline="\n")
    assert "Vancouver" in str(NQ._truc_trich_dan(d, ma, {}))


def test_ho_so_dtcs_nguon_tro_phu_luc_khi_de_muc_khong_danh_so(ket):
    """Khuôn đặt kế hoạch thực hiện thành phụ lục, mục con không đánh số ⇒ nguồn từng ghi «đề cương nộp mục » rỗng."""
    _dong, ds = DT.tach_muc(ket.md)
    nl = next(h for h in ds if h["ten"].startswith("Nhân lực"))
    assert DT._muc_dc(nl, ds) == "Phụ lục C, mục «Nhân lực và phân công nhiệm vụ»"
    dt = next(h for h in ds if h["ten"] == "Đối tượng nghiên cứu")
    assert DT._muc_dc(dt, ds) == "mục 2.1"
