"""
V4.3 — Offline Research Studio deterministic tests (20 kịch bản Phase G).

Tất cả synthetic, offline, qua control-plane. KHÔNG API/network/PII/dữ liệu thật.
Test counts KHÔNG hard-code (mỗi kịch bản là test độc lập).
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
"""

from __future__ import annotations

import pytest

from runtime.agent_registry import AgentRegistry, RegistryMode
from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.dispatch_guard import (
    reset_guard_context,
    assert_via_orchestrator,
    DirectRuntimeBypassError,
)
from runtime.mock_agent_runtime import MockAgentRuntime

from research_studio.project_registry import seeded_registry, ProjectRegistry
from research_studio.project_schema import (
    ResearchProject, StudyType, ResearchWorkflowState, ReviewStatus,
    validate_project, is_valid,
)
from research_studio.study_type_router import (
    get_template, all_templates, reporting_checklist_for,
)
from research_studio.artifact_registry import (
    ArtifactRegistry, ResearchArtifact, ArtifactIntegrityError,
)
from research_studio import research_quality_checks as q
from research_studio.research_quality_checks import ResearchGateDecision
from research_studio.research_workflow import (
    WORK_PACKAGES, WP_BY_ID, run_project, run_work_package,
    build_research_registry, build_research_runtime, seed_synthetic_ledger,
    RESEARCH_FIXTURE_CATALOG,
)


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


def _wp_harness():
    return (build_research_registry(), seed_synthetic_ledger(),
            build_research_runtime(), AuditLogger(run_id="AUDIT-T"), ArtifactRegistry())


def _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-001"):
    return ResearchProject(
        project_id=pid, title="[SYNTHETIC] test", principal_investigator="PI-SYNTH-T",
        research_domain="test", study_type=study_type,
        clinical_question="Q synthetic?", pico_or_equivalent={"P": "x", "O": "y"},
        objectives=["obj1"], outcomes=["outcome-A"],
    )


# 1 — schema validation
def test_01_schema_validation():
    assert is_valid(_project())
    bad = _project(); bad.objectives = []
    assert "MISSING_OBJECTIVES" in validate_project(bad)
    bad2 = _project(); bad2.draft_only = False
    assert "DRAFT_ONLY_MUST_BE_TRUE" in validate_project(bad2)
    bad3 = _project(); bad3.principal_investigator = "Nguyễn Văn A"
    assert "PI_LOOKS_LIKE_REAL_NAME_USE_SYNTHETIC_ID" in validate_project(bad3)


# 2 — study-type routing
def test_02_study_type_routing():
    assert len(all_templates()) == 7
    assert reporting_checklist_for(StudyType.RCT) == "CONSORT"
    assert reporting_checklist_for(StudyType.SYSTEMATIC_REVIEW) == "PRISMA"
    assert reporting_checklist_for(StudyType.CROSS_SECTIONAL) == "STROBE"
    for st in StudyType:
        t = get_template(st)
        assert t.required_sections and t.bias_checklist and t.minimum_artifact_set
        assert t.prohibited_shortcuts and t.human_review_requirements


# 3 — protocol/objective consistency
def test_03_protocol_objective_consistency():
    p = _project()
    assert q.gr1_question_objectives(p).passed
    assert q.gr2_design_method(p, {"design": p.study_type.value}).passed
    bad = q.gr2_design_method(p, {"design": "cohort"})
    assert bad.decision == ResearchGateDecision.BLOCK
    assert bad.reason_code == "DESIGN_METHOD_MISMATCH"


# 4 — outcome/variable/SAP consistency
def test_04_outcome_variable_sap_consistency():
    p = _project()
    sap = {"primary_outcome": "outcome-A", "analysis_outcomes": ["outcome-A"]}
    methods = {"sample_size_assumptions": {"alpha": 0.05, "power": 0.8, "effect": 0.5}}
    assert q.gr3_variables_outcomes_analysis(p, sap, methods).passed
    assert q.gr5_sap_protocol(p, sap).passed
    bad = q.gr5_sap_protocol(p, {"primary_outcome": "not-in-protocol"})
    assert bad.decision == ResearchGateDecision.BLOCK


# 5 — CRF/data dictionary validation
def test_05_crf_data_dictionary():
    good = {"crf_variables": ["age", "sbp"], "data_dictionary": {"age": {}, "sbp": {}}}
    assert q.gr4_crf_data_dictionary(good).passed
    bad = {"crf_variables": ["age", "sbp"], "data_dictionary": {"age": {}}}
    r = q.gr4_crf_data_dictionary(bad)
    assert r.decision == ResearchGateDecision.BLOCK and "sbp" in r.detail


# 6 — missing sample-size assumptions → REQUIRE_HUMAN_REVIEW
def test_06_missing_sample_size_requires_review():
    p = _project()
    r = q.gr3_variables_outcomes_analysis(p, {"analysis_outcomes": ["outcome-A"]}, {})
    assert r.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW
    assert r.reason_code == "MISSING_SAMPLE_SIZE_ASSUMPTIONS"


# 7 — fabricated data marker → BLOCK
def test_07_fabricated_data_blocks():
    p = _project()
    reg, ledger, rt, audit, arts = _wp_harness()
    res = run_work_package(p, WP_BY_ID["WP-07"], reg, ledger, rt, audit, arts,
                           fixture_override="RWP-FAB")
    assert res.decision == ResearchGateDecision.BLOCK
    assert res.artifact is None
    assert arts.count() == 0


# 8 — fabricated citation marker → BLOCK
def test_08_fabricated_citation_blocks():
    p = _project()
    reg, ledger, rt, audit, arts = _wp_harness()
    res = run_work_package(p, WP_BY_ID["WP-03"], reg, ledger, rt, audit, arts,
                           fixture_override="RWP-CIT")
    assert res.decision == ResearchGateDecision.BLOCK
    assert res.artifact is None


# 9 — retraction marker → REQUIRE_HUMAN_REVIEW
def test_09_retraction_requires_review():
    out = {"evidence_plan": "includes RETRACTION_MARKER source"}
    r = q.gr7_citation_retraction(out)
    assert r.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW
    assert r.reason_code == "RETRACTION_DETECTED"


# 10 — PII input → BLOCK
def test_10_pii_blocks():
    assert q.gr9_no_pii_no_real_data({"x": "cccd 012345678901"}).decision == ResearchGateDecision.BLOCK
    p = _project()
    reg, ledger, rt, audit, arts = _wp_harness()
    res = run_work_package(p, WP_BY_ID["WP-05"], reg, ledger, rt, audit, arts,
                           fixture_override="RWP-PII")
    assert res.decision == ResearchGateDecision.BLOCK
    assert res.artifact is None


# 11 — real-data marker → BLOCK
def test_11_real_data_marker_blocks():
    assert q.gr9_no_pii_no_real_data({"x": "REAL_PATIENT_DATA"}).decision == ResearchGateDecision.BLOCK
    p = _project()
    reg, ledger, rt, audit, arts = _wp_harness()
    res = run_work_package(p, WP_BY_ID["WP-05"], reg, ledger, rt, audit, arts,
                           fixture_override="RWP-REAL")
    assert res.decision == ResearchGateDecision.BLOCK
    assert res.artifact is None


# 12 — missing agent hash → BLOCK
def test_12_missing_agent_hash_blocks():
    art = ResearchArtifact(
        artifact_id="A", project_id="P", artifact_type="X", artifact_version="0.1",
        source_agent_id="cau-hoi-nghien-cuu", source_agent_hash=None,
        workflow_run_id="RUN-1", evidence_reference="e",
    )
    with pytest.raises(ArtifactIntegrityError):
        ArtifactRegistry().register(art)


# 13 — direct runtime bypass → BLOCK
def test_13_direct_runtime_bypass_blocks():
    reset_guard_context()
    with pytest.raises(DirectRuntimeBypassError):
        assert_via_orchestrator("RUN-NOT-REGISTERED")


# 14 — missing human-review flag → BLOCK
def test_14_missing_human_review_blocks():
    assert q.gr10_human_review({"human_review_required": False}).decision == ResearchGateDecision.BLOCK
    assert q.gr10_human_review({"human_review_required": True}).passed
    art = ResearchArtifact(
        artifact_id="A", project_id="P", artifact_type="X", artifact_version="0.1",
        source_agent_id="x", source_agent_hash="deadbeef", workflow_run_id="R",
        evidence_reference="e", human_review_required=False,
    )
    with pytest.raises(ArtifactIntegrityError):
        ArtifactRegistry().register(art)


# 15 — incomplete reporting checklist → BLOCK
def test_15_incomplete_reporting_blocks():
    p = _project(study_type=StudyType.RCT)
    full = get_template(StudyType.RCT).required_sections
    assert q.gr6_reporting_completeness(p, {"sections_addressed": full}).passed
    r = q.gr6_reporting_completeness(p, {"sections_addressed": full[:2]})
    assert r.decision == ResearchGateDecision.BLOCK


# 16–19 — happy-path synthetic workflows
@pytest.mark.parametrize("study_type,pid", [
    (StudyType.CROSS_SECTIONAL, "RS-T-XS"),
    (StudyType.COHORT, "RS-T-COH"),
    (StudyType.RCT, "RS-T-RCT"),
    (StudyType.SYSTEMATIC_REVIEW, "RS-T-SR"),
])
def test_16to19_happy_path_workflows(study_type, pid):
    reset_guard_context()
    p = _project(study_type=study_type, pid=pid)
    res = run_project(p)
    assert res.blocked is False
    assert res.final_state == ResearchWorkflowState.DRAFT_COMPLETE
    assert len(res.artifacts) == len(WORK_PACKAGES)
    for a in res.artifacts:
        assert a.is_traceable()
        assert a.source_agent_hash
        assert a.draft_only and a.human_review_required
        assert a.review_status == ReviewStatus.PENDING_HUMAN_REVIEW


# 20 — end-to-end traceability: brief → manuscript
def test_20_end_to_end_traceability():
    reset_guard_context()
    p = _project(study_type=StudyType.RCT, pid="RS-T-E2E")
    res = run_project(p)
    types = {a.artifact_type: a for a in res.artifacts}
    assert "RESEARCH_BRIEF_DRAFT" in types
    assert "MANUSCRIPT_OUTLINE_DRAFT" in types
    brief, manuscript = types["RESEARCH_BRIEF_DRAFT"], types["MANUSCRIPT_OUTLINE_DRAFT"]
    assert brief.project_id == manuscript.project_id == "RS-T-E2E"
    # mọi artifact có hash agent thật + run_id + evidence_reference
    for a in res.artifacts:
        assert a.source_agent_hash and a.workflow_run_id and a.evidence_reference


# Bổ sung: WP map vào agent có thật trong registry (không bịa agent)
def test_workpackages_map_to_real_agents():
    reg = build_research_registry()
    for wp in WORK_PACKAGES:
        assert reg.get(wp.lead_agent) is not None, f"{wp.wp_id} lead agent missing"
        for s in wp.supporting_agents:
            assert reg.get(s) is not None, f"{wp.wp_id} supporting {s} missing"


# ── Remediation từ xác minh đối kháng V4.3 ────────────────────────────────────

# G-R8 được test TRỰC TIẾP (không chỉ dựa orchestrator) — vá điểm "gate chưa exercised".
def test_gr8_fabrication_gate_direct():
    assert q.gr8_no_fabrication({"note": "FABRICATED_DATA_MARKER"}).decision == ResearchGateDecision.BLOCK
    assert q.gr8_no_fabrication({"p_value": 0.03, "source_pmid": None}).decision == ResearchGateDecision.BLOCK
    assert q.gr8_no_fabrication({"p_value": 0.03, "source_pmid": "PMID:1"}).passed
    # safety_gates_on_output gộp G-R7/8/9 → BLOCK khi có fabrication
    worst = q.worst_decision(q.safety_gates_on_output({"note": "FABRICATED_DATA_MARKER"}))
    assert worst == ResearchGateDecision.BLOCK


# Synthetic approval có MARKER CẤU TRÚC (is_synthetic), không chỉ free-text.
def test_synthetic_approvals_structurally_marked():
    from runtime.approval_ledger import ApprovalLedger
    ledger = seed_synthetic_ledger()
    syn = ledger.synthetic_approvals()
    assert len(syn) == 5, "G2/G4/G9/GATE_A/GATE_B"
    assert all(r.is_synthetic for r in syn)
    assert ledger.has_synthetic_approvals() is True
    assert ledger.has_only_synthetic_for("G4") is True
    # export phơi bày is_synthetic + nhãn NOT-A-PERSON
    js = ledger.export_json()
    assert '"is_synthetic": true' in js
    assert "MRAQ_HARNESS_NOT_A_PERSON" in js
    # phê duyệt người THẬT (factory khác) KHÔNG bị gắn synthetic
    human = ApprovalLedger.make_human_approval(
        gate_id="G2", reviewer_role="IRB_CHAIR", reviewer_ref="REF",
        scope="real", evidence_content="x")
    assert human.is_synthetic is False


# V4.3.1: artifact là DRAFT_CREATION và KHÔNG dùng approval cổng nào (real hay synthetic).
def test_artifact_is_draft_creation_no_gate_approval():
    reset_guard_context()
    p = _project(study_type=StudyType.RCT, pid="RS-T-SYN")
    res = run_project(p)
    assert res.artifacts
    assert all(a.governance_level == "DRAFT_CREATION" for a in res.artifacts)
    assert all(a.gate_approvals_synthetic is False for a in res.artifacts)
    assert all(a.draft_only and a.human_review_required for a in res.artifacts)
