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
T3  (04/10/2026, G5-05) Đã KHOÁ KỸ THUẬT nhưng CHƯA ký → vẫn TỪ CHỐI, dictionary/DMP/checkpoint giữ nguyên byte, G5
    vẫn READY (bản cũ ghi đè cả ba, G5 tụt BLOCKED vĩnh viễn).
T4  Manifest khoá không đọc được → từ chối (không chứng minh được là CHƯA khoá).
T5  Manifest của lần khoá BỊ TỪ CHỐI (status BLOCKED) → không phải khoá, đi tiếp như lần chạy đầu.

04/10/2026: mọi ca chạy trong tmp_path (gọi main() trong tiến trình, BASE trỏ sang thư mục tạm) — bản cũ ghi vào
exports/ thật của repo.
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

import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g5_auto as G5A  # noqa: E402


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-g5-relock-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(root: Path, name: str) -> Path:
    d = root / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sign(study_dir: Path, gate_id: str, artifact_path: Path, reviewer_role: str, root: Path) -> None:
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
    ledger_path.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8", newline="\n")
    GC.write_ledger_seal(study_dir.name, existing, repo_root=root)


def _run_g5(study: str, root: Path, monkeypatch, capsys) -> subprocess.CompletedProcess:
    """Chạy run_g5_auto.main() TRONG tiến trình với BASE = gốc tạm (không đụng exports/ thật của repo)."""
    monkeypatch.setattr(G5A, "BASE", root)
    monkeypatch.setattr(sys, "argv", ["run_g5_auto.py", "--study", study])
    capsys.readouterr()
    rc = G5A.main()
    out = capsys.readouterr()
    return subprocess.CompletedProcess(args=["run_g5_auto.py", study], returncode=rc or 0,
                                       stdout=out.out, stderr=out.err)


def test_g5_da_ky_duyet_tu_choi_chay_lai_khong_dung_toi_checkpoint(tmp_path, monkeypatch, capsys):
    study = "PYTEST-G5-RELOCK-T1"
    d = _study_dir(tmp_path, study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)

        g4_artifact = d / f"G4_A5_SAP_FINAL_{study}.md"
        g4_artifact.write_text("SAP FINAL — nội dung đã khóa (giả lập test)", encoding="utf-8", newline="\n")
        _sign(d, "G4", g4_artifact, "METHODS_STATISTICS_REVIEWER", tmp_path)

        g5_checkpoint = d / "G5_checkpoint.json"
        locked_content = {
            "gate": "G5", "study": study, "g5_status": "LOCKED",
            "data_lock_date": "2026-07-29", "locked_dataset_sha256": "abc123",
            "reviewer_role": "DATA_GOVERNANCE_QA_REVIEWER", "reviewer_ref": "REF-TEST-001",
            "database_lock_status": "LOCKED",
        }
        g5_checkpoint.write_text(
            json.dumps(locked_content, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        before_bytes = g5_checkpoint.read_bytes()
        _sign(d, "G5", g5_checkpoint, "DATA_GOVERNANCE_QA_REVIEWER", tmp_path)

        assert GC.ledger_approved("G5", study, g5_checkpoint, repo_root=tmp_path), (
            "Tiền đề test sai — G5 phải được coi là đã duyệt hợp lệ trước khi chạy lại.")

        result = _run_g5(study, tmp_path, monkeypatch, capsys)

        assert result.returncode != 0, result.stdout + result.stderr
        assert "TỪ CHỐI CHẠY LẠI" in result.stdout, result.stdout
        after_bytes = g5_checkpoint.read_bytes()
        assert after_bytes == before_bytes, (
            "Checkpoint đã ký KHÔNG được đụng tới — nếu test này fail nghĩa là "
            "lỗ hổng ghi-đè-mất-chữ-ký đã hồi quy.")
        assert GC.ledger_approved("G5", study, g5_checkpoint, repo_root=tmp_path), (
            "Chữ ký duyệt G5 phải vẫn còn hiệu lực sau lần chạy lại bị từ chối.")
    finally:
        _rmtree_retry(d)


def test_g5_chua_tung_ky_khong_bi_chan_boi_guard_moi(tmp_path, monkeypatch, capsys):
    """Guard mới CHỈ chặn khi đã có chữ ký hợp lệ — lần chạy đầu (chưa ký) phải
    đi tiếp bình thường tới bước kiểm G4 như cũ, không bị lẫn với guard mới."""
    study = "PYTEST-G5-RELOCK-T2"
    d = _study_dir(tmp_path, study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        # KHÔNG ký G5 — chỉ để chắc guard mới không tự kích hoạt khi chưa có ledger.
        assert not GC.ledger_approved("G5", study, d / "G5_checkpoint.json", repo_root=tmp_path)

        result = _run_g5(study, tmp_path, monkeypatch, capsys)
        assert "TỪ CHỐI CHẠY LẠI" not in result.stdout, result.stdout
        # Không ký G4 nên vẫn DỪNG ở chốt G4 cũ — đúng hành vi ĐÃ CÓ, không phải guard mới.
        assert "G5 DỪNG" in result.stdout, result.stdout
    finally:
        _rmtree_retry(d)


def _bam_tep(d: Path, study: str) -> dict:
    return {ten: (d / ten).read_bytes() for ten in (
        f"G5_REDCap_dictionary_{study}.csv", f"G5_A6_DATA_MGMT_{study}.md", "G5_checkpoint.json",
        "DATA_LOCK_manifest.json") if (d / ten).exists()}


def test_g5_khoa_ky_thuat_chua_ky_van_tu_choi_va_giu_nguyen_byte(tmp_path, monkeypatch, capsys):
    """T3 (G5-05): khoá kỹ thuật xong, CHƯA ký ⇒ từ chối TRƯỚC mọi thao tác ghi; G5 vẫn READY sau lần bị từ chối."""
    from tests.g5_test_helpers import configure_test_signing_key, prepare_locked_g5_study  # noqa: PLC0415

    configure_test_signing_key(tmp_path, monkeypatch)
    study = "PYTEST-G5-RELOCK-T3"
    nguon = tmp_path / "nguon.csv"
    nguon.write_text("record_id,age,sex,exposure_var,primary_outcome\nS001,45,F,0,0\nS002,52,M,1,1\n",
                     encoding="utf-8", newline="\n")
    _, report = prepare_locked_g5_study(study, nguon, exports_root=tmp_path / "exports", repo_root=tmp_path,
                                        approve_g5=False)
    d = tmp_path / "exports" / study
    assert report["status"] == G5Q.STATUS_READY, "Tiền đề: khoá kỹ thuật hợp lệ, chờ ký"
    truoc = _bam_tep(d, study)
    assert len(truoc) == 4

    result = _run_g5(study, tmp_path, monkeypatch, capsys)

    assert result.returncode == GC.EXIT_GUARDRAIL_FAIL, result.stdout
    assert "TỪ CHỐI CHẠY LẠI" in result.stdout and "LOCKED_FOR_ANALYSIS" in result.stdout, result.stdout
    assert _bam_tep(d, study) == truoc, "Dictionary/DMP/checkpoint/manifest phải giữ nguyên byte"
    sau = G5Q.evaluate_study(study, d, repo_root=tmp_path, write=False)
    assert sau["status"] == G5Q.STATUS_READY, [c["id"] for c in sau["automatic_criteria"] if c["status"] != "PASS"]


def test_g5_manifest_khoa_khong_doc_duoc_thi_tu_choi(tmp_path, monkeypatch, capsys):
    """T4: manifest khoá hỏng ⇒ không chứng minh được là CHƯA khoá ⇒ từ chối (fail-closed), không ghi gì."""
    study = "PYTEST-G5-RELOCK-T4"
    d = _study_dir(tmp_path, study)
    (d / "DATA_LOCK_manifest.json").write_text("{khong phai json", encoding="utf-8", newline="\n")
    result = _run_g5(study, tmp_path, monkeypatch, capsys)
    assert result.returncode == GC.EXIT_GUARDRAIL_FAIL, result.stdout
    assert "không đọc được" in result.stdout, result.stdout
    assert sorted(p.name for p in d.iterdir()) == ["DATA_LOCK_manifest.json"]


def test_g5_manifest_lan_khoa_bi_tu_choi_khong_phai_khoa(tmp_path, monkeypatch, capsys):
    """T5: manifest status BLOCKED (lần khoá trước bị từ chối) không phải khoá ⇒ đi tiếp tới chốt G4 như lần đầu."""
    study = "PYTEST-G5-RELOCK-T5"
    d = _study_dir(tmp_path, study)
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps({"status": "BLOCKED"}), encoding="utf-8", newline="\n")
    result = _run_g5(study, tmp_path, monkeypatch, capsys)
    assert "TỪ CHỐI CHẠY LẠI" not in result.stdout, result.stdout
    assert "G5 DỪNG" in result.stdout, result.stdout
