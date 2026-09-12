"""Hồi quy 5 phát hiện của Workflow đối kháng đa-agent vòng 2 (2026-09-03) trong
tools/run_stats_analysis.py — mọi phát hiện đều cùng một họ lỗi: dữ liệu THIẾU/
KHÔNG HỮU HẠN ở mức độ cực đoan (một nhóm 100% missing, một giá trị Inf, dataset
rỗng) không được guard, khiến pipeline SẬP GIỮA CHỪNG (mất luôn các bảng đã tính
được trước đó) hoặc ÂM THẦM cho ra kết quả sai/loại bỏ dữ liệu mà không cảnh báo.

  #1 CRITICAL — compare_primary_outcome() nhánh binary: ZeroDivisionError khi một
     nhóm có kết cục chính thiếu 100% (mất dấu theo dõi toàn bộ 1 nhánh).
  #2 HIGH — table1_descriptive() nhánh binary: ValueError max() rỗng khi một biến
     nền thiếu 100% ở một nhóm.
  #3 HIGH — Inf âm thầm biến MD/CI/p thành inf/nan không cảnh báo; JSON đầu ra
     chứa token Infinity/NaN không chuẩn RFC 8259.
  #4 MEDIUM — analyze_missingness() ném ZeroDivisionError trên dataset rỗng.
  #5 MEDIUM — kaplan_meier_summary() âm thầm loại bỏ một nhánh nghiên cứu khỏi
     báo cáo KM khi nhánh đó thiếu 100% dữ liệu time/event.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))
import run_stats_analysis as RSA  # noqa: E402

# ── #1 CRITICAL: compare_primary_outcome() binary, một nhóm n=0 ────────────────


class TestPrimaryOutcomeBinaryEmptyGroup:
    def test_group_zero_all_missing_returns_error_not_crash(self):
        df = pd.DataFrame({
            "group": [0] * 15 + [1] * 15,
            "outcome": [None] * 15 + ([1, 0] * 7 + [1]),
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" in res
        assert "n=0" in res["error"] or "0" in res["error"]
        assert "note" in res

    def test_group_one_all_missing_returns_error_not_crash(self):
        df = pd.DataFrame({
            "group": [0] * 15 + [1] * 15,
            "outcome": ([1, 0] * 7 + [1]) + [None] * 15,
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" in res

    def test_normal_binary_case_unaffected(self):
        """Đối chứng: trường hợp bình thường (cả hai nhóm đủ dữ liệu) không đổi hành vi."""
        rng = np.random.default_rng(42)
        df = pd.DataFrame({
            "group": [0] * 40 + [1] * 40,
            "outcome": list(rng.integers(0, 2, 40)) + list(rng.integers(0, 2, 40)),
        })
        res = RSA.compare_primary_outcome(df, "outcome", "group", outcome_type="binary")
        assert "error" not in res
        assert res["group_0"]["n"] == 40
        assert res["group_1"]["n"] == 40

    def test_format_outcome_text_handles_error_gracefully(self):
        res = {"error": "test error", "note": "[CẦN...]"}
        txt = RSA.format_outcome_text(res, "outcome")
        assert "LỖI" in txt
        assert "test error" in txt


# ── #2 HIGH: table1_descriptive() binary, một nhóm 0 quan sát ──────────────────


class TestTable1BinaryEmptyGroup:
    def test_binary_var_all_missing_in_one_group_no_crash(self):
        df = pd.DataFrame({
            "group": [0] * 20 + [1] * 20,
            "sex_male": [1, 0] * 10 + [None] * 20,
        })
        t1 = RSA.table1_descriptive(df, "group", ["sex_male"])
        row = t1["rows"][0]
        assert row["grp_0"] != "N/A (0 quan sát)"
        assert row["grp_1"] == "N/A (0 quan sát)"

    def test_normal_binary_var_unaffected(self):
        df = pd.DataFrame({
            "group": [0] * 20 + [1] * 20,
            "sex_male": ([1, 0] * 10) + ([0, 1] * 10),
        })
        t1 = RSA.table1_descriptive(df, "group", ["sex_male"])
        row = t1["rows"][0]
        assert "N/A" not in row["grp_0"]
        assert "N/A" not in row["grp_1"]


# ── #3 HIGH: Inf không bị lọc, làm hỏng thống kê + JSON ─────────────────────────


class TestInfHandling:
    def test_compare_continuous_drops_inf_and_warns(self):
        a = pd.Series([1.0, 2.0, np.inf, 3.0, 4.0, 5.0])
        b = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5, 6.5])
        r = RSA._compare_continuous(a, b)
        assert np.isfinite(r["p"]) if r["p"] is not None else True
        assert "inf" not in r["effect"].lower() or "warning" in r
        assert r.get("warning") is not None
        assert "1" in r["warning"]

    def test_compare_primary_outcome_continuous_with_inf_flags_warning(self):
        rng = np.random.default_rng(1)
        df = pd.DataFrame({
            "group": [0] * 30 + [1] * 30,
            "age": [10.0] * 29 + [np.inf] + list(rng.normal(12, 2, 30)),
        })
        res = RSA.compare_primary_outcome(df, "age", "group", outcome_type="continuous")
        assert np.isfinite(res["group_0"]["mean"])
        assert np.isfinite(res["group_0"]["sd"])
        assert np.isfinite(res["md_crude"])
        assert res.get("data_quality_warning") is not None
        assert res["group_0"]["n"] == 29  # Inf đã bị loại khỏi n

    def test_table1_continuous_with_inf_flags_warning_in_cell(self):
        rng = np.random.default_rng(2)
        df = pd.DataFrame({
            "group": [0] * 20 + [1] * 20,
            "bmi": [22.0] * 19 + [np.inf] + list(rng.normal(23, 3, 20)),
        })
        t1 = RSA.table1_descriptive(df, "group", ["bmi"])
        row = t1["rows"][0]
        assert "⚠loại 1 giá trị Inf" in row["grp_0"]
        assert "inf" not in row["grp_0"].lower().replace("⚠loại 1 giá trị inf", "")

    def test_json_safe_sanitizes_inf_and_nan_to_null(self):
        payload = {
            "mean": float("inf"),
            "sd": float("nan"),
            "md": float("-inf"),
            "ok": 1.5,
            "nested": {"x": np.float64("inf")},
        }
        safe = RSA._json_safe(payload)
        text = json.dumps(safe, allow_nan=False)  # RFC 8259 nghiêm ngặt — ném lỗi nếu còn NaN/Infinity
        assert safe["mean"] is None
        assert safe["sd"] is None
        assert safe["md"] is None
        assert safe["ok"] == 1.5
        assert safe["nested"]["x"] is None
        assert "Infinity" not in text and "NaN" not in text

    def test_normal_finite_data_unaffected_by_inf_guard(self):
        rng = np.random.default_rng(3)
        df = pd.DataFrame({
            "group": [0] * 30 + [1] * 30,
            "age": list(rng.normal(50, 10, 30)) + list(rng.normal(55, 10, 30)),
        })
        res = RSA.compare_primary_outcome(df, "age", "group", outcome_type="continuous")
        assert res.get("data_quality_warning") is None
        assert res["group_0"]["n"] == 30


# ── #4 MEDIUM: analyze_missingness() dataset rỗng ───────────────────────────────


class TestMissingnessEmptyDataset:
    def test_empty_dataset_returns_error_not_crash(self):
        df = pd.DataFrame({"group": [], "outcome": []})
        m = RSA.analyze_missingness(df)
        assert "error" in m

    def test_normal_dataset_unaffected(self):
        df = pd.DataFrame({"a": [1, 2, None, 4], "b": [1, 2, 3, 4]})
        m = RSA.analyze_missingness(df)
        assert "error" not in m
        assert m["n_total"] == 4


# ── #5 MEDIUM: kaplan_meier_summary() âm thầm loại một nhánh ────────────────────


@pytest.mark.skipif(not RSA.HAS_LIFELINES, reason="lifelines chưa cài trên máy này")
class TestKaplanMeierSilentGroupDrop:
    def test_group_with_all_missing_time_event_is_flagged_not_silent(self):
        rng = np.random.default_rng(4)
        df = pd.DataFrame({
            "group": [0] * 10 + [1] * 10,
            "time": [None] * 10 + list(rng.uniform(1, 100, 10)),
            "event": [None] * 10 + list(rng.integers(0, 2, 10)),
        })
        r = RSA.kaplan_meier_summary(df, "time", "event", "group")
        assert "0" not in r["groups"]  # nhóm 0 vẫn bị loại (không đủ dữ liệu để fit KM)
        assert "1" in r["groups"]
        assert r.get("warnings"), "phải có cảnh báo khi một nhóm bị loại"
        assert "0" in r["warnings"][0]

    def test_format_survival_text_surfaces_km_warning(self):
        res = {"n": 20, "n_events": 10, "crude": {"HR": 1.5, "CI_95": [1.0, 2.0], "p": 0.04, "concordance": 0.6}}
        km = {"groups": {"1": {"n": 10, "n_events": 5, "median_survival": 12.0}},
              "warnings": ["Nhóm '0' không có quan sát hợp lệ cho time/event — đã LOẠI khỏi phân tích Kaplan-Meier."]}
        txt = RSA.format_survival_text(res, km)
        assert "Nhóm '0'" in txt
        assert "LOẠI khỏi phân tích" in txt

    def test_both_groups_present_no_warning(self):
        rng = np.random.default_rng(5)
        df = pd.DataFrame({
            "group": [0] * 10 + [1] * 10,
            "time": list(rng.uniform(1, 100, 10)) + list(rng.uniform(1, 100, 10)),
            "event": list(rng.integers(0, 2, 10)) + list(rng.integers(0, 2, 10)),
        })
        r = RSA.kaplan_meier_summary(df, "time", "event", "group")
        assert "0" in r["groups"] and "1" in r["groups"]
        assert "warnings" not in r
