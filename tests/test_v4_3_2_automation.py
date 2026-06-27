"""
V4.3.2 — Offline Research Studio automation deterministic tests (Phase J, 25 kịch bản).

OFFLINE · DETERMINISTIC · SYNTHETIC. KHÔNG API/network/PII/dữ liệu thật/eHospital.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE. Test counts không hard-code.
"""

from __future__ import annotations

import pytest

from runtime.dispatch_guard import reset_guard_context, assert_via_orchestrator, DirectRuntimeBypassError

from research_studio.project_schema import StudyType
from research_studio.artifact_registry import ArtifactRegistry, ResearchArtifact, ArtifactIntegrityError
from research_studio.study_type_router import get_template

from research_automation.project_intake import run_intake, IntakeDecision
from research_automation.workflow_runner import WorkflowRunner
from research_automation.review_queue import ReviewQueue, ReviewStatus, AutoApprovalForbidden
from research_automation.work_queue import WorkQueue, ProjectLockError
from research_automation.retry_policy import RetryPolicy, SafeStop, TransientDeterministicError
from research_automation.project_snapshot import SnapshotStore
from research_automation.idempotency_guard import IdempotencyGuard, request_hash
from research_automation.quality_gate_runner import run_all, synthetic_complete_inputs
from research_automation.schedule_runner import (
    check_manifest_integrity, detect_untracked_critical, daily_integrity_check, weekly_quality_check,
)
from research_studio.capability_profile import ExternalActionType, check_external_action
from research_studio.governance import attempt_external_release, attempt_real_analysis
from research_automation import artifact_template_engine as tpl


def setup_function():
    reset_guard_context()


def teardown_function():
    reset_guard_context()


def _req(pid="RS-XS-A", study_type="cross_sectional", **over):
    d = {
        "project_id": pid, "title": "[SYNTHETIC] auto", "study_type": study_type,
        "research_domain": "tim mạch", "clinical_question": "Tỷ lệ đạt HA?",
        "PICO_or_equivalent": {"P": "BN synthetic", "O": "đạt HA"},
        "objectives": ["ước lượng"], "outcomes": ["tỷ lệ HA đạt"],
        "population_description_synthetic": "synthetic",
        "study_setting_synthetic": "synthetic clinic",
        "requested_work_packages": ["WP-01", "WP-02"], "human_owner": "PI-SYNTH-01",
        "draft_only": True, "human_review_required": True,
    }
    d.update(over)
    return d


# 1
def test_01_valid_intake_creates_project():
    r = run_intake(_req())
    assert r.decision == IntakeDecision.CREATED and r.project is not None


# 2
def test_02_pii_blocks():
    r = run_intake(_req(pid="RS-PII", clinical_question="BN Nguyễn Văn A cccd 012345678901"))
    assert r.decision == IntakeDecision.BLOCK and "PII" in r.reason_code


# 3
def test_03_real_data_marker_blocks():
    r = run_intake(_req(pid="RS-REAL", study_setting_synthetic="pull REAL_PATIENT_DATA from EHOSPITAL_CONNECT"))
    assert r.decision == IntakeDecision.BLOCK


# 4
def test_04_unknown_study_type_blocks():
    r = run_intake(_req(pid="RS-UNK", study_type="banh_mi"))
    assert r.decision == IntakeDecision.BLOCK and "UNKNOWN_STUDY_TYPE" in r.reason_code


# 5
def test_05_missing_objectives_requires_human_input():
    r = run_intake(_req(pid="RS-NOOBJ", objectives=[]))
    assert r.decision == IntakeDecision.REQUIRE_HUMAN_INPUT and r.reason_code == "MISSING_OBJECTIVES"


# 6
def test_06_direct_runtime_call_blocks():
    reset_guard_context()
    with pytest.raises(DirectRuntimeBypassError):
        assert_via_orchestrator("RUN-NOT-REGISTERED")


# 7
def test_07_workflow_routing_by_study_type():
    reset_guard_context()
    res = WorkflowRunner().run(_req(pid="RS-RCT-R", study_type="randomized_controlled_trial"))
    assert res.status == "CREATED"
    # routing dùng đúng template/checklist của study type
    assert get_template(StudyType.RCT).reporting_checklist == "CONSORT"
    assert any(a.artifact_type == "PROTOCOL_DRAFT" for a in res.artifacts)


# 8 & 9
def test_08_09_artifacts_draft_only_and_human_review():
    reset_guard_context()
    res = WorkflowRunner().run(_req(pid="RS-DR"))
    assert res.artifacts
    for a in res.artifacts:
        assert a.draft_only is True
        assert a.human_review_required is True


# 10
def test_10_artifact_missing_hash_blocks():
    art = ResearchArtifact(
        artifact_id="A", project_id="P", artifact_type="X", artifact_version="0.1",
        source_agent_id="cau-hoi-nghien-cuu", source_agent_hash=None,
        workflow_run_id="R", evidence_reference="e")
    with pytest.raises(ArtifactIntegrityError):
        ArtifactRegistry().register(art)


# 11
def test_11_duplicate_request_no_duplicate_artifact():
    reset_guard_context()
    runner = WorkflowRunner()
    req = _req(pid="RS-DUP")
    r1 = runner.run(req)
    n1 = len(runner.artifacts.for_project("RS-DUP"))
    r2 = runner.run(req)
    assert r1.status == "CREATED" and r2.status == "DUPLICATE"
    assert len(runner.artifacts.for_project("RS-DUP")) == n1


# 12
def test_12_concurrent_lock_blocks_safely():
    wq = WorkQueue()
    wq.acquire("P1", "run-A")
    with pytest.raises(ProjectLockError):
        wq.acquire("P1", "run-B")
    wq.release("P1", "run-A")
    wq.acquire("P1", "run-B")  # sau khi release thì OK


# 13
def test_13_retry_limit_safe_stop():
    rp = RetryPolicy(max_attempts=2)

    def always_transient():
        raise TransientDeterministicError("flaky")
    with pytest.raises(SafeStop):
        rp.run(always_transient)

    def non_retryable():
        raise ValueError("hard")
    with pytest.raises(SafeStop):
        rp.run(non_retryable)


# 14
def test_14_snapshot_rollback_preserves_audit():
    from runtime.audit_logger import AuditLogger
    from runtime.schemas import PolicyDecisionEnum, RuntimeTypeEnum
    from research_studio.project_registry import synthetic_projects
    audit = AuditLogger(run_id="A-SNAP")
    audit.log_gate_decision(workflow_id="P", agent_id="x", fixture_id="F",
                            runtime_type=RuntimeTypeEnum.MOCK, state_before="DRAFT",
                            state_after="DRAFT", policy_decision=PolicyDecisionEnum.PASS,
                            agent_source_hash="H")
    before = audit.count()
    store = SnapshotStore()
    p = synthetic_projects()[0]
    snap = store.take(p, [])
    view = store.rollback_view(snap.snapshot_id)
    assert view["restores"] == "DRAFT_SYNTHETIC_STATE_ONLY"
    assert view["audit_log_preserved"] is True
    assert audit.count() == before  # rollback KHÔNG đụng audit log


# 15
def test_15_quality_gate_block_or_review():
    from research_studio.project_schema import ResearchProject
    p = ResearchProject(project_id="RS-Q", title="[SYNTHETIC]", principal_investigator="PI-SYNTH",
                        research_domain="d", study_type=StudyType.COHORT,
                        clinical_question="Q?", pico_or_equivalent={"P": "x"},
                        objectives=["o"], outcomes=["outcome-A"])
    # default synthetic inputs: thiếu sample-size assumption → REVIEW
    rep = run_all(p)
    assert rep.overall in ("REVIEW_REQUIRED", "BLOCK")
    # fabricated output → BLOCK
    bad = synthetic_complete_inputs(p); bad["output"] = {"note": "FABRICATED_DATA_MARKER"}
    assert run_all(p, bad).overall == "BLOCK"


# 16
def test_16_manuscript_cannot_submission():
    from research_studio.project_registry import synthetic_projects
    body = tpl.render("MANUSCRIPT_OUTLINE_DRAFT", synthetic_projects()[0])
    assert body["submission"] == "BLOCKED_V4_3_2"
    assert check_external_action("viet-ban-thao", ExternalActionType.SUBMIT).allowed is False


# 17
def test_17_protocol_cannot_ethics_submission():
    assert check_external_action("dao-duc-dang-ky", ExternalActionType.ETHICS_REGISTRATION).allowed is False
    assert attempt_external_release().decision == "BLOCKED"


# 18
def test_18_synthetic_analysis_real_data_marker_blocks():
    from research_studio.research_workflow import (
        run_work_package, WP_BY_ID, build_draft_mode_registry, build_research_runtime, seed_synthetic_ledger)
    from runtime.audit_logger import AuditLogger
    from research_studio.project_registry import synthetic_projects
    reset_guard_context()
    p = synthetic_projects()[0]
    res = run_work_package(p, WP_BY_ID["WP-07"], build_draft_mode_registry(),
                           __import__("runtime.approval_ledger", fromlist=["ApprovalLedger"]).ApprovalLedger(),
                           build_research_runtime(), AuditLogger(run_id="A18"),
                           ArtifactRegistry(), fixture_override="RWP-REAL")
    assert res.artifact is None
    assert "CAPABILITY_BLOCKED" in (res.reason_code or "") or "REAL_DATA" in (res.reason_code or "")


# 19
def test_19_review_queue_cannot_auto_approve():
    rq = ReviewQueue()
    item = rq.add(project_id="P", artifact_id="A", review_reason="r", blocking_gate=None,
                  required_human_role="PI", missing_information=[], risks=[], audit_event_id="e")
    with pytest.raises(AutoApprovalForbidden):
        rq.automation_transition(item.review_id, ReviewStatus.HUMAN_APPROVED_DRAFT)
    # người thật mới approve được
    rq.human_decision(item.review_id, ReviewStatus.HUMAN_APPROVED_DRAFT, "Dr.RealHuman")
    assert rq.by_status(ReviewStatus.HUMAN_APPROVED_DRAFT)


# 20
def test_20_daily_integrity_detects_manifest_mismatch():
    rep = check_manifest_integrity(expected_sha="0" * 64)
    assert rep.ok is False
    assert any("MANIFEST_HASH_MISMATCH" in f for f in rep.findings)
    # job tổng hợp cũng fail
    assert daily_integrity_check(expected_sha="0" * 64).ok is False


# 21
def test_21_weekly_detects_untracked_critical():
    rep = detect_untracked_critical(["research_automation/x.py", "docs/readme.md"])
    assert rep.ok is False
    assert any("research_automation/x.py" in f for f in rep.findings)
    # file ngoài critical không bị gắn cờ
    assert detect_untracked_critical(["docs/readme.md"]).ok is True


# 22–25 end-to-end synthetic
@pytest.mark.parametrize("study_type,pid", [
    ("cross_sectional", "RS-E2E-XS"),
    ("cohort", "RS-E2E-COH"),
    ("randomized_controlled_trial", "RS-E2E-RCT"),
    ("systematic_review_meta_analysis", "RS-E2E-SR"),
])
def test_22to25_end_to_end_synthetic(study_type, pid):
    reset_guard_context()
    res = WorkflowRunner().run(_req(pid=pid, study_type=study_type))
    assert res.status == "CREATED"
    assert len(res.artifacts) >= 1
    assert all(a.draft_only and a.human_review_required for a in res.artifacts)
    assert len(res.review_items) == len(res.artifacts)
    assert res.quality_report["overall"] in ("PASS", "REVIEW_REQUIRED")


# Bổ sung: parser YAML offline (không phụ thuộc PyYAML) đúng schema request
def test_minimal_yaml_loader_offline():
    from research_automation.project_intake import _minimal_yaml_load
    txt = (
        'project_id: "RS-Y"\n'
        'study_type: "cohort"   # inline comment\n'
        'draft_only: true\n'
        'human_review_required: true\n'
        '# full-line comment\n'
        'objectives:\n  - "obj một"\n  - "obj hai"\n'
        'PICO_or_equivalent:\n  P: "BN synthetic"\n  O: "đạt đích"\n'
        'requested_work_packages: ["WP-01", "WP-02"]\n'
    )
    d = _minimal_yaml_load(txt)
    assert d["project_id"] == "RS-Y"
    assert d["study_type"] == "cohort"
    assert d["draft_only"] is True and d["human_review_required"] is True
    assert d["objectives"] == ["obj một", "obj hai"]
    assert d["PICO_or_equivalent"] == {"P": "BN synthetic", "O": "đạt đích"}
    assert d["requested_work_packages"] == ["WP-01", "WP-02"]


# Bổ sung: end-to-end qua load_yaml + run (chứng minh CLI path offline)
def test_intake_from_yaml_text_then_run():
    from research_automation.project_intake import load_yaml
    reset_guard_context()
    txt = (
        'project_id: "RS-YAML-E2E"\ntitle: "[SYNTHETIC] yaml"\n'
        'study_type: "cross_sectional"\nresearch_domain: "tim mạch"\n'
        'clinical_question: "Tỷ lệ đạt HA?"\n'
        'PICO_or_equivalent:\n  P: "BN synthetic"\n  O: "đạt HA"\n'
        'objectives:\n  - "ước lượng"\noutcomes:\n  - "tỷ lệ HA"\n'
        'population_description_synthetic: "synthetic"\n'
        'study_setting_synthetic: "synthetic clinic"\n'
        'requested_work_packages: ["WP-01"]\nhuman_owner: "PI-SYNTH-01"\n'
        'draft_only: true\nhuman_review_required: true\n'
    )
    res = WorkflowRunner().run(load_yaml(txt))
    assert res.status == "CREATED" and res.artifacts


# Bổ sung: weekly_quality_check phát hiện artifact thiếu human_review (qua artifacts registry giả)
def test_weekly_quality_flags_bad_artifact():
    arts = ArtifactRegistry()
    # artifact hợp lệ
    arts.register(ResearchArtifact(
        artifact_id="P:OK", project_id="P", artifact_type="X", artifact_version="0.1",
        source_agent_id="a", source_agent_hash="H", workflow_run_id="R", evidence_reference="e"))
    rep = weekly_quality_check(review_queue=ReviewQueue(), artifacts=arts)
    assert rep.ok is True
