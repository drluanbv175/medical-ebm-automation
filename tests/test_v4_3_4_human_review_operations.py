"""
test_v4_3_4_human_review_operations.py — deterministic tests (V4.3.4).

Kiểm tra Human Review Operating Model:
- Enums và routing matrix đúng
- Automation không thể tạo review decision
- ReviewLedger ghi thêm (append-only), không ghi đè
- record_decision trả ReviewRecord đúng cấu trúc
- ForbiddenReviewMode bị từ chối
- list_review_queue không PII
- get_review_status đúng counter
- build_revision_plan khi có REVISION_REQUIRED
- CLI 4 subcommand có trong parser

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
"""

from __future__ import annotations

import json
import pathlib
import tempfile

import pytest

from research_project.project_config import (
    ARTIFACT_FILENAME,
    ArtifactID,
    ProjectConfig,
)
from research_project.project_config import (
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
)
from research_project.project_review_operations import (
    REVIEW_ROUTING_MATRIX,
    AutoReviewForbidden,
    ForbiddenReviewMode,
    HumanDecision,
    MissingReviewActorReference,
    PIIInReviewRecord,
    ReviewLedger,
    ReviewMode,
    ReviewRecord,
    ReviewRole,
    RiskLevel,
    UnauthorizedReviewRole,
    _make_audit_event_id,
    _make_review_id,
    build_revision_plan,
    get_review_status,
    list_review_queue,
    make_review_queue_item,
    record_decision,
    required_roles_for_artifact,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_config(project_id: str = "SYNTH-TEST-001") -> ProjectConfig:
    return ProjectConfig(
        project_id=project_id,
        title="Synthetic Test Project",
        study_type="cohort",
        primary_objectives=["[REQUIRE_HUMAN_INPUT] Mục tiêu"],
        secondary_objectives=[],
        primary_outcomes=["[REQUIRE_HUMAN_INPUT] Kết cục"],
        secondary_outcomes=[],
        research_constraints={},
        data_mode="NO_REAL_DATA",
        external_actions_forbidden=True,
        draft_only=True,
        created_at="2026-06-28T00:00:00+00:00",
        version="0.1.0",
        human_owner="PI-SYNTH-001",
    )


def _populate_project_dir(project_dir: pathlib.Path, config: ProjectConfig) -> None:
    """Tạo artifact tối thiểu cho list_review_queue."""
    for art_id, fname in ARTIFACT_FILENAME.items():
        fpath = project_dir / fname
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(
            f"# {art_id.value}\n{RHI} Nội dung cần PI điền.\n",
            encoding="utf-8",
        )


def _reviewer_ref(role="PI") -> str:
    """Mã giả định danh reviewer dùng trong fixture synthetic, không chứa PII."""
    value = role.value if isinstance(role, ReviewRole) else str(role)
    return f"REF-{value}-001"


# ---------------------------------------------------------------------------
# T01 — ReviewRole có đúng 6 giá trị
# ---------------------------------------------------------------------------

def test_t01_review_role_has_6_values():
    values = [r.value for r in ReviewRole]
    assert len(values) == 6
    assert "PI_PROJECT_OWNER" in values
    assert "IRB_ETHICS_COMMITTEE" in values
    assert "METHODS_STATISTICS_REVIEWER" in values
    assert "INDEPENDENT_PEER_REVIEWER" in values
    assert "EVIDENCE_CITATION_REVIEWER" in values
    assert "DATA_GOVERNANCE_QA_REVIEWER" in values


# ---------------------------------------------------------------------------
# T02 — Automation không thể tạo review decision
# ---------------------------------------------------------------------------

def test_t02_automation_caller_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        with pytest.raises(AutoReviewForbidden):
            record_decision(
                project_dir=project_dir,
                config=config,
                artifact_id_str=ArtifactID.PROTOCOL_DRAFT.value,
                decision=HumanDecision.REVISION_REQUIRED,
                review_role=ReviewRole.PI_PROJECT_OWNER,
                reason="test automation block",
                reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
                automation_caller=True,
            )


# ---------------------------------------------------------------------------
# T03 — ReviewLedger ghi append-only, không ghi đè record cũ
# ---------------------------------------------------------------------------

def test_t03_ledger_append_only():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        ledger = ReviewLedger(project_dir)

        r1 = record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.RESEARCH_CHARTER.value,
            decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="First acceptance",
            reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
            automation_caller=False,
        )
        r2 = record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.RESEARCH_CHARTER.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="Actually needs revision",
            reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
            automation_caller=False,
        )

        records = ledger.read_all()
        assert len(records) == 2
        assert records[0].review_id == r1.review_id
        assert records[1].review_id == r2.review_id
        # Lần 1 vẫn được bảo toàn
        assert records[0].decision == HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE


# ---------------------------------------------------------------------------
# T04 — record_decision trả ReviewRecord đúng cấu trúc
# ---------------------------------------------------------------------------

def test_t04_review_record_fields():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        rec = record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.SAP_DRAFT.value,
            decision=HumanDecision.REQUEST_HUMAN_INPUT,
            review_role=ReviewRole.METHODS_STATISTICS_REVIEWER,
            reason="Cần PI xác nhận assumptions",
            required_actions=["Điền effect size", "Xác nhận alpha=0.05"],
            reviewer_ref=_reviewer_ref(ReviewRole.METHODS_STATISTICS_REVIEWER),
            automation_caller=False,
        )
        assert rec.review_id.startswith("RV-")
        assert rec.project_id == "SYNTH-TEST-001"
        assert rec.artifact_id == ArtifactID.SAP_DRAFT.value
        assert rec.review_role == ReviewRole.METHODS_STATISTICS_REVIEWER
        assert rec.reviewer_identity_reference == _reviewer_ref(ReviewRole.METHODS_STATISTICS_REVIEWER)
        assert rec.review_mode == ReviewMode.HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED
        assert rec.decision == HumanDecision.REQUEST_HUMAN_INPUT
        assert len(rec.required_actions) == 2
        assert rec.blocking_gate == "D-R6"
        assert rec.risk_level == RiskLevel.CRITICAL
        assert rec.audit_event_id.startswith("AE-")
        assert rec.created_at_utc != ""


# ---------------------------------------------------------------------------
# T05 — ForbiddenReviewMode bị từ chối khi ghi vào ledger
# ---------------------------------------------------------------------------

def test_t05_forbidden_review_mode_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        ledger = ReviewLedger(project_dir)

        forbidden_mode_str = "INDEPENDENT_REVIEW_APPROVED"
        # Tạo record trực tiếp để bypass enum validation
        rec = ReviewRecord(
            review_id="RV-FORCED",
            project_id="SYNTH-001",
            artifact_id="00_RESEARCH_CHARTER",
            artifact_version="0.1.0",
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reviewer_identity_reference=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
            review_mode=ReviewMode.SELF_REVIEW,  # placeholder
            decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
            reason="forced test",
            required_actions=[],
            blocking_gate="D-R1",
            risk_level=RiskLevel.LOW,
            created_at_utc="2026-06-28T00:00:00+00:00",
            audit_event_id="AE-FORCED",
        )
        # Patch review_mode với giá trị cấm
        object.__setattr__(rec, "review_mode", type(
            "FakeMode", (), {"value": forbidden_mode_str}
        )())
        with pytest.raises(ForbiddenReviewMode):
            ledger.append(rec)


# ---------------------------------------------------------------------------
# T06 — HumanDecision có đúng 5 giá trị
# ---------------------------------------------------------------------------

def test_t06_human_decision_5_values():
    values = set(d.value for d in HumanDecision)
    assert values == {
        "REQUEST_HUMAN_INPUT",
        "REVISION_REQUIRED",
        "ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE",
        "REJECT_DRAFT",
        "ARCHIVE_DRAFT",
    }


# ---------------------------------------------------------------------------
# T07 — ReviewMode chỉ 2 giá trị hợp lệ
# ---------------------------------------------------------------------------

def test_t07_review_mode_2_allowed_values():
    allowed = {m.value for m in ReviewMode}
    forbidden = {
        "INDEPENDENT_REVIEW_APPROVED", "ETHICS_APPROVED",
        "PI_APPROVED", "FINAL_APPROVED",
    }
    assert not (allowed & forbidden), f"Forbidden mode found: {allowed & forbidden}"
    assert len(allowed) == 2


# ---------------------------------------------------------------------------
# T08 — REVIEW_ROUTING_MATRIX có 19 entries (một cho mỗi ArtifactID)
# ---------------------------------------------------------------------------

def test_t08_routing_matrix_covers_all_artifacts():
    all_artifact_ids = set(ArtifactID)
    routed = set(REVIEW_ROUTING_MATRIX.keys())
    # Mọi artifact trong routing phải là ArtifactID hợp lệ
    assert routed.issubset(all_artifact_ids)
    # Số lượng phải bằng số ArtifactID
    assert len(routed) == len(all_artifact_ids), (
        f"Missing from routing: {all_artifact_ids - routed}"
    )


# ---------------------------------------------------------------------------
# T09 — PROTOCOL_DRAFT được route tới CRITICAL risk
# ---------------------------------------------------------------------------

def test_t09_protocol_draft_critical_risk():
    roles, focus, risk, gate = REVIEW_ROUTING_MATRIX[ArtifactID.PROTOCOL_DRAFT]
    assert risk == RiskLevel.CRITICAL
    assert ReviewRole.PI_PROJECT_OWNER in roles
    assert ReviewRole.METHODS_STATISTICS_REVIEWER in roles
    assert ReviewRole.IRB_ETHICS_COMMITTEE in roles
    assert "IRB" in focus or "ethics" in focus


# ---------------------------------------------------------------------------
# T10 — SAP_DRAFT được route tới METHODS_STATISTICS_REVIEWER
# ---------------------------------------------------------------------------

def test_t10_sap_draft_routed_to_methods_reviewer():
    roles, _, _, gate = REVIEW_ROUTING_MATRIX[ArtifactID.SAP_DRAFT]
    assert ReviewRole.METHODS_STATISTICS_REVIEWER in roles
    assert gate == "D-R6"


# ---------------------------------------------------------------------------
# T10B — Sai role không được ghi review decision cho artifact
# ---------------------------------------------------------------------------

def test_t10b_record_decision_blocks_unrouted_role():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        with pytest.raises(UnauthorizedReviewRole):
            record_decision(
                project_dir, config,
                artifact_id_str=ArtifactID.SAP_DRAFT.value,
                decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
                review_role=ReviewRole.PI_PROJECT_OWNER,
                reason="PI không được thay thống kê viên cho SAP",
                reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
                automation_caller=False,
            )
        assert ReviewLedger(project_dir).read_all() == []


# ---------------------------------------------------------------------------
# T10C — Artifact nhiều role chỉ hoàn tất khi đủ mọi role bắt buộc
# ---------------------------------------------------------------------------

def test_t10c_protocol_requires_pi_irb_and_statistician_acceptance():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        _populate_project_dir(project_dir, config)
        assert required_roles_for_artifact(ArtifactID.PROTOCOL_DRAFT) == [
            ReviewRole.PI_PROJECT_OWNER,
            ReviewRole.METHODS_STATISTICS_REVIEWER,
            ReviewRole.IRB_ETHICS_COMMITTEE,
        ]

        record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.PROTOCOL_DRAFT.value,
            decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
            review_role=ReviewRole.PI_PROJECT_OWNER,
            reason="PI chấp nhận draft nội bộ",
            reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
            automation_caller=False,
        )
        protocol_item = next(
            item for item in list_review_queue(project_dir, config)
            if item["artifact_id"] == ArtifactID.PROTOCOL_DRAFT.value
        )
        assert protocol_item["current_status"] == "PARTIAL_REVIEW"
        assert protocol_item["complete_required_review"] is False
        assert ReviewRole.METHODS_STATISTICS_REVIEWER.value in protocol_item["missing_roles"]
        assert ReviewRole.IRB_ETHICS_COMMITTEE.value in protocol_item["missing_roles"]

        for role in (ReviewRole.METHODS_STATISTICS_REVIEWER, ReviewRole.IRB_ETHICS_COMMITTEE):
            record_decision(
                project_dir, config,
                artifact_id_str=ArtifactID.PROTOCOL_DRAFT.value,
                decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
                review_role=role,
                reason=f"{role.value} chấp nhận draft nội bộ",
                reviewer_ref=_reviewer_ref(role),
                automation_caller=False,
            )

        protocol_item = next(
            item for item in list_review_queue(project_dir, config)
            if item["artifact_id"] == ArtifactID.PROTOCOL_DRAFT.value
        )
        assert protocol_item["current_status"] == "ACCEPTED_DRAFT"
        assert protocol_item["complete_required_review"] is True
        assert protocol_item["missing_roles"] == []
        status = get_review_status(project_dir)
        assert status["accepted_as_draft_internal"] == 1
        assert status["partial_review"] == 0


# ---------------------------------------------------------------------------
# T10D — Thiếu mã reviewer giả danh bị chặn trước khi ghi ledger
# ---------------------------------------------------------------------------

def test_t10d_record_decision_requires_reviewer_reference():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        with pytest.raises(MissingReviewActorReference):
            record_decision(
                project_dir, config,
                artifact_id_str=ArtifactID.RESEARCH_CHARTER.value,
                decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
                review_role=ReviewRole.PI_PROJECT_OWNER,
                reason="Thiếu mã reviewer phải bị chặn.",
                reviewer_ref="",
                automation_caller=False,
            )
        assert ReviewLedger(project_dir).read_all() == []


# ---------------------------------------------------------------------------
# T10E — PII trong reviewer/reason/actions bị chặn trước khi ghi ledger
# ---------------------------------------------------------------------------

def test_t10e_record_decision_blocks_pii_in_review_record():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        with pytest.raises(PIIInReviewRecord):
            record_decision(
                project_dir, config,
                artifact_id_str=ArtifactID.SAP_DRAFT.value,
                decision=HumanDecision.REVISION_REQUIRED,
                review_role=ReviewRole.METHODS_STATISTICS_REVIEWER,
                reason="Cần xóa email trong phần mô tả trước khi duyệt.",
                required_actions=["Không đưa họ tên hoặc patient_id vào sổ review."],
                reviewer_ref=_reviewer_ref(ReviewRole.METHODS_STATISTICS_REVIEWER),
                automation_caller=False,
            )
        assert ReviewLedger(project_dir).read_all() == []


# ---------------------------------------------------------------------------
# T11 — ReviewLedger.read_all() trả list rỗng khi chưa có file
# ---------------------------------------------------------------------------

def test_t11_ledger_empty_when_no_file():
    with tempfile.TemporaryDirectory() as tmp:
        ledger = ReviewLedger(pathlib.Path(tmp))
        assert ledger.read_all() == []
        assert not ledger.exists()


# ---------------------------------------------------------------------------
# T12 — get_review_status trả đúng counter sau 3 records
# ---------------------------------------------------------------------------

def test_t12_review_status_counters():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()

        record_decision(project_dir, config,
                        artifact_id_str=ArtifactID.RESEARCH_CHARTER.value,
                        decision=HumanDecision.REVISION_REQUIRED,
                        review_role=ReviewRole.PI_PROJECT_OWNER,
                        reason="needs revision",
                        reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
                        automation_caller=False)
        record_decision(project_dir, config,
                        artifact_id_str=ArtifactID.SAP_DRAFT.value,
                        decision=HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE,
                        review_role=ReviewRole.METHODS_STATISTICS_REVIEWER,
                        reason="ok",
                        reviewer_ref=_reviewer_ref(ReviewRole.METHODS_STATISTICS_REVIEWER),
                        automation_caller=False)
        record_decision(project_dir, config,
                        artifact_id_str=ArtifactID.EVIDENCE_PLAN.value,
                        decision=HumanDecision.REQUEST_HUMAN_INPUT,
                        review_role=ReviewRole.EVIDENCE_CITATION_REVIEWER,
                        reason="missing evidence",
                        reviewer_ref=_reviewer_ref(ReviewRole.EVIDENCE_CITATION_REVIEWER),
                        automation_caller=False)

        status = get_review_status(project_dir)
        assert status["total_review_records"] == 3
        assert status["total_artifacts_reviewed"] == 3
        assert status["revision_required"] == 1
        assert status["accepted_as_draft_internal"] == 1
        assert status["human_input_required"] == 1
        assert status["final_released_submitted_count"] == 0
        assert status["draft_only_status"] is True


# ---------------------------------------------------------------------------
# T13 — get_review_status chứa qualification và disclaimer
# ---------------------------------------------------------------------------

def test_t13_review_status_has_no_go_qualification():
    with tempfile.TemporaryDirectory() as tmp:
        status = get_review_status(pathlib.Path(tmp))
        assert "NO-GO" in status["qualification"]
        assert "DRAFT" in status["disclaimer"] or "bác sĩ" in status["disclaimer"]


# ---------------------------------------------------------------------------
# T14 — build_revision_plan khi không có REVISION_REQUIRED
# ---------------------------------------------------------------------------

def test_t14_revision_plan_empty_when_no_revisions():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        plan = build_revision_plan(project_dir, config)
        assert plan["revision_items"] == []
        assert plan["stale_artifacts"] == []
        assert "Không có REVISION_REQUIRED" in plan["summary"]


# ---------------------------------------------------------------------------
# T15 — build_revision_plan khi có REVISION_REQUIRED ghi downstream STALE
# ---------------------------------------------------------------------------

def test_t15_revision_plan_marks_downstream_stale():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        _populate_project_dir(project_dir, config)

        record_decision(project_dir, config,
                        artifact_id_str=ArtifactID.RESEARCH_QUESTION_AND_PICO.value,
                        decision=HumanDecision.REVISION_REQUIRED,
                        review_role=ReviewRole.PI_PROJECT_OWNER,
                        reason="PICO cần làm lại",
                        reviewer_ref=_reviewer_ref(ReviewRole.PI_PROJECT_OWNER),
                        automation_caller=False)

        plan = build_revision_plan(project_dir, config)
        assert len(plan["revision_items"]) == 1
        assert plan["revision_items"][0]["artifact_id"] == ArtifactID.RESEARCH_QUESTION_AND_PICO.value
        # Downstream artifacts bị đánh dấu STALE
        assert len(plan["stale_artifacts"]) > 0
        assert plan["no_overwrite_policy"] != ""


# ---------------------------------------------------------------------------
# T16 — ReviewLedger đọc đúng record sau khi persist
# ---------------------------------------------------------------------------

def test_t16_ledger_roundtrip_json():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()

        original = record_decision(
            project_dir, config,
            artifact_id_str=ArtifactID.CRF_DRAFT.value,
            decision=HumanDecision.REVISION_REQUIRED,
            review_role=ReviewRole.DATA_GOVERNANCE_QA_REVIEWER,
            reason="Biến số cần chuẩn hóa",
            required_actions=["Đặt lại codebook", "Gắn LOINC"],
            reviewer_ref=_reviewer_ref(ReviewRole.DATA_GOVERNANCE_QA_REVIEWER),
            automation_caller=False,
        )

        ledger = ReviewLedger(project_dir)
        records = ledger.read_all()
        assert len(records) == 1
        restored = records[0]
        assert restored.review_id == original.review_id
        assert restored.decision == HumanDecision.REVISION_REQUIRED
        assert restored.review_role == ReviewRole.DATA_GOVERNANCE_QA_REVIEWER
        assert restored.reviewer_identity_reference == _reviewer_ref(ReviewRole.DATA_GOVERNANCE_QA_REVIEWER)
        assert len(restored.required_actions) == 2


# ---------------------------------------------------------------------------
# T17 — list_review_queue không trả PII
# ---------------------------------------------------------------------------

def test_t17_review_queue_no_pii():
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = pathlib.Path(tmp)
        config = _make_config()
        _populate_project_dir(project_dir, config)
        items = list_review_queue(project_dir, config)
        for item in items:
            text = json.dumps(item).lower()
            assert "patient_id" not in text
            assert "mã bệnh nhân" not in text
            assert "họ tên" not in text
            assert "date_of_birth" not in text


# ---------------------------------------------------------------------------
# T18 — make_review_queue_item trả dict đúng cấu trúc
# ---------------------------------------------------------------------------

def test_t18_make_review_queue_item_structure():
    item = make_review_queue_item(
        project_id="SYNTH-001",
        artifact_id=ArtifactID.PROTOCOL_DRAFT,
        reason="Protocol cần kiểm tra design",
    )
    assert item["project_id"] == "SYNTH-001"
    assert item["artifact_id"] == ArtifactID.PROTOCOL_DRAFT.value
    assert item["auto_approve"] is False
    assert item["draft_only"] is True
    assert item["human_review_required"] is True
    assert len(item["primary_roles"]) >= 1
    assert ReviewRole.IRB_ETHICS_COMMITTEE.value in item["primary_roles"]

    review_pack = make_review_queue_item(
        project_id="SYNTH-001",
        artifact_id=ArtifactID.REVIEW_PACK,
        reason="Gói phản biện cần phản biện độc lập",
    )
    assert review_pack["auto_approve"] is False
    assert ReviewRole.INDEPENDENT_PEER_REVIEWER.value in review_pack["primary_roles"]


# ---------------------------------------------------------------------------
# T19 — review_id và audit_event_id có tiền tố đúng
# ---------------------------------------------------------------------------

def test_t19_id_prefixes():
    rid = _make_review_id("SYNTH-001", "02_PROTOCOL_DRAFT")
    assert rid.startswith("RV-")
    aid = _make_audit_event_id(rid)
    assert aid.startswith("AE-")


# ---------------------------------------------------------------------------
# T20 — CLI parser có đủ 4 subcommand V4.3.4
# ---------------------------------------------------------------------------

def test_t20_cli_has_4_new_subcommands():
    from research_project.project_cli import _build_parser
    parser = _build_parser()

    # Extract all subcommand names from parser
    subparsers_actions = [
        action for action in parser._actions
        if hasattr(action, "choices") and action.choices
    ]
    assert len(subparsers_actions) >= 1
    subcommand_names = set(subparsers_actions[0].choices.keys())

    assert "project-review-list" in subcommand_names
    assert "project-review-record" in subcommand_names
    assert "project-review-status" in subcommand_names
    assert "project-revision-plan" in subcommand_names
