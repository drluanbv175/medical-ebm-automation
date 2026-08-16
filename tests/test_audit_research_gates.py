from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import audit_research_gates as ARG  # noqa: E402
import gate_contract as GC  # noqa: E402


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8", newline="\n")
    return path


def _cp(out_dir: Path, gate: str, payload: dict) -> Path:
    data = {"gate": gate, "guardrail": {"passed": True}}
    data.update(payload)
    return _write_json(out_dir / f"{gate}_checkpoint.json", data)


def test_new_study_points_to_g0_with_topic_command(tmp_path):
    report = ARG.audit_gates("AUTO-NEW", out_dir=tmp_path, topic="Tỷ lệ kiểm soát huyết áp", write=False)

    assert report["overall_status"] == "ACTION_REQUIRED"
    assert report["current_actionable_gate"] == "G0"
    assert report["artifact_issue_count"] > 0
    g0 = report["pipeline_gates"][0]
    assert g0["status"] == ARG.STATUS_MISSING
    assert "run_g0_auto.py" in g0["next_action"]
    assert g0["release_contract"]["verdict"] == ARG.RELEASE_AUTO_ACTION
    assert g0["release_contract"]["can_release_to_next_gate"] is False
    assert g0["release_contract"]["responsible_actor"] == "agent"
    assert "Tỷ lệ kiểm soát huyết áp" in g0["next_action"]


def test_hard_gate_draft_requires_real_irb_signal(tmp_path):
    _cp(tmp_path, "G2", {"g2_irb_number": "[CẦN BỔ SUNG]"})

    report = ARG.audit_gates("AUTO-IRB", out_dir=tmp_path, write=False)
    g2 = next(row for row in report["pipeline_gates"] if row["gate"] == "G2")

    assert g2["status"] == ARG.STATUS_NEEDS_REAL
    assert g2["real_signal"]["key"] == "irb_approved"
    assert g2["real_signal"]["present"] is False
    assert "IRB" in g2["next_action"]
    assert g2["release_contract"]["verdict"] == ARG.RELEASE_HUMAN_EVIDENCE
    assert g2["release_contract"]["prevents_downstream"] is True
    assert g2["release_contract"]["responsible_actor"] == "human_pi_or_irb"


def test_hard_gate_locks_when_meta_signal_is_present(tmp_path):
    _cp(tmp_path, "G2", {"g2_irb_number": "[CẦN BỔ SUNG]"})
    _write_json(tmp_path / "study_meta.json", {"irb_approved": True})

    report = ARG.audit_gates("AUTO-IRB-LOCK", out_dir=tmp_path, write=False)
    g2 = next(row for row in report["pipeline_gates"] if row["gate"] == "G2")

    assert g2["status"] == ARG.STATUS_LOCKED
    assert g2["real_signal"]["present"] is True
    assert g2["release_contract"]["verdict"] == ARG.RELEASE_LOCKED


def test_gate_requirement_manifest_detects_artifact_and_metadata(tmp_path):
    _cp(tmp_path, "G0", {})
    _write_json(tmp_path / "study_meta.json", {"title": "Đề tài X"})
    (tmp_path / "G0_A1_PICO_FINER_AUTO.md").write_text("PICO", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-MANIFEST", out_dir=tmp_path, write=False)
    g0 = next(row for row in report["pipeline_gates"] if row["gate"] == "G0")

    assert g0["automation_profile"]["mode"] == "AUTO_DRAFT"
    assert g0["artifact_readiness"]["status"] == "PASS"
    assert "pico_finer" in g0["artifact_readiness"]["present"]
    assert g0["metadata_readiness"]["status"] == "PASS"
    assert "topic_or_title" in g0["metadata_readiness"]["present"]


def test_ready_checkpoint_missing_required_artifact_is_actionable(tmp_path):
    _cp(tmp_path, "G0", {})
    _write_json(tmp_path / "study_meta.json", {"title": "Đề tài X"})

    report = ARG.audit_gates("AUTO-MISSING-ARTIFACT", out_dir=tmp_path, write=False)
    g0 = next(row for row in report["pipeline_gates"] if row["gate"] == "G0")

    assert g0["status"] == ARG.STATUS_READY
    assert g0["artifact_readiness"]["status"] == "MISSING_REQUIRED"
    assert report["current_actionable_gate"] == "G0"
    assert "Thiếu artifact bắt buộc" in g0["next_action"]


def test_dependency_readiness_surfaces_missing_analysis_locks(tmp_path):
    _cp(tmp_path, "G6", {})
    (tmp_path / "G6_A7_ANALYSIS_SCRIPTS_AUTO.md").write_text(
        "analysis syntax", encoding="utf-8"
    )
    _write_json(tmp_path / "study_meta.json", {"irb_approved": True})

    report = ARG.audit_gates("AUTO-DEPS", out_dir=tmp_path, write=False)
    g6 = next(row for row in report["pipeline_gates"] if row["gate"] == "G6")

    assert report["dependency_issue_count"] > 0
    assert g6["dependency_readiness"]["status"] == "MISSING_REQUIRED"
    assert "sap_locked" in g6["dependency_readiness"]["items"][0]["missing_signals"]
    assert "db_locked" in g6["dependency_readiness"]["items"][0]["missing_signals"]
    assert "điều kiện tiền kiểm" in g6["next_action"]


def test_data_pipeline_steps_block_until_real_irb_and_sap_signals(tmp_path):
    report = ARG.audit_gates("AUTO-DATA-DEPS", out_dir=tmp_path, write=False)
    intake = next(row for row in report["data_pipeline"] if row["step"] == "intake")
    data_lock = next(row for row in report["data_pipeline"] if row["step"] == "data_lock")

    assert intake["can_run"] is False
    assert "phê duyệt IRB/EC thật" in intake["blocked_by"]
    assert data_lock["can_run"] is False
    assert "SAP đã ký khóa trước khi xem dữ liệu" in data_lock["blocked_by"]

    _write_json(
        tmp_path / "study_meta.json",
        {"irb_approved": True, "sap_lock_date": "2026-07-13"},
    )
    report = ARG.audit_gates("AUTO-DATA-DEPS", out_dir=tmp_path, write=False)
    data_lock = next(row for row in report["data_pipeline"] if row["step"] == "data_lock")

    assert data_lock["can_run"] is True
    assert data_lock["blocked_by"] == []


def test_action_queue_routes_new_study_to_agent_g0(tmp_path):
    report = ARG.audit_gates(
        "AUTO-QUEUE", out_dir=tmp_path, topic="Tỷ lệ kiểm soát huyết áp", write=False
    )

    first = report["action_queue"][0]
    assert first["source"] == "gate"
    assert first["gate"] == "G0"
    assert first["actor"] == "agent"
    assert first["can_auto_run"] is True
    assert "run_g0_auto.py" in first["next_action"]
    assert report["next_agent_action"] == first
    assert report["resume_contract"]["mode"] == "AUTO_RUN_ALLOWED"
    assert report["resume_contract"]["can_auto_resume"] is True
    assert report["resume_contract"]["next_command"] == first["next_action"]
    assert report["gate_release_summary"]["first_blocking_gate"]["gate"] == "G0"


def test_action_queue_marks_dependency_blocks_as_human_evidence(tmp_path):
    _cp(tmp_path, "G6", {})
    (tmp_path / "G6_A7_ANALYSIS_SCRIPTS_AUTO.md").write_text(
        "analysis syntax", encoding="utf-8"
    )
    _write_json(tmp_path / "study_meta.json", {"irb_approved": True})

    report = ARG.audit_gates("AUTO-QUEUE-DEPS", out_dir=tmp_path, write=False)
    g6_item = next(
        item for item in report["action_queue"]
        if item["source"] == "gate" and item.get("gate") == "G6"
    )

    assert g6_item["actor"] == "human_pi_or_data_manager"
    assert g6_item["can_auto_run"] is False
    assert "SAP đã ký khóa trước khi xem dữ liệu" in g6_item["blocked_by"]
    assert "dataset phân tích đã khóa" in g6_item["blocked_by"]


def test_action_queue_includes_blocked_data_steps_until_irb(tmp_path):
    report = ARG.audit_gates("AUTO-QUEUE-DATA", out_dir=tmp_path, write=False)
    intake_item = next(
        item for item in report["action_queue"]
        if item["source"] == "data_pipeline" and item.get("step") == "intake"
    )

    assert intake_item["actor"] == "human_pi_or_irb"
    assert intake_item["can_auto_run"] is False
    assert "phê duyệt IRB/EC thật" in intake_item["blocked_by"]


def test_next_agent_action_does_not_skip_human_gate_blocker(tmp_path):
    _cp(tmp_path, "G0", {})
    _cp(tmp_path, "G1", {
        "quality_gate": {
            "status": "PASS_G1_CONFIRMED",
            "pending_actions": [],
        },
    })
    _cp(tmp_path, "G2", {"g2_irb_number": "[CẦN BỔ SUNG]"})
    _write_json(tmp_path / "study_meta.json", {
        "title": "Đề tài X",
        "design_code": "rct",
        "gate_params": {
            "G1": {
                "design": "rct",
                "design_confirmed": True,
                "objectives": ["Mục tiêu đã chốt"],
                "primary_outcome": "Kết cục chính tại 12 tuần",
                "population": "Quần thể đích",
                "setting": "Bệnh viện",
                "study_period": "2027-2028",
                "feasibility_confirmed": True,
                "evidence_review_confirmed": True,
                "reviewed_by_role": "methodologist",
                "reviewed_at": "2026-07-27T10:00:00+07:00",
            },
        },
    })
    (tmp_path / "G0_A1_PICO_FINER_AUTO.md").write_text("PICO", encoding="utf-8", newline="\n")
    (tmp_path / "G1_A2_PROTOCOL_DESIGN_AUTO.md").write_text(
        "design rationale", encoding="utf-8"
    )
    (tmp_path / "G1_A1b_PROJECT_CHARTER_AUTO.md").write_text(
        "project charter", encoding="utf-8"
    )
    (tmp_path / "G1_A2b_EVIDENCE_LEDGER_AUTO.md").write_text(
        "evidence ledger", encoding="utf-8"
    )
    (tmp_path / "G1_A13_IMPLEMENTATION_PLAN_AUTO.md").write_text(
        "implementation plan", encoding="utf-8"
    )
    (tmp_path / "G1_A13b_RISK_REGISTER_AUTO.md").write_text(
        "risk register", encoding="utf-8"
    )
    (tmp_path / "G2_A3_ETHICS_PACKAGE_AUTO.md").write_text("ethics", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-HUMAN-BLOCK", out_dir=tmp_path, write=False)

    assert report["action_queue"][0]["gate"] == "G2"
    assert report["action_queue"][0]["can_auto_run"] is False
    assert report["next_agent_action"] is None
    assert report["resume_contract"]["mode"] == "HUMAN_GATE_REQUIRED"
    assert report["resume_contract"]["can_auto_resume"] is False
    assert report["resume_contract"]["human_blocker"]["gate"] == "G2"
    assert report["resume_contract"]["next_command"] is None
    assert report["gate_release_summary"]["first_blocking_gate"]["gate"] == "G2"


def test_blocked_needs_input_surfaces_remediation_command(tmp_path):
    _cp(
        tmp_path,
        "G3",
        {
            "needs_input": GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                "Cần effect size có nguồn thật.",
                "python3 tools/run_g3_auto.py --study AUTO --effect-size 0.5",
                ["effect_size"],
            ),
        },
    )

    report = ARG.audit_gates("AUTO-BLOCKED", out_dir=tmp_path, write=False)
    g3 = next(row for row in report["pipeline_gates"] if row["gate"] == "G3")

    assert g3["status"] == ARG.STATUS_BLOCKED
    assert "run_g3_auto.py" in g3["next_action"]
    assert "effect-size" in g3["next_action"]


def test_data_pipeline_reads_cleaning_and_lock_status(tmp_path):
    _write_json(
        tmp_path / "study_meta.json",
        {
            "real_data_cleaning": {
                "status": "CLEAN_REQUIRES_QUERY_RESOLUTION",
                "clean_dataset_path": "03_clean_working/df_clean.csv",
                "open_query_count": 2,
            },
            "real_data_lock": {
                "status": "BLOCKED_DATA_LOCK_REQUIREMENTS",
                "blockers": ["open_query_log"],
            },
        },
    )

    report = ARG.audit_gates("AUTO-DATA", out_dir=tmp_path, write=False)
    cleaning = next(row for row in report["data_pipeline"] if row["step"] == "cleaning")
    lock = next(row for row in report["data_pipeline"] if row["step"] == "data_lock")

    assert cleaning["status"] == "CLEAN_REQUIRES_QUERY_RESOLUTION"
    assert cleaning["open_query_count"] == 2
    assert lock["blockers"] == ["open_query_log"]


def test_g0_draft_quality_gate_is_visible_not_silently_ready(tmp_path):
    """Hồi quy G0-01 (audit toàn diện G0-G10, HIGH): trước đây đài kiểm soát
    không đọc quality_gate của G0 — một checkpoint với PICO/kết cục chính CHƯA
    được bác sĩ chốt (DRAFT_READY_NEEDS_HUMAN_REVIEW) vẫn báo STATUS_READY/
    "Không cần hành động" nếu artifact+metadata đã có mặt trên đĩa."""
    _cp(tmp_path, "G0", {
        "quality_gate": {
            "status": "DRAFT_READY_NEEDS_HUMAN_REVIEW",
            "pending_actions": ["Chốt PICO trong study_meta.json"],
        },
    })
    _write_json(tmp_path / "study_meta.json", {"title": "Đề tài X"})
    (tmp_path / "G0_A1_PICO_FINER_AUTO-G0-DRAFT.md").write_text("PICO", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-G0-DRAFT", out_dir=tmp_path, write=False)
    g0 = next(row for row in report["pipeline_gates"] if row["gate"] == "G0")

    assert g0["status"] == ARG.STATUS_NEEDS_REAL, g0
    assert g0["next_action"] == "Chốt PICO trong study_meta.json"


def test_g0_blocked_quality_gate_is_visible(tmp_path):
    _cp(tmp_path, "G0", {"quality_gate": {"status": "BLOCKED", "pending_actions": []}})
    (tmp_path / "G0_A1_PICO_FINER_AUTO-G0-BLOCK.md").write_text("PICO", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-G0-BLOCK", out_dir=tmp_path, write=False)
    g0 = next(row for row in report["pipeline_gates"] if row["gate"] == "G0")

    assert g0["status"] == ARG.STATUS_GUARDRAIL_FAIL, g0
    assert "g0_quality_gate.py" in g0["next_action"]


def test_g0_checkpoint_truoc_2026_khong_bi_hoi_to(tmp_path):
    """Checkpoint CŨ (trước 2026-07-28, không có khối quality_gate) phải giữ
    nguyên hành vi cũ — không bị nhánh mới hồi tố phán BLOCK/NEEDS_REAL oan."""
    _cp(tmp_path, "G0", {})
    _write_json(tmp_path / "study_meta.json", {"title": "Đề tài X"})
    (tmp_path / "G0_A1_PICO_FINER_AUTO-G0-LEGACY.md").write_text("PICO", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-G0-LEGACY", out_dir=tmp_path, write=False)
    g0 = next(row for row in report["pipeline_gates"] if row["gate"] == "G0")

    assert g0["status"] == ARG.STATUS_READY, g0


def test_g7_blocked_quality_gate_is_visible_not_silently_passed(tmp_path):
    """Hồi quy G7-F2 (audit toàn diện G0-G10, HIGH): trước đây G7_QUALITY_REPORT.json
    hoàn toàn vô hình với đài kiểm soát này — một G7 bị BLOCKED bởi lớp chất lượng
    riêng (vd PII/số liệu bịa bắt được lúc chấm lại) vẫn lọt qua như bình thường vì
    chỉ cần artifact manuscript tồn tại + guardrail cache cũ."""
    _cp(tmp_path, "G7", {
        "quality_contract_version": "G7-2026.1",
        "quality_gate": {"status": "BLOCKED", "pending_actions": []},
    })
    (tmp_path / "G7_A8_MANUSCRIPT_AUTO-G7-BLOCK.md").write_text(
        "bản thảo có nội dung đã bị chặn bởi lớp chất lượng", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-G7-BLOCK", out_dir=tmp_path, write=False)
    g7 = next(row for row in report["pipeline_gates"] if row["gate"] == "G7")

    assert g7["status"] == ARG.STATUS_GUARDRAIL_FAIL, g7
    assert "g7_quality_gate.py" in g7["next_action"]


def test_g7_needs_real_quality_gate_is_visible(tmp_path):
    _cp(tmp_path, "G7", {
        "quality_contract_version": "G7-2026.1",
        "quality_gate": {
            "status": "DRAFT_READY_NEEDS_HUMAN_REVIEW",
            "pending_actions": ["Điền kết quả thật ở Bảng 2"],
        },
    })
    (tmp_path / "G7_A8_MANUSCRIPT_AUTO-G7-DRAFT.md").write_text(
        "bản thảo khung", encoding="utf-8", newline="\n")

    report = ARG.audit_gates("AUTO-G7-DRAFT", out_dir=tmp_path, write=False)
    g7 = next(row for row in report["pipeline_gates"] if row["gate"] == "G7")

    assert g7["status"] == ARG.STATUS_NEEDS_REAL, g7
    assert g7["next_action"] == "Điền kết quả thật ở Bảng 2"


def test_g9_blocked_quality_gate_is_visible_not_silently_passed(tmp_path):
    """Cùng lớp lỗi G7-F2, phát hiện thêm ở G9: artifact quality_report ĐÃ đăng
    ký required=True nhưng thiếu nhánh phân loại đọc quality_gate.status."""
    _cp(tmp_path, "G9", {
        "quality_contract_version": "G9-2026.2",
        "quality_gate": {"status": "BLOCKED", "pending_actions": []},
    })
    (tmp_path / "G9_A10_AUTHOR_INTEGRITY_AUTO-G9-BLOCK.md").write_text(
        "hồ sơ liêm chính", encoding="utf-8", newline="\n")
    _write_json(tmp_path / "G9_PUBLICATION_READINESS.json", {})

    report = ARG.audit_gates("AUTO-G9-BLOCK", out_dir=tmp_path, write=False)
    g9 = next(row for row in report["pipeline_gates"] if row["gate"] == "G9")

    assert g9["status"] == ARG.STATUS_GUARDRAIL_FAIL, g9
    assert "g9_quality_gate.py" in g9["next_action"]


def test_write_reports_and_updates_study_meta(tmp_path):
    report = ARG.audit_gates("AUTO-WRITE", out_dir=tmp_path, topic="Đề tài X", write=True)

    assert (tmp_path / ARG.REPORT_JSON).exists()
    assert (tmp_path / ARG.REPORT_MD).exists()
    assert (tmp_path / ARG.ACTION_QUEUE_JSON).exists()
    meta = json.loads((tmp_path / "study_meta.json").read_text(encoding="utf-8"))
    assert meta["research_gate_automation"]["json"] == ARG.REPORT_JSON
    assert meta["research_gate_automation"]["markdown"] == ARG.REPORT_MD
    assert meta["research_gate_automation"]["action_queue_json"] == ARG.ACTION_QUEUE_JSON
    assert meta["research_gate_automation"]["current_actionable_gate"] == report["current_actionable_gate"]
    assert (
        meta["research_gate_automation"]["dependency_issue_count"]
        == report["dependency_issue_count"]
    )
    assert (
        meta["research_gate_automation"]["artifact_issue_count"]
        == report["artifact_issue_count"]
    )
    assert (
        meta["research_gate_automation"]["metadata_issue_count"]
        == report["metadata_issue_count"]
    )
    assert meta["research_gate_automation"]["action_queue_size"] == len(
        report["action_queue"]
    )
    assert (
        meta["research_gate_automation"]["next_agent_action"]
        == report["next_agent_action"]
    )
    assert (
        meta["research_gate_automation"]["resume_contract"]
        == report["resume_contract"]
    )
    assert (
        meta["research_gate_automation"]["gate_release_summary"]
        == report["gate_release_summary"]
    )
    queue_payload = json.loads(
        (tmp_path / ARG.ACTION_QUEUE_JSON).read_text(encoding="utf-8")
    )
    assert queue_payload["resume_contract"] == report["resume_contract"]
    assert queue_payload["items"] == report["action_queue"]
