"""Khoá hành vi vá 2026-08-24 (audit đa-agent G0-G10, phát hiện NGHIÊM TRỌNG):
``tools/approve_gate.py`` trước đây KHÔNG gọi ``g8_quality_gate.py`` trước khi
ghi ledger G8 — module tồn tại, logic đúng, có test riêng, nhưng hoàn toàn
không được nối dây. Ai giữ khoá vai trò PHAN_BIEN có thể ký "đã bình duyệt độc
lập" mà không cần bản nhận xét thật, không cần cổng A12 đã chạy, và không ai
kiểm tra reviewer_ref có trùng người ký G4 hay không. G2/G4 cũng chỉ chạy đủ
tiêu chí SAU khi đã ghi ledger (thuần advisory).

Test dưới đây kiểm LOGIC NỐI DÂY của approve_gate.py — tách biệt khỏi độ đúng
nội bộ của g2/g4/g8_quality_gate.py (đã có test riêng ở
test_g2_quality_gate.py/test_g4_quality_gate.py/test_g8_quality_gate.py).
Dùng monkeypatch thay vì dựng toàn bộ fixture G0-G7 thật, để test chạy nhanh
và chỉ phụ thuộc vào hợp đồng (status trả về) chứ không phụ thuộc nội dung.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import g2_quality_gate as G2Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402

_STUDY = "PYTEST-WIRING-20260824"


@pytest.fixture()
def study_dir():
    d = REPO_ROOT / "exports" / _STUDY
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _run_main(monkeypatch, *args) -> int:
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", *args])
    return AG.main()


def _fake_report(status: str, criteria=None) -> dict:
    return {"status": status, "automatic_criteria": criteria or [], "approval_criteria": []}


# ════════════════════════════════════════════════════════════════════════════
# G8 — trước 2026-08-24 KHÔNG có chốt nào; nay phải chặn đúng
# ════════════════════════════════════════════════════════════════════════════


def test_approve_gate_import_g8_quality_gate():
    """Bảo vệ chống revert nhầm: approve_gate.py PHẢI import g8_quality_gate.
    Đây chính là dòng còn thiếu duy nhất trước bản vá này."""
    assert hasattr(AG, "G8Q")
    assert AG.G8Q is G8Q


def test_g8_tu_choi_ky_khi_status_blocked(monkeypatch, study_dir):
    artifact = study_dir / G8Q.presubmission_artifact_name(_STUDY)
    artifact.write_text("nội dung tự kiểm G0-G7", encoding="utf-8", newline="\n")
    monkeypatch.setattr(
        G8Q, "evaluate_study",
        lambda *a, **k: _fake_report(G8Q.STATUS_BLOCKED, [
            {"id": "G8-AUTO-99", "label": "giả lập BLOCK", "status": "BLOCK", "evidence": "test"},
        ]),
    )
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G8", "--artifact", str(artifact),
        "--reviewer-role", "PHAN_BIEN", "--reviewer-ref", "REV-01",
    )
    assert rc != 0
    ledger = study_dir / "approval_ledger.json"
    assert not ledger.exists() or json.loads(ledger.read_text(encoding="utf-8")) == []


def test_g8_tu_choi_ky_khi_status_ready_thieu_ban_nhan_xet(monkeypatch, study_dir, capsys):
    """STATUS_READY = READY_FOR_INDEPENDENT_REVIEW nghĩa là CHƯA có bản nhận
    xét phản biện thật (G8_PEER_REVIEW_REPORT). Đây chính là ca lỗ hổng thật:
    trước bản vá, ai giữ khoá vai trò có thể ký G8 ngay ở trạng thái này."""
    artifact = study_dir / G8Q.presubmission_artifact_name(_STUDY)
    artifact.write_text("nội dung tự kiểm G0-G7", encoding="utf-8", newline="\n")
    monkeypatch.setattr(G8Q, "evaluate_study", lambda *a, **k: _fake_report(G8Q.STATUS_READY))
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G8", "--artifact", str(artifact),
        "--reviewer-role", "PHAN_BIEN", "--reviewer-ref", "REV-01",
    )
    assert rc != 0
    assert "bản nhận xét phản biện THẬT" in capsys.readouterr().out
    ledger = study_dir / "approval_ledger.json"
    assert not ledger.exists() or json.loads(ledger.read_text(encoding="utf-8")) == []


def test_g8_cho_phep_ky_khi_status_pending(monkeypatch, study_dir):
    """PENDING_REAL_REVIEW_SIGNATURE là trạng thái TỐI ĐA đạt được TRƯỚC khi
    ký (G8-HUMAN-03/04 tự đọc ledger nên luôn REVIEW khi ledger G8 rỗng) —
    đây phải là ngưỡng CHO PHÉP ký, không phải STATUS_REVIEWED."""
    artifact = study_dir / G8Q.presubmission_artifact_name(_STUDY)
    artifact.write_text("nội dung tự kiểm G0-G7", encoding="utf-8", newline="\n")
    monkeypatch.setattr(G8Q, "evaluate_study", lambda *a, **k: _fake_report(G8Q.STATUS_PENDING))
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G8", "--artifact", str(artifact),
        "--reviewer-role", "PHAN_BIEN", "--reviewer-ref", "REV-01",
    )
    assert rc == 0
    records = json.loads((study_dir / "approval_ledger.json").read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["gate_id"] == "G8"


def test_g8_artifact_phai_dung_ten_chuan(monkeypatch, study_dir):
    """G8 phải ràng buộc đúng G8_A9_PRESUBMISSION_<study>.md — file tự chọn
    không được thay thế bản tự kiểm G0-G7 thật."""
    wrong = study_dir / "tu-khai-g8.md"
    wrong.write_text("Tự khai đã bình duyệt.", encoding="utf-8", newline="\n")
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G8", "--artifact", str(wrong),
        "--reviewer-role", "PHAN_BIEN", "--reviewer-ref", "REV-01",
    )
    assert rc != 0
    ledger = study_dir / "approval_ledger.json"
    assert not ledger.exists()


# ════════════════════════════════════════════════════════════════════════════
# G4 — chốt trước-ký mới (G4Q.evaluate_study), tách khỏi _g4_sections_still_draft
# ════════════════════════════════════════════════════════════════════════════


def test_g4_tu_choi_ky_khi_g4q_bao_blocked(monkeypatch, study_dir):
    """SAP không còn '[CẦN' ở 4 mục bắt buộc (qua được chốt cũ
    _g4_sections_still_draft) NHƯNG G4Q báo BLOCK ở tiêu chí khác (vd EPV/VIF,
    §12 không khớp G3) — trước bản vá 2026-08-24, ca này ký sạch."""
    artifact = study_dir / "G4_A5_SAP_FINAL.md"
    artifact.write_text("# SAP đã khóa\nKhông còn placeholder ở 4 mục chính.",
                        encoding="utf-8", newline="\n")
    monkeypatch.setattr(
        G4Q, "evaluate_study",
        lambda *a, **k: _fake_report(G4Q.STATUS_BLOCKED, [
            {"id": "G4-AUTO-99", "label": "giả lập BLOCK", "status": "BLOCK", "evidence": "test"},
        ]),
    )
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact", str(artifact),
        "--reviewer-role", "PI", "--reviewer-ref", "PI-01",
    )
    assert rc != 0
    ledger = study_dir / "approval_ledger.json"
    assert not ledger.exists() or json.loads(ledger.read_text(encoding="utf-8")) == []


def test_g4_cho_phep_ky_khi_g4q_bao_ready(monkeypatch, study_dir):
    artifact = study_dir / "G4_A5_SAP_FINAL.md"
    artifact.write_text("# SAP đã khóa\nKhông còn placeholder ở 4 mục chính.",
                        encoding="utf-8", newline="\n")
    monkeypatch.setattr(G4Q, "evaluate_study", lambda *a, **k: _fake_report(G4Q.STATUS_READY))
    rc = _run_main(
        monkeypatch, "--study", _STUDY, "--gate", "G4", "--artifact", str(artifact),
        "--reviewer-role", "PI", "--reviewer-ref", "PI-01",
    )
    assert rc == 0
    records = json.loads((study_dir / "approval_ledger.json").read_text(encoding="utf-8"))
    assert len(records) == 1 and records[0]["gate_id"] == "G4"


# ════════════════════════════════════════════════════════════════════════════
# G2 — chốt trước-ký mới (G2Q.evaluate_study), tách khỏi _prepare_g2_attestation
# ════════════════════════════════════════════════════════════════════════════


def _g2_cli_args(study: str, artifact: Path) -> list[str]:
    return [
        "--study", study, "--gate", "G2", "--artifact", str(artifact),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01",
        "--g2-approval-number", "IRB-2026-001",
        "--g2-approval-date", "2026-08-01",
        "--g2-valid-until", "2027-08-01",
        "--g2-protocol-version", "v1.0",
        "--g2-icf-version", "v1.0",
        "--g2-ethics-decision", "APPROVED",
        "--g2-recruitment-mode", "NOT_APPLICABLE",
        "--g2-registration-status", "NOT_REQUIRED",
    ]


def test_g2_tu_choi_ky_khi_g2q_bao_blocked(monkeypatch, study_dir):
    """Attestation IRB đủ metadata (qua được _prepare_g2_attestation cũ)
    NHƯNG G2Q báo BLOCK ở tiêu chí khác (vd WHO TRDS mục 13/14/19/20 thiếu)
    — trước bản vá 2026-08-24, ca này ký sạch vì G2Q chỉ chạy SAU ledger."""
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\nNội dung đầy đủ, không placeholder.",
                        encoding="utf-8", newline="\n")
    monkeypatch.setattr(
        G2Q, "evaluate_study",
        lambda *a, **k: _fake_report(G2Q.STATUS_BLOCKED, [
            {"id": "G2-AUTO-99", "label": "giả lập BLOCK", "status": "BLOCK", "evidence": "test"},
        ]),
    )
    rc = _run_main(monkeypatch, *_g2_cli_args(_STUDY, artifact))
    assert rc != 0
    ledger = study_dir / "approval_ledger.json"
    assert not ledger.exists() or json.loads(ledger.read_text(encoding="utf-8")) == []
