"""Cox PH + Kaplan-Meier THẬT trong run_stats_analysis.py — vá 2026-07-15 (Ngày 2
lộ trình 7 ngày, reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA_2026-07-14.md).

Trước đây Cox/KM (lifelines) chỉ tồn tại nhúng trong chuỗi template mà
run_g6_auto.py ghi ra exports/<study>/run_analysis_cli.py cho bác sĩ tự chạy
tay — run_stats_analysis.py (script chạy TRỰC TIẾP trên dữ liệu đã khóa, qua
cổng G2/G4/G5) tự khai "CHƯA hỗ trợ phân tích sống còn". File này kiểm cả unit
(gọi hàm trực tiếp, số liệu chính xác) lẫn end-to-end (CLI thật qua cổng
data-lock, dùng lại helper của test_run_stats_data_lock_gate.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
import run_stats_analysis as RSA  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    prepare_locked_g5_study,
    prepare_upstream_approvals,
    write_g5_toolkit,
)
from tests.test_run_stats_data_lock_gate import (  # noqa: E402
    _configure_test_signing_key,
    _csv,
    _rmtree_retry,
)

# ── Dữ liệu synthetic có CENSORING, HR khác 1 rõ ràng (không chỉ "chạy không lỗi") ──
# Nhóm 1 (exposure_var=1): thời gian tới biến cố NGẮN hơn hẳn nhóm 0 → kỳ vọng HR > 1.
_SURVIVAL_CSV = """
record_id,age,exposure_var,follow_time,event_flag
S01,45,0,40,1
S02,50,0,55,0
S03,42,0,48,1
S04,60,0,60,0
S05,38,0,35,1
S06,55,0,58,0
S07,41,0,44,1
S08,47,0,52,0
S09,52,0,50,1
S10,39,0,57,0
S11,44,0,46,1
S12,58,0,59,0
S13,36,0,42,1
S14,49,0,53,0
S15,43,0,45,1
S16,46,1,10,1
S17,51,1,15,1
S18,40,1,8,1
S19,61,1,20,0
S20,37,1,12,1
S21,56,1,25,1
S22,42,1,6,1
S23,48,1,18,1
S24,53,1,22,0
S25,38,1,9,1
S26,45,1,14,1
S27,59,1,28,1
S28,35,1,7,1
S29,50,1,16,1
S30,44,1,11,1
"""


def _survival_df() -> pd.DataFrame:
    from io import StringIO
    return pd.read_csv(StringIO(_SURVIVAL_CSV.strip() + "\n"))


# ════════════════════════════════════════════════════════════════════════════
# Unit test — gọi thẳng survival_model()/kaplan_meier_summary(), số liệu chính xác
# ════════════════════════════════════════════════════════════════════════════

class TestSurvivalModelUnit:
    def test_crude_hr_greater_than_one_for_higher_hazard_group(self):
        df = _survival_df()
        res = RSA.survival_model(df, "follow_time", "event_flag", "exposure_var", [])
        assert "crude" not in res or "crude_error" not in res, res.get("crude_error")
        c = res["crude"]
        assert c["HR"] > 1.5, f"Nhóm 1 có hazard rõ ràng cao hơn — kỳ vọng HR > 1.5, được {c['HR']}"
        lo, hi = c["CI_95"]
        assert lo < c["HR"] < hi, "HR phải nằm trong khoảng CI của chính nó"
        assert 0.0 <= c["p"] <= 1.0
        assert 0.5 <= c["concordance"] <= 1.0
        assert res["n"] == 30
        assert res["n_events"] == 21  # 8 (nhóm 0) + 13 (nhóm 1), đếm tay từ CSV

    def test_adjusted_model_runs_with_covariate(self):
        df = _survival_df()
        res = RSA.survival_model(df, "follow_time", "event_flag", "exposure_var", ["age"])
        assert "adjusted" in res, res.get("adjusted_error")
        a = res["adjusted"]
        assert a["HR"] > 1.0
        assert a["CI_95"][0] < a["CI_95"][1]
        assert res["adjusted_covariates"] == ["age"]

    def test_missing_covariate_column_silently_dropped_not_crashed(self):
        """Covariate không có trong df bị loại (giống multivariate_model()), không crash."""
        df = _survival_df()
        res = RSA.survival_model(df, "follow_time", "event_flag", "exposure_var", ["age", "khong_ton_tai"])
        assert "adjusted" in res
        assert res["adjusted_covariates"] == ["age"]

    def test_kaplan_meier_median_and_logrank(self):
        df = _survival_df()
        km = RSA.kaplan_meier_summary(df, "follow_time", "event_flag", "exposure_var")
        assert "0" in km["groups"] and "1" in km["groups"]
        assert km["groups"]["0"]["n"] == 15
        assert km["groups"]["1"]["n"] == 15
        med0 = km["groups"]["0"]["median_survival"]
        med1 = km["groups"]["1"]["median_survival"]
        assert med0 is not None and med1 is not None
        assert med1 < med0, "Nhóm 1 có biến cố sớm hơn — trung vị sống còn phải NGẮN hơn nhóm 0"
        assert 0.0 <= km["logrank_p"] <= 1.0
        assert km["logrank_p"] < 0.05, "Khác biệt sống còn giữa 2 nhóm quá rõ để log-rank p >= 0.05"

    def test_without_lifelines_returns_structured_error_not_crash(self, monkeypatch):
        monkeypatch.setattr(RSA, "HAS_LIFELINES", False)
        df = _survival_df()
        res = RSA.survival_model(df, "follow_time", "event_flag", "exposure_var", [])
        assert "error" in res and "lifelines" in res["error"]
        km = RSA.kaplan_meier_summary(df, "follow_time", "event_flag", "exposure_var")
        assert "error" in km


class TestSurvivalArgValidation:
    """--time/--event phải đi cùng nhau; --group bắt buộc cho Cox — kiểm ở main()
    TRƯỚC khi chạm cổng data-lock (lỗi sai cờ không nên trông như thiếu phê duyệt)."""

    def _run(self, extra_args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", "PYTEST-SURV-ARGVAL", "--data", "nonexistent.csv", *extra_args],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )

    def test_time_without_event_rejected(self):
        res = self._run(["--time", "follow_time", "--group", "exposure_var"])
        assert res.returncode != 0
        assert "--time và --event" in res.stdout

    def test_event_without_time_rejected(self):
        res = self._run(["--event", "event_flag", "--group", "exposure_var"])
        assert res.returncode != 0
        assert "--time và --event" in res.stdout

    def test_survival_without_group_rejected(self):
        res = self._run(["--time", "follow_time", "--event", "event_flag"])
        assert res.returncode != 0
        assert "--group" in res.stdout


# ════════════════════════════════════════════════════════════════════════════
# End-to-end — CLI thật qua cổng data-lock/G2/G4/G5 (mẫu dùng lại từ
# test_run_stats_data_lock_gate.py)
# ════════════════════════════════════════════════════════════════════════════

def _lock_survival_study(study: str, tmp_path: Path) -> Path:
    clean = _csv(tmp_path / f"{study}_df_clean.csv", _SURVIVAL_CSV)
    locked_path, _ = prepare_locked_g5_study(
        study, clean, exports_root=REPO_ROOT / "exports",
        repo_root=REPO_ROOT,
    )
    return locked_path


def test_survival_cli_end_to_end_through_data_lock_gate(tmp_path, monkeypatch):
    study = "PYTEST-SURV-E2E"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        locked_path = _lock_survival_study(study, tmp_path)
        res = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", study, "--data", str(locked_path),
             "--time", "follow_time", "--event", "event_flag",
             "--group", "exposure_var", "--covariates", "age",
             "--i-confirm-sap-locked", "--i-confirm-irb-approved"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
        )
        assert res.returncode == 0, res.stdout + res.stderr
        assert "Cox PH thô: HR=" in res.stdout

        surv_txt = (study_dir / "G6_table3_survival.txt").read_text(encoding="utf-8")
        assert "Cox PH" in surv_txt
        assert "KAPLAN-MEIER" in surv_txt

        r_script = (study_dir / "G6_survival_syntax.R").read_text(encoding="utf-8")
        assert "coxph(Surv(follow_time, event_flag)" in r_script
        # Không comment sẵn (khác bản template run_g6_auto.py) — đây là phân tích ĐÃ CHẠY THẬT.
        assert "# coxph" not in r_script and "#coxph" not in r_script

        summary = json.loads((study_dir / "G6_analysis_summary.json").read_text(encoding="utf-8"))
        crude = summary["survival"]["crude"]
        assert isinstance(crude["HR"], float) and crude["HR"] > 1.0
        assert isinstance(crude["p"], float)
        assert summary["kaplan_meier"]["logrank_p"] < 0.05

        km_png = study_dir / "G6_km_curve.png"
        assert summary["kaplan_meier"].get("plot_path"), summary["kaplan_meier"].get("plot_error")
        assert km_png.exists() and km_png.stat().st_size > 0
    finally:
        _rmtree_retry(study_dir)


def test_survival_cli_blocked_without_data_lock(tmp_path, monkeypatch):
    """Cùng cổng data-lock áp dụng cho nhánh sống còn — không phải đường vòng.
    G2/G4/G5 được duyệt hợp lệ (để chạm ĐÚNG cổng đang test, không bị chặn sớm
    hơn ở G2) nhưng dataset KHÔNG được khóa qua lock_analysis_dataset.py."""
    study = "PYTEST-SURV-NOLOCK"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        study_dir.mkdir(parents=True, exist_ok=True)
        write_g5_toolkit(study, study_dir)
        prepare_upstream_approvals(study, study_dir, repo_root=REPO_ROOT)
        unlocked = _csv(tmp_path / "unlocked.csv", _SURVIVAL_CSV)
        res = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", study, "--data", str(unlocked),
             "--time", "follow_time", "--event", "event_flag",
             "--group", "exposure_var",
             "--i-confirm-sap-locked", "--i-confirm-irb-approved"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
        )
        assert res.returncode != 0
        assert "G5 (khóa DB)" in res.stdout
        assert "DRAFT_READY_NEEDS_REAL_DATA" in res.stdout
    finally:
        _rmtree_retry(study_dir)
