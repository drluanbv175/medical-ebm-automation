"""Regression (2026-07-11, vòng 9): run_g1/g2/g4/g6/g7/g8_auto.py trước đây LUÔN exit code 0
và in banner "HOÀN THÀNH" vô điều kiện dù guardrail() tìm thấy lỗi THẬT — checkpoint ghi đúng
"guardrail": trạng thái lỗi, nhưng process exit code không phản ánh, nên chạy trực tiếp script
(không qua run_pipeline.py, vốn đã tự đọc lại checkpoint phòng thủ) sẽ tưởng nhầm là xong.

Test này chứng minh HÀNH VI THẬT (không chỉ đọc mã nguồn) cho 1 đại diện — G1, chuỗi fixture
đơn giản nhất (chỉ cần G0_checkpoint.json). 5 cổng còn lại (G2/G4/G6/G7/G8) dùng đúng khuôn mẫu
`if <điều kiện lỗi>: raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)` giống hệt — đã soát mã nguồn từng
file + toàn bộ test suite/smoke test G1→G9 vẫn xanh trên đường KHÔNG lỗi (xác nhận sys.exit mới
không phá đường thành công). Không lặp lại fixture chain đầy đủ cho từng cổng (G2 cần G0+G1,
G4 cần G1+G3, G6 cần G4+G5, G7/G8 cần chuỗi dài hơn) vì chi phí không tương xứng lợi ích tăng
thêm so với 1 đại diện đã chứng minh đúng khuôn mẫu.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import run_g1_auto as g1  # noqa: E402

STUDY = "PYTEST-GATEEXIT-G1"
STUDY_DIR = REPO_ROOT / "exports" / STUDY

FIXTURE_G0_CHECKPOINT = {
    "study": STUDY,
    "gate": "G0",
    "gate_status": "DRAFT — CHỜ BÁC SĨ XÁC NHẬN PICO",
    "generated_at": "2026-01-01T00:00:00",
    "topic": "Hiệu quả Metformin trong kiểm soát đường huyết ở bệnh nhân tiền đái tháo đường",
    "base_query": "metformin AND prediabetes",
    "pubmed_results": {
        "total_found": 120, "n_pmids": 30, "n_sr": 4, "n_rct": 8,
        "n_guideline": 2, "n_recent": 10, "most_recent_year": 2025,
    },
    "evidence_level": "Có SR/MA + RCT",
    "research_gaps": [
        "Chưa có nghiên cứu tại Việt Nam về hiệu quả Metformin ở quần thể tiền đái tháo đường"
    ],
    "design_suggestion": "cohort",
    "guardrail": {"passed": True, "n_errors": 0, "errors": []},
    "artifacts": {"A1_markdown": "", "A1_docx": ""},
    "pending_doctor_actions": [],
    "next_gate": "G1",
    "disclaimer": "Cần bác sĩ kiểm chứng.",
}


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


@pytest.fixture
def study_dir():
    _rmtree_retry(STUDY_DIR)
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    (STUDY_DIR / "G0_checkpoint.json").write_text(
        json.dumps(FIXTURE_G0_CHECKPOINT, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        yield STUDY_DIR
    finally:
        _rmtree_retry(STUDY_DIR)


def test_g1_exits_guardrail_fail_code_when_guardrail_fails(study_dir, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_g1_auto.py", "--study", STUDY])
    with patch.object(
        g1, "guardrail_check_g1",
        return_value={"passed": False, "errors": ["R7 🔴 fake lỗi test"], "warnings": []},
    ):
        with pytest.raises(SystemExit) as exc_info:
            g1.main()
    assert exc_info.value.code == GC.EXIT_GUARDRAIL_FAIL


def test_g1_exits_zero_when_guardrail_passes(study_dir, monkeypatch):
    """Đối chứng: xác nhận vá không phá đường THÀNH CÔNG (không SystemExit khi guardrail thật sạch)."""
    monkeypatch.setattr(sys, "argv", ["run_g1_auto.py", "--study", STUDY])
    g1.main()  # không raise gì
    assert (study_dir / "G1_checkpoint.json").exists()
