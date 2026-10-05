# -*- coding: utf-8 -*-
"""Soát từng cổng + điều phối thống nhất G0–G10 (04/10/2026 — bác sĩ: «từng cổng phải hoàn thiện một cách triệt để,
sau đó là sự điều phối thống nhất giữa các cổng một cách triệt để»).

Khoá các hành vi:
  TỪNG CỔNG
  • G1: thiết kế bác sĩ GHIM ngoài 8 mã hỗ trợ ⇒ G1-AUTO-02c CHẶN; pin bị từ chối NẰM TRONG checkpoint; «case-control»
    (gạch nối) là case_control, không bị từ chối như mã lạ.
  • G4: §4 PHÂN TÍCH CHÍNH và §9 PHÂN TÍCH ĐỘ NHẠY còn «[CẦN» ⇒ chặn ký; SAP ĐÃ KÝ trước mốc không bị hạ cấp vì hai mục.
  • G7: thiết kế chưa có bảng checklist ⇒ tên chuẩn ĐÚNG + «[CẦN …]», KHÔNG rơi về STROBE/khuôn cohort.
  • G8: tín hiệu «phản biện đã duyệt» chấm sống qua bộ chấm G8 khi có hợp đồng chất lượng; không chấm được ⇒ False
    (không lùi về trạng thái lưu sẵn).
  ĐIỀU PHỐI
  • Nhạc trưởng, tổng quan đề tài, bộ xuất Word, audit: ĐỦ sáu cổng cứng theo gate_contract.
  • nhat_quan_xuyen_cong: N/α/power/thiết kế lệch ⇒ LỆCH CỨNG (G10 BLOCK); kết cục chính lệch ⇒ LỆCH MỀM (REVIEW) trừ
    khi chủ nhiệm xác nhận gắn dấu vân tay; «Non-interventional» là quan sát; «1.000» là một nghìn; dict không làm
    sập; thông số bắt buộc chưa đủ nơi để so ⇒ REVIEW; CLI hỏng ⇒ mã 3.
  • Độ tươi: mtime bị dàn phẳng (bản clone) ⇒ KHÔNG đo được (fresh=False), không báo «tươi» giả.
Ngoại tuyến (thư mục tạm).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import approve_gate as AG  # noqa: E402
import audit_research_gates as ARG  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import gen_research_docx as GRD  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as KCT  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import pipeline_freshness as PF  # noqa: E402
import research_studies_overview as RSO  # noqa: E402
import run_g1_auto as G1  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import run_pipeline as RP  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "de-tai-thu-dieu-phoi"
SAU_CONG_CUNG = ["G2", "G4", "G5", "G8", "G9", "G10"]


def _ghi(p: Path, v) -> None:
    """Ghi tệp thử với xuống dòng LF cố định (CRLF trên Windows phá hash — chốt kiem_newline_vung_ky)."""
    p.write_text(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")


# ───────────────────────────────────────────────────────────────────────────── dựng đề tài giả
def _de_tai(tmp_path: Path, *, n_g3=400, n_trds="400", n_sap=400, thiet_ke_g1="rct", thiet_ke_g3="rct",
            loai_trds="Interventional", kc_g0="Tử vong mọi nguyên nhân 30 ngày (biến TuVong_30N)",
            kc_sap="Tử vong mọi nguyên nhân sau 30 ngày (biến TuVong_30N)", ghi_trds=True, ghi_sap=True,
            quan_the_g0="Người lớn suy tim nhập viện tại khoa Nội tim mạch") -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    meta = {"design_code": thiet_ke_g1, "gate_params": {
        "G0": {"primary_outcome": kc_g0, "population": quan_the_g0},
        "G1": {"design": thiet_ke_g1, "primary_outcome": {"name": kc_g0},
               "population": "Người lớn suy tim nhập viện tại khoa Nội tim mạch, đủ 18 tuổi"},
        "G3": {"confirmed_n": n_g3}}}
    _ghi(out / "study_meta.json", meta)
    _ghi(out / "G3_checkpoint.json", {"design_code": thiet_ke_g3, "confirmed_n": n_g3, "alpha": 0.05, "power": 0.8})
    _ghi(out / "G4_checkpoint.json", {"design_code": thiet_ke_g1, "n_from_g3": n_g3})
    if ghi_trds:
        items = [{"number": "15", "label": "Study Type", "value": str({"design": loai_trds})},
                 {"number": "17", "label": "Target Sample Size", "value": n_trds},
                 {"number": "19", "label": "Primary Outcome(s)", "value": str({"name": kc_g0})}]
        _ghi(out / f"G2_REGISTRATION_DRAFT_{STUDY}.json", {"items": items})
    if ghi_sap:
        _ghi(out / f"G4_A5_SAP_FINAL_{STUDY}.md",
             f"## PHẦN 3, SAP 12 MỤC CUỐI\n\n### §2 KẾT CỤC\n\n- **Kết cục chính:** {kc_sap}\n\n"
             f"### §12 ALPHA + POWER\n\n- **Alpha (two-sided):** 0.05  \n- **Power:** 80%  \n"
             f"- **Cỡ mẫu:** N = {n_sap}  \n")
    return out


def _muc(ket, ma):
    return next(k for k in ket["thong_so"] if k["ma"] == ma)


def _sua_meta(out: Path, sua) -> None:
    meta = json.loads((out / "study_meta.json").read_text(encoding="utf-8"))
    sua(meta)
    _ghi(out / "study_meta.json", meta)


# ───────────────────────────────────────────────────────────────────────────── ĐIỀU PHỐI: nhất quán xuyên cổng
def test_de_tai_nhat_quan_moi_thong_so_khop_va_g10_pass(tmp_path):
    ket = NQ.doi_chieu(_de_tai(tmp_path), STUDY)
    for ma in ("co_mau", "alpha", "power", "thiet_ke", "ket_cuc_chinh", "quan_the"):
        assert _muc(ket, ma)["muc"] == NQ.MUC_KHOP, (ma, _muc(ket, ma))
    assert len(_muc(ket, "co_mau")["nguon"]) == 5, "N phải gom đủ G3 (2 nơi) · TRDS 17 · G4 n_from_g3 · SAP §12"
    assert NQ.tieu_chi_g10(ket)[0] == "PASS"


def test_co_mau_lech_giua_dang_ky_va_g3_la_lech_cung(tmp_path):
    ket = NQ.doi_chieu(_de_tai(tmp_path, n_trds="380"), STUDY)
    assert _muc(ket, "co_mau")["muc"] == NQ.MUC_LECH_CUNG and "[380, 400]" in _muc(ket, "co_mau")["ghi_chu"]
    trang_thai, bang_chung = NQ.tieu_chi_g10(ket)
    assert trang_thai == "BLOCK" and "|" not in bang_chung, "bằng chứng nằm trong ô bảng Markdown — không chứa «|»"


@pytest.mark.parametrize("ghi", ["1.000", "1,000", "1 000", "N = 1.000 người", 1000, "1000.0"])
def test_so_nghin_kieu_viet_va_kieu_anh_deu_la_mot_nghin(tmp_path, ghi):
    ket = NQ.doi_chieu(_de_tai(tmp_path, n_g3=1000, n_sap=1000, n_trds=ghi), STUDY)
    assert _muc(ket, "co_mau")["muc"] == NQ.MUC_KHOP, (ghi, _muc(ket, "co_mau"))


def test_so_vo_nghia_khong_dem_la_mot_noi_ghi():
    assert NQ._so_nguyen(0) is None and NQ._so_nguyen("-5") is None and NQ._so_nguyen(True) is None
    assert NQ._ty_le(0) is None and NQ._ty_le("150") is None
    assert NQ._ty_le("80%") == 0.8 and NQ._ty_le("0,05") == 0.05 and NQ._ty_le("α = 0.05 (two-sided)") == 0.05


def test_thiet_ke_lech_giua_cong_va_dang_ky_sai_loai_la_lech_cung(tmp_path):
    assert _muc(NQ.doi_chieu(_de_tai(tmp_path, thiet_ke_g3="cohort"), STUDY), "thiet_ke")["muc"] == NQ.MUC_LECH_CUNG
    ket = NQ.doi_chieu(_de_tai(tmp_path / "b", loai_trds="Observational"), STUDY)
    tk = _muc(ket, "thiet_ke")
    assert tk["muc"] == NQ.MUC_LECH_CUNG and "Observational" in tk["ghi_chu"], tk


@pytest.mark.parametrize("loai", ["Non-interventional", "non interventional", "Không can thiệp (quan sát)"])
def test_rct_khai_khong_can_thiep_o_dang_ky_la_lech_cung(tmp_path, loai):
    # Bản trước so CHUỖI CON: «interventional» nằm trong «Non-interventional» ⇒ RCT khai quan sát lọt qua.
    tk = _muc(NQ.doi_chieu(_de_tai(tmp_path, loai_trds=loai), STUDY), "thiet_ke")
    assert tk["muc"] == NQ.MUC_LECH_CUNG, (loai, tk)


def test_quan_sat_khai_non_interventional_la_khop(tmp_path):
    tk = _muc(NQ.doi_chieu(_de_tai(tmp_path, thiet_ke_g1="cohort", thiet_ke_g3="cohort",
                                   loai_trds="Non-interventional"), STUDY), "thiet_ke")
    assert tk["muc"] == NQ.MUC_KHOP, tk


def test_chan_doan_khai_interventional_chi_can_xem(tmp_path):
    ket = NQ.doi_chieu(_de_tai(tmp_path, thiet_ke_g1="diagnostic", thiet_ke_g3="diagnostic"), STUDY)
    assert _muc(ket, "thiet_ke")["muc"] == NQ.MUC_CAN_XEM
    assert NQ.tieu_chi_g10(ket)[0] == "PASS", "cơ quan đăng ký xếp nghiên cứu chẩn đoán khác nhau — không chặn"


def test_ket_cuc_chinh_doi_giua_cong_la_lech_mem(tmp_path):
    ket = NQ.doi_chieu(_de_tai(tmp_path, kc_sap="Nhập viện lại vì suy tim trong 90 ngày (biến TaiNhapVien_90N)"), STUDY)
    assert _muc(ket, "ket_cuc_chinh")["muc"] == NQ.MUC_LECH_MEM
    assert NQ.tieu_chi_g10(ket)[0] == "REVIEW"


def test_xac_nhan_cua_chu_nhiem_gan_dau_van_tay_moi_ha_lech_mem(tmp_path):
    out = _de_tai(tmp_path, kc_g0="Mức hài lòng chung của người bệnh",
                  kc_sap="Điểm hài lòng tổng thể khi rời phòng khám")
    kc = _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")
    assert kc["muc"] == NQ.MUC_LECH_MEM
    dau = NQ.dau_van_tay_ket_cuc(kc["nguon"])
    assert dau in kc["ghi_chu"], "CLI phải in dấu vân tay để chủ nhiệm chép"
    hom_qua = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")

    def xn(dau_vt, ngay=hom_qua, gt="Hai cách diễn đạt cùng một thang hài lòng chung, cùng biến"):
        _sua_meta(out, lambda m: m["gate_params"].setdefault("G10", {}).update(
            {"xac_nhan_ket_cuc_chinh": {"giai_trinh": gt, "reviewed_at": ngay, "dau_van_tay": dau_vt}}))
        return _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")

    assert xn(dau)["muc"] == NQ.MUC_CAN_XEM
    assert xn("0" * 16)["muc"] == NQ.MUC_LECH_MEM, "dấu vân tay khác ⇒ xác nhận không gắn với tập mô tả này"
    assert xn(dau, ngay="2099-12-31T00:00:00")["muc"] == NQ.MUC_LECH_MEM, "ngày ở tương lai ⇒ không hợp lệ"
    assert xn(dau, ngay="04/10/2026")["muc"] == NQ.MUC_LECH_MEM, "ngày không ISO ⇒ không hợp lệ"
    assert xn(dau, gt="ok")["muc"] == NQ.MUC_LECH_MEM, "giải trình rỗng nghĩa ⇒ không hợp lệ"
    # Xác nhận hợp lệ, rồi SAP đổi kết cục ⇒ dấu đổi ⇒ xác nhận hết hiệu lực.
    xn(dau)
    sap = out / f"G4_A5_SAP_FINAL_{STUDY}.md"
    _ghi(sap, sap.read_text(encoding="utf-8").replace("khi rời phòng khám", "sau 7 ngày qua điện thoại"))
    assert _muc(NQ.doi_chieu(out, STUDY), "ket_cuc_chinh")["muc"] == NQ.MUC_LECH_MEM


def test_cung_ma_bien_khac_dien_dat_van_la_mot_ket_cuc():
    assert NQ.cung_ket_cuc("G1 — mức hài lòng chung (biến SHLNBChung_TrucTiep)",
                           "G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_TrucTiep, Phần 3 phiếu)")
    assert not NQ.cung_ket_cuc("Tử vong (biến TuVong_30N)", "Tử vong (biến TuVong_90N)"), "khác mã biến ⇒ khác kết cục"
    assert not NQ.cung_ket_cuc("Tử vong", "Tử vong do tim mạch trong 30 ngày sau xuất viện"), \
        "cố ý chặt: bao hàm chuỗi không đủ để coi là cùng kết cục"


def test_gia_tri_dict_khong_lam_sap_bo_doi_chieu(tmp_path):
    out = _de_tai(tmp_path, quan_the_g0={"tieu_chi": "Người lớn suy tim nhập viện", "tuoi": ">= 18"})
    _sua_meta(out, lambda m: m["gate_params"]["G3"].update({"powered_for_outcome": {"ten": "Tử vong 30 ngày"}}))
    ket = NQ.doi_chieu(out, STUDY)
    assert _muc(ket, "quan_the")["muc"] in (NQ.MUC_KHOP, NQ.MUC_CAN_XEM)


def test_ham_so_tu_nhan_dict_va_list_truc_tiep():
    # Lớp phòng thủ thứ hai: hàm so từ tự nhận dict/list, không phụ thuộc nơi gọi đã chuẩn hoá trước.
    assert NQ._bao_ham({"tieu_chi": "suy tim"}, "người lớn suy tim nhập viện") == 1.0
    assert NQ.cung_ket_cuc(["Tử vong 30 ngày"], {"ten": "Tử vong 30 ngày"})


def test_mot_noi_ghi_la_chua_du_de_so_khong_phai_khop(tmp_path):
    out = tmp_path / "rong" / "exports" / STUDY
    out.mkdir(parents=True)
    _ghi(out / "study_meta.json", {"gate_params": {"G3": {"confirmed_n": 100}}})
    ket = NQ.doi_chieu(out, STUDY)
    assert _muc(ket, "co_mau")["muc"] == NQ.MUC_CHUA_DU
    trang_thai, bang_chung = NQ.tieu_chi_g10(ket)
    assert trang_thai == "REVIEW" and "CHƯA ĐỦ NƠI ĐỂ SO" in bang_chung, (trang_thai, bang_chung)


@pytest.mark.parametrize("thiet_ke,bat_buoc", [
    ("qualitative", ["thiet_ke"]), ("sr_ma", ["thiet_ke", "ket_cuc_chinh"]),
    ("systematic_review", ["thiet_ke", "ket_cuc_chinh"]), ("rct", ["thiet_ke", "co_mau", "ket_cuc_chinh"]),
    (None, ["thiet_ke", "co_mau", "ket_cuc_chinh"])])
def test_thong_so_bat_buoc_theo_thiet_ke(thiet_ke, bat_buoc):
    assert NQ.thong_so_bat_buoc(thiet_ke) == bat_buoc


def test_co_mau_tinh_cho_ket_cuc_thu_cap_la_can_xem_khong_doi_trang_thai(tmp_path):
    out = _de_tai(tmp_path)

    def sua(m):
        m["gate_params"]["G1"]["secondary_outcomes"] = ["Tỷ lệ nhập viện lại vì suy tim trong 90 ngày theo ngưỡng"]
        m["gate_params"]["G3"]["powered_for_outcome"] = "Cỡ mẫu tính cho tỷ lệ nhập viện lại vì suy tim trong 90 ngày"
    _sua_meta(out, sua)
    ket = NQ.doi_chieu(out, STUDY)
    assert _muc(ket, "co_mau_cho_ket_cuc")["muc"] == NQ.MUC_CAN_XEM
    assert NQ.tieu_chi_g10(ket)[0] == "PASS", "CẦN XEM chỉ báo, không đổi trạng thái G10"


def test_cli_ma_thoat_theo_trang_thai_g10(tmp_path, monkeypatch):
    monkeypatch.setattr(NQ, "BASE", tmp_path)
    _de_tai(tmp_path, n_trds="380")
    assert NQ.main(["--study", STUDY]) == 2
    assert NQ.main(["--study", "khong-co"]) == 3


def test_cli_lech_mem_ma_1_va_bo_doi_chieu_hong_ma_3(tmp_path, monkeypatch):
    monkeypatch.setattr(NQ, "BASE", tmp_path)
    _de_tai(tmp_path, kc_sap="Nhập viện lại vì suy tim trong 90 ngày (biến TaiNhapVien_90N)")
    assert NQ.main(["--study", STUDY]) == 1

    def hong(*_a, **_k):
        raise KeyError("thong_so")
    monkeypatch.setattr(NQ, "doi_chieu", hong)
    assert NQ.main(["--study", STUDY]) == 3, "bộ đối chiếu hỏng ⇒ KHÔNG ĐO ĐƯỢC (mã 3), không bao giờ mã 0"


def test_g10_that_co_tieu_chi_xuyen_cong_va_chan_khi_lech_cung(tmp_path):
    out = _de_tai(tmp_path, n_trds="380")
    r = G10Q.evaluate_study(STUDY, out, repo_root=tmp_path, write=False)
    row = next(c for c in r["automatic_criteria"] if c["id"] == "G10-AUTO-11")
    assert row["status"] == "BLOCK" and "Cỡ mẫu" in row["evidence"], row


def test_kiem_chi_tiet_co_muc_xuyen_cong_va_cong_cung_tu_gate_contract(tmp_path):
    muc = KCT.kiem_xuyen_cong(STUDY, _de_tai(tmp_path, n_trds="380"))
    co_mau = next(m for m in muc if m.nhan.startswith("Cỡ mẫu kế hoạch"))
    assert co_mau.muc == KCT.DO and co_mau.cong == "XUYÊN"
    assert list(KCT.CONG_CUNG) == SAU_CONG_CUNG


# ───────────────────────────────────────────────────────────────────────────── ĐIỀU PHỐI: sáu cổng cứng ở mọi công cụ
def test_nhac_truong_rut_cong_cung_tu_gate_contract_va_bao_g8(tmp_path, monkeypatch):
    assert RP._hard_gates() == SAU_CONG_CUNG
    assert set(RP._hard_gates()) - {"G10"} <= set(RP.HARD_GATE_SIGNAL), "mọi cổng cứng (trừ G10 xử riêng) có tín hiệu"
    for g in ("G2", "G4", "G5", "G8", "G9"):
        _ghi(tmp_path / f"{g}_checkpoint.json", '{"study": "x"}')
    monkeypatch.setattr(RP.SKILL, "real_world_signals", lambda cps, meta: {})
    bao = {h["gate"]: h for h in RP._hard_gate_report(tmp_path, {})}
    assert "G8" in bao and bao["G8"]["locked"] is False and "phản biện" in bao["G8"]["state"]
    monkeypatch.setitem(GC._GATE_REQUIRED_STAKEHOLDERS, "G6", ("PI",))
    _ghi(tmp_path / "G6_checkpoint.json", '{"study": "x"}')
    bao = {h["gate"]: h for h in RP._hard_gate_report(tmp_path, {})}
    assert "CHƯA CÓ TÍN HIỆU" in bao["G6"]["state"] and bao["G6"]["locked"] is False


def test_tong_quan_de_tai_bao_du_sau_cong_cung(tmp_path, monkeypatch):
    assert RSO._hard_gates() == SAU_CONG_CUNG
    cps = {g: {"study": "x"} for g in SAU_CONG_CUNG}
    monkeypatch.setattr(RSO.SKILL, "real_world_signals", lambda cps, meta: {"release_locked": True})
    bao = {h["gate"]: h for h in RSO._hard_gate_states(cps, {})}
    assert list(bao) == SAU_CONG_CUNG
    assert bao["G10"]["locked"] is True and bao["G8"]["locked"] is False


def test_bo_xuat_word_va_audit_dung_tap_cong_cung_that():
    assert [g for g, _ in GRD._cong_cung()] == SAU_CONG_CUNG
    hang = {"status": ARG.STATUS_NEEDS_REAL}
    assert ARG._gate_action_actor(dict(hang, gate="G8"), []) == "human_independent_reviewer"
    assert ARG._gate_action_actor(dict(hang, gate="G5"), []) == "human_pi_or_data_manager"
    assert ARG._gate_action_actor(dict(hang, gate="G10"), []) == "human_pi_or_irb"
    assert ARG._gate_action_actor(dict(hang, gate="G2"), []) == "human_pi_or_irb"


# ───────────────────────────────────────────────────────────────────────────── TỪNG CỔNG
def test_g8_khong_tin_co_tu_khai_khi_co_hop_dong_chat_luong(tmp_path, monkeypatch):
    import g8_quality_gate as G8Q
    g8 = {"quality_contract_version": "G8-2026.1", "study": STUDY}
    monkeypatch.setattr(SK, "_GOC_REPO", tmp_path)
    # Thư mục đề tài vắng ⇒ không chấm được ⇒ False, KỂ CẢ khi study_meta tự khai trạng thái đã duyệt.
    assert SK.real_world_signals({"G8": g8}, {"peer_review_approved": True})["peer_review_approved"] is False
    tu_khai = {"g8_quality_status": G8Q.STATUS_REVIEWED}
    assert SK.real_world_signals({"G8": g8}, tu_khai)["peer_review_approved"] is False
    (tmp_path / "exports" / STUDY).mkdir(parents=True)
    goi = []

    def cham(study, out_dir, **kw):
        goi.append((study, Path(out_dir), kw.get("write")))
        return {"status": G8Q.STATUS_REVIEWED}
    monkeypatch.setattr(G8Q, "evaluate_study", cham)
    assert SK.real_world_signals({"G8": g8}, {})["peer_review_approved"] is True
    assert goi == [(STUDY, tmp_path / "exports" / STUDY, False)], "chấm SỐNG, chỉ đọc (write=False)"

    def hong(*_a, **_k):
        raise KeyError("x")
    monkeypatch.setattr(G8Q, "evaluate_study", hong)
    assert SK.real_world_signals({"G8": g8}, {})["peer_review_approved"] is False, "bộ chấm hỏng ⇒ bi quan, không sập"
    assert SK.real_world_signals({"G8": {}}, {"peer_review_approved": True})["peer_review_approved"] is True, \
        "checkpoint cũ (chưa có hợp đồng chất lượng) giữ hành vi cũ"


def test_g4_chan_ky_khi_phan_tich_chinh_hoac_do_nhay_con_trong():
    sap = ("### §1 QUẦN THỂ\n\nĐủ\n\n### §2 KẾT CỤC\n\nĐủ\n\n### §4 PHÂN TÍCH CHÍNH\n\n"
           "- [CẦN BÁC SĨ ĐIỀN] phương pháp\n\n### §5 ĐA BIẾN\n\nĐủ\n\n### §9 PHÂN TÍCH ĐỘ NHẠY\n\n- [CẦN] kịch bản\n\n"
           "### §10 PHẦN MỀM\n\nR 4.4, seed 2026\n")
    con = {s.split()[0] for s in AG._g4_sections_still_draft(sap)}
    assert con == {"§4", "§9"}, con


def _g4_sap_day_du(monkeypatch, *, con, ledger_signed):
    """SAP đầy đủ của bộ test G4 (không chặn gì ⇒ LOCKED khi đã ký), rồi giả lập mục còn «[CẦN» ở G4-AUTO-10."""
    from tests.test_g4_quality_gate import _evaluate
    # 04/10/2026 (soát từng cổng G4): hàm nhận thêm design_code (RCT ⇒ §13–§15 bắt buộc).
    monkeypatch.setattr(AG, "_g4_sections_still_draft", lambda _t, _thiet_ke=None: list(con))
    r = _evaluate(ledger_signed=ledger_signed, ledger_reason="" if ledger_signed else "chưa ký")
    return next(c for c in r["automatic_criteria"] if c["id"] == "G4-AUTO-10"), r


def test_g4_sap_da_ky_truoc_moc_khong_bi_ha_cap_vi_4_9(monkeypatch):
    row, r = _g4_sap_day_du(monkeypatch, con=["§4 Phân tích chính", "§9 Phân tích độ nhạy"], ledger_signed=True)
    assert row["status"] == "REVIEW" and "amendment" in row["evidence"], row
    assert r["status"] == G4Q.STATUS_LOCKED, "G4-AUTO-10 (chỉ §4/§9) không được kéo SAP đã ký về DRAFT"


def test_g4_muc_bat_buoc_cu_van_ha_cap_ca_khi_da_ky(monkeypatch):
    row, r = _g4_sap_day_du(monkeypatch, con=["§2 Kết cục chính", "§9 Phân tích độ nhạy"], ledger_signed=True)
    assert row["status"] == "REVIEW" and "amendment" not in row["evidence"]
    assert r["status"] == G4Q.STATUS_DRAFT


def test_g4_chua_ky_ma_4_9_trong_van_ha_cap(monkeypatch):
    row, r = _g4_sap_day_du(monkeypatch, con=["§4 Phân tích chính"], ledger_signed=False)
    assert row["status"] == "REVIEW" and r["status"] == G4Q.STATUS_DRAFT


def test_g1_chan_khi_thiet_ke_ghim_bi_tu_choi(tmp_path):
    _ghi(tmp_path / "study_meta.json", {"design_code": "quality_improvement"})
    assert G1._read_pinned_design(tmp_path) == "" and G1._raw_pinned_design(tmp_path) == "quality_improvement"
    r = G1Q.evaluate_g1_quality(design={"internal_code": "cohort", "pin_bi_tu_choi": "quality_improvement"},
                                artifact_texts={}, artifact_paths={}, g0_checkpoint={}, meta={},
                                evidence_identifiers={})
    row = next(c for c in r["automatic_criteria"] if c["id"] == "G1-AUTO-02c")
    assert row["status"] == "BLOCK" and "quality_improvement" in row["evidence"]
    r = G1Q.evaluate_g1_quality(design={"internal_code": "cohort"}, artifact_texts={}, artifact_paths={},
                                g0_checkpoint={}, meta={}, evidence_identifiers={})
    assert next(c for c in r["automatic_criteria"] if c["id"] == "G1-AUTO-02c")["status"] == "PASS"


def test_g1_checkpoint_mang_pin_bi_tu_choi(tmp_path):
    design = {"primary": "Cohort", "internal_code": "cohort", "reporting_standard": "STROBE 2007",
              "alternative_1": "n/a", "pin_bi_tu_choi": "quality_improvement"}
    cp = json.loads(G1.write_g1_checkpoint("PYTEST-PIN", tmp_path, "descriptive", design, [],
                                           {"passed": True, "errors": []}, tmp_path / "a2.md", None)
                    .read_text(encoding="utf-8"))
    assert cp["design"]["pin_bi_tu_choi"] == "quality_improvement"
    design.pop("pin_bi_tu_choi")
    cp = json.loads(G1.write_g1_checkpoint("PYTEST-PIN", tmp_path, "descriptive", design, [],
                                           {"passed": True, "errors": []}, tmp_path / "a2.md", None)
                    .read_text(encoding="utf-8"))
    assert "pin_bi_tu_choi" not in cp["design"]


@pytest.mark.parametrize("ghim,ma", [("case-control", "case_control"), ("Cross sectional", "cross_sectional"),
                                     ("Cross-Sectional", "cross_sectional"), ("RCT", "rct"),
                                     ("systematic-review", "sr_ma")])
def test_ghim_thiet_ke_gach_noi_khoang_trang_van_nhan(ghim, ma):
    assert G1._canonicalize_pinned_design_code(ghim) == ma
    assert SK.canonical_design_code(ghim) == SK.canonical_design_code(ma)


@pytest.mark.parametrize("thiet_ke,chuan", [("quality_improvement", "SQUIRE 2.0"), ("case_report", "CARE"),
                                            ("non_randomized", "TREND")])
def test_g7_khong_roi_ve_strobe_khi_chua_co_checklist(thiet_ke, chuan):
    ten, tong, muc = G7._checklist_cho_thiet_ke(thiet_ke)
    assert ten.startswith(chuan) and "[CẦN BỔ SUNG DANH MỤC" in ten and tong == 0 and muc == []
    assert muc is not G7.CHECKLIST_ITEMS["cohort"]


def test_g7_thiet_ke_co_bang_van_dung_checklist_cua_no():
    ten, tong, muc = G7._checklist_cho_thiet_ke("rct")
    assert ten.startswith("CONSORT") and tong == 30 and muc == G7.CHECKLIST_ITEMS["rct"]


# ───────────────────────────────────────────────────────────────────────────── ĐIỀU PHỐI: độ tươi
def _cp(out: Path, gate: str, ngay: str, mtime: float):
    p = out / f"{gate}_checkpoint.json"
    _ghi(p, {"generated_at": ngay})
    os.utime(p, (mtime, mtime))


def test_mtime_bi_dan_phang_la_khong_do_duoc_khong_phai_tuoi(tmp_path):
    # G2↔G3 phụ thuộc nhau ⇒ cần đủ G0–G3 để không có cổng mồ côi.
    for g, ngay in (("G0", "2026-07-01T10:00:00"), ("G1", "2026-07-05T10:00:00"), ("G2", "2026-08-20T10:00:00"),
                    ("G3", "2026-08-20T11:00:00")):
        _cp(tmp_path, g, ngay, 1_790_000_000.0)
    rep = PF.stale_report(tmp_path)
    assert rep["fresh"] is False and rep["mtime_khong_tin_duoc"], rep
    assert rep["stale_gates"] == [] and rep["orphan_gates"] == [], "không tự đánh dấu cổng nào để chạy lại hàng loạt"


def test_mtime_that_khong_bi_nham_la_dan_phang(tmp_path):
    for g, ngay, mt in (("G0", "2026-07-01T10:00:00", 1_780_000_000.0), ("G1", "2026-07-05T10:00:00", 1_780_400_000.0),
                        ("G2", "2026-08-20T10:00:00", 1_784_000_000.0), ("G3", "2026-08-20T10:01:00", 1_784_000_060.0)):
        _cp(tmp_path, g, ngay, mt)
    rep = PF.stale_report(tmp_path)
    assert rep["mtime_khong_tin_duoc"] is None and rep["fresh"] is True


# ───────────────────────────────────────────────────────────────────────────── dòng THI HÀNH (không chỉ có hàm)
def _dong_thi_hanh(tep: str, dong: str) -> bool:
    """Chốt khớp chuỗi phải khớp DÒNG THI HÀNH, không khớp bình luận (CLAUDE.md §0.8)."""
    return any(x.strip().startswith(dong) for x in (TOOLS / tep).read_text(encoding="utf-8").splitlines())


def test_g1_main_ghi_pin_bi_tu_choi_vao_design():
    assert _dong_thi_hanh("run_g1_auto.py", 'design["pin_bi_tu_choi"] = raw_pin')


def test_nhac_truong_dua_tom_tat_xuyen_cong_vao_bao_cao(tmp_path):
    assert _dong_thi_hanh("run_pipeline.py", '"nhat_quan_xuyen_cong": _nhat_quan_tom_tat(out_dir, study),')
    tt = RP._nhat_quan_tom_tat(_de_tai(tmp_path, n_trds="380"), STUDY)
    assert tt["muc_cao_nhat"] == NQ.MUC_LECH_CUNG and any(k["ma"] == "co_mau" for k in tt["lech"])


def test_kiem_de_tai_that_co_muc_xuyen_cong(tmp_path):
    r = KCT.kiem_de_tai(STUDY, _de_tai(tmp_path, n_trds="380"), canary=False)
    xc = [m for m in r["muc"] if m["cong"] == "XUYÊN"]
    assert xc and any(m["muc"] == KCT.DO for m in xc), xc
