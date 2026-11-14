# -*- coding: utf-8 -*-
"""Hồi quy giả lập đề tài RCT 14/11/2026 — K6 (sinh lại G2/G4 sau khi đổi thiết kế), K8 (G3 ghim mặc định máy),
K9 (mẫu rủi ro G2 theo loại can thiệp).

K6 — rào chống đè G2/G4 đoán «bác sĩ đã biên tập» bằng ĐẾM nhãn [CẦN…]: hồ sơ máy sinh cho thiết kế CŨ (chưa ai sửa) có
     ít nhãn hơn hồ sơ RCT ⇒ bị giữ, pipeline dừng mã 2. Nay so DẤU SHA-256 của bản máy ghi lần trước
     (tools/dau_may_sinh.py): khớp ⇒ sinh lại; lệch ⇒ giữ + báo lý do/cờ; chưa có dấu ⇒ luật đếm cũ (C1a không đổi).
K8 — run_pipeline truyền lại qua dòng lệnh giá trị checkpoint cũ (gồm mặc định máy) ⇒ G3 coi là «CLI» và ghim vào vùng
     quyết định của PI; nhánh có effect size còn ghim kèm dropout/p_event mặc định. Nay chỉ ghim giá trị người cấp.
K9 — mẫu rủi ro của MỌI RCT là thử thuốc có lấy máu, chép vào phiếu đồng thuận của can thiệp tin nhắn. Nay chọn theo
     loại can thiệp (PI chốt > máy suy từ PICO I); chưa rõ ⇒ liệt kê để PI chọn, phiếu đồng thuận một ô [CẦN].

Mọi lượt chạy THẬT trong thư mục tạm (không ghi exports/ của repo). Dữ liệu tổng hợp, không PII, không mạng.
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import dau_may_sinh as DMS  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g2_auto as G2  # noqa: E402
import run_g3_auto as R3  # noqa: E402
import run_g4_auto as R4  # noqa: E402
import run_pipeline as RP  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot, dung_g0_g3_da_chot  # noqa: E402

PYTHON = sys.executable
SMS = "Tin nhắn SMS tự động nhắc uống thuốc hạ áp hằng ngày kèm chăm sóc thường quy trong 6 tháng"


# ═══════════════════════════════════════════════ K6 — dấu bản máy sinh ═══════════════════════════════════════════════
def test_k6_dau_khop_lech_va_khong_co(tmp_path):
    ho_so = tmp_path / "HS.md"
    ho_so.write_text("nội dung máy\n", encoding="utf-8", newline="\n")
    assert DMS.xet_ban_hien_co(ho_so, "nội dung máy\n", {"design_code": "rct"})["trang_thai"] == DMS.KHONG_CO_DAU
    DMS.ghi_dau(ho_so, "nội dung máy\n", {"design_code": "cross_sectional", "n": 0}, "test")
    khop = DMS.xet_ban_hien_co(ho_so, "nội dung máy\r\n", {"design_code": "rct", "n": 218})
    assert khop["trang_thai"] == DMS.MAY_SINH_NGUYEN, "đổi CRLF không phải «đã sửa tay»"
    assert khop["doi"] == {"design_code": ("cross_sectional", "rct"), "n": (None, 218)}
    assert DMS.xet_ban_hien_co(ho_so, "nội dung máy\nPI thêm\n", {})["trang_thai"] == DMS.DA_SUA_TAY
    DMS.duong_dan_dau(ho_so).write_text("{hỏng", encoding="utf-8", newline="\n")
    assert DMS.xet_ban_hien_co(ho_so, "nội dung máy\n", {})["trang_thai"] == DMS.KHONG_CO_DAU


def test_k6_quyet_dinh_ghi_de_theo_thu_tu(tmp_path):
    ho_so = tmp_path / "HS.md"
    DMS.ghi_dau(ho_so, "máy\n", {"design_code": "cross_sectional"}, "test")

    def qd(noi_dung, **kw):
        tham_so = dict(ep_sinh_lai=False, cu_day_du_hon_theo_luat_cu=True, da_ky=lambda: False)
        tham_so.update(kw)
        return DMS.quyet_dinh_ghi_de(ho_so, noi_dung, {"design_code": "rct"}, **tham_so)

    # Khớp dấu ⇒ đè dù luật đếm cũ nói «đầy đủ hơn» (đúng ca K6).
    assert qd("máy\n")["giu"] is False
    # Khớp dấu nhưng chính nội dung đó đã KÝ ⇒ không tự đè (luật mới không hạ cấp quyết định đã ký).
    da_ky = qd("máy\n", da_ky=lambda: True)
    assert da_ky["giu"] is True and "đã được ký" in da_ky["ly_do"]
    # Lệch dấu ⇒ giữ, KỂ CẢ khi luật đếm cũ nói bản đang có kém đầy đủ hơn.
    lech = qd("máy\nsửa\n", cu_day_du_hon_theo_luat_cu=False)
    assert lech["giu"] is True and "lệch dấu SHA-256" in lech["ly_do"]
    # Cờ --regenerate thắng mọi nhánh.
    assert qd("máy\nsửa\n", ep_sinh_lai=True)["giu"] is False
    # Không có dấu ⇒ đúng luật đếm cũ, hai chiều.
    DMS.duong_dan_dau(ho_so).unlink()
    assert qd("x", cu_day_du_hon_theo_luat_cu=True)["giu"] is True
    assert qd("x", cu_day_du_hon_theo_luat_cu=False)["giu"] is False
    cu = qd("x", thiet_ke_cu_checkpoint="cross_sectional")
    assert "cross_sectional → rct" in cu["mo_ta_doi"]


def test_k6_sau_dong_cuoi_noi_ly_do_va_co():
    dong = DMS.dong_cuoi_giu_ban_bien_tap("G2", "S", {"ly_do": "đã có người sửa tay",
                                                      "mo_ta_doi": "thiết kế: cross_sectional → rct"},
                                          "tools/run_g2_auto.py")
    assert len(dong) == 6, "run_pipeline lấy đúng 6 dòng cuối stdout"
    assert "đã có người sửa tay" in dong[0] and "--regenerate" in dong[0]
    assert "cross_sectional → rct" in dong[1]


def _g2(goc: Path, study: str, *them: str) -> subprocess.CompletedProcess:
    return subprocess.run([PYTHON, "-B", str(ROOT / "tools" / "run_g2_auto.py"), "--study", study, "--skip-registry",
                           "--repo-root", str(goc), *them], capture_output=True, text=True, timeout=240)


def test_k6_g2_doi_thiet_ke_ban_may_sinh_duoc_sinh_lai(tmp_path):
    study = "S-K6-G2"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional")
    r1 = _g2(tmp_path, study)
    assert r1.returncode == 0, r1.stdout[-1500:] + r1.stderr[-800:]
    ho_so = d / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    ban_cat_ngang = ho_so.read_text(encoding="utf-8")
    assert DMS.duong_dan_dau(ho_so).exists(), "lượt máy ghi hồ sơ phải ghi dấu"
    # PI sửa thiết kế sang RCT (G0/G1 chốt lại) — hồ sơ G2 cắt ngang CHƯA AI ĐỤNG.
    dung_g0_g1_da_chot(d, study, thiet_ke="rct", them_meta={"G1": {"intervention_or_exposure": SMS}})
    r2 = _g2(tmp_path, study)
    assert r2.returncode == 0, "bản máy sinh nguyên phải được sinh lại\n" + r2.stdout[-1500:]
    ban_rct = ho_so.read_text(encoding="utf-8")
    # Đồ gá thật sự kích hoạt luật đếm cũ (bản RCT nhiều nhãn hơn) — không có dấu thì máy đã từ chối.
    assert ban_cat_ngang.count("[CẦN") < ban_rct.count("[CẦN")
    assert ban_rct != ban_cat_ngang and "CONSORT" in ban_rct
    assert "MÁY SINH NGUYÊN" in r2.stdout and "cross_sectional → rct" in r2.stdout
    cp = json.loads((d / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["design_code"] == "rct" and cp["sinh_lai"]["giu_ban_bien_tap"] is False
    # K9 trên chính lượt này: can thiệp tin nhắn ⇒ máy suy «hành vi», phiếu đồng thuận không có rủi ro lấy máu.
    assert cp["loai_can_thiep"]["loai"] == ["behavioral"] and cp["loai_can_thiep"]["da_chot"] is False
    icf = ban_rct.split("TÀI LIỆU 4")[1].split("TÀI LIỆU 5")[0]
    assert "Lấy máu" not in icf and "thuốc/sản phẩm thử nghiệm" not in icf


def test_k6_g2_ban_da_sua_doi_thiet_ke_giu_va_bao_ro(tmp_path):
    study = "S-K6-G2-SUA"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional")
    assert _g2(tmp_path, study).returncode == 0
    ho_so = d / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    ban_sua = ho_so.read_text(encoding="utf-8") + "\nPI đã viết lại mục ICF 2 cho đúng quy trình khoa.\n"
    ho_so.write_text(ban_sua, encoding="utf-8", newline="\n")
    dung_g0_g1_da_chot(d, study, thiet_ke="rct")
    r = _g2(tmp_path, study)
    assert r.returncode == GC.EXIT_BLOCKED, r.stdout[-1500:]
    assert ho_so.read_text(encoding="utf-8") == ban_sua, "bản người sửa phải nguyên từng byte"
    duoi = [x for x in r.stdout.splitlines()][-6:]
    assert "lệch dấu SHA-256" in duoi[0] and "--regenerate" in duoi[0], duoi
    assert any("cross_sectional → rct" in x for x in duoi), duoi
    cp = json.loads((d / "G2_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["sinh_lai"]["giu_ban_bien_tap"] is True and cp["sinh_lai"]["trang_thai_dau"] == DMS.DA_SUA_TAY
    # Bí danh chung --regenerate (G2 cũ chỉ có --regenerate-artifact) sinh lại có chủ đích, bản cũ vẫn .bak-*.
    r2 = _g2(tmp_path, study, "--regenerate")
    assert r2.returncode == 0, r2.stdout[-1200:] + r2.stderr[-600:]
    assert ho_so.read_text(encoding="utf-8") != ban_sua
    assert list(d.glob(f"{ho_so.name}.bak-*"))


@pytest.mark.parametrize("cong,co", [("run_g2_auto.py", ("--regenerate-artifact", "--regenerate")),
                                     ("run_g4_auto.py", ("--regenerate-sap", "--regenerate", "--regenerate-artifact"))])
def test_k6_bi_danh_co_khai_tuong_minh(cong, co):
    """Bí danh chung phải được KHAI (không dựa vào argparse tự nhận tiền tố — thêm một cờ «--regenerate-x» là vỡ)."""
    r = subprocess.run([PYTHON, "-B", str(ROOT / "tools" / cong), "--help"], capture_output=True, text=True,
                       timeout=60)
    assert r.returncode == 0, r.stderr[-400:]
    dong = next(x for x in r.stdout.splitlines() if x.strip().startswith(co[0]))  # dòng mục tuỳ chọn, không phải usage
    assert all(f"{c}," in dong or dong.rstrip().endswith(c) for c in co), dong


def _g4(goc: Path, study: str, monkeypatch, *them: str):
    monkeypatch.setattr(R4, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g4_auto.py", "--study", study, *them])
    CS.xoa_dem()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = R4.main()
        except SystemExit as exc:
            rc = exc.code
    CS.xoa_dem()
    return rc, buf.getvalue()


def test_k6_g4_doi_thiet_ke_sap_may_sinh_duoc_sinh_lai(tmp_path, monkeypatch):
    study = "S-K6-G4"
    d = tmp_path / "exports" / study
    dung_g0_g3_da_chot(d, study, thiet_ke="cross_sectional")
    rc1, out1 = _g4(tmp_path, study, monkeypatch)
    assert rc1 in (None, 0), out1[-1500:]
    sap = d / f"G4_A5_SAP_FINAL_{study}.md"
    sap_cat_ngang = sap.read_text(encoding="utf-8")
    dung_g0_g3_da_chot(d, study, thiet_ke="rct")
    rc2, out2 = _g4(tmp_path, study, monkeypatch)
    assert rc2 in (None, 0), "SAP máy sinh nguyên phải được sinh lại\n" + out2[-1500:]
    sap_rct = sap.read_text(encoding="utf-8")
    assert sap_cat_ngang.count("[CẦN") < sap_rct.count("[CẦN"), "đồ gá phải kích hoạt luật đếm cũ"
    assert "§13" in sap_rct and "§13" not in sap_cat_ngang
    assert "MÁY SINH NGUYÊN" in out2 and "cross_sectional → rct" in out2
    # SAP đã sửa tay + bí danh cờ: --regenerate-artifact (tên G2) cũng nhận ở G4.
    sap.write_text(sap_rct + "\nThống kê viên sửa §9.\n", encoding="utf-8", newline="\n")
    rc3, out3 = _g4(tmp_path, study, monkeypatch)
    assert rc3 == GC.EXIT_BLOCKED and "lệch dấu SHA-256" in out3.splitlines()[-6]
    rc4, out4 = _g4(tmp_path, study, monkeypatch, "--regenerate-artifact")
    assert rc4 in (None, 0), out4[-1200:]
    assert "Thống kê viên sửa §9." not in sap.read_text(encoding="utf-8")


# ═══════════════════════════════════════ K8 — G3 không ghim mặc định máy ═══════════════════════════════════════════
def _g3(goc: Path, study: str, monkeypatch, argv: list):
    monkeypatch.setattr(R3, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    CS.xoa_dem()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = R3.main()
    d = goc / "exports" / study
    return (json.loads((d / "G3_checkpoint.json").read_text(encoding="utf-8")), rc, buf.getvalue(),
            json.loads((d / "study_meta.json").read_text(encoding="utf-8"))["gate_params"].get("G3") or {})


_MAC_DINH_MAY = ("precision", "p_event", "dropout", "alpha", "power", "p0", "hypothesis_type", "effect_size",
                 "effect_type", "prevalence")


def test_k8_mac_dinh_truyen_lai_qua_pipeline_khong_ghim(tmp_path, monkeypatch):
    """Lượt «thiết kế sai» (cắt ngang, mọi tham số mặc định) → pipeline chạy lại G3 bằng dòng lệnh dựng từ checkpoint
    cũ: bản cũ ghim precision=0,05, p_event=0,3… vào gate_params.G3 như quyết định của PI."""
    study = "S-K8-PIPE"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[])
    cp1, _, _, g3_1 = _g3(tmp_path, study, monkeypatch, [])
    assert cp1["nguon_tham_so"]["precision"] == "mặc định 0.05"
    assert all(g3_1.get(k) is None for k in _MAC_DINH_MAY), g3_1
    argv = RP._recover_params("G3", d, json.loads((d / "study_meta.json").read_text(encoding="utf-8")))
    assert "--precision" in argv and "--p-event" in argv, "đồ gá phải tái hiện đúng lệnh pipeline truyền lại"
    cp2, _, out2, g3_2 = _g3(tmp_path, study, monkeypatch, argv)
    assert all(g3_2.get(k) is None for k in _MAC_DINH_MAY), f"mặc định máy bị ghim: {g3_2}"
    assert "TRÙNG giá trị MÁY của lượt trước" in out2
    assert cp2["nguon_tham_so"].get("effect_size") != "CLI", "giá trị truyền lại không được mang nhãn «CLI»"
    assert cp2["n_adjusted"] == cp1["n_adjusted"], "lọc truyền-lại không được đổi phép tính"
    assert {"p_event", "precision", "dropout"} <= set(cp2["tham_so_mac_dinh_may"]), cp2["tham_so_mac_dinh_may"]


def test_k8_effect_size_tu_study_meta_khong_ghim_kem_p_event(tmp_path, monkeypatch):
    """«Xoá đi thì run_g3_auto lại tự ghi p_event»: effect size đã ghim, dropout/p_event chưa — chạy lại chỉ --study."""
    study = "S-K8-HQ"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="rct", mau_hieu_qua=[],
                       them_meta={"G3": {"effect_size": 0.7, "effect_type": "RR", "p0": 0.3}})
    cp, _, _, g3 = _g3(tmp_path, study, monkeypatch, [])
    assert cp["effect_val"] == 0.7 and cp["n_adjusted"] > 0
    assert g3.get("p_event") is None and g3.get("dropout") is None, g3


def test_k8_nguoi_truyen_qua_dong_lenh_van_ghim(tmp_path, monkeypatch):
    """Lượt đầu (chưa có checkpoint) người gõ --p-event 0.3 — trùng mặc định nhưng là quyết định của người ⇒ ghim."""
    study = "S-K8-NGUOI"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="rct", mau_hieu_qua=[])
    _, _, _, g3 = _g3(tmp_path, study, monkeypatch,
                      ["--effect-size", "0.7", "--effect-type", "RR", "--p0", "0.3", "--p-event", "0.3"])
    assert (g3.get("effect_size"), g3.get("effect_type"), g3.get("p_event"), g3.get("p0")) == (0.7, "RR", 0.3, 0.3)
    assert g3.get("dropout") is None, "dropout không truyền ⇒ không ghim"


def test_k8_doi_thiet_ke_gia_thuyet_cu_khong_bam_theo(tmp_path, monkeypatch):
    """Sau khi đổi cắt ngang → RCT, pipeline truyền lại giả thuyết «descriptive_precision» và p=0,5 của lượt cũ: giá trị
    máy không được thắng phép suy mới từ thiết kế hiện hành, và không bị ghim."""
    study = "S-K8-TK"
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[])
    _g3(tmp_path, study, monkeypatch, [])
    dung_g0_g1_da_chot(d, study, thiet_ke="rct", mau_hieu_qua=[])
    argv = RP._recover_params("G3", d, json.loads((d / "study_meta.json").read_text(encoding="utf-8")))
    assert "--hypothesis-type" in argv
    cp, _, _, g3 = _g3(tmp_path, study, monkeypatch, argv)
    assert cp["hypothesis_type"] == "superiority", cp["nguon_tham_so"]
    assert cp["effect_type"] != "PREVALENCE"
    assert all(g3.get(k) is None for k in _MAC_DINH_MAY), g3


# ═══════════════════════════════════════ K9 — rủi ro G2 theo loại can thiệp ════════════════════════════════════════
def _meta(**g):
    return {"gate_params": {k: v for k, v in g.items()}}


@pytest.mark.parametrize("meta,topic,ky_vong", [
    (_meta(G0={"intervention": SMS}), "", ["behavioral"]),
    (None, "Hiệu quả của tin nhắn nhắc uống thuốc so với chăm sóc thường", ["behavioral"]),
    (None, "Dapagliflozin 10 mg so với giả dược ở suy tim", ["drug"]),
    (None, "Phẫu thuật nội soi so với mổ mở", ["procedure"]),
    (None, "Thiết bị đo huyết áp đeo tay", ["device"]),
    (None, "Máy đo huyết áp tại nhà kèm tin nhắn nhắc", []),
    (None, "Hiệu quả của X so với Y", []),
    (_meta(G0={"intervention": SMS}, G2={"intervention_type": "drug"}), "", ["drug"]),
    (_meta(G2={"intervention_type": ["thuốc", "hành vi"]}), "", ["behavioral", "drug"]),
])
def test_k9_phan_loai_can_thiep(meta, topic, ky_vong):
    assert G2.phan_loai_can_thiep(meta, topic)["loai"] == ky_vong


def test_k9_ghim_sai_gia_tri_canh_bao_roi_suy():
    pl = G2.phan_loai_can_thiep(_meta(G0={"intervention": SMS}, G2={"intervention_type": "khác"}), "")
    assert pl["loai"] == ["behavioral"] and pl["da_chot"] is False and "không nhận ra" in pl["canh_bao"]


def _goi(risk, meta=None):
    md = G2.generate_g2_full_package(
        topic="Đề tài tổng hợp", study_name="S", design_code="rct", design_primary="RCT", reporting_std="CONSORT 2025",
        n_sr=0, n_rct=0, evidence_level="", registry=None, risk=risk, run_date="2026-11-14T10:00", meta=meta)
    return md.split("TÀI LIỆU 3")[1].split("TÀI LIỆU 4")[0], md.split("TÀI LIỆU 4")[1].split("TÀI LIỆU 5")[0]


def test_k9_can_thiep_tin_nhan_icf_khong_co_rui_ro_thuoc_lay_mau():
    meta = _meta(G0={"intervention": SMS})
    risk = G2.ap_loai_can_thiep(G2.get_risk_profile("rct", "RCT"), "rct", meta, "")
    tl3, icf = _goi(risk, meta)
    assert "Lấy máu" not in icf and "thuốc/sản phẩm thử nghiệm" not in icf
    assert "tin nhắn" in icf.lower()
    assert "[CẦN PI XÁC NHẬN loại can thiệp" in tl3, "máy suy ⇒ phải đòi PI xác nhận"
    # Máy suy KHÔNG được hạ mức nguy cơ/lộ trình trình Hội đồng.
    assert risk["risk_level"] == G2.RISK_PROFILES["rct"]["risk_level"]
    assert risk["irb_route"] == G2.RISK_PROFILES["rct"]["irb_route"]


def test_k9_chua_ro_loai_bang_liet_ke_icf_mot_o_can():
    risk = G2.ap_loai_can_thiep(G2.get_risk_profile("rct", "RCT"), "rct", None, "Hiệu quả của X so với Y")
    tl3, icf = _goi(risk)
    so_dong_rieng = sum(len(v) for v in G2._RUI_RO_RCT_THEO_LOAI.values())
    assert tl3.count("[CẦN PI CHỌN") == so_dong_rieng
    assert "Lấy máu" not in icf and "[CẦN PI XÁC NHẬN loại can thiệp]" in icf
    # Hồ sơ RCT mặc định (không qua ap_loai_can_thiep, vd fallback thiết kế lạ) cũng không chép rủi ro lấy máu vào ICF.
    _, icf_mac_dinh = _goi(G2.RISK_PROFILES["rct"])
    assert "Lấy máu" not in icf_mac_dinh


def test_k9_pi_chot_loai_can_thiep():
    hanh_vi = G2.ap_loai_can_thiep(G2.get_risk_profile("rct", "RCT"), "rct",
                                   _meta(G2={"intervention_type": "behavioral"}), "")
    assert hanh_vi["risk_level"].startswith("TỐI THIỂU") and "Hội đồng" in hanh_vi["irb_route"]
    thuoc = G2.ap_loai_can_thiep(G2.get_risk_profile("rct", "RCT"), "rct", _meta(G2={"intervention_type": "drug"}), "")
    _, icf = _goi(thuoc)
    assert thuoc["risk_level"] == "LỚN HƠN TỐI THIỂU" and "Lấy máu" in icf and "CHỈ khi đề cương có" in icf


@pytest.mark.parametrize("thiet_ke", ["cross_sectional", "cohort", "case_control", "diagnostic", "sr_ma",
                                      "prediction", "qualitative"])
def test_k9_khong_doi_thiet_ke_khong_phai_rct(thiet_ke):
    """C1a (cắt ngang) và mọi thiết kế không phải RCT: hồ sơ nguy cơ giữ nguyên từng khoá."""
    goc = G2.get_risk_profile(thiet_ke, "Thiết kế")
    assert G2.ap_loai_can_thiep(goc, thiet_ke, _meta(G0={"intervention": SMS}), "") is goc
