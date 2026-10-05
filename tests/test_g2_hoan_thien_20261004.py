# -*- coding: utf-8 -*-
"""Hoàn thiện cổng G2 (soát từng cổng G0–G10, 04/10/2026) — mỗi test neo vào MỘT phát hiện đã được phản biện xác nhận.

G2-02 liêm chính trên NỘI DUNG HIỆN HÀNH · G2-03 kế hoạch an toàn RCT riêng + PI xác nhận · G2-04 ICF RCT đủ yếu tố
đồng thuận của thử nghiệm can thiệp · G2-05 thiết kế G1 hiện hành/G1 chấm sống · G2-07 WHO TRDS một bảng, mục khoa học
của bản .md dựng từ bản JSON, masking không in cứng, mục 9/12 do PI khai · G2-08 dấu đầu vào lúc ký + phiên bản do PI
khai · G2-10 ICF chẩn đoán có thủ thuật/mẫu sinh học · G2-11 ICF tiếng Anh cùng tập mục · G2-12 mọi tiêu chí tự động
lái trạng thái · G2-13 ô «sau khi kết thúc nghiên cứu» không chặn ký · G7-03 phía G2 (xoá trường khoá khi tụt) ·
G8-16 phía G2 (trình-ký liệt kê tiêu chí người). Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import g2_quality_gate as G2Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g2_auto as R  # noqa: E402
import trinh_ky_cong as TK  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402
from test_g2_quality_gate import (  # noqa: E402
    _attestation,
    _evaluate,
    _ke_hoach_an_toan_day_du,
    _meta,
    _package,
)

THIET_KE = ("rct", "cohort", "case_control", "cross_sectional", "diagnostic", "sr_ma", "prediction", "qualitative")


def _row(r, tid):
    return next(c for c in r["automatic_criteria"] + r["human_approval_criteria"] if c["id"] == tid)


def _sinh(design, meta=None, n=0):
    doc = R.generate_g2_full_package(
        topic="Can thiệp X ở người trưởng thành", study_name="S", design_code=design, design_primary=f"TK {design}",
        reporting_std="X", n_sr=0, n_rct=0, evidence_level="", registry=None, risk=R.get_risk_profile(design, ""),
        run_date="2026-10-04 10:00", n_adjusted=n, meta=meta if meta is not None else {})
    return R._VNSTYLE.clean_generated_prose(doc)


def _cham_voi_meta(tmp_path, meta, package_text=None):
    """Như _evaluate của test_g2_quality_gate nhưng bản đăng ký WHO TRDS dựng từ CHÍNH meta truyền vào."""
    study = "TEST-G2"
    tmp_path.mkdir(parents=True, exist_ok=True)
    pp = tmp_path / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    pp.write_text(package_text or _package(), encoding="utf-8", newline="\n")
    (tmp_path / G2Q.ten_ke_hoach_an_toan(study)).write_text(_ke_hoach_an_toan_day_du(study), encoding="utf-8",
                                                           newline="\n")
    rp = G2Q.build_registration_draft(study=study, topic="Can thiệp X ở người trưởng thành", design_code="rct",
                                      design_primary="RCT", risk={"registration": "x", "register_where": "y"},
                                      n_target=200, out_dir=tmp_path, generated_at="2026-07-27T10:00:00", meta=meta)
    return G2Q.evaluate_g2_quality(study=study, design_code="rct", package_path=pp, registration_path=rp,
                                   g1_checkpoint={"quality_gate": {"status": "PASS_G1_CONFIRMED"}}, meta=meta,
                                   guardrail_passed=True, ledger_approved=False, today=date(2026, 7, 27))


def test_duong_pass_van_dat_duoc(tmp_path):
    base = _package()
    r = _evaluate(tmp_path, G2Q.append_attestation(base, _attestation("TEST-G2", base)), ledger=True)
    assert r["status"] == G2Q.STATUS_APPROVED, [c for c in r["automatic_criteria"] if c["status"] != "PASS"]


# ── G2-02 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g2_02_pii_chen_sau_khi_sinh_bi_chan_du_guardrail_luu_pass(tmp_path):
    r = _evaluate(tmp_path, _package() + "\nNgười tham gia số 1 — CCCD 012345678901\n", ledger=False)
    a1 = _row(r, "G2-AUTO-01")
    assert a1["status"] == "BLOCK" and "R1" in a1["evidence"] and "012345678901" not in a1["evidence"]
    assert r["status"] == G2Q.STATUS_BLOCKED


@pytest.mark.parametrize("chen,luat", [
    ("\nSố IRB: HDDD-2026-999\n", "R2"),
    ("\nAPPROVED_EXTERNALLY\n", "R3"),
    ("\nTrạng thái hiện tại: LOCKED\n", "R3"),
])
def test_g2_02_r2_r3_tren_noi_dung_hien_hanh(tmp_path, chen, luat):
    a1 = _row(_evaluate(tmp_path, _package() + chen, ledger=False), "G2-AUTO-01")
    assert a1["status"] == "BLOCK" and luat in a1["evidence"], a1


def test_g2_02_thieu_disclaimer_la_r7():
    loi = G2Q.kiem_liem_chinh_noi_dung(_package().replace("Cần bác sĩ kiểm chứng", ""))
    assert any(x.startswith("R7") for x in loi)


def test_g2_02_so_irb_that_trung_attestation_duoc_mien(tmp_path):
    base = _package() + "\nSố IRB: IRB-2026-001\n"
    r = _evaluate(tmp_path, G2Q.append_attestation(base, _attestation("TEST-G2", base)), ledger=True)
    assert _row(r, "G2-AUTO-01")["status"] == "PASS"
    assert r["status"] == G2Q.STATUS_APPROVED


def test_g2_02_khong_doi_nhan_draft_hay_so_o_can(tmp_path):
    """R4 (≥5 nhãn DRAFT) và R5 (≥10 ô [CẦN]) phạt chính việc hoàn thiện — không còn lái G2-AUTO-01."""
    assert "DRAFT" not in _package() and "[CẦN" not in _package()
    assert _row(_evaluate(tmp_path, _package(), ledger=False), "G2-AUTO-01")["status"] == "PASS"


# ── G2-03 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _cham_an_toan(tmp_path, design="rct", noi_dung=None, meta=None):
    if noi_dung is not None:
        (tmp_path / G2Q.ten_ke_hoach_an_toan("S")).write_text(noi_dung, encoding="utf-8", newline="\n")
    return G2Q.kiem_ke_hoach_an_toan(tmp_path, "S", design, _meta() if meta is None else meta)


def test_g2_03_rct_phai_co_ke_hoach_an_toan_rieng(tmp_path):
    st, ev = _cham_an_toan(tmp_path)
    assert st == "REVIEW" and "thiếu G2_SAFETY_PLAN_S.md" in ev
    st, ev = _cham_an_toan(tmp_path, noi_dung=G2Q.khung_ke_hoach_an_toan("S"))
    assert st == "REVIEW" and "mục 1 còn trống" in ev, "khung máy dựng (còn [CẦN]) chưa phải kế hoạch an toàn"
    meta = copy.deepcopy(_meta())
    meta["gate_params"]["G2"]["safety_plan_confirmed"] = False
    st, ev = _cham_an_toan(tmp_path, noi_dung=_ke_hoach_an_toan_day_du("S"), meta=meta)
    assert st == "REVIEW" and "safety_plan_confirmed" in ev
    assert _cham_an_toan(tmp_path, noi_dung=_ke_hoach_an_toan_day_du("S"))[0] == "PASS"


def test_g2_03_thieu_mot_muc_bi_bat(tmp_path):
    van = _ke_hoach_an_toan_day_du("S").replace("## 3. Quy tắc dừng", "## Ghi chú khác")
    st, ev = _cham_an_toan(tmp_path, noi_dung=van)
    assert st == "REVIEW" and "Quy tắc dừng" in ev


def test_g2_03_khong_phai_rct_chi_khi_pi_khai_bat_buoc(tmp_path):
    assert _cham_an_toan(tmp_path, design="cohort")[0] == "PASS"
    meta = copy.deepcopy(_meta())
    meta["gate_params"]["G2"]["safety_plan_required"] = True
    assert _cham_an_toan(tmp_path, design="cohort", meta=meta)[0] == "REVIEW"


def test_g2_03_tieu_chi_khong_con_do_chuoi_tren_ca_ho_so(tmp_path):
    r = _evaluate(tmp_path, _package(), ledger=False)
    assert _row(r, "G2-AUTO-07")["status"] == "PASS"
    (tmp_path / G2Q.ten_ke_hoach_an_toan("TEST-G2")).unlink()
    r2 = G2Q.evaluate_g2_quality(
        study="TEST-G2", design_code="rct", package_path=tmp_path / "G2_A3_ETHICS_PACKAGE_TEST-G2.md",
        registration_path=tmp_path / "G2_REGISTRATION_DRAFT_TEST-G2.json", g1_checkpoint={}, meta=_meta(),
        guardrail_passed=True, ledger_approved=False, today=date(2026, 7, 27))
    assert "AE/SAE" in _package() and _row(r2, "G2-AUTO-07")["status"] == "REVIEW"


# ── G2-04 / G2-10 / G2-11 ──────────────────────────────────────────────────────────────────────────────────────────
def test_g2_04_icf_rct_co_du_muc_ich_va_ngoai_le_truy_cap():
    doc = _sinh("rct", {"gate_params": {"G1": {"blinding": "Double blind"}}})
    vi = G2Q.nhan_muc_icf(G2Q.khoi_tai_lieu(doc, 4))
    assert set(G2Q.NHAN_ICF_RCT) <= vi
    tl4 = G2Q.khoi_tai_lieu(doc, 4)
    assert "NGOẠI LỆ ở mục 5b" in tl4 and "giám sát viên" in tl4
    assert G2Q.kiem_icf(doc, "rct") == ([], [])


def test_g2_04_quan_sat_khong_bi_doi_muc_rct():
    doc = _sinh("cross_sectional")
    assert not (set(G2Q.NHAN_ICF_RCT) & G2Q.nhan_muc_icf(G2Q.khoi_tai_lieu(doc, 4)))
    assert G2Q.kiem_icf(doc, "cross_sectional") == ([], [])
    assert "NGOẠI LỆ ở mục 5b" not in doc


def test_g2_04_ho_so_rct_thieu_muc_6g_bi_chan(tmp_path):
    van = _package().replace("6g. THEO DÕI KHI NGỪNG HOẶC RÚT", "THEO DÕI KHI NGỪNG HOẶC RÚT")
    a3 = _row(_evaluate(tmp_path, van, ledger=False), "G2-AUTO-03")
    assert a3["status"] == "BLOCK" and "6g" in a3["evidence"]


def test_g2_04_chi_khop_nhan_dau_dong():
    khoi = "Ghi chú: xem 6g. THEO DÕI ở phụ lục\n1. MỤC ĐÍCH\n"
    assert G2Q.nhan_muc_icf(khoi) == {"1"}


def test_g2_10_icf_chan_doan_co_thu_thuat_va_mau_sinh_hoc():
    doc = _sinh("diagnostic")
    tl4 = G2Q.khoi_tai_lieu(doc, 4)
    assert "index test" in tl4 and "reference standard" in tl4
    assert "6e" in G2Q.nhan_muc_icf(tl4)
    assert "KHÔNG có can thiệp/thủ thuật y khoa nào thực hiện thêm" not in tl4
    assert "6e" not in G2Q.nhan_muc_icf(G2Q.khoi_tai_lieu(_sinh("cross_sectional"), 4))


@pytest.mark.parametrize("che_do,co_6e", [("PROSPECTIVE_NEW_PARTICIPANTS", True),
                                          ("RETROSPECTIVE_SECONDARY_DATA", False)])
def test_g2_10_prediction_tuyen_moi_moi_co_muc_mau_sinh_hoc(che_do, co_6e):
    doc = _sinh("prediction", {"gate_params": {"G2": {"recruitment_mode": che_do}}})
    assert ("6e" in G2Q.nhan_muc_icf(G2Q.khoi_tai_lieu(doc, 4))) is co_6e


@pytest.mark.parametrize("design", THIET_KE)
def test_g2_11_icf_tieng_anh_cung_tap_muc(design):
    doc = _sinh(design)
    vi, en = (G2Q.nhan_muc_icf(G2Q.khoi_tai_lieu(doc, so)) for so in (4, 5))
    assert vi and vi == en, (design, sorted(vi ^ en))


def test_g2_11_lech_ban_tieng_anh_la_review(tmp_path):
    van = _package().replace("1b. SECTION 1B", "SECTION 1B")
    a3b = _row(_evaluate(tmp_path, van, ledger=False), "G2-AUTO-03b")
    assert a3b["status"] == "REVIEW" and "1b" in a3b["evidence"]


# ── G2-07 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _ban_json(tmp_path, design, meta):
    path = G2Q.build_registration_draft(study="S", topic="Đề tài khoa học X", design_code=design, design_primary="TK",
                                        risk={"registration": "x", "register_where": "y"}, n_target=100,
                                        out_dir=tmp_path, generated_at="2026-10-04T10:00:00", meta=meta)
    return json.loads(path.read_text(encoding="utf-8"))


def _muc(doc, so):
    return next(i["value"] for i in doc["items"] if i["number"] == so)


def test_g2_07_rct_chua_khai_masking_khong_in_blinded(tmp_path):
    doc = _sinh("rct")
    dong15 = doc.split("Trường 15")[1].split("Trường 16")[0]
    assert "Blinded" not in dong15 and "[CẦN" in dong15
    assert "Double blind" in _sinh("rct", {"gate_params": {"G1": {"blinding": "Double blind"}}})
    gaps = G2Q.registration_pi_confirmation_gaps(_ban_json(tmp_path, "rct", {}), "rct")
    assert any("#15" in g for g in gaps)


@pytest.mark.parametrize("design", THIET_KE)
def test_g2_07_muc_dich_chinh_md_trung_json(tmp_path, design):
    doc = _sinh(design)
    j = _ban_json(tmp_path, design, {})
    dong15 = doc.split("Trường 15")[1].split("Trường 16")[0]
    assert _muc(j, 15)["primary_purpose"] in dong15 and _muc(j, 15)["design"] in dong15


def test_g2_07_muc_khoa_hoc_md_dung_tu_du_kien_ghim(tmp_path):
    meta = {"gate_params": {"G1": {"inclusion_criteria": ["Người lớn từ 18 tuổi"], "exclusion_criteria": ["Mang thai"],
                                   "intervention_or_exposure": "Can thiệp X", "comparator": "Chăm sóc chuẩn",
                                   "blinding": "Open label"},
                            "G2": {"public_title": "X có giúp người lớn khỏe hơn", "health_condition": "Bệnh Y"}}}
    doc = _sinh("rct", meta)
    for chuoi in ("Người lớn từ 18 tuổi", "Mang thai", "Chăm sóc chuẩn", "X có giúp người lớn khỏe hơn", "Bệnh Y"):
        assert chuoi in doc, chuoi
    assert G2Q.registration_pi_confirmation_gaps(_ban_json(tmp_path, "rct", meta), "rct") == []


def test_g2_07_muc_9_12_chep_ten_de_tai_la_review(tmp_path):
    meta = copy.deepcopy(_meta())
    for k in ("public_title", "health_condition"):
        meta["gate_params"]["G2"].pop(k)
    r = _cham_voi_meta(tmp_path, meta)
    a8b = _row(r, "G2-AUTO-08b")
    assert a8b["status"] == "REVIEW" and "#9" in a8b["evidence"] and "#12" in a8b["evidence"]


# ── G2-08 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _thu_muc_ky(tmp_path):
    d = tmp_path / "exports" / "S-KY"
    meta = dung_g0_g1_da_chot(d, "S-KY", them_meta={"G2": dict(_meta()["gate_params"]["G2"])})
    (d / "G3_checkpoint.json").write_text(json.dumps({"confirmed_n": 200}), encoding="utf-8", newline="\n")
    return d, meta


def _loi_attest(d, meta, **them):
    base = _package()
    att = _attestation("S-KY", base, meta=meta, out_dir=d, **them)
    return G2Q.validate_attestation(attestation=att, package_text=G2Q.append_attestation(base, att), study="S-KY",
                                    design_code="rct", meta=meta, today=date(2026, 7, 27), out_dir=d)


def test_g2_08_dau_dau_vao_khop_thi_khong_loi(tmp_path):
    d, meta = _thu_muc_ky(tmp_path)
    assert not [e for e in _loi_attest(d, meta) if "dấu" in e]


def test_g2_08_sua_de_cuong_sau_khi_ky_mat_hieu_luc(tmp_path):
    d, meta = _thu_muc_ky(tmp_path)
    base = _package()
    att = _attestation("S-KY", base, meta=meta, out_dir=d)
    meta2 = copy.deepcopy(meta)
    meta2["gate_params"]["G1"]["inclusion_criteria"].append("Tiêu chí thêm sau khi Hội đồng duyệt")
    loi = G2Q.validate_attestation(attestation=att, package_text=G2Q.append_attestation(base, att), study="S-KY",
                                   design_code="rct", meta=meta2, today=date(2026, 7, 27), out_dir=d)
    assert any("đã đổi SAU khi Hội đồng duyệt" in e for e in loi)


def test_g2_08_doi_co_mau_g3_sau_khi_ky_mat_hieu_luc(tmp_path):
    d, meta = _thu_muc_ky(tmp_path)
    base = _package()
    att = _attestation("S-KY", base, meta=meta, out_dir=d)
    (d / "G3_checkpoint.json").write_text(json.dumps({"confirmed_n": 260}), encoding="utf-8", newline="\n")
    loi = G2Q.validate_attestation(attestation=att, package_text=G2Q.append_attestation(base, att), study="S-KY",
                                   design_code="rct", meta=meta, today=date(2026, 7, 27), out_dir=d)
    assert any("đã đổi SAU khi Hội đồng duyệt" in e for e in loi)


def test_g2_08_attestation_kieu_cu_khong_dau_phai_ky_lai(tmp_path):
    d, meta = _thu_muc_ky(tmp_path)
    loi = _loi_attest(d, meta, dau_dau_vao=None)
    assert any("kiểu cũ" in e for e in loi)


def test_g2_08_hop_dong_gate_contract_so_dau_dau_vao(tmp_path):
    d, meta = _thu_muc_ky(tmp_path)
    base = _package()
    att = _attestation("S-KY", base, meta=meta, out_dir=d)
    (d / "G2_A3_ETHICS_PACKAGE_S-KY.md").write_text(G2Q.append_attestation(base, att), encoding="utf-8",
                                                    newline="\n")
    cp = {"quality_contract_version": "G2-2026.1", "quality_gate": {"status": "PASS_G2_APPROVED"},
          "g2_approval_valid_until": "2027-07-20", "g2_protocol_version": "2.1", "g2_icf_version": "2.0"}
    assert GC._g2_signed_attestation_state("S-KY", d, meta) is not False
    (d / "G3_checkpoint.json").write_text(json.dumps({"confirmed_n": 999}), encoding="utf-8", newline="\n")
    assert GC._g2_signed_attestation_state("S-KY", d, meta) is False
    assert GC.g2_quality_contract_satisfied(cp, meta, study="S-KY", out_dir=d) is False


def test_g2_08_khuon_khong_gieo_phien_ban_va_auto10(tmp_path):
    assert GC._GATE_PARAMS_SKELETON["G2"]["protocol_version"] is None
    assert GC._GATE_PARAMS_SKELETON["G2"]["icf_version"] is None
    meta = copy.deepcopy(_meta())
    meta["gate_params"]["G2"]["protocol_version"] = None
    a10 = _row(_evaluate(tmp_path, _package(), ledger=False, meta=meta), "G2-AUTO-10")
    assert a10["status"] == "REVIEW" and "protocol_version" in a10["evidence"]
    meta["gate_params"]["G2"].update({"protocol_version": "1.0", "icf_version": "1.0"})
    a10 = _row(_cham_voi_meta(tmp_path / "b", meta), "G2-AUTO-10")
    assert a10["status"] == "PASS" and "giá trị khuôn" in a10["evidence"]


def test_g2_08_mien_icf_khong_doi_icf_version(tmp_path):
    meta = copy.deepcopy(_meta())
    meta["gate_params"]["G2"].update({"icf_version": None, "icf_waiver_requested": True})
    assert _row(_evaluate(tmp_path, _package(), ledger=False, meta=meta), "G2-AUTO-10")["status"] == "PASS"


# ── G2-05 / G1-10 phía tiêu thụ ────────────────────────────────────────────────────────────────────────────────────
def _thu_muc_g2(tmp_path, *, thiet_ke_g2="rct", chot_g1=True):
    study = "S-G2"
    d = tmp_path / "exports" / study
    meta = dung_g0_g1_da_chot(d, study, them_meta={"G2": dict(_meta()["gate_params"]["G2"])})
    if not chot_g1:
        meta["gate_params"]["G1"]["design_confirmed"] = False
        (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / f"G2_A3_ETHICS_PACKAGE_{study}.md").write_text(_package(), encoding="utf-8", newline="\n")
    (d / G2Q.ten_ke_hoach_an_toan(study)).write_text(_ke_hoach_an_toan_day_du(study), encoding="utf-8", newline="\n")
    G2Q.build_registration_draft(study=study, topic="Can thiệp X ở người trưởng thành", design_code=thiet_ke_g2,
                                 design_primary="TK", risk={"registration": "x", "register_where": "y"},
                                 n_target=200, out_dir=d, generated_at="2026-10-04T10:00:00", meta=_meta())
    (d / "G2_checkpoint.json").write_text(json.dumps({"study": study, "gate": "G2", "design_code": thiet_ke_g2,
                                                      "guardrail": {"passed": True}}), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    return d, study


def test_g2_05_thiet_ke_ho_so_lech_g1_da_xac_nhan_la_chan(tmp_path):
    d, study = _thu_muc_g2(tmp_path, thiet_ke_g2="cohort")
    r = G2Q.evaluate_study(study, d, write=False)
    a6b = _row(r, "G2-AUTO-06b")
    assert a6b["status"] == "BLOCK" and "cohort" in a6b["evidence"] and "rct" in a6b["evidence"]
    assert r["status"] == G2Q.STATUS_BLOCKED


def test_g2_05_lech_khi_g1_chua_xac_nhan_la_review(tmp_path):
    d, study = _thu_muc_g2(tmp_path, thiet_ke_g2="cohort", chot_g1=False)
    r = G2Q.evaluate_study(study, d, write=False)
    assert _row(r, "G2-AUTO-06b")["status"] == "REVIEW"
    a2 = _row(r, "G2-AUTO-02")
    assert a2["status"] == "REVIEW" and "chấm sống" in a2["evidence"]


def test_g2_05_khop_thiet_ke_va_g1_song_pass(tmp_path):
    d, study = _thu_muc_g2(tmp_path)
    r = G2Q.evaluate_study(study, d, write=False)
    assert _row(r, "G2-AUTO-06b")["status"] == "PASS"
    assert _row(r, "G2-AUTO-02")["status"] == "PASS" and "chấm sống" in _row(r, "G2-AUTO-02")["evidence"]


def test_g2_05_g1_ban_luu_pass_nhung_song_chua_dat(tmp_path):
    d, study = _thu_muc_g2(tmp_path, chot_g1=False)
    cp = json.loads((d / "G1_checkpoint.json").read_text(encoding="utf-8"))
    cp["quality_gate"] = {"status": "PASS_G1_CONFIRMED"}
    (d / "G1_checkpoint.json").write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    a2 = _row(G2Q.evaluate_study(study, d, write=False), "G2-AUTO-02")
    assert a2["status"] == "REVIEW" and "bản LƯU=PASS_G1_CONFIRMED" in a2["evidence"]


def test_g2_05_g1_song_bi_chan_thi_g2_chan(tmp_path):
    d, study = _thu_muc_g2(tmp_path)
    (d / "G1_A13b_RISK_REGISTER_S-G2.md").unlink()  # G1 mất artifact bắt buộc ⇒ G1 BLOCKED
    CS.xoa_dem()
    a2 = _row(G2Q.evaluate_study(study, d, write=False), "G2-AUTO-02")
    assert a2["status"] == "BLOCK"


def test_g2_05_khong_mac_dinh_cohort_khi_khong_biet_thiet_ke(tmp_path):
    d, study = _thu_muc_g2(tmp_path)
    (d / "G1_checkpoint.json").unlink()
    (d / "G2_checkpoint.json").write_text(json.dumps({"study": study, "gate": "G2"}), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    r = G2Q.evaluate_study(study, d, write=False)
    assert _row(r, "G2-AUTO-06b")["status"] == "BLOCK" and r["status"] == G2Q.STATUS_BLOCKED


# ── G2-12 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g2_12_moi_tieu_chi_tu_dong_lai_trang_thai(tmp_path):
    assert not hasattr(G2Q, "_NON_BLOCKING_CRITERIA")
    meta = copy.deepcopy(_meta())
    meta["gate_params"]["G1"]["secondary_outcomes"] = []
    meta["gate_params"]["G0"]["outcomes"] = []
    r = _cham_voi_meta(tmp_path, meta)
    assert _row(r, "G2-AUTO-08")["status"] == "REVIEW" and r["status"] == G2Q.STATUS_DRAFT


# ── G2-13 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g2_13_o_sau_khi_ket_thuc_nghien_cuu_khong_chan_ky():
    van = _package() + ("\nTrường 23 — Summary results:\n            [CẦN CẬP NHẬT sau nghiên cứu — ngày đăng kết "
                        "quả/tác phẩm,\n             protocol URL + phiên bản, participant flow, AE, outcomes]\n")
    phan = G2Q.classify_placeholders(van)
    assert len(phan["post_study"]) == 1 and not phan["pre_submission"] and not phan["post_approval"]
    assert G2Q.unresolved_critical_placeholders(van) == []


def test_g2_13_khuon_moi_muc_23_khong_mang_o_can():
    dong23 = _sinh("rct").split("Trường 23")[1].split("Trường 24")[0]
    assert "[CẦN" not in dong23 and "chỉ điền sau khi kết thúc nghiên cứu" in dong23


def test_g2_13_o_sau_phe_duyet_van_chan_ky():
    van = _package() + "\nSố phê duyệt IRB: [CẦN sau khi nhận]\n"
    assert G2Q.classify_placeholders(van)["post_approval"]
    assert G2Q.unresolved_critical_placeholders(van)


# ── G7-03 phía G2: tụt khỏi APPROVED thì xoá trường khoá ───────────────────────────────────────────────────────────
def test_g7_03_tut_trang_thai_xoa_truong_khoa(tmp_path):
    cp = tmp_path / "G2_checkpoint.json"
    cp.write_text(json.dumps({"g2_status": "LOCKED", "g2_irb_number": "IRB-1", "g2_approval_date": "2026-07-20",
                              "g2_protocol_version": "2.1", "g2_registration": "NCT1"}), encoding="utf-8",
                  newline="\n")
    G2Q.refresh_checkpoint(study="S", out_dir=tmp_path, report={"status": G2Q.STATUS_DRAFT},
                           quality_report_path=Path("r"))
    sau = json.loads(cp.read_text(encoding="utf-8"))
    assert sau["g2_status"] == "PENDING"
    for k in ("g2_irb_number", "g2_approval_date", "g2_protocol_version", "g2_registration"):
        assert k not in sau, k


# ── G8-16 phía G2: trợ lý trình-ký liệt kê cả tiêu chí NGƯỜI của G2 ──────────────────────────────────────────────────
def test_g8_16_trinh_ky_liet_ke_tieu_chi_nguoi_g2(tmp_path):
    r = _evaluate(tmp_path, _package(), ledger=False)
    ids = [m["id"] for m in TK.cac_tieu_chi(r)]
    assert "G2-HUMAN-01" in ids and "G2-AUTO-01" in ids and len(ids) == len(set(ids))


# ── run_g2_auto: khung kế hoạch an toàn chỉ ghi khi CHƯA có tệp ─────────────────────────────────────────────────────
def test_g2_03_run_g2_dung_khung_khong_ghi_de(tmp_path, monkeypatch):
    study = "S-RUN"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, them_meta={"G2": dict(_meta()["gate_params"]["G2"])})
    monkeypatch.chdir(tmp_path)

    def chay():
        monkeypatch.setattr(sys, "argv", ["run_g2_auto.py", "--study", study, "--skip-registry",
                                          "--regenerate-artifact"])
        CS.xoa_dem()
        try:
            R.main()
        except SystemExit:
            pass

    chay()
    kh = d / G2Q.ten_ke_hoach_an_toan(study)
    assert kh.read_text(encoding="utf-8") == G2Q.khung_ke_hoach_an_toan(study)
    kh.write_text(_ke_hoach_an_toan_day_du(study), encoding="utf-8", newline="\n")
    chay()
    assert kh.read_text(encoding="utf-8") == _ke_hoach_an_toan_day_du(study), "không được ghi đè bản chủ nhiệm"


def test_g2_08_g2_human_01_so_dau_dau_vao(tmp_path):
    base = _package()
    att = _attestation("TEST-G2", base, dau_dau_vao="0" * 16)
    r = _evaluate(tmp_path, G2Q.append_attestation(base, att), ledger=True)
    h1 = _row(r, "G2-HUMAN-01")
    assert h1["status"] == "REVIEW" and "đã đổi SAU khi Hội đồng duyệt" in h1["evidence"]
    assert r["status"] != G2Q.STATUS_APPROVED


def test_chung_f_run_g2_khong_g1_khong_design_la_mo_ho(tmp_path, monkeypatch):
    study = "S-KHONG-G1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_g2_auto.py", "--study", study, "--topic", "Đề tài thử", "--skip-registry"])
    CS.xoa_dem()
    try:
        R.main()
    except SystemExit:
        pass
    cp = json.loads((tmp_path / "exports" / study / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["design_code"] == "cohort" and cp["design_ambiguous"] is True
