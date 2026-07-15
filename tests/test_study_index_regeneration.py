"""Test STUDY_INDEX.md sống — trạng thái đọc checkpoint THẬT thay vì cố định
"🔴 Mới" mãi mãi sau scaffold (bug tìm thấy 2026-07-15: STUDY_INDEX.md không
bao giờ được viết lại sau lúc scaffold, kể cả sau khi pipeline chạy hết G0-G10).

CHỈ dùng fixture tmp_path — không đụng exports/ thật.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import scaffold_research_project as SCAF  # noqa: E402


def _write_cp(study_dir: Path, gate: str, data: dict):
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / f"{gate}_checkpoint.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8")


class TestLastGateToken:
    def test_single_gate(self):
        assert SCAF._last_gate_token("G3") == "G3"

    def test_range_picks_highest(self):
        assert SCAF._last_gate_token("G0-G1") == "G1"
        assert SCAF._last_gate_token("G3-G5") == "G5"
        assert SCAF._last_gate_token("G7-G9") == "G9"

    def test_plus_picks_highest(self):
        assert SCAF._last_gate_token("G1+G7") == "G7"


class TestRowStatus:
    def test_no_checkpoint_is_red(self, tmp_path):
        assert SCAF._row_status("G3", tmp_path) == "🔴 Chưa có"

    def test_present_not_blocked_is_done(self, tmp_path):
        _write_cp(tmp_path, "G0", {"guardrail": {"passed": True}})
        assert SCAF._row_status("G0", tmp_path) == "✅ Xong"

    def test_present_blocked_is_draft(self, tmp_path):
        _write_cp(tmp_path, "G3", {
            "needs_input": {"blocked": True, "human_message": "cần effect size"},
        })
        assert SCAF._row_status("G3", tmp_path) == "🚧 Dự thảo — chờ input"

    def test_range_uses_last_gate_checkpoint(self, tmp_path):
        # "G3-G5": chỉ G5 có checkpoint -> tính theo G5, bỏ qua G3 thiếu.
        _write_cp(tmp_path, "G5", {"guardrail": {"passed": True}})
        assert SCAF._row_status("G3-G5", tmp_path) == "✅ Xong"

    def test_corrupt_checkpoint_json_is_red_not_crash(self, tmp_path):
        tmp_path.mkdir(exist_ok=True)
        (tmp_path / "G0_checkpoint.json").write_text("{not valid json", encoding="utf-8")
        assert SCAF._row_status("G0", tmp_path) == "🔴 Chưa có"


class TestRegenerateStudyIndex:
    def test_fresh_dir_all_red(self, tmp_path):
        p = SCAF.regenerate_study_index("DEMO", tmp_path, "DEMO")
        text = p.read_text(encoding="utf-8")
        assert text.count("🔴 Chưa có") == len(SCAF.SCAFFOLD_FILES)
        assert "✅ Xong" not in text

    def test_reflects_real_progress_after_gates_run(self, tmp_path):
        _write_cp(tmp_path, "G0", {"guardrail": {"passed": True}})
        _write_cp(tmp_path, "G1", {"guardrail": {"passed": True}})
        p = SCAF.regenerate_study_index("DEMO", tmp_path, "DEMO")
        text = p.read_text(encoding="utf-8")
        lines = {ln.split("|")[1].strip(): ln for ln in text.splitlines() if ln.startswith("| ")}
        assert "✅ Xong" in lines["00"]  # G0
        assert "✅ Xong" in lines["02"]  # G0 (PICO)
        assert "🔴 Chưa có" in lines["06"]  # G2 chưa chạy

    def test_rerun_updates_previously_red_rows(self, tmp_path):
        p = SCAF.regenerate_study_index("DEMO", tmp_path, "DEMO")
        assert "🔴 Chưa có" in p.read_text(encoding="utf-8")
        _write_cp(tmp_path, "G9", {"guardrail": {"passed": True}})
        p = SCAF.regenerate_study_index("DEMO", tmp_path, "DEMO")
        text = p.read_text(encoding="utf-8")
        row_20 = [ln for ln in text.splitlines() if ln.startswith("| 20 ")][0]
        assert "✅ Xong" in row_20

    def test_header_no_longer_claims_static_new(self, tmp_path):
        p = SCAF.regenerate_study_index("DEMO", tmp_path, "DEMO")
        text = p.read_text(encoding="utf-8")
        assert "tất cả 🔴" not in text  # câu cũ gây hiểu lầm đã bị bỏ

    def test_disclaimer_present(self, tmp_path):
        p = SCAF.regenerate_study_index("DEMO", tmp_path, "DEMO")
        assert "Cần bác sĩ kiểm chứng" in p.read_text(encoding="utf-8")
