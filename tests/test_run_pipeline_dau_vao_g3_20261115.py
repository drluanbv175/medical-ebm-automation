# -*- coding: utf-8 -*-
"""N4 (giả lập lần 2, 14/11/2026) — run_pipeline nhận ra khi PI đổi gate_params.G3 (dấu vân tay ĐẦU VÀO của G3).

Đo được ở lượt a09 của giả lập RCT lần 2 (BAO-CAO-GIA-LAP-CHI-TIET-20261114.md, N4): PI điền gate_params.G3 có nguồn
(effect size RR 1,4583 · p0 0,48 · bỏ cuộc 20 %) rồi chạy run_pipeline thường ⇒ «G3: đã tươi, bỏ qua», N giữ mặc định
máy (1323) cho tới khi PI tự chạy run_g3_auto — can thiệp duy nhất «do máy» của Phần A. Bảng mtime chỉ nhìn checkpoint,
không nhìn study_meta. Nay so NỘI DUNG như K5 làm cho G0: giá trị PI khai ↔ giá trị G3 đã dùng (G3_checkpoint).

Ba lớp phép thử:
  • Bộ so (`_g3_lech_dau_vao_chi_tiet`) trên checkpoint dựng tay — từng nhóm luật + những chỗ PHẢI im (ô mẫu, gỡ ghim,
    tham số G3 không dùng ở thiết kế đó) để không chạy lại G3 vô cớ.
  • orchestrate với cổng GIẢ — G3 chạy lại, dây chuyền sau G3 thành «cũ», rào cổng ĐÃ KÝ giữ nguyên, chống lặp khi G3
    không áp được giá trị ghim, check-only/--from.
  • HỘI TỤ với run_g3_auto THẬT — chạy G3 đúng đường pipeline (`_recover_params`) rồi bộ so phải về [] và đứng yên ở
    lượt sau; qua orchestrate thật: lượt 1 chạy lại G3, lượt 2 «đã tươi».
Thư mục tạm, dữ liệu tổng hợp, không PII, không mạng, không ký gì, không đụng exports/ thật. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g3_auto as R3  # noqa: E402
import run_pipeline as RP  # noqa: E402
from _chuoi_da_chot import EFFECTS, chay_g3_that, dung_g0_g1_da_chot  # noqa: E402

STUDY = "ZZTEST-PIPE-DAU-VAO-G3"


# ───────────────────────────────────────────────────────────────────────────────────────────── đồ gá
def _ghi(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _doc(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _thu_muc(tmp_path: Path) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    return out


def _cp(out: Path, gate: str, **kw) -> None:
    _ghi(out / f"{gate}_checkpoint.json", {"gate": gate, "study": STUDY, "guardrail": {"passed": True}, **kw})


def _meta(out: Path, g3: dict | None = None, **gp) -> dict:
    meta = {"gate_params": {**({"G3": g3} if g3 is not None else {}), **gp}}
    _ghi(out / "study_meta.json", meta)
    return meta


# G3_checkpoint của lượt a05 (máy tự chạy, chưa ghim gì): OR 1,44 trích từ y văn G1, p0/bỏ cuộc/α/lực mặc định máy.
CP_A05 = {
    "design_code": "rct", "alpha": 0.05, "power": 0.8, "effect_val": 1.44, "effect_type": "OR", "dropout": 0.2,
    "p_event": 0.3, "p0": 0.3, "sd": None, "hypothesis_type": "superiority", "margin": None,
    "outcome_direction": None, "precision": None, "prevalence": None, "icc": None, "cluster_size": None,
    "population_n": None, "confirmed_n": None, "n_adjusted": 1323,
    "nguon_hieu_qua": "trích từ y văn G1/G0 (chất lượng labeled)",
    "nguon_tham_so": {"effect_size": None, "effect_type": None, "sd": None, "confirmed_n": None,
                      "hypothesis_type": "đặc tả thiết kế G1 (g1_khoa)", "alpha": "mặc định 0.05",
                      "power": "mặc định 0.8", "p0": "mặc định 0.3", "dropout": "mặc định 0.2",
                      "p_event": "mặc định 0.3", "precision": "mặc định 0.05"},
}
# Bộ ghim PI điền ở a09 (TEXT4BP, PMID 35342691 — nguồn THẬT của giả lập; tỷ lệ bỏ cuộc là giả định của PI).
GHIM_A09 = {"effect_size": 1.4583, "effect_type": "RR", "dropout": 0.2, "p_event": None, "sd": None, "p0": 0.48,
            "alpha": 0.05, "power": 0.8, "hypothesis_type": "superiority",
            "effect_source": "PMID: 35342691", "dropout_source": "Giả định thận trọng 20 % của PI"}
# G3_checkpoint sau khi G3 chạy lại với bộ ghim (a11): mọi tham số đem vào phép tính = bản ghim.
CP_A11 = {**CP_A05, "effect_val": 1.4583, "effect_type": "RR", "p0": 0.48, "n_adjusted": 218, "nguon_hieu_qua": "CLI",
          "nguon_tham_so": {**CP_A05["nguon_tham_so"], "effect_size": "CLI", "effect_type": "CLI", "p0": "CLI",
                            "dropout": "CLI", "alpha": "CLI", "power": "CLI", "hypothesis_type": "CLI"}}


def _khoa(lech) -> set:
    return {d["khoa"] for d in lech}


# ═══════════════════════════════════════════════════════ 1. Bộ so đầu vào G3 ══════════════════════════════════════
def test_n4_a09_ghim_g3_doi_thi_phat_hien_dung_khoa(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A05)
    meta = _meta(out, GHIM_A09)
    lech = RP._g3_lech_dau_vao_chi_tiet(out, meta)
    assert _khoa(lech) == {"gate_params.G3.effect_size", "gate_params.G3.effect_type", "gate_params.G3.p0"}, lech
    ly_do = RP._g3_lech_dau_vao(out, meta)
    assert "1.4583" in ly_do and "1.44" in ly_do and "0.48" in ly_do and "mặc định 0.3" in ly_do
    assert "trích từ y văn" in ly_do, "nêu nguồn lượt trước để PI thấy G3 đang dùng gì"


def test_n4_a11_g3_da_dung_ban_ghim_thi_khop(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, GHIM_A09)) == []
    assert RP._g3_lech_dau_vao(out, _meta(out, GHIM_A09)) is None


@pytest.mark.parametrize("gia_tri", ["[CẦN — PI ghi p0 có nguồn]", "<tỷ lệ nhóm chứng>", "0,48", "", True, None])
def test_n4_o_mau_khong_ep_duoc_khong_tinh_la_doi(tmp_path, gia_tri):
    """run_g3_auto coi giá trị không ép được float là «chưa cấp» ⇒ bộ so cũng bỏ qua (nếu không: G3 chạy lại mãi)."""
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A05)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {"p0": gia_tri})) == []


def test_n4_go_ghim_khong_tu_chay_lai(tmp_path):
    """Gỡ khoá ghim (ô trống/ô mẫu không phân biệt được với «chưa khai») KHÔNG tự chạy lại — như K5 với query_en."""
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {})) == []
    assert RP._g3_lech_dau_vao_chi_tiet(out, {}) == []


def test_n4_g3_chua_co_hoac_dang_chan_thi_khong_so(tmp_path):
    out = _thu_muc(tmp_path)
    meta = _meta(out, GHIM_A09)
    assert RP._g3_lech_dau_vao_chi_tiet(out, meta) == [], "chưa có G3 ⇒ G3 sẽ chạy vì thiếu checkpoint"
    _cp(out, "G3", **CP_A05, needs_input={"blocked": True, "reason_code": "X", "human_message": "chờ"})
    assert RP._g3_lech_dau_vao_chi_tiet(out, meta) == [], "checkpoint chặn đã luôn được chạy lại"


@pytest.mark.parametrize("khoa,ghim,cp_khoa,cp_cu", [
    ("dropout", 0.15, "dropout", 0.2), ("alpha", 0.025, "alpha", 0.05), ("power", 0.9, "power", 0.8),
    ("p_event", 0.4, "p_event", 0.3), ("sd", 12, "sd", None), ("margin", 0.1, "margin", None),
    ("icc", 0.02, "icc", None), ("cluster_size", 20, "cluster_size", None),
    ("population_n", 5000, "population_n", None), ("confirmed_n", 900, "confirmed_n", None),
    ("confirmed_n", "900", "confirmed_n", None),
])
def test_n4_moi_tham_so_quyet_dinh_n_deu_vao_dau_van_tay(tmp_path, khoa, ghim, cp_khoa, cp_cu):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **{**CP_A11, cp_khoa: cp_cu})
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, khoa: ghim}))) == {f"gate_params.G3.{khoa}"}
    # Cùng giá trị (kể cả dạng chuỗi số) ⇒ khớp.
    _cp(out, "G3", **{**CP_A11, cp_khoa: float(ghim)})
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, khoa: ghim})) == []


@pytest.mark.parametrize("ghim", [0, -5, 12.5, "abc"])
def test_n4_confirmed_n_khong_hop_le_bi_bo_qua(tmp_path, ghim):
    """run_g3_auto bỏ confirmed_n không phải số nguyên dương (checkpoint ghi None) ⇒ bộ so cũng bỏ qua."""
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "confirmed_n": ghim})) == []


def test_n4_cluster_cv_khoa_chuan_thang_ten_cu(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **{**CP_A11, "cluster_cv": 0.14})
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "cluster_size_cv": 0.14})) == []
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "cluster_cv": 0.14})) == []
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "cluster_size_cv": 0.3}))) == {
        "gate_params.G3.cluster_size_cv"}
    # Khoá chuẩn có mặt (kể cả None) thì G3 đọc khoá chuẩn — tên cũ bị bỏ qua (run_g3_auto: .get(chuẩn, cũ)).
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "cluster_size_cv": None,
                                                         "cluster_cv": 0.3})) == []


# Đề tài mô tả cắt ngang kiểu C1a (giá trị tổng hợp): effect_type PREVALENCE + prevalence ghim riêng.
CP_CAT_NGANG = {"design_code": "cross_sectional", "alpha": 0.05, "power": 0.8, "effect_val": 0.5,
                "effect_type": "PREVALENCE", "dropout": 0.15, "p_event": 0.3, "p0": 0.3, "sd": None,
                "hypothesis_type": "descriptive_precision", "precision": 0.05, "prevalence": 0.5, "n_adjusted": 452,
                "nguon_hieu_qua": "study_meta",
                "nguon_tham_so": {"effect_size": "study_meta", "effect_type": "study_meta",
                                  "hypothesis_type": "study_meta", "prevalence": "study_meta",
                                  "precision": "study_meta", "dropout": "study_meta"}}
GHIM_CAT_NGANG = {"effect_size": 0.5, "effect_type": "PREVALENCE", "prevalence": 0.5, "precision": 0.05,
                  "dropout": 0.15, "hypothesis_type": "descriptive_precision", "sd": None}


def test_n4_cat_ngang_prevalence_precision(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_CAT_NGANG)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, GHIM_CAT_NGANG)) == []
    # prevalence ghim riêng thì G3 lấy nó — effect_size đổi không có tác dụng ⇒ không chạy lại vô cớ.
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_CAT_NGANG, "effect_size": 0.4})) == []
    # Không ghim prevalence ⇒ effect_size LÀ tỷ lệ ước lượng — so với prevalence G3 đã dùng.
    ghim = {k: v for k, v in GHIM_CAT_NGANG.items() if k != "prevalence"}
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim)) == []
    lech = RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**ghim, "effect_size": 0.4}))
    assert len(lech) == 1 and "PREVALENCE" in lech[0]["khoa"] and lech[0]["da_dung"] == 0.5
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_CAT_NGANG, "prevalence": 0.3}))) == {
        "gate_params.G3.prevalence"}
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_CAT_NGANG, "precision": 0.04}))) == {
        "gate_params.G3.precision"}
    # Cắt ngang + ghim «superiority» ⇒ run_g3_auto đổi thành descriptive_precision — không phải lệch.
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_CAT_NGANG, "hypothesis_type": "superiority"})) == []


def test_n4_precision_chi_so_khi_g3_tinh_theo_do_chinh_xac(tmp_path):
    """RCT: G3 không ghi precision (None) ⇒ precision ghim (thừa) không làm G3 chạy lại mãi."""
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "precision": 0.04})) == []


def test_n4_effect_type_hoa_thuong_bi_danh_ni_va_dung_mot_minh(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    for loai in ("rr", "Risk Ratio", " RR "):
        assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "effect_type": loai})) == [], loai
    # Loại hiệu quả đứng một mình (không effect_size) — G3 không dùng ⇒ không so.
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {"effect_type": "HR"})) == []
    # NI/tương đương: G3 ghi «NI_PROPORTION», effect_size là p_test ⇒ so effect_size, KHÔNG so effect_type.
    cp_ni = {**CP_A11, "effect_type": "NI_PROPORTION", "effect_val": 0.85, "hypothesis_type": "non_inferiority",
             "margin": 0.1}
    _cp(out, "G3", **cp_ni)
    ghim_ni = {"hypothesis_type": "non_inferiority", "effect_size": 0.85, "effect_type": "RR", "margin": 0.1,
               "p0": 0.48, "dropout": 0.2, "alpha": 0.05, "power": 0.8}
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim_ni)) == []
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**ghim_ni, "effect_size": 0.8}))) == {
        "gate_params.G3.effect_size"}
    # Checkpoint CŨ (trước G3-07) ghi NI bằng «p_test» và có thể thiếu hypothesis_type: vẫn không so loại hiệu quả.
    for loai_cu in ("p_test", "NI_PROPORTION"):
        cu = {k: v for k, v in {**cp_ni, "effect_type": loai_cu}.items() if k != "hypothesis_type"}
        _cp(out, "G3", **cu)
        ghim_cu = {k: v for k, v in ghim_ni.items() if k != "hypothesis_type"}
        assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim_cu)) == [], loai_cu


def test_n4_gia_thuyet_ghim_chuan_hoa_va_lech(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "hypothesis_type": "Superiority"})) == []
    lech = RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "hypothesis_type": "Non-inferiority"}))
    assert _khoa(lech) == {"gate_params.G3.hypothesis_type"} and lech[0]["mong_muon"] == "non_inferiority"


def test_n4_test_type_g0_khi_g3_lay_gia_thuyet_tu_g0_hoac_mac_dinh(tmp_path):
    out = _thu_muc(tmp_path)
    tu_g0 = {**CP_A11, "nguon_tham_so": {**CP_A11["nguon_tham_so"],
                                         "hypothesis_type": "G0 test_type (study_meta.gate_params.G0)"}}
    _cp(out, "G3", **tu_g0)
    ghim = {k: v for k, v in GHIM_A09.items() if k != "hypothesis_type"}
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim, G0={"test_type": "superiority"})) == []
    lech = RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim, G0={"test_type": "non_inferiority"}))
    assert len(lech) == 1 and "test_type" in lech[0]["khoa"] and lech[0]["mong_muon"] == "non_inferiority"
    _cp(out, "G3", **{**tu_g0, "nguon_tham_so": {**tu_g0["nguon_tham_so"], "hypothesis_type": "mặc định máy"}})
    assert len(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim, G0={"test_type": "equivalence"}))) == 1
    # Giả thuyết lấy từ đặc tả G1 (đứng TRƯỚC test_type G0 trong run_g3_auto) ⇒ test_type không quyết — không so.
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, ghim, G0={"test_type": "non_inferiority"})) == []
    _cp(out, "G3", **CP_A05)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {}, G0={"test_type": "non_inferiority"})) == []


def test_n4_chieu_ket_cuc_chuan_hoa_va_lech(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **{**CP_A11, "outcome_direction": "higher_better"})
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "outcome_direction": "cao là tốt"})) == []
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "outcome_direction": "lower_better"}))) \
        == {"gate_params.G3.outcome_direction"}
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, {**GHIM_A09, "outcome_direction": "không rõ"})) == [], \
        "chiều không nhận ra ⇒ run_g3_auto dừng lỗi — không phải «đổi» để chạy lại"


def test_n4_thiet_ke_phan_giai_doi_thi_g3_cu(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A11)
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, GHIM_A09)) == [], \
        "G1/G2 chưa ghi thiết kế ⇒ resolve_design_code rơi về mặc định «cohort» — không đo được ≠ đổi"
    _cp(out, "G1", design={"internal_code": "rct"})
    assert RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, GHIM_A09)) == []
    _cp(out, "G2", design_code="cohort")   # G2 thắng G1 trong gate_contract.resolve_design_code
    lech = RP._g3_lech_dau_vao_chi_tiet(out, _meta(out, GHIM_A09))
    assert len(lech) == 1 and "thiết kế" in lech[0]["khoa"] and lech[0]["mong_muon"] == "cohort"


CFG_LUC = {"muc_tieu": "Mục tiêu 2", "ket_cuc": "Điểm hài lòng", "phoi_nhiem": "thời gian chờ", "don_vi": "phút",
           "buoc": 15, "sd_gia_dinh": [20, 30], "r2": 0.2, "nguon": "Giả định tổng hợp cho phép thử",
           "phan_bo_ket_cuc": {"Lệch vừa": [0.02, 0.05, 0.18, 0.45, 0.30]}}


def test_n4_luc_muc_tieu_phu_tinh_lai_bang_chinh_run_g3_auto(tmp_path):
    out = _thu_muc(tmp_path)
    cp = {**CP_CAT_NGANG, "confirmed_n": 1000, "design_effect": 1.38}
    _cp(out, "G3", **cp)
    meta = _meta(out, {**GHIM_CAT_NGANG, "confirmed_n": 1000, "luc_muc_tieu_phu": CFG_LUC})
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, meta)) == {"gate_params.G3.luc_muc_tieu_phu"}, \
        "khai cấu hình mà lượt G3 chưa tính ⇒ cũ"
    luc = R3.tinh_luc_muc_tieu_phu(CFG_LUC, 1000, 0.15, 1.38, 0.05, 0.8)
    _cp(out, "G3", **cp, luc_muc_tieu_phu=luc)
    assert RP._g3_lech_dau_vao_chi_tiet(out, meta) == []
    meta = _meta(out, {**GHIM_CAT_NGANG, "confirmed_n": 1000, "luc_muc_tieu_phu": {**CFG_LUC, "buoc": 10}})
    assert _khoa(RP._g3_lech_dau_vao_chi_tiet(out, meta)) == {"gate_params.G3.luc_muc_tieu_phu"}


# ═══════════════════════════════════════════ 2. orchestrate với cổng GIẢ ═══════════════════════════════════════════
def _cong_cua(cmd) -> str:
    ten = Path(cmd[1]).name
    if ten == "run_g10_assemble.py":
        return "G10"
    return ten.replace("run_", "").replace("_auto.py", "").upper()


class _CongGia:
    """Cổng con GIẢ: {cổng: hàm(out, cmd) -> mã thoát}; cổng không có trong kịch bản ⇒ mã 2 (chờ input)."""

    def __init__(self, out: Path, kich_ban: dict):
        self.out, self.kb, self.lenh, self.cmd = out, kich_ban, [], []

    def __call__(self, cmd, out_dir):
        gate = _cong_cua(cmd)
        self.lenh.append(gate)
        self.cmd.append(list(cmd))
        hd = self.kb.get(gate, GC.EXIT_BLOCKED)
        ma = hd(self.out, cmd) if callable(hd) else hd
        return {"exit_code": GC.EXIT_BLOCKED if ma is None else ma, "stdout_tail": f"giả {gate}", "stderr_tail": ""}


_SONG_MAC_DINH = {"G0": "PASS", "G1": "PASS", "G2": "DRAFT", "G3": "DRAFT", "G4": "DRAFT"}


def _song(muc: str) -> dict:
    status = {"PASS": "PASS_GX_CONFIRMED", "DRAFT": "DRAFT_READY_NEEDS_HUMAN_REVIEW", "BLOCKED": "BLOCKED"}[muc]
    return {"status": status, "muc": muc, "nguon": "song", "ly_do": "giả",
            "chan": ["GX-AUTO-18: giả"] if muc == "BLOCKED" else [], "cho": ["GX-AUTO-07"] if muc == "DRAFT" else []}


def _chay(tmp_path, monkeypatch, out, kich_ban, *, song=None, start=None, runner=None):
    gia = runner or _CongGia(out, kich_ban)
    song = {**_SONG_MAC_DINH, **(song or {})}
    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP, "_run_gate_once", gia)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": [], "orphan_gates": [], "fresh": True, "issues": [], "checkpoints_present": []})
    monkeypatch.setattr(RP, "_cham_song", lambda gate, study, out_dir: _song(song.get(gate, "DRAFT")))
    return gia, RP.orchestrate(STUDY, None, 1, start, False)


def _theo_cong(bc) -> dict:
    return {r["gate"]: r for r in bc["gate_results"]}


def _ghi_cp(gate, **kw):
    def hd(out, cmd):
        _cp(out, gate, **kw)
        return GC.EXIT_OK
    return hd


def _chuoi_a08(out):
    """Trạng thái ngay trước a09: G0–G4 «tươi» theo mtime, G3 mang tham số máy (CP_A05); PI vừa điền gate_params.G3."""
    for g in ("G0", "G1", "G2", "G4"):
        _cp(out, g)
    _cp(out, "G3", **CP_A05)
    _meta(out, GHIM_A09)


def test_n4_pipeline_chay_lai_g3_va_day_chuyen_sau_g3_thanh_cu(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G3": _ghi_cp("G3", **CP_A11), "G4": _ghi_cp("G4")})
    assert gia.lenh == ["G3", "G4", "G5"], "mtime «tươi» nhưng đầu vào G3 đổi ⇒ G3 chạy lại, sau G3 thành cũ"
    kq = _theo_cong(bc)
    assert kq["G0"]["status"] == kq["G1"]["status"] == kq["G2"]["status"] == "skipped_fresh"
    assert "đầu vào G3 đổi" in kq["G3"]["ly_do_chay_lai"] and "p0=0.48" in kq["G3"]["ly_do_chay_lai"]
    cmd_g3 = gia.cmd[0]
    assert cmd_g3[cmd_g3.index("--effect-size") + 1] == "1.4583" and cmd_g3[cmd_g3.index("--p0") + 1] == "0.48", \
        "G3 chạy lại với ĐÚNG bản ghim (không phải giá trị checkpoint cũ)"
    assert bc["g3_dau_vao_doi"] == [] and bc["g3_dau_vao_khong_ap"] is None, "G3 đã áp bản ghim ⇒ hết lệch"
    assert not {"dau_vao_g3_doi", "dau_vao_g3_khong_ap"} & {i["kind"] for i in bc["do_tuoi_tong_hop"]["issues"]}
    RP.print_summary(bc)
    assert "↳ chạy lại vì: CHẠY LẠI G3 vì đầu vào G3 đổi" in capsys.readouterr().out
    # Hội tụ: lượt kế tiếp không chạy lại G3.
    gia2, bc2 = _chay(tmp_path, monkeypatch, out, {"G3": _ghi_cp("G3", **CP_A11), "G4": _ghi_cp("G4")})
    assert "G3" not in gia2.lenh and _theo_cong(bc2)["G3"]["status"] == "skipped_fresh"


def test_n4_truoc_ban_va_khong_ghim_thi_g3_van_tuoi(tmp_path, monkeypatch):
    """Đối chứng: chưa ghim gì (hoặc ghim trùng) ⇒ không đụng G3 — đúng hành vi trước bản vá."""
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    _meta(out, {})
    gia, _bc = _chay(tmp_path, monkeypatch, out, {"G3": _ghi_cp("G3", **CP_A11)})
    assert gia.lenh == ["G5"]


def test_n4_rao_cong_da_ky_g4_giu_nguyen_khi_g3_chay_lai(tmp_path, monkeypatch, capsys):
    """G4 (SAP) ĐÃ KÝ: đầu vào G3 đổi ⇒ G3 chạy lại, nhưng dây chuyền KHÔNG sinh lại G4 — chỉ báo (rào #249)."""
    assert "G4" in GC._GATE_REQUIRED_STAKEHOLDERS
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G3": _ghi_cp("G3", **CP_A11), "G4": _ghi_cp("G4")},
                    song={"G4": "PASS"})
    assert gia.lenh[0] == "G3" and "G4" not in gia.lenh, "cổng cứng đã ký không bị sinh lại qua dây chuyền G3 → G4"
    kq = _theo_cong(bc)
    assert kq["G4"]["status"] == "giu_cong_da_ky" and "dây chuyền: G3" in kq["G4"]["detail"]
    assert "--from G4" in kq["G4"]["detail"]
    assert bc["n_giu_da_ky"] == 1 and bc["converged_fresh"] is False
    RP.print_summary(bc)
    ra = capsys.readouterr().out
    assert "🔏 G4: GIỮ — cổng ĐÃ KÝ" in ra and "✅ TƯƠI" not in ra


def test_n4_g3_khong_ap_duoc_ghim_chi_bao_khong_chay_lai_mai(tmp_path, monkeypatch, capsys):
    """Chống lặp: G3 chạy lại mà vẫn dùng giá trị khác bản ghim (vd effect_size thiếu effect_type) ⇒ lượt sau KHÔNG chạy
    lại G3 nữa (cùng checkpoint, cùng giá trị ghim) — chỉ báo «không áp được», không «TƯƠI». Đổi giá trị ghim ⇒ chạy
    lại."""
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    _meta(out, {"effect_size": 1.4583})                         # thiếu effect_type: G3 vẫn dùng OR 1,44 trích y văn
    g3_bo_qua = _ghi_cp("G3", **CP_A05)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua, "G4": _ghi_cp("G4")})
    assert gia.lenh[0] == "G3"
    assert bc["g3_dau_vao_khong_ap"]["khoa"] == {"gate_params.G3.effect_size": "1.4583"}
    assert len(bc["g3_dau_vao_khong_ap"]["chu_ky"]) == 64
    assert "dau_vao_g3_khong_ap" in {i["kind"] for i in bc["do_tuoi_tong_hop"]["issues"]}
    assert bc["converged_fresh"] is False
    gia2, bc2 = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua, "G4": _ghi_cp("G4")})
    assert "G3" not in gia2.lenh, "không chạy lại G3 mãi khi G3 không áp được giá trị ghim"
    assert bc2["g3_dau_vao_khong_ap"]["khoa"] == {"gate_params.G3.effect_size": "1.4583"}, "bản ghi được giữ tiếp"
    assert bc2["converged_fresh"] is False
    RP.print_summary(bc2)
    ra = capsys.readouterr().out
    assert "KHÔNG được áp dù G3 đã chạy lại" in ra and "✅ TƯƠI" not in ra
    # PI sửa bộ ghim — kể cả khi chỉ THÊM effect_type trùng loại G3 đang dùng (effect_size giữ nguyên giá trị đã ghi
    # «không áp được») — tổ hợp mới chưa từng thử ⇒ bản ghi hết hiệu lực, chạy lại.
    _meta(out, {"effect_size": 1.4583, "effect_type": "OR"})
    gia3, _bc3 = _chay(tmp_path, monkeypatch, out, {"G3": _ghi_cp("G3", **{**CP_A05, "effect_val": 1.4583}),
                                                    "G4": _ghi_cp("G4")})
    assert gia3.lenh[0] == "G3", "bộ ghim đổi ⇒ thử lại dù khoá effect_size cùng giá trị đã ghi"
    _meta(out, GHIM_A09)
    gia4, bc4 = _chay(tmp_path, monkeypatch, out, {"G3": _ghi_cp("G3", **CP_A11), "G4": _ghi_cp("G4")})
    assert gia4.lenh[0] == "G3" and bc4["g3_dau_vao_khong_ap"] is None


def test_n4_bo_cham_g3_ghi_lai_checkpoint_khong_lam_mat_ban_ghi_khong_ap(tmp_path, monkeypatch):
    """g3_quality_gate (CLI, write=True) ghi kết quả chấm VÀO G3_checkpoint mà G3 không chạy lại — bản ghi «không áp
    được» phải còn hiệu lực (nếu không: mỗi lần PI chạy bộ chấm, lượt pipeline sau sinh lại G3 + mọi cổng sau G3 vô cớ).
    G3 chạy lại thật (tham số/N khác) thì bản ghi hết hiệu lực."""
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    _meta(out, {"effect_size": 1.4583})
    g3_bo_qua = _ghi_cp("G3", **CP_A05)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua, "G4": _ghi_cp("G4")})
    assert gia.lenh[0] == "G3" and bc["g3_dau_vao_khong_ap"]["khoa"]
    # Mô phỏng đúng các khoá bộ chấm ghi (g3_quality_gate.write_quality_report → ghi_checkpoint_giu_moc_sinh).
    p = out / "G3_checkpoint.json"
    cp = _doc(p)
    cp.update({"quality_contract_version": "G3-2026.1", "disclaimer": "Cần bác sĩ kiểm chứng.",
               "quality_gate": {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW", "evaluated_at": "2026-11-15T09:00:00"},
               "pending_doctor_actions": ["Xác nhận effect size"], "artifacts": {"quality_report": "x.json"}})
    _ghi(p, cp)
    gia2, bc2 = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua, "G4": _ghi_cp("G4")})
    assert "G3" not in gia2.lenh, "bộ chấm ghi lại checkpoint ≠ G3 chạy lại — không sinh lại G3 vô cớ"
    assert bc2["g3_dau_vao_khong_ap"]["khoa"] == {"gate_params.G3.effect_size": "1.4583"}
    # PI tự chạy run_g3_auto với tham số khác (N đổi) ⇒ lượt G3 mới ⇒ bản ghi hết hiệu lực, pipeline thử lại bản ghim.
    _ghi(p, {**cp, "p0": 0.35, "n_adjusted": 1100})
    gia3, _bc3 = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua, "G4": _ghi_cp("G4")})
    assert gia3.lenh[0] == "G3", "G3 đã chạy lại bằng đường khác ⇒ bản ghi cũ không còn che"


def test_n4_g3_chay_lai_ma_cham_song_bi_chan_van_ghi_khong_ap(tmp_path, monkeypatch):
    """G3 đã sinh lại checkpoint (mã 0) nhưng chấm sống BỊ CHẶN ⇒ vẫn là «G3 đã chạy với bộ ghim này»: ghi «không áp
    được» để lượt sau không chạy lại G3 mãi (chuỗi dừng ở G3 như trước)."""
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    _meta(out, {"effect_size": 1.4583})
    g3_bo_qua = _ghi_cp("G3", **CP_A05)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua}, song={"G3": "BLOCKED"})
    assert gia.lenh == ["G3"] and _theo_cong(bc)["G3"]["status"] == "chan_song"
    assert bc["g3_dau_vao_khong_ap"] and bc["g3_dau_vao_khong_ap"]["khoa"]
    gia2, _bc2 = _chay(tmp_path, monkeypatch, out, {"G3": g3_bo_qua}, song={"G3": "BLOCKED"})
    assert "G3" not in gia2.lenh


def test_n4_check_only_bao_dau_vao_g3_ma_thoat_1(tmp_path, monkeypatch, capsys):
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    monkeypatch.setattr(RP, "BASE", tmp_path)
    monkeypatch.setattr(RP.FRESH, "stale_report", lambda out_dir: {
        "stale_gates": [], "orphan_gates": [], "fresh": True, "issues": [], "checkpoints_present": ["G0", "G3"]})
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--study", STUDY, "--check-only"])
    assert RP.main() == 1
    ra = capsys.readouterr().out
    assert "dau_vao_g3_doi" in ra and "p0=0.48" in ra and "✅ TƯƠI" not in ra


def test_n4_from_sau_g3_khong_chay_g3_nhung_khong_bao_tuoi(tmp_path, monkeypatch):
    out = _thu_muc(tmp_path)
    _chuoi_a08(out)
    gia, bc = _chay(tmp_path, monkeypatch, out, {"G4": _ghi_cp("G4")}, start="G4")
    assert "G3" not in gia.lenh and _theo_cong(bc)["G3"]["status"] == "skipped_before_start"
    assert bc["g3_dau_vao_doi"] and bc["converged_fresh"] is False
    assert "dau_vao_g3_doi" in {i["kind"] for i in bc["do_tuoi_tong_hop"]["issues"]}


def test_n4_do_tuoi_tong_hop_tach_doi_va_khong_ap(capsys):
    tuoi = {"fresh": True, "issues": [], "stale_gates": [], "orphan_gates": [], "checkpoints_present": ["G3"]}
    doi = {"khoa": "gate_params.G3.p0", "ly_do": "gate_params.G3.p0=0.48 ≠ G3 đã dùng 0.3", "khong_ap": False}
    th = RP._do_tuoi_tong_hop(tuoi, {}, None, {"tong": {}, "lech": []}, lech_g3=[doi])
    assert th["fresh"] is False and th["dau_vao_g3_doi"] and not th["dau_vao_g3_khong_ap"]
    th2 = RP._do_tuoi_tong_hop(tuoi, {}, None, {"tong": {}, "lech": []}, lech_g3=[{**doi, "khong_ap": True}])
    assert th2["fresh"] is False and th2["issues"][0]["kind"] == "dau_vao_g3_khong_ap"
    assert RP._do_tuoi_tong_hop(tuoi, {}, None, {"tong": {}, "lech": []}, lech_g3=[])["fresh"] is True
    RP._in_do_tuoi(th, "Freshness sau")
    assert "dau_vao_g3_doi" in capsys.readouterr().out


# ═════════════════════════════════════ 3. _recover_params — bản ghim tới được run_g3_auto ════════════════════════════
def test_n4_recover_params_chuan_hoa_loai_hieu_qua_va_gia_thuyet(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_A05)
    argv = RP._recover_params("G3", out, {"gate_params": {"G3": {"effect_size": 1.2, "effect_type": "risk ratio",
                                                                 "hypothesis_type": "Non-inferiority"}}})
    assert argv[argv.index("--effect-type") + 1] == "RR"
    assert argv[argv.index("--hypothesis-type") + 1] == "non_inferiority"
    # Mã lạ: giữ hành vi cũ (truyền nguyên văn để argparse báo rõ) — không đoán thay.
    argv = RP._recover_params("G3", out, {"gate_params": {"G3": {"effect_type": "XYZ"}}})
    assert argv[argv.index("--effect-type") + 1] == "XYZ"


def test_n4_recover_params_prevalence_cu_khong_de_effect_size_moi(tmp_path):
    out = _thu_muc(tmp_path)
    _cp(out, "G3", **CP_CAT_NGANG)
    ghim = {"effect_size": 0.4, "effect_type": "PREVALENCE", "precision": 0.05}
    argv = RP._recover_params("G3", out, {"gate_params": {"G3": ghim}})
    assert "--prevalence" not in argv, "prevalence cũ (0,5) của checkpoint sẽ thắng effect_size PI vừa sửa"
    argv = RP._recover_params("G3", out, {"gate_params": {"G3": {**ghim, "prevalence": 0.3}}})
    assert argv[argv.index("--prevalence") + 1] == "0.3"
    argv = RP._recover_params("G3", out, {"gate_params": {"G3": {"precision": 0.05}}})
    assert argv[argv.index("--prevalence") + 1] == "0.5", "không ghim effect_size PREVALENCE ⇒ giữ hành vi cũ"


# ═════════════════════════════════════ 4. HỘI TỤ với run_g3_auto THẬT ═══════════════════════════════════════════════
_KICH_BAN_THAT = {
    # PI gõ «rr» chữ thường — đường bản ghim → dòng lệnh phải chuẩn hoá (choices viết hoa).
    "rct_superiority": ("rct", {"effect_size": 1.4583, "effect_type": "rr", "p0": 0.48, "dropout": 0.2}),
    "rct_md_sd": ("rct", {"effect_size": 5, "effect_type": "MD", "sd": 12, "power": 0.9, "dropout": 0.1}),
    "rct_ni": ("rct", {"hypothesis_type": "Non-inferiority", "effect_size": 0.85, "margin": 0.1,
                       "outcome_direction": "higher_better", "p0": 0.85, "dropout": 0.1}),
    "rct_cum": ("rct", {"effect_size": 0.7, "effect_type": "RR", "p0": 0.3, "icc": 0.02, "cluster_size": 20,
                        "cluster_size_cv": 0.3, "dropout": 0.1}),
    "rct_n_chot": ("rct", {"effect_size": 0.7, "effect_type": "RR", "p0": 0.3, "confirmed_n": 900, "alpha": 0.025}),
    "cohort_quan_the_huu_han": ("cohort", {"effect_size": 0.7, "effect_type": "RR", "p0": 0.3,
                                           "population_n": 5000, "p_event": 0.4}),
    "cat_ngang_effect_size_prevalence": ("cross_sectional", {"effect_size": 0.4, "effect_type": "PREVALENCE",
                                                             "precision": 0.04, "dropout": 0.1}),
    "cat_ngang_prevalence_rieng": ("cross_sectional", {"prevalence": 0.3, "precision": 0.05, "dropout": 0.15,
                                                       "confirmed_n": 600, "luc_muc_tieu_phu": CFG_LUC}),
}


def _g3_qua_pipeline(out: Path):
    """Chạy run_g3_auto THẬT bằng ĐÚNG dòng lệnh pipeline dựng (_recover_params) — trả (checkpoint, mã thoát)."""
    argv = RP._recover_params("G3", out, RP._load_meta(out))
    CS.xoa_dem()
    try:
        return chay_g3_that(out, STUDY, argv)
    finally:
        CS.xoa_dem()


def _ghim_vao_meta(out: Path, ghim: dict) -> dict:
    p = out / "study_meta.json"
    meta = _doc(p)
    meta.setdefault("gate_params", {}).setdefault("G3", {}).update(ghim)
    _ghi(p, meta)
    return meta


@pytest.mark.parametrize("ten", sorted(_KICH_BAN_THAT))
def test_n4_hoi_tu_voi_run_g3_auto_that(tmp_path, ten):
    """Lượt máy (chưa ghim) → PI ghim → bộ so báo ĐỔI → G3 chạy lại đúng đường pipeline → bộ so về [] và ĐỨNG YÊN ở lượt
    chạy lại kế tiếp (không vòng lặp)."""
    thiet_ke, ghim = _KICH_BAN_THAT[ten]
    out = tmp_path / "exports" / STUDY
    dung_g0_g1_da_chot(out, STUDY, thiet_ke=thiet_ke, mau_hieu_qua=EFFECTS if thiet_ke != "cross_sectional" else [],
                       kiem=False)
    cp0, _rc0 = _g3_qua_pipeline(out)
    assert cp0.get("n_adjusted") is not None
    meta = _ghim_vao_meta(out, ghim)
    truoc = RP._g3_lech_dau_vao_chi_tiet(out, meta)
    assert truoc, f"{ten}: PI vừa ghim khác lượt máy ⇒ phải báo đổi"
    cp1, rc1 = _g3_qua_pipeline(out)
    assert rc1 in (None, 0, GC.EXIT_OK), f"{ten}: run_g3_auto mã {rc1}"
    sau = RP._g3_lech_dau_vao_chi_tiet(out, RP._load_meta(out))
    assert sau == [], f"{ten}: G3 chạy lại với bản ghim mà bộ so vẫn báo đổi (sẽ chạy lại mãi): {sau}"
    _cp2, _rc2 = _g3_qua_pipeline(out)
    assert RP._g3_lech_dau_vao_chi_tiet(out, RP._load_meta(out)) == [], f"{ten}: lượt chạy lại kế tiếp lệch lại"


def test_n4_dau_cuoi_orchestrate_voi_g3_that_luot2_da_tuoi(tmp_path, monkeypatch):
    """Đường a09 qua orchestrate thật (chỉ G3 là cổng thật): PI ghim ⇒ lượt 1 chạy lại G3 với bản ghim (N đổi), lượt 2
    G3 «đã tươi» — không còn can thiệp «PI tự chạy run_g3_auto»."""
    out = tmp_path / "exports" / STUDY
    dung_g0_g1_da_chot(out, STUDY, thiet_ke="rct", mau_hieu_qua=EFFECTS, kiem=False)
    cp0, _ = _g3_qua_pipeline(out)
    for g in ("G2", "G4"):
        _cp(out, g)
    _ghim_vao_meta(out, {"effect_size": 1.4583, "effect_type": "RR", "p0": 0.48, "dropout": 0.2})

    def g3_that(o, cmd):
        CS.xoa_dem()
        _cp_moi, rc = chay_g3_that(o, STUDY, list(cmd[4:]))
        return GC.EXIT_OK if rc in (None, 0) else rc

    kb = {"G1": GC.EXIT_OK, "G2": GC.EXIT_OK, "G3": g3_that, "G4": GC.EXIT_OK}
    gia, bc = _chay(tmp_path, monkeypatch, out, kb)
    assert gia.lenh[0] == "G3", gia.lenh
    cp1 = _doc(out / "G3_checkpoint.json")
    assert cp1["effect_val"] == 1.4583 and cp1["effect_type"] == "RR" and cp1["p0"] == 0.48
    assert cp1["n_adjusted"] != cp0["n_adjusted"], "N tính lại theo bản ghim"
    assert bc["g3_dau_vao_doi"] == [] and bc["g3_dau_vao_khong_ap"] is None
    gia2, bc2 = _chay(tmp_path, monkeypatch, out, kb)
    assert "G3" not in gia2.lenh and _theo_cong(bc2)["G3"]["status"] == "skipped_fresh"
