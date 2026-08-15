"""
artifact_template_engine — Template DRAFT deterministic (V4.3.2, Phase E).

13 loại artifact. KHÔNG số liệu nghiên cứu thật, KHÔNG kết quả, KHÔNG citation
chưa xác minh. Chỗ thiếu → REQUIRE_HUMAN_INPUT / REQUIRE_HUMAN_REVIEW. Sample size
CHỈ tạo assumption template (không tự tính). OFFLINE · deterministic · synthetic.
"""

from __future__ import annotations

from typing import List

from research_studio.project_schema import ResearchProject
from research_studio.research_preflight import scan_unsafe_content
from research_studio.study_type_router import get_template

REQUIRE_INPUT = "REQUIRE_HUMAN_INPUT"
REQUIRE_REVIEW = "REQUIRE_HUMAN_REVIEW"
CONTENT_BLOCKED = "BLOCKED_UNSAFE_CONTENT"

# 13 loại artifact (Phase E).
TEMPLATE_TYPES: List[str] = [
    "RESEARCH_BRIEF_DRAFT",
    "PROTOCOL_DRAFT",
    "EVIDENCE_PLAN_DRAFT",
    "METHODS_SAMPLE_SIZE_DRAFT",
    "CRF_DRAFT",
    "DATA_DICTIONARY_DRAFT",
    "SAP_DRAFT",
    "SYNTHETIC_ANALYSIS_READINESS_DRAFT",
    "MANUSCRIPT_OUTLINE_DRAFT",
    "REPORTING_CHECKLIST_DRAFT",
    "GOVERNANCE_PACK_DRAFT",
    "CAPA_REGISTER_DRAFT",
    "REVIEW_CHECKLIST_DRAFT",
]


def _common_disclaimer() -> dict:
    return {
        "draft_only": True,
        "human_review_required": True,
        "disclaimer": "DRAFT synthetic — Cần bác sĩ/PI kiểm chứng. NO-GO.",
        "no_real_data": True,
        "no_unverified_citations": True,
    }


def render(artifact_type: str, project: ResearchProject) -> dict:
    """Trả body template (dict) cho artifact_type theo project. KHÔNG bịa số liệu.

    Defense-in-depth (audit 2026-07-10): trên default path (workflow_runner.py),
    project đã qua project_intake + research_preflight trước khi tới đây. Quét
    lại ở đây để render() tự bảo vệ khi bị gọi TRỰC TIẾP (bỏ qua 2 lớp trên) —
    không copy title/clinical_question/PICO/objectives/outcomes chưa quét vào
    artifact body.
    """
    if artifact_type not in TEMPLATE_TYPES:
        raise KeyError(f"UNKNOWN_TEMPLATE_TYPE:{artifact_type}")
    unsafe_reasons = scan_unsafe_content(project)
    if unsafe_reasons:
        body = {"artifact_type": artifact_type, CONTENT_BLOCKED: True,
                "unsafe_content_reasons": unsafe_reasons}
        body["_meta"] = _common_disclaimer()
        return body
    body = _RENDERERS[artifact_type](project)
    body["_meta"] = _common_disclaimer()
    body["artifact_type"] = artifact_type
    return body


# ── Renderers (synthetic, placeholder-driven) ─────────────────────────────────

def _brief(p: ResearchProject) -> dict:
    return {
        "title": p.title,
        "clinical_question": p.clinical_question,
        "pico_or_equivalent": p.pico_or_equivalent,
        "objectives": p.objectives,
        "outcomes": p.outcomes,
        "evidence_gap": REQUIRE_INPUT,
        "finer_feasibility": {k: REQUIRE_INPUT for k in
                              ("Feasible", "Interesting", "Novel", "Ethical", "Relevant")},
        "proposed_study_type": p.study_type.value,
    }


def _protocol(p: ResearchProject) -> dict:
    t = get_template(p.study_type)
    return {
        "background": REQUIRE_INPUT,
        "objectives": p.objectives,
        "hypotheses": REQUIRE_INPUT,
        "design": p.study_type.value,
        "required_sections": {s: REQUIRE_INPUT for s in t.required_sections},
        "inclusion_exclusion": REQUIRE_INPUT,
        "variables": REQUIRE_INPUT,
        "outcomes": p.outcomes,
        "data_collection_procedure": REQUIRE_INPUT,
        "risk_of_bias": {b: REQUIRE_REVIEW for b in t.bias_checklist},
        "ethics_section": REQUIRE_REVIEW,
    }


def _evidence_plan(p: ResearchProject) -> dict:
    return {
        "search_questions": [p.clinical_question],
        "expected_sources": ["PubMed", "Cochrane", "Europe PMC"],
        "source_selection_criteria": REQUIRE_INPUT,
        "evidence_hierarchy": ["SR/MA", "RCT", "Cohort", "Case-control", "Cross-sectional"],
        "evidence_table_schema": ["author_year", "design", "n", "effect", "ci", "rob", "pmid_doi"],
        "citation_integrity": REQUIRE_REVIEW,
        "retraction_check": REQUIRE_REVIEW,
    }


def _methods_sample(p: ResearchProject) -> dict:
    # Sample size: CHỈ assumption template — KHÔNG tự tính.
    return {
        "design_decision": p.study_type.value,
        "sampling_strategy": REQUIRE_INPUT,
        "variable_operationalization": REQUIRE_INPUT,
        "confounding_plan": REQUIRE_INPUT,
        "missing_data_plan": REQUIRE_INPUT,
        "sample_size_assumptions_template": {
            "alpha": REQUIRE_INPUT, "power": REQUIRE_INPUT,
            "effect_size": REQUIRE_INPUT, "event_rate": REQUIRE_INPUT,
            "sd": REQUIRE_INPUT, "dropout": REQUIRE_INPUT, "design_effect": REQUIRE_INPUT,
        },
        "computed_sample_size": REQUIRE_INPUT,   # KHÔNG tự tính khi thiếu assumption
        "note": "Sample size KHÔNG tự tính; cần người ấn định assumption.",
    }


def _crf(p: ResearchProject) -> dict:
    return {
        "crf_structure": ["screening", "baseline", "follow_up"],
        "crf_variables": REQUIRE_INPUT,
        "coding_rules": REQUIRE_INPUT,
        "allowable_values": REQUIRE_INPUT,
        "validation_rules": REQUIRE_INPUT,
        "provenance": REQUIRE_REVIEW,
        "data_quality_checks": REQUIRE_INPUT,
    }


def _data_dictionary(p: ResearchProject) -> dict:
    return {
        "variables": REQUIRE_INPUT,
        "types_units": REQUIRE_INPUT,
        "allowable_values": REQUIRE_INPUT,
        "coding": REQUIRE_INPUT,
        "missing_codes": REQUIRE_INPUT,
        "provenance": REQUIRE_REVIEW,
    }


def _sap(p: ResearchProject) -> dict:
    return {
        "population_definitions": REQUIRE_INPUT,
        "primary_outcome": p.outcomes[0] if p.outcomes else REQUIRE_INPUT,
        "secondary_outcomes": p.outcomes[1:] or REQUIRE_INPUT,
        "descriptive_analysis": REQUIRE_INPUT,
        "comparative_analysis": REQUIRE_INPUT,
        "regression_plan": REQUIRE_INPUT,
        "subgroup_plan": REQUIRE_INPUT,
        "sensitivity_analysis": REQUIRE_INPUT,
        "missing_data": REQUIRE_INPUT,
        "multiplicity": REQUIRE_INPUT,
        "table_shells": REQUIRE_INPUT,
        "figure_shells": REQUIRE_INPUT,
        "analysis_outcomes": p.outcomes,
    }


def _analysis_readiness(p: ResearchProject) -> dict:
    return {
        "mode": "SYNTHETIC_ONLY",
        "real_analysis": "BLOCKED_V4_3_2",
        "execution_checklist": REQUIRE_REVIEW,
        "table_shells": REQUIRE_INPUT,
        "figure_shells": REQUIRE_INPUT,
        "note": "Chỉ kiểm tra sẵn sàng bằng fixture synthetic; KHÔNG phân tích dữ liệu thật.",
    }


def _manuscript(p: ResearchProject) -> dict:
    t = get_template(p.study_type)
    return {
        "reporting_checklist": t.reporting_checklist,
        "imrad_outline": {s: REQUIRE_INPUT for s in
                          ("Introduction", "Methods", "Results", "Discussion")},
        "authorship_integrity": REQUIRE_REVIEW,
        "citation_verification_status": REQUIRE_REVIEW,
        "limitations": REQUIRE_INPUT,
        "transparency_statement": REQUIRE_REVIEW,
        "submission": "BLOCKED_V4_3_2",
    }


def _reporting_checklist(p: ResearchProject) -> dict:
    t = get_template(p.study_type)
    return {
        "checklist": t.reporting_checklist,
        "items": {s: REQUIRE_REVIEW for s in t.required_sections},
        "completeness": REQUIRE_REVIEW,
    }


def _governance_pack(p: ResearchProject) -> dict:
    return {
        "ethics_readiness_checklist": REQUIRE_REVIEW,
        "protocol_deviation_log": REQUIRE_INPUT,
        "decision_log": REQUIRE_INPUT,
        "version_control_register": REQUIRE_INPUT,
        "audit_trail_review": REQUIRE_REVIEW,
        "ethics_submission": "BLOCKED_V4_3_2",
    }


def _capa_register(p: ResearchProject) -> dict:
    return {
        "findings": REQUIRE_INPUT,
        "corrective_actions": REQUIRE_INPUT,
        "preventive_actions": REQUIRE_INPUT,
        "owner": REQUIRE_INPUT,
        "status": REQUIRE_REVIEW,
    }


def _review_checklist(p: ResearchProject) -> dict:
    return {
        "consistency_checks": [f"G-R{i}" for i in range(1, 11)],
        "missing_fields_summary": REQUIRE_INPUT,
        "human_reviewer_role": REQUIRE_INPUT,
        "decision": REQUIRE_REVIEW,
    }


_RENDERERS = {
    "RESEARCH_BRIEF_DRAFT": _brief,
    "PROTOCOL_DRAFT": _protocol,
    "EVIDENCE_PLAN_DRAFT": _evidence_plan,
    "METHODS_SAMPLE_SIZE_DRAFT": _methods_sample,
    "CRF_DRAFT": _crf,
    "DATA_DICTIONARY_DRAFT": _data_dictionary,
    "SAP_DRAFT": _sap,
    "SYNTHETIC_ANALYSIS_READINESS_DRAFT": _analysis_readiness,
    "MANUSCRIPT_OUTLINE_DRAFT": _manuscript,
    "REPORTING_CHECKLIST_DRAFT": _reporting_checklist,
    "GOVERNANCE_PACK_DRAFT": _governance_pack,
    "CAPA_REGISTER_DRAFT": _capa_register,
    "REVIEW_CHECKLIST_DRAFT": _review_checklist,
}


def human_markers(body: dict) -> List[str]:
    """Liệt kê đường dẫn chứa REQUIRE_HUMAN_* (để tổng hợp missing fields)."""
    out: List[str] = []

    def walk(prefix, v):
        if isinstance(v, str) and v in (REQUIRE_INPUT, REQUIRE_REVIEW):
            out.append(f"{prefix}={v}")
        elif isinstance(v, dict):
            for k, vv in v.items():
                walk(f"{prefix}.{k}" if prefix else k, vv)
        elif isinstance(v, list):
            for i, vv in enumerate(v):
                walk(f"{prefix}[{i}]", vv)

    walk("", body)
    return out
