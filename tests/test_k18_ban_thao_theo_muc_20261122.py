# -*- coding: utf-8 -*-
"""K18 — đối chiếu BẢN THẢO bài báo với từng mục chuẩn báo cáo (22/11/2026).

Bác sĩ 21–22/11/2026: mọi khâu tới «Viết báo cáo & công bố kết quả» phải đạt từng mục chuẩn quốc tế và Việt Nam, cho mọi
thiết kế; «những gì không đạt chuẩn sẽ phải được loại bỏ». Mỗi test dưới đây khoá một hành vi đã đo trên bản thảo thật
(BTM, bài báo giao thức C1a) hoặc 8 bản thảo G7 giả lập — kể cả các ca BÁO NHẦM đã sửa (để không quay lại).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import chuan_bao_cao_items as CBC  # noqa: E402
import kiem_ban_thao_tap_chi as KB  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402

CO_SO = {
    "tom_tat": ("## TÓM TẮT\n\n**Mục tiêu:** Mô tả tỷ lệ kiểm soát huyết áp và phân tích yếu tố liên quan.\n\n"
                "**Phương pháp:** Nghiên cứu cắt ngang trên 400 người tăng huyết áp tại Bệnh viện A năm 2026.\n\n"
                "**Kết quả:** Tỷ lệ kiểm soát là 48,6% (KTC 95% 43,9–53,3%).\n\n"
                "**Kết luận:** Khoảng một nửa người bệnh đạt kiểm soát.\n"),
    "dat_van_de": ("## 1. ĐẶT VẤN ĐỀ\n\nTăng huyết áp là gánh nặng lớn [1]. Chưa có số liệu tại cơ sở. Nghiên cứu "
                   "nhằm: (1) mô tả tỷ lệ kiểm soát huyết áp; (2) phân tích yếu tố liên quan với kiểm soát "
                   "huyết áp.\n"),
    "phuong_phap": ("## 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n*Thiết kế:* cắt ngang mô tả có phân tích, thu thập "
                    "tại một thời điểm.\n\n*Đối tượng:* Người bệnh từ 18 tuổi; loại trừ người mang thai. Chọn mẫu "
                    "liên tiếp.\n\n*Phân tích:* hồi quy Poisson, phân tích thăm dò.\n"),
    "ket_qua": ("## 3. KẾT QUẢ\n\nTrong 450 người được mời, 400 người tham gia và được phân tích; 50 người bị loại "
                "vì từ chối.\n\n**Bảng 1. Đặc điểm chung của đối tượng**\n\n| Đặc điểm | n (%) |\n|---|---|\n"
                "| Nam | 120 (30,0) |\n"),
    "ban_luan": ("## 4. BÀN LUẬN\n\nNghiên cứu cho thấy tỷ lệ kiểm soát là 48,6%, tương tự nghiên cứu trước [2]. "
                 "Hạn chế: thiết kế cắt ngang không xác lập trình tự thời gian; một cơ sở nên khó suy rộng.\n"),
    "ket_luan": "## 5. KẾT LUẬN\n\nKhoảng một nửa người bệnh đạt kiểm soát.\n",
    "tltk": "## TÀI LIỆU THAM KHẢO\n\n[1] A. A cohort study of something. 2024.\n\n[2] B. Bài 2. 2025.\n",
}


def _bt(**thay) -> str:
    phan = dict(CO_SO, **thay)
    return "# YẾU TỐ LIÊN QUAN KIỂM SOÁT HUYẾT ÁP\n\n" + "\n".join(phan[k] for k in CO_SO if phan.get(k))


def _kq(md: str, tk: str = "cross_sectional", co_so_lieu=None, che_do: str = "ban_thao"):
    return K.doi_chieu(md, tk, che_do=che_do, co_so_lieu=co_so_lieu)


def _muc(kq, chuan: str, ma: str):
    ra = [r for r in kq["ket_qua"] if r.chuan == chuan and r.ma == ma]
    assert ra, f"không thấy {chuan} {ma}"
    return ra[0]


# ───────────────────────────── kho nguyên văn CONSORT 2025 ─────────────────────────────
def test_consort_2025_nguyen_van_cc_by_du_42_muc_khop_bang_tieu_chi():
    assert CBC.GIAY_PHEP["CONSORT"] == "creativecommons.org/licenses/by/4.0"
    ma = [r[0] for r in CBC.CONSORT_2025_ITEMS]
    assert len(ma) == 42 and ma[0] == "1a" and ma[-1] == "30"
    assert set(ma) == set(TB._CONSORT)
    muc26 = dict((r[0], r[3]) for r in CBC.CONSORT_2025_ITEMS)["26"]
    assert " • the number of participants included in the analysis" in muc26  # gạch đầu dòng không dính chữ


def test_rct_dung_consort_2025_thay_spirit_tong_quan_dung_prisma_2020_theo_muc():
    kq = _kq(_bt(), "rct")
    assert any(c == "CONSORT 2025" for c, _ in kq["chuan"]) and not any(c == "SPIRIT 2025" for c, _ in kq["chuan"])
    # 22/11/2026: PRISMA 2020 có tiêu chí theo mục (tests/test_k18_prisma_2020_20261122.py) — không còn ⚪ cả chuẩn
    kq_sr = _kq(_bt(), "systematic_review")
    assert not kq_sr["chua_do"] and [c for c, _ in kq_sr["chuan"]] == ["PRISMA 2020"]
    assert len([r for r in kq_sr["ket_qua"] if r.chuan == "PRISMA 2020"]) == 42


# ───────────────────────────── tách chương IMRAD ─────────────────────────────
def test_ten_bai_bat_dau_bang_ket_qua_khong_bi_nhan_la_chuong():
    md = _bt().replace("# YẾU TỐ LIÊN QUAN KIỂM SOÁT HUYẾT ÁP", "# KẾT QUẢ ĐIỀU TRỊ TĂNG HUYẾT ÁP NGOẠI TRÚ")
    bt = TB.tach_ban_thao(md)
    assert bt.cap_chuong == 2 and [p.tieu_de for p in bt.chuong["ket_qua"]] == ["3. KẾT QUẢ"]
    assert bt.tieu_de and "ĐIỀU TRỊ" in bt.tieu_de[0].van


def test_tltk_va_phu_luc_bang_kiem_bi_xoa_trang_khong_lam_bang_chung():
    """Tên bài «A cohort study» trong TLTK và chữ của bảng kiểm STROBE ở phụ lục không được làm STROBE 1a đạt."""
    md = _bt(tom_tat=CO_SO["tom_tat"].replace("Nghiên cứu cắt ngang", "Nghiên cứu"))
    md = md.replace("# YẾU TỐ LIÊN QUAN", "# YẾU TỐ")
    md += "\n## PHỤ LỤC — CHECKLIST STROBE 2007\n\n| 1a | Thiết kế cắt ngang nêu ở tiêu đề | ☑ |\n"
    assert _muc(_kq(md), "STROBE 2007", "1a").trang_thai == "thieu"
    assert _muc(_kq(_bt()), "STROBE 2007", "1a").trang_thai == "dat"
    # mục có phần «phụ lục» (CROSS 5d) không được lấy bằng chứng từ chính bảng kiểm tác giả tự đánh dấu
    pp = CO_SO["phuong_phap"] + "\nNgười bệnh tự điền phiếu khảo sát tại khu vực chờ.\n"
    md_ks = _bt(phuong_phap=pp) + ("\n## PHỤ LỤC — CHECKLIST CROSS 2021\n\n| 5d | Bộ câu hỏi đầy đủ ở phụ lục kèm theo "
                                   "| ☑ |\n")
    assert _muc(_kq(md_ks, co_so_lieu=True), "CROSS 2021", "5d").trang_thai == "thieu"
    md_pl = _bt(phuong_phap=pp) + "\n## PHỤ LỤC 1. BỘ CÂU HỎI\n\nBộ câu hỏi đầy đủ ở phụ lục này gồm 30 câu.\n"
    assert _muc(_kq(md_pl, co_so_lieu=True), "CROSS 2021", "5d").trang_thai == "dat"


def test_cau_truc_thieu_chuong_bi_bao():
    kq = _kq(_bt(ban_luan=""), co_so_lieu=True)
    assert any("Bàn luận" in x for x in kq["cau_truc"])
    assert not _kq(_bt(), co_so_lieu=True)["cau_truc"]


# ───────────────────────────── chưa có số liệu ⇒ chưa đo, không bao giờ đạt ─────────────────────────────
def test_ban_nhap_chua_so_lieu_muc_ket_qua_chua_do_khong_bao_gio_dat():
    md = _bt(ket_qua="## 3. KẾT QUẢ\n\nTrong [CẦN SỐ] người được mời, [CẦN SỐ] người được phân tích.\n")
    kq = _kq(md)
    assert kq["co_so_lieu"] is False
    for ma in ("13a", "13b", "14a", "18", "19", "21"):
        assert _muc(kq, "STROBE 2007", ma).trang_thai == "chua_do", ma
    assert _muc(kq, "STROBE 2007", "4").trang_thai == "dat"  # phương pháp vẫn chấm
    kq_nop = _kq(md, co_so_lieu=True)
    assert _muc(kq_nop, "STROBE 2007", "13a").trang_thai == "thieu"


def test_ket_luan_chi_co_o_cho_la_binh_thuong_o_ban_nhap_nhung_thieu_khi_nop():
    md = _bt(ket_luan="## 5. KẾT LUẬN\n\n[CẦN KẾT QUẢ THẬT: kết luận]\n")
    assert not any("Kết luận" in x for x in _kq(md)["cau_truc"])
    assert any("Kết luận" in x and "không có nội dung" in x for x in _kq(md, co_so_lieu=True)["cau_truc"])


def test_o_cho_cung_cau_khong_xoa_bang_chung_o_ban_nhap_nhung_nghiem_khi_nop():
    """BTM: «Hội đồng Đạo đức … chấp thuận theo Quyết định số [CẦN…]» — nháp: chấp thuận có, số quyết định chưa đo; nộp:
    câu còn ô trống ⇒ thiếu."""
    pp = CO_SO["phuong_phap"] + ("\n*Đạo đức:* nghiên cứu được Hội đồng Đạo đức Bệnh viện A chấp thuận theo Quyết "
                                 "định số [CẦN QĐ ĐẠO ĐỨC: số]. Người tham gia ký phiếu đồng ý tham gia.\n")
    md = _bt(phuong_phap=pp, ket_qua="## 3. KẾT QUẢ\n\n[CẦN SỐ]\n")
    assert _muc(_kq(md), "Việt Nam", "TT43-HĐĐ").trang_thai == "chua_do"
    assert _muc(_kq(md, co_so_lieu=True), "Việt Nam", "TT43-HĐĐ").trang_thai == "thieu"
    md_du = md.replace("[CẦN QĐ ĐẠO ĐỨC: số]", "125/QĐ-BV")
    assert _muc(_kq(md_du, co_so_lieu=True), "Việt Nam", "TT43-HĐĐ").trang_thai == "dat"


def test_nhan_trong_cua_bo_sinh_chua_co_thong_tin_la_o_trong():
    md = _bt(ket_qua="## 3. KẾT QUẢ\n\n*Lý do loại trừ chính:* chưa có thông tin\n\nSàng lọc: N = chưa có thông tin.\n")
    assert _muc(_kq(md, co_so_lieu=True), "STROBE 2007", "13b").trang_thai == "thieu"


# ───────────────────────────── phạm vi điều kiện (báo nhầm đã sửa) ─────────────────────────────
def test_nhom_chung_cua_nghien_cuu_khac_o_ban_luan_khong_kich_hoat_strobe_8():
    bl = CO_SO["ban_luan"] + "\nThử nghiệm CKD-DETECT ghi 36,0% ở nhóm can thiệp so với 11,5% ở nhóm chứng [2].\n"
    r = _muc(_kq(_bt(ban_luan=bl), co_so_lieu=True), "STROBE 2007", "8")
    assert not any("tương đồng" in t for t in r.thieu), r.thieu


def test_matching_neu_can_trong_bang_sai_lech_khong_phai_ghep_cap():
    pp = CO_SO["phuong_phap"] + "\n| Nguồn sai lệch | Biện pháp |\n|---|---|\n| Selection bias | matching nếu cần |\n"
    assert _muc(_kq(_bt(phuong_phap=pp), "cohort", co_so_lieu=True), "STROBE 2007", "6b").trang_thai == "khong_ap_dung"


def test_de_muc_nhap_tu_dien_khong_kich_hoat_cross():
    md = _bt().replace("## 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU",
                       "## II. PHƯƠNG PHÁP  *(ước tính: ~700 từ | Tự điền: ~75%)*")
    assert not any(c == "CROSS 2021" for c, _ in _kq(md)["chuan"])
    md2 = md.replace("Chọn mẫu liên tiếp.", "Chọn mẫu liên tiếp; người bệnh tự điền phiếu khảo sát.")
    assert any(c == "CROSS 2021" for c, _ in _kq(md2)["chuan"])


def test_cau_phu_dinh_khong_bat_buoc_khong_kich_hoat_gramms():
    van = "Cấu phần định tính có thể bổ trợ nhưng không thay được cắt ngang, và không bắt buộc trong đề tài này."
    assert not K.co_dieu_kien(K.HON_HOP, van)
    assert K.co_dieu_kien(K.HON_HOP, "Đề tài có cấu phần định tính gồm 20 phỏng vấn sâu.")


# ───────────────────────────── diễn giải thận trọng (STROBE 20) ─────────────────────────────
def test_cat_ngang_khang_dinh_nhan_qua_khong_trich_dan_bi_chan_co_rao_don_thi_khong():
    bl = CO_SO["ban_luan"] + "\nĐái tháo đường làm tăng nguy cơ huyết áp không kiểm soát trong mẫu này.\n"
    r = _muc(_kq(_bt(ban_luan=bl), co_so_lieu=True), "STROBE 2007", "20")
    assert r.trang_thai == "thieu" and any("nhân quả" in t for t in r.thieu)
    bl_rao = CO_SO["ban_luan"] + "\nĐái tháo đường có thể làm tăng nguy cơ huyết áp không kiểm soát.\n"
    assert _muc(_kq(_bt(ban_luan=bl_rao), co_so_lieu=True), "STROBE 2007", "20").trang_thai == "dat"
    bl_dan = CO_SO["ban_luan"] + "\nTăng huyết áp kéo dài làm tăng nguy cơ tổn thương thận [2].\n"
    assert _muc(_kq(_bt(ban_luan=bl_dan), co_so_lieu=True), "STROBE 2007", "20").trang_thai == "dat"


def test_cat_ngang_phan_tich_phai_neu_gioi_han_nhan_qua():
    bl = CO_SO["ban_luan"].replace("thiết kế cắt ngang không xác lập trình tự thời gian; ", "")
    r = _muc(_kq(_bt(ban_luan=bl), co_so_lieu=True), "STROBE 2007", "20")
    assert r.trang_thai == "thieu" and any("giới hạn suy nhân quả" in t for t in r.thieu)


# ───────────────────────────── mục khuyến nghị / chưa có tiêu chí ─────────────────────────────
def test_so_do_luong_13c_chi_canh_bao_vi_strobe_ghi_consider():
    r = _muc(_kq(_bt(), co_so_lieu=True), "STROBE 2007", "13c")
    assert r.trang_thai == "canh_bao" and "Consider" in r.ly_do
    kq = _kq(_bt(ket_qua=CO_SO["ket_qua"] + "\n**Hình 1. Sơ đồ chọn mẫu nghiên cứu**\n"), co_so_lieu=True)
    assert _muc(kq, "STROBE 2007", "13c").trang_thai == "dat"


def test_muc_bao_cao_chua_co_tieu_chi_ban_thao_la_chua_do():
    assert _muc(_kq(_bt(), "diagnostic", co_so_lieu=True), "STARD 2015", "1").trang_thai == "chua_do"


def test_record_1_1_doi_ten_co_so_du_lieu_khi_phuong_phap_neu_ten():
    pp = CO_SO["phuong_phap"] + "\n*Nguồn dữ liệu:* hồ sơ bệnh án điện tử (eHospital) năm 2026.\n"
    kq = _kq(_bt(phuong_phap=pp), co_so_lieu=True)
    assert any(c == "RECORD 2015" for c, _ in kq["chuan"])
    assert "tên cơ sở dữ liệu" in _muc(kq, "RECORD 2015", "1.1").thieu
    md2 = _bt(phuong_phap=pp).replace("400 người tăng huyết áp", "400 người (hồ sơ bệnh án điện tử eHospital)")
    assert _muc(_kq(md2, co_so_lieu=True), "RECORD 2015", "1.1").trang_thai == "dat"


# ───────────────────────────── bài báo giao thức ─────────────────────────────
def test_bai_bao_giao_thuc_giu_muc_do_de_cuong_tim_ket_qua_du_kien():
    md = ("# GIAO THỨC NGHIÊN CỨU\n\n## Tỷ lệ hài lòng: giao thức nghiên cứu cắt ngang\n\n# 1. ĐẶT VẤN ĐỀ\n\nX [1].\n\n"
          "# 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP\n\nCắt ngang.\n\n# 3. KẾT QUẢ DỰ KIẾN\n\nKết quả trình bày Bảng 1 Đặc "
          "điểm chung; sơ đồ luồng tham gia.\n\n# 4. BÀN LUẬN\n\nHạn chế.\n")
    kq = _kq(md, che_do="giao_thuc", co_so_lieu=False)
    assert _muc(kq, "STROBE 2007", "1a").trang_thai == "bao_cao"
    assert _muc(kq, "STROBE 2007", "13a").trang_thai == "dat"
    assert KB.la_bai_giao_thuc(Path("Bai-bao-giao-thuc_X.md"), "") and KB.la_bai_giao_thuc(Path("x.md"), md)
    assert not KB.la_bai_giao_thuc(Path("BAN_THAO_X.md"), _bt())


# ───────────────────────────── nối vào kiem_ban_thao_tap_chi ─────────────────────────────
def test_k18_trong_kiem_tap_chi_thiet_ke_tu_study_meta_va_khong_ro_thiet_ke(tmp_path):
    de_tai = tmp_path / "exports" / "X"
    (de_tai / "tap_chi" / "YDTH175").mkdir(parents=True)
    p = de_tai / "tap_chi" / "YDTH175" / "BAN_THAO_X.md"
    p.write_text(_bt(), encoding="utf-8", newline="\n")
    assert KB.thiet_ke_cua(p) == ""
    k = KB.k18(_bt(), "")
    assert not k["vi_pham"] and any("không xác định được thiết kế" in x for x in k["ghi_chu"])
    assert KB.k18(_bt(), "", nop=True)["vi_pham"]
    (de_tai / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": {"design": "cross_sectional"}}}),
                                            encoding="utf-8", newline="\n")
    assert KB.thiet_ke_cua(p) == "cross_sectional"
    kq = KB.kiem(p, "Tạp chí Y Dược Thực hành 175")
    assert kq["k18"]["thiet_ke"] == "cross_sectional" and "STROBE 2007" in kq["k18"]["tom_tat"]
    assert any(x.startswith("K18 STROBE 2007") for x in kq["vi_pham"])


def test_k18_ban_nhap_ghi_chu_chua_do_khong_bao_gio_tinh_dat():
    md = _bt(ket_qua="## 3. KẾT QUẢ\n\n[CẦN SỐ]\n")
    k = KB.k18(md, "cross_sectional")
    assert any("CHƯA ĐO ĐƯỢC" in x and "không tính là đạt" in x for x in k["ghi_chu"])
    assert not any("13a" in x for x in k["vi_pham"])


# ───────────────────────────── bộ sinh G7: dữ kiện đã chốt, không câu mẫu ─────────────────────────────
def _meta(tmp_path, **gp):
    (tmp_path / "study_meta.json").write_text(json.dumps({"gate_params": gp}, ensure_ascii=False), encoding="utf-8",
                                              newline="\n")
    return tmp_path


def test_g7_nguon_tham_so_lay_tu_g3_khong_ghi_tu_y_van(tmp_path):
    d = _meta(tmp_path, G3={"effect_source": "PMID: 23137151 (Castellsague 2012, Drug Saf) — RR 1,84",
                            "prevalence_source": "Giả định p = 0,5 cho cỡ mẫu lớn nhất khi chưa có ước tính"})
    assert G7._nguon_tham_so_g3(d, "OR") == "PMID: 23137151 (Castellsague 2012, Drug Saf)"
    assert G7._nguon_tham_so_g3(d, "PREVALENCE").startswith("Giả định p = 0,5")
    assert G7._nguon_tham_so_g3(_meta(tmp_path, G3={"effect_source": "[CẦN PMID]"}), "OR") is None


def test_g7_ly_do_mien_va_dang_ky_tu_g2(tmp_path):
    d = _meta(tmp_path, G2={"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA", "registration_registry":
                            "ClinicalTrials.gov", "registration_date": "2027-02-01"})
    assert "hồi cứu" in G7._ly_do_mien_g7(d)
    assert G7._dang_ky_g7(d, "NCT99999999") == "ClinicalTrials.gov NCT99999999 (đăng ký ngày 2027-02-01)"
    assert G7._dang_ky_g7(d, "[CẦN SỐ ĐĂNG KÝ]") == "[CẦN SỐ ĐĂNG KÝ]"
    assert G7._ly_do_mien_g7(_meta(tmp_path, G2={"recruitment_mode": "NOT_APPLICABLE"})) is None


def test_g7_khoi_rct_chep_nguyen_chu_g1_sap_bo_truong_vang_va_dau_vet_may(tmp_path):
    d = _meta(tmp_path, G1={"design_rationale": "Câu hỏi điều trị (G0 treatment/superiority) — RCT song song 2 nhánh",
                            "comparator": "Chăm sóc thường quy", "randomisation": "Khối hoán vị sinh bằng phần mềm",
                            "allocation_concealment": "[CẦN — PI điền]", "blinding": "Không áp dụng — nhãn mở"})
    sap = {"ton_hai": "Biến cố bất lợi liên quan can thiệp", "danh_gia_ton_hai": "Hỏi chủ động mỗi lần tái khám",
           "giua_ky": "Không"}
    khoi = "\n".join(G7._khoi_rct_g7(d, sap, "superiority"))
    assert "(G0" not in khoi and "khung so sánh vượt trội" in khoi and "*Nhóm chứng:* Chăm sóc thường quy." in khoi
    assert "Giấu phân bổ" not in khoi and "Làm mù" not in khoi
    assert "*Tổn hại:* Biến cố bất lợi liên quan can thiệp; cách đánh giá: hỏi chủ động" in khoi
    assert G7._khoi_rct_g7(_meta(tmp_path), {}, "") == []


def test_g7_khoi_doi_tuong_va_chan_doan_tu_g1(tmp_path):
    d = _meta(tmp_path, G1={"control_source": "Cùng cơ sở, ghép theo giới và nhóm tuổi, 2 chứng : 1 ca",
                            "reference_standard": "Đo đàn hồi gan, người đọc không biết kết quả FIB-4",
                            "intervention_or_exposure": "Chỉ số FIB-4"},
              G2={"recruitment_mode": "PROSPECTIVE_NEW_PARTICIPANTS"})
    dt = "\n".join(G7._khoi_doi_tuong_g7(d))
    assert "ghép theo giới" in dt and "tiến cứu" in dt
    cd = "\n".join(G7._khoi_chan_doan_du_bao_g7(d, "diagnostic"))
    assert "*Chuẩn tham chiếu:*" in cd and "*Xét nghiệm đánh giá:* Chỉ số FIB-4." in cd
    assert G7._khoi_chan_doan_du_bao_g7(d, "cohort") == []


def test_g7_sap_tom_tat_lay_bien_mo_hinh_bien_lien_tuc_ton_hai(tmp_path):
    sap = ("### §3 THỐNG KÊ MÔ TẢ\n\n- Biến liên tục: trung bình ± SD hoặc trung vị [IQR]\n\n"
           "### §5 PHÂN TÍCH ĐA BIẾN\n\n- **Biến độc lập đưa vào:** `tuoi` (Tuổi) *(từ ma trận)*, lý do: gây nhiễu\n"
           "- **Giả định:** Kiểm dạng tuyến tính của tuổi\n\n### §13 GIỮA KỲ\n\n- **Có phân tích giữa kỳ:** Không\n\n"
           "### §15 TỔN HẠI\n\n- **Định nghĩa tổn hại (harms):** Biến cố bất lợi\n- **Cách đánh giá:** Hỏi chủ động\n")
    (tmp_path / "G4_A5_SAP_FINAL_X.md").write_text(sap, encoding="utf-8", newline="\n")
    ra = G7._sap_tom_tat(tmp_path, "X")
    assert ra["bien_da_bien"] == "tuoi (Tuổi), lý do: gây nhiễu" and ra["bien_lien_tuc"].startswith("trung bình")
    assert ra["gia_dinh_mo_hinh"] == "Kiểm dạng tuyến tính của tuổi" and ra["giua_ky"] == "Không"
    assert ra["ton_hai"] == "Biến cố bất lợi" and ra["danh_gia_ton_hai"] == "Hỏi chủ động"
    (tmp_path / "G4_A5_SAP_FINAL_X.md").write_text(sap.replace("`tuoi` (Tuổi) *(từ ma trận)*, lý do: gây nhiễu",
                                                               "Không áp dụng — mô tả"), encoding="utf-8", newline="\n")
    assert "bien_da_bien" not in G7._sap_tom_tat(tmp_path, "X")


# ───────────────────────────── đồng nghĩa đã đo (báo nhầm) ─────────────────────────────
@pytest.mark.parametrize("cau", ["phân tích nhạy cảm theo cách hoàn thành phiếu", "phân tích độ nhạy định trước"])
def test_phan_tich_nhay_cam_la_phan_tich_do_nhay(cau):
    pp = CO_SO["phuong_phap"] + f"\n*Phân tích độ nhạy:* {cau}.\n"
    assert _muc(_kq(_bt(phuong_phap=pp), co_so_lieu=True), "STROBE 2007", "12e").trang_thai == "dat"


def test_doan_he_la_thuan_tap_va_ten_sai_lech_tieng_anh_duoc_nhan():
    pp = ("## 2. PHƯƠNG PHÁP\n\nĐây là nghiên cứu đoàn hệ (Cohort), hồi cứu.\n\n"
          "| Nguồn sai lệch | Biện pháp |\n|---|---|\n| Selection bias | Chọn mẫu liên tiếp |\n")
    kq = _kq(_bt(phuong_phap=pp), "cohort", co_so_lieu=True)
    assert _muc(kq, "STROBE 2007", "4").trang_thai == "dat" and _muc(kq, "STROBE 2007", "9").trang_thai == "dat"


def test_mau_de_cuong_thay_mau_ban_thao_cho_moi_chuan():
    """Bản thảo G7 viết «Tiêu chí nhận/loại» và «Tài trợ: Không có tài trợ…» — STARD 6, 30 từng báo nhầm."""
    pp = ("## 2. PHƯƠNG PHÁP\n\n*Tiêu chí nhận:* Tuổi ≥18; gan nhiễm mỡ trên siêu âm.  \n"
          "*Tiêu chí loại:* Uống rượu nguy hại.\n")
    md = _bt(phuong_phap=pp) + "\n## KHAI BÁO\n\n**Tài trợ:**  \nKhông có tài trợ bên ngoài\n"
    kq = _kq(md, "diagnostic", co_so_lieu=True)
    assert _muc(kq, "STARD 2015", "6").trang_thai == "dat"
    assert _muc(kq, "STARD 2015", "30").trang_thai == "dat"


# ───────────────────────────── phiên «G7 đọc sổ sàng lọc» báo (22/11/2026) ─────────────────────────────
_KQ_CHI_DAN = ("## 3. KẾT QUẢ\n\n> Phần G6 không có (sàng lọc, kết cục phụ…) — điền khi có sổ.\n\n"
               "*Bảng 1 gồm đúng các biến nền G6 đã phân tích (theo SAP).*\n")


def test_dong_chi_dan_g6_va_bang_1_khong_phai_so_nguoi():
    r13 = _muc(_kq(_bt(ket_qua=_KQ_CHI_DAN), co_so_lieu=True), "STROBE 2007", "13a")
    assert r13.trang_thai == "thieu", r13.bang_chung
    r22 = _muc(_kq(_bt(ket_qua=_KQ_CHI_DAN), "rct", co_so_lieu=True), "CONSORT 2025", "22a")
    assert not any("phân tích kết cục" in b for b in r22.bang_chung), r22.bang_chung
    that = ("## 3. KẾT QUẢ\n\n218 người được phân bổ ngẫu nhiên (109 người mỗi nhóm), mọi người nhận đúng can thiệp; "
            "218 người được phân tích ở cả hai nhóm.\n")
    assert _muc(_kq(_bt(ket_qua=that), "rct", co_so_lieu=True), "CONSORT 2025", "22a").trang_thai == "dat"
    assert _muc(_kq(_bt(ket_qua="## 3. KẾT QUẢ\n\nSàng lọc: N = 450; Phân tích (G6): N = 400.\n"), co_so_lieu=True),
                "STROBE 2007", "13a").trang_thai == "dat"


def test_khong_co_nguoi_mat_theo_doi_khong_can_ly_do():
    md = _bt(ket_qua="## 3. KẾT QUẢ\n\nKhông có người mất theo dõi sau phân bổ ngẫu nhiên ở cả hai nhóm.\n")
    assert _muc(_kq(md, "rct", co_so_lieu=True), "CONSORT 2025", "22b").trang_thai == "dat"
    md2 = _bt(ket_qua="## 3. KẾT QUẢ\n\nNhóm can thiệp có 5 người mất theo dõi.\n")
    assert _muc(_kq(md2, "rct", co_so_lieu=True), "CONSORT 2025", "22b").trang_thai == "thieu"
    md3 = _bt(ket_qua="## 3. KẾT QUẢ\n\nNhóm can thiệp có 5 người mất theo dõi vì chuyển nơi điều trị.\n")
    assert _muc(_kq(md3, "rct", co_so_lieu=True), "CONSORT 2025", "22b").trang_thai == "dat"
