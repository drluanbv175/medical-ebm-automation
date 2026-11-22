"""K17 — 12 chuẩn thêm (SPIRIT, PRISMA-P, STARD, TRIPOD+AI, COREQ, SRQR, GRAMMS, SQUIRE, CHEERS, TREND, CARE, COSMIN).

Bác sĩ 21/11/2026: «từng tiêu chuẩn trong từng cấu trúc đề cương nghiên cứu phải đạt tiêu chuẩn và sự tin cậy cao nhất»,
cho MỌI thiết kế. Mỗi test khoá một hành vi đã phân xử trên 8 đề cương giả lập mới (G0→G10) và hai đề cương thật: báo
nhầm đã sửa ở bộ kiểm, đạt giả đã chặn, cơ chế mới (cảnh báo khi chưa đối chiếu bảng gốc, loại tên đề tài khỏi phần
phương pháp, chuẩn có điều kiện, bộ sinh nguyên văn từ XML Europe PMC).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))

import chuan_bao_cao_items as CBC  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import sinh_chuan_bao_cao_items as G  # noqa: E402
import tieu_chi_chuan_de_cuong as TC  # noqa: E402


def _kq(md: str, tk: str):
    return {(r.chuan, r.ma): r for r in K.doi_chieu(md, tk)["ket_qua"]}


def _dc(*khoi: str, ten: str = "## ĐỀ TÀI THỬ") -> str:
    """Đề cương khuôn 18 mục tối thiểu: tên đề tài cấp 2 dưới «# ĐỀ CƯƠNG…», rồi các khối."""
    return "# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC\n\n" + ten + ("\n\n## THÔNG TIN CHUNG VỀ ĐỀ TÀI\n\n| Kinh phí | Đơn vị cấp |"
                                                         "\n\n") \
        + "\n\n".join(khoi) + "\n"


# ───────────────────────────── dữ liệu nguyên văn + bộ sinh ─────────────────────────────
def test_du_lieu_nguyen_van_cac_chuan_cc_dung_so_dong_va_giay_phep():
    assert (len(CBC.STARD_2015_ITEMS), len(CBC.TRIPOD_AI_2024_ITEMS), len(CBC.CHEERS_2022_ITEMS),
            len(CBC.SQUIRE_2_0_ITEMS), len(CBC.CARE_2013_ITEMS),
            len(CBC.HARPER_2023_MUC_LUC)) == (34, 52, 28, 40, 23, 43)
    assert all("creativecommons.org/licenses/" in v for v in CBC.GIAY_PHEP.values())
    assert CBC.GIAY_PHEP["SQUIRE"].endswith("by-nc/4.0")  # phi thương mại — ghi rõ ở docstring mô-đun
    stard = {m: v for m, _p, _c, v in CBC.STARD_2015_ITEMS}
    assert stard["13b"].startswith("Whether clinical information and index test results were available")
    tripod = {m: (d, v) for m, _p, _c, d, v in CBC.TRIPOD_AI_2024_ITEMS}
    assert tripod["12f"][0] == "E" and tripod["9a"][0] == "D"
    care = dict((m, v) for m, _c, v in CBC.CARE_2013_ITEMS)
    assert care["3b"].startswith("Case Presentation: - The main symptoms")  # gạch con nối vào mục chữ cái trước


_XML_LIC = ('<article xmlns:xlink="http://www.w3.org/1999/xlink"><front><permissions><license '
            'xlink:href="https://creativecommons.org/licenses/by/4.0/"><p>CC BY</p></license></permissions></front>'
            '<body>{}</body></article>')


def _xml(tmp_path, ten, than, lic=True):
    tep = tmp_path / ten
    tep.write_text((_XML_LIC if lic else "<article><body>{}</body></article>").format(than), encoding="utf-8",
                   newline="\n")
    return tep


def test_bo_sinh_tach_rowspan_tripod_va_danh_sach_squire(tmp_path):
    tripod = _xml(tmp_path, "t.xml", "<table-wrap/>" + (
        "<table-wrap><table><tr><th>S</th><th>I</th><th>D</th><th>C</th></tr>"
        "<tr><td colspan='4'>Methods</td></tr>"
        "<tr><td rowspan='2'>Outcome</td><td>8a</td><td>D;E</td><td>Define it</td></tr>"
        "<tr><td>8b</td><td>E</td><td>Blind it</td></tr>"
        "<tr><td>Sample size</td><td>10</td><td>D;E</td><td>Explain</td></tr></table></table-wrap>"))
    assert G.muc_tripod_ai(tripod) == [("8a", "Methods", "Outcome", "D;E", "Define it"),
                                      ("8b", "Methods", "Outcome", "E", "Blind it"),
                                      ("10", "Methods", "Sample size", "D;E", "Explain")]
    squire = _xml(tmp_path, "s.xml", (
        "<table-wrap><table><tr><th>a</th><th>b</th></tr><tr><td>Introduction</td><td>Why did you start?</td></tr>"
        "<tr><td>2. Abstract</td><td><list list-type='alpha-lower'><list-item><p>One.</p></list-item>"
        "<list-item><p>Two.</p></list-item></list></td></tr><tr><td>3. Problem</td><td>Local.</td></tr>"
        "</table></table-wrap>"))
    ra, dan = G.muc_squire(squire)
    assert ra == [("2a", "Introduction", "Abstract", "One."), ("2b", "Introduction", "Abstract", "Two."),
                  ("3", "Introduction", "Problem", "Local.")]
    assert dan == {"Introduction": "Why did you start?"}


def test_bo_sinh_care_noi_gach_con_va_harper_ma_bang(tmp_path):
    care = _xml(tmp_path, "c.xml", (
        "<table-wrap><table><tr><th colspan='3'>Narrative</th></tr><tr><th>N</th><th>No</th><th>D</th></tr>"
        "<tr><td>Abstract</td><td>3</td><td>a) Intro</td></tr><tr><td></td><td></td><td>b) Case:</td></tr>"
        "<tr><td></td><td></td><td>- symptom</td></tr><tr><td>Timeline</td><td>7</td><td>Dates</td></tr>"
        "</table></table-wrap>"))
    ra, mo_dau = G.muc_care(care)
    assert mo_dau == "Narrative"
    assert ra == [("3a", "Abstract", "Intro"), ("3b", "Abstract", "Case: - symptom"), ("7", "Timeline", "Dates")]
    harper = _xml(tmp_path, "h.xml", "<table-wrap/><table-wrap/><table-wrap><table>"
                  "<tr><td>7.3.1 Context of time 0</td></tr><tr><td>Table 3 Operational Definition</td></tr>"
                  "</table></table-wrap>")
    assert G.muc_harper(harper) == [("7.3.1", "Context of time 0", ""),
                                    ("T3", "Table 3 Operational Definition", "7.3.1")]


def test_bo_sinh_tu_choi_ghi_khi_giay_phep_khong_phai_creative_commons(tmp_path):
    for ten, (pmc, _n, _i) in G.NGUON.items():
        _xml(tmp_path, f"raw_{pmc}.xml", "<p>x</p>", lic=(ten != "CARE"))
    _du, phep, loi = G.doc_tat_ca(tmp_path, {})
    assert phep["CARE"] == "" and any(x.startswith("CARE: giấy phép không phải Creative Commons") for x in loi)
    assert not any(x.startswith("STARD: giấy phép") for x in loi)


# ───────────────────────────── phủ đủ chuẩn, tiêu chí hợp lệ ─────────────────────────────
def test_moi_chuan_cua_moi_thiet_ke_deu_co_tieu_chi_khong_con_chua_do():
    for tk, ds in K.CHUAN_CO_SO.items():
        for chuan in ds:
            muc = K.danh_sach_muc(chuan, tk)
            assert muc, (tk, chuan)
            assert all(p in K.PHAN for m in muc for p in m.phan), (tk, chuan)
    for chuan, _m, _l in K.CHUAN_DIEU_KIEN:
        if chuan == "ISPOR BIA GPP II 2014":  # chủ ý chưa có tiêu chí — báo ⚪, không bao giờ đạt
            assert K.danh_sach_muc(chuan, "economic") is None
            continue
        assert K.danh_sach_muc(chuan, "cross_sectional"), chuan


def test_moi_bieu_thuc_bien_dich_duoc_va_ma_muc_khop_nguyen_van():
    for chuan in TC.BANG:
        for m in TC.danh_sach_muc_them(chuan):
            for yt in m.yeu_to:
                re.compile(yt.mau)
                if yt.khi:
                    re.compile(yt.khi)
            if m.ap_dung_khi:
                re.compile(m.ap_dung_khi.lstrip("!"))
    spirit = {m.ma for m in TC.danh_sach_muc_them("SPIRIT 2025")}
    assert spirit == {ma for ma, _v, _p in __import__("protocol_checklist_items").SPIRIT_2025_ITEMS}
    assert {m.ma for m in TC.danh_sach_muc_them("STARD 2015")} == {x[0] for x in CBC.STARD_2015_ITEMS}
    assert {m.ma for m in TC.danh_sach_muc_them("TRIPOD+AI 2024")} == {x[0] for x in CBC.TRIPOD_AI_2024_ITEMS}
    assert {m.ma for m in TC.danh_sach_muc_them("CHEERS 2022")} == {x[0] for x in CBC.CHEERS_2022_ITEMS}
    assert {m.ma for m in TC.danh_sach_muc_them("SQUIRE 2.0")} == {x[0] for x in CBC.SQUIRE_2_0_ITEMS}
    assert {m.ma for m in TC.danh_sach_muc_them("CARE 2013")} == {x[0] for x in CBC.CARE_2013_ITEMS}


def test_chuan_ban_quyen_khong_luu_nguyen_van():
    for chuan in ("TREND 2004", "COREQ 2007", "SRQR 2014", "GRAMMS 2008", "COSMIN 2021"):
        assert all(m.nguyen_van is None for m in TC.danh_sach_muc_them(chuan)), chuan


# ───────────────────────────── cơ chế mới ─────────────────────────────
def test_chuan_chua_doi_chieu_bang_goc_chi_canh_bao_khong_chan():
    # 22/11/2026: COREQ/SRQR đã đối chiếu bản in lại toàn văn bảng gốc và bật chặn — ví dụ chuẩn chưa đối chiếu là TREND
    md = _dc("# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n## 4.1. Thiết kế nghiên cứu\n\nNghiên cứu can thiệp không "
             "ngẫu nhiên.")
    kq = K.doi_chieu(md, "non_randomized")
    trend = [r for r in kq["ket_qua"] if r.chuan == "TREND 2004"]
    assert trend and all(r.trang_thai in ("canh_bao", "dat", "bao_cao", "khong_ap_dung") for r in trend)
    assert any(r.trang_thai == "canh_bao" for r in trend)
    assert not any(x.startswith("K17 TREND") for x in K.loi_k17(md, "non_randomized"))
    assert any(x.startswith("K17 Việt Nam") for x in K.loi_k17(md, "non_randomized"))  # chuẩn khác vẫn chặn
    dt = _dc("# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n## 4.1. Thiết kế nghiên cứu\n\nNghiên cứu định tính.")
    assert any(x.startswith("K17 COREQ 2007") for x in K.loi_k17(dt, "qualitative"))
    assert any(x.startswith("K17 SRQR 2014") for x in K.loi_k17(dt, "qualitative"))


def test_ten_de_tai_khong_bi_nhan_la_phan_phuong_phap():
    ten = "## HIỆU QUẢ CỦA TIN NHẮN: THỬ NGHIỆM LÂM SÀNG NGẪU NHIÊN — TỔNG QUAN HỆ THỐNG VÀ PHÂN TÍCH GỘP"
    md = _dc("# 1. ĐẶT VẤN ĐỀ\n\nNội dung.", ten=ten + "\n\nDanh sách ngẫu nhiên sinh bằng phần mềm do thống kê viên "
                                                       "độc"
                                                          " lập giữ.")
    assert _kq(md, "rct")[("SPIRIT 2025", "21a")].trang_thai == "thieu"
    assert _kq(md, "rct")[("SPIRIT 2025", "21a")].vi_tri == []
    assert _kq(md, "rct")[("SPIRIT 2025", "1a")].trang_thai == "dat"  # nhưng tên vẫn là bằng chứng cho mục tiêu đề


def test_phu_luc_tom_tat_ke_hoach_phan_tich_khong_phai_bia():
    md = _dc("# 6. KẾ HOẠCH\n\n## 6.1. Nhân lực và phân công nhiệm vụ\n\nChủ nhiệm đề tài.",
             "# PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ\n\n| Mục tiêu | Biến | Vai trò |")
    r = _kq(md, "rct")[("SPIRIT 2025", "3a")]
    assert r.trang_thai == "thieu" and r.thieu == ["vai trò/nhiệm vụ"]
    md2 = md.replace("Chủ nhiệm đề tài.", "Chủ nhiệm đề tài, thống kê viên, 2 điều tra viên.")
    assert _kq(md2, "rct")[("SPIRIT 2025", "3a")].trang_thai == "dat"


def test_chuan_co_dieu_kien_cheers_coreq_gramms_va_khong_trung():
    ten = lambda md, tk: [c for c, _ in K.chuan_ap_dung(tk, md)]  # noqa: E731
    assert "CHEERS 2022" in ten("Phân tích chi phí–hiệu quả, ICER theo QALY.", "rct")
    assert "CHEERS 2022" not in ten("Phân tích chi phí–hiệu quả — không áp dụng.", "rct")
    # BIA báo cáo theo ISPOR BIA GPP II, không theo CHEERS (agent kinh-te-y-te M7): chưa có tiêu chí ⇒ ⚪
    bia = ten("Phân tích tác động ngân sách 5 năm từ quan điểm BHYT.", "economic")
    assert bia == ["ISPOR BIA GPP II 2014", "Việt Nam"]
    chua_do = K.doi_chieu("Phân tích tác động ngân sách.", "economic")["chua_do"]
    assert [c for c, _ in chua_do] == ["ISPOR BIA GPP II 2014"]
    assert "CHEERS 2022" in ten("Phân tích chi phí–hiệu quả (ICER) và tác động ngân sách.", "economic")
    hon_hop = ten("Thiết kế phương pháp hỗn hợp: phỏng vấn sâu 20 người sau thử nghiệm.", "rct")
    assert {"COREQ 2007", "SRQR 2014", "GRAMMS 2008"} <= set(hon_hop)
    dinh_tinh = ten("Phỏng vấn sâu bán cấu trúc.", "qualitative")
    assert dinh_tinh.count("COREQ 2007") == 1 and dinh_tinh.count("SRQR 2014") == 1
    assert ten("Phỏng vấn nhận thức 10 người để thử bộ câu hỏi tự điền.", "cross_sectional").count("COREQ 2007") == 0


# ───────────────────────────── đạt giả đã chặn (phân xử 21/11/2026) ─────────────────────────────
DAO_DUC = "# 4. PHƯƠNG PHÁP\n\n## 4.12. Đạo đức trong nghiên cứu\n\n"


def test_spirit_ppi_khong_dat_nho_cau_loi_ich_cong_dong():
    md = _dc(DAO_DUC + "Lợi ích cộng đồng: Góp phần tạo bằng chứng cho thực hành; người tham gia được tư vấn.")
    assert _kq(md, "rct")[("SPIRIT 2025", "11")].trang_thai == "thieu"
    md2 = _dc(DAO_DUC + "Đại diện người bệnh tham gia góp ý vào thiết kế nội dung tin nhắn.")
    assert _kq(md2, "rct")[("SPIRIT 2025", "11")].trang_thai == "dat"


def test_spirit_34_khong_dat_nho_chu_ton_hai_tron():
    md = _dc(DAO_DUC + "- Tổn hại: Biến cố bất lợi liên quan can thiệp: phàn nàn, lo âu.")
    assert _kq(md, "rct")[("SPIRIT 2025", "34")].trang_thai == "thieu"
    md2 = _dc(DAO_DUC + "- Người tham gia gặp tổn hại do nghiên cứu được điều trị miễn phí và bồi thường theo quy "
                        "định.")
    assert _kq(md2, "rct")[("SPIRIT 2025", "34")].trang_thai == "dat"


def test_vai_tro_tai_tro_phai_cung_doan_voi_nguon_kinh_phi():
    md = _dc(DAO_DUC + "Nghiên cứu này được tài trợ bởi: Không có tài trợ bên ngoài.")
    assert _kq(md, "rct")[("SPIRIT 2025", "3c")].trang_thai == "thieu"
    md2 = md.replace("| Kinh phí | Đơn vị cấp |", "| Kinh phí | Đơn vị cấp; đơn vị không tham gia thiết kế, phân tích "
                                                  "|")
    assert _kq(md2, "rct")[("SPIRIT 2025", "3c")].trang_thai == "dat"


XN = ("# 4. PHƯƠNG PHÁP\n\n## 4.5. Xét nghiệm cần đánh giá và tiêu chuẩn tham chiếu\n\n"
      "- Xét nghiệm cần đánh giá: Chỉ số FIB-4 tính từ tuổi, AST, ALT, tiểu cầu.\n"
      "- Tiêu chuẩn tham chiếu: Đo độ đàn hồi gan ≥10 kPa, người đọc không biết kết quả FIB-4.")


def test_stard_13a_khong_dat_nho_cau_lam_mu_cua_chuan_tham_chieu():
    kq = _kq(_dc(XN), "diagnostic")
    assert kq[("STARD 2015", "13b")].trang_thai == "dat"
    assert kq[("STARD 2015", "13a")].trang_thai == "thieu"
    md = _dc(XN + "\n- FIB-4 được tính trước khi có kết quả tiêu chuẩn tham chiếu.")
    assert _kq(md, "diagnostic")[("STARD 2015", "13a")].trang_thai == "dat"


def test_tripod_9a_khong_dat_nho_cau_nguon_sai_so():
    sai_so = ("# 4. PHƯƠNG PHÁP\n\n## 4.9. Sai số và biện pháp khống chế sai số\n\n"
              "- Nguồn sai số có thể gặp: quá khớp; chọn yếu tố dự báo theo dữ liệu.")
    md = _dc(sai_so, "## 4.10. Xử lý\n\nPhát triển mô hình dự báo mới.")
    assert _kq(md, "prediction")[("TRIPOD+AI 2024", "9a")].trang_thai == "thieu"
    md2 = md.replace("theo dữ liệu.", "theo dữ liệu.\n- Biện pháp khống chế: yếu tố dự báo định trước theo y văn.")
    assert _kq(md2, "prediction")[("TRIPOD+AI 2024", "9a")].trang_thai == "dat"


def test_prisma_p_15a_khong_dat_nho_cau_hoi_quy_gop():
    pt = "# 4. PHƯƠNG PHÁP\n\n## 4.10. Xử lý và phân tích số liệu\n\n"
    md = _dc(pt + "- Kiểm định tương tác: hồi quy gộp (meta-regression) khi đủ nghiên cứu.")
    assert _kq(md, "sr_ma")[("PRISMA-P 2015", "15a")].trang_thai == "thieu"
    md2 = _dc(pt + "- Chỉ gộp khi các nghiên cứu đủ tương đồng lâm sàng về quần thể và can thiệp; phân tích gộp khi ≥ "
                   "2.")
    assert _kq(md2, "sr_ma")[("PRISMA-P 2015", "15a")].trang_thai == "dat"


# ───────────────────────────── báo nhầm đã sửa (phân xử 21/11/2026) ─────────────────────────────
def test_stard_22_nhan_trong_cung_30_ngay():
    md = _dc("# 4. PHƯƠNG PHÁP\n\n## 4.8. Quy trình nghiên cứu\n\n1. Xét nghiệm máu.\n2. Đo đàn hồi trong 30 ngày.")
    assert _kq(md, "diagnostic")[("STARD 2015", "22")].trang_thai == "dat"


def test_tripod_dca_va_han_che_chi_o_de_muc():
    md = _dc("# 4. PHƯƠNG PHÁP\n\n## 4.10. Xử lý và phân tích số liệu\n\n"
             "- Phương pháp: discrimination (C-statistic), calibration và DCA.",
             "## 4.12. Hạn chế của nghiên cứu\n\nChưa kiểm định ngoài; một cơ sở.")
    kq = _kq(md, "prediction")
    assert kq[("TRIPOD+AI 2024", "12e")].trang_thai == "dat"
    assert kq[("TRIPOD+AI 2024", "26")].trang_thai == "dat"


def test_spirit_28a_28b_nhan_cau_khong_thanh_lap_co_ly_do():
    md = _dc(DAO_DUC + "- Phân tích giữa kỳ: không thực hiện vì can thiệp nguy cơ tối thiểu.\n"
             "- Hội đồng theo dõi dữ liệu và an toàn: không thành lập vì can thiệp nguy cơ tối thiểu.")
    kq = _kq(md, "rct")
    assert kq[("SPIRIT 2025", "28a")].trang_thai == "dat" and kq[("SPIRIT 2025", "28b")].trang_thai == "dat"


def test_cosmin_icc_gom_cum_va_cau_khong_thuoc_pham_vi_khong_kich_hoat_do_tin_cay_lap_lai():
    md = _dc("# 2. PHƯƠNG PHÁP\n\n## 2.5. Cỡ mẫu\n\nHiệu chỉnh gom cụm với ICC = 0,02. Mỗi nửa mẫu 500 quan sát, tương "
             "đương 17 quan sát cho mỗi câu.\n\n## 2.6. Công cụ thu thập\n\nBộ câu hỏi tự điền 30 câu; Cronbach's "
             "alpha "
             "≥ 0,7; CVI.\n\nĐộ tin cậy lặp lại, sai số đo lường không thuộc phạm vi đề tài.")
    kq = _kq(md, "cross_sectional")
    assert kq[("COSMIN 2021", "R2")].trang_thai == "khong_ap_dung"
    assert kq[("COSMIN 2021", "GM5")].trang_thai == "dat"
    assert K.co_dieu_kien(TC.TEST_RETEST, "Đo lặp lại sau 2 tuần (test–retest).")


def test_prisma_p_12_nhan_dac_diem_nghien_cuu_o_phan_tich():
    md = _dc("# 4. PHƯƠNG PHÁP\n\n## 4.10. Xử lý và phân tích số liệu\n\n"
             "- Mô tả đặc điểm các nghiên cứu được đưa vào (thiết kế, cỡ mẫu, quần thể, can thiệp).")
    assert _kq(md, "sr_ma")[("PRISMA-P 2015", "12")].trang_thai == "dat"


def test_tripod_muc_chi_cho_phat_trien_hoac_danh_gia_theo_dung_loai_de_cuong():
    phat_trien = _dc("# 2. MỤC TIÊU\n\n1. Xây dựng mô hình dự báo nhập viện.")
    kq = _kq(phat_trien, "prediction")
    assert kq[("TRIPOD+AI 2024", "12f")].trang_thai == "khong_ap_dung"  # E: chỉ khi đánh giá mô hình có sẵn
    assert kq[("TRIPOD+AI 2024", "12a")].trang_thai != "khong_ap_dung"  # D: có xây dựng mô hình
    danh_gia = _dc("# 2. MỤC TIÊU\n\n1. Kiểm định ngoại thang điểm đã có (GRACE) tại bệnh viện.")
    kq2 = _kq(danh_gia, "prediction")
    assert kq2[("TRIPOD+AI 2024", "12a")].trang_thai == "khong_ap_dung"
    assert kq2[("TRIPOD+AI 2024", "12f")].trang_thai != "khong_ap_dung"


def test_cac_chuan_chua_co_van_ban_that_do_duoc_tren_de_cuong_mau():
    md = _dc("# 4. PHƯƠNG PHÁP\n\n## 4.1. Thiết kế nghiên cứu\n\nThiết kế phương pháp hỗn hợp giải thích tuần tự: cấu "
             "phần định lượng chính, cấu phần định tính phụ nhằm giải thích kết quả.\n\n## 4.10. Xử lý và phân tích số "
             "liệu\n\nHồi quy logistic; phỏng vấn sâu phân tích chủ đề. Tích hợp kết quả bằng ma trận tích hợp (joint "
             "display) do chủ nhiệm thực hiện.")
    kq = _kq(md, "mixed_methods")
    assert all(kq[("GRAMMS 2008", m)].trang_thai == "dat" for m in ("1", "2", "3", "4"))
    for tk, chuan in (("quality_improvement", "SQUIRE 2.0"), ("economic", "CHEERS 2022"),
                      ("non_randomized", "TREND 2004"), ("case_report", "CARE 2013")):
        kq = K.doi_chieu(md, tk)
        assert any(r.chuan == chuan for r in kq["ket_qua"]) and not kq["chua_do"], tk


# ───────────────────────────── khâu chặn nộp (sau #399: K17 chặn mọi đề cương nộp) ─────────────────────────────
def test_chuan_cho_bo_sinh_chi_canh_bao_o_khau_nop_con_cosmin_va_strobe_van_chan():
    md = _dc(DAO_DUC + "Nghiên cứu này được tài trợ bởi: Không có tài trợ bên ngoài.")
    assert _kq(md, "rct")[("SPIRIT 2025", "3c")].trang_thai == "thieu"  # bộ đo vẫn báo ✗ đầy đủ
    assert not any(x.startswith("K17 SPIRIT") for x in K.loi_k17(md, "rct"))
    assert any(x.startswith("K17 SPIRIT 2025 mục 3c") and x.endswith("[chờ bộ sinh phủ chuẩn]")
               for x in K.canh_bao_k17(md, "rct"))
    assert any(x.startswith("K17 Việt Nam") for x in K.loi_k17(md, "rct"))  # chuẩn khác vẫn chặn
    cosmin = _dc("# 2. PHƯƠNG PHÁP\n\n## 2.6. Công cụ thu thập\n\nBộ câu hỏi tự điền 30 câu; Cronbach's alpha; CVI.")
    assert any(x.startswith("K17 COSMIN 2021") for x in K.loi_k17(cosmin, "cross_sectional"))
    assert not any(x.startswith("K17 COSMIN") for x in K.canh_bao_k17(cosmin, "cross_sectional"))
    assert any(x.endswith("[chưa đối chiếu bảng gốc]") for x in K.canh_bao_k17(md, "non_randomized"))


def test_bo_kiem_nop_in_canh_bao_k17_khong_doi_ma_thoat(tmp_path):
    import json

    import kiem_de_cuong_nop_hoi_dong as KD  # noqa: PLC0415

    (tmp_path / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": {"design": "rct"}}}), encoding="utf-8",
                                              newline="\n")
    (tmp_path / "DE_CUONG_NOP_HOI_DONG_X.md").write_text(_dc(DAO_DUC + "Nội dung."), encoding="utf-8", newline="\n")
    canh = KD.canh_bao_k17(tmp_path, "X")
    assert canh and all("[chờ bộ sinh phủ chuẩn]" in x or "[chưa đối chiếu bảng gốc]" in x for x in canh)
    assert KD.canh_bao_k17(tmp_path, "KHONG-CO") == []


def test_lien_he_trong_de_cuong_nop_la_dia_chi_don_vi_khong_doi_email():
    # K7 cấm email/số điện thoại trong đề cương nộp ⇒ SPIRIT 3b / PRISMA-P 3a nhận địa chỉ đơn vị.
    md = _dc("## 6.1. Nhân lực và phân công nhiệm vụ\n\nChủ nhiệm đề tài; đơn vị chủ trì: Bệnh viện X, địa chỉ "
             "786 đường Y, TP. Hồ Chí Minh.")
    assert _kq(md, "rct")[("SPIRIT 2025", "3b")].trang_thai == "dat"
    assert _kq(md, "sr_ma")[("PRISMA-P 2015", "3a")].trang_thai == "dat"
    md2 = md.replace(", địa chỉ 786 đường Y, TP. Hồ Chí Minh", "")
    assert _kq(md2, "rct")[("SPIRIT 2025", "3b")].trang_thai == "thieu"
