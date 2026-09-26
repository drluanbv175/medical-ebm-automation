"""Hồi quy #26 (2026-09-26): export_json phải ghi trả NGUYÊN VĂN, ĐÚNG THỨ TỰ mọi
phần tử đã nạp, rồi mới nối bản ghi mới vào ĐUÔI.

Lỗi gốc: dòng không parse được (vd thiếu `scope` — trường KHÔNG nằm trong nội dung
ký) bị dời xuống CUỐI sổ khi ghi. Lượt approve_gate kế tiếp lấy prev_hash từ đuôi
file thô, nên sau khi ghi thì bản ghi mới không đứng ở đuôi nữa ⇒ ĐỨT CHUỖI băm ⇒
mọi cổng của đề tài bị khoá vĩnh viễn («ĐỨT CHUỖI»), ký lại không cứu được.

Mỗi ca mô phỏng ĐÚNG approve_gate: prev_hash lấy từ đuôi file thô, ký, rồi ghi qua
locked_update. Mọi thứ trong tmp_path (repo_root=tmp_path) — không đụng exports/ thật.
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

import gate_contract as GC  # noqa: E402

from runtime.approval_ledger import ApprovalLedger  # noqa: E402
from runtime.schemas import ApprovalDecisionEnum  # noqa: E402

_NOI_DUNG = "noi dung artifact"
_ROLE = {"G2": "IRB", "G8": "PHAN_BIEN_DOC_LAP", "G9": "PI", "G10": "PI"}


@pytest.fixture()
def moi_truong(tmp_path, monkeypatch):
    key = tmp_path / "keys" / "gate_approval_key"
    key.parent.mkdir(parents=True)
    key.write_text("pytest-giu-thu-tu-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key))
    study = "PYTEST-GIU-THU-TU-20260926"
    d = tmp_path / "exports" / study
    d.mkdir(parents=True)
    artifact = d / "artifact.md"
    artifact.write_text(_NOI_DUNG, encoding="utf-8", newline="\n")
    return tmp_path, study, d, artifact


def _chuoi(study: str, entries, *, co_id_scope=()) -> list:
    """Sổ nối xích thật; chỉ bản ghi có gate trong co_id_scope được thêm approval_id/scope
    (hai trường KHÔNG được ký) — bản ghi còn lại from_file không parse được."""
    h = hashlib.sha256(_NOI_DUNG.encode("utf-8")).hexdigest()
    chain: list = []
    for i, (gate, ts) in enumerate(entries):
        role = _ROLE[gate]
        prev = GC.chain_prev_hash(chain[-1] if chain else None)
        rec = {
            "gate_id": gate, "decision": "APPROVED", "is_synthetic": False,
            "reviewer_role": role, "evidence_hash": h, "timestamp_utc": ts,
            "reviewer_identity_reference": "ref", "prev_hash": prev,
            "approver_signature": GC.sign_approval(gate, study, h, ts, reviewer_role=role,
                                                   reviewer_ref="ref", decision="APPROVED",
                                                   prev_hash=prev),
        }
        if gate in co_id_scope:
            rec = {"approval_id": f"id-{i}-{gate}", "scope": f"duyệt {gate}", **rec}
        chain.append(rec)
    return chain


def _ghi(root: Path, study: str, chain: list) -> Path:
    p = root / "exports" / study / "approval_ledger.json"
    p.write_text(json.dumps(chain, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert GC.write_ledger_seal(study, chain, repo_root=root)
    return p


def _ky_nhu_approve_gate(ledger_path: Path, study: str, gate: str, ts: str) -> None:
    raw = json.loads(ledger_path.read_text(encoding="utf-8"))
    prev = GC.chain_prev_hash(raw[-1] if raw and isinstance(raw[-1], dict) else None)
    h = hashlib.sha256(_NOI_DUNG.encode("utf-8")).hexdigest()
    role = _ROLE[gate]
    sig = GC.sign_approval(gate, study, h, ts, reviewer_role=role, reviewer_ref="ref",
                           decision="APPROVED", is_synthetic=False, prev_hash=prev)
    assert sig
    with ApprovalLedger.locked_update(ledger_path) as ledger:
        rec = ApprovalLedger.make_human_approval(
            gate_id=gate, reviewer_role=role, reviewer_ref="ref", scope=f"duyệt {gate}",
            evidence_content=_NOI_DUNG, decision=ApprovalDecisionEnum.APPROVED,
            approver_signature=sig, timestamp_utc=ts, prev_hash=prev,
        )
        ok, reason = ledger.add_approval(rec, created_by_agent=False)
        assert ok, reason


def _kiem(root: Path, study: str, artifact: Path, truoc: list, gates_moi: list) -> None:
    p = root / "exports" / study / "approval_ledger.json"
    sau = json.loads(p.read_text(encoding="utf-8"))
    # (d) phần tử cũ giữ nguyên từng byte JSON, đúng vị trí
    assert len(sau) == len(truoc) + len(gates_moi)
    for a, b in zip(truoc, sau):
        assert json.dumps(a, sort_keys=False) == json.dumps(b, sort_keys=False)
    assert [r["gate_id"] for r in sau] == [r["gate_id"] for r in truoc] + gates_moi
    ok, ly_do = GC.verify_ledger_chain(sau)
    assert ok, ly_do
    ok, ly_do = GC.verify_ledger_seal(study, sau, repo_root=root)
    assert ok, ly_do
    for gate in {r["gate_id"] for r in sau}:
        assert GC.ledger_approved(gate, study, artifact, repo_root=root) is True, gate


def test_dong_thieu_scope_o_giua_khong_bi_doi_xuong_cuoi(moi_truong):
    """(a) [G2, G8 thiếu scope, G9] + G10 ⇒ thứ tự giữ nguyên, chuỗi OK, 4 cổng True."""
    root, study, _d, artifact = moi_truong
    chain = _chuoi(study, [("G2", "2026-09-01T10:00:00Z"), ("G8", "2026-09-02T10:00:00Z"),
                           ("G9", "2026-09-03T10:00:00Z")], co_id_scope=("G2", "G9"))
    p = _ghi(root, study, chain)
    assert len(ApprovalLedger.from_file(p)._unparsed_raw) == 1   # fixture đúng: G8 không parse được
    _ky_nhu_approve_gate(p, study, "G10", "2026-09-04T10:00:00Z")
    _kiem(root, study, artifact, chain, ["G10"])


def test_dong_loi_o_duoi(moi_truong):
    """(b) [G2, G8 thiếu scope] + G9 ⇒ cả 3 cổng True."""
    root, study, _d, artifact = moi_truong
    chain = _chuoi(study, [("G2", "2026-09-01T10:00:00Z"), ("G8", "2026-09-02T10:00:00Z")],
                   co_id_scope=("G2",))
    p = _ghi(root, study, chain)
    _ky_nhu_approve_gate(p, study, "G9", "2026-09-03T10:00:00Z")
    _kiem(root, study, artifact, chain, ["G9"])


def test_so_dang_chained_ledger_khong_approval_id(moi_truong):
    """(c) Sổ không có approval_id/scope ở MỌI dòng (dạng _chained_ledger) ⇒ thêm hai
    lượt ký liên tiếp vẫn nối đúng chuỗi."""
    root, study, _d, artifact = moi_truong
    chain = _chuoi(study, [("G2", "2026-09-01T10:00:00Z"), ("G8", "2026-09-02T10:00:00Z")])
    p = _ghi(root, study, chain)
    _ky_nhu_approve_gate(p, study, "G9", "2026-09-03T10:00:00Z")
    _ky_nhu_approve_gate(p, study, "G10", "2026-09-04T10:00:00Z")
    _kiem(root, study, artifact, chain, ["G9", "G10"])


def test_khoa_ngoai_luoc_do_khong_bi_roi(moi_truong):
    """Phần tử đã nạp được ghi NGUYÊN VĂN — khoá ngoài lược đồ (vd bí danh
    reviewer_ref) không bị record_to_dict làm rơi."""
    root, study, _d, _artifact = moi_truong
    chain = _chuoi(study, [("G2", "2026-09-01T10:00:00Z")], co_id_scope=("G2",))
    chain[0]["reviewer_ref"] = "bi-danh-cu"
    p = _ghi(root, study, chain)
    _ky_nhu_approve_gate(p, study, "G9", "2026-09-03T10:00:00Z")
    sau = json.loads(p.read_text(encoding="utf-8"))
    assert sau[0] == chain[0]


def test_ledger_trong_bo_nho_giu_hanh_vi_cu(tmp_path):
    """Ledger không nạp file: xuất đúng các bản ghi đã thêm, kể cả nối thẳng _records."""
    ledger = ApprovalLedger()
    r1 = ApprovalLedger.make_human_approval(gate_id="G4", reviewer_role="PI", reviewer_ref="a",
                                            scope="s", evidence_content="e1")
    r2 = ApprovalLedger.make_synthetic_approval(gate_id="G5", scope="s", evidence_content="e2")
    assert ledger.add_approval(r1)[0]
    ledger._records.append(r2)
    out = json.loads(ledger.export_json())
    assert [d["gate_id"] for d in out] == ["G4", "G5"]
