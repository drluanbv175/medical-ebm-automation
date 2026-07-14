"""
project_methodology_planner — Checklist thiết kế theo loại nghiên cứu (V4.3.3).

7 loại: CROSS_SECTIONAL/COHORT/CASE_CONTROL → STROBE;
RCT → CONSORT; DIAGNOSTIC → STARD; SR_MA → PRISMA; QUALITATIVE → COREQ.
OFFLINE · KHÔNG API / PII / dữ liệu thật. Mọi output là DRAFT.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List

from .project_config import (
    REPORTING_STANDARD,
    REQUIRE_HUMAN_INPUT_MARKER,
    StudyType,
)

# ---------------------------------------------------------------------------
# Dataclass cho từng hạng mục checklist
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ChecklistItem:
    item_id: str
    section: str
    description: str
    rationale: str
    status: str = REQUIRE_HUMAN_INPUT_MARKER

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class MethodologyPlan:
    study_type: str
    reporting_standard: str
    design_checklist: List[ChecklistItem]
    sample_size_note: str           # NOTE ONLY — KHÔNG tính số cụ thể
    analysis_approach_note: str     # NOTE ONLY
    key_bias_risks: List[str]
    requires_human_review: List[str]

    def as_dict(self) -> dict:
        return {
            "study_type": self.study_type,
            "reporting_standard": self.reporting_standard,
            "design_checklist": [c.as_dict() for c in self.design_checklist],
            "sample_size_note": self.sample_size_note,
            "analysis_approach_note": self.analysis_approach_note,
            "key_bias_risks": self.key_bias_risks,
            "requires_human_review": self.requires_human_review,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Methodology Plan — {self.study_type} ({self.reporting_standard})",
            "",
            f"> **DRAFT** — {REQUIRE_HUMAN_INPUT_MARKER} — Cần PI kiểm chứng.",
            "",
            "## Design Checklist",
            "",
        ]
        for item in self.design_checklist:
            lines.append(f"### [{item.item_id}] {item.section}")
            lines.append(f"- **Mô tả:** {item.description}")
            lines.append(f"- **Lý do:** {item.rationale}")
            lines.append(f"- **Trạng thái:** {item.status}")
            lines.append("")

        lines += [
            "## Cỡ mẫu (ghi chú)",
            self.sample_size_note, "",
            "## Tiếp cận phân tích (ghi chú)",
            self.analysis_approach_note, "",
            "## Nguy cơ thiên lệch chính",
        ]
        for b in self.key_bias_risks:
            lines.append(f"- {b}")
        lines += ["", "## Cần PI xem xét"]
        for r in self.requires_human_review:
            lines.append(f"- {r}")
        lines += ["", "---", "**Disclaimer:** Bản DRAFT tự động. Cần bác sĩ / PI kiểm chứng."]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Checklist theo loại nghiên cứu
# ---------------------------------------------------------------------------

def _strobe_cross_sectional() -> List[ChecklistItem]:
    return [
        ChecklistItem("S-CS-1", "Tiêu đề / Tóm tắt",
            "Nêu rõ thiết kế cắt ngang trong tiêu đề hoặc tóm tắt (STROBE 1).",
            "STROBE item 1a: Xác định thiết kế bằng thuật ngữ thường dùng."),
        ChecklistItem("S-CS-2", "Bối cảnh / Lý do",
            "Giải thích lý do khoa học và mục tiêu nghiên cứu (STROBE 2).",
            "STROBE item 2: Bối cảnh, lý do, giả thuyết."),
        ChecklistItem("S-CS-3", "Thiết kế nghiên cứu",
            "Nêu các yếu tố thiết kế chính (STROBE 6).",
            "STROBE item 6: Cài đặt, địa điểm, ngày tháng."),
        ChecklistItem("S-CS-4", "Tiêu chí tham gia",
            "Tiêu chí đưa vào / loại trừ rõ ràng (STROBE 7).",
            "STROBE item 7a: Tiêu chí tuyển chọn."),
        ChecklistItem("S-CS-5", "Biến số",
            "Định nghĩa rõ biến phụ thuộc, biến độc lập, biến nhiễu (STROBE 8).",
            "STROBE item 8: Tất cả biến số liên quan."),
        ChecklistItem("S-CS-6", "Cỡ mẫu",
            "Giải thích cách xác định cỡ mẫu (STROBE 10) — [REQUIRE_HUMAN_INPUT].",
            "STROBE item 10: Tính cỡ mẫu dựa effect size PI ấn định."),
        ChecklistItem("S-CS-7", "Phương pháp thống kê",
            "Mô tả phương pháp thống kê, kể cả kiểm soát confounding (STROBE 12).",
            "STROBE item 12a: Mô tả phương pháp thống kê."),
        ChecklistItem("S-CS-8", "Thiên lệch",
            "Mô tả nỗ lực giải quyết thiên lệch tiềm ẩn (STROBE 9).",
            "STROBE item 9: Thiên lệch, phương pháp xử lý."),
    ]


def _strobe_cohort() -> List[ChecklistItem]:
    base = _strobe_cross_sectional()
    base.append(ChecklistItem("S-CO-9", "Theo dõi",
        "Mô tả thời gian theo dõi, mất theo dõi, kiểm duyệt (STROBE 12).",
        "STROBE item 12d: Thời gian theo dõi, xử lý censoring."))
    base.append(ChecklistItem("S-CO-10", "Phân tích sống còn",
        "Nêu phương pháp phân tích sống còn nếu dùng (Kaplan-Meier, Cox).",
        "Cohort studies often use time-to-event analysis."))
    return base


def _strobe_case_control() -> List[ChecklistItem]:
    base = _strobe_cross_sectional()
    base.append(ChecklistItem("S-CC-9", "Định nghĩa ca bệnh / chứng",
        "Nêu rõ tiêu chí định nghĩa ca bệnh và chứng (STROBE 7b).",
        "STROBE item 7b: Tiêu chí tuyển case, control."))
    base.append(ChecklistItem("S-CC-10", "Ghép cặp",
        "Mô tả chiến lược ghép cặp nếu dùng (STROBE 6, 12).",
        "Matching variables must be documented."))
    return base


def _consort_rct() -> List[ChecklistItem]:
    return [
        ChecklistItem("C-1", "Tiêu đề",
            "Xác định là RCT trong tiêu đề (CONSORT 1a).",
            "CONSORT item 1a."),
        ChecklistItem("C-2", "Bối cảnh",
            "Giải thích lý do khoa học và mục tiêu (CONSORT 2a).",
            "CONSORT item 2a."),
        ChecklistItem("C-3", "Tiêu chí tuyển",
            "Tiêu chí đưa vào / loại trừ, bối cảnh và địa điểm (CONSORT 4a, 4b).",
            "CONSORT items 4a-4b."),
        ChecklistItem("C-4", "Can thiệp",
            "Mô tả can thiệp đủ để tái lập, gồm thời điểm và thời gian (CONSORT 5).",
            "CONSORT item 5."),
        ChecklistItem("C-5", "Kết cục",
            "Định nghĩa trước kết cục chính và phụ, phương pháp đo (CONSORT 6a).",
            "CONSORT item 6a."),
        ChecklistItem("C-6", "Cỡ mẫu",
            "Cách xác định cỡ mẫu, giả định (CONSORT 7a) — [REQUIRE_HUMAN_INPUT].",
            "CONSORT item 7a: giả định α, β, effect size do PI ấn định."),
        ChecklistItem("C-7", "Phân bổ ngẫu nhiên",
            "Phương pháp tạo dãy ngẫu nhiên (CONSORT 8a, 8b).",
            "CONSORT items 8a-8b."),
        ChecklistItem("C-8", "Che giấu phân bổ",
            "Cơ chế che giấu (CONSORT 9).",
            "CONSORT item 9."),
        ChecklistItem("C-9", "Mù",
            "Mô tả mù (mù đơn/kép) (CONSORT 11a).",
            "CONSORT item 11a."),
        ChecklistItem("C-10", "Thống kê",
            "Phương pháp thống kê cho kết cục chính và phụ (CONSORT 12a).",
            "CONSORT item 12a."),
    ]


def _stard_diagnostic() -> List[ChecklistItem]:
    return [
        ChecklistItem("D-1", "Tiêu đề",
            "Xác định là nghiên cứu độ chính xác chẩn đoán (STARD 1).",
            "STARD item 1."),
        ChecklistItem("D-2", "Câu hỏi / mục tiêu",
            "Xác định câu hỏi nghiên cứu và mục tiêu (STARD 3).",
            "STARD item 3."),
        ChecklistItem("D-3", "Dân số mục tiêu",
            "Mô tả dân số dự kiến áp dụng test (STARD 5).",
            "STARD item 5."),
        ChecklistItem("D-4", "Test chỉ số",
            "Mô tả test chỉ số và cách thực hiện (STARD 6).",
            "STARD item 6."),
        ChecklistItem("D-5", "Chuẩn vàng",
            "Mô tả chuẩn vàng và lý do (STARD 7).",
            "STARD item 7."),
        ChecklistItem("D-6", "Cỡ mẫu",
            "Cách tính cỡ mẫu — [REQUIRE_HUMAN_INPUT] (STARD 9).",
            "STARD item 9."),
        ChecklistItem("D-7", "Phân tích",
            "Phương pháp ước tính độ nhạy, độ đặc hiệu, LR (STARD 13).",
            "STARD item 13."),
    ]


def _prisma_sr_ma() -> List[ChecklistItem]:
    return [
        ChecklistItem("P-1", "Giao thức",
            "Đăng ký giao thức PROSPERO/OSF — [REQUIRE_HUMAN_INPUT] (PRISMA 24).",
            "PRISMA-2020 item 24."),
        ChecklistItem("P-2", "Tiêu chí đưa vào",
            "Tiêu chí đưa vào PICO, loại thiết kế, thời gian (PRISMA 6).",
            "PRISMA-2020 item 6."),
        ChecklistItem("P-3", "Chiến lược tìm kiếm",
            "Mô tả đầy đủ chiến lược tìm kiếm ≥1 CSDL (PRISMA 7).",
            "PRISMA-2020 item 7."),
        ChecklistItem("P-4", "Sàng lọc",
            "Mô tả quy trình sàng lọc tiêu đề, tóm tắt, toàn văn (PRISMA 8).",
            "PRISMA-2020 item 8."),
        ChecklistItem("P-5", "Trích xuất dữ liệu",
            "Phương pháp trích xuất, công cụ, kiểm tra liên observer (PRISMA 9).",
            "PRISMA-2020 item 9."),
        ChecklistItem("P-6", "Đánh giá nguy cơ sai lệch",
            "Công cụ RoB (RoB 2/ROBINS-I) theo thiết kế (PRISMA 12).",
            "PRISMA-2020 item 12."),
        ChecklistItem("P-7", "Tổng hợp",
            "Mô tả kế hoạch gộp meta-analysis hoặc tổng hợp định tính (PRISMA 13).",
            "PRISMA-2020 item 13."),
        ChecklistItem("P-8", "Bias xuất bản",
            "Kế hoạch đánh giá bias xuất bản (PRISMA 15).",
            "PRISMA-2020 item 15."),
    ]


def _coreq_qualitative() -> List[ChecklistItem]:
    return [
        ChecklistItem("Q-1", "Nhóm nghiên cứu",
            "Mô tả kinh nghiệm, đặc điểm nhóm nghiên cứu (COREQ 1-9).",
            "COREQ domain 1: Research team."),
        ChecklistItem("Q-2", "Thiết kế nghiên cứu",
            "Mô tả lý do chọn phương pháp định tính (COREQ 10).",
            "COREQ domain 2, item 10."),
        ChecklistItem("Q-3", "Lấy mẫu",
            "Phương pháp lấy mẫu có chủ đích, tiêu chí bão hòa (COREQ 12).",
            "COREQ domain 2, item 12."),
        ChecklistItem("Q-4", "Thu thập dữ liệu",
            "Phương pháp phỏng vấn/nhóm tiêu điểm, hướng dẫn phỏng vấn (COREQ 14-18).",
            "COREQ domain 2, items 14-18."),
        ChecklistItem("Q-5", "Phân tích",
            "Mô tả phương pháp mã hóa, phân tích chủ đề, kiểm tra tín cậy (COREQ 22-28).",
            "COREQ domain 3."),
        ChecklistItem("Q-6", "Độ tin cậy (Trustworthiness)",
            "Ghi rõ chiến lược credibility, transferability, confirmability.",
            "COREQ: member checking, negative case analysis."),
        ChecklistItem("Q-7", "Cỡ mẫu / Bão hòa",
            "Giải thích cỡ mẫu dự kiến và tiêu chí bão hòa — [REQUIRE_HUMAN_INPUT].",
            "Qualitative: purposive + saturation criterion."),
    ]


# ---------------------------------------------------------------------------
# Dispatch function
# ---------------------------------------------------------------------------

_CHECKLIST_MAP = {
    StudyType.CROSS_SECTIONAL: _strobe_cross_sectional,
    StudyType.COHORT: _strobe_cohort,
    StudyType.CASE_CONTROL: _strobe_case_control,
    StudyType.RCT: _consort_rct,
    StudyType.DIAGNOSTIC: _stard_diagnostic,
    StudyType.SR_MA: _prisma_sr_ma,
    StudyType.QUALITATIVE: _coreq_qualitative,
}

_SAMPLE_SIZE_NOTES: Dict[StudyType, str] = {
    StudyType.CROSS_SECTIONAL: (
        f"Cỡ mẫu cắt ngang phụ thuộc vào tỷ lệ ước tính, độ chính xác mong muốn (d), "
        f"và α. {REQUIRE_HUMAN_INPUT_MARKER}: tỷ lệ dự kiến từ pilot hoặc y văn (PMID cần xác minh), "
        f"d, α do PI ấn định."
    ),
    StudyType.COHORT: (
        f"Cỡ mẫu cohort phụ thuộc vào tỷ lệ phơi nhiễm, RR dự kiến, α, β, thời gian theo dõi. "
        f"{REQUIRE_HUMAN_INPUT_MARKER}: thông số từ y văn (cần xác minh) hoặc pilot data do PI cung cấp."
    ),
    StudyType.CASE_CONTROL: (
        f"Cỡ mẫu case-control phụ thuộc vào OR dự kiến, tỷ lệ phơi nhiễm ở chứng, tỷ lệ case:control. "
        f"{REQUIRE_HUMAN_INPUT_MARKER}: OR, tần số phơi nhiễm từ y văn do PI xác nhận."
    ),
    StudyType.RCT: (
        f"Cỡ mẫu RCT phụ thuộc vào effect size tối thiểu có ý nghĩa (MCID), α, β (power), "
        f"tỷ lệ bỏ cuộc ước tính. {REQUIRE_HUMAN_INPUT_MARKER}: MCID do PI/bệnh nhân ấn định; "
        f"tỷ lệ bỏ cuộc từ pilot; α=0.05, β=0.2 nếu không nêu khác."
    ),
    StudyType.DIAGNOSTIC: (
        f"Cỡ mẫu chẩn đoán phụ thuộc vào độ nhạy/đặc hiệu mong đợi, tỷ lệ bệnh. "
        f"{REQUIRE_HUMAN_INPUT_MARKER}: thông số từ y văn (cần xác minh) do PI xác nhận."
    ),
    StudyType.SR_MA: (
        f"SR+MA không tính cỡ mẫu trước thu thập — số nghiên cứu phụ thuộc vào kết quả tìm kiếm. "
        f"{REQUIRE_HUMAN_INPUT_MARKER}: Số nghiên cứu dự kiến từ tìm kiếm sơ bộ, power phân tích phụ."
    ),
    StudyType.QUALITATIVE: (
        f"Nghiên cứu định tính không tính cỡ mẫu theo công thức — dừng khi đạt BÃO HÒA DỮ LIỆU. "
        f"{REQUIRE_HUMAN_INPUT_MARKER}: Tiêu chí bão hòa, phương pháp kiểm tra (member check)."
    ),
}

_ANALYSIS_NOTES: Dict[StudyType, str] = {
    StudyType.CROSS_SECTIONAL: (
        "Thống kê mô tả + hồi quy logistic/Poisson cho kết cục nhị phân, "
        "hoặc hồi quy tuyến tính cho kết cục liên tục. Kiểm soát confounding qua mô hình đa biến."
    ),
    StudyType.COHORT: (
        "Phân tích sống còn (Kaplan-Meier, log-rank), mô hình Cox proportional-hazards. "
        "Kiểm tra assumption proportional hazards. Phân tích per-protocol và ITT nếu có can thiệp."
    ),
    StudyType.CASE_CONTROL: (
        "Tính OR với 95% CI bằng hồi quy logistic điều kiện (nếu ghép cặp) hoặc không điều kiện. "
        "Kiểm soát confounding đo lường được."
    ),
    StudyType.RCT: (
        "Phân tích ITT là chính. Mô hình hỗn hợp cho dữ liệu lặp, phân tích per-protocol phụ. "
        "Tất cả mô tả trong SAP phải được khóa TRƯỚC KHI xem dữ liệu."
    ),
    StudyType.DIAGNOSTIC: (
        "Tính độ nhạy, độ đặc hiệu, LR+, LR−, AUC ROC với 95% CI (bootstrapping). "
        "Phân tích subgroup nếu SAP đã định trước."
    ),
    StudyType.SR_MA: (
        "Mô hình hiệu ứng ngẫu nhiên (DerSimonian-Laird) hoặc fixed-effects tùy I². "
        "Funnel plot, Egger's test cho publication bias. Phân tích subgroup và sensitivity đã định trước."
    ),
    StudyType.QUALITATIVE: (
        "Phân tích chủ đề (thematic analysis) hoặc framework analysis. "
        "Mã hóa tổng thể và giữa-người mã; kiểm tra tín cậy bằng member checking."
    ),
}

_BIAS_RISKS: Dict[StudyType, List[str]] = {
    StudyType.CROSS_SECTIONAL: [
        "Thiên lệch chọn lựa (selection bias) nếu không ngẫu nhiên",
        "Thiên lệch thông tin (recall bias) với dữ liệu hồi cứu",
        "Confounding chưa đo được (residual confounding)",
        "Không thể xác định quan hệ nhân quả (cross-sectional)",
    ],
    StudyType.COHORT: [
        "Mất theo dõi không ngẫu nhiên (informative censoring)",
        "Thiên lệch healthy worker effect",
        "Confounding chỉ định điều trị (confounding by indication)",
        "Thời gian tiềm tàng phơi nhiễm → kết cục không rõ",
    ],
    StudyType.CASE_CONTROL: [
        "Thiên lệch nhớ lại (recall bias) — thường ở case cao hơn control",
        "Thiên lệến nguồn chứng (control selection bias)",
        "Thiên lệch phỏng vấn viên (interviewer bias)",
        "Confounding không đo được",
    ],
    StudyType.RCT: [
        "Thiên lệch thực hiện (performance bias) nếu không mù",
        "Thiên lệch phát hiện (detection bias) khi đánh giá kết cục",
        "Mất theo dõi không cân bằng giữa hai nhóm",
        "Nhiễm chéo giữa nhóm can thiệp và chứng",
    ],
    StudyType.DIAGNOSTIC: [
        "Thiên lệch phổ (spectrum bias) — tuyển chọn ca bệnh không đại diện",
        "Thiên lệch xác nhận chuẩn vàng một phần (partial verification)",
        "Thiên lệch giải thích (interpretation bias) khi đọc test",
        "Thiên lệch tập hợp (incorporation bias) nếu test chỉ số ảnh hưởng chuẩn vàng",
    ],
    StudyType.SR_MA: [
        "Thiên lệch xuất bản (publication bias) — nghiên cứu âm tính ít được công bố",
        "Không đồng nhất lâm sàng và phương pháp giữa các nghiên cứu (heterogeneity)",
        "Thiên lệch ngôn ngữ nếu chỉ tìm tiếng Anh",
        "Thiên lệch tìm kiếm không toàn diện",
    ],
    StudyType.QUALITATIVE: [
        "Thiên lệch phản hồi xã hội (social desirability bias) trong phỏng vấn",
        "Thiên lệch nhà nghiên cứu (researcher bias) ảnh hưởng mã hóa",
        "Tính không chuyển đổi được (non-transferability) sang bối cảnh khác",
        "Bão hòa giả (premature saturation)",
    ],
}

_HUMAN_REVIEW_ITEMS: Dict[StudyType, List[str]] = {
    StudyType.CROSS_SECTIONAL: [
        "Xác nhận tỷ lệ ước tính từ y văn (PMID cần kiểm chứng)",
        "Xác nhận độ chính xác mong muốn (d) và α",
        "Xác nhận biến confounding cần đo",
        "Xác nhận tiêu chí tuyển chọn / loại trừ",
    ],
    StudyType.COHORT: [
        "Xác nhận RR dự kiến và α, β",
        "Xác nhận định nghĩa phơi nhiễm và kết cục",
        "Xác nhận thời gian theo dõi tối thiểu",
        "Xác nhận kế hoạch xử lý mất theo dõi",
    ],
    StudyType.CASE_CONTROL: [
        "Xác nhận OR dự kiến từ y văn (PMID cần kiểm chứng)",
        "Xác nhận tỷ lệ phơi nhiễm ở chứng",
        "Xác nhận nguồn tuyển chọn chứng",
        "Xác nhận chiến lược ghép cặp (nếu có)",
    ],
    StudyType.RCT: [
        "Xác nhận MCID từ guideline hoặc nghiên cứu trước (PMID cần kiểm chứng)",
        "Xác nhận tỷ lệ bỏ cuộc ước tính",
        "Xác nhận phương pháp ngẫu nhiên hóa và che giấu phân bổ",
        "Xác nhận kế hoạch mù và đánh giá kết cục",
    ],
    StudyType.DIAGNOSTIC: [
        "Xác nhận độ nhạy/đặc hiệu dự kiến từ y văn (PMID cần kiểm chứng)",
        "Xác nhận tỷ lệ bệnh trong dân số mục tiêu",
        "Xác nhận quy trình chuẩn vàng",
        "Xác nhận ngưỡng dương tính của test chỉ số",
    ],
    StudyType.SR_MA: [
        "Xác nhận giao thức đăng ký PROSPERO/OSF",
        "Xác nhận chiến lược tìm kiếm đầy đủ (tất cả CSDL liên quan)",
        "Xác nhận công cụ đánh giá RoB theo thiết kế",
        "Xác nhận kế hoạch gộp (pooling) và ngưỡng heterogeneity",
    ],
    StudyType.QUALITATIVE: [
        "Xác nhận cách tiếp cận (hiện tượng học, grounded theory, thematic analysis…)",
        "Xác nhận tiêu chí bão hòa và kế hoạch kiểm tra",
        "Xác nhận phương pháp member checking",
        "Xác nhận tính phản tư (reflexivity) của nhóm nghiên cứu",
    ],
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def plan_methodology(study_type: StudyType) -> MethodologyPlan:
    """Trả MethodologyPlan cho loại nghiên cứu. Mọi nội dung là DRAFT."""
    checklist_fn = _CHECKLIST_MAP.get(study_type)
    if checklist_fn is None:
        raise ValueError(f"StudyType không hỗ trợ: {study_type}")

    return MethodologyPlan(
        study_type=study_type.value,
        reporting_standard=REPORTING_STANDARD[study_type],
        design_checklist=checklist_fn(),
        sample_size_note=_SAMPLE_SIZE_NOTES[study_type],
        analysis_approach_note=_ANALYSIS_NOTES[study_type],
        key_bias_risks=_BIAS_RISKS[study_type],
        requires_human_review=_HUMAN_REVIEW_ITEMS[study_type],
    )
