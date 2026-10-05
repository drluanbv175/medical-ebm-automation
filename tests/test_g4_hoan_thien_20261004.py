# -*- coding: utf-8 -*-
"""Hoàn thiện cổng G4 — khoá SAP (soát từng cổng G0–G10, 04/10/2026). Mỗi test neo vào MỘT phát hiện đã được phản biện
xác nhận:

G4-01 mục bắt buộc VẮNG ⇒ chặn; thân §7/§8 rỗng ⇒ REVIEW · G4-02 §13–§15 bắt buộc cho SAP RCT (QĐ-1) · G4-03 estimand
G1 vào §4 SAP RCT + G4-AUTO-15 · G4-04 ≡ G3-05 G3 CHẤM SỐNG (G4-AUTO-12; run_g4_auto từ chối khi G3 bị chặn) · G4-05
N kế hoạch < N tối thiểu nói thật + giải trình (G4-AUTO-14; G3-AUTO-13 nhận giải trình) · G4-06 khung §12/chứng chỉ/
bảng giả theo thiết kế · G4-07 ký sau khoá dữ liệu; ngày sai dạng ISO · G4-08 §12 thiếu số; N §1/§12/chứng chỉ · G4-09
chứng chỉ khoá còn ô trống · G4-10 dòng phần mềm · G4-11 hướng dẫn khoá đúng cơ chế · CHUNG-C xác nhận G4 gắn dấu vân
tay (G4-HUMAN-08) và approve_gate đòi xác nhận người trước khi ký.

Luồng thật: chuỗi G0→G1 RCT đã chốt → run_g3_auto THẬT → xác nhận G3 gắn dấu (tests/_chuoi_da_chot.py) → run_g4_auto
THẬT. Luồng không ký chạy trong thư mục tạm (BASE trỏ tmp); luồng KÝ dùng exports/PYTEST-… của cây (approve_gate cố
định gốc) với khoá ký GIẢ trong thư mục tạm (EBM_GATE_KEY_PATH), dọn sạch sau test. Dữ liệu tổng hợp, không mạng.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
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
import g3_quality_gate as G3Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g4_auto as R4  # noqa: E402
from _chuoi_da_chot import (  # noqa: E402
    G3_THEO_THIET_KE,
    dien_sap_g4,
    dung_g0_g3_da_chot,
    xac_nhan_g4,
)
from test_g4_quality_gate import (  # noqa: E402
    _ESTIMAND,
    _checkpoint,
    _evaluate,
    _filled_comparative_sap,
    _fresh_sap,
    _g3_checkpoint,
    _meta,
    _row,
)


def _chay_g4(tmp_path, monkeypatch, study, **chuoi):
    """Dựng chuỗi G0→G3 (tmp) rồi chạy run_g4_auto.main() THẬT; trả (thư mục, mã thoát, stdout)."""
    d = tmp_path / "exports" / study
    dung_g0_g3_da_chot(d, study, **chuoi)
    monkeypatch.setattr(R4, "BASE", tmp_path)
    monkeypatch.setattr(sys, "argv", ["run_g4_auto.py", "--study", study])
    CS.xoa_dem()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = R4.main()
        except SystemExit as exc:
            rc = exc.code
    return d, (0 if rc is None else rc), buf.getvalue()


def _sap(d: Path, study: str) -> Path:
    return d / G4Q.sap_artifact_name(study)


def _cham(d: Path, study: str, base: Path) -> dict:
    CS.xoa_dem()
    return G4Q.evaluate_study(study, d, repo_root=base, write=False)


def _bo_muc(text: str, so: str) -> str:
    """Xoá TRỌN mục §N (tiêu đề + thân) — giả lập người sửa tay xoá mục."""
    lines = text.splitlines()
    dau = next(i for i, ln in enumerate(lines) if re.match(rf"^#{{2,3}}\s+{re.escape(so)}\b", ln))
    cuoi = next((j for j in range(dau + 1, len(lines))
                 if re.match(r"^#{2,3}\s+§\d", lines[j]) or re.match(r"^##\s+PHẦN", lines[j])), len(lines))
    return "\n".join(lines[:dau] + lines[cuoi:])


def _bo_than_muc(text: str, so: str) -> str:
    """Giữ tiêu đề §N, xoá toàn bộ thân."""
    lines = text.splitlines()
    dau = next(i for i, ln in enumerate(lines) if re.match(rf"^#{{2,3}}\s+{re.escape(so)}\b", ln))
    cuoi = next((j for j in range(dau + 1, len(lines))
                 if re.match(r"^#{2,3}\s+§\d", lines[j]) or re.match(r"^##\s+PHẦN", lines[j])), len(lines))
    return "\n".join(lines[:dau + 1] + [""] + lines[cuoi:])


# ── G4-01 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("so", ["§2", "§4", "§9"])
def test_g4_01_muc_bat_buoc_vang_bi_chan(so):
    text = _bo_muc(_filled_comparative_sap(design_code="cohort"), so)
    still = AG._g4_sections_still_draft(text, "cohort")
    assert any(s.startswith(so) and "VẮNG" in s for s in still), still
    r = _evaluate(artifact_text=text, checkpoint=_checkpoint(design_code="cohort"),
                  g3_checkpoint=_g3_checkpoint(design_code="cohort"))
    assert _row(r, "G4-AUTO-10")["status"] == "REVIEW" and r["status"] == G4Q.STATUS_DRAFT


def test_g4_01_vang_sach_van_bao_mot_lan():
    still = AG._g4_sections_still_draft("# không phải SAP\nchữ thường", "cohort")
    assert still and all("VẮNG SẠCH" in s for s in still)


@pytest.mark.parametrize("so,tieu_chi", [("§7", "G4-AUTO-07"), ("§8", "G4-AUTO-06")])
def test_g4_01_than_muc_7_8_rong_la_review(so, tieu_chi):
    text = _bo_than_muc(_filled_comparative_sap(), so)
    row = _row(_evaluate(artifact_text=text), tieu_chi)
    assert row["status"] == "REVIEW" and "không có nội dung" in row["evidence"], row


def test_g4_01_o_trong_khong_dau_cung_bi_bat():
    """CHUNG-B: «[CAN …]» (bỏ dấu) và «[TBD]» là ô trống — bản cũ chỉ so chuỗi «[CẦN»."""
    text = _filled_comparative_sap(design_code="cohort").replace(
        "- **Tiêu chí nhận:** Tuổi 18-75  ", "- **Tiêu chí nhận:** [CAN BAC SI DIEN]  ")
    assert any(s.startswith("§1") for s in AG._g4_sections_still_draft(text, "cohort"))
    text2 = _filled_comparative_sap(design_code="cohort").replace(
        "- **Kết cục chính:** Tỷ lệ nhập viện tim mạch trong 12 tháng  ", "- **Kết cục chính:** [TBD]  ")
    assert any(s.startswith("§2") for s in AG._g4_sections_still_draft(text2, "cohort"))


# ── G4-02 (QĐ-1) ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_02_rct_13_15_con_o_trong_khong_ky_duoc():
    text = _filled_comparative_sap()
    dau = text.index("### §14")
    text = text[:dau] + "### §14 HỘI ĐỒNG THEO DÕI DỮ LIỆU\n\n- **Có DMC/DSMB:** [CẦN — có/không]  \n\n" + \
        text[text.index("### §15"):]
    still = AG._g4_sections_still_draft(text, "rct")
    assert [s for s in still if s.startswith("§14")], still
    r = _evaluate(artifact_text=text, ledger_signed=False, ledger_reason="chưa ký")
    assert r["status"] == G4Q.STATUS_DRAFT


def test_g4_02_sap_rct_da_ky_truoc_moc_khong_ha_cap_vi_13_15(monkeypatch):
    monkeypatch.setattr(AG, "_g4_sections_still_draft", lambda _t, _d=None: ["§13 (Phân tích giữa kỳ)"])
    r = _evaluate()
    row = _row(r, "G4-AUTO-10")
    assert row["status"] == "REVIEW" and "amendment" in row["evidence"]
    assert r["status"] == G4Q.STATUS_LOCKED


def test_g4_02_approve_gate_rct_xoa_han_13_bi_chan(monkeypatch, tmp_path, capsys):
    """Chốt trước-ký biết thiết kế từ G4_checkpoint: SAP RCT bị XOÁ TRỌN §13 (không còn tiêu đề để tự nhận ra) vẫn
    bị chặn — kể cả khi bộ chấm (giả lập) báo READY."""
    study = "PYTEST-G4HT-RCT-XOA-13"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    try:
        sap = d / G4Q.sap_artifact_name(study)
        text = _filled_comparative_sap()
        text = _bo_muc(_bo_muc(_bo_muc(text, "§13"), "§14"), "§15")
        sap.write_text(text, encoding="utf-8", newline="\n")
        (d / "G4_checkpoint.json").write_text(json.dumps({"gate": "G4", "design_code": "rct"}), encoding="utf-8",
                                               newline="\n")
        hang = [{"id": t, "label": t, "status": "PASS", "evidence": "x"} for t in AG._TIEU_CHI_NGUOI_TRUOC_KY["G4"]]
        monkeypatch.setattr(G4Q, "evaluate_study", lambda *a, **k: {
            "status": G4Q.STATUS_READY, "automatic_criteria": [], "approval_criteria": hang})
        monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khoa"))
        (tmp_path / "khoa").write_text("khoa-gia-pytest", encoding="utf-8", newline="\n")
        monkeypatch.setattr(sys, "argv", ["approve_gate.py", "--study", study, "--gate", "G4", "--artifact", str(sap),
                                          "--reviewer-role", "PI", "--reviewer-ref", "PI-01"])
        assert AG.main() != 0
        out = capsys.readouterr().out
        assert "§13" in out and "VẮNG" in out
        assert not (d / "approval_ledger.json").exists()
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── G4-03 ≡ G1-08 ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_03_sap_rct_in_estimand_g1_va_quan_the_chinh():
    text = _fresh_sap()
    body4 = G4Q._section_body(text, "§4")
    for v in _ESTIMAND.values():
        assert v in body4
    assert "Quần thể phân tích CHÍNH:** [CẦN" in body4
    assert "Intention-to-treat (ITT), Per-protocol (PP)" not in text


def test_g4_03_sap_rct_khong_estimand_la_o_trong():
    body4 = G4Q._section_body(_fresh_sap(estimand=None), "§4")
    assert body4.count("[CẦN — ") >= 5 and "gate_params.G1.estimand" in body4


def test_g4_03_auto15_g1_chua_khai_du_la_review():
    thieu = dict(_ESTIMAND, intercurrent_events_strategy=None)
    row = _row(_evaluate(dac_ta={"estimand": thieu}, ledger_signed=False, ledger_reason="x"), "G4-AUTO-15")
    assert row["status"] == "REVIEW" and "intercurrent_events_strategy" in row["evidence"]


def test_g4_03_auto15_estimand_doi_sau_khi_sinh_sap_la_review():
    doi = dict(_ESTIMAND, population_summary_measure="Hiệu số nguy cơ")
    r = _evaluate(dac_ta={"estimand": doi}, ledger_signed=False, ledger_reason="x")
    row = _row(r, "G4-AUTO-15")
    assert row["status"] == "REVIEW" and "population_summary_measure" in row["evidence"]
    assert r["status"] == G4Q.STATUS_DRAFT


def test_g4_luat_moi_khong_ha_cap_sap_da_ky():
    """AUTO-13 (chứng chỉ, chưa từng được kiểm trước 04/10) và AUTO-15 (so khớp estimand) chỉ HIỂN THỊ sau khi ký."""
    doi = dict(_ESTIMAND, population_summary_measure="Hiệu số nguy cơ")
    r = _evaluate(dac_ta={"estimand": doi})
    assert _row(r, "G4-AUTO-15")["status"] == "REVIEW" and r["status"] == G4Q.STATUS_LOCKED
    text = _filled_comparative_sap().replace(
        "║ KQ chính  : Tỷ lệ nhập viện tim mạch trong 12 tháng        ║",
        "║ KQ chính  : Tử vong toàn bộ                                ║")
    r2 = _evaluate(artifact_text=text)
    assert _row(r2, "G4-AUTO-13")["status"] == "REVIEW" and r2["status"] == G4Q.STATUS_LOCKED


def test_g4_03_auto15_khong_ap_cho_thiet_ke_khac():
    r = _evaluate(checkpoint=_checkpoint(design_code="cohort"), g3_checkpoint=_g3_checkpoint(design_code="cohort"),
                  artifact_text=_filled_comparative_sap(design_code="cohort"), dac_ta={"estimand": None})
    assert _row(r, "G4-AUTO-15")["status"] == "PASS"


# ── G4-04 ≡ G3-05 ──────────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("song,ky_vong", [
    ({"status": "BLOCKED", "muc": "BLOCKED", "nguon": "song", "bao_cao": {"automatic_criteria": [
        {"id": "G3-AUTO-16", "status": "BLOCK"}]}}, "BLOCK"),
    ({"status": "DRAFT_READY_NEEDS_STATISTICIAN_REVIEW", "muc": "DRAFT", "nguon": "song"}, "REVIEW"),
    ({"status": "KHONG_DO_DUOC", "muc": "KHONG_DO_DUOC", "nguon": "loi", "ly_do": "bộ chấm hỏng"}, "REVIEW"),
    (None, "REVIEW"),
])
def test_g4_04_auto12_g3_cham_song(song, ky_vong):
    r = _evaluate(g3_song=song)
    row = _row(r, "G4-AUTO-12")
    assert row["status"] == ky_vong, row
    assert r["status"] == (G4Q.STATUS_BLOCKED if ky_vong == "BLOCK" else G4Q.STATUS_DRAFT)
    if ky_vong == "BLOCK":
        assert "G3-AUTO-16" in row["evidence"]


def test_g4_04_g3_da_chot_thi_auto12_pass():
    assert _row(_evaluate(), "G4-AUTO-12")["status"] == "PASS"


def test_g4_04_run_g4_tu_choi_khi_g3_bi_chan(tmp_path, monkeypatch):
    d, rc, out = _chay_g4(tmp_path, monkeypatch, "S-G4-CHAN", them_meta={"G3": {"population_n": 3000}},
                          kiem=False)
    assert rc == GC.EXIT_BLOCKED, out
    assert not _sap(d, "S-G4-CHAN").exists(), "không được sinh SAP khoá N bị G3 chặn"
    cp = json.loads((d / "G4_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["g4_status"].startswith("BLOCKED") and "g3_quality_gate.py" in json.dumps(cp["needs_input"])
    assert "G3-AUTO-16" in out


def test_g4_04_g3_chua_chot_thi_g4_draft(tmp_path, monkeypatch):
    d, rc, out = _chay_g4(tmp_path, monkeypatch, "S-G4-NHAP", chot_g3=False)
    assert rc == 0 and "KHÔNG ký" in out
    p = _sap(d, "S-G4-NHAP")
    text = dien_sap_g4(p.read_text(encoding="utf-8"))
    p.write_text(text, encoding="utf-8", newline="\n")
    xac_nhan_g4(d, text)
    r = _cham(d, "S-G4-NHAP", tmp_path)
    assert _row(r, "G4-AUTO-12")["status"] == "REVIEW" and r["status"] == G4Q.STATUS_DRAFT


def test_g4_04_luong_that_g3_da_chot_san_sang_ky(tmp_path, monkeypatch):
    d, rc, out = _chay_g4(tmp_path, monkeypatch, "S-G4-DU")
    assert rc == 0, out
    p = _sap(d, "S-G4-DU")
    text = dien_sap_g4(p.read_text(encoding="utf-8"))
    p.write_text(text, encoding="utf-8", newline="\n")
    xac_nhan_g4(d, text)
    # SAP sinh THẬT mang tham số quyết định N của G3 (G4-06/G4-08): bỏ cuộc, SD — không chỉ alpha/power/N.
    body12 = G4Q._section_body(text, "§12")
    assert "Tỷ lệ bỏ cuộc dự kiến:** 0.1" in body12 and "Độ lệch chuẩn (SD) kết cục:** 10" in body12
    r = _cham(d, "S-G4-DU", tmp_path)
    loi = [(c["id"], c["evidence"]) for c in r["automatic_criteria"] if c["status"] != "PASS"]
    assert r["status"] == G4Q.STATUS_READY, loi
    for tid in AG._TIEU_CHI_NGUOI_TRUOC_KY["G4"]:
        assert _row(r, tid)["status"] == "PASS", tid


@pytest.mark.parametrize("thiet_ke", sorted(G3_THEO_THIET_KE))
def test_chung_h_dau_cuoi_8_thiet_ke_bo_sinh_khop_bo_cham(tmp_path, monkeypatch, thiet_ke):
    """CHUNG-H: đầu ra THẬT của run_g4_auto (sau G3 đã chốt thật) điền như người thật phải tới READY_FOR_SIGNATURE ở
    MỌI thiết kế — bộ sinh không được sinh thứ bộ chấm từ chối (lộ G4-AUTO-09 chặn đề tài mô tả)."""
    study = f"E2E-{thiet_ke}"
    d, rc, out = _chay_g4(tmp_path, monkeypatch, study, thiet_ke=thiet_ke)
    assert rc == 0, out
    p = _sap(d, study)
    text = dien_sap_g4(p.read_text(encoding="utf-8"))
    p.write_text(text, encoding="utf-8", newline="\n")
    xac_nhan_g4(d, text)
    r = _cham(d, study, tmp_path)
    loi = [(c["id"], c["evidence"][:120]) for c in r["automatic_criteria"] + r["approval_criteria"]
           if c["status"] != "PASS" and c["id"] not in ("G4-HUMAN-01", "G4-HUMAN-02", "G4-HUMAN-03")]
    assert r["status"] == G4Q.STATUS_READY and not loi, loi


# ── G4-05 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_05_cau_thieu_luc_dung_chieu():
    thap = _fresh_sap(design_code="cohort", n_adjusted=300, n_statistical_min=453)
    assert "lớn hơn mức tối thiểu" not in thap and G4Q.NHAN_LOAI_THIEU_LUC in thap
    assert "THIẾU LỰC THỐNG KÊ" in thap and "[CẦN THỐNG KÊ VIÊN/PI GIẢI TRÌNH" in G4Q._section_body(thap, "§1")
    cao = _fresh_sap(design_code="cohort", n_adjusted=1000, n_statistical_min=453)
    assert "lớn hơn mức tối thiểu" in cao and G4Q.NHAN_LOAI_THIEU_LUC not in cao
    co_gt = _fresh_sap(design_code="cohort", n_adjusted=300, n_statistical_min=453,
                       giai_trinh_thieu_luc="Nghiên cứu khả thi — chỉ ước lượng tham số")
    assert "Nghiên cứu khả thi — chỉ ước lượng tham số" in G4Q._section_body(co_gt, "§1")


def test_g4_05_auto14_khang_dinh_sai_bi_chan():
    g3 = _g3_checkpoint(n_adjusted=453, confirmed_n=300)
    sai = _fresh_sap(n_adjusted=300).replace(
        "- **Cỡ mẫu cuối:**", "- **N tối thiểu theo thống kê (từ G3):** 453 — N ở trên là cỡ mẫu KẾ HOẠCH do chủ "
        "nhiệm/Hội đồng chốt, lớn hơn mức tối thiểu.  \n- **Cỡ mẫu cuối:**", 1)
    row = _row(_evaluate(artifact_text=sai, g3_checkpoint=g3), "G4-AUTO-14")
    assert row["status"] == "BLOCK" and "khẳng định SAI" in row["evidence"]


def test_g4_05_auto14_can_giai_trinh_nguoi_that():
    g3 = _g3_checkpoint(n_adjusted=453, confirmed_n=300)
    text = _filled_comparative_sap(n_adjusted=300, n_statistical_min=453)
    row = _row(_evaluate(artifact_text=text, g3_checkpoint=g3), "G4-AUTO-14")
    assert row["status"] == "REVIEW" and "underpowered_acceptance_justification" in row["evidence"]
    ok = _evaluate(artifact_text=text, g3_checkpoint=g3,
                   meta=_meta(g3_overrides={"underpowered_acceptance_justification": "Giới hạn nguồn lực"}))
    assert _row(ok, "G4-AUTO-14")["status"] == "PASS"
    khong_neu = _filled_comparative_sap(n_adjusted=300)  # SAP không nói gì về N tối thiểu
    assert _row(_evaluate(artifact_text=khong_neu, g3_checkpoint=g3,
                          meta=_meta(g3_overrides={"underpowered_acceptance_justification": "x"})),
                "G4-AUTO-14")["status"] == "REVIEW"


def test_g4_05_g3_auto13_nhan_giai_trinh(tmp_path):
    cp = {"design_code": "rct", "n_adjusted": 453, "confirmed_n": 300, "guardrail": "✅ PASS"}
    (tmp_path / "A4.md").write_text("", encoding="utf-8", newline="\n")

    def _a13(meta):
        r = G3Q.evaluate_g3_quality(study="S", checkpoint=cp, artifact_path=tmp_path / "A4.md", g0_checkpoint={},
                                    g1_checkpoint={"gate": "G1"}, meta=meta)
        return next(c for c in r["automatic_criteria"] if c["id"] == "G3-AUTO-13")

    assert _a13({})["status"] == "REVIEW"
    co = _a13({"gate_params": {"G3": {"underpowered_acceptance_justification": "Nghiên cứu thí điểm"}}})
    assert co["status"] == "PASS" and "THẤP HƠN" in co["evidence"]
    o_trong = _a13({"gate_params": {"G3": {"underpowered_acceptance_justification": "[CẦN]"}}})
    assert o_trong["status"] == "REVIEW"


# ── G4-06 ≡ G3-08 ──────────────────────────────────────────────────────────────────────────────────────────────────
def _sap_mo_ta(precision=0.05, **kw):
    return _fresh_sap(design_code="cross_sectional", effect_type="PREVALENCE", effect_val=0.5, n_adjusted=482,
                      g3={"precision": precision, "dropout": 0.2}, **kw)


def test_g4_06_thiet_ke_chinh_xac_ky_d_khong_ky_power():
    text = _sap_mo_ta()
    body12 = G4Q._section_body(text, "§12")
    assert "Sai số tuyệt đối cho phép (d):** ±0.05" in body12 and "Tỷ lệ ước lượng (p):** 0.5" in body12
    assert "**Power:** 80%" not in text and "Power     : 80%" not in text
    assert "Sai số d" in G4Q._phan_body(text, "5")
    p = G4Q.parse_signed_numbers(text)
    assert p["precision"] == 0.05 and p["power_pct"] is None and p["n"] == 482 == p["n_chung_chi"]


def test_g4_06_auto03_doi_chieu_d_voi_g3():
    g3 = _g3_checkpoint(design_code="cross_sectional", effect_type="PREVALENCE", effect_val=0.5, n_adjusted=482,
                        precision=0.05)
    kw = dict(checkpoint=_checkpoint(design_code="cross_sectional"), artifact_text=_sap_mo_ta())
    assert _row(_evaluate(g3_checkpoint=g3, **kw), "G4-AUTO-03")["status"] == "PASS"
    row = _row(_evaluate(g3_checkpoint=dict(g3, precision=0.04), **kw), "G4-AUTO-03")
    assert row["status"] == "BLOCK" and "sai số d" in row["evidence"]


def test_g4_06_sap_cu_in_power_cho_thiet_ke_chinh_xac_la_review():
    g3 = _g3_checkpoint(design_code="cross_sectional", effect_type="PREVALENCE", effect_val=0.5, n_adjusted=482,
                        precision=0.05)
    text = _sap_mo_ta().replace("- **Power:** không dùng", "- **Power:** 80% — không dùng")
    row = _row(_evaluate(checkpoint=_checkpoint(design_code="cross_sectional"), g3_checkpoint=g3,
                         artifact_text=text), "G4-AUTO-03")
    assert row["status"] == "REVIEW" and "khung ký sai" in row["evidence"]


def test_g4_06_dinh_tinh_khong_alpha_power_khong_cot_p():
    text = _fresh_sap(design_code="qualitative", n_adjusted=25)
    assert "**Power:** 80%" not in text and "Alpha (two-sided)" not in text
    assert "| p |" not in G4Q._section_body(text, "§11") and "t-test" not in G4Q._section_body(text, "§3")
    p = G4Q.parse_signed_numbers(text)
    assert p["alpha_khong_ap_dung"] and p["power_khong_ap_dung"] and p["n"] == 25


def test_g4_06_bang_gia_theo_thiet_ke():
    rct11 = G4Q._section_body(_fresh_sap(), "§11")
    assert "| p |" not in rct11 and "PMID 20332511" in rct11
    assert "CONSORT 2010" in G4Q._section_body(_fresh_sap(), "§3")
    assert "2×2" in G4Q._section_body(_fresh_sap(design_code="diagnostic", effect_type="AUC", effect_val=0.75), "§11")
    assert "I²" in G4Q._section_body(_fresh_sap(design_code="sr_ma", n_adjusted=0), "§11")
    assert "C-statistic" in G4Q._section_body(_fresh_sap(design_code="prediction", n_adjusted=0), "§11")
    assert "| p |" in G4Q._section_body(_fresh_sap(design_code="cohort"), "§11")


def test_g4_06_chan_doan_ky_so_ca_benh_va_doi_chieu():
    g3x = {"n_benh": 32, "n_khong_benh": 32, "prevalence": 0.5}
    text = _fresh_sap(design_code="diagnostic", effect_type="AUC", effect_val=0.7, n_adjusted=64, g3=g3x)
    p = G4Q.parse_signed_numbers(text)
    assert p["n_benh"] == 32 and p["n_khong_benh"] == 32 and p["prevalence"] == 0.5
    g3 = _g3_checkpoint(design_code="diagnostic", effect_type="AUC", effect_val=0.7, n_adjusted=64, **g3x)
    kw = dict(checkpoint=_checkpoint(design_code="diagnostic"), artifact_text=text)
    assert _row(_evaluate(g3_checkpoint=g3, **kw), "G4-AUTO-03")["status"] == "PASS"
    assert _row(_evaluate(g3_checkpoint=dict(g3, n_benh=40), **kw), "G4-AUTO-03")["status"] == "BLOCK"


def test_g4_06_cum_va_tham_so_quyet_dinh_n_vao_sap():
    g3x = {"icc": 0.05, "cluster_size": 20, "design_effect": 1.95, "n_clusters": 13, "p0": 0.3, "dropout": 0.1}
    text = _fresh_sap(g3=g3x)
    assert "Hiệu chỉnh cụm" in G4Q._section_body(text, "§4")
    p = G4Q.parse_signed_numbers(text)
    assert (p["icc"], p["cluster_size"], p["design_effect"], p["n_clusters"], p["p0"], p["dropout"]) == \
        (0.05, 20, 1.95, 13, 0.3, 0.1)
    row = _row(_evaluate(artifact_text=text, g3_checkpoint=_g3_checkpoint(**dict(g3x, icc=0.02))), "G4-AUTO-03")
    assert row["status"] == "BLOCK" and "ICC" in row["evidence"]


def test_g4_06_ni_ky_chieu_ket_cuc():
    text = _fresh_sap(hypothesis_type="non_inferiority", margin=0.1, effect_type="NI_PROPORTION", effect_val=0.85,
                      g3={"outcome_direction": "higher_better", "p0": 0.8})
    p = G4Q.parse_signed_numbers(text)
    assert p["outcome_direction"] == "higher_better" and p["effect_val"] == 0.85
    assert "so cận khoảng tin cậy với biên Δ = 0.1" in G4Q._section_body(text, "§4")
    g3 = _g3_checkpoint(hypothesis_type="non_inferiority", margin=0.1, effect_type="NI_PROPORTION", effect_val=0.85,
                        outcome_direction="lower_better", p0=0.8)
    row = _row(_evaluate(artifact_text=text, g3_checkpoint=g3), "G4-AUTO-03")
    assert row["status"] == "BLOCK" and "chiều kết cục" in row["evidence"]


def test_g4_auto09_gia_thuyet_mo_ta_khong_doi_margin():
    """Lộ ở kiểm đầu–cuối 8 thiết kế: descriptive_precision (đề tài mô tả như C1a) từng bị BLOCK «thiếu margin»."""
    g3 = _g3_checkpoint(design_code="cross_sectional", effect_type="PREVALENCE", effect_val=0.5, n_adjusted=482,
                        precision=0.05, hypothesis_type="descriptive_precision", margin=None)
    r = _evaluate(checkpoint=_checkpoint(design_code="cross_sectional"), g3_checkpoint=g3, artifact_text=_sap_mo_ta())
    assert _row(r, "G4-AUTO-09")["status"] == "PASS"
    ni = _g3_checkpoint(hypothesis_type="non_inferiority", margin=None)
    assert _row(_evaluate(g3_checkpoint=ni), "G4-AUTO-09")["status"] == "BLOCK"
    # Cắt ngang PHÂN TÍCH (có effect size, G3 gán descriptive_precision): SAP không in khối margin «[CẦN từ G3]».
    phan_tich = _fresh_sap(design_code="cross_sectional", effect_type="OR", effect_val=2.0,
                           hypothesis_type="descriptive_precision")
    assert "Biên (margin" not in phan_tich and "Margin (Δ)" not in phan_tich


def test_g4_06_khong_mac_dinh_im_lang_alpha_power():
    text = _fresh_sap(alpha=None, power=None)
    body12 = G4Q._section_body(text, "§12")
    assert "Alpha (two-sided):** [CẦN từ G3]" in body12 and "Power:** [CẦN từ G3]" in body12


# ── G4-07 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_07_ky_sau_khoa_du_lieu():
    text = _filled_comparative_sap()
    assert G4Q.ky_sau_khoa_du_lieu(text, None, "2026-09-10T00:00:00+00:00") is None
    assert G4Q.ky_sau_khoa_du_lieu(text, "2026-09-15", "2026-09-10T00:00:00+00:00") is None
    ly_do = G4Q.ky_sau_khoa_du_lieu(text, "2026-09-01", "2026-09-10T00:00:00+00:00")
    assert ly_do and "SAP AMENDMENT" in ly_do
    # Câu quy tắc in sẵn của PHẦN 4 có chữ «SAP AMENDMENT» — không được tính là đã khai sửa đổi (chống tautology).
    assert "SAP AMENDMENT" in G4Q._phan_body(text, "4")
    co_sua = text.replace("| (chưa có) | | | |",
                          "| 2026-09-09 | Thêm phân tích độ nhạy theo tuân thủ | SAP AMENDMENT | Thống kê viên |")
    assert G4Q.ky_sau_khoa_du_lieu(co_sua, "2026-09-01", "2026-09-10T00:00:00+00:00") is None
    assert "ISO" in G4Q.ky_sau_khoa_du_lieu(text, "01/09/2026", "2026-09-10T00:00:00+00:00")


def test_g4_07_human06_ngay_kieu_viet_nam_la_review():
    r = _evaluate(meta=_meta(g4_overrides={"reviewed_at": "15/09/2026"}, top_level={"data_lock_date": "2026-09-01"}))
    row = _row(r, "G4-HUMAN-06")
    assert row["status"] == "REVIEW" and "ISO" in row["evidence"]


def test_g4_07_human06_ky_so_cai_sau_khoa_du_lieu():
    meta = _meta(g4_overrides={"reviewed_at": "2026-08-20T08:00:00+00:00"}, top_level={"data_lock_date": "2026-09-01"})
    r = _evaluate(meta=meta, ledger_lock_timestamp="2026-09-10T03:00:00+00:00")
    row = _row(r, "G4-HUMAN-06")
    assert row["status"] == "REVIEW" and "HARKing" in row["evidence"]
    assert _row(_evaluate(meta=meta, ledger_lock_timestamp="2026-08-25T03:00:00+00:00"),
                "G4-HUMAN-06")["status"] == "PASS"


def test_g4_07_approve_gate_tu_choi_ky_sau_khoa_du_lieu(monkeypatch, tmp_path, capsys):
    study = "PYTEST-G4HT-KY-SAU-KHOA"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    try:
        sap = d / G4Q.sap_artifact_name(study)
        sap.write_text(_filled_comparative_sap(design_code="cohort"), encoding="utf-8", newline="\n")
        (d / "study_meta.json").write_text(json.dumps({"data_lock_date": "2026-09-01"}), encoding="utf-8",
                                           newline="\n")
        hang = [{"id": t, "label": t, "status": "PASS", "evidence": "x"} for t in AG._TIEU_CHI_NGUOI_TRUOC_KY["G4"]]
        monkeypatch.setattr(G4Q, "evaluate_study", lambda *a, **k: {
            "status": G4Q.STATUS_READY, "automatic_criteria": [], "approval_criteria": hang})
        monkeypatch.setenv("EBM_GATE_KEY_PATH", str(tmp_path / "khoa"))
        (tmp_path / "khoa").write_text("khoa-gia-pytest", encoding="utf-8", newline="\n")
        monkeypatch.setattr(sys, "argv", ["approve_gate.py", "--study", study, "--gate", "G4", "--artifact", str(sap),
                                          "--reviewer-role", "PI", "--reviewer-ref", "PI-01"])
        assert AG.main() != 0
        out = capsys.readouterr().out
        assert "SAU ngày khoá dữ liệu" in out and "SAP AMENDMENT" in out
        assert not (d / "approval_ledger.json").exists()
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── G4-08 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_08_xoa_dong_so_o_muc_12_la_review():
    text = _filled_comparative_sap()
    for nhan in ("- **Alpha (two-sided):**", "- **Power:**", "- **Cỡ mẫu:** N ="):
        text = "\n".join(ln for ln in text.splitlines() if not ln.startswith(nhan))
    row = _row(_evaluate(artifact_text=text), "G4-AUTO-03")
    assert row["status"] == "REVIEW" and "thiếu số ký" in row["evidence"]
    for ten in ("Alpha", "Power", "Cỡ mẫu N"):
        assert ten in row["evidence"]


def test_g4_08_n_o_muc_1_va_chung_chi_lech_bi_chan():
    text = _filled_comparative_sap()
    text = "\n".join(ln for ln in text.splitlines() if not ln.startswith("- **Cỡ mẫu:** N ="))
    text = text.replace("**Cỡ mẫu cuối:** N = 400", "**Cỡ mẫu cuối:** N = 999").replace(
        "Cỡ mẫu   : N = 400", "Cỡ mẫu   : N = 999")
    row = _row(_evaluate(artifact_text=text), "G4-AUTO-03")
    assert row["status"] == "BLOCK" and "§1" in row["evidence"] and "chứng chỉ" in row["evidence"]


def test_g4_08_n_noi_bo_sap_lech_khi_g3_khong_co_n():
    """Thiết kế không dùng power, G3 chưa chốt N: không có N của G3 để so — nhưng N trong CHÍNH SAP (§12 và chứng
    chỉ khoá) vẫn phải khớp nhau."""
    text = _fresh_sap(design_code="sr_ma", n_adjusted=15).replace("Cỡ mẫu   : N = 15", "Cỡ mẫu   : N = 16")
    g3 = _g3_checkpoint(design_code="sr_ma", n_adjusted=0, confirmed_n=None, effect_val=None, effect_type=None)
    row = _row(_evaluate(artifact_text=text, checkpoint=_checkpoint(design_code="sr_ma"), g3_checkpoint=g3),
               "G4-AUTO-03")
    assert row["status"] == "BLOCK" and "N ở §12=15" in row["evidence"], row


def test_g4_08_chung_chi_lech_muc_12():
    text = _filled_comparative_sap().replace("Cỡ mẫu   : N = 400", "Cỡ mẫu   : N = 401")
    row = _row(_evaluate(artifact_text=text), "G4-AUTO-03")
    assert row["status"] == "BLOCK" and "chứng chỉ" in row["evidence"]


# ── G4-09 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_09_chung_chi_con_o_trong_khong_ky_duoc():
    text = _filled_comparative_sap().replace(
        "║ KQ chính  : Tỷ lệ nhập viện tim mạch trong 12 tháng        ║",
        "║ KQ chính  : [CẦN BÁC SĨ ĐIỀN — từ SAP §2]                 ║")
    r = _evaluate(artifact_text=text, ledger_signed=False, ledger_reason="chưa ký")
    row = _row(r, "G4-AUTO-13")
    assert row["status"] == "REVIEW" and "còn ô trống" in row["evidence"] and "KQ chính" in row["evidence"]
    assert r["status"] == G4Q.STATUS_DRAFT
    # Ô «Phân tích» còn trống trong khi «KQ chính» đã đúng §2 — chỉ luật ô trống bắt được.
    text2 = _filled_comparative_sap().replace(
        "║ Phân tích : Intention-to-treat (ITT)                      ║",
        "║ Phân tích : [CẦN BÁC SĨ ĐIỀN — quần thể phân tích]        ║")
    row2 = _row(_evaluate(artifact_text=text2, ledger_signed=False, ledger_reason="x"), "G4-AUTO-13")
    assert row2["status"] == "REVIEW" and "Phân tích" in row2["evidence"]


def test_g4_09_kq_chinh_khac_muc_2():
    text = _filled_comparative_sap().replace(
        "║ KQ chính  : Tỷ lệ nhập viện tim mạch trong 12 tháng        ║",
        "║ KQ chính  : Tử vong toàn bộ                                ║")
    row = _row(_evaluate(artifact_text=text, ledger_signed=False, ledger_reason="x"), "G4-AUTO-13")
    assert row["status"] == "REVIEW" and "khác" in row["evidence"]


def test_g4_09_dien_dat_lai_cung_ket_cuc_khong_bao_dong_gia():
    """Đo C1a: chứng chỉ «G1 hài lòng chung (thứ hạng 1-5)…», §2 «G1 — mức hài lòng chung…» — cùng kết cục."""
    goc = _filled_comparative_sap()
    dien_dat_lai = goc.replace("║ KQ chính  : Tỷ lệ nhập viện tim mạch trong 12 tháng        ║",
                               "║ KQ chính  : Nhập viện tim mạch 12 tháng (tỷ lệ)            ║")
    assert _row(_evaluate(artifact_text=dien_dat_lai, ledger_signed=False, ledger_reason="x"),
                "G4-AUTO-13")["status"] == "PASS"
    nua = goc.replace("║ KQ chính  : Tỷ lệ nhập viện tim mạch trong 12 tháng        ║",
                      "║ KQ chính  : Tỷ lệ tử vong                                  ║")
    assert _row(_evaluate(artifact_text=nua, ledger_signed=False, ledger_reason="x"),
                "G4-AUTO-13")["status"] == "REVIEW", "chung đúng nửa số từ («tỷ lệ») vẫn là kết cục khác"


def test_g4_auto11_khong_phu_thuoc_dau_cau():
    """Đo C1a: G1 «… (biến X, Phần 3 phiếu)» và §2 «… (biến X), Phần 3 phiếu» chỉ khác vị trí dấu ngoặc."""
    text = _filled_comparative_sap().replace(
        "- **Kết cục chính:** Tỷ lệ nhập viện tim mạch trong 12 tháng  ",
        "- **Kết cục chính:** G1 — mức hài lòng chung (biến SHL_TrucTiep), Phần 3 phiếu, thang 1–5  ")
    meta = _meta()
    ten = "G1 — mức hài lòng chung (biến SHL_TrucTiep, Phần 3 phiếu)"
    meta["gate_params"]["G1"] = {"primary_outcome": {"name": ten}}
    assert _row(_evaluate(artifact_text=text, meta=meta), "G4-AUTO-11")["status"] == "PASS"


def test_g4_09_dong_ky_tay_khong_phai_o_trong():
    assert _row(_evaluate(), "G4-AUTO-13")["status"] == "PASS"
    assert "____" in G4Q._phan_body(_filled_comparative_sap(), "5")


# ── G4-10 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_10_phan_mem_ok_va_seed_42_khong_qua():
    text = _filled_comparative_sap().replace("- **Phần mềm:** R v4.3.1  ", "- **Phần mềm:** OK  ").replace(
        "- **Random seed:** set.seed(20260730)  ", "- **Random seed:** seed 42  ")
    row = _row(_evaluate(artifact_text=text), "G4-AUTO-08")
    assert row["status"] == "REVIEW" and "phần mềm" in row["evidence"]


def test_g4_10_seed_so_tran_va_dinh_tinh_khong_ap_dung():
    text = _filled_comparative_sap().replace("set.seed(20260730)", "20260730")
    assert _row(_evaluate(artifact_text=text), "G4-AUTO-08")["status"] == "PASS"
    body10 = G4Q._section_body(_fresh_sap(design_code="qualitative", n_adjusted=20), "§10")
    assert "Random seed:** KHÔNG ÁP DỤNG" in body10


# ── G4-11 ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_g4_11_huong_dan_khoa_dung_co_che():
    text = _fresh_sap()
    assert "G4_STATUS: LOCKED" not in text and "Cung cấp ngày ký" not in text
    assert "approve_gate.py --study TEST-G4Q --gate G4" in text
    phan6 = G4Q._phan_body(text, "6")
    for muc in ("§1/§2/§4/§5/§9/§10/§13/§14/§15", "dau_van_tay_chot", "KHÔNG tự ghi trạng thái khoá"):
        assert muc in phan6, muc
    assert "§13" not in G4Q._phan_body(_fresh_sap(design_code="cohort"), "6")


def test_g4_11_checkpoint_huong_dan_dung(tmp_path, monkeypatch):
    d, rc, out = _chay_g4(tmp_path, monkeypatch, "S-G4-HD")
    cp = json.loads((d / "G4_checkpoint.json").read_text(encoding="utf-8"))
    assert "approve_gate.py --gate G4" in cp["lock_instruction"] and "G4_STATUS=LOCKED" not in json.dumps(cp)
    assert "§13/§14/§15" in cp["pending_doctor_actions"][0]
    assert cp["g3_trang_thai_luc_sinh"] == G3Q.STATUS_CONFIRMED and cp["loai_muc_12"] == "power"


# ── CHUNG-C / QĐ-7 — xác nhận G4 gắn dấu vân tay ───────────────────────────────────────────────────────────────────
def test_g4_xac_nhan_kieu_cu_khong_dau_la_review():
    r = _evaluate(_chot=False)
    row = _row(r, "G4-HUMAN-08")
    assert row["status"] == "REVIEW" and G4Q.dau_van_tay_g4(_filled_comparative_sap()) in row["action"]
    assert r["status"] == G4Q.STATUS_READY, "thiếu xác nhận người không phải lỗi máy — không hạ xuống DRAFT"


def test_g4_sua_muc_5_sau_khi_xac_nhan_mat_hieu_luc():
    goc = _filled_comparative_sap()
    meta = _meta(g4_overrides={"dau_van_tay_chot": G4Q.dau_van_tay_g4(goc)})
    sua = goc.replace("Tuổi, HbA1c — EPV=15 cho 8 biến", "Tuổi, HbA1c, BMI — EPV=12 cho 10 biến")
    row = _row(_evaluate(artifact_text=sua, meta=meta), "G4-HUMAN-08")
    assert row["status"] == "REVIEW" and "đã đổi" in row["evidence"]


def test_g4_dau_van_tay_khong_doi_khi_ky_tay_chung_chi():
    goc = _filled_comparative_sap()
    ky = goc.replace("║ Chủ nhiệm đề tài: _________________________", "║ Chủ nhiệm đề tài: BS. A ___________________")
    assert G4Q.dau_van_tay_g4(goc) == G4Q.dau_van_tay_g4(ky)


def test_g4_g1_ket_cuc_co_cau_truc_khong_review_oan():
    meta = _meta()
    meta["gate_params"]["G1"] = {"primary_outcome": {"name": "Tỷ lệ nhập viện tim mạch trong 12 tháng",
                                                     "timepoint": "12 tháng"}}
    assert _row(_evaluate(meta=meta), "G4-AUTO-11")["status"] == "PASS"


# ── approve_gate: ký thật cuối chuỗi; xác nhận người trước khi ký; g4_lock_date tụt ─────────────────────────────────
@pytest.fixture()
def _khoa_gia(tmp_path, monkeypatch):
    khoa = tmp_path / "gate_approval_key"
    khoa.write_text("khoa-gia-pytest-g4", encoding="utf-8", newline="\n")
    (tmp_path / "gate_approval_key_STATISTICIAN").write_text("khoa-gia-pytest-g4-stat", encoding="utf-8",
                                                              newline="\n")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(khoa))
    return khoa


def _ky(monkeypatch, study, sap):
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", "--study", study, "--gate", "G4", "--artifact", str(sap),
                                      "--reviewer-role", "METHODS_STATISTICS_REVIEWER", "--reviewer-ref", "STAT-HT"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = AG.main()
    return rc, buf.getvalue()


def test_g4_luong_ky_that_cuoi_chuoi(monkeypatch, _khoa_gia):
    study = "PYTEST-G4HT-KY-THAT"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    try:
        dung_g0_g3_da_chot(d, study)
        monkeypatch.setattr(sys, "argv", ["run_g4_auto.py", "--study", study])
        CS.xoa_dem()
        with contextlib.redirect_stdout(io.StringIO()):
            R4.main()
        sap = _sap(d, study)
        text = dien_sap_g4(sap.read_text(encoding="utf-8"))
        sap.write_text(text, encoding="utf-8", newline="\n")
        # (a) Chưa xác nhận G4 ⇒ approve_gate TỪ CHỐI (tiêu chí người kiểm được trước khi ký).
        CS.xoa_dem()
        rc, out = _ky(monkeypatch, study, sap)
        assert rc != 0 and "G4-HUMAN-08" in out, out
        assert not (d / "approval_ledger.json").exists() or json.loads(
            (d / "approval_ledger.json").read_text(encoding="utf-8")) == []
        # (b) Xác nhận gắn dấu ⇒ ký được và đạt LOCKED.
        xac_nhan_g4(d, text)
        CS.xoa_dem()
        rc, out = _ky(monkeypatch, study, sap)
        assert rc == 0, out
        assert "PASS_G4_SAP_LOCKED" in out, out
        cp = json.loads((d / "G4_checkpoint.json").read_text(encoding="utf-8"))
        assert cp["g4_lock_date"]
        # (c) Sửa SAP sau khi ký ⇒ băm lệch ⇒ không còn LOCKED, g4_lock_date bị XOÁ (không còn «đã khoá ngày X» sai).
        sap.write_text(text.replace("Theo tuổi <65/≥65", "Theo tuổi <70/≥70"), encoding="utf-8", newline="\n")
        CS.xoa_dem()
        r = G4Q.evaluate_study(study, d, repo_root=ROOT, write=True)
        assert r["status"] != G4Q.STATUS_LOCKED
        assert json.loads((d / "G4_checkpoint.json").read_text(encoding="utf-8"))["g4_lock_date"] is None
    finally:
        shutil.rmtree(d, ignore_errors=True)
        CS.xoa_dem()


def test_g4_auto11_uu_tien_ket_cuc_g1_da_ghim():
    """G4-AUTO-11 ưu tiên kết cục ĐÃ GHIM ở G1 (G3 tính N cho kết cục này) hơn câu hỏi G0."""
    meta = _meta()
    meta["gate_params"]["G1"] = {"primary_outcome": {"name": "Một kết cục khác hẳn"}}
    meta["gate_params"]["G0"] = {"primary_outcome": "Tỷ lệ nhập viện tim mạch trong 12 tháng"}
    row = _row(_evaluate(meta=meta), "G4-AUTO-11")
    assert row["status"] == "REVIEW", "G1 đã ghim phải được ưu tiên hơn câu hỏi G0"
