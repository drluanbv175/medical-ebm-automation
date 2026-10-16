"""F14 (diễn tập C1a 16/10/2026): khuôn G6 theo ĐÚNG thiết kế.

- 00_setup.R cài/nạp đúng gói các script 01–03 gọi (C1a cắt ngang thứ bậc từng thiếu `ordinal`, thừa survminer/pROC…).
- Thiết kế không có thời gian-đến-biến-cố nhận tệp Python DẪN ĐƯỜNG (in lệnh đúng, thoát mã 2) thay khuôn Cox+KM.
- Cổng G6 nhận diện tệp dẫn đường (tên + dòng mô tả bộ sinh + không có dòng thi hành đọc dữ liệu); R6 không đòi 95%CI
  cho định tính.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g6_quality_gate as G6Q  # noqa: E402
import run_g6_auto as G6A  # noqa: E402
from test_g6_hoan_thien_20261004 import _de_tai_g6_that  # noqa: E402

_V = {"exposure": "tg_cho", "outcome": "g1", "time_col": None, "covariates": ["tuoi"], "detection_log": [],
      "cluster_col": "ma_ban_kham", "outcome_ordinal": True}
_KHONG_SONG_CON = ("cross_sectional", "diagnostic", "prediction", "sr_ma", "qualitative")


def test_goi_r_doc_tu_script_ca_dong_chu_thich_bo_goi_kem_san():
    goi = G6A.goi_r_cho_script('library(ordinal)\n# fit <- MASS::polr(y ~ x)\nsandwich::vcovCL(f)\n'
                               'stats::lm(y ~ x)\ndplyr::mutate(d)\nrequireNamespace("brant")')
    assert goi[:len(G6A._GOI_R_NEN)] == list(G6A._GOI_R_NEN)
    assert {"ordinal", "MASS", "sandwich", "brant"} <= set(goi)
    assert "stats" not in goi and "dplyr" not in goi, "gói kèm R / lõi tidyverse không liệt kê lại"


#: Hàm gọi trần được phép trong khuôn mà KHÔNG cần khai gói: R gốc + tidyverse/gtsummary (gói nền của 00_setup.R).
_TRAN_DUOC_PHEP = frozenset((
    "Filter I Sys.time across add_p add_smd aggregate all_categorical all_continuous all_of anova any "
    "arrange as.character as.integer as.numeric attr binomial c capture.output cbind coef confint desc "
    "everything exp factor file.path filter fitted format function get get0 ggsave glm globalenv "
    "identical ifelse install.packages installed.packages is.data.frame is.na lapply length library list "
    "lm mean message model.matrix names ncol nrow options paste0 plot poisson predict print prop.test "
    "read.csv readRDS round rowSums saveRDS sessionInfo source sprintf stopifnot sum summarise summary "
    "suppressPackageStartupMessages t.test table unique warning where with write.csv writeLines"
).split())


def test_quet_8_thiet_ke_moi_ham_tran_deu_co_goi():
    """Khuôn G6 thêm hàm gọi trần của gói ngoài mà không khai ở _HAM_TRAN_GOI_R ⇒ 00_setup.R không cài gói đó ⇒ đỏ."""
    v0 = dict(_V, time_col="t", outcome_levels=[1, 2, 3, 4, 5])
    for thiet_ke in ("rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction", "sr_ma",
                     "qualitative"):
        for loai in ("HR", "RR", "OR", "MD", "ARR%", "NI_PROPORTION", "AUC"):
            for thu_bac in (False, True):
                v = dict(v0, outcome_ordinal=thu_bac)
                r03 = G6A.R_ANALYSIS_MAP_FUNC(thiet_ke, v, 100, 0.05, 0.8, 1.5, loai)
                ma = "\n".join([G6A.make_r01_cleaning(v, thiet_ke), G6A.make_r02_tables(v, thiet_ke),
                                G6A.hau_xu_ly_script_r(r03, "S", ("y2",), la_03=True)])
                goi = set(G6A.goi_r_cho_script(ma))
                tran = {m.group(1) for m in re.finditer(r"(?<![:$\w.])([A-Za-z][A-Za-z0-9_.]*)\(", ma)}
                la = sorted(tran - _TRAN_DUOC_PHEP - set(G6A._HAM_TRAN_GOI_R))
                assert not la, f"{thiet_ke}/{loai}: hàm trần chưa biết gói — thêm vào _HAM_TRAN_GOI_R: {la}"
                thieu = sorted({G6A._HAM_TRAN_GOI_R[h] for h in tran & set(G6A._HAM_TRAN_GOI_R)} - goi)
                assert not thieu, f"{thiet_ke}/{loai}: 00_setup.R thiếu gói {thieu}"


def test_setup_nhan_danh_sach_goi_mac_dinh_giu_nguyen():
    moi = G6A.make_r00_setup("S", "2026", alpha=0.05, packages=G6A.goi_r_cho_script("ordinal::clm(y ~ x)"))
    assert '"ordinal"' in moi and '"survminer"' not in moi and '"pROC"' not in moi
    assert '"survminer"' in G6A.make_r00_setup("S", "2026", alpha=0.05), "caller cũ (không truyền gói) giữ danh sách cũ"


@pytest.mark.parametrize("thiet_ke", _KHONG_SONG_CON)
def test_khong_song_con_nhan_tep_dan_duong_khong_cox(thiet_ke):
    for ma, ten in ((G6A.make_run_analysis_cli(_V, 100, "S", thiet_ke, "OR"), "run_analysis_cli.py"),
                    (G6A.make_sensitivity_analysis(_V, "S", thiet_ke), "sensitivity_analysis.py")):
        assert "lifelines" not in ma and "CoxPHFitter" not in ma and "KaplanMeier" not in ma
        assert G6Q._la_tep_dan_duong(ten, ma), "cổng G6 phải nhận ra tệp dẫn đường do bộ sinh tạo"
        r = subprocess.run([sys.executable, "-c", ma], capture_output=True, text=True, timeout=30)
        assert r.returncode == 2 and "03_analysis.R" in r.stdout


def test_cat_ngang_thu_bac_in_lenh_run_stats_dung_bien():
    ma = G6A.make_run_analysis_cli(_V, 100, "S", "cross_sectional", "OR")
    assert "--outcome g1 --outcome-type ordinal --group tg_cho --cot-cum ma_ban_kham" in ma


def test_cohort_van_giu_khuon_cox():
    v = dict(_V, time_col="tg_theo_doi")
    assert "CoxPHFitter" in G6A.make_run_analysis_cli(v, 100, "S", "cohort", "HR")


def test_cong_khong_nhan_nham_script_phan_tich_la_dan_duong():
    ma = G6A.make_run_analysis_cli(_V, 100, "S", "cross_sectional", "OR")
    assert not G6Q._la_tep_dan_duong("phan_tich.py", ma), "đổi tên ⇒ không phải tệp dẫn đường của bộ sinh"
    assert not G6Q._la_tep_dan_duong("run_analysis_cli.py", ma.replace("import sys", "import sys\nimport pandas as pd"))
    assert not G6Q._la_tep_dan_duong("run_analysis_cli.py", ma + "\npd.read_csv('x.csv')\n")
    assert G6Q._la_tep_dan_duong("run_analysis_cli.py", ma + "\n# pd.read_csv('x.csv')\n"), "chú thích không tính"


def test_a7_mo_ta_dung_tep_that_va_goi_r():
    a7 = G6A.generate_artifact("S", "Chủ đề", "cross_sectional", "STROBE", 1000, 0.05, 0.8, 1.5, "OR", "LOCKED",
                               "2026-10-16", "scripts/", dict(_V, covariates=["tuoi"]),
                               goi_r=["tidyverse", "here", "ordinal"])
    assert "tidyverse, here, ordinal" in a7
    assert "**Dẫn đường** — KHÔNG phân tích" in a7 and "lifelines" not in a7
    assert "--outcome-type ordinal --group tg_cho --cot-cum ma_ban_kham" in a7


def test_r6_khong_doi_95ci_cho_dinh_tinh_nhung_van_chan_thiet_ke_khac():
    van_ban = "**Thiết kế:** {} | **Chuẩn báo cáo:** X\nCần bác sĩ kiểm chứng.\n"
    loi_dt, _ = G6A.guardrail(van_ban.format("qualitative"), "")
    loi_ct, _ = G6A.guardrail(van_ban.format("cross_sectional"), "")
    assert not [e for e in loi_dt if e.startswith("R6")]
    assert [e for e in loi_ct if e.startswith("R6")], "thiết kế có suy luận thống kê vẫn phải có 95%CI"


@pytest.mark.parametrize("thiet_ke", ["cross_sectional", "cohort"])
def test_dau_cuoi_main_setup_theo_thiet_ke(tmp_path, monkeypatch, thiet_ke):
    _study, out, _goc = _de_tai_g6_that(tmp_path, monkeypatch, thiet_ke)
    setup = (out / "scripts" / "00_setup.R").read_text(encoding="utf-8")
    cli = (out / "scripts" / "run_analysis_cli.py").read_text(encoding="utf-8")
    r03 = (out / "scripts" / "03_analysis.R").read_text(encoding="utf-8")
    for goi in set(G6A.goi_r_cho_script(r03)):
        assert f'"{goi}"' in setup, f"03_analysis.R dùng {goi} mà 00_setup.R không cài"
    if thiet_ke == "cohort":
        assert "CoxPHFitter" in cli, "thiết kế có trục thời gian giữ khuôn CLI Cox"
    else:
        assert '"survminer"' not in setup and '"survival"' not in setup
        assert G6Q._la_tep_dan_duong("run_analysis_cli.py", cli)
