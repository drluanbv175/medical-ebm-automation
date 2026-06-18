"""ResearchOS pilot Phase 2B ở mức metadata, không raw patient data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping


@dataclass(frozen=True)
class ResearchTraceabilityChain:
    title: str
    research_questions: List[str]
    objectives: List[str]
    primary_outcomes: List[str]
    secondary_outcomes: List[str]
    variables: List[str]
    questionnaire_items: List[str]
    data_fields: List[str]
    data_dictionary_id: str
    sap_id: str
    syntax_version: str
    expected_tables: List[str]
    results_placeholder: str
    discussion_boundaries: str

    def issues(self) -> List[str]:
        checks = {
            "title": bool(self.title),
            "research_questions": bool(self.research_questions),
            "objectives": bool(self.objectives),
            "primary_outcomes": bool(self.primary_outcomes),
            "variables": bool(self.variables),
            "questionnaire_items": bool(self.questionnaire_items),
            "data_fields": bool(self.data_fields),
            "data_dictionary_id": bool(self.data_dictionary_id),
            "sap_id": bool(self.sap_id),
            "syntax_version": bool(self.syntax_version),
            "expected_tables": bool(self.expected_tables),
            "results_placeholder": bool(self.results_placeholder),
            "discussion_boundaries": bool(self.discussion_boundaries),
        }
        return [name for name, ok in checks.items() if not ok]


@dataclass(frozen=True)
class ResearchPilotGateInput:
    protocol_complete: bool
    instrument_consistent: bool
    dictionary_consistent: bool
    sap_locked: bool
    data_locked: bool
    syntax_versioned: bool
    expected_tables_aligned: bool
    reporting_checklist_ready: bool
    outcomes_have_variables: bool
    tables_within_sap: bool
    dataset_status_clear: bool


@dataclass(frozen=True)
class ResearchPilotReport:
    title: str
    traceability_passed: bool
    gates_passed: bool
    analysis_ready: bool
    issues: List[str] = field(default_factory=list)
    allowed_content: Mapping[str, bool] = field(default_factory=dict)


def evaluate_researchos_pilot(chain: ResearchTraceabilityChain, gates: ResearchPilotGateInput) -> ResearchPilotReport:
    issues = chain.issues()
    gate_checks = {
        "protocol_completeness": gates.protocol_complete,
        "instrument_consistency": gates.instrument_consistent,
        "dictionary_consistency": gates.dictionary_consistent,
        "sap_lock_readiness": gates.sap_locked,
        "data_lock_status": gates.data_locked,
        "syntax_version_status": gates.syntax_versioned,
        "expected_table_alignment": gates.expected_tables_aligned,
        "reporting_checklist_status": gates.reporting_checklist_ready,
        "outcomes_have_variables": gates.outcomes_have_variables,
        "tables_within_sap": gates.tables_within_sap,
        "dataset_status_clear": gates.dataset_status_clear,
    }
    issues.extend(name for name, ok in gate_checks.items() if not ok)
    analysis_ready = all([
        not issues,
        gates.sap_locked,
        gates.data_locked,
        gates.dictionary_consistent,
        gates.outcomes_have_variables,
        gates.tables_within_sap,
        gates.syntax_versioned,
        gates.dataset_status_clear,
    ])
    return ResearchPilotReport(
        title=chain.title,
        traceability_passed=not chain.issues(),
        gates_passed=all(gate_checks.values()),
        analysis_ready=analysis_ready,
        issues=issues,
        allowed_content={
            "title": True,
            "objectives": True,
            "design": True,
            "data_dictionary": True,
            "variable_mapping": True,
            "questionnaire_mapping": True,
            "sap": True,
            "syntax_metadata": True,
            "table_shells": True,
            "data_quality_summary_no_pii": True,
            "raw_dataset": False,
            "patient_identifiers": False,
            "identified_questionnaires": False,
            "spss_with_pii": False,
        },
    )
