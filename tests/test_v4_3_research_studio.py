# ruff: noqa: I001
"""
V4.3 — Offline Research Studio deterministic tests (20 kịch bản Phase G).

Tất cả synthetic, offline, qua control-plane. KHÔNG API/network/PII/dữ liệu thật.
Test counts KHÔNG hard-code (mỗi kịch bản là test độc lập).
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
"""

from __future__ import annotations

import pytest

from runtime.approval_ledger import ApprovalLedger
from runtime.audit_logger import AuditLogger
from runtime.dispatch_guard import (
    DirectRuntimeBypassError,
    assert_via_orchestrator,
    reset_guard_context,
)
from research_studio import research_quality_checks as q
from research_studio.artifact_registry import (
    ArtifactIntegrityError,
    ArtifactRegistry,
    ResearchArtifact,
)
from research_studio.dashboard import _build_data
from research_studio.gate_agent_matrix import build_gate_agent_matrix
from research_studio.governance import DraftWorkflowState
from research_studio.project_schema import (
    ResearchProject,
    ResearchWorkflowState,
    ReviewStatus,
    StudyType,
    is_valid,
    validate_project,
)
from research_studio.research_completion_gates import evaluate_research_completion
from research_studio.research_preflight import evaluate_research_preflight
from research_studio.research_quality_checks import ResearchGateDecision
from research_studio.research_workflow import (
    WORK_PACKAGES,
    WP_BY_ID,
    build_draft_mode_registry,
    build_research_registry,
    build_research_runtime,
    run_project,
    run_work_package,
    seed_synthetic_ledger,
)
from research_studio.study_type_router import (
    all_templates,
    get_template,
    reporting_checklist_for,
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
    bad = _project()
    bad.objectives = []
    assert "MISSING_OBJECTIVES" in validate_project(bad)
    bad2 = _project()
    bad2.draft_only = False
    assert "DRAFT_ONLY_MUST_BE_TRUE" in validate_project(bad2)
    bad3 = _project()
    bad3.principal_investigator = "Nguyễn Văn A"
    assert "PI_LOOKS_LIKE_REAL_NAME_USE_SYNTHETIC_ID" in validate_project(bad3)


def test_research_preflight_passes_valid_project_and_lists_review_items():
    p = _project(study_type=StudyType.RCT, pid="RS-T-PREFLIGHT")
    report = evaluate_research_preflight(
        p,
        full_registry=build_research_registry(),
        draft_registry=build_draft_mode_registry(),
    )

    assert report.decision == ResearchGateDecision.PASS
    assert report.reporting_checklist == "CONSORT"
    assert "PROTOCOL_DRAFT" in report.minimum_artifact_set
    assert any(item.startswith("REPORTING_SECTION_REQUIRED:") for item in report.review_items)
    assert any(item.startswith("HUMAN_REVIEW_REQUIRED:") for item in report.review_items)


def test_research_preflight_blocks_missing_core_pico_before_artifacts():
    p = _project(study_type=StudyType.COHORT, pid="RS-T-PREFLIGHT-BLOCK")
    p.pico_or_equivalent = {"E": "exposure only"}

    res = run_project(p)

    assert res.blocked is True
    assert res.artifacts == []
    assert res.preflight_report is not None
    assert res.preflight_report.decision == ResearchGateDecision.BLOCK
    assert any(reason.startswith("PICO_CORE_MISSING:") for reason in res.preflight_report.reason_codes)
    assert res.block_reason.startswith("PREFLIGHT_BLOCK:")


@pytest.mark.parametrize("field,payload", [
    # PII hư cấu (KHÔNG người thật) đặt vào TỪNG field văn bản tự do.
    ("clinical_question", "BN Nguyễn Văn Bình, SĐT 0987654321 có tuân thủ thuốc không?"),
    ("title", "[SYNTHETIC] Khảo sát — BN Trần Thị Bích, CCCD 079185001234"),
    ("research_domain", "Nội tiết, liên hệ bn@hospital.vn"),
])
def test_research_preflight_blocks_pii_in_free_text_fields(field, payload):
    """Defense-in-depth: preflight PHẢI tự chặn PII trong field tự do dù caller
    gọi thẳng run_project() (bỏ qua project_intake)."""
    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-PII")
    setattr(p, field, payload)

    res = run_project(p)

    assert res.blocked is True
    assert res.artifacts == []
    assert res.preflight_report.decision == ResearchGateDecision.BLOCK
    assert any(r.startswith("PII_DETECTED:") for r in res.preflight_report.reason_codes)


def test_research_preflight_blocks_production_connector_marker():
    """Marker connector production (EMR/HIS/PACS/LIVE_DATABASE…) trong nội dung
    đề tài → BLOCK ngay ở preflight."""
    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-CONN")
    p.pico_or_equivalent = {"P": "kéo từ EHOSPITAL_CONNECT", "O": "y"}

    res = run_project(p)

    assert res.blocked is True
    assert any(r.startswith("PRODUCTION_CONNECTOR:") for r in res.preflight_report.reason_codes)


def test_research_preflight_clean_synthetic_project_still_passes():
    """Không dương-tính-giả: đề tài synthetic sạch vẫn PASS sau khi thêm quét PII."""
    p = _project(study_type=StudyType.RCT, pid="RS-T-CLEAN")
    report = evaluate_research_preflight(
        p,
        full_registry=build_research_registry(),
        draft_registry=build_draft_mode_registry(),
    )
    assert report.decision == ResearchGateDecision.PASS
    assert not any(r.startswith(("PII_DETECTED", "PRODUCTION_CONNECTOR", "RAW_DATA_WRITE"))
                   for r in report.reason_codes)


# Audit 2026-07-11: research_preflight's own scan was narrower than project_intake's —
# missed "mã bệnh nhân"/"patient id" (space variant) and fake-result markers that a
# direct run_project() caller (bypassing intake) would have sailed through undetected.

def test_research_preflight_blocks_vietnamese_patient_id_phrase():
    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-PATID-PHRASE")
    p.clinical_question = "mã bệnh nhân BN12345 có đáp ứng điều trị không?"
    res = run_project(p)
    assert res.blocked is True
    assert any(r.startswith("PII_DETECTED:") for r in res.preflight_report.reason_codes)


def test_research_preflight_blocks_fake_result_marker():
    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-FAKERESULT")
    p.title = "[SYNTHETIC] Khảo sát — kết quả p_value=0.03 đã có sẵn"
    res = run_project(p)
    assert res.blocked is True
    assert any(r.startswith("FAKE_RESULT_PLACEHOLDER:") for r in res.preflight_report.reason_codes)


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
    assert res.preflight_report is not None
    assert res.preflight_report.decision == ResearchGateDecision.PASS
    assert res.final_state == ResearchWorkflowState.DRAFT_COMPLETE
    assert len(res.artifacts) == len(WORK_PACKAGES) + 1
    assert "REPORTING_CHECKLIST_DRAFT" in {a.artifact_type for a in res.artifacts}
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
    ledger = seed_synthetic_ledger()
    syn = ledger.synthetic_approvals()
    assert len(syn) == 5, "G2/G4/G9/GATE_A/GATE_B"
    assert all(r.is_synthetic for r in syn)
    assert ledger.has_synthetic_approvals() is True
    assert ledger.has_only_synthetic_for("G4") is True
    assert ledger.has_self_review_violations() is False
    assert all(r.artifact_creator_agent == "research-studio-synthetic-fixture" for r in syn)
    assert all(r.reviewer_agent == "technical-harness-reviewer" for r in syn)
    # export phơi bày is_synthetic + nhãn NOT-A-PERSON
    js = ledger.export_json()
    assert '"is_synthetic": true' in js
    assert "MRAQ_HARNESS_NOT_A_PERSON" in js
    assert "research-studio-synthetic-fixture" in js
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


def test_research_completion_gate_requires_human_review_after_structural_completion():
    reset_guard_context()
    p = _project(study_type=StudyType.RCT, pid="RS-T-COMPLETE")
    res = run_project(p)
    reporting = {"sections_addressed": get_template(p.study_type).required_sections}
    report = evaluate_research_completion(p, res.artifacts, reporting=reporting)

    assert report.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW
    assert report.missing_artifacts == []
    assert report.reporting_checklist == "CONSORT"
    assert report.real_research_blocked is True
    assert report.external_release_blocked is True
    assert "HUMAN_REVIEW_REQUIRED_BEFORE_REAL_USE" in report.reason_codes


def test_research_completion_gate_blocks_missing_required_artifact():
    reset_guard_context()
    p = _project(study_type=StudyType.SYSTEMATIC_REVIEW, pid="RS-T-INCOMPLETE")
    res = run_project(p)
    artifacts = [
        a for a in res.artifacts
        if a.artifact_type != "EVIDENCE_PLAN_DRAFT"
    ]
    reporting = {"sections_addressed": get_template(p.study_type).required_sections}
    report = evaluate_research_completion(p, artifacts, reporting=reporting)

    assert report.decision == ResearchGateDecision.BLOCK
    assert "EVIDENCE_PLAN_DRAFT" in report.missing_artifacts
    assert any(reason.startswith("MISSING_REQUIRED_ARTIFACTS") for reason in report.reason_codes)


def test_dashboard_exposes_research_completion_gate_status():
    reset_guard_context()
    data = _build_data("TEST-UTC")
    assert data["projects"]
    for project in data["projects"]:
        assert project["completion_decision"] == ResearchGateDecision.REQUIRE_HUMAN_REVIEW.value
        assert project["preflight_decision"] == ResearchGateDecision.PASS.value
        assert project["preflight_reason_codes"] == []
        assert project["preflight_review_items"]
        assert project["completion_missing_artifacts"] == []
        assert project["gate_agent_matrix_pass"] is True
        assert project["real_research_blocked"] is True
        assert project["external_release_blocked"] is True
        assert "HUMAN_REVIEW_REQUIRED_BEFORE_REAL_USE" in project["completion_reason_codes"]


def test_gate_agent_matrix_validates_agents_hashes_and_artifacts():
    reset_guard_context()
    p = _project(study_type=StudyType.RCT, pid="RS-T-MATRIX")
    res = run_project(p)
    matrix = build_gate_agent_matrix(
        full_registry=build_research_registry(),
        draft_registry=build_draft_mode_registry(),
        artifacts=res.artifacts,
        project_id=p.project_id,
    )

    assert matrix.decision == ResearchGateDecision.PASS
    assert len(matrix.rows) == len(WORK_PACKAGES)
    assert all(row.lead_hash12 for row in matrix.rows)
    assert all(row.supporting_missing == [] for row in matrix.rows)
    assert all(row.artifact_present for row in matrix.rows)
    assert any("REPORTING_CHECKLIST_DRAFT" in row.extra_artifacts_present for row in matrix.rows)


def test_gate_agent_matrix_blocks_when_gate_artifact_missing():
    reset_guard_context()
    p = _project(study_type=StudyType.RCT, pid="RS-T-MATRIX-BLOCK")
    res = run_project(p)
    artifacts = [
        artifact for artifact in res.artifacts
        if artifact.artifact_type != "SAP_DRAFT"
    ]
    matrix = build_gate_agent_matrix(
        full_registry=build_research_registry(),
        draft_registry=build_draft_mode_registry(),
        artifacts=artifacts,
        project_id=p.project_id,
    )

    assert matrix.decision == ResearchGateDecision.BLOCK
    assert any("EXPECTED_ARTIFACT_MISSING:SAP_DRAFT" in r for r in matrix.reason_codes)


# ── PII defense-in-depth: quality_gate_runner.run_all / artifact_template_engine
# .render / ProjectRegistry.add (audit 2026-07-10) ─────────────────────────────
# Trước khi sửa: chỉ project_intake + research_preflight tự quét PII trên
# ResearchProject. 3 entry point dưới đây nhận thẳng ResearchProject nhưng KHÔNG
# tự quét — một caller bỏ qua intake/preflight (vd
# schedule_runner.on_demand_project_qa() gọi run_all() trực tiếp) có thể đưa
# PII lọt qua. Test này xác nhận cả 3 giờ tự chặn độc lập.

def test_run_all_blocks_pii_in_project_content_bypassing_intake():
    from research_automation.quality_gate_runner import run_all

    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-QGR-PII")
    p.clinical_question = "BN Nguyễn Văn Bình, SĐT 0987654321 có tuân thủ thuốc không?"

    report = run_all(p)

    assert report.overall == "BLOCK"
    assert any(b.startswith("PROJECT_CONTENT_UNSAFE:") for b in report.blocks)


def test_run_all_clean_project_not_affected_by_new_scan():
    from research_automation.quality_gate_runner import run_all

    p = _project(study_type=StudyType.COHORT, pid="RS-T-QGR-CLEAN")
    report = run_all(p)

    assert not any(b.startswith("PROJECT_CONTENT_UNSAFE:") for b in report.blocks)


def test_artifact_render_blocks_pii_instead_of_copying_into_body():
    from research_automation import artifact_template_engine as tpl

    p = _project(study_type=StudyType.RCT, pid="RS-T-TPL-PII")
    p.title = "[SYNTHETIC] Khảo sát — BN Trần Thị Bích, CCCD 079185001234"

    body = tpl.render("RESEARCH_BRIEF_DRAFT", p)

    assert body.get(tpl.CONTENT_BLOCKED) is True
    assert "title" not in body  # nội dung PII KHÔNG được copy vào body
    assert any(r.startswith("PII_DETECTED:") for r in body["unsafe_content_reasons"])


def test_artifact_render_clean_project_unaffected():
    from research_automation import artifact_template_engine as tpl

    p = _project(study_type=StudyType.RCT, pid="RS-T-TPL-CLEAN")
    body = tpl.render("RESEARCH_BRIEF_DRAFT", p)

    assert tpl.CONTENT_BLOCKED not in body
    assert body["title"] == p.title


def test_project_registry_add_rejects_pii_content():
    from research_studio.project_registry import ProjectRegistry

    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-REG-PII")
    p.research_domain = "Nội tiết, liên hệ bn@hospital.vn"

    reg = ProjectRegistry()
    issues = reg.add(p)

    assert any(i.startswith("UNSAFE_CONTENT:") for i in issues)
    assert reg.get("RS-T-REG-PII") is None  # KHÔNG thêm vào registry


def test_project_registry_add_clean_project_still_works():
    from research_studio.project_registry import ProjectRegistry

    p = _project(study_type=StudyType.RCT, pid="RS-T-REG-CLEAN")
    reg = ProjectRegistry()
    issues = reg.add(p)

    assert issues == []
    assert reg.get("RS-T-REG-CLEAN") is p


# ── Audit 2026-07-11 (vòng 4): DraftStateMachine history + terminal-transition ─

def test_run_project_returns_draft_transition_history():
    """sm.history trước đây bị tính rồi bỏ (biến cục bộ, không escape run_project()).
    Nay ProjectRunResult.history phải phản ánh TOÀN bộ chuỗi transition thật, kết
    thúc bằng DRAFT_COMPLETE ALLOWED cho happy path."""
    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-HISTORY")
    res = run_project(p)

    assert res.blocked is False
    assert len(res.history) >= len(WORK_PACKAGES)  # 1 transition/WP (trừ INTAKE) + DRAFT_COMPLETE
    assert res.history[-1].requested == "DRAFT_COMPLETE"
    assert res.history[-1].decision == "ALLOWED"
    assert all(t.decision == "ALLOWED" for t in res.history)


def test_preflight_block_routes_through_state_machine_history():
    """Trước đây nhánh preflight-block gán project.workflow_state=BLOCKED bằng
    attribute trực tiếp, KHÔNG qua sm.request() — res.history rỗng, không auditable.
    Nay phải có ít nhất 1 DraftTransition ghi lại việc BLOCK."""
    p = _project(study_type=StudyType.COHORT, pid="RS-T-PREFLIGHT-HISTORY")
    p.pico_or_equivalent = {"E": "exposure only"}  # thiếu PICO core → preflight BLOCK

    res = run_project(p)

    assert res.blocked is True
    assert len(res.history) == 1
    assert res.history[0].requested == "BLOCKED"
    assert res.history[0].decision == "ALLOWED"  # chuyển SANG BLOCKED luôn được phép
    assert res.history[0].reason_code == "MOVED_TO_BLOCKED"


def test_wp_subset_missing_final_wp_reports_blocked_not_silent_success():
    """Audit: wp_ids bỏ WP cuối (WP-09) khiến sm.request(DRAFT_COMPLETE) bị BLOCKED
    (thiếu 1 bước tuyến tính) nhưng trước đây hàm vẫn trả blocked=False vì kết quả
    request() bị bỏ qua không kiểm tra. Nay phải báo blocked=True trung thực."""
    p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-WPSUBSET")
    subset = [wp.wp_id for wp in WORK_PACKAGES if wp.wp_id != "WP-09"]

    res = run_project(p, wp_ids=subset)

    assert res.blocked is True
    assert res.final_state == DraftWorkflowState.MANUSCRIPT_DRAFT  # dừng lại đây, KHÔNG tới DRAFT_COMPLETE
    assert res.history[-1].requested == "DRAFT_COMPLETE"
    assert res.history[-1].decision == "BLOCKED"
    assert "INVALID_DRAFT_TRANSITION" in res.history[-1].reason_code


# ── Audit 2026-07-11 (vòng 4): ArtifactRegistry idempotent theo artifact_id ────

def test_artifact_registry_register_idempotent_by_id():
    """artifact_id tất định (project_id:artifact_type) — một retry re-đăng ký
    CÙNG artifact_id phải trả bản ĐÃ CÓ, không append trùng (audit: retry không
    idempotent, ArtifactRegistry.register() trước đây luôn append vô điều kiện)."""
    reg = ArtifactRegistry()
    a1 = ResearchArtifact(
        artifact_id="RS-T-DUP:RESEARCH_BRIEF_DRAFT", project_id="RS-T-DUP",
        artifact_type="RESEARCH_BRIEF_DRAFT", artifact_version="0.1-draft",
        source_agent_id="cau-hoi-nghien-cuu", source_agent_hash="hash-1",
        workflow_run_id="run-1", evidence_reference="ev-1",
    )
    a2 = ResearchArtifact(
        artifact_id="RS-T-DUP:RESEARCH_BRIEF_DRAFT", project_id="RS-T-DUP",
        artifact_type="RESEARCH_BRIEF_DRAFT", artifact_version="0.1-draft",
        source_agent_id="cau-hoi-nghien-cuu", source_agent_hash="hash-1",
        workflow_run_id="run-2", evidence_reference="ev-2",  # lần thử lại, run_id khác
    )
    r1 = reg.register(a1)
    r2 = reg.register(a2)

    assert r1 is a1
    assert r2 is a1                       # trả bản ĐÃ CÓ, không phải a2
    assert reg.count() == 1
    assert reg.for_project("RS-T-DUP") == [a1]


def test_workflow_runner_retry_does_not_double_register_artifacts():
    """End-to-end: một attempt raise lỗi retryable SAU khi vài WP đã đăng ký
    artifact, attempt thứ 2 chạy trọn vẹn — self.artifacts không được có bản trùng
    (audit: _do() trước đây dùng THẲNG self.artifacts xuyên các lần thử lại)."""
    from research_automation.retry_policy import RetryPolicy, TransientDeterministicError
    from research_automation.workflow_runner import WorkflowRunner
    import research_automation.workflow_runner as wr_mod

    calls = {"n": 0}
    real_run_project = wr_mod.run_project

    def flaky_run_project(project, wp_ids=None, registry=None, artifacts=None):
        calls["n"] += 1
        if calls["n"] == 1:
            # Giả lập: vài WP đã đăng ký artifact vào registry SCRATCH của lần thử
            # này trước khi lỗi retryable xảy ra giữa chừng (mô phỏng lỗi thật).
            real_run_project(project, wp_ids=[WORK_PACKAGES[0].wp_id], registry=registry,
                             artifacts=artifacts)
            raise TransientDeterministicError("simulated contention")
        return real_run_project(project, wp_ids=wp_ids, registry=registry, artifacts=artifacts)

    wr_mod.run_project = flaky_run_project
    try:
        runner = WorkflowRunner(retry=RetryPolicy(max_attempts=3))
        req = {
            "project_id": "RS-T-RETRY-DEDUP", "title": "[SYNTHETIC] retry test",
            "study_type": "cross_sectional", "research_domain": "test",
            "clinical_question": "Q synthetic?",
            "PICO_or_equivalent": {"P": "x", "O": "y"},
            "objectives": ["obj1"], "outcomes": ["outcome-A"],
            "population_description_synthetic": "synthetic",
            "study_setting_synthetic": "synthetic clinic",
            "requested_work_packages": [wp.wp_id for wp in WORK_PACKAGES],
            "human_owner": "PI-SYNTH-T", "draft_only": True, "human_review_required": True,
        }
        res = runner.run(req)
    finally:
        wr_mod.run_project = real_run_project

    assert calls["n"] == 2  # 1 lần lỗi + 1 lần thành công
    assert res.status == "CREATED"
    ids = [a.artifact_id for a in runner.artifacts.for_project("RS-T-RETRY-DEDUP")]
    assert len(ids) == len(set(ids))  # không id nào trùng
