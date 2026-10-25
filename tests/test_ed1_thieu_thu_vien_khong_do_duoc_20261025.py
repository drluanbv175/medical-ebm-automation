#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hồi quy 25/10/2026 — «KHÔNG KIỂM ĐƯỢC chữ ký» không được đọc thành trạng thái cổng.

Bối cảnh: hội đồng G1 của C1a gọi `python3` hệ thống (thiếu thư viện `cryptography`). Mọi chữ ký Ed25519 (ed1) của sổ
cái ra False ⇒ G4 đã ký + khoá bị chấm thành READY_FOR_SIGNATURE kèm «BẤT THƯỜNG — bị sửa sau khi ký», agent ghi
«G4 chưa khoá — còn cửa bổ sung SAP» vào biên bản tranh biện. Vá: (1) hàm xác minh VẪN trả False (fail-closed, không nới
cổng) nhưng ghi sổ «không kiểm được»; (2) `cong_song` thấy sổ đó trong lượt chấm ⇒ «không đo được», nêu cách đo lại;
(3) thông điệp chẩn đoán sổ cái nói đúng nguyên nhân. Ngoại tuyến; thiếu thư viện được giả lập bằng monkeypatch.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402

STUDY = "ED1-THU"


def _ban_ghi_ed1(gate: str = "G4") -> dict:
    return {"gate_id": gate, "decision": "APPROVED", "timestamp_utc": "2026-10-18T02:00:00+00:00",
            "reviewer_role": "STATISTICIAN", "reviewer_identity_reference": "TKV-1", "evidence_hash": "ab" * 32,
            "approver_signature": "ed1:role:" + "cd" * 64}


@pytest.fixture()
def thieu_thu_vien(monkeypatch):
    monkeypatch.setattr(GC, "thu_vien_ed25519_san_co", lambda: False)


def test_thieu_thu_vien_van_fail_closed_va_ghi_so_khong_kiem_duoc(thieu_thu_vien):
    moc = GC.moc_khong_kiem_duoc_ed1()
    assert GC.verify_approval_signature(_ban_ghi_ed1(), STUDY) is False, "không kiểm được KHÔNG BAO GIỜ là đạt"
    assert GC.khong_kiem_duoc_ed1_tu(moc) == ["G4@2026-10-18T02:00:00+00:00"]


def test_co_thu_vien_chu_ky_sai_khong_ghi_so_khong_kiem_duoc():
    if not GC.thu_vien_ed25519_san_co():
        pytest.skip("Python này không có cryptography — ca «có thư viện» chạy trên ~/.ebm-venv và CI")
    moc = GC.moc_khong_kiem_duoc_ed1()
    assert GC.verify_approval_signature(_ban_ghi_ed1(), STUDY) is False
    assert GC.khong_kiem_duoc_ed1_tu(moc) == [], "chữ ký sai khi CÓ thư viện là sai thật, không phải «không kiểm được»"


def _bo_cham_gia(monkeypatch, status: str) -> None:
    """Bộ chấm giả của cổng G99: xác minh một chữ ký ed1 như bộ chấm thật rồi trả `status`."""
    mod = types.ModuleType("g99_quality_gate")

    def evaluate_study(study, out_dir=None, write=True, repo_root=None):
        GC.verify_approval_signature(_ban_ghi_ed1("G99"), study)
        return {"status": status}

    mod.evaluate_study = evaluate_study
    monkeypatch.setitem(sys.modules, "g99_quality_gate", mod)
    CS.xoa_dem()


def test_cham_song_khong_do_duoc_khi_chu_ky_khong_kiem_duoc(tmp_path, monkeypatch, thieu_thu_vien):
    _bo_cham_gia(monkeypatch, "READY_FOR_SIGNATURE")
    kq = CS.trang_thai_song("G99", STUDY, tmp_path)
    assert kq["muc"] == CS.KHONG_DO_DUOC and kq["dat"] is False, kq
    assert "cryptography" in kq["ly_do"] and "READY_FOR_SIGNATURE" in kq["ly_do"], kq["ly_do"]


def test_cham_song_giu_trang_thai_khi_kiem_duoc(tmp_path, monkeypatch):
    if not GC.thu_vien_ed25519_san_co():
        pytest.skip("Python này không có cryptography — ca «có thư viện» chạy trên ~/.ebm-venv và CI")
    _bo_cham_gia(monkeypatch, "READY_FOR_SIGNATURE")
    kq = CS.trang_thai_song("G99", STUDY, tmp_path)
    assert kq["status"] == "READY_FOR_SIGNATURE" and kq["muc"] == "READY", kq


def test_ly_do_ban_ghi_noi_dung_nguyen_nhan(thieu_thu_vien):
    ly_do = GC._ly_do_chu_ky_khong_xac_minh(_ban_ghi_ed1(), "bản ghi #1/1 của G4")
    assert "THIẾU thư viện cryptography" in ly_do and "bị sửa sau khi ký" not in ly_do, ly_do


def test_ly_do_ban_ghi_hmac_van_la_nghi_bi_sua(thieu_thu_vien):
    rec = {**_ban_ghi_ed1(), "approver_signature": "v4:role:" + "ab" * 32}
    assert "bị sửa sau khi ký" in GC._ly_do_chu_ky_khong_xac_minh(rec, "bản ghi #1/1 của G4")
