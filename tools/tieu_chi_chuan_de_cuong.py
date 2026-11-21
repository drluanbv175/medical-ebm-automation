#!/usr/bin/env python3
"""Tiêu chí kiểm ĐỀ CƯƠNG theo từng mục cho 12 chuẩn ngoài STROBE/RECORD/CROSS — dùng bởi K17.

VÌ SAO (21/11/2026, bác sĩ): «từng tiêu chuẩn trong từng cấu trúc đề cương nghiên cứu phải đạt tiêu chuẩn và sự tin cậy
cao nhất», cho MỌI thiết kế; «những gì không đạt chuẩn sẽ phải được loại bỏ». PR K17 đầu tiên chỉ có tiêu chí cho
STROBE, RECORD, CROSS và chuẩn Việt Nam; các chuẩn dưới đây báo ⚪ «chưa đo được». Tệp này viết tiêu chí cho:
  SPIRIT 2025 (rct) · PRISMA-P 2015 (systematic_review) · STARD 2015 (diagnostic) · TRIPOD+AI 2024 (prediction) ·
  COREQ 2007 + SRQR 2014 (qualitative) · GRAMMS 2008 (mixed_methods) · SQUIRE 2.0 (quality_improvement) ·
  CHEERS 2022 (economic) · TREND 2004 (non_randomized) · CARE 2013 (case_report) · COSMIN 2021 (kiểm định bộ câu hỏi).

KHUÔN mỗi bảng (giống `_CROSS_TIEU_CHI`): mã → (phần đề cương, mức độ, tiêu chí tiếng Việt, yếu tố, [áp dụng khi,
lý do điều kiện, cùng đoạn]). Mức độ: `bat_buoc` (mục phương pháp phải có trong đề cương) · `ke_hoach` (mục kết quả/bàn
luận — đề cương phải lên kế hoạch) · `bao_cao` (chỉ áp khi viết bài báo). Áp dụng khi bắt đầu bằng «!» = áp dụng khi
biểu thức KHÔNG có trong đề cương; mọi điều kiện đi qua `co_dieu_kien` (bỏ câu phủ định).

NGUYÊN VĂN mục: chuẩn có giấy phép Creative Commons lấy từ `chuan_bao_cao_items.py` (sinh từ XML Europe PMC) hoặc
`protocol_checklist_items.py` (SPIRIT 2025, PRISMA-P 2015). Chuẩn thuộc bản quyền nhà xuất bản (TREND © AJPH, COREQ
© OUP, SRQR © AAMC, GRAMMS — bài không truy cập mở, COSMIN © Springer) KHÔNG lưu nguyên văn: chỉ mã mục, chủ đề ngắn
tiếng Anh và tiêu chí do hệ viết.

CHƯA ĐỐI CHIẾU BẢNG GỐC: danh mục TREND, COREQ, SRQR do agent đọc qua bản tóm lược WebFetch hoặc nguồn thứ cấp
(`~/.ebm-worktrees/_du_lieu_chuan_bao_cao_20261121/*.json`, trường `nguon_lay`); lượt tải byte thô bảng gốc ngày
21/11/2026 thất bại (Europe PMC 500, CDC 403, EQUATOR 404). Theo chỉ thị bác sĩ, ba chuẩn này CHƯA được dùng làm luật
chặn: mục thiếu báo `canh_bao` (⚠), không làm K17 đỏ — cho tới khi có người đối chiếu bảng gốc và gỡ tên khỏi
`CHUAN_CHUA_DOI_CHIEU_GOC`.

GIỚI HẠN (như K17): yếu tố có mặt ≠ nội dung đúng. Bộ kiểm bắt THIẾU một cách tin cậy; ĐẠT chỉ là «có dấu hiệu đủ yếu
tố», người phân xử đọc bằng chứng từng dòng.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import chuan_bao_cao_items as CBC
import protocol_checklist_items as PCI
from kiem_chuan_de_cuong_theo_muc import (
    DINH_TINH_CP,
    KINH_TE,
    NGAY,
    NOI,
    MucKiem,
    _y,
)

# ───────────────────────────── mẫu dùng chung ─────────────────────────────
TRICH_DAN = r"\[\d+(?:[,–-]\s*\d+)*\]"
MUC_TIEU_CU_THE = (r"^[ \t]*(?:\d[.)]|-|\*)[ \t]*[*_]*[ \t]*(?:MT\d+[ \t]*:[ \t]*)?(?:Mô tả|Xác định|Phân tích|Đánh "
                   r"giá|"
                   r"So sánh|Ước tính|Khảo sát|Xây dựng|Kiểm định|Tìm hiểu|Khám phá|Tổng hợp|Phát triển)")
TIEU_CHUAN_CHON = r"Tiêu chuẩn (lựa )?chọn"
TIEU_CHUAN_LOAI = r"Tiêu chuẩn loại"
KINH_PHI = r"kinh phí|nguồn (tài trợ|kinh phí)"
VAI_TRO_TAI_TRO = (r"vai trò (của )?(nhà |đơn vị )?tài trợ|không tham gia (vào )?(thiết kế|phân tích)|độc lập với|"
                   r"không can thiệp vào (thiết kế|phân tích|công bố)|tự túc|không có (nhà |đơn vị )?tài trợ|"
                   r"không đề nghị cấp kinh phí")
XUNG_DOT = r"xung đột lợi ích"
#: vai trò trong nhóm nghiên cứu (đề mục «Nhân lực và phân công nhiệm vụ» thường chỉ liệt kê chức danh theo vai trò)
VAI_TRO_NHOM = (r"vai trò|nhiệm vụ|phụ trách|thống kê viên|quản lý dữ liệu|điều tra viên|người (sàng lọc|phỏng vấn|mã "
                r"ho[áa]|"
                r"trích)")
HOI_DONG = r"Hội đồng (Đạo đức|đạo đức)"
DONG_Y = r"đồng (ý|thuận)|tự nguyện"
DU_LIEU_THIEU = r"(dữ liệu|số liệu|giá trị) thiếu|thiếu (dữ liệu|số liệu)|missing"
XU_LY_THIEU = (r"ca đầy đủ|complete case|đa quy|điền khuyết|multiple imputation|MICE|trường hợp đủ dữ liệu|gán|"
               r"loại khỏi|phân tích độ nhạy")
PP_THONG_KE = (r"hồi quy|kiểm định|chi bình phương|χ²|Mann|Wilcoxon|Fisher|logistic|Poisson|\bCox\b|khoảng tin cậy|KTC"
               r"|phân tích gộp|hiệu ứng ngẫu nhiên")
CONG_THUC_CO_MAU = r"công thức|Cochran|lực mẫu|độ chính xác|\bpower\b|Riley|\bEPV\b|n\s*=|toàn bộ|bão hoà|bão hòa"
CO_MAU_CUOI = r"\d[\d.,]*\s*(người|bệnh nhân|đối tượng|hồ sơ|lượt|trường hợp|nghiên cứu|phỏng vấn|cặp)"
THAM_SO_NGUON = r"\[\d+|tham khảo|nghiên cứu (trước|thử|của)"
HAN_CHE = r"hạn chế|sai lệch|sai số"
SUY_RONG = r"suy rộng|khái quát|giá trị ngoại|tính đại diện|áp dụng cho|chuyển giao"
SO_DO = r"sơ đồ|lưu đồ"
DE_CUONG_TRUY_CAP = (r"(đề cương|kế hoạch phân tích|\bSAP\b).{0,160}(truy cập|công bố|lưu (trữ|tại)|cung cấp|đăng tải|"
                     r"theo yêu cầu)")
CHIA_SE_DU_LIEU = (r"(dữ liệu (cá nhân|đã khử định danh|ở mức cá nhân|gốc|thô)|bộ dữ liệu|từ điển dữ liệu|mã (phân "
                   r"tích|"
                   r"lệnh|nguồn|lập trình)|script).{0,160}(chia sẻ|cung cấp|truy cập|theo yêu cầu|công bố|lưu)|"
                   r"(không|chưa) chia sẻ (dữ liệu|bộ dữ liệu)")
CHIA_SE_MA = r"(mã (phân tích|lệnh|nguồn|lập trình)|script|code).{0,160}(chia sẻ|cung cấp|công bố|lưu|theo yêu cầu)"
DANG_KY = r"ClinicalTrials\.gov|\bICTRP\b|PROSPERO|\bOSF\b|đăng ký (thử nghiệm|nghiên cứu|đề cương|trên)"
DANG_KY_SO = r"số đăng ký|\bNCT\d|CRD\d|(sẽ|dự kiến) (được )?đăng ký|đăng ký.{0,60}trước khi"
PPI = (r"(người bệnh|người dân|cộng đồng|công chúng|đại diện người bệnh).{0,60}(tham gia|góp ý|tư vấn) (vào |trong |"
       r"khi )?"
       r"(thiết kế|xây dựng|soạn|thực hiện|phổ biến|đề cương|bộ câu hỏi|nội dung|nghiên cứu)|\bPPI\b|"
       r"(không có|chưa có|không) (sự )?tham gia của (người bệnh|cộng đồng|công chúng)")
PHO_BIEN_NGUOI_THAM_GIA = (r"(kết quả|tóm tắt).{0,120}(người tham gia|công chúng|cộng đồng|người bệnh)|"
                           r"(người tham gia|công chúng|cộng đồng).{0,120}(kết quả|tóm tắt)|bản tóm tắt (dễ hiểu|phổ "
                           r"thông)|"
                           r"(cập nhật|đăng) kết quả (lên|trên) (ClinicalTrials|cơ quan đăng ký)")
SUA_DOI_DE_CUONG = (r"(sửa đổi|thay đổi|điều chỉnh) (đề cương|quan trọng).{0,160}(thông báo|báo cáo|trình|cập nhật|ghi "
                    r"(nhận|lại)|xin phép|công bố)")
BAO_MAT = r"khử định danh|ẩn danh|mã hoá|mã hóa|mã số (thay|nghiên cứu)|bảo mật"
TRUY_CAP_GIOI_HAN = r"quyền truy cập|phân quyền|mật khẩu|chỉ (nghiên cứu viên|chủ nhiệm|nhóm nghiên cứu)"
CHAT_LUONG_DL = (r"nhập (liệu )?kép|(hai|2) lượt nhập|nhập (hai|2) lần|kiểm tra (phạm vi|khoảng giá trị|logic|nhập "
                 r"liệu)|"
                 r"luật kiểm|làm sạch|đối chiếu")

DINH_LUONG_CP = (r"hồi quy|kiểm định (thống kê|chi bình phương|t\b)|tỷ lệ|khoảng tin cậy|thử nghiệm|phân bổ ngẫu nhiên|"
                 r"cỡ mẫu được tính")

# ───────────────────────── chuẩn chưa đối chiếu bảng gốc (chỉ cảnh báo) ─────────────────────────
CHUAN_CHUA_DOI_CHIEU_GOC: Dict[str, str] = {
    "TREND 2004": "danh mục đọc qua bản tóm lược WebFetch trang PMC1448256 (byte thô bị chặn: Europe PMC 500, CDC 403)",
    "COREQ 2007": "nhãn từ Bảng 2 nguồn thứ cấp CC BY (PMC8436506) + bản dịch SciELO; bài gốc OUP chỉ cho thuê bao",
    "SRQR 2014": "nhãn từ chú thích Hình 3 nguồn thứ cấp CC BY (PMC13289893); bài gốc AAMC chỉ cho thuê bao",
}

NGUON_CHUAN_THEM: Dict[str, str] = {
    "SPIRIT 2025": "Chan AW et al. JAMA 2025;334(5):435-443 (PMID 40294593); E&E BMJ 2025 (PMID 40294956)",
    "PRISMA-P 2015": "Moher D et al. Syst Rev 2015;4:1 (PMID 25554246)",
    "STARD 2015": "Bossuyt PM et al. BMJ 2015;351:h5527 (PMID 26511519)",
    "TRIPOD+AI 2024": "Collins GS et al. BMJ 2024;385:e078378 (PMID 38626948)",
    "COREQ 2007": "Tong A et al. Int J Qual Health Care 2007;19(6):349-57 (PMID 17872937)",
    "SRQR 2014": "O'Brien BC et al. Acad Med 2014;89(9):1245-51 (PMID 24979285)",
    "GRAMMS 2008": "O'Cathain A et al. J Health Serv Res Policy 2008;13(2):92-8 (PMID 18416914)",
    "SQUIRE 2.0": "Ogrinc G et al. BMJ Qual Saf 2016;25(12):986-992 (PMID 26369893)",
    "CHEERS 2022": "Husereau D et al. BMJ 2022;376:e067975 (PMID 35017145)",
    "TREND 2004": "Des Jarlais DC et al. Am J Public Health 2004;94(3):361-6 (PMID 14998794)",
    "CARE 2013": "Gagnier JJ et al. J Med Case Rep 2013;7:223 (PMID 24228906)",
    "COSMIN 2021": "Gagnier JJ et al. Qual Life Res 2021;30(8):2197-2218 (PMID 33818733)",
}

# ═════════════════════════════════════ SPIRIT 2025 (rct) ═════════════════════════════════════
LAM_MU = r"mù (đơn|đôi|ba)|được làm mù|làm mù (người|đối tượng|nhân viên|thống kê|bác sĩ)|che giấu nhánh"
_SPIRIT: Dict[str, tuple] = {
    "1a": (("dau",), "bat_buoc", "Tiêu đề nêu thiết kế, quần thể, can thiệp.",
           (_y("thiết kế trong tiêu đề", r"ngẫu nhiên|thử nghiệm", de_muc=True),)),
    "1b": (("tom_tat",), "bat_buoc", "Có tóm tắt có cấu trúc về thiết kế và phương pháp.",
           (_y("tóm tắt mục tiêu", r"mục tiêu"), _y("tóm tắt thiết kế/phương pháp", r"phương pháp|thiết kế"))),
    "2": (("dau", "bia"), "bat_buoc", "Ghi số phiên bản và ngày của đề cương.",
          (_y("phiên bản", r"phiên bản|version"),)),
    "3a": (("bia", "nhan_luc"), "bat_buoc", "Nêu tên, đơn vị và vai trò người soạn đề cương.",
           (_y("người soạn/chủ nhiệm", r"chủ nhiệm|nghiên cứu viên|thành viên"),
            _y("vai trò/nhiệm vụ", VAI_TRO_NHOM))),
    "3b": (("bia", "kinh_phi", "nhan_luc"), "bat_buoc", "Nêu tên và thông tin liên hệ của đơn vị tài trợ/chủ trì.",
           (_y("đơn vị tài trợ/chủ trì", r"nhà tài trợ|đơn vị (tài trợ|chủ trì|thực hiện)|cơ quan chủ trì|tự túc"),
            _y("thông tin liên hệ", r"điện thoại|email|thư điện tử|địa chỉ|liên hệ"))),
    "3c": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu vai trò nhà tài trợ trong thiết kế, thực hiện, phân tích.",
           (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
    "3d": (("nhan_luc", "giam_sat", "quan_ly_dl"), "bat_buoc",
           "Có ban điều phối/ban chỉ đạo/hội đồng thẩm định kết cục: nêu thành phần, vai trò, trách nhiệm.",
           (_y("thành phần/vai trò", r"thành phần|vai trò|trách nhiệm|gồm"),),
           r"ban (điều phối|chỉ đạo|điều hành)|hội đồng thẩm định kết cục|đa trung tâm", "có ban điều phối/đa trung "
                                                                                         "tâm"),
    "4": (("pho_bien", "dao_duc", "bia"), "bat_buoc", "Nêu cơ quan đăng ký và số đăng ký (hoặc nơi dự kiến đăng ký).",
          (_y("cơ quan đăng ký", DANG_KY), _y("số/kế hoạch đăng ký", DANG_KY_SO))),
    "5": (("pho_bien", "quan_ly_dl", "phan_tich"), "bat_buoc", "Nêu nơi truy cập đề cương và kế hoạch phân tích.",
          (_y("truy cập đề cương/SAP", DE_CUONG_TRUY_CAP),)),
    "6": (("pho_bien", "quan_ly_dl"), "bat_buoc",
          "Nêu nơi và cách truy cập dữ liệu cá nhân đã khử định danh, từ điển dữ liệu, mã thống kê.",
          (_y("chia sẻ dữ liệu/mã", CHIA_SE_DU_LIEU),)),
    "7a": (("kinh_phi", "bia"), "bat_buoc", "Nêu nguồn kinh phí và hỗ trợ khác.", (_y("nguồn kinh phí", KINH_PHI),)),
    "7b": (("dao_duc", "bia", "kinh_phi"), "bat_buoc", "Khai xung đột lợi ích của chủ nhiệm và ban chỉ đạo.",
           (_y("xung đột lợi ích", XUNG_DOT),)),
    "8": (("pho_bien",), "bat_buoc", "Nêu kế hoạch phổ biến kết quả tới người tham gia, nhân viên y tế, công chúng.",
          (_y("kênh chuyên môn", r"tạp chí|hội (nghị|thảo)|báo cáo tại|đơn vị|nhân viên y tế"),
           _y("người tham gia/công chúng", PHO_BIEN_NGUOI_THAM_GIA))),
    "9a": (("dat_van_de", "tong_quan"), "bat_buoc",
           "Nêu cơ sở khoa học, tóm tắt nghiên cứu liên quan về cả lợi ích và tác hại của từng can thiệp.",
           (_y("trích dẫn nguồn", TRICH_DAN), _y("lợi ích", r"lợi ích|hiệu quả|cải thiện"),
            _y("tác hại", r"tác hại|nguy cơ|an toàn|bất lợi|tác dụng (phụ|không mong muốn)"))),
    "9b": (("can_thiep", "thiet_ke", "tong_quan"), "bat_buoc", "Giải thích lý do chọn nhóm so sánh.",
           (_y("lý do chọn nhóm chứng", r"lý do chọn (nhóm )?(chứng|so sánh|đối chứng)|(nhóm chứng|đối chứng|so sánh)"
                                       r".{0,160}(vì|do|nhằm|là thực hành|cho biết)"),)),
    "10": (("muc_tieu", "cau_hoi"), "bat_buoc", "Nêu mục tiêu cụ thể về lợi ích và tác hại.",
           (_y("mục tiêu cụ thể", MUC_TIEU_CU_THE),
            _y("mục tiêu về tác hại/an toàn", r"an toàn|tác hại|biến cố|bất lợi|tác dụng (phụ|không mong muốn)"))),
    "11": (("dao_duc", "quy_trinh", "thiet_ke", "pho_bien"), "bat_buoc",
           "Nêu chi tiết (hoặc kế hoạch) sự tham gia của người bệnh/công chúng vào thiết kế, thực hiện, báo cáo.",
           (_y("sự tham gia của người bệnh/công chúng", PPI),)),
    "12": (("thiet_ke",), "bat_buoc", "Nêu loại thử nghiệm, tỷ lệ phân bổ và khung so sánh (vượt trội/không kém…).",
           (_y("loại thử nghiệm", r"song song|bắt chéo|giai thừa|theo cụm|nhánh"),
            _y("tỷ lệ phân bổ", r"\b\d\s*:\s*\d\b|tỷ lệ (phân bổ|phân nhóm)"),
            _y("khung so sánh", r"vượt trội|không kém|tương đương|thăm dò|superiority|non-inferiority|equivalence"))),
    "13": (("dia_diem", "thiet_ke"), "bat_buoc", "Nêu bối cảnh và địa điểm thực hiện.", (_y("nơi thực hiện", NOI),)),
    "14a": (("doi_tuong",), "bat_buoc", "Nêu tiêu chuẩn chọn và loại người tham gia.",
            (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True), _y("tiêu chuẩn loại", TIEU_CHUAN_LOAI, de_muc=True))),
    "14b": (("doi_tuong", "can_thiep"), "bat_buoc",
            "Nêu tiêu chuẩn chọn cơ sở và người thực hiện can thiệp.",
            (_y("tiêu chuẩn cơ sở/người thực hiện", r"tiêu chuẩn.{0,80}(cơ sở|người thực hiện|điều dưỡng|phẫu thuật "
                                                   r"viên|bác sĩ thực hiện)"),),
            r"phẫu thuật viên|người thực hiện can thiệp|đa trung tâm|nhiều (cơ sở|trung tâm)",
            "can thiệp do người có kỹ năng riêng thực hiện hoặc đa cơ sở"),
    "15a": (("can_thiep",), "bat_buoc",
            "Mô tả can thiệp và nhóm chứng đủ để lặp lại: thực hiện thế nào, khi nào, bởi ai.",
            (_y("nhóm can thiệp", r"nhóm can thiệp|nhánh can thiệp"), _y("nhóm chứng", r"nhóm (đối )?chứng|nhánh "
                                                                                       r"chứng"),
             _y("liều/tần suất/thời gian", r"mỗi (ngày|tuần|tháng)|\d+\s*(lần|tin nhắn|buổi)\s*/|trong \d+ (ngày|tuần|"
                                          r"tháng)|hằng (ngày|tuần)|liều"))),
    "15b": (("can_thiep", "giam_sat", "quy_trinh", "dao_duc"), "bat_buoc",
            "Nêu tiêu chí ngừng hoặc điều chỉnh can thiệp cho từng người tham gia.",
            (_y("tiêu chí ngừng/điều chỉnh", r"(ngừng|dừng|điều chỉnh|rút khỏi)[^|\n]{0,80}\bkhi\b"),)),
    "15c": (("can_thiep",), "bat_buoc", "Nêu chiến lược tăng và cách theo dõi tuân thủ can thiệp.",
            (_y("tuân thủ", r"tuân thủ"),)),
    "15d": (("can_thiep",), "bat_buoc", "Nêu chăm sóc đồng thời được phép hoặc bị cấm.",
            (_y("chăm sóc đồng thời", r"chăm sóc (đồng thời|đi kèm)|điều trị (đi kèm|phối hợp|đồng thời)|được phép|"
                                     r"không cấm|bị cấm"),)),
    "16": (("bien_so", "bang_bien"), "bat_buoc",
           "Nêu kết cục chính và phụ: biến đo, thước đo phân tích, cách tổng hợp, thời điểm.",
           (_y("kết cục chính", r"kết cục chính"), _y("kết cục phụ", r"kết cục phụ"),
            _y("thời điểm đánh giá", r"(tại|sau|ở) (tháng|tuần|ngày|thời điểm)|tháng thứ \d+"))),
    "17": (("bien_so", "giam_sat", "quy_trinh", "dao_duc"), "bat_buoc", "Định nghĩa tác hại và cách đánh giá.",
           (_y("tác hại/biến cố bất lợi", r"biến cố (bất lợi|không mong muốn)|tác dụng (phụ|không mong muốn)|tác hại"),
            _y("cách đánh giá/ghi nhận", r"ghi nhận|đánh giá|theo dõi|thu thập|báo cáo")), None, "", True),
    "18": (("quy_trinh", "cong_cu", "tien_do"), "bat_buoc",
           "Nêu lịch trình tuyển, can thiệp, đánh giá, thăm khám (khuyến nghị có sơ đồ).",
           (_y("lịch trình đánh giá", r"(ban đầu|sàng lọc).{0,120}(tháng|tuần)|lịch (trình|thăm khám|theo dõi)|thời "
                                     r"điểm (thu thập|đánh giá)"),)),
    "19": (("co_mau",), "bat_buoc", "Nêu cách tính cỡ mẫu và mọi giả định.",
           (_y("công thức/phương pháp", CONG_THUC_CO_MAU), _y("tham số có nguồn", THAM_SO_NGUON),
            _y("cỡ mẫu cuối cùng", CO_MAU_CUOI))),
    "20": (("chon_mau", "quy_trinh", "co_mau"), "bat_buoc", "Nêu chiến lược tuyển để đạt cỡ mẫu.",
           (_y("chiến lược tuyển", r"tuyển (liên tiếp|chọn|mộ)|chiến lược tuyển|đạt (đủ )?cỡ mẫu"),)),
    "21a": (("ngau_nhien",), "bat_buoc", "Nêu ai tạo trình tự ngẫu nhiên và bằng phương pháp nào.",
            (_y("phương pháp tạo trình tự", r"(tạo|sinh) (trình tự|danh sách|chuỗi)|phần mềm|máy tính|bảng số ngẫu "
                                            r"nhiên"),
             _y("người tạo", r"thống kê viên|người (độc lập|không tham gia)|độc lập"))),
    "21b": (("ngau_nhien",), "bat_buoc", "Nêu kiểu ngẫu nhiên hoá (đơn/giới hạn) và yếu tố phân tầng.",
            (_y("kiểu ngẫu nhiên hoá", r"khối|ngẫu nhiên (đơn|giản đơn)|phân tầng|không phân tầng|tối thiểu hoá"),)),
    "22": (("ngau_nhien",), "bat_buoc", "Nêu cơ chế thực hiện và giấu trình tự phân bổ.",
           (_y("giấu phân bổ", r"giấu (phân bổ|trình tự)|phong bì|phân bổ trung tâm|qua (điện thoại|hệ thống)"),)),
    "23": (("ngau_nhien",), "bat_buoc", "Nêu người tuyển và người phân bổ có tiếp cận trình tự hay không.",
           (_y("kiểm soát tiếp cận trình tự", r"(tiếp cận|biết|giữ) (trình tự|danh sách)|người tuyển.{0,120}(không|"
                                              r"chỉ)|"
                                             r"độc lập (sinh|giữ)"),)),
    "24a": (("ngau_nhien",), "bat_buoc", "Nêu ai được làm mù sau phân bổ (hoặc nêu không làm mù).",
            (_y("làm mù", r"làm mù|che giấu|mù (đơn|đôi)|nhãn mở"),
             _y("đối tượng làm mù", r"người (tham gia|đo|đánh giá)|thống kê viên|người phân tích|bác sĩ"))),
    "24b": (("ngau_nhien", "can_thiep", "sai_so"), "bat_buoc", "Nếu làm mù: nêu cách làm mù và độ tương tự của can "
                                                               "thiệp.",
            (_y("cách làm mù", r"(giống|tương tự) nhau|giả dược|cách làm mù|che (nhãn|mã)|(không|chưa) (tham gia|có "
                               r"mặt)"
                               r".{0,60}(phân bổ|ngẫu nhiên|can thiệp|gửi tin)|tách (biệt|riêng) (vai trò|người)"),),
            LAM_MU, "có làm mù"),
    "24c": (("ngau_nhien", "giam_sat"), "bat_buoc", "Nếu làm mù: nêu hoàn cảnh và quy trình mở mù.",
            (_y("mở mù", r"mở mù|giải mù|phá mù"),), LAM_MU, "có làm mù"),
    "25a": (("cong_cu", "quy_trinh", "quan_ly_dl"), "bat_buoc",
            "Nêu kế hoạch thu thập dữ liệu, biện pháp bảo đảm chất lượng, công cụ và nơi để phiếu thu thập.",
            (_y("biện pháp chất lượng", r"chuẩn hoá|chuẩn hóa|tập huấn|đo (hai|2) lần|đối chiếu|kiểm soát chất lượng"),
             _y("phiếu/công cụ", r"phụ lục|phiếu|công cụ"))),
    "25b": (("quy_trinh", "can_thiep", "cong_cu", "sai_so", "dao_duc"), "bat_buoc",
            "Nêu kế hoạch duy trì người tham gia, theo dõi đầy đủ, kể cả người ngừng can thiệp.",
            (_y("biện pháp duy trì", r"duy trì (người tham gia|theo dõi)|giảm (tỷ lệ )?(mất|bỏ) theo dõi|nhắc (lịch|"
                                     r"hẹn)|"
                                    r"gọi (điện )?nhắc|hỗ trợ (đi lại|chi phí)"),
             _y("theo dõi người ngừng can thiệp", r"(ngừng|rút khỏi|vi phạm|bỏ).{0,120}(vẫn|tiếp tục|sẽ) (được )?(liên "
                                                  r"hệ|"
                                                 r"theo dõi|thu thập)"))),
    "26": (("quan_ly_dl", "cong_cu"), "bat_buoc",
           "Nêu kế hoạch nhập liệu, mã hoá, bảo mật, lưu trữ và biện pháp chất lượng dữ liệu.",
           (_y("nhập liệu/kiểm chất lượng", CHAT_LUONG_DL), _y("bảo mật/lưu trữ", r"bảo mật|lưu (trữ|tại)|mã hoá|mã "
                                                                                  r"hóa"))),
    "27a": (("phan_tich",), "bat_buoc", "Nêu phương pháp thống kê so sánh các nhóm cho kết cục chính và phụ.",
            (_y("phương pháp thống kê", PP_THONG_KE), _y("kết cục chính", r"kết cục chính|phân tích chính"))),
    "27b": (("phan_tich",), "bat_buoc", "Định nghĩa quần thể của từng phân tích (vd theo ý định điều trị).",
            (_y("quần thể phân tích", r"ý định điều trị|\bITT\b|theo đề cương|per[- ]protocol|(mọi|tất cả) (người|đối "
                                      r"tượng)"
                                     r" (được )?(ngẫu nhiên|phân bổ)"),)),
    "27c": (("phan_tich",), "bat_buoc", "Nêu cách xử lý dữ liệu thiếu trong phân tích.",
            (_y("dữ liệu thiếu", DU_LIEU_THIEU), _y("phương pháp xử lý", XU_LY_THIEU)), None, "", True),
    "27d": (("phan_tich", "du_kien_kq"), "bat_buoc", "Nêu phương pháp các phân tích bổ sung (phân nhóm, độ nhạy).",
            (_y("phân tích bổ sung", r"phân tích (độ nhạy|phân nhóm|nhóm nhỏ)"),)),
    "28a": (("giam_sat", "dao_duc", "quan_ly_dl", "nhan_luc"), "bat_buoc",
            "Nêu thành phần, vai trò, tính độc lập của hội đồng giám sát dữ liệu — hoặc giải thích vì sao không cần.",
            (_y("hội đồng giám sát dữ liệu", r"hội đồng (giám sát|theo dõi)|\bDMC\b|\bDSMB\b|ban (giám sát|theo dõi) "
                                             r"(dữ liệu|an toàn)"),
             _y("thành phần/độc lập/lý do không cần", r"độc lập|thành phần|gồm|không (cần|thành lập)|vì"))),
    "28b": (("phan_tich", "giam_sat", "dao_duc"), "bat_buoc", "Nêu phân tích giữa kỳ và quy tắc dừng (hoặc nêu không "
                                                              "có).",
            (_y("giữa kỳ/quy tắc dừng", r"phân tích giữa kỳ|quy tắc dừng|dừng sớm"),)),
    "29": (("giam_sat", "quan_ly_dl", "dao_duc"), "bat_buoc",
           "Nêu tần suất và quy trình giám sát việc thực hiện thử nghiệm (hoặc giải thích nếu không giám sát).",
           (_y("giám sát thực hiện", r"giám sát (việc )?(thực hiện|tuân thủ|chất lượng|thử nghiệm|nghiên cứu)|kiểm tra "
                                    r"(định kỳ|tại chỗ)|monitor|thẩm tra|không (có|thực hiện) giám sát"),
            _y("tần suất/quy trình", r"định kỳ|hằng (tháng|quý|tuần)|mỗi|tần suất|vì")), None, "", True),
    "30": (("dao_duc",), "bat_buoc", "Nêu kế hoạch xin chấp thuận của Hội đồng Đạo đức.", (_y("Hội đồng Đạo "
                                                                                              "đức", HOI_DONG),)),
    "31": (("dao_duc", "quan_ly_dl", "pho_bien"), "bat_buoc",
           "Nêu kế hoạch thông báo các sửa đổi quan trọng của đề cương tới các bên liên quan.",
           (_y("thông báo sửa đổi đề cương", SUA_DOI_DE_CUONG),)),
    "32a": (("dao_duc", "quy_trinh"), "bat_buoc", "Nêu ai lấy đồng thuận và lấy như thế nào.",
            (_y("cách lấy đồng thuận", r"(giải thích|ký) .{0,80}(phiếu|đồng ý|đồng thuận)|phiếu (đồng ý|tình "
                                       r"nguyện)"),)),
    "32b": (("dao_duc",), "bat_buoc", "Nêu đồng thuận bổ sung cho mẫu sinh học/nghiên cứu phụ.",
            (_y("đồng thuận bổ sung", r"đồng (ý|thuận).{0,120}(mẫu|lưu|nghiên cứu (phụ|khác|tương lai))"),),
            r"mẫu sinh học|lưu (trữ )?mẫu|nghiên cứu (phụ|tương lai)", "có mẫu sinh học hoặc nghiên cứu phụ"),
    "33": (("dao_duc", "quan_ly_dl"), "bat_buoc", "Nêu cách thu thập, chia sẻ, lưu giữ thông tin cá nhân để bảo mật.",
           (_y("bảo mật thông tin cá nhân", BAO_MAT), _y("giới hạn truy cập", TRUY_CAP_GIOI_HAN))),
    "34": (("dao_duc",), "bat_buoc", "Nêu chăm sóc sau thử nghiệm và bồi thường khi có tổn hại.",
           (_y("chăm sóc sau thử nghiệm/bồi thường", r"bồi thường|chăm sóc sau (thử nghiệm|nghiên cứu)|bảo hiểm "
                                                     r"(nghiên cứu|"
                                                    r"trách nhiệm)|chi trả.{0,60}(tổn hại|biến cố|điều trị)|(được|sẽ) "
                                                    r"(điều "
                                                    r"trị|xử trí|chăm sóc).{0,60}(miễn phí|không mất phí|do tổn "
                                                    r"hại)"),)),
}

# ═════════════════════════════════════ PRISMA-P 2015 (systematic_review) ═════════════════════════════════════
_PRISMA_P: Dict[str, tuple] = {
    "1a": (("dau",), "bat_buoc", "Tiêu đề nêu đây là đề cương tổng quan hệ thống.",
           (_y("tổng quan hệ thống trong tiêu đề", r"tổng quan (hệ thống|có hệ thống)|phân tích gộp", de_muc=True),)),
    "1b": (("dau", "bia"), "bat_buoc", "Đề cương cập nhật một tổng quan: nêu rõ.",
           (_y("nêu là bản cập nhật", r"cập nhật"),), r"cập nhật (của |cho )?(một )?tổng quan", "cập nhật tổng quan "
                                                                                                "cũ"),
    "2": (("pho_bien", "dao_duc", "bia"), "bat_buoc", "Nêu cơ quan đăng ký (vd PROSPERO) và số đăng ký.",
          (_y("cơ quan đăng ký", r"PROSPERO|\bOSF\b|INPLASY|đăng ký"), _y("số/kế hoạch đăng ký", DANG_KY_SO))),
    "3a": (("bia", "nhan_luc"), "bat_buoc", "Nêu tên, đơn vị, email tác giả; địa chỉ tác giả liên hệ.",
           (_y("tác giả", r"chủ nhiệm|tác giả|nghiên cứu viên"), _y("liên hệ", r"email|thư điện tử|@|địa chỉ|điện "
                                                                               r"thoại"))),
    "3b": (("nhan_luc", "bia"), "bat_buoc", "Nêu đóng góp của từng tác giả và người bảo đảm của tổng quan.",
           (_y("đóng góp/phân công", r"đóng góp|" + VAI_TRO_NHOM),
            _y("người bảo đảm", r"bảo đảm|chịu trách nhiệm (chính|chung|toàn bộ)|guarantor"))),
    "4": (("bia", "dao_duc", "pho_bien", "quan_ly_dl"), "bat_buoc",
          "Nêu kế hoạch ghi nhận các sửa đổi quan trọng của đề cương.", (_y("ghi nhận sửa đổi", SUA_DOI_DE_CUONG),)),
    "5a": (("kinh_phi", "bia"), "bat_buoc", "Nêu nguồn kinh phí/hỗ trợ.", (_y("nguồn kinh phí", KINH_PHI),)),
    "5b": (("kinh_phi", "bia"), "bat_buoc", "Nêu tên nhà tài trợ hoặc đơn vị cấp kinh phí.",
           (_y("tên nhà tài trợ/đơn vị", r"nhà tài trợ|đơn vị (cấp|tài trợ|chủ trì)|tự túc|kinh phí (đơn vị|từ|"
                                         r"của)"),)),
    "5c": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu vai trò nhà tài trợ trong xây dựng đề cương.",
           (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
    "6": (("dat_van_de", "tong_quan"), "bat_buoc", "Nêu lý do thực hiện tổng quan trong bối cảnh hiểu biết hiện có.",
          (_y("trích dẫn nguồn", TRICH_DAN), _y("lý do/khoảng trống", r"khoảng trống|chưa (có|thấy|được)|cần (thiết|"
                                                                      r"có)"))),
    "7": (("muc_tieu", "cau_hoi"), "bat_buoc", "Nêu câu hỏi của tổng quan theo người tham gia, can thiệp, so sánh, kết "
                                               "cục.",
          (_y("quần thể", r"\bPICO\b|quần thể|người (bệnh|tham gia)|ở người"),
           _y("can thiệp/phơi nhiễm", r"can thiệp|phơi nhiễm|điều trị|thuốc|\bSGLT2"),
           _y("so sánh", r"so (sánh|với)|đối chứng|giả dược"), _y("kết cục", r"kết cục|tử vong|nhập viện|biến cố"))),
    "8": (("doi_tuong", "chon_nc"), "bat_buoc",
          "Nêu tiêu chuẩn chọn: đặc điểm nghiên cứu (PICO, thiết kế) và đặc điểm báo cáo (năm, ngôn ngữ, tình trạng "
          "xuất "
          "bản).",
          (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True),
           _y("thiết kế nghiên cứu được chọn", r"thử nghiệm|\bRCT\b|thiết kế|loại nghiên cứu"),
           _y("đặc điểm báo cáo", r"ngôn ngữ|năm (xuất bản|công bố)|tình trạng (xuất bản|công bố)|tiếng Anh|"
                                 r"không giới hạn"))),
    "9": (("tim_kiem",), "bat_buoc", "Liệt kê mọi nguồn thông tin dự kiến kèm khoảng thời gian bao phủ.",
          (_y("cơ sở dữ liệu", r"PubMed|MEDLINE|Embase|Cochrane|CENTRAL|Scopus|Web of Science"),
           _y("thời gian bao phủ", r"từ .{0,60}(đến|tới) .{0,30}\d|khởi (đầu|tạo)|từ khi (thành lập|bắt đầu)|không "
                                   r"giới "
                                   r"hạn (thời gian|năm)|thời gian bao phủ"),
           _y("nguồn khác/tài liệu xám", r"tài liệu xám|đăng ký thử nghiệm|ClinicalTrials|ICTRP|liên hệ tác giả|"
                                         r"danh mục tham khảo"))),
    "10": (("tim_kiem", "phu_luc_tim"), "bat_buoc", "Trình bày dự thảo chiến lược tìm cho ít nhất một cơ sở dữ liệu.",
           (_y("câu lệnh tìm", r"\bAND\b|\bOR\b|\[MeSH|\[tiab|\[Mesh|\[pt\]"),)),
    "11a": (("quan_ly_dl", "chon_nc", "tim_kiem"), "bat_buoc", "Nêu cách quản lý hồ sơ và dữ liệu trong tổng quan.",
            (_y("quản lý hồ sơ/dữ liệu", r"EndNote|Zotero|Rayyan|Covidence|ASReview|phần mềm quản lý|quản lý (hồ sơ|"
                                         r"tài "
                                        r"liệu|trích dẫn|dữ liệu)|loại (bản )?trùng"),)),
    "11b": (("chon_nc",), "bat_buoc", "Nêu quy trình chọn nghiên cứu (vd hai người độc lập) qua từng giai đoạn.",
            (_y("người độc lập", r"(hai|2) (người|nghiên cứu viên).{0,60}độc lập|độc lập"),
             _y("các giai đoạn", r"tiêu đề|tóm tắt|toàn văn"))),
    "11c": (("trich_xuat", "phan_tich", "sai_so"), "bat_buoc",
            "Nêu cách trích xuất dữ liệu (thử biểu mẫu, độc lập, lặp đôi) và cách xin dữ liệu từ tác giả.",
            (_y("trích xuất độc lập/lặp đôi", r"độc lập|(hai|2) người|lặp (đôi|lại)|thử (nghiệm )?(biểu mẫu|phiếu)"),
             _y("xin dữ liệu từ tác giả", r"liên hệ (tác giả|nhà nghiên cứu)|xin (thêm )?dữ liệu"))),
    "12": (("trich_xuat", "bien_so", "phan_tich", "bang_bien"), "bat_buoc",
           "Liệt kê và định nghĩa mọi biến cần trích xuất, các giả định định trước.",
           (_y("biến trích xuất", r"(biến|dữ liệu|thông tin) (cần |được )?trích xuất|trích xuất.{0,80}(thiết kế|cỡ mẫu|"
                                  r"đặc điểm|tài trợ)|đặc điểm (các |của )?nghiên cứu.{0,80}(thiết kế|cỡ mẫu|quần thể|"
                                  r"can thiệp)"),)),
    "13": (("bien_so", "trich_xuat"), "bat_buoc", "Liệt kê và định nghĩa kết cục, phân thứ tự ưu tiên kèm lý do.",
           (_y("kết cục chính", r"kết cục chính"), _y("kết cục phụ", r"kết cục phụ"))),
    "14": (("nguy_co",), "bat_buoc",
           "Nêu phương pháp đánh giá nguy cơ sai lệch (mức nghiên cứu/kết cục) và cách dùng trong tổng hợp.",
           (_y("công cụ nguy cơ sai lệch", r"RoB ?2|ROBINS|Newcastle|QUADAS|AMSTAR|nguy cơ sai lệch"),
            _y("dùng trong tổng hợp", r"phân tích độ nhạy|\bGRADE\b|loại (bỏ )?(thử nghiệm|nghiên cứu).{0,40}nguy cơ "
                                      r"sai "
                                     r"lệch|(phân nhóm|theo) (mức )?nguy cơ sai lệch"))),
    "15a": (("tong_hop", "phan_tich"), "bat_buoc", "Nêu tiêu chí quyết định tổng hợp định lượng.",
            (_y("điều kiện gộp", r"(gộp|tổng hợp định lượng|phân tích gộp) (chỉ )?(khi|nếu)|điều kiện (để )?gộp|(đủ|"
                                 r"có) "
                                 r"(tương đồng|đồng nhất) (lâm sàng|về).{0,80}(gộp|phân tích gộp)"),)),
    "15b": (("tong_hop", "phan_tich"), "bat_buoc",
            "Nêu thước đo tổng hợp, phương pháp gộp và cách khảo sát tính nhất quán (vd I²).",
            (_y("thước đo hiệu ứng", r"\bRR\b|\bOR\b|\bHR\b|\bMD\b|\bSMD\b|tỷ số (nguy cơ|chênh|rủi ro)"),
             _y("mô hình gộp", r"hiệu ứng ngẫu nhiên|hiệu ứng cố định|DerSimonian|\bREML\b|Hartung|Mantel"),
             _y("tính không đồng nhất", r"I²|\bI2\b|không đồng nhất|dị biệt|\bτ|tau"))),
    "15c": (("tong_hop", "phan_tich"), "bat_buoc", "Nêu các phân tích bổ sung (độ nhạy, phân nhóm, hồi quy gộp).",
            (_y("phân tích bổ sung", r"phân tích (độ nhạy|phân nhóm|nhóm nhỏ)|hồi quy gộp|meta-regression"),)),
    "15d": (("tong_hop", "phan_tich"), "bat_buoc", "Nêu cách tóm tắt khi không gộp định lượng được.",
            (_y("tổng hợp không định lượng", r"tổng hợp (mô tả|tường thuật|định tính)|\bSWiM\b|không (phù hợp|thể) gộp|"
                                            r"không gộp"),)),
    "16": (("nguy_co", "tong_hop", "phan_tich"), "bat_buoc",
           "Nêu đánh giá sai lệch tổng thể (sai lệch xuất bản, báo cáo chọn lọc).",
           (_y("sai lệch xuất bản/báo cáo chọn lọc", r"sai lệch (xuất bản|công bố)|biểu đồ phễu|funnel|Egger|báo cáo "
                                                     r"chọn "
                                                    r"lọc"),)),
    "17": (("tong_hop", "phan_tich", "nguy_co"), "bat_buoc", "Nêu cách đánh giá độ tin cậy của tập chứng cứ (vd "
                                                             "GRADE).",
           (_y("độ tin cậy tập chứng cứ", r"\bGRADE\b|độ (tin cậy|chắc chắn) (của )?(bằng chứng|chứng cứ)"),)),
}

# ═════════════════════════════════════ STARD 2015 (diagnostic) ═════════════════════════════════════
XET_NGHIEM_DANH_GIA = (r"xét nghiệm (chỉ điểm|được đánh giá|cần đánh giá|đánh giá|đang (được )?đánh giá)|test (chỉ "
                       r"điểm|đánh giá)")
CHUAN_THAM_CHIEU = r"(tiêu )?chuẩn (tham chiếu|vàng)|reference standard"
LY_DO_NGUONG = (r"(ngưỡng|điểm cắt).{0,160}(theo (khuyến cáo|y văn|hướng dẫn)|\[\d+|vì|do|dựa (trên|vào)|được (khuyến "
                r"cáo|"
                r"dùng))|(khuyến cáo|hướng dẫn|y văn).{0,80}(ngưỡng|điểm cắt)")
XAM_LAN = r"sinh thiết|nội soi|chọc (dò|hút)|xâm lấn|thủ thuật|cản quang"
_STARD: Dict[str, tuple] = {
    "1": ((), "bao_cao", "Tiêu đề/tóm tắt nêu đây là nghiên cứu độ chính xác chẩn đoán.", ()),
    "2": ((), "bao_cao", "Tóm tắt có cấu trúc bài báo.", ()),
    "3": (("dat_van_de", "tong_quan"), "bat_buoc",
          "Nêu bối cảnh khoa học–lâm sàng, mục đích sử dụng và vai trò lâm sàng của xét nghiệm đánh giá.",
          (_y("trích dẫn nguồn", TRICH_DAN),
           _y("vai trò/mục đích sử dụng xét nghiệm", r"vai trò|(mục đích|vị trí) (sử dụng|của)|sàng lọc|phân loại|thay "
                                                    r"thế|bổ sung|phân tầng"))),
    "4": (("muc_tieu", "cau_hoi"), "bat_buoc", "Nêu mục tiêu và giả thuyết (về độ chính xác kỳ vọng).",
          (_y("mục tiêu độ chính xác", r"độ nhạy|độ đặc hiệu|\bAUC\b|giá trị (dự (đoán|báo)|chẩn đoán)|độ chính xác"),
           _y("giả thuyết", r"giả thuyết|kỳ vọng|không thấp hơn|tối thiểu"))),
    "5": (("thiet_ke",), "bat_buoc", "Nêu thu thập dữ liệu được lập kế hoạch trước (tiến cứu) hay sau (hồi cứu).",
          (_y("tiến cứu/hồi cứu", r"tiến cứu|hồi cứu"),)),
    "6": (("doi_tuong",), "bat_buoc", "Nêu tiêu chuẩn chọn và loại.",
          (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True), _y("tiêu chuẩn loại", TIEU_CHUAN_LOAI, de_muc=True))),
    "7": (("doi_tuong", "chon_mau"), "bat_buoc",
          "Nêu căn cứ xác định người đủ tiêu chuẩn (triệu chứng, kết quả trước, sổ đăng ký).",
          (_y("căn cứ xác định", r"triệu chứng|nghi ngờ|được chỉ định|kết quả (xét nghiệm )?trước|sổ đăng ký|danh sách|"
                                 r"đến khám|có chỉ định"),)),
    "8": (("dia_diem", "chon_mau"), "bat_buoc", "Nêu nơi và thời gian xác định người tham gia.",
          (_y("nơi", NOI), _y("thời gian", NGAY))),
    "9": (("chon_mau",), "bat_buoc", "Nêu người tham gia là chuỗi liên tiếp, ngẫu nhiên hay thuận tiện.",
          (_y("kiểu chuỗi", r"liên tiếp|ngẫu nhiên|thuận tiện|toàn bộ"),)),
    "10a": (("xet_nghiem", "cong_cu", "bien_so", "quy_trinh"), "bat_buoc", "Mô tả xét nghiệm đánh giá đủ để lặp lại.",
            (_y("xét nghiệm đánh giá", XET_NGHIEM_DANH_GIA),
             _y("cách thực hiện/tính", r"công thức|tính (theo|bằng|từ)|\bđo\b|thực hiện|máy|bộ (xét nghiệm|thuốc "
                                       r"thử)")),
            None, "", True),
    "10b": (("xet_nghiem", "cong_cu", "bien_so", "quy_trinh"), "bat_buoc", "Mô tả tiêu chuẩn tham chiếu đủ để lặp lại.",
            (_y("tiêu chuẩn tham chiếu", CHUAN_THAM_CHIEU),
             _y("cách thực hiện", r"thực hiện|\bđo\b|sinh thiết|đàn hồi|siêu âm|máy|kỹ thuật")), None, "", True),
    "11": (("xet_nghiem", "thiet_ke", "bien_so", "tong_quan"), "bat_buoc",
           "Nêu lý do chọn tiêu chuẩn tham chiếu (nếu có lựa chọn khác).",
           (_y("lý do chọn chuẩn tham chiếu", r"(tiêu )?chuẩn (tham chiếu|vàng).{0,200}(vì|do|lý do|được (chấp nhận|"
                                              r"khuyến "
                                             r"cáo|dùng rộng rãi)|thay (cho|thế))|lý do chọn"),)),
    "12a": (("xet_nghiem", "bien_so", "phan_tich"), "bat_buoc",
            "Định nghĩa và nêu lý do ngưỡng dương tính của xét nghiệm đánh giá, phân biệt định trước với thăm dò.",
            (_y("ngưỡng/điểm cắt", r"ngưỡng|điểm cắt"),
             _y("định trước hay thăm dò", r"định trước|tiền định|xác định trước|thăm dò|Youden"),
             _y("lý do chọn ngưỡng", LY_DO_NGUONG))),
    "12b": (("xet_nghiem", "bien_so", "phan_tich"), "bat_buoc",
            "Định nghĩa và nêu lý do ngưỡng/phân loại của tiêu chuẩn tham chiếu.",
            (_y("ngưỡng của chuẩn tham chiếu", r"(tiêu )?chuẩn (tham chiếu|vàng).{0,200}(ngưỡng|≥|>|điểm cắt|giai đoạn|"
                                              r"phân độ|\bkPa\b|\bF[0-4]\b)|(ngưỡng|≥|điểm cắt).{0,120}(tiêu )?chuẩn "
                                              r"(tham chiếu|vàng)"),
             _y("lý do chọn ngưỡng", LY_DO_NGUONG))),
    "13a": (("xet_nghiem", "sai_so", "quy_trinh"), "bat_buoc",
            "Nêu người thực hiện/đọc xét nghiệm đánh giá có biết thông tin lâm sàng và kết quả chuẩn tham chiếu không.",
            (_y("làm mù người đọc xét nghiệm đánh giá", r"(người (thực hiện|tính|đọc) |)(xét nghiệm (cần |chỉ điểm|"
                                                        r"được )?đánh"
                                                       r" giá|xét nghiệm chỉ điểm).{0,160}(không biết|che giấu|làm mù|"
                                                       r"trước "
                                                       r"khi có) .{0,60}(tiêu )?chuẩn (tham chiếu|vàng)|(tính|thực "
                                                       r"hiện|đọc)"
                                                       r".{0,80}trước khi (có|biết) kết quả (tiêu )?chuẩn"),)),
    "13b": (("xet_nghiem", "sai_so", "quy_trinh"), "bat_buoc",
            "Nêu người đánh giá chuẩn tham chiếu có biết thông tin lâm sàng và kết quả xét nghiệm đánh giá không.",
            (_y("làm mù người đánh giá chuẩn tham chiếu", r"(tiêu )?chuẩn (tham chiếu|vàng).{0,200}(không biết|che "
                                                          r"giấu|"
                                                          r"làm mù|độc lập)|(không biết|che giấu|làm mù|độc "
                                                          r"lập).{0,200}"
                                                          r"(tiêu )?chuẩn (tham chiếu|vàng)"),)),
    "14": (("phan_tich",), "bat_buoc", "Nêu phương pháp ước lượng/so sánh độ chính xác chẩn đoán.",
           (_y("chỉ số chính xác", r"độ nhạy|độ đặc hiệu|\bAUC\b|giá trị dự (báo|đoán)|tỷ số khả dĩ|\bLR\b"),
            _y("độ chính xác ước lượng", r"khoảng tin cậy|KTC|Wilson|Clopper|DeLong|bootstrap"))),
    "15": (("phan_tich", "xet_nghiem", "du_kien_kq"), "bat_buoc", "Nêu cách xử lý kết quả không xác định.",
           (_y("kết quả không xác định", r"không xác định|không (kết luận|phân loại) được|vùng xám|trung gian|"
                                        r"indeterminate"),)),
    "16": (("phan_tich", "quan_ly_dl"), "bat_buoc", "Nêu cách xử lý dữ liệu thiếu của xét nghiệm đánh giá và chuẩn "
                                                    "tham chiếu.",
           (_y("dữ liệu thiếu", DU_LIEU_THIEU), _y("phương pháp xử lý", XU_LY_THIEU)), None, "", True),
    "17": (("phan_tich",), "bat_buoc", "Nêu phân tích biến thiên độ chính xác, phân biệt định trước với thăm dò.",
           (_y("phân nhóm định trước/thăm dò", r"(nhóm nhỏ|phân nhóm|phân tầng).{0,120}(định trước|tiền định|xác định "
                                               r"trước|"
                                               r"thăm dò)|(định trước|tiền định|thăm dò).{0,120}(nhóm nhỏ|phân "
                                               r"nhóm)"),),
           r"phân (nhóm|tầng)|nhóm nhỏ", "có phân tích phân nhóm"),
    "18": (("co_mau",), "bat_buoc", "Nêu cỡ mẫu dự kiến và cách xác định.",
           (_y("công thức/phương pháp", CONG_THUC_CO_MAU), _y("cỡ mẫu cuối cùng", CO_MAU_CUOI))),
    "19": (("du_kien_kq", "quy_trinh", "chon_mau"), "ke_hoach", "Lên kế hoạch sơ đồ luồng người tham gia.",
           (_y("sơ đồ luồng", SO_DO),)),
    "20": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch bảng đặc điểm nhân khẩu–lâm sàng ban đầu.",
           (_y("bảng đặc điểm", r"Đặc điểm (chung|đối tượng|nền|người tham gia)", de_muc=True),)),
    "21a": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch mô tả phân bố mức độ bệnh ở người có bệnh đích.",
            (_y("phân bố mức độ bệnh", r"mức độ (nặng|bệnh|xơ ho[áa])|giai đoạn|phân độ|\bF[0-4]\b"),)),
    "21b": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch mô tả chẩn đoán khác ở người không có bệnh đích.",
            (_y("chẩn đoán khác", r"chẩn đoán (khác|thay thế)|nguyên nhân khác|bệnh (gan )?khác"),)),
    "22": (("quy_trinh", "xet_nghiem", "doi_tuong"), "bat_buoc",
           "Nêu khoảng thời gian (và can thiệp) cho phép giữa xét nghiệm đánh giá và chuẩn tham chiếu.",
           (_y("khoảng thời gian giữa hai xét nghiệm", r"khoảng (thời gian|cách)|trong (cùng |vòng )?\d+ (ngày|tuần|"
                                                       r"giờ)|"
                                                       r"cùng (ngày|thời điểm|lần|đợt)|không quá \d+|cách nhau"),)),
    "23": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch bảng chéo kết quả xét nghiệm đánh giá với chuẩn tham "
                                                    "chiếu.",
           (_y("bảng chéo", r"bảng (2\s*[x×]\s*2|chéo|tiếp liên|hai chiều)"),)),
    "24": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch trình bày ước lượng độ chính xác kèm khoảng tin cậy.",
           (_y("khoảng tin cậy", r"KTC|khoảng tin cậy|\bCI\b"),)),
    "25": (("du_kien_kq", "dao_duc", "giam_sat"), "ke_hoach",
           "Lên kế hoạch ghi nhận biến cố bất lợi do thực hiện xét nghiệm đánh giá hoặc chuẩn tham chiếu.",
           (_y("biến cố bất lợi", r"biến cố|tai biến|bất lợi|an toàn"),), XAM_LAN, "có xét nghiệm xâm lấn"),
    "26": (("han_che", "ban_luan", "sai_so"), "ke_hoach", "Bàn hạn chế: nguồn sai lệch, bất định thống kê, khả năng "
                                                          "suy rộng.",
           (_y("hạn chế/sai lệch", HAN_CHE, de_muc=True), _y("suy rộng", SUY_RONG))),
    "27": (("ban_luan", "han_che", "du_kien_kq"), "ke_hoach", "Bàn ý nghĩa cho thực hành và vai trò lâm sàng của xét "
                                                              "nghiệm.",
           (_y("ý nghĩa thực hành", r"ý nghĩa (thực hành|lâm sàng)|thực hành|vai trò|áp dụng"),)),
    "28": (("pho_bien", "dao_duc", "bia"), "bat_buoc", "Nêu cơ quan và số đăng ký (hoặc kế hoạch đăng ký).",
           (_y("đăng ký", DANG_KY), _y("số/kế hoạch đăng ký", DANG_KY_SO))),
    "29": (("pho_bien", "quan_ly_dl"), "bat_buoc", "Nêu nơi truy cập đề cương đầy đủ.",
           (_y("truy cập đề cương", DE_CUONG_TRUY_CAP),)),
    "30": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu nguồn kinh phí và vai trò nhà tài trợ.",
           (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
}

# ═════════════════════════════════════ TRIPOD+AI 2024 (prediction) ═════════════════════════════════════
PHAT_TRIEN_MH = r"(xây dựng|phát triển) (một |mới )?(mô hình|thang điểm|công cụ dự báo)"
DANH_GIA_MH_CO_SAN = (r"(kiểm định|đánh giá|thẩm định) (ngoại|bên ngoài|lại)?\s*(mô hình|thang điểm|công cụ).{0,60}"
                      r"(đã có|hiện có|sẵn có|đã công bố|đã được (phát triển|xây dựng))")
_TRIPOD_AI: Dict[str, tuple] = {
    "1": ((), "bao_cao", "Tiêu đề nêu xây dựng/đánh giá mô hình dự báo đa biến, quần thể đích và kết cục.", ()),
    "2": ((), "bao_cao", "Tóm tắt theo TRIPOD+AI for Abstracts.", ()),
    "3a": (("dat_van_de", "tong_quan"), "bat_buoc",
           "Nêu bối cảnh chăm sóc (chẩn đoán hay tiên lượng), lý do xây dựng/đánh giá, dẫn mô hình đã có.",
           (_y("trích dẫn nguồn", TRICH_DAN), _y("chẩn đoán/tiên lượng", r"tiên lượng|chẩn đoán|dự báo"),
            _y("mô hình đã có", r"mô hình (hiện có|đã có|trước|đã công bố)|thang điểm|công cụ (hiện có|sẵn có)"))),
    "3b": (("dat_van_de", "muc_tieu", "doi_tuong", "tong_quan"), "bat_buoc",
           "Nêu quần thể đích và mục đích sử dụng mô hình trong lộ trình chăm sóc, kể cả người dùng dự kiến.",
           (_y("mục đích sử dụng/người dùng", r"người (sử dụng|dùng)|mục đích (sử dụng|của mô hình)|thời điểm (sử dụng|"
                                              r"áp "
                                             r"dụng)|lộ trình (chăm sóc|điều trị)|hỗ trợ (quyết định|phân tầng|bác sĩ)|"
                                             r"để "
                                             r"(bác sĩ|nhân viên y tế|điều dưỡng)"),)),
    "3c": (("dat_van_de", "tong_quan"), "bat_buoc", "Nêu bất bình đẳng sức khoẻ đã biết giữa các nhóm dân số.",
           (_y("bất bình đẳng giữa nhóm", r"bất bình đẳng|công bằng|chênh lệch (giữa|theo)|khác biệt (giữa|theo) (nhóm|"
                                         r"giới|tuổi|vùng)"),)),
    "4": (("muc_tieu", "cau_hoi"), "bat_buoc", "Nêu mục tiêu: xây dựng hay đánh giá mô hình (hoặc cả hai).",
          (_y("mục tiêu xây dựng/đánh giá", r"xây dựng|phát triển|kiểm định|đánh giá (hiệu năng|mô hình)"),)),
    "5a": (("cong_cu", "quy_trinh", "doi_tuong", "thiet_ke", "quan_ly_dl"), "bat_buoc",
           "Mô tả nguồn dữ liệu riêng cho tập phát triển và tập đánh giá, lý do chọn và tính đại diện.",
           (_y("nguồn dữ liệu", r"nguồn (dữ liệu|số liệu)|hồ sơ|bệnh án|\bHIS\b|sổ đăng ký|thuần tập"),
            _y("tập phát triển/đánh giá", r"(tập|dữ liệu) (phát triển|huấn luyện|kiểm định|đánh giá)|bootstrap|kiểm "
                                          r"định "
                                         r"(nội|ngoại|chéo)"))),
    "5b": (("dia_diem", "thiet_ke", "doi_tuong"), "bat_buoc", "Nêu mốc thời gian tuyển và kết thúc theo dõi.",
           (_y("mốc ngày", NGAY), _y("tuyển/theo dõi", r"theo dõi|thu thập|tuyển|nhập viện|trích xuất"))),
    "6a": (("dia_diem", "thiet_ke"), "bat_buoc", "Nêu bối cảnh (tuyến chăm sóc), số và vị trí cơ sở.",
           (_y("bối cảnh/cơ sở", NOI),)),
    "6b": (("doi_tuong",), "bat_buoc", "Nêu tiêu chuẩn chọn và loại.",
           (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True), _y("tiêu chuẩn loại", TIEU_CHUAN_LOAI, de_muc=True))),
    "6c": (("doi_tuong", "bien_so", "phan_tich"), "bat_buoc",
           "Nêu điều trị người tham gia nhận và cách xử lý điều trị khi xây dựng/đánh giá mô hình.",
           (_y("điều trị và cách xử lý", r"điều trị.{0,160}(xử lý|tính đến|đưa vào|hiệu chỉnh|không đưa|bỏ qua|biến|"
                                         r"yếu tố"
                                        r" dự báo)"),)),
    "7": (("quan_ly_dl", "phan_tich", "cong_cu"), "bat_buoc",
          "Mô tả tiền xử lý và kiểm tra chất lượng dữ liệu, có tương tự giữa các nhóm/nguồn không.",
          (_y("tiền xử lý/kiểm tra chất lượng", r"tiền xử lý|làm sạch|kiểm (tra )?(chất lượng|logic|phạm vi)|chuẩn hoá|"
                                               r"luật kiểm"),)),
    "8a": (("bien_so", "du_bao"), "bat_buoc",
           "Định nghĩa kết cục dự báo và khoảng thời gian dự báo, cách và thời điểm đánh giá.",
           (_y("kết cục", r"kết cục"), _y("khoảng dự báo", r"(trong|sau) (vòng )?\d+ (ngày|tháng|năm)|khoảng (thời "
                                                           r"gian )?"
                                                          r"dự báo|horizon"),
            _y("cách xác định", r"xác định (bằng|qua|theo|là)|ghi nhận|đánh giá")), None, "", True),
    "8b": (("bien_so", "quy_trinh"), "bat_buoc", "Kết cục cần đánh giá chủ quan: nêu trình độ người đánh giá.",
           (_y("trình độ người đánh giá", r"(bác sĩ|chuyên gia|người đánh giá).{0,80}(chuyên khoa|kinh nghiệm|trình "
                                          r"độ)"),),
           r"hội đồng (thẩm định|xác định) kết cục|đánh giá (chủ quan|lâm sàng) kết cục|adjudicat",
           "kết cục cần đánh giá chủ quan"),
    "8c": (("bien_so", "sai_so", "quy_trinh"), "bat_buoc", "Nêu biện pháp làm mù khi đánh giá kết cục (hoặc nêu "
                                                           "không).",
           (_y("làm mù đánh giá kết cục", r"(không biết|làm mù|che giấu|độc lập|không được (biết|tiếp cận)).{0,160}"
                                          r"(yếu tố dự báo|biến dự báo|kết quả|kết cục)|(không|chưa) (thể )?làm mù"),)),
    "9a": (("du_bao", "bien_so", "phan_tich", "sai_so"), "bat_buoc",
           "Nêu cách chọn yếu tố dự báo ban đầu và mọi bước chọn trước khi dựng mô hình.",
           (_y("căn cứ chọn yếu tố dự báo", r"(chọn|lựa chọn|định trước)[^.;\n]{0,60}(theo|dựa (trên|vào)) (y văn|tổng "
                                            r"quan|mô hình (trước|đã có)|kiến thức|chuyên gia)"),),
           PHAT_TRIEN_MH, "có xây dựng mô hình"),
    "9b": (("du_bao", "bien_so", "bang_bien"), "bat_buoc", "Định nghĩa mọi yếu tố dự báo, cách và thời điểm đo.",
           (_y("yếu tố dự báo", r"yếu tố dự báo|biến dự báo|biến (độc lập|đầu vào)"),
            _y("cách đo/nguồn", r"Nguồn thu thập|đo (bằng|theo)|xét nghiệm|siêu âm|hồ sơ"),
            _y("thời điểm đo", r"(đo|ghi nhận|thu thập|lấy)[^.;\n]{0,80}(tại|lúc|ở|trong) (lần )?(khám tuyển|lúc tuyển|"
                               r"thời điểm (tuyển|ban đầu|vào)|ban đầu|nhập viện)|tại thời điểm (tuyển|ban đầu)"))),
    "9c": (("bien_so", "quy_trinh"), "bat_buoc", "Yếu tố dự báo cần đánh giá chủ quan: nêu trình độ người đánh giá.",
           (_y("trình độ người đánh giá", r"(bác sĩ|chuyên gia|người đánh giá).{0,80}(chuyên khoa|kinh nghiệm|trình "
                                          r"độ)"),),
           r"đọc (phim|hình ảnh)|đánh giá (chủ quan|lâm sàng) (yếu tố|biến)", "yếu tố dự báo cần đánh giá chủ quan"),
    "10": (("co_mau",), "bat_buoc", "Giải thích cách xác định cỡ mẫu (riêng phát triển và đánh giá), chứng minh đủ.",
           (_y("phương pháp cỡ mẫu cho mô hình", r"Riley|\bEPV\b|biến cố (trên|mỗi) (biến|tham số)|pmsampsize|cỡ mẫu "
                                                r"(tối thiểu|cho)|số biến cố"),
            _y("cỡ mẫu cuối cùng", CO_MAU_CUOI))),
    "11": (("phan_tich", "quan_ly_dl"), "bat_buoc", "Mô tả cách xử lý dữ liệu thiếu.",
           (_y("dữ liệu thiếu", DU_LIEU_THIEU), _y("phương pháp xử lý", XU_LY_THIEU)), None, "", True),
    "12a": (("phan_tich",), "bat_buoc", "Mô tả cách dùng dữ liệu (chia tập, bootstrap, kiểm định chéo).",
            (_y("cách dùng dữ liệu", r"(chia|tách) (dữ liệu|tập)|bootstrap|kiểm định chéo|cross-validation|tập (huấn "
                                     r"luyện|phát triển|kiểm định)|kiểm định (nội|ngoại)"),), PHAT_TRIEN_MH,
            "có xây dựng mô hình"),
    "12b": (("phan_tich", "bien_so", "bang_bien"), "bat_buoc",
            "Mô tả cách xử lý yếu tố dự báo trong phân tích (dạng hàm, biến đổi, chuẩn hoá).",
            (_y("dạng hàm/biến đổi", r"dạng (hàm|tuyến tính)|spline|phi tuyến|biến đổi|chuẩn hoá|giữ (nguyên )?(dạng "
                                     r")?liên "
                                     r"tục|phân nhóm|tuyến tính"),), PHAT_TRIEN_MH, "có xây dựng mô hình"),
    "12c": (("phan_tich",), "bat_buoc",
            "Nêu loại mô hình, lý do, các bước dựng mô hình (chọn biến, tinh chỉnh) và phương pháp kiểm định nội.",
            (_y("loại mô hình", r"hồi quy (logistic|Cox|tuyến tính)|LASSO|rừng ngẫu nhiên|học máy|XGBoost"),
             _y("bước dựng/co rút", r"(chọn|lựa chọn) biến|loại (dần|ngược)|co rút|shrinkage|penali|siêu tham số|LASSO|"
                                    r"định trước"),
             _y("kiểm định nội", r"kiểm định nội|bootstrap|kiểm định chéo|cross-validation")), PHAT_TRIEN_MH,
            "có xây dựng mô hình"),
    "12d": (("phan_tich",), "bat_buoc", "Nêu cách đánh giá không đồng nhất của tham số/hiệu năng giữa các cụm (cơ sở).",
            (_y("không đồng nhất giữa cụm", r"không đồng nhất|khác biệt giữa (các )?(cơ sở|trung tâm|bệnh viện)|hiệu "
                                            r"ứng "
                                           r"ngẫu nhiên|internal-external|theo (từng )?(cơ sở|trung tâm)"),),
            r"đa trung tâm|nhiều (cơ sở|bệnh viện|trung tâm)", "dữ liệu nhiều cơ sở"),
    "12e": (("phan_tich",), "bat_buoc",
            "Nêu thước đo và biểu đồ đánh giá hiệu năng: phân biệt, hiệu chuẩn, lợi ích lâm sàng.",
            (_y("phân biệt", r"phân biệt|\bAUC\b|C-statistic|chỉ số C|\bAUROC\b"),
             _y("hiệu chuẩn", r"hiệu chuẩn|calibration|độ dốc hiệu chuẩn"),
             _y("lợi ích lâm sàng", r"lợi ích (lâm sàng|ròng)|đường cong quyết định|decision curve|net benefit|"
                                    r"\bDCA\b"))),
    "12f": (("phan_tich",), "bat_buoc", "Mô tả việc cập nhật mô hình (vd hiệu chuẩn lại) sau đánh giá.",
            (_y("cập nhật mô hình", r"cập nhật mô hình|hiệu chuẩn lại|recalibrat|không cập nhật"),), DANH_GIA_MH_CO_SAN,
            "đánh giá mô hình có sẵn"),
    "12g": (("phan_tich",), "bat_buoc", "Mô tả cách tính dự báo của mô hình khi đánh giá (công thức, mã).",
            (_y("cách tính dự báo", r"công thức|phương trình|hệ số (đã công bố|gốc)|mã (nguồn|"
                                    r"lệnh)"),), DANH_GIA_MH_CO_SAN,
            "đánh giá mô hình có sẵn"),
    "13": (("phan_tich",), "bat_buoc", "Dùng phương pháp xử lý mất cân bằng lớp: nêu lý do, cách và cách hiệu chuẩn "
                                       "lại.",
           (_y("lý do/cách xử lý mất cân bằng", r"mất cân bằng|SMOTE|lấy mẫu (lại|thừa|thiếu)"),),
           r"mất cân bằng (lớp|kết cục)|SMOTE|oversampl|undersampl", "có xử lý mất cân bằng lớp"),
    "14": (("phan_tich", "sai_so"), "bat_buoc", "Mô tả cách tiếp cận tính công bằng của mô hình và lý do.",
           (_y("công bằng của mô hình", r"công bằng|fairness|hiệu năng (theo|giữa|trong) (các )?(nhóm|giới|tuổi)|"
                                        r"(nhóm|giới|tuổi).{0,60}(hiệu năng|hiệu chuẩn|AUC)"),)),
    "15": (("phan_tich", "bien_so"), "bat_buoc", "Nêu đầu ra của mô hình (xác suất, phân loại) và lý do chọn ngưỡng.",
           (_y("đầu ra", r"xác suất|nguy cơ (dự báo|tuyệt đối)|phân loại|nhóm nguy cơ"),
            _y("ngưỡng và lý do", r"ngưỡng.{0,160}(lý do|vì|nhằm|được chọn|dựa)|(lý do|vì|nhằm|dựa).{0,120}ngưỡng|"
                                  r"không "
                                  r"(đặt|chọn) ngưỡng")), PHAT_TRIEN_MH, "có xây dựng mô hình"),
    "16": (("phan_tich", "doi_tuong"), "bat_buoc",
           "Nêu khác biệt giữa dữ liệu phát triển và đánh giá (bối cảnh, tiêu chuẩn, kết cục, yếu tố dự báo).",
           (_y("so sánh tập phát triển–đánh giá", r"khác biệt|so sánh (đặc điểm|phân bố)|tương đồng"),),
           r"kiểm định (ngoại|bên ngoài)|tập (kiểm định|đánh giá) (độc lập|bên ngoài)", "có dữ liệu đánh giá riêng"),
    "17": (("dao_duc",), "bat_buoc", "Nêu Hội đồng Đạo đức chấp thuận và cách lấy (hoặc miễn) đồng thuận.",
           (_y("Hội đồng Đạo đức", HOI_DONG), _y("đồng thuận/miễn", r"đồng (ý|thuận)|miễn"))),
    "18a": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu nguồn kinh phí và vai trò nhà tài trợ.",
            (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
    "18b": (("dao_duc", "bia", "kinh_phi"), "bat_buoc", "Khai xung đột lợi ích.", (_y("xung đột lợi ích", XUNG_DOT),)),
    "18c": (("pho_bien", "quan_ly_dl"), "bat_buoc", "Nêu nơi truy cập đề cương.", (_y("truy cập đề "
                                                                                      "cương", DE_CUONG_TRUY_CAP),)),
    "18d": (("pho_bien", "dao_duc", "bia"), "bat_buoc", "Nêu thông tin đăng ký (cơ quan, số) hoặc nêu không đăng ký.",
            (_y("đăng ký", DANG_KY + r"|không đăng ký"),)),
    "18e": (("pho_bien", "quan_ly_dl"), "bat_buoc", "Nêu khả năng chia sẻ dữ liệu nghiên cứu.",
            (_y("chia sẻ dữ liệu", CHIA_SE_DU_LIEU),)),
    "18f": (("pho_bien", "quan_ly_dl", "phan_tich"), "bat_buoc", "Nêu khả năng chia sẻ mã phân tích.",
            (_y("chia sẻ mã", CHIA_SE_MA),)),
    "19": (("dao_duc", "quy_trinh", "thiet_ke", "pho_bien"), "bat_buoc",
           "Nêu sự tham gia của người bệnh/công chúng (hoặc nêu không có).", (_y("sự tham gia của người bệnh", PPI),)),
    "20a": (("du_kien_kq", "quy_trinh", "chon_mau"), "ke_hoach", "Lên kế hoạch sơ đồ luồng người tham gia, số có/không "
                                                                 "kết cục.",
            (_y("sơ đồ luồng", SO_DO),)),
    "20b": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch mô tả đặc điểm chung, theo từng nguồn dữ liệu.",
            (_y("bảng đặc điểm", r"Đặc điểm (chung|đối tượng|nền|người tham gia)", de_muc=True),)),
    "20c": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch so sánh phân bố yếu tố dự báo giữa tập đánh giá và "
                                                     "phát triển.",
            (_y("so sánh phân bố", r"so sánh (phân bố|đặc điểm)"),), DANH_GIA_MH_CO_SAN, "đánh giá mô hình có sẵn"),
    "21": (("du_kien_kq", "phan_tich", "co_mau"), "ke_hoach", "Lên kế hoạch báo cáo số người và số biến cố của từng "
                                                              "phân tích.",
           (_y("số biến cố", r"số (biến cố|sự kiện)|số (người|đối tượng).{0,60}(biến cố|kết cục)|biến cố \(n\s*="),)),
    "22": (("du_kien_kq", "pho_bien", "phan_tich"), "ke_hoach", "Lên kế hoạch công bố đầy đủ mô hình (công thức, mã).",
           (_y("công bố mô hình", r"(công bố|trình bày|báo cáo) (đầy đủ )?(mô hình|công thức|hệ số|phương trình)|hệ số "
                                  r"(hồi quy|chặn)|phương trình"),), PHAT_TRIEN_MH, "có xây dựng mô hình"),
    "23a": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch báo cáo hiệu năng kèm khoảng tin cậy, cả theo nhóm "
                                                     "then chốt.",
            (_y("khoảng tin cậy", r"KTC|khoảng tin cậy|\bCI\b"),
             _y("theo nhóm then chốt", r"(theo|trong) (các )?(nhóm|phân nhóm|giới|tuổi)|phân nhóm|nhóm nhỏ"))),
    "23b": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch báo cáo không đồng nhất hiệu năng giữa các cụm.",
            (_y("không đồng nhất giữa cụm", r"không đồng nhất|giữa (các )?(cơ sở|trung tâm)"),),
            r"đa trung tâm|nhiều (cơ sở|bệnh viện|trung tâm)", "dữ liệu nhiều cơ sở"),
    "24": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch báo cáo kết quả cập nhật mô hình.",
           (_y("kết quả cập nhật", r"cập nhật|hiệu chuẩn lại"),), DANH_GIA_MH_CO_SAN, "đánh giá mô hình có sẵn"),
    "25": (("ban_luan", "du_kien_kq"), "ke_hoach", "Lên kế hoạch diễn giải kết quả chính, kể cả tính công bằng.",
           (_y("diễn giải", r"diễn giải|bàn luận|ý nghĩa"),)),
    "26": (("han_che",), "ke_hoach", "Bàn hạn chế (mẫu không đại diện, cỡ mẫu, quá khớp, thiếu dữ liệu).",
           (_y("hạn chế", r"hạn chế", de_muc=True),
            _y("hạn chế đặc thù mô hình", r"quá khớp|overfitting|không đại diện|cỡ mẫu|kiểm định (ngoại|ngoài|bên "
                                          r"ngoài)|"
                                         r"một (cơ sở|trung tâm)"))),
    "27a": (("ban_luan", "han_che", "du_kien_kq", "phan_tich"), "ke_hoach",
            "Nêu cách xử lý dữ liệu đầu vào kém chất lượng/không có khi áp dụng mô hình.",
            (_y("dữ liệu đầu vào khi áp dụng", r"(thiếu|không có) (giá trị|dữ liệu)( đầu vào)?.{0,80}(áp dụng|sử dụng) "
                                               r"mô "
                                               r"hình|khi (áp dụng|sử dụng) mô hình"),), PHAT_TRIEN_MH, "có xây dựng "
                                                                                                        "mô hình"),
    "27b": (("ban_luan", "han_che", "du_kien_kq"), "ke_hoach",
            "Nêu người dùng có cần thao tác với dữ liệu đầu vào và trình độ cần có.",
            (_y("tương tác của người dùng", r"người (dùng|sử dụng).{0,100}(nhập|thao tác|kỹ năng|chuyên môn|trình "
                                            r"độ)"),),
            PHAT_TRIEN_MH, "có xây dựng mô hình"),
    "27c": (("ban_luan", "han_che", "du_kien_kq"), "ke_hoach", "Nêu bước nghiên cứu tiếp theo về khả năng áp dụng, suy "
                                                               "rộng.",
            (_y("nghiên cứu tiếp theo", r"nghiên cứu (tiếp theo|trong tương lai|tiếp)|kiểm định (ngoại|bên ngoài)|"
                                        r"hướng "
                                        r"(nghiên cứu )?tiếp"),)),
}

# ═════════════════════════════════════ COREQ 2007 (qualitative — chỉ cảnh báo) ═════════════════════════════════════
_COREQ_CHU_DE = {
    "1": "Interviewer/facilitator", "2": "Credentials", "3": "Occupation", "4": "Gender",
    "5": "Experience and training", "6": "Relationship established", "7": "Participant knowledge of the interviewer",
    "8": "Interviewer characteristics", "9": "Methodological orientation and theory", "10": "Sampling",
    "11": "Method of approach", "12": "Sample size", "13": "Non-participation", "14": "Setting of data collection",
    "15": "Presence of non-participants", "16": "Description of sample", "17": "Interview guide",
    "18": "Repeat interviews", "19": "Audio/visual recording", "20": "Field notes", "21": "Duration",
    "22": "Data saturation", "23": "Transcripts returned", "24": "Number of data coders",
    "25": "Description of the coding tree", "26": "Derivation of themes", "27": "Software", "28": "Participant "
                                                                                                  "checking",
    "29": "Quotations presented", "30": "Data and findings consistent", "31": "Clarity of major themes",
    "32": "Clarity of minor themes",
}
NGUOI_PHONG_VAN = (r"(chủ nhiệm|nghiên cứu viên|tác giả|điều dưỡng|bác sĩ|thành viên)[^.;\n]{0,60}(trực tiếp )?(phỏng "
                   r"vấn|"
                   r"điều phối)|(phỏng vấn|điều phối) (do|bởi) ")
_COREQ: Dict[str, tuple] = {
    "1": (("nhom_nc", "tiep_can", "quy_trinh", "cong_cu", "nhan_luc", "sai_so"), "bat_buoc",
          "Nêu ai trực tiếp phỏng vấn/điều phối nhóm.", (_y("người phỏng vấn", NGUOI_PHONG_VAN),)),
    "2": (("nhom_nc", "nhan_luc", "bia"), "bat_buoc", "Nêu bằng cấp/chức danh của người nghiên cứu.",
          (_y("bằng cấp/chức danh", r"\b(BS|ThS|TS|CKI|CKII|PGS|GS)\b\.?|Bác sĩ|Thạc sĩ|Tiến sĩ|chuyên khoa|cử nhân|"
                                    r"điều dưỡng"),)),
    "3": (("nhom_nc", "nhan_luc", "sai_so", "bia"), "bat_buoc", "Nêu công việc của người phỏng vấn khi làm nghiên cứu.",
          (_y("công việc người phỏng vấn", r"(người phỏng vấn|điều tra viên|nghiên cứu viên).{0,120}(là|không phải) "
                                           r"(bác sĩ|điều dưỡng|nhân viên|cán bộ)"),)),
    "4": (("nhom_nc", "nhan_luc"), "ke_hoach", "Lên kế hoạch nêu giới của người phỏng vấn.",
          (_y("giới người phỏng vấn", r"(người phỏng vấn|điều tra viên).{0,80}(nam|nữ|giới)"),)),
    "5": (("nhom_nc", "nhan_luc", "quy_trinh", "sai_so"), "bat_buoc", "Nêu kinh nghiệm và đào tạo của người phỏng vấn.",
          (_y("kinh nghiệm/đào tạo", r"kinh nghiệm|được (đào tạo|tập huấn)|tập huấn"),)),
    "6": (("nhom_nc", "sai_so", "dao_duc"), "bat_buoc", "Nêu quan hệ có trước giữa người phỏng vấn và người tham gia.",
          (_y("quan hệ có trước", r"quan hệ|không phải bác sĩ điều trị|không (trực tiếp )?điều trị|không quen biết"),)),
    "7": (("nhom_nc", "dao_duc", "quy_trinh", "phieu"), "bat_buoc",
          "Nêu người tham gia được biết gì về người phỏng vấn và mục đích nghiên cứu.",
          (_y("người tham gia biết về người phỏng vấn/mục đích", r"giới thiệu (người phỏng vấn|bản thân|nhóm nghiên "
                                                                 r"cứu)"
                                                                 r"|được (giải thích|thông báo).{0,120}mục đích"),)),
    "8": (("nhom_nc", "sai_so"), "bat_buoc", "Nêu đặc điểm/thiên kiến/giả định của người phỏng vấn và cách phản tư.",
          (_y("phản tư/thiên kiến", r"phản tư|thiên kiến|giả định|định kiến|ảnh hưởng của người phỏng vấn"),)),
    "9": (("thiet_ke", "tiep_can"), "bat_buoc", "Nêu định hướng phương pháp luận và lý thuyết nền.",
          (_y("định hướng phương pháp luận", r"hiện tượng học|lý thuyết (nền|cơ sở)|grounded|phân tích (chủ đề|nội "
                                             r"dung)|"
                                             r"dân tộc học|nghiên cứu trường hợp|thematic"),)),
    "10": (("chon_mau",), "bat_buoc", "Mô tả cách chọn người tham gia.",
           (_y("cách chọn mẫu", r"có chủ đích|chủ định|quả bóng tuyết|thuận tiện|lý thuyết|đa dạng"),)),
    "11": (("chon_mau", "quy_trinh", "tiep_can"), "bat_buoc", "Mô tả cách tiếp cận người tham gia (trực tiếp, điện "
                                                              "thoại…).",
           (_y("cách tiếp cận người tham gia", r"(mời|tiếp cận|liên hệ).{0,80}(trực tiếp|điện thoại|thư|qua|tại)|"
                                               r"giới thiệu (bởi|qua)"),)),
    "12": (("co_mau",), "bat_buoc", "Nêu số người tham gia dự kiến.", (_y("số người tham gia", CO_MAU_CUOI),)),
    "13": (("du_kien_kq", "quy_trinh", "chon_mau"), "ke_hoach", "Lên kế hoạch ghi số người từ chối/rút lui và lý do.",
           (_y("từ chối/rút lui và lý do", r"(từ chối|rút lui|không tham gia).{0,80}lý do|lý do (từ chối|rút lui)"),)),
    "14": (("dia_diem", "tiep_can", "quy_trinh"), "bat_buoc", "Nêu nơi thu thập dữ liệu.",
           (_y("nơi phỏng vấn", r"(phòng|tại|nơi) (riêng|yên tĩnh|khám|nhà)|tại (phòng khám|khoa|nhà|bệnh "
                                r"viện)|" + NOI),)),
    "15": (("tiep_can", "quy_trinh", "dao_duc"), "bat_buoc", "Nêu có người khác có mặt khi thu thập dữ liệu không.",
           (_y("người khác có mặt", r"(có|không có) (người )?(khác|thân|người nhà) (có mặt|tham dự)|riêng (tư|biệt)|"
                                    r"chỉ có "
                                    r"người (phỏng vấn|tham gia)"),)),
    "16": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch mô tả đặc điểm mẫu.",
           (_y("đặc điểm mẫu", r"Đặc điểm (người tham gia|chung|đối tượng)", de_muc=True),)),
    "17": (("cong_cu", "phieu", "tiep_can"), "bat_buoc", "Cung cấp bộ hướng dẫn phỏng vấn và nêu đã thử trước chưa.",
           (_y("bộ hướng dẫn phỏng vấn", r"hướng dẫn phỏng vấn|bộ câu hỏi (phỏng vấn|hướng dẫn)|câu hỏi gợi mở"),
            _y("thử trước", r"thử (nghiệm|bộ câu hỏi|trước)|pilot|chạy thử"))),
    "18": (("tiep_can", "cong_cu", "quy_trinh"), "bat_buoc", "Nêu có phỏng vấn lặp lại không, bao nhiêu lần.",
           (_y("phỏng vấn lặp lại", r"phỏng vấn (lại|lặp|lần (hai|2))|một (cuộc|lần) phỏng vấn|không phỏng vấn lại"),)),
    "19": (("tiep_can", "cong_cu", "quy_trinh"), "bat_buoc", "Nêu có ghi âm/ghi hình không.",
           (_y("ghi âm/ghi hình", r"ghi (âm|hình)"),)),
    "20": (("tiep_can", "cong_cu", "quy_trinh"), "bat_buoc", "Nêu có ghi chép thực địa không.",
           (_y("ghi chép thực địa", r"ghi chép (thực địa|hiện trường)|nhật ký (thực địa|phỏng vấn)|field note"),)),
    "21": (("tiep_can", "cong_cu", "quy_trinh"), "bat_buoc", "Nêu thời lượng phỏng vấn/thảo luận.",
           (_y("thời lượng", r"\d+\s*[–-]?\s*\d*\s*phút|thời lượng"),)),
    "22": (("co_mau", "tiep_can", "phan_tich"), "bat_buoc", "Nêu tiêu chí bão hoà dữ liệu.",
           (_y("bão hoà dữ liệu", r"bão ho[àa]"),)),
    "23": (("tiep_can", "phan_tich", "dao_duc", "sai_so"), "bat_buoc", "Nêu có gửi lại bản gỡ băng cho người tham gia "
                                                                       "không.",
           (_y("gửi lại bản gỡ băng", r"(gửi|trả) lại (bản|nội dung) (gỡ băng|ghi chép)|người tham gia (xem|đọc) lại "
                                      r"bản|"
                                     r"không gửi lại"),)),
    "24": (("phan_tich",), "bat_buoc", "Nêu số người mã hoá dữ liệu.",
           (_y("số người mã hoá", r"(\d+|hai|ba|một) người mã ho[áa]|mã ho[áa] (độc lập|song song)"),)),
    "25": (("phan_tich",), "bat_buoc", "Nêu có mô tả cây mã hoá/bộ mã không.",
           (_y("cây mã/bộ mã", r"cây mã|bộ mã|codebook|khung mã"),)),
    "26": (("phan_tich", "tiep_can"), "bat_buoc", "Nêu chủ đề xác định trước hay rút ra từ dữ liệu.",
           (_y("cách hình thành chủ đề", r"rút ra từ dữ liệu|quy nạp|diễn dịch|xác định trước|mở mã|inductive|"
                                         r"deductive"),)),
    "27": (("phan_tich", "quan_ly_dl"), "bat_buoc", "Nêu phần mềm quản lý dữ liệu (nếu có).",
           (_y("phần mềm", r"phần mềm|NVivo|ATLAS|MAXQDA|bảng tính|không dùng phần mềm"),)),
    "28": (("phan_tich", "sai_so", "tiep_can"), "bat_buoc", "Nêu người tham gia có phản hồi kết quả phân tích không.",
           (_y("kiểm tra với người tham gia", r"kiểm tra lại với người tham gia|member check|người tham gia (phản hồi|"
                                              r"góp ý)"),)),
    "29": (("phan_tich", "du_kien_kq"), "ke_hoach", "Lên kế hoạch trích lời người tham gia minh hoạ chủ đề, có định "
                                                    "danh mã.",
           (_y("trích dẫn minh hoạ", r"trích (dẫn|lời)"),)),
    "30": ((), "bao_cao", "Dữ liệu trình bày nhất quán với phát hiện.", ()),
    "31": ((), "bao_cao", "Chủ đề chính trình bày rõ.", ()),
    "32": ((), "bao_cao", "Mô tả trường hợp khác biệt/chủ đề phụ.", ()),
}

# ═════════════════════════════════════ SRQR 2014 (qualitative — chỉ cảnh báo) ═════════════════════════════════════
_SRQR_CHU_DE = {
    "S1": "Title", "S2": "Abstract", "S3": "Problem formulation", "S4": "Purpose or research question",
    "S5": "Qualitative approach and research paradigm", "S6": "Researcher characteristics and reflexivity",
    "S7": "Context", "S8": "Sampling strategy", "S9": "Ethical issues pertaining to human subjects",
    "S10": "Data collection methods", "S11": "Data collection instruments and technologies", "S12": "Units of study",
    "S13": "Data processing", "S14": "Data analysis", "S15": "Techniques to enhance trustworthiness",
    "S16": "Synthesis and interpretation", "S17": "Links to empirical data",
    "S18": "Integration with prior work, implications, transferability, and contribution(s) to the field",
    "S19": "Limitations", "S20": "Conflicts of interest", "S21": "Funding",
}
_SRQR: Dict[str, tuple] = {
    "S1": ((), "bao_cao", "Tiêu đề nêu bản chất, chủ đề; nên nêu là nghiên cứu định tính.", ()),
    "S2": ((), "bao_cao", "Tóm tắt theo khuôn của tạp chí.", ()),
    "S3": (("dat_van_de", "tong_quan"), "bat_buoc", "Mô tả vấn đề và tầm quan trọng, kèm lý thuyết/nghiên cứu liên "
                                                    "quan.",
           (_y("trích dẫn nguồn", TRICH_DAN), _y("tầm quan trọng/khoảng trống", r"khoảng trống|chưa (có|thấy|được)|"
                                                                             r"cần (thiết|có)|quan trọng"))),
    "S4": (("muc_tieu", "cau_hoi"), "bat_buoc", "Nêu mục đích và câu hỏi nghiên cứu cụ thể.",
           (_y("mục tiêu/câu hỏi", MUC_TIEU_CU_THE + r"|câu hỏi nghiên cứu"),)),
    "S5": (("thiet_ke", "tiep_can"), "bat_buoc", "Nêu cách tiếp cận định tính, hệ hình nghiên cứu và lý do chọn.",
           (_y("cách tiếp cận", r"hiện tượng học|lý thuyết (nền|cơ sở)|grounded|phân tích (chủ đề|nội dung)|dân tộc "
                                r"học|"
                                r"nghiên cứu trường hợp|thematic"),
            _y("hệ hình/lý do", r"hệ hình|kiến tạo|diễn giải|hậu thực chứng|lý do|phù hợp (với|để)|nhằm"))),
    "S6": (("nhom_nc", "sai_so", "nhan_luc"), "bat_buoc",
           "Mô tả đặc điểm người nghiên cứu có thể ảnh hưởng (trình độ, quan hệ, giả định) và cách xử lý (phản tư).",
           (_y("phản tư/quan hệ", r"phản tư|quan hệ|giả định|không phải bác sĩ điều trị|ảnh hưởng của người phỏng "
                                  r"vấn"),)),
    "S7": (("dia_diem", "tiep_can"), "bat_buoc", "Mô tả bối cảnh/địa điểm và yếu tố bối cảnh nổi bật.",
           (_y("bối cảnh", NOI),)),
    "S8": (("chon_mau", "co_mau"), "bat_buoc", "Giải thích cách, lý do chọn người tham gia và tiêu chí dừng chọn mẫu.",
           (_y("cách chọn mẫu", r"có chủ đích|chủ định|quả bóng tuyết|lý thuyết|đa dạng"),
            _y("tiêu chí dừng", r"bão ho[àa]|dừng"))),
    "S9": (("dao_duc",), "bat_buoc", "Ghi chấp thuận đạo đức, đồng thuận và vấn đề bảo mật.",
           (_y("Hội đồng Đạo đức", HOI_DONG), _y("đồng thuận", DONG_Y), _y("bảo mật", BAO_MAT))),
    "S10": (("tiep_can", "quy_trinh", "cong_cu"), "bat_buoc",
            "Mô tả loại dữ liệu, quy trình thu thập (mốc thời gian, tính lặp, phối hợp nguồn) và lý do.",
            (_y("phương pháp thu thập", r"phỏng vấn|thảo luận nhóm|quan sát|nhóm tiêu điểm"),
             _y("mốc/trình tự", NGAY + r"|song song|lặp|đồng thời"))),
    "S11": (("cong_cu", "tiep_can", "phieu"), "bat_buoc", "Mô tả công cụ (hướng dẫn phỏng vấn) và thiết bị (máy ghi "
                                                          "âm).",
            (_y("hướng dẫn phỏng vấn", r"hướng dẫn phỏng vấn|bộ câu hỏi"), _y("thiết bị ghi", r"ghi (âm|hình)|máy "
                                                                                              r"ghi"))),
    "S12": (("co_mau", "du_kien_kq", "doi_tuong"), "bat_buoc", "Nêu số và đặc điểm người tham gia (có thể ở Kết quả).",
            (_y("số người tham gia", CO_MAU_CUOI),)),
    "S13": (("phan_tich", "quan_ly_dl", "tiep_can"), "bat_buoc",
            "Mô tả xử lý dữ liệu: gỡ băng, nhập liệu, quản lý–bảo mật, kiểm toàn vẹn, khử định danh trích đoạn.",
            (_y("gỡ băng", r"gỡ băng|phiên âm|chép lời"), _y("bảo mật/khử định danh", BAO_MAT))),
    "S14": (("phan_tich",), "bat_buoc", "Mô tả quá trình phân tích, ai tham gia, gắn với cách tiếp cận.",
            (_y("quá trình phân tích", r"mã ho[áa]|phân tích chủ đề|chủ đề"), _y("người phân tích", r"(\d+|hai|ba) "
                                                                                                    r"người|"
                                                                              r"độc lập|người thứ ba"))),
    "S15": (("phan_tich", "sai_so"), "bat_buoc", "Nêu kỹ thuật tăng độ tin cậy (kiểm với người tham gia, vết kiểm "
                                                 "toán…).",
            (_y("kỹ thuật tăng độ tin cậy", r"member check|kiểm tra lại với người tham gia|audit trail|vết kiểm toán|"
                                            r"nhật ký|phối hợp (nguồn|dữ liệu)|triangulation|credibility|"
                                            r"độ tin cậy của kết quả"),)),
    "S16": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch trình bày phát hiện chính (chủ đề, mô hình).",
            (_y("phát hiện chính", r"chủ đề"),)),
    "S17": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch dẫn chứng (trích lời, ghi chép) cho phát hiện.",
            (_y("dẫn chứng", r"trích (dẫn|lời)|ghi chép"),)),
    "S18": (("phan_tich", "ban_luan", "han_che"), "ke_hoach",
            "Lên kế hoạch liên hệ phát hiện với nghiên cứu trước, phạm vi chuyển giao và đóng góp.",
            (_y("chuyển giao/đóng góp", r"chuyển giao|transferab|đóng góp|so sánh với (nghiên cứu|y văn)|mô tả dày"),)),
    "S19": (("han_che",), "ke_hoach", "Bàn độ tin cậy và hạn chế của phát hiện.",
            (_y("hạn chế", r"hạn chế", de_muc=True),)),
    "S20": (("dao_duc", "bia", "kinh_phi"), "bat_buoc", "Nêu nguồn ảnh hưởng tiềm tàng và cách quản lý (xung đột lợi "
                                                        "ích).",
            (_y("xung đột lợi ích", XUNG_DOT),)),
    "S21": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu nguồn kinh phí và vai trò nhà tài trợ.",
            (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
}

# ═══════════════════════════════ GRAMMS 2008 (mixed_methods hoặc có cấu phần hỗn hợp) ═══════════════════════════════
_GRAMMS_CHU_DE = {"1": "Justification for mixed methods", "2": "Design: purpose, priority, sequence",
                  "3": "Each method: sampling, data collection, analysis", "4": "Integration: where, how, who",
                  "5": "Limitations of one method associated with the presence of the other",
                  "6": "Insights gained from mixing or integrating methods"}
_GRAMMS: Dict[str, tuple] = {
    "1": (("thiet_ke", "tong_quan", "tiep_can"), "bat_buoc", "Giải thích vì sao dùng phương pháp hỗn hợp.",
          (_y("lý do dùng hỗn hợp", r"(hỗn hợp|định tính).{0,200}(nhằm|để|vì|giải thích|bổ sung|hiểu)"),)),
    "2": (("thiet_ke", "tiep_can"), "bat_buoc", "Mô tả thiết kế: mục đích, mức ưu tiên và trình tự các phương pháp.",
          (_y("trình tự", r"song song|tuần tự|đồng thời|sau (khi|đó)|hội tụ|giải thích tuần tự|khám phá tuần tự|lồng "
                          r"ghép"),
           _y("mức ưu tiên/mục đích", r"ưu tiên|chính|phụ|bổ sung|giải thích|lồng"))),
    "3": (("chon_mau", "tiep_can", "phan_tich", "cong_cu"), "bat_buoc",
          "Mô tả từng phương pháp (định lượng, định tính): chọn mẫu, thu thập, phân tích.",
          (_y("cấu phần định tính", DINH_TINH_CP), _y("cấu phần định lượng", DINH_LUONG_CP))),
    "4": (("phan_tich", "tiep_can", "thiet_ke"), "bat_buoc", "Nêu tích hợp diễn ra ở đâu, bằng cách nào, ai thực hiện.",
          (_y("tích hợp", r"tích hợp|kết hợp (kết quả|dữ liệu)|đối chiếu (kết quả|hai)|ma trận (kết hợp|tích hợp)|"
                          r"joint display"),)),
    "5": (("han_che",), "ke_hoach", "Nêu hạn chế của một phương pháp phát sinh do có mặt phương pháp kia.",
          (_y("hạn chế do kết hợp", r"hạn chế.{0,200}(định tính|định lượng|kết hợp|hỗn hợp)"),)),
    "6": (("ban_luan", "du_kien_kq", "han_che"), "ke_hoach", "Nêu hiểu biết thu được nhờ kết hợp phương pháp.",
          (_y("hiểu biết từ kết hợp", r"(kết hợp|tích hợp|hỗn hợp).{0,160}(giúp|làm rõ|giải thích|bổ sung|hiểu)"),)),
}

# ═════════════════════════════════════ SQUIRE 2.0 (quality_improvement) ═════════════════════════════════════
_SQUIRE: Dict[str, tuple] = {
    "1": ((), "bao_cao", "Tiêu đề nêu đây là sáng kiến cải tiến chăm sóc.", ()),
    "2a": ((), "bao_cao", "Tóm tắt đủ để tra cứu và lập chỉ mục.", ()),
    "2b": ((), "bao_cao", "Tóm tắt toàn bộ thông tin then chốt.", ()),
    "3": (("dat_van_de",), "bat_buoc", "Mô tả bản chất và tầm quan trọng của vấn đề tại chỗ.",
          (_y("vấn đề tại chỗ", r"tại (đơn vị|khoa|bệnh viện|phòng khám)|của đơn vị|tại cơ sở"),)),
    "4": (("dat_van_de", "tong_quan"), "bat_buoc", "Tóm tắt hiểu biết hiện có, nghiên cứu trước liên quan.",
          (_y("trích dẫn nguồn", TRICH_DAN),)),
    "5": (("tong_quan", "dat_van_de"), "bat_buoc", "Nêu khung/mô hình/lý thuyết giải thích vấn đề và lý do can thiệp "
                                                   "có hiệu quả.",
          (_y("khung lý thuyết", r"khung (lý thuyết|khái niệm)|mô hình (PDSA|logic|cải tiến)|lý thuyết|PDSA"),)),
    "6": (("muc_tieu",), "bat_buoc", "Nêu mục đích của dự án.", (_y("mục tiêu cụ thể", MUC_TIEU_CU_THE),)),
    "7": (("dia_diem", "thiet_ke"), "bat_buoc", "Nêu yếu tố bối cảnh quan trọng lúc bắt đầu can thiệp.",
          (_y("bối cảnh", NOI),)),
    "8a": (("can_thiep",), "bat_buoc", "Mô tả can thiệp đủ chi tiết để người khác lặp lại.",
           (_y("mô tả can thiệp", r"can thiệp|cải tiến|sáng kiến"),)),
    "8b": (("nhan_luc", "can_thiep"), "bat_buoc", "Nêu thành phần đội thực hiện.", (_y("đội thực hiện", r"nhóm|đội|"
                                                                                                        r"thành "
                                                                                                        r"viên"),)),
    "9a": (("thiet_ke", "phan_tich"), "bat_buoc", "Nêu cách đánh giá tác động của can thiệp.",
           (_y("cách đánh giá tác động", r"trước[\s–-]*sau|chuỗi thời gian|biểu đồ (kiểm soát|chạy)|run chart|SPC|so "
                                        r"sánh"),)),
    "9b": (("thiet_ke", "phan_tich", "sai_so"), "bat_buoc", "Nêu cách xác lập kết quả là do can thiệp.",
           (_y("quy kết do can thiệp", r"nhóm (chứng|so sánh)|chuỗi thời gian gián đoạn|xu hướng|nhiễu|hiệu chỉnh"),)),
    "10a": (("bien_so",), "bat_buoc", "Nêu thước đo quá trình và kết cục, lý do chọn, định nghĩa vận hành, độ tin cậy.",
            (_y("thước đo quá trình", r"(chỉ số|thước đo) quá trình"), _y("thước đo kết cục", r"(chỉ số|thước đo) kết "
                                                                                              r"cục|"
                                                                                       r"kết cục"))),
    "10b": (("bien_so", "quy_trinh"), "bat_buoc", "Nêu cách đánh giá liên tục các yếu tố bối cảnh.",
            (_y("đánh giá bối cảnh", r"(yếu tố )?bối cảnh"),)),
    "10c": (("quan_ly_dl", "cong_cu"), "bat_buoc", "Nêu cách đánh giá đầy đủ và chính xác của dữ liệu.",
            (_y("độ đầy đủ/chính xác dữ liệu", CHAT_LUONG_DL + r"|đầy đủ"),)),
    "11a": (("phan_tich",), "bat_buoc", "Nêu phương pháp định tính và định lượng để suy luận từ dữ liệu.",
            (_y("phương pháp phân tích", PP_THONG_KE + r"|biểu đồ (kiểm soát|chạy)"),)),
    "11b": (("phan_tich",), "bat_buoc", "Nêu phương pháp hiểu biến thiên trong dữ liệu, kể cả tác động của thời gian.",
            (_y("biến thiên theo thời gian", r"biến thiên|theo thời gian|xu hướng|biểu đồ (kiểm soát|chạy)|SPC"),)),
    "12": (("dao_duc",), "bat_buoc", "Nêu khía cạnh đạo đức và cách xử lý, kể cả xung đột lợi ích.",
           (_y("đạo đức", HOI_DONG + r"|đạo đức"), _y("xung đột lợi ích", XUNG_DOT))),
    "13a": (("du_kien_kq", "tien_do"), "ke_hoach", "Lên kế hoạch mô tả các bước can thiệp và diễn tiến theo thời gian.",
            (_y("diễn tiến theo thời gian", r"theo thời gian|mốc|giai đoạn|chu kỳ"),)),
    "13b": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch báo cáo chi tiết thước đo quá trình và kết cục.",
            (_y("thước đo quá trình/kết cục", r"quá trình|kết cục"),)),
    "13c": ((), "bao_cao", "Báo cáo yếu tố bối cảnh tương tác với can thiệp.", ()),
    "13d": ((), "bao_cao", "Báo cáo liên quan quan sát được giữa kết cục, can thiệp và bối cảnh.", ()),
    "13e": (("du_kien_kq", "giam_sat"), "ke_hoach", "Lên kế hoạch ghi nhận hệ quả ngoài ý muốn.",
            (_y("hệ quả ngoài ý muốn", r"ngoài ý muốn|không mong muốn|bất lợi"),)),
    "13f": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch báo cáo dữ liệu thiếu.",
            (_y("dữ liệu thiếu", DU_LIEU_THIEU),)),
    "14a": ((), "bao_cao", "Phát hiện chính.", ()), "14b": ((), "bao_cao", "Điểm mạnh của dự án.", ()),
    "15a": ((), "bao_cao", "Bản chất liên quan can thiệp–kết cục.", ()),
    "15b": (("ban_luan",), "ke_hoach", "Lên kế hoạch so sánh với y văn.", (_y("so sánh với y văn", r"so sánh|y văn|"
                                                                                                 r"nghiên cứu khác"),)),
    "15c": ((), "bao_cao", "Tác động lên con người và hệ thống.", ()),
    "15d": ((), "bao_cao", "Lý do khác biệt giữa kết quả quan sát và dự kiến.", ()),
    "15e": (("ban_luan", "kinh_phi"), "ke_hoach", "Lên kế hoạch bàn chi phí và đánh đổi.",
            (_y("chi phí", r"chi phí"),)),
    "16a": (("han_che",), "ke_hoach", "Bàn giới hạn suy rộng.", (_y("suy rộng", SUY_RONG),)),
    "16b": (("han_che", "sai_so"), "ke_hoach", "Bàn yếu tố giới hạn giá trị nội (nhiễu, sai lệch, thiếu chính xác).",
            (_y("giá trị nội", r"nhiễu|sai lệch|sai số|thiếu chính xác"),)),
    "16c": (("han_che", "sai_so"), "ke_hoach", "Nêu nỗ lực giảm thiểu và hiệu chỉnh hạn chế.",
            (_y("giảm thiểu hạn chế", r"khống chế|giảm thiểu|hiệu chỉnh|kiểm soát"),)),
    "17a": ((), "bao_cao", "Tính hữu ích.", ()),
    "17b": (("ban_luan", "du_kien_kq", "pho_bien"), "ke_hoach", "Lên kế hoạch bàn tính bền vững.",
            (_y("bền vững", r"bền vững|duy trì"),)),
    "17c": ((), "bao_cao", "Khả năng lan rộng sang bối cảnh khác.", ()),
    "17d": ((), "bao_cao", "Hàm ý cho thực hành và nghiên cứu.", ()),
    "17e": ((), "bao_cao", "Bước tiếp theo.", ()),
    "18": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu nguồn kinh phí và vai trò nhà tài trợ.",
           (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
}

# ═══════════════════════════════ CHEERS 2022 (economic hoặc có cấu phần kinh tế) ═══════════════════════════════
_CHEERS: Dict[str, tuple] = {
    "1": ((), "bao_cao", "Tiêu đề nêu đánh giá kinh tế và can thiệp so sánh.", ()),
    "2": ((), "bao_cao", "Tóm tắt có cấu trúc.", ()),
    "3": (("dat_van_de", "tong_quan", "muc_tieu"), "bat_buoc", "Nêu bối cảnh, câu hỏi và ý nghĩa cho quyết định chính "
                                                               "sách.",
          (_y("câu hỏi kinh tế", KINH_TE + r"|chi phí"),)),
    "4": (("kinh_te", "phan_tich", "pho_bien"), "bat_buoc", "Nêu có kế hoạch phân tích kinh tế y tế và nơi truy cập.",
          (_y("kế hoạch phân tích kinh tế", r"kế hoạch phân tích (kinh tế|chi phí)|\bHEAP\b|phân tích kinh tế"),)),
    "5": (("doi_tuong", "kinh_te"), "bat_buoc", "Mô tả đặc điểm quần thể nghiên cứu.",
          (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True),)),
    "6": (("dia_diem", "kinh_te"), "bat_buoc", "Nêu bối cảnh có thể ảnh hưởng kết quả.", (_y("bối cảnh", NOI),)),
    "7": (("can_thiep", "kinh_te"), "bat_buoc", "Mô tả can thiệp/chiến lược so sánh và lý do chọn.",
          (_y("can thiệp so sánh", r"so sánh|nhóm chứng|chiến lược"),)),
    "8": (("kinh_te",), "bat_buoc", "Nêu quan điểm phân tích và lý do.",
          (_y("quan điểm phân tích", r"quan điểm (của )?(hệ thống y tế|xã hội|người (bệnh|chi trả)|bảo hiểm|cơ sở)|"
                                     r"perspective"),)),
    "9": (("kinh_te",), "bat_buoc", "Nêu khung thời gian phân tích và lý do.",
          (_y("khung thời gian", r"khung thời gian|thời gian (phân tích|mô hình)|suốt đời|time horizon|\d+ (tháng|"
                                 r"năm)"),)),
    "10": (("kinh_te",), "bat_buoc", "Nêu tỷ lệ chiết khấu và lý do.",
           (_y("tỷ lệ chiết khấu", r"chiết khấu|discount"),)),
    "11": (("kinh_te", "bien_so"), "bat_buoc", "Nêu kết cục đo lợi ích và tác hại.",
           (_y("kết cục lợi ích", r"\bQALY\b|\bDALY\b|kết cục|năm sống"),)),
    "12": (("kinh_te", "bien_so", "cong_cu"), "bat_buoc", "Nêu cách đo kết cục.",
           (_y("cách đo kết cục", r"\bEQ-5D\b|SF-6D|đo (bằng|theo)|thang"),)),
    "13": (("kinh_te",), "bat_buoc", "Nêu quần thể và phương pháp định giá kết cục (vd bộ trọng số thoả dụng).",
           (_y("định giá kết cục", r"thoả dụng|thỏa dụng|utility|bộ (giá trị|trọng số)|value set|định giá"),)),
    "14": (("kinh_te",), "bat_buoc", "Nêu cách định giá nguồn lực và chi phí.",
           (_y("định giá chi phí", r"chi phí (trực tiếp|gián tiếp|y tế|đơn vị)|đơn giá|định giá|biểu giá"),)),
    "15": (("kinh_te",), "bat_buoc", "Nêu năm giá, đơn vị tiền tệ và phương pháp quy đổi.",
           (_y("đơn vị tiền tệ/năm giá", r"VNĐ|\bVND\b|đồng|USD|năm (giá|\d{4})|quy đổi|lạm phát"),)),
    "16": (("kinh_te",), "bat_buoc", "Mô hình hoá: mô tả mô hình và lý do dùng.",
           (_y("mô tả mô hình", r"Markov|cây quyết định|vi mô phỏng|cấu trúc mô hình|trạng thái"),),
           r"Markov|cây quyết định|mô hình (kinh tế|mô phỏng)", "có mô hình kinh tế"),
    "17": (("kinh_te", "phan_tich"), "bat_buoc", "Mô tả phương pháp phân tích, ngoại suy, giả định.",
           (_y("phân tích/giả định", r"\bICER\b|giả định|ngoại suy|tỷ số chi phí"),)),
    "18": (("kinh_te", "phan_tich"), "bat_buoc", "Mô tả cách ước lượng khác biệt kết quả theo phân nhóm.",
           (_y("không đồng nhất theo phân nhóm", r"phân nhóm|nhóm nhỏ|không đồng nhất"),)),
    "19": (("kinh_te", "phan_tich"), "bat_buoc", "Mô tả phân bố tác động giữa các cá nhân/nhóm (công bằng).",
           (_y("tác động phân bố", r"phân bố|công bằng|equity|nhóm (thu nhập|kinh tế)"),)),
    "20": (("kinh_te", "phan_tich"), "bat_buoc", "Mô tả phương pháp đặc trưng hoá bất định.",
           (_y("phân tích bất định", r"phân tích độ nhạy|xác suất|\bPSA\b|\bCEAC\b|bất định"),)),
    "21": (("kinh_te", "dao_duc", "pho_bien"), "bat_buoc", "Mô tả cách thu hút người bệnh/cộng đồng tham gia thiết kế.",
           (_y("sự tham gia của người bệnh", PPI),)),
    "22": (("du_kien_kq", "kinh_te"), "ke_hoach", "Lên kế hoạch báo cáo mọi tham số đầu vào kèm bất định và nguồn.",
           (_y("bảng tham số", r"tham số|đầu vào"),)),
    "23": (("du_kien_kq", "kinh_te"), "ke_hoach", "Lên kế hoạch báo cáo chi phí, kết cục trung bình và tỷ số chi "
                                                  "phí–hiệu quả.",
           (_y("kết quả chính", r"\bICER\b|chi phí trung bình|tỷ số chi phí"),)),
    "24": (("du_kien_kq", "kinh_te"), "ke_hoach", "Lên kế hoạch mô tả ảnh hưởng của bất định lên kết quả.",
           (_y("ảnh hưởng bất định", r"độ nhạy|bất định|CEAC|tornado"),)),
    "25": ((), "bao_cao", "Báo cáo khác biệt do sự tham gia của người bệnh/cộng đồng.", ()),
    "26": (("ban_luan", "han_che"), "ke_hoach", "Bàn phát hiện, hạn chế, công bằng, khả năng suy rộng.",
           (_y("hạn chế", r"hạn chế", de_muc=True), _y("suy rộng", SUY_RONG))),
    "27": (("kinh_phi", "bia", "dao_duc"), "bat_buoc", "Nêu nguồn kinh phí và vai trò nhà tài trợ.",
           (_y("nguồn kinh phí", KINH_PHI), _y("vai trò tài trợ", VAI_TRO_TAI_TRO)), None, "", True),
    "28": (("dao_duc", "bia", "kinh_phi"), "bat_buoc", "Khai xung đột lợi ích.", (_y("xung đột lợi ích", XUNG_DOT),)),
}

# ═════════════════════════════════════ TREND 2004 (non_randomized — chỉ cảnh báo) ═════════════════════════════════════
_TREND_CHU_DE = {
    "1": "Title and abstract", "2": "Background", "3": "Participants", "4": "Interventions", "5": "Objectives",
    "6": "Outcomes", "7": "Sample size", "8": "Assignment method", "9": "Blinding (masking)", "10": "Unit of analysis",
    "11": "Statistical methods", "12": "Participant flow", "13": "Recruitment", "14": "Baseline data",
    "15": "Baseline equivalence", "16": "Numbers analyzed", "17": "Outcomes and estimation", "18": "Ancillary analyses",
    "19": "Adverse events", "20": "Interpretation", "21": "Generalizability", "22": "Overall evidence",
}
_TREND: Dict[str, tuple] = {
    "1": ((), "bao_cao", "Tiêu đề/tóm tắt nêu cách phân bổ và quần thể.", ()),
    "2": (("dat_van_de", "tong_quan"), "bat_buoc", "Nêu cơ sở khoa học và lý thuyết làm nền cho can thiệp.",
          (_y("trích dẫn nguồn", TRICH_DAN), _y("lý thuyết nền", r"lý thuyết|khung (lý thuyết|khái niệm)|mô hình"))),
    "3": (("doi_tuong", "chon_mau", "dia_diem"), "bat_buoc", "Nêu tiêu chuẩn chọn, cách tuyển, nơi tuyển và thu thập.",
          (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True), _y("cách tuyển", r"tuyển|chọn mẫu|lấy mẫu"),
           _y("nơi", NOI))),
    "4": (("can_thiep",), "bat_buoc",
          "Mô tả can thiệp từng nhóm: nội dung, cách chuyển tải, người thực hiện, liều–thời lượng, hoạt động tăng tuân "
          "thủ.",
          (_y("nội dung can thiệp", r"nhóm can thiệp|can thiệp"), _y("nhóm so sánh", r"nhóm (chứng|so sánh)"),
           _y("liều/thời lượng", r"mỗi (ngày|tuần|tháng)|trong \d+ (ngày|tuần|tháng)|\d+\s*(buổi|lần)|thời lượng"),
           _y("người thực hiện", r"(do|bởi) .{0,60}(thực hiện|chuyển tải)|người thực hiện|điều dưỡng|bác sĩ|nhân "
                                 r"viên"))),
    "5": (("muc_tieu", "cau_hoi"), "bat_buoc", "Nêu mục tiêu cụ thể và giả thuyết.",
          (_y("mục tiêu cụ thể", MUC_TIEU_CU_THE), _y("giả thuyết", r"giả thuyết"))),
    "6": (("bien_so", "cong_cu"), "bat_buoc", "Định nghĩa kết cục chính/phụ, cách thu thập, độ giá trị của công cụ.",
          (_y("kết cục chính", r"kết cục chính"), _y("cách thu thập", r"thu thập|đo|phỏng vấn|hồ sơ"),
           _y("độ giá trị công cụ", r"độ (giá trị|tin cậy)|đã (được )?(kiểm định|chuẩn hoá)|Cronbach|\[\d+"))),
    "7": (("co_mau",), "bat_buoc", "Giải thích cách xác định cỡ mẫu (và phân tích giữa kỳ/quy tắc dừng nếu có).",
          (_y("công thức/phương pháp", CONG_THUC_CO_MAU), _y("cỡ mẫu cuối cùng", CO_MAU_CUOI))),
    "8": (("thiet_ke", "chon_mau", "can_thiep"), "bat_buoc",
          "Nêu đơn vị phân bổ, cách phân bổ và biện pháp giảm sai lệch do không ngẫu nhiên hoá.",
          (_y("đơn vị/cách phân bổ", r"phân bổ|phân nhóm|đơn vị (can thiệp|phân bổ)|theo (khoa|cơ sở|thời gian)"),
           _y("giảm sai lệch", r"ghép cặp|hiệu chỉnh|điểm xu hướng|propensity|phân tầng|tương đồng"))),
    "9": (("ngau_nhien", "sai_so", "can_thiep"), "bat_buoc", "Nêu ai được làm mù và cách làm mù (hoặc nêu không làm "
                                                             "mù).",
          (_y("làm mù", r"làm mù|che giấu|nhãn mở|không (thể )?làm mù"),)),
    "10": (("phan_tich", "thiet_ke"), "bat_buoc", "Nêu đơn vị phân tích và cách xử lý khi khác đơn vị phân bổ.",
           (_y("đơn vị phân tích", r"đơn vị phân tích|mức (cá nhân|cụm)|hiệu chỉnh (gom )?cụm|\bICC\b|\bGEE\b|hỗn "
                                   r"hợp"),)),
    "11": (("phan_tich",), "bat_buoc", "Mô tả phương pháp so sánh nhóm, phân tích bổ sung, dữ liệu thiếu, phần mềm.",
           (_y("phương pháp thống kê", PP_THONG_KE), _y("dữ liệu thiếu", DU_LIEU_THIEU),
            _y("phần mềm", r"phần mềm|\bSPSS\b|\bStata\b|\bSAS\b|\bR\b"))),
    "12": (("du_kien_kq", "quy_trinh"), "ke_hoach", "Lên kế hoạch sơ đồ luồng người tham gia.", (_y("sơ đồ "
                                                                                                    "luồng", SO_DO),)),
    "13": (("dia_diem", "thiet_ke"), "bat_buoc", "Nêu mốc thời gian tuyển và theo dõi.", (_y("mốc ngày", NGAY),)),
    "14": (("du_kien_kq",), "ke_hoach", "Lên kế hoạch bảng đặc điểm ban đầu theo nhóm.",
           (_y("bảng đặc điểm", r"Đặc điểm (chung|đối tượng|nền|ban đầu)", de_muc=True),)),
    "15": (("phan_tich", "du_kien_kq"), "ke_hoach", "Lên kế hoạch đánh giá tương đồng ban đầu và cách kiểm soát khác "
                                                    "biệt.",
           (_y("tương đồng ban đầu", r"tương đồng|khác biệt ban đầu|cân bằng|hiệu chỉnh"),)),
    "16": (("phan_tich",), "ke_hoach", "Nêu mẫu số của từng phân tích, có theo ý định điều trị không.",
           (_y("quần thể phân tích", r"ý định điều trị|\bITT\b|theo đề cương|quần thể (chính|phân tích)"),)),
    "17": (("du_kien_kq", "phan_tich"), "ke_hoach", "Lên kế hoạch báo cáo cỡ hiệu ứng kèm khoảng tin cậy.",
           (_y("khoảng tin cậy", r"KTC|khoảng tin cậy|\bCI\b"),)),
    "18": (("phan_tich", "du_kien_kq"), "ke_hoach", "Phân biệt phân tích định trước và thăm dò.",
           (_y("định trước/thăm dò", r"định trước|tiền định|xác định trước|thăm dò"),)),
    "19": (("du_kien_kq", "giam_sat", "dao_duc"), "ke_hoach", "Lên kế hoạch báo cáo tác dụng bất lợi theo nhóm.",
           (_y("bất lợi", r"bất lợi|ngoài ý muốn|không mong muốn"),)),
    "20": ((), "bao_cao", "Diễn giải kết quả so với giả thuyết.", ()),
    "21": (("han_che", "ban_luan"), "ke_hoach", "Bàn tính khái quát.", (_y("suy rộng", SUY_RONG),)),
    "22": ((), "bao_cao", "Diễn giải chung trong bối cảnh chứng cứ.", ()),
}

# ═════════════════════════════════════ CARE 2013 (case_report) ═════════════════════════════════════
_CARE: Dict[str, tuple] = {
    "1": ((), "bao_cao", "Tiêu đề có chữ «báo cáo ca» và hiện tượng quan tâm.", ()),
    "2": ((), "bao_cao", "Từ khoá.", ()), "3a": ((), "bao_cao", "Tóm tắt — giới thiệu.", ()),
    "3b": ((), "bao_cao", "Tóm tắt — trình bày ca.", ()), "3c": ((), "bao_cao", "Tóm tắt — kết luận.", ()),
    "4": (("dat_van_de", "tong_quan"), "bat_buoc", "Tóm tắt bối cảnh của ca, dẫn y văn liên quan.",
          (_y("trích dẫn nguồn", TRICH_DAN),)),
    "5a": (("trinh_bay_ca", "doi_tuong"), "bat_buoc", "Thông tin nhân khẩu học (khử định danh).",
           (_y("nhân khẩu học", r"tuổi|giới|nghề"),)),
    "5b": (("trinh_bay_ca",), "bat_buoc", "Triệu chứng chính.", (_y("triệu chứng", r"triệu chứng|lý do (vào viện|"
                                                                                   r"khám)"),)),
    "5c": (("trinh_bay_ca",), "bat_buoc", "Tiền sử bệnh, gia đình, tâm lý–xã hội.", (_y("tiền sử", r"tiền sử"),)),
    "6": (("trinh_bay_ca",), "bat_buoc", "Phát hiện khám thực thể.", (_y("khám", r"khám"),)),
    "7": (("trinh_bay_ca", "tien_do"), "bat_buoc", "Mốc thời gian quan trọng (bảng/hình).",
          (_y("dòng thời gian", r"dòng thời gian|mốc thời gian|timeline"),)),
    "8a": (("trinh_bay_ca",), "bat_buoc", "Phương pháp chẩn đoán.", (_y("chẩn đoán", r"xét nghiệm|chẩn đoán hình ảnh|"
                                                                                     r"chẩn đoán"),)),
    "8b": (("trinh_bay_ca",), "bat_buoc", "Khó khăn trong chẩn đoán.", (_y("khó khăn chẩn đoán", r"khó khăn|thách "
                                                                                                 r"thức"),)),
    "8c": (("trinh_bay_ca",), "bat_buoc", "Lập luận chẩn đoán, chẩn đoán phân biệt.",
           (_y("chẩn đoán phân biệt", r"chẩn đoán phân biệt"),)),
    "8d": (("trinh_bay_ca",), "bat_buoc", "Đặc điểm tiên lượng (vd giai đoạn).", (_y("tiên lượng", r"tiên lượng|giai "
                                                                                                   r"đoạn"),),
           r"ung thư|giai đoạn|tiên lượng", "có yếu tố tiên lượng"),
    "9a": (("trinh_bay_ca", "can_thiep"), "bat_buoc", "Loại can thiệp, cách dùng, thay đổi can thiệp.",
           (_y("can thiệp/điều trị", r"điều trị|can thiệp|liều"),)),
    "10a": (("trinh_bay_ca",), "bat_buoc", "Diễn tiến theo dõi, kết cục, tuân thủ, biến cố bất lợi.",
            (_y("theo dõi/kết cục", r"theo dõi|kết cục|tái khám"),)),
    "11a": (("ban_luan",), "ke_hoach", "Điểm mạnh và hạn chế của xử trí ca.", (_y("hạn chế", r"hạn chế|điểm mạnh"),)),
    "11b": (("ban_luan",), "ke_hoach", "Y văn liên quan.", (_y("y văn", TRICH_DAN + r"|y văn"),)),
    "11c": (("ban_luan",), "ke_hoach", "Lý do của kết luận (kể cả quan hệ nhân quả).", (_y("lập luận", r"nhân quả|lý "
                                                                                                       r"do"),)),
    "11d": (("ban_luan",), "ke_hoach", "Bài học chính.", (_y("bài học", r"bài học|thông điệp"),)),
    "12": (("trinh_bay_ca", "ban_luan"), "ke_hoach", "Quan điểm của người bệnh.",
           (_y("quan điểm người bệnh", r"quan điểm|trải nghiệm|chia sẻ của người bệnh"),)),
    "13": (("dao_duc",), "bat_buoc", "Người bệnh đồng ý cho công bố.", (_y("đồng ý công bố", DONG_Y),)),
}

# ═════════════════════════════════════ COSMIN 2021 (kiểm định bộ câu hỏi/PROM) ═════════════════════════════════════
_COSMIN_CHU_DE = {
    "I1": "Name and describe the PROM", "I2": "Target population", "I3": "Original development citation",
    "I4": "State of knowledge & rationale", "I6": "Objectives and hypotheses", "GM1": "Study design",
    "GM2": "Participants", "GM3": "PROM administration", "GM4": "Data collection procedures",
    "GM5": "Power/sample size calculation", "GM6": "Statistical analyses", "GM7": "Missing data",
    "D3": "Strengths and limitations", "D4": "Generalizability", "O1": "Conflict of interest",
    "CV1": "Relevance", "CV2": "Comprehensiveness", "CV3": "Comprehensibility", "SV1": "Factor analyses (CTT PROMs)",
    "IC1": "Unit of measurement", "IC2": "Continuous scores", "CCV1": "Comparator group(s)",
    "R1": "PROM administrations", "R2": "Statistical analyses (reliability)", "CriV1": "Criterion",
    "ConV1": "Comparator instrument(s)", "ConV3": "Hypotheses (construct validity)",
}
GIA_TRI_NOI_DUNG = r"giá trị nội dung|\bCVI\b|phỏng vấn nhận thức|chuyên gia (đánh giá|thẩm định)"
PHAN_TICH_NHAN_TO = r"phân tích nhân tố|\bEFA\b|\bCFA\b"
CRONBACH = r"Cronbach|nhất quán nội tại|omega"
# «ICC» trơn KHÔNG dùng làm điều kiện: đề cương khảo sát có chọn mẫu cụm dùng ICC cho hiệu ứng gom cụm (C1a, 21/11/2026)
TEST_RETEST = (r"test[\s–-]*retest|đo lặp lại|độ tin cậy (lặp lại|test)|kappa|\bICC\b.{0,40}(lặp lại|hai lần đo|giữa "
               r"hai lần)")
GIA_TRI_GIA_THUYET = (r"giá trị (hội tụ|phân biệt)|(sự |tính )?hội tụ (với|giữa)|kiểm định giả thuyết (về )?giá trị|"
                      r"construct validity|convergent")
_COSMIN: Dict[str, tuple] = {
    "I1": (("cong_cu", "tong_quan"), "bat_buoc", "Giới thiệu bộ câu hỏi: tên, phiên bản, ngôn ngữ, cấu trúc, cách "
                                                 "chấm.",
           (_y("tên/nguồn bộ câu hỏi", r"bộ câu hỏi|thang|Mẫu số|Quyết định"),
            _y("cấu trúc/cách chấm", r"\d+\s*(câu|mục|phần|lĩnh vực)|thang (Likert|\d)|chấm điểm|cách tính điểm"))),
    "I2": (("cong_cu", "doi_tuong"), "bat_buoc", "Mô tả quần thể đích của bộ câu hỏi.",
           (_y("quần thể đích", r"dành cho|áp dụng (cho|với)|người bệnh|đối tượng"),)),
    "I3": (("cong_cu", "tong_quan"), "bat_buoc", "Dẫn bài phát triển gốc của bộ câu hỏi.", (_y("trích dẫn "
                                                                                               "gốc", TRICH_DAN),)),
    "I4": (("tong_quan", "cong_cu", "dat_van_de"), "bat_buoc",
           "Tóm lược hiểu biết về đặc tính đo lường của đúng phiên bản và lý do nghiên cứu.",
           (_y("đặc tính đo lường đã biết", r"độ (tin cậy|giá trị)|Cronbach|đã (được )?kiểm định|chưa (được )?kiểm "
                                            r"định"),)),
    "I6": (("muc_tieu", "cau_hoi", "cong_cu"), "bat_buoc", "Nêu mục tiêu và giả thuyết liên quan bộ câu hỏi.",
           (_y("mục tiêu về bộ câu hỏi", r"(kiểm định|đánh giá|thích ứng|chuẩn hoá).{0,80}(bộ câu hỏi|thang|công cụ)|"
                                         r"độ "
                                         r"(tin cậy|giá trị)"),)),
    "GM1": (("thiet_ke", "cong_cu"), "bat_buoc", "Nêu yếu tố then chốt của thiết kế kiểm định.",
            (_y("thiết kế kiểm định", r"cắt ngang|test[\s–-]*retest|dọc|kiểm định"),)),
    "GM2": (("doi_tuong", "chon_mau"), "bat_buoc", "Nêu cách chọn người tham gia và tiêu chuẩn chọn/loại.",
            (_y("tiêu chuẩn chọn", TIEU_CHUAN_CHON, de_muc=True),)),
    "GM3": (("quy_trinh", "cong_cu"), "bat_buoc", "Mô tả bộ câu hỏi được thực hiện khi nào, ở đâu, phương tiện gì.",
            (_y("hình thức thực hiện", r"tự điền|phỏng vấn|giấy|điện tử|trực tuyến"),
             _y("thời điểm/nơi", r"(sau|trước|khi) (khám|ra viện|tư vấn)|tại (khu vực|phòng|quầy|khoa)|thời điểm"))),
    "GM5": (("co_mau", "cong_cu"), "bat_buoc", "Trình bày cỡ mẫu cho phân tích đặc tính đo lường (hoặc quy tắc kinh "
                                               "nghiệm).",
            (_y("cỡ mẫu cho kiểm định", r"(cỡ mẫu|số người).{0,160}(phân tích nhân tố|kiểm định|Cronbach|thử nghiệm|"
                                       r"test[\s–-]*retest)|(\d+|mười) (người|đối tượng|quan sát|phiếu) (cho|mỗi|trên) "
                                       r"(mỗi )?(câu|mục)"),)),
    "GM6": (("phan_tich", "cong_cu"), "bat_buoc", "Mô tả phân tích thống kê cho mọi đặc tính đo lường và ngưỡng đánh "
                                                  "giá.",
            (_y("phân tích đặc tính đo lường", CRONBACH + "|" + PHAN_TICH_NHAN_TO + "|" + GIA_TRI_NOI_DUNG),
             _y("ngưỡng chấp nhận", r"≥\s*0[,.]\d|ngưỡng|tối thiểu"))),
    "GM7": (("phan_tich", "cong_cu"), "bat_buoc", "Nêu cách xử lý dữ liệu thiếu.",
            (_y("dữ liệu thiếu", DU_LIEU_THIEU), _y("phương pháp xử lý", XU_LY_THIEU)), None, "", True),
    "D3": (("han_che",), "ke_hoach", "Bàn điểm mạnh, hạn chế, sai lệch tiềm ẩn của kiểm định.",
           (_y("hạn chế", HAN_CHE, de_muc=True),)),
    "D4": (("han_che", "ban_luan"), "ke_hoach", "Bàn khả năng khái quát sang quần thể khác.",
           (_y("suy rộng", SUY_RONG),)),
    "O1": (("dao_duc", "bia", "kinh_phi"), "bat_buoc", "Khai xung đột lợi ích liên quan bộ câu hỏi.",
           (_y("xung đột lợi ích", XUNG_DOT),)),
    "CV1": (("cong_cu", "quy_trinh"), "bat_buoc", "Nêu cách hỏi người bệnh/chuyên gia về mức liên quan của từng câu.",
            (_y("đánh giá mức liên quan", r"liên quan|\bI-CVI\b|\bCVI\b|chuyên gia (đánh giá|"
                                          r"chấm)"),), GIA_TRI_NOI_DUNG,
            "kiểm định giá trị nội dung"),
    "CV2": (("cong_cu", "quy_trinh"), "bat_buoc", "Nêu cách hỏi về độ bao quát khái niệm then chốt.",
            (_y("độ bao quát", r"bao quát|đầy đủ|thiếu (khía cạnh|nội dung)|bổ sung câu"),), GIA_TRI_NOI_DUNG,
            "kiểm định giá trị nội dung"),
    "CV3": (("cong_cu", "quy_trinh"), "bat_buoc", "Nêu cách đánh giá mức dễ hiểu của câu hỏi, phương án trả lời.",
            (_y("độ dễ hiểu", r"dễ hiểu|hiểu (đúng|câu)|phỏng vấn nhận thức|diễn đạt"),), GIA_TRI_NOI_DUNG,
            "kiểm định giá trị nội dung"),
    "SV1": (("phan_tich", "cong_cu"), "bat_buoc", "Phân tích nhân tố: lý do, mô hình kiểm, giả định, tiêu chí phù hợp.",
            (_y("phân tích nhân tố", PHAN_TICH_NHAN_TO),
             _y("giả định/tiêu chí phù hợp", r"\bKMO\b|Bartlett|\bRMSEA\b|\bCFI\b|\bTLI\b|hệ số tải|eigenvalue|giá trị "
                                            r"riêng")), PHAN_TICH_NHAN_TO, "có phân tích nhân tố"),
    "IC1": (("phan_tich", "cong_cu"), "bat_buoc", "Nêu nhất quán nội tại cho từng thang/tiểu thang đơn chiều.",
            (_y("nhất quán nội tại theo thang", r"(từng|mỗi) (thang|tiểu thang|lĩnh vực|khía cạnh)|tiểu thang"),),
            CRONBACH, "có đánh giá nhất quán nội tại"),
    "IC2": (("phan_tich", "cong_cu"), "bat_buoc", "Nêu thống kê nhất quán nội tại (Cronbach alpha/omega) và ngưỡng.",
            (_y("alpha/omega", r"Cronbach|omega"), _y("ngưỡng", r"≥\s*0[,.]\d|ngưỡng")), CRONBACH,
            "có đánh giá nhất quán nội tại"),
    "CCV1": (("phan_tich", "cong_cu"), "bat_buoc", "Thích ứng văn hoá: mô tả nhóm so sánh và cỡ mẫu từng nhóm.",
             (_y("nhóm so sánh", r"nhóm (so sánh|ngôn ngữ)|đa nhóm|bất biến đo lường|\bDIF\b"),),
             r"thích ứng (văn ho[áa]|xuyên)|bất biến đo lường|\bDIF\b", "có kiểm định xuyên văn hoá"),
    "R1": (("quy_trinh", "cong_cu"), "bat_buoc", "Mô tả số lần đo, khoảng cách giữa các lần đo, điều kiện đo.",
           (_y("khoảng cách giữa lần đo", r"(sau|cách) \d+\s*(ngày|tuần)|khoảng cách"),), TEST_RETEST, "có đo độ tin "
                                                                                                       "cậy lặp lại"),
    "R2": (("phan_tich",), "bat_buoc", "Mô tả và biện minh phân tích độ tin cậy (mô hình ICC, kappa).",
           (_y("mô hình ICC/kappa", r"\bICC\b.{0,60}(mô hình|hai chiều|tuyệt đối|nhất quán)|kappa"),), TEST_RETEST,
           "có đo độ tin cậy lặp lại"),
    "CriV1": (("cong_cu", "phan_tich"), "bat_buoc", "Mô tả tiêu chuẩn đối chiếu và lý do chọn.",
              (_y("tiêu chuẩn đối chiếu", CHUAN_THAM_CHIEU + r"|tiêu chuẩn đối chiếu"),),
              r"giá trị tiêu chuẩn|criterion validity", "có kiểm định giá trị tiêu chuẩn"),
    "ConV1": (("cong_cu", "phan_tich"), "bat_buoc", "Mô tả công cụ so sánh theo khái niệm đo.",
              (_y("công cụ so sánh", r"công cụ (so sánh|đối chiếu)|thang (khác|đối chiếu)|hội tụ với (câu |chỉ số |"
                                     r"thang )?"
                                   r"[A-ZĐ]{0,3}\d|đối chiếu với (câu|thang|chỉ số|công cụ)"),),
              GIA_TRI_GIA_THUYET, "có kiểm định giả thuyết giá trị cấu trúc (hội tụ/phân biệt)"),
    "ConV3": (("cong_cu", "phan_tich", "cau_hoi"), "bat_buoc", "Nêu giả thuyết kèm chiều và độ lớn kỳ vọng.",
              (_y("giả thuyết chiều/độ lớn", r"giả thuyết.{0,160}(tương quan|cao hơn|thấp hơn|≥|r\s*[><=])"),),
              GIA_TRI_GIA_THUYET, "có kiểm định giả thuyết giá trị cấu trúc (hội tụ/phân biệt)"),
}

# ───────────────────────────── lắp mục kiểm ─────────────────────────────
#: chuẩn → (bảng tiêu chí, {mã: (chủ đề, nguyên văn|None)})


def _nguon_spirit() -> Dict[str, Tuple[str, Optional[str]]]:
    return {ma: (ma, van) for ma, van, _vt in PCI.SPIRIT_2025_ITEMS}


def _nguon_prisma_p() -> Dict[str, Tuple[str, Optional[str]]]:
    return {ma: (ma, van) for ma, van, _vt in PCI.PRISMA_P_2015_ITEMS}


def _nguon_4(bo) -> Dict[str, Tuple[str, Optional[str]]]:
    return {x[0]: (x[2], x[-1]) for x in bo}


def _chi_chu_de(d: Dict[str, str]) -> Dict[str, Tuple[str, Optional[str]]]:
    return {ma: (cd, None) for ma, cd in d.items()}


BANG: Dict[str, tuple] = {
    "SPIRIT 2025": (_SPIRIT, _nguon_spirit),
    "PRISMA-P 2015": (_PRISMA_P, _nguon_prisma_p),
    "STARD 2015": (_STARD, lambda: _nguon_4(CBC.STARD_2015_ITEMS)),
    "TRIPOD+AI 2024": (_TRIPOD_AI, lambda: _nguon_4(CBC.TRIPOD_AI_2024_ITEMS)),
    "COREQ 2007": (_COREQ, lambda: _chi_chu_de(_COREQ_CHU_DE)),
    "SRQR 2014": (_SRQR, lambda: _chi_chu_de(_SRQR_CHU_DE)),
    "GRAMMS 2008": (_GRAMMS, lambda: _chi_chu_de(_GRAMMS_CHU_DE)),
    "SQUIRE 2.0": (_SQUIRE, lambda: _nguon_4(CBC.SQUIRE_2_0_ITEMS)),
    "CHEERS 2022": (_CHEERS, lambda: _nguon_4(CBC.CHEERS_2022_ITEMS)),
    "TREND 2004": (_TREND, lambda: _chi_chu_de(_TREND_CHU_DE)),
    "CARE 2013": (_CARE, lambda: {x[0]: (x[1], x[2]) for x in CBC.CARE_2013_ITEMS}),
    "COSMIN 2021": (_COSMIN, lambda: _chi_chu_de(_COSMIN_CHU_DE)),
}


def danh_sach_muc_them(chuan: str) -> Optional[List[MucKiem]]:
    """Mục kiểm của một chuẩn trong tệp này; None nếu chuẩn không có ở đây."""
    if chuan not in BANG:
        return None
    bang, nguon = BANG[chuan]
    van = nguon()
    chan = chuan not in CHUAN_CHUA_DOI_CHIEU_GOC
    ra = []
    for ma, tc in bang.items():
        phan, muc_do, tieu_chi, yeu_to = tc[:4]
        khi, ly_do = (tc[4], tc[5]) if len(tc) > 4 else (None, "")
        cung = bool(tc[6]) if len(tc) > 6 else False
        chu_de, nguyen_van = van.get(ma, (ma, None))
        ra.append(MucKiem(chuan, ma, chu_de, nguyen_van, tieu_chi, tuple(phan), tuple(yeu_to), muc_do, khi, ly_do, cung,
                          chan))
    return ra
