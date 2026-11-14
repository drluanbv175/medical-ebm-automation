# -*- coding: utf-8 -*-
"""G4-HUMAN-03 so theo VAI thống kê viên và không hạ cấp SAP đã khoá (giả lập đề tài lần 1, K3 — 14/11/2026).

Lỗi gốc (diễn tập C1a, khoá giả): G4-HUMAN-03 so reviewer_ref của bản ký G4 MỚI NHẤT bất kỳ vai (PI đồng ký) với bản
mới nhất của từng cổng khác ⇒ PI ký G5 bằng cùng mã ⇒ G4 rơi khỏi PASS_G4_SAP_LOCKED hồi tố ⇒ G5-AUTO-05 «G4=False»
⇒ G6… chặn cả chuỗi. Bác sĩ kiêm mọi vai là thiết kế đã biết nên đề tài thật gần như chắc gặp.

Vá: (1) so reviewer_ref của bản ký VAI STATISTICIAN của G4 với mọi bản ký VAI KHÁC (gồm PI đồng ký G4); (2) sau khi G4
đã ký hợp lệ, G4-HUMAN-03 chỉ HIỂN THỊ — không tham gia human_complete (nguyên tắc «sự kiện sau không hạ cấp quyết định
đã ký»); trước khi ký vẫn hiện REVIEW để nhắc.

Luồng KÝ dùng exports/PYTEST-… của cây (approve_gate cố định gốc) với khoá ký GIẢ trong thư mục tạm (EBM_GATE_KEY_PATH),
dọn sạch sau test. Dữ liệu tổng hợp, không mạng, không PII.
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import approve_gate as AG  # noqa: E402
import cong_song as CS  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402
from _chuoi_da_chot import dien_sap_g4, dung_g0_g3_da_chot, sinh_sap_g4_that, xac_nhan_g4  # noqa: E402
from test_g4_quality_gate import _evaluate, _row  # noqa: E402

# ════════════════════════════════════════════════════════════════════════════
# Đơn vị — đọc sổ cái theo vai
# ════════════════════════════════════════════════════════════════════════════


def test_doc_ban_ky_theo_vai_lay_moi_nhat_tung_cap_cong_vai():
    so = [
        {"gate_id": "G4", "decision": "APPROVED", "reviewer_role": "METHODS_STATISTICS_REVIEWER",
         "reviewer_identity_reference": "TKV-CU", "timestamp_utc": "2026-11-01T08:00:00Z"},
        {"gate_id": "G4", "decision": "APPROVED", "reviewer_role": "METHODS_STATISTICS_REVIEWER",
         "reviewer_identity_reference": "TKV-MOI", "timestamp_utc": "2026-11-02T08:00:00Z"},
        {"gate_id": "G4", "decision": "APPROVED", "reviewer_role": "PI",
         "reviewer_identity_reference": "PI-1", "timestamp_utc": "2026-11-03T08:00:00Z"},
        {"gate_id": "G5", "decision": "REJECTED", "reviewer_role": "PI",
         "reviewer_identity_reference": "PI-TU-CHOI", "timestamp_utc": "2026-11-04T08:00:00Z"},
        {"gate_id": "A12", "decision": "APPROVED", "reviewer_role": "",
         "reviewer_identity_reference": "MAY", "timestamp_utc": "2026-11-05T08:00:00Z"},
    ]
    assert G4Q.doc_ban_ky_theo_vai(so) == {"G4/STATISTICIAN": "TKV-MOI", "G4/PI": "PI-1"}


# ════════════════════════════════════════════════════════════════════════════
# Đơn vị — G4-HUMAN-03 theo vai + chỉ hiển thị sau khi ký
# ════════════════════════════════════════════════════════════════════════════


def test_thong_ke_vien_khac_moi_vai_thi_pass_va_khoa():
    r = _evaluate(ban_ky_theo_vai={"G4/STATISTICIAN": "TKV-01", "G4/PI": "PI-01", "G5/PI": "PI-01",
                                   "G2/IRB": "IRB-01"})
    row = _row(r, "G4-HUMAN-03")
    assert row["status"] == "PASS" and "thống kê viên" in row["evidence"], row
    assert r["status"] == G4Q.STATUS_LOCKED


def test_pi_ky_cong_sau_cung_ma_pi_dong_ky_g4_khong_lam_trung():
    """Đúng kịch bản diễn tập C1a: PI đồng ký G4 và ký G5 cùng mã; thống kê viên mã riêng ⇒ PASS (bản cũ REVIEW)."""
    r = _evaluate(ban_ky_theo_vai={"G4/STATISTICIAN": "DIEN-TAP-TKV", "G4/PI": "DIEN-TAP-PI",
                                   "G5/DATA_MANAGER": "DIEN-TAP-DM", "G5/PI": "DIEN-TAP-PI"})
    assert _row(r, "G4-HUMAN-03")["status"] == "PASS"
    assert r["status"] == G4Q.STATUS_LOCKED


def test_thong_ke_vien_trung_pi_dong_ky_g4_thi_review_nhung_van_khoa_sau_ky():
    """Một người ký hai vai trên CÙNG SAP (so sau chuẩn hoá hoa/thường như G8/G9) ⇒ chỉ dấu REVIEW, nhưng G4 đã ký
    hợp lệ nên chỉ HIỂN THỊ — SAP vẫn khoá, việc nhắc vẫn nằm trong pending_actions."""
    r = _evaluate(ban_ky_theo_vai={"G4/STATISTICIAN": "BS-Moi-Vai", "G4/PI": "bs moi vai"})
    row = _row(r, "G4-HUMAN-03")
    assert row["status"] == "REVIEW" and "TRÙNG" in row["evidence"] and "G4/PI" in row["evidence"], row
    assert "CHỈ HIỂN THỊ" in row["evidence"], row
    assert r["status"] == G4Q.STATUS_LOCKED
    assert r["human_confirmation_complete"] is True
    assert row["action"] in r["pending_actions"]


def test_chua_ky_thi_van_nhac_review():
    r = _evaluate(ledger_signed=False, ledger_reason="chưa có bản ghi phê duyệt nào cho cổng G4",
                  ban_ky_theo_vai={"G4/STATISTICIAN": "BS-A", "G2/IRB": "BS-A"})
    row = _row(r, "G4-HUMAN-03")
    assert row["status"] == "REVIEW" and "TRÙNG" in row["evidence"], row
    assert "CHỈ HIỂN THỊ" not in row["evidence"], "trước khi ký là lời NHẮC, không phải dòng chỉ hiển thị"
    assert r["status"] == G4Q.STATUS_READY


def test_chi_pi_ky_g4_thi_review_chua_co_thong_ke_vien():
    r = _evaluate(ban_ky_theo_vai={"G4/PI": "PI-01", "G2/IRB": "IRB-01"})
    row = _row(r, "G4-HUMAN-03")
    assert row["status"] == "REVIEW" and "chưa có bản ký G4 của vai thống kê viên" in row["evidence"], row
    assert "G4/PI" in row["evidence"]
    assert r["status"] == G4Q.STATUS_LOCKED, "G4 cho PI ký (hợp đồng vai) — thiếu chỉ dấu không hạ cấp SAP đã ký"


def test_thong_ke_vien_ky_cong_khac_cung_vai_khong_tinh_trung():
    r = _evaluate(ban_ky_theo_vai={"G4/STATISTICIAN": "TKV-01", "G6/STATISTICIAN": "TKV-01", "G9/PI": "PI-01"})
    assert _row(r, "G4-HUMAN-03")["status"] == "PASS"


def test_thong_ke_vien_khong_ghi_ref_thi_khong_doi_chieu_duoc():
    row = _row(_evaluate(ban_ky_theo_vai={"G4/STATISTICIAN": "", "G4/PI": "PI-01"}), "G4-HUMAN-03")
    assert row["status"] == "REVIEW" and "không đối chiếu được" in row["evidence"], row


def test_duong_cu_theo_cong_trung_sau_ky_khong_ha_cap():
    """Nơi gọi trực tiếp kiểu cũ (không có ban_ky_theo_vai): phép so theo cổng giữ nguyên, nhưng sau ký chỉ hiển thị."""
    r = _evaluate(cross_gate_refs={"G2": "BS-A", "G4": "BS-A", "G8": "BS-B", "G9": "BS-C"})
    row = _row(r, "G4-HUMAN-03")
    assert row["status"] == "REVIEW" and "TRÙNG" in row["evidence"]
    assert r["status"] == G4Q.STATUS_LOCKED


def test_sua_sap_sau_ky_thi_chi_dau_lai_tham_gia():
    """Sửa SAP sau khi ký ⇒ băm lệch ⇒ ledger_signed=False ⇒ G4-HUMAN-03 lại tham gia (không còn LOCKED)."""
    r = _evaluate(ledger_signed=False, ledger_reason="băm lệch",
                  ban_ky_theo_vai={"G4/STATISTICIAN": "TKV-01", "G4/PI": "PI-01"})
    assert r["status"] != G4Q.STATUS_LOCKED


# ════════════════════════════════════════════════════════════════════════════
# Đầu–cuối — ký thật (khoá GIẢ): ký G4 rồi PI ký G5 cùng mã ⇒ G4 vẫn khoá, G5 không bị chặn vì G4
# ════════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def _khoa_gia(tmp_path, monkeypatch):
    khoa = tmp_path / "gate_approval_key"
    khoa.write_text("khoa-gia-pytest-g4-k3", encoding="utf-8", newline="\n")
    for nhom in ("STATISTICIAN", "PI", "DATA_MANAGER"):
        (tmp_path / f"gate_approval_key_{nhom}").write_text(f"khoa-gia-pytest-k3-{nhom.lower()}", encoding="utf-8",
                                                            newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(khoa))
    return khoa


def _ky(monkeypatch, study: str, cong: str, artifact: Path, vai: str, ref: str) -> tuple[int, str]:
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", "--study", study, "--gate", cong, "--artifact", str(artifact),
                                      "--reviewer-role", vai, "--reviewer-ref", ref])
    CS.xoa_dem()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = AG.main()
    return rc, buf.getvalue()


def _ky_g5_pi(monkeypatch, study: str, d: Path, ref: str) -> tuple[int, str]:
    """PI ký G5 bằng approve_gate THẬT; chỉ thay bộ chấm G5 (hồ sơ dữ liệu không phải đối tượng của test này)."""
    cp = d / "G5_checkpoint.json"
    if not cp.exists():
        cp.write_text('{"gate": "G5"}', encoding="utf-8", newline="\n")
    with monkeypatch.context() as m:
        m.setattr(G5Q, "evaluate_study", lambda *a, **k: {"status": G5Q.STATUS_READY, "automatic_criteria": []})
        return _ky(monkeypatch, study, "G5", cp, "PI", ref)


def _dung_g4_da_ky(monkeypatch, study: str, ref_tkv: str, ref_pi: str) -> tuple[Path, Path]:
    d = ROOT / "exports" / study
    dung_g0_g3_da_chot(d, study)
    sap = sinh_sap_g4_that(d, study)
    text = dien_sap_g4(sap.read_text(encoding="utf-8"))
    sap.write_text(text, encoding="utf-8", newline="\n")
    xac_nhan_g4(d, text)
    rc, out = _ky(monkeypatch, study, "G4", sap, "METHODS_STATISTICS_REVIEWER", ref_tkv)
    assert rc == 0, out
    rc, out = _ky(monkeypatch, study, "G4", sap, "PI", ref_pi)
    assert rc == 0, out
    return d, sap


def _cham_g4(study: str, d: Path) -> dict:
    CS.xoa_dem()
    return G4Q.evaluate_study(study, d, repo_root=ROOT, write=False)


def _g4_ok_theo_g5(study: str, d: Path) -> str:
    """Bằng chứng G5-AUTO-05 (bộ chấm G5 THẬT) — chuỗi «G2=…; G4=…»."""
    CS.xoa_dem()
    r = G5Q.evaluate_study(study, d, repo_root=ROOT, write=False)
    return next(c["evidence"] for c in r["automatic_criteria"] if c["id"] == "G5-AUTO-05")


def test_dau_cuoi_dien_tap_pi_ky_g5_cung_ma_g4_van_khoa(monkeypatch, _khoa_gia):
    study = "PYTEST-G4-K3-DIEN-TAP"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    try:
        d, _sap = _dung_g4_da_ky(monkeypatch, study, "DIEN-TAP-TKV", "DIEN-TAP-PI")
        assert _cham_g4(study, d)["status"] == G4Q.STATUS_LOCKED
        rc, out = _ky_g5_pi(monkeypatch, study, d, "DIEN-TAP-PI")
        assert rc == 0, out
        r = _cham_g4(study, d)
        assert r["status"] == G4Q.STATUS_LOCKED, [c for c in r["approval_criteria"] if c["status"] != "PASS"]
        row = _row(r, "G4-HUMAN-03")
        assert row["status"] == "PASS" and "DIEN-TAP-TKV" in row["evidence"], row
        assert GC.g4_quality_contract_satisfied(study, repo_root=ROOT) is True
        assert "G4=True" in _g4_ok_theo_g5(study, d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
        CS.xoa_dem()


def test_dau_cuoi_bac_si_kiem_moi_vai_ky_g5_g4_van_khoa(monkeypatch, _khoa_gia):
    """Bác sĩ kiêm mọi vai: thống kê viên = PI = cùng một mã. Chỉ dấu REVIEW (hiển thị), nhưng ký G5 sau KHÔNG làm G4
    mất khoá và G5-AUTO-05 thấy G4=True."""
    study = "PYTEST-G4-K3-MOI-VAI"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    try:
        d, _sap = _dung_g4_da_ky(monkeypatch, study, "BS-KIEM-MOI-VAI", "BS-KIEM-MOI-VAI")
        r = _cham_g4(study, d)
        assert r["status"] == G4Q.STATUS_LOCKED, [c for c in r["approval_criteria"] if c["status"] != "PASS"]
        rc, out = _ky_g5_pi(monkeypatch, study, d, "BS-KIEM-MOI-VAI")
        assert rc == 0, out
        r = _cham_g4(study, d)
        assert r["status"] == G4Q.STATUS_LOCKED, [c for c in r["approval_criteria"] if c["status"] != "PASS"]
        row = _row(r, "G4-HUMAN-03")
        assert row["status"] == "REVIEW" and "CHỈ HIỂN THỊ" in row["evidence"], row
        assert "G4/PI" in row["evidence"] and "G5/PI" in row["evidence"], row
        assert GC.g4_quality_contract_satisfied(study, repo_root=ROOT) is True
        assert "G4=True" in _g4_ok_theo_g5(study, d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
        CS.xoa_dem()
