"""Hồi quy 24/09/2026 — cổng triển khai giám sát chứng cứ không được FAIL GIẢ vì bố cục thư mục.

Đo thật 24/09 trên Cloud: engine là ANH EM của repo EBM (/home/user/medical-ebm-automation cạnh
/home/user/EBM-drluanbv175) hoặc repo EBM vắng hẳn ⇒ ESD02/04/07/08 FAIL giả vì ROOT bị ghép cứng
là thư mục cha của engine. Bản vá: dò gốc EBM ở cả bố cục lồng lẫn anh em; thiếu thứ cần đo ⇒
NOT_MEASURED (không FAIL, không PASS, không bao giờ READY). Canary scanner dùng --max 20 và
chạy bản vendor trong hộp cát tạm để không ghi gì vào cây repo EBM.

Toàn bộ NGOẠI TUYẾN: repo EBM giả dựng trong tmp_path, scanner giả là script Python nhỏ.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import verify_evidence_surveillance_deployment as V

VENDOR_A = Path("sync/skills/cap-nhat-chung-cu-y-khoa/tools/surveillance_scan.py")
VENDOR_B = Path("sync/skills/dark-analyst/tools/surveillance_scan.py")

# Scanner giả bắt chước ĐÚNG các đường ghi của bản vendor thật: khoá cạnh skill, alert ở
# <skills>/alerts/, và dò `medical-ebm-automation/app/sources` theo cây thư mục.
SCANNER_GIA = r'''
import argparse, json, sys
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--watchlist"); p.add_argument("--days"); p.add_argument("--max")
p.add_argument("--report"); p.add_argument("--json-report"); p.add_argument("--khong-cursor", action="store_true")
a = p.parse_args()
skill = Path(__file__).resolve().parents[1]
(skill / ".quet.lock").write_text("{}", encoding="utf-8")
alerts = skill.parent / "alerts"
alerts.mkdir(exist_ok=True)
(alerts / "canary.md").write_text("x", encoding="utf-8")
q = Path(__file__).resolve().parent
engine = None
for _ in range(7):
    if (q / "medical-ebm-automation" / "app" / "sources").is_dir():
        engine = q / "medical-ebm-automation"; break
    q = q.parent
Path(a.report).write_text("# r", encoding="utf-8")
Path(a.json_report).write_text(json.dumps({
    "status": "PASS" if (engine and a.max == "20") else "PARTIAL",
    "topic_count": 2, "failed_topics": 0, "candidate_count": 7, "topics": [],
    "engine_found": bool(engine),
}), encoding="utf-8")
'''


def _dung_ebm(goc: Path, *, dashboards: bool = False, onedrive: bool = False,
              noi_dung_b: str | None = None) -> Path:
    for rel in (VENDOR_A, VENDOR_B):
        f = goc / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(SCANNER_GIA, encoding="utf-8", newline="\n")
    if noi_dung_b is not None:
        (goc / VENDOR_B).write_text(noi_dung_b, encoding="utf-8", newline="\n")
    (goc / "tools").mkdir(exist_ok=True)
    verifier = goc / "tools" / "verify_clinical_evidence_update_pipeline.py"
    verifier.write_text("print('ok')\n", encoding="utf-8", newline="\n")
    if dashboards:
        d = goc / "EBM-Dashboards" / "tools"
        d.mkdir(parents=True)
        (d / "surveillance_scan.py").write_text(SCANNER_GIA, encoding="utf-8", newline="\n")
    if onedrive:
        for ten in V.TAI_SAN_CHI_ONEDRIVE:
            (goc / ten).mkdir()
    return goc


def _anh_chup(goc: Path) -> dict[str, str]:
    return {
        str(p.relative_to(goc)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(goc.rglob("*")) if p.is_file()
    }


@pytest.fixture(autouse=True)
def _khong_env(monkeypatch):
    monkeypatch.delenv("EBM_REPO_ROOT", raising=False)


# ── Phân giải gốc EBM ─────────────────────────────────────────────────────────

def test_bo_cuc_long(tmp_path, monkeypatch):
    goc = _dung_ebm(tmp_path / "Claude AI")
    monkeypatch.setattr(V, "ROOT", goc)
    assert V._tim_goc_ebm() == (goc, "long")


def test_bo_cuc_anh_em_cloud(tmp_path, monkeypatch):
    home = tmp_path / "home_user"
    goc = _dung_ebm(home / "EBM-drluanbv175")
    monkeypatch.setattr(V, "ROOT", home)
    assert V._tim_goc_ebm() == (goc, "anh_em")


def test_bien_moi_truong_ghi_de(tmp_path, monkeypatch):
    goc = _dung_ebm(tmp_path / "clone_khac")
    monkeypatch.setattr(V, "ROOT", tmp_path / "trong")
    monkeypatch.setenv("EBM_REPO_ROOT", str(goc))
    assert V._tim_goc_ebm() == (goc.resolve(), "env")


def test_vang_repo_ebm(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "ROOT", tmp_path)
    assert V._tim_goc_ebm() == (None, "vang")


# ── Vắng repo EBM ⇒ NOT_MEASURED, không FAIL giả ─────────────────────────────

def test_vang_ebm_bon_cong_la_chua_do(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "ROOT", tmp_path)
    for check in (V._check_tool_mirrors(), V._check_offline_pipeline(),
                  V._check_online_scanner(), V._check_online_dashboard()):
        assert check.status == V.NOT_MEASURED, check
        assert "CHƯA ĐO ĐƯỢC" in check.evidence


def _stub(check_id: str, status: str) -> V.Check:
    return V.Check(check_id, "stub", "static", status, "stub", "stub")


@pytest.mark.parametrize("mode", ["runtime_canary", "contract_check", "full"])
def test_chua_do_khong_bao_gio_ready(mode, tmp_path, monkeypatch):
    monkeypatch.setattr(V, "ROOT", tmp_path)  # vắng repo EBM
    monkeypatch.setattr(V, "_check_scheduler_loaded", lambda: _stub("ESD05", V.PASS))
    monkeypatch.setattr(V, "_check_online_sources", lambda: _stub("ESD06", V.PASS))
    monkeypatch.setattr(V, "_check_runtime_history", lambda c: _stub("ESD09", V.PASS))
    monkeypatch.setattr(V, "_check_notification_config", lambda: _stub("ESD10", V.PASS))
    monkeypatch.setattr(V, "_check_uat", lambda c, p: _stub("ESD11", V.PASS))
    report = V.run_verification(
        online=True, runtime_canary=mode == "runtime_canary",
        contract_check=mode == "contract_check", uat_path=tmp_path / "uat.json",
    )
    assert report["deployment_status"] == "MEASUREMENT_INCOMPLETE"
    assert report["deployment_allowed"] is False
    assert report["failure_count"] == 0
    assert report["not_measured_count"] >= 2


def test_main_runtime_canary_thoat_khac_0_khi_chua_do(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(V, "ROOT", tmp_path)
    monkeypatch.setattr(V, "_check_scheduler_loaded", lambda: _stub("ESD05", V.PASS))
    monkeypatch.setattr(V, "_check_online_sources", lambda: _stub("ESD06", V.PASS))
    assert V.main(["--runtime-canary", "--no-write"]) == 1
    assert '"MEASUREMENT_INCOMPLETE"' in capsys.readouterr().out


def test_fail_that_van_uu_tien_hon_chua_do(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "ROOT", tmp_path)
    monkeypatch.setattr(V, "_check_scheduler_loaded", lambda: _stub("ESD05", V.FAIL))
    report = V.run_verification(online=False, runtime_canary=False, contract_check=True,
                                uat_path=tmp_path / "uat.json")
    assert report["deployment_status"] == "BLOCKED_FOR_DEPLOYMENT"


# ── ESD02 ─────────────────────────────────────────────────────────────────────

def test_esd02_hai_vendor_khop_nhung_thieu_dashboards_la_chua_do(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _dung_ebm(home / "EBM-drluanbv175")
    monkeypatch.setattr(V, "ROOT", home)
    check = V._check_tool_mirrors()
    assert check.status == V.NOT_MEASURED
    assert "2/3" in check.evidence


def test_esd02_vendor_lech_van_fail_that(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _dung_ebm(home / "EBM-drluanbv175", noi_dung_b="# khac\n")
    monkeypatch.setattr(V, "ROOT", home)
    assert V._check_tool_mirrors().status == V.FAIL


def test_esd02_du_ba_ban_khop_la_pass(tmp_path, monkeypatch):
    goc = _dung_ebm(tmp_path / "ws", dashboards=True)
    monkeypatch.setattr(V, "ROOT", goc)
    check = V._check_tool_mirrors()
    assert check.status == V.PASS
    assert "files=3/3" in check.evidence


# ── ESD04/ESD08 ───────────────────────────────────────────────────────────────

def test_esd04_thieu_tai_san_onedrive_la_chua_do(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _dung_ebm(home / "EBM-drluanbv175")
    monkeypatch.setattr(V, "ROOT", home)
    monkeypatch.setattr(V, "_run", lambda *a, **k: pytest.fail("không được chạy verifier khi thiếu tài sản"))
    for check in (V._check_offline_pipeline(), V._check_online_dashboard()):
        assert check.status == V.NOT_MEASURED
        assert "EBM_MASTER" in check.evidence


def test_esd04_chay_verifier_tai_goc_ebm_anh_em(tmp_path, monkeypatch):
    home = tmp_path / "home"
    goc = _dung_ebm(home / "EBM-drluanbv175", onedrive=True)
    monkeypatch.setattr(V, "ROOT", home)
    goi: dict = {}

    def fake_run(cmd, *, cwd):
        goi["cmd"], goi["cwd"] = list(cmd), cwd
        return True, "ok"

    monkeypatch.setattr(V, "_run", fake_run)
    assert V._check_offline_pipeline().status == V.PASS
    assert goi["cwd"] == goc
    assert goi["cmd"][1] == str(goc / "tools" / "verify_clinical_evidence_update_pipeline.py")


# ── ESD07 ─────────────────────────────────────────────────────────────────────

def _tao_duoc_symlink(tmp_path: Path) -> bool:
    """Windows không bật Developer Mode/quyền admin thì không tạo được symlink thư mục."""
    try:
        (tmp_path / "_thu_symlink").symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError):
        return False
    return True


def test_esd07_vendor_chay_trong_hop_cat_khong_ghi_vao_repo_ebm(tmp_path, monkeypatch):
    home = tmp_path / "home"
    goc = _dung_ebm(home / "EBM-drluanbv175")
    truoc = _anh_chup(goc)
    monkeypatch.setattr(V, "ROOT", home)
    co_symlink = _tao_duoc_symlink(tmp_path)
    check = V._check_online_scanner()  # chạy subprocess THẬT với scanner giả
    if not co_symlink:
        # Máy không cho tạo symlink (vd Windows runner): phải «chưa đo được», KHÔNG chạy vendor tại chỗ.
        assert check.status == V.NOT_MEASURED, check.evidence
        assert "symlink" in check.evidence
        assert _anh_chup(goc) == truoc
        return
    assert check.status == V.PASS, check.evidence
    assert "vendor_hop_cat" in check.evidence
    assert f"max={V.CANARY_SCANNER_MAX}" in check.evidence
    assert _anh_chup(goc) == truoc  # không khoá, không alert nào rơi vào cây repo EBM
    assert not (goc / "sync" / "skills" / "alerts").exists()


def test_esd07_canary_dung_max_20(tmp_path, monkeypatch):
    goc = _dung_ebm(tmp_path / "ws", dashboards=True)
    monkeypatch.setattr(V, "ROOT", goc)
    goi: dict = {}

    def fake_run(cmd, *, cwd):
        goi["cmd"] = list(cmd)
        out = Path(cmd[cmd.index("--json-report") + 1])
        Path(cmd[cmd.index("--report") + 1]).write_text("r", encoding="utf-8", newline="\n")
        out.write_text(json.dumps({"status": "PASS", "topic_count": 2}), encoding="utf-8", newline="\n")
        return True, ""

    monkeypatch.setattr(V, "_run", fake_run)
    check = V._check_online_scanner()
    assert check.status == V.PASS
    assert goi["cmd"][goi["cmd"].index("--max") + 1] == "20"
    assert "--khong-cursor" in goi["cmd"]
    assert "scanner=EBM-Dashboards" in check.evidence


def test_esd07_khong_tao_duoc_symlink_la_chua_do(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _dung_ebm(home / "EBM-drluanbv175")
    monkeypatch.setattr(V, "ROOT", home)

    def no_symlink(self, *a, **k):
        raise OSError("symlink bị cấm")

    monkeypatch.setattr(Path, "symlink_to", no_symlink)
    check = V._check_online_scanner()
    assert check.status == V.NOT_MEASURED
    assert "symlink" in check.evidence
