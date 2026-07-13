#!/usr/bin/env python3
"""Nguồn sự thật (canon) của skill `nghien-cuu-y-khoa-chuan-quoc-te`.

Module này mã hoá các chuẩn của skill để CHUỖI cổng tự động (run_g*_auto.py)
tuân thủ ĐÚNG mẫu/checklist của skill một cách tự động, thay vì để Claude tự
đối chiếu thủ công mỗi lần. Bao gồm:

- 5 NHÃN TRẠNG THÁI bắt buộc khi soạn hồ sơ.
- Mẫu ĐỀ CƯƠNG 16 mục (templates/01_mau_de_cuong_tong_the.md).
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
from typing import Dict, List, Optional, Tuple

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


# Ba CỔNG CỨNG của pipeline (CLAUDE.md): không được tự vượt.
PIPELINE_HARD_GATES = {
    "G2": "Đạo đức IRB — cần số phê duyệt thật từ Hội đồng Đạo đức",
    "G4": "Khoá SAP — cần chữ ký SAP Lock Certificate",
    "G9": "Liêm chính tác giả — cần tất cả tác giả ký ICMJE + PI ký liêm chính",
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
     ["G7", "G8", "G9"], ["results_final", "integrity_signed"],
     "BẮT BUỘC có kết quả phân tích THẬT (results_final, bác sĩ xác nhận) + gói liêm chính đã ký (integrity_signed)"),
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
    """Trả dict{irb_approved, sap_locked, db_locked, results_final, integrity_signed}."""
    meta = meta or {}
    g2 = checkpoints.get("G2") or {}
    g4 = checkpoints.get("G4") or {}
    g5 = checkpoints.get("G5") or {}
    g9 = checkpoints.get("G9") or {}

    irb = (
        _guardrail_passed(g2)
        and _is_real_value(g2.get("g2_irb_number"))
        and _is_real_value(g2.get("g2_approval_date"))
    ) or bool(meta.get("irb_approved"))

    sap = (
        _guardrail_passed(g4)
        and (_is_real_value(g4.get("g4_lock_date"))
             or _status_is_locked(g4.get("g4_status")))
    ) or _is_real_value(meta.get("sap_lock_date"))

    db = _status_is_locked(g5.get("database_lock_status")) \
        or _is_real_value(meta.get("data_lock_date"))

    # Kết quả phân tích thật KHÔNG do pipeline sinh — chỉ bác sĩ xác nhận.
    results = bool(meta.get("results_final"))

    integ = (
        g9.get("submission_package_ready") is True and _guardrail_passed(g9)
    ) or bool(meta.get("integrity_signed"))

    return {"irb_approved": irb, "sap_locked": sap, "db_locked": db,
            "results_final": results, "integrity_signed": integ}


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
    if pipeline_gate == "G9" and sig["integrity_signed"]:
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
