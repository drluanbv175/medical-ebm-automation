"""tools/goc_ebm.py — dò gốc repo EBM ở bố cục lồng (Mac/Windows), anh em (Cloud) và EBM_REPO_ROOT. 26/09/2026."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TEP = Path(__file__).resolve().parents[1] / "tools" / "goc_ebm.py"
_sp = importlib.util.spec_from_file_location("goc_ebm_test", _TEP)
G = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(G)


def _goc_ebm(p: Path) -> Path:
    (p / "tools").mkdir(parents=True)
    (p / "tools" / "verify_clinical_evidence_update_pipeline.py").write_text("", encoding="utf-8", newline="\n")
    (p / ".claude" / "agents").mkdir(parents=True)
    return p


@pytest.fixture(autouse=True)
def _khong_env(monkeypatch):
    monkeypatch.delenv("EBM_REPO_ROOT", raising=False)


def test_bo_cuc_long_thang_ca_khi_co_thu_muc_anh_em_trung_ten(tmp_path):
    """Bố cục lồng được xét TRƯỚC: có thêm một bản EBM-drluanbv175 bên trong cũng không được lấy nhầm."""
    goc = _goc_ebm(tmp_path / "Claude AI")
    _goc_ebm(goc / "EBM-drluanbv175")
    assert G.tim_goc_ebm(goc / "medical-ebm-automation") == goc


def test_thieu_claude_agents_khong_phai_goc_ebm(tmp_path):
    gia = tmp_path / "EBM-drluanbv175"
    (gia / "tools").mkdir(parents=True)
    (gia / "tools" / "verify_clinical_evidence_update_pipeline.py").write_text("", encoding="utf-8", newline="\n")
    assert not G.la_goc_ebm(gia)


def test_bo_cuc_anh_em_cloud(tmp_path):
    goc = _goc_ebm(tmp_path / "EBM-drluanbv175")
    assert G.tim_goc_ebm(tmp_path / "medical-ebm-automation") == goc


def test_bien_moi_truong_thang(monkeypatch, tmp_path):
    _goc_ebm(tmp_path / "EBM-drluanbv175")
    rieng = _goc_ebm(tmp_path / "noi-khac")
    monkeypatch.setenv("EBM_REPO_ROOT", str(rieng))
    assert G.tim_goc_ebm(tmp_path / "medical-ebm-automation") == rieng.resolve()


def test_env_sai_bi_bo_qua_va_khong_doan_thu_muc_la(monkeypatch, tmp_path):
    monkeypatch.setenv("EBM_REPO_ROOT", str(tmp_path / "khong-ton-tai"))
    (tmp_path / "EBM-drluanbv175").mkdir()        # cùng tên nhưng KHÔNG có dấu vết repo EBM
    assert G.tim_goc_ebm(tmp_path / "medical-ebm-automation") == tmp_path   # giữ hành vi cũ REPO.parent


@pytest.mark.parametrize("ten", ["verify_clinical_evidence_agent_standards", "verify_clinical_production_control_plane",
                                 "verify_direct_clinical_practice_readiness", "verify_personal_production_hardening"])
def test_bon_verifier_dung_bo_do_chung(ten):
    dong = [x for x in (_TEP.parent / f"{ten}.py").read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.strip().startswith("#")]
    assert any(x.startswith("ROOT = _goc.tim_goc_ebm(REPO)") for x in dong)
    assert not any(x.strip() == "ROOT = REPO.parent" for x in dong)


def test_chi_thieu_tep_onedrive_tren_ban_sao_tran(tmp_path):
    goc = _goc_ebm(tmp_path / "EBM-drluanbv175")
    loi = ["missing:EBM_MASTER/tools/sync_all.py", "missing:dashboard_mockups/templates/a.html"]
    assert G.chi_thieu_tep_onedrive(loi, goc, "missing:") is True


@pytest.mark.parametrize("loi", [
    ["missing:EBM_MASTER/tools/sync_all.py", "upgrade_verify_missing_pipeline:x"],   # lỗi nội dung ⇒ vẫn FAIL
    ["missing:tools/upgrade_verify.py"],                                           # thiếu tệp TRONG git
    [],
])
def test_loi_khac_van_la_fail(tmp_path, loi):
    goc = _goc_ebm(tmp_path / "EBM-drluanbv175")
    assert G.chi_thieu_tep_onedrive(loi, goc, "missing:") is False


def test_may_that_co_onedrive_thi_thieu_la_fail(tmp_path):
    """Có EBM-Dashboards/ (máy thật) mà thiếu EBM_MASTER/… là cây OneDrive hỏng dở — phải ĐỎ."""
    goc = _goc_ebm(tmp_path / "EBM-drluanbv175")
    (goc / "EBM-Dashboards").mkdir()
    assert G.chi_thieu_tep_onedrive(["missing:EBM_MASTER/tools/sync_all.py"], goc, "missing:") is False


@pytest.mark.parametrize("ten,tien_to", [
    ("verify_clinical_production_control_plane", '"missing:"'),
    ("verify_clinical_evidence_agent_standards", '"missing_file:"'),
])
def test_hai_verifier_dung_bo_phan_loai_va_ma_2(ten, tien_to):
    nguon = (_TEP.parent / f"{ten}.py").read_text(encoding="utf-8")
    dong = [x for x in nguon.splitlines() if x.strip() and not x.strip().startswith("#")]
    assert any("_goc.chi_thieu_tep_onedrive(" in x and tien_to in x for x in dong)
    assert any('return 2 if report["overall_status"] == "MEASUREMENT_INCOMPLETE" else 0' in x for x in dong)
