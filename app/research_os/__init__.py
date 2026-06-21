"""Research Operating System V7 — public API.

Import từ đây để truy cập tất cả module research_os.
"""
from app.research_os.causal_inference import CausalPlan, causal_design_warning, design_allows_causal
from app.research_os.data_lock import DataLockRecord, lock_dataset, verify_dataset_hash
from app.research_os.data_quality_firewall import DataQualityReport, run_quality_firewall
from app.research_os.design_router import route_design, route_design_with_confidence
from app.research_os.instrument_mapping import InstrumentMap, missing_instrument_mappings
from app.research_os.methods_review_workflow import MethodsReview, required_method_reviews
from app.research_os.pilot import (
    ResearchPilotGateInput,
    ResearchPilotReport,
    ResearchTraceabilityChain,
    evaluate_researchos_pilot,
)
from app.research_os.project_registry import (
    ProjectRegistry,
    ResearchProject,
    ResearchProjectStatus,
)
from app.research_os.protocol_compiler import ProtocolDraft, compile_protocol
from app.research_os.reporting_guideline_mapper import (
    GUIDELINE_BY_DESIGN,
    reporting_guideline_for_design,
    reporting_guidelines_all,
)
from app.research_os.reproducibility_runner import ReproducibilityResult, compare_result_hash
from app.research_os.research_health_score import ResearchHealthScore, calculate_research_health_score
from app.research_os.sap_engine import SapStatus, StatisticalAnalysisPlan, create_sap, lock_sap
from app.research_os.study_traceability_matrix import (
    TraceabilityRow,
    build_traceability_matrix,
    validate_traceability,
)
from app.research_os.variable_dictionary import VariableDefinition, validate_variable_dictionary

__all__ = [
    # project_registry
    "ProjectRegistry", "ResearchProject", "ResearchProjectStatus",
    # sap_engine
    "StatisticalAnalysisPlan", "SapStatus", "create_sap", "lock_sap",
    # study_traceability_matrix
    "TraceabilityRow", "validate_traceability", "build_traceability_matrix",
    # design_router
    "route_design", "route_design_with_confidence",
    # reporting_guideline_mapper
    "reporting_guideline_for_design", "reporting_guidelines_all", "GUIDELINE_BY_DESIGN",
    # data_lock
    "DataLockRecord", "lock_dataset", "verify_dataset_hash",
    # data_quality_firewall
    "DataQualityReport", "run_quality_firewall",
    # causal_inference
    "CausalPlan", "design_allows_causal", "causal_design_warning",
    # methods_review_workflow
    "MethodsReview", "required_method_reviews",
    # instrument_mapping
    "InstrumentMap", "missing_instrument_mappings",
    # variable_dictionary
    "VariableDefinition", "validate_variable_dictionary",
    # protocol_compiler
    "ProtocolDraft", "compile_protocol",
    # reproducibility_runner
    "ReproducibilityResult", "compare_result_hash",
    # research_health_score
    "ResearchHealthScore", "calculate_research_health_score",
    # pilot
    "ResearchTraceabilityChain", "ResearchPilotGateInput",
    "ResearchPilotReport", "evaluate_researchos_pilot",
]
