# -*- coding: utf-8 -*-
"""CHUNG-D (soát từng cổng G0–G10, 04/10/2026) — approve_gate:
  • lệnh ký THẤT BẠI trước khi ghi sổ cái ⇒ artifact về ĐÚNG byte trước lệnh (G2 từng để lại phụ lục quyết định IRB
    trong gói đạo đức dù không ký; G10 từng để lại checkpoint đã dọn needs_input);
  • tiêu chí NGƯỜI kiểm được trước khi ký (G2-HUMAN-01; G8-HUMAN-01, G8-HUMAN-05) chưa PASS ⇒ từ chối;
  • thiết kế cho bước ký G2 lấy từ pin của bác sĩ đối chiếu các cổng, không từ G2_checkpoint (không ký); RCT phải
    tiến cứu.
Bộ chấm được giả lập (monkeypatch) — test khoá LOGIC NỐI DÂY của approve_gate, không nội dung GxQ.
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
import g8_quality_gate as G8Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402

_STUDY = "PYTEST-CHUNG-D-20261004"


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


def _run(monkeypatch, *args) -> int:
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", *args])
    return AG.main()


def _bao_cao(status, nguoi_pass=True, thieu=()):
    nguoi = [{"id": tid, "label": tid, "status": "PASS" if (nguoi_pass and tid not in thieu) else "REVIEW",
              "evidence": "giả lập"} for tid in ("G2-HUMAN-01", "G8-HUMAN-01", "G8-HUMAN-05")]
    return {"status": status, "automatic_criteria": [], "approval_criteria": nguoi, "human_approval_criteria": nguoi}


def _g2_args(artifact, mode="NOT_APPLICABLE"):
    return ["--study", _STUDY, "--gate", "G2", "--artifact", str(artifact), "--reviewer-role", "IRB",
            "--reviewer-ref", "IRB-01", "--g2-approval-number", "IRB-2026-001", "--g2-approval-date", "2026-08-01",
            "--g2-valid-until", "2027-08-01", "--g2-protocol-version", "v1.0", "--g2-icf-version", "v1.0",
            "--g2-ethics-decision", "APPROVED", "--g2-recruitment-mode", mode,
            "--g2-registration-status", "NOT_REQUIRED"]


def _so_cai_rong(study_dir: Path) -> bool:
    p = study_dir / "approval_ledger.json"
    return not p.exists() or json.loads(p.read_text(encoding="utf-8")) == []


def test_g2_cham_that_bai_thi_goi_dao_duc_ve_dung_byte(monkeypatch, study_dir):
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\nNội dung đầy đủ, không placeholder.\n", encoding="utf-8", newline="\n")
    goc = artifact.read_bytes()
    monkeypatch.setattr(G2Q, "evaluate_study", lambda *a, **k: _bao_cao(G2Q.STATUS_DRAFT))
    assert _run(monkeypatch, *_g2_args(artifact)) != 0
    assert artifact.read_bytes() == goc, "phụ lục quyết định IRB không được ở lại trong gói khi không ký"
    assert _so_cai_rong(study_dir)


def test_g2_tieu_chi_nguoi_truoc_ky_chua_dat_thi_tu_choi(monkeypatch, study_dir, capsys):
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\nNội dung đầy đủ.\n", encoding="utf-8", newline="\n")
    goc = artifact.read_bytes()
    monkeypatch.setattr(G2Q, "evaluate_study",
                        lambda *a, **k: _bao_cao(G2Q.STATUS_PENDING, thieu=("G2-HUMAN-01",)))
    assert _run(monkeypatch, *_g2_args(artifact)) != 0
    out = capsys.readouterr().out
    assert artifact.read_bytes() == goc and _so_cai_rong(study_dir)
    assert "tiêu chí người kiểm được TRƯỚC khi ký chưa đạt" in out and "G2-HUMAN-01" in out, out


def test_g2_bao_cao_vang_tieu_chi_nguoi_la_fail_closed():
    assert AG._tieu_chi_nguoi_chua_dat("G2", {"status": "PENDING"}) == [
        "G2-HUMAN-01: không thấy trong báo cáo chấm (fail-closed)"]
    assert AG._tieu_chi_nguoi_chua_dat("G4", {}) == [], "cổng không có tiêu chí người trước ký ⇒ không thêm điều kiện"


def test_g2_rct_ghi_hoi_cuu_bi_tu_choi(monkeypatch, study_dir):
    (study_dir / "study_meta.json").write_text('{"design_code": "rct"}', encoding="utf-8", newline="\n")
    artifact = study_dir / f"G2_A3_ETHICS_PACKAGE_{_STUDY}.md"
    artifact.write_text("# Hồ sơ đạo đức\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(G2Q, "evaluate_study", lambda *a, **k: _bao_cao(G2Q.STATUS_PENDING))
    assert _run(monkeypatch, *_g2_args(artifact, mode="RETROSPECTIVE_SECONDARY_DATA")) != 0
    assert _so_cai_rong(study_dir)


def test_thiet_ke_g2_lay_pin_bac_si_doi_chieu_cong(study_dir):
    (study_dir / "study_meta.json").write_text('{"design_code": "RCT"}', encoding="utf-8", newline="\n")
    assert AG._thiet_ke_cho_g2(study_dir) == ("rct", [])
    (study_dir / "G2_checkpoint.json").write_text('{"design_code": "cohort"}', encoding="utf-8", newline="\n")
    ma, loi = AG._thiet_ke_cho_g2(study_dir)
    assert loi and "khác thiết kế các cổng" in loi[0], "checkpoint G2 (không ký) không được lặng lẽ đè pin bác sĩ"


def test_g8_khai_bao_nguoi_phan_bien_chua_du_thi_tu_choi(monkeypatch, study_dir, capsys):
    artifact = study_dir / G8Q.presubmission_artifact_name(_STUDY)
    artifact.write_text("# A9\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(G8Q, "evaluate_study",
                        lambda *a, **k: _bao_cao(G8Q.STATUS_PENDING, thieu=("G8-HUMAN-05",)))
    rc = _run(monkeypatch, "--study", _STUDY, "--gate", "G8", "--artifact", str(artifact),
              "--reviewer-role", "PEER_REVIEWER", "--reviewer-ref", "REV-77")
    out = capsys.readouterr().out
    assert rc != 0 and _so_cai_rong(study_dir)
    assert "tiêu chí người kiểm được TRƯỚC khi ký chưa đạt" in out and "G8-HUMAN-05" in out, out


def test_g10_cham_that_bai_sau_khi_don_needs_input_thi_checkpoint_ve_dung_byte(monkeypatch, study_dir):
    artifact = study_dir / G10Q.CHECKPOINT_JSON
    artifact.write_text(json.dumps({"gate": "G10", "needs_input": {"blocked": True}}, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    goc = artifact.read_bytes()
    monkeypatch.setattr(G10Q, "evaluate_study", lambda *a, **k: {"status": G10Q.STATUS_READY,
                                                                 "automatic_criteria": []})

    def ky_hong(*a, **k):
        raise RuntimeError("giả lập lỗi ký sau khi checkpoint đã bị dọn")
    monkeypatch.setattr(AG.GC, "sign_approval", ky_hong)
    with pytest.raises(RuntimeError):
        _run(monkeypatch, "--study", _STUDY, "--gate", "G10", "--artifact", str(artifact),
             "--reviewer-role", "Chủ nhiệm đề tài", "--reviewer-ref", "PI-01")
    assert artifact.read_bytes() == goc, "checkpoint G10 không được giữ bản đã dọn needs_input khi không ký"
    assert _so_cai_rong(study_dir)
