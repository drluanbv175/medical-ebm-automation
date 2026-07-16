"""Hồi quy (vòng audit đối kháng 3, 2026-07-16): gate_contract.ledger_approved() là CHỐT
KIỂM DUY NHẤT dùng bởi run_g6_auto.py/run_g9_auto.py/run_stats_analysis.py/
run_g10_assemble.py để quyết định "cổng gate_id đã được bác sĩ duyệt THẬT chưa". Trên một
máy CHƯA cấu hình khóa ký (chưa chạy setup_gate_approval_key.py — vd máy CI, sandbox agent,
hoặc máy bác sĩ mới), hàm này hạ về kiểm tra CŨ (không xác minh chữ ký) — nghĩa là một bản
ghi approval_ledger.json TỰ BỊA (không chữ ký, reviewer_ref bất kỳ) vẫn qua được miễn tính
đúng evidence_hash (điều KHÔNG cần bí mật gì để làm — sha256 không phải khóa bí mật). Đã tái
hiện bằng script độc lập TRƯỚC khi vá — xác nhận đây là lỗ hổng THẬT, không phải suy diễn.

Vá: với đề tài THẬT trong REAL_STUDY_DENYLIST, "chưa cấu hình khóa ký" giờ = "COI NHƯ CHƯA
DUYỆT" (fail-closed), KHÔNG hạ chuẩn. Hành vi legacy (không chữ ký vẫn qua được) GIỮ NGUYÊN
cho mọi đề tài khác (synthetic/test) để không phá các test/luồng đã có từ trước 2026-07-13.

Dùng repo_root=tmp_path xuyên suốt — KHÔNG bao giờ đụng vào exports/hai-long-benh-nhan-C1a-
BVQY175 thật.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402

REAL_STUDY = "hai-long-benh-nhan-C1a-BVQY175"


def _write_forged_ledger(root: Path, study: str, *, gate_id: str = "G2",
                          reviewer_role: str = "IRB") -> Path:
    study_dir = root / "exports" / study
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / "artifact.md"
    artifact.write_text("noi dung artifact that", encoding="utf-8")
    evidence_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    forged_record = {
        "gate_id": gate_id,
        "decision": "APPROVED",
        "is_synthetic": False,
        "reviewer_role": reviewer_role,
        "evidence_hash": evidence_hash,
        "timestamp_utc": "2026-07-16T00:00:00Z",
        "reviewer_ref": "ke-gia-mao-tu-bia-ban-ghi",
        # KHÔNG có approver_signature — kẻ giả mạo không có khóa ký thật.
    }
    (study_dir / "approval_ledger.json").write_text(
        json.dumps([forged_record]), encoding="utf-8"
    )
    return artifact


def test_forged_ledger_entry_rejected_for_real_study_without_signing_key(tmp_path, monkeypatch):
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khong_ton_tai"))
    assert GC.signing_key_configured() is False

    artifact = _write_forged_ledger(tmp_path, REAL_STUDY)

    assert GC.ledger_approved("G2", REAL_STUDY, artifact, repo_root=tmp_path) is False


def test_forged_ledger_entry_rejected_for_denylisted_alias_too(tmp_path, monkeypatch):
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khong_ton_tai"))

    artifact = _write_forged_ledger(tmp_path, "KKB-HAI-LONG-2026", gate_id="G8",
                                     reviewer_role="INDEPENDENT_PEER_REVIEWER")

    assert GC.ledger_approved("G8", "KKB-HAI-LONG-2026", artifact, repo_root=tmp_path) is False


def test_legacy_no_key_behavior_unchanged_for_non_real_study(tmp_path, monkeypatch):
    """Đối chứng bắt buộc: hành vi CŨ (không chữ ký vẫn qua được khi chưa có khóa) phải GIỮ
    NGUYÊN cho đề tài KHÔNG nằm trong denylist — bản vá chỉ siết đúng đề tài thật, không đổi
    hành vi toàn hệ thống (tránh phá test/luồng synthetic có từ trước 2026-07-13)."""
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khong_ton_tai"))

    artifact = _write_forged_ledger(tmp_path, "mot-de-tai-tong-hop-nao-do")

    assert GC.ledger_approved(
        "G2", "mot-de-tai-tong-hop-nao-do", artifact, repo_root=tmp_path
    ) is True


def test_real_study_still_approved_when_signature_actually_valid(tmp_path, monkeypatch):
    """Đối chứng: fail-closed chỉ áp dụng khi CHƯA có khóa — một khi máy CÓ khóa và bản ghi
    được ký ĐÚNG (qua sign_approval thật), đề tài thật vẫn duyệt được bình thường."""
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-real-study-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    assert GC.signing_key_configured() is True

    study_dir = tmp_path / "exports" / REAL_STUDY
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact = study_dir / "artifact.md"
    artifact.write_text("noi dung artifact that", encoding="utf-8")
    evidence_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    timestamp = "2026-07-16T00:00:00Z"
    signature = GC.sign_approval("G2", REAL_STUDY, evidence_hash, timestamp)
    assert signature is not None

    record = {
        "gate_id": "G2", "decision": "APPROVED", "is_synthetic": False,
        "reviewer_role": "IRB", "evidence_hash": evidence_hash,
        "timestamp_utc": timestamp, "reviewer_ref": "bac-si-that",
        "approver_signature": signature,
    }
    (study_dir / "approval_ledger.json").write_text(json.dumps([record]), encoding="utf-8")

    assert GC.ledger_approved("G2", REAL_STUDY, artifact, repo_root=tmp_path) is True
