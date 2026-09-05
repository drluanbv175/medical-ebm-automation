"""Checklist hồ sơ hội đồng đạo đức + nghiệm thu, và gợi ý biến số/thống kê.

Tất cả là KHUNG GỢI Ý theo chuẩn báo cáo (STROBE/CONSORT/SPIRIT) + thực hành thường
quy. KHÔNG tự tạo số liệu/kết quả; chỉ đề xuất khung để người nghiên cứu điền.
"""
from __future__ import annotations

from typing import Dict, List

# --- Checklist hồ sơ nộp hội đồng đạo đức -------------------------------------
ETHICS_SUBMISSION_CHECKLIST: List[str] = [
    "Đơn xin xét duyệt đạo đức (theo mẫu hội đồng)",
    "Đề cương nghiên cứu đầy đủ (protocol) có phiên bản & ngày",
    "Thuyết minh đề tài / bản tóm tắt",
    "Phiếu thông tin và bản đồng thuận tham gia (ICF) cho người tham gia",
    "Bộ công cụ thu thập (phiếu khảo sát / CRF / bảng câu hỏi)",
    "Lý lịch khoa học nghiên cứu viên chính (CV/biosketch)",
    "Cam kết tuân thủ đạo đức nghiên cứu & xung đột lợi ích (COI)",
    "Kế hoạch quản lý & bảo mật dữ liệu (data management & privacy)",
    "Tính cỡ mẫu và cơ sở thống kê (kèm giả định)",
    "Nguồn kinh phí & phê duyệt đơn vị chủ trì",
    "Đăng ký nghiên cứu (nếu thử nghiệm lâm sàng: ClinicalTrials.gov/registry)",
    "Phê duyệt sử dụng dữ liệu/bệnh án (nếu hồi cứu)",
]

# --- Checklist nghiệm thu -------------------------------------------------------
ACCEPTANCE_CHECKLIST: List[str] = [
    "Báo cáo toàn văn theo cấu trúc IMRAD",
    "Bộ số liệu thô + bộ số liệu đã làm sạch (có nhật ký làm sạch)",
    "Kế hoạch/biên bản phân tích thống kê (SAP) và kết quả tái lập được",
    "Minh chứng đạt mục tiêu nghiên cứu (primary/secondary outcomes)",
    "Sản phẩm khoa học: bản thảo bài báo / báo cáo hội nghị (nếu có)",
    "Biên bản nghiệm thu cấp cơ sở",
    "Đối chiếu với đề cương đã duyệt (sai khác & lý do)",
    "Tuyên bố COI, đóng góp tác giả, lời cảm ơn nguồn tài trợ",
    "Lưu trữ dữ liệu theo quy định (thời hạn, bảo mật)",
]

# --- Gợi ý phân tích thống kê theo thiết kế nghiên cứu --------------------------
# Khóa khớp lỏng theo từ trong study_design.
# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 16) — stats_suggestions()
# dừng ở match ĐẦU TIÊN theo THỨ TỰ KHAI BÁO dict. Một thiết kế "nested
# case-control" (bệnh-chứng lồng trong một cohort có sẵn — rất phổ biến
# trong dịch tễ học) chứa CẢ HAI từ khóa "cohort"/"thuần tập" LẪN
# "case-control"/"bệnh chứng". Khi "cohort" được khai báo TRƯỚC
# "case-control" trong dict, hàm trả nhầm gợi ý của cohort (RR/Cox/Kaplan-
# Meier) cho một thiết kế thực ra cần gợi ý của case-control (OR/hồi quy
# logistic/ghép cặp) — sai phương pháp thống kê được đề xuất cho một thiết
# kế dịch tễ phổ biến. Đặt thiết kế CỤ THỂ hơn (case-control, rct) TRƯỚC
# thiết kế TỔNG QUÁT hơn (cohort, cross-sectional) để khớp đúng ưu tiên.
_STATS_BY_DESIGN: Dict[str, List[str]] = {
    "case-control": [
        "Tỷ số chênh (OR) qua hồi quy logistic (đơn & đa biến).",
        "Kiểm soát nhiễu: ghép cặp (matching) và/hoặc hiệu chỉnh đa biến.",
        "Báo cáo theo STROBE (case-control).",
    ],
    "rct": [
        "Phân tích theo ý định điều trị (ITT) là chính; per-protocol là phụ.",
        "So sánh kết cục chính: t-test/Mann-Whitney hoặc Chi-square; ước lượng hiệu quả + KTC 95%.",
        "Điều chỉnh biến nền nếu phân tầng; phân tích sống còn nếu kết cục thời gian-đến-biến cố.",
        "Báo cáo theo CONSORT 2025; đăng ký thử nghiệm; tính ARR/RRR/NNT.",
    ],
    "cross-sectional": [
        "Mô tả: tần số/tỷ lệ (biến định tính), trung bình±SD hoặc trung vị (IQR) (định lượng).",
        "So sánh nhóm: Chi-square/Fisher (định tính); t-test/Mann-Whitney (2 nhóm); ANOVA/Kruskal-Wallis (≥3 nhóm).",
        "Liên quan: hồi quy logistic (kết cục nhị phân) ước tính OR; hồi quy tuyến tính (kết cục liên tục).",
        "Báo cáo theo STROBE (cross-sectional).",
    ],
    "cohort": [
        "Tỷ suất mới mắc/incidence; nguy cơ tương đối (RR) hoặc tỷ số nguy cơ.",
        "Phân tích sống còn: Kaplan-Meier + log-rank; hồi quy Cox (HR) cho thời gian đến biến cố.",
        "Kiểm soát nhiễu: hồi quy đa biến / điểm xu hướng (propensity score) nếu phù hợp.",
        "Báo cáo theo STROBE (cohort).",
    ],
    "descriptive": [
        "Thống kê mô tả: tần số/tỷ lệ, trung bình±SD, trung vị (IQR).",
        "Trình bày bảng/biểu đồ; khoảng tin cậy cho các ước lượng tỷ lệ.",
    ],
}


def stats_suggestions(study_design: str | None) -> List[str]:
    """Trả về gợi ý phân tích thống kê theo thiết kế (khớp lỏng)."""
    d = (study_design or "").lower()
    for key, items in _STATS_BY_DESIGN.items():
        token = key.replace("-", " ")
        if key in d or token in d or _vn_alias(key) in d:
            return items
    return _STATS_BY_DESIGN["descriptive"]


def _vn_alias(key: str) -> str:
    return {
        "cross-sectional": "cắt ngang", "cohort": "thuần tập",
        "case-control": "bệnh chứng", "rct": "thử nghiệm", "descriptive": "mô tả",
    }.get(key, "___")


def variable_framework() -> Dict[str, List[str]]:
    """Khung gợi ý phân loại biến số (người nghiên cứu điền cụ thể)."""
    return {
        "Biến độc lập / phơi nhiễm": ["(điền: yếu tố nguy cơ/can thiệp đang khảo sát)"],
        "Biến phụ thuộc / kết cục": ["(điền: kết cục chính & phụ, đơn vị đo, thời điểm đo)"],
        "Biến gây nhiễu (confounders)": ["Tuổi", "Giới", "Bệnh đồng mắc", "Thuốc đang dùng",
                                         "(bổ sung theo y văn nền)"],
        "Biến nền nhân khẩu học": ["Tuổi", "Giới", "BMI", "Nghề nghiệp", "Nơi ở"],
        "Loại biến & cách đo": ["Định tính (nhị phân/danh mục/thứ tự)",
                                "Định lượng (liên tục/rời rạc)",
                                "Ghi rõ định nghĩa thao tác & nguồn dữ liệu"],
    }
