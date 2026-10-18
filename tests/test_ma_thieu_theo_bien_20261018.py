# -*- coding: utf-8 -*-
"""Mã thiếu THEO TỪNG BIẾN (`_ma-thieu-theo-bien.csv`) — 18/10/2026 (hội đồng G3 C1a, việc sửa 8 của tranh biện
G3-TB-20261017T190638-43914aa7).

Trước đây 998 của `kyvong_thoigiancho` (ngoài khoảng 0–600 của chính trường) thành cờ ngoài khoảng ở mọi phiếu, và
cách lách duy nhất là `--missing-tokens 998` TOÀN CỤC — xoá luôn 998 phút hợp lệ của `thoigian_cho`. Test chốt:
① bộ làm sạch chỉ coi 998 là thiếu ở ĐÚNG cột đã khai; mã «*» áp mọi cột; tệp hỏng ⇒ chặn, không âm thầm bỏ qua;
② script G5 sinh ra miễn mã thiếu của biến khỏi kiểm khoảng nhưng vẫn bắt giá trị ngoài khoảng thật;
③ `_kiem_crf` bắt câu «tối đa N» thiếu `@MAXCHECKED=N` và mã thiếu nằm TRONG khoảng hợp lệ.
Ngoại tuyến, dữ liệu giả, không PII.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import clean_research_dataset as CLEAN  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import run_g5_auto as G5  # noqa: E402

STUDY = "MA-THIEU-THU"
COT = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
       "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
       "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
       "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name",
       "Matrix Ranking?", "Field Annotation"]


def _ma_thieu(out: Path, dong=(("*", "BTR"), ("ky_vong", "998"))) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / "_ma-thieu-theo-bien.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["bien", "ma", "nhan"])
        w.writerows([(b, m, "nhãn") for b, m in dong])
    return p


def _bo_bien(out: Path, *, annotation: str = "@MAXCHECKED=2", ky_vong_max: str = "600") -> None:
    out.mkdir(parents=True, exist_ok=True)
    dong = [
        {"Variable / Field Name": "record_id", "Form Name": "phieu", "Field Type": "text", "Field Label": "Mã phiếu",
         "Required Field?": "y"},
        {"Variable / Field Name": "ky_vong", "Form Name": "phieu", "Field Type": "text",
         "Field Label": "Kỳ vọng (phút)",
         "Text Validation Type OR Show Slider Number": "integer", "Text Validation Min": "0",
         "Text Validation Max": ky_vong_max, "Required Field?": "y"},
        {"Variable / Field Name": "cho", "Form Name": "phieu", "Field Type": "text", "Field Label": "Thời gian chờ",
         "Text Validation Type OR Show Slider Number": "integer", "Text Validation Min": "0",
         "Text Validation Max": "1440"},
        {"Variable / Field Name": "ly_do", "Form Name": "phieu", "Field Type": "checkbox",
         "Field Label": "Lý do (chọn tối đa 2)", "Choices, Calculations, OR Slider Labels": "1, A | 2, B | 3, C",
         "Field Annotation": annotation},
    ]
    with (out / G5.BO_BIEN_RIENG_TEN_FILE).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT)
        w.writeheader()
        w.writerows(dong)


# ── ① bộ làm sạch ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _lam_sach(tmp_path: Path, ma_thieu_path=None) -> dict:
    data = tmp_path / "input.csv"
    data.write_text("record_id,ky_vong,cho,ghi_chu\nP01,998,998,BTR\nP02,30,45,ok\n", encoding="utf-8", newline="\n")
    tu_dien = tmp_path / "dictionary.json"
    tu_dien.write_text(json.dumps({"variables": [
        {"name": "record_id", "type": "text"}, {"name": "ky_vong", "type": "number", "min": 0, "max": 600},
        {"name": "cho", "type": "number", "min": 0, "max": 1440}, {"name": "ghi_chu", "type": "text"}]}),
        encoding="utf-8", newline="\n")
    return CLEAN.clean_dataset(STUDY, data, dictionary_path=tu_dien, exports_root=tmp_path / "exports",
                               ma_thieu_path=ma_thieu_path)


def test_lam_sach_chi_coi_998_la_thieu_o_dung_cot(tmp_path):
    _ma_thieu(tmp_path / "exports" / STUDY)
    rp = _lam_sach(tmp_path)
    assert rp["missing_tokens_by_column"] == {"ky_vong": ["998"]} and rp["ma_thieu_theo_bien_sha256"]
    with open(tmp_path / "exports" / STUDY / rp["clean_dataset_path"], encoding="utf-8") as f:
        p01 = next(r for r in csv.DictReader(f) if r["record_id"] == "P01")
    assert p01["ky_vong"] == "" and p01["cho"] == "998", "998 phút của cột khác là giá trị THẬT"
    assert p01["ghi_chu"] == "", "mã «*» (cấp dự án) áp mọi cột"
    assert not rp["query_summary"].get("range_high"), "998 đã khai là thiếu ⇒ không thành truy vấn ngoài khoảng"


def test_khong_co_tep_thi_giu_hanh_vi_cu(tmp_path):
    rp = _lam_sach(tmp_path)
    assert rp["missing_tokens_by_column"] == {} and rp["ma_thieu_theo_bien_sha256"] is None
    assert rp["query_summary"].get("range_high") == 1, "chưa khai thì 998 vẫn là ngoài khoảng như trước"


def test_tep_ma_thieu_hong_thi_chan(tmp_path):
    p = tmp_path / "hong.csv"
    p.write_text("bien,nhan\nky_vong,x\n", encoding="utf-8", newline="\n")
    rp = _lam_sach(tmp_path, ma_thieu_path=p)
    assert "ma_thieu_theo_bien_invalid" in str(rp.get("blocker") or rp.get("status")) or \
        "ma_thieu_theo_bien_invalid" in json.dumps(rp, ensure_ascii=False)


# ── ② script G5 sinh ra ───────────────────────────────────────────────────────────────────────────────────────────────
def test_g5_nap_ma_thieu_va_tep_hong(tmp_path):
    assert G5.nap_ma_thieu_theo_bien(tmp_path) is None
    _ma_thieu(tmp_path)
    assert G5.nap_ma_thieu_theo_bien(tmp_path) == {"*": ["BTR"], "ky_vong": ["998"]}
    assert G5._ma_thieu_so(G5.nap_ma_thieu_theo_bien(tmp_path)) == repr({"ky_vong": [998.0]})
    (tmp_path / "_ma-thieu-theo-bien.csv").write_text("bien\nky_vong\n", encoding="utf-8", newline="\n")
    with pytest.raises(SystemExit):
        G5.nap_ma_thieu_theo_bien(tmp_path)


def test_script_g5_mien_ma_thieu_khoi_kiem_khoang(tmp_path):
    _bo_bien(tmp_path)
    _ma_thieu(tmp_path)
    rows = G5.nap_bo_bien_rieng(tmp_path, STUDY)
    src = G5.gen_data_cleaning_script(STUDY, "cross_sectional", rows, G5.nap_ma_thieu_theo_bien(tmp_path))
    assert "MISSING_CODES = {'ky_vong': [998.0]}" in src
    ns: dict = {}
    exec(compile(src.split("\nif __name__")[0], "data_cleaning.py", "exec"), ns)  # noqa: S102 — script do G5 sinh
    df = pd.DataFrame({"ky_vong": ["998", "700", "30"], "cho": ["998", "20", "30"]})
    ra = ns["range_validation"](df)
    assert ra["flag_ky_vong"].tolist() == [False, True, False], "998 đã khai là thiếu; 700 vẫn ngoài khoảng"
    assert ra["flag_cho"].tolist() == [False, False, False]
    src_dqr = G5.gen_data_quality_report_script(STUDY, "cross_sectional", rows, G5.nap_ma_thieu_theo_bien(tmp_path))
    assert "MISSING_CODES = {'ky_vong': [998.0]}" in src_dqr and "col_num.mask(col_num.isin(MISSING_CODES" in src_dqr


# ── ③ kiểm máy CRF của G3-T3 ─────────────────────────────────────────────────────────────────────────────────────────
def test_kiem_crf_bat_maxchecked_va_ma_thieu_trong_khoang(tmp_path):
    _bo_bien(tmp_path)
    _ma_thieu(tmp_path)
    assert HD._kiem_crf(tmp_path, STUDY) == []
    _bo_bien(tmp_path, annotation="")
    assert any("@MAXCHECKED" in x and "ly_do" in x for x in HD._kiem_crf(tmp_path, STUDY))
    _bo_bien(tmp_path, ky_vong_max="1000")
    assert any("TRONG khoảng" in x and "ky_vong=998" in x for x in HD._kiem_crf(tmp_path, STUDY))
