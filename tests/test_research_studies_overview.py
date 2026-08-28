"""Test tools/research_studies_overview.py — tổng quan 1 màn hình mọi đề tài G0-G10.

CHỈ dùng fixture study dir giả trong tmp_path (không đụng exports/ thật của dự
án). Tập trung vào: nhận diện đề tài (có checkpoint mới tính), cổng xa nhất,
freshness, blocked-detail, exclude regex, và thứ tự sắp xếp theo cập nhật gần
nhất — không kiểm phần in bảng (đã phủ qua render_text/render_md thủ công).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import research_studies_overview as OV  # noqa: E402


def _write_cp(study_dir: Path, gate: str, data: dict, mtime: float = None):
    study_dir.mkdir(parents=True, exist_ok=True)
    p = study_dir / f"{gate}_checkpoint.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8", newline="\n")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


class TestFindStudyDirs:
    def test_only_dirs_with_checkpoints_count(self, tmp_path):
        _write_cp(tmp_path / "REAL-STUDY", "G0", {"gate": "G0"})
        (tmp_path / "NOT-A-STUDY").mkdir()  # thư mục rỗng, không checkpoint
        (tmp_path / "NOT-A-STUDY" / "notes.txt").write_text("x", encoding="utf-8", newline="\n")
        found = OV.find_study_dirs(tmp_path, exclude=None)
        names = [d.name for d in found]
        assert "REAL-STUDY" in names
        assert "NOT-A-STUDY" not in names

    def test_exclude_regex_filters_out(self, tmp_path):
        _write_cp(tmp_path / "PYTEST-FIXTURE-1", "G0", {"gate": "G0"})
        _write_cp(tmp_path / "REAL-STUDY-2026", "G0", {"gate": "G0"})
        found = OV.find_study_dirs(tmp_path, exclude=r"^PYTEST-")
        names = [d.name for d in found]
        assert "PYTEST-FIXTURE-1" not in names
        assert "REAL-STUDY-2026" in names

    def test_no_exclude_by_default_shows_everything(self, tmp_path):
        _write_cp(tmp_path / "PROBE-X", "G0", {"gate": "G0"})
        found = OV.find_study_dirs(tmp_path, exclude=None)
        assert any(d.name == "PROBE-X" for d in found)


class TestStudySummary:
    def test_current_gate_is_latest_present(self, tmp_path):
        base = time.time()
        d = tmp_path / "S1"
        _write_cp(d, "G0", {"gate": "G0"}, mtime=base)
        _write_cp(d, "G1", {"gate": "G1"}, mtime=base + 1)
        _write_cp(d, "G3", {"gate": "G3"}, mtime=base + 2)
        s = OV.study_summary(d)
        assert s["current_gate"] == "G3"
        assert s["gates_present"] == ["G0", "G1", "G3"]
        assert s["n_gates"] == 3

    def test_fresh_chain_not_flagged(self, tmp_path):
        base = time.time()
        d = tmp_path / "S2"
        _write_cp(d, "G0", {"gate": "G0"}, mtime=base)
        _write_cp(d, "G1", {"gate": "G1"}, mtime=base + 1)
        s = OV.study_summary(d)
        assert s["fresh"] is True
        assert s["stale_gates"] == []
        assert s["orphan_gates"] == []

    def test_stale_gate_detected(self, tmp_path):
        base = time.time()
        d = tmp_path / "S3"
        _write_cp(d, "G0", {"gate": "G0"}, mtime=base)
        _write_cp(d, "G1", {"gate": "G1"}, mtime=base + 10000)
        _write_cp(d, "G3", {"gate": "G3"}, mtime=base + 5)  # cũ hơn G1 nhiều
        s = OV.study_summary(d)
        assert s["fresh"] is False
        assert "G3" in s["stale_gates"]

    def test_blocked_gate_surfaces_detail(self, tmp_path):
        d = tmp_path / "S4"
        _write_cp(d, "G0", {
            "needs_input": {
                "blocked": True,
                "human_message": "Cần từ khóa tiếng Anh.",
                "remediation": {"command": "python tools/run_g0_auto.py --query-en ..."},
            },
        })
        s = OV.study_summary(d)
        assert s["blocked"] is True
        assert "tiếng Anh" in s["blocked_detail"]

    def test_not_blocked_when_no_needs_input(self, tmp_path):
        d = tmp_path / "S5"
        _write_cp(d, "G0", {"guardrail": {"passed": True}})
        s = OV.study_summary(d)
        assert s["blocked"] is False
        assert s["blocked_detail"] is None

    def test_topic_from_study_meta_preferred_over_g0(self, tmp_path):
        d = tmp_path / "S6"
        _write_cp(d, "G0", {"topic": "chủ đề G0"})
        (d / "study_meta.json").write_text(
            json.dumps({"title": "chủ đề chính thức"}), encoding="utf-8", newline="\n")
        s = OV.study_summary(d)
        assert s["topic"] == "chủ đề chính thức"

    def test_topic_falls_back_to_g0_when_no_meta(self, tmp_path):
        d = tmp_path / "S7"
        _write_cp(d, "G0", {"topic": "chủ đề G0"})
        s = OV.study_summary(d)
        assert s["topic"] == "chủ đề G0"

    def test_empty_study_dir_no_crash(self, tmp_path):
        d = tmp_path / "EMPTY"
        d.mkdir()
        s = OV.study_summary(d)
        assert s["current_gate"] is None
        assert s["gates_present"] == []


class TestBuildOverview:
    def test_sorted_by_last_updated_desc(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path / "OLDER", "G0", {"gate": "G0"}, mtime=base)
        _write_cp(tmp_path / "NEWER", "G0", {"gate": "G0"}, mtime=base + 1000)
        overview = OV.build_overview(tmp_path, exclude=None)
        names = [s["study"] for s in overview["studies"]]
        assert names.index("NEWER") < names.index("OLDER")

    def test_counts_blocked_and_stale(self, tmp_path):
        base = time.time()
        _write_cp(tmp_path / "BLOCKED-1", "G0", {
            "needs_input": {"blocked": True, "human_message": "cần input"},
        }, mtime=base)
        _write_cp(tmp_path / "OK-1", "G0", {"guardrail": {"passed": True}}, mtime=base)
        overview = OV.build_overview(tmp_path, exclude=None)
        assert overview["n_studies"] == 2
        assert overview["n_blocked"] == 1

    def test_missing_exports_dir_returns_empty(self, tmp_path):
        overview = OV.build_overview(tmp_path / "does-not-exist", exclude=None)
        assert overview["n_studies"] == 0
        assert overview["studies"] == []


class TestRenderers:
    def test_render_text_and_md_no_crash_on_empty(self):
        empty = {"n_studies": 0, "n_blocked": 0, "n_stale": 0, "studies": []}
        assert "0 đề tài" in OV.render_text(empty)
        assert "0 đề tài" in OV.render_md(empty)

    def test_render_text_includes_study_name(self, tmp_path):
        _write_cp(tmp_path / "DEMO-2026", "G0", {"topic": "demo"})
        overview = OV.build_overview(tmp_path, exclude=None)
        text = OV.render_text(overview)
        assert "DEMO-2026" in text
