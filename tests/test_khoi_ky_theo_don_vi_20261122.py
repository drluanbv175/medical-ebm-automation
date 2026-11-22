"""Khối ký bìa phụ theo đơn vị thật · tham chiếu «chương N» sau khi chuyển khuôn · chốt K19 (22/11/2026).

Chốt cuối `tham-dinh-dau-ra` trên đề cương nộp C1a bắt hai lỗi mà K1–K17 bỏ sót, cùng gốc ở bộ chuyển khuôn
`tools/khuon_de_cuong_bvqy175.py`:
  1. Phụ lục A ghi «| Khung bảng kết quả | Theo chương 5 |» — số chương của cấu trúc cũ («5. DỰ KIẾN KẾT QUẢ»); khuôn
     chỉ có Chương 1–3, khung bảng nằm ở Chương 3. Bộ chuyển đổi số «mục», «Bảng» nhưng bỏ sót «chương».
  2. Bìa phụ luôn có «VIỆN TRƯỞNG — (Họ tên và chữ ký — nếu Khoa trực thuộc Viện)»: chép nguyên lời hướng dẫn của khuôn,
     sai đơn vị thật (Khoa C1a thuộc Trung tâm C1; Khoa Khám bệnh của BTM trực thuộc bệnh viện).

Fixture tự soạn, ngoại tuyến, không dữ liệu thật (repo công khai)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import khuon_de_cuong_bvqy175 as K  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402

from tests.test_khuon_de_cuong_bvqy175_20261121 import DE_CUONG_CU  # noqa: E402

DV_TRUNG_TAM = "Khoa Khám Thử C9, Trung tâm Khám Thử T9, Bệnh viện Mẫu 175"
DV_VIEN = "Khoa Khám Thử C9, Viện Thử Nghiệm V9, Bệnh viện Mẫu 175"
DV_TRUC_THUOC = "Khoa Khám Thử C9, Bệnh viện Mẫu 175"
HUONG_DAN_CU = "(Họ tên và chữ ký — nếu Khoa trực thuộc Viện)"


def _cu(don_vi: str = DV_TRUC_THUOC, them_chuong: bool = True) -> str:
    """Đề cương cấu trúc cũ của bộ test khuôn, đổi đơn vị chủ trì; kèm hai tham chiếu chương kiểu C1a viết tay."""
    md = DE_CUONG_CU.replace("| Đơn vị chủ trì | Khoa Mẫu, Bệnh viện Mẫu 175 |", f"| Đơn vị chủ trì | {don_vi} |")
    if them_chuong:
        md = md.replace("# PHỤ LỤC A. PHIẾU KHẢO SÁT\n\nPhiếu giả.",
                        "# PHỤ LỤC A. PHIẾU KHẢO SÁT\n\nPhiếu giả.\n\n| Hạng mục | Nội dung |\n|---|---|\n"
                        "| Khung bảng kết quả | Theo chương 5 |")
        md = md.replace("Phân tích mô tả.", "Phân tích mô tả; các bảng trình bày ở chương 5, cách đo ở chương 4.")
    return md


def _bia_phu(md: str) -> str:
    return md.split("# DANH SÁCH CÁC CÁN BỘ")[0].split("\n---\n")[1]


def _ban_loi_21_11(md_khuon: str) -> str:
    """Tái tạo đầu ra của bộ chuyển ngày 21/11: khối Viện trưởng kèm lời hướng dẫn, «Theo chương 5» chưa đổi."""
    bp = "**CHỦ NHIỆM KHOA**\n\n(Họ tên và chữ ký)\n\n"
    i = md_khuon.index(bp, md_khuon.index("\n---\n")) + len(bp)
    md = md_khuon[:i] + f"**VIỆN TRƯỞNG**\n\n{HUONG_DAN_CU}\n\n" + md_khuon[i:]
    md = md.replace("**GIÁM ĐỐC TRUNG TÂM**\n\n(Họ tên và chữ ký)\n\n", "")
    return md.replace("| Khung bảng kết quả | Theo Chương 3 |", "| Khung bảng kết quả | Theo chương 5 |")


# ── đọc đơn vị ngay trên Khoa ────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("nguon, mong", [
    ((DV_TRUNG_TAM,), ("trung_tam", "Trung tâm Khám Thử T9")),
    ((DV_VIEN,), ("vien", "Viện Thử Nghiệm V9")),
    ((DV_TRUC_THUOC,), ("truc_thuoc", "")),
    (("Khoa Nội, Học viện Mẫu",), ("truc_thuoc", "")),  # «Học viện», «Bệnh viện» không phải Viện
    (("**BỘ QUỐC PHÒNG**\n**BỆNH VIỆN QUÂN Y MẪU**\n**TRUNG TÂM KHÁM THỬ T9**\n**KHOA KHÁM THỬ C9**",),
     ("trung_tam", "TRUNG TÂM KHÁM THỬ T9")),
    (("", "………", "[CẦN CHỦ NHIỆM ẤN ĐỊNH]", None), ("khong_ro", "")),
    # chỉ đọc nguồn ĐẦU TIÊN có tên đơn vị (hồ sơ thắng đề cương)
    ((DV_TRUC_THUOC, DV_VIEN), ("truc_thuoc", "")),
    (("Thành phố Hồ Chí Minh", DV_VIEN), ("vien", "Viện Thử Nghiệm V9")),
])
def test_don_vi_cap_tren(nguon, mong):
    assert K.don_vi_cap_tren(*nguon) == mong


def test_don_vi_ho_so_bo_o_cho_dien():
    assert K.don_vi_ho_so({"administrative": {"pi_unit": DV_VIEN}}) == DV_VIEN
    for v in ("[PII — điền ở bản nộp ngoài hệ thống]", "………", "", None):
        assert K.don_vi_ho_so({"administrative": {"pi_unit": v}}) == ""
    assert K.don_vi_ho_so({}) == "" and K.don_vi_ho_so(None) == ""


# ── khối ký bìa phụ khi chuyển khuôn ─────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("don_vi, co, khong", [
    (DV_TRUNG_TAM, "**GIÁM ĐỐC TRUNG TÂM**", "**VIỆN TRƯỞNG**"),
    (DV_VIEN, "**VIỆN TRƯỞNG**", "**GIÁM ĐỐC TRUNG TÂM**"),
    (DV_TRUC_THUOC, None, ("**VIỆN TRƯỞNG**", "**GIÁM ĐỐC TRUNG TÂM**")),
])
def test_khoi_ky_bia_phu_theo_don_vi_that(don_vi, co, khong):
    kq = K.chuyen(_cu(don_vi), nam=2026)
    bp = _bia_phu(kq.md)
    assert "**CHỦ NHIỆM ĐỀ TÀI**\n\n(Họ tên và chữ ký)\n\n**CHỦ NHIỆM KHOA**\n\n(Họ tên và chữ ký)" in bp
    if co:
        assert f"{co}\n\n(Họ tên và chữ ký)\n\n**THÀNH PHỐ HỒ CHÍ MINH, 2026**" in bp
    for x in (khong if isinstance(khong, tuple) else (khong,)):
        assert x not in kq.md
    assert "nếu" not in bp and "—" not in bp  # không lời hướng dẫn của khuôn
    assert not [x for x in KDN.loi_k19(kq.md) if "bìa phụ" in x or "hướng dẫn" in x]
    assert KDN.loi_k14(kq.md) == []


def test_don_vi_trong_ho_so_thang_don_vi_ghi_trong_de_cuong():
    kq = K.chuyen(_cu(DV_TRUC_THUOC), nam=2026, don_vi=DV_VIEN)
    assert "**VIỆN TRƯỞNG**" in _bia_phu(kq.md)
    assert any("Viện trưởng (Khoa thuộc «Viện Thử Nghiệm V9»)" in x for x in kq.bao_cao)


def test_khong_doc_duoc_don_vi_khong_khang_dinh_vien():
    md = _cu().replace("| Đơn vị chủ trì | Khoa Khám Thử C9, Bệnh viện Mẫu 175 |\n", "")
    md = md.replace("**BỘ QUỐC PHÒNG**\n**BỆNH VIỆN MẪU 175**\n", "")
    md = md.replace("| Chủ nhiệm đề tài | BS. Người Thử – Khoa Mẫu, Bệnh viện Mẫu 175 |",
                    "| Chủ nhiệm đề tài | BS. Người Thử |")
    kq = K.chuyen(md, nam=2026)
    bp = _bia_phu(kq.md)
    assert "**VIỆN TRƯỞNG**" not in bp and "nếu" not in bp
    assert any("không khai đơn vị" in x for x in kq.canh_bao)


# ── tham chiếu «chương N» của bản cũ ─────────────────────────────────────────────────────────────────────────────────

def test_chuyen_doi_tham_chieu_chuong_cu_sang_chuong_moi():
    md = K.chuyen(_cu(DV_TRUNG_TAM), nam=2026).md
    # «5. DỰ KIẾN KẾT QUẢ» ⇒ Chương 3; «4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP» ⇒ Chương 2
    assert "| Khung bảng kết quả | Theo Chương 3 |" in md
    assert "các bảng trình bày ở Chương 3, cách đo ở Chương 2." in md
    assert not re.search(r"(?i)chương [4-9]", md)
    # đề mục cấp 1 do khuôn dựng mang số MỚI — không bị đổi lần hai
    h1 = [d for d in md.splitlines() if d.startswith("# CHƯƠNG")]
    assert h1 == ["# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU", "# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU",
                  "# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN"]
    assert "- CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN" in md  # mục lục
    assert "đã tổng quan ở Chương 1" in md  # khung bàn luận chèn sau khi đánh số
    assert not [x for x in KDN.loi_k19(md) if "chương" in x]


def test_chuong_khong_co_trong_ban_cu_giu_nguyen_de_k19_bat():
    md = K.chuyen(_cu().replace("cách đo ở chương 4", "cách đo ở chương 9"), nam=2026).md
    assert "chương 9" in md
    assert any("«chương 9» trỏ tới chương không có" in x for x in KDN.loi_k19(md))


# ── văn bản ĐÃ theo khuôn (bản lỗi 21/11, người đã sửa tiếp) ─────────────────────────────────────────────────────────

def test_sua_ban_da_theo_khuon_chi_sua_hai_loi():
    dung = K.chuyen(_cu(DV_TRUNG_TAM), nam=2026).md
    loi = _ban_loi_21_11(dung)
    assert loi != dung and HUONG_DAN_CU in loi
    kq = K.chuyen(loi)
    assert kq.da_theo_khuon and kq.md == dung
    assert any("khối ký bìa phụ" in x for x in kq.bao_cao)
    assert any("«chương 5»" in x and "Chương 3" in x for x in kq.bao_cao)
    # lần hai không đổi gì
    lai = K.chuyen(kq.md)
    assert lai.md == kq.md and lai.bao_cao == ["văn bản đã theo khuôn — không chuyển lại"]


def test_sua_ban_da_theo_khuon_giu_ho_ten_da_dien_va_bo_khoi_sai_don_vi():
    dung = K.chuyen(_cu(DV_TRUC_THUOC), nam=2026).md
    loi = _ban_loi_21_11(dung)
    bp_cu = _bia_phu(loi)
    co_ten = loi.replace(bp_cu, bp_cu.replace("**CHỦ NHIỆM ĐỀ TÀI**\n\n(Họ tên và chữ ký)",
                                              "**CHỦ NHIỆM ĐỀ TÀI**\n\nBS. Người Thử"))
    kq = K.chuyen(co_ten)
    bp = _bia_phu(kq.md)
    assert "**CHỦ NHIỆM ĐỀ TÀI**\n\nBS. Người Thử" in bp
    assert "**VIỆN TRƯỞNG**" not in bp and "nếu" not in bp
    assert "(Họ tên và chữ ký)\n\n**THÀNH PHỐ HỒ CHÍ MINH, 2026**" in bp


def test_sua_ban_da_theo_khuon_them_khoi_thieu():
    dung = K.chuyen(_cu(DV_VIEN), nam=2026).md
    thieu = dung.replace("**VIỆN TRƯỞNG**\n\n(Họ tên và chữ ký)\n\n", "")
    assert any("thiếu khối ký «VIỆN TRƯỞNG»" in x for x in KDN.loi_k19(thieu))
    assert K.chuyen(thieu).md == dung


def test_tham_chieu_chuong_lac_ngoai_khung_bang_chi_canh_bao():
    dung = K.chuyen(_cu(DV_TRUC_THUOC), nam=2026).md
    lac = dung.replace("cách đo ở Chương 2", "cách đo ở chương 4")
    kq = K.chuyen(lac)
    assert kq.md == lac  # không đoán chương đích khi câu không nói về khung bảng
    assert any("«chương 4» trỏ tới chương không có" in x for x in kq.canh_bao)


def test_chay_ghi_ban_da_theo_khuon_co_sao_luu(tmp_path):
    ma = "de-tai-ky-thu-BVQY175"
    d = tmp_path / ma
    d.mkdir()
    (d / "study_meta.json").write_text(json.dumps({"administrative": {"pi_unit": DV_TRUNG_TAM}}, ensure_ascii=False),
                                       encoding="utf-8", newline="\n")
    loi = _ban_loi_21_11(K.chuyen(_cu(DV_TRUNG_TAM), nam=2026).md)
    p = d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md"
    p.write_text(loi, encoding="utf-8", newline="\n")
    kho = K.chay(ma, d, ghi=False)
    assert kho["doi"] and not kho["da_ghi"] and p.read_text(encoding="utf-8") == loi
    pytest.importorskip("docx")
    that = K.chay(ma, d, ghi=True)
    moi = p.read_text(encoding="utf-8")
    assert that["da_ghi"] and "**GIÁM ĐỐC TRUNG TÂM**" in moi and HUONG_DAN_CU not in moi
    assert "| Khung bảng kết quả | Theo Chương 3 |" in moi
    sao = list((d / "_sao_luu_de_cuong").glob("*.truoc-sua-khuon-*.md"))
    assert len(sao) == 1 and sao[0].read_text(encoding="utf-8") == loi
    assert not [x for x in that["loi_kiem"] if x.startswith("K19")]
    assert K.chay(ma, d, ghi=True)["da_ghi"] is False  # lần hai: không có gì để ghi


# ── K19 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_k19_bat_ban_loi_21_11():
    loi = KDN.loi_k19(_ban_loi_21_11(K.chuyen(_cu(DV_TRUNG_TAM), nam=2026).md))
    assert any("còn lời hướng dẫn của khuôn «(Họ tên và chữ ký — nếu Khoa trực thuộc Viện)»" in x for x in loi)
    assert any("«chương 5» trỏ tới chương không có (văn bản có chương 1, 2, 3)" in x for x in loi)
    assert any("có khối ký «VIỆN TRƯỞNG» nhưng hồ sơ khai Khoa thuộc «Trung tâm Khám Thử T9»" in x for x in loi)
    assert any("thiếu khối ký «GIÁM ĐỐC TRUNG TÂM»" in x for x in loi)


def test_k19_don_vi_tu_ho_so_thang_de_cuong():
    md = K.chuyen(_cu(DV_TRUC_THUOC), nam=2026).md
    assert not [x for x in KDN.loi_k19(md) if "bìa phụ" in x]
    assert any("thiếu khối ký «VIỆN TRƯỞNG»" in x for x in KDN.loi_k19(md, DV_VIEN))


def test_k19_khung_bang_tro_sai_chuong_co_that():
    md = K.chuyen(_cu(DV_TRUC_THUOC), nam=2026).md.replace("Theo Chương 3 |", "Theo Chương 2 |")
    assert any("khung bảng kết quả nằm ở chương 3, không phải «Chương 2»" in x for x in KDN.loi_k19(md))


def test_k19_cau_truc_cu_va_cac_cach_viet_hop_le():
    md = _cu()
    # cấu trúc cũ: «chương 5», «chương 4» trỏ đúng «# 5. DỰ KIẾN KẾT QUẢ», «# 4. ĐỐI TƯỢNG…» ⇒ không lỗi
    assert KDN.loi_k19(md) == []
    hop_le = md.replace("Phân tích mô tả;",
                        "Biến cố bất lợi (nếu có) được ghi nhận; chương trình 5 năm; Phân tích mô tả;")
    hop_le = hop_le.replace("4. Adams P. Cross-sectional designs.",
                            "4. Adams P. Cross-sectional designs (chương 12 — nếu cần).")
    assert KDN.loi_k19(hop_le) == []  # «(nếu có)» trong văn xuôi, «chương trình», danh mục TLTK: không bắt
    assert any("«chương 9» trỏ tới chương không có" in x for x in KDN.loi_k19(md.replace("chương 4", "chương 9")))


def test_kiem_goi_k19_va_doc_don_vi_tu_study_meta(tmp_path):
    ma = "de-tai-k19-thu"
    d = tmp_path / ma
    d.mkdir()
    md = K.chuyen(_cu(DV_TRUC_THUOC), nam=2026).md
    (d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md").write_text(md, encoding="utf-8", newline="\n")
    assert not [x for x in KDN.kiem(d, ma) if x.startswith("K19")]
    (d / "study_meta.json").write_text(json.dumps({"administrative": {"pi_unit": DV_VIEN}}, ensure_ascii=False),
                                       encoding="utf-8", newline="\n")
    assert any(x.startswith("K19 bìa phụ thiếu khối ký «VIỆN TRƯỞNG»") for x in KDN.kiem(d, ma))


# ── bộ sinh đề cương nộp truyền đơn vị của hồ sơ cho khuôn ───────────────────────────────────────────────────────────

def test_sinh_de_cuong_khuon_dung_don_vi_trong_ho_so(tmp_path):
    from tests.test_sinh_de_cuong_nop_hoi_dong_20261116 import _de_tai  # noqa: PLC0415

    d = _de_tai(tmp_path)
    p = d / "study_meta.json"
    meta = json.loads(p.read_text(encoding="utf-8"))
    meta["administrative"]["pi_unit"] = DV_TRUNG_TAM
    p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    kq = SDC.sinh(d, d.name, ghi=False, khuon=True)
    assert any("Giám đốc Trung tâm (Khoa thuộc «Trung tâm Khám Thử T9»)" in x for x in kq["khuon_bvqy175"])
