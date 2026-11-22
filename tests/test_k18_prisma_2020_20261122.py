# -*- coding: utf-8 -*-
"""K18 — PRISMA 2020 theo từng mục cho BẢN THẢO tổng quan hệ thống/phân tích gộp (22/11/2026).

Bác sĩ 21–22/11/2026: mọi khâu tới «Viết báo cáo & công bố kết quả» phải đạt từng mục chuẩn quốc tế, cho mọi thiết kế.
Trước lượt này tổng quan hệ thống chỉ báo ⚪ «chưa đo được» cho cả chuẩn PRISMA 2020. Mỗi test khoá một hành vi đã đo
trên bản thảo G7 giả lập ZZCANARY-TONG-QUAN-GOP (docs/K18-PHAN-XU-BAN-THAO-20261122.md §3.4) — kể cả ba ca BÁO NHẦM
(đạt nhầm) đã sửa ở bộ kiểm và các dòng bộ sinh G7 thêm từ dữ kiện đã chốt.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import chuan_bao_cao_items as CBC  # noqa: E402
import kiem_ban_thao_tap_chi as KB  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as K  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import sinh_chuan_bao_cao_items as SINH  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402

TK = "systematic_review"

#: bản thảo tổng quan TỔNG HỢP đạt đủ 42 dòng PRISMA 2020 — test thay từng đoạn để đo một mục
TQ = {
    "tieu_de": "# Thuốc X và nhập viện vì suy tim ở người đái tháo đường: tổng quan hệ thống và phân tích gộp\n",
    "tom_tat": ("## TÓM TẮT\n\n"
                "**Mục tiêu:** Ước lượng hiệu quả của thuốc X lên nhập viện vì suy tim ở người đái tháo đường.\n\n"
                "**Phương pháp:** Tiêu chí nhận: thử nghiệm ngẫu nhiên ở người trưởng thành. Tìm PubMed, Embase và "
                "Cochrane CENTRAL đến ngày 30/06/2027. Nguy cơ sai lệch đánh giá bằng RoB 2. Gộp bằng mô hình hiệu ứng "
                "ngẫu nhiên.\n\n"
                "**Kết quả:** Gộp 12 thử nghiệm với 24.000 người tham gia: RR 0,70 (KTC 95% 0,62–0,79); I² 10%.\n\n"
                "**Hạn chế:** Hai thử nghiệm có nguy cơ sai lệch cao.\n\n"
                "**Kết luận:** Thuốc X giảm nhập viện vì suy tim.\n\n"
                "**Tài trợ:** Không có tài trợ bên ngoài.\n\n"
                "**Đăng ký:** PROSPERO CRD42027000001.\n"),
    "dat_van_de": ("## 1. ĐẶT VẤN ĐỀ\n\nSuy tim là biến chứng nặng của đái tháo đường [1]. Các tổng quan trước chưa "
                   "có ước lượng riêng cho người không có suy tim lúc đầu. Tổng quan này nhằm ước lượng hiệu quả của "
                   "thuốc X lên nhập viện vì suy tim ở người đái tháo đường.\n"),
    "phuong_phap": ("## 2. PHƯƠNG PHÁP\n\n"
                    "*Tiêu chí nhận:* thử nghiệm ngẫu nhiên ở người trưởng thành đái tháo đường; không giới hạn ngôn "
                    "ngữ. *Tiêu chí loại:* theo dõi dưới 24 tuần.\n\n"
                    "*Nguồn thông tin:* PubMed, Embase, Cochrane CENTRAL và ClinicalTrials.gov; tìm lần cuối ngày "
                    "30/06/2027.\n\n"
                    "*Chiến lược tìm:* câu lệnh đầy đủ cho từng cơ sở dữ liệu ở Phụ lục 1, gồm bộ lọc thử nghiệm ngẫu "
                    "nhiên.\n\n"
                    "*Chọn nghiên cứu:* hai người sàng lọc độc lập tiêu đề–tóm tắt rồi toàn văn.\n\n"
                    "*Trích dữ liệu:* hai người trích dữ liệu độc lập bằng biểu mẫu thử trước; liên hệ tác giả để xin "
                    "dữ liệu thiếu.\n\n"
                    "*Kết cục:* kết cục chính là nhập viện vì suy tim, định nghĩa theo từng thử nghiệm; chọn thời điểm "
                    "theo dõi dài nhất.\n\n"
                    "*Biến trích xuất:* thiết kế, cỡ mẫu, đặc điểm người tham gia, liều thuốc; thông tin không rõ được "
                    "giả định là không báo cáo.\n\n"
                    "*Nguy cơ sai lệch:* hai người đánh giá độc lập bằng RoB 2.\n\n"
                    "*Tổng hợp:* thước đo hiệu ứng là RR; gộp bằng mô hình hiệu ứng ngẫu nhiên (REML) trong R 4.4 "
                    "(metafor); không đồng nhất đo bằng I² và τ²; chỉ gộp khi các thử nghiệm đủ tương đồng lâm "
                    "sàng.\n\n"
                    "*Trình bày:* bảng đặc điểm các nghiên cứu và biểu đồ rừng cho từng tổng hợp.\n\n"
                    "*Không đồng nhất:* phân nhóm theo loại thuốc.\n\n"
                    "*Phân tích độ nhạy:* loại thử nghiệm nguy cơ sai lệch cao.\n\n"
                    "*Sai lệch công bố:* biểu đồ phễu và kiểm định Egger.\n\n"
                    "*Mức chắc chắn:* GRADE cho từng kết cục.\n\n"
                    "*Đăng ký:* PROSPERO CRD42027000001; đề cương công bố trên PROSPERO; không có sửa đổi so với đề "
                    "cương đã đăng ký.\n"),
    "ket_qua": ("## 3. KẾT QUẢ\n\n"
                "Tìm được 1.250 bản ghi; sau sàng lọc, 12 thử nghiệm được đưa vào (Hình 1, sơ đồ PRISMA).\n\n"
                "Ba nghiên cứu bị loại vì không tách được nhóm không suy tim [5–7].\n\n"
                "**Bảng 1. Đặc điểm các nghiên cứu được đưa vào**\n\n"
                "| Nghiên cứu | Thuốc | Biến cố/N nhánh X | Biến cố/N nhánh chứng | RoB 2 |\n|---|---|---|---|---|\n"
                "| A 2016 [2] | X1 | 40/2000 | 60/2000 | Thấp |\n\n"
                "Nguy cơ sai lệch của từng nghiên cứu trình bày ở Hình 2; Hình 3 là biểu đồ rừng.\n\n"
                "Mười hai thử nghiệm (k = 12) đóng góp vào tổng hợp chính; đa số có nguy cơ sai lệch thấp; thời gian "
                "theo dõi trung vị 3 năm.\n\n"
                "RR gộp 0,70 (KTC 95% 0,62–0,79); I² = 10%.\n\n"
                "Phân nhóm theo loại thuốc không cho thấy khác biệt (Q giữa nhóm p = 0,40).\n\n"
                "Phân tích độ nhạy loại thử nghiệm nguy cơ sai lệch cao cho RR 0,71.\n\n"
                "Biểu đồ phễu cân đối; kiểm định Egger p = 0,52, không gợi ý sai lệch công bố.\n\n"
                "Mức chắc chắn của bằng chứng theo GRADE là cao cho nhập viện vì suy tim.\n"),
    "ban_luan": ("## 4. BÀN LUẬN\n\nKết quả tương tự phân tích gộp trước [8].\n\n"
                 "Hạn chế của bằng chứng: hai thử nghiệm có nguy cơ sai lệch cao và ước lượng thiếu chính xác ở phân "
                 "nhóm nhỏ.\n\n"
                 "Hạn chế của tổng quan: chiến lược tìm không gồm tài liệu xám tiếng Việt.\n\n"
                 "Kết quả ủng hộ dùng thuốc X trong thực hành; cần thêm nghiên cứu ở người cao tuổi.\n"),
    "ket_luan": "## 5. KẾT LUẬN\n\nThuốc X giảm nhập viện vì suy tim.\n",
    "khai_bao": ("## KHAI BÁO\n\n**Tài trợ:** Không có tài trợ bên ngoài.\n\n"
                 "**Xung đột lợi ích:** Các tác giả không có xung đột lợi ích.\n\n"
                 "**Tính có sẵn dữ liệu:** Biểu mẫu trích dữ liệu, dữ liệu đã trích và mã phân tích R được công bố "
                 "trên OSF.\n"),
    "tltk": "## TÀI LIỆU THAM KHẢO\n\n[1] A. Một tổng quan hệ thống khác. 2024.\n",
}


def _tq(**thay) -> str:
    return "\n".join(v for k, v in dict(TQ, **thay).items() if v)


def _pp(cu: str, moi: str) -> str:
    assert cu in TQ["phuong_phap"], cu
    return TQ["phuong_phap"].replace(cu, moi)


def _kq(md: str, co_so_lieu=True):
    return K.doi_chieu(md, TK, che_do="ban_thao", co_so_lieu=co_so_lieu)


def _muc(kq, ma: str):
    ra = [r for r in kq["ket_qua"] if r.chuan == "PRISMA 2020" and r.ma == ma]
    assert ra, f"không thấy PRISMA 2020 {ma}"
    return ra[0]


# ───────────────────────────── kho nguyên văn (CC BY 4.0, bản PLOS Med) ─────────────────────────────
def test_kho_nguyen_van_prisma_2020_cc_by_du_42_dong_va_12_muc_tom_tat():
    assert CBC.GIAY_PHEP["PRISMA"] == CBC.GIAY_PHEP["PRISMA_TOM_TAT"] == "creativecommons.org/licenses/by/4.0"
    ma = [r[0] for r in CBC.PRISMA_2020_ITEMS]
    assert len(ma) == 42 and ma[0] == "1" and ma[-1] == "27" and len(set(ma)) == 42
    for con in ("10a", "10b", "13a", "13f", "16a", "16b", "20a", "20d", "23a", "23d", "24a", "24c"):
        assert con in ma, con
    assert set(ma) == set(TB._PRISMA_2020)
    assert [r[0] for r in CBC.PRISMA_2020_ABSTRACT_ITEMS] == [str(i) for i in range(1, 13)]
    assert dict((r[0], r[2]) for r in CBC.PRISMA_2020_ITEMS)["24a"] == "Registration and protocol"


def test_bo_sinh_doc_bang_prisma_rowspan_hang_phan_va_colspan():
    """Khuôn bảng PLOS Med: hàng phần (ô mã/nội dung rỗng hoặc colspan 2), chủ đề trải nhiều hàng bằng rowspan."""
    xml = ET.fromstring(
        "<table-wrap><table><tr><th>Section and topic</th><th>Item #</th><th>Checklist item</th><th>Loc</th></tr>"
        "<tr><td>Methods</td><td/><td/><td/></tr>"
        "<tr><td>Eligibility criteria</td><td>5</td><td>Specify the inclusion criteria.</td><td/></tr>"
        "<tr><td rowspan='2'>Data items<break/></td><td>10a</td><td>List all outcomes.</td><td/></tr>"
        "<tr><td>10b</td><td>List all other variables.</td><td/></tr>"
        "<tr><td colspan='2'>Other information</td><td/><td/></tr>"
        "<tr><td>Support</td><td>25</td><td>Describe sources of support.</td><td/></tr></table></table-wrap>")
    assert SINH._muc_prisma_bang(xml) == [
        ("5", "Methods", "Eligibility criteria", "Specify the inclusion criteria."),
        ("10a", "Methods", "Data items", "List all outcomes."),
        ("10b", "Methods", "Data items", "List all other variables."),
        ("25", "Other information", "Support", "Describe sources of support."),
    ]


def test_muc_2_kem_nguyen_van_12_muc_prisma_for_abstracts():
    m2 = next(m for m in TB.danh_sach_muc_ban_thao("PRISMA 2020", TK) if m.ma == "2")
    assert "PRISMA 2020 for Abstracts" in m2.nguyen_van and "A12. Provide the register name" in m2.nguyen_van


# ───────────────────────────── chấm theo mục ─────────────────────────────
def test_tong_quan_dung_prisma_2020_moi_muc_co_tieu_chi_ban_thao_tong_hop_dat_du_42():
    kq = _kq(_tq())
    assert [c for c, _ in kq["chuan"]] == ["PRISMA 2020"] and not kq["chua_do"] and not kq["cau_truc"]
    ket = {r.ma: r for r in kq["ket_qua"]}
    assert len(ket) == 42 and all(m.yeu_to for m in TB._muc_prisma())
    sai = {ma: r.thieu for ma, r in ket.items() if r.trang_thai != "dat"}
    assert not sai, sai


def test_ban_nhap_chua_so_lieu_muc_ket_qua_prisma_chua_do_khong_bao_gio_dat():
    md = _tq(ket_qua="## 3. KẾT QUẢ\n\n[CẦN KẾT QUẢ THẬT — sàng lọc, đặc điểm, ước lượng gộp]\n")
    kq = _kq(md, co_so_lieu=None)
    assert kq["co_so_lieu"] is False
    for ma in ("16a", "16b", "17", "18", "19", "20a", "20b", "21", "22", "23a", "23d"):
        assert _muc(kq, ma).trang_thai == "chua_do", ma
    assert _muc(kq, "6").trang_thai == "dat" and _muc(kq, "13d").trang_thai == "dat"  # phương pháp vẫn chấm


def test_tom_tat_thieu_ten_co_quan_dang_ky_va_ngay_tim():
    tt = TQ["tom_tat"].replace("PROSPERO CRD42027000001", "CRD42027000001").replace(" đến ngày 30/06/2027", "")
    r = _muc(_kq(_tq(tom_tat=tt)), "2")
    assert r.trang_thai == "thieu"
    assert set(r.thieu) == {"ngày tìm cuối (A4)", "cơ quan và số đăng ký (A12)"}


def test_nguon_chi_co_so_dang_ky_thu_nghiem_khong_thay_co_so_du_lieu():
    """Báo nhầm 22/11/2026: «search unpublished (clinicaltrials.gov)» ở bảng sai lệch từng làm mục 6 đạt."""
    pp = _pp("*Nguồn thông tin:* PubMed, Embase, Cochrane CENTRAL và ClinicalTrials.gov",
             "*Nguồn thông tin:* ClinicalTrials.gov và WHO ICTRP")
    r = _muc(_kq(_tq(phuong_phap=pp)), "6")
    assert r.trang_thai == "thieu" and "cơ sở dữ liệu/sổ đăng ký đã tìm" in r.thieu
    pp2 = _pp("; tìm lần cuối ngày 30/06/2027", "")
    assert "ngày tìm cuối" in _muc(_kq(_tq(phuong_phap=pp2)), "6").thieu
    pp3 = _pp("tìm lần cuối ngày 30/06/2027", "tìm lần cuối ngày 2027-06-30")  # ngày ISO của G1 search_last_date
    assert _muc(_kq(_tq(phuong_phap=pp3)), "6").trang_thai == "dat"


def test_mo_ta_chien_luoc_tim_khong_thay_cau_lenh_day_du():
    pp = _pp("câu lệnh đầy đủ cho từng cơ sở dữ liệu ở Phụ lục 1, gồm bộ lọc thử nghiệm ngẫu nhiên",
             "kết hợp MeSH và từ khoá, bộ lọc thử nghiệm ngẫu nhiên")
    assert "chiến lược tìm đầy đủ (câu lệnh hoặc dẫn phụ lục)" in _muc(_kq(_tq(phuong_phap=pp)), "7").thieu
    pp2 = pp + "\n(\"SGLT2 inhibitors\"[MeSH] AND \"heart failure\"[tiab]) — PubMed, không giới hạn năm.\n"
    assert _muc(_kq(_tq(phuong_phap=pp2)), "7").trang_thai == "dat"


def test_nguy_co_sai_lech_phai_cung_doan_so_nguoi_doc_lap_va_cong_cu():
    """Bộ sinh G7 từng viết khối §3d liền một đoạn: «RoB 2» (dòng biến trích xuất) + «Hai người … độc lập» (dòng chọn
    nghiên cứu) làm mục 11 «đạt» khi chưa ai chốt người đánh giá nguy cơ sai lệch."""
    pp = _pp("*Nguy cơ sai lệch:* hai người đánh giá độc lập bằng RoB 2.", "*Biến nguy cơ sai lệch:* RoB 2 tổng.")
    assert _muc(_kq(_tq(phuong_phap=pp)), "11").trang_thai == "thieu"
    assert _muc(_kq(_tq()), "11").trang_thai == "dat"


def test_bang_dac_diem_nen_nguoi_tham_gia_khong_la_dac_diem_tung_nghien_cuu():
    """Báo nhầm 22/11/2026: «Bảng 1. Đặc điểm nền người tham gia» (khuôn nghiên cứu gốc) từng làm mục 17 đạt."""
    kq_moi = TQ["ket_qua"].replace("Bảng 1. Đặc điểm các nghiên cứu được đưa vào",
                                   "Bảng 1. Đặc điểm nền người tham gia")
    r = _muc(_kq(_tq(ket_qua=kq_moi)), "17")
    assert r.trang_thai == "thieu" and "đặc điểm các nghiên cứu" in r.thieu


def test_so_bang_2_tren_3_khong_la_so_bien_co_tren_so_nguoi():
    """Báo nhầm 22/11/2026: «biến kết cục … nằm ở Bảng 2/3» từng làm «thống kê tóm tắt từng nhóm» của mục 19 đạt."""
    kq_moi = (TQ["ket_qua"].replace("| A 2016 [2] | X1 | 40/2000 | 60/2000 | Thấp |",
                                    "| A 2016 [2] | X1 | — | — | Thấp |")
              + "\nBiến kết cục nằm ở Bảng 2/3; tìm lần cuối 21/11/2026.\n")
    r = _muc(_kq(_tq(ket_qua=kq_moi)), "19")
    assert r.trang_thai == "thieu" and any("từng nhóm" in t for t in r.thieu)


def test_ket_qua_phan_nhom_chi_doi_khi_phuong_phap_co_phan_nhom_khong_lay_tu_ban_luan():
    pp = _pp("*Không đồng nhất:* phân nhóm theo loại thuốc.",
             "*Không đồng nhất:* không khảo sát nguyên nhân không đồng nhất.")
    kq_moi = TQ["ket_qua"].replace("Phân nhóm theo loại thuốc không cho thấy khác biệt (Q giữa nhóm p = 0,40).\n\n", "")
    # câu khẳng định về NGHIÊN CỨU KHÁC ở Bàn luận không kích hoạt mục 20c (phạm vi chương: Phương pháp + Kết quả)
    bl = (TQ["ban_luan"].replace("ở phân nhóm nhỏ", "ở các thử nghiệm nhỏ")
          + "\nPhân tích gộp trước [8] có phân nhóm theo liều.\n")
    kq = _kq(_tq(phuong_phap=pp, ket_qua=kq_moi, ban_luan=bl))
    assert _muc(kq, "20c").trang_thai == "khong_ap_dung"
    assert _muc(kq, "13e").trang_thai == "dat"  # nêu rõ không khảo sát là đã báo cáo
    kq2 = _kq(_tq(ket_qua=kq_moi))  # phương pháp có phân nhóm mà kết quả không có ⇒ thiếu
    assert _muc(kq2, "20c").trang_thai == "thieu"


def test_sai_lech_cong_bo_phai_co_nhan_dinh_khong_chi_hinh_pheu():
    kq_moi = TQ["ket_qua"].replace("Biểu đồ phễu cân đối; kiểm định Egger p = 0,52, không gợi ý sai lệch công bố.",
                                   "Hình 4. Funnel plot.")
    r = _muc(_kq(_tq(ket_qua=kq_moi)), "21")
    assert r.trang_thai == "thieu" and r.thieu == ["nhận định/kết quả kiểm định"]


def test_khong_dang_ky_va_khong_de_cuong_duoc_neu_ro_la_dat():
    pp = _pp("*Đăng ký:* PROSPERO CRD42027000001; đề cương công bố trên PROSPERO; không có sửa đổi so với đề cương "
             "đã đăng ký.", "*Đăng ký:* tổng quan không được đăng ký và không soạn đề cương; không có sửa đổi so với "
                            "đề cương vì không có đề cương.")
    kq = _kq(_tq(phuong_phap=pp, tom_tat=TQ["tom_tat"].replace("**Đăng ký:** PROSPERO CRD42027000001.\n", "")))
    assert _muc(kq, "24a").trang_thai == "dat" and _muc(kq, "24b").trang_thai == "dat"


def test_k18_kiem_tap_chi_bao_vi_pham_prisma_theo_muc():
    md = _tq(ket_qua=TQ["ket_qua"].replace("Ba nghiên cứu bị loại vì không tách được nhóm không suy tim [5–7].\n\n",
                                           ""))
    k = KB.k18(md, TK, nop=True)
    assert k["tom_tat"]["PRISMA 2020"].get("thieu") == 1
    assert any(x.startswith("K18 PRISMA 2020 mục 16b") for x in k["vi_pham"])


# ───────────────────────────── bộ sinh G7: dữ kiện đã chốt, không câu mẫu ─────────────────────────────
_SAP_TQ = ("### §3 THỐNG KÊ MÔ TẢ\n\n- Mô tả đặc điểm các nghiên cứu được đưa vào (thiết kế, cỡ mẫu), PRISMA 2020\n\n"
           "### §5 TỔNG HỢP ĐỊNH LƯỢNG\n\n- **Thước đo hiệu ứng:** RR (nguy cơ tương đối)\n"
           "- **Mô hình gộp:** hiệu ứng ngẫu nhiên (REML) là chính *(điền sẵn từ quyết định đã chốt, PI sửa nếu cần)*\n"
           "- **Mức chắc chắn:** [CẦN — PI chọn]\n- **Không đồng nhất:** Không áp dụng\n\n"
           "### §7 PHÂN NHÓM\n\n- **Nhóm nhỏ tiền định:** Loại thuốc\n\n"
           "### §11 DUMMY TABLES\n\n**Bảng 1, Đặc điểm các nghiên cứu được đưa vào (PRISMA 2020):**\n\n"
           "**Bảng MT1, Kết quả trả lời Mục tiêu 1 (MT1): X**\n\n### §12 ALPHA\n")


def _de_tai(tmp_path, g1=None, g7=None):
    gp = {"G1": g1 or {}, **({"G7": g7} if g7 else {})}
    (tmp_path / "study_meta.json").write_text(json.dumps({"gate_params": gp}, ensure_ascii=False), encoding="utf-8",
                                              newline="\n")
    (tmp_path / "G4_A5_SAP_FINAL_X.md").write_text(_SAP_TQ, encoding="utf-8", newline="\n")
    return tmp_path


_G1_TQ = {"information_sources": ["PubMed/MEDLINE", "Embase"], "search_last_date": "2027-06-30",
          "search_strategy": "MeSH và từ khoá; bộ lọc RCT Cochrane",
          "study_selection_process": "Hai người sàng lọc độc lập tiêu đề–tóm tắt rồi toàn văn (G1 đã chốt)"}


def test_g7_khoi_tong_quan_chep_nguyen_chu_g1_sap_g5_moi_du_kien_mot_doan(tmp_path):
    d = _de_tai(tmp_path, _G1_TQ)
    bien = [{"variable": "study_id", "label": "Mã thử nghiệm"},
            {"variable": "n_can_thiep", "label": "Số người nhánh X"},
            {"variable": "rob2_tong", "label": "RoB 2 — đánh giá chung"}]
    khoi = G7._khoi_tong_quan_g7(d, "X", bien)
    van = "\n".join(khoi)
    assert khoi[0].startswith("**§3d ") and "PRISMA 2020 mục 5–15" in khoi[0]
    assert "*Nguồn thông tin:* PubMed/MEDLINE; Embase; tìm lần cuối ngày 2027-06-30." in van
    assert "*Chọn nghiên cứu:* Hai người sàng lọc độc lập tiêu đề–tóm tắt rồi toàn văn." in van  # bỏ chú thích «(G1 …)»
    assert "Số người nhánh X; RoB 2 — đánh giá chung." in van and "Mã thử nghiệm" not in van
    assert "*Thước đo hiệu ứng:* RR (nguy cơ tương đối)." in van and "*Nhóm nhỏ tiền định:* Loại thuốc." in van
    assert "*Mô hình gộp:* hiệu ứng ngẫu nhiên (REML) là chính." in van  # bỏ chú thích «điền sẵn…»
    assert "Mức chắc chắn" not in van and "Không đồng nhất" not in van  # ô [CẦN] và «Không áp dụng» ⇒ bỏ dòng
    assert ("*Trình bày kết quả:* mô tả đặc điểm các nghiên cứu được đưa vào (thiết kế, cỡ mẫu); bảng đặc điểm các "
            "nghiên cứu được đưa vào." in van) and "MT1" not in van and "PRISMA 2020)" not in van
    # mỗi dữ kiện một đoạn (yếu tố «cùng đoạn» của K18 không ghép chữ hai dòng)
    assert all(khoi[i] == "" for i in range(2, len(khoi), 2)) and all(khoi[i] for i in range(1, len(khoi), 2))
    rong = tmp_path / "rong"
    rong.mkdir()
    assert G7._khoi_tong_quan_g7(rong, "X", []) == []  # không study_meta, không SAP ⇒ không in gì


def test_g7_tom_tat_tong_quan_nguon_tong_hop_tai_tro_chi_khi_da_chot(tmp_path):
    d = _de_tai(tmp_path, _G1_TQ)
    tt = "\n".join(G7._tom_tat_tong_quan_g7(d, "X"))
    assert "**Information sources:** PubMed/MEDLINE; Embase; tìm lần cuối ngày 2027-06-30." in tt
    assert "**Synthesis methods:** RR (nguy cơ tương đối); hiệu ứng ngẫu nhiên (REML) là chính." in tt
    assert "Funding" not in tt  # G7 chưa khai ⇒ không tự viết
    d2 = _de_tai(tmp_path, _G1_TQ, g7={"funding_declared": "Không có tài trợ bên ngoài"})
    assert "**Funding:** Không có tài trợ bên ngoài." in "\n".join(G7._tom_tat_tong_quan_g7(d2, "X"))


def test_g7_khoi_tong_quan_lam_muc_6_8_10b_13c_dat_khi_ghep_vao_ban_thao(tmp_path):
    """Vòng kín: khối bộ sinh in ra phải đủ cho K18 nhận mục 6, 8, 10b, 13c (không còn ở đoạn khác của bản thảo)."""
    d = _de_tai(tmp_path, _G1_TQ)
    khoi = "\n".join(G7._khoi_tong_quan_g7(d, "X", [{"variable": "n_can_thiep", "label": "Số người nhánh X"}]))
    pp = "## 2. PHƯƠNG PHÁP\n\n" + khoi + "\n"
    kq = _kq(_tq(phuong_phap=pp))
    for ma in ("6", "8", "13c", "12", "13e"):
        assert _muc(kq, ma).trang_thai == "dat", (ma, _muc(kq, ma).thieu)
    # 10b: «biến khác được trích» do khối in; «giả định khi thiếu» nằm ở §6 (dữ liệu thiếu SAP §6) — không có ở đây
    assert _muc(kq, "10b").thieu == ["giả định khi thiếu/không rõ"]
    assert _muc(kq, "11").trang_thai == "thieu"  # chưa ai chốt người đánh giá nguy cơ sai lệch


@pytest.mark.parametrize("ma", ["16a", "17", "19", "21", "22"])
def test_muc_ket_qua_prisma_co_so_lieu(ma):
    """Mục thuộc trọn chương Kết quả: yếu tố số liệu phải có — bản nộp thiếu là thiếu, không «chưa đo»."""
    assert _muc(_kq(_tq(ket_qua="## 3. KẾT QUẢ\n\nKhông có nội dung kết quả.\n")), ma).trang_thai == "thieu"
