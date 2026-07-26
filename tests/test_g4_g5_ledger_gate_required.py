"""Test hồi quy: run_stats_analysis.py PHẢI từ chối chạy khi G4/G5 "LOCKED" chỉ là
văn bản tự do trong checkpoint JSON, KHÔNG kèm phê duyệt thật trong
approval_ledger.json (2026-07-09, kiểm định đối kháng guardrail).

Lỗ hổng đã xác nhận TRƯỚC khi vá: _is_locked() chỉ đọc 1 trường text — bất kỳ ai
(hoặc agent lỗi) tự tay ghi {"g4_status": "LOCKED"} vào G4_checkpoint.json là script
tin ngay và chạy phân tích thật, dù chưa từng có phê duyệt thật nào. Cơ chế
ApprovalLedger cryptographic-binding (BL-06, 2026-07-08) đã tồn tại nhưng CHƯA từng
được nối vào đây trước vòng vá này — 3 test dưới khóa đúng hành vi ĐÃ NỐI:
  T1  checkpoint LOCKED + KHÔNG có approval_ledger.json → vẫn CHẶN (hồi quy chính)
  T2  checkpoint LOCKED + approval_ledger có bản ghi thật khớp hash → CHO CHẠY
  T3  checkpoint LOCKED + approval_ledger có bản ghi nhưng artifact bị sửa SAU
      khi duyệt (hash lệch) → vẫn CHẶN (phát hiện giả mạo)
"""
from __future__ import annotations

import hashlib
import json
import re as _re_module
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

import gate_contract as GC  # noqa: E402


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g4-g5-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    """rmtree bền hơn trên Windows/OneDrive — xem test_gate_blocked_contract.py."""
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_locked_checkpoints(study_dir: Path) -> Path:
    """Ghi G4/G5 checkpoint với trạng thái LOCKED (text tự do) + 1 artifact SAP giả
    làm nội dung để hash — trả về đường dẫn artifact đó."""
    (study_dir / "G2_checkpoint.json").write_text(
        json.dumps({"g2_status": "LOCKED"}, ensure_ascii=False), encoding="utf-8")
    (study_dir / "G4_checkpoint.json").write_text(
        json.dumps({"g4_status": "LOCKED"}, ensure_ascii=False), encoding="utf-8")
    (study_dir / "G5_checkpoint.json").write_text(
        json.dumps({"g5_status": "LOCKED"}, ensure_ascii=False), encoding="utf-8")
    g2_artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{study_dir.name}.md"
    g2_artifact.write_text("ETHICS PACKAGE — nội dung đã duyệt (giả lập test)", encoding="utf-8")
    artifact = study_dir / f"G4_A5_SAP_FINAL_{study_dir.name}.md"
    artifact.write_text("SAP FINAL — nội dung đã khóa (giả lập test)", encoding="utf-8")
    return artifact


def _write_ledger_approval(study_dir: Path, gate_id: str, artifact_content: str) -> None:
    """Ghi 1 approval_ledger.json hợp lệ (không synthetic, không agent-tạo) với
    evidence_hash khớp ĐÚNG artifact_content — mô phỏng tools/approve_gate.py."""
    evidence_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
    timestamp_utc = "2026-07-09T00:00:00+00:00"
    role_by_gate = {
        "G2": "IRB_ETHICS_COMMITTEE",
        "G4": "METHODS_STATISTICS_REVIEWER",
        "G5": "DATA_GOVERNANCE_QA_REVIEWER",
    }
    reviewer_role = role_by_gate.get(gate_id, "PI_PROJECT_OWNER")
    signature = GC.sign_approval(gate_id, study_dir.name, evidence_hash, timestamp_utc,
                                 reviewer_role=reviewer_role, reviewer_ref="REF-TEST-001",
                                 decision="APPROVED")
    record = {
        "approval_id": f"test-{gate_id}-001", "gate_id": gate_id,
        "reviewer_role": reviewer_role,
        "reviewer_identity_reference": "REF-TEST-001",
        "decision": "APPROVED", "scope": "test", "evidence_hash": evidence_hash,
        "timestamp_utc": timestamp_utc, "supersedes": None,
        "artifact_creator_agent": None, "reviewer_agent": None,
        "is_synthetic": False,
        "approver_signature": signature,
    }
    ledger_path = study_dir / "approval_ledger.json"
    existing = []
    if ledger_path.exists():
        existing = json.loads(ledger_path.read_text(encoding="utf-8"))
    existing.append(record)
    ledger_path.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")


def _run_stats(study: str) -> subprocess.CompletedProcess:
    args = [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
            "--data", "khong-ton-tai.csv", "--study", study]
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)


def test_checkpoint_locked_without_ledger_still_blocked():
    """T1 — hồi quy chính: bug đã xác nhận trước khi vá."""
    study = "PYTEST-LEDGER-T1"
    d = _study_dir(study)
    try:
        _write_locked_checkpoints(d)
        # KHÔNG ghi approval_ledger.json — mô phỏng đúng lỗ hổng đã tìm thấy.
        res = _run_stats(study)
        assert "DỪNG" in res.stdout, (
            f"Checkpoint LOCKED (text tự do) KHÔNG kèm approval_ledger.json thật vẫn "
            f"phải bị CHẶN — nếu test này fail nghĩa là lỗ hổng đã hồi quy.\n{res.stdout}")
        assert "approval_ledger" in res.stdout
    finally:
        _rmtree_retry(d)


def test_checkpoint_locked_with_matching_ledger_passes_gate(tmp_path, monkeypatch):
    """T2 — phê duyệt thật khớp hash → KHÔNG bị chặn ở bước cổng (không assert
    chạy phân tích thành công trọn vẹn — chỉ assert đã QUA được cổng G4/G5)."""
    study = "PYTEST-LEDGER-T2"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        artifact = _write_locked_checkpoints(d)
        g2_artifact = d / f"G2_A3_ETHICS_PACKAGE_{study}.md"
        _write_ledger_approval(d, "G2", g2_artifact.read_text(encoding="utf-8"))
        _write_ledger_approval(d, "G4", artifact.read_text(encoding="utf-8"))
        g5_artifact = d / "G5_checkpoint.json"
        _write_ledger_approval(d, "G5", g5_artifact.read_text(encoding="utf-8"))
        res = _run_stats(study)
        assert "DỪNG: G4" not in res.stdout and "DỪNG: G5" not in res.stdout, (
            f"Phê duyệt thật khớp hash phải cho QUA cổng G4/G5 (lỗi khác sau đó, vd "
            f"thiếu file --data, là chấp nhận được — chỉ cổng khóa không được chặn)."
            f"\n{res.stdout}")
    finally:
        _rmtree_retry(d)


def _cli_module():
    """import run_g6_auto — 2 template CLI nhúng (cohort/Cox + case-control) tự sinh
    chuỗi mã nguồn cho bác sĩ chạy tay; kiểm ở mức TEXT sinh ra (không exec subprocess
    — hành vi runtime của cùng logic đã được test đầy đủ ở 3 test trên cho
    run_stats_analysis.py, vốn dùng ĐÚNG cùng 1 mẫu _ledger_approved())."""
    import sys as _sys
    if str(TOOLS_DIR) not in _sys.path:
        _sys.path.insert(0, str(TOOLS_DIR))
    import run_g6_auto
    return run_g6_auto


_V = {"exposure": "arm", "outcome": "outcome", "time_col": "fu", "covariates": ["age"],
      "detection_log": []}


def test_cohort_cox_template_requires_ledger_and_not_or():
    """Template cohort/Cox (_RUN_CLI_TEMPLATE) TRƯỚC vòng vá này THIẾU hẳn
    _ledger_approved — chỉ có checkpoint text. Khóa lại: hàm phải có mặt VÀ phải
    dùng 'and' (bắt buộc cả hai), không phải 'or' (một trong hai đủ)."""
    G6 = _cli_module()
    code = G6.make_run_analysis_cli(_V, 60, "TEST-STUDY", "cohort", "HR")
    assert "_ledger_approved" in code, (
        "Template cohort/Cox vẫn thiếu _ledger_approved — hồi quy về chỉ-kiểm-text.")
    assert ") or _ledger_approved(" not in code, (
        "Template dùng 'or' — checkpoint text một mình vẫn đủ qua cổng, không phải "
        "rào bắt buộc thật.")


def test_case_control_template_requires_ledger_and_not_or():
    """Template case-control (_CASE_CONTROL_CLI_TEMPLATE) TRƯỚC vòng vá này dùng
    'or' — _ledger_approved() chỉ là lối tắt thêm, checkpoint text một mình vẫn đủ.
    Khóa lại: phải là 'and'."""
    G6 = _cli_module()
    code = G6.make_run_analysis_cli(_V, 60, "TEST-STUDY", "case_control", "OR")
    assert "_ledger_approved" in code
    assert ") or _ledger_approved(" not in code, (
        "Template vẫn dùng 'or' cũ — hồi quy về lỗ hổng checkpoint text một mình đủ "
        "để qua cổng, bỏ qua hoàn toàn cơ chế mật mã.")

def _ledger_approved_gate_ids(code: str) -> set[str]:
    """Trích các gate_id được truyền vào _ledger_approved(...)/_GC.ledger_approved(...)
    trong code sinh ra — bất kể xuống dòng/thụt lề cụ thể thế nào (tránh test giòn
    theo whitespace). Vá 2026-07-12: 4 template giờ gọi qua gate_contract.ledger_approved()
    dùng chung thay vì hàm cục bộ — regex nới để bắt cả 2 dạng gọi."""
    return set(_re_module.findall(
        r'(?:_ledger_approved|_GC\.ledger_approved)\(\s*"([A-Z0-9]+)"', code))


def test_cohort_cox_template_g2_also_requires_ledger():
    """T6 — vá 2026-07-09 (rà lại G2/G9 sau vòng G4/G5): G2 dùng CHUNG hàm
    _check_sap_db_locked với G4/G5 trong CÙNG template này, nhưng bị bỏ sót ở vòng
    vá trước — chỉ G4/G5 được nối _ledger_approved, G2 vẫn chỉ kiểm text tự do.
    Khóa lại: G2 giờ cũng phải gọi _ledger_approved("G2", ...)."""
    G6 = _cli_module()
    code = G6.make_run_analysis_cli(_V, 60, "TEST-STUDY", "cohort", "HR")
    gate_ids = _ledger_approved_gate_ids(code)
    assert "G2" in gate_ids, (
        f"Template cohort/Cox: G2 vẫn thiếu _ledger_approved (chỉ thấy {gate_ids}) — "
        f"hồi quy về khoảng trống đã tìm thấy trong vòng rà G2/G9.")
    assert {"G2", "G4", "G5"} <= gate_ids


def test_case_control_template_g2_also_requires_ledger():
    """T7 — cùng phát hiện T6, áp cho template case-control."""
    G6 = _cli_module()
    code = G6.make_run_analysis_cli(_V, 60, "TEST-STUDY", "case_control", "OR")
    gate_ids = _ledger_approved_gate_ids(code)
    assert "G2" in gate_ids, (
        f"Template case-control: G2 vẫn thiếu _ledger_approved (chỉ thấy {gate_ids}).")
    assert {"G2", "G4", "G5"} <= gate_ids


def test_cohort_sensitivity_template_requires_ledger_gate():
    """Audit 2026-07-11: make_sensitivity_analysis() (cohort/Cox — chạy hồi quy
    Cox THẬT trên CSV thật, giống hệt make_run_analysis_cli) TRƯỚC vòng vá này
    KHÔNG có cổng nào — không _check_sap_db_locked, không _ledger_approved. Khóa
    lại: phải có đủ G2+G4+G5 qua _ledger_approved, giống template CLI chính."""
    G6 = _cli_module()
    code = G6.make_sensitivity_analysis(_V, "TEST-STUDY", "cohort")
    assert "_check_sap_db_locked" in code, (
        "Template sensitivity cohort/Cox vẫn thiếu cổng G2/G4/G5 — chạy hồi quy "
        "thật trên dữ liệu thật mà không kiểm gì.")
    gate_ids = _ledger_approved_gate_ids(code)
    assert {"G2", "G4", "G5"} <= gate_ids, (
        f"Template sensitivity cohort/Cox thiếu gate trong _ledger_approved (chỉ thấy {gate_ids}).")


def test_case_control_sensitivity_template_requires_ledger_gate():
    """Cùng phát hiện trên, áp cho template sensitivity case-control (logistic/OR)."""
    G6 = _cli_module()
    code = G6.make_sensitivity_analysis(_V, "TEST-STUDY", "case_control")
    assert "_check_sap_db_locked" in code
    gate_ids = _ledger_approved_gate_ids(code)
    assert {"G2", "G4", "G5"} <= gate_ids, (
        f"Template sensitivity case-control thiếu gate trong _ledger_approved (chỉ thấy {gate_ids}).")


def test_tampered_artifact_after_approval_still_blocked(tmp_path, monkeypatch):
    """T3 — artifact bị sửa SAU khi duyệt (hash lệch) → vẫn phải CHẶN, chứng minh
    ràng buộc mật mã hoạt động thật, không chỉ kiểm 'có bản ghi nào đó'."""
    study = "PYTEST-LEDGER-T3"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        artifact = _write_locked_checkpoints(d)
        # Duyệt với nội dung GỐC...
        g2_artifact = d / f"G2_A3_ETHICS_PACKAGE_{study}.md"
        _write_ledger_approval(d, "G2", g2_artifact.read_text(encoding="utf-8"))
        _write_ledger_approval(d, "G4", artifact.read_text(encoding="utf-8"))
        g5_artifact = d / "G5_checkpoint.json"
        _write_ledger_approval(d, "G5", g5_artifact.read_text(encoding="utf-8"))
        # ...rồi SỬA artifact SAU khi đã "duyệt" — mô phỏng giả mạo/chỉnh sửa hậu duyệt.
        artifact.write_text("SAP FINAL — NỘI DUNG ĐÃ BỊ SỬA SAU KHI DUYỆT", encoding="utf-8")
        res = _run_stats(study)
        assert "DỪNG" in res.stdout, (
            f"Artifact bị sửa sau khi duyệt (hash lệch) phải bị CHẶN — nếu lọt qua "
            f"nghĩa là ràng buộc mật mã không hoạt động thật.\n{res.stdout}")
    finally:
        _rmtree_retry(d)
