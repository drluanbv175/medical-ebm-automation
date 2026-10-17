"""Quyết định đăng ký PI đã ghim thắng gợi ý mặc định của G2 — 17/10/2026 (hoàn thiện G2 của C1a).

C1a: bác sĩ chọn OSF Registries (13/09/2026, chép tay vào hồ sơ A3) nhưng chưa ghim thành `gate_params.G2` ⇒ bản
nháp đăng ký WHO TRDS sinh lại mỗi lượt vẫn ghi «ClinicalTrials.gov hoặc WHO ICTRP» — hai tài liệu cùng bộ hồ sơ nói
hai nơi đăng ký. Test chốt: ghim registry ⇒ cả checkpoint lẫn bản nháp đăng ký dùng đúng nơi đó, ghi nguồn; tiến cứu
⇒ BẮT BUỘC; `registration_required=false` không hạ được nghĩa vụ của nghiên cứu tiến cứu; chưa ghim ⇒ giữ gợi ý cũ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g2_quality_gate as G2Q  # noqa: E402
import run_g2_auto as G2  # noqa: E402

GOC = G2.get_risk_profile("cross_sectional", "Cắt ngang mô tả")


def _meta(**g2) -> dict:
    return {"gate_params": {"G2": g2}}


def test_chua_ghim_giu_goi_y_mac_dinh():
    assert G2.ap_quyet_dinh_dang_ky(GOC, _meta()) == GOC
    assert G2.ap_quyet_dinh_dang_ky(GOC, _meta(registration_registry="[CẦN BỔ SUNG]")) == GOC
    assert G2.ap_quyet_dinh_dang_ky(GOC, None) == GOC


def test_ghim_registry_va_tien_cuu():
    ra = G2.ap_quyet_dinh_dang_ky(GOC, _meta(registration_registry="OSF Registries",
                                             recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS"))
    assert ra["register_where"] == "OSF Registries (PI đã chốt — gate_params.G2.registration_registry)"
    assert ra["registration"].startswith("BẮT BUỘC — tiến cứu") and "recruitment_mode" in ra["registration"]
    assert "[CẦN" not in ra["registration"]
    assert GOC["register_where"].startswith("ClinicalTrials.gov"), "không sửa hồ sơ gốc dùng chung"


def test_false_khong_ha_nghia_vu_tien_cuu():
    ra = G2.ap_quyet_dinh_dang_ky(GOC, _meta(recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS",
                                             registration_required=False))
    assert ra["registration"].startswith("BẮT BUỘC")


def test_hoi_cuu_la_tuy_chon():
    ra = G2.ap_quyet_dinh_dang_ky(GOC, _meta(recruitment_mode="RETROSPECTIVE_SECONDARY_DATA"))
    assert ra["registration"].startswith("TÙY CHỌN") and ra["register_where"] == GOC["register_where"]


def test_ban_nhap_dang_ky_dung_noi_da_ghim(tmp_path):
    meta = _meta(registration_registry="OSF Registries", recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS")
    risk = G2.ap_quyet_dinh_dang_ky(GOC, meta)
    p = G2Q.build_registration_draft(study="S", topic="T", design_code="cross_sectional",
                                     design_primary="Cắt ngang mô tả", risk=risk, n_target=1000, out_dir=tmp_path,
                                     generated_at="2026-10-17T12:00:00", meta=meta)
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    assert d["suggested_registry"].startswith("OSF Registries (PI đã chốt")
    assert d["registration_requirement"].startswith("BẮT BUỘC")


def test_dau_cuoi_run_g2_auto_dung_registry_da_ghim():
    """Đường nối thật: `main()` phải áp quyết định đã ghim trước khi dựng checkpoint + bản nháp đăng ký."""
    import shutil  # noqa: PLC0415
    import subprocess  # noqa: PLC0415

    sys.path.insert(0, str(ROOT / "tests"))
    from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: PLC0415

    study = "PYTEST-G2-GHIM-DK"
    d = ROOT / "exports" / study
    shutil.rmtree(d, ignore_errors=True)
    try:
        d.mkdir(parents=True)
        dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional")
        mp = d / "study_meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
        meta.setdefault("gate_params", {}).setdefault("G2", {}).update(
            registration_registry="OSF Registries", recruitment_mode="PROSPECTIVE_NEW_PARTICIPANTS")
        mp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "run_g2_auto.py"), "--study", study, "--topic",
                            "Hài lòng người bệnh ngoại trú", "--design", "cross_sectional", "--skip-registry"],
                           cwd=ROOT, capture_output=True, text=True, timeout=180)
        assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]
        dk = json.loads((d / f"G2_REGISTRATION_DRAFT_{study}.json").read_text(encoding="utf-8"))
        cp = json.loads((d / "G2_checkpoint.json").read_text(encoding="utf-8"))
        assert dk["suggested_registry"].startswith("OSF Registries (PI đã chốt")
        assert cp["register_where"] == dk["suggested_registry"] and cp["registration_required"].startswith("BẮT BUỘC")
    finally:
        shutil.rmtree(d, ignore_errors=True)
