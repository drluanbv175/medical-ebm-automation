"""Kiểm `tools/ho_so_hdd_bvqy175.py` — hồ sơ Hội đồng Đạo đức BVQY175.

KHÔNG phụ thuộc bộ mẫu thật của bệnh viện (ngoài git, CI không có): tự dựng bộ mẫu .docx GIẢ trong `tmp_path` mang
đúng các nhãn/FORMCHECKBOX của mẫu thật (Mẫu 2–8 + hướng dẫn gốc), một đề tài giả (study_meta.json, gói G2, đề cương
nộp có phụ lục, quy trình dữ liệu). Không dữ liệu thật, không PII, địa chỉ email đều thuộc miền example.org.

Luật được canh (mỗi lỗi đã tái hiện 19/11/2026 có ít nhất một test hồi quy):
  * Lỗi 1 — phiếu thu thập CHỈ lấy phụ lục phiếu/bảng biến, thành bảng Word thật (không chép thân đề cương).
  * Lỗi 2 — căn cứ miễn đồng thuận đúng nguồn (Helsinki §32/§24, CIOMS HD10/HD12, TT43 Điều 7 khoản 1 điểm b) ở cả
    công cụ lẫn run_g2_auto; JSON cũ mang «Điều 15/§29» được thay khi nâng cấp.
  * Lỗi 3 — cờ «dữ liệu xác định được» suy trung thực; dữ liệu xác định được không phải cờ buộc lấy chấp thuận; ngày
    làm đơn để bác sĩ điền.
  * Lỗi 4 — `dung` sinh đủ Mẫu 2, 3, 6, 7, 8 (nhiều bản ICF), Mẫu 4 ghi tên tài liệu khác + địa chỉ/điện thoại; schema
    Phụ lục 11 đủ 4(c)–4(n), 6(f)/6(g), ô 2a; Phụ lục 10 có tên NCV chính; JSON 1.0 vẫn đọc được.
  * Lỗi 5 — danh mục xét tệp HIỆN CÓ trên đĩa.
  * Lỗi 6 — văn bản nộp không mang dấu vết máy; `kiem` chặn.
  * Lỗi 7 — tìm bộ mẫu không qua đường dẫn cứng.
  * Chạy lại `dung` sao lưu tệp người đã sửa tay; email Thư ký không viết cứng.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

docx = pytest.importorskip("docx")

from tools import ho_so_hdd_bvqy175 as hs  # noqa: E402

EMAIL_GIA = "thuky.gia@example.org"
EMAIL_GIA_PL10 = "nckh.gia@example.org"

# ---------------------------------------------------------------------------
# Bộ mẫu GIẢ — cùng nhãn với mẫu thật của bệnh viện
# ---------------------------------------------------------------------------


def _luu(thu_muc: Path, khoa: str, dong: list[str]) -> None:
    doc = docx.Document()
    for t in dong:
        p = doc.add_paragraph()
        if t:
            p.add_run(t)
    thu_muc.mkdir(parents=True, exist_ok=True)
    doc.save(str(thu_muc / hs.TEN_TEP_MAU[khoa]))


def _mau_don4() -> list[str]:
    return [
        "BỘ QUỐC PHÒNG\tCỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "ĐƠN XIN ĐÁNH GIÁ ĐẠO ĐỨC TRONG NGHIÊN CỨU",
        "Họ và tên Chủ nhiệm đề tài (dự án):", "Đơn vị:", "Địa chỉ:", "Điện thoại:\tFax: \tEmail:",
        "Tên đề tài (dự án) xin đánh giá đạo đức trong nghiên cứu:", "Tên đơn vị chủ trì đề tài (dự án):",
        "Địa chỉ:", "Điện thoại:\tFax: \tEmail:", "Địa điểm, thời gian triển khai nghiên cứu:",
        "Hồ sơ gửi kèm theo đơn xin đánh giá bao gồm: (đánh dấu “X” vào ô tương ứng)",
        " FORMCHECKBOX \tBảng kiểm lựa chọn qui trình xem xét (phụ lục 10). ",
        " FORMCHECKBOX \tPhiếu thông tin xem xét theo qui trình đầy đủ (phụ lục 11).",
        " FORMCHECKBOX \tĐề cương NCYSH.",
        " FORMCHECKBOX \tCác bảng câu hỏi, biểu mẫu, phụ lục trong nghiên cứu.",
        " FORMCHECKBOX \tMẫu phiếu chấp thuận tình nguyện của người tham gia nghiên cứu.",
        " FORMCHECKBOX \tTrang thông tin giới thiệu nghiên cứu.",
        " FORMCHECKBOX \tLý lịch khoa học của Chủ nhiệm đề tài và những nghiên cứu viên chính.",
        " FORMCHECKBOX \tCác tài liệu, văn bản có giá trị về mặt khoa học, pháp lý có liên quan (ghi rõ tên)",
        "\t", "\t", "Thay mặt nhóm nghiên cứu, tôi xin cam kết thực hiện theo đúng các Quy định.",
    ]


def _mau_ly_lich() -> list[str]:
    return [
        "LÝ LỊCH KHOA HỌC", "1. Họ và tên: ", "2. Ngày tháng năm sinh: ", "3. Nam, nữ: ", "4. Địa chỉ gửi thư: ",
        "5. Mobile: ", "6. E-mail: ", "7. Chức vụ: ", "8. Cơ quan - nơi  làm việc: ",
        "Tên người Lãnh đạo cơ quan (Thủ trưởng cơ quan):", "     Điện thoại người Lãnh đạo cơ quan: ",
        "     Địa chỉ cơ quan: ", "9. Trình độ chuyên môn", "    Học vị: ", "    Năm nhận bằng:",
        "    Chuyên ngành đào tạo: ", "    Học hàm:", "10.\tKinh nghiệm nghiên cứu:",
        "Tên đề tài/dự án đã chủ trì", "Nhiệm vụ cá nhân trong nghiên cứu", "Cơ quan chủ trì đề tài/dự án",
        "Năm bắt đầu - kết thúc", "", "", "", "TP.Hồ Chí Minh, ngày    tháng    năm 20  ",
    ]


def _mau_bia(ho_so: bool) -> list[str]:
    dong = ["BỆNH VIỆN QUÂN Y 175", "TÊN ĐỀ TÀI"]
    if not ho_so:
        dong += ["Mã số:", "", "Chuyên ngành:"]
    dong += ["Nghiên cứu viên chính (Chủ nhiệm đề tài): "]
    if not ho_so:
        dong += ["Cơ quan công tác:"]
    dong += ["Đơn vị chủ trì:", "Thời gian thực hiện: Từ tháng …/… đến tháng …/…"]
    if ho_so:
        dong += ["Hồ sơ đăng ký gồm:", "1. Đơn xin đánh giá đạo đức trong nghiên cứu y sinh học.",
                 "6. Phiếu đồng thuận tham gia nghiên cứu.",
                 "8. Giấy chứng nhận chấp thuận của Hội đồng đạo đức trong Nghiên cứu y sinh học BV/ĐH …"]
    dong += ["", "TP. HỒ CHÍ MINH, 20…"]
    return dong


def _mau_pl10() -> list[str]:
    dong = ["Phụ lục 10 ", "BẢNG KIỂM LỰA CHỌN QUI TRÌNH XEM XÉT ĐẠO ĐỨC", "PHẦN MỘT", "A. con người",
            " FORMCHECKBOX            ", "", "B.  động vật", " FORMCHECKBOX  ", "", "PHẦN HAI"]
    for nhan in ("Tên NCYSH", "Nghiên cứu viên chính", "KHOA/ BỘ MÔN", "TRƯỜNG/ĐƠN VỊ", "ĐIÊN THOAI",
                 "THƯ ĐIÊN TỬ", "ĐỊA CHỈ LIÊN HỆ", "Người giám sát/hướng dẫn (nếu liên quan)", "NƠI LÀM VIỆC",
                 "ĐIÊN THOAI", "THƯ ĐIÊN TỬ"):
        dong += [nhan, "", ""]
    dong += ["PHẦN BA", "A. Đây là NCYSH liên quan đến "]
    for k, nhan in hs.A_LABELS.items():
        if k == "A10":
            dong += [f"{k}. {nhan.lower()}", ""]
        else:
            dong += [f"{k}. {nhan}", " FORMCHECKBOX "]
    dong += ["Nếu trả lời “Có” đối với bất kì một câu nào từ A1-A6 …", "B. Trong nghiên cứu có...."]
    for k, nhan in hs.B_LABELS.items():
        dong += [f"B.{k[1:]} {nhan}", " FORMCHECKBOX "]
    dong += ["", "PHẦN BỐN", "Mô tả qui trình nghiên cứu",
             "C.1 Mô tả quy trình Huy động và chọn người tham gia nghiên cứu", "",
             "C.2 Mô tả quy trình Thu thập số liệu", "", "C.3 Mô tả quy trình Xin chấp thuận tự nguyện", "", "",
             "PHẦN NĂM", "C.4 Thử nghiệm thuốc thử nghiệm/thủ thuật can thiệp/thông tin nhạy cảm", "",
             " FORMCHECKBOX ", "C.5 Nghiên cứu chỉ liên quan đến nguy cơ tối thiểu?", "\t", " FORMCHECKBOX ",
             "C.6 Dự án gồm nhiều cơ quan/đơn vị tham gia?\t\t", "", " FORMCHECKBOX ",
             "C.7 Đây là đơn xin gia hạn/tái xin phép?", "\t", " FORMCHECKBOX ",
             "Thời gian tiến hành thử nghiệm của nghiên cứu",
             "từ  _____  /  _____  /  _____      đến      _____  / _____  / _____", "",
             "Thời gian thu thập số liệu của nghiên cứu",
             "từ  _____  /  _____  /  _____      đến      _____  / _____  / _____", "",
             "Toàn bộ quỹ thời gian nghiên cứu",
             "từ  _____  /  _____  /  _____      đến      _____  / _____  / _____", "",
             "Họ tên\t và thông tin về các nghiên cứu viên khác", "", "",
             f"Đề nghị đánh dấu “ X” nếu bản điện tử đã được gửi cho thư ký của HĐĐĐ ({EMAIL_GIA_PL10}).",
             " FORMCHECKBOX ", "", "Mô tả NCYSH", "", "", "PHẦN SÁU", "PHẦN KHAI CỦA NGHIÊN CỨU VIÊN CHÍNH",
             " FORMCHECKBOX  không thuộc phạm vi điều chỉnh về đạo đức/được miễn xem xét theo qui chế của Đơn vị",
             "HOẶC", " FORMCHECKBOX  Đủ điều kiện được xem xét theo qui trình rút gọn",
             "Xin gửi thông báo đến Phòng Khoa học Quân sự - Đào tạo    FORMCHECKBOX  Có     FORMCHECKBOX  Không ",
             "Xin gửi thông báo đến Phòng TCKT \t   FORMCHECKBOX  Có     FORMCHECKBOX  Không ",
             "Ý KIẾN CỦA NGƯỜI HƯỚNG DẪN/GIÁM SÁT NGHIÊN CỨU ",
             " FORMCHECKBOX  không thuộc phạm vi điều chỉnh về đạo đức/được miễn xem xét theo qui chế của Đơn vị",
             " FORMCHECKBOX  Đủ điều kiện được xem xét theo qui trình rút gọn"]
    return dong


def _mau_pl11() -> list[str]:
    dong = ["Phụ lục 11 ", "PHIẾU THÔNG TIN XEM XÉT ĐẠO ĐỨC THEO QUI TRÌNH ĐẦY ĐỦ ", "Tính chất của NCYSH",
            " FORMCHECKBOX  Nghiên cứu được tài trợ", " FORMCHECKBOX  Nghiên cứu của học viên sau đại học",
            " FORMCHECKBOX  Nghiên cứu của sinh viên đại học", " FORMCHECKBOX  Xin phép tập thể",
            " FORMCHECKBOX  Đơn xin tái cấp phép", " FORMCHECKBOX  Số giấy phép cũ",
            " FORMCHECKBOX  Không thuộc nghiên cứu nào ở trên", "",
            "Tên NCYSH (tiếng Việt và  ngôn ngữ gốc)", "", "", "Các nghiên cứu viên", " Họ tên", "Chức danh",
            "Nghiên cứu viên chính", "", "", "Các nghiên cứu viên khác", "", "", "Đơn vị chủ trì nghiên cứu", "", "",
            "Người giao dịch (Nếu không phải là nghiên cứu viên chính)", "Họ, tên, chức danh:", "Địa chỉ giao dịch:",
            "Điện thoại:", "CQ", "Fax", "NR", "Di động:", "Thư điện tử:", "",
            "Nghiên cứu có sự tham gia của nhiều cơ quan", "Cơ quan", "Tình trạng cấp phép về đạo đức", "", "",
            " FORMCHECKBOX  Đã được cấp phép", " FORMCHECKBOX  Đã nộp đơn và đang chờ cấp phép",
            " FORMCHECKBOX  Chưa xin phép/ Không có HĐĐĐ", " FORMCHECKBOX  Ghi chú khác_______________", "",
            "Nghiên cứu cần áp dụng những qui chế đặc biệt", "Điền “X” (có) hoặc để trống (không)"]
    for nhan in ("Trẻ em, vị thành niên, người trẻ tuổi", "Người có tổn thương thần kinh hoặc thiểu năng trí tuệ",
                 "Người thường xuyên cần đến chăm sóc y tế", "Người có quan hệ  lệ thuộc hoặc không  bình  đẳng",
                 "Các tập thể/ nhóm người ", "Người dân tộc thiểu số", "Phóng xạ, chất ion hóa",
                 "Công nghệ sinh sản có trợ giúp kĩ thuật", "Thử nghiệm lâm sàng",
                 "Phác đồ điều trị hoặc thủ thuật y tế mới", "Nghiên cứu dịch tễ học",
                 "Sử dụng mẫu mô, chất dịch người", "Gien người"):
        dong.append(f" FORMCHECKBOX  {nhan}")
    dong += ["", "Thông tin về nguồn tài trợ", "", "", "Thông tin về NCYSH sinh viên", "", "",
             "1. MÔ TẢ QUI TRÌNH, PHƯƠNG PHÁP THU THẬP DỮ LIỆU"]
    for nhan in ("1a. Mô tả dự án", "1b. Qui trình thực hiện", "1c. Mục đích", "1d. Dân tộc thiểu số",
                 "1e. Địa điểm nghiên cứu", "1f. Nơi làm việc"):
        dong += [nhan, "", ""]
    dong += ["2. NGUY CƠ TIỀM TÀNG", "2a. Có các nguy cơ nào?", "Những nguy cơ đó xảy ra với: ",
             " FORMCHECKBOX  Nhóm nghiên cứu ", " FORMCHECKBOX  Người tham gia", " FORMCHECKBOX  Cộng đồng của trường",
             " FORMCHECKBOX  Cộng đồng lớn hơn", "", ""]
    for nhan in ("2b. So sánh mức độ rủi ro", "2c. Qui trình giảm thiểu rủi ro", "2d. Cách xử lí",
                 "2e. Nguy cơ sức khoẻ", "2f. An toàn sinh học", "2g. Thao tác gen", "3a. Lợi ích", "3b. Ai được lợi?",
                 "3c. Đóng góp khoa học", "3d. So sánh nguy cơ và lợi ích"):
        dong += [nhan, "", ""]
    for chu in "abcdefghijklmn":
        dong += [f"4({chu}) Mục 4{chu}\t", "", ""]
    dong += ["5. QUI TRÌNH XIN CHẤP THUẬN TÌNH NGHUYỆN", "", "", "6. QUẢN LÍ DỮ LIỆU & BẢO MẬT THÔNG TIN"]
    for chu in "abcde":
        dong += [f"6({chu}) Mục 6{chu}", "", ""]
    dong += ["6(f) Bảo quản và lưu trữ trong ____ năm. Làm rõ việc lưu trữ riêng cho hai loại thông tin:", "",
             "6(f)i. Dữ liệu, thông tin thu thập trong nghiên cứu", "",
             "Địa điểm lưu trữ________________________________   FORMCHECKBOX  Đã có sự chấp thuận của bộ môn", "",
             "Ai được phép tiếp cận thông tin", "", "Cách kiểm soát tiếp cận thông tin", "",
             "6(f)ii. phần báo cáo kết quả nghiên cứu được công bố", "",
             "Địa điểm lưu trữ________________________________   FORMCHECKBOX  Đã có sự chấp thuận của bộ môn", "",
             "Ai được phép tiếp cận thông tin", "", "Cách kiểm soát tiếp cận thông tin", "",
             "6(g) Bảo vệ thông tin cá nhân", "", "\t6(g)i. Cơ quan/ Nơi đang lưu trữ", "",
             "\t6(g)ii. Số lượng hồ sơ", "", "\t6(g)iii. Các nguyên tắc bảo mật thông tin cá nhân đang áp dụng", "",
             "7. THỜI GIAN THỰC HIỆN", "7(a) Thời gian thử nghiệm của nghiên cứu",
             "\t\tTừ   _____  /  _____  /  _____      đến      _____  / _____  / _____",
             "7(b) Thời gian thu thập dữ liệu của nghiên cứu",
             "\t\tTừ   _____  /  _____  /  _____      đến      _____  / _____  / _____",
             "7(c) Tổng quỹ thời gian của nghiên cứu",
             "Từ _____  /  _____  /  _____      đến      _____  / _____  / _____", "", "8.  MÂU THUẪN LỢI ÍCH"]
    for chu in "abc":
        dong += [f"8({chu}) Mục 8{chu}", "", ""]
    dong += ["9. NHỮNG CÂN NHẮC ĐẠO ĐỨC KHÁC", "", "",
             "10. TỔNG QUAN, TỔNG QUAN TÀI LIỆU, KẾ HOẠCH VÀ PHƯƠNG PHÁP ",
             "Đính kèm câu trả lời của bạn về vấn đề này (không được dài quá 6 trang).", "", "",
             "11. CAM KẾT CỦA CÁC NGHIÊN CỨU VIÊN  ", "", "Tên NCYSH:", "",
             "12. Ý KIẾN CỦA NGƯỜI HƯỚNG DẪN NGHIÊN CỨU SAU ĐẠI HỌC (nếu có)", "Tên NCYSH:", "",
             "13. Ý KIẾN CỦA TRƯỞNG KHOA/ BỘ MÔN ", " FORMCHECKBOX  CÓ", " FORMCHECKBOX  KHÔNG"]
    return dong


def _mau_icf() -> list[str]:
    return ["Phụ lục 8", "BẢN THÔNG TIN DÀNH CHO ĐỐI TƯỢNG NGHIÊN CỨU", "Tên nghiên cứu: ..........",
            "Nhà tài trợ: ..........", "Nghiên cứu viên chính: ..........", "Đơn vị chủ trì: ..........",
            "(Bản Thông tin dành cho đối tượng nghiên cứu cần phải có ít nhất những thông tin dưới đây.)",
            "THÔNG TIN VỀ NGHIÊN CỨU", "1.\tMục đích và tiến hành nghiên cứu", "Vì sao nghiên cứu được tiến hành?",
            "2.\tCác lợi ích và nguy cơ bất lợi", "Liệu có những nguy cơ nào?",
            "3.\tBồi thường/điều trị khi có tổn thương liên quan đến nghiên cứu:", "Người tham gia có được điều trị?",
            "4.\tNgười liên hệ", "Họ tên, số điện thoại người cần liên hệ.", "5.\tSự tự nguyện tham gia",
            "Người tham gia được quyền tự quyết định.", "6.\tTính bảo mật", "Công bố rõ biện pháp bảo mật.",
            "CHẤP THUẬN THAM GIA NGHIÊN CỨU", "Tôi đã đọc và hiểu thông tin trên đây.", "Chữ ký của người tham gia:"]


def _tao_bo_mau_gia(thu_muc: Path, *, co_huong_dan: bool = True) -> None:
    _luu(thu_muc, "don_mau4", _mau_don4())
    _luu(thu_muc, "ly_lich", _mau_ly_lich())
    _luu(thu_muc, "bia_thuyet_minh", _mau_bia(False))
    _luu(thu_muc, "bia_ho_so", _mau_bia(True))
    _luu(thu_muc, "phu_luc_10", _mau_pl10())
    _luu(thu_muc, "phu_luc_11", _mau_pl11())
    _luu(thu_muc, "icf", _mau_icf())
    if co_huong_dan:
        _luu(thu_muc, "huong_dan_quy_trinh", [
            "HỒ SƠ ĐĂNG KÝ ĐÁNH GIÁ ĐẠO ĐỨC",
            f"Chủ nhiệm gửi bản mềm (file) về địa chỉ hộp thư điện tử {EMAIL_GIA}, trong thời gian 05 ngày.",
            f"- 01 bản mềm: gửi về email {EMAIL_GIA}, gồm 01 file thuyết minh và 01 file hồ sơ đăng ký.",
        ])
    for khoa in ("phu_luc_10_huong_dan", "phu_luc_11_huong_dan", "icf_huong_dan"):
        _luu(thu_muc, khoa, ["Bản hướng dẫn giả."])


@pytest.fixture()
def thu_muc_mau_gia(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    thu_muc = tmp_path / "mau"
    _tao_bo_mau_gia(thu_muc)
    monkeypatch.setenv("EBM_MAU_HDD_BVQY175", str(thu_muc))
    monkeypatch.delenv(hs.ENV_EMAIL_THU_KY, raising=False)
    return thu_muc


# ---------------------------------------------------------------------------
# Đề tài giả
# ---------------------------------------------------------------------------

DE_CUONG_GIA = """# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## THÔNG TIN CHUNG VỀ ĐỀ TÀI

Thông tin chung giả định của đề tài (có nhắc phụ lục phiếu thu thập ở cuối).

# 1. ĐẶT VẤN ĐỀ

Đoạn đặt vấn đề giả định — KHÔNG được xuất hiện trong phiếu thu thập.

# 3. TỔNG QUAN TÀI LIỆU

Tổng quan giả định.

# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

## 4.10. Đạo đức trong nghiên cứu

Phiếu thu thập số liệu ở Phụ lục C.

# PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ

Nội dung kế hoạch phân tích giả định.

# PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU

Nội dung phiếu đồng ý giả định.

# PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU

**Mã nghiên cứu:** ……

| STT | Biến | Giá trị |
|---|---|---|
| 1 | Tuổi (năm) | …… |
| 2 | Giới | ☐ 1. Nam ☐ 2. Nữ |

# PHỤ LỤC D. BẢNG BIẾN SỐ VÀ MÃ HOÁ

| Biến | Định nghĩa |
|---|---|
| tuoi_gia | Tuổi tính bằng năm |
"""

QUY_TRINH_BANG_NOI = (
    "muc,gia_tri,nguon,neo_de_cuong,neo_g2,ghi_chu\n"
    "thu_thap,Chủ nhiệm mở từng hồ sơ bệnh án điện tử được chọn,SOP,,,\n"
    "an_danh,Phiếu chỉ mang mã nghiên cứu,SOP,,,\n"
    "nhap_lieu,Nhập vào cơ sở dữ liệu của đề tài,SOP,,,\n"
    "huy_bang_noi,Bảng nối mã nghiên cứu với mã người bệnh lưu riêng; huỷ sau khi khoá dữ liệu,SOP,,,\n"
    "luu_tru,Số liệu điện tử lưu 2 năm sau khi kết thúc nghiên cứu,SOP,,,\n"
    "huy_du_lieu,Hết hạn lưu trữ: xoá an toàn có biên bản,SOP,,,\n"
)
QUY_TRINH_KHUYET_DANH = (
    "muc,gia_tri,nguon,neo_de_cuong,neo_g2,ghi_chu\n"
    "thu_thap,Phiếu tự điền bỏ hòm phiếu kín,SOP,,,\n"
    "an_danh,Phiếu khuyết danh hoàn toàn; không ghi họ tên,SOP,,,\n"
    "nhap_lieu,Nhập kép,SOP,,,\n"
    "luu_tru,Lưu 3 năm,SOP,,,\n"
    "huy_du_lieu,Huỷ có biên bản,SOP,,,\n"
)


def _ghi_study_meta(thu_muc: Path, *, icf_waiver: bool, recruitment_mode: str, title: str) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    meta = {
        "title": title,
        "gate_params": {
            "G1": {"design": "cross_sectional", "protocol_version": "1.0",
                   "study_period": "Thời gian thực hiện dự kiến 11/2026–09/2027."},
            "G2": {"icf_waiver_requested": icf_waiver, "recruitment_mode": recruitment_mode,
                   "public_title": "Fictional study title"},
        },
    }
    (thu_muc / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")


def _ghi_ethics_md(thu_muc: Path, study: str) -> None:
    noi_dung = f"""# A3 | {study}

## TÀI LIỆU 1. ĐƠN XIN PHÊ DUYỆT IRB

```
 Nơi thực hiện: Khoa Khám bệnh giả định, Bệnh viện giả định.
 Cỡ mẫu dự kiến: 123
```

## TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF

```
Chủ nhiệm: [CẦN BỔ SUNG]
Ngày: 2026-11-19
Loại dữ liệu: Hồ sơ điện tử có sẵn
Mã hóa: Mã nghiên cứu, không ghi định danh
Quyền truy cập: Chỉ nhóm nghiên cứu
Kế hoạch hủy: 2 năm, xoá an toàn có biên bản
```
"""
    (thu_muc / f"G2_A3_ETHICS_PACKAGE_{study}.md").write_text(noi_dung, encoding="utf-8", newline="\n")


def _tao_de_tai(tmp_path: Path, study: str, *, icf_waiver: bool, recruitment_mode: str,
                title: str = "Đề tài giả định", quy_trinh: str | None = QUY_TRINH_BANG_NOI) -> Path:
    exports_root = tmp_path / "exports"
    thu_muc = exports_root / study
    _ghi_study_meta(thu_muc, icf_waiver=icf_waiver, recruitment_mode=recruitment_mode, title=title)
    _ghi_ethics_md(thu_muc, study)
    (thu_muc / f"DE_CUONG_NOP_HOI_DONG_{study}.md").write_text(DE_CUONG_GIA, encoding="utf-8", newline="\n")
    if quy_trinh is not None:
        (thu_muc / "_quy-trinh-du-lieu.csv").write_text(quy_trinh, encoding="utf-8", newline="\n")
    return exports_root


def _tao_de_tai_hoi_cuu(tmp_path: Path, study: str, **kw) -> Path:
    """Đề tài giả — hồi cứu dữ liệu sẵn có, xin miễn ICF."""
    return _tao_de_tai(tmp_path, study, icf_waiver=True, recruitment_mode="RETROSPECTIVE_SECONDARY_DATA", **kw)


def _trich(exports_root: Path, study: str) -> Path:
    args = hs.build_parser().parse_args(["trich", "--study", study, "--exports-root", str(exports_root), "--ghi"])
    assert hs.lenh_trich(args) == 0
    return exports_root / study / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"


def _dung(exports_root: Path, study: str, quy_trinh: str = "rut_gon") -> int:
    args = hs.build_parser().parse_args(
        ["dung", "--study", study, "--exports-root", str(exports_root), "--quy-trinh", quy_trinh, "--ghi"])
    return hs.lenh_dung(args)


def _kiem(exports_root: Path, study: str) -> int:
    return hs.lenh_kiem(hs.build_parser().parse_args(["kiem", "--study", study, "--exports-root", str(exports_root)]))


def _chu(p: Path) -> str:
    doc = docx.Document(str(p))
    dong = [x.text for x in doc.paragraphs]
    for bang in doc.tables:
        for hang in bang.rows:
            dong.extend(o.text for o in hang.cells)
    return "\n".join(dong)


def _sua_json(duong_dan: Path, ham) -> None:
    d = json.loads(duong_dan.read_text(encoding="utf-8"))
    ham(d)
    duong_dan.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# `mau`
# ---------------------------------------------------------------------------


def test_mau_bao_thieu_khi_khong_co_bo_mau(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Thư mục CÓ TỒN TẠI nhưng rỗng: override hợp lệ nên KHÔNG rơi về dò tự động trên máy thật.
    thu_muc_rong = tmp_path / "thu-muc-rong"
    thu_muc_rong.mkdir()
    monkeypatch.setenv("EBM_MAU_HDD_BVQY175", str(thu_muc_rong))
    assert hs.kiem_mau(hs.build_parser().parse_args(["mau"])) == 2


def test_mau_bao_du_khi_du_bo_mau(thu_muc_mau_gia: Path) -> None:
    assert hs.kiem_mau(hs.build_parser().parse_args(["mau"])) == 0


# ---------------------------------------------------------------------------
# `trich` — không bịa
# ---------------------------------------------------------------------------


def test_trich_khong_bia_o_thieu_du_kien(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-01")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-01")
    assert d["bia"]["nghien_cuu_vien_chinh"] == hs.CAN_BAC_SI_DIEN
    assert d["don_mau4"]["ho_ten_chu_nhiem"] == hs.CAN_BAC_SI_DIEN
    assert d["ly_lich_khoa_hoc"][0]["ngay_thang_nam_sinh"] == hs.CAN_BAC_SI_DIEN
    assert d["bia"]["ten_de_tai"] == "Đề tài giả định"
    assert d["don_mau4"]["dia_diem_thoi_gian"].startswith("Khoa Khám bệnh giả định")
    assert (d["bia"]["thoi_gian_tu"], d["bia"]["thoi_gian_den"]) == ("11/2026", "09/2027")
    assert d["phien_ban_schema"] == hs.SCHEMA_VERSION


def test_trich_suy_luan_a9_tu_hoi_cuu_du_lieu_san_co(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-02")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-02")
    assert d["phu_luc_10"]["phan_ba"]["A"]["A9"]["gia_tri"] is True
    assert d["phu_luc_10"]["phan_ba"]["A"]["A1"]["gia_tri"] is False
    assert d["phu_luc_10"]["phan_ba"]["A"]["A7"]["gia_tri"] is None  # không suy luận được ⇒ để ngỏ


def test_trich_khong_suy_luan_khi_tien_cuu(tmp_path: Path) -> None:
    exports_root = _tao_de_tai(tmp_path, "gia-dinh-03", icf_waiver=False,
                               recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-03")
    assert d["phu_luc_10"]["phan_ba"]["A"]["A9"]["gia_tri"] is None
    assert d["icf"] is not None
    assert d["mien_icf"] is None


def test_trich_bao_loi_khi_khong_co_de_tai(tmp_path: Path) -> None:
    exports_root = tmp_path / "exports"
    exports_root.mkdir()
    with pytest.raises(FileNotFoundError):
        hs.trich_du_kien(exports_root, "khong-ton-tai")


def test_lenh_trich_khong_ghi_de_gia_tri_da_sua(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-04")
    duong_dan_json = exports_root / "gia-dinh-04" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    duong_dan_json.parent.mkdir(parents=True)
    da_sua = {"phien_ban_schema": "1.0", "bia": {"nghien_cuu_vien_chinh": "BS. Nguyễn Văn A (đã bác sĩ điền tay)"}}
    duong_dan_json.write_text(json.dumps(da_sua, ensure_ascii=False), encoding="utf-8", newline="\n")
    _trich(exports_root, "gia-dinh-04")
    ket_qua = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    assert ket_qua["bia"]["nghien_cuu_vien_chinh"] == "BS. Nguyễn Văn A (đã bác sĩ điền tay)"
    assert "don_mau4" in ket_qua
    assert ket_qua["phien_ban_schema"] == hs.SCHEMA_VERSION


def test_lenh_trich_ghi_de_khi_co_co_ghi_de_va_sao_luu(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-05")
    duong_dan_json = exports_root / "gia-dinh-05" / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json"
    duong_dan_json.parent.mkdir(parents=True)
    duong_dan_json.write_text(json.dumps({"bia": {"nghien_cuu_vien_chinh": "Giá trị cũ"}}, ensure_ascii=False),
                              encoding="utf-8", newline="\n")
    args = hs.build_parser().parse_args(
        ["trich", "--study", "gia-dinh-05", "--exports-root", str(exports_root), "--ghi", "--ghi-de"])
    assert hs.lenh_trich(args) == 0
    ket_qua = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    assert ket_qua["bia"]["nghien_cuu_vien_chinh"] == hs.CAN_BAC_SI_DIEN
    assert len(list(duong_dan_json.parent.glob("HO_SO_HDD_BVQY175.bak-*.json"))) == 1


# ---------------------------------------------------------------------------
# `dung` — ô đánh dấu theo quy trình
# ---------------------------------------------------------------------------


def _dau_mau4(out: Path) -> list[str]:
    doc = docx.Document(str(out))
    return [("☒" if "☒" in p.text else "☐") for p in doc.paragraphs if ("☒" in p.text or "☐" in p.text)]


def test_dung_dien_checkbox_theo_quy_trinh_rut_gon(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-06")
    _trich(exports_root, "gia-dinh-06")
    assert _dung(exports_root, "gia-dinh-06", "rut_gon") == 0
    out = exports_root / "gia-dinh-06" / "ho_so_hdd" / "MAU4_DON_XIN_DANH_GIA_DAO_DUC_gia-dinh-06.docx"
    dau = _dau_mau4(out)
    assert dau[0] == "☒"  # bảng kiểm rút gọn
    assert dau[1] == "☐"  # phiếu đầy đủ
    assert "FORMCHECKBOX" not in _chu(out)


def test_dung_dien_checkbox_ca_hai_quy_trinh(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-07")
    _trich(exports_root, "gia-dinh-07")
    assert _dung(exports_root, "gia-dinh-07", "ca_hai") == 0
    out = exports_root / "gia-dinh-07" / "ho_so_hdd" / "MAU4_DON_XIN_DANH_GIA_DAO_DUC_gia-dinh-07.docx"
    dau = _dau_mau4(out)
    assert dau[:2] == ["☒", "☒"]


def test_dung_sinh_mien_icf_khi_xin_mien(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-08")
    _trich(exports_root, "gia-dinh-08")
    _dung(exports_root, "gia-dinh-08", "rut_gon")
    thu = exports_root / "gia-dinh-08" / "ho_so_hdd"
    assert (thu / "MIEN_ICF_gia-dinh-08.docx").is_file()
    assert not any(p.name.startswith("MAU8") for p in thu.glob("*.docx"))


def test_dung_bao_loi_khi_chua_trich(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = tmp_path / "exports"
    (exports_root / "gia-dinh-09").mkdir(parents=True)
    assert _dung(exports_root, "gia-dinh-09", "rut_gon") == 2


# ---------------------------------------------------------------------------
# Lỗi 1 — phiếu thu thập
# ---------------------------------------------------------------------------


def test_phieu_thu_thap_chi_lay_phu_luc_phieu_va_bang_bien(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-p1")
    p = _trich(exports_root, "gia-dinh-p1")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["phieu_thu_thap"]["phu_luc"] == ["PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU",
                                             "PHỤ LỤC D. BẢNG BIẾN SỐ VÀ MÃ HOÁ"]
    assert _dung(exports_root, "gia-dinh-p1") == 0
    out = exports_root / "gia-dinh-p1" / "ho_so_hdd" / "PHIEU_THU_THAP_SO_LIEU_gia-dinh-p1.docx"
    chu = _chu(out)
    assert "Tuổi (năm)" in chu and "tuoi_gia" in chu  # đúng hai phụ lục C, D
    for khong in ("Đoạn đặt vấn đề giả định", "Tổng quan giả định", "Nội dung kế hoạch phân tích giả định",
                  "Nội dung phiếu đồng ý giả định", "Thông tin chung giả định"):
        assert khong not in chu, f"phiếu thu thập chép nhầm thân đề cương/phụ lục khác: {khong}"
    doc = docx.Document(str(out))
    assert len(doc.tables) >= 2, "bảng markdown phải thành BẢNG Word thật"
    assert not [x.text for x in doc.paragraphs if x.text.lstrip().startswith(("|", "#")) or "**" in x.text]


def test_tach_phu_luc_dung_o_de_muc_ke_tiep() -> None:
    ds = hs.tach_phu_luc(DE_CUONG_GIA)
    assert [t for t, _k in ds] == ["PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ",
                                   "PHỤ LỤC B. BẢN THÔNG TIN VÀ PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU",
                                   "PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU", "PHỤ LỤC D. BẢNG BIẾN SỐ VÀ MÃ HOÁ"]
    khoi_c = dict(ds)["PHỤ LỤC C. PHIẾU THU THẬP SỐ LIỆU"]
    assert "tuoi_gia" not in khoi_c and "ĐẶT VẤN ĐỀ" not in khoi_c


# ---------------------------------------------------------------------------
# Lỗi 2 — căn cứ miễn đồng thuận
# ---------------------------------------------------------------------------


def _khong_can_cu_sai(van_ban: str) -> None:
    assert "Điều 15" not in van_ban and "§29" not in van_ban
    assert "§32" in van_ban and "Hướng dẫn 10" in van_ban and "Điều 7 khoản 1 điểm b" in van_ban


def test_can_cu_mien_dong_thuan_dung_nguon_trong_cong_cu(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-c1")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-c1")
    _khong_can_cu_sai(d["mien_icf"]["can_cu"])
    _trich(exports_root, "gia-dinh-c1")
    _dung(exports_root, "gia-dinh-c1")
    _khong_can_cu_sai(_chu(exports_root / "gia-dinh-c1" / "ho_so_hdd" / "MIEN_ICF_gia-dinh-c1.docx"))


def test_can_cu_mien_dong_thuan_dung_nguon_trong_run_g2_auto() -> None:
    import run_g2_auto as G2  # noqa: PLC0415

    meta = {"gate_params": {"G1": {"data_collection_method": "Hồi cứu hồ sơ bệnh án điện tử"},
                            "G2": {"icf_waiver_requested": True}}}
    risk = G2.ap_nguon_du_lieu(G2.get_risk_profile("cross_sectional"), "cross_sectional", meta)
    md = G2.generate_g2_full_package(
        topic="Chủ đề", study_name="ZZTEST-HDD", design_code="cross_sectional", design_primary="Cắt ngang",
        reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="—", registry=None, risk=risk,
        run_date="2026-11-19T10:00:00", meta=meta, quy_trinh=[])
    khoi = md[md.index("TÀI LIỆU 9"):]
    khoi = khoi[:khoi.index("═══\n```") + 6] if "═══\n```" in khoi else khoi[:3000]
    _khong_can_cu_sai(khoi)
    assert "ICF bắt buộc" not in khoi, "dữ liệu nhận dạng được không phải cờ buộc lấy chấp thuận (CIOMS HD10)"
    assert "phải thoả CẢ BA" in khoi


def test_nang_cap_json_cu_thay_can_cu_sai_va_ngay_iso() -> None:
    cu = {"phien_ban_schema": "1.0", "bia": {"nghien_cuu_vien_chinh": "BS. Giả"},
          "phu_luc_10": {"phan_hai": {"nghien_cuu_vien_chinh": {"khoa_bo_mon": "x"}}},
          "phu_luc_11": {"muc": {"6f": "Lưu trữ 3 năm sau khi kết thúc."}},
          "mien_icf": {"can_cu": "TT43/2024/TT-BYT Điều 15 · Helsinki (WMA, bản sửa 2024) §29",
                       "ngay": "2026-11-19", "bon_dieu_kien": {}},
          "icf_phong_van": {"ten_nghien_cuu": "x", "muc": {}}}
    moi, ghi = hs.nang_cap_schema(cu)
    _khong_can_cu_sai(moi["mien_icf"]["can_cu"])
    assert moi["mien_icf"]["ngay"] == hs.CAN_BAC_SI_DIEN
    assert set(moi["mien_icf"]["ba_dieu_kien_cioms"]) == {"i_khong_kha_thi", "ii_gia_tri_xa_hoi",
                                                          "iii_nguy_co_toi_thieu"}
    assert moi["phu_luc_10"]["phan_hai"]["nghien_cuu_vien_chinh"]["ho_ten"] == "BS. Giả"
    assert moi["phu_luc_11"]["luu_tru_so_nam"] == "03"
    assert moi["icf_khac"][0]["khoa"] == "phong_van" and "icf_phong_van" not in moi
    assert moi["phien_ban_schema"] == hs.SCHEMA_VERSION and ghi
    assert cu["mien_icf"]["ngay"] == "2026-11-19", "không được sửa bản gốc tại chỗ"


# ---------------------------------------------------------------------------
# Lỗi 3 — cờ dữ liệu xác định được, ba điều kiện CIOMS, ngày làm đơn
# ---------------------------------------------------------------------------


def test_co_du_lieu_xac_dinh_duoc_suy_trung_thuc(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-x1")
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-x1")
    assert d["mien_icf"]["co_do"]["co_du_lieu_ca_nhan_nhan_dang_duoc"] is True  # còn bảng nối mã
    assert d["mien_icf"]["co_do"]["co_tiep_xuc_nguoi_tham_gia"] is False
    assert d["phu_luc_10"]["phan_ba"]["B"]["B1"]["gia_tri"] is True

    exports_root = _tao_de_tai_hoi_cuu(tmp_path / "b", "gia-dinh-x2", quy_trinh=None)
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-x2")
    assert d["mien_icf"]["co_do"]["co_du_lieu_ca_nhan_nhan_dang_duoc"] is None  # không đủ bằng chứng ⇒ không đoán

    exports_root = _tao_de_tai_hoi_cuu(tmp_path / "c", "gia-dinh-x3", quy_trinh=QUY_TRINH_KHUYET_DANH)
    d, _ = hs.trich_du_kien(exports_root, "gia-dinh-x3")
    assert d["mien_icf"]["co_do"]["co_du_lieu_ca_nhan_nhan_dang_duoc"] is False
    assert d["phu_luc_11"]["luu_tru_so_nam"] == "03"


def test_don_mien_lap_luan_ba_dieu_kien_khong_coi_du_lieu_xac_dinh_la_co_chan(
        tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-x4")
    p = _trich(exports_root, "gia-dinh-x4")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["mien_icf"]["ngay"] == hs.CAN_BAC_SI_DIEN, "không lấy ngày sinh gói G2 làm ngày làm đơn"
    _dung(exports_root, "gia-dinh-x4")
    chu = _chu(exports_root / "gia-dinh-x4" / "ho_so_hdd" / "MIEN_ICF_gia-dinh-x4.docx")
    for bat_buoc in ("(i) Nghiên cứu không khả thi", "(ii) Nghiên cứu có giá trị xã hội quan trọng",
                     "(iii) Nguy cơ không vượt mức tối thiểu", "không phải lý do tự động buộc lấy chấp thuận"):
        assert bat_buoc in chu
    for cam in ("PHẢI lấy ICF", "ICF bắt buộc", "2026-11-19"):
        assert cam not in chu


def test_kiem_bat_co_du_lieu_xac_dinh_khong_trung_thuc(tmp_path: Path, thu_muc_mau_gia: Path,
                                                      capsys: pytest.CaptureFixture) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-x5")
    p = _trich(exports_root, "gia-dinh-x5")
    _sua_json(p, lambda d: d["mien_icf"]["co_do"].__setitem__("co_du_lieu_ca_nhan_nhan_dang_duoc", False))
    _dung(exports_root, "gia-dinh-x5")
    capsys.readouterr()
    assert _kiem(exports_root, "gia-dinh-x5") == 1
    assert "CỜ KHÔNG TRUNG THỰC" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Lỗi 4 — đủ mẫu, schema mở rộng
# ---------------------------------------------------------------------------


def test_dung_sinh_du_mau_va_dien_du_truong(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    s = "gia-dinh-m1"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    p = _trich(exports_root, s)

    def sua(d: dict) -> None:
        d["don_mau4"].update({"dia_chi": "Số 1 đường Giả Định", "dien_thoai": "0000 000 001",
                              "dia_chi_don_vi_chu_tri": "Số 9 đường Giả Định", "dien_thoai_don_vi": "0000 000 009"})
        d["phu_luc_10"]["phan_hai"]["nghien_cuu_vien_chinh"]["ho_ten"] = "BS. Nghiên Cứu Viên Giả"
        d["phu_luc_11"]["muc"]["4c"] = "Không — chỉ người trưởng thành (mục 4c giả)."
        d["phu_luc_11"]["muc"]["4n"] = "Mục 4n giả định."
        d["phu_luc_11"]["muc"]["6g_i"] = "Kho hồ sơ giả định"
        d["phu_luc_11"]["muc"]["6f_i_dia_diem"] = "Máy chủ giả định"
        d["phu_luc_11"]["nguy_co_xay_ra_voi"]["nguoi_tham_gia"] = True
        d["phu_luc_10"]["phan_nam"]["C6_nhieu_co_quan"]["gia_tri"] = False

    _sua_json(p, sua)
    assert _dung(exports_root, s, "ca_hai") == 0
    thu = exports_root / s / "ho_so_hdd"
    for ten in ("MAU2_BIA_THUYET_MINH_DE_CUONG", "MAU3_BIA_HO_SO_DANG_KY", "MAU6_PHU_LUC_10_BANG_KIEM_RUT_GON",
                "MAU7_PHU_LUC_11_PHIEU_QUY_TRINH_DAY_DU"):
        assert (thu / f"{ten}_{s}.docx").is_file(), ten
    bia = _chu(thu / f"MAU2_BIA_THUYET_MINH_DE_CUONG_{s}.docx")
    assert "ĐỀ TÀI GIẢ ĐỊNH" in bia and "Từ tháng 11/2026 đến tháng 09/2027" in bia
    bia3 = _chu(thu / f"MAU3_BIA_HO_SO_DANG_KY_{s}.docx")
    assert "Đơn đề nghị miễn thủ tục đồng thuận" in bia3 and "không áp dụng" in bia3
    don = _chu(thu / f"MAU4_DON_XIN_DANH_GIA_DAO_DUC_{s}.docx")
    assert "Địa chỉ: Số 1 đường Giả Định" in don and "Địa chỉ: Số 9 đường Giả Định" in don
    assert "Điện thoại: 0000 000 001" in don and "Điện thoại: 0000 000 009" in don
    assert "– Đơn đề nghị miễn thủ tục đồng thuận tham gia nghiên cứu" in don, "ô tài liệu khác phải ghi TÊN"
    pl10 = _chu(thu / f"MAU6_PHU_LUC_10_BANG_KIEM_RUT_GON_{s}.docx")
    assert "BS. Nghiên Cứu Viên Giả" in pl10 and "FORMCHECKBOX" not in pl10
    pl11 = _chu(thu / f"MAU7_PHU_LUC_11_PHIEU_QUY_TRINH_DAY_DU_{s}.docx")
    for co in ("mục 4c giả", "Mục 4n giả định.", "Kho hồ sơ giả định", "Máy chủ giả định",
               "lưu trữ trong 02 năm", "☒  Người tham gia", "Tên tiếng Anh (tên công khai dự kiến): Fictional",
               "chỉ thực hiện tại Bệnh viện Quân y 175"):
        assert co in pl11, co
    assert "FORMCHECKBOX" not in pl11


def test_dung_icf_nhieu_ban_tu_json_phien_ban_cu(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    s = "gia-dinh-m2"
    exports_root = _tao_de_tai(tmp_path, s, icf_waiver=False, recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS",
                               quy_trinh=QUY_TRINH_KHUYET_DANH)
    p = _trich(exports_root, s)

    def ve_ban_cu(d: dict) -> None:  # JSON 1.0 như agent đã dựng: ICF phụ nằm ở khoá cấp 1
        d["phien_ban_schema"] = "1.0"
        d.pop("icf_khac", None)
        d["icf"]["muc"] = {str(k): f"Nội dung mục {k} bản chính." for k in range(1, 8)}
        d["icf"]["ten_muc_bo_sung"] = {"7": "Nguồn kinh phí và xung đột lợi ích"}
        d["icf_phong_van_nhan_thuc"] = {**d["icf"], "muc": {str(k): f"Mục {k} bản phỏng vấn." for k in range(1, 7)},
                                        "ten_muc_bo_sung": {}}

    _sua_json(p, ve_ban_cu)
    assert _dung(exports_root, s, "day_du") == 0
    thu = exports_root / s / "ho_so_hdd"
    chinh = _chu(thu / f"MAU8_PHU_LUC_8_ICF_MAU_CHINH_{s}.docx")
    phu = _chu(thu / f"MAU8_PHU_LUC_8_ICF_PHONG_VAN_NHAN_THUC_{s}.docx")
    assert "Nội dung mục 1 bản chính." in chinh and "7.\tNguồn kinh phí và xung đột lợi ích" in chinh
    assert "Nội dung mục 7 bản chính." in chinh and "Vì sao nghiên cứu được tiến hành?" not in chinh
    assert "Mục 6 bản phỏng vấn." in phu


# ---------------------------------------------------------------------------
# Lỗi 5 — danh mục theo tệp trên đĩa
# ---------------------------------------------------------------------------


def test_danh_muc_xet_tep_hien_co_tren_dia(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    s = "gia-dinh-d1"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    _trich(exports_root, s)
    _dung(exports_root, s, "ca_hai")
    thu = exports_root / s / "ho_so_hdd"
    danh_muc = (thu / f"DANH_MUC_HO_SO_HDD_{s}.md").read_text(encoding="utf-8")
    assert "CHƯA" not in danh_muc.split("## Việc CHỈ")[0], danh_muc
    assert f"MAU6_PHU_LUC_10_BANG_KIEM_RUT_GON_{s}.docx" in danh_muc
    assert f"MAU7_PHU_LUC_11_PHIEU_QUY_TRINH_DAY_DU_{s}.docx" in danh_muc
    # Tệp cũ hơn JSON ⇒ báo cũ; tệp vắng ⇒ báo chưa có — đều đọc từ ĐĨA, không từ lượt chạy.
    d = json.loads((thu / "HO_SO_HDD_BVQY175.json").read_text(encoding="utf-8"))
    moc = (thu / "HO_SO_HDD_BVQY175.json").stat().st_mtime
    os.utime(thu / f"MAU7_PHU_LUC_11_PHIEU_QUY_TRINH_DAY_DU_{s}.docx", (moc - 100, moc - 100))
    (thu / f"MAU6_PHU_LUC_10_BANG_KIEM_RUT_GON_{s}.docx").unlink()
    hs.sinh_danh_muc(thu, d, "ca_hai", thu_muc_mau_gia)
    danh_muc = (thu / f"DANH_MUC_HO_SO_HDD_{s}.md").read_text(encoding="utf-8")
    dong_6 = next(x for x in danh_muc.splitlines() if x.startswith("5a."))
    dong_7 = next(x for x in danh_muc.splitlines() if x.startswith("5b."))
    assert "CHƯA có tệp" in dong_6 and "CŨ HƠN JSON" in dong_7


# ---------------------------------------------------------------------------
# Lỗi 6 — không dấu vết máy trong văn bản nộp
# ---------------------------------------------------------------------------


def test_cau_mac_dinh_khong_mang_dau_vet_may(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    s = "gia-dinh-v1"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    d, _ = hs.trich_du_kien(exports_root, s)
    for van_ban in (d["phu_luc_11"]["muc"]["10"], d["phu_luc_10"]["phan_ba"]["A"]["A9"]["giai_thich"],
                    d["phu_luc_10"]["phan_ba"]["B"]["B1"]["giai_thich"],
                    d["phu_luc_10"]["phan_bon"]["C3_xin_chap_thuan_tu_nguyen"]):
        assert not hs.tim_dau_vet_may(van_ban), van_ban
    assert "mục 3 (tổng quan tài liệu) và mục 4" in d["phu_luc_11"]["muc"]["10"]
    _trich(exports_root, s)
    _dung(exports_root, s, "ca_hai")
    for p in (exports_root / s / "ho_so_hdd").glob("*.docx"):
        assert not hs.tim_dau_vet_may(_chu(p)), p.name


def test_kiem_chan_dau_vet_may_nhung_khong_chan_ma_cau_hoi(tmp_path: Path, thu_muc_mau_gia: Path,
                                                          capsys: pytest.CaptureFixture) -> None:
    assert hs.tim_dau_vet_may("Kết cục chính là câu hài lòng chung G1; ba câu G1–G3.") == []
    for may in ("xem tệp DE_CUONG_NOP_HOI_DONG_x.md", "đã qua cổng G2", "theo G0 §3.0", "G10-AUTO-11",
                "/Users/ai/exports/x", "C:\\du-lieu\\a"):
        assert hs.tim_dau_vet_may(may), may
    s = "gia-dinh-v2"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    p = _trich(exports_root, s)
    _sua_json(p, lambda d: d["phu_luc_11"]["muc"].__setitem__("9", "Xem tệp G2_A3_ETHICS_PACKAGE_x.md (cổng G2)."))
    _dung(exports_root, s, "day_du")
    capsys.readouterr()
    assert _kiem(exports_root, s) == 1
    assert "DẤU VẾT MÁY" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Lỗi 7 — tìm bộ mẫu không qua đường dẫn cứng
# ---------------------------------------------------------------------------


def test_tim_bo_mau_qua_goc_workspace_khong_duong_dan_cung(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nguon = (ROOT / "tools" / "ho_so_hdd_bvqy175.py").read_text(encoding="utf-8")
    # Không đường dẫn tuyệt đối của MỘT máy (Mac «/Users/<tên>», Windows «C:\\Users\\<tên>», thư mục OneDrive).
    assert not re.search(r"/Users/\w|[A-Za-z]:\\\\Users\\\\\w|OneDrive-Personal", nguon)
    goc = tmp_path / "OneDrive" / "Claude AI"
    mau = tmp_path / "OneDrive" / "Đề tài NCKH" / "Mau HDDD BV175" / "docx"
    goc.mkdir(parents=True)
    mau.mkdir(parents=True)
    monkeypatch.delenv("EBM_MAU_HDD_BVQY175", raising=False)
    monkeypatch.setenv("EBM_WORKSPACE_ROOT", str(goc))
    assert hs.tim_thu_muc_mau() == mau


# ---------------------------------------------------------------------------
# Sao lưu tệp người đã sửa tay
# ---------------------------------------------------------------------------


def test_dung_lai_sao_luu_tep_nguoi_da_sua_tay(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    s = "gia-dinh-s1"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    _trich(exports_root, s)
    _dung(exports_root, s)
    thu = exports_root / s / "ho_so_hdd"
    tep = thu / f"MAU4_DON_XIN_DANH_GIA_DAO_DUC_{s}.docx"
    doc = docx.Document(str(tep))
    doc.add_paragraph("Dòng bác sĩ tự sửa tay.")
    doc.save(str(tep))
    _dung(exports_root, s)
    sao_luu = list((thu / "_sao_luu").glob(f"MAU4_DON_XIN_DANH_GIA_DAO_DUC_{s}.bak-*.docx"))
    assert len(sao_luu) == 1 and "Dòng bác sĩ tự sửa tay." in _chu(sao_luu[0])
    _dung(exports_root, s)  # không ai sửa ⇒ không sao lưu thêm
    assert len(list((thu / "_sao_luu").glob(f"MAU4_DON_XIN_DANH_GIA_DAO_DUC_{s}.bak-*.docx"))) == 1


# ---------------------------------------------------------------------------
# Email Thư ký — không viết cứng
# ---------------------------------------------------------------------------


def test_email_thu_ky_doc_tu_huong_dan_goc(tmp_path: Path, thu_muc_mau_gia: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    email, khac = hs.doc_email_thu_ky(thu_muc_mau_gia)
    assert email == EMAIL_GIA and khac == [EMAIL_GIA_PL10]
    s = "gia-dinh-e1"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    _trich(exports_root, s)
    _dung(exports_root, s)
    danh_muc = (exports_root / s / "ho_so_hdd" / f"DANH_MUC_HO_SO_HDD_{s}.md").read_text(encoding="utf-8")
    assert EMAIL_GIA in danh_muc and EMAIL_GIA_PL10 in danh_muc and "hỏi lại" in danh_muc
    monkeypatch.setenv(hs.ENV_EMAIL_THU_KY, "khac@example.org")
    assert hs.doc_email_thu_ky(thu_muc_mau_gia)[0] == "khac@example.org"
    monkeypatch.delenv(hs.ENV_EMAIL_THU_KY)
    (thu_muc_mau_gia / hs.TEN_TEP_MAU["huong_dan_quy_trinh"]).unlink()
    assert hs.doc_email_thu_ky(thu_muc_mau_gia)[0] is None
    hs.sinh_danh_muc(exports_root / s / "ho_so_hdd",
                     json.loads((exports_root / s / "ho_so_hdd" / "HO_SO_HDD_BVQY175.json").read_text("utf-8")),
                     "rut_gon", thu_muc_mau_gia)
    danh_muc = (exports_root / s / "ho_so_hdd" / f"DANH_MUC_HO_SO_HDD_{s}.md").read_text(encoding="utf-8")
    assert hs.EMAIL_THU_KY_KHONG_DOC_DUOC in danh_muc


# ---------------------------------------------------------------------------
# `kiem`
# ---------------------------------------------------------------------------


def test_kiem_khong_do_duoc_khi_chua_trich(tmp_path: Path) -> None:
    exports_root = tmp_path / "exports"
    (exports_root / "gia-dinh-10").mkdir(parents=True)
    assert _kiem(exports_root, "gia-dinh-10") == 2


def test_kiem_bat_lech_ten_de_tai(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-11")
    p = _trich(exports_root, "gia-dinh-11")
    _sua_json(p, lambda d: d["bia"].__setitem__("ten_de_tai", "Tên đề tài SAI, không khớp study_meta.json"))
    assert _kiem(exports_root, "gia-dinh-11") == 1


def test_kiem_bat_vi_pham_logic_icf_xor_mien_icf(tmp_path: Path) -> None:
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, "gia-dinh-12")
    p = _trich(exports_root, "gia-dinh-12")
    _sua_json(p, lambda d: d.__setitem__("icf", {"ten_nghien_cuu": "x", "muc": {}}))
    assert _kiem(exports_root, "gia-dinh-12") == 1


def _dien_het(obj):
    """Giả lập bác sĩ đã điền/quyết hết: chuỗi `[CẦN…]` ⇒ giá trị; ô chưa quyết (None) ⇒ False.

    Ô kết luận của người hướng dẫn/trưởng khoa/Chủ tịch và ô gửi thông báo vẫn để None (không thuộc nghiên cứu viên).
    """
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in ("phan_khai", "phan_sau", "_nguon"):
                continue
            if isinstance(v, str) and "[CẦN" in v:
                obj[k] = "đã điền"
            elif v is None and k not in ("icf", "mien_icf"):
                obj[k] = False
            else:
                _dien_het(v)
    elif isinstance(obj, list):
        for v in obj:
            _dien_het(v)


def test_kiem_sach_khi_du_viec_va_khong_con_can(tmp_path: Path, thu_muc_mau_gia: Path) -> None:
    s = "gia-dinh-13"
    exports_root = _tao_de_tai_hoi_cuu(tmp_path, s)
    p = _trich(exports_root, s)

    def dien(d: dict) -> None:
        _dien_het(d)
        d["ly_lich_khoa_hoc"][0]["kinh_nghiem_nghien_cuu"] = ["Chưa có"]
        d["mien_icf"]["cam_ket"] = ["Cam kết giả định."]

    _sua_json(p, dien)
    assert _dung(exports_root, s, "rut_gon") == 0
    assert _kiem(exports_root, s) == 0


def test_dem_can_khong_dem_chuoi_khong_lien_quan() -> None:
    assert hs._dem_can({"a": "bình thường", "b": ["[CẦN BỔ SUNG]", "ổn"]}) == 1
    assert hs._dem_can("[CẦN BÁC SĨ ĐIỀN]") == 1
    assert hs._dem_can({"a": {"b": {"c": "[CẦN KÝ]"}}}) == 1
    assert hs._dem_can({"_nguon": {"x": "[CẦN BỔ SUNG]"}}) == 0
