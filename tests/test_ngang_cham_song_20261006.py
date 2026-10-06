# -*- coding: utf-8 -*-
"""Đợt NGANG (06/10/2026, soát từng cổng G0–G10) — công cụ HIỂN THỊ/ĐIỀU PHỐI đọc cùng MỘT định nghĩa trạng thái cổng.

CHUNG-A (gốc lỗi lặp ở nhiều cổng): công cụ đọc `quality_gate.status` LƯU trong checkpoint thay vì chấm lại. Sau khi
11 cổng đều chấm sống tiền đề (G7–G10 dùng cong_song / g7_quality_gate.tien_de_song), các công cụ còn đọc bản lưu là:
  • study_readiness._gate_state — cổng mềm «✅ có checkpoint», G0 đọc trạng thái lưu, cổng cứng «🔒» khi có chữ ký dù
    hợp đồng đã mất hiệu lực;
  • audit_research_gates._classify_gate — mọi nhánh G0–G9 đọc trạng thái lưu, khối guardrail lúc sinh artifact;
  • kiem_chi_tiet_he_nghien_cuu._cham_song — G1 đọc báo cáo lưu (G1 nay đã có evaluate_study), SystemExit rơi về bản
    lưu;
  • skill_standards.real_world_signals — «IRB đã duyệt» theo quality_gate.status LƯU của G2; results_final dùng bool().
G0-06 + G4→G10: nhat_quan_xuyen_cong thêm hai trục — loại giả thuyết (G0 ↔ G3 ↔ SAP §12) và sai số d (G3 ↔ SAP §12).
Mọi luồng có ký chạy trong pytest với khoá giả tạm. Không PII.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import audit_research_gates as ARG  # noqa: E402
import cong_song as CS  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as KCT  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import skill_standards as S  # noqa: E402
import study_readiness as SR  # noqa: E402

from tests._chuoi_da_chot import (  # noqa: E402,E501
    dien_sap_g4,
    dung_g0_g1_da_chot,
    dung_g0_g3_da_chot,
    sinh_sap_g4_that,
    xac_nhan_g4,
)
from tests.g5_test_helpers import append_signed_approval, configure_test_signing_key  # noqa: E402
from tests.test_g10_hoan_thien_20261005 import _de_tai_truoc_irb  # noqa: E402


def _dong(rows, gate: str) -> str:
    return next(state for g, _nhan, state in rows if g == gate)


def _sua_g0_sau_khi_chot(d: Path) -> None:
    """Bác sĩ sửa PICO SAU khi chốt (dấu vân tay lệch) nhưng checkpoint vẫn LƯU PASS_G0_CONFIRMED (C1a 04/10/2026)."""
    cp = json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8"))
    cp["quality_gate"] = {"status": "PASS_G0_CONFIRMED", "pending_actions": []}
    (d / "G0_checkpoint.json").write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")
    meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G0"]["population"] = "Quần thể đã sửa SAU khi bác sĩ chốt PICO"
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    CS.xoa_dem()


# ── đài kiểm soát (audit_research_gates) ─────────────────────────────────────────────────────────────────────────────

def test_dai_kiem_soat_khong_tin_trang_thai_luu_cua_g0(tmp_path):
    d = tmp_path / "exports" / "S-NG"
    dung_g0_g1_da_chot(d, "S-NG")
    CS.xoa_dem()
    g0 = next(r for r in ARG.audit_gates("S-NG", out_dir=d, write=False)["pipeline_gates"] if r["gate"] == "G0")
    assert g0["trang_thai_song"]["muc"] == "PASS" and g0["status"] != ARG.STATUS_NEEDS_REAL, g0
    _sua_g0_sau_khi_chot(d)
    g0 = next(r for r in ARG.audit_gates("S-NG", out_dir=d, write=False)["pipeline_gates"] if r["gate"] == "G0")
    assert g0["trang_thai_song"]["muc"] == "DRAFT", g0
    assert g0["status"] == ARG.STATUS_NEEDS_REAL, g0  # bản cũ: READY theo PASS_G0_CONFIRMED lưu sẵn


def test_dai_kiem_soat_g2_san_sang_nop_chua_duyet_la_viec_cua_irb(tmp_path, monkeypatch):
    study, out, _goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    CS.xoa_dem()
    g2 = next(r for r in ARG.audit_gates(study, out_dir=out, write=False)["pipeline_gates"] if r["gate"] == "G2")
    assert g2["trang_thai_song"]["muc"] == "READY", g2
    assert g2["status"] == ARG.STATUS_NEEDS_REAL and g2["can_auto_run"] is False, g2
    # Tín hiệu đời thực trên CÙNG thư mục: chưa duyệt IRB, SAP chưa ký ⇒ không bật (chấm sống, không suy từ artifact).
    import run_g10_assemble as G10A

    tin_hieu = S.real_world_signals(G10A.load_checkpoints(out), G10A.load_meta(out), out_dir=out)
    assert tin_hieu["irb_approved"] is False and tin_hieu["sap_locked"] is False, tin_hieu


# ── study_readiness ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_study_readiness_cham_song_cong_cung_chua_ky_va_cong_mem(tmp_path, monkeypatch):
    study, out, _goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    CS.xoa_dem()
    rows = SR._gate_state(study, out)
    assert _dong(rows, "G1").startswith("✅ ĐÃ CHỐT"), rows  # bản cũ: «✅ có checkpoint» với mọi trạng thái
    assert _dong(rows, "G3").startswith("✅ ĐÃ CHỐT"), rows
    for gate in ("G2", "G4"):
        assert _dong(rows, gate).startswith("📝 CHƯA AI KÝ — 🟢 SẴN SÀNG"), (gate, rows)
    assert _dong(rows, "G5") == "— chưa chạy"


def test_study_readiness_chu_ky_mat_hieu_luc_khong_tinh_la_khoa(tmp_path, monkeypatch, capsys):
    """SAP đã ký (sổ cái khớp ĐÚNG tệp SAP) nhưng cỡ mẫu G3 đổi SAU khi ký ⇒ G4 chấm sống không còn khoá (G4-AUTO-12) ⇒
    «⚠️ CÓ CHỮ KÝ nhưng KHÔNG còn hiệu lực», không đếm vào «chữ ký thật»."""
    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    khoa_vai = Path(os.environ["EBM_GATE_KEY_PATH"])
    khoa_vai.with_name(khoa_vai.name + "_STATISTICIAN").write_text("pytest-g4-statistician-role-key", encoding="utf-8",
                                                                    newline="\n")
    append_signed_approval(study, out / G4Q.sap_artifact_name(study), "G4", "METHODS_STATISTICS_REVIEWER",
                           repo_root=goc)
    CS.xoa_dem()
    assert _dong(SR._gate_state(study, out), "G4").startswith("🔒 ĐÃ KHOÁ"), SR._gate_state(study, out)
    cp3 = json.loads((out / "G3_checkpoint.json").read_text(encoding="utf-8"))
    cp3["confirmed_n"] = int(cp3.get("confirmed_n") or cp3.get("n_adjusted") or 100) + 50
    (out / "G3_checkpoint.json").write_text(json.dumps(cp3, ensure_ascii=False), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    assert _dong(SR._gate_state(study, out), "G4").startswith("⚠️ CÓ CHỮ KÝ nhưng KHÔNG còn hiệu lực")
    monkeypatch.setattr(SR, "_study_dir", lambda _s: out)
    SR.report(study)
    ra = capsys.readouterr().out
    assert "chữ ký thật: 0/6" in ra and "KHÔNG còn hiệu lực khi chấm sống: G4" in ra, ra


# ── kiem_chi_tiet_he_nghien_cuu ──────────────────────────────────────────────────────────────────────────────────────

def test_kiem_chi_tiet_cham_song_g1_khong_doc_bao_cao_luu(tmp_path):
    d = tmp_path / "exports" / "S-KCT"
    dung_g0_g1_da_chot(d, "S-KCT")
    (d / "G1_QUALITY_REPORT.json").write_text(json.dumps({"status": "BLOCKED"}), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    rep, cach = KCT._cham_song("G1", "S-KCT", d)
    assert cach == "chấm sống" and rep["status"] == "PASS_G1_CONFIRMED", (cach, rep and rep.get("status"))


def test_kiem_chi_tiet_bo_cham_hong_la_chet_khong_lui_ve_ban_luu(tmp_path, monkeypatch):
    d = tmp_path / "exports" / "S-KCT2"
    dung_g0_g1_da_chot(d, "S-KCT2")
    (d / "G1_QUALITY_REPORT.json").write_text(json.dumps({"status": "PASS_G1_CONFIRMED"}), encoding="utf-8",
                                              newline="\n")
    import g1_quality_gate as G1Q

    def _hong(*_a, **_k):
        raise SystemExit(4)

    monkeypatch.setattr(G1Q, "evaluate_study", _hong)
    CS.xoa_dem()
    rep, cach = KCT._cham_song("G1", "S-KCT2", d)
    assert rep is None and cach.startswith("chết"), (rep, cach)  # bản cũ: SystemExit ⇒ dùng báo cáo LƯU


# ── skill_standards.real_world_signals ───────────────────────────────────────────────────────────────────────────────

def test_tin_hieu_irb_khong_tin_trang_thai_luu_cua_g2():
    """G2 có hợp đồng nhưng không chấm sống được (thư mục đề tài không có ở exports/ của repo) ⇒ chưa duyệt. Bản cũ:
    quality_gate.status LƯU = PASS_G2_APPROVED ⇒ irb_approved=True."""
    g2 = {"quality_contract_version": "G2-2026.1", "study": "KHONG-CO-THU-MUC-NG",
          "quality_gate": {"status": "PASS_G2_APPROVED"}}
    assert S.real_world_signals({"G2": g2})["irb_approved"] is False
    # Checkpoint CÓ hợp đồng: cờ tự khai trong study_meta không thay được phê duyệt thật (chỉ checkpoint kiểu cũ mới
    # nhận).
    assert S.real_world_signals({"G2": g2}, {"irb_approved": True})["irb_approved"] is False
    assert S.real_world_signals({"G2": {"g2_status": "x"}}, {"irb_approved": True})["irb_approved"] is True


def test_results_final_chi_nhan_true_that():
    for gia_tri, mong in ((True, True), ("false", False), ("chưa", False), (1, False), (None, False)):
        assert S.real_world_signals({}, meta={"results_final": gia_tri})["results_final"] is mong, gia_tri


# ── nhat_quan_xuyen_cong: hai trục mới ───────────────────────────────────────────────────────────────────────────────

def _truc(out: Path, study: str, ma: str) -> dict:
    return next(k for k in NQ.doi_chieu(out, study)["thong_so"] if k["ma"] == ma)


def _sinh_sap(out: Path, study: str) -> Path:
    sap = sinh_sap_g4_that(out, study)
    noi_dung = dien_sap_g4(sap.read_text(encoding="utf-8"))
    sap.write_text(noi_dung, encoding="utf-8", newline="\n")
    xac_nhan_g4(out, noi_dung)
    return sap


def test_truc_gia_thuyet_va_sai_so_d_thiet_ke_mo_ta(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    out = tmp_path / "exports" / "S-CX"
    dung_g0_g3_da_chot(out, "S-CX", thiet_ke="cross_sectional")
    sap = _sinh_sap(out, "S-CX")
    gt, d = _truc(out, "S-CX", "loai_gia_thuyet"), _truc(out, "S-CX", "sai_so_d")
    assert gt["muc"] == NQ.MUC_KHOP and d["muc"] == NQ.MUC_KHOP, (gt, d)
    # Checkpoint G3 kiểu C1a (đo 06/10/2026): hypothesis_type LƯU giá trị mặc định «superiority» dù N tính theo độ chính
    # xác (effect_type PREVALENCE) ⇒ vẫn là «mô tả», không báo lệch cứng oan với G0 «descriptive».
    cp3 = json.loads((out / "G3_checkpoint.json").read_text(encoding="utf-8"))
    cp3["hypothesis_type"] = "superiority"
    (out / "G3_checkpoint.json").write_text(json.dumps(cp3, ensure_ascii=False), encoding="utf-8", newline="\n")
    gt = _truc(out, "S-CX", "loai_gia_thuyet")
    assert gt["muc"] == NQ.MUC_KHOP, gt
    # SAP ký một sai số d khác G3 đã tính ⇒ N trong SAP không còn do d đó quyết định.
    sap.write_text(sap.read_text(encoding="utf-8").replace("cho phép (d):** ±0.05", "cho phép (d):** ±0.03"),
                   encoding="utf-8", newline="\n")
    d = _truc(out, "S-CX", "sai_so_d")
    assert d["muc"] == NQ.MUC_LECH_CUNG, d
    assert NQ.tieu_chi_g10(NQ.doi_chieu(out, "S-CX"))[0] == "BLOCK"


def test_truc_gia_thuyet_g0_khong_kem_hon_ma_g3_tinh_uu_the_la_lech_cung(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    out = tmp_path / "exports" / "S-RCT"
    dung_g0_g3_da_chot(out, "S-RCT", thiet_ke="rct")
    assert _truc(out, "S-RCT", "loai_gia_thuyet")["muc"] == NQ.MUC_KHOP
    meta = json.loads((out / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"]["G0"]["test_type"] = "non_inferiority"
    (out / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    gt = _truc(out, "S-RCT", "loai_gia_thuyet")
    assert gt["muc"] == NQ.MUC_LECH_CUNG and "non_inferiority" in gt["ghi_chu"], gt


def test_truc_gia_thuyet_bo_qua_g3_khi_n_khong_tinh_theo_gia_thuyet(tmp_path, monkeypatch):
    """Định tính: G0 «mô tả», G3 chốt N theo bão hoà (hypothesis_type chỉ là mặc định của bộ tính) ⇒ không đem G3 ra so,
    không báo lệch oan."""
    configure_test_signing_key(tmp_path, monkeypatch)
    out = tmp_path / "exports" / "S-QL"
    dung_g0_g3_da_chot(out, "S-QL", thiet_ke="qualitative")
    gt = _truc(out, "S-QL", "loai_gia_thuyet")
    assert gt["muc"] != NQ.MUC_LECH_CUNG and all(n["cong"] != "G3" for n in gt["nguon"]), gt


def test_g10_cham_lai_de_cuong_khong_de_quy_qua_tin_hieu_doi_thuc(tmp_path, monkeypatch):
    """Lỗi do chính bản vá G10-02 (dbcab0a) gây ra, sửa 06/10/2026: G10.evaluate_study → check_de_cuong.validate (chấm
    lại đề cương) → skill_standards.real_world_signals → G10.evaluate_study … đệ quy tới RecursionError (bị nuốt thành
    «chưa khoá»; ~23 giây/lần trên C1a). Tín hiệu đời thực nay chấm qua cong_song (đệm + chốt vòng lặp) ⇒ một lượt chấm
    G10 gọi bộ chấm G10 tối đa HAI lần (lượt ngoài + một lượt lồng bị cong_song cắt ở tầng sau)."""
    import g10_quality_gate as G10Q

    study, out, goc = _de_tai_truoc_irb(tmp_path, monkeypatch)
    that = G10Q.evaluate_study
    dem = {"n": 0}

    def _dem(*a, **k):
        dem["n"] += 1
        return that(*a, **k)

    monkeypatch.setattr(G10Q, "evaluate_study", _dem)
    CS.xoa_dem()
    bao = G10Q.evaluate_study(study, out, repo_root=goc, write=False)
    assert bao["status"] == G10Q.STATUS_READY
    assert dem["n"] <= 2, dem


# ── bổ sung sau lượt đột biến đầu (06/10/2026) ──────────────────────────────────────────────────────────────────────

def test_tin_hieu_doi_thuc_va_study_readiness_tren_chuoi_khoa_that(tmp_path, monkeypatch):
    """Chuỗi THẬT G0→G10 khoá: tín hiệu đời thực chấm SỐNG đúng thư mục đề tài đang xét (tham số tường minh hoặc ngữ
    cảnh lắp ráp G10); study_readiness khoá đủ sáu cổng cứng — G2 theo định nghĩa dùng chung g2_da_duyet (sổ cái + hợp
    đồng), không theo bộ chấm hồ sơ G2."""
    import run_g10_assemble as G10A

    from tests.test_g10_hoan_thien_20261005 import _de_tai_g10_that, _ky_g10

    study, out, goc = _de_tai_g10_that(tmp_path, monkeypatch)
    _ky_g10(study, out, goc)
    CS.xoa_dem()
    cps, meta = G10A.load_checkpoints(out), G10A.load_meta(out)  # load_checkpoints chỉ đọc G0–G9
    cps["G10"] = json.loads((out / "G10_checkpoint.json").read_text(encoding="utf-8"))
    tin_hieu = S.real_world_signals(cps, meta, out_dir=out)
    for khoa in ("irb_approved", "sap_locked", "db_locked", "peer_review_approved", "integrity_signed",
                 "release_locked"):
        assert tin_hieu[khoa] is True, (khoa, tin_hieu)
    assert S.real_world_signals(cps, dict(meta, _g10={"out_dir": str(out)}))["release_locked"] is True
    # Không có thư mục nào để chấm (vị trí chuẩn <repo>/exports/<mã> không có) ⇒ chưa khoá, không đoán.
    assert S.real_world_signals(cps, meta)["release_locked"] is False
    rows = SR._gate_state(study, out)
    for gate in ("G2", "G4", "G5", "G8", "G9", "G10"):
        assert _dong(rows, gate).startswith("🔒 ĐÃ KHOÁ"), (gate, rows)


def test_dai_kiem_soat_g2_da_duyet_dung_chung_thang_bo_cham_ho_so(tmp_path, monkeypatch):
    """«G2 đã duyệt» = g7_quality_gate.g2_da_duyet ở MỌI nơi: phê duyệt IRB thật (sổ cái + hợp đồng) không thành «chưa
    duyệt» chỉ vì bộ chấm hồ sơ G2 áp luật mới; không có phê duyệt thì vẫn là việc của IRB."""
    import g7_quality_gate as G7Q

    from tests._gia_lap_cham_song import gia_lap_cham_song

    d = tmp_path / "exports" / "S-G2DD"
    d.mkdir(parents=True)
    (d / "G2_checkpoint.json").write_text(json.dumps({
        "gate": "G2", "study": "S-G2DD", "quality_contract_version": "G2-2026.1", "guardrail": {"passed": True},
        "quality_gate": {"status": "DRAFT_NEEDS_HUMAN_COMPLETION", "pending_actions": []}}), encoding="utf-8",
        newline="\n")
    gia_lap_cham_song(monkeypatch)  # bộ chấm hồ sơ G2 (luật mới): DỰ THẢO
    monkeypatch.setattr(G7Q, "g2_da_duyet", lambda *_a, **_k: (True, "giả lập: sổ cái + hợp đồng"))
    g2 = next(r for r in ARG.audit_gates("S-G2DD", out_dir=d, write=False)["pipeline_gates"] if r["gate"] == "G2")
    assert g2["trang_thai_song"]["status"] == "PASS_G2_APPROVED" and g2["status"] != ARG.STATUS_NEEDS_REAL, g2
    monkeypatch.setattr(G7Q, "g2_da_duyet", lambda *_a, **_k: (False, "giả lập: chưa có chữ ký IRB"))
    g2 = next(r for r in ARG.audit_gates("S-G2DD", out_dir=d, write=False)["pipeline_gates"] if r["gate"] == "G2")
    assert g2["status"] == ARG.STATUS_NEEDS_REAL, g2


def test_dai_kiem_soat_khoi_guardrail_luu_khong_con_la_nguon_phan_khi_cham_song_duoc(tmp_path, monkeypatch):
    """Khối guardrail trong checkpoint là ảnh chụp lúc SINH artifact: khi bộ chấm của cổng chấm sống được, kết luận của
    nó thắng (bộ chấm nào cần guardrail thì tự đọc). Bản cũ: guardrail lưu False ⇒ GUARDRAIL_FAIL dù cổng đã đạt."""
    from tests._gia_lap_cham_song import gia_lap_cham_song

    d = tmp_path / "exports" / "S-GR"
    d.mkdir(parents=True)
    (d / "G1_checkpoint.json").write_text(json.dumps({"gate": "G1", "guardrail": {"passed": False}}),
                                          encoding="utf-8", newline="\n")
    gia_lap_cham_song(monkeypatch, G1="PASS_G1_CONFIRMED")
    g1 = next(r for r in ARG.audit_gates("S-GR", out_dir=d, write=False)["pipeline_gates"] if r["gate"] == "G1")
    assert g1["status"] != ARG.STATUS_GUARDRAIL_FAIL, g1


def test_dai_kiem_soat_khong_do_duoc_khong_giu_trang_thai_luu(tmp_path, monkeypatch):
    """Bộ chấm hỏng/không đo được ⇒ «KHÔNG ĐO ĐƯỢC» — không bao giờ giữ trạng thái LƯU (PASS) làm kết luận."""
    d = tmp_path / "exports" / "S-KDD"
    d.mkdir(parents=True)
    (d / "G0_checkpoint.json").write_text(json.dumps({"gate": "G0", "guardrail": {"passed": True},
                                                      "quality_gate": {"status": "PASS_G0_CONFIRMED"}}),
                                          encoding="utf-8", newline="\n")
    monkeypatch.setattr(CS, "trang_thai_song", lambda gate, *_a, **_k: CS._ket(
        str(gate).upper(), None, CS.NGUON_LOI, "giả lập: bộ chấm hỏng", "PASS_G0_CONFIRMED"))
    g0 = next(r for r in ARG.audit_gates("S-KDD", out_dir=d, write=False)["pipeline_gates"] if r["gate"] == "G0")
    assert g0["status"] == ARG.STATUS_NEEDS_REAL and g0["trang_thai_song"]["muc"] == CS.KHONG_DO_DUOC, g0
