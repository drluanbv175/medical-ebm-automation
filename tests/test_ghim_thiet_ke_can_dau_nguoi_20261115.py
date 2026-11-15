"""G2 thôi gieo `study_meta.design_code` + «ghim thiết kế cần dấu người» (15/11/2026).

BỐI CẢNH: thẩm định đối kháng PR #277 phát hiện run_g2_auto gieo `study_meta.design_code` = thiết kế G1 MÁY suy —
đúng ô G1 hiểu là «bác sĩ ghim». Mỗi lần G1 chạy lại sau G2, G1 coi đó là quyết định của PI: gỡ cờ thiết kế mơ hồ
(G1-AUTO-04/04b) và hạ G1-AUTO-02d CHẶN→XEM mà không ai xác nhận (CLAUDE.md §0.5). Bác sĩ chọn phương án «G2 thôi gieo +
ghim cần dấu người»:
  - G2 không ghi `design_code` nữa; bản sao của máy vào `design_code_tu_g1` (chỉ để tra cứu);
  - giá trị ghim chỉ là quyết định của PI khi có dấu người (`gate_params.G1.design`, `design_confirmed is True`,
    hoặc `design_code_nguon == "PI"`); `design_code` cấp cao đứng một mình vẫn là thiết kế đang dùng nhưng không gỡ
    cờ mơ hồ.

CÁCH KIỂM: soi HÀNH VI (study_meta sau G2 thật, checkpoint sau G1 thật, trạng thái tiêu chí của bộ chấm) — không grep
mã nguồn. Không gọi mạng.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "tools"))
sys.path.insert(0, str(_REPO_ROOT / "tests"))

import g1_quality_gate as G1Q  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402
import run_g1_auto as G1  # noqa: E402
import skill_standards as S  # noqa: E402
from test_dong_bo_xuyen_cong_20261115 import STUDY as STUDY_MT  # noqa: E402
from test_dong_bo_xuyen_cong_20261115 import _de_tai, _ghi_bo_bien, _ghi_ma_tran  # noqa: E402
from test_g1_hoan_thien_20261004 import _chay_main  # noqa: E402
from test_g1_quality_gate import _build_case, _design, _evaluate  # noqa: E402
from test_g2_registry_prior_art_20260728 import _install_http, _run_g2, _write_g0_checkpoint  # noqa: E402


def _row(r, tid):
    return next(c for c in r["automatic_criteria"] + r["human_criteria"] if c["id"] == tid)


def _meta(d: Path) -> dict:
    return json.loads((d / "study_meta.json").read_text(encoding="utf-8"))


def _ghi_meta(d: Path, meta: dict) -> None:
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")


# ── (1) G2 không gieo ô ghim của PI ─────────────────────────────────────────────────────────────────────────────────
def test_g2_khong_gieo_design_code_va_khong_doi_byte_study_meta(monkeypatch, tmp_path):
    """G2 không gieo ô ghim; thẩm định #281 (Đ2): cũng KHÔNG ghi khoá máy nào khác vào study_meta — đổi byte tệp này làm
    biên bản hội đồng băm study_meta thành «cũ». Bản sao thiết kế G2 dùng nằm ở G2_checkpoint.design_code."""
    study = "PYTEST-G2-KHONG-GIEO"
    _write_g0_checkpoint(tmp_path / "exports" / study, topic="Sự hài lòng của người bệnh ngoại trú",
                         base_query="outpatient patient satisfaction")
    _install_http(monkeypatch, total=0, active=0)
    d = _run_g2(monkeypatch, tmp_path, study)
    meta = _meta(d)
    assert not meta.get("design_code") and "design_code_tu_g1" not in meta, meta
    cp2 = json.loads((d / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp2.get("design_code") == "cross_sectional", cp2.get("design_code")
    truoc = (d / "study_meta.json").read_bytes()
    _run_g2(monkeypatch, tmp_path, study, extra_argv=["--design", "cohort"])
    assert (d / "study_meta.json").read_bytes() == truoc, "chạy lại G2 (thiết kế khác) không được đổi byte study_meta"


def test_g2_giu_nguyen_ghim_cua_pi(monkeypatch, tmp_path):
    study = "PYTEST-G2-GIU-GHIM"
    d = tmp_path / "exports" / study
    _write_g0_checkpoint(d, topic="Sự hài lòng của người bệnh ngoại trú", base_query="outpatient satisfaction")
    _ghi_meta(d, {"design_code": "cross_sectional", "design_code_nguon": "PI"})
    _install_http(monkeypatch, total=0, active=0)
    _run_g2(monkeypatch, tmp_path, study)
    meta = _meta(d)
    assert meta["design_code"] == "cross_sectional" and meta["design_code_nguon"] == "PI", meta


# ── (2) Hàm dùng chung: giá trị ghim + dấu người ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("meta,ky_vong", [
    ({}, ("", False)),
    ({"design_code": "rct"}, ("rct", False)),                                          # G2 gieo kiểu cũ
    ({"design_code": "rct", "design_code_nguon": "PI"}, ("rct", True)),
    ({"design_code": "rct", "design_code_nguon": "pi "}, ("rct", True)),
    ({"design_code": "rct", "design_code_nguon": "G2"}, ("rct", False)),
    ({"design_code": "rct", "gate_params": {"G1": {"design_confirmed": True}}}, ("rct", True)),
    ({"design_code": "rct", "gate_params": {"G1": {"design_confirmed": "true"}}}, ("rct", False)),
    ({"design_code": "RCT", "gate_params": {"G1": {"design": "rct"}}}, ("RCT", True)),  # trùng sau chuẩn hoá
    # Thẩm định #281 (Đ1): G1.design của PI LỆCH design_code không nhãn PI ⇒ ô G1 THẮNG (máy gieo không thắng lặng lẽ),
    # kể cả khi có design_confirmed (dấu không gắn giá trị nào — không được «đóng dấu PI» cho giá trị máy).
    ({"design_code": "rct", "gate_params": {"G1": {"design": "cohort"}}}, ("cohort", True)),
    ({"design_code": "rct", "gate_params": {"G1": {"design": "cohort", "design_confirmed": True}}}, ("cohort", True)),
    ({"design_code": "rct", "design_code_nguon": "PI", "gate_params": {"G1": {"design": "cohort"}}}, ("rct", True)),
    ({"design_code": "   ", "gate_params": {"G1": {"design": "rct"}}}, ("rct", True)),   # X8: khoảng trắng = trống
    ({"gate_params": {"G1": {"design": "cohort"}}}, ("cohort", True)),                  # ô chỉ PI ghi
])
def test_ghim_thiet_ke_dau_nguoi(meta, ky_vong):
    assert S.ghim_thiet_ke(meta) == ky_vong


# ── (3) run_g1_auto: ghim chưa có dấu KHÔNG gỡ cờ mơ hồ ────────────────────────────────────────────────────────────
def _suy(internal="rct", ambiguous=True):
    return {"internal_code": internal, "primary": "RCT", "ambiguous": ambiguous, "alternative_1": "Cohort",
            "alternative_2": "Bệnh-chứng", "rationale": "[CẦN PI XÁC NHẬN] suy luận", "bias_controls": ["a"] * 7,
            "tu_khoa_bi_bo_qua": ["«tỷ lệ» gợi ý cross_sectional bị bỏ qua (treatment)"]}


def test_apply_ghim_chua_dau_trung_suy_luan_giu_co_mo_ho():
    d = G1._apply_design_pin(_suy(), "rct", {}, co_dau_nguoi=False)
    assert d["ambiguous"] is True and d["internal_code"] == "rct" and d["ghim_chua_co_dau_pi"] == "rct"
    assert d["tu_khoa_bi_bo_qua"] and d["alternative_1"] == "Cohort"


def test_apply_ghim_chua_dau_khac_suy_luan_dung_ghim_va_bat_co():
    d = G1._apply_design_pin(_suy(ambiguous=False), "cross_sectional", {}, co_dau_nguoi=False)
    assert d["internal_code"] == "cross_sectional" and d["ambiguous"] is True, d
    assert d["rationale"].startswith("[CẦN PI XÁC NHẬN]") and "BÁC SĨ pin" not in d["rationale"]
    assert d["alternative_1"] == G1._THAY_THE_GHIM_CHUA_DAU and "STROBE" in d["reporting_standard"]


def test_apply_ghim_co_dau_go_co_mo_ho_nhu_cu():
    d = G1._apply_design_pin(_suy(), "rct", {}, co_dau_nguoi=True)
    assert d["ambiguous"] is False and not d["tu_khoa_bi_bo_qua"] and "ghim_chua_co_dau_pi" not in d


# ── (4) Đường thật: G1 chạy lại sau khi G2 (kiểu cũ) gieo design_code ──────────────────────────────────────────────
def test_g1_chay_lai_sau_gieo_kieu_cu_khong_tu_go_co_mo_ho(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={})  # G0 chưa chốt loại câu hỏi ⇒ thiết kế MƠ HỒ
    assert cp["design"]["ambiguous"] is True
    meta = _meta(d)
    meta["design_code"] = cp["design"]["internal_code"]  # đúng việc run_g2_auto từng làm
    _ghi_meta(d, meta)
    _, cp2 = _chay_main(tmp_path, monkeypatch)
    assert cp2["design"]["ambiguous"] is True, cp2["design"]
    assert cp2["design"]["internal_code"] == cp["design"]["internal_code"]
    r = G1Q.evaluate_study("TEST-G1-MAIN", d, write=False)
    a04 = _row(r, "G1-AUTO-04")
    assert a04["status"] == "REVIEW" and "chưa có dấu PI" in a04["evidence"], a04
    assert _row(r, "G1-AUTO-04b")["status"] != "PASS"


@pytest.mark.parametrize("dau", [
    {"design_code_nguon": "PI"},
    {"gate_params": {"G1": {"design": "__TK__"}}},
])
def test_g1_ghim_co_dau_nguoi_van_go_co_mo_ho(tmp_path, monkeypatch, dau):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={})
    tk = cp["design"]["internal_code"]
    meta = _meta(d)
    meta["design_code"] = tk
    if "design_code_nguon" in dau:
        meta["design_code_nguon"] = dau["design_code_nguon"]
    else:
        meta.setdefault("gate_params", {}).setdefault("G1", {})["design"] = tk
    _ghi_meta(d, meta)
    _, cp2 = _chay_main(tmp_path, monkeypatch)
    assert cp2["design"]["ambiguous"] is False and "ghim_chua_co_dau_pi" not in cp2["design"], cp2["design"]


# ── (5) G1-AUTO-02d: chỉ ghim có dấu người mới hạ CHẶN xuống XEM ───────────────────────────────────────────────────
def _thiet_ke_cat_ngang():
    return _design(internal_code="cross_sectional", primary="Cắt ngang mô tả", reporting_standard="STROBE",
                   protocol_standard="STROBE (không có chuẩn protocol bắt buộc)")


def test_02d_design_code_khong_dau_van_chan(tmp_path):
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": {"question_type": "treatment"}}}
    a2d = _row(_evaluate(_build_case(tmp_path, meta=meta, design_value=_thiet_ke_cat_ngang())), "G1-AUTO-02d")
    assert a2d["status"] == "BLOCK", a2d


@pytest.mark.parametrize("them", [
    {"design_code_nguon": "PI"},
    {"gate_params": {"G0": {"question_type": "treatment"}, "G1": {"design": "cross_sectional"}}},
    {"gate_params": {"G0": {"question_type": "treatment"}, "G1": {"design_confirmed": True}}},
])
def test_02d_ghim_co_dau_chi_review(tmp_path, them):
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": {"question_type": "treatment"}}, **them}
    a2d = _row(_evaluate(_build_case(tmp_path, meta=meta, design_value=_thiet_ke_cat_ngang())), "G1-AUTO-02d")
    assert a2d["status"] == "REVIEW" and "PI đã ghim" in a2d["evidence"], a2d


# ── (6) MT-05: đề tài định tính chưa ghim đọc thiết kế G1 đang dùng (thay giá trị G2 từng gieo) ────────────────────
def test_mt05_dinh_tinh_doc_thiet_ke_tu_checkpoint_g1(tmp_path):
    d = _de_tai(tmp_path)
    m = MT.doc_meta(d)
    m.pop("design_code", None)
    m["gate_params"]["G1"].pop("design", None)
    m["gate_params"]["G1"]["objectives"] = ["Khám phá trải nghiệm chờ khám của người bệnh"]
    _ghi_meta(d, m)
    (d / "G1_checkpoint.json").write_text(json.dumps({"design": {"internal_code": "qualitative"}}),
                                          encoding="utf-8", newline="\n")
    _ghi_bo_bien(d, [("record_id", "text", "Mã", "", "", ""), ("ban_go_bang", "notes", "Bản gỡ băng", "", "", "")])
    _ghi_ma_tran(d, [("1", "trải nghiệm chờ khám", "mo_ta", "ban_go_bang", "van_ban", "", "phỏng vấn sâu", "§4")])
    kq = MT.kiem(d, STUDY_MT)
    assert not [x for x in kq["loi"] if "MT-05" in str(x)], kq["loi"]


# ── (7) Thẩm định #281 — Đ1 đường thật: G1.design của PI thắng design_code máy gieo ────────────────────────────────
def test_g1_design_cua_pi_thang_design_code_may_gieo(tmp_path, monkeypatch):
    d, cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    assert cp["design"]["internal_code"] == "cross_sectional"
    meta = _meta(d)
    meta["design_code"] = "cross_sectional"                       # G2 bản cũ gieo
    meta["gate_params"].setdefault("G1", {})["design"] = "cohort"  # PI làm theo lời khuyên G1-AUTO-04
    _ghi_meta(d, meta)
    _, cp2 = _chay_main(tmp_path, monkeypatch)
    assert cp2["design"]["internal_code"] == "cohort" and cp2["design"]["ambiguous"] is False, cp2["design"]
    meta = _meta(d)
    meta["gate_params"]["G1"]["design_confirmed"] = True
    _ghi_meta(d, meta)
    _, cp3 = _chay_main(tmp_path, monkeypatch)
    assert cp3["design"]["internal_code"] == "cohort", cp3["design"]
    h01 = _row(G1Q.evaluate_study("TEST-G1-MAIN", d, write=False), "G1-HUMAN-01")
    assert "'cohort'" in h01["evidence"] and "cross_sectional" not in h01["evidence"], h01


# ── (8) V4: ghim chưa có dấu vẫn giữ chuẩn báo cáo của đề tài + nhãn theo mục tiêu ──────────────────────────────────
def test_ghim_chua_dau_giu_chuan_mo_rong_va_nhan_theo_muc_tieu():
    meta = {"gate_params": {"G1": {"reporting_extensions": ["CROSS"],
                                   "objectives": ["Xác định tỷ lệ hài lòng của người bệnh",
                                                  "Phân tích một số yếu tố liên quan đến hài lòng"]}}}
    suy = {**_suy("cross_sectional", ambiguous=True), "primary": "Cắt ngang", "reporting_standard": "STROBE"}
    co = G1._apply_design_pin(dict(suy), "cross_sectional", meta, co_dau_nguoi=True)
    chua = G1._apply_design_pin(dict(suy), "cross_sectional", meta, co_dau_nguoi=False)
    assert "CROSS" in (co.get("reporting_extensions") or []), co
    for k in ("reporting_standard", "reporting_extensions", "primary"):
        assert chua.get(k) == co.get(k), (k, chua.get(k), co.get(k))
    assert chua["ambiguous"] is True
    khac = G1._apply_design_pin(_suy("rct", ambiguous=False), "cross_sectional", meta, co_dau_nguoi=False)
    assert khac.get("reporting_extensions") == co.get("reporting_extensions") and khac["primary"] == co["primary"]


# ── (9) V3: trục chuẩn báo cáo / mô tả thiết kế không biến mất ở đề tài chưa ghim ───────────────────────────────────
def test_nhat_quan_hai_truc_doc_thiet_ke_g1_khi_chua_ghim(tmp_path):
    import nhat_quan_xuyen_cong as NQ
    d = tmp_path / "exports" / "ZZ-NQ-CHUA-GHIM"
    d.mkdir(parents=True)
    meta = {"gate_params": {"G1": {"objectives": ["Xác định tỷ lệ", "Phân tích yếu tố liên quan"]}}}
    assert NQ._truc_chuan_bao_cao(d, d.name, meta, "") is None  # chưa có thiết kế nào ⇒ None (đúng như cũ)
    (d / "G1_checkpoint.json").write_text(json.dumps({"design": {"internal_code": "cross_sectional"}}),
                                          encoding="utf-8", newline="\n")
    assert NQ._truc_chuan_bao_cao(d, d.name, meta, "") is not None
    assert NQ._truc_mo_ta_thiet_ke(d, d.name, meta, "") is not None


# ── (10) X6: tổng quan hệ thống G1 đang dùng (chưa ghim) vẫn bị đòi tra PROSPERO ở G0-HUMAN-08 ─────────────────────
def test_g0_prospero_doc_thiet_ke_g1_khi_chua_ghim(tmp_path):
    import g0_quality_gate as G0Q
    from test_g0_hoan_thien_20261004 import _chot_lai
    from test_g0_quality_gate_20260728 import _artifact_text, _checkpoint, _confirmed_g0_meta
    a1 = tmp_path / "G0_A1_PICO_FINER_ZZ.md"
    a1.write_text(_artifact_text(), encoding="utf-8", newline="\n")
    cp = _checkpoint()
    g0 = _chot_lai(_confirmed_g0_meta())

    def _h8():
        r = G0Q.evaluate_g0_quality(checkpoint=cp, meta={"gate_params": {"G0": g0}}, artifact_text=_artifact_text(),
                                    artifact_paths={"A1": a1}, registry_check=cp.get("registry_check"))
        return _row(r, "G0-HUMAN-08")
    assert "prospero" not in _h8()["evidence"]
    (tmp_path / "G1_checkpoint.json").write_text(json.dumps({"design": {"internal_code": "sr_ma"}}),
                                                 encoding="utf-8", newline="\n")
    h8 = _h8()
    assert h8["status"] == "REVIEW" and "prospero" in h8["evidence"], h8
