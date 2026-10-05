# -*- coding: utf-8 -*-
"""Soát từng cổng G0–G10 (04/10/2026) — cổng G6 (script phân tích ↔ SAP đã khoá): khoá hành vi các bản vá G6-01…G6-12.

G6-01 AUTO-01: «G4 đã khoá» = chữ ký sổ cái khớp SAP + G4 chấm trực tiếp PASS — g4_was_locked tự khai không đủ.
G6-02 Đường R có chốt khoá (tools/kiem_khoa_phan_tich.py — cùng hợp đồng khuôn Python); AUTO-08 đòi mọi script đọc dữ
      liệu đi qua chốt (dòng THI HÀNH, không tính chú thích); 01_cleaning.R chỉ đọc dataset đã khoá.
G6-03 Nhóm con chỉ theo SAP §7 (bộ sinh) và soi cả sensitivity_* (bộ chấm); nhãn post-hoc chỉ miễn trừ cùng khối.
G6-04 RCT/cohort kết cục nhị phân (RR/OR/ARR%) không còn sinh Cox; AUTO-09 họ mô hình script ↔ SAP §4; SAP §4 (G4) theo
      effect_type.
G6-05 Alpha của SAP do G4 sinh («- **Alpha (two-sided):** 0.05») đọc được.  G6-06 Mốc khoá = manifest + chữ ký G5.
G6-07 Bộ chấm giữ mốc sinh checkpoint.  G6-08 Kết cục CHÍNH rút riêng, phải trùng biến kết cục script.
G6-09 Bộ sinh lấy seed/alpha/phiên bản R/kết cục phụ/nhóm con TỪ SAP.  G6-10 Xác nhận gắn dấu nội dung script.
G6-11 Ghi phiên bản môi trường (sessionInfo / G6_moi_truong.json).  G6-12 Seed tới 12 chữ số.
Mọi luồng có ký chạy trong pytest với khoá giả tạm (EBM_GATE_KEY_PATH chỉ có hiệu lực dưới pytest). Không PII.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import kiem_khoa_phan_tich as KK  # noqa: E402
import run_g4_auto as G4A  # noqa: E402
import run_g6_auto as G6A  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    configure_test_signing_key,
    ghi_ban_go_bang_tong_hop,
    prepare_locked_g5_study,
)

THIET_KE = ["rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction", "sr_ma", "qualitative"]
RSCRIPT = shutil.which("Rscript")


def _ck(bao: dict, ma: str) -> dict:
    return next(k for k in bao["checks"] if k["id"] == ma)


def _ghi(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _de_tai_g6_that(tmp_path: Path, monkeypatch, thiet_ke: str) -> tuple[str, Path, Path]:
    """Chuỗi THẬT G0→G5 (dữ liệu khoá + G5 ký bằng khoá giả tạm) rồi chạy run_g6_auto.main() thật."""
    configure_test_signing_key(tmp_path, monkeypatch)
    goc = tmp_path / "goc"
    study = f"G6HT-{thiet_ke}"
    out = goc / "exports" / study
    out.mkdir(parents=True)
    _ghi(out / "G1_checkpoint.json", json.dumps({"design_code": thiet_ke}))
    them: dict = {}
    if thiet_ke == "qualitative":
        nguon = _ghi(goc / "nguon.csv", "record_id,transcript_id,age,sex,exposure_var,primary_outcome\n" + "\n".join(
            f"S00{i},T0{i},4{i},{'F' if i % 2 else 'M'},{i // 4},{i % 2}" for i in range(1, 7)) + "\n")
        them = {"extra_text_columns": frozenset({"transcript_id"}),
                "truoc_khi_khoa": lambda d: ghi_ban_go_bang_tong_hop(d, [f"T0{i}" for i in range(1, 7)])}
    else:
        nguon = _ghi(goc / "nguon.csv", "record_id,age,sex,exposure_var,primary_outcome\n" + "\n".join(
            f"S00{i},4{i},{'F' if i % 2 else 'M'},{i // 4},{i % 2}" for i in range(1, 7)) + "\n")
    prepare_locked_g5_study(study, nguon, exports_root=goc / "exports", repo_root=goc, **them)
    CS.xoa_dem()
    monkeypatch.setattr(G6A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g6_auto.py", "--study", study])
    with contextlib.redirect_stdout(io.StringIO()):
        G6A.main()
    CS.xoa_dem()
    return study, out, goc


# ── CHUNG-H: chuỗi đầu–cuối G0→G6 cho 8 thiết kế ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("thiet_ke", THIET_KE)
def test_chung_h_dau_cuoi_g6_8_thiet_ke_toi_ready_va_xac_nhan_gan_dau(tmp_path, monkeypatch, thiet_ke):
    study, out, goc = _de_tai_g6_that(tmp_path, monkeypatch, thiet_ke)
    bao = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    chua = [(k["id"], k["pass"], k["detail"][:120]) for k in bao["checks"]
            if k["pass"] is not True and k["id"] != "G6-HUMAN-01"
            and not (thiet_ke == "qualitative" and k["id"] in ("G6-AUTO-02", "G6-AUTO-03"))]
    assert bao["status"] == "READY_FOR_STATISTICIAN_REVIEW", chua
    assert _ck(bao, "G6-AUTO-01")["pass"] is True, "G4 khoá THẬT (sổ cái + G4 chấm trực tiếp)"
    assert _ck(bao, "G6-AUTO-08")["pass"] is True and _ck(bao, "G6-AUTO-09")["pass"] is True
    setup = (out / "scripts" / "00_setup.R").read_text(encoding="utf-8")
    if thiet_ke == "qualitative":
        assert "SEED <- NA   # SAP §10: seed KHÔNG ÁP DỤNG" in setup and "alpha KHÔNG ÁP DỤNG" in setup
    else:
        assert "SEED <- 20261004" in setup, "seed lấy TỪ SAP §10 (bản cũ cứng 2026)"
    assert "kiem_khoa_phan_tich.py" in setup and 'here::here("data", "raw")' not in setup
    for tep in ("01_cleaning.R", "02_tables.R", "03_analysis.R"):
        assert f'source(here::here("exports", "{study}", "scripts", "00_setup.R"))' in \
            (out / "scripts" / tep).read_text(encoding="utf-8")
    r03 = (out / "scripts" / "03_analysis.R").read_text(encoding="utf-8")
    if 'readRDS(file.path(DATA_PROC, "df_clean.rds"))' in r03:  # SR/MA (bảng trích xuất) và định tính không đọc RDS
        assert 'identical(attr(df, "sha256_khoa"), LOCKED_SHA)' in r03, "RDS phải đối chiếu sha256 dataset khoá"
    assert "- [x] **G4 SAP đã khoá THẬT**" in (out / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").read_text(encoding="utf-8")

    # G6-10: xác nhận gắn dấu ⇒ PASS; sửa script sau xác nhận ⇒ hết hiệu lực.
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta.setdefault("gate_params", {})["G6"] = {
        "scripts_match_sap_confirmed": True, "reviewed_by_role": "STATISTICIAN",
        "reviewed_at": datetime.now().date().isoformat(), "dau_van_tay_chot": G6Q.dau_van_tay_script(out, study)}
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    assert G6Q.evaluate_study(study, out, write=False, repo_root=goc)["status"] == "PASS_G6_SCRIPTS_CONFIRMED"
    p03 = out / "scripts" / "03_analysis.R"
    _ghi(p03, p03.read_text(encoding="utf-8") + "\n# sửa sau khi thống kê viên xác nhận\n")
    sau = G6Q.evaluate_study(study, out, write=False, repo_root=goc)
    assert sau["status"] != "PASS_G6_SCRIPTS_CONFIRMED" and "dau_van_tay_chot" in _ck(sau, "G6-HUMAN-01")["detail"]


@pytest.mark.skipif(RSCRIPT is None, reason="máy không có Rscript")
def test_moi_script_r_sinh_ra_phan_tich_cu_phap_duoc_va_chot_khoa_chay_that(tmp_path, monkeypatch):
    """Lộ 04/10/2026: 01_cleaning.R của MỌI đề tài từng lỗi cú pháp R (khối mutate không chú thích). Đồng thời chạy
    khối chốt khoá của 00_setup.R bằng R THẬT: đề tài đã khoá ⇒ nhận LOCKED_DATA; đề tài chưa khoá ⇒ stop()."""
    study, out, goc = _de_tai_g6_that(tmp_path, monkeypatch, "cohort")
    tep_r = sorted(str(p) for p in (out / "scripts").glob("*.R"))
    kq = subprocess.run([RSCRIPT, "-e", "for (f in commandArgs(TRUE)) invisible(parse(file = f)); cat('OK')", *tep_r],
                        capture_output=True, text=True, timeout=120)
    assert kq.returncode == 0 and "OK" in kq.stdout, kq.stderr[-800:]

    setup = (out / "scripts" / "00_setup.R").read_text(encoding="utf-8")
    khoi = setup[setup.index("# ---- CHỐT DATA LOCK"):setup.index("DATA_PROC <- ")]
    khoi = khoi.replace('"--study", STUDY)', '"--study", STUDY, "--repo-root", REPO_EXPORTS)')
    chay = _ghi(tmp_path / "chay_khoa.R", (
        "args <- commandArgs(TRUE)\nSTUDY <- args[1]; REPO <- args[2]; REPO_EXPORTS <- args[3]\n"
        f"Sys.setenv(EBM_PYTHON = '{sys.executable}')\n"
        "kq <- tryCatch({\n" + khoi + "\npaste('OK', basename(LOCKED_DATA))\n}, error = function(e) "
        "paste('STOP', conditionMessage(e)))\ncat(kq, '\\n')\n"))
    env = dict(os.environ)  # có PYTEST_CURRENT_TEST + EBM_GATE_KEY_PATH (khoá giả) ⇒ công cụ con dùng khoá giả
    da_khoa = subprocess.run([RSCRIPT, str(chay), study, str(REPO_ROOT), str(goc)], capture_output=True, text=True,
                             timeout=180, env=env)
    assert da_khoa.stdout.strip().startswith("OK") and ".locked.csv" in da_khoa.stdout, da_khoa.stdout + da_khoa.stderr
    _ghi(goc / "exports" / "G6HT-CHUA-KHOA" / "G1_checkpoint.json", "{}")
    chua_khoa = subprocess.run([RSCRIPT, str(chay), "G6HT-CHUA-KHOA", str(REPO_ROOT), str(goc)], capture_output=True,
                               text=True, timeout=180, env=env)
    assert chua_khoa.stdout.strip().startswith("STOP") and "G4_chua" in chua_khoa.stdout, chua_khoa.stdout


# ── G6-02: công cụ chốt khoá + AUTO-08 ────────────────────────────────────────────────────────────────────────────────

def test_g6_02_cong_cu_chot_khoa_chan_de_tai_chua_ky_va_cho_de_tai_da_khoa(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g6_that(tmp_path, monkeypatch, "cross_sectional")
    ly_do, tep, sha = KK.kiem(study, repo_root=goc)
    assert ly_do == [] and tep is not None and tep.name.endswith(".locked.csv") and sha
    # CSV khác bản khoá ⇒ chặn (chống phân tích trên dữ liệu đã cắt gọt)
    khac = _ghi(tmp_path / "khac.csv", tep.read_text(encoding="utf-8") + "S999,99,F,1,1\n")
    assert "provided_data_is_not_locked_dataset" in KK.kiem(study, str(khac), repo_root=goc)[0]
    monkeypatch.setattr(KK.GC, "g4_quality_contract_satisfied", lambda *a, **k: False)
    assert "G4_chua_PASS_G4_SAP_LOCKED" in KK.kiem(study, repo_root=goc)[0]
    monkeypatch.undo()
    _ghi(goc / "exports" / "CHUA-KY" / "G1_checkpoint.json", "{}")
    ly_do2, tep2, _ = KK.kiem("CHUA-KY", repo_root=goc)
    assert tep2 is None and any(x.startswith("G2_chua") for x in ly_do2)
    assert any(x.startswith("G4_chua") for x in ly_do2)
    assert "missing_DATA_LOCK_manifest" in ly_do2


def _de_tai_tay(tmp_path: Path, scripts: dict, sap_them: str = "", cp: dict | None = None) -> Path:
    d = tmp_path / "TAY"
    _ghi(d / "G4_A5_SAP_FINAL_TAY.md", (
        "# SAP\n\n### §2 Kết cục\nKết cục chính: `diem` (thang 5 mức).\n\n"
        "### §4 Phân tích chính\nHồi quy tuyến tính (lm).\n\n### §7 Nhóm con\nKhông có phân tích nhóm con.\n\n"
        "### §10 Phần mềm\nR 4.4.1. Seed: set.seed(2026)\n\n### §12 Ngưỡng\nAlpha: 0.05 hai phía.\n" + sap_them))
    _ghi(d / "G6_A7_ANALYSIS_SCRIPTS_TAY.md", "**Phân tích chính:** Hồi quy tuyến tính\n")
    _ghi(d / "G6_checkpoint.json", json.dumps(cp or {"variables_detected": {"outcome": "diem"}}))
    for ten, nd in scripts.items():
        _ghi(d / "scripts" / ten, nd)
    return d


_R_DUOC = "SEED <- 2026\nset.seed(SEED)\nalpha <- 0.05\nfit <- lm(diem ~ tuoi, data = d)\n" \
          "writeLines(capture.output(sessionInfo()), 'session_info.txt')\n"


@pytest.fixture()
def g4_khoa_gia(monkeypatch):
    monkeypatch.setattr(G6Q, "_g4_da_khoa", lambda *a, **k: (True, "giả lập: sổ cái + G4 PASS_G4_SAP_LOCKED"))


@pytest.mark.parametrize(("scripts", "thieu"), [
    ({"00_setup.R": _R_DUOC, "03_analysis.R": "# df <- readRDS('x.rds')\n" + _R_DUOC}, "không nạp 00_setup.R"),
    ({"00_setup.R": _R_DUOC + "# system2(PY, 'tools/kiem_khoa_phan_tich.py'); stop('x')\n",
      "03_analysis.R": ("source(here::here('exports', 'TAY', 'scripts', '00_setup.R'))\n# df <- readRDS('x')\n"
                        + _R_DUOC)},
     "00_setup.R không gọi"),
    ({"cli.py": "import sys\ndef main():\n    df = pd.read_csv(args.data)\n    print(sys.version)\n"},
     "không gọi _check_sap_db_locked"),
])
def test_g6_02_auto08_script_doc_du_lieu_khong_qua_chot_thi_block(tmp_path, g4_khoa_gia, scripts, thieu):
    bao = G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path, scripts), write=False)
    c = _ck(bao, "G6-AUTO-08")
    assert c["pass"] is False and thieu in c["detail"] and bao["status"] == "BLOCKED", c


def test_g6_01_chu_ky_g4_co_nhung_g4_khong_locked_thi_auto01_khong_dat(tmp_path, monkeypatch):
    import gate_contract as GC
    monkeypatch.setattr(GC, "ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(GC, "g4_quality_contract_satisfied", lambda *a, **k: False)
    c = _ck(G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path, {"01.R": _R_DUOC}), write=False), "G6-AUTO-01")
    assert c["pass"] is False and "PASS_G4_SAP_LOCKED" in c["detail"], c


def test_g6_01_tu_khai_g4_was_locked_khong_con_du(tmp_path):
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC}, cp={"g4_was_locked": True, "variables_detected": {"outcome": "diem"}})
    c = _ck(G6Q.evaluate_study("TAY", d, write=False), "G6-AUTO-01")
    assert c["pass"] is None and "TỰ KHAI" in c["detail"]
    d2 = _de_tai_tay(tmp_path / "b", {"01.R": _R_DUOC})
    bao2 = G6Q.evaluate_study("TAY", d2, write=False)
    assert _ck(bao2, "G6-AUTO-01")["pass"] is False and bao2["status"] == "BLOCKED"


# ── G6-03 nhóm con ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_g6_03_nhom_con_ngoai_sap_trong_sensitivity_bi_bat_nhan_o_tep_khac_khong_mien(tmp_path, g4_khoa_gia):
    sens = "for sg in ['sex', 'dm', 'htn']:\n    pass\nAGE_CUT = 70\n"
    bao = G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path, {"01.R": _R_DUOC, "sensitivity_analysis.py": sens,
                                                        "khac.R": "# exploratory\n" + _R_DUOC}), write=False)
    c = _ck(bao, "G6-AUTO-05")
    assert c["pass"] is False and "sex" in c["detail"] and "age" in c["detail"], c
    # nhãn post-hoc CÙNG khối thì miễn trừ; đối số từ khoá «Subgroup=» (nhãn cột kết quả) không phải lời khai biến
    sens_nhan = "# THĂM DÒ post-hoc — ngoài SAP §7\nfor sg in ['sex']:\n    rows.append(dict(Subgroup=sg))\n"
    bao2 = G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path / "b", {"01.R": _R_DUOC,
                                                                 "sensitivity_analysis.py": sens_nhan}), write=False)
    assert _ck(bao2, "G6-AUTO-05")["pass"] is True
    xa = "# exploratory\n" + "x = 1\n" * 5 + "for sg in ['sex']:\n    pass\n"
    bao3 = G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path / "c", {"01.R": _R_DUOC, "sensitivity_analysis.py": xa}),
                              write=False)
    assert _ck(bao3, "G6-AUTO-05")["pass"] is False, "nhãn ở xa (khác khối) không miễn trừ"


def test_g6_03_bo_sinh_lay_nhom_con_va_nguong_tuoi_tu_sap():
    sap = "### §7 Nhóm con\n- **Nhóm nhỏ tiền định:** `gioi_tinh`, `nhom_benh`; theo tuổi <65/≥65\n"
    ts = G6A.doc_tham_so_sap(sap, ["gioi_tinh", "tuoi"])
    assert ts["nhom_con"] == ["gioi_tinh"] and ts["nguong_tuoi"] == 65, "chỉ nhận biến có trong dictionary"
    v = {"exposure": "e", "outcome": "o", "time_col": "t", "covariates": ["tuoi"], "detection_log": [],
         "nhom_con_sap": ts["nhom_con"], "nguong_tuoi_sap": ts["nguong_tuoi"]}
    code = G6A.make_sensitivity_analysis(v, "S", "cohort", "HR")
    assert "for sg in ['gioi_tinh']:" in code and "AGE_CUT = 65" in code and "MI-demo" not in code
    rong = G6A.make_sensitivity_analysis(dict(v, nhom_con_sap=[], nguong_tuoi_sap=None), "S", "cohort", "HR")
    assert "for sg in []:" in rong and "AGE_CUT = None" in rong


# ── G6-04 kết cục nhị phân + họ mô hình ───────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("effect_type", "ho"), [("HR", "cox"), ("RR", "poisson"), ("OR", "logistic"),
                                                 ("ARR%", "risk_diff"), ("MD", "linear")])
@pytest.mark.parametrize("thiet_ke", ["rct", "cohort"])
def test_g6_04_script_va_sap_g4_cung_ho_mo_hinh_theo_effect_type(thiet_ke, effect_type, ho):
    v = {"exposure": "nhom", "outcome": "bien_co", "time_col": "tg", "covariates": ["tuoi"], "detection_log": []}
    r03 = G6A.R_ANALYSIS_MAP_FUNC(thiet_ke, v, 100, 0.05, 0.8, 1.5, effect_type)
    assert G6Q._ho_mo_hinh_script(r03)[0] == ho
    sap = G4A.generate("S", "Chủ đề", thiet_ke, thiet_ke, "CONSORT 2025", 100, 0.05, 0.8, 1.5, effect_type,
                       "2026-10-04")
    assert ho in G6Q._ho_mo_hinh_sap(G6Q._sec(sap, 4)), "SAP §4 (G4) phải nêu đúng họ mô hình theo effect_type"
    assert G6A._is_cox_like(thiet_ke, effect_type) is (effect_type == "HR")
    if effect_type in G6A._KET_CUC_NHI_PHAN:
        assert "coxph" not in r03 and "Surv(" not in r03
        assert "[CẦN CHÚ Ý — KẾT CỤC NHỊ PHÂN" in G6A.make_run_analysis_cli(v, 100, "S", thiet_ke, effect_type)


def test_g6_04_auto09_cox_trong_khi_sap_khoa_poisson_thi_block(tmp_path, g4_khoa_gia):
    sap_poisson = "### §4 Phân tích chính\nHồi quy Poisson với sai số chuẩn robust → RR.\n"
    r_cox = _R_DUOC.replace("fit <- lm(diem ~ tuoi, data = d)", "fit <- coxph(Surv(t, diem) ~ nhom, data = d)")
    d = _de_tai_tay(tmp_path, {"03_analysis.R": r_cox})
    d.joinpath("G4_A5_SAP_FINAL_TAY.md").write_text(
        d.joinpath("G4_A5_SAP_FINAL_TAY.md").read_text(encoding="utf-8").replace(
            "### §4 Phân tích chính\nHồi quy tuyến tính (lm).\n", sap_poisson), encoding="utf-8", newline="\n")
    c = _ck(G6Q.evaluate_study("TAY", d, write=False), "G6-AUTO-09")
    assert c["pass"] is False and "cox" in c["detail"], c


def test_g6_04_logistic_thu_tu_khong_cho_qua_logistic_nhi_phan():
    assert G6Q._ho_mo_hinh_sap("Hồi quy logistic thứ tự (proportional odds), cOR") == {"ordinal"}
    assert "logistic" in G6Q._ho_mo_hinh_sap("Hồi quy logistic thứ tự; độ nhạy: logistic nhị phân gộp mức")


def test_g6_04_sap_khong_neu_ho_mo_hinh_thi_draft(tmp_path, g4_khoa_gia):
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC})
    p = d / "G4_A5_SAP_FINAL_TAY.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Hồi quy tuyến tính (lm).", "Theo đề cương."), encoding="utf-8",
                 newline="\n")
    bao = G6Q.evaluate_study("TAY", d, write=False)
    assert _ck(bao, "G6-AUTO-09")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


# ── G6-05 / G6-12: alpha và seed của SAP do G4 sinh ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dong", ["- **Alpha (two-sided):** 0.05  ", "- **Alpha (one-sided):** 0.025  ",
                                  "- **Alpha (two-sided):** 0.05, độ tin cậy 95%  "])
def test_g6_05_doc_alpha_dinh_dang_g4(dong):
    assert G6Q.doc_alpha_sap(f"### §12 NGƯỠNG\n\n{dong}\n") in (0.05, 0.025)


def test_g6_05_khong_doc_duoc_alpha_khuyen_ky_lai_khong_sua_tay(tmp_path, g4_khoa_gia):
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC})
    p = d / "G4_A5_SAP_FINAL_TAY.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Alpha: 0.05 hai phía.", "Ngưỡng: như đề cương."),
                 encoding="utf-8", newline="\n")
    c = _ck(G6Q.evaluate_study("TAY", d, write=False), "G6-AUTO-03")
    assert c["pass"] is None and "SAP AMENDMENT" in c["detail"] and "approve_gate" in c["detail"]


def test_g6_12_seed_8_chu_so_khong_bi_cat():
    assert G6Q.doc_seed_sap("- **Seed:** 20260830") == "20260830"
    assert G6Q.doc_seed_sap("set.seed(20260830)") == "20260830"
    assert G6Q.doc_seed_sap("Seed: [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]") is None


# ── G6-06 mốc khoá ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_g6_06_ket_qua_truoc_moc_khoa_thi_block_va_mtime_khong_tin_duoc_thi_draft(tmp_path, g4_khoa_gia, monkeypatch):
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC})
    kq = _ghi(d / "06_ket_qua" / "G6_results_main.xlsx", "x")
    _ghi(d / "DATA_LOCK_manifest.json", json.dumps({"status": "LOCKED_FOR_ANALYSIS", "locked_at": (
        datetime.now() + timedelta(hours=1)).isoformat(timespec="seconds")}))
    monkeypatch.setattr(G6Q, "_g5_da_khoa", lambda s, t, r: (True, json.loads(
        (t / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))))
    c = _ck(G6Q.evaluate_study("TAY", d, write=False), "G6-AUTO-06")
    assert c["pass"] is False and kq.name in c["detail"], "kết quả G6 CLI (06_ket_qua) nay được thấy"
    _ghi(d / "DATA_LOCK_manifest.json", json.dumps({"status": "LOCKED_FOR_ANALYSIS", "locked_at": (
        datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")}))
    import pipeline_freshness as PF
    monkeypatch.setattr(PF, "mtime_khong_tin_duoc", lambda out_dir: "mtime dàn phẳng (giả lập)")
    bao = G6Q.evaluate_study("TAY", d, write=False)
    assert _ck(bao, "G6-AUTO-06")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


# ── G6-07 giữ mốc sinh ────────────────────────────────────────────────────────────────────────────────────────────────

def test_g6_07_bo_cham_khong_lam_moi_mtime_checkpoint(tmp_path, g4_khoa_gia):
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC})
    cp = d / "G6_checkpoint.json"
    cu = datetime(2026, 1, 1).timestamp()
    os.utime(cp, (cu, cu))
    G6Q.evaluate_study("TAY", d, write=True)
    assert "quality_gate" in json.loads(cp.read_text(encoding="utf-8"))
    assert abs(cp.stat().st_mtime - cu) < 1, "mtime checkpoint phải giữ mốc sinh"


# ── G6-08 kết cục chính ───────────────────────────────────────────────────────────────────────────────────────────────

def test_g6_08_ket_cuc_chinh_rut_tu_ngoac_va_phai_trung_bien_script(tmp_path, g4_khoa_gia):
    assert G6Q.ket_cuc_chinh_sap("- **Kết cục chính:** hài lòng chung (biến SHLNBChung_TrucTiep, 5 mức)") == \
        "shlnbchung_tructiep"
    assert G6Q.ket_cuc_chinh_sap("Kết cục chính: hài lòng chung của người bệnh") is None
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC.replace("diem", "diem_hai_long") + "# diem\n"},
                    cp={"variables_detected": {"outcome": "diem_hai_long"}})
    c = _ck(G6Q.evaluate_study("TAY", d, write=False), "G6-AUTO-04")
    assert c["pass"] is False and "kết cục CHÍNH" in c["detail"], c
    d2 = _de_tai_tay(tmp_path / "b", {"01.R": _R_DUOC})
    p = d2 / "G4_A5_SAP_FINAL_TAY.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Kết cục chính: `diem` (thang 5 mức).",
                                                       "Kết cục chính: mức hài lòng chung."), encoding="utf-8",
                 newline="\n")
    bao = G6Q.evaluate_study("TAY", d2, write=False)
    assert _ck(bao, "G6-AUTO-04")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"


# ── G6-09 bộ sinh theo SAP ────────────────────────────────────────────────────────────────────────────────────────────

def test_g6_09_bo_sinh_lay_tham_so_tu_sap():
    sap = ("### §2 KẾT CỤC\n- **Kết cục chính:** `diem_chung`\n- **Kết cục phụ:** `diem_a`, `diem_b`\n\n"
           "### §10 PHẦN MỀM + SEED\n- **Phần mềm:** R ≥ 4.3\n- **Random seed:** set.seed(20260830)\n\n"
           "### §12 NGƯỠNG\n- **Alpha (two-sided):** 0.05  \n")
    ts = G6A.doc_tham_so_sap(sap)
    assert (ts["seed"], ts["alpha"], ts["r_version"], ts["ket_cuc_chinh"], ts["ket_cuc_phu"]) == \
        ("20260830", 0.05, "4.3", "diem_chung", ["diem_a", "diem_b"])
    setup = G6A.make_r00_setup("S", ts["seed"], r_version=ts["r_version"], alpha=ts["alpha"])
    assert "SEED <- 20260830" in setup and "ALPHA <- 0.05" in setup and 'getRversion() < "4.3"' in setup
    chua = G6A.make_r00_setup("S")
    assert "[CẦN SEED THEO SAP §10]" in chua and "stop(" in chua
    r03 = G6A.hau_xu_ly_script_r('source(here::here("scripts", "00_setup.R"))\n', "S", ["diem_a", "diem_b"], la_03=True)
    assert 'source(here::here("exports", "S", "scripts", "00_setup.R"))' in r03
    assert "# Kết cục phụ: diem_a" in r03 and "sessionInfo()" in r03


def test_g6_09_seed_sap_chua_chot_thi_g6_draft(tmp_path, g4_khoa_gia):
    setup = G6A.make_r00_setup("TAY", alpha=0.05)   # alpha đã khoá — CHỈ còn seed chưa chốt
    bao = G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path, {"00_setup.R": setup, "01.R": _R_DUOC}), write=False)
    c = _ck(bao, "G6-AUTO-07")
    assert c["pass"] is None and "SEED THEO SAP" in c["detail"], c
    assert bao["status"] in ("DRAFT_NEEDS_HUMAN_PARAMETERS", "BLOCKED")
    alpha_chua = G6A.make_r00_setup("TAY", seed="2026")
    c2 = _ck(G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path / "b", {"00_setup.R": alpha_chua, "01.R": _R_DUOC}),
                                write=False), "G6-AUTO-07")
    assert c2["pass"] is None and "ALPHA THEO SAP" in c2["detail"], c2


# ── G6-10 xác nhận gắn dấu ────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(("ghi_de", "ly_do"), [
    ({"reviewed_at": "2999-01-01"}, "reviewed_at"),
    ({"reviewed_at": "2020-01-01"}, "sớm hơn ngày sinh script"),
    ({"dau_van_tay_chot": "0" * 16}, "dau_van_tay_chot"),
    ({"reviewed_by_role": "PI_ASSISTANT"}, "reviewed_by_role"),
])
def test_g6_10_xac_nhan_khong_hop_le_thi_khong_pass(tmp_path, g4_khoa_gia, ghi_de, ly_do):
    d = _de_tai_tay(tmp_path, {"01.R": _R_DUOC},
                    cp={"run_date": "2026-10-04", "variables_detected": {"outcome": "diem"}})
    g6 = {"scripts_match_sap_confirmed": True, "reviewed_by_role": "STATISTICIAN", "reviewed_at": "2026-10-05",
          "dau_van_tay_chot": G6Q.dau_van_tay_script(d, "TAY")}
    _ghi(d / "study_meta.json", json.dumps({"gate_params": {"G6": g6}}))
    assert G6Q.evaluate_study("TAY", d, write=False)["status"] == "PASS_G6_SCRIPTS_CONFIRMED"
    _ghi(d / "study_meta.json", json.dumps({"gate_params": {"G6": {**g6, **ghi_de}}}))
    bao = G6Q.evaluate_study("TAY", d, write=False)
    assert bao["status"] != "PASS_G6_SCRIPTS_CONFIRMED" and ly_do in _ck(bao, "G6-HUMAN-01")["detail"]


# ── G6-11 phiên bản môi trường ────────────────────────────────────────────────────────────────────────────────────────

def test_g6_11_khong_ghi_phien_ban_moi_truong_thi_draft(tmp_path, g4_khoa_gia):
    bao = G6Q.evaluate_study("TAY", _de_tai_tay(tmp_path, {"01.R": _R_DUOC.replace(
        "writeLines(capture.output(sessionInfo()), 'session_info.txt')\n", "")}), write=False)
    assert _ck(bao, "G6-AUTO-10")["pass"] is None and bao["status"] == "DRAFT_NEEDS_HUMAN_PARAMETERS"
    v = {"exposure": "e", "outcome": "o", "time_col": "t", "covariates": [], "detection_log": []}
    cli = G6A.make_run_analysis_cli(v, 10, "S", "cohort", "HR")
    assert "ghi_moi_truong(out_dir)" in cli and 'default="exports/S/06_ket_qua"' in cli


# ── Tiêu thụ G4: Bảng 1 RCT không kiểm định khác biệt nền ─────────────────────────────────────────────────────────────

def test_bang1_rct_khong_kiem_dinh_khac_biet_nen():
    import pandas as pd
    df = pd.DataFrame({"nhom": [0, 0, 0, 1, 1, 1], "tuoi": [40, 50, 60, 45, 55, 65], "nam": [1, 0, 1, 0, 1, 0]})
    rct = RSA.table1_descriptive(df, "nhom", ["tuoi", "nam"], kiem_dinh_nen=False)
    assert all("p" not in r and "CONSORT" in r["test"] for r in rct["rows"])
    qs = RSA.table1_descriptive(df, "nhom", ["tuoi", "nam"])
    assert any("p" in r for r in qs["rows"]), "thiết kế khác giữ kiểm định như cũ"
