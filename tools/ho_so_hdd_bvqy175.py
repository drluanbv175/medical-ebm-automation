#!/usr/bin/env python3
"""Hồ sơ Hội đồng Đạo đức trong nghiên cứu y sinh học, Bệnh viện Quân y 175.

Mục đích
--------
Dựng NHÁP toàn bộ Quyển 1 (bìa Thuyết minh đề cương) + Quyển 2 (Hồ sơ đăng ký đánh giá đạo đức) theo đúng bộ mẫu
của Hội đồng Đạo đức BVQY175, cho MỖI đề tài trong `exports/<mã>/` — tự sinh ĐỦ các tệp Word, không cần script
điền tay. Công cụ KHÔNG tự ký, KHÔNG tự gửi email, KHÔNG tự chuyển lệ phí — những việc đó thuộc về bác sĩ.

Bốn lệnh con, theo đúng thứ tự dùng:

    python3 tools/ho_so_hdd_bvqy175.py mau
        Dò bộ mẫu của bệnh viện (ngoài git). Báo tệp nào có/thiếu. Thiếu ⇒ mã 2, không bao giờ báo "đạt" giả.

    python3 tools/ho_so_hdd_bvqy175.py trich --study <mã> [--ghi] [--ghi-de]
        Trích TẤT ĐỊNH dữ kiện đã chốt (study_meta.json, gói G2, `_quy-trinh-du-lieu.csv`, đề cương nộp) vào
        exports/<mã>/ho_so_hdd/HO_SO_HDD_BVQY175.json. Ô không trích được ghi "[CẦN ...]", KHÔNG BAO GIỜ bịa.
        Chạy khô mặc định; `--ghi` mới ghi; JSON đã có được NÂNG CẤP schema rồi chỉ BỔ SUNG khoá còn thiếu
        (không ghi đè giá trị đã sửa) trừ khi dùng `--ghi-de` (có sao lưu).

    python3 tools/ho_so_hdd_bvqy175.py dung --study <mã> --quy-trinh rut_gon|day_du|ca_hai [--ghi]
        Điền các mẫu Word của bệnh viện: Mẫu 2, 3 (bìa), Mẫu 4 (đơn), Mẫu 5 (lý lịch, một tệp mỗi người), Mẫu 6
        (Phụ lục 10) và/hoặc Mẫu 7 (Phụ lục 11) theo quy trình, Mẫu 8 (ICF — một tệp cho mỗi bản thông tin) HOẶC Đơn
        đề nghị miễn đồng thuận, Phiếu thu thập số liệu (bảng Word thật), cùng DANH_MUC_HO_SO_HDD_<mã>.md. Tệp đã có
        mà người đã sửa tay ⇒ sao lưu `ho_so_hdd/_sao_luu/<tên>.bak-<giờ>.<đuôi>` TRƯỚC khi ghi đè.

    python3 tools/ho_so_hdd_bvqy175.py sau-chap-thuan --study <mã> [--loai sua_doi|tien_do|ket_qua|ca_ba] [--ghi]
        (22/11/2026) Ba văn bản gửi Hội đồng SAU khi chấp thuận: đề nghị thay đổi đề cương, báo cáo tiến độ, báo cáo
        kết quả — dựng theo nội dung Thông tư 43/2024/TT-BYT (tools/ho_so_sau_chap_thuan.py).

    python3 tools/ho_so_hdd_bvqy175.py kiem --study <mã> [--quy-trinh …]
        Kiểm JSON + tệp Word: đủ tệp theo quy trình? logic ICF/miễn theo ba điều kiện CIOMS? cờ dữ liệu xác định được
        trung thực? Word mới hơn JSON? còn bao nhiêu ô "[CẦN"? văn bản nộp có dấu vết máy (đường dẫn, tên tệp
        .md/.json, ký hiệu cổng G0–G10)? Mã thoát: 0 sạch · 1 còn việc/vấn đề · 2 không đo được.

Căn cứ pháp lý của Đơn đề nghị miễn đồng thuận
---------------------------------------------
Lấy từ `tools/can_cu_dao_duc.py` (dùng chung với `run_g2_auto.py`), đã tự đối chiếu nguồn chính thức ngày 19/11/2026:
Tuyên bố Helsinki (WMA, bản 10/2024, trang wma.net) §32 (miễn chấp thuận cho dữ liệu/vật liệu xác định được khi không
thể hoặc không thực tế xin, sau khi hội đồng đạo đức chấp thuận) và §24 (riêng tư); CIOMS 2016 Hướng dẫn 10 (tr. 37–39:
ba điều kiện — không khả thi nếu không miễn, giá trị xã hội quan trọng, nguy cơ tối thiểu) và Hướng dẫn 12 (tr. 47–52);
Thông tư 43/2024/TT-BYT Điều 7 khoản 1 điểm b (Hội đồng chấp thuận miễn bản thông tin + phiếu tình nguyện) và Điều 16
khoản 6 (quy trình rút gọn chỉ cho nghiên cứu nguy cơ tối thiểu). Căn cứ cũ «TT43 Điều 15 · Helsinki §29» là SAI
(Điều 15 = chuyên gia tư vấn độc lập; §29 = sự ưng thuận của người không đủ năng lực) — JSON cũ mang chuỗi đó được
thay khi nâng cấp. Dữ liệu xác định được/giả danh hoá KHÔNG tự động buộc lấy chấp thuận (CIOMS Hướng dẫn 10).

Cấu trúc JSON (`phien_ban_schema` = "2.0"; JSON "1.0" vẫn đọc được — nâng cấp trong bộ nhớ)
--------------------------------------------------------------------------------------------
- `meta` — {study, title, quy_trinh, quy_trinh_de_xuat?, ngay_trich, co_mau_du_kien}
- `bia` — Mẫu 2/3: ten_de_tai, ma_so, chuyen_nganh, nghien_cuu_vien_chinh, co_quan_cong_tac, don_vi_chu_tri,
  thoi_gian_tu, thoi_gian_den, nam_nop.
- `don_mau4` — chủ nhiệm (ho_ten_chu_nhiem, don_vi, dia_chi, dien_thoai, fax, email), đơn vị chủ trì
  (ten_don_vi_chu_tri, dia_chi_don_vi_chu_tri, dien_thoai_don_vi, fax_don_vi, email_don_vi), dia_diem_thoi_gian,
  ho_so_kem_theo (cờ + `tai_lieu_khac`: chuỗi hoặc danh sách TÊN tài liệu — in đúng tên vào đơn).
- `ly_lich_khoa_hoc` — list mỗi người: 8 mục cá nhân + lãnh đạo cơ quan + trinh_do{hoc_vi, nam_nhan_bang,
  chuyen_nganh_dao_tao, hoc_ham} + kinh_nghiem_nghien_cuu (list {ten_de_tai, nhiem_vu, co_quan_chu_tri, nam} hoặc
  chuỗi). Ô cá nhân luôn `[CẦN BÁC SĨ ĐIỀN]` cho tới khi bác sĩ tự điền.
- `phu_luc_10` — Mẫu 6: phan_mot, phan_hai{ten_ncysh, nghien_cuu_vien_chinh{ho_ten, khoa_bo_mon, truong_don_vi,
  dien_thoai, thu_dien_tu, dia_chi_lien_he}, nguoi_giam_sat}, phan_ba{A1–A10, B1–B11: {gia_tri, giai_thich}},
  phan_bon (C1–C3), phan_nam (C4–C7), thoi_gian, nghien_cuu_vien_khac, phan_khai (kết luận — chỉ ô của NCV chính
  được in khi bác sĩ đã ghi «mien»/«rut_gon»), phan_sau.gui_thong_bao (bốn phòng: true/false/null).
- `phu_luc_11` — Mẫu 7: tinh_chat (7 cờ + so_giay_phep_cu), ten_ncysh, ten_tieng_anh, nghien_cuu_vien (list; phần
  tử đầu là NCV chính), nghien_cuu_vien_khac, don_vi_chu_tri, nguoi_giao_dich, nhieu_co_quan (list {ten,
  trang_thai: da_cap_phep|dang_cho|chua_xin|khac}), quy_che_dac_biet (13 cờ), nguy_co_xay_ra_voi (4 cờ ô 2a),
  nguon_tai_tro, thong_tin_sinh_vien, luu_tru_so_nam, chap_thuan_bo_mon_luu_tru{i, ii}, muc (khoá theo
  `MUC_PHU_LUC_11`: 1a–3d, 4a–4n, 5, 6a–6g, 6f_i_*/6f_ii_*, 6g_i–6g_iii, 7a–7c, 8a–8c, 9, 10), cam_ket.
- `icf` — Mẫu 8 bản chính (khi KHÔNG xin miễn): ten_nghien_cuu, nha_tai_tro, nghien_cuu_vien_chinh, don_vi_chu_tri,
  phien_ban, muc{"1".."6" và mục bổ sung}, ten_muc_bo_sung{số: tên}. `icf_khac` — list bản thông tin khác (mỗi bản
  cùng cấu trúc + `khoa` đặt hậu tố tên tệp, vd «phong_van_nhan_thuc»). JSON 1.0 có khoá cấp 1 `icf_<x>` ⇒ chuyển
  vào `icf_khac`.
- `mien_icf` — Đơn đề nghị miễn (khi `icf_waiver_requested` = true): can_cu, kinh_gui, ten_de_tai, chu_nhiem, ngay
  (để bác sĩ điền — KHÔNG lấy ngày sinh gói G2), tom_tat, ba_dieu_kien_cioms{i_khong_kha_thi, ii_gia_tri_xa_hoi,
  iii_nguy_co_toi_thieu}, phuong_an_sua_doi_da_xem_xet, dam_bao_bao_mat, co_do{co_du_lieu_ca_nhan_nhan_dang_duoc,
  co_tiep_xuc_nguoi_tham_gia} (suy TRUNG THỰC: còn bảng nối mã/ghép mã/hồ sơ bệnh án ⇒ true; không đủ bằng chứng ⇒
  null), co_do_giai_thich, xung_dot_loi_ich, cam_ket.
- `phieu_thu_thap` — {nguon, phu_luc: [tiêu đề phụ lục chọn]} — mặc định chọn MỌI phụ lục của đề cương nộp TRỪ
  phụ lục đã nộp thành mục riêng (bản thông tin/phiếu đồng ý, đơn miễn đồng thuận → mục 6) và tóm tắt kế hoạch
  phân tích thống kê (thuộc phương pháp, Quyển 1). Bác sĩ đổi danh sách bằng cách sửa `phu_luc`.
- `viec_bac_si`, `_nguon` ("đường.dẫn.khoá" → nguồn trích, chỉ dùng nội bộ — KHÔNG in vào văn bản nộp).

Ranh giới
---------
Chỉ soạn NHÁP. Không tự ký, không tự xin thư giới thiệu/quyết định phân công, không tự chuyển lệ phí, không tự gửi
email cho Thư ký Hội đồng. Ô cá nhân (ngày sinh, học vị, địa chỉ, điện thoại…) LUÔN `[CẦN BÁC SĨ ĐIỀN]`. Ô ý kiến
người hướng dẫn/trưởng khoa/Chủ tịch Hội đồng không bao giờ được đánh dấu. Địa chỉ email Thư ký KHÔNG viết cứng —
đọc từ hướng dẫn gốc của Hội đồng (tệp 1 của bộ mẫu) hoặc biến môi trường `EBM_EMAIL_THU_KY_HDD_BVQY175`.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

for _luong in (sys.stdout, sys.stderr):  # Windows: ép UTF-8 cho stdout (luật §0.9)
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

_TOOLS = Path(__file__).resolve().parent
_REPO = _TOOLS.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import can_cu_dao_duc as CCDD  # noqa: E402
import ho_so_nguon_chung as HSC  # noqa: E402

try:
    import docx  # type: ignore
    from docx.oxml import OxmlElement  # type: ignore
    from docx.oxml.ns import qn  # type: ignore
    from docx.shared import Pt  # type: ignore
    from docx.text.paragraph import Paragraph  # type: ignore
except ImportError:  # pragma: no cover - môi trường thiếu python-docx
    docx = None  # type: ignore
    OxmlElement = None  # type: ignore
    qn = None  # type: ignore
    Pt = None  # type: ignore
    Paragraph = None  # type: ignore

CAN_BO_SUNG = "[CẦN BỔ SUNG]"
CAN_BAC_SI_DIEN = "[CẦN BÁC SĨ ĐIỀN]"
CAN_KY = "[CẦN KÝ]"
CHUA_QUYET = "[CẦN BÁC SĨ XÁC NHẬN]"
SCHEMA_VERSION = "2.0"
BENH_VIEN = "Bệnh viện Quân y 175"
KINH_GUI_HOI_DONG = "Chủ tịch Hội đồng Đạo đức trong nghiên cứu y sinh học, Bệnh viện Quân y 175"
FONT = "Times New Roman"
CO_CHU = 12
ENV_EMAIL_THU_KY = "EBM_EMAIL_THU_KY_HDD_BVQY175"
EMAIL_THU_KY_KHONG_DOC_DUOC = "địa chỉ email Thư ký ghi trong hướng dẫn gốc của Hội đồng (tệp 1)"

# Mục của Phụ lục 11 (Mẫu 7, quy trình đầy đủ) — tên đầy đủ theo mẫu bệnh viện.
MUC_PHU_LUC_11 = {
    "1a": "Mô tả dự án",
    "1b": "Qui trình thực hiện",
    "1c": "Mục đích/giả thuyết/vấn đề nghiên cứu",
    "1d": "Vấn đề liên quan đến người dân tộc thiểu số",
    "1e": "Địa điểm nghiên cứu",
    "1f": "Nghiên cứu tại nơi làm việc của người tham gia",
    "2a": "Có các nguy cơ nào?",
    "2b": "So sánh mức độ rủi ro khi tham gia nghiên cứu với sinh hoạt hàng ngày",
    "2c": "Qui trình giảm thiểu rủi ro",
    "2d": "Cách xử lí khi xảy ra rủi ro",
    "2e": "Các nguy cơ về sức khoẻ và tính an toàn",
    "2f": "Các vấn đề về an toàn sinh học",
    "2g": "Thao tác gen",
    "3a": "Có những lợi ích gì?",
    "3b": "Ai được lợi?",
    "3c": "Đóng góp khoa học của nghiên cứu",
    "3d": "So sánh giữa nguy cơ và lợi ích của người tham gia",
    "4a": "Người tham gia dự kiến?",
    "4b": "Cách xác định, tiếp xúc, và tuyển mộ",
    "4c": "Sự tham gia của trẻ vị thành niên?",
    "4d": "Sự tham gia của người bị thương tổn thần kinh hoặc thiểu năng trí tuệ?",
    "4e": "Sự tham gia của người đang bị giam giữ, người có quan hệ lệ thuộc/không bình đẳng?",
    "4f": "Mối quan hệ sẵn có với những người tham gia?",
    "4g": "Rào cản ngôn ngữ phổ thông?",
    "4h": "Sàng tuyển?",
    "4i": "Người tham gia phải từ chối phác đồ điều trị đang áp dụng?",
    "4j": "Tuyển chọn có chủ định các thành viên thuộc các cộng đồng dân tộc thiểu số",
    "4k": "Sự tham gia tập thể?",
    "4l": "Chi trả khuyến khích",
    "4m": "Qui trình báo cáo, công bố kết quả cuối cùng",
    "4n": "Qui trình công bố báo cáo tóm tắt",
    "5": "Qui trình xin chấp thuận tình nguyện",
    "6a": "Thu thập dữ liệu trực tiếp?",
    "6b": "Tiếp cận thông tin cá nhân?",
    "6c": "Dữ liệu sẽ được ghi lại như thế nào?",
    "6d": "Thông tin cá nhân/nhạy cảm",
    "6e": "Bảo mật thông tin",
    "6f": "Bảo quản và lưu trữ",
    "6f_i_dia_diem": "6(f)i. Địa điểm lưu trữ dữ liệu thu thập",
    "6f_i_ai_tiep_can": "6(f)i. Ai được phép tiếp cận",
    "6f_i_kiem_soat": "6(f)i. Cách kiểm soát tiếp cận",
    "6f_ii_dia_diem": "6(f)ii. Địa điểm lưu trữ báo cáo công bố",
    "6f_ii_ai_tiep_can": "6(f)ii. Ai được phép tiếp cận",
    "6f_ii_kiem_soat": "6(f)ii. Cách kiểm soát tiếp cận",
    "6g": "Bảo vệ thông tin cá nhân",
    "6g_i": "6(g)i. Cơ quan/nơi đang lưu trữ",
    "6g_ii": "6(g)ii. Số lượng hồ sơ",
    "6g_iii": "6(g)iii. Các nguyên tắc bảo mật thông tin cá nhân đang áp dụng",
    "7a": "Thời gian thử nghiệm của nghiên cứu",
    "7b": "Thời gian thu thập dữ liệu của nghiên cứu",
    "7c": "Tổng quỹ thời gian của nghiên cứu",
    "8a": "Nghiên cứu theo yêu cầu của (thay cho) người tài trợ/tổ chức thương mại?",
    "8b": "Sự phụ thuộc hoặc liên quan về tài chính",
    "8c": "Lợi ích tài chính trực tiếp/gián tiếp của nhóm nghiên cứu",
    "9": "Những cân nhắc đạo đức khác",
    "10": "Tổng quan, tổng quan tài liệu, kế hoạch và phương pháp",
}

MUC_PHU_LUC_8 = {
    "1": "Mục đích và tiến hành nghiên cứu",
    "2": "Các lợi ích và nguy cơ bất lợi",
    "3": "Bồi thường/điều trị khi có tổn thương liên quan đến nghiên cứu",
    "4": "Người liên hệ",
    "5": "Sự tự nguyện tham gia",
    "6": "Tính bảo mật",
}

A_LABELS = {
    "A1": "Thử nghiệm dược phẩm mới",
    "A2": "Thử nghiệm chế phẩm sinh học mới",
    "A3": "Thử nghiệm các phương pháp điều trị mới không dùng thuốc",
    "A4": "Thử nghiệm các thiết bị y tế mới",
    "A5": "Sử dụng phương pháp xạ trị và siêu âm",
    "A6": "Sử dụng các thủ thuật, phẫu thuật",
    "A7": "Bối cảnh giáo dục đã được chấp nhận rộng rãi",
    "A8": "Test giáo dục/quy trình điều tra/phỏng vấn/quan sát hành vi công cộng",
    "A9": "Số liệu, văn bản, hồ sơ, bệnh phẩm hay bệnh phẩm chẩn đoán sẵn có",
    "A10": "Chương trình dịch vụ hay phúc lợi công",
}
B_LABELS = {
    "B1": "Ghi/lưu trữ thông tin xác định danh tính cá nhân",
    "B2": "Sự tham gia của người không có năng lực hành vi",
    "B3": "Sự tham gia của vị thành niên",
    "B4": "Sự tham gia của người có quan hệ phụ thuộc vào nghiên cứu viên",
    "B5": "Các vấn đề nhạy cảm về văn hoá",
    "B6": "Gây đau đớn hoặc mệt mỏi tâm lý cao hơn mức thông thường",
    "B7": "Có chi trả khuyến khích",
    "B8": "Có thu thập thông tin nhạy cảm",
    "B9": "Có thu thập bí mật cá nhân",
    "B10": "Có thể liên quan đến trách nhiệm pháp lý",
    "B11": "Có sự tham gia có chọn lọc của người thiểu số",
}
QUY_CHE_DAC_BIET = (
    "tre_em_vi_thanh_nien", "ton_thuong_than_kinh_thieu_nang_tri_tue", "can_cham_soc_y_te_thuong_xuyen",
    "quan_he_le_thuoc_khong_binh_dang", "tap_the_nhom_nguoi", "dan_toc_thieu_so", "phong_xa_chat_ion_hoa",
    "cong_nghe_sinh_san_co_tro_giup", "thu_nghiem_lam_sang", "phac_do_dieu_tri_thu_thuat_moi",
    "nghien_cuu_dich_te_hoc", "mau_mo_chat_dich_nguoi", "gien_nguoi",
)

# Tên tệp mẫu CHUẨN của bệnh viện, tương đối so với thư mục mẫu.
TEN_TEP_MAU = {
    "don_mau4": "4 - MH175.IRB.Phu_luc_6_Đơn xin đánh giá đạo đức_Nghiên cứu viên.docx",
    "ly_lich": "5 - Mẫu Lý lịch Khoa học.docx",
    "phu_luc_10": "6 - MH175.IRB.phu_luc_10-lựa chọn quy trình xem xét đạo đức_Quy trình rút gọn.docx",
    "phu_luc_10_huong_dan": (
        "6 - MH175.IRB.phu_luc_10-lựa chọn quy trình xem xét đạo đức"
        "_Quy trình rút gọn_[hướng dẫn].docx"
    ),
    "phu_luc_11": "7 - MH175.IRB.Phu_luc_11-lựa chọn quy trình xem xét đạo đức_Quy trình xem xét đầy đủ.docx",
    "phu_luc_11_huong_dan": (
        "7 - MH175.IRB.Phu_luc_11-lựa chọn quy trình xem xét đạo đức"
        "_Quy trình xem xét đầy đủ_[hướng dẫn].docx"
    ),
    "icf": "8 - MH175.IRB.phu_luc_8_Bản thông tin dành cho đối tượng nghiên cứu_ICF.docx",
    "icf_huong_dan": (
        "8 - MH175.IRB.phu_luc_8_Bản thông tin dành cho đối tượng nghiên cứu"
        "_ICF_hướng dẫn.docx"
    ),
    "bia_thuyet_minh": "2 - Mẫu bìa Thuyết minh đề cương.docx",
    "bia_ho_so": "3 - Mẫu bìa Hồ sơ đăng ký.docx",
    "huong_dan_quy_trinh": (
        "1 - Hồ sơ đăng ký đánh giá đạo đức trong nghiên cứu y sinh học BV Quân y 175.docx"
    ),
}

VAN_BAN_LE_PHI = "THÔNG TIN CHUYỂN KHOẢN.docx"
THU_MUC_SAO_LUU = "_sao_luu"
TEP_BAM = "_bam_lan_dung.json"


def _ten_ra(loai: str, study: str, hau_to: str = "") -> str:
    """Tên tệp đầu ra (hợp đồng tên với danh mục và `kiem`)."""
    return {
        "bia_thuyet_minh": f"MAU2_BIA_THUYET_MINH_DE_CUONG_{study}.docx",
        "bia_ho_so": f"MAU3_BIA_HO_SO_DANG_KY_{study}.docx",
        "don_mau4": f"MAU4_DON_XIN_DANH_GIA_DAO_DUC_{study}.docx",
        "ly_lich": f"MAU5_LY_LICH_KHOA_HOC_{study}_{hau_to}.docx",
        "phu_luc_10": f"MAU6_PHU_LUC_10_BANG_KIEM_RUT_GON_{study}.docx",
        "phu_luc_11": f"MAU7_PHU_LUC_11_PHIEU_QUY_TRINH_DAY_DU_{study}.docx",
        "icf": f"MAU8_PHU_LUC_8_ICF_{hau_to}{study}.docx",
        "mien_icf": f"MIEN_ICF_{study}.docx",
        "phieu": f"PHIEU_THU_THAP_SO_LIEU_{study}.docx",
        "danh_muc": f"DANH_MUC_HO_SO_HDD_{study}.md",
    }[loai]


# ---------------------------------------------------------------------------
# Bộ mẫu bệnh viện (ngoài git)
# ---------------------------------------------------------------------------


def _ung_vien_tu_goc(goc: Path) -> list[Path]:
    """Hai vị trí bộ mẫu suy từ thư mục gốc workspace «Claude AI» (cùng cha OneDrive)."""
    duoi = Path("Đề tài NCKH") / "Mau HDDD BV175" / "docx"
    return [goc.parent / duoi, goc / duoi]


def tim_thu_muc_mau() -> Path | None:
    """Tìm thư mục chứa bộ mẫu bệnh viện (ngoài git). KHÔNG đường dẫn cứng của một máy.

    Thứ tự: biến `EBM_MAU_HDD_BVQY175` → gốc workspace (`EBM_WORKSPACE_ROOT`, `EBM_REPO_ROOT`, `tools/goc_ebm.py`)
    → tổ tiên tên «medical-ebm-automation» của tệp này. Mẫu nằm ở ``<cha-của-«Claude AI»>/Đề tài NCKH/
    Mau HDDD BV175/docx`` trên cả Mac lẫn Windows. Không thấy ⇒ None (không bịa).
    """
    override = os.environ.get("EBM_MAU_HDD_BVQY175")
    if override:
        p = Path(override).expanduser()
        if p.is_dir():
            return p
    goc_thu: list[Path] = []
    for bien in ("EBM_WORKSPACE_ROOT", "EBM_REPO_ROOT"):
        gia_tri = os.environ.get(bien, "").strip()
        if gia_tri:
            goc_thu.append(Path(gia_tri).expanduser())
    try:
        import goc_ebm  # noqa: PLC0415

        goc_thu.append(goc_ebm.tim_goc_ebm(_REPO))
    except Exception:  # noqa: BLE001 - dò vị trí không được làm hỏng lệnh
        pass
    for ancestor in Path(__file__).resolve().parents:
        if ancestor.name == "medical-ebm-automation":
            goc_thu.append(ancestor.parent)
            break
    for goc in goc_thu:
        for ung_vien in _ung_vien_tu_goc(goc):
            if ung_vien.is_dir():
                return ung_vien
    return None


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _van_ban_docx(duong_dan: Path) -> list[str]:
    """Mọi đoạn văn (thân + bảng) của một tệp .docx; lỗi đọc ⇒ []."""
    if docx is None or not duong_dan.is_file():
        return []
    try:
        tai_lieu = docx.Document(str(duong_dan))
    except Exception:  # noqa: BLE001 - tệp mẫu hỏng ⇒ coi như không đọc được
        return []
    dong = [p.text for p in tai_lieu.paragraphs]
    for bang in tai_lieu.tables:
        for hang in bang.rows:
            for o in hang.cells:
                dong.append(o.text)
    return dong


def doc_email_thu_ky(mau_dir: Path | None) -> tuple[str | None, list[str]]:
    """(email Thư ký Hội đồng, các email KHÁC ghi trong mẫu Phụ lục 10).

    Không viết cứng địa chỉ (repo công khai): biến `EBM_EMAIL_THU_KY_HDD_BVQY175` thắng; không có thì đọc hướng dẫn
    gốc của Hội đồng (tệp 1 của bộ mẫu) — lấy email xuất hiện nhiều nhất trong các câu nói về bản mềm/Thư ký.
    Không đọc được ⇒ None. Email khác ở mẫu Phụ lục 10 trả về riêng để danh mục nhắc bác sĩ hỏi lại Thư ký.
    """
    tu_env = os.environ.get(ENV_EMAIL_THU_KY, "").strip()
    email: str | None = tu_env or None
    if mau_dir is not None and email is None:
        dem: dict[str, int] = {}
        for dong in _van_ban_docx(mau_dir / TEN_TEP_MAU["huong_dan_quy_trinh"]):
            thap = dong.lower()
            if not any(t in thap for t in ("bản mềm", "thư ký", "email", "thư điện tử")):
                continue
            for e in _EMAIL_RE.findall(dong):
                dem[e.lower()] = dem.get(e.lower(), 0) + 1
        if dem:
            email = max(dem.items(), key=lambda kv: kv[1])[0]
    khac: list[str] = []
    if mau_dir is not None:
        for dong in _van_ban_docx(mau_dir / TEN_TEP_MAU["phu_luc_10"]):
            for e in _EMAIL_RE.findall(dong):
                e = e.lower()
                if e != (email or "").lower() and e not in khac:
                    khac.append(e)
    return email, khac


def kiem_mau(args: argparse.Namespace) -> int:
    """Lệnh `mau`: dò bộ mẫu, báo tệp nào có/thiếu."""
    thu_muc = tim_thu_muc_mau()
    if thu_muc is None:
        print("KHÔNG TÌM THẤY thư mục bộ mẫu Hội đồng Đạo đức BVQY175.")
        print(
            "Đặt biến môi trường EBM_MAU_HDD_BVQY175 trỏ tới thư mục chứa các tệp .docx, hoặc để đúng cấu trúc"
            " <OneDrive>/Đề tài NCKH/Mau HDDD BV175/docx/."
        )
        return 2
    print(f"Thư mục mẫu: {thu_muc}")
    thieu = []
    for khoa, ten in TEN_TEP_MAU.items():
        duong_dan = thu_muc / ten
        dau_tep = "✓" if duong_dan.is_file() else "✗ THIẾU"
        print(f"  [{dau_tep}] {khoa}: {ten}")
        if not duong_dan.is_file():
            thieu.append(khoa)
    le_phi = thu_muc.parent / "goc" / VAN_BAN_LE_PHI
    print(f"  [{'✓' if le_phi.is_file() else '✗ THIẾU'}] (tham khảo, KHÔNG dùng số tài khoản) {VAN_BAN_LE_PHI}")
    if thieu:
        print(f"\nTHIẾU {len(thieu)} tệp mẫu — chưa thể chạy `dung` đầy đủ.")
        return 2
    print("\nĐủ bộ mẫu cần cho `dung`.")
    return 0


# ---------------------------------------------------------------------------
# Trích xuất tất định từ dữ liệu đề tài đã chốt
# ---------------------------------------------------------------------------


def _doc(exports_root: Path, study: str) -> Path:
    return exports_root / study


def _doc_hdd(exports_root: Path, study: str) -> Path:
    return _doc(exports_root, study) / "ho_so_hdd"


def _lay(d: Any, *path: str, default: Any = None) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _cho_trong(gia_tri: Any) -> bool:
    """Ô chưa có nội dung thật: rỗng, None hoặc còn nhãn «[CẦN…»."""
    if gia_tri is None:
        return True
    s = str(gia_tri).strip()
    return not s or "[CẦN" in s


def _nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or ""))


def _doc_md_mien_icf(noi_dung_md: str) -> dict | None:
    """Trích khối «TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF» từ G2_A3_ETHICS_PACKAGE_*.md.

    KHÔNG lấy dòng «Ngày:» — đó là ngày SINH gói G2, không phải ngày chủ nhiệm làm đơn (ô ngày để bác sĩ điền).
    """
    m = re.search(r"## TÀI LIỆU 9\b[^\n]*ĐỀ NGHỊ MIỄN ICF.*?```\n(.*?)\n```", noi_dung_md, re.S)
    if not m:
        return None
    than = m.group(1)
    ra: dict[str, Any] = {}
    chu_nhiem = re.search(r"Chủ nhiệm:\s*(.+)", than)
    if chu_nhiem and not _cho_trong(chu_nhiem.group(1)):
        ra["chu_nhiem"] = chu_nhiem.group(1).strip()
    bao_mat: dict[str, str] = {}
    for khoa, nhan in (("ma_hoa", "Mã hóa"), ("quyen_truy_cap", "Quyền truy cập"),
                       ("ke_hoach_huy", "Kế hoạch hủy"), ("loai_du_lieu", "Loại dữ liệu")):
        mm = re.search(rf"{nhan}:\s*(.+)", than)
        if mm:
            bao_mat[khoa] = mm.group(1).strip()
    if bao_mat:
        ra["dam_bao_bao_mat"] = bao_mat
    return ra


def _doc_md_dia_diem_thoi_gian(noi_dung_md: str) -> str | None:
    m = re.search(r"Nơi thực hiện:\s*(.+)", noi_dung_md)
    if m:
        return m.group(1).split(".")[0].strip()
    return None


def _doc_md_co_mau(noi_dung_md: str) -> str | None:
    m = re.search(r"Cỡ mẫu dự kiến:\s*(.+)", noi_dung_md)
    return m.group(1).strip() if m else None


def _doc_quy_trinh(thu_muc: Path) -> list[dict]:
    """Bảng `_quy-trinh-du-lieu.csv` đã chốt (mỗi dòng một quyết định); không có/không đọc được ⇒ []."""
    try:
        import quy_trinh_du_lieu as QTD  # noqa: PLC0415

        dong, _cot, _loi = QTD.doc_bang(thu_muc)
    except Exception:  # noqa: BLE001 - thiếu mô-đun/bảng hỏng ⇒ coi như chưa có
        return []
    return list(dong or [])


def _gia_tri_qt(dong: list[dict], *muc: str) -> list[str]:
    """Giá trị THẬT (không còn «[CẦN…») của các dòng thuộc mục đã cho, giữ thứ tự bảng."""
    return [str(r.get("gia_tri") or "").strip() for r in dong
            if r.get("muc") in muc and not _cho_trong(r.get("gia_tri"))]


_KHUYET_DANH = re.compile(r"khuyết danh|ẩn danh hoàn toàn|nặc danh|không thể truy ngược", re.I)
_HO_SO_CO_DINH_DANH = re.compile(r"hồ sơ|bệnh án|eHospital|HIS\b", re.I)


def suy_du_lieu_xac_dinh_duoc(dong_qt: list[dict], g2: dict) -> tuple[bool | None, str, str]:
    """Suy TRUNG THỰC cờ «có dữ liệu cá nhân xác định được» — (giá trị, nguồn, giải thích).

    - Còn bảng nối/đối chiếu mã hoặc ghép dữ liệu bằng mã (mục `huy_bang_noi`/`ghep_du_lieu`) ⇒ True: dữ liệu GIẢ
      DANH HOÁ, tái xác định được cho tới khi huỷ bảng nối.
    - Hồi cứu dữ liệu sẵn có mà nhóm tự mở hồ sơ bệnh án (`thu_thap` nói hồ sơ/bệnh án/eHospital/HIS) ⇒ True.
    - Chỉ có cam kết khuyết danh/ẩn danh hoàn toàn và KHÔNG có dòng bảng nối/ghép ⇒ False.
    - Không đủ bằng chứng ⇒ None (để bác sĩ xác nhận) — không đoán.
    """
    lien_ket = _gia_tri_qt(dong_qt, "huy_bang_noi", "ghep_du_lieu")
    if lien_ket:
        return True, "_quy-trinh-du-lieu.csv#huy_bang_noi/ghep_du_lieu", "; ".join(lien_ket)
    thu_thap = _gia_tri_qt(dong_qt, "thu_thap")
    if g2.get("recruitment_mode") == "RETROSPECTIVE_SECONDARY_DATA" and any(
            _HO_SO_CO_DINH_DANH.search(v) for v in thu_thap):
        return True, "_quy-trinh-du-lieu.csv#thu_thap + recruitment_mode", "; ".join(thu_thap)
    an_danh = _gia_tri_qt(dong_qt, "an_danh")
    co_dong_lien_ket = any(r.get("muc") in ("huy_bang_noi", "ghep_du_lieu") for r in dong_qt)
    if an_danh and not co_dong_lien_ket and any(_KHUYET_DANH.search(v) for v in an_danh):
        return False, "_quy-trinh-du-lieu.csv#an_danh", "; ".join(an_danh)
    return None, "", ""


def _so_nam_luu_tru(dong_qt: list[dict]) -> str | None:
    for v in _gia_tri_qt(dong_qt, "luu_tru"):
        m = re.search(r"(\d+)\s*năm", v)
        if m:
            return f"{int(m.group(1)):02d}"
    return None


_THOI_GIAN_RE = re.compile(
    r"(\d{1,2}/\d{4})\s*(?:[–—-]|đến(?:\s+tháng)?|tới(?:\s+tháng)?)\s*(\d{1,2}/\d{4})")


def _thoi_gian_tu_den(van_ban: str) -> tuple[str, str] | None:
    m = _THOI_GIAN_RE.search(van_ban or "")
    return (m.group(1), m.group(2)) if m else None


# --- Phụ lục của đề cương nộp ------------------------------------------------

_DAU_PHU_LUC = re.compile(r"^(#{1,6})\s+((?:PHỤ LỤC|Phụ lục|PHIẾU THU THẬP|Phiếu thu thập|BỆNH ÁN NGHIÊN CỨU)\b.*)$")
# 22/11/2026: kế hoạch thực hiện và thông tin chung thuộc Quyển 1 (tổ chức thực hiện), không phải phiếu thu thập.
_TIEU_DE_KHONG_CHON = ("KẾ HOẠCH THỰC HIỆN", "THÔNG TIN CHUNG", "KẾ HOẠCH PHÂN TÍCH", "ĐỒNG THUẬN", "ĐỒNG Ý",
                       "THÔNG TIN DÀNH CHO", "BẢN THÔNG TIN", "MIỄN THỦ TỤC", "MIỄN ĐỒNG")


def tach_phu_luc(noi_dung_md: str) -> list[tuple[str, str]]:
    """Mọi phụ lục của đề cương: [(tiêu đề, khối markdown kể cả dòng tiêu đề)].

    Khối kết thúc ở đề mục KẾ TIẾP cùng cấp hoặc cấp cao hơn — không «ăn» sang phần sau (lỗi cũ: biểu thức `## .*`
    với re.S khớp từ đề mục `##` đầu tiên tới hết tệp và bỏ sót đề mục `# PHỤ LỤC …`).
    """
    dong = _nfc(noi_dung_md).split("\n")
    ra: list[tuple[str, str]] = []
    i = 0
    trong_khoi_ma = False
    while i < len(dong):
        if dong[i].lstrip().startswith("```"):
            trong_khoi_ma = not trong_khoi_ma
        m = None if trong_khoi_ma else _DAU_PHU_LUC.match(dong[i].rstrip())
        if not m:
            i += 1
            continue
        cap = len(m.group(1))
        j = i + 1
        ma = False
        while j < len(dong):
            if dong[j].lstrip().startswith("```"):
                ma = not ma
            if not ma:
                mm = re.match(r"^(#{1,6})\s", dong[j])
                if mm and len(mm.group(1)) <= cap:
                    break
            j += 1
        ra.append((m.group(2).strip(), "\n".join(dong[i:j]).rstrip()))
        i = j
    return ra


def chon_phu_luc_mac_dinh(ds: list[tuple[str, str]]) -> list[str]:
    """Phụ lục đưa vào mục 7 Quyển 2: mọi phụ lục TRỪ phụ lục đã nộp thành mục riêng (bản thông tin/phiếu đồng ý,
    đơn miễn đồng thuận → mục 6) và tóm tắt kế hoạch phân tích thống kê (thuộc phương pháp, Quyển 1)."""
    chon = []
    for tieu_de, _khoi in ds:
        hoa = tieu_de.upper()
        if any(t in hoa for t in _TIEU_DE_KHONG_CHON):
            continue
        chon.append(tieu_de)
    return chon


def _so_muc_de_cuong(noi_dung_md: str, tu_khoa: str) -> str | None:
    """Vị trí phần của đề cương để trỏ tới: «mục 3» (cấu trúc cũ «# 3. TỔNG QUAN…») hoặc «Chương 1» (khuôn hướng dẫn
    chung «# CHƯƠNG 1. TỔNG QUAN…», 21/11/2026)."""
    m = re.search(rf"(?m)^#\s+(CHƯƠNG\s+)?(\d+)\.\s+{re.escape(tu_khoa)}", _nfc(noi_dung_md))
    if not m:
        return None
    return f"Chương {m.group(2)}" if m.group(1) else f"mục {m.group(2)}"


# --- Trích ---------------------------------------------------------------------


def trich_du_kien(exports_root: Path, study: str) -> tuple[dict, list[str]]:
    """Trích tất định dữ kiện đã chốt của một đề tài (schema 2.0).

    Trả về (dữ liệu, ghi chú). KHÔNG bịa — ô không trích được giữ nguyên placeholder [CẦN ...]. Mọi trường trích
    tự động có mục `_nguon` (chỉ dùng nội bộ, không bao giờ in vào văn bản nộp Hội đồng).
    """
    ghi_chu: list[str] = []
    thu_muc = _doc(exports_root, study)
    meta_path = thu_muc / "study_meta.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"Không thấy {meta_path} — đề tài chưa tồn tại hoặc sai mã.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    title = meta.get("title") or CAN_BO_SUNG
    gp = meta.get("gate_params", {}) or {}
    g1 = gp.get("G1", {}) if isinstance(gp.get("G1"), dict) else {}
    g2 = gp.get("G2", {}) or {}

    md_path = thu_muc / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    noi_dung_md = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    if not noi_dung_md:
        ghi_chu.append(f"Không thấy {md_path.name} — một số trường phải để [CẦN].")

    de_cuong_path = thu_muc / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    noi_dung_de_cuong = de_cuong_path.read_text(encoding="utf-8") if de_cuong_path.is_file() else ""
    if not noi_dung_de_cuong:
        ghi_chu.append(f"Không thấy {de_cuong_path.name} — chưa trích được phiếu thu thập (mục 7).")
    dong_qt = _doc_quy_trinh(thu_muc)

    icf_waiver = bool(g2.get("icf_waiver_requested"))
    dia_diem_thoi_gian = _doc_md_dia_diem_thoi_gian(noi_dung_md) or CAN_BO_SUNG
    co_mau = _doc_md_co_mau(noi_dung_md)
    thoi_gian = _thoi_gian_tu_den(str(g1.get("study_period") or ""))
    recruitment_mode = g2.get("recruitment_mode")
    la_hoi_cuu_du_lieu_san_co = recruitment_mode == "RETROSPECTIVE_SECONDARY_DATA"
    la_tien_cuu_moi = recruitment_mode == "PROSPECTIVE_NEW_PARTICIPANTS"

    nguon: dict[str, str] = {}

    def dat(path: str, value: Any, nguon_tag: str | None = None) -> Any:
        if nguon_tag:
            nguon[path] = nguon_tag
        return value

    tu, den = thoi_gian if thoi_gian else (CAN_BO_SUNG, CAN_BO_SUNG)
    if thoi_gian:
        for k in ("bia.thoi_gian_tu", "bia.thoi_gian_den", "phu_luc_10.thoi_gian.toan_bo", "phu_luc_11.muc.7c"):
            nguon[k] = "study_meta.json#gate_params.G1.study_period"

    bia = {
        "ten_de_tai": dat("bia.ten_de_tai", title, "study_meta.json#title"),
        "ma_so": CAN_BAC_SI_DIEN,
        "chuyen_nganh": CAN_BAC_SI_DIEN,
        "nghien_cuu_vien_chinh": CAN_BAC_SI_DIEN,
        "co_quan_cong_tac": CAN_BAC_SI_DIEN,
        "don_vi_chu_tri": CAN_BO_SUNG,
        "thoi_gian_tu": tu,
        "thoi_gian_den": den,
        "nam_nop": str(datetime.now(timezone.utc).year),
    }

    phu_luc_ds = tach_phu_luc(noi_dung_de_cuong) if noi_dung_de_cuong else []
    phu_luc_chon = chon_phu_luc_mac_dinh(phu_luc_ds)
    tai_lieu_khac: list[str] = []
    if icf_waiver:
        tai_lieu_khac.append("Đơn đề nghị miễn thủ tục đồng thuận tham gia nghiên cứu (thay cho phiếu chấp thuận)")

    don_mau4 = {
        "ho_ten_chu_nhiem": CAN_BAC_SI_DIEN,
        "chuc_vu": CAN_BAC_SI_DIEN,
        "don_vi": CAN_BAC_SI_DIEN,
        "dia_chi": CAN_BAC_SI_DIEN,
        "dien_thoai": CAN_BAC_SI_DIEN,
        "fax": "",
        "email": CAN_BAC_SI_DIEN,
        "ten_de_tai": dat("don_mau4.ten_de_tai", title, "study_meta.json#title"),
        "ten_don_vi_chu_tri": CAN_BO_SUNG,
        "dia_chi_don_vi_chu_tri": CAN_BAC_SI_DIEN,
        "dien_thoai_don_vi": "",
        "fax_don_vi": "",
        "email_don_vi": "",
        "dia_diem_thoi_gian": dat(
            "don_mau4.dia_diem_thoi_gian", dia_diem_thoi_gian,
            f"{md_path.name}#Nơi thực hiện" if dia_diem_thoi_gian != CAN_BO_SUNG else None,
        ),
        "ho_so_kem_theo": {
            "bang_kiem_rut_gon": None,
            "phieu_day_du": None,
            "de_cuong": True,
            "bang_cau_hoi_phu_luc": True if phu_luc_chon else None,
            "phieu_chap_thuan": not icf_waiver,
            "trang_thong_tin": not icf_waiver,
            "ly_lich_khoa_hoc": True,
            "tai_lieu_khac": tai_lieu_khac,
        },
    }

    ly_lich_khoa_hoc = [
        {
            "vai_tro": "Chủ nhiệm đề tài",
            "ho_ten": CAN_BAC_SI_DIEN,
            "ngay_thang_nam_sinh": CAN_BAC_SI_DIEN,
            "nam_nu": CAN_BAC_SI_DIEN,
            "dia_chi_gui_thu": CAN_BAC_SI_DIEN,
            "mobile": CAN_BAC_SI_DIEN,
            "email": CAN_BAC_SI_DIEN,
            "chuc_vu": CAN_BAC_SI_DIEN,
            "co_quan_noi_lam_viec": CAN_BAC_SI_DIEN,
            "ten_lanh_dao_co_quan": CAN_BAC_SI_DIEN,
            "dien_thoai_lanh_dao_co_quan": CAN_BAC_SI_DIEN,
            "dia_chi_co_quan": CAN_BAC_SI_DIEN,
            "trinh_do": {
                "hoc_vi": CAN_BAC_SI_DIEN,
                "nam_nhan_bang": CAN_BAC_SI_DIEN,
                "chuyen_nganh_dao_tao": CAN_BAC_SI_DIEN,
                "hoc_ham": CAN_BAC_SI_DIEN,
            },
            "kinh_nghiem_nghien_cuu": [],
        }
    ]

    def co_khong(gia_tri: bool | None, giai_thich: str = "") -> dict:
        return {"gia_tri": gia_tri, "giai_thich": giai_thich if gia_tri is not None or giai_thich else ""}

    co_xac_dinh, nguon_xac_dinh, chung_cu_xac_dinh = suy_du_lieu_xac_dinh_duoc(dong_qt, g2)

    phan_ba_a = {k: co_khong(None) for k in A_LABELS}
    if la_hoi_cuu_du_lieu_san_co:
        phan_ba_a["A9"] = co_khong(True, "Có — hồi cứu dữ liệu sẵn có, không can thiệp, không tiếp xúc người bệnh.")
        nguon["phu_luc_10.phan_ba.A.A9"] = "study_meta.json#gate_params.G2.recruitment_mode"
        for k in ("A1", "A2", "A3", "A4", "A5", "A6"):
            phan_ba_a[k] = co_khong(False)
    phan_ba_b = {k: co_khong(None) for k in B_LABELS}
    if co_xac_dinh is True:
        phan_ba_b["B1"] = co_khong(True, f"Có — {chung_cu_xac_dinh}.")
        nguon["phu_luc_10.phan_ba.B.B1"] = nguon_xac_dinh
    elif co_xac_dinh is False:
        phan_ba_b["B1"] = co_khong(False, f"Không — {chung_cu_xac_dinh}.")
        nguon["phu_luc_10.phan_ba.B.B1"] = nguon_xac_dinh

    phu_luc_10 = {
        "phan_mot": {"doi_tuong_con_nguoi": True, "doi_tuong_dong_vat": False},
        "phan_hai": {
            "ten_ncysh": dat("phu_luc_10.phan_hai.ten_ncysh", title, "study_meta.json#title"),
            "nghien_cuu_vien_chinh": {
                "ho_ten": CAN_BAC_SI_DIEN,
                "khoa_bo_mon": CAN_BAC_SI_DIEN,
                "truong_don_vi": CAN_BAC_SI_DIEN,
                "dien_thoai": CAN_BAC_SI_DIEN,
                "thu_dien_tu": CAN_BAC_SI_DIEN,
                "dia_chi_lien_he": CAN_BAC_SI_DIEN,
            },
            "nguoi_giam_sat": {"noi_lam_viec": "", "dien_thoai": "", "thu_dien_tu": ""},
        },
        "phan_ba": {"A": phan_ba_a, "B": phan_ba_b},
        "phan_bon": {
            "C1_huy_dong_chon_nguoi_tham_gia": CAN_BO_SUNG,
            "C2_thu_thap_so_lieu": CAN_BO_SUNG,
            "C3_xin_chap_thuan_tu_nguyen": (
                "Đề nghị Hội đồng miễn thủ tục đồng thuận tham gia nghiên cứu (Đơn đề nghị miễn thủ tục đồng thuận"
                " nộp kèm theo hồ sơ)." if icf_waiver else CAN_BO_SUNG
            ),
        },
        "phan_nam": {
            "C4_thu_nghiem_thuoc_can_thiep": co_khong(False if la_hoi_cuu_du_lieu_san_co else None),
            "C5_nguy_co_toi_thieu_de_quan_ly": co_khong(None),
            "C6_nhieu_co_quan": co_khong(None),
            "C7_gia_han_tai_xin_phep": co_khong(False, "Không — hồ sơ nộp lần đầu."),
        },
        "thoi_gian": {
            "thu_nghiem": {"tu": CAN_BO_SUNG, "den": CAN_BO_SUNG},
            "thu_thap": {"tu": CAN_BO_SUNG, "den": CAN_BO_SUNG},
            "toan_bo": {"tu": tu, "den": den},
        },
        "nghien_cuu_vien_khac": "",
        "phan_khai": {
            "ket_luan_nghien_cuu_vien_chinh": None,
            "ket_luan_nguoi_huong_dan": None,
            "ket_luan_truong_khoa": None,
            "ket_luan_chu_tich_hoi_dong": None,
        },
        "phan_sau": {"gui_thong_bao": {"phong_khqs_dao_tao": None, "phong_dao_tao_dai_hoc": None,
                                       "phong_dao_tao_sau_dai_hoc": None, "phong_tckt": None}},
    }

    muc_11: dict[str, str] = {k: CAN_BO_SUNG for k in MUC_PHU_LUC_11}
    so_tq = _so_muc_de_cuong(noi_dung_de_cuong, "TỔNG QUAN TÀI LIỆU")
    so_pp = _so_muc_de_cuong(noi_dung_de_cuong, "ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP")
    vi_tri = ""
    if so_tq and so_pp:
        vi_tri = f", {so_tq} (tổng quan tài liệu) và {so_pp} (đối tượng và phương pháp nghiên cứu)"
    muc_11["10"] = (
        f"{CAN_BO_SUNG}: tóm tắt tổng quan tài liệu, kế hoạch và phương pháp (không quá 6 trang). Bản đầy đủ trình"
        f" bày trong Thuyết minh đề cương nộp kèm (Quyển 1){vi_tri}."
    )
    luu_tru = _gia_tri_qt(dong_qt, "luu_tru")
    huy = _gia_tri_qt(dong_qt, "huy_du_lieu")
    if luu_tru or huy:
        muc_11["6f"] = dat("phu_luc_11.muc.6f", ". ".join(v.rstrip(".") for v in luu_tru + huy) + ".",
                           "_quy-trinh-du-lieu.csv#luu_tru/huy_du_lieu")
    if thoi_gian:
        muc_11["7c"] = f"Từ {tu} đến {den}"

    so_nam = _so_nam_luu_tru(dong_qt)
    phu_luc_11 = {
        "tinh_chat": {
            "duoc_tai_tro": None,
            "hoc_vien_sau_dai_hoc": None,
            "sinh_vien_dai_hoc": None,
            "xin_phep_tap_the": None,
            "don_xin_tai_cap_phep": False,
            "so_giay_phep_cu": "",
            "khong_thuoc_nhom_nao_tren": None,
        },
        "ten_ncysh": dat("phu_luc_11.ten_ncysh", title, "study_meta.json#title"),
        "ten_tieng_anh": dat("phu_luc_11.ten_tieng_anh", g2.get("public_title"),
                             "study_meta.json#gate_params.G2.public_title")
        if g2.get("public_title") else "",
        "nghien_cuu_vien": [
            {"ho_ten": CAN_BAC_SI_DIEN, "chuc_danh": CAN_BAC_SI_DIEN, "chuc_vu_noi_cong_tac": CAN_BAC_SI_DIEN}
        ],
        "don_vi_chu_tri": CAN_BO_SUNG,
        "nguoi_giao_dich": {
            "ho_ten_chuc_danh": "", "dia_chi_giao_dich": "", "dien_thoai_cq": "", "fax": "",
            "dien_thoai_nr": "", "di_dong": "", "thu_dien_tu": "",
        },
        "nhieu_co_quan": [],
        "quy_che_dac_biet": {k: None for k in QUY_CHE_DAC_BIET},
        "nguy_co_xay_ra_voi": {"nhom_nghien_cuu": None, "nguoi_tham_gia": None, "cong_dong_cua_truong": None,
                               "cong_dong_lon_hon": None},
        "nguon_tai_tro": CAN_BO_SUNG,
        "thong_tin_sinh_vien": "",
        "luu_tru_so_nam": dat("phu_luc_11.luu_tru_so_nam", so_nam, "_quy-trinh-du-lieu.csv#luu_tru")
        if so_nam else CAN_BO_SUNG,
        "chap_thuan_bo_mon_luu_tru": {"i": None, "ii": None},
        "muc": muc_11,
        "cam_ket": [],
    }
    if la_hoi_cuu_du_lieu_san_co:
        phu_luc_11["quy_che_dac_biet"]["mau_mo_chat_dich_nguoi"] = False

    if icf_waiver:
        mien_icf_md = _doc_md_mien_icf(noi_dung_md) or {}
        co_tiep_xuc = False if la_hoi_cuu_du_lieu_san_co else True if la_tien_cuu_moi else None
        mien_icf: dict | None = {
            "can_cu": CCDD.CAN_CU_MIEN_DONG_THUAN,
            "kinh_gui": KINH_GUI_HOI_DONG,
            "ten_de_tai": dat("mien_icf.ten_de_tai", title, "study_meta.json#title"),
            "chu_nhiem": mien_icf_md.get("chu_nhiem", CAN_BAC_SI_DIEN),
            "ngay": CAN_BAC_SI_DIEN,
            "tom_tat": CAN_BO_SUNG,
            "ba_dieu_kien_cioms": {khoa: CAN_BO_SUNG for khoa, _nhan in CCDD.BA_DIEU_KIEN_CIOMS},
            "phuong_an_sua_doi_da_xem_xet": {
                "xin_dong_y_khi_tai_kham": CAN_BO_SUNG,
                "thong_bao_va_cho_tu_choi": CAN_BO_SUNG,
                "quyet_dinh_bo_sung": "",
            },
            "dam_bao_bao_mat": mien_icf_md.get("dam_bao_bao_mat", {
                "loai_du_lieu": CAN_BO_SUNG,
                "ma_hoa": CAN_BO_SUNG,
                "quyen_truy_cap": CAN_BO_SUNG,
                "ke_hoach_huy": CAN_BO_SUNG,
            }),
            "co_do": {
                "co_du_lieu_ca_nhan_nhan_dang_duoc": co_xac_dinh,
                "co_tiep_xuc_nguoi_tham_gia": co_tiep_xuc,
            },
            "co_do_giai_thich": "",
            "xung_dot_loi_ich": CAN_BO_SUNG,
            "cam_ket": [],
        }
        nguon["mien_icf.can_cu"] = f"tools/can_cu_dao_duc.py (đối chiếu nguồn {CCDD.NGAY_DOI_CHIEU})"
        if nguon_xac_dinh:
            nguon["mien_icf.co_do.co_du_lieu_ca_nhan_nhan_dang_duoc"] = nguon_xac_dinh
        if co_tiep_xuc is not None:
            nguon["mien_icf.co_do.co_tiep_xuc_nguoi_tham_gia"] = "study_meta.json#gate_params.G2.recruitment_mode"
        if mien_icf_md:
            nguon["mien_icf.dam_bao_bao_mat"] = f"{md_path.name}#TÀI LIỆU 9. ĐỀ NGHỊ MIỄN ICF"
        icf = None
    else:
        mien_icf = None
        icf_version = str(g2.get("icf_version") or "").strip()
        icf = {
            "ten_nghien_cuu": dat("icf.ten_nghien_cuu", title, "study_meta.json#title"),
            "nha_tai_tro": CAN_BO_SUNG,
            "nghien_cuu_vien_chinh": CAN_BAC_SI_DIEN,
            "don_vi_chu_tri": CAN_BO_SUNG,
            "phien_ban": (f"Phiên bản {icf_version}, ngày ……/……/……" if icf_version
                          and not icf_version.lower().startswith("không") and "[CẦN" not in icf_version else ""),
            "muc": {k: CAN_BO_SUNG for k in MUC_PHU_LUC_8},
            "ten_muc_bo_sung": {},
        }

    du_lieu: dict[str, Any] = {
        "phien_ban_schema": SCHEMA_VERSION,
        "meta": {
            "study": study,
            "title": title,
            "quy_trinh": "rut_gon" if la_hoi_cuu_du_lieu_san_co else "day_du" if la_tien_cuu_moi else CAN_BO_SUNG,
            "ngay_trich": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "co_mau_du_kien": co_mau or CAN_BO_SUNG,
        },
        "bia": bia,
        "don_mau4": don_mau4,
        "ly_lich_khoa_hoc": ly_lich_khoa_hoc,
        "phu_luc_10": phu_luc_10,
        "phu_luc_11": phu_luc_11,
        "icf": icf,
        "icf_khac": [],
        "mien_icf": mien_icf,
        "phieu_thu_thap": {
            "nguon": f"DE_CUONG_NOP_HOI_DONG_{study}.md" if noi_dung_de_cuong else CAN_BO_SUNG,
            "phu_luc": phu_luc_chon,
        },
        "viec_bac_si": [],
        "_nguon": nguon,
    }
    if not g1.get("design"):
        ghi_chu.append("Chưa thấy gate_params.G1.design trong study_meta.json — một số suy luận A/B để trống.")
    if noi_dung_de_cuong and not phu_luc_chon:
        ghi_chu.append("Đề cương nộp không có phụ lục phiếu thu thập/bảng biến nào chọn được — kiểm lại đề cương.")
    # 22/11/2026: ô dùng chung lấy từ NGUỒN CHUNG (một bản sự thật với gói G2 và hồ sơ đề tài cơ sở), rồi khối
    # dữ kiện riêng của biểu mẫu Hội đồng Đạo đức trong study_meta (ho_so_nguon_chung.py).
    n_chung = HSC.NguonDeTai(exports_root, study)
    du_lieu["meta"]["dau_nguon"] = n_chung.dau_nguon()
    da_suy = ap_nguon_chung(du_lieu, n_chung, nguon, ghi_chu)
    ap_khoi_ho_so(du_lieu, n_chung, nguon, ghi_chu, da_suy)
    return du_lieu, ghi_chu


# ---------------------------------------------------------------------------
# Trích từ NGUỒN CHUNG (22/11/2026) — một bản sự thật với gói G2 và hồ sơ đề tài cơ sở
# ---------------------------------------------------------------------------

#: Khối dữ kiện riêng của biểu mẫu Hội đồng Đạo đức trong study_meta (câu trả lời của bảng kiểm/phiếu mà không nguồn
#: nào khác có). Khoá dùng chung (đơn vị, chủ nhiệm, kinh phí, xung đột lợi ích, quản trị dữ liệu, mục tiêu, thời
#: gian, cỡ mẫu, căn cứ miễn đồng thuận, bản thông tin) KHÔNG được ghi ở đây — có thì bị bỏ qua và báo.
KHOI_HDD = ("gate_params", "G2", "ho_so_hdd")

#: Đường dẫn khoá lấy từ nguồn chung — khối riêng không ghi đè được.
DUONG_DUNG_CHUNG = (
    "meta.title", "meta.co_mau_du_kien",
    "bia.ten_de_tai", "bia.nghien_cuu_vien_chinh", "bia.co_quan_cong_tac", "bia.don_vi_chu_tri",
    "bia.thoi_gian_tu", "bia.thoi_gian_den", "bia.ma_so",
    "don_mau4.ho_ten_chu_nhiem", "don_mau4.chuc_vu", "don_mau4.don_vi", "don_mau4.dia_chi", "don_mau4.dien_thoai",
    "don_mau4.email", "don_mau4.ten_de_tai", "don_mau4.ten_don_vi_chu_tri", "don_mau4.dia_chi_don_vi_chu_tri",
    "ly_lich_khoa_hoc", "phu_luc_10.phan_hai", "phu_luc_10.thoi_gian.toan_bo",
    "phu_luc_11.ten_ncysh", "phu_luc_11.nghien_cuu_vien", "phu_luc_11.don_vi_chu_tri", "phu_luc_11.nguon_tai_tro",
    "phu_luc_11.tinh_chat.duoc_tai_tro", "phu_luc_11.luu_tru_so_nam", "phu_luc_11.muc.1c", "phu_luc_11.muc.6f",
    "phu_luc_11.muc.6f_i_dia_diem", "phu_luc_11.muc.6f_i_ai_tiep_can", "phu_luc_11.muc.7c", "phu_luc_11.muc.8a",
    "phu_luc_11.muc.8b", "phu_luc_11.muc.8c",
    "mien_icf.can_cu", "mien_icf.ten_de_tai", "mien_icf.chu_nhiem", "mien_icf.ngay", "mien_icf.ba_dieu_kien_cioms",
    "mien_icf.xung_dot_loi_ich", "mien_icf.cam_ket",
)


def _phan_duong(duong: str) -> list:
    return [int(p[1:-1]) if p.startswith("[") else p for p in re.findall(r"[^.\[\]]+|\[\d+\]", duong)]


def _dat_duong(d: dict, duong: str, gia_tri: Any) -> None:
    """Gán `gia_tri` vào đường dẫn kiểu «a.b.c» (tạo dict trung gian khi thiếu)."""
    phan = _phan_duong(duong)
    o: Any = d
    for k in phan[:-1]:
        if isinstance(k, int):
            o = o[k]
        else:
            if not isinstance(o.get(k), dict):
                o[k] = {}
            o = o[k]
    o[phan[-1]] = gia_tri


def _thuoc_dung_chung(duong: str) -> bool:
    return any(duong == g or duong.startswith(g + ".") or duong.startswith(g + "[") for g in DUONG_DUNG_CHUNG)


def _la_khoi(o: Any, duong: str = "") -> list[tuple[str, Any]]:
    """Mọi lá của khối riêng (giá trị không phải dict) kèm đường dẫn."""
    if isinstance(o, dict):
        ra: list[tuple[str, Any]] = []
        for k, v in o.items():
            ra += _la_khoi(v, f"{duong}.{k}" if duong else str(k))
        return ra
    return [(duong, o)]


def _so(n: HSC.NguonDeTai, truong: str) -> str:
    """Ô cá nhân: lấy từ sổ lý lịch lúc dựng Word (không ghi dữ liệu cá nhân vào JSON)."""
    if n.khoa_so:
        return HSC.so_ly_lich(n.khoa_so, truong)
    return HSC.goi_ky(f"tự khai của chủ nhiệm đề tài — {HSC.NHAN_TRUONG_SO.get(truong, truong)}")


def _tach_don_vi(don_vi: str) -> tuple[str, str]:
    """«Khoa A, Trung tâm B, Bệnh viện Quân y 175» → («Khoa A, Trung tâm B», «Bệnh viện Quân y 175»)."""
    phan = [x.strip() for x in don_vi.split(",") if x.strip()]
    if len(phan) >= 2:
        return ", ".join(phan[:-1]), phan[-1]
    return don_vi, BENH_VIEN


_HEADING_ICF = (
    ("1", re.compile(r"mục đích|vì sao|nếu đồng ý|thông tin thời gian|người thực hiện|quy trình", re.I)),
    ("2", re.compile(r"nguy cơ|bất tiện|rủi ro|lợi ích", re.I)),
    ("3", re.compile(r"bồi thường|tổn hại|tổn thương|điều trị khi", re.I)),
    ("4", re.compile(r"liên hệ", re.I)),
    ("5", re.compile(r"tự nguyện|rút lui", re.I)),
    ("6", re.compile(r"bảo mật", re.I)),
)
_PHU_LUC_ICF = re.compile(r"^PHỤ LỤC\s+([A-Z]\d?)\.\s+BẢN THÔNG TIN\b(.*)$", re.I)


def _thay_cho_trong_icf(van: str, n: HSC.NguonDeTai) -> str:
    """Chỗ chấm trong bản thông tin của đề cương ⇒ ô có nguồn (điện thoại chủ nhiệm từ sổ) hoặc dữ kiện cần nhập."""
    dong = []
    for d in van.split("\n"):
        if n.chu_nhiem_ho_ten and n.chu_nhiem_ho_ten in d and re.search(r"Điện thoại:\s*[.…]{3,}", d):
            d = re.sub(r"Điện thoại:\s*[.…]{3,}", "Điện thoại: " + _so(n, "mobile"), d)
        elif re.search(r"(Hội đồng|Đạo đức|Y đức)[^\n]*Điện thoại:\s*[.…]{3,}", d):
            d = re.sub(r"Điện thoại:\s*[.…]{3,}", "Điện thoại: " + HSC.can_nhap(
                "điện thoại liên hệ của Hội đồng (Thư ký hành chính Hội đồng cung cấp khi tiếp nhận hồ sơ)"), d)
        d = re.sub(r"Quyết định số\s*[.…]{3,}\s*ngày\s*[.…/]{3,}[.…/]*",
                   "Quyết định số " + HSC.can_nhap("số và ngày quyết định chấp thuận của Hội đồng — có sau khi"
                                                    " Hội đồng chấp thuận"), d)
        dong.append(d)
    return "\n".join(dong)


def _doan_tai_lieu_g2(van: str) -> list[tuple[str, str]]:
    """Đoạn «6c. BỒI THƯỜNG …» của bản thông tin trong gói G2 ⇒ [(tên đoạn, nội dung)] (chỗ PII ⇒ dòng chấm)."""
    ra: list[tuple[str, str]] = []
    for d in van.split("\n"):
        m = re.match(r"^(\d+[a-z]?)\.\s+(\S.{2,})$", d.strip())
        if m and m.group(2) == m.group(2).upper() and re.search(r"[A-ZĐ]", m.group(2)):  # tiêu đề IN HOA
            ra.append((m.group(2).strip().capitalize(), ""))
        elif ra and d.strip() and not d.startswith("---"):
            ra[-1] = (ra[-1][0], (ra[-1][1] + "\n" + d.strip()).strip())
        elif d.startswith("---"):
            ra.append(("", ""))
    return [(t, re.sub(r"\[PII[^\]]*\]", "……………………", v)) for t, v in ra if t and v]


def icf_tu_de_cuong(n: HSC.NguonDeTai) -> tuple[dict | None, list[dict]]:
    """(bản thông tin chính, các bản thông tin khác) dựng từ phụ lục «BẢN THÔNG TIN …» của đề cương nộp.

    Mỗi đoạn có nhãn đậm của phụ lục được xếp vào đúng mục 1–6 của Mẫu 8; đoạn không thuộc mục nào thành mục bổ sung
    (giữ tên đoạn). Câu chữ chép nguyên văn từ đề cương — một bản sự thật với tài liệu trình Hội đồng.
    """
    if not n.de_cuong:
        return None, []
    ban: list[dict] = []
    for h in HSC.tach_muc_md(n.de_cuong):
        m = _PHU_LUC_ICF.match(HSC.nfc(h["tieu_de"]))
        if not m or "MIỄN" in h["tieu_de"].upper():
            continue
        than = "\n".join(n.de_cuong.split("\n")[h["dau"] + 1:h["cuoi"]])
        doan = HSC.doan_dam(than)
        if not doan:
            continue
        muc: dict[str, list[str]] = {}
        bo_sung: dict[str, str] = {}
        so_bs = len(MUC_PHU_LUC_8)
        for nhan, noi_dung in doan:
            ten_goc = re.sub(r"^\d+[a-z]?\.\s*", "", nhan).strip()
            ten = ten_goc.rstrip(".:").strip()
            la_kinh_phi = bool(re.search(r"kinh phí|xung đột", ten, re.I))
            khoa = None if la_kinh_phi else next((k for k, mau in _HEADING_ICF if mau.search(ten)), None)
            if la_kinh_phi:
                khoa = next((k for k, v in bo_sung.items() if v == "Nguồn kinh phí và xung đột lợi ích"), None)
                if khoa is None:
                    so_bs += 1
                    khoa = str(so_bs)
                    bo_sung[khoa] = "Nguồn kinh phí và xung đột lợi ích"
            elif khoa is None:
                so_bs += 1
                khoa = str(so_bs)
                bo_sung[khoa] = ten
            noi_dung = re.sub(r"\*{1,3}([^*\n]+?)\*{1,3}", r"\1", noi_dung)
            if khoa in MUC_PHU_LUC_8:
                dau_nhan = ten_goc if ten_goc.endswith((".", ":")) else ten_goc + "."
                noi_dung = f"{dau_nhan}{chr(10) if noi_dung.startswith('- ') else ' '}{noi_dung}".strip()
            muc.setdefault(khoa, []).append(noi_dung)
        nghieng = re.search(r"^\*\((.+?)\)\*\s*$", than, re.M)
        phien_ban = nghieng.group(1).strip() if nghieng else ""
        hau = m.group(2).strip(" .,:")
        khoa_ban = re.sub(r"[^a-z0-9]+", "_", HSC.slug(re.sub(r"(?i)^.*THAM GIA\s*", "", hau) or hau)).strip("_")
        ban.append({
            "ten_nghien_cuu": n.ten_de_tai or CAN_BO_SUNG,
            "nha_tai_tro": n.nha_tai_tro or CAN_BO_SUNG,
            "nghien_cuu_vien_chinh": n.chu_nhiem or CAN_BO_SUNG,
            "don_vi_chu_tri": n.don_vi_chu_tri or CAN_BO_SUNG,
            "phien_ban": phien_ban,
            "muc": {k: _thay_cho_trong_icf("\n".join(v), n) for k, v in muc.items()},
            "ten_muc_bo_sung": bo_sung,
            "khoa": khoa_ban or f"phu_luc_{m.group(1).lower()}",
            "_nguon_phu_luc": f"đề cương nộp — {h['tieu_de']}",
        })
    if not ban:
        return None, []
    tl4 = _doan_tai_lieu_g2(str(_lay(n.gp("G2"), "da_soan", "tl4", default="") or ""))
    for b in ban:
        for k, mau in _HEADING_ICF:
            if k in b["muc"]:
                continue
            doan = next((v for ten, v in tl4 if mau.search(ten)), "")
            if doan:
                b["muc"][k] = _thay_cho_trong_icf(doan, n)
                b["_du_phong"] = b.get("_du_phong", []) + [k]
        for k in MUC_PHU_LUC_8:
            b["muc"].setdefault(k, CAN_BO_SUNG)
    chinh, khac = ban[0], ban[1:]
    chinh.pop("khoa", None)
    return chinh, khac


def ap_nguon_chung(du_lieu: dict, n: HSC.NguonDeTai, nguon: dict[str, str], ghi_chu: list[str]) -> set[str]:
    """Ghi đè các ô dùng chung bằng dữ kiện từ nguồn chung (đơn vị, chủ nhiệm, sổ lý lịch, kinh phí, xung đột lợi
    ích, quản trị dữ liệu, mục tiêu, thời gian, cỡ mẫu, căn cứ miễn đồng thuận, bản thông tin).

    Trả tập đường dẫn đã suy được — khối dữ kiện riêng không ghi đè các ô này (nguồn chung thắng khi có)."""
    da_suy: set[str] = set()

    def dat(duong: str, gia_tri: Any, tag: str) -> None:
        if gia_tri in (None, "", [], {}):
            return
        _dat_duong(du_lieu, duong, gia_tri)
        nguon[duong] = tag
        da_suy.add(duong)

    sm = "study_meta.json#administrative"
    if n.co_mau:
        dat("meta.co_mau_du_kien", HSC.so_viet(n.co_mau), "G3 (cỡ mẫu hiệu lực)")
    dat("bia.nghien_cuu_vien_chinh", n.chu_nhiem, f"{sm}.pi_title + principal_investigator")
    dat("bia.co_quan_cong_tac", n.don_vi_cong_tac, f"{sm}.pi_unit")
    dat("bia.don_vi_chu_tri", n.don_vi_chu_tri, f"{sm}.don_vi_chu_tri (lùi pi_unit)")
    dat("bia.ma_so", HSC.can_nhap("mã số đề tài — Phòng Khoa học Quân sự cấp khi đăng ký"), "dữ kiện khi triển khai")
    if _cho_trong(_lay(du_lieu, "bia", "chuyen_nganh")):
        dat("bia.chuyen_nganh", _so(n, "chuyen_nganh_dao_tao"), "sổ lý lịch cá nhân")
    tg = n.thoi_gian
    if tg:
        dat("bia.thoi_gian_tu", tg[0], "study_meta.json#gate_params.G1.study_period")
        dat("bia.thoi_gian_den", tg[1], "study_meta.json#gate_params.G1.study_period")
        dat("phu_luc_10.thoi_gian.toan_bo", {"tu": tg[0], "den": tg[1]}, "study_meta.json#gate_params.G1")
        dat("phu_luc_11.muc.7c", f"Từ {tg[0]} đến {tg[1]}", "study_meta.json#gate_params.G1.study_period")

    dat("don_mau4.ho_ten_chu_nhiem", n.chu_nhiem, sm)
    dat("don_mau4.chuc_vu", _so(n, "chuc_vu"), "sổ lý lịch cá nhân")
    dat("don_mau4.don_vi", n.don_vi_cong_tac, f"{sm}.pi_unit")
    dat("don_mau4.dia_chi", _so(n, "dia_chi_gui_thu"), "sổ lý lịch cá nhân")
    dat("don_mau4.dien_thoai", _so(n, "mobile"), "sổ lý lịch cá nhân")
    dat("don_mau4.email", _so(n, "email"), "sổ lý lịch cá nhân")
    dat("don_mau4.ten_don_vi_chu_tri", n.don_vi_chu_tri, f"{sm}.don_vi_chu_tri")
    dat("don_mau4.dia_chi_don_vi_chu_tri", _so(n, "dia_chi_co_quan"), "sổ lý lịch cá nhân (địa chỉ cơ quan)")
    ttc = n.thong_tin_chung
    noi, tgian = HSC.co(ttc.get("Đơn vị thực hiện")), HSC.co(ttc.get("Thời gian thực hiện"))
    if noi and tgian:
        dat("don_mau4.dia_diem_thoi_gian", f"{noi}; {tgian[0].lower() + tgian[1:]}",
            "đề cương nộp — Thông tin chung về đề tài")

    if n.chu_nhiem_ho_ten:
        ll = du_lieu.setdefault("ly_lich_khoa_hoc", [{}])
        nguoi = ll[0] if ll and isinstance(ll[0], dict) else {}
        nguoi.update({
            "vai_tro": "Chủ nhiệm đề tài", "ho_ten": n.chu_nhiem_ho_ten,
            "ngay_thang_nam_sinh": _so(n, "ngay_sinh"), "nam_nu": _so(n, "gioi_tinh"),
            "dia_chi_gui_thu": _so(n, "dia_chi_gui_thu"), "mobile": _so(n, "mobile"), "email": _so(n, "email"),
            "chuc_vu": _so(n, "chuc_vu"), "co_quan_noi_lam_viec": n.don_vi_cong_tac or CAN_BO_SUNG,
            "ten_lanh_dao_co_quan": _so(n, "lanh_dao"), "dien_thoai_lanh_dao_co_quan": _so(n, "dien_thoai_lanh_dao"),
            "dia_chi_co_quan": _so(n, "dia_chi_co_quan"),
            "trinh_do": {"hoc_vi": _so(n, "hoc_vi"), "nam_nhan_bang": _so(n, "nam_nhan_bang"),
                         "chuyen_nganh_dao_tao": _so(n, "chuyen_nganh_dao_tao"), "hoc_ham": _so(n, "hoc_ham")},
        })
        rec = n.ban_ghi_so
        if rec:
            kn = []
            for nhiem_vu, ds in (("Chủ nhiệm", rec.get("nhiem_vu_chu_tri")),
                                 ("Tham gia", rec.get("nhiem_vu_tham_gia"))):
                for m in ds or []:
                    if isinstance(m, dict) and HSC.co(m.get("ten")):
                        kn.append({"ten_de_tai": HSC.co(m.get("ten")), "nhiem_vu": nhiem_vu,
                                   "co_quan_chu_tri": HSC.co(m.get("chuong_trinh")), "nam": HSC.co(m.get("thoi_gian"))})
            nguoi["kinh_nghiem_nghien_cuu"] = kn or ["Chưa có đề tài, dự án trong 5 năm gần đây (theo lý lịch khoa"
                                                     " học đã khai)"]
        ll[0] = nguoi
        nguon["ly_lich_khoa_hoc"] = "study_meta.json#administrative + sổ lý lịch cá nhân"
        da_suy.add("ly_lich_khoa_hoc")

    khoa_bm, truong = _tach_don_vi(n.don_vi_cong_tac) if n.don_vi_cong_tac else ("", "")
    if n.chu_nhiem:
        dat("phu_luc_10.phan_hai.nghien_cuu_vien_chinh", {
            "ho_ten": n.chu_nhiem, "khoa_bo_mon": khoa_bm or CAN_BO_SUNG, "truong_don_vi": truong or CAN_BO_SUNG,
            "dien_thoai": _so(n, "mobile"), "thu_dien_tu": _so(n, "email"),
            "dia_chi_lien_he": _so(n, "dia_chi_co_quan"),
        }, f"{sm} + sổ lý lịch cá nhân")
        dat("phu_luc_11.nghien_cuu_vien", [{
            "ho_ten": n.chu_nhiem_ho_ten, "chuc_danh": n.chuc_danh or CAN_BO_SUNG,
            "chuc_vu_noi_cong_tac": f"{_so(n, 'chuc_vu')} — {n.don_vi_cong_tac}" if n.don_vi_cong_tac else CAN_BO_SUNG,
        }], f"{sm} + sổ lý lịch cá nhân")
    dat("phu_luc_11.don_vi_chu_tri", n.don_vi_chu_tri, f"{sm}.don_vi_chu_tri")

    # Kinh phí + xung đột lợi ích (cùng nguồn với gói G2)
    tu_tuc = n.tu_tuc
    if n.nha_tai_tro:
        dat("phu_luc_11.nguon_tai_tro", n.nha_tai_tro.rstrip(".") + ".", f"{sm}.sponsor")
    if tu_tuc is not None:
        dat("phu_luc_11.tinh_chat.duoc_tai_tro", not tu_tuc, "study_meta.json#gate_params.G2.external_funding")
    coi = n.coi
    if tu_tuc:
        dat("phu_luc_11.muc.8a", f"Không — {n.kinh_phi.rstrip('.')}; không có nhà tài trợ hay tổ chức thương mại.",
            "đề cương nộp — Thông tin chung (Kinh phí)")
        dat("phu_luc_11.muc.8b", "Không — đề tài tự túc kinh phí, không có quan hệ tài chính với tổ chức hay cá nhân"
            " nào có lợi ích liên quan đến kết quả.", "study_meta.json#gate_params.G2.external_funding")
    if coi.get("co_cau"):
        cau = ("Không có lợi ích tài chính và không nhận tài trợ. " if tu_tuc else "")
        cau += f"Có xung đột lợi ích không tài chính: {coi['co_cau'].rstrip('.')}."
        if coi.get("quan_ly"):
            cau += f" Biện pháp quản lý: {coi['quan_ly'].rstrip('.')}."
        dat("phu_luc_11.muc.8c", cau, "study_meta.json#gate_params.G2.coi (cùng nguồn với gói G2)")
    elif tu_tuc and coi:
        dat("phu_luc_11.muc.8c", "Không có lợi ích tài chính trực tiếp hay gián tiếp; không nhận tài trợ.",
            "study_meta.json#gate_params.G2.coi")

    # Quản trị dữ liệu (cùng nguồn với gói G2 và kế hoạch quản lý dữ liệu của đề cương)
    if n.so_nam_luu:
        dat("phu_luc_11.luu_tru_so_nam", f"{n.so_nam_luu:02d}", "đề cương nộp — Kế hoạch quản lý dữ liệu")
    khdl = n.ke_hoach_du_lieu
    han_luu = HSC.tim_nhan(khdl, "Thời hạn lưu")
    if han_luu:
        dat("phu_luc_11.muc.6f", han_luu[0].upper() + han_luu[1:],
            "đề cương nộp — Kế hoạch quản lý dữ liệu (thời hạn lưu)")
    if HSC.co(coi.get("noi_luu")):
        dat("phu_luc_11.muc.6f_i_dia_diem", coi["noi_luu"][0].upper() + coi["noi_luu"][1:],
            "study_meta.json#data_governance.storage_location")
    if HSC.co(coi.get("phan_quyen")):
        dat("phu_luc_11.muc.6f_i_ai_tiep_can", coi["phan_quyen"], "study_meta.json#data_governance.access")

    # Mục tiêu nguyên văn (G1)
    if n.muc_tieu:
        dat("phu_luc_11.muc.1c", "Mục tiêu: " + "; ".join(f"({i}) {m.rstrip('.')}" for i, m in
                                                           enumerate(n.muc_tieu, 1)) + ".",
            "study_meta.json#gate_params.G1.objectives (nguyên văn)")

    # Đơn đề nghị miễn đồng thuận
    if isinstance(du_lieu.get("mien_icf"), dict):
        dat("mien_icf.chu_nhiem", n.chu_nhiem, sm)
        dat("mien_icf.ngay", HSC.goi_ky("ngày ký Đơn đề nghị miễn thủ tục đồng thuận (chủ nhiệm ghi khi ký)"),
            "gói ký")
        ll = n.lap_luan_mien
        if all(HSC.co(ll.get(k)) for k, _nhan in CCDD.BA_DIEU_KIEN_CIOMS):
            dat("mien_icf.ba_dieu_kien_cioms", {k: ll[k] for k, _nhan in CCDD.BA_DIEU_KIEN_CIOMS},
                "study_meta.json#gate_params.G2.mien_icf_lap_luan (cùng nguồn với gói G2 và đề cương)")
        bm = {}
        loai = HSC.co(_lay(n.gp("G2"), "da_soan", "tl6_loai_du_lieu")) or HSC.tim_nhan(n.dao_duc, "Bảo mật")
        for k, v in (("loai_du_lieu", loai), ("ma_hoa", HSC.tim_nhan(khdl, "Khử định danh", "Định danh")),
                     ("quyen_truy_cap", HSC.tim_nhan(khdl, "Phân quyền")), ("ke_hoach_huy", han_luu)):
            if HSC.co(v):
                bm[k] = re.sub(r"^\s*Cụ thể:\s*", "", HSC.nfc(v)).strip()
        for k, v in bm.items():
            dat(f"mien_icf.dam_bao_bao_mat.{k}", v, "đề cương nộp — Kế hoạch quản lý dữ liệu + gói G2 (loại dữ liệu)")
        if coi.get("tom_tat"):
            dat("mien_icf.xung_dot_loi_ich", coi["tom_tat"].rstrip(".") + "." + (
                f" Biện pháp quản lý: {coi['quan_ly'].rstrip('.')}." if coi.get("quan_ly") else ""),
                "study_meta.json#gate_params.G2.coi")
        pl_mien = HSC.than_muc(n.de_cuong, "ĐƠN ĐỀ NGHỊ MIỄN")
        m = re.search(r"Nhóm nghiên cứu cam kết:\s*(.+)", pl_mien)
        if m:
            dat("mien_icf.cam_ket", [x.strip().rstrip(".") + "." for x in m.group(1).split(";") if x.strip()],
                "đề cương nộp — Phụ lục đơn đề nghị miễn đồng thuận")

    htx = HSC.tim_nhan(n.dao_duc, "Hình thức xét duyệt").lower()
    if "rút gọn" in htx:
        tag = "đề cương nộp — Đạo đức trong nghiên cứu (hình thức xét duyệt)"
        dat("meta.quy_trinh_de_xuat", "rut_gon", tag)
        dat("phu_luc_10.phan_khai.ket_luan_nghien_cuu_vien_chinh", "rut_gon", tag)
    elif "đầy đủ" in htx:
        dat("meta.quy_trinh_de_xuat", "day_du", "đề cương nộp — Đạo đức trong nghiên cứu (hình thức xét duyệt)")

    # Bản thông tin + phiếu đồng ý: nguyên văn phụ lục của đề cương nộp
    if du_lieu.get("icf") is not None:
        chinh, khac = icf_tu_de_cuong(n)
        if chinh:
            du_lieu["icf"] = {k: v for k, v in chinh.items() if not k.startswith("_")}
            nguon["icf"] = chinh["_nguon_phu_luc"]
            da_suy.update({"icf", "icf_khac"})
            du_lieu["icf_khac"] = [{k: v for k, v in b.items() if not k.startswith("_")} for b in khac]
            if khac:
                nguon["icf_khac"] = "; ".join(b["_nguon_phu_luc"] for b in khac)
            for b in [chinh] + khac:
                if b.get("_du_phong"):
                    ghi_chu.append(f"{b['_nguon_phu_luc']}: thiếu đoạn cho mục {', '.join(b['_du_phong'])} của Mẫu 8 —"
                                   " lấy đoạn tương ứng của bản thông tin trong gói G2; nên bổ sung vào phụ lục"
                                   " đề cương để hai bản trùng nhau.")
            ten_khac = [f"Bản thông tin và phiếu đồng ý riêng — {b['phien_ban'] or b['khoa']}" for b in khac]
            if ten_khac:
                tl = _van_ban_list(_lay(du_lieu, "don_mau4", "ho_so_kem_theo", "tai_lieu_khac"))
                du_lieu["don_mau4"]["ho_so_kem_theo"]["tai_lieu_khac"] = tl + [t for t in ten_khac if t not in tl]
        else:
            ghi_chu.append("Đề cương nộp không có phụ lục «BẢN THÔNG TIN …» có đoạn đánh số — bản thông tin lấy"
                           " từ khối riêng hoặc để [CẦN].")
    return da_suy


def ap_khoi_ho_so(du_lieu: dict, n: HSC.NguonDeTai, nguon: dict[str, str], ghi_chu: list[str],
                  da_suy: set[str] | None = None) -> None:
    """Áp khối dữ kiện riêng `gate_params.G2.ho_so_hdd` (câu trả lời của bảng kiểm/phiếu). Khoá dùng chung và ô đã
    suy được từ nguồn chung bị bỏ (một bản sự thật)."""
    da_suy = da_suy or set()
    khoi = _lay(n.meta, *KHOI_HDD)
    if not isinstance(khoi, dict) or not khoi:
        return
    bo = []
    for duong, gia_tri in _la_khoi(khoi):
        if _thuoc_dung_chung(duong) or any(duong == x or duong.startswith(x + ".") for x in da_suy):
            bo.append(duong)
            continue
        if duong.startswith(("icf.", "icf_khac")) and nguon.get("icf"):
            bo.append(duong)
            continue
        if duong.split(".")[0] == "mien_icf" and not isinstance(du_lieu.get("mien_icf"), dict):
            continue
        if duong.split(".")[0] == "icf" and du_lieu.get("icf") is None:
            continue
        _dat_duong(du_lieu, duong, copy.deepcopy(gia_tri))
        nguon[duong] = "study_meta.json#" + ".".join(KHOI_HDD) + "." + duong
    if bo:
        ghi_chu.append(f"Khối {'.'.join(KHOI_HDD)} có {len(bo)} khoá thuộc nguồn chung — bỏ qua (một bản sự thật): "
                       + ", ".join(bo[:8]) + ("…" if len(bo) > 8 else ""))


def _hop_nhat_bo_sung(cu: dict, moi: dict) -> dict:
    """Hợp nhất đệ quy: giữ giá trị CŨ, chỉ thêm khoá MỚI còn thiếu."""
    ra = copy.deepcopy(cu)
    for k, v in moi.items():
        if k not in ra:
            ra[k] = copy.deepcopy(v)
        elif isinstance(v, dict) and isinstance(ra[k], dict):
            ra[k] = _hop_nhat_bo_sung(ra[k], v)
        # list và scalar: giữ nguyên bản cũ, không ghi đè
    return ra


def nang_cap_schema(d: dict) -> tuple[dict, list[str]]:
    """Nâng JSON 1.0 → 2.0 TRONG BỘ NHỚ, không mất giá trị đã sửa. Trả (bản mới, ghi chú thay đổi).

    Quy tắc 1.0 → 2.0: khoá cấp 1 `icf_<x>` → `icf_khac`; tên NCV chính của Phụ lục 10 lấy từ bìa; số năm lưu trữ
    lấy từ câu mục 6(f); căn cứ miễn đồng thuận SAI
    (TT43 Điều 15/Helsinki §29) được thay bằng căn cứ đã đối chiếu; ngày làm đơn dạng ISO (máy chép từ ngày sinh gói
    G2) trả về ô bác sĩ điền; thiếu ba điều kiện CIOMS ⇒ thêm ô [CẦN BỔ SUNG]. Danh sách phụ lục của phiếu thu thập
    KHÔNG suy từ chuỗi mô tả `phieu_thu_thap.nguon` (chuỗi tự do, từng ghi thiếu phụ lục) — lượt trích bổ sung
    `phu_luc` theo luật chọn mặc định.
    """
    d = copy.deepcopy(d)
    ghi: list[str] = []
    phien_ban = str(d.get("phien_ban_schema") or "1.0")
    nguon = d.setdefault("_nguon", {}) if isinstance(d.get("_nguon", {}), dict) else {}

    for k in [k for k in list(d) if k.startswith("icf_") and k != "icf_khac" and isinstance(d.get(k), dict)]:
        ban = d.pop(k)
        ban.setdefault("khoa", k[len("icf_"):])
        d.setdefault("icf_khac", []).append(ban)
        ghi.append(f"chuyển `{k}` vào `icf_khac`")

    ncv = _lay(d, "phu_luc_10", "phan_hai", "nghien_cuu_vien_chinh")
    if isinstance(ncv, dict) and "ho_ten" not in ncv:
        ncv["ho_ten"] = _lay(d, "bia", "nghien_cuu_vien_chinh", default=CAN_BAC_SI_DIEN)
        ghi.append("Phụ lục 10: thêm `ho_ten` NCV chính (lấy từ bìa)")

    pl11 = d.get("phu_luc_11")
    if isinstance(pl11, dict) and "luu_tru_so_nam" not in pl11:
        m = re.search(r"(\d+)\s*năm", str(_lay(pl11, "muc", "6f", default="")))
        if m:
            pl11["luu_tru_so_nam"] = f"{int(m.group(1)):02d}"
            nguon["phu_luc_11.luu_tru_so_nam"] = "phu_luc_11.muc.6f (nâng cấp schema)"
            ghi.append("Phụ lục 11: thêm `luu_tru_so_nam` từ mục 6(f)")

    mi = d.get("mien_icf")
    if isinstance(mi, dict):
        if CCDD.can_cu_sai(str(mi.get("can_cu", ""))):
            mi["can_cu"] = CCDD.CAN_CU_MIEN_DONG_THUAN
            ghi.append("mien_icf: thay căn cứ SAI (TT43 Điều 15/Helsinki §29) bằng căn cứ đã đối chiếu")
        if phien_ban == "1.0" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(mi.get("ngay", "")).strip()):
            mi["ngay"] = CAN_BAC_SI_DIEN
            ghi.append("mien_icf: ngày làm đơn chép từ ngày sinh gói G2 ⇒ trả về ô bác sĩ điền")
        if not isinstance(mi.get("ba_dieu_kien_cioms"), dict):
            mi["ba_dieu_kien_cioms"] = {khoa: CAN_BO_SUNG for khoa, _n in CCDD.BA_DIEU_KIEN_CIOMS}
            ghi.append("mien_icf: thêm ô lập luận ba điều kiện CIOMS 2016 Hướng dẫn 10")
        mi.setdefault("kinh_gui", KINH_GUI_HOI_DONG)

    if phien_ban != SCHEMA_VERSION:
        d["phien_ban_schema"] = SCHEMA_VERSION
        ghi.append(f"phiên bản schema {phien_ban} → {SCHEMA_VERSION}")
    return d, ghi


def doc_json_da_nang_cap(exports_root: Path, study: str, duong_dan_json: Path) -> tuple[dict, list[str]]:
    """Đọc JSON → nâng cấp schema → bổ sung khoá mới từ một lượt trích mới (không ghi đè giá trị cũ)."""
    d = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    d, ghi = nang_cap_schema(d)
    try:
        moi, _ = trich_du_kien(exports_root, study)
    except FileNotFoundError:
        return d, ghi
    return _hop_nhat_bo_sung(d, moi), ghi


def lenh_trich(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    try:
        moi, ghi_chu = trich_du_kien(exports_root, args.study)
    except FileNotFoundError as exc:
        print(f"LỖI: {exc}")
        return 2
    for g in ghi_chu:
        print(f"[chú ý] {g}")

    duong_dan_json = _doc_hdd(exports_root, args.study) / "HO_SO_HDD_BVQY175.json"
    if duong_dan_json.is_file():
        cu = json.loads(duong_dan_json.read_text(encoding="utf-8"))
        if args.ghi_de:
            ket_qua = moi
            print("Ghi ĐÈ toàn bộ (do --ghi-de).")
        else:
            cu, thay_doi = nang_cap_schema(cu)
            for t in thay_doi:
                print(f"[nâng cấp] {t}")
            ket_qua = _hop_nhat_bo_sung(cu, moi)
            print("Đã có JSON — chỉ bổ sung khoá còn thiếu, giữ nguyên giá trị đã sửa.")
    else:
        ket_qua = moi

    so_can = _dem_can(ket_qua)
    print(f"Số ô còn [CẦN...]: {so_can}")

    if not args.ghi:
        print("(chạy khô — thêm --ghi để lưu tệp)")
        print(json.dumps(ket_qua, ensure_ascii=False, indent=1)[:4000])
        return 0

    duong_dan_json.parent.mkdir(parents=True, exist_ok=True)
    if duong_dan_json.is_file():
        sao_luu = duong_dan_json.with_suffix(
            f".bak-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        )
        shutil.copy2(duong_dan_json, sao_luu)
        print(f"Đã sao lưu bản cũ: {sao_luu}")
    duong_dan_json.write_text(
        json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Đã ghi: {duong_dan_json}")
    return 0


def _dem_can(obj: Any) -> int:
    dem = 0
    if isinstance(obj, str):
        if "[CẦN" in obj:
            dem += 1
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k == "_nguon":
                continue
            dem += _dem_can(v)
    elif isinstance(obj, list):
        for v in obj:
            dem += _dem_can(v)
    return dem


# ---------------------------------------------------------------------------
# Tiện ích Word
# ---------------------------------------------------------------------------


class MauKhongKhop(Exception):
    """Mẫu bệnh viện không có nhãn công cụ cần (mẫu đổi/không đúng bản)."""


def _can_docx() -> None:
    if docx is None:
        raise RuntimeError(
            "Thiếu python-docx — cài bằng: pip install python-docx (hoặc dùng venv ~/.ebm-venv)."
        )


def _run(p, text: str, bold: bool | None = None, italic: bool | None = None, size: int = CO_CHU):
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    rpr = r._r.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is not None:
        rfonts.set(qn("w:eastAsia"), FONT)
    if bold is not None:
        r.bold = bold
    if italic is not None:
        r.italic = italic
    return r


def dat_text(p, text: str, giu_dinh_dang: bool = False, **kw) -> None:
    """Thay toàn bộ chữ của đoạn. giu_dinh_dang=True: ghi vào run đầu, giữ định dạng gốc."""
    if giu_dinh_dang and p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
        return
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    _run(p, text, **kw)


def chen_sau(p, text: str = "", **kw):
    moi = OxmlElement("w:p")
    p._p.addnext(moi)
    q = Paragraph(moi, p._parent)
    if text:
        _run(q, text, **kw)
    return q


def xoa(p) -> None:
    p._p.getparent().remove(p._p)


def dau(v: Any) -> str:
    return "☒" if v is True else "☐"


def _thay_o(p, dau_seq: list[str]) -> int:
    """Thay lần lượt từng «FORMCHECKBOX» trong đoạn bằng ký hiệu trong `dau_seq` (thiếu ⇒ ☐)."""
    idx = 0
    for r in p.runs:
        while "FORMCHECKBOX" in r.text:
            ky = dau_seq[idx] if idx < len(dau_seq) else "☐"
            r.text = r.text.replace("FORMCHECKBOX", ky, 1)
            idx += 1
    return idx


def thay_hop(p, v: Any, them: str = "", danh_dau_chua_quyet: bool = True) -> None:
    """Thay MỌI «FORMCHECKBOX» trong đoạn bằng ☒/☐ rồi nối phần giải thích; None ⇒ ☐ + [CẦN BÁC SĨ XÁC NHẬN]."""
    if isinstance(v, str) and HSC.DAU_DANH_DAU.search(v):  # ô thuộc gói ký/dữ kiện cần nhập ⇒ ☐ + dấu
        them, v, danh_dau_chua_quyet = f"{them} {v}".strip(), None, False
    for r in p.runs:
        if "FORMCHECKBOX" in r.text:
            r.text = r.text.replace("FORMCHECKBOX", dau(v))
    them = (them or "").strip()
    if v is None and danh_dau_chua_quyet and "[CẦN" not in them:
        them = f"{them} {CHUA_QUYET}".strip()
    if them:
        _run(p, "  " + them)


def don_hop_con_lai(doc) -> None:
    """Ô đánh dấu còn lại (không thuộc dữ kiện của nghiên cứu viên) ⇒ ☐."""
    doan = list(doc.paragraphs)
    for bang in doc.tables:
        for hang in bang.rows:
            for o in hang.cells:
                doan.extend(o.paragraphs)
    for p in doan:
        for r in p.runs:
            if "FORMCHECKBOX" in r.text:
                r.text = r.text.replace("FORMCHECKBOX", "☐")


def doan_trong_ke(ps, i: int, toi_da: int = 6):
    """Đoạn trống đầu tiên sau ps[i] (trong toi_da đoạn); không có thì chèn mới."""
    for j in range(i + 1, min(i + 1 + toi_da, len(ps))):
        if not ps[j].text.strip():
            return ps[j]
        if j > i + 1 and ps[j].text.strip():
            break
    return chen_sau(ps[i])


def ghi_nhieu_dong(p, text: str) -> None:
    """Ghi văn bản (có thể nhiều dòng '\\n' — ngắt dòng mềm) vào đoạn p, Times New Roman 12."""
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    _run(p, text)


def _chuan(s: str) -> str:
    return " ".join(_nfc(s).split())


def tim(ps, bat_dau: str, tu: int = 0, den: int | None = None) -> int | None:
    """Chỉ số đoạn đầu tiên (từ `tu`) bắt đầu bằng `bat_dau` (so sánh đã chuẩn hoá khoảng trắng)."""
    khoa = _chuan(bat_dau)
    for i in range(tu, len(ps) if den is None else min(den, len(ps))):
        if _chuan(ps[i].text).startswith(khoa):
            return i
    return None


def tim_chua(ps, *cum: str, tu: int = 0, den: int | None = None) -> int | None:
    """Chỉ số đoạn đầu tiên chứa MỌI cụm (không phân biệt hoa thường)."""
    can = [_chuan(c).lower() for c in cum]
    for i in range(tu, len(ps) if den is None else min(den, len(ps))):
        t = _chuan(ps[i].text).lower()
        if all(c in t for c in can):
            return i
    return None


def _noi_gia_tri(p, gia_tri: str) -> None:
    """«Nhãn:» → «Nhãn: giá trị», giữ định dạng run đầu; giá trị rỗng ⇒ để nguyên."""
    if gia_tri is None or str(gia_tri) == "":
        return
    dat_text(p, f"{p.text.rstrip()} {gia_tri}", giu_dinh_dang=True)


class _NhatKyMau:
    """Gom nhãn không thấy trong mẫu — báo ra, không làm sập lệnh."""

    def __init__(self, ten_mau: str) -> None:
        self.ten_mau = ten_mau
        self.thieu: list[str] = []

    def can(self, chi_so: int | None, nhan: str) -> int | None:
        if chi_so is None:
            self.thieu.append(nhan)
        return chi_so


def _van_ban_list(gia_tri: Any) -> list[str]:
    if gia_tri is None or gia_tri == "":
        return []
    if isinstance(gia_tri, (list, tuple)):
        return [str(x) for x in gia_tri if str(x).strip()]
    return [str(gia_tri)]


def _nghien_cuu_mot_co_quan(d: dict) -> bool | None:
    """True khi đã chốt chỉ một cơ quan; False khi nhiều cơ quan; None khi chưa chốt."""
    if _lay(d, "phu_luc_11", "nhieu_co_quan"):
        return False
    c6 = _lay(d, "phu_luc_10", "phan_nam", "C6_nhieu_co_quan", "gia_tri")
    if c6 is False:
        return True
    if c6 is True:
        return False
    return None


# ---------------------------------------------------------------------------
# Từng mẫu
# ---------------------------------------------------------------------------


def dung_bia(mau: Path, out: Path, d: dict, nhat_ky: _NhatKyMau) -> Path:
    """Mẫu 2 (bìa Thuyết minh) và Mẫu 3 (bìa Hồ sơ đăng ký)."""
    doc = docx.Document(str(mau))
    b = d["bia"]
    mien = d.get("mien_icf") is not None and d.get("icf") is None
    mot_co_quan = _nghien_cuu_mot_co_quan(d)
    thay_ten = False
    for p in doc.paragraphs:
        t = _chuan(p.text)
        if t == "TÊN ĐỀ TÀI":
            dat_text(p, str(b["ten_de_tai"]).upper(), giu_dinh_dang=True)
            thay_ten = True
        elif t.startswith("Mã số:"):
            _noi_gia_tri(p, b.get("ma_so", ""))
        elif t.startswith("Chuyên ngành:"):
            _noi_gia_tri(p, b.get("chuyen_nganh", ""))
        elif t.startswith("Nghiên cứu viên chính (Chủ nhiệm đề tài):"):
            _noi_gia_tri(p, b.get("nghien_cuu_vien_chinh", ""))
        elif t.startswith("Cơ quan công tác:"):
            _noi_gia_tri(p, b.get("co_quan_cong_tac", ""))
        elif t.startswith("Đơn vị chủ trì:"):
            _noi_gia_tri(p, b.get("don_vi_chu_tri", ""))
        elif t.startswith("Thời gian thực hiện:"):
            dat_text(p, f"Thời gian thực hiện: Từ tháng {b['thoi_gian_tu']} đến tháng {b['thoi_gian_den']}",
                     giu_dinh_dang=True)
        elif t.startswith("TP. HỒ CHÍ MINH, 20"):
            dat_text(p, f"TP. HỒ CHÍ MINH, {b['nam_nop']}", giu_dinh_dang=True)
        elif mien and t.startswith("6. Phiếu đồng thuận"):
            dat_text(p, "6. Đơn đề nghị miễn thủ tục đồng thuận tham gia nghiên cứu (thay phiếu đồng thuận).",
                     giu_dinh_dang=True)
        elif t.startswith("8. Giấy chứng nhận chấp thuận") and mot_co_quan:
            _noi_gia_tri(p, f"(không áp dụng — nghiên cứu chỉ thực hiện tại {BENH_VIEN})")
    if not thay_ten:
        nhat_ky.thieu.append("TÊN ĐỀ TÀI")
    doc.save(str(out))
    return out


HO_SO_KEM_THEO_NHAN = (
    ("phụ lục 10", "bang_kiem_rut_gon"),
    ("phụ lục 11", "phieu_day_du"),
    ("đề cương", "de_cuong"),
    ("bảng câu hỏi", "bang_cau_hoi_phu_luc"),
    ("phiếu chấp thuận", "phieu_chap_thuan"),
    ("trang thông tin", "trang_thong_tin"),
    ("lý lịch", "ly_lich_khoa_hoc"),
    ("tài liệu, văn bản", "tai_lieu_khac"),
)


def dung_don_mau4(mau: Path, out: Path, d: dict, quy_trinh: str, nhat_ky: _NhatKyMau) -> Path:
    """Mẫu 4 — Đơn xin đánh giá đạo đức: điền chủ nhiệm + đơn vị chủ trì (địa chỉ, điện thoại), ô hồ sơ kèm theo
    theo ĐÚNG nhãn (không theo vị trí), và ghi TÊN từng tài liệu khác dưới ô «tài liệu, văn bản»."""
    doc = docx.Document(str(mau))
    don = d["don_mau4"]
    qua_don_vi = False
    for p in doc.paragraphs:
        t = _chuan(p.text)
        if t.startswith("Họ và tên Chủ nhiệm đề tài"):
            dat_text(p, f"Họ và tên Chủ nhiệm đề tài (dự án): {don.get('ho_ten_chu_nhiem', '')}".rstrip(),
                     giu_dinh_dang=True)
        elif t.startswith("Tên đơn vị chủ trì"):
            dat_text(p, f"Tên đơn vị chủ trì đề tài (dự án): {don.get('ten_don_vi_chu_tri', '')}".rstrip(),
                     giu_dinh_dang=True)
            qua_don_vi = True
        elif t.startswith("Tên đề tài (dự án)"):
            dat_text(p, f"Tên đề tài (dự án) xin đánh giá đạo đức trong nghiên cứu: {don.get('ten_de_tai', '')}"
                     .rstrip(), giu_dinh_dang=True)
        elif t.startswith("Đơn vị:"):
            dat_text(p, f"Đơn vị: {don.get('don_vi', '')}".rstrip(), giu_dinh_dang=True)
        elif t.startswith("Địa chỉ:"):
            gia_tri = don.get("dia_chi_don_vi_chu_tri" if qua_don_vi else "dia_chi", "")
            dat_text(p, f"Địa chỉ: {gia_tri}".rstrip(), giu_dinh_dang=True)
        elif t.startswith("Điện thoại:"):
            if qua_don_vi:
                dt, fax, em = (don.get("dien_thoai_don_vi", ""), don.get("fax_don_vi", ""),
                               don.get("email_don_vi", ""))
            else:
                dt, fax, em = don.get("dien_thoai", ""), don.get("fax", ""), don.get("email", "")
            dat_text(p, f"Điện thoại: {dt}\tFax: {fax}\tEmail: {em}", giu_dinh_dang=True)
        elif t.startswith("Địa điểm, thời gian triển khai"):
            dat_text(p, f"Địa điểm, thời gian triển khai nghiên cứu: {don.get('dia_diem_thoi_gian', '')}".rstrip(),
                     giu_dinh_dang=True)

    ho_so = dict(don.get("ho_so_kem_theo") or {})
    ho_so["bang_kiem_rut_gon"] = quy_trinh in ("rut_gon", "ca_hai")
    ho_so["phieu_day_du"] = quy_trinh in ("day_du", "ca_hai")
    tai_lieu_khac = _van_ban_list(ho_so.get("tai_lieu_khac"))
    ho_so["tai_lieu_khac"] = bool(tai_lieu_khac)
    ps = doc.paragraphs
    thu_tu = [k for _n, k in HO_SO_KEM_THEO_NHAN]
    vi_tri_tai_lieu: int | None = None
    so_o = 0
    for i, p in enumerate(ps):
        if "FORMCHECKBOX" not in p.text:
            continue
        thap = p.text.lower()
        khoa = next((k for nhan, k in HO_SO_KEM_THEO_NHAN if nhan in thap), None)
        if khoa is None and so_o < len(thu_tu):
            khoa = thu_tu[so_o]  # mẫu đổi chữ ⇒ lùi về thứ tự chuẩn của bệnh viện
        so_o += 1
        if khoa is None:
            continue
        gia_tri = ho_so.get(khoa)
        thay_hop(p, gia_tri if gia_tri is None else bool(gia_tri))
        if khoa == "tai_lieu_khac":
            vi_tri_tai_lieu = i
    if tai_lieu_khac:
        if vi_tri_tai_lieu is None:
            nhat_ky.thieu.append("ô «Các tài liệu, văn bản…»")
        else:
            q = ps[vi_tri_tai_lieu]
            for ten in tai_lieu_khac:
                ke = q._p.getnext()
                if ke is not None and ke.tag == qn("w:p") and not Paragraph(ke, q._parent).text.strip():
                    q = Paragraph(ke, q._parent)
                    dat_text(q, f"        – {ten}")
                else:
                    q = chen_sau(q, f"        – {ten}")
    don_hop_con_lai(doc)
    doc.save(str(out))
    return out


_LY_LICH_NHAN = (
    ("1. Họ và tên:", ("ho_ten",)),
    ("2. Ngày tháng năm sinh:", ("ngay_thang_nam_sinh",)),
    ("3. Nam, nữ:", ("nam_nu",)),
    ("4. Địa chỉ gửi thư:", ("dia_chi_gui_thu",)),
    ("5. Mobile:", ("mobile",)),
    ("6. E-mail:", ("email",)),
    ("7. Chức vụ:", ("chuc_vu",)),
    ("8. Cơ quan - nơi làm việc:", ("co_quan_noi_lam_viec",)),
    ("Tên người Lãnh đạo cơ quan", ("ten_lanh_dao_co_quan",)),
    ("Điện thoại người Lãnh đạo cơ quan:", ("dien_thoai_lanh_dao_co_quan",)),
    ("Địa chỉ cơ quan:", ("dia_chi_co_quan",)),
    ("Học vị:", ("trinh_do", "hoc_vi")),
    ("Năm nhận bằng:", ("trinh_do", "nam_nhan_bang")),
    ("Chuyên ngành đào tạo:", ("trinh_do", "chuyen_nganh_dao_tao")),
    ("Học hàm:", ("trinh_do", "hoc_ham")),
)


def _dong_kinh_nghiem(muc: Any) -> str:
    if isinstance(muc, dict):
        phan = [("Tên đề tài/dự án", muc.get("ten_de_tai")), ("Nhiệm vụ", muc.get("nhiem_vu")),
                ("Cơ quan chủ trì", muc.get("co_quan_chu_tri")), ("Năm", muc.get("nam"))]
        return "; ".join(f"{n}: {v}" for n, v in phan if v)
    return str(muc)


def dung_ly_lich(mau: Path, out: Path, nguoi: dict, nhat_ky: _NhatKyMau) -> Path:
    """Mẫu 5 — Lý lịch khoa học: đủ 15 trường + kinh nghiệm nghiên cứu 5 năm gần đây."""
    doc = docx.Document(str(mau))
    ps = doc.paragraphs
    for nhan, duong in _LY_LICH_NHAN:
        i = tim(ps, nhan)
        if i is None:
            nhat_ky.thieu.append(nhan)
            continue
        gia_tri = _lay(nguoi, *duong, default="")
        dat_text(ps[i], f"{ps[i].text.rstrip()} {gia_tri}".rstrip(), giu_dinh_dang=True)
    i = tim(ps, "Năm bắt đầu - kết thúc")
    if i is None:
        nhat_ky.thieu.append("Năm bắt đầu - kết thúc")
    else:
        kinh_nghiem = nguoi.get("kinh_nghiem_nghien_cuu") or []
        if isinstance(kinh_nghiem, str):
            kinh_nghiem = [kinh_nghiem]
        dong = [_dong_kinh_nghiem(m) for m in kinh_nghiem if _dong_kinh_nghiem(m)]
        if not dong:
            dong = [f"{CAN_BAC_SI_DIEN} (đề tài/dự án 5 năm gần đây; ghi «Chưa có» nếu không có)"]
        q = ps[i]
        for t in dong:
            ke = q._p.getnext()
            if ke is not None and ke.tag == qn("w:p") and not Paragraph(ke, q._parent).text.strip():
                q = Paragraph(ke, q._parent)
                dat_text(q, f"– {t}")
            else:
                q = chen_sau(q, f"– {t}")
    doc.save(str(out))
    return out


def dung_phu_luc_10(mau: Path, out: Path, d: dict, nhat_ky: _NhatKyMau) -> Path:
    """Mẫu 6 — Phụ lục 10, Bảng kiểm lựa chọn quy trình xem xét (rút gọn)."""
    doc = docx.Document(str(mau))
    pl = d["phu_luc_10"]
    ps = doc.paragraphs
    for nhan, khoa in (("A. con người", "doi_tuong_con_nguoi"), ("B. động vật", "doi_tuong_dong_vat")):
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is not None:
            j = next((x for x in range(i + 1, min(i + 4, len(ps))) if "FORMCHECKBOX" in ps[x].text), None)
            if j is not None:
                thay_hop(ps[j], pl["phan_mot"].get(khoa))

    ncv = pl["phan_hai"]["nghien_cuu_vien_chinh"]
    ten_ncv = ncv.get("ho_ten") or d["bia"].get("nghien_cuu_vien_chinh", "")
    cap = [
        ("Tên NCYSH", pl["phan_hai"].get("ten_ncysh", "")),
        ("Nghiên cứu viên chính", ten_ncv),
        ("KHOA/ BỘ MÔN", ncv.get("khoa_bo_mon", "")),
        ("TRƯỜNG/ĐƠN VỊ", ncv.get("truong_don_vi", "")),
        ("ĐIÊN THOAI", ncv.get("dien_thoai", "")),
        ("THƯ ĐIÊN TỬ", ncv.get("thu_dien_tu", "")),
        ("ĐỊA CHỈ LIÊN HỆ", ncv.get("dia_chi_lien_he", "")),
    ]
    tu = 0
    for nhan, gt in cap:
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, nhan, tu), nhan)
        if i is None:
            continue
        dat_text(doan_trong_ke(ps, i), str(gt or ""))
        tu = i + 1
    gs = pl["phan_hai"].get("nguoi_giam_sat") or {}
    i_gs = tim(doc.paragraphs, "Người giám sát/hướng dẫn")
    if i_gs is not None and any(str(v).strip() for v in gs.values()):
        for nhan, k in (("NƠI LÀM VIỆC", "noi_lam_viec"), ("ĐIÊN THOAI", "dien_thoai"),
                        ("THƯ ĐIÊN TỬ", "thu_dien_tu")):
            ps = doc.paragraphs
            j = tim(ps, nhan, i_gs)
            if j is not None:
                dat_text(doan_trong_ke(ps, j), str(gs.get(k, "")))

    # Phần ba: A1–A10, B1–B11 (mẫu xếp hai cột ⇒ tìm nhãn rồi ô đánh dấu ngay sau nhãn)
    ps = doc.paragraphs
    i_ba = tim(ps, "PHẦN BA") or 0
    i_bon = tim(ps, "PHẦN BỐN", i_ba) or len(ps)
    nhan_idx = []
    for i in range(i_ba, i_bon):
        t = ps[i].text.strip()
        m = re.match(r"^A(\d+)\.", t)
        if m:
            nhan_idx.append((i, "A", f"A{m.group(1)}"))
            continue
        m = re.match(r"^B\.(\d+)\s", t)
        if m:
            nhan_idx.append((i, "B", f"B{m.group(1)}"))
    da_dien = set()
    for n, (i, nhom, k) in enumerate(nhan_idx):
        ket_thuc = nhan_idx[n + 1][0] if n + 1 < len(nhan_idx) else min(i + 4, i_bon)
        muc = pl["phan_ba"][nhom].get(k) or {"gia_tri": None, "giai_thich": ""}
        hop = next((ps[j] for j in range(i + 1, ket_thuc) if "FORMCHECKBOX" in ps[j].text), None)
        nhan_tl = "Có" if muc.get("gia_tri") is True else ("Không" if muc.get("gia_tri") is False else "")
        gt = muc.get("giai_thich") or nhan_tl
        if hop is None:  # A10 trong mẫu không có ô ⇒ vẽ ô ngay sau nhãn
            them = gt if muc.get("gia_tri") is not None or "[CẦN" in gt else f"{gt} {CHUA_QUYET}".strip()
            _run(ps[i], f"   {dau(muc.get('gia_tri'))}  {them}")
        else:
            thay_hop(hop, muc.get("gia_tri"), gt)
        da_dien.add(k)
    for k in list(A_LABELS) + list(B_LABELS):
        if k not in da_dien:
            nhat_ky.thieu.append(f"Phần ba {k}")

    for nhan, k in (("C.1 Mô tả", "C1_huy_dong_chon_nguoi_tham_gia"), ("C.2 Mô tả", "C2_thu_thap_so_lieu"),
                    ("C.3 Mô tả", "C3_xin_chap_thuan_tu_nguyen")):
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is not None:
            ghi_nhieu_dong(doan_trong_ke(ps, i), str(pl["phan_bon"].get(k, CAN_BO_SUNG)))

    for nhan, k in (("C.4", "C4_thu_nghiem_thuoc_can_thiep"), ("C.5", "C5_nguy_co_toi_thieu_de_quan_ly"),
                    ("C.6", "C6_nhieu_co_quan"), ("C.7", "C7_gia_han_tai_xin_phep")):
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is None:
            continue
        j = next((x for x in range(i, min(i + 6, len(ps))) if "FORMCHECKBOX" in ps[x].text), None)
        if j is None:
            nhat_ky.thieu.append(f"ô {nhan}")
            continue
        muc = pl["phan_nam"].get(k) or {"gia_tri": None}
        thay_hop(ps[j], muc.get("gia_tri"), muc.get("giai_thich", ""))

    ps = doc.paragraphs
    dong_tg = [p for p in ps if _chuan(p.text).startswith("từ _____")]
    if len(dong_tg) < 3:
        nhat_ky.thieu.append("ba dòng thời gian «từ ___ đến ___»")
    for p, k in zip(dong_tg, ("thu_nghiem", "thu_thap", "toan_bo")):
        tg = pl["thoi_gian"].get(k) or {}
        dat_text(p, f"từ  {tg.get('tu', CAN_BO_SUNG)}      đến      {tg.get('den', CAN_BO_SUNG)}")

    ps = doc.paragraphs
    i = nhat_ky.can(tim_chua(ps, "Họ tên", "nghiên cứu viên khác"), "Họ tên và thông tin về các nghiên cứu viên khác")
    if i is not None:
        dat_text(doan_trong_ke(ps, i), str(pl.get("nghien_cuu_vien_khac") or ""))
    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "Mô tả NCYSH"), "Mô tả NCYSH")
    if i is not None:
        ghi_nhieu_dong(doan_trong_ke(ps, i), str(_lay(d, "phu_luc_11", "muc", "1a", default=CAN_BO_SUNG)))

    # Phần sáu: chỉ ô KẾT LUẬN CỦA NCV CHÍNH (khi bác sĩ đã ghi) và ô gửi thông báo; ô của người khác để trống.
    ps = doc.paragraphs
    i6 = tim(ps, "PHẦN KHAI CỦA NGHIÊN CỨU VIÊN CHÍNH")
    i_hd = tim_chua(ps, "Ý KIẾN CỦA NGƯỜI HƯỚNG DẪN", tu=i6 or 0) if i6 is not None else None
    kl = _lay(pl, "phan_khai", "ket_luan_nghien_cuu_vien_chinh")
    if i6 is not None and kl in ("mien", "rut_gon"):
        for j in range(i6, i_hd or len(ps)):
            t = ps[j].text.lower()
            if "formcheckbox" in t and "không thuộc phạm vi" in t:
                _thay_o(ps[j], [dau(kl == "mien")])
            elif "formcheckbox" in t and "đủ điều kiện" in t:
                _thay_o(ps[j], [dau(kl == "rut_gon")])
    gui = _lay(pl, "phan_sau", "gui_thong_bao", default={}) or {}
    for cum, khoa in (("Khoa học Quân sự", "phong_khqs_dao_tao"), ("Đào tạo đại học", "phong_dao_tao_dai_hoc"),
                      ("Đào tạo sau đại học", "phong_dao_tao_sau_dai_hoc"), ("TCKT", "phong_tckt")):
        j = tim_chua(ps, "Xin gửi thông báo", cum)
        if j is not None and gui.get(khoa) is not None:
            _thay_o(ps[j], [dau(gui[khoa] is True), dau(gui[khoa] is False)])
    don_hop_con_lai(doc)
    doc.save(str(out))
    return out


_MUC_TIEU_DE_11 = [
    ("1a.", "1a"), ("1b.", "1b"), ("1c.", "1c"), ("1d.", "1d"), ("1e.", "1e"), ("1f.", "1f"),
    ("2a.", None), ("2b.", "2b"), ("2c.", "2c"), ("2d.", "2d"), ("2e.", "2e"), ("2f.", "2f"), ("2g.", "2g"),
    ("3a.", "3a"), ("3b.", "3b"), ("3c.", "3c"), ("3d.", "3d"),
    ("4(a)", "4a"), ("4(b)", "4b"), ("4(c)", "4c"), ("4(d)", "4d"), ("4(e)", "4e"), ("4(f)", "4f"),
    ("4(g)", "4g"), ("4(h)", "4h"), ("4(i)", "4i"), ("4(j)", "4j"), ("4(k)", "4k"), ("4(l)", "4l"),
    ("4(m)", "4m"), ("4(n)", "4n"), ("5. QUI TRÌNH", "5"),
    ("6(a)", "6a"), ("6(b)", "6b"), ("6(c)", "6c"), ("6(d)", "6d"), ("6(e)", "6e"),
    ("8(a)", "8a"), ("8(b)", "8b"), ("8(c)", "8c"), ("9. NHỮNG", "9"),
]
_TINH_CHAT_11 = (
    ("Nghiên cứu được tài trợ", "duoc_tai_tro"), ("học viên sau đại học", "hoc_vien_sau_dai_hoc"),
    ("sinh viên đại học", "sinh_vien_dai_hoc"), ("Xin phép tập thể", "xin_phep_tap_the"),
    ("Đơn xin tái cấp phép", "don_xin_tai_cap_phep"), ("Không thuộc nghiên cứu nào", "khong_thuoc_nhom_nao_tren"),
)
_QUY_CHE_11 = (
    ("Trẻ em", "tre_em_vi_thanh_nien"), ("tổn thương thần kinh", "ton_thuong_than_kinh_thieu_nang_tri_tue"),
    ("thường xuyên cần", "can_cham_soc_y_te_thuong_xuyen"), ("lệ thuộc", "quan_he_le_thuoc_khong_binh_dang"),
    ("tập thể", "tap_the_nhom_nguoi"), ("dân tộc thiểu số", "dan_toc_thieu_so"),
    ("Phóng xạ", "phong_xa_chat_ion_hoa"), ("sinh sản", "cong_nghe_sinh_san_co_tro_giup"),
    ("Thử nghiệm lâm sàng", "thu_nghiem_lam_sang"), ("Phác đồ", "phac_do_dieu_tri_thu_thuat_moi"),
    ("dịch tễ", "nghien_cuu_dich_te_hoc"), ("mẫu mô", "mau_mo_chat_dich_nguoi"), ("Gien", "gien_nguoi"),
)
_NGUY_CO_2A = (("Nhóm nghiên cứu", "nhom_nghien_cuu"), ("Người tham gia", "nguoi_tham_gia"),
               ("Cộng đồng của trường", "cong_dong_cua_truong"), ("Cộng đồng lớn hơn", "cong_dong_lon_hon"))
_TRANG_THAI_CQ = {"da_cap_phep": "Đã được cấp phép", "dang_cho": "Đã nộp đơn", "chua_xin": "Chưa xin phép",
                  "khac": "Ghi chú khác"}


def _dinh_dang_ncv(nv: Any) -> str:
    if isinstance(nv, dict):
        return (f"Họ tên: {nv.get('ho_ten', '')}\nChức danh: {nv.get('chuc_danh', '')}\n"
                f"Chức vụ, nơi công tác: {nv.get('chuc_vu_noi_cong_tac', '')}")
    return str(nv)


def dung_phu_luc_11(mau: Path, out: Path, d: dict, nhat_ky: _NhatKyMau) -> Path:
    """Mẫu 7 — Phụ lục 11, Phiếu thông tin xem xét theo quy trình đầy đủ (đủ mục 1a–11)."""
    doc = docx.Document(str(mau))
    pl = d["phu_luc_11"]
    tc = pl.get("tinh_chat") or {}
    for p in doc.paragraphs:
        if "FORMCHECKBOX" not in p.text:
            continue
        if "Số giấy phép cũ" in p.text:
            so = str(tc.get("so_giay_phep_cu") or "")
            thay_hop(p, bool(so.strip()), so, danh_dau_chua_quyet=False)
            continue
        for cum, khoa in _TINH_CHAT_11:
            if cum in p.text:
                thay_hop(p, tc.get(khoa))
                break

    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "Tên NCYSH (tiếng Việt"), "Tên NCYSH (tiếng Việt và ngôn ngữ gốc)")
    if i is not None:
        ten = str(pl.get("ten_ncysh", ""))
        if pl.get("ten_tieng_anh"):
            ten += f"\nTên tiếng Anh (tên công khai dự kiến): {pl['ten_tieng_anh']}"
        ghi_nhieu_dong(doan_trong_ke(ps, i), ten)
    ds_ncv = pl.get("nghien_cuu_vien") or []
    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "Nghiên cứu viên chính"), "Nghiên cứu viên chính")
    if i is not None:
        ghi_nhieu_dong(doan_trong_ke(ps, i), _dinh_dang_ncv(ds_ncv[0]) if ds_ncv else CAN_BAC_SI_DIEN)
    khac = _van_ban_list(pl.get("nghien_cuu_vien_khac")) or _van_ban_list(_lay(d, "phu_luc_10", "nghien_cuu_vien_khac"))
    khac += [_dinh_dang_ncv(nv) for nv in ds_ncv[1:]]
    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "Các nghiên cứu viên khác"), "Các nghiên cứu viên khác")
    if i is not None:
        ghi_nhieu_dong(doan_trong_ke(ps, i), "\n".join(khac))
    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "Đơn vị chủ trì nghiên cứu"), "Đơn vị chủ trì nghiên cứu")
    if i is not None:
        dat_text(doan_trong_ke(ps, i), str(pl.get("don_vi_chu_tri", "")))

    gd = pl.get("nguoi_giao_dich") or {}
    for nhan, khoa in (("Họ, tên, chức danh:", "ho_ten_chuc_danh"), ("Địa chỉ giao dịch:", "dia_chi_giao_dich"),
                       ("CQ", "dien_thoai_cq"), ("Fax", "fax"), ("NR", "dien_thoai_nr"),
                       ("Di động:", "di_dong"), ("Thư điện tử:", "thu_dien_tu")):
        if str(gd.get(khoa) or "").strip():
            ps = doc.paragraphs
            j = tim(ps, nhan, tim(ps, "Người giao dịch") or 0)
            if j is not None:
                _noi_gia_tri(ps[j], str(gd[khoa]))

    # Nhiều cơ quan + tình trạng cấp phép
    ps = doc.paragraphs
    i = tim(ps, "Tình trạng cấp phép về đạo đức")
    ds_cq = pl.get("nhieu_co_quan") or []
    mot_co_quan = _nghien_cuu_mot_co_quan(d)
    if i is not None:
        if ds_cq:
            dong = [f"{cq.get('ten', '') if isinstance(cq, dict) else cq}" for cq in ds_cq]
            ghi_nhieu_dong(doan_trong_ke(ps, i, 2), "\n".join(dong))
            nhom = [j for j, p in enumerate(doc.paragraphs)
                    if "FORMCHECKBOX" in p.text and "Đã được cấp phép" in p.text]
            for so, cq in enumerate(ds_cq[:len(nhom)]):
                tt = _TRANG_THAI_CQ.get(cq.get("trang_thai", "") if isinstance(cq, dict) else "")
                ps = doc.paragraphs
                for j in range(nhom[so], min(nhom[so] + 4, len(ps))):
                    if "FORMCHECKBOX" in ps[j].text:
                        thay_hop(ps[j], bool(tt and tt in ps[j].text), danh_dau_chua_quyet=False)
        elif mot_co_quan:
            dat_text(doan_trong_ke(ps, i, 2),
                     f"Không — nghiên cứu chỉ thực hiện tại {BENH_VIEN}, không có cơ quan tham gia khác.")
        else:
            dat_text(doan_trong_ke(ps, i, 2), f"{CHUA_QUYET}: nghiên cứu có cơ quan khác tham gia không")
    else:
        nhat_ky.thieu.append("Tình trạng cấp phép về đạo đức")

    qc = pl.get("quy_che_dac_biet") or {}
    ny = pl.get("nguy_co_xay_ra_voi") or {}
    ps = doc.paragraphs
    i_qc = nhat_ky.can(tim(ps, "Nghiên cứu cần áp dụng những qui chế"), "Nghiên cứu cần áp dụng những qui chế đặc biệt")
    i_2a = nhat_ky.can(tim(ps, "Những nguy cơ đó xảy ra với"), "Những nguy cơ đó xảy ra với")
    for j, p in enumerate(ps):
        if "FORMCHECKBOX" not in p.text:
            continue
        if i_qc is not None and i_qc < j < i_qc + 16:
            for cum, khoa in _QUY_CHE_11:
                if cum in p.text:
                    thay_hop(p, qc.get(khoa))
                    break
        elif i_2a is not None and i_2a < j < i_2a + 6:
            for cum, khoa in _NGUY_CO_2A:
                if cum in p.text:
                    thay_hop(p, ny.get(khoa))
                    break
    for nhan, khoa in (("Thông tin về nguồn tài trợ", "nguon_tai_tro"),
                       ("Thông tin về NCYSH sinh viên", "thong_tin_sinh_vien")):
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is not None:
            dat_text(doan_trong_ke(ps, i), str(pl.get(khoa) or ""))

    muc = pl.get("muc") or {}
    for tieu_de, k in _MUC_TIEU_DE_11:
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, tieu_de), tieu_de)
        if i is None:
            continue
        if k is None:  # 2a: văn xuôi đặt SAU khối ô đánh dấu
            j = tim(ps, "Cộng đồng lớn hơn", i)
            if j is None:
                j = next((x for x in range(i, min(i + 8, len(ps))) if "Cộng đồng lớn hơn" in ps[x].text), i)
            ghi_nhieu_dong(doan_trong_ke(ps, j), str(muc.get("2a", CAN_BO_SUNG)))
            continue
        ghi_nhieu_dong(doan_trong_ke(ps, i), str(muc.get(k, CAN_BO_SUNG)))

    # 6(f) — số năm lưu trữ + hai loại thông tin
    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "6(f) Bảo quản"), "6(f) Bảo quản và lưu trữ")
    if i is not None:
        so_nam = str(pl.get("luu_tru_so_nam") or CAN_BO_SUNG)
        for r in ps[i].runs:
            if "____" in r.text:
                r.text = r.text.replace("____", so_nam, 1)
                break
        ghi_nhieu_dong(doan_trong_ke(ps, i, 1), str(muc.get("6f", CAN_BO_SUNG)))
        chap_thuan = pl.get("chap_thuan_bo_mon_luu_tru") or {}
        for lan, hau in ((0, "i"), (1, "ii")):
            ps = doc.paragraphs
            ds = [j for j, p in enumerate(ps) if p.text.strip().startswith("Địa điểm lưu trữ")]
            if len(ds) <= lan:
                nhat_ky.thieu.append(f"Địa điểm lưu trữ 6(f){hau}")
                continue
            j = ds[lan]
            dia_diem = str(muc.get(f"6f_{hau}_dia_diem", CAN_BO_SUNG))
            for r in ps[j].runs:
                if "____" in r.text:
                    r.text = re.sub(r"_{4,}", " " + dia_diem.replace("\\", "\\\\") + " ", r.text, count=1)
                    break
            else:
                _run(ps[j], " " + dia_diem)
            thay_hop(ps[j], chap_thuan.get(hau))
            for nhan, k in (("Ai được phép tiếp cận", f"6f_{hau}_ai_tiep_can"),
                            ("Cách kiểm soát tiếp cận", f"6f_{hau}_kiem_soat")):
                ps = doc.paragraphs
                q = tim(ps, nhan, j)
                if q is not None:
                    dat_text(doan_trong_ke(ps, q, 1), str(muc.get(k, CAN_BO_SUNG)))
    for nhan, k in (("6(g) Bảo vệ", "6g"), ("6(g)i.", "6g_i"), ("6(g)ii.", "6g_ii"), ("6(g)iii.", "6g_iii")):
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is not None:
            ghi_nhieu_dong(doan_trong_ke(ps, i, 2), str(muc.get(k, CAN_BO_SUNG)))
    for nhan, k in (("7(a)", "7a"), ("7(b)", "7b"), ("7(c)", "7c")):
        ps = doc.paragraphs
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is None:
            continue
        if i + 1 < len(ps) and "_____" in ps[i + 1].text:
            dat_text(ps[i + 1], "\t\t" + str(muc.get(k, CAN_BO_SUNG)))
        else:
            dat_text(doan_trong_ke(ps, i, 2), "\t\t" + str(muc.get(k, CAN_BO_SUNG)))
    ps = doc.paragraphs
    i = nhat_ky.can(tim(ps, "Đính kèm câu trả lời"), "10 — Đính kèm câu trả lời")
    if i is not None:
        ghi_nhieu_dong(doan_trong_ke(ps, i), str(muc.get("10", CAN_BO_SUNG)))
    ps = doc.paragraphs
    i = tim(ps, "11. CAM KẾT")
    j = tim(ps, "Tên NCYSH:", i) if i is not None else None
    if nhat_ky.can(j, "11. CAM KẾT — Tên NCYSH:") is not None:
        _run(ps[j], " " + str(pl.get("ten_ncysh", "")))
    don_hop_con_lai(doc)
    doc.save(str(out))
    return out


def dung_icf(mau: Path, out: Path, icf: dict, nhat_ky: _NhatKyMau) -> Path:
    """Mẫu 8 — Bản thông tin dành cho đối tượng nghiên cứu + chấp thuận tham gia (Phụ lục 8)."""
    doc = docx.Document(str(mau))
    ps = doc.paragraphs
    for nhan, k in (("Tên nghiên cứu:", "ten_nghien_cuu"), ("Nhà tài trợ:", "nha_tai_tro"),
                    ("Nghiên cứu viên chính:", "nghien_cuu_vien_chinh"), ("Đơn vị chủ trì:", "don_vi_chu_tri")):
        i = nhat_ky.can(tim(ps, nhan), nhan)
        if i is not None:
            dat_text(ps[i], f"{nhan} {icf.get(k, CAN_BO_SUNG)}", giu_dinh_dang=True)
    i = tim(ps, "Đơn vị chủ trì:")
    if i is not None and icf.get("phien_ban"):
        chen_sau(ps[i], str(icf["phien_ban"]), italic=True)
    ps = doc.paragraphs
    i = tim(ps, "(Bản Thông tin dành cho")
    if i is not None:
        xoa(ps[i])  # câu hướng dẫn của mẫu, không thuộc bản phát cho người tham gia

    muc = icf.get("muc") or {}
    ps = doc.paragraphs
    i_ct = nhat_ky.can(tim(ps, "CHẤP THUẬN THAM GIA NGHIÊN CỨU"), "CHẤP THUẬN THAM GIA NGHIÊN CỨU")
    if i_ct is None:
        doc.save(str(out))
        return out
    tieu = [(j, m.group(1)) for j, p in enumerate(ps[:i_ct]) if (m := re.match(r"^\s*([1-6])\.\s", p.text))]
    khoang = []
    for n, (j, k) in enumerate(tieu):
        het = tieu[n + 1][0] if n + 1 < len(tieu) else i_ct
        khoang.append((j, het, k))
    for j, het, k in reversed(khoang):  # từ cuối lên để chỉ số không lệch
        ps = doc.paragraphs
        for p in [ps[x] for x in range(j + 1, het)]:
            xoa(p)
        ps = doc.paragraphs
        q = ps[j]
        for t in str(muc.get(k, CAN_BO_SUNG)).split("\n"):
            q = chen_sau(q, t)
    da_co = {k for _j, k in tieu}
    for k in MUC_PHU_LUC_8:
        if k not in da_co:
            nhat_ky.thieu.append(f"mục {k} của Phụ lục 8")

    bo_sung = icf.get("ten_muc_bo_sung") or {}
    if bo_sung and tieu:
        ps = doc.paragraphs
        i_ct = tim(ps, "CHẤP THUẬN THAM GIA NGHIÊN CỨU")
        i6 = max(j for j, p in enumerate(ps[:i_ct]) if re.match(r"^\s*[1-6]\.\s", p.text))
        mau_tieu_de = ps[i6]._p
        truoc = ps[i_ct]._p.getprevious()
        for k in sorted(bo_sung, key=lambda x: (len(str(x)), str(x))):
            el = copy.deepcopy(mau_tieu_de)
            truoc.addnext(el)
            ptd = Paragraph(el, ps[i6]._parent)
            dat_text(ptd, f"{k}.\t{bo_sung[k]}", giu_dinh_dang=True)
            q = ptd
            for t in str(muc.get(str(k), CAN_BO_SUNG)).split("\n"):
                q = chen_sau(q, t)
            truoc = q._p
    doc.save(str(out))
    return out


def _dong_co_do(mi: dict) -> list[tuple[str, str]]:
    """Dòng «dữ liệu xác định được» / «tiếp xúc người tham gia» của đơn miễn — theo cờ, KHÔNG phải cờ chặn."""
    cd = mi.get("co_do") or {}
    ra: list[tuple[str, str]] = []
    xd = cd.get("co_du_lieu_ca_nhan_nhan_dang_duoc")
    if str(mi.get("co_do_giai_thich") or "").strip():
        ra.append(("Dữ liệu xác định được", str(mi["co_do_giai_thich"])))
    elif xd is True:
        ra.append(("Dữ liệu xác định được", CCDD.LUU_Y_DU_LIEU_XAC_DINH_DUOC))
    elif xd is False:
        ra.append(("Dữ liệu xác định được", "Không — dữ liệu ẩn danh hoàn toàn, không còn bảng nối mã."))
    else:
        ra.append(("Dữ liệu xác định được", f"{CHUA_QUYET}: dữ liệu có xác định được người bệnh không (còn bảng"
                                             " nối mã, hồ sơ có định danh?)"))
    tx = cd.get("co_tiep_xuc_nguoi_tham_gia")
    if tx is True:
        ra.append(("Tiếp xúc người tham gia", CCDD.LUU_Y_TIEP_XUC_NGUOI_THAM_GIA))
    elif tx is None:
        ra.append(("Tiếp xúc người tham gia", f"{CHUA_QUYET}: có tiếp xúc trực tiếp người tham gia không"))
    return ra


_NHAN_PHUONG_AN = {
    "xin_dong_y_khi_tai_kham": "Xin đồng ý khi người bệnh tái khám",
    "thong_bao_va_cho_tu_choi": "Thông báo và cho từ chối (informed opt-out)",
}


def dung_mien_icf(out: Path, d: dict) -> Path:
    """Đơn đề nghị miễn thủ tục đồng thuận (bệnh viện không có mẫu riêng) — lập luận theo ĐỦ BA điều kiện của CIOMS
    2016 Hướng dẫn 10; dữ liệu xác định được KHÔNG phải cờ buộc lấy chấp thuận."""
    mi = d["mien_icf"]
    doc = docx.Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(13)

    def dong(t: str, **kw):
        p = doc.add_paragraph()
        _run(p, t, size=13, **kw)
        return p

    for t in ("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "Độc lập – Tự do – Hạnh phúc",
              "ĐƠN ĐỀ NGHỊ MIỄN THỦ TỤC ĐỒNG THUẬN THAM GIA NGHIÊN CỨU"):
        dong(t, bold=True).alignment = 1
    dong(f"Kính gửi: {mi.get('kinh_gui') or KINH_GUI_HOI_DONG}")
    dong(f"Chủ nhiệm đề tài: {mi.get('chu_nhiem', CAN_BAC_SI_DIEN)}")
    dong(f"Tên đề tài: {mi.get('ten_de_tai', '')}")
    dong("1. Tóm tắt đề tài", bold=True)
    dong(str(mi.get("tom_tat", CAN_BO_SUNG)))
    dong("2. Căn cứ", bold=True)
    dong(str(mi.get("can_cu") or CCDD.CAN_CU_MIEN_DONG_THUAN))
    dong("3. Lập luận theo ba điều kiện miễn đồng thuận (CIOMS 2016, Hướng dẫn 10)", bold=True)
    bk = mi.get("ba_dieu_kien_cioms") or {}
    for khoa, nhan in CCDD.BA_DIEU_KIEN_CIOMS:
        dong(f"{nhan}:", italic=True)
        dong(str(bk.get(khoa, CAN_BO_SUNG)))
    dong("4. Các phương án sửa đổi thủ tục đồng thuận đã xem xét", bold=True)
    pa = mi.get("phuong_an_sua_doi_da_xem_xet") or {}
    chu = "abcdefgh"
    so = 0
    for khoa, gia_tri in pa.items():
        if not str(gia_tri or "").strip():
            continue
        nhan = _NHAN_PHUONG_AN.get(khoa)
        dong(f"{chu[so]}) {nhan}: {gia_tri}" if nhan else f"{chu[so]}) {gia_tri}")
        so += 1
    if so == 0:
        dong(CAN_BO_SUNG)
    dong("5. Bảo đảm bảo mật dữ liệu", bold=True)
    bm = mi.get("dam_bao_bao_mat") or {}
    for nhan, k in (("Loại dữ liệu", "loai_du_lieu"), ("Mã hoá và lưu tệp có mã người bệnh", "ma_hoa"),
                    ("Quyền truy cập", "quyen_truy_cap"), ("Kế hoạch huỷ và xử lý sự cố", "ke_hoach_huy")):
        dong(f"– {nhan}: {bm.get(k, CAN_BO_SUNG)}")
    for nhan, noi_dung in _dong_co_do(mi):
        dong(f"– {nhan}: {noi_dung}")
    dong("6. Xung đột lợi ích", bold=True)
    dong(str(mi.get("xung_dot_loi_ich", CAN_BO_SUNG)))
    dong("7. Cam kết của nhóm nghiên cứu", bold=True)
    cam_ket = _van_ban_list(mi.get("cam_ket"))
    for c in cam_ket or [CAN_BO_SUNG]:
        dong("– " + c)
    dong("Kính đề nghị Hội đồng xem xét, chấp thuận miễn thủ tục đồng thuận tham gia nghiên cứu cho đề tài trên.")
    ngay_ky = mi.get("ngay") or HSC.goi_ky("ngày ký Đơn đề nghị miễn thủ tục đồng thuận")
    dong(f"TP. Hồ Chí Minh, ngày: {ngay_ky}").alignment = 2
    dong("Chủ nhiệm đề tài", bold=True).alignment = 2
    dong("(Ký và ghi rõ họ tên)", italic=True).alignment = 2
    dong(HSC.goi_ky("chữ ký và họ tên chủ nhiệm đề tài — Đơn đề nghị miễn thủ tục đồng thuận")).alignment = 2
    doc.save(str(out))
    return out


def du_lieu_phieu_thu_thap(exports_root: Path, d: dict) -> tuple[str | None, list[str], list[str]]:
    """(markdown phiếu thu thập, phụ lục đã lấy, phụ lục không thấy) — CHỈ các phụ lục đã chọn của đề cương nộp."""
    study = d["meta"]["study"]
    de_cuong_md = exports_root / study / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    if not de_cuong_md.is_file():
        return None, [], []
    ds = tach_phu_luc(de_cuong_md.read_text(encoding="utf-8"))
    chon = _lay(d, "phieu_thu_thap", "phu_luc")
    if not isinstance(chon, list) or not chon:
        chon = chon_phu_luc_mac_dinh(ds)
    khoi: list[str] = []
    da_lay: list[str] = []
    khong_thay: list[str] = []
    for tieu_de in chon:
        khoa = _chuan(tieu_de).upper()
        hit = next(((t, k) for t, k in ds if _chuan(t).upper() == khoa), None) or next(
            ((t, k) for t, k in ds if _chuan(t).upper().startswith(khoa)), None)
        if hit is None:
            khong_thay.append(tieu_de)
            continue
        da_lay.append(hit[0])
        khoi.append(re.sub(r"^#{1,6}\s+", "# ", hit[1], count=1))
    if not khoi:
        return None, da_lay, khong_thay
    ten_ngan = [re.sub(r"(?i)^(phụ lục\s+[A-Z0-9]+)\b.*$", r"\1", _chuan(t)).replace("PHỤ LỤC", "Phụ lục")
                for t in da_lay]
    meta_path = exports_root / study / "study_meta.json"
    phien_ban = ""
    if meta_path.is_file():
        try:
            pv = _lay(json.loads(meta_path.read_text(encoding="utf-8")), "gate_params", "G1", "protocol_version")
            phien_ban = f", phiên bản {pv}" if pv and not _cho_trong(pv) else ""
        except (OSError, ValueError):
            phien_ban = ""
    dau_trang = (
        "# BỆNH ÁN NGHIÊN CỨU, PHIẾU THU THẬP SỐ LIỆU VÀ PHỤ LỤC CỦA ĐỀ CƯƠNG\n\n"
        f"**Đề tài:** {d['meta'].get('title', '')}\n\n"
        f"*(Trích nguyên văn {', '.join(ten_ngan)} của đề cương nộp Hội đồng{phien_ban} — Quyển 2, mục 7)*\n\n"
    )
    return dau_trang + "\n\n".join(khoi) + "\n", da_lay, khong_thay


def dung_phieu_thu_thap(exports_root: Path, out: Path, d: dict) -> tuple[Path | None, list[str]]:
    """Phiếu thu thập số liệu + phụ lục (Quyển 2, mục 7) — bảng Word thật qua `md2docx_vn` (chuẩn chung của repo)."""
    md, _da_lay, khong_thay = du_lieu_phieu_thu_thap(exports_root, d)
    if md is None:
        return None, khong_thay
    import md2docx_vn  # noqa: PLC0415 - chỉ cần khi có phụ lục để dựng

    md2docx_vn.markdown_to_docx(md, out)
    return out, khong_thay


# ---------------------------------------------------------------------------
# Ghi an toàn — sao lưu tệp người đã sửa tay
# ---------------------------------------------------------------------------


def _bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class BoGhiAnToan:
    """Ghi đè tệp đầu ra mà KHÔNG làm mất bản người đã sửa tay.

    Lưu dấu băm của từng tệp do công cụ ghi (`_sao_luu/_bam_lan_dung.json`). Lần sau, tệp hiện có KHÁC dấu băm đã
    lưu (người đã sửa, hoặc tệp chưa từng do công cụ ghi) ⇒ chép sang `_sao_luu/<tên>.bak-<giờ><đuôi>` TRƯỚC khi ghi.
    """

    def __init__(self, thu_muc: Path) -> None:
        self.thu_muc = thu_muc
        self.sao_luu_dir = thu_muc / THU_MUC_SAO_LUU
        self.tep_bam = self.sao_luu_dir / TEP_BAM
        try:
            self.bam = json.loads(self.tep_bam.read_text(encoding="utf-8")) if self.tep_bam.is_file() else {}
        except (OSError, ValueError):
            self.bam = {}
        self.gio = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.da_sao_luu: list[Path] = []

    def ghi(self, out: Path, ham_ghi: Callable[[Path], Any]) -> Any:
        if out.is_file() and self.bam.get(out.name) != _bam(out):
            self.sao_luu_dir.mkdir(parents=True, exist_ok=True)
            dich = self.sao_luu_dir / f"{out.stem}.bak-{self.gio}{out.suffix}"
            shutil.copy2(out, dich)
            self.da_sao_luu.append(dich)
        ket_qua = ham_ghi(out)
        if out.is_file():
            self.bam[out.name] = _bam(out)
        return ket_qua

    def luu(self) -> None:
        self.sao_luu_dir.mkdir(parents=True, exist_ok=True)
        self.tep_bam.write_text(json.dumps(self.bam, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Danh mục — theo tệp HIỆN CÓ trên đĩa
# ---------------------------------------------------------------------------


def _tep_hien_co(ra_dir: Path, mau_glob: str) -> list[Path]:
    return sorted(p for p in ra_dir.glob(mau_glob) if p.is_file() and not p.name.startswith("~$"))


def _trang_thai(ra_dir: Path, mau_glob: str, moc: float | None) -> str:
    ds = _tep_hien_co(ra_dir, mau_glob)
    if not ds:
        return "**CHƯA có tệp**"
    ten = ", ".join(f"`{p.name}`" for p in ds)
    cu = [p for p in ds if moc is not None and p.stat().st_mtime < moc]
    if cu:
        return f"có {ten} — **CŨ HƠN JSON**, chạy lại `dung`"
    return f"đã soạn: {ten}"


#: Ô đánh dấu của NGHIÊN CỨU VIÊN — để trống (None) là ô (a) chưa quyết. Ô ý kiến người hướng dẫn/trưởng khoa/Chủ tịch
#: Hội đồng và ô gửi thông báo (phan_khai, phan_sau) không thuộc nghiên cứu viên nên không tính.
_O_DANH_DAU_NCV = ("phu_luc_10.phan_mot", "phu_luc_10.phan_ba", "phu_luc_10.phan_nam", "phu_luc_11.tinh_chat",
                   "phu_luc_11.quy_che_dac_biet", "phu_luc_11.nguy_co_xay_ra_voi",
                   "phu_luc_11.chap_thuan_bo_mon_luu_tru", "mien_icf.co_do")


def _o_chua_quyet(o: Any, duong: str = "") -> list[tuple[str, str]]:
    if isinstance(o, dict):
        ra: list[tuple[str, str]] = []
        for k, v in o.items():
            ra += _o_chua_quyet(v, f"{duong}.{k}" if duong else str(k))
        return ra
    if o is None and any(duong == g or duong.startswith(g + ".") for g in _O_DANH_DAU_NCV):
        return [(duong, "ô đánh dấu chưa quyết")]
    return []


def ba_loai_hdd(d: dict, so: dict | None = None) -> dict[str, list[tuple[str, str]]]:
    """Ba loại ô chưa điền của JSON hồ sơ (a: suy được · b: gói ký · c: dữ kiện cần nhập); sổ lý lịch quyết định
    ô cá nhân đã có hay chưa; ô đánh dấu của nghiên cứu viên còn trống tính là (a)."""
    so = HSC.doc_so() if so is None else so
    ll = d.get("ly_lich_khoa_hoc") or [{}]
    khoa = HSC.slug(ll[0].get("ho_ten", "")) if isinstance(ll[0], dict) else ""
    ra = HSC.dem_ba_loai(d, HSC.ham_so_co(so, khoa))
    ra["a"] += _o_chua_quyet({k: d.get(k) for k in ("phu_luc_10", "phu_luc_11", "mien_icf")})
    return ra


def sinh_danh_muc(ra_dir: Path, d: dict, quy_trinh: str, mau_dir: Path | None = None,
                  dau_theo_tep: dict[str, dict[str, list[str]]] | None = None) -> Path:
    """Danh mục hồ sơ: 8 mục Quyển 2 (trạng thái theo tệp HIỆN CÓ trên đĩa), GÓI KÝ (tài liệu ký đúng thứ tự),
    DỮ KIỆN CẦN NHẬP (gom một chỗ) và cách nộp. Ô thuộc gói ký/dữ kiện cần nhập in dòng chấm trong Word — danh mục
    là nơi duy nhất liệt kê chúng (22/11/2026)."""
    study = d["meta"]["study"]
    json_path = ra_dir / "HO_SO_HDD_BVQY175.json"
    moc = json_path.stat().st_mtime if json_path.is_file() else None
    mien = d.get("icf") is None and d.get("mien_icf") is not None
    email, email_khac = doc_email_thu_ky(mau_dir)
    dau_theo_tep = dau_theo_tep or {}
    don_vi = _lay(d, "bia", "don_vi_chu_tri", default="") or "đơn vị chủ trì"
    khong_hv = "không áp dụng" in str(_lay(d, "phu_luc_11", "thong_tin_sinh_vien", default="")).lower()

    def tt(mau_glob: str) -> str:
        return _trang_thai(ra_dir, mau_glob, moc)

    def dau_cua(mau_glob: str, loai: str) -> list[str]:
        ra: list[str] = []
        for p in _tep_hien_co(ra_dir, mau_glob):
            for x in (dau_theo_tep.get(p.name) or {}).get(loai, []):
                if x not in ra:
                    ra.append(x)
        return ra

    dong: list[str] = [
        f"# Danh mục hồ sơ Hội đồng Đạo đức BVQY175 — {study}", "",
        f"Đề tài: {d['meta'].get('title', '')}",
        f"Quy trình: {quy_trinh}"
        + (f" (đề nghị trong đề cương: {d['meta']['quy_trinh_de_xuat']})" if d["meta"].get("quy_trinh_de_xuat")
           else ""),
        "",
        "## Quyển 1 — Thuyết minh đề cương (bìa Mẫu 2)",
        f"- Bìa: {tt(f'MAU2_*_{study}.docx')}",
        f"- Ruột: bản Word đề cương nộp hiện có `DE_CUONG_NOP_HOI_DONG_{study}.docx` (thư mục đề tài).",
        "",
        "## Quyển 2 — Hồ sơ đăng ký (bìa Mẫu 3), đúng thứ tự 8 mục",
        f"- Bìa: {tt(f'MAU3_*_{study}.docx')}",
        f"1. Đơn xin đánh giá đạo đức (Mẫu 4) — {tt(f'MAU4_*_{study}.docx')}",
        f"2. Thư giới thiệu của đơn vị chủ trì — văn bản do Thủ trưởng {don_vi} ký (gói ký, mục 2)",
        "3. Bản sao quyết định phân công người hướng dẫn — "
        + ("không áp dụng (không phải đề tài của học viên)" if khong_hv else "chỉ khi có người hướng dẫn (gói ký)"),
        f"4. Lý lịch khoa học (Mẫu 5) — {tt(f'MAU5_*_{study}_*.docx')} (một tệp mỗi người)",
    ]
    if quy_trinh in ("rut_gon", "ca_hai") or _tep_hien_co(ra_dir, f"MAU6_*_{study}.docx"):
        dong.append(f"5a. Bảng kiểm quy trình rút gọn (Mẫu 6, Phụ lục 10) — {tt(f'MAU6_*_{study}.docx')}")
    if quy_trinh in ("day_du", "ca_hai") or _tep_hien_co(ra_dir, f"MAU7_*_{study}.docx"):
        dong.append(f"5b. Phiếu quy trình đầy đủ (Mẫu 7, Phụ lục 11) — {tt(f'MAU7_*_{study}.docx')}")
    if mien:
        dong.append(f"6. Đơn đề nghị miễn thủ tục đồng thuận (thay Mẫu 8) — {tt(f'MIEN_ICF_{study}.docx')}")
    else:
        dong.append(f"6. Bản thông tin + chấp thuận tham gia (Mẫu 8, Phụ lục 8) — {tt(f'MAU8_*_{study}.docx')}")
    dong.append(f"7. Bệnh án/phiếu thu thập số liệu và phụ lục của đề cương — {tt(f'PHIEU_THU_THAP_*_{study}.docx')}")
    mot_co_quan = _nghien_cuu_mot_co_quan(d)
    if mot_co_quan:
        dong.append(f"8. Giấy chấp thuận đạo đức nơi khác — không áp dụng (chỉ thực hiện tại {BENH_VIEN})")
    elif mot_co_quan is False:
        dong.append("8. Giấy chấp thuận đạo đức nơi khác — giấy chấp thuận của Hội đồng các cơ quan tham gia (gói ký)")
    else:
        dong.append("8. Giấy chấp thuận đạo đức nơi khác — [CẦN BỔ SUNG: danh sách cơ quan tham gia trong khối"
                    " dữ kiện của biểu mẫu]")
    if quy_trinh in ("rut_gon", "ca_hai"):
        dong += ["", f"Lưu ý quy trình rút gọn: {CCDD.CAN_CU_QUY_TRINH_RUT_GON}."]

    # GÓI KÝ — đúng thứ tự tài liệu nộp
    chu_nhiem = _lay(d, "don_mau4", "ho_ten_chu_nhiem", default="")
    ky: list[str] = [f"Đơn xin đánh giá đạo đức (Mẫu 4) — chữ ký chủ nhiệm đề tài ({chu_nhiem})."]
    ky.append(f"Thư giới thiệu của đơn vị chủ trì — Thủ trưởng {don_vi} ký, đóng dấu.")
    tu_khai = dau_cua(f"MAU5_*_{study}_*.docx", "tu_khai")
    ky.append("Lý lịch khoa học (Mẫu 5) — chữ ký từng người"
              + (f"; tự khai khi ký: {', '.join(tu_khai)}" if tu_khai else "") + ".")
    if quy_trinh in ("rut_gon", "ca_hai"):
        ky.append("Bảng kiểm quy trình rút gọn (Mẫu 6) — nghiên cứu viên chính ký Phần sáu; ô ý kiến người hướng dẫn,"
                  " trưởng khoa và Chủ tịch Hội đồng do chính người đó ghi.")
    if quy_trinh in ("day_du", "ca_hai"):
        ky.append("Phiếu quy trình đầy đủ (Mẫu 7) — mọi nghiên cứu viên ký cam kết ở mục 11.")
    if mien:
        ky.append("Đơn đề nghị miễn thủ tục đồng thuận — chủ nhiệm đề tài ký, ghi ngày.")
    else:
        ky.append("Bản thông tin + phiếu chấp thuận (Mẫu 8) — nộp bản trắng; người tham gia, người làm chứng và người"
                  " giải thích ký khi triển khai.")
    da_co = " ".join(ky).lower()
    for loai_tep in ("MAU*", "MIEN_ICF*", "PHIEU*"):
        for x in dau_cua(f"{loai_tep}_{study}*.docx", "goi_ky"):
            if x.lower() not in da_co:
                ky.append(x[0].upper() + x[1:] + ("." if not x.endswith(".") else ""))
                da_co += " " + x.lower()
        for x in dau_cua(f"{loai_tep}_{study}*.docx", "tu_khai"):
            if x.lower() not in da_co:
                ky.append(f"Tự khai khi ký: {x}.")
                da_co += " " + x.lower()
    for x in d.get("goi_ky") or []:
        for _loai, mo_ta in HSC.mo_ta_dau(x) or [("b", str(x))]:
            if mo_ta.lower() not in da_co:
                ky.append(mo_ta[0].upper() + mo_ta[1:] + ("." if not mo_ta.endswith(".") else ""))
                da_co += " " + mo_ta.lower()
    dong += ["", "## Gói ký — tài liệu ký, đúng thứ tự nộp"] + [f"{i}. {x}" for i, x in enumerate(ky, 1)]

    # DỮ KIỆN CẦN NHẬP — gom một chỗ
    nhap: dict[str, list[str]] = {}
    for p in sorted(ra_dir.glob(f"*_{study}*.docx")):
        for x in (dau_theo_tep.get(p.name) or {}).get("can_nhap", []):
            tep = nhap.setdefault(x[0].upper() + x[1:], [])
            if p.name not in tep:
                tep.append(p.name)
    dong += ["", "## Dữ kiện cần nhập (chỉ có khi triển khai; ô in dòng chấm trong văn bản)"]
    dong += [f"- {x} (tệp {', '.join(f'`{t}`' for t in tep)})" for x, tep in nhap.items()] or ["- Không có."]

    noi_gui = f"`{email}`" if email else EMAIL_THU_KY_KHONG_DOC_DUOC
    dong += ["", "## Nộp hồ sơ",
             f"- Bản mềm (PDF/scan: 1 tệp thuyết minh + 1 tệp hồ sơ đăng ký) gửi tới {noi_gui} trước khi nộp bản cứng."]
    if email_khac:
        dong.append(f"- Mẫu Phụ lục 10 ghi thêm địa chỉ khác ({', '.join(f'`{e}`' for e in email_khac)}) — địa chỉ"
                    " nhận bản mềm theo hướng dẫn gốc của Hội đồng ở trên.")
    dong += [
        "- Bản cứng: 03 bộ (quy trình rút gọn) hoặc 07 bộ (quy trình đầy đủ), nộp tại Phòng Khoa học Quân sự.",
        "- Lệ phí 2.000.000 đ/hồ sơ theo Phụ lục 2 của hướng dẫn gốc (số tài khoản không lưu trong repo).",
        "- Mốc xét duyệt sau khi nộp: 5/2/2/10/2 ngày làm việc.",
    ]
    ba = ba_loai_hdd(d)
    dong += ["", f"Ô chưa điền trong JSON: (a) suy được từ nguồn {len(ba['a'])} · (b) gói ký {len(ba['b'])} · (c) dữ"
                 f" kiện cần nhập {len(ba['c'])} — chạy `kiem --study {study}` để xem chi tiết."]
    ra = ra_dir / _ten_ra("danh_muc", study)
    ra.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    return ra


# ---------------------------------------------------------------------------
# Lệnh dung
# ---------------------------------------------------------------------------


def _ke_hoach(d: dict, quy_trinh: str) -> list[tuple[str, str, str, Any]]:
    """[(loại, khoá mẫu, tên tệp ra, dữ liệu riêng)] các tệp Word phải dựng."""
    s = d["meta"]["study"]
    kh: list[tuple[str, str, str, Any]] = [
        ("bia", "bia_thuyet_minh", _ten_ra("bia_thuyet_minh", s), None),
        ("bia", "bia_ho_so", _ten_ra("bia_ho_so", s), None),
        ("don_mau4", "don_mau4", _ten_ra("don_mau4", s), None),
    ]
    for i, nguoi in enumerate(d.get("ly_lich_khoa_hoc") or [], start=1):
        kh.append(("ly_lich", "ly_lich", _ten_ra("ly_lich", s, f"{i:02d}"), nguoi))
    if quy_trinh in ("rut_gon", "ca_hai"):
        kh.append(("phu_luc_10", "phu_luc_10", _ten_ra("phu_luc_10", s), None))
    if quy_trinh in ("day_du", "ca_hai"):
        kh.append(("phu_luc_11", "phu_luc_11", _ten_ra("phu_luc_11", s), None))
    if d.get("icf") is not None:
        khac = [b for b in (d.get("icf_khac") or []) if isinstance(b, dict)]
        kh.append(("icf", "icf", _ten_ra("icf", s, "MAU_CHINH_" if khac else ""), d["icf"]))
        for b in khac:
            hau = re.sub(r"[^A-Z0-9]+", "_", _nfc(str(b.get("khoa") or "KHAC")).upper()).strip("_") or "KHAC"
            kh.append(("icf", "icf", _ten_ra("icf", s, f"{hau}_"), b))
    elif d.get("mien_icf") is not None:
        kh.append(("mien_icf", "", _ten_ra("mien_icf", s), None))
    kh.append(("phieu", "", _ten_ra("phieu", s), None))
    return kh


def lenh_dung(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    quy_trinh = args.quy_trinh
    thu_muc_hdd = _doc_hdd(exports_root, args.study)
    duong_dan_json = thu_muc_hdd / "HO_SO_HDD_BVQY175.json"
    if not duong_dan_json.is_file():
        print(f"LỖI: chưa có {duong_dan_json} — chạy `trich --study {args.study} --ghi` trước.")
        return 2
    d, nang_cap = doc_json_da_nang_cap(exports_root, args.study, duong_dan_json)
    if nang_cap:
        print("JSON được nâng cấp TRONG BỘ NHỚ (chạy `trich --ghi` để lưu): " + "; ".join(nang_cap))

    mau_dir = tim_thu_muc_mau()
    if mau_dir is None:
        print("LỖI: không tìm thấy bộ mẫu bệnh viện — chạy `mau` để kiểm.")
        return 2
    if docx is None:
        print("LỖI: thiếu python-docx. pip install python-docx")
        return 2

    ke_hoach = _ke_hoach(d, quy_trinh)
    if not args.ghi:
        print("(chạy khô — thêm --ghi để sinh tệp Word thật)")
        print(f"Sẽ dựng hồ sơ cho {args.study}, quy trình={quy_trinh}, vào {thu_muc_hdd}:")
        for _loai, khoa_mau, ten, _x in ke_hoach:
            thieu = khoa_mau and not (mau_dir / TEN_TEP_MAU[khoa_mau]).is_file()
            print(f"  - {ten}" + ("  (THIẾU MẪU)" if thieu else ""))
        print(f"Số ô còn [CẦN...]: {_dem_can(d)}")
        return 0

    thu_muc_hdd.mkdir(parents=True, exist_ok=True)
    bo_ghi = BoGhiAnToan(thu_muc_hdd)
    da_sinh: list[str] = []
    van_de: list[str] = []
    so = HSC.doc_so()
    dau_theo_tep: dict[str, dict[str, list[str]]] = {}

    def _xong(ham: Callable[[Path], Any]) -> Callable[[Path], Any]:
        """Dựng xong ⇒ giải dấu trong Word (sổ lý lịch → giá trị; gói ký/dữ kiện cần nhập → dòng chấm)."""
        def _chay(o: Path) -> Any:
            kq = ham(o)
            if o.is_file() and o.suffix == ".docx":
                dau_theo_tep[o.name] = HSC.hoan_thien_docx(o, so)
            return kq
        return _chay

    ten_ke_hoach = {ten for _l, _k, ten, _r in ke_hoach}
    mau_ra = re.compile(rf"^(MAU[2-8]|MIEN_ICF|PHIEU_THU_THAP)_.*{re.escape(args.study)}.*\.docx$")
    for cu in sorted(thu_muc_hdd.glob("*.docx")):
        if mau_ra.match(cu.name) and cu.name not in ten_ke_hoach:
            (thu_muc_hdd / THU_MUC_SAO_LUU).mkdir(parents=True, exist_ok=True)
            dich = thu_muc_hdd / THU_MUC_SAO_LUU / f"{cu.stem}.bo-{bo_ghi.gio}{cu.suffix}"
            shutil.move(str(cu), str(dich))
            print(f"  [không còn trong hồ sơ — dời vào sao lưu] {dich}")

    for loai, khoa_mau, ten, rieng in ke_hoach:
        out = thu_muc_hdd / ten
        mau = mau_dir / TEN_TEP_MAU[khoa_mau] if khoa_mau else None
        if mau is not None and not mau.is_file():
            van_de.append(f"THIẾU MẪU «{TEN_TEP_MAU[khoa_mau]}» — chưa dựng {ten}")
            continue
        nhat_ky = _NhatKyMau(mau.name if mau else ten)
        try:
            if loai == "bia":
                bo_ghi.ghi(out, _xong(lambda o, m=mau: dung_bia(m, o, d, nhat_ky)))
            elif loai == "don_mau4":
                bo_ghi.ghi(out, _xong(lambda o, m=mau: dung_don_mau4(m, o, d, quy_trinh, nhat_ky)))
            elif loai == "ly_lich":
                bo_ghi.ghi(out, _xong(lambda o, m=mau, r=rieng: dung_ly_lich(m, o, r, nhat_ky)))
            elif loai == "phu_luc_10":
                bo_ghi.ghi(out, _xong(lambda o, m=mau: dung_phu_luc_10(m, o, d, nhat_ky)))
            elif loai == "phu_luc_11":
                bo_ghi.ghi(out, _xong(lambda o, m=mau: dung_phu_luc_11(m, o, d, nhat_ky)))
            elif loai == "icf":
                bo_ghi.ghi(out, _xong(lambda o, m=mau, r=rieng: dung_icf(m, o, r, nhat_ky)))
            elif loai == "mien_icf":
                bo_ghi.ghi(out, _xong(lambda o: dung_mien_icf(o, d)))
            elif loai == "phieu":
                ket = bo_ghi.ghi(out, _xong(lambda o: dung_phieu_thu_thap(exports_root, o, d)))
                _p, khong_thay = ket if ket else (None, [])
                if khong_thay:
                    van_de.append(f"phiếu thu thập: không thấy phụ lục {khong_thay} trong đề cương nộp")
                if not out.is_file():
                    van_de.append("phiếu thu thập: CHƯA trích được (thiếu đề cương nộp hoặc phụ lục)")
                    continue
        except MauKhongKhop as exc:
            van_de.append(f"{ten}: mẫu không khớp — {exc}")
            continue
        if nhat_ky.thieu:
            van_de.append(f"{ten}: mẫu «{nhat_ky.ten_mau}» không có nhãn {nhat_ky.thieu}")
        if out.is_file():
            da_sinh.append(ten)
    bo_ghi.luu()
    danh_muc = bo_ghi.ghi(thu_muc_hdd / _ten_ra("danh_muc", args.study),
                          lambda o: sinh_danh_muc(thu_muc_hdd, d, quy_trinh, mau_dir, dau_theo_tep))
    bo_ghi.luu()
    print(f"Đã sinh {len(da_sinh)} tệp Word + danh mục: {danh_muc}")
    for t in da_sinh:
        print(f"  - {t}")
    for p in bo_ghi.da_sao_luu:
        print(f"  [sao lưu bản đã sửa tay] {p}")
    if van_de:
        print("\nCÒN VIỆC:")
        for v in van_de:
            print(f"  ✗ {v}")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Kiểm
# ---------------------------------------------------------------------------

# Dấu vết máy KHÔNG được có trong văn bản nộp Hội đồng. Mã câu hỏi kiểu «G1», «G1–G3» của bộ câu hỏi là nội dung
# hợp lệ — chỉ chặn ký hiệu cổng trong NGỮ CẢNH máy (cổng G…, G2_A3, G10-AUTO, G0–G10, PASS_G…, theo G0 §…).
DAU_VET_MAY = (
    (re.compile(r"(?:\b[A-Za-z]:\\|/Users/|/home/|~/|\\\\[A-Za-z])"), "đường dẫn máy"),
    (re.compile(r"\b(?:exports|tools|scripts|ho_so_hdd|\.claude)/"), "đường dẫn máy"),
    (re.compile(r"\b[\w.\-]+\.(?:md|json|py|ya?ml|csv|docx|txt|sh)\b", re.I), "tên tệp"),
    (re.compile(r"\b[Cc]ổng\s+G(?:10|[0-9])\b"), "ký hiệu cổng"),
    (re.compile(r"\bG(?:10|[0-9])[_-](?:AUTO|A\d|T\d|checkpoint|quality)", re.I), "ký hiệu cổng"),
    (re.compile(r"\bG0\s*[–—-]\s*G10\b"), "ký hiệu cổng"),
    (re.compile(r"\b(?:PASS|READY_FOR|BLOCKED|LOCKED)_G(?:10|[0-9])"), "ký hiệu cổng"),
    (re.compile(r"\b(?:[Tt]heo|ở|tại|từ|qua)\s+G(?:10|[0-9])\b(?!\s*[–—-]\s*G)"), "ký hiệu cổng"),
    (re.compile(r"\bG(?:10|[0-9])\s*§"), "ký hiệu cổng"),
    (re.compile(r"\bTÀI LIỆU \d+\b"), "số tài liệu nội bộ gói G2"),
    (re.compile(r"\b(?:gate_params|study_meta|icf_waiver_requested|recruitment_mode|mien_icf|phu_luc_1[01])\b"),
     "khoá dữ liệu máy"),
)


def tim_dau_vet_may(van_ban: str) -> list[tuple[str, str]]:
    """[(loại, đoạn khớp)] dấu vết máy trong một chuỗi văn bản nộp."""
    ra = []
    for mau, loai in DAU_VET_MAY:
        for m in mau.finditer(van_ban or ""):
            ra.append((loai, m.group(0)))
    return ra


def _van_ban_tep(p: Path) -> str:
    return "\n".join(_van_ban_docx(p))


def _tep_bat_buoc(d: dict, quy_trinh: str) -> list[tuple[str, str]]:
    s = d["meta"]["study"]
    ds = [("Mẫu 2 (bìa thuyết minh)", f"MAU2_*_{s}.docx"), ("Mẫu 3 (bìa hồ sơ)", f"MAU3_*_{s}.docx"),
          ("Mẫu 4 (đơn)", f"MAU4_*_{s}.docx"), ("Mẫu 5 (lý lịch)", f"MAU5_*_{s}_*.docx"),
          ("phiếu thu thập (mục 7)", f"PHIEU_THU_THAP_*_{s}.docx")]
    if d.get("icf") is not None:
        ds.append(("Mẫu 8 (ICF)", f"MAU8_*_{s}.docx"))
    elif d.get("mien_icf") is not None:
        ds.append(("Đơn đề nghị miễn đồng thuận", f"MIEN_ICF_{s}.docx"))
    if quy_trinh in ("rut_gon", "ca_hai"):
        ds.append(("Mẫu 6 (Phụ lục 10)", f"MAU6_*_{s}.docx"))
    if quy_trinh in ("day_du", "ca_hai"):
        ds.append(("Mẫu 7 (Phụ lục 11)", f"MAU7_*_{s}.docx"))
    return ds


def lenh_kiem(args: argparse.Namespace) -> int:
    exports_root = Path(args.exports_root).resolve()
    study = args.study
    thu_muc_hdd = _doc_hdd(exports_root, study)
    duong_dan_json = thu_muc_hdd / "HO_SO_HDD_BVQY175.json"
    if not duong_dan_json.is_file():
        print(f"KHÔNG ĐO ĐƯỢC: chưa có {duong_dan_json}.")
        return 2
    d_goc = json.loads(duong_dan_json.read_text(encoding="utf-8"))
    d, _nang = doc_json_da_nang_cap(exports_root, study, duong_dan_json)

    van_de: list[str] = []
    con_viec: list[str] = []
    khoa_bat_buoc = ["phien_ban_schema", "meta", "bia", "don_mau4", "ly_lich_khoa_hoc", "phu_luc_10", "phu_luc_11"]
    for k in khoa_bat_buoc:
        if k not in d_goc:
            van_de.append(f"THIẾU khoá bắt buộc: {k}")
    if str(d_goc.get("phien_ban_schema")) != SCHEMA_VERSION:
        con_viec.append(f"JSON schema {d_goc.get('phien_ban_schema')} — chạy `trich --ghi` để lưu schema "
                        f"{SCHEMA_VERSION}")

    if (d.get("icf") is None) == (d.get("mien_icf") is None):
        van_de.append("LOGIC: phải có ĐÚNG MỘT trong hai, icf HOẶC mien_icf (loại trừ nhau).")

    meta_path = _doc(exports_root, study) / "study_meta.json"
    meta: dict = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title_thuc = meta.get("title")
        if title_thuc and _lay(d_goc, "bia", "ten_de_tai") not in (title_thuc, None):
            van_de.append(f"LỆCH TÊN ĐỀ TÀI: JSON='{d_goc['bia']['ten_de_tai']}' khác study_meta.title='{title_thuc}'")
    else:
        van_de.append(f"KHÔNG ĐO ĐƯỢC: thiếu {meta_path}")
    g2 = _lay(meta, "gate_params", "G2", default={}) or {}
    if g2.get("icf_waiver_requested") and d.get("icf") is not None:
        van_de.append("LOGIC: gate_params.G2.icf_waiver_requested=true nhưng JSON vẫn có khối icf (phải dùng"
                      " mien_icf).")
    if g2.get("icf_waiver_requested") is False and d.get("mien_icf") is not None:
        van_de.append("LOGIC: gate_params.G2.icf_waiver_requested=false nhưng JSON lại có mien_icf.")

    a9 = _lay(d, "phu_luc_10", "phan_ba", "A", "A9", "gia_tri")
    if g2.get("recruitment_mode") == "RETROSPECTIVE_SECONDARY_DATA" and a9 is False:
        van_de.append("LOGIC: recruitment_mode hồi cứu dữ liệu sẵn có nhưng Phụ lục 10/A9 lại đánh 'Không'.")

    quy_trinh = getattr(args, "quy_trinh", None) or _lay(d, "meta", "quy_trinh")
    if quy_trinh not in ("rut_gon", "day_du", "ca_hai"):
        quy_trinh = None
    if quy_trinh in ("rut_gon", "ca_hai"):
        co_a = [k for k in ("A1", "A2", "A3", "A4", "A5", "A6")
                if _lay(d, "phu_luc_10", "phan_ba", "A", k, "gia_tri") is True]
        if co_a:
            van_de.append(f"LOGIC: Phụ lục 10 trả lời «Có» ở {co_a} — không được xét theo quy trình rút gọn.")
        if _lay(d, "phu_luc_10", "phan_nam", "C4_thu_nghiem_thuoc_can_thiep", "gia_tri") is True:
            van_de.append("LOGIC: Phụ lục 10 C4 «Có» — không đủ tiêu chuẩn quy trình rút gọn.")

    mi = d.get("mien_icf")
    if isinstance(mi, dict):
        if CCDD.can_cu_sai(str(mi.get("can_cu", ""))):
            van_de.append("CĂN CỨ SAI: mien_icf.can_cu còn «Điều 15»/«§29» — dùng căn cứ đã đối chiếu (Helsinki §32,"
                          " CIOMS Hướng dẫn 10, TT43 Điều 7 khoản 1 điểm b).")
        bk = mi.get("ba_dieu_kien_cioms") or {}
        thieu_dk = [nhan for khoa, nhan in CCDD.BA_DIEU_KIEN_CIOMS if _cho_trong(bk.get(khoa))]
        if thieu_dk:
            con_viec.append(f"đơn miễn: chưa lập luận đủ ba điều kiện CIOMS — {thieu_dk}")
        co_xd, _ng, chung_cu = suy_du_lieu_xac_dinh_duoc(_doc_quy_trinh(_doc(exports_root, study)), g2)
        co_json = _lay(mi, "co_do", "co_du_lieu_ca_nhan_nhan_dang_duoc")
        if co_xd is True and co_json is False:
            van_de.append(f"CỜ KHÔNG TRUNG THỰC: co_du_lieu_ca_nhan_nhan_dang_duoc=false nhưng quy trình dữ liệu có"
                          f" liên kết mã ({chung_cu}).")
        if co_json is None:
            con_viec.append("đơn miễn: cờ «dữ liệu xác định được» chưa xác nhận")
        if _lay(mi, "co_do", "co_tiep_xuc_nguoi_tham_gia") is True:
            con_viec.append("đơn miễn: có tiếp xúc trực tiếp người tham gia — thường phải xin chấp thuận; kiểm lập"
                            " luận điều kiện (i)")

    so = HSC.doc_so()
    ba = ba_loai_hdd(d, so)  # đếm trên bản đã nâng cấp — đúng những ô `dung` sẽ in
    so_can = len(ba["a"])
    n_chung = HSC.NguonDeTai(exports_root, study, so)
    dau_cu = _lay(d_goc, "meta", "dau_nguon")
    if dau_cu and dau_cu != n_chung.dau_nguon():
        con_viec.append("nguồn đã chốt (đề cương nộp/study_meta/G3) đổi sau lượt trích — chạy lại `trich --ghi-de` rồi"
                        " `dung --ghi`")
    dtcs_path = _doc(exports_root, study) / "ho_so_dtcs" / "HO_SO_DTCS_BVQY175.json"
    try:
        dtcs = json.loads(dtcs_path.read_text(encoding="utf-8")) if dtcs_path.is_file() else None
    except (OSError, ValueError):
        dtcs = None
    doi_chieu = HSC.doi_chieu(n_chung, d, dtcs)
    khop, lech, khong_do = HSC.tom_tat_doi_chieu(doi_chieu)
    if lech:
        van_de.append(f"ĐỐI CHIẾU NHẤT QUÁN: {lech} chỗ lệch giữa đề cương nộp, gói G2 và hai bộ hồ sơ (xem dưới)")

    word_docs = sorted(p for p in thu_muc_hdd.glob("*.docx") if not p.name.startswith("~$"))
    moc_json = duong_dan_json.stat().st_mtime
    cu_hon = [p.name for p in word_docs if p.stat().st_mtime < moc_json]
    thieu_tep = []
    if quy_trinh is None and not any(p.name.startswith(("MAU6_", "MAU7_")) for p in word_docs):
        thieu_tep.append("Mẫu 6 hoặc Mẫu 7 (chưa rõ quy trình)")
    for nhan, mau_glob in _tep_bat_buoc(d, quy_trinh or ""):
        if not _tep_hien_co(thu_muc_hdd, mau_glob):
            thieu_tep.append(nhan)

    can_trong_word = 0
    dau_vet: list[str] = []
    for p in word_docs:
        van_ban = _van_ban_tep(p)
        can_trong_word += van_ban.count("[CẦN") - van_ban.count(CAN_KY)
        if HSC.DAU_DANH_DAU.search(van_ban):
            van_de.append(f"{p.name}: còn dấu nội bộ chưa giải (sổ lý lịch/gói ký/dữ kiện cần nhập) — chạy lại"
                          " `dung --ghi`")
        for loai, doan in tim_dau_vet_may(van_ban):
            dau_vet.append(f"{p.name}: {loai} «{doan}»")
        if p.name.startswith("PHIEU_THU_THAP_"):
            tho = [ln for ln in van_ban.split("\n") if re.match(r"^\s*(\||#{1,6}\s|```)", ln) or "**" in ln]
            if tho:
                van_de.append(f"{p.name}: còn {len(tho)} dòng cú pháp markdown thô (vd «{tho[0][:60]}»)")
    if dau_vet:
        van_de.append(f"DẤU VẾT MÁY trong văn bản nộp ({len(dau_vet)}): " + "; ".join(dau_vet[:8]))

    print(f"=== Kiểm hồ sơ HĐĐĐ BVQY175 — {study} ===")
    print(f"Ô chưa điền trong JSON: (a) suy được từ nguồn đã chốt {len(ba['a'])} · (b) gói ký {len(ba['b'])}"
          f" · (c) dữ kiện cần nhập {len(ba['c'])}")
    for duong, gia_tri in ba["a"][:40]:
        print(f"  (a) {duong}: {gia_tri[:110]}")
    print(f"Đối chiếu nhất quán đề cương nộp ↔ gói G2 ↔ hồ sơ Hội đồng Đạo đức ↔ hồ sơ đề tài cơ sở: khớp {khop} ·"
          f" lệch {lech} · không đo được {khong_do}")
    for dong_dc in HSC.in_doi_chieu(doi_chieu):
        print(dong_dc)
    if word_docs:
        print(f"Số tệp Word đã dựng: {len(word_docs)}; ô «[CẦN» trong Word: {can_trong_word}"
              + (f" — CŨ HƠN JSON: {cu_hon} (chạy lại `dung`)" if cu_hon else ""))
    else:
        print("Chưa có tệp Word nào — chạy `dung --ghi` để điền mẫu.")
    if thieu_tep:
        con_viec.append(f"thiếu tệp: {thieu_tep}")
    if van_de:
        print("\nVẤN ĐỀ:")
        for v in van_de:
            print(f"  ✗ {v}")
    if con_viec:
        print("\nCÒN VIỆC:")
        for v in con_viec:
            print(f"  - {v}")
    if van_de or con_viec or so_can > 0 or can_trong_word > 0 or not word_docs or cu_hon:
        if not van_de:
            print("\nCòn việc cần làm (xem trên).")
        return 1
    print("\nSạch — không phát hiện vấn đề cấu trúc/logic (KHÔNG thay việc bác sĩ tự kiểm nội dung).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Hồ sơ Hội đồng Đạo đức BVQY175 — sinh nháp Quyển 1 + Quyển 2."
    )
    sub = p.add_subparsers(dest="lenh", required=True)

    p_mau = sub.add_parser("mau", help="Dò bộ mẫu bệnh viện")
    p_mau.set_defaults(func=kiem_mau)

    p_trich = sub.add_parser("trich", help="Trích dữ kiện đề tài vào JSON nháp")
    p_trich.add_argument("--study", required=True)
    p_trich.add_argument("--exports-root", default="exports")
    p_trich.add_argument("--ghi", action="store_true")
    p_trich.add_argument("--ghi-de", action="store_true")
    p_trich.set_defaults(func=lenh_trich)

    p_dung = sub.add_parser("dung", help="Điền mẫu Word của bệnh viện")
    p_dung.add_argument("--study", required=True)
    p_dung.add_argument("--exports-root", default="exports")
    p_dung.add_argument("--quy-trinh", choices=["rut_gon", "day_du", "ca_hai"], required=True)
    p_dung.add_argument("--ghi", action="store_true")
    p_dung.set_defaults(func=lenh_dung)

    p_kiem = sub.add_parser("kiem", help="Kiểm JSON + Word")
    p_kiem.add_argument("--study", required=True)
    p_kiem.add_argument("--exports-root", default="exports")
    p_kiem.add_argument("--quy-trinh", choices=["rut_gon", "day_du", "ca_hai"], default=None)
    p_kiem.set_defaults(func=lenh_kiem)

    p_sct = sub.add_parser("sau-chap-thuan",
                           help="Hồ sơ gửi Hội đồng sau chấp thuận: thay đổi đề cương · tiến độ · kết quả")
    p_sct.add_argument("--study", required=True)
    p_sct.add_argument("--exports-root", default="exports")
    p_sct.add_argument("--loai", choices=["sua_doi", "tien_do", "ket_qua", "ca_ba"], default="ca_ba")
    p_sct.add_argument("--ghi", action="store_true")
    p_sct.set_defaults(func=lenh_sau_chap_thuan)

    return p


def lenh_sau_chap_thuan(args: argparse.Namespace) -> int:
    """Ba văn bản gửi Hội đồng Đạo đức sau chấp thuận — dựng theo nội dung Thông tư 43/2024/TT-BYT (không có mẫu
    nghiên cứu viên nộp trong Thông tư lẫn bộ mẫu BVQY175); xem tools/ho_so_sau_chap_thuan.py."""
    import ho_so_sau_chap_thuan as SCT  # noqa: PLC0415

    cac_loai = list(SCT.LOAI) if args.loai == "ca_ba" else [args.loai]
    ma, dong = SCT.chay(Path(args.exports_root).resolve(), args.study, cac_loai, args.ghi)
    print("\n".join(dong))
    return ma


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
