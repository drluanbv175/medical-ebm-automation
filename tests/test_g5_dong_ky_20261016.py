"""ĐỒNG KÝ khoá dữ liệu G5 (diễn tập C1a 16/10/2026): quản trị dữ liệu ký trước ⇒ PASS_G5_DATA_LOCKED ⇒ PI đồng ký
từng bị từ chối «chưa ở READY». Nay nhận đồng ký khi đã khoá VÀ mọi tiêu chí tự động PASS; báo cáo ghi vai đã ký."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import approve_gate as AG  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402

_STUDY = "zz-test-g5-dong-ky-20261016"


@pytest.fixture()
def thu_muc():
    d = REPO_ROOT / "exports" / _STUDY
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _tieu_chi(*review: str) -> list[dict]:
    hang = [{"id": "G5-AUTO-01", "label": "khoá", "status": "PASS", "evidence": "ok"},
            {"id": "G5-HUMAN-01", "label": "ký", "status": "PASS", "evidence": "approval_ledger_G5=True"}]
    hang += [{"id": ma, "label": "rà", "status": "REVIEW", "evidence": "x"} for ma in review]
    return hang


def _ky_pi(monkeypatch, thu_muc: Path, bao_cao: dict) -> int:
    cp = thu_muc / "G5_checkpoint.json"
    if not cp.exists():
        cp.write_text('{"gate": "G5"}', encoding="utf-8", newline="\n")
    monkeypatch.setattr(G5Q, "evaluate_study", lambda *a, **k: bao_cao)
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", "--study", _STUDY, "--gate", "G5", "--artifact", str(cp),
                                      "--reviewer-role", "PI", "--reviewer-ref", "PI-01"])
    return AG.main()


def test_dong_ky_pi_sau_khi_da_khoa_duoc_ghi_so_cai(monkeypatch, thu_muc, capsys):
    ma = _ky_pi(monkeypatch, thu_muc, {"status": G5Q.STATUS_LOCKED, "automatic_criteria": _tieu_chi()})
    out = capsys.readouterr().out
    assert "TỪ CHỐI ký G5" not in out, out
    assert ma == 0, out
    so = json.loads((thu_muc / "approval_ledger.json").read_text(encoding="utf-8"))
    assert [r["gate_id"] for r in so] == ["G5"] and so[0]["reviewer_role"] == "PI"


def test_da_khoa_nhung_con_review_thi_khong_dong_ky(monkeypatch, thu_muc, capsys):
    ma = _ky_pi(monkeypatch, thu_muc, {"status": G5Q.STATUS_LOCKED, "automatic_criteria": _tieu_chi("G5-AUTO-04b")})
    out = capsys.readouterr().out
    assert ma != 0 and "TỪ CHỐI ký G5" in out and "REVIEW G5-AUTO-04b" in out, out
    assert not (thu_muc / "approval_ledger.json").exists()


def test_trang_thai_khac_ready_va_locked_van_bi_chan(monkeypatch, thu_muc, capsys):
    ma = _ky_pi(monkeypatch, thu_muc, {"status": G5Q.STATUS_DRAFT, "automatic_criteria": _tieu_chi()})
    assert ma != 0 and "TỪ CHỐI ký G5" in capsys.readouterr().out
    assert not (thu_muc / "approval_ledger.json").exists()


def _so_cai(thu_muc: Path, cp: Path, ban_ghi: list[tuple[str, str, str, bool]]) -> None:
    h = hashlib.sha256(cp.read_bytes()).hexdigest()
    (thu_muc / "approval_ledger.json").write_text(json.dumps([
        {"gate_id": cong, "decision": quyet, "reviewer_role": vai, "evidence_hash": h if dung_hash else "0" * 64}
        for cong, quyet, vai, dung_hash in ban_ghi]), encoding="utf-8", newline="\n")


def test_vai_da_ky_doc_dung_hash_va_thu_hoi(thu_muc):
    cp = thu_muc / "G5_checkpoint.json"
    cp.write_text('{"gate": "G5"}', encoding="utf-8", newline="\n")
    _so_cai(thu_muc, cp, [("G5", "APPROVED", "DATA_GOVERNANCE_QA_REVIEWER", True), ("G5", "APPROVED", "PI", True)])
    assert G5Q.vai_da_ky_g5(_STUDY, cp, REPO_ROOT) == ["DATA_MANAGER", "PI"]
    _so_cai(thu_muc, cp, [("G5", "APPROVED", "PI", True), ("G5", "REJECTED", "PI", True),
                          ("G5", "APPROVED", "DATA_MANAGER", True), ("G4", "APPROVED", "PI", True),
                          ("G5", "APPROVED", "PI", False)])
    assert G5Q.vai_da_ky_g5(_STUDY, cp, REPO_ROOT) == ["DATA_MANAGER"], "thu hồi · cổng khác · hash cũ: không tính"


def test_bao_cao_markdown_ghi_vai_da_ky(tmp_path):
    md = tmp_path / "r.md"
    G5Q._write_markdown(md, {"vai_da_ky": ["DATA_MANAGER", "PI"], "dong_ky_du": True, "automatic_criteria": []})
    assert "Vai đã ký G5: DATA_MANAGER + PI (đồng ký đủ" in md.read_text(encoding="utf-8")
    G5Q._write_markdown(md, {"vai_da_ky": [], "automatic_criteria": []})
    assert "Vai đã ký G5: chưa có" in md.read_text(encoding="utf-8")
