"""Hồi quy G9-F6 (audit toàn diện G0-G10, 2026-07-30, MEDIUM):

g8_quality_gate.py (G8-HUMAN-04) đối chiếu reviewer_ref của G8 với TẤT CẢ
cổng khác — kể cả G9 — để phát hiện "cùng một người ký nhiều vai trò". Nhưng
vì G8 thường ký TRƯỚC G9 trong luồng chuẩn, lúc g8_quality_gate.py chạy G9
CHƯA có bản ghi nên phép đối chiếu ở G8 luôn "chưa có gì để so" — thời điểm
DUY NHẤT phép so khớp này có ý nghĩa thật (sau khi CẢ HAI đã ký) là ở phía
G9, nhưng g9_quality_gate.py trước vá này không có đối chiếu ngược lại nào.
Thêm G9-HUMAN-10 tái dùng ledger_records/_latest_approved/_reviewer_ref của
g8_quality_gate.py.

Tiêu chí mới CỐ Ý không gate STATUS_LOCKED (g9_ref chỉ có giá trị SAU KHI G9
đã ký — gate sẽ tạo bẫy con-gà-quả-trứng chặn cả READY_FOR_G9_PI_APPROVAL
trước khi ký)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g9_quality_gate as G9Q  # noqa: E402

from tests.test_g9_quality_gate import _evaluate_ready  # noqa: E402


def _write_ledger(out_dir: Path, records: list[dict]) -> None:
    (out_dir / "approval_ledger.json").write_text(
        json.dumps(records, ensure_ascii=False), encoding="utf-8", newline="\n"
    )


def _row(report, criterion_id):
    for row in report["automatic_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


def _record(gate_id: str, ref: str, ts: str) -> dict:
    return {
        "gate_id": gate_id,
        "decision": "APPROVED",
        "timestamp_utc": ts,
        "reviewer_identity_reference": ref,
    }


def test_no_ledger_yet_is_review_not_blocking(tmp_path, monkeypatch):
    """Chưa có approval_ledger.json nào — tiêu chí REVIEW (thông tin), nhưng
    KHÔNG kéo report xuống dưới STATUS_READY (đã xác nhận bằng _evaluate_ready
    tự assert STATUS_READY)."""
    out_dir, report = _evaluate_ready(tmp_path, monkeypatch, study="PYTEST-G9-REF-T1")
    row = _row(report, "G9-HUMAN-10")
    assert row["status"] == "REVIEW"
    assert report["status"] == G9Q.STATUS_READY


def test_same_reviewer_signs_g8_and_g9_is_flagged(tmp_path, monkeypatch):
    study = "PYTEST-G9-REF-T2"
    out_dir, report = _evaluate_ready(tmp_path, monkeypatch, study=study)
    _write_ledger(out_dir, [
        _record("G8", "DR-A", "2026-07-01T00:00:00+00:00"),
        _record("G9", "DR-A", "2026-07-02T00:00:00+00:00"),
    ])
    report2 = G9Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
    row = _row(report2, "G9-HUMAN-10")
    assert row["status"] == "REVIEW"
    assert "DR-A" in row["evidence"]
    assert "G8" in row["evidence"]


def test_different_reviewers_sign_g8_and_g9_passes(tmp_path, monkeypatch):
    study = "PYTEST-G9-REF-T3"
    out_dir, report = _evaluate_ready(tmp_path, monkeypatch, study=study)
    _write_ledger(out_dir, [
        _record("G8", "DR-REVIEWER", "2026-07-01T00:00:00+00:00"),
        _record("G9", "DR-PI", "2026-07-02T00:00:00+00:00"),
    ])
    report2 = G9Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
    row = _row(report2, "G9-HUMAN-10")
    assert row["status"] == "PASS"


def test_clash_does_not_block_status_ready(tmp_path, monkeypatch):
    """Đúng thiết kế: G9-HUMAN-10 chỉ dấu, không phải phán quyết — không kéo
    report xuống DRAFT dù có trùng người ký."""
    study = "PYTEST-G9-REF-T4"
    out_dir, report = _evaluate_ready(tmp_path, monkeypatch, study=study)
    _write_ledger(out_dir, [
        _record("G8", "DR-A", "2026-07-01T00:00:00+00:00"),
        _record("G9", "DR-A", "2026-07-02T00:00:00+00:00"),
    ])
    report2 = G9Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
    assert report2["status"] == G9Q.STATUS_READY
