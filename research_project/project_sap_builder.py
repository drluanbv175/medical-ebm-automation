"""
project_sap_builder — Xây dựng SAP draft theo loại nghiên cứu (V4.3.3).

Mọi thông số thống kê là REQUIRE_HUMAN_INPUT. OFFLINE · KHÔNG PII / API.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List

from .project_config import REQUIRE_HUMAN_INPUT_MARKER, DISCLAIMER, StudyType


@dataclasses.dataclass
class SAPSection:
    section_id: str
    title: str
    content: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class SAPDraft:
    study_type: str
    version: str
    sections: List[SAPSection]
    lock_reminder: str

    def to_markdown(self) -> str:
        RHI = REQUIRE_HUMAN_INPUT_MARKER
        lines = [
            f"# STATISTICAL ANALYSIS PLAN (DRAFT) — {self.study_type}",
            f"> Phiên bản: {self.version} · {RHI} · {DISCLAIMER}",
            f"> **CẢNH BÁO:** SAP phải được PI khóa TRƯỚC KHI xem dữ liệu (G4). Đây là bản DRAFT.",
            "",
        ]
        for sec in self.sections:
            lines.append(f"## {sec.section_id}. {sec.title}")
            lines.append("")
            lines.append(sec.content)
            lines.append("")
        lines += [
            "---",
            f"**Lock reminder:** {self.lock_reminder}",
            f"**Disclaimer:** {DISCLAIMER}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section chung cho mọi loại
# ---------------------------------------------------------------------------

def _general_sections(rhi: str) -> List[SAPSection]:
    return [
        SAPSection("SAP-1", "Tổng quan và mục tiêu phân tích", f"""
Đây là SAP DRAFT cho đề tài đăng ký tại: {rhi}

**Kết cục chính:** {rhi}
**Kết cục phụ:** {rhi}
**Dân số phân tích:** {rhi} (ITT / Per-protocol / Dân số đủ tiêu chuẩn)
**Thời điểm phân tích:** {rhi}
"""),
        SAPSection("SAP-2", "Phân tích mô tả (Descriptive statistics)", f"""
- Biến liên tục: Mean ± SD hoặc Median [IQR] tùy phân phối.
- Biến phân loại: n (%).
- Kiểm tra phân phối: Shapiro-Wilk (n < 50) hoặc Kolmogorov-Smirnov.
- Biến thiếu: mô tả số lượng + tỷ lệ thiếu mỗi biến; {rhi}: kế hoạch xử lý thiếu (imputation vs complete case).
"""),
        SAPSection("SAP-3", "Xử lý dữ liệu thiếu", f"""
- Định nghĩa: thiếu hoàn toàn ngẫu nhiên (MCAR), ngẫu nhiên (MAR), không ngẫu nhiên (MNAR).
- Phương pháp dự kiến: {rhi} (multiple imputation / complete-case / LOCF — chọn 1 và giải thích).
- Ngưỡng thiếu có thể chấp nhận: {rhi}% mỗi biến.
"""),
    ]


# ---------------------------------------------------------------------------
# SAP đặc thù theo loại nghiên cứu
# ---------------------------------------------------------------------------

def _sap_cross_sectional(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Phân tích chính", f"""
- Kết cục nhị phân: Tỷ lệ (%) với 95% CI (Wilson/exact binomial).
- So sánh nhóm: Chi-square / Fisher's exact; OR với 95% CI (hồi quy logistic đơn biến).
- Phân tích đa biến: Hồi quy logistic đa biến — biến đưa vào: {rhi} (dựa DAG, không stepwise).
- Biến liên tục: t-test (phân phối chuẩn) hoặc Mann-Whitney U.
"""),
        SAPSection("SAP-5", "Phân tích độ nhạy", f"""
- Phân tích độ nhạy chính: {rhi}
- Subgroup analysis (định trước): {rhi}
- Ngưỡng p có ý nghĩa: α = {rhi} (mặc định 0.05 nếu PI không ấn định khác).
"""),
    ]


def _sap_cohort(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Phân tích sống còn chính", f"""
- Kaplan-Meier: đường cong sống còn mỗi nhóm phơi nhiễm.
- Log-rank test so sánh đường cong.
- Cox proportional hazards: HR với 95% CI.
  - Biến vào mô hình: {rhi} (dựa lý thuyết / DAG).
  - Kiểm tra assumption PH: Schoenfeld residuals.
- Time-zero: {rhi}; thời điểm censoring: {rhi}.
"""),
        SAPSection("SAP-5", "Phân tích phụ và độ nhạy", f"""
- Subgroup phân tích định trước: {rhi}
- Cạnh tranh sự kiện (competing risks): Fine-Gray nếu có biến cố cạnh tranh {rhi}
- Phân tích độ nhạy: {rhi}
"""),
    ]


def _sap_case_control(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Phân tích chính", f"""
- OR thô (crude OR) với 95% CI: hồi quy logistic đơn biến.
- OR hiệu chỉnh: hồi quy logistic đa biến — biến đưa vào: {rhi}.
- Nếu ghép cặp: hồi quy logistic điều kiện (conditional logistic regression).
- Kiểm tra tương tác: {rhi}
"""),
        SAPSection("SAP-5", "Phân tích độ nhạy", f"""
- E-value tính toán độ nhạy với unmeasured confounding.
- Subgroup: {rhi}
"""),
    ]


def _sap_rct(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Dân số phân tích", f"""
- **ITT (Intention-to-treat):** Tất cả đã phân bổ ngẫu nhiên — phân tích CHÍNH.
- **Per-protocol:** Chỉ người tuân thủ ≥ {rhi}% — phân tích PHỤ.
- **Safety set:** Tất cả nhận ít nhất 1 liều can thiệp.
"""),
        SAPSection("SAP-5", "Phân tích kết cục chính", f"""
- Kết cục nhị phân: RR / RD / NNT với 95% CI (risk difference phù hợp cho RCT).
- Kết cục liên tục: Hiệu khác biệt trung bình (MD) với 95% CI; t-test hoặc ANCOVA điều chỉnh baseline.
- Kết cục thời gian-đến-biến-cố: HR (Cox) với 95% CI.
- **Mọi so sánh dùng 2-sided α = {rhi} (mặc định 0.05).**
"""),
        SAPSection("SAP-6", "Điều chỉnh đa so sánh", f"""
- Nếu nhiều kết cục chính: {rhi} (Bonferroni / Hochberg / FDR — PI chọn).
- Kết cục phụ: mang tính thăm dò, không điều chỉnh p nhưng ghi rõ.
"""),
        SAPSection("SAP-7", "Phân tích trung gian và tương tác", f"""
- Phân tích tương tác (heterogeneity of treatment effect): {rhi}
- Phân tích trung gian (mediation): {rhi}
"""),
    ]


def _sap_diagnostic(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Phân tích độ chính xác chẩn đoán", f"""
- Bảng 2×2: TP, FP, FN, TN.
- Độ nhạy, độ đặc hiệu, PPV, NPV với 95% CI (Wilson binomial).
- LR+, LR− và DOR.
- AUC ROC với 95% CI (DeLong method).
- Ngưỡng tối ưu: Youden index hoặc {rhi}.
"""),
        SAPSection("SAP-5", "Phân tích phụ", f"""
- Phân tích theo subgroup định trước: {rhi}
- Nếu nhiều ngưỡng: phân tích độ nhạy đối với từng ngưỡng.
- Hiệu chỉnh prevalence nếu dân số tham chiếu khác dân số nghiên cứu: {rhi}
"""),
    ]


def _sap_sr_ma(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Tổng hợp định lượng (Meta-analysis)", f"""
- **Mô hình:** Hiệu ứng ngẫu nhiên (DerSimonian-Laird) nếu I² > 50%; fixed-effects nếu I² ≤ 25%.
- **Chỉ số hiệu ứng:** {rhi} (OR / RR / MD / SMD — PI ấn định).
- **Đánh giá không đồng nhất:** Q-test, I², τ².
- **Phân tích subgroup định trước:** {rhi}
- **Meta-regression:** {rhi}
"""),
        SAPSection("SAP-5", "Publication bias", f"""
- Funnel plot + Egger's test (nếu ≥ 10 nghiên cứu).
- Trim-and-fill nếu có bất cân xứng.
"""),
        SAPSection("SAP-6", "Phân tích độ nhạy", f"""
- Loại lần lượt từng nghiên cứu (leave-one-out).
- Phân tích giới hạn nghiên cứu chất lượng cao.
- Ngưỡng I² để gộp: {rhi}
"""),
    ]


def _sap_qualitative(rhi: str) -> List[SAPSection]:
    return _general_sections(rhi) + [
        SAPSection("SAP-4", "Phương pháp phân tích định tính", f"""
- Phương pháp: {rhi} (Thematic analysis / Framework / Grounded theory / Phenomenology).
- Phần mềm hỗ trợ: {rhi} (NVivo / Atlas.ti / MAXQDA / thủ công).
- Quy trình mã hóa: {rhi} (mã hóa độc lập → thống nhất → kiểm tra liên quan người mã).
- Kappa liên người mã: {rhi} (nếu áp dụng).
"""),
        SAPSection("SAP-5", "Độ tin cậy (Trustworthiness)", f"""
- Credibility: member checking, prolonged engagement.
- Transferability: mô tả dày (thick description).
- Dependability: audit trail.
- Confirmability: reflexivity log.
- Phương pháp kiểm tra: {rhi}
"""),
    ]


_SAP_MAP: Dict[StudyType, object] = {
    StudyType.CROSS_SECTIONAL: _sap_cross_sectional,
    StudyType.COHORT: _sap_cohort,
    StudyType.CASE_CONTROL: _sap_case_control,
    StudyType.RCT: _sap_rct,
    StudyType.DIAGNOSTIC: _sap_diagnostic,
    StudyType.SR_MA: _sap_sr_ma,
    StudyType.QUALITATIVE: _sap_qualitative,
}


def build_sap_draft(study_type: StudyType, version: str = "0.1.0") -> SAPDraft:
    """Xây dựng SAP draft. Mọi thông số là REQUIRE_HUMAN_INPUT."""
    fn = _SAP_MAP.get(study_type)
    if fn is None:
        raise ValueError(f"StudyType không hỗ trợ: {study_type}")
    rhi = REQUIRE_HUMAN_INPUT_MARKER
    sections = fn(rhi)
    return SAPDraft(
        study_type=study_type.value,
        version=version,
        sections=sections,
        lock_reminder=(
            f"SAP PHẢI được PI ký duyệt và khóa (G4) TRƯỚC KHI bất kỳ người nào xem "
            f"dữ liệu nghiên cứu. Thay đổi sau khi xem dữ liệu = post-hoc, phải khai báo rõ. "
            f"{rhi}: Ghi ngày khóa, tên PI, chữ ký."
        ),
    )
