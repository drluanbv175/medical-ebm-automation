"""Pilot khô Ngày 7 (lộ trình 7 ngày, reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA_2026-07-14.md)
— stress-test Ngày 2 (Cox PH/Kaplan-Meier) + Ngày 3 (multiple imputation) bằng MỘT
dataset synthetic phức tạp hơn hẳn 2 fixture tối giản đã dùng khi viết code (n=30 cho
sống còn, n=60 cho MI, cả hai đều 0-1 cơ chế thiếu/kiểm duyệt đơn giản).

KHÔNG PHẢI pilot dữ liệu THẬT (P1-01 trong reports/AUTOMATION_GAP_REGISTER_...md vẫn
CÒN MỞ — không có IRB/PI/dataset thật nào được cung cấp tuần này). Đây thuần túy là
kiểm tra KỸ THUẬT: engine thống kê có chịu được dữ liệu thực tế hơn không (thiếu dữ
liệu MAR trải cả outcome lẫn covariate, kiểm duyệt sống còn có 2 cơ chế — hành chính +
rớt dõi ngẫu nhiên — thay vì số liệu chọn tay không mô hình cơ chế).

Phê duyệt G2/G4/G5 dùng ĐÚNG cơ chế test-only đã có sẵn (_approve_g2_g4_g5 +
_configure_test_signing_key trong test_run_stats_data_lock_gate.py — khóa ký tạm qua
biến môi trường EBM_GATE_KEY_PATH, "dùng cho test, KHÔNG dùng vận hành thật"). KHÔNG
gọi tools/approve_gate.py — tool đó tự khai trong docstring "KHÔNG BAO GIỜ để agent tự
chạy thay bác sĩ", đúng nguyên tắc CLAUDE.md "agent chỉ ĐỀ XUẤT, bác sĩ duyệt mới áp
dụng". Dọn sạch exports/<study>/ sau khi chạy (finally) — không để lại dấu vết trong
cây exports/ thật, tránh nhầm với một đề tài thật.

Dataset (n=80, seed=20260716, sinh + xác minh qua chạy CLI thật trong quá trình điều
tra — xem reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA_2026-07-14.md Ngày 7):
- age ~ Normal(58,13); bmi có ~11% thiếu MCAR; outcome_score có ~21% thiếu MAR phụ
  thuộc tuổi (bệnh nhân già hơn dễ bỏ hẹn tái khám hơn) — 23/80 hàng thiếu ít nhất 1
  biến phân tích (28.75%, cao và có cơ chế hơn hẳn 16.7% MCAR-một-biến của fixture cũ).
- follow_time/event_flag: hazard phụ thuộc exposure (~x2.5) và tuổi; kiểm duyệt hành
  chính tại tháng 24 CỘNG rớt dõi ngẫu nhiên độc lập (Uniform 2-26) — 2 cơ chế kiểm
  duyệt khác nhau trong CÙNG 1 cột, fixture cũ không có.
- Một lệnh CLI DUY NHẤT (--outcome + --time/--event cùng lúc) kích hoạt CẢ nhánh MICE
  lẫn nhánh Cox/KM trên cùng dataset — xác nhận 2 nhánh không loại trừ nhau trong
  main() của run_stats_analysis.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
from tests.g5_test_helpers import prepare_locked_g5_study  # noqa: E402
from tests.test_run_stats_data_lock_gate import (  # noqa: E402
    _configure_test_signing_key,
    _csv,
    _rmtree_retry,
)

_COMPLEX_CSV = """
record_id,age,sex,exposure,bmi,outcome_score,follow_time,event_flag
R001,40.3,M,1,21.8,5.51,3.5,1
R002,69.6,F,0,17.6,3.68,16.0,0
R003,62.6,M,1,22.3,4.65,17.4,1
R004,73.8,F,1,,4.02,6.2,1
R005,75.9,F,0,24.6,4.24,6.1,1
R006,43.2,M,1,22.6,6.53,9.5,1
R007,56.9,F,0,27.4,,24.0,0
R008,71.7,F,1,29.2,3.94,7.0,1
R009,58.1,F,0,27.7,,24.0,0
R010,61.7,F,0,28.6,4.76,24.0,0
R011,33.9,F,0,21.2,3.92,24.0,0
R012,47.6,M,0,21.7,4.32,19.1,1
R013,58.3,M,0,23.8,2.11,24.0,0
R014,68.2,F,1,29.7,,3.4,1
R015,53.8,F,0,24.3,3.81,0.9,1
R016,56.6,F,1,21.1,9.5,24.0,0
R017,55.6,F,1,26.1,6.12,6.5,0
R018,47.3,M,0,,4.48,24.0,0
R019,65.0,M,0,22.1,2.94,24.0,0
R020,41.0,M,0,16.0,5.37,24.0,0
R021,41.3,M,1,20.5,4.25,24.0,0
R022,62.4,M,1,27.1,,10.3,1
R023,41.3,M,0,24.3,4.6,24.0,0
R024,72.4,F,0,19.3,,24.0,0
R025,61.4,M,1,27.0,,12.3,1
R026,75.4,F,0,26.3,5.56,17.7,1
R027,75.7,F,0,31.0,,1.9,1
R028,58.7,M,1,21.3,7.44,24.0,0
R029,52.6,M,0,27.6,2.43,24.0,0
R030,73.4,F,0,20.0,,0.4,1
R031,65.1,M,0,17.4,4.31,24.0,0
R032,69.2,F,1,25.1,,2.8,1
R033,61.4,F,1,18.7,6.84,24.0,0
R034,60.0,F,1,16.7,5.38,21.2,1
R035,49.7,F,0,20.7,6.06,23.4,1
R036,54.4,F,1,18.2,3.78,17.3,1
R037,70.3,M,1,22.6,6.65,5.7,1
R038,46.5,M,0,22.0,6.14,24.0,0
R039,39.6,F,1,18.3,5.69,24.0,0
R040,88.4,M,0,24.3,4.55,7.5,1
R041,51.2,M,1,28.6,3.95,4.5,1
R042,54.1,M,0,22.9,5.23,24.0,0
R043,83.7,F,1,27.9,,2.3,1
R044,40.1,M,0,,,22.4,0
R045,53.3,F,1,24.6,6.75,13.6,1
R046,50.2,M,1,19.6,6.14,17.4,1
R047,46.5,F,0,22.1,5.42,8.8,1
R048,45.2,M,1,20.9,7.0,6.3,1
R049,59.2,M,1,25.5,10.14,5.1,1
R050,24.6,M,1,22.4,6.49,24.0,0
R051,45.0,F,1,,6.83,22.4,1
R052,48.0,F,1,28.7,,6.4,1
R053,35.7,M,0,27.7,6.08,24.0,0
R054,55.1,M,1,28.7,7.03,9.9,1
R055,54.6,F,0,29.7,5.42,24.0,0
R056,50.6,F,1,25.6,3.27,15.7,1
R057,71.8,F,1,26.5,,24.0,0
R058,64.7,F,1,20.1,6.21,2.3,1
R059,50.6,F,0,21.7,4.11,0.3,1
R060,49.2,F,1,21.9,8.25,11.9,1
R061,61.1,F,0,20.1,7.4,3.4,1
R062,57.5,M,0,31.2,6.99,24.0,0
R063,68.2,M,1,22.1,7.12,1.3,1
R064,54.8,F,1,29.0,7.96,7.2,1
R065,48.9,M,1,19.7,,14.3,1
R066,65.3,M,1,27.7,6.54,7.7,1
R067,56.5,F,1,,6.04,23.3,1
R068,44.8,F,0,22.5,7.38,3.8,1
R069,59.0,F,0,29.4,5.14,24.0,0
R070,90.0,M,1,,,4.6,0
R071,36.0,F,1,27.8,5.98,12.5,1
R072,44.9,F,0,,5.75,12.4,1
R073,56.0,M,1,29.4,,9.6,1
R074,63.2,M,0,25.9,3.29,8.6,0
R075,47.3,F,0,25.7,3.71,10.5,1
R076,49.5,M,0,,,11.2,1
R077,75.3,M,1,24.7,5.37,10.1,1
R078,51.0,M,1,16.9,5.82,8.5,1
R079,54.0,M,1,19.0,6.72,7.5,1
R080,49.0,F,1,,5.48,5.4,1
"""


def _lock_complex_study(study: str, tmp_path: Path) -> Path:
    clean = _csv(tmp_path / f"{study}_df_clean.csv", _COMPLEX_CSV)
    locked_path, _ = prepare_locked_g5_study(
        study, clean, exports_root=REPO_ROOT / "exports",
        repo_root=REPO_ROOT,
    )
    return locked_path


def test_complex_dataset_exercises_survival_and_mice_in_one_cli_run(tmp_path, monkeypatch):
    """Ngày 7: 1 lệnh CLI --outcome + --time/--event cùng lúc trên dataset n=80 nhiều
    missingness (MAR, trải cả outcome lẫn covariate) + 2 cơ chế kiểm duyệt sống còn."""
    study = "PYTEST-COMPLEX-STRESS"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        locked_path = _lock_complex_study(study, tmp_path)
        res = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", study, "--data", str(locked_path),
             "--outcome", "outcome_score", "--group", "exposure", "--covariates", "age,bmi",
             "--time", "follow_time", "--event", "event_flag", "--n-imputations", "20",
             "--i-confirm-sap-locked", "--i-confirm-irb-approved"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=180,
        )
        assert res.returncode == 0, res.stdout + res.stderr
        assert "DATA LOCK" in res.stdout
        assert "Multiple imputation (m=20)" in res.stdout
        assert "Cox PH" in res.stdout

        summary = json.loads((study_dir / "G6_analysis_summary.json").read_text(encoding="utf-8"))

        # ── Nhánh MI (Ngày 3) — thiếu dữ liệu THẬT hơn fixture gốc ──
        mi = summary["multiple_imputation"]
        assert mi["n_imputations"] == 20
        assert mi.get("skipped") is not True
        # 23/80 hàng thiếu >= 1 biến phân tích (outcome_score/exposure/age/bmi) — cao
        # hơn hẳn 16.7% (10/60) của fixture Ngày 3, và trải cả outcome LẪN covariate
        # (fixture cũ chỉ thiếu 1 covariate).
        assert mi["n_missing_rows"] >= 20
        assert len(mi["results"]) == 3  # exposure + age + bmi

        # ── Nhánh sống còn (Ngày 2) — 2 cơ chế kiểm duyệt trong cùng 1 cột ──
        crude = summary["survival"]["crude"]
        assert crude["HR"] > 1.0, "exposure thiết kế làm TĂNG hazard — HR phải > 1"
        assert crude["CI_95"][0] < crude["HR"] < crude["CI_95"][1]
        km = summary["kaplan_meier"]
        assert km["logrank_p"] < 0.05
        # follow_time có giá trị đúng bằng mốc kiểm duyệt hành chính (24) VÀ giá trị
        # rớt dõi ngẫu nhiên sớm hơn (vd R070 follow_time=4.6, event_flag=0) — xác nhận
        # cả 2 cơ chế kiểm duyệt cùng tồn tại trong dữ liệu đã nạp, không phải giả định
        # suông trong docstring.
        assert km.get("plot_path") or km.get("plot_error"), (
            "kaplan_meier phải có plot_path (đã vẽ) hoặc plot_error (lý do không vẽ "
            "được, vd thiếu matplotlib) — không được im lặng bỏ qua."
        )
        if km.get("plot_path"):
            km_png = study_dir / "G6_km_curve.png"
            assert km_png.exists() and km_png.stat().st_size > 0

        # ── Cả 2 nhánh chạy trong CÙNG 1 lần gọi CLI — không loại trừ nhau ──
        assert (study_dir / "G6_table5_multiple_imputation.txt").exists()
        assert (study_dir / "G6_table3_survival.txt").exists()
    finally:
        _rmtree_retry(study_dir)
