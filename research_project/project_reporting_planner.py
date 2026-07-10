"""
project_reporting_planner — Checklist báo cáo theo chuẩn STROBE/CONSORT/STARD/PRISMA/COREQ (V4.3.3).

OFFLINE · KHÔNG PII / API. Mọi output là DRAFT.
"""

from __future__ import annotations

import dataclasses
from typing import List

from .project_config import (
    DISCLAIMER,
    REPORTING_STANDARD,
    REQUIRE_HUMAN_INPUT_MARKER,
    StudyType,
)


@dataclasses.dataclass
class ReportingItem:
    item_no: str
    description: str
    location: str   # "REQUIRE_HUMAN_INPUT" cho đến khi PI điền

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ReportingChecklist:
    standard: str
    study_type: str
    items: List[ReportingItem]
    total_items: int
    completed_count: int   # luôn = 0 cho draft

    def to_markdown(self) -> str:
        RHI = REQUIRE_HUMAN_INPUT_MARKER
        lines = [
            f"# REPORTING CHECKLIST DRAFT — {self.standard} ({self.study_type})",
            f"> {RHI} · {DISCLAIMER}",
            f"> Tổng: {self.total_items} mục · Hoàn thành: {self.completed_count} (DRAFT — PI điền)",
            "",
            "| Mục | Mô tả | Vị trí trong bản thảo |",
            "|-----|-------|----------------------|",
        ]
        for item in self.items:
            lines.append(f"| {item.item_no} | {item.description} | {item.location} |")
        lines += ["", "---", f"**Disclaimer:** {DISCLAIMER}"]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Checklist STROBE
# ---------------------------------------------------------------------------

def _strobe_items() -> List[ReportingItem]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        ReportingItem("1a", "Xác định thiết kế trong tiêu đề / tóm tắt", RHI),
        ReportingItem("1b", "Cung cấp tóm tắt có cấu trúc thông tin chính", RHI),
        ReportingItem("2", "Giải thích bối cảnh khoa học và lý do nghiên cứu", RHI),
        ReportingItem("3", "Nêu mục tiêu, gồm giả thuyết định trước", RHI),
        ReportingItem("4", "Nêu yếu tố thiết kế chính", RHI),
        ReportingItem("5", "Mô tả cài đặt, địa điểm, ngày tháng liên quan", RHI),
        ReportingItem("6", "Tiêu chí đưa vào và loại trừ; nguồn và phương pháp tuyển", RHI),
        ReportingItem("7", "Xác định rõ các biến số, nếu áp dụng", RHI),
        ReportingItem("8", "Định nghĩa và phương pháp đo lường các biến", RHI),
        ReportingItem("9", "Mô tả biện pháp xử lý thiên lệch tiềm ẩn", RHI),
        ReportingItem("10", "Giải thích cách tính cỡ mẫu", RHI),
        ReportingItem("11", "Giải thích phân tích thống kê, kiểm soát confounding", RHI),
        ReportingItem("12a", "Báo cáo số tuyển chọn từng giai đoạn (diagram)", RHI),
        ReportingItem("12b", "Mô tả đặc điểm người tham gia", RHI),
        ReportingItem("13", "Báo cáo số đo phơi nhiễm và kết cục", RHI),
        ReportingItem("14", "Trình bày kết quả phân tích chính (OR/RR/HR + 95% CI)", RHI),
        ReportingItem("15", "Báo cáo phân tích khác: subgroup, tương tác, độ nhạy", RHI),
        ReportingItem("16", "Tóm tắt kết quả chính theo mục tiêu", RHI),
        ReportingItem("17", "Thảo luận kết quả theo kết cục ngoài nghiên cứu", RHI),
        ReportingItem("18", "Thảo luận giới hạn — thiên lệch, không chính xác, nhiều kết cục", RHI),
        ReportingItem("19", "Giải thích cẩn trọng, tính tổng quát hóa", RHI),
        ReportingItem("20", "Nguồn tài trợ và vai trò của nhà tài trợ", RHI),
    ]


# ---------------------------------------------------------------------------
# Checklist CONSORT
# ---------------------------------------------------------------------------

def _consort_items() -> List[ReportingItem]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        ReportingItem("1a", "Xác định là RCT trong tiêu đề", RHI),
        ReportingItem("1b", "Tóm tắt có cấu trúc: thiết kế, phương pháp, kết quả, kết luận", RHI),
        ReportingItem("2a", "Bối cảnh khoa học và giải thích lý do thử nghiệm", RHI),
        ReportingItem("2b", "Mục tiêu hoặc giả thuyết cụ thể", RHI),
        ReportingItem("3a", "Mô tả thiết kế thử nghiệm", RHI),
        ReportingItem("3b", "Thay đổi quan trọng sau khi bắt đầu (lý do)", RHI),
        ReportingItem("4a", "Tiêu chí đưa vào và loại trừ", RHI),
        ReportingItem("4b", "Cài đặt, địa điểm thu thập dữ liệu", RHI),
        ReportingItem("5", "Can thiệp từng nhóm (đủ chi tiết để tái lập)", RHI),
        ReportingItem("6a", "Kết cục chính và phụ xác định trước (thời điểm đánh giá)", RHI),
        ReportingItem("6b", "Thay đổi kết cục sau khi thử nghiệm bắt đầu (lý do)", RHI),
        ReportingItem("7a", "Cách tính cỡ mẫu", RHI),
        ReportingItem("7b", "Giải thích phân tích trung gian và dừng sớm (nếu có)", RHI),
        ReportingItem("8a", "Phương pháp tạo dãy phân bổ ngẫu nhiên", RHI),
        ReportingItem("8b", "Kiểu ngẫu nhiên hóa: chi tiết giới hạn (vd block size)", RHI),
        ReportingItem("9", "Cơ chế che giấu phân bổ ngẫu nhiên", RHI),
        ReportingItem("10", "Người tạo dãy / tuyển / phân bổ (có thể cùng người)", RHI),
        ReportingItem("11a", "Mù: ai bị mù sau phân bổ và cách thực hiện", RHI),
        ReportingItem("11b", "Nếu cần thiết: đánh giá sự thành công của mù", RHI),
        ReportingItem("12a", "Phương pháp thống kê so sánh nhóm", RHI),
        ReportingItem("12b", "Phương pháp phân tích bổ sung (subgroup, hiệu chỉnh…)", RHI),
        ReportingItem("13a", "CONSORT flow diagram — số mỗi giai đoạn", RHI),
        ReportingItem("13b", "Mất follow-up và loại trừ sau ngẫu nhiên (lý do)", RHI),
        ReportingItem("14a", "Ngày tuyển và ngày theo dõi", RHI),
        ReportingItem("14b", "Lý do kết thúc hoặc dừng thử nghiệm sớm", RHI),
        ReportingItem("15", "Bảng đặc điểm nền mỗi nhóm", RHI),
        ReportingItem("16", "Số tham gia viên phân tích mỗi nhóm", RHI),
        ReportingItem("17a", "Kết quả kết cục chính và phụ; ước lượng hiệu quả + CI", RHI),
        ReportingItem("17b", "Kết quả phân tích nhị phân: RR tuyệt đối và tương đối", RHI),
        ReportingItem("18", "Kết quả thử nghiệm phụ và subgroup (ghi rõ định trước hay không)", RHI),
        ReportingItem("19", "Tất cả tác hại hoặc tác dụng không mong muốn quan trọng", RHI),
        ReportingItem("20", "Hạn chế thử nghiệm; nguồn thiên lệch tiềm ẩn; không chính xác", RHI),
        ReportingItem("21", "Khả năng tổng quát hóa (giá trị áp dụng) của kết quả", RHI),
        ReportingItem("22", "Giải thích phù hợp với kết quả, cân nhắc lợi-hại; bằng chứng khác", RHI),
        ReportingItem("23", "Đăng ký thử nghiệm: số đăng ký và tên registry", RHI),
        ReportingItem("24", "Giao thức (có thể tiếp cận ở đâu không)", RHI),
        ReportingItem("25", "Nguồn tài trợ và hỗ trợ khác; vai trò nhà tài trợ", RHI),
    ]


# ---------------------------------------------------------------------------
# Checklist STARD
# ---------------------------------------------------------------------------

def _stard_items() -> List[ReportingItem]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        ReportingItem("1", "Xác định nghiên cứu độ chính xác chẩn đoán trong tiêu đề", RHI),
        ReportingItem("2", "Tóm tắt có cấu trúc: thiết kế, phương pháp, kết quả, kết luận", RHI),
        ReportingItem("3", "Bối cảnh khoa học và lâm sàng; lý do nghiên cứu", RHI),
        ReportingItem("4", "Mục tiêu và giả thuyết nghiên cứu", RHI),
        ReportingItem("5", "Thiết kế nghiên cứu (prospective/retrospective)", RHI),
        ReportingItem("6", "Tiêu chí đưa vào và loại trừ tham gia viên", RHI),
        ReportingItem("7", "Cài đặt và địa điểm; dữ liệu thu thập giai đoạn nào", RHI),
        ReportingItem("8", "Mô tả test chỉ số, gồm cách thực hiện và đọc kết quả", RHI),
        ReportingItem("9", "Mô tả chuẩn vàng, gồm cách thực hiện và đọc kết quả", RHI),
        ReportingItem("10", "Tiêu chí kỹ thuật và lâm sàng để phân loại kết quả test", RHI),
        ReportingItem("11", "Số tham gia viên và cách tuyển chọn (diagram)", RHI),
        ReportingItem("12", "Phân tích thống kê dùng để ước tính độ chính xác chẩn đoán", RHI),
        ReportingItem("13", "Tính cỡ mẫu (dựa độ nhạy/đặc hiệu dự kiến)", RHI),
        ReportingItem("14", "Flow diagram: số tuyển, nhận test chỉ số, chuẩn vàng, loại", RHI),
        ReportingItem("15", "Đặc điểm nền tham gia viên và mẫu lâm sàng", RHI),
        ReportingItem("16", "Khoảng thời gian giữa test chỉ số và chuẩn vàng", RHI),
        ReportingItem("17", "Bảng chéo (2×2): phân phối kết quả test theo kết quả chuẩn vàng", RHI),
        ReportingItem("18", "Ước lượng độ chính xác chẩn đoán + độ bất định (95% CI)", RHI),
        ReportingItem("19", "Kết quả phân tích bất kỳ về biến thể trong độ chính xác", RHI),
        ReportingItem("20", "Thảo luận giới hạn", RHI),
        ReportingItem("21", "Hàm ý thực hành; tính tổng quát hóa", RHI),
        ReportingItem("22", "Đăng ký nghiên cứu và số đăng ký", RHI),
        ReportingItem("23", "Giao thức (có thể tiếp cận ở đâu)", RHI),
        ReportingItem("24", "Nguồn tài trợ và hỗ trợ; vai trò nhà tài trợ", RHI),
    ]


# ---------------------------------------------------------------------------
# Checklist PRISMA 2020
# ---------------------------------------------------------------------------

def _prisma_items() -> List[ReportingItem]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        ReportingItem("1", "Xác định là SR/MA trong tiêu đề", RHI),
        ReportingItem("2", "Tóm tắt có cấu trúc (Background, Objectives, Data sources, Eligibility, Results, Conclusions)", RHI),
        ReportingItem("3", "Lý do / nhu cầu SR này so với SR đã có", RHI),
        ReportingItem("4", "Mục tiêu tường minh cho câu hỏi PICO", RHI),
        ReportingItem("5", "Giao thức và đăng ký (PROSPERO/OSF) — số đăng ký", RHI),
        ReportingItem("6", "Tiêu chí đưa vào (PICO, thiết kế NC, thời gian, ngôn ngữ)", RHI),
        ReportingItem("7", "Nguồn thông tin — CSDL, ngày tìm kiếm cuối", RHI),
        ReportingItem("8", "Chiến lược tìm kiếm đầy đủ ≥ 1 CSDL", RHI),
        ReportingItem("9", "Quy trình sàng lọc (số người, độc lập, giải quyết bất đồng)", RHI),
        ReportingItem("10", "Quy trình trích xuất dữ liệu (số người, độc lập, bất đồng)", RHI),
        ReportingItem("11", "Danh sách và định nghĩa biến trích xuất", RHI),
        ReportingItem("12", "Đánh giá nguy cơ sai lệch (công cụ, quy trình)", RHI),
        ReportingItem("13", "Phương pháp tổng hợp (không gộp hoặc meta-analysis)", RHI),
        ReportingItem("14", "Đánh giá không đồng nhất (I², Q, τ²)", RHI),
        ReportingItem("15", "Đánh giá thiên lệch báo cáo (publication bias)", RHI),
        ReportingItem("16", "Phân tích độ nhạy", RHI),
        ReportingItem("17", "PRISMA flow diagram", RHI),
        ReportingItem("18", "Đặc điểm mỗi nghiên cứu đưa vào", RHI),
        ReportingItem("19", "Nguy cơ sai lệch mỗi nghiên cứu", RHI),
        ReportingItem("20", "Kết quả tổng hợp từng kết cục; forest plot", RHI),
        ReportingItem("21", "Kết quả điều tra không đồng nhất", RHI),
        ReportingItem("22", "Kết quả đánh giá thiên lệch báo cáo", RHI),
        ReportingItem("23", "Kết quả phân tích độ nhạy", RHI),
        ReportingItem("24", "Thảo luận: giới hạn NC đưa vào; giới hạn SR", RHI),
        ReportingItem("25", "Kết luận; hàm ý thực hành; nghiên cứu tương lai", RHI),
        ReportingItem("26", "Khai báo xung đột lợi ích", RHI),
        ReportingItem("27", "Nguồn tài trợ", RHI),
        ReportingItem("28", "Ghi nhận đóng góp và tác giả", RHI),
    ]


# ---------------------------------------------------------------------------
# Checklist COREQ
# ---------------------------------------------------------------------------

def _coreq_items() -> List[ReportingItem]:
    RHI = REQUIRE_HUMAN_INPUT_MARKER
    return [
        ReportingItem("1-T", "Tên phỏng vấn viên / điều phối viên nhóm", RHI),
        ReportingItem("2-T", "Chuyên môn và trình độ học vấn (vd PhD)", RHI),
        ReportingItem("3-T", "Giới tính", RHI),
        ReportingItem("4-T", "Kinh nghiệm và đào tạo phỏng vấn / định tính", RHI),
        ReportingItem("5-T", "Mối quan hệ với người tham gia", RHI),
        ReportingItem("6-T", "Giả định / quan niệm trước (assumptions) của nhà NC", RHI),
        ReportingItem("7-T", "Mô tả nghiên cứu cho người tham gia", RHI),
        ReportingItem("8-T", "Phần mềm ghi âm / quay (có/không)", RHI),
        ReportingItem("9-T", "Đặc điểm hiện trường phỏng vấn", RHI),
        ReportingItem("10-D", "Lấy mẫu có mục đích (purposive sampling)", RHI),
        ReportingItem("11-D", "Phương pháp tiếp cận người tham gia", RHI),
        ReportingItem("12-D", "Cỡ mẫu", RHI),
        ReportingItem("13-D", "Không tham gia (số và lý do)", RHI),
        ReportingItem("14-D", "Đặc điểm người tham gia", RHI),
        ReportingItem("15-D", "Hướng dẫn phỏng vấn (interview guide): pilot hay không", RHI),
        ReportingItem("16-D", "Lặp phỏng vấn (có/không)", RHI),
        ReportingItem("17-D", "Ghi âm / quay", RHI),
        ReportingItem("18-D", "Ghi chép trường (field notes — có/không)", RHI),
        ReportingItem("19-D", "Thời gian phỏng vấn", RHI),
        ReportingItem("20-D", "Bão hòa dữ liệu", RHI),
        ReportingItem("21-D", "Trả phiên âm cho người tham gia (member check — có/không)", RHI),
        ReportingItem("22-F", "Số dữ liệu mô tả so với trích dẫn", RHI),
        ReportingItem("23-F", "Phân tích kết quả có / không nhất quán với dữ liệu", RHI),
        ReportingItem("24-F", "Sự rõ ràng của chủ đề chính", RHI),
        ReportingItem("25-F", "Sự phong phú và đa chiều của mô tả", RHI),
        ReportingItem("26-F", "Sự nhất quán giữa dữ liệu và kết quả", RHI),
        ReportingItem("27-F", "Sự rõ ràng của ý kiến chủ quan so với khách quan", RHI),
        ReportingItem("28-F", "Hàm ý và giới hạn của phát hiện", RHI),
        ReportingItem("29-F", "Chuyển đổi được (transferability) sang bối cảnh khác", RHI),
        ReportingItem("30-F", "Hàm ý cho thực hành và nghiên cứu tương lai", RHI),
        ReportingItem("31-F", "Nguồn tài trợ và khai báo xung đột lợi ích", RHI),
        ReportingItem("32-F", "Sự phê duyệt đạo đức", RHI),
    ]


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_CHECKLIST_MAP = {
    StudyType.CROSS_SECTIONAL: _strobe_items,
    StudyType.COHORT: _strobe_items,
    StudyType.CASE_CONTROL: _strobe_items,
    StudyType.RCT: _consort_items,
    StudyType.DIAGNOSTIC: _stard_items,
    StudyType.SR_MA: _prisma_items,
    StudyType.QUALITATIVE: _coreq_items,
}


def build_reporting_checklist(study_type: StudyType) -> ReportingChecklist:
    """Xây dựng checklist báo cáo. Mọi nội dung là DRAFT — REQUIRE_HUMAN_INPUT."""
    fn = _CHECKLIST_MAP.get(study_type)
    if fn is None:
        raise ValueError(f"StudyType không hỗ trợ: {study_type}")
    items = fn()
    return ReportingChecklist(
        standard=REPORTING_STANDARD[study_type],
        study_type=study_type.value,
        items=items,
        total_items=len(items),
        completed_count=0,
    )
