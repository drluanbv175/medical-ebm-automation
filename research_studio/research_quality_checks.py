"""
research_quality_checks — Quality gates G-R1..G-R10 cho Research Studio (V4.3).

Gate là HÀM THUẦN trên project/artifacts/output synthetic. Tái dùng
runtime.data_boundary cho PII/fabrication/real-data. Gate fail → giữ safe state,
trả reason_code; KHÔNG tạo artifact final.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import List, Optional

from runtime.data_boundary import DataBoundary

from .project_schema import ResearchProject, StudyType
from .study_type_router import get_template

_boundary = DataBoundary()

# Marker synthetic (chỉ dùng trong fixture để kích hoạt gate; KHÔNG phải dữ liệu thật)
RETRACTION_MARKER = "RETRACTION_MARKER"
REAL_DATA_MARKERS = ("REAL_PATIENT_DATA", "REAL_DATA_MARKER", "LIVE_DATABASE", "EHOSPITAL_CONNECT")


class ResearchGateDecision(str, enum.Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"


@dataclasses.dataclass
class GateResult:
    gate_id: str
    decision: ResearchGateDecision
    reason_code: str
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.decision == ResearchGateDecision.PASS


def _ok(gate_id, reason="OK") -> GateResult:
    return GateResult(gate_id, ResearchGateDecision.PASS, reason)


def _block(gate_id, reason, detail="") -> GateResult:
    return GateResult(gate_id, ResearchGateDecision.BLOCK, reason, detail)


def _review(gate_id, reason, detail="") -> GateResult:
    return GateResult(gate_id, ResearchGateDecision.REQUIRE_HUMAN_REVIEW, reason, detail)


# ── G-R1: research question / objectives consistency ──────────────────────────

def gr1_question_objectives(p: ResearchProject) -> GateResult:
    if not p.clinical_question.strip():
        return _block("G-R1", "MISSING_CLINICAL_QUESTION")
    if not p.objectives:
        return _block("G-R1", "MISSING_OBJECTIVES")
    if not p.outcomes:
        return _block("G-R1", "MISSING_OUTCOMES")
    return _ok("G-R1")


# ── G-R2: study design / method consistency ───────────────────────────────────

def gr2_design_method(p: ResearchProject, methods: dict) -> GateResult:
    declared = methods.get("design")
    if declared is None:
        return _review("G-R2", "METHODS_DESIGN_NOT_DECLARED")
    if str(declared) != p.study_type.value:
        return _block("G-R2", "DESIGN_METHOD_MISMATCH",
                      f"project={p.study_type.value} methods={declared}")
    return _ok("G-R2")


# ── G-R3: variables / outcomes / analysis consistency (+ sample-size) ──────────

def gr3_variables_outcomes_analysis(p: ResearchProject, sap: dict, methods: dict) -> GateResult:
    # Missing sample-size assumptions → REQUIRE_HUMAN_REVIEW (không tự bịa số)
    assumptions = methods.get("sample_size_assumptions")
    if not assumptions:
        return _review("G-R3", "MISSING_SAMPLE_SIZE_ASSUMPTIONS",
                       "Thiếu giả định cỡ mẫu — không tự tính/bịa; cần người ấn định")
    analysis_outcomes = set(sap.get("analysis_outcomes", []))
    if not analysis_outcomes:
        return _block("G-R3", "SAP_HAS_NO_ANALYSIS_OUTCOMES")
    missing = [o for o in p.outcomes if o not in analysis_outcomes]
    if missing:
        return _block("G-R3", "OUTCOME_NOT_IN_ANALYSIS", f"missing={missing}")
    return _ok("G-R3")


# ── G-R4: CRF / data dictionary consistency ───────────────────────────────────

def gr4_crf_data_dictionary(crf: dict) -> GateResult:
    crf_vars = set(crf.get("crf_variables", []))
    dict_vars = set(crf.get("data_dictionary", {}).keys())
    if not crf_vars:
        return _block("G-R4", "CRF_HAS_NO_VARIABLES")
    undefined = crf_vars - dict_vars
    if undefined:
        return _block("G-R4", "CRF_VARS_NOT_IN_DICTIONARY", f"undefined={sorted(undefined)}")
    return _ok("G-R4")


# ── G-R5: SAP / protocol consistency ──────────────────────────────────────────

def gr5_sap_protocol(p: ResearchProject, sap: dict) -> GateResult:
    primary = sap.get("primary_outcome")
    if not primary:
        return _block("G-R5", "SAP_MISSING_PRIMARY_OUTCOME")
    if primary not in p.outcomes:
        return _block("G-R5", "SAP_PRIMARY_NOT_IN_PROTOCOL_OUTCOMES", f"primary={primary}")
    return _ok("G-R5")


# ── G-R6: reporting checklist completeness ────────────────────────────────────

def gr6_reporting_completeness(p: ResearchProject, reporting: dict) -> GateResult:
    template = get_template(p.study_type)
    addressed = set(reporting.get("sections_addressed", []))
    required = set(template.required_sections)
    missing = required - addressed
    if missing:
        return _block("G-R6", "REPORTING_CHECKLIST_INCOMPLETE",
                      f"checklist={template.reporting_checklist} missing={sorted(missing)}")
    return _ok("G-R6")


# ── G-R7: citation / retraction integrity ─────────────────────────────────────

def gr7_citation_retraction(output: dict) -> GateResult:
    text = _boundary._to_scannable(output)
    if RETRACTION_MARKER in text or "retracted" in text.lower():
        return _review("G-R7", "RETRACTION_DETECTED",
                       "Tài liệu nghi bị rút — cần người kiểm chứng trước khi dùng")
    found, reason = _boundary.check_fabricated_citation(output)
    if found:
        return _block("G-R7", f"CITATION_INTEGRITY:{reason}")
    return _ok("G-R7")


# ── G-R8: no fabricated data / results / citations ────────────────────────────

def gr8_no_fabrication(output: dict) -> GateResult:
    found, reason = _boundary.check_fabricated_data(output)
    if found:
        return _block("G-R8", f"FABRICATED_DATA:{reason}")
    found_c, reason_c = _boundary.check_fabricated_citation(output)
    if found_c and "FABRICATED" in reason_c:
        return _block("G-R8", f"FABRICATED_CITATION:{reason_c}")
    return _ok("G-R8")


# ── G-R9: no PII / no real data (conservative block) ──────────────────────────

def gr9_no_pii_no_real_data(output: dict) -> GateResult:
    # Real-data markers → BLOCK
    text = _boundary._to_scannable(output)
    for m in REAL_DATA_MARKERS:
        if m.lower() in text.lower():
            return _block("G-R9", f"REAL_DATA_MARKER:{m}")
    # PII → BLOCK (conservative). LƯU Ý: regex KHÔNG bắt được toàn bộ PII —
    # nguyên tắc bảo thủ: nghi ngờ thì chặn; người duyệt vẫn phải kiểm thủ công.
    pii, reason = _boundary.check_pii_in_output(output)
    if pii:
        return _block("G-R9", f"PII_DETECTED:{reason}")
    return _ok("G-R9")


# ── G-R10: human review required before external use ──────────────────────────

def gr10_human_review(artifact_like) -> GateResult:
    """artifact_like có .human_review_required và .review_status (hoặc dict)."""
    if isinstance(artifact_like, dict):
        hrr = artifact_like.get("human_review_required", False)
        status = artifact_like.get("review_status", "")
    else:
        hrr = getattr(artifact_like, "human_review_required", False)
        status = getattr(getattr(artifact_like, "review_status", None), "value",
                         getattr(artifact_like, "review_status", ""))
    if not hrr:
        return _block("G-R10", "HUMAN_REVIEW_FLAG_MISSING")
    return _ok("G-R10", "PENDING_HUMAN_REVIEW")


# ── Tổng hợp cho output synthetic (G-R7/8/9 chạy chung trên một output) ────────

def safety_gates_on_output(output: dict) -> List[GateResult]:
    """Chạy G-R7/G-R8/G-R9 trên một output synthetic; dùng trong WP dispatch."""
    return [gr8_no_fabrication(output), gr7_citation_retraction(output),
            gr9_no_pii_no_real_data(output)]


def worst_decision(results: List[GateResult]) -> ResearchGateDecision:
    """BLOCK > REQUIRE_HUMAN_REVIEW > PASS."""
    decisions = {r.decision for r in results}
    if ResearchGateDecision.BLOCK in decisions:
        return ResearchGateDecision.BLOCK
    if ResearchGateDecision.REQUIRE_HUMAN_REVIEW in decisions:
        return ResearchGateDecision.REQUIRE_HUMAN_REVIEW
    return ResearchGateDecision.PASS
