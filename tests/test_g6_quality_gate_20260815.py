# -*- coding: utf-8 -*-
"""Hồi quy cho g6_quality_gate (PHA R, 15/08/2026) — lớp quality cuối cùng (11/11).

Dùng fixture THẬT trong exports/ (không dựng giả): ZZREB2-G6-SAPDRIFT sinh ra
đúng để chở một drift seed; REFUTE-G6-RCT-HR thiếu SAP. Hai phép đột biến
(tháo seed-check, tháo ánh xạ BLOCKED) đã chạy tay 15/08 — đều làm cổng mất răng
rồi phục hồi; test ở đây khoá HÀNH VI để refactor sau không tháo lặng lẽ.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def _nap():
    spec = importlib.util.spec_from_file_location(
        "g6qg_test", HERE / "tools" / "g6_quality_gate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["g6qg_test"] = m
    spec.loader.exec_module(m)
    return m


def test_thieu_sap_thi_blocked_khong_doan():
    """Không có SAP để đối chiếu ⇒ BLOCKED ngay AUTO-00 — không suy đoán hộ."""
    m = _nap()
    bao = m.evaluate_study("REFUTE-G6-RCT-HR", write=False)
    assert bao["status"] == "BLOCKED"
    assert any(k["id"] == "G6-AUTO-00" and k["pass"] is False for k in bao["checks"])


def test_sapdrift_seed_bi_bat():
    """SAP ấn định seed KHÁC seed trong script ⇒ BLOCKED nêu rõ hai giá trị.

    Lịch sử: kỳ vọng đầu dựa trên fixture ZZREB2 khi cổng CHỈ đọc artifact md;
    sau khi cổng đọc đủ scripts/ (bản vá 15/08) thì seed fixture đó khớp thật —
    kỳ vọng cũ sai chứ không phải cổng sai. Nay dựng drift THẬT: nhân bản fixture
    rồi đổi seed SAP thành 9999 ≠ 2026 của template R.
    """
    import re
    import shutil
    m = _nap()
    goc = HERE / "exports" / "ZZREB2-G6-SAPDRIFT"
    tmp = HERE / "exports" / "ZZTEST-G6-SEED-DRIFT-TMP"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(goc, tmp)
    try:
        for f in tmp.glob("G6_A7_ANALYSIS_SCRIPTS_ZZREB2-G6-SAPDRIFT.*"):
            f.rename(tmp / f.name.replace("ZZREB2-G6-SAPDRIFT",
                                          "ZZTEST-G6-SEED-DRIFT-TMP"))
        for f in tmp.glob("G4_A5_SAP_FINAL_ZZREB2-G6-SAPDRIFT.*"):
            f.rename(tmp / f.name.replace("ZZREB2-G6-SAPDRIFT",
                                          "ZZTEST-G6-SEED-DRIFT-TMP"))
        sap = tmp / "G4_A5_SAP_FINAL_ZZTEST-G6-SEED-DRIFT-TMP.md"
        sap.write_text(re.sub(r"set\.seed\(\d+\)", "set.seed(9999)",
                              sap.read_text(encoding="utf-8")), encoding="utf-8")
        bao = m.evaluate_study("ZZTEST-G6-SEED-DRIFT-TMP", write=False)
        lech = [k for k in bao["checks"] if k["id"] == "G6-AUTO-02"]
        assert bao["status"] == "BLOCKED"
        assert lech and lech[0]["pass"] is False and "9999" in lech[0]["detail"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_fixture_lanh_khong_bi_block_oan():
    """Fixture đủ bộ, SAP còn placeholder ⇒ trạng thái CHỜ NGƯỜI, không phải BLOCKED
    (biến «chưa biết» thành «có vấn đề» là lớp lỗi BH08 — cổng không được mắc)."""
    m = _nap()
    bao = m.evaluate_study("ZZPH-G6-AUDIT", write=False)
    assert bao["status"] in ("READY_FOR_STATISTICIAN_REVIEW",
                             "DRAFT_NEEDS_HUMAN_PARAMETERS")


def test_khong_ghi_khi_write_false():
    """write=False không được để lại report — hàm chấm phải sạch tác dụng phụ."""
    m = _nap()
    bc = HERE / "exports" / "REFUTE-G6-RCT-HR" / "G6_QUALITY_REPORT.json"
    truoc = bc.read_bytes() if bc.exists() else None
    m.evaluate_study("REFUTE-G6-RCT-HR", write=False)
    sau = bc.read_bytes() if bc.exists() else None
    assert truoc == sau


def test_moi_check_deu_co_ba_truong():
    """Hợp đồng cấu trúc: mỗi check mang id/pass/blocking — consumer đọc máy được."""
    m = _nap()
    bao = m.evaluate_study("ZZPH-G6-AUDIT", write=False)
    for k in bao["checks"]:
        assert {"id", "pass", "detail", "blocking"} <= set(k)
