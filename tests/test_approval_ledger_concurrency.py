"""Hồi quy: lost-update race trong ApprovalLedger.from_file()→mutate→to_file()
(phát hiện qua red-team đối kháng 2026-07-15, xem tools/approve_gate_synthetic_admin.py
docstring + commit vá ApprovalLedger.locked_update()).

Lỗ hổng đã xác nhận TRƯỚC khi vá: 2 tiến trình gọi tools/approve_gate.py (hoặc
approve_gate_synthetic_admin.py) gần như đồng thời trên CÙNG approval_ledger.json
— cả hai load snapshot, mutate độc lập, ghi đè — tiến trình ghi SAU xóa mất bản
ghi tiến trình ghi TRƯỚC, dù cả hai đều báo "✅ đã ghi" thành công. Ảnh hưởng cả
tools/approve_gate.py (đường duyệt cổng THẬT), không chỉ tool synthetic hôm nay.

Test dùng 2 THREAD (không phải 2 tiến trình hệ điều hành) vì khóa
fcntl.flock/msvcrt.locking hoạt động trên OPEN FILE DESCRIPTION/HANDLE — mỗi
thread tự mở file lock riêng bằng locked_update() nên vẫn đối kháng đúng như
2 tiến trình thật; rẻ hơn và xác định hơn spawn subprocess thật cho mục đích
khóa lẫn nhau (không kiểm race ở tầng OS-process, chỉ kiểm đúng cơ chế khóa)."""
from __future__ import annotations

import json
import shutil
import threading
import time
from pathlib import Path

from runtime.approval_ledger import ApprovalLedger
from runtime.schemas import ApprovalDecisionEnum

REPO_ROOT = Path(__file__).resolve().parent.parent


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _approve(ledger_path: Path, gate_id: str, hold_lock_s: float) -> tuple[bool, str]:
    with ApprovalLedger.locked_update(ledger_path) as ledger:
        record = ApprovalLedger.make_human_approval(
            gate_id=gate_id,
            reviewer_role="PI_PROJECT_OWNER",
            reviewer_ref=f"REF-{gate_id}",
            scope=f"test concurrency {gate_id}",
            evidence_content=f"evidence for {gate_id}",
            decision=ApprovalDecisionEnum.APPROVED,
        )
        ok, reason = ledger.add_approval(record, created_by_agent=False)
        # Giữ khóa một lúc SAU khi mutate, TRƯỚC khi to_file() tự động chạy lúc
        # thoát "with" — mở rộng cửa sổ race để thread kia CHẮC CHẮN phải chờ,
        # thay vì tình cờ không đụng nhau (chống test giả-xanh do may mắn timing).
        time.sleep(hold_lock_s)
    return ok, reason


def test_concurrent_approvals_on_same_ledger_do_not_lose_updates(tmp_path):
    """T-RACE-1 — hồi quy chính: 2 thread duyệt 2 cổng KHÁC NHAU gần như đồng
    thời trên CÙNG 1 ledger → cả hai bản ghi phải còn nguyên sau cùng (trước khi
    vá: bản ghi ghi trước bị mất)."""
    study_dir = tmp_path / "CONCURRENCY-TEST-STUDY"
    study_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = study_dir / "approval_ledger.json"

    results: dict[str, tuple[bool, str]] = {}

    def _run(gate_id: str, delay_before_s: float, hold_lock_s: float):
        time.sleep(delay_before_s)
        results[gate_id] = _approve(ledger_path, gate_id, hold_lock_s)

    # Thread G2 bắt đầu trước, giữ khóa 0.3s SAU khi mutate (mô phỏng "đang ghi
    # ra đĩa"); thread G4 cố tình bắt đầu NGAY SAU đó (0.05s) — đúng cửa sổ race
    # thật (2 lệnh gõ gần như liên tiếp) — để chắc chắn thread G4 phải CHỜ khóa
    # thay vì chạy xen kẽ tình cờ không đụng nhau.
    t1 = threading.Thread(target=_run, args=("G2", 0.0, 0.3))
    t2 = threading.Thread(target=_run, args=("G4", 0.05, 0.0))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert results.get("G2") == (True, "ADDED"), f"G2 approval thất bại: {results.get('G2')}"
    assert results.get("G4") == (True, "ADDED"), f"G4 approval thất bại: {results.get('G4')}"

    final = json.loads(ledger_path.read_text(encoding="utf-8"))
    gate_ids = sorted(r["gate_id"] for r in final)
    assert gate_ids == ["G2", "G4"], (
        f"LOST UPDATE: mong đợi cả G2 và G4 còn trong ledger, thực tế: {gate_ids} "
        f"(nếu chỉ còn 1 gate_id, khóa liên-tiến-trình đã KHÔNG hoạt động — hồi quy)"
    )


def test_locked_update_leaves_ledger_unchanged_when_add_approval_rejected(tmp_path):
    """T-RACE-2 — locked_update() vẫn to_file() đúng trạng thái hiện tại khi
    add_approval() bên trong khối with trả về False (không mất bản ghi cũ, không
    ghi rác)."""
    study_dir = tmp_path / "CONCURRENCY-TEST-STUDY-2"
    study_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = study_dir / "approval_ledger.json"

    ok1, _ = _approve(ledger_path, "G9", 0.0)
    assert ok1 is True

    with ApprovalLedger.locked_update(ledger_path) as ledger:
        bad_record = ApprovalLedger.make_human_approval(
            gate_id="G9", reviewer_role="PI_PROJECT_OWNER", reviewer_ref="REF-BAD",
            scope="thiếu evidence_hash", evidence_content="",
            decision=ApprovalDecisionEnum.APPROVED,
        )
        bad_record.evidence_hash = ""  # ép MISSING_EVIDENCE_HASH
        ok2, reason2 = ledger.add_approval(bad_record, created_by_agent=False)
    assert ok2 is False
    assert reason2 == "MISSING_EVIDENCE_HASH"

    final = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert len(final) == 1
    assert final[0]["gate_id"] == "G9"


def test_lock_file_created_alongside_ledger_and_reusable(tmp_path):
    """T-RACE-3 — file khóa (.lock) tạo cạnh ledger, không cản trở lần gọi tiếp
    theo (khóa được nhả đúng cách sau mỗi lần dùng)."""
    study_dir = tmp_path / "CONCURRENCY-TEST-STUDY-3"
    study_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = study_dir / "approval_ledger.json"
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")

    ok1, _ = _approve(ledger_path, "G2", 0.0)
    assert ok1 is True
    assert lock_path.exists()

    # Gọi lại NGAY — nếu khóa lần trước không được nhả đúng cách, lần này sẽ
    # timeout (locked_update mặc định timeout 30s — test dùng timeout ngắn qua
    # gọi trực tiếp _exclusive_file_lock để không chờ 30s nếu thật sự bị kẹt).
    with ApprovalLedger._exclusive_file_lock(lock_path, timeout_s=2.0):
        pass  # lấy khóa thành công = PASS; timeout sẽ raise TimeoutError
