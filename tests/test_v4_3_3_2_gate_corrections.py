"""
test_v4_3_3_2_gate_corrections.py — 15 tests cho V4.3.3.2 gate semantic corrections.

Phase E / V4.3.3.2:
  - D-R13: Semantic correction (không false positive trên safety instruction text)
  - D-R8:  Evidence state correction (REQUIRE_HUMAN_EVIDENCE_INPUT khi manifest rỗng)
  - Integration: QA end-to-end không FAIL trên fresh DRAFT project

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
"""

from __future__ import annotations

import sys


# ---------------------------------------------------------------------------
# Invariant 0 — không import module gọi API/network
# ---------------------------------------------------------------------------
def test_v4332_inv0_no_api_imports():
    """research_project import không kéo thêm client API / network nào."""
    forbidden = {"openai", "anthropic", "requests", "httpx", "aiohttp"}
    before = set(sys.modules.keys())

    import research_project  # noqa: F401

    after = set(sys.modules.keys())
    newly_loaded = (after - before) & forbidden
    assert not newly_loaded, f"Forbidden network modules imported: {newly_loaded}"


# ---------------------------------------------------------------------------
# Nhóm 1 — contains_external_action_positive: safety text PASS
# ---------------------------------------------------------------------------

def test_v4332_dr13_safety_no_submit():
    """Safety instruction 'không được tự nộp' KHÔNG được bị coi là external action."""
    from research_project import contains_external_action_positive
    text = "Quy tắc an toàn: KHÔNG được tự nộp đề cương lên Hội đồng Đạo đức."
    assert not contains_external_action_positive(text), (
        "D-R13: 'không được tự nộp' là safety instruction, không phải action thật"
    )


def test_v4332_dr13_safety_blocked_publish():
    """Safety instruction 'blocked' + 'publish' KHÔNG phải action thật."""
    from research_project import contains_external_action_positive
    text = "External submission is blocked. Do not publish this draft."
    assert not contains_external_action_positive(text), (
        "D-R13: 'blocked' + 'publish' trong ngữ cảnh phủ định = PASS"
    )


def test_v4332_dr13_safety_forbidden_email():
    """'Cấm' + 'email' → phủ định, không phải action thật."""
    from research_project import contains_external_action_positive
    text = "Cấm: không email_to bất kỳ địa chỉ bên ngoài khi chưa được PI phê duyệt."
    assert not contains_external_action_positive(text), (
        "D-R13: 'cấm' + 'email_to' là instruction cấm, phải PASS"
    )


def test_v4332_dr13_safety_do_not_post():
    """'Do not post_to' → phủ định an toàn."""
    from research_project import contains_external_action_positive
    text = "DO NOT post_to any public registry without human approval."
    assert not contains_external_action_positive(text), (
        "D-R13: 'DO NOT post_to' = phủ định → PASS"
    )


def test_v4332_dr13_real_action_submit():
    """Action thật 'submit protocol to IRB' PHẢI bị phát hiện."""
    from research_project import contains_external_action_positive
    text = "Please submit protocol to IRB for approval."
    assert contains_external_action_positive(text), (
        "D-R13: action thật 'submit' không có phủ định → phải FAIL"
    )


def test_v4332_dr13_real_action_publish():
    """Action thật 'publish this manuscript' PHẢI bị phát hiện."""
    from research_project import contains_external_action_positive
    text = "We will publish this manuscript in Nature Medicine."
    assert contains_external_action_positive(text), (
        "D-R13: 'publish' không có phủ định → phải FAIL"
    )


def test_v4332_dr13_mixed_lines():
    """File có 1 dòng safety + 1 dòng action thật: PHẢI phát hiện action thật."""
    from research_project import contains_external_action_positive
    text = (
        "Quy tắc: KHÔNG được tự nộp khi chưa được phê duyệt.\n"
        "Tuy nhiên PI đã yêu cầu nộp hồ sơ ethics ngay hôm nay.\n"
    )
    assert contains_external_action_positive(text), (
        "D-R13: dòng có action thật không phủ định phải bị FAIL dù có dòng safety"
    )


def test_v4332_dr13_empty_content():
    """Nội dung rỗng → PASS (không có action)."""
    from research_project import contains_external_action_positive
    assert not contains_external_action_positive(""), (
        "D-R13: nội dung rỗng không có action"
    )


# ---------------------------------------------------------------------------
# Nhóm 2 — D-R8 evidence_gate_state semantics
# ---------------------------------------------------------------------------

def test_v4332_dr8_empty_manifest_state(tmp_path):
    """Manifest rỗng → WARN + evidence_gate_state = REQUIRE_HUMAN_EVIDENCE_INPUT."""
    from research_project import (
        EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT,
        GateStatus,
    )
    from research_project.project_qa_runner import ProjectQARunner

    # Tạo evidence dir nhưng để manifest rỗng
    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    manifest = ev_dir / "evidence_manifest.csv"
    manifest.write_text("evidence_id,pmid,doi,title,status\n", encoding="utf-8")

    cfg = _make_config()
    runner = ProjectQARunner(tmp_path, cfg)
    result = runner._dr8_evidence_status()

    assert result.status == GateStatus.WARN, "Empty manifest → WARN (not PASS/FAIL)"
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT, (
        f"Expected {EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT}, got {result.evidence_gate_state}"
    )


def test_v4332_dr8_retracted_state(tmp_path):
    """Bằng chứng RETRACTED → FAIL + evidence_gate_state = BLOCK."""
    from research_project import EVIDENCE_GATE_STATE_BLOCK, GateStatus
    from research_project.project_qa_runner import ProjectQARunner

    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    manifest = ev_dir / "evidence_manifest.csv"
    manifest.write_text(
        "evidence_id,pmid,doi,title,status\n"
        "EV001,12345678,,Retracted Study,RETRACTED\n",
        encoding="utf-8",
    )

    cfg = _make_config()
    runner = ProjectQARunner(tmp_path, cfg)
    result = runner._dr8_evidence_status()

    assert result.status == GateStatus.FAIL, "RETRACTED evidence → FAIL"
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_BLOCK, (
        f"Expected {EVIDENCE_GATE_STATE_BLOCK}, got {result.evidence_gate_state}"
    )


def test_v4332_dr8_manual_review_state(tmp_path):
    """Bằng chứng MANUAL_REVIEW_REQUIRED → WARN + evidence_gate_state = REQUIRE_HUMAN_REVIEW."""
    from research_project import (
        EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW,
        GateStatus,
    )
    from research_project.project_qa_runner import ProjectQARunner

    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    manifest = ev_dir / "evidence_manifest.csv"
    manifest.write_text(
        "evidence_id,pmid,doi,title,status\n"
        "EV001,11111111,,Unverified Study,MANUAL_REVIEW_REQUIRED\n",
        encoding="utf-8",
    )

    cfg = _make_config()
    runner = ProjectQARunner(tmp_path, cfg)
    result = runner._dr8_evidence_status()

    assert result.status == GateStatus.WARN
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW


def test_v4332_dr8_verified_state(tmp_path):
    """Tất cả VERIFIED_BY_HUMAN → PASS + evidence_gate_state = PASS."""
    from research_project import EVIDENCE_GATE_STATE_PASS, GateStatus
    from research_project.project_qa_runner import ProjectQARunner

    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    manifest = ev_dir / "evidence_manifest.csv"
    manifest.write_text(
        "evidence_id,pmid,doi,title,status\n"
        "EV001,22222222,,Verified Study,VERIFIED_BY_HUMAN\n",
        encoding="utf-8",
    )

    cfg = _make_config()
    runner = ProjectQARunner(tmp_path, cfg)
    result = runner._dr8_evidence_status()

    assert result.status == GateStatus.PASS
    assert result.evidence_gate_state == EVIDENCE_GATE_STATE_PASS


def test_v4332_dr8_no_evidence_dir(tmp_path):
    """Không có thư mục evidence/ → SKIP (không phải WARN)."""
    from research_project import GateStatus
    from research_project.project_qa_runner import ProjectQARunner

    cfg = _make_config()
    runner = ProjectQARunner(tmp_path, cfg)
    result = runner._dr8_evidence_status()

    assert result.status == GateStatus.SKIP, "Không có evidence dir → SKIP"


# ---------------------------------------------------------------------------
# Nhóm 3 — Integration: fresh DRAFT project không FAIL D-R13
# ---------------------------------------------------------------------------

def test_v4332_integration_fresh_draft_dr13_no_false_positive(tmp_path):
    """Fresh DRAFT artifacts không gây false positive cho D-R13.

    Tạo artifact nội dung chứa safety instructions → D-R13 PASS.
    """
    from research_project import contains_external_action_positive

    # Nội dung điển hình của template artifact V4.3.3
    template_safety_content = """
# RESEARCH CHARTER — DRAFT

## Quy tắc an toàn bắt buộc
- Không được tự nộp đề cương mà không có PI phê duyệt.
- Không được publish bất kỳ kết quả nào trước khi PI ký.
- Không phép gửi tới bất kỳ registry nào (ClinicalTrials.gov / DRKS / WHO ICTRP).
- External submission is BLOCKED until human review is complete.
- Do not post_to any public endpoint without written approval.

## Placeholder
[REQUIRE_HUMAN_INPUT] — PI điền vào đây.
"""
    assert not contains_external_action_positive(template_safety_content), (
        "D-R13 integration: fresh DRAFT template chứa safety instructions phải PASS"
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_config():
    """Tạo ProjectConfig tối giản để khởi tạo QARunner."""
    from research_project import ProjectConfig, StudyType
    return ProjectConfig(
        project_id="TEST_V4332",
        title="Test Project V4.3.3.2",
        study_type=StudyType.CROSS_SECTIONAL,
        primary_objectives=["Mục tiêu test"],
        secondary_objectives=[],
        primary_outcomes=["Kết cục test"],
        secondary_outcomes=[],
        research_constraints={},
        data_mode="NO_REAL_DATA",
        external_actions_forbidden=True,
        draft_only=True,
        created_at="2026-06-28T00:00:00Z",
        version="0.1.0",
        human_owner="TEST_PI",
    )
