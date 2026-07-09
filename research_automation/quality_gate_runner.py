"""
quality_gate_runner — Chạy G-R1..G-R10 → quality report (V4.3.2).

Tái dùng research_studio.research_quality_checks. KHÔNG bịa số liệu: sample-size
assumptions để TRỐNG → G-R3 trả REQUIRE_HUMAN_REVIEW (đúng ngữ nghĩa). OFFLINE.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional

from research_studio import research_quality_checks as q
from research_studio.project_schema import ResearchProject
from research_studio.research_quality_checks import GateResult, ResearchGateDecision


@dataclasses.dataclass
class QualityReport:
    project_id: str
    results: List[GateResult]
    blocks: List[str]
    reviews: List[str]
    overall: str            # PASS | REVIEW_REQUIRED | BLOCK

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "overall": self.overall,
            "gates": [{"gate_id": r.gate_id, "decision": r.decision.value,
                       "reason_code": r.reason_code} for r in self.results],
            "blocks": self.blocks,
            "reviews": self.reviews,
        }


def synthetic_complete_inputs(project: ResearchProject) -> Dict[str, dict]:
    """
    Bộ input synthetic 'đầy đủ' để QA — TRỪ sample-size assumptions (để trống có
    chủ ý → G-R3 REVIEW, vì không được tự bịa assumption).
    """
    outcomes = project.outcomes or ["outcome-A"]
    return {
        "methods": {"design": project.study_type.value},  # KHÔNG có sample_size_assumptions
        "sap": {"primary_outcome": outcomes[0], "analysis_outcomes": list(outcomes)},
        "crf": {"crf_variables": ["age", "outcome_var"],
                "data_dictionary": {"age": {}, "outcome_var": {}}},
        "reporting": {"sections_addressed": _all_sections(project)},
        "output": {"summary": "synthetic clean draft", "source_pmid": "PMID:0000000"},
    }


def _all_sections(project: ResearchProject) -> list:
    from research_studio.study_type_router import get_template
    return list(get_template(project.study_type).required_sections)


def run_all(project: ResearchProject, inputs: Optional[Dict[str, dict]] = None) -> QualityReport:
    """Chạy 10 gate; tổng hợp. inputs mặc định = synthetic_complete_inputs."""
    inp = inputs or synthetic_complete_inputs(project)
    methods = inp.get("methods", {})
    sap = inp.get("sap", {})
    crf = inp.get("crf", {})
    reporting = inp.get("reporting", {})
    output = inp.get("output", {})

    results: List[GateResult] = [
        q.gr1_question_objectives(project),
        q.gr2_design_method(project, methods),
        q.gr3_variables_outcomes_analysis(project, sap, methods),
        q.gr4_crf_data_dictionary(crf),
        q.gr5_sap_protocol(project, sap),
        q.gr6_reporting_completeness(project, reporting),
        q.gr7_citation_retraction(output),
        q.gr8_no_fabrication(output),
        q.gr9_no_pii_no_real_data(output),
        q.gr10_human_review({"human_review_required": True,
                             "review_status": "PENDING_HUMAN_REVIEW"}),
    ]
    blocks = [r.reason_code for r in results if r.decision == ResearchGateDecision.BLOCK]
    reviews = [r.reason_code for r in results
               if r.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW]
    if blocks:
        overall = "BLOCK"
    elif reviews:
        overall = "REVIEW_REQUIRED"
    else:
        overall = "PASS"
    return QualityReport(project.project_id, results, blocks, reviews, overall)
