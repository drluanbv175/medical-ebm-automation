"""Hồi quy #27 (2026-09-26): approve_gate phải đọc LẠI đuôi sổ cái DƯỚI KHOÁ.

Lỗi gốc (đã tái lập bằng 2 tiến trình thật): prev_hash được tính NGOÀI khoá, rồi
mới vào locked_update. Nếu một tiến trình khác ghi xen vào giữa hai bước, cả hai
đều báo ADDED nhưng bản ghi sau trỏ tới đuôi CŨ ⇒ ĐỨT CHUỖI vĩnh viễn (mọi cổng
của đề tài bị khoá). Chú thích cũ khẳng định ngược lại.

Test tái hiện đúng khe hở đó một cách XÁC ĐỊNH: chèn một lượt ghi của «tiến trình
khác» vào ngay sau khi approve_gate đã ký (tức đã chốt prev_hash ngoài khoá) và
trước khi nó lấy khoá. Kỳ vọng: approve_gate từ chối (mã 1), không ghi gì, chuỗi và
con dấu vẫn nguyên vẹn. Mọi thứ trong tmp_path — không đụng exports/ thật.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import approve_gate as AG  # noqa: E402
import gate_contract as GC  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402
from runtime.schemas import ApprovalDecisionEnum  # noqa: E402

_STUDY = "PYTEST-DUOI-SO-DUOI-KHOA-20260926"


@pytest.fixture()
def cay(tmp_path, monkeypatch):
    key = tmp_path / "keys" / "gate_approval_key"
    key.parent.mkdir(parents=True)
    key.write_text("pytest-duoi-khoa-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
    fake_tools = tmp_path / "tools"
    fake_tools.mkdir()
    # approve_gate + gate_contract dựng exports/<study> và con dấu từ __file__ ⇒ trỏ
    # vào tmp_path để không bao giờ chạm exports/ thật của repo.
    monkeypatch.setattr(AG, "__file__", str(fake_tools / "approve_gate.py"))
    monkeypatch.setattr(GC, "__file__", str(fake_tools / "gate_contract.py"))
    d = tmp_path / "exports" / _STUDY
    d.mkdir(parents=True)
    artifact = d / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\nnội dung\n", encoding="utf-8", newline="\n")
    return tmp_path, d, artifact


def _ghi_cua_tien_trinh_khac(ledger_path: Path, ts: str, sign) -> None:
    """Một lượt ký ĐÚNG quy trình của tiến trình khác (prev_hash tính dưới khoá)."""
    content = "noi dung cua tien trinh khac"
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    with ApprovalLedger.locked_update(ledger_path) as ledger:
        prev = GC.chain_prev_hash(ledger.export_tail())
        sig = sign(
            "G2", _STUDY, h, ts, reviewer_role="IRB", reviewer_ref="IRB-khac",
            decision="REJECTED", is_synthetic=False, prev_hash=prev)
        rec = ApprovalLedger.make_human_approval(
            gate_id="G2", reviewer_role="IRB", reviewer_ref="IRB-khac", scope="khac",
            evidence_content=content, decision=ApprovalDecisionEnum.REJECTED,
            approver_signature=sig, timestamp_utc=ts, prev_hash=prev)
        ok, reason = ledger.add_approval(rec, created_by_agent=False)
        assert ok, reason


def _chay(monkeypatch, artifact: Path, ref: str) -> int:
    monkeypatch.setattr(sys, "argv", [
        "approve_gate.py", "--study", _STUDY, "--gate", "G2", "--artifact", str(artifact),
        "--reviewer-role", "IRB", "--reviewer-ref", ref, "--decision", "REJECTED",
    ])
    return AG.main()


def test_ghi_xen_giua_ky_va_lay_khoa_bi_tu_choi_chuoi_nguyen(cay, monkeypatch, capsys):
    root, d, artifact = cay
    ledger_path = d / "approval_ledger.json"
    # Sổ có sẵn 1 bản ghi hợp lệ (ký qua chính approve_gate).
    assert _chay(monkeypatch, artifact, "IRB-01") == 0
    capsys.readouterr()

    sign_goc = GC.sign_approval
    da_chen = {"v": False}

    def _sign_co_chen(gate_id, study, *a, **k):
        sig = sign_goc(gate_id, study, *a, **k)
        if gate_id == "G2" and not da_chen["v"]:
            da_chen["v"] = True   # đặt TRƯỚC để lượt ghi chèn (cũng ký) không đệ quy
            _ghi_cua_tien_trinh_khac(ledger_path, "2026-09-26T09:00:00+00:00", sign_goc)
        return sig

    monkeypatch.setattr(GC, "sign_approval", _sign_co_chen)
    truoc = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert len(truoc) == 1

    rc = _chay(monkeypatch, artifact, "IRB-02")
    out = capsys.readouterr().out
    assert da_chen["v"], "phép chèn không chạy — test không kiểm gì"

    sau = json.loads(ledger_path.read_text(encoding="utf-8"))
    ok, ly_do = GC.verify_ledger_chain(sau)
    assert ok, f"ĐỨT CHUỖI sau lượt ký chồng: {ly_do}"
    assert rc == 1, out
    assert "tiến trình khác cập nhật" in out, out
    assert len(sau) == 2, "lượt bị từ chối không được ghi gì"
    ok, ly_do = GC.verify_ledger_seal(_STUDY, sau, repo_root=root)
    assert ok, ly_do

    # Chạy lại chính xác lệnh ⇒ ký theo đuôi mới, chuỗi vẫn đúng.
    monkeypatch.setattr(GC, "sign_approval", sign_goc)
    assert _chay(monkeypatch, artifact, "IRB-02") == 0
    lai = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert len(lai) == 3
    ok, ly_do = GC.verify_ledger_chain(lai)
    assert ok, ly_do


def test_khong_co_ghi_xen_van_ky_binh_thuong(cay, monkeypatch):
    """Đối chứng: không có tiến trình khác ⇒ hai lượt ký liên tiếp đều qua, chuỗi đúng."""
    _root, d, artifact = cay
    assert _chay(monkeypatch, artifact, "IRB-01") == 0
    assert _chay(monkeypatch, artifact, "IRB-02") == 0
    recs = json.loads((d / "approval_ledger.json").read_text(encoding="utf-8"))
    assert len(recs) == 2
    assert GC.verify_ledger_chain(recs)[0]
