"""
study_type_router — Template tối thiểu theo loại nghiên cứu (V4.3, Phase D).

Mỗi template: required_sections, required_outcomes, bias_checklist,
reporting_checklist, minimum_artifact_set, prohibited_shortcuts,
human_review_requirements. KHÔNG bịa số liệu/ngưỡng.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List

from .project_schema import StudyType


@dataclasses.dataclass
class StudyTypeTemplate:
    study_type: StudyType
    reporting_checklist: str
    required_sections: List[str]
    required_outcomes: List[str]
    bias_checklist: List[str]
    minimum_artifact_set: List[str]
    prohibited_shortcuts: List[str]
    human_review_requirements: List[str]


_COMMON_PROHIBITED = [
    "KHÔNG bịa số liệu/kết quả/trích dẫn",
    "KHÔNG dùng dữ liệu thật/PII",
    "KHÔNG tự nộp ethics/đề cương/bài báo",
    "KHÔNG bỏ qua human review",
]
_COMMON_HUMAN_REVIEW = [
    "PI/bác sĩ phải duyệt mọi DRAFT trước khi dùng ngoài",
    "Kiểm chứng PMID/DOI thủ công",
    "Xác nhận đạo đức/đăng ký trước thu thập dữ liệu thật",
]

_TEMPLATES: Dict[StudyType, StudyTypeTemplate] = {
    StudyType.CROSS_SECTIONAL: StudyTypeTemplate(
        study_type=StudyType.CROSS_SECTIONAL,
        reporting_checklist="STROBE",
        required_sections=["Background", "Objectives", "Design (cross-sectional)",
                            "Setting", "Participants", "Variables", "Measurement",
                            "Bias", "Statistical methods", "Limitations"],
        required_outcomes=["Prevalence/association outcome (synthetic)"],
        bias_checklist=["Selection bias", "Information/measurement bias",
                        "Confounding", "Non-response bias"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "METHODS_SAMPLE_SIZE_DRAFT", "CRF_DRAFT",
                              "SAP_DRAFT", "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG suy diễn nhân quả từ cắt ngang"],
        human_review_requirements=_COMMON_HUMAN_REVIEW,
    ),
    StudyType.COHORT: StudyTypeTemplate(
        study_type=StudyType.COHORT,
        reporting_checklist="STROBE",
        required_sections=["Background", "Objectives", "Design (cohort)", "Exposure",
                            "Follow-up", "Outcomes", "Confounding", "Statistical methods",
                            "Loss to follow-up", "Limitations"],
        required_outcomes=["Incidence/relative risk or hazard ratio (synthetic)"],
        bias_checklist=["Selection bias", "Loss-to-follow-up bias", "Confounding",
                        "Immortal time bias", "Misclassification of exposure"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "EVIDENCE_PLAN_DRAFT", "METHODS_SAMPLE_SIZE_DRAFT",
                              "CRF_DRAFT", "SAP_DRAFT", "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG bỏ qua kế hoạch mất dấu theo dõi"],
        human_review_requirements=_COMMON_HUMAN_REVIEW,
    ),
    StudyType.CASE_CONTROL: StudyTypeTemplate(
        study_type=StudyType.CASE_CONTROL,
        reporting_checklist="STROBE",
        required_sections=["Background", "Objectives", "Design (case-control)",
                            "Case definition", "Control selection", "Exposure ascertainment",
                            "Matching", "Confounding", "Statistical methods", "Limitations"],
        required_outcomes=["Odds ratio (synthetic)"],
        bias_checklist=["Recall bias", "Selection bias (control choice)",
                        "Confounding", "Matching adequacy"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "METHODS_SAMPLE_SIZE_DRAFT", "CRF_DRAFT", "SAP_DRAFT",
                              "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG chọn control không so sánh được"],
        human_review_requirements=_COMMON_HUMAN_REVIEW,
    ),
    StudyType.RCT: StudyTypeTemplate(
        study_type=StudyType.RCT,
        reporting_checklist="CONSORT",
        required_sections=["Background", "Objectives", "Trial design", "Randomization",
                            "Allocation concealment", "Blinding", "Interventions",
                            "Primary/secondary outcomes", "Sample size", "Statistical methods",
                            "Harms", "Limitations"],
        required_outcomes=["Primary efficacy outcome (synthetic)", "Safety outcome (synthetic)"],
        bias_checklist=["Randomization (RoB2 D1)", "Deviations from intervention (D2)",
                        "Missing outcome data (D3)", "Measurement of outcome (D4)",
                        "Selective reporting (D5)"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "METHODS_SAMPLE_SIZE_DRAFT", "CRF_DRAFT", "SAP_DRAFT",
                              "GOVERNANCE_PACK_DRAFT", "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG phân tích trước khi khóa SAP",
                                                   "KHÔNG bỏ đăng ký thử nghiệm"],
        human_review_requirements=_COMMON_HUMAN_REVIEW + ["Bắt buộc đăng ký thử nghiệm trước"],
    ),
    StudyType.DIAGNOSTIC_ACCURACY: StudyTypeTemplate(
        study_type=StudyType.DIAGNOSTIC_ACCURACY,
        reporting_checklist="STARD",
        required_sections=["Background", "Objectives", "Index test", "Reference standard",
                            "Participants", "Test methods", "Analysis (Se/Sp/LR)",
                            "Flow diagram", "Limitations"],
        required_outcomes=["Sensitivity/Specificity/LR (synthetic)"],
        bias_checklist=["QUADAS-2 patient selection", "Index test", "Reference standard",
                        "Flow and timing"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "METHODS_SAMPLE_SIZE_DRAFT", "CRF_DRAFT", "SAP_DRAFT",
                              "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG dùng reference standard không độc lập"],
        human_review_requirements=_COMMON_HUMAN_REVIEW,
    ),
    StudyType.SYSTEMATIC_REVIEW: StudyTypeTemplate(
        study_type=StudyType.SYSTEMATIC_REVIEW,
        reporting_checklist="PRISMA",
        required_sections=["Background", "Objectives (PICO)", "Eligibility criteria",
                            "Information sources", "Search strategy", "Selection process",
                            "Risk of bias assessment", "Synthesis methods", "Limitations"],
        required_outcomes=["Pooled effect estimate (synthetic)"],
        bias_checklist=["AMSTAR-2 critical domains", "RoB of included studies",
                        "Publication bias", "Heterogeneity assessment"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "EVIDENCE_PLAN_DRAFT", "SAP_DRAFT", "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG gộp ép khi không đồng nhất",
                                                   "KHÔNG bỏ đăng ký PROSPERO"],
        human_review_requirements=_COMMON_HUMAN_REVIEW + ["Đăng ký giao thức (PROSPERO)"],
    ),
    StudyType.QUALITATIVE: StudyTypeTemplate(
        study_type=StudyType.QUALITATIVE,
        reporting_checklist="COREQ",
        required_sections=["Background", "Objectives", "Methodological approach",
                            "Sampling (purposive)", "Data collection", "Saturation",
                            "Analysis (thematic/framework)", "Trustworthiness", "Reflexivity"],
        required_outcomes=["Themes/categories (synthetic, no participant quotes)"],
        bias_checklist=["Credibility", "Transferability", "Dependability", "Confirmability"],
        minimum_artifact_set=["RESEARCH_BRIEF_DRAFT", "PROTOCOL_DRAFT",
                              "EVIDENCE_PLAN_DRAFT", "REPORTING_CHECKLIST_DRAFT"],
        prohibited_shortcuts=_COMMON_PROHIBITED + ["KHÔNG trích lời người tham gia thật"],
        human_review_requirements=_COMMON_HUMAN_REVIEW,
    ),
}


def get_template(study_type: StudyType) -> StudyTypeTemplate:
    if study_type not in _TEMPLATES:
        raise KeyError(f"NO_TEMPLATE_FOR_STUDY_TYPE:{study_type}")
    return _TEMPLATES[study_type]


def reporting_checklist_for(study_type: StudyType) -> str:
    return get_template(study_type).reporting_checklist


def all_templates() -> Dict[StudyType, StudyTypeTemplate]:
    return dict(_TEMPLATES)
