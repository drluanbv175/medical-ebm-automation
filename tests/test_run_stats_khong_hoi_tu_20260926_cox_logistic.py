"""Hồi quy #10 (26/09/2026) — Cox/logistic/MI KHÔNG hội tụ không được in HR/OR như thật.

Lỗi gốc: tools/run_stats_analysis.py đặt warnings.filterwarnings("ignore") toàn cục,
Cox trên dữ liệu tách hoàn toàn in «HR = 255220126.69 (95%CI 0.0–inf)» kèm dòng «số liệu
lấy trực tiếp từ dữ liệu thật»; logistic tách gần hoàn toàn trả convergence=False nhưng
bảng 4 không đọc trường đó. Bản vá:
  (1) bọc từng fit bằng catch_warnings(record=True) — bắt ConvergenceWarning;
  (2) phép kiểm ĐỘC LẬP (CI không hữu hạn/bằng 0, |hệ số|/sai số chuẩn quá lớn,
      converged=False) — không phụ thuộc câu chữ cảnh báo;
  (3) cờ khong_hoi_tu + ly_do trong JSON, số thô chỉ ở «so_tho_khong_tin_cay»;
  (4) văn bản/CLI THAY con số bằng dòng «⚠ MÔ HÌNH KHÔNG HỘI TỤ …», ✓ đổi thành ⚠;
  (5) KHÔNG tự chuyển Firth/penalizer (SAP đã khoá ở G4).
Dữ liệu synthetic, không PII.
"""
from __future__ import annotations

import json
import subprocess
import sys
import warnings
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
import run_stats_analysis as RSA  # noqa: E402

pytest.importorskip("lifelines")
pytest.importorskip("statsmodels")

# Bản fixture CŨ của test_run_stats_survival.py — TÁCH HOÀN TOÀN: nhóm 1 luôn ≤28 ngày,
# nhóm 0 luôn ≥35 ngày ⇒ likelihood đơn điệu, Cox không hội tụ.
_TACH_HOAN_TOAN_CSV = """
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


def _df_tach() -> pd.DataFrame:
    return pd.read_csv(StringIO(_TACH_HOAN_TOAN_CSV.strip() + "\n"))


def _df_tach_gan_logistic(missing: bool = False) -> pd.DataFrame:
    """Tách GẦN hoàn toàn (quasi-separation): x>0 ⇒ y=1, x<0 ⇒ y=0, x=0 ⇒ y lẫn.
    (Tách HOÀN TOÀN làm statsmodels ném 'Singular matrix' — nhánh except đã có nhãn
    [CẦN BIOSTATISTICIAN]; lỗ hổng thật là ca này: fit xong, converged=False, OR≈1e10.)
    Tất định (không RNG); EPV đủ (40 biến cố nhóm hiếm ≥ 10/biến)."""
    x = np.r_[np.linspace(1, 5, 30), np.zeros(20), np.linspace(-5, -1, 30)]
    y = np.r_[np.ones(30), np.tile([1, 0], 10), np.zeros(30)]
    z = np.round(50 + 10 * np.sin(np.arange(80) * 1.7), 1)
    df = pd.DataFrame({"y": y, "x": x, "z": z})
    if missing:
        df.loc[[3, 17, 41, 55, 66, 72], "z"] = np.nan
    return df


# ════════════════════════════════════════════════════════════════════════════
# Cox — tách hoàn toàn
# ════════════════════════════════════════════════════════════════════════════

class TestCoxKhongHoiTu:
    def test_crude_va_adjusted_gan_co_va_go_con_so(self):
        res = RSA.survival_model(_df_tach(), "follow_time", "event_flag", "exposure_var", ["age"])
        for key in ("crude", "adjusted"):
            m = res[key]
            assert m.get("khong_hoi_tu") is True, (key, m)
            assert m["ly_do"], key
            # Con số KHÔNG còn ở khoá chính — người/agent đọc JSON không chép được HR.
            for k in ("HR", "CI_95", "p"):
                assert k not in m, (key, k)
            assert "HR" in m["so_tho_khong_tin_cay"]
        # n / số biến cố giữ nguyên (không đổi fixture ngầm).
        assert res["n"] == 30 and res["n_events"] == 21

    def test_phep_kiem_doc_lap_bat_duoc_CI_vo_han(self):
        """Kiểm độc lập với câu chữ cảnh báo: CI sau exp chạm 0/inf phải có lý do riêng."""
        res = RSA.survival_model(_df_tach(), "follow_time", "event_flag", "exposure_var", [])
        ly_do = " | ".join(res["crude"]["ly_do"])
        assert "exposure_var: cận trên CI sau exp" in ly_do, ly_do

    def test_catch_warnings_bat_duoc_ConvergenceWarning(self):
        """Filter «ignore» toàn cục không được nuốt cảnh báo hội tụ của lifelines.
        pytest tự đặt lại bộ lọc cho mỗi test, nên phải DỰNG LẠI đúng filter
        «ignore» mà module đặt lúc import (chạy CLI thật) rồi mới gọi fit."""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            res = RSA.survival_model(_df_tach(), "follow_time", "event_flag", "exposure_var", [])
        assert any(ld.startswith("ConvergenceWarning") for ld in res["crude"]["ly_do"]), \
            res["crude"]["ly_do"]

    def test_van_ban_thay_con_so_bang_dong_canh_bao(self):
        res = RSA.survival_model(_df_tach(), "follow_time", "event_flag", "exposure_var", ["age"])
        txt = RSA.format_survival_text(res)
        assert RSA.DONG_KHONG_HOI_TU in txt
        assert "Thô: HR =" not in txt
        assert "HR = 255220126" not in txt and "255220126" not in txt
        assert "Firth" in txt  # nêu như lựa chọn cho thống kê viên, không tự áp

    def test_du_lieu_chong_lap_khong_gan_co(self):
        """Đối chứng dương: dữ liệu chồng lấp ⇒ không cờ, HR/CI hữu hạn giữ ở khoá chính."""
        df = _df_tach()
        df.loc[df.record_id == "S05", "follow_time"] = 13
        df.loc[df.record_id == "S21", "follow_time"] = 38
        df.loc[df.record_id == "S27", "follow_time"] = 50
        res = RSA.survival_model(df, "follow_time", "event_flag", "exposure_var", [])
        c = res["crude"]
        assert "khong_hoi_tu" not in c and "so_tho_khong_tin_cay" not in c
        assert 0.0 < c["CI_95"][0] < c["HR"] < c["CI_95"][1] < float("inf")

    def test_hiep_bien_tach_hoan_toan_gan_co_mo_hinh_hieu_chinh(self):
        """Bổ sung khi rà phản biện: phép kiểm độc lập phải chạy trên MỌI hệ số, không
        chỉ group_col. Phơi nhiễm chồng lấp (thô hội tụ) nhưng hiệp biến «marker» tách
        hoàn toàn (mọi ca marker=1 có biến cố sớm nhất) ⇒ mô hình hiệu chỉnh không tin
        cậy dù HR của phơi nhiễm trông hữu hạn. Đột biến «chỉ kiểm group_col» phải đỏ."""
        df = _df_tach()
        df.loc[df.record_id == "S05", "follow_time"] = 13
        df.loc[df.record_id == "S21", "follow_time"] = 38
        df.loc[df.record_id == "S27", "follow_time"] = 50
        df["marker"] = ((df.follow_time <= 9) & (df.event_flag == 1)).astype(int)
        res = RSA.survival_model(df, "follow_time", "event_flag", "exposure_var", ["marker"])
        assert "khong_hoi_tu" not in res["crude"], res["crude"]
        a = res["adjusted"]
        assert a.get("khong_hoi_tu") is True and "HR" not in a, a
        assert any(ld.startswith("marker: ") for ld in a["ly_do"]), a["ly_do"]


# ════════════════════════════════════════════════════════════════════════════
# Logistic đa biến + MI — tách gần hoàn toàn
# ════════════════════════════════════════════════════════════════════════════

class TestLogisticKhongHoiTu:
    def test_multivariate_gan_co_va_bang4_khong_in_so(self):
        mv = RSA.multivariate_model(_df_tach_gan_logistic(), "y", "x", ["z"], "binary")
        assert "error" not in mv and "warning" not in mv, mv
        assert mv.get("khong_hoi_tu") is True, mv
        rx = next(r for r in mv["results"] if r["variable"] == "x")
        assert rx.get("khong_hoi_tu") is True and "OR_adj" not in rx
        txt = RSA.format_multivariate_text(mv)
        assert RSA.DONG_KHONG_HOI_TU in txt
        raw_or = str(rx["so_tho_khong_tin_cay"]["OR_adj"])
        assert raw_or not in txt, "Con số OR của mô hình không hội tụ vẫn lọt vào Bảng 4"

    def test_bang4_doc_truong_convergence_false(self):
        """Dù thiếu cờ khong_hoi_tu (dict cũ), convergence=False vẫn phải hiện ⚠."""
        mv = {"model": "logistic", "n": 10, "aic": 1.0, "convergence": False,
              "results": [{"variable": "x", "OR_adj": 1.5, "CI_95": [1.1, 2.0], "p": 0.01}]}
        assert RSA.DONG_KHONG_HOI_TU in RSA.format_multivariate_text(mv)

    def test_mi_gan_co_va_bang5_khong_in_so(self):
        df = _df_tach_gan_logistic(missing=True)
        # MICEData rút ngẫu nhiên từ np.random toàn cục — cố định hạt giống để test
        # tất định (vài hạt giống cho 'Singular matrix' ⇒ nhánh except, không phải ca cần kiểm).
        np.random.seed(20260926)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mi = RSA.multiple_imputation_model(df, "y", "x", ["z"], "binary", n_imputations=3)
        assert "error" not in mi and not mi.get("skipped"), mi
        assert mi.get("khong_hoi_tu") is True, mi
        rx = next(r for r in mi["results"] if r["variable"] == "x")
        assert rx.get("khong_hoi_tu") is True and "OR_adj" not in rx
        txt = RSA.format_mi_text(mi)
        assert RSA.DONG_KHONG_HOI_TU in txt
        assert str(rx["so_tho_khong_tin_cay"]["OR_adj"]) not in txt


class TestPhepKiemDocLap:
    def test_ci_vo_han_va_he_so_lon(self):
        assert RSA._ly_do_tu_uoc_luong("x", 0.5, 0.2, 0.1, 0.9) == []
        assert RSA._ly_do_tu_uoc_luong("x", 20.0, 0.5, 19.0, 21.0)  # |coef| > 15
        assert RSA._ly_do_tu_uoc_luong("x", 1.0, 50.0, -97.0, 99.0)  # se > 10
        assert RSA._ly_do_tu_uoc_luong("x", 1.0, 0.5, -1000.0, 2.0)  # exp(cận dưới)=0
        assert RSA._ly_do_tu_uoc_luong("x", 1.0, 0.5, 0.0, float("inf"))


# ════════════════════════════════════════════════════════════════════════════
# End-to-end — CLI thật: dòng ✓ đổi thành ⚠, JSON mang cờ
# ════════════════════════════════════════════════════════════════════════════

def test_cli_cox_tach_hoan_toan_in_canh_bao_khong_in_HR(tmp_path, monkeypatch):
    from tests.g5_test_helpers import prepare_locked_g5_study
    from tests.test_run_stats_data_lock_gate import (
        _configure_test_signing_key,
        _csv,
        _rmtree_retry,
    )

    study = "PYTEST-SURV-KHT-20260926"
    study_dir = REPO_ROOT / "exports" / study
    _rmtree_retry(study_dir)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        clean = _csv(tmp_path / f"{study}_df_clean.csv", _TACH_HOAN_TOAN_CSV)
        locked_path, _ = prepare_locked_g5_study(
            study, clean, exports_root=REPO_ROOT / "exports", repo_root=REPO_ROOT)
        res = subprocess.run(
            [PYTHON, str(TOOLS_DIR / "run_stats_analysis.py"),
             "--study", study, "--data", str(locked_path),
             "--time", "follow_time", "--event", "event_flag",
             "--group", "exposure_var", "--covariates", "age",
             "--i-confirm-sap-locked", "--i-confirm-irb-approved"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=180,
        )
        assert res.returncode == 0, res.stdout + res.stderr
        assert "⚠ Cox PH thô: " + RSA.DONG_KHONG_HOI_TU in res.stdout, res.stdout
        assert "✓ Cox PH thô" not in res.stdout
        surv_txt = (study_dir / "G6_table3_survival.txt").read_text(encoding="utf-8")
        assert RSA.DONG_KHONG_HOI_TU in surv_txt and "Thô: HR =" not in surv_txt
        summary = json.loads((study_dir / "G6_analysis_summary.json").read_text(encoding="utf-8"))
        crude = summary["survival"]["crude"]
        assert crude.get("khong_hoi_tu") is True and "HR" not in crude
    finally:
        _rmtree_retry(study_dir)
