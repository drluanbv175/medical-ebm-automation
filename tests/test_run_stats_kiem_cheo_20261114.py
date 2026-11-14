"""E4 — `run_stats_analysis.py --kiem-cheo`: sau khi ghi G6_analysis_summary.json thì chạy kiểm chéo SPSS + R
(`tools/kiem_cheo_g6.py chay`) ở chế độ TƯ VẤN — không đổi mã thoát, không đổi trạng thái cổng, lỗi chỉ in ra.

`kiem_cheo_g6.py` được thay bằng một script giả (ghi lại tham số, thoát với mã chọn trước) — không cần SPSS/R. Dữ liệu
giả, không PII.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import run_stats_analysis as RSA  # noqa: E402


def _script_gia(tmp_path: Path, ma: int, *, in_ra: str = "") -> tuple[Path, Path]:
    ghi = tmp_path / "goi_kiem_cheo.json"
    p = tmp_path / "kiem_cheo_gia.py"
    p.write_text(
        "import json, sys\n"
        f"open({str(ghi)!r}, 'w', encoding='utf-8').write(json.dumps(sys.argv[1:]))\n"
        f"print({in_ra!r})\n"
        f"sys.exit({ma})\n",
        encoding="utf-8",
        newline="\n",
    )
    return p, ghi


@pytest.mark.parametrize("ma, nhan", [(0, "khớp"), (1, "LỆCH"), (2, "không đo được"), (3, "từ chối")])
def test_tu_van_tra_ma_kiem_cheo_va_in_nhan(tmp_path, monkeypatch, capfd, ma, nhan):
    p, ghi = _script_gia(tmp_path, ma, in_ra="KIEM_CHEO_GIA_CHAY")
    monkeypatch.setattr(RSA, "TEP_KIEM_CHEO", p)
    assert RSA.chay_kiem_cheo_tu_van("THU", "G6") == ma
    assert json.loads(ghi.read_text(encoding="utf-8")) == ["chay", "--study", "THU", "--gate", "G6"]
    ra = capfd.readouterr().out
    assert "KIEM_CHEO_GIA_CHAY" in ra  # đầu ra của kiểm chéo chảy thẳng ra màn hình
    assert f"mã {ma} — " in ra and nhan in ra and "TƯ VẤN" in ra


def test_tu_van_loi_chi_in_khong_nem(tmp_path, monkeypatch, capsys):
    def hong(*a, **k):
        raise OSError("không chạy được trình thông dịch")

    monkeypatch.setattr(RSA.subprocess, "run", hong)
    assert RSA.chay_kiem_cheo_tu_van("THU", "G6") is None
    assert "Không chạy được kiểm chéo" in capsys.readouterr().out

    def qua_han(*a, **k):
        raise subprocess.TimeoutExpired(cmd="kiem_cheo", timeout=1)

    monkeypatch.setattr(RSA.subprocess, "run", qua_han)
    assert RSA.chay_kiem_cheo_tu_van("THU", "G6") is None
    assert "quá" in capsys.readouterr().out


def _chay_main(tmp_path: Path, monkeypatch, *them: str) -> tuple[dict, Path]:
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    pytest.importorskip("statsmodels")
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "BASE", tmp_path)
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cohort", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    study = "KC-THU"
    d = tmp_path / "exports" / study
    (d / "05_clean_locked").mkdir(parents=True)
    rng = np.random.default_rng(20261114)
    n = 120
    nhom = rng.integers(0, 2, n)
    tuoi = np.round(rng.normal(55, 10, n), 1)
    kq = (rng.random(n) < 1 / (1 + np.exp(-(-0.5 + 0.7 * nhom)))).astype(int)
    p = d / "05_clean_locked" / "k.csv"
    pd.DataFrame({"nhom": nhom, "tuoi": tuoi, "kq": kq}).to_csv(p, index=False)
    man = {"locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
           "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}  # fmt: skip
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda study, _d: man)
    argv = ["run_stats_analysis.py", "--data", str(p), "--study", study, "--gate", "G6", "--outcome", "kq",
            "--group", "nhom", "--covariates", "tuoi", "--outcome-type", "binary", "--n-imputations", "2",
            *them]  # fmt: skip
    monkeypatch.setattr(sys, "argv", argv)
    with contextlib.redirect_stdout(io.StringIO()):
        tom = RSA.main()  # KHÔNG ném SystemExit: mã thoát của phân tích là 0 dù kiểm chéo LỆCH
    return tom, d


def test_main_kiem_cheo_chay_sau_khi_ghi_tom_tat_va_khong_doi_ket_qua(tmp_path, monkeypatch):
    p, ghi = _script_gia(tmp_path, 1)  # kiểm chéo LỆCH ⇒ phân tích vẫn xong bình thường
    seen: dict = {}
    goc = RSA.chay_kiem_cheo_tu_van

    def boc(study, gate):
        tom_p = tmp_path / "exports" / study / f"{gate}_analysis_summary.json"
        seen["co_tom_tat"] = tom_p.is_file()
        seen["sha_truoc"] = hashlib.sha256(tom_p.read_bytes()).hexdigest()
        return goc(study, gate)

    monkeypatch.setattr(RSA, "TEP_KIEM_CHEO", p)
    monkeypatch.setattr(RSA, "chay_kiem_cheo_tu_van", boc)
    tom, d = _chay_main(tmp_path, monkeypatch, "--kiem-cheo")
    assert seen["co_tom_tat"]  # chạy SAU khi G6_analysis_summary.json đã ghi
    assert json.loads(ghi.read_text(encoding="utf-8")) == ["chay", "--study", "KC-THU", "--gate", "G6"]
    sha_sau = hashlib.sha256((d / "G6_analysis_summary.json").read_bytes()).hexdigest()
    assert sha_sau == seen["sha_truoc"] and tom.get("primary_outcome")  # kiểm chéo không đụng tới kết quả chính


def test_main_khong_co_co_thi_khong_kiem_cheo(tmp_path, monkeypatch):
    p, ghi = _script_gia(tmp_path, 0)
    monkeypatch.setattr(RSA, "TEP_KIEM_CHEO", p)
    _chay_main(tmp_path, monkeypatch)
    assert not ghi.exists()


def test_main_kiem_cheo_sap_van_khong_lam_hong_phan_tich(tmp_path, monkeypatch):
    def hong(*a, **k):
        raise RuntimeError("tiến trình con sập")

    monkeypatch.setattr(RSA.subprocess, "run", hong)
    tom, d = _chay_main(tmp_path, monkeypatch, "--kiem-cheo")
    assert (d / "G6_analysis_summary.json").is_file() and tom.get("primary_outcome")
