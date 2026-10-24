# -*- coding: utf-8 -*-
"""Diễn tập G5 cho C1a (24/10/2026) — hai lỗi máy lộ khi đi tiếp ĐÚNG thứ tự sau khi PI khoá gói trình Hội đồng.

1. G10: gói ETHICS_SUBMISSION chỉ dựa G0–G4, nhưng StudySpec tính lại (G10-AUTO-06) đếm MỌI checkpoint có trên đĩa trong
   `provenance.checkpoints` ⇒ chạy run_g5_auto.py (sinh từ điển REDCap sau khi G4 ký, đúng checklist) làm G10 đang
   PASS_G10_RELEASE_PACKAGE_LOCKED tụt BLOCKED. Vá: lắp và chấm lại cùng dựng StudySpec từ cổng của mục đích
   (g10_quality_gate.checkpoint_theo_muc_dich).
2. G5: DMP/lưu đồ in «N dự kiến: 808» (N tối thiểu theo thống kê) trong khi SAP đã ký ghi N hiệu lực = confirmed_n
   (1000) — cùng lớp lỗi đã vá ở G4 ngày 31/07/2026. Lưu đồ cắt ngang một mẫu từng in «KHÔNG PHƠI NHIỄM N ≈ 0».
Dữ liệu tổng hợp, không PII, không gọi mạng; luồng có ký chạy với khoá giả tạm của pytest.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g10_quality_gate as G10Q  # noqa: E402
import run_g5_auto as G5A  # noqa: E402

from tests.test_g5_relock_overwrite_guard import _configure_test_signing_key, _run_g5, _sign, _study_dir  # noqa: E402
from tests.test_g8_hoan_thien_20261004 import _ghi  # noqa: E402
from tests.test_g10_hoan_thien_20261005 import (  # noqa: E402
    _cham10,
    _chua_dat,
    _ck,
    _de_tai_truoc_irb,
    _ky_g10,
    _lap_g10,
)


def _ghi_g5_checkpoint(out: Path, study: str) -> None:
    """Checkpoint G5 như run_g5_auto.py vừa sinh bộ công cụ (chưa có dữ liệu)."""
    _ghi(out / "G5_checkpoint.json", json.dumps({
        "gate": "G5", "study": study, "g5_status": "PENDING", "design_code": "cohort",
        "crf_columns": ["record_id", "primary_outcome"],
    }, ensure_ascii=False, indent=2))


# ── 1. G10: gói trước dữ liệu đã khoá không vỡ vì G5 ─────────────────────────────────────────────────────────────────

def test_goi_truoc_du_lieu_da_khoa_khong_vo_khi_sinh_bo_cong_cu_g5(tmp_path, monkeypatch):
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    bao = _cham10(study, out, goc, write=True)
    assert bao["status"] == G10Q.STATUS_READY, _chua_dat(bao)
    _ky_g10(study, out, goc)
    assert _cham10(study, out, goc)["status"] == G10Q.STATUS_LOCKED
    _ghi_g5_checkpoint(out, study)
    bao = _cham10(study, out, goc)
    assert _ck(bao, "G10-AUTO-06")["status"] == "PASS", _ck(bao, "G10-AUTO-06")
    assert bao["status"] == G10Q.STATUS_LOCKED, _chua_dat(bao)


def test_lap_goi_truoc_du_lieu_khi_da_co_g5_thi_studyspec_chi_dua_g0_g4(tmp_path, monkeypatch):
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    _ghi_g5_checkpoint(out, study)
    _lap_g10(goc, study, monkeypatch)
    spec = json.loads((out / f"STUDY_SPEC_{study}.json").read_text(encoding="utf-8"))
    assert spec["provenance"]["checkpoints"] == ["G0", "G1", "G2", "G3", "G4"], spec["provenance"]
    assert _ck(_cham10(study, out, goc), "G10-AUTO-06")["status"] == "PASS"


def test_checkpoint_theo_muc_dich():
    cps = {f"G{i}": {"gate": f"G{i}"} for i in range(10)}
    truoc = G10Q.checkpoint_theo_muc_dich(cps, "ETHICS_SUBMISSION")
    assert [g for g, v in truoc.items() if v] == ["G0", "G1", "G2", "G3", "G4"]
    assert set(truoc) == set(cps)
    for muc_dich in ("JOURNAL_SUBMISSION", None):
        assert G10Q.checkpoint_theo_muc_dich(cps, muc_dich) == cps


# ── 2. G5: N hiệu lực = confirmed_n; lưu đồ một mẫu không in số chia nhóm do máy tính ─────────────────────────────────

def _de_tai_g5_cat_ngang(tmp_path: Path, monkeypatch, study: str, g3_them: dict) -> Path:
    """G1/G3 cắt ngang một mẫu kiểu C1a + G4 ký bằng khoá giả tạm (run_g5_auto đòi G4 đã ký)."""
    d = _study_dir(tmp_path, study)
    _configure_test_signing_key(tmp_path, monkeypatch)
    _ghi(d / "G0_checkpoint.json", json.dumps({"gate": "G0", "topic": "Hài lòng người bệnh ngoại trú"}))
    _ghi(d / "G1_checkpoint.json", json.dumps({"gate": "G1", "design": {"internal_code": "cross_sectional"}}))
    _ghi(d / "G3_checkpoint.json", json.dumps({
        "gate": "G3", "design_code": "cross_sectional", "n_adjusted": 808, "n_total": 686, "n_per_group": 686,
        **g3_them}))
    sap = d / f"G4_A5_SAP_FINAL_{study}.md"
    sap.write_text("SAP FINAL — nội dung đã khoá (giả lập test)", encoding="utf-8", newline="\n")
    _sign(d, "G4", sap, "METHODS_STATISTICS_REVIEWER", tmp_path)
    return d


def test_g5_dung_n_hieu_luc_confirmed_n_nhu_sap(tmp_path, monkeypatch, capsys):
    study = "PYTEST-G5-NHIEU-LUC"
    d = _de_tai_g5_cat_ngang(tmp_path, monkeypatch, study, {"confirmed_n": 1000})
    _run_g5(study, tmp_path, monkeypatch, capsys)
    dmp = (d / f"G5_A6_DATA_MGMT_{study}.md").read_text(encoding="utf-8")
    assert "**N dự kiến:** 1000 (cỡ mẫu kế hoạch, G3 confirmed_n; tối thiểu theo thống kê 808)" in dmp
    assert "N = 1000 (cỡ mẫu kế hoạch, tối thiểu theo thống kê 808)" in dmp
    assert "N dự kiến:** 808" not in dmp and "N = 808" not in dmp


def test_g5_khong_co_confirmed_n_giu_n_dieu_chinh_va_luu_do_mot_mau_khong_chia_nhom(tmp_path, monkeypatch, capsys):
    study = "PYTEST-G5-MOT-MAU"
    d = _de_tai_g5_cat_ngang(tmp_path, monkeypatch, study, {})
    _run_g5(study, tmp_path, monkeypatch, capsys)
    dmp = (d / f"G5_A6_DATA_MGMT_{study}.md").read_text(encoding="utf-8")
    assert "**N dự kiến:** 808  " in dmp and "N = 808 (N dự kiến + 20% dự phòng)" in dmp
    assert "N ≈ 0" not in dmp and "N ≈ 686" not in dmp
    assert dmp.count("N ≈ [CẦN]") == 2
    assert "Phân tích chính: N = [CẦN — sau loại trừ] (cần tối thiểu 686 theo G3)" in dmp


def test_luu_do_hai_nhom_van_in_so_chia_nhom_cua_g3():
    lu = G5A.build_strobe_flowchart("S", "cohort", 400, 360, 180)
    assert "N ≈ 180" in lu and "N ≈ [CẦN]" not in lu and "N = 400 (N dự kiến + 20% dự phòng)" in lu


# ── 3. Trách nhiệm cổng: chuỗi dữ liệu G5 chưa tới lượt khi G2/G4 chưa vào sổ cái (G5-AUTO-05) ──────────────────────

import cong_song as CS  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import skill_standards as SK  # noqa: E402

_CHUOI_DU_LIEU = ("G5-AUTO-06", "G5-AUTO-07", "G5-AUTO-08", "G5-AUTO-09")


def _trach_nhiem_g5(monkeypatch, tmp_path: Path, hang: dict) -> dict:
    """G5 chấm sống DRAFT với các tiêu chí `hang`; bộ công cụ G5 đã sinh (chỉ còn thiếu DATA_LOCK_manifest)."""
    study = "G5-CHUA-TOI-LUOT"
    out = tmp_path / "exports" / study
    out.mkdir(parents=True)
    for ten in (f"G5_A6_DATA_MGMT_{study}.md", f"G5_REDCap_dictionary_{study}.csv", "G5_checkpoint.json"):
        (out / ten).write_text("x", encoding="utf-8", newline="\n")

    def gia(gate, study_, out_dir, repo_root=None):
        return {"status": "DRAFT_READY_NEEDS_REAL_DATA", "nguon": "song",
                "bao_cao": {"automatic_criteria": [{"id": k, "status": v, "action": f"việc {k}"}
                                                   for k, v in hang.items()]}}
    monkeypatch.setattr(CS, "trang_thai_song", gia)
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": "cross_sectional"})
    return HD.trach_nhiem(study, "G5", out)


def test_chuoi_du_lieu_g5_cho_cong_truoc_khi_g2_chua_vao_so_cai(monkeypatch, tmp_path):
    kq = _trach_nhiem_g5(monkeypatch, tmp_path, {"G5-AUTO-01": "PASS", "G5-AUTO-05": "REVIEW",
                                                 **{m: "REVIEW" for m in _CHUOI_DU_LIEU}})
    assert kq["ket_luan"] == "CHO_CONG_TRUOC", kq["agent_con_viec"]
    assert not kq["agent_con_viec"]
    cho = {m["id"]: m for m in kq["cho_cong_truoc"]}
    assert set(_CHUOI_DU_LIEU) | {"G5-AUTO-05", "G5-T1:dau-ra"} == set(cho)
    assert all(cho[m]["chua_toi_luot_vi"] == "G5-AUTO-05" and cho[m]["cong"] == ["G2", "G4"]
               for m in (*_CHUOI_DU_LIEU, "G5-T1:dau-ra"))


def test_chuoi_du_lieu_g5_tro_lai_viec_agent_khi_g2_g4_da_vao_so_cai(monkeypatch, tmp_path):
    kq = _trach_nhiem_g5(monkeypatch, tmp_path, {"G5-AUTO-05": "PASS", **{m: "REVIEW" for m in _CHUOI_DU_LIEU}})
    assert kq["ket_luan"] == "AGENT_CON_VIEC"
    assert {m["id"] for m in kq["agent_con_viec"]} == set(_CHUOI_DU_LIEU) | {"G5-T1:dau-ra"}
    assert not kq["cho_cong_truoc"]


def test_viec_bo_cong_cu_g5_khong_phu_thuoc_g2_van_la_viec_agent(monkeypatch, tmp_path):
    kq = _trach_nhiem_g5(monkeypatch, tmp_path, {"G5-AUTO-01": "REVIEW", "G5-AUTO-05": "REVIEW"})
    assert kq["ket_luan"] == "AGENT_CON_VIEC" and "G5-AUTO-01" in {m["id"] for m in kq["agent_con_viec"]}


def test_bang_chi_sau_tieu_chi_tro_tieu_chi_va_dau_ra_co_that():
    for gate, bang in HD.CHI_SAU_TIEU_CHI.items():
        dau_ra = {d for nv in HD.NHIEM_VU.get(gate, []) for d in nv["dau_ra"]}
        for khoa, goc in bang.items():
            assert khoa in HD.PHAN_CONG[gate] or khoa in dau_ra, khoa
            assert HD.PHAN_CONG[gate][goc].startswith("^"), f"{goc} phải là tiêu chí tiền đề cổng trước"
