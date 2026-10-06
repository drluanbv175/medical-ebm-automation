# -*- coding: utf-8 -*-
"""Hoàn thiện cổng G1 (soát từng cổng G0–G10, 04/10/2026) — mỗi test neo vào MỘT phát hiện đã được phản biện xác nhận.

G1-01 design_confirmed phải `is True` · G1-02 đề cương lõi: dòng phạm vi G1 lấy từ gate_params, còn trống ⇒ REVIEW,
dòng hoãn cho cổng sau bỏ qua · G1-03 risk register/kinh phí từ study_meta, «Ngày rà» không do máy điền, sao lưu bản sửa
tay · G1-04/G0-01 tiền đề G0 chấm sống · G1-05 pin bị từ chối lan xuống resolve_design_code · G1-06 loại câu hỏi lấy từ
G0, thiết kế phải hợp loại câu hỏi · G1-07 ghim gỡ cờ mơ hồ + lý do của PI · G1-08 SAP RCT theo estimand đã khai ·
G1-09 xác nhận gắn dấu vân tay + ngày không ở tương lai · G1-10 evaluate_study + khối đặc tả thiết kế (CHUNG-F) ·
G1-11 RCT phải khai Annex 2 · G1-12 so pin sau chuẩn hoá. Ngoại tuyến.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import annex2_quality_gate as A2X  # noqa: E402
import cong_song as CS  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g1_auto as G1  # noqa: E402
import skill_standards as SK  # noqa: E402
from test_g1_quality_gate import _build_case, _chot_g1, _confirmed_meta, _design, _evaluate, _g0  # noqa: E402


def _row(r, tid):
    return next(c for c in r["automatic_criteria"] + r["human_criteria"] if c["id"] == tid)


def _da_chot():
    return _chot_g1(_confirmed_meta(), _design())


def test_duong_pass_van_dat_duoc(tmp_path):
    assert _evaluate(_build_case(tmp_path, meta=_da_chot()))["status"] == G1Q.STATUS_CONFIRMED


# ── G1-01 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("gia_tri", ["false", "chưa", "[CẦN PI XÁC NHẬN]", "yes", 1, None])
def test_g1_01_chi_true_moi_la_da_xac_nhan_thiet_ke(tmp_path, gia_tri):
    meta = _confirmed_meta()
    meta["gate_params"]["G1"]["design_confirmed"] = gia_tri
    r = _evaluate(_build_case(tmp_path, meta=_chot_g1(meta, _design())))
    h1 = _row(r, "G1-HUMAN-01")
    assert h1["status"] == "REVIEW" and repr(gia_tri) in h1["evidence"], h1
    assert r["status"] != G1Q.STATUS_CONFIRMED


# ── G1-12 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ghim", ["RCT", "rct_parallel", "Randomised"])
def test_g1_12_so_pin_sau_khi_chuan_hoa(tmp_path, ghim):
    meta = _confirmed_meta()
    meta["design_code"] = ghim
    meta["gate_params"]["G1"]["design"] = ghim
    r = _evaluate(_build_case(tmp_path, meta=_chot_g1(meta, _design())))
    assert _row(r, "G1-HUMAN-01")["status"] == "PASS", ghim


# ── G1-04 / G0-01 ──────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("song,ky_vong", [
    ({"nguon": CS.NGUON_SONG, "muc": "PASS", "status": "PASS_G0_CONFIRMED"}, "PASS"),
    ({"nguon": CS.NGUON_SONG, "muc": "DRAFT", "status": "DRAFT_READY_NEEDS_HUMAN_REVIEW",
      "trang_thai_luu": "PASS_G0_CONFIRMED"}, "REVIEW"),
    ({"nguon": CS.NGUON_SONG, "muc": "BLOCKED", "status": "BLOCKED"}, "BLOCK"),
    ({"nguon": CS.NGUON_LOI, "muc": CS.KHONG_DO_DUOC, "status": CS.KHONG_DO_DUOC, "ly_do": "hỏng"}, "REVIEW"),
])
def test_g1_04_tien_de_g0_cham_song(tmp_path, song, ky_vong):
    r = _evaluate(_build_case(tmp_path, meta=_da_chot()), g0_song=song)
    a1 = _row(r, "G1-AUTO-01")
    assert a1["status"] == ky_vong, a1
    if song.get("trang_thai_luu"):
        assert "bản LƯU=PASS_G0_CONFIRMED" in a1["evidence"], "phải nói rõ bản lưu khác chấm sống"


def test_g1_04_g0_kieu_cu_khong_con_mo_cua(tmp_path):
    g0 = _g0()
    g0.pop("quality_gate")
    g0.pop("quality_contract_version")
    assert _row(_evaluate(_build_case(tmp_path, meta=_da_chot(), g0=g0)), "G1-AUTO-01")["status"] == "REVIEW"
    g0["quality_gate"] = {"status": "DRAFT_READY_NEEDS_HUMAN_REVIEW"}
    assert _row(_evaluate(_build_case(tmp_path / "b", meta=_da_chot(), g0=g0)), "G1-AUTO-01")["status"] == "REVIEW"


# ── G1-06 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_06_thiet_ke_phai_hop_loai_cau_hoi_g0(tmp_path):
    meta = _da_chot()
    meta["gate_params"]["G0"] = {"question_type": "descriptive"}
    a2d = _row(_evaluate(_build_case(tmp_path, meta=meta)), "G1-AUTO-02d")
    assert a2d["status"] == "REVIEW" and "descriptive" in a2d["evidence"]
    meta["gate_params"]["G0"] = {"question_type": "therapy"}
    assert _row(_evaluate(_build_case(tmp_path / "b", meta=meta)), "G1-AUTO-02d")["status"] == "PASS"


def _chay_main(tmp_path, monkeypatch, meta_g0=None, them_args=(), g0_luu=None, g0_ghi_de=None):
    """Chạy run_g1_auto.main() thật (mạng giả). Gọi lại trên cùng tmp_path = SINH LẠI (giữ nguyên G0 đã có).

    g0_luu: trạng thái chất lượng G0 LƯU trong checkpoint (để thử «bản lưu PASS nhưng chấm sống chưa đạt»)."""
    study = "TEST-G1-MAIN"
    d = tmp_path / "exports" / study
    if not d.exists():
        d.mkdir(parents=True)
        from test_g0_quality_gate_20260728 import _artifact_text as g0_a1
        from test_g0_quality_gate_20260728 import _checkpoint as g0_cp
        cp0 = g0_cp(study=study, **(g0_ghi_de or {}))
        if g0_luu:
            cp0.update({"quality_contract_version": 1, "quality_gate": {"status": g0_luu}})
        (d / "G0_checkpoint.json").write_text(json.dumps(cp0, ensure_ascii=False), encoding="utf-8", newline="\n")
        (d / f"G0_A1_PICO_FINER_{study}.md").write_text(g0_a1(), encoding="utf-8", newline="\n")
        if meta_g0 is not None:
            (d / "study_meta.json").write_text(json.dumps({"gate_params": {"G0": meta_g0}}, ensure_ascii=False),
                                               encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(G1, "_REPO_ROOT", tmp_path)  # 06/10/2026: G0–G2 neo exports theo _REPO_ROOT, không theo cwd
    monkeypatch.setattr(sys, "argv", ["run_g1_auto.py", "--study", study, *them_args])
    CS.xoa_dem()
    with patch.object(G1, "search_for_effect_sizes", return_value=[]), \
            patch.object(G1, "export_docx_g1", return_value=None):
        try:
            G1.main()
        except SystemExit:
            pass
    return d, json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))


def test_g1_06_main_lay_loai_cau_hoi_tu_g0(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    assert cp["question_type"] == "descriptive" and cp["design"]["internal_code"] == "cross_sectional"
    assert cp["dac_ta_thiet_ke"]["question_type"] == "descriptive"


_G0_KHONG_RCT = {"pubmed_results": {"total_found": 0, "n_pmids": 0, "all_pmids": [], "n_sr": 0, "n_rct": 0,
                                     "n_guideline": 0, "n_observational": 0, "n_recent": 0, "counts_are_real": True,
                                     "counts_unavailable": []}}


def test_g1_06_main_khong_co_g0_thi_mac_dinh_nhung_mo_ho(tmp_path, monkeypatch):
    # Bằng chứng nền trống ⇒ suy luận tự nó KHÔNG mơ hồ (RCT); cờ mơ hồ chỉ đến từ việc loại câu hỏi là MẶC ĐỊNH.
    d, cp = _chay_main(tmp_path, monkeypatch, g0_ghi_de=_G0_KHONG_RCT)
    assert cp["question_type"] == "treatment" and cp["design"]["internal_code"] == "rct"
    assert cp["design"]["ambiguous"] is True


def test_g1_06_main_loai_cau_hoi_da_chot_thi_khong_mo_ho(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "therapy"}, g0_ghi_de=_G0_KHONG_RCT)
    assert cp["question_type"] == "treatment" and cp["design"]["ambiguous"] is False


# ── G1-07 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_07_ghim_go_co_mo_ho_va_lay_ly_do_pi():
    d = G1._apply_design_pin({"ambiguous": True, "rationale": "[CẦN XÁC NHẬN] suy luận cũ", "internal_code": "rct"},
                             "cohort", {"gate_params": {"G1": {"design_rationale": "Không ngẫu nhiên hoá được"}}})
    assert d["ambiguous"] is False and "Không ngẫu nhiên hoá được" in d["rationale"] and "[CẦN" not in d["rationale"]


# ── G1-08 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _a2_rct(estimand):
    meta = {"gate_params": {"G1": {"estimand": estimand}}} if estimand else {}
    design = G1._apply_design_pin(G1.infer_study_design("treatment", {}, "thử nghiệm X"), "rct", meta)
    return G1.generate_g1_artifact("thử nghiệm X", "S", "treatment", design, [], {}, "2026-10-04 10:00", meta=meta)


def test_g1_08_sap_rct_theo_estimand_da_khai():
    est = {"population": "Người lớn có bệnh Z", "treatment_condition": "X so với chuẩn", "variable": "Điểm Y",
           "intercurrent_events_strategy": "Hypothetical cho ngừng thuốc do tác dụng phụ",
           "population_summary_measure": "Chênh lệch trung bình"}
    a2 = _a2_rct(est)
    assert "treatment-policy estimand" not in a2
    assert ("Phân tích chính: theo estimand PI đã khai — chiến lược biến cố xen ngang: Hypothetical cho ngừng thuốc"
            in a2), "SAP §4 phải dựng từ estimand đã khai"
    assert "Biến cố xen ngang + chiến lược: Hypothetical" in a2
    trong = _a2_rct(None)
    assert "KHÔNG mặc định treatment-policy" in trong and "Phân tích chính: theo estimand PI đã khai" not in trong


# ── G1-09 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_09_xac_nhan_gan_dau_van_tay_va_ngay(tmp_path):
    meta = _da_chot()
    meta["gate_params"]["G1"]["follow_up_schedule"] = "Ban đầu và tuần 24"  # đổi quyết định SAU khi chốt
    h8 = _row(_evaluate(_build_case(tmp_path, meta=meta)), "G1-HUMAN-08")
    assert h8["status"] == "REVIEW" and "đã đổi" in h8["evidence"]
    meta = _confirmed_meta()
    meta["gate_params"]["G1"]["reviewed_at"] = "2099-12-31T00:00:00"
    assert _row(_evaluate(_build_case(tmp_path / "b", meta=_chot_g1(meta, _design()))), "G1-HUMAN-08")["status"] \
        == "REVIEW"
    h8 = _row(_evaluate(_build_case(tmp_path / "c", meta=_confirmed_meta())), "G1-HUMAN-08")
    assert h8["status"] == "REVIEW" and "kiểu cũ" in h8["evidence"]
    assert G1Q.dau_van_tay_g1(_confirmed_meta(), _design()) in h8["action"]


def test_g1_09_dau_khong_doi_khi_chi_doi_khoa_xac_nhan():
    m = _confirmed_meta()
    dau = G1Q.dau_van_tay_g1(m, _design())
    m["gate_params"]["G1"].update({"reviewed_at": "2026-08-01T00:00:00", "protocol_core_confirmed": False})
    assert G1Q.dau_van_tay_g1(m, _design()) == dau


# ── G1-11 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_11_rct_chua_khai_annex2_thi_review(tmp_path):
    meta = _confirmed_meta()
    meta["gate_params"]["G1"].pop("annex2")
    a2b = _row(_evaluate(_build_case(tmp_path, meta=_chot_g1(meta, _design()))), "G1-AUTO-02b")
    assert a2b["status"] == "REVIEW" and "chưa khai" in a2b["evidence"]
    assert A2X.evaluate({}, "rct", "G1")["status"] == "NEEDS_DECLARATION"
    assert "annex2" in GC._GATE_PARAMS_SKELETON["G1"]


# ── G1-02 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
_KHOA_PHAM_VI_G1 = ("team_roles", "background_problem", "evidence_summary", "knowledge_gap", "benefit_risk_rationale",
                    "study_schema_timeline", "intervention_dose_adherence", "stopping_rescue_rules",
                    "critical_to_quality", "monitoring_plan", "randomisation", "allocation_concealment", "blinding")


def _loi(meta):
    return G1Q.build_protocol_core(study="S", topic="thử nghiệm X", design=_design(), meta=meta,
                                   generated_at="2026-10-04")


def test_g1_02_dong_pham_vi_g1_con_trong_bi_dem_dong_hoan_bo_qua():
    con = G1Q.o_trong_pham_vi_g1(_loi(_confirmed_meta()))
    noi = " ".join(con)
    assert "Chủ nhiệm, nhà phương pháp" in noi and "Tạo chuỗi ngẫu nhiên" in noi
    assert "Ở G2" not in noi and "Ở G3" not in noi and "Ở G9" not in noi, "dòng hoãn cho cổng sau không bị đếm"


def test_g1_02_dien_du_khoa_thi_khong_con_o_trong():
    meta = _confirmed_meta()
    g1 = meta["gate_params"]["G1"]
    for k in _KHOA_PHAM_VI_G1:
        g1[k] = "Nội dung PI điền (giá trị của test)"
    g1["research_question"] = "Ở người lớn có bệnh Z, X so với chuẩn có cải thiện Y?"
    g1["protocol_version"] = "1.2"
    g1["secondary_outcomes"] = ["Biến cố bất lợi đến tuần 12"]
    meta["gate_params"]["G0"] = {"test_type": "superiority", "hypothesis_h1": "X tốt hơn chuẩn",
                                 "expected_direction": "tăng"}
    assert G1Q.o_trong_pham_vi_g1(_loi(meta)) == []


def test_g1_02_khuon_co_khoa_va_g1_auto_07_review(tmp_path):
    for k in _KHOA_PHAM_VI_G1 + ("risk_register", "budget", "dau_van_tay_chot"):
        assert k in GC._GATE_PARAMS_SKELETON["G1"], k
    case = list(_build_case(tmp_path, meta=_da_chot()))
    case[4] = {**case[4], "A2": _loi(_confirmed_meta())}
    a7 = _row(_evaluate(tuple(case)), "G1-AUTO-07")
    assert a7["status"] == "REVIEW" and "dòng còn trống" in a7["evidence"]


# ── G1-03 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_03_risk_register_tu_study_meta_va_ngay_ra_khong_do_may_dien(tmp_path):
    case = _build_case(tmp_path, meta=_da_chot())
    a13b = case[4]["A13b"]
    assert "[CẦN NGƯỜI RÀ]" in a13b and "2026-07-27" not in a13b.split("## Quy tắc")[0]
    meta = _da_chot()
    meta["gate_params"]["G1"]["risk_register"] = [{"id": "R-01", "loai": "Tuyển mẫu", "rui_ro": "Chậm tuyển",
                                                   "xac_suat": "Trung bình", "tac_dong": "Cao", "trang_thai": "Mở",
                                                   "ngay_ra": "2026-09-30"}]
    a13b = _build_case(tmp_path / "b", meta=meta)[4]["A13b"]
    assert "| R-01 | Tuyển mẫu | Chậm tuyển |" in a13b and "2026-09-30" in a13b and "G1-R01" not in a13b


def test_g1_03_sao_luu_ban_sua_tay_truoc_khi_ghi_de(tmp_path):
    import hashlib
    p = tmp_path / "G1_A13b_RISK_REGISTER_S.md"
    p.write_text("bản máy sinh\n", encoding="utf-8", newline="\n")
    sha_sinh = hashlib.sha256(p.read_bytes()).hexdigest()
    assert G1Q.sao_luu_neu_sua_tay(p, sha_sinh) is None, "chưa ai sửa ⇒ không sao lưu"
    p.write_text("bản PI sửa tay\n", encoding="utf-8", newline="\n")
    bak = G1Q.sao_luu_neu_sua_tay(p, sha_sinh)
    assert bak is not None and bak.read_text(encoding="utf-8") == "bản PI sửa tay\n"


# ── G1-05 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_05_resolve_design_code_canh_bao_pin_bi_tu_choi(tmp_path):
    (tmp_path / "G1_checkpoint.json").write_text(json.dumps({"design": {
        "internal_code": "cohort", "pin_bi_tu_choi": "quality_improvement"}}), encoding="utf-8", newline="\n")
    ma, canh_bao = GC.resolve_design_code(tmp_path)
    assert canh_bao and "quality_improvement" in canh_bao and "ĐANG CHẶN" in canh_bao


# ── G1-10 / CHUNG-F ────────────────────────────────────────────────────────────────────────────────────────────────
def test_g1_10_evaluate_study_va_cham_song_qua_cong_song(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    assert set(SK.DAC_TA_KHOA) <= set(cp["dac_ta_thiet_ke"]) and cp["dac_ta_thiet_ke"]["dau_van_tay"]
    assert cp["dau_gate_params_g1"]
    assert SK.dac_ta_thiet_ke(d)["nguon"] == "g1_khoa"
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=False)
    assert r["status"] in (G1Q.STATUS_DRAFT_READY, G1Q.STATUS_BLOCKED) and r["dau_van_tay_hien_tai"]
    CS.xoa_dem()
    song = CS.trang_thai_song("G1", "TEST-G1-MAIN", d)
    assert song["nguon"] == CS.NGUON_SONG and song["status"] == r["status"]


def test_g1_10_evaluate_study_khong_co_checkpoint_la_blocked(tmp_path):
    (tmp_path / "study_meta.json").write_text("{}", encoding="utf-8", newline="\n")
    assert G1Q.evaluate_study("X", tmp_path, write=False)["status"] == G1Q.STATUS_BLOCKED


def test_g1_10_evaluate_study_giu_manifest_luc_sinh(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    luc_sinh = json.loads((d / "G1_QUALITY_REPORT.json").read_text(encoding="utf-8"))["artifact_manifest_luc_sinh"]
    a13b = d / "G1_A13b_RISK_REGISTER_TEST-G1-MAIN.md"
    a13b.write_text(a13b.read_text(encoding="utf-8") + "\nPI ghi thêm\n", encoding="utf-8", newline="\n")
    G1Q.evaluate_study("TEST-G1-MAIN", d, write=True)
    sau = json.loads((d / "G1_QUALITY_REPORT.json").read_text(encoding="utf-8"))["artifact_manifest_luc_sinh"]
    assert sau == luc_sinh, "chấm lại không được ghi đè mốc lúc sinh (nếu không, lượt sinh sau sẽ đè mất bản sửa tay)"


def test_g2_cung_giu_review_khi_rct_chua_khai_annex2():
    import g2_quality_gate as G2Q
    src = [x.strip() for x in Path(G2Q.__file__).read_text(encoding="utf-8").splitlines()]
    assert '{"BLOCK": "BLOCK", "NEEDS_DECLARATION": "REVIEW"}.get(annex2["status"], "PASS"),' in src


def test_khong_sua_meta_goc():
    m = _confirmed_meta()
    goc = copy.deepcopy(m)
    G1Q.dau_van_tay_g1(m, _design())
    assert m == goc


# ── G1-03 (luồng thật): sinh lại không được đè mất bản PI sửa tay ─────────────────────────────────────────────────
@pytest.mark.parametrize("cham_lai_giua_chung", [False, True])
def test_g1_03_sinh_lai_sao_luu_ban_sua_tay(tmp_path, monkeypatch, cham_lai_giua_chung):
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    a2 = d / "G1_A2_PROTOCOL_DESIGN_TEST-G1-MAIN.md"
    a13b = d / "G1_A13b_RISK_REGISTER_TEST-G1-MAIN.md"
    assert a2.is_file() and a13b.is_file()
    for p in (a2, a13b):
        p.write_text(p.read_text(encoding="utf-8") + "\nPI SỬA TAY — không được mất\n", encoding="utf-8", newline="\n")
    if cham_lai_giua_chung:  # chấm lại (ghi báo cáo) giữa lúc sửa tay và lúc sinh lại — mốc lúc sinh phải còn
        G1Q.evaluate_study("TEST-G1-MAIN", d, write=True)
    _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    for p in (a2, a13b):
        baks = sorted(d.glob(p.name + ".bak-*"))
        assert baks, f"thiếu bản sao lưu cho {p.name}"
        assert "PI SỬA TAY — không được mất" in baks[-1].read_text(encoding="utf-8")
        assert "PI SỬA TAY" not in p.read_text(encoding="utf-8"), "bản mới sinh không mang phần sửa tay"


def test_g1_03_sinh_lai_khi_khong_ai_sua_thi_khong_sao_luu(tmp_path, monkeypatch):
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    assert not list(d.glob("*.bak-*"))


# ── G1-04 (luồng thật): main và evaluate_study chấm SỐNG G0, không tin bản lưu ──────────────────────────────────
def test_g1_04_main_va_evaluate_study_cham_song_g0(tmp_path, monkeypatch):
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"}, g0_luu="PASS_G0_CONFIRMED")
    rep = json.loads((d / "G1_QUALITY_REPORT.json").read_text(encoding="utf-8"))
    a1 = _row(rep, "G1-AUTO-01")
    assert a1["status"] == "REVIEW" and "bản LƯU=PASS_G0_CONFIRMED" in a1["evidence"], a1
    CS.xoa_dem()
    a1 = _row(G1Q.evaluate_study("TEST-G1-MAIN", d, write=False), "G1-AUTO-01")
    assert a1["status"] == "REVIEW" and "bản LƯU=PASS_G0_CONFIRMED" in a1["evidence"], a1


# ── G1-10: chấm lại ghi dấu lúc chấm vào checkpoint (để nơi tiêu thụ biết bản lưu còn khớp nội dung không) ────────
def test_g1_10_evaluate_study_luu_dau_luc_cham(tmp_path, monkeypatch):
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=True)
    cp = json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["quality_gate"]["dau_van_tay_luc_cham"] == r["dau_van_tay_hien_tai"]
    assert cp["quality_gate"]["status"] == r["status"]


# ── G1-12 (phía sinh): run_g1_auto dùng CÙNG bảng bí danh với cổng ───────────────────────────────────────────────
@pytest.mark.parametrize("ghim,ma", [("Randomised", "rct"), ("dta", "diagnostic"), ("Cắt ngang", "cross_sectional"),
                                     ("randomised controlled trial", "rct"), ("qualitative study", "qualitative")])
def test_g1_12_run_g1_dung_bang_bi_danh_chung(ghim, ma):
    assert G1._canonicalize_pinned_design_code(ghim) == ma
    assert SK.ma_thiet_ke_chuoi(ghim) == ma


# ── G1-03 chuyển tiếp: báo cáo kiểu cũ chưa có mốc LÚC SINH ⇒ không đoán «chưa ai sửa» ─────────────────────────────
def test_g1_03_bao_cao_kieu_cu_van_sao_luu_ban_sua_tay(tmp_path, monkeypatch):
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    a13b = d / "G1_A13b_RISK_REGISTER_TEST-G1-MAIN.md"
    a13b.write_text(a13b.read_text(encoding="utf-8") + "\nPI SỬA TAY\n", encoding="utf-8", newline="\n")
    # Mô phỏng báo cáo kiểu cũ: không có mốc lúc sinh; artifact_manifest được tính SAU khi đã sửa tay.
    rp = d / "G1_QUALITY_REPORT.json"
    rep = json.loads(rp.read_text(encoding="utf-8"))
    rep.pop("artifact_manifest_luc_sinh", None)
    import hashlib
    rep["artifact_manifest"]["A13b"]["sha256"] = hashlib.sha256(a13b.read_bytes()).hexdigest()
    rp.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert G1Q._manifest_luot_truoc(d) == {}, "artifact_manifest kiểu cũ không được dùng làm mốc lúc sinh"
    G1Q.evaluate_study("TEST-G1-MAIN", d, write=True)
    assert json.loads(rp.read_text(encoding="utf-8"))["artifact_manifest_luc_sinh"] == {}, \
        "chấm lại không được nâng manifest hiện hành thành mốc lúc sinh"
    _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    baks = list(d.glob(a13b.name + ".bak-*"))
    assert baks and "PI SỬA TAY" in baks[0].read_text(encoding="utf-8")
    assert not list(d.glob("G1_A1b_PROJECT_CHARTER_TEST-G1-MAIN.md.bak-*")), "tệp không đổi thì không sao lưu"


def test_g1_03_sao_luu_khong_de_nhau_trong_cung_mot_giay(tmp_path):
    p = tmp_path / "A.md"
    p.write_text("một\n", encoding="utf-8", newline="\n")
    b1 = G1Q.sao_luu_neu_sua_tay(p, "0" * 64)
    p.write_text("hai\n", encoding="utf-8", newline="\n")
    b2 = G1Q.sao_luu_neu_sua_tay(p, "0" * 64)
    assert b1 != b2 and b1.read_text(encoding="utf-8") == "một\n" and b2.read_text(encoding="utf-8") == "hai\n"


# ── G1-10: CLI chấm lại MẶC ĐỊNH chỉ in — chạy trên đề tài thật không được đổi tệp exports/ ───────────────────────
def test_g1_10_cli_mac_dinh_khong_ghi_chi_ghi_khi_co_co(tmp_path, monkeypatch):
    import hashlib
    import subprocess
    d, _ = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    cli = tmp_path / "tools" / "g1_quality_gate.py"  # CLI tìm exports/ theo vị trí tệp ⇒ chạy bản chép trong tmp
    cli.parent.mkdir()
    cli.write_bytes(Path(G1Q.__file__).read_bytes())
    tep = [d / "G1_QUALITY_REPORT.json", d / "G1_QUALITY_REPORT.md", d / "G1_checkpoint.json"]

    def bam():
        return [hashlib.sha256(p.read_bytes()).hexdigest() for p in tep]

    truoc = bam()
    env = {**__import__("os").environ, "PYTHONPATH": str(Path(G1Q.__file__).parent)}
    r = subprocess.run([sys.executable, "-B", str(cli), "--study", "TEST-G1-MAIN"], capture_output=True, text=True,
                       env=env, timeout=120)
    assert "G1 QUALITY" in r.stdout and "chỉ in, không ghi" in r.stdout, r.stdout + r.stderr
    assert bam() == truoc, "CLI mặc định đã ghi vào exports/"
    r = subprocess.run([sys.executable, "-B", str(cli), "--study", "TEST-G1-MAIN", "--ghi"], capture_output=True,
                       text=True, env=env, timeout=120)
    assert "đã ghi báo cáo/checkpoint" in r.stdout, r.stdout + r.stderr
    assert bam() != truoc, "--ghi phải lưu kết quả chấm lại"
