"""Multiple imputation THẬT trong run_stats_analysis.py — vá 2026-07-15 (Ngày 3
lộ trình 7 ngày, reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA_2026-07-14.md).

Trước đây "MI" trong exports/<study>/sensitivity_analysis.py (template do
run_g6_auto.py sinh ra) chỉ là mean-impute, tự khai "MI-demo (mean-impute; R
mice m=20 for real)" — MI thật (mice m=20) chỉ tồn tại trong R template, bị
comment `#` chờ dữ liệu thật. File này kiểm cả unit (gọi thẳng
multiple_imputation_model(), số liệu hợp lý) lẫn end-to-end (CLI thật qua cổng
data-lock, dùng lại helper của test_run_stats_data_lock_gate.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
import run_stats_analysis as RSA  # noqa: E402

from tests.g5_test_helpers import prepare_locked_g5_study  # noqa: E402
from tests.test_run_stats_data_lock_gate import (  # noqa: E402
    _configure_test_signing_key,
    _csv,
    _rmtree_retry,
)

# ── n=60, 10 hàng thiếu 'age' (16.7% MCAR, seed=2026) — có cả outcome liên tục
# và nhị phân để test cả 2 nhánh linear_mi/logistic_mi trên CÙNG một dataset. ──
_MI_CSV = """
record_id,age,group,outcome_cont,outcome_bin
S01,45.7,0,2.2,0
S02,36.1,1,4.92,0
S03,53.1,1,3.79,1
S04,49.9,1,3.81,1
S05,64.5,0,3.53,0
S06,53.0,0,4.02,0
S07,41.7,0,4.43,0
S08,34.0,1,4.18,0
S09,56.1,1,5.77,1
S10,46.8,0,4.79,0
S11,49.3,1,3.89,1
S12,43.9,1,4.49,1
S13,,1,4.64,1
S14,59.1,0,4.58,1
S15,,1,4.63,1
S16,52.2,1,6.01,1
S17,,1,4.34,0
S18,37.5,1,3.79,1
S19,69.7,1,5.34,1
S20,46.8,0,3.33,0
S21,53.6,1,3.5,1
S22,57.5,0,4.91,1
S23,,1,3.61,1
S24,66.8,0,5.08,0
S25,50.6,0,4.81,0
S26,33.0,1,2.69,1
S27,46.4,1,4.87,0
S28,77.3,1,4.76,1
S29,,1,4.61,0
S30,35.8,0,3.82,0
S31,48.4,1,3.67,1
S32,,1,3.58,0
S33,43.8,0,3.45,0
S34,44.0,1,3.94,0
S35,61.8,1,4.27,1
S36,58.3,0,4.21,1
S37,49.9,0,3.47,0
S38,49.3,0,4.09,1
S39,,1,5.11,1
S40,45.7,1,3.62,1
S41,49.9,1,3.9,1
S42,51.4,1,4.77,1
S43,64.8,0,4.31,1
S44,38.3,1,4.24,1
S45,59.4,1,6.15,0
S46,66.7,1,6.43,1
S47,41.4,0,1.73,0
S48,51.9,0,3.72,1
S49,,0,3.47,0
S50,,1,3.39,1
S51,45.2,0,1.88,0
S52,40.0,0,1.12,1
S53,,1,3.44,1
S54,55.7,1,4.1,0
S55,17.3,1,3.61,1
S56,55.1,0,3.43,0
S57,59.1,1,5.38,1
S58,39.7,0,4.36,0
S59,55.6,0,3.03,1
S60,57.2,0,3.22,0
"""


def _mi_df() -> pd.DataFrame:
    return pd.read_csv(StringIO(_MI_CSV.strip() + "\n"))


# ════════════════════════════════════════════════════════════════════════════
# Unit test — gọi thẳng multiple_imputation_model()/format_mi_text()
# ════════════════════════════════════════════════════════════════════════════

class TestMultipleImputationUnit:
    def test_continuous_outcome_pools_real_estimates(self):
        df = _mi_df()
        mi = RSA.multiple_imputation_model(df, "outcome_cont", "group", ["age"],
                                            "continuous", n_imputations=20)
        assert mi.get("model") == "linear_mi"
        assert mi["n_total"] == 60
        assert mi["n_missing_rows"] == 10
        assert mi["n_complete_case"] == 50
        by_var = {r["variable"]: r for r in mi["results"]}
        assert "group" in by_var and "age" in by_var
        for r in mi["results"]:
            lo, hi = r["CI_95"]
            assert lo < hi, f"CI phải low<high, được {r['CI_95']}"
            assert 0.0 <= r["p"] <= 1.0

    def test_binary_outcome_pools_real_estimates(self):
        df = _mi_df()
        mi = RSA.multiple_imputation_model(df, "outcome_bin", "group", ["age"],
                                            "binary", n_imputations=20)
        assert mi.get("model") == "logistic_mi"
        by_var = {r["variable"]: r for r in mi["results"]}
        assert "group" in by_var and "age" in by_var
        for r in mi["results"]:
            assert r["OR_adj"] > 0, "OR phải dương (exp của hệ số thật)"
            lo, hi = r["CI_95"]
            assert lo < hi
            assert 0.0 <= r["p"] <= 1.0

    def test_skipped_when_no_missing_data_in_analysis_columns(self):
        df = _mi_df().dropna(subset=["age"])
        mi = RSA.multiple_imputation_model(df, "outcome_cont", "group", ["age"], "continuous")
        assert mi.get("skipped") is True
        assert "MULTIPLE IMPUTATION" in RSA.format_mi_text(mi)

    def test_missing_outside_analysis_columns_does_not_trigger_mi(self):
        """Cột KHÔNG dùng trong phân tích (vd chỉ cho Bảng 1) có thiếu KHÔNG được
        kích hoạt MI — khác analyze_missingness() vốn quét toàn dataset."""
        df = _mi_df().dropna(subset=["age"]).copy()
        df["unrelated_var"] = None
        mi = RSA.multiple_imputation_model(df, "outcome_cont", "group", ["age"], "continuous")
        assert mi.get("skipped") is True

    def test_column_names_with_special_characters_handled_via_safe_rename(self):
        """MICEData/patsy tự dựng công thức nội bộ theo TÊN CỘT GỐC — tên có
        khoảng trắng/gạch ngang làm patsy.dmatrices ném SyntaxError nếu không
        đổi tên an toàn trước (xác nhận qua test thủ công khi viết hàm này)."""
        df = _mi_df().rename(columns={"age": "tuổi - năm", "group": "nhóm phơi nhiễm"})
        mi = RSA.multiple_imputation_model(
            df, "outcome_cont", "nhóm phơi nhiễm", ["tuổi - năm"], "continuous")
        assert mi.get("model") == "linear_mi", mi.get("error")
        by_var = {r["variable"] for r in mi["results"]}
        assert by_var == {"nhóm phơi nhiễm", "tuổi - năm"}, "phải trả về ĐÚNG tên cột gốc, không phải v0/v1"

    def test_without_statsmodels_returns_structured_error_not_crash(self, monkeypatch):
        monkeypatch.setattr(RSA, "HAS_STATSMODELS", False)
        df = _mi_df()
        mi = RSA.multiple_imputation_model(df, "outcome_cont", "group", ["age"], "continuous")
        assert "error" in mi and "statsmodels" in mi["error"]

    def test_format_mi_text_shows_complete_case_comparison(self):
        df = _mi_df()
        mi = RSA.multiple_imputation_model(df, "outcome_cont", "group", ["age"], "continuous")
        mv = RSA.multivariate_model(df, "outcome_cont", "group", ["age"], "continuous")
        text = RSA.format_mi_text(mi, mv)
        assert "MULTIPLE IMPUTATION" in text
        assert "complete-case" in text.lower()
        assert "group" in text and "age" in text


# ════════════════════════════════════════════════════════════════════════════
# End-to-end — CLI thật qua cổng data-lock/G2/G4/G5
# ════════════════════════════════════════════════════════════════════════════

def _lock_mi_study(study: str, tmp_path: Path) -> Path:
    clean = _csv(tmp_path / f"{study}_df_clean.csv", _MI_CSV)
    locked_path, _ = prepare_locked_g5_study(
        study, clean, exports_root=REPO_ROOT / "exports",
        repo_root=REPO_ROOT,
    )
    return locked_path


def test_mi_cli_end_to_end_through_data_lock_gate(tmp_path, monkeypatch):
    study = "PYTEST-MI-E2E"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        locked_path = _lock_mi_study(study, tmp_path)
        res = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", study, "--data", str(locked_path),
             "--outcome", "outcome_cont", "--group", "group", "--covariates", "age",
             "--n-imputations", "20",
             "--i-confirm-sap-locked", "--i-confirm-irb-approved"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
        )
        assert res.returncode == 0, res.stdout + res.stderr
        assert "Multiple imputation (m=20)" in res.stdout

        mi_txt = (study_dir / "G6_table5_multiple_imputation.txt").read_text(encoding="utf-8")
        assert "MULTIPLE IMPUTATION" in mi_txt

        summary = json.loads((study_dir / "G6_analysis_summary.json").read_text(encoding="utf-8"))
        mi = summary["multiple_imputation"]
        assert mi["n_imputations"] == 20
        assert mi["n_missing_rows"] == 10
        assert len(mi["results"]) == 2  # group + age
    finally:
        _rmtree_retry(study_dir)


def test_mi_cli_skips_cleanly_when_no_missing_data(tmp_path, monkeypatch):
    study = "PYTEST-MI-NOMISS"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        complete_csv = "\n".join(
            line for line in _MI_CSV.strip().splitlines()
            if line.split(",")[1] != ""  # loại các hàng thiếu age
        )
        locked_path = _lock_mi_study_from_text(study, tmp_path, complete_csv)
        res = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", study, "--data", str(locked_path),
             "--outcome", "outcome_cont", "--group", "group", "--covariates", "age",
             "--i-confirm-sap-locked", "--i-confirm-irb-approved"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120,
        )
        assert res.returncode == 0, res.stdout + res.stderr
        assert "bỏ qua" in res.stdout
        assert not (study_dir / "G6_table5_multiple_imputation.txt").exists()
    finally:
        _rmtree_retry(study_dir)


def _lock_mi_study_from_text(study: str, tmp_path: Path, csv_text: str) -> Path:
    clean = _csv(tmp_path / f"{study}_df_clean.csv", csv_text)
    locked_path, _ = prepare_locked_g5_study(
        study, clean, exports_root=REPO_ROOT / "exports",
        repo_root=REPO_ROOT,
    )
    return locked_path
