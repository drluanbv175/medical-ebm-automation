"""
research_preflight — Preflight chuẩn mực trước khi tự động chạy đề tài y khoa.

Gate này chạy offline, không gọi mạng, không dùng dữ liệu thật. Mục tiêu là chặn
đề tài thiếu cấu trúc tối thiểu trước khi pipeline sinh artifact, đồng thời trả
danh sách review_items để người thật/Claude tiếp tục hoàn thiện mà không bịa dữ liệu.
"""

from __future__ import annotations

import dataclasses
from typing import List

from runtime.data_boundary import DataBoundary

from .project_schema import ResearchProject, StudyType, validate_project
from .research_quality_checks import ResearchGateDecision, gr1_question_objectives
from .study_type_router import get_template

# Phòng thủ theo lớp (defense-in-depth): quét PII / real-data / production
# connector NGAY tại cổng preflight, không chỉ ở research_automation.project_intake.
# Lý do: run_project()/evaluate_research_preflight() có thể được gọi TRỰC TIẾP
# (bỏ qua intake) — nếu preflight không tự bảo vệ, một caller mới bất kỳ sẽ đưa
# nội dung PII/dữ liệu thật vào pipeline. Guard này khiến cổng vào tự thực thi
# đúng lời cam kết ở docstring ("không dùng dữ liệu thật"). OFFLINE, không network.
_boundary = DataBoundary()


_CORE_KEYS_BY_STUDY_TYPE = {
    StudyType.CROSS_SECTIONAL: ("P", "O"),
    StudyType.COHORT: ("P", "O"),
    StudyType.CASE_CONTROL: ("P", "O"),
    StudyType.RCT: ("P", "O"),
    StudyType.DIAGNOSTIC_ACCURACY: ("P", "O"),
    StudyType.SYSTEMATIC_REVIEW: ("P", "O"),
    StudyType.QUALITATIVE: ("P", "O"),
}

_RECOMMENDED_KEYS_BY_STUDY_TYPE = {
    StudyType.CROSS_SECTIONAL: ("P", "E", "O"),
    StudyType.COHORT: ("P", "E", "C", "O"),
    StudyType.CASE_CONTROL: ("P", "E", "C", "O"),
    StudyType.RCT: ("P", "I", "C", "O"),
    StudyType.DIAGNOSTIC_ACCURACY: ("P", "Index test", "Reference standard", "O"),
    StudyType.SYSTEMATIC_REVIEW: ("P", "I", "C", "O"),
    StudyType.QUALITATIVE: ("P", "E", "O"),
}


@dataclasses.dataclass(frozen=True)
class ResearchPreflightReport:
    project_id: str
    decision: ResearchGateDecision
    reason_codes: List[str]
    review_items: List[str]
    reporting_checklist: str
    minimum_artifact_set: List[str]
    required_sections: List[str]
    human_review_requirements: List[str]
    prohibited_shortcuts: List[str]

    @property
    def passed(self) -> bool:
        return self.decision == ResearchGateDecision.PASS

    def to_dict(self) -> dict:
        data = dataclasses.asdict(self)
        data["decision"] = self.decision.value
        data["passed"] = self.passed
        return data


def _missing_keys(project: ResearchProject, keys: tuple[str, ...]) -> list[str]:
    present = {
        str(key).strip().lower()
        for key, value in project.pico_or_equivalent.items()
        if str(key).strip() and str(value).strip()
    }
    return [key for key in keys if key.lower() not in present]


def scan_unsafe_content(project: ResearchProject) -> list[str]:
    """Quét các field VĂN BẢN TỰ DO của đề tài tìm PII / dữ liệu thật / connector
    production. Trả danh sách reason_code (rỗng = sạch). Đây là lưới an toàn ĐỘC
    LẬP với project_intake — bảo đảm dù gọi thẳng preflight (hoặc bất kỳ entry
    point nào khác trên ResearchProject) vẫn không lọt PII.
    KHÔNG log nội dung quét (tránh rò); chỉ trả mã lý do đã rút gọn.

    Public — tái dùng ở mọi entry point nhận ResearchProject trực tiếp (audit
    2026-07-10: quality_gate_runner.run_all(), artifact_template_engine.render(),
    ProjectRegistry.add() KHÔNG tự quét, chỉ project_intake/preflight có).
    """
    # Chỉ gom field ngữ nghĩa tự do — nơi dữ liệu bệnh nhân thật có thể rò. KHÔNG
    # gom project_id/enum trạng thái (định danh cấu trúc, dễ trùng chuỗi số vô hại).
    scannable = {
        "title": project.title,
        "research_domain": project.research_domain,
        "clinical_question": project.clinical_question,
        "principal_investigator": project.principal_investigator,
        "pico_or_equivalent": project.pico_or_equivalent,
        "objectives": project.objectives,
        "outcomes": project.outcomes,
    }
    reasons: list[str] = []
    pii, pii_reason = _boundary.check_pii_in_output(scannable)
    if pii:
        reasons.append(f"PII_DETECTED:{pii_reason}")
    conn, conn_reason = _boundary.check_production_connector(scannable)
    if conn:
        reasons.append(f"PRODUCTION_CONNECTOR:{conn_reason}")
    raw, raw_reason = _boundary.check_raw_data_write(scannable)
    if raw:
        reasons.append(f"RAW_DATA_WRITE:{raw_reason}")
    return reasons


def evaluate_research_preflight(
    project: ResearchProject,
    *,
    full_registry=None,
    draft_registry=None,
) -> ResearchPreflightReport:
    """Đánh giá đề tài trước khi chạy WP automation.

    BLOCK: lỗi schema, thiếu câu hỏi/objectives/outcomes, thiếu core P/O,
    hoặc ma trận agent không hợp lệ.
    PASS: đủ điều kiện sinh DRAFT synthetic, nhưng vẫn trả review_items để
    hoàn thiện theo checklist báo cáo và human review.
    """
    template = get_template(project.study_type)
    reasons: list[str] = []
    review_items: list[str] = []

    schema_issues = validate_project(project)
    reasons.extend(f"SCHEMA:{issue}" for issue in schema_issues)

    # Lưới an toàn THỨ HAI (defense-in-depth): PII / dữ liệu thật / connector.
    reasons.extend(scan_unsafe_content(project))

    q_gate = gr1_question_objectives(project)
    if q_gate.decision == ResearchGateDecision.BLOCK:
        reasons.append(f"{q_gate.gate_id}:{q_gate.reason_code}")

    core_missing = _missing_keys(project, _CORE_KEYS_BY_STUDY_TYPE[project.study_type])
    if core_missing:
        reasons.append("PICO_CORE_MISSING:" + ",".join(core_missing))

    recommended_missing = _missing_keys(
        project,
        _RECOMMENDED_KEYS_BY_STUDY_TYPE[project.study_type],
    )
    for key in recommended_missing:
        review_items.append(f"PICO_RECOMMENDED_FIELD_REVIEW:{key}")

    if full_registry is not None and draft_registry is not None:
        # SỬA 2026-07-08: import lazy (không phải top-level) để phá vòng lặp
        # import — gate_agent_matrix → research_workflow → research_preflight
        # → gate_agent_matrix — vòng này làm ImportError "partially initialized
        # module" mỗi khi bất kỳ module nào trong 3 module trên được import
        # trước tiên (phát hiện qua kiểm định đối kháng, chặn 3 file test).
        from .gate_agent_matrix import build_gate_agent_matrix
        matrix = build_gate_agent_matrix(
            full_registry=full_registry,
            draft_registry=draft_registry,
            artifacts=(),
            project_id=project.project_id,
        )
        if matrix.decision == ResearchGateDecision.BLOCK:
            reasons.append("AGENT_MATRIX_PRECHECK:" + ",".join(matrix.reason_codes))

    for section in template.required_sections:
        review_items.append(f"REPORTING_SECTION_REQUIRED:{section}")
    for requirement in template.human_review_requirements:
        review_items.append(f"HUMAN_REVIEW_REQUIRED:{requirement}")
    for shortcut in template.prohibited_shortcuts:
        review_items.append(f"PROHIBITED_SHORTCUT:{shortcut}")

    decision = ResearchGateDecision.BLOCK if reasons else ResearchGateDecision.PASS
    return ResearchPreflightReport(
        project_id=project.project_id,
        decision=decision,
        reason_codes=reasons,
        review_items=review_items,
        reporting_checklist=template.reporting_checklist,
        minimum_artifact_set=list(template.minimum_artifact_set),
        required_sections=list(template.required_sections),
        human_review_requirements=list(template.human_review_requirements),
        prohibited_shortcuts=list(template.prohibited_shortcuts),
    )
