"""Kiểm `tools/ho_so_dtcs_bvqy175.py` — hồ sơ đăng ký chủ trì đề tài cơ sở BVQY175 (DKCT.01–03).

KHÔNG phụ thuộc bộ mẫu thật (ngoài git, CI không có) hay sổ lý lịch thật: mọi test dựng bộ mẫu .docx GIẢ mang đúng
nhãn/ô kiểm (trường FORMCHECKBOX thật của Word) của mẫu bệnh viện, một đề tài giả và sổ lý lịch giả trong `tmp_path`;
biến môi trường trỏ cả hai vị trí vào `tmp_path` nên không bao giờ chạm thư mục «Đề tài NCKH» thật. Số định danh,
điện thoại, email đều là giá trị giả (miền example.org).

Luật được canh:
  * Không bịa tiền/định mức/khoán chi/sản phẩm — các ô đó là «[CẦN CHỦ NHIỆM ẤN ĐỊNH]».
  * Mục 16 chỉ gồm tài liệu được trích trong thuyết minh, đánh số lại theo thứ tự xuất hiện; mục `loai_bo` và mục
    chưa xác minh mang nhãn [CẦN…]; số trong văn bản đổi theo.
  * Tổng quan xếp «Ngoài nước/Trong nước/Luận giải» theo tiêu đề và nhãn đậm đầu đoạn; «chiến lược tìm kiếm» bỏ.
  * Dữ liệu cá nhân chỉ ở sổ lý lịch cá nhân; JSON chính không chứa; mọi lệnh ghi từ chối khi đích đi vào git.
  * Mẫu chỉ có bản .doc thì không điền (không điền bừa); chạy lại `dung` sao lưu tệp người đã sửa tay.
  * Văn bản nộp không mang dấu vết máy; mã câu hỏi «G1» do chính văn bản định nghĩa không bị coi là ký hiệu cổng.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

docx = pytest.importorskip("docx")
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

from tools import ho_so_dtcs_bvqy175 as hs  # noqa: E402

STUDY = "de-tai-gia-dtcs"
CCCD_GIA = "099000111222"  # bimat-mien: số giả cho test, không phải định danh thật
DT_GIA = "0900000001"  # bimat-mien: số giả cho test
EMAIL_GIA = "bacsi.gia@example.org"
EMAIL_BAN = "nckh.gia@example.org"
CHAM = "." * 60

# ---------------------------------------------------------------------------
# Bộ mẫu GIẢ
# ---------------------------------------------------------------------------


def _hop(p) -> None:
    """Thêm một trường FORMCHECKBOX thật (fldChar + ffData/checkBox) vào đoạn."""
    r = p.add_run()
    bat_dau = OxmlElement("w:fldChar")
    bat_dau.set(qn("w:fldCharType"), "begin")
    ff = OxmlElement("w:ffData")
    cb = OxmlElement("w:checkBox")
    cb.append(OxmlElement("w:sizeAuto"))
    mac_dinh = OxmlElement("w:default")
    mac_dinh.set(qn("w:val"), "0")
    cb.append(mac_dinh)
    ff.append(cb)
    bat_dau.append(ff)
    r._r.append(bat_dau)
    r2 = p.add_run()
    it = OxmlElement("w:instrText")
    it.text = " FORMCHECKBOX "
    r2._r.append(it)
    r3 = p.add_run()
    ket = OxmlElement("w:fldChar")
    ket.set(qn("w:fldCharType"), "end")
    r3._r.append(ket)


def _doan(doc, *phan) -> None:
    """Đoạn gồm các phần chữ; phần None = một ô kiểm."""
    p = doc.add_paragraph()
    for x in phan:
        if x is None:
            _hop(p)
        else:
            p.add_run(x)


def _bang(doc, hang: list[list[str]]) -> None:
    t = doc.add_table(rows=len(hang), cols=max(len(h) for h in hang))
    for i, h in enumerate(hang):
        for j, c in enumerate(h):
            t.cell(i, j).text = c


def _mau_thuyet_minh(p: Path) -> None:
    d = docx.Document()
    for x in ("Mẫu DTCS-DKCT.02-TM", "I. THÔNG TIN CHUNG VỀ ĐỀ TÀI", "1. Tên đề tài", CHAM, CHAM,
              "- Mã số (được cấp khi Hồ sơ thông qua):", "2. Thời gian thực hiện: ……….tháng",
              "(Từ tháng         /20… đến tháng        /20…)", "3. Cấp quản lý: Cấp cơ sở",
              "4. Tổng kinh phí thực hiện: ........................... triệu đồng, trong đó:"):
        _doan(d, x)
    _bang(d, [["Nguồn", "Kinh phí (triệu đồng)"], ["- Từ ngân sách nhà nước", ""]])
    _doan(d, "5. Đề nghị phương thức khoán chi:")
    _doan(d, "6. Loại đề tài:")
    _doan(d, None, " Độc lập")
    _doan(d, "7. Lĩnh vực:")
    _doan(d, "\t", None, "  Tự nhiên;    \t", None, "  Nông nghiệp; ")
    _doan(d, "\t", None, " Kỹ thuật và công nghệ;  \t", None, "  Y, dược.")
    for muc in ("8. Chủ nhiệm đề tài", "9. Thư ký khoa học của đề tài"):
        _doan(d, muc)
        _doan(d, "Họ và tên: ................................... Số định danh cá nhân/CMTQĐ: ......................")
        _doan(d, "Ngày, tháng, năm sinh: ........................ Giới tính:  Nam  ", None, " / Nữ: ", None)
        for x in ("Học hàm, học vị/Trình độ chuyên môn: ...........................................",
                  "Chức danh SQCM-KT-NV: ...............................", "Cấp bậc:………………………………",
                  "Chức vụ: ...............................", "Điện thoại: ……………… E-mail: ..................",
                  "Tên đơn vị đang công tác: Khoa …/Bệnh viện Quân y 175"):
            _doan(d, x)
    for x in ("10. Đơn vị chủ trì đề tài (Khoa, Phòng, Ban, Trung tâm, Viện)", "Tên đơn vị chủ trì thực hiện đề tài: ",
              "Họ và tên thủ trưởng đơn vị: ", "Tên đơn vị chủ quản đề tài: Bệnh viện Quân y 175",
              "11. Các đơn vị phối hợp chính thực hiện đề tài (nếu có)", "1. Tên đơn vị 1: " + CHAM,
              "12. Thành viên thực hiện đề tài"):
        _doan(d, x)
    _bang(d, [["TT", "Họ và tên, học hàm, học vị", "Chức danh thực hiện đề tài", "Tổ chức công tác"],
              ["1", "", "Chủ nhiệm đề tài", ""], ["2", "", "Thư ký khoa học", ""], ["3", "", "Thành viên chính", ""],
              ["…", "", "Thành viên chính", ""]])
    for x in ("II. MỤC TIÊU, NỘI DUNG VÀ PHƯƠNG ÁN TỔ CHỨC THỰC HIỆN ĐỀ TÀI",
              "13. Mục tiêu của đề tài (Bám sát và cụ thể hoá định hướng mục tiêu theo đề xuất)", CHAM, CHAM,
              "14. Tình trạng của đề tài"):
        _doan(d, x)
    _doan(d, None, " Mới")
    for x in ("15. Tổng quan tình hình nghiên cứu", "15.1. Đánh giá tổng quan tình hình nghiên cứu",
              "Ngoài nước (Phân tích, đánh giá được những công trình nghiên cứu có liên quan)", CHAM, CHAM,
              "Trong nước (Phân tích, đánh giá tình hình nghiên cứu trong nước)", CHAM, CHAM,
              "15.2. Luận giải về những nội dung cần nghiên cứu của đề tài", "(Trên cơ sở đánh giá …)", CHAM, CHAM,
              "16. Liệt kê danh mục các công trình nghiên cứu, tài liệu có liên quan",
              "(Tên công trình, tác giả, nơi và năm công bố)", CHAM, CHAM,
              "17. Nội dung nghiên cứu khoa học và triển khai thực nghiệm của đề tài và phương án thực hiện",
              "(Liệt kê và mô tả chi tiết:", "Nội dung 1 : " + CHAM, "Công việc 1.1: " + CHAM, CHAM,
              "Nội dung 2 : " + CHAM,
              "18. Phương án phối hợp với các đơn vị nghiên cứu và cơ sở sản xuất trong nước", "(Trình bày …)", CHAM,
              "19. Phương án hợp tác quốc tế (nếu có)", "(Trình bày …)", CHAM,
              "20. Phương án thuê chuyên gia (nếu có)", "20.1. Thuê chuyên gia trong nước", "21. Tiến độ thực hiện"):
        _doan(d, x)
    _bang(d, [["", "Các nội dung, công việc", "Kết quả phải đạt", "Thời gian", "Cá nhân, đơn vị chủ trì*",
               "Dự kiến kinh phí"], ["(1)", "(2)", "(3)", "(4)", "(5)", "(6)"], ["1", "Nội dung 1", "", "", "", ""],
              ["", "- Công việc 1.1", "", "", "", ""]])
    for x in ("III. SẢN PHẨM KH&CN CỦA ĐỀ TÀI", "22. Sản phẩm KH&CN chính của đề tài và yêu cầu chất lượng cần đạt",
              "22.1. Kết quả tham gia đào tạo sau đại học", "22.2. Trình độ khoa học của sản phẩm", CHAM,
              "22.3. Mức chất lượng các sản phẩm", CHAM, "23. Khả năng ứng dụng và phương thức chuyển giao",
              "23.1. Khả năng về thị trường", CHAM, "23.2. Khả năng ứng dụng", CHAM, "23.3. Khả năng liên doanh", CHAM,
              "23.4. Mô tả phương thức chuyển giao", CHAM,
              "24. Phạm vi và địa chỉ (dự kiến) ứng dụng các kết quả của đề tài", CHAM,
              "25. Tác động và lợi ích mang lại của kết quả nghiên cứu", "25.1. Đối với quân sự", CHAM,
              "25.2. Đối với lĩnh vực KH&CN có liên quan", CHAM, "25.3 Đối với đơn vị chủ trì", CHAM,
              "26. Phương án trang bị thiết bị", "26.1. Phương án trang bị tài sản",
              "a) Bố trí trong số thiết bị máy móc hiện có", CHAM, "b) Điều chuyển thiết bị máy móc (nếu có)", CHAM,
              "c) Thuê thiết bị máy móc", "d) Mua sắm mới thiết bị máy móc", "26.2. Đề xuất phương án xử lý tài sản",
              "………………………………", "V. NHU CẦU KINH PHÍ THỰC HIỆN ĐỀ TÀI VÀ NGUỒN KINH PHÍ",
              "(Giải trình chi tiết trong phụ lục kèm theo)", "Đơn vị tính: triệu đồng", "PHỤ LỤC – TMĐT",
              "DỰ TOÁN KINH PHÍ THỰC HIỆN ĐỀ TÀI", "Đơn vị: triệu đồng"):
        _doan(d, x)
    d.save(str(p))


def _mau_dang_ky(p: Path) -> None:
    d = docx.Document()
    _doan(d, "Mẫu DTCS-DKCT.01-DK")
    t = d.add_table(rows=2, cols=2)
    t.cell(0, 0).text = "BỆNH VIỆN QUÂN Y 175"
    t.cell(0, 0).add_paragraph("…")
    t.cell(0, 1).text = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"
    for x in ("Kính gửi: Phòng Khoa học quân sự/Bệnh viện Quân y 175.",
              "Căn cứ Thông tư số 05/2024/TT-BQP …",
              "…1 kính đề nghị Phòng Khoa học Quân sự xem xét và tổ chức đánh giá:",
              "a) Đơn vị đăng ký chủ trì thực hiện nhiệm vụ", "(Tên Khoa, phòng Ban, Trung Tâm, Viện đăng ký chủ trì)",
              "b) Cá nhân đăng ký chủ nhiệm nhiệm vụ", " (Họ tên, học hàm, học vị, cấp bậc, chức vụ cá nhân)",
              "Đăng ký chủ trì thực hiện nhiệm vụ KH&CN cấp Bệnh viện: ", CHAM, CHAM, "Hồ sơ gồm có:",
              f"Số lượng 07 bộ theo quy định trong đó có 01 bản điện tử gửi về địa chỉ email {EMAIL_BAN}"):
        _doan(d, x)
    d.save(str(p))


def _mau_ly_lich(p: Path, dien: dict | None = None) -> None:
    """Mẫu DKCT.03 GIẢ (bảng 5 cột, dòng nhãn gộp ô); `dien` ⇒ bản ĐÃ ĐIỀN dùng cho `nap-ly-lich`."""
    dien = dien or {}
    d = docx.Document()
    _doan(d, "Mẫu DTCS-DKCT.03-LLKH")
    _doan(d, "LÝ LỊCH KHOA HỌC")
    _doan(d, "     ĐĂNG KÝ ", "CHỦ NHIỆM NHIỆM VỤ:", "\t", "\t", "ĐĂNG KÝ ", "THAM GIA THỰC HIỆN ", "NHIỆM VỤ", ":")
    hang = [
        [f"1. Họ và tên: {dien.get('ho_ten', '')}"],
        [f"2. Ngày/tháng/năm sinh: {dien.get('ngay_sinh', '')}          Nam/Nữ: {dien.get('gioi_tinh', '')}",
         f"3. Số định danh cá nhân/CCCD: {dien.get('cccd', '')}"],
        ["4. Học hàm:            Năm được phong học hàm:", "    Học vị:          Năm đạt học vị:"],
        ["5. Chức danh nghiên cứu:", "   Chức vụ:"],
        [f"6. Điện thoại: Tổ chức:        Mobile: {dien.get('mobile', '')}",
         f"7. Địa chỉ:          E-mail: {dien.get('email', '')}"],
        ["8. Nơi làm việc của cá nhân đăng ký chủ nhiệm/thành viên chính: ",
         f"     Tên tổ chức\xa0: {dien.get('to_chuc', '')}", "     Tên người lãnh đạo: ", "     Điện thoại:",
         "     Địa chỉ: "],
        ["9. Quá trình đào tạo"],
    ]
    t = d.add_table(rows=0, cols=5)

    def dong_nhan(cac_doan: list[str]) -> None:
        r = t.add_row()
        o = r.cells[0].merge(r.cells[4])
        o.text = cac_doan[0]
        for x in cac_doan[1:]:
            o.add_paragraph(x)

    def dong_o(gia_tri: list[str]) -> None:
        r = t.add_row()
        for j, v in enumerate(gia_tri):
            r.cells[j].text = v

    for h in hang:
        dong_nhan(h)
    dong_o(["Bậc đào tạo", "Nơi đào tạo", "Chuyên môn", "Năm tốt nghiệp"])
    dao_tao = dien.get("dao_tao") or []
    dong_o(dao_tao[0] if len(dao_tao) > 0 else ["Đại học", "", "", ""])
    dong_o(dao_tao[1] if len(dao_tao) > 1 else ["Thạc sĩ", "", "", ""])
    dong_o(["Tiến sĩ", "", "", ""])
    dong_nhan(["10. Quá trình công tác"])
    dong_o(["Thời gian (Từ năm ... đến năm...)", "Vị trí công tác", "Tổ chức công tác", "Địa chỉ tổ chức"])
    cong_tac = dien.get("cong_tac") or []
    for k in range(max(2, len(cong_tac))):
        dong_o(cong_tac[k] if k < len(cong_tac) else ["", "", "", ""])
    for tieu_de, cot in (("11. Các công trình công bố chủ yếu", ["TT", "Tên công trình", "Vai", "Nơi", "Năm"]),
                         ("12. Số lượng văn bằng bảo hộ", ["TT", "Tên và nội dung văn bằng", "Năm cấp"]),
                         ("13. Số công trình được áp dụng trong thực tiễn", ["TT", "Tên công trình", "Hình thức",
                                                                             "Thời gian"])):
        dong_nhan([tieu_de])
        dong_o(cot)
        dong_o([""] * len(cot))
    dong_nhan(["14. Các nhiệm vụ KH&CN đã chủ trì hoặc tham gia"])
    dong_o(["Tên nhiệm vụ KH&CN đã chủ trì", "Thời gian", "Thuộc Chương trình", "Tình trạng"])
    dong_o(["", "", "", ""])
    dong_o(["Tên nhiệm vụ KH&CN đã tham gia", "Thời gian", "Thuộc Chương trình", "Tình trạng"])
    dong_o(["", "", "", ""])
    dong_nhan(["15. Giải thưởng trong lĩnh vực khoa học và công nghệ"])
    dong_o(["TT", "Hình thức và nội dung giải thưởng", "Năm tặng thưởng"])
    dong_o(["", "", ""])
    dong_nhan(["16. Thành tựu hoạt động KH&CN và sản xuất kinh doanh khác", "(liên quan …)"])
    ky = d.add_table(rows=1, cols=2)
    ky.cell(0, 0).text = "XÁC NHẬN CỦA CƠ QUAN CÔNG TÁC"
    ky.cell(0, 1).text = "CHỦ NHIỆM ĐỀ TÀI"
    ky.cell(0, 1).add_paragraph("(chữ ký và họ tên)")
    d.save(str(p))


def _mau_pdx(p: Path) -> None:
    d = docx.Document()
    for t in ("Mẫu DTCS-XDNV.01-PDX", "BỆNH VIỆN QUÂN Y 175\tCỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
              "…(K-P-B-TT-V)\tĐộc lập – Tự do – Hạnh phúc",
              "ĐỀ XUẤT NHIỆM VỤ NGHIÊN CỨU KHOA HỌC VÀ CÔNG NGHỆ CẤP BỆNH VIỆN",
              "Tên nhiệm vụ KHCN:", "Lý do đề xuất (Tính cấp thiết):", "Mục tiêu:",
              "Các kết quả chính và các chỉ tiêu cần đạt:", "Các nội dung chính cần thực hiện:",
              "Dự kiến cơ quan, đơn vị ứng dụng các kết quả:", "Phương án sử dụng kết quả:",
              "Thời gian cần thực hiện:", "Nhu cầu kinh phí cần thực hiện:",
              "\tChỉ huy cơ quan, đơn vị xác nhận\tChủ nhiệm đề xuất nhiệm vụ"):
        d.add_paragraph(t)
    d.save(str(p))


@pytest.fixture(autouse=True)
def _cach_ly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Bộ mẫu + sổ lý lịch GIẢ cho MỌI test — không bao giờ chạm vị trí thật."""
    mau = tmp_path / "mau_dtcs"
    (mau / "docx").mkdir(parents=True)
    _mau_dang_ky(mau / "docx" / f"{hs.TEN_TEP_MAU['dang_ky']}.docx")
    _mau_thuyet_minh(mau / "docx" / f"{hs.TEN_TEP_MAU['thuyet_minh']}.docx")
    _mau_ly_lich(mau / "docx" / f"{hs.TEN_TEP_MAU['ly_lich']}.docx")
    _mau_pdx(mau / "docx" / f"{hs.TEN_TEP_MAU['de_xuat']}.docx")
    so = tmp_path / "ho_so_ca_nhan"
    monkeypatch.setenv(hs.ENV_MAU, str(mau))
    monkeypatch.setenv(hs.ENV_CA_NHAN, str(so))
    return {"mau": mau, "so": so / hs.TEN_SO_CA_NHAN}


# ---------------------------------------------------------------------------
# Đề tài GIẢ
# ---------------------------------------------------------------------------

DE_CUONG = """# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## THÔNG TIN CHUNG VỀ ĐỀ TÀI

| Mục | Nội dung |
|---|---|
| Tên đề tài | Đề tài giả |
| Chủ nhiệm đề tài | BS.CKI Trần Văn Giả – Khoa Giả A, Bệnh viện Quân y 175 |
| Đơn vị chủ trì | Khoa Giả A, Bệnh viện Quân y 175, Thành phố Hồ Chí Minh |
| Kinh phí | Tự túc |

# 1. ĐẶT VẤN ĐỀ

Nền [9].

# 2. MỤC TIÊU NGHIÊN CỨU

## 2.1. Mục tiêu

1. Mô tả tỷ lệ X.
2. Phân tích yếu tố liên quan Y.

# 3. TỔNG QUAN TÀI LIỆU

## 3.1. Chiến lược tìm kiếm tài liệu

Tìm PubMed [5].

## 3.2. Khái niệm X

Định nghĩa X [3]. Thêm [2, 3].

## 3.3. Thực trạng X

**Trên thế giới.** Tỷ lệ X 30% [4].

**Tại Việt Nam.** Tỷ lệ X 20% [6].

Thêm số liệu trong nước [6].

**Tổng hợp các yếu tố.** Gồm A và B [4, 6].

## 3.4. Nghiên cứu tại Việt Nam

Một nghiên cứu [7].

## 3.5. Khoảng trống nghiên cứu và đóng góp

Chưa có số liệu [8]. Mức hài lòng ở câu G1 và ở G1 theo từng nhóm.

![Hình 3.1](bieu-bang/khong-co.png)

# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 4.1. Thiết kế nghiên cứu

Cắt ngang [3]. Mã `R` tự do.

## 4.2. Cỡ mẫu

n = 385.

| Biến | Định nghĩa |
|---|---|
| Tuổi | năm |

## 4.3. Quy trình nghiên cứu

1. Chốt đề cương (11/2026).
2. Thu thập số liệu (01–03/2027).
3. Phân tích.

# 6. KẾ HOẠCH THỰC HIỆN

## 6.1. Nhân lực và phân công nhiệm vụ

Chủ nhiệm: chịu trách nhiệm chung.

## 6.2. Tiến độ thực hiện

Theo các mốc ở mục 4.3.

## 6.3. Kế hoạch phổ biến kết quả

- Báo cáo Ban Giám đốc.

# 7. TÀI LIỆU THAM KHẢO

1. Tài liệu không trích. PMID: 10000001.
2. Tác giả B. Bài B. 2020. doi:10.1000/b. PMID: 10000002.
3. Tác giả C. Bài C. 2021. PMID: 10000003.
4. Tác giả D. Bài D. 2022. PMID: 10000004.
5. Tác giả E. Bài E. PMID: 10000005.
6. Tác giả F. Bài F trong nước. doi:10.1000/f.
7. Tác giả G. Bài G đã loại. doi:10.1000/g.
8. Bộ Y tế. Quyết định số 1/QĐ-BYT.
9. Tác giả I. PMID: 10000009.
"""


def _tao_de_tai(goc: Path, study: str = STUDY) -> Path:
    thu_muc = goc / study
    thu_muc.mkdir(parents=True)
    (thu_muc / "study_meta.json").write_text(json.dumps({
        "title": "Đề tài giả",
        "gate_params": {"G1": {"design": "cross_sectional",
                               "study_period": "Dự kiến từ tháng 01/2027 đến tháng 06/2027."}},
    }, ensure_ascii=False), encoding="utf-8", newline="\n")
    (thu_muc / f"DE_CUONG_NOP_HOI_DONG_{study}.md").write_text(DE_CUONG, encoding="utf-8", newline="\n")
    meta = {p: {"status": "resolved"} for p in ("10000002", "10000003", "10000005", "10000009")}
    (thu_muc / "A12_METADATA_RECEIPT.json").write_text(json.dumps({"metadata": meta}), encoding="utf-8", newline="\n")
    rut = {p: {"status": "ok"} for p in ("10000002", "10000003", "10000004", "10000005")}
    (thu_muc / "A12_RETRACTION_RECEIPT.json").write_text(json.dumps({"results": rut}), encoding="utf-8", newline="\n")
    (thu_muc / f"DANH_MUC_TRICH_DAN_{study}.json").write_text(json.dumps({
        "trich_dan": [{"doi": "10.1000/f"}],
        "loai_bo": [{"doi": "10.1000/g", "ly_do": "không lấy được toàn văn", "ngay": "2026-10-25"}],
    }), encoding="utf-8", newline="\n")
    return goc


def _trich(goc: Path, *them: str) -> int:
    return hs.main(["trich", "--study", STUDY, "--exports-root", str(goc), "--ghi", *them])


def _json(goc: Path) -> dict:
    return json.loads((goc / STUDY / hs.THU_MUC_RA / hs.TEN_JSON).read_text(encoding="utf-8"))


def _chu(p: Path) -> str:
    return "\n".join(hs.HDD._van_ban_docx(p))


def _nap_ly_lich(tmp_path: Path, ghi: bool = True) -> int:
    filled = tmp_path / "ly_lich_da_dien.docx"
    _mau_ly_lich(filled, {
        "ho_ten": "Trần Văn Giả", "ngay_sinh": "01/01/1980", "gioi_tinh": "Nam", "cccd": CCCD_GIA,
        "mobile": DT_GIA, "email": EMAIL_GIA, "to_chuc": "Trung tâm Giả",
        "dao_tao": [["Đại học", "Học viện Giả", "Bác sĩ đa khoa", "2005"],
                    ["Chuyên khoa I", "Đại học Giả", "Chuyên khoa I Nội", "2012"]],
        "cong_tac": [["2005-2011", "Bác sĩ điều trị", "Khoa Cũ", "BV Giả"],
                     ["2012 đến nay", "Bác sĩ điều trị", "Khoa Giả A", "Bệnh viện Quân y 175"],
                     ["", "", "", ""]],
    })
    return hs.main(["nap-ly-lich", "--tu", str(filled)] + (["--ghi"] if ghi else []))


# ---------------------------------------------------------------------------
# mau
# ---------------------------------------------------------------------------


def test_mau_thieu_thu_muc_bao_ma_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(hs.ENV_MAU, str(tmp_path / "khong-co"))
    assert hs.main(["mau"]) == 2


def test_mau_du_bao_ma_0(_cach_ly: dict) -> None:
    assert hs.main(["mau"]) == 0


def test_mau_chi_co_doc_bao_ma_2_va_dung_khong_dien_bua(tmp_path: Path, _cach_ly: dict,
                                                        capsys: pytest.CaptureFixture) -> None:
    ll = _cach_ly["mau"] / "docx" / f"{hs.TEN_TEP_MAU['ly_lich']}.docx"
    ll.unlink()
    (_cach_ly["mau"] / f"{hs.TEN_TEP_MAU['ly_lich']}.doc").write_bytes(b"\xd0\xcf\x11\xe0 doc gia")
    assert hs.main(["mau"]) == 2
    assert "CHỈ CÓ .doc" in capsys.readouterr().out
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    assert hs.main(["dung", "--study", STUDY, "--exports-root", str(goc), "--ghi"]) == 1
    ra = goc / STUDY / hs.THU_MUC_RA
    assert (ra / hs.ten_ra("thuyet_minh", STUDY)).is_file()
    assert not list(ra.glob("DKCT03_*.docx")), "mẫu chỉ có .doc thì KHÔNG được điền bừa"


# ---------------------------------------------------------------------------
# trich
# ---------------------------------------------------------------------------


def test_trich_khong_bia_tien_dinh_muc_khoan_chi(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    tm = _json(goc)["thuyet_minh"]
    for k in ("m6_loai_de_tai", "m14_tinh_trang", "m22_san_pham"):
        assert tm[k] == hs.CAN_CHU_NHIEM, k
    # 22/11/2026: đề cương ghi «Tự túc» ⇒ ô kinh phí ghi ĐÚNG trạng thái tự túc, không đề nghị cấp — không có số tiền
    for k in ("m4_tong_kinh_phi", "m5_khoan_chi", "m27_kinh_phi", "phu_luc_tmdt"):
        assert "tự túc" in tm[k].lower() and "[CẦN" not in tm[k], k
        assert not re.search(r"\d", tm[k]) and "đồng" not in tm[k], f"{k}: không được có số tiền/định mức"
    assert all(r["kinh_phi"] == "Tự túc" and r["chu_tri"] == hs.CAN_CHU_NHIEM for r in tm["m21_tien_do"])
    assert set(tm["m23_ung_dung_chuyen_giao"].values()) == {hs.CAN_CHU_NHIEM}
    assert set(tm["m26_tai_san"].values()) == {hs.CAN_CHU_NHIEM}


def test_trich_phan_loai_tong_quan_theo_tieu_de_va_nhan_doan(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    nhom: dict[str, list[str]] = {}
    for k in _json(goc)["thuyet_minh"]["m15"]:
        nhom.setdefault(k["nhom"], []).append(k["tieu_de"])
    assert nhom["ngoai_nuoc"] == ["Khái niệm X", "Thực trạng X"]
    assert nhom["trong_nuoc"] == ["Thực trạng X", "Nghiên cứu tại Việt Nam"]
    assert nhom["luan_giai"] == ["Thực trạng X", "Khoảng trống nghiên cứu và đóng góp"]
    assert "bo_qua" in nhom  # «Chiến lược tìm kiếm» không chép sang thuyết minh
    van = " ".join(d for k in _json(goc)["thuyet_minh"]["m15"] if k["nhom"] == "trong_nuoc" for d in k["dong"])
    assert "Tại Việt Nam" in van and "Thêm số liệu trong nước" in van and "Trên thế giới" not in van


def test_trich_muc_16_danh_so_lai_va_trang_thai(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    tm = _json(goc)["thuyet_minh"]
    m16 = tm["m16_tltk"]
    assert [m["so_de_cuong"] for m in m16] == [3, 2, 4, 6, 7, 8], "chỉ tài liệu được trích, theo thứ tự xuất hiện"
    trang = {m["so_de_cuong"]: m["trang_thai"] for m in m16}
    assert trang == {3: "da_xac_minh", 2: "da_xac_minh", 4: "chua_xac_minh", 6: "chua_kiem_rut_bai",
                     7: "loai_bo", 8: "khong_dinh_danh"}
    assert "[CẦN BÁC SĨ XỬ LÝ" in hs.dong_tltk_in(m16[4]) and "[CẦN XÁC MINH" in hs.dong_tltk_in(m16[2])
    khai_niem = next(k for k in tm["m15"] if k["tieu_de"] == "Khái niệm X")
    assert "Định nghĩa X [1]. Thêm [1, 2]." in khai_niem["dong"][0]
    tong_hop = next(k for k in tm["m15"] if k["nhom"] == "luan_giai" and k["tieu_de"] == "Thực trạng X")
    assert "[3, 4]" in " ".join(tong_hop["dong"])
    assert "[1]" in tm["m17_phuong_an"][0]["dong"][0]


def test_trich_thoi_gian_tien_do_muc_tieu(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    tm = _json(goc)["thuyet_minh"]
    assert tm["m2_thoi_gian"] == {"tu": "01/2027", "den": "06/2027", "so_thang": 6}
    assert [r["thoi_gian"] for r in tm["m21_tien_do"]] == ["11/2026", "01–03/2027", hs.CAN_CHU_NHIEM]
    assert tm["m21_tien_do"][0]["noi_dung"] == "Chốt đề cương."
    assert [n["mo_ta"] for n in tm["m17_noi_dung"]] == ["Mô tả tỷ lệ X.", "Phân tích yếu tố liên quan Y."]
    assert tm["m10_don_vi_chu_tri"].startswith("Khoa Giả A")
    assert tm["m7_linh_vuc"]["y_duoc"] is True
    cn = _json(goc)["nhan_su"][0]
    assert cn["ho_ten"] == "Trần Văn Giả" and cn["hoc_vi_tien_to"] == "BS.CKI"


def test_trich_giu_gia_tri_da_sua_va_lap_o_trong(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    p = goc / STUDY / hs.THU_MUC_RA / hs.TEN_JSON
    d = _json(goc)
    d["thuyet_minh"]["m5_khoan_chi"] = "Khoán chi đến sản phẩm cuối cùng"
    d["thuyet_minh"]["m10_don_vi_chu_tri"] = hs.CAN_BO_SUNG
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert _trich(goc) == 0
    d2 = _json(goc)
    assert d2["thuyet_minh"]["m5_khoan_chi"] == "Khoán chi đến sản phẩm cuối cùng"
    assert d2["thuyet_minh"]["m10_don_vi_chu_tri"].startswith("Khoa Giả A")
    assert list((goc / STUDY / hs.THU_MUC_RA).glob("HO_SO_DTCS_BVQY175.bak-*.json"))


# ---------------------------------------------------------------------------
# Dữ liệu cá nhân + chốt git
# ---------------------------------------------------------------------------


def test_nap_ly_lich_chay_kho_khong_in_gia_tri_va_ghi_so_rieng(tmp_path: Path, _cach_ly: dict,
                                                              capsys: pytest.CaptureFixture) -> None:
    assert _nap_ly_lich(tmp_path, ghi=False) == 0
    out = capsys.readouterr().out
    assert CCCD_GIA not in out and DT_GIA not in out and EMAIL_GIA not in out
    assert not _cach_ly["so"].exists()
    assert _nap_ly_lich(tmp_path) == 0
    rec = json.loads(_cach_ly["so"].read_text(encoding="utf-8"))["nguoi"]["tran-van-gia"]
    assert rec["so_dinh_danh"] == CCCD_GIA and rec["mobile"] == DT_GIA and rec["email"] == EMAIL_GIA
    assert rec["gioi_tinh"] == "Nam" and rec["noi_lam_viec"]["ten_to_chuc"] == "Trung tâm Giả"
    assert [m["bac"] for m in rec["dao_tao"]] == ["Đại học", "Chuyên khoa I"]
    assert len(rec["cong_tac"]) == 2
    if os.name == "posix":
        assert oct(_cach_ly["so"].stat().st_mode & 0o777) == "0o600"


def test_json_chinh_khong_chua_du_lieu_ca_nhan(tmp_path: Path) -> None:
    assert _nap_ly_lich(tmp_path) == 0
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    d = _json(goc)
    assert d["nhan_su"][0]["khoa_ca_nhan"] == "tran-van-gia"
    van = json.dumps(d, ensure_ascii=False)
    assert CCCD_GIA not in van and DT_GIA not in van and EMAIL_GIA not in van
    assert hs.du_lieu_ca_nhan_trong(d) == []
    d["nhan_su"][0]["mobile"] = DT_GIA
    d["nhan_su"][0]["ngay_sinh"] = "01/01/1980"  # không khớp mẫu số nào — chỉ luật theo KHOÁ bắt được
    assert hs.du_lieu_ca_nhan_trong(d) == ["nhan_su.0.mobile", "nhan_su.0.ngay_sinh"]


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.mark.skipif(shutil.which("git") is None, reason="cần git")
def test_tu_choi_ghi_khi_dich_nam_trong_git_khong_bi_loai(tmp_path: Path) -> None:
    kho = tmp_path / "kho"
    kho.mkdir()
    _git("init", "-q", cwd=kho)
    goc = _tao_de_tai(kho / "exports")
    assert _trich(goc) == 2
    assert not (goc / STUDY / hs.THU_MUC_RA / hs.TEN_JSON).exists()
    (kho / ".gitignore").write_text("/exports/\n", encoding="utf-8", newline="\n")
    assert _trich(goc) == 0
    assert hs.trang_thai_git(goc / STUDY / hs.THU_MUC_RA / hs.TEN_JSON)[0] is True


@pytest.mark.skipif(shutil.which("git") is None, reason="cần git")
def test_gitignore_cua_repo_loai_thu_muc_ho_so_dtcs() -> None:
    dich = ROOT / "exports" / "de-tai-bat-ky" / hs.THU_MUC_RA / hs.TEN_JSON
    an_toan, mo_ta = hs.trang_thai_git(dich)
    assert an_toan is True, mo_ta


# ---------------------------------------------------------------------------
# dung
# ---------------------------------------------------------------------------


def _dung(goc: Path) -> int:
    return hs.main(["dung", "--study", STUDY, "--exports-root", str(goc), "--ghi"])


def _o_kiem(p: Path, nhan: str) -> list[bool]:
    for doan in docx.Document(str(p)).paragraphs:
        if nhan in doan.text:
            return [cb.find(qn("w:checked")) is not None for cb in doan._p.iter(qn("w:checkBox"))]
    raise AssertionError(nhan)


def test_dung_dien_du_ba_mau(tmp_path: Path) -> None:
    assert _nap_ly_lich(tmp_path) == 0
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    assert _dung(goc) == 0
    ra = goc / STUDY / hs.THU_MUC_RA
    tm_p = ra / hs.ten_ra("thuyet_minh", STUDY)
    tm = _chu(tm_p)
    assert "Đề tài giả" in tm and "2. Thời gian thực hiện: 6 tháng" in tm
    assert "(Từ tháng 01/2027 đến tháng 06/2027)" in tm
    assert "Định nghĩa X [1]. Thêm [1, 2]." in tm
    assert "1. Tác giả C. Bài C. 2021. PMID: 10000003." in tm
    assert "[CẦN BÁC SĨ XỬ LÝ: đã loại khỏi danh mục trích dẫn" in tm
    assert "Tìm PubMed" not in tm, "chiến lược tìm kiếm không chép sang thuyết minh"
    assert "Nội dung 1: Mô tả tỷ lệ X." in tm and "Nội dung 1 :" not in tm
    assert "[CẦN BỔ SUNG HÌNH: Hình 3.1]" in tm and "![" not in tm and "`" not in tm
    assert f"Số định danh cá nhân/CMTQĐ: {CCCD_GIA}" in tm and "Họ và tên: Trần Văn Giả " in tm
    assert "4. Tổng kinh phí thực hiện: Tự túc." in tm
    assert "Chuyên khoa I Nội" in tm and "BS.CKI Trần Văn Giả" in tm
    assert _o_kiem(tm_p, "Y, dược") == [False, True]
    assert _o_kiem(tm_p, "Ngày, tháng, năm sinh") == [True, False]
    assert _o_kiem(tm_p, "Độc lập") == [False], "loại đề tài là quyết định của chủ nhiệm — không tự đánh dấu"
    bang = next(t for t in docx.Document(str(tm_p)).tables
                if len(t.columns) > 2 and "Kết quả phải đạt" in t.rows[0].cells[2].text)
    assert [r.cells[3].text for r in bang.rows[2:]] == ["11/2026", "01–03/2027", hs.CAN_CHU_NHIEM]
    dk = _chu(ra / hs.ten_ra("dang_ky", STUDY))
    assert "Khoa Giả A1 kính đề nghị" in dk and "Đề tài giả" in dk and "Khoa Giả A, Bệnh viện Quân y 175" in dk
    assert "Trần Văn Giả, Chuyên khoa I Nội, cấp bậc ……………………" in dk, "cấp bậc tự khai khi ký (gói ký)"
    assert "[CẦN" not in dk and "[GÓI KÝ" not in dk
    ll_p = ra / hs.ten_ra("ly_lich", STUDY, "01")
    ll = _chu(ll_p)
    assert f"3. Số định danh cá nhân/CCCD: {CCCD_GIA}" in ll and "Học viện Giả" in ll and "Khoa Giả A" in ll
    dong_dk = next(p.text for p in docx.Document(str(ll_p)).paragraphs if "CHỦ NHIỆM NHIỆM VỤ" in p.text)
    assert dong_dk.count("☒") == 1 and dong_dk.count("☐") == 1
    assert dong_dk.index("☒") < dong_dk.index("THAM GIA")
    danh_muc = (ra / hs.ten_ra("danh_muc", STUDY)).read_text(encoding="utf-8")
    assert EMAIL_BAN in danh_muc and "## Gói ký" in danh_muc and "## Dữ kiện cần nhập" in danh_muc


def test_dung_lai_sao_luu_tep_nguoi_da_sua_tay(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    assert _dung(goc) == 0
    p = goc / STUDY / hs.THU_MUC_RA / hs.ten_ra("thuyet_minh", STUDY)
    d = docx.Document(str(p))
    d.add_paragraph("Bác sĩ sửa tay")
    d.save(str(p))
    assert _dung(goc) == 0
    sao_luu = list((p.parent / "_sao_luu").glob("DKCT02_THUYET_MINH_*.bak-*.docx"))
    assert sao_luu and "Bác sĩ sửa tay" in _chu(sao_luu[0])


# ---------------------------------------------------------------------------
# kiem
# ---------------------------------------------------------------------------


def test_kiem_khong_do_duoc_khi_chua_trich(tmp_path: Path) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert hs.main(["kiem", "--study", STUDY, "--exports-root", str(goc)]) == 2


def test_kiem_bat_dau_vet_may_va_trich_dan_vuot(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    goc = _tao_de_tai(tmp_path / "exp")
    assert _trich(goc) == 0
    p = goc / STUDY / hs.THU_MUC_RA / hs.TEN_JSON
    d = _json(goc)
    d["thuyet_minh"]["m17_phuong_an"][0]["dong"].append("Chi tiết theo G3 và tệp G3_checkpoint.json [99].")
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert _dung(goc) == 0
    capsys.readouterr()
    assert hs.main(["kiem", "--study", STUDY, "--exports-root", str(goc)]) == 1
    out = capsys.readouterr().out
    assert "DẤU VẾT MÁY" in out and "theo G3" in out and "G3_checkpoint.json" in out
    assert "TRÍCH DẪN [99]" in out
    assert "ở G1" not in out, "mã câu hỏi G1 do chính văn bản định nghĩa không phải ký hiệu cổng"


def test_tim_dau_vet_may_mien_ma_cau_hoi_da_dinh_nghia() -> None:
    assert hs.tim_dau_vet_may("Điểm ở câu G1 và ở G1 theo nhóm.") == []
    assert hs.tim_dau_vet_may("Đã chạy ở G1 xong.") != []


# ---------------------------------------------------------------------------
# Hàm tiện ích
# ---------------------------------------------------------------------------


def test_nen_va_tach_thoi_gian() -> None:
    assert hs._nen([5, 1, 2, 3]) == "1–3, 5"
    assert hs._nen([4, 6]) == "4, 6"
    assert hs.tach_thoi_gian("Nộp hồ sơ (14/12/2026); xét duyệt (14/12/2026–15/02/2027).") == (
        "Nộp hồ sơ (14/12/2026); xét duyệt (14/12/2026–15/02/2027).", "14/12/2026; 14/12/2026–15/02/2027")
    assert hs.tach_thoi_gian("Phân tích (05–16/04/2027).") == ("Phân tích.", "05–16/04/2027")


def test_tach_hoc_vi() -> None:
    assert hs.tach_hoc_vi("BS.CKI Nguyễn Hà Giả") == ("BS.CKI", "Nguyễn Hà Giả")
    assert hs.tach_hoc_vi("PGS.TS Lê Giả") == ("PGS.TS", "Lê Giả")
    assert hs.tach_hoc_vi("Nguyễn Văn Giả") == ("", "Nguyễn Văn Giả")
