from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

import pytest  # noqa: E402 — guard đặt sau REPO để dùng Path đã có

# CI HERMETIC ĐƠN-REPO (16/08/2026): bộ kiểm này chấm chuẩn trên TOÀN WORKSPACE
# (.claude/agents + tools/ ở thư mục MẸ) — checkout một-repo không có chúng nên
# tool fail-closed ĐÚNG THIẾT KẾ và test đỏ oan. Skip CÓ KHAI BÁO, không giả đạt:
# phán quyết chuẩn-agent chỉ có nghĩa khi đứng trong workspace thật (máy bác sĩ).
_WORKSPACE_ME = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    not (_WORKSPACE_ME / ".claude" / "agents").is_dir(),
    reason="cần workspace gốc (.claude/agents ở thư mục mẹ) — CI checkout đơn-repo không chấm được chuẩn agent",
)

MODULE_PATH = REPO / "tools" / "verify_clinical_production_control_plane.py"
FIXED_NOW = "2026-07-16T00:00:00+00:00"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_clinical_production_control_plane", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_clinical_production_control_plane_is_connected_and_human_gated() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)

    assert report["kind"] == "clinical_production_control_plane_report"
    assert report["overall_status"] == "CONTROLLED_AUTOMATION_READY_WITH_HUMAN_GATES"
    assert report["fail_count"] == 0
    assert report["human_gate_count"] >= 2
    assert report["offline_controlled_automation_available"] is True
    assert report["auto_repair_available"] is True
    assert report["auto_agent_generation_available"] is True
    assert report["clinical_orchestration_available"] is True
    assert report["clinical_evidence_update_pipeline_available"] is True
    assert report["clinical_production_allowed"] is False
    assert report["real_patient_data_allowed"] is False
    assert report["auto_apply_allowed"] is False


def test_control_plane_checks_cover_requested_automation_surfaces() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    rows = {row["check_id"]: row for row in report["checks"]}

    assert set(rows) == {"CP1", "CP2", "CP3", "CP4", "CP5"}
    assert rows["CP1"]["status"] == "PASS"
    assert rows["CP2"]["status"] == "HUMAN_GATE"
    assert rows["CP3"]["status"] == "PASS"
    assert rows["CP4"]["status"] == "PASS"
    assert rows["CP5"]["status"] == "HUMAN_GATE"
    assert "self" in rows["CP1"]["title"].lower() or "Tự sửa" in rows["CP1"]["title"]
    assert "agent" in rows["CP2"]["title"].lower()
    assert "lâm sàng" in rows["CP3"]["title"].lower()


def test_markdown_report_keeps_fail_closed_flags_visible() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    markdown = mod.markdown_report(report)

    assert "Clinical Production Control Plane" in markdown
    assert "CONTROLLED_AUTOMATION_READY_WITH_HUMAN_GATES" in markdown
    assert "Clinical production allowed: `False`" in markdown
    assert "Real patient data allowed: `False`" in markdown
    assert "Auto-apply allowed: `False`" in markdown
    assert "Cần bác sĩ kiểm chứng" in markdown
