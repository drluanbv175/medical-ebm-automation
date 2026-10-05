# -*- coding: utf-8 -*-
"""Hoàn thiện cổng G3 (soát từng cổng G0–G10, 04/10/2026) — mỗi test neo vào MỘT phát hiện đã được phản biện xác nhận.

G3-01 NI theo chiều kết cục · G3-02 cụm/FPC đọc cả study_meta, N đã nhân DE · G3-03 xác nhận gắn dấu vân tay, tham số
ghim khớp checkpoint · G3-04 AUC theo Hanley–McNeil 1982 + tỷ lệ hiện mắc · G3-06 bảng độ nhạy neo vào N chính ·
G3-07 nguồn theo thiết kế, câu phủ định không phải nguồn · G3-08 nguồn thật + khung mô tả · G3-09 chạy lại qua
run_pipeline · G3-10 không kẹp im lặng · G3-11 ép kiểu confirmed_n · G1-05 phía G3 (G1 chấm sống). run_g3_auto chạy
THẬT trong thư mục tạm (BASE trỏ sang tmp — không ghi exports/ của repo). Dữ liệu tổng hợp, không mạng.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import g3_quality_gate as G3Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g3_auto as R  # noqa: E402
import run_pipeline as RP  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402


def _chay(tmp_path, monkeypatch, study, thiet_ke, argv, *, meta_g3=None, dung=True, chot_g1=True):
    """Dựng G0→G1 thật (nếu dung) rồi chạy run_g3_auto.main() thật; trả (thư mục, checkpoint, mã thoát, stdout)."""
    monkeypatch.setattr(R, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    if dung:
        dung_g0_g1_da_chot(d, study, thiet_ke=thiet_ke, mau_hieu_qua=[], chot_g1=chot_g1,
                           them_meta={"G3": meta_g3} if meta_g3 else None)
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = R.main()
    cp = json.loads((d / "G3_checkpoint.json").read_text(encoding="utf-8"))
    return d, cp, rc, buf.getvalue()


def _row(r, tid):
    return next(c for c in r["automatic_criteria"] + r["human_criteria"] if c["id"] == tid)


def _q(cp):
    return cp["quality_gate"]


# ── G3-01 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_01_cong_thuc_ni_theo_chieu():
    assert R.n_two_proportion_ni(0.85, 0.65, 0.10, 0.05, 0.80, "higher_better") == 25  # ví dụ HyLown (đáp ứng)
    assert R.n_two_proportion_ni(0.10, 0.08, 0.05, 0.05, 0.80, "lower_better") == 1124  # biến cố bất lợi
    with pytest.raises(R.InvalidEffectSizeError):
        R.n_two_proportion_ni(0.10, 0.08, 0.05, 0.05, 0.80, None)
    with pytest.raises(R.InvalidEffectSizeError):  # vi phạm biên ngay ở giá trị kỳ vọng (biến cố bất lợi)
        R.n_two_proportion_ni(0.15, 0.08, 0.05, 0.05, 0.80, "lower_better")


@pytest.mark.parametrize("raw,ky_vong", [("lower_better", "lower_better"), ("Thấp là tốt", "lower_better"),
                                         ("higher-better", "higher_better"), ("cao là tốt", "higher_better"),
                                         ("giảm", None), ("tăng", None), (None, None)])
def test_g3_01_chuan_hoa_chieu_khong_doan(raw, ky_vong):
    assert R.chuan_hoa_chieu_ket_cuc(raw) == ky_vong


def test_g3_01_ni_bien_co_bat_loi_qua_cli(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-NI", "rct",
                           ["--effect-size", "0.10", "--p0", "0.08", "--hypothesis-type", "non_inferiority",
                            "--margin", "0.05", "--outcome-direction", "lower_better"])
    assert cp["n_per_group"] == 1124 and cp["outcome_direction"] == "lower_better"
    assert cp["effect_type"] == "NI_PROPORTION"
    a4 = (d / "G3_A4_SAMPLE_SIZE_S-NI.md").read_text(encoding="utf-8")
    assert "Chiều kết cục | lower_better" in a4 and "tỷ lệ THẤP là tốt" in a4
    assert "p0 (tỷ lệ kết cục nhóm chứng)" in _row(_q(cp), "G3-AUTO-08")["evidence"], "NI dùng p_control ⇒ cần nguồn"


def test_g3_01_ni_thieu_chieu_bi_chan(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-NI2", "rct",
                           ["--effect-size", "0.10", "--p0", "0.08", "--hypothesis-type", "non_inferiority",
                            "--margin", "0.05"])
    assert rc == GC.EXIT_BLOCKED and cp["n_adjusted"] == 0
    assert "outcome_direction" in json.dumps(cp.get("needs_input", {}), ensure_ascii=False)
    a11 = _row(_q(cp), "G3-AUTO-11")
    assert a11["status"] == "BLOCK" and "CHIỀU kết cục" in a11["evidence"]


# ── G3-02 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_02_cum_khai_trong_study_meta_duoc_ap_de(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-CUM", "rct",
                           ["--effect-size", "5", "--effect-type", "MD", "--sd", "10", "--dropout", "0.1"],
                           meta_g3={"cluster_randomised": True, "icc": 0.05, "cluster_size": 20})
    assert cp["icc"] == 0.05 and cp["cluster_size"] == 20 and abs(cp["design_effect"] - 1.95) < 1e-9
    assert cp["n_total_truoc_de"] == 126 and cp["n_total"] >= 126 * 1.95 - 1 and cp["n_clusters"] == 13
    assert _row(_q(cp), "G3-AUTO-12")["status"] != "BLOCK"


def test_g3_02_gate_chan_khi_n_chua_nhan_de(tmp_path):
    cp = {"design_code": "rct", "n_total": 126, "n_per_group": 63, "n_adjusted": 140, "alpha": 0.05, "power": 0.8,
          "effect_val": 5, "effect_type": "MD", "sd": 10, "dropout": 0.1, "guardrail": "✅ PASS"}
    meta = {"gate_params": {"G3": {"cluster_randomised": True, "icc": 0.05, "cluster_size": 20}}}
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")
    r = G3Q.evaluate_g3_quality(study="S", checkpoint=cp, artifact_path=tmp_path / "A4.md", g0_checkpoint={},
                                g1_checkpoint={"gate": "G1"}, meta=meta)
    a12 = _row(r, "G3-AUTO-12")
    assert a12["status"] == "BLOCK" and "CHƯA nhân hệ số thiết kế" in a12["evidence"]


def test_g3_02_icc_lech_giua_checkpoint_va_meta_la_review(tmp_path):
    cp = {"design_code": "rct", "n_total": 246, "n_total_truoc_de": 126, "design_effect": 1.95, "icc": 0.05,
          "cluster_size": 20, "n_clusters": 13, "guardrail": "✅ PASS"}
    meta = {"gate_params": {"G3": {"icc": 0.02, "cluster_size": 20}}}
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")
    r = G3Q.evaluate_g3_quality(study="S", checkpoint=cp, artifact_path=tmp_path / "A4.md", g0_checkpoint={},
                                g1_checkpoint={"gate": "G1"}, meta=meta)
    assert "ICC lệch" in _row(r, "G3-AUTO-12")["evidence"]


def test_g3_02_fpc_trong_checkpoint_cua_rct_bi_chan(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-FPC", "rct", ["--effect-size", "0.75", "--effect-type", "HR"],
                           meta_g3={"population_n": 3000})
    assert cp["population_n"] == 3000 and rc == GC.EXIT_GUARDRAIL_FAIL
    assert _row(_q(cp), "G3-AUTO-16")["status"] == "BLOCK"


# ── G3-03 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_03_doi_effect_sau_khi_xac_nhan_mat_hieu_luc(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-XN", "rct",
                           ["--effect-size", "5", "--effect-type", "MD", "--sd", "10"])
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G3"].update({"reviewed_by_role": "STATISTICIAN", "reviewed_at": "2026-09-01T09:00:00",
                                      "dau_van_tay_chot": G3Q.dau_van_tay_g3(cp)})
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    assert "xác nhận gắn đúng nội dung hiện tại" in _row(G3Q.evaluate_study("S-XN", d, write=False),
                                                         "G3-HUMAN-06")["evidence"]
    d, cp2, rc, out = _chay(tmp_path, monkeypatch, "S-XN", "rct",
                            ["--effect-size", "8", "--effect-type", "MD", "--sd", "10"], dung=False)
    h6 = _row(_q(cp2), "G3-HUMAN-06")
    assert h6["status"] == "REVIEW" and "đã đổi" in h6["evidence"]
    assert _q(cp2)["status"] != G3Q.STATUS_CONFIRMED
    a18 = _row(_q(cp2), "G3-AUTO-18")
    assert a18["status"] == "REVIEW" and "effect_size" in a18["evidence"], "CLI khác bản ghim phải bị nói ra"


def test_g3_03_gia_thuyet_ghim_duoc_khoi_phuc(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-GT", "rct", ["--effect-size", "0.85", "--p0", "0.65"],
                           meta_g3={"hypothesis_type": "non_inferiority", "margin": 0.10,
                                    "outcome_direction": "higher_better"})
    assert cp["hypothesis_type"] == "non_inferiority" and cp["margin"] == 0.10 and cp["n_per_group"] == 25
    assert cp["nguon_tham_so"]["hypothesis_type"] == "study_meta"


def test_g3_03_gia_thuyet_ghim_lech_checkpoint_bi_chan(tmp_path):
    cp = {"design_code": "rct", "hypothesis_type": "superiority", "guardrail": "✅ PASS"}
    meta = {"gate_params": {"G3": {"hypothesis_type": "non_inferiority"}}}
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")
    r = G3Q.evaluate_g3_quality(study="S", checkpoint=cp, artifact_path=tmp_path / "A4.md", g0_checkpoint={},
                                g1_checkpoint={"gate": "G1"}, meta=meta)
    a18 = _row(r, "G3-AUTO-18")
    assert a18["status"] == "BLOCK" and "non_inferiority" in a18["evidence"]


def test_g3_03_dau_khong_doi_khi_them_khoa_khuon_rong(tmp_path):
    d = tmp_path / "exports" / "S-KHUON"
    dung_g0_g1_da_chot(d, "S-KHUON")
    GC.ensure_study_meta(d, seed={"gate_params": {"G3": {"precision": 0.03}}})
    CS.xoa_dem()
    assert CS.trang_thai_song("G1", "S-KHUON", d)["muc"] == "PASS", "khoá khuôn rỗng không được vô hiệu xác nhận G1"


# ── G3-04 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_04_auc_hanley_mcneil_va_ty_le_hien_mac(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-DG", "diagnostic",
                           ["--effect-size", "0.75", "--effect-type", "AUC", "--prevalence", "0.5"])
    assert (cp["n_benh"], cp["n_khong_benh"], cp["n_total"], cp["n_per_group"]) == (20, 20, 40, 40)
    assert _row(_q(cp), "G3-AUTO-09")["status"] == "PASS"
    assert "PMID 7063747" in cp["formula_used"]


def test_g3_04_chan_doan_thieu_ty_le_hien_mac_la_cho_input(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-DG2", "diagnostic",
                           ["--effect-size", "0.75", "--effect-type", "AUC"])
    assert rc == GC.EXIT_BLOCKED and cp["n_adjusted"] == 0
    assert "prevalence" in json.dumps(cp["needs_input"], ensure_ascii=False)


def test_g3_04_chan_doan_khong_nhan_loai_khac_auc():
    with pytest.raises(R.InvalidEffectSizeError):
        R.tinh_n_loi("diagnostic", "OR", 2.0, 0.05, 0.8, prevalence=0.3)


# ── G3-06 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("study,thiet_ke,argv", [
    ("S-HR", "rct", ["--effect-size", "0.75", "--effect-type", "HR"]),
    ("S-ARR", "rct", ["--effect-size", "5", "--effect-type", "ARR%", "--p0", "0.08"]),
    ("S-MDCUM", "rct", ["--effect-size", "5", "--effect-type", "MD", "--sd", "10", "--icc", "0.05",
                        "--cluster-size", "20"]),
    ("S-CS03", "cross_sectional", ["--precision", "0.03"]),
    ("S-CSFPC", "cross_sectional", ["--population-n", "2000"]),
    ("S-NIB", "rct", ["--effect-size", "0.85", "--p0", "0.65", "--hypothesis-type", "non_inferiority",
                      "--margin", "0.10", "--outcome-direction", "higher_better"]),
])
def test_g3_06_bang_do_nhay_neo_vao_n_chinh(tmp_path, monkeypatch, study, thiet_ke, argv):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, study, thiet_ke, argv)
    a9 = _row(_q(cp), "G3-AUTO-09")
    assert a9["status"] == "PASS", a9
    if thiet_ke == "cross_sectional":
        assert cp["n_per_group"] == cp["n_total"], "thiết kế một nhóm: n_per_group = n_total (cả sau FPC)"


# ── G3-07 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cau", ["chưa có pilot", "Không có MCID cho thang này", "Không áp dụng theo thiết kế",
                                 "n/a"])
def test_g3_07_cau_phu_dinh_khong_phai_nguon(cau):
    assert G3Q.source_kind(cau) is None


def test_g3_07_nguon_co_pmid_van_nhan_du_co_chu_khong():
    assert G3Q.source_kind("PMID: 12345678 (không có dữ liệu châu Á)") == "PMID"


def _cham(tmp_path, cp, g3):
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")
    return G3Q.evaluate_g3_quality(study="S", checkpoint=cp, artifact_path=tmp_path / "A4.md", g0_checkpoint={},
                                   g1_checkpoint={"gate": "G1"}, meta={"gate_params": {"G3": g3}})


def test_g3_07_human_01_theo_thiet_ke(tmp_path):
    co = {"effect_source_confirmed": True}
    mo_ta = {"design_code": "cross_sectional", "effect_type": "PREVALENCE", "effect_val": 0.5, "guardrail": "✅ PASS"}
    assert _row(_cham(tmp_path, mo_ta, {**co, "prevalence_source": "Khảo sát cơ sở 2025"}), "G3-HUMAN-01")["status"] \
        == "PASS"
    dinh_tinh = {"design_code": "qualitative", "confirmed_n": 20, "guardrail": "✅ PASS"}
    assert _row(_cham(tmp_path, dinh_tinh, {**co, "confirmed_n_method": "Bão hòa dữ liệu"}), "G3-HUMAN-01")[
        "status"] == "PASS"
    ni = {"design_code": "rct", "effect_type": "NI_PROPORTION", "effect_val": 0.85,
          "hypothesis_type": "non_inferiority",
          "margin": 0.1, "guardrail": "✅ PASS"}
    assert _row(_cham(tmp_path, ni, {**co, "margin_source": "PMID: 30560792"}), "G3-HUMAN-01")["status"] == "REVIEW"
    assert _row(_cham(tmp_path, ni, {**co, "margin_source": "PMID: 30560792", "p0_source": "Sổ khoa 2024"}),
                "G3-HUMAN-01")["status"] == "PASS"
    assert _row(_cham(tmp_path, ni, {}), "G3-AUTO-03")["status"] == "PASS", "NI_PROPORTION hợp lệ cho NI trên rct"


# ── G3-08 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_08_a4_mo_ta_khong_gan_nguon_sai_va_khong_khung_kiem_dinh(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-A4", "cross_sectional", [])
    a4 = (d / "G3_A4_SAMPLE_SIZE_S-A4.md").read_text(encoding="utf-8")
    assert "Trích từ y văn G0" not in a4 and "mặc định quy ước p=0,5" in a4
    khoi = a4.split("## PHẦN 4")[1].split("```")[1]
    assert "lực thống kê" not in khoi and "mỗi nhóm" not in khoi and "385" in khoi
    assert "Lực thống kê (1−β)" not in a4.split("## PHẦN 2")[0]
    assert cp["hypothesis_type"] == "descriptive_precision" and rc == GC.EXIT_OK
    assert _row(_q(cp), "G3-AUTO-11")["status"] == "PASS", "ước lượng theo độ chính xác KHÔNG phải non-inferiority"


def test_g3_08_cat_ngang_khong_muon_hieu_ung_g1(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "BASE", tmp_path)
    d = tmp_path / "exports" / "S-RR"
    dung_g0_g1_da_chot(d, "S-RR", thiet_ke="cross_sectional")  # G1 có mẫu RR 0,80
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-RR", "cross_sectional", [], dung=False)
    assert cp["effect_type"] == "PREVALENCE" and cp["effect_val"] == 0.5 and cp["n_total"] == 385


# ── G3-09 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_09_nhan_effect_type_prevalence(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-PREV", "cross_sectional",
                           ["--effect-type", "PREVALENCE", "--effect-size", "0.3"])
    assert cp["effect_type"] == "PREVALENCE" and cp["effect_val"] == 0.3 and rc == GC.EXIT_OK


def test_g3_09_run_pipeline_khoi_phuc_du_tham_so(tmp_path):
    (tmp_path / "G3_checkpoint.json").write_text(json.dumps({
        "effect_val": 0.85, "effect_type": "p_test", "hypothesis_type": "non_inferiority", "margin": 0.1,
        "outcome_direction": "lower_better", "precision": None, "icc": 0.02, "cluster_size": 15}), encoding="utf-8",
        newline="\n")
    args = RP._recover_params("G3", tmp_path, {"gate_params": {"G3": {"prevalence": 0.4}}})
    assert "--effect-type" not in args
    for co in ("--hypothesis-type", "--margin", "--outcome-direction", "--icc", "--cluster-size", "--prevalence"):
        assert co in args, co
    assert "--precision" not in args


def test_g3_09_loi_doi_so_khong_doc_thanh_cho_input(tmp_path, monkeypatch):
    monkeypatch.setattr(RP, "_build_cmd", lambda *a, **k: ["x"])
    monkeypatch.setattr(RP, "_run_gate_once", lambda cmd, out: {
        "exit_code": GC.EXIT_BLOCKED, "stdout_tail": "", "stderr_tail": "usage: run_g3_auto.py\nerror: argument --x"})
    r = RP.run_gate_with_healing("G3", "S", tmp_path, None, {}, 1)
    assert r["status"] == "failed" and "ĐỐI SỐ SAI" in r["detail"]
    monkeypatch.setattr(RP, "_run_gate_once", lambda cmd, out: {
        "exit_code": GC.EXIT_BLOCKED, "stdout_tail": "chờ input", "stderr_tail": ""})
    assert RP.run_gate_with_healing("G3", "S", tmp_path, None, {}, 1)["status"] == "blocked_missing_input"


# ── G3-10 / G3-11 ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_g3_10_khong_kep_im_lang():
    with pytest.raises(R.InvalidEffectSizeError):
        R.tinh_n_loi("rct", "RR", 4.0, 0.05, 0.8, p0=0.3)
    with pytest.raises(R.InvalidEffectSizeError):
        R.tinh_n_loi("rct", "ARR%", 40, 0.05, 0.8, p0=0.3)
    with pytest.raises(R.InvalidEffectSizeError):
        R.tinh_n_loi("cross_sectional", "PREVALENCE", 1.2, 0.05, 0.8)


@pytest.mark.parametrize("gia_tri,ky_vong", [("300", 300), (300, 300), ("<CẦN BÁC SĨ CẤP>", None)])
def test_g3_11_confirmed_n_ep_kieu(tmp_path, monkeypatch, gia_tri, ky_vong):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, f"S-CN{ky_vong}", "cross_sectional", [],
                           meta_g3={"confirmed_n": gia_tri})
    assert cp["confirmed_n"] == ky_vong


# ── G1-05 phía G3: tiền đề G1 chấm sống ────────────────────────────────────────────────────────────────────────────
def test_g1_05_g1_chua_chot_thi_g3_review(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-G1N", "rct", ["--effect-size", "0.75", "--effect-type", "HR"],
                           chot_g1=False)
    a1 = _row(_q(cp), "G3-AUTO-01")
    assert a1["status"] == "REVIEW" and "chấm sống" in a1["evidence"]


def test_g1_05_g1_bi_chan_thi_g3_chan(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "BASE", tmp_path)
    d = tmp_path / "exports" / "S-G1B"
    dung_g0_g1_da_chot(d, "S-G1B", mau_hieu_qua=[])
    cp1 = json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))
    cp1["design"]["pin_bi_tu_choi"] = "quality_improvement"
    (d / "G1_checkpoint.json").write_text(json.dumps(cp1, ensure_ascii=False), encoding="utf-8", newline="\n")
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-G1B", "rct", ["--effect-size", "0.75", "--effect-type", "HR"],
                           dung=False)
    a1 = _row(_q(cp), "G3-AUTO-01")
    assert a1["status"] == "BLOCK" and "quality_improvement" in a1["evidence"] and rc == GC.EXIT_GUARDRAIL_FAIL


def test_human_04_ket_cuc_chinh_co_cau_truc_so_theo_ten(tmp_path):
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")
    meta = {"gate_params": {"G1": {"primary_outcome": {"name": "Điểm Y", "measure": "thang", "timepoint": "12 tuần"}},
                            "G3": {"powered_for_outcome": "Điểm Y"}}}
    r = G3Q.evaluate_g3_quality(study="S", checkpoint={"design_code": "rct", "guardrail": "✅ PASS"},
                                artifact_path=tmp_path / "A4.md", g0_checkpoint={}, g1_checkpoint={"gate": "G1"},
                                meta=meta)
    assert _row(r, "G3-HUMAN-04")["status"] == "PASS"


def test_khuon_khong_gieo_gia_tri_ngoai_co_xac_nhan():
    """Khoá khuôn có giá trị KHÁC rỗng chỉ được là cờ xác nhận (bị loại khỏi dấu vân tay) — mọi giá trị gieo khác sẽ đổi
    dấu vân tay của cổng khi ensure_study_meta điền khoá còn thiếu."""
    for gate, khuon in GC._GATE_PARAMS_SKELETON.items():
        for khoa, gia_tri in khuon.items():
            if not CS._rong(CS._chuan_tac(gia_tri)):
                assert gia_tri is False and (khoa.endswith(("_confirmed", "_reviewed", "_requested"))), (gate, khoa)



def test_g3_02_cum_chi_qua_cli_van_duoc_nhan(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-CUMCLI", "rct",
                           ["--effect-size", "5", "--effect-type", "MD", "--sd", "10", "--icc", "0.05",
                            "--cluster-size", "20"])
    a12 = _row(_q(cp), "G3-AUTO-12")
    assert "không khai thiết kế theo chùm" not in a12["evidence"], a12


def test_g3_02_n_nho_hon_n_truoc_de_nhan_de_bi_chan(tmp_path):
    cp = {"design_code": "rct", "n_total": 200, "n_total_truoc_de": 126, "design_effect": 1.95, "icc": 0.05,
          "cluster_size": 20, "guardrail": "✅ PASS"}
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")
    r = G3Q.evaluate_g3_quality(study="S", checkpoint=cp, artifact_path=tmp_path / "A4.md", g0_checkpoint={},
                                g1_checkpoint={"gate": "G1"}, meta={})
    a12 = _row(r, "G3-AUTO-12")
    assert a12["status"] == "BLOCK" and "N trước DE" in a12["evidence"]


def test_g3_04_ty_le_hien_mac_vao_phep_tinh(tmp_path, monkeypatch):
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-DG20", "diagnostic",
                           ["--effect-size", "0.75", "--effect-type", "AUC", "--prevalence", "0.2"])
    assert (cp["n_benh"], cp["n_khong_benh"], cp["n_total"]) == (13, 52, 65)


def test_g3_03_dau_gom_ca_gia_tri_effect_khi_n_khong_doi(tmp_path, monkeypatch):
    """HR 0,75 (bảo vệ) và HR 1,333 (có hại) cho CÙNG một N — xác nhận cho chiều này không được mang sang chiều kia."""
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-HRD", "rct", ["--effect-size", "0.75", "--effect-type", "HR"])
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G3"].update({"reviewed_by_role": "PI", "reviewed_at": "2026-09-01T09:00:00",
                                      "dau_van_tay_chot": G3Q.dau_van_tay_g3(cp)})
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    d, cp2, rc, out = _chay(tmp_path, monkeypatch, "S-HRD", "rct",
                            ["--effect-size", str(1 / 0.75), "--effect-type", "HR"], dung=False)
    assert cp2["n_adjusted"] == cp["n_adjusted"]
    assert _row(_q(cp2), "G3-HUMAN-06")["status"] == "REVIEW"


def test_g3_chay_lai_chi_voi_study_khong_troi_tham_so(tmp_path, monkeypatch):
    """Đo trên C1a (04/10/2026): chạy lại chỉ với --study từng đưa tỷ lệ bỏ cuộc 15% về mặc định 20% (N đổi lặng lẽ)."""
    d, cp, rc, out = _chay(tmp_path, monkeypatch, "S-TROI", "rct",
                           ["--effect-size", "0.75", "--effect-type", "HR", "--dropout", "0.15", "--p-event", "0.4",
                            "--power", "0.9"])
    d, cp2, rc, out = _chay(tmp_path, monkeypatch, "S-TROI", "rct", [], dung=False)
    assert (cp2["dropout"], cp2["p_event"], cp2["power"]) == (0.15, 0.4, 0.9)
    assert cp2["n_adjusted"] == cp["n_adjusted"] and cp2["nguon_tham_so"]["dropout"] == "study_meta"
    # Đề tài cũ (như C1a) chưa ghim các tham số này: lấy từ checkpoint lượt trước, không về mặc định.
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    for k in ("dropout", "p_event", "power"):
        meta["gate_params"]["G3"].pop(k, None)
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    d, cp3, rc, out = _chay(tmp_path, monkeypatch, "S-TROI", "rct", [], dung=False)
    assert (cp3["dropout"], cp3["p_event"], cp3["power"]) == (0.15, 0.4, 0.9)
    assert cp3["nguon_tham_so"]["dropout"] == "checkpoint lượt trước"
