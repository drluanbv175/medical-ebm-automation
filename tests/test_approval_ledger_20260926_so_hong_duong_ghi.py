"""Hồi quy #8 (2026-09-26): approval_ledger.json TỒN TẠI mà hỏng KHÔNG được bị
đường GHI xoá sạch rồi niêm phong lại như hợp lệ.

Lỗi gốc (đã tái lập): sổ 2 bản ghi bị cắt cụt → một lượt locked_update thêm G4 →
sổ còn đúng 1 bản ghi, con dấu mới record_count=1, verify_ledger_seal trả True.
Lịch sử phê duyệt (kể cả quyết định THU HỒI) mất vĩnh viễn vì exports/ bị gitignore.

Bản vá: locked_update nạp NGHIÊM NGẶT (LedgerUnreadable) trước khi yield; approve_gate
và approve_gate_synthetic_admin trả 1 TRƯỚC khi ký. Đường ĐỌC (from_file mặc định)
giữ «hỏng = rỗng» cho công cụ kiểm toán chỉ-đọc.

Mọi test chạy trong tmp_path — không đụng exports/ thật, không đụng ledger thật.
"""
from __future__ import annotations

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
from runtime.approval_ledger import ApprovalLedger, LedgerUnreadable  # noqa: E402
from runtime.schemas import ApprovalDecisionEnum  # noqa: E402

_STUDY = "PYTEST-SO-HONG-20260926"


@pytest.fixture()
def khoa(tmp_path, monkeypatch):
    key_path = tmp_path / "keys" / "gate_approval_key"
    key_path.parent.mkdir(parents=True)
    key_path.write_text("pytest-so-hong-key", encoding="utf-8", newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))
    return key_path


@pytest.fixture()
def study_dir(tmp_path):
    d = tmp_path / "exports" / _STUDY
    d.mkdir(parents=True)
    return d


def _add(ledger_path: Path, gate_id: str, decision=ApprovalDecisionEnum.APPROVED) -> None:
    with ApprovalLedger.locked_update(ledger_path) as ledger:
        rec = ApprovalLedger.make_human_approval(
            gate_id=gate_id, reviewer_role="PI_PROJECT_OWNER", reviewer_ref=f"REF-{gate_id}",
            scope=f"test {gate_id}", evidence_content=f"evidence {gate_id}", decision=decision,
        )
        ok, reason = ledger.add_approval(rec, created_by_agent=False)
        assert ok, reason


def _so_hai_ban_ghi_bi_cat(study_dir: Path) -> Path:
    ledger_path = study_dir / "approval_ledger.json"
    _add(ledger_path, "G2")
    _add(ledger_path, "G2", ApprovalDecisionEnum.REJECTED)
    seal = study_dir / "approval_ledger.seal.json"
    assert seal.exists(), "fixture phải có con dấu (khoá test đã cấu hình)"
    data = ledger_path.read_bytes()
    ledger_path.write_bytes(data[:-40])   # cắt cụt → JSON hỏng
    with pytest.raises(ValueError):
        json.loads(ledger_path.read_text(encoding="utf-8"))
    return ledger_path


def test_so_bi_cat_locked_update_nem_loi_khong_ghi_gi(khoa, study_dir):
    ledger_path = _so_hai_ban_ghi_bi_cat(study_dir)
    seal = study_dir / "approval_ledger.seal.json"
    truoc_so, truoc_seal = ledger_path.read_bytes(), seal.read_bytes()

    with pytest.raises(LedgerUnreadable):
        _add(ledger_path, "G4")

    assert ledger_path.read_bytes() == truoc_so, "sổ hỏng bị GHI ĐÈ — lịch sử bị xoá"
    assert seal.read_bytes() == truoc_seal, "con dấu bị NIÊM PHONG LẠI trên sổ bị cắt"
    assert not (study_dir / "approval_ledger.json.tmp").exists()
    # Chỉ SAO CHÉP bản chụp hỗ trợ khôi phục, tệp gốc vẫn tại chỗ.
    snaps = list(study_dir.glob("approval_ledger.json.corrupt-*"))
    assert len(snaps) == 1 and snaps[0].read_bytes() == truoc_so


@pytest.mark.parametrize("noi_dung", ['{"G2": "APPROVED"}', "42", "", "   \n"])
def test_goc_khong_phai_list_hoac_rong_nem_loi(khoa, study_dir, noi_dung):
    ledger_path = study_dir / "approval_ledger.json"
    ledger_path.write_text(noi_dung, encoding="utf-8", newline="\n")
    with pytest.raises(LedgerUnreadable):
        _add(ledger_path, "G4")
    assert ledger_path.read_text(encoding="utf-8") == noi_dung


def test_duong_doc_mac_dinh_van_tra_rong_khong_nem(study_dir):
    """Đường ĐỌC (công cụ kiểm toán) giữ hành vi cũ: hỏng ⇒ sổ rỗng, không raise."""
    p = study_dir / "approval_ledger.json"
    for noi_dung in ("{ hỏng", "42", '{"a": 1}'):
        p.write_text(noi_dung, encoding="utf-8", newline="\n")
        assert ApprovalLedger.from_file(p).count() == 0


def test_so_khong_ton_tai_van_ghi_binh_thuong(khoa, study_dir):
    """Đối chứng: đề tài chưa từng duyệt (không có tệp) vẫn ký được."""
    ledger_path = study_dir / "approval_ledger.json"
    _add(ledger_path, "G4")
    assert len(json.loads(ledger_path.read_text(encoding="utf-8"))) == 1


def test_cli_g2_rejected_tren_so_hong_tra_1(khoa, study_dir, tmp_path, monkeypatch, capsys):
    ledger_path = _so_hai_ban_ghi_bi_cat(study_dir)
    seal = study_dir / "approval_ledger.seal.json"
    truoc_so, truoc_seal = ledger_path.read_bytes(), seal.read_bytes()
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\nnội dung\n", encoding="utf-8", newline="\n")
    # Trỏ approve_gate + gate_contract vào cây tmp_path (study_dir, con dấu) — không
    # bao giờ chạm exports/ thật của repo.
    fake_tools = tmp_path / "tools"
    fake_tools.mkdir()
    monkeypatch.setattr(AG, "__file__", str(fake_tools / "approve_gate.py"))
    monkeypatch.setattr(GC, "__file__", str(fake_tools / "gate_contract.py"))
    monkeypatch.setattr(sys, "argv", [
        "approve_gate.py", "--study", _STUDY, "--gate", "G2", "--artifact", str(artifact),
        "--reviewer-role", "IRB", "--reviewer-ref", "IRB-01", "--decision", "REJECTED",
    ])
    assert AG.main() == 1
    out = capsys.readouterr().out
    assert "sổ cái KHÔNG đọc được" in out, out   # từ chối ĐÚNG lý do, không phải lý do khác
    assert ledger_path.read_bytes() == truoc_so
    assert seal.read_bytes() == truoc_seal
    assert artifact.read_text(encoding="utf-8") == "# Hồ sơ đạo đức\nnội dung\n"
