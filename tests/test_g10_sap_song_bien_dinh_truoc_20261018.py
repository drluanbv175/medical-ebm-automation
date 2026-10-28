# -*- coding: utf-8 -*-
"""Gói G10 lấy SAP từ NGUỒN SỐNG + mục Biến số của gói trước dữ liệu — 18/10/2026 (tranh biện hội đồng G10 C1a,
G10-TB-20261018T074752-4af4efab, việc sửa 1–3).

Lỗi đã đo trên C1a: đề cương thống nhất in «SAP 1.0 — PENDING — CHỜ BÁC SĨ KÝ SAP» (trường thô run_g4_auto ghi cứng
vào G4_checkpoint) trong khi SAP 1.3 đã khoá và chấm sống G4 là PASS_G4_SAP_LOCKED; mục 8 in «0 biến, chuyên khoa
nhận diện = `generic`» vì gói trình Hội đồng chưa có G5. Test chốt:
① `RS.sap_song` đọc phiên bản từ tiêu đề SAP và trạng thái từ chấm sống G4; không đọc được ⇒ None (không đoán);
② StudySpec dùng `sap` khi có, không rơi về trường thô; người gọi cũ (không truyền `sap`) giữ hành vi cũ;
③ mục SAP / ma trận / kiểm soát phiên bản chỉ ghi «đã khoá» khi chấm sống G4 khoá, KHÔNG BAO GIỜ in trường thô;
④ mục 8 của gói chưa có G5 in số biến định trước;
⑤ G10-AUTO-06 tính lại StudySpec cùng nguồn sống ⇒ không báo lệch giả sau khi lắp.
Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402

THO = "PENDING — CHỜ BÁC SĨ KÝ SAP"
KHOA = {"sap_version": "1.3", "sap_status": RS.SAP_LOCKED_STATUS, "sap_locked": True}


def _gia_song(monkeypatch, status):
    monkeypatch.setattr(CS, "trang_thai_song", lambda gate, study, out_dir, repo_root=None: {"status": status})


def test_sap_song_doc_tieu_de_va_cham_song(tmp_path, monkeypatch):
    _gia_song(monkeypatch, RS.SAP_LOCKED_STATUS)
    assert RS.sap_song("X", tmp_path) == {"sap_version": None, "sap_status": RS.SAP_LOCKED_STATUS, "sap_locked": True}
    (tmp_path / "G4_A5_SAP_FINAL_X.md").write_text("# A5\n**Mã:** X | **Phiên bản SAP:** 1.3 | **Cập nhật:** 2026\n",
                                                  encoding="utf-8", newline="\n")
    assert RS.sap_song("X", tmp_path)["sap_version"] == "1.3"
    _gia_song(monkeypatch, "READY_FOR_SIGNATURE")
    assert RS.sap_song("X", tmp_path)["sap_locked"] is False


def test_study_spec_dung_sap_song_khong_roi_ve_truong_tho():
    cps = {"G4": {"g4_sap_version": "1.0", "g4_status": THO}}
    spec = RS.build_study_spec("X", cps, {}, sap=KHOA)
    assert (spec["analysis"]["sap_version"], spec["analysis"]["sap_status"]) == ("1.3", RS.SAP_LOCKED_STATUS)
    spec_rong = RS.build_study_spec("X", cps, {}, sap={"sap_version": None, "sap_status": None, "sap_locked": False})
    assert spec_rong["analysis"]["sap_version"] != "1.0" and spec_rong["analysis"]["sap_status"] != THO
    assert RS.build_study_spec("X", cps, {})["analysis"]["sap_version"] == "1.0", "người gọi cũ giữ hành vi cũ"


def test_muc_sap_ma_tran_va_kiem_soat_khong_in_truong_tho():
    cps = {f"G{i}": {} for i in range(10)}
    cps["G1"] = {"design": {"internal_code": "cross_sectional"}}
    cps["G4"] = {"g4_sap_version": "1.0", "g4_status": THO}
    meta = {"_g10": {"sap": KHOA}}
    for van_ban in (G10.sec_sap(cps, meta), G10.build_traceability_matrix(cps, meta),
                    G10.build_document_control("X", cps, meta), G10.sec_dukien_ketqua(cps, meta)):
        assert THO not in van_ban and "1.3" in van_ban
    assert "đã khoá (chấm sống G4: PASS_G4_SAP_LOCKED)" in G10.sec_sap(cps, meta)
    cho = {"_g10": {"sap": {"sap_version": "1.3", "sap_status": "READY_FOR_SIGNATURE", "sap_locked": False}}}
    assert "chưa khoá (chấm sống G4: READY_FOR_SIGNATURE)" in G10.sec_sap(cps, cho)
    assert "đã khoá" not in G10.sec_sap(cps, cho)
    assert G10._sap_hien_thi({}) == (G10.TAG_BS, G10.TAG_BS), "không có ngữ cảnh lắp ráp ⇒ nhãn chờ, không đoán"


def test_muc_bien_so_goi_truoc_du_lieu_in_bien_dinh_truoc():
    cps = {f"G{i}": {} for i in range(10)}
    van_ban = G10.sec_bienso(cps, {"variables": ["a", "b", "c"]})
    assert "**Biến định trước:** 3 biến (study_meta.variables)" in van_ban and "0 biến" not in van_ban
    assert "0 biến" in G10.sec_bienso(cps, {}), "không có biến định trước thì giữ dòng cũ"
    cps["G5"] = {"crf_columns": ["x", "y"], "redcap_rows": 2, "specialty": "khac"}
    assert "**Bộ biến số CRF/REDCap (tự động từ G5):** 2 biến" in G10.sec_bienso(cps, {"variables": ["a"]})


def test_g10_auto06_tinh_lai_cung_nguon_song_khong_lech_gia(tmp_path):
    _write_cross_sectional_fixture(tmp_path)
    G10.assemble("FIXT", tmp_path)
    luu = json.loads((tmp_path / "STUDY_SPEC_FIXT.json").read_text(encoding="utf-8"))
    assert luu["analysis"]["sap_status"] != "PENDING", "StudySpec đã lắp không mang trường thô của checkpoint"
    _danh_gia, lech = G10Q._study_spec_song("FIXT", tmp_path)
    assert lech is None, lech


def test_muc13_khong_in_phien_ban_tho_cua_checkpoint():
    """SỬA 28/10/2026 (G10-DG-20261028T211135-9a0c2aba, RQ4): mục 13 từng in «SAP phiên bản 1.0» (trường thô) khi SAP
    1.4 đã khoá. Không có ngữ cảnh lắp ráp ⇒ không in số phiên bản nào (không đoán, không rơi về trường thô)."""
    cps = {f"G{i}": {} for i in range(10)}
    cps["G1"] = {"design": {"internal_code": "cross_sectional"}}
    cps["G4"] = {"g4_sap_version": "1.0", "g4_status": THO}
    meta = {"_g10": {"sap": {"sap_version": "1.4", "sap_status": RS.SAP_LOCKED_STATUS, "sap_locked": True}}}
    assert "SAP phiên bản 1.4 §11 DUMMY TABLES" in G10.sec_dukien_ketqua(cps, meta)
    van_ban = G10.sec_dukien_ketqua(cps, {})
    assert "SAP phiên bản" not in van_ban and "SAP §11 DUMMY TABLES (sinh ở G4)" in van_ban
