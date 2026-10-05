"""Hồi quy #42 (2026-09-26): hành vi BLOCKED của cổng chất lượng G6 (AUTO-00 thiếu
đầu vào, AUTO-02 lệch seed SAP↔script) phải được kiểm bằng fixture TỔNG HỢP trong
tmp_path — chạy được trên CI/Cloud.

Trước đây chỉ tests/test_g6_quality_gate_20260815.py kiểm, và tệp đó dựa vào fixture
exports/ nằm NGOÀI git (chỉ có trên OneDrive) ⇒ đột biến tháo phép kiểm seed hoặc
AUTO-00 sống sót trên CI. Tệp cũ được GIỮ cho máy bác sĩ.

Khuôn fixture: G4 phải ĐÃ KHOÁ — thiếu thì AUTO-01 tự chặn và làm BLOCKED ngay cả khi phép
kiểm seed bị tháo (xanh giả). Từ 04/10/2026 (G6-01) ``g4_was_locked`` tự khai KHÔNG còn đủ:
test cần AUTO-01 đạt giả lập đúng phép kiểm thật (_g4_da_khoa: sổ cái + G4 chấm trực tiếp).
Mọi test gọi evaluate_study(study, out_dir=tmp_path, …) với study id riêng; KHÔNG ghi exports/ thật.
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

import g6_quality_gate as G6Q  # noqa: E402

_STUDY = "ZZSYN-G6-QG-20260926"


def _dung(d: Path, *, seed_sap: int | None = 2026, seed_script: int | None = 2026,
          co_sap: bool = True) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    script = "# Script phân tích\n```r\n"
    if seed_script is not None:
        script += f"set.seed({seed_script})\n"
    script += "summary(df)\n```\n"
    (d / f"G6_A7_ANALYSIS_SCRIPTS_{_STUDY}.md").write_text(script, encoding="utf-8", newline="\n")
    if co_sap:
        sap = "# SAP\n\n### §10 Tái lập\n"
        if seed_sap is not None:
            sap += f"Hạt giống ngẫu nhiên: set.seed({seed_sap})\n"
        sap += "\n### §11 Khác\nnội dung\n"
        (d / f"G4_A5_SAP_FINAL_{_STUDY}.md").write_text(sap, encoding="utf-8", newline="\n")
    (d / "G6_checkpoint.json").write_text(json.dumps({"g4_was_locked": True}),
                                          encoding="utf-8", newline="\n")
    return d


def _check(bao: dict, ma: str) -> dict:
    hits = [k for k in bao["checks"] if k["id"] == ma]
    assert hits, f"không thấy {ma} trong {[k['id'] for k in bao['checks']]}"
    return hits[-1]


def test_thieu_sap_auto00_chan(tmp_path):
    d = _dung(tmp_path / _STUDY, co_sap=False)
    bao = G6Q.evaluate_study(_STUDY, out_dir=d, write=False)
    assert bao["status"] == "BLOCKED"
    c = _check(bao, "G6-AUTO-00")
    assert c["pass"] is False and c["blocking"] is True
    assert "G4_A5_SAP_FINAL" in c["detail"]


def test_seed_lech_auto02_chan_va_auto01_dat(tmp_path, monkeypatch):
    monkeypatch.setattr(G6Q, "_g4_da_khoa", lambda *a, **k: (True, "giả lập: sổ cái + G4 PASS_G4_SAP_LOCKED"))
    d = _dung(tmp_path / _STUDY, seed_sap=9999, seed_script=2026)
    bao = G6Q.evaluate_study(_STUDY, out_dir=d, write=False)
    # AUTO-01 phải ĐẠT để BLOCKED quy được đúng về AUTO-02 (không xanh giả).
    assert _check(bao, "G6-AUTO-01")["pass"] is True
    c = _check(bao, "G6-AUTO-02")
    assert c["pass"] is False and c["blocking"] is True
    assert "9999" in c["detail"] and "2026" in c["detail"]
    assert bao["status"] == "BLOCKED"


def test_doi_chung_seed_khop_khong_blocked(tmp_path):
    d = _dung(tmp_path / _STUDY, seed_sap=2026, seed_script=2026)
    bao = G6Q.evaluate_study(_STUDY, out_dir=d, write=False)
    assert _check(bao, "G6-AUTO-02")["pass"] is True
    assert bao["status"] != "BLOCKED", bao["checks"]


def test_sap_co_seed_script_khong_seed_chan(tmp_path):
    d = _dung(tmp_path / _STUDY, seed_sap=2026, seed_script=None)
    bao = G6Q.evaluate_study(_STUDY, out_dir=d, write=False)
    c = _check(bao, "G6-AUTO-02")
    assert c["pass"] is False and c["blocking"] is True
    assert bao["status"] == "BLOCKED"


@pytest.mark.parametrize("write", [False, True])
def test_write_false_khong_ghi_gi_doi_chung_write_true(tmp_path, write):
    d = _dung(tmp_path / _STUDY, seed_sap=9999, seed_script=2026)
    cp = d / "G6_checkpoint.json"
    truoc = cp.read_bytes()
    G6Q.evaluate_study(_STUDY, out_dir=d, write=write)
    co_report = (d / "G6_QUALITY_REPORT.json").exists() and (d / "G6_QUALITY_REPORT.md").exists()
    if write:
        assert co_report, "đối chứng: write=True phải ghi report (chứng minh ca write=False có nghĩa)"
    else:
        assert not (d / "G6_QUALITY_REPORT.json").exists()
        assert not (d / "G6_QUALITY_REPORT.md").exists()
        assert cp.read_bytes() == truoc
