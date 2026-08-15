#!/usr/bin/env python3
"""Nguồn sự thật (canon) của skill `nghien-cuu-y-khoa-chuan-quoc-te`.

Module này mã hoá các chuẩn của skill để CHUỖI cổng tự động (run_g*_auto.py)
tuân thủ ĐÚNG mẫu/checklist của skill một cách tự động, thay vì để Claude tự
đối chiếu thủ công mỗi lần. Bao gồm:

- 5 NHÃN TRẠNG THÁI bắt buộc khi soạn hồ sơ.
- Mẫu ĐỀ CƯƠNG 16 mục và 20 thành phần protocol lõi.
- Định nghĩa 10 CỔNG CHẤT LƯỢNG của skill (G0-G9): điều kiện tối thiểu + sản
  phẩm bắt buộc (SKILL.md).
- BẢN ĐỒ CHUẨN BÁO CÁO theo mã thiết kế (references/02_ban_do_chuan_bao_cao.md).
- QUY TẮC KẾT LUẬN "sẵn sàng" (SKILL.md §Cổng chất lượng).
- Tham chiếu PHÁP LÝ/ĐẠO ĐỨC Việt Nam + quốc tế, kèm cờ [CẦN KIỂM CHỨNG NGUỒN
  CHÍNH THỨC] theo đúng Quy tắc 7 của skill.

QUAN TRỌNG — HAI HỆ ĐÁNH SỐ CỔNG KHÁC NHAU:
  Chuỗi pipeline (run_g*_auto.py) và skill DÙNG CHUNG nhãn G0-G9 nhưng Ý NGHĨA
  KHÁC nhau ở một số chỉ số. Ví dụ: pipeline G2 = Đạo đức IRB, nhưng skill G3 =
  Đạo đức. Pipeline G3/G4 = Cỡ mẫu/SAP, nhưng skill G2 = Protocol. Vì vậy phải
  DÙNG bản đồ chéo PIPELINE_TO_SKILL_GATE dưới đây, KHÔNG ghép 1-1 theo số.

Nguồn skill tham chiếu (phiên bản 5.2, ngày skill tự ghi 2026-06-06 — xem
MANIFEST.md của skill). Khi trích luật/tiêu chuẩn để KẾT LUẬN, luôn kiểm nguồn
chính thức; nếu chưa kiểm được thì giữ nguyên cờ [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC].
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ════════════════════════════════════════════════════════════════════════════
# 1. NĂM NHÃN TRẠNG THÁI (SKILL.md §Trạng thái bắt buộc khi soạn hồ sơ)
# ════════════════════════════════════════════════════════════════════════════

# Mỗi ô thông tin trong hồ sơ phải mang đúng MỘT trong 5 nhãn này.
STATUS_TAGS: Dict[str, str] = {
    "DA_CUNG_CAP": "[ĐÃ CUNG CẤP]",           # lấy từ hồ sơ/dữ liệu người dùng gửi
    "DA_KIEM_CHUNG": "[ĐÃ KIỂM CHỨNG]",       # đã đối chiếu nguồn chính thức
    "CAN_BO_SUNG": "[CẦN BỔ SUNG]",           # thiếu thông tin để hoàn thiện
    "CAN_XAC_NHAN_DON_VI": "[CẦN XÁC NHẬN TẠI ĐƠN VỊ]",  # phụ thuộc BV/IRB/cơ quan
    "DU_THAO": "[DỰ THẢO]",                    # chưa được phê duyệt/chưa khoá
}

# Cờ đặc biệt theo Quy tắc 7: dùng khi CHƯA kiểm được nguồn chính thức của
# chuẩn/luật/đăng ký/yêu cầu tạp chí.
TAG_CAN_KIEM_CHUNG_NGUON = "[CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]"

# Danh sách phẳng mọi nhãn hợp lệ (dùng cho validator check_de_cuong.py).
VALID_STATUS_TAGS: Tuple[str, ...] = tuple(STATUS_TAGS.values()) + (
    TAG_CAN_KIEM_CHUNG_NGUON,
)


def is_valid_status_tag(tag_text: str) -> bool:
    """Kiểm 1 chuỗi nhãn (vd '[ĐÃ CUNG CẤP]') có thuộc bộ nhãn skill hợp lệ."""
    return tag_text.strip() in VALID_STATUS_TAGS


# ════════════════════════════════════════════════════════════════════════════
# 2. MẪU ĐỀ CƯƠNG 16 MỤC (templates/01_mau_de_cuong_tong_the.md)
# ════════════════════════════════════════════════════════════════════════════

# Mỗi phần tử: (số mục, tiêu đề, danh sách tiểu mục). Tiểu mục rỗng = không có.
DE_CUONG_SECTIONS: List[Tuple[str, str, List[str]]] = [
    ("1", "Tóm tắt", []),
    ("2", "Đặt vấn đề", []),
    ("3", "Câu hỏi nghiên cứu và giả thuyết", []),
    ("4", "Mục tiêu", ["4.1. Mục tiêu chung", "4.2. Mục tiêu cụ thể"]),
    ("5", "Thiết kế và bối cảnh", []),
    ("6", "Đối tượng nghiên cứu",
     ["6.1. Tiêu chuẩn chọn", "6.2. Tiêu chuẩn loại", "6.3. Tuyển mẫu"]),
    ("7", "Biến số và kết cục", []),
    ("8", "Cỡ mẫu", []),
    ("9", "Công cụ và quy trình thu thập", []),
    ("10", "Quản trị dữ liệu và bảo mật", []),
    ("11", "Kế hoạch phân tích thống kê", []),
    ("12", "Sai lệch và kiểm soát", []),
    ("13", "Đạo đức nghiên cứu", []),
    ("14", "Kế hoạch phổ biến kết quả/ứng dụng", []),
    ("15", "Tiến độ và nguồn lực", []),
    ("16", "Tài liệu tham khảo Vancouver/NLM", []),
]

# Phụ lục bắt buộc kèm đề cương (templates/01 §Phụ lục).
DE_CUONG_PHU_LUC: List[str] = [
    "Ma trận mục tiêu – biến – phân tích – bảng",
    "CRF/phiếu khảo sát",
    "Phiếu đồng thuận (ICF)",
    "Data dictionary",
    "SAP (Kế hoạch phân tích thống kê)",
    "Checklist reporting guideline",
]

# Hai mươi thành phần NỘI DUNG của một protocol y khoa. Một đề cương có thể giữ
# bố cục 16 chương để phù hợp hồ sơ trong nước, nhưng validator phải chứng minh
# đủ 20 thành phần này; số chương không thay thế độ đầy đủ nội dung.
PROTOCOL_CORE_ITEMS: Tuple[Tuple[str, str], ...] = (
    ("P01", "Trang bìa, mã đề tài, phiên bản và ngày"),
    ("P02", "Tóm tắt protocol"),
    ("P03", "Bối cảnh và lý do nghiên cứu"),
    ("P04", "Câu hỏi nghiên cứu và giả thuyết"),
    ("P05", "Mục tiêu chính và mục tiêu phụ"),
    ("P06", "Thiết kế, bối cảnh và thời gian"),
    ("P07", "Đối tượng, tiêu chuẩn chọn và loại"),
    ("P08", "Tuyển mẫu và quy trình đồng thuận"),
    ("P09", "Phơi nhiễm, can thiệp hoặc đánh giá"),
    ("P10", "Kết cục và định nghĩa vận hành"),
    ("P11", "Biến số, yếu tố nhiễu và biến tương tác"),
    ("P12", "Cỡ mẫu và giả định"),
    ("P13", "Thu thập dữ liệu và quản lý chất lượng"),
    ("P14", "Quản trị dữ liệu và bảo mật"),
    ("P15", "Kế hoạch phân tích thống kê"),
    ("P16", "Sai lệch và biện pháp giảm thiểu"),
    ("P17", "Đạo đức và an toàn"),
    ("P18", "Đăng ký và phổ biến kết quả"),
    ("P19", "Tiến độ, nhân lực và kinh phí"),
    ("P20", "Tài liệu tham khảo và phụ lục"),
)

# Các nội dung phải được làm rõ thêm theo thiết kế. Đây là bản đồ tối thiểu để
# G10 sinh gói quyết định; checklist chi tiết vẫn phải đối chiếu nguồn chính
# thức trước khi nộp.
DESIGN_PROTOCOL_REQUIREMENTS: Dict[str, Tuple[str, ...]] = {
    "cross_sectional": (
        "Khung chọn mẫu và xử lý không đáp ứng",
        "Công cụ khảo sát/PROM, bản quyền và quy tắc chấm điểm khi áp dụng",
        "STROBE; CROSS/COSMIN/RECORD khi phù hợp",
    ),
    "case_control": (
        "Định nghĩa ca và chứng, nguồn tuyển và matching khi áp dụng",
        "Cửa sổ phơi nhiễm và kiểm soát recall/selection bias",
        "STROBE",
    ),
    "cohort": (
        "Mốc bắt đầu theo dõi, lịch follow-up và tiêu chí kiểm duyệt",
        "Xử lý mất theo dõi và time-varying exposure khi áp dụng",
        "STROBE; RECORD khi dùng dữ liệu thường quy",
    ),
    "rct": (
        "Can thiệp và comparator đủ chi tiết để tái lập",
        "Randomization, allocation concealment và blinding",
        "Harms, monitoring, stopping rules và lịch SPIRIT",
        "Đăng ký trial trước tuyển mẫu; SPIRIT 2025 và CONSORT 2025",
    ),
    "non_randomized": (
        "Mô tả can thiệp/comparator và cách phân nhóm",
        "Kiểm soát confounding by indication và ROBINS-I",
        "TREND hoặc STROBE phù hợp",
    ),
    "diagnostic": (
        "Index test, reference standard và ngưỡng định trước",
        "Blinding giữa index test/reference standard",
        "Spectrum/verification bias và bảng 2x2",
        "STARD",
    ),
    "prediction": (
        "Định nghĩa target outcome và thời điểm dự báo",
        "Cỡ mẫu theo số biến/biến cố và xử lý overfitting",
        "Internal/external validation, calibration, discrimination và utility",
        "TRIPOD+AI; PROBAST+AI khi phù hợp",
    ),
    "systematic_review": (
        "Tiêu chí chọn nghiên cứu và chiến lược tìm kiếm tái lập",
        "Quy trình sàng lọc/trích xuất kép và risk of bias",
        "Kế hoạch tổng hợp, heterogeneity, sensitivity và certainty",
        "PRISMA-P; PROSPERO/OSF khi phù hợp",
    ),
    "qualitative": (
        "Sampling, information power/bão hòa và reflexivity",
        "Quy trình ghi âm, phiên mã, mã hóa và audit trail",
        "COREQ hoặc SRQR",
    ),
    "mixed_methods": (
        "Lý do mixed-method và thứ tự/ưu tiên hai nhánh",
        "Điểm tích hợp, joint display và meta-inference",
        "Checklist cho từng nhánh",
    ),
    "quality_improvement": (
        "Phân định QI hay research tại đơn vị",
        "Chỉ số outcome/process/balancing và kế hoạch PDSA/SPC",
        "SQUIRE 2.0",
    ),
    "economic": (
        "Perspective, time horizon, discounting và currency year",
        "Nguồn chi phí/utility và uncertainty analysis",
        "CHEERS 2022",
    ),
}

# Chuẩn tối thiểu cho bảng/hình trong đề cương và bản thảo khoa học.
# Mỗi đề cương G10 phải có danh mục này để tránh bản thảo thiếu Table 1/flowchart/
# biểu đồ chính hoặc thiếu caption/trục/đơn vị khi đi từ SAP sang manuscript.
DISPLAY_ITEM_CHECKLIST: Tuple[str, ...] = (
    "Caption tự giải thích được, nêu rõ dân số/phân nhóm/thời điểm.",
    "Mọi bảng/hình có N/mẫu số hoặc n phân tích; nêu thiếu dữ liệu nếu có.",
    "Bảng có đơn vị, thang đo, số chữ số thập phân và chú thích viết tắt.",
    "Hình có nhãn trục, đơn vị, chú giải, thang đo; không dùng màu làm kênh duy nhất.",
    "Ước lượng chính đi kèm 95% CI/KTC 95% và p-value khi phù hợp với SAP.",
    "Không lặp cùng một thông tin chi tiết ở cả văn bản, bảng và hình.",
)

DISPLAY_ITEM_CORE: Tuple[Tuple[str, str, str], ...] = (
    ("Bảng 1", "Đặc điểm nền/đặc điểm mẫu",
     "N, n (%), trung bình ± ĐLC hoặc trung vị [IQR], đơn vị, thiếu dữ liệu."),
    ("Bảng 2", "Kết cục chính/phân tích chính",
     "Ước lượng hiệu ứng hoặc tỷ lệ chính, 95% CI/KTC 95%, p-value theo SAP."),
    ("Hình 1", "Sơ đồ dòng người tham gia/nghiên cứu",
     "CONSORT/STROBE/PRISMA/STARD flow; n tuyển, loại, phân tích, lý do loại."),
)

DISPLAY_ITEM_BY_DESIGN: Dict[str, Tuple[str, str]] = {
    "cross_sectional": (
        "Biểu đồ phân bố/kết cục chính hoặc forest plot yếu tố liên quan",
        "Trục có đơn vị; hiển thị n/mẫu số; 95% CI cho tỷ lệ/OR/PR nếu có.",
    ),
    "case_control": (
        "Forest plot OR hiệu chỉnh cho phơi nhiễm chính",
        "OR/aOR, 95% CI, nhóm tham chiếu, biến điều chỉnh theo SAP.",
    ),
    "cohort": (
        "Kaplan-Meier/forest plot HR hoặc biểu đồ nguy cơ tích lũy",
        "Số at-risk theo mốc thời gian, HR/aHR, 95% CI, log-rank nếu phù hợp.",
    ),
    "rct": (
        "Forest plot hiệu quả điều trị hoặc biểu đồ kết cục chính",
        "ITT/PP, effect size, 95% CI, harms nếu là kết cục an toàn.",
    ),
    "diagnostic": (
        "ROC curve + bảng 2x2 ở ngưỡng định trước",
        "AUC, 95% CI, sensitivity/specificity, threshold, reference standard.",
    ),
    "prediction": (
        "Calibration plot/ROC/decision curve",
        "AUC/C-statistic, calibration slope/intercept, net benefit, 95% CI.",
    ),
    "systematic_review": (
        "Forest plot kết quả gộp",
        "Effect measure, 95% CI, I², τ², mô hình fixed/random theo protocol.",
    ),
    "quality_improvement": (
        "Run chart/SPC chart theo thời gian",
        "Trục thời gian, baseline, center line/control limits, chú thích can thiệp.",
    ),
    "economic": (
        "Cost-effectiveness plane hoặc acceptability curve",
        "Perspective, currency/year, ICER/NMB, uncertainty intervals.",
    ),
    "mixed_methods": (
        "Joint display tích hợp định lượng-định tính",
        "Nguồn dữ liệu, theme, chỉ số định lượng, inference tích hợp.",
    ),
    "qualitative": (
        "Sơ đồ chủ đề/conceptual framework",
        "Nguồn trích dẫn ẩn danh, theme/subtheme, audit trail/reflexivity.",
    ),
}

# Chuẩn tuân thủ quốc tế tối thiểu cho báo cáo/bài báo khoa học. G10 dùng bảng
# này để sinh ma trận bắt buộc; check_de_cuong.py dùng R8 để không cho đề cương
# PASS nếu thiếu lớp minh bạch/tái lập/ICH-GCP.
INTERNATIONAL_REPORTING_GUIDELINES: Tuple[str, ...] = (
    "CONSORT",
    "STROBE",
    "PRISMA",
    "STARD",
    "TRIPOD",
    "SPIRIT",
    "CHEERS",
    "CARE",
    "SQUIRE",
)

INTERNATIONAL_COMPLIANCE_CORE: Tuple[Tuple[str, str, str], ...] = (
    ("Reporting guideline",
     "EQUATOR map: CONSORT/STROBE/PRISMA/STARD/TRIPOD/SPIRIT/CHEERS/CARE/SQUIRE",
     "Checklist đúng thiết kế, điền từng mục, nêu số trang/dòng trong bản thảo."),
    ("Ethics + ICH-GCP",
     "Helsinki, ICH-GCP E6(R3), IRB/EC approval, informed consent, trial registration khi cần",
     "Số IRB thật, ngày duyệt, consent/waiver, đăng ký nghiên cứu; không để AI tự phê duyệt."),
    ("Protocol + SAP",
     "Protocol định trước, SAP khóa trước khi xem dữ liệu, mọi deviation được log",
     "Protocol version, SAP lock certificate, amendment/deviation log, seed/phần mềm phân tích."),
    ("Transparency",
     "Data availability, code availability, funding, COI, AI disclosure, authorship/CRediT",
     "Tuyên bố dữ liệu/mã nguồn, nguồn tài trợ, ICMJE COI, khai báo AI, đóng góp tác giả."),
    ("Reliability",
     "Nguồn truy nguyên PMID/DOI, kiểm định công cụ, QC dữ liệu, phân tích đúng SAP",
     "Citation ledger, data dictionary, query log, lock memo, output đối chiếu với SAP."),
    ("Reproducibility",
     "Syntax tái lập, environment/package versions, raw-to-analysis provenance, fixed seed khi mô phỏng",
     "Script, session info/requirements, README tái chạy, hash artifact, không chỉnh tay kết quả."),
)

# Bảng kiểm hoàn thành kỹ thuật theo đặc tả "Codex hoàn thiện nghiên cứu y khoa":
# chỉ được ghi HOÀN THÀNH KỸ THUẬT khi không còn lỗi nghiêm trọng và mọi quyết
# định cần chủ nhiệm/IRB/thống kê viên đã có bằng chứng thật.
RESEARCH_COMPLETION_STEPS: Tuple[Tuple[str, str, str], ...] = (
    ("B1", "Tiếp nhận và khóa phạm vi",
     "Tên đề tài, mục tiêu, câu hỏi, giả thuyết, thiết kế đã khóa; không tự ý đổi."),
    ("B2", "Kiểm tra tính khả thi",
     "FINER, tuyển mẫu, đo lường, nhân lực/kinh phí/thời gian, nguy cơ IRB."),
    ("B3", "Kiểm tra câu hỏi và thiết kế",
     "PICO/PECO/PICOT, mục tiêu, giả thuyết, thiết kế, kết luận dự kiến nhất quán."),
    ("B4", "Hoàn thiện phương pháp",
     "Đối tượng, chọn mẫu, cỡ mẫu, biến số, công cụ, QC, dữ liệu thiếu, bảo mật."),
    ("B5", "Hoàn thiện phân tích thống kê",
     "SAP trước dữ liệu, mô tả/đơn biến/đa biến, giả định, nhiễu, 95% CI, ý nghĩa lâm sàng."),
    ("B6", "Kiểm tra đạo đức",
     "Nguy cơ-lợi ích, consent, rút lui, bảo mật, nhóm dễ tổn thương, COI, liêm chính."),
    ("B7", "Kiểm tra tính nhất quán",
     "Ma trận mục tiêu-câu hỏi-biến-công cụ-phân tích-bảng-kết luận; không vượt thiết kế."),
    ("B8", "Phản biện độc lập",
     "Ba phản biện: phương pháp, thống kê, lâm sàng/đạo đức; quyết định và sửa cụ thể."),
    ("B9", "Tạo bộ đầu ra hoàn chỉnh",
     "Bộ hồ sơ đủ để hội đồng khoa học/đạo đức, triển khai, phân tích, báo cáo, công bố."),
    ("B10", "Kiểm định cuối",
     "Chỉ HOÀN THÀNH KỸ THUẬT khi mọi lỗi nghiêm trọng đã xử lý hoặc được chủ nhiệm quyết định."),
)

RESEARCH_OUTPUT_PACKAGE_ITEMS: Tuple[str, ...] = (
    "Tóm tắt nghiên cứu",
    "Đề cương nghiên cứu hoàn chỉnh",
    "Thuyết minh nghiên cứu hoàn chỉnh",
    "Tổng quan tài liệu có trích dẫn",
    "Bảng biến số và định nghĩa hoạt động",
    "Phiếu thu thập số liệu/bảng hỏi",
    "Hướng dẫn sử dụng phiếu",
    "Kế hoạch phân tích thống kê",
    "Kế hoạch quản lý dữ liệu",
    "Hồ sơ đạo đức nghiên cứu",
    "Bảng kiểm báo cáo theo hướng dẫn phù hợp",
    "Báo cáo phản biện ba vai trò",
    "Danh mục vấn đề còn tồn tại",
    "Nhật ký thay đổi phiên bản",
    "Danh mục tài liệu tham khảo đã kiểm tra",
    "Bản cuối cùng sẵn sàng để nhà nghiên cứu thẩm định",
)

FINAL_TECHNICAL_CHECKS: Tuple[str, ...] = (
    "Mục tiêu đã được đo lường đầy đủ",
    "Thiết kế trả lời được câu hỏi nghiên cứu",
    "Cỡ mẫu có cơ sở",
    "Biến số có định nghĩa rõ ràng",
    "Phiếu thu thập số liệu đầy đủ",
    "Phân tích thống kê phù hợp",
    "Sai lệch và nhiễu được kiểm soát",
    "Không còn nguy cơ vi phạm đạo đức nghiêm trọng",
    "Tài liệu tham khảo xác thực",
    "Các tài liệu thống nhất với nhau",
    "Nghiên cứu có thể tái lập",
    "Kết luận không vượt quá dữ liệu/thiết kế",
)

FINAL_REPORT_SECTIONS: Tuple[str, ...] = (
    "Kết luận điều hành",
    "Trạng thái nghiên cứu",
    "Các nội dung đã đạt",
    "Các lỗi nghiêm trọng",
    "Các lỗi quan trọng",
    "Các đề xuất sửa đổi",
    "Bảng ma trận truy xuất",
    "Kế hoạch phân tích",
    "Đánh giá đạo đức",
    "Báo cáo phản biện",
    "Bảng kiểm cuối",
    "Danh sách tài liệu cần người dùng xác nhận",
    "Danh sách tệp đầu ra",
    "Nhật ký phiên bản",
)


def de_cuong_section_titles() -> List[str]:
    """Trả về danh sách 16 tiêu đề mục chính (dùng cho validator đối chiếu)."""
    return [f"{num}. {title}" for num, title, _ in DE_CUONG_SECTIONS]


# ════════════════════════════════════════════════════════════════════════════
# 3. MƯỜI CỔNG CHẤT LƯỢNG CỦA SKILL — G0..G9 (SKILL.md §Cổng chất lượng)
# ════════════════════════════════════════════════════════════════════════════

# LƯU Ý: đây là cổng theo cách đánh số của SKILL, KHÁC pipeline (xem bản đồ chéo).
# Mỗi mục: id -> (tên, điều kiện tối thiểu, sản phẩm bắt buộc).
SKILL_GATES: Dict[str, Tuple[str, str, str]] = {
    "G0": ("Ý tưởng", "Giá trị, khả thi, câu hỏi ban đầu",
           "Concept note + FINER"),
    "G1": ("Thiết kế", "Thiết kế phù hợp; chuẩn báo cáo xác định",
           "Design rationale + reporting map"),
    "G2": ("Protocol",
           "Mục tiêu, kết cục, cỡ mẫu, biến, phân tích định trước",
           "Protocol có phiên bản"),
    "G3": ("Đạo đức/pháp lý/dữ liệu",
           "Rủi ro-lợi ích, consent, bảo mật, thẩm quyền, đăng ký khi cần",
           "Hồ sơ đạo đức + data protection/registration plan"),
    "G4": ("Công cụ", "CRF/phiếu khảo sát/codebook/pilot phù hợp",
           "Bộ công cụ final + báo cáo pilot"),
    "G5": ("Triển khai", "SOP, đào tạo, giám sát và deviation log",
           "SOP + training/monitoring log"),
    "G6": ("Dữ liệu", "Làm sạch tái lập, query giải quyết, khóa dữ liệu",
           "Dataset phân tích + syntax + lock memo"),
    "G7": ("Phân tích", "Thực hiện theo SAP; deviation được giải trình",
           "Output + analysis report"),
    "G8": ("Báo cáo", "Báo cáo minh bạch đúng checklist",
           "Manuscript/report + checklist"),
    "G9": ("Công bố/ứng dụng",
           "Authorship, COI, AI/data disclosure, chuyển giao",
           "Submission/close-out package"),
}

# ────────────────────────────────────────────────────────────────────────────
# BẢN ĐỒ CHÉO: cổng pipeline (run_g*_auto.py) -> (các) cổng skill tương ứng.
# Một cổng pipeline có thể đóng góp cho nhiều cổng skill và ngược lại.
# ────────────────────────────────────────────────────────────────────────────
# QUAN TRỌNG (sửa sau kiểm định đối kháng): pipeline G5 chỉ sinh CÔNG CỤ (CRF/
# REDCap dictionary + script làm sạch) — docstring run_g5 ghi rõ "KHÔNG xử lý dữ
# liệu thật". Vì vậy pipeline G5 KHÔNG được map sang skill G6 (Dữ liệu = dataset
# đã KHOÁ + lock memo), chỉ map sang skill G4 (Công cụ) + skill G5 (Triển khai,
# ở mức script/SOP dự thảo). Skill G6 (Dữ liệu) và skill G7 (Phân tích) KHÔNG có
# cổng pipeline nào sinh bằng chứng THẬT — chúng chỉ KHOÁ qua tín hiệu thực-tế
# (real_world_signals: db_locked / results_final) do bác sĩ xác nhận.
PIPELINE_TO_SKILL_GATE: Dict[str, List[str]] = {
    "G0": ["G0"],              # PICO/FINER            -> Ý tưởng
    "G1": ["G1", "G2"],        # Thiết kế              -> Thiết kế + (nền Protocol)
    "G2": ["G3"],              # IRB/Đạo đức           -> Đạo đức/pháp lý
    "G3": ["G2"],              # Cỡ mẫu                -> Protocol (định trước)
    "G4": ["G2"],              # SAP                   -> Protocol (phân tích định trước)
    "G5": ["G4", "G5"],        # CRF/REDCap/scripts    -> Công cụ + Triển khai (KHÔNG Dữ liệu)
    "G6": ["G7"],              # Script phân tích      -> Phân tích (chuẩn bị, chưa có kết quả thật)
    "G7": ["G8"],              # Bản thảo IMRAD        -> Báo cáo
    "G8": ["G8", "G9"],        # Presubmission/peer    -> Báo cáo + (nền Công bố)
    "G9": ["G9"],             # Liêm chính tác giả    -> Công bố
}

# Chiều ngược: cổng skill -> các cổng pipeline cấp bằng chứng cho nó.
SKILL_TO_PIPELINE_GATE: Dict[str, List[str]] = {}
for _pg, _sgs in PIPELINE_TO_SKILL_GATE.items():
    for _sg in _sgs:
        SKILL_TO_PIPELINE_GATE.setdefault(_sg, []).append(_pg)


# Sáu CỔNG CỨNG của vòng đời nghiên cứu: không được tự vượt. Danh sách này
# phải khớp gate_contract.py; G5 là cổng khóa dữ liệu thật và G10 là capstone.
PIPELINE_HARD_GATES = {
    "G2": "Đạo đức IRB — cần số phê duyệt thật từ Hội đồng Đạo đức",
    "G4": "Khoá SAP — cần chữ ký SAP Lock Certificate",
    "G5": "Dữ liệu thật — phải làm sạch, giải quyết query và khóa trước phân tích chính",
    "G8": "Bình duyệt độc lập — cần người phản biện độc lập phê duyệt đúng vai trò",
    "G9": (
        "Liêm chính tác giả — cần xác nhận từng tác giả, quyền truy cập dữ liệu "
        "ICMJE 1/2026 và PI ký liêm chính"
    ),
    "G10": "Khóa gói phát hành — cần PI rà và ký đúng manifest cuối",
}


# ════════════════════════════════════════════════════════════════════════════
# 4. BẢN ĐỒ CHUẨN BÁO CÁO theo mã thiết kế (references/02_ban_do_chuan_bao_cao.md)
# ════════════════════════════════════════════════════════════════════════════

# design_code (dùng trong pipeline) -> dict{primary, protocol, extra}
REPORTING_STANDARDS: Dict[str, Dict[str, str]] = {
    "cross_sectional": {
        "primary": "STROBE",
        "protocol": "Protocol định trước; đăng ký nếu cần minh bạch",
        "extra": "CROSS (nếu là khảo sát); COSMIN nếu phát triển/thẩm định thang đo; "
                 "RECORD nếu dùng dữ liệu bệnh án/HIS/EMR; ROBINS-E tuỳ câu hỏi",
    },
    "case_control": {
        "primary": "STROBE",
        "protocol": "Protocol định trước",
        "extra": "ROBINS-I/ROBINS-E tuỳ câu hỏi và bản hiện hành",
    },
    "cohort": {
        "primary": "STROBE",
        "protocol": "Protocol định trước; đăng ký nếu cần minh bạch",
        "extra": "ROBINS-I/ROBINS-E; RECORD nếu dùng registry/EMR",
    },
    "rct": {
        "primary": "CONSORT 2025",
        "protocol": "SPIRIT 2025; đăng ký trial TRƯỚC tuyển mẫu; ICH-GCP nếu áp dụng",
        "extra": "TIDieR cho mô tả can thiệp; báo cáo harms; extension pragmatic/"
                 "pilot/cluster/AI nếu phù hợp",
    },
    "non_randomized": {
        "primary": "TREND hoặc STROBE (nếu quan sát)",
        "protocol": "Protocol định trước",
        "extra": "ROBINS-I; mô tả can thiệp",
    },
    "diagnostic": {
        "primary": "STARD",
        "protocol": "Protocol định trước/đăng ký nếu thích hợp",
        "extra": "QUADAS-2/QUADAS-C khi thẩm định sai lệch",
    },
    "prediction": {
        "primary": "TRIPOD+AI",
        "protocol": "Protocol + SAP; đăng ký nếu phù hợp",
        "extra": "PROBAST+AI; calibration, discrimination, clinical utility",
    },
    "systematic_review": {
        "primary": "PRISMA 2020",
        "protocol": "PRISMA-P; đăng ký PROSPERO/OSF nếu phù hợp",
        "extra": "RoB 2/ROBINS-I/QUADAS-2/AMSTAR 2/ROBIS; GRADE cho độ chắc chắn",
    },
    "qualitative": {
        "primary": "COREQ (phỏng vấn/focus group) hoặc SRQR",
        "protocol": "Protocol/reflexivity plan",
        "extra": "Audit trail, reflexivity, saturation/information power",
    },
    "mixed_methods": {
        "primary": "Chuẩn từng nhánh + hướng dẫn mixed-method",
        "protocol": "Protocol tích hợp",
        "extra": "Integration/joint display",
    },
    "quality_improvement": {
        "primary": "SQUIRE 2.0",
        "protocol": "Charter/PDSA/logic model",
        "extra": "Run/SPC charts, context, sustainability",
    },
    "economic": {
        "primary": "CHEERS 2022",
        "protocol": "Health economic analysis plan",
        "extra": "Perspective, costing, uncertainty, model validation",
    },
    "case_report": {
        "primary": "CARE",
        "protocol": "Consent xuất bản",
        "extra": "Bảo mật hình ảnh/thông tin",
    },
}


# Bí danh mã thiết kế: pipeline (run_g1/g3/g7) phát vài mã KHÁC key canon —
# chuẩn hoá về key canon để không mất chuẩn báo cáo (sửa #5/#12: 'sr_ma' -> PRISMA).
DESIGN_CODE_ALIASES: Dict[str, str] = {
    "sr_ma": "systematic_review",
    "sr": "systematic_review",
    "meta_analysis": "systematic_review",
    "metaanalysis": "systematic_review",
    "rct_parallel": "rct",
    "rct_crossover": "rct",
    "randomized": "rct",
    "case_control_study": "case_control",
    "cross_sectional_descriptive": "cross_sectional",
    "prevalence": "cross_sectional",
    "prognostic": "prediction",
    "prediction_model": "prediction",
    "diagnostic_accuracy": "diagnostic",
    "qual": "qualitative",
    "mixed": "mixed_methods",
    "qi": "quality_improvement",
}


def canonical_design_code(design_code: Optional[str]) -> Optional[str]:
    """Chuẩn hoá mã thiết kế về key canon (áp bí danh, lowercase)."""
    if not design_code:
        return None
    key = str(design_code).strip().lower()
    return DESIGN_CODE_ALIASES.get(key, key)


def reporting_standards_for(design_code: Optional[str]) -> Dict[str, str]:
    """Trả về gói chuẩn báo cáo cho 1 mã thiết kế (đã chuẩn hoá bí danh).

    Nếu mã thiết kế chưa có trong bản đồ, trả về mục nhắc tra EQUATOR + cờ
    [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] (không tự bịa chuẩn).
    """
    code = canonical_design_code(design_code)
    if code and code in REPORTING_STANDARDS:
        return REPORTING_STANDARDS[code]
    return {
        "primary": f"{TAG_CAN_KIEM_CHUNG_NGUON} — tra EQUATOR Network theo thiết kế thật",
        "protocol": "Protocol định trước",
        "extra": "Chọn checklist theo THIẾT KẾ THẬT, không theo tên đề tài",
    }


# ════════════════════════════════════════════════════════════════════════════
# 5. QUY TẮC KẾT LUẬN "SẴN SÀNG" (SKILL.md §Kết luận trạng thái)
# ════════════════════════════════════════════════════════════════════════════

# Mỗi mốc: (nhãn, các cổng skill cần có ≥ dự thảo, các TÍN HIỆU THỰC-TẾ bắt
# buộc bật, điều kiện thêm).
#
# Phân biệt cốt lõi (làm lại sau kiểm định đối kháng #4/#6/#10/#11):
#   - "Sẵn sàng document" (nộp đạo đức): chỉ cần hồ sơ DỰ THẢO đầy đủ. hard_signals rỗng.
#   - "Sẵn sàng evidence" (triển khai/phân tích/công bố): BẮT BUỘC có TÍN HIỆU
#     THỰC-TẾ (real_world_signals) tương ứng bật — KHÔNG suy từ artifact. Đặc biệt
#     mốc phân tích chính cần CẢ sap_locked LẪN db_locked (khớp SKILL.md "đạt G6
#     VÀ SAP đã chốt"); mốc công bố cần results_final (kết quả thật) + integrity.
READINESS_MILESTONES: List[Tuple[str, List[str], List[str], str]] = [
    ("Sẵn sàng nộp Hội đồng đạo đức",
     ["G0", "G1", "G2", "G3"], [],
     "Hồ sơ đạo đức + protocol ở dạng dự thảo đầy đủ; bác sĩ điền nốt rồi nộp XIN phê duyệt"),
    ("Sẵn sàng triển khai (thu thập dữ liệu)",
     ["G0", "G1", "G2", "G3", "G4", "G5"], ["irb_approved"],
     "BẮT BUỘC có phê duyệt Hội đồng Đạo đức THẬT (tín hiệu irb_approved) + công cụ/SOP dự thảo đầy đủ"),
    ("Sẵn sàng phân tích chính",
     ["G6"], ["sap_locked", "db_locked"],
     "BẮT BUỘC SAP đã ký khoá (sap_locked) VÀ dữ liệu đã khoá thật (db_locked) — khớp SKILL.md §Kết luận"),
    ("Sẵn sàng nộp công bố/nghiệm thu",
     ["G7", "G8", "G9"],
     ["results_final", "peer_review_approved", "integrity_signed"],
     "BẮT BUỘC có kết quả phân tích THẬT, bình duyệt độc lập đúng vai trò và gói liêm chính đã ký"),
]


# ════════════════════════════════════════════════════════════════════════════
# 6. THAM CHIẾU PHÁP LÝ/ĐẠO ĐỨC (references/00 + 01) — kèm cờ kiểm chứng
# ════════════════════════════════════════════════════════════════════════════

# Các mốc pháp lý/tiêu chuẩn skill đã dẫn. NGÀY tự skill ghi; khi dùng để KẾT
# LUẬN phải kiểm nguồn chính thức lại (Quy tắc 7). Giữ cờ để không quên.
LEGAL_ETHICS_REFS: List[Dict[str, str]] = [
    {"ten": "Tuyên ngôn Helsinki (World Medical Association)",
     "phien_ban": "2024", "linh_vuc": "Đạo đức nghiên cứu y sinh trên người",
     "co": TAG_CAN_KIEM_CHUNG_NGUON},
    {"ten": "ICH E6(R3) Good Clinical Practice",
     "phien_ban": "2025", "linh_vuc": "Thực hành lâm sàng tốt (thử nghiệm)",
     "co": TAG_CAN_KIEM_CHUNG_NGUON},
    {"ten": "ICMJE Recommendations",
     "phien_ban": "01/2026", "linh_vuc": "Tác giả, COI, khai báo AI, công bố",
     "co": TAG_CAN_KIEM_CHUNG_NGUON},
    {"ten": "Luật Bảo vệ dữ liệu cá nhân (Quốc hội Việt Nam)",
     "phien_ban": "91/2025/QH15 (hiệu lực 01/01/2026)",
     "linh_vuc": "Bảo mật dữ liệu cá nhân", "co": TAG_CAN_KIEM_CHUNG_NGUON},
    {"ten": "Luật Khám bệnh, chữa bệnh (Quốc hội Việt Nam)",
     "phien_ban": "15/2023/QH15", "linh_vuc": "Khám chữa bệnh",
     "co": TAG_CAN_KIEM_CHUNG_NGUON},
    {"ten": "Thông tư Bộ Y tế về nghiên cứu y sinh học",
     "phien_ban": "43/2024/TT-BYT (hiệu lực 01/02/2025, Điều 22)",
     "linh_vuc": "Đạo đức nghiên cứu y sinh tại Việt Nam",
     "co": TAG_CAN_KIEM_CHUNG_NGUON},
]


# ════════════════════════════════════════════════════════════════════════════
# 7. CHUẨN HOÁ TRẠNG THÁI CỔNG PIPELINE TỪ CHECKPOINT
# ════════════════════════════════════════════════════════════════════════════

# Bốn trạng thái chuẩn hoá cho 1 cổng pipeline (đọc từ checkpoint JSON).
GATE_STATE_LOCKED = "KHOÁ"          # có phê duyệt/chữ ký/dữ liệu thật
GATE_STATE_DRAFT = "DỰ THẢO (ĐẠT guardrail)"  # artifact tạo tự động + guardrail PASS
GATE_STATE_PENDING = "CHỜ (thiếu điều kiện)"  # bị chặn, chờ thượng nguồn
GATE_STATE_MISSING = "THIẾU"        # chưa có checkpoint


def _status_str_passes(s: str) -> bool:
    """Chuỗi trạng thái có nghĩa PASS không (✅ PASS / [OK] PASS / PASS)."""
    up = s.upper()
    return ("PASS" in up) or ("✅" in s) or ("[OK]" in up)


def _guardrail_passed(cp: Dict) -> bool:
    """Đọc trường guardrail ĐA DẠNG một cách an toàn.

    Các cổng lưu guardrail theo nhiều hình dạng khác nhau (đã kiểm bằng
    checkpoint thật):
      - {"passed": true, ...}                     (G0, G1, G2, G8, G9)
      - {"status": "✅ PASS", "errors": []}       (G7 — KHÔNG có key 'passed')
      - "✅ PASS" / "[OK] PASS" (chuỗi thẳng)      (G3, G4, G5, G6)
    Hàm này chấp nhận cả 3 để không âm thầm coi G7 là 'chưa đạt'.
    """
    g = cp.get("guardrail")
    if isinstance(g, dict):
        if "passed" in g:
            return bool(g.get("passed"))
        status = g.get("status")
        if isinstance(status, str):
            return _status_str_passes(status)
        return False
    if isinstance(g, str):
        return _status_str_passes(g)
    return False


# ── Nhận diện giá trị THẬT vs placeholder/nhãn/phủ định ─────────────────────
_PLACEHOLDER_TOKENS = (
    "[CẦN", "CẦN ", "TBD", "N/A", "NONE", "NULL", "PENDING", "CHƯA",
    "UNLOCK", "NOT LOCK", "DỰ THẢO", "DRAFT", "PLACEHOLDER", "XXX", "...",
    "CHỜ", "ĐANG", "SẼ",
)


def _is_real_value(v) -> bool:
    """True nếu v là GIÁ TRỊ THẬT — không rỗng/None/placeholder/nhãn skill/phủ định.

    Chặn kiểu 'g2_irb_number = "[CẦN BỔ SUNG]"' hay '"TBD"' bị coi là đã có IRB.
    """
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip()
    if not s:
        return False
    up = s.upper()
    return not any(tok in up for tok in _PLACEHOLDER_TOKENS)


def _status_is_locked(status: Optional[str]) -> bool:
    """True nếu chuỗi trạng thái CÓ token 'LOCKED' đứng riêng và KHÔNG bị phủ định.

    Sửa bug substring (kiểm định đối kháng #7): 'UNLOCKED'/'NOT LOCKED'/'CHƯA
    LOCKED'/'PENDING ... LOCKED' KHÔNG được coi là đã khoá. Dùng ranh giới từ.
    """
    if not status:
        return False
    up = str(status).upper()
    if any(neg in up for neg in ("UNLOCK", "NOT LOCK", "CHƯA", "PENDING", "SẼ ")):
        return False
    return re.search(r"\bLOCKED\b", up) is not None


# ── Tín hiệu THỰC-TẾ (real-world) — nền tảng của mọi kết luận 'KHOÁ' ─────────
# Tách bạch "artifact đã tạo (guardrail PASS)" với "SỰ KIỆN THẬT đã xảy ra".
# Cổng chỉ được coi KHOÁ khi có tín hiệu thực-tế tương ứng, KHÔNG suy từ việc
# artifact tồn tại. Nguồn tín hiệu: trường bằng chứng có cấu trúc + guardrail
# của chính cổng, HOẶC study_meta.json do bác sĩ xác nhận.
def real_world_signals(checkpoints: Dict[str, Dict],
                       meta: Optional[Dict] = None) -> Dict[str, bool]:
    """Trả các tín hiệu đời thực; artifact/checkpoint đơn thuần không đủ."""
    meta = meta or {}
    g2 = checkpoints.get("G2") or {}
    g4 = checkpoints.get("G4") or {}
    g5 = checkpoints.get("G5") or {}
    g8 = checkpoints.get("G8") or {}
    g9 = checkpoints.get("G9") or {}
    g10 = checkpoints.get("G10") or {}

    if g2.get("quality_contract_version"):
        quality = g2.get("quality_gate")
        irb = (
            isinstance(quality, dict)
            and quality.get("status") == "PASS_G2_APPROVED"
        )
    else:
        irb = (
            _guardrail_passed(g2)
            and _is_real_value(g2.get("g2_irb_number"))
            and _is_real_value(g2.get("g2_approval_date"))
        ) or bool(meta.get("irb_approved"))

    # SỬA 2026-07-29 (audit toàn diện G0-G10, F6): trước đây tín hiệu "SAP đã
    # khóa" chỉ đọc g4_lock_date/g4_status — cả hai đều KHÔNG được approve_gate.py
    # cập nhật khi ký thật (chỉ g4_quality_gate.py mới ghi g4_lock_date, xem
    # refresh_checkpoint() của module đó) — nên một G4 đã ký hợp lệ vẫn báo "chưa
    # khóa" ở đây. Mirror đúng nhánh G5/G9: có quality_contract_version thì chấm
    # TRỰC TIẾP (bắt lại drift số liệu với G3 hiện tại), không tin field cũ.
    if g4.get("quality_contract_version"):
        study = str(g4.get("study") or "").strip()
        if study and re.fullmatch(r"[\w-]+", study):
            root = Path(__file__).resolve().parents[1]
            default_out = root / "exports" / study
            if default_out.exists():
                try:
                    import g4_quality_gate as G4Q  # noqa: PLC0415

                    live = G4Q.evaluate_study(
                        study,
                        default_out,
                        repo_root=root,
                        write=False,
                    )
                    sap = live.get("status") == G4Q.STATUS_LOCKED
                except (ImportError, OSError, RuntimeError, ValueError):
                    sap = False
            else:
                # Audit/verifier có thể chạy trong TemporaryDirectory; ở đó caller
                # vừa chấm G4 và pin trạng thái vào meta của chính fixture.
                sap = meta.get("g4_quality_status") == "PASS_G4_SAP_LOCKED"
        else:
            sap = meta.get("g4_quality_status") == "PASS_G4_SAP_LOCKED"
    else:
        sap = (
            _guardrail_passed(g4)
            and (_is_real_value(g4.get("g4_lock_date"))
                 or _status_is_locked(g4.get("g4_status")))
        ) or _is_real_value(meta.get("sap_lock_date"))

    if g5.get("quality_contract_version"):
        study = str(g5.get("study") or "").strip()
        if study and re.fullmatch(r"[\w-]+", study):
            root = Path(__file__).resolve().parents[1]
            default_out = root / "exports" / study
            if default_out.exists():
                try:
                    import g5_quality_gate as G5Q  # noqa: PLC0415

                    live = G5Q.evaluate_study(
                        study,
                        default_out,
                        repo_root=root,
                        write=False,
                    )
                    db = live.get("status") == G5Q.STATUS_LOCKED
                except (ImportError, OSError, RuntimeError, ValueError):
                    db = False
            else:
                # Audit/verifier có thể chạy trong TemporaryDirectory; ở đó
                # caller vừa chấm G5 và pin trạng thái vào meta của chính fixture.
                db = (
                    meta.get("g5_quality_status") == "PASS_G5_DATA_LOCKED"
                    and _is_real_value(meta.get("data_lock_date"))
                )
        else:
            # Checkpoint fixture/legacy không có study: giữ đường tương thích,
            # còn pipeline thật luôn ghi study và phải chấm trực tiếp từ artifact.
            db = (
                meta.get("g5_quality_status") == "PASS_G5_DATA_LOCKED"
                and _is_real_value(meta.get("data_lock_date"))
            )
    else:
        db = _status_is_locked(g5.get("database_lock_status")) \
            or _is_real_value(meta.get("data_lock_date"))

    # Kết quả phân tích thật KHÔNG do pipeline sinh — chỉ bác sĩ xác nhận.
    results = bool(meta.get("results_final"))

    peer = (
        _guardrail_passed(g8)
        and g8.get("independent_peer_review_approved") is True
        and _is_real_value(g8.get("peer_review_approval_date"))
    ) or bool(meta.get("peer_review_approved"))

    if g9.get("quality_contract_version"):
        study = str(g9.get("study") or "").strip()
        if study and re.fullmatch(r"[\w-]+", study):
            root = Path(__file__).resolve().parents[1]
            default_out = root / "exports" / study
            if default_out.exists():
                try:
                    import g9_quality_gate as G9Q  # noqa: PLC0415

                    live = G9Q.evaluate_study(
                        study,
                        default_out,
                        repo_root=root,
                        write=False,
                    )
                    integ = live.get("status") == G9Q.STATUS_LOCKED
                except (ImportError, OSError, RuntimeError, ValueError):
                    integ = False
            else:
                integ = (
                    meta.get("g9_quality_status")
                    == "PASS_G9_PUBLICATION_INTEGRITY_LOCKED"
                )
        else:
            integ = (
                meta.get("g9_quality_status")
                == "PASS_G9_PUBLICATION_INTEGRITY_LOCKED"
            )
    else:
        integ = (
            g9.get("submission_package_ready") is True and _guardrail_passed(g9)
        ) or bool(meta.get("integrity_signed"))

    if g10.get("quality_contract_version"):
        study = str(g10.get("study") or "").strip()
        if study and re.fullmatch(r"[\w-]+", study):
            root = Path(__file__).resolve().parents[1]
            default_out = root / "exports" / study
            if default_out.exists():
                try:
                    import g10_quality_gate as G10Q  # noqa: PLC0415

                    live = G10Q.evaluate_study(
                        study,
                        default_out,
                        repo_root=root,
                        write=False,
                    )
                    release = live.get("status") == G10Q.STATUS_LOCKED
                except (ImportError, OSError, RuntimeError, ValueError):
                    release = False
            else:
                release = (
                    meta.get("g10_quality_status")
                    == "PASS_G10_RELEASE_PACKAGE_LOCKED"
                )
        else:
            release = (
                meta.get("g10_quality_status")
                == "PASS_G10_RELEASE_PACKAGE_LOCKED"
            )
    else:
        release = (
            g10.get("release_package_locked") is True
            and _guardrail_passed(g10)
        ) or bool(meta.get("g10_release_locked"))

    return {"irb_approved": irb, "sap_locked": sap, "db_locked": db,
            "results_final": results, "peer_review_approved": peer,
            "integrity_signed": integ, "release_locked": release}


def normalize_pipeline_gate_state(pipeline_gate: str, cp: Optional[Dict],
                                  meta: Optional[Dict] = None) -> str:
    """Suy trạng thái ARTIFACT của 1 cổng pipeline (DRAFT/PENDING/MISSING).

    LƯU Ý sau kiểm định đối kháng: hàm này KHÔNG còn tự kết luận KHOÁ từ việc 1
    trường non-empty (bug #8) hay substring 'LOCKED' (bug #7). 'KHOÁ' là khái
    niệm THỰC-TẾ, do real_world_signals() + skill_gate_state() quyết định. Ở đây
    chỉ phản ánh: artifact đã tạo + guardrail PASS -> DỰ THẢO; chưa -> CHỜ; không
    có checkpoint -> THIẾU. Nhưng nếu tín hiệu thực-tế của cổng cứng đã bật thì
    nâng lên KHOÁ (để bảng trạng thái phản ánh đúng khi bác sĩ đã cấp bằng chứng).
    """
    if not cp:
        return GATE_STATE_MISSING

    # Với cổng cứng, kiểm tín hiệu thực-tế của CHÍNH nó (dựng cps 1-phần tử).
    sig = real_world_signals({pipeline_gate: cp}, meta)
    if pipeline_gate == "G2" and sig["irb_approved"]:
        return GATE_STATE_LOCKED
    if pipeline_gate == "G4" and sig["sap_locked"]:
        return GATE_STATE_LOCKED
    if pipeline_gate == "G5" and sig["db_locked"]:
        return GATE_STATE_LOCKED
    if pipeline_gate == "G8" and sig["peer_review_approved"]:
        return GATE_STATE_LOCKED
    if pipeline_gate == "G9" and sig["integrity_signed"]:
        return GATE_STATE_LOCKED
    if pipeline_gate == "G10" and sig["release_locked"]:
        return GATE_STATE_LOCKED

    return GATE_STATE_DRAFT if _guardrail_passed(cp) else GATE_STATE_PENDING


# Cổng SKILL nào KHOÁ được nhờ tín hiệu THỰC-TẾ nào (số còn lại tối đa DỰ THẢO).
# skill G6 (Dữ liệu) & G7 (Phân tích) KHÔNG có cổng pipeline nào sinh bằng chứng
# thật -> chỉ khoá qua tín hiệu do bác sĩ xác nhận (sửa dead-end #11).
SKILL_GATE_LOCK_SIGNAL: Dict[str, str] = {
    "G2": "sap_locked",       # Protocol chốt khi SAP đã ký (thiết kế/cỡ mẫu đã có)
    "G3": "irb_approved",     # Đạo đức
    "G6": "db_locked",        # Dữ liệu đã khoá thật
    "G7": "results_final",    # Phân tích có kết quả thật
    "G8": "peer_review_approved",  # Báo cáo đã được bình duyệt độc lập
    "G9": "integrity_signed", # Công bố: gói liêm chính đã ký
}


def skill_gate_state(skill_gate: str, checkpoints: Dict[str, Dict],
                     meta: Optional[Dict] = None) -> str:
    """Suy trạng thái 1 cổng SKILL.

    Hai tầng (sửa sau kiểm định đối kháng):
      1) KHOÁ chỉ khi TÍN HIỆU THỰC-TẾ tương ứng bật (SKILL_GATE_LOCK_SIGNAL) —
         không suy KHOÁ từ việc artifact tồn tại.
      2) Chưa khoá thì lấy trạng thái ARTIFACT gộp từ cổng pipeline nguồn:
         THIẾU nếu mọi nguồn thiếu; CHỜ nếu có nguồn chờ/thiếu; ngược lại DỰ THẢO.
    """
    signals = real_world_signals(checkpoints, meta)
    sig_key = SKILL_GATE_LOCK_SIGNAL.get(skill_gate)
    if sig_key and signals.get(sig_key):
        return GATE_STATE_LOCKED

    sources = SKILL_TO_PIPELINE_GATE.get(skill_gate, [])
    if not sources:
        # Cổng skill không có nguồn pipeline (vd G6 Dữ liệu): THIẾU cho tới khi
        # có tín hiệu thực-tế (đã xử ở tầng 1).
        return GATE_STATE_MISSING
    states = [
        normalize_pipeline_gate_state(pg, checkpoints.get(pg), meta)
        for pg in sources
    ]
    if all(s == GATE_STATE_MISSING for s in states):
        return GATE_STATE_MISSING
    if any(s in (GATE_STATE_PENDING, GATE_STATE_MISSING) for s in states):
        return GATE_STATE_PENDING
    return GATE_STATE_DRAFT


def readiness_report(checkpoints: Dict[str, Dict],
                     meta: Optional[Dict] = None) -> List[Dict[str, str]]:
    """Đánh giá 4 mốc 'sẵn sàng' — cổng mềm (dự thảo) + TÍN HIỆU THỰC-TẾ (cứng).

    Trả list dict{moc, dat, chi_tiet}. 'dat' ∈ {'ĐẠT (khoá...)', 'ĐẠT (dự
    thảo...)', 'CHƯA ĐẠT'}. Điều kiện cứng dựa TRỰC TIẾP trên real_world_signals
    (irb_approved/sap_locked/db_locked/results_final/integrity_signed), không suy
    từ artifact — nên không thể báo 'đạt' khi chưa có sự kiện thật.
    """
    signals = real_world_signals(checkpoints, meta)
    skill_states = {
        sg: skill_gate_state(sg, checkpoints, meta) for sg in SKILL_GATES
    }
    sig_label = {
        "irb_approved": "phê duyệt IRB thật",
        "sap_locked": "SAP đã ký khoá",
        "db_locked": "dữ liệu đã khoá thật",
        "results_final": "kết quả phân tích thật (bác sĩ xác nhận)",
        "peer_review_approved": "bình duyệt độc lập đã phê duyệt đúng vai trò",
        "integrity_signed": "gói liêm chính đã ký",
    }
    out: List[Dict[str, str]] = []
    for label, need_gates, hard_signals, extra in READINESS_MILESTONES:
        states = [skill_states.get(g, GATE_STATE_MISSING) for g in need_gates]
        hard_ok = all(signals.get(s) for s in hard_signals)
        soft_ok = all(s in (GATE_STATE_LOCKED, GATE_STATE_DRAFT) for s in states)
        if hard_signals and hard_ok and all(
                s == GATE_STATE_LOCKED for s in states):
            dat = "ĐẠT (khoá — có bằng chứng thật)"
        elif hard_ok and soft_ok:
            dat = ("ĐẠT (dự thảo — chờ bác sĩ điền/nộp)" if not hard_signals
                   else "ĐẠT (đủ điều kiện thật)")
        else:
            dat = "CHƯA ĐẠT"
        blockers: List[str] = []
        for s in hard_signals:
            if not signals.get(s):
                blockers.append(f"thiếu {sig_label.get(s, s)}")
        for g, st in zip(need_gates, states):
            if st in (GATE_STATE_PENDING, GATE_STATE_MISSING):
                blockers.append(f"cổng skill {g} ({SKILL_GATES[g][0]}): {st}")
        detail = extra
        if blockers:
            detail += " | Chặn bởi: " + "; ".join(blockers)
        out.append({"moc": label, "dat": dat, "chi_tiet": detail})
    return out


if __name__ == "__main__":
    # Tự kiểm nhanh: in tóm tắt canon để mắt thường soát.
    print("=== skill_standards.py — tự kiểm ===")
    print(f"Số nhãn trạng thái hợp lệ: {len(VALID_STATUS_TAGS)}")
    print(f"Số mục đề cương: {len(DE_CUONG_SECTIONS)} (cần = 16)")
    print(f"Số cổng skill: {len(SKILL_GATES)} (cần = 10)")
    print(f"Số mã thiết kế có chuẩn báo cáo: {len(REPORTING_STANDARDS)}")
    print(f"Số mốc sẵn sàng: {len(READINESS_MILESTONES)}")
    print(f"Số tham chiếu pháp lý: {len(LEGAL_ETHICS_REFS)}")
    print("Bản đồ chéo pipeline->skill:")
    for pg, sgs in PIPELINE_TO_SKILL_GATE.items():
        print(f"  pipeline {pg} -> skill {', '.join(sgs)}")
