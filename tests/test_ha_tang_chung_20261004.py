# -*- coding: utf-8 -*-
"""Hạ tầng dùng chung đợt A (soát từng cổng G0–G10, 04/10/2026):
  • skill_standards.ma_thiet_ke_chuoi — bảng bí danh DUY NHẤT cho 8 mã chuỗi (G1-12); mã lạ ⇒ None (để cổng chặn).
  • skill_standards.dac_ta_thiet_ke — khối đặc tả thiết kế G1 khoá; chưa có khối ⇒ dựng từ gate_params, giá trị chưa
    biết là None + liệt kê ở `thieu` (CHUNG-F: KHÔNG BAO GIỜ mặc định «treatment»/«superiority»).
  • placeholder_contract — token trần «TBD»/«TODO»/«chưa có» không phải nội dung thật (CHUNG-B).
Ngoại tuyến.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import placeholder_contract as PC  # noqa: E402
import skill_standards as SK  # noqa: E402


@pytest.mark.parametrize("raw,ma", [
    ("RCT", "rct"), ("rct_parallel", "rct"), ("Randomised", "rct"), ("case-control", "case_control"),
    ("Cross sectional", "cross_sectional"), ("prevalence", "cross_sectional"), ("systematic-review", "sr_ma"),
    ("meta analysis", "sr_ma"), ("diagnostic_accuracy", "diagnostic"), ("prediction_model", "prediction"),
    ("Qualitative", "qualitative"), ("cohort", "cohort"),
])
def test_ma_thiet_ke_chuoi_nhan_bi_danh(raw, ma):
    assert SK.ma_thiet_ke_chuoi(raw) == ma


@pytest.mark.parametrize("raw", ["quality_improvement", "case_report", "mixed_methods", "non_randomized", "",
                                 None, "economic"])
def test_ma_thiet_ke_chuoi_ma_la_tra_none(raw):
    assert SK.ma_thiet_ke_chuoi(raw) is None


def test_chuan_hoa_khong_bao_gio_mac_dinh():
    assert SK.chuan_hoa_question_type("therapy") == "treatment"
    assert SK.chuan_hoa_question_type("Mô tả") == "descriptive"
    assert SK.chuan_hoa_question_type("xyz") is None and SK.chuan_hoa_question_type(None) is None
    assert SK.chuan_hoa_hypothesis_type("NI") == "non_inferiority"
    assert SK.chuan_hoa_hypothesis_type("non-inferiority") == "non_inferiority"
    assert SK.chuan_hoa_hypothesis_type("precision") == "descriptive_precision"
    assert SK.chuan_hoa_hypothesis_type("") is None and SK.chuan_hoa_hypothesis_type("abc") is None


def _ghi(p: Path, v) -> None:
    p.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")


def test_dac_ta_suy_lai_tu_gate_params_khong_mac_dinh(tmp_path):
    _ghi(tmp_path / "study_meta.json", {"design_code": "Cross sectional", "gate_params": {
        "G0": {"question_type": "mô tả"}, "G3": {"hypothesis_type": "precision"}}})
    dt = SK.dac_ta_thiet_ke(tmp_path)
    assert dt["nguon"] == "suy_lai" and dt["design_code"] == "cross_sectional"
    assert dt["question_type"] == "descriptive" and dt["hypothesis_type"] == "descriptive_precision"
    assert dt["masking"] is None and "masking" in dt["thieu"] and "outcome_direction" in dt["thieu"]
    assert set(SK.DAC_TA_KHOA) <= set(dt)


def test_dac_ta_thu_muc_trong_moi_khoa_la_none(tmp_path):
    dt = SK.dac_ta_thiet_ke(tmp_path)
    assert all(dt[k] is None for k in SK.DAC_TA_KHOA) and sorted(dt["thieu"]) == sorted(SK.DAC_TA_KHOA)


def test_dac_ta_uu_tien_khoi_g1_khoa(tmp_path):
    _ghi(tmp_path / "study_meta.json", {"design_code": "cohort"})
    _ghi(tmp_path / "G1_checkpoint.json", {"dac_ta_thiet_ke": {
        "design_code": "RCT", "question_type": "therapy", "hypothesis_type": "NI", "margin": 0.1,
        "outcome_direction": "lower_better", "masking": "double", "dau_van_tay": "abc"}})
    dt = SK.dac_ta_thiet_ke(tmp_path)
    assert dt["nguon"] == "g1_khoa" and dt["design_code"] == "rct" and dt["question_type"] == "treatment"
    assert dt["hypothesis_type"] == "non_inferiority" and dt["margin"] == 0.1 and dt["dau_van_tay"] == "abc"


def test_huong_ket_cuc_la_bi_loai(tmp_path):
    _ghi(tmp_path / "study_meta.json", {"gate_params": {"G3": {"outcome_direction": "tốt hơn"}}})
    assert SK.dac_ta_thiet_ke(tmp_path)["outcome_direction"] is None


@pytest.mark.parametrize("v", ["TBD", "todo", "Pending", "chưa có", "Điền sau"])
def test_token_tran_khong_phai_noi_dung_that(v):
    assert PC.co_noi_dung_that(v) is False


@pytest.mark.parametrize("v", ["Chưa có nghiên cứu nào tại Việt Nam", "TBD-2026 là mã đề tài", "Pending review 2x"])
def test_cau_co_token_khong_bi_coi_la_rong(v):
    assert PC.co_noi_dung_that(v) is True
