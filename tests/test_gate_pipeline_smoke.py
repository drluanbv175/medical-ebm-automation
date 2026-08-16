"""
Smoke test tích hợp: chạy chuỗi soạn thảo G1→G4 (bỏ G0 vì cần mạng thật), rồi
xác nhận G5 fail-closed vì chưa có phê duyệt thật G2/G4. Test không được tự tạo
phê duyệt IRB/thống kê viên chỉ để đi tiếp tới G9.

Đề tài dùng mã "PYTEST-SMOKE-*" trong exports/ và tự dọn dẹp sau khi chạy.
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


def _read_guardrail_passed(out_dir: Path, gate: str):
    """Đọc checkpoint gate, trả True/False/None — LOGIC Y HỆT run_pipeline.py::_read_guardrail()
    (dùng chung để test này thật sự kiểm tra đúng cái pipeline production tin cậy, không phải
    một tiêu chí riêng dễ hơn). Vá 2026-07-11 (vòng 8): trước đây smoke test chỉ đọc lại
    checkpoint THẬT cho 3/9 cổng (G3/G5/G9) — 6 cổng còn lại (G1/G2/G4/G6/G7/G8) chỉ được kiểm
    qua returncode==0 + substring chung chung trong stdout, nên guardrail LỖI thật (checkpoint
    có 🔴/errors) không hề bị bắt nếu script không sys.exit(khác 0) khi lỗi."""
    p = out_dir / f"{gate}_checkpoint.json"
    if not p.exists():
        return None
    cp = json.loads(p.read_text(encoding="utf-8"))
    g = cp.get("guardrail")
    if isinstance(g, dict):
        if "passed" in g:
            return bool(g.get("passed"))
        st = g.get("status")
        if isinstance(st, str):
            up = st.upper()
            return ("PASS" in up) or ("✅" in st) or ("[OK]" in up)
        return None
    if isinstance(g, str):
        up = g.upper()
        return ("PASS" in up) or ("✅" in g) or ("[OK]" in up)
    return None


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    """rmtree bền hơn trên Windows/OneDrive: xóa có thể "thành công" trong khi
    thư mục chưa thực sự biến mất do khóa file/độ trễ đồng bộ — retry ngắn
    tránh crash mkdir(exist_ok=False) ngay sau (cùng lớp bug đã vá ở
    test_gate_blocked_contract.py 2026-07-05)."""
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


@pytest.fixture
def smoke_study():
    """Tạo G0 checkpoint giả lập, dọn dẹp exports/PYTEST-SMOKE-COHORT/ khi xong."""
    _rmtree_retry(STUDY_DIR)
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    (STUDY_DIR / "G0_checkpoint.json").write_text(
        json.dumps(FIXTURE_G0_CHECKPOINT, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        yield STUDY
    finally:
        _rmtree_retry(STUDY_DIR)


@pytest.mark.slow
def test_draft_chain_stops_before_data_without_human_approvals(smoke_study):
    """
    G1→G4 được phép tạo hồ sơ nháp; G5 phải dừng nếu thiếu phê duyệt thật.
    """
    steps = [
        ("G1", "run_g1_auto.py", None),
        ("G2", "run_g2_auto.py", None),
        ("G3", "run_g3_auto.py", ["--alpha", "0.05", "--power", "0.8", "--effect-size", "0.75",
                                   "--effect-type", "HR", "--p-event", "0.3", "--dropout", "0.15"]),
        ("G4", "run_g4_auto.py", None),
    ]
    for gate, script, extra_args in steps:
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
        # Vá 2026-07-11: KHÔNG chỉ tin returncode/substring trong stdout — chuỗi "✅"/"pass" có
        # thể xuất hiện ở banner in vô điều kiện dù guardrail checkpoint THẬT báo lỗi (vd script
        # không sys.exit khác 0 khi errors không rỗng). Đọc lại checkpoint bằng ĐÚNG logic
        # run_pipeline.py dùng để quyết định pipeline có tiếp tục hay không.
        passed = _read_guardrail_passed(STUDY_DIR, gate)
        assert passed is not False, (
            f"{gate}_checkpoint.json báo guardrail LỖI (passed=False) dù {script} thoát mã 0 và "
            f"in banner PASS — đây chính là kịch bản 'pass giả' cần bắt được:\n{result.stdout[-2000:]}"
        )

    # Xác nhận G3 tính ra cỡ mẫu dương hợp lệ.
    g3 = json.loads((STUDY_DIR / "G3_checkpoint.json").read_text(encoding="utf-8", newline="\n"))
    assert g3.get("n_adjusted", 0) > 0

    # Hồ sơ G2 tự sinh chỉ là hồ sơ nháp, không được tự nhận đã có IRB thật.
    g2 = json.loads((STUDY_DIR / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert g2.get("quality_gate", {}).get("status") != "PASS_G2_APPROVED"
    assert not (STUDY_DIR / "approval_ledger.json").exists()

    # Không có phê duyệt G2/G4 thật thì tuyệt đối không được khóa/thu dữ liệu ở G5.
    g5_result = _run("run_g5_auto.py")
    assert g5_result.returncode == 2
    assert "chưa có phê duyệt THẬT" in g5_result.stdout
    assert not (STUDY_DIR / "G5_checkpoint.json").exists()
