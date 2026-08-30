"""Hồi quy cho quyết định ĐỔI QUY TRÌNH 30/08/2026 — bác sĩ chọn «Nâng G3
thành chặn cứng» (trả lời AskUserQuestion trong đợt «hoàn thiện cho xanh»).

Hợp đồng mới của run_g3_auto.py, hẹp có chủ ý:
- quality BLOCKED trên một lượt lẽ ra EXIT_OK ⇒ nâng thành EXIT_GUARDRAIL_FAIL
  (3 — mã có sẵn trong hợp đồng, không phát minh mã mới).
- Lớp chấm chất lượng CRASH trên lượt lẽ ra EXIT_OK ⇒ cũng 3 (fail-closed —
  từ khi cổng gánh việc chặn, exception nuốt im lặng là fail-open kiểu BH27).
- quality DRAFT_* ⇒ GIỮ mã cũ: đó là kết quả ĐÚNG của lượt tự động đầu tiên.
- exit_code vốn đã 2 (chờ input đời thực) ⇒ GIỮ 2, không đổi 2→3 làm sai nghĩa.

Test gọi main() trong-tiến-trình (monkeypatch sys.argv + G3Q) vì luật cần ép
trạng thái quality — subprocess không monkeypatch được.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g3_quality_gate as G3Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g3_auto as G3  # noqa: E402


def _mk_upstream(study_dir: Path) -> None:
    study_dir.mkdir(parents=True, exist_ok=True)
    study_dir.joinpath("G0_checkpoint.json").write_text(
        json.dumps(
            {
                "study": study_dir.name,
                "gate": "G0",
                "topic": "Tác dụng can thiệp X lên kết cục Y ở bệnh nhân ngoại trú",
                "base_query": "intervention X outcome Y",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    study_dir.joinpath("G1_checkpoint.json").write_text(
        json.dumps(
            {
                "study": study_dir.name,
                "gate": "G1",
                "design": {
                    "internal_code": "cohort",
                    "primary": "Cohort tiến cứu",
                    "reporting_standard": "STROBE 2007",
                },
                "effect_size_samples": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
        newline="\n",
    )


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
    name = f"PYTEST-G3HARD-{request.node.name[-18:].replace('[', '').replace(']', '')}"
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    _mk_upstream(d)
    try:
        yield d
    finally:
        _rmtree_retry(d)


def _fake_quality(status: str) -> dict:
    # Khối tối thiểu mà đoạn in tóm tắt của run_g3_auto.py đọc tới.
    return {"status": status, "automatic_criteria": [], "human_criteria": []}


def _main_with(monkeypatch, study: str, extra: list[str]) -> int:
    monkeypatch.setattr(
        sys, "argv", ["run_g3_auto.py", "--study", study, *extra]
    )
    return int(G3.main() or 0)


_OK_ARGS = ["--effect-size", "0.55", "--effect-type", "OR", "--dropout", "0.1"]


class TestHardBlock:
    def test_quality_blocked_escalates_ok_to_exit_3(self, study_dir, monkeypatch):
        monkeypatch.setattr(
            G3.G3Q,
            "evaluate_study",
            lambda *a, **k: _fake_quality(G3Q.STATUS_BLOCKED),
        )
        rc = _main_with(monkeypatch, study_dir.name, _OK_ARGS)
        assert rc == GC.EXIT_GUARDRAIL_FAIL, (
            "quality BLOCKED không được để lượt chạy báo thành công"
        )

    def test_quality_crash_fails_closed_to_exit_3(self, study_dir, monkeypatch):
        def _boom(*a, **k):
            raise RuntimeError("hỏng giả lập lớp chấm")

        monkeypatch.setattr(G3.G3Q, "evaluate_study", _boom)
        rc = _main_with(monkeypatch, study_dir.name, _OK_ARGS)
        assert rc == GC.EXIT_GUARDRAIL_FAIL, (
            "lớp chấm crash phải fail-closed — luật chưa chạy thì không có 'đạt'"
        )


class TestContractPreserved:
    def test_quality_draft_keeps_exit_ok(self, study_dir, monkeypatch):
        """Kết quả ĐÚNG của lượt tự động đầu tiên (DRAFT_NEEDS_HUMAN_PARAMETERS)
        không bị phạt — đây là ranh giới giữ cho bức tường đỏ không thành giả."""
        monkeypatch.setattr(
            G3.G3Q,
            "evaluate_study",
            lambda *a, **k: _fake_quality(G3Q.STATUS_DRAFT_PARAMS),
        )
        rc = _main_with(monkeypatch, study_dir.name, _OK_ARGS)
        assert rc == GC.EXIT_OK

    def test_blocked_run_keeps_exit_2_semantics(self, study_dir, monkeypatch):
        """Lượt vốn DỪNG chờ input (không effect size ⇒ EXIT_BLOCKED=2) giữ
        nguyên mã 2 kể cả khi quality cũng BLOCKED — 2→3 là đổi NGHĨA."""
        monkeypatch.setattr(
            G3.G3Q,
            "evaluate_study",
            lambda *a, **k: _fake_quality(G3Q.STATUS_BLOCKED),
        )
        rc = _main_with(monkeypatch, study_dir.name, [])
        assert rc == GC.EXIT_BLOCKED
