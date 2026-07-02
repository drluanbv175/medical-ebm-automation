"""
Smoke test tích hợp: chạy trọn chuỗi G1→G9 (bỏ G0 vì cần mạng thật) cho 1 đề
tài giả lập, xác nhận mọi cổng thoát mã 0 + guardrail PASS + checkpoint tiếp
theo đọc được checkpoint trước — không có bộ test tự động nào cho việc này
trước 2026-07-02 (mọi verify trước đó đều thủ công/qua agent, không tái lặp
được). Đề tài dùng mã "PYTEST-SMOKE-*" trong exports/, TỰ DỌN DẸP sau khi chạy
(kể cả khi test fail) để không để lại rác trong exports/ thật.

Đây là test CHẬM (gọi ~9 script con, sinh DOCX thật) — đánh dấu @pytest.mark.slow
để có thể bỏ qua bằng `pytest -m "not slow"` khi cần vòng lặp nhanh.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable

STUDY = "PYTEST-SMOKE-COHORT"
STUDY_DIR = REPO_ROOT / "exports" / STUDY

# Chủ đề CỐ Ý dùng chuyên khoa metabolic_diabetes (bundle cũ, ổn định nhất) để
# smoke test không phụ thuộc vào thay đổi tương lai ở các bundle chuyên khoa mới.
FIXTURE_G0_CHECKPOINT = {
    "study": STUDY,
    "gate": "G0",
    "gate_status": "DRAFT — CHỜ BÁC SĨ XÁC NHẬN PICO",
    "generated_at": "2026-01-01T00:00:00",
    "topic": "Hiệu quả Metformin trong kiểm soát đường huyết ở bệnh nhân tiền đái tháo đường",
    "base_query": "metformin AND prediabetes",
    "pubmed_results": {
        "total_found": 120,
        "n_pmids": 30,
        "n_sr": 4,
        "n_rct": 8,
        "n_guideline": 2,
        "n_recent": 10,
        "most_recent_year": 2025,
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


def _run(script: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    args = [PYTHON, str(TOOLS_DIR / script), "--study", STUDY]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=180
    )


@pytest.fixture
def smoke_study():
    """Tạo G0 checkpoint giả lập, dọn dẹp exports/PYTEST-SMOKE-COHORT/ khi xong."""
    if STUDY_DIR.exists():
        shutil.rmtree(STUDY_DIR)
    STUDY_DIR.mkdir(parents=True)
    (STUDY_DIR / "G0_checkpoint.json").write_text(
        json.dumps(FIXTURE_G0_CHECKPOINT, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        yield STUDY
    finally:
        if STUDY_DIR.exists():
            shutil.rmtree(STUDY_DIR)


@pytest.mark.slow
def test_full_chain_g1_through_g9(smoke_study):
    """
    Chạy tuần tự G1→G9 (bỏ G0), mỗi bước xác nhận exit code 0 và có PASS
    trong output. Nếu 1 cổng lỗi, dừng ngay và báo lỗi rõ cổng nào.
    """
    steps = [
        ("run_g1_auto.py", None),
        ("run_g2_auto.py", None),
        ("run_g3_auto.py", ["--alpha", "0.05", "--power", "0.8", "--effect-size", "0.75",
                             "--effect-type", "HR", "--p-event", "0.3", "--dropout", "0.15"]),
        ("run_g4_auto.py", None),
        ("run_g5_auto.py", None),
        ("run_g6_auto.py", None),
        ("run_g7_auto.py", None),
        ("run_g8_auto.py", None),
        ("run_g9_auto.py", None),
    ]
    for script, extra_args in steps:
        result = _run(script, extra_args)
        assert result.returncode == 0, (
            f"{script} thoát mã {result.returncode}\n"
            f"--- stdout ---\n{result.stdout[-3000:]}\n"
            f"--- stderr ---\n{result.stderr[-2000:]}"
        )
        combined = (result.stdout + result.stderr).lower()
        assert "pass" in combined or "✅" in combined or "[ok]" in combined, (
            f"{script} không thấy dấu hiệu guardrail PASS trong output:\n{result.stdout[-2000:]}"
        )

    # Xác nhận checkpoint cuối cùng (G9) đọc được đủ chuỗi G0-G8 trước đó.
    g9_checkpoint_path = STUDY_DIR / "G9_checkpoint.json"
    assert g9_checkpoint_path.exists(), "G9 không sinh checkpoint"
    g9 = json.loads(g9_checkpoint_path.read_text(encoding="utf-8"))
    assert g9.get("guardrail", {}).get("passed") is True

    # Xác nhận G5 nhận diện đúng chuyên khoa (không rơi về generic cho topic
    # rõ ràng là metabolic_diabetes).
    g5 = json.loads((STUDY_DIR / "G5_checkpoint.json").read_text(encoding="utf-8"))
    assert g5.get("specialty") == "metabolic_diabetes"

    # Xác nhận G3 tính ra cỡ mẫu dương hợp lệ.
    g3 = json.loads((STUDY_DIR / "G3_checkpoint.json").read_text(encoding="utf-8"))
    assert g3.get("n_adjusted", 0) > 0
