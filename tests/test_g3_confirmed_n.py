"""Test cho --confirmed-n của cổng G3 (tools/run_g3_auto.py) — thêm 2026-07-17.

Phát hiện thật: bác sĩ báo "Mẫu được chốt là 1000 mẫu" cho đề tài khảo sát
hài lòng bệnh nhân C1a, BVQY175 — trước đây G3 CHỈ tính N từ effect size,
KHÔNG có chỗ ghi nhận khi bác sĩ/chủ nhiệm CHỐT một N thực tế khác (thường
theo khả năng thu thập/hành chính, không nhất thiết bằng N tối thiểu tính
theo thống kê). --confirmed-n ghi SONG SONG cả hai — KHÔNG thay thế công thức
— và cảnh báo khi N chốt thấp hơn N tối thiểu (nguy cơ underpowered).

Test cấp CLI (subprocess) theo đúng quy ước của test_gate_blocked_contract.py.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
import gate_contract as GC  # noqa: E402


def _mk_upstream(study_dir: Path):
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G0",
        "topic": "Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh",
        "base_query": "patient satisfaction outpatient",
    }, ensure_ascii=False), encoding="utf-8", newline="\n")
    (study_dir / "G1_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G1",
        "design": {"internal_code": "cross_sectional", "primary": "Cắt ngang mô tả",
                   "reporting_standard": "STROBE"},
        "effect_size_samples": [],
    }, ensure_ascii=False), encoding="utf-8", newline="\n")


def _run(study: str, extra=None):
    args = [PYTHON, str(TOOLS_DIR / "run_g3_auto.py"), "--study", study]
    if extra:
        args += extra
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)


def _load_cp(study_dir: Path) -> dict:
    return json.loads((study_dir / "G3_checkpoint.json").read_text(encoding="utf-8"))


def _load_artifact(study_dir: Path, study: str) -> str:
    return (study_dir / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


@pytest.fixture
def study_dir(request):
    name = f"PYTEST-CONFN-{request.node.name[-20:].replace('[', '').replace(']', '')}"
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    try:
        yield d
    finally:
        _rmtree_retry(d)


class TestConfirmedNAdequate:
    """N chốt >= N tối thiểu tính toán → ĐẠT, không cảnh báo underpowered."""

    def test_confirmed_n_recorded_in_checkpoint(self, study_dir):
        _mk_upstream(study_dir)
        res = _run(study_dir.name, [
            "--effect-size", "0.5", "--effect-type", "OR", "--dropout", "0.1",
            "--confirmed-n", "1000",
        ])
        assert res.returncode == GC.EXIT_OK, res.stdout[-1500:]
        cp = _load_cp(study_dir)
        assert cp["confirmed_n"] == 1000
        assert cp["n_adjusted"] < 1000  # Wilson p=0.5,e=0.05,dropout10% → 428
        assert cp["confirmed_n_adequate"] is True

    def test_artifact_shows_adat_and_margin_of_error(self, study_dir):
        _mk_upstream(study_dir)
        _run(study_dir.name, [
            "--effect-size", "0.5", "--effect-type", "OR", "--dropout", "0.1",
            "--confirmed-n", "1000",
        ])
        text = _load_artifact(study_dir, study_dir.name)
        assert "PHẦN 2b" in text
        assert "1000" in text
        assert "ĐẠT" in text
        assert "margin of error" in text.lower()

    def test_pinned_to_study_meta_and_restored_on_rerun(self, study_dir):
        _mk_upstream(study_dir)
        _run(study_dir.name, [
            "--effect-size", "0.5", "--effect-type", "OR", "--dropout", "0.1",
            "--confirmed-n", "1000",
        ])
        meta = GC.load_study_meta(study_dir)
        assert meta["gate_params"]["G3"]["confirmed_n"] == 1000

        # Chạy lại KHÔNG truyền --confirmed-n → phải tự khôi phục từ study_meta.json.
        res2 = _run(study_dir.name)
        assert res2.returncode == GC.EXIT_OK, res2.stdout[-1500:]
        assert "Khôi phục confirmed_n=1000" in res2.stdout
        cp2 = _load_cp(study_dir)
        assert cp2["confirmed_n"] == 1000


class TestConfirmedNUnderpowered:
    """N chốt < N tối thiểu tính toán → CẢNH BÁO rõ ràng, KHÔNG âm thầm chấp nhận."""

    def test_confirmed_n_below_minimum_flags_warning(self, study_dir):
        _mk_upstream(study_dir)
        res = _run(study_dir.name, [
            "--effect-size", "0.5", "--effect-type", "OR", "--dropout", "0.1",
            "--confirmed-n", "50",
        ])
        assert res.returncode == GC.EXIT_OK, res.stdout[-1500:]
        cp = _load_cp(study_dir)
        assert cp["confirmed_n"] == 50
        assert cp["confirmed_n_adequate"] is False
        text = _load_artifact(study_dir, study_dir.name)
        assert "CẢNH BÁO" in text
        assert "underpowered" in text.lower() or "THIẾU LỰC THỐNG KÊ" in text


class TestConfirmedNAbsentUnchanged:
    """Không truyền --confirmed-n → hành vi giữ NGUYÊN như trước (không hồi quy)."""

    def test_no_confirmed_n_section_when_absent(self, study_dir):
        _mk_upstream(study_dir)
        res = _run(study_dir.name, [
            "--effect-size", "0.5", "--effect-type", "OR", "--dropout", "0.1",
        ])
        assert res.returncode == GC.EXIT_OK, res.stdout[-1500:]
        cp = _load_cp(study_dir)
        assert cp["confirmed_n"] is None
        assert cp["confirmed_n_adequate"] is None
        text = _load_artifact(study_dir, study_dir.name)
        assert "PHẦN 2b" not in text
