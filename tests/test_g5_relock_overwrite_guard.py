"""Hồi quy (audit toàn diện G0-G10, 2026-07-29, G5-F1 — CRITICAL):

Trước vá này, `run_g5_auto.py::main()` LUÔN ghi đè G5_checkpoint.json bằng một
dict mới hoàn toàn (`g5_status="PENDING"`), không đọc/merge checkpoint cũ. Nếu
G5 đã được khóa (`lock_analysis_dataset.py`) và ký duyệt thật
(`approve_gate.py --gate G5`), chạy lại CHÍNH `run_g5_auto.py` sẽ xóa mất
`locked_dataset_sha256`/`reviewer_role`/`data_lock_date` — evidence_hash trong
`approval_ledger.json` không còn khớp checkpoint hiện tại, chữ ký duyệt G5 mất
hiệu lực NGAY LẬP TỨC dù dữ liệu/khoa học không đổi, kéo theo G6/
run_stats_analysis.py (đều gọi `ledger_approved("G5", ...)`) bị chặn theo.
Chạy lại `lock_analysis_dataset.py` để "sửa" KHÔNG cứu được: manifest cũ vẫn
khớp hash nên đường idempotent trả về SỚM, không ghi lại checkpoint — G5 kẹt ở
PENDING vĩnh viễn.

T1  G5 đã ký duyệt hợp lệ → run_g5_auto.py TỪ CHỐI chạy lại, KHÔNG đụng tới
    checkpoint (byte-identical trước/sau), exit code khác 0.
T2  G5 CHƯA từng ký (lần chạy đầu) → không bị chặn bởi guard mới này.
"""

from __future__ import annotations

import hashlib
import json
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
    key_path.write_text("pytest-g5-relock-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
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


def _sign(study_dir: Path, gate_id: str, artifact_path: Path, reviewer_role: str) -> None:
    """Mô phỏng approve_gate.py: ký + ghi 1 bản ghi hợp lệ vào approval_ledger.json."""
    content = artifact_path.read_text(encoding="utf-8")
    evidence_hash = hashlib.sha256(content.encode()).hexdigest()
    timestamp_utc = "2026-07-30T00:00:00+00:00"
    ledger_path = study_dir / "approval_ledger.json"
    existing = []
    if ledger_path.exists():
        existing = json.loads(ledger_path.read_text(encoding="utf-8"))
    prev = existing[-1] if existing else None
    prev_hash = GC.chain_prev_hash(prev)
    signature = GC.sign_approval(
        gate_id, study_dir.name, evidence_hash, timestamp_utc,
        reviewer_role=reviewer_role, reviewer_ref="REF-TEST-001",
        decision="APPROVED", is_synthetic=False, prev_hash=prev_hash,
    )
    record = {
        "approval_id": f"test-{gate_id}-001", "gate_id": gate_id,
        "reviewer_role": reviewer_role, "reviewer_identity_reference": "REF-TEST-001",
        "decision": "APPROVED", "scope": "test", "evidence_hash": evidence_hash,
        "timestamp_utc": timestamp_utc, "supersedes": None, "prev_hash": prev_hash,
        "artifact_creator_agent": None, "reviewer_agent": None, "is_synthetic": False,
        "approver_signature": signature,
    }
    existing.append(record)
    ledger_path.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
    GC.write_ledger_seal(study_dir.name, existing, repo_root=REPO_ROOT)


def _run_g5(study: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(TOOLS_DIR / "run_g5_auto.py"), "--study", study],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )


def test_g5_da_ky_duyet_tu_choi_chay_lai_khong_dung_toi_checkpoint(tmp_path, monkeypatch):
    study = "PYTEST-G5-RELOCK-T1"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)

        g4_artifact = d / f"G4_A5_SAP_FINAL_{study}.md"
        g4_artifact.write_text("SAP FINAL — nội dung đã khóa (giả lập test)", encoding="utf-8")
        _sign(d, "G4", g4_artifact, "METHODS_STATISTICS_REVIEWER")

        g5_checkpoint = d / "G5_checkpoint.json"
        locked_content = {
            "gate": "G5", "study": study, "g5_status": "LOCKED",
            "data_lock_date": "2026-07-29", "locked_dataset_sha256": "abc123",
            "reviewer_role": "DATA_GOVERNANCE_QA_REVIEWER", "reviewer_ref": "REF-TEST-001",
            "database_lock_status": "LOCKED",
        }
        g5_checkpoint.write_text(
            json.dumps(locked_content, ensure_ascii=False, indent=2), encoding="utf-8")
        before_bytes = g5_checkpoint.read_bytes()
        _sign(d, "G5", g5_checkpoint, "DATA_GOVERNANCE_QA_REVIEWER")

        assert GC.ledger_approved("G5", study, g5_checkpoint, repo_root=REPO_ROOT), (
            "Tiền đề test sai — G5 phải được coi là đã duyệt hợp lệ trước khi chạy lại.")

        result = _run_g5(study)

        assert result.returncode != 0, result.stdout + result.stderr
        assert "TỪ CHỐI CHẠY LẠI" in result.stdout, result.stdout
        after_bytes = g5_checkpoint.read_bytes()
        assert after_bytes == before_bytes, (
            "Checkpoint đã ký KHÔNG được đụng tới — nếu test này fail nghĩa là "
            "lỗ hổng ghi-đè-mất-chữ-ký đã hồi quy.")
        assert GC.ledger_approved("G5", study, g5_checkpoint, repo_root=REPO_ROOT), (
            "Chữ ký duyệt G5 phải vẫn còn hiệu lực sau lần chạy lại bị từ chối.")
    finally:
        _rmtree_retry(d)


def test_g5_chua_tung_ky_khong_bi_chan_boi_guard_moi(tmp_path, monkeypatch):
    """Guard mới CHỈ chặn khi đã có chữ ký hợp lệ — lần chạy đầu (chưa ký) phải
    đi tiếp bình thường tới bước kiểm G4 như cũ, không bị lẫn với guard mới."""
    study = "PYTEST-G5-RELOCK-T2"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        # KHÔNG ký G5 — chỉ để chắc guard mới không tự kích hoạt khi chưa có ledger.
        assert not GC.ledger_approved("G5", study, d / "G5_checkpoint.json", repo_root=REPO_ROOT)

        result = _run_g5(study)
        assert "TỪ CHỐI CHẠY LẠI" not in result.stdout, result.stdout
        # Không ký G4 nên vẫn DỪNG ở chốt G4 cũ — đúng hành vi ĐÃ CÓ, không phải guard mới.
        assert "G5 DỪNG" in result.stdout, result.stdout
    finally:
        _rmtree_retry(d)
