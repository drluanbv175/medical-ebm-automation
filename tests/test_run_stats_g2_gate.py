"""
Test cổng G2 (đạo đức/IRB) của run_stats_analysis.py — vá 2026-07-10.

Bối cảnh: run_stats_analysis.py là script DUY NHẤT chạy phân tích thống kê trên DỮ LIỆU
BỆNH NHÂN THẬT (CSV/Excel do bác sĩ cấp). Trước vá này nó chỉ chặn theo G4 (SAP)/G5 (khóa DB)
mà KHÔNG kiểm G2 (phê duyệt Hội đồng Đạo đức) — trong khi sibling run_g6_auto.py (chỉ sinh
template, không đụng dữ liệu thật) lại CÓ cổng G2. Nghĩa là có thể chạy phân tích thật trên
dữ liệu thật mà không có cổng kỹ thuật nào xác nhận đã được phê duyệt đạo đức. Test này khóa
lại hành vi: G2 chưa duyệt → script TỪ CHỐI chạy, độc lập với G4/G5.
"""

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TOOLS_DIR = _REPO_ROOT / "tools"
_SCRIPT = _REPO_ROOT / "tools" / "run_stats_analysis.py"

sys.path.insert(0, str(_TOOLS_DIR))
sys.path.insert(0, str(_REPO_ROOT))
import gate_contract as GC  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402


def _run(*extra, study="__g2gate_pytest__"):
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--study", study,
         "--data", "/khong_ton_tai_9z9z.csv", *extra],
        cwd=str(_REPO_ROOT), capture_output=True, text=True,
    )


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g2-gate-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _write_real_approval(study: str, gate_id: str, artifact_rel: str, content: str) -> None:
    """Tạo phê duyệt THẬT trong exports/<study>/approval_ledger.json — giống hệt những
    gì tools/approve_gate.py làm (không đi qua subprocess để test nhanh/gọn hơn)."""
    study_dir = _REPO_ROOT / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / artifact_rel
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(content, encoding="utf-8")
    ledger_path = study_dir / "approval_ledger.json"
    ledger = ApprovalLedger.from_file(ledger_path)
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    evidence_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    role_by_gate = {
        "G2": "IRB_ETHICS_COMMITTEE",
        "G4": "METHODS_STATISTICS_REVIEWER",
        "G9": "PI_PROJECT_OWNER",
    }
    reviewer_role = role_by_gate.get(gate_id, "PI_PROJECT_OWNER")
    signature = GC.sign_approval(gate_id, study, evidence_hash, timestamp_utc,
                                 reviewer_role=reviewer_role, reviewer_ref=f"TEST-{gate_id}")
    assert signature
    record = ApprovalLedger.make_human_approval(
        gate_id=gate_id,
        reviewer_role=reviewer_role,
        reviewer_ref=f"TEST-{gate_id}",
        scope="test", evidence_content=content,
        approver_signature=signature,
        timestamp_utc=timestamp_utc,
    )
    ok, reason = ledger.add_approval(record)
    assert ok, reason
    ledger.to_file(ledger_path)


class TestRunStatsG2Gate:
    def test_blocks_when_g2_not_approved_even_if_sap_bypassed(self):
        # Bỏ qua G4/G5 bằng --i-confirm-sap-locked, NHƯNG G2 chưa duyệt và KHÔNG có cờ IRB
        # → phải DỪNG ở cổng G2 (exit != 0) với đúng thông báo, TRƯỚC khi đụng dữ liệu.
        res = _run("--i-confirm-sap-locked")
        assert res.returncode != 0
        assert "G2" in res.stdout
        assert "đạo đức" in res.stdout or "IRB" in res.stdout

    def test_bare_irb_confirm_flag_alone_no_longer_bypasses_ledger(self):
        """Vá 2026-07-12 (audit toàn diện, kiểm định đối kháng xác nhận bypass THẬT):
        --i-confirm-irb-approved trước đây bỏ qua TOÀN BỘ kiểm tra kể cả ledger — cờ
        tự khai trần, không kèm phê duyệt thật, đủ để "qua cổng". Khóa lại: cờ KHÔNG
        còn đủ một mình; ledger_approved() (phê duyệt thật) LUÔN bắt buộc."""
        res = _run("--i-confirm-sap-locked", "--i-confirm-irb-approved")
        assert res.returncode != 0
        assert "DỪNG: G2" in res.stdout
        assert "KHÔNG thay được ledger" in res.stdout

    def test_passes_g2_gate_with_real_ledger_approval(self, tmp_path, monkeypatch):
        """Phê duyệt G2 THẬT (ledger) + cờ IRB thay checkpoint-file bị mất → phải VƯỢT
        cổng G2, rồi mới thất bại ở bước khác (dữ liệu không tồn tại), không phải bị
        chặn ở G2."""
        study = "__g2gate_pytest_real_approval__"
        study_dir = _REPO_ROOT / "exports" / study
        shutil.rmtree(study_dir, ignore_errors=True)
        try:
            _configure_test_signing_key(tmp_path, monkeypatch)
            _write_real_approval(
                study, "G2", f"G2_A3_ETHICS_PACKAGE_{study}.md", "Ethics package test content")
            res = _run("--i-confirm-sap-locked", "--i-confirm-irb-approved", study=study)
            combined = res.stdout + res.stderr
            assert "DỪNG: G2" not in combined  # không còn bị chặn ở cổng G2
        finally:
            shutil.rmtree(study_dir, ignore_errors=True)

    def test_g2_gate_is_independent_of_sap_gate(self):
        # Không cờ nào → phải dừng ở cổng ĐẦU TIÊN gặp phải (G2, vì G2 đứng trước G4/G5).
        res = _run()
        assert res.returncode != 0
        assert "G2" in res.stdout
