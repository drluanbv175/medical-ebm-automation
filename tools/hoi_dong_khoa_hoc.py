#!/usr/bin/env python3
"""Hội đồng Khoa học MÁY cấp đề tài — chấm đề cương như một hội đồng thật, qua Claude Batch API (22/11/2026).

VÌ SAO (bác sĩ 22/11/2026): «Nội dung có đúng chuẩn, đề cương có đúng chuẩn, đề tài nghiên cứu có đúng chuẩn hay tất
cả các vấn đề của hệ thống nghiên cứu có đúng chuẩn hay không thì vẫn do hội đồng chấm. Hãy xây dựng cho tôi hội đồng
đúng chuẩn tốt nhất và kết hợp API Claude». Hệ đã có hội đồng CỔNG (`hoi_dong_cong[_batch].py`: chấm từng NHIỆM VỤ của
một cổng theo RQ1–RQ8) và phản biện máy MỘT người đọc (`phan_bien_may_de_cuong.py`). Chưa có hội đồng CẤP ĐỀ TÀI chấm
trọn đề cương theo đúng thể thức Hội đồng Khoa học — đó là công cụ này.

Thể thức (mô phỏng Hội đồng Khoa học xét đề cương; mục chấm = «Phiếu nhận xét», Phụ lục 2 hướng dẫn chung bác sĩ gửi
21/11/2026 — cùng bảng `goi_bao_ve_hoi_dong.TIEU_CHI_PHIEU`):
- Năm thành viên CHẤM ĐỘC LẬP (mỗi người một yêu cầu, không thấy điểm người khác — tránh neo điểm): Phản biện 1
  (phương pháp luận), Phản biện 2 (chuyên môn lâm sàng), Uỷ viên thống kê, Uỷ viên đạo đức–pháp lý–liêm chính, Uỷ viên
  tổng quan–trích dẫn. Mỗi người chấm mục 1–4 của phiếu (thang 1–5 có mô tả mốc) và nêu tồn tại (mục 5).
- MỌI nhận xét phải trích NGUYÊN VĂN đề cương kèm số dòng; MÁY kiểm lại (`api_claude_nc.co_nguyen_van` trong cửa sổ
  ±3 dòng). Không khớp ⇒ «máy không xác minh được», KHÔNG vào biên bản như lỗi (liệt kê riêng, không giấu).
- Chủ tịch (bước 2) đọc các nhận xét ĐÃ xác minh: gộp trùng, phán từng nhận xét giữ/hạ mức/loại (chỉ được HẠ, không
  nâng, không thêm nhận xét mới), viết nhận xét chung và thứ tự yêu cầu chỉnh sửa.
- Thư ký là MÁY tất định: điểm trung vị từng mục, độ lệch giữa thành viên, KẾT LUẬN theo luật cố định
  (`ket_luan_tat_dinh`) — model không tự tuyên kết luận.
- Hồ sơ kiểm máy (K17 theo từng mục chuẩn, K1–K17, nhất quán xuyên cổng) phát kèm cho mọi thành viên để hội đồng dành
  sức cho PHÁN ĐOÁN chuyên môn, không đếm lại cái máy đã đếm.
- HIỆU CHUẨN (`hieu-chuan`): cài lỗi đã biết vào một BẢN SAO đề cương (đáp án lưu riêng), cho hội đồng chấm bản sao,
  rồi đo tỷ lệ bắt lỗi — chất lượng hội đồng phải chứng minh bằng số, không bằng lời tự khen.

Model: mặc định Claude Opus 5.5, `effort=high` + suy nghĩ thích ứng; Batch API (−50%) + cache prompt cho phần đề cương
dùng chung (mọi thành viên cùng một tiền tố ⇒ đọc cache 0,05×). Ước chi phí: `uoc-tinh` (0 gọi API).

Ranh giới: TƯ VẤN — không thay Hội đồng Khoa học/Hội đồng Đạo đức thật, không mở/chặn cổng, không ký, không ghi
gate_params/sổ cái, không sửa đề cương. Triệu tập tính phí là quyết định của bác sĩ: `hop` chạy khô mặc định,
`--goi-api` mới nộp/lấy batch; `bien-ban --ap-dung` mới ghi biên bản.

Dùng:
  hoi_dong_khoa_hoc.py uoc-tinh  --study <mã> [--tep <md>]
  hoi_dong_khoa_hoc.py hop       --study <mã> [--tep <md>] [--goi-api] [--lam-lai]   # lặp tới «xong»
  hoi_dong_khoa_hoc.py bien-ban  --study <mã> [--tep <md>] [--ap-dung]
  hoi_dong_khoa_hoc.py hieu-chuan --study <mã> --tao | --cham
Mã thoát: 0 xong bước · 1 có phần không hợp lệ · 2 không gọi được API · 3 tham số sai · 4 batch đang xử lý.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import api_claude_nc as API  # noqa: E402

SCHEMA = "hoi_dong_khoa_hoc/v1"
CONG_CU = "tools/hoi_dong_khoa_hoc.py"
THU_MUC = "hoi_dong_khoa_hoc"
MODEL_MAC_DINH = "claude-opus-5-5"
EFFORT = "high"
MAX_TOKENS_TV = 24000
MAX_TOKENS_CT = 24000
TOKEN_RA_UOC = 7000          # ước token ra mỗi thành viên (gồm suy nghĩ) — để báo chi phí điển hình, không phải trần
CUA_SO_DONG = 3              # trích phải nằm trong ±3 dòng quanh số dòng thành viên nêu
MUC_DO = ("nghiem_trong", "can_sua", "goi_y")
KET_LUAN = {"thong_qua": "Thông qua", "thong_qua_co_sua": "Thông qua sau khi chỉnh sửa",
            "thong_qua_cho_du_kien": "Thông qua phần thuộc thẩm quyền nhóm soạn thảo — còn dữ kiện/quyết định của "
                                     "người có thẩm quyền (liệt kê dưới)",
            "chua_dat": "Chưa đạt — chỉnh sửa tiếp theo kết luận thẩm tra",
            "khong_thong_qua": "Không thông qua (chỉnh sửa lớn, trình lại)"}
# Mục chấm điểm của Phiếu nhận xét (mục 5 «Tồn tại và đề xuất» là danh sách nhận xét, không chấm điểm).
MUC_PHIEU = {"1": "Tính cấp thiết, ý nghĩa khoa học và thực tiễn",
             "2": "Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật",
             "3": "Dự kiến kết quả",
             "4": "Chất lượng văn bản, tài liệu trích dẫn (đầy đủ, rõ ràng, xác thực, lôgíc)"}
MOC_DIEM = ("5 — Xuất sắc: đáp ứng đầy đủ chuẩn, không còn điểm cần sửa.\n"
            "4 — Tốt: chỉ còn góp ý nhỏ (mức «goi_y»).\n"
            "3 — Đạt: có điểm cần sửa nhưng không ảnh hưởng tính hợp lệ khoa học.\n"
            "2 — Chưa đạt: thiếu sót ảnh hưởng tính hợp lệ hoặc khả thi, phải sửa trước khi thông qua.\n"
            "1 — Không đạt: thiếu sót nghiêm trọng hoặc thiếu hẳn nội dung.")
# Chuẩn chung được phép dẫn (ngoài chuẩn báo cáo theo thiết kế do K17 xác định cho từng đề cương).
CHUAN_CHUNG = ("Helsinki", "CIOMS", "ICH E6", "ICH E9", "Luật 91/2025", "Nghị định 13/2023", "Vancouver", "ICMJE",
               "SAMPL", "GRADE", "COPE", "EQUATOR", "WHO TRDS", "Phiếu nhận xét")

THANH_VIEN: Tuple[Dict[str, Any], ...] = (
    {"ma": "pb1", "vai": "Phản biện 1 — Phương pháp luận nghiên cứu", "trong_tam": ("2", "3"),
     "nhiem_vu": "thiết kế có phù hợp câu hỏi và mục tiêu không; kiểm soát sai lệch chọn, đo lường, nhiễu; quần thể, "
                 "tiêu chuẩn chọn–loại, kỹ thuật chọn mẫu; định nghĩa biến và kết cục; công cụ đo (COSMIN khi có thang "
                 "đo); đề cương đáp ứng TỪNG mục của chuẩn báo cáo áp dụng cho thiết kế (danh sách ở hồ sơ kiểm máy)."},
    {"ma": "pb2", "vai": "Phản biện 2 — Chuyên môn lâm sàng", "trong_tam": ("1", "2", "3"),
     "nhiem_vu": "tính cấp thiết và ý nghĩa lâm sàng; định nghĩa bệnh, kết cục, ngưỡng có đúng TIÊU CHUẨN của nguồn "
                 "được dẫn (vd định nghĩa theo guideline nào, thời gian kéo dài bao lâu); tính khả thi tại cơ sở ngoại "
                 "trú Việt Nam; kết quả dự kiến có dùng được cho thực hành không."},
    {"ma": "uv_tk", "vai": "Uỷ viên — Thống kê sinh học", "trong_tam": ("2", "3"),
     "nhiem_vu": "công thức cỡ mẫu đúng thiết kế, tham số có nguồn, tính lại ra đúng N; kế hoạch phân tích (kiểm "
                 "định/mô hình đúng loại biến, biến hiệu chỉnh có lý do, dữ liệu thiếu, đa so sánh, phân tích độ nhạy, "
                 "phân tích nhóm nhỏ định trước); khung bảng dự kiến khớp mục tiêu; trình bày số theo SAMPL."},
    {"ma": "uv_dd", "vai": "Uỷ viên — Đạo đức, pháp lý và liêm chính nghiên cứu", "trong_tam": ("2", "4"),
     "nhiem_vu": "đồng thuận tham gia (hoặc lý do miễn), quyền rút lui, rủi ro–lợi ích, bảo vệ dữ liệu cá nhân (Luật "
                 "91/2025), khử định danh, lưu trữ–huỷ, xung đột lợi ích, nguồn kinh phí, đăng ký nghiên cứu; theo "
                 "Helsinki, CIOMS, ICH E6(R3). Đây là ý kiến tư vấn — KHÔNG thay Hội đồng Đạo đức."},
    {"ma": "uv_tl", "vai": "Uỷ viên — Tổng quan tài liệu và trích dẫn", "trong_tam": ("1", "4"),
     "nhiem_vu": "tổng quan cập nhật, đủ nghiên cứu then chốt trong và ngoài nước; khoảng trống có căn cứ; MỌI con số "
                 "và khẳng định ở đặt vấn đề/tổng quan có trích dẫn; trích dẫn đúng thứ tự Vancouver, tài liệu khớp "
                 "câu khẳng định; văn bản rõ ràng, nhất quán, không mâu thuẫn giữa các chương."},
)


# ── QC-HDKH-3.0 (bác sĩ 22/11/2026 duyệt): loại tài liệu ngoài đề cương ─────────────────────────────────────────────
# «Phiếu nhận xét» Phụ lục 2 dùng chung cho xét đề cương (mục 3 = dự kiến kết quả) và NGHIỆM THU (mục 3 = kết quả) —
# xem `goi_bao_ve_hoi_dong.TIEU_CHI_PHIEU`. SAP và bản thảo dùng phiếu riêng (nội dung SAP theo Gamble và cs., JAMA
# 2017, PMID 29260229; bản thảo theo chuẩn báo cáo của thiết kế + ICMJE). Vòng kín (biên tập có rào) CHỈ cho đề cương:
# SAP đã khoá ở G4 không được máy sửa; bản thảo/báo cáo chưa có bộ rào văn bản riêng.
LOAI_TAI_LIEU: Dict[str, Dict[str, Any]] = {
    "de_cuong": {
        "ten": "đề cương nộp Hội đồng", "mau_tep": "DE_CUONG_NOP_HOI_DONG_{s}.md", "vong_kin": True,
        "phieu": dict(MUC_PHIEU),
        "chu_y": "",
    },
    "sap": {
        "ten": "kế hoạch phân tích thống kê (SAP)", "mau_tep": "G4_A5_SAP_FINAL_{s}.md", "vong_kin": False,
        "phieu": {
            "1": "Khớp đề cương: câu hỏi, giả thuyết, kết cục, quần thể và cỡ mẫu đã đăng ký",
            "2": ("Phương pháp thống kê: quần thể phân tích, mô hình và giả định, dữ liệu thiếu, đa so sánh, phân "
                  "tích nhóm nhỏ và độ nhạy"),
            "3": ("Kế hoạch trình bày và diễn giải kết quả (khung bảng, hình, quy tắc làm tròn, cách đọc kết quả "
                  "không có ý nghĩa thống kê)"),
            "4": ("Chất lượng văn bản, khả năng tái lập (phần mềm, phiên bản, kiểm soát thay đổi) và trích dẫn phương "
                  "pháp"),
        },
        "chu_y": ("SAP đã khoá ở cổng G4 thì mọi đề xuất là ĐỀ XUẤT SỬA ĐỔI SAP để chủ nhiệm/thống kê viên quyết (ghi "
                  "rõ trong «de_xuat»); đối chiếu SAP với đề cương (kết cục chính, quần thể, cỡ mẫu)."),
    },
    "ban_thao": {
        "ten": "bản thảo bài báo", "mau_tep": "G7_A8_MANUSCRIPT_{s}.md", "vong_kin": False,
        "phieu": {
            "1": "Tính mới, ý nghĩa khoa học và thực tiễn; câu hỏi nghiên cứu rõ",
            "2": "Phương pháp và mức tuân thủ chuẩn báo cáo theo thiết kế",
            "3": ("Kết quả và diễn giải: số liệu khớp giữa tóm tắt, bài và bảng; kết luận đúng mức chứng cứ, không "
                  "khái quát quá mức"),
            "4": ("Văn bản, trích dẫn và liêm chính công bố (ICMJE: tác giả, xung đột lợi ích, khai báo dùng AI, chia "
                  "sẻ dữ liệu)"),
        },
        "chu_y": ("đối chiếu số giữa tóm tắt, kết quả và bảng; kết luận chỉ rút từ kết quả đã trình bày; không khẳng "
                  "định nhân quả vượt thiết kế."),
    },
    "bao_cao": {
        "ten": "báo cáo tổng hợp kết quả (nghiệm thu)", "mau_tep": "BAO_CAO_TONG_HOP_{s}.md", "vong_kin": False,
        "phieu": {"1": "Tính cấp thiết, ý nghĩa khoa học và thực tiễn của đề tài",
                  "2": "Mục tiêu và phương pháp nghiên cứu; phương pháp tính toán và kỹ thuật đã sử dụng",
                  "3": "Kết quả nghiên cứu",
                  "4": "Chất lượng của Báo cáo tổng hợp đề tài nghiên cứu, sản phẩm trung gian, tài liệu trích dẫn "
                       "(đầy đủ, rõ ràng, xác thực và lôgíc)"},
        "chu_y": ("đối chiếu kết quả với mục tiêu và nội dung đã đăng ký trong đề cương; mức độ hoàn thành; sản phẩm "
                  "đúng như đăng ký."),
    },
}


def phieu(loai: str = "de_cuong") -> Dict[str, str]:
    return LOAI_TAI_LIEU[loai]["phieu"]


# ── QC-HDKH-3.0: ghế uỷ viên CHUYÊN THIẾT KẾ (đổi theo gate_params.G1.design) + ghế kinh tế y tế khi có cấu phần ──
THIET_KE_BI_DANH = {"diagnostic_accuracy": "diagnostic", "systematic_review": "sr_ma", "prediction_model": "prediction"}
GHE_THIET_KE: Dict[str, Dict[str, str]] = {
    "rct": {
        "vai": "Uỷ viên — Thử nghiệm lâm sàng và an toàn người tham gia",
        "nhiem_vu": ("ngẫu nhiên hoá (tạo chuỗi, che giấu phân bổ), làm mù, nhóm chứng, kết cục và ước lượng mục tiêu "
                     "(estimand, ICH E9(R1)), phân tích theo ý định điều trị, quy tắc dừng và hội đồng theo dõi dữ "
                     "liệu (DMC/DSMB), định nghĩa và báo cáo biến cố bất lợi (AE/SAE), tuân thủ can thiệp; đối chiếu "
                     "SPIRIT 2025/CONSORT 2025 và ICH E6(R3)."),
    },
    "cohort": {
        "vai": "Uỷ viên — Dịch tễ học nghiên cứu thuần tập",
        "nhiem_vu": ("định nghĩa phơi nhiễm và thời điểm bắt đầu theo dõi (tránh sai lệch thời gian bất tử), chọn "
                     "nhóm so sánh, mất theo dõi, xác định kết cục độc lập với phơi nhiễm, nhiễu và đồ thị nhân quả "
                     "(DAG), phương pháp sống còn và biến cố cạnh tranh; đối chiếu STROBE."),
    },
    "case_control": {
        "vai": "Uỷ viên — Dịch tễ học nghiên cứu bệnh – chứng",
        "nhiem_vu": ("định nghĩa ca bệnh, nguồn và cách chọn nhóm chứng (cùng quần thể nguồn, không chọn theo phơi "
                     "nhiễm), ghép cặp và phân tích tương ứng, sai lệch nhớ lại, đo phơi nhiễm trước khởi phát; đối "
                     "chiếu STROBE."),
    },
    "cross_sectional": {
        "vai": "Uỷ viên — Dịch tễ học nghiên cứu cắt ngang",
        "nhiem_vu": ("khung mẫu và cách chọn mẫu đại diện quần thể đích, hiệu ứng thiết kế khi chọn cụm, tỷ lệ đáp "
                     "ứng, định nghĩa ca theo đúng tiêu chuẩn của nguồn, ước lượng tỷ lệ kèm khoảng tin cậy, không "
                     "suy diễn trình tự thời gian; đối chiếu STROBE."),
    },
    "diagnostic": {
        "vai": "Uỷ viên — Nghiên cứu độ chính xác chẩn đoán",
        "nhiem_vu": ("tiêu chuẩn tham chiếu và xác minh đầy đủ (tránh sai lệch xác minh), phổ bệnh của mẫu, làm mù "
                     "khi đọc kết quả, ngưỡng định trước, khoảng thời gian giữa xét nghiệm và tham chiếu, kết quả "
                     "không xác định; đối chiếu STARD 2015 và QUADAS-3."),
    },
    "prediction": {
        "vai": "Uỷ viên — Mô hình dự báo và trí tuệ nhân tạo lâm sàng",
        "nhiem_vu": ("cỡ mẫu cho mô hình (số biến cố trên tham số, cách tính của Riley), chọn yếu tố dự báo, dữ liệu "
                     "thiếu, quá khớp và kiểm định nội/ngoại, hiệu chuẩn và khả năng phân biệt, độ hữu ích lâm sàng, "
                     "công bằng giữa các nhóm; đối chiếu TRIPOD+AI và PROBAST+AI."),
    },
    "sr_ma": {
        "vai": "Uỷ viên — Tổng quan hệ thống và phân tích gộp",
        "nhiem_vu": ("đăng ký đề cương (PROSPERO), chiến lược tìm nhiều cơ sở dữ liệu và tài liệu xám (PRISMA-S), "
                     "sàng lọc và trích xuất độc lập hai người, công cụ đánh giá nguy cơ sai lệch đúng thiết kế, mô "
                     "hình gộp và không đồng nhất, sai lệch công bố, mức chắc chắn GRADE; đối chiếu PRISMA-P 2015."),
    },
    "qualitative": {
        "vai": "Uỷ viên — Phương pháp nghiên cứu định tính",
        "nhiem_vu": ("tiếp cận phương pháp luận, lấy mẫu có chủ đích và tiêu chí bão hoà (không dùng công thức cỡ mẫu "
                     "thống kê), hướng dẫn phỏng vấn, tính phản thân của người nghiên cứu, quy trình mã hoá và phân "
                     "tích chủ đề, tính tin cậy (đối chiếu, kiểm tra với người tham gia); đối chiếu COREQ và SRQR."),
    },
}
GHE_KINH_TE: Dict[str, Any] = {
    "ma": "uv_kt", "vai": "Uỷ viên — Kinh tế y tế", "trong_tam": ("2", "3"),
    "nhiem_vu": ("quan điểm phân tích, khung thời gian, nguồn chi phí và giá, đo kết cục sức khoẻ (QALY/DALY), mô "
                 "hình (Markov, cây quyết định), chiết khấu, tỷ số ICER và ngưỡng sẵn lòng chi trả, phân tích độ nhạy "
                 "xác suất; đối chiếu CHEERS 2022."),
}
_CO_KINH_TE = re.compile(r"chi phí\s*[–-]\s*hiệu quả|\bICER\b|\bQALY|\bDALY|tác động ngân sách|kinh tế y tế"
                         r"|cost[- ]effectiveness", re.IGNORECASE)


def chuan_hoa_thiet_ke(thiet_ke: str) -> str:
    t = (thiet_ke or "").strip().lower()
    return THIET_KE_BI_DANH.get(t, t)


def thanh_phan_hoi_dong(thiet_ke: str, van: str, loai: str = "de_cuong") -> List[Dict[str, Any]]:
    """Năm ghế cố định + ghế CHUYÊN THIẾT KẾ (thiết kế đã chốt ở G1) + ghế kinh tế y tế khi tài liệu có cấu phần
    kinh tế. Thiết kế không xác định ⇒ không có ghế chuyên thiết kế (biên bản ghi rõ)."""
    ds = [dict(t) for t in THANH_VIEN]
    g = GHE_THIET_KE.get(chuan_hoa_thiet_ke(thiet_ke))
    if g:
        ds.append({"ma": "uv_ctk", "trong_tam": ("2", "3"), **g})
    if _CO_KINH_TE.search(van or ""):
        ds.append(dict(GHE_KINH_TE))
    for t in ds:  # 4.0: agent sở hữu chuyên môn của từng ghế
        t["tac_nhan"] = list(tac_nhan_cua_ghe(t["ma"], loai, thiet_ke))
    return ds


def tuc_so(so_ghe: int) -> int:
    """Túc số = QUÁ BÁN số ghế của phiên (5 ghế ⇒ 3; 6 hoặc 7 ghế ⇒ 4)."""
    return so_ghe // 2 + 1


def _ds_tv(st: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(st.get("thanh_phan") or THANH_VIEN)


# ── QC-HDKH-4.0 (bác sĩ 22/11/2026: «phải kết hợp đồng thời Claude Code, các Agent và hệ thống») ─────────────────
# Mỗi ghế mang DOCTRINE của agent sở hữu chuyên môn trong `.claude/agents/` — đọc từ BẢN CHỤP KHOÁ
# `docs/hoi-dong/DOCTRINE_GHE.json` (SHA tính vào quy chế). Không đọc tệp agent đang sống: tệp agent đổi thường xuyên,
# đọc sống làm quy chế đổi ngầm. Chụp lại là việc có chủ ý (`chup-doctrine --ghi`) ⇒ quy chế mới ⇒ hiệu chuẩn lại.
TAC_NHAN_GHE: Dict[str, Tuple[str, ...]] = {
    "pb1": ("thiet-ke-nghien-cuu",), "pb2": ("huong-dan-lam-sang",),
    "uv_tk": ("co-mau-nghien-cuu", "phan-tich-thong-ke"), "uv_dd": ("dao-duc-dang-ky",),
    "uv_tl": ("kiem-chung-trich-dan", "tong-quan-y-van"), "uv_kt": ("kinh-te-y-te",),
}
TAC_NHAN_THIET_KE: Dict[str, Tuple[str, ...]] = {
    "rct": ("an-toan-nghien-cuu",), "cohort": ("bien-so-nghien-cuu",), "case_control": ("bien-so-nghien-cuu",),
    "cross_sectional": ("bien-so-nghien-cuu",), "diagnostic": ("tham-dinh-do-chinh-xac-chan-doan",),
    "prediction": ("mo-hinh-tien-luong",), "sr_ma": ("meta-phan-tich",), "qualitative": ("nghien-cuu-dinh-tinh",),
}
TAC_NHAN_THEO_LOAI: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "sap": {"uv_tk": ("thiet-ke-nghien-cuu",)},          # thiet-ke-nghien-cuu soạn và KHOÁ SAP ở G4
    "ban_thao": {"uv_tl": ("viet-ban-thao",)}, "bao_cao": {"uv_tl": ("viet-ban-thao",)},
}
TEP_DOCTRINE = "docs/hoi-dong/DOCTRINE_GHE.json"
TRAN_DOCTRINE = 6000
_MUC_DOCTRINE = re.compile(r"(?i)luật|nguyên tắc|tiêu chí|bài học|mục tiêu|ranh giới|tự kiểm|chuẩn|đo lại|đồng bộ"
                           r"|bắt buộc|trách nhiệm")
_MUC_BO_DOCTRINE = re.compile(r"(?i)chế độ tự động|bước 0|mẫu đầu ra|ví dụ|định dạng trả về|cài đặt|full auto")


def tac_nhan_cua_ghe(ma: str, loai: str = "de_cuong", thiet_ke: str = "") -> Tuple[str, ...]:
    goc = TAC_NHAN_THIET_KE.get(chuan_hoa_thiet_ke(thiet_ke), ()) if ma == "uv_ctk" else TAC_NHAN_GHE.get(ma, ())
    them = TAC_NHAN_THEO_LOAI.get(loai, {}).get(ma, ())
    return tuple(dict.fromkeys(goc + them))


def trich_doctrine(van: str, toi_da: int = TRAN_DOCTRINE) -> str:
    """Phần CHUYÊN MÔN của tệp agent (luật, tiêu chí, bài học, ranh giới…), bỏ phần thao tác công cụ/ví dụ."""
    than = van.split("\n---", 1)[1] if van.startswith("---") and "\n---" in van else van
    phan = [x for x in re.split(r"(?m)^(?=#{1,3}\s)", than) if x.strip()]
    giu = [x for x in phan if x.lstrip().startswith("#") and _MUC_DOCTRINE.search(x.splitlines()[0])
           and not _MUC_BO_DOCTRINE.search(x.splitlines()[0])]
    return ("\n".join(giu) if giu else than).strip()[:toi_da]


def chup_doctrine(goc_repo: Path = REPO) -> Dict[str, Any]:
    """Bản chụp doctrine của MỌI agent được gắn ghế (đọc tệp agent đang sống — chỉ dùng khi chụp có chủ ý)."""
    ten = sorted({t for v in list(TAC_NHAN_GHE.values()) + list(TAC_NHAN_THIET_KE.values()) for t in v}
                 | {t for d in TAC_NHAN_THEO_LOAI.values() for v in d.values() for t in v})
    ra: Dict[str, Any] = {}
    for t in ten:
        f = goc_repo / ".claude" / "agents" / f"{t}.md"
        try:
            van = f.read_text(encoding="utf-8")
            ra[t] = {"sha_tep": hashlib.sha256(van.encode("utf-8")).hexdigest(), "doctrine": trich_doctrine(van)}
        except OSError:
            ra[t] = {"sha_tep": None, "doctrine": ""}
    return ra


def doc_doctrine(goc_repo: Path = REPO) -> Dict[str, Any]:
    try:
        return json.loads((goc_repo / TEP_DOCTRINE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def khoi_doctrine(tac_nhan: Sequence[str], ban_chup: Optional[Dict[str, Any]] = None) -> str:
    bc = doc_doctrine() if ban_chup is None else ban_chup
    khoi = []
    for t in tac_nhan:
        d = (bc.get(t) or {}).get("doctrine") or ""
        khoi.append(f"--- Doctrine của agent hệ `{t}` ---\n{d}" if d else
                    f"--- Doctrine của agent hệ `{t}`: KHÔNG có trong bản chụp (chấm theo nhiệm vụ của ghế) ---")
    return "\n".join(khoi)


# ── 4.0: bằng chứng CÔNG CỤ của hệ cho hội đồng (chấm sống từng cổng, cỡ mẫu G3, biên nhận trích dẫn A12) ──
CONG_HE = ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10")


def bang_chung_he(study: str, out_dir: Path) -> Dict[str, Any]:
    """Đo bằng công cụ tất định của hệ; thư mục không có checkpoint cổng (hộp cát) ⇒ ghi rõ «không có»."""
    if not any((out_dir / f"{g}_checkpoint.json").exists() for g in CONG_HE):
        return {"ghi_chu": "không có checkpoint cổng nào trong thư mục đề tài — không có bằng chứng công cụ của hệ"}
    ra: Dict[str, Any] = {"cong_song": {}}
    try:
        import cong_song as CS  # noqa: PLC0415

        for g in CONG_HE:
            if not (out_dir / f"{g}_checkpoint.json").exists():
                continue
            kq = CS.trang_thai_song(g, study, out_dir)
            bc = kq.get("bao_cao") or {}
            chua = [f"{x.get('id')}: {x.get('label')}" for k in ("automatic_criteria", "human_criteria")
                    for x in bc.get(k) or [] if str(x.get("status")) not in ("PASS", "NA", "N/A", "SKIP")]
            ra["cong_song"][g] = {"trang_thai": kq.get("status"), "muc": kq.get("muc"), "chua_dat": chua[:8]}
    except Exception as exc:  # noqa: BLE001
        ra["cong_song"] = f"không đo được ({type(exc).__name__})"
    g3 = _doc_st(out_dir / "G3_checkpoint.json") or {}
    if g3:
        ra["co_mau_g3"] = {k: g3.get(k) for k in ("design_code", "alpha", "power", "effect_type", "effect_val",
                                                   "n_total", "n_adjusted", "confirmed_n") if k in g3}
    md = _doc_st(out_dir / "A12_METADATA_RECEIPT.json") or {}
    rb = _doc_st(out_dir / "A12_RETRACTION_RECEIPT.json") or {}
    if md or rb:
        kq_rut = rb.get("results") if isinstance(rb.get("results"), dict) else {}
        ra["trich_dan_a12"] = {"so_pmid_da_kiem": len(md.get("pmids_checked") or rb.get("pmids_checked") or []),
                               "metadata_du": md.get("all_resolved"), "khong_bai_rut": rb.get("all_clean"),
                               "pmid_co_van_de": {k: (v or {}).get("status") for k, v in kq_rut.items()
                                                  if (v or {}).get("status") != "ok"}}
    return ra


# ── 4.0: cấu trúc BÁO CÁO TỔNG HỢP KẾT QUẢ theo hướng dẫn chung bác sĩ gửi 21/11/2026 (mục III, bản BV TƯQĐ 108 2019 —
# BVQY175 chưa có mẫu báo cáo riêng): thứ tự chương, 50–60 trang, kết luận và khuyến nghị mỗi phần 1–2 trang.
CAU_TRUC_BAO_CAO: Tuple[Tuple[str, str], ...] = (
    ("Danh sách cán bộ tham gia", r"danh sách (?:các )?cán bộ"), ("Mục lục", r"mục lục"),
    ("Danh mục chữ viết tắt", r"chữ viết tắt"), ("Danh mục bảng biểu", r"danh mục (?:các )?(?:bảng|biểu)"),
    ("Đặt vấn đề", r"đặt vấn đề"), ("Chương 1: Tổng quan tài liệu", r"tổng quan"),
    ("Chương 2: Đối tượng và phương pháp nghiên cứu", r"đối tượng và phương pháp|phương pháp nghiên cứu"),
    ("Chương 3: Kết quả", r"kết quả"), ("Chương 4: Bàn luận", r"bàn luận"), ("Kết luận", r"kết luận"),
    ("Khuyến nghị", r"khuyến nghị|kiến nghị"), ("Tài liệu tham khảo", r"tài liệu tham khảo"), ("Phụ lục", r"phụ lục"),
)
TU_MOI_TRANG = 450          # ước lượng thô (A4, cỡ 13–14, giãn dòng 1,5) — chỉ để cảnh báo, không chặn


def kiem_cau_truc_bao_cao(van: str) -> Dict[str, Any]:
    dong = van.splitlines()
    de_muc = [(i, d) for i, d in enumerate(dong) if re.match(r"^#{1,3}\s", d)]
    vi_tri, thieu = [], []
    for ten, mau in CAU_TRUC_BAO_CAO:
        k = next((i for i, d in de_muc if re.search(mau, d, re.IGNORECASE)), None)
        (thieu.append(ten) if k is None else vi_tri.append((k, ten)))
    thu_tu = [t for _, t in sorted(vi_tri)]
    mong = [t for t, _ in CAU_TRUC_BAO_CAO if t in thu_tu]
    sai_thu_tu = [t for t, m in zip(thu_tu, mong) if t != m]

    def so_tu(mau: str) -> Optional[int]:
        k = next((i for i, d in de_muc if re.search(mau, d, re.IGNORECASE)), None)
        if k is None:
            return None
        j = next((i for i, _ in de_muc if i > k), len(dong))
        return len(" ".join(dong[k + 1:j]).split())

    trang = round(len(van.split()) / TU_MOI_TRANG, 1)
    kl, kn = so_tu(r"^#{1,3}\s*(?:\d+\.?\s*)?kết luận"), so_tu(r"khuyến nghị|kiến nghị")
    canh_bao = ([f"thiếu: {', '.join(thieu)}"] if thieu else []) + (
        [f"thứ tự chương lệch hướng dẫn ở: {', '.join(sai_thu_tu)}"] if sai_thu_tu else []) + (
        [f"ước ~{trang} trang (> 60)"] if trang > 60 else []) + (
        [f"kết luận ~{round(kl / TU_MOI_TRANG, 1)} trang (> 2)"] if kl and kl > 2 * TU_MOI_TRANG else []) + (
        [f"khuyến nghị ~{round(kn / TU_MOI_TRANG, 1)} trang (> 2)"] if kn and kn > 2 * TU_MOI_TRANG else [])
    return {"thieu": thieu, "sai_thu_tu": sai_thu_tu, "uoc_trang": trang, "canh_bao": canh_bao,
            "can_cu": "hướng dẫn chung mục III (bác sĩ gửi 21/11/2026; bản BV TƯQĐ 108, 2019) — BVQY175 chưa có mẫu "
                      "báo cáo tổng hợp riêng"}


class LoiThamSo(ValueError):
    """Tham số sai — mã 3."""


# ── QUY CHẾ hội đồng — khoá TRƯỚC khi họp (bác sĩ 22/11/2026) ───────────────────────────────────────────────────────
# «Phải đảm bảo hội đồng hoạt động theo quy trình khoa học nghiêm ngặt, được lên kế hoạch kỹ lưỡng ngay từ đầu và được
# thực hiện với sự trung thực tuyệt đối. Khi hội đồng đã quyết định thì vấn đề được thông qua … nếu không được thì phải
# chỉnh sửa theo hội đồng». ⇒ Mọi luật (thành phần, tiêu chí, mốc điểm, xác minh, kết luận, rào biên tập, hiệu chuẩn,
# model, NGUYÊN VĂN mọi lời dặn) gom vào MỘT quy chế có phiên bản + SHA-256. Phiên mang SHA lúc khởi tạo; quy chế đổi
# giữa phiên ⇒ phiên hết hiệu lực. Kết luận chỉ có HIỆU LỰC khi hội đồng đã hiệu chuẩn đạt ngưỡng DƯỚI ĐÚNG quy chế đó.
PHIEN_BAN_QUY_CHE = "QC-HDKH-4.0"
NGAY_KHOA_QUY_CHE = "2026-11-22"
TUC_SO = 3
DO_NHAY_TOI_THIEU = 5 / 6        # mỗi bản cài lỗi phải bắt ≥ 5/6 lỗi
TEP_QUY_CHE = "docs/QUY-CHE-HOI-DONG-KHOA-HOC-MAY.md"


def ke_hoach(model: str = MODEL_MAC_DINH) -> Dict[str, Any]:
    """Quy chế đầy đủ (dữ liệu thuần, xác định) — nguồn của SHA và của văn bản quy chế."""
    return {
        "phien_ban": PHIEN_BAN_QUY_CHE, "ngay_khoa": NGAY_KHOA_QUY_CHE,
        "lich_su": ["1.0 (22/11/2026): bản đầu — hiệu chuẩn 6/6 trên bản sao BTM và C1a.",
                    "1.1 (22/11/2026): đo thật dưới 1.0 — 85% thay thế đúng bị loại oan vì luật «đúng dòng ±3» "
                    "(dòng lệch sau các thay thế trước; nhiều vấn đề phải sửa ở chỗ khác chỗ nêu) ⇒ bỏ ràng buộc dòng "
                    "của THAY THẾ (an toàn vẫn nhờ đoạn cũ duy nhất; nhận xét của hội đồng vẫn ±3 dòng); dạy biên tập "
                    "viên K4/K10/K11/K15; trần đoạn thay 3.000 ký tự (khung bảng). Phải hiệu chuẩn lại dưới SHA mới.",
                    "2.0 (22/11/2026): đo thật dưới 1.1 — mỗi vòng hội đồng đọc lại TOÀN VĂN và nêu vấn đề mới (BTM 10→"
                    "13→13, C1a 10→15→14), không hội tụ. Bác sĩ chọn quy trình THẨM TRA CHỈNH SỬA như hội đồng thật: "
                    "vòng 1 thẩm định toàn diện; các vòng sau mỗi thành viên chỉ thẩm tra yêu cầu mình đã nêu (đã giải "
                    "quyết — trích bằng chứng / chưa giải quyết / cần dữ kiện của người có thẩm quyền) và lỗi mới CHỈ "
                    "trong đoạn vừa sửa. Bắt đầu lại từ đề cương gốc; hiệu chuẩn lại.",
                    "2.1 (22/11/2026): đo thật dưới 2.0 — hội tụ (BTM 13→8→7→5, C1a 22→10→9→4) nhưng chưa thông qua "
                    "sau 4 vòng vì ba lỗi QUY TRÌNH: phản hồi thẩm tra hỏng JSON bị tính là «chưa giải quyết» (4/5 "
                    "yêu cầu còn lại của BTM); biên tập viên không được báo lý do rào đã loại bản sửa nên lặp lại bản "
                    "bị loại; K10 bắt nhầm «khoảng tin cậy 95%» là số liệu. Sửa: phản hồi hỏng ⇒ nộp lại tối đa 2 lần "
                    "rồi mới fail-safe; biên tập viên nhận lý do chưa đạt của người thẩm tra và lý do rào loại; tối "
                    "đa 6 vòng. Bắt đầu lại từ đề cương gốc; hiệu chuẩn lại.",
                    "3.0 (22/11/2026, bác sĩ duyệt bốn việc): (a) ghế uỷ viên CHUYÊN THIẾT KẾ theo thiết kế đã chốt "
                    "ở G1 (8 thiết kế) + ghế kinh tế y tế khi có cấu phần kinh tế, túc số quá bán; (b) ĐO BÁO NHẦM — "
                    "trọng tài độc lập khác model phán từng nhận xét ngoài lỗi cài, có đối chứng dương/âm để kiểm "
                    "chính trọng tài; hiệu lực kết luận cần CẢ độ nhạy lẫn độ chính xác; (c) lỗi cài đặc thù từng "
                    "thiết kế để hiệu chuẩn trên đủ 8 thiết kế; (d) mở rộng sang SAP, bản thảo bài báo và báo cáo "
                    "tổng hợp kết quả (nghiệm thu), mỗi loại một phiếu, bộ chuẩn và bộ lỗi cài riêng; vòng kín vẫn "
                    "chỉ cho đề cương. Mọi hiệu chuẩn cũ hết hiệu lực.",
                    "4.0 (22/11/2026, bác sĩ: «phải kết hợp đồng thời Claude Code, các Agent và hệ thống», «phân "
                    "chia thế mạnh từng thành phần», chọn «kết hợp có trọng tâm»): API chỉ họp thẩm định độc lập MỘT "
                    "lần mỗi phiên bản tài liệu; mỗi ghế mang doctrine agent của hệ (bản chụp khoá) và bằng chứng "
                    "công cụ của hệ; thẩm định nhận xét, biên tập, thẩm tra, chốt cuối và trọng tài đo báo nhầm do "
                    "agent Claude Code làm qua phiếu việc máy-kiểm-được. Đo thật cùng ngày: chốt kiểm "
                    "tham-dinh-dau-ra trả về CẢ HAI đề cương «thông qua» theo 2.1 (biên tập viên API sửa vào SAP đã "
                    "khoá, mã hoá biến đã duyệt, đăng ký, xung đột lợi ích) ⇒ thêm RÀO NỘI DUNG ĐÃ KHOÁ và chốt cuối "
                    "bắt buộc trước khi trình bác sĩ."],
        "muc_dich": "Chấm tài liệu nghiên cứu (đề cương, SAP, bản thảo, báo cáo nghiệm thu) theo thể thức Hội đồng "
                    "Khoa học, tư vấn — không thay hội đồng thật.",
        "phan_chia_the_manh": [
            "Công cụ tất định của hệ (luật K1–K18, chấm sống cổng G0–G10, nhất quán xuyên cổng, cỡ mẫu G3, biên nhận "
            "trích dẫn A12, kiểm cấu trúc báo cáo, rào biên tập) — mọi việc ĐO được; 0 USD.",
            "Claude API (Batch) — các ghế đọc ĐỘC LẬP, song song, MỘT lần thẩm định mỗi phiên bản tài liệu; không dùng "
            "cho việc công cụ đo được, không lặp đọc toàn văn.",
            "Agent Claude Code của hệ — thẩm định nhận xét cần tra cứu/tính lại, biên tập, thẩm tra chỉnh sửa, trọng "
            "tài đo báo nhầm, chốt cuối tham-dinh-dau-ra; có công cụ và doctrine; qua phiếu việc máy-kiểm-được.",
            "Claude Code (phiên điều phối) — giao phiếu việc, chẩn đoán vòng kẹt, sửa công cụ khi máy sai.",
            "Chủ nhiệm / thống kê viên / bác sĩ — mọi nội dung đã khoá (SAP, bộ biến, đăng ký, xung đột lợi ích, kinh "
            "phí, nhân sự), ký cổng; nhận danh sách «cần dữ kiện»."],
        "doctrine": {"tep": TEP_DOCTRINE, "sha_ban_chup": _sha_tep(REPO / TEP_DOCTRINE),
                     "gan_ghe": {k: list(v) for k, v in TAC_NHAN_GHE.items()},
                     "gan_thiet_ke": {k: list(v) for k, v in TAC_NHAN_THIET_KE.items()},
                     "gan_theo_loai": {lo: {k: list(v) for k, v in d.items()} for lo, d in TAC_NHAN_THEO_LOAI.items()},
                     "tran_ky_tu": TRAN_DOCTRINE},
        "ket_hop": {"cho_agent": f"mã thoát {CHO_AGENT}: phiếu việc ghi ở hoi_dong_khoa_hoc/viec_agent/, Claude Code "
                                 "giao đúng agent (lệnh viec-agent), agent ghi JSON vào đường dẫn định sẵn",
                    "tham_dinh": "nhận xét đã qua chủ tịch → agent sở hữu chuyên môn của ghế; «sai» phải có cơ sở "
                                 + "/".join(CO_SO_SAI) + "; agent phải phán đúng đối chứng âm, sai ⇒ không áp phán "
                                 "quyết của agent đó; nhận xét bị bác có chứng minh ⇒ không phải sửa, ghi biên bản",
                    "bien_tap": {k: v for k, v in TAC_NHAN_BIEN_TAP.items()},
                    "tham_tra": "agent sở hữu của ghế đã nêu — cùng luật máy-kiểm như thẩm tra API",
                    "chot_cuoi": "tham-dinh-dau-ra BẮT BUỘC trước khi trình bác sĩ; lỗi đã xác minh ⇒ thành yêu cầu "
                                 "sửa của vòng sau",
                    "trong_tai_mac_dinh": f"agent {TRONG_TAI_AGENT} (API Fable chỉ khi chọn --trong-tai api)",
                    "hieu_chuan": "chế độ kết hợp chỉ có hiệu lực khi hiệu chuẩn cũng chạy chế độ kết hợp"},
        "rao_khoa": {"luon_khoa": _KHOA_LUON.pattern, "khoa_khi_sap_da_khoa": _KHOA_KHI_SAP.pattern,
                     "sap_da_chot": "chấm sống G4 mức PASS hoặc READY",
                     "mo_khoa": _MO_KHOA.pattern, "dong_khoa": _DONG_KHOA.pattern,
                     "luat": "thay thế chạm vùng khoá ⇒ loại, yêu cầu thành «vượt thẩm quyền — cần dữ kiện»; bản đã "
                             "qua hội đồng mà chốt cuối nêu lỗi vượt thẩm quyền ⇒ hoàn nguyên đúng các khối chạm vùng "
                             "khoá/dòng bị nêu về bản gốc, giữ các khối khác"},
        "thanh_phan": [{"ma": t["ma"], "vai": t["vai"], "trong_tam": list(t["trong_tam"]), "nhiem_vu": t["nhiem_vu"]}
                       for t in THANH_VIEN],
        "ghe_thiet_ke": {k: dict(v) for k, v in GHE_THIET_KE.items()},
        "ghe_kinh_te": {"vai": GHE_KINH_TE["vai"], "nhiem_vu": GHE_KINH_TE["nhiem_vu"],
                        "khi_nao": "tài liệu có cấu phần kinh tế y tế (máy dò: " + _CO_KINH_TE.pattern + ")"},
        "chon_ghe": "năm ghế cố định + một ghế chuyên thiết kế theo gate_params.G1.design (bí danh: "
                    + ", ".join(f"{a}→{b}" for a, b in THIET_KE_BI_DANH.items())
                    + "); thiết kế không xác định ⇒ không có ghế chuyên thiết kế, biên bản ghi rõ",
        "loai_tai_lieu": {k: {"ten": v["ten"], "tep_mac_dinh": v["mau_tep"], "phieu": dict(v["phieu"]),
                              "chu_y": v["chu_y"], "vong_kin": v["vong_kin"]} for k, v in LOAI_TAI_LIEU.items()},
        "chuan_theo_loai": {"de_cuong": "K17 theo thiết kế (SPIRIT 2025, STROBE, STARD 2015, TRIPOD+AI, PRISMA-P, "
                                        "COREQ/SRQR) + Việt Nam",
                            "sap": "Gamble và cs. 2017 (PMID 29260229) + ICH E9(R1) + SAMPL + chuẩn báo cáo của thiết "
                                   "kế; máy chưa đo theo mục Gamble",
                            "ban_thao": "K18 chế độ bản thảo theo thiết kế (CONSORT 2025, STROBE, STARD, TRIPOD+AI, "
                                        "PRISMA 2020, SRQR/COREQ) + ICMJE",
                            "bao_cao": "như bản thảo (K18, có số liệu) + Phiếu nhận xét mục 3 «Kết quả»",
                            "kinh_te": "CHEERS 2022 thêm vào danh mục khi có cấu phần kinh tế; máy chưa đo theo mục"},
        "doc_lap": "mỗi thành viên một yêu cầu riêng, không thấy điểm/nhận xét của người khác",
        "chu_tich": "chỉ giữ, hạ mức (không nâng) hoặc loại kèm lý do; không thêm nhận xét, không sửa điểm, không "
                    "tuyên kết luận; chủ tịch hỏng ⇒ giữ mọi nhận xét đã xác minh",
        "thu_ky": "máy tất định: trung vị, độ lệch, kết luận theo luật, biên bản",
        "tieu_chi": dict(MUC_PHIEU), "moc_diem": MOC_DIEM, "muc_do": list(MUC_DO),
        "xac_minh": {"trich_nguyen_van_cua_so_dong": CUA_SO_DONG, "pii": "loại nhận xét có chuỗi giống số điện thoại",
                     "chuan_ngoai_danh_muc": "bỏ nhãn chuẩn, giữ nhận xét, cảnh báo", "chuan_chung": list(CHUAN_CHUNG),
                     "diem": "số nguyên 1–5 (nhận chuỗi một chữ số); điểm ≤ 2 phải có nhận xét nặng đã xác minh"},
        "tuc_so": "quá bán số ghế của phiên: 5 ghế ⇒ 3; 6 hoặc 7 ghế ⇒ 4",
        "ket_luan": " ".join((ket_luan_tat_dinh.__doc__ or "").split()),
        "vong_kin": {"so_vong_toi_da": SO_VONG_TOI_DA, "tran_ky_tu_thay": TRAN_KY_TU_THAY,
                     "rao_thay_the": ["đoạn cũ xuất hiện đúng 1 lần trong văn bản (số dòng chỉ để tham chiếu)",
                                      "không trích dẫn mới", "không con số mới",
                                      "không ô [CẦN]/dấu vết máy", "không PII"],
                     "rao_van_ban": ["K17 không thêm mục thiếu", "K1–K17 không tăng lỗi theo mã",
                                     "nhất quán xuyên cổng không tăng lệch", "xấu đi ⇒ hoàn nguyên .md + Word",
                                     "luôn sao lưu bản cũ"]},
        "tham_tra": {"vong": "từ vòng 2: không thẩm định lại từ đầu",
                     "pham_vi": "mỗi thành viên thẩm tra ĐÚNG các yêu cầu nghiêm trọng/cần sửa mình đã nêu",
                     "ket_qua": ["da_giai_quyet — phải trích nguyên văn đoạn đáp ứng (máy kiểm, không có ⇒ chưa giải "
                                 "quyết)", "chua_giai_quyet — nêu còn thiếu gì",
                                 "can_du_kien — chỉ khi biên tập viên đã khai vượt thẩm quyền (máy kiểm)"],
                     "thieu_phan_quyet": "coi là chưa giải quyết",
                     "phan_hoi_hong": "phản hồi của một thành viên không đọc được (JSON hỏng/cắt cụt) là lỗi KỸ THUẬT, "
                                      "không phải phán quyết ⇒ nộp lại riêng thành viên đó tối đa 2 lần; vẫn hỏng ⇒ "
                                      "mọi yêu cầu của thành viên đó chưa giải quyết (ghi rõ lý do)",
                     "phan_hoi_bien_tap": "biên tập viên nhận kèm mỗi yêu cầu: lý do người thẩm tra coi là chưa giải "
                                          "quyết và lý do rào liêm chính/chuẩn đã loại bản sửa trước",
                     "loi_moi": "chỉ trong khoảng dòng vừa sửa ±3 (máy kiểm); ngoài phạm vi ⇒ loại",
                     "ket_luan": "Thông qua khi không còn yêu cầu chưa giải quyết và không lỗi mới nghiêm trọng/cần "
                                 "sửa; còn yêu cầu cần dữ kiện ⇒ «Thông qua phần thuộc thẩm quyền… còn dữ kiện» kèm "
                                 "danh sách; còn chưa giải quyết ⇒ chỉnh sửa tiếp (tối đa SO_VONG_TOI_DA vòng)",
                     "cong_don": "yêu cầu «cần dữ kiện» cộng dồn qua các vòng — không rơi khỏi kết luận cuối"},
        "hieu_chuan": {"loi_cai": {"de_cuong": [[m, mo] for m, mo, *_ in LOI_CAI],
                                   "sap": [[m, mo] for m, mo, *_ in LOI_CAI_SAP],
                                   "ban_thao": [[m, mo] for m, mo, *_ in LOI_CAI_BAN_THAO],
                                   "bao_cao": [[m, mo] for m, mo, *_ in LOI_CAI_BAO_CAO]},
                       "loi_dac_thu_thiet_ke": {k: [v[0], v[1]] for k, v in LOI_CAI_THIET_KE.items()},
                       "ghep": "một–một trong ±3 dòng", "do_nhay_toi_thieu": round(DO_NHAY_TOI_THIEU, 4),
                       "so_loi_cai_toi_thieu": SO_LOI_CAI_TOI_THIEU,
                       "dac_thu": "đề cương có thiết kế xác định: phải bắt được lỗi đặc thù thiết kế",
                       "dieu_kien": "theo TỪNG đề tài và TỪNG loại tài liệu: kết luận chỉ có hiệu lực (và vòng kín chỉ "
                                    "chạy) khi độ nhạy đạt, lỗi đặc thù được bắt, VÀ đo báo nhầm hợp lệ đạt — cùng "
                                    "SHA"},
        "do_bao_nham": {"trong_tai": TRONG_TAI_MODEL + " — khác model hội đồng, ngữ cảnh mới, không biết ai nêu",
                        "doi_chung_duong": "nhận xét đã ghép đúng lỗi cài ⇒ phải phán «dung»",
                        "doi_chung_am": f"tối đa {SO_DOI_CHUNG_AM} nhận xét SAI do máy dựng («không trình bày X» khi "
                                        "đề mục X có ≥ 2 dòng nội dung) ⇒ phải phán «sai»",
                        "chu_de_doi_chung": {k: [c for c, _ in v] for k, v in CHU_DE_DOI_CHUNG.items()},
                        "trong_tai_hop_le": f"≥ 4 đối chứng và phán đúng ≥ {TRONG_TAI_KIEM_SOAT_TOI_THIEU}",
                        "sai_phai_chung_minh": "«sai — tài liệu đã đáp ứng» phải trích nguyên văn ±3 dòng; «sai — "
                                               "chuẩn không đòi» phải nêu lý do; không thì thành «khong_ro»",
                        "do_chinh_xac_toi_thieu": DO_CHINH_XAC_TOI_THIEU, "khong_ro_toi_da": KHONG_RO_TOI_DA,
                        "khoang_tin_cay": "Wilson 95%",
                        "ghi_chu": "ngưỡng độ chính xác là ngưỡng VẬN HÀNH của hệ, không phải chuẩn quốc tế"},
        "mo_hinh": {"model": model, "effort": EFFORT, "thinking": "adaptive", "batch_api": True,
                    "cache": "tiền tố đề cương + hồ sơ kiểm máy dùng chung"},
        "trung_thuc": ["lưu nguyên văn mọi trả lời của model", "liệt kê mọi nhận xét bị loại kèm lý do",
                       "không đổi quy chế giữa phiên", "biên bản gắn SHA tài liệu và SHA quy chế",
                       "chi phí thật ghi sổ theo id batch"],
        "loi_nhan": {"dau_tien_to": {lo: khoi_chung("<MA>", "<TEP>", "", {}, lo) for lo in LOAI_TAI_LIEU},
                     "thanh_vien": {lo: {t["ma"] + (f":{k}" if k else ""): loi_nhan_thanh_vien(t, lo)
                                         for k, t in [("", x) for x in THANH_VIEN]
                                         + [(k, {"ma": "uv_ctk", "trong_tam": ("2", "3"), **g})
                                            for k, g in GHE_THIET_KE.items()] + [("", GHE_KINH_TE)]}
                                    for lo in LOAI_TAI_LIEU},
                     "chu_tich": loi_nhan_chu_tich([], {}, 6), "bien_tap": loi_nhan_bien_tap([]),
                     "tham_tra": loi_nhan_tham_tra(THANH_VIEN[0], [], []),
                     "trong_tai": {lo: loi_nhan_trong_tai([], lo) for lo in LOAI_TAI_LIEU},
                     "agent_tham_dinh": loi_nhan_agent_tham_dinh("<agent>", [], "<TEP>", "de_cuong", "<MA>", "<TL>"),
                     "agent_bien_tap": loi_nhan_agent_bien_tap("<agent>", [], "<TEP>", "de_cuong", "<MA>", "<TL>"),
                     "agent_tham_tra": loi_nhan_agent_tham_tra("<agent>", THANH_VIEN[0], [], [], "<TEP>", "<MA>",
                                                               "<TL>"),
                     "agent_dau_ra": loi_nhan_tham_dinh_dau_ra("<TEP>", "<BB>", "de_cuong", "<MA>", "<TL>")},
    }


def _sha_tep(p: Path) -> Optional[str]:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def sha_ke_hoach(model: str = MODEL_MAC_DINH) -> str:
    return hashlib.sha256(json.dumps(ke_hoach(model), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def van_ban_quy_che(model: str = MODEL_MAC_DINH) -> str:
    """Văn bản quy chế (Markdown) sinh từ ĐÚNG dữ liệu khoá — test buộc tệp trong repo khớp SHA."""
    k = ke_hoach(model)
    d = [f"# Quy chế Hội đồng Khoa học máy cấp đề tài — {k['phien_ban']}", "",
         f"- Khoá ngày: {k['ngay_khoa']} · SHA-256 quy chế: `{sha_ke_hoach(model)}`",
         f"- Mục đích: {k['muc_dich']}", f"- Công cụ: `{CONG_CU}` (văn bản này sinh bằng lệnh `ke-hoach --ghi`).", "",
         "## 1. Thành phần (chấm độc lập)", ""]
    d += [f"- **{t['vai']}** — mục trọng tâm {', '.join(t['trong_tam'])}: {t['nhiem_vu']}" for t in k["thanh_phan"]]
    d += [f"- Độc lập: {k['doc_lap']}.", f"- Chủ tịch: {k['chu_tich']}.", f"- Thư ký: {k['thu_ky']}.", "",
          "## 1b. Ghế chuyên thiết kế và ghế kinh tế y tế", "", f"- Cách chọn: {k['chon_ghe']}.", ""]
    d += [f"- `{tk}` — **{g['vai']}**: {g['nhiem_vu']}" for tk, g in k["ghe_thiet_ke"].items()]
    d += [f"- **{k['ghe_kinh_te']['vai']}** (khi {k['ghe_kinh_te']['khi_nao']}): {k['ghe_kinh_te']['nhiem_vu']}", "",
          "## 2. Tiêu chí (Phiếu nhận xét, Phụ lục 2) và mốc điểm", ""]
    d += [f"{so}. {ten}" for so, ten in k["tieu_chi"].items()] + ["", "```", k["moc_diem"], "```", "",
                                                                 "## 2b. Loại tài liệu", ""]
    for lo, v in k["loai_tai_lieu"].items():
        d += [f"### {v['ten']} (`--loai {lo}`, tệp `{v['tep_mac_dinh']}`, vòng kín: "
              f"{'có' if v['vong_kin'] else 'không'})", ""]
        d += [f"{so}. {ten}" for so, ten in v["phieu"].items()]
        d += ([f"- Lưu ý: {v['chu_y']}"] if v["chu_y"] else []) + [f"- Chuẩn: {k['chuan_theo_loai'][lo]}.", ""]
    d += [f"- Kinh tế y tế: {k['chuan_theo_loai']['kinh_te']}.", "", "## 3. Xác minh nhận xét (máy)", ""]
    d += [f"- {a}: {b}" for a, b in k["xac_minh"].items() if a != "chuan_chung"]
    d += [f"- Chuẩn chung được dẫn: {', '.join(k['xac_minh']['chuan_chung'])}; cộng chuẩn báo cáo theo thiết kế (K17).",
          "", "## 4. Túc số và kết luận", "", f"- Túc số: {k['tuc_so']} bản chấm hợp lệ.", f"- {k['ket_luan']}", "",
          "## 5. Vòng kín: chỉnh sửa theo hội đồng", "",
          f"- Tối đa {k['vong_kin']['so_vong_toi_da']} vòng; mỗi đoạn thay ≤ {k['vong_kin']['tran_ky_tu_thay']} ký tự.",
          "- Rào từng thay thế: " + "; ".join(k["vong_kin"]["rao_thay_the"]) + ".",
          "- Rào toàn văn bản: " + "; ".join(k["vong_kin"]["rao_van_ban"]) + ".", "",
          "## 6. Hiệu chuẩn (điều kiện tiên quyết)", ""]
    for lo, ds in k["hieu_chuan"]["loi_cai"].items():
        d += [f"- Lỗi cài ({lo}): " + "; ".join(f"{m} — {mo}" for m, mo in ds) + "."]
    d += ["- Lỗi đặc thù thiết kế (đề cương): " + "; ".join(f"`{tk}` {v[0]} — {v[1]}" for tk, v in
                                                         k["hieu_chuan"]["loi_dac_thu_thiet_ke"].items()) + "."]
    d += [f"- Ghép {k['hieu_chuan']['ghep']}; độ nhạy tối thiểu {k['hieu_chuan']['do_nhay_toi_thieu']} mỗi bản, trên "
          f"≥ {k['hieu_chuan']['so_loi_cai_toi_thieu']} lỗi cài; {k['hieu_chuan']['dac_thu']}.",
          f"- {k['hieu_chuan']['dieu_kien']}.", "", "## 6a. Đo báo nhầm (trọng tài độc lập)", ""]
    d += [f"- {a}: {b}" for a, b in k["do_bao_nham"].items()]
    d += ["", "## 6b. Thẩm tra chỉnh sửa (từ vòng 2)", ""]
    d_40 = ["", "## 0. Phân chia thế mạnh (QC-HDKH-4.0)", ""] + [f"- {x}" for x in k["phan_chia_the_manh"]]
    d_40 += ["", "## 0b. Doctrine agent theo ghế (bản chụp khoá)", "",
             f"- Tệp `{k['doctrine']['tep']}`, SHA {k['doctrine']['sha_ban_chup']}; tối đa "
             f"{k['doctrine']['tran_ky_tu']} ký tự mỗi agent.",
             "- Gắn ghế: " + "; ".join(f"{a} ← {', '.join(b)}" for a, b in k["doctrine"]["gan_ghe"].items()),
             "- Ghế chuyên thiết kế: " + "; ".join(f"{a} ← {', '.join(b)}" for a, b in
                                                    k["doctrine"]["gan_thiet_ke"].items()),
             "", "## 0c. Giao việc cho agent Claude Code", ""]
    d_40 += [f"- {a}: {b}" for a, b in k["ket_hop"].items()]
    d_40 += ["", "## 0d. Rào nội dung đã khoá", "", f"- {k['rao_khoa']['luat']}.",
             f"- Luôn khoá (đề mục): `{k['rao_khoa']['luon_khoa']}`",
             f"- Khoá khi SAP đã chốt (G4 đạt hoặc sẵn sàng ký): `{k['rao_khoa']['khoa_khi_sap_da_khoa']}`",
             f"- Không khoá khi đề mục gần nhất là: `{k['rao_khoa']['mo_khoa']}`",
             f"- Dòng khai báo bị khoá: `{k['rao_khoa']['dong_khoa']}`"]
    d[6:6] = d_40
    d += [f"- {a}: {'; '.join(b) if isinstance(b, list) else b}" for a, b in k["tham_tra"].items()]
    d += ["", "## 7. Mô hình", ""]
    d += [f"- {a}: {b}" for a, b in k["mo_hinh"].items()]
    d += ["", "## 8. Trung thực", ""] + [f"- {x}." for x in k["trung_thuc"]]
    d += ["", "## 9. Lịch sử phiên bản", ""] + [f"- {x}" for x in k["lich_su"]]
    d += ["", "Nguyên văn mọi lời dặn gửi hội đồng nằm trong mã và được tính vào SHA ở trên — sửa một chữ là đổi "
          "quy chế.",
          "", "Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật. Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(d)


def hieu_luc_hieu_chuan(out_dir: Path, model: str = MODEL_MAC_DINH, loai: str = "de_cuong",
                        ket_hop: bool = False) -> Tuple[bool, str]:
    """Hội đồng đã hiệu chuẩn đạt DƯỚI quy chế hiện hành cho đề tài + loại tài liệu này chưa? Cần CẢ: độ nhạy ≥ ngưỡng
    trên ≥ 5 lỗi cài, bắt lỗi đặc thù thiết kế (nếu có), và đo báo nhầm hợp lệ đạt ngưỡng (không đo được ⇒ chưa)."""
    hc = thu_muc_hd(out_dir) / "hieu_chuan" / loai
    kq = _doc_st(hc / "ket_qua.json")
    if not kq:
        return False, "chưa hiệu chuẩn"
    if kq.get("sha_quy_che") != sha_ke_hoach(model):
        return False, "hiệu chuẩn dưới quy chế khác (SHA không khớp) — hiệu chuẩn lại"
    if int(kq.get("so_loi_cai") or 0) < SO_LOI_CAI_TOI_THIEU:
        return False, f"chỉ cài được {kq.get('so_loi_cai')} lỗi (< {SO_LOI_CAI_TOI_THIEU}) — hiệu chuẩn không hợp lệ"
    if not isinstance(kq.get("do_nhay"), (int, float)) or kq["do_nhay"] < DO_NHAY_TOI_THIEU:
        return False, f"độ nhạy {kq.get('do_nhay')} < ngưỡng {round(DO_NHAY_TOI_THIEU, 3)}"
    if kq.get("bat_dac_thu") is False:
        return False, "không bắt được lỗi đặc thù thiết kế"
    if ket_hop and not kq.get("ket_hop"):
        return False, "hiệu chuẩn chưa chạy ở chế độ KẾT HỢP (agent thẩm định nhận xét) — hiệu chuẩn lại với --ket-hop"
    bn = _doc_st(hc / "bao_nham.json")
    if not bn or bn.get("sha_quy_che") != sha_ke_hoach(model):
        return False, f"độ nhạy {kq['bat']}/{kq['so_loi_cai']} đạt nhưng CHƯA đo báo nhầm dưới quy chế này"
    if not bn.get("dat"):
        return False, f"đo báo nhầm chưa đạt: {bn.get('ly_do')}"
    return True, (f"độ nhạy {kq['bat']}/{kq['so_loi_cai']}; độ chính xác nhận xét {bn.get('do_chinh_xac')} (trọng tài "
                  f"{bn.get('model_trong_tai')}, đối chứng {bn.get('doi_chung_dung')}/{bn.get('so_doi_chung')}) dưới "
                  f"{PHIEN_BAN_QUY_CHE}")


# ── văn bản & hồ sơ kiểm máy ─────────────────────────────────────────────────────────────────────────────────────────
def tep_mac_dinh(study: str, goc: Path = REPO, loai: str = "de_cuong") -> Path:
    return goc / "exports" / study / LOAI_TAI_LIEU[loai]["mau_tep"].format(s=study)


def danh_so_dong(van: str) -> str:
    return "\n".join(f"{i}| {d}" for i, d in enumerate(van.splitlines(), 1))


def _sha(van: str) -> str:
    return hashlib.sha256(van.encode("utf-8")).hexdigest()


def _thiet_ke(out_dir: Path) -> str:
    try:
        meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
        return str(((meta.get("gate_params") or {}).get("G1") or {}).get("design") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""


def ho_so_kiem_may(study: str, out_dir: Path, van: str, la_ban_chinh: bool, loai: str = "de_cuong") -> Dict[str, Any]:
    """Kết quả các bộ kiểm TẤT ĐỊNH phát kèm cho hội đồng. Bộ nào lỗi ⇒ ghi «không đo được», không bao giờ ghi «đạt»."""
    ra: Dict[str, Any] = {"thiet_ke": _thiet_ke(out_dir), "loai_tai_lieu": LOAI_TAI_LIEU[loai]["ten"],
                          "bang_chung_he": bang_chung_he(study, out_dir)}
    if loai == "bao_cao":
        ra["cau_truc_bao_cao"] = kiem_cau_truc_bao_cao(van)
    if loai != "de_cuong":
        ra.update(_ho_so_ngoai_de_cuong(study, out_dir, van, la_ban_chinh, loai, ra["thiet_ke"]))
        if _CO_KINH_TE.search(van or ""):
            ra["chuan_ap_dung"] = list(ra.get("chuan_ap_dung") or []) + ["CHEERS 2022"]
            ra["cheers_2022"] = "có cấu phần kinh tế y tế — máy CHƯA đo theo từng mục CHEERS 2022"
        return ra
    try:
        import kiem_chuan_de_cuong_theo_muc as K17  # noqa: PLC0415

        dc = K17.doi_chieu(van, ra["thiet_ke"])
        ra["chuan_ap_dung"] = [c for c, _ in dc["chuan"]]
        thieu = [r for r in dc["ket_qua"] if r.trang_thai in ("thieu", "canh_bao")]
        ra["k17"] = {"dat": sum(1 for r in dc["ket_qua"] if r.trang_thai == "dat"), "thieu": len(thieu),
                     "muc_thieu": [f"{r.chuan} {r.ma} — {r.chu_de}" for r in thieu][:40],
                     "chua_do": [f"{c}: {ly}" for c, ly in dc["chua_do"]]}
    except Exception as exc:  # noqa: BLE001
        ra["chuan_ap_dung"] = []
        ra["k17"] = f"không đo được ({type(exc).__name__})"
    if la_ban_chinh:
        try:
            import kiem_de_cuong_nop_hoi_dong as KDC  # noqa: PLC0415

            ra["k1_k17"] = KDC.kiem(out_dir, study)[:40]
        except Exception as exc:  # noqa: BLE001
            ra["k1_k17"] = f"không đo được ({type(exc).__name__})"
        try:
            import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

            kq = NQ.doi_chieu(out_dir, study)
            ra["nhat_quan"] = {"tong": kq.get("tong"),
                               "can_luu_y": [{"ten": x.get("ten"), "muc": x.get("muc"), "ghi_chu": x.get("ghi_chu")}
                                             for x in kq.get("thong_so") or [] if x.get("muc") != "khop"]}
        except Exception as exc:  # noqa: BLE001
            ra["nhat_quan"] = f"không đo được ({type(exc).__name__})"
    else:
        ra["k1_k17"] = "không chạy (tài liệu không phải bản đề cương nộp chính thức của đề tài)"
    if _CO_KINH_TE.search(van or ""):
        ra["chuan_ap_dung"] = list(ra.get("chuan_ap_dung") or []) + ["CHEERS 2022"]
        ra["cheers_2022"] = "có cấu phần kinh tế y tế — máy CHƯA đo theo từng mục CHEERS 2022"
    return ra


def _ho_so_ngoai_de_cuong(study: str, out_dir: Path, van: str, la_ban_chinh: bool, loai: str,
                          thiet_ke: str) -> Dict[str, Any]:
    """SAP: chuẩn nội dung SAP + chuẩn báo cáo của thiết kế (máy CHƯA đo theo mục Gamble 2017) + nhất quán xuyên cổng.
    Bản thảo/báo cáo: chuẩn báo cáo theo mục của thiết kế (K18, chế độ bản thảo)."""
    ra: Dict[str, Any] = {}
    try:
        import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: PLC0415

        dc = KCM.doi_chieu(van, thiet_ke, che_do="ban_thao", co_so_lieu=True if loai == "bao_cao" else None)
        chuan = [c for c, _ in dc["chuan"]]
        if loai == "sap":
            ra["chuan_ap_dung"] = ["Gamble 2017 (nội dung SAP, PMID 29260229)", "ICH E9(R1)", "SAMPL"] + chuan
            ra["kiem_muc"] = "SAP: máy CHƯA đo theo từng mục Gamble 2017 — hội đồng tự đối chiếu"
        else:
            ra["chuan_ap_dung"] = chuan
            thieu = [r for r in dc["ket_qua"] if r.trang_thai in ("thieu", "canh_bao")]
            ra["k18"] = {"dat": sum(1 for r in dc["ket_qua"] if r.trang_thai == "dat"), "thieu": len(thieu),
                         "muc_thieu": [f"{r.chuan} {r.ma} — {r.chu_de}" for r in thieu][:40],
                         "cau_truc": list(dc.get("cau_truc") or [])[:10],
                         "chua_do": [f"{c}: {ly}" for c, ly in dc.get("chua_do") or []]}
    except Exception as exc:  # noqa: BLE001
        ra["chuan_ap_dung"] = []
        ra["kiem_muc"] = f"không đo được ({type(exc).__name__})"
    if la_ban_chinh and loai == "sap":
        try:
            import nhat_quan_xuyen_cong as NQ  # noqa: PLC0415

            kq = NQ.doi_chieu(out_dir, study)
            ra["nhat_quan"] = {"tong": kq.get("tong"),
                               "can_luu_y": [{"ten": x.get("ten"), "muc": x.get("muc"), "ghi_chu": x.get("ghi_chu")}
                                             for x in kq.get("thong_so") or [] if x.get("muc") != "khop"]}
        except Exception as exc:  # noqa: BLE001
            ra["nhat_quan"] = f"không đo được ({type(exc).__name__})"
    return ra


def ten_cho_hoi_dong(tep: str) -> str:
    """Tên tài liệu ghi trong lời gửi hội đồng. Bản cài lỗi của lượt hiệu chuẩn (thư mục ``hieu_chuan``) mang tên TRUNG
    TÍNH ``TAI_LIEU_<sha8>`` — đo thật 22/11/2026: tên «BAN_CAI_LOI_…» lọt vào khối tài liệu gửi hội đồng ở lượt hiệu
    chuẩn QC-HDKH-4.0 (cùng lỗi làm mù đã vá cho phiếu agent ở ``tep_cho_agent``). Tài liệu thật giữ tên."""
    goc = Path(tep)
    if "hieu_chuan" not in goc.resolve().parts:
        return goc.name
    return f"TAI_LIEU_{hashlib.sha256(goc.read_bytes()).hexdigest()[:8]}{goc.suffix}"


def khoi_chung(study: str, ten_tep: str, van: str, ho_so: Dict[str, Any], loai: str = "de_cuong") -> str:
    """Tiền tố DÙNG CHUNG cho mọi thành viên và chủ tịch (được cache): tài liệu đánh số dòng + hồ sơ kiểm máy."""
    ten = LOAI_TAI_LIEU[loai]["ten"]
    return (f"BẠN LÀ THÀNH VIÊN HỘI ĐỒNG KHOA HỌC xét {ten} của đề tài «{study}» (hội đồng MÁY, tư vấn — không thay "
            f"hội đồng thật). Tài liệu được giao là {ten}, mỗi dòng mang số «n| ».\n\n"
            f"=== TÀI LIỆU: {ten_tep} ===\n{danh_so_dong(van)}\n=== HẾT TÀI LIỆU ===\n\n"
            "=== HỒ SƠ KIỂM MÁY (bộ kiểm tất định; «không đo được» KHÔNG có nghĩa là đạt) ===\n"
            f"{json.dumps(ho_so, ensure_ascii=False, indent=1, default=str)}\n=== HẾT HỒ SƠ ===\n")


def _khuon_tv() -> str:
    return json.dumps({
        "diem": {"1": 4, "2": 3, "3": 4, "4": 3},
        "ly_do_diem": {"1": "một–hai câu, nói căn cứ", "2": "…", "3": "…", "4": "…"},
        "phat_hien": [{"muc_phieu": "1|2|3|4", "muc_do": "nghiem_trong|can_sua|goi_y", "dong": "số dòng",
                       "trich": "NGUYÊN VĂN một đoạn ngắn của dòng đó (chép đúng từng chữ)",
                       "van_de": "điều chưa đạt, nói cụ thể",
                       "chuan": "chuẩn + mục nếu có (vd «STROBE 12d»), không thì «»",
                       "de_xuat": "sửa cụ thể thế nào"}],
        "diem_manh": ["…"], "ket_luan": "thong_qua|thong_qua_co_sua|khong_thong_qua"}, ensure_ascii=False, indent=1)


def loi_nhan_thanh_vien(tv: Dict[str, Any], loai: str = "de_cuong", ban_chup: Optional[Dict[str, Any]] = None) -> str:
    lt = LOAI_TAI_LIEU[loai]
    dt_ = ""
    if tv.get("tac_nhan"):
        dt_ = ("CHUYÊN MÔN CỦA HỆ mà ghế bạn đại diện (doctrine agent — chấm theo các luật này; phần thao tác công cụ "
               "trong đó không áp dụng cho bạn):\n" + khoi_doctrine(tv["tac_nhan"], ban_chup) + "\n\n")
    return (f"VAI CỦA BẠN: {tv['vai']}.\nTRỌNG TÂM: {tv['nhiem_vu']}\n" + dt_
            + "BẰNG CHỨNG CÔNG CỤ CỦA HỆ ở mục «bang_chung_he» của hồ sơ kiểm máy (chấm sống từng cổng, cỡ mẫu G3, "
            "biên nhận trích dẫn A12) là số đo — dùng làm căn cứ, không đếm lại.\n"
            f"LOẠI TÀI LIỆU: {lt['ten']}." + (f" Lưu ý riêng: {lt['chu_y']}" if lt["chu_y"] else "") + "\n\n"
            "Chấm ĐỘC LẬP — bạn không biết ý kiến thành viên khác. Chấm cả bốn mục của Phiếu nhận xét, nhưng nhận xét "
            f"chuyên sâu ở mục {', '.join(tv['trong_tam'])}:\n"
            + "\n".join(f"  {k}. {v}" for k, v in lt["phieu"].items())
            + f"\nMốc điểm (dùng ĐÚNG mốc):\n{MOC_DIEM}\n\n"
            "LUẬT BẮT BUỘC:\n"
            "1. Mỗi nhận xét phải có «dong» và «trich» chép NGUYÊN VĂN từ đúng dòng đó — máy sẽ đối chiếu, trích không "
            "khớp thì nhận xét bị loại. Nhận xét về điều THIẾU: trích dòng nơi lẽ ra phải có (tiêu đề mục).\n"
            "2. Điểm 1–2 ở mục nào phải có ít nhất một nhận xét «nghiem_trong» hoặc «can_sua» ở mục đó; đã có "
            "«can_sua» thì không chấm 5.\n"
            "3. Không bịa số liệu, nguồn, mục chuẩn; không đòi điều chuẩn không đòi. Không đánh giá lại lựa chọn thuộc "
            "thẩm quyền chủ nhiệm khi lựa chọn đó có lý do ghi trong tài liệu — chỉ nêu khi lý do sai hoặc thiếu.\n"
            "4. Không nhắc lại lỗi mà hồ sơ kiểm máy đã liệt kê trừ khi bạn có thêm điều máy không thấy.\n"
            "5. Không ghi thông tin định danh cá nhân.\n"
            "Trả về DUY NHẤT một đối tượng JSON theo khuôn:\n" + _khuon_tv())


def loi_nhan_chu_tich(ds: Sequence[Dict[str, Any]], bang_diem: Dict[str, Dict[str, int]], so_tv: int = 5) -> str:
    gon = [{k: f[k] for k in ("id", "thanh_vien", "muc_phieu", "muc_do", "dong", "trich", "van_de", "chuan", "de_xuat")}
           for f in ds]
    return (f"VAI CỦA BẠN: CHỦ TỊCH HỘI ĐỒNG. {so_tv} thành viên đã chấm độc lập; dưới đây là các nhận xét ĐÃ được máy "
            "xác minh trích nguyên văn, và bảng điểm.\nNHIỆM VỤ:\n"
            "1. Với TỪNG nhận xét: «giu», «ha_muc» (chỉ được HẠ: nghiem_trong→can_sua→goi_y) hoặc «loai» (báo động giả "
            "— tài liệu thật ra đã đáp ứng ở chỗ khác: nêu số dòng đó; hoặc đòi điều chuẩn không đòi). Mỗi phán quyết "
            "kèm lý do có căn cứ trong tài liệu.\n"
            "2. Gộp các nhận xét trùng ý (cùng một vấn đề) thành nhóm.\n"
            "3. Viết «nhan_xet_chung» (3–6 câu, khách quan) và «yeu_cau_chinh_sua» theo thứ tự ưu tiên.\n"
            "Bạn KHÔNG thêm nhận xét mới, KHÔNG nâng mức, KHÔNG sửa điểm, KHÔNG tuyên kết luận (máy tính theo luật).\n"
            f"NHẬN XÉT:\n{json.dumps(gon, ensure_ascii=False, indent=1)}\n"
            f"BẢNG ĐIỂM:\n{json.dumps(bang_diem, ensure_ascii=False)}\n"
            "Trả về DUY NHẤT JSON: " + json.dumps({
                "phan_quyet": [{"id": "F01", "quyet": "giu|ha_muc|loai", "muc_do_moi": "chỉ khi ha_muc",
                                "ly_do": "…"}],
                "gop": [["F01", "F07"]], "nhan_xet_chung": "…", "yeu_cau_chinh_sua": ["…"]}, ensure_ascii=False))


# ── yêu cầu API ─────────────────────────────────────────────────────────────────────────────────────────────────────
def tham_so_yeu_cau(chung: str, loi_nhan: str, model: str, max_tokens: int) -> Dict[str, Any]:
    p = API.tham_so(loi_nhan, he_thong=chung, model=model, max_tokens=max_tokens, effort=EFFORT, cache_he_thong=True)
    if p["model"] in API.MODEL_HIEN_HANH:
        p["thinking"] = {"type": "adaptive"}
    return p


def yeu_cau_thanh_vien(chung: str, model: str, sha8: str, ds_tv: Optional[Sequence[Dict[str, Any]]] = None,
                       loai: str = "de_cuong") -> List[Tuple[str, Dict[str, Any]]]:
    return [(f"{tv['ma']}_{sha8}", tham_so_yeu_cau(chung, loi_nhan_thanh_vien(tv, loai), model, MAX_TOKENS_TV))
            for tv in (ds_tv or THANH_VIEN)]


# ── xác minh (máy) ──────────────────────────────────────────────────────────────────────────────────────────────────
_SO_DIEN_THOAI = re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)")


def _trong_cua_so(trich: str, dong: int, cac_dong: Sequence[str]) -> bool:
    if not (1 <= dong <= len(cac_dong)):
        return False
    a, b = max(0, dong - 1 - CUA_SO_DONG), min(len(cac_dong), dong + CUA_SO_DONG)
    return API.co_nguyen_van(trich, "\n".join(cac_dong[a:b]))


def _chuan_hop_le(chuan: str, chuan_ap_dung: Sequence[str]) -> bool:
    c = (chuan or "").strip()
    if not c:
        return True
    ten = [x.split()[0] for x in chuan_ap_dung if x and x != "(không xác định)"] + list(CHUAN_CHUNG)
    return any(t.casefold() in c.casefold() for t in ten)


def xac_minh_thanh_vien(ma: str, dl: Any, van: str, chuan_ap_dung: Sequence[str]) -> Dict[str, Any]:
    """Chuẩn hoá + kiểm một bản chấm. Trả {'diem', 'ly_do_diem', 'dat': [...], 'khong_xac_minh': [...], 'canh_bao'}."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("bản chấm không phải đối tượng JSON")
    cac_dong = van.splitlines()
    diem: Dict[str, int] = {}
    for k in MUC_PHIEU:
        v = (dl.get("diem") or {}).get(k)
        # 22/11/2026 (lượt hiệu chuẩn thật đầu tiên): khuôn cũ ghi «"số nguyên 1–5"» nên model trả điểm dạng CHUỖI "3"
        # ⇒ 9/10 bản chấm bị loại. Nhận chuỗi MỘT chữ số 1–5; mọi dạng khác (0, 6, 4.5, true, rỗng) vẫn hỏng.
        if isinstance(v, str) and v.strip() in {"1", "2", "3", "4", "5"}:
            v = int(v.strip())
        if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 5:
            raise API.KetQuaHong(f"điểm mục {k} không hợp lệ: {v!r}")
        diem[k] = v
    dat, khong, canh_bao = [], [], []
    for f in dl.get("phat_hien") or []:
        if not isinstance(f, dict):
            continue
        g = {"thanh_vien": ma, "muc_phieu": str(f.get("muc_phieu") or "").strip(),
             "muc_do": str(f.get("muc_do") or "").strip(), "trich": str(f.get("trich") or "").strip(),
             "van_de": str(f.get("van_de") or "").strip(), "chuan": str(f.get("chuan") or "").strip(),
             "de_xuat": str(f.get("de_xuat") or "").strip()}
        try:
            g["dong"] = int(f.get("dong"))
        except (TypeError, ValueError):
            g["dong"] = 0
        ly = []
        if g["muc_phieu"] not in MUC_PHIEU:
            ly.append("mục phiếu không hợp lệ")
        if g["muc_do"] not in MUC_DO:
            ly.append("mức độ không hợp lệ")
        if not g["van_de"] or not g["de_xuat"]:
            ly.append("thiếu vấn đề hoặc đề xuất")
        if not _trong_cua_so(g["trich"], g["dong"], cac_dong):
            ly.append("trích không có nguyên văn quanh dòng đã nêu")
        if any(_SO_DIEN_THOAI.search(g[k]) for k in ("van_de", "de_xuat", "trich")):
            ly.append("có chuỗi giống số điện thoại (PII)")
        if not _chuan_hop_le(g["chuan"], chuan_ap_dung):
            g["chuan_goc"], g["chuan"] = g["chuan"], ""
            canh_bao.append(f"{ma}: chuẩn «{g['chuan_goc']}» ngoài danh mục áp dụng — bỏ nhãn chuẩn, giữ nhận xét")
        (khong if ly else dat).append({**g, "ly_do_loai": "; ".join(ly)} if ly else g)
    for k, v in diem.items():
        nang = [x for x in dat if x["muc_phieu"] == k and x["muc_do"] in ("nghiem_trong", "can_sua")]
        if v <= 2 and not nang:
            canh_bao.append(f"{ma}: điểm {v} mục {k} không có nhận xét nghiêm trọng/cần sửa đã xác minh")
        if v == 5 and nang:
            canh_bao.append(f"{ma}: điểm 5 mục {k} trong khi có nhận xét cần sửa")
    kl = str(dl.get("ket_luan") or "").strip()
    return {"diem": diem, "ly_do_diem": dl.get("ly_do_diem") or {}, "dat": dat, "khong_xac_minh": khong,
            "canh_bao": canh_bao, "diem_manh": [str(x) for x in (dl.get("diem_manh") or [])][:8],
            "ket_luan": kl if kl in KET_LUAN else ""}


def ap_phan_quyet(ds: Sequence[Dict[str, Any]], dl: Any) -> Dict[str, Any]:
    """Áp phán quyết của chủ tịch (chỉ hạ/loại, không thêm). Thiếu phán quyết cho một nhận xét ⇒ GIỮ (fail-safe)."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("phán quyết chủ tịch không phải đối tượng JSON")
    theo_id = {f["id"]: dict(f) for f in ds}
    loai, canh_bao = [], []
    for pq in dl.get("phan_quyet") or []:
        if not isinstance(pq, dict) or pq.get("id") not in theo_id:
            canh_bao.append(f"phán quyết trỏ id không có: {pq.get('id') if isinstance(pq, dict) else pq!r}")
            continue
        f, quyet, ly = theo_id[pq["id"]], str(pq.get("quyet") or ""), str(pq.get("ly_do") or "").strip()
        if quyet == "loai":
            if not ly:
                canh_bao.append(f"{f['id']}: loại mà không có lý do — giữ nguyên")
                continue
            loai.append({**f, "ly_do_chu_tich": ly})
            del theo_id[f["id"]]
        elif quyet == "ha_muc":
            moi = str(pq.get("muc_do_moi") or "")
            if moi in MUC_DO and MUC_DO.index(moi) > MUC_DO.index(f["muc_do"]):
                f.update(muc_do_goc=f["muc_do"], muc_do=moi, ly_do_chu_tich=ly)
            else:
                canh_bao.append(f"{f['id']}: «hạ mức» không hợp lệ ({f['muc_do']}→{moi}) — giữ nguyên")
        elif quyet != "giu":
            canh_bao.append(f"{f['id']}: phán quyết lạ «{quyet}» — giữ nguyên")
    nhom = [[i for i in g if i in theo_id] for g in (dl.get("gop") or []) if isinstance(g, list)]
    return {"giu": list(theo_id.values()), "loai": loai, "gop": [g for g in nhom if len(g) > 1],
            "nhan_xet_chung": str(dl.get("nhan_xet_chung") or "").strip(),
            "yeu_cau_chinh_sua": [str(x) for x in (dl.get("yeu_cau_chinh_sua") or [])][:20], "canh_bao": canh_bao}


def _nhom_dai_dien(giu: Sequence[Dict[str, Any]], gop: Sequence[Sequence[str]]) -> List[Dict[str, Any]]:
    """Một vấn đề = một dòng: nhóm gộp lấy nhận xét có mức NẶNG NHẤT làm đại diện."""
    trong_nhom = {i for g in gop for i in g}
    ra = [f for f in giu if f["id"] not in trong_nhom]
    theo_id = {f["id"]: f for f in giu}
    for g in gop:
        cac = [theo_id[i] for i in g if i in theo_id]
        if cac:
            dd = min(cac, key=lambda f: MUC_DO.index(f["muc_do"]))
            ra.append({**dd, "gop_voi": [f["id"] for f in cac if f is not dd]})
    return sorted(ra, key=lambda f: (MUC_DO.index(f["muc_do"]), f["muc_phieu"], f["dong"]))


def ket_luan_tat_dinh(van_de: Sequence[Dict[str, Any]], trung_vi: Dict[str, float]) -> Tuple[str, str]:
    """LUẬT CỐ ĐỊNH của thư ký máy (không phải quy định của bệnh viện — luật nội bộ để kết luận tái lập được):
    - Không thông qua: ≥ 3 vấn đề nghiêm trọng còn giữ, HOẶC trung vị mục 1 hoặc 2 ≤ 2.
    - Thông qua sau khi chỉnh sửa: ≥ 1 vấn đề nghiêm trọng/cần sửa còn giữ, HOẶC trung vị mục nào ≤ 3.
    - Thông qua: còn lại."""
    nt = sum(1 for f in van_de if f["muc_do"] == "nghiem_trong")
    cs = sum(1 for f in van_de if f["muc_do"] == "can_sua")
    if nt >= 3 or min(trung_vi.get("1", 5), trung_vi.get("2", 5)) <= 2:
        return "khong_thong_qua", (f"{nt} vấn đề nghiêm trọng; trung vị mục 1 = {trung_vi.get('1')}, "
                                   f"mục 2 = {trung_vi.get('2')}")
    if nt or cs or min(trung_vi.values()) <= 3:
        return "thong_qua_co_sua", (f"{nt} vấn đề nghiêm trọng, {cs} vấn đề cần sửa; "
                                    f"trung vị thấp nhất {min(trung_vi.values())}")
    return "thong_qua", "không còn vấn đề nghiêm trọng/cần sửa; mọi trung vị ≥ 4"


def tong_hop(st: Dict[str, Any]) -> Dict[str, Any]:
    """Bảng điểm, trung vị, độ lệch, vấn đề còn giữ và kết luận — từ trạng thái đã xong cả hai bước."""
    tv = st["thanh_vien"]
    bang = {ma: kq["diem"] for ma, kq in tv.items() if isinstance(kq, dict) and "diem" in kq}
    trung_vi = {k: statistics.median([b[k] for b in bang.values()]) for k in MUC_PHIEU} if bang else {}
    lech = {k: max(b[k] for b in bang.values()) - min(b[k] for b in bang.values()) for k in MUC_PHIEU} if bang else {}
    ct = st.get("chu_tich") or {}
    van_de = _nhom_dai_dien(ct.get("giu") or [], ct.get("gop") or [])
    kl, ly = ket_luan_tat_dinh(van_de, trung_vi) if trung_vi else ("", "chưa đủ bản chấm")
    return {"bang_diem": bang, "trung_vi": trung_vi, "do_lech": lech, "van_de": van_de, "ket_luan": kl,
            "ly_do_ket_luan": ly,
            "phieu_bau": {ma: kq.get("ket_luan") for ma, kq in tv.items() if isinstance(kq, dict)}}


# ── trạng thái & các bước ───────────────────────────────────────────────────────────────────────────────────────────
def thu_muc_hd(out_dir: Path) -> Path:
    return out_dir / THU_MUC


def tep_trang_thai(out_dir: Path, sha: str) -> Path:
    return thu_muc_hd(out_dir) / f"trang_thai_{sha[:12]}.json"


def _doc_st(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _ghi_json(p: Path, du_lieu: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    tam.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                   newline="\n")
    tam.replace(p)


def khoi_tao(study: str, out_dir: Path, tep: Path, model: str, loai: str = "de_cuong") -> Dict[str, Any]:
    van = tep.read_text(encoding="utf-8")
    la_chinh = tep.resolve() == tep_mac_dinh(study, out_dir.parents[1], loai).resolve()
    ho_so = ho_so_kiem_may(study, out_dir, van, la_chinh, loai)
    return {"schema": SCHEMA, "study": study, "tep": str(tep), "sha": _sha(van), "model": model, "loai": loai,
            "thanh_phan": thanh_phan_hoi_dong(ho_so.get("thiet_ke") or "", van, loai),
            "ho_so": ho_so, "buoc": "thanh_vien", "batch": {}, "thanh_vien": {}, "chu_tich": None,
            "quy_che": {"phien_ban": PHIEN_BAN_QUY_CHE, "sha": sha_ke_hoach(model)},
            "bat_dau": dt.datetime.now().isoformat(timespec="seconds")}


def uoc_tinh(st: Dict[str, Any], van: str) -> Dict[str, Any]:
    chung = khoi_chung(st["study"], ten_cho_hoi_dong(st["tep"]), van, st["ho_so"], st.get("loai", "de_cuong"))
    yc = yeu_cau_thanh_vien(chung, st["model"], st["sha"][:8], _ds_tv(st), st.get("loai", "de_cuong"))
    tok_chung = API.uoc_token(chung)
    tok_tv = [API.uoc_token(p["messages"][0]["content"]) for _, p in yc]
    n = len(yc) + 1  # + chủ tịch
    toi_da = sum(API.uoc_toi_da(p, batch=True) or 0 for _, p in yc) * n / len(yc)
    # điển hình: ghi cache 1 lần (1,25×), đọc cache n−1 lần; ra TOKEN_RA_UOC mỗi yêu cầu
    gia = API.GIA_USD_TRIEU_TOKEN.get(st["model"], API.GIA_USD_TRIEU_TOKEN[API.MODEL_MAC_DINH])
    vao = tok_chung * 1.25 * gia["vao"] + tok_chung * (n - 1) * gia["doc_cache"] + (sum(tok_tv) + 6000) * gia["vao"]
    ra = n * TOKEN_RA_UOC * gia["ra"]
    return {"so_yeu_cau": n, "token_tai_lieu": tok_chung, "usd_dien_hinh": round((vao + ra) / 1e6 * 0.5, 2),
            "usd_toi_da": round(toi_da, 2), "model": st["model"]}


def _chay_buoc(st: Dict[str, Any], van: str, goi_api: bool, client: Any) -> int:
    """Một lượt: nộp hoặc lấy batch của bước hiện tại. Trả mã thoát."""
    loai = st.get("loai", "de_cuong")
    ds_tv = _ds_tv(st)
    chung = khoi_chung(st["study"], ten_cho_hoi_dong(st["tep"]), van, st["ho_so"], loai)
    sha8 = st["sha"][:8]
    if st["buoc"] == "xong":
        print("✅ Hội đồng đã họp xong — chạy «bien-ban» để xem/ghi biên bản.")
        return 0
    bid = st["batch"].get(st["buoc"])
    if not bid:
        if st["buoc"] == "thanh_vien":
            yc = yeu_cau_thanh_vien(chung, st["model"], sha8, ds_tv, loai)
        else:
            ds = [f for kq in st["thanh_vien"].values() if isinstance(kq, dict) for f in kq.get("dat", [])]
            for i, f in enumerate(ds, 1):
                f["id"] = f"F{i:02d}"
            st["ds_xac_minh"] = ds
            bang = {ma: kq["diem"] for ma, kq in st["thanh_vien"].items() if isinstance(kq, dict) and "diem" in kq}
            yc = [(f"ct_{sha8}", tham_so_yeu_cau(chung, loi_nhan_chu_tich(ds, bang, len(ds_tv)), st["model"],
                                                 MAX_TOKENS_CT))]
        if not goi_api:
            print(f"(chạy khô) bước «{st['buoc']}»: {len(yc)} yêu cầu — thêm --goi-api để nộp batch (tính phí).")
            return 0
        st["batch"][st["buoc"]] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        print(f"📨 Đã nộp batch bước «{st['buoc']}»: {st['batch'][st['buoc']]} ({len(yc)} yêu cầu).")
        return 4
    if not goi_api:
        print(f"(chạy khô) batch bước «{st['buoc']}» {bid} đang chờ — thêm --goi-api để lấy kết quả.")
        return 0
    tt = API.trang_thai_batch(bid, client=client)
    if tt["trang_thai"] != "ended":
        print(f"⏳ Batch {bid} đang xử lý ({tt['dang_xu_ly']} yêu cầu) — chạy lại sau.")
        return 4
    ket = API.doc_ket_qua_batch(bid, client=client, nguon=CONG_CU)
    ma_loi = 0
    if st["buoc"] == "thanh_vien":
        for tv in ds_tv:
            cid = f"{tv['ma']}_{sha8}"
            try:
                tho = API.van_ban_ket_qua_batch(ket.get(cid, {"loai": "thieu"}), MAX_TOKENS_TV)
                st.setdefault("tho", {})[tv["ma"]] = tho  # nguyên văn trả lời — kiểm toán/đọc lại không tốn phí
                dl = API.doc_json(tho)
                st["thanh_vien"][tv["ma"]] = xac_minh_thanh_vien(tv["ma"], dl, van, st["ho_so"].get("chuan_ap_dung")
                                                                 or [])
            except API.LoiApi as exc:
                st["thanh_vien"][tv["ma"]] = {"loi": str(exc)[:300]}
                ma_loi = 1
        hop_le = [m for m, kq in st["thanh_vien"].items() if "diem" in kq]
        if len(hop_le) < tuc_so(len(ds_tv)):
            print(f"🔴 Chỉ {len(hop_le)}/{len(ds_tv)} bản chấm hợp lệ — không đủ túc số (≥ {tuc_so(len(ds_tv))}). "
                  "Chạy lại với --lam-lai.")
            return 1
        st["buoc"] = "chu_tich"
    else:
        try:
            dl = API.doc_json(API.van_ban_ket_qua_batch(ket.get(f"ct_{sha8}", {"loai": "thieu"}), MAX_TOKENS_CT))
            st["chu_tich"] = ap_phan_quyet(st.get("ds_xac_minh") or [], dl)
        except API.LoiApi as exc:
            # Chủ tịch hỏng ⇒ GIỮ mọi nhận xét đã xác minh (fail-safe), ghi rõ không có tổng hợp của chủ tịch.
            st["chu_tich"] = {"giu": st.get("ds_xac_minh") or [], "loai": [], "gop": [], "nhan_xet_chung": "",
                              "yeu_cau_chinh_sua": [], "canh_bao": [f"chủ tịch không trả lời hợp lệ: {exc}"[:300]]}
            ma_loi = 1
        st["buoc"] = "tham_dinh_agent" if st.get("ket_hop") else "xong"
    print(f"✅ Xong bước — bước kế tiếp: «{st['buoc']}».")
    return ma_loi


# ── biên bản ────────────────────────────────────────────────────────────────────────────────────────────────────────
def _o_bang(x: Any, toi_da: int = 160) -> str:
    return str(x or "").replace("|", "/").replace("\n", " ")[:toi_da]


def bien_ban_tham_tra_md(st: Dict[str, Any]) -> str:
    """Biên bản một vòng THẨM TRA CHỈNH SỬA (QC-HDKH-2.0)."""
    tt = st.get("tham_tra") or {}
    kl, ly = ket_luan_tham_tra(tham_tra_cong_don(st)) if tt else ("", "chưa thẩm tra")
    ten_tv = {tv["ma"]: tv["vai"] for tv in _ds_tv(st)}
    nhan = {"da_giai_quyet": "✅ Đã giải quyết", "chua_giai_quyet": "🟠 Chưa giải quyết",
            "can_du_kien": "⏳ Cần dữ kiện của người có thẩm quyền"}
    qc = st.get("quy_che") or {}
    d = [f"# Biên bản thẩm tra chỉnh sửa (máy) — {st['study']} · vòng {st.get('vong')}", "",
         f"- Tài liệu: `{Path(st['tep']).name}` (SHA-256 {st['sha'][:16]}…), sửa từ bản "
         f"{str(st.get('ban_truoc'))[:12]}…",
         f"- Quy chế: {qc.get('phien_ban', '—')} (SHA {str(qc.get('sha', '—'))[:16]}…) — khoá trước khi họp.",
         f"- Hiệu chuẩn hội đồng: {st.get('hieu_luc_ly_do', '—')}.",
         "- **Hiệu lực kết luận: " + ("CÓ" if st.get("hieu_luc") else "CHƯA — hội đồng chưa hiệu chuẩn đạt") + "**",
         "- Phạm vi: mỗi thành viên thẩm tra đúng các yêu cầu mình đã nêu; lỗi mới chỉ trong các đoạn vừa sửa ("
         + (", ".join(f"dòng {a}–{b}" for a, b in (st.get("khoang") or [])[:30]) or "không có") + ").", "",
         f"## Kết luận (luật cố định): **{KET_LUAN.get(kl, '—')}**", "", f"Căn cứ: {ly}.", "",
         "## Kết quả thẩm tra từng yêu cầu", "",
         "| Yêu cầu | Mức | Người thẩm tra | Kết quả | Bằng chứng (bản đã sửa) / lý do |", "|---|---|---|---|---|"]
    for loai in ("chua_giai_quyet", "can_du_kien", "da_giai_quyet"):
        for x in tt.get(loai) or []:
            bc = (f"dòng {x.get('dong_moi')}: «{_o_bang(x.get('trich_moi'), 120)}»" if loai == "da_giai_quyet"
                  else _o_bang(x.get("ly_do_tham_tra")))
            d.append(f"| {x['id']} · mục {x.get('muc_phieu')} — {_o_bang(x.get('van_de'), 110)} | {x.get('muc_do')} | "
                     f"{_o_bang(ten_tv.get(x.get('nguoi_tham_tra')), 40)} | {nhan[loai]} | {bc} |")
    if tt.get("loi_moi"):
        d += ["", "## Lỗi mới trong đoạn vừa sửa (đã máy xác minh)", ""]
        d += [f"- {g['id']} · {g['muc_do']} · mục {g['muc_phieu']} · dòng {g['dong']} ({ten_tv.get(g['thanh_vien'])}): "
              f"«{g['trich'][:120]}» — {g['van_de']} → {g['de_xuat']}" for g in tt["loi_moi"]]
    if tt.get("loai"):
        d += ["", "## Lỗi mới bị loại (ngoài phạm vi thẩm tra hoặc không xác minh được)", ""]
        d += [f"- dòng {g.get('dong')} ({ten_tv.get(g.get('thanh_vien'))}): {str(g.get('van_de'))[:160]} — "
              f"{g.get('ly_do_loai')}" for g in tt["loai"]]
    du_kien = list(st.get("can_du_kien_truoc") or []) + list(tt.get("can_du_kien") or [])
    if du_kien:
        d += ["", "## Dữ kiện/quyết định cần người có thẩm quyền (cộng dồn các vòng)", ""]
        d += [f"- {x['id']} (mục {x.get('muc_phieu')}): {_o_bang(x.get('van_de'), 200)} — cần: "
              f"{_o_bang(x.get('ly_do_tham_tra') or x.get('ly_do_bien_tap'), 300)}" for x in du_kien]
    d += ["", "---", "", "Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật, không mở/chặn "
          "cổng, không ký. Kết luận theo luật cố định của quy chế. Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(d)


def bien_ban_md(st: Dict[str, Any]) -> str:
    if st.get("che_do") == "tham_tra":
        return bien_ban_tham_tra_md(st)
    th = tong_hop(st)
    ds_tv = _ds_tv(st)
    ten_tv = {tv["ma"]: tv["vai"] for tv in ds_tv}
    d = [f"# Biên bản Hội đồng Khoa học (máy) — {st['study']} · {LOAI_TAI_LIEU[st.get('loai', 'de_cuong')]['ten']}", "",
         f"- Tài liệu: `{Path(st['tep']).name}` (SHA-256 {st['sha'][:16]}…)",
         f"- Thành phần: {len(ds_tv)} thành viên chấm độc lập ({'; '.join(tv['vai'] for tv in ds_tv)}) + chủ tịch tổng "
         f"hợp; thư ký là máy tất định; túc số {tuc_so(len(ds_tv))}. Model {st['model']} (Batch API, effort {EFFORT}).",
         f"- Bắt đầu: {st.get('bat_dau')} · vòng {st.get('vong', 1)}",
         f"- Quy chế: {(st.get('quy_che') or {}).get('phien_ban', '—')} (SHA "
         f"{str((st.get('quy_che') or {}).get('sha', '—'))[:16]}…) — khoá trước khi họp, không đổi giữa phiên.",
         f"- Hiệu chuẩn hội đồng: {st.get('hieu_luc_ly_do', 'không áp dụng (bản hiệu chuẩn)')}.",
         "- **Hiệu lực kết luận: " + ("CÓ" if st.get("hieu_luc")
                                       else "CHƯA — hội đồng chưa hiệu chuẩn đạt dưới quy chế này") + "**",
         "",
         f"## Kết luận (luật cố định của thư ký máy): **{KET_LUAN.get(th['ket_luan'], '—')}**", "",
         f"Căn cứ: {th['ly_do_ket_luan']}.", "",
         "## Bảng điểm (thang 1–5, Phiếu nhận xét)", "",
         "| Thành viên | " + " | ".join(f"Mục {k}" for k in MUC_PHIEU) + " | Phiếu bầu |",
         "|---|" + "---|" * (len(MUC_PHIEU) + 1)]
    for ma, b in th["bang_diem"].items():
        d.append(f"| {ten_tv.get(ma, ma)} | " + " | ".join(str(b[k]) for k in MUC_PHIEU)
                 + f" | {KET_LUAN.get(th['phieu_bau'].get(ma) or '', '—')} |")
    if th["trung_vi"]:
        d.append("| **Trung vị** | " + " | ".join(str(th["trung_vi"][k]).replace(".", ",") for k in MUC_PHIEU) + " | |")
        d.append("| Độ lệch (cao − thấp) | " + " | ".join(str(th["do_lech"][k]) for k in MUC_PHIEU) + " | |")
    for ma, kq in st["thanh_vien"].items():
        if "loi" in kq:
            d.append(f"\n> {ten_tv.get(ma, ma)}: không có bản chấm hợp lệ ({kq['loi'][:160]}).")
    lech_lon = [k for k, v in th["do_lech"].items() if v >= 2]
    if lech_lon:
        d += ["", f"> Bất đồng lớn (lệch ≥ 2 điểm) ở mục {', '.join(lech_lon)} — xem lý do điểm từng thành viên."]
    ct = st.get("chu_tich") or {}
    d += ["", "## Nhận xét chung của chủ tịch", "", ct.get("nhan_xet_chung") or "(không có)", "",
          "## Tồn tại và yêu cầu chỉnh sửa (mục 5 — nhận xét đã máy xác minh nguyên văn, chủ tịch giữ)", ""]
    nhan = {"nghiem_trong": "🔴 Nghiêm trọng", "can_sua": "🟠 Cần sửa", "goi_y": "🟢 Gợi ý"}
    for f in th["van_de"]:
        d += [f"- **{nhan[f['muc_do']]} · mục {f['muc_phieu']} · dòng {f['dong']}** ({ten_tv.get(f['thanh_vien'])}"
              + (f"; trùng ý {', '.join(f['gop_voi'])}" if f.get("gop_voi") else "") + ")",
              f"  - Trích: «{f['trich']}»", f"  - Vấn đề: {f['van_de']}" + (f" ({f['chuan']})" if f["chuan"] else ""),
              f"  - Đề xuất: {f['de_xuat']}"]
    if ct.get("yeu_cau_chinh_sua"):
        d += ["", "**Thứ tự chỉnh sửa (chủ tịch):**", ""]
        d += [f"{i}. {x}" for i, x in enumerate(ct["yeu_cau_chinh_sua"], 1)]
    if ct.get("loai"):
        d += ["", "## Nhận xét chủ tịch loại (báo động giả) — giữ để minh bạch", ""]
        d += [f"- {f['id']} dòng {f['dong']} ({ten_tv.get(f['thanh_vien'])}): {f['van_de']} — lý do loại: "
              f"{f['ly_do_chu_tich']}" for f in ct["loai"]]
    khong = [f for kq in st["thanh_vien"].values() for f in (kq.get("khong_xac_minh") or [])]
    if khong:
        d += ["", "## Nhận xét máy KHÔNG xác minh được (không tính vào kết luận)", ""]
        d += [f"- {ten_tv.get(f['thanh_vien'])} dòng {f.get('dong')}: {f.get('van_de')[:200]} — {f['ly_do_loai']}"
              for f in khong]
    cb = [x for kq in st["thanh_vien"].values() for x in (kq.get("canh_bao") or [])] + (ct.get("canh_bao") or [])
    if cb:
        d += ["", "## Cảnh báo của thư ký máy", ""] + [f"- {x}" for x in cb]
    manh = [(ma, x) for ma, kq in st["thanh_vien"].items() for x in (kq.get("diem_manh") or [])]
    if manh:
        d += ["", "## Điểm mạnh thành viên ghi nhận", ""] + [f"- {x} ({ten_tv.get(ma)})" for ma, x in manh]
    d += ["", "---", "", "Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học/Hội đồng Đạo đức thật, không mở/chặn "
          "cổng, không ký. Nhận xét đã xác minh nguyên văn là căn cứ để nhóm nghiên cứu/agent sửa; kết luận là luật "
          "nội bộ tái lập được. Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(d)


def ghi_bien_ban(st: Dict[str, Any], out_dir: Path) -> Path:
    """Ghi biên bản .md + .json của MỘT lần họp (tên gắn ngày + SHA tài liệu)."""
    ngay = dt.date.today().strftime("%Y%m%d")
    p_md = thu_muc_hd(out_dir) / f"BIEN_BAN_HDKH_{st['study']}_{ngay}_{st['sha'][:8]}.md"
    p_md.parent.mkdir(parents=True, exist_ok=True)
    tam = p_md.with_name(p_md.name + ".tam")
    tam.write_text(bien_ban_md(st), encoding="utf-8", newline="\n")
    tam.replace(p_md)
    _ghi_json(p_md.with_suffix(".json"), {"schema": SCHEMA, "study": st["study"], "tep": st["tep"], "sha": st["sha"],
                                          "vong": st.get("vong", 1), "model": st["model"], "tong_hop": tong_hop(st),
                                          "chu_tich": st.get("chu_tich"), "bien_tap": st.get("bien_tap"),
                                          "disclaimer": API.DISCLAIMER})
    return p_md


# ── vòng kín: hội đồng → biên tập (có rào liêm chính) → họp lại tới khi thông qua ────────────────────────────────────
# Bác sĩ 22/11/2026: «Hội đồng đã được xây dựng đủ tiêu chuẩn để phản biện nên đừng để xảy ra vấn đề phát hiện lỗi và để
# tôi phải quyết; tôi chỉ nhận lại là những nội dung liêm chính và chuẩn mực nhất». Nhận xét đã xác minh ⇒ biên tập viên
# (Claude) đề xuất THAY THẾ NGUYÊN VĂN; MÁY chỉ áp thay thế qua đủ rào; bản mới họp lại; tối đa `SO_VONG_TOI_DA` vòng.
SO_VONG_TOI_DA = 6          # 1 vòng thẩm định toàn diện + tối đa 5 vòng thẩm tra chỉnh sửa (QC-HDKH-2.1)
MAX_TOKENS_BT = 64000
VAN_DE_MOI_YEU_CAU = 6
SO_LAN_NOP_LAI_BIEN_TAP = 2
TRAN_KY_TU_THAY = 3000
_SO_RE = re.compile(r"\d+(?:[.,]\d+)*")
_TRICH_RE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
_DAU_VET_MAY = re.compile(r"\[CẦN|giả lập|máy sinh|Claude|trí tuệ nhân tạo sinh|\bAI\b", re.IGNORECASE)


def loi_nhan_bien_tap(van_de: Sequence[Dict[str, Any]]) -> str:
    gon = [{k: f.get(k) for k in ("id", "muc_phieu", "muc_do", "dong", "trich", "van_de", "chuan", "de_xuat",
                                  "ly_do_tham_tra", "rao_loai") if f.get(k) not in (None, "", [])}
           for f in van_de]
    dong = [
        "VAI CỦA BẠN: BIÊN TẬP VIÊN thay mặt nhóm nghiên cứu, sửa đề cương theo các vấn đề hội đồng đã giữ (đã xác",
        "minh nguyên văn). Với TỪNG vấn đề chọn một hành động:",
        "- «sua»: danh sách thay thế {dong, cu, moi} — «cu» là đoạn NGUYÊN VĂN, đủ dài để chỉ xuất hiện MỘT lần",
        "  trong tài liệu (có thể ở chỗ khác dòng nêu vấn đề, vd thêm khung bảng ở Chương 3); «dong» là số dòng của",
        "  «cu» để tham chiếu; «moi» là đoạn thay.",
        "- «khong_sua»: đề cương thật ra đã đáp ứng — nêu số dòng chứng minh.",
        "- «vuot_tham_quyen»: chỉ khi cần dữ kiện/quyết định KHÔNG có trong tài liệu và hồ sơ (số liệu thật, kinh",
        "  phí, chữ ký, quyết định của Hội đồng Đạo đức) — nêu đúng dữ kiện cần.",
        "LUẬT LIÊM CHÍNH (máy kiểm, vi phạm ⇒ thay thế bị loại):",
        "1. KHÔNG thêm con số nào chưa có trong tài liệu; KHÔNG thêm trích dẫn/tài liệu tham khảo mới (chỉ dùng số",
        "   trích dẫn đã có).",
        "2. KHÔNG đổi quyết định đã chốt: thiết kế, cỡ mẫu, kết cục chính, quần thể, kế hoạch phân tích đã khoá",
        "   trong SAP. Vấn đề đòi đổi những điều đó ⇒ «vuot_tham_quyen» kèm đề xuất.",
        "3. Khẳng định không có nguồn ⇒ viết lại cho đúng mức chứng cứ hoặc bỏ; KHÔNG bịa nguồn.",
        "4. Văn phong tiếng Việt học thuật, đọc như văn bản người viết: không «[CẦN …]», không nhắc máy/giả lập/AI.",
        "5. Sửa tối thiểu đủ giải quyết vấn đề; mỗi «moi» ≤ 3.000 ký tự.",
        "6. Giữ chuẩn trình bày máy kiểm (vi phạm ⇒ thay thế bị loại khi chọn lọc): không ký hiệu nội bộ («§», «SAP",
        "   §», tên biến dạng ten_bien ngoài bảng/phụ lục) — K4; ở đặt vấn đề/tổng quan/bàn luận mỗi mệnh đề có số",
        "   liệu kiểu kết quả phải tự mang trích dẫn [n] — K10; số thập phân dấu phẩy, ngày dd/mm/yyyy, ngoặc kép “…”,",
        "   không «vs», không chữ IN HOA nhấn mạnh — K11; từ mơ hồ («phần lớn», «đa số», «thường gặp»…) phải có trích",
        "   dẫn — K15.",
        "7. Vấn đề có «ly_do_tham_tra» (lý do người thẩm tra coi là CHƯA giải quyết) hoặc «rao_loai» (lý do rào đã",
        "   LOẠI bản sửa trước của bạn): sửa đúng chỗ còn thiếu, KHÔNG lặp lại bản đã bị loại.",
        f"VẤN ĐỀ:\n{json.dumps(gon, ensure_ascii=False, indent=1)}",
        "Trả về DUY NHẤT JSON: " + json.dumps({"sua": [{"id": "F01", "hanh_dong": "sua|khong_sua|vuot_tham_quyen",
                                                    "thay": [{"dong": 12, "cu": "…", "moi": "…"}], "ly_do": "…"}]},
                                            ensure_ascii=False),
    ]
    return "\n".join(dong)


# ── QC-HDKH-4.0: NỘI DUNG ĐÃ KHOÁ — máy KHÔNG được sửa (đo thật 22/11/2026: chốt kiểm `tham-dinh-dau-ra` trả về CẢ HAI
# đề cương «thông qua» theo QC-2.1 — biên tập viên API đã đảo mã hoá biến phái sinh đã duyệt, lật quyết định đăng ký,
# tự viết khai xung đột lợi ích, sửa Phụ lục A tóm tắt SAP đã ký, xoá/thêm phân tích độ nhạy trái SAP, đổi đơn vị cụm,
# thêm biến ngoài bộ biến). Các vùng này thuộc quyết định của chủ nhiệm / SAP đã khoá / hồ sơ đạo đức ⇒ thay thế chạm
# vào ⇒ LOẠI, yêu cầu trở thành «vượt thẩm quyền — cần dữ kiện của người có thẩm quyền».
_KHOA_LUON = re.compile(r"(?i)kế hoạch phân tích thống kê|\bSAP\b|bảng biến|mã hoá|mã hóa|biến phái sinh"
                        r"|phiếu thu thập|kinh phí|dự trù|danh sách (?:các )?cán bộ|nhân lực|đăng ký nghiên cứu"
                        r"|xung đột lợi ích")
_KHOA_KHI_SAP = re.compile(r"(?i)xử lý (?:và phân tích )?số liệu|phân tích (?:số liệu|thống kê|dữ liệu)|cỡ mẫu"
                           r"|dự kiến kết quả|khung bảng|biến số|chỉ số nghiên cứu|biến dự báo|kết cục")
_MO_KHOA = re.compile(r"(?i)bàn luận|hạn chế|tổng quan|đặt vấn đề|mục tiêu|tính cấp thiết")
_DONG_KHOA = re.compile(r"(?i)^\s*(?:[-*+]\s*)?\**\s*(?:đăng ký nghiên cứu|xung đột lợi ích|nguồn kinh phí|kinh phí"
                        r"|tài trợ)\s*\**\s*:")


def vung_khoa(van: str, sap_khoa: bool = False) -> List[bool]:
    """Cờ khoá cho TỪNG dòng: đề mục gần nhất (hoặc tổ tiên, khi đề mục gần nhất không «mở khoá») thuộc vùng khoá,
    hoặc dòng là mục khai đăng ký/xung đột lợi ích/kinh phí."""
    co: List[bool] = []
    chuoi: List[Tuple[int, str]] = []   # (cấp, đề mục)
    for d in van.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", d)
        if m:
            cap = len(m.group(1))
            chuoi = [(c, t) for c, t in chuoi if c < cap] + [(cap, m.group(2))]

        def khoa(t: str) -> bool:
            return bool(_KHOA_LUON.search(t) or (sap_khoa and _KHOA_KHI_SAP.search(t)))

        gan = chuoi[-1][1] if chuoi else ""
        k = khoa(gan) or (not _MO_KHOA.search(gan) and any(khoa(t) for _, t in chuoi[:-1]))
        co.append(bool(k or _DONG_KHOA.search(d)))
    return co


def sap_da_khoa(ho_so: Dict[str, Any]) -> bool:
    """SAP đã chốt ⇔ chấm sống G4 ĐẠT hoặc SẴN SÀNG KÝ (đo thật 22/11/2026: worktree/đề tài chưa ký vẫn có SAP đã chốt —
    BTM G4 READY nhưng máy từng thêm phân tích ĐN10 trái SAP). Hai mức đều ⇒ sửa phân tích là việc của PI/thống kê
    viên, không phải máy."""
    g4 = ((ho_so.get("bang_chung_he") or {}).get("cong_song") or {})
    g4 = g4.get("G4") if isinstance(g4, dict) else None
    return bool(g4 and g4.get("muc") in ("PASS", "READY"))


def kiem_thay(th: Dict[str, Any], van: str, khoa: Optional[Sequence[bool]] = None) -> Optional[str]:
    """Lý do LOẠI một thay thế (None = nhận). Kiểm trên văn bản HIỆN TẠI (sau các thay thế đã áp trước nó)."""
    cu, moi = str(th.get("cu") or ""), str(th.get("moi") or "")
    if not cu.strip():
        return "thiếu đoạn cũ"
    if van.count(cu) != 1:
        return f"đoạn cũ xuất hiện {van.count(cu)} lần (phải đúng 1)"
    if khoa is not None:
        dau = van[:van.index(cu)].count("\n")
        cuoi = dau + cu.count("\n")
        if any(khoa[i] for i in range(dau, min(cuoi + 1, len(khoa)))):
            return (f"chạm NỘI DUNG ĐÃ KHOÁ (dòng {dau + 1}–{cuoi + 1}: SAP/bảng biến/phiếu thu thập/đăng ký/xung "
                    "đột lợi ích/kinh phí, hoặc mục phân tích khi SAP đã khoá) — thuộc thẩm quyền chủ nhiệm/thống kê "
                    "viên: khai «vuot_tham_quyen»")
    # QC-HDKH-1.1: KHÔNG ràng buộc số dòng — đo thật dưới 1.0, 85% thay thế đúng bị loại oan (dòng lệch sau thay thế
    # trước; vấn đề nêu ở danh mục bảng phải sửa ở Chương 3). Đoạn cũ duy nhất đã định vị không nhập nhằng.
    if len(moi) > TRAN_KY_TU_THAY:
        return f"đoạn thay dài {len(moi)} ký tự (> {TRAN_KY_TU_THAY})"
    da_co = {int(x) for m in _TRICH_RE.findall(van) for x in re.findall(r"\d+", m)}
    trich_moi = {int(x) for m in _TRICH_RE.findall(moi) for x in re.findall(r"\d+", m)} - da_co
    if trich_moi:
        return f"trích dẫn mới không có trong đề cương: {sorted(trich_moi)}"
    khong_trich = _TRICH_RE.sub(" ", moi)
    so_moi = set(_SO_RE.findall(khong_trich)) - set(_SO_RE.findall(cu)) - set(_SO_RE.findall(van))
    if so_moi:
        return f"số mới không có trong đề cương: {', '.join(sorted(so_moi))}"
    if _DAU_VET_MAY.search(moi):
        return "đoạn thay có ô trống hoặc dấu vết máy"
    if _SO_DIEN_THOAI.search(moi):
        return "đoạn thay có chuỗi giống số điện thoại (PII)"
    return None


def ap_bien_tap(dl: Any, van: str, sap_khoa: Optional[bool] = None) -> Tuple[str, Dict[str, Any]]:
    """Áp các thay thế hợp lệ theo thứ tự; trả (văn bản mới, nhật ký nhận/loại/không sửa/vượt thẩm quyền)."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("đề xuất biên tập không phải đối tượng JSON")
    nk: Dict[str, Any] = {"nhan": [], "loai": [], "khong_sua": [], "vuot_tham_quyen": []}
    for muc in dl.get("sua") or []:
        if not isinstance(muc, dict):
            continue
        hd, fid, ly = str(muc.get("hanh_dong") or ""), muc.get("id"), str(muc.get("ly_do") or "")
        if hd in ("khong_sua", "vuot_tham_quyen"):
            nk[hd].append({"id": fid, "ly_do": ly})
            continue
        for th in muc.get("thay") or []:
            if not isinstance(th, dict):
                continue
            loi = kiem_thay(th, van, vung_khoa(van, sap_khoa) if sap_khoa is not None else None)
            ban = {"id": fid, "dong": th.get("dong"), "cu": str(th.get("cu") or ""),
                   "moi": str(th.get("moi") or "")[:TRAN_KY_TU_THAY]}
            if loi:
                nk["loai"].append({**ban, "cu": ban["cu"][:300], "ly_do_loai": loi})
            else:
                van = van.replace(str(th["cu"]), str(th.get("moi") or ""), 1)
                nk["nhan"].append(ban)
    return van, nk


def _do_chuan(van: str, study: str, out_dir: Path, la_chinh: bool) -> Dict[str, Any]:
    """Số đo tất định để so TRƯỚC/SAU biên tập: số mục chuẩn thiếu (K17), lỗi K1–K17, lệch xuyên cổng."""
    hs = ho_so_kiem_may(study, out_dir, van, la_chinh)
    k17 = hs.get("k17") if isinstance(hs.get("k17"), dict) else {}
    nq = (hs.get("nhat_quan") or {}) if isinstance(hs.get("nhat_quan"), dict) else {}
    tong = nq.get("tong") or {}
    return {"k17_thieu": k17.get("thieu"), "k1_k17": hs.get("k1_k17") if isinstance(hs.get("k1_k17"), list) else None,
            "lech": (tong.get("lech_cung") or 0) + (tong.get("lech_mem") or 0) if tong else None}


def _xau_di(truoc: Dict[str, Any], sau: Dict[str, Any]) -> List[str]:
    ra = []
    if isinstance(truoc.get("k17_thieu"), int) and isinstance(sau.get("k17_thieu"), int) \
            and sau["k17_thieu"] > truoc["k17_thieu"]:
        ra.append(f"K17 thiếu {truoc['k17_thieu']} → {sau['k17_thieu']}")
    if isinstance(truoc.get("k1_k17"), list) and isinstance(sau.get("k1_k17"), list):
        # So SỐ LỖI theo từng mã K, không so nguyên chuỗi: thông điệp lỗi trích đoạn văn nên cùng một lỗi cũ ở cùng
        # chỗ đổi chữ sau khi sửa câu (đo 22/11: K10 dòng 8 bị coi là «mới» ⇒ hoàn nguyên nhầm một bản sửa đúng).
        def _dem(ds: Sequence[str]) -> Dict[str, int]:
            d: Dict[str, int] = {}
            for x in ds:
                m = re.match(r"\s*(K\d+)", str(x))
                d[m.group(1) if m else "khac"] = d.get(m.group(1) if m else "khac", 0) + 1
            return d
        dt_, ds_ = _dem(truoc["k1_k17"]), _dem(sau["k1_k17"])
        tang = [f"{k} {dt_.get(k, 0)}→{v}" for k, v in sorted(ds_.items()) if v > dt_.get(k, 0)]
        if tang:
            ra.append("lỗi K1–K17 tăng: " + ", ".join(tang))
    if isinstance(truoc.get("lech"), int) and isinstance(sau.get("lech"), int) and sau["lech"] > truoc["lech"]:
        ra.append(f"lệch xuyên cổng {truoc['lech']} → {sau['lech']}")
    return ra


def _ghi_van(p: Path, van: str) -> None:
    tam = p.with_name(p.name + ".tam")
    tam.write_text(van, encoding="utf-8", newline="\n")
    tam.replace(p)


def _xuat_word(out_dir: Path, study: str, van: str) -> str:
    """Xuất lại Word của đề cương nộp (bộ xuất riêng của đề cương, không thêm bìa máy). Trả ghi chú kết quả."""
    try:
        import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: PLC0415

        kq = SDC.xuat_word(out_dir, study, van)
        return "đã xuất lại Word" if kq else "chưa xuất lại Word (thiếu python-docx)"
    except Exception as exc:  # noqa: BLE001
        return f"chưa xuất lại Word: {type(exc).__name__}"


def _thu_ban(van_thu: str, tep: Path, out_dir: Path, study: str, k_truoc: Dict[str, Any]) -> List[str]:
    """Ghi bản thử + xuất Word (K1–K17 so Word với .md) rồi đo; trả danh sách «xấu đi» so với bản đầu vòng.
    Bản thử NẰM LẠI trên đĩa — bên gọi chịu trách nhiệm ghi bản cuối hoặc hoàn nguyên."""
    _ghi_van(tep, van_thu)
    _xuat_word(out_dir, study, van_thu)
    try:
        k = _do_chuan(van_thu, study, out_dir, True)
    except Exception as exc:  # noqa: BLE001 — không đo được ⇒ coi là xấu đi (không bao giờ «đạt»)
        return [f"không đo được: {type(exc).__name__}"]
    return _xau_di(k_truoc, k)


# ── thẩm tra chỉnh sửa (QC-HDKH-2.0) ────────────────────────────────────────────────────────────────────────────────
KET_QUA_TT = ("da_giai_quyet", "chua_giai_quyet", "can_du_kien")
MAX_TOKENS_TT = 24000


def khoang_sua(van_cu: str, van_moi: str) -> List[List[int]]:
    """Các khoảng dòng (đánh số từ 1, đóng) của bản MỚI đã thay đổi so với bản cũ; dòng bị xoá ⇒ dòng kề trong bản
    mới."""
    import difflib  # noqa: PLC0415

    a, b = van_cu.splitlines(), van_moi.splitlines()
    ra: List[List[int]] = []
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        ra.append([j1 + 1, j2] if j2 > j1 else [max(1, j1), max(1, j1)])
    return ra


def _trong_khoang(dong: int, khoang: Sequence[Sequence[int]]) -> bool:
    return any(a - CUA_SO_DONG <= dong <= b + CUA_SO_DONG for a, b in khoang)


def loi_nhan_tham_tra(tv: Dict[str, Any], ds: Sequence[Dict[str, Any]], khoang: Sequence[Sequence[int]]) -> str:
    gon = [{k: f.get(k) for k in ("id", "muc_phieu", "muc_do", "dong", "trich", "van_de", "de_xuat",
                                  "hanh_dong_bien_tap", "ly_do_bien_tap")} for f in ds]
    dong = [
        f"VAI CỦA BẠN: {tv['vai']} — THẨM TRA VIỆC CHỈNH SỬA theo kết luận hội đồng (KHÔNG thẩm định lại từ đầu).",
        "Tài liệu ở trên là bản ĐÃ SỬA. Dưới đây là các yêu cầu bạn đã nêu ở vòng thẩm định («dong», «trich» là của",
        "bản trước) và hành động của biên tập viên. Với TỪNG yêu cầu, chọn một kết quả:",
        "- «da_giai_quyet»: trích NGUYÊN VĂN đoạn trong bản đã sửa đáp ứng yêu cầu, kèm số dòng — máy đối chiếu, không",
        "  khớp ⇒ coi là chưa giải quyết.",
        "- «chua_giai_quyet»: nói rõ còn thiếu gì.",
        "- «can_du_kien»: chỉ khi biên tập viên đã khai «vuot_tham_quyen» VÀ đúng là cần dữ kiện/quyết định của người",
        "  có thẩm quyền (số liệu thật, kinh phí, họ tên, chữ ký, sửa kế hoạch phân tích đã khoá) — nêu dữ kiện cần.",
        "Lỗi MỚI chỉ được nêu khi nằm TRONG các đoạn vừa sửa (khoảng dòng của bản đã sửa: "
        + (", ".join(f"{a}–{b}" for a, b in khoang) or "không có") + "); lỗi khác ngoài phạm vi thẩm tra.",
        "Không đòi điều chuẩn không đòi; không ghi thông tin định danh cá nhân.",
        f"YÊU CẦU CỦA BẠN:\n{json.dumps(gon, ensure_ascii=False, indent=1)}",
        "Trả về DUY NHẤT JSON: " + json.dumps({
            "tham_tra": [{"id": "F01", "ket_qua": "da_giai_quyet|chua_giai_quyet|can_du_kien", "dong": 12,
                          "trich": "…", "ly_do": "…"}],
            "loi_moi": [{"muc_phieu": "1|2|3|4", "muc_do": "nghiem_trong|can_sua", "dong": 12, "trich": "…",
                         "van_de": "…", "de_xuat": "…"}]}, ensure_ascii=False),
    ]
    return "\n".join(dong)


def xac_minh_tham_tra(ma: str, dl: Any, ds: Sequence[Dict[str, Any]], van: str, khoang: Sequence[Sequence[int]],
                      vtq_ids: Sequence[str]) -> Dict[str, Any]:
    """Kiểm phán quyết thẩm tra của MỘT thành viên. Thiếu phán quyết ⇒ chưa giải quyết (fail-safe)."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("phán quyết thẩm tra không phải đối tượng JSON")
    cac_dong = van.splitlines()
    pq = {str(x.get("id")): x for x in (dl.get("tham_tra") or []) if isinstance(x, dict)}
    ket: Dict[str, Dict[str, Any]] = {}
    for f in ds:
        x = pq.get(str(f["id"])) or {}
        kq, ly, trich = str(x.get("ket_qua") or ""), str(x.get("ly_do") or "").strip(), str(x.get("trich") or "")
        try:
            dong = int(x.get("dong"))
        except (TypeError, ValueError):
            dong = 0
        if kq not in KET_QUA_TT:
            kq, ly = "chua_giai_quyet", "không có phán quyết hợp lệ — coi là chưa giải quyết"
        elif kq == "da_giai_quyet" and not _trong_cua_so(trich, dong, cac_dong):
            kq, ly = "chua_giai_quyet", f"bằng chứng «đã giải quyết» không có nguyên văn quanh dòng {dong}"
        elif kq == "can_du_kien" and str(f["id"]) not in set(map(str, vtq_ids)):
            kq, ly = "chua_giai_quyet", "biên tập viên không khai vượt thẩm quyền cho yêu cầu này"
        elif kq != "da_giai_quyet" and not ly:
            ly = "không nêu lý do"
        ket[str(f["id"])] = {**f, "ket_qua": kq, "ly_do_tham_tra": ly, "dong_moi": dong, "trich_moi": trich[:300],
                             "nguoi_tham_tra": ma}
    moi, loai = [], []
    for g in dl.get("loi_moi") or []:
        if not isinstance(g, dict):
            continue
        h = {k: str(g.get(k) or "").strip() for k in ("muc_phieu", "muc_do", "trich", "van_de", "de_xuat")}
        try:
            h["dong"] = int(g.get("dong"))
        except (TypeError, ValueError):
            h["dong"] = 0
        ly = []
        if h["muc_phieu"] not in MUC_PHIEU or h["muc_do"] not in ("nghiem_trong", "can_sua"):
            ly.append("mục/mức không hợp lệ")
        if not h["van_de"] or not h["de_xuat"]:
            ly.append("thiếu vấn đề hoặc đề xuất")
        if not _trong_cua_so(h["trich"], h["dong"], cac_dong):
            ly.append("trích không có nguyên văn quanh dòng đã nêu")
        if not _trong_khoang(h["dong"], khoang):
            ly.append("ngoài các đoạn vừa sửa — ngoài phạm vi thẩm tra")
        if any(_SO_DIEN_THOAI.search(h[k]) for k in ("van_de", "de_xuat", "trich")):
            ly.append("có chuỗi giống số điện thoại (PII)")
        ban = {**h, "thanh_vien": ma, "chuan": ""}
        if ly:
            loai.append({**ban, "ly_do_loai": "; ".join(ly)})
        else:
            moi.append(ban)
    return {"ket": ket, "loi_moi": moi, "loai": loai}


def ket_luan_tham_tra(tt: Dict[str, Any]) -> Tuple[str, str]:
    """LUẬT CỐ ĐỊNH của vòng thẩm tra: còn yêu cầu chưa giải quyết hoặc lỗi mới ⇒ chưa đạt; không còn nhưng có yêu cầu
    cần dữ kiện ⇒ thông qua phần thuộc thẩm quyền nhóm soạn thảo (kèm danh sách dữ kiện); còn lại ⇒ thông qua."""
    chua, moi, du_kien = tt.get("chua_giai_quyet") or [], tt.get("loi_moi") or [], tt.get("can_du_kien") or []
    if chua or moi:
        return "chua_dat", f"{len(chua)} yêu cầu chưa giải quyết, {len(moi)} lỗi mới trong đoạn vừa sửa"
    if du_kien:
        return ("thong_qua_cho_du_kien",
                f"mọi yêu cầu đã giải quyết; {len(du_kien)} yêu cầu cần dữ kiện của người có thẩm quyền")
    return "thong_qua", "mọi yêu cầu đã giải quyết, không lỗi mới"


def tham_tra_cong_don(st: Dict[str, Any]) -> Dict[str, Any]:
    """Kết quả thẩm tra của vòng hiện tại CỘNG DỒN các yêu cầu «cần dữ kiện» của những vòng trước (vòng sau chỉ thẩm
    tra yêu cầu còn chưa giải quyết, nên yêu cầu cần dữ kiện cũ không được rơi khỏi kết luận)."""
    tt = dict(st.get("tham_tra") or {})
    tt["can_du_kien"] = list(st.get("can_du_kien_truoc") or []) + list(tt.get("can_du_kien") or [])
    return tt


def van_de_can_sua(st: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Danh sách giao biên tập viên: vòng thẩm định ⇒ mọi vấn đề hội đồng giữ; vòng thẩm tra ⇒ yêu cầu chưa giải quyết
    + lỗi mới."""
    if st.get("che_do") == "tham_tra":
        tt = st.get("tham_tra") or {}
        return list(tt.get("chua_giai_quyet") or []) + list(tt.get("loi_moi") or [])
    return list(tong_hop(st)["van_de"])


def _chay_tham_tra(st: Dict[str, Any], van: str, goi_api: bool, client: Any) -> int:
    """Một lượt nộp/lấy batch thẩm tra (mỗi thành viên có yêu cầu ⇒ một yêu cầu API)."""
    chung = khoi_chung(st["study"], ten_cho_hoi_dong(st["tep"]), van, st["ho_so"])
    theo_tv: Dict[str, List[Dict[str, Any]]] = {}
    for f in st.get("ds_yeu_cau") or []:
        theo_tv.setdefault(f["thanh_vien"], []).append(f)
    ten = {tv["ma"]: tv for tv in _ds_tv(st)}
    cids = {ma: f"tt_{ma}_{st['sha'][:8]}" for ma in theo_tv}
    bid = st["batch"].get("tham_tra")
    if not bid:
        if not theo_tv:
            st["tham_tra"] = {"da_giai_quyet": [], "chua_giai_quyet": [], "can_du_kien": [], "loi_moi": [],
                              "loai": []}
            st["buoc"] = "xong"
            return 0
        if not goi_api:
            print(f"(chạy khô) thẩm tra {sum(map(len, theo_tv.values()))} yêu cầu của {len(theo_tv)} thành viên.")
            return 0
        yc = [(cids[ma], tham_so_yeu_cau(chung, loi_nhan_tham_tra(ten[ma], ds, st.get("khoang") or []), st["model"],
                                         MAX_TOKENS_TT)) for ma, ds in theo_tv.items()]
        st["batch"]["tham_tra"] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        print(f"📨 Đã nộp batch thẩm tra: {st['batch']['tham_tra']} ({len(yc)} thành viên).")
        return 4
    if not goi_api:
        return 0
    tt_b = API.trang_thai_batch(bid, client=client)
    if tt_b["trang_thai"] != "ended":
        print(f"⏳ Batch thẩm tra {bid} đang xử lý — chạy lại sau.")
        return 4
    ket = API.doc_ket_qua_batch(bid, client=client, nguon=CONG_CU)
    da_co: Dict[str, Any] = st.setdefault("tt_tung_tv", {})   # kết quả đã đọc được, giữ qua các lần nộp lại
    hong_tv: Dict[str, str] = {}
    for ma, ds in theo_tv.items():
        if ma in da_co:
            continue
        try:
            tho = API.van_ban_ket_qua_batch(ket.get(cids[ma], {"loai": "thieu"}), MAX_TOKENS_TT)
            st.setdefault("tho", {})[cids[ma]] = tho
            da_co[ma] = xac_minh_tham_tra(ma, API.doc_json(tho), ds, van, st.get("khoang") or [],
                                          st.get("vtq_ids") or [])
        except API.LoiApi as exc:
            hong_tv[ma] = f"thẩm tra hỏng: {exc}"[:200]
    if hong_tv and int(st.get("so_lan_nop_lai_tt", 0)) < SO_LAN_NOP_LAI_BIEN_TAP:
        # QC-HDKH-2.1: phản hồi không đọc được là lỗi KỸ THUẬT, không phải phán quyết ⇒ nộp lại riêng thành viên đó
        st["so_lan_nop_lai_tt"] = int(st.get("so_lan_nop_lai_tt", 0)) + 1
        st.setdefault("loi_tham_tra", []).extend(f"{ma}: {ly}" for ma, ly in hong_tv.items())
        yc = [(cids[ma], tham_so_yeu_cau(chung, loi_nhan_tham_tra(ten[ma], theo_tv[ma], st.get("khoang") or []),
                                         st["model"], MAX_TOKENS_TT)) for ma in hong_tv]
        st["batch"]["tham_tra"] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        print(f"⚠️ Phản hồi thẩm tra của {', '.join(hong_tv)} không đọc được — đã nộp lại lần "
              f"{st['so_lan_nop_lai_tt']}: {st['batch']['tham_tra']}")
        return 4
    for ma, hong in hong_tv.items():  # nộp lại đủ số lần vẫn hỏng ⇒ mọi yêu cầu của họ chưa giải quyết (fail-safe)
        da_co[ma] = {"ket": {str(f["id"]): {**f, "ket_qua": "chua_giai_quyet", "ly_do_tham_tra": hong,
                                            "nguoi_tham_tra": ma} for f in theo_tv[ma]}, "loi_moi": [], "loai": []}
    gop: Dict[str, Any] = {"da_giai_quyet": [], "chua_giai_quyet": [], "can_du_kien": [], "loi_moi": [], "loai": []}
    for ma in theo_tv:
        kq = da_co[ma]
        for x in kq["ket"].values():
            gop[x["ket_qua"]].append(x)
        gop["loi_moi"] += kq["loi_moi"]
        gop["loai"] += kq["loai"]
    for i, g in enumerate(gop["loi_moi"], 1):
        g["id"] = f"N{st.get('vong', 2)}_{i:02d}"
    st["tham_tra"] = gop
    st["buoc"] = "xong"
    print(f"✅ Thẩm tra xong: {len(gop['da_giai_quyet'])} đã giải quyết · {len(gop['chua_giai_quyet'])} chưa · "
          f"{len(gop['can_du_kien'])} cần dữ kiện · {len(gop['loi_moi'])} lỗi mới.")
    return 0


def _de_xuat_bien_tap(st: Dict[str, Any], van: str, out_dir: Path, goi_api: bool,
                      client: Any) -> Tuple[Optional[int], Dict[str, Any], List[str]]:
    """Lấy đề xuất biên tập: chế độ KẾT HỢP ⇒ agent của hệ (phiếu việc, mã 5 khi chờ); chế độ API ⇒ batch như cũ.
    Trả (mã thoát nếu phải dừng bước, đề xuất gộp, yêu cầu hỏng)."""
    if st.get("ket_hop"):
        if not st.get("viec_bien_tap"):
            st["viec_bien_tap"] = lap_viec_bien_tap(st, van_de_can_sua(st), out_dir, van)
            gom = [f"{'+'.join(c)} → {ten}" for ten, v in st["viec_bien_tap"].items() for c in v.get("cum") or []]
            if gom:
                print(f"🔗 Gom yêu cầu chạm cùng chỗ vào một phiếu: {'; '.join(gom)}.")
        gop_ag = gop_tra_loi_bien_tap(st["viec_bien_tap"])
        if gop_ag is None:
            print(f"🤝 Chờ agent biên tập: {', '.join(st['viec_bien_tap'])} — chạy «viec-agent» để xem phiếu việc.")
            return CHO_AGENT, {}, []
        return None, gop_ag, []
    # bien_tap — chia nhóm ≤ VAN_DE_MOI_YEU_CAU vấn đề mỗi yêu cầu (22/11/2026: một yêu cầu gom 14–20 vấn đề bị cắt cụt
    # ở 32.000 token ra trên cả hai đề cương thật), KHÔNG tách một cụm yêu cầu chạm cùng chỗ (`gom_cum_bien_tap`) ra hai
    # yêu cầu API. Tham số VẬN HÀNH, không phải luật/lời dặn của quy chế.
    chung = khoi_chung(st["study"], ten_cho_hoi_dong(st["tep"]), van, st["ho_so"])
    vd = van_de_can_sua(st)
    cum = gom_cum_bien_tap(vd, van)
    nhom = xep_lo_theo_cum(cum, VAN_DE_MOI_YEU_CAU)
    cids = [f"bt{i}_{st['sha'][:8]}" for i in range(len(nhom))]
    bid = st["batch"].get("bien_tap")
    if not bid:
        if int(st.get("so_lan_hong_bien_tap", 0)) > SO_LAN_NOP_LAI_BIEN_TAP:
            print(f"⛔ Biên tập hỏng {st['so_lan_hong_bien_tap']} lần (1 lần đầu + {SO_LAN_NOP_LAI_BIEN_TAP} lần nộp "
                  f"lại) — dừng: {(st.get('loi_bien_tap') or ['?'])[-1]}")
            return 1, {}, []
        if not goi_api:
            print(f"(chạy khô) biên tập {len(vd)} vấn đề trong {len(nhom)} yêu cầu — thêm --goi-api.")
            return 0, {}, []
        yc = [(c, tham_so_yeu_cau(chung, loi_nhan_bien_tap(g), st["model"], MAX_TOKENS_BT)) for c, g in zip(cids, nhom)]
        st["batch"]["bien_tap"] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        print(f"📨 Đã nộp batch biên tập: {st['batch']['bien_tap']} ({len(yc)} yêu cầu).")
        gom = ["+".join(str(f["id"]) for f in c) for c in cum if len(c) > 1]
        if gom:
            print(f"🔗 Gom yêu cầu chạm cùng chỗ vào cùng một yêu cầu API: {'; '.join(gom)}.")
        return 4, {}, []
    if not goi_api:
        return 0, {}, []
    tt = API.trang_thai_batch(bid, client=client)
    if tt["trang_thai"] != "ended":
        print(f"⏳ Batch biên tập {bid} đang xử lý — chạy lại sau.")
        return 4, {}, []
    ket = API.doc_ket_qua_batch(bid, client=client, nguon=CONG_CU)
    gop: Dict[str, Any] = {"sua": []}
    hong = []
    for c in cids:
        try:
            tho = API.van_ban_ket_qua_batch(ket.get(c, {"loai": "thieu"}), MAX_TOKENS_BT)
            st.setdefault("tho", {})[c] = tho
            dl = API.doc_json(tho)
            gop["sua"] += list((dl or {}).get("sua") or []) if isinstance(dl, dict) else []
        except API.LoiApi as exc:
            hong.append(f"{c}: {exc}"[:300])
    if hong and len(hong) == len(cids):
        # mọi yêu cầu hỏng ⇒ ghi lại, bỏ id batch để lượt sau NỘP LẠI (giới hạn SO_LAN_NOP_LAI_BIEN_TAP lần)
        st.setdefault("loi_bien_tap", []).extend(hong)
        st["so_lan_hong_bien_tap"] = int(st.get("so_lan_hong_bien_tap", 0)) + 1
        st["batch"].pop("bien_tap", None)
        print(f"⚠️ Biên tập hỏng cả {len(cids)} yêu cầu — sẽ nộp lại: {hong[0]}")
        return 1, {}, []
    return None, gop, hong


def vong_kin_buoc(st: Dict[str, Any], van: str, tep: Path, out_dir: Path, goi_api: bool, ap_dung: bool,
                  client: Any) -> int:
    """MỘT bước của vòng kín trên tài liệu hiện tại. Trả mã thoát; 0 + st['buoc']=='dat' ⇒ đã thông qua."""
    if st["buoc"] in ("thanh_vien", "chu_tich"):
        return _chay_buoc(st, van, goi_api, client)
    if st["buoc"] == "tham_dinh_agent":
        return buoc_tham_dinh_agent(st, van, out_dir)
    if st["buoc"] == "tham_tra":
        return buoc_tham_tra_agent(st, van, out_dir) if st.get("ket_hop") else _chay_tham_tra(st, van, goi_api, client)
    if st["buoc"] == "xong":
        if st.get("che_do") == "tham_tra":
            kl, ly = ket_luan_tham_tra(tham_tra_cong_don(st))
            con_n = len(van_de_can_sua(st))
        else:
            th0 = tong_hop(st)
            con_n = sum(1 for f in th0["van_de"] if f["muc_do"] in ("nghiem_trong", "can_sua"))
            kl, ly = ("thong_qua", th0["ly_do_ket_luan"]) if th0["ket_luan"] == "thong_qua" and not con_n else \
                ("chua_dat", th0["ly_do_ket_luan"])
        if kl != "chua_dat":
            st["buoc"], st["ket_luan_cuoi"] = "dat", kl
        elif int(st.get("vong", 1)) >= SO_VONG_TOI_DA:
            print(f"⛔ Đã {st.get('vong', 1)} vòng mà còn {con_n} yêu cầu chưa đạt — dừng, xem biên bản ({ly}).")
            return 1
        else:
            st["buoc"] = "bien_tap"
    if st["buoc"] == "dat" and st.get("ket_hop") and not st.get("trinh_bac_si"):
        ma_dr = buoc_tham_dinh_dau_ra(st, van, out_dir)
        if ma_dr == CHO_AGENT:
            return ma_dr
        loi_dr = (st.get("ket_qua_dau_ra") or {}).get("loi_xac_minh") or []
        if loi_dr and int(st.get("vong", 1)) < SO_VONG_TOI_DA:
            # lỗi liêm chính đã xác minh của chốt cuối ⇒ thành yêu cầu sửa của vòng sau (không trình bác sĩ)
            tt = st.setdefault("tham_tra", {"da_giai_quyet": [], "chua_giai_quyet": [], "can_du_kien": [],
                                            "loi_moi": [], "loai": []})
            st["che_do"] = "tham_tra"
            tt["loi_moi"] = list(tt.get("loi_moi") or []) + [
                {"id": f"R{st.get('vong', 1)}_{k:02d}", "thanh_vien": "dau_ra", "muc_phieu": "4", "muc_do": "can_sua",
                 "dong": int(x.get("dong") or 0), "trich": str(x.get("trich") or ""),
                 "van_de": f"[{x.get('ma')}] {x.get('mo_ta')}", "de_xuat": str(x.get("de_xuat") or "")}
                for k, x in enumerate(loi_dr, 1)]
            st["buoc"] = "bien_tap"
            print(f"↩️ tham-dinh-dau-ra nêu {len(loi_dr)} lỗi liêm chính đã xác minh — chưa trình, sửa tiếp.")
            return 0
        if loi_dr:
            print(f"⛔ Đã {st.get('vong', 1)} vòng; chốt cuối còn {len(loi_dr)} lỗi liêm chính — dừng, xem biên bản.")
            return 1
    if st["buoc"] == "dat":
        print(f"✅ ĐẠT ({KET_LUAN.get(st.get('ket_luan_cuoi') or 'thong_qua')}) ở vòng {st.get('vong', 1)}"
              + (" · tham-dinh-dau-ra ĐẠT — được trình bác sĩ." if st.get("trinh_bac_si") else "."))
        return 0
    if st["buoc"] == "da_sua":
        print(f"↻ Đã sửa ở vòng {st.get('vong', 1)} — chạy lại để hội đồng họp bản mới.")
        return 0
    vd = van_de_can_sua(st)
    ma_bt, gop, hong = _de_xuat_bien_tap(st, van, out_dir, goi_api, client)
    if ma_bt is not None:
        return ma_bt
    sap_k = sap_da_khoa(st.get("ho_so") or {})
    van_moi, nk = ap_bien_tap(gop, van, sap_khoa=sap_k)   # 4.0: rào nội dung đã khoá (vùng tính lại mỗi thay thế)
    nk["yeu_cau_hong"] = hong   # nhóm hỏng: vấn đề của nhóm đó sẽ được hội đồng vòng sau nêu lại (không bị bỏ qua)
    la_chinh = Path(st["tep"]).resolve() == tep_mac_dinh(st["study"], out_dir.parents[1]).resolve()
    st["bien_tap"] = nk
    # 22/11/2026 (đo thật, BTM vòng 4): biên tập viên khai MỌI vấn đề còn lại «vượt thẩm quyền» (vùng khoá) ⇒ 0 thay
    # thế ⇒ máy cũ dừng như thất bại. Đúng ra: KHÔNG ghi tệp, vẫn sang vòng thẩm tra trên chính bản này để người thẩm
    # tra xác nhận «cần dữ kiện» (hoặc biên tập viên thấy lý do rào loại ở vòng sau). Chỉ dừng khi đã hết số vòng.
    khong_doi = not nk["nhan"]
    if khong_doi and int(st.get("vong", 1)) >= SO_VONG_TOI_DA:
        print(f"⛔ Không thay thế nào qua rào liêm chính ({len(nk['loai'])} bị loại) ở vòng tối đa — dừng.")
        return 1
    if not la_chinh:
        print("⛔ Vòng kín chỉ sửa đề cương chính của đề tài.")
        return 3
    if not ap_dung:
        print(f"(chạy khô) {len(nk['nhan'])} thay thế qua rào, {len(nk['loai'])} bị loại — thêm --ap-dung để ghi.")
        return 0
    if khong_doi:
        return _sang_vong_tham_tra(st, out_dir, tep, van, van, gop, vd, nk)
    sao_luu = thu_muc_hd(out_dir) / f"sao_luu_{st['sha'][:12]}{tep.suffix}"
    if not sao_luu.exists():
        _ghi_van(sao_luu, van)
    # K1–K17 và nhất quán xuyên cổng đọc TỆP trên đĩa ⇒ đo «trước» khi ghi bản mới.
    k_truoc = _do_chuan(van, st["study"], out_dir, True)
    xau = _thu_ban(van_moi, tep, out_dir, st["study"], k_truoc)
    nk["do_truoc"] = k_truoc
    if xau:
        # 22/11/2026 (đo thật): hoàn nguyên CẢ LƯỢT vì vài thay thế làm K11/K15/K4 tăng đã bỏ luôn hàng chục thay thế
        # tốt ⇒ CHỌN LỌC: thử từng thay thế, giữ cái không làm chuẩn xấu đi so với bản đầu vòng, loại cái làm xấu đi.
        nk["xau_di_ca_luot"] = xau
        van_moi, giu, bo = van, [], []
        for e in nk["nhan"]:
            loi = kiem_thay(e, van_moi, vung_khoa(van_moi, sap_k))
            if loi:
                bo.append({**e, "cu": e["cu"][:300], "ly_do_loai": f"khi chọn lọc: {loi}"})
                continue
            ung = van_moi.replace(e["cu"], e["moi"], 1)
            x = _thu_ban(ung, tep, out_dir, st["study"], k_truoc)
            if x:
                bo.append({**e, "cu": e["cu"][:300], "ly_do_loai": "làm chuẩn xấu đi: " + "; ".join(x)})
            else:
                van_moi = ung
                giu.append(e)
        nk["nhan"], nk["loai_chon_loc"] = giu, bo
        xau_cuoi = _thu_ban(van_moi, tep, out_dir, st["study"], k_truoc) if giu else ["không giữ được thay thế nào"]
        if xau_cuoi:
            _ghi_van(tep, van)  # hoàn nguyên cả .md lẫn Word
            _xuat_word(out_dir, st["study"], van)
            nk["xau_di"] = xau_cuoi
            print("⛔ Không còn thay thế nào giữ được mà chuẩn không xấu đi — đã HOÀN NGUYÊN: " + "; ".join(xau_cuoi))
            return 1
        print(f"🔎 Chọn lọc: giữ {len(giu)}/{len(giu) + len(bo)} thay thế; loại {len(bo)} vì làm chuẩn xấu đi.")
    nk["word"] = _xuat_word(out_dir, st["study"], van_moi)
    return _sang_vong_tham_tra(st, out_dir, tep, van, van_moi, gop, vd, nk)


def _sang_vong_tham_tra(st: Dict[str, Any], out_dir: Path, tep: Path, van: str, van_moi: str, gop: Dict[str, Any],
                        vd: Sequence[Dict[str, Any]], nk: Dict[str, Any]) -> int:
    """Mở vòng thẩm tra kế tiếp trên ``van_moi`` (trùng ``van`` khi không thay thế nào qua rào — không ghi tệp)."""
    st["buoc"], st["sha_moi"] = "da_sua", _sha(van_moi)
    moi = khoi_tao(st["study"], out_dir, tep, st["model"], st.get("loai", "de_cuong"))
    # QC-HDKH-2.0: vòng sau là THẨM TRA đúng các yêu cầu nghiêm trọng/cần sửa vừa giao, trên các đoạn vừa sửa.
    hd = {str(m.get("id")): m for m in gop["sua"] if isinstance(m, dict)}
    # QC-HDKH-2.1: lý do rào đã loại bản sửa ⇒ đi kèm yêu cầu tới vòng sau (thẩm tra thấy, biên tập viên thấy)
    rao_loai: Dict[str, List[str]] = {}
    for x in list(nk.get("loai") or []) + list(nk.get("loai_chon_loc") or []):
        ds_ly = rao_loai.setdefault(str(x.get("id")), [])
        if len(ds_ly) < 3:
            ds_ly.append(str(x.get("ly_do_loai") or "")[:200])
    tt_cu = st.get("tham_tra") or {}
    moi.update(vong=int(st.get("vong", 1)) + 1, ban_truoc=st["sha"], che_do="tham_tra", buoc="tham_tra",
               ket_hop=st.get("ket_hop", False),
               ds_yeu_cau=[{**f, "hanh_dong_bien_tap": str(hd.get(str(f.get("id")), {}).get("hanh_dong")
                                                          or "không có đề xuất"),
                            "ly_do_bien_tap": str(hd.get(str(f.get("id")), {}).get("ly_do") or ""),
                            "rao_loai": rao_loai.get(str(f.get("id")), [])}
                           for f in vd if f.get("muc_do") in ("nghiem_trong", "can_sua")],
               vtq_ids=[str(x.get("id")) for x in nk["vuot_tham_quyen"]], khoang=khoang_sua(van, van_moi),
               can_du_kien_truoc=list(st.get("can_du_kien_truoc") or []) + list(tt_cu.get("can_du_kien") or []),
               da_giai_quyet_truoc=list(st.get("da_giai_quyet_truoc") or []) + list(tt_cu.get("da_giai_quyet") or []))
    moi["buoc"] = "tham_tra" if moi["ds_yeu_cau"] else "xong"
    if not moi["ds_yeu_cau"]:
        moi["tham_tra"] = {"da_giai_quyet": [], "chua_giai_quyet": [], "can_du_kien": [], "loi_moi": [], "loai": []}
    if van_moi == van:
        # cùng tệp ⇒ cùng SHA ⇒ cùng tệp trạng thái: chuyển st TẠI CHỖ sang vòng mới (tầng gọi ghi st sau khi trả về)
        st.clear()
        st.update(moi)
    _ghi_json(tep_trang_thai(out_dir, moi["sha"]), moi)
    print(f"✍️ Đã áp {len(nk['nhan'])} thay thế ({len(nk['loai'])} bị loại, {len(nk['vuot_tham_quyen'])} vượt thẩm "
          f"quyền) — vòng {moi['vong']} thẩm tra {len(moi['ds_yeu_cau'])} yêu cầu trên "
          + ("bản mới." if van_moi != van else "CHÍNH bản này (không thay thế nào — không ghi tệp)."))
    return 0


# ── hiệu chuẩn: cài lỗi đã biết vào bản sao ──────────────────────────────────────────────────────────────────────────
LOI_CAI: Tuple[Tuple[str, str, str, str], ...] = (
    # (mã, mô tả, mẫu dòng neo — chèn NGAY SAU dòng khớp đầu tiên, câu chèn). Neo chỉ bám ĐỀ MỤC («#…»/«**…»): dòng
    # mục lục («- PHỤ LỤC B…») và câu giữa đoạn không phải chỗ một lỗi thật nằm.
    ("khong_nguon", "khẳng định số liệu không có trích dẫn ở đặt vấn đề",
     r"(?i)^#+\s*(?:\d+\.?\s*)?đặt vấn đề",
     "Tại Việt Nam, tỷ lệ người bệnh không hài lòng với dịch vụ ngoại trú là 47,3%."),
    ("nhan_qua", "ngôn ngữ nhân quả vượt thiết kế quan sát",
     r"(?i)^#+.*(?:ý nghĩa|dự kiến kết quả)", "Kết quả nghiên cứu sẽ chứng minh các yếu tố trên là nguyên nhân gây ra "
     "tình trạng của người bệnh."),
    ("kiem_dinh_sai", "kiểm định thống kê sai loại biến",
     r"(?i)^#+.*(?:phân tích|xử lý) (?:số liệu|thống kê|dữ liệu)", "So sánh tỷ lệ giữa hai nhóm bằng kiểm định "
     "t-Student cho hai mẫu độc lập."),
    ("tieu_chuan_mau_thuan", "tiêu chuẩn loại trừ mâu thuẫn tiêu chuẩn chọn",
     r"(?i)^(?:#+|\*\*).*tiêu chuẩn loại trừ", "- Người bệnh từ 18 tuổi trở lên."),
    ("muc_tieu_khong_phan_tich", "mục tiêu không có phương pháp/phân tích tương ứng",
     r"(?i)^#+.*mục tiêu", "Mục tiêu bổ sung: đánh giá chi phí điều trị trực tiếp của người bệnh trong 12 tháng."),
    ("dong_thuan_sai", "quyền rút lui trái nguyên tắc tự nguyện",
     r"(?i)^(?:#+|\*\*).*(?:đồng thuận|đồng ý tham gia|phiếu đồng ý|chấp thuận tham gia)",
     "Người tham gia không được rút khỏi nghiên cứu sau khi đã ký phiếu đồng ý."),
)


# QC-HDKH-3.0: bộ lỗi cài riêng cho SAP và bản thảo/báo cáo (neo bám đề mục của khuôn hệ sinh; nhiều mẫu ⇒ thử lần
# lượt) + MỘT lỗi ĐẶC THÙ THIẾT KẾ cho đề cương để chứng minh ghế chuyên thiết kế làm đúng việc.
LOI_CAI_SAP: Tuple[Tuple[str, str, Any, str], ...] = (
    ("kiem_dinh_sai", "kiểm định thống kê sai loại biến",
     (r"(?i)^#+.*phân tích chính", r"(?i)^#+.*(?:phương pháp|phân tích) thống kê"),
     "So sánh tỷ lệ kết cục chính giữa hai nhóm bằng kiểm định t-Student cho hai mẫu độc lập."),
    ("du_lieu_thieu", "thay dữ liệu thiếu bằng trung bình mẫu, không phân tích độ nhạy",
     (r"(?i)^#+.*(?:dữ liệu thiếu|thiếu dữ liệu|missing)",),
     "Mọi giá trị thiếu được thay bằng giá trị trung bình của toàn mẫu; không cần phân tích độ nhạy."),
    ("da_so_sanh", "chọn kết cục theo p nhỏ nhất, không hiệu chỉnh đa so sánh",
     (r"(?i)^#+.*đa so sánh", r"(?i)^#+.*nhóm nhỏ"),
     "Không hiệu chỉnh đa so sánh; kết cục phụ nào có giá trị p nhỏ nhất sẽ được báo cáo như kết quả chính."),
    ("loai_ngoai_lai", "loại quan sát khỏi phân tích chính không ghi lý do",
     (r"(?i)^#+.*quần thể phân tích",),
     "Các quan sát có giá trị bất thường được loại khỏi phân tích chính mà không cần ghi lại lý do."),
    ("doi_ket_cuc", "đổi kết cục chính sau khi xem dữ liệu",
     (r"(?i)^#+.*kết cục",),
     "Kết cục chính có thể được thay bằng kết cục khác sau khi xem dữ liệu nếu kết quả ban đầu không có ý nghĩa thống "
     "kê."),
    ("dien_giai_p", "diễn giải p ≥ 0,05 là tương đương",
     (r"(?i)^#+.*(?:độ nhạy|dummy|khung bảng|trình bày)",),
     "Khi giá trị p lớn hơn hoặc bằng 0,05, hai nhóm được kết luận là tương đương nhau."),
)
LOI_CAI_BAN_THAO: Tuple[Tuple[str, str, Any, str], ...] = (
    ("khong_nguon", "khẳng định số liệu không có trích dẫn ở phần mở đầu",
     (r"(?i)^#+.*(?:giới thiệu|đặt vấn đề|introduction)",),
     "Tại Việt Nam, tỷ lệ người bệnh không được điều trị đúng hướng dẫn là 47,3%."),
    ("kiem_dinh_sai", "kiểm định thống kê sai loại biến",
     (r"(?i)^#+.*(?:phân tích thống kê|xử lý số liệu|phân tích số liệu|statistical)", r"(?i)^#+.*phương pháp"),
     "Tỷ lệ giữa hai nhóm được so sánh bằng kiểm định t-Student cho hai mẫu độc lập."),
    ("so_lieu_mau_thuan", "số người phân tích mâu thuẫn với phần còn lại của bài",
     (r"(?i)^#+.*(?:kết quả|results)",),
     "Tổng cộng 1.287 người tham gia được đưa vào phân tích cuối cùng."),
    ("khai_quat_qua_muc", "khái quát kết quả vượt quần thể nghiên cứu",
     (r"(?i)^#+.*(?:bàn luận|discussion)",),
     "Kết quả này áp dụng được cho mọi người bệnh trên cả nước mà không cần thêm nghiên cứu xác nhận."),
    ("ket_luan_vuot_ket_qua", "kết luận về kết cục không được nghiên cứu",
     (r"(?i)^#+.*(?:kết luận|conclusion)",),
     "Nghiên cứu cho thấy tỷ lệ tử vong do mọi nguyên nhân giảm một nửa."),
    ("du_lieu_dinh_danh", "công bố dữ liệu định danh người tham gia",
     (r"(?i)^#+.*(?:khai báo|đạo đức|xung đột|tài trợ|chia sẻ dữ liệu|data availability)",),
     "Bộ dữ liệu kèm họ tên và số điện thoại của người tham gia được công bố công khai cùng bài báo."),
)
_DE_MUC_SO = r"(?i)^#{2,}\s*\d+(?:\.\d+)+\.?\s+.*"   # đề mục CON có đánh số «4.6. …» — tránh neo vào tên đề tài
LOI_CAI_BAO_CAO: Tuple[Tuple[str, str, Any, str], ...] = LOI_CAI_BAN_THAO + (
    ("khuyen_nghi_khong_can_cu", "khuyến nghị không dựa trên kết luận của đề tài (hướng dẫn mục III.12)",
     (r"(?i)^#+.*(?:khuyến nghị|kiến nghị)",),
     "Khuyến nghị Bộ Y tế miễn phí toàn bộ thuốc điều trị bệnh mạn tính cho mọi người dân trên cả nước."),
)
LOI_CAI_THIET_KE: Dict[str, Tuple[str, str, Any, str]] = {
    "rct": ("tk_phan_bo_lo", "không che giấu phân bổ (chẵn/lẻ, biết trước nhóm)",
            (_DE_MUC_SO + r"(?:ngẫu nhiên|phân bổ|phân nhóm)", _DE_MUC_SO + r"thiết kế",
             r"(?i)^#+.*(?:ngẫu nhiên|phân bổ|phân nhóm)"),
            "Người bệnh được phân nhóm theo ngày khám chẵn hoặc lẻ; nghiên cứu viên tuyển chọn biết trước người bệnh "
            "tiếp theo vào nhóm nào."),
    "cohort": ("tk_chon_theo_ket_cuc", "chọn nhóm không phơi nhiễm theo kết cục",
               (_DE_MUC_SO + r"(?:chọn mẫu|đối tượng|nhóm phơi nhiễm|quần thể)",
                r"(?i)^#+.*(?:chọn mẫu|đối tượng|nhóm phơi nhiễm|quần thể)"),
               "Nhóm không phơi nhiễm được chọn trong số người bệnh đã có kết cục để bảo đảm đủ số biến cố."),
    "case_control": ("tk_chung_theo_phoi_nhiem", "chọn nhóm chứng theo phơi nhiễm",
                     (_DE_MUC_SO + r"(?:nhóm chứng|chọn mẫu|đối tượng)", r"(?i)^#+.*(?:nhóm chứng|chọn mẫu|đối tượng)"),
                     "Nhóm chứng được chọn trong số người đang dùng thuốc nghiên cứu để hai nhóm cân bằng về phơi "
                     "nhiễm."),
    "cross_sectional": ("tk_mau_lech", "ước lượng tỷ lệ trên mẫu chỉ gồm người đã có biến chứng",
                        (_DE_MUC_SO + r"(?:chọn mẫu|cỡ mẫu|đối tượng)", r"(?i)^#+.*(?:chọn mẫu|cỡ mẫu|đối tượng)"),
                        "Tỷ lệ hiện mắc được ước lượng trên mẫu chỉ gồm người bệnh đã có biến chứng."),
    "diagnostic": ("tk_xac_minh_mot_phan", "chỉ người test dương tính được làm tiêu chuẩn tham chiếu",
                   (_DE_MUC_SO + r"(?:tiêu chuẩn tham chiếu|xét nghiệm|quy trình)", _DE_MUC_SO + r"thiết kế",
                    r"(?i)^#+.*(?:tiêu chuẩn tham chiếu|quy trình|xét nghiệm)"),
                   "Chỉ người có kết quả xét nghiệm chỉ điểm dương tính mới được làm tiêu chuẩn tham chiếu."),
    "prediction": ("tk_khong_kiem_dinh", "đánh giá mô hình trên chính dữ liệu xây dựng, không kiểm định",
                   (_DE_MUC_SO + r"(?:phát triển mô hình|xây dựng mô hình|kiểm định|đánh giá mô hình)",
                    _DE_MUC_SO + r"thiết kế", _DE_MUC_SO + r"biến dự báo",
                    r"(?i)^#+.*(?:xây dựng mô hình|kiểm định)"),
                   "Mô hình được xây dựng và đánh giá hiệu năng trên cùng toàn bộ dữ liệu, không kiểm định nội hay "
                   "ngoại."),
    "sr_ma": ("tk_tim_hep_chon_ket_qua", "chỉ tìm một cơ sở dữ liệu và chỉ nhận nghiên cứu có ý nghĩa thống kê",
              (_DE_MUC_SO + r"(?:chiến lược tìm|nguồn dữ liệu|tìm kiếm|tiêu chuẩn chọn)",
               r"(?i)^#+.*(?:chiến lược tìm|nguồn dữ liệu|tìm kiếm|tiêu chuẩn chọn)"),
              "Chỉ tìm trên PubMed bằng tiếng Anh và chỉ đưa vào các nghiên cứu có kết quả có ý nghĩa thống kê."),
    "qualitative": ("tk_co_mau_thong_ke", "tính cỡ mẫu định tính bằng công thức thống kê",
                    (_DE_MUC_SO + r"(?:cỡ mẫu|chọn mẫu|người tham gia)",
                     r"(?i)^#+.*(?:cỡ mẫu|chọn mẫu|người tham gia)"),
                    "Số người được phỏng vấn tính bằng công thức ước lượng một tỷ lệ với sai số 5% và độ tin cậy 95%."),
}
SO_LOI_CAI_TOI_THIEU = 5         # bản cài lỗi có < 5 lỗi (thiếu neo) ⇒ hiệu chuẩn KHÔNG hợp lệ, không phải «đạt»


def bo_loi_cai(loai: str = "de_cuong", thiet_ke: str = "") -> List[Tuple[str, str, Any, str, bool]]:
    """(mã, mô tả, neo, câu, đặc thù thiết kế?) theo loại tài liệu; đề cương có thêm lỗi đặc thù của thiết kế."""
    goc = {"de_cuong": LOI_CAI, "sap": LOI_CAI_SAP, "ban_thao": LOI_CAI_BAN_THAO, "bao_cao": LOI_CAI_BAO_CAO}[loai]
    ds = [(m, mo, neo, cau, False) for m, mo, neo, cau in goc]
    dt_ = LOI_CAI_THIET_KE.get(chuan_hoa_thiet_ke(thiet_ke))
    if loai == "de_cuong" and dt_:
        ds.append((*dt_, True))
    return ds


def cai_loi(van: str, loai: str = "de_cuong", thiet_ke: str = "") -> Tuple[str, List[Dict[str, Any]]]:
    """Chèn mỗi lỗi một dòng sau neo đầu tiên còn chưa dùng; trả (văn bản mới, đáp án theo SỐ DÒNG mới)."""
    dong = van.splitlines()
    chen: List[Tuple[int, str, str, str, bool]] = []
    for ma, mo_ta, neo, cau, dac_thu in bo_loi_cai(loai, thiet_ke):
        for mau in (neo,) if isinstance(neo, str) else neo:
            i = next((k for k, d in enumerate(dong) if re.search(mau, d) and all(k != c[0] for c in chen)), None)
            if i is not None:
                chen.append((i, ma, mo_ta, cau, dac_thu))
                break
    dap_an = []
    for lech, (i, ma, mo_ta, cau, dac_thu) in enumerate(sorted(chen)):
        vi_tri = i + 1 + lech  # vị trí trong danh sách SAU khi đã chèn các lỗi phía trước
        dong.insert(vi_tri, cau)
        dap_an.append({"ma": ma, "mo_ta": mo_ta, "dong": vi_tri + 1, "cau": cau, "dac_thu_thiet_ke": dac_thu})
    return "\n".join(dong) + "\n", dap_an


def cham_hieu_chuan(dap_an: Sequence[Dict[str, Any]], st: Dict[str, Any]) -> Dict[str, Any]:
    """Một lỗi cài được tính là BẮT khi có vấn đề hội đồng giữ (sau chủ tịch) nằm trong ±3 dòng quanh dòng cài. Ghép
    MỘT–MỘT: mỗi vấn đề chỉ được tính cho một lỗi cài (gần nhất) — hai lỗi cài sát nhau không được «bắt» bằng một nhận
    xét (đo được ở test: ghép nhiều–một thổi phồng độ nhạy)."""
    van_de = tong_hop(st)["van_de"]
    da_dung: set = set()
    ket = []
    for a in sorted(dap_an, key=lambda x: int(x["dong"])):
        ung = sorted((abs(int(f["dong"]) - int(a["dong"])), i) for i, f in enumerate(van_de)
                     if i not in da_dung and abs(int(f["dong"]) - int(a["dong"])) <= CUA_SO_DONG)
        if ung:
            da_dung.add(ung[0][1])
        ket.append({**a, "bat": bool(ung), "boi": [van_de[ung[0][1]]["thanh_vien"]] if ung else [],
                    "van_de_id": van_de[ung[0][1]].get("id") if ung else None})
    bat = sum(1 for k in ket if k["bat"])
    dac_thu = [k for k in ket if k.get("dac_thu_thiet_ke")]
    return {"so_loi_cai": len(ket), "bat": bat, "do_nhay": round(bat / len(ket), 3) if ket else None, "chi_tiet": ket,
            "bat_dac_thu": (all(k["bat"] for k in dac_thu) if dac_thu else None),
            "van_de_ngoai_loi_cai": sum(1 for f in van_de if all(abs(int(f["dong"]) - int(a["dong"])) > CUA_SO_DONG
                                                                    for a in dap_an))}


# ── QC-HDKH-3.0: đo BÁO NHẦM (độ chính xác của nhận xét) bằng TRỌNG TÀI ĐỘC LẬP ─────────────────────────────────────
# Độ nhạy (bắt lỗi cài) chưa đủ: hội đồng còn nêu nhiều vấn đề NGOÀI lỗi cài mà chưa ai đối chiếu đúng/sai. Trọng tài
# (model KHÁC hội đồng, ngữ cảnh mới, không biết ai nêu) phán từng nhận xét. Chính trọng tài cũng bị kiểm: trộn mù ĐỐI
# CHỨNG DƯƠNG (nhận xét đã bắt đúng lỗi cài ⇒ phải «dung») và ĐỐI CHỨNG ÂM (máy dựng nhận xét SAI: «không trình bày X»
# trong khi mục X có nội dung ⇒ phải «sai»). Trọng tài sai đối chứng ⇒ phép đo không hợp lệ, không phải «đạt».
TRONG_TAI_MODEL = "claude-fable-5-2"
MAX_TOKENS_TRONG_TAI = 32000
TRONG_TAI_KIEM_SOAT_TOI_THIEU = 0.9   # tỷ lệ đối chứng trọng tài phán đúng (≥ 4 đối chứng)
DO_CHINH_XAC_TOI_THIEU = 0.8          # nhận xét ngoài lỗi cài: đúng/(đúng+sai) — ngưỡng VẬN HÀNH, không phải chuẩn
KHONG_RO_TOI_DA = 0.5                 # trọng tài «không rõ» quá nửa ⇒ không đo được
SO_DOI_CHUNG_AM = 4
CHU_DE_DOI_CHUNG: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "de_cuong": (("cách tính cỡ mẫu", r"cỡ mẫu"), ("tiêu chuẩn lựa chọn đối tượng", r"tiêu chuẩn (?:lựa )?chọn"),
                 ("tiêu chuẩn loại trừ", r"tiêu chuẩn loại trừ"),
                 ("phương pháp xử lý và phân tích số liệu", r"(?:xử lý|phân tích) (?:số liệu|dữ liệu|thống kê)"),
                 ("vấn đề đạo đức trong nghiên cứu", r"đạo đức"), ("biến số và chỉ số nghiên cứu", r"biến số|chỉ số")),
    "sap": (("quần thể phân tích", r"quần thể phân tích"), ("định nghĩa kết cục", r"kết cục"),
            ("cách xử lý dữ liệu thiếu", r"dữ liệu thiếu"), ("phân tích độ nhạy", r"độ nhạy"),
            ("cách xử lý đa so sánh", r"đa so sánh"), ("phần mềm phân tích", r"phần mềm")),
    "ban_thao": (("phương pháp nghiên cứu", r"phương pháp"), ("kết quả nghiên cứu", r"kết quả"),
                 ("phần bàn luận", r"bàn luận"), ("kết luận", r"kết luận"),
                 ("danh mục tài liệu tham khảo", r"tài liệu tham khảo")),
}
CHU_DE_DOI_CHUNG["bao_cao"] = CHU_DE_DOI_CHUNG["ban_thao"]
_DE_MUC_RE = re.compile(r"^#+\s")


def doi_chung_am(van: str, loai: str = "de_cuong") -> List[Dict[str, Any]]:
    """Nhận xét SAI do máy dựng: «tài liệu hoàn toàn không trình bày X» — chỉ dựng khi đề mục X có ≥ 2 dòng nội dung."""
    dong, ra = van.splitlines(), []
    for chu_de, mau in CHU_DE_DOI_CHUNG[loai]:
        for i, d in enumerate(dong):
            if not (_DE_MUC_RE.match(d) and re.search(mau, d, re.IGNORECASE)):
                continue
            j, noi_dung = i + 1, 0
            while j < len(dong) and not _DE_MUC_RE.match(dong[j]):
                noi_dung += bool(dong[j].strip())
                j += 1
            if noi_dung >= 2:
                ra.append({"nhom": "kiem_soat_am", "muc_phieu": "2", "muc_do": "can_sua", "dong": i + 1,
                           "trich": d.strip()[:120], "van_de": f"Tài liệu hoàn toàn không trình bày {chu_de}.",
                           "de_xuat": f"Bổ sung phần {chu_de}.", "chuan": ""})
                break
        if len(ra) >= SO_DOI_CHUNG_AM:
            break
    return ra


def lap_muc_bao_nham(st: Dict[str, Any], kq_cham: Dict[str, Any], van: str, loai: str) -> List[Dict[str, Any]]:
    """Mọi vấn đề hội đồng giữ (đã ghép lỗi cài ⇒ đối chứng dương; còn lại ⇒ cần phán) + đối chứng âm; trộn tất định,
    mã mù M01…"""
    khop = {k.get("van_de_id") for k in kq_cham.get("chi_tiet") or [] if k.get("bat")}
    muc = [{"nhom": "kiem_soat_duong" if f.get("id") in khop else "nghi_van", "goc": f.get("id"),
            **{k: f.get(k) for k in ("muc_phieu", "muc_do", "dong", "trich", "van_de", "de_xuat", "chuan")}}
           for f in tong_hop(st)["van_de"]]
    muc += doi_chung_am(van, loai)
    muc.sort(key=lambda m: hashlib.sha256((st["sha"] + json.dumps(m, ensure_ascii=False, sort_keys=True))
                                          .encode("utf-8")).hexdigest())
    for k, m in enumerate(muc, 1):
        m["id"] = f"M{k:02d}"
    return muc


def loi_nhan_trong_tai(muc: Sequence[Dict[str, Any]], loai: str = "de_cuong") -> str:
    gon = [{k: m.get(k) for k in ("id", "muc_phieu", "muc_do", "dong", "trich", "van_de", "de_xuat", "chuan")}
           for m in muc]
    return ("VAI CỦA BẠN: TRỌNG TÀI ĐỘC LẬP thẩm định CHẤT LƯỢNG NHẬN XÉT của một hội đồng về "
            f"{LOAI_TAI_LIEU[loai]['ten']} ở trên. Bạn không thuộc hội đồng và không biết nhận xét nào do ai nêu.\n"
            "Với TỪNG nhận xét, phán một trong ba:\n"
            "- «dung»: tài liệu thật sự có vấn đề như nhận xét nêu (theo chuẩn áp dụng hoặc nguyên tắc phương pháp "
            "được thừa nhận) — nêu lý do.\n"
            "- «sai»: nhận xét không đúng, kèm «co_so»: «tai_lieu_da_dap_ung» (trích NGUYÊN VĂN đoạn đáp ứng kèm số "
            "dòng — máy đối chiếu, không khớp thì phán quyết thành «khong_ro») hoặc «chuan_khong_doi» (giải thích vì "
            "sao chuẩn/nguyên tắc không đòi điều đó).\n"
            "- «khong_ro»: không đủ căn cứ để phán.\n"
            "Phán theo nội dung tài liệu, không theo giọng văn của nhận xét; không ghi thông tin định danh cá nhân.\n"
            f"NHẬN XÉT:\n{json.dumps(gon, ensure_ascii=False, indent=1)}\n"
            "Trả về DUY NHẤT JSON: " + json.dumps({"phan_dinh": [
                {"id": "M01", "ket_qua": "dung|sai|khong_ro", "co_so": "tai_lieu_da_dap_ung|chuan_khong_doi|",
                 "dong": 12, "trich": "…", "ly_do": "…"}]}, ensure_ascii=False))


def xac_minh_trong_tai(dl: Any, muc: Sequence[Dict[str, Any]], van: str) -> Dict[str, Dict[str, Any]]:
    """Phán quyết đã máy kiểm theo mã M…; thiếu/không hợp lệ/«sai» không chứng minh được ⇒ «khong_ro»."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("phán quyết trọng tài không phải đối tượng JSON")
    cac_dong = van.splitlines()
    pq = {str(x.get("id")): x for x in (dl.get("phan_dinh") or []) if isinstance(x, dict)}
    ra: Dict[str, Dict[str, Any]] = {}
    for m in muc:
        x = pq.get(m["id"]) or {}
        kq, co_so, ly = str(x.get("ket_qua") or ""), str(x.get("co_so") or ""), str(x.get("ly_do") or "").strip()
        try:
            dong = int(x.get("dong"))
        except (TypeError, ValueError):
            dong = 0
        ghi = ""
        if kq not in ("dung", "sai", "khong_ro"):
            kq, ghi = "khong_ro", "thiếu phán quyết hợp lệ"
        elif kq == "sai" and co_so == "tai_lieu_da_dap_ung" and not _trong_cua_so(str(x.get("trich") or ""), dong,
                                                                                  cac_dong):
            kq, ghi = "khong_ro", f"«sai» nhưng trích không có nguyên văn quanh dòng {dong}"
        elif kq == "sai" and co_so == "chuan_khong_doi" and not ly:
            kq, ghi = "khong_ro", "«sai — chuẩn không đòi» mà không nêu lý do"
        elif kq == "sai" and co_so not in ("tai_lieu_da_dap_ung", "chuan_khong_doi"):
            kq, ghi = "khong_ro", "«sai» không có cơ sở hợp lệ"
        ra[m["id"]] = {"ket_qua": kq, "co_so": co_so, "dong": dong, "trich": str(x.get("trich") or "")[:300],
                       "ly_do": ly[:600], "ghi_may": ghi}
    return ra


def _wilson(k: int, n: int, z: float = 1.959964) -> Optional[List[float]]:
    if n <= 0:
        return None
    ph = k / n
    tam = (ph + z * z / (2 * n)) / (1 + z * z / n)
    nua = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return [round(max(0.0, tam - nua), 3), round(min(1.0, tam + nua), 3)]


def cham_bao_nham(muc: Sequence[Dict[str, Any]], pd: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Độ hợp lệ của trọng tài (trên đối chứng) và độ chính xác nhận xét ngoài lỗi cài (Wilson 95%)."""
    ks = [m for m in muc if m["nhom"] in ("kiem_soat_duong", "kiem_soat_am")]
    dung_ks = sum(1 for m in ks if pd[m["id"]]["ket_qua"] == ("dung" if m["nhom"] == "kiem_soat_duong" else "sai"))
    nghi = [m for m in muc if m["nhom"] == "nghi_van"]
    d = sum(1 for m in nghi if pd[m["id"]]["ket_qua"] == "dung")
    sai = sum(1 for m in nghi if pd[m["id"]]["ket_qua"] == "sai")
    kr = len(nghi) - d - sai
    hop_le = len(ks) >= 4 and dung_ks / len(ks) >= TRONG_TAI_KIEM_SOAT_TOI_THIEU
    do_chinh_xac = round(d / (d + sai), 3) if d + sai else None
    du_phan = not nghi or kr / len(nghi) <= KHONG_RO_TOI_DA
    dat = hop_le and du_phan and (do_chinh_xac is None or do_chinh_xac >= DO_CHINH_XAC_TOI_THIEU)
    ly = ("trọng tài sai đối chứng — phép đo không hợp lệ" if not hop_le else
          "trọng tài không phán được quá nửa nhận xét — không đo được" if not du_phan else
          f"độ chính xác {do_chinh_xac} < {DO_CHINH_XAC_TOI_THIEU}" if not dat else "đạt")
    return {"so_doi_chung": len(ks), "doi_chung_dung": dung_ks, "trong_tai_hop_le": hop_le,
            "so_nhan_xet": len(nghi), "dung": d, "sai": sai, "khong_ro": kr, "do_chinh_xac": do_chinh_xac,
            "khoang_tin_cay_95": _wilson(d, d + sai), "dat": dat, "ly_do": ly,
            "sai_chi_tiet": [{"id": m["id"], "goc": m.get("goc"), "van_de": m.get("van_de"),
                              "phan_quyet": pd[m["id"]]} for m in nghi if pd[m["id"]]["ket_qua"] == "sai"],
            "doi_chung_sai": [{"id": m["id"], "nhom": m["nhom"], "phan_quyet": pd[m["id"]]} for m in ks
                              if pd[m["id"]]["ket_qua"] != ("dung" if m["nhom"] == "kiem_soat_duong" else "sai")]}


def _do_bao_nham(goc: Path, out_dir: Path, study: str, loai: str, goi_api: bool, client: Any, model: str,
                 trong_tai: str = "agent") -> int:
    hc_dir = thu_muc_hd(out_dir) / "hieu_chuan" / loai
    da, kq_cham = _doc_st(hc_dir / "dap_an.json"), _doc_st(hc_dir / "ket_qua.json")
    if not da or not kq_cham:
        print("❌ chưa hiệu chuẩn xong (cần «hieu-chuan --tao», họp bản cài lỗi, «hieu-chuan --cham»)", file=sys.stderr)
        return 3
    st = _doc_st(tep_trang_thai(out_dir, da["sha"]))
    if not st or st.get("buoc") != "xong" or (st.get("quy_che") or {}).get("sha") != sha_ke_hoach(model):
        print("⛔ phiên họp bản cài lỗi chưa xong hoặc không cùng quy chế hiện hành", file=sys.stderr)
        return 1
    van = Path(da["tep"]).read_text(encoding="utf-8")
    p_tt = hc_dir / "bao_nham_trang_thai.json"
    tt = _doc_st(p_tt)
    if not tt or tt.get("sha_quy_che") != sha_ke_hoach(model) or tt.get("sha") != da["sha"]:
        tt = {"sha": da["sha"], "sha_quy_che": sha_ke_hoach(model), "muc": lap_muc_bao_nham(st, kq_cham, van, loai),
              "batch": None, "so_lan_nop_lai": 0, "model_trong_tai": TRONG_TAI_MODEL}
    if trong_tai == "agent":   # 4.0: trọng tài là agent Claude Code của hệ — không tốn tín dụng API
        if not tt.get("viec_trong_tai"):
            # làm mù (22/11/2026): phiếu ở ngoài cây hieu_chuan (không cạnh dap_an.json, đường dẫn không lộ)
            tm_tt = thu_muc_hd(out_dir) / "viec_agent" / f"bao_nham_{loai}_{da['sha'][:12]}"
            tl = tm_tt / f"tra_loi_trong_tai_{TRONG_TAI_AGENT}.json"
            tt["viec_trong_tai"] = ghi_viec(tm_tt, "trong_tai", TRONG_TAI_AGENT, (
                f"Bạn là agent `{TRONG_TAI_AGENT}` (ngữ cảnh mới, không tham gia hội đồng). "
                f"Tài liệu: `{tep_cho_agent(da['tep'], tm_tt)}` "
                "(số dòng tính từ 1).\n" + loi_nhan_trong_tai(tt["muc"], loai).replace("ở trên", "nêu trên")
                + f"\nGhi DUY NHẤT JSON trên vào `{tl}`; không ghi tệp khác."), {"muc": _mu(tt["muc"])})
            _ghi_json(p_tt, tt)
        p_tl = Path(tt["viec_trong_tai"]["tra_loi"])
        if not p_tl.exists():
            print(f"🤝 Chờ agent {TRONG_TAI_AGENT} — «viec-agent» để xem phiếu việc.")
            return CHO_AGENT
        try:
            pd = xac_minh_trong_tai(json.loads(p_tl.read_text(encoding="utf-8")), tt["muc"], van)
        except (OSError, ValueError, API.LoiApi) as exc:
            print(f"❌ trả lời trọng tài agent không đọc được: {exc} — xoá tệp trả lời và giao lại.", file=sys.stderr)
            return 1
        kq = cham_bao_nham(tt["muc"], pd)
        kq.update(sha=da["sha"], sha_quy_che=sha_ke_hoach(model), quy_che=PHIEN_BAN_QUY_CHE, loai=loai,
                  model_trong_tai=f"agent:{TRONG_TAI_AGENT}", ngay=dt.date.today().isoformat())
        tt["phan_dinh"] = pd
        _ghi_json(p_tt, tt)
        _ghi_json(hc_dir / "bao_nham.json", kq)
        print(f"⚖️ Trọng tài agent {TRONG_TAI_AGENT}: đối chứng {kq['doi_chung_dung']}/{kq['so_doi_chung']}; "
              f"{kq['dung']} đúng · {kq['sai']} sai · {kq['khong_ro']} không rõ ⇒ độ chính xác {kq['do_chinh_xac']} — "
              f"{kq['ly_do']}.")
        return 0 if kq["dat"] else 1
    cid = f"tt_bn_{da['sha'][:8]}"
    yc = [(cid, tham_so_yeu_cau(khoi_chung(study, Path(da["tep"]).name, van, st["ho_so"], loai),
                                loi_nhan_trong_tai(tt["muc"], loai), TRONG_TAI_MODEL, MAX_TOKENS_TRONG_TAI))]
    if not goi_api:
        n = {g: sum(1 for m in tt["muc"] if m["nhom"] == g) for g in ("nghi_van", "kiem_soat_duong", "kiem_soat_am")}
        print(f"(chạy khô) trọng tài {TRONG_TAI_MODEL} sẽ phán {n['nghi_van']} nhận xét + {n['kiem_soat_duong']} đối "
              f"chứng dương + {n['kiem_soat_am']} đối chứng âm — thêm --goi-api (tính phí).")
        return 0
    if not tt["batch"]:
        tt["batch"] = API.nop_batch(yc, client=client, nguon=CONG_CU)
        _ghi_json(p_tt, tt)
        print(f"📨 Đã nộp batch trọng tài: {tt['batch']} ({len(tt['muc'])} mục).")
        return 4
    if API.trang_thai_batch(tt["batch"], client=client)["trang_thai"] != "ended":
        print(f"⏳ Batch trọng tài {tt['batch']} đang xử lý — chạy lại sau.")
        return 4
    ket = API.doc_ket_qua_batch(tt["batch"], client=client, nguon=CONG_CU)
    try:
        tho = API.van_ban_ket_qua_batch(ket.get(cid, {"loai": "thieu"}), MAX_TOKENS_TRONG_TAI)
        tt["tho"] = tho
        pd = xac_minh_trong_tai(API.doc_json(tho), tt["muc"], van)
    except API.LoiApi as exc:
        if tt["so_lan_nop_lai"] < SO_LAN_NOP_LAI_BIEN_TAP:   # lỗi KỸ THUẬT ⇒ nộp lại, không phải phán quyết
            tt["so_lan_nop_lai"] += 1
            tt.setdefault("loi", []).append(str(exc)[:200])
            tt["batch"] = API.nop_batch(yc, client=client, nguon=CONG_CU)
            _ghi_json(p_tt, tt)
            print(f"⚠️ Phản hồi trọng tài không đọc được — đã nộp lại lần {tt['so_lan_nop_lai']}: {tt['batch']}")
            return 4
        _ghi_json(p_tt, tt)
        print(f"❌ trọng tài hỏng sau {SO_LAN_NOP_LAI_BIEN_TAP} lần nộp lại: {exc}", file=sys.stderr)
        return 1
    kq = cham_bao_nham(tt["muc"], pd)
    kq.update(sha=da["sha"], sha_quy_che=sha_ke_hoach(model), quy_che=PHIEN_BAN_QUY_CHE, loai=loai,
              model_trong_tai=TRONG_TAI_MODEL, ngay=dt.date.today().isoformat())
    tt["phan_dinh"] = pd
    _ghi_json(p_tt, tt)
    _ghi_json(hc_dir / "bao_nham.json", kq)
    ci = kq["khoang_tin_cay_95"]
    print(f"⚖️ Trọng tài {TRONG_TAI_MODEL}: đối chứng {kq['doi_chung_dung']}/{kq['so_doi_chung']} đúng "
          f"({'hợp lệ' if kq['trong_tai_hop_le'] else 'KHÔNG hợp lệ'}); nhận xét ngoài lỗi cài: {kq['dung']} đúng · "
          f"{kq['sai']} sai · {kq['khong_ro']} không rõ ⇒ độ chính xác {kq['do_chinh_xac']}"
          + (f" (KTC 95% {ci[0]}–{ci[1]})" if ci else "") + f" — {kq['ly_do']}.")
    return 0 if kq["dat"] else 1


# ── QC-HDKH-4.0: GIAO VIỆC CHO AGENT CLAUDE CODE (bác sĩ chọn «kết hợp có trọng tâm», 22/11/2026) ─────────────────
# API chấm độc lập (rẻ, song song) — nhưng nhận xét cần TRA CỨU/TÍNH LẠI, việc BIÊN TẬP và CHỐT CUỐI giao cho agent của
# hệ chạy trong Claude Code (có công cụ: PubMed, run_g3_auto, check_citation_retraction, bộ chấm cổng…). Công cụ này
# KHÔNG gọi được agent: nó ghi PHIẾU VIỆC + lời dặn soạn sẵn rồi trả mã 5; Claude Code giao từng phiếu cho đúng agent
# (subagent_type = tên agent); agent ghi JSON trả lời vào đường dẫn đã định; lượt chạy sau công cụ MÁY-KIỂM câu trả lời
# (trích nguyên văn ±3 dòng, căn cứ công cụ phải có lệnh + kết quả, agent phải phán đúng đối chứng âm) rồi mới áp.
CHO_AGENT = 5
TAC_NHAN_BIEN_TAP: Dict[str, str] = {"pb1": "thiet-ke-nghien-cuu", "pb2": "viet-ban-thao",
                                     "uv_tk": "co-mau-nghien-cuu", "uv_dd": "dao-duc-dang-ky",
                                     "uv_tl": "viet-ban-thao", "uv_kt": "kinh-te-y-te"}
CONG_CU_GOI_Y: Dict[str, str] = {
    "kiem-chung-trich-dan": "python3 tools/check_citation_retraction.py --pmid <PMID…>; biên nhận A12 trong thư mục đề "
                            "tài; connector PubMed để đối chiếu nội dung",
    "co-mau-nghien-cuu": "python3 tools/run_g3_auto.py --study <mã> (chạy khô) / G3_checkpoint.json; "
                         "python3 tools/g3_quality_gate.py --study <mã>",
    "phan-tich-thong-ke": "G4_A5_SAP_FINAL + python3 tools/g4_quality_gate.py --study <mã>",
    "thiet-ke-nghien-cuu": "python3 tools/g1_quality_gate.py / g4_quality_gate.py --study <mã>; "
                           "python3 tools/nhat_quan_xuyen_cong.py --study <mã>",
    "dao-duc-dang-ky": "python3 tools/g2_quality_gate.py --study <mã>",
    "tong-quan-y-van": "connector PubMed/Cochrane để đối chiếu khẳng định với nguồn",
    "viet-ban-thao": "python3 tools/kiem_de_cuong_nop_hoi_dong.py / kiem_ban_thao_tap_chi.py (luật K)",
    "tham-dinh-dau-ra": "đọc tài liệu + biên bản; luật R1–R7 của chính agent",
}
CO_SO_SAI = ("tai_lieu_da_dap_ung", "cong_cu", "chuan_khong_doi")
_KHOA_MU = ("id", "muc_phieu", "muc_do", "dong", "trich", "van_de", "de_xuat", "chuan")


def _mu(muc: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bản MÙ của danh sách mục giao agent: bỏ «nhom» (đối chứng hay nhận xét thật) và «goc» (id hội đồng)."""
    return [{k: m.get(k) for k in _KHOA_MU} for m in muc]


def _ma_tv_theo_tac_nhan(st: Dict[str, Any]) -> Dict[str, str]:
    return {t["ma"]: (t.get("tac_nhan") or [""])[0] for t in _ds_tv(st)}


def thu_muc_viec(out_dir: Path, st: Dict[str, Any]) -> Path:
    return thu_muc_hd(out_dir) / "viec_agent" / f"{st['sha'][:12]}_v{st.get('vong', 1)}"


def tep_cho_agent(tep: str, thu_muc: Path) -> str:
    """Đường dẫn tài liệu ghi vào phiếu việc của agent.

    Bản cài lỗi của lượt hiệu chuẩn (nằm trong thư mục ``hieu_chuan``) được chép sang thư mục phiếu việc dưới tên
    TRUNG TÍNH ``TAI_LIEU_<sha8>.md`` — nội dung, số dòng y hệt. Đo thật 22/11/2026: tên «BAN_CAI_LOI_…» và tệp
    ``dap_an.json`` nằm cạnh làm agent biết đang hiệu chuẩn và đối chiếu với đề cương gốc để tìm câu cài ⇒ lớp agent
    được đo dễ hơn khi dùng thật. Tài liệu thật (ngoài ``hieu_chuan``) giữ nguyên đường dẫn."""
    goc = Path(tep)
    if "hieu_chuan" not in goc.resolve().parts:
        return tep
    van = goc.read_bytes()
    dich = thu_muc / f"TAI_LIEU_{hashlib.sha256(van).hexdigest()[:8]}{goc.suffix}"
    thu_muc.mkdir(parents=True, exist_ok=True)
    if not dich.exists() or dich.read_bytes() != van:
        tam = dich.with_suffix(dich.suffix + ".tam")
        tam.write_bytes(van)
        os.replace(tam, dich)
    return str(dich)


def lap_viec_tham_dinh(st: Dict[str, Any], van: str, ds: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Nhóm nhận xét theo agent SỞ HỮU chuyên môn của ghế đã nêu; mỗi nhóm trộn mù ≥ 1 đối chứng âm (nhận xét sai do
    máy dựng). Mã mù A01…; ánh xạ về id hội đồng chỉ lưu trong trạng thái."""
    chu = _ma_tv_theo_tac_nhan(st)
    nhom: Dict[str, List[Dict[str, Any]]] = {}
    for f in ds:
        nhom.setdefault(chu.get(f.get("thanh_vien"), "") or "thiet-ke-nghien-cuu", []).append(
            {"nhom": "nhan_xet", "goc": f["id"],
             **{k: f.get(k) for k in ("muc_phieu", "muc_do", "dong", "trich", "van_de", "de_xuat", "chuan")}})
    am = doi_chung_am(van, st.get("loai", "de_cuong"))
    for i, ten in enumerate(sorted(nhom)):
        if am:
            nhom[ten].append(dict(am[i % len(am)]))
    k = 0
    for ten in sorted(nhom):
        nhom[ten].sort(key=lambda m: hashlib.sha256((st["sha"] + ten + json.dumps(m, ensure_ascii=False,
                                                                                 sort_keys=True)).encode()).hexdigest())
        for m in nhom[ten]:
            k += 1
            m["id"] = f"A{k:02d}"
    return nhom


def loi_nhan_agent_tham_dinh(ten: str, muc: Sequence[Dict[str, Any]], tep: str, loai: str, study: str,
                             tra_loi: str) -> str:
    gon = [{k: m.get(k) for k in ("id", "muc_phieu", "muc_do", "dong", "trich", "van_de", "de_xuat", "chuan")}
           for m in muc]
    goi_y = CONG_CU_GOI_Y.get(ten, "công cụ hệ")
    return (f"Bạn là agent `{ten}` của hệ, THẨM ĐỊNH nhận xét của Hội đồng Khoa học máy về "
            f"{LOAI_TAI_LIEU[loai]['ten']} của đề tài «{study}». Đọc tài liệu: `{tep}` (số dòng tính từ 1 theo tệp).\n"
            f"Dùng công cụ của hệ khi nhận xét cần tra cứu hoặc tính lại — gợi ý: {goi_y}.\n"
            "Với TỪNG mục dưới đây phán: «dung» (tài liệu thật sự có vấn đề như nêu — nêu căn cứ), «sai» kèm «co_so» "
            "là "
            "«tai_lieu_da_dap_ung» (trích NGUYÊN VĂN đoạn đáp ứng + số dòng — máy đối chiếu ±3 dòng), «cong_cu» (ghi "
            "«lenh» và «ket_qua_cong_cu» rút gọn — chép đúng đầu ra) hoặc «chuan_khong_doi» (giải thích), hoặc "
            "«khong_ro». Không biết mục nào do ai nêu; không sửa tài liệu; không ghi tệp nào khác; không PII.\n"
            f"MỤC:\n{json.dumps(gon, ensure_ascii=False, indent=1)}\n"
            f"Ghi DUY NHẤT JSON vào `{tra_loi}`: " + json.dumps({"phan_dinh": [
                {"id": "A01", "ket_qua": "dung|sai|khong_ro", "co_so": "|".join(CO_SO_SAI), "dong": 12,
                 "trich": "…", "lenh": "…", "ket_qua_cong_cu": "…", "ly_do": "…"}]}, ensure_ascii=False))


def xac_minh_agent(dl: Any, muc: Sequence[Dict[str, Any]], van: str) -> Dict[str, Dict[str, Any]]:
    """Như trọng tài, thêm cơ sở «cong_cu» (bắt buộc có lệnh + kết quả; ghi nguyên văn vào biên bản)."""
    if not isinstance(dl, dict):
        raise API.KetQuaHong("trả lời agent không phải đối tượng JSON")
    pd = xac_minh_trong_tai({"phan_dinh": [dict(x, co_so=("chuan_khong_doi" if x.get("co_so") == "cong_cu"
                                                         else x.get("co_so")), ly_do=(x.get("ly_do") or "")
                                                + (" · lệnh: " + str(x.get("lenh")) if x.get("lenh") else ""))
                                           for x in dl.get("phan_dinh") or [] if isinstance(x, dict)]}, muc, van)
    goc = {str(x.get("id")): x for x in dl.get("phan_dinh") or [] if isinstance(x, dict)}
    for m in muc:
        x = goc.get(m["id"]) or {}
        if x.get("ket_qua") == "sai" and x.get("co_so") == "cong_cu":
            if not str(x.get("lenh") or "").strip() or not str(x.get("ket_qua_cong_cu") or "").strip():
                pd[m["id"]].update(ket_qua="khong_ro", ghi_may="«sai — công cụ» thiếu lệnh hoặc kết quả công cụ")
            else:
                pd[m["id"]].update(co_so="cong_cu", lenh=str(x["lenh"])[:300],
                                   ket_qua_cong_cu=str(x["ket_qua_cong_cu"])[:600])
    return pd


def ghi_viec(thu_muc: Path, loai_viec: str, ten: str, loi_nhan: str, du_lieu: Any) -> Dict[str, str]:
    thu_muc.mkdir(parents=True, exist_ok=True)
    tl = thu_muc / f"tra_loi_{loai_viec}_{ten}.json"
    _ghi_van(thu_muc / f"viec_{loai_viec}_{ten}.md", loi_nhan + "\n")
    _ghi_json(thu_muc / f"viec_{loai_viec}_{ten}.json", du_lieu)
    return {"agent": ten, "loai_viec": loai_viec, "loi_nhan": str(thu_muc / f"viec_{loai_viec}_{ten}.md"),
            "tra_loi": str(tl)}


def buoc_tham_dinh_agent(st: Dict[str, Any], van: str, out_dir: Path) -> int:
    """Giao thẩm định nhận xét (đã qua chủ tịch) cho agent sở hữu; đủ trả lời ⇒ máy kiểm, áp, sang «xong»."""
    tm = thu_muc_viec(out_dir, st)
    if not st.get("viec_tham_dinh"):
        ct = st.get("chu_tich") or {}
        ds = list(ct.get("giu") or [])
        if not ds:
            st["buoc"] = "xong"
            return 0
        nhom = lap_viec_tham_dinh(st, van, ds)
        st["viec_tham_dinh"] = {ten: {"muc": muc, **ghi_viec(tm, "tham_dinh", ten, loi_nhan_agent_tham_dinh(
            ten, muc, tep_cho_agent(st["tep"], tm), st.get("loai", "de_cuong"), st["study"],
            str(tm / f"tra_loi_tham_dinh_{ten}.json")), {"muc": _mu(muc)})} for ten, muc in nhom.items()}
    thieu = [ten for ten, v in st["viec_tham_dinh"].items() if not Path(v["tra_loi"]).exists()]
    if thieu:
        print(f"🤝 Chờ agent thẩm định: {', '.join(thieu)} — chạy «viec-agent» để xem phiếu việc.")
        return CHO_AGENT
    ct = st["chu_tich"]
    theo_id = {f["id"]: f for f in ct.get("giu") or []}
    bac, ghi = set(), {}
    for ten, v in st["viec_tham_dinh"].items():
        try:
            pd = xac_minh_agent(json.loads(Path(v["tra_loi"]).read_text(encoding="utf-8")), v["muc"], van)
        except (OSError, ValueError, API.LoiApi) as exc:
            ghi[ten] = {"hop_le": False, "ly_do": f"trả lời không đọc được: {exc}"[:200]}
            continue
        am = [m for m in v["muc"] if m["nhom"] == "kiem_soat_am"]
        hop_le = all(pd[m["id"]]["ket_qua"] == "sai" for m in am)
        ghi[ten] = {"hop_le": hop_le, "phan_dinh": pd,
                    "ly_do": "đạt đối chứng âm" if hop_le else "phán sai đối chứng âm — không áp phán quyết của agent"}
        if hop_le:
            bac |= {m["goc"] for m in v["muc"] if m["nhom"] == "nhan_xet" and pd[m["id"]]["ket_qua"] == "sai"}
    for gid in bac:
        f = theo_id.get(gid)
        if f:
            ten = next(t for t, v in st["viec_tham_dinh"].items() if any(m.get("goc") == gid for m in v["muc"]))
            m = next(m for m in st["viec_tham_dinh"][ten]["muc"] if m.get("goc") == gid)
            ct.setdefault("loai_agent", []).append({**f, "agent": ten,
                                                    "phan_quyet_agent": ghi[ten]["phan_dinh"][m["id"]]})
    ct["giu"] = [f for f in ct.get("giu") or [] if f["id"] not in bac]
    st["tham_dinh_agent"] = ghi
    st["buoc"] = "xong"
    print(f"✅ Agent thẩm định xong: bác {len(bac)} nhận xét có chứng minh; agent không hợp lệ: "
          f"{', '.join(t for t, g in ghi.items() if not g['hop_le']) or 'không'}.")
    return 0


def loi_nhan_agent_bien_tap(ten: str, vd: Sequence[Dict[str, Any]], tep: str, loai: str, study: str,
                            tra_loi: str) -> str:
    return (f"Bạn là agent `{ten}` của hệ, BIÊN TẬP {LOAI_TAI_LIEU[loai]['ten']} của đề tài «{study}» theo các vấn đề "
            f"Hội đồng Khoa học máy đã giữ. Đọc tài liệu: `{tep}`. KHÔNG sửa tệp trực tiếp — chỉ đề xuất thay thế; "
            "máy áp qua rào liêm chính. Được dùng công cụ của hệ để tra cứu/tính lại trước khi viết.\n"
            + loi_nhan_bien_tap(vd) + f"\nGhi DUY NHẤT JSON trên vào `{tra_loi}`.")


# Gom yêu cầu chạm CÙNG chỗ vào MỘT phiếu biên tập. Đo thật vòng 2 C1a (22/11/2026): N2_03 (pb2 → viet-ban-thao) và
# N2_08 (uv_tk → co-mau-nghien-cuu) cùng nêu dòng 926 nhưng nằm ở hai phiếu ⇒ thay thế áp sau không còn thấy đoạn cũ
# («xuất hiện 0 lần») ⇒ bị loại, vòng kín tốn thêm một vòng; N2_05 (pb1) và N2_06 (uv_dd) cùng trích một câu ở dòng 496
# mà N2_06 còn phải sửa đồng bộ dòng 1072 ⇒ hai agent dễ làm hai chỗ lệch nhau. Dùng cho cả phiếu agent (chế độ kết
# hợp) lẫn nhóm yêu cầu của chế độ chỉ-API (`xep_lo_theo_cum`). Tham số VẬN HÀNH: không đổi lời dặn, không đổi SHA quy
# chế; ghế nêu yêu cầu vẫn là ghế thẩm tra nó ở vòng sau.
CAU_TOI_THIEU = 20   # mảnh trích ngắn hơn («[49]», «n (%)») xuất hiện ở quá nhiều câu — không đủ để coi là «cùng câu»
_TACH_CAU = re.compile(r"(?<=[.!?;])\s+")


def _cac_cau(s: str) -> List[str]:
    """Các câu của chuỗi, chuẩn hoá như khi so «trích nguyên văn», chỉ giữ câu đủ dài để nhận diện."""
    return [c for c in (x.strip(" .;:,") for x in _TACH_CAU.split(API.chuan_hoa(s))) if len(c) >= CAU_TOI_THIEU]


def _so_dong(x: Any) -> int:
    try:
        return max(0, int(x))
    except (TypeError, ValueError):
        return 0


def _dau_vet_van_de(f: Dict[str, Any], cac_dong: Sequence[str],
                    cac_dong_ch: Sequence[str]) -> Tuple[List[List[int]], List[str]]:
    """(các khoảng dòng của yêu cầu trong bản HIỆN TẠI, các câu nó trích).

    Từ vòng thẩm tra, «dong»/«trich» là của bản trước còn «dong_moi»/«trich_moi» là của bản hiện tại ⇒ ưu tiên định vị
    trích nguyên văn trong bản hiện tại (lần gần dòng gợi ý nhất); không định vị được ⇒ dùng số dòng gợi ý. Câu trích
    định vị được ⇒ lấy NGUYÊN câu của tài liệu chứa nó (hai mảnh khác nhau của cùng một câu vẫn khớp); không định vị
    được ⇒ dùng chính các câu của trích."""
    khoang: List[List[int]] = []
    cau: List[str] = []
    for trich, goi_y in ((f.get("trich_moi"), _so_dong(f.get("dong_moi"))), (f.get("trich"), _so_dong(f.get("dong")))):
        t = API.chuan_hoa(str(trich or ""))
        if not t:
            continue
        manh = _cac_cau(str(trich))
        ung = [i + 1 for i, d in enumerate(cac_dong_ch) if t in d]
        if not ung:
            cau += manh
            continue
        dong = min(ung, key=lambda d: (abs(d - goi_y) if goi_y else 0, d))
        khoang.append([dong, dong])
        cau += [c for c in _cac_cau(cac_dong[dong - 1]) if any(m in c for m in manh)] or manh
    if not khoang:
        d = _so_dong(f.get("dong_moi")) or _so_dong(f.get("dong"))
        if d:
            khoang.append([d, d])
    return khoang, cau


def gom_cum_bien_tap(vd: Sequence[Dict[str, Any]], van: str) -> List[List[Dict[str, Any]]]:
    """Chia yêu cầu sửa thành CỤM phải do MỘT biên tập viên xử lý: khoảng dòng (trong bản hiện tại) cách nhau
    ≤ CUA_SO_DONG dòng, hoặc cùng trích một câu (so theo nội dung ⇒ cả câu lặp ở hai nơi, vd thân đề cương và bản thông
    tin cho người tham gia); bắc cầu. Cụm và yêu cầu trong cụm giữ thứ tự của danh sách vào."""
    cac_dong = van.splitlines()
    cac_dong_ch = [API.chuan_hoa(d) for d in cac_dong]
    dv = [_dau_vet_van_de(f, cac_dong, cac_dong_ch) for f in vd]
    cha = list(range(len(vd)))

    def goc(i: int) -> int:
        while cha[i] != i:
            cha[i] = cha[cha[i]]
            i = cha[i]
        return i

    for i in range(len(vd)):
        for j in range(i + 1, len(vd)):
            gan = any(a1 - CUA_SO_DONG <= b2 and a2 - CUA_SO_DONG <= b1 for a1, b1 in dv[i][0] for a2, b2 in dv[j][0])
            chung_cau = any(x in y or y in x for x in dv[i][1] for y in dv[j][1])
            if gan or chung_cau:
                cha[goc(j)] = goc(i)
    cum: Dict[int, List[Dict[str, Any]]] = {}
    for i, f in enumerate(vd):
        cum.setdefault(goc(i), []).append(f)
    return list(cum.values())


def xep_lo_theo_cum(cum: Sequence[Sequence[Dict[str, Any]]], co: int) -> List[List[Dict[str, Any]]]:
    """Chế độ chỉ-API: xếp các cụm theo thứ tự vào nhóm ≤ `co` vấn đề mỗi yêu cầu, KHÔNG tách cụm nào ra hai yêu cầu;
    cụm lớn hơn `co` đi nguyên một yêu cầu riêng (tách nó lại gây đúng lỗi «đoạn cũ xuất hiện 0 lần»)."""
    nhom: List[List[Dict[str, Any]]] = []
    for c in cum:
        if nhom and len(nhom[-1]) + len(c) <= max(1, int(co)):
            nhom[-1].extend(c)
        else:
            nhom.append(list(c))
    return nhom


def lap_viec_bien_tap(st: Dict[str, Any], vd: Sequence[Dict[str, Any]], out_dir: Path,
                      van: Optional[str] = None) -> Dict[str, Any]:
    """Một phiếu biên tập cho mỗi agent. Yêu cầu được gom thành cụm (`gom_cum_bien_tap`) TRƯỚC khi chia: cả cụm vào
    phiếu của agent sở hữu nhiều yêu cầu nhất trong cụm (hoà ⇒ agent của yêu cầu đứng trước); phiếu ghi «cum» các cụm
    có từ hai yêu cầu để biên bản truy được."""
    chu = {t["ma"]: (TAC_NHAN_BIEN_TAP.get(t["ma"]) or (t.get("tac_nhan") or ["viet-ban-thao"])[0]) for t in _ds_tv(st)}
    if van is None:
        van = Path(st["tep"]).read_text(encoding="utf-8")
    nhom: Dict[str, List[Dict[str, Any]]] = {}
    cum_gop: Dict[str, List[List[str]]] = {}
    for cum in gom_cum_bien_tap(vd, van):
        dem: Dict[str, int] = {}
        for f in cum:
            ag = chu.get(f.get("thanh_vien"), "viet-ban-thao")
            dem[ag] = dem.get(ag, 0) + 1
        ten = max(dem, key=lambda ag: dem[ag])
        nhom.setdefault(ten, []).extend(cum)
        if len(cum) > 1:
            cum_gop.setdefault(ten, []).append([f["id"] for f in cum])
    tm = thu_muc_viec(out_dir, st)
    return {ten: {"ids": [f["id"] for f in ds], "cum": cum_gop.get(ten, []), **ghi_viec(
        tm, "bien_tap", ten, loi_nhan_agent_bien_tap(ten, ds, st["tep"], st.get("loai", "de_cuong"), st["study"],
                                                    str(tm / f"tra_loi_bien_tap_{ten}.json")),
        {"van_de": ds})} for ten, ds in nhom.items()}


def gop_tra_loi_bien_tap(viec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Đủ trả lời ⇒ gộp thành MỘT bản đề xuất (cùng khuôn biên tập viên API); thiếu ⇒ None."""
    if any(not Path(v["tra_loi"]).exists() for v in viec.values()):
        return None
    sua: List[Any] = []
    for v in viec.values():
        try:
            dl = json.loads(Path(v["tra_loi"]).read_text(encoding="utf-8"))
            sua += [m for m in (dl.get("sua") or []) if isinstance(m, dict) and str(m.get("id")) in set(v["ids"])]
        except (OSError, ValueError, AttributeError):
            continue
    return {"sua": sua}


def loi_nhan_tham_dinh_dau_ra(tep: str, bien_ban: str, loai: str, study: str, tra_loi: str) -> str:
    return ("Bạn là agent `tham-dinh-dau-ra`. CHỐT KIỂM CUỐI trước khi trình bác sĩ "
            f"{LOAI_TAI_LIEU[loai]['ten']} của đề tài «{study}» mà Hội đồng Khoa học máy vừa thông qua. Đọc tài liệu "
            f"`{tep}` và biên bản `{bien_ban}`. Soi "
            "Lớp 1 LIÊM CHÍNH R1–R7 của bạn (nguồn · PII · vượt cổng · tự gán mức · tách hai trục · nhãn [CẦN…] · "
            "disclaimer theo đúng loại tài liệu). Mỗi lỗi phải trích NGUYÊN VĂN + số dòng (máy đối chiếu). Không sửa "
            f"tài liệu. Ghi DUY NHẤT JSON vào `{tra_loi}`: " + json.dumps(
                {"ket_qua": "DAT|TRA_VE_SUA", "loi": [{"ma": "R1", "dong": 12, "trich": "…", "mo_ta": "…",
                                                       "de_xuat": "…"}]}, ensure_ascii=False))


def buoc_tham_dinh_dau_ra(st: Dict[str, Any], van: str, out_dir: Path) -> int:
    """«ĐẠT» chỉ thành «trình bác sĩ» khi `tham-dinh-dau-ra` trả ĐẠT, hoặc mọi lỗi nó nêu không xác minh được."""
    tm = thu_muc_viec(out_dir, st)
    if not st.get("viec_dau_ra"):
        st["viec_dau_ra"] = ghi_viec(tm, "dau_ra", "tham-dinh-dau-ra", loi_nhan_tham_dinh_dau_ra(
            st["tep"], str(thu_muc_hd(out_dir) / (st.get("bien_ban") or "")), st.get("loai", "de_cuong"), st["study"],
            str(tm / "tra_loi_dau_ra_tham-dinh-dau-ra.json")), {"tep": st["tep"]})
    p_tl = Path(st["viec_dau_ra"]["tra_loi"])
    if not p_tl.exists():
        print("🤝 Chờ agent tham-dinh-dau-ra — chạy «viec-agent» để xem phiếu việc.")
        return CHO_AGENT
    try:
        dl = json.loads(p_tl.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dl = {}
    cac_dong = van.splitlines()
    loi = [x for x in (dl.get("loi") or []) if isinstance(x, dict)
           and _trong_cua_so(str(x.get("trich") or ""), int(x.get("dong") or 0) if str(x.get("dong") or "").isdigit()
                             else 0, cac_dong)]
    st["ket_qua_dau_ra"] = {"ket_qua": dl.get("ket_qua"), "loi_xac_minh": loi,
                            "loi_khong_xac_minh": len(dl.get("loi") or []) - len(loi)}
    if dl.get("ket_qua") not in ("DAT", "TRA_VE_SUA"):
        print("⛔ tham-dinh-dau-ra trả lời không hợp lệ — xoá tệp trả lời và giao lại.")
        return 1
    st["trinh_bac_si"] = not loi
    print("✅ tham-dinh-dau-ra: ĐẠT — tài liệu được trình bác sĩ." if not loi else
          f"⛔ tham-dinh-dau-ra: {len(loi)} lỗi liêm chính đã xác minh — CHƯA trình bác sĩ (xem biên bản).")
    return 0 if not loi else 1


def loi_nhan_agent_tham_tra(ten: str, tv: Dict[str, Any], ds: Sequence[Dict[str, Any]], khoang: Sequence[Sequence[int]],
                            tep: str, study: str, tra_loi: str) -> str:
    return (f"Bạn là agent `{ten}` của hệ, thay mặt ghế «{tv.get('vai')}» THẨM TRA việc chỉnh sửa tài liệu của đề tài "
            f"«{study}». Tài liệu đã sửa: `{tep}` (số dòng tính từ 1). Dùng công cụ của hệ khi cần — gợi ý: "
            f"{CONG_CU_GOI_Y.get(ten, 'công cụ hệ')}.\n"
            + loi_nhan_tham_tra(tv, ds, khoang).replace("Tài liệu ở trên là bản ĐÃ SỬA", "Tài liệu trên là bản ĐÃ SỬA")
            + f"\nGhi DUY NHẤT JSON trên vào `{tra_loi}`; không sửa tài liệu, không ghi tệp khác.")


def buoc_tham_tra_agent(st: Dict[str, Any], van: str, out_dir: Path) -> int:
    """Thẩm tra (từ vòng 2) bằng agent SỞ HỮU chuyên môn của từng ghế — cùng luật máy-kiểm như thẩm tra API."""
    tm = thu_muc_viec(out_dir, st)
    theo_tv: Dict[str, List[Dict[str, Any]]] = {}
    for f in st.get("ds_yeu_cau") or []:
        theo_tv.setdefault(f["thanh_vien"], []).append(f)
    tv_theo_ma = {t["ma"]: t for t in _ds_tv(st)}
    chu = _ma_tv_theo_tac_nhan(st)
    if not st.get("viec_tham_tra"):
        if not theo_tv:
            st["tham_tra"] = {"da_giai_quyet": [], "chua_giai_quyet": [], "can_du_kien": [], "loi_moi": [], "loai": []}
            st["buoc"] = "xong"
            return 0
        viec = {}
        for ma, ds in theo_tv.items():
            ten = chu.get(ma) or TAC_NHAN_BIEN_TAP.get(ma) or "viet-ban-thao"
            tv = tv_theo_ma.get(ma) or {"ma": ma, "vai": "Chốt kiểm đầu ra" if ma == "dau_ra" else ma}
            viec[ma] = {"ds": ds, **ghi_viec(tm, "tham_tra", f"{ma}-{ten}", loi_nhan_agent_tham_tra(
                ten, tv, ds, st.get("khoang") or [], st["tep"], st["study"],
                str(tm / f"tra_loi_tham_tra_{ma}-{ten}.json")), {"yeu_cau": ds})}
        st["viec_tham_tra"] = viec
    thieu = [ma for ma, v in st["viec_tham_tra"].items() if not Path(v["tra_loi"]).exists()]
    if thieu:
        print(f"🤝 Chờ agent thẩm tra: {', '.join(st['viec_tham_tra'][m]['agent'] for m in thieu)} — «viec-agent».")
        return CHO_AGENT
    gop: Dict[str, Any] = {"da_giai_quyet": [], "chua_giai_quyet": [], "can_du_kien": [], "loi_moi": [], "loai": []}
    for ma, v in st["viec_tham_tra"].items():
        try:
            kq = xac_minh_tham_tra(ma, json.loads(Path(v["tra_loi"]).read_text(encoding="utf-8")), v["ds"], van,
                                   st.get("khoang") or [], st.get("vtq_ids") or [])
        except (OSError, ValueError, API.LoiApi) as exc:   # trả lời hỏng ⇒ chưa giải quyết (fail-safe), ghi lý do
            kq = {"ket": {str(f["id"]): {**f, "ket_qua": "chua_giai_quyet", "nguoi_tham_tra": ma,
                                         "ly_do_tham_tra": f"trả lời agent không đọc được: {exc}"[:200]}
                          for f in v["ds"]}, "loi_moi": [], "loai": []}
        for x in kq["ket"].values():
            gop[x["ket_qua"]].append(x)
        gop["loi_moi"] += kq["loi_moi"]
        gop["loai"] += kq["loai"]
    for i, g in enumerate(gop["loi_moi"], 1):
        g["id"] = f"N{st.get('vong', 2)}_{i:02d}"
    st["tham_tra"] = gop
    st["buoc"] = "xong"
    print(f"✅ Agent thẩm tra xong: {len(gop['da_giai_quyet'])} đã giải quyết · {len(gop['chua_giai_quyet'])} chưa · "
          f"{len(gop['can_du_kien'])} cần dữ kiện · {len(gop['loi_moi'])} lỗi mới.")
    return 0


TRONG_TAI_AGENT = "trong-tai-tranh-bien"


def viec_agent_dang_cho(goc: Path, study: str) -> List[Dict[str, str]]:
    """Mọi phiếu việc agent còn thiếu trả lời của đề tài (Claude Code đọc để giao)."""
    ra = []
    for p_st in (goc / "exports" / study / THU_MUC).glob("trang_thai_*.json"):
        st = _doc_st(p_st) or {}
        for v in (list((st.get("viec_tham_dinh") or {}).values()) + list((st.get("viec_bien_tap") or {}).values())
                  + list((st.get("viec_tham_tra") or {}).values())
                  + ([st["viec_dau_ra"]] if st.get("viec_dau_ra") else [])):
            if not Path(v["tra_loi"]).exists():
                ra.append({k: v[k] for k in ("agent", "loai_viec", "loi_nhan", "tra_loi")})
    for p_tt in (goc / "exports" / study / THU_MUC / "hieu_chuan").glob("*/bao_nham_trang_thai.json"):
        tt = _doc_st(p_tt) or {}
        v = tt.get("viec_trong_tai")
        if v and not Path(v["tra_loi"]).exists():
            ra.append({k: v[k] for k in ("agent", "loai_viec", "loi_nhan", "tra_loi")})
    return ra


def hoan_nguyen_vuot_quyen(van_goc: str, van_sua: str, sap_khoa: bool,
                           dong_bi_neu: Sequence[int] = ()) -> Tuple[str, List[Dict[str, Any]]]:
    """Trả về bản gốc mọi KHỐI đổi (difflib) chạm vùng khoá (của bản gốc hoặc bản sửa) hoặc chạm dòng chốt kiểm đã nêu
    (số dòng của bản SỬA, ±3). Giữ nguyên các khối sửa khác. Trả (văn bản mới, nhật ký khối đã hoàn nguyên)."""
    import difflib  # noqa: PLC0415

    a, b = van_goc.splitlines(), van_sua.splitlines()
    ka, kb = vung_khoa(van_goc, sap_khoa), vung_khoa(van_sua, sap_khoa)
    neu = set()
    for d in dong_bi_neu:
        neu |= set(range(max(1, int(d) - CUA_SO_DONG), int(d) + CUA_SO_DONG + 1))
    ra: List[str] = []
    nk: List[Dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            ra += b[j1:j2]
            continue
        cham_khoa = any(ka[i] for i in range(i1, i2)) or any(kb[j] for j in range(j1, j2)) or (
            i1 == i2 and 0 < i1 <= len(ka) and ka[i1 - 1])
        cham_neu = any((j + 1) in neu for j in range(j1, max(j2, j1 + 1)))
        if cham_khoa or cham_neu:
            ra += a[i1:i2]
            nk.append({"dong_ban_sua": [j1 + 1, j2], "dong_ban_goc": [i1 + 1, i2],
                       "ly_do": "chạm nội dung đã khoá" if cham_khoa else "dòng chốt kiểm đầu ra đã nêu",
                       "doan_sua": "\n".join(b[j1:j2])[:400], "doan_goc": "\n".join(a[i1:i2])[:400]})
        else:
            ra += b[j1:j2]
    return "\n".join(ra) + ("\n" if van_sua.endswith("\n") else ""), nk


# ── CLI ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def main(argv: Optional[Sequence[str]] = None, client: Any = None, goc: Path = REPO) -> int:
    ap = argparse.ArgumentParser(description="Hội đồng Khoa học máy cấp đề tài (Claude Batch API).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    va = sub.add_parser("viec-agent", help="phiếu việc agent còn chờ (Claude Code đọc để giao)")
    va.add_argument("--study", required=True)
    k = sub.add_parser("ke-hoach", help="in/ghi văn bản quy chế (khoá trước khi họp)")
    k.add_argument("--ghi", action="store_true", help=f"ghi {TEP_QUY_CHE}")
    cd = sub.add_parser("chup-doctrine", help="chụp doctrine agent theo ghế (đổi quy chế — có chủ ý)")
    cd.add_argument("--ghi", action="store_true", help=f"ghi {TEP_DOCTRINE}")
    for ten in ("uoc-tinh", "hop", "bien-ban", "hieu-chuan", "vong-kin", "do-bao-nham"):
        p = sub.add_parser(ten)
        p.add_argument("--study", required=True)
        p.add_argument("--loai", choices=sorted(LOAI_TAI_LIEU), default="de_cuong",
                       help="loại tài liệu (mặc định đề cương nộp Hội đồng)")
        p.add_argument("--tep", type=Path, help="tài liệu (mặc định: tệp chuẩn của loại tài liệu của đề tài)")
        p.add_argument("--model", default=MODEL_MAC_DINH)
        if ten == "do-bao-nham":
            p.add_argument("--goi-api", action="store_true", help="trọng tài API: nộp/lấy batch (TÍNH PHÍ)")
            p.add_argument("--trong-tai", choices=("agent", "api"), default="agent",
                           help="agent = agent Claude Code (mặc định, không tốn tín dụng API); api = Fable (tính phí)")
        if ten in ("hop", "vong-kin"):
            p.add_argument("--ket-hop", action="store_true",
                           help="chế độ KẾT HỢP: agent thẩm định/biên tập/thẩm tra/chốt cuối (mặc định của vong-kin)")
            p.add_argument("--chi-api", action="store_true", help="vong-kin chỉ dùng API (chế độ cũ)")
        if ten == "hop":
            p.add_argument("--goi-api", action="store_true", help="nộp/lấy batch (TÍNH PHÍ)")
            p.add_argument("--lam-lai", action="store_true", help="bỏ trạng thái cũ của tài liệu này, họp lại")
        if ten == "bien-ban":
            p.add_argument("--ap-dung", action="store_true", help="ghi biên bản .md + .json")
        if ten == "vong-kin":
            p.add_argument("--goi-api", action="store_true", help="nộp/lấy batch (TÍNH PHÍ)")
            p.add_argument("--ap-dung", action="store_true",
                           help="ghi bản đã sửa (sao lưu bản cũ; hoàn nguyên nếu xấu đi)")
            p.add_argument("--lam-lai", action="store_true", help="bỏ phiên cũ của tài liệu này (vd quy chế đã đổi)")
        if ten == "hieu-chuan":
            g = p.add_mutually_exclusive_group(required=True)
            g.add_argument("--tao", action="store_true", help="tạo bản sao cài lỗi + đáp án (0 gọi API)")
            g.add_argument("--cham", action="store_true", help="chấm độ nhạy sau khi hội đồng họp bản sao")
    a = ap.parse_args(argv)
    if a.lenh == "viec-agent":
        ds = viec_agent_dang_cho(goc, a.study)
        print(json.dumps(ds, ensure_ascii=False, indent=1))
        return 0 if not ds else CHO_AGENT
    if a.lenh == "chup-doctrine":
        moi_bc, cu_bc = chup_doctrine(goc), doc_doctrine(goc)
        doi = sorted(t for t in moi_bc if (cu_bc.get(t) or {}).get("sha_tep") != moi_bc[t]["sha_tep"])
        print(f"Doctrine {len(moi_bc)} agent; khác bản chụp hiện hành: {', '.join(doi) or 'không'}.")
        if a.ghi:
            _ghi_json(goc / TEP_DOCTRINE, moi_bc)
            print(f"📸 Đã ghi {TEP_DOCTRINE} — quy chế đổi SHA, phải hiệu chuẩn lại.")
        return 0
    if a.lenh == "ke-hoach":
        vb = van_ban_quy_che()
        if a.ghi:
            p_qc = goc / TEP_QUY_CHE
            p_qc.parent.mkdir(parents=True, exist_ok=True)
            _ghi_van(p_qc, vb)
            print(f"📜 Đã ghi {TEP_QUY_CHE} ({PHIEN_BAN_QUY_CHE}, SHA {sha_ke_hoach()[:16]}…).")
        else:
            print(vb)
        return 0
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", a.study):
        print("❌ mã đề tài không hợp lệ", file=sys.stderr)
        return 3
    out_dir = goc / "exports" / a.study
    loai = a.loai
    hc_dir = thu_muc_hd(out_dir) / "hieu_chuan" / loai
    if a.lenh == "do-bao-nham":
        try:
            return _do_bao_nham(goc, out_dir, a.study, loai, a.goi_api, client, a.model, a.trong_tai)
        except API.LoiApi as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2
    if a.lenh == "hieu-chuan":
        goc_tep = a.tep or tep_mac_dinh(a.study, goc, loai)
        if a.tao:
            if not goc_tep.is_file():
                print(f"❌ không thấy {goc_tep}", file=sys.stderr)
                return 3
            van_moi, dap_an = cai_loi(goc_tep.read_text(encoding="utf-8"), loai, _thiet_ke(out_dir))
            if len(dap_an) < SO_LOI_CAI_TOI_THIEU:
                print(f"⛔ Chỉ tìm được neo cho {len(dap_an)} lỗi cài (< {SO_LOI_CAI_TOI_THIEU}) — tài liệu thiếu đề "
                      "mục chuẩn; hiệu chuẩn sẽ không hợp lệ.", file=sys.stderr)
            ban = hc_dir / f"BAN_CAI_LOI_{a.study}_{loai}.md"
            ban.parent.mkdir(parents=True, exist_ok=True)
            tam = ban.with_name(ban.name + ".tam")
            tam.write_text(van_moi, encoding="utf-8", newline="\n")
            tam.replace(ban)
            _ghi_json(hc_dir / "dap_an.json", {"tep": str(ban), "sha": _sha(van_moi), "dap_an": dap_an,
                                               "sha_goc": _sha(goc_tep.read_text(encoding="utf-8")), "loai": loai,
                                               "thiet_ke": _thiet_ke(out_dir),
                                               "sha_quy_che": sha_ke_hoach(a.model), "quy_che": PHIEN_BAN_QUY_CHE})
            print(f"🧪 Đã cài {len(dap_an)} lỗi vào {ban.name} (đáp án riêng, hội đồng không thấy). Họp bằng:\n"
                  f"   hoi_dong_khoa_hoc.py hop --study {a.study} --loai {loai} --tep {ban} --goi-api")
            return 0 if len(dap_an) >= SO_LOI_CAI_TOI_THIEU else 1
        da = _doc_st(hc_dir / "dap_an.json")
        if not da:
            print("❌ chưa có đáp án — chạy «hieu-chuan --tao» trước", file=sys.stderr)
            return 3
        st = _doc_st(tep_trang_thai(out_dir, da["sha"]))
        if not st or st.get("buoc") != "xong":
            print("⏳ hội đồng chưa họp xong bản cài lỗi", file=sys.stderr)
            return 4
        if not (st.get("quy_che") or {}).get("sha") == da.get("sha_quy_che") == sha_ke_hoach(a.model):
            print("⛔ Phiên hiệu chuẩn không cùng quy chế hiện hành — tạo lại bản cài lỗi và họp lại.", file=sys.stderr)
            return 1
        kq = cham_hieu_chuan(da["dap_an"], st)
        kq.update(sha_quy_che=da["sha_quy_che"], quy_che=PHIEN_BAN_QUY_CHE, sha_goc=da.get("sha_goc"), loai=loai,
                  ket_hop=bool(st.get("ket_hop")),
                  thiet_ke=da.get("thiet_ke"), ngay=dt.date.today().isoformat(),
                  dat=(kq["do_nhay"] is not None and kq["do_nhay"] >= DO_NHAY_TOI_THIEU
                       and kq["so_loi_cai"] >= SO_LOI_CAI_TOI_THIEU and kq["bat_dac_thu"] is not False))
        _ghi_json(hc_dir / "ket_qua.json", kq)
        print(f"🎯 Độ nhạy hội đồng: bắt {kq['bat']}/{kq['so_loi_cai']} lỗi cài ({kq['do_nhay']}); "
              f"{kq['van_de_ngoai_loi_cai']} vấn đề khác ngoài lỗi cài"
              + ("" if kq["bat_dac_thu"] is None
                 else f"; lỗi đặc thù thiết kế: {'BẮT' if kq['bat_dac_thu'] else 'SÓT'}")
              + ". Bước kế: «do-bao-nham» đo độ chính xác của các vấn đề khác.")
        for k in kq["chi_tiet"]:
            print(f"   {'✓' if k['bat'] else '✗'} {k['ma']} (dòng {k['dong']}) {', '.join(k['boi'])}")
        return 0 if kq["dat"] else 1
    tep = a.tep or tep_mac_dinh(a.study, goc, loai)
    if not tep.is_file():
        print(f"❌ không thấy tài liệu {tep}", file=sys.stderr)
        return 3
    van = tep.read_text(encoding="utf-8")
    p_st = tep_trang_thai(out_dir, _sha(van))
    st = None if getattr(a, "lam_lai", False) else _doc_st(p_st)
    if st and st.get("sha") != _sha(van):
        st = None
    if st and (st.get("quy_che") or {}).get("sha") != sha_ke_hoach(st.get("model", a.model)):
        print(f"⛔ Phiên của tài liệu này khởi tạo dưới quy chế khác (hoặc chưa có quy chế) — hết hiệu lực. Chạy lại "
              f"với --lam-lai để họp dưới {PHIEN_BAN_QUY_CHE}.", file=sys.stderr)
        return 1
    try:
        if st is None:
            st = khoi_tao(a.study, out_dir, tep, a.model, loai)
            st["ket_hop"] = bool(getattr(a, "ket_hop", False)) or (a.lenh == "vong-kin"
                                                                   and not getattr(a, "chi_api", False))
        la_ban_chinh = tep.resolve() == tep_mac_dinh(a.study, goc, loai).resolve()
        if la_ban_chinh:
            st["hieu_luc"], st["hieu_luc_ly_do"] = hieu_luc_hieu_chuan(out_dir, st["model"], loai,
                                                                       bool(st.get("ket_hop")))
        if a.lenh == "uoc-tinh":
            u = uoc_tinh(st, van)
            print(f"Hội đồng: {u['so_yeu_cau']} yêu cầu ({len(_ds_tv(st))} thành viên + chủ tịch), model {u['model']}, "
                  f"tài liệu ≈ {u['token_tai_lieu']:,} token. Chi phí điển hình ≈ {u['usd_dien_hinh']} USD "
                  f"(Batch −50%, cache tài liệu); trần ước tối đa {u['usd_toi_da']} USD. 0 gọi API.")
            return 0
        if a.lenh == "hop":
            ma = (buoc_tham_dinh_agent(st, van, out_dir) if st["buoc"] == "tham_dinh_agent"
                  else _chay_buoc(st, van, a.goi_api, client))
            if a.goi_api or st.get("batch"):
                _ghi_json(p_st, st)
            return ma
        if a.lenh == "vong-kin":
            if not LOAI_TAI_LIEU[loai]["vong_kin"]:
                print(f"⛔ Vòng kín chỉ cho đề cương; {LOAI_TAI_LIEU[loai]['ten']} chỉ được THẨM ĐỊNH (SAP đã khoá "
                      "không được máy sửa — nhận xét là đề xuất sửa đổi cho chủ nhiệm/thống kê viên).", file=sys.stderr)
                return 3
            if not la_ban_chinh or not st.get("hieu_luc"):
                print(f"⛔ Vòng kín chỉ chạy trên đề cương chính khi hội đồng đã hiệu chuẩn đạt dưới "
                      f"{PHIEN_BAN_QUY_CHE}: "
                      f"{st.get('hieu_luc_ly_do', 'không phải đề cương chính')}. Chạy «hieu-chuan --tao», họp bản cài "
                      "lỗi, «hieu-chuan --cham» trước.", file=sys.stderr)
                return 3
            ma = vong_kin_buoc(st, van, tep, out_dir, a.goi_api, a.ap_dung, client)
            if a.goi_api or st.get("batch"):
                if st["buoc"] in ("bien_tap", "dat", "da_sua") and not st.get("bien_ban"):
                    st["bien_ban"] = ghi_bien_ban(st, out_dir).name  # mỗi vòng một biên bản — để kiểm toán
                _ghi_json(p_st, st)
            return ma
        if st.get("buoc") not in ("xong", "bien_tap", "dat", "da_sua"):
            print("⏳ hội đồng chưa họp xong — chạy «hop --goi-api» tới khi xong.", file=sys.stderr)
            return 4
        if not a.ap_dung:
            print(bien_ban_md(st))
            print("(chạy khô — thêm --ap-dung để ghi biên bản)")
            return 0
        print(f"📝 Đã ghi {ghi_bien_ban(st, out_dir).name} (+ .json). Cần bác sĩ kiểm chứng.")
        return 0
    except API.HetNganSach as exc:
        print(f"⛔ {exc}", file=sys.stderr)
        return 2
    except API.LoiApi as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
