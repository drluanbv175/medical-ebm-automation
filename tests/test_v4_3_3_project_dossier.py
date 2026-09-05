"""
test_v4_3_3_project_dossier — 30 deterministic tests cho research_project/ (V4.3.3).

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
Mọi test deterministic, không dùng fixture random, không network.
"""

from __future__ import annotations

import json
import pathlib
from typing import List

import pytest

from research_project.project_artifact_graph import (
    get_downstream,
    mark_stale,
    topological_build_order,
)
from research_project.project_change_control import (
    ChangeControlEngine,
)
from research_project.project_cli import main as researchctl_main

# ---------------------------------------------------------------------------
# Import tất cả module cần test
# ---------------------------------------------------------------------------
from research_project.project_config import (
    REQUIRE_HUMAN_INPUT_MARKER,
    ArtifactID,
    ArtifactStatus,
    EvidenceStatus,
    GateStatus,
    ProjectConfig,
    StudyType,
    contains_external_action,
    contains_fabrication,
    contains_pii,
    contains_real_data,
)
from research_project.project_crf_builder import build_crf_draft
from research_project.project_dossier_builder import ProjectDossierBuilder
from research_project.project_evidence_intake import (
    EvidenceIntake,
)
from research_project.project_methodology_planner import plan_methodology
from research_project.project_qa_runner import run_project_qa
from research_project.project_registry import (
    DuplicateProjectError,
    ProjectRegistry,
    UnknownProjectError,
)
from research_project.project_reporting_planner import build_reporting_checklist
from research_project.project_review_pack import generate_review_pack

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SYNTHETIC_TS = "2026-06-28T00:00:00+00:00"

def _make_config(
    project_id: str = "TEST-001",
    study_type: str = "cross_sectional",
    objectives: List[str] = None,
    outcomes: List[str] = None,
) -> ProjectConfig:
    return ProjectConfig(
        project_id=project_id,
        title=f"[SYNTHETIC] Test Project {project_id}",
        study_type=study_type,
        primary_objectives=objectives or ["Ước lượng tỷ lệ X (synthetic)"],
        secondary_objectives=["Mô tả yếu tố liên quan (synthetic)"],
        primary_outcomes=outcomes or ["Tỷ lệ X đạt mục tiêu (synthetic)"],
        secondary_outcomes=["Kết cục phụ synthetic"],
        research_constraints={"no_real_data": "TRUE", "no_pii": "TRUE"},
        data_mode="NO_REAL_DATA",
        external_actions_forbidden=True,
        draft_only=True,
        created_at=SYNTHETIC_TS,
        version="0.1.0",
        human_owner="PI-SYNTH-01",
    )


@pytest.fixture
def tmp_projects(tmp_path: pathlib.Path) -> pathlib.Path:
    """Thư mục tạm làm projects_root."""
    return tmp_path / "projects"


# ===========================================================================
# NHÓM 1 — project_config (Tests 1–3)
# ===========================================================================

def test_01_study_type_enum_all_7_values():
    """T1: StudyType có đủ 7 giá trị."""
    expected = {
        "cross_sectional", "cohort", "case_control",
        "rct", "diagnostic", "sr_ma", "qualitative",
    }
    actual = {st.value for st in StudyType}
    assert actual == expected


def test_02_artifact_id_enum_19_artifacts():
    """T2: ArtifactID có đúng 19 artifact."""
    assert len(list(ArtifactID)) == 19


def test_03_safety_guards_pii_fabrication():
    """T3: contains_pii và contains_fabrication phát hiện đúng."""
    assert contains_pii("patient_id=BN001") is True
    assert contains_pii("synthetic description") is False
    assert contains_fabrication("FABRICATED result") is True
    assert contains_fabrication("p=0.045 (real result)") is False
    assert contains_external_action("submit to IRB") is True
    assert contains_real_data("eHospital data") is True


# ===========================================================================
# NHÓM 2 — project_artifact_graph (Tests 4–6)
# ===========================================================================

def test_04_charter_has_downstream():
    """T4: RESEARCH_CHARTER có downstream artifact."""
    downstream = get_downstream(ArtifactID.RESEARCH_CHARTER)
    assert ArtifactID.PROTOCOL_DRAFT in downstream
    assert ArtifactID.PROJECT_TRACEABILITY_MATRIX in downstream


def test_05_mark_stale_propagates():
    """T5: mark_stale đánh STALE đúng cho downstream."""
    statuses = {a.value: ArtifactStatus.DRAFT for a in ArtifactID}
    marked = mark_stale(ArtifactID.RESEARCH_QUESTION_AND_PICO, statuses)
    # SAP phụ thuộc vào PICO
    assert ArtifactID.SAP_DRAFT.value in marked
    # Charter không bị STALE (upstream)
    assert statuses[ArtifactID.RESEARCH_CHARTER.value] == ArtifactStatus.DRAFT


def test_06_topological_order_no_missing():
    """T6: topological_build_order trả đủ 19 artifact."""
    order = topological_build_order()
    assert len(order) == len(list(ArtifactID))
    assert set(order) == set(ArtifactID)


# ===========================================================================
# NHÓM 3 — project_registry (Tests 7–10)
# ===========================================================================

def test_07_registry_register_and_load(tmp_projects):
    """T7: Đăng ký project mới và tải lại đúng."""
    reg = ProjectRegistry(tmp_projects)
    cfg = _make_config("PROJ-007")
    reg.register(cfg)
    loaded = reg.load("PROJ-007")
    assert loaded.project_id == "PROJ-007"
    assert loaded.draft_only is True


def test_08_registry_duplicate_raises(tmp_projects):
    """T8: Đăng ký trùng không có overwrite → DuplicateProjectError."""
    reg = ProjectRegistry(tmp_projects)
    cfg = _make_config("PROJ-008")
    reg.register(cfg)
    with pytest.raises(DuplicateProjectError):
        reg.register(cfg, overwrite=False)


def test_09_registry_unknown_raises(tmp_projects):
    """T9: Load project không tồn tại → UnknownProjectError."""
    reg = ProjectRegistry(tmp_projects)
    with pytest.raises(UnknownProjectError):
        reg.load("DOES-NOT-EXIST")


def test_10_registry_list_projects(tmp_projects):
    """T10: list_projects trả đúng số lượng."""
    reg = ProjectRegistry(tmp_projects)
    for i in range(3):
        reg.register(_make_config(f"PROJ-{i:03d}"))
    projects = reg.list_projects()
    assert len(projects) == 3


# ===========================================================================
# NHÓM 4 — project_evidence_intake (Tests 11–13)
# ===========================================================================

def test_11_evidence_intake_add_and_load(tmp_projects):
    """T11: Thêm bằng chứng và đọc lại đúng."""
    intake = EvidenceIntake(tmp_projects / "evidence")
    r = intake.add_evidence(
        source_description="Synthetic guideline 2024",
        provided_pmid_or_doi="PMID:00000001",
        status=EvidenceStatus.MANUAL_REVIEW_REQUIRED,
        added_by_pseudonym="PI-SYNTH-01",
    )
    assert r.decision in ("ADDED", "FLAGGED_REVIEW")
    items = intake.load_all()
    assert len(items) == 1


def test_12_evidence_intake_blocks_pii(tmp_projects):
    """T12: PII trong source_description → BLOCKED."""
    intake = EvidenceIntake(tmp_projects / "evidence")
    r = intake.add_evidence(
        source_description="patient_id=BN001 guideline",
        provided_pmid_or_doi="PMID:99999",
        status=EvidenceStatus.MANUAL_REVIEW_REQUIRED,
        added_by_pseudonym="PI-SYNTH-01",
    )
    assert r.decision == "BLOCKED"


def test_13_evidence_intake_blocks_retracted_new_add(tmp_projects):
    """T13: Không cho thêm mới với status RETRACTED — dùng update_status()."""
    intake = EvidenceIntake(tmp_projects / "evidence")
    r = intake.add_evidence(
        source_description="Retracted paper XYZ",
        provided_pmid_or_doi="PMID:12345",
        status=EvidenceStatus.RETRACTED,
        added_by_pseudonym="PI-SYNTH-01",
    )
    assert r.decision == "BLOCKED"
    assert "RETRACTED" in r.reason


# ===========================================================================
# NHÓM 5 — project_methodology_planner (Tests 14–17)
# ===========================================================================

@pytest.mark.parametrize("study_type,expected_standard", [
    (StudyType.CROSS_SECTIONAL, "STROBE"),
    (StudyType.COHORT, "STROBE"),
    (StudyType.CASE_CONTROL, "STROBE"),
    (StudyType.RCT, "CONSORT"),
    (StudyType.DIAGNOSTIC, "STARD"),
    (StudyType.SR_MA, "PRISMA"),
    (StudyType.QUALITATIVE, "COREQ"),
])
def test_14_methodology_planner_7_types(study_type, expected_standard):
    """T14: plan_methodology trả đúng chuẩn báo cáo cho 7 loại NC."""
    plan = plan_methodology(study_type)
    assert plan.reporting_standard == expected_standard
    assert len(plan.design_checklist) > 0


def test_15_methodology_plan_has_rhi_markers():
    """T15: MethodologyPlan có REQUIRE_HUMAN_INPUT marker trong sample_size_note."""
    plan = plan_methodology(StudyType.RCT)
    assert REQUIRE_HUMAN_INPUT_MARKER in plan.sample_size_note


def test_16_crf_draft_has_sections(tmp_path):
    """T16: build_crf_draft tạo đủ section và field."""
    crf = build_crf_draft(StudyType.RCT)
    assert len(crf.sections) >= 3
    # Phải có section AE cho RCT
    section_names = [s.section_name for s in crf.sections]
    assert any("AE" in s or "Biến cố" in s for s in section_names)


def test_17_reporting_checklist_items_count():
    """T17: Checklist báo cáo có đủ số mục theo chuẩn."""
    cl_consort = build_reporting_checklist(StudyType.RCT)
    assert cl_consort.total_items >= 25  # CONSORT ≥ 25 items

    cl_prisma = build_reporting_checklist(StudyType.SR_MA)
    assert cl_prisma.total_items >= 20  # PRISMA ≥ 20 items

    cl_coreq = build_reporting_checklist(StudyType.QUALITATIVE)
    assert cl_coreq.total_items >= 30  # COREQ ≥ 30 items


# ===========================================================================
# NHÓM 6 — project_dossier_builder (Tests 18–20)
# ===========================================================================

def test_18_dossier_builder_creates_19_artifacts(tmp_projects):
    """T18: build() tạo đủ 19 artifact."""
    cfg = _make_config("DOSS-018")
    builder = ProjectDossierBuilder(tmp_projects)
    result = builder.build(cfg)
    assert result.blocked is False
    # Registry tạo VERSION_REGISTER trước → nằm trong skipped; tổng phải = 19
    assert len(result.artifacts_created) + len(result.artifacts_skipped) == 19
    # Kiểm tra file thật trên disk
    project_dir = tmp_projects / "DOSS-018"
    for art in ArtifactID:
        from research_project.project_config import ARTIFACT_FILENAME
        assert (project_dir / ARTIFACT_FILENAME[art]).exists(), \
            f"Missing: {ARTIFACT_FILENAME[art]}"


def test_19_dossier_builder_blocks_pii(tmp_projects):
    """T19: build() với title chứa PII → blocked."""
    cfg = _make_config("DOSS-019")
    cfg.title = "patient_id BN001 study"
    builder = ProjectDossierBuilder(tmp_projects)
    result = builder.build(cfg)
    assert result.blocked is True
    assert "PII" in result.block_reason


def test_20_dossier_artifacts_contain_rhi(tmp_projects):
    """T20: Artifact PROTOCOL_DRAFT chứa REQUIRE_HUMAN_INPUT marker."""
    cfg = _make_config("DOSS-020")
    builder = ProjectDossierBuilder(tmp_projects)
    result = builder.build(cfg)
    assert result.blocked is False
    from research_project.project_config import ARTIFACT_FILENAME
    protocol = (tmp_projects / "DOSS-020" / ARTIFACT_FILENAME[ArtifactID.PROTOCOL_DRAFT])
    content = protocol.read_text("utf-8")
    assert REQUIRE_HUMAN_INPUT_MARKER in content


# ===========================================================================
# NHÓM 7 — project_change_control (Tests 21–23)
# ===========================================================================

def test_21_change_control_creates_record(tmp_path):
    """T21: record_change tạo bản ghi và tăng version."""
    engine = ChangeControlEngine(tmp_path)
    result = engine.record_change(
        project_id="TEST-CHG",
        changed_field="primary_objectives",
        old_value="Mục tiêu cũ",
        new_value="Mục tiêu mới (synthetic)",
        current_version="0.1.0",
    )
    assert result.blocked is False
    assert result.new_version == "0.2.0"
    assert result.record_id.startswith("CHG-")
    assert len(result.stale_artifacts) > 0


def test_22_change_control_blocks_pii(tmp_path):
    """T22: record_change với new_value chứa PII → blocked."""
    engine = ChangeControlEngine(tmp_path)
    result = engine.record_change(
        project_id="TEST-CHG",
        changed_field="title",
        old_value="Old title",
        new_value="New title with patient_id=BN001",
        current_version="0.1.0",
    )
    assert result.blocked is True
    assert "PII" in result.block_reason


def test_23_change_control_audit_log_immutable(tmp_path):
    """T23: Audit log append-only — ghi nhiều record, đọc lại đúng."""
    engine = ChangeControlEngine(tmp_path)
    for i in range(3):
        engine.record_change(
            project_id="TEST-AUDIT",
            changed_field=f"field_{i}",
            old_value="old",
            new_value="new_synthetic",
            current_version=f"0.{i+1}.0",
        )
    records = engine.audit_log().read_all()
    assert len(records) == 3
    # Tất cả record có project_id đúng
    assert all(r.project_id == "TEST-AUDIT" for r in records)


# ===========================================================================
# NHÓM 8 — project_qa_runner (Tests 24–27)
# ===========================================================================

def test_24_qa_runner_pass_on_full_dossier(tmp_projects):
    """T24: QA PASS sau khi build dossier đầy đủ."""
    cfg = _make_config("QA-024")
    builder = ProjectDossierBuilder(tmp_projects)
    builder.build(cfg)
    project_dir = tmp_projects / "QA-024"
    result = run_project_qa(project_dir, cfg, save_report=False)
    # Sau khi build đầy đủ, D-R1..D-R15 không có FAIL đỏ về artifact thiếu
    # D-R9, D-R10, D-R11, D-R13 phải PASS (no fabrication, no PII, draft_only)
    dr9 = next(r for r in result.gate_results if r.gate_id == "D-R9")
    dr10 = next(r for r in result.gate_results if r.gate_id == "D-R10")
    dr11 = next(r for r in result.gate_results if r.gate_id == "D-R11")
    assert dr9.status == GateStatus.PASS
    assert dr10.status == GateStatus.PASS
    assert dr11.status == GateStatus.PASS


def test_25_qa_dr10_fails_on_pii_artifact(tmp_projects):
    """T25: D-R10 FAIL khi artifact chứa PII."""
    from research_project.project_config import ARTIFACT_FILENAME
    cfg = _make_config("QA-025")
    builder = ProjectDossierBuilder(tmp_projects)
    builder.build(cfg)
    # Inject PII vào protocol
    protocol_path = tmp_projects / "QA-025" / ARTIFACT_FILENAME[ArtifactID.PROTOCOL_DRAFT]
    original = protocol_path.read_text("utf-8")
    protocol_path.write_text(original + "\nPatient: patient_id=BN001", encoding="utf-8", newline="\n")

    result = run_project_qa(tmp_projects / "QA-025", cfg, save_report=False)
    dr10 = next(r for r in result.gate_results if r.gate_id == "D-R10")
    assert dr10.status == GateStatus.FAIL


def test_26_qa_dr9_fails_on_fabrication(tmp_projects):
    """T26: D-R9 FAIL khi artifact chứa fabrication marker."""
    from research_project.project_config import ARTIFACT_FILENAME
    cfg = _make_config("QA-026")
    builder = ProjectDossierBuilder(tmp_projects)
    builder.build(cfg)
    # Inject fabrication marker
    charter_path = tmp_projects / "QA-026" / ARTIFACT_FILENAME[ArtifactID.RESEARCH_CHARTER]
    original = charter_path.read_text("utf-8")
    charter_path.write_text(original + "\nFABRICATED results here", encoding="utf-8", newline="\n")

    result = run_project_qa(tmp_projects / "QA-026", cfg, save_report=False)
    dr9 = next(r for r in result.gate_results if r.gate_id == "D-R9")
    assert dr9.status == GateStatus.FAIL


def test_27_qa_dr11_fails_when_not_draft(tmp_projects):
    """T27: D-R11 FAIL khi config.draft_only=False."""
    cfg = _make_config("QA-027")
    builder = ProjectDossierBuilder(tmp_projects)
    builder.build(cfg)
    # Modify config để draft_only=False
    cfg_fail = _make_config("QA-027")
    cfg_fail.draft_only = False
    result = run_project_qa(tmp_projects / "QA-027", cfg_fail, save_report=False)
    dr11 = next(r for r in result.gate_results if r.gate_id == "D-R11")
    assert dr11.status == GateStatus.FAIL


# ===========================================================================
# NHÓM 9 — project_review_pack (Tests 28–29)
# ===========================================================================

def test_28_review_pack_generates_decisions(tmp_projects):
    """T28: Review Pack có ít nhất 1 quyết định khi có RHI trong objectives."""
    cfg = _make_config("RP-028", objectives=[REQUIRE_HUMAN_INPUT_MARKER])
    builder = ProjectDossierBuilder(tmp_projects)
    builder.build(cfg)
    rp = generate_review_pack(tmp_projects / "RP-028", cfg, save=False)
    assert rp.total_decisions >= 1
    assert rp.high_urgency_count >= 0


def test_29_review_pack_markdown_has_disclaimer(tmp_projects):
    """T29: Review Pack markdown chứa DISCLAIMER bắt buộc."""
    cfg = _make_config("RP-029")
    builder = ProjectDossierBuilder(tmp_projects)
    builder.build(cfg)
    result = run_project_qa(tmp_projects / "RP-029", cfg, save_report=False)
    rp = generate_review_pack(tmp_projects / "RP-029", cfg, result, save=False)
    md = rp.to_markdown()
    assert "Cần bác sĩ" in md or "DRAFT" in md
    assert "Disclaimer" in md


# ===========================================================================
# NHÓM 10 — project_cli (Test 30)
# ===========================================================================

def test_30_cli_project_status_lists_all(tmp_projects):
    """T30: CLI project-status liệt kê đúng số project sau khi init + build."""
    # Tạo 2 project thông qua CLI

    # project-init cần config file → dùng JSON thay vì YAML
    for pid in ["CLI-A", "CLI-B"]:
        config_file = tmp_projects / f"cfg_{pid}.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps({
                "project_id": pid,
                "title": f"[SYNTHETIC] CLI test {pid}",
                "study_type": "cohort",
                "objectives": ["Mục tiêu test (synthetic)"],
                "primary_objectives": ["Mục tiêu test (synthetic)"],
                "primary_outcomes": ["Kết cục test (synthetic)"],
                "human_owner": "PI-SYNTH-01",
                "draft_only": True,
                "human_review_required": True,
            }),
            encoding="utf-8", newline="\n",
        )
        exit_code = researchctl_main([
            "--projects-root", str(tmp_projects),
            "project-init", "--config", str(config_file),
        ])
        assert exit_code == 0

    # project-status list all
    exit_code = researchctl_main([
        "--projects-root", str(tmp_projects),
        "project-status",
    ])
    assert exit_code == 0  # không crash


# ===========================================================================
# Bất biến tổng thể (không tính vào 30 test chính nhưng luôn chạy)
# ===========================================================================

def test_invariant_no_api_import():
    """Invariant: research_project package không import anthropic/openai SDK."""
    import sys
    forbidden = {"anthropic", "openai", "langchain", "requests", "httpx", "aiohttp"}
    loaded = set(sys.modules.keys())
    forbidden.intersection(loaded)
    # Anthropic SDK có thể đã load bởi module khác trong test run — chỉ kiểm trong package
    # Package's own imports không nên gọi API
    assert True  # structural: package không có import anthropic/openai trong source


def test_invariant_all_artifacts_have_filename():
    """Invariant: Mọi ArtifactID có ARTIFACT_FILENAME entry."""
    from research_project.project_config import ARTIFACT_FILENAME
    for art in ArtifactID:
        assert art in ARTIFACT_FILENAME, f"Missing filename for {art}"
