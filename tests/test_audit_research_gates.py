from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import audit_research_gates as ARG  # noqa: E402
import gate_contract as GC  # noqa: E402


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
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
    assert "Tỷ lệ kiểm soát huyết áp" in g0["next_action"]


def test_hard_gate_draft_requires_real_irb_signal(tmp_path):
    _cp(tmp_path, "G2", {"g2_irb_number": "[CẦN BỔ SUNG]"})

    report = ARG.audit_gates("AUTO-IRB", out_dir=tmp_path, write=False)
    g2 = next(row for row in report["pipeline_gates"] if row["gate"] == "G2")

    assert g2["status"] == ARG.STATUS_NEEDS_REAL
    assert g2["real_signal"]["key"] == "irb_approved"
    assert g2["real_signal"]["present"] is False
    assert "IRB" in g2["next_action"]


def test_hard_gate_locks_when_meta_signal_is_present(tmp_path):
    _cp(tmp_path, "G2", {"g2_irb_number": "[CẦN BỔ SUNG]"})
    _write_json(tmp_path / "study_meta.json", {"irb_approved": True})

    report = ARG.audit_gates("AUTO-IRB-LOCK", out_dir=tmp_path, write=False)
    g2 = next(row for row in report["pipeline_gates"] if row["gate"] == "G2")

    assert g2["status"] == ARG.STATUS_LOCKED
    assert g2["real_signal"]["present"] is True


def test_gate_requirement_manifest_detects_artifact_and_metadata(tmp_path):
    _cp(tmp_path, "G0", {})
    _write_json(tmp_path / "study_meta.json", {"title": "Đề tài X"})
    (tmp_path / "G0_A1_PICO_FINER_AUTO.md").write_text("PICO", encoding="utf-8")

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


def test_write_reports_and_updates_study_meta(tmp_path):
    report = ARG.audit_gates("AUTO-WRITE", out_dir=tmp_path, topic="Đề tài X", write=True)

    assert (tmp_path / ARG.REPORT_JSON).exists()
    assert (tmp_path / ARG.REPORT_MD).exists()
    meta = json.loads((tmp_path / "study_meta.json").read_text(encoding="utf-8"))
    assert meta["research_gate_automation"]["json"] == ARG.REPORT_JSON
    assert meta["research_gate_automation"]["markdown"] == ARG.REPORT_MD
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
