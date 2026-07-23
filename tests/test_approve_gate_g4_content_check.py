"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 15, 2026-07-24, phát hiện HIGH):

Trước vòng vá này, KHÔNG có chỗ nào trong chuỗi khóa G4 thật
(approve_gate.py → ApprovalLedger.add_approval() → gate_contract.
ledger_approved()) kiểm nội dung artifact còn placeholder "[CẦN" hay chưa
trước khi cho ký/coi LOCKED. approve_gate.py chỉ kiểm: file tồn tại, role
đúng nhóm stakeholder, rồi hash+ký — không kiểm nội dung. Một SAP vừa sinh ra
(nguyên placeholder ở §2 kết cục chính/§5 covariates/§10 phần mềm+seed) vẫn
ký được — phá vỡ mục đích chống HARKing/p-hacking của G4.

Test dưới khóa 2 hành vi:
  T1  _g4_sections_still_draft() phát hiện đúng các mục §1/§2/§5/§10 còn
      "[CẦN" trên SAP tươi do run_g4_auto.py::generate() sinh ra, và không
      còn báo mục nào sau khi mục đó được điền.
  T2  CLI approve_gate.py --gate G4 TỪ CHỐI ký (exit != 0) trên SAP tươi,
      KHÔNG ghi approval_ledger.json.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import run_g4_auto as G4  # noqa: E402


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _fresh_sap(design_code="rct"):
    return G4.generate(
        "TEST-STUDY", "Test topic", design_code, "Thiết kế test", "CONSORT",
        500, 0.05, 0.8, 0.2, "RR", "2026-07-24",
    )


def test_fresh_sap_flags_all_four_required_sections():
    artifact = _fresh_sap()
    still_draft = AG._g4_sections_still_draft(artifact)
    labels = " ".join(still_draft)
    assert "§1" in labels
    assert "§2" in labels
    assert "§5" in labels
    assert "§10" in labels


def test_filling_a_section_removes_it_from_still_draft_list():
    artifact = _fresh_sap()
    filled = artifact.replace(
        "- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
        "- **Kết cục chính:** Tỷ lệ nhập viện tim mạch trong 12 tháng  ",
    ).replace(
        "- **Đơn vị / ngưỡng:** [CẦN]  ", "- **Đơn vị / ngưỡng:** %  ",
    ).replace(
        "- **Kết cục phụ 1:** [CẦN]  ", "- **Kết cục phụ 1:** Tử vong toàn bộ  ",
    ).replace(
        "- **Kết cục phụ 2:** [CẦN]  ", "- **Kết cục phụ 2:** Đột quỵ  ",
    ).replace(
        "- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  ",
        "- **Kết cục an toàn:** Xuất huyết nặng  ",
    )
    still_draft = AG._g4_sections_still_draft(filled)
    labels = " ".join(still_draft)
    assert "§2" not in labels, f"§2 đã điền đủ nhưng vẫn bị báo: {still_draft}"
    assert "§1" in labels  # chưa đụng tới §1 → vẫn phải báo


def test_qualitative_design_still_checked_no_crash():
    artifact = _fresh_sap("qualitative")
    still_draft = AG._g4_sections_still_draft(artifact)
    assert isinstance(still_draft, list)


def test_cli_refuses_to_sign_fresh_sap_and_writes_no_ledger(tmp_path, monkeypatch):
    study = "TEST-VONG15-G4-CONTENT-CHECK"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    study_dir.mkdir(parents=True)
    try:
        artifact_path = study_dir / f"G4_A5_SAP_FINAL_{study}.md"
        artifact_path.write_text(_fresh_sap(), encoding="utf-8")
        ledger_path = study_dir / "approval_ledger.json"
        assert not ledger_path.exists()

        result = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "approve_gate.py"),
             "--study", study, "--gate", "G4",
             "--artifact", str(artifact_path),
             "--reviewer-role", "METHODS_STATISTICS_REVIEWER",
             "--reviewer-ref", "TEST-REVIEWER"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        assert result.returncode != 0, result.stdout + result.stderr
        assert "TỪ CHỐI ký G4" in result.stdout
        assert not ledger_path.exists(), "Không được ghi ledger khi SAP còn placeholder"
    finally:
        _rmtree_retry(study_dir)
